from scripts.check_corpus_invariants import find_violations


def test_no_violations_when_all_resolve():
    passages = [{"passage_id": "p1"}]
    citations = [{"passage_id": "p1", "kg_node_id": "n1"}]
    node_ids = {"n1"}
    v = find_violations(passages, citations, node_ids)
    assert v["dangling_passage"] == []
    assert v["dangling_node"] == []
    assert v["duplicate_passage_id"] == []
    assert v["duplicate_citation_triplet"] == []


def test_detects_dangling_passage_and_node():
    passages = [{"passage_id": "p1"}]
    citations = [
        {"passage_id": "p1", "kg_node_id": "n1"},
        {"passage_id": "pX", "kg_node_id": "n1"},
        {"passage_id": "p1", "kg_node_id": "nX"},
    ]
    node_ids = {"n1"}
    v = find_violations(passages, citations, node_ids)
    assert v["dangling_passage"] == [{"passage_id": "pX", "kg_node_id": "n1"}]
    assert v["dangling_node"] == [{"passage_id": "p1", "kg_node_id": "nX"}]


def test_detects_duplicate_passage_ids_and_citation_triplets():
    passages = [{"passage_id": "p1"}, {"passage_id": "p1", "text": "copy"}]
    citation = {
        "passage_id": "p1",
        "kg_node_id": "n1",
        "citation_type": "snapshot_passage_node",
    }
    citations = [citation, dict(citation)]
    v = find_violations(passages, citations, {"n1"})
    assert v["duplicate_passage_id"] == [passages[1]]
    assert v["duplicate_citation_triplet"] == [citations[1]]
