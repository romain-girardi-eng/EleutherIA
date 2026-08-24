"""Deterministic set scoring used by the GraphRAG evaluation harness.

The functions in this module are deliberately dependency-free.  They never
infer that a missing retrieval trace is an empty retrieval: callers must pass
``None`` for an unobserved channel, and the resulting metrics remain ``None``.
That distinction is essential for release reports — an unavailable metric must
not quietly become a zero (or a vacuous perfect score).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CitationPRF:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


@dataclass(frozen=True)
class GoldSetScore:
    """Precision/recall for a gold-bearing identifier channel.

    ``scored`` is false when the channel was not observed or the case has no
    gold for that channel.  In that state every metric is explicitly nullable.
    """

    scored: bool
    precision: float | None
    recall: float | None
    f1: float | None
    true_positives: int | None
    false_positives: int | None
    false_negatives: int | None
    predicted_count: int | None
    gold_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "scored": self.scored,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "predicted_count": self.predicted_count,
            "gold_count": self.gold_count,
        }


def citation_prf(predicted: Iterable[str], expected: Iterable[str]) -> CitationPRF:
    """Score predicted citation ids against the gold expected set.

    Conventions for empty sets:
    - no gold and no predictions -> perfect (1.0 across the board);
    - no gold but predictions exist -> recall stays 1.0 (nothing was missed),
      precision is 0.0 (nothing predicted can be right);
    - gold exists but no predictions -> precision 1.0 vacuously, recall 0.0.
    """
    predicted_set = {p for p in predicted if p}
    expected_set = {e for e in expected if e}

    tp = len(predicted_set & expected_set)
    fp = len(predicted_set - expected_set)
    fn = len(expected_set - predicted_set)

    # Vacuous truths: empty prediction set makes no false claim (P=1.0);
    # empty gold set leaves nothing to miss (R=1.0).
    precision = tp / len(predicted_set) if predicted_set else 1.0
    recall = tp / len(expected_set) if expected_set else 1.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return CitationPRF(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )


def score_gold_set(
    predicted: Iterable[str] | None,
    expected: Iterable[str],
) -> GoldSetScore:
    """Score an observed identifier set only when gold exists.

    Unlike :func:`citation_prf`, this evaluation-facing helper does not award
    1.0 to a case with no gold.  Such a case is *unscored* and therefore cannot
    inflate an aggregate.  ``predicted=None`` means the runner did not expose
    the channel; ``predicted=[]`` is an observed empty result and scores zero
    recall when gold exists.
    """

    expected_set = {str(value) for value in expected if str(value)}
    if predicted is None or not expected_set:
        return GoldSetScore(
            scored=False,
            precision=None,
            recall=None,
            f1=None,
            true_positives=None,
            false_positives=None,
            false_negatives=None,
            predicted_count=None if predicted is None else len(set(predicted)),
            gold_count=len(expected_set),
        )

    predicted_set = {str(value) for value in predicted if str(value)}
    raw = citation_prf(predicted_set, expected_set)
    return GoldSetScore(
        scored=True,
        precision=raw.precision,
        recall=raw.recall,
        f1=raw.f1,
        true_positives=raw.true_positives,
        false_positives=raw.false_positives,
        false_negatives=raw.false_negatives,
        predicted_count=len(predicted_set),
        gold_count=len(expected_set),
    )


def complete_evidence_set_recall(
    predicted: Iterable[str] | None,
    evidence_sets: Iterable[Iterable[str]],
) -> dict[str, Any]:
    """Return the fraction of required evidence groups retrieved in full.

    Each inner iterable is one conjunctive evidence group.  A group counts only
    when *all* of its passage identifiers are present.  This catches the common
    failure where a system retrieves one individually relevant passage but
    misses the other source needed for a comparison or transmission claim.
    """

    groups = [
        {str(value) for value in group if str(value)}
        for group in evidence_sets
    ]
    groups = [group for group in groups if group]
    if predicted is None or not groups:
        return {
            "scored": False,
            "recall": None,
            "complete_sets": None,
            "required_sets": len(groups),
            "set_hits": None,
        }

    predicted_set = {str(value) for value in predicted if str(value)}
    hits = [group.issubset(predicted_set) for group in groups]
    complete = sum(hits)
    return {
        "scored": True,
        "recall": round(complete / len(groups), 4),
        "complete_sets": complete,
        "required_sets": len(groups),
        "set_hits": hits,
    }
