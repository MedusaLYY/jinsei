# Project Agent Charter

These instructions apply to the entire repository. They govern both development work and every
future gameplay session.

## Authority boundaries

- Python mechanics and the active SQLite save are authoritative. A dialogue model may interpret
  player language and render visible outcomes; it is never the state engine.
- Treat `content/` JSON as authored, versioned, read-only-at-runtime definitions. Never turn an
  export into an authority or silently replace the content snapshot locked into a save.
- Never edit a save database directly, including through a SQLite shell. All mutations must use a
  validated engine command, one-writer transaction, event reducer, and revision check.
- Never invent an ability, spell, item, effect opcode, class, race, status, or exception that is not
  registered in the save's locked content snapshot.
- Never expose GM-only facts, secret difficulty values, hidden abilities, private NPC beliefs, or
  other data outside the requesting viewer's knowledge projection.
- Never choose an action, build choice, route, dialogue commitment, or level allocation for the
  player. Clarify material ambiguity and wait for the player's decision.

## Mandatory gameplay-session opening gate

Before accepting the first gameplay action, every session must:

1. Resolve the requested save slot and active branch without changing either.
2. Acquire the application save lock and open the database through the engine.
3. Run the health checks: SQLite integrity and foreign keys, schema and engine versions, locked
   rules/content versions and SHA-256, event-chain head, revision, RNG stream state, active branch,
   and any pending long-advance job.
4. Refuse play on a mismatch or failed check. Use the supported migration, verification, backup, or
   restore-as-new-branch workflow; never patch rows by hand.
5. Load only the player's visible projection and state the active branch, game time, revision, and
   any required pending choice before taking input.

## Mandatory turn order

For every player input: load and validate the current revision; translate free text into a
structured intent; ask for clarification when the intent is materially ambiguous; validate the
registered command and references; resolve mechanics and deterministic RNG; atomically commit the
command result, events, state, time, resources, RNG, and new revision; process due background
events; then narrate from the visible committed projection.

Mechanics always commit before narration. If narration fails, mark the committed turn unrendered
and retry rendering only. Never reroll or recreate events to make prose fit.

An invalid or ambiguous command consumes no game time, RNG, or revision. A valid in-world attempt
that fails still commits its costs, elapsed time, roll, and consequences.

## Query and slash-command rules

- Query commands are pure reads. They never advance time, consume RNG or resources, emit domain
  events, or increment the save revision.
- `/status`, `/skills`, `/inventory`, `/map`, `/relations`, `/time`, and `/log` must use the viewer's
  knowledge projection. `/help` and `/rules` expose only public registered material.
- `/save` may create and verify an out-of-band recovery artifact but may not mutate world state.
  `/branch` listing is read-only; creating or activating a branch requires its explicit engine
  operation and must never masquerade as a query.

## Engineering rules

- Target Python 3.14 and keep a `src/` layout with complete type annotations.
- Use integers and the ruleset's fixed-point policy for authoritative arithmetic; do not introduce
  binary floating-point state.
- Develop production behavior test-first: write a focused test, observe the expected failure, add
  the smallest implementation, and observe the test pass.
- Run full pytest with coverage, Ruff check and format check, and mypy before claiming completion.
- Preserve deterministic ordering, stable namespaced IDs, explicit versions, and canonical JSON.
- Keep secrets and generated runtime artifacts out of Git. Do not weaken `.gitignore` protections
  for saves, WAL files, backups, or exports.
