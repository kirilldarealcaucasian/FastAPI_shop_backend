from fastapi import FastAPI, HTTPException

from recommendations.config import settings
from recommendations.schemas import RecommendationRequest, RecommendationResponse
from recommendations.service import (
    BookFactorsStore,
    RecommendationService,
)

app = FastAPI(
    title="Recommendations Inference Server",
    version="0.1.0",
    description="Serves candidate generation from recent user interactions.",
)

factors_store = BookFactorsStore(
    factors_path=settings.BOOKS_FACTORS_PATH,
    book_ids_path=settings.BOOKS_IDS_PATH,
)
recommendation_service = RecommendationService(
    factors_store=factors_store,
    candidates_limit=settings.RECOMMENDATIONS_CANDIDATES,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/inference/recommendations", response_model=RecommendationResponse)
async def recommend(
    payload: RecommendationRequest,
) -> RecommendationResponse:
    try:
        recommendations = recommendation_service.recommend(
            interactions=payload.recent_interactions
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return RecommendationResponse(candidates=recommendations)
