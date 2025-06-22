from typing import List, Tuple, Union

from .api_client import APIClient
from .neo4j_client import Neo4jClient
from .interest_extractor import InterestExtractor
from .aggregation import InterestAggregator

class UserNotFoundError(Exception):
    pass

def infer_interests(username: str, settings) -> Union[List[str], List[Tuple[str, float]]]:
    user = username.lower()
    api = APIClient(settings)
    api.sync_user_followings(user)

    neo4j = Neo4jClient(settings)
    try:
        followings = neo4j.get_followings_with_bios(user)
        if followings is None:
            raise UserNotFoundError(f"User {user} not found in Neo4j")
        extractor = InterestExtractor(settings)
        user_bio = neo4j.get_user_bio(user)
        user_interests = extractor.extract_interest_from_bio(user_bio)
        followings_interests = [
            extractor.extract_interest_from_bio(f["bio"]) for f in followings
        ]
        aggregator = InterestAggregator(settings)
        return aggregator.aggregate(user_interests, followings_interests)
    finally:
        neo4j.close()
