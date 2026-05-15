"""
Share routes — create and render read-only public share links for query traces.

POST /api/graphrag/query/{trace_id}/share   — JWT-authenticated, owner-only
GET  /share/{token}                         — no auth, returns read-only HTML
"""

from __future__ import annotations

import html
import logging
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from backend.dependencies import get_db
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])
# Separate router for the public /share/{token} endpoint (no /api prefix)
public_router = APIRouter(tags=["share"])

_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL", "https://free-will.app"
).rstrip("/")
_SHARE_TTL_DAYS = 30


# ---------------------------------------------------------------------------
# POST /api/graphrag/query/{trace_id}/share
# ---------------------------------------------------------------------------


@router.post("/query/{trace_id}/share")
async def create_share_link(
    trace_id: str,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> JSONResponse:
    """Create a 30-day read-only share link for a trace.  Owner-only."""
    try:
        trace_uuid = uuid.UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trace_id format") from None

    user_id = current_user["user_id"]

    # Verify the trace exists and belongs to the caller
    row = await db.fetchrow(
        """
        SELECT trace_id, user_id
        FROM free_will.query_traces
        WHERE trace_id = $1
        """,
        trace_uuid,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    if row.get("user_id") and str(row["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Not the owner of this trace")

    token = secrets.token_hex(32)  # 64 hex chars
    expires_at = datetime.now(UTC) + timedelta(days=_SHARE_TTL_DAYS)

    await db.execute(
        """
        INSERT INTO free_will.shared_traces
            (token, trace_id, created_by, expires_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (token) DO NOTHING
        """,
        token,
        trace_uuid,
        uuid.UUID(user_id),
        expires_at,
    )

    share_url = f"{_BASE_URL}/share/{token}"
    return JSONResponse(
        {"share_url": share_url, "expires_at": expires_at.isoformat()},
        status_code=201,
    )


# ---------------------------------------------------------------------------
# GET /share/{token}
# ---------------------------------------------------------------------------


@public_router.get("/share/{token}", response_class=HTMLResponse, include_in_schema=False)
async def render_shared_trace(
    token: str,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> HTMLResponse:
    """Render a read-only HTML page for a shared trace.  No authentication."""
    row = await db.fetchrow(
        """
        SELECT st.token, st.expires_at, st.view_count,
               qt.query, qt.final_answer_text, qt.final_answer_citations,
               qt.started_at, qt.completed_at, qt.mode
        FROM free_will.shared_traces st
        JOIN free_will.query_traces qt USING (trace_id)
        WHERE st.token = $1
        """,
        token,
    )

    if not row:
        return HTMLResponse(_error_page("Ce lien n'existe pas ou a expiré."), status_code=404)

    expires_at: datetime = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return HTMLResponse(_error_page("Ce lien de partage a expiré."), status_code=410)

    # Increment view counter (non-fatal)
    try:
        await db.execute(
            """
            UPDATE free_will.shared_traces
            SET view_count = view_count + 1,
                last_viewed_at = now()
            WHERE token = $1
            """,
            token,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Could not increment view_count for token %s", token)

    query = row.get("query") or ""
    answer = row.get("final_answer_text") or ""
    citations_raw = row.get("final_answer_citations") or []
    started_at = row.get("started_at")

    return HTMLResponse(_render_page(query, answer, citations_raw, started_at))


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------


def _render_page(
    query: str,
    answer: str,
    citations: list[Any],
    started_at: datetime | None,
) -> str:
    date_str = started_at.strftime("%Y-%m-%d") if started_at else ""
    q_escaped = html.escape(query)
    a_escaped = html.escape(answer).replace("\n", "<br>")

    citation_rows = ""
    for i, c in enumerate(citations or [], start=1):
        if isinstance(c, dict):
            label = html.escape(c.get("work_label") or c.get("passage_id") or "")
            urn = html.escape(c.get("cts_urn") or "")
            excerpt = html.escape(c.get("excerpt") or "")
            citation_rows += (
                f'<li class="citation"><span class="cnum">[{i}]</span> '
                f'<strong>{label}</strong>'
                + (f' <code class="urn">{urn}</code>' if urn else "")
                + (f'<br><em class="excerpt">{excerpt}</em>' if excerpt else "")
                + "</li>\n"
            )

    citations_section = (
        f'<section class="citations"><h2>Sources</h2><ol>{citation_rows}</ol></section>'
        if citation_rows
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EleutherIA — {q_escaped}</title>
<style>
  :root{{--amber:#d97706;--stone:#292524;--bg:#fafaf9;--border:#e7e5e4}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Georgia',serif;background:var(--bg);color:var(--stone);line-height:1.7;padding:2rem 1rem}}
  .wrap{{max-width:800px;margin:0 auto}}
  header{{border-bottom:2px solid var(--amber);padding-bottom:1rem;margin-bottom:2rem}}
  .logo{{font-size:1.1rem;font-weight:700;color:var(--amber);letter-spacing:.08em;text-transform:uppercase}}
  .badge{{font-size:.75rem;color:#78716c;margin-top:.25rem}}
  h1{{font-size:1.35rem;line-height:1.4;margin-bottom:1.5rem;color:var(--stone)}}
  .answer{{background:#fff;border:1px solid var(--border);border-radius:.75rem;padding:1.5rem;margin-bottom:2rem;white-space:pre-wrap}}
  .citations{{margin-bottom:2rem}}
  .citations h2{{font-size:1rem;text-transform:uppercase;letter-spacing:.1em;color:#78716c;margin-bottom:.75rem}}
  ol{{padding-left:0;list-style:none}}
  .citation{{padding:.5rem 0;border-bottom:1px solid var(--border);font-size:.9rem}}
  .cnum{{color:var(--amber);font-weight:700;margin-right:.4rem}}
  .urn{{font-size:.75rem;color:#a8a29e;background:#f5f5f4;padding:.1rem .3rem;border-radius:.2rem}}
  .excerpt{{color:#57534e;font-size:.85rem;display:block;margin-top:.25rem}}
  footer{{font-size:.75rem;color:#a8a29e;text-align:center;border-top:1px solid var(--border);padding-top:1rem}}
  a{{color:var(--amber)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">EleutherIA</div>
    <div class="badge">Résultat de recherche partagé{' — ' + date_str if date_str else ''}</div>
  </header>
  <h1>{q_escaped}</h1>
  <section class="answer">{a_escaped}</section>
  {citations_section}
  <footer>Généré par <a href="https://free-will.app">EleutherIA</a> · CC BY 4.0</footer>
</div>
</body>
</html>"""


def _error_page(message: str) -> str:
    msg = html.escape(message)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>EleutherIA — Lien invalide</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#fafaf9;color:#292524}}
.box{{text-align:center;max-width:400px}}h1{{color:#d97706;margin-bottom:1rem}}a{{color:#d97706}}</style>
</head>
<body><div class="box"><h1>Lien invalide</h1><p>{msg}</p><br>
<a href="https://free-will.app">← Retour à EleutherIA</a></div></body></html>"""
