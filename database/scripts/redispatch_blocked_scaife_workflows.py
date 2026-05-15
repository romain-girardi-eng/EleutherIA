#!/usr/bin/env python3
"""Re-dispatch Scaife ingestion workflows with configured fallback sources.

The 2026-05-15 Perseus CTS TLS/SNI incident left a small batch of workflows
terminated before fetch. This script reads that incident log, reconstructs
workflow metadata from the frozen KG JSONL snapshot, and starts fresh Temporal
workflows using the new `source_policy`/`fallback_sources` inputs.

Example dry run:
    python database/scripts/redispatch_blocked_scaife_workflows.py \
      --source-policy auto \
      --fallback-source phi \
      --fallback-source json_mirror \
      --source-options-file data/ingestion_log/20260515-scaife-fallback-options.example.json \
      --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eleutheria_worker"))


def _normalise_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _load_nodes(path: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            node = json.loads(raw)
            node_id = node.get("id") or node.get("node_id")
            if node_id:
                nodes[str(node_id)] = node
    return nodes


def _load_author_edges(path: Path) -> dict[str, str]:
    author_by_work: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            edge = json.loads(raw)
            relation = edge.get("relation")
            source = edge.get("source") or edge.get("source_id")
            target = edge.get("target") or edge.get("target_id")
            if not source or not target:
                continue
            if relation == "authored_by":
                author_by_work[str(source)] = str(target)
            elif relation == "created_by":
                author_by_work.setdefault(str(target), str(source))
    return author_by_work


def _language_for(cts_urn: str, metadata: dict[str, Any]) -> str:
    if language := metadata.get("language"):
        return str(language)
    if "latinLit" in cts_urn:
        return "lat"
    return "grc"


def _work_options(
    options_by_work: dict[str, Any],
    work_node_id: str,
    cts_urn: str,
) -> dict[str, Any]:
    options = options_by_work.get("default", {})
    selected = options_by_work.get(work_node_id, options_by_work.get(cts_urn, {}))
    merged: dict[str, Any] = {}
    if isinstance(options, dict):
        merged.update(options)
    if isinstance(selected, dict):
        merged.update(selected)
    return _format_option_templates(merged, work_node_id=work_node_id, cts_urn=cts_urn)


def _format_option_templates(value: Any, *, work_node_id: str, cts_urn: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _format_option_templates(
                nested,
                work_node_id=work_node_id,
                cts_urn=cts_urn,
            )
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [
            _format_option_templates(
                nested,
                work_node_id=work_node_id,
                cts_urn=cts_urn,
            )
            for nested in value
        ]
    if isinstance(value, str):
        return value.format(work_node_id=work_node_id, cts_urn=cts_urn)
    return value


def _build_inputs(
    incident: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
    author_edges: dict[str, str],
    *,
    source_policy: str,
    fallback_sources: list[str],
    options_by_work: dict[str, Any],
    overwrite: bool,
    ref_prefix: str,
    level: int,
) -> list[Any]:
    inputs: list[Any] = []
    for entry in incident.get("workflows", []):
        work_node_id = str(entry["work_node_id"])
        cts_urn = str(entry["cts_urn"])
        node = nodes.get(work_node_id, {})
        metadata = _normalise_mapping(node.get("metadata"))
        title = str(node.get("label") or metadata.get("title") or work_node_id)
        author = str(metadata.get("author") or "")
        canonical_id = metadata.get("cts_urn")

        inputs.append(
            {
                "cts_urn": cts_urn,
                "canonical_id": str(canonical_id) if canonical_id else None,
                "title": title,
                "author": author,
                "language": _language_for(cts_urn, metadata),
                "period": str(node.get("period") or metadata.get("period") or ""),
                "school": node.get("school") or metadata.get("school"),
                "ref_prefix": ref_prefix,
                "level": level,
                "work_label": title,
                "work_node_id": work_node_id,
                "author_node_id": author_edges.get(work_node_id),
                "overwrite": overwrite,
                "source_policy": source_policy,
                "fallback_sources": fallback_sources,
                "source_options": _work_options(options_by_work, work_node_id, cts_urn),
            }
        )
    return inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incident-log",
        default="data/ingestion_log/20260515-scaife-blocked.json",
    )
    parser.add_argument("--nodes", default="data/kg/nodes.jsonl")
    parser.add_argument("--edges", default="data/kg/edges.jsonl")
    parser.add_argument("--source-policy", default="auto")
    parser.add_argument(
        "--fallback-source",
        action="append",
        default=[],
        help="Fallback source name. Repeat for ordered fallback chain.",
    )
    parser.add_argument(
        "--source-options-file",
        default="",
        help="JSON object keyed by work_node_id, CTS URN, or `default`.",
    )
    parser.add_argument("--ref-prefix", default="")
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--temporal-host",
        default=os.getenv("TEMPORAL_HOST", "localhost:7233"),
    )
    parser.add_argument(
        "--task-queue",
        default=os.getenv("TEMPORAL_TASK_QUEUE", "eleutheria-ingestion"),
    )
    parser.add_argument("--workflow-prefix", default="scaife-fallback")
    return parser.parse_args()


async def _dispatch(inputs: list[Any], args: argparse.Namespace) -> list[str]:
    from eleutheria_worker.workflows import ScaifeIngestionInput
    from temporalio.client import Client

    client = await Client.connect(args.temporal_host)
    workflow_ids: list[str] = []
    timestamp = int(time.time())
    for index, workflow_input_data in enumerate(inputs, start=1):
        workflow_input = ScaifeIngestionInput(**workflow_input_data)
        workflow_id = f"{args.workflow_prefix}-{workflow_input.work_node_id}-{timestamp}-{index}"
        handle = await client.start_workflow(
            "ScaifeIngestionWorkflow",
            workflow_input,
            id=workflow_id,
            task_queue=args.task_queue,
        )
        workflow_ids.append(handle.id)
        print(f"dispatched {handle.id} -> {workflow_input.cts_urn}")
    return workflow_ids


def main() -> int:
    args = parse_args()
    incident = _load_json(ROOT / args.incident_log)
    options_by_work = (
        _load_json(ROOT / args.source_options_file) if args.source_options_file else {}
    )
    inputs = _build_inputs(
        incident,
        _load_nodes(ROOT / args.nodes),
        _load_author_edges(ROOT / args.edges),
        source_policy=args.source_policy,
        fallback_sources=args.fallback_source,
        options_by_work=options_by_work,
        overwrite=args.overwrite,
        ref_prefix=args.ref_prefix,
        level=args.level,
    )

    preview = [
        {
            "work_node_id": item["work_node_id"],
            "cts_urn": item["cts_urn"],
            "language": item["language"],
            "source_policy": item["source_policy"],
            "fallback_sources": item["fallback_sources"],
            "source_options": item["source_options"],
            "author_node_id": item["author_node_id"],
        }
        for item in inputs
    ]
    print(json.dumps(preview, indent=2, ensure_ascii=False))

    if args.dry_run:
        return 0

    asyncio.run(_dispatch(inputs, args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
