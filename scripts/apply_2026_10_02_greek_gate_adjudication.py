#!/usr/bin/env python3
"""Apply the adjudication of the 56 Greek runs failing check_greek_gate --all. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_10_02_greek_gate_adjudication.py --tei-root DIR --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_10_02_greek_gate_adjudication.py --tei-root DIR --apply

DIR holds checkouts of OpenGreekAndLatin/canonical-greekLit and
OpenGreekAndLatin/First1KGreek (paths in the data module).

For every decision the run is re-derived from the node with the gate's own
functions and must still hash to the recorded value. For ``verified``,
``composite``, ``ocr_damaged`` and the ``scholar_greek`` items that name a
TEI file, the letters are searched again in that TEI (accents, case, spaces
and punctuation ignored); the script refuses to write if any check fails.
Then:

* ``verified`` / ``composite`` / ``ocr_damaged`` / ``scholar_greek`` get an
  entry in data/audit/greek_allowlist.json (hash, excerpt, source), the
  category being stated in the source;
* ``ocr_damaged`` nodes also get an English note in
  metadata.quote_greek_note (no Greek is added to any node);
* ``needs_romain`` is only recorded in the decisions file.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_greek_gate as gate  # noqa: E402

from scripts.data_2026_10_02_greek_gate_adjudication import DECISIONS  # noqa: E402
from scripts.verification_2026_09_24_lib import DATA, Store, meta, set_meta  # noqa: E402

SLUG = "greek_gate_adjudication"
DATE = "2026-10-02"
NOW = "2026-10-02 00:00:00+00:00"
ALLOWLIST = DATA / "audit" / "greek_allowlist.json"
TEI_NS = "{http://www.tei-c.org/ns/1.0}"
LABEL = {
    "verified": "VERIFIED against the edition",
    "composite": "VERIFIED, composite run",
    "ocr_damaged": "OCR-DAMAGED copy of a verified passage, not certified as Greek text",
    "scholar_greek": "SCHOLAR'S OWN GREEK, not an ancient quotation",
}


def letters(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in text if unicodedata.category(c) in ("Lu", "Ll", "Lo")).lower().replace("ς", "σ")


_cache: dict[Path, str] = {}


def tei_letters(path: Path) -> str:
    if path not in _cache:
        root = ET.parse(path).getroot()
        body = root.find(f".//{TEI_NS}text")
        out = []

        def walk(el):
            if el.tag.replace(TEI_NS, "") in ("note", "bibl", "teiHeader"):
                return
            out.append(el.text or "")
            for ch in el:
                walk(ch)
                out.append(ch.tail or "")

        walk(body if body is not None else root)
        _cache[path] = letters("".join(out))
    return _cache[path]


def found(fragments: list[str], path: Path) -> bool:
    """All fragments, in order, within 600 letters of each other."""
    s = tei_letters(path)
    parts = [letters(f) for f in fragments if len(letters(f)) >= 3]
    i = s.find(parts[0])
    while i >= 0:
        j, ok = i + len(parts[0]), True
        for p in parts[1:]:
            k = s.find(p, j)
            if k < 0 or k - j > 600:
                ok = False
                break
            j = k + len(p)
        if ok:
            return True
        i = s.find(parts[0], i + 1)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tei-root", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run
    tei_root = Path(args.tei_root)

    store = Store()
    nodes = store.nodes
    allow = json.loads(ALLOWLIST.read_text())
    entries = allow["allow"]
    blob = " ␟ ".join(
        gate.strip(json.loads(l).get("text_content") or "")
        for l in (DATA / "corpus" / "passages.jsonl").open() if l.strip())

    decisions, problems = [], []
    counts: collections.Counter = collections.Counter()
    for nid, h, cat, tei, checks, source in DECISIONS:
        node = nodes.get(nid)
        runs = {gate.run_hash(r): r for r in gate.extract_runs(gate.node_text(node))} if node else {}
        run = runs.get(h)
        already = any(e.get("hash") == h for e in entries.get(nid, []))
        if run is None and not already:
            problems.append((nid, h, "run no longer present on the node"))
            continue
        if run is not None and gate.strip(run) in blob:
            problems.append((nid, h, "run now attested in the corpus; no entry needed"))
            continue
        if tei and run is not None:
            frags = checks or re.split(r"\.\s*\.\s*\.|…", run)
            if not found(frags, tei_root / tei):
                problems.append((nid, h, f"letters not found in {tei}"))
                continue
        record = {"item_id": f"{nid}#{h}", "queue": "check_greek_gate --all (56 runs outside the baseline)",
                  "claim_checked": "The Greek run is verbatim from a named edition, or is declared for what it is.",
                  "evidence": source, "source": tei or "not reachable here",
                  "method": "letter-level search in the TEI of the edition (accents, case, spaces, punctuation ignored)",
                  "jev": None, "category": cat}
        if cat == "needs_romain":
            record.update(verdict="needs_romain", change="none; the run keeps failing --all until checked")
        else:
            if not already:
                entries.setdefault(nid, []).append({
                    "hash": h, "excerpt": run[:80],
                    "source": f"{LABEL[cat]}: {source} (adjudicated {DATE}; TEI {tei or 'n/a'})"})
            change = "allowlist entry added" if not already else "allowlist entry already present"
            if cat == "ocr_damaged":
                m = meta(node)
                note = m.get("quote_greek_note") or ""
                if source not in note:
                    m["quote_greek_note"] = (note + " " if note else "") + source
                    set_meta(node, m)
                    node["updated_at"] = NOW
                    change += "; English note in metadata.quote_greek_note"
            record.update(verdict="confirmed_correct" if cat in ("verified", "composite") else "corrected", change=change)
        counts[cat] += 1
        decisions.append(record)

    if problems:
        print(json.dumps({"refused": problems}, ensure_ascii=False, indent=1))
        sys.exit(1)
    summary = store.commit(SLUG, apply=apply)
    if apply:
        ALLOWLIST.write_text(json.dumps(allow, ensure_ascii=False, indent=1) + "\n")
        with (DATA / "audit" / f"{DATE}_{SLUG}_decisions.jsonl").open("w") as fh:
            for d in decisions:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "changes": summary},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
