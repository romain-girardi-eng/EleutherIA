"""
Share routes — create and render read-only public share links for query traces.

POST /api/graphrag/query/{trace_id}/share   — JWT-authenticated, owner-only
GET  /share/{token}                         — no auth, returns read-only HTML
"""

from __future__ import annotations

import html
import json
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

_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://free-will.app").rstrip("/")
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
    # Anonymous traces have no accountable owner and must never be claimable
    # merely by knowing/guessing their UUID.  Publication is explicit and
    # owner-only; the separate public-gallery flag is not a sharing shortcut.
    if not row.get("user_id") or str(row["user_id"]) != str(user_id):
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


@public_router.get(
    "/share/{token}", response_class=HTMLResponse, include_in_schema=False
)
async def render_shared_trace(
    token: str,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> HTMLResponse:
    """Render a read-only HTML page for a shared trace.  No authentication."""
    row = await db.fetchrow(
        """
        SELECT st.token, st.expires_at, st.view_count,
               qt.query, qt.final_answer_text, qt.final_answer_citations,
               qt.started_at, qt.completed_at, qt.mode, qt.metadata
        FROM free_will.shared_traces st
        JOIN free_will.query_traces qt USING (trace_id)
        WHERE st.token = $1
        """,
        token,
    )

    if not row:
        return HTMLResponse(
            _error_page("Ce lien n'existe pas ou a expiré."), status_code=404
        )

    expires_at: datetime = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return HTMLResponse(
            _error_page("Ce lien de partage a expiré."), status_code=410
        )

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
        # Never log the capability token in full — logs are a lower-trust
        # sink and the token alone grants access to the shared trace.
        logger.warning("Could not increment view_count for token %s…", token[:8])

    query = row.get("query") or ""
    answer = row.get("final_answer_text") or ""
    citations_raw = _coerce_json_value(row.get("final_answer_citations"), [])
    trace_metadata = _coerce_json_value(row.get("metadata"), {})
    started_at = row.get("started_at")

    claim_ledger: list[Any] = []
    answer_metadata: dict[str, Any] = {}
    if isinstance(trace_metadata, dict):
        raw_ledger = trace_metadata.get("claim_ledger")
        if isinstance(raw_ledger, list):
            claim_ledger = raw_ledger
        raw_meta = trace_metadata.get("answer_metadata")
        if isinstance(raw_meta, dict):
            answer_metadata = raw_meta

    return HTMLResponse(
        _render_page(
            query,
            answer,
            citations_raw,
            started_at,
            claim_ledger=claim_ledger,
            answer_metadata=answer_metadata,
        )
    )


def _coerce_json_value(value: Any, default: Any) -> Any:
    """asyncpg may return JSONB columns as parsed objects or as strings."""
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default
    return value


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------


def _render_page(
    query: str,
    answer: str,
    citations: list[Any],
    started_at: datetime | None,
    *,
    claim_ledger: list[Any] | None = None,
    answer_metadata: dict[str, Any] | None = None,
) -> str:
    date_str = started_at.strftime("%Y-%m-%d") if started_at else ""
    q_escaped = html.escape(query)
    a_escaped = html.escape(answer).replace("\n", "<br>")

    citation_rows = ""
    citation_labels: dict[str, str] = {}
    for i, c in enumerate(citations or [], start=1):
        if isinstance(c, dict):
            label = html.escape(
                c.get("work_label")
                or c.get("label")
                or c.get("passage_id")
                or c.get("id")
                or ""
            )
            if c.get("id"):
                citation_labels[str(c["id"])] = label
            urn = html.escape(c.get("cts_urn") or "")
            excerpt = html.escape(c.get("excerpt") or "")
            verified = c.get("verified")
            note = html.escape(c.get("verification_note") or "")
            verdict_badge = ""
            if verified is True:
                verdict_badge = '<span class="verdict ok">vérifiée</span>'
            elif verified is False:
                verdict_badge = '<span class="verdict warn">non vérifiée</span>'
            citation_rows += (
                f'<li class="citation"><span class="cnum">[{i}]</span> '
                f"<strong>{label}</strong> {verdict_badge}"
                + (f' <code class="urn">{urn}</code>' if urn else "")
                + (f'<br><em class="excerpt">{excerpt}</em>' if excerpt else "")
                + (f'<br><em class="excerpt">{note}</em>' if note else "")
                + "</li>\n"
            )

    citations_section = (
        f'<section class="citations"><h2>Sources</h2><ol>{citation_rows}</ol></section>'
        if citation_rows
        else ""
    )

    claims_section = _render_claims_section(
        claim_ledger or [], answer_metadata or {}, citation_labels
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
  .verdict{{font-size:.7rem;padding:.1rem .4rem;border-radius:.25rem;vertical-align:middle}}
  .verdict.ok{{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0}}
  .verdict.warn{{background:#fffbeb;color:#b45309;border:1px solid #fde68a}}
  .claims{{margin-bottom:2rem}}
  .claims h2{{font-size:1rem;text-transform:uppercase;letter-spacing:.1em;color:#78716c;margin-bottom:.75rem}}
  .claim{{padding:.5rem 0;border-bottom:1px solid var(--border);font-size:.9rem}}
  .claim .evidence{{color:#78716c;font-size:.8rem;display:block;margin-top:.2rem}}
  .verifnote{{font-size:.8rem;color:#78716c;margin-top:.5rem}}
  footer{{font-size:.75rem;color:#a8a29e;text-align:center;border-top:1px solid var(--border);padding-top:1rem}}
  a{{color:var(--amber)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">EleutherIA</div>
    <div class="badge">Résultat de recherche partagé{" — " + date_str if date_str else ""}</div>
  </header>
  <h1>{q_escaped}</h1>
  <section class="answer">{a_escaped}</section>
  {citations_section}
  {claims_section}
  <footer>Généré par <a href="https://free-will.app">EleutherIA</a> · CC BY 4.0</footer>
</div>
</body>
</html>"""


def _render_claims_section(
    claim_ledger: list[Any],
    answer_metadata: dict[str, Any],
    citation_labels: dict[str, str],
) -> str:
    """Claims-with-evidence + verification summary for the share page.

    Renders the typed claim ledger (claim text, status, evidence ids resolved
    to citation labels when possible) and a one-line verification note from
    the citation audit / text verification reports. Empty string when the
    trace carries no provenance (older traces).
    """
    claim_rows = ""
    for item in claim_ledger:
        if not isinstance(item, dict):
            continue
        claim_text = html.escape(str(item.get("claim") or ""))
        if not claim_text:
            continue
        status = str(item.get("status") or "supported")
        status_class = "ok" if status == "supported" else "warn"
        status_label = "étayée" if status == "supported" else "insuffisante"
        evidence_ids = item.get("evidence_ids") or []
        evidence_labels = [
            citation_labels.get(str(eid), html.escape(str(eid)))
            for eid in evidence_ids
            if eid
        ]
        evidence_html = (
            f'<span class="evidence">Preuves : {", ".join(evidence_labels)}</span>'
            if evidence_labels
            else ""
        )
        claim_rows += (
            f'<li class="claim">{claim_text} '
            f'<span class="verdict {status_class}">{status_label}</span>'
            f"{evidence_html}</li>\n"
        )

    notes: list[str] = []
    verifier = answer_metadata.get("citation_verifier_v2")
    if isinstance(verifier, dict) and verifier.get("total"):
        notes.append(
            f"Audit des citations : {int(verifier.get('verified') or 0)}/"
            f"{int(verifier.get('total') or 0)} vérifiées"
        )
    text_verification = answer_metadata.get("text_verification")
    if isinstance(text_verification, dict):
        unverified = int(text_verification.get("unverified") or 0)
        verified = int(text_verification.get("verified") or 0)
        if unverified:
            notes.append(
                f"Textes anciens : {unverified} extrait(s) non vérifié(s) "
                "dans le corpus"
            )
        elif verified:
            notes.append(f"Textes anciens : {verified} extrait(s) vérifié(s)")
    grounding = answer_metadata.get("grounding")
    if isinstance(grounding, dict) and grounding.get("score") is not None:
        coverage = grounding.get("coverage")
        notes.append(
            f"Score d'ancrage : {grounding['score']}/100"
            + (f" ({coverage})" if coverage else "")
        )

    if not claim_rows and not notes:
        return ""

    notes_html = (
        f'<p class="verifnote">{" · ".join(html.escape(n) for n in notes)}</p>'
        if notes
        else ""
    )
    list_html = f"<ol>{claim_rows}</ol>" if claim_rows else ""
    return (
        '<section class="claims"><h2>Affirmations et preuves</h2>'
        f"{list_html}{notes_html}</section>"
    )


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
