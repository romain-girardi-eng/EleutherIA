from scripts.check_corpus_invariants import find_violations


def test_no_violations_when_all_resolve():
    passages = [{"passage_id": "p1"}]
    citations = [{"passage_id": "p1", "kg_node_id": "n1"}]
    node_ids = {"n1"}
    v = find_violations(passages, citations, node_ids)
    assert v["dangling_passage"] == []
    assert v["dangling_node"] == []


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
