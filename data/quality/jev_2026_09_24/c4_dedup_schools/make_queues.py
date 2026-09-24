"""Explode chunk-level Jev results back to per-item rows and build the
review-queue CSVs described in BRIEF_COMMON.md. Reads only from this
campaign dir + data/kg/nodes.jsonl (read-only). Writes only under this dir.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict

from build_candidates_school import SCHOOL_CRITERIA
from lib_common import CAMPAIGN_DIR, load_nonpassage_nodes

SCHOOL_KEYWORDS = {
    "Stoic": ["stoic", "zeno", "chrysippus", "seneca", "epictetus", "marcus aurelius", "heimarmen", "stoa"],
    "Epicurean": ["epicurean", "epicurus", "lucretius", "philodemus", "atom", "swerve", "clinamen"],
    "Peripatetic": ["peripatetic", "aristotle", "aristotelian", "lyceum", "alexander of aphrodisias"],
    "Academic/Platonist": ["academ", "plato", "platonist", "platonic"],
    "Middle Platonist": ["middle platon", "alcinous", "plutarch", "numenius", "apuleius"],
    "Neoplatonist": ["neoplaton", "plotinus", "porphyry", "iamblichus", "proclus", "simplicius"],
    "Pyrrhonist/Sceptic": ["pyrrho", "sceptic", "skeptic", "sextus empiricus", "carneades", "epoch"],
    "Presocratic": ["presocratic", "pre-socratic", "heraclitus", "parmenides", "democritus", "anaximander"],
    "Cynic": ["cynic", "diogenes of sinope"],
    "Christian (patristic)": ["patristic", "church father", "christian", "origen", "augustine",
                               "tertullian", "clement of alexandria", "gregory", "apologist"],
    "Gnostic": ["gnostic", "valentinus", "basilides", "demiurge"],
    "Jewish": ["jewish", "judaism", "philo of alexandria", "rabbinic", "talmud"],
    "Hermetic": ["hermetic", "hermes trismegistus", "corpus hermeticum"],
    "Modern scholarship": ["modern scholar", "contemporary philosopher", "20th century", "21st century",
                            "modern commentator"],
}

SENT_SPLIT_RE = re.compile(r"(?<=[.;])\s+")


def find_anchor(description: str, school: str) -> str:
    kws = SCHOOL_KEYWORDS.get(school)
    if not kws:
        return "no textual anchor"
    low = description.lower()
    for sent in SENT_SPLIT_RE.split(description):
        sl = sent.lower()
        if any(kw in sl for kw in kws):
            return sent.strip()[:280]
    if any(kw in low for kw in kws):
        return description.strip()[:280]
    return "no textual anchor"


def tier(p: float) -> str:
    if p >= 0.9:
        return ">=0.9"
    if p >= 0.7:
        return "0.7-0.9"
    if p >= 0.3:
        return "0.3-0.7"
    return "<=0.3"


# ---------------------------------------------------------------------------
# PART A -- dedup
# ---------------------------------------------------------------------------

def explode_dedup() -> list[dict]:
    chunk_map = {}
    with (CAMPAIGN_DIR / "chunks_map_dedup.jsonl").open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            chunk_map[d["id"]] = d["pair_ids"]

    pair_state = {}
    with (CAMPAIGN_DIR / "candidates.jsonl").open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            pair_state[d["pair_id"]] = d

    rows = []
    n_missing = 0
    with (CAMPAIGN_DIR / "results_dedup.jsonl").open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            pair_ids = chunk_map.get(d["id"])
            if not pair_ids:
                continue
            answers = d.get("answers") or {}
            for i, pid in enumerate(pair_ids):
                same = (answers.get(f"same_{i}") or {}).get("probability")
                part = (answers.get(f"part_{i}") or {}).get("probability")
                if same is None:
                    n_missing += 1
                    continue
                cand = pair_state.get(pid)
                if not cand:
                    continue
                rows.append({
                    "pair_id": pid,
                    "type": cand["type"],
                    "a_id": cand["a"]["id"], "a_name": cand["a"]["name"],
                    "b_id": cand["b"]["id"], "b_name": cand["b"]["name"],
                    "same_probability": same,
                    "part_of_probability": part,
                    "reasons": ";".join(cand.get("reasons", [])),
                    "a_desc_excerpt": (cand["a"]["description"] or "")[:200],
                    "b_desc_excerpt": (cand["b"]["description"] or "")[:200],
                })
    print(f"exploded dedup rows: {len(rows)} (missing answers: {n_missing})")
    return rows


def suggest_survivor(a_id: str, b_id: str, node_edge_count: dict[str, int],
                      node_meta_richness: dict[str, int]) -> str:
    ea, eb = node_edge_count.get(a_id, 0), node_edge_count.get(b_id, 0)
    if ea != eb:
        return a_id if ea > eb else b_id
    ma, mb = node_meta_richness.get(a_id, 0), node_meta_richness.get(b_id, 0)
    return a_id if ma >= mb else b_id


def write_dedup_queues(rows: list[dict]) -> None:
    # edge counts, computed from data/kg/edges.jsonl (read-only) for the survivor heuristic
    from lib_common import REPO_ROOT
    edges_path = REPO_ROOT / "data" / "kg" / "edges.jsonl"
    edge_count: dict[str, int] = defaultdict(int)
    if edges_path.exists():
        with edges_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                s = e.get("source") or e.get("source_id")
                t = e.get("target") or e.get("target_id")
                if s:
                    edge_count[s] += 1
                if t:
                    edge_count[t] += 1

    nodes = load_nonpassage_nodes()
    meta_richness = {n["id"]: len(json.dumps(n.get("metadata") or {})) for n in nodes}

    for r in rows:
        r["survivor_suggestion"] = suggest_survivor(r["a_id"], r["b_id"], edge_count, meta_richness)
        r["tier"] = tier(r["same_probability"])

    likely_dup = sorted(
        [r for r in rows if r["same_probability"] >= 0.9],
        key=lambda r: -r["same_probability"],
    )
    ambiguous = sorted(
        [r for r in rows if 0.3 <= r["same_probability"] < 0.9],
        key=lambda r: -r["same_probability"],
    )
    part_of_only = sorted(
        [r for r in rows if r["same_probability"] < 0.9 and r["part_of_probability"] >= 0.7],
        key=lambda r: -r["part_of_probability"],
    )
    rejected_sample = sorted(
        [r for r in rows if r["same_probability"] < 0.3 and r["part_of_probability"] < 0.3],
        key=lambda r: -r["same_probability"],
    )[:300]

    fieldnames = ["pair_id", "type", "a_id", "a_name", "b_id", "b_name",
                  "same_probability", "part_of_probability", "tier",
                  "survivor_suggestion", "reasons", "a_desc_excerpt", "b_desc_excerpt"]

    def write_csv(path, data):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)
        print(f"  {path.name}: {len(data)} rows")

    write_csv(CAMPAIGN_DIR / "queue_likely_duplicates.csv", likely_dup)
    write_csv(CAMPAIGN_DIR / "queue_ambiguous_pairs.csv", ambiguous)
    write_csv(CAMPAIGN_DIR / "queue_part_of_relations.csv", part_of_only)
    write_csv(CAMPAIGN_DIR / "queue_rejected_sample.csv", rejected_sample)

    return {
        "n_total": len(rows),
        "n_likely_dup": len(likely_dup),
        "n_ambiguous": len(ambiguous),
        "n_part_of": len(part_of_only),
        "n_rejected": len(rows) - len(likely_dup) - len(ambiguous),
    }


# ---------------------------------------------------------------------------
# PART B -- school proposals
# ---------------------------------------------------------------------------

def _explode_school_pass(chunk_map_path, candidates_path, results_path) -> tuple[list[dict], int]:
    chunk_map = {}
    with chunk_map_path.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            chunk_map[d["id"]] = d["node_ids"]

    node_state = {}
    with candidates_path.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            node_state[d["node_id"]] = d

    rows = []
    n_missing = 0
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            node_ids = chunk_map.get(d["id"])
            if not node_ids:
                continue
            answers = d.get("answers") or {}
            confidence = d.get("confidence") or {}
            for i, nid in enumerate(node_ids):
                ans = answers.get(f"school_{i}")
                if not ans:
                    n_missing += 1
                    continue
                cand = node_state.get(nid)
                if not cand:
                    continue
                choice = ans.get("choice")
                probs = ans.get("probabilities") or {}
                p = probs.get(choice, 0)
                desc = cand["state"]["description"] or ""
                rows.append({
                    "node_id": nid,
                    "type": cand["type"],
                    "name": cand["state"]["name"],
                    "existing_school": cand.get("existing_school") or "",
                    "proposed_school": choice,
                    "probability": p,
                    "confidence": confidence.get(f"school_{i}"),
                    "anchor_sentence": find_anchor(desc, choice),
                    "desc_excerpt": desc[:220],
                })
    return rows, n_missing


def explode_school() -> list[dict]:
    rows, n_missing = _explode_school_pass(
        CAMPAIGN_DIR / "chunks_map_school.jsonl",
        CAMPAIGN_DIR / "candidates_school.jsonl",
        CAMPAIGN_DIR / "results_school.jsonl",
    )
    seen = {r["node_id"] for r in rows}
    n_missing_pw = 0
    pw_map = CAMPAIGN_DIR / "chunks_map_school_pw.jsonl"
    if pw_map.exists():
        pw_rows, n_missing_pw = _explode_school_pass(
            pw_map,
            CAMPAIGN_DIR / "candidates_school_pw.jsonl",
            CAMPAIGN_DIR / "results_school_pw.jsonl",
        )
        for r in pw_rows:
            if r["node_id"] not in seen:  # person/work priority pass takes precedence, no dupes
                rows.append(r)
                seen.add(r["node_id"])
    print(f"exploded school rows: {len(rows)} (missing answers: {n_missing + n_missing_pw})")
    return rows


def write_school_queues(rows: list[dict]) -> dict:
    determinate = {"No school affiliation / not a school-bound figure",
                   "Cannot be determined from the description"}

    fill_in = sorted(
        [r for r in rows if not r["existing_school"] and r["proposed_school"] not in determinate
         and r["probability"] >= 0.9],
        key=lambda r: -r["probability"],
    )
    conflicts = sorted(
        [r for r in rows if r["existing_school"] and r["proposed_school"] not in determinate
         and r["existing_school"] != r["proposed_school"] and r["probability"] >= 0.8],
        key=lambda r: -r["probability"],
    )
    undetermined = sorted(
        [r for r in rows if r["proposed_school"] in determinate or r["probability"] < 0.5],
        key=lambda r: r["probability"],
    )

    fieldnames = ["node_id", "type", "name", "existing_school", "proposed_school",
                  "probability", "confidence", "anchor_sentence", "desc_excerpt"]

    def write_csv(path, data):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)
        print(f"  {path.name}: {len(data)} rows")

    write_csv(CAMPAIGN_DIR / "queue_school_fill_in.csv", fill_in)
    write_csv(CAMPAIGN_DIR / "queue_school_conflicts.csv", conflicts)
    write_csv(CAMPAIGN_DIR / "queue_school_undetermined.csv", undetermined)

    return {
        "n_total": len(rows),
        "n_fill_in": len(fill_in),
        "n_conflicts": len(conflicts),
        "n_undetermined": len(undetermined),
    }


def main() -> None:
    print("=== Part A dedup ===")
    dedup_rows = explode_dedup()
    with (CAMPAIGN_DIR / "exploded_dedup.jsonl").open("w", encoding="utf-8") as f:
        for r in dedup_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    dedup_stats = write_dedup_queues(dedup_rows)
    print(dedup_stats)

    print("=== Part B school ===")
    school_rows = explode_school()
    with (CAMPAIGN_DIR / "exploded_school.jsonl").open("w", encoding="utf-8") as f:
        for r in school_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    school_stats = write_school_queues(school_rows)
    print(school_stats)

    stats = {"dedup": dedup_stats, "school": school_stats}
    (CAMPAIGN_DIR / "queue_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
