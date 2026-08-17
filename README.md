# Overlord WorldSim

Overlord WorldSim is a Python 3.14 foundation for a long-running, deterministic dark-fantasy
role-playing game and world simulator. The engine, not a dialogue model, owns mechanics and
state. Authored canon lives in versioned JSON; a later phase will keep all mutable state in one
SQLite database per save branch.

This first slice freezes the public rules constitution and provides a typed loader plus canonical
JSON CLI. Persistence, combat execution, world content, and gameplay are deliberately outside the
current implementation.

## Quick start

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m overlord_worldsim rules --path content/core/ruleset.json
```

The `rules` command validates the document before printing sorted, compact canonical JSON. Invalid
or contradictory rules return exit status 2 and a diagnostic on standard error.

## Quality gates

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
```

## Repository map

- `content/core/ruleset.json` — frozen, versioned public rules constitution.
- `src/overlord_worldsim/` — typed loader, validation API, and CLI.
- `tests/` — behavioral rules and CLI tests.
- `docs/game-master-protocol.md` — mandatory runtime protocol for future gameplay sessions.
- `docs/superpowers/specs/` — approved system design.
- `docs/superpowers/plans/` — staged implementation plan.
- `saves/`, `backups/`, `exports/` — ignored runtime artifacts; `.gitkeep` files preserve layout.

Read [AGENTS.md](AGENTS.md) before changing engine code or operating a gameplay session. Authored
content JSON is source material and must remain version controlled; generated databases, backups,
and exports must not be committed.
