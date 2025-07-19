import pytest
from twitter_interest.service import infer_interests, UserNotFoundError

@pytest.fixture
def dummy_settings(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://dummy")
    monkeypatch.setenv("NEO4J_USERNAME", "user")
    monkeypatch.setenv("NEO4J_PASSWORD", "pass")
    monkeypatch.setenv("INTEREST_MODEL_NAME", "all-MiniLM-L6-v2")
    return __import__('twitter_interest.settings').settings.Settings()

def test_infer_interests_success(mocker, dummy_settings):
    # Mock everything
    mock_api = mocker.patch("twitter_interest.service.APIClient")
    mock_neo = mocker.patch("twitter_interest.service.Neo4jClient")
    mock_ext = mocker.patch("twitter_interest.service.InterestExtractor")
    mock_agg = mocker.patch("twitter_interest.service.InterestAggregator")

    # Configure API mock
    mock_api.return_value.sync_user_followings.return_value = None

    # Configure Neo4j mock
    mock_neo_instance = mock_neo.return_value
    mock_neo_instance.get_followings_with_bios.return_value = [
        {"bio": "crypto and AI", "username": "user1"}, {"bio": "solidity and rust", "username": "user2"}
    ]
    mock_neo_instance.get_user_bio.return_value = "I love decentralized finance"

    # Configure extractor
    mock_ext_instance = mock_ext.return_value
    mock_ext_instance.extract_interest_from_bio.side_effect = [
        ["defi", "crypto"],              # user bio
        ["crypto", "ai"],                # follower 1
        ["solidity", "rust"]             # follower 2
    ]

    # Configure aggregator
    mock_agg_instance = mock_agg.return_value
    mock_agg_instance.aggregate.return_value = ["crypto", "defi", "ai"]

    result = infer_interests("Alice", dummy_settings)
    assert result == ["crypto", "defi", "ai"]

def test_infer_interests_with_scores(mocker, dummy_settings):
    mocker.patch("twitter_interest.service.APIClient")
    mock_neo = mocker.patch("twitter_interest.service.Neo4jClient")
    mock_ext = mocker.patch("twitter_interest.service.InterestExtractor")
    mock_agg = mocker.patch("twitter_interest.service.InterestAggregator")

    dummy_settings.return_scores = True

    mock_neo_instance = mock_neo.return_value
    mock_neo_instance.get_followings_with_bios.return_value = [{"bio": "rust", "username": "alice"}]
    mock_neo_instance.get_user_bio.return_value = "smart contracts"

    mock_ext_instance = mock_ext.return_value
    mock_ext_instance.extract_interest_from_bio.side_effect = [["solidity"], ["rust"]]

    mock_agg_instance = mock_agg.return_value
    mock_agg_instance.aggregate.return_value = [("solidity", 0.6), ("rust", 0.4)]

    result = infer_interests("Bob", dummy_settings)

    assert isinstance(result, list)
    assert isinstance(result[0], tuple)
    assert result[0][0] == "solidity"

def test_infer_interests_no_followings(mocker, dummy_settings):
    mocker.patch("twitter_interest.service.APIClient")
    mock_neo = mocker.patch("twitter_interest.service.Neo4jClient")
    mock_ext = mocker.patch("twitter_interest.service.InterestExtractor")
    mock_agg = mocker.patch("twitter_interest.service.InterestAggregator")

    mock_neo_instance = mock_neo.return_value
    mock_neo_instance.get_followings_with_bios.return_value = []
    mock_neo_instance.get_user_bio.return_value = "cryptography and privacy"

    mock_ext_instance = mock_ext.return_value
    mock_ext_instance.extract_interest_from_bio.side_effect = [["cryptography", "privacy"]]

    mock_agg_instance = mock_agg.return_value
    mock_agg_instance.aggregate.return_value = ["cryptography", "privacy"]

    result = infer_interests("EmptyUser", dummy_settings)

    assert result == ["cryptography", "privacy"]

def test_infer_interests_ignores_empty_follower_bios_and_uses_user_bio_only(mocker, dummy_settings):
    mocker.patch("twitter_interest.service.APIClient")
    mock_neo = mocker.patch("twitter_interest.service.Neo4jClient")
    mock_ext = mocker.patch("twitter_interest.service.InterestExtractor")
    mock_agg = mocker.patch("twitter_interest.service.InterestAggregator")
    mock_api = mocker.patch("twitter_interest.service.APIClient")

    mock_neo_instance = mock_neo.return_value
    mock_neo_instance.get_followings_with_bios.return_value = [{"bio": "", "username": "user1"}]
    mock_neo_instance.get_user_bio.return_value = "python developer"

    mock_ext_instance = mock_ext.return_value
    mock_ext_instance.extract_interest_from_bio.side_effect = [["python"], []]

    mock_agg_instance = mock_agg.return_value
    mock_agg_instance.aggregate.return_value = ["python"]

    result = infer_interests("DevUser", dummy_settings)

    mock_api.return_value.sync_user_followings.assert_called_once_with("devuser")
    assert result == ["python"]

def test_infer_interests_closes_neo4j_on_exception(mocker, dummy_settings):
    mocker.patch("twitter_interest.service.APIClient")

    mock_neo = mocker.patch("twitter_interest.service.Neo4jClient")
    mock_ext = mocker.patch("twitter_interest.service.InterestExtractor")
    mock_neo_instance = mock_neo.return_value
    mock_neo_instance.get_followings_with_bios.return_value = [{"bio": "", "username": "user1"}]
    mock_neo_instance.get_user_bio.return_value = "python developer"

    mock_ext_instance = mock_ext.return_value
    mock_ext_instance.extract_interest_from_bio.side_effect = RuntimeError("Extractor failed")

    with pytest.raises(RuntimeError, match="Extractor failed"):
        infer_interests("DevUser", dummy_settings)

    mock_neo_instance.close.assert_called_once()