from scripts.apply_2026_08_24_bobzien_monograph_year_repair import (
    NODE_ID,
    STAMP,
    node_id,
    read_nodes,
    transform,
)


def test_bobzien_first_publication_and_paperback_are_distinct() -> None:
    nodes, _ = transform(read_nodes())
    node = next(node for node in nodes if node_id(node) == NODE_ID)
    assert node["metadata"]["year"] == 1998
    assert node["metadata"]["edition_used_year"] == 2001
    assert node["metadata"][STAMP] is True


def test_bobzien_year_repair_is_idempotent() -> None:
    first, _ = transform(read_nodes())
    second, changed = transform(first)
    assert second == first
    assert changed is False
