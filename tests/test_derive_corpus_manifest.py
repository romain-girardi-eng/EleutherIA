from scripts.derive_corpus_manifest import derive_manifest


def test_derive_includes_work_nodes_and_passage_referenced_works():
    nodes = [
        {"id": "work_de_int", "type": "work", "label": "De Interpretatione",
         "period": "Classical", "metadata": {"cts_urn": "urn:cts:greekLit:tlg0086.tlg028"}},
        {"id": "person_aristotle", "type": "person", "label": "Aristotle"},
        {"id": "pass_1", "type": "passage", "label": "DI 9",
         "metadata": {"work_canonical_id": "work_de_int"}},
        {"id": "pass_2", "type": "passage", "label": "EN III.5",
         "metadata": {"work_canonical_id": "work_en"}},
    ]
    edges = [
        {"source": "work_de_int", "target": "person_aristotle", "relation": "authored_by"},
    ]
    rows = derive_manifest(nodes, edges)
    by_id = {r["canonical_id"]: r for r in rows}
    assert set(by_id) == {"work_de_int", "work_en"}
    assert by_id["work_de_int"]["author"] == "Aristotle"
    assert by_id["work_de_int"]["cts_urn"] == "urn:cts:greekLit:tlg0086.tlg028"
    assert by_id["work_de_int"]["source"] == "scaife:urn:cts:greekLit:tlg0086.tlg028"
    assert by_id["work_de_int"]["status"] == "pending"
    assert by_id["work_en"]["status"] == "needs_source"
    assert by_id["work_en"]["source"] == ""


def test_derive_is_sorted_by_canonical_id():
    nodes = [
        {"id": "work_b", "type": "work", "label": "B"},
        {"id": "work_a", "type": "work", "label": "A"},
    ]
    rows = derive_manifest(nodes, [])
    assert [r["canonical_id"] for r in rows] == ["work_a", "work_b"]
