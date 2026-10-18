"""Logging setup shared by every module.

Logs must never contain guide or artifact content; log run ids, rule ids and
counts only.
"""

import logging
from typing import Final

_LOG_FORMAT: Final[str] = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once, with a consistent format."""
    logging.basicConfig(level=level, format=_LOG_FORMAT)
