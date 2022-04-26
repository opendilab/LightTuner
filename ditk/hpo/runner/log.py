import logging

from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%m-%d %H:%M:%S]", handlers=[
        RichHandler(rich_tracebacks=True)
    ]
)

logger = logging.getLogger()
