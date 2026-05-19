#!/usr/bin/env python3
"""Phase D — Enrichissement métadonnées publications (audit qualité 2026-05-18).

Constat audit :
- 320/339 publications sans `local_pdf_path`
- 167/339 sans ISBN ni DOI
- 11/339 sans `year` dans metadata

Mandat (3 sous-tâches idempotentes, DRY-RUN par défaut) :

D1 — `local_pdf_path` depuis DOCTORAT
    Pour chaque pub sans local_pdf_path, extrait <surname>+<year> de l'ID,
    cherche dans `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/
    04_Littérature_secondaire/` un PDF dont le nom contient à la fois
    surname et year. Match unique → ajout ; matchs multiples → choisit le
    plus gros PDF ; aucun match → log "no_local_pdf".

D2 — ISBN/DOI via Crossref + OpenLibrary
    Pour chaque pub sans ISBN ET sans DOI ET avec author + year + title :
    - Articles (metadata.journal présent)   → Crossref par auteur + titre
    - Monographes (metadata.publisher etc.) → Crossref puis OpenLibrary
    Match score > 0.85 → ajout DOI ; ISBN OL ajouté si trouvé.
    Rate limit Crossref : 5 req/s (sleep 0.2s) ; OpenLibrary : 100/min.

D3 — `year` manquant
    Si metadata.year est null/0/missing ET l'ID matche `<prefix>_<surname>_<YEAR>_*`
    avec YEAR != 0, pose metadata.year = YEAR.

D4 — Validation
    - ISBN-13 valide (regex ^97[89]\\d{10}$)
    - DOI valide (regex ^10\\.\\d+/\\S+$)
    - year int entre 1500 et 2030
    - local_pdf_path → fichier existant (os.path.exists)

Marker : `phase_d_enriched_at: 2026-05-18` + `phase_d_added_fields: [...]`.
Préservation byte-exact des publications non touchées.
Snapshot OBLIGATOIRE dans `data/kg/snapshots/2026-05-18-pre-phase-d-metadata/`.

DRY-RUN par défaut. `--commit` pour appliquer.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
SNAPSHOT_DIR = (
    ROOT / "data" / "kg" / "snapshots"
    / "2026-05-18-pre-phase-d-metadata"
)

DOCTORAT_ROOT = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/"
    "04_Littérature_secondaire"
)

PHASE_TAG = "phase_d_enriched_at"
PHASE_VALUE = "2026-05-18"
PHASE_FIELDS_KEY = "phase_d_added_fields"
NOW = datetime.now(UTC).isoformat(sep=" ")

CROSSREF_BASE = "https://api.crossref.org/works"
OPENLIBRARY_BASE = "https://openlibrary.org/search.json"
USER_AGENT = (
    "EleutherIA-PhaseD/1.0 (https://free-will.app; "
    "mailto:contact@free-will.app)"
)
CROSSREF_SLEEP = 0.2  # 5 req/s
OPENLIBRARY_SLEEP = 0.65  # ~90 req/min
HTTP_TIMEOUT = 10.0

ISBN13_RE = re.compile(r"^97[89]\d{10}$")
ISBN10_RE = re.compile(r"^\d{9}[\dXx]$")
DOI_RE = re.compile(r"^10\.\d+/\S+$")

# Pub-ID extraction. Surname may contain underscores (e.g. boys_stones).
ID_RE = re.compile(
    r"^(?:pub|scholarly_work)_([a-z][a-z_]*?)_(\d{1,4})_(.+)$"
)


# ============================================================
# Utilities
# ============================================================


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def extract_id_parts(node_id: str) -> tuple[str | None, int | None, str]:
    """Return (surname, year, slug). Year=None if not encoded or == 0."""
    m = ID_RE.match(node_id)
    if not m:
        return (None, None, "")
    surname = m.group(1)
    year_raw = int(m.group(2))
    year = year_raw if 1500 <= year_raw <= 2030 else None
    return (surname, year, m.group(3))


# ============================================================
# D1 — Local PDF discovery
# ============================================================


def index_doctorat_pdfs() -> list[Path]:
    if not DOCTORAT_ROOT.exists():
        return []
    return sorted(p for p in DOCTORAT_ROOT.rglob("*") if p.is_file()
                  and p.suffix.lower() == ".pdf")


def find_local_pdf(
    surname: str,
    year: int | None,
    pdfs: list[Path],
    title_slug: str = "",
) -> tuple[Path | None, str]:
    """Return (path, reason). Match strategy :
    1) name normalize contains surname AND year
    2) if year is None, name contains surname AND >=2 title-slug tokens
    Tie-break : largest file (most likely full text, not metadata stub).
    """
    surname_norm = normalize(surname.replace("_", ""))
    surname_alt = normalize(surname.replace("_", " "))
    cands: list[Path] = []
    for p in pdfs:
        name = normalize(p.name)
        has_surname = (
            surname_norm in name.replace(" ", "").replace("_", "")
            or surname_alt in name
        )
        if not has_surname:
            continue
        if year is not None:
            if str(year) in name:
                cands.append(p)
        else:
            slug_tokens = [
                t for t in title_slug.split("_")
                if len(t) > 3 and t not in {
                    "with", "from", "this", "that", "their",
                    "into", "free", "will", "and", "the",
                }
            ]
            if not slug_tokens:
                continue
            hits = sum(1 for t in slug_tokens if normalize(t) in name)
            if hits >= 2:
                cands.append(p)
    if not cands:
        return (None, "no_local_pdf")
    if len(cands) == 1:
        return (cands[0], "unique_match")
    cands.sort(key=lambda p: p.stat().st_size, reverse=True)
    return (cands[0], f"largest_of_{len(cands)}")


# ============================================================
# D2 — Crossref + OpenLibrary lookups
# ============================================================


def http_get_json(url: str) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError):
        return None


def crossref_lookup(
    surname: str, year: int | None, title: str,
) -> tuple[str | None, float, str]:
    """Return (doi, score, reason)."""
    params = {
        "query.author": surname,
        "query.title": title[:200],
        "rows": "3",
    }
    url = f"{CROSSREF_BASE}?{urllib.parse.urlencode(params)}"
    data = http_get_json(url)
    time.sleep(CROSSREF_SLEEP)
    if not data or "message" not in data:
        return (None, 0.0, "crossref_no_response")
    items = data["message"].get("items") or []
    best_doi: str | None = None
    best_score = 0.0
    for it in items:
        cr_title = (it.get("title") or [""])[0]
        if not cr_title:
            continue
        score = title_similarity(title, cr_title)
        # Year confirmation bonus
        cr_year_parts = (it.get("issued") or {}).get("date-parts") or [[None]]
        cr_year = cr_year_parts[0][0] if cr_year_parts and cr_year_parts[0] else None
        if year and cr_year and abs(int(cr_year) - year) <= 1:
            score += 0.05
        # Author surname confirmation
        authors = it.get("author") or []
        if any(normalize(surname) in normalize(a.get("family", ""))
               for a in authors):
            score += 0.05
        if score > best_score:
            best_score = score
            best_doi = it.get("DOI")
    if best_doi and best_score >= 0.85 and DOI_RE.match(best_doi):
        return (best_doi, best_score, "crossref_match")
    return (None, best_score, "crossref_low_score")


def openlibrary_lookup(
    surname: str, year: int | None, title: str,
) -> tuple[str | None, float, str]:
    """Return (isbn13, score, reason)."""
    params = {
        "author": surname,
        "title": title[:120],
        "limit": "5",
    }
    url = f"{OPENLIBRARY_BASE}?{urllib.parse.urlencode(params)}"
    data = http_get_json(url)
    time.sleep(OPENLIBRARY_SLEEP)
    if not data:
        return (None, 0.0, "ol_no_response")
    docs = data.get("docs") or []
    best_isbn: str | None = None
    best_score = 0.0
    for d in docs:
        ol_title = d.get("title") or ""
        if not ol_title:
            continue
        score = title_similarity(title, ol_title)
        ol_year = d.get("first_publish_year")
        if year and ol_year and abs(int(ol_year) - year) <= 2:
            score += 0.05
        if score < 0.85:
            continue
        isbns = d.get("isbn") or []
        for isbn in isbns:
            clean = isbn.replace("-", "").replace(" ", "")
            if ISBN13_RE.match(clean):
                if score > best_score:
                    best_score = score
                    best_isbn = clean
                break
    if best_isbn:
        return (best_isbn, best_score, "openlibrary_match")
    return (None, best_score, "openlibrary_low_score")


# ============================================================
# D4 — Validators
# ============================================================


def valid_isbn13(s: str) -> bool:
    return bool(ISBN13_RE.match(s))


def valid_doi(s: str) -> bool:
    return bool(DOI_RE.match(s))


def valid_year(y: Any) -> bool:
    try:
        return 1500 <= int(y) <= 2030
    except (TypeError, ValueError):
        return False


# ============================================================
# Pipeline
# ============================================================


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)


def apply_phase_d(
    commit: bool,
    skip_lookups: bool = False,
    limit_lookups: int | None = None,
) -> int:
    raw_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pdfs = index_doctorat_pdfs()
    print(f"[index] {len(pdfs)} PDFs under {DOCTORAT_ROOT}", file=sys.stderr)

    # D1/D2/D3 counters + logs
    d1_found: list[tuple[str, str, str]] = []
    d1_missing: list[str] = []
    d2_doi: list[tuple[str, str, float]] = []
    d2_isbn: list[tuple[str, str, float]] = []
    d2_failed: list[tuple[str, str]] = []
    d3_year: list[tuple[str, int]] = []
    skipped: list[tuple[str, str]] = []
    invalid: list[tuple[str, str, str]] = []

    out_lines: list[str] = list(raw_lines)
    lookups_done = 0

    for idx, line in enumerate(raw_lines):
        node = json.loads(line)
        if node.get("type") != "publication":
            continue
        pid = node["id"]
        try:
            meta = parse_metadata(node.get("metadata"))
        except Exception as e:
            invalid.append((pid, "meta_parse_error", str(e)))
            continue

        if meta.get(PHASE_TAG) == PHASE_VALUE:
            skipped.append((pid, "already_phase_d_enriched"))
            continue

        surname, id_year, slug = extract_id_parts(pid)
        added_fields: list[str] = []

        # ---- D3: year inference from ID
        meta_year = meta.get("year")
        year_missing = (
            meta_year is None or meta_year == 0 or meta_year == "0"
        )
        if year_missing and id_year is not None and valid_year(id_year):
            meta["year"] = id_year
            added_fields.append("year")
            d3_year.append((pid, id_year))
        # Working year for downstream lookups
        effective_year: int | None
        try:
            effective_year = int(meta.get("year")) if meta.get("year") else None
        except (TypeError, ValueError):
            effective_year = None
        if effective_year is not None and not valid_year(effective_year):
            effective_year = None

        # ---- D1: local PDF lookup
        if not meta.get("local_pdf_path") and surname is not None:
            pdf, reason = find_local_pdf(
                surname, effective_year, pdfs, slug,
            )
            if pdf is not None and pdf.exists():
                meta["local_pdf_path"] = str(pdf)
                added_fields.append("local_pdf_path")
                d1_found.append((pid, str(pdf), reason))
            else:
                d1_missing.append(pid)
        elif not meta.get("local_pdf_path"):
            d1_missing.append(pid)

        # ---- D2: ISBN/DOI lookup
        has_isbn = bool(meta.get("isbn") or meta.get("ISBN")
                        or meta.get("isbn13"))
        has_doi = bool(meta.get("doi") or meta.get("DOI"))
        title = (meta.get("title") or meta.get("book_title")
                 or node.get("label") or "")
        # Trim "Surname YYYY — " prefix the shells use as label
        title = re.sub(r"^[A-Za-zÀ-ÿ\-]+\s*\?\s*—\s*", "", title).strip()

        if (not has_isbn and not has_doi and surname and title
                and effective_year and not skip_lookups):
            if limit_lookups is not None and lookups_done >= limit_lookups:
                d2_failed.append((pid, "lookup_limit_reached"))
            else:
                lookups_done += 1
                is_article = bool(meta.get("journal")
                                  or meta.get("journal_short"))
                doi: str | None = None
                isbn: str | None = None
                # Try Crossref for both, but for articles it's primary
                cr_doi, cr_score, cr_reason = crossref_lookup(
                    surname, effective_year, title,
                )
                if cr_doi:
                    doi = cr_doi
                    d2_doi.append((pid, cr_doi, cr_score))
                # OpenLibrary mainly for monographs (or as ISBN backstop)
                if not is_article:
                    ol_isbn, ol_score, _ol_reason = openlibrary_lookup(
                        surname, effective_year, title,
                    )
                    if ol_isbn and valid_isbn13(ol_isbn):
                        isbn = ol_isbn
                        d2_isbn.append((pid, ol_isbn, ol_score))
                if doi:
                    meta["doi"] = doi
                    added_fields.append("doi")
                if isbn:
                    meta["isbn"] = isbn
                    added_fields.append("isbn")
                if not doi and not isbn:
                    d2_failed.append((pid, cr_reason))

        # ---- D4: validate everything we touched
        if ("local_pdf_path" in added_fields
                and not os.path.exists(meta["local_pdf_path"])):
            invalid.append((pid, "local_pdf_path",
                            meta["local_pdf_path"]))
            added_fields.remove("local_pdf_path")
            meta.pop("local_pdf_path", None)
        if "doi" in added_fields and not valid_doi(meta.get("doi", "")):
            invalid.append((pid, "doi", str(meta.get("doi"))))
            added_fields.remove("doi")
            meta.pop("doi", None)
        if "isbn" in added_fields and not valid_isbn13(meta.get("isbn", "")):
            invalid.append((pid, "isbn", str(meta.get("isbn"))))
            added_fields.remove("isbn")
            meta.pop("isbn", None)
        if "year" in added_fields and not valid_year(meta.get("year")):
            invalid.append((pid, "year", str(meta.get("year"))))
            added_fields.remove("year")

        # Commit changes to node only if at least one field was added
        if added_fields:
            meta[PHASE_TAG] = PHASE_VALUE
            existing_phase_fields = meta.get(PHASE_FIELDS_KEY) or []
            if not isinstance(existing_phase_fields, list):
                existing_phase_fields = []
            meta[PHASE_FIELDS_KEY] = sorted(
                set(existing_phase_fields) | set(added_fields)
            )
            node["metadata"] = json.dumps(meta, ensure_ascii=False)
            node["updated_at"] = NOW
            out_lines[idx] = json.dumps(node, ensure_ascii=False)

    # ---- Report
    print()
    print("=" * 64)
    print("Phase D — enrichment report")
    print("=" * 64)
    print(f"D1 PDFs found:    {len(d1_found)} "
          f"(missing: {len(d1_missing)})")
    print(f"D2 DOIs added:    {len(d2_doi)}")
    print(f"D2 ISBNs added:   {len(d2_isbn)}")
    print(f"D2 lookups fail:  {len(d2_failed)}")
    print(f"D3 years added:   {len(d3_year)}")
    print(f"Skipped (already enriched): {len(skipped)}")
    print(f"Invalidated (D4): {len(invalid)}")
    print()
    if d1_found:
        print("--- Sample D1 (first 15) ---")
        for pid, path, reason in d1_found[:15]:
            print(f"  [{reason}] {pid}")
            print(f"      -> {path}")
    if d2_doi:
        print("--- D2 DOI additions (first 15) ---")
        for pid, doi, score in d2_doi[:15]:
            print(f"  {pid}  doi={doi}  score={score:.2f}")
    if d2_isbn:
        print("--- D2 ISBN additions (first 15) ---")
        for pid, isbn, score in d2_isbn[:15]:
            print(f"  {pid}  isbn={isbn}  score={score:.2f}")
    if d3_year:
        print("--- D3 year inferences ---")
        for pid, y in d3_year:
            print(f"  {pid}  year={y}")
    if invalid:
        print("--- D4 invalidations ---")
        for pid, field, val in invalid:
            print(f"  {pid}  {field}={val!r}")

    # ---- Write
    if not commit:
        print()
        print("DRY-RUN — no file written. Re-run with --commit to persist.")
        return 0

    snapshot()
    NODES_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print()
    print(f"Snapshot:    {SNAPSHOT_DIR}")
    print(f"Written:     {NODES_PATH}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true",
                    help="Persist changes. Default is DRY-RUN.")
    ap.add_argument("--skip-lookups", action="store_true",
                    help="Skip D2 (Crossref / OpenLibrary). "
                         "Run only D1 + D3.")
    ap.add_argument("--limit-lookups", type=int, default=None,
                    help="Hard cap on number of D2 HTTP lookups "
                         "(useful for testing).")
    args = ap.parse_args()
    return apply_phase_d(
        commit=args.commit,
        skip_lookups=args.skip_lookups,
        limit_lookups=args.limit_lookups,
    )


if __name__ == "__main__":
    sys.exit(main())
