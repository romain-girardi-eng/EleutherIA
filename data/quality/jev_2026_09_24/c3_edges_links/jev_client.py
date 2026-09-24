"""Shared async Jev (typesafe-ai/jev) client over the Vercel AI Gateway.

Raw HTTP via httpx (mirrors graphrag/src/eleutheria_graphrag/services/jev_reranker.py),
since no local `ai` npm package is installed anywhere on this machine. Requires
AI_GATEWAY_API_KEY in the environment (source ~/.config/vercel-ai-gateway/env first).
"""
from __future__ import annotations

import asyncio
import os
import random
import time

import httpx

BASE_URL = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
MODEL = "typesafe-ai/jev"


def headers() -> dict[str, str]:
    key = os.environ["AI_GATEWAY_API_KEY"]
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "ai-model-id": MODEL,
        "ai-evaluation-model-specification-version": "4",
        "ai-gateway-auth-method": "api-key",
        "ai-gateway-protocol-version": "0.0.1",
    }


async def evaluate(client: httpx.AsyncClient, state, questions: dict, *, max_retries: int = 5) -> dict:
    body = {"state": state, "questions": questions}
    delay = 1.0
    last_exc = None
    for attempt in range(max_retries):
        try:
            r = await client.post(BASE_URL, headers=headers(), json=body, timeout=60.0)
            if r.status_code in (429, 500, 502, 503, 504):
                last_exc = RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                await asyncio.sleep(delay + random.random())
                delay = min(delay * 2, 30)
                continue
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, RuntimeError) as exc:
            last_exc = exc
            await asyncio.sleep(delay + random.random())
            delay = min(delay * 2, 30)
    raise last_exc or RuntimeError("evaluate failed with no exception captured")


class Pool:
    """Bounded-concurrency async task runner."""

    def __init__(self, concurrency: int):
        self.sem = asyncio.Semaphore(concurrency)

    async def run(self, coro):
        async with self.sem:
            return await coro
