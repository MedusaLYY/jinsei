from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from overlord_worldsim.__main__ import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULESET_PATH = PROJECT_ROOT / "content" / "core" / "ruleset.json"
MAX_RULESET_BYTES = 4 * 1024 * 1024


def test_rules_command_prints_canonical_json() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "overlord_worldsim",
            "rules",
            "--path",
            str(RULESET_PATH),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    document = json.loads(RULESET_PATH.read_text(encoding="utf-8"))
    expected = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == f"{expected}\n"
    assert completed.stderr == ""


def test_rules_command_reports_invalid_ruleset(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")

    assert main(["rules", "--path", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "missing required field 'compatibility'" in captured.err


def _run_rules_subprocess(path: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    environment["PYTHONINTMAXSTRDIGITS"] = "640"
    return subprocess.run(
        [sys.executable, "-m", "overlord_worldsim", "rules", "--path", str(path)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_rules_command_handles_decoder_integer_limit(tmp_path: Path) -> None:
    path = tmp_path / "too-many-digits.json"
    path.write_text('{"ruleset_id":' + "9" * 5_000 + "}", encoding="utf-8")

    completed = _run_rules_subprocess(path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "JSON integer exceeds the safe digit limit" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_rules_command_handles_oversized_growth_target(tmp_path: Path) -> None:
    serialized = RULESET_PATH.read_text(encoding="utf-8")
    serialized = serialized.replace(
        '"target_level": 1',
        '"target_level": ' + "9" * 3_000,
        1,
    )
    path = tmp_path / "oversized-target-level.json"
    path.write_text(serialized, encoding="utf-8")

    completed = _run_rules_subprocess(path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "target_level must be from 1 through 100" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_rules_command_does_not_echo_oversized_growth_cost(tmp_path: Path) -> None:
    oversized_cost = "8" * 3_000
    serialized = RULESET_PATH.read_text(encoding="utf-8").replace(
        '"cost": 100',
        f'"cost": {oversized_cost}',
        1,
    )
    path = tmp_path / "oversized-growth-cost.json"
    path.write_text(serialized, encoding="utf-8")

    completed = _run_rules_subprocess(path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "cost must be 100 for target level 1" in completed.stderr
    assert oversized_cost not in completed.stderr
    assert len(completed.stderr) < 500
    assert "Traceback" not in completed.stderr


def test_rules_command_handles_large_frozen_integer_diagnostic(tmp_path: Path) -> None:
    oversized_integer = "9" * 1_000
    serialized = RULESET_PATH.read_text(encoding="utf-8").replace(
        '"hours_per_day": 24',
        f'"hours_per_day": {oversized_integer}',
        1,
    )
    path = tmp_path / "oversized-frozen-integer.json"
    path.write_text(serialized, encoding="utf-8")

    completed = _run_rules_subprocess(path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "calendar.hours_per_day" in completed.stderr
    assert "integer" in completed.stderr
    assert oversized_integer not in completed.stderr
    assert len(completed.stderr) < 500
    assert "Traceback" not in completed.stderr


def test_rules_command_rejects_ruleset_larger_than_loader_limit(tmp_path: Path) -> None:
    path = tmp_path / "oversized-ruleset.json"
    path.write_bytes(b" " * (MAX_RULESET_BYTES + 1))

    completed = _run_rules_subprocess(path)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "exceeds maximum size of 4194304 bytes" in completed.stderr
    assert len(completed.stderr) < 500
    assert "Traceback" not in completed.stderr
