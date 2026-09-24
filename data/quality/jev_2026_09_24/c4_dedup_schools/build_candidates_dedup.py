"""PART A -- deterministic candidate-pair construction for entity resolution.

Reads data/kg/nodes.jsonl (READ-ONLY), blocks non-passage nodes by type, and
proposes candidate duplicate/part-of pairs via:
  1. shared significant tokens in label + alternative_names (Jaccard-filtered
     inverted index, hub tokens excluded to avoid combinatorial blow-up)
  2. shared significant tokens in the first 500 chars of description
  3. exact bibtex_key match (publications)
  4. (author surname, year) match (publications)
  5. shared surname (person)

Writes candidates.jsonl: one row per pair with the two node states truncated
to <=2500 chars description, plus the blocking reason(s) and a cheap prior
score (not used to filter -- for queue sorting only).

Does not call Jev. Nothing under data/kg/* is written.
"""

from __future__ import annotations

import itertools
import json
from collections import defaultdict
from typing import Any

from lib_common import CAMPAIGN_DIR, load_nonpassage_nodes, significant_tokens

MAX_DESC_CHARS = 2500
DESC_BLOCK_CHARS = 500
MAX_PAIRS = 30000

# Metadata keys worth surfacing per type (keeps state compact, avoids huge
# nested blobs like amand_location / provenance notes).
META_WHITELIST = [
    "author", "authors", "editors", "bibtex_key", "year", "publisher",
    "book_title", "journal", "pages", "place", "type",
    "birth_date", "death_date", "cts_urn", "work_canonical_id",
    "date_composed", "wikidata_qid",
]


def node_state(n: dict[str, Any]) -> dict[str, Any]:
    meta = n.get("metadata") or {}
    meta_small = {k: meta[k] for k in META_WHITELIST if k in meta and meta[k]}
    desc = (n.get("description") or "")[:MAX_DESC_CHARS]
    return {
        "id": n["id"],
        "type": n.get("type"),
        "name": n.get("label"),
        "alternative_names": n.get("alternative_names") or [],
        "period": n.get("period"),
        "school": n.get("school"),
        "description": desc,
        "metadata": meta_small,
    }


def surname_of(label: str) -> str:
    """Best-effort surname: text before first comma, else first significant
    token before a parenthesis, else last significant token."""
    base = label.split("(")[0].strip()
    if "," in base:
        return significant_tokens(base.split(",")[0]).pop() if significant_tokens(base.split(",")[0]) else ""
    toks = [t for t in significant_tokens(base)]
    if not toks:
        return ""
    # last capitalized-ish word of the raw (pre-normalization) base as heuristic
    raw_words = [w.strip(".,;:") for w in base.split() if w.strip(".,;:")]
    for w in reversed(raw_words):
        if len(w) >= 3 and w[0].isupper():
            return significant_tokens(w).pop() if significant_tokens(w) else w.lower()
    return toks[-1]


def author_year_key(n: dict[str, Any]) -> tuple[str, str] | None:
    meta = n.get("metadata") or {}
    author = meta.get("author") or meta.get("authors")
    year = meta.get("year")
    if not author:
        # fall back to bibtex_key pattern author-year-...
        bk = meta.get("bibtex_key") or ""
        parts = bk.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            return (parts[0], parts[1])
        return None
    if isinstance(author, list):
        author = author[0] if author else ""
    surname = significant_tokens(str(author))
    surname_key = sorted(surname)[0] if surname else str(author).lower()
    return (surname_key, str(year)) if year else None


def build_inverted_index(
    nodes_by_id: dict[str, dict], tok_fn, hub_cap: int
) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for nid, n in nodes_by_id.items():
        for tok in tok_fn(n):
            idx[tok].append(nid)
    return {t: ids for t, ids in idx.items() if 2 <= len(ids) <= hub_cap}


def pairs_from_index(idx: dict[str, list[str]]) -> dict[frozenset, set[str]]:
    pairs: dict[frozenset, set[str]] = defaultdict(set)
    for tok, ids in idx.items():
        for a, b in itertools.combinations(sorted(set(ids)), 2):
            pairs[frozenset((a, b))].add(tok)
    return pairs


def main() -> None:
    nodes = load_nonpassage_nodes()
    print(f"non-passage nodes loaded: {len(nodes)}")
    by_type: dict[str, list[dict]] = defaultdict(list)
    for n in nodes:
        by_type[n.get("type")].append(n)

    all_candidates: dict[frozenset, dict[str, Any]] = {}

    for ntype, tnodes in by_type.items():
        nodes_by_id = {n["id"]: n for n in tnodes}
        N = len(tnodes)
        hub_cap = 25 if N > 100 else 12

        def label_toks(n, _=None):
            toks = significant_tokens(n.get("label"))
            for alt in n.get("alternative_names") or []:
                toks |= significant_tokens(str(alt))
            return toks

        def desc_toks(n):
            return significant_tokens((n.get("description") or "")[:DESC_BLOCK_CHARS], min_len=5)

        label_idx = build_inverted_index(nodes_by_id, label_toks, hub_cap)
        desc_idx = build_inverted_index(nodes_by_id, desc_toks, hub_cap)

        label_pairs = pairs_from_index(label_idx)
        desc_pairs = pairs_from_index(desc_idx)

        # merge, tag reason
        merged: dict[frozenset, dict[str, Any]] = {}
        for pair, toks in label_pairs.items():
            merged.setdefault(pair, {"reasons": [], "shared_tokens": set()})
            merged[pair]["reasons"].append("label_token_overlap")
            merged[pair]["shared_tokens"] |= toks
        for pair, toks in desc_pairs.items():
            merged.setdefault(pair, {"reasons": [], "shared_tokens": set()})
            merged[pair]["reasons"].append("description_token_overlap")
            merged[pair]["shared_tokens"] |= toks

        # publication-specific: bibtex_key exact + author/year
        if ntype == "publication":
            bibtex_idx: dict[str, list[str]] = defaultdict(list)
            ay_idx: dict[tuple, list[str]] = defaultdict(list)
            for n in tnodes:
                bk = (n.get("metadata") or {}).get("bibtex_key")
                if bk:
                    bibtex_idx[bk].append(n["id"])
                ay = author_year_key(n)
                if ay:
                    ay_idx[ay].append(n["id"])
            for bk, ids in bibtex_idx.items():
                if 2 <= len(ids) <= 30:
                    for a, b in itertools.combinations(sorted(set(ids)), 2):
                        pair = frozenset((a, b))
                        merged.setdefault(pair, {"reasons": [], "shared_tokens": set()})
                        merged[pair]["reasons"].append("bibtex_key_exact")
            for ay, ids in ay_idx.items():
                if 2 <= len(ids) <= 30:
                    for a, b in itertools.combinations(sorted(set(ids)), 2):
                        pair = frozenset((a, b))
                        merged.setdefault(pair, {"reasons": [], "shared_tokens": set()})
                        merged[pair]["reasons"].append("author_year_match")

        # person-specific: shared surname
        if ntype == "person":
            surname_idx: dict[str, list[str]] = defaultdict(list)
            for n in tnodes:
                sn = surname_of(n.get("label") or "")
                if sn:
                    surname_idx[sn].append(n["id"])
            for sn, ids in surname_idx.items():
                if 2 <= len(ids) <= 20:
                    for a, b in itertools.combinations(sorted(set(ids)), 2):
                        pair = frozenset((a, b))
                        merged.setdefault(pair, {"reasons": [], "shared_tokens": set()})
                        merged[pair]["reasons"].append("shared_surname")

        strong_reasons = {"bibtex_key_exact", "author_year_match", "shared_surname"}
        filtered: dict[frozenset, dict[str, Any]] = {}
        for pair, info in merged.items():
            reasons = set(info["reasons"])
            weak_only = not (reasons & strong_reasons)
            if weak_only and len(info["shared_tokens"]) < 2:
                continue
            score = len(reasons) + 0.1 * len(info["shared_tokens"])
            info["score"] = score
            info["type"] = ntype
            filtered[pair] = info
        all_candidates.update(filtered)
        print(f"  type={ntype:22s} N={N:5d} hub_cap={hub_cap:3d} raw_pairs={len(merged):7d} "
              f"kept={len(filtered):6d}")

    print(f"TOTAL candidate pairs before cap: {len(all_candidates)}")

    ranked = sorted(all_candidates.items(), key=lambda kv: -kv[1]["score"])
    if len(ranked) > MAX_PAIRS:
        print(f"capping to top {MAX_PAIRS} by prior score")
        ranked = ranked[:MAX_PAIRS]

    nodes_by_id_all = {n["id"]: n for n in nodes}
    out_path = CAMPAIGN_DIR / "candidates.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for pair, info in ranked:
            a_id, b_id = sorted(pair)
            a, b = nodes_by_id_all[a_id], nodes_by_id_all[b_id]
            row = {
                "pair_id": f"{a_id}__{b_id}",
                "type": info["type"],
                "reasons": sorted(set(info["reasons"])),
                "shared_tokens": sorted(info["shared_tokens"])[:20],
                "prior_score": round(info["score"], 2),
                "a": node_state(a),
                "b": node_state(b),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(ranked)} pairs -> {out_path}")


if __name__ == "__main__":
    main()
