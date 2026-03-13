# Agentic Reading Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 8 correctness and quality issues identified in the code review of the agentic reading + ResearchGraph pivot.

**Architecture:** All fixes are isolated and non-breaking — no new abstractions, no API surface changes. Backend fixes are in `graph_nodes.py` and `scholarly_agent.py`; frontend fixes are in `ResearchGraphPanel.tsx` and `graphrag.ts`; new tests land in `test_graph_nodes.py`.

**Tech Stack:** Python 3.11, pydantic-graph, FastAPI, React 19 + TypeScript, pytest + pytest-asyncio

---

## Chunk 1: Backend correctness fixes

### Task 1: Guard against infinite recursion in `_verify_answer_programmatically`

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py:3532–3537`
- Test: `graphrag/tests/unit/test_graph_nodes.py`

The current code at lines 3532–3537 calls itself recursively without a depth limit. If `_render_answer_fallback` produces text with no valid refs, the function loops forever.

Fix: add a `_depth: int = 0` parameter, and on the recursive call pass `_depth + 1`. If `_depth > 0`, return the fallback directly without re-entering.

- [ ] **Step 1: Write the failing test**

Add to `class TestRenderAndVerify` in `graphrag/tests/unit/test_graph_nodes.py`:

```python
def test_verify_does_not_recurse_infinitely_when_fallback_has_no_refs(self):
    """If _render_answer_fallback yields no grounded refs, verification must not recurse."""
    state = RAGState(question="What is Stoic fate?")
    # No bundle_refs → no valid refs at all
    state.context_pack = ContextPack(bundle_refs={})
    state.raw_answer = "A line with no ref."
    state.claim_ledger = []  # fallback will emit nothing grounded
    # Must return (non-empty-or-empty string, []) without hanging
    answer, citations = _verify_answer_programmatically(state)
    assert citations == []
```

- [ ] **Step 2: Confirm the test hangs or fails** (set a `pytest-timeout` limit or observe stack overflow)

```bash
cd /Users/romaingirardi/Projects/EleutherIA
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestRenderAndVerify::test_verify_does_not_recurse_infinitely_when_fallback_has_no_refs -v --timeout=5
```

Expected: timeout or RecursionError.

- [ ] **Step 3: Apply the fix**

In `graph_nodes.py`, change the signature of `_verify_answer_programmatically`:

```python
# BEFORE (line 3448):
def _verify_answer_programmatically(state: RAGState) -> tuple[str, list[Citation]]:

# AFTER:
def _verify_answer_programmatically(state: RAGState, _depth: int = 0) -> tuple[str, list[Citation]]:
```

Change the recursive call block (lines 3532–3537):

```python
# BEFORE:
    if not kept_lines:
        fallback = _render_answer_fallback(state)
        state.raw_answer = fallback
        if not _extract_line_refs(fallback):
            return fallback, []
        return _verify_answer_programmatically(state)

# AFTER:
    if not kept_lines:
        fallback = _render_answer_fallback(state)
        state.raw_answer = fallback
        if _depth > 0 or not _extract_line_refs(fallback):
            return fallback, []
        return _verify_answer_programmatically(state, _depth=_depth + 1)
```

- [ ] **Step 4: Verify test passes**

```bash
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestRenderAndVerify::test_verify_does_not_recurse_infinitely_when_fallback_has_no_refs -v
```

Expected: PASS.

- [ ] **Step 5: Run full unit suite**

```bash
python -m pytest graphrag/tests/unit/ -q
```

Expected: all green, count ≥ 254.

- [ ] **Step 6: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/graph_nodes.py graphrag/tests/unit/test_graph_nodes.py
git commit -m "fix: guard _verify_answer_programmatically against infinite recursion"
```

---

### Task 2: Fix O(n²) in `_reverse_ref_maps`

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py:2710–2722`

The current implementation nests bundle iteration inside bundle_refs iteration (O(n²)). Replace both comprehensions with single-pass indexed lookups.

- [ ] **Step 1: Apply the fix**

Replace lines 2710–2723:

```python
# BEFORE:
def _reverse_ref_maps(state: RAGState) -> tuple[dict[str, EvidenceBundle], dict[str, Evidence]]:
    bundles_by_ref = {
        ref: bundle
        for bundle in state.context_pack.passage_bundles
        for bundle_id, ref in state.context_pack.bundle_refs.items()
        if bundle.bundle_id == bundle_id
    }
    nodes_by_ref = {
        ref: ev
        for ev in state.all_evidence()
        for node_id, ref in state.context_pack.node_refs.items()
        if ev.id == node_id
    }
    return bundles_by_ref, nodes_by_ref

# AFTER:
def _reverse_ref_maps(state: RAGState) -> tuple[dict[str, EvidenceBundle], dict[str, Evidence]]:
    bundle_index = {b.bundle_id: b for b in state.context_pack.passage_bundles}
    bundles_by_ref = {
        ref: bundle_index[bundle_id]
        for bundle_id, ref in state.context_pack.bundle_refs.items()
        if bundle_id in bundle_index
    }
    node_index = {ev.id: ev for ev in state.all_evidence()}
    nodes_by_ref = {
        ref: node_index[node_id]
        for node_id, ref in state.context_pack.node_refs.items()
        if node_id in node_index
    }
    return bundles_by_ref, nodes_by_ref
```

- [ ] **Step 2: Run full unit suite (output must be identical to before)**

```bash
python -m pytest graphrag/tests/unit/ -q
```

Expected: all green, count ≥ 254.

- [ ] **Step 3: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/graph_nodes.py
git commit -m "perf: fix O(n²) double-loop in _reverse_ref_maps"
```

---

### Task 3: Fix evidence_class not read from `_bundle_academic_features` in work card builder

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py:1645`
- Test: `graphrag/tests/unit/test_graph_nodes.py`

At line 1645, `bundle.metadata.get("evidence_class")` returns `None` for any bundle not explicitly marked by `SeekCounterEvidence`, so testimony bundles are misclassified as `primary`. The fix is to always call `_bundle_academic_features` (which already computes the class correctly).

- [ ] **Step 1: Write the failing test**

Add to `class TestHelpers` in `test_graph_nodes.py`:

```python
def test_build_research_graph_work_card_classifies_testimony_bundles_correctly(self):
    """Work cards must count testimony bundles under testimony_count, not primary_count."""
    state = RAGState(question="Who was Seneca?")
    # A bundle from Diogenes Laertius: ancient_testimony
    testimony_bundle = EvidenceBundle(
        bundle_id="bundle-dl",
        work_id="work_diogenes_laertius",
        work_title="Lives of Eminent Philosophers",
        author="Diogenes Laertius",
        original_passage_id="p1",
        canonical_ref="7.1",
        original_text="Zeno of Citium was the founder of Stoicism.",
        token_estimate=20,
    )
    # bundle_refs and context_pack
    state.context_pack = ContextPack(
        bundle_refs={"bundle-dl": "P1"},
        passage_bundles=[testimony_bundle],
    )
    state.evidence_bundles = [testimony_bundle]
    state.scholarly_dossier = ScholarlyDossier(
        facets=[
            DossierFacet(
                facet_id="f1",
                title="Main thesis",
                question="Q",
                primary_bundle_ids=["bundle-dl"],
            )
        ]
    )
    payload = _build_research_graph_payload(state)
    works = payload["works"]
    assert len(works) == 1
    work = works[0]
    assert work["testimony_count"] == 1
    assert work["primary_count"] == 0
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestHelpers::test_build_research_graph_work_card_classifies_testimony_bundles_correctly -v
```

Expected: FAIL (testimony_count == 0, primary_count == 1).

- [ ] **Step 3: Apply the fix**

In `graph_nodes.py`, replace line 1645:

```python
# BEFORE:
        evidence_class = str(bundle.metadata.get("evidence_class") or bundle.evidence_role or "direct_text")

# AFTER:
        evidence_class = _bundle_academic_features(bundle, state)["evidence_class"]
```

- [ ] **Step 4: Verify test passes**

```bash
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestHelpers::test_build_research_graph_work_card_classifies_testimony_bundles_correctly -v
```

Expected: PASS.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest graphrag/tests/unit/ -q
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/graph_nodes.py graphrag/tests/unit/test_graph_nodes.py
git commit -m "fix: use _bundle_academic_features for evidence_class in work card builder"
```

---

### Task 4: Add `claim_ledger_size` to `query_stream` metadata

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py:135–143`
- Test: `graphrag/tests/unit/test_graph_nodes.py` (or a dedicated `test_scholarly_agent.py`)

`query_dict` includes `"claim_ledger_size": len(answer.claim_ledger)` but `query_stream`'s `complete_data` does not. Any frontend reading this from SSE gets `undefined`.

- [ ] **Step 1: Write the failing test**

Add a new test file `graphrag/tests/unit/test_scholarly_agent.py`:

```python
"""Tests for ScholarlyAgent facade."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)


def make_mock_deps():
    deps = MagicMock()
    deps.llm.last_model_used = "gemini-2.5-flash"
    deps.llm.last_provider_used = "google"
    return deps


@pytest.mark.asyncio
async def test_query_stream_includes_claim_ledger_size():
    """query_stream complete payload must include claim_ledger_size."""
    deps = make_mock_deps()
    agent = ScholarlyAgent(deps)

    answer = ScholarlyAnswer(
        answer="Stoic fate [P1].",
        question="What is fate?",
        claim_ledger=[
            ClaimLedgerItem(
                claim="Stoic fate is determinism.",
                evidence_ids=["P1"],
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ],
    )
    with patch.object(agent, "query", new=AsyncMock(return_value=answer)):
        chunks = [chunk async for chunk in agent.query_stream("What is fate?")]

    complete_chunk = next(c for c in chunks if c.startswith("{"))
    data = json.loads(complete_chunk)
    assert data["type"] == "complete"
    assert data["data"]["metadata"]["claim_ledger_size"] == 1
```

- [ ] **Step 2: Run test to confirm failure**

```bash
python -m pytest graphrag/tests/unit/test_scholarly_agent.py::test_query_stream_includes_claim_ledger_size -v
```

Expected: FAIL (KeyError or assertion error).

- [ ] **Step 3: Apply the fix**

In `scholarly_agent.py`, add `claim_ledger_size` to the `complete_data` metadata dict (line 143 area):

```python
# BEFORE:
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
            },

# AFTER:
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
                "claim_ledger_size": len(answer.claim_ledger),
            },
```

- [ ] **Step 4: Verify test passes**

```bash
python -m pytest graphrag/tests/unit/test_scholarly_agent.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py graphrag/tests/unit/test_scholarly_agent.py
git commit -m "fix: add claim_ledger_size to query_stream complete payload"
```

---

## Chunk 2: Missing test coverage

### Task 5: Test `_quality_badge_from_state` High and Medium paths

**Files:**
- Test: `graphrag/tests/unit/test_graph_nodes.py`

Only the `pipeline_degraded → Low` path is covered. The `score >= 80 and citations → High` and `score >= 60 → Medium` paths have no tests.

- [ ] **Step 1: Add tests to `class TestHelpers`**

```python
def test_quality_badge_high_when_score_80_and_citations(self):
    from eleutheria_graphrag.agents.state import Citation
    state = RAGState()
    state.sufficiency_score = 0.85
    state.citations = [Citation(ref="P1", work_title="De Fato", author="Cicero", canonical_ref="1.1")]
    state.metadata["pipeline_degraded"] = False
    assert _quality_badge_from_state(state) == "High"

def test_quality_badge_medium_when_score_60_no_citations(self):
    state = RAGState()
    state.sufficiency_score = 0.65
    state.citations = []
    assert _quality_badge_from_state(state) == "Medium"

def test_quality_badge_low_when_score_below_60(self):
    state = RAGState()
    state.sufficiency_score = 0.5
    state.citations = []
    assert _quality_badge_from_state(state) == "Low"
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestHelpers::test_quality_badge_high_when_score_80_and_citations graphrag/tests/unit/test_graph_nodes.py::TestHelpers::test_quality_badge_medium_when_score_60_no_citations graphrag/tests/unit/test_graph_nodes.py::TestHelpers::test_quality_badge_low_when_score_below_60 -v
```

Expected: PASS (no code change needed, these are pure state tests).

- [ ] **Step 3: Commit**

```bash
git add graphrag/tests/unit/test_graph_nodes.py
git commit -m "test: cover High/Medium/Low paths of _quality_badge_from_state"
```

---

### Task 6: Test `SeekCounterEvidence` marks `evidence_class` in bundle metadata

**Files:**
- Test: `graphrag/tests/unit/test_graph_nodes.py`

`SeekCounterEvidence` sets `bundle.metadata["evidence_class"] = "counter_evidence"` at line 4740, but there's no test verifying this behaviour.

- [ ] **Step 1: Add test class**

```python
class TestSeekCounterEvidence:
    @pytest.mark.asyncio
    async def test_marks_selected_bundles_as_counter_evidence_in_metadata(self):
        """Selected bundles must have evidence_class=counter_evidence in metadata."""
        bundle_a = EvidenceBundle(
            bundle_id="bundle-a",
            work_id="work-1",
            work_title="De Fato",
            author="Cicero",
            original_passage_id="p1",
            canonical_ref="1.1",
            original_text="Fate rules all.",
            token_estimate=20,
        )
        bundle_b = EvidenceBundle(
            bundle_id="bundle-b",
            work_id="work-2",
            work_title="De Principiis",
            author="Origen",
            original_passage_id="p2",
            canonical_ref="3.1.5",
            original_text="Free will contradicts fate.",
            token_estimate=20,
        )
        state = RAGState(question="Is fate compatible with free will?")
        state.evidence_bundles = [bundle_a, bundle_b]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-a": "P1", "bundle-b": "P2"},
            passage_bundles=[bundle_a, bundle_b],
        )
        state.research_notebook.competing_hypotheses = ["Fate is compatible", "Fate is incompatible"]

        # LLM returns bundle-b as counter-evidence
        deps = make_deps(llm_response='{"bundle_ids": ["bundle-b"], "rationale": "Origen rejects fate"}')
        ctx = make_ctx(state, deps)

        result = await SeekCounterEvidence().run(ctx)

        assert isinstance(result, EvidenceSufficiency)
        assert bundle_b.metadata.get("evidence_class") == "counter_evidence"
        assert bundle_a.metadata.get("evidence_class") != "counter_evidence"

    @pytest.mark.asyncio
    async def test_skips_when_no_competing_hypotheses(self):
        """SeekCounterEvidence must skip (return EvidenceSufficiency) when notebook has no hypotheses."""
        state = RAGState(question="What is Stoic fate?")
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-a",
                work_id="work-1",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p1",
                canonical_ref="1.1",
                original_text="Fate is a chain of causes.",
                token_estimate=20,
            )
        ]
        state.research_notebook.competing_hypotheses = []
        deps = make_deps()
        ctx = make_ctx(state, deps)

        result = await SeekCounterEvidence().run(ctx)
        assert isinstance(result, EvidenceSufficiency)
```

- [ ] **Step 2: Run the tests**

```bash
python -m pytest graphrag/tests/unit/test_graph_nodes.py::TestSeekCounterEvidence -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add graphrag/tests/unit/test_graph_nodes.py
git commit -m "test: cover SeekCounterEvidence evidence_class marking and skip path"
```

---

## Chunk 3: Frontend fixes

### Task 7: Add `uncertainty_count` MetricPill to FacetCard

**Files:**
- Modify: `frontend/src/components/graphrag/ResearchGraphPanel.tsx:262–266`

`uncertainty_count` is in the TS type and emitted by the backend but never displayed.

- [ ] **Step 1: Apply the fix**

In `ResearchGraphPanel.tsx`, inside `FacetCard`, add one line after the `note_count` pill:

```tsx
// BEFORE (lines 262–266):
        <MetricPill label="direct" value={facet.primary_count} />
        <MetricPill label="testimony" value={facet.testimony_count} />
        <MetricPill label="counter" value={facet.counter_count} />
        <MetricPill label="metadata" value={facet.metadata_count} />
        <MetricPill label="notes" value={facet.note_count} />

// AFTER:
        <MetricPill label="direct" value={facet.primary_count} />
        <MetricPill label="testimony" value={facet.testimony_count} />
        <MetricPill label="counter" value={facet.counter_count} />
        <MetricPill label="metadata" value={facet.metadata_count} />
        <MetricPill label="notes" value={facet.note_count} />
        <MetricPill label="uncertain" value={facet.uncertainty_count} />
```

- [ ] **Step 2: Build the frontend to confirm no TS errors**

```bash
npm --prefix /Users/romaingirardi/Projects/EleutherIA/frontend run build
```

Expected: build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/graphrag/ResearchGraphPanel.tsx
git commit -m "fix: display uncertainty_count pill in FacetCard"
```

---

### Task 8: Remove spurious `?` from `ResearchGraphOverview` fields

**Files:**
- Modify: `frontend/src/types/graphrag.ts:101–118`

All fields in `ResearchGraphOverview` are declared optional (`?`) but `_build_research_graph_payload` always emits every field. The optional markers create unnecessary null-guard boilerplate in component code.

- [ ] **Step 1: Apply the fix**

Replace the `ResearchGraphOverview` interface in `graphrag.ts`:

```typescript
// BEFORE:
export interface ResearchGraphOverview {
  query_type?: string;
  complexity?: string;
  grounding_policy?: string;
  quality_badge?: string;
  pipeline_degraded?: boolean;
  claim_ledger_mode?: string;
  render_answer_mode?: string;
  scholarly_polish_mode?: string;
  seed_node_count?: number;
  context_node_count?: number;
  bundle_count?: number;
  work_count?: number;
  claim_count?: number;
  citation_count?: number;
  tool_call_count?: number;
  decision_count?: number;
}

// AFTER:
export interface ResearchGraphOverview {
  query_type: string;
  complexity: string;
  grounding_policy: string;
  quality_badge: string;
  pipeline_degraded: boolean;
  claim_ledger_mode: string;
  render_answer_mode: string;
  scholarly_polish_mode: string;
  seed_node_count: number;
  context_node_count: number;
  bundle_count: number;
  work_count: number;
  claim_count: number;
  citation_count: number;
  tool_call_count: number;
  decision_count: number;
}
```

- [ ] **Step 2: Build the frontend to confirm no TS errors**

```bash
npm --prefix /Users/romaingirardi/Projects/EleutherIA/frontend run build
```

If TypeScript reports errors about places that access these fields with optional chaining (`?.`), remove the unnecessary `?.` operators — they are now guaranteed non-null. If the compiler reports errors on access sites where these fields might legitimately come from a legacy or partial response, revert only those specific fields to optional.

Expected: clean build.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/graphrag.ts
git commit -m "fix: make ResearchGraphOverview fields non-optional (always emitted by backend)"
```

---

## Final verification

- [ ] **Run full Python test suite**

```bash
cd /Users/romaingirardi/Projects/EleutherIA
python -m pytest graphrag/tests/ -q
```

Expected: all green, count ≥ 258 (254 existing + 4 new quality_badge + 2 seek_counter + recursion guard).

- [ ] **Run frontend build**

```bash
npm --prefix frontend run build
```

Expected: clean build.

- [ ] **Run linter**

```bash
ruff check graphrag/src/eleutheria_graphrag/agents/graph_nodes.py graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py graphrag/tests/unit/test_graph_nodes.py graphrag/tests/unit/test_scholarly_agent.py
```

Expected: no errors.
