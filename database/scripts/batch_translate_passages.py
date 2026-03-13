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

SCHEMA = "free_will"

# Gemini Flash 2.5 — cheapest, 1M context
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Batch sizes tuned for Gemini Flash context limits
# ~50 passages per batch, ~200k chars max per batch
BATCH_SIZE = 10
MAX_CHARS_PER_BATCH = 40_000

# Priority tiers (work canonical_id patterns)
PRIORITY_TIERS = {
    "P0": [
        # Core free will texts — highest GraphRAG query frequency
        "urn:cts:latinLit:phi0474.phi049",  # Cicero De Fato
        "urn:cts:greekLit:tlg0557",          # Epictetus
        "urn:cts:greekLit:tlg0732",          # Alexander of Aphrodisias
    ],
    "P1": [
        # Major philosophical sources
        "oga:tlg0086.tlg010",                # Aristotle NE
        "oga:tlg0086.tlg025",                # Aristotle Met
        "urn:cts:greekLit:tlg0086.tlg007",   # Aristotle DI
        "urn:cts:greekLit:tlg0059.tlg031",   # Plato Timaeus
        "urn:cts:greekLit:tlg0059.tlg004",   # Plato Phaedo
        "urn:cts:greekLit:tlg0059.tlg012",   # Plato Phaedrus
        "urn:cts:greekLit:tlg0007.tlg142",   # Plutarch De Fato
        "urn:cts:greekLit:tlg0007",          # Plutarch (all)
    ],
    "P2": [
        # Patristic/Late Antique core
        "urn:cts:latinLit:stoa0040.stoa003", # Augustine DLA
        "urn:cts:latinLit:stoa0040.stoa001", # Augustine CivDei
        "urn:cts:latinLit:phi2089.phi002",   # Boethius
        "urn:cts:greekLit:tlg2959.tlg001",   # Methodius
    ],
    "P3": [
        # Large corpora, high value
        "urn:cts:greekLit:tlg0562.tlg001",   # Marcus Aurelius
        "urn:cts:latinLit:phi0550.phi001",   # Lucretius
        "urn:cts:greekLit:tlg0544",          # Sextus Empiricus
        "urn:cts:latinLit:phi1017.phi015",   # Seneca Ep.
    ],
}


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


def build_translation_prompt(batch: list[dict]) -> str:
    """Build a prompt for translating a batch of passages."""
    lang = batch[0]["language"]
    lang_name = {"grc": "Ancient Greek", "lat": "Latin", "heb": "Hebrew"}.get(lang, lang)

    prompt = f"""You are a classical philologist translating {lang_name} passages into English.

INSTRUCTIONS:
- Translate each passage faithfully into scholarly English
- Preserve technical philosophical terms in transliteration where standard (e.g. heimarmene, pronoia, to eph' hêmin, autexousion)
- Do NOT paraphrase, summarize, or add commentary
- Do NOT add information not present in the original
- For fragmentary or unclear text, translate what is there and mark lacunae with [...]
- Keep the scholarly register appropriate for an academic philosophy reference work

OUTPUT FORMAT:
Return a JSON array. For each passage, output:
{{"id": "<node_id>", "en": "<English translation>"}}

PASSAGES TO TRANSLATE:
"""
    for p in batch:
        ref_label = f" ({p['ref']})" if p['ref'] else ""
        prompt += f"\n--- {p['node_id']}{ref_label} ---\n{p['text']}\n"

    return prompt


def call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini Flash API and return the text response."""
    import urllib.error
    import urllib.request

    url = GEMINI_API_URL.format(model=GEMINI_MODEL) + f"?key={api_key}"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 65536,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  HTTP {e.code}: {body[:500]}")
        raise

    # Extract text from Gemini response
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        print(f"  Unexpected response structure: {json.dumps(data)[:500]}")
        raise
    return text


def parse_translation_response(text: str) -> list[dict]:
    """Parse Gemini's JSON response into translation dicts."""
    import re as _re

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                items = json.loads(text[start:end])
            except json.JSONDecodeError:
                # Last resort: extract individual objects with regex
                items = []
                for m in _re.finditer(r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"en"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', text):
                    items.append({"id": m.group(1), "en": m.group(2).replace('\\"', '"').replace('\\n', '\n')})
                if not items:
                    print(f"  ERROR: Could not parse response as JSON: {text[:200]}...")
                    return []
        else:
            print(f"  ERROR: Could not parse response as JSON: {text[:200]}...")
            return []

    results = []
    for item in items:
        node_id = item.get("id", "")
        translation = item.get("en", "")
        if node_id and translation:
            results.append({"node_id": node_id, "translation": translation})
    return results


def batch_passages(passages: list[dict]) -> list[list[dict]]:
    """Split passages into batches respecting size limits."""
    batches = []
    current_batch: list[dict] = []
    current_chars = 0

    for p in passages:
        text_len = len(p["text"])
        if current_batch and (
            len(current_batch) >= BATCH_SIZE
            or current_chars + text_len > MAX_CHARS_PER_BATCH
        ):
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(p)
        current_chars += text_len

    if current_batch:
        batches.append(current_batch)

    return batches


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
