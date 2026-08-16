#!/usr/bin/env python3
"""Apply the 2026-08-17 semantic-merge wave.

See ``data_2026_08_17_semantic_merges.py`` for the evidence behind every
operation, and ``data/audit/2026-08-17_semantic_merges_plan.md`` for the plan.

Nothing here is applied from a list of ids alone. Every merge re-reads BOTH
nodes and re-checks the property that made them a duplicate — same locus, same
publication, same DB passage uuid, same chapter — and refuses (with a logged
SKIP) when the graph has moved since the plan was written. Running the script
twice is a no-op.

Usage:
    python3 scripts/apply_2026_08_17_semantic_merges.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_semantic_merges import (  # noqa: E402
    AMAND_1945,
    LOT1_DESTREE_PAIRS,
    LOT1_PAGES_TRUSTED,
    LOT2_BOETHIUS,
    LOT3_EN_DUPLICATES,
    LOT3_LIB_ARB_APPARATUS,
    LOT3_WORK_MERGE,
    LOT4_EDGE_REPAIRS,
    LOT4_PUBLICATION_MERGES,
    LOT5_CAFMA_MERGES,
    LOT5_DEFERRED,
    LOT5_EDGE_DROPS,
    LOT5_RESCOPE,
    LOT5_WITNESS_FIX,
    LOT6_EDGE_DROPS,
    LOT6_MERGES,
    LOT6_PAGE_RANGE_CONFLICTS,
    LOT6_PUBLICATION_KEYS,
    LOT7_EDITORS,
    NOW,
    REJECTED,
    SAME_THESIS_AS,
    STAMP,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"
AUDIT_SEMANTIC = ROOT / "data" / "audit" / "2026-08-16_deep_audit_semantic.jsonl"
REPORT_PATH = ROOT / "data" / "audit" / "2026-08-17_semantic_merges_applied.md"
BACKUP_SUFFIX = ".bak-semantic_merges"

# Clusters whose members are genuinely distinct arguments: never star-linked.
LINK_SKIP_TITLE_PREFIXES = ("CAFMA", "Destrée/Salles")

# Metadata keys that record history and must never be rewritten by the
# id-remap pass.
# They record what an id USED to be; rewriting them would erase the trail.
HISTORY_KEY_RE = re.compile(
    r"(merged_from|previous_node_id|_pre_\d{4}|_remapped_|renamed_from|"
    r"remapped_from|superseded_by_history|_history$|_before$|"
    r"_absorbed_description$|_chapter_synthesis$|_repointed_from$|_retyped_from$)"
)

log: list[str] = []
counts: collections.Counter = collections.Counter()


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] += 1


def skip(op: str, msg: str) -> None:
    log.append(f"[{op}] SKIPPED: {msg}")
    counts[f"{op}__skipped"] += 1


# --------------------------------------------------------------------------- io
def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def set_meta(node: dict, data: dict) -> None:
    """Write metadata back in the shape it was stored in (some are JSON strings)."""
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        node["metadata"] = data


def nfc(s: str | None) -> str:
    return unicodedata.normalize("NFC", s or "")


def pubkey(source_file: str | None) -> str | None:
    s = nfc(source_file).split("/")[-1]
    for key, patterns in LOT6_PUBLICATION_KEYS.items():
        for pattern in patterns:
            if nfc(pattern) in s:
                return key
    return None


def page_spans(page_range: str | None) -> list[tuple[int, int]] | None:
    if not page_range:
        return None
    spans: list[tuple[int, int]] = []
    for token in re.findall(r"\d+\s*-\s*\d+|\d+", page_range):
        if "-" in token:
            a, b = (int(x) for x in token.split("-"))
            spans.append((a, b))
        else:
            spans.append((int(token), int(token)))
    return spans or None


def pages_compatible(a: str | None, b: str | None) -> bool:
    sa, sb = page_spans(a), page_spans(b)
    if sa is None or sb is None:
        return True
    return any(x[0] <= y[1] and y[0] <= x[1] for x in sa for y in sb)


# ------------------------------------------------------------------- merge core
class Wave:
    def __init__(self) -> None:
        self.nodes = read_jsonl(NODES_PATH)
        self.edges = read_jsonl(EDGES_PATH)
        self.before = (len(self.nodes), len(self.edges))
        self.N = {nid(n): n for n in self.nodes}
        self.remap: dict[str, str] = {}          # absorbed -> survivor
        self.drop_edges: set[tuple[str, str, str]] = set()
        self.new_edges: list[dict] = []
        self.deferred_edges: list[str] = []
        self.degree = collections.Counter()
        for e in self.edges:
            self.degree[e["source"]] += 1
            self.degree[e["target"]] += 1
        with ONTOLOGY_PATH.open(encoding="utf-8") as fh:
            self.ontology = json.load(fh)

    # -- helpers ------------------------------------------------------------
    def resolve(self, node_id: str) -> str:
        seen = set()
        while node_id in self.remap and node_id not in seen:
            seen.add(node_id)
            node_id = self.remap[node_id]
        return node_id

    def alive(self, node_id: str) -> bool:
        return node_id in self.N and node_id not in self.remap

    def merge(
        self,
        survivor: str,
        absorbed: str,
        reason: str,
        lot: str,
        port_keys: list[str] | None = None,
        rewrite_keys: dict[str, str] | None = None,
        port_description_as: str | None = None,
    ) -> bool:
        """Record a merge after re-reading both nodes. Returns True if recorded."""
        op = f"merge_{lot}"
        if survivor not in self.N:
            skip(op, f"{absorbed} -> {survivor}: survivor missing")
            return False
        if absorbed not in self.N:
            skip(op, f"{absorbed} -> {survivor}: already merged or absent")
            return False
        if absorbed in self.remap:
            skip(op, f"{absorbed}: already scheduled for merge")
            return False
        src, dst = self.N[absorbed], self.N[survivor]
        sm, dm = meta(src), meta(dst)

        # port metadata absent from the survivor
        ported: list[str] = []
        keys = port_keys if port_keys is not None else sorted(sm)
        for key in keys:
            if key not in sm or HISTORY_KEY_RE.search(key):
                continue
            if key in dm and dm[key] not in (None, "", [], {}):
                continue
            dm[key] = sm[key]
            ported.append(key)
        for key, value in (rewrite_keys or {}).items():
            if key in sm:
                dm[key] = value
                ported.append(f"{key}(rewritten)")
        # richer description or citation verdict never silently lost
        if port_description_as and src.get("description"):
            dm.setdefault(port_description_as, src["description"])
            ported.append(port_description_as)
        elif len(src.get("description") or "") > len(dst.get("description") or ""):
            dm.setdefault(f"{STAMP}_absorbed_description", src["description"])
            ported.append("absorbed_description")
        if sm.get("citation_verdict") and not dm.get("citation_verdict"):
            dm["citation_verdict"] = sm["citation_verdict"]
            ported.append("citation_verdict")
        for key in ("cited_in", "verified_reference", "page_range", "bibtex_key",
                    "doi", "isbn", "source_file"):
            if sm.get(key) and not dm.get(key):
                dm[key] = sm[key]
                ported.append(key)

        merged_from = list(dm.get("merged_from") or [])
        if absorbed not in merged_from:
            merged_from.append(absorbed)
        dm["merged_from"] = merged_from
        dm.setdefault(f"{STAMP}_merges", {})
        if isinstance(dm[f"{STAMP}_merges"], dict):
            dm[f"{STAMP}_merges"][absorbed] = reason
        dm[STAMP] = True
        set_meta(dst, dm)
        dst["updated_at"] = NOW

        self.remap[absorbed] = survivor
        note(op, f"{absorbed} -> {survivor} (ported: {', '.join(ported) or 'nothing'})")
        return True

    # -- edge rewrite -------------------------------------------------------
    def rewrite_edges(self) -> None:
        types = {nid(n): n.get("type") for n in self.nodes}
        et = self.ontology["edge_types"]
        seen: set[tuple[str, str, str]] = set()
        kept: list[dict] = []
        for edge in self.edges:
            triple0 = (edge["source"], edge["relation"], edge["target"])
            if triple0 in self.drop_edges:
                note("edge_dropped", f"{triple0[0]} -{triple0[1]}-> {triple0[2]}")
                continue
            src = self.resolve(edge["source"])
            dst = self.resolve(edge["target"])
            if src == dst:
                note("edge_selfloop_dropped",
                     f"{triple0[0]} -{triple0[1]}-> {triple0[2]} collapsed onto {src}")
                continue
            triple = (src, edge["relation"], dst)
            if triple in self.drop_edges:
                note("edge_dropped", f"{src} -{edge['relation']}-> {dst}")
                continue
            if triple in seen:
                counts["edge_deduplicated"] += 1
                continue
            if triple in LOT4_EDGE_REPAIRS:
                repair = LOT4_EDGE_REPAIRS[triple]
                if repair is None:
                    note("edge_repair_dropped",
                         f"{src} -{edge['relation']}-> {dst} (no legal relation)")
                    continue
                new_src, new_rel, new_dst, reason = repair
                if (new_src, new_rel, new_dst) in seen:
                    counts["edge_deduplicated"] += 1
                    continue
                data = edge.get("metadata")
                if isinstance(data, dict):
                    data[STAMP] = True
                    data[f"{STAMP}_retyped_from"] = list(triple)
                    data[f"{STAMP}_retype_reason"] = reason
                    edge["metadata"] = data
                edge["source"] = edge["source_id"] = new_src
                edge["target"] = edge["target_id"] = new_dst
                edge["relation"] = new_rel
                src, dst = new_src, new_dst
                triple = (new_src, new_rel, new_dst)
                note("edge_repaired", f"{triple[0]} -{new_rel}-> {triple[2]}")
            spec = et.get(edge["relation"])
            if spec and triple != triple0:
                st, tt = types.get(src), types.get(dst)
                ok_s = "*" in spec["source_types"] or st in spec["source_types"]
                ok_t = "*" in spec["target_types"] or tt in spec["target_types"]
                if not (ok_s and ok_t):
                    self.deferred_edges.append(
                        f"{src} ({st}) -{edge['relation']}-> {dst} ({tt}) — "
                        f"illegal after merge; not written"
                    )
                    counts["edge_deferred_type_violation"] += 1
                    continue
            if (src, dst) != (edge["source"], edge["target"]):
                data = edge.get("metadata")
                if isinstance(data, dict):
                    data[STAMP] = True
                    data[f"{STAMP}_repointed_from"] = list(triple0)
                    edge["metadata"] = data
                edge["source"] = edge["source_id"] = src
                edge["target"] = edge["target_id"] = dst
                counts["edge_repointed"] += 1
            seen.add(triple)
            kept.append(edge)
        for edge in self.new_edges:
            triple = (edge["source"], edge["relation"], edge["target"])
            if triple in seen or edge["source"] == edge["target"]:
                counts["new_edge_deduplicated"] += 1
                continue
            seen.add(triple)
            kept.append(edge)
        self.edges = kept

    def add_edge(self, source: str, relation: str, target: str, reason: str,
                 lot: str) -> None:
        if not (self.alive(source) and self.alive(target)):
            skip(f"edge_{lot}", f"{source} -{relation}-> {target}: endpoint absent")
            return
        if source == target:
            return
        self.new_edges.append({
            "created_at": NOW,
            "edge_id": f"semmerge-{relation}-{source}-{target}",
            "metadata": {STAMP: True, "reason": reason},
            "relation": relation,
            "source": source,
            "source_id": source,
            "target": target,
            "target_id": target,
            "weight": 1.0,
        })
        note(f"edge_{lot}", f"{source} -{relation}-> {target}")

    # -- id remap inside metadata and citations -----------------------------
    def remap_in_obj(self, obj, changed: list[str]):
        if isinstance(obj, str):
            target = self.resolve(obj)
            if target != obj and obj in self.remap:
                changed.append(f"{obj} -> {target}")
                return target
            return obj
        if isinstance(obj, list):
            return [self.remap_in_obj(x, changed) for x in obj]
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                out[k] = v if HISTORY_KEY_RE.search(k) else self.remap_in_obj(v, changed)
            return out
        return obj

    def remap_metadata(self) -> None:
        for node in self.nodes:
            if nid(node) in self.remap:
                continue
            data = meta(node)
            if not data:
                continue
            changed: list[str] = []
            new = self.remap_in_obj(data, changed)
            if changed:
                set_meta(node, new)
                note("metadata_pointer", f"{nid(node)}: {'; '.join(sorted(set(changed)))}")
        for edge in self.edges:
            data = edge.get("metadata")
            if not isinstance(data, dict):
                continue
            changed: list[str] = []
            new = self.remap_in_obj(data, changed)
            if changed:
                edge["metadata"] = new
                counts["metadata_pointer_edge"] += 1

    def remap_citations(self) -> list[dict] | None:
        if not CITATIONS_PATH.exists():
            return None
        rows = read_jsonl(CITATIONS_PATH)
        touched = 0
        for row in rows:
            changed: list[str] = []
            new = self.remap_in_obj(row, changed)
            if changed:
                row.clear()
                row.update(new)
                touched += 1
        counts["citations_rows_repointed"] = touched
        return rows


# ---------------------------------------------------------------------- lots
def lot0_ontology(w: Wave) -> None:
    et = w.ontology["edge_types"]
    name = SAME_THESIS_AS["name"]
    if name in et:
        skip("ontology", f"{name} already declared")
        return
    rebuilt: dict = {}
    for key, value in et.items():
        rebuilt[key] = value
        if key == SAME_THESIS_AS["after"]:
            rebuilt[name] = SAME_THESIS_AS["definition"]
    if name not in rebuilt:
        rebuilt[name] = SAME_THESIS_AS["definition"]
    w.ontology["edge_types"] = rebuilt
    old, new = SAME_THESIS_AS["version_bump"]
    if w.ontology.get("version") == old:
        w.ontology["version"] = new
    note("ontology", f"declared {name} (version {old} -> {w.ontology.get('version')})")


def lot1_destree(w: Wave) -> None:
    for synth, arg, chapter, pages in LOT1_DESTREE_PAIRS:
        if synth not in w.N or arg not in w.N:
            skip("merge_lot1", f"{synth} / {arg}: node missing")
            continue
        # precondition: the synthesis really is the summary of this chapter and
        # the argument really is that chapter's argument.
        sdesc = w.N[synth].get("description") or ""
        adesc = w.N[arg].get("description") or ""
        number = str(int(chapter[2:]))
        if not re.search(rf"ch\.?\s*0?{number}\b", sdesc):
            skip("merge_lot1", f"{synth}: description does not name ch. {number}")
            continue
        if not re.search(rf"ch\.?\s*0?{number}\b", adesc) and "2014" not in adesc:
            skip("merge_lot1", f"{arg}: description does not tie it to Destrée 2014 ch. {number}")
            continue
        if w.N[synth].get("type") != "synthesis" or w.N[arg].get("type") != "argument":
            skip("merge_lot1", f"{synth}/{arg}: unexpected node types")
            continue
        # survivor = the argument node (dialectical wiring); absorbed = synthesis
        if not w.merge(arg, synth,
                       f"Destrée/Salles/Zingano 2014 {chapter}: chapter summary and "
                       f"chapter argument ingested in the same pass; the argument node "
                       f"carries the dialectical wiring, the synthesis node has zero "
                       f"inbound edges.",
                       "lot1", port_description_as=f"{STAMP}_chapter_synthesis"):
            continue
        node = w.N[arg]
        data = meta(node)
        data["destree2014_chapter"] = chapter
        if chapter in LOT1_PAGES_TRUSTED:
            data.setdefault("page_range", pages)
            data["destree2014_chapter_pages"] = pages
        else:
            data["destree2014_chapter_pages_claimed"] = pages
            data["needs_page_verification"] = (
                "Chapter page ranges of ch01 and ch16-ch22 contradict each other "
                "in the source syntheses (ch16 301-322 vs ch19 295-310 vs ch20 "
                "311-328); not written to page_range."
            )
        set_meta(node, data)


def lot2_boethius(w: Wave) -> None:
    cfg = LOT2_BOETHIUS
    short = sorted(i for i in w.N if i.startswith(cfg["short_prefix"]))
    done = 0
    for sid in short:
        suffix = sid[len(cfg["short_prefix"]):]
        lid = cfg["long_prefix"] + suffix
        if lid not in w.N:
            skip("merge_lot2", f"{sid}: no {lid}")
            continue
        sm, lm = meta(w.N[sid]), meta(w.N[lid])
        if sm.get("canonical_ref") != lm.get("canonical_ref"):
            skip("merge_lot2", f"{sid}: canonical_ref differs")
            continue
        if sm.get("cts_urn") != lm.get("cts_urn"):
            skip("merge_lot2", f"{sid}: cts_urn differs")
            continue
        if sm.get("db_passage_id") and lm.get("passage_id") and \
           sm["db_passage_id"] != lm["passage_id"]:
            skip("merge_lot2", f"{sid}: DB passage uuid differs")
            continue
        short_text = (w.N[sid].get("description") or "").strip()
        long_text = w.N[lid].get("description") or ""
        stripped = long_text
        if stripped.startswith(cfg["strip_prefix"]):
            stripped = stripped[len(cfg["strip_prefix"]):]
        stripped = re.sub(cfg["strip_tail_pattern"], "", stripped).strip()
        if stripped != short_text:
            skip("merge_lot2", f"{sid}: Latin does not match {lid} after unwrapping")
            continue
        # survivor = the long id (whole semantic layer + its _en children)
        if not w.merge(lid, sid, cfg["reason"], "lot2",
                       port_keys=cfg["port_metadata_keys"]):
            continue
        # unwrap the survivor's text: proven identical to the attested twin
        node = w.N[lid]
        if node["description"] != stripped:
            data = meta(node)
            data[f"{STAMP}_text_unwrapped"] = (
                "Removed the editorial 'Latin: ' prefix and the trailing "
                f"self-citation. The result is byte-identical to {sid}, which "
                "held the same Latin unwrapped. No Latin was edited."
            )
            set_meta(node, data)
            node["description"] = stripped
            counts["lot2_text_unwrapped"] += 1
        done += 1
    if done != cfg["expected_pairs"]:
        note("lot2_pair_count", f"{done} pairs merged, plan expected "
                                f"{cfg['expected_pairs']}")


def lot3(w: Wave) -> None:
    # 3a — the two work nodes
    cfg = LOT3_WORK_MERGE
    surv, absorbed = cfg["survivor"], cfg["absorbed"]
    if surv in w.N and absorbed in w.N:
        sm, am = meta(w.N[surv]), meta(w.N[absorbed])
        if sm.get("author") != am.get("author"):
            skip("merge_lot3a", "author differs between the two work nodes")
        elif not sm.get("cts_urn"):
            skip("merge_lot3a", f"{surv} has no cts_urn — refusing to keep it")
        else:
            w.merge(surv, absorbed, cfg["reason"], "lot3a",
                    port_keys=cfg["port_metadata_keys"],
                    rewrite_keys=cfg["rewrite_metadata_keys"])
    else:
        skip("merge_lot3a", "one of the two work nodes is absent")

    # 3b — the apparatus family: URN + role + pointer, NO merge
    ap = LOT3_LIB_ARB_APPARATUS
    text_by_ref = {}
    for i in w.N:
        if i.startswith(ap["text_prefix"]):
            text_by_ref[meta(w.N[i]).get("canonical_ref")] = i
    fixed_urn = fixed_role = pointed = 0
    for i in sorted(w.N):
        if not i.startswith(ap["apparatus_prefix"]) or i.endswith(LOT3_EN_DUPLICATES["suffix"]):
            continue
        data = meta(w.N[i])
        ref = data.get("canonical_ref")
        twin = text_by_ref.get(ref)
        if not twin:
            skip("lot3b", f"{i}: no primary-text twin for {ref}")
            continue
        twin_meta = meta(w.N[twin])
        twin_urn = twin_meta.get("cts_urn") or ""
        if not twin_urn.endswith(":" + str(ref)):
            skip("lot3b", f"{twin}: its own URN does not end in {ref}; not used as source")
        elif data.get("cts_urn") != twin_urn:
            data[f"{STAMP}_cts_urn_before"] = data.get("cts_urn")
            data["cts_urn"] = twin_urn
            data[f"{STAMP}_cts_urn_fix"] = (
                f"The stored URN did not resolve to this node's own "
                f"canonical_ref {ref}; taken from {twin}, whose URN does."
            )
            fixed_urn += 1
        if data.get("passage_role") == ap["role_from"]:
            data["passage_role"] = ap["role_to"]
            data[f"{STAMP}_role_fix"] = (
                "This node is an editorial apparatus (English summary + elided "
                "Latin excerpt + translation + glossary), not the continuous "
                f"text: that is {twin}."
            )
            fixed_role += 1
        if data.get(ap["pointer_key"]) != twin:
            data[ap["pointer_key"]] = twin
            pointed += 1
        set_meta(w.N[i], data)
    counts["lot3b_cts_urn_fixed"] = fixed_urn
    counts["lot3b_role_summary"] = fixed_role
    counts["lot3b_primary_text_pointer"] = pointed

    # 3c — the 170 zero-information _en copies
    en = LOT3_EN_DUPLICATES
    for i in sorted(w.N):
        if not (i.startswith(en["prefix"]) and i.endswith(en["suffix"])):
            continue
        parent = i[: -len(en["suffix"])]
        if parent not in w.N:
            skip("merge_lot3c", f"{i}: parent {parent} absent")
            continue
        data = meta(w.N[i])
        if data.get("passage_role") != en["require_role"]:
            skip("merge_lot3c", f"{i}: role is {data.get('passage_role')!r}")
            continue
        if (w.N[i].get("description") or "") != (w.N[parent].get("description") or ""):
            skip("merge_lot3c", f"{i}: not byte-identical to {parent}")
            continue
        if en["require_parent_contains"] not in (w.N[parent].get("description") or ""):
            skip("merge_lot3c", f"{parent}: carries no inline translation")
            continue
        w.merge(parent, i, en["reason"], "lot3c", port_keys=[])


def lot4(w: Wave) -> None:
    for survivor, absorbed, reason in LOT4_PUBLICATION_MERGES:
        if survivor not in w.N or absorbed not in w.N:
            skip("merge_lot4", f"{absorbed} -> {survivor}: node absent (earlier wave?)")
            continue
        sm, am = meta(w.N[survivor]), meta(w.N[absorbed])
        sy, ay = sm.get("year"), am.get("year")
        if sy and ay and sy != ay:
            note("lot4_year_resolved", f"{absorbed} -> {survivor}: year {ay} "
                                       f"superseded by the verified {sy} (see plan)")
        w.merge(survivor, absorbed, reason, "lot4")
        # the survivor's own year is authoritative; never take the absorbed one
        data = meta(w.N[survivor])
        if sy:
            data["year"] = sy
        set_meta(w.N[survivor], data)


def lot5(w: Wave) -> None:
    for survivor, absorbed, reason in LOT5_CAFMA_MERGES:
        if survivor not in w.N or absorbed not in w.N:
            skip("merge_lot5", f"{absorbed} -> {survivor}: node absent")
            continue
        w.merge(survivor, absorbed, reason, "lot5")

    for source, relation, target, reason in LOT5_EDGE_DROPS:
        w.drop_edges.add((source, relation, target))
        log.append(f"[edge_drop_lot5] {source} -{relation}-> {target}: {reason}")

    # witness list, verified against the printed book
    fix = LOT5_WITNESS_FIX
    if fix["node"] in w.N:
        data = meta(w.N[fix["node"]])
        data["amand_1945_witnesses"] = AMAND_1945["witnesses"]
        data["amand_1945_witnesses_page"] = AMAND_1945["witnesses_page"]
        data["amand_1945_iron_rule"] = AMAND_1945["iron_rule"]
        data["amand_1945_series"] = [
            {"n": n, "heading": h, "witnesses_pages": p1, "synthesis_pages": p2}
            for n, h, p1, p2 in AMAND_1945["headings"]
        ]
        data[f"{STAMP}_witness_fix"] = fix["reason"]
        data["citation_verdict"] = "corrected"
        set_meta(w.N[fix["node"]], data)
        note("lot5_witness_fix", fix["node"])
    else:
        skip("lot5_witness_fix", f"{fix['node']} absent")

    # the argument that is not in Amand's series
    rs = LOT5_RESCOPE
    if rs["node"] in w.N:
        node = w.N[rs["node"]]
        if node.get("label") == rs["old_label"]:
            node["label"] = rs["new_label"]
            note("lot5_rescope", f"{rs['node']}: relabelled")
        data = meta(node)
        data.update(rs["metadata"])
        data[STAMP] = True
        set_meta(node, data)
        w.drop_edges.add(rs["drop_edge"])
        log.append(f"[edge_drop_lot5] {' -'.join(rs['drop_edge'][:2])}-> "
                   f"{rs['drop_edge'][2]}: not a member of Amand's reconstructed series")
    else:
        skip("lot5_rescope", f"{rs['node']} absent")

    # the argument that straddles two of Amand's heads
    df = LOT5_DEFERRED
    if df["node"] in w.N:
        data = meta(w.N[df["node"]])
        data[df["flag"]] = df["reason"]
        set_meta(w.N[df["node"]], data)
        w.add_edge(df["node"], "same_thesis_as", df["same_thesis_as"], df["reason"], "lot5")


def lot6(w: Wave) -> None:
    for survivor, absorbed_ids, key, title in LOT6_MERGES:
        if survivor not in w.N:
            skip("merge_lot6", f"{survivor} absent")
            continue
        sm = meta(w.N[survivor])
        if pubkey(sm.get("source_file")) != key:
            skip("merge_lot6", f"{survivor}: source_file no longer maps to {key}")
            continue
        for absorbed in absorbed_ids:
            if absorbed not in w.N:
                skip("merge_lot6", f"{absorbed}: absent")
                continue
            am = meta(w.N[absorbed])
            if pubkey(am.get("source_file")) != key:
                skip("merge_lot6", f"{absorbed}: source_file no longer maps to {key}")
                continue
            s_scholar = sm.get("scholar_id") or sm.get("author_id")
            a_scholar = am.get("scholar_id") or am.get("author_id")
            if s_scholar != a_scholar:
                skip("merge_lot6", f"{absorbed}: scholar {a_scholar} != {s_scholar}")
                continue
            if not pages_compatible(sm.get("page_range"), am.get("page_range")):
                skip("merge_lot6",
                     f"{absorbed}: page_range {am.get('page_range')!r} disjoint from "
                     f"{sm.get('page_range')!r}")
                continue
            w.merge(survivor, absorbed,
                    f"{title} — same scholar, same publication ({key}) extracted "
                    f"twice, overlapping page range.", "lot6")

    for source, relation, target, reason in LOT6_EDGE_DROPS:
        w.drop_edges.add((source, relation, target))
        log.append(f"[edge_drop_lot6] {source} -{relation}-> {target}: {reason}")

    for node_id, page_range, why in LOT6_PAGE_RANGE_CONFLICTS:
        if node_id not in w.N or node_id in w.remap:
            continue
        data = meta(w.N[node_id])
        if data.get("page_range") == page_range:
            data["needs_page_verification"] = why
            set_meta(w.N[node_id], data)
            counts["lot6_page_range_flagged"] += 1


def lot6_links(w: Wave) -> None:
    """One same_thesis_as star per cluster, between namespaces only."""
    if not AUDIT_SEMANTIC.exists():
        skip("edge_lot6", "audit file missing")
        return

    def namespace(node_id: str) -> str:
        for prefix in ("scholarly_argument_", "scholar_position_", "argument_",
                       "synthesis_", "concept_"):
            if node_id.startswith(prefix):
                return prefix
        return "other"

    for row in read_jsonl(AUDIT_SEMANTIC):
        if row.get("category") != "same_thesis_cluster":
            continue
        if row.get("verdict") != "same":
            continue
        title = row.get("title") or ""
        if title.startswith(LINK_SKIP_TITLE_PREFIXES):
            continue
        members = [w.resolve(m) for m in row.get("members_present") or []]
        members = sorted({m for m in members if w.alive(m)})
        if len(members) < 2:
            continue
        by_ns: dict[str, str] = {}
        for m in members:
            ns = namespace(m)
            if ns not in by_ns or w.degree[m] > w.degree[by_ns[ns]]:
                by_ns[ns] = m
        reps = sorted(by_ns.values())
        if len(reps) < 2:
            continue
        best = w.resolve(row.get("best_member") or "")
        hub = best if best in reps else max(reps, key=lambda x: (w.degree[x], x))
        for other in reps:
            if other == hub:
                continue
            w.add_edge(hub, "same_thesis_as", other,
                       f"DAS-001 / {title}: same thesis carried in two namespaces "
                       f"at different granularity.", "lot6")


def lot7(w: Wave) -> None:
    cfg = LOT7_EDITORS
    node_id = cfg["node"]
    if node_id not in w.N:
        skip("lot7", f"{node_id} already absent")
        return
    members = [m for m in cfg["members"] if m in w.N]
    if len(members) != len(cfg["members"]):
        skip("lot7", "one of the three scholars is missing; refusing to split")
        return
    data = meta(w.N[node_id])
    if data.get("role") != "editorial_group":
        skip("lot7", f"{node_id}: metadata.role is {data.get('role')!r}")
        return

    incident = [e for e in w.edges if e["target"] == node_id or e["source"] == node_id]
    for edge in incident:
        triple = (edge["source"], edge["relation"], edge["target"])
        if triple[0] == "scholar_frede_michael" and triple[1] == "influences":
            continue  # handled by drop_edges below
        relation = edge["relation"]
        new_relation = relation
        for source, old_rel, new_rel, _reason in cfg["rewire"]:
            if triple[0] == source and relation == old_rel:
                new_relation = new_rel
        for member in members:
            w.add_edge(triple[0], new_relation, member,
                       f"Split of the collective node {node_id} "
                       f"({relation} -> {new_relation}).", "lot7")
        w.drop_edges.add(triple)

    for source, relation, target, reason in cfg["drop_edges"]:
        w.drop_edges.add((source, relation, target))
        log.append(f"[edge_drop_lot7] {source} -{relation}-> {target}: {reason}")

    if cfg["retype_volume_authorship"]:
        volume = "pub_destree_salles_zingano_2014_what_is_up_to_us"
        for edge in w.edges:
            if edge["source"] == volume and edge["relation"] == "authored_by" \
                    and edge["target"] in members:
                edge["relation"] = "edited_by"
                mdata = edge.get("metadata")
                if isinstance(mdata, dict):
                    mdata[STAMP] = True
                    mdata[f"{STAMP}_retype"] = (
                        "edited_volume: the three are the editors, not the authors."
                    )
                counts["lot7_authored_by_to_edited_by"] += 1

    # the node itself: no longer referenced by any edge
    w.nodes = [n for n in w.nodes if nid(n) != node_id]
    del w.N[node_id]
    note("lot7", f"{node_id} split into {members} and removed")


def cosmetic_fixes(w: Wave) -> None:
    """The two rejected-merge nodes whose labels caused the false positive."""
    gill = "scholarly_work_gill_2014_a_free_will_origins_of_the_notion_in_anc"
    if gill in w.N:
        node = w.N[gill]
        data = meta(node)
        new_title = ("Review of M. Frede, A Free Will: Origins of the Notion in "
                     "Ancient Thought (ed. A. A. Long, Sather 68, 2011)")
        if data.get("title") != new_title:
            data[f"{STAMP}_title_before"] = data.get("title")
            data["title"] = new_title
            data[f"{STAMP}_note"] = REJECTED["gill_2014"]
            node["label"] = "Gill 2014 — " + new_title
            node["description"] = (
                "Christopher Gill's review of Michael Frede, A Free Will: Origins "
                "of the Notion in Ancient Thought (ed. A. A. Long, Sather Classical "
                "Lectures 68, University of California Press, 2011), The European "
                "Legacy 19.6 (2014) 797-798."
            )
            set_meta(node, data)
            note("gill_2014", "review re-titled so Gill is no longer shown as the "
                              "author of Frede's book")

    for node_id, volume in (
        ("scholarly_work_bobichon_2003_justin_martyr_dialogue_avec_tryphon_diti", "vol. 1"),
        ("scholarly_work_bobichon_2003_justin_martyr_dialogue_avec_le_tryphon_d", "vol. 2"),
    ):
        if node_id not in w.N:
            continue
        node = w.N[node_id]
        if volume in (node.get("label") or ""):
            continue
        node["label"] = (
            f"Bobichon 2003 — Justin Martyr, Dialogue avec Tryphon, "
            f"édition critique, {volume} (Paradosis 47/{volume[-1]})"
        )
        data = meta(node)
        data[f"{STAMP}_note"] = REJECTED["bobichon_2003"]
        set_meta(node, data)
        note("bobichon_2003", f"{node_id}: label disambiguated ({volume})")


# ---------------------------------------------------------------------- main
def check_invariants(nodes: list[dict], edges: list[dict]) -> None:
    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    present = set(ids)
    dangling = [e for e in edges
                if e["source"] not in present or e["target"] not in present]
    assert not dangling, f"dangling edges: {dangling[:3]}"
    assert not [e for e in edges
                if e["source"] != e["source_id"] or e["target"] != e["target_id"]], \
        "source/source_id or target/target_id disagree"
    triples = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triples) == len(set(triples)), "duplicate (source, relation, target)"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", dest="dry_run", action="store_false",
                        help="actually write (default is --dry-run)")
    args = parser.parse_args()

    w = Wave()

    lot0_ontology(w)
    lot1_destree(w)
    lot2_boethius(w)
    lot3(w)
    lot4(w)
    lot5(w)
    lot6(w)
    lot7(w)
    lot6_links(w)
    cosmetic_fixes(w)

    # everything that touches edges happens once, here
    w.rewrite_edges()
    absorbed = set(w.remap)
    w.nodes = [n for n in w.nodes if nid(n) not in absorbed]
    w.N = {nid(n): n for n in w.nodes}
    w.remap_metadata()
    citations = w.remap_citations()

    check_invariants(w.nodes, w.edges)

    print(f"nodes {w.before[0]} -> {len(w.nodes)}   "
          f"edges {w.before[1]} -> {len(w.edges)}")
    print(f"merged away: {len(absorbed)} nodes")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    if w.deferred_edges:
        print(f"\n{len(w.deferred_edges)} edges NOT written (ontology types after merge):")
        for line in w.deferred_edges[:20]:
            print(f"  {line}")
    print("invariants: OK")

    if args.dry_run:
        print("\n--dry-run: nothing written (use --apply to write)")
        return 0

    for path in (NODES_PATH, EDGES_PATH, CITATIONS_PATH):
        if path.exists():
            path.with_suffix(path.suffix + BACKUP_SUFFIX).write_bytes(path.read_bytes())
    ONTOLOGY_PATH.with_suffix(ONTOLOGY_PATH.suffix + BACKUP_SUFFIX).write_bytes(
        ONTOLOGY_PATH.read_bytes())

    write_jsonl(NODES_PATH, w.nodes)
    write_jsonl(EDGES_PATH, w.edges)
    if citations is not None:
        write_jsonl(CITATIONS_PATH, citations)
    with ONTOLOGY_PATH.open("w", encoding="utf-8") as fh:
        json.dump(w.ontology, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    REPORT_PATH.write_text(
        "# Semantic merges — applied 2026-08-17\n\n"
        f"nodes {w.before[0]} -> {len(w.nodes)}, edges {w.before[1]} -> {len(w.edges)}\n"
        f"absorbed nodes: {len(absorbed)}\n\n"
        "## Counts\n\n"
        + "\n".join(f"- {k}: {v}" for k, v in sorted(counts.items()))
        + "\n\n## Edges deferred (ontology types)\n\n"
        + ("\n".join(f"- {line}" for line in w.deferred_edges) or "- none")
        + "\n\n## Log\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {ONTOLOGY_PATH}\n"
          f"wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
