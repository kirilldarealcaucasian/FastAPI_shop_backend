from pydantic import BaseModel, Field


class UserInteraction(BaseModel):
    book_id: int = Field(ge=0)
    weight: float = Field(default=1.0, gt=0)


class RecommendationRequest(BaseModel):
    recent_interactions: list[UserInteraction] = Field(min_length=1)


class CandidateScore(BaseModel):
    book_id: int
    score: float


class RecommendationResponse(BaseModel):
    candidates: list[CandidateScore]
