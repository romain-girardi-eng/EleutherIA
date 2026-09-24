"""C1 analysis: merges the 4 per-passage chunks, compares against existing
discusses/evidenced_by edges, and writes the review queues + summary stats
described in BRIEF_COMMON.md."""
import csv
import gzip
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).parent
SURE, PROB, UNC = 0.9, 0.7, 0.3

concepts = json.load(open(D / "concepts.json", encoding="utf-8"))
short = {k: (v["label"] or k).split(" - ")[0][:44] for k, v in concepts.items()}

candidates = {}
for line in open(D / "candidates.jsonl", encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        candidates[r["id"]] = r

n_chunks = json.load(open(D / "questions.json", encoding="utf-8"))["n_chunks"]

# merge chunks per passage
merged = defaultdict(dict)  # pid -> concept_id -> p (float) or passage-level answers
extra = {}  # pid -> {q_centrality, q_text_quality, q_is_greek, q_is_latin}
cost_total = 0.0
ms_all = []
tokens_all = []
n_rows = 0
chunks_present = defaultdict(set)

results_path = D / "results.jsonl"
if not results_path.exists():
    results_path = D / "results.jsonl.gz"
opener = gzip.open if str(results_path).endswith(".gz") else open

with opener(results_path, "rt", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        row = json.loads(line)
        n_rows += 1
        pid, ci = row["id"], row["chunk"]
        chunks_present[pid].add(ci)
        cost_total += row.get("cost") or 0
        if row.get("ms") is not None:
            ms_all.append(row["ms"])
        if row.get("tokens") is not None:
            tokens_all.append(row["tokens"])
        ans = row["answers"]
        for k, v in ans.items():
            if k.startswith("q_"):
                extra.setdefault(pid, {})[k] = v
            else:
                merged[pid][k] = v

# two different populations, since the 2026-09-24 re-plan splits passage-level
# questions (stage 1, all 15,212 passages) from the 212 concept booleans
# (stage 2, only the high-value subset) into separate calls:
concept_complete_pids = {
    pid for pid, s in chunks_present.items()
    if "all" in s or "concepts_only" in s or all(ci in s for ci in range(n_chunks))
}
passage_level_pids = {
    pid for pid, s in chunks_present.items()
    if "all" in s or "passage_level" in s or 0 in s
}
print(f"raw result rows: {n_rows}, passages with >=1 chunk: {len(chunks_present)}")
print(f"passages with passage-level answers (stage 1): {len(passage_level_pids)} / {len(candidates)} planned")
print(f"passages with full 212-concept coverage (stage 2): {len(concept_complete_pids)} / {len(candidates)} planned")

errors_path = D / "errors.jsonl"
n_errors = sum(1 for _ in open(errors_path)) if errors_path.exists() else 0
print(f"errors logged: {n_errors}")
print(f"cost total: ${cost_total:.4f}")
if ms_all:
    print(f"latency median {st.median(ms_all):.0f} ms, p90 {sorted(ms_all)[int(len(ms_all)*0.9)]:.0f} ms")
if tokens_all:
    print(f"input tokens median {st.median(tokens_all):.0f}")

# ---- concept-edge comparison (only on complete passages) ----
contradictions = []   # existing edge, p <= UNC
new_high = []          # no edge, p >= SURE
uncertain = []          # existing edge & UNC<=p<PROB   OR   no edge & PROB<=p<SURE
band_counts = Counter()
per_concept = defaultdict(Counter)

for pid in concept_complete_pids:
    cand = candidates[pid]
    existing = set(cand["existing"])
    concept_p = merged[pid]
    for cid, p in concept_p.items():
        if cid not in concepts:
            continue
        has_edge = cid in existing
        if p >= SURE:
            band = "sur(>=0.9)"
        elif p >= PROB:
            band = "probable(0.7-0.9)"
        elif p >= UNC:
            band = "incertain(0.3-0.7)"
        else:
            band = "non(<0.3)"
        band_counts[band] += 1
        per_concept[cid][band] += 1
        if has_edge:
            per_concept[cid]["existant"] += 1
            if p <= UNC:
                per_concept[cid]["existant_contredit"] += 1
                contradictions.append((cid, p, pid))
            elif p < PROB:
                uncertain.append(("edge_faible", cid, p, pid))
        else:
            if p >= SURE:
                new_high.append((cid, p, pid))
            elif p >= PROB:
                uncertain.append(("candidat_proche", cid, p, pid))

excerpt = lambda pid: candidates[pid]["text"][:240].replace("\n", " ")


def centrality_score(e: dict) -> float | None:
    """q_centrality was a raw float score (0-3) in the earliest runs, then
    switched to {'score':..,'probabilities':{'0':..,'1':..,'2':..,'3':..}}."""
    c = e.get("q_centrality")
    if c is None:
        return None
    if isinstance(c, dict):
        return c.get("score")
    return c


def p_theme_or_main(e: dict) -> float | None:
    """P(centrality in {'a theme among others','the main topic'}) = P(index 2 or 3).
    Legacy float-only rows (no probabilities) fall back to a 0/1 proxy from the
    rounded score -- a small minority of early rows, noted in REPORT.md."""
    c = e.get("q_centrality")
    if c is None:
        return None
    if isinstance(c, dict):
        probs = c.get("probabilities") or {}
        if probs:
            return round(probs.get("2", 0) + probs.get("3", 0), 4)
        return 1.0 if round(c.get("score", 0)) >= 2 else 0.0
    return 1.0 if round(c) >= 2 else 0.0

def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    print(f"{path.name}: {len(rows)} lignes")

contradictions.sort(key=lambda t: t[1])  # lowest p first = worst contradiction
write_csv(
    D / "queue_contradictions.csv",
    ["concept_id", "concept_label", "question", "probability", "passage_id", "auteur", "oeuvre", "ref", "langue", "extrait"],
    [
        [cid, short[cid], f"discusses {short[cid]}?", p, pid,
         candidates[pid]["author"], (candidates[pid]["work"] or "")[:50], (candidates[pid]["ref"] or "")[:60],
         candidates[pid]["lang"], excerpt(pid)]
        for cid, p, pid in contradictions
    ],
)

new_high.sort(key=lambda t: -t[1])
write_csv(
    D / "queue_new_high_conf.csv",
    ["concept_id", "concept_label", "question", "probability", "passage_id", "auteur", "oeuvre", "ref", "langue", "extrait"],
    [
        [cid, short[cid], f"discusses {short[cid]}?", p, pid,
         candidates[pid]["author"], (candidates[pid]["work"] or "")[:50], (candidates[pid]["ref"] or "")[:60],
         candidates[pid]["lang"], excerpt(pid)]
        for cid, p, pid in new_high
    ],
)

uncertain.sort(key=lambda t: (t[0], -t[2]))
write_csv(
    D / "queue_uncertain.csv",
    ["type", "concept_id", "concept_label", "question", "probability", "passage_id", "auteur", "oeuvre", "ref", "langue", "extrait"],
    [
        [kind, cid, short[cid], f"discusses {short[cid]}?", p, pid,
         candidates[pid]["author"], (candidates[pid]["work"] or "")[:50], (candidates[pid]["ref"] or "")[:60],
         candidates[pid]["lang"], excerpt(pid)]
        for kind, cid, p, pid in uncertain
    ],
)

# ---- quality flags: OCR / apparatus / modern-language with confidence >= 0.7 ----
BAD_QUALITY = {
    "text with OCR noise or broken words",
    "text mixed with critical apparatus, line numbers or editorial notes",
    "mostly modern-language text",
}
quality_flags = []
for pid in passage_level_pids:
    e = extra.get(pid) or {}
    tq = e.get("q_text_quality")
    if not tq:
        continue
    choice = tq.get("choice")
    probs = tq.get("probabilities") or {}
    p = probs.get(choice, 0.0)
    if choice in BAD_QUALITY and p >= 0.7:
        quality_flags.append((choice, p, pid))
quality_flags.sort(key=lambda t: -t[1])
write_csv(
    D / "queue_quality_flags.csv",
    ["flag", "probability", "passage_id", "auteur", "oeuvre", "ref", "langue", "extrait"],
    [
        [flag, p, pid, candidates[pid]["author"], (candidates[pid]["work"] or "")[:50],
         (candidates[pid]["ref"] or "")[:60], candidates[pid]["lang"], excerpt(pid)]
        for flag, p, pid in quality_flags
    ],
)

# language mismatch flags (metadata says grc/lat, Jev disagrees with high confidence)
lang_mismatch = []
for pid in passage_level_pids:
    e = extra.get(pid) or {}
    meta_lang = candidates[pid]["lang"]
    is_grc = e.get("q_is_greek")
    is_lat = e.get("q_is_latin")
    if is_grc is None or is_lat is None:
        continue
    if meta_lang == "grc" and is_grc < 0.3:
        lang_mismatch.append(("meta=grc,jev_says_not_greek", is_grc, pid))
    if meta_lang == "lat" and is_lat < 0.3:
        lang_mismatch.append(("meta=lat,jev_says_not_latin", is_lat, pid))
lang_mismatch.sort(key=lambda t: t[1])
write_csv(
    D / "queue_language_mismatch.csv",
    ["flag", "probability", "passage_id", "auteur", "oeuvre", "ref", "langue_meta", "extrait"],
    [
        [flag, p, pid, candidates[pid]["author"], (candidates[pid]["work"] or "")[:50],
         (candidates[pid]["ref"] or "")[:60], candidates[pid]["lang"], excerpt(pid)]
        for flag, p, pid in lang_mismatch
    ],
)

# ---- centrality distribution per work / author ----
work_centrality = defaultdict(list)
author_centrality = defaultdict(list)
for pid in passage_level_pids:
    e = extra.get(pid) or {}
    c = centrality_score(e)
    if c is None:
        continue
    cand = candidates[pid]
    work_centrality[(cand["author"] or "?", (cand["work"] or "?"))].append(c)
    author_centrality[cand["author"] or "?"].append(c)

with open(D / "relevance_by_work.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["auteur", "oeuvre", "n_passages", "centralite_moyenne", "centralite_mediane", "pct_theme_principal(>=2.5)"])
    rows = []
    for (author, work), vals in work_centrality.items():
        rows.append((author, work, len(vals), sum(vals) / len(vals), st.median(vals), sum(1 for v in vals if v >= 2.5) / len(vals)))
    rows.sort(key=lambda r: -r[3])
    for r in rows:
        w.writerow([r[0], r[1], r[2], round(r[3], 2), round(r[4], 2), round(r[5], 3)])
print(f"relevance_by_work.csv: {len(work_centrality)} lignes")

with open(D / "relevance_by_author.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["auteur", "n_passages", "centralite_moyenne", "centralite_mediane", "pct_theme_principal(>=2.5)"])
    rows = []
    for author, vals in author_centrality.items():
        rows.append((author, len(vals), sum(vals) / len(vals), st.median(vals), sum(1 for v in vals if v >= 2.5) / len(vals)))
    rows.sort(key=lambda r: -r[2])
    for r in rows:
        w.writerow([r[0], r[1], round(r[2], 2), round(r[3], 2), round(r[4], 3)])
print(f"relevance_by_author.csv: {len(author_centrality)} lignes")

# ---- work-level edge posing: for (work, concept) with >=3 passages carrying the
# existing edge, check whether ALL passages of that work carry it (work-level
# tagging signature), and the contradiction rate Jev finds within that set.
# Coverage denominator uses the FULL candidate population of the work (existing
# edges are known regardless of Jev coverage); the Jev-contradiction rate is
# necessarily restricted to the passages we have concept answers for.
work_passages = defaultdict(list)  # (author,work) -> [pid,...] over ALL candidates
for pid, cand in candidates.items():
    work_passages[(cand["author"] or "?", cand["work"] or "?")].append(pid)

work_level_rows = []
edge_by_work_concept = defaultdict(set)  # (author,work,concept) -> {pid with edge}
for pid, cand in candidates.items():
    key_wa = (cand["author"] or "?", cand["work"] or "?")
    for cid in cand["existing"]:
        if cid in concepts:
            edge_by_work_concept[(key_wa[0], key_wa[1], cid)].add(pid)

FIELDNAMES = ["auteur", "oeuvre", "concept", "n_passages_oeuvre", "n_passages_avec_arete",
              "couverture", "n_evalues_par_jev", "p_mediane_jev", "taux_contredit_par_jev"]
for (author, work, cid), edge_pids in edge_by_work_concept.items():
    total_pids = work_passages.get((author, work), [])
    if len(edge_pids) < 3 or len(total_pids) < 3:
        continue
    coverage = len(edge_pids) / len(total_pids)
    ps = [merged[pid].get(cid) for pid in edge_pids if cid in merged.get(pid, {})]
    ps = [p for p in ps if p is not None]
    row = {
        "auteur": author, "oeuvre": work, "concept": short[cid],
        "n_passages_oeuvre": len(total_pids), "n_passages_avec_arete": len(edge_pids),
        "couverture": round(coverage, 3), "n_evalues_par_jev": len(ps),
        "p_mediane_jev": round(st.median(ps), 3) if ps else None,
        "taux_contredit_par_jev": round(sum(1 for p in ps if p <= UNC) / len(ps), 3) if ps else None,
    }
    work_level_rows.append(row)
work_level_rows.sort(key=lambda r: (-r["couverture"], -(r["taux_contredit_par_jev"] or 0)))
with open(D / "work_level_edges.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDNAMES)
    w.writeheader()
    for r in work_level_rows:
        w.writerow(r)
print(f"work_level_edges.csv: {len(work_level_rows)} lignes ((oeuvre,concept) avec >=3 passages porteurs d'arete)")

high_coverage = [r for r in work_level_rows if r["couverture"] >= 0.8]
print(f"  -> (oeuvre,concept) ou >=80% des passages de l'oeuvre portent l'arete: {len(high_coverage)}")

# ---- summary dump for REPORT.md ----
summary = {
    "n_rows_raw": n_rows,
    "n_passages_passage_level": len(passage_level_pids),
    "n_passages_concept_complete": len(concept_complete_pids),
    "n_passages_planned": len(candidates),
    "n_errors": n_errors,
    "cost_total": cost_total,
    "band_counts": dict(band_counts),
    "n_contradictions": len(contradictions),
    "n_new_high_conf": len(new_high),
    "n_uncertain": len(uncertain),
    "n_quality_flags": len(quality_flags),
    "n_lang_mismatch": len(lang_mismatch),
    "n_work_concept_high_coverage": len(high_coverage),
    "latency_median_ms": st.median(ms_all) if ms_all else None,
    "tokens_median": st.median(tokens_all) if tokens_all else None,
}
with open(D / "summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print("\nsummary:", json.dumps(summary, ensure_ascii=False, indent=1))
