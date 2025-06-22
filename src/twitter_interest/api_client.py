import requests
from .settings import Settings

class APIClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.neo4j_api_base_url
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
