# Game Master Protocol

This protocol is mandatory for any agent or interface operating an Overlord WorldSim gameplay
session. It separates player language, deterministic adjudication, authoritative state, hidden
knowledge, and narration.

## 1. Open the session safely

Do not accept an action until the active save is healthy and loaded.

1. Resolve the slot's active branch pointer and acquire the single-writer save lock.
2. Open the branch through the engine; never edit SQLite directly.
3. Verify `integrity_check`, foreign keys, database schema, content schema, rules version, engine
   version, locked ruleset SHA-256, locked content snapshot SHA-256, world seed, event hash head,
   semantic state hash, revision, and all PCG32 stream positions.
4. Detect pending migrations, unresolved player choices, committed-but-unrendered turns, and active
   long-advance jobs. Refuse incompatible state and route recovery through supported operations.
5. Load the player projection only. Report active branch, game date/time, revision, current player
   condition, and any pending choice without revealing hidden facts.

## 2. Interpret without taking agency

Translate each player message into `IntentDraft` or `Clarification`. Preserve the original text for
the command audit. Resolve names against visible, registered entities and definitions.

Ask a clarification when target, scope, route, resource commitment, risk posture, or another
high-impact choice is ambiguous. Never select a player action, level, talent, equipment package,
dialogue promise, or moral decision. Never create an unregistered ability or silently substitute a
different one.

Ambiguous and invalid drafts are rejected before transaction start. They consume no time, RNG,
resource, event, or revision.

## 3. Commit mechanics before narration

For a valid structured command, enforce this order:

1. Check `command_id`, `expected_revision`, prerequisites, references, ownership, range, costs, and
   the save's locked rules/content snapshot.
2. Begin the engine's immediate transaction and draw only from the command's assigned deterministic
   PCG32 stream.
3. Resolve the d100 check and other mechanics. A failed in-world attempt is still a real result.
4. Record final rolls and modifiers, state-changing events, speech or claims, resource/time changes,
   RNG state, command result, event hash, semantic state hash, and revision atomically.
5. Commit, then process due background events in stable scheduler order.
6. Build a fresh viewer projection and narrate only the committed visible result.

If step 6 fails, retain the committed outcome and retry rendering. Never reroll, edit the database,
or backsolve mechanics from preferred prose.

## 4. Protect hidden information

The adjudicator may use hidden state; the narrator may not receive it. Pass the narrator only the
viewer projection and visible events. Player-facing roll summaries include the player's roll and
known modifiers, but omit secret DCs, enemy abilities, private plans, concealed beliefs, hidden
rolls, and GM-only causation. Describe only observable effects.

NPC facts, NPC beliefs, and player knowledge are distinct. A rumor can be false. A hidden truth does
not become player knowledge because it exists in the database. No slash view may bypass this
projection boundary.

## 5. Preserve player choice and continuity

Never move, speak, spend, equip, level, accept a quest, form a relationship, or make a strategic
choice for the player without an explicit standing routine that covers that exact low-risk action.
Interrupt long advances for lethal danger, capture, forced relocation, exhausted required
resources, or pending player level allocation.

Death is an engine result, not a narration preference. Ordinary healing cannot clear `dead`.
Registered resurrection follows its own constraints. After player death, present the supported
choices—new character, continued observation, or restore from a checkpoint as a new branch—and
wait. Never auto-rewind, overwrite the dead timeline, or merge branches.

## 6. Keep queries pure

`/status`, `/skills`, `/inventory`, `/map`, `/relations`, `/time`, and `/log` are read-only projected
queries. `/help` and `/rules` are read-only public-reference queries. They do not consume RNG,
advance game time, emit domain events, or increment revision. `/save` creates a verified recovery
artifact outside world state. `/branch` inspection is read-only; branch creation or activation is a
separate explicit operation.

## 7. Long advances

Any requested advance longer than 24 game-hours needs an explicit long-term activity or stored
routine. Without either, apply only `safe_maintenance`: ordinary food, rest, and shelter upkeep with
zero free growth. Run the persistent advance job in deterministic chunks and stop at the mandated
interruptions. Resuming after a crash continues from the last committed chunk and never repeats a
draw or event.
