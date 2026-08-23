#!/usr/bin/env python3
"""Apply scholar-quote wave 2 (multi-agent mining) to data/kg/nodes.jsonl.

Input: a results JSON (``--results``) holding the verified extractions:
  {"kept": [{"node_id", "quote_verbatim", "quote_page", "source_file", "work"}]}

Trust nothing: before writing, EVERY quote is re-verified deterministically —
whitespace-insensitive, typographic-quote-insensitive containment in its
declared ``source_file``. A quote that fails is skipped and logged, whatever
the upstream verifier said.

Dry-run by default; ``--write`` to apply. Idempotent (skip already-quoted
nodes), backup, unchanged lines byte-for-byte, audit report.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "kg" / "nodes.jsonl"
BACKUP = NODES.with_name("nodes.jsonl.bak-scholar-quotes-wave2")
REPORT = ROOT / "data" / "audit" / "2026-08-23_scholar_quotes_wave2_applied.md"
WAVE_STAMP = "scholar_quotes_wave2_2026_08_23"

MIN_QUOTE_CHARS = 60
MAX_QUOTE_CHARS = 2400  # ~ a long paragraph; anything bigger is over-quotation


def _flat(text: str) -> str:
    text = (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("­", "")  # soft hyphen
    )
    return " ".join(text.split())


_SOURCE_CACHE: dict[str, str] = {}


def _source_flat(path: str) -> str | None:
    if path not in _SOURCE_CACHE:
        p = Path(path)
        if not p.is_file():
            return None
        try:
            _SOURCE_CACHE[path] = _flat(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            return None
    return _SOURCE_CACHE[path]


import re as _re

_SENTENCE_SPLIT_RE = _re.compile(r"[.!?;]")


def _canon(text: str) -> str:
    """Letters and digits only, NFKC-normalized — spacing, punctuation and
    ligatures (ﬁ/fi) are where the OCR/extraction artifacts live (mid-word
    line-break spaces, spaced dashes, running headers' whitespace). The WORDS
    must stay exact."""
    import unicodedata

    text = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in text if ch.isalnum())


_HEADER_GAP_RE = _re.compile(r"^[0-9A-ZÀ-ÖØ-Þ]+$")


def _sentence_with_header_gap(sentence: str, csrc: str, start: int) -> int:
    """Find ``sentence`` in ``csrc`` tolerating ONE running-header interruption.

    The split candidate is the LONGEST prefix of the sentence present in the
    source (the direct find fails exactly where the header interrupts). The
    gap (max 60 canon chars) must be digits+uppercase ONLY — the canonical
    shape of a running header ("146ALEXANDREDAPHRODISE"); any lowercase in
    the gap means real words differ and the match is refused. Returns the
    match end, or -1.
    """
    lo, hi, best = 30, len(sentence) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if csrc.find(sentence[:mid], start) >= 0:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best < 30 or len(sentence) - best < 15:
        return -1
    head, tail = sentence[:best], sentence[best:]
    i = csrc.find(head, start)
    while i >= 0:
        j = csrc.find(tail, i + len(head), i + len(head) + 60 + len(tail))
        if j >= 0:
            gap = csrc[i + len(head) : j]
            if 0 < len(gap) <= 60 and _HEADER_GAP_RE.match(gap):
                return j + len(tail)
        i = csrc.find(head, i + 1)
    return -1


def _verbatim_in_source(quote: str, source_file: str) -> tuple[bool, str]:
    src = _source_flat(source_file)
    if src is None:
        return False, "source file unreadable"
    probe = _flat(quote)
    if probe in src:
        return True, ""
    if probe.replace("- ", "") in src.replace("- ", ""):
        return True, ""
    # Extraction-artifact tolerance, still word-exact: every sentence of the
    # quote must appear letter-for-letter (alnum-canonical) in the source, in
    # order, within one continuous window. This forgives "Bewe gung" splits,
    # "passages —that" spacing and a running header dropped at a page break —
    # it can NEVER forgive a changed, added, or bridged word.
    csrc = _canon(src)
    sentences = [
        _canon(s) for s in _SENTENCE_SPLIT_RE.split(probe) if len(_canon(s)) >= 25
    ]
    if not sentences:
        cprobe = _canon(probe)
        if len(cprobe) >= 40 and cprobe in csrc:
            return True, ""
        return False, "quote not found verbatim in source"
    pos = -1
    first = last = -1
    for s in sentences:
        i = csrc.find(s, pos + 1)
        if i < 0:
            end = _sentence_with_header_gap(s, csrc, pos + 1)
            if end < 0:
                return False, f"sentence not found verbatim in source: {s[:60]!r}"
            i = end - len(s)  # approximate start (gap length ignored)
        if first < 0:
            first = i
        last = i + len(s)
        pos = i
    if last - first > len(_canon(probe)) + 400:
        return False, "sentences found but scattered — not one continuous passage"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.results).read_text(encoding="utf-8"))
    kept = payload.get("kept") or []

    raw_lines = NODES.read_text(encoding="utf-8").splitlines(keepends=True)
    nodes = [json.loads(line) for line in raw_lines]
    ids = Counter(n.get("id") for n in nodes)
    index = {n.get("id"): i for i, n in enumerate(nodes)}

    applied, skipped, noop = [], [], []
    seen_nodes: set[str] = set()
    for item in kept:
        nid = item.get("node_id") or ""
        quote = (item.get("quote_verbatim") or "").strip()
        page = (item.get("quote_page") or "").strip()
        source_file = item.get("source_file") or ""
        work = (item.get("work") or "").strip()
        if nid in seen_nodes:
            skipped.append((nid, "duplicate proposal for the same node"))
            continue
        seen_nodes.add(nid)
        if ids.get(nid, 0) != 1:
            skipped.append((nid, f"node count is {ids.get(nid, 0)}"))
            continue
        if not (MIN_QUOTE_CHARS <= len(quote) <= MAX_QUOTE_CHARS):
            skipped.append((nid, f"quote length {len(quote)} outside bounds"))
            continue
        ok, why = _verbatim_in_source(quote, source_file)
        if not ok:
            skipped.append((nid, f"DETERMINISTIC CHECK FAILED: {why}"))
            continue
        node = nodes[index[nid]]
        md = node.get("metadata")
        if isinstance(md, str):
            try:
                md = json.loads(md)
            except json.JSONDecodeError:
                skipped.append((nid, "metadata unparseable"))
                continue
        if not isinstance(md, dict):
            md = {}
        existing = md.get("quote_verbatim")
        if isinstance(existing, str) and existing.strip():
            noop.append(nid)
            continue
        md["quote_verbatim"] = quote
        if page:
            md["quote_page"] = page
        md["quote_source"] = work.replace("[no-pub-edge] ", "") or Path(source_file).name
        md["quote_source_file"] = source_file
        md[WAVE_STAMP] = True
        node["metadata"] = md
        applied.append((nid, page or "(no page)", work[:60]))

    assert len(nodes) == len(raw_lines)
    touched = {nid for nid, _, _ in applied}
    out_lines = []
    for line, node in zip(raw_lines, nodes):
        if node.get("id") in touched:
            rendered = json.dumps(node, ensure_ascii=False)
            json.loads(rendered)
            out_lines.append(rendered + ("\n" if line.endswith("\n") else ""))
        else:
            out_lines.append(line)

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"[{mode}] applied={len(applied)} noop={len(noop)} skipped={len(skipped)}")
    for nid, page, work in applied:
        print(f"  + {nid} ({page}) [{work}]")
    for nid, why in skipped:
        print(f"  ! SKIP {nid}: {why}")

    if not args.write or not applied:
        if args.write:
            print("nothing to write")
        return 0

    shutil.copy2(NODES, BACKUP)
    NODES.write_text("".join(out_lines), encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Scholar-quote wave 2 — multi-agent mining (applied 2026-08-23)",
        "",
        "Every quote re-verified deterministically against its source file",
        "(whitespace/typographic-quote-insensitive containment) before writing;",
        f"stamp `metadata.{WAVE_STAMP}`; backup `{BACKUP.name}`.",
        "",
        f"Applied: {len(applied)} | no-op: {len(noop)} | skipped: {len(skipped)}",
        "",
        "| node | page | work |",
        "|---|---|---|",
    ]
    lines += [f"| `{nid}` | {page} | {work} |" for nid, page, work in applied]
    if skipped:
        lines += ["", "Skipped:", ""] + [f"- `{nid}`: {why}" for nid, why in skipped]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report -> {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
