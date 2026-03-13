#!/usr/bin/env python3
"""A/B test a public production GraphRAG endpoint against the new local pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "docs" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A/B test prod GraphRAG vs the new local pipeline")
    parser.add_argument("--query", required=True, help="Question to run against both systems")
    parser.add_argument(
        "--prod-url",
        default="https://free-will.app/api/graphrag/answer",
        help="Public production endpoint to use for arm A",
    )
    parser.add_argument(
        "--prod-auth-token",
        default=os.getenv("PROD_AUTH_TOKEN", ""),
        help="Optional bearer token for protected production endpoints",
    )
    parser.add_argument(
        "--prod-username",
        default=os.getenv("PROD_USERNAME", "researcher"),
        help="Username for automatic login when prod-auth-token is omitted",
    )
    parser.add_argument(
        "--prod-password",
        default=os.getenv("PROD_PASSWORD", "research123"),
        help="Password for automatic login when prod-auth-token is omitted",
    )
    parser.add_argument(
        "--prefer-cloud-qdrant",
        action="store_true",
        help="Unset localhost QDRANT_URL so the local arm uses QDRANT_HOST/QDRANT_API_KEY",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=300.0,
        help="HTTP timeout for the production arm",
    )
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional output prefix (defaults to docs/reports/<timestamp>-graphrag-ab-test)",
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


def _timestamped_prefix(output_prefix: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if output_prefix:
        return Path(output_prefix)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    return REPORT_DIR / f"{stamp}-graphrag-ab-test"


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


async def _run_new_system(query: str) -> dict[str, Any]:
    graphrag = await _build_graphrag()
    started = time.perf_counter()
    try:
        result = await graphrag.query(query)
    finally:
        await graphrag.close()
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "metadata": result.get("metadata", {}) or {},
        "llm_provider": result.get("llm_provider"),
        "llm_model": result.get("llm_model"),
        "processing_time_seconds": elapsed,
    }


def _run_prod(
    query: str,
    prod_url: str,
    timeout_seconds: float,
    prod_auth_token: str = "",
) -> dict[str, Any]:
    started = time.perf_counter()
    headers = {"content-type": "application/json"}
    if prod_auth_token:
        headers["authorization"] = f"Bearer {prod_auth_token}"
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(prod_url, json={"query": query}, headers=headers)
    elapsed = round(time.perf_counter() - started, 3)
    payload: dict[str, Any] = {
        "http_status": response.status_code,
        "processing_time_seconds": elapsed,
    }
    try:
        payload["response_json"] = response.json()
    except Exception:
        payload["response_text"] = response.text
    return payload


def _auth_url_from_prod_url(prod_url: str) -> str:
    parsed = urlsplit(prod_url)
    return f"{parsed.scheme}://{parsed.netloc}/api/auth/login"


def _login_prod(
    prod_url: str,
    timeout_seconds: float,
    username: str,
    password: str,
) -> str:
    if not username or not password:
        return ""
    auth_url = _auth_url_from_prod_url(prod_url)
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(
            auth_url,
            json={"username": username, "password": password},
            headers={"content-type": "application/json"},
        )
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("access_token") or "")


def _response_answer(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("answer") or "")


def _response_citation_count(payload: dict[str, Any]) -> int:
    if not isinstance(payload, dict):
        return 0
    if isinstance(payload.get("sources"), list):
        return len(payload["sources"])
    if isinstance(payload.get("citations"), list):
        return len(payload["citations"])
    return 0


def _score_answer(answer: str, citation_count: int, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    ref_markers = len(
        {
            token
            for block in re.findall(r"\[([^\[\]]+)\]", answer)
            for token in re.findall(r"P?\d+", block)
        }
    )
    quote_blocks = len(re.findall(r"^>\s", answer, flags=re.MULTILINE))
    section_headers = len(re.findall(r"^#{1,3}\s+", answer, flags=re.MULTILINE))
    paragraphs = len([item for item in re.split(r"\n\s*\n", answer) if item.strip()])
    scholarly_cues = sum(
        1
        for cue in (
            "direct textual evidence",
            "ancient testimony",
            "interpretive synthesis",
            "limits of the evidence",
        )
        if cue in answer.lower()
    )
    return {
        "chars": len(answer),
        "citations": citation_count,
        "ref_markers": ref_markers,
        "quote_blocks": quote_blocks,
        "section_headers": section_headers,
        "paragraphs": paragraphs,
        "scholarly_cues": scholarly_cues,
        "pipeline_degraded": metadata.get("pipeline_degraded"),
        "claim_ledger_mode": metadata.get("claim_ledger_mode"),
        "render_answer_mode": metadata.get("render_answer_mode"),
        "quality_badge": metadata.get("quality_badge"),
    }


def _markdown_report(report: dict[str, Any]) -> str:
    prod = report["arm_a_prod"]
    new = report["arm_b_new_system"]
    prod_payload = prod.get("response_json", {})
    prod_answer = _response_answer(prod_payload)
    new_answer = new.get("answer", "")
    prod_score = report["scorecards"]["arm_a_prod"]
    new_score = report["scorecards"]["arm_b_new_system"]
    lines = [
        f"# GraphRAG A/B Test - {report['generated_at']}",
        "",
        f"- Query: {report['query']}",
        f"- Arm A URL: {report['prod_url']}",
        "",
        "| Arm | Status | Time (s) | Provider | Model | Citations | Preview |",
        "| --- | --- | ---: | --- | --- | ---: | --- |",
        "| A (prod) | {status} | {time:.3f} | {provider} | {model} | {cites} | {preview} |".format(
            status=prod.get("http_status", "-"),
            time=prod.get("processing_time_seconds", 0.0),
            provider="-",
            model="-",
            cites=prod_score["citations"],
            preview=prod_answer[:140].replace("\n", " ") or "-",
        ),
        "| B (new) | {status} | {time:.3f} | {provider} | {model} | {cites} | {preview} |".format(
            status="ok",
            time=new.get("processing_time_seconds", 0.0),
            provider=new.get("llm_provider") or "-",
            model=new.get("llm_model") or "-",
            cites=new_score["citations"],
            preview=new_answer[:140].replace("\n", " ") or "-",
        ),
        "",
        "## Scorecards",
        "",
        "### Arm A",
        "",
        f"- chars: {prod_score['chars']}",
        f"- citations: {prod_score['citations']}",
        f"- ref_markers: {prod_score['ref_markers']}",
        f"- quote_blocks: {prod_score['quote_blocks']}",
        f"- section_headers: {prod_score['section_headers']}",
        f"- paragraphs: {prod_score['paragraphs']}",
        f"- scholarly_cues: {prod_score['scholarly_cues']}",
        "",
        "### Arm B",
        "",
        f"- chars: {new_score['chars']}",
        f"- citations: {new_score['citations']}",
        f"- ref_markers: {new_score['ref_markers']}",
        f"- quote_blocks: {new_score['quote_blocks']}",
        f"- section_headers: {new_score['section_headers']}",
        f"- paragraphs: {new_score['paragraphs']}",
        f"- scholarly_cues: {new_score['scholarly_cues']}",
        f"- pipeline_degraded: {new_score['pipeline_degraded']}",
        f"- claim_ledger_mode: {new_score['claim_ledger_mode']}",
        f"- render_answer_mode: {new_score['render_answer_mode']}",
        f"- quality_badge: {new_score['quality_badge']}",
        "",
        "## Arm A",
        "",
        prod_answer or json.dumps(prod_payload, ensure_ascii=False, indent=2),
        "",
        "## Arm B",
        "",
        new_answer or "-",
        "",
    ]
    return "\n".join(lines) + "\n"


async def main() -> None:
    args = parse_args()
    _prepare_environment(args.prefer_cloud_qdrant)
    prod_auth_token = args.prod_auth_token or _login_prod(
        args.prod_url,
        args.timeout_seconds,
        args.prod_username,
        args.prod_password,
    )

    report = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": args.query,
        "prod_url": args.prod_url,
        "arm_a_prod": _run_prod(
            args.query,
            args.prod_url,
            args.timeout_seconds,
            prod_auth_token,
        ),
        "arm_b_new_system": await _run_new_system(args.query),
    }
    prod_payload = report["arm_a_prod"].get("response_json", {})
    new_payload = report["arm_b_new_system"]
    report["scorecards"] = {
        "arm_a_prod": _score_answer(
            _response_answer(prod_payload),
            _response_citation_count(prod_payload),
        ),
        "arm_b_new_system": _score_answer(
            new_payload.get("answer", ""),
            len(new_payload.get("citations", [])),
            new_payload.get("metadata", {}) or {},
        ),
    }

    prefix = _timestamped_prefix(args.output_prefix)
    json_path = prefix.with_suffix(".json")
    md_path = prefix.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    md_path.write_text(_markdown_report(report))

    print(f"Wrote JSON report to {json_path}")
    print(f"Wrote Markdown report to {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
