from neo4j import GraphDatabase
from .settings import Settings

class Neo4jClient:
    def __init__(self, settings: Settings):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()))

    def get_followings_with_bios(self, user_id):
        """
        Fetches all followings for a given user (by id), returning their id and bio.
        """
        query = (
            "MATCH (u:User {id: $user_id})-[:FOLLOWS]->(f:User) "
            "RETURN f.id AS id, f.bio AS bio"
        )
        with self.driver.session() as session:
            results = session.run(query, user_id=user_id)
            return [{"id": record["id"], "bio": record["bio"] or ""} for record in results]
   
    def get_user_bio(self, user_id):
        """
        Fetches the bio of a single user by their id.
        """
        query = (
            "MATCH (u:User {id: $user_id}) "
            "RETURN u.bio AS bio"
        )
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id).single()
            return result["bio"] if result and result["bio"] else ""

    def get_followings_usernames_with_bios_limit(self, username: str, max_records: int = 10):
        """
        Fetches the usernames and bios of users that the specified username follows.
        
        Args:
            username (str): The username of the user whose followings you want to fetch.
            max_records (int): The maximum number of records to return.
            
        Returns:
            List[dict]: List of dicts with 'username' and 'bio' keys.
        """
        query = (
            "MATCH (u:User {id: $username})-[:FOLLOWS]->(f:User) "
            "RETURN f.id AS username, f.bio AS bio "
            "LIMIT $max_records"
        )
        with self.driver.session() as session:
            results = session.run(query, username=username, max_records=max_records)
            return [{"username": record["username"], "bio": record["bio"] or ""} for record in results]


    def close(self):
        self.driver.close()