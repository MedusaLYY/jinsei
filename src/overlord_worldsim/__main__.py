"""Command-line entry point for Overlord WorldSim."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from overlord_worldsim.rules import RulesetValidationError, canonical_json, load_ruleset


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="overlord-worldsim")
    subcommands = parser.add_subparsers(dest="command", required=True)
    rules_parser = subcommands.add_parser(
        "rules",
        help="validate a ruleset and print canonical JSON",
    )
    rules_parser.add_argument("--path", type=Path, required=True, help="path to ruleset JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit status."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    command = cast(str, arguments.command)

    if command == "rules":
        path = cast(Path, arguments.path)
        try:
            ruleset = load_ruleset(path)
        except RulesetValidationError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        print(canonical_json(ruleset))
        return 0

    parser.error(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
