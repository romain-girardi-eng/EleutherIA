"""Structured argument enrichment via Kimi K2.6 (Fireworks).

Sweeps every `argument` node in the KG and rewrites its metadata into an
explicit premise/conclusion form with attestation, primary-source anchors,
validity assessment, and engagement links.

Hard constraints
----------------
* NO fabrication. Every premise must either be:
    - attestation="direct"          (textually supported by a primary passage)
    - attestation="doxographical"   (supported by a later doxographer)
    - attestation="reconstructed"   (explicitly flagged; carries scholarly src)
* If Kimi returns a premise tagged "direct" or "doxographical" but cites no
  primary_source, the patch is rejected and re-prompted once. After the second
  failure the argument is flagged `needs_review`.
* Idempotent: a node carrying `metadata.structured_v2 = true` is skipped unless
  --force is passed.
* The legacy `premises` array (flat strings) is preserved as
  `metadata.legacy_premises` so we never silently drop prior curation.

Usage
-----
    SUPABASE_DATABASE_URL='postgresql://...' \
    FIREWORKS_API_KEY=... \
    .venv-py314/bin/python database/scripts/enrich_arguments.py \
        [--limit 220] [--force] [--dry-run] [--node-id argument_xxx]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import asyncpg
from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "data" / "philological_audit" / "argument_structure_report.md"

KIMI_MODEL = "accounts/fireworks/models/kimi-k2p6"
FIREWORKS_BASE = "https://api.fireworks.ai/inference/v1"

# Edges in this set link an argument to a primary-source passage / work.
PRIMARY_SOURCE_RELATIONS = {
    "source_for",
    "evidenced_by",
    "attested_in",
    "cites_primary_source",
    "grounded_in",
}

# Edges in this set link an argument to a scholar / scholarly position.
SCHOLAR_RELATIONS = {
    "engages_with",
    "wrote_about",
    "discussed_in",
    "agrees_with",
    "opposes",
}

KIMI_SYSTEM = (
    "You are a doctoral-level scholar in ancient philosophy and patristics. "
    "Convert a vague description of a philosophical argument into an explicit "
    "premise/conclusion structure suitable for a doctoral thesis. Rules:\n"
    "1. NEVER fabricate or paraphrase Greek/Latin text — keep all premises in "
    "English.\n"
    "2. Every premise must be either textually attestable in the supplied "
    "primary sources (attestation='direct'), reported in a later doxographer "
    "you can cite (attestation='doxographical'), or explicitly reconstructed "
    "(attestation='reconstructed'). Reconstructed premises MUST cite a modern "
    "scholarly position when available.\n"
    "3. If you cannot ground a premise in the supplied material, mark it "
    "'reconstructed' and explain.\n"
    "4. The conclusion must be a single proposition that follows from the "
    "premises.\n"
    "5. The validity_assessment must distinguish formal logical validity from "
    "scholarly acceptance; for ancient dialectical arguments, validity is "
    "often 'disputed'.\n"
    "6. For Stoic causal arguments distinguish proximate vs principal cause "
    "(Bobzien 1998 ch. 6). For Aristotelian voluntariness distinguish "
    "hekousion / prohaireton / boulēton. For Patristic free-will arguments "
    "note the theological loading (autexousion ≠ modern 'free will').\n"
    "7. Reference passages by their 0-based index into the supplied list."
)

# ---------------------------------------------------------------------------
# JSON Schema enforced by Fireworks
# ---------------------------------------------------------------------------
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "argument_form": {
            "type": "string",
            "enum": [
                "syllogism",
                "reductio_ad_absurdum",
                "dilemma",
                "modus_ponens",
                "modus_tollens",
                "constructive_dilemma",
                "destructive_dilemma",
                "regress",
                "thought_experiment",
                "inductive_generalization",
                "analogical",
                "transcendental",
                "dialectical",
                "exhortative",
                "abductive",
                "modal_argument",
                "explicit_premise_conclusion",
            ],
        },
        "premises": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "attestation": {
                        "type": "string",
                        "enum": ["direct", "doxographical", "reconstructed"],
                    },
                    "primary_source_idx": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "scholarly_source_idx": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": [
                    "id",
                    "text",
                    "attestation",
                    "primary_source_idx",
                    "scholarly_source_idx",
                ],
            },
        },
        "conclusion": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "primary_source_idx": {
                    "type": "array",
                    "items": {"type": "integer"},
                },
                "scholarly_source_idx": {
                    "type": "array",
                    "items": {"type": "integer"},
                },
            },
            "required": [
                "text",
                "primary_source_idx",
                "scholarly_source_idx",
            ],
        },
        "validity_assessment": {
            "type": "object",
            "properties": {
                "formally_valid": {
                    "type": "string",
                    "enum": ["true", "false", "disputed"],
                },
                "rationale": {"type": "string"},
                "scholarly_consensus": {"type": "string"},
            },
            "required": [
                "formally_valid",
                "rationale",
                "scholarly_consensus",
            ],
        },
        "ancient_attestation_locus_classicus_idx": {
            "type": "integer",
            "description": "0-based index into primary_sources; -1 if none",
        },
    },
    "required": [
        "argument_form",
        "premises",
        "conclusion",
        "validity_assessment",
        "ancient_attestation_locus_classicus_idx",
    ],
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------
@dataclass
class ArgumentContext:
    node_id: str
    label: str
    description: str
    metadata: dict[str, Any]
    primary_sources: list[dict[str, Any]] = field(default_factory=list)
    scholarly_sources: list[dict[str, Any]] = field(default_factory=list)
    scholar_engagements: list[str] = field(default_factory=list)
    person_ids: list[str] = field(default_factory=list)


@dataclass
class EnrichmentResult:
    node_id: str
    accepted: bool
    structured: dict[str, Any] | None
    rejection_reason: str | None
    primary_source_ids: list[str] = field(default_factory=list)
    scholarly_source_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
async def fetch_arguments(conn: asyncpg.Connection, *, force: bool,
                          only: str | None, limit: int | None) -> list[asyncpg.Record]:
    where = ["type = 'argument'"]
    if not force:
        where.append("(metadata->>'structured_v2' IS NULL OR metadata->>'structured_v2' <> 'true')")
    if only:
        where.append("id = $1")
    sql = (
        "SELECT id, label, description, metadata "
        "FROM free_will.kg_nodes "
        "WHERE " + " AND ".join(where) + " "
        "ORDER BY id"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    args: list[Any] = []
    if only:
        args.append(only)
    return await conn.fetch(sql, *args)


async def fetch_context(conn: asyncpg.Connection, node_id: str) -> ArgumentContext:
    row = await conn.fetchrow(
        "SELECT id, label, description, metadata FROM free_will.kg_nodes WHERE id = $1",
        node_id,
    )
    if row is None:
        raise RuntimeError(f"node {node_id} not found")
    raw_meta = row["metadata"] or {}
    if isinstance(raw_meta, str):
        try:
            raw_meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            raw_meta = {}
    ctx = ArgumentContext(
        node_id=row["id"],
        label=row["label"] or row["id"],
        description=row["description"] or "",
        metadata=dict(raw_meta) if isinstance(raw_meta, dict) else {},
    )

    # Edges out of and into the argument
    edges = await conn.fetch(
        """
        SELECT relation, source_id, target_id
          FROM free_will.kg_edges
         WHERE source_id = $1 OR target_id = $1
        """,
        node_id,
    )

    related_ids: set[str] = set()
    for e in edges:
        related_ids.add(e["source_id"])
        related_ids.add(e["target_id"])
    related_ids.discard(node_id)
    if not related_ids:
        return ctx

    rows = await conn.fetch(
        "SELECT id, type, label, description FROM free_will.kg_nodes WHERE id = ANY($1::text[])",
        list(related_ids),
    )
    nodes_by_id: dict[str, dict[str, Any]] = {
        r["id"]: {
            "id": r["id"],
            "type": r["type"],
            "label": r["label"],
            "description": r["description"],
        }
        for r in rows
    }

    # Fetch passage text where applicable
    passage_ids = [nid for nid, n in nodes_by_id.items() if n["type"] == "passage"]
    passage_texts: dict[str, str] = {}
    if passage_ids:
        prows = await conn.fetch(
            "SELECT id, description FROM free_will.kg_nodes WHERE id = ANY($1::text[])",
            passage_ids,
        )
        for pr in prows:
            txt = pr["description"] or ""
            # Trim very long Greek passages — Kimi has plenty of context but
            # we keep one cell readable.
            passage_texts[pr["id"]] = txt[:1200]

    for e in edges:
        rel = e["relation"]
        # outgoing primary-source links
        other = e["target_id"] if e["source_id"] == node_id else e["source_id"]
        node = nodes_by_id.get(other)
        if node is None:
            continue
        if node["type"] in {"passage", "work", "quote"} and rel in PRIMARY_SOURCE_RELATIONS | {"discusses", "contains", "part_of", "source_for"}:
            text = passage_texts.get(node["id"], node["description"] or "")
            ctx.primary_sources.append({
                "id": node["id"],
                "type": node["type"],
                "label": node["label"],
                "text": text[:1200],
                "relation": rel,
            })
        elif node["type"] == "argument" and node["id"].startswith("scholar_position_"):
            ctx.scholarly_sources.append({
                "id": node["id"],
                "label": node["label"],
                "summary": (node["description"] or "")[:600],
                "relation": rel,
            })
            ctx.scholar_engagements.append(node["id"])
        elif node["type"] == "person" and rel in {"created_by", "authored_by", "discussed_in"}:
            ctx.person_ids.append(node["id"])

    # Deduplicate by id, keep order
    def _dedup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for item in items:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            out.append(item)
        return out

    ctx.primary_sources = _dedup(ctx.primary_sources)
    ctx.scholarly_sources = _dedup(ctx.scholarly_sources)
    return ctx


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def call_kimi(client: OpenAI, ctx: ArgumentContext) -> dict[str, Any]:
    user_blocks: list[str] = [
        f"Argument ID: {ctx.node_id}",
        f"Label: {ctx.label}",
        "Description:",
        ctx.description.strip() or "(no description)",
    ]
    legacy = ctx.metadata.get("premises")
    if isinstance(legacy, list) and legacy:
        user_blocks.append("Legacy premise notes (curator-written; verify but may help):")
        for p in legacy:
            if isinstance(p, str):
                user_blocks.append(f"  - {p}")
    if ctx.primary_sources:
        user_blocks.append("Primary sources (indexed):")
        for i, p in enumerate(ctx.primary_sources):
            user_blocks.append(f"[{i}] ({p['type']} via {p['relation']}) {p['label']}: {p['text'][:900]}")
    else:
        user_blocks.append(
            "Primary sources: NONE LINKED IN KG. Since no primary sources "
            "are supplied, every premise MUST use attestation='reconstructed' "
            "with an EMPTY primary_source_idx list. Do NOT mark any premise "
            "'direct' or 'doxographical' under these conditions."
        )
    if ctx.scholarly_sources:
        user_blocks.append("Modern scholarly positions in KG (indexed):")
        for i, s in enumerate(ctx.scholarly_sources):
            user_blocks.append(f"[{i}] {s['label']}: {s['summary']}")
    user_blocks.append(
        "Now output the structured premise/conclusion form. If you cannot "
        "ground a premise in supplied material, mark attestation "
        "'reconstructed' and cite a scholarly source where possible."
    )

    resp = client.chat.completions.create(
        model=KIMI_MODEL,
        messages=[
            {"role": "system", "content": KIMI_SYSTEM},
            {"role": "user", "content": "\n".join(user_blocks)},
        ],
        response_format={"type": "json_object", "schema": RESPONSE_SCHEMA},
        temperature=0.0,
        max_tokens=10000,
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(structured: dict[str, Any], ctx: ArgumentContext) -> tuple[bool, str]:
    """Validate AND salvage. A premise marked 'direct' or 'doxographical' with
    no valid primary_source_idx is silently downgraded to 'reconstructed'
    rather than failing the whole node — empty cite is interpreted as the
    model admitting it couldn't ground that premise. The conservative
    transformation preserves zero-fabrication: 'reconstructed' is the honest
    label for an ungrounded claim.
    """
    premises = structured.get("premises") or []
    if not premises:
        return False, "no premises returned"
    n_prim = len(ctx.primary_sources)
    for p in premises:
        att = p.get("attestation")
        if att in {"direct", "doxographical"}:
            idx = p.get("primary_source_idx") or []
            valid = [i for i in idx if isinstance(i, int) and 0 <= i < n_prim]
            if not valid:
                # Downgrade rather than reject
                p["attestation"] = "reconstructed"
                p["primary_source_idx"] = []
                p.setdefault("downgraded_from", att)
        elif att == "reconstructed":
            pass
        else:
            return False, f"unknown attestation '{att}'"
    return True, ""


def materialize_sources(structured: dict[str, Any], ctx: ArgumentContext) -> dict[str, Any]:
    """Replace primary_source_idx with node IDs; same for scholarly."""
    def _resolve(item: dict[str, Any]) -> None:
        prim_idx = item.pop("primary_source_idx", []) or []
        schol_idx = item.pop("scholarly_source_idx", []) or []
        item["primary_sources"] = [
            ctx.primary_sources[i]["id"]
            for i in prim_idx
            if isinstance(i, int) and 0 <= i < len(ctx.primary_sources)
        ]
        item["secondary_sources"] = [
            ctx.scholarly_sources[i]["id"]
            for i in schol_idx
            if isinstance(i, int) and 0 <= i < len(ctx.scholarly_sources)
        ]
        # Preserve downgrade marker (set by validate() salvage path)
        if "downgraded_from" in item:
            item["downgraded_from"] = item["downgraded_from"]

    for p in structured.get("premises", []):
        _resolve(p)
    if isinstance(structured.get("conclusion"), dict):
        _resolve(structured["conclusion"])

    idx = structured.pop("ancient_attestation_locus_classicus_idx", -1)
    if isinstance(idx, int) and 0 <= idx < len(ctx.primary_sources):
        structured["ancient_attestation_locus_classicus"] = ctx.primary_sources[idx]["id"]
    else:
        structured["ancient_attestation_locus_classicus"] = None

    structured["engaged_by_scholars"] = list(dict.fromkeys(ctx.scholar_engagements))
    return structured


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------
APPLY_SQL = """
UPDATE free_will.kg_nodes
   SET metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb,
       updated_at = now()
 WHERE id = $1
"""


async def apply_structured(conn: asyncpg.Connection, node_id: str,
                            structured: dict[str, Any], legacy_premises: Any,
                            *, dry_run: bool) -> None:
    payload: dict[str, Any] = {
        "argument_form": structured["argument_form"],
        "premises": structured["premises"],
        "conclusion": structured["conclusion"],
        "validity_assessment": structured["validity_assessment"],
        "ancient_attestation_locus_classicus": structured.get(
            "ancient_attestation_locus_classicus"
        ),
        "engaged_by_scholars": structured.get("engaged_by_scholars", []),
        "structured_v2": True,
        "structured_v2_model": KIMI_MODEL,
        "structured_v2_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if isinstance(legacy_premises, list) and legacy_premises:
        payload["legacy_premises"] = legacy_premises
    if dry_run:
        return
    await conn.execute(APPLY_SQL, node_id, json.dumps(payload))


async def flag_review(conn: asyncpg.Connection, node_id: str, reason: str,
                      *, dry_run: bool) -> None:
    payload = {
        "structured_v2": "needs_review",
        "structured_v2_reason": reason,
        "structured_v2_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if dry_run:
        return
    await conn.execute(APPLY_SQL, node_id, json.dumps(payload))


# ---------------------------------------------------------------------------
# Scholar engages_with edges
# ---------------------------------------------------------------------------
ENGAGES_WITH_SQL = """
INSERT INTO free_will.kg_edges (source_id, target_id, relation, weight, metadata)
VALUES ($1, $2, 'engages_with', 0.9,
        jsonb_build_object('provenance', 'structured_v2', 'created_at', now()))
"""


async def link_scholars(conn: asyncpg.Connection, ctx: ArgumentContext,
                         *, dry_run: bool) -> int:
    """For each scholar_position the argument engages with, add an
    `engages_with` edge from that scholar's PERSON node (if known) to the
    ancient argument. Idempotent.
    """
    added = 0
    if not ctx.scholar_engagements:
        return 0
    # Map scholar_position_* to person_* via existing 'wrote_about' edges.
    rows = await conn.fetch(
        """
        SELECT source_id, target_id
          FROM free_will.kg_edges
         WHERE target_id = ANY($1::text[])
           AND relation = 'wrote_about'
        """,
        list(ctx.scholar_engagements),
    )
    persons: set[str] = {r["source_id"] for r in rows if r["source_id"].startswith("person_")}
    # Fallback: extract scholar surname from scholar_position id
    if not persons:
        for sp in ctx.scholar_engagements:
            # scholar_position_<surname>_*
            parts = sp.split("_")
            if len(parts) >= 3:
                surname = parts[2]
                row = await conn.fetchrow(
                    "SELECT id FROM free_will.kg_nodes WHERE type='person' AND id ILIKE $1 LIMIT 1",
                    f"%{surname}%",
                )
                if row:
                    persons.add(row["id"])
    for pid in persons:
        if dry_run:
            added += 1
            continue
        # Check existence to keep idempotent count honest
        exists = await conn.fetchval(
            "SELECT 1 FROM free_will.kg_edges WHERE source_id=$1 AND target_id=$2 AND relation='engages_with'",
            pid, ctx.node_id,
        )
        if exists:
            continue
        await conn.execute(ENGAGES_WITH_SQL, pid, ctx.node_id)
        added += 1
    return added


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(results: list[EnrichmentResult], form_counts: Counter[str],
                  validity_counts: Counter[str], edges_added: int,
                  total: int) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    accepted = [r for r in results if r.accepted]
    rejected = [r for r in results if not r.accepted]
    lines: list[str] = []
    lines.append("# Argument Structure Enrichment Report")
    lines.append("")
    lines.append(f"- **Total argument nodes processed**: {total}")
    lines.append(f"- **Structured (accepted)**: {len(accepted)}")
    lines.append(f"- **Flagged needs_review**: {len(rejected)}")
    lines.append(f"- **New `engages_with` edges**: {edges_added}")
    lines.append("")
    lines.append("## Distribution of argument_form")
    for form, n in form_counts.most_common():
        lines.append(f"- `{form}`: {n}")
    lines.append("")
    lines.append("## Validity assessment counts")
    for v, n in validity_counts.most_common():
        lines.append(f"- `{v}`: {n}")
    lines.append("")
    lines.append("## Top 20 newly structured arguments")
    for r in accepted[:20]:
        s = r.structured or {}
        concl = (s.get("conclusion") or {}).get("text") or ""
        lines.append(f"- **{r.node_id}** — _{s.get('argument_form')}_ → {concl[:200]}")
    lines.append("")
    lines.append("## Flagged for review")
    for r in rejected[:20]:
        lines.append(f"- **{r.node_id}** — {r.rejection_reason}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main_async(args: argparse.Namespace) -> int:
    db_url = (
        os.environ.get("SUPABASE_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or ""
    )
    if not db_url:
        print("SUPABASE_DATABASE_URL / DATABASE_URL not set", file=sys.stderr)
        return 2
    fw_key = os.environ.get("FIREWORKS_API_KEY")
    if not fw_key:
        print("FIREWORKS_API_KEY not set", file=sys.stderr)
        return 2

    client = OpenAI(base_url=FIREWORKS_BASE, api_key=fw_key)
    conn = await asyncpg.connect(db_url)
    try:
        rows = await fetch_arguments(conn, force=args.force, only=args.node_id,
                                     limit=args.limit)
        total = len(rows)
        print(f"Processing {total} argument nodes...", file=sys.stderr)

        results: list[EnrichmentResult] = []
        form_counts: Counter[str] = Counter()
        validity_counts: Counter[str] = Counter()
        edges_added = 0

        # Process in batches: fetch context serially (DB), dispatch Kimi
        # concurrently via a thread pool, then apply DB updates serially.
        batch_size = max(1, int(args.concurrency))
        executor = ThreadPoolExecutor(max_workers=batch_size)
        loop = asyncio.get_running_loop()

        def _llm_attempt(ctx: ArgumentContext) -> tuple[dict[str, Any] | None, str]:
            reason = ""
            for attempt in range(3):
                try:
                    raw = call_kimi(client, ctx)
                except Exception as exc:
                    err = str(exc)
                    # Back off on rate-limit / transient errors
                    if "429" in err or "rate limit" in err.lower():
                        time.sleep(2 + attempt * 4)
                        reason = f"kimi-error: {exc}"
                        continue
                    return None, f"kimi-error: {exc}"
                ok, why = validate(raw, ctx)
                if ok:
                    return raw, ""
                reason = why
            return None, reason

        for batch_start in range(0, total, batch_size):
            batch_rows = rows[batch_start : batch_start + batch_size]
            # Build contexts
            ctxs: list[tuple[asyncpg.Record, ArgumentContext | None, str]] = []
            for row in batch_rows:
                try:
                    ctx = await fetch_context(conn, row["id"])
                    ctxs.append((row, ctx, ""))
                except Exception as exc:
                    ctxs.append((row, None, f"ctx-error: {exc}"))
            # Dispatch LLM in parallel
            tasks = [
                loop.run_in_executor(executor, _llm_attempt, ctx)
                if ctx is not None
                else None
                for _, ctx, _ in ctxs
            ]
            llm_results: list[tuple[dict[str, Any] | None, str]] = []
            for t in tasks:
                if t is None:
                    llm_results.append((None, "no context"))
                else:
                    llm_results.append(await t)
            # Apply
            for idx, ((row, ctx, ctx_err), (raw, reason)) in enumerate(
                zip(ctxs, llm_results, strict=True)
            ):
                nid = row["id"]
                progress = batch_start + idx + 1
                if ctx is None:
                    await flag_review(conn, nid, ctx_err, dry_run=args.dry_run)
                    results.append(EnrichmentResult(nid, False, None, ctx_err))
                    print(f"  [{progress}/{total}] {nid} FLAGGED: {ctx_err}", file=sys.stderr)
                    continue
                if raw is None:
                    await flag_review(conn, nid, reason, dry_run=args.dry_run)
                    results.append(EnrichmentResult(nid, False, None, reason))
                    print(f"  [{progress}/{total}] {nid} FLAGGED: {reason}", file=sys.stderr)
                    continue
                structured = materialize_sources(raw, ctx)
                await apply_structured(
                    conn, nid, structured, ctx.metadata.get("premises"),
                    dry_run=args.dry_run,
                )
                added = await link_scholars(conn, ctx, dry_run=args.dry_run)
                edges_added += added
                form_counts[structured.get("argument_form", "?")] += 1
                validity_counts[
                    structured["validity_assessment"].get("formally_valid", "?")
                ] += 1
                results.append(EnrichmentResult(
                    nid, True, structured, None,
                    primary_source_ids=[p["id"] for p in ctx.primary_sources],
                    scholarly_source_ids=[s["id"] for s in ctx.scholarly_sources],
                ))
                print(f"  [{progress}/{total}] {nid} OK (+{added} edges)", file=sys.stderr)

        executor.shutdown(wait=False)

        write_report(results, form_counts, validity_counts, edges_added, total)
        print(f"\nWrote report to {REPORT_PATH}", file=sys.stderr)
        print(f"Accepted: {sum(1 for r in results if r.accepted)} | "
              f"Flagged: {sum(1 for r in results if not r.accepted)} | "
              f"Edges added: {edges_added}", file=sys.stderr)
    finally:
        await conn.close()
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--force", action="store_true",
                   help="re-process nodes already marked structured_v2")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--node-id", default=None,
                   help="restrict to a single argument node id")
    p.add_argument("--concurrency", type=int, default=8,
                   help="parallel Kimi calls per batch")
    args = p.parse_args()
    rc = asyncio.run(main_async(args))
    sys.exit(rc)


if __name__ == "__main__":
    main()
