import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

import numpy as np


def log(message: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    log(f"Loading embedding model: {model_name} (first load may download weights)")
    model = SentenceTransformer(model_name)
    log(f"Embedding model ready: {model_name}")
    return model


def load_faiss_module():
    import faiss

    return faiss


def load_products(data_path: Path) -> list[dict[str, Any]]:
    with data_path.open("r", encoding="utf-8") as f:
        products = json.load(f)

    if not isinstance(products, list):
        raise ValueError("Input JSON must be a list of product objects.")

    missing = [p.get("id", "unknown") for p in products if "combined_text" not in p]
    if missing:
        raise ValueError(f"Missing 'combined_text' in products: {missing[:5]}")

    return products


def build_embeddings(products: list[dict[str, Any]], model_name: str) -> np.ndarray:
    texts = [p["combined_text"] for p in products]
    model = load_sentence_transformer(model_name)
    log(f"Encoding {len(texts)} products into embeddings...")
    start = time.time()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    elapsed = time.time() - start
    log(f"Embedding generation complete in {elapsed:.2f}s")
    embeddings = embeddings.astype("float32")
    return embeddings


def save_embeddings(embeddings: np.ndarray, embeddings_path: Path) -> None:
    np.save(embeddings_path, embeddings)


def load_embeddings(embeddings_path: Path) -> np.ndarray:
    return np.load(embeddings_path)


def build_faiss_index(embeddings: np.ndarray) -> Any:
    faiss = load_faiss_module()
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index


def save_faiss_index(index: Any, index_path: Path) -> None:
    faiss = load_faiss_module()
    faiss.write_index(index, str(index_path))


def load_faiss_index(index_path: Path) -> Any:
    faiss = load_faiss_module()
    return faiss.read_index(str(index_path))


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return embeddings / norms


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1}


def normalize_need(need: str) -> str:
    return re.sub(r"\s+", " ", need.strip().lower())


def deduplicate_needs(needs: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for need in needs:
        normalized = normalize_need(need)
        if not normalized or normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)
    return deduped


LIFECYCLE_NEEDS_BY_STAGE: dict[str, list[str]] = {
    "first_trimester": [
        "maternity bra",
        "stretch mark cream",
        "pregnancy pillow",
    ],
    "second_trimester": [
        "support belt",
        "maternity leggings",
        "pregnancy pillow",
        "feeding pillow",
    ],
    "third_trimester": [
        "support belt",
        "pregnancy pillow",
        "breast pump",
        "postpartum pads",
    ],
    "postpartum": [
        "postpartum recovery",
        "postpartum pads",
        "nipple cream",
        "breast pump",
        "milk storage bags",
        "newborn diapers",
        "baby wipes",
    ],
}


def compute_lifecycle_from_lmp(
    lmp_date: str,
    *,
    today: date | None = None,
    postpartum_flag: bool = False,
) -> dict[str, Any]:
    try:
        lmp = datetime.strptime(lmp_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("LMP date must be in YYYY-MM-DD format.") from exc

    current = today or date.today()
    delta_days = (current - lmp).days
    if delta_days < 0:
        raise ValueError("LMP date cannot be in the future.")

    weeks = max(0, delta_days // 7)
    if postpartum_flag or weeks >= 41:
        stage = "postpartum"
    elif weeks <= 12:
        stage = "first_trimester"
    elif weeks <= 27:
        stage = "second_trimester"
    else:
        stage = "third_trimester"

    lifecycle_needs = deduplicate_needs(LIFECYCLE_NEEDS_BY_STAGE.get(stage, []))

    return {
        "weeks": weeks,
        "stage": stage,
        "lifecycle_needs": lifecycle_needs,
    }


def infer_user_context(user_query: str | None, needs: list[str]) -> dict[str, Any]:
    query = normalize_need(user_query or "")
    needs_set = {normalize_need(n) for n in needs}

    stage = "unknown"
    preferred_categories: set[str] = set()

    month_match = re.search(r"\b([1-9]|1[0-2])\s*(month|months)\b", query)
    if month_match:
        month = int(month_match.group(1))
        if month <= 3:
            stage = "first_trimester"
        elif month <= 6:
            stage = "second_trimester"
        else:
            stage = "third_trimester"

    week_match = re.search(r"\b([1-4][0-9])\s*(week|weeks)\b", query)
    if week_match:
        week = int(week_match.group(1))
        if week <= 13:
            stage = "first_trimester"
        elif week <= 27:
            stage = "second_trimester"
        else:
            stage = "third_trimester"

    if "pregnan" in query:
        preferred_categories.add("maternity_care")
    if "postpartum" in query or "after birth" in query:
        preferred_categories.add("maternity_care")
    if "newborn" in query:
        preferred_categories.update({"diapering", "feeding", "nursery_sleep", "health_safety"})
    if any(n in needs_set for n in {"support belt", "pregnancy pillow", "postpartum recovery", "postpartum pads"}):
        preferred_categories.add("maternity_care")
    if any(n in needs_set for n in {"newborn diapers", "baby wipes", "diaper rash cream", "diaper bag"}):
        preferred_categories.add("diapering")

    return {
        "stage": stage,
        "preferred_categories": sorted(preferred_categories),
    }


def resolve_allowed_categories(
    cli_allowed_categories: list[str] | None,
    context: dict[str, Any],
    enforce_preferred_category: bool,
) -> set[str] | None:
    if cli_allowed_categories:
        return {str(cat).strip() for cat in cli_allowed_categories if str(cat).strip()}

    if enforce_preferred_category:
        preferred = context.get("preferred_categories", [])
        if preferred:
            return {str(cat).strip() for cat in preferred if str(cat).strip()}

    return None


def pass_business_filters(
    product: dict[str, Any],
    min_rating: float,
    max_price: float | None,
    allowed_categories: set[str] | None,
) -> bool:
    if float(product.get("rating", 0)) < min_rating:
        return False
    if max_price is not None and float(product.get("price", float("inf"))) > max_price:
        return False
    if allowed_categories is not None and str(product.get("category", "")) not in allowed_categories:
        return False
    return True


def rerank_with_context(candidates: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    preferred_categories = set(context.get("preferred_categories", []))
    reranked: list[dict[str, Any]] = []

    for item in candidates:
        product = item["product"]
        category = str(product.get("category", ""))
        category_bonus = 0.15 if category in preferred_categories else 0.0
        category_penalty = 0.12 if preferred_categories and category not in preferred_categories else 0.0
        item_with_bonus = dict(item)
        item_with_bonus["context_bonus"] = category_bonus - category_penalty
        reranked.append(item_with_bonus)

    return sorted(
        reranked,
        key=lambda x: (x["distance"] - x.get("context_bonus", 0.0), -x["product"].get("rating", 0)),
    )


def load_controlled_vocabulary(vocab_path: Path | None) -> list[str]:
    if not vocab_path:
        from extraction import DEFAULT_CONTROLLED_NEEDS  # local import to avoid cycle

        return deduplicate_needs(DEFAULT_CONTROLLED_NEEDS)

    content = json.loads(vocab_path.read_text(encoding="utf-8"))
    if isinstance(content, list):
        if not all(isinstance(item, str) for item in content):
            raise ValueError("Vocabulary list must contain only strings.")
        return deduplicate_needs(content)

    if isinstance(content, dict) and "needs" in content and isinstance(content["needs"], list):
        if not all(isinstance(item, str) for item in content["needs"]):
            raise ValueError("Vocabulary payload 'needs' must contain only strings.")
        return deduplicate_needs(content["needs"])

    raise ValueError("Vocabulary JSON must be either a list of strings or {'needs': [...]}.")


def parse_needs_payload(raw_payload: str) -> list[str]:
    payload = json.loads(raw_payload)
    if not isinstance(payload, dict) or "needs" not in payload:
        raise ValueError("Payload must look like: {\"needs\": [\"support belt\"]}")
    needs = payload["needs"]
    if not isinstance(needs, list) or not all(isinstance(n, str) for n in needs):
        raise ValueError("'needs' must be a list of strings.")
    return deduplicate_needs(needs)


def parse_needs(needs_json: str | None, needs_list: list[str] | None) -> list[str]:
    if needs_json:
        return parse_needs_payload(needs_json)

    if needs_list:
        return deduplicate_needs(needs_list)

    return []
