from __future__ import annotations

import os

import pytest

from modell.config import ConfigError, load_config_data, resolve_env_value


def test_resolve_env_value_replaces_env_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODELL_LLM_API_KEY", "secret-key")

    value = resolve_env_value({"api_key": "env:MODELL_LLM_API_KEY"})

    assert value == {"api_key": "secret-key"}


def test_resolve_env_value_raises_for_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOES_NOT_EXIST", raising=False)

    with pytest.raises(ConfigError, match="Missing environment variable: DOES_NOT_EXIST"):
        resolve_env_value("env:DOES_NOT_EXIST")


def test_load_config_data_validates_and_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODELL_LLM_API_KEY", "abc123")

    cfg = load_config_data(
        {
            "blender": {
                "host": "127.0.0.1",
                "port": 8765,
                "token": "change-me",
                "timeout_seconds": 30,
                "connect_retries": 2,
                "retry_backoff_seconds": 0.5,
            },
            "llm": {
                "provider": "openai_compatible",
                "model": "gpt-4.1-mini",
                "base_url": "http://127.0.0.1:4000/v1",
                "api_key": "env:MODELL_LLM_API_KEY",
                "temperature": 0.2,
                "max_tokens": 2000,
            },
            "agent": {
                "max_steps": 10,
                "verbosity": 1,
                "planning_interval": 1,
                "require_confirmation_for_destructive": True,
            },
        }
    )

    assert cfg.blender.host == "127.0.0.1"
    assert cfg.blender.port == 8765
    assert cfg.llm.api_key == "abc123"
    assert cfg.agent.require_confirmation_for_destructive is True
