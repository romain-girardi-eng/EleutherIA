#!/usr/bin/env python3
"""Derive golden eval fixtures from the scholarly-audit corpus.

Reads the READ-ONLY audit queues under ``data/audit/`` and emits
machine-derived fixtures under ``data/eval/``:

- ``citation_gold.jsonl``       — (node, wrong-passage, right-passage) records
  from the citation-fix waves; the citation P/R scorer and future annotated
  queries consume these.
- ``must_not_appear.jsonl``     — fabricated/unverifiable ancient-Greek strings
  removed (status ``fixed``) or pending removal (status ``deferred``) by the
  Greek-integrity waves. These strings must never reappear in KG exports or
  generated answers.
- ``quote_gate_strings.json``   — verbatim ancient strings (genuine + audited
  fabrications) used by ``tests/eval/test_quote_gate_eval.py`` to exercise the
  programmatic quote gate. No ancient text is ever composed here: every string
  is copied verbatim from an audit record and traces back to its source line.

Usage:
    python scripts/eval/build_gold_from_audit.py            # (re)generate
    python scripts/eval/build_gold_from_audit.py --check    # CI drift gate
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "data" / "audit"
EVAL_DIR = REPO_ROOT / "data" / "eval"

GREEK_CHAR_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
# A run = Greek words joined by spaces/apostrophes/inline punctuation,
# anchored on Greek characters at both ends so surrounding Latin prose,
# parentheses and quotes are never captured.
GREEK_RUN_RE = re.compile(
    r"[Ͱ-Ͽἀ-῿]"
    r"[Ͱ-Ͽἀ-῿̀-ͯʼ'’᾽ ,·;.\-]*"
    r"[Ͱ-Ͽἀ-῿]"
)
QUOTED_SPAN_RE = re.compile(r'"([^"]+)"')


def _greek_word_count(run: str) -> int:
    return sum(1 for token in run.split() if GREEK_CHAR_RE.search(token))


def _greek_runs(text: str, min_words: int) -> list[str]:
    runs = [run.strip(" ,·;.-") for run in GREEK_RUN_RE.findall(text or "")]
    return [run for run in runs if _greek_word_count(run) >= min_words]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ---------------------------------------------------------------------------
# citation_gold.jsonl
# ---------------------------------------------------------------------------


def build_citation_gold() -> list[dict[str, Any]]:
    """Passage-level citation corrections from the cite-fix wave.

    ``applied`` records come from the changelog (fixes already deployed);
    ``deferred`` records come from the low-confidence queue (not yet applied,
    still useful as adversarial wrong-passage fixtures).
    """
    entries: list[dict[str, Any]] = []

    changelog = "cite_fix_changelog.jsonl"
    for line_no, rec in enumerate(_read_jsonl(AUDIT_DIR / changelog), start=1):
        entries.append(
            {
                "id": f"cg{len(entries) + 1:03d}",
                "node_id": rec["kg_node_id"],
                "op": rec["op"],
                "wrong_passage_id": rec.get("passage_id") or rec.get("old_passage_id"),
                "right_passage_id": rec.get("new_passage_id"),
                "status": "applied",
                "confidence": None,
                "rationale": None,
                "source_file": f"data/audit/{changelog}",
                "source_line": line_no,
            }
        )

    deferred = "cite_fix_deferred.jsonl"
    for line_no, rec in enumerate(_read_jsonl(AUDIT_DIR / deferred), start=1):
        new_passage = rec.get("new_passage_id")
        if new_passage in (None, "", "None"):
            new_passage = None
        entries.append(
            {
                "id": f"cg{len(entries) + 1:03d}",
                "node_id": rec["node_id"],
                "op": rec["action"],
                "wrong_passage_id": rec["bad_passage_id"],
                "right_passage_id": new_passage,
                "status": "deferred",
                "confidence": float(rec["confidence"])
                if rec.get("confidence")
                else None,
                "rationale": rec.get("rationale"),
                "source_file": f"data/audit/{deferred}",
                "source_line": line_no,
            }
        )

    return entries


# ---------------------------------------------------------------------------
# must_not_appear.jsonl
# ---------------------------------------------------------------------------

MIN_FORBIDDEN_WORDS = 3  # shorter runs are common vocabulary, not fingerprints


def _kg_occurrences(strings: list[str]) -> dict[str, list[dict[str, str]]]:
    """Where each string still occurs in the committed KG export.

    A string attested in a ``passage``-type node is genuine corpus text that
    was merely removed from a description for citation reasons — it must not
    be treated as a fabrication fingerprint in answer scans.
    """
    occurrences: dict[str, list[dict[str, str]]] = {s: [] for s in strings}
    nodes_path = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
    if not nodes_path.exists():
        return occurrences
    with nodes_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not any(s in line for s in strings):
                continue
            node = json.loads(line)
            blob = json.dumps(node, ensure_ascii=False)
            for s in strings:
                if s in blob:
                    occurrences[s].append(
                        {
                            "node_id": str(node.get("id")),
                            "node_type": str(node.get("type")),
                        }
                    )
    return occurrences


def build_must_not_appear() -> list[dict[str, Any]]:
    """Greek strings the audit removed (or confirmed for removal) as
    fabricated/unverifiable. A run qualifies when it appears in the old text
    but not in the corrected text, and is long enough (>= 3 Greek words) to
    be a fingerprint rather than ordinary vocabulary.

    Each entry carries two derived scan flags:

    - ``scan_kg``      — fix applied and string fully absent from the KG
      export at build time; reappearance anywhere is a regression.
    - ``scan_answers`` — string is not attested in any passage-type node, so
      a generated answer containing it cannot be quoting genuine corpus text.
    """
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        string: str,
        node_id: str,
        status: str,
        severity: str | None,
        source_file: str,
        source_line: int,
    ) -> None:
        if string in seen:
            return
        seen.add(string)
        entries.append(
            {
                "string": string,
                "node_id": node_id,
                "language": "grc",
                "status": status,
                "severity": severity,
                "source_file": source_file,
                "source_line": source_line,
            }
        )

    changelog = "wave1_greek_changelog.jsonl"
    for line_no, rec in enumerate(_read_jsonl(AUDIT_DIR / changelog), start=1):
        new_text = rec.get("new") or ""
        for run in _greek_runs(rec.get("old") or "", MIN_FORBIDDEN_WORDS):
            if run not in new_text:
                add(
                    run,
                    rec["node_id"],
                    "fixed",
                    rec.get("severity"),
                    f"data/audit/{changelog}",
                    line_no,
                )

    deferred = "greek_insertions_deferred.jsonl"
    for line_no, rec in enumerate(_read_jsonl(AUDIT_DIR / deferred), start=1):
        proposed = rec.get("proposed") or ""
        for run in _greek_runs(rec.get("current") or "", MIN_FORBIDDEN_WORDS):
            if run not in proposed:
                add(
                    run,
                    rec["node_id"],
                    "deferred",
                    rec.get("severity"),
                    f"data/audit/{deferred}",
                    line_no,
                )

    occurrences = _kg_occurrences([entry["string"] for entry in entries])
    for entry in entries:
        occ = occurrences[entry["string"]]
        entry["kg_occurrences"] = occ
        entry["scan_kg"] = entry["status"] == "fixed" and not occ
        entry["scan_answers"] = not any(o["node_type"] == "passage" for o in occ)

    return entries


# ---------------------------------------------------------------------------
# quote_gate_strings.json
# ---------------------------------------------------------------------------


def build_quote_gate_strings(
    must_not_appear: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verbatim ancient strings for the quote-gate adversarial suite.

    Genuine strings come from the corrected (``new``) side of the citation
    desc-fix changelog — audit-verified text. Fabricated Greek comes straight
    from the must-not-appear set.
    """
    descfix = "cite_descfix_changelog.jsonl"
    records = _read_jsonl(AUDIT_DIR / descfix)

    genuine_greek: dict[str, Any] | None = None
    genuine_latin: dict[str, Any] | None = None
    foreign_latin: dict[str, Any] | None = None

    for line_no, rec in enumerate(records, start=1):
        new_text = rec.get("new") or ""
        old_text = rec.get("old") or ""
        if genuine_greek is None:
            # Apostrophe-bearing runs (elision marks: U+02BC etc.) split Greek
            # run extraction in the quote gate and would make even a verbatim
            # quote fail word-bounded containment — prefer clean runs.
            runs = sorted(
                (
                    run
                    for run in _greek_runs(new_text, 6)
                    if not any(mark in run for mark in "ʼ'’᾽")
                ),
                key=len,
                reverse=True,
            )
            if runs:
                genuine_greek = {
                    "string": runs[0],
                    "node_id": rec["node_id"],
                    "source_file": f"data/audit/{descfix}",
                    "source_line": line_no,
                }
        if genuine_latin is None and not GREEK_CHAR_RE.search(new_text):
            spans = sorted(QUOTED_SPAN_RE.findall(new_text), key=len, reverse=True)
            old_spans = sorted(QUOTED_SPAN_RE.findall(old_text), key=len, reverse=True)
            if spans and old_spans and old_spans[0] not in new_text:
                genuine_latin = {
                    "string": spans[0],
                    "node_id": rec["node_id"],
                    "source_file": f"data/audit/{descfix}",
                    "source_line": line_no,
                }
                foreign_latin = {
                    "string": old_spans[0],
                    "node_id": rec["node_id"],
                    "source_file": f"data/audit/{descfix}",
                    "source_line": line_no,
                }

    # Only fingerprints not attested in any passage node: the gate fixtures
    # treat these as text that must never survive verification.
    fabricated_greek = [
        {
            "string": entry["string"],
            "node_id": entry["node_id"],
            "source_file": entry["source_file"],
            "source_line": entry["source_line"],
        }
        for entry in must_not_appear
        if entry["scan_answers"]
    ]

    missing = [
        name
        for name, value in (
            ("genuine_greek", genuine_greek),
            ("genuine_latin", genuine_latin),
            ("foreign_latin", foreign_latin),
        )
        if value is None
    ]
    if missing or not fabricated_greek:
        raise SystemExit(
            f"quote_gate_strings: could not extract {missing or 'fabricated_greek'} "
            "from the audit corpus"
        )

    return {
        "comment": (
            "Machine-derived by scripts/eval/build_gold_from_audit.py. Every "
            "string is copied verbatim from data/audit/ records — never edit "
            "ancient text by hand."
        ),
        "genuine_greek": genuine_greek,
        "genuine_latin": genuine_latin,
        "foreign_latin": foreign_latin,
        "fabricated_greek": fabricated_greek,
    }


# ---------------------------------------------------------------------------
# IO + drift check
# ---------------------------------------------------------------------------


def _render_jsonl(entries: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)


def _render_json(doc: dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify committed fixtures match a fresh derivation (CI gate).",
    )
    args = parser.parse_args(argv)

    citation_gold = build_citation_gold()
    must_not_appear = build_must_not_appear()
    quote_gate = build_quote_gate_strings(must_not_appear)

    outputs = {
        EVAL_DIR / "citation_gold.jsonl": _render_jsonl(citation_gold),
        EVAL_DIR / "must_not_appear.jsonl": _render_jsonl(must_not_appear),
        EVAL_DIR / "quote_gate_strings.json": _render_json(quote_gate),
    }

    if args.check:
        stale = [
            str(path.relative_to(REPO_ROOT))
            for path, content in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print(
                "Eval gold fixtures out of sync with data/audit/ — run "
                f"scripts/eval/build_gold_from_audit.py: {', '.join(stale)}",
                file=sys.stderr,
            )
            return 1
        print("Eval gold fixtures are in sync.")
        return 0

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(REPO_ROOT)}")
    print(
        f"citation_gold: {len(citation_gold)} | must_not_appear: "
        f"{len(must_not_appear)} | fabricated_greek: "
        f"{len(quote_gate['fabricated_greek'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
