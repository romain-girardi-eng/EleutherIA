from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.apply_2026_08_24_bobzien_bibliography_repair import (
    ARG_2013_RECEPTION,
    ARG_2013_VICE_VERSA,
    ARG_2014_ALTERNATIVES,
    ARG_2014_CHARACTER,
    ARG_2014_DISPOSITIONS,
    ARG_2014_PROHAIRESIS,
    DESTREE_VOLUME,
    EXISTING_DESTREE_ARGUMENT,
    NEW_NODE_IDS,
    POLANSKY_CHAPTER,
    PUB_2013,
    PUB_2014_DESTREE,
    TWO_SIDEDNESS,
    WRONG_EDGE_IDS,
    metadata,
    node_id,
    read_jsonl,
    transform,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_graph():
    return (
        read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        read_jsonl(ROOT / "data/kg/edges.jsonl"),
    )


def test_bobzien_works_and_arguments_are_separated() -> None:
    nodes, edges, quarantine, counts = transform(*load_graph())
    validate(nodes, edges)
    by_node = {node_id(node): node for node in nodes}

    assert by_node.keys() >= NEW_NODE_IDS
    assert metadata(by_node[PUB_2013])["doi"] == (
        "10.1093/acprof:oso/9780199679430.003.0004"
    )
    assert metadata(by_node[PUB_2014_DESTREE])["original_doi"] is None
    assert metadata(by_node[PUB_2014_DESTREE])["pages"] == "59-73"
    assert metadata(by_node[POLANSKY_CHAPTER])["doi"] == (
        "10.1017/CCO9781139022484.005"
    )
    assert metadata(by_node[DESTREE_VOLUME])["contribution_count"] == 22
    assert metadata(by_node[DESTREE_VOLUME])["page_count"] == 372

    for wanted in (EXISTING_DESTREE_ARGUMENT, TWO_SIDEDNESS):
        text = str(by_node[wanted]).lower()
        assert "say yes" not in text
        assert "say no" not in text
        assert "dire oui" not in text
        assert "dire non" not in text

    triples = {(edge["source"], edge["relation"], edge["target"]) for edge in edges}
    expected_work = {
        EXISTING_DESTREE_ARGUMENT: PUB_2014_DESTREE,
        ARG_2013_VICE_VERSA: PUB_2013,
        ARG_2013_RECEPTION: PUB_2013,
        ARG_2014_CHARACTER: POLANSKY_CHAPTER,
        ARG_2014_ALTERNATIVES: POLANSKY_CHAPTER,
        ARG_2014_PROHAIRESIS: POLANSKY_CHAPTER,
        ARG_2014_DISPOSITIONS: POLANSKY_CHAPTER,
    }
    for argument, publication in expected_work.items():
        assert metadata(by_node[argument])["scholarly_work_id"] == publication
        assert (argument, "advanced_in", publication) in triples
    assert not ({edge["edge_id"] for edge in edges} & WRONG_EDGE_IDS)
    if counts:
        assert quarantine


def test_bobzien_repair_is_idempotent() -> None:
    first = transform(*load_graph())
    second = transform(first[0], first[1])
    assert second[:2] == first[:2]
    assert second[2] == []
    assert second[3] == Counter()
