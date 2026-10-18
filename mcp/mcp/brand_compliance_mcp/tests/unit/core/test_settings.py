"""Tests for brand_compliance.core.settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from brand_compliance.core.settings import DEFAULT_CONFIG_FILE, load_settings


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


def test_default_config_file_exists_and_loads() -> None:
    assert DEFAULT_CONFIG_FILE.is_file()
    settings = load_settings()
    assert settings.server.host == "127.0.0.1"
    assert settings.server.transport == "sse"


def test_load_settings_reads_values_from_toml(tmp_path: Path) -> None:
    config = _write(tmp_path, "[server]\nport = 9100\n[limits]\nmax_guide_bytes = 10\n")
    settings = load_settings(config)
    assert settings.server.port == 9100
    assert settings.limits.max_guide_bytes == 10


def test_environment_overrides_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _write(tmp_path, "[server]\nport = 9100\n")
    monkeypatch.setenv("BRAND_MCP_SERVER__PORT", "9200")
    assert load_settings(config).server.port == 9200


def test_auth_token_is_secret_and_comes_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BRAND_MCP_AUTH_TOKEN", "s3cret")
    settings = load_settings(_write(tmp_path, ""))
    assert settings.auth_token is not None
    assert settings.auth_token.get_secret_value() == "s3cret"
    assert "s3cret" not in repr(settings)


def test_auth_token_defaults_to_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BRAND_MCP_AUTH_TOKEN", raising=False)
    assert load_settings(_write(tmp_path, "")).auth_token is None


def test_config_file_can_be_chosen_by_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _write(tmp_path, "[server]\nport = 9300\n")
    monkeypatch.setenv("BRAND_MCP_CONFIG_FILE", str(config))
    assert load_settings().server.port == 9300


@pytest.mark.parametrize(
    "toml",
    ["[server]\nport = 70000\n", '[server]\ntransport = "stdio"\n'],
)
def test_invalid_values_stop_startup(tmp_path: Path, toml: str) -> None:
    with pytest.raises(ValidationError):
        load_settings(_write(tmp_path, toml))
