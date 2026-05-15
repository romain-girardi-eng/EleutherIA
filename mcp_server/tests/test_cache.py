"""Unit tests for the per-session MCP tool cache."""

from __future__ import annotations

import time

from mcp_server.cache import SessionCache, _hash_args


def test_hash_args_stable_across_key_order() -> None:
    a = _hash_args({"node_id": "x", "limit": 5})
    b = _hash_args({"limit": 5, "node_id": "x"})
    assert a == b


def test_get_returns_none_when_empty() -> None:
    c = SessionCache()
    assert c.get("s1", "search_nodes", {"query": "stoic"}) is None
    stats = c.stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0


def test_put_then_get_hits() -> None:
    c = SessionCache()
    args = {"node_id": "person_chrysippus"}
    payload = {"node_id": "person_chrysippus", "label": "Chrysippus"}
    c.put("s1", "get_node_detail", args, payload)
    got = c.get("s1", "get_node_detail", args)
    assert got == payload
    assert c.stats()["hits"] == 1


def test_separate_sessions_dont_share() -> None:
    c = SessionCache()
    args = {"node_id": "x"}
    c.put("s1", "get_node_detail", args, {"label": "X"})
    assert c.get("s2", "get_node_detail", args) is None
    assert c.get("s1", "get_node_detail", args) == {"label": "X"}


def test_global_bucket_when_session_id_none() -> None:
    c = SessionCache()
    args = {"q": "fate"}
    c.put(None, "search_nodes", args, {"nodes": []})
    assert c.get(None, "search_nodes", args) == {"nodes": []}


def test_ttl_expiry() -> None:
    c = SessionCache(default_ttl_seconds=1)
    c.put("s1", "search_passages", {"q": "fate"}, {"passages": []}, ttl_s=0)
    # ttl_s clamped to >=1s, but expires_at is now+1s; sleep just past it.
    time.sleep(1.1)
    assert c.get("s1", "search_passages", {"q": "fate"}) is None


def test_max_entries_evicts_oldest() -> None:
    c = SessionCache(max_entries=3)
    for i in range(5):
        c.put("s1", "get_node_detail", {"node_id": f"n{i}"}, {"label": f"L{i}"})
    # n0 and n1 should have been evicted.
    assert c.get("s1", "get_node_detail", {"node_id": "n0"}) is None
    assert c.get("s1", "get_node_detail", {"node_id": "n1"}) is None
    assert c.get("s1", "get_node_detail", {"node_id": "n4"}) == {"label": "L4"}
    assert c.stats()["evictions"] >= 2


def test_evict_session_returns_count() -> None:
    c = SessionCache()
    c.put("s1", "search_nodes", {"q": "a"}, {"r": 1})
    c.put("s1", "search_nodes", {"q": "b"}, {"r": 2})
    assert c.evict_session("s1") == 2
    assert c.get("s1", "search_nodes", {"q": "a"}) is None


def test_put_rejects_non_dict_results() -> None:
    c = SessionCache()
    c.put("s1", "search_nodes", {"q": "x"}, ["not", "a", "dict"])  # type: ignore[arg-type]
    assert c.get("s1", "search_nodes", {"q": "x"}) is None


def test_lru_touch_on_get() -> None:
    c = SessionCache(max_entries=2)
    c.put("s1", "t", {"k": 1}, {"v": 1})
    c.put("s1", "t", {"k": 2}, {"v": 2})
    # Touch the older entry so it moves to the back.
    assert c.get("s1", "t", {"k": 1}) == {"v": 1}
    # Inserting a 3rd entry should evict {"k": 2}, not {"k": 1}.
    c.put("s1", "t", {"k": 3}, {"v": 3})
    assert c.get("s1", "t", {"k": 1}) == {"v": 1}
    assert c.get("s1", "t", {"k": 2}) is None
