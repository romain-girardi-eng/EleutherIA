"""Unit tests for the PDF contribution pipeline.

Covers the activity-level helpers in
``eleutheria_worker.activities.contribution_activities`` and the
synchronous orchestrator in ``backend.services.contribution_pipeline``.

The DatabaseService and LLMService are stubbed with ``AsyncMock`` so the
tests run without Postgres or any external network. The sample PDF used by
``test_extract_pdf_text_basic`` is generated in-memory with a tiny standards-
compliant PDF writer so no binary fixture or undeclared test dependency is
required.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from backend.services.contribution_pipeline import process_contribution_sync
from eleutheria_worker.activities import contribution_activities as ca

# ---------------------------------------------------------------------------
# Fixture PDF
# ---------------------------------------------------------------------------


def _build_sample_pdf() -> bytes:
    """Produce a 2-page PDF that exercises every metadata heuristic.

    Page 1 carries title / authors / DOI / year / abstract; page 2 carries a
    chunk of body text long enough to flow into stage-2 classification.
    """
    def literal(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def stream(lines: list[tuple[str, int, int, int, str]]) -> bytes:
        operators = [
            f"BT /{font} {size} Tf 1 0 0 1 {x} {y} Tm ({literal(text)}) Tj ET"
            for font, size, x, y, text in lines
        ]
        return ("\n".join(operators) + "\n").encode("ascii")

    page_one = stream(
        [
            ("F2", 14, 72, 720, "Autexousion in Origen: A Libertarian Reading"),
            ("F1", 11, 72, 700, "Susanne Bobzien and Michael Frede"),
            ("F1", 11, 72, 680, "DOI: 10.1234/origen.2021.001"),
            ("F1", 11, 72, 660, "Journal of Patristic Studies, 2021"),
            ("F2", 11, 72, 630, "Abstract"),
            ("F1", 10, 72, 612, "This article argues that Origen articulates a notion of autexousion"),
            ("F1", 10, 72, 598, "that breaks with Stoic compatibilism and anticipates later libertarian"),
            ("F1", 10, 72, 584, "accounts of free will. We trace the argument through De Principiis III.1"),
            ("F1", 10, 72, 570, "and Contra Celsum IV."),
        ]
    )
    page_two = stream(
        [
            ("F2", 12, 72, 720, "Section 1 - The Stoic Inheritance"),
            ("F1", 11, 72, 690, "Chrysippus' cylinder analogy is the locus classicus of what modern"),
            ("F1", 11, 72, 674, "scholars term Stoic compatibilism. Bobzien (1998) shows that the"),
            ("F1", 11, 72, 658, "analogy works only against a backdrop of universal sympatheia."),
            ("F1", 11, 72, 626, "Origen, by contrast, treats prohairesis as genuinely undetermined"),
            ("F1", 11, 72, 610, "by external causes (De Princ. III.1.5)."),
        ]
    )

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R /F2 8 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R /F2 8 0 R >> >> /Contents 6 0 R >>",
        b"<< /Length " + str(len(page_one)).encode("ascii") + b" >>\nstream\n" + page_one + b"endstream",
        b"<< /Length " + str(len(page_two)).encode("ascii") + b" >>\nstream\n" + page_two + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


@pytest.fixture(scope="module")
def sample_pdf_bytes() -> bytes:
    return _build_sample_pdf()


# ---------------------------------------------------------------------------
# Stage 1 — extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_pdf_text_basic(
    sample_pdf_bytes: bytes, tmp_path: Any, monkeypatch: Any
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)

    extracted = await ca.extract_pdf_text(str(pdf_path))

    assert len(extracted.pages) == 2
    assert extracted.full_text  # non-empty
    md = extracted.structured_metadata
    assert md.title is not None
    assert "Autexousion" in md.title
    assert any("Bobzien" in a for a in md.authors)
    assert md.doi == "10.1234/origen.2021.001"
    assert md.publication_year == 2021
    assert md.abstract is not None
    assert "autexousion" in md.abstract.lower()


# ---------------------------------------------------------------------------
# Stage 2 — relevance classification
# ---------------------------------------------------------------------------


def _make_extracted(title: str = "Test", body: str = "body") -> ca.ExtractedPdf:
    return ca.ExtractedPdf(
        pages=[ca.PdfPage(page_no=1, text=body, blocks=[body])],
        structured_metadata=ca.StructuredMetadata(
            title=title,
            authors=["Jane Doe"],
            abstract="A short abstract.",
        ),
        full_text=body,
    )


@pytest.mark.asyncio
async def test_classify_relevance_returns_score_in_range() -> None:
    llm = AsyncMock()
    llm.generate.return_value = (
        '{"score": 0.72, "summary": "Relevant.", "concepts": ["autexousion"]}'
    )

    result = await ca.classify_relevance(_make_extracted(), llm)

    assert 0.0 <= result.score <= 1.0
    assert result.score == pytest.approx(0.72)
    assert result.summary == "Relevant."
    assert result.concepts == ["autexousion"]
    # Schema-mode was used so the LLM call carried response_json_schema.
    args, kwargs = llm.generate.call_args
    assert kwargs.get("response_json_schema") is not None


@pytest.mark.asyncio
async def test_classify_relevance_strips_markdown_fences() -> None:
    llm = AsyncMock()
    llm.generate.return_value = (
        '```json\n{"score": 0.1, "summary": "Off-topic.", "concepts": []}\n```'
    )

    result = await ca.classify_relevance(_make_extracted(), llm)
    assert result.score == pytest.approx(0.1)
    assert result.concepts == []


# ---------------------------------------------------------------------------
# Stage 3 — proposal extraction + matching
# ---------------------------------------------------------------------------


def _tool_call_message(payload: dict[str, Any]) -> dict[str, Any]:
    """Shape an OpenAI-style assistant tool_call response."""
    import json

    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "irrelevant",
                    "arguments": json.dumps(payload),
                },
            }
        ],
    }


@pytest.mark.asyncio
async def test_extract_kg_proposals_matches_existing_nodes_when_similar() -> None:
    extracted = _make_extracted()
    relevance = ca.RelevanceResult(score=0.8, summary="rel", concepts=["autexousion"])

    llm = AsyncMock()
    llm.generate_with_tools.side_effect = [
        # Scholars
        _tool_call_message(
            {
                "proposals": [
                    {
                        "node_type": "scholar",
                        "label": "Susanne Bobzien",
                        "proposed_id": "scholar_bobzien_s",
                        "description": "Modern Stoic specialist.",
                        "period": "Modern",
                        "evidence_page": 1,
                        "evidence_excerpt": "Bobzien argues…",
                    }
                ]
            }
        ),
        # Citations
        _tool_call_message(
            {
                "proposals": [
                    {
                        "citation_text": "De Princ. III.1.5",
                        "scholar_node_id": "scholar_bobzien_s",
                        "stance": "discusses",
                        "evidence_page": 2,
                        "evidence_excerpt": "Origen treats prohairesis…",
                    }
                ]
            }
        ),
        # Edges
        _tool_call_message(
            {
                "proposals": [
                    {
                        "subject_id": "scholar_bobzien_s",
                        "predicate": "interprets",
                        "object_id": "concept_autexousion",
                        "claim": "Bobzien reads autexousion libertarianly.",
                        "confidence": 0.78,
                        "evidence_page": 1,
                    }
                ]
            }
        ),
    ]

    db = AsyncMock()
    db.fetch.return_value = [
        {"id": "scholar_bobzien_s", "label": "Susanne Bobzien", "sim": 0.95}
    ]
    db.fetchrow.return_value = {"passage_id": "uuid-1"}

    # node_exists checks for scholar_bobzien_s (returns 1) and concept_autexousion
    db.fetchval.side_effect = [1, 1]

    proposals = await ca.extract_kg_proposals(extracted, relevance, db, llm)

    assert len(proposals) == 3
    scholar_p = next(p for p in proposals if p.kind == "node")
    assert scholar_p.target_kg_id == "scholar_bobzien_s"
    assert scholar_p.payload["matches_existing_id"] == "scholar_bobzien_s"

    citation_p = next(p for p in proposals if p.kind == "passage_citation")
    assert citation_p.target_kg_id == "uuid-1"

    edge_p = next(p for p in proposals if p.kind == "edge")
    assert edge_p.payload["subject_resolution"] == "existing"
    assert edge_p.payload["object_resolution"] == "existing"


@pytest.mark.asyncio
async def test_extract_kg_proposals_marks_new_node_when_no_match() -> None:
    extracted = _make_extracted()
    relevance = ca.RelevanceResult(score=0.7, summary="rel", concepts=[])

    llm = AsyncMock()
    llm.generate_with_tools.side_effect = [
        _tool_call_message(
            {
                "proposals": [
                    {
                        "node_type": "scholar",
                        "label": "Quirinus Q. eleutheriaius",
                        "proposed_id": "scholar_eleutheriaius_q",
                    }
                ]
            }
        ),
        _tool_call_message({"proposals": []}),
        _tool_call_message({"proposals": []}),
    ]
    db = AsyncMock()
    db.fetch.return_value = []  # no similar nodes

    proposals = await ca.extract_kg_proposals(extracted, relevance, db, llm)
    assert len(proposals) == 1
    p = proposals[0]
    assert p.kind == "node"
    assert p.target_kg_id is None
    assert p.payload["matches_existing_id"] is None
    assert p.confidence == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# End-to-end orchestration (synchronous runner)
# ---------------------------------------------------------------------------


def _patch_extract_pdf_text(monkeypatch: Any, extracted: ca.ExtractedPdf) -> None:
    async def _fake(_pdf_url: str) -> ca.ExtractedPdf:
        return extracted

    monkeypatch.setattr(ca, "extract_pdf_text", _fake)


@pytest.mark.asyncio
async def test_pipeline_short_circuits_below_threshold(monkeypatch: Any) -> None:
    extracted = _make_extracted(title="Off-topic")
    _patch_extract_pdf_text(monkeypatch, extracted)

    llm = AsyncMock()
    llm.generate.return_value = (
        '{"score": 0.1, "summary": "Not relevant.", "concepts": []}'
    )

    db = AsyncMock()
    db.fetchrow.return_value = {
        "contribution_id": "abc",
        "pdf_url": "/tmp/fake.pdf",
        "pdf_filename": "fake.pdf",
        "status": "uploaded",
    }
    db.execute.return_value = "OK"

    result = await process_contribution_sync("abc", db, llm)

    assert result["status"] == "ready"
    assert result["proposals"] == 0
    assert result["relevance_score"] == pytest.approx(0.1)
    # Stage 3 (tool-calling) must NOT have been invoked.
    llm.generate_with_tools.assert_not_called()
    # Persistence happens through db.execute; at least the status update fires.
    assert db.execute.await_count >= 1


@pytest.mark.asyncio
async def test_pipeline_persists_proposals_when_relevant(monkeypatch: Any) -> None:
    extracted = _make_extracted(title="On Origen")
    _patch_extract_pdf_text(monkeypatch, extracted)

    llm = AsyncMock()
    llm.generate.return_value = (
        '{"score": 0.85, "summary": "Highly relevant.", "concepts": ["autexousion"]}'
    )
    llm.generate_with_tools.side_effect = [
        _tool_call_message(
            {
                "proposals": [
                    {
                        "node_type": "scholar",
                        "label": "Susanne Bobzien",
                        "proposed_id": "scholar_bobzien_s",
                    }
                ]
            }
        ),
        _tool_call_message({"proposals": []}),
        _tool_call_message({"proposals": []}),
    ]

    db = AsyncMock()
    db.fetchrow.return_value = {
        "contribution_id": "abc",
        "pdf_url": "/tmp/fake.pdf",
        "pdf_filename": "fake.pdf",
        "status": "uploaded",
    }
    db.fetch.return_value = []  # no similar nodes
    db.execute.return_value = "OK"

    result = await process_contribution_sync("abc", db, llm)

    assert result["status"] == "ready"
    assert result["proposals"] == 1
    # First execute = mark_processing; second = main UPDATE on contribution;
    # third = the INSERT into kg_contribution_proposals.
    assert db.execute.await_count >= 3
    # The proposal insert references the proposals table.
    insert_calls = [
        c
        for c in db.execute.await_args_list
        if "kg_contribution_proposals" in (c.args[0] if c.args else "")
    ]
    assert len(insert_calls) == 1


@pytest.mark.asyncio
async def test_pipeline_marks_failed_on_extraction_error(monkeypatch: Any) -> None:
    async def _boom(_pdf_url: str) -> ca.ExtractedPdf:
        raise RuntimeError("pdf is corrupted")

    monkeypatch.setattr(ca, "extract_pdf_text", _boom)

    llm = AsyncMock()
    db = AsyncMock()
    db.fetchrow.return_value = {
        "contribution_id": "abc",
        "pdf_url": "/tmp/fake.pdf",
        "pdf_filename": "fake.pdf",
        "status": "uploaded",
    }
    db.execute.return_value = "OK"

    with pytest.raises(RuntimeError, match="pdf is corrupted"):
        await process_contribution_sync("abc", db, llm)

    # The last execute call must mark the row failed with the error message.
    last_call = db.execute.await_args_list[-1]
    sql = last_call.args[0]
    assert "status = 'failed'" in sql
    assert "pdf is corrupted" in last_call.args[2]
