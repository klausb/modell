from __future__ import annotations

import pytest

from modell.repl import ReplParseError, parse_repl_input


def test_parse_raw_with_json_payload() -> None:
    parsed = parse_repl_input('/raw create_primitive {"primitive_type":"CUBE"}')

    assert parsed.kind == "raw"
    assert parsed.action == "create_primitive"
    assert parsed.params == {"primitive_type": "CUBE"}


def test_parse_raw_without_json_defaults_to_empty_object() -> None:
    parsed = parse_repl_input("/raw ping")

    assert parsed.kind == "raw"
    assert parsed.action == "ping"
    assert parsed.params == {}


def test_parse_raw_rejects_non_object_json() -> None:
    with pytest.raises(ReplParseError, match="Raw payload must be a JSON object"):
        parse_repl_input("/raw ping []")


def test_parse_plan_toggles_and_quit() -> None:
    assert parse_repl_input("/plan on").enabled is True
    assert parse_repl_input("/plan off").enabled is False
    assert parse_repl_input("/quit").kind == "quit"
