from __future__ import annotations

import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

repair = importlib.import_module("scripts.apply_2026_08_24_hildebrandt_p0_repair")

EXPECTED_COUNTS = Counter(
    {
        "kg_nodes_modified": 10,
        "kg_edges_modified": 8,
        "corpus_citations_modified": 4,
        "literature_builder_modified": 1,
        "literature_manifest_rows_modified": 1,
        "scholarly_manifest_rows_added": 1,
        "bibliography_entries_modified": 1,
        "bibliography_reports_modified": 1,
        "registry_sources_added": 1,
        "registry_evidence_added": 9,
        "registry_issues_added": 2,
        "registry_waves_modified": 2,
    }
)
EXPECTED_PATHS = set(repair.FILE_BEFORE_SHA256)
HISTORICAL_FILE_BEFORE_SHA256 = dict(repair.FILE_BEFORE_SHA256)
HISTORICAL_FILE_AFTER_SHA256 = dict(repair.FILE_AFTER_SHA256)
HISTORICAL_IMMUTABLE_FILE_HASHES = dict(repair.IMMUTABLE_FILE_HASHES)


def parse_rows(payload: bytes) -> list[dict]:
    return [json.loads(line) for line in payload.decode().splitlines() if line.strip()]


def output_rows(plan: repair.RepairPlan, relative: str) -> list[dict]:
    return parse_rows(plan.outputs[plan.root / relative])


def keyed_raw_lines(path: Path, key) -> dict[str, tuple[dict, str]]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result[str(key(row))] = (row, line)
    return result


def keyed_output_lines(payload: bytes, key) -> dict[str, tuple[dict, str]]:
    result = {}
    for line in payload.decode().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result[str(key(row))] = (row, line)
    return result


def symlink_children(source: Path, destination: Path, exclude: set[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if child.name in exclude:
            continue
        (destination / child.name).symlink_to(child, target_is_directory=child.is_dir())


def hardlink(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, destination)


def replace_bytes(path: Path, payload: bytes) -> None:
    path.unlink(missing_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def build_shadow_base(tmp_path: Path) -> Path:
    shadow = tmp_path / "repo"
    shadow.mkdir()
    (shadow / "docs").symlink_to(ROOT / "docs", target_is_directory=True)
    (shadow / "tests").symlink_to(ROOT / "tests", target_is_directory=True)

    scripts = shadow / "scripts"
    symlink_children(
        ROOT / "scripts", scripts, {Path(repair.BUILDER_RELATIVE).name}
    )
    hardlink(ROOT / repair.BUILDER_RELATIVE, shadow / repair.BUILDER_RELATIVE)

    data = shadow / "data"
    symlink_children(
        ROOT / "data",
        data,
        {"kg", "corpus", "literature_acquisition", "scholarly_sources", "goals", "audit"},
    )

    kg = data / "kg"
    kg_mutable = {
        Path(repair.NODES_RELATIVE).name,
        Path(repair.EDGES_RELATIVE).name,
        Path(repair.BIB_RELATIVE).name,
        Path(repair.BIB_REPORT_RELATIVE).name,
    }
    symlink_children(ROOT / "data/kg", kg, kg_mutable)
    for relative in (
        repair.NODES_RELATIVE,
        repair.EDGES_RELATIVE,
        repair.BIB_RELATIVE,
        repair.BIB_REPORT_RELATIVE,
    ):
        hardlink(ROOT / relative, shadow / relative)

    corpus = data / "corpus"
    symlink_children(
        ROOT / "data/corpus", corpus, {Path(repair.CITATIONS_RELATIVE).name}
    )
    hardlink(ROOT / repair.CITATIONS_RELATIVE, shadow / repair.CITATIONS_RELATIVE)

    literature = data / "literature_acquisition"
    symlink_children(
        ROOT / "data/literature_acquisition",
        literature,
        {Path(repair.LITERATURE_RELATIVE).name},
    )
    hardlink(ROOT / repair.LITERATURE_RELATIVE, shadow / repair.LITERATURE_RELATIVE)

    scholarly = data / "scholarly_sources"
    symlink_children(
        ROOT / "data/scholarly_sources",
        scholarly,
        {Path(repair.SCHOLARLY_RELATIVE).name},
    )
    hardlink(ROOT / repair.SCHOLARLY_RELATIVE, shadow / repair.SCHOLARLY_RELATIVE)

    (data / "goals").mkdir()
    shutil.copytree(
        ROOT / "data/goals/sota",
        data / "goals/sota",
        copy_function=os.link,
    )

    audit = data / "audit"
    audit.mkdir()
    for child in (ROOT / "data/audit").iterdir():
        if child.name.startswith(".hildebrandt_p0") or child.name in {
            Path(repair.REPORT_RELATIVE).name,
            Path(repair.QUARANTINE_RELATIVE).name,
        }:
            continue
        (audit / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    return shadow


def replace_jsonl_line(
    path: Path, key, wanted: str, raw_line: str | None
) -> None:
    output: list[str] = []
    found = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(key(row)) == wanted:
            found += 1
            if raw_line is not None:
                output.append(raw_line)
        else:
            output.append(line)
    assert found == 1, (path, wanted, found)
    replace_bytes(path, ("\n".join(output) + "\n").encode())


def reconstruct_snapshot_a_from_quarantine(
    shadow: Path, quarantine_path: Path | None = None
) -> None:
    quarantine_path = quarantine_path or (ROOT / repair.QUARANTINE_RELATIVE)
    assert quarantine_path.is_file(), "postwrite reconstruction requires quarantine"
    quarantine = repair.read_jsonl(quarantine_path)

    for row in quarantine:
        kind = row["record_type"]
        if kind == "kg_node_before":
            replace_jsonl_line(
                shadow / repair.NODES_RELATIVE,
                repair.node_id,
                repair.node_id(row["record"]),
                row["raw_line"],
            )
        elif kind == "kg_edge_before":
            replace_jsonl_line(
                shadow / repair.EDGES_RELATIVE,
                repair.edge_id,
                repair.edge_id(row["record"]),
                row["raw_line"],
            )
        elif kind == "corpus_citation_before":
            replace_jsonl_line(
                shadow / repair.CITATIONS_RELATIVE,
                repair.citation_key,
                repair.citation_key(row["record"]),
                row["raw_line"],
            )
        elif kind == "literature_manifest_row_before":
            replace_jsonl_line(
                shadow / repair.LITERATURE_RELATIVE,
                lambda item: item.get("artifact_id"),
                repair.LITERATURE_ARTIFACT_ID,
                row["raw_line"],
            )
        elif kind == "scholarly_manifest_absence_before":
            replace_jsonl_line(
                shadow / repair.SCHOLARLY_RELATIVE,
                lambda item: item.get("publication_dir"),
                repair.SCHOLARLY_PUBLICATION_DIR,
                None,
            )
        elif kind == "registry_source_absence_before":
            replace_jsonl_line(
                shadow / repair.SOURCES_RELATIVE,
                lambda item: item.get("source_id"),
                repair.SOURCE_ID,
                None,
            )
        elif kind == "registry_evidence_absence_before":
            replace_jsonl_line(
                shadow / repair.EVIDENCE_RELATIVE,
                lambda item: item.get("evidence_id"),
                row["evidence_id"],
                None,
            )
        elif kind == "registry_issue_absence_before":
            replace_jsonl_line(
                shadow / repair.ISSUES_RELATIVE,
                lambda item: item.get("issue_id"),
                row["issue_id"],
                None,
            )
        elif kind == "registry_wave_before":
            replace_jsonl_line(
                shadow / repair.WAVES_RELATIVE,
                lambda item: item.get("wave_id"),
                row["record"]["wave_id"],
                row["raw_line"],
            )

    builder = (shadow / repair.BUILDER_RELATIVE).read_text(encoding="utf-8")
    assert builder.count(repair.NEW_BUILDER_BLOCK) == 1
    replace_bytes(
        shadow / repair.BUILDER_RELATIVE,
        builder.replace(repair.NEW_BUILDER_BLOCK, repair.OLD_BUILDER_BLOCK).encode(),
    )

    bib_before = next(
        row["raw_text"]
        for row in quarantine
        if row["record_type"] == "bibliography_entry_before"
    )
    bib_path = shadow / repair.BIB_RELATIVE
    current = bib_path.read_text(encoding="utf-8")
    current_entry = repair.bib_entry(current, repair.BIBTEX_KEY)
    replace_bytes(bib_path, current.replace(current_entry, bib_before).encode())

    report_before = next(
        row["raw_text"]
        for row in quarantine
        if row["record_type"] == "bibliography_report_before"
    )
    replace_bytes(shadow / repair.BIB_REPORT_RELATIVE, report_before.encode())

def build_before_shadow(tmp_path: Path) -> Path:
    shadow = build_shadow_base(tmp_path)
    if (ROOT / repair.QUARANTINE_RELATIVE).is_file():
        reconstruct_snapshot_a_from_quarantine(shadow)
    return shadow


@pytest.fixture(scope="module")
def prospective_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_before_shadow(tmp_path_factory.mktemp("hildebrandt-prospective"))


@pytest.fixture(scope="module", autouse=True)
def composable_hildebrandt_freeze(prospective_root: Path):
    original_before = dict(repair.FILE_BEFORE_SHA256)
    original_after = dict(repair.FILE_AFTER_SHA256)
    original_immutable = dict(repair.IMMUTABLE_FILE_HASHES)
    composite_before = {
        relative: repair.sha256_file(prospective_root / relative)
        for relative in original_before
    }
    composite_immutable = {
        relative: repair.sha256_file(prospective_root / relative)
        for relative in original_immutable
    }
    repair.FILE_BEFORE_SHA256.clear()
    repair.FILE_BEFORE_SHA256.update(composite_before)
    repair.FILE_AFTER_SHA256.clear()
    repair.FILE_AFTER_SHA256.update(
        dict.fromkeys(original_after, "__COMPOSABLE_PENDING__")
    )
    repair.IMMUTABLE_FILE_HASHES.clear()
    repair.IMMUTABLE_FILE_HASHES.update(composite_immutable)
    pending = repair.build_plan(prospective_root)
    composite_after = {
        str(path.relative_to(prospective_root)): repair.sha256_bytes(payload)
        for path, payload in pending.outputs.items()
    }
    assert set(composite_after) == set(original_after)
    repair.FILE_AFTER_SHA256.clear()
    repair.FILE_AFTER_SHA256.update(composite_after)
    replay = repair.build_plan(prospective_root)
    assert replay.outputs == pending.outputs
    try:
        yield {
            "before": composite_before,
            "after": composite_after,
            "immutable": composite_immutable,
        }
    finally:
        repair.FILE_BEFORE_SHA256.clear()
        repair.FILE_BEFORE_SHA256.update(original_before)
        repair.FILE_AFTER_SHA256.clear()
        repair.FILE_AFTER_SHA256.update(original_after)
        repair.IMMUTABLE_FILE_HASHES.clear()
        repair.IMMUTABLE_FILE_HASHES.update(original_immutable)


@pytest.fixture(scope="module")
def prospective_plan(
    prospective_root: Path, composable_hildebrandt_freeze
) -> repair.RepairPlan:
    return repair.build_plan(prospective_root)


def test_historical_snapshot_and_live_hildebrandt_records_are_exact() -> None:
    report = json.loads((ROOT / repair.REPORT_RELATIVE).read_text())
    assert report["snapshot_a_file_sha256"] == HISTORICAL_FILE_BEFORE_SHA256
    assert report["output_sha256_preview"] == HISTORICAL_FILE_AFTER_SHA256

    nodes = {
        repair.node_id(row): row
        for row in repair.read_jsonl(ROOT / repair.NODES_RELATIVE)
    }
    assert {
        wanted: repair.canonical_hash(nodes[wanted])
        for wanted in report["after_record_hashes"]["nodes"]
    } == report["after_record_hashes"]["nodes"]

    edges = {
        repair.edge_id(row): row
        for row in repair.read_jsonl(ROOT / repair.EDGES_RELATIVE)
    }
    assert {
        wanted: repair.canonical_hash(edges[wanted])
        for wanted in report["after_record_hashes"]["edges"]
    } == report["after_record_hashes"]["edges"]

    citations = {
        repair.citation_key(row): row
        for row in repair.read_jsonl(ROOT / repair.CITATIONS_RELATIVE)
    }
    assert {
        wanted: repair.canonical_hash(citations[wanted])
        for wanted in report["after_record_hashes"]["citations"]
    } == report["after_record_hashes"]["citations"]


def test_prospective_breakdown_and_frozen_scope(
    prospective_plan: repair.RepairPlan,
) -> None:
    plan = prospective_plan
    assert plan.counts == EXPECTED_COUNTS
    assert plan.summary["status"] == "ready_for_independent_review_no_apply"
    assert plan.summary["write_performed"] is False
    assert set(plan.summary["changed_paths"]) == EXPECTED_PATHS
    assert len(plan.outputs) == 12
    assert len(plan.quarantine) == 41
    assert plan.summary["quarantine_record_count"] == 41
    assert set(plan.summary["touched_node_ids"]) == {
        repair.PUBLICATION_ID,
        repair.SCHOLAR_ID,
        *repair.POSITION_IDS,
    }
    assert set(plan.summary["modified_edge_ids"]) == repair.AUTHOR_EDGE_IDS
    assert plan.summary["corpus_passage_rows_modified"] == 0
    assert plan.summary["verification_records_added"] == 0
    schema = plan.summary["registry_schema_debt"]
    assert schema["baseline_errors"] == schema["preview_errors"] == 41
    assert schema["new_errors"] == schema["touched_record_errors"] == 0
    debt = plan.summary["strict_ingestion_debt"]
    assert debt["before"]["block"] == debt["after_preview"]["block"]
    assert debt["after_preview"]["warn"] <= debt["before"]["warn"]
    for relative, expected in repair.FILE_AFTER_SHA256.items():
        assert repair.sha256_bytes(plan.outputs[plan.root / relative]) == expected


def test_node_diff_is_exact_and_positions_are_fail_closed(
    prospective_plan: repair.RepairPlan,
) -> None:
    plan = prospective_plan
    before = keyed_raw_lines(plan.root / repair.NODES_RELATIVE, repair.node_id)
    after = keyed_output_lines(plan.outputs[plan.root / repair.NODES_RELATIVE], repair.node_id)
    changed = {wanted for wanted in before if before[wanted][0] != after[wanted][0]}
    expected = {repair.PUBLICATION_ID, repair.SCHOLAR_ID, *repair.POSITION_IDS}
    assert changed == expected
    assert all(before[wanted][1] == after[wanted][1] for wanted in set(before) - expected)

    spec = importlib.util.spec_from_file_location(
        "hildebrandt_true_citability",
        ROOT / "graphrag/src/eleutheria_graphrag/agents/citability.py",
    )
    assert spec is not None and spec.loader is not None
    policy = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = policy
    spec.loader.exec_module(policy)

    nodes = {wanted: row for wanted, (row, _line) in after.items()}
    for wanted in repair.POSITION_IDS:
        data = repair.metadata(nodes[wanted])
        assert data["page_range"] == repair.page_ranges(repair.POSITION_SPECS[wanted])
        assert data["claim_status"] == "in_review"
        assert data["citability"] == "discoverable_only"
        assert data["manifestation_id"] == repair.MANIFESTATION_ID
        assert data["scholarly_work_id"] == repair.PUBLICATION_ID
        assert policy.evidence_policy(nodes[wanted]).tier is (
            policy.CitabilityTier.DISCOVERABLE_ONLY
        )
        assert not {
            "page",
            "quote_verbatim",
            "citation_verified",
            "verified_reference",
            "ingestion_debt_2026_08_17_schema_normalised",
        } & data.keys()
    central = nodes[repair.POSITION_IDS[0]]["description"].lower()
    assert "one succeeds" not in central
    assert "measured consensus" not in central
    average = repair.metadata(nodes[repair.POSITION_IDS[2]])
    assert {item["role"] for item in average["claim_components"]} == {
        "hildebrandt_interpretive_extension",
        "hildebrandt_extension_partly_derived_from_brennan_2005",
    }
    negative = nodes[repair.POSITION_IDS[6]]["description"].lower()
    assert "not proof of absolute historical absence" in negative


def test_publication_identity_rights_and_scholar_privacy(
    prospective_plan: repair.RepairPlan,
) -> None:
    nodes = {
        repair.node_id(row): row
        for row in output_rows(prospective_plan, repair.NODES_RELATIVE)
    }
    publication = repair.metadata(nodes[repair.PUBLICATION_ID])
    assert publication["title"] == repair.TITLE
    assert publication["author"] == repair.AUTHOR
    assert publication["doi"] == repair.DOI
    assert publication["manifestation_id"] == repair.MANIFESTATION_ID
    assert publication["printed_page_range"] == {"start": 25, "end": 44}
    assert publication["pdf_page_range"] == {"start": 1, "end": 20}
    assert publication["access_status"] == "open_access"
    assert publication["rights_statement"] == repair.RIGHTS_STATEMENT
    assert publication["license_status"] == "no_explicit_reuse_licence_archived"
    assert publication["reuse_status"] == "unverified_do_not_republish"
    assert "license" not in publication and "citation_verified" not in publication

    scholar_blob = json.dumps(nodes[repair.SCHOLAR_ID], ensure_ascii=False)
    assert "Emil-Figge" not in scholar_blob
    assert "44227" not in scholar_blob
    assert "@" not in scholar_blob
    affiliations = repair.metadata(nodes[repair.SCHOLAR_ID])["affiliations_at_publication"]
    assert all("temporal_scope" in row for row in affiliations)
    assert "November 2022-September 2023" in json.dumps(affiliations)


def test_eight_attribution_edges_change_direction_only_with_bounded_metadata(
    prospective_plan: repair.RepairPlan,
) -> None:
    before = keyed_raw_lines(prospective_plan.root / repair.EDGES_RELATIVE, repair.edge_id)
    after = keyed_output_lines(
        prospective_plan.outputs[prospective_plan.root / repair.EDGES_RELATIVE],
        repair.edge_id,
    )
    changed = {wanted for wanted in before if before[wanted][0] != after[wanted][0]}
    assert changed == repair.AUTHOR_EDGE_IDS
    assert all(before[wanted][1] == after[wanted][1] for wanted in set(before) - changed)
    for wanted in changed:
        old = before[wanted][0]
        new = after[wanted][0]
        assert old["relation"] == "created_by"
        assert new["relation"] == "authored_by"
        assert (new.get("target_id") or new.get("target")) == repair.SCHOLAR_ID
        assert new["metadata"]["claim_status"] == "in_review"
        assert new["metadata"]["citability"] == "discoverable_only"
        for key in ("edge_id", "source", "source_id", "target", "target_id", "weight", "created_at"):
            assert new.get(key) == old.get(key)


def test_citation_diff_repairs_phi054_and_registers_de_fato_debt_without_corpus_edit(
    prospective_plan: repair.RepairPlan,
) -> None:
    before = keyed_raw_lines(
        prospective_plan.root / repair.CITATIONS_RELATIVE, repair.citation_key
    )
    after = keyed_output_lines(
        prospective_plan.outputs[prospective_plan.root / repair.CITATIONS_RELATIVE],
        repair.citation_key,
    )
    changed = {wanted for wanted in before if before[wanted][0] != after[wanted][0]}
    expected = {"\x1f".join(key) for key in repair.CITATION_TARGETS}
    assert changed == expected
    for wanted in changed:
        old, new = before[wanted][0], after[wanted][0]
        assert {key for key in set(old) | set(new) if old.get(key) != new.get(key)} == {"notes"}
    for wanted in changed:
        note = after[wanted][0]["notes"]
        if repair.CITATION_TARGETS[tuple(wanted.split("\x1f"))] == "cicero_phi054":
            assert "phi049" not in note and "phi054" in note
    assert "ἀργύριον ριον" in after[
        "\x1f".join((repair.POSITION_IDS[1], repair.DE_FATO_8_UUID, "discussion"))
    ][0]["notes"]
    assert "Primary recollation" in after[
        "\x1f".join((repair.POSITION_IDS[7], repair.DE_FATO_11_UUID, "paraphrase"))
    ][0]["notes"]
    assert repair.sha256_file(ROOT / "data/corpus/passages.jsonl") == (
        repair.IMMUTABLE_FILE_HASHES["data/corpus/passages.jsonl"]
    )


def test_builder_and_literature_manifest_change_only_hildebrandt(
    prospective_plan: repair.RepairPlan,
) -> None:
    before = (prospective_plan.root / repair.BUILDER_RELATIVE).read_bytes()
    after = prospective_plan.outputs[prospective_plan.root / repair.BUILDER_RELATIVE]
    assert after == before.decode().replace(
        repair.OLD_BUILDER_BLOCK, repair.NEW_BUILDER_BLOCK
    ).encode()
    assert before.decode().count(repair.OLD_BUILDER_BLOCK) == 1
    generated = repair.execute_candidate_literature_builder(after, prospective_plan.root)
    assert repair.serialize_jsonl(generated) == prospective_plan.outputs[
        prospective_plan.root / repair.LITERATURE_RELATIVE
    ]
    old = {
        row["artifact_id"]: row
        for row in repair.read_jsonl(prospective_plan.root / repair.LITERATURE_RELATIVE)
    }
    new = {row["artifact_id"]: row for row in generated}
    assert set(old) == set(new)
    assert {wanted for wanted in old if old[wanted] != new[wanted]} == {
        repair.LITERATURE_ARTIFACT_ID
    }
    row = new[repair.LITERATURE_ARTIFACT_ID]
    assert row["creators"] == [repair.AUTHOR]
    assert row["title"] == repair.TITLE
    assert row["audit_status"] == "deep_read_wave1"
    assert row["rights_statement"] == repair.RIGHTS_STATEMENT
    assert row["license_status"] == "no_explicit_reuse_licence_archived"


def test_scholarly_manifest_registry_and_issues_remain_partial_open_no_fake_passes(
    prospective_plan: repair.RepairPlan,
) -> None:
    scholarly = output_rows(prospective_plan, repair.SCHOLARLY_RELATIVE)
    row = next(
        item
        for item in scholarly
        if item.get("publication_dir") == repair.SCHOLARLY_PUBLICATION_DIR
    )
    assert row["manifestation_id"] == repair.MANIFESTATION_ID
    assert row["kg_ingestion_status"] == "partial"
    assert row["page_count"] == 20
    assert row["pdf_sha256"] == repair.PDF_SHA256
    assert row["reuse_status"] == "unverified_do_not_republish"

    sources = output_rows(prospective_plan, repair.SOURCES_RELATIVE)
    source = next(item for item in sources if item.get("source_id") == repair.SOURCE_ID)
    assert source["coverage"]["state"] == "partial"
    assert source["canonical_identifiers"]["doi"] == repair.DOI
    assert source["creators"] == [repair.AUTHOR]

    evidence = {
        item["evidence_id"]: item
        for item in output_rows(prospective_plan, repair.EVIDENCE_RELATIVE)
    }
    assert set(repair.ALL_EVIDENCE_IDS) <= set(evidence)
    for wanted in repair.ALL_EVIDENCE_IDS:
        assert evidence[wanted]["claim_status"] == "in_review"
        assert evidence[wanted]["quotation"]["status"] == "paraphrase_only"
        assert "independent_review" in evidence[wanted]["required_verification"]

    issues = {
        item["issue_id"]: item
        for item in output_rows(prospective_plan, repair.ISSUES_RELATIVE)
    }
    assert issues[repair.CLAIM_ISSUE_ID]["status"] == "open"
    assert issues[repair.TEXT_ISSUE_ID]["status"] == "open"
    assert repair.DE_FATO_8_UUID in issues[repair.TEXT_ISSUE_ID]["summary"]
    assert repair.DE_FATO_11_UUID in issues[repair.TEXT_ISSUE_ID]["summary"]
    assert "verifications" not in prospective_plan.summary["changed_paths"]
    assert prospective_plan.summary["verification_records_added"] == 0


def test_bibtex_entry_and_report_are_atomically_consistent(
    prospective_plan: repair.RepairPlan,
) -> None:
    bib = prospective_plan.outputs[prospective_plan.root / repair.BIB_RELATIVE].decode()
    entry = repair.bib_entry(bib, repair.BIBTEX_KEY)
    assert repair.TITLE in entry
    assert "Hildebrandt 2022 —" not in entry
    assert repair.DOI in entry
    assert repair.MANIFESTATION_ID in entry
    report = json.loads(
        prospective_plan.outputs[
            prospective_plan.root / repair.BIB_REPORT_RELATIVE
        ]
    )
    assert report["generation_mode"] == (
        "hildebrandt_bibliography_surgical_snapshot_transform"
    )
    assert report["bibtex_sha256"] == repair.sha256_bytes(bib.encode())
    assert report["entries_written"] == len(report["entry_keys"])
    assert len(report["entry_keys"]) == len(set(report["entry_keys"]))
    assert report["baseline_bibtex_sha256"] == repair.FILE_BEFORE_SHA256[
        repair.BIB_RELATIVE
    ]


def test_quarantine_has_exact_raw_before_images(
    prospective_plan: repair.RepairPlan,
) -> None:
    kinds = Counter(row["record_type"] for row in prospective_plan.quarantine)
    assert kinds == Counter(
        {
            "kg_node_before": 10,
            "kg_edge_before": 8,
            "corpus_citation_before": 4,
            "literature_manifest_row_before": 1,
            "literature_builder_before_summary": 1,
            "scholarly_manifest_absence_before": 1,
            "bibliography_entry_before": 1,
            "bibliography_report_before": 1,
            "registry_source_absence_before": 1,
            "registry_evidence_absence_before": 9,
            "registry_issue_absence_before": 2,
            "registry_wave_before": 2,
        }
    )
    raw_kinds = {
        "kg_node_before",
        "kg_edge_before",
        "corpus_citation_before",
        "literature_manifest_row_before",
        "registry_wave_before",
    }
    assert all(
        "raw_line" in row
        for row in prospective_plan.quarantine
        if row["record_type"] in raw_kinds
    )
    assert not any(
        row["record_type"].startswith("corpus_passage")
        for row in prospective_plan.quarantine
    )


def test_full_registry_audit_accepts_preview(
    prospective_plan: repair.RepairPlan, tmp_path: Path
) -> None:
    from scripts.audit_sota_registry import audit_registry

    shadow = build_before_shadow(tmp_path)
    plan = repair.build_plan(shadow)
    for path, payload in plan.outputs.items():
        replace_bytes(path, payload)
    report = audit_registry(shadow / "data/goals/sota", shadow)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["errors"] == []
    assert report["exit_ready"] is False


def test_copy_write_then_dry_run_and_repeat_are_truthful(tmp_path: Path) -> None:
    shadow = build_before_shadow(tmp_path)
    plan = repair.build_plan(shadow)
    root_before = {
        relative: (ROOT / relative).read_bytes()
        for relative in repair.FILE_BEFORE_SHA256
    }
    repair.apply_plan(plan)
    first = json.loads((shadow / repair.REPORT_RELATIVE).read_text())
    assert first["status"] == "applied_open_issues_pending_review"
    assert first["write_performed"] is True
    for relative, expected in repair.FILE_AFTER_SHA256.items():
        assert repair.sha256_file(shadow / relative) == expected
    assert (shadow / repair.REPORT_RELATIVE).is_file()
    assert (shadow / repair.QUARANTINE_RELATIVE).is_file()

    applied = {
        relative: (shadow / relative).read_bytes()
        for relative in repair.FILE_AFTER_SHA256
    }
    dry = repair.build_plan(shadow)
    assert dry.summary["status"] == "already_applied"
    assert dry.summary["write_performed"] is False
    assert dry.counts == Counter()
    repair.apply_plan(dry)
    assert applied == {
        relative: (shadow / relative).read_bytes()
        for relative in repair.FILE_AFTER_SHA256
    }
    assert root_before == {
        relative: (ROOT / relative).read_bytes()
        for relative in repair.FILE_BEFORE_SHA256
    }


def test_persisted_quarantine_reconstructs_exact_snapshot_a(tmp_path: Path) -> None:
    shadow = build_before_shadow(tmp_path)
    plan = repair.build_plan(shadow)
    repair.apply_plan(plan)
    assert all(
        repair.sha256_file(shadow / relative) == expected
        for relative, expected in repair.FILE_AFTER_SHA256.items()
    )
    reconstruct_snapshot_a_from_quarantine(
        shadow, shadow / repair.QUARANTINE_RELATIVE
    )
    for relative, expected in repair.FILE_BEFORE_SHA256.items():
        assert repair.sha256_file(shadow / relative) == expected
    reconstructed = repair.build_plan(shadow)
    assert reconstructed.counts == EXPECTED_COUNTS


def assert_scratch_absent(root: Path) -> None:
    journal, backup = repair.journal_paths(root)
    assert not journal.exists() and not backup.exists()


def test_copy_hard_abort_after_bib_report_restores_snapshot_a(tmp_path: Path) -> None:
    shadow = build_before_shadow(tmp_path)
    plan = repair.build_plan(shadow)
    before = {
        path: (path.read_bytes() if path.exists() else None)
        for path in {
            **plan.before_bytes,
            shadow / repair.REPORT_RELATIVE: None,
            shadow / repair.QUARANTINE_RELATIVE: None,
        }
    }
    with pytest.raises(repair.InjectedTransactionAbort):
        repair.apply_plan(plan, fail_after=8)
    assert before == {
        path: (path.read_bytes() if path.exists() else None) for path in before
    }
    assert_scratch_absent(shadow)


def transaction_fixture(tmp_path: Path):
    (tmp_path / "data/audit").mkdir(parents=True)
    live = tmp_path / "live"
    live.mkdir()
    first = live / "first.json"
    second = live / "second.json"
    first.write_bytes(b"first-before\n")
    second.write_bytes(b"second-before\n")
    before = {first: first.read_bytes(), second: second.read_bytes()}
    outputs = {first: b"first-after\n", second: b"second-after\n"}
    return first, second, before, outputs


def test_transaction_precommit_drift_preserves_external_writer(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)

    def external() -> None:
        second.write_bytes(b"external\n")

    with pytest.raises(repair.PreconditionsError, match="pre-commit snapshot drift"):
        repair.transactional_replace(
            tmp_path, outputs, before, before_commit_hook=external
        )
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == b"external\n"
    assert_scratch_absent(tmp_path)


def test_transaction_rollback_failure_can_be_recovered(tmp_path: Path, monkeypatch) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_replace = os.replace
    commit_failed = False
    rollback_failed = False

    def fail_commit_and_rollback(source: Path, destination: Path) -> None:
        nonlocal commit_failed, rollback_failed
        target = Path(destination)
        if target == second and not commit_failed:
            commit_failed = True
            raise OSError("commit failure")
        if target == first and commit_failed and not rollback_failed:
            rollback_failed = True
            raise OSError("rollback failure")
        real_replace(source, destination)

    monkeypatch.setattr(repair, "replace_path", fail_commit_and_rollback)
    with pytest.raises(OSError, match="rollback failure"):
        repair.transactional_replace(tmp_path, outputs, before)
    journal, backup = repair.journal_paths(tmp_path)
    assert journal.is_file() and backup.is_dir()
    monkeypatch.setattr(repair, "replace_path", real_replace)
    assert repair.recover_transaction(tmp_path) == "rolled_back"
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_scratch_absent(tmp_path)


def test_production_write_requires_explicit_approval() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / repair.SCRIPT_RELATIVE),
            "--root",
            str(ROOT),
            "--write",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked_explicit_production_approval_required"
    assert payload["write_performed"] is False


def test_live_hildebrandt_records_are_applied_and_record_scoped_noop() -> None:
    watched = [ROOT / relative for relative in EXPECTED_PATHS]
    before = {path: path.read_bytes() for path in watched}

    nodes = repair.read_jsonl(ROOT / repair.NODES_RELATIVE)
    node_after, node_quarantine, node_counts = repair.transform_nodes(
        nodes, state="after"
    )
    assert node_after == nodes
    assert node_quarantine == [] and node_counts == Counter()

    edges = repair.read_jsonl(ROOT / repair.EDGES_RELATIVE)
    edge_after, edge_quarantine, edge_counts = repair.transform_edges(
        edges, state="after"
    )
    assert edge_after == edges
    assert edge_quarantine == [] and edge_counts == Counter()

    citations = repair.read_jsonl(ROOT / repair.CITATIONS_RELATIVE)
    citation_after, citation_quarantine, citation_counts = (
        repair.transform_citations(citations, state="after")
    )
    assert citation_after == citations
    assert citation_quarantine == [] and citation_counts == Counter()

    literature = repair.read_jsonl(ROOT / repair.LITERATURE_RELATIVE)
    builder = (ROOT / repair.BUILDER_RELATIVE).read_bytes()
    builder_after, literature_after, literature_quarantine, literature_counts = (
        repair.transform_literature(ROOT, builder, literature, state="after")
    )
    assert builder_after == builder and literature_after == literature
    assert literature_quarantine == [] and literature_counts == Counter()

    scholarly = repair.read_jsonl(ROOT / repair.SCHOLARLY_RELATIVE)
    scholarly_after, scholarly_quarantine, scholarly_counts = (
        repair.transform_scholarly_manifest(scholarly, state="after")
    )
    assert scholarly_after == scholarly
    assert scholarly_quarantine == [] and scholarly_counts == Counter()

    registry_before = {
        "sources": repair.read_jsonl(ROOT / repair.SOURCES_RELATIVE),
        "evidence": repair.read_jsonl(ROOT / repair.EVIDENCE_RELATIVE),
        "issues": repair.read_jsonl(ROOT / repair.ISSUES_RELATIVE),
        "waves": repair.read_jsonl(ROOT / repair.WAVES_RELATIVE),
    }
    registry_after, registry_quarantine, registry_counts = repair.transform_registry(
        registry_before["sources"],
        registry_before["evidence"],
        registry_before["issues"],
        registry_before["waves"],
        state="after",
    )
    assert registry_after == registry_before
    assert registry_quarantine == [] and registry_counts == Counter()

    from scripts.export_publications_bibtex import publication_to_bibtex

    publication = next(
        row for row in nodes if repair.node_id(row) == repair.PUBLICATION_ID
    )
    expected_entry, missing = publication_to_bibtex(publication)
    assert missing == []
    assert repair.bib_entry(
        (ROOT / repair.BIB_RELATIVE).read_text(encoding="utf-8"),
        repair.BIBTEX_KEY,
    ) == expected_entry
    assert {path: path.read_bytes() for path in watched} == before
