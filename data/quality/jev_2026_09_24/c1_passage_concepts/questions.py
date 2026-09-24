"""Builds the exact chunked question sets for campaign C1 and writes questions.json
for reproducibility. Concepts are split into 4 chunks of 53 (212 total); chunk 0
also carries the passage-level questions (centrality score, text-quality choice,
is_greek / is_latin booleans)."""
import json
from pathlib import Path

OUT = Path(__file__).parent
concepts = json.load(open(OUT / "concepts.json", encoding="utf-8"))
concept_ids = sorted(concepts.keys())

N_CHUNKS = 4
size = -(-len(concept_ids) // N_CHUNKS)  # ceil
concept_chunks = [concept_ids[i:i + size] for i in range(0, len(concept_ids), size)]

TEXT_QUALITY_CRITERIA = {
    "clean edited ancient text": "a clean, correctly edited passage of ancient Greek or Latin",
    "text with OCR noise or broken words": "the text has OCR artefacts, broken or garbled words, misrecognised characters",
    "text mixed with critical apparatus, line numbers or editorial notes": "the passage text is mixed with a critical apparatus, line/verse numbers, sigla, or editorial brackets and notes",
    "mostly modern-language text": "the passage is mostly in a modern language (e.g. French, English, German), not ancient Greek or Latin",
    "fragmentary or too short to judge": "the passage is too short, cut off, or fragmentary to judge its quality",
}

CENTRALITY_CRITERIA = [
    "not at all",
    "mentioned in passing",
    "a theme among others",
    "the main topic",
]


def concept_question(cid: str) -> dict:
    c = concepts[cid]
    gloss = (c.get("gloss") or "").strip()
    return {
        "type": "boolean",
        "instructions": (
            f"The passage (Ancient Greek or Latin) explicitly discusses this concept: "
            f"{c['label']}. {gloss}"
        ),
    }


def build_chunks() -> list[dict]:
    chunks = []
    for i, ids in enumerate(concept_chunks):
        q = {cid: concept_question(cid) for cid in ids}
        if i == 0:
            q["q_centrality"] = {
                "type": "score",
                "instructions": (
                    "How central is the question of what is up to us / free choice / "
                    "fate and responsibility to this passage?"
                ),
                "criteria": CENTRALITY_CRITERIA,
            }
            q["q_text_quality"] = {
                "type": "choice",
                "instructions": "What is the textual quality of this passage?",
                "criteria": TEXT_QUALITY_CRITERIA,
            }
            q["q_is_greek"] = {
                "type": "boolean",
                "instructions": "The passage is written in Ancient Greek.",
            }
            q["q_is_latin"] = {
                "type": "boolean",
                "instructions": "The passage is written in Latin.",
            }
        chunks.append(q)
    return chunks


def passage_level_questions() -> dict:
    return {
        "q_centrality": {
            "type": "score",
            "instructions": (
                "How central is the question of what is up to us / free choice / "
                "fate and responsibility to this passage?"
            ),
            "criteria": CENTRALITY_CRITERIA,
        },
        "q_text_quality": {
            "type": "choice",
            "instructions": "What is the textual quality of this passage?",
            "criteria": TEXT_QUALITY_CRITERIA,
        },
        "q_is_greek": {"type": "boolean", "instructions": "The passage is written in Ancient Greek."},
        "q_is_latin": {"type": "boolean", "instructions": "The passage is written in Latin."},
    }


def build_passage_only() -> dict:
    """Stage 1 (re-plan 2026-09-24): passage-level questions only, small/cheap
    calls, run over all 15,212 passages first -- the gateway is token-rate
    limited, not request-rate limited, so this is the fast phase."""
    return passage_level_questions()


def build_concepts_only() -> dict:
    """Stage 2 (re-plan 2026-09-24): the 212 concept booleans alone, no
    passage-level questions (already collected in stage 1), run only on the
    high-value subset selected after stage 1."""
    return {cid: concept_question(cid) for cid in concept_ids}


def build_all_in_one() -> dict:
    """All 212 concept booleans + the 4 passage-level questions in a single call.
    Switched to after throughput testing showed the gateway throttles on
    requests/second, not on the 64k token budget (~15-22k tokens actually used
    per passage here) -- 1 call/passage instead of 4 quarters the call count."""
    q = {cid: concept_question(cid) for cid in concept_ids}
    q["q_centrality"] = {
        "type": "score",
        "instructions": (
            "How central is the question of what is up to us / free choice / "
            "fate and responsibility to this passage?"
        ),
        "criteria": CENTRALITY_CRITERIA,
    }
    q["q_text_quality"] = {
        "type": "choice",
        "instructions": "What is the textual quality of this passage?",
        "criteria": TEXT_QUALITY_CRITERIA,
    }
    q["q_is_greek"] = {"type": "boolean", "instructions": "The passage is written in Ancient Greek."}
    q["q_is_latin"] = {"type": "boolean", "instructions": "The passage is written in Latin."}
    return q


if __name__ == "__main__":
    chunks = build_chunks()
    all_in_one = build_all_in_one()
    passage_only = build_passage_only()
    concepts_only = build_concepts_only()
    with open(OUT / "questions.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "n_chunks": len(chunks),
                "concept_chunks": [list(c.keys() if i > 0 else [k for k in c if k in concepts]) for i, c in enumerate(chunks)],
                "chunks": chunks,
                "all_in_one": all_in_one,
                "passage_only": passage_only,
                "concepts_only": concepts_only,
            },
            f, ensure_ascii=False, indent=1,
        )
    for i, c in enumerate(chunks):
        print(f"chunk {i}: {len(c)} questions")
    print(f"all_in_one: {len(all_in_one)} questions")
    print(f"passage_only: {len(passage_only)} questions")
    print(f"concepts_only: {len(concepts_only)} questions")
