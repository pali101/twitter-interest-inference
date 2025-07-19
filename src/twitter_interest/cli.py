from .settings import Settings
from .logging_config import setup_logging, get_logger
import time
import typer

logger = get_logger(__name__)

app = typer.Typer(
    help="Twitter Interest Inference - Analyze a Twitter user's interests."
)

def _run(userName: str, settings: Settings):
    from .api_client import APIClient
    from .neo4j_client import Neo4jClient
    from .interest_extractor import InterestExtractor
    from .aggregation import InterestAggregator

    user = userName.lower()
    logger.info(f"Starting analysis for user: @{user}")

    start_total = time.perf_counter()

    # 1) Sync
    sync_start = time.perf_counter()
    logger.info("Starting user followings sync...")
    api = APIClient(settings)
    try:
        api.sync_user_followings(user)
        sync_end = time.perf_counter()
        logger.info(f"Sync completed in {sync_end - sync_start:.2f} seconds")
        typer.echo(f"Sync completed in {sync_end - sync_start:.2f} seconds")
    except Exception as e:
        logger.error(f"Failed to sync user followings: {e}")
        typer.secho(f"Error: Failed to sync user followings: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # 2) fetch and extract
    logger.info("Fetching followings and bios from Neo4j...")
    typer.echo("Fetching followings and bios from Neo4j…")
    fetch_start = time.perf_counter()
    neo4j = Neo4jClient(settings)
    try:
        followings = neo4j.get_followings_with_bios(user)
        logger.info(f"Fetched {len(followings)} followings from Neo4j")
        typer.echo(f"{len(followings)} followings fetched")

        fetch_end = time.perf_counter()
        logger.debug(f"Data fetch took {fetch_end - fetch_start:.2f} seconds")
        typer.echo(f"Data fetch took {fetch_end - fetch_start:.2f} seconds")

        extract_start = time.perf_counter()
        extractor = InterestExtractor(settings)
        user_bio = neo4j.get_user_bio(user)
        logger.debug(f"User bio: {user_bio[:100]}..." if user_bio else "No user bio found")
        
        user_interests = extractor.extract_interest_from_bio(user_bio)
        logger.debug(f"Extracted user interests: {user_interests}")

        followings_interests = [
            extractor.extract_interest_from_bio(f["bio"]) for f in followings
        ]
        logger.info(f"Extracted interests using model {settings.model_name}")
        typer.echo(f"Extracted interests using model {settings.model_name}")
        extract_end = time.perf_counter()
        logger.debug(f"Interest extraction for user and all followings took {extract_end - extract_start:.2f} seconds")
        typer.echo(
            f"Interest extraction for user and all followings took {extract_end - extract_start:.2f} seconds"
        )

        agg_start = time.perf_counter()
        aggregator = InterestAggregator(settings)
        top_interests = aggregator.aggregate(user_interests, followings_interests)
        agg_end = time.perf_counter()
        logger.debug(f"Aggregation completed in {agg_end - agg_start:.2f} seconds")
        typer.echo(f"Aggregation completed in {agg_end - agg_start:.2f} seconds")

        logger.info(f"Analysis completed for @{user}. Top interests: {top_interests}")
        typer.secho(
            f"Top interests for @{user}: {top_interests}", fg=typer.colors.GREEN
        )
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        typer.secho(f"Error: Analysis failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    finally:
        neo4j.close()

    end_total = time.perf_counter()
    logger.info(f"Total execution time: {end_total - start_total:.2f} seconds")
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging (DEBUG level)",
    ),
):
    """
    Analyze a Twitter user's followings and infer their top interests.
    """
    settings = Settings()
    
    # Setup logging based on verbosity
    log_level = "DEBUG" if verbose else settings.log_level
    setup_logging(
        level=log_level,
        log_file=settings.log_file,
        enable_file_logging=settings.enable_file_logging,
        enable_rotation=settings.enable_log_rotation,
        max_file_size=settings.max_log_file_size,
        retention=settings.log_retention
    )
    
    if model:
        settings.model_name = model
        logger.info(f"Using model override: {model}")
    
    _run(user_name, settings)


def main():
    app()


if __name__ == "__main__":
    main()
