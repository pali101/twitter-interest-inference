from functools import lru_cache
from typing import List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # twitter_api_token: SecretStr = Field(..., alias='TWITTER_API_TOKEN')

    # Neo4j
    neo4j_uri: str = Field(default=..., validation_alias="NEO4J_URI")
    neo4j_user: str = Field(default=..., validation_alias="NEO4J_USERNAME")
    neo4j_password: SecretStr = Field(default=..., validation_alias="NEO4J_PASSWORD")

    # Sync API
    neo4j_api_base_url: str = Field(
        default="http://localhost:4000", validation_alias="NEO4J_API_BASE_URL"
    )
    api_timeout: float = Field(default=300.0, validation_alias="API_TIMEOUT_SECONDS")

    # Interest extraction
    model_name: str = Field(
        # default="all-MiniLM-L6-v2", validation_alias="INTEREST_MODEL_NAME"
        default="paraphrase-mpnet-base-v2", validation_alias="INTEREST_MODEL_NAME"
    )
    categories: List[str] = Field(
        default_factory=lambda: [
            "blockchain",
            "cryptocurrency",
            "decentralized finance",
            "defi",
            "nft",
            "smart contracts",
            "ethereum",
            "bitcoin",
            "web3",
            "zero knowledge",
            "privacy",
            "machine learning",
            "deep learning",
            "artificial intelligence",
            "distributed systems",
            "filecoin",
            "ipfs",
            "peer-to-peer",
            "data analytics",
            "python",
            "rust",
            "go",
            "javascript",
            "solidity",
            "cryptography",
        ],
        validation_alias="INTEREST_CATEGORIES",
    )
    similarity_threshold: float = Field(gt=0.0, lt=1.0,default=0.4, validation_alias="SIMILARITY_THRESHOLD")
    top_n_extractor: int = Field(default=3, validation_alias="TOP_N_EXTRACTOR")
    return_scores: bool = Field(default=False, validation_alias="RETURN_SCORES")

    # Aggregator
    self_weight: float = Field(default=0.2, validation_alias="SELF_WEIGHT")
    followings_weight: float = Field(default=0.8, validation_alias="FOLLOWINGS_WEIGHT")
    top_n_aggregator: int = Field(default=5, validation_alias="TOP_N_AGGREGATOR")

@lru_cache()
def get_settings() -> Settings:
    """
    FastAPI dependency that returns a singleton Settings instance,
    loading from .env and environment variables on first call.
    """
    return Settings()