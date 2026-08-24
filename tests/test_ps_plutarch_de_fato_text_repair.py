import json
from pathlib import Path

import scripts.apply_2026_08_24_ps_plutarch_de_fato_text_repair as repair

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    return (
        repair.read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        repair.read_jsonl(ROOT / "data/kg/edges.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/passages.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/citations.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/manifest.jsonl"),
    )


def test_pinned_greek_and_published_english_are_exact_distinct_manifestations() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    repair.validate(nodes, edges, passages, citations, manifest)

    corpus = [
        row
        for row in passages
        if row.get("work_canonical_id")
        in {repair.GRC_MANIFEST_ID, repair.ENG_MANIFEST_ID}
    ]
    assert len(corpus) == 24
    assert {row["language"] for row in corpus} == {"grc", "eng"}
    assert all(row["source_commit"] == repair.UPSTREAM_COMMIT for row in corpus)
    assert all(row["source_artifact_sha256"] for row in corpus)

    english = [row for row in corpus if row["language"] == "eng"]
    assert all(row["translation_type"] == "published_human" for row in english)
    assert all(
        row["translator"] == "A. G. (as credited in the edition)" for row in english
    )
    for row in english:
        section = int(row["sequence_number"])
        assert row["source_passage_id"] == repair.GOOD_GREEK_UUIDS[section]
        assert row["translation_of_work"] == repair.WORK_URN
        assert row["aligned_to_manifestation"] == repair.GRC_MANIFEST_ID
        assert "translation_of_edition" not in row

    for row in corpus:
        section = int(row["sequence_number"])
        assert row["stephanus_range"] == repair.SECTION_STEPHANUS[section]
        assert repair.SECTION_STEPHANUS[section] in row["canonical_ref"]

    manifests = {
        row["canonical_id"]: row
        for row in manifest
        if row.get("canonical_id") in {repair.GRC_MANIFEST_ID, repair.ENG_MANIFEST_ID}
    }
    assert set(manifests) == {repair.GRC_MANIFEST_ID, repair.ENG_MANIFEST_ID}
    assert manifests[repair.GRC_MANIFEST_ID]["cts_urn"] == repair.GRC_VERSION
    assert manifests[repair.ENG_MANIFEST_ID]["cts_urn"] == repair.ENG_VERSION
    assert manifests[repair.ENG_MANIFEST_ID]["translation_of_work"] == repair.WORK_URN
    assert (
        manifests[repair.ENG_MANIFEST_ID]["aligned_to_manifestation"]
        == repair.GRC_MANIFEST_ID
    )
    assert "translation_of" not in manifests[repair.ENG_MANIFEST_ID]


def test_exact_snapshot_nodes_match_corpus_and_analysis_cannot_self_verify() -> None:
    nodes, _edges, passages, citations, _manifest = load_data()
    by_node = {repair.node_id(node): node for node in nodes}
    by_passage = {row["passage_id"]: row for row in passages}

    exact_ids = {
        repair.exact_node_id(language, section)
        for language in ("grc", "eng")
        for section in range(12)
    }
    for wanted in exact_ids:
        node = by_node[wanted]
        data = repair.metadata(node)
        assert node["description"] == by_passage[data["passage_id"]]["text_content"]
        assert data["citability"] == "citable"
        match = repair.EXACT_NODE_RE.fullmatch(wanted)
        assert match is not None
        assert data["stephanus_range"] == repair.SECTION_STEPHANUS[int(match.group(2))]

    exact_snapshots = {
        row["kg_node_id"]: row["passage_id"]
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("kg_node_id") in exact_ids
    }
    assert set(exact_snapshots) == exact_ids

    for section in range(1, 20):
        wanted = f"passage_plut_fat_{section}"
        data = repair.metadata(by_node[wanted])
        assert data["citability"] == "non_citable"
        assert data["passage_role"] == "editorial_analysis"
        assert "cts_urn" not in data
        assert not any(
            row.get("kg_node_id") == wanted
            and row.get("citation_type") == "snapshot_passage_node"
            for row in citations
        )
        exact_section = repair.ANALYTICAL_PRIMARY_SECTION.get(section)
        if exact_section is not None:
            assert data["primary_attestation"] == {
                "transmitting_author": repair.AUTHOR_NODE,
                "transmitting_work": repair.WORK_NODE,
                "transmitting_passage": repair.exact_node_id("grc", exact_section),
            }


def test_pseudonymous_and_translation_edges_are_unambiguous() -> None:
    nodes, edges, _passages, _citations, _manifest = load_data()
    node_ids = {repair.node_id(node) for node in nodes}
    assert repair.AUTHOR_NODE in node_ids

    assert not any(repair.is_false_genuine_plutarch_attribution(edge) for edge in edges)
    translation_pairs = {
        (
            str(edge.get("source_id") or edge.get("source")),
            str(edge.get("target_id") or edge.get("target")),
        )
        for edge in edges
        if edge.get("relation") == "translation_of"
        and repair.EXACT_NODE_RE.fullmatch(
            str(edge.get("source_id") or edge.get("source") or "")
        )
    }
    assert translation_pairs == {
        (
            repair.exact_node_id("eng", section),
            repair.exact_node_id("grc", section),
        )
        for section in range(12)
    }


def test_legacy_machine_translation_and_foreign_cts_identity_are_quarantined() -> None:
    nodes, _edges, passages, citations, _manifest = load_data()
    assert not any(
        repair.REMOVED_NODE_RE.fullmatch(repair.node_id(node)) for node in nodes
    )
    assert not any("tlg9857.tlg062" in json.dumps(row) for row in passages)
    assert not any(
        row.get("work_canonical_id") == "urn_cts_greeklit_tlg0007_tlg099_eng"
        for row in passages
    )
    assert not any(
        row.get("passage_id") in repair.LEGACY_CITATION_REMAP for row in citations
    )
    passage_ids = {row["passage_id"] for row in passages}
    assert all(row["passage_id"] in passage_ids for row in citations)

    quarantine = ROOT / "data/audit/2026-08-24_ps_plutarch_de_fato_quarantine.jsonl"
    rows = repair.read_jsonl(quarantine)
    assert len(rows) == 213
    serialized = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    assert "tlg9857.tlg062" in serialized
    assert any(
        row.get("record_type") == "kg_node"
        and repair.metadata(row["record"]).get("translation_type") == "machine"
        for row in rows
    )


def test_repair_is_offline_idempotent(monkeypatch) -> None:
    data = load_data()

    def fail_fetch():
        raise AssertionError("an already repaired snapshot must not use the network")

    monkeypatch.setattr(repair, "fetch_source_sections", fail_fetch)
    result = repair.transform(*data)
    assert result[:5] == data
    assert result[5] == []
    assert result[6] == []

    report = json.loads(
        (ROOT / "data/audit/2026-08-24_ps_plutarch_de_fato_text_repair.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        "independent and adversarial scholarly review still required"
        in report["status"]
    )
