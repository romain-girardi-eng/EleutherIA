#!/usr/bin/env python3
"""Run an academic canary benchmark against the GraphRAG pipeline.

This script is meant for post-rebuild validation of the live scholarly stack.
It boots the Python GraphRAG service against the configured PostgreSQL and
Qdrant backends, runs a focused set of canary questions, evaluates simple
grounding heuristics, and writes JSON + Markdown reports.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "docs" / "reports"
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


@dataclass(frozen=True)
class QueryCase:
    case_id: str
    category: str
    query: str
    expected_keywords: tuple[str, ...] = ()
    expect_citations: bool = True
    expect_greek: bool = False
    expect_translation: bool = False
    expect_insufficient: bool = False


DEFAULT_CASES: tuple[QueryCase, ...] = (
    QueryCase(
        case_id="doctrinal_stoics",
        category="doctrinal",
        query="What did the Stoics believe about fate and moral responsibility?",
        expected_keywords=("stoic", "fate", "responsibility", "chrysipp"),
    ),
    QueryCase(
        case_id="comparative_stoic_epicurean",
        category="comparative",
        query="Compare Stoic and Epicurean views on determinism and free choice.",
        expected_keywords=("stoic", "epicure", "determin", "choice"),
    ),
    QueryCase(
        case_id="philology_alexander_de_fato_1",
        category="philological",
        query="Quote Alexander of Aphrodisias, De Fato 1 in Greek and English.",
        expected_keywords=("alexander", "de fato"),
        expect_greek=True,
        expect_translation=True,
    ),
    QueryCase(
        case_id="insufficient_parmenides_liberum_arbitrium",
        category="insufficiency",
        query="Quote a passage where Parmenides uses the phrase liberum arbitrium.",
        expected_keywords=("parmenides",),
        expect_insufficient=True,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the GraphRAG academic canary benchmark")
    parser.add_argument(
        "--cases",
        default="all",
        help="Comma-separated case ids to run, or 'all' (default)",
    )
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional output prefix (defaults to timestamped file in docs/reports)",
    )
    parser.add_argument(
        "--prefer-cloud-qdrant",
        action="store_true",
        help="Unset localhost QDRANT_URL so the script uses QDRANT_HOST/QDRANT_API_KEY",
    )
    return parser.parse_args()


def _prepare_imports() -> None:
    sys.path.insert(0, str(REPO_ROOT / "database" / "src"))
    sys.path.insert(0, str(REPO_ROOT / "knowledge graph" / "src"))
    sys.path.insert(0, str(REPO_ROOT / "graphrag" / "src"))


def _prepare_environment(prefer_cloud_qdrant: bool) -> None:
    qdrant_url = os.getenv("QDRANT_URL", "").strip().lower()
    if (
        prefer_cloud_qdrant
        and qdrant_url.startswith("http://localhost")
        and os.getenv("QDRANT_HOST")
        and os.getenv("QDRANT_API_KEY")
    ):
        os.environ.pop("QDRANT_URL", None)


def _selected_cases(case_arg: str) -> list[QueryCase]:
    if case_arg.strip().lower() == "all":
        return list(DEFAULT_CASES)
    requested = {item.strip() for item in case_arg.split(",") if item.strip()}
    return [case for case in DEFAULT_CASES if case.case_id in requested]


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    haystack = text.lower()
    return any(term.lower() in haystack for term in terms)


def _looks_like_translation(answer: str) -> bool:
    lower = answer.lower()
    return "(" in answer and ")" in answer and any(
        marker in lower
        for marker in ("translation", "english", "means", "renders as", "translated as")
    )


def _insufficiency_triggered(result: dict[str, Any]) -> bool:
    answer = str(result.get("answer", "")).lower()
    metadata = result.get("metadata", {}) or {}
    return bool(
        metadata.get("pipeline_degraded")
        or metadata.get("insufficient_evidence")
        or "insufficient" in answer
        or "not enough evidence" in answer
        or "no passage in the database directly addresses" in answer
        or "sources insuffisantes" in answer
    )


def _evaluate_case(case: QueryCase, result: dict[str, Any]) -> dict[str, Any]:
    answer = str(result.get("answer", ""))
    citations = result.get("citations", []) or []
    metadata = result.get("metadata", {}) or {}
    issues: list[str] = []

    if len(answer.strip()) < 120:
        issues.append("answer_too_short")
    if case.expect_citations and not citations:
        issues.append("missing_citations")
    if case.expected_keywords and not _contains_any(
        answer + " " + " ".join(c.get("label", "") for c in citations),
        case.expected_keywords,
    ):
        issues.append("expected_keywords_missing")
    if case.expect_greek and not GREEK_RE.search(answer):
        issues.append("missing_greek")
    if case.expect_translation and not _looks_like_translation(answer):
        issues.append("translation_not_detected")
    if case.expect_insufficient and not _insufficiency_triggered(result):
        issues.append("insufficiency_not_triggered")
    if not case.expect_insufficient and result.get("metadata", {}).get("pipeline_degraded"):
        issues.append("pipeline_degraded")

    return {
        "passed": not issues,
        "issues": issues,
        "answer_length": len(answer),
        "citations_count": len(citations),
        "quality_badge": metadata.get("quality_badge"),
        "query_type": metadata.get("query_type"),
        "llm_provider": result.get("llm_provider"),
        "llm_model": result.get("llm_model"),
        "claim_ledger_mode": metadata.get("claim_ledger_mode"),
        "render_answer_mode": metadata.get("render_answer_mode"),
        "pipeline_degraded": bool(metadata.get("pipeline_degraded")),
        "packed_tokens": metadata.get("context_pack", {}).get("token_estimate")
        if isinstance(metadata.get("context_pack"), dict)
        else None,
        "selected_sections": len(metadata.get("selected_sections", []) or []),
    }


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# GraphRAG Academic Benchmark - {report['generated_at']}",
        "",
        f"- Cases: {report['summary']['total_cases']}",
        f"- Passed: {report['summary']['passed_cases']}",
        f"- Failed: {report['summary']['failed_cases']}",
        f"- Prefer cloud Qdrant: {report['environment']['prefer_cloud_qdrant']}",
        "",
        "| Case | Category | Pass | Query Type | Badge | Citations | Provider | Model | Issues |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]

    for case in report["cases"]:
        evaluation = case["evaluation"]
        issues = ", ".join(evaluation["issues"]) if evaluation["issues"] else "-"
        lines.append(
            "| {case_id} | {category} | {passed} | {query_type} | {badge} | {citations} | {provider} | {model} | {issues} |".format(
                case_id=case["case_id"],
                category=case["category"],
                passed="yes" if evaluation["passed"] else "no",
                query_type=evaluation.get("query_type") or "-",
                badge=evaluation.get("quality_badge") or "-",
                citations=evaluation.get("citations_count") or 0,
                provider=evaluation.get("llm_provider") or "-",
                model=evaluation.get("llm_model") or "-",
                issues=issues,
            )
        )

    lines.extend(["", "## Notes", ""])
    for case in report["cases"]:
        evaluation = case["evaluation"]
        lines.append(f"### {case['case_id']}")
        lines.append(f"- Query: {case['query']}")
        lines.append(f"- Passed: {'yes' if evaluation['passed'] else 'no'}")
        lines.append(f"- Issues: {', '.join(evaluation['issues']) if evaluation['issues'] else 'none'}")
        lines.append("")

    return "\n".join(lines) + "\n"


async def _build_graphrag() -> Any:
    _prepare_imports()

    from eleutheria_database.services.db import DatabaseService
    from eleutheria_graphrag.services.graphrag_service import GraphRAGService
    from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
    from eleutheria_kg.services.qdrant import QdrantService

    db = DatabaseService()
    await db.connect()

    qdrant = QdrantService()
    await qdrant.connect()

    llm = LLMService(preferred_provider=ModelProvider.GEMINI)

    graphrag = GraphRAGService(
        db_service=db,
        qdrant_service=qdrant,
        llm_service=llm,
    )
    await graphrag.load_kg()
    return graphrag


async def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    _prepare_environment(args.prefer_cloud_qdrant)
    cases = _selected_cases(args.cases)
    if not cases:
        raise SystemExit("No benchmark cases selected.")

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    graphrag = await _build_graphrag()

    try:
        case_results: list[dict[str, Any]] = []
        for case in cases:
            result = await graphrag.query(case.query)
            evaluation = _evaluate_case(case, result)
            case_results.append(
                {
                    **asdict(case),
                    "result": {
                        "answer_preview": str(result.get("answer", ""))[:1200],
                        "citations": result.get("citations", []),
                        "metadata": result.get("metadata", {}),
                    },
                    "evaluation": evaluation,
                }
            )
    finally:
        await graphrag.close()

    passed_cases = sum(1 for case in case_results if case["evaluation"]["passed"])
    report = {
        "generated_at": generated_at,
        "environment": {
            "prefer_cloud_qdrant": args.prefer_cloud_qdrant,
            "llm_preferred_provider": os.getenv("LLM_PREFERRED_PROVIDER", "gemini"),
            "llm_thinking_provider": os.getenv("LLM_THINKING_PROVIDER", ""),
            "qdrant_url_effective": os.getenv("QDRANT_URL", ""),
            "qdrant_host": os.getenv("QDRANT_HOST", ""),
        },
        "summary": {
            "total_cases": len(case_results),
            "passed_cases": passed_cases,
            "failed_cases": len(case_results) - passed_cases,
        },
        "cases": case_results,
    }
    return report


def _output_base(output_prefix: str) -> Path:
    if output_prefix:
        return Path(output_prefix)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_DIR / f"{timestamp}-graphrag-academic-benchmark"


def main() -> None:
    args = parse_args()
    report = asyncio.run(run_benchmark(args))
    output_base = _output_base(args.output_prefix)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    json_path = output_base.with_suffix(".json")
    md_path = output_base.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")

    print(f"Wrote benchmark JSON report to {json_path}")
    print(f"Wrote benchmark Markdown report to {md_path}")
    print(
        f"Summary: {report['summary']['passed_cases']}/{report['summary']['total_cases']} cases passed"
    )


if __name__ == "__main__":
    main()
