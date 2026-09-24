"""Stage 2 re-plan (2026-09-24): select the high-value passage subset for the
212-concept-boolean pass, from stage 1's passage-level results.

Selection: p(centrality in {'a theme among others','the main topic'}) >= 0.5,
UNION all passages that already carry >=1 existing discusses/evidenced_by edge
(so contradictions against the existing graph can still be checked even if
Jev's own relevance read is lower). Ordered by relevance descending so a
concurrency-limited, time-boxed stage 2 covers the best passages first."""
import gzip
import json
from pathlib import Path

D = Path(__file__).parent

candidates = {}
for line in open(D / "candidates.jsonl", encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        candidates[r["id"]] = r

extra = {}  # pid -> {q_centrality, ...}
chunks_seen = {}
results_path = D / "results.jsonl"
if not results_path.exists():
    results_path = D / "results.jsonl.gz"
opener = gzip.open if str(results_path).endswith(".gz") else open
with opener(results_path, "rt", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        row = json.loads(line)
        pid = row["id"]
        chunks_seen.setdefault(pid, set()).add(row["chunk"])
        for k, v in row["answers"].items():
            if k.startswith("q_"):
                extra.setdefault(pid, {})[k] = v


def p_theme_or_main(e: dict) -> float | None:
    c = e.get("q_centrality")
    if c is None:
        return None
    if isinstance(c, dict):
        probs = c.get("probabilities") or {}
        if probs:
            return round(probs.get("2", 0) + probs.get("3", 0), 4)
        return 1.0 if round(c.get("score", 0)) >= 2 else 0.0
    return 1.0 if round(c) >= 2 else 0.0


scored = []  # (p, pid, reason)
n_have_passage_level = 0
for pid, cand in candidates.items():
    e = extra.get(pid)
    has_pl = bool(e) and "q_centrality" in e
    has_edge = bool(cand["existing"])
    if has_pl:
        n_have_passage_level += 1
    p = p_theme_or_main(e) if e else None
    relevant = p is not None and p >= 0.5
    if relevant or has_edge:
        reason = []
        if relevant:
            reason.append("relevant")
        if has_edge:
            reason.append("existing_edge")
        sort_key = p if p is not None else -1
        scored.append((sort_key, p, pid, "+".join(reason)))

scored.sort(key=lambda t: -t[0])

with open(D / "stage2_ids.txt", "w", encoding="utf-8") as f:
    for _, p, pid, reason in scored:
        f.write(pid + "\n")

with open(D / "stage2_ids_annotated.csv", "w", encoding="utf-8") as f:
    f.write("passage_id,p_theme_or_main,reason\n")
    for _, p, pid, reason in scored:
        f.write(f"{pid},{'' if p is None else p},{reason}\n")

n_relevant = sum(1 for p, pid, r in scored if "relevant" in r)
n_edge_only = sum(1 for p, pid, r in scored if r == "existing_edge")
print(f"candidates total: {len(candidates)}")
print(f"passages with stage-1 passage-level answers so far: {n_have_passage_level}")
print(f"stage2 selected: {len(scored)} (relevant>=0.5: {n_relevant}, edge-only no passage-level yet: {n_edge_only})")
print(f"-> data/quality/jev_2026_09_24/c1_passage_concepts/stage2_ids.txt")
