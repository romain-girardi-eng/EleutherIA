"""Unit tests for the citation P/R/F1 scorer (pure, offline)."""

from __future__ import annotations

from tests.eval.eval_lib.scoring import citation_prf


def test_perfect_match() -> None:
    prf = citation_prf(["p1", "p2"], ["p2", "p1"])
    assert prf.precision == 1.0
    assert prf.recall == 1.0
    assert prf.f1 == 1.0
    assert prf.true_positives == 2
    assert prf.false_positives == 0
    assert prf.false_negatives == 0


def test_partial_overlap() -> None:
    prf = citation_prf(["p1", "p2", "p3"], ["p1", "p4"])
    assert prf.precision == round(1 / 3, 4)
    assert prf.recall == 0.5
    expected_f1 = round(2 * (1 / 3) * 0.5 / ((1 / 3) + 0.5), 4)
    assert abs(prf.f1 - expected_f1) < 1e-3
    assert prf.true_positives == 1
    assert prf.false_positives == 2
    assert prf.false_negatives == 1


def test_disjoint_sets() -> None:
    prf = citation_prf(["p1"], ["p2"])
    assert prf.precision == 0.0
    assert prf.recall == 0.0
    assert prf.f1 == 0.0


def test_empty_both_is_perfect() -> None:
    prf = citation_prf([], [])
    assert prf.precision == 1.0
    assert prf.recall == 1.0
    assert prf.f1 == 1.0


def test_no_predictions_with_gold_misses_recall() -> None:
    prf = citation_prf([], ["p1"])
    assert prf.precision == 1.0  # vacuous: no wrong citation made
    assert prf.recall == 0.0
    assert prf.f1 == 0.0
    assert prf.false_negatives == 1


def test_predictions_without_gold_kill_precision() -> None:
    prf = citation_prf(["p1"], [])
    assert prf.precision == 0.0
    assert prf.recall == 1.0
    assert prf.f1 == 0.0
    assert prf.false_positives == 1


def test_duplicates_and_empties_are_ignored() -> None:
    prf = citation_prf(["p1", "p1", ""], ["p1"])
    assert prf.precision == 1.0
    assert prf.recall == 1.0
    assert prf.true_positives == 1
