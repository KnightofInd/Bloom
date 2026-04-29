import json
from typing import Any
from core import log


def generate_explanation_gemini(
    user_query: str,
    needs: list[str],
    products: list[dict[str, Any]],
    api_key: str,
    model_name: str,
) -> str:
    compact_products = [
        {
            "name": p.get("name"),
            "category": p.get("category"),
            "price": p.get("price"),
            "rating": p.get("rating"),
            "matched_need": p.get("matched_need"),
        }
        for p in products
    ]

    prompt = (
        "You are an assistant explaining recommendation results for baby/maternity ecommerce.\n"
        "Write 2-3 concise sentences that explain why these recommendations match the user situation.\n"
        "Do not fabricate medical claims. Do not mention retrieval distance.\n"
        "Keep tone practical and reassuring.\n\n"
        f"User query: {user_query}\n"
        f"Extracted needs: {json.dumps(needs, ensure_ascii=False)}\n"
        f"Selected products: {json.dumps(compact_products, ensure_ascii=False)}"
    )

    from extraction import call_gemini_json

    parsed = call_gemini_json(
        prompt=("Return JSON only in this format: {\"explanation\": \"...\"}.\n\n" + prompt),
        api_key=api_key,
        model_name=model_name,
    )

    explanation = parsed.get("explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        raise RuntimeError("Gemini explanation response missing 'explanation' text.")
    return explanation.strip()


def generate_explanation_fallback(
    needs: list[str],
    min_rating: float,
    max_price: float | None,
    context: dict[str, Any],
    products: list[dict[str, Any]],
    allowed_categories: set[str] | None,
) -> str:
    filters = [f"rating >= {min_rating}"]
    if max_price is not None:
        filters.append(f"price <= {max_price}")
    if allowed_categories is not None:
        filters.append(f"category in {sorted(allowed_categories)}")

    stage = context.get("stage", "unknown")
    stage_text = ""
    if stage == "third_trimester":
        stage_text = " in late pregnancy"
    elif stage == "second_trimester":
        stage_text = " in mid pregnancy"
    elif stage == "first_trimester":
        stage_text = " in early pregnancy"
    elif stage == "postpartum":
        stage_text = " in postpartum recovery"

    categories = sorted({str(p.get("category", "")) for p in products if p.get("category")})
    category_text = f" Relevant categories: {', '.join(categories)}." if categories else ""

    return (
        f"These recommendations are aligned to your needs ({', '.join(needs)}){stage_text}, "
        f"then filtered for quality and budget constraints ({', '.join(filters)})."
        + category_text
    )
