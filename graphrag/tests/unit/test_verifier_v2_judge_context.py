"""The v2 verifier as a scholar-judge: whole-argument context and fetch-on-demand.

Fixtures replay the production false rejections adjudicated by hand: in a
multi-source sentence the citation of one proposition was rejected because
its evidence "says nothing about" the proposition another citation carries.
The assertions are on WHAT THE JUDGE IS SHOWN (the isolated proposition, the
companion sources, the sentence and paragraph, the verdict-scope rule) — the
LLM is a stub. The three legitimate rejections stay rejected, and the prompt
still exposes their mismatch. The tool loop is exercised with stubbed
``generate_with_tools`` / ``generate`` responses: fetch then verdict, budget
exhaustion, tool error, provider fallback.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _aggregate_tool_calls,
    _draft_claim_for,
)
from eleutheria_graphrag.agents.state import Citation, ScholarlyAnswer
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    CompanionRef,
    DraftClaim,
    SynthesizedDraft,
    VerificationReport,
)
from eleutheria_graphrag.services.citation_verifier_v2 import (
    VERDICT_JSON_SCHEMA,
    CitationVerifierV2,
    build_corpus_search,
    build_graph_neighbors,
)
from eleutheria_graphrag.services.llm_service import LLMService
from tests.unit.conftest import make_deps

# --------------------------------------------------------------------------- helpers


def _verdict(status: str, reasoning: str = "stub", **extra: Any) -> str:
    return json.dumps({"status": status, "reasoning": reasoning, **extra})


def _llm(*responses: str) -> AsyncMock:
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=list(responses))
    return llm


def _fetcher(evidence: dict[str, dict[str, Any] | None]) -> Any:
    async def fetch(citation_id: str) -> dict[str, Any] | None:
        record = evidence.get(citation_id)
        return dict(record) if record else None

    return fetch


def _passage(text: str, label: str = "") -> dict[str, Any]:
    return {"text": text, "label": label or "passage"}


def _node(text: str, label: str, node_type: str = "argument") -> dict[str, Any]:
    return {
        "kind": "node",
        "text": text,
        "label": label,
        "node_type": node_type,
        "text_chars": len(text),
    }


def _citation(ref: str, cid: str, label: str, kind: str = "node") -> Citation:
    return Citation(ref=ref, type=kind, id=cid, label=label)


def _answer(text: str, *citations: Citation) -> ScholarlyAnswer:
    return ScholarlyAnswer(answer=text, question="q", citations=list(citations))


async def _audit(
    answer: ScholarlyAnswer,
    citation: Citation,
    evidence: dict[str, dict[str, Any] | None],
    *,
    verdict: str = "VERIFIED",
    **verifier_kwargs: Any,
) -> tuple[CitationCheck, str]:
    """Audit ``citation`` inside ``answer`` with a stubbed judge; return the
    check and the prompt the judge saw."""
    llm = _llm(_verdict(verdict))
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=_fetcher(evidence), **verifier_kwargs
    )
    sentence = answer.answer
    claim = _draft_claim_for(answer, citation, sentence)
    report = await verifier.verify_draft(SynthesizedDraft(claims=[claim]))
    prompt = llm.generate.call_args.args[0]
    return report.checks[0], prompt


def _proposition(prompt: str) -> str:
    """The text of the 'Proposition being audited' section of the prompt."""
    head = prompt.split("Proposition being audited", 1)[1]
    body = head.split(":\n", 1)[1]
    return body.split("\n", 1)[0]


# ----------------------------------------------------- the five false rejections


NASCIMENTO = (
    "Nascimento argues that the passage distinguishes the involuntary "
    "reception of impressions from the rational judgment governing their use."
)
FURST = (
    "Fürst places the same argument within Origen's campaign against "
    "astrological, Stoic-causal and Gnostic-theological determination."
)


@pytest.mark.asyncio
async def test_nascimento_is_judged_on_its_own_proposition_with_furst_beside() -> None:
    text = (
        "Nascimento reads this as an argument that distinguishes the "
        "involuntary reception of impressions from the rational judgment "
        "governing their use [N1], whereas Fürst's 2022 dissertation places "
        "the same argument within Origen's campaign against astrological, "
        "Stoic-causal, and Gnostic-theological determination [N2]."
    )
    nascimento = _citation("N1", "scholarly_argument_nascimento", "Nascimento")
    furst = _citation("N2", "scholarly_argument_furst_2022", "Fürst 2022")
    check, prompt = await _audit(
        _answer(text, nascimento, furst),
        nascimento,
        {
            nascimento.id: _node(NASCIMENTO, "Nascimento"),
            furst.id: _node(FURST, "Fürst 2022"),
        },
    )

    assert check.status is CitationStatus.VERIFIED
    # The proposition handed to the judge is Nascimento's clause only.
    proposition = _proposition(prompt)
    assert proposition.startswith("Nascimento reads this as an argument")
    assert "Fürst" not in proposition
    # The whole sentence and Fürst's evidence are there as context.
    assert "Full sentence (context" in prompt
    assert text in prompt
    assert "Companion sources cited in the same sentence" in prompt
    assert "[N2] Fürst 2022 (graph statement)" in prompt
    assert FURST in prompt
    assert '<companion id="companion:scholarly_argument_furst_2022">' in prompt
    # The verdict-scope rule.
    assert "Never reject this citation because its evidence says nothing" in prompt
    assert check.companion_ids == [furst.id]
    assert check.sentence == text
    assert check.claim == proposition


@pytest.mark.asyncio
async def test_dihle_sees_irwin_and_frede_carried_by_their_own_markers() -> None:
    # Three adjacent markers after the period: one group, the whole sentence
    # is the shared clause, and every companion's evidence is shown.
    text = (
        "Irwin objects that this conclusion may merely identify the absence "
        "of a voluntarist theory, not the absence of every conception of "
        "will, while Frede relocates the principal innovation to Epictetus. "
        "[N1] [N2] [N3]"
    )
    dihle = _citation("N1", "scholar_dihle", "Dihle 1982")
    irwin = _citation("N2", "scholarly_argument_irwin", "Irwin 1992")
    frede = _citation("N3", "scholarly_argument_frede", "Frede 2011")
    check, prompt = await _audit(
        _answer(text, dihle, irwin, frede),
        dihle,
        {
            dihle.id: _node(
                "Dihle argues that classical Greek had no concept of the will; "
                "the notion emerges only with Augustine.",
                "Dihle 1982",
            ),
            irwin.id: _node(
                "Irwin objects that Dihle's thesis may only show the absence of "
                "a voluntarist theory, not of every conception of will.",
                "Irwin 1992",
            ),
            frede.id: _node(
                "Frede relocates the invention of the notion of a free will to "
                "Epictetus rather than Augustine.",
                "Frede 2011",
            ),
        },
    )

    assert check.status is CitationStatus.VERIFIED
    assert "[N2] Irwin 1992 (graph statement)" in prompt
    assert "Irwin objects that Dihle's thesis" in prompt
    assert "[N3] Frede 2011 (graph statement)" in prompt
    assert "Frede relocates the invention" in prompt
    assert check.companion_ids == [irwin.id, frede.id]


@pytest.mark.asyncio
async def test_bobzien_quote_is_audited_without_the_origen_inference() -> None:
    quote = (
        "“The faculty of assent is the power of either confirming the "
        "impression or withholding such confirmation.”"
    )
    text = (
        f"{quote} [P_scholarly_argument_bobzien_2001: Bobzien 2001, pp. 239-242] "
        "Origen's conceptual vocabulary is therefore continuous with the Stoic "
        "analysis of assent."
    )
    bobzien = _citation("P1", "scholarly_argument_bobzien_2001", "Bobzien 2001")
    answer = _answer(text, bobzien)
    evidence = {
        bobzien.id: _node(
            "Bobzien: the faculty of assent is the power of either confirming "
            "the impression or withholding such confirmation.",
            "Bobzien 2001",
        )
    }
    llm = _llm(_verdict("VERIFIED"))
    verifier = CitationVerifierV2(llm=llm, passage_fetcher=_fetcher(evidence))
    agent = ScholarlyAgent(make_deps())
    agent.deps.verifier_v2 = verifier

    updated, report = await agent._run_citation_verifier_v2(answer)

    prompt = llm.generate.call_args.args[0]
    proposition = _proposition(prompt)
    assert proposition == quote
    assert "Origen" not in proposition
    # The inference stays visible as paragraph context.
    assert "Surrounding paragraph of the draft" in prompt
    assert "continuous with the Stoic analysis" in prompt
    assert "the inference is not the citation's burden" in prompt
    assert report is not None and report.checks[0].status is CitationStatus.VERIFIED
    assert updated.metadata["citation_verifier_v2"]["clauses_isolated"] == 1


@pytest.mark.asyncio
async def test_bobzien_is_shown_long_when_long_endorses_bobzien() -> None:
    text = (
        "Long expressly endorses Bobzien's judgment that Epictetus is not "
        "offering a new intervention in a metaphysical debate [N1] [N2]."
    )
    long_ = _citation("N1", "scholarly_argument_long_2002", "Long 2002")
    bobzien = _citation("N2", "scholarly_argument_bobzien_1998", "Bobzien 1998")
    long_text = (
        "Long endorses Bobzien's judgment that Epictetus does not intervene "
        "in the metaphysical debate on determinism."
    )
    check, prompt = await _audit(
        _answer(text, long_, bobzien),
        bobzien,
        {
            long_.id: _node(long_text, "Long 2002"),
            bobzien.id: _node(
                "Bobzien argues that Epictetus's freedom is not a contribution "
                "to the determinism debate.",
                "Bobzien 1998",
            ),
        },
    )

    assert check.status is CitationStatus.VERIFIED
    assert _proposition(prompt).startswith("Long expressly endorses")
    assert "[N1] Long 2002 (graph statement)" in prompt
    assert long_text in prompt
    assert check.companion_ids == [long_.id]


@pytest.mark.asyncio
async def test_frede_is_not_burdened_with_the_bobzien_quotation() -> None:
    text = (
        "Frede locates the invention of the notion of a free will in "
        "Epictetus [N1], whereas Bobzien writes that 'the development of the "
        "concept of the will did not spring from' a single source [N2]."
    )
    frede = _citation("N1", "scholarly_argument_frede", "Frede 2011")
    bobzien = _citation("N2", "scholarly_argument_bobzien_1998", "Bobzien 1998")
    check, prompt = await _audit(
        _answer(text, frede, bobzien),
        frede,
        {
            frede.id: _node(
                "Frede argues that the notion of a free will was invented by "
                "Epictetus.",
                "Frede 2011",
            ),
            bobzien.id: _node(
                "Bobzien writes that the development of the concept of the "
                "will did not spring from one source.",
                "Bobzien 1998",
            ),
        },
    )

    assert check.status is CitationStatus.VERIFIED
    proposition = _proposition(prompt)
    assert proposition == (
        "Frede locates the invention of the notion of a free will in Epictetus"
    )
    assert "did not spring from" not in proposition
    assert "[N2] Bobzien 1998 (graph statement)" in prompt


# ---------------------------------------------------- the three legitimate ones


@pytest.mark.asyncio
async def test_salles_claim_cited_to_ramelli_stays_rejected() -> None:
    text = "Salles argues that Chrysippean fate leaves assent genuinely up to us [N1]."
    ramelli = _citation("N1", "scholarly_argument_ramelli", "Ramelli 2009")
    ramelli_text = (
        "Ramelli argues that Origen's doctrine of apokatastasis presupposes "
        "the freedom of rational creatures."
    )
    check, prompt = await _audit(
        _answer(text, ramelli),
        ramelli,
        {ramelli.id: _node(ramelli_text, "Ramelli 2009")},
        verdict="REJECTED",
    )

    assert check.status is CitationStatus.REJECTED
    assert "Salles argues" in _proposition(prompt)
    assert ramelli_text in prompt
    assert "Companion sources" not in prompt
    assert "a proposition ABOUT a different author" in prompt


@pytest.mark.asyncio
async def test_origen_inference_cited_to_a_chrysippus_record_stays_rejected() -> None:
    text = (
        "Chrysippus distinguishes perfect from auxiliary causes [P1], so "
        "Origen too holds that assent remains up to us under fate [P2]."
    )
    chrysippus = _citation("P1", "p_cicero_fat_41", "Cicero, Fat. 41", "passage")
    chrysippus_2 = _citation("P2", "p_cicero_fat_43", "Cicero, Fat. 43", "passage")
    fat_43 = (
        "Chrysippus says that assent, though it cannot occur without an "
        "impression, has as its principal cause our own nature."
    )
    check, prompt = await _audit(
        _answer(text, chrysippus, chrysippus_2),
        chrysippus_2,
        {
            chrysippus.id: _passage(
                "Chrysippus distinguishes perfect and principal causes from "
                "auxiliary and proximate causes."
            ),
            chrysippus_2.id: _passage(fat_43),
        },
        verdict="REJECTED",
    )

    assert check.status is CitationStatus.REJECTED
    proposition = _proposition(prompt)
    assert proposition.startswith("so Origen too holds")
    assert fat_43 in prompt
    assert '<passage id="citation:p_cicero_fat_43">' in prompt


@pytest.mark.asyncio
async def test_origen_claim_cited_to_bobzien_record_stays_rejected() -> None:
    text = (
        "Origen holds that the soul's self-motion is the root of responsibility [N1]."
    )
    bobzien = _citation("N1", "scholarly_argument_bobzien_mr", "Bobzien 1998")
    bobzien_text = (
        "Bobzien distinguishes two Stoic notions of moral responsibility, MR1 "
        "and MR2, neither of which requires an ability to do otherwise."
    )
    check, prompt = await _audit(
        _answer(text, bobzien),
        bobzien,
        {bobzien.id: _node(bobzien_text, "Bobzien 1998")},
        verdict="REJECTED",
    )

    assert check.status is CitationStatus.REJECTED
    assert "Origen holds" in _proposition(prompt)
    assert bobzien_text in prompt
    assert "supports the claim AS ATTRIBUTED" in prompt


# ----------------------------------------------------------------- draft claim


def test_draft_claim_carries_clause_sentence_context_and_companions() -> None:
    text = (
        "Intro paragraph.\n\n"
        "Nascimento reads this one way [N1], whereas Fürst reads it another "
        "[N2]. A following sentence.\n\n"
        "Closing paragraph."
    )
    nascimento = _citation("N1", "n_nascimento", "Nascimento")
    furst = _citation("N2", "n_furst", "Fürst 2022", "node")
    answer = _answer(text, nascimento, furst)
    sentence = (
        "Nascimento reads this one way [N1], whereas Fürst reads it another [N2]."
    )

    claim = _draft_claim_for(answer, furst, sentence)

    assert claim.claim == "whereas Fürst reads it another"
    assert claim.sentence == sentence
    assert claim.context == (
        "Nascimento reads this one way [N1], whereas Fürst reads it another "
        "[N2]. A following sentence."
    )
    assert claim.companions == [
        CompanionRef(
            citation_id="n_nascimento",
            marker="N1",
            label="Nascimento",
            citation_kind="node",
        )
    ]
    assert claim.citation_id == "n_furst"


@pytest.mark.asyncio
async def test_companions_are_capped_and_missing_ones_are_named() -> None:
    claim = DraftClaim(
        claim="X argues A",
        sentence="X argues A [N1], B [N2], C [N3], D [N4].",
        citation_id="n1",
        citation_kind="node",
        companions=[
            CompanionRef(citation_id="n2", marker="N2", label="Two"),
            CompanionRef(
                citation_id="n3", marker="N3", label="Three", citation_kind="node"
            ),
            CompanionRef(citation_id="n4", marker="N4", label="Four"),
        ],
    )
    llm = _llm(_verdict("VERIFIED"))
    verifier = CitationVerifierV2(
        llm=llm,
        passage_fetcher=_fetcher(
            {
                "n1": _node("X argues A at length in the record.", "One"),
                "n2": _node("Two says B in its own record.", "Two"),
                "n4": _node("Four says D.", "Four"),
            }
        ),
        max_companions=2,
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[claim]))

    prompt = llm.generate.call_args.args[0]
    assert "[N2] Two (graph statement)" in prompt
    assert "Two says B in its own record." in prompt
    assert "[N3] Three (graph statement): no citable evidence resolved" in prompt
    assert "Four" not in prompt
    assert report.checks[0].companion_ids == ["n2", "n3"]


# ------------------------------------------------------------------- tool loop


def _tool_call(name: str, args: dict[str, Any], call_id: str = "c1") -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def _assistant(content: str | None = None, *calls: dict[str, Any]) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if calls:
        message["tool_calls"] = list(calls)
    return message


SALLES_CLAIM = DraftClaim(
    claim="Salles argues that Chrysippean fate leaves assent up to us",
    citation_id="scholarly_argument_salles",
    citation_kind="node",
)
SALLES_EVIDENCE = {
    "scholarly_argument_salles": _node(
        "Salles argues that Chrysippus's compatibilism keeps assent up to us.",
        "Salles 2005",
    ),
    "scholar_chrysippus": _node(
        "Chrysippus, third head of the Stoa, author of the theory of fate as "
        "the chain of causes.",
        "Chrysippus",
        "person",
    ),
}


@pytest.mark.asyncio
async def test_native_loop_fetches_a_node_then_verdicts() -> None:
    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            _assistant(
                None, _tool_call("fetch_node", {"node_id": "scholar_chrysippus"})
            ),
            _assistant(_verdict("VERIFIED", "record states the position")),
        ]
    )
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=_fetcher(SALLES_EVIDENCE), tool_mode="native"
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    check = report.checks[0]
    assert check.status is CitationStatus.VERIFIED
    assert check.tool_calls == [
        {"tool": "fetch_node", "args": {"node_id": "scholar_chrysippus"}, "hit": True}
    ]
    llm.generate.assert_not_called()
    assert llm.generate_with_tools.await_count == 2
    first_args, first_kwargs = llm.generate_with_tools.await_args_list[0]
    messages, tools = first_args
    assert [t["function"]["name"] for t in tools] == ["fetch_passage", "fetch_node"]
    assert first_kwargs["tool_choice"] == "auto"
    assert first_kwargs["tier"] == "synthesis"
    assert (
        "call the tools (fetch_passage, fetch_node); at most 3 calls"
        in (messages[1]["content"])
    )
    # The second turn carries the assistant call and the tool result.
    second_messages = llm.generate_with_tools.await_args_list[1].args[0]
    assert second_messages[2]["role"] == "assistant"
    assert second_messages[3]["role"] == "tool"
    assert second_messages[3]["tool_call_id"] == "c1"
    result = json.loads(second_messages[3]["content"])
    assert result["hit"] is True
    assert "third head of the Stoa" in result["text"]
    assert '<tool-result id="tool:fetch_node:scholar_chrysippus">' in result["text"]


@pytest.mark.asyncio
async def test_native_budget_exhaustion_forces_the_verdict() -> None:
    call = _tool_call("fetch_node", {"node_id": "scholar_chrysippus"})
    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            _assistant(None, call),
            _assistant(None, call),
            _assistant(None, call),
            _assistant(None, call),  # refused: budget spent
            _assistant(_verdict("WEAK", "could not settle the scope")),
        ]
    )
    verifier = CitationVerifierV2(
        llm=llm,
        passage_fetcher=_fetcher(SALLES_EVIDENCE),
        tool_mode="native",
        max_tool_calls=3,
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    check = report.checks[0]
    assert check.status is CitationStatus.WEAK
    assert not check.parse_error
    assert len(check.tool_calls) == 3
    assert "verdict forced after the tool budget of 3 calls was exhausted" in (
        check.reasoning
    )
    choices = [
        kwargs["tool_choice"] for _, kwargs in llm.generate_with_tools.await_args_list
    ]
    assert choices == ["auto", "auto", "auto", "none", "none"]
    fourth_messages = llm.generate_with_tools.await_args_list[3].args[0]
    assert fourth_messages[-1]["role"] == "user"
    assert "Tool budget exhausted" in fourth_messages[-1]["content"]
    refused = json.loads(
        llm.generate_with_tools.await_args_list[4].args[0][-2]["content"]
    )
    assert "Tool budget exhausted" in refused["error"]


@pytest.mark.asyncio
async def test_tool_error_fails_closed_to_weak() -> None:
    async def fetch(citation_id: str) -> dict[str, Any] | None:
        if citation_id == "scholar_chrysippus":
            raise RuntimeError("DB connection died")
        return SALLES_EVIDENCE.get(citation_id)

    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            _assistant(
                None, _tool_call("fetch_node", {"node_id": "scholar_chrysippus"})
            ),
            _assistant(_verdict("VERIFIED", "never reached")),
        ]
    )
    verifier = CitationVerifierV2(llm=llm, passage_fetcher=fetch, tool_mode="native")

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    check = report.checks[0]
    assert check.status is CitationStatus.WEAK
    assert check.parse_error is True
    assert "fetch_node failed" in check.reasoning
    assert check.suggested_action == "manual review"
    assert check.tool_calls == [
        {
            "tool": "fetch_node",
            "args": {"node_id": "scholar_chrysippus"},
            "hit": False,
            "error": "DB connection died",
        }
    ]
    assert llm.generate_with_tools.await_count == 1


@pytest.mark.asyncio
async def test_unknown_tool_costs_nothing_and_is_answered() -> None:
    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            _assistant(None, _tool_call("search_corpus", {"query": "assent"})),
            _assistant(_verdict("VERIFIED")),
        ]
    )
    # search_corpus is not wired → not offered → unknown to the session.
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=_fetcher(SALLES_EVIDENCE), tool_mode="native"
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    assert report.checks[0].status is CitationStatus.VERIFIED
    assert report.checks[0].tool_calls == []
    answered = json.loads(
        llm.generate_with_tools.await_args_list[1].args[0][-1]["content"]
    )
    assert "unknown tool" in answered["error"]


@pytest.mark.asyncio
async def test_native_unavailable_falls_back_to_the_json_round() -> None:
    llm = AsyncMock(spec=LLMService)
    llm.generate_with_tools = AsyncMock(
        side_effect=RuntimeError(
            "No OpenAI-compatible provider available for tool-calling"
        )
    )
    llm.generate = AsyncMock(return_value=_verdict("VERIFIED"))
    verifier = CitationVerifierV2(llm=llm, passage_fetcher=_fetcher(SALLES_EVIDENCE))

    report = await verifier.verify_draft(
        SynthesizedDraft(claims=[SALLES_CLAIM, SALLES_CLAIM])
    )

    assert [c.status for c in report.checks] == [CitationStatus.VERIFIED] * 2
    # Fallback is remembered: the second citation skips the native attempt.
    assert llm.generate_with_tools.await_count == 1
    assert llm.generate.await_count == 2
    prompt = llm.generate.await_args.args[0]
    assert 'a "requests" array of up to 3 items' in prompt
    assert llm.generate.await_args.kwargs["response_json_schema"] is VERDICT_JSON_SCHEMA


@pytest.mark.asyncio
async def test_json_round_serves_requests_then_reasks() -> None:
    llm = _llm(
        _verdict(
            "WEAK",
            "need the passage",
            requests=[{"tool": "fetch_passage", "args": {"passage_id": "p_fat_43"}}],
        ),
        _verdict("VERIFIED", "the passage settles it"),
    )
    evidence = {
        **SALLES_EVIDENCE,
        "p_fat_43": _passage("Chrysippus says assent is in our power.", "Fat. 43"),
    }
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=_fetcher(evidence), tool_mode="json"
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    check = report.checks[0]
    assert check.status is CitationStatus.VERIFIED
    assert check.tool_calls == [
        {"tool": "fetch_passage", "args": {"passage_id": "p_fat_43"}, "hit": True}
    ]
    assert llm.generate.await_count == 2
    second_prompt = llm.generate.await_args_list[1].args[0]
    assert "Tool results (untrusted data)" in second_prompt
    assert "Chrysippus says assent is in our power." in second_prompt
    assert "2 request(s) remain." in second_prompt


@pytest.mark.asyncio
async def test_json_round_provisional_verdict_is_final_once_budget_is_spent() -> None:
    request = {"tool": "fetch_node", "args": {"node_id": "scholar_chrysippus"}}
    llm = _llm(
        _verdict("WEAK", "need more", requests=[request]),
        _verdict("REJECTED", "still unsure", requests=[request]),
    )
    verifier = CitationVerifierV2(
        llm=llm,
        passage_fetcher=_fetcher(SALLES_EVIDENCE),
        tool_mode="json",
        max_tool_calls=1,
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    check = report.checks[0]
    assert check.status is CitationStatus.REJECTED
    assert len(check.tool_calls) == 1
    assert "tool budget of 1 calls was exhausted" in check.reasoning
    assert "Tool budget exhausted" in llm.generate.await_args_list[1].args[0]


@pytest.mark.asyncio
async def test_tool_mode_off_keeps_the_plain_single_call() -> None:
    llm = _llm(_verdict("VERIFIED"))
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=_fetcher(SALLES_EVIDENCE), tool_mode="off"
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    assert report.checks[0].status is CitationStatus.VERIFIED
    assert report.checks[0].tool_calls == []
    prompt = llm.generate.call_args.args[0]
    assert "requests" not in prompt
    assert "fetch_node" not in prompt
    assert verifier.tool_names == ()


@pytest.mark.asyncio
async def test_search_and_neighbors_tools_are_offered_when_wired() -> None:
    search = AsyncMock()
    search.fulltext_search = AsyncMock(
        return_value=[
            {
                "passage_id": "p_fat_43",
                "author": "Cicero",
                "title": "De fato",
                "canonical_ref": "43",
                "snippet": "assent ... in our power",
            }
        ]
    )
    neighbors = build_graph_neighbors(
        {"scholar_chrysippus": {"label": "Chrysippus", "type": "person"}},
        {
            "scholarly_argument_salles": [
                {"target": "scholar_chrysippus", "relation": "about", "description": ""}
            ]
        },
        {},
    )
    llm = AsyncMock()
    llm.generate_with_tools = AsyncMock(
        side_effect=[
            _assistant(
                None,
                _tool_call("search_corpus", {"query": "assent power", "k": 99}, "c1"),
                _tool_call(
                    "neighbors", {"node_id": "scholarly_argument_salles", "k": 2}, "c2"
                ),
            ),
            _assistant(_verdict("VERIFIED")),
        ]
    )
    verifier = CitationVerifierV2(
        llm=llm,
        passage_fetcher=_fetcher(SALLES_EVIDENCE),
        tool_mode="native",
        corpus_search=build_corpus_search(search),
        graph_neighbors=neighbors,
    )

    report = await verifier.verify_draft(SynthesizedDraft(claims=[SALLES_CLAIM]))

    assert verifier.tool_names == (
        "fetch_passage",
        "fetch_node",
        "search_corpus",
        "neighbors",
    )
    assert [c["tool"] for c in report.checks[0].tool_calls] == [
        "search_corpus",
        "neighbors",
    ]
    assert all(c["hit"] for c in report.checks[0].tool_calls)
    # k is clamped to the tool's ceiling.
    search.fulltext_search.assert_awaited_once_with("assent power", limit=5)
    second_messages = llm.generate_with_tools.await_args_list[1].args[0]
    search_result = json.loads(second_messages[3]["content"])
    assert search_result["results"][0]["passage_id"] == "p_fat_43"
    assert "in our power" in search_result["results"][0]["snippet"]
    neighbor_result = json.loads(second_messages[4]["content"])
    assert neighbor_result["neighbors"] == [
        {
            "node_id": "scholar_chrysippus",
            "label": "Chrysippus",
            "type": "person",
            "relation": "about",
            "direction": "out",
            "description": "",
        }
    ]


def test_graph_neighbors_dedupes_and_caps() -> None:
    neighbors = build_graph_neighbors(
        {"b": {"label": "B", "type": "concept"}},
        {"a": [{"target": "b", "relation": "r"}, {"target": "b", "relation": "r"}]},
        {"a": [{"source": "c", "relation": "s"}, {"source": "d", "relation": "t"}]},
    )
    rows = neighbors("a", 2)
    assert [(r["node_id"], r["direction"]) for r in rows] == [("b", "out"), ("c", "in")]
    assert rows[1]["label"] == "c"
    assert neighbors("zzz", 5) == []


# ------------------------------------------------------------ metadata aggregation


def test_aggregate_tool_calls_counts_hits_errors_and_tools() -> None:
    checks = [
        CitationCheck(
            citation_id="a",
            status=CitationStatus.VERIFIED,
            tool_calls=[
                {"tool": "fetch_node", "args": {}, "hit": True},
                {"tool": "search_corpus", "args": {}, "hit": False},
            ],
        ),
        CitationCheck(
            citation_id="b",
            status=CitationStatus.WEAK,
            tool_calls=[{"tool": "fetch_node", "args": {}, "hit": False, "error": "x"}],
        ),
        CitationCheck(citation_id="c", status=CitationStatus.VERIFIED),
    ]
    assert _aggregate_tool_calls(checks) == {
        "total": 3,
        "hits": 1,
        "errors": 1,
        "by_tool": {"fetch_node": 2, "search_corpus": 1},
        "citations_with_tool_calls": 2,
    }


@pytest.mark.asyncio
async def test_run_verifier_records_judge_context_aggregates() -> None:
    answer = _answer(
        "X argues A [N1], whereas Y argues B [N2]. Z alone [N3].",
        _citation("N1", "n1", "X"),
        _citation("N2", "n2", "Y"),
        _citation("N3", "n3", "Z"),
    )
    report = VerificationReport.from_checks(
        [
            CitationCheck(
                citation_id="n1",
                status=CitationStatus.VERIFIED,
                sentence="X argues A [N1], whereas Y argues B [N2].",
                companion_ids=["n2"],
                tool_calls=[{"tool": "fetch_node", "args": {}, "hit": True}],
            ),
            CitationCheck(
                citation_id="n2",
                status=CitationStatus.VERIFIED,
                sentence="X argues A [N1], whereas Y argues B [N2].",
                companion_ids=["n1"],
            ),
            CitationCheck(citation_id="n3", status=CitationStatus.VERIFIED),
        ]
    )
    agent = ScholarlyAgent(make_deps())
    agent.deps.verifier_v2 = AsyncMock()
    agent.deps.verifier_v2.verify_draft = AsyncMock(return_value=report)

    updated, _ = await agent._run_citation_verifier_v2(answer)

    draft = agent.deps.verifier_v2.verify_draft.call_args.args[0]
    by_id = {claim.citation_id: claim for claim in draft.claims}
    assert by_id["n1"].claim == "X argues A"
    assert by_id["n2"].claim == "whereas Y argues B"
    assert [c.citation_id for c in by_id["n1"].companions] == ["n2"]
    assert by_id["n3"].companions == []
    meta = updated.metadata["citation_verifier_v2"]
    assert meta["status"] == "passed"
    assert meta["clauses_isolated"] == 2
    assert meta["companions"] == {"total": 2, "citations_with_companions": 2}
    assert meta["tool_calls"] == {
        "total": 1,
        "hits": 1,
        "errors": 0,
        "by_tool": {"fetch_node": 1},
        "citations_with_tool_calls": 1,
    }
    # The failed-citation record keeps its shape for existing consumers.
    assert meta["failed_citations"] == []
