from __future__ import annotations

import copy
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

import scripts.apply_2026_08_24_sorabji_p0_repair as repair  # noqa: E402

EXPECTED_COUNTS = Counter(
    {
        "kg_nodes_modified": 11,
        "kg_edges_removed": 2,
        "bib_entries_modified": 1,
        "bibtex_reports_modified": 1,
        "e2_patch_modified": 1,
        "scholarly_manifest_rows_added": 1,
        "registry_sources_modified": 1,
        "registry_evidence_modified": 2,
        "registry_evidence_added": 5,
        "registry_issues_added": 2,
        "registry_waves_modified": 1,
        "registry_primary_verifications_added": 8,
    }
)

EXPECTED_CHANGED_PATHS = {
    "data/kg/nodes.jsonl",
    "data/kg/edges.jsonl",
    "data/kg/publications.bib",
    "data/kg/publications_bibtex_report.json",
    "data/kg/e2_patches/sorabji.json",
    "data/scholarly_sources/manifest.jsonl",
    "data/goals/sota/registry/sources/seed_priority_20260824.jsonl",
    "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
    "data/goals/sota/registry/issues/seed_known_20260824.jsonl",
    "data/goals/sota/registry/waves/priority_20260824.jsonl",
    "data/goals/sota/registry/verifications/sorabji_20260824.jsonl",
}


@pytest.fixture(scope="module")
def post_sorabji_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return a composable post-Sorabji view over the advanced live repository."""

    return build_post_sorabji_shadow(
        tmp_path_factory.mktemp("sorabji-postwrite")
    )


@pytest.fixture(scope="module")
def plan(post_sorabji_root: Path) -> repair.RepairPlan:
    return repair.build_plan(post_sorabji_root)


@pytest.fixture(scope="module")
def true_citability_policy():
    path = (
        ROOT
        / "graphrag/src/eleutheria_graphrag/agents/citability.py"
    )
    spec = importlib.util.spec_from_file_location("sorabji_true_citability", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def output_rows(plan: repair.RepairPlan, relative: str) -> list[dict]:
    payload = plan.outputs[plan.root / relative].decode("utf-8")
    return [json.loads(line) for line in payload.splitlines() if line.strip()]


def planned_nodes(plan: repair.RepairPlan) -> dict[str, dict]:
    return {
        repair.node_id(row): row
        for row in output_rows(plan, "data/kg/nodes.jsonl")
    }


def find_generic_verification_keys(value: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in {"verified", "citation_verified"}:
                found.append(child_path)
            found.extend(find_generic_verification_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_generic_verification_keys(child, f"{path}[{index}]"))
    return found


def test_dry_run_breakdown_touched_set_and_dynamic_baseline(
    plan: repair.RepairPlan,
) -> None:
    # The same tests remain useful after an authorized write: an applied state
    # must be exactly idempotent rather than reporting a second change wave.
    assert plan.counts in (EXPECTED_COUNTS, Counter())
    if plan.counts:
        assert plan.summary["status"] == "ready_for_independent_re_review_no_apply"
        assert set(plan.summary["changed_paths"]) == EXPECTED_CHANGED_PATHS
        assert len(plan.quarantine) == 36
    else:
        assert plan.summary["status"] == "already_applied"
        assert plan.summary["changed_paths"] == []
        assert plan.quarantine == []
    assert plan.summary["write_performed"] is False
    assert set(plan.summary["touched_node_ids"]) == repair.TOUCHED_NODE_IDS
    assert set(plan.summary["removed_edge_ids"]) == set(
        repair.DOG_EPICETUS_EDGE_HASHES
    )
    assert plan.summary["citation_rows_modified"] == 0
    assert plan.summary["corpus_files_modified"] == 0
    assert plan.summary["before_record_hashes"]["nodes"] == (
        repair.NODE_BEFORE_HASHES
    )
    assert plan.summary["after_record_hashes"]["nodes"] == repair.NODE_AFTER_HASHES
    assert plan.summary["after_record_hashes"]["e2_file"] == repair.E2_AFTER_SHA256
    baseline = plan.summary["measured_baseline"]
    assert baseline["registry"]["structurally_valid"] is True
    assert baseline["registry"]["errors"] == []
    assert baseline["strict_ingestion_debt"]["new_block_debt"] == 0
    assert baseline["strict_ingestion_debt"]["new_warn_debt"] == 0
    assert baseline["strict_ingestion_debt"]["before"] == baseline[
        "strict_ingestion_debt"
    ]["after_preview"]
    assert plan.summary["review_status"]["independent"] == (
        "fail_no_apply_re_review_required"
    )
    assert plan.summary["bibliography_companion"]["baseline_entry_count_drift"] == (
        2 if plan.counts else 0
    )
    assert plan.summary["bibliography_companion"]["preview_entry_count_drift"] == 0


def test_manifestations_are_separated_without_generic_verification(
    plan: repair.RepairPlan,
) -> None:
    nodes = planned_nodes(plan)
    publication = repair.metadata(nodes[repair.PUB_ID])
    assert publication["publication_identity"] == "intellectual_publication"
    assert not {"isbn", "publisher", "place", "verified", "citation_verified"} & (
        publication.keys()
    )
    manifestations = publication["manifestations"]
    assert [row["manifestation_id"] for row in manifestations] == [
        "sorabji_ncb_duckworth_london_1980",
        "sorabji_ncb_cornell_ithaca_1980_family",
        "sorabji_ncb_chicago_2006",
    ]
    duckworth, cornell, chicago = manifestations
    assert duckworth["isbns"] == ["0715613723", "0715615491"]
    assert duckworth["binding_assignment"] == "unresolved_do_not_infer"
    assert cornell["hardback_isbn"] == "0801411629"
    assert cornell["paperback"] == {
        "first_published": 1983,
        "isbn": "0801492440",
        "basis": "local copyright page, PDF 5",
    }
    assert cornell["local_artifact"]["printing_status"] == "unknown_not_inferred"
    assert cornell["local_artifact"]["scan"]["sha256"] == repair.SCAN_SHA256
    assert cornell["local_artifact"]["ocr_derivative"]["sha256"] == (
        repair.OCR_SHA256
    )
    assert chicago["publisher"] == "University of Chicago Press"
    assert chicago["isbn_10"] == "0226768244"
    assert chicago["isbn_13"] == "9780226768243"
    assert publication["bibtex_manifestations"] == (
        repair.bibtex_manifestation_records()
    )
    assert len(publication["bibtex_manifestations"]) == 4
    assert all(row["publisher"] for row in publication["bibtex_manifestations"])
    person_text = nodes[repair.PERSON_ID]["description"]
    assert "Bristol" not in person_text
    assert "University of Chicago Press, 2006" in person_text
    for node_id in repair.TOUCHED_NODE_IDS:
        assert find_generic_verification_keys(nodes[node_id]) == []
        assert "verified_reference" not in repair.metadata(nodes[node_id])


def test_all_nine_interpretive_nodes_are_discovery_only_in_runtime_policy(
    plan: repair.RepairPlan, true_citability_policy
) -> None:
    nodes = planned_nodes(plan)
    for node_id in repair.INTERPRETIVE_NODE_IDS:
        data = repair.metadata(nodes[node_id])
        assert data["citability"] == "discoverable_only"
        decision = true_citability_policy.evidence_policy(nodes[node_id])
        assert decision.tier is true_citability_policy.CitabilityTier.DISCOVERABLE_ONLY
    assert true_citability_policy.evidence_policy(nodes[repair.PERSON_ID]).tier is (
        true_citability_policy.CitabilityTier.CITABLE
    )
    assert true_citability_policy.evidence_policy(nodes[repair.PUB_ID]).tier is (
        true_citability_policy.CitabilityTier.CITABLE
    )


def test_bounded_interpretive_corrections_are_attributed_and_fail_closed(
    plan: repair.RepairPlan,
) -> None:
    nodes = planned_nodes(plan)
    taxonomy = nodes[repair.TAXONOMY_ID]
    assert taxonomy["description"].startswith(
        "Sorabji presents the Cicero and Gellius reports"
    )
    assert "necessitated only by auxiliary causes" not in json.dumps(
        taxonomy
    ).lower()

    expected_attributors = {
        "Augustine's reading of Chrysippus",
        "P. L. Donini's interpretation",
        "Michael Frede's interpretation",
    }
    for node_id in (
        repair.TAXONOMY_ID,
        repair.CYLINDER_ARGUMENT_ID,
        repair.CYLINDER_CONCEPT_ID,
    ):
        data = repair.metadata(nodes[node_id])
        readings = data.get("sorabji_1980_readings") or data["typed_readings"]
        assert {row["attributed_to"] for row in readings} == expected_attributors
    assert repair.metadata(nodes[repair.CYLINDER_ARGUMENT_ID])[
        "sorabji_1980_conclusion"
    ] == "The eight Stoic retreats fail to escape commitment to necessity."

    dog = repair.metadata(nodes[repair.DOG_ID])
    assert "primary_source" not in dog
    assert "ancient_attestation_locus_classicus" not in dog
    assert dog["candidate_witness"] == {
        "reported_by_secondary": "Sorabji 1980, p. 70 (local PDF 87)",
        "candidate_source": "Hippolytus, Refutatio Omnium Haeresium I.21",
        "attributed_figures": ["Zeno of Citium", "Chrysippus of Soli"],
        "status": "pending_hippolytus_primary_recollation",
    }
    assert not {
        "formulator",
        "targets",
        "legacy_premises",
        "verified_reference",
    } & dog.keys()
    assert dog["argument_form"] == "analogy"
    assert dog["validity_assessment"]["status"] == (
        "not_assessed_pending_primary_recollation"
    )
    assert "combines consent with necessity" in next(
        row["text"] for row in dog["premises"] if row["id"] == "P2"
    )
    assert "agency" not in next(
        row["text"].lower() for row in dog["premises"] if row["id"] == "P2"
    )
    assert "Cleanthes" not in json.dumps(dog, ensure_ascii=False)
    assert "alternative outcome" in nodes[repair.DOG_ID]["description"]
    assert "rejecting a categorical Megarian-school classification" in nodes[
        repair.MASTER_ID
    ]["description"]
    assert "This Sorabji evidence does not provide" in nodes[repair.CLINAMEN_ID][
        "description"
    ]
    assert "No surviving text" not in nodes[repair.CLINAMEN_ID]["description"]
    clinamen = repair.metadata(nodes[repair.CLINAMEN_ID])
    assert [row["source"] for row in clinamen["typed_attestations"]] == [
        "Lucretius, De Rerum Natura II.216-293",
        "Cicero, De Fato 22-23 and De Natura Deorum I.69-70",
        "Epicurus' surviving texts",
    ]


def test_generic_concepts_keep_their_ontology_and_gain_typed_dispute_metadata(
    plan: repair.RepairPlan,
) -> None:
    after = planned_nodes(plan)
    for node_id in (repair.EPH_HEMIN_ID, repair.STOIC_DEBATE_ID):
        data = repair.metadata(after[node_id])
        assert data["needs_evidence"] is True
        assert "disputed" in data["interpretation_status"]
        assert isinstance(data["typed_readings"], list)
        assert "verified_reference" not in data
        assert "reference_bundle_pending_recollation" in data
    eph = after[repair.EPH_HEMIN_ID]["description"]
    assert "Cross-period concept node" in eph
    assert "In Sorabji's disputed 1980 reading" in eph
    assert "states no single ancient doctrine or consensus" in eph
    assert "The concept implies:" not in eph
    debate = after[repair.STOIC_DEBATE_ID]["description"]
    assert debate.startswith("Modern analytical debate node")
    assert "appears perhaps with Chrysippus" in debate
    assert "remain disputed pending primary recollation" in debate
    position = repair.metadata(after[repair.POSITION_ID])
    assert position["interpretation_status"] == (
        "attributed_disputed_sorabji_interpretation"
    )
    assert "not primary-source or consensus status" in position["conclusion"][
        "text"
    ]
    position_description = after[repair.POSITION_ID]["description"]
    assert "separates coincidences from other effects" in position_description
    assert "denying causes to coincidences" in position_description
    assert "constructed human-action example" in position_description


def test_edges_are_surgical_and_2017_provenance_is_immutable(
    plan: repair.RepairPlan,
) -> None:
    before = repair.read_jsonl(plan.root / "data/kg/edges.jsonl")
    after = output_rows(plan, "data/kg/edges.jsonl")
    before_by_id = {repair.edge_id(row): row for row in before}
    after_by_id = {repair.edge_id(row): row for row in after}
    assert not set(repair.DOG_EPICETUS_EDGE_HASHES) & after_by_id.keys()
    for edge_id, expected_hash in repair.SORABJI_2017_ADVANCED_IN_HASHES.items():
        assert repair.canonical_hash(after_by_id[edge_id]) == expected_hash
    for edge_id, row in before_by_id.items():
        if edge_id not in repair.DOG_EPICETUS_EDGE_HASHES:
            assert after_by_id[edge_id] == row
    assert all(not path.startswith("data/corpus/") for path in plan.summary["changed_paths"])
    assert "data/corpus/citations.jsonl" not in plan.summary["changed_paths"]


def test_exact_node_edge_and_file_touched_sets_have_no_hidden_mutations(
    plan: repair.RepairPlan,
) -> None:
    nodes_path = plan.root / "data/kg/nodes.jsonl"
    before_node_lines = {
        repair.node_id(json.loads(line)): line
        for line in nodes_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    after_node_lines = {
        repair.node_id(json.loads(line)): line
        for line in plan.outputs[nodes_path].decode("utf-8").splitlines()
        if line.strip()
    }
    assert before_node_lines.keys() == after_node_lines.keys()
    changed_nodes = {
        node_id
        for node_id in before_node_lines
        if repair.canonical_hash(json.loads(before_node_lines[node_id]))
        != repair.canonical_hash(json.loads(after_node_lines[node_id]))
    }
    assert changed_nodes == (set(repair.TOUCHED_NODE_IDS) if plan.counts else set())
    for node_id in before_node_lines.keys() - repair.TOUCHED_NODE_IDS:
        assert after_node_lines[node_id] == before_node_lines[node_id]

    edges_path = plan.root / "data/kg/edges.jsonl"
    before_edges = {
        repair.edge_id(json.loads(line)): line
        for line in edges_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    after_edges = {
        repair.edge_id(json.loads(line)): line
        for line in plan.outputs[edges_path].decode("utf-8").splitlines()
        if line.strip()
    }
    assert before_edges.keys() - after_edges.keys() == (
        set(repair.DOG_EPICETUS_EDGE_HASHES) if plan.counts else set()
    )
    assert after_edges.keys() - before_edges.keys() == set()
    assert all(after_edges[key] == before_edges[key] for key in after_edges)

    assert set(plan.summary["changed_paths"]) == (
        EXPECTED_CHANGED_PATHS if plan.counts else set()
    )
    assert {path.relative_to(plan.root).as_posix() for path in plan.outputs} == (
        EXPECTED_CHANGED_PATHS
    )
    assert not any(path.startswith("data/corpus/") for path in EXPECTED_CHANGED_PATHS)


def test_e2_patch_separates_scan_ocr_order_and_1980_2017_evidence(
    plan: repair.RepairPlan,
) -> None:
    payload = json.loads(
        plan.outputs[plan.root / "data/kg/e2_patches/sorabji.json"].decode("utf-8")
    )
    assert payload["source_artifacts"]["source_scan"] == {
        "locator": repair.SCAN_RELATIVE,
        "sha256": repair.SCAN_SHA256,
        "md5": repair.SCAN_MD5,
        "byte_size": repair.SCAN_BYTES,
        "role": "visual_authority",
    }
    assert payload["source_artifacts"]["ocr_derivative"]["role"] == (
        "navigation_only"
    )
    assert payload["page_map"]["rule"] == "pdf_page = printed_page + 17"
    assert payload["page_map"]["printed_range"] == "3-326"
    eight = payload["patches"][
        "new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity"
    ]
    assert eight["strategy_order"] == repair.EIGHT_STRATEGIES
    assert len(eight["strategy_order"]) == 8
    assert [row.split(":", 1)[0] for row in eight["strategy_order"]] == [
        str(index) for index in range(1, 9)
    ]
    assert "Cleanthes" in eight["strategy_order"][0]
    assert "Chrysippus" in eight["strategy_order"][1]
    assert payload["runtime_exposure"] == "internal_audit_only"
    assert payload["reuse_status"] == "unverified_do_not_republish"
    assert payload["legacy_quotes_status"] == "retained_in_place_not_duplicated"
    assert payload["independent_review"] == {
        "artifact": repair.INDEPENDENT_REVIEW_RELATIVE,
        "sha256": repair.INDEPENDENT_REVIEW_SHA256,
        "verdict": "fail_no_apply",
        "status": "candidate_re_review_required_after_blocker_corrections",
    }
    for key in repair.E2_PAGE_SCOPES:
        patch = payload["patches"][key]
        assert patch["legacy_ocr_review"]
        assert patch["current_review"]["scan_sha256"] == repair.SCAN_SHA256
        assert not {
            "verified_against_ocr_version",
            "verification_confidence",
            "verified_at",
            "verified_by",
        } & patch.keys()
    cicero = payload["patches"][
        "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4"
    ]
    assert cicero["publication_id"] == (
        "scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins"
    )
    assert cicero["background_publication_id"] == repair.PUB_ID
    assert set(cicero["evidence_scopes"]) == {"sorabji_1980", "sorabji_2017"}

    quote_values: list[str] = []

    def collect_legacy_quotes(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.startswith("quote_verbatim"):
                    assert isinstance(child, str)
                    quote_values.append(child)
                collect_legacy_quotes(child)
        elif isinstance(value, list):
            for child in value:
                collect_legacy_quotes(child)

    collect_legacy_quotes(payload)
    assert len(quote_values) == 9
    quarantine_text = json.dumps(plan.quarantine, ensure_ascii=False)
    evidence_text = plan.outputs[
        plan.root
        / "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
    ].decode("utf-8")
    assert all(quote not in quarantine_text for quote in quote_values)
    assert all(quote not in evidence_text for quote in quote_values)


def test_eight_strategy_review_cannot_pass_with_seven_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repair.validate_eight_strategies(repair.EIGHT_STRATEGIES)
    broken = ["1-2: conflated Cleanthes and Chrysippus", *repair.EIGHT_STRATEGIES[2:]]
    assert len(broken) == 7
    with pytest.raises(RuntimeError, match="exactly eight"):
        repair.validate_eight_strategies(broken)
    monkeypatch.setattr(repair, "EIGHT_STRATEGIES", broken)
    with pytest.raises(RuntimeError, match="exactly eight"):
        repair.verification_records()


def test_no_active_runtime_consumer_loads_e2_patch() -> None:
    runtime_roots = [
        ROOT / "backend",
        ROOT / "frontend/src",
        ROOT / "graphrag/src",
        ROOT / "knowledge graph/src",
    ]
    forbidden = []
    for runtime_root in runtime_roots:
        for path in runtime_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "e2_patches" in text or "data/kg/e2_patches/sorabji.json" in text:
                forbidden.append(str(path.relative_to(ROOT)))
    assert forbidden == []


def test_manifest_registry_and_bibliography_remain_partial_and_open(
    plan: repair.RepairPlan,
) -> None:
    manifest = next(
        row
        for row in output_rows(plan, "data/scholarly_sources/manifest.jsonl")
        if row.get("publication_dir") == repair.SOURCE_MANIFEST_DIR
    )
    assert manifest["kg_ingestion_status"] == "partial"
    assert manifest["year_original"] == 1980
    assert manifest["year_edition_used"] == 1983
    assert manifest["edition_used"] == (
        "Cornell Paperbacks, Cornell University Press, Ithaca, first paperback "
        "edition 1983; exact printing unknown"
    )
    assert manifest["local_printing_year"] is None
    assert manifest["local_printing_status"] == "unknown_not_inferred"
    assert manifest["bibtex_key"] == (
        "sorabji-1983-necessity-cause-and-blame-cornell-paperbacks"
    )
    assert manifest["ocr_extracted_word_count_unreliable"] == 166_001
    assert "word_count" not in manifest
    assert "line_count" not in manifest
    assert "duplicated blocks" in manifest["ocr_extraction_caveat"]

    sources = output_rows(
        plan, "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
    )
    source = next(row for row in sources if row.get("source_id") == repair.SOURCE_ID)
    assert source["coverage"]["state"] == "partial"
    assert source["acquisition"]["status"] == "archived_verified"
    assert set(source["acquisition"]) == {
        "status",
        "manifest_publication_dirs",
        "artifacts",
    }
    assert "fingerprints (SHA-256/MD5/size)" in source["notes"]
    assert "visual page map for printed pages 3-326" in source["notes"]
    evidence = {
        row["evidence_id"]: row
        for row in output_rows(
            plan,
            "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
        )
        if row.get("evidence_id") in repair.ALL_SORABJI_EVIDENCE_IDS
    }
    assert set(evidence) == set(repair.ALL_SORABJI_EVIDENCE_IDS)
    for row in evidence.values():
        assert row["claim_status"] == "in_review"
        assert row["locator"]["page_map_status"] == "visually_verified"
        assert row["quotation"]["status"] == "paraphrase_only"
        assert "primary_source_verified" not in row
        assert "consensus" not in row
    issues = {
        row["issue_id"]: row
        for row in output_rows(
            plan, "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
        )
        if row.get("issue_id")
        in {repair.MANIFESTATION_ISSUE_ID, repair.INTERPRETATION_ISSUE_ID}
    }
    assert set(issues) == {
        repair.MANIFESTATION_ISSUE_ID,
        repair.INTERPRETATION_ISSUE_ID,
    }
    assert {row["status"] for row in issues.values()} == {"open"}
    for issue in issues.values():
        reviews = [
            artifact
            for artifact in issue["evidence_artifacts"]
            if artifact.get("locator") == repair.INDEPENDENT_REVIEW_RELATIVE
        ]
        assert reviews
        assert set(reviews[0]) <= {"locator", "role", "sha256", "accessed_at"}
    e2_artifact = next(
        artifact
        for artifact in issues[repair.INTERPRETATION_ISSUE_ID]["evidence_artifacts"]
        if artifact.get("locator") == "data/kg/e2_patches/sorabji.json"
    )
    assert e2_artifact["role"] == "catalog_record"
    assert set(e2_artifact) == {"locator", "role"}
    assert "internal legacy curation/evidence patch" in issues[
        repair.INTERPRETATION_ISSUE_ID
    ]["summary"]
    assert "FAIL-NO APPLY" in issues[repair.INTERPRETATION_ISSUE_ID]["summary"]
    verifications = output_rows(
        plan,
        "data/goals/sota/registry/verifications/sorabji_20260824.jsonl",
    )
    assert len(verifications) == 8
    assert {row["stage"] for row in verifications} == {"identity", "primary"}
    assert all("not independent review" in row["notes"] for row in verifications)
    assert not any(row["stage"] in {"independent", "adversarial"} for row in verifications)

    bib = plan.outputs[plan.root / "data/kg/publications.bib"].decode("utf-8")
    publication = planned_nodes(plan)[repair.PUB_ID]
    canonical = repair.canonical_sorabji_bibtex_block(publication)
    assert canonical in bib
    assert repair.OLD_BIB_ENTRY not in bib
    assert canonical.count("@book{") == 4
    assert canonical.count("publisher = {") == 4
    assert "@book{sorabji-1980-necessity-cause-and-blame-duckworth" in canonical
    assert "@book{sorabji-1980-necessity-cause-and-blame-cornell" in canonical
    assert "@book{sorabji-1983-necessity-cause-and-blame-cornell-paperbacks" in canonical
    assert "@book{sorabji-2006-necessity-cause-and-blame-chicago" in canonical
    duckworth_entry = canonical.split("@book{sorabji-1980-necessity", 1)[1].split(
        "@book{", 1
    )[0]
    assert "9780226768243" not in duckworth_entry

    from scripts.export_publications_bibtex import (
        bibtex_entry_keys,
        build_companion_report,
    )

    report = json.loads(
        plan.outputs[plan.root / repair.PUBLICATIONS_BIB_REPORT_RELATIVE].decode("utf-8")
    )
    all_nodes = list(planned_nodes(plan).values())
    expected_report = build_companion_report(
        all_nodes,
        bib,
        generation_mode="sorabji_manifestation_surgical_snapshot_transform",
        baseline_bibtex_sha256=repair.BIB_BEFORE_SHA256,
    )
    assert report == expected_report
    assert report["entry_keys"] == bibtex_entry_keys(bib)
    assert report["entries_written"] == len(report["entry_keys"])
    assert report["bibtex_sha256"] == repair.sha256_bytes(bib.encode("utf-8"))
    assert report["publication_count"] == sum(
        row.get("type") == "publication" for row in all_nodes
    )
    assert report["nodes_with_missing_fields"] == len(report["missing"])
    baseline_report = json.loads(
        (ROOT / repair.PUBLICATIONS_BIB_REPORT_RELATIVE).read_text(encoding="utf-8")
    )
    baseline_entry_count = len(
        bibtex_entry_keys((ROOT / repair.PUBLICATIONS_BIB_RELATIVE).read_text())
    )
    baseline_drift = abs(
        baseline_entry_count - int(baseline_report["entries_written"])
    )
    candidate_drift = abs(
        len(bibtex_entry_keys(bib)) - int(report["entries_written"])
    )
    assert baseline_drift == (2 if plan.counts else 0)
    assert candidate_drift == 0
    assert candidate_drift <= baseline_drift


def test_full_registry_audit_accepts_the_complete_preview(
    plan: repair.RepairPlan, tmp_path: Path
) -> None:
    from scripts.audit_sota_registry import audit_registry

    shadow = tmp_path / "repo"
    shadow.mkdir()
    for child in ROOT.iterdir():
        if child.name == "data":
            continue
        (shadow / child.name).symlink_to(child, target_is_directory=child.is_dir())

    shadow_data = shadow / "data"
    shadow_data.mkdir()
    for child in (ROOT / "data").iterdir():
        if child.name in {"kg", "goals", "scholarly_sources"}:
            continue
        (shadow_data / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )

    shadow_kg = shadow_data / "kg"
    shadow_kg.mkdir()
    planned_kg_names = {
        "nodes.jsonl",
        "edges.jsonl",
        "publications.bib",
        "publications_bibtex_report.json",
    }
    for child in (ROOT / "data/kg").iterdir():
        if child.name in planned_kg_names | {"e2_patches"}:
            continue
        (shadow_kg / child.name).symlink_to(child, target_is_directory=child.is_dir())
    for name in planned_kg_names:
        (shadow_kg / name).write_bytes(plan.outputs[plan.root / f"data/kg/{name}"])
    shadow_e2 = shadow_kg / "e2_patches"
    shadow_e2.mkdir()
    for child in (ROOT / "data/kg/e2_patches").iterdir():
        if child.name == "sorabji.json":
            continue
        (shadow_e2 / child.name).symlink_to(child, target_is_directory=child.is_dir())
    (shadow_e2 / "sorabji.json").write_bytes(
        plan.outputs[plan.root / "data/kg/e2_patches/sorabji.json"]
    )

    shadow_scholarly = shadow_data / "scholarly_sources"
    shadow_scholarly.mkdir()
    for child in (ROOT / "data/scholarly_sources").iterdir():
        if child.name == "manifest.jsonl":
            continue
        (shadow_scholarly / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    (shadow_scholarly / "manifest.jsonl").write_bytes(
        plan.outputs[plan.root / "data/scholarly_sources/manifest.jsonl"]
    )

    shadow_goals = shadow_data / "goals"
    shadow_goals.mkdir()
    for child in (ROOT / "data/goals").iterdir():
        if child.name == "sota":
            continue
        (shadow_goals / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    shutil.copytree(ROOT / "data/goals/sota", shadow_goals / "sota")
    for path, payload in plan.outputs.items():
        relative = path.relative_to(plan.root)
        if relative.parts[:3] == ("data", "goals", "sota"):
            destination = shadow / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)

    report = audit_registry(shadow_goals / "sota", shadow)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["errors"] == []


def test_normative_registry_schema_has_zero_new_preview_errors(
    plan: repair.RepairPlan,
) -> None:
    from jsonschema import Draft7Validator

    schema = json.loads(
        (ROOT / "data/goals/sota/registry.schema.json").read_text(encoding="utf-8")
    )
    configs = {
        "source": ("sources", "source_id"),
        "evidence": ("evidence", "evidence_id"),
        "issue": ("issues", "issue_id"),
        "verification": ("verifications", "verification_id"),
        "wave": ("waves", "wave_id"),
    }
    registry_root = ROOT / "data/goals/sota/registry"

    def records(record_type: str, directory: str, key: str) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for path in sorted((registry_root / directory).glob("*.jsonl")):
            for row in repair.read_jsonl(path):
                assert row["record_type"] == record_type
                result[str(row[key])] = row
        return result

    before = {
        record_type: records(record_type, directory, key)
        for record_type, (directory, key) in configs.items()
    }
    after = copy.deepcopy(before)
    preview_paths = {
        "source": "data/goals/sota/registry/sources/seed_priority_20260824.jsonl",
        "evidence": "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
        "issue": "data/goals/sota/registry/issues/seed_known_20260824.jsonl",
        "verification": "data/goals/sota/registry/verifications/sorabji_20260824.jsonl",
        "wave": "data/goals/sota/registry/waves/priority_20260824.jsonl",
    }
    for record_type, relative in preview_paths.items():
        key = configs[record_type][1]
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

    def schema_errors(collections: dict[str, dict[str, dict]]) -> set[tuple]:
        found: set[tuple] = set()
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

    before_errors = schema_errors(before)
    after_errors = schema_errors(after)
    assert after_errors - before_errors == set()

    touched = {
        "source": {repair.SOURCE_ID},
        "evidence": set(repair.ALL_SORABJI_EVIDENCE_IDS),
        "issue": {repair.MANIFESTATION_ISSUE_ID, repair.INTERPRETATION_ISSUE_ID},
        "verification": {
            row["verification_id"] for row in repair.verification_records()
        },
        "wave": {repair.WAVE_ID},
    }
    for record_type, identifiers in touched.items():
        for identifier in identifiers:
            errors = list(validators[record_type].iter_errors(after[record_type][identifier]))
            assert errors == [], [error.message for error in errors]


def test_exact_quarantine_and_preview_hashes(plan: repair.RepairPlan) -> None:
    if not plan.counts:
        pytest.skip("authorized repair is already applied; quarantine lives on disk")
    kinds = Counter(row["record_type"] for row in plan.quarantine)
    assert kinds == Counter(
        {
            "kg_node_before": 11,
            "kg_edge_removed": 2,
            "e2_patch_before_summary": 1,
            "scholarly_manifest_absence_before": 1,
            "registry_source_before": 1,
            "registry_evidence_before": 2,
            "registry_evidence_absence_before": 5,
            "registry_issue_absence_before": 2,
            "registry_wave_before": 1,
            "registry_verification_absence_before": 8,
            "bib_entry_before": 1,
            "bibtex_report_before_summary": 1,
        }
    )
    node_before = {
        repair.node_id(row["record"]): repair.canonical_hash(row["record"])
        for row in plan.quarantine
        if row["record_type"] == "kg_node_before"
    }
    assert node_before == repair.NODE_BEFORE_HASHES
    edge_before = {
        repair.edge_id(row["record"]): repair.canonical_hash(row["record"])
        for row in plan.quarantine
        if row["record_type"] == "kg_edge_removed"
    }
    assert edge_before == repair.DOG_EPICETUS_EDGE_HASHES
    e2_before = next(
        row
        for row in plan.quarantine
        if row["record_type"] == "e2_patch_before_summary"
    )
    assert e2_before["file_sha256"] == repair.E2_BEFORE_SHA256
    bib_before = next(
        row for row in plan.quarantine if row["record_type"] == "bib_entry_before"
    )
    assert bib_before["entry"] == repair.OLD_BIB_ENTRY
    assert bib_before["entry_sha256"] == repair.sha256_bytes(
        repair.OLD_BIB_ENTRY.encode("utf-8")
    )
    report_before = next(
        row
        for row in plan.quarantine
        if row["record_type"] == "bibtex_report_before_summary"
    )
    assert report_before["file_sha256"] == repair.BIB_REPORT_BEFORE_SHA256
    assert report_before["entries_written"] == 538
    assert set(plan.summary["output_sha256_preview"]) == EXPECTED_CHANGED_PATHS
    for path, payload in plan.outputs.items():
        relative = str(path.relative_to(plan.root))
        assert plan.summary["output_sha256_preview"][relative] == (
            repair.sha256_bytes(payload)
        )


def test_transform_layers_are_idempotent(plan: repair.RepairPlan) -> None:
    nodes_before = repair.read_jsonl(plan.root / "data/kg/nodes.jsonl")
    nodes_first = repair.transform_nodes(nodes_before)
    nodes_second = repair.transform_nodes(nodes_first[0])
    assert nodes_second[0] == nodes_first[0]
    assert nodes_second[1] == []
    assert nodes_second[2] == Counter()

    edges_before = repair.read_jsonl(plan.root / "data/kg/edges.jsonl")
    edges_first = repair.transform_edges(edges_before)
    edges_second = repair.transform_edges(edges_first[0])
    assert edges_second[0] == edges_first[0]
    assert edges_second[1] == []
    assert edges_second[2] == Counter()

    e2_path = plan.root / "data/kg/e2_patches/sorabji.json"
    e2_bytes = e2_path.read_bytes()
    e2_first = repair.transform_e2(
        json.loads(e2_bytes), current_file_sha256=repair.sha256_bytes(e2_bytes)
    )
    e2_payload = (
        json.dumps(e2_first[0], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    e2_second = repair.transform_e2(
        e2_first[0], current_file_sha256=repair.sha256_bytes(e2_payload)
    )
    assert e2_second == (e2_first[0], [], Counter())

    registry_root = plan.root / "data/goals/sota/registry"
    registry_first = repair.transform_registry(
        repair.read_jsonl(registry_root / "sources/seed_priority_20260824.jsonl"),
        repair.read_jsonl(registry_root / "evidence/seed_priority_20260824.jsonl"),
        repair.read_jsonl(registry_root / "issues/seed_known_20260824.jsonl"),
        repair.read_jsonl(registry_root / "waves/priority_20260824.jsonl"),
        repair.read_jsonl(registry_root / "verifications/sorabji_20260824.jsonl"),
    )
    mapped = registry_first[0]
    registry_second = repair.transform_registry(
        mapped["sources"],
        mapped["evidence"],
        mapped["issues"],
        mapped["waves"],
        mapped["verifications"],
    )
    assert registry_second == (mapped, [], Counter())

    bib_path = plan.root / "data/kg/publications.bib"
    bib_bytes = bib_path.read_bytes()
    report_path = plan.root / repair.PUBLICATIONS_BIB_REPORT_RELATIVE
    report_bytes = report_path.read_bytes()
    publication = next(
        row for row in nodes_first[0] if repair.node_id(row) == repair.PUB_ID
    )
    bib_first = repair.transform_bib(
        bib_bytes.decode("utf-8"),
        json.loads(report_bytes),
        current_sha256=repair.sha256_bytes(bib_bytes),
        report_sha256=repair.sha256_bytes(report_bytes),
        publication_node=publication,
        all_nodes=nodes_first[0],
    )
    bib_after = bib_first[0].encode("utf-8")
    report_after = (
        json.dumps(bib_first[1], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    bib_second = repair.transform_bib(
        bib_first[0],
        bib_first[1],
        current_sha256=repair.sha256_bytes(bib_after),
        report_sha256=repair.sha256_bytes(report_after),
        publication_node=publication,
        all_nodes=nodes_first[0],
    )
    assert bib_second == (bib_first[0], bib_first[1], [], Counter())


def test_record_level_drift_is_fail_closed() -> None:
    nodes = repair.read_jsonl(ROOT / "data/kg/nodes.jsonl")
    by_id = {repair.node_id(row): row for row in nodes}
    changed = copy.deepcopy(by_id[repair.PUB_ID])
    if repair.metadata(changed).get(repair.STAMP) is True:
        changed["description"] += " drift"
    else:
        changed["unexpected_drift"] = True
    nodes[nodes.index(by_id[repair.PUB_ID])] = changed
    with pytest.raises(repair.PreconditionsError, match="drift"):
        repair.transform_nodes(nodes)

    e2_path = ROOT / "data/kg/e2_patches/sorabji.json"
    payload = json.loads(e2_path.read_text(encoding="utf-8"))
    with pytest.raises(repair.PreconditionsError, match="drift"):
        repair.transform_e2(payload, current_file_sha256="0" * 64)

    sources = repair.read_jsonl(
        ROOT / "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
    )
    source = next(row for row in sources if row.get("source_id") == repair.SOURCE_ID)
    source["unexpected_drift"] = True
    with pytest.raises(repair.PreconditionsError, match="drift"):
        repair.replace_registry_record(
            sources,
            key="source_id",
            wanted=repair.SOURCE_ID,
            before_hash=repair.REGISTRY_BEFORE_HASHES[repair.SOURCE_ID],
            transform=repair.transform_source_record,
        )


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


def assert_transaction_scratch_absent(root: Path) -> None:
    journal, backup = repair.journal_paths(root)
    assert not journal.exists()
    assert not backup.exists()


def test_precommit_drift_preserves_concurrent_writer(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)

    def concurrent_writer() -> None:
        second.write_bytes(b"external-concurrent-change\n")

    with pytest.raises(repair.PreconditionsError, match="pre-commit snapshot drift"):
        repair.transactional_replace(
            tmp_path,
            outputs,
            before,
            before_commit_hook=concurrent_writer,
        )
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == b"external-concurrent-change\n"
    assert_transaction_scratch_absent(tmp_path)


def test_baseexception_after_first_replace_restores_snapshot_a(tmp_path: Path) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    with pytest.raises(repair.InjectedTransactionAbort):
        repair.transactional_replace(
            tmp_path,
            outputs,
            before,
            fail_after=1,
        )
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_scratch_absent(tmp_path)


def test_replace_failure_restores_snapshot_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_replace = os.replace
    failed = False

    def fail_second_once(source: Path, destination: Path) -> None:
        nonlocal failed
        if Path(destination) == second and not failed:
            failed = True
            raise OSError("injected replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(repair, "replace_path", fail_second_once)
    with pytest.raises(OSError, match="injected replace failure"):
        repair.transactional_replace(tmp_path, outputs, before)
    assert failed is True
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_scratch_absent(tmp_path)


def test_rollback_failure_keeps_durable_recovery_and_second_run_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_replace = os.replace
    commit_failed = False
    rollback_failed = False

    def fail_commit_then_rollback(source: Path, destination: Path) -> None:
        nonlocal commit_failed, rollback_failed
        target = Path(destination)
        if target == second and not commit_failed:
            commit_failed = True
            raise OSError("injected commit replace failure")
        if target == first and commit_failed and not rollback_failed:
            rollback_failed = True
            raise OSError("injected rollback replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(repair, "replace_path", fail_commit_then_rollback)
    with pytest.raises(OSError, match="injected rollback replace failure"):
        repair.transactional_replace(tmp_path, outputs, before)
    journal, backup = repair.journal_paths(tmp_path)
    assert commit_failed is True and rollback_failed is True
    assert first.read_bytes() == outputs[first]
    assert second.read_bytes() == before[second]
    assert journal.is_file()
    assert backup.is_dir()

    monkeypatch.setattr(repair, "replace_path", real_replace)
    assert repair.recover_transaction(tmp_path) == "rolled_back"
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_scratch_absent(tmp_path)


def test_fsync_failure_restores_snapshot_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    real_fsync_directory = repair.fsync_directory
    failed = False

    def fail_live_directory_once(path: Path) -> None:
        nonlocal failed
        if Path(path) == first.parent and not failed:
            failed = True
            raise OSError("injected fsync failure")
        real_fsync_directory(path)

    monkeypatch.setattr(repair, "fsync_directory", fail_live_directory_once)
    with pytest.raises(OSError, match="injected fsync failure"):
        repair.transactional_replace(tmp_path, outputs, before)
    assert failed is True
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_scratch_absent(tmp_path)


def test_hard_crash_journal_recovery_rolls_back_committing_state(
    tmp_path: Path,
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    journal = repair.prepare_transaction(tmp_path, outputs, before)
    journal_path, backup_dir = repair.journal_paths(tmp_path)
    journal["state"] = "committing"
    repair.write_journal(journal_path, journal)
    entry = journal["entries"][0]
    repair.replace_path(backup_dir / entry["staged"], tmp_path / entry["target"])
    repair.fsync_directory((tmp_path / entry["target"]).parent)
    journal["committed_targets"].append(entry["target"])
    repair.write_journal(journal_path, journal)

    assert repair.recover_transaction(tmp_path) == "rolled_back"
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == before[second]
    assert_transaction_scratch_absent(tmp_path)


def test_prepared_crash_recovery_discards_stage_without_overwriting_drift(
    tmp_path: Path,
) -> None:
    first, _second, before, outputs = transaction_fixture(tmp_path)
    journal = repair.prepare_transaction(tmp_path, outputs, before)
    assert journal["state"] == "prepared"
    first.write_bytes(b"external-after-preparation\n")
    assert repair.recover_transaction(tmp_path) == "prepared_stage_discarded"
    assert first.read_bytes() == b"external-after-preparation\n"
    assert_transaction_scratch_absent(tmp_path)


def test_committed_crash_recovery_keeps_desired_bytes_and_finishes_cleanup(
    tmp_path: Path,
) -> None:
    first, second, before, outputs = transaction_fixture(tmp_path)
    journal = repair.prepare_transaction(tmp_path, outputs, before)
    journal_path, backup_dir = repair.journal_paths(tmp_path)
    journal["state"] = "committing"
    repair.write_journal(journal_path, journal)
    for entry in journal["entries"]:
        target = tmp_path / entry["target"]
        repair.replace_path(backup_dir / entry["staged"], target)
        repair.fsync_directory(target.parent)
        journal["committed_targets"].append(entry["target"])
        repair.write_journal(journal_path, journal)
    journal["state"] = "committed"
    repair.write_journal(journal_path, journal)

    assert repair.recover_transaction(tmp_path) == "completed_cleanup"
    assert first.read_bytes() == outputs[first]
    assert second.read_bytes() == outputs[second]
    assert_transaction_scratch_absent(tmp_path)


def test_orphaned_prejournal_stage_is_recoverable(tmp_path: Path) -> None:
    first, _second, _before, _outputs = transaction_fixture(tmp_path)
    _journal, backup_dir = repair.journal_paths(tmp_path)
    backup_dir.mkdir(parents=True)
    (backup_dir / "private-stage").write_bytes(b"private")
    first.write_bytes(b"external-byte-state\n")
    assert repair.recover_transaction(tmp_path) == "orphaned_stage_discarded"
    assert first.read_bytes() == b"external-byte-state\n"
    assert_transaction_scratch_absent(tmp_path)


def test_registry_and_ingestion_debt_gates_fail_closed() -> None:
    valid = {
        "registry": {"structurally_valid": True, "errors": []},
        "strict_ingestion_debt": {"new_block_debt": 0, "new_warn_debt": 0},
    }
    repair.enforce_measured_baseline(valid)
    invalid_registry = copy.deepcopy(valid)
    invalid_registry["registry"] = {
        "structurally_valid": False,
        "errors": ["missing artifact"],
    }
    with pytest.raises(repair.PreconditionsError, match="global SOTA registry invalid"):
        repair.enforce_measured_baseline(invalid_registry)
    for key in ("new_block_debt", "new_warn_debt"):
        debt = copy.deepcopy(valid)
        debt["strict_ingestion_debt"][key] = 1
        with pytest.raises(
            repair.PreconditionsError, match="creates strict ingestion debt"
        ):
            repair.enforce_measured_baseline(debt)


def test_cli_returns_nonzero_blocked_status_for_invalid_registry(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def blocked(_root: Path) -> repair.RepairPlan:
        raise repair.PreconditionsError(
            "global SOTA registry invalid: ['injected missing artifact']"
        )

    monkeypatch.setattr(repair, "build_plan", blocked)
    assert repair.main(["--root", str(ROOT), "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked_precondition_failed"
    assert payload["write_performed"] is False
    assert "global SOTA registry invalid" in payload["error"]


def pyc_snapshot() -> dict[Path, bytes]:
    sources = [
        ROOT / repair.SCRIPT_RELATIVE,
        ROOT / "scripts/check_ingestion_rules.py",
        ROOT / "scripts/audit_sota_registry.py",
        ROOT / "scripts/check_scholarly_sources_manifest.py",
        ROOT / "scripts/export_publications_bibtex.py",
        (
            ROOT
            / "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py"
        ),
    ]
    return {
        path: path.read_bytes()
        for source in sources
        for path in (source.parent / "__pycache__").glob(f"{source.stem}.*.pyc")
        if path.is_file()
    }


def git_head_bytes(relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def build_post_sorabji_shadow(tmp_path: Path) -> Path:
    """Overlay the exact Sorabji cohort state without undoing later work.

    Long--Sedley subsequently refined six Sorabji-touched nodes and the shared
    priority wave.  Their persisted before-images are therefore the authoritative
    post-Sorabji records.  All unrelated live records remain visible so this
    historical harness composes with every later migration.
    """

    shadow = tmp_path / "post-sorabji-repo"
    shadow.mkdir()
    for child in ROOT.iterdir():
        if child.name in {".git", "data"}:
            continue
        (shadow / child.name).symlink_to(child, target_is_directory=child.is_dir())

    shadow_data = shadow / "data"
    shadow_data.mkdir()
    for child in (ROOT / "data").iterdir():
        if child.name in {"kg", "goals"}:
            continue
        (shadow_data / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )

    long_quarantine = repair.read_jsonl(
        ROOT / "data/audit/2026-08-24_long_sedley_vol2_p0_quarantine.jsonl"
    )
    post_sorabji_nodes = {
        repair.node_id(row["record"]): row["record"]
        for row in long_quarantine
        if row["record_type"] == "kg_node_before"
        and repair.node_id(row["record"]) in repair.TOUCHED_NODE_IDS
    }
    live_nodes = repair.read_jsonl(ROOT / "data/kg/nodes.jsonl")
    for node_id, record in post_sorabji_nodes.items():
        assert repair.canonical_hash(record) == repair.NODE_AFTER_HASHES[node_id]
    restored_nodes = [
        copy.deepcopy(post_sorabji_nodes.get(repair.node_id(row), row))
        for row in live_nodes
    ]

    shadow_kg = shadow_data / "kg"
    shadow_kg.mkdir()
    for child in (ROOT / "data/kg").iterdir():
        if child.name in {"nodes.jsonl", "publications_bibtex_report.json"}:
            continue
        (shadow_kg / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    (shadow_kg / "nodes.jsonl").write_bytes(repair.serialize_jsonl(restored_nodes))

    from scripts.export_publications_bibtex import build_companion_report

    bib_text = (ROOT / repair.PUBLICATIONS_BIB_RELATIVE).read_text(encoding="utf-8")
    historical_report = build_companion_report(
        restored_nodes,
        bib_text,
        generation_mode="sorabji_manifestation_surgical_snapshot_transform",
        baseline_bibtex_sha256=repair.BIB_BEFORE_SHA256,
    )
    (shadow_kg / "publications_bibtex_report.json").write_text(
        json.dumps(historical_report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    shadow_goals = shadow_data / "goals"
    shadow_goals.mkdir()
    for child in (ROOT / "data/goals").iterdir():
        if child.name == "sota":
            continue
        (shadow_goals / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    shutil.copytree(ROOT / "data/goals/sota", shadow_goals / "sota")
    post_sorabji_wave = next(
        row["record"]
        for row in long_quarantine
        if row["record_type"] == "registry_wave_before"
        and row["record"].get("wave_id") == repair.WAVE_ID
    )
    wave_path = shadow_goals / "sota/registry/waves/priority_20260824.jsonl"
    waves = repair.read_jsonl(wave_path)
    waves = [
        copy.deepcopy(post_sorabji_wave)
        if row.get("wave_id") == repair.WAVE_ID
        else row
        for row in waves
    ]
    wave_path.write_bytes(repair.serialize_jsonl(waves))
    # The historical Sorabji wave still names Long--Sedley's pre-split aggregate
    # evidence row.  Keep that retired row only inside this shadow so the global
    # registry audit can validate the historical wave alongside today's split
    # evidence records.
    retired_long_evidence = next(
        row["record"]
        for row in long_quarantine
        if row["record_type"] == "registry_evidence_removed"
    )
    evidence_path = (
        shadow_goals / "sota/registry/evidence/seed_priority_20260824.jsonl"
    )
    evidence = repair.read_jsonl(evidence_path)
    if not any(
        row.get("evidence_id") == retired_long_evidence.get("evidence_id")
        for row in evidence
    ):
        evidence.append(copy.deepcopy(retired_long_evidence))
        evidence_path.write_bytes(repair.serialize_jsonl(evidence))
    return shadow


def reconstruct_preapply_workspace(tmp_path: Path, postapply_root: Path) -> Path:
    """Build an exact mutable Snapshot-A copy from the applied quarantine."""

    shadow = tmp_path / "preapply-repo"
    shadow.mkdir()
    for child in postapply_root.iterdir():
        if child.name in {".git", "data"}:
            continue
        (shadow / child.name).symlink_to(child, target_is_directory=child.is_dir())

    shadow_data = shadow / "data"
    shadow_data.mkdir()
    for child in (postapply_root / "data").iterdir():
        if child.name in {"audit", "goals", "kg", "scholarly_sources"}:
            continue
        (shadow_data / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )

    quarantine = repair.read_jsonl(ROOT / repair.QUARANTINE_RELATIVE)

    def quarantined_records(kind: str) -> list[dict]:
        return [row["record"] for row in quarantine if row["record_type"] == kind]

    def rewrite_lines(
        source: Path,
        destination: Path,
        *,
        key,
        replacements: dict[str, dict] | None = None,
        removals: set[str] | None = None,
    ) -> None:
        replacements = replacements or {}
        removals = removals or set()
        output: list[str] = []
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            identifier = str(key(row))
            if identifier in removals:
                continue
            if identifier in replacements:
                line = json.dumps(
                    replacements[identifier], ensure_ascii=False, sort_keys=True
                )
            output.append(line)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(output) + "\n", encoding="utf-8")

    shadow_audit = shadow_data / "audit"
    shadow_audit.mkdir()
    excluded_audit = {
        Path(repair.REPORT_RELATIVE).name,
        Path(repair.QUARANTINE_RELATIVE).name,
        Path(repair.LOCK_RELATIVE).name,
        Path(repair.JOURNAL_RELATIVE).name,
        Path(repair.BACKUP_DIR_RELATIVE).name,
    }
    for child in (postapply_root / "data/audit").iterdir():
        if child.name in excluded_audit:
            continue
        (shadow_audit / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )

    shadow_kg = shadow_data / "kg"
    shadow_kg.mkdir()
    special_kg = {
        "nodes.jsonl",
        "edges.jsonl",
        "publications.bib",
        "publications_bibtex_report.json",
        "e2_patches",
    }
    for child in (postapply_root / "data/kg").iterdir():
        if child.name in special_kg:
            continue
        (shadow_kg / child.name).symlink_to(child, target_is_directory=child.is_dir())

    node_before = {
        repair.node_id(row): row for row in quarantined_records("kg_node_before")
    }
    rewrite_lines(
        postapply_root / "data/kg/nodes.jsonl",
        shadow_kg / "nodes.jsonl",
        key=repair.node_id,
        replacements=node_before,
    )
    edge_lines = (postapply_root / "data/kg/edges.jsonl").read_text(encoding="utf-8")
    removed_edges = quarantined_records("kg_edge_removed")
    (shadow_kg / "edges.jsonl").write_text(
        edge_lines
        + "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in removed_edges
        ),
        encoding="utf-8",
    )

    current_nodes = {
        repair.node_id(row): row
        for row in repair.read_jsonl(postapply_root / "data/kg/nodes.jsonl")
    }
    desired_bib = repair.canonical_sorabji_bibtex_block(current_nodes[repair.PUB_ID])
    applied_bib = (ROOT / repair.PUBLICATIONS_BIB_RELATIVE).read_text(encoding="utf-8")
    # Reverse the two later bibliography-only refinements to recover the exact
    # persisted post-Sorabji container before restoring Sorabji's old entry.
    import scripts.apply_2026_08_24_alexander_sharples_global_p0 as sharples
    import scripts.apply_2026_08_24_hildebrandt_p0_repair as hildebrandt

    live_nodes = {
        repair.node_id(row): row
        for row in repair.read_jsonl(ROOT / "data/kg/nodes.jsonl")
    }
    applied_bib = applied_bib.replace(
        sharples.canonical_publication_bibtex(
            live_nodes[sharples.PUBLICATION_ID]
        ),
        sharples.OLD_BIB_ENTRY,
    )
    hildebrandt_quarantine = repair.read_jsonl(
        ROOT / hildebrandt.QUARANTINE_RELATIVE
    )
    hildebrandt_before = next(
        row["raw_text"]
        for row in hildebrandt_quarantine
        if row["record_type"] == "bibliography_entry_before"
    )
    applied_bib = applied_bib.replace(
        hildebrandt.bib_entry(applied_bib, hildebrandt.BIBTEX_KEY),
        hildebrandt_before,
    )
    assert repair.sha256_bytes(applied_bib.encode("utf-8")) == (
        json.loads((ROOT / repair.REPORT_RELATIVE).read_text(encoding="utf-8"))[
            "output_sha256_preview"
        ][repair.PUBLICATIONS_BIB_RELATIVE]
    )
    before_bib = applied_bib.replace(desired_bib, repair.OLD_BIB_ENTRY)
    assert repair.sha256_bytes(before_bib.encode("utf-8")) == repair.BIB_BEFORE_SHA256
    (shadow / repair.PUBLICATIONS_BIB_RELATIVE).write_text(before_bib, encoding="utf-8")
    before_report = git_head_bytes(repair.PUBLICATIONS_BIB_REPORT_RELATIVE)
    assert repair.sha256_bytes(before_report) == repair.BIB_REPORT_BEFORE_SHA256
    (shadow / repair.PUBLICATIONS_BIB_REPORT_RELATIVE).write_bytes(before_report)

    shadow_e2 = shadow_kg / "e2_patches"
    shadow_e2.mkdir()
    for child in (postapply_root / "data/kg/e2_patches").iterdir():
        if child.name == "sorabji.json":
            continue
        (shadow_e2 / child.name).symlink_to(child, target_is_directory=child.is_dir())
    before_e2 = git_head_bytes("data/kg/e2_patches/sorabji.json")
    assert repair.sha256_bytes(before_e2) == repair.E2_BEFORE_SHA256
    (shadow_e2 / "sorabji.json").write_bytes(before_e2)

    shadow_scholarly = shadow_data / "scholarly_sources"
    shadow_scholarly.mkdir()
    for child in (postapply_root / "data/scholarly_sources").iterdir():
        if child.name == "manifest.jsonl":
            continue
        (shadow_scholarly / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    rewrite_lines(
        postapply_root / "data/scholarly_sources/manifest.jsonl",
        shadow_scholarly / "manifest.jsonl",
        key=lambda row: row.get("publication_dir"),
        removals={
            repair.SOURCE_MANIFEST_DIR,
            "long_sedley1987hp2",
            "hildebrandt2022lazyarguments",
            "sharples1983alexander",
        },
    )
    assert repair.sha256_file(shadow_scholarly / "manifest.jsonl") == (
        repair.SCHOLARLY_MANIFEST_BEFORE_SHA256
    )

    shadow_goals = shadow_data / "goals"
    shadow_goals.mkdir()
    for child in (postapply_root / "data/goals").iterdir():
        if child.name == "sota":
            continue
        (shadow_goals / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )
    shutil.copytree(postapply_root / "data/goals/sota", shadow_goals / "sota")
    registry = shadow_goals / "sota/registry"

    def reverse_later_registry(quarantine_path: Path) -> None:
        """Replay one later wave's registry before-images in the test shadow."""

        rows = repair.read_jsonl(quarantine_path)
        config = {
            "source": (
                "source_id",
                registry / "sources/seed_priority_20260824.jsonl",
            ),
            "evidence": (
                "evidence_id",
                registry / "evidence/seed_priority_20260824.jsonl",
            ),
            "issue": (
                "issue_id",
                registry / "issues/seed_known_20260824.jsonl",
            ),
            "wave": (
                "wave_id",
                registry / "waves/priority_20260824.jsonl",
            ),
            "verification": (
                "verification_id",
                registry / "verifications/sorabji_20260824.jsonl",
            ),
        }
        for kind, (key, default_path) in config.items():
            markers = [
                row
                for row in rows
                if str(row.get("record_type") or "").startswith(
                    f"registry_{kind}_"
                )
            ]
            if not markers:
                continue
            directory = registry / {
                "source": "sources",
                "evidence": "evidence",
                "issue": "issues",
                "wave": "waves",
                "verification": "verifications",
            }[kind]
            files = sorted(directory.glob("*.jsonl"))
            collections = {path: repair.read_jsonl(path) for path in files}
            for marker in markers:
                record_type = str(marker["record_type"])
                if record_type.endswith("_absence_before"):
                    identifier = str(marker[key])
                    for path in collections:
                        collections[path] = [
                            row
                            for row in collections[path]
                            if str(row.get(key)) != identifier
                        ]
                    continue
                if not (
                    record_type.endswith("_before")
                    or record_type.endswith("_removed")
                ):
                    continue
                record = copy.deepcopy(marker["record"])
                identifier = str(record[key])
                replaced = False
                for path in collections:
                    for index, current in enumerate(collections[path]):
                        if str(current.get(key)) == identifier:
                            collections[path][index] = copy.deepcopy(record)
                            replaced = True
                if not replaced:
                    if default_path not in collections:
                        collections[default_path] = []
                    collections[default_path].append(record)
            for path, records in collections.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(repair.serialize_jsonl(records))

    for later_quarantine in (
        ROOT / "data/audit/2026-08-24_alexander_sharples_global_p0_quarantine.jsonl",
        ROOT / "data/audit/2026-08-24_tatian_p0_quarantine.jsonl",
        ROOT / "data/audit/2026-08-24_hildebrandt_p0_quarantine.jsonl",
        ROOT / "data/audit/2026-08-24_long_sedley_vol2_p0_quarantine.jsonl",
    ):
        reverse_later_registry(later_quarantine)

    source_before = {
        row["source_id"]: row
        for row in quarantined_records("registry_source_before")
    }
    evidence_before = {
        row["evidence_id"]: row
        for row in quarantined_records("registry_evidence_before")
    }
    wave_before = {
        row["wave_id"]: row for row in quarantined_records("registry_wave_before")
    }
    evidence_absent = {
        row["evidence_id"]
        for row in quarantine
        if row["record_type"] == "registry_evidence_absence_before"
    }
    issue_absent = {
        row["issue_id"]
        for row in quarantine
        if row["record_type"] == "registry_issue_absence_before"
    }
    verification_absent = {
        row["verification_id"]
        for row in quarantine
        if row["record_type"] == "registry_verification_absence_before"
    }
    rewrite_lines(
        registry / "sources/seed_priority_20260824.jsonl",
        registry / "sources/seed_priority_20260824.jsonl",
        key=lambda row: row.get("source_id"),
        replacements=source_before,
    )
    rewrite_lines(
        registry / "evidence/seed_priority_20260824.jsonl",
        registry / "evidence/seed_priority_20260824.jsonl",
        key=lambda row: row.get("evidence_id"),
        replacements=evidence_before,
        removals=evidence_absent,
    )
    rewrite_lines(
        registry / "issues/seed_known_20260824.jsonl",
        registry / "issues/seed_known_20260824.jsonl",
        key=lambda row: row.get("issue_id"),
        removals=issue_absent,
    )
    rewrite_lines(
        registry / "waves/priority_20260824.jsonl",
        registry / "waves/priority_20260824.jsonl",
        key=lambda row: row.get("wave_id"),
        replacements=wave_before,
    )
    sorabji_verifications = registry / "verifications/sorabji_20260824.jsonl"
    if sorabji_verifications.exists():
        remaining = [
            row
            for row in repair.read_jsonl(sorabji_verifications)
            if row.get("verification_id") not in verification_absent
        ]
        if remaining:
            sorabji_verifications.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                    for row in remaining
                ),
                encoding="utf-8",
            )
        else:
            sorabji_verifications.unlink()

    return shadow


def test_cli_first_write_applied_dry_run_and_repeat_write_are_truthful(
    tmp_path: Path,
    post_sorabji_root: Path,
) -> None:
    shadow = reconstruct_preapply_workspace(tmp_path, post_sorabji_root)
    script = ROOT / repair.SCRIPT_RELATIVE
    reviewed_report = json.loads(
        (ROOT / repair.REPORT_RELATIVE).read_text(encoding="utf-8")
    )
    reviewed_hashes = reviewed_report["output_sha256_preview"]
    prospective = repair.build_plan(shadow)
    assert prospective.counts == EXPECTED_COUNTS
    assert set(prospective.summary["changed_paths"]) == EXPECTED_CHANGED_PATHS
    assert prospective.summary["after_record_hashes"] == reviewed_report[
        "after_record_hashes"
    ]
    composed_hashes = prospective.summary["output_sha256_preview"]
    assert set(composed_hashes) == set(reviewed_hashes)

    def invoke(*arguments: str) -> tuple[dict, str]:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(shadow), *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return json.loads(result.stdout), result.stdout

    first, first_stdout = invoke("--write", "--json")
    assert first["mode"] == "write"
    assert first["status"] == "applied_open_issues_pending_review"
    assert first["write_performed"] is True
    assert json.dumps(first, ensure_ascii=False)  # one parsed document, no trailing text
    assert "write complete" not in first_stdout
    for relative, expected_hash in composed_hashes.items():
        assert repair.sha256_file(shadow / relative) == expected_hash
    assert json.loads(
        (shadow / repair.REPORT_RELATIVE).read_text(encoding="utf-8")
    ) == first
    assert repair.sha256_file(
        shadow / repair.QUARANTINE_RELATIVE
    ) == repair.sha256_file(ROOT / repair.QUARANTINE_RELATIVE)

    applied_paths = [shadow / relative for relative in composed_hashes]
    applied_paths.extend(
        [shadow / repair.REPORT_RELATIVE, shadow / repair.QUARANTINE_RELATIVE]
    )
    applied_bytes = {path: path.read_bytes() for path in applied_paths}

    dry_run, dry_stdout = invoke("--json")
    assert dry_run["mode"] == "dry_run"
    assert dry_run["status"] == "already_applied"
    assert dry_run["write_performed"] is False
    assert json.loads(dry_stdout) == dry_run

    repeated, repeated_stdout = invoke("--write", "--json")
    assert repeated["mode"] == "write"
    assert repeated["status"] == "already_applied"
    assert repeated["write_performed"] is False
    assert json.loads(repeated_stdout) == repeated
    assert "write complete" not in repeated_stdout
    assert {path: path.read_bytes() for path in applied_paths} == applied_bytes


def test_cli_dry_run_writes_nothing(plan: repair.RepairPlan) -> None:
    assert sys.dont_write_bytecode is True
    before = {
        path: (path.read_bytes() if path.exists() else None)
        for path in plan.before_bytes
    }
    report = plan.root / repair.REPORT_RELATIVE
    quarantine = plan.root / repair.QUARANTINE_RELATIVE
    audit_before = {
        report: report.read_bytes() if report.exists() else None,
        quarantine: quarantine.read_bytes() if quarantine.exists() else None,
    }
    pyc_before = pyc_snapshot()
    environment = dict(os.environ)
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / repair.SCRIPT_RELATIVE),
            "--root",
            str(plan.root),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    summary = json.loads(result.stdout)
    assert summary["mode"] == "dry_run"
    assert summary["write_performed"] is False
    assert before == {
        path: (path.read_bytes() if path.exists() else None)
        for path in plan.before_bytes
    }
    assert audit_before == {
        report: report.read_bytes() if report.exists() else None,
        quarantine: quarantine.read_bytes() if quarantine.exists() else None,
    }
    assert pyc_snapshot() == pyc_before
