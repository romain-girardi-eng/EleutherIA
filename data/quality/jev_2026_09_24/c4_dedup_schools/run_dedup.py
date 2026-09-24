"""PART A -- send candidate pairs to Jev, two booleans per pair, chunked.

Resumable: reruns skip chunk ids already present in results_dedup.jsonl.
Writes only under this campaign dir; never touches data/kg/*.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from lib_common import CAMPAIGN_DIR, JevRunner, get_api_key

PAIRS_PER_CHUNK = 10
CANDIDATES_PATH = CAMPAIGN_DIR / "candidates.jsonl"
RESULTS_PATH = CAMPAIGN_DIR / "results_dedup.jsonl"
ERRORS_PATH = CAMPAIGN_DIR / "errors_dedup.jsonl"

Q_SAME = (
    "a and b refer to exactly the same real-world entity (same person, same "
    "work, same publication, or same concept) -- not merely related or similar."
)
Q_PART = (
    "a is a part, section, edition, or translation of b, OR b is a part, "
    "section, edition, or translation of a (related but not strictly identical)."
)


def load_candidates() -> list[dict]:
    rows = []
    with CANDIDATES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def chunk_pairs(rows: list[dict], size: int) -> list[dict]:
    chunks = []
    for i in range(0, len(rows), size):
        batch = rows[i : i + size]
        chunks.append({
            "id": f"chunk_{i // size:05d}",
            "pair_ids": [r["pair_id"] for r in batch],
            "pairs": batch,
        })
    return chunks


def state_of(chunk: dict) -> dict:
    return {
        "pairs": [
            {"index": i, "a": r["a"], "b": r["b"]}
            for i, r in enumerate(chunk["pairs"])
        ]
    }


def questions_of(chunk: dict) -> dict:
    qs = {}
    for i in range(len(chunk["pairs"])):
        qs[f"same_{i}"] = {
            "type": "boolean",
            "instructions": f"For pairs[{i}]: {Q_SAME}",
        }
        qs[f"part_{i}"] = {
            "type": "boolean",
            "instructions": f"For pairs[{i}]: {Q_PART}",
        }
    return qs


async def main() -> None:
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    rows = load_candidates()
    print(f"candidates: {len(rows)}")
    chunks = chunk_pairs(rows, PAIRS_PER_CHUNK)
    print(f"chunks: {len(chunks)} (size {PAIRS_PER_CHUNK})")

    # persist the chunk->pair_ids map for the explode step (resumable-safe: append-only, dedup on load)
    map_path = CAMPAIGN_DIR / "chunks_map_dedup.jsonl"
    existing_chunk_ids = set()
    if map_path.exists():
        with map_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_chunk_ids.add(json.loads(line)["id"])
    with map_path.open("a", encoding="utf-8") as f:
        for c in chunks:
            if c["id"] not in existing_chunk_ids:
                f.write(json.dumps({"id": c["id"], "pair_ids": c["pair_ids"]}, ensure_ascii=False) + "\n")

    runner = JevRunner(api_key=get_api_key(), concurrency=concurrency)
    await runner.run(chunks, state_of, questions_of, RESULTS_PATH, ERRORS_PATH, id_key="id")


if __name__ == "__main__":
    asyncio.run(main())
