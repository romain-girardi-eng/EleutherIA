"""GraphRAG evaluation harness.

Replays a curated set of queries against a running EleutherIA backend, captures
retrieval results, and computes per-query and per-type metrics. Two runs can be
compared side-by-side to detect regressions.

Usage
-----
    # Capture a run
    python tests/eval/run_eval.py --output baseline.json

    # Capture a run with custom backend / subset
    python tests/eval/run_eval.py \\
        --base-url http://localhost:8000 \\
        --queries tests/eval/queries.yaml \\
        --filter-type concept-author \\
        --limit 5 \\
        --output sample.json

    # Compare two runs
    python tests/eval/run_eval.py --compare baseline.json vectorless.json

Dependencies
------------
Stdlib + ``httpx`` (already in pyproject ``[api]`` extras) + ``pyyaml``.
No evaluation framework (ragas / deepeval) — keep it simple and auditable.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - import guard for clearer error message
    print(
        "ERROR: httpx is required. Install with: pip install 'httpx>=0.28.0'",
        file=sys.stderr,
    )
    raise

try:
    import yaml
except ImportError:  # pragma: no cover
    print(
        "ERROR: pyyaml is required. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    raise


DEFAULT_BASE_URL = "http://localhost:8000"
QUERY_PATH = "/api/graphrag/query"
DEFAULT_TIMEOUT = 180.0  # seconds


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class QueryCase:
    """A single eval query loaded from queries.yaml."""

    id: str
    query: str
    query_type: str
    difficulty: str
    expected_entities: list[str] = field(default_factory=list)
    expected_entity_keywords: list[str] = field(default_factory=list)
    expected_works: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """The result of running one query through the backend."""

    id: str
    query: str
    query_type: str
    difficulty: str
    expected_entities: list[str]
    expected_works: list[str]
    returned_entities: list[str]
    returned_works: list[str]
    citation_count: int
    answer_chars: int
    latency_ms: float
    entity_recall: float
    entity_precision: float
    keyword_hit_rate: float
    work_recall: float
    error: str | None = None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_queries(path: Path) -> list[QueryCase]:
    """Load the YAML query set into typed cases."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not raw or "queries" not in raw:
        raise ValueError(f"{path}: missing top-level 'queries' key")

    cases: list[QueryCase] = []
    for entry in raw["queries"]:
        cases.append(
            QueryCase(
                id=entry["id"],
                query=entry["query"],
                query_type=entry.get("query_type", "unknown"),
                difficulty=entry.get("difficulty", "unknown"),
                expected_entities=list(entry.get("expected_entities", [])),
                expected_entity_keywords=list(
                    entry.get("expected_entity_keywords", [])
                ),
                expected_works=list(entry.get("expected_works", [])),
            )
        )
    return cases


# ---------------------------------------------------------------------------
# Backend call
# ---------------------------------------------------------------------------


def call_graphrag(
    client: httpx.Client, base_url: str, question: str
) -> tuple[dict[str, Any], float]:
    """POST to the GraphRAG endpoint and return (payload, elapsed_ms)."""
    url = base_url.rstrip("/") + QUERY_PATH
    body = {"question": question, "stream": False}

    start = time.perf_counter()
    resp = client.post(url, json=body, timeout=DEFAULT_TIMEOUT)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    resp.raise_for_status()
    return resp.json(), elapsed_ms


def extract_returned_ids(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Collect every node ID surfaced by the pipeline.

    Pulls from: citations[].id (where type=='node'), sources[].node_id,
    context_nodes (already a list of ids), seed_nodes, and evidence_map keys.
    De-dupes while preserving insertion order. Splits work-typed ids into a
    separate bucket (any id starting with ``work_`` or ``sc`` for SC-prefixed
    work nodes).
    """
    seen: dict[str, None] = {}

    for cit in payload.get("citations") or []:
        if not isinstance(cit, dict):
            continue
        ctype = cit.get("type")
        nid = cit.get("id")
        if isinstance(nid, str) and ctype in (None, "node"):
            seen.setdefault(nid, None)

    for src in payload.get("sources") or []:
        if isinstance(src, dict):
            nid = src.get("node_id")
            if isinstance(nid, str):
                seen.setdefault(nid, None)

    for nid in payload.get("context_nodes") or []:
        if isinstance(nid, str):
            seen.setdefault(nid, None)

    for nid in payload.get("seed_nodes") or []:
        if isinstance(nid, str):
            seen.setdefault(nid, None)

    evmap = payload.get("evidence_map") or {}
    if isinstance(evmap, dict):
        for k, v in evmap.items():
            if isinstance(k, str):
                seen.setdefault(k, None)
            if isinstance(v, dict):
                nid = v.get("node_id")
                if isinstance(nid, str):
                    seen.setdefault(nid, None)

    all_ids = list(seen.keys())
    works = [i for i in all_ids if i.startswith("work_") or i.startswith("sc")]
    return all_ids, works


def extract_answer_text(payload: dict[str, Any]) -> str:
    """Return the answer body for keyword matching."""
    ans = payload.get("answer")
    return ans if isinstance(ans, str) else ""


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def compute_query_metrics(
    case: QueryCase,
    returned_entities: list[str],
    returned_works: list[str],
    answer_text: str,
) -> dict[str, float]:
    """Per-query recall / precision / keyword hit rate."""
    expected_set = set(case.expected_entities)
    returned_set = set(returned_entities)
    intersect = expected_set & returned_set

    recall = safe_div(len(intersect), len(expected_set))
    precision = safe_div(len(intersect), len(returned_set))

    # Keyword hit rate runs against returned ids (lowercased) AND answer text.
    haystack = " ".join(returned_entities + [answer_text]).lower()
    keywords = case.expected_entity_keywords
    if keywords:
        hits = sum(1 for kw in keywords if kw.lower() in haystack)
        kw_rate = hits / len(keywords)
    else:
        kw_rate = 0.0

    work_recall = safe_div(
        len(set(case.expected_works) & set(returned_works)),
        len(case.expected_works),
    )

    return {
        "entity_recall": round(recall, 4),
        "entity_precision": round(precision, 4),
        "keyword_hit_rate": round(kw_rate, 4),
        "work_recall": round(work_recall, 4),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    # Nearest-rank percentile, 1-indexed.
    k = max(1, int(round(pct / 100.0 * len(s))))
    return s[min(k, len(s)) - 1]


def aggregate(results: list[QueryResult]) -> dict[str, Any]:
    """Build the top-level aggregate block."""
    successes = [r for r in results if r.error is None]
    failures = [r for r in results if r.error is not None]

    latencies = [r.latency_ms for r in successes]
    recalls = [r.entity_recall for r in successes]
    precisions = [r.entity_precision for r in successes]
    kw_rates = [r.keyword_hit_rate for r in successes]
    work_recalls = [r.work_recall for r in successes]
    citation_counts = [r.citation_count for r in successes]

    by_type: dict[str, dict[str, Any]] = {}
    for r in successes:
        bucket = by_type.setdefault(
            r.query_type,
            {"n": 0, "recalls": [], "precisions": [], "kw_rates": [], "latencies": []},
        )
        bucket["n"] += 1
        bucket["recalls"].append(r.entity_recall)
        bucket["precisions"].append(r.entity_precision)
        bucket["kw_rates"].append(r.keyword_hit_rate)
        bucket["latencies"].append(r.latency_ms)

    by_type_summary = {
        qtype: {
            "n": data["n"],
            "entity_recall_mean": round(statistics.mean(data["recalls"]), 4)
            if data["recalls"]
            else 0.0,
            "entity_precision_mean": round(statistics.mean(data["precisions"]), 4)
            if data["precisions"]
            else 0.0,
            "keyword_hit_rate_mean": round(statistics.mean(data["kw_rates"]), 4)
            if data["kw_rates"]
            else 0.0,
            "latency_p50_ms": round(percentile(data["latencies"], 50), 1),
        }
        for qtype, data in by_type.items()
    }

    return {
        "total_queries": len(results),
        "successes": len(successes),
        "failures": len(failures),
        "error_rate": round(safe_div(len(failures), len(results)), 4),
        "entity_recall_mean": round(statistics.mean(recalls), 4) if recalls else 0.0,
        "entity_precision_mean": round(statistics.mean(precisions), 4)
        if precisions
        else 0.0,
        "keyword_hit_rate_mean": round(statistics.mean(kw_rates), 4)
        if kw_rates
        else 0.0,
        "work_recall_mean": round(statistics.mean(work_recalls), 4)
        if work_recalls
        else 0.0,
        "citation_count_mean": round(statistics.mean(citation_counts), 2)
        if citation_counts
        else 0.0,
        "latency_p50_ms": round(percentile(latencies, 50), 1),
        "latency_p95_ms": round(percentile(latencies, 95), 1),
        "latency_mean_ms": round(statistics.mean(latencies), 1) if latencies else 0.0,
        "by_query_type": by_type_summary,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def run(
    base_url: str,
    cases: list[QueryCase],
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    """Execute every case against the backend and return a result document."""
    results: list[QueryResult] = []

    with httpx.Client() as client:
        for i, case in enumerate(cases, start=1):
            if verbose:
                print(
                    f"[{i:2d}/{len(cases)}] {case.id} ({case.query_type}/"
                    f"{case.difficulty}): {case.query[:80]}",
                    flush=True,
                )
            try:
                payload, elapsed_ms = call_graphrag(client, base_url, case.query)
            except Exception as exc:  # noqa: BLE001
                results.append(
                    QueryResult(
                        id=case.id,
                        query=case.query,
                        query_type=case.query_type,
                        difficulty=case.difficulty,
                        expected_entities=case.expected_entities,
                        expected_works=case.expected_works,
                        returned_entities=[],
                        returned_works=[],
                        citation_count=0,
                        answer_chars=0,
                        latency_ms=0.0,
                        entity_recall=0.0,
                        entity_precision=0.0,
                        keyword_hit_rate=0.0,
                        work_recall=0.0,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                if verbose:
                    print(f"     -> ERROR: {type(exc).__name__}: {exc}", flush=True)
                continue

            returned, returned_works = extract_returned_ids(payload)
            answer = extract_answer_text(payload)
            metrics = compute_query_metrics(case, returned, returned_works, answer)
            citation_count = len(payload.get("citations") or [])

            results.append(
                QueryResult(
                    id=case.id,
                    query=case.query,
                    query_type=case.query_type,
                    difficulty=case.difficulty,
                    expected_entities=case.expected_entities,
                    expected_works=case.expected_works,
                    returned_entities=returned,
                    returned_works=returned_works,
                    citation_count=citation_count,
                    answer_chars=len(answer),
                    latency_ms=round(elapsed_ms, 1),
                    error=None,
                    **metrics,
                )
            )

            if verbose:
                print(
                    f"     -> recall={metrics['entity_recall']:.2f} "
                    f"precision={metrics['entity_precision']:.2f} "
                    f"kw={metrics['keyword_hit_rate']:.2f} "
                    f"cites={citation_count} "
                    f"{elapsed_ms:.0f}ms",
                    flush=True,
                )

    return {
        "schema_version": 1,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": base_url,
        "n_queries": len(cases),
        "aggregate": aggregate(results),
        "results": [asdict(r) for r in results],
    }


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


def _index(run_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in run_doc.get("results", [])}


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    """Print a side-by-side per-query table and a delta summary."""
    base_idx = _index(baseline)
    cand_idx = _index(candidate)
    all_ids = sorted(set(base_idx) | set(cand_idx))

    base_agg = baseline.get("aggregate", {})
    cand_agg = candidate.get("aggregate", {})

    print("\n" + "=" * 100)
    print("PER-QUERY COMPARISON  (baseline -> candidate, delta)")
    print("=" * 100)
    header = (
        f"{'id':<5} {'type':<16} {'recall':<22} {'precision':<22} "
        f"{'kw':<22} {'latency(ms)':<22}"
    )
    print(header)
    print("-" * 100)

    def fmt(base_val: float | None, cand_val: float | None, width: int) -> str:
        b = f"{base_val:.2f}" if isinstance(base_val, (int, float)) else "  - "
        c = f"{cand_val:.2f}" if isinstance(cand_val, (int, float)) else "  - "
        if isinstance(base_val, (int, float)) and isinstance(cand_val, (int, float)):
            d = cand_val - base_val
            sign = "+" if d >= 0 else ""
            delta = f"{sign}{d:.2f}"
        else:
            delta = "  ? "
        return f"{b:>5} -> {c:>5} ({delta:>5})".ljust(width)

    def fmt_ms(b: float | None, c: float | None, width: int) -> str:
        bs = f"{b:.0f}" if isinstance(b, (int, float)) else "  - "
        cs = f"{c:.0f}" if isinstance(c, (int, float)) else "  - "
        if isinstance(b, (int, float)) and isinstance(c, (int, float)):
            d = c - b
            sign = "+" if d >= 0 else ""
            delta = f"{sign}{d:.0f}"
        else:
            delta = "  ? "
        return f"{bs:>5} -> {cs:>5} ({delta:>5})".ljust(width)

    for qid in all_ids:
        b = base_idx.get(qid)
        c = cand_idx.get(qid)
        qtype = (c or b or {}).get("query_type", "?")[:16]
        print(
            f"{qid:<5} {qtype:<16} "
            f"{fmt((b or {}).get('entity_recall'), (c or {}).get('entity_recall'), 22)} "
            f"{fmt((b or {}).get('entity_precision'), (c or {}).get('entity_precision'), 22)} "
            f"{fmt((b or {}).get('keyword_hit_rate'), (c or {}).get('keyword_hit_rate'), 22)} "
            f"{fmt_ms((b or {}).get('latency_ms'), (c or {}).get('latency_ms'), 22)}"
        )

    print("\n" + "=" * 100)
    print("AGGREGATE DELTA")
    print("=" * 100)
    metric_keys = [
        ("entity_recall_mean", "Entity recall (mean)"),
        ("entity_precision_mean", "Entity precision (mean)"),
        ("keyword_hit_rate_mean", "Keyword hit rate (mean)"),
        ("work_recall_mean", "Work recall (mean)"),
        ("citation_count_mean", "Citation count (mean)"),
        ("latency_p50_ms", "Latency p50 (ms)"),
        ("latency_p95_ms", "Latency p95 (ms)"),
        ("error_rate", "Error rate"),
    ]
    for key, label in metric_keys:
        b = base_agg.get(key)
        c = cand_agg.get(key)
        if isinstance(b, (int, float)) and isinstance(c, (int, float)):
            d = c - b
            sign = "+" if d >= 0 else ""
            print(f"  {label:<28} {b:>10.3f} -> {c:>10.3f}  ({sign}{d:.3f})")
        else:
            print(f"  {label:<28} {b!r:>10} -> {c!r:>10}")

    print("\n" + "=" * 100)
    print("BY QUERY TYPE")
    print("=" * 100)
    base_types = base_agg.get("by_query_type", {})
    cand_types = cand_agg.get("by_query_type", {})
    for qtype in sorted(set(base_types) | set(cand_types)):
        bt = base_types.get(qtype, {})
        ct = cand_types.get(qtype, {})
        br = bt.get("entity_recall_mean")
        cr = ct.get("entity_recall_mean")
        bp = bt.get("entity_precision_mean")
        cp = ct.get("entity_precision_mean")
        if isinstance(br, (int, float)) and isinstance(cr, (int, float)):
            dr = cr - br
            dp = (cp or 0) - (bp or 0)
            print(
                f"  {qtype:<18} recall {br:.2f} -> {cr:.2f} ({dr:+.2f})  "
                f"precision {bp:.2f} -> {cp:.2f} ({dp:+.2f})"
            )
        else:
            print(f"  {qtype:<18} (missing in one run)")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the EleutherIA GraphRAG eval harness."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend base URL (default {DEFAULT_BASE_URL}).",
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=Path(__file__).parent / "queries.yaml",
        help="Path to queries.yaml.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Where to write the JSON result document.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N queries (smoke test).",
    )
    parser.add_argument(
        "--filter-type",
        default=None,
        help="Only run queries of this query_type.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-query progress lines."
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "CANDIDATE"),
        help="Two JSON result files to compare. Skips a backend run.",
    )

    args = parser.parse_args(argv)

    if args.compare:
        base_path, cand_path = (Path(p) for p in args.compare)
        baseline = json.loads(base_path.read_text(encoding="utf-8"))
        candidate = json.loads(cand_path.read_text(encoding="utf-8"))
        compare(baseline, candidate)
        return 0

    cases = load_queries(args.queries)
    if args.filter_type:
        cases = [c for c in cases if c.query_type == args.filter_type]
    if args.limit:
        cases = cases[: args.limit]

    if not cases:
        print("No queries selected.", file=sys.stderr)
        return 2

    doc = run(args.base_url, cases, verbose=not args.quiet)

    print("\n" + "=" * 60)
    print("AGGREGATE")
    print("=" * 60)
    agg = doc["aggregate"]
    print(f"  successes / total       : {agg['successes']} / {agg['total_queries']}")
    print(f"  error rate              : {agg['error_rate']:.2%}")
    print(f"  entity recall (mean)    : {agg['entity_recall_mean']:.3f}")
    print(f"  entity precision (mean) : {agg['entity_precision_mean']:.3f}")
    print(f"  keyword hit rate (mean) : {agg['keyword_hit_rate_mean']:.3f}")
    print(f"  work recall (mean)      : {agg['work_recall_mean']:.3f}")
    print(f"  citations / query (mean): {agg['citation_count_mean']:.2f}")
    print(f"  latency p50 (ms)        : {agg['latency_p50_ms']:.0f}")
    print(f"  latency p95 (ms)        : {agg['latency_p95_ms']:.0f}")

    if args.output:
        args.output.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        print(f"\nWrote {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
