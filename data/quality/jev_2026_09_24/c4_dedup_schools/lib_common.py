"""Shared helpers for the c4_dedup_schools Jev campaign (2026-09-24).

Loads data/kg/nodes.jsonl READ-ONLY, normalizes text for blocking, and wraps
the Jev evaluation-model endpoint with a bounded async pool + resumable
results file. No writes to data/kg/* ever happen here.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import httpx

REPO_ROOT = Path(__file__).resolve().parents[4]
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
CAMPAIGN_DIR = Path(__file__).resolve().parent

JEV_URL = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
JEV_MODEL = "typesafe-ai/jev"

STOPWORDS = {
    "the", "and", "of", "in", "on", "de", "du", "la", "le", "les", "des",
    "der", "die", "das", "van", "von", "el", "al", "on", "to", "for",
    "with", "his", "her", "its", "their", "book", "part", "vol", "volume",
    "letter", "letters", "chapter", "chapters", "fragment", "fragments",
    "saint", "st", "sur", "et", "und", "or", "a", "an", "this", "that",
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def norm_text(s: str | None) -> str:
    if not s:
        return ""
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


YEAR_RE = re.compile(r"^\d{3,4}[a-z]?$")


def significant_tokens(s: str | None, min_len: int = 4) -> set[str]:
    toks = norm_text(s).split()
    out = set()
    for t in toks:
        if len(t) < min_len:
            continue
        if t in STOPWORDS:
            continue
        if YEAR_RE.match(t):
            continue
        out.add(t)
    return out


def safe_json_field(v: Any) -> Any:
    """metadata / alternative_names are sometimes a JSON string, sometimes parsed."""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return v
    return v


def load_nonpassage_nodes() -> list[dict[str, Any]]:
    nodes = []
    with NODES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("type") == "passage":
                continue
            d["alternative_names"] = safe_json_field(d.get("alternative_names")) or []
            d["metadata"] = safe_json_field(d.get("metadata")) or {}
            nodes.append(d)
    return nodes


def load_all_nodes_school_field() -> list[dict[str, Any]]:
    """Includes passages too -- only for the deterministic school-string tally."""
    nodes = []
    with NODES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            nodes.append(d)
    return nodes


# ---------------------------------------------------------------------------
# Jev HTTP
# ---------------------------------------------------------------------------


def jev_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "ai-model-id": JEV_MODEL,
        "ai-evaluation-model-specification-version": "4",
        "ai-gateway-auth-method": "api-key",
        "ai-gateway-protocol-version": "0.0.1",
    }


class JevRunner:
    """Bounded-concurrency, resumable runner over evaluation-model calls."""

    def __init__(
        self,
        api_key: str,
        concurrency: int = 12,
        timeout_s: float = 60.0,
        max_retries: int = 5,
    ) -> None:
        self.api_key = api_key
        self.concurrency = concurrency
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.total_cost = 0.0
        self.n_calls = 0
        self.n_errors = 0

    async def _call_once(
        self, client: httpx.AsyncClient, state: Any, questions: dict[str, Any]
    ) -> dict[str, Any]:
        body = {"state": state, "questions": questions}
        backoff = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                r = await client.post(
                    JEV_URL, headers=jev_headers(self.api_key), json=body,
                    timeout=self.timeout_s,
                )
                if r.status_code == 429 or r.status_code >= 500:
                    last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 20.0)
                    continue
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, RuntimeError) as exc:
                last_exc = exc
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 20.0)
        raise last_exc or RuntimeError("unknown Jev failure")

    async def run(
        self,
        items: list[dict[str, Any]],
        state_of,
        questions_of,
        results_path: Path,
        errors_path: Path,
        id_key: str = "pair_id",
    ) -> None:
        """items: list of dicts each carrying id_key + whatever state_of/questions_of need."""
        done_ids: set[str] = set()
        if results_path.exists():
            with results_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        done_ids.add(json.loads(line)["id"])
                    except (json.JSONDecodeError, KeyError):
                        continue
        todo = [it for it in items if it[id_key] not in done_ids]
        print(f"[JevRunner] total={len(items)} already_done={len(done_ids)} todo={len(todo)}")
        if not todo:
            return

        sem = asyncio.Semaphore(self.concurrency)
        results_f = results_path.open("a", encoding="utf-8")
        errors_f = errors_path.open("a", encoding="utf-8")
        lock = asyncio.Lock()

        async with httpx.AsyncClient() as client:
            async def worker(it: dict[str, Any]) -> None:
                async with sem:
                    t0 = time.perf_counter()
                    try:
                        payload = await self._call_once(
                            client, state_of(it), questions_of(it)
                        )
                    except Exception as exc:  # noqa: BLE001
                        async with lock:
                            self.n_errors += 1
                            errors_f.write(json.dumps({
                                "id": it[id_key], "error": str(exc),
                                "ts": time.time(),
                            }, ensure_ascii=False) + "\n")
                            errors_f.flush()
                        return
                    ms = int((time.perf_counter() - t0) * 1000)
                    meta = payload.get("providerMetadata") or {}
                    gw = meta.get("gateway") or {}
                    cost = float(gw.get("cost") or 0.0)
                    row = {
                        "id": it[id_key],
                        "answers": payload.get("answers"),
                        "confidence": (meta.get("typesafe") or {}).get("confidence"),
                        "cost": cost,
                        "generationId": gw.get("generationId"),
                        "canonicalSlug": ((gw.get("routing") or {}).get("canonicalSlug")),
                        "usage": payload.get("usage"),
                        "ms": ms,
                    }
                    async with lock:
                        self.n_calls += 1
                        self.total_cost += cost
                        results_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        results_f.flush()
                        if self.n_calls % 50 == 0:
                            print(f"  ... {self.n_calls}/{len(todo)} done, "
                                  f"{self.n_errors} errors, cost so far ${self.total_cost:.4f}")

            await asyncio.gather(*(worker(it) for it in todo))
        results_f.close()
        errors_f.close()
        print(f"[JevRunner] DONE calls={self.n_calls} errors={self.n_errors} "
              f"cost=${self.total_cost:.4f}")


def get_api_key() -> str:
    key = os.environ.get("AI_GATEWAY_API_KEY")
    if not key:
        raise RuntimeError("AI_GATEWAY_API_KEY not set; source ~/.config/vercel-ai-gateway/env")
    return key
