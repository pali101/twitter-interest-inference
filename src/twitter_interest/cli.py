from .settings import Settings
import time
import typer

app = typer.Typer(
    help="Twitter Interest Inference - Analyze a Twitter user's interests."
)

def _run(userName: str, settings: Settings):
    from .api_client import APIClient
    from .neo4j_client import Neo4jClient
    from .interest_extractor import InterestExtractor
    from .aggregation import InterestAggregator

    user = userName.lower()

    start_total = time.perf_counter()

    # 1) Sync
    sync_start = time.perf_counter()
    api = APIClient(settings)
    api.sync_user_followings(user)
    sync_end = time.perf_counter()
    typer.echo(f"Sync completed in {sync_end - sync_start:.2f} seconds")

    # 2) fetch and extract
    typer.echo("Fetching followings and bios from Neo4j…")
    fetch_start = time.perf_counter()
    neo4j = Neo4jClient(settings)
    try:
        followings = neo4j.get_followings_with_bios(user)
        typer.echo(f"{len(followings)} followings fetched")

        fetch_end = time.perf_counter()
        typer.echo(f"Data fetch took {fetch_end - fetch_start:.2f} seconds")

        extract_start = time.perf_counter()
        extractor = InterestExtractor(settings)
        user_bio = neo4j.get_user_bio(user)
        user_interests = extractor.extract_interest_from_bio(user_bio)

        followings_interests = [
            extractor.extract_interest_from_bio(f["bio"]) for f in followings
        ]
        typer.echo(f"Extracted interests using model {settings.model_name}")
        extract_end = time.perf_counter()
        typer.echo(
            f"Interest extraction for user and all followings took {extract_end - extract_start:.2f} seconds"
        )

        agg_start = time.perf_counter()
        aggregator = InterestAggregator(settings)
        top_interests = aggregator.aggregate(user_interests, followings_interests)
        agg_end = time.perf_counter()
        typer.echo(f"Aggregation completed in {agg_end - agg_start:.2f} seconds")

        typer.secho(
            f"Top interests for @{user}: {top_interests}", fg=typer.colors.GREEN
        )
    finally:
        neo4j.close()

    end_total = time.perf_counter()
    typer.echo(f"Total execution time: {end_total - start_total:.2f} seconds")


@app.command("analyze")
def analyze(
    user_name: str = typer.Argument(..., help="Twitter username (e.g., hc_protocol)"),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Override the model name (defaults to what's in Settings)",
    ),
):
    """
    Analyze a Twitter user's followings and infer their top interests.
    """
    settings = Settings()
    if model:
        settings.model_name = model
    _run(user_name, settings)


def main():
    app()


if __name__ == "__main__":
    main()
