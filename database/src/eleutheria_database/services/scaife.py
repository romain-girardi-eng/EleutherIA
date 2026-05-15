"""Scaife (Perseus CTS) fetch + ingest service.

Pure, reusable logic extracted from
`database/scripts/fetch_scaife_work.py` and
`database/scripts/ingest_scaife_work.py` so that both the CLI scripts and
the Temporal `ScaifeIngestionWorkflow` activities call into the same code.

No CLI concerns here — no argparse, no `sys.exit`, no print statements.
The module also avoids adding new third-party HTTP dependencies: it relies
on `urllib.request` like `translation.py`, so the Temporal activity stays
sandbox-friendly without pulling `requests` into the worker image.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree as ET

CTS_BASE = "https://scaife-cts.perseus.org/api/cts"
DEFAULT_RATE_LIMIT_SECONDS = 0.5
DEFAULT_TIMEOUT_SECONDS = 30

NS_CTS = "http://chs.harvard.edu/xmlns/cts"
NS_TEI = "http://www.tei-c.org/ns/1.0"

GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
LATIN_RE = re.compile(r"[a-zA-ZÀ-ÿ]")

SCHEMA = "free_will"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScaifeSection:
    """A single fetched section of a work."""

    section_n: int
    canonical_ref: str
    cts_urn: str
    text: str
    word_count: int
    char_length: int
    char_ratio: float
    language: str
    source_name: str = "scaife_cts"


@dataclass(frozen=True)
class ScaifePayload:
    """The complete fetched-and-cleaned payload for a work."""

    work_urn: str
    language: str
    ref_prefix: str
    level: int
    sections: list[ScaifeSection] = field(default_factory=list)
    errors: int = 0
    source_name: str = "scaife_cts"
    source_url: str | None = None


@dataclass(frozen=True)
class IngestMetadata:
    """Metadata required to ingest a fetched payload."""

    canonical_id: str
    title: str
    author: str
    language: str
    period: str
    school: str | None = None
    work_node_id: str = ""
    author_node_id: str | None = None
    overwrite: bool = False
    source: str | None = None
    source_url: str | None = None
    license: str | None = None


@dataclass(frozen=True)
class IngestResult:
    """Outcome of inserting fetched sections into Postgres."""

    work_id: str
    work_node_id: str
    inserted_passages: int
    skipped_existing: bool = False


@dataclass(frozen=True)
class KGLinkResult:
    """Outcome of linking the ingested work into the knowledge graph."""

    work_node_id: str
    created_work_node: bool
    edges_added: int


# ---------------------------------------------------------------------------
# XML helpers (lifted verbatim from fetch_scaife_work.py and kept private)
# ---------------------------------------------------------------------------


def _find_parent(root: ET.Element, target: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        for child in parent:
            if child is target:
                return parent
    return None


def _strip_notes(elem: ET.Element) -> None:
    for note in elem.findall(f".//{{{NS_TEI}}}note"):
        parent = _find_parent(elem, note)
        if parent is not None:
            if note.tail:
                prev_idx = (
                    list(parent).index(note) - 1 if list(parent).index(note) > 0 else -1
                )
                if prev_idx >= 0:
                    sibling = list(parent)[prev_idx]
                    sibling.tail = (sibling.tail or "") + note.tail
                else:
                    parent.text = (parent.text or "") + note.tail
            parent.remove(note)


def _extract_text(elem: ET.Element) -> str:
    parts: list[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        tag = child.tag.replace(f"{{{NS_TEI}}}", "")
        if tag in ("pb", "lb", "milestone"):
            pass
        elif tag == "gap":
            parts.append("[...]")
        elif tag == "del":
            pass
        else:
            parts.append(_extract_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def clean_text(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip()
    text = re.sub(r"\s+([,;:.\?])", r"\1", text)
    text = re.sub(r"\s+\[\.\.\.\]\s+", " [...] ", text)
    return text


def char_ratio(text: str, lang: str) -> float:
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return 0.0
    if lang == "grc":
        count = sum(1 for c in alpha_chars if GREEK_RE.match(c))
    elif lang == "lat":
        count = sum(1 for c in alpha_chars if LATIN_RE.match(c))
    else:
        return 1.0
    return count / len(alpha_chars)


def extract_ref(urn: str, work_urn: str) -> str:
    if ":" in urn:
        parts = urn.rsplit(":", 1)
        if len(parts) == 2:
            return parts[1]
    return urn.replace(work_urn, "").lstrip(":.")


# ---------------------------------------------------------------------------
# HTTP layer — urllib only, no third-party deps
# ---------------------------------------------------------------------------


def _http_get(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> bytes:
    """Synchronous GET against the Scaife CTS API."""
    req = urllib.request.Request(url, headers={"User-Agent": "EleutherIA-Worker/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return bytes(resp.read())


def get_valid_reff(work_urn: str, level: int = 1) -> list[str]:
    url = f"{CTS_BASE}?request=GetValidReff&urn={work_urn}&level={level}"
    payload = _http_get(url)
    root = ET.fromstring(payload)
    urns: list[str] = []
    for urn_elem in root.iter(f"{{{NS_CTS}}}urn"):
        text = (urn_elem.text or "").strip()
        if text:
            urns.append(text)
    return urns


def get_passage(urn: str) -> str:
    url = f"{CTS_BASE}?request=GetPassage&urn={urn}"
    payload = _http_get(url)
    root = ET.fromstring(payload)

    passage_elem = root.find(f".//{{{NS_CTS}}}passage")
    if passage_elem is None:
        raise ValueError(f"No <passage> element for {urn}")

    tei = passage_elem.find(f".//{{{NS_TEI}}}TEI")
    if tei is None:
        body = passage_elem.find(f".//{{{NS_TEI}}}body")
        if body is None:
            raise ValueError(f"No <TEI> or <body> element for {urn}")
        _strip_notes(body)
        paragraphs = body.findall(f".//{{{NS_TEI}}}p") or body.findall(
            f".//{{{NS_TEI}}}l"
        )
        if not paragraphs:
            return clean_text(_extract_text(body))
        return clean_text("\n\n".join(_extract_text(p) for p in paragraphs))

    _strip_notes(tei)
    paragraphs = tei.findall(f".//{{{NS_TEI}}}p")
    if not paragraphs:
        paragraphs = tei.findall(f".//{{{NS_TEI}}}l")
    if not paragraphs:
        body = tei.find(f".//{{{NS_TEI}}}body")
        if body is not None:
            return clean_text(_extract_text(body))
        return clean_text(_extract_text(tei))
    return clean_text("\n\n".join(_extract_text(p) for p in paragraphs))


# ---------------------------------------------------------------------------
# Fetch + parse
# ---------------------------------------------------------------------------


def fetch_work(
    work_urn: str,
    language: str = "grc",
    ref_prefix: str = "",
    level: int = 1,
    rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
    sleep_fn: Any = time.sleep,
    progress_callback: Any = None,
) -> ScaifePayload:
    """Fetch every section of a work and return a structured payload.

    `progress_callback`, if supplied, is invoked as `progress_callback(idx, total)`
    after each section is fetched so the Temporal activity can heartbeat.
    """
    urns = get_valid_reff(work_urn, level=level)
    sections: list[ScaifeSection] = []
    errors = 0

    for i, urn in enumerate(urns):
        ref = extract_ref(urn, work_urn)
        canonical_ref = f"{ref_prefix} {ref}".strip() if ref_prefix else ref

        try:
            text = get_passage(urn)
        except Exception:
            errors += 1
            continue

        section = ScaifeSection(
            section_n=i + 1,
            canonical_ref=canonical_ref,
            cts_urn=urn,
            text=text,
            word_count=len(text.split()),
            char_length=len(text),
            char_ratio=round(char_ratio(text, language), 3),
            language=language,
            source_name="scaife_cts",
        )
        sections.append(section)

        if progress_callback is not None:
            progress_callback(i + 1, len(urns))

        if i < len(urns) - 1 and rate_limit_seconds > 0:
            sleep_fn(rate_limit_seconds)

    return ScaifePayload(
        work_urn=work_urn,
        language=language,
        ref_prefix=ref_prefix,
        level=level,
        sections=sections,
        errors=errors,
        source_name="scaife_cts",
        source_url=CTS_BASE,
    )


def fetch_work_with_fallbacks(
    work_urn: str,
    language: str = "grc",
    ref_prefix: str = "",
    level: int = 1,
    source_policy: str = "scaife",
    fallback_sources: list[str] | None = None,
    source_options: dict[str, Any] | None = None,
    progress_callback: Any = None,
) -> ScaifePayload:
    """Fetch a work from Scaife or a configured fallback source.

    ``source_policy``:
    - ``scaife``: Scaife only (legacy behavior)
    - ``auto``: Scaife, then the listed ``fallback_sources``
    - any source name: that source only (``phi`` or ``json_mirror``)

    Fallback source options are passed as ``source_options[source_name]``.
    For PHI: ``{"author_num": 474, "work_num": 54}``.
    For JSON mirrors: ``{"uri": "/path/to/export.json"}``.
    """
    from eleutheria_database.services import corpus_sources

    options = source_options or {}
    if source_policy == "auto":
        source_order = ["scaife", *(fallback_sources or [])]
    elif source_policy == "scaife":
        source_order = ["scaife"]
    else:
        source_order = [source_policy]

    failures: list[str] = []
    for source_name in source_order:
        try:
            if source_name == "scaife":
                payload = fetch_work(
                    work_urn=work_urn,
                    language=language,
                    ref_prefix=ref_prefix,
                    level=level,
                    progress_callback=progress_callback,
                )
            elif source_name == "phi":
                phi_options = options.get("phi", options)
                payload = corpus_sources.fetch_phi_latin_work(
                    work_urn=work_urn,
                    author_num=phi_options["author_num"],
                    work_num=phi_options["work_num"],
                    ref_prefix=ref_prefix,
                    base_url=phi_options.get("base_url", corpus_sources.PHI_BASE),
                )
            elif source_name in {"json_mirror", "local_json"}:
                mirror_options = options.get(source_name, options)
                payload = corpus_sources.fetch_json_mirror_work(
                    work_urn=work_urn,
                    uri=mirror_options["uri"],
                    language=mirror_options.get("language", language),
                    ref_prefix=ref_prefix,
                    source_name=mirror_options.get("source_name", source_name),
                )
            else:
                raise ValueError(f"Unknown corpus source: {source_name}")

            if payload.sections:
                return payload
            failures.append(f"{source_name}: no sections returned")
        except Exception as exc:
            failures.append(f"{source_name}: {exc}")

    raise RuntimeError(
        "All corpus sources failed for "
        f"{work_urn}: " + "; ".join(failures)
    )


def payload_to_dict(payload: ScaifePayload) -> dict[str, Any]:
    """Serialize a payload for Temporal transport (JSON-friendly)."""
    return {
        "work_urn": payload.work_urn,
        "language": payload.language,
        "ref_prefix": payload.ref_prefix,
        "level": payload.level,
        "errors": payload.errors,
        "source_name": payload.source_name,
        "source_url": payload.source_url,
        "sections": [
            {
                "section_n": s.section_n,
                "canonical_ref": s.canonical_ref,
                "cts_urn": s.cts_urn,
                "text": s.text,
                "word_count": s.word_count,
                "char_length": s.char_length,
                "char_ratio": s.char_ratio,
                "language": s.language,
                "source_name": s.source_name,
            }
            for s in payload.sections
        ],
    }


def payload_from_dict(data: dict[str, Any]) -> ScaifePayload:
    return ScaifePayload(
        work_urn=data["work_urn"],
        language=data.get("language", "grc"),
        ref_prefix=data.get("ref_prefix", ""),
        level=int(data.get("level", 1)),
        errors=int(data.get("errors", 0)),
        source_name=data.get("source_name", "scaife_cts"),
        source_url=data.get("source_url"),
        sections=[
            ScaifeSection(
                section_n=int(s["section_n"]),
                canonical_ref=s["canonical_ref"],
                cts_urn=s["cts_urn"],
                text=s["text"],
                word_count=int(s["word_count"]),
                char_length=int(s["char_length"]),
                char_ratio=float(s["char_ratio"]),
                language=s["language"],
                source_name=s.get("source_name", data.get("source_name", "scaife_cts")),
            )
            for s in data.get("sections", [])
        ],
    )


# ---------------------------------------------------------------------------
# Postgres ingest — synchronous (psycopg2), wrapped by activities in a thread
# ---------------------------------------------------------------------------


def _parse_urn_ref(cts_urn: str) -> tuple[str | None, str | None, str | None]:
    urn_ref = cts_urn.rsplit(":", 1)[-1] if ":" in cts_urn else ""
    parts = urn_ref.split(".") if urn_ref else []
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 1:
        return None, parts[0], None
    return None, None, None


def lookup_existing_work(
    conn: Any,
    canonical_id: str,
) -> tuple[str | None, int]:
    """Return `(work_id, passage_count)` for an existing canonical_id, or `(None, 0)`."""
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")
    cur.execute(
        "SELECT work_id FROM ancient_works WHERE canonical_id = %s",
        (canonical_id,),
    )
    row = cur.fetchone()
    if not row:
        return None, 0
    work_id = str(row[0])
    cur.execute("SELECT COUNT(*) FROM passages WHERE work_id = %s", (work_id,))
    count_row = cur.fetchone()
    count = int(count_row[0]) if count_row else 0
    return work_id, count


def parse_and_insert(
    conn: Any,
    payload: ScaifePayload,
    meta: IngestMetadata,
    heartbeat_callback: Any = None,
) -> IngestResult:
    """Insert payload into `ancient_works` + `passages`, respecting `overwrite`.

    The caller owns the connection (so the activity wrapper can manage commit/
    rollback). Heartbeats are emitted every 100 rows via `heartbeat_callback`.
    """
    import psycopg2.extras

    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    existing_work_id, existing_count = lookup_existing_work(conn, meta.canonical_id)

    if existing_work_id and not meta.overwrite and existing_count > 0:
        return IngestResult(
            work_id=existing_work_id,
            work_node_id=meta.work_node_id,
            inserted_passages=0,
            skipped_existing=True,
        )

    if existing_work_id:
        work_id = existing_work_id
        if meta.overwrite and existing_count > 0:
            cur.execute("DELETE FROM passages WHERE work_id = %s", (work_id,))
    else:
        work_id = str(uuid.uuid4())
        cts_root = (
            payload.sections[0].cts_urn.rsplit(":", 1)[0] if payload.sections else None
        )
        cur.execute(
            """
            INSERT INTO ancient_works
                (
                    work_id, canonical_id, title, author, language, period, school,
                    cts_urn, source, source_url, license, metadata
                )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                work_id,
                meta.canonical_id,
                meta.title,
                meta.author,
                meta.language,
                meta.period,
                meta.school,
                cts_root,
                meta.source or payload.source_name,
                meta.source_url or payload.source_url,
                meta.license,
                json.dumps(
                    {
                        "corpus_source": payload.source_name,
                        "corpus_source_url": payload.source_url,
                    }
                ),
            ),
        )

    rows: list[tuple] = []
    for i, section in enumerate(payload.sections):
        book, chapter, sec = _parse_urn_ref(section.cts_urn)
        rows.append(
            (
                str(uuid.uuid4()),
                work_id,
                section.canonical_ref,
                section.cts_urn,
                book,
                chapter,
                sec,
                i,
                section.text,
                section.char_length,
                section.word_count,
            )
        )

    inserted = 0
    if rows:
        for chunk_start in range(0, len(rows), 100):
            chunk = rows[chunk_start : chunk_start + 100]
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO passages (
                    passage_id, work_id, canonical_ref, cts_urn,
                    book, chapter, section, sequence_number,
                    text_content, char_length, word_count
                )
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                chunk,
                template="(%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                page_size=100,
            )
            inserted += len(chunk)
            if heartbeat_callback is not None:
                heartbeat_callback(inserted, len(rows))

    return IngestResult(
        work_id=work_id,
        work_node_id=meta.work_node_id,
        inserted_passages=inserted,
        skipped_existing=False,
    )


def link_to_kg(
    conn: Any,
    meta: IngestMetadata,
    work_id: str,  # noqa: ARG001 - retained for caller compatibility / future use
) -> KGLinkResult:
    """Upsert the `kg_nodes` work entry and add the `authored_by` edge.

    Caller owns the connection (activity wrapper commits).
    """
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    if not meta.work_node_id:
        return KGLinkResult(
            work_node_id="",
            created_work_node=False,
            edges_added=0,
        )

    cur.execute("SELECT 1 FROM kg_nodes WHERE node_id = %s", (meta.work_node_id,))
    exists = cur.fetchone() is not None

    created = False
    if not exists:
        cur.execute(
            """
            INSERT INTO kg_nodes (node_id, label, type, description, period, metadata)
            VALUES (%s, %s, 'work', %s, %s, %s::jsonb)
            """,
            (
                meta.work_node_id,
                f"{meta.author}, {meta.title}",
                f"{meta.author}, {meta.title} ({meta.language}, {meta.period})",
                meta.period,
                json.dumps(
                    {
                        "canonical_id": meta.canonical_id,
                        "language": meta.language,
                        "author": meta.author,
                        "source": meta.source,
                        "source_url": meta.source_url,
                        "auto_generated": True,
                    }
                ),
            ),
        )
        created = True

    edges = 0
    if meta.author_node_id:
        cur.execute(
            """
            SELECT 1 FROM kg_edges
            WHERE source_id = %s AND target_id = %s AND relation = 'authored_by'
            """,
            (meta.work_node_id, meta.author_node_id),
        )
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO kg_edges (source_id, target_id, relation, metadata)
                VALUES (%s, %s, 'authored_by', %s::jsonb)
                """,
                (
                    meta.work_node_id,
                    meta.author_node_id,
                    json.dumps({"auto_generated": True}),
                ),
            )
            edges = 1

    return KGLinkResult(
        work_node_id=meta.work_node_id,
        created_work_node=created,
        edges_added=edges,
    )


__all__ = [
    "CTS_BASE",
    "DEFAULT_RATE_LIMIT_SECONDS",
    "DEFAULT_TIMEOUT_SECONDS",
    "SCHEMA",
    "ScaifeSection",
    "ScaifePayload",
    "IngestMetadata",
    "IngestResult",
    "KGLinkResult",
    "clean_text",
    "char_ratio",
    "extract_ref",
    "get_valid_reff",
    "get_passage",
    "fetch_work",
    "fetch_work_with_fallbacks",
    "payload_to_dict",
    "payload_from_dict",
    "lookup_existing_work",
    "parse_and_insert",
    "link_to_kg",
]
