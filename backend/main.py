import os
import logging
from daphne.server import Server

from src.service.app import app


def main() -> None:
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

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
