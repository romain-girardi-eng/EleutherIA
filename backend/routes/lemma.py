"""
Lemma intelligence routes — dictionary lookup, corpus stats, co-occurrences, KG connections.

Queries the existing passages/oga_tokens tables and the knowledge graph.
No new services needed — all SQL-based.
"""

import logging
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_db
from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["lemma"])


@router.get("/dictionary/{lemma}")
async def get_lemma_dictionary(
    lemma: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str = Query("grc", description="Language: grc or lat"),
) -> dict[str, Any]:
    """
    Look up a lemma in the corpus (mimics LSJ/Lewis & Short dictionary lookup).

    Returns definition-like data from the corpus — occurrence counts,
    common forms, and external links to Logeion and Perseus.
    """
    # Find the lemma in OGA tokens
    row = await db.fetchrow(
        """
        SELECT
            t.lemma, t.pos,
            w.language,
            COUNT(*) as occurrences,
            COUNT(DISTINCT t.work_id) as work_count
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        GROUP BY t.lemma, t.pos, w.language
        LIMIT 1
        """,
        lemma, language,
    )

    if not row:
        encoded = quote(lemma, safe="")
        return {
            "found": False,
            "language": language,
            "lemma": lemma,
            "message": "Lemma not found in corpus",
            "external_links": {
                "logeion": f"https://logeion.uchicago.edu/{encoded}",
            },
        }

    # Get surface forms
    forms_rows = await db.fetch(
        """
        SELECT DISTINCT surface_form
        FROM free_will.oga_tokens
        WHERE lemma = $1
        LIMIT 20
        """,
        lemma,
    )
    forms = [r["surface_form"] for r in forms_rows]

    encoded = quote(lemma, safe="")
    dict_name = "LSJ" if language == "grc" else "Lewis & Short"

    return {
        "found": True,
        "language": language,
        "dictionary": dict_name,
        "lemma": lemma,
        "lemma_latin": _greek_to_latin(lemma) if language == "grc" else lemma,
        "short_def": f"{row['occurrences']} occurrences across {row['work_count']} works",
        "forms": forms,
        "greek_forms": forms if language == "grc" else [],
        "external_links": {
            "logeion": f"https://logeion.uchicago.edu/{encoded}",
            "perseus": f"https://www.perseus.tufts.edu/hopper/morph?l={encoded}&la={'greek' if language == 'grc' else 'latin'}",
        },
    }


@router.get("/dictionary/search/{query}")
async def search_lemma_dictionary(
    query: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str = Query("grc"),
    limit: int = Query(20, ge=1, le=100),
    fuzzy: bool = Query(False),
) -> dict[str, Any]:
    """Search dictionary entries by prefix or fuzzy match."""
    if fuzzy:
        pattern_sql = "t.lemma ILIKE '%' || $1 || '%'"
    else:
        pattern_sql = "t.lemma ILIKE $1 || '%'"

    rows = await db.fetch(
        f"""
        SELECT
            t.lemma,
            t.pos,
            COUNT(*) as count
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE {pattern_sql}
          AND w.language = $2
          AND t.lemma IS NOT NULL
        GROUP BY t.lemma, t.pos
        ORDER BY COUNT(*) DESC
        LIMIT $3
        """,
        query, language, limit,
    )

    results = []
    for r in rows:
        results.append({
            "lemma": r["lemma"],
            "lemma_latin": _greek_to_latin(r["lemma"]) if language == "grc" else r["lemma"],
            "short_def": f"{r['count']} occurrences",
        })

    return {
        "query": query,
        "language": language,
        "fuzzy": fuzzy,
        "results": results,
        "count": len(results),
    }


@router.get("/stats/{lemma}")
async def get_lemma_stats(
    lemma: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str = Query("grc"),
) -> dict[str, Any]:
    """Get corpus statistics for a lemma — occurrences, distribution by author/work/period."""
    # Total occurrences
    total = await db.fetchval(
        """
        SELECT COUNT(*) FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        """,
        lemma, language,
    )

    # Passage count (unique works)
    passage_count = await db.fetchval(
        """
        SELECT COUNT(DISTINCT t.work_id)
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        """,
        lemma, language,
    )

    # By author
    by_author = await db.fetch(
        """
        SELECT w.author, COUNT(DISTINCT t.work_id) as passages
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        GROUP BY w.author ORDER BY passages DESC LIMIT 20
        """,
        lemma, language,
    )

    # By work
    by_work = await db.fetch(
        """
        SELECT w.author, w.title, COUNT(*) as passages
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        GROUP BY w.author, w.title ORDER BY passages DESC LIMIT 20
        """,
        lemma, language,
    )

    # By period
    by_period = await db.fetch(
        """
        SELECT w.period, COUNT(DISTINCT t.work_id) as passages
        FROM free_will.oga_tokens t
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2 AND w.period IS NOT NULL
        GROUP BY w.period ORDER BY passages DESC
        """,
        lemma, language,
    )

    return {
        "lemma": lemma,
        "language": language,
        "total_occurrences": int(total or 0),
        "passage_count": int(passage_count or 0),
        "by_author": [dict(r) for r in by_author],
        "by_work": [dict(r) for r in by_work],
        "by_period": [dict(r) for r in by_period],
    }


@router.get("/related/{lemma}")
async def get_related_lemmas(
    lemma: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str = Query("grc"),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get lemmas that frequently co-occur with the given lemma (same work)."""
    rows = await db.fetch(
        """
        SELECT t2.lemma, t2.pos, COUNT(*) as cooccurrences
        FROM free_will.oga_tokens t1
        JOIN free_will.oga_tokens t2
            ON t1.work_id = t2.work_id
            AND t2.lemma != $1
            AND t2.lemma IS NOT NULL
        JOIN free_will.ancient_works w ON t1.work_id = w.work_id
        WHERE t1.lemma = $1 AND w.language = $2
        GROUP BY t2.lemma, t2.pos
        ORDER BY cooccurrences DESC
        LIMIT $3
        """,
        lemma, language, limit,
    )

    return {
        "lemma": lemma,
        "language": language,
        "related": [dict(r) for r in rows],
    }


@router.get("/kg-connections/{lemma}")
async def get_lemma_kg_connections(
    lemma: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    language: str = Query("grc"),
) -> dict[str, Any]:
    """Find KG nodes related to a lemma via passage citations."""
    rows = await db.fetch(
        """
        SELECT DISTINCT
            n.node_id, n.label, n.type, n.description
        FROM free_will.oga_tokens t
        JOIN free_will.passages p ON t.work_id = p.work_id
        JOIN free_will.passage_citations pc ON p.passage_id = pc.passage_id
        JOIN free_will.kg_nodes n ON pc.kg_node_id = n.node_id
        JOIN free_will.ancient_works w ON t.work_id = w.work_id
        WHERE t.lemma = $1 AND w.language = $2
        LIMIT 20
        """,
        lemma, language,
    )

    return {
        "lemma": lemma,
        "language": language,
        "kg_nodes": [dict(r) for r in rows],
    }


# ---------- Helpers ----------

_GREEK_TO_LATIN: dict[str, str] = {
    "\u03b1": "a", "\u03b2": "b", "\u03b3": "g", "\u03b4": "d",
    "\u03b5": "e", "\u03b6": "z", "\u03b7": "h", "\u03b8": "q",
    "\u03b9": "i", "\u03ba": "k", "\u03bb": "l", "\u03bc": "m",
    "\u03bd": "n", "\u03be": "x", "\u03bf": "o", "\u03c0": "p",
    "\u03c1": "r", "\u03c3": "s", "\u03c4": "t", "\u03c5": "u",
    "\u03c6": "f", "\u03c7": "c", "\u03c8": "y", "\u03c9": "w",
    "\u03c2": "s",  # final sigma
}


def _greek_to_latin(text: str) -> str:
    return "".join(_GREEK_TO_LATIN.get(c, c) for c in text.lower())
