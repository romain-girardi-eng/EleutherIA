#!/usr/bin/env python3
"""
Batch-translate KG passage nodes from Greek/Latin to English.

Reads original-language passage nodes from the DB, sends them to Gemini Flash
for translation in batches, and writes JSON output compatible with
create_passage_translations.py.

Usage:
    set -a; source .env; set +a

    # Translate all passages for a specific work (dry-run — just shows what would be sent)
    uv run --directory database python database/scripts/batch_translate_passages.py \
        --work-canonical-id "urn:cts:latinLit:phi0474.phi049" \
        --output /tmp/translations_cic_fat.json

    # Translate P0 priority works (core free will texts)
    uv run --directory database python database/scripts/batch_translate_passages.py \
        --priority P0 \
        --output /tmp/translations_p0.json

    # Translate ALL passages missing _en nodes
    uv run --directory database python database/scripts/batch_translate_passages.py \
        --all \
        --output /tmp/translations_all.json

    # Then apply:
    uv run --directory database python database/scripts/create_passage_translations.py \
        --translations /tmp/translations_p0.json --confirm
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import psycopg2

from eleutheria_database.services.translation import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_CHARS_PER_BATCH,
    DEFAULT_MODEL,
    PRIORITY_TIERS,
    PassageToTranslate,
)
from eleutheria_database.services.translation import (
    batch_passages as _batch_passages,
)
from eleutheria_database.services.translation import (
    build_translation_prompt as _build_translation_prompt,
)
from eleutheria_database.services.translation import (
    call_gemini as _call_gemini,
)
from eleutheria_database.services.translation import (
    parse_translation_response as _parse_translation_response,
)

SCHEMA = "free_will"

# Re-exported for CLI compatibility — single source of truth lives in
# eleutheria_database.services.translation.
GEMINI_MODEL = DEFAULT_MODEL
BATCH_SIZE = DEFAULT_BATCH_SIZE
MAX_CHARS_PER_BATCH = DEFAULT_MAX_CHARS_PER_BATCH


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


def fetch_passages_needing_translation(
    db_url: str,
    work_canonical_id: str | None = None,
    priority: str | None = None,
    fetch_all: bool = False,
) -> list[dict]:
    """Fetch passage nodes that need _en translation."""
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    where_clauses = [
        "n.type = 'passage'",
        "n.node_id NOT LIKE '%%\\_en'",
        "NOT EXISTS (SELECT 1 FROM kg_nodes en WHERE en.node_id = n.node_id || '_en')",
    ]
    params: list = []

    if work_canonical_id:
        where_clauses.append("n.metadata->>'work_canonical_id' = %s")
        params.append(work_canonical_id)
    elif priority:
        tiers = PRIORITY_TIERS.get(priority, [])
        if not tiers:
            print(f"ERROR: Unknown priority tier '{priority}'")
            sys.exit(1)
        # Match any of the canonical_ids (prefix match for broad URNs)
        like_clauses = []
        for t in tiers:
            like_clauses.append("n.metadata->>'work_canonical_id' LIKE %s")
            params.append(t + "%")
        where_clauses.append("(" + " OR ".join(like_clauses) + ")")
    elif not fetch_all:
        print("ERROR: Specify --work-canonical-id, --priority, or --all")
        sys.exit(1)

    query = f"""
        SELECT n.node_id, n.description, n.metadata->>'language' as lang,
               n.metadata->>'author' as author, n.metadata->>'work_title' as title,
               n.metadata->>'canonical_ref' as ref
        FROM kg_nodes n
        WHERE {' AND '.join(where_clauses)}
        ORDER BY n.metadata->>'work_canonical_id', n.node_id
    """
    cur.execute(query, tuple(params) if params else None)
    rows = cur.fetchall()
    conn.close()

    passages = []
    for r in rows:
        passages.append({
            "node_id": r[0],
            "text": r[1] or "",
            "language": r[2] or "unknown",
            "author": r[3] or "",
            "title": r[4] or "",
            "ref": r[5] or "",
        })
    return passages


def _to_dataclass(p: dict) -> PassageToTranslate:
    """Coerce the script's dict-shaped passage into the service dataclass."""
    return PassageToTranslate(
        node_id=p["node_id"],
        text=p.get("text", ""),
        language=p.get("language", "unknown"),
        author=p.get("author", ""),
        title=p.get("title", ""),
        ref=p.get("ref", ""),
    )


def build_translation_prompt(batch: list[dict]) -> str:
    """Build a prompt for translating a batch of passages."""
    return _build_translation_prompt([_to_dataclass(p) for p in batch])


def call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini Flash API and return the text response."""
    try:
        return _call_gemini(prompt, api_key, model=GEMINI_MODEL)
    except RuntimeError as e:
        print(f"  {e}")
        raise


def parse_translation_response(text: str) -> list[dict]:
    """Parse Gemini's JSON response into translation dicts."""
    items = _parse_translation_response(text)
    if not items:
        print(f"  ERROR: Could not parse response as JSON: {text[:200]}...")
    return [{"node_id": t.node_id, "translation": t.translation} for t in items]


def batch_passages(passages: list[dict]) -> list[list[dict]]:
    """Split passages into batches respecting size limits."""
    typed_batches = _batch_passages(
        [_to_dataclass(p) for p in passages],
        batch_size=BATCH_SIZE,
        max_chars_per_batch=MAX_CHARS_PER_BATCH,
    )
    # Round-trip back to dicts so existing CLI logic (sum(len(p["text"])),
    # batch[0]["language"], etc.) keeps working.
    return [
        [
            {
                "node_id": p.node_id,
                "text": p.text,
                "language": p.language,
                "author": p.author,
                "title": p.title,
                "ref": p.ref,
            }
            for p in batch
        ]
        for batch in typed_batches
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-translate KG passage nodes to English."
    )
    parser.add_argument("--work-canonical-id", help="Translate passages for a specific work")
    parser.add_argument("--priority", choices=["P0", "P1", "P2", "P3"], help="Translate by priority tier")
    parser.add_argument("--all", action="store_true", help="Translate all passages needing _en")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--db-url", help="Database URL (default: DATABASE_URL env var)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated without calling LLM")
    parser.add_argument("--resume", help="Resume from a partial output file (skip already-translated node_ids)")
    args = parser.parse_args()

    db_url = args.db_url or get_db_url()
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: GEMINI_API_KEY not set.")
        sys.exit(1)

    # Fetch passages
    passages = fetch_passages_needing_translation(
        db_url,
        work_canonical_id=args.work_canonical_id,
        priority=args.priority,
        fetch_all=args.all,
    )
    print(f"Passages to translate: {len(passages)}")
    total_chars = sum(len(p["text"]) for p in passages)
    print(f"Total characters: {total_chars:,}")

    if not passages:
        print("Nothing to translate.")
        return

    # Load existing translations if resuming
    existing_ids: set[str] = set()
    all_translations: list[dict] = []
    if args.resume and Path(args.resume).exists():
        with open(args.resume) as f:
            all_translations = json.load(f)
        existing_ids = {t["node_id"] for t in all_translations}
        print(f"Resuming: {len(existing_ids)} already translated")
        passages = [p for p in passages if p["node_id"] not in existing_ids]
        print(f"Remaining: {len(passages)}")

    # Build batches
    batches = batch_passages(passages)
    print(f"Batches: {len(batches)}")

    if args.dry_run:
        print("\nDRY RUN — showing batch breakdown:")
        for i, batch in enumerate(batches):
            chars = sum(len(p["text"]) for p in batch)
            lang = batch[0]["language"]
            print(f"  Batch {i+1}: {len(batch)} passages, {chars:,} chars, lang={lang}")
            if i < 2:
                for p in batch[:3]:
                    print(f"    {p['node_id']:50s} {len(p['text']):>6} chars  {p['ref']}")
        est_tokens = total_chars / 4 * 2  # input + output estimate
        print(f"\nEstimated tokens: ~{est_tokens:,.0f}")
        print(f"Estimated cost (Gemini Flash): ~${est_tokens * 0.15 / 1_000_000:.2f}")
        return

    # Translate batches
    output_path = Path(args.output)
    for i, batch in enumerate(batches):
        chars = sum(len(p["text"]) for p in batch)
        print(f"\nBatch {i+1}/{len(batches)}: {len(batch)} passages, {chars:,} chars")

        prompt = build_translation_prompt(batch)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_text = call_gemini(prompt, api_key)
                translations = parse_translation_response(response_text)
                if translations:
                    print(f"  Got {len(translations)} translations")
                    break
                else:
                    print(f"  WARNING: Empty parse result, retrying ({attempt+1}/{max_retries})")
                    time.sleep(2)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 60 if "429" in str(e) else 3 * (attempt + 1)
                    print(f"  Retry {attempt+1}/{max_retries} after error: {e}")
                    time.sleep(wait)
                else:
                    print(f"  ERROR in batch {i+1}: {e}")
                    with open(output_path, "w") as f:
                        json.dump(all_translations, f, ensure_ascii=False, indent=2)
                    print(f"  Saved {len(all_translations)} translations so far to {output_path}")
                    print(f"  Re-run with --resume {output_path} to continue.")
                    sys.exit(1)
        else:
            print(f"  SKIP batch {i+1}: all retries failed")
            continue

        # Validate: check all node_ids match
        batch_ids = {p["node_id"] for p in batch}
        returned_ids = {t["node_id"] for t in translations}
        missing = batch_ids - returned_ids
        if missing:
            print(f"  WARNING: {len(missing)} passages not returned: {list(missing)[:5]}")

        all_translations.extend(translations)

        # Save incrementally after each batch
        with open(output_path, "w") as f:
            json.dump(all_translations, f, ensure_ascii=False, indent=2)

        # Rate limit: 5 seconds between batches (free tier = ~10 RPM safe)
        if i < len(batches) - 1:
            time.sleep(5)

    # Final save
    with open(output_path, "w") as f:
        json.dump(all_translations, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(all_translations)} translations saved to {output_path}")
    print(f"Next: uv run --directory database python database/scripts/create_passage_translations.py --translations {output_path} --confirm")


if __name__ == "__main__":
    main()
