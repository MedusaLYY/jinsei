"""Command-line entry point for Overlord WorldSim."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC
from pathlib import Path
from typing import cast

from overlord_worldsim.canon.extract_model import ExtractionBatch
from overlord_worldsim.canon.fts import search_canon_text
from overlord_worldsim.canon.io import write_parsed
from overlord_worldsim.canon.loader import build_canon_db
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.rules import RulesetValidationError, canonical_json, load_ruleset


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="overlord-worldsim")
    subcommands = parser.add_subparsers(dest="command", required=True)
    rules_parser = subcommands.add_parser(
        "rules",
        help="validate a ruleset and print canonical JSON",
    )
    rules_parser.add_argument("--path", type=Path, required=True, help="path to ruleset JSON")
    canon_parser = subcommands.add_parser(
        "canon", help="build and query the Mushoku Tensei canon database"
    )
    canon_subcommands = canon_parser.add_subparsers(dest="canon_command", required=True)
    parse_parser = canon_subcommands.add_parser(
        "parse", help="parse the raw TXT into units, scenes, and chunks"
    )
    parse_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    parse_parser.add_argument(
        "--out", type=Path, required=True, help="output directory for parsed artifacts"
    )
    build_parser = canon_subcommands.add_parser("build", help="parse and load the canon database")
    build_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    build_parser.add_argument(
        "--db", type=Path, required=True, help="path to the canon SQLite database"
    )
    search_parser = canon_subcommands.add_parser(
        "search", help="full-text search over the canon database"
    )
    search_parser.add_argument(
        "--db", type=Path, required=True, help="path to the canon SQLite database"
    )
    search_parser.add_argument("--query", type=str, required=True, help="search query text")
    search_parser.add_argument(
        "--volume", type=int, default=None, help="restrict to a volume number"
    )
    search_parser.add_argument("--limit", type=int, default=20, help="maximum number of hits")
    emb_parser = canon_subcommands.add_parser(
        "build-embeddings", help="embed all chunks into an offline index database"
    )
    emb_parser.add_argument(
        "--db", type=Path, required=True, help="path to the canon SQLite database"
    )
    emb_parser.add_argument("--index", type=Path, required=True, help="output embedding index path")
    emb_parser.add_argument(
        "--provider", type=str, default="hash", help="registered embedding provider name"
    )
    verify_parser = canon_subcommands.add_parser(
        "verify", help="verify one extraction candidate batch against the source"
    )
    verify_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    verify_parser.add_argument(
        "--candidate", type=Path, required=True, help="path to the extraction batch JSON"
    )
    verify_parser.add_argument(
        "--out", type=Path, required=True, help="path for the verification report JSON"
    )
    apply_parser = canon_subcommands.add_parser(
        "apply", help="verify and apply one extraction batch into the canon database"
    )
    apply_parser.add_argument(
        "--db", type=Path, required=True, help="path to the canon SQLite database"
    )
    apply_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    apply_parser.add_argument(
        "--candidate", type=Path, required=True, help="path to the extraction batch JSON"
    )
    enrich_verify_parser = canon_subcommands.add_parser(
        "enrich-verify", help="verify the enrichment corpus against source and registry"
    )
    enrich_verify_parser.add_argument(
        "--content", type=Path, required=True, help="enrichment content directory"
    )
    enrich_verify_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    enrich_verify_parser.add_argument(
        "--canon", type=Path, required=True, help="path to the extraction canon batches dir"
    )
    enrich_verify_parser.add_argument(
        "--out", type=Path, required=True, help="path for the verification report JSON"
    )
    enrich_apply_parser = canon_subcommands.add_parser(
        "enrich-apply", help="verify and apply the enrichment corpus into the canon database"
    )
    enrich_apply_parser.add_argument(
        "--db", type=Path, required=True, help="path to the canon SQLite database"
    )
    enrich_apply_parser.add_argument(
        "--content", type=Path, required=True, help="enrichment content directory"
    )
    enrich_apply_parser.add_argument(
        "--source", type=Path, required=True, help="path to the raw canon TXT"
    )
    enrich_apply_parser.add_argument(
        "--canon", type=Path, required=True, help="path to the extraction canon batches dir"
    )
    return parser


def _read_source(source: Path) -> str:
    try:
        return source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read source: {error}") from error


def _run_canon_parse(arguments: argparse.Namespace) -> int:
    source = cast(Path, arguments.source)
    out_dir = cast(Path, arguments.out)
    try:
        text = _read_source(source)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    doc = parse_source(text, source_name=source.name)
    write_parsed(doc, out_dir)
    print(_canonical_json(doc.to_summary()))
    return 0


def _run_canon_build(arguments: argparse.Namespace) -> int:
    source = cast(Path, arguments.source)
    db_path = cast(Path, arguments.db)
    try:
        text = _read_source(source)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    doc = parse_source(text, source_name=source.name)
    build_canon_db(doc, db_path, sha256=sha256)
    print(_canonical_json(doc.to_summary()))
    return 0


def _run_canon_search(arguments: argparse.Namespace) -> int:
    db_path = cast(Path, arguments.db)
    query = cast(str, arguments.query)
    volume_no = cast(int | None, arguments.volume)
    limit = cast(int, arguments.limit)
    try:
        hits = search_canon_text(db_path, query, volume_no=volume_no, limit=limit)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(_canonical_json([hit.__dict__ for hit in hits]))
    return 0


def _run_canon_build_embeddings(arguments: argparse.Namespace) -> int:
    import sqlite3

    from overlord_worldsim.canon import embeddings as embeddings_module
    from overlord_worldsim.canon.embeddings import (
        HashEmbeddingProvider,
        build_embedding_index,
        register_provider,
    )

    db_path = cast(Path, arguments.db)
    index_path = cast(Path, arguments.index)
    provider_name = cast(str, arguments.provider)
    provider = embeddings_module._PROVIDERS.get(provider_name)
    if provider is None:
        if provider_name == "hash":
            provider = register_provider("hash", HashEmbeddingProvider())
        else:
            available = ["hash", *sorted(embeddings_module._PROVIDERS)]
            message = (
                f"error: unknown embedding provider: {provider_name} "
                f"(available: {', '.join(available)})"
            )
            print(message, file=sys.stderr)
            return 2
    try:
        build_embedding_index(db_path, index_path, provider)
    except (OSError, sqlite3.DatabaseError) as error:
        print(f"error: cannot build embedding index: {error}", file=sys.stderr)
        return 2
    connection = sqlite3.connect(index_path)
    try:
        embedded = int(connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0])
    finally:
        connection.close()
    print(_canonical_json({"embedded": embedded, "provider": provider.name}))
    return 0


def _load_candidate(candidate: Path) -> ExtractionBatch:
    import json

    from overlord_worldsim.canon.extract_model import ExtractionBatch

    try:
        document = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read candidate: {error}") from error
    try:
        return ExtractionBatch.from_json(document)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"invalid candidate batch: {error}") from error


def _run_canon_verify(arguments: argparse.Namespace) -> int:

    from overlord_worldsim.canon.verifier import verify_batch

    source = cast(Path, arguments.source)
    candidate_path = cast(Path, arguments.candidate)
    out_path = cast(Path, arguments.out)
    try:
        text = _read_source(source)
        batch = _load_candidate(candidate_path)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    doc = parse_source(text, source_name=source.name)
    report = verify_batch(batch, doc)
    payload = {
        "batch_id": report.batch_id,
        "is_clean": report.is_clean,
        "errors": [error.to_json() for error in report.errors],
    }
    try:
        out_path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"error: cannot write report: {error}", file=sys.stderr)
        return 2
    print(_canonical_json(payload))
    if not report.is_clean:
        print("error: cannot apply: verification failed", file=sys.stderr)
        return 1
    return 0


def _run_canon_apply(arguments: argparse.Namespace) -> int:
    from overlord_worldsim.canon.loader import apply_extraction_batch, open_canon_db
    from overlord_worldsim.canon.verifier import verify_batch

    db_path = cast(Path, arguments.db)
    source = cast(Path, arguments.source)
    candidate_path = cast(Path, arguments.candidate)
    try:
        text = _read_source(source)
        batch = _load_candidate(candidate_path)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    doc = parse_source(text, source_name=source.name)
    report = verify_batch(batch, doc)
    if not report.is_clean:
        for issue in report.errors:
            print(f"error: verification failed: {issue.to_json()}", file=sys.stderr)
        return 1
    try:
        connection = open_canon_db(db_path)
        try:
            with connection:
                apply_extraction_batch(connection, batch)
        finally:
            connection.close()
    except (OSError, sqlite3.DatabaseError) as error:
        print(f"error: cannot apply batch: {error}", file=sys.stderr)
        return 2
    print(
        _canonical_json(
            {
                "batch_id": batch.batch_id,
                "entities": len(batch.entities),
                "facts": len(batch.facts),
                "relationships": len(batch.relationships),
                "knowledge": len(batch.knowledge),
                "events": len(batch.events),
                "phases": len(batch.phases),
            }
        )
    )
    return 0


def _run_canon_enrich_verify(arguments: argparse.Namespace) -> int:
    from overlord_worldsim.canon.enrich_registry import (
        load_enrichment_batches,
        load_entity_registry,
    )
    from overlord_worldsim.canon.enrich_verifier import verify_enrichment

    content_dir = cast(Path, arguments.content)
    source = cast(Path, arguments.source)
    canon_dir = cast(Path, arguments.canon)
    out_path = cast(Path, arguments.out)
    try:
        text = _read_source(source)
        batches = load_enrichment_batches(content_dir)
        registry = load_entity_registry(canon_dir)
    except (ValueError, FileNotFoundError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    doc = parse_source(text, source_name=source.name)
    report = verify_enrichment(batches, doc, registry)
    payload = {
        "is_clean": report.is_clean,
        "batch_count": len(batches),
        "errors": [error.to_json() for error in report.errors],
    }
    try:
        out_path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"error: cannot write report: {error}", file=sys.stderr)
        return 2
    print(_canonical_json(payload))
    if not report.is_clean:
        print("error: enrichment verification failed", file=sys.stderr)
        return 1
    return 0


def _run_canon_enrich_apply(arguments: argparse.Namespace) -> int:
    from datetime import datetime

    from overlord_worldsim.canon.enrich_loader import (
        apply_enrichment,
        build_manifest,
        canonical_content_hash,
        write_manifest_json,
    )
    from overlord_worldsim.canon.loader import open_canon_db
    from overlord_worldsim.canon.enrich_query import enrichment_summary
    from overlord_worldsim.canon.enrich_registry import (
        load_enrichment_batches,
        load_entity_registry,
    )
    from overlord_worldsim.canon.enrich_verifier import verify_enrichment

    db_path = cast(Path, arguments.db)
    content_dir = cast(Path, arguments.content)
    source = cast(Path, arguments.source)
    canon_dir = cast(Path, arguments.canon)
    try:
        text = _read_source(source)
        batches = load_enrichment_batches(content_dir)
        registry = load_entity_registry(canon_dir)
    except (ValueError, FileNotFoundError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    doc = parse_source(text, source_name=source.name)
    report = verify_enrichment(batches, doc, registry)
    if not report.is_clean:
        for issue in report.errors:
            print(f"error: verification failed: {issue.to_json()}", file=sys.stderr)
        return 1
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    content_hash = canonical_content_hash(batches)
    manifest = build_manifest(
        content_sha256=content_hash,
        source_sha256=source_sha256,
        source_volumes=[batch.source_volume for batch in batches],
        source_unit_count=len(doc.units),
        build_tool_version="overlord-worldsim-cli",
        batch_counts={batch.batch_id: sum(batch.counts().values()) for batch in batches},
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    try:
        connection = open_canon_db(db_path)
        try:
            with connection:
                apply_enrichment(connection, batches, manifest)
        finally:
            connection.close()
        write_manifest_json(manifest, content_dir / "manifest.json")
    except (OSError, sqlite3.DatabaseError) as error:
        print(f"error: cannot apply enrichment: {error}", file=sys.stderr)
        return 2
    print(_canonical_json({"manifest": manifest, "summary": enrichment_summary(db_path)}))
    return 0


def _canonical_json(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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

    if command == "canon":
        canon_command = cast(str, arguments.canon_command)
        if canon_command == "parse":
            return _run_canon_parse(arguments)
        if canon_command == "build":
            return _run_canon_build(arguments)
        if canon_command == "search":
            return _run_canon_search(arguments)
        if canon_command == "build-embeddings":
            return _run_canon_build_embeddings(arguments)
        if canon_command == "verify":
            return _run_canon_verify(arguments)
        if canon_command == "apply":
            return _run_canon_apply(arguments)
        if canon_command == "enrich-verify":
            return _run_canon_enrich_verify(arguments)
        if canon_command == "enrich-apply":
            return _run_canon_enrich_apply(arguments)
        parser.error(f"unknown canon command: {canon_command}")

    parser.error(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
