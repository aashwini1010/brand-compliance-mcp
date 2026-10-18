"""Create and run the MCP server over HTTP + SSE."""

import logging
from typing import Final

import uvicorn
from fastmcp import FastMCP

from brand_compliance.core.errors import ConfigurationError
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.core.settings import Settings, load_settings
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.rules.vocabulary import Vocabulary, load_vocabulary
from brand_compliance.server.auth import MIN_TOKEN_LENGTH, BearerTokenVerifier
from brand_compliance.server.tools import register_tools

logger = logging.getLogger(__name__)

SERVER_NAME: Final = "brand-compliance"
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})
_INSTRUCTIONS: Final = (
    "Applies a design guide to an HTML artifact (static page or email) and "
    "reports every change and every rule not applied. Typical use: "
    "call classify_artifact, then apply_brand, then read the report with get_report."
)
_TOKEN_HELP: Final = (
    "Set BRAND_MCP_AUTH_TOKEN to a secret of at least "
    f"{MIN_TOKEN_LENGTH} characters, for example: "
    'python -c "import secrets; print(secrets.token_urlsafe(32))"'
)


def create_server(
    settings: Settings,
    vocabulary: Vocabulary,
    registry: PluginRegistry | None = None,
) -> FastMCP:
    """Build the FastMCP server with all tools registered."""
    registry = registry or build_registry(settings, vocabulary)
    orchestrator = Orchestrator(registry, settings, vocabulary)
    verifier = BearerTokenVerifier(settings.auth_token) if settings.auth_token else None
    server = FastMCP(
        SERVER_NAME,
        instructions=_INSTRUCTIONS,
        auth=verifier,
        mask_error_details=True,
    )
    register_tools(server, orchestrator, registry)
    return server


def validate_startup(settings: Settings) -> None:
    """Refuse unsafe configurations before opening a port."""
    token = settings.auth_token.get_secret_value() if settings.auth_token else ""
    exposed = settings.server.host not in LOOPBACK_HOSTS
    if token and len(token) < MIN_TOKEN_LENGTH:
        raise ConfigurationError(f"The auth token is too short. {_TOKEN_HELP}")
    if (settings.server.require_auth or exposed) and not token:
        reason = (
            "require_auth is on"
            if settings.server.require_auth
            else (f"host {settings.server.host} is reachable beyond this machine")
        )
        raise ConfigurationError(f"No auth token configured ({reason}). {_TOKEN_HELP}")
    if not settings.server.require_auth:
        logger.warning("Authentication is turned off: only use this on 127.0.0.1")
    if exposed:
        logger.warning(
            "Listening on %s, beyond localhost: put TLS in front of this server",
            settings.server.host,
        )


def endpoint_url(settings: Settings) -> str:
    """The URL an MCP client connects to."""
    path = "/sse" if settings.server.transport == "sse" else "/mcp"
    host = settings.server.host
    host = f"[{host}]" if ":" in host else host
    return f"http://{host}:{settings.server.port}{path}"


def build_http_app(server: FastMCP, settings: Settings):  # type: ignore[no-untyped-def]
    """Return the ASGI app, with Host/Origin protection switched on."""
    validate_startup(settings)
    return server.http_app(
        transport=settings.server.transport,
        host_origin_protection=True,
        allowed_hosts=settings.server.allowed_hosts or None,
        allowed_origins=settings.server.allowed_origins or None,
    )


def serve(settings: Settings | None = None) -> None:
    """Run the server until stopped."""
    settings = settings or load_settings()
    vocabulary = load_vocabulary()
    server = create_server(settings, vocabulary)
    app = build_http_app(server, settings)
    logger.info("MCP endpoint: %s (bearer token required)", endpoint_url(settings))
    uvicorn.run(
        app, host=settings.server.host, port=settings.server.port, log_level="info"
    )
