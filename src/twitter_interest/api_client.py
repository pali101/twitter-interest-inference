import requests
from .settings import Settings
from .logging_config import get_logger

logger = get_logger(__name__)

class APIClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.network_sync_url
        self.timeout = settings.api_timeout
        logger.debug(f"Initialized APIClient with base_url: {self.base_url}, timeout: {self.timeout}")

    def sync_user_followings(self, userName):
        url = f"{self.base_url}/api/sync"
        payload = {"userName": userName}
        logger.info(f"Syncing followings for user: {userName}")
        logger.debug(f"Making POST request to {url} with payload: {payload}")
        
        try:
            res = requests.post(url, json=payload, timeout=self.timeout)
            res.raise_for_status()
            result = res.json()
            logger.info(f"Successfully synced followings for user: {userName}")
            logger.debug(f"Sync response: {result}")
            return result
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while syncing followings for user: {userName}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while syncing followings for user {userName}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while syncing followings for user {userName}: {e}")
            raise
    
    def store_user_in_Neo4j(self, userName):
        url = f"{self.base_url}/api/user/store"
        payload = {"userName": userName}
        logger.info(f"Storing user in Neo4j: {userName}")
        logger.debug(f"Making POST request to {url} with payload: {payload}")
        
        try:
            res = requests.post(url, json=payload)
            res.raise_for_status()
            result = res.json()
            logger.info(f"Successfully stored user in Neo4j: {userName}")
            logger.debug(f"Store response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while storing user {userName} in Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while storing user {userName} in Neo4j: {e}")
            raise

    def get_mutual_followings(self, user1, user2):
        """
        Calls the /api/mutual endpoint to get mutual followings of two users.
        """
        url = f"{self.base_url}/api/mutual"
        params = {"user1": user1, "user2": user2}
        logger.info(f"Getting mutual followings between {user1} and {user2}")
        logger.debug(f"Making GET request to {url} with params: {params}")
        
        try:
            res = requests.get(url, params=params, timeout=self.timeout)
            res.raise_for_status()
            result = res.json()
            logger.info(f"Successfully retrieved mutual followings between {user1} and {user2}")
            logger.debug(f"Mutual followings response: {result}")
            return result
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while getting mutual followings between {user1} and {user2}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while getting mutual followings between {user1} and {user2}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting mutual followings between {user1} and {user2}: {e}")
            raise