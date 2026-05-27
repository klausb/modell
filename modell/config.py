from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import Field

from modell.models import ModellBaseModel


class BlenderConfig(ModellBaseModel):
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)
    token: str
    timeout_seconds: float = Field(default=30.0, gt=0)
    connect_retries: int = Field(default=2, ge=0)
    retry_backoff_seconds: float = Field(default=0.5, ge=0)


class LLMConfig(ModellBaseModel):
    provider: str = "openai_compatible"
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = Field(default=0.2, ge=0.0)
    max_tokens: int = Field(default=2000, gt=0)


class AgentConfig(ModellBaseModel):
    max_steps: int = Field(default=10, gt=0)
    verbosity: int = Field(default=1, ge=0)
    planning_interval: int = Field(default=1, ge=1)
    require_confirmation_for_destructive: bool = True


class ModellConfig(ModellBaseModel):
    blender: BlenderConfig
    llm: LLMConfig
    agent: AgentConfig


class ConfigError(RuntimeError):
    pass


def resolve_env_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: resolve_env_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env_value(item) for item in value]
    if isinstance(value, str) and value.startswith("env:"):
        env_name = value.removeprefix("env:")
        if not env_name:
            raise ConfigError("Empty environment variable reference")
        try:
            return os.environ[env_name]
        except KeyError as exc:
            raise ConfigError(f"Missing environment variable: {env_name}") from exc
    return value


def load_toml_file(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)
    with config_path.open("rb") as handle:
        return tomllib.load(handle)


def load_config_data(data: dict[str, Any]) -> ModellConfig:
    resolved = resolve_env_value(data)
    return ModellConfig.model_validate(resolved)


def default_config_paths() -> list[Path]:
    env_path = os.environ.get("MODELL_CONFIG")
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([Path("config/modell.toml"), Path("config/modell.example.toml")])
    return candidates


def load_config(path: str | Path | None = None) -> ModellConfig:
    if path is not None:
        return load_config_data(load_toml_file(path))

    for candidate in default_config_paths():
        if candidate.exists():
            return load_config_data(load_toml_file(candidate))

    raise FileNotFoundError("No Modell configuration file found")


def dump_config(config: ModellConfig) -> dict[str, Any]:
    return config.model_dump()