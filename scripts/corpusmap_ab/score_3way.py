"""Score the three-arm Opus 5.5 run (A current tools, B + CorpusMap, C + CorpusMap + passage leg).

    .venv/bin/python scripts/corpusmap_ab/score_3way.py data/eval/corpusmap_ab/opus
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean, stdev

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "eval"))
sys.path.insert(0, str(Path(__file__).parent))
from run_eval import load_query_files  # noqa: E402
from score import _jsonl, parse_answer, sign_test, trajectory_tokens  # noqa: E402

ARMS = "ABC"


def main() -> int:
    ab = Path(sys.argv[1]).resolve()
    sel = json.loads((REPO / "scripts/corpusmap_ab/selection.json").read_text())
    cases = {
        c.id: c
        for c in load_query_files(
            [REPO / "tests/eval/queries.yaml", REPO / "tests/eval/release_scholarly_2026_09_06.yaml"]
        )
    }
    known = {json.loads(line)["id"] for line in (REPO / "data/kg/nodes.jsonl").open(encoding="utf-8")}
    known |= {json.loads(line)["passage_id"] for line in (REPO / "data/corpus/passages.jsonl").open(encoding="utf-8")}

    calls = defaultdict(list)
    for c in _jsonl(ab / "calls.jsonl"):
        calls[c["run"]].append(c)
    mapping = json.loads((ab / "judge_mapping.json").read_text()) if (ab / "judge_mapping.json").exists() else {}
    judge: dict[str, dict] = {}
    best = defaultdict(int)
    for j in _jsonl(ab / "judgments_raw.jsonl"):
        m = mapping[j["query_id"]]
        judge[j["query_id"]] = {m[k]: v for k, v in j["scores"].items()}
        best[m.get(j.get("best"), "tie")] += 1

    rows = []
    for qid in sel:
        case = cases[qid]
        for arm in ARMS:
            run = f"{qid}-{arm}"
            path = ab / "answers" / f"{run}.md"
            if not path.exists():
                continue
            body, ids = parse_answer(path.read_text(encoding="utf-8"))
            got = set(ids)

            def rec(gold, got=got):
                return None if not gold else sum(g in got for g in gold) / len(gold)

            rc = calls.get(run, [])
            brief = ab / "briefs" / f"{run}.txt"
            turns, traj = trajectory_tokens(rc, len(brief.read_text(encoding="utf-8")) if brief.exists() else 0)
            rows.append({
                "query_id": qid, "arm": arm, "query_type": case.query_type,
                "group": "thesis" if qid.startswith("r0") else "release" if qid.startswith("release") else case.query_type,
                "entity_recall": rec(list(case.expected_entities)),
                "work_recall": rec(list(case.expected_works)),
                "passage_recall": rec(list(case.expected_passages)),
                "cited_ids": len(ids), "invalid_ids": sum(i not in known for i in ids),
                "tool_calls": len(rc), "model_turns": turns,
                "tool_output_tokens": sum(c["out_chars"] for c in rc) // 4,
                "trajectory_input_tokens": traj,
                "judge": judge.get(qid, {}).get(arm),
            })
    (ab / "agentic_rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    by = defaultdict(dict)
    for r in rows:
        by[r["query_id"]][r["arm"]] = r
    full = {q: d for q, d in by.items() if len(d) == 3}

    def avg(arm, key, sub=None, qs=None):
        vals = []
        for q, d in full.items():
            if qs and q not in qs:
                continue
            v = d[arm][key]
            if sub:
                v = v[sub] if v else None
            if v is not None:
                vals.append(v)
        return round(mean(vals), 3) if vals else None

    summary = {"n_queries": len(full), "judge_best": dict(best), "arms": {}}
    for arm in ARMS:
        s = {k: avg(arm, k) for k in ("entity_recall", "work_recall", "passage_recall", "cited_ids", "invalid_ids",
                                     "tool_calls", "model_turns", "tool_output_tokens", "trajectory_input_tokens")}
        s["trajectory_input_tokens_total"] = sum(d[arm]["trajectory_input_tokens"] for d in full.values())
        s["tool_output_tokens_total"] = sum(d[arm]["tool_output_tokens"] for d in full.values())
        for k in ("correctness", "completeness", "grounding", "overall"):
            s[f"judge_{k}"] = avg(arm, "judge", k)
        summary["arms"][arm] = s
    pairs = {}
    for a, b in combinations(ARMS, 2):
        res = {}
        for key, sub, higher in (("judge", "overall", True), ("trajectory_input_tokens", None, False),
                                 ("tool_output_tokens", None, False), ("passage_recall", None, True)):
            w = lo = t = 0
            diffs = []
            for d in full.values():
                va, vb = d[a][key], d[b][key]
                if sub:
                    va, vb = (va or {}).get(sub), (vb or {}).get(sub)
                if va is None or vb is None:
                    continue
                diffs.append(vb - va)
                if va == vb:
                    t += 1
                elif (vb > va) == higher:
                    w += 1
                else:
                    lo += 1
            name = f"{key}{'_' + sub if sub else ''}"
            res[name] = {f"{b}_better": w, f"{a}_better": lo, "tie": t, "sign_test_p": round(sign_test(w, lo), 4)}
            if sub and len(diffs) > 1:
                res[name]["mean_diff"] = round(mean(diffs), 3)
                res[name]["ci95"] = round(1.96 * stdev(diffs) / len(diffs) ** 0.5, 3)
        tot_a = summary["arms"][a]["trajectory_input_tokens_total"]
        tot_b = summary["arms"][b]["trajectory_input_tokens_total"]
        res["trajectory_tokens_change"] = round(tot_b / tot_a - 1, 4)
        pairs[f"{a}_vs_{b}"] = res
    summary["pairs"] = pairs
    groups = defaultdict(list)
    for q, d in full.items():
        groups[d["A"]["group"]].append(q)
    summary["groups"] = {
        g: {arm: {"judge_overall": avg(arm, "judge", "overall", set(qs)),
                  "trajectory_tokens_total": sum(full[q][arm]["trajectory_input_tokens"] for q in qs)} for arm in ARMS}
        | {"n": len(qs)}
        for g, qs in groups.items()
    }
    (ab / "agentic_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
