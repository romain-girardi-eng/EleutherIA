"""Shared I/O and invariant helpers for the 2026-09-24 verification batches.

Every ``apply_2026_09_24_*`` script loads the canonical JSONL through this
module, mutates records in memory, then calls :func:`commit` which re-checks
the graph invariants and writes only the lines that actually changed. The
decisions themselves live in the matching ``data_2026_09_24_*`` module; this
file only knows *how* to apply them.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FILES = {
    "nodes": (DATA / "kg" / "nodes.jsonl", "id"),
    "edges": (DATA / "kg" / "edges.jsonl", "edge_id"),
    "passages": (DATA / "corpus" / "passages.jsonl", "passage_id"),
    "citations": (DATA / "corpus" / "citations.jsonl", None),
}

# Metadata fields that hold a KG node id and must keep resolving.
POINTER_FIELDS = (
    "scholar_id",
    "author_id",
    "scholarly_work_id",
    "publication",
    "original_node_id",
    "source_passage_id",
    "work_node_id",
)


def dumps(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def sha(record: Any) -> str:
    return hashlib.sha256(
        json.dumps(record, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def meta(node: dict[str, Any]) -> dict[str, Any]:
    raw = node.get("metadata") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return dict(raw)


def set_meta(node: dict[str, Any], data: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        node["metadata"] = data


class Store:
    """The four canonical JSONL files, with their original lines kept."""

    def __init__(self) -> None:
        self.lines: dict[str, list[str]] = {}
        self.rows: dict[str, list[dict[str, Any]]] = {}
        for name, (path, _key) in FILES.items():
            lines = [line for line in path.read_text().splitlines() if line.strip()]
            self.lines[name] = lines
            self.rows[name] = [json.loads(line) for line in lines]
        self.before = {name: [copy.deepcopy(r) for r in rows] for name, rows in self.rows.items()}
        self.quarantine: list[dict[str, Any]] = []

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        return {n["id"]: n for n in self.rows["nodes"]}

    @property
    def edges(self) -> list[dict[str, Any]]:
        return self.rows["edges"]

    def remove_node(self, node_id: str, reason: str) -> None:
        keep = []
        for node in self.rows["nodes"]:
            if node["id"] == node_id:
                self.quarantine.append({"record_type": "kg_node", "reason": reason, "record": node})
            else:
                keep.append(node)
        self.rows["nodes"] = keep

    def remove_edges(self, predicate, reason: str) -> int:
        keep, removed = [], 0
        for edge in self.rows["edges"]:
            if predicate(edge):
                self.quarantine.append({"record_type": "kg_edge", "reason": reason, "record": edge})
                removed += 1
            else:
                keep.append(edge)
        self.rows["edges"] = keep
        return removed

    def remove_citations(self, predicate, reason: str) -> int:
        keep, removed = [], 0
        for cit in self.rows["citations"]:
            if predicate(cit):
                self.quarantine.append({"record_type": "corpus_citation", "reason": reason, "record": cit})
                removed += 1
            else:
                keep.append(cit)
        self.rows["citations"] = keep
        return removed

    def remove_passages(self, predicate, reason: str) -> int:
        keep, removed = [], 0
        for p in self.rows["passages"]:
            if predicate(p):
                self.quarantine.append({"record_type": "corpus_passage", "reason": reason, "record": p})
                removed += 1
            else:
                keep.append(p)
        self.rows["passages"] = keep
        return removed

    # ------------------------------------------------------------------ checks
    def pointer_debt(self, rows: dict[str, list[dict[str, Any]]]) -> Counter:
        ids = {n["id"] for n in rows["nodes"]}
        debt: Counter = Counter()
        for node in rows["nodes"]:
            data = meta(node)
            for field in POINTER_FIELDS:
                value = data.get(field)
                values = value if isinstance(value, list) else [value]
                for v in values:
                    if isinstance(v, str) and v and v in self._all_ids_before and v not in ids:
                        debt[(node["id"], field, v)] += 1
        return debt

    def assert_invariants(self) -> None:
        nodes = self.rows["nodes"]
        ids = [n["id"] for n in nodes]
        dup = [k for k, c in Counter(ids).items() if c > 1]
        assert not dup, f"duplicate node ids: {dup[:5]}"
        idset = set(ids)
        triples: Counter = Counter()
        for e in self.rows["edges"]:
            assert e.get("source") == e.get("source_id"), f"source != source_id: {e['edge_id']}"
            assert e.get("target") == e.get("target_id"), f"target != target_id: {e['edge_id']}"
            assert e["source"] != e["target"], f"self-loop: {e['edge_id']}"
            assert e["source"] in idset and e["target"] in idset, f"dangling edge: {e['edge_id']}"
            triples[(e["source"], e["relation"], e["target"])] += 1
        dup_t = [t for t, c in triples.items() if c > 1]
        before_dup = Counter((e["source"], e["relation"], e["target"]) for e in self.before["edges"])
        new_dup = [t for t in dup_t if before_dup.get(t, 0) < 2]
        assert not new_dup, f"new duplicate triples: {new_dup[:5]}"
        eids = Counter(e["edge_id"] for e in self.rows["edges"])
        assert not [k for k, c in eids.items() if c > 1], "duplicate edge ids"
        for c in self.rows["citations"]:
            assert c["kg_node_id"] in idset, f"dangling citation: {c}"
        pids = {p["passage_id"] for p in self.rows["passages"]}
        for c in self.rows["citations"]:
            assert c["passage_id"] in pids, f"citation to missing passage: {c}"
        self._all_ids_before = {n["id"] for n in self.before["nodes"]}
        new_debt = set(self.pointer_debt(self.rows))
        assert not new_debt, f"new dangling metadata pointers: {sorted(new_debt)[:5]}"

    # ------------------------------------------------------------------ write
    def changed(self) -> dict[str, dict[str, int]]:
        out = {}
        for name, (_path, key) in FILES.items():
            if key is None:
                old = Counter(dumps(r) for r in self.before[name])
                new = Counter(dumps(r) for r in self.rows[name])
                out[name] = {"added": sum((new - old).values()), "removed": sum((old - new).values()), "modified": 0}
                continue
            old = {r[key]: r for r in self.before[name]}
            new = {r[key]: r for r in self.rows[name]}
            out[name] = {
                "added": len(set(new) - set(old)),
                "removed": len(set(old) - set(new)),
                "modified": sum(1 for k in set(old) & set(new) if old[k] != new[k]),
            }
        return out

    def commit(self, slug: str, apply: bool) -> dict[str, dict[str, int]]:
        self.assert_invariants()
        summary = self.changed()
        if not apply:
            return summary
        for name, (path, key) in FILES.items():
            s = summary[name]
            if not (s["added"] or s["removed"] or s["modified"]):
                continue
            backup = path.with_name(path.name + f".bak-{slug}")
            if not backup.exists():
                shutil.copy2(path, backup)
            original = {}
            for line, row in zip(self.lines[name], self.before[name]):
                ident = row[key] if key else dumps(row)
                original[ident] = (row, line)
            out = []
            for row in self.rows[name]:
                ident = row[key] if key else dumps(row)
                if ident in original and original[ident][0] == row:
                    out.append(original[ident][1])
                else:
                    out.append(dumps(row))
            path.write_text("\n".join(out) + "\n")
        if self.quarantine:
            qpath = DATA / "audit" / f"2026-09-24_{slug}_quarantine.jsonl"
            with qpath.open("w") as fh:
                for rec in self.quarantine:
                    fh.write(dumps({**rec, "record_sha256": sha(rec["record"])}) + "\n")
        return summary


def write_decisions(slug: str, decisions: list[dict[str, Any]]) -> Path:
    path = DATA / "audit" / f"2026-09-24_{slug}_decisions.jsonl"
    with path.open("w") as fh:
        for d in decisions:
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    return path
