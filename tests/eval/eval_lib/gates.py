"""Deterministic, dimension-by-dimension comparison gates for eval v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from tests.eval.eval_lib.schema import RunSchemaError, validate_run_document
except ImportError:  # direct ``tests/eval/run_eval.py`` execution
    from .schema import RunSchemaError, validate_run_document

DEFAULT_MAX_MEAN_REGRESSION = 0.02


def _dig(value: Mapping[str, Any], *path: str) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _decision(
    name: str,
    *,
    status: str,
    baseline: Any,
    candidate: Any,
    rule: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "baseline": baseline,
        "candidate": candidate,
        "rule": rule,
    }


def compare_with_gates(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    max_mean_regression: float = DEFAULT_MAX_MEAN_REGRESSION,
) -> dict[str, Any]:
    """Compare like-for-like runs without collapsing metrics into one score."""

    validation_errors: list[str] = []
    for label, document in (("baseline", baseline), ("candidate", candidate)):
        try:
            validate_run_document(document)
        except RunSchemaError as exc:
            validation_errors.append(f"{label}: {exc}")
    if validation_errors:
        return {
            "artifact_type": "eleutheria.graphrag.eval_comparison",
            "schema_version": "1.0",
            "comparable": False,
            "release_gate": "fail",
            "reasons": validation_errors,
            "decisions": [],
        }

    reasons: list[str] = []
    if _dig(baseline, "dataset", "query_sha256") != _dig(
        candidate, "dataset", "query_sha256"
    ):
        reasons.append("query_sha256 differs")
    if _dig(baseline, "dataset", "case_ids") != _dig(
        candidate, "dataset", "case_ids"
    ):
        reasons.append("case ids/order differ")
    for label, document in (("baseline", baseline), ("candidate", candidate)):
        invalid_count = _dig(
            document, "dataset", "gold_validation", "invalid_gold_count"
        )
        if invalid_count:
            reasons.append(
                f"{label} has {invalid_count} invalid gold identifiers"
            )
    if reasons:
        return {
            "artifact_type": "eleutheria.graphrag.eval_comparison",
            "schema_version": "1.0",
            "comparable": False,
            "release_gate": "fail",
            "reasons": reasons,
            "decisions": [],
        }

    decisions: list[dict[str, Any]] = []
    base_error = _dig(baseline, "summary", "counts", "error_rate")
    cand_error = _dig(candidate, "summary", "counts", "error_rate")
    decisions.append(
        _decision(
            "error_rate_no_regression",
            status="pass" if cand_error <= base_error else "fail",
            baseline=base_error,
            candidate=cand_error,
            rule="candidate <= baseline",
        )
    )

    metric_paths = (
        ("entity_recall", ("summary", "retrieval", "entity", "recall_mean")),
        ("work_recall", ("summary", "retrieval", "work", "recall_mean")),
        (
            "manifestation_recall",
            ("summary", "retrieval", "manifestation", "recall_mean"),
        ),
        ("passage_recall", ("summary", "retrieval", "passage", "recall_mean")),
        (
            "complete_evidence_set_recall",
            ("summary", "retrieval", "complete_evidence_set", "recall_mean"),
        ),
        ("citation_recall", ("summary", "generation", "citation", "recall_mean")),
        (
            "abstention_accuracy",
            ("summary", "generation", "abstention", "accuracy"),
        ),
    )
    for name, path in metric_paths:
        base_value = _dig(baseline, *path)
        cand_value = _dig(candidate, *path)
        if not isinstance(base_value, (int, float)) or not isinstance(
            cand_value, (int, float)
        ):
            decisions.append(
                _decision(
                    f"{name}_no_regression",
                    status="not_evaluated",
                    baseline=base_value,
                    candidate=cand_value,
                    rule="both runs must observe this gold-bearing channel",
                )
            )
            continue
        passed = cand_value + max_mean_regression >= base_value
        decisions.append(
            _decision(
                f"{name}_no_regression",
                status="pass" if passed else "fail",
                baseline=base_value,
                candidate=cand_value,
                rule=f"candidate >= baseline - {max_mean_regression}",
            )
        )

    # A mean can hide a total loss on one multi-source case.  Gate those cases
    # independently whenever the baseline had a complete evidence set.
    baseline_results = {row["id"]: row for row in baseline["results"]}
    candidate_results = {row["id"]: row for row in candidate["results"]}
    lost_complete_sets: list[str] = []
    for case_id, base_result in baseline_results.items():
        base_value = _dig(
            base_result,
            "retrieval",
            "scores",
            "complete_evidence_set",
            "recall",
        )
        cand_value = _dig(
            candidate_results[case_id],
            "retrieval",
            "scores",
            "complete_evidence_set",
            "recall",
        )
        if base_value == 1.0 and cand_value != 1.0:
            lost_complete_sets.append(case_id)
    decisions.append(
        _decision(
            "no_complete_evidence_set_lost",
            status="pass" if not lost_complete_sets else "fail",
            baseline=[],
            candidate=lost_complete_sets,
            rule="a baseline-complete case must remain complete",
        )
    )

    # Means may improve while individual scholarly loci regress. Keep the raw
    # query ids visible and gate passage/citation regressions independently.
    for section, channel in (
        ("retrieval", "entity"),
        ("retrieval", "work"),
        ("retrieval", "manifestation"),
        ("retrieval", "passage"),
        ("generation", "citation"),
    ):
        regressions: list[dict[str, Any]] = []
        for case_id, base_result in baseline_results.items():
            base_score = _dig(base_result, section, "scores", channel)
            cand_score = _dig(candidate_results[case_id], section, "scores", channel)
            if not isinstance(base_score, Mapping) or not isinstance(
                cand_score, Mapping
            ):
                continue
            base_recall = base_score.get("recall") if base_score.get("scored") else None
            cand_recall = cand_score.get("recall") if cand_score.get("scored") else None
            if isinstance(base_recall, (int, float)) and (
                not isinstance(cand_recall, (int, float))
                or cand_recall + max_mean_regression < base_recall
            ):
                regressions.append(
                    {
                        "query_id": case_id,
                        "baseline": base_recall,
                        "candidate": cand_recall,
                    }
                )
        decisions.append(
            _decision(
                f"no_per_query_{channel}_recall_regressions",
                status="pass" if not regressions else "fail",
                baseline=[],
                candidate=regressions,
                rule=(
                    "each observed case candidate recall >= baseline recall - "
                    f"{max_mean_regression}"
                ),
            )
        )

    for channel in (
        "forbidden_strings",
        "source_identity",
        "quote_fidelity",
        "publication",
    ):
        failures = _dig(
            candidate, "summary", "safety", channel, "failure_count"
        )
        observed = _dig(
            candidate, "summary", "safety", channel, "observed_queries"
        )
        if not observed:
            status = "not_evaluated"
        else:
            status = "pass" if failures == 0 else "fail"
        decisions.append(
            _decision(
                f"{channel}_zero_failures",
                status=status,
                baseline=_dig(
                    baseline, "summary", "safety", channel, "failure_count"
                ),
                candidate={"observed_queries": observed, "failure_count": failures},
                rule="zero observed failures; unobserved is never a pass",
            )
        )

    # A generation-enabled release must expose its quote and publication gate
    # verdicts. Retrieval-only baselines explicitly mark these not evaluated.
    if _dig(candidate, "binding", "generation_enabled"):
        success_count = _dig(candidate, "summary", "counts", "successes") or 0
        for channel in ("quote_fidelity", "publication"):
            observed = (
                _dig(candidate, "summary", "safety", channel, "observed_queries")
                or 0
            )
            decisions.append(
                _decision(
                    f"{channel}_coverage",
                    status="pass" if observed == success_count else "fail",
                    baseline=None,
                    candidate={"observed": observed, "successes": success_count},
                    rule="every successful generation must expose this verdict",
                )
            )

    failed = [row["name"] for row in decisions if row["status"] == "fail"]
    return {
        "artifact_type": "eleutheria.graphrag.eval_comparison",
        "schema_version": "1.0",
        "comparable": True,
        "release_gate": "fail" if failed else "pass",
        "reasons": failed,
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "decisions": decisions,
    }


__all__ = ["DEFAULT_MAX_MEAN_REGRESSION", "compare_with_gates"]
