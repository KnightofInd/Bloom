import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import compute_lifecycle_from_lmp, load_controlled_vocabulary
from extraction import extract_needs_lifecycle_gemini
from pipeline import run_pipeline

app = FastAPI(title="Recommendation API")

UI_DIR = Path(__file__).resolve().parent / "ui"
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


class RecommendRequest(BaseModel):
    user_query: str
    need_extractor: Optional[str] = None
    retrieval_backend: Optional[str] = None
    top_n: Optional[int] = 3
    k: Optional[int] = 5
    min_rating: Optional[float] = 4.2
    max_price: Optional[float] = None


class LifecycleRequest(BaseModel):
    lmp_date: str
    user_query: Optional[str] = None
    postpartum_flag: Optional[bool] = False
    need_extractor: Optional[str] = None
    retrieval_backend: Optional[str] = None
    top_n: Optional[int] = 3
    k: Optional[int] = 5
    min_rating: Optional[float] = 4.2
    max_price: Optional[float] = None


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    try:
        result = run_pipeline(
            user_query=req.user_query,
            need_extractor=req.need_extractor or "vocab",
            retrieval_backend=req.retrieval_backend or "faiss",
            gemini_api_key=gemini_api_key,
            top_n=req.top_n if req.top_n is not None else 3,
            k=req.k if req.k is not None else 5,
            min_rating=req.min_rating if req.min_rating is not None else 4.2,
            max_price=req.max_price,
            write_output=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=400, detail="No recommendation output was produced.")

    return result


@app.post("/lifecycle_recommend")
async def lifecycle_recommend(req: LifecycleRequest):
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    try:
        lifecycle = compute_lifecycle_from_lmp(
            req.lmp_date,
            postpartum_flag=bool(req.postpartum_flag),
        )
        lifecycle_needs = lifecycle["lifecycle_needs"]

        if gemini_api_key:
            vocab = load_controlled_vocabulary(None)
            lifecycle_needs = extract_needs_lifecycle_gemini(
                lifecycle_stage=lifecycle["stage"],
                lifecycle_weeks=lifecycle["weeks"],
                lifecycle_needs=lifecycle_needs,
                user_query=req.user_query,
                controlled_vocabulary=vocab,
                api_key=gemini_api_key,
                model_name="gemini-2.5-flash",
            )

        result = run_pipeline(
            user_query=req.user_query,
            need_extractor=req.need_extractor or "vocab",
            retrieval_backend=req.retrieval_backend or "faiss",
            gemini_api_key=gemini_api_key,
            top_n=req.top_n if req.top_n is not None else 3,
            k=req.k if req.k is not None else 5,
            min_rating=req.min_rating if req.min_rating is not None else 4.2,
            max_price=req.max_price,
            additional_needs=lifecycle_needs,
            lifecycle_stage=lifecycle["stage"],
            lifecycle_weeks=lifecycle["weeks"],
            write_output=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=400, detail="No recommendation output was produced.")

    return result


@app.get("/")
def ui_home():
    return FileResponse(UI_DIR / "index.html")
