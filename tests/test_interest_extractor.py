import pytest
from twitter_interest.interest_extractor import InterestExtractor
from twitter_interest.settings import Settings

@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://dummy")
    monkeypatch.setenv("NEO4J_USERNAME", "dummy")
    monkeypatch.setenv("NEO4J_PASSWORD", "dummy")
    monkeypatch.setenv("INTEREST_MODEL_NAME", "all-MiniLM-L6-v2")
    return Settings()

@pytest.fixture
def extractor(settings):
    return InterestExtractor(settings)

def test_extract_from_meaningful_bio(extractor):
    bio = "I work on decentralized finance and smart contracts with Ethereum."
    interests = extractor.extract_interest_from_bio(bio)
    assert isinstance(interests, list)
    assert any("decentralized finance" in i or "smart contracts" in i for i in interests)

@pytest.mark.parametrize("bio", ["", " ", "   "])
def test_empty_bio_returns_empty_list(extractor, bio):
    assert extractor.extract_interest_from_bio(bio) == []

def test_top_n_limit(extractor):
    bio = "Machine learning, blockchain, cryptography and distributed systems are my interests."
    interests = extractor.extract_interest_from_bio(bio, top_n=2)
    assert len(interests) <= 2

def test_similarity_threshold_filtering(extractor):
    bio = "I love gardening and baking cakes on weekends."  # unlikely to match tech categories
    interests = extractor.extract_interest_from_bio(bio, similarity_threshold=0.9)
    assert interests == []

def test_exact_category_match(extractor):
    bio = "python"
    interests = extractor.extract_interest_from_bio(bio)
    assert "python" in interests

def test_multi_category_bio(extractor):
    bio = "I'm working on IPFS, cryptography, smart contracts, and Rust-based blockchain nodes."
    interests = extractor.extract_interest_from_bio(bio)
    expected = {"ipfs", "cryptography", "smart contracts", "rust"}
    assert expected.intersection(set(interests))