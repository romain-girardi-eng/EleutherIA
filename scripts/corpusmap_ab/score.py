"""Score the agentic CorpusMap A/B runs.

Inputs (under data/eval/corpusmap_ab/):
  answers/<qid>-<arm>.md   final answer + CITED_IDS written by each agent
  calls.jsonl              every tool call with the size of its output (kgtool server log)
  agent_tokens.jsonl       {"run": ..., "subagent_tokens": ...} reported by the agent runtime
  judgments.jsonl          blind pairwise judge verdicts (optional)

Per arm: gold recall of cited entities / works / passages, invalid (non-existent)
cited ids, tool calls, tool-output tokens (chars / 4), total agent tokens, and
judge scores; plus paired win/loss counts and a two-sided sign test.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))
from run_eval import load_query_files  # noqa: E402

AB = REPO / "data/eval/corpusmap_ab"
PROMPTS = AB / "briefs"


def _jsonl(path: Path) -> list[dict]:
    """One object per line; a stray trailing brace from a hand-written line is tolerated."""
    if not path.exists():
        return []
    decoder = json.JSONDecoder()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(decoder.raw_decode(line)[0])
        except json.JSONDecodeError:
            # Judges hand-write their verdict line; the one observed defect is a
            # missing brace closing "scores" before "preferred".
            out.append(
                decoder.raw_decode(
                    line.replace('}, "preferred"', '}}, "preferred"', 1)
                )[0]
            )
    return out


def sign_test(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * p)


def trajectory_tokens(run_calls: list[dict], prompt_chars: int) -> tuple[int, int]:
    """Input tokens re-read over the trajectory, excluding the fixed runtime system prompt.

    Calls issued in one Bash command (gap < 1 s) belong to one model turn; each
    turn re-reads the brief plus every tool output returned before it, and a
    final turn writes the answer. Returns (turns, tokens) with tokens = chars / 4.
    """
    turns: list[int] = []
    last = None
    for c in sorted(run_calls, key=lambda c: c["ts"]):
        if last is None or c["ts"] - last > 1.0:
            turns.append(0)
        turns[-1] += c["out_chars"]
        last = c["ts"]
    context, total = prompt_chars, 0
    for out in turns + [0]:
        total += context
        context += out
    return len(turns) + 1, total // 4


def parse_answer(text: str) -> tuple[str, list[str]]:
    m = re.search(r"CITED_IDS:\s*(\[.*?\])", text, re.S)
    ids: list[str] = []
    if m:
        try:
            ids = [str(x) for x in json.loads(m.group(1))]
        except json.JSONDecodeError:
            ids = re.findall(r'"([^"]+)"', m.group(1))
    body = text.split("CITED_IDS:")[0].replace("ANSWER:", "").strip()
    # ids cited inline in square brackets count too
    ids += re.findall(r"\[([A-Za-z0-9_\-]{8,})\]", body)
    return body, list(dict.fromkeys(ids))


def main() -> int:
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
    known = {
        json.loads(line)["id"]
        for line in (REPO / "data/kg/nodes.jsonl").open(encoding="utf-8")
    }
    known |= {
        json.loads(line)["passage_id"]
        for line in (REPO / "data/corpus/passages.jsonl").open(encoding="utf-8")
    }

    calls = defaultdict(list)
    for c in _jsonl(AB / "calls.jsonl"):
        calls[c["run"]].append(c)
    agent_tokens = {
        r["run"]: r["subagent_tokens"] for r in _jsonl(AB / "agent_tokens.jsonl")
    }
    # Un-blind the judge: X/Y -> A/B through the hidden mapping.
    mapping = (
        json.loads((AB / "judge_mapping.json").read_text())
        if (AB / "judge_mapping.json").exists()
        else {}
    )
    judge = defaultdict(dict)
    preferred = {"A": 0, "B": 0, "tie": 0}
    unblinded = []
    for j in _jsonl(AB / "judgments_raw.jsonl"):
        # Same hand-writing defect, other shape: "preferred"/"reason" nested inside "scores".
        for key in ("preferred", "reason"):
            if key in j["scores"]:
                j[key] = j["scores"].pop(key)
        m = mapping[j["query_id"]]
        scores = {m[k]: v for k, v in j["scores"].items()}
        pref = m.get(j.get("preferred"), "tie")
        preferred[pref] += 1
        judge[j["query_id"]] = scores
        unblinded.append(
            {
                "query_id": j["query_id"],
                "scores": scores,
                "preferred": pref,
                "reason": j.get("reason"),
            }
        )
    (AB / "judgments.jsonl").write_text(
        "".join(json.dumps(u, ensure_ascii=False) + "\n" for u in unblinded),
        encoding="utf-8",
    )

    rows = []
    for qid in sel:
        case = cases[qid]
        for arm in "AB":
            run = f"{qid}-{arm}"
            path = AB / "answers" / f"{run}.md"
            if not path.exists():
                continue
            body, ids = parse_answer(path.read_text(encoding="utf-8"))
            got = set(ids)

            def rec(gold, got=got):
                return None if not gold else sum(g in got for g in gold) / len(gold)

            rc = calls.get(run, [])
            prompt_file = PROMPTS / f"{run}.txt"
            prompt_chars = (
                len(prompt_file.read_text(encoding="utf-8"))
                if prompt_file.exists()
                else 0
            )
            n_turns, traj = trajectory_tokens(rc, prompt_chars)
            rows.append(
                {
                    "query_id": qid,
                    "arm": arm,
                    "query_type": case.query_type,
                    "entity_recall": rec(list(case.expected_entities)),
                    "work_recall": rec(list(case.expected_works)),
                    "passage_recall": rec(list(case.expected_passages)),
                    "cited_ids": len(ids),
                    "invalid_ids": sum(i not in known for i in ids),
                    "tool_calls": len(rc),
                    "map_calls": sum(
                        c["tool"] in {"search_entity_pages", "read_entity_page"}
                        for c in rc
                    ),
                    "tool_output_tokens": sum(c["out_chars"] for c in rc) // 4,
                    "brief_tokens": prompt_chars // 4,
                    "model_turns": n_turns,
                    "trajectory_input_tokens": traj,
                    "agent_tokens": agent_tokens.get(run),
                    "judge": judge.get(qid, {}).get(arm),
                    "answer_words": len(body.split()),
                }
            )
    (AB / "agentic_rows.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )

    metrics = [
        "entity_recall",
        "work_recall",
        "passage_recall",
        "cited_ids",
        "invalid_ids",
        "tool_calls",
        "map_calls",
        "tool_output_tokens",
        "brief_tokens",
        "model_turns",
        "trajectory_input_tokens",
        "agent_tokens",
        "answer_words",
    ]
    summary: dict = {
        "n_runs": {a: sum(r["arm"] == a for r in rows) for a in "AB"},
        "judge_preferred": preferred,
        "judge_preferred_sign_test_p": round(
            sign_test(preferred["B"], preferred["A"]), 4
        ),
    }
    for a in "AB":
        rs = [r for r in rows if r["arm"] == a]
        summary[a] = {}
        for m in metrics:
            vals = [r[m] for r in rs if r[m] is not None]
            summary[a][m] = (
                {"mean": round(mean(vals), 3), "median": round(median(vals), 1)}
                if vals
                else None
            )
        jv = [r["judge"] for r in rs if r["judge"]]
        if jv:
            summary[a]["judge"] = {k: round(mean(v[k] for v in jv), 3) for k in jv[0]}

    paired = defaultdict(lambda: [0, 0, 0])  # B better, A better, tie
    by_q = defaultdict(dict)
    for r in rows:
        by_q[r["query_id"]][r["arm"]] = r
    for d in by_q.values():
        if len(d) < 2:
            continue
        for m, higher_better in (
            ("entity_recall", True),
            ("work_recall", True),
            ("passage_recall", True),
            ("tool_output_tokens", False),
            ("trajectory_input_tokens", False),
            ("agent_tokens", False),
        ):
            a, b = d["A"][m], d["B"][m]
            if a is None or b is None:
                continue
            if a == b:
                paired[m][2] += 1
            elif (b > a) == higher_better:
                paired[m][0] += 1
            else:
                paired[m][1] += 1
        if d["A"]["judge"] and d["B"]["judge"]:
            a, b = d["A"]["judge"]["overall"], d["B"]["judge"]["overall"]
            paired["judge_overall"][0 if b > a else 1 if a > b else 2] += 1
    summary["paired"] = {
        m: {
            "B_better": w,
            "A_better": lo,
            "tie": t,
            "sign_test_p": round(sign_test(w, lo), 4),
        }
        for m, (w, lo, t) in paired.items()
    }
    tok = [
        (d["A"]["agent_tokens"], d["B"]["agent_tokens"])
        for d in by_q.values()
        if len(d) == 2 and d["A"]["agent_tokens"] and d["B"]["agent_tokens"]
    ]
    if tok:
        summary["agent_tokens_total"] = {
            "A": sum(a for a, _ in tok),
            "B": sum(b for _, b in tok),
            "B_vs_A": round(sum(b for _, b in tok) / sum(a for a, _ in tok) - 1, 4),
        }
    for m in ("trajectory_input_tokens",):
        pairs = [(d["A"][m], d["B"][m]) for d in by_q.values() if len(d) == 2]
        summary[f"{m}_total"] = {
            "A": sum(a for a, _ in pairs),
            "B": sum(b for _, b in pairs),
            "B_vs_A": round(
                sum(b for _, b in pairs) / max(1, sum(a for a, _ in pairs)) - 1, 4
            ),
        }
    tt = [
        (d["A"]["tool_output_tokens"], d["B"]["tool_output_tokens"])
        for d in by_q.values()
        if len(d) == 2
    ]
    if tt:
        summary["tool_output_tokens_total"] = {
            "A": sum(a for a, _ in tt),
            "B": sum(b for _, b in tt),
            "B_vs_A": round(
                sum(b for _, b in tt) / max(1, sum(a for a, _ in tt)) - 1, 4
            ),
        }
    (AB / "agentic_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
