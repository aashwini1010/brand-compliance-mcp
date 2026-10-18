"""Tests for brand_compliance.core.errors."""

import pytest

from brand_compliance.core import errors


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (errors.InvalidInputError, "INVALID_INPUT"),
        (errors.UnsupportedFormatError, "UNSUPPORTED_FORMAT"),
        (errors.ParseFailedError, "PARSE_FAILED"),
        (errors.PathNotAllowedError, "PATH_NOT_ALLOWED"),
        (errors.PluginError, "PLUGIN_ERROR"),
    ],
)
def test_error_code_is_stable(
    error: type[errors.BrandComplianceError], code: str
) -> None:
    assert error.code == code
    assert issubclass(error, errors.BrandComplianceError)
