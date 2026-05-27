from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from modell.config import LLMConfig


class LLMAdapter(Protocol):
    def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        ...


@dataclass(slots=True)
class DeterministicEchoLLM:
    """Safe fallback adapter when a concrete provider is not available."""

    def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        _ = system_prompt
        return f"TODO: LLM adapter fallback used. Prompt was: {prompt}"


def build_smolagents_model(config: LLMConfig) -> Any:
    """Build a smolagents-compatible model object using a conservative adapter strategy.

    TODO: If your local smolagents version exposes a preferred OpenAI-compatible model
    constructor, wire it here directly and remove this dynamic fallback.
    """

    try:
        import smolagents  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("smolagents is not importable") from exc

    candidate_names = [
        "OpenAIServerModel",
        "LiteLLMModel",
        "OpenAIModel",
    ]

    kwargs = {
        "model_id": config.model,
        "api_base": config.base_url,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    for name in candidate_names:
        model_cls = getattr(smolagents, name, None)
        if model_cls is None:
            continue
        try:
            return model_cls(**kwargs)
        except TypeError:
            pass

    raise RuntimeError(
        "Unable to construct a smolagents model for provider "
        f"{config.provider!r}. Update modell/llm.py build_smolagents_model()."
    )
