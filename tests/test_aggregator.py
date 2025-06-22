import pytest
from twitter_interest.aggregation import InterestAggregator
from twitter_interest.settings import Settings
from typing import Tuple

@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://dummy")
    monkeypatch.setenv("NEO4J_USERNAME", "user")
    monkeypatch.setenv("NEO4J_PASSWORD", "pass")
    return Settings()

def test_aggregate_default(settings):
    """
    user_interests = ["a","b","b"]
    followings  = [["b","c"], ["c","c","a"]]
    Final scores (approx): c > b > a
    """
    user_interests = ["a", "b", "b"]
    followings = [["b", "c"], ["c", "c", "a"]]
    agg = InterestAggregator(settings)

    top = agg.aggregate(user_interests, followings, return_scores=False)
    assert isinstance(top, list)
    assert all(isinstance(x, str) for x in top)
    assert top[0] == "c"
    assert set(top) == {"a", "b", "c"}

def test_aggregate_with_scores(settings):
    """
    user_interests = ["x"]
    followings = [["x","y","y","z"]]
    x and y tie at top score (0.4), order may vary.
    """
    user_interests = ["x"]
    followings = [["x", "y", "y", "z"]]
    agg = InterestAggregator(settings)

    scored = agg.aggregate(user_interests, followings, return_scores=True)
    assert isinstance(scored, list)
    for name, score in scored:
        assert isinstance(name, str)
        assert isinstance(score, float)

    top_names = [x[0] for x in scored]
    assert "x" in top_names[:2]
    assert "y" in top_names[:2]

def test_empty_inputs(settings):
    agg = InterestAggregator(settings)
    result = agg.aggregate([], [], return_scores=False)
    assert result == []

def test_only_user_interests(settings):
    user_interests = ["a", "b", "b"]
    followings = []
    agg = InterestAggregator(settings)

    result = agg.aggregate(user_interests, followings, return_scores=False)
    assert result[0] == "b"
    assert set(result) == {"a", "b"}

def test_top_n_limit(settings):
    user_interests = ["a", "b", "c"]
    followings = [["b", "c", "d", "e", "f"]]
    agg = InterestAggregator(settings)

    result = agg.aggregate(user_interests, followings, top_n=3, return_scores=False)
    assert len(result) == 3

def test_top_n_exceeds_available(settings):
    user_interests = ["a"]
    followings = [["b", "c"]]
    agg = InterestAggregator(settings)

    result = agg.aggregate(user_interests, followings, top_n=10, return_scores=False)
    assert set(result) == {"a", "b", "c"}

def test_only_followings_interests(settings):
    user_interests = []
    followings = [["x", "y", "y", "z"]]
    agg = InterestAggregator(settings)

    result = agg.aggregate(user_interests, followings, return_scores=True)
    assert isinstance(result[0], tuple)
    assert result[0][1] > result[1][1] # type: ignore