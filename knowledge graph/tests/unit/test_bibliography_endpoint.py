"""Tests for the /bibliography aggregation helper."""

from eleutheria_kg.api.routes import collect_modern_scholarship


def test_collects_from_node_field_and_metadata() -> None:
    nodes = [
        {"modern_scholarship": ["Bobzien, S. (1998). Determinism and Freedom."]},
        {"metadata": {"modern_scholarship": ["Frede, M. (2011). A Free Will."]}},
        {"metadata": {}},
        {},
    ]
    refs = collect_modern_scholarship(nodes)
    assert refs == [
        "Bobzien, S. (1998). Determinism and Freedom.",
        "Frede, M. (2011). A Free Will.",
    ]


def test_parses_json_encoded_metadata_strings() -> None:
    nodes = [
        {"metadata": {"modern_scholarship": '["Dihle, A. (1982). The Theory of Will."]'}},
        {"metadata": {"modern_scholarship": "not json, plain citation"}},
    ]
    refs = collect_modern_scholarship(nodes)
    assert "Dihle, A. (1982). The Theory of Will." in refs
    assert "not json, plain citation" in refs


def test_deduplicates_and_handles_dict_entries() -> None:
    nodes = [
        {"modern_scholarship": ["Kane, R. (1996). The Significance of Free Will."]},
        {"modern_scholarship": [{"citation": "Kane, R. (1996). The Significance of Free Will."}]},
        {"modern_scholarship": [{"title": "Untitled entry"}, "", "   "]},
    ]
    refs = collect_modern_scholarship(nodes)
    assert refs.count("Kane, R. (1996). The Significance of Free Will.") == 1
    assert "Untitled entry" in refs


def test_sorted_by_author_case_insensitive() -> None:
    nodes = [
        {"modern_scholarship": ["zeller, E. (1880). Stoics."]},
        {"modern_scholarship": ["Amand, D. (1945). Fatalisme."]},
    ]
    refs = collect_modern_scholarship(nodes)
    assert refs == [
        "Amand, D. (1945). Fatalisme.",
        "zeller, E. (1880). Stoics.",
    ]
