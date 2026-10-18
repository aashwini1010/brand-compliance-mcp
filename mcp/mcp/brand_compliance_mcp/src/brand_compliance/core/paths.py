"""Safe handling of file paths received from outside the server."""

import logging
from collections.abc import Iterable
from pathlib import Path

from brand_compliance.core.errors import InvalidInputError, PathNotAllowedError

logger = logging.getLogger(__name__)


def resolve_within(path: str | Path, allowed_dirs: Iterable[str | Path]) -> Path:
    """Return the fully resolved path if it lies inside an allowed folder.

    Symlinks and ``..`` are resolved first, so they cannot escape the folders.
    Raises ``PathNotAllowedError`` otherwise.
    """
    resolved = Path(path).expanduser().resolve()
    for allowed in allowed_dirs:
        root = Path(allowed).expanduser().resolve()
        if resolved == root or resolved.is_relative_to(root):
            return resolved
    logger.warning("Rejected path outside allowed folders")
    raise PathNotAllowedError("Path is outside the allowed folders")


def validate_input_file(
    path: str | Path,
    allowed_dirs: Iterable[str | Path],
    max_bytes: int,
    suffixes: Iterable[str],
) -> Path:
    """Check an input file exists, is allowed, small enough and the right type."""
    resolved = resolve_within(path, allowed_dirs)
    if not resolved.is_file():
        raise InvalidInputError(f"Not a file: {resolved.name}")
    allowed_suffixes = {s.lower() for s in suffixes}
    if resolved.suffix.lower() not in allowed_suffixes:
        raise InvalidInputError(
            f"Unsupported file type {resolved.suffix!r}; "
            f"expected one of {sorted(allowed_suffixes)}"
        )
    size = resolved.stat().st_size
    if size > max_bytes:
        raise InvalidInputError(f"File too large: {size} bytes (limit {max_bytes})")
    return resolved


def validate_output_dir(
    path: str | Path,
    allowed_dirs: Iterable[str | Path],
    protected_files: Iterable[Path] = (),
) -> Path:
    """Check an output folder is allowed and does not contain protected files.

    ``protected_files`` are the inputs; an output folder that is, or holds,
    one of them is rejected so the originals can never be overwritten.
    """
    resolved = resolve_within(path, allowed_dirs)
    if resolved.exists() and not resolved.is_dir():
        raise InvalidInputError(f"Output path is not a folder: {resolved.name}")
    for protected in protected_files:
        if protected.resolve().is_relative_to(resolved):
            raise PathNotAllowedError("Output folder would contain an input file")
    return resolved
