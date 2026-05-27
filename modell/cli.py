from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from modell.agent import AgentRuntime
from modell.config import ModellConfig, load_config
from modell.logging_config import configure_logging
from modell.repl import run_repl
from modell.tcp_client import ProtocolResponseError, TCPClient, TCPClientError
from modell.tools import build_toolkit


app = typer.Typer(help="Modell CLI")


def _parse_json_payload(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON payload: {exc}") from exc
    if not isinstance(parsed, dict):
        raise typer.BadParameter("JSON payload must be an object")
    return parsed


def _load_runtime(config_path: str | None) -> tuple[ModellConfig, TCPClient, AgentRuntime]:
    cfg = load_config(Path(config_path) if config_path else None)

    def confirm_callback(reason: str) -> bool:
        return typer.confirm(f"Confirm destructive action: {reason}?", default=False)

    client = TCPClient(cfg.blender)
    tools = build_toolkit(client, cfg.agent, confirm_callback=confirm_callback)
    agent = AgentRuntime(config=cfg, tools=tools)
    return cfg, client, agent


def _print_json(data: Any) -> None:
    typer.echo(json.dumps(data, indent=2, default=str))


@app.command()
def ping(config: str | None = typer.Option(None, "--config", help="Path to TOML config")) -> None:
    """Send ping to Blender add-on."""
    _, client, _ = _load_runtime(config)
    try:
        _print_json(client.ping())
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


@app.command()
def health(config: str | None = typer.Option(None, "--config", help="Path to TOML config")) -> None:
    """Get Blender add-on health."""
    _, client, _ = _load_runtime(config)
    try:
        _print_json(client.health())
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


@app.command()
def capabilities(config: str | None = typer.Option(None, "--config", help="Path to TOML config")) -> None:
    """Get remote capabilities."""
    _, client, _ = _load_runtime(config)
    try:
        _print_json(client.capabilities())
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


@app.command()
def command(
    prompt: str,
    config: str | None = typer.Option(None, "--config", help="Path to TOML config"),
) -> None:
    """Run one natural-language command through the agent runtime."""
    _, _, agent = _load_runtime(config)
    try:
        typer.echo(agent.run(prompt, planning_enabled=True))
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


@app.command()
def raw(
    action: str,
    json_payload: str | None = typer.Option(None, "--json", help="JSON object for params"),
    config: str | None = typer.Option(None, "--config", help="Path to TOML config"),
) -> None:
    """Send a raw action and params to the Blender add-on."""
    _, client, _ = _load_runtime(config)
    params = _parse_json_payload(json_payload)
    try:
        _print_json(client.request(action, params))
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


@app.command()
def chat(config: str | None = typer.Option(None, "--config", help="Path to TOML config")) -> None:
    """Start interactive REPL chat."""
    configure_logging()
    _, client, agent = _load_runtime(config)

    def run_agent_prompt(user_prompt: str, planning_enabled: bool) -> str:
        return agent.run(user_prompt, planning_enabled=planning_enabled)

    try:
        run_repl(client=client, run_agent_prompt=run_agent_prompt)
    except (TCPClientError, ProtocolResponseError) as exc:
        raise typer.Exit(code=_emit_error(exc))


def _emit_error(exc: Exception) -> int:
    typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
    return 1


if __name__ == "__main__":
    app()