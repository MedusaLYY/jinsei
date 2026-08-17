# Long-Form RPG Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, local-first dark-fantasy RPG and world simulator whose mechanics, long-term state, hidden-information boundaries, and branch recovery remain trustworthy across years of play.

**Architecture:** Versioned JSON is the authority for static rules and authored canon; each branch's SQLite database is the sole authority for mutable state. Free text crosses a typed intent boundary, mechanics commit as deterministic events and projections in one transaction, and narration sees only the post-commit viewer projection. PCG32 split streams, canonical hashes, embedded content snapshots, persistent time jobs, online backups, and immutable branches make replay and recovery auditable.

**Tech Stack:** Python 3.14, stdlib (`sqlite3`, `json`, `hashlib`, `argparse`, `dataclasses`), JSON Schema via `jsonschema`, pytest, pytest-cov, Hypothesis, Ruff, and mypy.

---

## File structure

- `content/core/ruleset.json`: frozen public mechanics constitution.
- `content/schemas/`: JSON Schemas for manifests, definitions, effects, world canon, and content packs.
- `content/mechanics/`: races, jobs, abilities, spells, items, statuses, and creator budgets.
- `content/world/`: public continent, polity, organization, location, history, and NPC definitions.
- `content/gm/`: separately loaded GM-only facts; never included in public or narrator projections.
- `src/overlord_worldsim/rules.py`: rules loading, semantic validation, and canonical serialization.
- `src/overlord_worldsim/content.py`: content dependency, reference, checksum, quota, and coverage validation.
- `src/overlord_worldsim/storage/`: connections, migrations, transactions, save locks, backups, branches, and exports.
- `src/overlord_worldsim/events/`: versioned event records, reducers, canonical hashes, and replay.
- `src/overlord_worldsim/rng.py`: PCG32 split streams and persisted draw records.
- `src/overlord_worldsim/commands/`: typed commands, interpreter boundary, execution, idempotency, and rejection results.
- `src/overlord_worldsim/characters/`: builds, acquisition graphs, growth, stats, and magic tiers.
- `src/overlord_worldsim/effects/`: closed declarative opcode registry and executor.
- `src/overlord_worldsim/combat/`: checks, actions, range, initiative, damage, statuses, summons, domains, and life states.
- `src/overlord_worldsim/items/`: definitions, instances, slots, ownership, durability, and charges.
- `src/overlord_worldsim/world/`: NPC knowledge, relationships, factions, markets, territories, armies, and demographic models.
- `src/overlord_worldsim/scheduler/`: deterministic queue and persistent long-advance jobs.
- `src/overlord_worldsim/views/`: viewer knowledge projections, slash queries, and stored narration.
- `src/overlord_worldsim/creator/`: start modes, budgets, legal histories, validation, and creation commit.
- `tests/`: unit, integration, property, migration, failure-injection, leak, replay, and soak suites mirroring these modules.

### Task 1: Scaffold and freeze the rules constitution

**Files:**

- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/game-master-protocol.md`
- Create: `content/core/ruleset.json`
- Create: `src/overlord_worldsim/__init__.py`
- Create: `src/overlord_worldsim/__main__.py`
- Create: `src/overlord_worldsim/rules.py`
- Test: `tests/test_package.py`
- Test: `tests/test_rules.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: initialize Git without implementing on `main`**

```powershell
git init -b main
git commit --allow-empty -m "chore: initialize repository"
git switch -c feat/worldsim-v1
```

- [ ] **Step 2: write behavioral tests for the public foundation API**

```python
def test_growth_boundaries() -> None:
    rules = load_ruleset(Path("content/core/ruleset.json"))
    assert rules.growth_cost_for(1) == 100
    assert rules.growth_cost_for(100) == 1_000_000


def test_magic_boundaries() -> None:
    rules = load_ruleset(Path("content/core/ruleset.json"))
    assert rules.minimum_level_for_magic_tier(0) == 0
    assert rules.minimum_level_for_magic_tier(10) == 64
    assert rules.minimum_level_for_magic_tier("super") == 70
```

Include import/version, valid load, invalid cap, duplicate damage phase, repeated growth level,
malformed JSON, the explicit opposed/fixed-DC d100 equations and audit fields, and canonical CLI
tests.

- [ ] **Step 3: run the tests and confirm the missing package/ruleset failure**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_package.py tests\test_rules.py tests\test_cli.py -v
```

Expected: failures identify the absent `overlord_worldsim` package and ruleset.

- [ ] **Step 4: implement only the typed loader, validator, canonical serializer, and CLI**

```python
@dataclass(frozen=True, slots=True)
class Ruleset:
    ruleset_id: str
    schema_version: str
    rules_version: str

    def growth_cost_for(self, target_level: int) -> int:
        return self._growth_costs[target_level]

    def minimum_level_for_magic_tier(self, tier: str | int) -> int:
        return self._magic_thresholds[str(tier)]


def load_ruleset(path: str | Path) -> Ruleset:
    """Reject malformed JSON, duplicate keys, floats, and every frozen-rule inconsistency."""
```

Freeze every value in the approved design, including quotas and scarcity. Keep runtime state out of
this task.

- [ ] **Step 5: run the foundation quality gate**

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
```

Expected: all commands exit zero and coverage meets the configured threshold.

- [ ] **Step 6: commit the foundation**

```powershell
git add .gitignore AGENTS.md README.md pyproject.toml backups content docs exports saves src tests
git commit -m "feat: scaffold deterministic worldsim rules foundation"
```

### Task 2: Validate and lock versioned content packs

**Files:**

- Create: `content/schemas/manifest.schema.json`
- Create: `content/schemas/effect.schema.json`
- Create: `content/schemas/mechanics.schema.json`
- Create: `content/schemas/world.schema.json`
- Create: `src/overlord_worldsim/content.py`
- Create: `tests/content/test_manifest.py`
- Create: `tests/content/test_references.py`
- Create: `tests/content/test_coverage.py`

- [ ] **Step 1: write failing manifest, dependency, reference, cycle, opcode, checksum, and quota tests**

```python
def test_content_snapshot_is_order_independent(tmp_path: Path) -> None:
    first = load_content_pack(tmp_path / "pack", file_order="forward")
    second = load_content_pack(tmp_path / "pack", file_order="reverse")
    assert first.sha256 == second.sha256
    assert first.canonical_document == second.canonical_document


def test_unknown_effect_opcode_blocks_publication(pack_builder: PackBuilder) -> None:
    pack_builder.add_ability("urn:ow:ability:bad", opcode="execute_python")
    with pytest.raises(ContentValidationError, match="unknown effect opcode"):
        pack_builder.validate()
```

- [ ] **Step 2: run the content tests and confirm imports fail**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\content -v
```

- [ ] **Step 3: implement canonical manifests and the content snapshot API**

```python
@dataclass(frozen=True, slots=True)
class ContentSnapshot:
    content_schema_version: str
    content_version: str
    sha256: str
    definitions: Mapping[str, Definition]
    canonical_document: bytes


def load_content_pack(path: Path) -> ContentSnapshot:
    """Validate schemas, IDs, dependencies, references, graphs, opcodes, quotas, and coverage."""
```

Hash canonical UTF-8 JSON with sorted keys and no whitespace. Reject duplicate namespaced IDs,
unresolved dependencies, graph cycles, unreachable classes, illegal numeric floats, and any count or
coverage shortfall. Keep public and GM-only definitions in separate indexed projections.

- [ ] **Step 4: run content tests plus the full gate**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\content -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

- [ ] **Step 5: commit content validation**

```powershell
git add content/schemas src/overlord_worldsim/content.py tests/content
git commit -m "feat: validate versioned content snapshots"
```

### Task 3: Establish SQLite saves, migrations, and atomic transactions

**Files:**

- Create: `src/overlord_worldsim/storage/connection.py`
- Create: `src/overlord_worldsim/storage/locking.py`
- Create: `src/overlord_worldsim/storage/migrations.py`
- Create: `src/overlord_worldsim/storage/transaction.py`
- Create: `src/overlord_worldsim/storage/migrations/0001_initial.sql`
- Create: `tests/storage/test_connection.py`
- Create: `tests/storage/test_migrations.py`
- Create: `tests/storage/test_atomicity.py`

- [ ] **Step 1: write failing persistence-policy and failure-injection tests**

```python
@pytest.mark.parametrize("failure_stage", COMMIT_STAGES)
def test_turn_commit_is_all_old_or_all_new(save: SaveHarness, failure_stage: str) -> None:
    before = save.authoritative_fingerprint()
    save.fail_at(failure_stage)
    with pytest.raises(InjectedFailure):
        save.execute(WAIT_ONE_SECOND)
    assert save.authoritative_fingerprint() == before


def test_connection_enforces_required_pragmas(database: Database) -> None:
    assert database.pragma("foreign_keys") == 1
    assert database.pragma("journal_mode") == "wal"
    assert database.pragma("synchronous") == 2
```

- [ ] **Step 2: run the storage tests and confirm the missing storage layer**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\storage -v
```

- [ ] **Step 3: implement the save envelope and one-writer transaction boundary**

```python
@dataclass(frozen=True, slots=True)
class SaveIdentity:
    database_schema_version: int
    content_schema_version: str
    content_version: str
    rules_version: str
    ruleset_sha256: str
    engine_version: str
    content_sha256: str
    world_seed: int
    branch_id: str
    revision: int


@contextmanager
def immediate_transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
```

The first migration creates metadata, commands, events, RNG streams, branches, definitions snapshot,
entities, projections, scheduler jobs, and narration records with foreign keys and version columns.
Use a process-level slot lock plus SQLite's writer lock. A version or hash mismatch refuses loading
until an explicit tested migration runs.

- [ ] **Step 4: run migrations from every published fixture and the full gate**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\storage -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

- [ ] **Step 5: commit persistence foundations**

```powershell
git add src/overlord_worldsim/storage tests/storage
git commit -m "feat: add atomic version-locked saves"
```

### Task 4: Add deterministic commands, RNG, events, reducers, and replay

**Files:**

- Create: `src/overlord_worldsim/rng.py`
- Create: `src/overlord_worldsim/events/models.py`
- Create: `src/overlord_worldsim/events/reducer.py`
- Create: `src/overlord_worldsim/events/hashing.py`
- Create: `src/overlord_worldsim/events/replay.py`
- Create: `src/overlord_worldsim/commands/models.py`
- Create: `src/overlord_worldsim/commands/service.py`
- Create: `tests/events/test_rng.py`
- Create: `tests/events/test_replay.py`
- Create: `tests/commands/test_execution.py`

- [ ] **Step 1: write failing idempotency, stale-revision, hash, and replay tests**

```python
def test_retrying_command_one_hundred_times_commits_once(engine: Engine) -> None:
    results = [engine.execute("cmd-7", 0, WAIT_ONE_SECOND) for _ in range(100)]
    assert len({result.revision for result in results}) == 1
    assert engine.event_count(command_id="cmd-7") == 1


def test_replay_never_draws_rng(save: SaveHarness) -> None:
    committed = save.execute(ATTACK_COMMAND)
    replayed = replay(save.genesis, save.events, rng=FailOnDrawRng())
    assert replayed.semantic_hash == committed.semantic_hash
```

- [ ] **Step 2: run command/event tests and confirm the missing services**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\events tests\commands -v
```

- [ ] **Step 3: implement the closed command result and reducer interfaces**

```python
type ExecutionResult = CommittedTurn | RejectedCommand


def execute(
    command_id: str,
    expected_revision: int,
    command: StructuredCommand,
) -> ExecutionResult:
    """Reject pre-mechanic errors without a draw; atomically commit valid in-world results."""


def apply(previous_state: State, event: DomainEvent) -> State:
    """Apply a versioned event without external reads or random draws."""
```

Implement PCG32 with named split streams persisted in the same turn transaction. Record every final
draw and mechanical result in the event payload. Canonical event hashes include previous hash,
event type/version, stable ID, game timestamp, and canonical payload. Canonical semantic hashes omit
prose, caches, wall time, and SQLite layout.

- [ ] **Step 4: run deterministic repetition and replay gates**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\events tests\commands -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit deterministic execution**

```powershell
git add src/overlord_worldsim/rng.py src/overlord_worldsim/events src/overlord_worldsim/commands tests/events tests/commands
git commit -m "feat: commit deterministic commands and replayable events"
```

### Task 5: Implement verified backups, immutable branches, and exports

**Files:**

- Create: `src/overlord_worldsim/storage/backups.py`
- Create: `src/overlord_worldsim/storage/branches.py`
- Create: `src/overlord_worldsim/storage/exports.py`
- Create: `src/overlord_worldsim/storage/integrity.py`
- Create: `tests/storage/test_backups.py`
- Create: `tests/storage/test_branches.py`
- Create: `tests/storage/test_exports.py`

- [ ] **Step 1: write failing online-backup, corruption, branch, and export-authority tests**

```python
def test_restore_creates_branch_and_preserves_source(slot: SaveSlot) -> None:
    source = slot.active_branch
    backup = slot.backups.create(reason="manual")
    restored = slot.backups.restore_as_branch(backup.id)
    assert restored.parent_branch_id == source.id
    assert source.semantic_hash == slot.open_branch(source.id).semantic_hash
    assert restored.id != source.id


def test_export_cannot_be_loaded_as_authority(slot: SaveSlot) -> None:
    export_path = slot.exports.create("world")
    with pytest.raises(AuthorityBoundaryError):
        slot.load_authoritative_state(export_path)
```

- [ ] **Step 2: run backup/branch tests and confirm the missing API**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\storage\test_backups.py tests\storage\test_branches.py tests\storage\test_exports.py -v
```

- [ ] **Step 3: implement the recovery API**

```python
class BackupService:
    def create(self, reason: BackupReason) -> BackupRecord:
        """Use SQLite Online Backup and attach hashes, versions, branch, and revision."""

    def verify(self, backup_id: str) -> VerificationReport:
        """Check file SHA-256, integrity, foreign keys, content snapshot, event head, and state hash."""

    def restore_as_branch(self, backup_id: str) -> BranchRecord:
        """Verify in a temporary path, create a namespaced branch, and atomically switch slot.json."""
```

Keep two rolling recovery backups after ordinary state turns. Archive before long advances and
migrations, on manual save, and each 100 events. Quarantine corrupt artifacts. Never copy an active
WAL file, overwrite a branch, merge branches, or reuse entity IDs across branch namespaces.

- [ ] **Step 4: run corruption matrices and the full gate**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\storage -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit recovery and exports**

```powershell
git add src/overlord_worldsim/storage tests/storage
git commit -m "feat: add verified branch-only recovery"
```

### Task 6: Implement characters, acquisition history, growth, magic tiers, and effect opcodes

**Files:**

- Create: `src/overlord_worldsim/characters/models.py`
- Create: `src/overlord_worldsim/characters/prerequisites.py`
- Create: `src/overlord_worldsim/characters/growth.py`
- Create: `src/overlord_worldsim/characters/stats.py`
- Create: `src/overlord_worldsim/characters/magic.py`
- Create: `src/overlord_worldsim/effects/opcodes.py`
- Create: `src/overlord_worldsim/effects/executor.py`
- Create: `tests/characters/`
- Create: `tests/effects/`

- [ ] **Step 1: write failing acquisition-order, cap, growth, tradition, and opcode tests**

```python
def test_prerequisite_is_checked_at_acquisition_time(builder: BuildBuilder) -> None:
    builder.acquire("urn:ow:job:fallen-banner", level=1, tokens={"oath"})
    builder.remove_token("oath")
    assert builder.build().has_job("urn:ow:job:fallen-banner")


def test_pending_level_requires_player_allocation(character: Character) -> None:
    character.award_growth(character.cost_to_next_level)
    assert character.pending_level_allocations == 1
    assert character.total_level_unchanged
```

- [ ] **Step 2: run character/effect tests and confirm missing implementations**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\characters tests\effects -v
```

- [ ] **Step 3: implement ordered builds and a closed opcode registry**

```python
@dataclass(frozen=True, slots=True)
class Acquisition:
    sequence: int
    node_id: str
    resulting_node_level: int
    satisfied_by: tuple[str, ...]


type Prerequisite = AllOf | AnyOf | Not | HasLevel | HasToken | HasTag
type EffectOpcode = DealDamage | Heal | ApplyStatus | Move | SpendResource | Summon | Transform
```

Total level equals all racial and job levels and never exceeds 100. Enforce node caps and graph
reachability. Growth is an audited event; zero-yield repetition and training limits are rules, not
narrator judgment. Track effective caster level per tradition using registered class contribution
rates; do not combine traditions implicitly. Reject arbitrary code and unknown opcodes at load.

- [ ] **Step 4: run property tests across legal and illegal builds**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\characters tests\effects -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit character mechanics**

```powershell
git add src/overlord_worldsim/characters src/overlord_worldsim/effects tests/characters tests/effects
git commit -m "feat: add legal character growth and declarative effects"
```

### Task 7: Implement items, action economy, combat, and life-state mechanics

**Files:**

- Create: `src/overlord_worldsim/items/`
- Create: `src/overlord_worldsim/combat/`
- Create: `tests/items/`
- Create: `tests/combat/`

- [ ] **Step 1: write failing ownership, action, d100, damage-order, resistance, and death tests**

```python
def test_damage_pipeline_uses_constitution_order(combat: CombatHarness) -> None:
    result = combat.resolve(HIGH_PENETRATION_ATTACK)
    assert result.phase_names == (
        "hit",
        "raw_power",
        "penetration",
        "defense",
        "resistance",
        "shield",
        "hp",
    )


@pytest.mark.parametrize(
    ("hp", "expected"),
    [(1, "alive"), (0, "incapacitated"), (-49, "dying"), (-50, "dead")],
)
def test_life_thresholds(hp: int, expected: str) -> None:
    assert life_state(hp=hp, max_hp=100) == expected
```

- [ ] **Step 2: run item/combat tests and confirm missing modules**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\items tests\combat -v
```

- [ ] **Step 3: implement registered primitives and exact combat order**

```python
@dataclass(frozen=True, slots=True)
class TurnBudget:
    move: int = 1
    major: int = 1
    minor: int = 1
    reaction: int = 1


class DamagePhase(StrEnum):
    HIT = "hit"
    RAW_POWER = "raw_power"
    PENETRATION = "penetration"
    DEFENSE = "defense"
    RESISTANCE = "resistance"
    SHIELD = "shield"
    HP = "hp"
```

Track item instance identity, slot, owner, container, durability, charges, and tombstone. Distance is
integer fixed point in metres; durations and cooldowns advance by game seconds. Initiative is rolled
once and ties sort by agility then stable ID. Opposed checks add d100, action rating, and situational
modifier and compare with `50 + defense_rating`; non-opposed checks use an explicit fixed DC. Store
the roll, ratings/modifiers, defense or DC, and margin separately. Same-source named effects take the
strongest; distinct sources add within category, then categories multiply under fixed-point rules.
Resistance caps at 9,000 bp without explicit immunity. Ordinary healing cannot clear dead.
Resurrection, execution,
summoning, transformation, and domains execute only registered opcodes and constraints.

- [ ] **Step 4: run combat invariants and full gates**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\items tests\combat -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit combat mechanics**

```powershell
git add src/overlord_worldsim/items src/overlord_worldsim/combat tests/items tests/combat
git commit -m "feat: resolve items combat and life states"
```

### Task 8: Publish encyclopedia-scale mechanics and original world canon

**Files:**

- Create: `content/mechanics/manifest.json`
- Create: `content/mechanics/races/`
- Create: `content/mechanics/jobs/`
- Create: `content/mechanics/abilities/`
- Create: `content/mechanics/spells/`
- Create: `content/mechanics/items/`
- Create: `content/world/manifest.json`
- Create: `content/world/public/`
- Create: `content/gm/manifest.json`
- Create: `content/gm/hidden/`
- Test: `tests/content/test_published_pack.py`

- [ ] **Step 1: write failing quota, role, tier, build, reference, and public/hidden separation tests**

```python
def test_published_minima(content: ContentSnapshot) -> None:
    assert content.count("racial_node") >= 60
    assert content.count("job_class_node") >= 180
    assert content.count_distinct_abilities(ignore_numeric_upgrades=True) >= 800
    assert content.count("spell") >= 360
    assert content.count("item") >= 500
    assert content.count("sovereign_polity") >= 14
    assert content.count("major_organization") >= 48
    assert content.count("full_important_npc") >= 120
```

- [ ] **Step 2: run the publication test and observe quota failures**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\content\test_published_pack.py -v
```

- [ ] **Step 3: author content in independently valid batches**

Each definition uses its stable namespace ID, version, dependencies, tags, references, and only
registered opcodes. Cover tiers 0–10 and super plus attack, defense, control, support, scouting, and
counter roles. Cover equipment slots, rarity, level bands, damage types, tactical roles, counters,
and every start build. Publish the fallen-god-age empire only as public history and observable canon
in `content/world/public`; keep GM truth records in `content/gm/hidden` and exclude them from public
manifests and narrator payloads.

- [ ] **Step 4: validate every batch and final canonical pack**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\content -v
.\.venv\Scripts\python.exe -m overlord_worldsim content validate --path content
```

Expected: all schema, reference, dependency, graph, opcode, quota, coverage, scarcity, and hidden
separation checks pass.

- [ ] **Step 5: commit published content**

```powershell
git add content tests/content
git commit -m "feat: publish mechanics encyclopedia and continent canon"
```

### Task 9: Implement NPC knowledge, factions, economy, territory, armies, and demographics

**Files:**

- Create: `src/overlord_worldsim/world/knowledge.py`
- Create: `src/overlord_worldsim/world/npcs.py`
- Create: `src/overlord_worldsim/world/relationships.py`
- Create: `src/overlord_worldsim/world/factions.py`
- Create: `src/overlord_worldsim/world/markets.py`
- Create: `src/overlord_worldsim/world/armies.py`
- Create: `src/overlord_worldsim/world/demographics.py`
- Create: `tests/world/`

- [ ] **Step 1: write failing belief, relationship, plan, scarcity, faction, war, and aging tests**

```python
def test_false_belief_does_not_change_objective_fact(world: WorldHarness) -> None:
    world.tell(npc="npc:a", claim="bridge_safe", truth=False, confidence_bp=8000)
    assert world.belief("npc:a", "bridge_safe").value is True
    assert world.fact("bridge_safe").value is False


def test_dead_npc_has_no_orphaned_future_plan(world: WorldHarness) -> None:
    world.kill("npc:a")
    assert world.pending_plans(owner="npc:a") == ()
```

- [ ] **Step 2: run world tests and confirm missing simulation modules**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\world -v
```

- [ ] **Step 3: implement the three simulation tiers and authoritative resources**

```python
class SimulationTier(StrEnum):
    FULL = "full"
    SUMMARY = "summary"
    AGGREGATE = "aggregate"


@dataclass(frozen=True, slots=True)
class Memory:
    subject_id: str
    claim_id: str
    source_id: str
    learned_at: GameTimestamp
    confidence_bp: int
    secrecy: int
    event_id: str
```

Store directional relationships. Full and summary NPCs own plans; aggregate cohorts do not. Model
faction treasury, food, population/manpower, logistics, stability, legitimacy, influence,
intelligence, and territory. Markets use stock and price indices. Armies use strength, training,
morale, supply, command, terrain, and magic. Derive age from birth date; keep agelessness separate
from death immunity. Resolve important life events individually and background demographics yearly.
Enforce all scarcity caps at generation and simulation boundaries.

- [ ] **Step 4: run knowledge-leak and world invariant tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\world -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit world simulation**

```powershell
git add src/overlord_worldsim/world tests/world
git commit -m "feat: simulate beliefs factions economy and war"
```

### Task 10: Implement deterministic scheduling, long advances, projections, and slash views

**Files:**

- Create: `src/overlord_worldsim/scheduler/queue.py`
- Create: `src/overlord_worldsim/scheduler/advance.py`
- Create: `src/overlord_worldsim/views/projections.py`
- Create: `src/overlord_worldsim/views/slash.py`
- Create: `src/overlord_worldsim/session.py`
- Create: `tests/scheduler/`
- Create: `tests/views/`
- Create: `tests/test_session_protocol.py`

- [ ] **Step 1: write failing ordering, chunk recovery, segmentation, query-purity, and leak tests**

```python
def test_year_equals_twelve_months(world_factory: WorldFactory) -> None:
    yearly = world_factory(seed=17)
    monthly = world_factory(seed=17)
    yearly.advance(years=1, activity=FARM_ROUTINE)
    for _month in range(12):
        monthly.advance(months=1, activity=FARM_ROUTINE)
    assert yearly.semantic_hash == monthly.semantic_hash


@pytest.mark.parametrize("view", QUERY_VIEWS)
def test_query_is_pure_and_hides_sentinels(save: SaveHarness, view: str) -> None:
    before = save.authoritative_fingerprint()
    output = save.query(viewer="pc", view=view, revision=save.revision)
    assert "GM_ONLY_SENTINEL" not in output.canonical_text
    assert save.authoritative_fingerprint() == before
```

- [ ] **Step 2: run scheduler/view tests and confirm missing modules**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\scheduler tests\views tests\test_session_protocol.py -v
```

- [ ] **Step 3: implement stable queues, persistent jobs, and viewer projections**

```python
@dataclass(frozen=True, order=True, slots=True)
class ScheduleKey:
    game_timestamp: int
    phase: int
    priority: int
    stable_id: str


def query(viewer: str, view: ViewName, revision: int) -> ViewerProjection:
    """Return projected knowledge without time, RNG, events, resources, or revision changes."""
```

Support second, daily, weekly/monthly, seasonal, and annual phases. Long jobs persist target time,
processed time, next schedule key, status, and activity. Require an explicit activity or stored
routine above 24 hours; otherwise use zero-growth safe maintenance. Commit deterministic chunks,
resume from the last committed boundary, and interrupt for the five constitution events. Version 1
does not cancel a running job.

Implement `/status`, `/skills`, `/inventory`, `/map`, `/relations`, `/time`, `/log`, `/help`, and
`/rules` as pure projected queries. `/save` invokes verified backup without changing world state.
Branch mutation uses explicit branch service calls.

- [ ] **Step 4: verify health-check, intent, commit-before-narration, and render-retry protocol**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\scheduler tests\views tests\test_session_protocol.py -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit session and time orchestration**

```powershell
git add src/overlord_worldsim/scheduler src/overlord_worldsim/views src/overlord_worldsim/session.py tests/scheduler tests/views tests/test_session_protocol.py
git commit -m "feat: advance time and expose safe projected views"
```

### Task 11: Implement all character start modes and stop before the prologue

**Files:**

- Create: `src/overlord_worldsim/creator/models.py`
- Create: `src/overlord_worldsim/creator/service.py`
- Create: `src/overlord_worldsim/creator/budgets.py`
- Create: `tests/creator/test_modes.py`
- Create: `tests/creator/test_legal_history.py`
- Create: `tests/creator/test_agency.py`

- [ ] **Step 1: write failing mode, budget, acquisition-history, and player-agency tests**

```python
@pytest.mark.parametrize(
    ("mode", "level"),
    [("ordinary", 1), ("heroic", 35), ("legendary", 60), ("otherworld_player", 100)],
)
def test_start_mode_builds_exact_legal_level(mode: str, level: int, creator: Creator) -> None:
    draft = creator.draft(mode=mode, choices=complete_choices_for(mode))
    assert draft.total_level == level
    assert validate_acquisition_history(draft.acquisitions).is_valid


def test_level_100_gear_waits_for_player(creator: Creator) -> None:
    draft = creator.draft(mode="otherworld_player", choices=choices_without_gear())
    assert draft.needs_choice == "equipment_package"
    assert draft.selected_equipment == ()
```

- [ ] **Step 2: run creator tests and confirm the missing service**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\creator -v
```

- [ ] **Step 3: implement the staged creator**

```python
@dataclass(frozen=True, slots=True)
class CharacterDraft:
    mode: StartMode
    identity: Identity
    origin_id: str
    region_id: str
    concept: str
    acquisitions: tuple[Acquisition, ...]
    talent_ids: tuple[str, ...]
    appearance: str
    personality: str
    selected_equipment: tuple[str, ...]
    needs_choice: str | None
```

Collect identity, age, race, origin, region, concept, legal ordered acquisitions, talents,
appearance, personality, and equipment. Apply distinct budgets for ordinary, heroic, legendary, and
otherworld-player starts. Allow level 1–100 custom starts and mark budget overrides as custom while
preserving caps and references. Restricted nodes need origin authorization or achievement tokens.
Commit the completed creation command and stop before any prologue action or narration.

- [ ] **Step 4: run every start build and full gates**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\creator -v
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
```

- [ ] **Step 5: commit the creator**

```powershell
git add src/overlord_worldsim/creator tests/creator
git commit -m "feat: create legal player-selected start builds"
```

### Task 12: Prove release invariants and soak determinism

**Files:**

- Create: `tests/acceptance/test_determinism.py`
- Create: `tests/acceptance/test_replay.py`
- Create: `tests/acceptance/test_failure_injection.py`
- Create: `tests/acceptance/test_hidden_information.py`
- Create: `tests/acceptance/test_long_advance.py`
- Create: `tests/acceptance/test_invariants.py`
- Create: `tests/soak/test_state_machine.py`
- Create: `scripts/run_soak.py`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: encode the release acceptance matrix as failing tests**

```python
def test_same_seed_and_commands_produce_same_hashes(scenario: Scenario) -> None:
    first = scenario.run(seed=99)
    second = scenario.run(seed=99)
    assert first.semantic_state_hash == second.semantic_state_hash
    assert first.event_head_hash == second.event_head_hash


def test_all_hidden_sentinels_are_absent_from_every_surface(leak_harness: LeakHarness) -> None:
    leak_harness.seed_every_hidden_field("GM_ONLY_SENTINEL")
    assert leak_harness.scan_all_queries_narrator_inputs_and_outputs() == ()
```

- [ ] **Step 2: run acceptance tests and capture each unmet invariant**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\acceptance -v
```

- [ ] **Step 3: close only the behavior gaps exposed by those tests**

Require schema/reference/cycle/opcode/quota coverage; transaction failure atomicity; deterministic
hashes; replay equivalence; idempotency; stale-revision rejection; long-job recovery and segmented
time equivalence; immutable branch restore; zero hidden sentinels; life, item, time, NPC knowledge,
relationship, faction, and scarcity invariants; and every start mode.

- [ ] **Step 4: run the regular state-machine budget**

```powershell
.\.venv\Scripts\python.exe scripts\run_soak.py --seeds 20 --actions 1000
```

Expected: zero broken references, invariant failures, event-chain failures, nondeterministic hashes,
hidden leaks, or scarcity violations.

- [ ] **Step 5: run the long state-machine budget**

```powershell
.\.venv\Scripts\python.exe scripts\run_soak.py --seeds 100 --actions 10000
```

Expected: the same zero-failure conditions across one million actions.

- [ ] **Step 6: run the release gate and commit CI**

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=overlord_worldsim --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
git add tests/acceptance tests/soak scripts/run_soak.py .github/workflows/ci.yml
git commit -m "test: enforce deterministic worldsim release gates"
```
