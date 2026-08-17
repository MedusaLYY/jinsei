# Long-Form Dark-Fantasy RPG Engine Design

**Status:** Approved on 2026-08-17
**Product:** Overlord WorldSim
**Runtime:** Python 3.14, stdlib-first
**Tone:** Adult dark fantasy; intimacy fades to black

## Objective

Build a trustworthy engine for a years-long role-playing campaign in an original continent shaped
by a fallen-god-age empire. It must support character growth, tactical combat, factions, economy,
war, NPC memory, and decade-scale world evolution without letting narration become the source of
truth. The same locked versions, seed, structured commands, and recorded events must reproduce the
same authoritative state.

The engine is local-first. It does not embed an external LLM API. A dialogue model or human game
master may translate prose to structured intent and render committed visible results, but cannot
write state, invent mechanics, choose for the player, or see hidden data while narrating.

## Scope and delivery shape

The system is delivered in nine vertical phases:

1. Python project scaffold, rules constitution, loader, protocol, and quality gates.
2. Versioned content schemas and SQLite persistence, migrations, events, hashing, backups, branches,
   exports, and integrity tooling.
3. Characters, racial and job-class acquisition graphs, stats, growth, magic-tier calculation, and
   declarative ability effect opcodes.
4. Equipment, ownership, free actions, tactical combat, statuses, cooldowns, summoning,
   transformation, domains, death, and resurrection.
5. Encyclopedia-scale public mechanics content at the frozen quotas.
6. Original continent canon: public history, polities, organizations, regions, and locations, with
   GM-hidden truths stored separately from public facts.
7. Full, summary, and aggregate NPC simulation; relationships, beliefs, plans, factions, markets,
   territories, and armies.
8. Deterministic event scheduling, persistent long advances, knowledge-projected slash views, and
   gameplay session orchestration.
9. Character creator for every start mode, ending after the complete legal build and before the
   prologue. The player chooses the level-100 equipment package later; the engine does not choose it.

Phase 1 does not implement persistence, combat execution, world content, or gameplay. It freezes
the contract those phases must obey.

## Authority model

### Static authored content

`content/` contains version-controlled JSON definitions and schemas. Every definition has a stable
namespaced ID, schema version, content version, declared dependencies, and canonical SHA-256.
Published content is fixed canon. A seed may fill only explicitly noncritical empty detail using a
derivation based on `world_seed + entity_id + field_name`; the first result is persisted. It cannot
replace authored fields or change because of access order or prompt wording.

Content expands only in controlled, versioned releases. A running save embeds and locks its exact
content snapshot. It never reads a newer repository definition silently. Unknown effect opcodes,
unresolved references, dependency failures, cycles, impossible acquisition paths, and quota or
coverage failures block content publication and save startup.

### Dynamic state

The only mutable authority is:

`saves/<slot>/branches/<branch_id>/state.sqlite3`

World, player, inventory, map, relationship, and log JSON files are read-only exports. They never
become an input authority. Each save locks database schema version, content schema version, rules
version and ruleset hash, engine version, content snapshot hash, and world seed.

SQLite uses foreign keys, WAL mode, synchronous `FULL`, an application save lock, and one writer.
Every accepted command atomically records its command result, events, materialized state, elapsed
time, resource changes, RNG changes, event-chain head, semantic state hash, and new revision. A
transaction either commits all of those or none.

Runtime entities are tombstoned rather than hard-deleted. JSON payload references are checked
against event schemas before insertion because SQLite foreign keys cannot inspect arbitrary JSON.
Derived caches carry a source revision, are fully rebuildable, and are excluded from the
authoritative semantic hash.

## Determinism and replay

Randomness uses PCG32 with purpose-split streams. Stable IDs, stable collection ordering, and the
saved stream positions make draws independent of database row order and narration. Events record
final mechanical results; replay applies reducers and never rerolls. Idempotent `command_id` values
make a response retry return the prior result rather than create a second turn.

The semantic state hash is computed over canonical ordered records and canonical JSON. It excludes
wall-clock timestamps, SQLite page layout, derived caches, backup metadata, and display prose. Event
hashes form an append-only chain. The determinism guarantee applies to a fixed engine/rules/content
snapshot plus a structured command sequence or recorded event sequence; it does not promise that a
nondeterministic language model will produce identical prose or intent parsing.

## Frozen public mechanics

`content/core/ruleset.json` is the machine-readable constitution. Version 1 freezes these points:

- Authoritative arithmetic uses signed integers. Fractions use fixed point at 10,000 basis points
  per whole with half-away-from-zero rounding; binary floating point is forbidden in state.
- The calendar has twelve 30-day months, five intercalary days, 365 days per year, and 24-hour days.
- Total level is at most 100. Per-node caps are base 15, advanced 10, and rare, hidden, legendary,
  and world 5 each.
- The target-level growth table has exactly levels 1 through 100 once each, with cost `100 * N^2`.
  Progress comes only from elapsed game time and committed activity, never wall time.
- Magic minimum effective caster levels are tier 0: 0, tier 1: 1, then 8, 15, 22, 29, 36, 43,
  50, 57, and 64 for tiers 2 through 10; super-tier begins at 70 and may require further content
  prerequisites. Different traditions do not combine unless a registered rule explicitly says so.
- An opposed check succeeds when `d100 + action_rating + situational_modifier` is at least
  `50 + defense_rating`; a non-opposed check substitutes an explicit fixed DC for that target.
  Natural 1 and 100 never override feasibility and have no automatic failure or success. The audit
  stores roll, action rating, situational modifiers, defense or fixed DC, and margin separately.
  Player-facing output includes only fields the player knows and never reveals a secret defense.
- A combat round is six game-seconds. Each turn grants one move, one major, and one minor action;
  each round grants one reaction. Unused actions expire.
- Damage resolves only in this order: hit, raw power, penetration, defense, resistance, shield, HP.
  Resistance is capped at 9,000 basis points unless a separate explicit immunity applies. Final
  damage may be zero.
- Life states are alive at HP above zero, incapacitated at zero, dying below zero but above negative
  half maximum HP, and dead at or below negative half maximum HP. Integer evaluation compares twice
  HP with negative maximum HP. A valid execution or registered successful instant-death effect may
  set dead directly. Ordinary healing cannot clear dead; only a registered resurrection can.
- Advances longer than 24 game-hours require an explicit long-term activity or a stored routine.
  Otherwise only `safe_maintenance` runs—ordinary food, rest, and shelter upkeep—with zero free
  growth. Lethal danger, capture, forced relocation, exhausted required resources, and a pending
  player level allocation interrupt the advance.
- Death is true death in the committed timeline. Loading a checkpoint creates a preserved new
  branch; it never overwrites or merges the dead branch.

Character growth uses one audited growth-point event stream across combat, research, politics,
trade, governance, and training. Repetitive, riskless, or grossly under-level activity can yield
zero. Reaching a threshold creates a pending allocation; the player selects a legal next racial or
job-class level in acquisition order. Prerequisites are declarative `all`/`any`/`not` expressions,
checked at acquisition time, and the ordered history remains part of the build proof.

Abilities use registered declarative effect opcodes. Content cannot execute arbitrary Python.

## Content, starts, and scarcity contract

The published mechanics corpus must contain at least:

- 60 independently referenceable racial nodes;
- 180 independently referenceable job-class nodes;
- 800 distinct abilities, with pure numeric upgrades not counted again;
- 360 spells spanning tiers 0 through 10 and super, with attack, defense, control, support,
  scouting, and counter coverage;
- 500 items covering useful equipment, consumables, materials, and key items rather than reaching
  the number through unusable filler.

The world corpus must expose at least 14 sovereign polities, 48 major organizations, and 120 fully
modeled important NPCs, plus summary NPCs and aggregate population. Public canon and GM-hidden
truths are different content projections. This design records no hidden cosmology or plot facts.

Start modes are ordinary level 1, heroic level 35, legendary level 60, otherworld-player level 100,
and custom level 1–100. Every high-level start contains a legal ordered acquisition history.
Restricted classes require registered origin authorization or achievement tokens. Talent, wealth,
and equipment use mode budgets. Custom mode may exceed ordinary budgets only when the save is
marked custom, and can never break total-level or reference invariants.

At least 99% of sapient population is below level 20. Random generators may not produce level 35 or
higher. Every level-45-or-higher person is named. Native populations are capped at 24 people from
levels 60–74, nine from 75–89, and two from 90–99; no public native is level 100.

## Command and transaction interfaces

The public application boundary is explicit:

```text
interpret(text, viewer_revision) -> IntentDraft | Clarification
execute(command_id, expected_revision, command) -> CommittedTurn | RejectedCommand
query(viewer, view, revision) -> ViewerProjection
start_advance(command_id, expected_revision, request) -> AdvanceJob
resume_advance(job_id) -> AdvanceJob
get_job_status(job_id) -> AdvanceJobStatus
backup.create / backup.verify / backup.list / backup.restore_as_branch
```

Invalid references, illegal prerequisites, ambiguity, and stale revisions reject before mechanics:
no time, RNG, event, or revision is consumed. A valid action that misses, fails a check, or has an
unfavorable outcome is committed with its time, costs, roll, and events.

The turn sequence is fixed: load and validate, interpret, clarify if needed, begin the one-writer
transaction, adjudicate and draw RNG, create structured events, update projections and hashes,
validate invariants, commit, process due background events, then narrate from the new viewer
projection. Speech, promises, lies, threats, and transmitted information become structured events
before prose. A narration failure creates `committed_unrendered`; rendering retries do not rerun the
turn.

## Branches, backups, and recovery

Active WAL databases are backed up only through the SQLite Online Backup API. Each ordinary state
turn keeps two rotating recovery backups. Long advances, migrations, manual saves, and every 100
events create verified archival snapshots. Each snapshot records database SHA-256, semantic state
hash, event-chain head, versions, branch, and revision.

Restoration copies into a temporary path, verifies integrity, foreign keys, hashes, versions, and
the embedded content snapshot, then creates and activates a new branch through an atomically
replaced slot pointer. The old branch stays immutable. A branch records its parent, fork revision,
and fork event hash; new entity IDs use its namespace. Branches never merge. A corrupt artifact is
quarantined. Version 1 promises recovery to the latest complete verified snapshot, not zero-loss
reconstruction from an external event tail.

## World and NPC simulation

NPCs have three simulation tiers: full important NPCs, active-region summary NPCs, and aggregate
background populations. Full and summary NPCs maintain individual plans; aggregate populations use
cohort models. Objective facts, NPC beliefs, and player knowledge are distinct. Memories record
source, game time, confidence, secrecy, and originating event. Directly witnessed durable facts do
not vanish arbitrarily, while rumors may decay, conflict, or remain wrong. Death cancels or
transfers future plans through explicit events.

Race definitions provide maturity, expected lifespan, maximum lifespan, and agelessness. Age derives
from birth date. Ageless does not mean invulnerable. Important NPC marriages, succession, births,
and deaths resolve individually; ordinary populations use annual aggregate models.

Faction state includes treasury, food, population/manpower, logistics, stability, legitimacy,
influence, intelligence, and territory. Regional markets track stock and price indices. Armies
track strength, training, morale, supply, command, terrain, and magical support. Politics, trade,
territory, and war resolve from authoritative state and registered d100 mechanics, not improvised
narrative outcomes.

## Time and read models

The event queue orders work by `(game_timestamp, phase, priority, stable_id)`. It supports exact
seconds, daily, weekly/monthly, seasonal, and annual processing. Long advances are persistent jobs
committed in deterministic chunks with target time, processed time, next scheduling key, and status.
Crashes resume after the last committed chunk. Version 1 does not cancel a running job midway.
Advancing one year at once and in twelve monthly segments must produce the same authoritative hash
when commands, versions, and seed are equal.

`/status`, `/skills`, `/inventory`, `/map`, `/relations`, `/time`, and `/log` are knowledge-projected
read models. `/help` and `/rules` expose public references. Query-only commands do not change time,
RNG, resources, events, or revision. `/save` produces a verified recovery artifact outside world
state. Branch mutation is an explicit operation, not a disguised query.

## Character creator

The creator captures identity, age, race, origin, starting region, concept, ordered legal class
history, talents, appearance, personality, and mode-budgeted equipment. It validates every
prerequisite and reference and previews derived state from the same reducer used in play. Completion
persists a creation command and stops before the prologue. The engine never selects a player's
build, dialogue, or level-100 equipment package.

## Verification contract

Publication and continuous integration validate schemas, references, dependency and prerequisite
cycles, opcodes, quota and coverage matrices, and all starting builds. Persistence tests inject a
failure after every transaction stage and require state, event, RNG, command, and revision to be all
old or all new. Repeating one `command_id` 100 times creates one result. Stale concurrent revisions
are rejected.

Given the same snapshot, seed, and structured commands, semantic state and event-head hashes match.
Replaying from genesis or a snapshot produces the materialized state. Long jobs interrupted at each
chunk boundary recover to the uninterrupted hash; segmented time equals unsegmented time. Branch
restore preserves the source branch and cannot collide entity IDs. Hidden-field sentinels produce
zero leaks across every query, narration input, and final output.

Tests cover life, items, time, NPC belief/knowledge, relationships, factions, content, and all start
modes. Pull requests run at least 20 seeds × 1,000 state actions. The long suite runs 100 seeds ×
10,000 actions with zero broken references, invariant failures, event-chain failures, or scarcity
violations.

Hidden-information protection is a logical application boundary, not encryption against the local
file owner.
