from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from modell.tcp_client import TCPClient


class ReplParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedInput:
    kind: str
    text: str | None = None
    action: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool | None = None


def parse_repl_input(line: str) -> ParsedInput:
    text = line.strip()
    if not text:
        return ParsedInput(kind="empty")

    if not text.startswith("/"):
        return ParsedInput(kind="prompt", text=text)

    if text == "/help":
        return ParsedInput(kind="help")
    if text == "/quit":
        return ParsedInput(kind="quit")
    if text == "/plan on":
        return ParsedInput(kind="plan", enabled=True)
    if text == "/plan off":
        return ParsedInput(kind="plan", enabled=False)

    if text.startswith("/raw"):
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            raise ReplParseError("Usage: /raw <action> <json>")
        action = parts[1]
        raw_json = parts[2] if len(parts) == 3 else "{}"
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ReplParseError(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ReplParseError("Raw payload must be a JSON object")
        return ParsedInput(kind="raw", action=action, params=parsed)

    raise ReplParseError("Unknown command. Use /help for available commands.")


def repl_help_text() -> str:
    return "\n".join(
        [
            "Commands:",
            "  /help                Show this help",
            "  /plan on             Enable planning summaries",
            "  /plan off            Disable planning summaries",
            "  /raw <action> <json> Send a raw protocol action",
            "  /quit                Exit",
        ]
    )


def run_repl(
    *,
    client: TCPClient,
    run_agent_prompt: Callable[[str, bool], str],
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    planning_enabled = True
    while True:
        try:
            line = input_fn("modell> ")
        except (EOFError, KeyboardInterrupt):
            output_fn("bye")
            return

        try:
            parsed = parse_repl_input(line)
        except ReplParseError as exc:
            output_fn(f"error: {exc}")
            continue

        if parsed.kind == "empty":
            continue
        if parsed.kind == "help":
            output_fn(repl_help_text())
            continue
        if parsed.kind == "quit":
            output_fn("bye")
            return
        if parsed.kind == "plan":
            planning_enabled = bool(parsed.enabled)
            output_fn(f"planning {'on' if planning_enabled else 'off'}")
            continue
        if parsed.kind == "raw":
            result = client.request(parsed.action or "", parsed.params)
            output_fn(json.dumps(result, indent=2, default=str))
            continue
        if parsed.kind == "prompt" and parsed.text is not None:
            output_fn(run_agent_prompt(parsed.text, planning_enabled))
            continue
