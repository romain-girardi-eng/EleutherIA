"""C1 runner: every passage in candidates.jsonl x every chunk in questions.json,
against Jev (typesafe-ai/jev) via the Vercel AI Gateway evaluation-model endpoint.

Resumable: skips (passage_id, chunk_idx) pairs already present in results.jsonl.
Concurrency-bounded asyncio pool with exponential backoff on 429/5xx.

Usage: .venv/bin/python run_c1.py [--limit N] [--concurrency 20]
"""
import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

import httpx

OUT = Path(__file__).parent
BASE_URL = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
RESULTS = OUT / "results.jsonl"
ERRORS = OUT / "errors.jsonl"


class RateLimiter:
    """Global cross-worker cooldown: on 429/5xx every worker backs off together
    (else independent per-task backoff still floods the gateway at concurrency)."""

    def __init__(self):
        self.cooldown_until = 0.0
        self.consecutive = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        now = time.monotonic()
        if now < self.cooldown_until:
            await asyncio.sleep(self.cooldown_until - now + random.uniform(0, 0.3))

    async def penalize(self, retry_after: float | None):
        async with self.lock:
            self.consecutive += 1
            wait = retry_after if retry_after else min(2 ** min(self.consecutive, 6), 60)
            self.cooldown_until = max(self.cooldown_until, time.monotonic() + wait)

    async def reward(self):
        if self.consecutive > 0:
            self.consecutive = max(0, self.consecutive - 1)


def load_jsonl(p):
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "ai-model-id": "typesafe-ai/jev",
        "ai-evaluation-model-specification-version": "4",
        "ai-gateway-auth-method": "api-key",
        "ai-gateway-protocol-version": "0.0.1",
    }


def extract_answer(spec: dict, ans: dict):
    t = spec["type"]
    if t == "boolean":
        return round(float(ans["probability"]), 4)
    if t == "choice":
        return {"choice": ans.get("choice"), "probabilities": {k: round(float(v), 4) for k, v in (ans.get("probabilities") or {}).items()}}
    if t == "score":
        return {"score": round(float(ans["score"]), 4),
                "probabilities": {k: round(float(v), 4) for k, v in (ans.get("probabilities") or {}).items()}}
    return ans


async def call_chunk(client: httpx.AsyncClient, api_key: str, text: str, chunk: dict, sem: asyncio.Semaphore,
                      limiter: "RateLimiter", max_retries: int = 10):
    body = {"state": {"passage": text}, "questions": chunk}
    delay = 1.0
    for attempt in range(max_retries):
        await limiter.wait()
        async with sem:
            t0 = time.monotonic()
            try:
                r = await client.post(BASE_URL, headers=headers(api_key), json=body, timeout=90.0)
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, 60)
                continue
        ms = int((time.monotonic() - t0) * 1000)
        if r.status_code == 429 or r.status_code >= 500:
            retry_after = None
            ra = r.headers.get("retry-after")
            if ra:
                try:
                    retry_after = float(ra)
                except ValueError:
                    retry_after = None
            await limiter.penalize(retry_after)
            if attempt == max_retries - 1:
                r.raise_for_status()
            await asyncio.sleep(delay + random.uniform(0, 0.5))
            delay = min(delay * 2, 60)
            continue
        r.raise_for_status()
        await limiter.reward()
        payload = r.json()
        answers = payload["answers"]
        out = {k: extract_answer(chunk[k], answers[k]) for k in chunk}
        meta = payload.get("providerMetadata") or {}
        cost = float((meta.get("gateway") or {}).get("cost") or 0)
        conf = (meta.get("typesafe") or {}).get("confidence") or {}
        tokens = (payload.get("usage") or {}).get("inputTokens")
        return {"ms": ms, "cost": cost, "tokens": tokens, "confidence": conf, "answers": out}
    raise RuntimeError("unreachable")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--only-ids", nargs="*", default=None)
    ap.add_argument("--ids-file", default=None,
                     help="text file, one passage id per line, in priority order (used by "
                          "mode=concepts_only to filter+order the stage-2 high-value subset).")
    ap.add_argument("--mode", choices=["all", "chunked", "passage_only", "concepts_only"], default="all",
                     help="'all': one call/passage, all 216 questions (legacy, token-heavy). "
                          "'chunked': legacy 4-calls/passage mode. "
                          "'passage_only': stage 1 re-plan -- just the 4 passage-level questions, cheap/fast. "
                          "'concepts_only': stage 2 re-plan -- the 212 concept booleans, for a filtered subset "
                          "given by --ids-file.")
    args = ap.parse_args()

    api_key = os.environ.get("AI_GATEWAY_API_KEY")
    if not api_key:
        env_path = Path.home() / ".config/vercel-ai-gateway/env"
        for line in env_path.read_text().splitlines():
            if line.startswith("AI_GATEWAY_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
    if not api_key:
        print("no AI_GATEWAY_API_KEY", file=sys.stderr)
        sys.exit(1)

    qdata = json.load(open(OUT / "questions.json", encoding="utf-8"))
    chunks = qdata["chunks"]
    n_chunks = len(chunks)
    all_in_one = qdata["all_in_one"]
    passage_only_q = qdata["passage_only"]
    concepts_only_q = qdata["concepts_only"]

    candidates = list(load_jsonl(OUT / "candidates.jsonl"))
    by_id = {c["id"]: c for c in candidates}
    if args.only_ids:
        wanted = set(args.only_ids)
        candidates = [c for c in candidates if c["id"] in wanted]
    if args.ids_file:
        order = [line.strip() for line in Path(args.ids_file).read_text().splitlines() if line.strip()]
        candidates = [by_id[pid] for pid in order if pid in by_id]
    if args.limit:
        candidates = candidates[: args.limit]

    done = set()
    chunks_seen = {}
    for row in load_jsonl(RESULTS):
        done.add((row["id"], row["chunk"]))
        chunks_seen.setdefault(row["id"], set()).add(row["chunk"])
    print(f"resuming: {len(done)} (passage,chunk) pairs already done", flush=True)

    # a passage already has full concept coverage if it has 'all', or all 4
    # legacy chunks, or the dedicated 'concepts_only' row.
    concept_complete = {
        pid for pid, s in chunks_seen.items()
        if "all" in s or "concepts_only" in s or all(ci in s for ci in range(n_chunks))
    }
    # a passage already has the passage-level questions answered if it has
    # 'all', legacy chunk 0 (which carried them), or the dedicated row.
    passage_level_complete = {
        pid for pid, s in chunks_seen.items()
        if "all" in s or "passage_level" in s or 0 in s
    }

    if args.mode == "chunked":
        chunk_defs = {ci: chunks[ci] for ci in range(n_chunks)}
        tasks = []
        for c in candidates:
            for ci in range(n_chunks):
                if (c["id"], ci) not in done:
                    tasks.append((c, ci))
        print(f"todo: {len(tasks)} calls over {len(candidates)} passages x {n_chunks} chunks", flush=True)
    elif args.mode == "passage_only":
        chunk_defs = {"passage_level": passage_only_q}
        tasks = []
        for c in candidates:
            if c["id"] in passage_level_complete:
                continue
            if (c["id"], "passage_level") in done:
                continue
            tasks.append((c, "passage_level"))
        print(f"passage-level already covered: {len(passage_level_complete)}", flush=True)
        print(f"todo: {len(tasks)} calls (mode=passage_only) over {len(candidates)} passages", flush=True)
    elif args.mode == "concepts_only":
        chunk_defs = {"concepts_only": concepts_only_q}
        tasks = []
        for c in candidates:
            if c["id"] in concept_complete:
                continue
            if (c["id"], "concepts_only") in done:
                continue
            tasks.append((c, "concepts_only"))
        print(f"concept-coverage already complete: {len(concept_complete)}", flush=True)
        print(f"todo: {len(tasks)} calls (mode=concepts_only) over {len(candidates)} passages", flush=True)
    else:
        # 'all' mode: one call/passage. Skip passages already fully covered by the
        # legacy 4-chunk scheme (chunks 0..n_chunks-1 all present) -- their data is
        # equivalent, no need to re-spend a call. Everything else gets one 'all' call.
        chunk_defs = {"all": all_in_one}
        legacy_complete = {pid for pid, s in chunks_seen.items() if all(ci in s for ci in range(n_chunks))}
        tasks = []
        for c in candidates:
            if c["id"] in legacy_complete:
                continue
            if (c["id"], "all") in done:
                continue
            tasks.append((c, "all"))
        print(f"legacy-complete passages skipped: {len(legacy_complete)}", flush=True)
        print(f"todo: {len(tasks)} calls (mode=all, 1 call/passage) over {len(candidates)} passages", flush=True)

    sem = asyncio.Semaphore(args.concurrency)
    limiter = RateLimiter()
    results_lock = asyncio.Lock()
    errors_lock = asyncio.Lock()
    stats = {"ok": 0, "err": 0, "cost": 0.0}
    t0 = time.monotonic()

    async with httpx.AsyncClient() as client:
        async def worker(item):
            c, ci = item
            try:
                res = await call_chunk(client, api_key, c["text"], chunk_defs[ci], sem, limiter)
                row = {"id": c["id"], "chunk": ci, **res}
                async with results_lock:
                    with open(RESULTS, "a", encoding="utf-8") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                stats["ok"] += 1
                stats["cost"] += res["cost"]
            except Exception as e:
                async with errors_lock:
                    with open(ERRORS, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"id": c["id"], "chunk": ci, "error": str(e)[:300]}, ensure_ascii=False) + "\n")
                stats["err"] += 1
            n = stats["ok"] + stats["err"]
            if n % 500 == 0:
                el = time.monotonic() - t0
                print(f"{n}/{len(tasks)} ok={stats['ok']} err={stats['err']} cost=${stats['cost']:.3f} {el:.0f}s rate={n/max(el,1):.1f}/s", flush=True)

        CH = 2000
        for i in range(0, len(tasks), CH):
            batch = tasks[i:i + CH]
            await asyncio.gather(*(worker(t) for t in batch))

    el = time.monotonic() - t0
    print(f"DONE ok={stats['ok']} err={stats['err']} cost=${stats['cost']:.3f} {el:.0f}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
