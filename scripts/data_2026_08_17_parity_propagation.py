#!/usr/bin/env python3
"""Audited data selection for KG -> corpus locus-parity propagation.

This module contains the family-level decisions and derives the row plan from
the frozen 2026-08-17 repository state.  It does not write any file.  The
companion applier rechecks every derived precondition before changing locus
metadata in ``data/corpus/passages.jsonl``.

The selection is deliberately narrow:

* TLG E locus remaps recorded by the primary-wave changelog (Sextus and
  Epictetus);
* Augustine URN normalisations recorded by the primary-wave changelog;
* Augustine, De libero arbitrio URNs whose KG primary-text twins are the
  explicitly adjudicated source of truth;
* the stamped Origen/Clement and Tertullian reattributions.

Unstamped historical formatting differences and missing twins are not selected.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

STAMP = "parity_propagation_2026_08_17"
BACKUP_SUFFIX = ".bak-parity_prop"

BASELINE_FILE_SHA256 = {
    "kg/nodes.jsonl": "1a9eac1d14bb1a114b817d3ea1cb56f58c10c9a579f21f17dfd434b54e157139",
    "corpus/passages.jsonl": "02c156547569563d21a752e0e21d5324b4ba7c9e48ca16946b5e8a83f1dd5e5b",
    "corpus/citations.jsonl": "7fef4a4041e3a548686800248cf74beef5643b61d7c6a9de9119d1a0000f9231",
}

# Filled from the deterministic in-memory rewrite and checked by the applier.
APPLIED_PASSAGES_SHA256 = (
    "2252296708f07b8cad68cd4a3517d52416586afd84ca25c7c1356028588bbd01"
)

EXPECTED_BEFORE = {
    "declared_twins": 11011,
    "shared_twins": 10933,
    "violations": 4535,
    "missing_twins": 78,
    "missing_citations": 0,
    "canonical_ref_mismatches": 1817,
    "cts_urn_mismatches": 2640,
}

EXPECTED_AFTER = {
    "declared_twins": 11011,
    "shared_twins": 10933,
    "violations": 3051,
    "missing_twins": 78,
    "missing_citations": 0,
    "canonical_ref_mismatches": 1145,
    "cts_urn_mismatches": 1828,
}

EXPECTED_FAMILY_ROWS = {
    "sextus_tlge_locus": 532,
    "epictetus_tlge_locus": 45,
    "epictetus_unresolved_urn_defake": 1,
    "augustine_de_libero_arbitrio": 93,
    "augustine_de_gratia_urn": 25,
    "augustine_de_correptione_urn": 21,
    "origen_exhortatio": 51,
    "tertullian_reattributions": 44,
}

EXPECTED_REPAIR_ROWS = 812
EXPECTED_FIXED_VIOLATIONS = 1484
EXPECTED_FIELD_CHANGES = {
    "canonical_ref": 672,
    "cts_urn": 812,
    "work_canonical_id_removed": 44,
}

FAMILY_FIELDS = {
    "sextus_tlge_locus": ("canonical_ref", "cts_urn"),
    "epictetus_tlge_locus": ("canonical_ref", "cts_urn"),
    "epictetus_unresolved_urn_defake": ("cts_urn",),
    "augustine_de_libero_arbitrio": ("cts_urn",),
    "augustine_de_gratia_urn": ("cts_urn",),
    "augustine_de_correptione_urn": ("cts_urn",),
    "origen_exhortatio": ("canonical_ref", "cts_urn"),
    "tertullian_reattributions": (
        "canonical_ref",
        "cts_urn",
        "work_canonical_id",
    ),
}

FAMILY_EVIDENCE = {
    "sextus_tlge_locus": (
        "data/audit/primary_wave/chunk_locus_changelog.jsonl: remappage "
        "TLG E multi-probe, famille passage_sext_*"
    ),
    "epictetus_tlge_locus": (
        "data/audit/primary_wave/chunk_locus_changelog.jsonl: remappage "
        "TLG E multi-probe, famille passage_epict_*"
    ),
    "epictetus_unresolved_urn_defake": (
        "data/audit/primary_wave/chunk_locus_changelog.jsonl: locus_defaked "
        "sans reference resolue; seul l'URN d'oeuvre est etabli"
    ),
    "augustine_de_libero_arbitrio": (
        "scripts/data_2026_08_17_semantic_merges.py: les URN dla sont "
        "adjugees correctes 170/170 et servent de jumeaux primaires"
    ),
    "augustine_de_gratia_urn": (
        "data/audit/primary_wave/urn_fix_changelog.jsonl: normalisation "
        "book_section_style"
    ),
    "augustine_de_correptione_urn": (
        "data/audit/primary_wave/urn_fix_changelog.jsonl: retrait du prefixe "
        "editorial PL 44"
    ),
    "origen_exhortatio": (
        "stamp linguistic_repairs_2026_08_17=reattribute_exhortatio; "
        "TLG2042.IDT work 007 et attestation textuelle locale"
    ),
    "tertullian_reattributions": (
        "stamp dialectical_repairs_2026_08_17=tert_reattribute; collation SC "
        "et retrait explicite des identifiants d'oeuvre non verifies"
    ),
}


class PlanError(RuntimeError):
    """Raised when an audited selection no longer matches its evidence."""


@dataclass(frozen=True)
class RepairRecord:
    family: str
    node_id: str
    passage_id: str
    expected_kg: dict[str, Any]
    expected_corpus: dict[str, Any]
    desired_corpus: dict[str, Any]
    remove_fields: tuple[str, ...]
    text_sha256: str
    stamp_value: dict[str, Any]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_target_maps(data_root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    audit_root = data_root / "audit" / "primary_wave"
    chunk_rows = read_jsonl(audit_root / "chunk_locus_changelog.jsonl")
    urn_rows = read_jsonl(audit_root / "urn_fix_changelog.jsonl")
    chunk = {
        str(row["node_id"]): row
        for row in chunk_rows
        if row.get("node_id") and isinstance(row.get("to"), dict)
    }
    urn_fixes = {
        str(row["node_id"]): row
        for row in urn_rows
        if row.get("node_id") and "to" in row
    }
    return chunk, urn_fixes


def _validate_augustine_adjudication() -> None:
    path = ROOT / "scripts" / "data_2026_08_17_semantic_merges.py"
    source = path.read_text(encoding="utf-8")
    markers = ("get the URN of their dla twin", "170/170")
    if not all(marker in source for marker in markers):
        raise PlanError("Augustine dla source-of-truth adjudication marker missing")


def _family_for_node(
    wanted: str,
    data: dict[str, Any],
    chunk_targets: dict[str, dict],
    urn_targets: dict[str, dict],
) -> str | None:
    if wanted.startswith("passage_sext_") and wanted in chunk_targets:
        target = chunk_targets[wanted]["to"]
        if data.get("canonical_ref") != target.get("ref"):
            return None
        if data.get("cts_urn") != target.get("urn"):
            return None
        return "sextus_tlge_locus"

    if wanted.startswith("passage_epict_") and wanted in chunk_targets:
        audit_row = chunk_targets[wanted]
        target = audit_row["to"]
        if data.get("cts_urn") != target.get("urn"):
            return None
        if audit_row.get("action") == "locus_defaked" and "ref" not in target:
            return "epictetus_unresolved_urn_defake"
        if data.get("canonical_ref") == target.get("ref"):
            return "epictetus_tlge_locus"
        return None

    title = data.get("work_title")
    if title == "De Gratia et Libero Arbitrio" and wanted in urn_targets:
        if data.get("cts_urn") != urn_targets[wanted].get("to"):
            return None
        return "augustine_de_gratia_urn"

    if title == "De Correptione et Gratia" and wanted in urn_targets:
        if data.get("cts_urn") != urn_targets[wanted].get("to"):
            return None
        return "augustine_de_correptione_urn"

    if wanted.startswith("passage_aug_dla_"):
        ref = data.get("canonical_ref")
        urn = data.get("cts_urn")
        if not isinstance(ref, str) or not isinstance(urn, str):
            return None
        if not urn.endswith(":" + ref):
            return None
        return "augustine_de_libero_arbitrio"

    if data.get("linguistic_repairs_2026_08_17") == "reattribute_exhortatio":
        if not wanted.startswith("passage_clement_protr_"):
            return None
        return "origen_exhortatio"

    if data.get("dialectical_repairs_2026_08_17") == "tert_reattribute":
        if not (
            wanted.startswith("passage_tert_adv_prax_")
            or wanted.startswith("passage_tert_exhort_cast_")
        ):
            return None
        if "work_canonical_id" in data or "cts_urn" in data:
            raise PlanError(f"{wanted}: stamped Tertullian KG identifiers reappeared")
        return "tertullian_reattributions"

    return None


def _stamp_value(family: str, wanted: str) -> dict[str, Any]:
    return {
        "family": family,
        "kg_node_id": wanted,
        "fields": list(FAMILY_FIELDS[family]),
        "evidence": FAMILY_EVIDENCE[family],
    }


def build_repair_records(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    data_root: Path,
) -> tuple[RepairRecord, ...]:
    """Derive the frozen, family-gated corpus repair plan."""

    _validate_augustine_adjudication()
    chunk_targets, urn_targets = _load_target_maps(data_root)
    passages_by_id = {
        str(row.get("passage_id") or ""): row for row in passages
    }
    citation_counts = Counter(
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
        )
        for row in citations
    )
    records: list[RepairRecord] = []

    for node in nodes:
        if node.get("type") != "passage":
            continue
        wanted = node_id(node)
        data = metadata(node)
        passage_id = str(data.get("db_passage_id") or "")
        if not passage_id:
            continue
        passage = passages_by_id.get(passage_id)
        if passage is None:
            continue
        family = _family_for_node(wanted, data, chunk_targets, urn_targets)
        if family is None:
            continue

        desired = {
            field: data.get(field)
            for field in FAMILY_FIELDS[family]
            if field in {"canonical_ref", "cts_urn"}
        }
        remove_fields: tuple[str, ...] = ()
        if family == "tertullian_reattributions":
            remove_fields = ("work_canonical_id",)

        expected_stamp = _stamp_value(family, wanted)
        needs_update = any(
            passage.get(field) != value for field, value in desired.items()
        ) or any(field in passage for field in remove_fields)
        if not needs_update and passage.get(STAMP) != expected_stamp:
            continue

        if citation_counts[(passage_id, wanted)] != 1:
            raise PlanError(
                f"{wanted}/{passage_id}: expected one twin citation, found "
                f"{citation_counts[(passage_id, wanted)]}"
            )

        expected_corpus = {
            field: passage.get(field)
            for field in desired
        }
        for field in remove_fields:
            if field in passage:
                expected_corpus[field] = passage[field]

        records.append(
            RepairRecord(
                family=family,
                node_id=wanted,
                passage_id=passage_id,
                expected_kg={
                    "db_passage_id": passage_id,
                    **desired,
                },
                expected_corpus=expected_corpus,
                desired_corpus=desired,
                remove_fields=remove_fields,
                text_sha256=sha256_text(str(passage.get("text_content") or "")),
                stamp_value=expected_stamp,
            )
        )

    records.sort(key=lambda row: (row.family, row.node_id, row.passage_id))
    family_counts = Counter(row.family for row in records)
    if dict(sorted(family_counts.items())) != dict(
        sorted(EXPECTED_FAMILY_ROWS.items())
    ):
        raise PlanError(
            f"repair family cardinality drift: {dict(sorted(family_counts.items()))}"
        )
    if len(records) != EXPECTED_REPAIR_ROWS:
        raise PlanError(f"repair row count drift: {len(records)}")
    passage_ids = [row.passage_id for row in records]
    if len(set(passage_ids)) != len(passage_ids):
        raise PlanError("a corpus passage was selected by more than one repair family")
    return tuple(records)


def record_digest(records: tuple[RepairRecord, ...]) -> str:
    payload = [
        {
            "family": row.family,
            "node_id": row.node_id,
            "passage_id": row.passage_id,
            "expected_kg": row.expected_kg,
            "expected_corpus": row.expected_corpus,
            "desired_corpus": row.desired_corpus,
            "remove_fields": row.remove_fields,
            "text_sha256": row.text_sha256,
            "stamp_value": row.stamp_value,
        }
        for row in records
    ]
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha256_text(raw)
