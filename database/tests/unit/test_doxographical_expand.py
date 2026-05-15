"""Tests for the doxographical mapping expansion scripts."""

from __future__ import annotations

import json
from pathlib import Path

from database.scripts import (
    apply_mappings_to_snapshot,
    crosslink_refs_to_passages,
    harvest_scholarly_refs,
    merge_fragment_mappings,
)


def test_harvest_normalize_ref() -> None:

    pat = harvest_scholarly_refs.PATTERNS["SVF"]
    m = pat.search("Cf. SVF II, 974")
    assert m is not None
    assert harvest_scholarly_refs.normalize_ref("SVF", m) == "SVF II.974"

    pat = harvest_scholarly_refs.PATTERNS["LS"]
    m = pat.search("(LS 62C)")
    assert m is not None
    assert harvest_scholarly_refs.normalize_ref("LS", m) == "LS 62C"

    pat = harvest_scholarly_refs.PATTERNS["DK"]
    m = pat.search("DK 22B1 cited by")
    assert m is not None
    assert harvest_scholarly_refs.normalize_ref("DK", m) == "DK 22B1"


def test_crosslink_parses_cicero_de_fato_locus() -> None:
    passages = {"passage_cic_fat_42": {}, "passage_cic_fat_43": {}}
    ctx = "famous example of Chrysippus: Cicero, On fate 42-3 (= LS 62C 8-9)"
    cands = crosslink_refs_to_passages.parse_locus(ctx, passages)
    pids = {c.passage_id for c in cands}
    # We expect at least the explicit "fato 42"
    assert "passage_cic_fat_42" in pids


def test_crosslink_parses_aulus_gellius_locus() -> None:
    passages = {"passage_gellius_na_vii_2_7_2_11": {}}
    ctx = "Gell., N. A., VII, 2, 11 (SVF II 1000): sic ordo et ratio"
    cands = crosslink_refs_to_passages.parse_locus(ctx, passages)
    pids = {c.passage_id for c in cands}
    assert "passage_gellius_na_vii_2_7_2_11" in pids


def test_crosslink_parses_dl_locus() -> None:
    passages = {"passage_dl_lives_7_1_87": {}, "passage_dl_lives_10_1_133": {}}
    ctx1 = "SVF III.4 (=DL Vit. VII.87 [for Chrysippus])"
    ctx2 = "Diogenes Laertius, at 10.133 (LS 20A), Epicurus writes"
    c1 = crosslink_refs_to_passages.parse_locus(ctx1, passages)
    c2 = crosslink_refs_to_passages.parse_locus(ctx2, passages)
    assert any(c.passage_id == "passage_dl_lives_7_1_87" for c in c1)
    assert any(c.passage_id == "passage_dl_lives_10_1_133" for c in c2)


def test_crosslink_philosopher_hint_svf() -> None:
    name, node = crosslink_refs_to_passages.philosopher_hint("SVF", "SVF II.974")
    assert name == "Chrysippus"
    assert node == "person_chrysippus_280_206bce_i9j0k1l2"
    name, node = crosslink_refs_to_passages.philosopher_hint("SVF", "SVF I.216")
    assert name == "Zeno of Citium"


def test_crosslink_philosopher_hint_dk() -> None:
    name, node = crosslink_refs_to_passages.philosopher_hint("DK", "DK 22B1")
    assert name == "Heraclitus"
    name, node = crosslink_refs_to_passages.philosopher_hint("DK", "DK 68B118")
    assert name == "Democritus"


def test_crosslink_no_false_positives_for_arbitrary_numbers() -> None:
    # Sextus is intentionally disabled; ensure "M. 30" in arbitrary context
    # does not produce a passage_sext_30 mapping
    passages = {"passage_sext_30": {}}
    ctx = "Aristotle, De an. III.4; cf. SVF I.84 (=Stob. Ecl. II.77, 20 W) [for Zeno]; M. 30"
    cands = crosslink_refs_to_passages.parse_locus(ctx, passages)
    pids = {c.passage_id for c in cands}
    assert "passage_sext_30" not in pids


def test_merge_collections_dedupes_by_collection_and_reference() -> None:
    a = [{"collection": "SVF", "reference": "II.974", "verification_source": "Bobzien"}]
    b = [
        {"collection": "SVF", "reference": "II.974", "verification_source": "DOCTORAT"},
        {"collection": "LS", "reference": "62C"},
    ]
    merged = merge_fragment_mappings.merge_collections(a, b)
    keys = {(c["collection"], c["reference"]) for c in merged}
    assert keys == {("SVF", "II.974"), ("LS", "62C")}
    # First source (a) wins on verification_source
    svf = next(c for c in merged if c["collection"] == "SVF")
    assert svf["verification_source"] == "Bobzien"


def test_merger_prefers_curated_source() -> None:
    rows_by_source = {
        "curated": [
            {
                "passage_id": "passage_cic_fat_42",
                "attestation_type": "doxographical_fragment",
                "confidence": "high",
                "fragment_collections": [{"collection": "SVF", "reference": "II.974"}],
                "doxographical_source": "curated",
            }
        ],
        "auto_doctorat": [
            {
                "passage_id": "passage_cic_fat_42",
                "attestation_type": "doxographical_fragment",
                "confidence": "medium",
                "fragment_collections": [{"collection": "LS", "reference": "62C"}],
                "doxographical_source": "auto_doctorat",
            }
        ],
    }
    out = merge_fragment_mappings.merge(rows_by_source)
    assert len(out) == 1
    row = out[0]
    assert row["confidence"] == "high"
    assert row["doxographical_source"] == "curated"
    keys = {(c["collection"], c["reference"]) for c in row["fragment_collections"]}
    assert keys == {("SVF", "II.974"), ("LS", "62C")}
    assert row["doxographical_contributing_sources"] == ["auto_doctorat", "curated"]


def test_apply_mapping_remaps_stale_philosopher_ids(tmp_path: Path) -> None:
    mapping_file = tmp_path / "m.jsonl"
    mapping_file.write_text(
        json.dumps(
            {
                "passage_id": "passage_x",
                "philosopher_node_id": "person_zeno_of_citium",
                "attestation_type": "doxographical_fragment",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    mappings = apply_mappings_to_snapshot.load_mappings(mapping_file)
    assert (
        mappings["passage_x"]["philosopher_node_id"] == "person_zeno_citium_334_262bce"
    )


def test_apply_merge_metadata_preserves_existing_fields() -> None:
    existing = {
        "author": "Cicero",
        "language": "lat",
        "doxographical_confidence": "low",
    }
    mapping = {
        "attestation_type": "doxographical_fragment",
        "fragment_collections": [{"collection": "SVF", "reference": "II.974"}],
        "confidence": "high",
    }
    out = apply_mappings_to_snapshot.merge_metadata(existing, mapping)
    assert out["author"] == "Cicero"
    assert out["language"] == "lat"
    assert out["attestation_type"] == "doxographical_fragment"
    assert out["fragment_collections"][0]["reference"] == "II.974"
    assert out["doxographical_confidence"] == "high"
