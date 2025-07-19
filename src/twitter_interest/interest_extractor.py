from sentence_transformers import SentenceTransformer, util
import numpy as np
from .settings import Settings
from .logging_config import get_logger

logger = get_logger(__name__)

class InterestExtractor:
    # lightweight model - all-MiniLM-L6-v2
    def __init__(self, settings: Settings):
        self.settings = settings
        logger.info(f"Initializing InterestExtractor with model: {settings.model_name}")
        logger.debug(f"Available categories: {settings.categories}")
        
        try:
            self.model = SentenceTransformer(settings.model_name)
            logger.info(f"Successfully loaded SentenceTransformer model: {settings.model_name}")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {settings.model_name}: {e}")
            raise
            
        self.categories = settings.categories
        logger.debug("Encoding category embeddings...")
        self.category_embeddings = self.model.encode(self.categories, normalize_embeddings=True)
        logger.debug(f"Encoded {len(self.categories)} category embeddings")

    def extract_interest_from_bio(
        self, 
        bio: str, 
        username: str | None = None,
        top_n: int | None = None, 
        similarity_threshold: float | None = None
    ) -> list[str]:
        top_n = top_n or self.settings.top_n_extractor
        similarity_threshold = similarity_threshold or self.settings.similarity_threshold

        logger.debug(f"Extracting interests from bio: '{bio[:100]}...' with top_n={top_n}, threshold={similarity_threshold}")

        if not bio.strip():
            logger.debug("Empty bio provided, returning empty interests list")
            return []
        
        try:
            bio_embedding = self.model.encode([bio], normalize_embeddings=True)[0]
            similarities = util.cos_sim(bio_embedding, self.category_embeddings)[0].cpu().numpy()
            sorted_indices = np.argsort(similarities)[::-1]
            
            interests = []
            for idx in sorted_indices[:top_n]:
                similarity_score = similarities[idx]
                category = self.categories[idx]
                if similarity_score >= similarity_threshold:
                    interests.append(category)
                    logger.debug(f"Interest '{category}' matched with similarity {similarity_score:.3f}")
                else:
                    logger.debug(f"Category '{category}' below threshold: {similarity_score:.3f} < {similarity_threshold}")

            logger.info(f"[{username}] Extracted {len(interests)} interests from bio: {interests}")
            return interests
        except Exception as e:
            logger.error(f"[{username}] Error extracting interests from bio: {e}")
            raise
