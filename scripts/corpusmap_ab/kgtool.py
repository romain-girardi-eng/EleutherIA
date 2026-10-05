"""Offline tool server + CLI for the agentic CorpusMap A/B.

Mirrors the production agent tools (search_nodes, get_node_detail,
get_neighbors, read_passages, search_passages) over the JSONL snapshot, plus
the CorpusMap tools (search_entity_pages, read_entity_page) that only arm B
may call. Every call is logged with the size of what it returned, so the
token cost of each trajectory is measured independently of the agent runtime.

    # once
    .venv/bin/python scripts/corpusmap_ab/kgtool.py serve --log data/eval/corpusmap_ab/calls.jsonl &
    # per call (the run id fixes the arm: *-A or *-B)
    .venv/bin/python scripts/corpusmap_ab/kgtool.py RUN_ID search_nodes query="Chrysippus fate" limit=10
"""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PORT = 8765
TEXT_CAP = 800  # same cap as the production search_passages tool
BASE_TOOLS = {
    "search_nodes",
    "get_node_detail",
    "get_neighbors",
    "read_passages",
    "search_passages",
    "read_passage",
}
MAP_TOOLS = {"search_entity_pages", "read_entity_page"}


def _clip(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


class Tools:
    def __init__(self) -> None:
        sys.path.insert(0, str(REPO / "tests" / "eval"))
        from eleutheria_graphrag.corpusmap import build_corpus_map
        from eval_lib.snapshot_runner import SnapshotIndex

        self.ix = SnapshotIndex()
        self.ix._ensure_adjacency("asserted_bidirectional")
        self.cmap = build_corpus_map(
            REPO / "data/kg",
            REPO / "data/corpus",
            allowed_passages=set(self.ix.passages),
        )
        self.edges_by_node: dict[str, list[dict]] = {}
        for row in self.ix._edge_rows:
            s, t = (
                row.get("source") or row.get("source_id"),
                row.get("target") or row.get("target_id"),
            )
            self.edges_by_node.setdefault(s, []).append(
                {"other": t, "relation": row["relation"], "direction": "outgoing"}
            )
            self.edges_by_node.setdefault(t, []).append(
                {"other": s, "relation": row["relation"], "direction": "incoming"}
            )

    def _node(self, nid: str) -> dict:
        return self.ix.nodes.get(nid) or {}

    def _passage(self, pid: str) -> dict:
        p = self.ix.passages[pid]
        ident = self.ix.passage_identity(pid) or {}
        doc = self.cmap.docs.get(pid)
        return {
            "passage_id": pid,
            "work": doc.title if doc else p.work_canonical_id,
            "canonical_ref": p.canonical_ref or ident.get("canonical_ref"),
            "language": p.language,
            "text_content": _clip(p.text_content, TEXT_CAP),
        }

    # ── production-equivalent tools ────────────────────────────────────────
    def search_nodes(
        self, query: str, type_filter: str | None = None, limit: int = 10
    ) -> dict:
        limit = max(1, min(int(limit), 30))
        hits = self.ix.lexical_nodes(
            query, limit=limit, node_types={type_filter} if type_filter else None
        )
        return {
            "nodes": [
                {
                    "node_id": h.node_id,
                    "label": h.label,
                    "type": h.node_type,
                    "description": _clip(
                        self._node(h.node_id).get("description") or "", 200
                    ),
                }
                for h in hits
                if h.node_type not in {"passage", "quote"}
            ]
        }

    def get_node_detail(self, node_id: str) -> dict:
        n = self._node(node_id)
        if not n:
            return {"error": f"unknown node {node_id}"}
        return {
            "node_id": node_id,
            "label": n.get("label"),
            "type": n.get("type"),
            "description": n.get("description"),
            "period": n.get("period"),
            "school": n.get("school"),
            "neighbor_count": len(self.edges_by_node.get(node_id, [])),
            "passage_count": len(self.ix.node_passages.get(node_id, [])),
        }

    def get_neighbors(
        self,
        node_id: str,
        relation_filter: str | None = None,
        direction: str = "both",
        limit: int = 15,
    ) -> dict:
        limit = max(1, min(int(limit), 30))
        edges = []
        for e in self.edges_by_node.get(node_id, []):
            if relation_filter and e["relation"] != relation_filter:
                continue
            if direction != "both" and not e["direction"].startswith(direction):
                continue
            o = self._node(e["other"])
            edges.append(
                {
                    "node_id": e["other"],
                    "label": _clip(o.get("label") or "", 120),
                    "type": o.get("type"),
                    "relation": e["relation"],
                    "direction": e["direction"],
                }
            )
            if len(edges) >= limit:
                break
        return {
            "center_node": node_id,
            "center_label": self._node(node_id).get("label"),
            "edges": edges,
        }

    def read_passages(self, node_id: str, limit: int = 5) -> dict:
        limit = max(1, min(int(limit), 10))
        pids = self.ix.node_passages.get(node_id, [])[:limit]
        return {
            "node_id": node_id,
            "node_label": self._node(node_id).get("label"),
            "passages": [self._passage(p) for p in pids],
        }

    def search_passages(
        self, query: str, work_filter: str | None = None, limit: int = 5
    ) -> dict:
        limit = max(1, min(int(limit), 10))
        hits = self.ix.passage_index.search(query, k=limit * (5 if work_filter else 1))
        if work_filter:
            hits = [
                h
                for h in hits
                if work_filter
                in (h.passage.work_canonical_id, h.passage.manifestation_id)
            ]
        return {"passages": [self._passage(h.passage.passage_id) for h in hits[:limit]]}

    def read_passage(self, passage_id: str) -> dict:
        if passage_id not in self.ix.passages:
            return {"error": f"unknown or non-citable passage {passage_id}"}
        return self._passage(passage_id)

    # ── CorpusMap tools (arm B only) ───────────────────────────────────────
    def search_entity_pages(self, query: str, limit: int = 8) -> dict:
        limit = max(1, min(int(limit), 20))
        return {
            "pages": [
                {
                    "entity_id": e,
                    "label": self.cmap.pages[e].label,
                    "type": self.cmap.pages[e].type,
                    "linked_documents": len(self.cmap.pages[e].linked_documents),
                }
                for e, _ in self.cmap.search_pages(query, k=limit)
            ]
        }

    def read_entity_page(self, entity_id: str, focus: str | None = None) -> dict:
        if entity_id not in self.cmap.pages:
            return {"error": f"no entity page for {entity_id}"}
        return {"page": self.cmap.render(entity_id, focus=focus)}


class Server:
    def __init__(self, log: Path) -> None:
        self.tools = Tools()
        self.log = log
        self.lock = threading.Lock()
        log.parent.mkdir(parents=True, exist_ok=True)

    def handle(self, run: str, tool: str, args: dict) -> str:
        arm = run.rsplit("-", 1)[-1]
        allowed = BASE_TOOLS | (MAP_TOOLS if arm == "B" else set())
        started = time.perf_counter()
        if tool not in allowed:
            out = json.dumps(
                {"error": f"tool {tool} is not available; tools: {sorted(allowed)}"}
            )
        else:
            try:
                out = json.dumps(getattr(self.tools, tool)(**args), ensure_ascii=False)
            except Exception as exc:  # report, never crash the run
                out = json.dumps({"error": f"{type(exc).__name__}: {exc}"})
        with self.lock, self.log.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "run": run,
                        "arm": arm,
                        "tool": tool,
                        "args": args,
                        "out_chars": len(out),
                        "ms": round((time.perf_counter() - started) * 1000, 1),
                        "ts": time.time(),
                    }
                )
                + "\n"
            )
        return out


def serve(log: Path) -> None:
    server = Server(log)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = server.handle(
                body["run"], body["tool"], body.get("args") or {}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    print(f"kgtool ready on :{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


def call(run: str, tool: str, kv: list[str]) -> None:
    args: dict = {}
    for item in kv:
        k, _, v = item.partition("=")
        args[k] = v
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/",
        data=json.dumps({"run": run, "tool": tool, "args": args}).encode(),
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    print(opener.open(req, timeout=60).read().decode())


if __name__ == "__main__":
    if sys.argv[1] == "serve":
        serve(Path(sys.argv[sys.argv.index("--log") + 1]))
    else:
        call(sys.argv[1], sys.argv[2], sys.argv[3:])
