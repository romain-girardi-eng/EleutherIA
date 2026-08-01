"""Tests for Posidonius testimonia wiring.

Posidonius's writings are lost; the Edelstein-Kidd 1972 edition is under
copyright. This script wires existing KG passages that mention Posidonius
(Cicero De Fato, Diogenes Laertius VII, Seneca Epistulae, Augustine De Civ. Dei,
Galen DPP) to the canonical person node via ``discusses`` edges -- producing
testimonia-level provenance evidence without ingesting new passages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest  # noqa: F401  (kept for parity with sibling test modules)

# Make repo root importable so `scripts.*` resolves regardless of pytest cwd.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.wire_posidonius_testimonia import (  # noqa: E402
    POSIDONIUS_PERSON_ID,
    build_discusses_edge,
    find_posidonius_passages,
)

# -----------------------------------------------------------------------------
# find_posidonius_passages
# -----------------------------------------------------------------------------


def test_find_posidonius_passages_returns_list():
    matches = find_posidonius_passages()
    assert isinstance(matches, list)
    assert all(m.startswith("passage_") for m in matches)


def test_find_posidonius_passages_is_nonempty():
    """Audit established 27 passages; require at least 5 to guard against regressions."""
    matches = find_posidonius_passages()
    assert len(matches) >= 5


def test_find_posidonius_passages_covers_expected_corpora():
    """At minimum, Cicero De Fato should be represented in the testimonia set."""
    matches = find_posidonius_passages()
    assert any("cic" in m and "fat" in m for m in matches), (
        "Expected at least one Cicero De Fato passage in Posidonius testimonia"
    )


# -----------------------------------------------------------------------------
# build_discusses_edge
# -----------------------------------------------------------------------------


def test_build_discusses_edge_canonical():
    edge = build_discusses_edge("passage_cic_div_1")
    assert edge["relation"] == "discusses"
    assert edge["source_id"] == "passage_cic_div_1"
    assert edge["target_id"] == POSIDONIUS_PERSON_ID
    assert "metadata" in edge


def test_build_discusses_edge_metadata_flags():
    edge = build_discusses_edge("passage_cic_div_1")
    # metadata stored as JSON string (matches existing convention in edges.jsonl)
    import json

    meta = (
        json.loads(edge["metadata"])
        if isinstance(edge["metadata"], str)
        else edge["metadata"]
    )
    assert meta.get("relation_type") == "testimonium"
    assert meta.get("auto_wired") is True
    assert meta.get("wired_from_keyword_match") is True
    assert meta.get("wired_date") == "2026-05-16"


def test_build_discusses_edge_has_required_fields():
    edge = build_discusses_edge("passage_cic_div_1")
    # parity with existing discusses edges in edges.jsonl
    assert "source" in edge
    assert "target" in edge
    assert edge["source"] == edge["source_id"]
    assert edge["target"] == edge["target_id"]
    assert edge.get("relation") == "discusses"
    assert "weight" in edge


def test_posidonius_person_id_constant():
    """Guard the canonical node id; the script depends on it being stable."""
    assert POSIDONIUS_PERSON_ID == "person_posidonius_apameia_135_51bce"
