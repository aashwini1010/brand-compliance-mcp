"""Tests for the bearer-token verifier and the error mapping."""

import asyncio

import pytest
from fastmcp.exceptions import ToolError
from pydantic import SecretStr

from brand_compliance.core.errors import InvalidInputError, PathNotAllowedError
from brand_compliance.server.auth import BearerTokenVerifier
from brand_compliance.server.error_mapping import (
    INTERNAL_MESSAGE,
    guarded,
    to_tool_error,
)


def test_verifier_accepts_only_the_configured_token() -> None:
    verifier = BearerTokenVerifier(SecretStr("correct-horse-battery"))
    assert asyncio.run(verifier.verify_token("correct-horse-battery")) is not None
    assert asyncio.run(verifier.verify_token("wrong")) is None
    assert asyncio.run(verifier.verify_token("")) is None
    assert asyncio.run(verifier.verify_token("correct-horse-batter")) is None


def test_verifier_returns_access_info_without_scopes() -> None:
    access = asyncio.run(
        BearerTokenVerifier(SecretStr("x" * 20)).verify_token("x" * 20)
    )
    assert access is not None
    assert access.client_id == "local-client"
    assert access.scopes == []


def test_typed_errors_become_tool_errors_with_their_code() -> None:
    error = to_tool_error(PathNotAllowedError("outside"), "t")
    assert isinstance(error, ToolError)
    assert str(error) == "[PATH_NOT_ALLOWED] outside"


def test_unexpected_errors_never_leak_details_to_the_client() -> None:
    error = to_tool_error(RuntimeError("secret /home/x/client-file.html"), "t")
    assert str(error) == INTERNAL_MESSAGE
    assert "secret" not in str(error)


def test_existing_tool_errors_pass_through_unchanged() -> None:
    original = ToolError("[INVALID_INPUT] nope")
    assert to_tool_error(original, "t") is original


def test_guarded_maps_exceptions_and_keeps_the_function_signature() -> None:
    @guarded("demo")
    def demo(value: int) -> int:
        """Demo docstring."""
        if value < 0:
            raise InvalidInputError("negative")
        if value == 0:
            raise ZeroDivisionError("internal detail")
        return value

    assert demo(2) == 2
    assert demo.__name__ == "demo"
    assert demo.__doc__ == "Demo docstring."
    with pytest.raises(ToolError, match=r"\[INVALID_INPUT\] negative"):
        demo(-1)
    with pytest.raises(ToolError) as info:
        demo(0)
    assert "internal detail" not in str(info.value)


def test_unexpected_errors_are_logged_on_the_server(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("ERROR"):
        to_tool_error(RuntimeError("boom"), "demo_tool")
    assert any("demo_tool failed unexpectedly" in r.message for r in caplog.records)
