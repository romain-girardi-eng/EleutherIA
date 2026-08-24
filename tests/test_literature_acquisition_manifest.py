from __future__ import annotations

import json
from pathlib import Path

from scripts.build_literature_acquisition_manifest import ARCHIVE, build_manifest

ROOT = Path(__file__).resolve().parents[1]


def committed_rows():
    return [
        json.loads(line)
        for line in (ARCHIVE / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_manifest_covers_every_pdf_and_epub_with_current_hashes() -> None:
    generated = build_manifest()
    committed = committed_rows()
    assert committed == generated
    files = {
        str(path.relative_to(ROOT))
        for path in ARCHIVE.iterdir()
        if path.suffix.lower() in {".pdf", ".epub"}
    }
    assert {row["path"] for row in committed} == files
    assert len(committed) == 33
    assert len({row["intellectual_object_id"] for row in committed}) == 31
    assert all(len(row["sha256"]) == 64 for row in committed)
    assert all(row["reuse_status"] == "unverified_do_not_republish" for row in committed)


def test_scan_ocr_pairs_are_explicit_and_wave1_is_registered() -> None:
    rows = committed_rows()
    by_name = {Path(row["path"]).name: row for row in rows}
    assert by_name["sharples_1983_alexander_de_fato_ocr.pdf"]["derivative_of"] == (
        "sharples_1983_alexander_de_fato.pdf"
    )
    assert by_name["sorabji_1980_necessity_cause_blame_ocr.pdf"]["derivative_of"] == (
        "sorabji_1980_necessity_cause_blame.pdf"
    )
    deep = {
        row["intellectual_object_id"]
        for row in rows
        if row["audit_status"] == "deep_read_wave1"
    }
    assert deep == {
        "blowers_2016_maximus",
        "boys_stones_2018_platonist_philosophy",
        "carter_fatalism_false_futures_author_manuscript",
        "hildebrandt_2022_alexander_lazy_arguments",
        "long_sedley_1987_hellenistic_philosophers_vol2",
        "sorabji_1980_necessity_cause_blame",
        "sytsma_2018_dissertation_origen",
    }
