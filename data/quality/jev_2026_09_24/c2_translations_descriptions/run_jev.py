"""Generic, resumable Jev runner over a candidates.jsonl file.

Usage:
    .venv/bin/python3 run_jev.py candidates_a.jsonl questions_a.json results_a.jsonl \
        --concurrency 12 [--extra-questions questions_b_person_extra.json --extra-if is_person]

Each candidate row must have "id" and "state". Questions are the same for every row
unless --extra-questions/--extra-if is given, in which case rows with
row[extra_if_key] truthy get the extra questions merged in (used for Part B's
person-only modern_scholar question).

Resumable: skips ids already present in the results file. Retries 429/5xx with
exponential backoff. Writes one JSON object per line to results file (append) and
to an errors file (candidates_a.jsonl -> errors_a.jsonl by replacing "results" name,
or <results>.errors.jsonl if the name doesn't match the convention).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
MODEL = "typesafe-ai/jev"


def load_jsonl(p: Path):
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "ai-model-id": MODEL,
        "ai-evaluation-model-specification-version": "4",
        "ai-gateway-auth-method": "api-key",
        "ai-gateway-protocol-version": "0.0.1",
    }


def extract_answers(payload: dict) -> dict:
    out = {}
    for qid, a in (payload.get("answers") or {}).items():
        if a.get("type") == "boolean":
            out[qid] = {"p": round(float(a.get("probability", 0.0)), 4)}
        elif a.get("type") == "choice":
            out[qid] = {"choice": a.get("choice"), "probs": a.get("probabilities")}
        else:
            out[qid] = a
    return out


async def call_one(client: httpx.AsyncClient, key: str, cand: dict, questions: dict, timeout: float, max_retries: int) -> dict:
    body = {"state": cand["state"], "questions": questions}
    attempt = 0
    while True:
        attempt += 1
        try:
            t0 = time.perf_counter()
            r = await client.post(BASE_URL, headers=headers(key), json=body, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                if attempt > max_retries:
                    r.raise_for_status()
                await asyncio.sleep(min(2 ** attempt, 30))
                continue
            r.raise_for_status()
            payload = r.json()
            ms = int((time.perf_counter() - t0) * 1000)
            gw = ((payload.get("providerMetadata") or {}).get("gateway")) or {}
            conf = ((payload.get("providerMetadata") or {}).get("typesafe") or {}).get("confidence")
            return {
                "id": cand["id"],
                "ms": ms,
                "cost": gw.get("cost"),
                "generationId": gw.get("generationId"),
                "canonicalSlug": (gw.get("routing") or {}).get("canonicalSlug"),
                "tokens": (payload.get("usage") or {}).get("inputTokens"),
                "confidence": conf,
                "answers": extract_answers(payload),
            }
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            if attempt > max_retries:
                return {"id": cand["id"], "error": f"{type(exc).__name__}: {exc}"[:500]}
            await asyncio.sleep(min(2 ** attempt, 30))


async def main_async(args: argparse.Namespace) -> None:
    key = os.environ.get("AI_GATEWAY_API_KEY")
    if not key:
        print("AI_GATEWAY_API_KEY not set -- source ~/.config/vercel-ai-gateway/env first", file=sys.stderr)
        sys.exit(1)

    candidates_path = Path(args.candidates)
    questions_path = Path(args.questions)
    results_path = Path(args.results)
    errors_path = results_path.with_name(results_path.stem.replace("results", "errors") + ".jsonl")
    if errors_path == results_path:
        errors_path = results_path.with_suffix(".errors.jsonl")

    base_questions = json.loads(questions_path.read_text(encoding="utf-8"))
    extra_questions = {}
    if args.extra_questions:
        extra_questions = json.loads(Path(args.extra_questions).read_text(encoding="utf-8"))

    done_ids = {r["id"] for r in load_jsonl(results_path) if "id" in r}
    all_candidates = list(load_jsonl(candidates_path))
    todo = [c for c in all_candidates if c["id"] not in done_ids]
    print(f"candidates total={len(all_candidates)} done={len(done_ids)} todo={len(todo)} concurrency={args.concurrency}")

    sem = asyncio.Semaphore(args.concurrency)
    results_f = open(results_path, "a", encoding="utf-8")
    errors_f = open(errors_path, "a", encoding="utf-8")
    lock = asyncio.Lock()
    ok = 0
    err = 0
    cost_total = 0.0
    t0 = time.perf_counter()

    async with httpx.AsyncClient() as client:
        async def worker(cand: dict) -> None:
            nonlocal ok, err, cost_total
            questions = base_questions
            if extra_questions and cand.get(args.extra_if):
                questions = {**base_questions, **extra_questions}
            async with sem:
                res = await call_one(client, key, cand, questions, args.timeout, args.max_retries)
            async with lock:
                if "error" in res:
                    err += 1
                    errors_f.write(json.dumps(res, ensure_ascii=False) + "\n")
                    errors_f.flush()
                else:
                    ok += 1
                    try:
                        cost_total += float(res.get("cost") or 0.0)
                    except (TypeError, ValueError):
                        pass
                    results_f.write(json.dumps(res, ensure_ascii=False) + "\n")
                    results_f.flush()
                n = ok + err
                if n % 200 == 0:
                    elapsed = time.perf_counter() - t0
                    print(f"{n}/{len(todo)} ok={ok} err={err} cost=${cost_total:.4f} {elapsed:.0f}s", flush=True)

        await asyncio.gather(*(worker(c) for c in todo))

    results_f.close()
    errors_f.close()
    elapsed = time.perf_counter() - t0
    print(f"DONE ok={ok} err={err} cost=${cost_total:.4f} elapsed={elapsed:.0f}s")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("candidates")
    p.add_argument("questions")
    p.add_argument("results")
    p.add_argument("--concurrency", type=int, default=12)
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--max-retries", type=int, default=5)
    p.add_argument("--extra-questions", default=None)
    p.add_argument("--extra-if", default=None, help="candidate dict key that gates the extra questions")
    asyncio.run(main_async(p.parse_args()))
