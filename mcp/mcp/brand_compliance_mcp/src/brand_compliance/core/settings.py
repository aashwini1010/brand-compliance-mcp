"""Application settings: defaults from ``config/settings.toml``, then env vars.

Environment variables use the ``BRAND_MCP_`` prefix and ``__`` for nesting,
e.g. ``BRAND_MCP_SERVER__PORT=9000``. Secrets come from the environment only.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

CONFIG_FILE_ENV = "BRAND_MCP_CONFIG_FILE"
DEFAULT_CONFIG_FILE = Path(__file__).resolve().parents[3] / "config" / "settings.toml"


class ServerSettings(BaseModel):
    """Where and how the MCP server listens."""

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    transport: Literal["sse", "http", "streamable-http"] = "sse"
    require_auth: bool = True
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_origins: list[str] = Field(default_factory=list)


class LimitSettings(BaseModel):
    """Input size limits in bytes."""

    max_guide_bytes: int = Field(default=5_000_000, gt=0)
    max_artifact_bytes: int = Field(default=5_000_000, gt=0)


class PathSettings(BaseModel):
    """Folders the server may read from and write to."""

    allowed_input_dirs: list[str] = Field(default_factory=lambda: ["."])
    allowed_output_dirs: list[str] = Field(default_factory=lambda: ["output"])


class Settings(BaseSettings):
    """All settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_prefix="BRAND_MCP_",
        env_nested_delimiter="__",
        toml_file=DEFAULT_CONFIG_FILE,
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    limits: LimitSettings = Field(default_factory=LimitSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    auth_token: SecretStr | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Order: init values, environment, then the TOML file."""
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )


def load_settings(config_file: Path | None = None) -> Settings:
    """Load settings from the given TOML file, ``BRAND_MCP_CONFIG_FILE``, or default."""
    chosen = config_file or _config_file_from_env() or DEFAULT_CONFIG_FILE
    custom = type(
        "_FileSettings",
        (Settings,),
        {"model_config": SettingsConfigDict(toml_file=chosen)},
    )
    settings: Settings = custom()
    return settings


def _config_file_from_env() -> Path | None:
    value = os.environ.get(CONFIG_FILE_ENV)
    return Path(value) if value else None
