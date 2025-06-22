from sentence_transformers import SentenceTransformer, util
import numpy as np
from .settings import Settings

class InterestExtractor:
    # lightweight model - all-MiniLM-L6-v2
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = SentenceTransformer(settings.model_name)
        self.categories = settings.categories
        self.category_embeddings = self.model.encode(self.categories, normalize_embeddings=True)

    def extract_interest_from_bio(
        self, 
        bio: str, 
        top_n: int | None = None, 
        similarity_threshold: float | None = None
    ) -> list[str]:
        top_n = top_n or self.settings.top_n_extractor
        similarity_threshold = similarity_threshold or self.settings.similarity_threshold

        if not bio.strip():
            return []
        
        bio_embedding = self.model.encode([bio], normalize_embeddings=True)[0]
        similarities = util.cos_sim(bio_embedding, self.category_embeddings)[0].cpu().numpy()
        sorted_indices = np.argsort(similarities)[::-1]
        interests = []
        for idx in sorted_indices[:top_n]:
            if similarities[idx] >= similarity_threshold:
                interests.append(self.categories[idx])
        return interests
