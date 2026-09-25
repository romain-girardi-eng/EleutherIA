#!/usr/bin/env python3
"""Put the right chapter of Volkmann's Enneads back on the drifted Plotinus nodes. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_plotinus_locus_drift.py --tei PATH --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_plotinus_locus_drift.py --tei PATH --apply

PATH is ``data/tlg2000/tlg001/tlg2000.tlg001.1st1K-grc1.xml`` from a checkout of
OpenGreekAndLatin/First1KGreek (commit pinned in the data module; the file hash
is checked).

The 646 ``passage_plotinus_<ennead>_<treatise>_<chapter>`` nodes and the corpus
rows they cite carry Volkmann's text cut into consecutive slices that slid
further away from the locus they are labelled with (the text stored under
Enn. VI.8.1 is Enn. IV.4.26).  For every item the script:

* re-locates the stored text in the TEI and refuses to act if the result differs
  from the recorded evidence, or if the node and its corpus twin disagree;
* when the TEI chapter matching the node's own locus is free of ``<gap>``,
  replaces the text on both sides with that chapter, verbatim (``<del>`` is
  printed in square brackets, as in the Teubner; page breaks are dropped),
  and moves the URN to the First1KGreek edition;
* when the chapter is missing from Volkmann's division or contains a ``<gap>``,
  leaves the text alone and blocks the node from citation, recording where
  its text really comes from.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET

from scripts.data_2026_09_24_plotinus_locus_drift import ITEMS, REPOINT, TEI_COMMIT, TEI_SHA256
from scripts.verification_2026_09_24_lib import Store, meta, set_meta, write_decisions

SLUG = "plotinus_locus_drift"
STAMP = "plotinus_locus_repair_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
NS = "{http://www.tei-c.org/ns/1.0}"
OLD_URN = "urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:"
NEW_URN = "urn:cts:greekLit:tlg2000.tlg001.1st1K-grc1:"
EDITION = (
    "R. Volkmann, Plotini Enneades, Leipzig: Teubner, 1883-1884; TEI "
    "tlg2000.tlg001.1st1K-grc1 (OpenGreekAndLatin/First1KGreek, commit " + TEI_COMMIT + ")"
)
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def letters(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    # Lm is left out: the modifier apostrophe (U+02BC) is punctuation here.
    return "".join(c for c in text if unicodedata.category(c) in ("Lu", "Ll", "Lo")).lower()


def render(elem: ET.Element) -> str:
    """Text of a TEI element; <del> in brackets, <pb> dropped, tails kept."""
    out = [elem.text or ""]
    for child in elem:
        tag = child.tag.replace(NS, "")
        if tag == "del":
            out.append("[" + render(child) + "]")
        elif tag in ("pb", "lb"):
            pass
        elif tag in ("q", "hi", "add"):
            out.append(render(child))
        else:
            raise ValueError(f"unexpected TEI element <{tag}>")
        out.append(child.tail or "")
    return "".join(out)


def chapter_text(chap: ET.Element) -> str:
    """The chapter's paragraphs, whitespace squeezed, separated by a blank line."""
    return "\n\n".join(re.sub(r"\s+", " ", render(p)).strip() for p in chap.iter(NS + "p"))


def load_tei(path: str):
    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != TEI_SHA256:
        raise SystemExit(f"TEI hash {digest} differs from the pinned {TEI_SHA256}")
    root = ET.fromstring(raw)
    chapters, order = {}, []
    for book in root.iter(NS + "div"):
        if book.get("subtype") != "book":
            continue
        for treatise in book.findall(NS + "div"):
            for chap in treatise.findall(NS + "div"):
                ref = f"{book.get('n')}.{treatise.get('n')}.{chap.get('n')}"
                tags = {e.tag.replace(NS, "") for e in chap.iter()}
                chapters[ref] = (chap, tags)
                order.append(ref)
    return chapters, order


def repoint(store, nodes, locate, decisions, skipped) -> None:
    """Move the III.2.10 quotation and its citers off the drifted IV.4.30 row."""
    r = REPOINT
    syn = nodes.get(r["synthesis_node"])
    if syn is None or syn.get("label") != r["wrong_label"]:
        skipped.append((r["synthesis_node"], "synthesis already repointed or changed"))
        return
    sm = meta(syn)
    quote = sm.get("greek_verified") or ""
    where = {locate(letters(part)) for part in quote.split("...") if part.strip()}
    assert where == {r["true_locus"]}, f"quotation located at {where}"
    def snapshot_row(nid):
        rows = [c["passage_id"] for c in store.rows["citations"]
                if c["kg_node_id"] == nid and c["citation_type"] == "snapshot_passage_node"]
        assert len(rows) == 1, (nid, rows)
        return rows[0]
    old_row, new_row = snapshot_row(r["drifted_node"]), snapshot_row(r["true_node"])
    moved = []
    existing = {(c["kg_node_id"], c["citation_type"], c["passage_id"]) for c in store.rows["citations"]}
    for c in store.rows["citations"]:
        if c["passage_id"] == old_row and c["kg_node_id"] not in (r["drifted_node"], r["synthesis_node"]):
            assert (c["kg_node_id"], c["citation_type"], new_row) not in existing, c
            moved.append(f"{c['kg_node_id']} ({c['citation_type']})")
            c["passage_id"] = new_row
    # The English synthesis is not a snapshot twin of any Greek row (the
    # snapshot-integrity baseline already lists it as editorial/non-bijective);
    # its link to the primary is primary_node_id.
    store.remove_citations(
        lambda c: c["kg_node_id"] == r["synthesis_node"] and c["passage_id"] == old_row
        and c["citation_type"] == "snapshot_passage_node",
        "English editorial synthesis cited as snapshot twin of a Greek row; link kept as primary_node_id",
    )
    stamp = {"previous_label": syn["label"], "previous_canonical_ref": sm.get("canonical_ref"),
             "previous_primary_node_id": sm.get("primary_node_id"),
             "previous_synthesis_of_urn": sm.get("synthesis_of_urn"),
             "previous_corpus_passage_id": old_row}
    b, t, ch = (int(x) for x in r["true_locus"].split("."))
    syn["label"] = r["right_label"]
    sm["canonical_ref"] = f"Enn. {ROMAN[b]}.{t}.{ch}"
    sm["primary_node_id"] = r["true_node"]
    sm["synthesis_of_urn"] = NEW_URN + r["true_locus"]
    if sm.get("passage_id") == old_row:
        stamp["previous_passage_id"] = sm.pop("passage_id")
    sm.pop("quote_coverage_of_primary", None)
    sm[STAMP] = stamp
    set_meta(syn, sm)
    syn["updated_at"] = NOW
    decisions.append({
        "item_id": r["synthesis_node"],
        "queue": "found while repairing the Plotinus locus drift",
        "claim_checked": "The quotation on this English synthesis is Enn. IV.4.30.",
        "verdict": "corrected",
        "evidence": {"quotation_located_at": r["true_locus"]},
        "source": EDITION,
        "method": "letter-sequence location of both halves of metadata.greek_verified in the TEI",
        "jev": None,
        "change": (f"label and canonical_ref to {sm['canonical_ref']}; primary_node_id to {r['true_node']}; "
                   f"corpus citations moved from row {old_row} to row {new_row}: " + ", ".join(moved)
                   + "; the synthesis' own snapshot citation to the Greek row withdrawn (quarantine)"),
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tei", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    chapters, order = load_tei(args.tei)
    stream, offsets, pos = [], [], 0
    for ref in order:
        chap_letters = letters("".join(chapters[ref][0].itertext()))
        offsets.append((pos, ref))
        stream.append(chap_letters)
        pos += len(chap_letters)
    full = "".join(stream)

    def locate(probe: str):
        i = full.find(probe) if probe else -1
        return [r for (o, r) in offsets if o <= i][-1] if i >= 0 else None

    def span(text: str):
        n = letters(text)
        return locate(n[:40]), locate(n[-40:])

    store = Store()
    nodes = store.nodes
    passages = {p["passage_id"]: p for p in store.rows["passages"]}
    cited = collections.defaultdict(list)
    passage_citers = collections.defaultdict(set)
    for c in store.rows["citations"]:
        cited[c["kg_node_id"]].append(c["passage_id"])
        if nodes.get(c["kg_node_id"], {}).get("type") == "passage":
            passage_citers[c["passage_id"]].add(c["kg_node_id"])

    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()
    repoint(store, nodes, locate, decisions, skipped)
    passage_citers.clear()
    for c in store.rows["citations"]:
        if c["kg_node_id"] != REPOINT["synthesis_node"] and nodes.get(c["kg_node_id"], {}).get("type") == "passage":
            passage_citers[c["passage_id"]].add(c["kg_node_id"])
    for node_id, claimed, was_start, was_end in ITEMS:
        node = nodes.get(node_id)
        if node is None:
            skipped.append((node_id, "node absent"))
            continue
        m = meta(node)
        if m.get(STAMP):
            skipped.append((node_id, "already stamped"))
            continue
        if m.get("cts_urn") != OLD_URN + claimed:
            skipped.append((node_id, f"cts_urn is {m.get('cts_urn')}"))
            continue
        twins = cited.get(node_id, [])
        # Argument or school nodes may cite the same corpus row (they cite the
        # locus); no other passage node may.
        if len(twins) != 1 or twins[0] not in passages or passage_citers[twins[0]] != {node_id}:
            skipped.append((node_id, f"expected one corpus twin, no other passage node on it; got {twins}"))
            continue
        twin = passages[twins[0]]
        old_text = node.get("description") or ""
        if letters(twin.get("text_content")) != letters(old_text) or twin.get("cts_urn") != m.get("cts_urn"):
            skipped.append((node_id, "node and corpus twin disagree"))
            continue
        where = span(old_text)
        if where != (was_start, was_end):
            skipped.append((node_id, f"stored text now located at {where}, recorded {(was_start, was_end)}"))
            continue

        b, t, c = (int(x) for x in claimed.split("."))
        locus = f"Enn. {ROMAN[b]}.{t}.{c}"
        record = {
            "item_id": node_id,
            "queue": "c3_edges_links/queue_A_likely_wrong.csv (rows on passage_plotinus_iii_1_7/8), extended to the whole series",
            "claim_checked": f"The Greek stored on {node_id} (and on corpus passage {twin['passage_id']}) is {locus}.",
            "evidence": {"stored_text_starts_in": was_start, "stored_text_ends_in": was_end,
                         "stored_text_sha256": hashlib.sha256(old_text.encode()).hexdigest()},
            "source": EDITION,
            "method": "letter-sequence location of the first and last 40 letters of the stored text in the TEI; chapter comparison",
            "jev": None,
        }
        chapter = chapters.get(claimed)
        stamp = {
            "previous_cts_urn": m.get("cts_urn"),
            "previous_text_located_at": [was_start, was_end],
            "previous_text_sha256": record["evidence"]["stored_text_sha256"],
        }
        for key in ("text_integrity", "source"):
            if key in m:
                stamp[f"previous_{key}"] = m.pop(key)

        clean = chapter is not None and "gap" not in chapter[1]
        if clean and letters(old_text) == letters(chapter_text(chapter[0])):
            record.update(verdict="confirmed_correct", change="none")
            counts["confirmed_correct"] += 1
            decisions.append(record)
            continue

        if chapter is None or "gap" in chapter[1]:
            why = "Volkmann has no such chapter" if chapter is None else "the TEI chapter contains an unrendered <gap>"
            stamp["action"] = "citation_blocked"
            stamp["reason"] = f"stored text is not {locus} (it runs from Volkmann {was_start} to {was_end}); {why}"
            m["citation_blocked"] = True
            m["needs_reference_remapping"] = stamp["reason"]
            m[STAMP] = stamp
            set_meta(node, m)
            node["updated_at"] = NOW
            record.update(verdict="needs_romain",
                          change=f"blocked from citation ({why}); re-ingestion of {locus} from a complete edition needed")
            counts["blocked"] += 1
            decisions.append(record)
            continue

        new_text = chapter_text(chapter[0])
        # Nothing outside the <p> elements may be lost.
        assert letters(new_text) == letters("".join(chapter[0].itertext())), node_id
        stamp["action"] = "text_replaced_from_tei"
        m["cts_urn"] = NEW_URN + claimed
        m["edition"] = EDITION
        m["word_count"] = len(new_text.split())
        m["char_length"] = len(new_text)
        m[STAMP] = stamp
        set_meta(node, m)
        node["description"] = new_text
        node["updated_at"] = NOW
        twin["text_content"] = new_text
        twin["cts_urn"] = NEW_URN + claimed
        record.update(verdict="corrected",
                      change=f"text replaced on node and corpus twin by Volkmann {locus} verbatim; URN {NEW_URN + claimed}")
        counts["corrected"] += 1
        decisions.append(record)

    # The quotation must now sit in the text of its primary.
    syn, prim = nodes[REPOINT["synthesis_node"]], nodes[REPOINT["true_node"]]
    for part in (meta(syn).get("greek_verified") or "").split("..."):
        assert letters(part) in letters(prim["description"]), part

    summary = store.commit(SLUG, apply=apply)
    if apply:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts,
                      "skipped": skipped[:10], "n_skipped": len(skipped), "changes": summary},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
