"""Blind pairwise judge briefs for the agentic CorpusMap A/B (arm labels hidden and order randomised)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))
from run_eval import load_query_files  # noqa: E402

AB = REPO / "data/eval/corpusmap_ab"
K = ".venv/bin/python scripts/corpusmap_ab/kgtool.py"

TEMPLATE = """You are a strict, blind referee for a scholarly QA system on ancient debates about free will, fate and
moral responsibility. Two anonymous systems (X and Y) answered the same QUESTION from the same knowledge
graph and passage corpus. Judge them on the merits only; their order is random.

QUESTION: {query}
{gold}
--- ANSWER X ---
{x}
--- ANSWER Y ---
{y}
--- END ---

You may verify what the cited ids actually say (at most 8 calls in total, run from /home/user/EleutherIA):
  {K} {run} get_node_detail node_id=...
  {K} {run} read_passage passage_id=...
Spot-check the claims that matter most in each answer. Do not read any repository file.

Score each answer from 1 to 10 on:
- correctness: claims are true and correctly attributed (penalise misattribution, invented loci or quotations)
- completeness: covers every part of the question
- grounding: claims are supported by the cited ids you checked; gaps are honestly flagged instead of filled
- overall: your holistic verdict for a scholar (not an average)

Then save your verdict with ONE Bash command, exactly:
echo '{{"query_id": "{qid}", "scores": {{"X": {{"correctness": _, "completeness": _, "grounding": _, "overall": _}}, "Y": {{"correctness": _, "completeness": _, "grounding": _, "overall": _}}}}, "preferred": "X|Y|tie", "reason": "<one sentence>"}}' >> data/eval/corpusmap_ab/judgments_raw.jsonl
(replace each _ with an integer; keep it on one line; no apostrophes inside the reason). Then reply: done
"""


def main() -> None:
    rng = random.Random(20261005)
    sel = json.loads((REPO / "scripts/corpusmap_ab/selection.json").read_text())
    cases = {
        c.id: c
        for c in load_query_files(
            [
                REPO / "tests/eval/queries.yaml",
                REPO / "tests/eval/release_scholarly_2026_09_06.yaml",
            ]
        )
    }
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for qid in sel:
        a = (AB / "answers" / f"{qid}-A.md").read_text(encoding="utf-8")
        b = (AB / "answers" / f"{qid}-B.md").read_text(encoding="utf-8")
        flip = rng.random() < 0.5
        mapping[qid] = {"X": "B" if flip else "A", "Y": "A" if flip else "B"}
        x, y = (b, a) if flip else (a, b)
        case = cases[qid]
        gold = ""
        if case.gold_claims:
            gold = (
                "Reference claims a good answer should support:\n"
                + "\n".join(f"- {c}" for c in case.gold_claims)
                + "\n"
            )
        if getattr(case, "answerable", True) is False:
            gold += "Note: this question is designed to be unanswerable from the corpus; the right answer says the evidence is missing.\n"
        (out / f"judge_{qid}.txt").write_text(
            TEMPLATE.format(
                query=case.query,
                gold=gold,
                x=x,
                y=y,
                K=K,
                run=f"judge_{qid}-B",
                qid=qid,
            ),
            encoding="utf-8",
        )
    (AB / "judge_mapping.json").write_text(
        json.dumps(mapping, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
