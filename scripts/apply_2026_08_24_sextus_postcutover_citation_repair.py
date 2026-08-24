#!/usr/bin/env python3
"""Repair four citation rows left dangling by the Sextus exact-cohort cutover.

The core migration correctly rewired the corresponding KG edges but its first
production version only quarantined snapshot citation rows whose ``kg_node_id``
was a legacy passage node.  Four non-snapshot citation rows instead point to a
school/person node and carry the retired legacy UUID in ``passage_id``.

This post-cutover repair applies the already-adjudicated one-to-one loci from
the core migration.  It changes only ``data/corpus/citations.jsonl`` and writes
dedicated, non-overlapping quarantine/report artifacts.  Dry-run is default.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import scripts.apply_2026_08_24_sextus_exact_cohort_repair as core
except ModuleNotFoundError:  # Support direct ``python scripts/...py`` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import scripts.apply_2026_08_24_sextus_exact_cohort_repair as core

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "sextus_postcutover_citation_repair_2026_08_24"
QUARANTINE_RELATIVE = (
    "audit/2026-08-24_sextus_postcutover_citation_quarantine.jsonl"
)
REPORT_RELATIVE = "audit/2026-08-24_sextus_postcutover_citation_repair.json"
RECOVERY_RELATIVE = "audit/.sextus-postcutover-citations.recovery.json"
LOCK_RELATIVE = "audit/.sextus-postcutover-citations.lock"


@dataclass(frozen=True)
class Snapshot:
    nodes: list[dict[str, Any]]
    passages: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    original_bytes: dict[str, bytes]


@dataclass
class Result:
    citations: list[dict[str, Any]]
    quarantine: list[dict[str, Any]]
    changes: int
    report: dict[str, Any]


def _paths(data_root: Path) -> dict[str, Path]:
    return {
        "nodes": data_root / "kg/nodes.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
    }


def _rows(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def load_snapshot(data_root: Path) -> Snapshot:
    paths = _paths(data_root)
    first = {name: path.read_bytes() for name, path in paths.items()}
    second = {name: path.read_bytes() for name, path in paths.items()}
    if first != second:
        raise RuntimeError("concurrent write detected while loading post-cutover snapshot A")
    return Snapshot(
        nodes=_rows(first["nodes"]),
        passages=_rows(first["passages"]),
        citations=_rows(first["citations"]),
        original_bytes=first,
    )


def target_passage_id(decision: core.CitationRewireDecision) -> str:
    work_key, book, section = decision.target_locus
    work = core.WORKS[work_key]
    return core.stable_uuid(f"passage:{work.edition_urn}:{book}.{section}")


def target_cts_urn(decision: core.CitationRewireDecision) -> str:
    work_key, book, section = decision.target_locus
    return f"{core.WORKS[work_key].edition_urn}:{book}.{section}"


def old_row(decision: core.CitationRewireDecision) -> dict[str, Any]:
    return {
        "citation_type": decision.citation_type,
        "confidence": decision.confidence,
        "kg_node_id": decision.kg_node_id,
        "passage_id": decision.old_passage_id,
    }


def new_row(decision: core.CitationRewireDecision) -> dict[str, Any]:
    return {
        "citation_type": decision.citation_type,
        "confidence": decision.confidence,
        "kg_node_id": decision.kg_node_id,
        "passage_id": target_passage_id(decision),
    }


def _validate_targets(
    nodes: list[dict[str, Any]], passages: list[dict[str, Any]]
) -> None:
    node_ids = {core.node_id(row) for row in nodes}
    passage_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    if len(node_ids) != len(nodes) or len(passage_by_id) != len(passages):
        raise RuntimeError("duplicate node/passage IDs before post-cutover citation repair")
    for decision in core.CITATION_REWIRE_DECISIONS:
        if decision.kg_node_id not in node_ids:
            raise RuntimeError(f"citation subject node missing: {decision.kg_node_id}")
        target_id = target_passage_id(decision)
        passage = passage_by_id.get(target_id)
        if passage is None or passage.get("cts_urn") != target_cts_urn(decision):
            raise RuntimeError(
                f"exact post-cutover passage target missing: {decision.decision_id}"
            )
        if decision.old_passage_id in passage_by_id:
            raise RuntimeError(
                f"retired legacy passage unexpectedly active: {decision.old_passage_id}"
            )


def validate(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> dict[str, int]:
    _validate_targets(nodes, passages)
    node_ids = {core.node_id(row) for row in nodes}
    passage_ids = {str(row.get("passage_id") or "") for row in passages}
    citations_by_key = {core.citation_key(row): row for row in citations}
    if len(citations_by_key) != len(citations):
        raise RuntimeError("duplicate citation triplets after post-cutover repair")
    expected: set[str] = set()
    for decision in core.CITATION_REWIRE_DECISIONS:
        old_key = core.citation_key(old_row(decision))
        wanted = new_row(decision)
        new_key = core.citation_key(wanted)
        if old_key in citations_by_key:
            raise RuntimeError(f"old citation remains: {decision.decision_id}")
        if citations_by_key.get(new_key) != wanted:
            raise RuntimeError(f"exact citation missing: {decision.decision_id}")
        expected.add(new_key)
    dangling_passages = sum(
        str(row.get("passage_id") or "") not in passage_ids for row in citations
    )
    dangling_nodes = sum(
        str(row.get("kg_node_id") or "") not in node_ids for row in citations
    )
    if dangling_passages or dangling_nodes:
        raise RuntimeError(
            f"global dangling citations remain: passages={dangling_passages} nodes={dangling_nodes}"
        )
    return {
        "exact_adjudicated_citations": len(expected),
        "dangling_citation_passages": dangling_passages,
        "dangling_citation_nodes": dangling_nodes,
    }


def transform(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> Result:
    _validate_targets(nodes, passages)
    citations_out = copy.deepcopy(citations)
    by_key = {core.citation_key(row): row for row in citations_out}
    old_keys = {core.citation_key(old_row(row)) for row in core.CITATION_REWIRE_DECISIONS}
    new_keys = {core.citation_key(new_row(row)) for row in core.CITATION_REWIRE_DECISIONS}
    present_old = old_keys & set(by_key)
    present_new = new_keys & set(by_key)
    if not present_old and present_new == new_keys:
        validation = validate(nodes, passages, citations_out)
        return Result(
            citations=citations_out,
            quarantine=[],
            changes=0,
            report={
                "migration": STAMP,
                "status": "already_applied",
                "validation": validation,
            },
        )
    if present_old != old_keys or present_new:
        raise RuntimeError(
            "partial post-cutover citation repair detected: "
            f"old={len(present_old)} new={len(present_new)}"
        )

    decision_by_old = {
        core.citation_key(old_row(decision)): decision
        for decision in core.CITATION_REWIRE_DECISIONS
    }
    quarantine: list[dict[str, Any]] = []
    output: list[dict[str, Any]] = []
    adjudications: list[dict[str, Any]] = []
    for row in citations_out:
        decision = decision_by_old.get(core.citation_key(row))
        if decision is None:
            output.append(row)
            continue
        wanted = new_row(decision)
        quarantine.append(
            {
                "migration": STAMP,
                "reason": f"citation_claim_by_claim_rewire:{decision.decision_id}",
                "record": copy.deepcopy(row),
                "record_type": "corpus_citation_before",
            }
        )
        output.append(wanted)
        adjudications.append(
            {
                "citation_type": decision.citation_type,
                "confidence": decision.confidence,
                "decision_id": decision.decision_id,
                "kg_node_id": decision.kg_node_id,
                "old_passage_id": decision.old_passage_id,
                "new_passage_id": wanted["passage_id"],
                "rationale": decision.rationale,
                "target_cts_urn": target_cts_urn(decision),
            }
        )
    validation = validate(nodes, passages, output)
    report = {
        "adjudications": adjudications,
        "changes": len(adjudications),
        "migration": STAMP,
        "scope": "data/corpus/citations.jsonl only; registry untouched",
        "status": "planned",
        "validation": validation,
    }
    return Result(
        citations=output,
        quarantine=quarantine,
        changes=len(adjudications),
        report=report,
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_recovery_path(data_root: Path, raw: str) -> Path:
    root = data_root.resolve()
    path = Path(raw).resolve()
    if path != root and root not in path.parents:
        raise RuntimeError(f"post-cutover recovery path escapes data root: {raw}")
    return path


def _remove_recovery_file(path: Path) -> None:
    path.unlink(missing_ok=True)
    if path.parent.exists():
        core._fsync_directory(path.parent)


def recover_if_needed(data_root: Path) -> str | None:
    """Recover a transaction interrupted by BaseException or process death."""

    data_root = data_root.resolve()
    journal_path = data_root / RECOVERY_RELATIVE
    if not journal_path.exists():
        return None
    lock_path = data_root / LOCK_RELATIVE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("migration") != STAMP:
            raise RuntimeError("unknown post-cutover recovery journal")
        citations_path = _safe_recovery_path(data_root, journal["citations_path"])
        quarantine_path = _safe_recovery_path(data_root, journal["quarantine_path"])
        report_path = _safe_recovery_path(data_root, journal["report_path"])
        backup_path = _safe_recovery_path(data_root, journal["backup_path"])
        staged_paths = [
            _safe_recovery_path(data_root, raw) for raw in journal["staged_paths"]
        ]
        backup = backup_path.read_bytes()
        if _sha256(backup) != journal["citations_sha256_before"]:
            raise RuntimeError("post-cutover recovery backup hash mismatch")
        current_hash = _sha256(citations_path.read_bytes())
        artifact_complete = (
            quarantine_path.exists()
            and report_path.exists()
            and _sha256(quarantine_path.read_bytes())
            == journal["quarantine_sha256"]
            and _sha256(report_path.read_bytes()) == journal["report_sha256"]
        )
        if current_hash == journal["citations_sha256_after"] and artifact_complete:
            outcome = "completed"
        else:
            if current_hash != journal["citations_sha256_before"]:
                core._restore_bytes(citations_path, backup)
            quarantine_path.unlink(missing_ok=True)
            report_path.unlink(missing_ok=True)
            core._fsync_directory(quarantine_path.parent)
            outcome = "rolled_back"
        for path in [*staged_paths, backup_path]:
            path.unlink(missing_ok=True)
        _remove_recovery_file(journal_path)
    lock_path.unlink(missing_ok=True)
    core._fsync_directory(lock_path.parent)
    return outcome


def write_result(data_root: Path, result: Result, expected: dict[str, bytes]) -> None:
    if set(expected) != {"nodes", "passages", "citations"}:
        raise RuntimeError("post-cutover write lacks complete snapshot A")
    paths = _paths(data_root)
    citation_content = core._jsonl_content_preserving(
        expected["citations"], result.citations, core.citation_key, "citations"
    ).encode("utf-8")
    quarantine_path = data_root / QUARANTINE_RELATIVE
    report_path = data_root / REPORT_RELATIVE
    if quarantine_path.exists() or report_path.exists():
        raise RuntimeError("post-cutover output artifact already exists before first write")
    quarantine_content = (
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in result.quarantine
        )
        + "\n"
    ).encode("utf-8")
    report = copy.deepcopy(result.report)
    report["citations_sha256_before"] = _sha256(expected["citations"])
    report["citations_sha256_after"] = _sha256(citation_content)
    report_content = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    targets = [
        ("quarantine", quarantine_path, quarantine_content, None),
        ("report", report_path, report_content, None),
        ("citations", paths["citations"], citation_content, expected["citations"]),
    ]
    staged = {
        name: core._stage_bytes(path, content)
        for name, path, content, _original in targets
    }
    backup_path = core._stage_bytes(paths["citations"], expected["citations"])
    journal_path = data_root / RECOVERY_RELATIVE
    lock_path = data_root / LOCK_RELATIVE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    replaced: list[tuple[Path, bytes | None]] = []
    cleanup_transaction = False
    try:
        with lock_path.open("a+b") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            for name, path in paths.items():
                if path.read_bytes() != expected[name]:
                    raise RuntimeError(
                        f"concurrent write detected since post-cutover snapshot A: {path}"
                    )
            journal = {
                "migration": STAMP,
                "citations_path": str(paths["citations"]),
                "quarantine_path": str(quarantine_path),
                "report_path": str(report_path),
                "backup_path": str(backup_path),
                "staged_paths": [str(path) for path in staged.values()],
                "citations_sha256_before": _sha256(expected["citations"]),
                "citations_sha256_after": _sha256(citation_content),
                "quarantine_sha256": _sha256(quarantine_content),
                "report_sha256": _sha256(report_content),
                "state": "prepared",
            }
            journal_staged = core._stage_bytes(
                journal_path,
                (
                    json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n"
                ).encode(),
            )
            core._replace_staged_file(journal_staged, journal_path)
            for _name, path, _content, original in targets:
                if original is None:
                    if path.exists():
                        raise RuntimeError(f"post-cutover artifact appeared: {path}")
                elif path.read_bytes() != original:
                    raise RuntimeError(
                        f"concurrent citation write immediately before replace: {path}"
                    )
                core._replace_staged_file(staged[_name], path)
                replaced.append((path, original))
            cleanup_transaction = True
    except Exception:
        for path, original in reversed(replaced):
            if original is None:
                path.unlink(missing_ok=True)
                core._fsync_directory(path.parent)
            else:
                core._restore_bytes(path, original)
        cleanup_transaction = True
        raise
    finally:
        # BaseException/process death intentionally preserves the fsynced
        # journal, backup, and stages for recover_if_needed() on the next run.
        if cleanup_transaction:
            for temporary in [*staged.values(), backup_path]:
                temporary.unlink(missing_ok=True)
            _remove_recovery_file(journal_path)
        lock_path.unlink(missing_ok=True)
        core._fsync_directory(lock_path.parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--production-write-approved", action="store_true")
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    recovered = recover_if_needed(data_root)
    if recovered:
        print("recovery:", recovered)
    if (
        args.write
        and data_root == DEFAULT_DATA_ROOT.resolve()
        and not args.production_write_approved
    ):
        parser.error("production post-cutover citation write requires explicit approval")

    snapshot = load_snapshot(data_root)
    result = transform(snapshot.nodes, snapshot.passages, snapshot.citations)
    print("Sextus post-cutover citation repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("changes:", result.changes)
    print("validation:", json.dumps(result.report["validation"], sort_keys=True))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not result.changes:
        print("already applied: no files written")
        return 0
    write_result(data_root, result, snapshot.original_bytes)
    print("citations repaired; registry untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
