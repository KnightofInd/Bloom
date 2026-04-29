import os
import json
from pathlib import Path
from typing import Any

from core import (
    load_products,
    load_embeddings,
    save_embeddings,
    build_embeddings,
    build_faiss_index,
    save_faiss_index,
    load_faiss_index,
    load_controlled_vocabulary,
    load_embeddings as core_load_embeddings,
    log,
    deduplicate_needs,
)
from extraction import extract_needs
from retrieval import search_by_needs, search_by_needs_numpy, search_by_needs_lexical
from explain import generate_explanation_gemini, generate_explanation_fallback
from core import infer_user_context, resolve_allowed_categories


def run_pipeline(
    *,
    data_json: str = "baby_maternity_products_fixed.json",
    embeddings_path: str = "embeddings.npy",
    index_path: str = "faiss_index.bin",
    vocab_json: str | None = None,
    model_name: str = "all-MiniLM-L6-v2",
    build_only: bool = False,
    rebuild_index: bool = False,
    retrieval_backend: str = "faiss",
    needs_json: str | None = None,
    needs: list[str] | None = None,
    additional_needs: list[str] | None = None,
    user_query: str | None = None,
    need_extractor: str = "vocab",
    gemini_api_key: str | None = None,
    gemini_model: str = "gemini-2.5-flash",
    allowed_categories: list[str] | None = None,
    enforce_preferred_category: bool = False,
    lifecycle_stage: str | None = None,
    lifecycle_weeks: int | None = None,
    k: int = 5,
    top_n: int = 3,
    min_rating: float = 4.2,
    max_price: float | None = None,
    output_json: str = "query_output.json",
    write_output: bool = True,
) -> dict[str, Any] | None:
    data_path = Path(data_json)
    embeddings_file = Path(embeddings_path)
    index_file = Path(index_path)
    vocab_path = Path(vocab_json) if vocab_json else None
    gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    log(f"Loading dataset from {data_path}")
    products = load_products(data_path)
    log(f"Loaded {len(products)} product records")

    embeddings = None
    if embeddings_file.exists():
        try:
            embeddings = core_load_embeddings(embeddings_file)
            log(f"Loaded embeddings from {embeddings_file} with shape {embeddings.shape}")
        except Exception as exc:
            log(f"Could not load saved embeddings, will regenerate: {exc}")

    should_build = rebuild_index or not embeddings_file.exists() or not index_file.exists()
    if should_build:
        log("Step 1/6: Generate embeddings")
        embeddings = build_embeddings(products, model_name)
        log(f"Saving embeddings to {embeddings_file}")
        save_embeddings(embeddings, embeddings_file)

        print(f"embeddings.shape = {embeddings.shape}")

        log("Step 2/6: Build FAISS index")
        index = build_faiss_index(embeddings)
        log(f"Saving FAISS index to {index_file}")
        save_faiss_index(index, index_file)

        print(f"Saved embeddings -> {embeddings_file}")
        print(f"Saved FAISS index -> {index_file}")
    else:
        log(f"Step 1/6: Reusing existing FAISS index from {index_file}")
        index = None

    if build_only:
        log("Build-only mode complete")
        return None

    resolved_needs = []
    if needs_json or needs:
        from core import parse_needs

        resolved_needs = parse_needs(needs_json, needs)

    need_extractor_used = "manual"

    if not resolved_needs and user_query:
        controlled_vocabulary = load_controlled_vocabulary(vocab_path)
        log(
            f"Step 3/6: Extracting needs from user query using {need_extractor} mode "
            f"with controlled vocabulary size={len(controlled_vocabulary)}"
        )
        resolved_needs, need_extractor_used = extract_needs(
            user_query=user_query,
            controlled_vocabulary=controlled_vocabulary,
            extractor=need_extractor,
            gemini_api_key=gemini_key,
            gemini_model=gemini_model,
        )

    if additional_needs:
        resolved_needs = deduplicate_needs(resolved_needs + additional_needs)

    if not resolved_needs:
        print("No needs provided. Build completed; skipping query retrieval.")
        print("Tip: pass --needs/--needs-json, or provide --user-query with --need-extractor.")
        return None

    context = infer_user_context(user_query, resolved_needs)
    if lifecycle_stage:
        context["stage"] = lifecycle_stage
        preferred = set(context.get("preferred_categories", []))
        if lifecycle_stage in {"first_trimester", "second_trimester", "third_trimester", "postpartum"}:
            preferred.add("maternity_care")
        context["preferred_categories"] = sorted(preferred)
    log(
        f"Inferred context: stage={context['stage']}, preferred_categories={context['preferred_categories']}"
    )
    allowed_category_set = resolve_allowed_categories(
        allowed_categories,
        context,
        enforce_preferred_category,
    )
    if allowed_category_set is not None:
        log(f"Effective category guardrail: {sorted(allowed_category_set)}")

    log("Step 5/6: Retrieve and merge results")
    if retrieval_backend == "faiss":
        from core import load_sentence_transformer, load_faiss_index

        log("Loading model for query embeddings (can be slow on first run)")
        model = load_sentence_transformer(model_name)
        if index is None:
            index = load_faiss_index(index_file)
        result = search_by_needs(
            needs=resolved_needs,
            products=products,
            index=index,
            model=model,
            context=context,
            allowed_categories=allowed_category_set,
            k=k,
            min_rating=min_rating,
            max_price=max_price,
            top_n=top_n,
        )
    elif retrieval_backend == "numpy":
        from core import load_sentence_transformer

        log("Loading model for query embeddings (can be slow on first run)")
        model = load_sentence_transformer(model_name)
        if embeddings is None:
            embeddings = build_embeddings(products, model_name)
            save_embeddings(embeddings, embeddings_file)
        result = search_by_needs_numpy(
            needs=resolved_needs,
            products=products,
            embeddings=embeddings,
            model=model,
            context=context,
            allowed_categories=allowed_category_set,
            k=k,
            min_rating=min_rating,
            max_price=max_price,
            top_n=top_n,
        )
    else:
        result = search_by_needs_lexical(
            needs=resolved_needs,
            products=products,
            context=context,
            allowed_categories=allowed_category_set,
            k=k,
            min_rating=min_rating,
            max_price=max_price,
            top_n=top_n,
        )

    if user_query and gemini_key:
        try:
            explanation = generate_explanation_gemini(
                user_query=user_query,
                needs=result["needs"],
                products=result["products"],
                api_key=gemini_key,
                model_name=gemini_model,
            )
            explanation_model = "gemini"
        except Exception as exc:
            log(f"Gemini explanation failed, using fallback: {exc}")
            explanation = generate_explanation_fallback(
                result["needs"],
                min_rating,
                max_price,
                context,
                result["products"],
                allowed_category_set,
            )
            explanation_model = "fallback"
    else:
        explanation = generate_explanation_fallback(
            result["needs"],
            min_rating,
            max_price,
            context,
            result["products"],
            allowed_category_set,
        )
        explanation_model = "fallback"

    final_output = {
        "user_query": user_query,
        "needs": result["needs"],
        "products": result["products"],
        "explanation": explanation,
        "meta": {
            "need_extractor": need_extractor_used,
            "explanation_generator": explanation_model,
            "retrieval_backend": result.get("backend", retrieval_backend),
            "inferred_stage": context.get("stage"),
            "preferred_categories": context.get("preferred_categories"),
            "effective_allowed_categories": sorted(allowed_category_set) if allowed_category_set is not None else None,
            "k": k,
            "top_n": top_n,
            "min_rating": min_rating,
            "max_price": max_price,
            "model_name": model_name,
            "gemini_model": gemini_model if gemini_key else None,
            "lifecycle_stage": lifecycle_stage,
            "lifecycle_weeks": lifecycle_weeks,
            "lifecycle_needs_added": additional_needs or [],
        },
    }

    if write_output:
        output_path = Path(output_json)
        log("Step 6/6: Save final output JSON")
        output_path.write_text(json.dumps(final_output, indent=2, ensure_ascii=False), encoding="utf-8")

        print("\nFinal output:")
        print(json.dumps(final_output, indent=2, ensure_ascii=False))
        print(f"Saved query output -> {output_path}")

    return final_output


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MVP embedding + FAISS retrieval pipeline")
    parser.add_argument("--data-json", default="baby_maternity_products_fixed.json")
    parser.add_argument("--embeddings-path", default="embeddings.npy")
    parser.add_argument("--index-path", default="faiss_index.bin")
    parser.add_argument("--vocab-json", default=None, help="Optional JSON list or {'needs': [...]} for controlled vocabulary")
    parser.add_argument("--model-name", default="all-MiniLM-L6-v2")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true", help="Force rebuild embeddings and FAISS index")
    parser.add_argument("--retrieval-backend", choices=["auto", "lexical", "numpy", "faiss"], default="faiss")

    parser.add_argument("--needs-json", default=None, help='Example: {"needs": ["support belt"]}')
    parser.add_argument("--needs", nargs="*", default=None)
    parser.add_argument("--user-query", default=None, help="Natural language user input for LLM/heuristic need extraction")
    parser.add_argument("--need-extractor", choices=["auto", "gemini", "heuristic", "vocab"], default="vocab")
    parser.add_argument("--gemini-api-key", default=None)
    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--allowed-categories", nargs="*", default=None)
    parser.add_argument(
        "--enforce-preferred-category",
        action="store_true",
        help="When no explicit categories are passed, restrict to inferred preferred categories.",
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--min-rating", type=float, default=4.2)
    parser.add_argument("--max-price", type=float, default=None)
    parser.add_argument("--output-json", default="query_output.json")

    args = parser.parse_args()

    run_pipeline(
        data_json=args.data_json,
        embeddings_path=args.embeddings_path,
        index_path=args.index_path,
        vocab_json=args.vocab_json,
        model_name=args.model_name,
        build_only=args.build_only,
        rebuild_index=args.rebuild_index,
        retrieval_backend=args.retrieval_backend,
        needs_json=args.needs_json,
        needs=args.needs,
        user_query=args.user_query,
        need_extractor=args.need_extractor,
        gemini_api_key=args.gemini_api_key or os.getenv("GEMINI_API_KEY"),
        gemini_model=args.gemini_model,
        allowed_categories=args.allowed_categories,
        enforce_preferred_category=args.enforce_preferred_category,
        k=args.k,
        top_n=args.top_n,
        min_rating=args.min_rating,
        max_price=args.max_price,
        output_json=args.output_json,
        write_output=True,
    )


if __name__ == "__main__":
    main()
