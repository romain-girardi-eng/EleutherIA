"""Tests for prompt templating — KG stats must come from data, not hardcoding."""

from types import SimpleNamespace

from eleutheria_graphrag.agents.prompts import (
    format_system_prompt,
    kg_scale_summary,
)
from eleutheria_graphrag.agents.react_loop import _native_system_prompt


def _kg_data(n_works: int, n_passages: int, n_other: int, n_edges: int) -> dict:
    nodes = (
        [{"type": "work"}] * n_works
        + [{"type": "passage"}] * n_passages
        + [{"type": "person"}] * n_other
    )
    return {"nodes": nodes, "edges": [{}] * n_edges}


class TestKgScaleSummary:
    def test_counts_come_from_kg_data(self):
        summary = kg_scale_summary(_kg_data(241, 17000, 2800, 56000))

        assert "~20k nodes" in summary
        assert "~56k edges" in summary
        assert "241 ancient works" in summary
        assert "~17k anchored passages" in summary

    def test_empty_snapshot_yields_count_free_description(self):
        summary = kg_scale_summary({})

        assert summary == "a knowledge graph and a corpus of ancient works"
        assert not any(ch.isdigit() for ch in summary)

    def test_none_is_accepted(self):
        assert "knowledge graph" in kg_scale_summary(None)


class TestSystemPromptTemplating:
    def test_text_loop_prompt_uses_live_counts(self):
        prompt = format_system_prompt(
            budget=7,
            remaining=7,
            tool_descriptions=[],
            kg_data=_kg_data(241, 17000, 2800, 56000),
        )

        assert "~20k nodes" in prompt
        assert "17,700" not in prompt
        assert "487" not in prompt

    def test_native_loop_prompt_uses_live_counts_and_inventory_contract(self):
        deps = SimpleNamespace(kg_data=_kg_data(241, 17000, 2800, 56000))

        prompt = _native_system_prompt(deps)

        assert "~20k nodes" in prompt
        assert "17,700" not in prompt
        assert "487" not in prompt
        # The loop's final text is not the user deliverable (react pipeline
        # synthesizes downstream) — the prompt must ask for an evidence
        # inventory, not a scholarly answer.
        assert "evidence inventory" in prompt
        assert "Coverage gaps" in prompt
        assert "NOT shown to the user" in prompt
