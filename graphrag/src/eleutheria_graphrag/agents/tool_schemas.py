"""
OpenAI-style tool/function schemas for the EleutherIA agent.

Each registered tool exposes a JSON Schema via ``parameters_schema``; this module
re-wraps those schemas in the OpenAI ``{"type": "function", "function": {...}}``
envelope used by Fireworks (Kimi K2.6) and any OpenAI-compatible provider.

Used by the native tool-calling path in ``react_loop.py``.
"""

from __future__ import annotations

from typing import Any

from eleutheria_graphrag.agents.tools import ToolRegistry


def build_tool_function_schemas(tools: ToolRegistry) -> list[dict[str, Any]]:
    """Return OpenAI-format function schemas for every tool in the registry.

    Output shape per tool::

        {
            "type": "function",
            "function": {
                "name": str,
                "description": str,
                "parameters": <JSON Schema>,
            },
        }
    """
    schemas: list[dict[str, Any]] = []
    for tool in tools._tools.values():  # noqa: SLF001 — registry exposes no iterator
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": _normalize_schema(tool.parameters_schema),
                },
            }
        )
    return schemas


def _normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize a JSON Schema for OpenAI / Fireworks function-calling.

    Some providers reject schemas that omit ``type`` at the top level or that
    use ``minItems`` / ``maxItems`` on items they cannot enforce. We keep the
    structure intact but ensure ``type: object`` is set.
    """
    normalized = dict(schema)
    normalized.setdefault("type", "object")
    if "properties" not in normalized:
        normalized["properties"] = {}
    return normalized
