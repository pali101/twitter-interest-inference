from typing import List, Optional, Tuple, cast

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel

from .settings import Settings, get_settings
from .service import infer_interests, UserNotFoundError

app = FastAPI(
    title="Twitter Interest Inference API",
    description= "Given a Twitter username, returns the top interests."
)

class InterestItem(BaseModel):
    interest: str
    score: Optional[float] = None

class InterestResponse(BaseModel):
    username: str
    model: str
    interests: List[InterestItem]

@app.get("/interests/{username}", response_model=InterestResponse)
def get_interests(
    username: str,
    model: Optional[str] = Query(
        None, 
        title="Model override",
        description="Sentence transformer model, e.g., all-MiniLM-L6-v2, paraphrase-mpnet-base-v2"
    ),
    return_scores: bool = Query(False),
    settings: Settings = Depends(get_settings),
):
    settings.return_scores = return_scores
    raw = infer_interests(username, settings)
    # raw can be either Union[List[str] or List[Tuple[str, float]]]
    items: List[InterestItem] = []

    if model:
        settings.model_name = model

    if return_scores:
        scored: List[Tuple[str, float]] = cast(List[Tuple[str, float]], raw)
        items = [
            InterestItem(interest=interest, score=score)
            for interest, score in scored 
        ]
    else:
        unscored: List[str] = cast(List[str], raw)
        items = [InterestItem(interest=interest) for interest in unscored]  

    return InterestResponse(
        username=username.lower(),
        model=settings.model_name,
        interests=items,
    )