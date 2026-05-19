#!/usr/bin/env python3
"""Phase E1 — wire modern ``argument`` nodes flagged ``needs_evidence`` to the
publication that hosts the underlying scholarly thesis.

Context
-------
After the orphan-argument repair (``wire_orphan_arguments_2026_05_18.py``),
989 modern arguments still carry ``needs_evidence=true`` *without* any edge
pointing at a publication. 872 of them belong to a scholar that already has
at least one publication node in the KG → those can be auto-wired.

This pass does *not* claim a passage-level proof has been attached
(``needs_evidence`` is preserved). It only declares: "this scholarly thesis
is discussed in publication X" — the textual evidence still needs a human
curation pass later.

Ontology
--------
Checked against ``knowledge graph/ontology/edge_types.json`` on 2026-05-19:

  * ``discusses``      source=argument allowed, target=publication **NOT** allowed
  * ``discussed_in``   source=argument allowed, target=publication **NOT** allowed
  * ``discusses``      source=publication allowed, target=argument **allowed**

The existing KG carries **474** ``publication → argument`` edges with
relation ``discusses`` (the precedent set by Phase 0 of the orphan-wiring
pass) and only 5 stray ``argument → publication`` edges (``critiques``). We
therefore emit **publication → argument** ``discusses`` edges — same
direction, same relation as the established precedent and the only
ontology-clean option.

Strategy
--------
For each candidate argument (type=argument, period ∈ {Contemporary, Modern,
Early Modern}, metadata.needs_evidence=true, id matches
``(?:scholarly_argument_|scholar_argument_|argument_)<surname_token>_*``,
no existing edge to/from any ``pub_*`` via discusses/discussed_in/discusses_pub/
discussed_in_pub):

  1. Resolve scholar via the ID surname slug (re-uses surname extraction +
     COMPOUND_HEADS + HARDCODED_SURNAME_TO_PERSONS from
     ``wire_orphan_arguments_2026_05_18.py``).

  2. Compute scholar→publications via outgoing ``authored_by`` edges
     (and inbound ``wrote``/``creates``).

  3. If scholar has exactly 1 publication → wire it,
     ``wiring_confidence=high``, ``pub_match_method=unique_pub``.
     If multiple → score each pub by Jaccard(arg-tokens, pub-title-tokens);
     pick the best.

       * score >= 0.5  → high   (``title_jaccard_strong``)
       * 0.2 <= score < 0.5 → medium (``title_jaccard_weak``)
       * score <  0.2  → skip, mark ``wiring_status=manual_review``

  4. Each wired edge: ``publication → argument`` ``discusses``,
     metadata::

         { "auto_generated": true,
           "wave": "wire_modern_args_to_pubs_2026_05_19",
           "pub_match_method": "unique_pub" | "title_jaccard_strong" | "title_jaccard_weak",
           "match_score": <float>,
           "wiring_confidence": "high" | "medium" }

  5. Argument node patched with::

         pub_evidence_attached: true
         e1_wired_at: "2026-05-19"
         e1_pub_id: "<pub_id>"

     ``needs_evidence`` is intentionally **preserved** — the publication
     pointer is not a passage-level proof.

Idempotency
-----------
Re-running is a no-op:

  * arguments already carrying ``e1_wired_at=2026-05-19`` are skipped
  * edge dedup via ``(source, target, relation)`` signature against the
    existing edges.jsonl

Snapshot
--------
A pre-mutation snapshot is written to
``data/kg/snapshots/2026-05-19-pre-e1-modern-args-wiring/`` (nodes + edges).

Usage
-----
  python3 scripts/wire_modern_args_to_pubs_2026_05_19.py            # dry-run
  python3 scripts/wire_modern_args_to_pubs_2026_05_19.py --commit   # apply
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-e1-modern-args-wiring"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"

WAVE_DATE = "2026-05-19"
WAVE_TAG = "wire_modern_args_to_pubs_2026_05_19"

MODERN_PERIODS = frozenset({"Contemporary", "Modern", "Early Modern"})
PUB_RELATIONS_BLOCKING = frozenset({
    "discusses",
    "discussed_in",
    "discusses_pub",
    "discussed_in_pub",
})
ARG_ID_PREFIXES = (
    "scholarly_argument_",
    "scholar_argument_",
    "scholar_position_",
    "argument_",
)

# Disambiguation overrides for ambiguous scholar surnames (same defaults as the
# 2026-05-18 orphan-wiring pass for consistency).
SCHOLAR_DISAMBIGUATION: dict[str, str] = {
    "frede": "scholar_frede_michael",
    "koch": "scholar_koch_i",
}

# Surname slugs we must hard-route because the diacritic-stripped slug doesn't
# survive our label-derived slug pipeline.
HARDCODED_SURNAME_TO_PERSONS: dict[str, list[str]] = {
    "f_rst": ["scholar_furst_alfons"],
    "l_demann": ["scholar_l_demann_g"],
    "l_hr": ["scholar_l_hr_w"],
}

PARTICLES = ("o", "f", "de", "la", "van", "von", "du", "l", "el")
COMPOUND_HEADS: dict[str, frozenset[str]] = {
    "engberg": frozenset({"pedersen"}),
    "boys": frozenset({"stones"}),
    "denzey": frozenset({"lewis"}),
    "acosta": frozenset({"l"}),
    "amand": frozenset({"de"}),
    "koch": frozenset({"piettre"}),
}

STOP_TOKENS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "is", "are", "as", "from", "at", "be", "this", "that", "his", "her", "its",
    "their", "s", "de", "la", "le", "et", "du", "des", "en", "un", "une",
})


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for src in (NODES_PATH, EDGES_PATH):
        dst = SNAPSHOT_DIR / src.name
        if not dst.exists():
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# Surname / token helpers
# ---------------------------------------------------------------------------

def normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def label_slug(label: str) -> str:
    out_chars: list[str] = []
    for c in label.lower():
        if c.isalnum() and c.isascii():
            out_chars.append(c)
        elif c == " " or c == "-":
            out_chars.append("_")
        elif c.isalpha():
            out_chars.append("_")
    return re.sub(r"_+", "_", "".join(out_chars)).strip("_")


def extract_surname_from_arg_id(aid: str) -> str | None:
    body = aid
    for prefix in ARG_ID_PREFIXES:
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    parts = body.split("_")
    if not parts:
        return None
    p0 = parts[0]
    if p0 in PARTICLES and len(parts) >= 2:
        return f"{p0}_{parts[1]}"
    if p0 in COMPOUND_HEADS and len(parts) >= 2 and parts[1] in COMPOUND_HEADS[p0]:
        return f"{p0}_{parts[1]}"
    return p0


def person_surname_variants(person: dict) -> set[str]:
    out: set[str] = set()
    pid = person["id"]
    label = person.get("label", "") or ""
    body = pid
    for prefix in ("scholar_", "person_"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    body = body.replace("_contemporary", "")
    parts = body.split("_")

    def _is_hash(tok: str) -> bool:
        return bool(tok) and 6 <= len(tok) <= 12 and any(c.isdigit() for c in tok)

    while parts and (len(parts[-1]) == 1 or _is_hash(parts[-1])):
        parts.pop()
    while parts and parts[-1].isdigit():
        parts.pop()
    if parts:
        p0 = parts[0]
        if p0 in PARTICLES and len(parts) >= 2:
            out.add(f"{p0}_{parts[1]}")
            out.add(parts[1])
        elif p0 in COMPOUND_HEADS and len(parts) >= 2 and parts[1] in COMPOUND_HEADS[p0]:
            out.add(f"{p0}_{parts[1]}")
            out.add(p0)
        else:
            out.add(p0)
    slug = label_slug(label)
    toks = [t for t in slug.split("_") if t]
    if toks:
        out.add(toks[-1])
        if len(toks) >= 2:
            out.add(f"{toks[-2]}_{toks[-1]}")
            if toks[-2] in PARTICLES and len(toks) >= 3:
                out.add(f"{toks[-3]}_{toks[-2]}_{toks[-1]}")
    norm = normalize(label)
    words = re.findall(r"[a-z]+", norm)
    if words:
        out.add(words[-1])
        if len(words) >= 2 and words[-2] in ("de", "van", "von", "la", "le", "du", "mc"):
            out.add(f"{words[-2]}_{words[-1]}")
    return {x for x in out if x and len(x) >= 2}


def tokens(text: str) -> set[str]:
    if not text:
        return set()
    norm = normalize(text)
    return {t for t in re.findall(r"[a-z]+", norm) if len(t) >= 3 and t not in STOP_TOKENS}


def topic_slug_from_arg_id(aid: str, surname: str) -> str:
    body = aid
    for prefix in ARG_ID_PREFIXES:
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    if body.startswith(surname + "_"):
        body = body[len(surname) + 1:]
    body = re.sub(r"_+\d+$", "", body)
    return body


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def build_scholar_index(nodes: list[dict]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        if n.get("type") != "person":
            continue
        pid = n["id"]
        for sn in person_surname_variants(n):
            if pid not in idx[sn]:
                idx[sn].append(pid)
    for sn, persons in HARDCODED_SURNAME_TO_PERSONS.items():
        for pid in persons:
            if pid not in idx[sn]:
                idx[sn].insert(0, pid)
    return idx


def is_scholarly_person(pid: str) -> bool:
    return pid.startswith("scholar_") or pid.endswith("_contemporary")


def pick_scholar(surname: str, candidates: list[str]) -> tuple[str | None, str, str]:
    if not candidates:
        return None, "none", "no candidate"
    if surname in SCHOLAR_DISAMBIGUATION:
        forced = SCHOLAR_DISAMBIGUATION[surname]
        if forced in candidates:
            return forced, "high", f"override:{surname}"
    scholar_pri = [c for c in candidates if c.startswith("scholar_")]
    contemporary = [c for c in candidates if c.endswith("_contemporary")]
    others = [c for c in candidates if c not in scholar_pri and c not in contemporary]
    ranked = scholar_pri + contemporary + others
    if len([c for c in candidates if is_scholarly_person(c)]) == 1:
        return ranked[0], "high", "unique-scholarly"
    if len(candidates) == 1:
        return ranked[0], "high", "unique"
    return ranked[0], "medium", f"ambiguous:{len(candidates)}"


def build_scholar_pubs(nodes: list[dict], edges: list[dict]) -> tuple[dict[str, set[str]], dict[str, dict]]:
    pubs = {n["id"]: n for n in nodes if n.get("type") == "publication"}
    edges_out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_in: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        edges_out[s].append((r, t))
        edges_in[t].append((r, s))
    scholar_pubs: dict[str, set[str]] = defaultdict(set)
    for pid in pubs:
        for r, t in edges_out[pid]:
            if r == "authored_by":
                scholar_pubs[t].add(pid)
        for r, s in edges_in[pid]:
            if r in ("wrote", "creates"):
                scholar_pubs[s].add(pid)
    return scholar_pubs, pubs


# ---------------------------------------------------------------------------
# Metadata helpers (metadata is sometimes a JSON string, sometimes a dict)
# ---------------------------------------------------------------------------

def parse_metadata(md_raw) -> dict:
    if isinstance(md_raw, dict):
        return dict(md_raw)
    if isinstance(md_raw, str) and md_raw.strip():
        try:
            parsed = json.loads(md_raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def serialize_metadata(md: dict, original) -> object:
    """Preserve the original metadata storage format (str vs dict)."""
    if isinstance(original, str):
        return json.dumps(md, ensure_ascii=False)
    return md


# ---------------------------------------------------------------------------
# Publication matching
# ---------------------------------------------------------------------------

YEAR_RE = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")


def extract_years(text: str) -> set[str]:
    return set(YEAR_RE.findall(text or ""))


def pub_year(pub_node: dict) -> str | None:
    """Best-effort: look at label, id, then metadata for a 4-digit year."""
    for field in (pub_node.get("label", ""), pub_node.get("id", "")):
        m = YEAR_RE.search(field or "")
        if m:
            return m.group(1)
    md = pub_node.get("metadata")
    if isinstance(md, dict):
        for v in md.values():
            if isinstance(v, str):
                m = YEAR_RE.search(v)
                if m:
                    return m.group(1)
    elif isinstance(md, str):
        m = YEAR_RE.search(md)
        if m:
            return m.group(1)
    return None


def near_duplicate_titles(pubs: dict[str, dict], pub_ids: set[str]) -> bool:
    """True iff all candidate pubs share the same token signature (e.g.
    Amand 1945 vs Amand 1973: same title, different year)."""
    sigs = set()
    for pid in pub_ids:
        title = pubs[pid].get("label", "") or ""
        toks = frozenset(t for t in tokens(title) if not t.isdigit())
        if not toks:
            return False
        sigs.add(toks)
    return len(sigs) == 1


def match_publication(
    scholar_pubs: set[str],
    pubs: dict[str, dict],
    topic: str,
    desc: str,
    label: str,
) -> tuple[str | None, str, float, str]:
    """Return (pub_id|None, confidence, score, method)."""
    if not scholar_pubs:
        return None, "none", 0.0, "no_pub"
    if len(scholar_pubs) == 1:
        return next(iter(scholar_pubs)), "high", 1.0, "unique_pub"

    arg_text = " ".join((topic.replace("_", " "), label, desc))
    arg_tokens = tokens(arg_text)
    arg_years = extract_years(arg_text)

    # 1. Year disambiguation: if exactly one pub's year is mentioned in the arg
    #    text, route there with high confidence (deterministic, no invention).
    year_hits: list[str] = []
    if arg_years:
        for pid in scholar_pubs:
            py = pub_year(pubs[pid])
            if py and py in arg_years:
                year_hits.append(pid)
        if len(year_hits) == 1:
            return year_hits[0], "high", 1.0, "year_match"

    # 2. Title scoring: blend Jaccard with directional coverage
    #    (how many pub-title content tokens appear in the arg). This is the
    #    right metric when pub titles are short and arg descriptions are long.
    best_score = 0.0
    best_method = "title_jaccard_weak"
    best_id: str | None = None
    for pid in scholar_pubs:
        title = pubs[pid].get("label", "") or ""
        # Drop the author surname and year tokens from the pub title — they
        # are not discriminating between the same scholar's pubs.
        pub_tokens = {t for t in tokens(title) if not t.isdigit()}
        if not pub_tokens:
            continue
        inter = arg_tokens & pub_tokens
        if not inter:
            continue
        jacc = len(inter) / len(arg_tokens | pub_tokens)
        coverage = len(inter) / len(pub_tokens)  # fraction of pub-title tokens recovered
        # Composite score: coverage dominates (titles are short), Jaccard
        # discounts for arg-token noise.
        composite = 0.7 * coverage + 0.3 * jacc
        if composite > best_score:
            best_score = composite
            best_id = pid

    if best_id is not None:
        if best_score >= 0.6:
            return best_id, "high", best_score, "title_jaccard_strong"
        if best_score >= 0.3:
            return best_id, "medium", best_score, "title_jaccard_weak"

    # 3. Fallback for near-duplicate titles (same canonical work, different
    #    editions/years). Pick the most recent edition with medium confidence —
    #    this is the standard scholarly default when no year cue exists.
    if near_duplicate_titles(pubs, scholar_pubs):
        with_years = [(pid, pub_year(pubs[pid])) for pid in scholar_pubs]
        dated = [(pid, y) for pid, y in with_years if y is not None]
        if dated:
            dated.sort(key=lambda x: x[1], reverse=True)
            return dated[0][0], "medium", 0.0, "near_duplicate_latest_edition"

    return None, "manual_review", best_score, "title_jaccard_low"


# ---------------------------------------------------------------------------
# Edge helpers
# ---------------------------------------------------------------------------

def signature(s: str, t: str, r: str) -> tuple[str, str, str]:
    return (s, t, r)


def edge_record(source: str, target: str, relation: str, *, weight: float, meta: dict) -> dict:
    now = datetime.now(UTC).isoformat(sep=" ")
    return {
        "created_at": now,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(meta, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="apply changes; otherwise dry-run")
    parser.add_argument("--limit", type=int, default=None, help="process only first N candidates (debug)")
    args = parser.parse_args(argv)

    mode = "COMMIT" if args.commit else "dry-run"
    print(f"=== Phase E1 :: modern-arg → publication wiring  ({mode}) ===")

    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"loaded {len(nodes)} nodes, {len(edges)} edges")

    nodes_by_id = {n["id"]: n for n in nodes}

    # Build edge indices and existing signatures
    existing_signatures: set[tuple[str, str, str]] = set()
    edges_out_by_src: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_in_by_tgt: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        existing_signatures.add(signature(s, t, r))
        edges_out_by_src[s].append((r, t))
        edges_in_by_tgt[t].append((r, s))

    pub_ids: set[str] = {n["id"] for n in nodes if n.get("type") == "publication"}

    # Pre-compute which arguments already have a pub-pointing edge.
    def has_pub_link(arg_id: str) -> bool:
        for r, t in edges_out_by_src[arg_id]:
            if r in PUB_RELATIONS_BLOCKING and t in pub_ids:
                return True
        for r, s in edges_in_by_tgt[arg_id]:
            if r in PUB_RELATIONS_BLOCKING and s in pub_ids:
                return True
        return False

    # Find candidates
    candidates: list[dict] = []
    for n in nodes:
        if n.get("type") != "argument":
            continue
        if (n.get("period") or "") not in MODERN_PERIODS:
            continue
        md = parse_metadata(n.get("metadata"))
        if md.get("needs_evidence") is not True:
            continue
        aid = n["id"]
        if not any(aid.startswith(p) for p in ARG_ID_PREFIXES):
            continue
        if md.get("e1_wired_at") == WAVE_DATE:
            continue  # idempotency
        if has_pub_link(aid):
            continue  # already wired
        candidates.append(n)
    print(f"candidate modern arguments (needs_evidence, no pub-link): {len(candidates)}")

    if args.limit:
        candidates = candidates[: args.limit]

    scholar_idx = build_scholar_index(nodes)
    scholar_pubs, pubs = build_scholar_pubs(nodes, edges)

    stat: Counter = Counter()
    by_scholar: Counter = Counter()
    by_scholar_wired: Counter = Counter()
    new_edges: list[dict] = []
    edge_seen: set[tuple[str, str, str]] = set(existing_signatures)
    node_updates: dict[str, dict] = {}
    manual_review: list[tuple[str, str, float]] = []
    unmatched_scholar: list[tuple[str, str]] = []
    scholar_no_pub: list[tuple[str, str]] = []
    compound_cases: list[tuple[str, str]] = []

    for arg in candidates:
        aid = arg["id"]
        desc = arg.get("description", "") or ""
        label = arg.get("label", "") or ""

        surname = extract_surname_from_arg_id(aid)
        if not surname:
            stat["skip_no_surname"] += 1
            continue

        # Track compound-name handling for the report
        if "_" in surname:
            compound_cases.append((aid, surname))

        cand_persons = scholar_idx.get(surname, [])
        scholar_id, scholar_conf, scholar_reason = pick_scholar(surname, cand_persons)

        if not scholar_id or scholar_id not in nodes_by_id:
            stat["skip_scholar_not_found"] += 1
            unmatched_scholar.append((aid, surname))
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            if (
                md.get("wiring_status") == "scholar_not_found"
                and md.get("e1_attempted_surname") == surname
            ):
                continue  # already flagged, idempotent
            md["wiring_status"] = "scholar_not_found"
            md["e1_attempted_surname"] = surname
            patched = dict(arg)
            patched["metadata"] = serialize_metadata(md, md_orig)
            node_updates[aid] = patched
            continue

        by_scholar[scholar_id] += 1

        pubs_for_scholar = scholar_pubs.get(scholar_id, set())
        if not pubs_for_scholar:
            stat["skip_scholar_no_pub"] += 1
            scholar_no_pub.append((aid, scholar_id))
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            if md.get("wiring_status") == "scholar_pub_not_found":
                continue
            md["wiring_status"] = "scholar_pub_not_found"
            patched = dict(arg)
            patched["metadata"] = serialize_metadata(md, md_orig)
            node_updates[aid] = patched
            continue

        topic = topic_slug_from_arg_id(aid, surname)
        pub_id, pub_conf, score, method = match_publication(
            pubs_for_scholar, pubs, topic, desc, label
        )

        if pub_id is None:
            stat["skip_no_match"] += 1
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            score_r = round(score, 3)
            if (
                md.get("wiring_status") == "manual_review"
                and md.get("e1_match_score") == score_r
            ):
                continue
            md["wiring_status"] = "manual_review"
            md["e1_match_score"] = score_r
            patched = dict(arg)
            patched["metadata"] = serialize_metadata(md, md_orig)
            node_updates[aid] = patched
            continue

        if pub_conf == "manual_review":
            stat["skip_manual_review"] += 1
            manual_review.append((aid, scholar_id, score))
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            score_r = round(score, 3)
            if (
                md.get("wiring_status") == "manual_review"
                and md.get("e1_match_score") == score_r
            ):
                continue
            md["wiring_status"] = "manual_review"
            md["e1_match_score"] = score_r
            patched = dict(arg)
            patched["metadata"] = serialize_metadata(md, md_orig)
            node_updates[aid] = patched
            continue

        # Emit publication → argument :: discusses
        sig = signature(pub_id, aid, "discusses")
        if sig in edge_seen:
            stat["skip_edge_exists"] += 1
            continue
        meta = {
            "auto_generated": True,
            "wave": WAVE_TAG,
            "pub_match_method": method,
            "match_score": round(score, 3),
            "wiring_confidence": pub_conf,
            "relation_type": "scholarly_thesis",
        }
        new_edges.append(edge_record(pub_id, aid, "discusses", weight=0.85, meta=meta))
        edge_seen.add(sig)
        stat[f"edges_discusses_{pub_conf}"] += 1
        stat[f"method_{method}"] += 1
        stat["edges_total"] += 1
        by_scholar_wired[scholar_id] += 1

        # Patch arg node
        md_orig = arg.get("metadata")
        md = parse_metadata(md_orig)
        md["pub_evidence_attached"] = True
        md["e1_wired_at"] = WAVE_DATE
        md["e1_pub_id"] = pub_id
        md["e1_match_method"] = method
        md["e1_match_score"] = round(score, 3)
        md["e1_wiring_confidence"] = pub_conf
        # NB: needs_evidence stays True on purpose — passage-level evidence
        # is still missing; only the publication pointer is established.
        patched = dict(arg)
        patched["metadata"] = serialize_metadata(md, md_orig)
        node_updates[aid] = patched

    # ------------------------- Report -------------------------
    print("\n=== Stats ===")
    for k in (
        "edges_total",
        "edges_discusses_high",
        "edges_discusses_medium",
        "method_unique_pub",
        "method_year_match",
        "method_title_jaccard_strong",
        "method_title_jaccard_weak",
        "method_near_duplicate_latest_edition",
        "skip_manual_review",
        "skip_no_match",
        "skip_scholar_not_found",
        "skip_scholar_no_pub",
        "skip_edge_exists",
        "skip_no_surname",
    ):
        print(f"  {k}: {stat[k]}")
    print(f"  total node updates: {len(node_updates)}")

    print("\nTop 20 scholars (by wired-arg count):")
    for sid, c in by_scholar_wired.most_common(20):
        label = nodes_by_id.get(sid, {}).get("label", sid)
        pubs_count = len(scholar_pubs.get(sid, set()))
        print(f"  {c:>3}  ({pubs_count} pub) {sid:<45} {label[:40]}")

    if manual_review:
        print(f"\nManual review (top 15 of {len(manual_review)}, multi-pub ambiguity):")
        for aid, sid, sc in manual_review[:15]:
            n_pubs = len(scholar_pubs.get(sid, set()))
            print(f"  [score={sc:.3f}] {aid}  scholar={sid} (#pubs={n_pubs})")

    if unmatched_scholar:
        print(f"\nUnmatched scholar (top 15 of {len(unmatched_scholar)}):")
        sample_surnames: Counter = Counter(sn for _, sn in unmatched_scholar)
        for sn, c in sample_surnames.most_common(15):
            print(f"  {c:>3}  surname={sn!r}")

    if scholar_no_pub:
        print(f"\nScholar has no publication node (top 15 of {len(scholar_no_pub)}):")
        sample_sids: Counter = Counter(sid for _, sid in scholar_no_pub)
        for sid, c in sample_sids.most_common(15):
            label = nodes_by_id.get(sid, {}).get("label", sid)
            print(f"  {c:>3}  {sid:<45} {label[:40]}")

    if compound_cases:
        print(f"\nCompound-name surname matches handled: {len(compound_cases)}")
        compounds_uniq: Counter = Counter(sn for _, sn in compound_cases)
        for sn, c in compounds_uniq.most_common(10):
            print(f"  {c:>3}  surname={sn!r}")

    if not args.commit:
        print("\n(dry-run; pass --commit to write)")
        return 0

    # ------------------------- Apply --------------------------
    if not new_edges and not node_updates:
        print("\nOK: nothing to apply.")
        return 0

    snapshot()
    print(f"\nsnapshot written to {SNAPSHOT_DIR}")

    if node_updates:
        new_nodes = []
        for n in nodes:
            if n["id"] in node_updates:
                new_nodes.append(node_updates[n["id"]])
            else:
                new_nodes.append(n)
        write_jsonl(NODES_PATH, new_nodes)
        print(f"updated {len(node_updates)} nodes in {NODES_PATH.name}")

    if new_edges:
        with EDGES_PATH.open("a", encoding="utf-8") as fh:
            for e in new_edges:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"appended {len(new_edges)} edges to {EDGES_PATH.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
