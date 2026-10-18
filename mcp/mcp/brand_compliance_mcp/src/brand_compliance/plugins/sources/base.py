"""Checks shared by every guide reader (Markdown now; PDF, JSON, ... later)."""

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from brand_compliance.core.errors import InvalidInputError, ParseFailedError

logger = logging.getLogger(__name__)

DEFAULT_MAX_BYTES: Final = 5_000_000


def read_source_text(
    path: Path,
    suffixes: Iterable[str],
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Read a text guide after checking type, size and encoding.

    Raises ``InvalidInputError`` for a missing, wrong-type or oversized file and
    ``ParseFailedError`` when it is not valid UTF-8 text.
    """
    if not path.is_file():
        raise InvalidInputError(f"Not a file: {path.name}")
    if path.suffix.lower() not in {s.lower() for s in suffixes}:
        raise InvalidInputError(f"Unsupported file type: {path.suffix!r}")
    size = path.stat().st_size
    if size > max_bytes:
        raise InvalidInputError(f"File too large: {size} bytes (limit {max_bytes})")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        logger.error("Guide %s is not valid UTF-8", path.name)
        raise ParseFailedError(f"{path.name} is not valid UTF-8 text") from exc
