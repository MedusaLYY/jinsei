"""Loading and validation for the frozen core rules constitution."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import cast

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type _FieldPathComponent = str | int
type _FieldPath = tuple[_FieldPathComponent, ...]


class RulesetValidationError(ValueError):
    """Raised when a ruleset cannot be read or violates the frozen contract."""


class _DuplicateJsonKeyError(ValueError):
    """Internal signal used to reject ambiguous JSON objects."""

    def __init__(self, key: str) -> None:
        super().__init__("duplicate JSON object key")
        self.key = key


class _JsonIntegerLimitError(ValueError):
    """Internal signal used when a JSON integer exceeds the loader-owned limit."""


_MAX_JSON_INTEGER_DIGITS = 4_300
# Rulesets are compact constitutional documents; cap input before decoding or parsing.
_MAX_RULESET_BYTES = 4 * 1024 * 1024
_MAX_DIAGNOSTIC_STRING_PREVIEW_CHARS = 64
_MAX_DIAGNOSTIC_INTEGER_MAGNITUDE = 10**18
_MAX_DIAGNOSTIC_PATH_CHARS = 320
_MAX_DIAGNOSTIC_MESSAGE_CHARS = 480
_DIAGNOSTIC_TRUNCATION_SUFFIX = "...<truncated>"


_EXPECTED_MAGIC_THRESHOLDS: dict[str, JsonValue] = {
    "0": 0,
    "1": 1,
    "2": 8,
    "3": 15,
    "4": 22,
    "5": 29,
    "6": 36,
    "7": 43,
    "8": 50,
    "9": 57,
    "10": 64,
    "super": 70,
}

_EXPECTED_DAMAGE_PHASES: list[JsonValue] = [
    "hit",
    "raw_power",
    "penetration",
    "defense",
    "resistance",
    "shield",
    "hp",
]

_EXPECTED_FIELDS: tuple[tuple[tuple[str, ...], JsonValue], ...] = (
    (("ruleset_id",), "urn:overlord-worldsim:ruleset:core"),
    (("schema_version",), "1.0.0"),
    (("rules_version",), "1.0.0"),
    (("compatibility", "minimum_engine_version"), "0.1.0"),
    (("compatibility", "expansion_policy"), "controlled_versioned_only"),
    (("numeric_policy", "authoritative_values"), "signed_integers"),
    (("numeric_policy", "binary_floating_point_allowed"), False),
    (("numeric_policy", "fixed_point_scale"), 10_000),
    (("numeric_policy", "ratio_unit"), "basis_points"),
    (("numeric_policy", "basis_points_per_whole"), 10_000),
    (("numeric_policy", "rounding"), "half_away_from_zero"),
    (("calendar", "months_per_year"), 12),
    (("calendar", "days_per_month"), 30),
    (("calendar", "intercalary_days"), 5),
    (("calendar", "days_per_year"), 365),
    (("calendar", "hours_per_day"), 24),
    (("calendar", "minutes_per_hour"), 60),
    (("calendar", "seconds_per_minute"), 60),
    (("progression", "maximum_total_level"), 100),
    (("progression", "level_caps", "base"), 15),
    (("progression", "level_caps", "advanced"), 10),
    (("progression", "level_caps", "rare"), 5),
    (("progression", "level_caps", "hidden"), 5),
    (("progression", "level_caps", "legendary"), 5),
    (("progression", "level_caps", "world"), 5),
    (("progression", "growth_cost_formula"), "100 * target_level^2"),
    (("progression", "clock"), "game_time_only"),
    (("progression", "growth_event_stream"), "unified_audited"),
    (
        ("progression", "eligible_activity_domains"),
        ["combat", "research", "politics", "trade", "governance", "training"],
    ),
    (("progression", "repetitive_riskless_or_under_level_yield_may_be_zero"), True),
    (("progression", "pending_allocation_requires_player_choice"), True),
    (
        ("progression", "prerequisites"),
        {
            "operators": ["all", "any", "not"],
            "checked_at": "acquisition_time",
            "ordered_history_required": True,
            "later_condition_loss_revokes_level": False,
        },
    ),
    (("magic", "minimum_caster_level_by_tier"), _EXPECTED_MAGIC_THRESHOLDS),
    (("magic", "traditions_combine_implicitly"), False),
    (("magic", "class_contribution_rates_require_registered_content"), True),
    (("magic", "tier_minimums_do_not_bypass_content_prerequisites"), True),
    (
        ("effects",),
        {
            "execution_model": "registered_declarative_opcodes",
            "arbitrary_python_allowed": False,
            "unknown_opcode_policy": "reject_content_load",
        },
    ),
    (("checks", "die"), "d100"),
    (("checks", "roll_minimum"), 1),
    (("checks", "roll_maximum"), 100),
    (("checks", "roll_total_formula"), "d100 + action_rating + situational_modifier"),
    (("checks", "opposed_target_formula"), "50 + defense_rating"),
    (("checks", "non_opposed_target"), "explicit_fixed_dc"),
    (("checks", "success_condition"), "roll_total >= target"),
    (("checks", "natural_1_automatic_failure"), False),
    (("checks", "natural_100_automatic_success"), False),
    (("checks", "natural_rolls_override_feasibility"), False),
    (
        ("checks", "audit_fields"),
        [
            "roll",
            "action_rating",
            "situational_modifiers",
            "defense_or_fixed_dc",
            "margin",
        ],
    ),
    (
        ("checks", "visibility"),
        {
            "player_roll_visible": True,
            "known_modifiers_visible": True,
            "secret_defense_or_dc_hidden": True,
            "hidden_rolls_hidden": True,
        },
    ),
    (("combat", "round_seconds"), 6),
    (("combat", "action_economy", "move_per_turn"), 1),
    (("combat", "action_economy", "major_per_turn"), 1),
    (("combat", "action_economy", "minor_per_turn"), 1),
    (("combat", "action_economy", "reaction_per_round"), 1),
    (("combat", "action_economy", "unused_actions"), "expire"),
    (("combat", "action_economy", "reaction_refresh"), "start_of_round"),
    (("combat", "damage_resolution", "phases"), _EXPECTED_DAMAGE_PHASES),
    (("combat", "damage_resolution", "final_damage_may_be_zero"), True),
    (("combat", "resistance", "unit"), "basis_points"),
    (("combat", "resistance", "maximum_without_immunity"), 9_000),
    (("combat", "resistance", "explicit_immunity_required"), True),
    (("combat", "resistance", "immunity_bypasses_damage"), True),
    (("life", "states"), ["alive", "incapacitated", "dying", "dead"]),
    (("life", "thresholds", "alive"), "hp > 0"),
    (("life", "thresholds", "incapacitated"), "hp == 0"),
    (("life", "thresholds", "dying"), "-max_hp / 2 < hp < 0"),
    (("life", "thresholds", "dead"), "hp <= -max_hp / 2"),
    (("life", "thresholds", "integer_evaluation"), "compare 2 * hp with -max_hp"),
    (("life", "direct_death", "valid_execution"), True),
    (("life", "direct_death", "registered_instant_death_effect"), True),
    (("life", "ordinary_healing_clears_dead"), False),
    (("life", "resurrection_requires_registered_ability"), True),
    (("life", "continuity"), "true_death_with_branch_reload"),
    (("time", "progression_clock"), "game_time_only"),
    (("time", "wall_clock_progression"), False),
    (("time", "long_jump", "threshold_game_hours"), 24),
    (("time", "long_jump", "comparison"), "strictly_greater_than"),
    (
        ("time", "long_jump", "activity_precedence"),
        ["explicit_long_term_activity", "stored_routine", "safe_maintenance"],
    ),
    (("time", "long_jump", "fallback_activity"), "safe_maintenance"),
    (
        ("time", "long_jump", "safe_maintenance_scope"),
        ["ordinary_food", "ordinary_rest", "ordinary_shelter_upkeep"],
    ),
    (("time", "long_jump", "safe_maintenance_free_growth"), 0),
    (
        ("time", "long_jump", "interruptions"),
        [
            "lethal_danger",
            "capture",
            "forced_relocation",
            "exhausted_required_resources",
            "pending_player_level_allocation",
        ],
    ),
    (("content", "minimum_counts", "racial_nodes"), 60),
    (("content", "minimum_counts", "job_class_nodes"), 180),
    (("content", "minimum_counts", "distinct_abilities"), 800),
    (("content", "minimum_counts", "spells"), 360),
    (("content", "minimum_counts", "items"), 500),
    (("content", "numeric_upgrades_count_as_distinct_abilities"), False),
    (
        ("content", "spell_tiers_required"),
        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "super"],
    ),
    (
        ("content", "spell_roles_required"),
        ["attack", "defense", "control", "support", "scouting", "counter"],
    ),
    (
        ("content", "item_categories_required"),
        ["equipment", "consumable", "material", "key_item"],
    ),
    (("content", "unusable_filler_counts_toward_item_minimum"), False),
    (("world", "minimum_counts", "sovereign_polities"), 14),
    (("world", "minimum_counts", "major_organizations"), 48),
    (("world", "minimum_counts", "full_important_npcs"), 120),
    (("world", "summary_npcs_required"), True),
    (("world", "aggregate_population_required"), True),
    (("world", "public_and_gm_hidden_projections_separate"), True),
    (
        ("start_modes",),
        [
            {"id": "ordinary", "level": 1},
            {"id": "heroic", "level": 35},
            {"id": "legendary", "level": 60},
            {"id": "otherworld_player", "level": 100},
            {"id": "custom", "minimum_level": 1, "maximum_level": 100},
        ],
    ),
    (
        ("character_creation",),
        {
            "legal_ordered_acquisition_history_required": True,
            "restricted_node_authorization": "origin_authorization_or_achievement_token",
            "mode_budgets": ["talent", "wealth", "equipment"],
            "custom_budget_override_marks_save_custom": True,
            "custom_may_break_total_level_cap": False,
            "custom_may_break_reference_integrity": False,
            "level_100_equipment_requires_player_choice": True,
            "stop_before_prologue": True,
        },
    ),
    (("scarcity", "sapient_population_below_level_20_minimum_basis_points"), 9_900),
    (("scarcity", "random_generation_maximum_level"), 34),
    (("scarcity", "all_npcs_at_or_above_level_must_be_named"), 45),
    (
        ("scarcity", "native_population_caps"),
        [
            {"minimum_level": 60, "maximum_level": 74, "maximum_count": 24},
            {"minimum_level": 75, "maximum_level": 89, "maximum_count": 9},
            {"minimum_level": 90, "maximum_level": 99, "maximum_count": 2},
        ],
    ),
    (("scarcity", "public_native_level_100_allowed"), False),
    (("authored_content", "scale"), "encyclopedia"),
    (("authored_content", "canon_policy"), "fixed"),
    (("authored_content", "seeded_noncritical_detail"), True),
    (("authored_content", "expansion_policy"), "controlled_versioned_only"),
)


@dataclass(frozen=True, slots=True)
class Ruleset:
    """A validated, typed view over a versioned ruleset document."""

    ruleset_id: str
    schema_version: str
    rules_version: str
    _document: JsonObject = field(repr=False)
    _growth_costs: Mapping[int, int] = field(repr=False)
    _magic_thresholds: Mapping[str, int] = field(repr=False)

    def growth_cost_for(self, target_level: int) -> int:
        """Return the frozen growth cost for a target level from 1 through 100."""
        if type(target_level) is not int:
            raise ValueError(
                _bounded_diagnostic_message(
                    "target level must be an integer from 1 through 100; got ",
                    _render_diagnostic_value(target_level),
                )
            )
        try:
            return self._growth_costs[target_level]
        except KeyError as error:
            rendered_target = (
                _render_small_decimal(target_level)
                if -_MAX_DIAGNOSTIC_INTEGER_MAGNITUDE
                <= target_level
                <= _MAX_DIAGNOSTIC_INTEGER_MAGNITUDE
                else _render_diagnostic_value(target_level)
            )
            raise ValueError(
                _bounded_diagnostic_message(
                    "target level must be from 1 through 100; got ", rendered_target
                )
            ) from error

    def minimum_level_for_magic_tier(self, tier: str | int) -> int:
        """Return the minimum caster level for a numbered tier or ``super``."""
        if type(tier) is int:
            if not 0 <= tier <= 10:
                rendered_tier = (
                    _render_small_decimal(tier)
                    if -_MAX_DIAGNOSTIC_INTEGER_MAGNITUDE
                    <= tier
                    <= _MAX_DIAGNOSTIC_INTEGER_MAGNITUDE
                    else _render_diagnostic_value(tier)
                )
                raise ValueError(_bounded_diagnostic_message("unknown magic tier: ", rendered_tier))
            normalized_tier = _render_small_decimal(tier)
        elif isinstance(tier, str):
            normalized_tier = tier
        else:
            raise ValueError(
                _bounded_diagnostic_message("unknown magic tier: ", _render_diagnostic_value(tier))
            )
        try:
            return self._magic_thresholds[normalized_tier]
        except KeyError as error:
            raise ValueError(
                _bounded_diagnostic_message("unknown magic tier: ", _render_diagnostic_value(tier))
            ) from error

    def to_dict(self) -> JsonObject:
        """Return a detached JSON-compatible copy of the ruleset document."""
        return copy.deepcopy(self._document)


def load_ruleset(path: str | Path) -> Ruleset:
    """Load a ruleset of at most 4 MiB and reject inconsistent content."""
    rules_path = Path(path)
    rendered_rules_path = _render_diagnostic_rules_path(rules_path)
    try:
        with rules_path.open("rb") as rules_file:
            serialized_bytes = rules_file.read(_MAX_RULESET_BYTES + 1)
    except OSError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(rendered_rules_path, ": cannot read ruleset")
        ) from error

    if len(serialized_bytes) > _MAX_RULESET_BYTES:
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                rendered_rules_path,
                ": ruleset exceeds maximum size of ",
                _render_small_decimal(_MAX_RULESET_BYTES),
                " bytes",
            )
        )

    try:
        serialized = serialized_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                rendered_rules_path,
                ": ruleset is not valid UTF-8 at byte ",
                _render_small_decimal(error.start),
            )
        ) from error

    try:
        parsed = cast(
            object,
            json.loads(
                serialized,
                object_pairs_hook=_object_with_unique_keys,
                parse_int=_parse_bounded_json_integer,
            ),
        )
    except json.JSONDecodeError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                rendered_rules_path,
                ": malformed JSON at line ",
                _render_small_decimal(error.lineno),
                ", column ",
                _render_small_decimal(error.colno),
                ": ",
                _render_diagnostic_string_literal(error.msg),
            )
        ) from error
    except _DuplicateJsonKeyError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                rendered_rules_path,
                ": malformed JSON: duplicate object key ",
                _render_diagnostic_key(error.key),
            )
        ) from error
    except _JsonIntegerLimitError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                rendered_rules_path,
                ": malformed JSON: JSON integer exceeds the safe digit limit",
            )
        ) from error
    except RecursionError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(rendered_rules_path, ": JSON nesting is too deep")
        ) from error

    if not isinstance(parsed, dict):
        raise RulesetValidationError(
            _bounded_diagnostic_message(rendered_rules_path, ": ruleset root must be a JSON object")
        )

    document = cast(JsonObject, parsed)
    try:
        _validate_no_unknown_fields(document)
        _reject_floating_point(document)
        growth_costs = _validate_growth_costs(document)
        _validate_damage_phases(document)
        for field_path, expected in _EXPECTED_FIELDS:
            _expect(document, field_path, expected)
        validated_document = copy.deepcopy(document)
    except RecursionError as error:
        raise RulesetValidationError(
            _bounded_diagnostic_message(rendered_rules_path, ": JSON nesting is too deep")
        ) from error

    return Ruleset(
        ruleset_id=cast(str, document["ruleset_id"]),
        schema_version=cast(str, document["schema_version"]),
        rules_version=cast(str, document["rules_version"]),
        _document=validated_document,
        _growth_costs=MappingProxyType(growth_costs),
        _magic_thresholds=MappingProxyType(
            {tier: cast(int, level) for tier, level in _EXPECTED_MAGIC_THRESHOLDS.items()}
        ),
    )


def canonical_json(ruleset: Ruleset) -> str:
    """Serialize a validated ruleset deterministically for hashing and inspection."""
    return json.dumps(
        ruleset.to_dict(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _object_with_unique_keys(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(key)
        result[key] = value
    return result


def _parse_bounded_json_integer(literal: str) -> int:
    digits = literal[1:] if literal.startswith("-") else literal
    if len(digits) > _MAX_JSON_INTEGER_DIGITS:
        raise _JsonIntegerLimitError

    value = 0
    for digit in digits:
        value = value * 10 + (ord(digit) - ord("0"))
    return -value if literal.startswith("-") else value


def _at(document: JsonObject, field_path: tuple[str, ...]) -> JsonValue:
    current: JsonValue = document
    traversed: list[str] = []
    for part in field_path:
        traversed.append(part)
        if not isinstance(current, dict) or part not in current:
            raise RulesetValidationError(
                _bounded_diagnostic_message(
                    "missing required field ",
                    _render_diagnostic_key(_render_diagnostic_field_path(tuple(traversed))),
                )
            )
        current = current[part]
    return current


def _validate_no_unknown_fields(document: JsonObject) -> None:
    expected_paths = [field_path for field_path, _expected in _EXPECTED_FIELDS]
    expected_paths.append(("progression", "target_level_growth_costs"))

    allowed_keys_by_path: dict[tuple[str, ...], set[str]] = {}
    for field_path in expected_paths:
        for index, key in enumerate(field_path):
            parent_path = field_path[:index]
            allowed_keys_by_path.setdefault(parent_path, set()).add(key)

    for parent_path, allowed_keys in allowed_keys_by_path.items():
        value: JsonValue = document if not parent_path else _at(document, parent_path)
        if not isinstance(value, dict):
            continue
        unknown_keys = sorted(value.keys() - allowed_keys)
        if unknown_keys:
            unknown_key = unknown_keys[0]
            rendered_field = (
                _render_diagnostic_field_path((*parent_path, unknown_key))
                if parent_path
                else _render_diagnostic_key(unknown_key)
            )
            raise RulesetValidationError(
                _bounded_diagnostic_message("unknown field ", rendered_field)
            )


def _expect(document: JsonObject, field_path: tuple[str, ...], expected: JsonValue) -> None:
    actual = _at(document, field_path)
    if not _json_values_equal_with_strict_types(actual, expected):
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                _render_diagnostic_field_path(field_path),
                " must be ",
                _render_diagnostic_value(expected),
                "; got ",
                _render_diagnostic_value(actual),
            )
        )


def _bounded_diagnostic_message(*parts: str) -> str:
    """Join safe diagnostic parts and enforce a final fixed-size ceiling."""
    return _truncate_diagnostic_text("".join(parts), _MAX_DIAGNOSTIC_MESSAGE_CHARS)


def _truncate_diagnostic_text(value: str, maximum_chars: int) -> str:
    if len(value) <= maximum_chars:
        return value
    retained_chars = maximum_chars - len(_DIAGNOSTIC_TRUNCATION_SUFFIX)
    return value[:retained_chars] + _DIAGNOSTIC_TRUNCATION_SUFFIX


def _render_small_decimal(value: int) -> str:
    """Render an integer already proven small enough for safe conversion."""
    return format(value, "d")


def _render_diagnostic_string_literal(value: str) -> str:
    preview = value[:_MAX_DIAGNOSTIC_STRING_PREVIEW_CHARS]
    rendered = ascii(preview)
    if len(value) <= len(preview):
        return rendered
    return rendered[:-1] + "…" + rendered[-1]


def _render_diagnostic_key(key: str) -> str:
    rendered = _render_diagnostic_string_literal(key)
    if len(key) <= _MAX_DIAGNOSTIC_STRING_PREVIEW_CHARS:
        return rendered
    return rendered + " (length=" + _render_small_decimal(len(key)) + ")"


def _render_diagnostic_rules_path(path: Path) -> str:
    raw_path = path.__fspath__()
    return (
        "ruleset path(name="
        + _render_diagnostic_key(path.name)
        + ", length="
        + _render_small_decimal(len(raw_path))
        + ")"
    )


def _render_diagnostic_value(value: object) -> str:
    """Render a deterministic typed summary without expanding attacker-sized values."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean(value=" + ("true" if value else "false") + ")"
    if isinstance(value, int):
        if -_MAX_DIAGNOSTIC_INTEGER_MAGNITUDE <= value <= _MAX_DIAGNOSTIC_INTEGER_MAGNITUDE:
            return "integer(value=" + _render_small_decimal(value) + ")"
        sign = "negative" if value < 0 else "positive"
        return (
            "integer(sign="
            + sign
            + ", bit_length="
            + _render_small_decimal(value.bit_length())
            + ")"
        )
    if isinstance(value, str):
        if len(value) <= _MAX_DIAGNOSTIC_STRING_PREVIEW_CHARS:
            return "string(value=" + _render_diagnostic_string_literal(value) + ")"
        return (
            "string(length="
            + _render_small_decimal(len(value))
            + ", prefix="
            + _render_diagnostic_string_literal(value)
            + ")"
        )
    if isinstance(value, list):
        return "array(length=" + _render_small_decimal(len(value)) + ")"
    if isinstance(value, dict):
        return "object(length=" + _render_small_decimal(len(value)) + ")"
    return "value(type=" + _render_diagnostic_key(type(value).__name__) + ")"


def _is_simple_field_key(key: str) -> bool:
    if not key or len(key) > _MAX_DIAGNOSTIC_STRING_PREVIEW_CHARS:
        return False
    first = key[0]
    if not ("a" <= first <= "z" or "A" <= first <= "Z" or first == "_"):
        return False
    return all(
        "a" <= character <= "z"
        or "A" <= character <= "Z"
        or "0" <= character <= "9"
        or character == "_"
        for character in key[1:]
    )


def _render_diagnostic_field_path(field_path: _FieldPath) -> str:
    if not field_path:
        return "<root>"
    rendered = ""
    for component in field_path:
        if isinstance(component, int):
            rendered += "[" + _render_small_decimal(component) + "]"
        elif _is_simple_field_key(component):
            rendered += ("." if rendered else "") + component
        else:
            rendered += "[" + _render_diagnostic_key(component) + "]"
    return _truncate_diagnostic_text(rendered, _MAX_DIAGNOSTIC_PATH_CHARS)


def _json_values_equal_with_strict_types(actual: JsonValue, expected: JsonValue) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or actual.keys() != expected.keys():
            return False
        return all(
            _json_values_equal_with_strict_types(actual[key], expected[key]) for key in actual
        )
    if isinstance(actual, list):
        if not isinstance(expected, list) or len(actual) != len(expected):
            return False
        return all(
            _json_values_equal_with_strict_types(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected, strict=True)
        )
    return actual == expected


def _reject_floating_point(value: JsonValue, field_path: _FieldPath = ()) -> None:
    if isinstance(value, float):
        raise RulesetValidationError(
            _bounded_diagnostic_message(
                _render_diagnostic_field_path(field_path),
                " contains a floating-point number; authoritative numbers must be integers",
            )
        )
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_floating_point(item, (*field_path, index))
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_floating_point(item, (*field_path, key))


def _validate_growth_costs(document: JsonObject) -> dict[int, int]:
    raw_entries = _at(document, ("progression", "target_level_growth_costs"))
    if not isinstance(raw_entries, list):
        raise RulesetValidationError("progression.target_level_growth_costs must be an array")

    costs: dict[int, int] = {}
    for index, raw_entry in enumerate(raw_entries):
        entry_path = f"progression.target_level_growth_costs[{index}]"
        if not isinstance(raw_entry, dict):
            raise RulesetValidationError(f"{entry_path} must be an object")
        if set(raw_entry) != {"target_level", "cost"}:
            raise RulesetValidationError(f"{entry_path} must contain exactly target_level and cost")

        target_level = raw_entry["target_level"]
        cost = raw_entry["cost"]
        if not isinstance(target_level, int) or isinstance(target_level, bool):
            raise RulesetValidationError(f"{entry_path}.target_level must be an integer")
        if not 1 <= target_level <= 100:
            raise RulesetValidationError(f"{entry_path}.target_level must be from 1 through 100")
        if not isinstance(cost, int) or isinstance(cost, bool):
            raise RulesetValidationError(f"{entry_path}.cost must be an integer")
        if target_level in costs:
            raise RulesetValidationError(
                "progression.target_level_growth_costs contains "
                f"duplicate target level {target_level}"
            )
        expected_cost = 100 * target_level**2
        if cost != expected_cost:
            raise RulesetValidationError(
                f"{entry_path}.cost must be {expected_cost} for target level {target_level}"
            )
        costs[target_level] = cost

    required_levels = set(range(1, 101))
    if set(costs) != required_levels:
        missing = sorted(required_levels - costs.keys())
        unexpected = sorted(costs.keys() - required_levels)
        raise RulesetValidationError(
            "progression.target_level_growth_costs must contain each target level "
            f"1 through 100 exactly once; missing={missing}, unexpected={unexpected}"
        )
    return costs


def _validate_damage_phases(document: JsonObject) -> None:
    raw_phases = _at(document, ("combat", "damage_resolution", "phases"))
    if not isinstance(raw_phases, list):
        raise RulesetValidationError("combat.damage_resolution.phases must be an array")

    seen: set[str] = set()
    for raw_phase in raw_phases:
        if not isinstance(raw_phase, str):
            raise RulesetValidationError("combat.damage_resolution.phases must contain strings")
        if raw_phase in seen:
            raise RulesetValidationError(
                _bounded_diagnostic_message(
                    "duplicate damage phase ", _render_diagnostic_value(raw_phase)
                )
            )
        seen.add(raw_phase)
