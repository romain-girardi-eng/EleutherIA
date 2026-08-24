from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.apply_2026_08_24_alexander_agent_causation_recollation import (
    ARGUMENT_ID,
    DF12_BRUNS,
    DF12_EN_NODE,
    DF12_NODE,
    DF12_PASSAGE,
    DF12_TEXT_HASH,
    DF20_BRUNS,
    DF20_EN_NODE,
    DF20_NODE,
    DF20_PASSAGE,
    DF20_TEXT_HASH,
    EDGE_SHARPLES_DF12,
    EDGE_SHARPLES_DF20,
    EVIDENCE_ID,
    ISSUE_ID,
    REPORT_RELATIVE,
    SHARPLES_POSITION,
    metadata,
    node_id,
    read_jsonl,
    sha256_nfc,
    transform_graph_corpus,
    transform_registry,
    validate_argument_node,
    validate_graph_corpus,
    validate_registry,
)
from scripts.check_snapshot_passage_integrity import audit_integrity

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REGISTRY = DATA / "goals/sota/registry"


def load_graph_corpus():
    return (
        read_jsonl(DATA / "kg/nodes.jsonl"),
        read_jsonl(DATA / "kg/edges.jsonl"),
        read_jsonl(DATA / "corpus/passages.jsonl"),
        read_jsonl(DATA / "corpus/citations.jsonl"),
    )


def load_registry():
    return (
        read_jsonl(REGISTRY / "sources/seed_priority_20260824.jsonl"),
        read_jsonl(REGISTRY / "evidence/seed_priority_20260824.jsonl"),
        read_jsonl(REGISTRY / "issues/seed_known_20260824.jsonl"),
        read_jsonl(
            REGISTRY / "verifications/alexander_agent_causation_20260824.jsonl"
        ),
    )


def test_alexander_claims_are_partitioned_and_page_grounded() -> None:
    nodes, edges, passages, citations, quarantine, _ = transform_graph_corpus(
        *load_graph_corpus()
    )
    validate_graph_corpus(nodes, edges, passages, citations)
    by_node = {node_id(row): row for row in nodes}
    argument = by_node[ARGUMENT_ID]
    data = metadata(argument)

    assert len(data["premises"]) == 6
    assert all(row["claim_role"] == "direct_text" for row in data["premises"])
    assert all(row["primary_sources"] for row in data["premises"])
    assert all(
        source.get("bruns_page_lines")
        for row in data["premises"]
        for source in row["primary_sources"]
    )
    assert data["reconstructed_inferences"][0]["claim_role"] == (
        "reconstructed_inference"
    )
    assert data["reconstructed_inferences"][0]["secondary_sources"]
    assert all(row["claim_role"] == "modern_taxonomy" for row in data["modern_taxonomy"])
    assert all(row["assertor_id"] == "scholar_sharples_robert" for row in data["modern_taxonomy"])
    assert all(row["active"] is False and row["reason"] for row in data["withdrawn_claims"])
    assert data["argument_form"] == "source_critical_claim_cluster"
    assert "modus tollens" not in argument["description"].lower()
    if quarantine:
        assert len(quarantine) == 13


def test_de_fato_12_20_text_loci_edges_and_snapshots_are_exact() -> None:
    nodes, edges, passages, citations, _, _ = transform_graph_corpus(
        *load_graph_corpus()
    )
    by_node = {node_id(row): row for row in nodes}
    by_passage = {row["passage_id"]: row for row in passages}

    assert metadata(by_node[DF12_NODE])["bruns_page_lines"] == DF12_BRUNS
    assert metadata(by_node[DF20_NODE])["bruns_page_lines"] == DF20_BRUNS
    assert sha256_nfc(by_node[DF12_NODE]["description"]) == DF12_TEXT_HASH
    assert sha256_nfc(by_node[DF20_NODE]["description"]) == DF20_TEXT_HASH
    assert by_node[DF12_NODE]["description"] == by_passage[DF12_PASSAGE]["text_content"]
    assert by_node[DF20_NODE]["description"] == by_passage[DF20_PASSAGE]["text_content"]
    assert "ἀναιρεῖται 40 καὶ" not in by_node[DF12_NODE]["description"]

    by_edge = {edge["edge_id"]: edge for edge in edges}
    assert by_edge[EDGE_SHARPLES_DF12]["metadata"]["alex_de_fato_bruns_pages"] == DF12_BRUNS
    assert by_edge[EDGE_SHARPLES_DF20]["metadata"]["alex_de_fato_bruns_pages"] == DF20_BRUNS
    assert any(
        edge["source"] == SHARPLES_POSITION
        and edge["relation"] == "interprets"
        and edge["target"] == ARGUMENT_ID
        for edge in edges
    )
    assert not any(
        row.get("citation_type") == "snapshot_passage_node"
        and row.get("kg_node_id") in {DF12_EN_NODE, DF20_EN_NODE}
        for row in citations
    )
    violations = audit_integrity(nodes, passages, citations)
    assert not [
        row
        for row in violations
        if row.get("node_id") in {DF12_NODE, DF20_NODE, DF12_EN_NODE, DF20_EN_NODE}
    ]


def test_alexander_recollation_does_not_touch_other_nodes_passages_or_citations() -> None:
    old_nodes, old_edges, old_passages, old_citations = load_graph_corpus()
    nodes, edges, passages, citations, _, _ = transform_graph_corpus(
        old_nodes, old_edges, old_passages, old_citations
    )
    touched_nodes = {ARGUMENT_ID, DF12_NODE, DF20_NODE}
    old_by_node = {node_id(row): row for row in old_nodes}
    new_by_node = {node_id(row): row for row in nodes}
    for wanted in old_by_node.keys() - touched_nodes:
        assert new_by_node[wanted] == old_by_node[wanted]

    old_by_passage = {row["passage_id"]: row for row in old_passages}
    new_by_passage = {row["passage_id"]: row for row in passages}
    for wanted in old_by_passage.keys() - {DF12_PASSAGE}:
        assert new_by_passage[wanted] == old_by_passage[wanted]
    removed = [row for row in old_citations if row not in citations]
    assert {
        (row["kg_node_id"], row["passage_id"], row["citation_type"])
        for row in removed
    } <= {
        (DF12_EN_NODE, DF12_PASSAGE, "snapshot_passage_node"),
        (DF20_EN_NODE, DF20_PASSAGE, "snapshot_passage_node"),
    }
    assert len(edges) in {len(old_edges), len(old_edges) + 1}


def test_alexander_recollation_is_idempotent() -> None:
    first = transform_graph_corpus(*load_graph_corpus())
    second = transform_graph_corpus(first[0], first[1], first[2], first[3])
    assert second[:4] == first[:4]
    assert second[4] == []
    assert second[5] == Counter()

    first_registry = transform_registry(*load_registry())
    mapped = first_registry[0]
    second_registry = transform_registry(
        mapped["sources"],
        mapped["evidence"],
        mapped["issues"],
        mapped["verifications"],
    )
    assert second_registry[0] == mapped
    assert second_registry[1] == []
    assert second_registry[2] == Counter()


def test_validator_rejects_unsourced_active_reconstruction() -> None:
    nodes, _, _, _, _, _ = transform_graph_corpus(*load_graph_corpus())
    argument = copy.deepcopy(next(row for row in nodes if node_id(row) == ARGUMENT_ID))
    data = metadata(argument)
    data["reconstructed_inferences"].append(
        {
            "id": "BAD",
            "claim_role": "reconstructed_inference",
            "status": "asserted",
            "text": "Unsupported inference",
            "basis_claim_ids": ["D20.1"],
            "secondary_sources": [],
        }
    )
    argument["metadata"] = data
    with pytest.raises(RuntimeError, match="lacks secondary support"):
        validate_argument_node(argument)


def test_validator_rejects_pseudo_greek_as_active_ancient_claim() -> None:
    nodes, _, _, _, _, _ = transform_graph_corpus(*load_graph_corpus())
    argument = copy.deepcopy(next(row for row in nodes if node_id(row) == ARGUMENT_ID))
    data = metadata(argument)
    data["conclusion"]["text"] += " αἴτιον οὐκ ἀναγκαστικόν"
    argument["metadata"] = data
    with pytest.raises(RuntimeError, match="unsupported claim remains active"):
        validate_argument_node(argument)


def test_alexander_registry_and_audit_report_are_closed_at_minimal_scope() -> None:
    mapped, _, _ = transform_registry(*load_registry())
    validate_registry(mapped)
    evidence = next(
        row for row in mapped["evidence"] if row.get("evidence_id") == EVIDENCE_ID
    )
    issue = next(row for row in mapped["issues"] if row.get("issue_id") == ISSUE_ID)
    assert evidence["claim_status"] == "verified"
    assert evidence["quotation"]["corpus_passage_ids"] == [
        DF12_PASSAGE,
        DF20_PASSAGE,
    ]
    assert issue["status"] == "adjudicated"

    report = json.loads((ROOT / REPORT_RELATIVE).read_text(encoding="utf-8"))
    assert report["verdict"] == "pass"
    assert report["loci"]["De fato 12"]["bruns_page_lines"] == DF12_BRUNS
    assert report["loci"]["De fato 20"]["bruns_page_lines"] == DF20_BRUNS
    assert report["textual_correction"]["action"] == (
        "removed_spurious_marginal_line_number_40"
    )
