"""Tests for ``scripts/analyze_amand_stoic_provenance.py``.

Read-only tests over ``data/kg/`` JSONL snapshot. The analyzer measures, for
each of Amand 1945's six moral anti-fatalist pivots, whether each of the four
primary Stoic philosophers (Chrysippus, Cleanthes, Posidonius, Panaetius) is
a plausible source via three cumulative tests:

  1. thematic   — keyword overlap on labels + descriptions
  2. conceptual — shared ``concept_*`` nodes via 1-hop traversal
  3. textual    — Greek lemma overlap on the Stoic's passages
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
NODES = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES = ROOT / "data" / "kg" / "edges.jsonl"
SCRIPT = ROOT / "scripts" / "analyze_amand_stoic_provenance.py"

skip_if_no_kg = pytest.mark.skipif(
    not NODES.exists() or not EDGES.exists() or not SCRIPT.exists(),
    reason="data/kg snapshot or script missing",
)


@pytest.fixture(scope="module")
def analyzer():  # type: ignore[no-untyped-def]
    """Import the analyzer script as a module so we can call its functions."""
    if not SCRIPT.exists():
        pytest.skip("script not available")
    sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))
    name = "analyze_amand_stoic_provenance"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def kg_node_ids() -> set[str]:
    ids: set[str] = set()
    with NODES.open() as f:
        for line in f:
            node = json.loads(line)
            nid = node.get("id") or node.get("node_id")
            if nid:
                ids.add(nid)
    return ids


@skip_if_no_kg
def test_six_amand_moral_pivots_exist(analyzer, kg_node_ids: set[str]) -> None:
    """All 6 declared Amand moral pivots resolve to nodes in the KG."""
    assert len(analyzer.AMAND_MORAL_PIVOTS) == 6
    missing = [p for p in analyzer.AMAND_MORAL_PIVOTS if p not in kg_node_ids]
    assert not missing, f"missing pivot nodes: {missing}"


@skip_if_no_kg
def test_four_stoic_primary_persons_exist(analyzer, kg_node_ids: set[str]) -> None:
    """All 4 primary Stoic person nodes resolve to nodes in the KG."""
    assert len(analyzer.STOIC_PRIMARY) == 4
    missing = [p for p in analyzer.STOIC_PRIMARY if p not in kg_node_ids]
    assert not missing, f"missing Stoic person nodes: {missing}"


@skip_if_no_kg
def test_pair_score_total_in_range(analyzer) -> None:
    """``PairScore.total_score`` is always in {0, 1, 2, 3}."""
    ps = analyzer.PairScore(
        pivot="argument_carneadean_virtue_vice_amand1945",
        stoic="person_chrysippus_280_206bce_i9j0k1l2",
    )
    assert ps.total_score == 0
    ps.thematic_hits = ["virtue"]
    assert ps.total_score == 1
    ps.conceptual_hits = ["concept_x"]
    assert ps.total_score == 2
    ps.textual_hits = ["αρετη"]
    assert ps.total_score == 3


@skip_if_no_kg
def test_thematic_test_for_virtue_vice_chrysippus(analyzer) -> None:
    """Pivot III (virtue/vice) should have thematic hits against Chrysippus.

    Chrysippus' large SVF corpus contains many passages discussing virtue,
    vice, ἔπαινος, ψόγος, moral responsibility — so we expect at least one
    thematic keyword to land.
    """
    index = analyzer.build_keyword_index()
    score = analyzer.thematic_test(
        "argument_carneadean_virtue_vice_amand1945",
        "person_chrysippus_280_206bce_i9j0k1l2",
        index,
    )
    assert isinstance(score, analyzer.PairScore)
    assert score.thematic_hits, "expected ≥1 thematic keyword hit on Chrysippus corpus"


@skip_if_no_kg
def test_conceptual_test_returns_pair_score(analyzer) -> None:
    """``conceptual_test`` returns a PairScore (type sanity)."""
    concepts = analyzer.build_concept_index()
    score = analyzer.conceptual_test(
        "argument_carneadean_general_theme_amand1945",
        "person_chrysippus_280_206bce_i9j0k1l2",
        concepts,
    )
    assert isinstance(score, analyzer.PairScore)
    assert isinstance(score.conceptual_hits, list)


@skip_if_no_kg
def test_normalize_greek_strips_diacritics(analyzer) -> None:
    """``normalize_greek`` removes combining marks and lowercases."""
    raw = "Εἱμαρμένη"  # capital, multiple diacritics
    assert analyzer.normalize_greek(raw) == "ειμαρμενη"
    # Also test ἀρετή
    assert analyzer.normalize_greek("ἀρετή") == "αρετη"
    # Latin/ASCII passthrough
    assert analyzer.normalize_greek("Heimarmene") == "heimarmene"


@skip_if_no_kg
def test_textual_test_chrysippus_passages_contain_heimarmene(analyzer) -> None:
    """Chrysippus' SVF II.913 explicitly discusses εἱμαρμένη.

    The textual test for pivot I (general theme) should land at least one
    Greek-lemma hit against Chrysippus.
    """
    score = analyzer.textual_test(
        "argument_carneadean_general_theme_amand1945",
        "person_chrysippus_280_206bce_i9j0k1l2",
    )
    assert isinstance(score, analyzer.PairScore)
    assert score.textual_hits, "expected ≥1 Greek-lemma hit on Chrysippus passages"


@skip_if_no_kg
def test_passages_for_person_returns_nonempty_for_chrysippus(analyzer) -> None:
    """``passages_for_person`` returns ≥1 passage for Chrysippus."""
    passages = analyzer.passages_for_person("person_chrysippus_280_206bce_i9j0k1l2")
    assert passages, "Chrysippus must have ≥1 authored_by passage"
    # Each passage carries a 'description' (Greek text body)
    assert all("id" in p for p in passages)


@skip_if_no_kg
def test_full_matrix_shape(analyzer) -> None:
    """``compute_matrix`` returns a 6×4 matrix of PairScore objects."""
    matrix = analyzer.compute_matrix()
    assert len(matrix) == 6, f"expected 6 rows, got {len(matrix)}"
    for row in matrix:
        assert len(row) == 4, f"expected 4 columns, got {len(row)}"
        for cell in row:
            assert isinstance(cell, analyzer.PairScore)
            assert 0 <= cell.total_score <= 3


# ---------------------------------------------------------------------------
# Figure-generation tests (Tasks 11-12)
# ---------------------------------------------------------------------------


FIGURES_SCRIPT = ROOT / "scripts" / "generate_provenance_figures.py"

skip_if_no_figures_script = pytest.mark.skipif(
    not FIGURES_SCRIPT.exists(),
    reason="generate_provenance_figures.py not yet implemented",
)


def _build_full_sample_matrix() -> list[dict]:
    """Build a synthetic 24-row flat matrix covering all 6 pivots × 4 stoics."""
    pivots = [
        "argument_carneadean_general_theme_amand1945",
        "argument_carneadean_legislation_amand1945",
        "argument_carneadean_virtue_vice_amand1945",
        "argument_carneadean_incentives_amand1945",
        "argument_carneadean_action_futility_amand1945",
        "argument_carneadean_piety_amand1945",
    ]
    stoics = [
        "person_chrysippus_280_206bce_i9j0k1l2",
        "person_cleanthes_assos_330_230bce",
        "person_posidonius_apameia_135_51bce",
        "person_panaetius_rhodes_185_109bce",
    ]
    rows: list[dict] = []
    for i, pivot in enumerate(pivots):
        for j, stoic in enumerate(stoics):
            score = (i + j) % 4  # spread 0..3 across the cells
            rows.append(
                {
                    "pivot": pivot,
                    "stoic": stoic,
                    "thematic_hits": ["t"] * min(score, 1),
                    "conceptual_hits": ["c"] if score >= 2 else [],
                    "textual_hits": ["x"] if score >= 3 else [],
                    "total_score": score,
                }
            )
    return rows


@skip_if_no_figures_script
def test_heatmap_generation(tmp_path: Path) -> None:
    """``generate_heatmap`` writes a non-empty PNG (and matching SVG) to disk."""
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location("gpf", FIGURES_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)

    sample = _build_full_sample_matrix()
    out = tmp_path / "heatmap.png"
    module.generate_heatmap(sample, out)

    assert out.exists()
    assert out.stat().st_size > 1000
    # SVG counterpart
    svg = out.with_suffix(".svg")
    assert svg.exists()
    assert svg.stat().st_size > 500


@skip_if_no_figures_script
def test_case_study_generation(tmp_path: Path) -> None:
    """``generate_case_study`` produces a per-pivot bar chart (PNG + SVG)."""
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location("gpf", FIGURES_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)

    stoics = [
        "person_chrysippus_280_206bce_i9j0k1l2",
        "person_cleanthes_assos_330_230bce",
        "person_posidonius_apameia_135_51bce",
        "person_panaetius_rhodes_185_109bce",
    ]
    sample = [
        {
            "pivot": "argument_carneadean_virtue_vice_amand1945",
            "stoic": s,
            "thematic_hits": ["a"] * (i + 1),
            "conceptual_hits": [],
            "textual_hits": ["b"] if i == 0 else [],
            "total_score": 2 if i == 0 else 1,
        }
        for i, s in enumerate(stoics)
    ]
    out = tmp_path / "case.png"
    module.generate_case_study(sample, "argument_carneadean_virtue_vice_amand1945", out)

    assert out.exists()
    assert out.stat().st_size > 1000
    assert out.with_suffix(".svg").exists()


@skip_if_no_figures_script
def test_case_study_filters_by_pivot(tmp_path: Path) -> None:
    """``generate_case_study`` must filter out unrelated pivots silently."""
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location("gpf", FIGURES_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)

    sample = _build_full_sample_matrix()  # all 24 rows, 6 pivots
    out = tmp_path / "case-piety.png"
    module.generate_case_study(sample, "argument_carneadean_piety_amand1945", out)

    assert out.exists()
    assert out.stat().st_size > 1000
