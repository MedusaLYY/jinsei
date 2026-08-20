from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULESET_PATH = PROJECT_ROOT / "content" / "core" / "ruleset.json"
MAX_RULESET_BYTES = 4 * 1024 * 1024


def _rules_api() -> tuple[type[Exception], Callable[[str | Path], Any]]:
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


def test_ruleset_empty_direct_construction_is_rejected() -> None:
    from overlord_worldsim.rules import Ruleset

    with pytest.raises(TypeError, match="load_ruleset"):
        Ruleset()


def test_ruleset_forged_direct_construction_is_rejected() -> None:
    from overlord_worldsim.rules import Ruleset

    with pytest.raises(TypeError, match="load_ruleset"):
        Ruleset(
            ruleset_id="forged",
            schema_version="forged",
            rules_version="forged",
            _document={},
            _growth_costs={},
            _magic_thresholds={},
        )


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
    assert ruleset.minimum_level_for_magic_tier(1) == 1


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


def test_naming_threshold_is_a_one_way_obligation() -> None:
    _, load_ruleset = _rules_api()
    document: Any = load_ruleset(RULESET_PATH).to_dict()
    scarcity = document["scarcity"]

    assert scarcity["all_npcs_at_or_above_level_must_be_named"] == 45
    assert "named_npc_minimum_level" not in scarcity


def test_ruleset_lookup_errors_are_clear() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    with pytest.raises(ValueError, match="target level must be from 1 through 100"):
        ruleset.growth_cost_for(0)
    with pytest.raises(ValueError, match="target level must be an integer from 1 through 100"):
        ruleset.growth_cost_for(True)
    with pytest.raises(ValueError, match="unknown magic tier: 11"):
        ruleset.minimum_level_for_magic_tier(11)


@pytest.mark.parametrize(
    ("invalid_value", "rendered_type"),
    [
        pytest.param("x" * 10_000, "string", id="string"),
        pytest.param([None] * 10_000, "array", id="array"),
        pytest.param(dict.fromkeys(range(10_000)), "object", id="object"),
    ],
)
@pytest.mark.parametrize(
    ("lookup", "expected_context"),
    [
        pytest.param(
            lambda ruleset, value: ruleset.growth_cost_for(value),
            "target level must be an integer",
            id="growth-cost",
        ),
        pytest.param(
            lambda ruleset, value: ruleset.minimum_level_for_magic_tier(value),
            "unknown magic tier",
            id="magic-tier",
        ),
    ],
)
def test_public_lookup_diagnostics_bound_strings_and_containers(
    invalid_value: Any,
    rendered_type: str,
    lookup: Callable[[Any, Any], int],
    expected_context: str,
) -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    with pytest.raises(ValueError) as captured:
        lookup(ruleset, invalid_value)

    message = str(captured.value)
    assert len(message) < 500
    assert expected_context in message
    assert rendered_type in message
    assert "length=10000" in message


@pytest.mark.parametrize(
    ("lookup", "expected_context"),
    [
        pytest.param(
            lambda ruleset, value: ruleset.growth_cost_for(value),
            "target level must be from 1 through 100",
            id="growth-cost",
        ),
        pytest.param(
            lambda ruleset, value: ruleset.minimum_level_for_magic_tier(value),
            "unknown magic tier",
            id="magic-tier",
        ),
    ],
)
def test_public_lookup_large_integer_is_safe_under_python_digit_guard(
    lookup: Callable[[Any, Any], int],
    expected_context: str,
) -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)
    integer_literal = "9" * 1_000
    oversized_integer = int(integer_literal)

    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        with pytest.raises(ValueError) as captured:
            lookup(ruleset, oversized_integer)
    finally:
        sys.set_int_max_str_digits(previous_limit)

    message = str(captured.value)
    assert len(message) < 500
    assert integer_literal not in message
    assert expected_context in message
    assert "integer" in message


@pytest.mark.parametrize(
    ("invalid_value", "rendered_value"),
    [
        pytest.param(None, "null", id="null"),
        pytest.param((), "value(type='tuple')", id="generic-type"),
    ],
)
def test_public_lookup_diagnostics_cover_other_runtime_types(
    invalid_value: Any,
    rendered_value: str,
) -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)

    with pytest.raises(ValueError) as captured:
        ruleset.growth_cost_for(invalid_value)

    message = str(captured.value)
    assert len(message) < 500
    assert rendered_value in message


def test_public_lookup_diagnostic_has_a_total_message_ceiling() -> None:
    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)
    escaped_payload = "\N{GRINNING FACE}" * 64

    with pytest.raises(ValueError) as captured:
        ruleset.minimum_level_for_magic_tier(escaped_payload)

    message = str(captured.value)
    assert len(message) == 480
    assert escaped_payload not in message
    assert message.endswith("...<truncated>")


def test_ruleset_document_copy_is_detached() -> None:
    from overlord_worldsim.rules import canonical_json

    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)
    canonical_before = canonical_json(ruleset)

    detached = ruleset.to_dict()
    detached["rules_version"] = "changed"
    detached["progression"]["target_level_growth_costs"][0]["cost"] = 999
    detached["magic"]["minimum_caster_level_by_tier"]["1"] = 999

    assert canonical_json(ruleset) == canonical_before
    assert ruleset.to_dict()["rules_version"] == "1.0.0"
    assert ruleset.rules_version == "1.0.0"
    assert ruleset.growth_cost_for(1) == 100
    assert ruleset.minimum_level_for_magic_tier(1) == 1


def test_ruleset_authority_cannot_be_desynchronized_after_load() -> None:
    from overlord_worldsim.rules import canonical_json

    _, load_ruleset = _rules_api()
    ruleset = load_ruleset(RULESET_PATH)
    internal_document: Any = getattr(ruleset, "_document", None)
    if isinstance(internal_document, dict):
        internal_document["rules_version"] = "forged"
        internal_document["progression"]["target_level_growth_costs"][0]["cost"] = 999
        internal_document["magic"]["minimum_caster_level_by_tier"]["1"] = 999

    canonical_document: Any = json.loads(canonical_json(ruleset))
    assert not hasattr(ruleset, "_document")
    assert canonical_document == ruleset.to_dict()
    assert canonical_document["rules_version"] == ruleset.rules_version == "1.0.0"
    assert canonical_document["progression"]["target_level_growth_costs"][0]["cost"] == 100
    assert ruleset.growth_cost_for(1) == 100
    assert canonical_document["magic"]["minimum_caster_level_by_tier"]["1"] == 1
    assert ruleset.minimum_level_for_magic_tier(1) == 1


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


def test_large_duplicate_damage_phase_has_bounded_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_phase = "phase-" + "x" * 10_000

    def duplicate_large_phase(document: dict[str, Any]) -> None:
        document["combat"]["damage_resolution"]["phases"] = [
            oversized_phase,
            oversized_phase,
        ]

    path = _write_mutated_ruleset(tmp_path, duplicate_large_phase)

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert len(message) < 500
    assert oversized_phase not in message
    assert "duplicate damage phase" in message
    assert "string" in message
    assert "length=10006" in message


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


@pytest.mark.parametrize(
    "invalid_path",
    [
        pytest.param("bad\0name.json", id="nul"),
        pytest.param("\N{GRINNING FACE}" * 64 + "\0.json", id="escaped-unicode-nul"),
    ],
)
def test_invalid_ruleset_path_value_has_bounded_read_error(invalid_path: str) -> None:
    error_type, load_ruleset = _rules_api()

    with pytest.raises(error_type) as captured:
        load_ruleset(invalid_path)

    message = str(captured.value)
    assert len(message) <= 480
    assert invalid_path not in message
    assert "cannot read ruleset" in message


def test_unreadable_large_ruleset_path_has_bounded_diagnostic() -> None:
    error_type, load_ruleset = _rules_api()
    oversized_path = "x" * 10_000 + ".json"

    with pytest.raises(error_type) as captured:
        load_ruleset(oversized_path)

    message = str(captured.value)
    assert len(message) < 500
    assert oversized_path not in message
    assert "cannot read ruleset" in message
    assert "length=10005" in message


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


def test_large_duplicate_json_key_has_bounded_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_key = "k" * 10_000
    path = tmp_path / "large-duplicate-key.json"
    path.write_text(
        '{"' + oversized_key + '":1,"' + oversized_key + '":2}',
        encoding="utf-8",
    )

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert len(message) < 500
    assert oversized_key not in message
    assert "duplicate object key" in message
    assert "length=10000" in message


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


def test_decoder_integer_above_safe_digit_limit_fails_clearly(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "too-many-digits.json"
    path.write_text('{"ruleset_id":' + "9" * 5_000 + "}", encoding="utf-8")

    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        with pytest.raises(error_type, match="JSON integer exceeds the safe digit limit"):
            load_ruleset(path)
    finally:
        sys.set_int_max_str_digits(previous_limit)


def test_growth_target_level_is_bounded_before_arithmetic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    serialized = RULESET_PATH.read_text(encoding="utf-8")
    oversized_level = "9" * 3_000
    serialized = serialized.replace(
        '"target_level": 1',
        f'"target_level": {oversized_level}',
        1,
    )
    path = tmp_path / "oversized-target-level.json"
    path.write_text(serialized, encoding="utf-8")

    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        with pytest.raises(error_type, match="target_level must be from 1 through 100") as captured:
            load_ruleset(path)
    finally:
        sys.set_int_max_str_digits(previous_limit)

    assert oversized_level not in str(captured.value)
    assert len(str(captured.value)) < 300


def test_oversized_growth_cost_is_not_echoed_in_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    serialized = RULESET_PATH.read_text(encoding="utf-8")
    oversized_cost = "8" * 3_000
    serialized = serialized.replace('"cost": 100', f'"cost": {oversized_cost}', 1)
    path = tmp_path / "oversized-growth-cost.json"
    path.write_text(serialized, encoding="utf-8")

    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        with pytest.raises(error_type, match="cost must be 100 for target level 1") as captured:
            load_ruleset(path)
    finally:
        sys.set_int_max_str_digits(previous_limit)

    assert oversized_cost not in str(captured.value)
    assert len(str(captured.value)) < 300


def test_large_frozen_integer_mismatch_has_bounded_typed_diagnostic(
    tmp_path: Path,
) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_integer = "9" * 1_000
    serialized = RULESET_PATH.read_text(encoding="utf-8").replace(
        '"hours_per_day": 24',
        f'"hours_per_day": {oversized_integer}',
        1,
    )
    path = tmp_path / "oversized-frozen-integer.json"
    path.write_text(serialized, encoding="utf-8")

    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        with pytest.raises(error_type) as captured:
            load_ruleset(path)
    finally:
        sys.set_int_max_str_digits(previous_limit)

    message = str(captured.value)
    assert "calendar.hours_per_day" in message
    assert "integer" in message
    assert oversized_integer not in message
    assert len(message) < 300


def test_large_string_mismatch_has_bounded_deterministic_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_string = "x" * 10_000
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({"ruleset_id": oversized_string}),
    )

    with pytest.raises(error_type) as first_captured:
        load_ruleset(path)
    with pytest.raises(error_type) as second_captured:
        load_ruleset(path)

    first_message = str(first_captured.value)
    assert first_message == str(second_captured.value)
    assert "ruleset_id" in first_message
    assert "string" in first_message
    assert "length=10000" in first_message
    assert oversized_string not in first_message
    assert len(first_message) < 300


def test_large_container_mismatch_has_bounded_deterministic_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_container: list[None] = [None] * 10_000
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({"start_modes": oversized_container}),
    )

    with pytest.raises(error_type) as first_captured:
        load_ruleset(path)
    with pytest.raises(error_type) as second_captured:
        load_ruleset(path)

    first_message = str(first_captured.value)
    assert first_message == str(second_captured.value)
    assert "start_modes" in first_message
    assert "array" in first_message
    assert "length=10000" in first_message
    assert len(first_message) < 300


def test_composite_mismatch_reports_first_recursive_leaf(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document["start_modes"][0].update({"level": True}),
    )

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert "start_modes[0].level" in message
    assert "integer(value=1)" in message
    assert "boolean(value=true)" in message
    assert len(message) <= 480


def test_empty_growth_levels_use_bounded_count_summary(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: _replace_growth_entries(document, []),
    )

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert len(message) <= 480
    assert "target level 1 through 100" in message
    assert "missing_count=100" in message
    assert "unexpected_count=0" in message


def test_ruleset_larger_than_loader_limit_is_rejected(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = tmp_path / "oversized-ruleset.json"
    path.write_bytes(b" " * (MAX_RULESET_BYTES + 1))

    with pytest.raises(error_type, match=r"exceeds maximum size of 4194304 bytes"):
        load_ruleset(path)


def test_ruleset_loader_caps_its_file_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error_type, load_ruleset = _rules_api()
    requested_sizes: list[int] = []

    class BoundedReadProbe:
        def __enter__(self) -> BoundedReadProbe:
            return self

        def __exit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            del exception_type, exception, traceback

        def read(self, size: int = -1) -> bytes:
            requested_sizes.append(size)
            if size != MAX_RULESET_BYTES + 1:
                raise AssertionError(f"uncapped or unexpected ruleset read size: {size}")
            return b" " * size

    probe = BoundedReadProbe()

    def open_probe(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> BoundedReadProbe:
        del path, buffering, encoding, errors, newline
        assert mode == "rb"
        return probe

    monkeypatch.setattr(Path, "open", open_probe)

    with pytest.raises(error_type, match=r"exceeds maximum size of 4194304 bytes"):
        load_ruleset(tmp_path / "read-probe.json")

    assert requested_sizes == [MAX_RULESET_BYTES + 1]


def test_unknown_ruleset_field_is_rejected(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({"unregistered_extension": True}),
    )

    with pytest.raises(error_type, match="unknown field 'unregistered_extension'"):
        load_ruleset(path)


def test_large_unknown_field_has_bounded_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_key = "z" * 10_000
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({oversized_key: True}),
    )

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert len(message) < 500
    assert oversized_key not in message
    assert "unknown field" in message
    assert "length=10000" in message


def test_large_floating_point_field_path_has_bounded_diagnostic(tmp_path: Path) -> None:
    error_type, load_ruleset = _rules_api()
    oversized_key = "z" * 10_000
    path = _write_mutated_ruleset(
        tmp_path,
        lambda document: document.update({"effects": {oversized_key: [1.5]}}),
    )

    with pytest.raises(error_type) as captured:
        load_ruleset(path)

    message = str(captured.value)
    assert len(message) < 500
    assert oversized_key not in message
    assert "effects" in message
    assert "length=10000" in message
    assert "authoritative numbers must be integers" in message


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
