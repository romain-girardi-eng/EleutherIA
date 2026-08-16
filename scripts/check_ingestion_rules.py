#!/usr/bin/env python3
"""Enforceable ingestion rules for the EleutherIA knowledge graph.

Every rule here exists because the defect it forbids was actually found in this
graph. The rule text names the incident. Rules are not advice: BLOCK rules must
be green before an ingestion is written, and the apply scripts call this module.

Two modes:

    python3 scripts/check_ingestion_rules.py                 # audit whole graph
    python3 scripts/check_ingestion_rules.py --new-only FILE  # gate a delta

``--new-only`` takes a JSON file ``{"nodes": [...], "edges": [...]}`` of the
records an ingestion proposes to ADD, and checks them against the live graph
plus each other. That is the pre-flight an ingestion script must pass.

Exit status: 0 if no BLOCK violation, 1 otherwise. WARN never fails the build
but is always printed — a WARN is a human decision, not a free pass.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ONTOLOGY = ROOT / "knowledge graph" / "ontology"

BLOCK, WARN = "BLOCK", "WARN"

violations: list[tuple[str, str, str, str]] = []  # (rule, level, ref, detail)


def fail(rule: str, level: str, ref: str, detail: str) -> None:
    violations.append((rule, level, ref, detail))


# --------------------------------------------------------------------------- io
def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def nid(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def meta(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def surname_tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", strip_accents(s).lower()))


# --------------------------------------------------------------------------- keys
def identity_key(node: dict) -> tuple | None:
    """The key on which a node is considered 'the same thing' as another.

    R2 forbids two nodes sharing a key. Keys differ per type because identity
    differs per type: a work is identified by its canonical text id, a
    publication by its DOI or author+year+title, a person by their name.
    """
    t = node.get("type")
    md = meta(node)
    if t == "work":
        canon = md.get("cts_urn") or md.get("work_canonical_id")
        if canon:
            return ("work", canon)
        # No canonical id: fall back on author + normalised title. Deliberately
        # weak, which is why R3b warns about canon-less works.
        return (
            "work",
            strip_accents(str(md.get("author"))).lower(),
            tuple(sorted(surname_tokens(node.get("label") or ""))),
        )
    if t == "publication":
        doi = md.get("doi")
        if doi and str(doi).strip() and str(doi).upper() != "UNKNOWN":
            return ("publication", str(doi).strip().lower())
        return (
            "publication",
            str(md.get("author_id") or md.get("author") or "").lower(),
            str(md.get("year") or ""),
            tuple(sorted(surname_tokens(node.get("label") or ""))),
        )
    if t == "person":
        return ("person", tuple(strip_accents(node.get("label") or "").lower().split()))
    if t == "passage":
        canon = md.get("cts_urn")
        if canon:
            # A translation legitimately shares its original's CTS URN, so the
            # role is part of passage identity.
            return ("passage", canon, md.get("passage_role") or "original")
    return None


# --------------------------------------------------------------------------- rules
CTS_RE = re.compile(
    r"^urn:cts:[a-zA-Z]+Lit:"
    r"[a-zA-Z]{3,4}\d{3,4}[a-zA-Z]?"
    r"(\.[a-zA-Z]*\d{2,4}[a-zA-Z_]*)?"
    r"(\.[A-Za-z0-9_\-]+)?"
    r"(:[\w.\-]*)?$"
)
URN_PLACEHOLDERS = ("?", "TODO", "todo", "unknown", "UNKNOWN", "xxx", "XXX", "N/A")
GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")

# Relations whose source must be the LATER figure, and the EARLIER one.
LATER_SOURCE = {
    "influenced_by",
    "student_of",
    "responds_to",
    "critiques",
    "interprets",
    "extends",
    "refutes",
    "opposes",
    "agrees_with",
    "uses_methodology_of",
}
EARLIER_SOURCE = {"influences", "teaches", "precedes"}
CHRONO_TOLERANCE = 60


def person_year(node_id: str, node: dict) -> int | None:
    md = meta(node)
    for field in ("floruit", "birth_date", "death_date"):
        raw = md.get(field)
        if not raw:
            continue
        s = re.sub(r"^\s*\d{1,2}(er)?\s+(?=[A-Za-zÀ-ÿ])", "", str(raw))
        s = re.sub(r"\([^)]*\)", " ", s)
        bce = bool(re.search(r"\b(BCE|BC|av\.?\s*J)", s, re.I))
        mm = re.search(r"\b(\d{3,4})\b", s)
        if not mm:
            cent = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th|er|e)?\s*[cs]\b", s, re.I)
            if cent:
                y = int(cent.group(1)) * 100 - 50
                return -y if bce else y
            continue
        y = int(mm.group(1))
        return -y if bce else y
    for pat, sign in (
        (r"_(\d{3,4})_\d{3,4}bce", -1),
        (r"_(\d{3,4})_\d{3,4}ce", 1),
        (r"_d(\d{3,4})\b", 1),
    ):
        mm = re.search(pat, node_id)
        if mm:
            return sign * int(mm.group(1))
    return None


def check(
    nodes: list[dict], edges: list[dict], new_nodes: list[dict], new_edges: list[dict]
) -> None:
    N = {nid(n): n for n in nodes}
    node_types = {k: v.get("type") for k, v in N.items()}
    gated_nodes = new_nodes if new_nodes is not None else nodes
    gated_edges = new_edges if new_edges is not None else edges

    attributed: dict[str, str] = {}
    all_authors: dict[str, set] = collections.defaultdict(set)
    for e in edges:
        if e.get("relation") in ("created_by", "authored_by", "edited_by"):
            attributed.setdefault(e["source"], e["target"])
            all_authors[e["source"]].add(e["target"])
    for e in edges:
        if e.get("relation") == "advanced_in" and e["source"] not in attributed:
            inh = attributed.get(e["target"])
            if inh:
                attributed[e["source"]] = inh

    # ---- R1 provenance ----------------------------------------------------
    # Incident: nodes were created by waves that left no trace of where the
    # claim came from, so later audits could not tell fact from guess.
    if new_nodes is not None:
        for n in gated_nodes:
            prov = meta(n).get("provenance")
            if not isinstance(prov, dict) or not prov.get("source"):
                fail(
                    "R1_provenance_required",
                    BLOCK,
                    nid(n),
                    "new node has no metadata.provenance.source (DOI, ISBN, CTS URN or on-disk path)",
                )

    # ---- R2 identity / dedup ---------------------------------------------
    # Incident: pub_long_1996 vs scholarly_work_long_1996; Crouzel 1962 forked by
    # accent-slugging; Jewett 2007 twice; two work nodes for the Book of the Laws.
    existing_keys: dict[tuple, str] = {}
    for n in nodes:
        k = identity_key(n)
        if k and (new_nodes is None or nid(n) not in {nid(x) for x in new_nodes}):
            existing_keys.setdefault(k, nid(n))
    seen_new: dict[tuple, str] = {}
    for n in gated_nodes:
        k = identity_key(n)
        if not k:
            continue
        if new_nodes is not None and k in existing_keys:
            fail(
                "R2_duplicate_identity",
                BLOCK,
                nid(n),
                f"identity key {k} already held by {existing_keys[k]} — attach to it, do not create",
            )
        if k in seen_new:
            fail(
                "R2_duplicate_identity",
                BLOCK,
                nid(n),
                f"identity key {k} duplicated within this batch ({seen_new[k]})",
            )
        seen_new[k] = nid(n)
    if new_nodes is None:
        dupes = collections.defaultdict(list)
        for n in nodes:
            k = identity_key(n)
            if k:
                dupes[k].append(nid(n))
        for k, ids in dupes.items():
            if len(ids) > 1:
                fail(
                    "R2_duplicate_identity",
                    WARN,
                    ids[0],
                    f"{len(ids)} nodes share identity key {k}: {', '.join(ids[:4])}",
                )

    # ---- R3 one work = one canonical text --------------------------------
    # Incident: 11 work nodes held 30+ works, ~3,350 passages misfiled
    # (Seneca's Letters under De Providentia, Plato's Apology under the Republic).
    kids = collections.defaultdict(list)
    for e in edges:
        if (
            e.get("relation") == "part_of"
            and node_types.get(e["target"]) == "work"
            and node_types.get(e["source"]) == "passage"
        ):
            kids[e["target"]].append(e["source"])
    for w, ps in kids.items():
        canons = {
            meta(N[p]).get("work_canonical_id")
            for p in ps
            if meta(N[p]).get("work_canonical_id")
        }
        if len(canons) > 1:
            fail(
                "R3_work_single_canonical",
                BLOCK,
                w,
                f"work holds passages from {len(canons)} different works: {sorted(canons)}",
            )

    # ---- R3b work without a canonical id ---------------------------------
    for n in gated_nodes:
        if n.get("type") != "work":
            continue
        md = meta(n)
        if not (md.get("cts_urn") or md.get("work_canonical_id")):
            fail(
                "R3b_work_without_canonical_id",
                WARN,
                nid(n),
                "work has neither cts_urn nor work_canonical_id, so it can only be deduplicated "
                "by title — the exact weakness that filed Clement's Protrepticus under Origen's "
                "Exhortation to Martyrdom",
            )

    # ---- R4 passage author must not be inherited -------------------------
    # Incident: 190 passages took their host work's author — 115 of Gregory of
    # Nazianzus were attributed to Augustine.
    work_author = {
        e["source"]: e["target"]
        for e in edges
        if e.get("relation") == "authored_by" and node_types.get(e["source"]) == "work"
    }
    passage_author = {
        e["source"]: e["target"]
        for e in edges
        if e.get("relation") == "authored_by"
        and node_types.get(e["source"]) == "passage"
    }
    for w, ps in kids.items():
        wa = work_author.get(w)
        if not wa:
            continue
        for p in ps:
            pa = passage_author.get(p)
            if pa and pa != wa:
                fail(
                    "R4_passage_author_disagrees_with_work",
                    BLOCK,
                    p,
                    f"passage authored_by {pa} but its work {w} is authored_by {wa}; "
                    "an author is read from the passage's own source, never inherited",
                )

    # ---- R5 CTS URN resolvable -------------------------------------------
    # Incident: 445 Plato passages carried a literal '?' in the URN.
    for n in gated_nodes:
        urn = meta(n).get("cts_urn")
        if not isinstance(urn, str) or not urn:
            continue
        if any(ph in urn for ph in URN_PLACEHOLDERS):
            fail(
                "R5_cts_urn_placeholder",
                BLOCK,
                nid(n),
                f"CTS URN contains a placeholder: {urn}",
            )
        elif not CTS_RE.match(urn):
            fail(
                "R5_cts_urn_malformed",
                WARN,
                nid(n),
                f"CTS URN does not match the grammar: {urn}",
            )

    # ---- R7 a translation must actually translate ------------------------
    # Incident: 340 nodes declared language=eng, passage_role=translation while
    # their text was byte-identical to the Greek or Latin original.
    for n in gated_nodes:
        md = meta(n)
        if md.get("passage_role") != "translation":
            continue
        origin = N.get(md.get("original_node_id"))
        if origin is None:
            fail(
                "R7_translation_without_original",
                BLOCK,
                nid(n),
                "passage_role=translation but original_node_id does not resolve",
            )
            continue
        if (n.get("description") or "").strip() == (
            origin.get("description") or ""
        ).strip():
            fail(
                "R7_translation_identical_to_original",
                BLOCK,
                nid(n),
                f"declared a translation of {nid(origin)} but the text is identical — no translation exists",
            )
        if md.get("language") in (None, "grc", "lat") and GREEK_RE.search(
            n.get("description") or ""
        ):
            fail(
                "R7_translation_language_suspect",
                WARN,
                nid(n),
                f"translation node declares language={md.get('language')!r} and contains Greek script",
            )

    # ---- R8 scholarly claims must resolve --------------------------------
    # Incident: 73 metadata pointers referenced 11 node ids that no longer existed.
    POINTERS = ("scholar_id", "author_id", "scholarly_work_id", "publication")
    for n in gated_nodes:
        md = meta(n)
        for field in POINTERS:
            v = md.get(field)
            if (
                isinstance(v, str)
                and v
                and v not in N
                and re.match(r"^(person|scholar|pub|scholarly_work)_", v)
            ):
                fail(
                    "R8_metadata_pointer_dangling",
                    BLOCK,
                    nid(n),
                    f"{field} -> {v} does not resolve",
                )
        if nid(n).startswith("scholarly_argument_"):
            # Two ingestion waves used different field names for the same thing.
            work_ref = (
                md.get("scholarly_work_id")
                or md.get("e2_publication_id")
                or md.get("publication")
            )
            pages = md.get("page_range") or md.get("page_or_loc") or md.get("chapter")
            if not work_ref:
                fail(
                    "R8_scholarly_argument_unsourced",
                    BLOCK,
                    nid(n),
                    "scholarly argument with no publication reference "
                    "(scholarly_work_id / e2_publication_id / publication)",
                )
            if not md.get("scholar_id") and not attributed.get(nid(n)):
                fail(
                    "R8_scholarly_argument_unsourced",
                    BLOCK,
                    nid(n),
                    "scholarly argument with no scholar_id and no created_by/authored_by edge",
                )
            if work_ref and not md.get("scholarly_work_id"):
                fail(
                    "R8_schema_drift_publication_field",
                    WARN,
                    nid(n),
                    f"publication recorded under a non-canonical key "
                    f"({'e2_publication_id' if md.get('e2_publication_id') else 'publication'}) "
                    "instead of scholarly_work_id",
                )
            if not pages:
                fail(
                    "R8_scholarly_argument_no_pages",
                    WARN,
                    nid(n),
                    "scholarly argument without page_range: the claim cannot be checked against the print",
                )

    # ---- R9 id surname must match the attributed scholar -----------------
    # Incident: 19 ids named the wrong scholar (Gourinat for D'Jeranian,
    # Guyomarc'h for Koch, Cross for Hyatt, Crouzel for Simonetti).
    for n in gated_nodes:
        i = nid(n)
        if not i.startswith(("scholarly_work_", "scholarly_argument_", "pub_")):
            continue
        who = attributed.get(i)
        if not who or who not in N:
            continue
        rest = i.split("_", 2)[2] if i.startswith("scholarly_") else i.split("_", 1)[1]
        sn = rest.split("_")[0]
        if len(sn) < 3:
            continue
        # A multi-author or edited volume is named after one contributor in the
        # id and may be attributed to another: check every author/editor.
        pool = set()
        for cand in all_authors.get(i) or {who}:
            pool |= surname_tokens(cand) | surname_tokens(
                N.get(cand, {}).get("label") or ""
            )
        if sn not in pool and not any(sn in tok or tok in sn for tok in pool):
            fail(
                "R9_id_surname_contradicts_author",
                WARN,
                i,
                f"id says '{sn}' but the node is attributed to {who} ({N[who].get('label')})",
            )

    # ---- R10 never invent a year -----------------------------------------
    # Incident: 10 ids used a '_0_' year placeholder; 7 ids embedded a year that
    # contradicted metadata.year.
    for n in gated_nodes:
        i, md = nid(n), meta(n)
        if (
            re.search(r"_0_[a-z]", i)
            and i.startswith(("scholarly_work_", "pub_"))
            and not md.get("grey_literature")
        ):
            fail(
                "R10_year_placeholder",
                BLOCK,
                i,
                "'_0_' year placeholder without grey_literature=true: either resolve the year "
                "against the print or record why it has none",
            )
        mm = re.search(r"_((?:1[5-9]|20)\d\d)_", i + "_")
        if mm and md.get("year"):
            id_year = mm.group(1)
            declared = str(md["year"])
            # A range such as "1952-53" or "1952/53" legitimately contains the id year.
            years = set(re.findall(r"(?:1[5-9]|20)\d\d", declared))
            years |= {declared[:2] + x for x in re.findall(r"(?<=[-/])(\d{2})$", declared)}
            if id_year not in years:
                fail(
                    "R10_id_year_contradicts_metadata",
                    BLOCK,
                    i,
                    f"id says {id_year}, metadata.year says {declared}",
                )

    # ---- R11/R12 edge hygiene --------------------------------------------
    try:
        ET = json.load((ONTOLOGY / "edge_types.json").open())["edge_types"]
    except Exception:
        ET = {}
    for e in gated_edges:
        r = e.get("relation")
        d = ET.get(r)
        if d is None:
            fail(
                "R11_relation_not_in_ontology",
                BLOCK,
                e.get("edge_id", "?"),
                f"relation {r!r}",
            )
            continue
        st, tt = node_types.get(e["source"]), node_types.get(e["target"])
        if d["source_types"] != ["*"] and st and st not in d["source_types"]:
            fail(
                "R11_edge_source_type",
                BLOCK,
                e.get("edge_id", "?"),
                f"{r}: source type {st} not in {d['source_types']}",
            )
        if d["target_types"] != ["*"] and tt and tt not in d["target_types"]:
            fail(
                "R11_edge_target_type",
                BLOCK,
                e.get("edge_id", "?"),
                f"{r}: target type {tt} not in {d['target_types']}",
            )
        if e.get("source") != e.get("source_id") or e.get("target") != e.get(
            "target_id"
        ):
            fail(
                "R12_edge_fields_unpaired",
                BLOCK,
                e.get("edge_id", "?"),
                "source/source_id or target/target_id disagree — the in-memory and SQL paths "
                "would return different answers",
            )
        if e.get("source") == e.get("target"):
            fail("R12_self_loop", BLOCK, e.get("edge_id", "?"), "self-loop")

    # ---- R13 chronology on directional intellectual relations ------------
    # Incident: 11 edges said Calvin influenced Augustine, Lucretius influenced
    # Epicurus, Boethius influenced Aristotle.
    for e in gated_edges:
        r = e.get("relation")
        if r not in LATER_SOURCE | EARLIER_SOURCE:
            continue
        if (
            node_types.get(e["source"]) != "person"
            or node_types.get(e["target"]) != "person"
        ):
            continue
        ys = person_year(e["source"], N.get(e["source"], {}))
        yt = person_year(e["target"], N.get(e["target"], {}))
        if ys is None or yt is None:
            continue
        if r in LATER_SOURCE and ys + CHRONO_TOLERANCE < yt:
            fail(
                "R13_chronology",
                WARN,
                e.get("edge_id", "?"),
                f"{e['source']} (~{ys}) -[{r}]-> {e['target']} (~{yt}): source predates target",
            )
        if r in EARLIER_SOURCE and yt + CHRONO_TOLERANCE < ys:
            fail(
                "R13_chronology",
                WARN,
                e.get("edge_id", "?"),
                f"{e['source']} (~{ys}) -[{r}]-> {e['target']} (~{yt}): target predates source",
            )

    # ---- R14 no orphan new nodes -----------------------------------------
    # Incident: a verified 1,265-word Hegesippus fragment sat with zero edges,
    # unreachable from the graph; 9 scholars still have none.
    if new_nodes is not None:
        touched = {
            x
            for e in list(edges) + list(new_edges or [])
            for x in (e.get("source"), e.get("target"))
        }
        for n in gated_nodes:
            if nid(n) not in touched:
                fail(
                    "R14_orphan_new_node",
                    BLOCK,
                    nid(n),
                    "new node has no edge: it would be invisible to every retrieval path",
                )

    # ---- R15 id prefix must match type -----------------------------------
    PREFIX = {
        "person_": "person",
        "scholar_": "person",
        "concept_": "concept",
        "scholarly_argument_": "argument",
        "argument_": "argument",
        "work_": "work",
        "passage_": "passage",
        "pub_": "publication",
        "scholarly_work_": "publication",
        "school_": "school",
        "debate_": "debate",
        "quote_": "quote",
        "group_": "group",
        "collection_": "source_collection",
        "controversy_": "controversy",
        "event_": "event",
        "synthesis_": "synthesis",
    }
    for n in gated_nodes:
        i, t = nid(n), n.get("type")
        for p in sorted(PREFIX, key=len, reverse=True):
            if i.startswith(p):
                if PREFIX[p] != t:
                    fail(
                        "R15_id_prefix_type_mismatch",
                        WARN,
                        i,
                        f"prefix '{p}' but type '{t}'",
                    )
                break


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--new-only",
        metavar="FILE",
        help='JSON {"nodes":[...],"edges":[...]} of records to be ADDED',
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="fail on BLOCK in whole-graph mode too (default: report existing debt, exit 0)",
    )
    args = ap.parse_args()

    nodes, edges = read_jsonl(NODES_PATH), read_jsonl(EDGES_PATH)
    new_nodes = new_edges = None
    if args.new_only:
        payload = json.loads(Path(args.new_only).read_text(encoding="utf-8"))
        new_nodes = payload.get("nodes", [])
        new_edges = payload.get("edges", [])
        nodes = nodes + new_nodes
        edges = edges + new_edges

    check(nodes, edges, new_nodes, new_edges)

    blocks = [v for v in violations if v[1] == BLOCK]
    warns = [v for v in violations if v[1] == WARN]
    scope = (
        f"delta of {len(new_nodes)} nodes / {len(new_edges)} edges"
        if new_nodes is not None
        else f"whole graph ({len(nodes)} nodes, {len(edges)} edges)"
    )
    print(f"ingestion-rules: {scope}")

    by_rule = collections.Counter(v[0] for v in violations)
    for rule, n in sorted(by_rule.items()):
        level = (
            BLOCK if any(v[1] == BLOCK for v in violations if v[0] == rule) else WARN
        )
        print(f"  [{level}] {rule}: {n}")
        for v in [x for x in violations if x[0] == rule][:5]:
            print(f"        {v[2]}: {v[3][:150]}")
        if n > 5:
            print(f"        ... +{n - 5} more")

    if not violations:
        print("  no violations")
    print(f"\nBLOCK: {len(blocks)}   WARN: {len(warns)}")
    if new_nodes is None and not args.strict:
        print(
            "whole-graph mode: reporting pre-existing debt, not failing. "
            "New ingestions are gated with --new-only, which does fail."
        )
        return 0
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())
