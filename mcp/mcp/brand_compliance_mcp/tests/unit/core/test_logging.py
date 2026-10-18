"""Tests for brand_compliance.core.logging."""

import logging

from brand_compliance.core.logging import configure_logging


def test_configure_logging_sets_root_level() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    configure_logging(logging.DEBUG)
    assert root.level == logging.DEBUG
