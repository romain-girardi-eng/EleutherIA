"""Part B runner: propose missing node -> concept links with Jev.

For every candidate node (argument/work/publication/person/synthesis, from
candidates_B.jsonl) ask booleans against all 212 concepts, batched ~55 per
call (4 calls/node). Never asks about doctrinal stance -- only "deals with
the concept". Resumable at node granularity (a node's chunks all succeed
before one merged result line is written); concurrency: 16 node-tasks.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from jev_client import Pool, evaluate  # noqa: E402

D = Path(__file__).parent
RESULTS = D / "results_B.jsonl"
ERRORS = D / "errors_B.jsonl"
CONCURRENCY = 16
CHUNK_SIZE = 55

TYPE_LABEL = {
    "argument": "philosophical argument",
    "work": "ancient work",
    "publication": "modern scholarly publication",
    "person": "person",
    "synthesis": "dialectical synthesis",
}


def load_jsonl(p: Path):
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


async def main() -> None:
    concepts = json.loads((D / "concepts_B.json").read_text(encoding="utf-8"))
    concept_items = list(concepts.items())
    chunks = list(chunk(concept_items, CHUNK_SIZE))
    rows = list(load_jsonl(D / "candidates_B.jsonl"))
    done = {r["id"] for r in load_jsonl(RESULTS)}
    todo = [r for r in rows if r["id"] not in done]
    print(f"nodes total {len(rows)}, already done {len(done)}, to do {len(todo)}, "
          f"concepts {len(concept_items)} in {len(chunks)} chunks/node", flush=True)

    pool = Pool(CONCURRENCY)
    results_f = open(RESULTS, "a", encoding="utf-8")
    errors_f = open(ERRORS, "a", encoding="utf-8")
    lock = asyncio.Lock()
    ok = 0
    errs = 0
    cost_total = 0.0
    t0 = time.time()

    async with httpx.AsyncClient() as client:
        async def one(row):
            nonlocal ok, errs, cost_total
            type_label = TYPE_LABEL.get(row["type"], row["type"])
            state = {"entity": {"type": row["type"], "name": row["name"], "description": row["description"]}}
            merged_p: dict[str, float] = {}
            calls_cost = 0.0
            tokens_total = 0
            t = time.time()
            try:
                for c in chunks:
                    jq = {
                        cid: {
                            "type": "boolean",
                            "instructions": (
                                f"This {type_label} (`entity`), as described, explicitly deals "
                                f"with the concept: {info['label']}. {info['gloss']}"
                            ),
                        }
                        for cid, info in c
                    }
                    out = await evaluate(client, state, jq)
                    gw = (out.get("providerMetadata") or {}).get("gateway") or {}
                    calls_cost += float(gw.get("cost") or 0)
                    tokens_total += (out.get("usage") or {}).get("inputTokens") or 0
                    for cid, ans in out["answers"].items():
                        merged_p[cid] = ans["probability"]
                rec = {
                    "id": row["id"],
                    "type": row["type"],
                    "p": merged_p,
                    "cost": calls_cost,
                    "tokens": tokens_total,
                    "ms": int((time.time() - t) * 1000),
                    "calls": len(chunks),
                }
                async with lock:
                    results_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    results_f.flush()
                    ok += 1
                    cost_total += calls_cost
                    if (ok + errs) % 100 == 0:
                        print(f"{ok + errs}/{len(todo)} ok={ok} errs={errs} "
                              f"${cost_total:.3f} {time.time() - t0:.0f}s", flush=True)
            except Exception as exc:  # noqa: BLE001
                async with lock:
                    errors_f.write(json.dumps({"id": row["id"], "error": str(exc)[:300]}, ensure_ascii=False) + "\n")
                    errors_f.flush()
                    errs += 1

        await asyncio.gather(*(pool.run(one(row)) for row in todo))

    results_f.close()
    errors_f.close()
    print(f"DONE ok={ok} errs={errs} cost=${cost_total:.3f} wall={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
