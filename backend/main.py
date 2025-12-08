import os
from daphne.server import Server
from api import app


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    server = Server(
        application=app,
        endpoints=[f"tcp:port={port}:interface={host}"],
        signal_handlers=True,
    )
    server.run()


if __name__ == "__main__":
    main()
