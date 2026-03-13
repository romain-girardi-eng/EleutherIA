#!/usr/bin/env python3
"""Validate the live LLM runtime stack used by GraphRAG.

Checks:
- reasoning provider routing (`thinking_mode=True`)
- Gemini prompt caching creation + reuse
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "docs" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the GraphRAG LLM runtime stack")
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional output prefix (defaults to timestamped file in docs/reports)",
    )
    return parser.parse_args()


def _prepare_imports() -> None:
    sys.path.insert(0, str(REPO_ROOT / "graphrag" / "src"))


def _long_cache_prefix() -> str:
    line = (
        "Stable scholarly preface for Gemini prompt caching. "
        "This block exists only to exercise provider-side cachedContents reuse. "
    )
    return "".join(line for _ in range(180))


async def run_validation() -> dict:
    _prepare_imports()

    from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    report: dict[str, object] = {
        "generated_at": generated_at,
        "environment": {
            "llm_preferred_provider": os.getenv("LLM_PREFERRED_PROVIDER", "gemini"),
            "llm_thinking_provider": os.getenv("LLM_THINKING_PROVIDER", ""),
            "gemini_prompt_cache_enabled": os.getenv("GEMINI_ENABLE_PROMPT_CACHE", "1"),
        },
        "reasoning_probe": {},
        "prompt_cache_probe": {},
    }

    reasoning_llm = LLMService(
        preferred_provider=ModelProvider.GEMINI,
        enable_rate_limiting=False,
    )
    try:
        response = await reasoning_llm.generate(
            'Return exactly this JSON and nothing else: {"ok":true}',
            temperature=0.0,
            max_tokens=32,
            thinking_mode=True,
        )
        report["reasoning_probe"] = {
            "ok": True,
            "provider": reasoning_llm.last_provider_used,
            "model": reasoning_llm.last_model_used,
            "response_preview": response[:200],
        }
    except Exception as exc:  # pragma: no cover - live probe
        report["reasoning_probe"] = {
            "ok": False,
            "provider": reasoning_llm.last_provider_used,
            "model": reasoning_llm.last_model_used,
            "error": f"{exc.__class__.__name__}: {exc}",
        }

    cache_llm = LLMService(
        preferred_provider=ModelProvider.GEMINI,
        enable_rate_limiting=False,
    )
    prefix = _long_cache_prefix()
    try:
        first = await cache_llm.generate(
            "Reply with OK.",
            system_prompt="You are validating Gemini provider-side prompt caching.",
            temperature=0.0,
            max_tokens=16,
            cache_key="runtime-validation",
            cache_prefix=prefix,
            cache_ttl_seconds=900,
        )
        cache_entries_after_first = len(cache_llm._prompt_cache_names)
        cached_names = list(cache_llm._prompt_cache_names.values())

        second = await cache_llm.generate(
            "Reply with OK.",
            system_prompt="You are validating Gemini provider-side prompt caching.",
            temperature=0.0,
            max_tokens=16,
            cache_key="runtime-validation",
            cache_prefix=prefix,
            cache_ttl_seconds=900,
        )
        cache_entries_after_second = len(cache_llm._prompt_cache_names)

        report["prompt_cache_probe"] = {
            "ok": True,
            "provider": cache_llm.last_provider_used,
            "model": cache_llm.last_model_used,
            "cache_entries_after_first": cache_entries_after_first,
            "cache_entries_after_second": cache_entries_after_second,
            "cached_content_created": bool(cached_names),
            "cached_content_name": cached_names[0] if cached_names else None,
            "first_response_preview": first[:120],
            "second_response_preview": second[:120],
        }
    except Exception as exc:  # pragma: no cover - live probe
        report["prompt_cache_probe"] = {
            "ok": False,
            "provider": cache_llm.last_provider_used,
            "model": cache_llm.last_model_used,
            "error": f"{exc.__class__.__name__}: {exc}",
            "cache_entries": len(cache_llm._prompt_cache_names),
        }

    return report


def _markdown_report(report: dict) -> str:
    reasoning = report["reasoning_probe"]
    cache = report["prompt_cache_probe"]
    lines = [
        f"# LLM Runtime Validation - {report['generated_at']}",
        "",
        "## Reasoning Probe",
        "",
        f"- OK: {reasoning.get('ok')}",
        f"- Provider: {reasoning.get('provider')}",
        f"- Model: {reasoning.get('model')}",
    ]
    if reasoning.get("error"):
        lines.append(f"- Error: {reasoning['error']}")

    lines.extend(
        [
            "",
            "## Prompt Cache Probe",
            "",
            f"- OK: {cache.get('ok')}",
            f"- Provider: {cache.get('provider')}",
            f"- Model: {cache.get('model')}",
            f"- Cached content created: {cache.get('cached_content_created')}",
            f"- Cache entries after first call: {cache.get('cache_entries_after_first')}",
            f"- Cache entries after second call: {cache.get('cache_entries_after_second')}",
        ]
    )
    if cache.get("error"):
        lines.append(f"- Error: {cache['error']}")
    return "\n".join(lines) + "\n"


def _output_base(output_prefix: str) -> Path:
    if output_prefix:
        return Path(output_prefix)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_DIR / f"{timestamp}-llm-runtime-validation"


def main() -> None:
    args = parse_args()
    report = asyncio.run(run_validation())
    output_base = _output_base(args.output_prefix)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    json_path = output_base.with_suffix(".json")
    md_path = output_base.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")

    print(f"Wrote validation JSON report to {json_path}")
    print(f"Wrote validation Markdown report to {md_path}")


if __name__ == "__main__":
    main()
