from __future__ import annotations

import json

from eleutheria_database.services import corpus_sources


def test_parse_phi_pages_extracts_locinfo_pages() -> None:
    html = 'var locInfo = {"pages": ["1.1", "3.1", "fr1.1"]};'
    assert corpus_sources.parse_phi_pages(html) == ["1.1", "3.1", "fr1.1"]


def test_sections_from_phi_rows_chunks_on_citation_markers() -> None:
    rows = [
        ("Title row", ""),
        ("prima linea", "1.1"),
        ("secunda linea", ""),
        ("line number row", "5"),
        ("tertia linea", "2.1"),
        ("fragmentum", "fr1.1"),
    ]
    sections = corpus_sources.sections_from_phi_rows(rows)
    assert sections == [
        {"canonical_ref": "1.1", "text": "prima linea secunda linea line number row"},
        {"canonical_ref": "2.1", "text": "tertia linea"},
        {"canonical_ref": "fr1.1", "text": "fragmentum"},
    ]


def test_parse_phi_text_table_reads_two_cells() -> None:
    html = """
    <table>
      <tr><td>fato omnia fiunt</td><td>1.1</td></tr>
      <tr><td>causis antecedentibus</td><td></td></tr>
    </table>
    """
    assert corpus_sources.parse_phi_text_table(html) == [
        ("fato omnia fiunt", "1.1"),
        ("causis antecedentibus", ""),
    ]


def test_fetch_json_mirror_work_accepts_sections_object(tmp_path) -> None:
    mirror = tmp_path / "mirror.json"
    mirror.write_text(
        json.dumps(
            {
                "source_name": "tlg_institutional_export",
                "source_url": "local://tlg",
                "sections": [
                    {"canonical_ref": "1", "text": "λόγος"},
                    {"canonical_ref": "2", "text": "προαίρεσις"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = corpus_sources.fetch_json_mirror_work(
        work_urn="urn:cts:greekLit:tlg0000.tlg000",
        uri=str(mirror),
        language="grc",
        ref_prefix="Test.",
    )

    assert payload.source_name == "tlg_institutional_export"
    assert len(payload.sections) == 2
    assert payload.sections[0].canonical_ref == "Test. 1"
    assert payload.sections[0].source_name == "tlg_institutional_export"
