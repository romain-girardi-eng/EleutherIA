"""Part A runner: validate existing semantic KG edges with Jev.

One API call per edge, two booleans (relation-specific + generic). Resumable
(skips ids already present in results_A.jsonl). Concurrency: 16.
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
RESULTS = D / "results_A.jsonl"
ERRORS = D / "errors_A.jsonl"
CONCURRENCY = 16


def load_jsonl(p: Path):
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


async def main() -> None:
    questions = json.loads((D / "questions_A.json").read_text(encoding="utf-8"))
    rows = list(load_jsonl(D / "candidates_A.jsonl"))
    done = {r["id"] for r in load_jsonl(RESULTS)}
    todo = [r for r in rows if r["id"] not in done]
    print(f"edges total {len(rows)}, already done {len(done)}, to do {len(todo)}", flush=True)

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
            q = questions[row["relation"]]
            jev_questions = {
                "specific": {"type": "boolean", "instructions": q["specific"]},
                "generic": {"type": "boolean", "instructions": q["generic"]},
            }
            state = {"source": row["source"], "target": row["target"]}
            t = time.time()
            try:
                out = await evaluate(client, state, jev_questions)
                gw = (out.get("providerMetadata") or {}).get("gateway") or {}
                rec = {
                    "id": row["id"],
                    "relation": row["relation"],
                    "source_id": row["source_id"],
                    "target_id": row["target_id"],
                    "p_specific": out["answers"]["specific"]["probability"],
                    "p_generic": out["answers"]["generic"]["probability"],
                    "cost": float(gw.get("cost") or 0),
                    "tokens": (out.get("usage") or {}).get("inputTokens"),
                    "ms": int((time.time() - t) * 1000),
                    "generation_id": gw.get("generationId"),
                }
                async with lock:
                    results_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    results_f.flush()
                    ok += 1
                    cost_total += rec["cost"]
                    if (ok + errs) % 500 == 0:
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
