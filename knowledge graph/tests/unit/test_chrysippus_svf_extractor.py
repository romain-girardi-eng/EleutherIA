"""Tests for Chrysippus SVF II TEI fragment extraction."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure repo root is importable so `scripts.*` resolves regardless of pytest cwd.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_chrysippus_svf_first1kgreek import (  # noqa: E402
    extract_fragments_from_tei,
    fragment_node_id,
)


def test_fragment_node_id_canonical():
    """SVF II fragment 913 → passage_chrysippus_svf_ii_913."""
    assert fragment_node_id(913) == "passage_chrysippus_svf_ii_913"


def test_fragment_node_id_with_suffix():
    """SVF II fragment 1a → passage_chrysippus_svf_ii_1a (preserved verbatim)."""
    assert fragment_node_id("1a") == "passage_chrysippus_svf_ii_1a"


def test_extract_fragments_returns_list(tmp_path):
    """Given a minimal TEI fragment, the parser returns structured output."""
    tei_sample = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="textpart" subtype="fragment" n="913">
        <p>Plutarchus de Stoic. rep. — content here</p>
      </div>
      <div type="textpart" subtype="fragment" n="914">
        <p>Galenus DPP — content here</p>
      </div>
    </body>
  </text>
</TEI>
"""
    p = tmp_path / "tei_sample.xml"
    p.write_text(tei_sample, encoding="utf-8")
    fragments = extract_fragments_from_tei(p)
    assert len(fragments) == 2
    assert fragments[0]["number"] == "913"
    assert "Plutarchus" in fragments[0]["text"]
    assert fragments[1]["number"] == "914"


def test_extract_fragments_filters_empty(tmp_path):
    """Fragments with empty <p> are still surfaced (caller filters)."""
    tei_sample = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="textpart" subtype="fragment" n="1">
        <p></p>
      </div>
      <div type="textpart" subtype="fragment" n="1a">
        <p>Strabo XIV — content</p>
      </div>
    </body>
  </text>
</TEI>
"""
    p = tmp_path / "tei_sample.xml"
    p.write_text(tei_sample, encoding="utf-8")
    fragments = extract_fragments_from_tei(p)
    nums = [f["number"] for f in fragments]
    assert "1" in nums
    assert "1a" in nums


def test_extract_fragments_real_svf_ii():
    """Real SVF II TEI file parses to >1000 fragments incl. the 913-1000 fate core."""
    real_path = REPO_ROOT / "data/scholarly_sources/ocr/svf_chrysippus/svf_ii_tei.xml"
    if not real_path.exists():
        pytest.skip("Real SVF II TEI not present locally")
    fragments = extract_fragments_from_tei(real_path)
    assert len(fragments) > 1000
    nums = {f["number"] for f in fragments}
    # Anti-fatalist core sanity-check
    for n in ("913", "925", "945", "974", "1000"):
        assert n in nums, f"missing fragment {n}"
    # Text quality: 913 mentions εἱμαρμένης
    f913 = next(f for f in fragments if f["number"] == "913")
    assert "εἱμαρμέ" in f913["text"]
