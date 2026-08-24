#!/usr/bin/env python3
"""Read-only audit of the EleutherIA SOTA scholarly completeness registry.

This script validates the registry as a durable proof system.  It deliberately
separates structural validity from scholarly exit readiness:

* return 0: the registry is structurally valid (work may remain);
* return 1: parse, invariant, hash, or cross-reference failure;
* return 2: ``--require-exit-gates`` was requested and a blocking gate failed.

It never edits the registry, KG, corpus, source archive, or audit artifacts, and
it never runs the external commands listed in ``exit_gates.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_ROOT = Path("data/goals/sota")

ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,127}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

SOURCE_KINDS = {
    "ancient_work",
    "ancient_witness",
    "critical_edition",
    "secondary_publication",
    "reference_work",
    "bibliographic_database",
}
SOURCE_SCOPE_DECISIONS = {"include_core", "include_context", "candidate", "exclude"}
IDENTITY_STATUSES = {
    "provisional",
    "bibliography_verified",
    "authority_verified",
    "rejected",
}
ACQUISITION_STATUSES = {
    "not_applicable",
    "not_sought",
    "missing",
    "local_unregistered",
    "archived_unverified",
    "archived_verified",
    "public_canonical",
}
COVERAGE_STATES = {
    "unknown",
    "none",
    "metadata_only",
    "partial",
    "complete",
    "complete_no_relevant_evidence",
    "excluded",
}
EVIDENCE_KINDS = {
    "ancient_passage",
    "secondary_claim",
    "bibliographic_fact",
    "translation_alignment",
    "negative_finding",
}
EVIDENCE_STATUSES = {
    "candidate",
    "in_review",
    "staged",
    "verified",
    "published",
    "rejected",
    "superseded",
}
ACTIVE_EVIDENCE_STATUSES = EVIDENCE_STATUSES - {"rejected", "superseded"}
ISSUE_STATUSES = {
    "open",
    "investigating",
    "blocked",
    "resolved",
    "adjudicated",
    "superseded",
}
OPEN_ISSUE_STATUSES = {"open", "investigating", "blocked"}
VERIFICATION_STAGES = {
    "identity",
    "primary",
    "independent",
    "adversarial",
    "adjudication",
    "regression",
    "human_signoff",
}
VERIFICATION_VERDICTS = {
    "pass",
    "fail",
    "supports_issue",
    "inconclusive",
    "superseded",
}
WAVE_STATUSES = {
    "planned",
    "next",
    "in_progress",
    "blocked",
    "complete",
    "superseded",
}

REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "source": (
        "record_type",
        "source_id",
        "source_kind",
        "display_label",
        "creators",
        "languages",
        "traditions",
        "topics",
        "scope_decision",
        "identity_status",
        "acquisition",
        "coverage",
        "provenance",
    ),
    "evidence": (
        "record_type",
        "evidence_id",
        "source_id",
        "evidence_kind",
        "claim_text",
        "attestation",
        "claim_status",
        "locator",
        "quotation",
        "kg_targets",
        "required_verification",
    ),
    "issue": (
        "record_type",
        "issue_id",
        "issue_type",
        "severity",
        "factual_risk",
        "status",
        "summary",
        "affected_ids",
        "evidence_artifacts",
        "resolution_criteria",
    ),
    "verification": (
        "record_type",
        "verification_id",
        "target_type",
        "target_id",
        "stage",
        "verifier",
        "method",
        "checked_locators",
        "verdict",
        "created_at",
        "artifacts",
    ),
    "wave": (
        "record_type",
        "wave_id",
        "label",
        "status",
        "score_components",
        "priority_score",
        "source_ids",
        "evidence_ids",
        "issue_ids",
        "blocked_by",
        "exit_criteria",
    ),
}

RECORD_CONFIG = {
    "source": ("registry/sources", "source_id"),
    "evidence": ("registry/evidence", "evidence_id"),
    "issue": ("registry/issues", "issue_id"),
    "verification": ("registry/verifications", "verification_id"),
    "wave": ("registry/waves", "wave_id"),
}


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 without mutating or loading the file at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


_INPUT_HASH_IGNORED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "dist",
        "node_modules",
    }
)


def input_set_sha256(repo_root: Path, relative_paths: list[str]) -> str:
    """Hash a deterministic file/tree set for current-snapshot proof freshness."""

    root = repo_root.resolve()
    entries: dict[str, Path] = {}
    for raw in sorted(set(relative_paths)):
        candidate = (root / raw).resolve()
        if root not in candidate.parents and candidate != root:
            raise ValueError(f"input path escapes repository: {raw!r}")
        if not candidate.exists():
            raise FileNotFoundError(raw)
        paths = [candidate] if candidate.is_file() else candidate.rglob("*")
        for path in paths:
            if not path.is_file() or any(
                part in _INPUT_HASH_IGNORED_PARTS for part in path.parts
            ):
                continue
            entries[path.relative_to(root).as_posix()] = path
    digest = hashlib.sha256()
    for relative, path in sorted(entries.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"{path}:{exc.lineno}: invalid JSON: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: expected a JSON object")
        return {}
    return value


def load_jsonl_shards(
    root: Path,
    relative_dir: str,
    expected_type: str,
    errors: list[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    directory = root / relative_dir
    records: list[dict[str, Any]] = []
    origins: dict[str, str] = {}
    if not directory.is_dir():
        errors.append(f"missing registry directory: {directory}")
        return records, origins

    id_field = RECORD_CONFIG[expected_type][1]
    paths = sorted(directory.glob("*.jsonl"))
    if not paths:
        errors.append(f"{directory}: no JSONL shards")
        return records, origins

    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}:{line_no}: invalid JSON: {exc.msg}")
                    continue
                if not isinstance(record, dict):
                    errors.append(f"{path}:{line_no}: expected a JSON object")
                    continue
                if record.get("record_type") != expected_type:
                    errors.append(
                        f"{path}:{line_no}: record_type must be {expected_type!r}"
                    )
                record_id = record.get(id_field)
                if isinstance(record_id, str):
                    if record_id in origins:
                        errors.append(
                            f"duplicate {id_field} {record_id!r}: "
                            f"{origins[record_id]} and {path}:{line_no}"
                        )
                    else:
                        origins[record_id] = f"{path}:{line_no}"
                records.append(record)
    return records, origins


def load_kg_ids(repo_root: Path, errors: list[str]) -> set[str]:
    path = repo_root / "data/kg/nodes.jsonl"
    ids: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}:{line_no}: invalid KG JSON: {exc.msg}")
                    continue
                node_id = row.get("node_id") or row.get("id")
                if isinstance(node_id, str) and node_id:
                    ids.add(node_id)
    except FileNotFoundError:
        errors.append(f"missing KG nodes file: {path}")
    return ids


def load_manifest_ids(repo_root: Path, errors: list[str]) -> set[str]:
    path = repo_root / "data/scholarly_sources/manifest.jsonl"
    ids: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}:{line_no}: invalid manifest JSON: {exc.msg}")
                    continue
                publication_dir = row.get("publication_dir")
                if isinstance(publication_dir, str):
                    ids.add(publication_dir)
    except FileNotFoundError:
        errors.append(f"missing scholarly source manifest: {path}")
    return ids


def require_fields(
    record: dict[str, Any],
    record_type: str,
    origin: str,
    errors: list[str],
) -> None:
    for field in REQUIRED_FIELDS[record_type]:
        if field not in record:
            errors.append(f"{origin}: missing required field {field!r}")


def require_string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        errors.append(f"{label}: expected a list of non-empty strings")
        return []
    if not allow_empty and not value:
        errors.append(f"{label}: list must not be empty")
    if len(value) != len(set(value)):
        errors.append(f"{label}: duplicate list values")
    return value


def validate_artifacts(
    artifacts: Any,
    label: str,
    repo_root: Path,
    errors: list[str],
) -> None:
    if not isinstance(artifacts, list):
        errors.append(f"{label}: artifacts must be a list")
        return
    for index, artifact in enumerate(artifacts):
        prefix = f"{label}[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{prefix}: artifact must be an object")
            continue
        locator = artifact.get("locator")
        if not isinstance(locator, str) or not locator:
            errors.append(f"{prefix}: missing locator")
            continue
        raw_hash = artifact.get("sha256")
        if raw_hash is not None and (
            not isinstance(raw_hash, str) or not SHA256_RE.fullmatch(raw_hash)
        ):
            errors.append(f"{prefix}: sha256 must be 64 lowercase hex characters")
            continue
        if locator.startswith(("data/", "docs/", "scripts/", "tests/")):
            resolved = repo_root / locator
            if not resolved.exists():
                errors.append(f"{prefix}: local artifact does not exist: {locator}")
            elif raw_hash is not None and resolved.is_file():
                actual = sha256_file(resolved)
                if actual != raw_hash:
                    errors.append(
                        f"{prefix}: stale artifact hash for {locator}: "
                        f"registered {raw_hash}, actual {actual}"
                    )


def validate_sources(
    records: list[dict[str, Any]],
    origins: dict[str, str],
    kg_ids: set[str],
    manifest_ids: set[str],
    repo_root: Path,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        source_id = record.get("source_id")
        origin = origins.get(str(source_id), "source record")
        require_fields(record, "source", origin, errors)
        if not isinstance(source_id, str) or not source_id.startswith("src_"):
            errors.append(f"{origin}: invalid source_id")
            continue
        index[source_id] = record
        if record.get("source_kind") not in SOURCE_KINDS:
            errors.append(f"{origin}: invalid source_kind {record.get('source_kind')!r}")
        if record.get("scope_decision") not in SOURCE_SCOPE_DECISIONS:
            errors.append(
                f"{origin}: invalid scope_decision {record.get('scope_decision')!r}"
            )
        if record.get("identity_status") not in IDENTITY_STATUSES:
            errors.append(
                f"{origin}: invalid identity_status {record.get('identity_status')!r}"
            )
        require_string_list(record.get("creators"), f"{origin}.creators", errors)
        require_string_list(record.get("languages"), f"{origin}.languages", errors)
        require_string_list(record.get("traditions"), f"{origin}.traditions", errors)
        require_string_list(record.get("topics"), f"{origin}.topics", errors)
        provenance = record.get("provenance")
        validate_artifacts(provenance, f"{origin}.provenance", repo_root, errors)
        if isinstance(provenance, list) and not provenance:
            errors.append(f"{origin}.provenance: at least one artifact is required")

        acquisition = record.get("acquisition")
        if not isinstance(acquisition, dict):
            errors.append(f"{origin}.acquisition: expected object")
        else:
            if acquisition.get("status") not in ACQUISITION_STATUSES:
                errors.append(
                    f"{origin}.acquisition: invalid status {acquisition.get('status')!r}"
                )
            manifest_refs = require_string_list(
                acquisition.get("manifest_publication_dirs"),
                f"{origin}.acquisition.manifest_publication_dirs",
                errors,
            )
            for manifest_ref in manifest_refs:
                if manifest_ref not in manifest_ids:
                    errors.append(
                        f"{origin}: unknown scholarly manifest publication_dir "
                        f"{manifest_ref!r}"
                    )
            validate_artifacts(
                acquisition.get("artifacts"),
                f"{origin}.acquisition.artifacts",
                repo_root,
                errors,
            )

        coverage = record.get("coverage")
        if not isinstance(coverage, dict):
            errors.append(f"{origin}.coverage: expected object")
        else:
            if coverage.get("state") not in COVERAGE_STATES:
                errors.append(
                    f"{origin}.coverage: invalid state {coverage.get('state')!r}"
                )
            node_ids = require_string_list(
                coverage.get("kg_node_ids"),
                f"{origin}.coverage.kg_node_ids",
                errors,
            )
            for node_id in node_ids:
                if node_id not in kg_ids:
                    errors.append(f"{origin}: unknown KG node id {node_id!r}")
            if not isinstance(coverage.get("basis"), str) or not coverage.get("basis"):
                errors.append(f"{origin}.coverage: non-empty basis is required")
    return index


def page_range_is_valid(value: Any) -> bool:
    if not isinstance(value, dict) or "start" not in value or "end" not in value:
        return False
    start = value["start"]
    end = value["end"]
    if isinstance(start, int) and isinstance(end, int):
        return start <= end
    return isinstance(start, str) and bool(start) and isinstance(end, str) and bool(end)


def validate_evidence(
    records: list[dict[str, Any]],
    origins: dict[str, str],
    sources: dict[str, dict[str, Any]],
    kg_ids: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        evidence_id = record.get("evidence_id")
        origin = origins.get(str(evidence_id), "evidence record")
        require_fields(record, "evidence", origin, errors)
        if not isinstance(evidence_id, str) or not evidence_id.startswith("ev_"):
            errors.append(f"{origin}: invalid evidence_id")
            continue
        index[evidence_id] = record
        source_id = record.get("source_id")
        if source_id not in sources:
            errors.append(f"{origin}: unknown source_id {source_id!r}")
        if record.get("evidence_kind") not in EVIDENCE_KINDS:
            errors.append(
                f"{origin}: invalid evidence_kind {record.get('evidence_kind')!r}"
            )
        if record.get("claim_status") not in EVIDENCE_STATUSES:
            errors.append(
                f"{origin}: invalid claim_status {record.get('claim_status')!r}"
            )
        if not isinstance(record.get("claim_text"), str) or not record.get("claim_text"):
            errors.append(f"{origin}: claim_text must be non-empty")
        targets = require_string_list(
            record.get("kg_targets"), f"{origin}.kg_targets", errors
        )
        for target in targets:
            if target not in kg_ids:
                errors.append(f"{origin}: unknown KG target {target!r}")
        require_string_list(
            record.get("required_verification"),
            f"{origin}.required_verification",
            errors,
            allow_empty=False,
        )
        locator = record.get("locator")
        if not isinstance(locator, dict):
            errors.append(f"{origin}.locator: expected object")
            continue
        printed_pages = locator.get("printed_pages")
        if printed_pages is not None and not page_range_is_valid(printed_pages):
            errors.append(f"{origin}.locator.printed_pages: invalid page range")
        pdf_pages = locator.get("pdf_pages")
        if pdf_pages is not None and not page_range_is_valid(pdf_pages):
            errors.append(f"{origin}.locator.pdf_pages: invalid page range")
        if record.get("evidence_kind") == "ancient_passage":
            if not locator.get("canonical_locus"):
                errors.append(f"{origin}: ancient passage requires canonical_locus")
            if not locator.get("edition_or_witness"):
                errors.append(f"{origin}: ancient passage requires edition_or_witness")
        if record.get("evidence_kind") == "secondary_claim" and not page_range_is_valid(
            printed_pages
        ):
            errors.append(f"{origin}: secondary claim requires printed_pages")
        quotation = record.get("quotation")
        if not isinstance(quotation, dict) or not quotation.get("status"):
            errors.append(f"{origin}.quotation: status is required")
    return index


def validate_issues(
    records: list[dict[str, Any]],
    origins: dict[str, str],
    repo_root: Path,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        issue_id = record.get("issue_id")
        origin = origins.get(str(issue_id), "issue record")
        require_fields(record, "issue", origin, errors)
        if not isinstance(issue_id, str) or not issue_id.startswith("issue_"):
            errors.append(f"{origin}: invalid issue_id")
            continue
        index[issue_id] = record
        if record.get("status") not in ISSUE_STATUSES:
            errors.append(f"{origin}: invalid issue status {record.get('status')!r}")
        if not isinstance(record.get("factual_risk"), bool):
            errors.append(f"{origin}: factual_risk must be boolean")
        require_string_list(record.get("affected_ids"), f"{origin}.affected_ids", errors)
        artifacts = record.get("evidence_artifacts")
        validate_artifacts(artifacts, f"{origin}.evidence_artifacts", repo_root, errors)
        if isinstance(artifacts, list) and not artifacts:
            errors.append(f"{origin}: at least one evidence artifact is required")
        if record.get("status") in {"resolved", "adjudicated"}:
            adjudication = record.get("adjudication")
            if not isinstance(adjudication, dict):
                errors.append(
                    f"{origin}: resolved/adjudicated issue requires adjudication object"
                )
            elif not adjudication.get("decision") or not adjudication.get("rationale"):
                errors.append(f"{origin}.adjudication: decision and rationale required")
    return index


def validate_verifications(
    records: list[dict[str, Any]],
    origins: dict[str, str],
    target_ids: dict[str, set[str]],
    repo_root: Path,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    index: dict[str, dict[str, Any]] = {}
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_review_keys: set[tuple[str, str, str]] = set()
    for record in records:
        verification_id = record.get("verification_id")
        origin = origins.get(str(verification_id), "verification record")
        require_fields(record, "verification", origin, errors)
        if not isinstance(verification_id, str) or not verification_id.startswith("ver_"):
            errors.append(f"{origin}: invalid verification_id")
            continue
        index[verification_id] = record
        target_type = record.get("target_type")
        target_id = record.get("target_id")
        if target_type not in target_ids:
            errors.append(f"{origin}: invalid target_type {target_type!r}")
        elif target_id not in target_ids[target_type]:
            errors.append(
                f"{origin}: unknown {target_type} target_id {target_id!r}"
            )
        if record.get("stage") not in VERIFICATION_STAGES:
            errors.append(f"{origin}: invalid stage {record.get('stage')!r}")
        if record.get("verdict") not in VERIFICATION_VERDICTS:
            errors.append(f"{origin}: invalid verdict {record.get('verdict')!r}")
        verifier = record.get("verifier")
        if not isinstance(verifier, dict):
            errors.append(f"{origin}.verifier: expected object")
            verifier_id = ""
        else:
            verifier_id = verifier.get("verifier_id")
            independence_group = verifier.get("independence_group")
            if not isinstance(verifier_id, str) or not ID_RE.fullmatch(verifier_id):
                errors.append(f"{origin}.verifier: invalid verifier_id")
            if not isinstance(independence_group, str) or not independence_group:
                errors.append(f"{origin}.verifier: independence_group is required")
        key = (str(target_id), str(record.get("stage")), str(verifier_id))
        if key in seen_review_keys:
            errors.append(
                f"{origin}: duplicate verifier/stage event for target {target_id!r}"
            )
        seen_review_keys.add(key)
        require_string_list(
            record.get("checked_locators"),
            f"{origin}.checked_locators",
            errors,
            allow_empty=False,
        )
        validate_artifacts(record.get("artifacts"), f"{origin}.artifacts", repo_root, errors)
        if isinstance(target_id, str):
            by_target[target_id].append(record)
    return index, by_target


def recompute_wave_score(
    wave: dict[str, Any], priority_model: dict[str, Any]
) -> float | None:
    components = wave.get("score_components")
    if not isinstance(components, dict) or not isinstance(priority_model, dict):
        return None
    try:
        return round(
            sum(float(priority_model[key]) * float(components[key]) for key in priority_model),
            4,
        )
    except (KeyError, TypeError, ValueError):
        return None


def validate_waves(
    records: list[dict[str, Any]],
    origins: dict[str, str],
    sources: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    issues: dict[str, dict[str, Any]],
    priority_model: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        wave_id = record.get("wave_id")
        origin = origins.get(str(wave_id), "wave record")
        require_fields(record, "wave", origin, errors)
        if not isinstance(wave_id, str) or not wave_id.startswith("wave_"):
            errors.append(f"{origin}: invalid wave_id")
            continue
        index[wave_id] = record
        if record.get("status") not in WAVE_STATUSES:
            errors.append(f"{origin}: invalid status {record.get('status')!r}")
        refs = (
            ("source_ids", sources),
            ("evidence_ids", evidence),
            ("issue_ids", issues),
            ("blocked_by", issues),
        )
        for field, target in refs:
            values = require_string_list(record.get(field), f"{origin}.{field}", errors)
            for value in values:
                if value not in target:
                    errors.append(f"{origin}.{field}: unknown id {value!r}")
        require_string_list(
            record.get("exit_criteria"),
            f"{origin}.exit_criteria",
            errors,
            allow_empty=False,
        )
        computed = recompute_wave_score(record, priority_model)
        if computed is None:
            errors.append(f"{origin}: invalid score_components or priority model")
        else:
            try:
                declared = float(record.get("priority_score"))
            except (TypeError, ValueError):
                errors.append(f"{origin}: priority_score must be numeric")
            else:
                if abs(computed - declared) > 0.01:
                    errors.append(
                        f"{origin}: priority_score {declared} != computed {computed}"
                    )
    return index


def has_independent_pair(
    reviews: Iterable[dict[str, Any]],
    primary_stages: frozenset[str] = frozenset({"primary"}),
) -> bool:
    """Return whether two passing reviews are genuinely independent.

    Evidence and issue claims use ``primary`` as the first stage. Source
    identities may use the more precise ``identity`` stage; callers opt into
    that stage explicitly rather than silently counting it everywhere.
    """
    primaries = [
        row
        for row in reviews
        if row.get("stage") in primary_stages and row.get("verdict") == "pass"
    ]
    independents = [
        row
        for row in reviews
        if row.get("stage") == "independent" and row.get("verdict") == "pass"
    ]
    for primary in primaries:
        p_verifier = primary.get("verifier") or {}
        for independent in independents:
            i_verifier = independent.get("verifier") or {}
            if (
                p_verifier.get("verifier_id") != i_verifier.get("verifier_id")
                and p_verifier.get("independence_group")
                != i_verifier.get("independence_group")
            ):
                return True
    return False


def has_adversarial_pass(reviews: Iterable[dict[str, Any]]) -> bool:
    return any(
        row.get("stage") == "adversarial" and row.get("verdict") == "pass"
        for row in reviews
    )


def gate_result(gate: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    return {
        "gate_id": gate.get("gate_id"),
        "label": gate.get("label"),
        "status": "pass" if not reasons else "fail",
        "blocking": bool(gate.get("blocking", True)),
        "reasons": reasons,
    }


def evaluate_gate(
    gate: dict[str, Any],
    *,
    errors: list[str],
    scope: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    issues: dict[str, dict[str, Any]],
    reviews_by_target: dict[str, list[dict[str, Any]]],
    repo_root: Path,
) -> dict[str, Any]:
    evaluator = gate.get("evaluator")
    reasons: list[str] = []
    included_sources = {
        source_id: source
        for source_id, source in sources.items()
        if source.get("scope_decision") in {"include_core", "include_context"}
    }
    active_evidence = {
        evidence_id: row
        for evidence_id, row in evidence.items()
        if row.get("claim_status") in ACTIVE_EVIDENCE_STATUSES
    }

    if evaluator == "registry_integrity":
        reasons.extend(errors)

    elif evaluator == "scope_saturation":
        required_facets = scope.get("required_facets") or {}
        cells = scope.get("coverage_cells") or []
        for facet, required_values in required_facets.items():
            covered = {
                value
                for cell in cells
                if isinstance(cell, dict)
                for value in cell.get(facet, [])
            }
            missing = sorted(set(required_values) - covered)
            if missing:
                reasons.append(f"facet {facet} absent from coverage cells: {', '.join(missing)}")
        policy = scope.get("closure_policy") or {}
        required_surfaces = set(policy.get("required_search_surfaces") or [])
        min_zero_rounds = int(policy.get("minimum_zero_yield_citation_chase_rounds", 2))
        for cell in cells:
            if not isinstance(cell, dict):
                reasons.append("scope contains a non-object coverage cell")
                continue
            cell_id = cell.get("cell_id", "unknown_cell")
            if cell.get("status") != "saturated":
                reasons.append(f"{cell_id}: status is {cell.get('status')!r}, not saturated")
            runs = cell.get("search_runs") or []
            seen_surfaces = {
                run.get("surface") for run in runs if isinstance(run, dict)
            }
            missing_surfaces = sorted(required_surfaces - seen_surfaces)
            if missing_surfaces:
                reasons.append(
                    f"{cell_id}: missing search surfaces: {', '.join(missing_surfaces)}"
                )
            rounds = cell.get("citation_chase_rounds") or []
            zero_tail = 0
            for round_record in reversed(rounds):
                if isinstance(round_record, dict) and not round_record.get(
                    "new_included_source_ids"
                ):
                    zero_tail += 1
                else:
                    break
            if zero_tail < min_zero_rounds:
                reasons.append(
                    f"{cell_id}: {zero_tail} consecutive zero-yield citation rounds; "
                    f"need {min_zero_rounds}"
                )
            if not has_independent_pair(reviews_by_target.get(str(cell_id), [])):
                reasons.append(f"{cell_id}: missing independent primary/review pair")
        candidates = sorted(
            source_id
            for source_id, source in sources.items()
            if source.get("scope_decision") == "candidate"
        )
        if candidates:
            reasons.append(f"{len(candidates)} unresolved candidate source(s)")

    elif evaluator == "source_identity":
        bad = sorted(
            source_id
            for source_id, source in included_sources.items()
            if source.get("identity_status")
            not in {"bibliography_verified", "authority_verified"}
        )
        if bad:
            reasons.append(f"{len(bad)} included source identity record(s) are provisional")
        unreviewed = sorted(
            source_id
            for source_id, source in included_sources.items()
            if source.get("identity_status")
            in {"bibliography_verified", "authority_verified"}
            and not has_independent_pair(
                reviews_by_target.get(source_id, []),
                frozenset({"identity", "primary"}),
            )
        )
        if unreviewed:
            reasons.append(
                f"{len(unreviewed)} verified identity flag(s) lack independent proof"
            )
        identity_issues = [
            issue_id
            for issue_id, issue in issues.items()
            if issue.get("issue_type") == "bibliographic_identity"
            and issue.get("status") in OPEN_ISSUE_STATUSES
        ]
        if identity_issues:
            reasons.append(f"{len(identity_issues)} open bibliographic identity issue(s)")

    elif evaluator == "source_reproducibility":
        by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in active_evidence.values():
            by_source[str(row.get("source_id"))].append(row)
        for source_id, source in included_sources.items():
            acquisition = source.get("acquisition") or {}
            status = acquisition.get("status")
            source_kind = source.get("source_kind")
            if source_kind == "ancient_work" and status == "not_applicable":
                units = by_source.get(source_id, [])
                reproducible = any(
                    (row.get("locator") or {}).get("edition_or_witness")
                    and (row.get("quotation") or {}).get("corpus_passage_ids")
                    for row in units
                )
                if not reproducible:
                    reasons.append(
                        f"{source_id}: abstract ancient work lacks reproducible witness evidence"
                    )
            elif status not in {"archived_verified", "public_canonical"}:
                reasons.append(f"{source_id}: acquisition status is {status!r}")

    elif evaluator == "evidence_coverage":
        for source_id, source in included_sources.items():
            state = (source.get("coverage") or {}).get("state")
            if state not in {"complete", "complete_no_relevant_evidence"}:
                reasons.append(f"{source_id}: coverage state is {state!r}")
            source_units = [
                row for row in active_evidence.values() if row.get("source_id") == source_id
            ]
            if state == "complete" and not source_units:
                reasons.append(f"{source_id}: complete coverage has no evidence units")
            if state == "complete_no_relevant_evidence":
                decisions = [
                    issue
                    for issue in issues.values()
                    if source_id in issue.get("affected_ids", [])
                    and issue.get("status") == "adjudicated"
                ]
                if not decisions:
                    reasons.append(
                        f"{source_id}: no-relevant-evidence state lacks adjudication"
                    )
        unresolved_units = [
            evidence_id
            for evidence_id, row in active_evidence.items()
            if row.get("claim_status") not in {"verified", "published"}
        ]
        if unresolved_units:
            reasons.append(f"{len(unresolved_units)} active evidence unit(s) are not verified")

    elif evaluator == "locator_completeness":
        for evidence_id, row in active_evidence.items():
            locator = row.get("locator") or {}
            quotation = row.get("quotation") or {}
            if row.get("evidence_kind") == "ancient_passage":
                if not locator.get("canonical_locus") or not locator.get(
                    "edition_or_witness"
                ):
                    reasons.append(f"{evidence_id}: missing ancient locus or witness")
                if quotation.get("status") != "collated":
                    reasons.append(f"{evidence_id}: ancient quotation is not collated")
                if not quotation.get("text_sha256") and not quotation.get(
                    "corpus_passage_ids"
                ):
                    reasons.append(f"{evidence_id}: no quote hash or corpus passage id")
            elif row.get("evidence_kind") == "secondary_claim":
                if not page_range_is_valid(locator.get("printed_pages")):
                    reasons.append(f"{evidence_id}: missing printed page range")
                if locator.get("page_map_status") != "visually_verified":
                    reasons.append(f"{evidence_id}: PDF/printed page map not visually verified")

    elif evaluator == "double_verification":
        for evidence_id in active_evidence:
            if not has_independent_pair(reviews_by_target.get(evidence_id, [])):
                reasons.append(f"{evidence_id}: no independent passing review pair")
        for issue_id, issue in issues.items():
            if (
                issue.get("factual_risk")
                and issue.get("status") in {"resolved", "adjudicated"}
                and not has_independent_pair(reviews_by_target.get(issue_id, []))
            ):
                reasons.append(f"{issue_id}: factual resolution lacks independent pair")

    elif evaluator == "adversarial_verification":
        for evidence_id in active_evidence:
            if not has_adversarial_pass(reviews_by_target.get(evidence_id, [])):
                reasons.append(f"{evidence_id}: no passing adversarial review")
        for issue_id, issue in issues.items():
            if (
                issue.get("factual_risk")
                and issue.get("status") in {"resolved", "adjudicated"}
                and not has_adversarial_pass(reviews_by_target.get(issue_id, []))
            ):
                reasons.append(f"{issue_id}: factual resolution lacks adversarial review")

    elif evaluator == "zero_known_factual_errors":
        open_factual = sorted(
            issue_id
            for issue_id, issue in issues.items()
            if issue.get("factual_risk") and issue.get("status") in OPEN_ISSUE_STATUSES
        )
        if open_factual:
            reasons.append(f"{len(open_factual)} factual-risk issue(s) remain open")

    elif evaluator == "kg_integrity_suite":
        required_commands = set(gate.get("required_commands") or [])
        proof_fresh = True
        input_paths = gate.get("input_paths")
        proof_locator = gate.get("proof_artifact")
        if not isinstance(input_paths, list) or not all(
            isinstance(path, str) and path for path in input_paths
        ):
            reasons.append("integrity input_paths are missing or invalid")
            proof_fresh = False
        if not isinstance(proof_locator, str) or not proof_locator:
            reasons.append("integrity proof_artifact is missing")
            proof_fresh = False
        if proof_fresh:
            try:
                current_input_hash = input_set_sha256(repo_root, input_paths)
                proof = json.loads(
                    (repo_root / proof_locator).read_text(encoding="utf-8")
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                reasons.append(f"integrity proof cannot be validated: {exc}")
                proof_fresh = False
            else:
                if proof.get("input_set_sha256") != current_input_hash:
                    reasons.append("integrity proof input hash is stale")
                    proof_fresh = False
        passing = [
            row
            for row in reviews_by_target.get(str(gate.get("gate_id")), [])
            if proof_fresh
            and row.get("stage") == "regression"
            and row.get("verdict") == "pass"
        ]
        passed_commands = {str(row.get("method")) for row in passing}
        missing = sorted(required_commands - passed_commands)
        if missing:
            reasons.append(f"{len(missing)} required current-snapshot command proof(s) missing")

    elif evaluator == "human_release_signoff":
        signoffs = [
            row
            for row in reviews_by_target.get(str(gate.get("gate_id")), [])
            if row.get("stage") == "human_signoff"
            and row.get("verdict") == "pass"
            and (row.get("verifier") or {}).get("kind") == "human_scholar"
        ]
        pairs = False
        for index, first in enumerate(signoffs):
            f = first.get("verifier") or {}
            for second in signoffs[index + 1 :]:
                s = second.get("verifier") or {}
                if (
                    f.get("verifier_id") != s.get("verifier_id")
                    and f.get("independence_group") != s.get("independence_group")
                ):
                    pairs = True
        if not pairs:
            reasons.append("two independent human-scholar signoffs are missing")

    else:
        reasons.append(f"unknown evaluator {evaluator!r}")
    return gate_result(gate, reasons)


def validate_scope(scope: dict[str, Any], errors: list[str]) -> set[str]:
    if scope.get("schema_version") != "1.0.0":
        errors.append("scope.json: schema_version must be '1.0.0'")
    cells = scope.get("coverage_cells")
    if not isinstance(cells, list) or not cells:
        errors.append("scope.json: coverage_cells must be a non-empty list")
        return set()
    ids: set[str] = set()
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"scope.json: coverage_cells[{index}] is not an object")
            continue
        cell_id = cell.get("cell_id")
        if not isinstance(cell_id, str) or not cell_id.startswith("cell_"):
            errors.append(f"scope.json: coverage_cells[{index}] has invalid cell_id")
            continue
        if cell_id in ids:
            errors.append(f"scope.json: duplicate cell_id {cell_id!r}")
        ids.add(cell_id)
        for facet in ("periods", "traditions", "topics", "languages"):
            require_string_list(
                cell.get(facet),
                f"scope.json:{cell_id}.{facet}",
                errors,
                allow_empty=False,
            )
        if cell.get("status") not in {"open", "screening", "saturated", "reopened"}:
            errors.append(f"scope.json:{cell_id}: invalid status {cell.get('status')!r}")
    return ids


def validate_gate_definitions(
    payload: dict[str, Any], errors: list[str]
) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    if payload.get("schema_version") != "1.0.0":
        errors.append("exit_gates.json: schema_version must be '1.0.0'")
    gates = payload.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("exit_gates.json: gates must be a non-empty list")
        gates = []
    ids: set[str] = set()
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"exit_gates.json:gates[{index}] is not an object")
            continue
        gate_id = gate.get("gate_id")
        if not isinstance(gate_id, str) or not gate_id.startswith("gate_"):
            errors.append(f"exit_gates.json:gates[{index}] has invalid gate_id")
        elif gate_id in ids:
            errors.append(f"exit_gates.json: duplicate gate_id {gate_id!r}")
        else:
            ids.add(gate_id)
        if not gate.get("evaluator") or not gate.get("acceptance"):
            errors.append(f"exit_gates.json:{gate_id}: evaluator and acceptance required")
    priority_model = payload.get("priority_model")
    if not isinstance(priority_model, dict) or not priority_model:
        errors.append("exit_gates.json: priority_model must be a non-empty object")
        priority_model = {}
    else:
        try:
            weight_sum = sum(float(value) for value in priority_model.values())
        except (TypeError, ValueError):
            errors.append("exit_gates.json: priority weights must be numeric")
        else:
            if abs(weight_sum - 100.0) > 0.001:
                errors.append(
                    f"exit_gates.json: priority weights sum to {weight_sum}, not 100"
                )
    return gates, ids, priority_model


def validate_affected_references(
    issues: dict[str, dict[str, Any]], known_ids: set[str], errors: list[str]
) -> None:
    for issue_id, issue in issues.items():
        for affected_id in issue.get("affected_ids", []):
            if affected_id not in known_ids:
                errors.append(f"{issue_id}: unknown affected_id {affected_id!r}")


def choose_next_wave(
    waves: dict[str, dict[str, Any]], issues: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    declared_next = [row for row in waves.values() if row.get("status") == "next"]
    if len(declared_next) != 1:
        problems.append(f"expected exactly one next wave, found {len(declared_next)}")
    eligible = []
    for row in waves.values():
        if row.get("status") not in {"next", "planned"}:
            continue
        unresolved_blockers = [
            issue_id
            for issue_id in row.get("blocked_by", [])
            if issues.get(issue_id, {}).get("status") not in {"resolved", "adjudicated", "superseded"}
        ]
        if not unresolved_blockers:
            eligible.append(row)
    expected = max(eligible, key=lambda row: float(row.get("priority_score", 0)), default=None)
    if declared_next and expected and declared_next[0].get("wave_id") != expected.get("wave_id"):
        problems.append(
            f"declared next wave {declared_next[0].get('wave_id')} is not highest-scoring "
            f"unblocked wave {expected.get('wave_id')}"
        )
    return (declared_next[0] if len(declared_next) == 1 else expected), problems


def audit_registry(registry_root: Path, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Audit the registry and return a JSON-serializable report."""
    if not registry_root.is_absolute():
        registry_root = repo_root / registry_root
    errors: list[str] = []
    warnings: list[str] = []

    schema = load_json(registry_root / "registry.schema.json", errors)
    if "$defs" not in schema:
        errors.append("registry.schema.json: missing $defs")
    scope = load_json(registry_root / "scope.json", errors)
    scope_cell_ids = validate_scope(scope, errors)
    gate_payload = load_json(registry_root / "exit_gates.json", errors)
    gates, gate_ids, priority_model = validate_gate_definitions(gate_payload, errors)

    loaded: dict[str, list[dict[str, Any]]] = {}
    origins: dict[str, dict[str, str]] = {}
    for record_type, (relative_dir, _id_field) in RECORD_CONFIG.items():
        loaded[record_type], origins[record_type] = load_jsonl_shards(
            registry_root, relative_dir, record_type, errors
        )

    kg_ids = load_kg_ids(repo_root, errors)
    manifest_ids = load_manifest_ids(repo_root, errors)
    sources = validate_sources(
        loaded["source"],
        origins["source"],
        kg_ids,
        manifest_ids,
        repo_root,
        errors,
    )
    evidence = validate_evidence(
        loaded["evidence"], origins["evidence"], sources, kg_ids, errors
    )
    issues = validate_issues(
        loaded["issue"], origins["issue"], repo_root, errors
    )
    waves = validate_waves(
        loaded["wave"],
        origins["wave"],
        sources,
        evidence,
        issues,
        priority_model,
        errors,
    )

    target_ids = {
        "source": set(sources),
        "evidence": set(evidence),
        "issue": set(issues),
        "scope_cell": scope_cell_ids,
        "gate": gate_ids,
    }
    verifications, reviews_by_target = validate_verifications(
        loaded["verification"],
        origins["verification"],
        target_ids,
        repo_root,
        errors,
    )
    known_ids = set(kg_ids) | set(sources) | set(evidence) | set(issues) | scope_cell_ids
    validate_affected_references(issues, known_ids, errors)

    next_wave, wave_problems = choose_next_wave(waves, issues)
    errors.extend(f"wave queue: {problem}" for problem in wave_problems)

    gate_results = [
        evaluate_gate(
            gate,
            errors=errors,
            scope=scope,
            sources=sources,
            evidence=evidence,
            issues=issues,
            reviews_by_target=reviews_by_target,
            repo_root=repo_root,
        )
        for gate in gates
        if isinstance(gate, dict)
    ]
    ready = bool(gate_results) and all(
        result["status"] == "pass"
        for result in gate_results
        if result.get("blocking", True)
    )

    source_kinds = Counter(row.get("source_kind", "unknown") for row in sources.values())
    coverage_states = Counter(
        (row.get("coverage") or {}).get("state", "unknown")
        for row in sources.values()
    )
    evidence_statuses = Counter(
        row.get("claim_status", "unknown") for row in evidence.values()
    )
    issue_statuses = Counter(row.get("status", "unknown") for row in issues.values())
    fully_reviewed = sum(
        1
        for evidence_id, row in evidence.items()
        if row.get("claim_status") in ACTIVE_EVIDENCE_STATUSES
        and has_independent_pair(reviews_by_target.get(evidence_id, []))
        and has_adversarial_pass(reviews_by_target.get(evidence_id, []))
    )
    active_count = sum(
        1
        for row in evidence.values()
        if row.get("claim_status") in ACTIVE_EVIDENCE_STATUSES
    )
    if not ready:
        warnings.append(
            "Registry is a valid open work queue, not evidence of exhaustive or error-free coverage."
        )

    return {
        "schema_version": "1.0.0",
        "registry_root": str(registry_root),
        "structurally_valid": not errors,
        "exit_ready": ready,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sources": len(sources),
            "source_kinds": dict(sorted(source_kinds.items())),
            "source_coverage_states": dict(sorted(coverage_states.items())),
            "evidence_units": len(evidence),
            "evidence_statuses": dict(sorted(evidence_statuses.items())),
            "active_evidence_fully_reviewed": fully_reviewed,
            "active_evidence_total": active_count,
            "issues": len(issues),
            "issue_statuses": dict(sorted(issue_statuses.items())),
            "verifications": len(verifications),
            "waves": len(waves),
            "scope_cells": len(scope_cell_ids),
            "kg_node_ids_seen": len(kg_ids),
            "scholarly_manifest_records_seen": len(manifest_ids),
        },
        "gates": gate_results,
        "next_wave": next_wave,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "SOTA scholarly registry audit",
        f"structurally_valid: {str(report['structurally_valid']).lower()}",
        f"exit_ready: {str(report['exit_ready']).lower()}",
    ]
    metrics = report["metrics"]
    lines.extend(
        [
            (
                f"records: {metrics['sources']} sources, "
                f"{metrics['evidence_units']} evidence units, "
                f"{metrics['issues']} issues, "
                f"{metrics['verifications']} verifications"
            ),
            (
                "independently+adversarially reviewed active evidence: "
                f"{metrics['active_evidence_fully_reviewed']}/"
                f"{metrics['active_evidence_total']}"
            ),
            "gates:",
        ]
    )
    for gate in report["gates"]:
        lines.append(
            f"  {gate['status'].upper():4} {gate['gate_id']}: "
            f"{len(gate['reasons'])} blocking reason(s)"
        )
    next_wave = report.get("next_wave")
    if next_wave:
        lines.append(
            f"next_wave: {next_wave.get('wave_id')} "
            f"(score {next_wave.get('priority_score')})"
        )
    if report["errors"]:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in report["errors"])
    lines.extend(f"warning: {warning}" for warning in report["warnings"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=DEFAULT_REGISTRY_ROOT,
        help="Registry root, relative to repository root by default.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--require-exit-gates",
        action="store_true",
        help="Return 2 unless every blocking SOTA exit gate passes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_registry(args.registry_root)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    if not report["structurally_valid"]:
        return 1
    if args.require_exit_gates and not report["exit_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
