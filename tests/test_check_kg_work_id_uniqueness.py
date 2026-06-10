import json

from scripts.check_kg_work_id_uniqueness import (
    collect_work_groups,
    find_collisions,
    load_allowlist,
    split_known_new,
    write_allowlist,
)


def _passage(nid: str, wcid: str, author: str = "Plato", title: str = "T") -> dict:
    return {
        "id": nid,
        "type": "passage",
        "metadata": json.dumps(
            {"work_canonical_id": wcid, "author": author, "work_title": title}
        ),
    }


def _edge(src: str, tgt: str, relation: str = "part_of") -> dict:
    return {"source": src, "target": tgt, "relation": relation}


WORK = {"id": "work_republic_plato", "type": "work", "metadata": "{}"}


def test_single_work_per_node_is_not_a_collision():
    nodes = [WORK, _passage("p1", "tlg0059.tlg030"), _passage("p2", "tlg0059.tlg030")]
    edges = [_edge("p1", "work_republic_plato"), _edge("p2", "work_republic_plato")]
    assert find_collisions(collect_work_groups(nodes, edges)) == []


def test_detects_one_kg_work_id_many_works_collision():
    nodes = [
        WORK,
        _passage("p1", "tlg0059.tlg030", title="Republic"),
        _passage("p2", "tlg0059.tlg002", title="Apology"),
        _passage("p3", "tlg0059.tlg002", title="Apology"),
    ]
    edges = [_edge(p, "work_republic_plato") for p in ("p1", "p2", "p3")]
    collisions = find_collisions(collect_work_groups(nodes, edges))
    assert len(collisions) == 1
    c = collisions[0]
    assert c["kg_work_id"] == "work_republic_plato"
    members = {m["work_canonical_id"]: m for m in c["members"]}
    assert set(members) == {"tlg0059.tlg030", "tlg0059.tlg002"}
    assert members["tlg0059.tlg002"]["passages"] == 2
    assert members["tlg0059.tlg002"]["title"] == "Apology"
    assert members["tlg0059.tlg002"]["author"] == "Plato"


def test_ignores_non_part_of_edges_and_missing_metadata():
    nodes = [
        WORK,
        _passage("p1", "tlg0059.tlg030"),
        _passage("p2", "tlg0059.tlg002"),
        {"id": "p3", "type": "passage", "metadata": "{}"},  # no work_canonical_id
    ]
    edges = [
        _edge("p1", "work_republic_plato"),
        _edge("p2", "work_republic_plato", relation="discusses"),  # not part_of
        _edge("p3", "work_republic_plato"),
        _edge("ghost", "work_republic_plato"),  # dangling source
    ]
    assert find_collisions(collect_work_groups(nodes, edges)) == []


def test_split_known_new_subset_semantics():
    collisions = [
        {
            "kg_work_id": "work_a",
            "members": [
                {"work_canonical_id": "w1", "passages": 1, "author": None, "title": None},
                {"work_canonical_id": "w2", "passages": 1, "author": None, "title": None},
            ],
        },
        {
            "kg_work_id": "work_b",
            "members": [
                {"work_canonical_id": "w3", "passages": 1, "author": None, "title": None},
                {"work_canonical_id": "w4", "passages": 1, "author": None, "title": None},
            ],
        },
    ]
    allowlist = {"work_a": ["w1", "w2"], "work_b": ["w3"]}
    known, new = split_known_new(collisions, allowlist)
    # work_a fully covered -> known; work_b gained member w4 -> NEW collision
    assert [c["kg_work_id"] for c in known] == ["work_a"]
    assert [c["kg_work_id"] for c in new] == ["work_b"]


def test_unlisted_work_node_is_new():
    collisions = [
        {
            "kg_work_id": "work_c",
            "members": [
                {"work_canonical_id": "w1", "passages": 1, "author": None, "title": None},
                {"work_canonical_id": "w2", "passages": 1, "author": None, "title": None},
            ],
        }
    ]
    known, new = split_known_new(collisions, {})
    assert known == []
    assert [c["kg_work_id"] for c in new] == ["work_c"]


def test_allowlist_round_trip(tmp_path):
    collisions = [
        {
            "kg_work_id": "work_a",
            "members": [
                {"work_canonical_id": "w2", "passages": 1, "author": None, "title": None},
                {"work_canonical_id": "w1", "passages": 2, "author": None, "title": None},
            ],
        }
    ]
    path = tmp_path / "allow.json"
    write_allowlist(collisions, path)
    assert load_allowlist(path) == {"work_a": ["w1", "w2"]}
    known, new = split_known_new(collisions, load_allowlist(path))
    assert len(known) == 1 and new == []


def test_missing_allowlist_file_is_empty(tmp_path):
    assert load_allowlist(tmp_path / "nope.json") == {}
