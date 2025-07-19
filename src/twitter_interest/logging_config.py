"""
Centralized logging configuration for Twitter Interest Inference using Loguru.
"""
import sys
from pathlib import Path
from loguru import logger
import logging

def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    enable_file_logging: bool = True,
    enable_rotation: bool = True,
    max_file_size: str = "10 MB",
    retention: str = "7 days"
) -> None:
    """
    Setup centralized logging configuration using Loguru.
    
    Args:
        level: Logging level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, uses default location
        enable_file_logging: Whether to enable file logging
        enable_rotation: Whether to enable log file rotation
        max_file_size: Maximum size per log file (e.g., "10 MB", "100 KB")
        retention: How long to keep log files (e.g., "7 days", "2 weeks")
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler for INFO, DEBUG, SUCCESS (and others if level allows) to stdout
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
        filter=lambda record: record["level"].no < logger.level("WARNING").no # Filter out WARNING and above
    )

    # Add console handler for WARNING, ERROR, CRITICAL to stderr
    # This sink will only capture messages at WARNING level or higher
    logger.add(
        sys.stderr,
        format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="WARNING", # Always start capturing from WARNING for stderr
        colorize=True
    )

    # Add file handler if enabled
    if enable_file_logging:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        if log_file is None:
            log_file = str(log_dir / "twitter_interest.log")
        
        if enable_rotation:
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                rotation=max_file_size,
                retention=retention,
                compression="zip",
                serialize=True
            )
        else:
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                serialize=True
            )
    
    # Suppress noisy third-party loggers by intercepting stdlib logging
    _intercept_stdlib_logging()


def _intercept_stdlib_logging():
    """
    Intercept standard library logging and redirect to loguru.
    This helps manage third-party libraries that use stdlib logging.
    """
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level if it exists
            level: str | int
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Set up interception for noisy third-party libraries
    noisy_loggers = [
        "neo4j",
        "requests", 
        "urllib3",
        "sentence_transformers",
        "transformers",
        "torch",
        "uvicorn.access"  # Suppress FastAPI access logs in production
    ]
    
    for logger_name in noisy_loggers:
        stdlib_logger = logging.getLogger(logger_name)
        stdlib_logger.handlers = [InterceptHandler()]
        stdlib_logger.setLevel(logging.WARNING)
        stdlib_logger.propagate = False


def get_logger(name: str):
    """
    Get a logger instance. With loguru, this is just the global logger 
    but bound to the module name for context.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        Loguru logger bound to the module name
    """
    return logger.bind(name=name)


# For backward compatibility and convenience
def configure_production_logging():
    """Configure logging optimized for production environments."""
    setup_logging(
        level="INFO",
        enable_file_logging=True,
        enable_rotation=True,
        max_file_size="50 MB",
        retention="30 days"
    )


def configure_development_logging():
    """Configure logging optimized for development."""
    setup_logging(
        level="DEBUG",
        enable_file_logging=True,
        enable_rotation=False
    )
