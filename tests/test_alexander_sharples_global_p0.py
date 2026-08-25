from __future__ import annotations

import copy
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

import scripts.apply_2026_08_24_alexander_sharples_global_p0 as repair  # noqa: E402

EXPECTED_COUNTS = Counter(
    {
        "kg_nodes_modified": 15,
        "kg_edges_removed": 55,
        "kg_edges_modified": 1,
        "corpus_citations_downgraded": 31,
        "corpus_citations_removed": 2,
        "scholarly_manifest_rows_added": 1,
        "registry_sources_modified": 1,
        "registry_sources_added": 1,
        "registry_evidence_added": 14,
        "registry_issues_added": 2,
        "registry_waves_added": 1,
        "bib_entries_modified": 1,
        "bibtex_reports_modified": 1,
    }
)

EXPECTED_PATHS = {
    "data/kg/nodes.jsonl",
    "data/kg/edges.jsonl",
    "data/corpus/citations.jsonl",
    "data/kg/publications.bib",
    "data/kg/publications_bibtex_report.json",
    "data/scholarly_sources/manifest.jsonl",
    "data/goals/sota/registry/sources/seed_priority_20260824.jsonl",
    "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
    "data/goals/sota/registry/issues/seed_known_20260824.jsonl",
    "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl",
}


@pytest.fixture(scope="module")
def plan() -> repair.RepairPlan:
    return repair.build_plan(ROOT)


@pytest.fixture(scope="module")
def citability_policy():
    path = ROOT / "graphrag/src/eleutheria_graphrag/agents/citability.py"
    spec = importlib.util.spec_from_file_location("alex_sharples_policy", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def output_rows(plan: repair.RepairPlan, relative: str) -> list[dict]:
    return [
        json.loads(line)
        for line in plan.outputs[ROOT / relative].decode("utf-8").splitlines()
        if line.strip()
    ]


def node_map(plan: repair.RepairPlan) -> dict[str, dict]:
    return {
        repair.node_id(row): row for row in output_rows(plan, "data/kg/nodes.jsonl")
    }


def test_source_fixture_hashes_and_post_hildebrandt_tatian_snapshot_are_frozen(
    plan: repair.RepairPlan,
) -> None:
    source_expected = {
        repair.SCAN_RELATIVE: repair.SCAN_SHA256,
        repair.OCR_RELATIVE: repair.OCR_SHA256,
        repair.AUDIT_RELATIVE: repair.AUDIT_SHA256,
        repair.TEI_RELATIVE: repair.TEI_SHA256,
        repair.INDEPENDENT_REVIEW_V2_RELATIVE: (
            repair.INDEPENDENT_REVIEW_V2_SHA256
        ),
        **repair.BASE_AUDIT_ARTIFACT_SHA256,
    }
    for relative, sha256 in source_expected.items():
        assert repair.sha256_file(ROOT / relative) == sha256
    data_paths = {
        "nodes": "data/kg/nodes.jsonl",
        "edges": "data/kg/edges.jsonl",
        "citations": "data/corpus/citations.jsonl",
        "passages": "data/corpus/passages.jsonl",
        "corpus_manifest": "data/corpus/manifest.jsonl",
        "bib": "data/kg/publications.bib",
        "bib_report": "data/kg/publications_bibtex_report.json",
        "scholarly_manifest": "data/scholarly_sources/manifest.jsonl",
        "registry_sources": (
            "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
        ),
        "registry_evidence": (
            "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
        ),
        "registry_issues": (
            "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
        ),
        "registry_waves": (
            "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl"
        ),
    }
    expected_state = (
        repair.FROZEN_FILE_BEFORE_SHA256
        if plan.summary["input_state"] == "before"
        else repair.FROZEN_FILE_AFTER_SHA256
    )
    for label, relative in data_paths.items():
        path = ROOT / relative
        actual = repair.sha256_file(path) if path.is_file() else None
        assert actual == expected_state[label]


def test_dry_run_counts_paths_and_open_reviews(plan: repair.RepairPlan) -> None:
    assert plan.counts in (EXPECTED_COUNTS, Counter())
    if plan.counts:
        assert plan.summary["status"] == "ready_for_independent_review_no_apply"
        assert set(plan.summary["changed_paths"]) == EXPECTED_PATHS
        assert len(plan.quarantine) == 126
    else:
        assert plan.summary["status"] == "already_applied"
        assert plan.summary["changed_paths"] == []
    assert plan.summary["write_performed"] is False
    assert plan.summary["input_state"] in {"before", "after"}
    assert plan.summary["corpus_passage_files_modified"] == 0
    assert plan.summary["corpus_manifest_files_modified"] == 0
    assert plan.summary["readonly_snapshot_dependencies"] == {
        "data/corpus/passages.jsonl": repair.CORPUS_PASSAGES_SHA256,
        "data/corpus/manifest.jsonl": repair.CORPUS_MANIFEST_SHA256,
    }
    assert plan.summary["page_map_validation"] == {
        "evidence_intervals_checked": 14,
        "argument_intervals_checked": 24,
    }
    assert plan.summary["source_artifacts"]["prior_independent_v2_sha256"] == (
        repair.INDEPENDENT_REVIEW_V2_SHA256
    )
    assert plan.summary["source_artifacts"][
        "post_hildebrandt_tatian_base_artifacts"
    ] == repair.BASE_AUDIT_ARTIFACT_SHA256
    gates = plan.summary["integrity_gates"]
    assert gates["new_snapshot_fingerprints"] == 0
    assert gates["new_corpus_violations"] == 0
    assert gates["parity_violations"] == 0
    assert gates["work_child_mismatches"] == 0
    assert gates["work_id_collisions"] == 0
    assert plan.summary["reviews"] == {
        "primary_visual_audit": "recorded_as_input_report",
        "independent": "not_performed_not_recorded",
        "adversarial": "not_performed_not_recorded",
        "human_signoff": "not_performed_not_recorded",
    }
    debt = plan.summary["measured_baseline"]["strict_ingestion_debt"]
    assert debt["new_block_debt"] == 0
    assert debt["new_warn_debt"] == 0


def test_every_sharples_page_map_is_derived_from_the_verified_spread_rule() -> None:
    assert repair.validate_page_maps() == {
        "evidence_intervals_checked": 14,
        "argument_intervals_checked": 24,
    }
    for spec in repair.EVIDENCE_SPECS:
        assert spec["pdf"] == repair.spread_pdf_range(spec["printed"])
    for spec in repair.ARGUMENT_SPECS.values():
        printed = repair.parse_page_ranges(spec["printed"])
        pdf = repair.parse_page_ranges(spec["pdf"])
        assert pdf == [repair.spread_pdf_range(interval) for interval in printed]
    evidence = dict(zip(repair.EVIDENCE_IDS, repair.EVIDENCE_SPECS, strict=True))
    assert evidence["ev_sec_sharples_1983_sha01"]["pdf"] == (14, 15)
    assert evidence["ev_sec_sharples_1983_sha06"]["pdf"] == (78, 79)
    assert evidence["ev_sec_sharples_1983_sha09"]["pdf"] == (78, 79)
    assert evidence["ev_sec_sharples_1983_sha12"]["pdf"] == (81, 81)
    assert repair.ARGUMENT_SPECS[repair.DELIBERATION_ID]["pdf"].startswith("33-35")


def test_exact_node_touched_set_and_long_safe_nodes_are_byte_immutable(
    plan: repair.RepairPlan,
) -> None:
    before_lines = {
        repair.node_id(json.loads(line)): line
        for line in (ROOT / "data/kg/nodes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    after_lines = {
        repair.node_id(json.loads(line)): line
        for line in plan.outputs[ROOT / "data/kg/nodes.jsonl"].decode().splitlines()
        if line.strip()
    }
    changed = {
        identifier
        for identifier in before_lines
        if repair.canonical_hash(json.loads(before_lines[identifier]))
        != repair.canonical_hash(json.loads(after_lines[identifier]))
    }
    assert changed == (set(repair.TOUCHED_NODE_IDS) if plan.counts else set())
    for identifier in before_lines.keys() - repair.TOUCHED_NODE_IDS:
        assert after_lines[identifier] == before_lines[identifier]
    for identifier in repair.LONG_OVERLAP_NODE_IDS | {repair.SAFE_AGENT_ID}:
        assert after_lines[identifier] == before_lines[identifier]
    if plan.counts:
        for identifier in repair.TOUCHED_NODE_IDS:
            assert repair.canonical_hash(json.loads(before_lines[identifier])) == (
                repair.NODE_BEFORE_HASHES[identifier]
            )
            assert repair.canonical_hash(json.loads(after_lines[identifier])) == (
                repair.NODE_AFTER_HASHES[identifier]
            )


def test_strong_nodes_are_layered_and_runtime_discovery_only(
    plan: repair.RepairPlan, citability_policy
) -> None:
    nodes = node_map(plan)
    for identifier in repair.STRONG_ARGUMENT_IDS:
        node = nodes[identifier]
        data = repair.metadata(node)
        assert node["label"].startswith("Legacy reconstruction (discovery only):")
        assert data["citability"] == "discoverable_only"
        assert data["needs_evidence"] is True
        assert data["canonical_claim_node"] == repair.SAFE_AGENT_ID
        assert {layer["claim_role"] for layer in data["claim_layers"]} == {
            "direct_alexander_text_candidate",
            "reported_stoic_position",
            "sharples_1983_interpretation",
            "modern_reconstruction",
        }
        assert not data.get("premises") and not data.get("legacy_premises")
        assert data["conclusion"]["primary_sources"] == []
        assert "citation_verified" not in data and "verified_reference" not in data
        decision = citability_policy.evidence_policy(node)
        assert decision.tier is citability_policy.CitabilityTier.DISCOVERABLE_ONLY
    assert citability_policy.evidence_policy(nodes[repair.SAFE_AGENT_ID]).tier is (
        citability_policy.CitabilityTier.CITABLE
    )


def test_work_publication_and_de_fato15_duplicates_are_fail_closed(
    plan: repair.RepairPlan, citability_policy
) -> None:
    nodes = node_map(plan)
    publication = nodes[repair.PUBLICATION_ID]
    pub_data = repair.metadata(publication)
    assert pub_data["publication_role"] == (
        "translation_commentary_with_photographic_bruns_facsimile"
    )
    assert pub_data["publisher"] == "Gerald Duckworth & Co. Ltd."
    assert pub_data["address"] == "London"
    assert pub_data["isbns_by_binding"] == {
        "cased": "0-7156-1589-0",
        "paper": "0-7156-1739-7",
    }
    assert "not a newly constituted standard critical edition" in (
        publication["description"].lower()
    )
    assert "photographic" in publication["description"].lower()
    work = nodes[repair.WORK_ID]
    assert "chapters II-VI" in work["description"]
    assert "chapters VII-XXXVIII" in work["description"]
    assert "ultimate" not in work["description"].lower()
    assert citability_policy.evidence_policy(work).tier is (
        citability_policy.CitabilityTier.DISCOVERABLE_ONLY
    )
    greek = nodes[repair.LEGACY_PASSAGE_ID]
    english = nodes[repair.LEGACY_PASSAGE_EN_ID]
    assert repair.metadata(greek)["exact_twin_status"] == "rejected"
    assert repair.metadata(greek)["canonical_candidate_node_id"] == (
        repair.CANONICAL_PASSAGE_15
    )
    assert repair.metadata(english)["translation_type"] == "machine"
    assert citability_policy.evidence_policy(english).tier is (
        citability_policy.CitabilityTier.BLOCKED
    )


def test_edges_exactly_remove_55_and_modify_only_publication_work(
    plan: repair.RepairPlan,
) -> None:
    before_lines = {
        repair.edge_id(json.loads(line)): line
        for line in (ROOT / "data/kg/edges.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    after_lines = {
        repair.edge_id(json.loads(line)): line
        for line in plan.outputs[ROOT / "data/kg/edges.jsonl"].decode().splitlines()
        if line.strip()
    }
    removed = before_lines.keys() - after_lines.keys()
    modified = {
        identifier
        for identifier in before_lines.keys() & after_lines.keys()
        if before_lines[identifier] != after_lines[identifier]
    }
    if plan.counts:
        assert len(removed) == 55
        assert modified == {repair.PUBLICATION_WORK_EDGE_ID}
        assert removed | modified == set(plan.summary["touched_edge_ids"])
        old_cohort = [
            json.loads(before_lines[identifier]) for identifier in removed | modified
        ]
        assert repair.edge_cohort_digest(old_cohort) == (
            repair.EDGE_BEFORE_COHORT_SHA256
        )
    else:
        assert removed == set() and modified == set()
    for identifier in after_lines.keys() - {repair.PUBLICATION_WORK_EDGE_ID}:
        if identifier in before_lines and identifier not in removed:
            assert after_lines[identifier] == before_lines[identifier]
    assert not any(
        repair.old_support_edge(json.loads(line)) for line in after_lines.values()
    )


def test_citations_exactly_downgrade_31_remove_two_and_preserve_every_other_row(
    plan: repair.RepairPlan, citability_policy
) -> None:
    live = repair.read_jsonl(ROOT / "data/corpus/citations.jsonl")
    after = output_rows(plan, "data/corpus/citations.jsonl")
    if plan.counts:
        before = live
        old_cohort = [
            row
            for row in before
            if repair.old_strong_citation(row)
            or repair.legacy_snapshot_citation(row)
        ]
    else:
        quarantine = repair.read_jsonl(ROOT / repair.QUARANTINE_RELATIVE)
        old_cohort = [
            row["record"]
            for row in quarantine
            if row.get("record_type")
            in {"corpus_citation_before", "corpus_citation_removed"}
        ]
        before = old_cohort
    assert len(old_cohort) == 33
    assert repair.citation_cohort_digest(old_cohort) == (
        repair.CITATION_BEFORE_COHORT_SHA256
    )
    after_applied = [
        row
        for row in after
        if row.get(repair.STAMP) is True
        and row.get("kg_node_id") in repair.STRONG_ARGUMENT_IDS
    ]
    assert len(after_applied) == 31
    assert all(row["citation_type"] == "related_passage_non_exact" for row in after_applied)
    assert all(
        citability_policy.evidence_policy(row).tier
        is citability_policy.CitabilityTier.DISCOVERABLE_ONLY
        for row in after_applied
    )
    assert not any(repair.legacy_snapshot_citation(row) for row in after)
    if plan.counts:
        before_untouched = [row for row in before if row not in old_cohort]
        after_untouched = [row for row in after if row.get(repair.STAMP) is not True]
        assert {repair.citation_key(row): row for row in after_untouched} == {
            repair.citation_key(row): row for row in before_untouched
        }
    else:
        assert repair.sha256_file(ROOT / "data/corpus/citations.jsonl") == (
            repair.FROZEN_FILE_AFTER_SHA256["citations"]
        )


def test_corpus_dependencies_are_snapshot_gated_but_not_written(
    plan: repair.RepairPlan,
) -> None:
    assert {path.relative_to(ROOT).as_posix() for path in plan.outputs} == EXPECTED_PATHS
    assert "data/corpus/passages.jsonl" not in EXPECTED_PATHS
    assert "data/corpus/manifest.jsonl" not in EXPECTED_PATHS
    passages = ROOT / "data/corpus/passages.jsonl"
    manifest = ROOT / "data/corpus/manifest.jsonl"
    assert plan.before_bytes[passages] == passages.read_bytes()
    assert plan.before_bytes[manifest] == manifest.read_bytes()
    assert repair.sha256_file(passages) == repair.CORPUS_PASSAGES_SHA256
    assert repair.sha256_file(manifest) == repair.CORPUS_MANIFEST_SHA256


def test_prospective_snapshot_corpus_parity_and_work_gates_do_not_grow(
    plan: repair.RepairPlan,
) -> None:
    from scripts.check_corpus_invariants import find_violations as corpus_violations
    from scripts.check_kg_corpus_locus_parity import (
        find_violations as parity_violations,
    )
    from scripts.check_kg_work_child_canonical import find_mismatches
    from scripts.check_kg_work_id_uniqueness import collect_work_groups, find_collisions
    from scripts.check_snapshot_passage_integrity import audit_integrity

    before_nodes = repair.read_jsonl(ROOT / "data/kg/nodes.jsonl")
    before_edges = repair.read_jsonl(ROOT / "data/kg/edges.jsonl")
    before_citations = repair.read_jsonl(ROOT / "data/corpus/citations.jsonl")
    passages = repair.read_jsonl(ROOT / "data/corpus/passages.jsonl")
    manifest = repair.read_jsonl(ROOT / "data/corpus/manifest.jsonl")
    after_nodes = output_rows(plan, "data/kg/nodes.jsonl")
    after_edges = output_rows(plan, "data/kg/edges.jsonl")
    after_citations = output_rows(plan, "data/corpus/citations.jsonl")

    before_snapshot = {row["fingerprint"] for row in audit_integrity(before_nodes, passages, before_citations)}
    after_snapshot = audit_integrity(after_nodes, passages, after_citations)
    assert {row["fingerprint"] for row in after_snapshot} - before_snapshot == set()
    before_corpus = corpus_violations(before_nodes, passages, before_citations)
    after_corpus = corpus_violations(after_nodes, passages, after_citations)
    for category in before_corpus.keys() | after_corpus.keys():
        before_rows = {
            (
                str(row.get("node_id") or row.get("id") or row.get("kg_node_id") or ""),
                str(row.get("passage_id") or ""),
                str(row.get("citation_type") or ""),
            )
            for row in before_corpus.get(category, [])
        }
        after_rows = {
            (
                str(row.get("node_id") or row.get("id") or row.get("kg_node_id") or ""),
                str(row.get("passage_id") or ""),
                str(row.get("citation_type") or ""),
            )
            for row in after_corpus.get(category, [])
        }
        assert after_rows - before_rows == set()
    _shared, parity = parity_violations(after_nodes, passages, after_citations)
    assert parity == []
    assert find_mismatches(after_nodes, after_edges, manifest) == []
    assert find_collisions(collect_work_groups(after_nodes, after_edges)) == []
    # The baseline gates are already clean; edge removal must not invent work debt.
    assert len(after_edges) == len(before_edges) - (55 if plan.counts else 0)


def test_scholarly_manifest_and_secondary_source_are_distinct_from_ancient_source(
    plan: repair.RepairPlan,
) -> None:
    manifest = next(
        row
        for row in output_rows(plan, "data/scholarly_sources/manifest.jsonl")
        if row.get("publication_dir") == repair.SCHOLARLY_DIR
    )
    assert manifest["year_edition_used"] == 1983
    assert manifest["page_count"] == 161
    assert manifest["pdf_sha256"] == repair.SCAN_SHA256
    assert manifest["ocr_pdf_sha256"] == repair.OCR_SHA256
    assert manifest["reuse_status"] == "unverified_do_not_republish"
    sources = {
        row["source_id"]: row
        for row in output_rows(
            plan, "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
        )
    }
    ancient = sources[repair.ANCIENT_SOURCE_ID]
    secondary = sources[repair.SECONDARY_SOURCE_ID]
    assert all(
        artifact["locator"] == repair.TEI_RELATIVE
        for artifact in ancient["acquisition"]["artifacts"]
    )
    assert secondary["source_kind"] == "secondary_publication"
    assert secondary["coverage"]["state"] == "partial"
    assert secondary["acquisition"]["manifest_publication_dirs"] == [
        repair.SCHOLARLY_DIR
    ]
    assert "not a new critical edition" in secondary["notes"]


def test_registry_evidence_issues_wave_are_open_and_normative(plan: repair.RepairPlan) -> None:
    evidence = {
        row["evidence_id"]: row
        for row in output_rows(
            plan, "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
        )
        if row.get("evidence_id") in repair.EVIDENCE_IDS
    }
    assert set(evidence) == set(repair.EVIDENCE_IDS)
    assert all(row["claim_status"] == "in_review" for row in evidence.values())
    assert all(row["quotation"]["status"] == "paraphrase_only" for row in evidence.values())
    issues = {
        row["issue_id"]: row
        for row in output_rows(
            plan, "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
        )
        if row.get("issue_id") in {repair.GLOBAL_ISSUE_ID, repair.TEXT_DEBT_ISSUE_ID}
    }
    assert set(issues) == {repair.GLOBAL_ISSUE_ID, repair.TEXT_DEBT_ISSUE_ID}
    assert {row["status"] for row in issues.values()} == {"open"}
    assert repair.OLD_LOCAL_ISSUE_ID in issues[repair.GLOBAL_ISSUE_ID]["affected_ids"]
    wave = output_rows(
        plan, "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl"
    )
    assert wave == [repair.wave_record()]
    assert wave[0]["status"] == "blocked"


def test_normative_registry_schema_has_zero_new_errors(plan: repair.RepairPlan) -> None:
    from jsonschema import Draft7Validator

    schema = json.loads(
        (ROOT / "data/goals/sota/registry.schema.json").read_text(encoding="utf-8")
    )
    configs = {
        "source": ("sources", "source_id", "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"),
        "evidence": ("evidence", "evidence_id", "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"),
        "issue": ("issues", "issue_id", "data/goals/sota/registry/issues/seed_known_20260824.jsonl"),
        "verification": ("verifications", "verification_id", None),
        "wave": ("waves", "wave_id", "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl"),
    }
    before: dict[str, dict[str, dict]] = {}
    after: dict[str, dict[str, dict]] = {}
    registry = ROOT / "data/goals/sota/registry"
    for record_type, (directory, key, relative) in configs.items():
        rows = []
        for path in sorted((registry / directory).glob("*.jsonl")):
            rows.extend(repair.read_jsonl(path))
        before[record_type] = {str(row[key]): row for row in rows}
        after[record_type] = copy.deepcopy(before[record_type])
        if relative:
            for row in output_rows(plan, relative):
                after[record_type][str(row[key])] = row
    validators = {
        record_type: Draft7Validator(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "$defs": schema["$defs"],
                "$ref": f"#/$defs/{record_type}",
            }
        )
        for record_type in configs
    }

    def errors(collections) -> set[tuple]:
        found = set()
        for record_type, rows in collections.items():
            for identifier, row in rows.items():
                for error in validators[record_type].iter_errors(row):
                    found.add(
                        (
                            record_type,
                            identifier,
                            tuple(error.absolute_path),
                            error.validator,
                            error.message,
                        )
                    )
        return found

    before_errors = errors(before)
    after_errors = errors(after)
    assert len(before_errors) == 41
    assert after_errors - before_errors == set()


def test_bibtex_and_companion_report_are_atomic_and_reproducible(
    plan: repair.RepairPlan,
) -> None:
    from scripts.export_publications_bibtex import build_companion_report

    bib = plan.outputs[ROOT / "data/kg/publications.bib"].decode("utf-8")
    nodes = output_rows(plan, "data/kg/nodes.jsonl")
    publication = next(row for row in nodes if repair.node_id(row) == repair.PUBLICATION_ID)
    desired_entry = repair.canonical_publication_bibtex(publication)
    assert desired_entry in bib
    assert repair.OLD_BIB_ENTRY not in bib
    assert "Gerald Duckworth & Co. Ltd." in desired_entry
    assert "photographic" not in desired_entry  # role belongs in node/source, not invented Bib field
    report = json.loads(
        plan.outputs[ROOT / "data/kg/publications_bibtex_report.json"].decode("utf-8")
    )
    expected = build_companion_report(
        nodes,
        bib,
        generation_mode="alexander_sharples_global_surgical_snapshot_transform",
        baseline_bibtex_sha256=repair.BIB_BEFORE_SHA256,
    )
    assert report == expected
    assert report["bibtex_sha256"] == repair.sha256_bytes(bib.encode("utf-8"))


def test_quarantine_exact_inventory(plan: repair.RepairPlan) -> None:
    quarantine = (
        plan.quarantine
        if plan.counts
        else repair.read_jsonl(ROOT / repair.QUARANTINE_RELATIVE)
    )
    assert Counter(row["record_type"] for row in quarantine) == Counter(
        {
            "kg_node_before": 15,
            "kg_edge_removed": 55,
            "kg_edge_before": 1,
            "corpus_citation_before": 31,
            "corpus_citation_removed": 2,
            "scholarly_manifest_absence_before": 1,
            "registry_source_before": 1,
            "registry_source_absence_before": 1,
            "registry_evidence_absence_before": 14,
            "registry_issue_absence_before": 2,
            "registry_wave_absence_before": 1,
            "bib_entry_before": 1,
            "bibtex_report_before_summary": 1,
        }
    )


def test_reviewed_before_images_replay_core_transforms_after_write(
    plan: repair.RepairPlan,
) -> None:
    quarantine = (
        plan.quarantine
        if plan.counts
        else repair.read_jsonl(ROOT / repair.QUARANTINE_RELATIVE)
    )
    current_nodes = {
        repair.node_id(row): row
        for row in repair.read_jsonl(ROOT / "data/kg/nodes.jsonl")
    }
    before_nodes = [
        row["record"] for row in quarantine if row.get("record_type") == "kg_node_before"
    ]
    before_nodes.append(current_nodes[repair.SAFE_AGENT_ID])
    replayed_nodes = {
        repair.node_id(row): row for row in repair.transform_nodes(before_nodes)[0]
    }
    for identifier in repair.TOUCHED_NODE_IDS:
        wanted = (
            node_map(plan)[identifier]
            if plan.counts
            else current_nodes[identifier]
        )
        assert replayed_nodes[identifier] == wanted

    before_edges = [
        row["record"]
        for row in quarantine
        if row.get("record_type") in {"kg_edge_removed", "kg_edge_before"}
    ]
    replayed_edges = {repair.edge_id(row): row for row in repair.transform_edges(before_edges)[0]}
    current_edges = {
        repair.edge_id(row): row
        for row in output_rows(plan, "data/kg/edges.jsonl")
    }
    assert replayed_edges == {
        repair.PUBLICATION_WORK_EDGE_ID: current_edges[repair.PUBLICATION_WORK_EDGE_ID]
    }

    before_citations = [
        row["record"]
        for row in quarantine
        if row.get("record_type")
        in {"corpus_citation_before", "corpus_citation_removed"}
    ]
    replayed_citations = {
        repair.citation_key(row): row
        for row in repair.transform_citations(before_citations)[0]
    }
    current_citations = {
        repair.citation_key(row): row
        for row in output_rows(plan, "data/corpus/citations.jsonl")
        if row.get(repair.STAMP) is True
        and row.get("kg_node_id") in repair.STRONG_ARGUMENT_IDS
    }
    assert replayed_citations == current_citations


def test_transform_layers_are_idempotent() -> None:
    nodes = repair.transform_nodes(repair.read_jsonl(ROOT / "data/kg/nodes.jsonl"))[0]
    assert repair.transform_nodes(nodes)[2] == Counter()
    edges = repair.transform_edges(repair.read_jsonl(ROOT / "data/kg/edges.jsonl"))[0]
    assert repair.transform_edges(edges)[2] == Counter()
    citations = repair.transform_citations(
        repair.read_jsonl(ROOT / "data/corpus/citations.jsonl")
    )[0]
    assert repair.transform_citations(citations)[2] == Counter()


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


def assert_transaction_clean(root: Path) -> None:
    journal, backups = repair.journal_paths(root)
    assert not journal.exists() and not backups.exists()


def test_precommit_drift_preserves_external_writer(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)

    def drift() -> None:
        second.write_bytes(b"external\n")

    with pytest.raises(repair.PreconditionsError, match="pre-commit snapshot drift"):
        repair.transactional_replace(tmp_path, outputs, before, before_commit_hook=drift)
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == b"external\n"
    assert_transaction_clean(tmp_path)


def test_readonly_dependency_drift_aborts_before_commit_and_is_preserved(
    tmp_path: Path,
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    dependency = tmp_path / "live" / "corpus-passages.jsonl"
    dependency.write_bytes(b"corpus-before\n")
    before[dependency] = dependency.read_bytes()

    def drift_dependency() -> None:
        dependency.write_bytes(b"external-corpus-change\n")

    with pytest.raises(repair.PreconditionsError, match="pre-commit snapshot drift"):
        repair.transactional_replace(
            tmp_path,
            outputs,
            before,
            before_commit_hook=drift_dependency,
        )
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert dependency.read_bytes() == b"external-corpus-change\n"
    assert_transaction_clean(tmp_path)


def test_interwindow_target_drift_is_never_overwritten_by_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_replace = os.replace
    injected = False

    def replace_then_drift(source: Path, destination: Path) -> None:
        nonlocal injected
        real_replace(source, destination)
        if Path(destination) == first and not injected:
            injected = True
            second.write_bytes(b"external-between-replaces\n")

    monkeypatch.setattr(repair, "replace_path", replace_then_drift)
    with pytest.raises(
        repair.PreconditionsError,
        match="refusing to overwrite foreign bytes during.*rollback",
    ):
        repair.transactional_replace(tmp_path, outputs, before)
    assert injected is True
    assert first.read_bytes() == outputs[first]
    assert second.read_bytes() == b"external-between-replaces\n"
    journal, backups = repair.journal_paths(tmp_path)
    assert journal.is_file() and backups.is_dir()
    assert json.loads(journal.read_text(encoding="utf-8"))["state"] == "rolling_back"


def test_hard_crash_journal_recovers_partial_commit(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    journal = repair.prepare_transaction(tmp_path, outputs, before)
    journal_path, backup_dir = repair.journal_paths(tmp_path)
    journal["state"] = "committing"
    repair.write_journal(journal_path, journal)
    entry = journal["entries"][0]
    repair.replace_path(backup_dir / entry["stage"], tmp_path / entry["target"])
    repair.fsync_directory((tmp_path / entry["target"]).parent)
    journal["committed_targets"].append(entry["target"])
    repair.write_journal(journal_path, journal)
    assert repair.recover_transaction(tmp_path) == "partial_commit_rolled_back"
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_clean(tmp_path)


def test_rollback_failure_retains_durable_material_and_second_recovery_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_replace = os.replace
    commit_failed = False
    rollback_failed = False

    def flaky(source: Path, destination: Path) -> None:
        nonlocal commit_failed, rollback_failed
        target = Path(destination)
        if target == second and not commit_failed:
            commit_failed = True
            raise OSError("commit failure")
        if target == first and commit_failed and not rollback_failed:
            rollback_failed = True
            raise OSError("rollback failure")
        real_replace(source, destination)

    monkeypatch.setattr(repair, "replace_path", flaky)
    with pytest.raises(OSError, match="rollback failure"):
        repair.transactional_replace(tmp_path, outputs, before)
    journal, backups = repair.journal_paths(tmp_path)
    assert journal.is_file() and backups.is_dir()
    monkeypatch.setattr(repair, "replace_path", real_replace)
    assert repair.recover_transaction(tmp_path) == "partial_commit_rolled_back"
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_clean(tmp_path)


def make_shadow_repo(tmp_path: Path) -> Path:
    shadow = tmp_path / "repo"
    shadow.mkdir()
    for child in ROOT.iterdir():
        if child.name in {".git", "data"}:
            continue
        (shadow / child.name).symlink_to(child, target_is_directory=child.is_dir())
    data = shadow / "data"
    data.mkdir()
    for child in (ROOT / "data").iterdir():
        if child.name in {"audit", "corpus", "goals", "kg", "scholarly_sources"}:
            continue
        (data / child.name).symlink_to(child, target_is_directory=child.is_dir())
    audit = data / "audit"
    audit.mkdir()
    excluded = {
        Path(repair.REPAIR_REPORT_RELATIVE).name,
        Path(repair.QUARANTINE_RELATIVE).name,
        Path(repair.LOCK_RELATIVE).name,
        Path(repair.JOURNAL_RELATIVE).name,
        Path(repair.BACKUP_DIR_RELATIVE).name,
    }
    persisted_audit = {
        Path(repair.REPAIR_REPORT_RELATIVE).name,
        Path(repair.QUARANTINE_RELATIVE).name,
    }
    for child in (ROOT / "data/audit").iterdir():
        if child.name in persisted_audit:
            shutil.copy2(child, audit / child.name)
        elif child.name not in excluded:
            (audit / child.name).symlink_to(child, target_is_directory=child.is_dir())
    kg = data / "kg"
    kg.mkdir()
    for child in (ROOT / "data/kg").iterdir():
        target = kg / child.name
        if child.name in {"nodes.jsonl", "edges.jsonl", "publications.bib", "publications_bibtex_report.json"}:
            shutil.copy2(child, target)
        else:
            target.symlink_to(child, target_is_directory=child.is_dir())
    corpus = data / "corpus"
    corpus.mkdir()
    for child in (ROOT / "data/corpus").iterdir():
        target = corpus / child.name
        if child.name in {"citations.jsonl", "passages.jsonl", "manifest.jsonl"}:
            shutil.copy2(child, target)
        else:
            target.symlink_to(child, target_is_directory=child.is_dir())
    scholarly = data / "scholarly_sources"
    scholarly.mkdir()
    for child in (ROOT / "data/scholarly_sources").iterdir():
        target = scholarly / child.name
        if child.name == "manifest.jsonl":
            shutil.copy2(child, target)
        else:
            target.symlink_to(child, target_is_directory=child.is_dir())
    goals = data / "goals"
    goals.mkdir()
    shutil.copytree(ROOT / "data/goals/sota", goals / "sota")
    return shadow


def test_full_copy_apply_is_idempotent_and_postwrite_hash_exact(
    tmp_path: Path,
) -> None:
    shadow = make_shadow_repo(tmp_path)
    plan = repair.build_plan(shadow)
    expected = plan.summary["output_sha256_preview"]
    repair.apply_plan(plan)
    for relative, sha256 in expected.items():
        assert repair.sha256_file(shadow / relative) == sha256
    second = repair.build_plan(shadow)
    assert second.counts == Counter()
    assert second.summary["status"] == "already_applied"
    assert second.summary["input_state"] == "after"
    assert second.summary["integrity_gates"]["new_snapshot_fingerprints"] == 0
    assert second.summary["integrity_gates"]["new_corpus_violations"] == 0
    for label, expected_hash in repair.FROZEN_FILE_AFTER_SHA256.items():
        path = {
            "nodes": shadow / "data/kg/nodes.jsonl",
            "edges": shadow / "data/kg/edges.jsonl",
            "citations": shadow / "data/corpus/citations.jsonl",
            "passages": shadow / "data/corpus/passages.jsonl",
            "corpus_manifest": shadow / "data/corpus/manifest.jsonl",
            "bib": shadow / "data/kg/publications.bib",
            "bib_report": shadow / "data/kg/publications_bibtex_report.json",
            "scholarly_manifest": shadow / "data/scholarly_sources/manifest.jsonl",
            "registry_sources": shadow
            / "data/goals/sota/registry/sources/seed_priority_20260824.jsonl",
            "registry_evidence": shadow
            / "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
            "registry_issues": shadow
            / "data/goals/sota/registry/issues/seed_known_20260824.jsonl",
            "registry_waves": shadow
            / "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl",
        }[label]
        assert (repair.sha256_file(path) if path.is_file() else None) == expected_hash
    repeated = repair.locked_write(shadow)
    assert repeated.counts == Counter()
    assert repair.cli_summary(shadow, repeated, write_requested=True)["status"] == (
        "already_applied"
    )
    assert (shadow / repair.REPAIR_REPORT_RELATIVE).is_file()
    assert (shadow / repair.QUARANTINE_RELATIVE).is_file()


def test_production_write_requires_explicit_approval() -> None:
    assert "intentionally unavailable" not in (repair.__doc__ or "")
    assert "--production-write-approved" in (repair.__doc__ or "")
    with pytest.raises(SystemExit):
        repair.main(["--write", "--root", str(ROOT)])


def test_cli_help_matches_the_review_and_approval_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        repair.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "apply the reviewed local transaction" in help_text
    assert "explicit root authorization" in help_text
