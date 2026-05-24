"""Full-corpus reference audit: verify every stored passage's CTS URN against
the authoritative TEI edition on PerseusDL/OpenGreekAndLatin GitHub.

Constraints:
- lxml only — stdlib xml.* / pyexpat broken in this Python 3.14 build.
- Reads data/corpus/passages.jsonl (no DB access).
- Caches each work's authoritative passages in data/corpus/_audit_cache/.
- Idempotent: re-running skips already-cached works.

Outputs:
- data/corpus/reference_audit.tsv   (flagged passages only)
- data/corpus/reference_audit_summary.md
"""
from __future__ import annotations

import difflib
import json
import sys
import unicodedata
import urllib.error
from collections import defaultdict
from pathlib import Path
from typing import Any

# -- project imports (lxml-safe) ------------------------------------------------
# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.corpus_github_fetch import fetch_work_passages, github_xml_urls
from scripts.corpus_lib import read_jsonl
from scripts.corpus_urn import derive_work_urn

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
_PASSAGES_PATH = _REPO_ROOT / "data" / "corpus" / "passages.jsonl"
_CACHE_DIR = _REPO_ROOT / "data" / "corpus" / "_audit_cache"
_AUDIT_TSV = _REPO_ROOT / "data" / "corpus" / "reference_audit.tsv"
_AUDIT_MD = _REPO_ROOT / "data" / "corpus" / "reference_audit_summary.md"

_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

_LACUNA_RE = __import__("re").compile(r"[…]|\.\.\.|\. \. \.")


def norm(text: str) -> str:
    """NFC-normalise, collapse whitespace, unify lacuna markers."""
    text = unicodedata.normalize("NFC", text)
    text = _LACUNA_RE.sub("…", text)
    text = __import__("re").sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Per-work fetch with disk cache
# ---------------------------------------------------------------------------

def _cache_path(work_urn: str) -> Path:
    safe = work_urn.replace(":", "_").replace("/", "_")
    return _CACHE_DIR / f"{safe}.json"


def _load_cache(work_urn: str) -> list[dict] | None:
    p = _cache_path(work_urn)
    if p.exists():
        with p.open(encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(work_urn: str, passages: list[dict]) -> None:
    p = _cache_path(work_urn)
    with p.open("w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False)


def _has_version_suffix(work_urn: str) -> bool:
    """Return True if the URN has at least 3 dot-parts in the work segment
    (author.work.version) and can be used to construct a GitHub URL."""
    try:
        github_xml_urls(work_urn)
        return True
    except (IndexError, Exception):
        return False


def fetch_authoritative(work_urn: str) -> list[dict] | None:
    """Fetch + cache authoritative passages for *work_urn*.

    Returns None if the work is unresolvable (no version suffix) or fetch fails.
    Cached result (even empty list) returned on subsequent calls.
    """
    # Check cache first
    cached = _load_cache(work_urn)
    if cached is not None:
        return cached if cached else None  # empty list stored as sentinel for failed fetch

    # Verify we can construct a URL
    if not _has_version_suffix(work_urn):
        _save_cache(work_urn, [])  # sentinel: not fetchable
        return None

    try:
        passages = fetch_work_passages(work_urn)
        _save_cache(work_urn, passages if passages else [])
        return passages if passages else None
    except (urllib.error.URLError, Exception):
        _save_cache(work_urn, [])  # sentinel: fetch failed
        return None


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------

def classify_passage(
    stored_text: str,
    auth_map: dict[str, str],
    passage_urn: str,
) -> tuple[str, float]:
    """Classify a stored passage against the authoritative edition.

    Returns (class, similarity) where class is one of:
      match | minor_diff | divergent | ref_not_in_edition
    """
    ref = passage_urn  # full passage URN

    if ref not in auth_map:
        return "ref_not_in_edition", 0.0

    auth_text = auth_map[ref]
    stored_norm = norm(stored_text)
    auth_norm = norm(auth_text)

    if stored_norm == auth_norm:
        return "match", 1.0

    ratio = difflib.SequenceMatcher(None, stored_norm, auth_norm).ratio()
    if ratio >= 0.98:
        return "match", ratio
    if ratio >= 0.85:
        return "minor_diff", ratio
    return "divergent", ratio


def run_audit() -> None:
    print("Reading passages.jsonl …")
    all_passages = read_jsonl(_PASSAGES_PATH)
    print(f"  {len(all_passages):,} passages loaded")

    # Group by work_canonical_id
    by_work: dict[str, list[dict]] = defaultdict(list)
    for p in all_passages:
        by_work[p["work_canonical_id"]].append(p)

    print(f"  {len(by_work)} works\n")

    # Per-work statistics
    work_stats: dict[str, dict[str, Any]] = {}

    flagged_rows: list[dict] = []  # for TSV output

    total_verifiable_works = 0
    total_unverifiable_works = 0
    total_verifiable_passages = 0
    total_unverifiable_passages = 0

    class_counts: dict[str, int] = {
        "match": 0,
        "minor_diff": 0,
        "divergent": 0,
        "ref_not_in_edition": 0,
    }

    for work_idx, (work_id, passages) in enumerate(sorted(by_work.items()), 1):
        n = len(passages)
        urns = [p.get("cts_urn") for p in passages]

        # Derive work URN
        work_urn, urn_status = derive_work_urn(urns)

        # Attempt fetch
        auth_passages: list[dict] | None = None
        fetch_status = "unverifiable"

        if work_urn and urn_status == "resolved":
            auth_passages = fetch_authoritative(work_urn)
            if auth_passages is not None and len(auth_passages) > 0:
                fetch_status = "verified"

        if fetch_status == "unverifiable":
            reason = urn_status if urn_status != "resolved" else "fetch_failed_or_empty"
            work_stats[work_id] = {
                "status": "unverifiable",
                "reason": reason,
                "n_passages": n,
                "n_match": 0,
                "n_minor": 0,
                "n_divergent": 0,
                "n_ref_missing": 0,
                "work_urn": work_urn,
            }
            total_unverifiable_works += 1
            total_unverifiable_passages += n
            status_char = "U"
        else:
            # Build authoritative map: full_cts_urn -> normalised text
            auth_map: dict[str, str] = {p["cts_urn"]: p["text_content"] for p in auth_passages}  # type: ignore[union-attr]

            stats: dict[str, int] = {"match": 0, "minor_diff": 0, "divergent": 0, "ref_not_in_edition": 0}

            for passage in passages:
                cts = passage.get("cts_urn")
                text = passage.get("text_content", "")

                if not cts or not text:
                    # No URN or no text: unverifiable passage
                    continue

                cls, sim = classify_passage(text, auth_map, cts)
                stats[cls] += 1
                class_counts[cls] += 1

                if cls in ("ref_not_in_edition", "divergent"):
                    # Truncate samples to 200 chars for TSV
                    stored_sample = text[:200].replace("\t", " ").replace("\n", " ")
                    if cts in auth_map:
                        auth_sample = auth_map[cts][:200].replace("\t", " ").replace("\n", " ")
                    else:
                        auth_sample = "(ref absent from edition)"
                    flagged_rows.append({
                        "severity": "HIGH",
                        "work_canonical_id": work_id,
                        "cts_urn": cts,
                        "class": cls,
                        "similarity": f"{sim:.3f}",
                        "stored_sample": stored_sample,
                        "auth_sample": auth_sample,
                    })

            work_stats[work_id] = {
                "status": "verified",
                "reason": "",
                "n_passages": n,
                "n_match": stats["match"],
                "n_minor": stats["minor_diff"],
                "n_divergent": stats["divergent"],
                "n_ref_missing": stats["ref_not_in_edition"],
                "work_urn": work_urn,
            }
            total_verifiable_works += 1
            total_verifiable_passages += n
            status_char = "V"

        flags = work_stats[work_id].get("n_divergent", 0) + work_stats[work_id].get("n_ref_missing", 0)
        print(
            f"  [{work_idx:3d}/{len(by_work)}] {status_char} | "
            f"{n:5d} p | flags={flags:4d} | {work_id[:70]}"
        )

    # ------------------------------------------------------------------
    # Write TSV
    # ------------------------------------------------------------------
    print(f"\nWriting {_AUDIT_TSV} ({len(flagged_rows)} flagged rows) …")
    tsv_header = "severity\twork_canonical_id\tcts_urn\tclass\tsimilarity\tstored_sample\tauth_sample"
    with _AUDIT_TSV.open("w", encoding="utf-8") as f:
        f.write(tsv_header + "\n")
        for row in flagged_rows:
            line = "\t".join([
                row["severity"],
                row["work_canonical_id"],
                row["cts_urn"],
                row["class"],
                row["similarity"],
                row["stored_sample"],
                row["auth_sample"],
            ])
            f.write(line + "\n")

    # ------------------------------------------------------------------
    # Write Markdown summary
    # ------------------------------------------------------------------
    print(f"Writing {_AUDIT_MD} …")

    total_passages = len(all_passages)
    total_works = len(by_work)

    # Sort problem works by flags descending
    problem_works = sorted(
        [
            (wid, ws)
            for wid, ws in work_stats.items()
            if ws["status"] == "verified" and (ws["n_divergent"] + ws["n_ref_missing"]) > 0
        ],
        key=lambda x: x[1]["n_divergent"] + x[1]["n_ref_missing"],
        reverse=True,
    )

    verified_works = [
        (wid, ws) for wid, ws in work_stats.items() if ws["status"] == "verified"
    ]

    unverifiable_works = sorted(
        [(wid, ws) for wid, ws in work_stats.items() if ws["status"] == "unverifiable"],
        key=lambda x: x[1]["n_passages"],
        reverse=True,
    )

    lines: list[str] = []
    lines.append("# EleutherIA Corpus Reference Audit")
    lines.append("")
    lines.append("Audit date: 2026-05-24")
    lines.append("")
    lines.append("## Overall Totals")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total passages | {total_passages:,} |")
    lines.append(f"| Total works | {total_works} |")
    lines.append(f"| Verifiable works (GitHub TEI found) | {total_verifiable_works} |")
    lines.append(f"| Unverifiable works (no GitHub edition / SC / no URN) | {total_unverifiable_works} |")
    lines.append(f"| Passages in verifiable works | {total_verifiable_passages:,} |")
    lines.append(f"| Passages in unverifiable works | {total_unverifiable_passages:,} |")
    lines.append("")
    lines.append("### Classification of passages in verifiable works")
    lines.append("")
    lines.append(f"| Class | Count | Meaning |")
    lines.append(f"|-------|-------|---------|")
    lines.append(f"| match | {class_counts['match']:,} | Text ≥ 0.98 similarity or normalised-equal |")
    lines.append(f"| minor_diff | {class_counts['minor_diff']:,} | 0.85–0.98 similarity (edition/formatting differences) |")
    lines.append(f"| divergent | {class_counts['divergent']:,} | < 0.85 similarity (likely wrong text/edition) |")
    lines.append(f"| ref_not_in_edition | {class_counts['ref_not_in_edition']:,} | Passage URN absent from authoritative edition |")
    lines.append("")

    if problem_works:
        lines.append("## Top Problem Works (by flagged passage count)")
        lines.append("")
        lines.append("| Work | Passages | ref_missing | divergent | minor_diff | match | Work URN |")
        lines.append("|------|----------|-------------|-----------|-----------|-------|----------|")
        for wid, ws in problem_works[:20]:
            lines.append(
                f"| `{wid}` | {ws['n_passages']} | {ws['n_ref_missing']} | "
                f"{ws['n_divergent']} | {ws['n_minor']} | {ws['n_match']} | "
                f"`{ws['work_urn'] or ''}` |"
            )
        lines.append("")

    lines.append("## All Verified Works")
    lines.append("")
    lines.append("| Work | Passages | match | minor_diff | divergent | ref_missing | Work URN |")
    lines.append("|------|----------|-------|-----------|-----------|-------------|----------|")
    for wid, ws in sorted(verified_works, key=lambda x: x[0]):
        lines.append(
            f"| `{wid}` | {ws['n_passages']} | {ws['n_match']} | "
            f"{ws['n_minor']} | {ws['n_divergent']} | {ws['n_ref_missing']} | "
            f"`{ws['work_urn'] or ''}` |"
        )
    lines.append("")

    lines.append("## Unverifiable Works")
    lines.append("")
    lines.append("These works could not be checked against a GitHub authoritative edition.")
    lines.append("They require manual verification (Sources Chrétiennes, local DOCTORAT corpus, non-Perseus editions).")
    lines.append("")
    lines.append("| Work | Passages | Reason |")
    lines.append("|------|----------|--------|")
    for wid, ws in unverifiable_works:
        lines.append(f"| `{wid}` | {ws['n_passages']} | {ws['reason']} |")
    lines.append("")

    _AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")

    # ------------------------------------------------------------------
    # Stdout summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("CORPUS REFERENCE AUDIT — RESULTS")
    print("=" * 72)
    print(f"Total passages:            {total_passages:,}")
    print(f"  in verifiable works:     {total_verifiable_passages:,}")
    print(f"  in unverifiable works:   {total_unverifiable_passages:,}")
    print(f"Total works:               {total_works}")
    print(f"  verifiable:              {total_verifiable_works}")
    print(f"  unverifiable:            {total_unverifiable_works}")
    print()
    print("Classification (verifiable works only):")
    print(f"  match:               {class_counts['match']:,}")
    print(f"  minor_diff:          {class_counts['minor_diff']:,}")
    print(f"  divergent:           {class_counts['divergent']:,}")
    print(f"  ref_not_in_edition:  {class_counts['ref_not_in_edition']:,}")
    print()

    if problem_works:
        print(f"Top problem works ({len(problem_works)} works with HIGH-severity flags):")
        for wid, ws in problem_works[:10]:
            flags = ws["n_divergent"] + ws["n_ref_missing"]
            print(
                f"  {flags:4d} flags | {ws['n_ref_missing']:3d} ref_missing "
                f"| {ws['n_divergent']:3d} divergent | {wid}"
            )
    else:
        print("No HIGH-severity flags found.")

    print()
    print(f"TSV output:      {_AUDIT_TSV}")
    print(f"Markdown report: {_AUDIT_MD}")
    print("=" * 72)


if __name__ == "__main__":
    run_audit()
