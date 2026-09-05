"""Release-bound GraphRAG evaluation harness (schema v2).

``live-http`` captures the raw backend response and scores retrieval separately
from generation. The ``snapshot-*`` runners are deterministic,
key-free retrieval baselines over the checked-out corpus/KG exports.

There is deliberately no composite quality score: passage/entity/work
retrieval, citations, complete evidence sets, abstention, source identity,
quote fidelity and publication safety remain independently visible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - offline runners do not need it
    httpx = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml is required (pip install pyyaml)", file=sys.stderr)
    raise

try:
    from tests.eval.eval_lib.forbidden import (
        ForbiddenString,
        find_forbidden_strings,
        load_forbidden_strings,
    )
    from tests.eval.eval_lib.gates import compare_with_gates
    from tests.eval.eval_lib.schema import RUN_SCHEMA_VERSION, validate_run_document
    from tests.eval.eval_lib.scoring import (
        complete_evidence_set_recall,
        score_gold_set,
    )
    from tests.eval.eval_lib.snapshot_runner import (
        DEFAULT_CITATIONS,
        DEFAULT_EDGES,
        DEFAULT_MANIFEST,
        DEFAULT_NODES,
        DEFAULT_PASSAGES,
        SUPPORTED_STRATEGIES,
        SnapshotIndex,
    )
except ImportError:  # direct execution from tests/eval/
    from eval_lib.forbidden import (  # type: ignore[no-redef]
        ForbiddenString,
        find_forbidden_strings,
        load_forbidden_strings,
    )
    from eval_lib.gates import compare_with_gates  # type: ignore[no-redef]
    from eval_lib.schema import (  # type: ignore[no-redef]
        RUN_SCHEMA_VERSION,
        validate_run_document,
    )
    from eval_lib.scoring import (  # type: ignore[no-redef]
        complete_evidence_set_recall,
        score_gold_set,
    )
    from eval_lib.snapshot_runner import (  # type: ignore[no-redef]
        DEFAULT_CITATIONS,
        DEFAULT_EDGES,
        DEFAULT_MANIFEST,
        DEFAULT_NODES,
        DEFAULT_PASSAGES,
        SUPPORTED_STRATEGIES,
        SnapshotIndex,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = float(os.environ.get("ELEUTHERIA_EVAL_TIMEOUT", "180"))
QUERY_PATH = "/api/graphrag/query"
STREAM_QUERY_PATH = "/api/graphrag/query/stream"
SAFE_RESPONSE_HEADERS = {
    "content-type",
    "date",
    "server",
    "x-request-id",
    "x-trace-id",
    "x-release-id",
}
CODE_BINDING_PATHS = (
    Path(__file__),
    Path(__file__).parent / "run.schema.json",
    Path(__file__).parent / "eval_lib" / "scoring.py",
    Path(__file__).parent / "eval_lib" / "schema.py",
    Path(__file__).parent / "eval_lib" / "gates.py",
    Path(__file__).parent / "eval_lib" / "snapshot_runner.py",
)


def _dedup(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _code_sha256() -> str:
    material = []
    for path in CODE_BINDING_PATHS:
        if not path.is_file():
            continue
        try:
            label = str(path.resolve().relative_to(REPO_ROOT))
        except ValueError:
            label = str(path.resolve())
        material.append({"path": label, "sha256": _file_sha256(path)})
    return _canonical_sha256(material)


def _git_state() -> tuple[str | None, bool | None]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return revision or None, dirty
    except OSError, subprocess.SubprocessError:
        return None, None


@dataclass
class QueryCase:
    id: str
    query: str
    query_type: str
    difficulty: str
    expected_entities: list[str] = field(default_factory=list)
    expected_entity_keywords: list[str] = field(default_factory=list)
    expected_works: list[str] = field(default_factory=list)
    expected_manifestations: list[str] = field(default_factory=list)
    expected_passages: list[str] = field(default_factory=list)
    complete_evidence_sets: list[list[str]] = field(default_factory=list)
    expected_passage_identities: dict[str, dict[str, str]] = field(default_factory=dict)
    forbidden_passages: list[str] = field(default_factory=list)
    gold_claims: list[str] = field(default_factory=list)
    answerable: bool = True
    strata: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def all_strata(self) -> list[str]:
        return _dedup(
            [
                *self.strata,
                f"query_type:{self.query_type}",
                f"difficulty:{self.difficulty}",
                f"answerability:{'answerable' if self.answerable else 'ood'}",
            ]
        )

    @property
    def evidence_sets(self) -> list[list[str]]:
        if self.complete_evidence_sets:
            return self.complete_evidence_sets
        return [self.expected_passages] if self.expected_passages else []


# Compatibility type for code that imported the v1 helper surface.
@dataclass
class QueryResult:
    id: str
    query: str
    query_type: str
    difficulty: str
    expected_entities: list[str]
    expected_works: list[str]
    returned_entities: list[str]
    returned_works: list[str]
    citation_count: int
    answer_chars: int
    latency_ms: float
    entity_recall: float
    entity_precision: float
    keyword_hit_rate: float
    work_recall: float
    citation_precision: float | None = None
    citation_recall: float | None = None
    citation_f1: float | None = None
    forbidden_hits: list[str] = field(default_factory=list)
    judge: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class RunBinding:
    runner_id: str
    release_id: str
    model_id: str | None
    config_id: str
    config_sha256: str
    generation_enabled: bool
    code_revision: str | None
    code_sha256: str
    workspace_dirty: bool | None
    python_version: str
    python_implementation: str
    snapshot_sha256: str | None
    snapshot_files: dict[str, str]
    snapshot_scope: str


def _parse_case(entry: dict[str, Any], source: Path) -> QueryCase:
    identities = entry.get("expected_passage_identities") or {}
    complete_sets = entry.get("complete_evidence_sets") or []
    if not isinstance(identities, dict):
        raise ValueError(
            f"{source}: {entry.get('id')}: expected_passage_identities must be a map"
        )
    if not isinstance(complete_sets, list) or not all(
        isinstance(group, list) for group in complete_sets
    ):
        raise ValueError(
            f"{source}: {entry.get('id')}: complete_evidence_sets must be a list of lists"
        )
    case = QueryCase(
        id=str(entry["id"]),
        query=str(entry["query"]),
        query_type=str(entry.get("query_type", "unknown")),
        difficulty=str(entry.get("difficulty", "unknown")),
        expected_entities=[str(v) for v in entry.get("expected_entities", [])],
        expected_entity_keywords=[
            str(v) for v in entry.get("expected_entity_keywords", [])
        ],
        expected_works=[str(v) for v in entry.get("expected_works", [])],
        expected_manifestations=[
            str(v) for v in entry.get("expected_manifestations", [])
        ],
        expected_passages=[str(v) for v in entry.get("expected_passages", [])],
        complete_evidence_sets=[[str(v) for v in group] for group in complete_sets],
        expected_passage_identities={
            str(passage_id): {str(key): str(value) for key, value in identity.items()}
            for passage_id, identity in identities.items()
            if isinstance(identity, dict)
        },
        forbidden_passages=[str(v) for v in entry.get("forbidden_passages", [])],
        gold_claims=[str(v) for v in entry.get("gold_claims", [])],
        answerable=bool(entry.get("answerable", True)),
        strata=[str(v) for v in entry.get("strata", [])],
        provenance=dict(entry.get("provenance") or {}),
    )
    if not case.id or not case.query.strip():
        raise ValueError(f"{source}: query id and text must be non-empty")
    for name, values in (
        ("expected_entities", case.expected_entities),
        ("expected_works", case.expected_works),
        ("expected_manifestations", case.expected_manifestations),
        ("expected_passages", case.expected_passages),
        ("forbidden_passages", case.forbidden_passages),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"{source}: {case.id}: duplicate value in {name}")
    if set(case.expected_passages) & set(case.forbidden_passages):
        raise ValueError(
            f"{source}: {case.id}: passage cannot be expected and forbidden"
        )
    return case


def load_queries(path: Path) -> list[QueryCase]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("queries"), list):
        raise ValueError(f"{path}: missing top-level 'queries' list")
    cases = [_parse_case(entry, path) for entry in raw["queries"]]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate query ids")
    return cases


def load_query_files(paths: list[Path]) -> list[QueryCase]:
    cases = [case for path in paths for case in load_queries(path)]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate query ids across query files")
    return cases


def _dataset(
    cases: list[QueryCase],
    query_files: list[Path],
    gold_validation: dict[str, Any],
) -> dict[str, Any]:
    labels: list[str] = []
    for path in query_files:
        try:
            labels.append(str(path.resolve().relative_to(REPO_ROOT)))
        except ValueError:
            labels.append(str(path.resolve()))
    return {
        "query_files": labels,
        "query_sha256": _canonical_sha256([asdict(case) for case in cases]),
        "case_count": len(cases),
        "case_ids": [case.id for case in cases],
        "gold_validation": {
            key: value for key, value in gold_validation.items() if key != "by_case"
        },
        "gold_counts": {
            "entity_ids": sum(len(case.expected_entities) for case in cases),
            "work_ids": sum(len(case.expected_works) for case in cases),
            "manifestation_ids": sum(
                len(case.expected_manifestations) for case in cases
            ),
            "passage_ids": sum(len(case.expected_passages) for case in cases),
            "complete_evidence_sets": sum(len(case.evidence_sets) for case in cases),
            "citation_cases": sum(bool(case.expected_passages) for case in cases),
            "ood_cases": sum(not case.answerable for case in cases),
            "identity_cases": sum(
                bool(case.expected_passage_identities or case.forbidden_passages)
                for case in cases
            ),
        },
    }


class LocalSnapshotCatalog:
    """Identity/citation map for exact gold validation and live trace scoring."""

    def __init__(self) -> None:
        required = (DEFAULT_PASSAGES, DEFAULT_NODES, DEFAULT_CITATIONS, DEFAULT_EDGES)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "local scoring snapshot missing: " + ", ".join(missing)
            )
        self.snapshot_files = {
            "passages": _file_sha256(DEFAULT_PASSAGES),
            "nodes": _file_sha256(DEFAULT_NODES),
            "edges": _file_sha256(DEFAULT_EDGES),
            "citations": _file_sha256(DEFAULT_CITATIONS),
        }
        if DEFAULT_MANIFEST.is_file():
            self.snapshot_files["manifest"] = _file_sha256(DEFAULT_MANIFEST)
        self.snapshot_sha256 = _canonical_sha256(self.snapshot_files)

        self.passages: dict[str, dict[str, Any]] = {}
        with DEFAULT_PASSAGES.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    passage_id = str(row.get("passage_id") or "")
                    if passage_id:
                        self.passages[passage_id] = row

        self.manifestation_ids: set[str] = set()
        with DEFAULT_MANIFEST.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    canonical_id = str(row.get("canonical_id") or "")
                    if canonical_id:
                        self.manifestation_ids.add(canonical_id)

        self.node_types: dict[str, str] = {}
        self.exact_node_passages: dict[str, list[str]] = {}
        with DEFAULT_NODES.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    node_id = str(row.get("node_id") or row.get("id") or "")
                    if node_id:
                        self.node_types[node_id] = str(row.get("type") or "").lower()
                        meta = row.get("metadata") or {}
                        if isinstance(meta, str):
                            meta = json.loads(meta)
                        ids = {
                            str(meta.get(key) or "")
                            for key in (
                                "corpus_passage_id",
                                "db_passage_id",
                                "passage_id",
                            )
                        }
                        ids.discard("")
                        if (
                            self.node_types[node_id] in {"passage", "quote"}
                            and len(ids) == 1
                        ):
                            pid = next(iter(ids))
                            passage = self.passages.get(pid)
                            if passage and meta.get("canonical_ref") == passage.get(
                                "canonical_ref"
                            ):
                                self.exact_node_passages[node_id] = [pid]

        self.node_passages: dict[str, list[str]] = {}
        with DEFAULT_CITATIONS.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("citation_type") == "related_passage_non_exact":
                    continue
                node_id = str(row.get("kg_node_id") or "")
                passage_id = str(row.get("passage_id") or "")
                if node_id and passage_id in self.passages:
                    values = self.node_passages.setdefault(node_id, [])
                    if passage_id not in values:
                        values.append(passage_id)

    def identity(self, passage_id: str) -> dict[str, Any] | None:
        row = self.passages.get(passage_id)
        if row is None:
            return None
        return {
            "passage_id": passage_id,
            "work_canonical_id": row.get("work_canonical_id"),
            "canonical_ref": row.get("canonical_ref"),
            "cts_urn": row.get("cts_urn"),
            "language": row.get("language"),
        }


def validate_gold_against_snapshot(
    cases: list[QueryCase], catalog: LocalSnapshotCatalog
) -> dict[str, Any]:
    """Audit every gold identifier and fail closed for proof-backed cases.

    The 2026-08-24 repair suite carries ``provenance.proof_test`` and is strict:
    any invalid entity/work/manifestation/passage or identity mismatch aborts
    admission. Legacy query debt is preserved as explicit invalid-gold metadata;
    affected channels are not scored and cannot enter release comparisons.
    """

    invalid: list[dict[str, Any]] = []
    by_case: dict[str, dict[str, Any]] = {}

    def check_channel(
        case: QueryCase,
        channel: str,
        values: list[str],
        predicate: Any,
        reason: str,
    ) -> None:
        valid_ids = [value for value in values if predicate(value)]
        invalid_ids = [value for value in values if value not in valid_ids]
        by_case[case.id][channel] = {
            "status": "invalid_gold" if invalid_ids else "valid",
            "valid_ids": valid_ids,
            "invalid_ids": invalid_ids,
        }
        for value in invalid_ids:
            invalid.append(
                {
                    "query_id": case.id,
                    "channel": channel,
                    "id": value,
                    "reason": reason,
                    "strict": bool(case.provenance.get("proof_test")),
                }
            )

    for case in cases:
        by_case[case.id] = {}
        check_channel(
            case,
            "entity",
            case.expected_entities,
            lambda value: (
                value in catalog.node_types and catalog.node_types[value] != "work"
            ),
            "missing KG node or node is a work (wrong gold channel)",
        )
        check_channel(
            case,
            "work",
            case.expected_works,
            lambda value: catalog.node_types.get(value) == "work",
            "missing KG work node or node type is not work",
        )
        check_channel(
            case,
            "manifestation",
            case.expected_manifestations,
            lambda value: value in catalog.manifestation_ids,
            "manifestation absent from data/corpus/manifest.jsonl",
        )

        referenced = _dedup(
            [
                *case.expected_passages,
                *case.expected_passage_identities,
                *(value for group in case.evidence_sets for value in group),
            ]
        )
        check_channel(
            case,
            "passage",
            referenced,
            lambda value: value in catalog.passages,
            "passage absent from data/corpus/passages.jsonl",
        )

        identity_errors: list[str] = []
        for passage_id, expected in case.expected_passage_identities.items():
            actual = catalog.identity(passage_id)
            if actual is None:
                continue
            for key, expected_value in expected.items():
                if str(actual.get(key) or "") != expected_value:
                    identity_errors.append(
                        f"{passage_id}:{key}={actual.get(key)!r}, "
                        f"expected {expected_value!r}"
                    )
        by_case[case.id]["passage_identity"] = {
            "status": "invalid_gold" if identity_errors else "valid",
            "errors": identity_errors,
        }
        for detail in identity_errors:
            invalid.append(
                {
                    "query_id": case.id,
                    "channel": "passage_identity",
                    "id": detail.split(":", 1)[0],
                    "reason": detail,
                    "strict": bool(case.provenance.get("proof_test")),
                }
            )

    strict_invalid = [row for row in invalid if row["strict"]]
    if strict_invalid:
        details = "\n".join(
            f"{row['query_id']} {row['channel']} {row['id']}: {row['reason']}"
            for row in strict_invalid
        )
        raise ValueError("strict gold/snapshot validation failed:\n" + details)

    return {
        "status": "legacy_invalid_gold" if invalid else "valid",
        "invalid_gold_count": len(invalid),
        "invalid_queries": sorted({row["query_id"] for row in invalid}),
        "invalid_gold": invalid,
        "strict_case_count": sum(
            bool(case.provenance.get("proof_test")) for case in cases
        ),
        "by_case": by_case,
    }


def _binding(
    *,
    runner_id: str,
    release_id: str,
    model_id: str | None,
    config_id: str,
    config: dict[str, Any],
    generation_enabled: bool,
    snapshot_sha256: str | None,
    snapshot_files: dict[str, str],
    snapshot_scope: str,
) -> RunBinding:
    if not release_id.strip() or not config_id.strip():
        raise ValueError("release_id and config_id are required")
    if generation_enabled and not (model_id and model_id.strip()):
        raise ValueError("generation-enabled runs require model_id")
    revision, dirty = _git_state()
    return RunBinding(
        runner_id=runner_id,
        release_id=release_id,
        model_id=model_id if generation_enabled else None,
        config_id=config_id,
        config_sha256=_canonical_sha256(config),
        generation_enabled=generation_enabled,
        code_revision=revision,
        code_sha256=_code_sha256(),
        workspace_dirty=dirty,
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        snapshot_sha256=snapshot_sha256,
        snapshot_files=snapshot_files,
        snapshot_scope=snapshot_scope,
    )


def extract_returned_ids(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Legacy mixed-channel extractor kept only for compatibility tests."""

    values: list[str] = []
    for citation in payload.get("citations") or []:
        if isinstance(citation, dict):
            value = citation.get("id")
            if isinstance(value, str) and citation.get("type") in (None, "node"):
                values.append(value)
    for source in payload.get("sources") or []:
        if isinstance(source, dict):
            value = source.get("node_id") or source.get("nodeId")
            if isinstance(value, str):
                values.append(value)
    for field_name in ("context_nodes", "seed_nodes"):
        values.extend(
            value for value in payload.get(field_name) or [] if isinstance(value, str)
        )
    evidence_map = payload.get("evidence_map") or {}
    if isinstance(evidence_map, dict):
        for key, value in evidence_map.items():
            if isinstance(key, str):
                values.append(key)
            if isinstance(value, dict) and isinstance(value.get("node_id"), str):
                values.append(value["node_id"])
    values = _dedup(values)
    works = [value for value in values if value.startswith(("work_", "sc"))]
    return values, works


def extract_predicted_passages(
    payload: dict[str, Any], catalog: LocalSnapshotCatalog | None = None
) -> list[str]:
    citations = payload.get("passage_citations")
    if not isinstance(citations, list):
        citations = payload.get("citations")
    if not isinstance(citations, list):
        citations = []
    values = [
        citation.get("id")
        for citation in citations
        if isinstance(citation, dict)
        and citation.get("type") == "passage"
        and isinstance(citation.get("id"), str)
    ]
    if catalog is not None:
        values = [
            resolved
            for value in values
            for resolved in catalog.exact_node_passages.get(value, [value])
        ]
    return _dedup(values)


def extract_answer_text(payload: dict[str, Any]) -> str:
    answer = payload.get("answer")
    return answer if isinstance(answer, str) else ""


def _retrieved_nodes(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field_name in ("seed_nodes", "context_nodes"):
        values.extend(
            value for value in payload.get(field_name) or [] if isinstance(value, str)
        )
    metadata = payload.get("metadata") or {}
    if isinstance(metadata, dict):
        for field_name in ("retrieved_node_ids", "activated_node_ids"):
            values.extend(
                value
                for value in metadata.get(field_name) or []
                if isinstance(value, str)
            )
    return _dedup(values)


def _passage_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if isinstance(item, str):
            output.append(item)
        elif isinstance(item, dict):
            passage_id = item.get("passage_id") or item.get("id")
            if isinstance(passage_id, str):
                output.append(passage_id)
    return output


def _retrieved_passages(
    payload: dict[str, Any], catalog: LocalSnapshotCatalog
) -> tuple[list[str] | None, list[str]]:
    values: list[str] = []
    provenance: list[str] = []
    observed = False
    for field_name in ("retrieved_passages", "passage_ids"):
        if field_name in payload:
            observed = True
            values.extend(_passage_values(payload.get(field_name)))
            provenance.append(f"payload.{field_name}")
    metadata = payload.get("metadata") or {}
    if isinstance(metadata, dict):
        for field_name in ("retrieved_passages", "passage_ids"):
            if field_name in metadata:
                observed = True
                values.extend(_passage_values(metadata.get(field_name)))
                provenance.append(f"payload.metadata.{field_name}")
    mapped = [
        passage_id
        for node_id in _retrieved_nodes(payload)
        for passage_id in catalog.exact_node_passages.get(node_id, [])
    ]
    if mapped:
        observed = True
        values.extend(mapped)
        provenance.append("context/seed nodes via local snapshot citations")
    return (_dedup(values), provenance) if observed else (None, [])


def safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def compute_query_metrics(
    case: QueryCase,
    returned_entities: list[str],
    returned_works: list[str],
    answer_text: str,
) -> dict[str, float]:
    """Legacy helper; v2 uses nullable gold-set scores."""

    expected = set(case.expected_entities)
    returned = set(returned_entities)
    overlap = expected & returned
    haystack = " ".join(returned_entities + [answer_text]).lower()
    keyword_hits = sum(
        1 for keyword in case.expected_entity_keywords if keyword.lower() in haystack
    )
    return {
        "entity_recall": round(safe_div(len(overlap), len(expected)), 4),
        "entity_precision": round(safe_div(len(overlap), len(returned)), 4),
        "keyword_hit_rate": round(
            safe_div(keyword_hits, len(case.expected_entity_keywords)), 4
        ),
        "work_recall": round(
            safe_div(
                len(set(case.expected_works) & set(returned_works)),
                len(case.expected_works),
            ),
            4,
        ),
    }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, int(round(pct / 100.0 * len(ordered))))
    return ordered[min(rank, len(ordered)) - 1]


def aggregate(results: list[QueryResult]) -> dict[str, Any]:
    """Minimal v1 compatibility aggregate; v2 artifacts use ``summarize``."""

    successes = [result for result in results if result.error is None]
    return {
        "total_queries": len(results),
        "successes": len(successes),
        "failures": len(results) - len(successes),
        "error_rate": round(safe_div(len(results) - len(successes), len(results)), 4),
    }


def _gold(case: QueryCase, validation: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "answerable": case.answerable,
        "expected_entities": case.expected_entities,
        "expected_entity_keywords": case.expected_entity_keywords,
        "expected_works": case.expected_works,
        "expected_manifestations": case.expected_manifestations,
        "expected_passages": case.expected_passages,
        "complete_evidence_sets": case.evidence_sets,
        "expected_passage_identities": case.expected_passage_identities,
        "forbidden_passages": case.forbidden_passages,
        "gold_claims": case.gold_claims,
        "provenance": case.provenance,
        "snapshot_validation": validation,
    }


def _abstention(payload: dict[str, Any]) -> tuple[bool | None, str | None]:
    metadata = payload.get("metadata") or {}
    candidates = (
        ("payload.abstained", payload.get("abstained")),
        ("payload.insufficient_evidence", payload.get("insufficient_evidence")),
        (
            "payload.metadata.abstained",
            metadata.get("abstained") if isinstance(metadata, dict) else None,
        ),
        (
            "payload.metadata.insufficient_evidence",
            metadata.get("insufficient_evidence")
            if isinstance(metadata, dict)
            else None,
        ),
    )
    for source, value in candidates:
        if isinstance(value, bool):
            return value, source
    return None, None


def _abstention_score(
    case: QueryCase, abstained: bool | None, source: str | None
) -> dict[str, Any]:
    if abstained is None:
        return {
            "scored": False,
            "accuracy": None,
            "expected_answerable": case.answerable,
            "abstained": None,
            "signal_source": None,
        }
    correct = (not case.answerable and abstained) or (case.answerable and not abstained)
    return {
        "scored": True,
        "accuracy": 1.0 if correct else 0.0,
        "expected_answerable": case.answerable,
        "abstained": abstained,
        "signal_source": source,
    }


def _scores(
    case: QueryCase,
    *,
    entities: list[str] | None,
    works: list[str] | None,
    manifestations: list[str] | None,
    passages: list[str] | None,
    citations: list[str] | None,
    abstained: bool | None,
    abstention_source: str | None,
    gold_validation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    gold_validation = gold_validation or {
        channel: {"status": "valid", "valid_ids": [], "invalid_ids": []}
        for channel in ("entity", "work", "manifestation", "passage")
    }

    def channel_score(
        predicted: list[str] | None,
        expected: list[str],
        channel: str,
    ) -> dict[str, Any]:
        validation = gold_validation.get(channel) or {}
        invalid_ids = list(validation.get("invalid_ids") or [])
        if invalid_ids:
            return {
                "status": "not_scored_invalid_gold",
                "scored": False,
                "precision": None,
                "recall": None,
                "f1": None,
                "true_positives": None,
                "false_positives": None,
                "false_negatives": None,
                "predicted_count": len(set(predicted))
                if predicted is not None
                else None,
                "gold_count": len(set(expected)),
                "valid_gold_ids": list(validation.get("valid_ids") or []),
                "invalid_gold_ids": invalid_ids,
            }
        score = score_gold_set(predicted, expected).as_dict()
        score["status"] = (
            "scored"
            if score["scored"]
            else "not_scored_unobserved"
            if predicted is None and expected
            else "not_scored_no_gold"
        )
        score["valid_gold_ids"] = list(validation.get("valid_ids") or expected)
        score["invalid_gold_ids"] = []
        return score

    retrieval = {
        "entity": channel_score(entities, case.expected_entities, "entity"),
        "work": channel_score(works, case.expected_works, "work"),
        "manifestation": channel_score(
            manifestations, case.expected_manifestations, "manifestation"
        ),
        "passage": channel_score(passages, case.expected_passages, "passage"),
        "complete_evidence_set": complete_evidence_set_recall(
            passages, case.evidence_sets
        ),
        "forbidden_passage_hits": (
            sorted(set(passages or []) & set(case.forbidden_passages))
            if passages is not None
            else None
        ),
    }
    if (gold_validation.get("passage") or {}).get("invalid_ids"):
        retrieval["complete_evidence_set"] = {
            "status": "not_scored_invalid_gold",
            "scored": False,
            "recall": None,
            "complete_sets": None,
            "required_sets": len(case.evidence_sets),
            "set_hits": None,
            "invalid_gold_ids": list(gold_validation["passage"]["invalid_ids"]),
        }
    else:
        retrieval["complete_evidence_set"]["status"] = (
            "scored"
            if retrieval["complete_evidence_set"]["scored"]
            else "not_scored_unobserved_or_no_gold"
        )
    generation = {
        "citation": channel_score(citations, case.expected_passages, "passage"),
        "abstention": _abstention_score(case, abstained, abstention_source),
    }
    return retrieval, generation


def _not_run_safety() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "observed": False,
            "status": "not_run",
            "failure_count": None,
            "details": [],
        }
        for name in (
            "source_identity",
            "quote_fidelity",
            "publication",
            "forbidden_strings",
        )
    }


def _safety(
    *,
    case: QueryCase,
    payload: dict[str, Any] | None,
    answer: str | None,
    cited_passages: list[str] | None,
    forbidden: list[ForbiddenString],
    catalog: LocalSnapshotCatalog,
) -> dict[str, dict[str, Any]]:
    if payload is None or answer is None or cited_passages is None:
        return _not_run_safety()

    identity_failures: list[dict[str, Any]] = []
    for passage_id in cited_passages:
        identity = catalog.identity(passage_id)
        if identity is None:
            identity_failures.append(
                {"passage_id": passage_id, "reason": "not_in_bound_snapshot"}
            )
            continue
        if passage_id in case.forbidden_passages:
            identity_failures.append(
                {"passage_id": passage_id, "reason": "forbidden_identity"}
            )
        for key, expected in case.expected_passage_identities.get(
            passage_id, {}
        ).items():
            if str(identity.get(key) or "") != expected:
                identity_failures.append(
                    {
                        "passage_id": passage_id,
                        "reason": "identity_mismatch",
                        "field": key,
                        "expected": expected,
                        "actual": identity.get(key),
                    }
                )

    metadata = payload.get("metadata") or {}
    metadata = metadata if isinstance(metadata, dict) else {}
    text_verification = metadata.get("text_verification")
    unsupported_quotes = metadata.get("unsupported_quotes")
    quote_observed = isinstance(text_verification, dict) or isinstance(
        unsupported_quotes, list
    )
    quote_details: list[Any] = []
    if isinstance(text_verification, dict):
        quote_details.extend(text_verification.get("unverified_spans") or [])
        if not quote_details:
            quote_details.extend(text_verification.get("unverified_texts") or [])
    if isinstance(unsupported_quotes, list):
        quote_details.extend(unsupported_quotes)

    publication_gate = metadata.get("publication_gate")
    publication_observed = isinstance(publication_gate, dict)
    publication_status = "not_run"
    publication_failures: list[Any] = []
    if publication_observed:
        publishable = publication_gate.get("publishable") is True
        reasons = publication_gate.get("reasons") or []
        if publishable and not reasons:
            publication_status = "passed"
        elif not publishable and answer == "":
            publication_status = "safely_blocked"
        else:
            publication_status = "failed"
            publication_failures = list(reasons) or ["inconsistent_publication_gate"]

    forbidden_hits = [
        {
            "string": hit.string,
            "node_id": hit.node_id,
            "source_file": hit.source_file,
            "source_line": hit.source_line,
        }
        for hit in find_forbidden_strings(answer, forbidden)
    ]
    return {
        "source_identity": {
            "observed": True,
            "status": "failed" if identity_failures else "passed",
            "failure_count": len(identity_failures),
            "details": identity_failures,
            "scope": (
                "citation ids resolved against bound local snapshot; "
                "gold identity fields checked when supplied"
            ),
        },
        "quote_fidelity": {
            "observed": quote_observed,
            "status": (
                "failed" if quote_details else "passed" if quote_observed else "not_run"
            ),
            "failure_count": len(quote_details) if quote_observed else None,
            "details": quote_details,
        },
        "publication": {
            "observed": publication_observed,
            "status": publication_status,
            "failure_count": (
                len(publication_failures) if publication_observed else None
            ),
            "details": publication_failures,
            "gate": publication_gate if publication_observed else None,
        },
        "forbidden_strings": {
            "observed": True,
            "status": "failed" if forbidden_hits else "passed",
            "failure_count": len(forbidden_hits),
            "details": forbidden_hits,
        },
    }


def _query_gates(
    retrieval_scores: dict[str, Any],
    safety: dict[str, dict[str, Any]],
    citation_evidence: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    complete = retrieval_scores["complete_evidence_set"]
    decisions = [
        {
            "name": "complete_evidence_set",
            "status": (
                "passed"
                if complete["scored"] and complete["recall"] == 1.0
                else "failed"
                if complete["scored"] or complete.get("required_sets", 0)
                else "not_run"
            ),
            "details": complete,
        },
        {
            "name": "forbidden_passages",
            "status": (
                "not_run"
                if retrieval_scores["forbidden_passage_hits"] is None
                else "failed"
                if retrieval_scores["forbidden_passage_hits"]
                else "passed"
            ),
            "details": retrieval_scores["forbidden_passage_hits"],
        },
    ]
    if citation_evidence is not None and citation_evidence.get("required_sets", 0):
        decisions.append(
            {
                "name": "published_complete_evidence_set",
                "status": "passed"
                if citation_evidence.get("recall") == 1.0
                else "failed",
                "details": citation_evidence,
            }
        )
    for channel in ("entity", "work", "manifestation", "passage"):
        score = retrieval_scores[channel]
        invalid_ids = score.get("invalid_gold_ids") or []
        decisions.append(
            {
                "name": f"valid_{channel}_gold",
                "status": "failed" if invalid_ids else "passed",
                "details": invalid_ids,
            }
        )
    for name, result in safety.items():
        status = result["status"]
        decisions.append(
            {
                "name": name,
                "status": "passed" if status == "safely_blocked" else status,
                "details": result["details"],
            }
        )
    return decisions


def _operation_values(
    payload: dict[str, Any],
    total_latency_ms: float,
    *,
    mode: str,
) -> dict[str, Any]:
    metadata = payload.get("metadata") or {}
    metadata = metadata if isinstance(metadata, dict) else {}
    legacy_stages = metadata.get("stage_durations_ms") or {}
    legacy_stages = legacy_stages if isinstance(legacy_stages, dict) else {}

    def number(value: Any) -> float | int | None:
        return (
            value
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )

    stage_metrics: list[dict[str, Any]] = []
    raw_stage_metrics = metadata.get("stage_metrics")
    if isinstance(raw_stage_metrics, list):
        for raw_metric in raw_stage_metrics:
            if not isinstance(raw_metric, dict):
                continue
            stage = str(raw_metric.get("stage") or "").strip()
            duration = number(raw_metric.get("ms", raw_metric.get("duration_ms")))
            if stage and duration is not None:
                stage_metrics.append({"stage": stage, "ms": duration})
    elif legacy_stages:
        stage_metrics = [
            {"stage": str(stage), "ms": duration}
            for stage, raw_duration in legacy_stages.items()
            if (duration := number(raw_duration)) is not None
        ]

    publication = metadata.get("publication_gate")
    publication = publication if isinstance(publication, dict) else {}
    retained = publication.get("publishable")
    retained = retained if isinstance(retained, bool) else None
    reasons = publication.get("reasons") or []
    if not isinstance(reasons, list):
        reasons = [reasons]

    return {
        "retrieval_latency_ms": number(legacy_stages.get("retrieval")),
        "generation_latency_ms": number(legacy_stages.get("generation")),
        "total_latency_ms": round(total_latency_ms, 3),
        "stage_metrics": stage_metrics,
        "input_tokens": number(metadata.get("input_tokens")),
        "output_tokens": number(metadata.get("output_tokens")),
        "total_tokens": number(metadata.get("total_tokens")),
        "estimated_cost_usd": number(metadata.get("total_cost_usd")),
        "cache_hit": (
            bool(payload.get("cached") or metadata.get("cached"))
            if "cached" in payload or "cached" in metadata
            else None
        ),
        "mode": mode,
        "retained": retained,
        "withholding_reasons": [str(reason) for reason in reasons]
        if not retained
        else [],
    }


def _error_result(
    case: QueryCase,
    *,
    error: str,
    total_latency_ms: float | None,
    raw_trace: dict[str, Any],
    gold_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    retrieval_scores, generation_scores = _scores(
        case,
        entities=None,
        works=None,
        manifestations=None,
        passages=None,
        citations=None,
        abstained=None,
        abstention_source=None,
        gold_validation=gold_validation,
    )
    safety = _not_run_safety()
    gates = _query_gates(retrieval_scores, safety)
    return {
        "id": case.id,
        "query": case.query,
        "query_type": case.query_type,
        "difficulty": case.difficulty,
        "strata": case.all_strata,
        "gold": _gold(case, gold_validation),
        "status": "error",
        "retrieval": {
            "observed": False,
            "method": None,
            "returned": {
                "entities": None,
                "works": None,
                "manifestations": None,
                "passages": None,
            },
            "scores": retrieval_scores,
            "trace_provenance": [],
        },
        "generation": {
            "observed": False,
            "answer": None,
            "cited_passages": None,
            "scores": generation_scores,
            "safety": safety,
            "judge": None,
        },
        "operations": {
            "retrieval_latency_ms": None,
            "generation_latency_ms": None,
            "total_latency_ms": total_latency_ms,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
            "cache_hit": None,
        },
        "gates": gates,
        "gate_failures": [
            decision["name"] for decision in gates if decision["status"] == "failed"
        ],
        "error": error,
        "raw_trace": raw_trace,
    }


def _http_capture(
    client: Any,
    base_url: str,
    case: QueryCase,
    *,
    mode: str,
    model: str | None = None,
) -> tuple[dict[str, Any] | None, float, dict[str, Any], str | None]:
    url = base_url.rstrip("/") + STREAM_QUERY_PATH
    request_params = {
        "question": case.query,
        "mode": mode,
        "force_refresh": "true",
    }
    if model:
        request_params["model"] = model
    request_trace = {"method": "GET", "url": url, "params": request_params}
    started = time.perf_counter()
    try:
        with client.stream(
            "GET",
            url,
            params=request_params,
            timeout=DEFAULT_TIMEOUT,
        ) as response:
            status_code = response.status_code
            response_headers = {
                key.lower(): value
                for key, value in response.headers.items()
                if key.lower() in SAFE_RESPONSE_HEADERS
            }
            if status_code < 200 or status_code >= 300:
                body = response.read().decode("utf-8", errors="replace")
                try:
                    parsed_error = json.loads(body)
                except json.JSONDecodeError, ValueError:
                    parsed_error = None
                error_payload = parsed_error if isinstance(parsed_error, dict) else None
                elapsed = round((time.perf_counter() - started) * 1000.0, 3)
                trace = {
                    "kind": "live-http-sse",
                    "request": request_trace,
                    "response": {
                        "status_code": status_code,
                        "headers": response_headers,
                        "body": body,
                        "json": parsed_error,
                        "sse_events": [],
                    },
                    "transport_error": None,
                }
                return (
                    error_payload,
                    elapsed,
                    trace,
                    f"HTTP {status_code}: {body[:500]}",
                )

            body_lines: list[str] = []
            events: list[dict[str, Any]] = []
            stage_metrics: list[dict[str, Any]] = []
            payload: dict[str, Any] | None = None
            cost_summary: dict[str, Any] = {}
            cache_hit = False
            stream_error: str | None = None
            retrieved_nodes: list[str] = []
            retrieved_passages: list[str] = []
            retrieval_observed = False
            for line in response.iter_lines():
                body_lines.append(line)
                if not line.startswith("data:"):
                    continue
                raw_event = line.removeprefix("data:").strip()
                try:
                    event = json.loads(raw_event)
                except json.JSONDecodeError, ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                events.append(event)
                event_type = str(event.get("type") or "")
                raw_event_data = event.get("data")
                event_data = (
                    raw_event_data if isinstance(raw_event_data, dict) else event
                )
                if event_type == "stage_complete":
                    stage = str(event_data.get("stage") or event.get("stage") or "")
                    duration = event_data.get(
                        "duration_ms",
                        event.get("duration_ms"),
                    )
                    if stage and isinstance(duration, (int, float)):
                        stage_metrics.append({"stage": stage, "ms": duration})
                elif event_type == "tool_result" and event_data.get("tool_call_id"):
                    retrieval_observed = True
                    retrieved_nodes.extend(
                        _passage_values(event_data.get("nodes_touched"))
                    )
                    retrieved_passages.extend(
                        _passage_values(event_data.get("passages_touched"))
                    )
                elif event_type == "cost_summary":
                    cost_summary = event_data
                elif event_type == "cache_hit":
                    cache_hit = True
                elif event_type == "complete" and isinstance(event.get("data"), dict):
                    payload = dict(event["data"])
                elif event_type == "error":
                    stream_error = str(
                        event.get("message")
                        or event_data.get("message")
                        or "stream error"
                    )

            elapsed = round((time.perf_counter() - started) * 1000.0, 3)
            body = "\n".join(body_lines)
            if payload is not None:
                metadata = payload.get("metadata")
                metadata = dict(metadata) if isinstance(metadata, dict) else {}
                metadata["stage_metrics"] = stage_metrics
                if retrieval_observed:
                    metadata["retrieved_node_ids"] = _dedup(
                        [
                            *metadata.get("retrieved_node_ids", []),
                            *retrieved_nodes,
                        ]
                    )
                    metadata["retrieved_passages"] = _dedup(retrieved_passages)
                for key in ("total_tokens", "total_cost_usd"):
                    if isinstance(cost_summary.get(key), (int, float)):
                        metadata[key] = cost_summary[key]
                payload["metadata"] = metadata
                payload["cached"] = cache_hit or metadata.get("cached") is True
            trace = {
                "kind": "live-http-sse",
                "request": request_trace,
                "response": {
                    "status_code": status_code,
                    "headers": response_headers,
                    "body": body,
                    "json": payload,
                    "sse_events": events,
                },
                "transport_error": None,
            }
    except Exception as exc:  # noqa: BLE001
        elapsed = round((time.perf_counter() - started) * 1000.0, 3)
        return (
            None,
            elapsed,
            {
                "kind": "live-http-sse",
                "request": request_trace,
                "response": None,
                "transport_error": f"{type(exc).__name__}: {exc}",
            },
            f"{type(exc).__name__}: {exc}",
        )

    if stream_error is not None:
        return payload, elapsed, trace, stream_error
    if payload is None:
        return None, elapsed, trace, "stream did not emit a complete payload"
    return payload, elapsed, trace, None


def _new_document(
    *, binding: RunBinding, dataset: dict[str, Any], results: list[dict[str, Any]]
) -> dict[str, Any]:
    captured_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run_material = {
        "captured_at": captured_at,
        "binding": asdict(binding),
        "dataset": dataset,
    }
    document = {
        "artifact_type": "eleutheria.graphrag.eval_run",
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": f"eval-{captured_at[:10]}-{_canonical_sha256(run_material)[:12]}",
        "captured_at": captured_at,
        "binding": asdict(binding),
        "dataset": dataset,
        "summary": summarize(results),
        "results": results,
    }
    validate_run_document(document)
    return document


def run(
    base_url: str,
    cases: list[QueryCase],
    *,
    release_id: str | None = None,
    model_id: str | None = None,
    config_id: str | None = None,
    mode: str = "fast",
    query_files: list[Path] | None = None,
    verbose: bool = True,
    strict: bool = False,
) -> dict[str, Any]:
    """Execute the live backend; release/model/config binding is mandatory."""

    if httpx is None:
        raise RuntimeError("httpx is required for live-http")
    if not release_id or not model_id or not config_id:
        raise ValueError("live runs require release_id, model_id, and config_id")
    query_files = query_files or [Path(__file__).parent / "queries.yaml"]
    catalog = LocalSnapshotCatalog()
    gold_validation = validate_gold_against_snapshot(cases, catalog)
    if strict and gold_validation.get("invalid_gold_count", 0):
        raise ValueError(
            f"Invalid gold: {gold_validation['invalid_gold_count']} unresolved identifiers. "
            "No live query was sent; repair the gold references before evaluation."
        )
    config = {
        "endpoint": STREAM_QUERY_PATH,
        "base_url": base_url,
        "mode": mode,
        "requested_model": model_id,
        "timeout_seconds": DEFAULT_TIMEOUT,
        "stream": True,
        "force_refresh": True,
    }
    binding = _binding(
        runner_id="live-http-v2",
        release_id=release_id,
        model_id=model_id,
        config_id=config_id,
        config=config,
        generation_enabled=True,
        snapshot_sha256=catalog.snapshot_sha256,
        snapshot_files=catalog.snapshot_files,
        snapshot_scope=(
            "local gold-resolution snapshot; release_id must identify the "
            "backend's matching frozen deployment"
        ),
    )
    try:
        forbidden = load_forbidden_strings()
    except FileNotFoundError:
        forbidden = []

    results: list[dict[str, Any]] = []
    from cli.graphrag_client import auth_headers

    with httpx.Client(headers=auth_headers(base_url)) as client:
        for position, case in enumerate(cases, start=1):
            if verbose:
                print(
                    f"[{position}/{len(cases)}] {case.id}: {case.query[:80]}",
                    flush=True,
                )
            payload, elapsed, raw_trace, error = _http_capture(
                client, base_url, case, mode=mode, model=model_id
            )
            if error or payload is None:
                results.append(
                    _error_result(
                        case,
                        error=error or "missing payload",
                        total_latency_ms=elapsed,
                        raw_trace=raw_trace,
                        gold_validation=gold_validation["by_case"][case.id],
                    )
                )
                continue

            retrieved_nodes = _retrieved_nodes(payload)
            works = [
                node_id
                for node_id in retrieved_nodes
                if catalog.node_types.get(node_id) == "work"
                or node_id.startswith("work_")
            ]
            entities = [node_id for node_id in retrieved_nodes if node_id not in works]
            passages, provenance = _retrieved_passages(payload, catalog)
            manifestations: list[str] = []
            for passage_id in passages or []:
                identity = catalog.identity(passage_id)
                manifestation_id = str((identity or {}).get("work_canonical_id") or "")
                if manifestation_id:
                    manifestations.append(manifestation_id)
            works = _dedup(works)
            manifestations = _dedup(manifestations)
            answer = extract_answer_text(payload)
            citations = extract_predicted_passages(payload, catalog)
            abstained, abstention_source = _abstention(payload)
            retrieval_scores, generation_scores = _scores(
                case,
                entities=entities,
                works=works,
                manifestations=manifestations,
                passages=passages,
                citations=citations,
                abstained=abstained,
                abstention_source=abstention_source,
                gold_validation=gold_validation["by_case"][case.id],
            )
            safety = _safety(
                case=case,
                payload=payload,
                answer=answer,
                cited_passages=citations,
                forbidden=forbidden,
                catalog=catalog,
            )
            gates = _query_gates(
                retrieval_scores,
                safety,
                complete_evidence_set_recall(citations, case.evidence_sets),
            )
            results.append(
                {
                    "id": case.id,
                    "query": case.query,
                    "query_type": case.query_type,
                    "difficulty": case.difficulty,
                    "strata": case.all_strata,
                    "gold": _gold(case, gold_validation["by_case"][case.id]),
                    "status": "ok",
                    "retrieval": {
                        "observed": True,
                        "method": "live-http response trace",
                        "returned": {
                            "entities": entities,
                            "works": works,
                            "manifestations": manifestations,
                            "passages": passages,
                        },
                        "scores": retrieval_scores,
                        "trace_provenance": provenance,
                    },
                    "generation": {
                        "observed": True,
                        "answer": answer,
                        "cited_passages": citations,
                        "scores": generation_scores,
                        "safety": safety,
                        "judge": None,
                    },
                    "operations": _operation_values(
                        payload,
                        elapsed,
                        mode=mode,
                    ),
                    "gates": gates,
                    "gate_failures": [
                        decision["name"]
                        for decision in gates
                        if decision["status"] == "failed"
                    ],
                    "error": None,
                    "raw_trace": raw_trace,
                }
            )
    return _new_document(
        binding=binding,
        dataset=_dataset(cases, query_files, gold_validation),
        results=results,
    )


def run_snapshot(
    cases: list[QueryCase],
    *,
    strategy: str,
    passage_k: int = 12,
    node_k: int = 30,
    seed_k: int = 5,
    query_files: list[Path] | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run retrieval only; generation/citation/abstention stay null/not-run."""

    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"unsupported strategy {strategy!r}")
    query_files = query_files or [Path(__file__).parent / "queries.yaml"]
    catalog = LocalSnapshotCatalog()
    gold_validation = validate_gold_against_snapshot(cases, catalog)
    index = SnapshotIndex()
    if catalog.snapshot_sha256 != _canonical_sha256(index.file_hashes):
        raise RuntimeError("snapshot hash disagreement between catalog and runner")
    config = {
        "strategy": strategy,
        "passage_k": passage_k,
        "node_k": node_k,
        "seed_k": seed_k,
        "passage_ranker": "Okapi BM25 + reciprocal-rank fusion",
        "node_ranker": "accent-folded lexical overlap",
        "fusion": {
            "rrf_constant": 60,
            "lexical_reservation": "max(1, passage_k // 2)",
            "purpose": "retain exact identity matches while fusing graph evidence",
        },
        "latency_budget": {
            "scope": "post-index, per-query offline snapshot retrieval",
            "p95_ms": 75.0,
            "max_ms": 150.0,
            "enforcement": "report_only; no flaky wall-clock CI assertion",
        },
        "evidence_policy": {
            "mode": "central_fail_closed",
            "policy_sha256": index.citability_policy_sha256,
            "excluded_passage_count": len(index.passage_exclusions),
            "non_citable_node_count": len(index.non_citable_nodes),
        },
        "graph": {
            "enabled": strategy.startswith("snapshot-ppr-"),
            "algorithm": "directed personalized PageRank",
            "edge_scope": "asserted rows present in data/kg/edges.jsonl only",
            "adjacency_mode": (
                "asserted_bidirectional"
                if strategy == "snapshot-ppr-bidirectional"
                else "asserted_directed"
                if strategy == "snapshot-ppr-directed"
                else None
            ),
            "direction": (
                "source to target, plus target to source traversal access"
                if strategy == "snapshot-ppr-bidirectional"
                else "source to target"
            ),
            "inverse_policy": (
                "no inferred inverse relation; bidirectional adjacency reuses the "
                "same asserted row"
            ),
            "alpha": 0.15 if strategy.startswith("snapshot-ppr-") else None,
            "iterations": 20 if strategy.startswith("snapshot-ppr-") else None,
        },
    }
    binding = _binding(
        runner_id=f"{strategy}-v2",
        release_id=f"snapshot:{index.snapshot_sha256[:16]}",
        model_id=None,
        config_id=f"{strategy}-v2-k{passage_k}-n{node_k}-s{seed_k}",
        config=config,
        generation_enabled=False,
        snapshot_sha256=index.snapshot_sha256,
        snapshot_files=index.file_hashes,
        snapshot_scope="local corpus/KG exports used directly by the runner",
    )

    results: list[dict[str, Any]] = []
    for position, case in enumerate(cases, start=1):
        if verbose:
            print(
                f"[{position}/{len(cases)}] {case.id}: {case.query[:80]}",
                flush=True,
            )
        try:
            retrieved = index.retrieve(
                case.query,
                strategy=strategy,
                passage_k=passage_k,
                node_k=node_k,
                seed_k=seed_k,
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                _error_result(
                    case,
                    error=f"{type(exc).__name__}: {exc}",
                    total_latency_ms=None,
                    raw_trace={
                        "kind": "snapshot-retrieval",
                        "strategy": strategy,
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                    gold_validation=gold_validation["by_case"][case.id],
                )
            )
            continue

        retrieval_scores, generation_scores = _scores(
            case,
            entities=retrieved.entity_ids,
            works=retrieved.work_ids,
            manifestations=retrieved.manifestation_ids,
            passages=retrieved.passage_ids,
            citations=None,
            abstained=None,
            abstention_source=None,
            gold_validation=gold_validation["by_case"][case.id],
        )
        safety = _not_run_safety()
        gates = _query_gates(retrieval_scores, safety)
        results.append(
            {
                "id": case.id,
                "query": case.query,
                "query_type": case.query_type,
                "difficulty": case.difficulty,
                "strata": case.all_strata,
                "gold": _gold(case, gold_validation["by_case"][case.id]),
                "status": "ok",
                "retrieval": {
                    "observed": True,
                    "method": strategy,
                    "returned": {
                        "entities": retrieved.entity_ids,
                        "works": retrieved.work_ids,
                        "manifestations": retrieved.manifestation_ids,
                        "passages": retrieved.passage_ids,
                    },
                    "scores": retrieval_scores,
                    "trace_provenance": ["direct checked-out snapshots"],
                },
                "generation": {
                    "observed": False,
                    "answer": None,
                    "cited_passages": None,
                    "scores": generation_scores,
                    "safety": safety,
                    "judge": None,
                },
                "operations": {
                    "retrieval_latency_ms": retrieved.latency_ms,
                    "generation_latency_ms": None,
                    "total_latency_ms": retrieved.latency_ms,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "estimated_cost_usd": None,
                    "cache_hit": None,
                },
                "gates": gates,
                "gate_failures": [
                    decision["name"]
                    for decision in gates
                    if decision["status"] == "failed"
                ],
                "error": None,
                "raw_trace": {
                    "kind": "snapshot-retrieval",
                    "snapshot_sha256": index.snapshot_sha256,
                    **retrieved.trace,
                },
            }
        )
    return _new_document(
        binding=binding,
        dataset=_dataset(cases, query_files, gold_validation),
        results=results,
    )


def _mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 4) if values else None


def _score_summary(
    results: list[dict[str, Any]], section: str, channel: str
) -> dict[str, Any]:
    all_scores = [result[section]["scores"][channel] for result in results]
    scores = [score for score in all_scores if score.get("scored")]
    invalid_results = [
        result
        for result in results
        if result[section]["scores"][channel].get("status") == "not_scored_invalid_gold"
    ]
    summary = {
        "scored_queries": len(scores),
        "precision_mean": _mean(
            [
                float(score["precision"])
                for score in scores
                if score.get("precision") is not None
            ]
        ),
        "recall_mean": _mean(
            [
                float(score["recall"])
                for score in scores
                if score.get("recall") is not None
            ]
        ),
        "f1_mean": _mean(
            [float(score["f1"]) for score in scores if score.get("f1") is not None]
        ),
        "metric_population": "fully_valid_gold_cases_only",
        "invalid_gold_queries": [result["id"] for result in invalid_results],
        "invalid_gold_count": sum(
            len(result[section]["scores"][channel].get("invalid_gold_ids") or [])
            for result in invalid_results
        ),
    }
    summary["precision_mean_valid_subset"] = summary["precision_mean"]
    summary["recall_mean_valid_subset"] = summary["recall_mean"]
    summary["f1_mean_valid_subset"] = summary["f1_mean"]
    return summary


def _summary_core(results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [result for result in results if result["status"] == "error"]
    invalid_gold_rows = [
        {
            "query_id": result["id"],
            "channel": channel,
            "invalid_ids": validation.get("invalid_ids") or [],
        }
        for result in results
        for channel, validation in (
            result["gold"].get("snapshot_validation") or {}
        ).items()
        if isinstance(validation, dict) and validation.get("invalid_ids")
    ]
    complete_scores = [
        float(result["retrieval"]["scores"]["complete_evidence_set"]["recall"])
        for result in results
        if result["retrieval"]["scores"]["complete_evidence_set"]["scored"]
    ]
    abstention_scores = [
        float(result["generation"]["scores"]["abstention"]["accuracy"])
        for result in results
        if result["generation"]["scores"]["abstention"]["scored"]
    ]
    ood_scores = [
        float(result["generation"]["scores"]["abstention"]["accuracy"])
        for result in results
        if not result["gold"]["answerable"]
        and result["generation"]["scores"]["abstention"]["scored"]
    ]

    safety_summary: dict[str, Any] = {}
    for channel in (
        "source_identity",
        "quote_fidelity",
        "publication",
        "forbidden_strings",
    ):
        observed = [
            result
            for result in results
            if result["generation"]["safety"][channel]["observed"]
        ]
        safety_summary[channel] = {
            "observed_queries": len(observed),
            "failure_count": sum(
                int(result["generation"]["safety"][channel]["failure_count"] or 0)
                for result in observed
            ),
            "failed_queries": [
                result["id"]
                for result in observed
                if result["generation"]["safety"][channel]["status"] == "failed"
            ],
            "status_counts": {
                status: sum(
                    result["generation"]["safety"][channel]["status"] == status
                    for result in observed
                )
                for status in ("passed", "failed", "safely_blocked")
            },
        }

    operations: dict[str, Any] = {}
    for channel in (
        "retrieval_latency_ms",
        "generation_latency_ms",
        "total_latency_ms",
    ):
        values = [
            float(result["operations"][channel])
            for result in results
            if isinstance(result["operations"][channel], (int, float))
        ]
        operations[channel.removesuffix("_ms")] = {
            "observed_queries": len(values),
            "p50_ms": round(percentile(values, 50) or 0.0, 3) if values else None,
            "p95_ms": round(percentile(values, 95) or 0.0, 3) if values else None,
            "max_ms": round(max(values), 3) if values else None,
        }
    for channel in ("input_tokens", "output_tokens", "total_tokens"):
        values = [
            float(result["operations"][channel])
            for result in results
            if isinstance(result["operations"][channel], (int, float))
        ]
        operations[channel] = {
            "observed_queries": len(values),
            "sum": int(sum(values)) if values else None,
        }
    costs = [
        float(result["operations"]["estimated_cost_usd"])
        for result in results
        if isinstance(result["operations"]["estimated_cost_usd"], (int, float))
    ]
    operations["estimated_cost_usd"] = {
        "observed_queries": len(costs),
        "sum": round(sum(costs), 8) if costs else None,
        "p50": round(percentile(costs, 50) or 0.0, 8) if costs else None,
        "mean": round(statistics.mean(costs), 8) if costs else None,
        "max": round(max(costs), 8) if costs else None,
    }

    stage_values: defaultdict[str, list[float]] = defaultdict(list)
    for result in results:
        result_operations = result["operations"]
        per_query: defaultdict[str, float] = defaultdict(float)
        raw_metrics = result_operations.get("stage_metrics")
        if isinstance(raw_metrics, list):
            for raw_metric in raw_metrics:
                if not isinstance(raw_metric, dict):
                    continue
                stage = str(raw_metric.get("stage") or "").strip()
                duration = raw_metric.get("ms")
                if (
                    stage
                    and isinstance(duration, (int, float))
                    and not isinstance(duration, bool)
                ):
                    per_query[stage] += float(duration)
        if not per_query:
            for stage, field in (
                ("retrieval", "retrieval_latency_ms"),
                ("generation", "generation_latency_ms"),
            ):
                duration = result_operations.get(field)
                if isinstance(duration, (int, float)) and not isinstance(
                    duration, bool
                ):
                    per_query[stage] = float(duration)
        for stage, duration in per_query.items():
            stage_values[stage].append(duration)
    operations["stage_latency"] = {
        stage: {
            "observed_queries": len(values),
            "p50_ms": round(percentile(values, 50) or 0.0, 3),
            "p95_ms": round(percentile(values, 95) or 0.0, 3),
            "max_ms": round(max(values), 3),
        }
        for stage, values in sorted(stage_values.items())
    }

    def retention_summary(subset: list[dict[str, Any]]) -> dict[str, Any]:
        observed = [
            result
            for result in subset
            if isinstance(result["operations"].get("retained"), bool)
        ]
        retained = sum(result["operations"]["retained"] is True for result in observed)
        withheld = len(observed) - retained
        reasons = Counter(
            reason
            for result in observed
            if result["operations"]["retained"] is False
            for reason in result["operations"].get("withholding_reasons", [])
        )
        return {
            "observed_queries": len(observed),
            "retained": retained,
            "withheld": withheld,
            "retention_rate": round(safe_div(retained, len(observed)), 4),
            "withheld_rate": round(safe_div(withheld, len(observed)), 4),
            "withholding_reasons": dict(sorted(reasons.items())),
        }

    retention_modes = sorted(
        {
            str(result["operations"].get("mode") or "unknown")
            for result in results
            if isinstance(result["operations"].get("retained"), bool)
        }
    )
    retention = {
        **retention_summary(results),
        "by_mode": {
            mode: retention_summary(
                [
                    result
                    for result in results
                    if str(result["operations"].get("mode") or "unknown") == mode
                ]
            )
            for mode in retention_modes
        },
    }

    return {
        "counts": {
            "total_queries": len(results),
            "successes": len(results) - len(failures),
            "failures": len(failures),
            "error_rate": round(safe_div(len(failures), len(results)), 4),
            "failed_queries": [result["id"] for result in failures],
        },
        "gold_validation": {
            "status": "invalid_gold" if invalid_gold_rows else "valid",
            "invalid_gold_count": sum(
                len(row["invalid_ids"]) for row in invalid_gold_rows
            ),
            "invalid_queries": sorted({row["query_id"] for row in invalid_gold_rows}),
            "invalid_channels": invalid_gold_rows,
            "release_comparable": not invalid_gold_rows,
        },
        "retrieval": {
            "entity": _score_summary(results, "retrieval", "entity"),
            "work": _score_summary(results, "retrieval", "work"),
            "manifestation": _score_summary(results, "retrieval", "manifestation"),
            "passage": _score_summary(results, "retrieval", "passage"),
            "complete_evidence_set": {
                "scored_queries": len(complete_scores),
                "recall_mean": _mean(complete_scores),
                "failed_queries": [
                    result["id"]
                    for result in results
                    if result["retrieval"]["scores"]["complete_evidence_set"]["scored"]
                    and result["retrieval"]["scores"]["complete_evidence_set"]["recall"]
                    < 1.0
                ],
            },
            "forbidden_passages": {
                "observed_queries": sum(
                    result["retrieval"]["scores"]["forbidden_passage_hits"] is not None
                    for result in results
                ),
                "failure_count": sum(
                    len(result["retrieval"]["scores"]["forbidden_passage_hits"] or [])
                    for result in results
                ),
                "failed_queries": [
                    result["id"]
                    for result in results
                    if result["retrieval"]["scores"]["forbidden_passage_hits"]
                ],
            },
        },
        "generation": {
            "citation": _score_summary(results, "generation", "citation"),
            "abstention": {
                "scored_queries": len(abstention_scores),
                "accuracy": _mean(abstention_scores),
                "ood_scored_queries": len(ood_scores),
                "ood_recall": _mean(ood_scores),
                "unobserved_queries": [
                    result["id"]
                    for result in results
                    if not result["generation"]["scores"]["abstention"]["scored"]
                ],
            },
        },
        "safety": safety_summary,
        "retention": retention,
        "operations": operations,
        "gate_failures": [
            {"query_id": result["id"], "gates": result["gate_failures"]}
            for result in results
            if result["gate_failures"]
        ],
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summary_core(results)
    strata = sorted({stratum for result in results for stratum in result["strata"]})
    summary["by_stratum"] = {
        stratum: _summary_core(
            [result for result in results if stratum in result["strata"]]
        )
        for stratum in strata
    }
    return summary


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    report = compare_with_gates(baseline, candidate)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def _print_summary(document: dict[str, Any]) -> None:
    summary = document["summary"]
    counts = summary["counts"]
    print("\nEVAL V2 SUMMARY (no composite score)")
    print(f"  run_id                    : {document['run_id']}")
    print(
        f"  successes / total         : {counts['successes']} / "
        f"{counts['total_queries']}"
    )
    print(f"  error rate                : {counts['error_rate']:.2%}")
    validation = summary["gold_validation"]
    print(
        f"  gold validation           : {validation['status']} "
        f"({validation['invalid_gold_count']} invalid ids; "
        f"release comparable={validation['release_comparable']})"
    )
    for channel in ("entity", "work", "manifestation", "passage"):
        metric = summary["retrieval"][channel]
        print(
            f"  valid-gold {channel:<11} recall: {metric['recall_mean']} "
            f"({metric['scored_queries']} scored)"
        )
    complete = summary["retrieval"]["complete_evidence_set"]
    print(
        "  complete evidence recall  : "
        f"{complete['recall_mean']} ({complete['scored_queries']} scored)"
    )
    citation = summary["generation"]["citation"]
    print(
        f"  generation citation recall: {citation['recall_mean']} "
        f"({citation['scored_queries']} scored)"
    )
    print(
        "  latency total p50 / p95 ms: "
        f"{summary['operations']['total_latency']['p50_ms']} / "
        f"{summary['operations']['total_latency']['p95_ms']}"
    )
    for channel, values in summary["safety"].items():
        print(
            f"  safety {channel:<16}: {values['failure_count']} failures / "
            f"{values['observed_queries']} observed"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runner",
        choices=["live-http", *sorted(SUPPORTED_STRATEGIES)],
        default="snapshot-lexical",
    )
    parser.add_argument(
        "--queries",
        action="append",
        type=Path,
        help="Query YAML (repeatable; default tests/eval/queries.yaml).",
    )
    parser.add_argument("--include-ood", action="store_true")
    parser.add_argument("--include-repair-wave", action="store_true")
    parser.add_argument("--filter-type")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return failure for invalid gold, query/gate failures or missing generation safety coverage.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--release-id")
    parser.add_argument("--model-id")
    parser.add_argument("--config-id")
    parser.add_argument("--mode", choices=["fast", "deep"], default="fast")
    parser.add_argument("--passage-k", type=int, default=12)
    parser.add_argument("--node-k", type=int, default=30)
    parser.add_argument("--seed-k", type=int, default=5)
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "CANDIDATE"),
        help="Validate and compare two v2 artifacts with deterministic gates.",
    )
    parser.add_argument("--comparison-output", type=Path)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args(argv)

    if args.validate:
        document = json.loads(args.validate.read_text(encoding="utf-8"))
        validate_run_document(document)
        print(f"valid eval run: {document['run_id']}")
        return 0

    if args.compare:
        baseline = json.loads(Path(args.compare[0]).read_text(encoding="utf-8"))
        candidate = json.loads(Path(args.compare[1]).read_text(encoding="utf-8"))
        report = compare(baseline, candidate)
        if args.comparison_output:
            args.comparison_output.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        return 0 if report["release_gate"] == "pass" else 1

    query_files = args.queries or [Path(__file__).parent / "queries.yaml"]
    if args.include_ood:
        query_files.append(Path(__file__).parent / "ood_queries.yaml")
    if args.include_repair_wave:
        query_files.append(Path(__file__).parent / "repair_wave_2026_08_24.yaml")
    cases = load_query_files(query_files)
    if args.filter_type:
        cases = [case for case in cases if case.query_type == args.filter_type]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("No queries selected.", file=sys.stderr)
        return 2

    if args.runner == "live-http":
        if not args.release_id or not args.model_id or not args.config_id:
            parser.error("live-http requires --release-id, --model-id and --config-id")
        try:
            document = run(
                args.base_url,
                cases,
                release_id=args.release_id,
                model_id=args.model_id,
                config_id=args.config_id,
                mode=args.mode,
                query_files=query_files,
                verbose=not args.quiet,
                strict=args.strict,
            )
        except ValueError as exc:
            parser.error(str(exc))
    else:
        document = run_snapshot(
            cases,
            strategy=args.runner,
            passage_k=args.passage_k,
            node_k=args.node_k,
            seed_k=args.seed_k,
            query_files=query_files,
            verbose=not args.quiet,
        )

    _print_summary(document)
    if args.output:
        from cli.graphrag_client import write_json

        write_json(args.output, document)
        print(f"Wrote {args.output}")
    if args.strict:
        # Reuse the named release/coverage gates, without inventing a composite
        # score. Comparing a run to itself checks validity and observed safety;
        # the per-query gates additionally require its actual gold evidence.
        passed = (
            compare(document, document)["release_gate"] == "pass"
            and document["summary"]["counts"]["failures"] == 0
            and not document["summary"]["gate_failures"]
        )
        print(f"Strict quality gates: {'PASS' if passed else 'FAIL'}")
        return 0 if passed else 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Evaluation cancelled.", file=sys.stderr)
        raise SystemExit(130) from None
