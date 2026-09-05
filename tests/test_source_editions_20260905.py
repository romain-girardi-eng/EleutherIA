"""Source-to-corpus contracts: conventional loci, faithful text, distinct witnesses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from scripts.apply_2026_09_05_source_editions import tei_reading
from scripts.data_2026_09_05_source_editions import SOURCES
from scripts.sync_corpus_to_db import load_corpus_payload

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    def rows(path):
        return [json.loads(line) for line in (ROOT / path).read_text().splitlines()]

    return {
        "nodes": {n["id"]: n for n in rows("data/kg/nodes.jsonl")},
        "passages": {p["passage_id"]: p for p in rows("data/corpus/passages.jsonl")},
        "citations": rows("data/corpus/citations.jsonl"),
        "manifest": {m["canonical_id"]: m for m in rows("data/corpus/manifest.jsonl")},
    }


def metadata(node):
    value = node["metadata"]
    return json.loads(value) if isinstance(value, str) else value


def test_cicero_all_48_sections_are_exact_primary_twins_with_edition_provenance(data):
    for section in range(1, 49):
        n = data["nodes"][f"passage_cic_fat_{section}"]
        m = metadata(n)
        p = data["passages"][m["corpus_passage_id"]]
        assert n["description"] == p["text_content"]
        assert (
            m["cts_urn"]
            == p["cts_urn"]
            == f"urn:cts:latinLit:phi0474.phi054.perseus-lat1:{section}"
        )
        assert m["provenance"]["source_sha256"] == SOURCES["cicero"]["sha256"]
        assert any(
            c["kg_node_id"] == n["id"]
            and c["passage_id"] == p["passage_id"]
            and c["citation_type"] == "snapshot_passage_node"
            for c in data["citations"]
        )
    text = data["nodes"]["passage_cic_fat_41"]["description"]
    assert text.startswith("Chrysippus autem cum et necessitatem inprobaret")
    assert (
        "adiuvantibus antecedentibus et proximis" not in text
    )  # deleted reading remains in raw TEI, not reading text


def test_tei_reader_excludes_apparatus_without_losing_following_text():
    p = ET.fromstring(
        "<p>Keep <del>deleted</del>this <note>apparatus</note>reading.</p>"
    )
    assert tei_reading(p) == "Keep this reading."


def test_dla_uses_cpl260_and_never_the_city_of_god_cts_identity(data):
    nodes = [
        n for n in data["nodes"].values() if n["id"].startswith("passage_aug_dla_")
    ]
    assert len(nodes) == 170
    for n in nodes:
        m = metadata(n)
        p = data["passages"][m["corpus_passage_id"]]
        assert m["cts_urn"] is None and p["cts_urn"] is None
        assert m["canonical_work_id"] == "cpl260"
        assert m["source_span_id"].startswith("LA_")
        assert n["description"] == p["text_content"]
        assert "Migne" in m["edition"]
    assert (
        metadata(data["nodes"]["work_de_libero_arbitrio"])["work_canonical_id"]
        == "cpl260"
    )


def test_city_of_god_verified_chapters_replace_legacy_quotation_evidence(data):
    exact = [
        n
        for n in data["nodes"].values()
        if n["id"].startswith("passage_augustine_civ_")
        and n["id"].endswith("_hoffmann")
    ]
    assert len(exact) == 81
    for n in exact:
        m = metadata(n)
        p = data["passages"][m["corpus_passage_id"]]
        assert n["description"] == p["text_content"]
        assert m["cts_urn"].startswith("urn:cts:latinLit:stoa0040.stoa003.opp-lat3:")
        assert m.get("citability") != "discoverable_only"
    n = data["nodes"]["passage_aug_civ_5_10_2"]
    m = metadata(n)
    assert m["work_title"] == "De Civitate Dei"
    assert m["canonical_ref"] == "De Civitate Dei 5.10, paragraph 2"
    assert (
        m["cts_urn"] is None
    )  # paragraph numbering must not pretend to be the edition's CTS hierarchy
    assert m["parent_cts_urn"].endswith(":5.10")
    assert n["description"] == data["passages"][m["corpus_passage_id"]]["text_content"]
    legacy = [
        p
        for p in data["passages"].values()
        if p.get("work_canonical_id")
        in ["augustine_civitate_legacy_notes_lat", "augustine_civitate_editorial_eng"]
    ]
    assert len(legacy) == 160 and all(p["passage_role"] == "paraphrase" for p in legacy)


def test_dihle_reference_is_the_visually_checked_printed_page(data):
    m = metadata(data["nodes"]["scholarly_argument_dihle_greek_concept_of_will_0"])
    assert m["page_range"] == m["quote_page"] == "68"
    assert m["needs_page_verification"] is False
    assert m["page_adjudication"]["pdf_page"] == 75
    assert len(m["page_adjudication"]["pdf_sha256"]) == 64


def test_romans_has_one_declared_chapter_and_a_real_corpus_twin(data):
    n = data["nodes"]["passage_paul_romans_9"]
    m = metadata(n)
    assert m["cts_urn"] == "urn:cts:greekLit:tlg0031.tlg006.perseus-grc2:9"
    assert n["description"] == data["passages"][m["corpus_passage_id"]]["text_content"]
    assert len(n["description"].split("\n\n")) == 33
    assert data["manifest"]["romans_westcott_hort_perseus_grc2"]["passages"] == 1


def test_gold_french_translations_remain_french_in_the_actual_loader(data):
    payload = load_corpus_payload()
    # The loader's tuple schema: id, canonical_id, title, author, language...
    from scripts.sync_corpus_to_db import work_uuid

    ids = {
        work_uuid("origen_principiis_sc268_fra"),
        work_uuid("origen_philocalia_sc226_fra"),
    }
    rows = [w for w in payload.works if w[0] in ids]
    assert len(rows) == 2
    assert all(row[4] == "fra" for row in rows)
    for pid in [
        "ae853539-5bf0-592e-9323-f4dad81d7fc8",
        "5d4a53e1-3e27-5179-98b4-1aa1231218f3",
        "481e3e44-0c73-54f3-9190-73f09e332def",
    ]:
        assert data["passages"][pid]["language"] == "fra"
        assert data["passages"][pid]["passage_role"] == "translation"


def test_pinned_primary_source_bytes_are_unchanged():
    for source in SOURCES.values():
        raw = (ROOT / "data/corpus/sources/2026-09-05" / source["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
