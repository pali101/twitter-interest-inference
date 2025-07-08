# Twitter Interest Inference Backend

This backend service analyzes a Twitter user's top interests by examining their bio and the bios of the people they follow. It powers both an API and a CLI for inferring interests using advanced language models and graph data.

## Features

- **Interest Extraction**: Uses Sentence Transformers to match Twitter bios to a set of pre-defined interest categories.
- **Interest Aggregation**: A user's top interests are derived from their own bio (20% weight) and the bios of the people they follow (80% weight).
- **API and CLI**: Exposes endpoints and commands to fetch and infer interests for any Twitter username.
- **Neo4j Integration**: Stores and queries user/following relationships and bios.
- **Highly Configurable**: Easily adjust models, interest categories, weights, and thresholds via environment variables.

## How it works

1. **Sync**: When analyzing a username, the service first syncs their followings and bios from a remote API to Neo4j.
2. **Extract Interests**: 
    - The user's bio is embedded using a Sentence Transformer and matched to a list of interest categories.
    - Each profile the user follows, their bio is processed the same way.
3. **Aggregate**:
    - The user's own detected interests are given 20% weight.
    - Interests extracted from all followings' bios are combined and given 80% weight.
    - The final interests list is sorted by these weighted scores.

## Interest Extraction and Aggregation

The core of this service lies in its ability to extract and aggregate interests for any given Twitter user. Interest extraction is performed using state-of-the-art Sentence Transformer models, which analyze a user's bio and compare it to a curated list of interest categories (such as “blockchain” “decentralized finance” “machine learning”) by computing semantic similarity scores. This process is also applied to the bios of all the user’s followings, capturing the broader context of their network. Aggregation then combines these results using a weighted scheme: a user's own bio determines 20% of the final interest profile, while the remaining 80% is derived from the interests detected in their followings' bios. This approach ensures that the inferred interests reflect not only the user’s self-described focus, but also the communities and topics they are most connected to.

## API Endpoints

- `GET /interests/{username}` – Get top inferred interests for a user.
- `GET /followings/{username}` – List followings' bios.
- `GET /mutual` – Find mutual followings of two provided usernames.
- `POST /sync` – Sync a user's followings.

