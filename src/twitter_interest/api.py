from typing import List, Optional, Tuple, cast

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
import requests

from .settings import Settings, get_settings
from .service import infer_interests, UserNotFoundError

from .api_client import APIClient
from .neo4j_client import Neo4jClient

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


class FollowingUser(BaseModel):
    username: str
    bio: str

@app.get("/followings/{username}", response_model=List[FollowingUser])
def get_followings_with_bios(
    username: str,
    max_records: int = Query(10, ge=1, le=100, description="Maximum number of followings to return"),
    settings: Settings = Depends(get_settings),
):
    neo4j_client = Neo4jClient(settings)
    client = APIClient(settings)
    
    # Try syncing user followings
    try:
        result = client.sync_user_followings(username)
        # If your sync returns a dict with error, handle it here:
        if result.get("status") != "success":
            detail = result.get("error", "Unknown error syncing user followings")
            raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        # Catch network errors or other unexpected exceptions
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    try:
        followings = neo4j_client.get_followings_usernames_with_bios_limit(username, max_records)
        return [FollowingUser(username=f["username"], bio=f["bio"]) for f in followings]
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    finally:
        neo4j_client.close()


class MutualUser(BaseModel):
    id: str
    name: Optional[str] = None
    profile_url: Optional[str] = None

class MutualsResponse(BaseModel):
    status: str
    mutuals: List[MutualUser] = []

@app.get("/mutual", response_model=MutualsResponse)
def get_mutual_followings(
    user1: str = Query(..., description="First username"),
    user2: str = Query(..., description="Second username"),
    settings: Settings = Depends(get_settings),
):
    client = APIClient(settings)
    try:
        result = client.get_mutual_followings(user1, user2)
        if result.get("status") != "success":
            detail = result.get("error") or result.get("msg") or "Unknown error fetching mutuals"
            raise HTTPException(status_code=400, detail=detail)
        # result["data"]["mutuals"] is a list of dicts
        return MutualsResponse(status="success", mutuals=[MutualUser(**item) for item in result["data"].get("mutuals", [])])
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get("error", str(e))
        raise HTTPException(status_code=e.response.status_code, detail=f"Mutuals fetch failed: {error_detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mutuals fetch failed: {str(e)}")


class SyncRequest(BaseModel):
    userName: str

class SyncResponse(BaseModel):
    status: str

@app.post("/sync", response_model=SyncResponse)
def sync_user_followings(
    payload: SyncRequest,
    settings: Settings = Depends(get_settings),
):
    client = APIClient(settings)
    
    try:
        result = client.sync_user_followings(payload.userName)
        return SyncResponse(status=result.get("status", "unknown"))
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get("error", str(e))
        raise HTTPException(status_code=e.response.status_code, detail=f"Sync failed: {error_detail}")