from eleutheria_graphrag.agents.state import (
    RAGState,
    ReasoningStep,
    RetrievalBudget,
)


def test_reasoning_step_creation():
    step = ReasoningStep(
        node_name="ClassifyQueryType",
        timestamp_ms=1000,
        duration_ms=340,
        model="gemini-3.1-pro-preview",
        prompt_summary="Classify the following query...",
        full_prompt_tokens=256,
        raw_output="Query type: COMPARATIVE",
        thinking=None,
        parsed_result={"query_type": "comparative"},
        skipped=False,
        skip_reason=None,
    )
    assert step.node_name == "ClassifyQueryType"
    assert step.duration_ms == 340
    assert step.thinking is None


def test_reasoning_step_skipped():
    step = ReasoningStep(
        node_name="SeekCounterEvidence",
        timestamp_ms=2000,
        duration_ms=0,
        model=None,
        prompt_summary="",
        full_prompt_tokens=0,
        raw_output="",
        thinking=None,
        parsed_result=None,
        skipped=True,
        skip_reason="SIMPLE complexity",
    )
    assert step.skipped is True
    assert step.skip_reason == "SIMPLE complexity"


def test_rag_state_has_reasoning_trace():
    state = RAGState()
    assert state.reasoning_trace == []
    assert state.retrieval_mode == "auto"
    assert state.selected_model == "gemini-3.1-pro"


def test_rag_state_accumulates_steps():
    state = RAGState()
    step = ReasoningStep(
        node_name="Test",
        timestamp_ms=0,
        duration_ms=100,
        model="test",
        prompt_summary="",
        full_prompt_tokens=0,
        raw_output="output",
        thinking=None,
        parsed_result=None,
        skipped=False,
        skip_reason=None,
    )
    state.reasoning_trace.append(step)
    assert len(state.reasoning_trace) == 1


def test_retrieval_budget_adapts_to_model_window():
    budget_1m = RetrievalBudget(model_window=1_000_000)
    budget_164k = RetrievalBudget(model_window=163_840)
    assert budget_1m.available_context_tokens() > budget_164k.available_context_tokens()
    assert budget_1m.passage_bundle_limit() > budget_164k.passage_bundle_limit()
