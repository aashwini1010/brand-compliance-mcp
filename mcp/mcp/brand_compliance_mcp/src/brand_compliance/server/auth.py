"""Bearer-token check for the HTTP transport."""

import hmac

from fastmcp.server.auth import AccessToken, TokenVerifier
from pydantic import SecretStr

MIN_TOKEN_LENGTH = 16
_CLIENT_ID = "local-client"


class BearerTokenVerifier(TokenVerifier):
    """Accepts exactly one pre-shared token, compared in constant time."""

    def __init__(self, token: SecretStr) -> None:
        super().__init__()
        self._expected = token.get_secret_value().encode("utf-8")

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return access info only for the configured token."""
        if hmac.compare_digest(token.encode("utf-8"), self._expected):
            return AccessToken(token=token, client_id=_CLIENT_ID, scopes=[])
        return None
