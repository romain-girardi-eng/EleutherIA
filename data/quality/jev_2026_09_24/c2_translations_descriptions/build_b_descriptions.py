"""Part B candidate builder: every non-passage KG node with a description >= 60 chars.

State = {name, type, description} (description truncated to 6k chars per the brief).
Person nodes get an extra question (modern-scholar framing), checked deterministically
against the node's own `period` field afterwards in analyze_b.py -- Jev is only asked
to read the description, never told the period, so a mismatch is a real signal.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/Users/romaingirardi/Projects/EleutherIA/data")
OUT = Path(__file__).parent
MAX_CHARS = 6000
MIN_CHARS = 60


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main() -> None:
    nodes = list(load_jsonl(ROOT / "kg/nodes.jsonl"))
    print(f"total nodes: {len(nodes)}")

    candidates = []
    for n in nodes:
        if n.get("type") == "passage":
            continue
        desc = (n.get("description") or "").strip()
        if len(desc) < MIN_CHARS:
            continue
        nid = n.get("node_id") or n.get("id")
        candidates.append({
            "id": nid,
            "label": n.get("label"),
            "type": n.get("type"),
            "period": n.get("period"),
            "role": n.get("role"),
            "desc_len": len(desc),
            "truncated": len(desc) > MAX_CHARS,
            "state": {
                "name": n.get("label"),
                "type": n.get("type"),
                "description": desc[:MAX_CHARS],
            },
            "is_person": n.get("type") == "person",
        })

    print(f"candidates built (desc >= {MIN_CHARS} chars, non-passage): {len(candidates)}")
    with open(OUT / "candidates_b.jsonl", "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    base_questions = {
        "about_entity": {
            "type": "boolean",
            "instructions": (
                "The text under `description` is about the entity named in `name` (of the "
                "kind given in `type`), not about a different person, work, or concept."
            ),
        },
        "curator_notes": {
            "type": "boolean",
            "instructions": (
                "The text under `description` contains internal editorial notes, "
                "verification remarks, TODOs, audit metadata, or instructions to a curator, "
                "rather than being purely content meant for readers."
            ),
        },
        "language": {
            "type": "choice",
            "instructions": "What language is the text under `description` written in?",
            "criteria": {
                "en": "English",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "mixed": "mixed (more than one language)",
                "other": "another language",
            },
        },
    }
    person_extra = {
        "modern_scholar": {
            "type": "boolean",
            "instructions": (
                "The `description` presents the person named in `name` as a modern scholar "
                "(19th century or later) writing about ancient philosophy or theology, rather "
                "than as an ancient, patristic, or medieval author who is himself a primary "
                "source in this period."
            ),
        },
    }
    with open(OUT / "questions_b_base.json", "w", encoding="utf-8") as f:
        json.dump(base_questions, f, ensure_ascii=False, indent=1)
    with open(OUT / "questions_b_person_extra.json", "w", encoding="utf-8") as f:
        json.dump(person_extra, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
