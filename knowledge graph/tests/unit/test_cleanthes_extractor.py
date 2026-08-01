"""Tests for Cleanthes TEI extractor (Hymn to Zeus + SVF I fragments).

Mirror structure of `test_chrysippus_svf_extractor.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make repo root importable so `scripts.*` resolves regardless of pytest cwd.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_cleanthes_fragments import (  # noqa: E402
    extract_fragments_from_tei,
    extract_hymn_lines,
    fragment_node_id,
    hymn_line_node_id,
)

# -----------------------------------------------------------------------------
# Node id helpers
# -----------------------------------------------------------------------------


def test_fragment_node_id_canonical():
    """SVF I fragment 489 -> passage_cleanthes_svf_i_489."""
    assert fragment_node_id(489) == "passage_cleanthes_svf_i_489"


def test_fragment_node_id_with_suffix():
    """Letter-suffixed fragments (e.g. 1a) preserved verbatim."""
    assert fragment_node_id("1a") == "passage_cleanthes_svf_i_1a"


def test_hymn_line_node_id_canonical():
    """Hymn to Zeus line 1 -> passage_cleanthes_hymn_zeus_line_1."""
    assert hymn_line_node_id(1) == "passage_cleanthes_hymn_zeus_line_1"


def test_hymn_line_node_id_padding():
    """Hymn line ids are NOT zero-padded -- single integer literal."""
    assert hymn_line_node_id(39) == "passage_cleanthes_hymn_zeus_line_39"


# -----------------------------------------------------------------------------
# Fragment extraction
# -----------------------------------------------------------------------------


def test_extract_fragments_returns_list(tmp_path):
    """Minimal TEI with two fragments parses cleanly."""
    tei_sample = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="textpart" subtype="fragment" n="489">
        <p>Arrianus Epict. Diss. II 19 -- content here</p>
      </div>
      <div type="textpart" subtype="fragment" n="537">
        <p>Stobaeus Ecl. I 1, 12 -- hymn introduction</p>
      </div>
    </body>
  </text>
</TEI>
"""
    p = tmp_path / "tei_sample.xml"
    p.write_text(tei_sample, encoding="utf-8")
    fragments = extract_fragments_from_tei(p)
    assert len(fragments) == 2
    assert fragments[0]["number"] == "489"
    assert "Arrianus" in fragments[0]["text"]
    assert fragments[1]["number"] == "537"


def test_extract_fragments_real_tlg1269():
    """Real Cleanthes TEI parses to ~157 fragments including #489, #537."""
    real_path = (
        REPO_ROOT / "data/scholarly_sources/ocr/svf_cleanthes/svf_i_cleanthes_tei.xml"
    )
    if not real_path.exists():
        pytest.skip("Real Cleanthes SVF I TEI not present locally")
    fragments = extract_fragments_from_tei(real_path)
    assert len(fragments) >= 150
    nums = {f["number"] for f in fragments}
    for n in ("489", "527", "537", "549", "551"):
        assert n in nums, f"missing fragment {n}"
    # The Hymn (537) mentions Zeus
    f537 = next(f for f in fragments if f["number"] == "537")
    assert "Ζεῦ" in f537["text"] or "Ζεύς" in f537["text"]


# -----------------------------------------------------------------------------
# Hymn-line extraction
# -----------------------------------------------------------------------------


def test_extract_hymn_lines_from_fragment_text(tmp_path):
    """Given a TEI fragment with <lb/> markers, extract one line per <lb/>."""
    tei_sample = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="textpart" subtype="fragment" n="537">
        <p><bibl>Stobaeus.</bibl> Cleanthes.
          <quote>
            <lb/>Line one greek text alpha,
            <lb/>Line two greek text beta,
            <lb/>Line three greek text gamma.
          </quote>
        </p>
      </div>
    </body>
  </text>
</TEI>
"""
    p = tmp_path / "tei_hymn.xml"
    p.write_text(tei_sample, encoding="utf-8")
    lines = extract_hymn_lines(p, hymn_fragment_number="537")
    assert len(lines) == 3
    assert lines[0] == "Line one greek text alpha,"
    assert lines[1] == "Line two greek text beta,"
    assert lines[2] == "Line three greek text gamma."


def test_extract_hymn_lines_real_hymn():
    """Real TEI Hymn = exactly 39 dactylic hexameter lines."""
    real_path = (
        REPO_ROOT / "data/scholarly_sources/ocr/svf_cleanthes/svf_i_cleanthes_tei.xml"
    )
    if not real_path.exists():
        pytest.skip("Real Cleanthes SVF I TEI not present locally")
    lines = extract_hymn_lines(real_path, hymn_fragment_number="537")
    assert len(lines) == 39
    # Line 1: famous opening
    assert "Κύδιστ" in lines[0] and "ἀθανάτων" in lines[0]
    # Line 2 invokes Zeus
    assert "Ζεῦ" in lines[1]
    # Line 32: ἀλλὰ Ζεῦ πάνδωρε (final prayer block)
    assert "πάνδωρε" in lines[31]
