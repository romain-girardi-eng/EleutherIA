#!/usr/bin/env python3
"""Report operational GraphRAG metrics from production query traces."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

TRACE_QUERY = """
SELECT
    trace_id,
    started_at,
    completed_at,
    mode,
    total_latency_ms,
    total_cost_usd,
    metadata,
    provider_usage,
    final_answer_citations
FROM free_will.query_traces
WHERE ($1::timestamptz IS NULL OR started_at >= $1)
ORDER BY started_at
"""


class TracePool(Protocol):
    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, Any]]: ...


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(decoded) if isinstance(decoded, Mapping) else {}
    return {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return decoded if isinstance(decoded, list) else []
    return []


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    # ``total_cost_usd`` is NUMERIC(10,6): asyncpg decodes it as ``Decimal``,
    # not ``float`` — dropping it left the per-query cost line at ``None``.
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    return None


def percentile(values: Sequence[float], percentage: float) -> float | None:
    """Linear-interpolated percentile, matching the eval harness."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _distribution(
    values: Sequence[float], *, include_p90: bool = True
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "count": len(values),
        "p50": round(percentile(values, 50) or 0.0, 3) if values else None,
    }
    if include_p90:
        result["p90"] = round(percentile(values, 90) or 0.0, 3) if values else None
    result["p95"] = round(percentile(values, 95) or 0.0, 3) if values else None
    result["mean"] = round(statistics.mean(values), 6) if values else None
    result["max"] = round(max(values), 6) if values else None
    return result


def _month(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime("%Y-%m")
    if isinstance(value, str) and len(value) >= 7:
        return value[:7]
    return "unknown"


def _publication_verdict(
    answer_metadata: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> tuple[str, list[str]]:
    gate = _mapping(
        answer_metadata.get("publication_gate", metadata.get("publication_gate"))
    )
    status = str(gate.get("status") or "").strip()
    if not status and isinstance(gate.get("publishable"), bool):
        status = "passed" if gate["publishable"] else "blocked"
    if gate:
        reasons = gate.get("reasons") or []
        if not isinstance(reasons, list):
            reasons = [reasons]
        return status or "unknown", [str(reason) for reason in reasons]

    # Historical rows predate publication_gate persistence. Reconstruct only
    # verdicts justified by the retained verifier summary; never assume a pass
    # from the mere presence of answer prose.
    audit = _mapping(answer_metadata.get("citation_verifier_v2"))
    if audit:
        audit_status = str(audit.get("status") or "")
        if audit_status == "passed":
            return "passed", []
        reasons = ["citation_audit_not_passed"]
        for field, reason in (
            ("weak", "weak_citations_present"),
            ("rejected", "rejected_citations_present"),
            ("missing", "missing_citations_present"),
            ("parse_errors", "citation_audit_parse_errors"),
        ):
            if (_number(audit.get(field)) or 0) > 0:
                reasons.append(reason)
        total = _number(audit.get("total_citations", audit.get("total")))
        verified = _number(audit.get("verified"))
        if total is not None and verified != total:
            reasons.append("not_all_citations_verified")
        if audit.get("aborted") is True:
            reasons.append("citation_audit_aborted")
        return "blocked", reasons

    if str(answer_metadata.get("quality_badge") or "").lower() == "blocked":
        return "blocked", ["unspecified"]
    return "unknown", []


def summarize_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate decoded asyncpg rows without database access."""
    total_latencies: list[float] = []
    stage_latencies: defaultdict[str, list[float]] = defaultdict(list)
    query_costs: list[float] = []
    provider_totals: defaultdict[str, dict[str, float]] = defaultdict(
        lambda: {"cost_usd": 0.0, "tokens": 0.0, "calls": 0.0}
    )
    badges: defaultdict[str, Counter[str]] = defaultdict(Counter)
    verdicts: Counter[str] = Counter()
    withholding_reasons: Counter[str] = Counter()
    citation_groups: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {"verified": 0, "total": 0}
    )
    cache_hits = 0
    incomplete = 0
    stage_rows = 0

    for row in rows:
        metadata = _mapping(row.get("metadata"))
        answer_metadata = _mapping(metadata.get("answer_metadata"))
        cache_hits += metadata.get("cache_hit") is True
        incomplete += row.get("completed_at") is None

        latency = _number(row.get("total_latency_ms"))
        if latency is not None:
            total_latencies.append(latency)

        metrics = _list(metadata.get("stage_metrics"))
        observed_stage = False
        for raw_metric in metrics:
            metric = _mapping(raw_metric)
            stage = str(metric.get("stage") or "").strip()
            duration = _number(metric.get("ms"))
            if stage and duration is not None:
                stage_latencies[stage].append(duration)
                observed_stage = True
        if observed_stage:
            stage_rows += 1
        elif latency is not None:
            stage_latencies["total_fallback"].append(latency)

        cost = _number(row.get("total_cost_usd"))
        if cost is not None:
            query_costs.append(cost)

        for provider, raw_usage in _mapping(row.get("provider_usage")).items():
            usage = _mapping(raw_usage)
            target = provider_totals[str(provider)]
            target["cost_usd"] += _number(usage.get("cost_usd")) or 0.0
            target["tokens"] += (
                _number(usage.get("total_tokens", usage.get("tokens"))) or 0.0
            )
            target["calls"] += _number(usage.get("calls")) or 0.0

        badge = answer_metadata.get("quality_badge", metadata.get("quality_badge"))
        badges[_month(row.get("started_at"))][str(badge or "unknown")] += 1

        status, reasons = _publication_verdict(answer_metadata, metadata)
        verdicts[status] += 1
        if status in {"blocked", "withheld", "failed"}:
            withholding_reasons.update(reasons or ["unspecified"])

        for raw_citation in _list(row.get("final_answer_citations")):
            citation = _mapping(raw_citation)
            citation_type = str(citation.get("type") or "unknown")
            layer = str(citation.get("layer") or "unknown")
            group = citation_groups[f"{citation_type}/{layer}"]
            group["total"] += 1
            group["verified"] += citation.get("verified") is True

    citation_summary = {
        key: {
            **counts,
            "verified_ratio": round(
                counts["verified"] / counts["total"],
                4,
            )
            if counts["total"]
            else None,
        }
        for key, counts in sorted(citation_groups.items())
    }
    provider_summary = {
        provider: {
            "cost_usd": round(values["cost_usd"], 8),
            "tokens": int(values["tokens"]),
            "calls": int(values["calls"]),
        }
        for provider, values in sorted(provider_totals.items())
    }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "counts": {
            "traces": len(rows),
            "pipeline_runs": len(rows) - cache_hits,
            "cache_hits": cache_hits,
            "incomplete_runs": incomplete,
            "rows_with_stage_metrics": stage_rows,
        },
        "latency_ms": {
            "overall": _distribution(total_latencies),
            "by_stage": {
                stage: _distribution(values)
                for stage, values in sorted(stage_latencies.items())
            },
        },
        "cost_usd": {
            "per_query": {
                **_distribution(query_costs, include_p90=False),
                "total": round(sum(query_costs), 8) if query_costs else None,
            },
            "by_provider": provider_summary,
        },
        "quality_badge_by_month": {
            month: dict(sorted(counts.items()))
            for month, counts in sorted(badges.items())
        },
        "publication": {
            "verdicts": dict(sorted(verdicts.items())),
            "withholding_reasons": dict(sorted(withholding_reasons.items())),
        },
        "citations": {"verified_by_type_layer": citation_summary},
    }


async def fetch_rows(
    pool: TracePool,
    *,
    since: datetime | None,
) -> Sequence[Mapping[str, Any]]:
    """Execute the reporter's sole, read-only production query."""
    return await pool.fetch(TRACE_QUERY, since)


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
        for row in rows
    )
    return output


def render_markdown(report: Mapping[str, Any], *, since: datetime | None) -> str:
    counts = _mapping(report["counts"])
    latency = _mapping(report["latency_ms"])
    overall = _mapping(latency.get("overall"))
    cost = _mapping(report["cost_usd"])
    per_query = _mapping(cost.get("per_query"))
    lines = [
        "# GraphRAG production trace report",
        "",
        f"- Since: {since.isoformat() if since else 'all retained traces'}",
        f"- Traces: {counts.get('traces', 0)}",
        f"- Pipeline runs / cache hits: {counts.get('pipeline_runs', 0)} / {counts.get('cache_hits', 0)}",
        f"- Incomplete runs: {counts.get('incomplete_runs', 0)}",
        f"- Rows with stage metrics: {counts.get('rows_with_stage_metrics', 0)}",
        "",
        "## Latency",
        "",
        f"Overall p50 / p90 / p95: {overall.get('p50')} / {overall.get('p90')} / {overall.get('p95')} ms",
        "",
    ]
    stage_rows = [
        (
            stage,
            values.get("count"),
            values.get("p50"),
            values.get("p90"),
            values.get("p95"),
        )
        for stage, raw_values in _mapping(latency.get("by_stage")).items()
        if (values := _mapping(raw_values))
    ]
    lines.extend(_table(("Stage", "n", "p50 ms", "p90 ms", "p95 ms"), stage_rows))
    lines.extend(
        [
            "",
            "## Cost",
            "",
            f"Per query p50 / mean / max: {per_query.get('p50')} / {per_query.get('mean')} / {per_query.get('max')} USD",
            f"Observed total: {per_query.get('total')} USD",
            "",
        ]
    )
    provider_rows = [
        (
            provider,
            values.get("cost_usd"),
            values.get("tokens"),
            values.get("calls"),
        )
        for provider, raw_values in _mapping(cost.get("by_provider")).items()
        if (values := _mapping(raw_values))
    ]
    lines.extend(_table(("Provider", "Cost USD", "Tokens", "Calls"), provider_rows))

    lines.extend(["", "## Quality badge by month", ""])
    badge_rows = [
        (month, badge, count)
        for month, raw_counts in _mapping(report["quality_badge_by_month"]).items()
        for badge, count in _mapping(raw_counts).items()
    ]
    lines.extend(_table(("Month", "Badge", "Count"), badge_rows))

    publication = _mapping(report["publication"])
    lines.extend(["", "## Publication and withholding", ""])
    lines.extend(
        _table(
            ("Verdict", "Count"),
            list(_mapping(publication.get("verdicts")).items()),
        )
    )
    lines.extend(["", "Withholding reasons:", ""])
    lines.extend(
        _table(
            ("Reason", "Count"),
            list(_mapping(publication.get("withholding_reasons")).items()),
        )
    )

    lines.extend(["", "## Citation verification", ""])
    citation_rows = [
        (
            group,
            values.get("verified"),
            values.get("total"),
            values.get("verified_ratio"),
        )
        for group, raw_values in _mapping(
            _mapping(report["citations"]).get("verified_by_type_layer")
        ).items()
        if (values := _mapping(raw_values))
    ]
    lines.extend(_table(("Type/layer", "Verified", "Total", "Ratio"), citation_rows))
    return "\n".join(lines) + "\n"


def parse_since(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


async def _run(database_url: str, *, since: datetime | None) -> dict[str, Any]:
    try:
        import asyncpg
    except ImportError as exc:  # pragma: no cover - environment dependency
        raise RuntimeError("asyncpg is required to read query traces") from exc

    pool = await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=3,
        server_settings={"default_transaction_read_only": "on"},
    )
    try:
        rows = await fetch_rows(pool, since=since)
        return summarize_rows(rows)
    finally:
        await pool.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since",
        type=parse_since,
        help="Inclusive ISO-8601 lower bound for started_at.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the machine-readable aggregation instead of Markdown.",
    )
    args = parser.parse_args(argv)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL is required")
    report = asyncio.run(_run(database_url, since=args.since))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report, since=args.since), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
