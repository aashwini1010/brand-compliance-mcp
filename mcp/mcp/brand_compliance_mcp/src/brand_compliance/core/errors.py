"""Named errors so failures are clear to callers instead of crashing."""


class BrandComplianceError(Exception):
    """Base class; ``code`` is the stable identifier sent to MCP clients."""

    code = "INTERNAL_ERROR"


class InvalidInputError(BrandComplianceError):
    """An input failed validation (size, type, missing value)."""

    code = "INVALID_INPUT"


class UnsupportedFormatError(BrandComplianceError):
    """No registered plugin can handle the given input."""

    code = "UNSUPPORTED_FORMAT"


class ParseFailedError(BrandComplianceError):
    """A guide or artifact could not be parsed."""

    code = "PARSE_FAILED"


class PathNotAllowedError(BrandComplianceError):
    """A path is outside the allowed folders or would overwrite the source."""

    code = "PATH_NOT_ALLOWED"


class PluginError(BrandComplianceError):
    """A plugin is invalid or could not be registered."""

    code = "PLUGIN_ERROR"


class ConfigurationError(BrandComplianceError):
    """The server is configured in a way that is unsafe or unusable."""

    code = "CONFIGURATION_ERROR"
