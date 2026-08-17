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
