"""Fail-closed retrieval of reviewed, page-level secondary evidence.

KG position metadata supplies only a publication id and a printed/physical page
reference.  This service resolves that reference through the separately
reviewed ``secondary_source_artifacts`` / ``secondary_evidence_pages`` store,
then recomputes every page-text hash before returning evidence to the citation
verifier.  It never reads a position claim or scholar biography as evidence.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

from eleutheria_database.services.text_integrity import text_sha256

logger = logging.getLogger(__name__)

SecondaryPageFetcher = Callable[[str, str], Awaitable[dict[str, Any] | None]]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_SINGLE_PRINTED_RE = re.compile(
    r"^(?:p{1,2}\.?\s*)?(?P<page>\d+[a-z]?|[ivxlcdm]+)(?:\s+n\.\s*\d+)?$",
    re.IGNORECASE,
)
_RANGE_PRINTED_RE = re.compile(
    r"^(?:p{1,2}\.?\s*)?(?P<start>\d+)\s*[-–—]\s*(?P<end>\d+)$",
    re.IGNORECASE,
)
_PHYSICAL_RE = re.compile(
    r"^(?:physical(?:\s+page)?|pdf\s+p(?:age)?\.?)\s*[:#]?\s*(?P<page>\d+)$",
    re.IGNORECASE,
)
_MAX_PAGE_SPAN = 8
_ALLOWED_REUSE = frozenset(
    {"full_text_allowed", "quotation_only", "internal_research_only"}
)
_ALLOWED_RIGHTS = frozenset({"public_domain", "licensed", "copyrighted"})
_ALLOWED_ARTIFACT_EXTRACTION = frozenset({"partial", "complete"})


@dataclass(frozen=True, slots=True)
class PageSelector:
    kind: Literal["printed", "physical"]
    values: tuple[str, ...] | tuple[int, ...]


def parse_page_reference(page_ref: str) -> PageSelector | None:
    """Parse only explicit printed/physical page locators.

    No chapter-to-page or printed-to-physical concordance is inferred. Numeric
    printed ranges are expanded only when bounded to at most eight pages; wider
    ranges must be refined during curation before they are citable.
    """

    raw = " ".join((page_ref or "").strip().split())
    if not raw:
        return None

    physical = _PHYSICAL_RE.fullmatch(raw)
    if physical:
        physical_value = int(physical.group("page"))
        return (
            PageSelector("physical", (physical_value,)) if physical_value > 0 else None
        )

    page_range = _RANGE_PRINTED_RE.fullmatch(raw)
    if page_range:
        start = int(page_range.group("start"))
        end = int(page_range.group("end"))
        if start <= 0 or end < start or end - start + 1 > _MAX_PAGE_SPAN:
            return None
        return PageSelector(
            "printed", tuple(str(page) for page in range(start, end + 1))
        )

    single = _SINGLE_PRINTED_RE.fullmatch(raw)
    if single:
        page_value = single.group("page")
        numeric = re.match(r"\d+", page_value)
        if numeric is not None and int(numeric.group()) <= 0:
            return None
        canonical = page_value.upper() if page_value.isalpha() else page_value.lower()
        return PageSelector("printed", (canonical,))
    return None


def _valid_digest(value: Any) -> str | None:
    digest = str(value or "").strip().lower()
    return digest if _SHA256_RE.fullmatch(digest) else None


def _row_is_publishable(row: dict[str, Any]) -> bool:
    if str(row.get("artifact_review_status") or "") != "reviewed":
        return False
    if str(row.get("artifact_extraction_status") or "") not in (
        _ALLOWED_ARTIFACT_EXTRACTION
    ):
        return False
    if str(row.get("page_review_status") or "") != "reviewed":
        return False
    if str(row.get("page_extraction_status") or "") != "extracted":
        return False
    if str(row.get("reuse_status") or "") not in _ALLOWED_REUSE:
        return False
    if str(row.get("rights_status") or "") not in _ALLOWED_RIGHTS:
        return False

    artifact_sha = _valid_digest(row.get("artifact_source_sha256"))
    page_source_sha = _valid_digest(row.get("page_source_sha256"))
    stored_text_sha = _valid_digest(row.get("text_sha256"))
    text = row.get("text_content")
    if (
        artifact_sha is None
        or page_source_sha is None
        or artifact_sha != page_source_sha
        or stored_text_sha is None
        or not isinstance(text, str)
        or not text.strip()
    ):
        return False
    return bool(text_sha256(text) == stored_text_sha)


def build_db_secondary_page_fetcher(
    db: Any,
    *,
    schema: str | None = None,
) -> SecondaryPageFetcher:
    """Build ``publication_id + page_ref -> reviewed page text | None``.

    Resolution fails closed on invalid locators, missing rows, multiple source
    manifestations, incomplete range coverage, unsafe rights/reuse, review
    debt, missing hashes, or hash disagreement.
    """

    resolved_schema = schema or os.getenv("ELEUTHERIA_DB_SCHEMA") or "free_will"
    if not _SCHEMA_RE.fullmatch(resolved_schema):
        raise ValueError(f"Invalid database schema identifier: {resolved_schema!r}")

    async def fetch(publication_id: str, page_ref: str) -> dict[str, Any] | None:
        selector = parse_page_reference(page_ref)
        if not publication_id or selector is None:
            return None

        printed_pages = (
            [str(value) for value in selector.values]
            if selector.kind == "printed"
            else []
        )
        physical_pages = (
            [int(value) for value in selector.values]
            if selector.kind == "physical"
            else []
        )
        try:
            rows = await db.fetch(
                f"""
                SELECT
                    a.manifestation_id,
                    a.publication_id,
                    a.source_locator,
                    a.source_sha256 AS artifact_source_sha256,
                    a.rights_status,
                    a.reuse_status,
                    a.extraction_status AS artifact_extraction_status,
                    a.review_status AS artifact_review_status,
                    p.source_sha256 AS page_source_sha256,
                    p.physical_page,
                    p.printed_page,
                    p.page_locator,
                    p.text_content,
                    p.text_sha256,
                    p.extraction_status AS page_extraction_status,
                    p.review_status AS page_review_status
                FROM {resolved_schema}.secondary_source_artifacts a
                JOIN {resolved_schema}.secondary_evidence_pages p
                  ON p.manifestation_id = a.manifestation_id
                 AND p.source_sha256 = a.source_sha256
                WHERE a.publication_id = $1
                  AND (
                    (cardinality($2::text[]) > 0 AND p.printed_page = ANY($2::text[]))
                    OR
                    (cardinality($3::integer[]) > 0 AND p.physical_page = ANY($3::integer[]))
                  )
                ORDER BY a.manifestation_id, p.physical_page
                """,
                publication_id,
                printed_pages,
                physical_pages,
            )
        except Exception:
            logger.debug(
                "Secondary page fetch failed for publication=%s page=%s",
                publication_id,
                page_ref,
                exc_info=True,
            )
            return None
        if not rows:
            return None

        normalized_rows = [dict(row) for row in rows]
        manifestations = {
            str(row.get("manifestation_id") or "") for row in normalized_rows
        }
        if "" in manifestations or len(manifestations) != 1:
            return None
        if any(
            str(row.get("publication_id") or "") != publication_id
            or not _row_is_publishable(row)
            for row in normalized_rows
        ):
            return None

        if selector.kind == "printed":
            expected_printed = set(printed_pages)
            actual_printed = {
                str(row.get("printed_page") or "") for row in normalized_rows
            }
            complete = actual_printed == expected_printed and len(
                normalized_rows
            ) == len(expected_printed)
        else:
            expected_physical = set(physical_pages)
            actual_physical = {
                int(row.get("physical_page") or 0) for row in normalized_rows
            }
            complete = actual_physical == expected_physical and len(
                normalized_rows
            ) == len(expected_physical)
        # A duplicate row for the same requested page is ambiguous even when it
        # comes from one manifestation. Do not choose one by ordering.
        if not complete:
            return None

        artifact = normalized_rows[0]
        return {
            "text": "\n\n".join(str(row["text_content"]) for row in normalized_rows),
            "label": f"{publication_id}, {page_ref}",
            "publication_id": publication_id,
            "page_ref": page_ref,
            "manifestation_id": next(iter(manifestations)),
            "source_locator": artifact.get("source_locator"),
            "source_sha256": artifact.get("artifact_source_sha256"),
            "rights_status": artifact.get("rights_status"),
            "reuse_status": artifact.get("reuse_status"),
            "pages": [
                {
                    "physical_page": int(row["physical_page"]),
                    "printed_page": row.get("printed_page"),
                    "page_locator": row.get("page_locator"),
                    "text_sha256": row.get("text_sha256"),
                }
                for row in normalized_rows
            ],
            "source": "secondary_evidence_pages",
        }

    return fetch


__all__ = [
    "PageSelector",
    "SecondaryPageFetcher",
    "build_db_secondary_page_fetcher",
    "parse_page_reference",
]
