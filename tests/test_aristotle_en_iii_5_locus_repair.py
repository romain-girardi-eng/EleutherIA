from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path

from scripts.apply_2026_08_24_aristotle_en_iii_5_locus_repair import (
    CORRUPT_SYNTHESIS_EN_NODE,
    CORRUPT_SYNTHESIS_PASSAGE,
    ENGLISH_1113,
    ENGLISH_NODE_1113,
    GREEK_1113,
    GREEK_NODE_1113,
    GREEK_NODE_1114,
    PASSAGE_1113_ENG,
    PASSAGE_1113_GRC,
    PASSAGE_1114_ENG,
    PASSAGE_1114_GRC,
    PASSAGE_PROHAIRESIS,
    STAMP,
    SYNTHESIS_NODE,
    citation_key,
    metadata,
    node_id,
    read_jsonl,
    transform,
    validate_repaired_state,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
QUARANTINE = DATA / "audit/2026-08-24_aristotle_en_iii_5_quarantine.jsonl"
FOLLOWUP_QUARANTINE = (
    DATA / "audit/2026-08-24_aristotle_en_iii_5_manifest_gap_quarantine.jsonl"
)


def load_graph():
    return (
        read_jsonl(DATA / "kg/nodes.jsonl"),
        read_jsonl(DATA / "kg/edges.jsonl"),
        read_jsonl(DATA / "corpus/passages.jsonl"),
        read_jsonl(DATA / "corpus/citations.jsonl"),
    )


def _edge_id(row: dict) -> str:
    return str(row.get("edge_id") or "")


def _by(rows: list[dict], key) -> dict:
    return {key(row): row for row in rows}


def load_initial_repair_graph():
    """Return the exact pre-follow-up graph using committed before-images."""

    nodes, edges, passages, citations = (copy.deepcopy(rows) for rows in load_graph())
    followup = read_jsonl(FOLLOWUP_QUARANTINE)
    configs = {
        "kg_node_before": (nodes, node_id),
        "corpus_passage_before": (
            passages,
            lambda row: str(row.get("passage_id") or ""),
        ),
    }
    for entry in followup:
        config = configs.get(str(entry.get("record_type") or ""))
        if config is None:
            continue
        rows, key = config
        record = copy.deepcopy(entry["record"])
        identifier = key(record)
        matches = [index for index, row in enumerate(rows) if key(row) == identifier]
        assert len(matches) == 1
        rows[matches[0]] = record
    return nodes, edges, passages, citations


def _legacy_fixture_from_quarantine():
    """Reconstruct the first migration's relevant before-image cohort.

    The historical JSONL applier was untracked, so byte identity is not
    asserted. The committed quarantine is authoritative for every replaced or
    removed record it contains; the four deterministic citation rewires and
    two deterministic edge rewires are reversed from the applier contract.
    """

    nodes, edges, passages, citations = (
        copy.deepcopy(rows) for rows in load_initial_repair_graph()
    )
    quarantine = read_jsonl(QUARANTINE)

    node_before = {
        node_id(row["record"]): copy.deepcopy(row["record"])
        for row in quarantine
        if row["record_type"] == "kg_node_before"
    }
    for index, node in enumerate(nodes):
        wanted = node_before.get(node_id(node))
        if wanted is not None:
            nodes[index] = wanted

    passages = [
        row for row in passages if row.get("passage_id") != PASSAGE_1113_GRC
    ]
    removed_passage = next(
        copy.deepcopy(row["record"])
        for row in quarantine
        if row["record_type"] == "corpus_passage_removed"
    )
    passages.append(removed_passage)
    old_english = next(
        row for row in passages if row.get("passage_id") == PASSAGE_1113_ENG
    )
    old_english["text_content"] = node_before[ENGLISH_NODE_1113]["description"]

    new_citation_key = (
        "argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        PASSAGE_1113_GRC,
        "source_for",
    )
    citations = [row for row in citations if citation_key(row) != new_citation_key]
    reverse_citations = {
        (
            "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
            PASSAGE_1113_GRC,
            "evidenced_by",
        ): PASSAGE_1114_GRC,
        (
            "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
            PASSAGE_1113_GRC,
            "grounded_in",
        ): PASSAGE_1114_GRC,
        (
            "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6",
            PASSAGE_PROHAIRESIS,
            "grounded_in",
        ): PASSAGE_1114_GRC,
        (GREEK_NODE_1113, PASSAGE_1113_GRC, "snapshot_passage_node"): PASSAGE_1114_GRC,
    }
    for citation in citations:
        old_passage = reverse_citations.get(citation_key(citation))
        if old_passage is not None:
            citation["passage_id"] = old_passage
    citations.extend(
        copy.deepcopy(row["record"])
        for row in quarantine
        if row["record_type"] == "citation_removed"
    )

    for edge in edges:
        if edge.get("edge_id") in {
            "8033b080-9a93-429c-83c1-42994e253005",
            "437087b9-973e-4a8a-829c-688b7ca769dc",
        }:
            edge["target"] = GREEK_NODE_1114
            edge["target_id"] = GREEK_NODE_1114
    edges.extend(
        copy.deepcopy(row["record"])
        for row in quarantine
        if row["record_type"] == "kg_edge_removed"
    )
    return nodes, edges, passages, citations


def test_current_initial_repair_is_exact_and_idempotent() -> None:
    current = load_graph()
    validate_repaired_state(*current)
    result = transform(*current)
    assert result[:4] == current
    assert result[4] == []
    assert result[5] == Counter()

    by_node = _by(result[0], node_id)
    by_passage = _by(result[2], lambda row: row["passage_id"])
    assert by_passage[PASSAGE_1113_GRC]["text_content"] == GREEK_1113
    assert by_passage[PASSAGE_1113_ENG]["text_content"] == ENGLISH_1113
    assert by_node[GREEK_NODE_1113]["description"] == GREEK_1113
    assert by_node[ENGLISH_NODE_1113]["description"] == ENGLISH_1113
    assert "λέγειν" not in GREEK_1113
    assert "say yes" not in ENGLISH_1113.lower()
    assert "say no" not in ENGLISH_1113.lower()


def test_historical_quarantine_round_trip_reproduces_repaired_records() -> None:
    current = load_initial_repair_graph()
    repaired = transform(*_legacy_fixture_from_quarantine())
    validate_repaired_state(*repaired[:4])
    assert repaired[5] == Counter(
        {
            "passages_added": 1,
            "corpus_rows_corrected": 2,
            "nodes_corrected": 6,
            "corrupt_corpus_rows_quarantined": 1,
            "citations_removed": 7,
            "citations_repointed": 4,
            "citations_qualified": 1,
            "citations_added": 1,
            "edges_removed": 6,
            "edges_repointed": 2,
        }
    )
    assert Counter(row["record_type"] for row in repaired[4]) == Counter(
        {
            "kg_node_before": 6,
            "corpus_passage_removed": 1,
            "citation_removed": 7,
            "kg_edge_removed": 6,
        }
    )

    assert _by(repaired[0], node_id) == _by(current[0], node_id)
    assert _by(repaired[1], _edge_id) == _by(current[1], _edge_id)
    assert _by(repaired[2], lambda row: row["passage_id"]) == _by(
        current[2], lambda row: row["passage_id"]
    )
    assert _by(repaired[3], citation_key) == _by(current[3], citation_key)


def test_atomic_repair_produces_exact_bijective_loci() -> None:
    nodes, edges, passages, citations, quarantine, counts = transform(*load_graph())
    validate_repaired_state(nodes, edges, passages, citations)
    snapshots = [
        row for row in citations if row.get("citation_type") == "snapshot_passage_node"
    ]
    by_corpus = Counter(row["passage_id"] for row in snapshots)
    assert by_corpus[PASSAGE_1113_GRC] == 1
    assert by_corpus[PASSAGE_1113_ENG] == 1
    assert by_corpus[PASSAGE_1114_GRC] == 1
    assert by_corpus[PASSAGE_1114_ENG] == 1
    by_node = _by(nodes, node_id)
    by_passage = _by(passages, lambda row: row["passage_id"])
    assert CORRUPT_SYNTHESIS_PASSAGE not in by_passage
    for wanted in (SYNTHESIS_NODE, CORRUPT_SYNTHESIS_EN_NODE):
        data = metadata(by_node[wanted])
        assert data["citable_as_primary"] is False
        assert data["attestation_type"] == "editorial_synthesis"
        assert "passage_id" not in data
    assert not counts
    assert not quarantine


def test_atomic_repair_second_transform_is_idempotent() -> None:
    first = transform(*load_graph())
    second = transform(first[0], first[1], first[2], first[3])
    assert second[:4] == first[:4]
    assert second[4] == []
    assert second[5] == Counter()
    assert all(
        metadata(node).get(STAMP) is True
        for node in second[0]
        if node_id(node)
        in {
            GREEK_NODE_1113,
            ENGLISH_NODE_1113,
            GREEK_NODE_1114,
            SYNTHESIS_NODE,
            CORRUPT_SYNTHESIS_EN_NODE,
        }
    )
