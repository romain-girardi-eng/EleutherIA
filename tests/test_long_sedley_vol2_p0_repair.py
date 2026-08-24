from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

repair = importlib.import_module(
    "scripts.apply_2026_08_24_long_sedley_vol2_p0_repair"
)


EXPECTED_COUNTS = Counter(
    {
        "kg_nodes_modified": 39,
        "kg_edges_removed": 13,
        "kg_edges_modified": 1,
        "kg_edges_added": 7,
        "literature_builder_modified": 1,
        "literature_manifest_rows_modified": 1,
        "scholarly_manifest_rows_added": 1,
        "registry_sources_modified": 1,
        "registry_evidence_modified": 1,
        "registry_evidence_removed": 1,
        "registry_evidence_added": 2,
        "registry_issues_modified": 1,
        "registry_issues_added": 3,
        "registry_waves_modified": 1,
        "registry_primary_verifications_added": 4,
    }
)

EXPECTED_PATHS = set(repair.FILE_BEFORE_SHA256)
HISTORICAL_FILE_BEFORE_SHA256 = dict(repair.FILE_BEFORE_SHA256)
HISTORICAL_FILE_AFTER_SHA256 = dict(repair.FILE_AFTER_SHA256)
HISTORICAL_IMMUTABLE_FILE_HASHES = dict(repair.IMMUTABLE_FILE_HASHES)


@pytest.fixture(scope="module")
def preapply_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return reconstruct_preapply_workspace(tmp_path_factory.mktemp("long-preapply"))


@pytest.fixture(scope="module")
def plan(preapply_root: Path, composable_long_freeze) -> repair.RepairPlan:
    return build_prospective_plan(preapply_root)


def build_prospective_plan(preapply_root: Path) -> repair.RepairPlan:
    return repair.build_plan(preapply_root)


@pytest.fixture(scope="module", autouse=True)
def composable_long_freeze(preapply_root: Path):
    original_before = dict(repair.FILE_BEFORE_SHA256)
    original_after = dict(repair.FILE_AFTER_SHA256)
    original_immutable = dict(repair.IMMUTABLE_FILE_HASHES)
    composite_before = {
        relative: (
            repair.sha256_file(preapply_root / relative)
            if (preapply_root / relative).exists()
            else None
        )
        for relative in original_before
    }
    composite_immutable = {
        relative: repair.sha256_file(preapply_root / relative)
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
    pending = repair.build_plan(preapply_root)
    composite_after = {
        str(path.relative_to(preapply_root)): repair.sha256_bytes(payload)
        for path, payload in pending.outputs.items()
    }
    assert set(composite_after) == set(original_after)
    repair.FILE_AFTER_SHA256.clear()
    repair.FILE_AFTER_SHA256.update(composite_after)
    replay = repair.build_plan(preapply_root)
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


def parse_rows(payload: bytes) -> list[dict]:
    return [json.loads(line) for line in payload.decode().splitlines() if line.strip()]


def output_rows(plan: repair.RepairPlan, relative: str) -> list[dict]:
    return parse_rows(plan.outputs[plan.root / relative])


def planned_nodes(plan: repair.RepairPlan) -> dict[str, dict]:
    return {
        repair.node_id(row): row
        for row in output_rows(plan, repair.NODES_RELATIVE)
    }


def planned_edges(plan: repair.RepairPlan) -> dict[str, dict]:
    return {
        repair.edge_id(row): row
        for row in output_rows(plan, repair.EDGES_RELATIVE)
    }


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


def test_dry_run_breakdown_and_frozen_scope(plan: repair.RepairPlan) -> None:
    assert plan.counts == EXPECTED_COUNTS
    assert plan.summary["status"] == "ready_for_independent_re_review_no_apply"
    assert plan.summary["write_performed"] is False
    assert set(plan.summary["changed_paths"]) == EXPECTED_PATHS
    assert len(plan.outputs) == 10
    assert len(plan.quarantine) == 77
    assert set(plan.summary["touched_node_ids"]) == repair.TOUCHED_NODE_IDS
    assert set(plan.summary["removed_edge_ids"]) == repair.REMOVED_EDGE_IDS
    assert set(plan.summary["added_edge_ids"]) == repair.NEW_EDGE_IDS
    assert plan.summary["modified_edge_ids"] == [repair.MODIFIED_EDGE_ID]
    assert plan.summary["citation_rows_modified"] == 0
    assert plan.summary["corpus_files_modified"] == 0
    assert plan.summary["bibtex_files_modified"] == 0
    assert plan.summary["e2_files_modified"] == 0
    assert all(
        not path.startswith("data/corpus/")
        and path not in repair.IMMUTABLE_FILE_HASHES
        for path in plan.summary["changed_paths"]
    )
    assert plan.summary["strict_ingestion_debt"]["before"] == plan.summary[
        "strict_ingestion_debt"
    ]["after_preview"]
    schema = plan.summary["registry_schema_debt"]
    assert schema["baseline_errors"] == schema["preview_errors"] == 41
    assert schema["new_errors"] == schema["touched_record_errors"] == 0


def test_reconstructed_snapshot_a_replays_reviewed_postwrite_hashes(
    plan: repair.RepairPlan,
) -> None:
    report = json.loads((ROOT / repair.REPORT_RELATIVE).read_text())
    assert plan.summary["before_record_hashes"] == report["before_record_hashes"]
    assert plan.summary["after_record_hashes"] == report["after_record_hashes"]
    assert len(plan.quarantine) == report["quarantine_record_count"] == 77
    assert report["snapshot_a_file_sha256"] == HISTORICAL_FILE_BEFORE_SHA256
    assert report["output_sha256_preview"] == HISTORICAL_FILE_AFTER_SHA256
    live_nodes = {
        repair.node_id(row): row
        for row in repair.read_jsonl(ROOT / repair.NODES_RELATIVE)
    }
    assert {
        wanted: repair.canonical_hash(live_nodes[wanted])
        for wanted in repair.TOUCHED_NODE_IDS
    } == report["after_record_hashes"]["nodes"]
    live_edges = {
        repair.edge_id(row): row
        for row in repair.read_jsonl(ROOT / repair.EDGES_RELATIVE)
    }
    assert not set(report["removed_edge_ids"]) & live_edges.keys()
    assert {
        wanted: repair.canonical_hash(live_edges[wanted])
        for wanted in {
            *report["added_edge_ids"],
            *report["modified_edge_ids"],
        }
    } == report["after_record_hashes"]["edges_modified_or_added"]


def test_node_diff_is_exact_and_all_other_lines_are_byte_identical(
    plan: repair.RepairPlan,
) -> None:
    before = keyed_raw_lines(plan.root / repair.NODES_RELATIVE, repair.node_id)
    after = keyed_output_lines(
        plan.outputs[plan.root / repair.NODES_RELATIVE], repair.node_id
    )
    assert set(before) == set(after)
    json_changed = {
        wanted for wanted in before if before[wanted][0] != after[wanted][0]
    }
    raw_changed = {
        wanted for wanted in before if before[wanted][1] != after[wanted][1]
    }
    assert json_changed == raw_changed == set(repair.TOUCHED_NODE_IDS)
    assert all(
        before[wanted][1] == after[wanted][1]
        for wanted in set(before) - repair.TOUCHED_NODE_IDS
    )
    assert {
        wanted: repair.canonical_hash(before[wanted][0])
        for wanted in repair.OVERLAP_NODE_IDS
    } == repair.OVERLAP_BEFORE_HASHES
    assert repair.sha256_bytes(plan.outputs[plan.root / repair.NODES_RELATIVE]) == (
        repair.FILE_AFTER_SHA256[repair.NODES_RELATIVE]
    )


def test_work_volume_and_scan_manifestation_are_separated(
    plan: repair.RepairPlan,
) -> None:
    nodes = planned_nodes(plan)
    work = repair.metadata(nodes[repair.WORK_ID])
    assert work["publication_identity"] == "two_volume_intellectual_work"
    assert work["author_ids"] == [repair.LONG_ID, repair.SEDLEY_ID]
    assert work["isbn"] == "978-0521275569"
    assert "volume 1" in work["isbn_scope"]
    assert "citation_verified" not in work and "verified_reference" not in work
    volume1, volume2 = work["volumes"]
    assert volume1["volume_number"] == 1
    assert volume1["isbn_13_paperback"] == "9780521275569"
    assert volume1["audit_status"] == "not_audited_in_this_transaction"
    assert volume2["volume_number"] == 2
    assert volume2["isbn_10_hardback"] == "0521255627"
    assert volume2["isbn_10_paperback"] == "0521275571"
    local = volume2["local_scan_manifestation"]
    assert local["visible_reprint_line_latest_year"] == 1998
    assert local["exact_printing_status"] == "unknown_not_inferred"
    assert local["binding_status"] == "unknown_cover_absent"
    assert local["physically_missing"] == ["front cover", "preliminaries i-ii"]

    from scripts.export_publications_bibtex import build_publication_export

    baseline = repair.read_jsonl(plan.root / repair.NODES_RELATIVE)
    assert build_publication_export(copy.deepcopy(baseline)) == build_publication_export(
        copy.deepcopy(list(nodes.values()))
    )


def test_collection_pages_are_volume_specific(plan: repair.RepairPlan) -> None:
    collection = repair.metadata(planned_nodes(plan)[repair.COLLECTION_ID])
    maps = collection["section_page_maps"]
    assert maps["volume_1"] == {
        "LS20_start": 102,
        "LS55_start": 333,
        "LS62_start": 386,
        "status": "legacy_labels_pending_dedicated_volume1_audit",
    }
    assert maps["volume_2"]["LS20"] == {
        "printed_pages": "104-113",
        "pdf_pages": "112-121",
    }
    assert maps["volume_2"]["LS55"]["printed_pages"] == "332-341"
    assert maps["volume_2"]["LS62"]["printed_pages"] == "382-389"
    assert maps["volume_2"]["status"] == "visually_verified"


def test_priority_and_overlap_nodes_are_runtime_discoverable_only(
    plan: repair.RepairPlan,
) -> None:
    nodes = planned_nodes(plan)
    spec = importlib.util.spec_from_file_location(
        "long_sedley_true_citability",
        ROOT / "graphrag/src/eleutheria_graphrag/agents/citability.py",
    )
    assert spec is not None and spec.loader is not None
    policy = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = policy
    spec.loader.exec_module(policy)
    interpretive = {repair.POSITION_ID, *repair.OVERLAP_NODE_IDS}
    for wanted in interpretive:
        data = repair.metadata(nodes[wanted])
        assert data["citability"] == "discoverable_only"
        assert policy.evidence_policy(nodes[wanted]).tier is (
            policy.CitabilityTier.DISCOVERABLE_ONLY
        )
    position = repair.metadata(nodes[repair.POSITION_ID])
    assert position["citation_verdict"] == (
        "attributed_disputed_priority_volume1_and_huby_audit_pending"
    )
    assert position["volume1_claim_audit"]["status"] == (
        "typed_pending_do_not_modify_edge"
    )
    assert "necessary" in position["conclusion"]["text"]
    assert "sufficient" in position["conclusion"]["text"]
    assert "direct" in position["conclusion"]["text"]


def test_overlap_public_descriptions_are_not_rewritten(plan: repair.RepairPlan) -> None:
    before = {
        repair.node_id(row): row
        for row in repair.read_jsonl(plan.root / repair.NODES_RELATIVE)
    }
    after = planned_nodes(plan)
    for wanted in repair.OVERLAP_NODE_IDS:
        assert after[wanted]["description"] == before[wanted]["description"]
        visual = repair.metadata(after[wanted])["long_sedley_vol2_visual_evidence"]
        assert visual["quotation_status"] == "paraphrase_only"
        assert visual["primary_source_status"] == (
            "ancient_loci_leads_not_primary_verified"
        )
    cylinder = repair.metadata(
        after["argument_cylinder_analogy_chrysippus_k1l2m3n4"]
    )
    assert "7.2.6-14" not in json.dumps(cylinder, ensure_ascii=False)
    assert "7.2.6-13" in json.dumps(cylinder, ensure_ascii=False)


def test_fragment_collection_corrections_are_exact(plan: repair.RepairPlan) -> None:
    nodes = planned_nodes(plan)
    for wanted, false_refs in repair.FALSE_LS_REFS_BY_NODE.items():
        assert not (repair.ls_refs(nodes[wanted]) & false_refs)
    for wanted, spec in repair.EXACT_LS_REFS_BY_NODE.items():
        assert spec["reference"] in repair.ls_refs(nodes[wanted])
    assert repair.ls_refs(nodes["passage_gellius_na_vii_2_7_2_3"]) >= {"55K"}
    for paragraph in (1, 2, 4, 5, 14, 15):
        assert "62D" not in repair.ls_refs(
            nodes[f"passage_gellius_na_vii_2_7_2_{paragraph}"]
        )
    assert "62D" in repair.ls_refs(nodes["passage_gellius_na_vii_2_7_2_6"])
    assert "55K" not in repair.ls_refs(nodes["passage_gellius_na_vii_2_7_2_13"])


def test_edge_diff_is_exact_and_ag026_is_byte_identical(
    plan: repair.RepairPlan,
) -> None:
    before = keyed_raw_lines(plan.root / repair.EDGES_RELATIVE, repair.edge_id)
    after = keyed_output_lines(
        plan.outputs[plan.root / repair.EDGES_RELATIVE], repair.edge_id
    )
    removed = set(before) - set(after)
    added = set(after) - set(before)
    modified = {
        wanted for wanted in set(before) & set(after) if before[wanted][0] != after[wanted][0]
    }
    assert removed == set(repair.REMOVED_EDGE_IDS)
    assert added == set(repair.NEW_EDGE_IDS)
    assert modified == {repair.MODIFIED_EDGE_ID}
    assert all(
        before[wanted][1] == after[wanted][1]
        for wanted in set(before) & set(after) - {repair.MODIFIED_EDGE_ID}
    )
    assert before[repair.AG026_EDGE_ID][1] == after[repair.AG026_EDGE_ID][1]
    assert repair.canonical_hash(after[repair.AG026_EDGE_ID][0]) == (
        repair.AG026_BEFORE_HASH
    )
    assert after[repair.MODIFIED_EDGE_ID][0]["metadata"]["fragment_reference"] == "55K"
    authored = {
        str(row.get("target_id") or row.get("target"))
        for row, _line in after.values()
        if str(row.get("source_id") or row.get("source")) == repair.WORK_ID
        and row.get("relation") == "authored_by"
    }
    assert authored == {repair.LONG_ID, repair.SEDLEY_ID}
    position_creators = {
        str(row.get("target_id") or row.get("target"))
        for row, _line in after.values()
        if str(row.get("source_id") or row.get("source")) == repair.POSITION_ID
        and row.get("relation") == "created_by"
    }
    assert position_creators == {repair.LONG_ID}


def test_literature_builder_diff_is_bounded_and_reproducible(
    plan: repair.RepairPlan,
) -> None:
    before = (plan.root / repair.LITERATURE_BUILDER_RELATIVE).read_bytes()
    after = plan.outputs[plan.root / repair.LITERATURE_BUILDER_RELATIVE]
    expected = before.decode().replace(
        repair.OLD_LONG_BUILDER_BLOCK, repair.NEW_LONG_BUILDER_BLOCK
    ).encode()
    assert after == expected
    assert before.decode().count(repair.OLD_LONG_BUILDER_BLOCK) == 1
    assert repair.sha256_bytes(after) == repair.FILE_AFTER_SHA256[
        repair.LITERATURE_BUILDER_RELATIVE
    ]
    generated = repair.execute_candidate_literature_builder(after, plan.root)
    assert repair.serialize_jsonl(generated) == plan.outputs[
        plan.root / repair.LITERATURE_MANIFEST_RELATIVE
    ]
    baseline = {
        row["artifact_id"]: row
        for row in repair.read_jsonl(plan.root / repair.LITERATURE_MANIFEST_RELATIVE)
    }
    preview = {row["artifact_id"]: row for row in generated}
    assert {
        wanted for wanted in baseline if baseline[wanted] != preview[wanted]
    } == {repair.LITERATURE_ARTIFACT_ID}
    row = preview[repair.LITERATURE_ARTIFACT_ID]
    assert row["content_completeness"] == "full"
    assert row["content_completeness_scope"] == (
        "scholarly main content from title page through bibliography"
    )
    assert row["physical_completeness"] == "incomplete"
    assert row["manifestation_role"] == "source_scan"


def test_scholarly_manifest_and_registry_are_partial_and_open(
    plan: repair.RepairPlan,
) -> None:
    scholarly = output_rows(plan, repair.SCHOLARLY_MANIFEST_RELATIVE)
    row = next(
        item
        for item in scholarly
        if item.get("publication_dir") == repair.SCHOLARLY_PUBLICATION_DIR
    )
    assert row["year_original"] == 1987
    assert row["year_edition_used"] == 1998
    assert row["local_printing_year"] is None
    assert row["binding_status"] == "unknown_cover_absent"
    assert row["kg_ingestion_status"] == "partial"
    assert row["quotation_policy"] == "internal_pointers_and_paraphrases_only"

    sources = output_rows(plan, repair.SOURCES_RELATIVE)
    source = next(item for item in sources if item.get("source_id") == repair.SOURCE_ID)
    assert source["acquisition"]["status"] == "archived_verified"
    assert source["coverage"]["state"] == "partial"
    assert source["acquisition"]["manifest_publication_dirs"] == [
        repair.SCHOLARLY_PUBLICATION_DIR
    ]

    evidence = {
        item["evidence_id"]: item
        for item in output_rows(plan, repair.EVIDENCE_RELATIVE)
    }
    assert repair.OLD_FUSED_EVIDENCE_ID not in evidence
    assert set(repair.ALL_LS_EVIDENCE_IDS) <= set(evidence)
    assert evidence[repair.LS20_EVIDENCE_ID]["locator"]["printed_pages"] == {
        "start": 104,
        "end": 113,
    }
    assert evidence[repair.LS55_EVIDENCE_ID]["locator"]["printed_pages"] == {
        "start": 332,
        "end": 341,
    }
    assert evidence[repair.LS62_EVIDENCE_ID]["locator"]["printed_pages"] == {
        "start": 382,
        "end": 389,
    }
    for wanted in repair.ALL_LS_EVIDENCE_IDS:
        assert evidence[wanted]["claim_status"] == "in_review"
        assert evidence[wanted]["quotation"] == {
            "status": "paraphrase_only",
            "language": "eng",
        }
        assert "independent_review" in evidence[wanted]["required_verification"]

    issues = {
        item["issue_id"]: item for item in output_rows(plan, repair.ISSUES_RELATIVE)
    }
    assert all(issues[wanted]["status"] == "open" for wanted in repair.NEW_ISSUE_IDS)
    assert repair.SOURCE_ID not in issues[repair.ARCHIVE_GAP_ISSUE_ID]["affected_ids"]
    verifications = output_rows(plan, repair.VERIFICATIONS_RELATIVE)
    assert len(verifications) == 4
    assert {row["stage"] for row in verifications} == {"identity", "primary"}
    assert not any(
        row["stage"] in {"independent", "adversarial", "human_signoff"}
        for row in verifications
    )


def test_cary_bibtex_e2_and_corpus_are_byte_immutable(
    plan: repair.RepairPlan,
) -> None:
    assert not set(repair.IMMUTABLE_FILE_HASHES) & set(plan.summary["changed_paths"])
    for relative, expected in repair.IMMUTABLE_FILE_HASHES.items():
        assert repair.sha256_file(ROOT / relative) == expected
    cary = json.loads((ROOT / "data/kg/e2_patches/cary.json").read_text())
    patch = cary["patches"]["scholarly_argument_cary_hellenistic_positions_on_deter_6"]
    assert "102" in patch["quote_verbatim"] and "112" in patch["quote_verbatim"]
    assert patch["publication_id"].startswith("scholarly_work_cary_")


def test_quarantine_exactly_matches_actual_diff(plan: repair.RepairPlan) -> None:
    kinds = Counter(row["record_type"] for row in plan.quarantine)
    assert kinds == Counter(
        {
            "kg_node_before": 39,
            "kg_edge_removed": 13,
            "kg_edge_before": 1,
            "kg_edge_absence_before": 7,
            "literature_manifest_row_before": 1,
            "literature_builder_before_summary": 1,
            "scholarly_manifest_absence_before": 1,
            "registry_source_before": 1,
            "registry_evidence_before": 1,
            "registry_evidence_removed": 1,
            "registry_evidence_absence_before": 2,
            "registry_issue_before": 1,
            "registry_issue_absence_before": 3,
            "registry_wave_before": 1,
            "registry_verification_absence_before": 4,
        }
    )
    node_ids = {
        repair.node_id(row["record"])
        for row in plan.quarantine
        if row["record_type"] == "kg_node_before"
    }
    assert node_ids == set(repair.TOUCHED_NODE_IDS)
    edge_ids = {
        repair.edge_id(row["record"])
        for row in plan.quarantine
        if row["record_type"] == "kg_edge_removed"
    }
    assert edge_ids == set(repair.REMOVED_EDGE_IDS)
    absence = {
        row["edge_id"]
        for row in plan.quarantine
        if row["record_type"] == "kg_edge_absence_before"
    }
    assert absence == set(repair.NEW_EDGE_IDS)
    builder = next(
        row
        for row in plan.quarantine
        if row["record_type"] == "literature_builder_before_summary"
    )
    assert builder["file_sha256"] == repair.FILE_BEFORE_SHA256[
        repair.LITERATURE_BUILDER_RELATIVE
    ]


def symlink_children(source: Path, destination: Path, exclude: set[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if child.name in exclude:
            continue
        (destination / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )


def hardlink(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, destination)


def build_shadow(tmp_path: Path) -> Path:
    shadow = tmp_path / "repo"
    shadow.mkdir()
    (shadow / "docs").symlink_to(ROOT / "docs", target_is_directory=True)
    (shadow / "tests").symlink_to(ROOT / "tests", target_is_directory=True)

    scripts = shadow / "scripts"
    symlink_children(
        ROOT / "scripts",
        scripts,
        {Path(repair.LITERATURE_BUILDER_RELATIVE).name},
    )
    hardlink(
        ROOT / repair.LITERATURE_BUILDER_RELATIVE,
        shadow / repair.LITERATURE_BUILDER_RELATIVE,
    )

    data = shadow / "data"
    symlink_children(
        ROOT / "data",
        data,
        {"kg", "literature_acquisition", "scholarly_sources", "goals", "audit"},
    )

    kg = data / "kg"
    symlink_children(ROOT / "data/kg", kg, {"nodes.jsonl", "edges.jsonl"})
    hardlink(ROOT / repair.NODES_RELATIVE, shadow / repair.NODES_RELATIVE)
    hardlink(ROOT / repair.EDGES_RELATIVE, shadow / repair.EDGES_RELATIVE)

    literature = data / "literature_acquisition"
    symlink_children(
        ROOT / "data/literature_acquisition",
        literature,
        {"manifest.jsonl"},
    )
    hardlink(
        ROOT / repair.LITERATURE_MANIFEST_RELATIVE,
        shadow / repair.LITERATURE_MANIFEST_RELATIVE,
    )

    scholarly = data / "scholarly_sources"
    symlink_children(ROOT / "data/scholarly_sources", scholarly, {"manifest.jsonl"})
    hardlink(
        ROOT / repair.SCHOLARLY_MANIFEST_RELATIVE,
        shadow / repair.SCHOLARLY_MANIFEST_RELATIVE,
    )

    (data / "goals").mkdir()
    shutil.copytree(
        ROOT / "data/goals/sota",
        data / "goals/sota",
        copy_function=os.link,
    )

    audit = data / "audit"
    audit.mkdir()
    for child in (ROOT / "data/audit").iterdir():
        if child.name.startswith(".long_sedley_vol2_p0") or child.name in {
            Path(repair.REPORT_RELATIVE).name,
            Path(repair.QUARANTINE_RELATIVE).name,
        }:
            continue
        (audit / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    return shadow


def long_quarantine() -> list[dict]:
    return repair.read_jsonl(ROOT / repair.QUARANTINE_RELATIVE)


def dump_record(row: dict, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(row, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def reverse_jsonl_records(
    path: Path,
    *,
    key,
    replacements: dict[str, dict] | None = None,
    removals: set[str] | None = None,
    additions_after: tuple[str, list[dict]] | None = None,
    compact: bool = False,
) -> None:
    replacements = replacements or {}
    removals = removals or set()
    output: list[tuple[dict, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        identifier = str(key(row))
        if identifier in removals:
            continue
        if identifier in replacements:
            old = replacements[identifier]
            output.append((old, dump_record(old, compact=compact)))
        else:
            output.append((row, line))
    if additions_after is not None:
        anchor, additions = additions_after
        index = next(
            i for i, (row, _line) in enumerate(output) if str(key(row)) == anchor
        ) + 1
        output[index:index] = [
            (row, dump_record(row, compact=compact)) for row in additions
        ]
    replace_shadow_bytes(
        path, ("\n".join(line for _row, line in output) + "\n").encode("utf-8")
    )


def reconstruct_preapply_workspace(tmp_path: Path) -> Path:
    shadow = build_shadow(tmp_path)
    quarantine = long_quarantine()

    node_before = {
        repair.node_id(row["record"]): row["record"]
        for row in quarantine
        if row["record_type"] == "kg_node_before"
    }
    reverse_jsonl_records(
        shadow / repair.NODES_RELATIVE,
        key=repair.node_id,
        replacements=node_before,
    )

    edge_removed = [
        row["record"]
        for row in quarantine
        if row["record_type"] == "kg_edge_removed"
    ]
    edge_modified = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "kg_edge_before"
    )
    edge_absent = {
        row["edge_id"]
        for row in quarantine
        if row["record_type"] == "kg_edge_absence_before"
    }
    edge_items = [
        (json.loads(line), line)
        for line in (shadow / repair.EDGES_RELATIVE).read_text().splitlines()
        if line.strip()
    ]
    edge_items = [
        (row, line)
        for row, line in edge_items
        if repair.edge_id(row) not in edge_absent
    ]
    edge_items = [
        (
            edge_modified,
            dump_record(edge_modified),
        )
        if repair.edge_id(row) == repair.edge_id(edge_modified)
        else (row, line)
        for row, line in edge_items
    ]
    nodes = repair.read_jsonl(shadow / repair.NODES_RELATIVE)
    node_position = {repair.node_id(row): index for index, row in enumerate(nodes)}
    start = next(
        i
        for i, (row, _line) in enumerate(edge_items)
        if repair.edge_id(row).startswith("deepaudit-")
    )
    end = next(
        i
        for i, (row, _line) in enumerate(edge_items[start:], start)
        if repair.edge_id(row).startswith("deepaudit-passage_hegesippus")
    )
    collection_batch = edge_items[start:end] + [
        (row, dump_record(row)) for row in edge_removed
    ]
    collection_batch.sort(
        key=lambda item: node_position.get(
            str(item[0].get("source_id") or item[0].get("source")), 10**9
        )
    )
    edge_items = edge_items[:start] + collection_batch + edge_items[end:]
    replace_shadow_bytes(
        shadow / repair.EDGES_RELATIVE,
        ("\n".join(line for _row, line in edge_items) + "\n").encode("utf-8"),
    )

    builder_path = shadow / repair.LITERATURE_BUILDER_RELATIVE
    builder = builder_path.read_text(encoding="utf-8")
    assert builder.count(repair.NEW_LONG_BUILDER_BLOCK) == 1
    replace_shadow_bytes(
        builder_path,
        builder.replace(
            repair.NEW_LONG_BUILDER_BLOCK, repair.OLD_LONG_BUILDER_BLOCK
        ).encode("utf-8"),
    )

    literature_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "literature_manifest_row_before"
    )
    reverse_jsonl_records(
        shadow / repair.LITERATURE_MANIFEST_RELATIVE,
        key=lambda row: row.get("artifact_id"),
        replacements={literature_before["artifact_id"]: literature_before},
    )
    reverse_jsonl_records(
        shadow / repair.SCHOLARLY_MANIFEST_RELATIVE,
        key=lambda row: row.get("publication_dir"),
        removals={repair.SCHOLARLY_PUBLICATION_DIR},
    )

    source_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "registry_source_before"
    )
    reverse_jsonl_records(
        shadow / repair.SOURCES_RELATIVE,
        key=lambda row: row.get("source_id"),
        replacements={source_before["source_id"]: source_before},
        compact=True,
    )
    evidence_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "registry_evidence_before"
    )
    fused_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "registry_evidence_removed"
    )
    reverse_jsonl_records(
        shadow / repair.EVIDENCE_RELATIVE,
        key=lambda row: row.get("evidence_id"),
        replacements={evidence_before["evidence_id"]: evidence_before},
        removals={repair.LS55_EVIDENCE_ID, repair.LS62_EVIDENCE_ID},
        additions_after=(repair.LS20_EVIDENCE_ID, [fused_before]),
        compact=True,
    )
    issue_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "registry_issue_before"
    )
    reverse_jsonl_records(
        shadow / repair.ISSUES_RELATIVE,
        key=lambda row: row.get("issue_id"),
        replacements={issue_before["issue_id"]: issue_before},
        removals=set(repair.NEW_ISSUE_IDS),
        compact=True,
    )
    wave_before = next(
        row["record"]
        for row in quarantine
        if row["record_type"] == "registry_wave_before"
    )
    reverse_jsonl_records(
        shadow / repair.WAVES_RELATIVE,
        key=lambda row: row.get("wave_id"),
        replacements={wave_before["wave_id"]: wave_before},
        compact=True,
    )
    (shadow / repair.VERIFICATIONS_RELATIVE).unlink(missing_ok=True)

    return shadow


def replace_shadow_bytes(path: Path, payload: bytes) -> None:
    path.unlink(missing_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_full_registry_audit_accepts_preview(
    plan: repair.RepairPlan, tmp_path: Path
) -> None:
    from scripts.audit_sota_registry import audit_registry

    shadow = build_shadow(tmp_path)
    for path, payload in plan.outputs.items():
        replace_shadow_bytes(shadow / path.relative_to(plan.root), payload)
    report = audit_registry(shadow / "data/goals/sota", shadow)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["errors"] == []
    assert report["exit_ready"] is False


def test_copy_first_write_dry_run_and_repeat_are_truthful(tmp_path: Path) -> None:
    shadow = reconstruct_preapply_workspace(tmp_path)
    shadow_plan = build_prospective_plan(shadow)
    root_before = {
        relative: (
            (ROOT / relative).read_bytes() if (ROOT / relative).exists() else None
        )
        for relative in repair.FILE_BEFORE_SHA256
    }

    repair.apply_plan(shadow_plan)
    first = json.loads((shadow / repair.REPORT_RELATIVE).read_text())
    assert first["mode"] == "write"
    assert first["status"] == "applied_open_issues_pending_review"
    assert first["write_performed"] is True
    for relative, expected in repair.FILE_AFTER_SHA256.items():
        assert repair.sha256_file(shadow / relative) == expected
    assert repair.sha256_file(shadow / repair.LITERATURE_BUILDER_RELATIVE) == (
        repair.FILE_AFTER_SHA256[repair.LITERATURE_BUILDER_RELATIVE]
    )
    assert (shadow / repair.REPORT_RELATIVE).is_file()
    assert (shadow / repair.QUARANTINE_RELATIVE).is_file()

    applied_paths = [shadow / relative for relative in repair.FILE_AFTER_SHA256]
    applied_paths += [shadow / repair.REPORT_RELATIVE, shadow / repair.QUARANTINE_RELATIVE]
    applied_bytes = {path: path.read_bytes() for path in applied_paths}

    dry = repair.build_plan(shadow)
    assert dry.summary["status"] == "already_applied"
    assert dry.summary["write_performed"] is False
    assert dry.counts == Counter()

    repair.apply_plan(dry)
    assert {path: path.read_bytes() for path in applied_paths} == applied_bytes
    assert root_before == {
        relative: (
            (ROOT / relative).read_bytes() if (ROOT / relative).exists() else None
        )
        for relative in repair.FILE_BEFORE_SHA256
    }


def test_copy_hard_abort_after_builder_and_manifest_restores_snapshot_a(
    tmp_path: Path,
) -> None:
    shadow = reconstruct_preapply_workspace(tmp_path)
    shadow_plan = build_prospective_plan(shadow)
    before = {
        path: (path.read_bytes() if path.exists() else None)
        for path in shadow_plan.before_bytes
    }
    with pytest.raises(repair.InjectedTransactionAbort):
        repair.apply_plan(shadow_plan, fail_after=4)
    assert before == {
        path: (path.read_bytes() if path.exists() else None)
        for path in shadow_plan.before_bytes
    }
    assert not (shadow / repair.REPORT_RELATIVE).exists()
    assert not (shadow / repair.QUARANTINE_RELATIVE).exists()
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


def assert_scratch_absent(root: Path) -> None:
    journal, backup = repair.journal_paths(root)
    assert not journal.exists() and not backup.exists()


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


def test_transaction_hard_abort_restores_snapshot(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    with pytest.raises(repair.InjectedTransactionAbort):
        repair.transactional_replace(tmp_path, outputs, before, fail_after=1)
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_scratch_absent(tmp_path)


def test_rollback_failure_preserves_recovery_for_second_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_prepared_and_committed_recovery_states(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    journal = repair.prepare_transaction(tmp_path, outputs, before)
    first.write_bytes(b"external-after-prepare\n")
    assert journal["state"] == "prepared"
    assert repair.recover_transaction(tmp_path) == "prepared_stage_discarded"
    assert first.read_bytes() == b"external-after-prepare\n"
    first.write_bytes(before[first])

    journal = repair.prepare_transaction(tmp_path, outputs, before)
    journal_path, backup = repair.journal_paths(tmp_path)
    journal["state"] = "committing"
    repair.write_journal(journal_path, journal)
    for entry in journal["entries"]:
        target = tmp_path / entry["target"]
        repair.replace_path(backup / entry["staged"], target)
        repair.fsync_directory(target.parent)
        journal["committed_targets"].append(entry["target"])
        repair.write_journal(journal_path, journal)
    journal["state"] = "committed"
    repair.write_journal(journal_path, journal)
    assert repair.recover_transaction(tmp_path) == "completed_cleanup"
    assert first.read_bytes() == outputs[first]
    assert second.read_bytes() == outputs[second]
    assert_scratch_absent(tmp_path)


def test_live_long_records_are_applied_and_record_scoped_noop() -> None:
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

    literature = repair.read_jsonl(ROOT / repair.LITERATURE_MANIFEST_RELATIVE)
    builder = (ROOT / repair.LITERATURE_BUILDER_RELATIVE).read_bytes()
    builder_after, literature_after, literature_quarantine, literature_counts = (
        repair.transform_literature(ROOT, builder, literature, state="after")
    )
    assert builder_after == builder and literature_after == literature
    assert literature_quarantine == [] and literature_counts == Counter()

    scholarly = repair.read_jsonl(ROOT / repair.SCHOLARLY_MANIFEST_RELATIVE)
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
        "verifications": repair.read_jsonl(ROOT / repair.VERIFICATIONS_RELATIVE),
    }
    registry_after, registry_quarantine, registry_counts = repair.transform_registry(
        registry_before["sources"],
        registry_before["evidence"],
        registry_before["issues"],
        registry_before["waves"],
        registry_before["verifications"],
        state="after",
    )
    assert registry_after == registry_before
    assert registry_quarantine == [] and registry_counts == Counter()
    assert {path: path.read_bytes() for path in watched} == before
