"""Write the per-run agent briefs for the agentic CorpusMap A/B (arm A = current tools, arm B = + CorpusMap, arm C = B + full-text passage candidates)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))
from eleutheria_graphrag.corpusmap import (  # noqa: E402
    build_corpus_map,
    select_candidates,
)
from eval_lib.snapshot_runner import SnapshotIndex  # noqa: E402
from run_eval import load_query_files  # noqa: E402

K = ".venv/bin/python scripts/corpusmap_ab/kgtool.py"

COMMON = """You are a scholarly research agent for EleutherIA (ancient debates on free will, fate and moral
responsibility). Answer the QUESTION below from the EleutherIA knowledge graph and ancient-text corpus.

You may ONLY obtain information through this command (run it with the Bash tool, from /home/user/EleutherIA):
  {K} {run} <tool> key=value key="value with spaces" ...
Do not read, grep or open any file in the repository, and do not use web search or your own memory of
the sources as evidence: anything not returned by a tool must be treated as unknown.

Tools:
- search_nodes query=... [type_filter=person|concept|argument|work|school|debate] [limit=1..30]
- get_node_detail node_id=...
- get_neighbors node_id=... [relation_filter=...] [direction=out|in|both] [limit=1..30]
- read_passages node_id=... [limit=1..10]      (ancient passages linked to a KG node)
- search_passages query=... [work_filter=...] [limit=1..10]   (BM25 over the passage corpus)
- read_passage passage_id=...
{extra_tools}
Budget: at most 15 tool calls. Stop as soon as the evidence suffices. Never fabricate Greek/Latin text or
references. If the corpus does not attest something, say so.
{candidates}
QUESTION: {query}

When done, save your result with ONE final Bash command (this write is the only file access allowed):
cat > {answers}/{run}.md <<'EOF_ANSWER'
ANSWER:
<the scholarly answer, at most 250 words, in the language of the question, citing node ids / passage ids in
square brackets for every claim>
CITED_IDS: <JSON list of every node_id / passage_id / entity_id your answer relies on>
EOF_ANSWER
Then reply with the single word: done
"""

EXTRA_B = """- search_entity_pages query=... [limit=1..20]   (CorpusMap: one page per person/concept/work/debate)
- read_entity_page entity_id=... [focus="the question or a sub-question"]
  An Entity Page consolidates what every linked document says about the entity: overview, aliases, key facts
  each tagged with its source document id, evidence passages and corpus holdings. Follow the ids it lists
  (get_node_detail / read_passage) to reach the documents themselves.
"""


def main() -> None:
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
    ix = SnapshotIndex()
    cmap = build_corpus_map(
        REPO / "data/kg", REPO / "data/corpus", allowed_passages=set(ix.passages)
    )
    out = Path(sys.argv[1])
    # optional: answers dir (repo-relative) and arms, e.g. data/eval/corpusmap_ab/opus/answers ABC
    answers = sys.argv[2] if len(sys.argv) > 2 else "data/eval/corpusmap_ab/answers"
    arms = sys.argv[3] if len(sys.argv) > 3 else "AB"
    out.mkdir(parents=True, exist_ok=True)
    for qid in sel:
        q = cases[qid].query
        for arm in arms:
            run = f"{qid}-{arm}"
            cand = ""
            if arm in "BC":
                n_passages = 5 if arm == "C" else 0
                cand = (
                    "\nStart from these CorpusMap candidates, chosen for this question:\n"
                    + select_candidates(cmap, q, n_passages=n_passages).render()
                    + "\n"
                )
            (out / f"{run}.txt").write_text(
                COMMON.format(
                    K=K,
                    run=run,
                    extra_tools=EXTRA_B if arm in "BC" else "",
                    candidates=cand,
                    query=q,
                    answers=answers,
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
