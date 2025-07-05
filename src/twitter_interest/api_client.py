import requests
from .settings import Settings

class APIClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.network_sync_url
        self.timeout = settings.api_timeout

    def sync_user_followings(self, userName):
        url = f"{self.base_url}/api/sync"
        res = requests.post(url, json={"userName": userName}, timeout=self.timeout)
        res.raise_for_status()
        return res.json()
    
    def store_user_in_Neo4j(self, userName):
        url = f"{self.base_url}/api/user/store"
        res = requests.post(url, json={"userName": userName})
        res.raise_for_status()
        return res.json()

    def get_mutual_followings(self, user1, user2):
        """
        Calls the /api/mutual endpoint to get mutual followings of two users.
        """
        url = f"{self.base_url}/api/mutual"
        params = {"user1": user1, "user2": user2}
        res = requests.get(url, params=params, timeout=self.timeout)
        res.raise_for_status()
        return res.json()