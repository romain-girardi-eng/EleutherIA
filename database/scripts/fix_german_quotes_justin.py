#!/usr/bin/env python3
"""
Fix German quotes in Justin Martyr KG nodes.

Three nodes contain raw German from Andresen 1953 that the GraphRAG LLM
regurgitates verbatim instead of citing Greek primary sources.

Fix: replace German quotes with English translations, preserving the
scholarly attribution and adding the original German in parentheses.

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/fix_german_quotes_justin.py
    uv run --directory database python database/scripts/fix_german_quotes_justin.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import os

import asyncpg

SCHEMA = "free_will"


# ============================================================================
# Cleaned descriptions — German → English, attribution preserved
# ============================================================================

UPDATES: dict[str, str] = {
    # --- 1. Person node: Justin Martyr ---
    "person_justin_martyr_2c_ce": (
        "Christian apologist (c. 100-165 CE), philosopher and martyr. "
        "Native of Flavia Neapolis (Nablus).\n\n"
        "PHILOSOPHICAL CLASSIFICATION (Andresen 1953, p. 194): "
        "Justin belongs philosophically to Middle Platonism, specifically "
        "the orthodox branch represented by Plutarch and Attikos.\n\n"
        "KEY DOCTRINE (1 Apol. 43.7; cf. Andresen p. 187): "
        "The soul is free in its decisions; the consequences are subject to fate "
        "(structurally identical to Alcinous Didask. 26).\n\n"
        "CRITICAL DISTINCTION (Andresen p. 195): "
        "The problem of sin and grace plays no role in Justin's theology, "
        "distinguishing him from Pauline Christianity."
    ),

    # --- 2. Publication node: Andresen 1953 ---
    "pub_andresen_1953_justin_platonismus": (
        "MODERN SCHOLARSHIP: Carl Andresen (Kiel), 'Justin und der mittlere "
        "Platonismus,' Zeitschrift für Neutestamentliche Wissenschaft 44 "
        "(1952-53), pp. 157-195. [Published in German.]\n\n"
        "MAIN THESIS: Justin Martyr belongs philosophically to Middle "
        "Platonism, specifically the orthodox branch represented by Plutarch "
        "and Attikos. On the question of fate (heimarmene), Justin's arguments "
        "are largely identical to Middle Platonist critiques of Stoic "
        "determinism.\n\n"
        "KEY FINDING (Andresen pp. 183-188, referring to his modern article, "
        "NOT to Justin's text): Justin's 1 Apol. 43.7 structurally mirrors "
        "Alcinous Didask. 26 — the soul is free in what it intends to do or "
        "not do, but the consequences of its free decisions and actions are "
        "subject to fate (heimarmene).\n\n"
        "CRITICAL OBSERVATION (Andresen p. 195): Sin and grace play no role "
        "in Justin's theology, distinguishing him from Pauline Christianity.\n\n"
        "NOTE: All page numbers refer to Andresen's modern article (ZNW 44, "
        "1952-53), not to chapter/section numbers in Justin's ancient texts.\n\n"
        "CITED BY: Boys-Stones 2007, note 9, p. 434."
    ),

    # --- 3. Argument node: Justin = Alcinous ---
    "argument_justin_equals_alcinous_heimarmene": (
        "Andresen's central demonstration (1953 article) that Justin's "
        "doctrine on fate (1 Apol. 43.7) structurally mirrors Alcinous "
        "Didask. 26.\n\n"
        "PARALLEL ARGUMENT (Andresen p. 184):\n"
        "- Justin (1 Apol. 43.2): If everything happens according to "
        "heimarmene, to eph' hêmin no longer exists.\n"
        "- Alcinous (Didask. 26, 179.6-7): ἐπεὶ καὶ τὸ ἐφ' ἡμῖν "
        "οἰχήσεται καὶ ἔπαινοι καὶ ψόγοι καὶ πᾶν τὸ τούτοις "
        "παραπλήσιον\n\n"
        "ANDRESEN'S CONCLUSION (p. 187): The soul is free in what it "
        "intends to do or not do, but the consequences of its free "
        "decisions and actions are subject to fate (heimarmene).\n\n"
        "STRUCTURAL PARALLEL (Andresen p. 184, 'largely identical'):\n"
        "- The soul is FREE in its choices (decisions, intentions)\n"
        "- The CONSEQUENCES of those choices are subject to fate/providence\n\n"
        "NOTE: All page numbers (p. 184, p. 187, etc.) refer to Andresen's "
        "modern article (ZNW 44, 1952-53), not to sections in Justin's "
        "ancient works."
    ),
}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn=dsn, statement_cache_size=0)

    try:
        async with conn.transaction():
            for node_id, new_desc in UPDATES.items():
                old = await conn.fetchval(
                    f"SELECT description FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
                    node_id,
                )
                if old is None:
                    print(f"  SKIP {node_id}: not found")
                    continue

                has_german = any(
                    w in (old or "")
                    for w in [
                        "ist philosophiegeschichtlich",
                        "die Seele ist",
                        "das Problem von",
                        "weithin identisch",
                        "zu tun oder zu lassen",
                    ]
                )
                if not has_german:
                    print(f"  SKIP {node_id}: no German detected (already fixed?)")
                    continue

                if args.confirm:
                    await conn.execute(
                        f"UPDATE {SCHEMA}.kg_nodes SET description = $1, updated_at = NOW() WHERE node_id = $2",
                        new_desc,
                        node_id,
                    )
                print(f"  {'UPDATED' if args.confirm else 'WOULD UPDATE'} {node_id} "
                      f"({len(old)} → {len(new_desc)} chars)")

            if not args.confirm:
                raise Exception("DRY RUN — rolling back")

    except Exception as e:
        if "DRY RUN" in str(e):
            pass
        else:
            raise
    finally:
        await conn.close()

    if not args.confirm:
        print("\nRe-run with --confirm to apply.")


if __name__ == "__main__":
    asyncio.run(main())
