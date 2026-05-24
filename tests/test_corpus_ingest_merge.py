from scripts.corpus_ingest_merge import passages_to_insert


def test_only_new_urns_are_inserted():
    existing = [{"cts_urn": "urn:cts:x:w:1", "text_content": "a"}]
    fetched = [
        {"cts_urn": "urn:cts:x:w:1", "text_content": "a"},   # already present
        {"cts_urn": "urn:cts:x:w:2", "text_content": "b"},   # new
        {"cts_urn": "urn:cts:x:w:3", "text_content": "c"},   # new
    ]
    new = passages_to_insert(existing, fetched, work_canonical_id="w", start_seq=10)
    assert [p["cts_urn"] for p in new] == ["urn:cts:x:w:2", "urn:cts:x:w:3"]
    assert [p["sequence_number"] for p in new] == [10, 11]
    assert all(p["work_canonical_id"] == "w" for p in new)


def test_empty_text_is_skipped_never_fabricated():
    existing = []
    fetched = [{"cts_urn": "urn:cts:x:w:1", "text_content": "   "},
               {"cts_urn": "urn:cts:x:w:2", "text_content": "real"}]
    new = passages_to_insert(existing, fetched, work_canonical_id="w", start_seq=0)
    assert [p["cts_urn"] for p in new] == ["urn:cts:x:w:2"]
