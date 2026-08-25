import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.apply_2026_08_24_irenaeus_primary_evidence_repair as repair  # noqa: E402


def load_data():
    return (
        repair.read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        repair.read_jsonl(ROOT / "data/kg/edges.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/passages.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/citations.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/manifest.jsonl"),
        repair.read_jsonl(
            ROOT / "data/goals/sota/registry/issues/irenaeus_20260824.jsonl"
        ),
        repair.read_jsonl(
            ROOT / "data/goals/sota/registry/sources/irenaeus_20260824.jsonl"
        ),
        repair.read_jsonl(
            ROOT / "data/goals/sota/registry/evidence/irenaeus_20260824.jsonl"
        ),
        repair.read_jsonl(
            ROOT
            / "data/goals/sota/registry/verifications/irenaeus_20260824.jsonl"
        ),
    )


def load_repaired_data():
    """Return the committed repair or the pure in-memory migration pre-write."""

    data = load_data()
    return repair.transform(*data)[:9]


def load_quarantine():
    path = ROOT / "data/audit/2026-08-24_irenaeus_primary_evidence_quarantine.jsonl"
    if path.exists():
        return repair.read_jsonl(path)
    return repair.transform(*load_data())[9]


def test_exact_role_language_witness_hash_and_snapshot_matrix() -> None:
    data = load_repaired_data()
    nodes, edges, passages, citations, manifest = data[:5]
    repair.validate(nodes, edges, passages, citations, manifest)

    by_node = {repair.node_id(row): row for row in nodes}
    by_passage = {row["passage_id"]: row for row in passages}
    for key, wanted_node_id in repair.NODE_IDS.items():
        spec = repair.PASSAGE_SPECS[key]
        node = by_node[wanted_node_id]
        passage = by_passage[repair.PASSAGE_IDS[key]]
        metadata = repair.metadata(node)
        expected_hash = repair.sha256_text(repair.TEXTS[key])

        assert node["description"] == passage["text_content"] == repair.TEXTS[key]
        assert metadata["text_content_sha256_nfc"] == expected_hash
        assert passage["text_sha256"] == expected_hash
        assert metadata["language"] == passage["language"] == spec["language"]
        assert (
            metadata["passage_role"] == passage["passage_role"] == spec["role"]
        )
        assert metadata["source_artifact_sha256"] == spec["source_sha"]
        assert metadata["scan_sha256"] == spec["scan_sha"]
        assert metadata["scan_page_map_visually_verified"] is True
        assert metadata["citability"] == "citable"
        assert metadata["work_canonical_id"] == repair.WORK_URN
        assert metadata["manifestation_id"] == spec["manifest"]
        assert passage["work_canonical_id"] == spec["manifest"]

        if spec["role"] == "translation":
            assert metadata["translation_type"] == "ancient_human_literal"
            assert passage["translation_type"] == "ancient_human_literal"
            assert metadata["source_passage_status"] == (
                "lost_continuous_greek_not_mapped"
            )
            assert "source_passage_id" not in metadata
            assert "source_passage_id" not in passage
        else:
            assert metadata["attestation_type"] == "indirect_fragment"
            assert metadata["transmitting_author_node_id"] == repair.TRANSMITTER_NODE
            assert metadata["transmitting_work"] == "Sacra Parallela"
            assert metadata["witness_reference"].endswith("p. 63")

    snapshots = {
        row["kg_node_id"]: row["passage_id"]
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("kg_node_id") in set(repair.NODE_IDS.values())
    }
    assert snapshots == {
        repair.NODE_IDS[key]: repair.PASSAGE_IDS[key] for key in repair.TEXTS
    }


def test_fragment_21_discontinuity_is_explicit_and_never_concatenated() -> None:
    nodes, _edges, passages, _citations, manifest = load_repaired_data()[:5]
    by_node = {repair.node_id(row): row for row in nodes}
    by_passage = {row["passage_id"]: row for row in passages}

    first = by_passage[repair.PASSAGE_IDS["iv_37_2_grc_frag21_seg1"]]
    second = by_passage[repair.PASSAGE_IDS["iv_37_4_grc_frag21_seg2"]]
    assert first["fragment_segment_index"] == 1
    assert first["fragment_lines"] == "1-19"
    assert first["canonical_locus"] == "IV.37.2"
    assert second["fragment_segment_index"] == 2
    assert second["fragment_lines"] == "20-29"
    assert second["canonical_locus"] == "IV.37.4"
    assert "Καὶ γὰρ αὐτὸ τὸ εὐαγγέλιον" not in first["text_content"]
    assert "Καὶ γὰρ αὐτὸ τὸ εὐαγγέλιον" in second["text_content"]

    first_metadata = repair.metadata(
        by_node[repair.NODE_IDS["iv_37_2_grc_frag21_seg1"]]
    )
    second_metadata = repair.metadata(
        by_node[repair.NODE_IDS["iv_37_4_grc_frag21_seg2"]]
    )
    assert first_metadata["fragment_segment_count"] == 2
    assert second_metadata["fragment_segment_count"] == 2

    greek_manifest = next(
        row for row in manifest if row.get("canonical_id") == repair.GRC4_MANIFEST
    )
    assert greek_manifest["fragment_segmentation"]["21"] == [
        "IV.37.2:lines1-19",
        "IV.37.4:lines20-29",
    ]


def test_false_twins_and_all_ten_legacy_citations_are_quarantined() -> None:
    nodes, edges, passages, citations, _manifest = load_repaired_data()[:5]
    assert not (repair.LEGACY_NODE_IDS & {repair.node_id(row) for row in nodes})
    assert not (
        repair.LEGACY_PASSAGE_IDS
        & {str(row.get("passage_id")) for row in passages}
    )
    assert not any(
        repair.edge_source(row) in repair.LEGACY_NODE_IDS
        or repair.edge_target(row) in repair.LEGACY_NODE_IDS
        for row in edges
    )
    assert not any(
        row.get("passage_id") in repair.LEGACY_PASSAGE_IDS for row in citations
    )

    quarantine = load_quarantine()
    old_nodes = {
        repair.node_id(row["record"])
        for row in quarantine
        if row.get("record_type") == "kg_node"
    }
    old_passages = {
        row["record"].get("passage_id")
        for row in quarantine
        if row.get("record_type") == "corpus_passage"
    }
    old_citations = [
        row for row in quarantine if row.get("record_type") == "citation"
    ]
    assert old_nodes == repair.LEGACY_NODE_IDS
    assert old_passages == repair.LEGACY_PASSAGE_IDS
    assert len(old_citations) == 10

    exact_node_ids = set(repair.NODE_IDS.values())
    exact_passage_ids = set(repair.PASSAGE_IDS.values())
    serialized_active = "\n".join(
        json.dumps(row, ensure_ascii=False)
        for row in [
            *(row for row in nodes if repair.node_id(row) in exact_node_ids),
            *(
                row
                for row in passages
                if str(row.get("passage_id")) in exact_passage_ids
            ),
        ]
    )
    assert "passage_irenaeus_ah_3_20_en" not in serialized_active
    assert "passage_irenaeus_ah_4_37_en" not in serialized_active
    assert "claude-opus-4-6" not in serialized_active


def test_dependents_are_rewired_only_when_directly_entailed() -> None:
    nodes, edges, _passages, citations, _manifest = load_repaired_data()[:5]
    by_node = {repair.node_id(row): row for row in nodes}
    frag21_uuid = repair.PASSAGE_IDS["iv_37_2_grc_frag21_seg1"]

    assert any(
        row.get("kg_node_id")
        == "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed"
        and row.get("passage_id") == frag21_uuid
        and row.get("citation_type") == "primary_source"
        for row in citations
    )
    assert any(
        row.get("kg_node_id")
        == "concept_autexousion_christian_freedom_u1v2w3x4"
        and row.get("passage_id") == frag21_uuid
        and row.get("citation_type") == "evidenced_by"
        for row in citations
    )
    assert any(
        row.get("kg_node_id")
        == "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7"
        and row.get("passage_id") == frag21_uuid
        and row.get("citation_type") == "evidenced_by"
        for row in citations
    )
    assert not any(
        row.get("kg_node_id")
        == "argument_furst_2022_irenaeus_against_gnostic_natures"
        and row.get("passage_id") in set(repair.PASSAGE_IDS.values())
        for row in citations
    )
    furst = repair.metadata(
        by_node["argument_furst_2022_irenaeus_against_gnostic_natures"]
    )
    assert furst["primary_locus_grounding_status"].startswith(
        "blocked_pending_exact_AH_IV.37.6-7"
    )
    assert by_node[
        "argument_furst_2022_irenaeus_against_gnostic_natures"
    ]["needs_evidence"] is True

    recap = repair.metadata(by_node["argument_irenaeus_recapitulation_theodicy"])
    premise_sources = {
        row["id"]: row.get("primary_sources") for row in recap["premises"]
    }
    exact_iii = repair.NODE_IDS["iii_20_3_lat"]
    assert premise_sources["P1"] == []
    assert premise_sources["P2"] == [exact_iii]
    assert premise_sources["P3"] == [exact_iii]
    assert premise_sources["P5"] == [exact_iii]
    assert recap["conclusion"]["primary_sources"] == []
    assert "τὴν ἀσθένειαν τοῦ ἀνθρώπου" not in recap["premises"][2]["text"]

    old_edge_ids = {
        row["record"].get("edge_id")
        for row in load_quarantine()
        if row.get("record_type") == "kg_edge"
    }
    assert old_edge_ids.isdisjoint({repair.edge_id(row) for row in edges})


def test_registry_records_scope_passes_without_closing_broader_issue() -> None:
    *_, issues, sources, evidence, verifications = load_repaired_data()
    issue = next(row for row in issues if row["issue_id"] == repair.ISSUE_ID)
    source = next(row for row in sources if row["source_id"] == repair.SOURCE_ID)
    assert issue["status"] == "open"
    assert issue["progress"]["p0_false_twins_quarantined"] is True
    assert issue["progress"]["armenian_ingested"] is False
    assert issue["progress"]["full_free_will_locus_coverage"] is False
    assert source["identity_status"] == "provisional"
    assert source["coverage"]["state"] == "partial"
    assert set(repair.EVIDENCE_IDS) <= {row["evidence_id"] for row in evidence}

    irenaeus_verifications = [
        row for row in verifications if str(row.get("target_id", "")).startswith(
            "issue_irenaeus_"
        )
    ]
    assert {row["stage"] for row in irenaeus_verifications} >= {
        "independent",
        "adversarial",
    }
    independent = next(
        row for row in irenaeus_verifications if row["stage"] == "independent"
    )
    assert "read_only_source_chain" in independent["verifier"]["verifier_id"]
    assert independent["verdict"] == "pass"
    evidence_verifications = [
        row
        for row in verifications
        if row.get("target_id") in repair.EVIDENCE_IDS
    ]
    assert len(evidence_verifications) == 4
    assert {
        (row["target_id"], row["stage"]) for row in evidence_verifications
    } == {
        (evidence_id, stage)
        for evidence_id in repair.EVIDENCE_IDS
        for stage in ("independent", "adversarial")
    }
    assert all(row["verdict"] == "pass" for row in evidence_verifications)


def test_repair_is_offline_idempotent() -> None:
    raw = load_data()
    first = repair.transform(*raw)
    second = repair.transform(*first[:9])
    assert second[:9] == first[:9]
    assert second[9] == []
    assert second[10] == []

    report_path = (
        ROOT / "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json"
    )
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"].endswith("broader_irenaeus_issue_remains_open")
        assert report["fragment_21"]["status"] == (
            "preserved_as_two_discontinuous_passage_units"
        )
        assert len(report["citation_reconciliation"]) == 10


def test_legacy_preimage_is_complete_or_preserved_verbatim_in_quarantine() -> None:
    raw = load_data()
    node_ids = {repair.node_id(row) for row in raw[0]}
    passage_ids = {str(row.get("passage_id")) for row in raw[2]}
    legacy_citations = [
        row for row in raw[3] if row.get("passage_id") in repair.LEGACY_PASSAGE_IDS
    ]
    if node_ids >= repair.LEGACY_NODE_IDS:
        assert passage_ids >= repair.LEGACY_PASSAGE_IDS
        assert len(legacy_citations) == 10
        assert not (set(repair.NODE_IDS.values()) & node_ids)
        return

    quarantine = load_quarantine()
    assert {
        repair.node_id(row["record"])
        for row in quarantine
        if row.get("record_type") == "kg_node"
    } == repair.LEGACY_NODE_IDS
    assert len(
        [row for row in quarantine if row.get("record_type") == "citation"]
    ) == 10


def test_write_transaction_rejects_concurrent_drift_without_overwrite(tmp_path) -> None:
    target = tmp_path / "state.jsonl"
    target.write_text('{"state":"frozen"}\n', encoding="utf-8")
    frozen_hash = repair.sha256_file(target)
    target.write_text('{"state":"concurrent-change"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="concurrent drift"):
        repair.write_transaction(
            {target: b'{"state":"migration"}\n'},
            {target: frozen_hash},
        )

    assert target.read_text(encoding="utf-8") == '{"state":"concurrent-change"}\n'
