from typing import List, Tuple, Union

from .api_client import APIClient
from .neo4j_client import Neo4jClient
from .interest_extractor import InterestExtractor
from .aggregation import InterestAggregator
from .logging_config import get_logger

logger = get_logger(__name__)

class UserNotFoundError(Exception):
    pass

def infer_interests(username: str, settings) -> Union[List[str], List[Tuple[str, float]]]:
    user = username.lower()
    logger.info(f"Starting interest inference for user: {user}")
    
    try:
        # Sync user followings
        logger.debug("Initializing API client for user sync")
        api = APIClient(settings)
        api.sync_user_followings(user)

        # Get data from Neo4j
        logger.debug("Initializing Neo4j client to fetch user data")
        neo4j = Neo4jClient(settings)
        try:
            followings = neo4j.get_followings_with_bios(user)
            if followings is None:
                logger.error(f"User {user} not found in Neo4j")
                raise UserNotFoundError(f"User {user} not found in Neo4j")
                
            logger.info(f"Found {len(followings)} followings for user {user}")
            
            # Extract interests
            logger.debug("Initializing interest extractor")
            extractor = InterestExtractor(settings)
            
            user_bio = neo4j.get_user_bio(user)
            user_interests = extractor.extract_interest_from_bio(user_bio, username=user)
            logger.debug(f"Extracted {len(user_interests)} interests from user bio")
            
            followings_interests = [
                extractor.extract_interest_from_bio(f["bio"], username=f["username"]) for f in followings
            ]
            logger.debug(f"Extracted interests from {len(followings_interests)} following bios")
            
            # Aggregate results
            logger.debug("Starting interest aggregation")
            aggregator = InterestAggregator(settings)
            result = aggregator.aggregate(user_interests, followings_interests)
            
            logger.info(f"Successfully completed interest inference for user {user}")
            return result
            
        finally:
            neo4j.close()
            
    except Exception as e:
        logger.error(f"Error during interest inference for user {user}: {e}")
        raise
