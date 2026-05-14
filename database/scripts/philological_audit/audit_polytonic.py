"""Audit Greek text on KG nodes for polytonic-diacritic discipline.

Checks performed on every node whose ``description``, ``label`` or
``metadata`` value contains Greek codepoints:

1. **NFC normalization**  -- if a string is not in NFC form, the
   suggested fix is the NFC-normalized version. Applied automatically
   (no scholarly judgement required).
2. **Diacritic presence** -- strings of >= 6 Greek characters with
   *zero* combining diacritics AND zero precomposed polytonic blocks
   are flagged ``metadata.diacritics_missing = true``. We never
   reconstruct -- only flag.
3. **Backslash escape artifacts** -- legacy importers left
   ``Greek\\ Greek`` patterns where a backslash precedes a space
   (caused by mis-escaped LaTeX-like markers). When the artifact is
   purely cosmetic (a single backslash-space following a Greek word)
   we strip it. Cases with multiple backslashes are deferred.
4. **Final sigma discipline** -- words ending in non-final sigma
   (``σ``) at a wordbreak are flagged; replacement to ``ς`` is
   suggested but flagged ``auto_apply=false`` because mid-word edits
   require seeing the boundary explicitly.

The script is a *read-only* report by default. Pass ``--apply`` to
write the auto-apply rows back to the DB.

Zero fabrication policy: NEVER fabricate polytonic forms from training
memory. The only mechanical fix we apply is unicode normalization.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import unicodedata
from typing import Any

import asyncpg
from _common import REPORTS_DIR, connect, emit_summary, normalize_meta, write_jsonl

GREEK_RANGE = re.compile(r"[Ͱ-Ͽἀ-῾]")
COMBINING_DIACRITIC = re.compile(r"[̀-ͯ]")
PRECOMPOSED_POLYTONIC = re.compile(r"[ἀ-῾]")
BACKSLASH_ARTIFACT = re.compile(r"([Ͱ-Ͽἀ-῾])\\(?=\s|$)")
NON_FINAL_SIGMA_AT_END = re.compile(r"σ(?=\s|[.,·;:!?\)\]\}»”]|$)")


def has_greek(text: str) -> bool:
    return bool(GREEK_RANGE.search(text))


def diacritic_count(text: str) -> int:
    decomposed = unicodedata.normalize("NFD", text)
    return len(COMBINING_DIACRITIC.findall(decomposed))


def precomposed_polytonic_count(text: str) -> int:
    return len(PRECOMPOSED_POLYTONIC.findall(text))


def greek_char_count(text: str) -> int:
    return len(GREEK_RANGE.findall(text))


def strip_backslash_artifacts(text: str) -> str:
    return BACKSLASH_ARTIFACT.sub(r"\1", text)


async def audit(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT node_id, type, label, description, metadata
          FROM free_will.kg_nodes
         WHERE label ~ '[Ͱ-Ͽἀ-῾]'
            OR description ~ '[Ͱ-Ͽἀ-῾]'
            OR metadata::text ~ '[Ͱ-Ͽἀ-῾]'
        """
    )

    findings: list[dict[str, Any]] = []
    for row in rows:
        node_id = row["node_id"]
        node_type = row["type"]
        for field in ("label", "description"):
            text = row[field]
            if not text or not has_greek(text):
                continue
            findings.extend(_audit_text(node_id, node_type, field, text))

        metadata = normalize_meta(row["metadata"])
        for key, value in metadata.items():
            if isinstance(value, str) and has_greek(value):
                findings.extend(
                    _audit_text(node_id, node_type, f"metadata.{key}", value)
                )

    return findings


def _audit_text(
    node_id: str, node_type: str, field: str, text: str
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    nfc = unicodedata.normalize("NFC", text)
    if nfc != text:
        found.append(
            {
                "node_id": node_id,
                "node_type": node_type,
                "dimension": "polytonic",
                "field": field,
                "issue": "not_in_nfc",
                "current_excerpt": text[:160],
                "suggested_fix": {"replace_with": nfc},
                "confidence": 1.0,
                "auto_apply": True,
            }
        )

    greek_chars = greek_char_count(text)
    diacritics = diacritic_count(text)
    polytonic = precomposed_polytonic_count(text)
    if greek_chars >= 6 and diacritics == 0 and polytonic == 0:
        found.append(
            {
                "node_id": node_id,
                "node_type": node_type,
                "dimension": "polytonic",
                "field": field,
                "issue": "no_diacritics_on_substantial_greek",
                "current_excerpt": text[:160],
                "suggested_fix": {"flag_metadata": "diacritics_missing"},
                "confidence": 0.8,
                "auto_apply": False,
            }
        )

    if BACKSLASH_ARTIFACT.search(text):
        cleaned = strip_backslash_artifacts(text)
        if cleaned != text:
            found.append(
                {
                    "node_id": node_id,
                    "node_type": node_type,
                    "dimension": "polytonic",
                    "field": field,
                    "issue": "backslash_escape_artifact",
                    "current_excerpt": text[:160],
                    "suggested_fix": {"replace_with": cleaned},
                    "confidence": 0.95,
                    "auto_apply": True,
                }
            )

    if NON_FINAL_SIGMA_AT_END.search(text):
        found.append(
            {
                "node_id": node_id,
                "node_type": node_type,
                "dimension": "polytonic",
                "field": field,
                "issue": "non_final_sigma_at_wordbreak",
                "current_excerpt": text[:160],
                "suggested_fix": {"note": "replace word-final σ with ς"},
                "confidence": 0.85,
                "auto_apply": False,
            }
        )

    return found


async def apply_fixes(conn: asyncpg.Connection, findings: list[dict[str, Any]]) -> int:
    applied = 0
    by_node: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        if not f.get("auto_apply"):
            continue
        by_node.setdefault(f["node_id"], []).append(f)

    if not by_node:
        return 0

    rows = await conn.fetch(
        "SELECT node_id, label, description, metadata FROM free_will.kg_nodes "
        "WHERE node_id = ANY($1::text[])",
        list(by_node.keys()),
    )

    for row in rows:
        node_id = row["node_id"]
        label = row["label"]
        description = row["description"]
        metadata = normalize_meta(row["metadata"])
        dirty_fields = {"label": False, "description": False, "metadata": False}

        for f in by_node[node_id]:
            field = f["field"]
            fix = f["suggested_fix"]
            replacement = fix.get("replace_with")
            if replacement is None:
                continue
            if field == "label":
                label = replacement
                dirty_fields["label"] = True
            elif field == "description":
                description = replacement
                dirty_fields["description"] = True
            elif field.startswith("metadata."):
                key = field[len("metadata.") :]
                if isinstance(metadata.get(key), str):
                    metadata[key] = replacement
                    dirty_fields["metadata"] = True

        if not any(dirty_fields.values()):
            continue

        await conn.execute(
            """
            UPDATE free_will.kg_nodes
               SET label = $2,
                   description = $3,
                   metadata = $4::jsonb,
                   updated_at = now()
             WHERE node_id = $1
            """,
            node_id,
            label,
            description,
            json.dumps(metadata, ensure_ascii=False),
        )
        applied += 1
    return applied


async def amain(args: argparse.Namespace) -> int:
    conn = await connect()
    try:
        findings = await audit(conn)
        report_path = REPORTS_DIR / "polytonic_report.jsonl"
        write_jsonl(findings, report_path)

        by_issue: dict[str, int] = {}
        auto = 0
        for f in findings:
            by_issue[f["issue"]] = by_issue.get(f["issue"], 0) + 1
            if f["auto_apply"]:
                auto += 1
        counts = {
            "total_findings": len(findings),
            "auto_apply_pending": auto,
            **{f"issue.{k}": v for k, v in sorted(by_issue.items())},
        }
        emit_summary("polytonic", counts)
        print(f"[polytonic] wrote {report_path}", file=sys.stderr)

        if args.apply:
            applied = await apply_fixes(conn, findings)
            print(f"[polytonic] applied {applied} nodes", file=sys.stderr)
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit polytonic Greek discipline")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
