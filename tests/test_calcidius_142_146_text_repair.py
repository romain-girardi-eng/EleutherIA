import json
from pathlib import Path

import scripts.apply_2026_08_24_calcidius_142_146_text_repair as repair

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    return (
        repair.read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        repair.read_jsonl(ROOT / "data/kg/edges.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/passages.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/citations.jsonl"),
        repair.read_jsonl(ROOT / "data/corpus/manifest.jsonl"),
    )


def test_calcidius_sections_are_exact_fingerprinted_latin_not_placeholders() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    repair.validate(nodes, edges, passages, citations, manifest)

    corpus = {
        int(row["sequence_number"]): row
        for row in passages
        if row.get("work_canonical_id") == repair.MANIFEST_ID
    }
    assert set(corpus) == set(range(142, 147))
    assert "arbitrio ac uoluntate" in corpus[142]["text_content"]
    assert "praecedit prouidentia, sequitur fatum" in corpus[143]["text_content"]
    assert "ut putat Chrysippus" in corpus[144]["text_content"]
    assert "nostri arbitrii nostrique iuris" in corpus[145]["text_content"]
    assert "quae fatum uocatur" in corpus[146]["text_content"]
    assert all("to be fetched" not in row["text_content"] for row in corpus.values())
    assert all(row["source_artifact_sha256"] == repair.SOURCE_SHA256 for row in corpus.values())
    assert all(row["scan_sha256"] == repair.SCAN_SHA256 for row in corpus.values())


def test_work_identity_page_map_and_exact_snapshot_contract() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    by_node = {repair.node_id(node): node for node in nodes}
    by_passage = {row["passage_id"]: row for row in passages}

    work = repair.metadata(by_node[repair.WORK_NODE])
    assert work["canonical_id"] == repair.WORK_URN
    assert work["catalog_edition_urn"] == repair.CATALOG_EDITION_URN
    assert work["digiliblt_id"] == "DLT000070"
    assert work["digiliblt_identifiers"] == {
        "dll_catalog_linked_record": "DLT000070",
        "digiliblt_later_edition_record": "DLT000607",
    }

    for section, wanted_node_id in repair.NODE_IDS.items():
        node = by_node[wanted_node_id]
        data = repair.metadata(node)
        passage = by_passage[data["passage_id"]]
        assert node["description"] == passage["text_content"]
        assert data["printed_page_range"] == repair.SECTION_PAGES[section]["printed"]
        assert data["pdf_page_range"] == repair.SECTION_PAGES[section]["pdf"]
        assert data["scan_page_map_visually_verified"] is True
        assert data["char_length"] == len(node["description"])
        assert data["word_count"] == len(node["description"].split())
        assert "school" not in data
        assert "doxographical_source" not in data
        assert "doxographical_confidence" not in data
        assert node["school"] is None
        assert any(
            row.get("kg_node_id") == wanted_node_id
            and row.get("passage_id") == passage["passage_id"]
            and row.get("citation_type") == "snapshot_passage_node"
            for row in citations
        )

    current_manifest = [row for row in manifest if row.get("canonical_id") == repair.MANIFEST_ID]
    assert len(current_manifest) == 1
    assert current_manifest[0]["alternate_identifiers"]["digiliblt"] == "DLT000070"
    assert current_manifest[0]["alternate_identifiers"][
        "digiliblt_later_edition_record"
    ] == "DLT000607"
    assert not any(
        repair.edge_id(edge) in repair.REMOVED_UNSUPPORTED_EDGES for edge in edges
    )
    for wanted_node_id in repair.NODE_IDS.values():
        authors = {
            str(edge.get("target") or edge.get("target_id"))
            for edge in edges
            if edge.get("relation") == "authored_by"
            and str(edge.get("source") or edge.get("source_id")) == wanted_node_id
        }
        assert authors == {repair.PERSON_NODE}


def test_calcidius_religious_and_school_classification_is_not_overstated() -> None:
    nodes, _edges, _passages, _citations, _manifest = load_data()
    by_node = {repair.node_id(node): node for node in nodes}
    person = by_node[repair.PERSON_NODE]
    data = repair.metadata(person)
    assert data["classification_status"] == (
        "platonist_author_exact_school_and_religious_affiliation_disputed"
    )
    assert person["school"] is None
    assert "does not assert Christian or Neoplatonist membership as fact" in person["description"]


def test_placeholders_and_wrong_digiliblt_identity_are_quarantined() -> None:
    quarantine = ROOT / "data/audit/2026-08-24_calcidius_142_146_quarantine.jsonl"
    rows = repair.read_jsonl(quarantine)
    assert len(rows) == 20
    serialized = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    assert "to be fetched from digilibLT" in serialized
    assert "digiliblt_dlt000607_lat" in serialized
    assert "Christian Neoplatonist" in serialized

    followup = (
        ROOT
        / "data/audit/2026-08-24_calcidius_142_146_independent_review_quarantine.jsonl"
    )
    followup_rows = repair.read_jsonl(followup)
    assert len(followup_rows) == 12
    assert sum(row["record_type"] == "kg_edge" for row in followup_rows) == 5
    assert sum(row["record_type"] == "kg_node_before" for row in followup_rows) == 6
    assert sum(row["record_type"] == "manifest_before" for row in followup_rows) == 1


def test_calcidius_repair_is_offline_idempotent_and_corpus_has_no_dangling_uuid(monkeypatch) -> None:
    data = load_data()

    def fail_fetch():
        raise AssertionError("an already repaired snapshot must not use the network")

    monkeypatch.setattr(repair, "fetch_source_sections", fail_fetch)
    result = repair.transform(*data)
    assert result[:5] == data
    assert result[5] == []
    assert result[6] == []

    passage_ids = {row["passage_id"] for row in data[2]}
    assert all(row["passage_id"] in passage_ids for row in data[3])
