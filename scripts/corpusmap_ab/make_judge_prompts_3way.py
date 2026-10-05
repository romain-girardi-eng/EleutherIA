"""Blind three-way judge briefs (arms A, B, C hidden as X, Y, Z in random order)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))
from run_eval import load_query_files  # noqa: E402

K = ".venv/bin/python scripts/corpusmap_ab/kgtool.py"

TEMPLATE = """You are a strict, blind referee for a scholarly QA system on ancient debates about free will, fate and
moral responsibility. Three anonymous systems (X, Y and Z) answered the same QUESTION from the same
knowledge graph and passage corpus. Judge them on the merits only; their order is random.

QUESTION: {query}
{gold}
--- ANSWER X ---
{x}
--- ANSWER Y ---
{y}
--- ANSWER Z ---
{z}
--- END ---

You may verify what the cited ids actually say (at most 10 calls in total, run from /home/user/EleutherIA):
  {K} {run} get_node_detail node_id=...
  {K} {run} read_passage passage_id=...
Spot-check the claims that matter most in each answer. Do not read any repository file.

Score each answer from 1 to 10 on:
- correctness: claims are true and correctly attributed (penalise misattribution, invented loci or quotations)
- completeness: covers every part of the question
- grounding: claims are supported by the cited ids you checked; gaps are honestly flagged instead of filled
- overall: your holistic verdict for a scholar (not an average)

Then save your verdict with ONE Bash command. Use exactly this Python one-liner so the JSON is valid
(replace each 0 with your integer score, replace X|Y|Z|tie by exactly one of X, Y, Z or tie, and write your one-sentence reason):
.venv/bin/python -c 'import json,sys; s={{"X":{{"correctness":0,"completeness":0,"grounding":0,"overall":0}},"Y":{{"correctness":0,"completeness":0,"grounding":0,"overall":0}},"Z":{{"correctness":0,"completeness":0,"grounding":0,"overall":0}}}}; open("{out}","a").write(json.dumps({{"query_id":"{qid}","scores":s,"best":"X|Y|Z|tie","reason":sys.argv[1]}})+"\\n")' "your one-sentence reason"
Then reply: done
"""


def main() -> None:
    out_dir, ab = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    rng = random.Random(20261006)
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
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for qid in sel:
        arms = ["A", "B", "C"]
        rng.shuffle(arms)
        mapping[qid] = dict(zip("XYZ", arms, strict=True))
        texts = [
            (ab / "answers" / f"{qid}-{a}.md").read_text(encoding="utf-8") for a in arms
        ]
        case = cases[qid]
        gold = ""
        if case.gold_claims:
            gold = (
                "Reference claims a good answer should support:\n"
                + "\n".join(f"- {c}" for c in case.gold_claims)
                + "\n"
            )
        if case.answerable is False:
            gold += "Note: this question is designed to be unanswerable from the corpus; the right answer says the evidence is missing.\n"
        (out_dir / f"judge_{qid}.txt").write_text(
            TEMPLATE.format(
                query=case.query,
                gold=gold,
                x=texts[0],
                y=texts[1],
                z=texts[2],
                K=K,
                run=f"judge_{qid}-C",
                qid=qid,
                out=str(ab.relative_to(REPO) / "judgments_raw.jsonl"),
            ),
            encoding="utf-8",
        )
    (ab / "judge_mapping.json").write_text(
        json.dumps(mapping, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
