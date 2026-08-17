from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULESET_PATH = PROJECT_ROOT / "content" / "core" / "ruleset.json"


def _rules_api() -> tuple[type[Exception], Callable[[Path], Any]]:
    from overlord_worldsim.rules import RulesetValidationError, load_ruleset

    return RulesetValidationError, load_ruleset


def _write_mutated_ruleset(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
) -> Path:
    document: dict[str, Any] = json.loads(RULESET_PATH.read_text(encoding="utf-8"))
    mutate(document)
    path = tmp_path / "ruleset.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _replace_growth_entries(document: dict[str, Any], value: Any) -> None:
    document["progression"]["target_level_growth_costs"] = value


def _replace_damage_phases(document: dict[str, Any], value: Any) -> None:
    document["combat"]["damage_resolution"]["phases"] = value


def test_loads_the_frozen_core_ruleset() -> None:
    _, load_ruleset = _rules_api()

    ruleset = load_ruleset(RULESET_PATH)

    assert ruleset.ruleset_id == "urn:overlord-worldsim:ruleset:core"
    assert ruleset.schema_version == "1.0.0"
    assert ruleset.rules_version == "1.0.0"


@pytest.mark.parametrize(
    ("target_level", "expected_cost"),
    [(1, 100), (100, 1_000_000)],
)
def test_growth_cost_table_has_frozen_boundary_values(
    target_level: int,
    expected_cost: int,
) -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    assert ruleset.growth_cost_for(target_level) == expected_cost


def test_magic_thresholds_cover_tiers_zero_through_super() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    assert {
        tier: ruleset.minimum_level_for_magic_tier(tier)
        for tier in [*(str(tier) for tier in range(11)), "super"]
    } == {
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


def test_d100_formulas_and_audit_fields_are_explicit() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)
    document: Any = ruleset.to_dict()
    checks = document["checks"]

    assert checks["roll_total_formula"] == "d100 + action_rating + situational_modifier"
    assert checks["opposed_target_formula"] == "50 + defense_rating"
    assert checks["non_opposed_target"] == "explicit_fixed_dc"
    assert checks["success_condition"] == "roll_total >= target"
    assert checks["natural_1_automatic_failure"] is False
    assert checks["natural_100_automatic_success"] is False
    assert checks["natural_rolls_override_feasibility"] is False
    assert checks["audit_fields"] == [
        "roll",
        "action_rating",
        "situational_modifiers",
        "defense_or_fixed_dc",
        "margin",
    ]


def test_cross_system_constitutional_policies_are_machine_frozen() -> None:
    _, load_ruleset = _rules_api()
    document: Any = load_ruleset(RULESET_PATH).to_dict()

    assert document["magic"]["traditions_combine_implicitly"] is False
    assert document["magic"]["tier_minimums_do_not_bypass_content_prerequisites"] is True
    assert document["checks"]["visibility"] == {
        "player_roll_visible": True,
        "known_modifiers_visible": True,
        "secret_defense_or_dc_hidden": True,
        "hidden_rolls_hidden": True,
    }
    assert document["combat"]["damage_resolution"]["final_damage_may_be_zero"] is True
    assert document["combat"]["action_economy"]["reaction_refresh"] == "start_of_round"
    assert document["progression"]["growth_event_stream"] == "unified_audited"
    assert document["progression"]["eligible_activity_domains"] == [
        "combat",
        "research",
        "politics",
        "trade",
        "governance",
        "training",
    ]
    assert document["progression"]["pending_allocation_requires_player_choice"] is True
    assert document["progression"]["prerequisites"] == {
        "operators": ["all", "any", "not"],
        "checked_at": "acquisition_time",
        "ordered_history_required": True,
        "later_condition_loss_revokes_level": False,
    }
    assert document["effects"] == {
        "execution_model": "registered_declarative_opcodes",
        "arbitrary_python_allowed": False,
        "unknown_opcode_policy": "reject_content_load",
    }
    assert document["world"]["aggregate_population_required"] is True
    assert document["world"]["public_and_gm_hidden_projections_separate"] is True
    assert document["content"]["item_categories_required"] == [
        "equipment",
        "consumable",
        "material",
        "key_item",
    ]
    assert document["content"]["unusable_filler_counts_toward_item_minimum"] is False
    assert document["character_creation"] == {
        "legal_ordered_acquisition_history_required": True,
        "restricted_node_authorization": "origin_authorization_or_achievement_token",
        "mode_budgets": ["talent", "wealth", "equipment"],
        "custom_budget_override_marks_save_custom": True,
        "custom_may_break_total_level_cap": False,
        "custom_may_break_reference_integrity": False,
        "level_100_equipment_requires_player_choice": True,
        "stop_before_prologue": True,
    }


def test_ruleset_lookup_errors_are_clear() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    with pytest.raises(ValueError, match="target level must be from 1 through 100"):
        ruleset.growth_cost_for(0)
    with pytest.raises(ValueError, match="target level must be an integer from 1 through 100"):
        ruleset.growth_cost_for(True)
    with pytest.raises(ValueError, match="unknown magic tier: 11"):
        ruleset.minimum_level_for_magic_tier(11)


def test_ruleset_document_copy_is_detached() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    detached = ruleset.to_dict()
    detached["rules_version"] = "changed"

    assert ruleset.to_dict()["rules_version"] == "1.0.0"


def test_rejects_an_inconsistent_level_cap(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document["progression"]["level_caps"].update({"base": 16}),
    )

    with pytest.raises(error_type, match=r"progression\.level_caps\.base"):
        load_ruleset(path)


def test_rejects_duplicate_damage_phases(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document["combat"]["damage_resolution"]["phases"].append("hp"),
    )

    with pytest.raises(error_type, match="duplicate damage phase"):
        load_ruleset(path)


def test_rejects_repeated_growth_target_levels(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()

    def repeat_first_entry(document: dict[str, Any]) -> None:
        growth_costs = document["progression"]["target_level_growth_costs"]
        growth_costs.append(growth_costs[0].copy())

    path = _write_mutated_ruleset(tmp_path, repeat_first_entry)

    with pytest.raises(error_type, match="duplicate target level 1"):
        load_ruleset(path)


def test_malformed_json_fails_with_path_and_parse_context(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "broken.json"
    path.write_text('{"ruleset_id":', encoding="utf-8")

    with pytest.raises(error_type, match=r"broken\.json.*malformed JSON"):
        load_ruleset(path)


def test_missing_ruleset_fails_with_read_context(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "missing.json"

    with pytest.raises(error_type, match=r"missing\.json.*cannot read ruleset"):
        load_ruleset(path)


def test_non_utf8_ruleset_fails_with_decode_context(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "non-utf8.json"
    path.write_bytes(b"{\xff}")

    with pytest.raises(error_type, match=r"non-utf8\.json.*not valid UTF-8"):
        load_ruleset(path)


def test_duplicate_json_object_key_is_rejected(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "duplicate-key.json"
    path.write_text('{"ruleset_id":"first","ruleset_id":"second"}', encoding="utf-8")

    with pytest.raises(error_type, match="duplicate object key 'ruleset_id'"):
        load_ruleset(path)


def test_non_object_ruleset_root_is_rejected(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "array.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(error_type, match="ruleset root must be a JSON object"):
        load_ruleset(path)


def test_excessive_json_nesting_fails_clearly(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "too-deep.json"
    serialized = RULESET_PATH.read_text(encoding="utf-8")
    start = serialized.index('  "start_modes": ')
    end = serialized.index(',\n  "character_creation"', start)
    deeply_nested_modes = '  "start_modes": ' + "[" * 2_000 + "0" + "]" * 2_000
    path.write_text(serialized[:start] + deeply_nested_modes + serialized[end:], encoding="utf-8")

    with pytest.raises(error_type, match="JSON nesting is too deep"):
        load_ruleset(path)


def test_unknown_ruleset_field_is_rejected(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({"unregistered_extension": True}),
    )

    with pytest.raises(error_type, match="unknown field 'unregistered_extension'"):
        load_ruleset(path)


def test_rejects_modified_action_expiration_policy(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document["combat"]["action_economy"].update(
            {"unused_actions": "carry_over"}
        ),
    )

    with pytest.raises(error_type, match=r"combat\.action_economy\.unused_actions"):
        load_ruleset(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["magic"]["minimum_caster_level_by_tier"].update({"1": True}),
            "magic.minimum_caster_level_by_tier",
        ),
        (
            lambda document: document["start_modes"][0].update({"level": True}),
            "start_modes",
        ),
    ],
)
def test_nested_boolean_cannot_substitute_for_integer(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(tmp_path, mutate)

    with pytest.raises(error_type, match=message):
        load_ruleset(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["calendar"].update({"hours_per_day": 24.0}),
            "authoritative numbers must be integers",
        ),
        (
            lambda document: document.pop("compatibility"),
            "missing required field 'compatibility'",
        ),
        (
            lambda document: _replace_growth_entries(document, {}),
            "target_level_growth_costs must be an array",
        ),
        (
            lambda document: _replace_growth_entries(document, [1]),
            r"target_level_growth_costs\[0\] must be an object",
        ),
        (
            lambda document: _replace_growth_entries(
                document, [{"target_level": 1, "cost": 100, "note": "extra"}]
            ),
            "must contain exactly target_level and cost",
        ),
        (
            lambda document: document["progression"]["target_level_growth_costs"][0].update(
                {"target_level": True}
            ),
            "target_level must be an integer",
        ),
        (
            lambda document: document["progression"]["target_level_growth_costs"][0].update(
                {"cost": False}
            ),
            "cost must be an integer",
        ),
        (
            lambda document: document["progression"]["target_level_growth_costs"][0].update(
                {"cost": 101}
            ),
            "cost must be 100 for target level 1",
        ),
        (
            lambda document: document["progression"]["target_level_growth_costs"].pop(),
            "must contain each target level 1 through 100 exactly once",
        ),
        (
            lambda document: _replace_damage_phases(document, {}),
            "damage_resolution.phases must be an array",
        ),
        (
            lambda document: _replace_damage_phases(document, [1]),
            "damage_resolution.phases must contain strings",
        ),
    ],
    ids=[
        "floating-point",
        "missing-field",
        "growth-not-array",
        "growth-entry-not-object",
        "growth-entry-extra-key",
        "growth-target-not-int",
        "growth-cost-not-int",
        "growth-cost-formula",
        "growth-missing-level",
        "damage-not-array",
        "damage-entry-not-string",
    ],
)
def test_rejects_other_malformed_or_inconsistent_rules(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(tmp_path, mutate)

    with pytest.raises(error_type, match=message):
        load_ruleset(path)
