from typing import Any
from core import tokenize, normalize_need, rerank_with_context, pass_business_filters, normalize_embeddings
import numpy as np


def search_by_needs_lexical(
    needs: list[str],
    products: list[dict[str, Any]],
    context: dict[str, Any],
    allowed_categories: set[str] | None,
    k: int,
    min_rating: float,
    max_price: float | None,
    top_n: int,
) -> dict[str, Any]:
    merged: dict[int, dict[str, Any]] = {}
    effective_k = min(k, len(products))
    product_tokens = [tokenize(p.get("combined_text", "")) for p in products]

    for need in needs:
        need_tokens = tokenize(need)

        scored: list[tuple[float, int]] = []
        for idx, product in enumerate(products):
            tokens = product_tokens[idx]
            overlap = len(need_tokens & tokens)
            substring_bonus = 2.0 if normalize_need(need) in normalize_need(product.get("combined_text", "")) else 0.0
            score = float(overlap) + substring_bonus
            if score > 0:
                scored.append((score, idx))

        scored.sort(key=lambda item: item[0], reverse=True)
        for score, idx in scored[:effective_k]:
            product = products[idx]
            pid = int(product["id"])
            distance = float(1.0 / (1.0 + score))
            if pid not in merged or distance < merged[pid]["distance"]:
                merged[pid] = {
                    "distance": distance,
                    "matched_need": need,
                    "product": product,
                }

    ranked = rerank_with_context(list(merged.values()), context)

    filtered = []
    for item in ranked:
        p = item["product"]
        if not pass_business_filters(p, min_rating, max_price, allowed_categories):
            continue
        filtered.append(item)

    top_products = []
    for item in filtered[:top_n]:
        p = dict(item["product"])
        p["retrieval_distance"] = round(item["distance"], 6)
        p["matched_need"] = item["matched_need"]
        top_products.append(p)

    return {
        "needs": needs,
        "products": top_products,
        "backend": "lexical",
    }


def search_by_needs_numpy(
    needs: list[str],
    products: list[dict[str, Any]],
    embeddings: np.ndarray,
    model: Any,
    context: dict[str, Any],
    allowed_categories: set[str] | None,
    k: int,
    min_rating: float,
    max_price: float | None,
    top_n: int,
) -> dict[str, Any]:
    normalized_embeddings = normalize_embeddings(embeddings.astype("float32"))
    merged: dict[int, dict[str, Any]] = {}
    effective_k = min(k, len(products))

    for need in needs:
        query_embedding = model.encode([need], convert_to_numpy=True).astype("float32")
        query_embedding = normalize_embeddings(query_embedding)[0]
        similarities = normalized_embeddings @ query_embedding
        best_indices = np.argsort(-similarities)[:effective_k]

        for idx in best_indices:
            if idx < 0 or idx >= len(products):
                continue

            product = products[int(idx)]
            pid = int(product["id"])
            distance = float(1.0 - similarities[int(idx)])

            if pid not in merged or distance < merged[pid]["distance"]:
                merged[pid] = {
                    "distance": distance,
                    "matched_need": need,
                    "product": product,
                }

    ranked = rerank_with_context(list(merged.values()), context)

    filtered = []
    for item in ranked:
        p = item["product"]
        if not pass_business_filters(p, min_rating, max_price, allowed_categories):
            continue
        filtered.append(item)

    top_products = []
    for item in filtered[:top_n]:
        p = dict(item["product"])
        p["retrieval_distance"] = round(item["distance"], 6)
        p["matched_need"] = item["matched_need"]
        top_products.append(p)

    return {
        "needs": needs,
        "products": top_products,
        "backend": "numpy",
    }


def search_by_needs(
    needs: list[str],
    products: list[dict[str, Any]],
    index: Any,
    model: Any,
    context: dict[str, Any],
    allowed_categories: set[str] | None,
    k: int,
    min_rating: float,
    max_price: float | None,
    top_n: int,
) -> dict[str, Any]:
    merged: dict[int, dict[str, Any]] = {}

    effective_k = min(k, index.ntotal)
    for need in needs:
        query_embedding = model.encode([need], convert_to_numpy=True).astype("float32")
        distances, indices = index.search(query_embedding, effective_k)

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(products):
                continue

            product = products[idx]
            pid = int(product["id"])

            if pid not in merged or dist < merged[pid]["distance"]:
                merged[pid] = {
                    "distance": float(dist),
                    "matched_need": need,
                    "product": product,
                }

    ranked = rerank_with_context(list(merged.values()), context)

    filtered = []
    for item in ranked:
        p = item["product"]
        if not pass_business_filters(p, min_rating, max_price, allowed_categories):
            continue
        filtered.append(item)

    top_products = []
    for item in filtered[:top_n]:
        p = dict(item["product"])
        p["retrieval_distance"] = round(item["distance"], 6)
        p["matched_need"] = item["matched_need"]
        top_products.append(p)

    return {
        "needs": needs,
        "products": top_products,
        "backend": "faiss",
    }
