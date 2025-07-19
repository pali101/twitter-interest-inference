from typing import List, Optional, Tuple, cast

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
import requests

from .settings import Settings, get_settings
from .service import infer_interests, UserNotFoundError
from .logging_config import setup_logging, get_logger

from .api_client import APIClient
from .neo4j_client import Neo4jClient

# Setup logging for API
settings_for_logging = Settings()
setup_logging(
    level=settings_for_logging.log_level,
    log_file=settings_for_logging.log_file,
    enable_file_logging=settings_for_logging.enable_file_logging,
    enable_rotation=settings_for_logging.enable_log_rotation,
    max_file_size=settings_for_logging.max_log_file_size,
    retention=settings_for_logging.log_retention
)

logger = get_logger(__name__)

app = FastAPI(
    title="Twitter Interest Inference API",
    description= "Given a Twitter username, returns the top interests."
)

def normalize_username(username: str) -> str:
    # Remove whitespace, leading '@', and lowercase
    normalized = username.strip().lstrip("@").lower()
    logger.debug(f"Normalized username '{username}' to '{normalized}'")
    return normalized

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
    username = normalize_username(username)
    logger.info(f"GET /interests/{username} - model: {model}, return_scores: {return_scores}")
    
    settings.return_scores = return_scores
    
    if model:
        logger.info(f"Using model override: {model}")
        settings.model_name = model

    try:
        raw = infer_interests(username, settings)
        # raw can be either Union[List[str] or List[Tuple[str, float]]]
        items: List[InterestItem] = []

        if return_scores:
            scored: List[Tuple[str, float]] = cast(List[Tuple[str, float]], raw)
            items = [
                InterestItem(interest=interest, score=score)
                for interest, score in scored 
            ]
        else:
            unscored: List[str] = cast(List[str], raw)
            items = [InterestItem(interest=interest) for interest in unscored]  

        response = InterestResponse(
            username=username.lower(),
            model=settings.model_name,
            interests=items,
        )
        logger.info(f"Successfully retrieved {len(items)} interests for user {username}")
        return response
        
    except UserNotFoundError:
        logger.warning(f"User '{username}' not found")
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    except Exception as e:
        logger.error(f"Error retrieving interests for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class FollowingUser(BaseModel):
    username: str
    bio: str

@app.get("/followings/{username}", response_model=List[FollowingUser])
def get_followings_with_bios(
    username: str,
    max_records: int = Query(10, ge=1, le=100, description="Maximum number of followings to return"),
    settings: Settings = Depends(get_settings),
):
    username = normalize_username(username)
    logger.info(f"GET /followings/{username} - max_records: {max_records}")
    
    neo4j_client = Neo4jClient(settings)
    client = APIClient(settings)
    
    # Try syncing user followings
    try:
        logger.debug(f"Syncing followings for user: {username}")
        result = client.sync_user_followings(username)
        # If your sync returns a dict with error, handle it here:
        if result.get("status") != "success":
            detail = result.get("error", "Unknown error syncing user followings")
            logger.error(f"Sync failed for user {username}: {detail}")
            raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        # Catch network errors or other unexpected exceptions
        logger.error(f"Sync failed for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    try:
        followings = neo4j_client.get_followings_usernames_with_bios_limit(username, max_records)
        logger.info(f"Retrieved {len(followings)} followings for user {username}")
        return [FollowingUser(username=f["username"], bio=f["bio"]) for f in followings]
    except UserNotFoundError:
        logger.warning(f"User '{username}' not found in Neo4j")
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    except Exception as e:
        logger.error(f"Error retrieving followings for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
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
    user1 = normalize_username(user1)
    user2 = normalize_username(user2)
    logger.info(f"GET /mutual - user1: {user1}, user2: {user2}")
    
    client = APIClient(settings)
    try:
        result = client.get_mutual_followings(user1, user2)
        if result.get("status") != "success":
            detail = result.get("error") or result.get("msg") or "Unknown error fetching mutuals"
            logger.error(f"Mutual followings fetch failed for {user1} and {user2}: {detail}")
            raise HTTPException(status_code=400, detail=detail)
        # result["data"]["mutuals"] is a list of dicts
        mutuals_count = len(result["data"].get("mutuals", []))
        logger.info(f"Successfully retrieved {mutuals_count} mutual followings for {user1} and {user2}")
        return MutualsResponse(status="success", mutuals=[MutualUser(**item) for item in result["data"].get("mutuals", [])])
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get("error", str(e))
        logger.error(f"HTTP error fetching mutuals for {user1} and {user2}: {error_detail}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Mutuals fetch failed: {error_detail}")
    except Exception as e:
        logger.error(f"Unexpected error fetching mutuals for {user1} and {user2}: {e}")
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
    username = normalize_username(payload.userName)
    logger.info(f"POST /sync - username: {username}")
    
    try:
        result = client.sync_user_followings(username)
        status = result.get("status", "unknown")
        logger.info(f"Sync completed for user {username} with status: {status}")
        return SyncResponse(status=status)
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get("error", str(e))
        logger.error(f"HTTP error during sync for user {username}: {error_detail}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Sync failed: {error_detail}")
    except Exception as e:
        logger.error(f"Unexpected error during sync for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    

@app.get("/health")
def health():
    """
    Simple health check endpoint for Docker and monitoring.
    Returns 200 if the service is up.
    """
    return {"status": "ok"}