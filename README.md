# Modell

Modell is a phased starter repository for an LLM-driven Blender modeling system.

## Current Status

Phase 1 is complete. This phase establishes the repository skeleton and the shared Python foundations only:

- package metadata and dependency declarations
- TOML configuration loading with environment-variable resolution
- typed protocol request/response models
- shared enums and payload schemas
- logging helpers

The following parts will be added in later phases and are intentionally not implemented yet:

- Phase 2: `modell` CLI, TCP client, REPL, LLM wiring, agent, and tool layer
- Phase 3: Blender add-on, socket server, request queue, actions, timers, and UI
- Phase 4: tests for the pure Python parts

## Planned Architecture

```text
User / CLI / REPL
        |
        v
   modell core
        |
   TCP JSON lines
        |
        v
 Blender add-on
        |
        v
      bpy / BMesh
```

## Repository Layout

```text
README.md
.gitignore
.env.example
pyproject.toml
config/
  modell.example.toml
modell/
  __init__.py
  config.py
  protocol.py
  models.py
  logging_config.py
```

## What Exists In Phase 1

The shared protocol is designed around newline-delimited UTF-8 JSON messages.

Each request must carry:

- `protocol_version`
- `request_id`
- `token`
- `action`
- `params`

Each response must carry:

- `protocol_version`
- `request_id`
- `ok`
- `result`
- `error`

The configuration layer supports TOML files plus `env:VAR` indirection for secrets and local machine overrides.

## Next Phases

Phase 2 will add the CLI, agent, REPL, tool wrappers, and TCP client.

Phase 3 will add the Blender add-on and the remote action execution path.

Phase 4 will add tests for the pure Python portions.

## Notes

This repository is intentionally being built in phases. The CLI entry point is declared in `pyproject.toml`, but `modell.cli` will not exist until Phase 2.

The more detailed setup, usage, security model, and Blender installation instructions will be completed once the core and add-on phases are in place.

## UV Commands

Use these commands from the repository root.

### Environment Setup

~~~bash
uv sync
~~~

### Build Package

~~~bash
uv build
~~~

### Run Tests

~~~bash
uv run --with pytest pytest -q
~~~

### Package Blender Add-on

Create a timestamped ZIP under dist/:

~~~bash
uv run python scripts/package_blender_addon.py
~~~

Create a ZIP at a custom path:

~~~bash
uv run python scripts/package_blender_addon.py --output /absolute/path/modell-addon.zip
~~~

### CLI Commands

~~~bash
uv run modell chat
uv run modell chat --config config/modell.toml
uv run modell ping
uv run modell health
uv run modell capabilities
uv run modell command "create a low poly stool with ribbed sides"
uv run modell raw ping
uv run modell raw list_objects
uv run modell raw create_primitive --json '{"primitive_type":"CUBE","name":"CubeA","location":[0,0,0],"rotation":[0,0,0],"scale":[1,1,1]}'
~~~