"""PART B.2 -- send the school CHOICE question to Jev, chunked, resumable."""

from __future__ import annotations

import asyncio
import json
import sys

from build_candidates_school import SCHOOL_CRITERIA
from lib_common import CAMPAIGN_DIR, JevRunner, get_api_key

NODES_PER_CHUNK = 8
CANDIDATES_PATH = CAMPAIGN_DIR / "candidates_school.jsonl"
RESULTS_PATH = CAMPAIGN_DIR / "results_school.jsonl"
ERRORS_PATH = CAMPAIGN_DIR / "errors_school.jsonl"

Q_INSTRUCTIONS = (
    "Based only on the description of items[{i}] (an ancient/medieval person, "
    "work, or a scholarly argument about one), which philosophical school or "
    "intellectual tradition is it primarily associated with?"
)


def load_candidates() -> list[dict]:
    rows = []
    with CANDIDATES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def chunk_rows(rows: list[dict], size: int) -> list[dict]:
    chunks = []
    for i in range(0, len(rows), size):
        batch = rows[i : i + size]
        chunks.append({
            "id": f"schunk_{i // size:05d}",
            "node_ids": [r["node_id"] for r in batch],
            "rows": batch,
        })
    return chunks


def state_of(chunk: dict) -> dict:
    return {"items": [r["state"] for r in chunk["rows"]]}


def questions_of(chunk: dict) -> dict:
    qs = {}
    for i in range(len(chunk["rows"])):
        qs[f"school_{i}"] = {
            "type": "choice",
            "instructions": Q_INSTRUCTIONS.format(i=i),
            "criteria": SCHOOL_CRITERIA,
        }
    return qs


async def main() -> None:
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    rows = load_candidates()
    print(f"candidates_school: {len(rows)}")
    chunks = chunk_rows(rows, NODES_PER_CHUNK)
    print(f"chunks: {len(chunks)} (size {NODES_PER_CHUNK})")

    map_path = CAMPAIGN_DIR / "chunks_map_school.jsonl"
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
                f.write(json.dumps({"id": c["id"], "node_ids": c["node_ids"]}, ensure_ascii=False) + "\n")

    runner = JevRunner(api_key=get_api_key(), concurrency=concurrency)
    await runner.run(chunks, state_of, questions_of, RESULTS_PATH, ERRORS_PATH, id_key="id")


if __name__ == "__main__":
    asyncio.run(main())
