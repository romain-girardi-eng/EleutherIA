import json

from scripts.check_kg_corpus_locus_parity import find_violations


def passage_node(node_id="passage_a", passage_id="p1", ref="1.1", urn="urn:1.1"):
    return {
        "id": node_id,
        "type": "passage",
        "metadata": json.dumps(
            {
                "db_passage_id": passage_id,
                "canonical_ref": ref,
                "cts_urn": urn,
            }
        ),
    }


def test_exact_locus_and_citation_parity():
    nodes = [passage_node()]
    passages = [{"passage_id": "p1", "canonical_ref": "1.1", "cts_urn": "urn:1.1"}]
    citations = [{"passage_id": "p1", "kg_node_id": "passage_a"}]
    shared, violations = find_violations(nodes, passages, citations)
    assert shared == 1
    assert violations == []


def test_reports_missing_citation_and_locus_mismatches():
    nodes = [passage_node(ref="KG 1", urn="urn:kg")]
    passages = [{"passage_id": "p1", "canonical_ref": "DB 1", "cts_urn": "urn:db"}]
    shared, violations = find_violations(nodes, passages, [])
    assert shared == 1
    assert {row["field"] for row in violations} == {
        "citation",
        "canonical_ref",
        "cts_urn",
    }


def test_prefix_scope_and_missing_twin():
    nodes = [
        passage_node(node_id="target_1", passage_id="missing"),
        passage_node(node_id="other_1"),
    ]
    shared, violations = find_violations(nodes, [], [], ("target_",))
    assert shared == 0
    assert len(violations) == 1
    assert violations[0]["reason"] == "missing_corpus_twin"
