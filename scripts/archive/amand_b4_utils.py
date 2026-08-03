"""B4 utility functions for nodes/edges."""
from __future__ import annotations
import json
from typing import Any

TIMESTAMP = "2026-05-15 22:30:00.000000+00:00"
SCHOLAR_ID = "scholar_amand_de_mendieta_e"
PUB_ID = "pub_amand_1945_fatalisme"
BIBTEX = "amand-1945-fatalisme-et-liberte-dans-l-antiquite-grecque"
AMAND_BOOK = "Fatalisme et liberté dans l'antiquité grecque"
AMAND_YEAR = 1945
AMAND_REPRINT = "Hakkert Amsterdam 1973"
WAVE_TAG = "B4_2026-05-15"


def md_base(
    *, page_range: str, md_line_range: str, chapter: str, chapter_actual: str,
    confidence: float, source_quality: str = "paraphrase_from_md_ocr_95pc",
    contains_greek: bool = True, contains_latin: bool = False,
    evidence_pending: bool = False, evidence_pending_reason: str = "",
    cited_editions: list[str] | None = None, extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md = {
        "claimed_by": SCHOLAR_ID,
        "publication": PUB_ID,
        "bibtex_key": BIBTEX,
        "source_quality": source_quality,
        "amand_book": AMAND_BOOK,
        "amand_book_year": AMAND_YEAR,
        "amand_book_reprint": AMAND_REPRINT,
        "wave": WAVE_TAG,
        "amand_location": {
            "page_range": page_range,
            "md_line_range": md_line_range,
            "chapter": chapter,
        },
        "amand_chapter_actual": chapter_actual,
        "confidence": confidence,
        "contains_greek_to_verify": contains_greek,
    }
    if contains_latin:
        md["contains_latin_to_verify"] = True
    if cited_editions:
        md["amand_cited_edition_unverified"] = cited_editions
    if evidence_pending:
        md["evidence_pending"] = True
        md["evidence_pending_reason"] = evidence_pending_reason
    if extra:
        md.update(extra)
    return md


def make_node(
    *, nid: str, ntype: str, label: str, period: str | None,
    school: str | None, role: str | None, description: str,
    description_en: str, md: dict[str, Any],
    alternative_names: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": nid, "node_id": nid, "type": ntype, "label": label,
        "description": description, "description_en": description_en,
        "period": period, "role": role, "school": school,
        "alternative_names": json.dumps(alternative_names or []),
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP, "updated_at": TIMESTAMP,
    }


def make_edge(
    *, src: str, tgt: str, relation: str, confidence: float,
    md: dict[str, Any] | None = None,
) -> dict[str, Any]:
    edge_md = (md.copy() if md else {})
    edge_md.setdefault("wave", WAVE_TAG)
    edge_md.setdefault("claimed_by", SCHOLAR_ID)
    edge_md.setdefault("publication", PUB_ID)
    edge_md.setdefault("bibtex_key", BIBTEX)
    edge_id = f"{src}__{relation}__{tgt}"[:200]
    return {
        "edge_id": edge_id, "source": src, "target": tgt,
        "source_id": src, "target_id": tgt,
        "relation": relation,
        "confidence": confidence,
        "metadata": json.dumps(edge_md, ensure_ascii=False),
        "weight": 1.0,
        "created_at": TIMESTAMP, "updated_at": TIMESTAMP,
    }
