import os
import logging
from urllib.parse import urlparse, urlunparse
from daphne.server import Server

from api import app
from src.config.settings import DATABASE_URL, DEFAULT_DB_PATH
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
    # Configure logging from config file
    setup_logging()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Log database configuration (with masked password)
    logging.info(f"Database URL: {mask_database_url(DATABASE_URL)}")
    logging.info(f"Database absolute path: {DEFAULT_DB_PATH.absolute()}")

    logging.info(f"Starting server on {host}:{port} with log level {log_level}")
    
    server = Server(
        application=app,
        endpoints=[f"tcp:port={port}:interface={host}"],
        signal_handlers=True,
        verbosity=1 if log_level == "INFO" else 2,  # 1=INFO, 2=DEBUG
    )
    server.run()


if __name__ == "__main__":
    main()
