from neo4j import GraphDatabase
from .settings import Settings
from .logging_config import get_logger

logger = get_logger(__name__)

class Neo4jClient:
    def __init__(self, settings: Settings):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()))
        logger.debug(f"Initialized Neo4j connection to {settings.neo4j_uri}")

    def get_followings_with_bios(self, user_id):
        """
        Fetches all followings for a given user (by id), returning their id and bio.
        """
        query = (
            "MATCH (u:User {id: $user_id})-[:FOLLOWS]->(f:User) "
            "RETURN f.id AS username, f.bio AS bio"
        )
        logger.debug(f"Fetching followings with bios for user: {user_id}")
        
        try:
            with self.driver.session() as session:
                results = session.run(query, user_id=user_id)
                followings = [{"username": record["username"], "bio": record["bio"] or ""} for record in results]
                logger.info(f"Retrieved {len(followings)} followings for user {user_id}")
                logger.debug(f"Followings data: {followings[:3]}..." if followings else "No followings found")
                return followings
        except Exception as e:
            logger.error(f"Error fetching followings for user {user_id}: {e}")
            raise
   
    def get_user_bio(self, user_id):
        """
        Fetches the bio of a single user by their id.
        """
        query = (
            "MATCH (u:User {id: $user_id}) "
            "RETURN u.bio AS bio"
        )
        logger.debug(f"Fetching bio for user: {user_id}")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id).single()
                bio = result["bio"] if result and result["bio"] else ""
                logger.debug(f"Retrieved bio for user {user_id}: {bio[:100]}..." if bio else f"No bio found for user {user_id}")
                return bio
        except Exception as e:
            logger.error(f"Error fetching bio for user {user_id}: {e}")
            raise

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
        logger.debug(f"Fetching up to {max_records} followings with bios for user: {username}")
        
        try:
            with self.driver.session() as session:
                results = session.run(query, username=username, max_records=max_records)
                followings = [{"username": record["username"], "bio": record["bio"] or ""} for record in results]
                logger.info(f"Retrieved {len(followings)} followings (limited to {max_records}) for user {username}")
                return followings
        except Exception as e:
            logger.error(f"Error fetching limited followings for user {username}: {e}")
            raise

    def close(self):
        logger.debug("Closing Neo4j driver connection")
        self.driver.close()