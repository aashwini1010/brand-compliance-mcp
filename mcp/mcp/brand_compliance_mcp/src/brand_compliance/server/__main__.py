"""Start the server: ``python -m brand_compliance.server``."""

import logging
import sys

from brand_compliance.core.errors import BrandComplianceError
from brand_compliance.core.logging import configure_logging
from brand_compliance.server.app import serve

logger = logging.getLogger(__name__)


def main() -> int:
    """Run the server; return a process exit code."""
    configure_logging()
    try:
        serve()
    except BrandComplianceError as exc:
        logger.error("Cannot start: [%s] %s", exc.code, exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
