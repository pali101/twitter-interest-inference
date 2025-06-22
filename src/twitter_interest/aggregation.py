from collections import Counter, defaultdict
from typing import List, Tuple, Union
from .settings import Settings

class InterestAggregator:
    def __init__(self, settings: Settings):
        self.settings = settings
        total = settings.self_weight + settings.followings_weight
        self.self_weight = settings.self_weight / total
        self.followings_weight = settings.followings_weight / total

    def aggregate(
            self,
            user_interests: list[str],
            followings_interests_list: list[list[str]],
            top_n: int | None = None,
            return_scores: bool = False
    ) -> Union[List[str], List[Tuple[str, float]]]:
        top_n = top_n or self.settings.top_n_aggregator
        return_scores = return_scores or self.settings.return_scores
        
        all_interests = []

        # Flatten all followings' interests into one list
        for interests in followings_interests_list:
            all_interests.extend(interests)

        # Count followings interests
        followings_counter = Counter(all_interests)
        total_followings = sum(followings_counter.values())

        # Count self interests
        self_counter = Counter(user_interests)
        total_self = sum(self_counter.values())

        # Combine with weights
        combined: dict[str, float] = defaultdict(float)

        # Scale based on weightage
        for interest, count in self_counter.items():
            if total_self > 0:
                combined[interest] += (count / total_self) * self.self_weight

        for interest, count in followings_counter.items():
            if total_followings > 0:
                combined[interest] += (count / total_followings) * self.followings_weight

        # Return top_n sorted interests (by weighted score)
        top = sorted(
            combined.items(),
            key=lambda pair: pair[1],
            reverse=True
        )[:top_n]

        if return_scores:
            return top
        else: 
            return [interest for interest, _ in top]