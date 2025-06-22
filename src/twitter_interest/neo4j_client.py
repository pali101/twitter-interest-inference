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

    def close(self):
        self.driver.close()