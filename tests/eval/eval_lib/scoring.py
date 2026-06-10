"""Citation precision / recall / F1 against gold expected passages.

Pure set arithmetic — no network, no DB. Used by the offline CI suites and by
``run_eval.py`` when a query carries ``expected_passages`` annotations.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class CitationPRF:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


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
