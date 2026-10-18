"""Turn internal errors into clear messages for MCP clients.

Typed errors become ``[CODE] message``. Anything unexpected is logged on the
server and reported as a generic internal error: no stack traces, no paths or
content leak to the client.
"""

import functools
import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from fastmcp.exceptions import ToolError

from brand_compliance.core.errors import BrandComplianceError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

INTERNAL_MESSAGE = "[INTERNAL_ERROR] The request failed; see the server log."


def to_tool_error(exc: Exception, tool: str) -> ToolError:
    """Return the error a client should see for an exception."""
    if isinstance(exc, ToolError):
        return exc
    if isinstance(exc, BrandComplianceError):
        logger.warning("Tool %s refused the request: %s [%s]", tool, exc, exc.code)
        return ToolError(f"[{exc.code}] {exc}")
    logger.exception("Tool %s failed unexpectedly", tool)
    return ToolError(INTERNAL_MESSAGE)


def guarded(tool: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator: run a tool and map any exception to a safe ``ToolError``."""

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return function(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 (mapped, logged, never swallowed)
                raise to_tool_error(exc, tool) from None

        return wrapper

    return decorate
