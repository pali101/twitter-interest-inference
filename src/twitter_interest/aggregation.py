from collections import Counter, defaultdict
from typing import List, Tuple, Union
from .settings import Settings
from .logging_config import get_logger

logger = get_logger(__name__)

class InterestAggregator:
    def __init__(self, settings: Settings):
        self.settings = settings
        total = settings.self_weight + settings.followings_weight
        self.self_weight = settings.self_weight / total
        self.followings_weight = settings.followings_weight / total
        
        logger.debug(f"Initialized InterestAggregator with weights - self: {self.self_weight:.3f}, followings: {self.followings_weight:.3f}")

    def aggregate(
            self,
            user_interests: list[str],
            followings_interests_list: list[list[str]],
            top_n: int | None = None,
            return_scores: bool = False
    ) -> Union[List[str], List[Tuple[str, float]]]:
        top_n = top_n or self.settings.top_n_aggregator
        return_scores = return_scores or self.settings.return_scores
        
        logger.info(f"Aggregating interests - user: {len(user_interests)} interests, followings: {len(followings_interests_list)} users")
        logger.debug(f"User interests: {user_interests}")
        logger.debug(f"Aggregation parameters - top_n: {top_n}, return_scores: {return_scores}")
        
        all_interests = []

        # Flatten all followings' interests into one list
        for interests in followings_interests_list:
            all_interests.extend(interests)

        # Count followings interests
        followings_counter = Counter(all_interests)
        total_followings = sum(followings_counter.values())
        logger.debug(f"Followings interests counter: {dict(followings_counter)}, total: {total_followings}")

        # Count self interests
        self_counter = Counter(user_interests)
        total_self = sum(self_counter.values())
        logger.debug(f"User interests counter: {dict(self_counter)}, total: {total_self}")

        # Combine with weights
        combined: dict[str, float] = defaultdict(float)

        # Scale based on weightage
        for interest, count in self_counter.items():
            if total_self > 0:
                weighted_score = (count / total_self) * self.self_weight
                combined[interest] += weighted_score
                logger.debug(f"User interest '{interest}': count={count}, weighted_score={weighted_score:.4f}")

        for interest, count in followings_counter.items():
            if total_followings > 0:
                weighted_score = (count / total_followings) * self.followings_weight
                combined[interest] += weighted_score
                logger.debug(f"Followings interest '{interest}': count={count}, weighted_score={weighted_score:.4f}")

        # Return top_n sorted interests (by weighted score)
        top = sorted(
            combined.items(),
            key=lambda pair: pair[1],
            reverse=True
        )[:top_n]

        logger.info(f"Final aggregated interests (top {len(top)}): {[f'{interest}:{score:.3f}' for interest, score in top]}")

        if return_scores:
            return top
        else: 
            return [interest for interest, _ in top]