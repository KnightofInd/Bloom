from typing import Any
from core import tokenize, normalize_need, deduplicate_needs, log
from typing import List
import re
import json
from core import load_controlled_vocabulary
from core import pass_business_filters
from urllib import error as urllib_error


DEFAULT_CONTROLLED_NEEDS = [
    "support belt",
    "pregnancy pillow",
    "maternity bra",
    "nursing bra",
    "nipple cream",
    "breast pump",
    "milk storage bags",
    "anti-colic bottles",
    "baby bottle",
    "formula dispenser",
    "sterilizer",
    "bottle warmer",
    "newborn diapers",
    "baby wipes",
    "diaper rash cream",
    "diaper bag",
    "diaper pail",
    "cloth diapers",
    "stroller",
    "car seat",
    "travel stroller",
    "baby carrier",
    "baby monitor",
    "crib",
    "cot mattress",
    "swaddle",
    "sleep sack",
    "white noise machine",
    "baby bath tub",
    "baby shampoo",
    "baby lotion",
    "thermometer",
    "nasal aspirator",
    "teether",
    "pacifier",
    "postpartum pads",
    "postpartum recovery",
    "stretch mark cream",
    "maternity leggings",
    "feeding pillow",
]


HEURISTIC_NEED_HINTS = {
    "support belt": ["back pain", "pelvic pain", "belly support", "back hurts", "lower back"],
    "pregnancy pillow": ["sleep", "sleeping", "can't sleep", "back pain at night", "side sleeping"],
    "maternity bra": ["maternity bra", "pregnancy bra", "bra tight"],
    "nursing bra": ["nursing", "breastfeeding bra", "feeding bra"],
    "nipple cream": ["sore nipples", "nipple pain", "cracked nipples"],
    "breast pump": ["pump", "express milk", "breast pump", "pumping"],
    "milk storage bags": ["store milk", "milk bags", "milk storage"],
    "anti-colic bottles": ["colic", "gas", "spit up", "anti colic"],
    "baby bottle": ["bottle feeding", "baby bottle", "feed bottle"],
    "sterilizer": ["sterilize", "sanitize bottles", "germs"],
    "bottle warmer": ["warm milk", "bottle warmer"],
}


def extract_needs_heuristic(user_query: str, controlled_vocabulary: List[str]) -> List[str]:
    query = normalize_need(user_query)
    extracted: list[str] = []

    for need, hints in HEURISTIC_NEED_HINTS.items():
        if any(hint in query for hint in hints):
            extracted.append(need)

    if ("pregnan" in query or "trimester" in query) and ("back pain" in query or "back hurts" in query):
        extracted.extend(["support belt", "pregnancy pillow"])

    constrained = [n for n in [normalize_need(x) for x in extracted] if normalize_need(n) in {normalize_need(v) for v in controlled_vocabulary}]
    if constrained:
        return deduplicate_needs(constrained)

    backoff = [
        "support belt" if "pregnan" in query or "trimester" in query else "",
        "newborn diapers" if "newborn" in query or "diaper" in query else "",
        "anti-colic bottles" if "feeding" in query or "colic" in query else "",
    ]
    return deduplicate_needs([item for item in backoff if item])


def map_to_vocab_by_lexical(user_query: str, controlled_vocabulary: List[str], top_k: int = 4) -> List[str]:
    q_tokens = set(tokenize(user_query))
    scores: list[tuple[int, str]] = []
    for v in controlled_vocabulary:
        v_tokens = set(tokenize(v))
        overlap = len(q_tokens & v_tokens)
        verbatim = 1 if normalize_need(v) in normalize_need(user_query) else 0
        scores.append((overlap + verbatim, v))

    scores.sort(key=lambda x: x[0], reverse=True)
    chosen = [v for s, v in scores if s > 0][:top_k]
    return deduplicate_needs(chosen)


def call_gemini_json(prompt: str, api_key: str, model_name: str, timeout_seconds: int = 20) -> dict[str, Any]:
    # kept lightweight here; pipeline will provide a richer retry surface via pipeline
    from urllib import request as urllib_request

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        f"?key={api_key}"
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }

    request = urllib_request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP error {err.code}: {detail}") from err
    except urllib_error.URLError as err:
        raise RuntimeError(f"Gemini API connection error: {err.reason}") from err

    payload = json.loads(raw)
    candidates = payload.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini API returned no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts or "text" not in parts[0]:
        raise RuntimeError("Gemini API returned no text content.")

    text = parts[0]["text"].strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"```$", "", text)
    return json.loads(text)


def extract_needs_gemini(user_query: str, controlled_vocabulary: List[str], api_key: str, model_name: str) -> List[str]:
    vocab_text = "\n".join(f"- {item}" for item in controlled_vocabulary)
    prompt = (
        "You are a strict need extraction engine for baby and maternity ecommerce.\n"
        "Extract only concrete user needs from the query using the controlled vocabulary below.\n"
        "Rules:\n"
        "1) Return JSON only.\n"
        "2) Format must be exactly: {\"needs\": [\"...\"]}.\n"
        "3) Do not output product names unless they are in vocabulary.\n"
        "4) Do not invent terms outside vocabulary.\n"
        "5) Return up to 4 needs, ranked by relevance.\n\n"
        f"Controlled vocabulary:\n{vocab_text}\n\n"
        f"User query:\n{user_query}"
    )

    parsed = call_gemini_json(prompt=prompt, api_key=api_key, model_name=model_name)
    if "needs" not in parsed or not isinstance(parsed["needs"], list):
        raise RuntimeError("Gemini extraction response missing 'needs' list.")

    raw_needs = [n for n in parsed["needs"] if isinstance(n, str)]
    # constrain
    vocab_set = {normalize_need(v) for v in controlled_vocabulary}
    constrained = [normalize_need(n) for n in raw_needs if normalize_need(n) in vocab_set]
    return deduplicate_needs(constrained)


def extract_needs_lifecycle_gemini(
    *,
    lifecycle_stage: str,
    lifecycle_weeks: int,
    lifecycle_needs: list[str],
    user_query: str | None,
    controlled_vocabulary: list[str],
    api_key: str,
    model_name: str,
) -> list[str]:
    vocab_text = "\n".join(f"- {item}" for item in controlled_vocabulary)
    base_needs_text = ", ".join(lifecycle_needs) if lifecycle_needs else "none"
    user_text = user_query or ""

    prompt = (
        "You are a strict need extraction engine for baby and maternity ecommerce.\n"
        "We are using lifecycle-based recommendations derived from pregnancy stage.\n"
        "Return only needs from the controlled vocabulary below.\n"
        "Rules:\n"
        "1) Return JSON only.\n"
        "2) Format must be exactly: {\"needs\": [\"...\"]}.\n"
        "3) Do not invent terms outside vocabulary.\n"
        "4) Return up to 5 needs, ranked by relevance.\n"
        "5) Use lifecycle base needs as a strong hint; keep them if relevant.\n\n"
        f"Lifecycle stage: {lifecycle_stage} (week {lifecycle_weeks}).\n"
        f"Lifecycle base needs: {base_needs_text}.\n\n"
        f"Controlled vocabulary:\n{vocab_text}\n\n"
        f"User query:\n{user_text}"
    )

    parsed = call_gemini_json(prompt=prompt, api_key=api_key, model_name=model_name)
    if "needs" not in parsed or not isinstance(parsed["needs"], list):
        raise RuntimeError("Gemini lifecycle response missing 'needs' list.")

    raw_needs = [n for n in parsed["needs"] if isinstance(n, str)]
    vocab_set = {normalize_need(v) for v in controlled_vocabulary}
    constrained = [normalize_need(n) for n in raw_needs if normalize_need(n) in vocab_set]
    merged = deduplicate_needs(constrained + lifecycle_needs)
    return merged


def extract_needs(
    user_query: str,
    controlled_vocabulary: List[str],
    extractor: str,
    gemini_api_key: str | None,
    gemini_model: str,
) -> tuple[List[str], str]:
    if extractor == "gemini":
        if not gemini_api_key:
            raise ValueError("--need-extractor gemini requires --gemini-api-key or GEMINI_API_KEY.")
        return extract_needs_gemini(user_query, controlled_vocabulary, gemini_api_key, gemini_model), "gemini"

    if extractor == "vocab":
        # try gemini mapping first if key present
        if gemini_api_key:
            try:
                mapped = extract_needs_gemini(user_query, controlled_vocabulary, gemini_api_key, gemini_model)
                if mapped:
                    return mapped, "gemini"
            except Exception as exc:
                log(f"Gemini vocab mapping failed, falling back to local mapping: {exc}")

        heuristic = extract_needs_heuristic(user_query, controlled_vocabulary)
        if heuristic:
            return heuristic, "heuristic"

        lexical = map_to_vocab_by_lexical(user_query, controlled_vocabulary, top_k=4)
        return lexical, "vocab_lexical"

    if extractor == "heuristic":
        return extract_needs_heuristic(user_query, controlled_vocabulary), "heuristic"

    # auto mode
    if gemini_api_key:
        try:
            needs = extract_needs_gemini(user_query, controlled_vocabulary, gemini_api_key, gemini_model)
            if needs:
                return needs, "gemini"
        except Exception as exc:
            log(f"Gemini need extraction failed, switching to heuristic mode: {exc}")

    return extract_needs_heuristic(user_query, controlled_vocabulary), "heuristic"
