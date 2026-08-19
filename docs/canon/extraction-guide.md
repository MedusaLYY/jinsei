# Canon Extraction Guide (M4)

Authoritative conventions for per-volume extraction from the Mushoku Tensei
raw text into structured batches (`data/canon/V###.json`), verified with
`canon verify` and committed with `canon apply`.

## Pipeline

1. Read the volume text: `data/parsed/chunks.jsonl`, filter `volume_no == N`,
   ordered by `source_start_line`. Use `text` verbatim; never paraphrase in
   evidence.
2. Read every prior batch `data/canon/V###.json` (lower volume numbers) to
   build the entity registry: `entity_id`, `name`, `aliases`, `kind`,
   `introduced_volume`, `introduced_line`, `description`.
3. Write the candidate batch for volume N; id numbers continue the global
   sequence of prior batches (entities `E0001+`, facts `F0001+`,
   relationships `R0001+`, knowledge `K0001+`, events `T0001+`, phases
   `P0001+`).
4. Verify: `canon verify --source data/raw/无职转生TXT合集.txt --candidate
   data/canon/V###.json --out data/canon/V###.report.json` — fix until clean.
5. Apply: `canon apply --db data/db/canon.sqlite3 --source
   data/raw/无职转生TXT合集.txt --candidate data/canon/V###.json`.

Extraction proceeds strictly by volume order; do not skip ahead.

## Batch shape

- `batch_id`: `V001`…`V026` (tail CROSSOVER units are never extracted; they
  remain retrieval-only chunks).
- `source_volume`: the volume number.
- `source_unit_ids`: every unit id of the volume (from `chapters.json`).

## Entities

- One entry per *named, recurring, or plot-relevant* entity. Include: major
  and minor characters, named locations, named organizations, notable
  items/artifacts (kind `ITEM`).
- `kind`: `CHARACTER`, `LOCATION`, `ORGANIZATION`, `ITEM`, `ABILITY`, `UNKNOWN`
  (species/races are expressed as facts on the character, not entities).
- First appearance: `introduced_volume` / `introduced_line` = the volume and
  line of the first mention (line within the volume's unit ranges, verifier
  enforced).
- Every entity referenced by a fact/relationship/event/phase **must be
  re-declared in the batch** with its original introduction data (the
  verifier only knows the current batch). Re-declared entries are identical
  to the registry, except `description` may be enriched.
- Aliases: all alternative names seen in the text (given name, nickname,
  title variants). No invented aliases.
- `description`: one factual sentence grounded in the text.

## Facts

- Predicates: `年纪`, `职业`, `称号`, `身份`, `住处`, `外貌`, `性格`,
  `擅长`, `弱点`, `梦想`, `经历`, `状态`, `所属`, `持有` (items),
  `信仰`, `约定`. Use the narrowest fit; do not invent new predicates without
  adding them here first.
- Family and social links go to `relationships`, not facts.
- `start_date` / `end_date`: only when the text (or a strong inference from an
  explicit age) supports a `YYYY-M` date; else `null` with
  `date_precision: "UNKNOWN"`. Explicit in-text years get `EXACT`/`YEAR_ONLY`.
- `visible_from_volume`: the volume where the fact becomes knowable (never
  before its source volume). `visible_to_volume`: `null` while ongoing, else
  the last volume where it holds.
- `confidence`: `EXPLICIT` (stated), `STRONG_INFERENCE` (deducible from the
  text), `INFERENCE` (plausible), `UNKNOWN`.
- `evidence_volumes` / `evidence_lines`: the exact chunk line ranges of the
  supporting sentences (from chunks.jsonl). Lines must fall inside the
  volume's units.

## Relationships

- Directed: `source_id` → `target_id` with `rel_type` like `父子`, `母子`,
  `兄妹`, `师徒`, `主仆`, `朋友`, `敌人`, `配偶`, `恋爱`, `同事`.
- `kind` (enum, not free text): `FAMILY` for blood/family ties, `MENTOR`
  for teaching, `FRIEND`, `ENEMY`, `ROMANTIC`, `ORGANIZATIONAL` for
  same-group ties, `UNKNOWN` otherwise.
- Same evidence, confidence, and visibility rules as facts.

## Events

- Major plot milestones: the reincarnation, the move, the transfer
  incident, world-shaking occurrences; per-volume arcs get one or two events
  each. `title` short, `description` one sentence, `date` only when the text
  supports it, `participants` = involved entity ids.

## Phases

- Life-stage segments per main character: `幼年期`, `少年期`, `学园期`,
  `冒险期`, `成年期`, etc. One or two per character per volume, with
  evidence.

## Knowledge

- What a character demonstrably knows about a fact (`owner_id` = the knower,
  `fact_id` = the known fact, `certainty`). Only include knowledge explicitly
  shown in the text. `note`: one short sentence.
- Knowledge rows may reference facts declared in this volume's batch.

## Prohibitions

- No invented names, places, dates, or relations absent from the text.
- No GM/hidden facts: anything the volume's characters could not know must
  not be declared with an earlier `visible_from_volume`.
- No speculation as fact: mark inference with the confidence ladder.
- Never edit prior batches; later volumes may only add new facts or phases.