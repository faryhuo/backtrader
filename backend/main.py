import os
import logging
import multiprocessing
from urllib.parse import urlparse, urlunparse

import uvicorn

from api import app
from src.config.settings import DATABASE_URL, get_sqlite_db_path_from_url
from src.utils.logger import setup_logging


def mask_database_url(url: str) -> str:
    """Mask password in database URL to prevent sensitive information leakage.
    
    Examples:
        postgresql://user:secret@localhost:5432/db -> postgresql://user:****@localhost:5432/db
        sqlite:///path/to/db.sqlite -> sqlite:///path/to/db.sqlite (no change)
    """
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Reconstruct netloc with masked password
            if parsed.port:
                masked_netloc = f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
            else:
                masked_netloc = f"{parsed.username}:****@{parsed.hostname}"
            masked_url = urlunparse((
                parsed.scheme,
                masked_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return masked_url
        return url
    except Exception:
        # If parsing fails, return a safe generic message
        return f"{url.split('://')[0]}://***masked***" if '://' in url else "***masked***"


def main() -> None:
    multiprocessing.freeze_support()

    # Configure logging from config file
    setup_logging()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Log database configuration (with masked password)
    logging.info(f"Database URL: {mask_database_url(DATABASE_URL)}")
    db_path = get_sqlite_db_path_from_url(DATABASE_URL)
    if db_path is not None:
        logging.info(f"Database absolute path: {db_path.resolve()}")

    logging.info(f"Starting Uvicorn server on {host}:{port} with log level {log_level}")
    
    # Use Uvicorn - properly triggers FastAPI startup/shutdown events
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()

