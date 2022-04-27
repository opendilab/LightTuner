import logging

from rich.logging import RichHandler

from ditk import hpo as _ditk_hpo_module

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%m-%d %H:%M:%S]", handlers=[
        RichHandler(rich_tracebacks=True, markup=True, tracebacks_suppress=[_ditk_hpo_module])
    ]
)

logger = logging.getLogger()


def escape(s: str) -> str:
    return s.replace('[', '\\[')
