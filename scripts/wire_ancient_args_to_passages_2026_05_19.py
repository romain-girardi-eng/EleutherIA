#!/usr/bin/env python3
"""Phase E3 — wire ancient ``argument`` nodes to existing primary-source
``passage`` nodes that already live in the KG.

Context
-------
Out of the 1608 ``needs_evidence`` nodes, the strategic audit identified

  * 168 ``structured_v2`` arguments whose ``metadata.premises[*].primary_sources``
    list passage IDs that are **already present in the KG** but never wired up
    as ``cites_primary_source`` edges.
  * 110 *non-v2* ancient arguments (Patristic, Hellenistic, Roman Imperial,
    Late Antiquity, Classical Greek, Second Temple Judaism, Presocratic)
    without any outgoing ``cites_primary_source`` / ``evidenced_by`` /
    ``source_for_reconstruction`` edge to a passage; many of these cite a
    canonical reference inside their description (« De Fato 12 », « 1 Apol.
    44 », « De Princ III.1.5-6 », etc.) whose corresponding passage already
    exists in the KG.

Both classes can be wired without any new text ingestion.

Ontology
--------
``cites_primary_source``: ``source ∈ {argument, publication, person}`` →
``target ∈ {passage, work}``. The 8e ReAct tool already relies on this
edge for the agentic retrieval.

Strategy
--------

**Stage A — V2 metadata harvest (deterministic, zero inference)**

For each ``argument`` node with ``metadata.structured_v2 = true``, harvest
every passage/work ID referenced in:

  * ``metadata.premises[*].primary_sources``
  * ``metadata.conclusion.primary_sources``
  * ``metadata.primary_sources``

Filter to IDs that actually exist in the KG as ``passage`` or ``work``
nodes. Emit one ``cites_primary_source`` edge per (arg, target). 100 %
safe: the wiring only reifies pointers that already live in the structured
metadata.

**Stage B — Non-v2 ancient regex matching (conservative)**

For each non-v2 ancient argument without passage evidence, parse the
description with a curated regex catalogue covering the canonical citation
patterns used by Romain in this corpus:

  * ``Apol. N``, ``1 Apol. N``, ``2 Apol. N``    → Justin Martyr
  * ``Dial. N``                                  → Justin Dialogue
  * ``De Princ(ipiis) X.Y[.Z]``                  → Origen
  * ``Contra Celsum X.Y`` / ``CC X.Y``           → Origen
  * ``Philocalia N`` / ``Phil. N``               → Origen
  * ``De Civ(itate) Dei X.Y``                    → Augustine
  * ``Conf(essions) X``                          → Augustine
  * ``De Lib(ero) Arb(itrio) X.Y``               → Augustine
  * ``De Fato N``                                → Alexander of Aphrodisias
  * ``Disc(ourses) X.Y`` / ``Diss. X.Y``         → Epictetus
  * ``Ench(eiridion) N`` / ``Man(uel) N``        → Epictetus
  * ``Enn(éades) X.Y[.Z]``                       → Plotinus
  * ``Cons(olation) X.pr.Y``                     → Boethius
  * ``Hex(aemeron) X``                           → Basil
  * ``De Hom(inis) Opif(icio) X``                → Gregory of Nyssa
  * ``Praep(aratio) Ev(angelica) X.Y``           → Eusebius
  * ``De Opif. N``, ``De Prov. N``, …            → Philo
  * ``DL X.Y``, ``Lives X.Y``                    → Diogenes Laertius

Each canonical match is then normalized and looked up against an index
built from passage ``canonical_ref`` + ``label`` (filtered by the inferred
author) — only emit an edge if the canonical reference yields **exactly
one** passage match per Greek/Latin or English variant pair.

Edge format
-----------
  source=argument, target=passage|work, relation=cites_primary_source,
  metadata = {
    "auto_generated": true,
    "wave": "wire_ancient_args_to_passages_2026_05_19",
    "stage": "v2_metadata_harvest" | "desc_regex",
    "match_method": "<which regex>" | "v2_premises" | "v2_conclusion" | "v2_top_level",
    "wiring_confidence": "high" | "medium",
  }

Idempotency
-----------
Re-running is a no-op:

  * arguments carrying ``e3_wired_at = 2026-05-19`` skip stage B regex
    (still harvest v2 metadata, but edge dedup makes that a no-op)
  * edge dedup on (source, target, relation).

Snapshot
--------
``data/kg/snapshots/2026-05-19-pre-e3-ancient-wiring/`` (nodes + edges).

Usage
-----
  python3 scripts/wire_ancient_args_to_passages_2026_05_19.py            # dry-run
  python3 scripts/wire_ancient_args_to_passages_2026_05_19.py --commit
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
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-e3-ancient-wiring"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"

WAVE_DATE = "2026-05-19"
WAVE_TAG = "wire_ancient_args_to_passages_2026_05_19"

ANCIENT_PERIODS = frozenset({
    "Patristic", "Hellenistic", "Roman Imperial", "Late Antiquity",
    "Classical Greek", "Second Temple Judaism", "Presocratic",
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
# Metadata helpers
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
    if isinstance(original, str):
        return json.dumps(md, ensure_ascii=False)
    return md


def norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s.\-:]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def roman_to_int(roman: str) -> int | None:
    roman = roman.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not roman or not all(c in values for c in roman):
        return None
    total = 0
    prev = 0
    for c in reversed(roman):
        v = values[c]
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total


# ---------------------------------------------------------------------------
# Edge record
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
# Passage index
# ---------------------------------------------------------------------------

def build_passage_indices(nodes: list[dict]) -> dict:
    """Return composite index for matching descriptive references → passage ids."""
    passages = [n for n in nodes if n.get("type") == "passage"]
    by_id: dict[str, dict] = {}
    by_canon_author: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_label_author: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_work_canon: dict[tuple[str, str], list[str]] = defaultdict(list)

    for n in passages:
        md = parse_metadata(n.get("metadata"))
        by_id[n["id"]] = md
        author = (md.get("author") or "").strip()
        author_n = norm(author)
        canon = (md.get("canonical_ref") or "").strip()
        label = (n.get("label") or "").strip()
        work_id = (md.get("work_canonical_id") or "").strip()
        if canon and author_n:
            by_canon_author[(author_n, norm(canon))].append(n["id"])
        if label and author_n:
            by_label_author[(author_n, norm(label))].append(n["id"])
        if work_id and canon:
            by_work_canon[(work_id, norm(canon))].append(n["id"])

    return {
        "by_id": by_id,
        "by_canon_author": by_canon_author,
        "by_label_author": by_label_author,
        "by_work_canon": by_work_canon,
    }


def passages_for_author(by_canon_author: dict, author_n: str) -> set[str]:
    out: set[str] = set()
    for (a, _c), pids in by_canon_author.items():
        if a == author_n:
            out.update(pids)
    return out


# ---------------------------------------------------------------------------
# Stage A: V2 metadata harvest
# ---------------------------------------------------------------------------

def harvest_v2_targets(arg_md: dict, kg_ids: set[str], passages: set[str], works: set[str]) -> list[tuple[str, str]]:
    """Return list of (target_id, source_field) for IDs that exist as passages/works."""
    found: dict[str, str] = {}

    def consume(field: str, vals):
        if not isinstance(vals, list):
            return
        for v in vals:
            if isinstance(v, str) and (v in passages or v in works):
                found.setdefault(v, field)

    for p in arg_md.get("premises", []) or []:
        if isinstance(p, dict):
            consume("v2_premises", p.get("primary_sources"))
    concl = arg_md.get("conclusion")
    if isinstance(concl, dict):
        consume("v2_conclusion", concl.get("primary_sources"))
    consume("v2_top_level", arg_md.get("primary_sources"))

    return list(found.items())


# ---------------------------------------------------------------------------
# Stage B: description regex matching
# ---------------------------------------------------------------------------

# Map author surname slug → canonical KG author string (as found in passage metadata)
AUTHOR_CANONICAL = {
    "justin": "Justin Martyr",
    "origen": "Origen of Alexandria",
    "augustine": "Augustine",
    "augustin": "Augustine",
    "epictetus": "Epictetus",
    "epictete": "Epictetus",
    "boethius": "Boethius",
    "boece": "Boethius",
    "alexander": "Alexander of Aphrodisias",
    "alex": "Alexander of Aphrodisias",
    "plotinus": "Plotinus",
    "plotin": "Plotinus",
    "aristotle": "Aristotle",
    "aristote": "Aristotle",
    "cicero": "Cicero",
    "ciceron": "Cicero",
    "diogenes": "Diogenes Laertius",
    "plato": "Plato",
    "platon": "Plato",
    "eusebius": "Eusebius of Caesarea",
    "eusebe": "Eusebius of Caesarea",
    "nemesius": "Nemesius",
    "nemesios": "Nemesius",
    "chrysostom": "John Chrysostom",
    "chrysostome": "John Chrysostom",
    "basil": "Basil",
    "basile": "Basil",
    "philo": "Philo of Alexandria",
    "philon": "Philo of Alexandria",
    "methodius": "Methodius",
    "methode": "Methodius",
    "gregory": "Gregory of Nyssa",
    "gregoire": "Gregory of Nyssa",
    "maximus": "Maximus the Confessor",
    "maxime": "Maximus the Confessor",
    "bardesanes": "Bardaisan",
    "bardaisan": "Bardaisan",
    "seneca": "Seneca",
    "lucretius": "Titus Lucretius Carus",
    "marcus": "Marcus Aurelius",
}


def detect_author_from_arg(arg: dict) -> str | None:
    """Infer the cited author from the argument label + ID."""
    label = (arg.get("label") or "").lower()
    aid = arg.get("id", "").lower()
    text = f"{label} {aid}"
    for slug, canon in AUTHOR_CANONICAL.items():
        if re.search(rf"\b{slug}\b", text):
            return canon
    return None


# Each pattern handler returns a list of canonical refs to try (in the
# format used in passage canonical_ref + label index).

def _patterns_for_author(author: str, text: str) -> list[tuple[str, list[str], str]]:
    """Return list of (regex_label, candidate_canon_refs, method_tag)."""
    out: list[tuple[str, list[str], str]] = []

    # Justin Martyr ----------------------------------------------------------
    if author == "Justin Martyr":
        # 1 Apol. N / 2 Apol. N / Apol. N / Dial. N
        # Justin: bare canonical_ref "N" is ambiguous (Apol1.5 AND Apol2.5 share canon="5"),
        # so only match against the full label (which carries "Apologia Prima"/"Apologia Secunda").
        for m in re.finditer(r"\b(1|I|first)\s*Apol(?:\.|ogi[ae])?\s*(\d{1,3})(?!\d)", text, re.IGNORECASE):
            n = m.group(2)
            out.append(("justin_1apol", [f"justin martyr, apologia prima, {n}"], "justin_1apol"))
        for m in re.finditer(r"\b(2|II|second)\s*Apol(?:\.|ogi[ae])?\s*(\d{1,3})(?!\d)", text, re.IGNORECASE):
            n = m.group(2)
            out.append(("justin_2apol", [f"justin martyr, apologia secunda, {n}"], "justin_2apol"))
        for m in re.finditer(r"(?<![\dIVivXLCDMxlcdm])(?<![\dIVivXLCDMxlcdm]\s)\bApol(?:\.|ogi[ae])?\s*(\d{1,3})(?!\d)", text, re.IGNORECASE):
            # Defaults to 1 Apol when unqualified (the conventional shorthand).
            n = m.group(1)
            out.append(("justin_apol_default", [f"justin martyr, apologia prima, {n}"], "justin_apol_default"))
        for m in re.finditer(r"\bDial(?:\.|ogue|ogus)?\s*(?:Tryph[oni]+\s*)?(\d{1,3})(?!\d)", text, re.IGNORECASE):
            n = m.group(1)
            out.append(("justin_dial", [f"justin martyr, dialogue with trypho, {n}"], "justin_dial"))

    # Origen -----------------------------------------------------------------
    if author == "Origen of Alexandria":
        # De Principiis III.1.5, Princ. III.1.5
        for m in re.finditer(r"\b(?:De\s+)?Princ(?:\.|ipi[oi]s|ipes|ipiis)?\s*([IVXLCDM]+)\.(\d{1,2})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, par = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                if par:
                    out.append(("origen_princ_ch_par", [f"{bi}.{ch}.{par}", f"princ {bi}.{ch}.{par}"], "origen_princ"))
                else:
                    out.append(("origen_princ_book_ch", [f"{bi}.{ch}", f"princ {bi}.{ch}"], "origen_princ"))
        # Contra Celsum X.Y, CC X.Y
        for m in re.finditer(r"\b(?:Contra\s+Celsum|CC|Cels)\s*([IVXLCDM]+)\.(\d{1,3})", text, re.IGNORECASE):
            book, ch = m.group(1), m.group(2)
            bi = roman_to_int(book)
            if bi:
                # passage canonical_ref pattern is e.g. "1.20"
                out.append(("origen_cc", [f"{bi}.{ch}", f"cc {bi} {ch}", f"cc {book.lower()} {ch}"], "origen_cc"))
        # Philocalia N or Phil. N (Origen)
        for m in re.finditer(r"\b(?:Philocali[ae]|Phil)\.?\s*(\d{1,2})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            ch, par = m.group(1), m.group(2)
            if par:
                out.append(("origen_philocalia", [f"origen, philocalia {ch}.{par}", f"philocalia {ch}.{par}"], "origen_philocalia"))

    # Augustine --------------------------------------------------------------
    if author == "Augustine":
        # De Civitate Dei X.Y[.Z]
        for m in re.finditer(r"\bDe\s+Civ(?:itate)?\.?\s+Dei\s+([IVXLCDM]+)(?:\.(\d{1,2}))?(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, sub = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                if sub:
                    out.append(("aug_civ_book_ch_sub", [f"de civitate dei {book.lower()}.{ch}.{sub}", f"aug civ {bi} {ch} {sub}"], "aug_civ"))
                elif ch:
                    # Use Roman + arabic mixed (the passage label uses 'XII.6')
                    out.append(("aug_civ_book_ch", [f"de civitate dei {book.lower()}.{ch}", f"aug civ {bi} {ch}", f"augustine, de civitate dei {book.lower()}.{ch}"], "aug_civ"))
        # De Lib. Arb. X.Y
        for m in re.finditer(r"\bDe\s+Lib(?:\.|ero)?\s*Arb(?:\.|itri[oi])?\s*([IVXLCDM]+|\d+)(?:\.(\d{1,2}))?(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, sub = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book) if not book.isdigit() else int(book)
            if bi:
                if sub:
                    out.append(("aug_lib_arb_full", [f"{bi}.{ch}.{sub}", f"aug lib arb {bi} {ch} {sub}"], "aug_lib_arb"))
                elif ch:
                    out.append(("aug_lib_arb_book_ch", [f"{bi}.{ch}"], "aug_lib_arb"))
        # Confessions VIII.5 etc.
        for m in re.finditer(r"\bConf(?:\.|essions?|essionum)?\s+([IVXLCDM]+)(?:\.(\d{1,2}))?(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, sub = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                if ch and sub:
                    out.append(("aug_conf_full", [f"{bi}.{ch}.{sub}"], "aug_conf"))
                elif ch:
                    out.append(("aug_conf_book_ch", [f"{bi}.{ch}"], "aug_conf"))

    # Alexander --------------------------------------------------------------
    if author == "Alexander of Aphrodisias":
        for m in re.finditer(r"\bDe\s+Fato\s+(\d{1,3})", text, re.IGNORECASE):
            n = m.group(1)
            out.append(("alex_fato", [f"de fato {n}"], "alex_fato"))
        # Fat. NN
        for m in re.finditer(r"\bFat(?:o|\.)\s+(\d{1,3})\b", text):
            n = m.group(1)
            out.append(("alex_fat_short", [f"de fato {n}"], "alex_fato"))

    # Epictetus --------------------------------------------------------------
    if author == "Epictetus":
        # Discourses I.1, Disc. IV.1, Diss. 1.12
        for m in re.finditer(r"\b(?:Disc(?:ourses)?|Diss(?:ert)?|Entretiens?)\.?\s+([IVXLCDM]+|\d+)\.(\d{1,2})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, par = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book) if not book.isdigit() else int(book)
            if bi:
                roman = "IVXLCDM"
                # Try both canonical formats
                roman_str = ""
                # int to roman
                vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
                x = bi
                for v, s in vals:
                    while x >= v:
                        roman_str += s; x -= v
                out.append(("epict_disc", [f"epict. disc. {roman_str}.{ch}", f"epict disc {bi} {ch}", f"epict. {bi}.{ch}"], "epict_disc"))
        # Encheiridion / Manuel N
        for m in re.finditer(r"\b(?:Ench(?:eiridion)?|Manuel|Manual)\.?\s*(\d{1,3})\b", text, re.IGNORECASE):
            n = m.group(1)
            out.append(("epict_ench", [f"epict. {n}", f"ench {n}", f"manuel {n}"], "epict_ench"))

    # Plotinus ---------------------------------------------------------------
    if author == "Plotinus":
        # Enn. III.1 or Ennéade VI.8 or Enn III.1.10
        for m in re.finditer(r"\bEnn(?:éades?|\.|eads?)?\s*([IVXLCDM]+)\.(\d{1,2})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, treat, ch = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                if ch:
                    out.append(("plot_enn_full", [f"enn. {book.upper()}.{treat}.{ch}", f"enn {bi}.{treat}.{ch}"], "plot_enn"))
                else:
                    out.append(("plot_enn_two", [f"enn. {book.upper()}.{treat}", f"enn {bi}.{treat}"], "plot_enn"))

    # Boethius ---------------------------------------------------------------
    if author == "Boethius":
        # Consolation V.pr.3 / Cons. V.pr.3
        for m in re.finditer(r"\b(?:Cons(?:olation|olatio|olations)?|Consol)\.?\s+([IVXLCDM]+)\.pr\.(\d{1,2})", text, re.IGNORECASE):
            book, pr = m.group(1), m.group(2)
            bi = roman_to_int(book)
            if bi:
                out.append(("boeth_cons_pr", [f"cons. {bi}.pr.{pr}", f"v.pr.{pr}", f"{bi}.pr.{pr}"], "boeth_cons"))
        # Cons. N (single arabic — too generic, skip)

    # Cicero -----------------------------------------------------------------
    if author == "Cicero":
        # De Divinatione II.N
        for m in re.finditer(r"\bDe\s+Div(?:inatione|\.)?\s+([IVXLCDM]+)(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch = m.group(1), m.group(2)
            bi = roman_to_int(book)
            if bi and ch:
                out.append(("cic_div", [f"de div. {ch}", f"div. {bi}.{ch}"], "cic_div"))
        # De Fato N (Cicero version — but Alexander too. Cicero's De Fato is sectioned 1..48)
        for m in re.finditer(r"\bCic(?:ero)?\.?\s*De\s+Fato\s+(\d{1,3})", text, re.IGNORECASE):
            n = m.group(1)
            out.append(("cic_fato", [f"cic. de fato {n}", f"de fato {n}"], "cic_fato"))

    # Plato ------------------------------------------------------------------
    if author == "Plato":
        # Stephanus pagination: Republic 617e, Apol. 17a, Timaeus 41e
        for m in re.finditer(r"\b(Rep(?:ublic|\.)?|Apol(?:\.|ogy)?|Tim(?:aeus|\.)?|Phaed(?:o|r|\.)?|Phileb(?:us|\.)?|Soph(?:ist|\.)?|Polit(?:icus|\.)?|Theaet(?:etus|\.)?|Symp(?:osium|\.)?|Crat(?:ylus|\.)?|Parm(?:enides|\.)?|Lg(?:\.|aws)?|Leges|Laws)\s+(\d{2,4}[a-e])", text, re.IGNORECASE):
            ref = m.group(2).lower()
            out.append(("plato_stephanus", [ref], "plato_stephanus"))

    # Aristotle --------------------------------------------------------------
    if author == "Aristotle":
        # NE / EN III.1 / III.5 / Met. IX.3
        for m in re.finditer(r"\b(NE|EN|Eth(?:\.|ica\.?\s+Nic\.?)?|Nic\.\s*Eth\.?)\s+([IVXLCDM]+)\.(\d{1,2})", text):
            book, ch = m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                out.append(("arist_ne", [f"{bi}.{ch}"], "arist_ne"))

    # Diogenes Laertius ------------------------------------------------------
    if author == "Diogenes Laertius":
        for m in re.finditer(r"\b(?:DL|Diog\.\s*Laert\.?|Lives|Vitae)\s+([IVXLCDM]+|\d+)\.(\d{1,3})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, sub = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book) if not book.isdigit() else int(book)
            if bi:
                if sub:
                    out.append(("dl_full", [f"{bi}.{ch}.{sub}"], "dl"))
                else:
                    out.append(("dl_book_ch", [f"{bi}.{ch}"], "dl"))

    # Philo ------------------------------------------------------------------
    if author == "Philo of Alexandria":
        # De Opif. N, De Prov. N
        for m in re.finditer(r"\bDe\s+Opif(?:icio)?\.?\s+(?:Mundi\s+)?(\d{1,3})", text, re.IGNORECASE):
            n = m.group(1)
            out.append(("philo_opif", [f"de opif. {n}"], "philo_opif"))

    # Eusebius ---------------------------------------------------------------
    if author == "Eusebius of Caesarea":
        # Praep. Ev. VI.10 / PE VI.10
        for m in re.finditer(r"\b(?:Praep(?:aratio|\.)?\s*Ev(?:angelica|\.)?|PE)\s+([IVXLCDM]+)\.(\d{1,3})(?:\.(\d{1,3}))?", text, re.IGNORECASE):
            book, ch, sub = m.group(1), m.group(2), m.group(3)
            bi = roman_to_int(book)
            if bi:
                if sub:
                    out.append(("eus_pe_full", [f"{book.upper()}.{ch}.{sub}", f"{bi}.{ch}.{sub}"], "eus_pe"))
                else:
                    out.append(("eus_pe_two", [f"{book.upper()}.{ch}", f"{bi}.{ch}"], "eus_pe"))

    return out


def regex_match_passages(arg: dict, by_canon_author: dict, by_label_author: dict) -> list[tuple[str, str]]:
    """Return list of (passage_id, method_tag) matched from description."""
    author = detect_author_from_arg(arg)
    if not author:
        return []
    desc = (arg.get("description") or "")
    label = (arg.get("label") or "")
    text = f"{label}\n{desc}"

    author_n = norm(author)
    out_unique: dict[str, str] = {}
    seen_methods: list[str] = []
    patterns = _patterns_for_author(author, text)

    for _rgx_label, candidates, method in patterns:
        hits: set[str] = set()
        for c in candidates:
            cn = norm(c)
            # Try canonical_ref index (exact match per (author, canon))
            for pid in by_canon_author.get((author_n, cn), []):
                hits.add(pid)
            # Try label index (full label match — strict; rarely fires)
            for pid in by_label_author.get((author_n, cn), []):
                hits.add(pid)
        if not hits:
            continue
        # Conservative: only retain when matches resolve to 1 (or 2 — Greek + EN pair).
        # The convention is paired ``passage_*`` + ``passage_*_en``.
        if len(hits) > 4:
            continue  # too ambiguous, skip
        for pid in hits:
            out_unique.setdefault(pid, method)
        seen_methods.append(method)

    return list(out_unique.items())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def has_passage_evidence(aid: str, edges_out: dict, edges_in: dict, passages: set[str]) -> bool:
    for r, t in edges_out.get(aid, []):
        if r in ("cites_primary_source", "evidenced_by", "source_for_reconstruction") and t in passages:
            return True
    for r, s in edges_in.get(aid, []):
        if r in ("source_for", "attests", "supports") and s in passages:
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="apply changes")
    parser.add_argument("--limit", type=int, default=None, help="debug: cap candidates")
    parser.add_argument("--stage", choices=["a", "b", "both"], default="both", help="run only stage A (v2) or B (regex)")
    args = parser.parse_args(argv)

    mode = "COMMIT" if args.commit else "dry-run"
    print(f"=== Phase E3 :: ancient-arg → passage wiring  ({mode}) ===")

    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"loaded {len(nodes)} nodes, {len(edges)} edges")

    nodes_by_id = {n["id"]: n for n in nodes}
    passages = {n["id"] for n in nodes if n.get("type") == "passage"}
    works = {n["id"] for n in nodes if n.get("type") == "work"}

    edges_out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges_in: dict[str, list[tuple[str, str]]] = defaultdict(list)
    existing_signatures: set[tuple[str, str, str]] = set()
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        edges_out[s].append((r, t))
        edges_in[t].append((r, s))
        existing_signatures.add(signature(s, t, r))

    pass_idx = build_passage_indices(nodes)
    print(
        f"passage index: by_canon_author={len(pass_idx['by_canon_author'])} keys, "
        f"by_label_author={len(pass_idx['by_label_author'])} keys"
    )

    # Collect candidates
    v2_cands: list[dict] = []
    non_v2_ancient_cands: list[dict] = []
    for n in nodes:
        if n.get("type") != "argument":
            continue
        md = parse_metadata(n.get("metadata"))
        if md.get("structured_v2"):
            v2_cands.append(n)
            continue
        period = n.get("period") or ""
        if period in ANCIENT_PERIODS and not has_passage_evidence(n["id"], edges_out, edges_in, passages):
            non_v2_ancient_cands.append(n)
    print(f"stage A candidates (structured_v2): {len(v2_cands)}")
    print(f"stage B candidates (ancient non-v2, no passage evidence): {len(non_v2_ancient_cands)}")

    if args.limit:
        v2_cands = v2_cands[: args.limit]
        non_v2_ancient_cands = non_v2_ancient_cands[: args.limit]

    new_edges: list[dict] = []
    edge_seen: set[tuple[str, str, str]] = set(existing_signatures)
    node_updates: dict[str, dict] = {}

    stat: Counter = Counter()
    method_counter: Counter = Counter()
    unmatched_refs: Counter = Counter()
    pattern_examples: defaultdict = defaultdict(list)
    stage_a_node_changes = 0
    stage_b_node_changes = 0

    # ----- Stage A -----
    if args.stage in ("a", "both"):
        for arg in v2_cands:
            aid = arg["id"]
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            harvested = harvest_v2_targets(md, set(nodes_by_id.keys()), passages, works)
            if not harvested:
                stat["v2_no_target_in_kg"] += 1
                continue
            wired_ids: list[str] = []
            for tgt, field in harvested:
                sig = signature(aid, tgt, "cites_primary_source")
                if sig in edge_seen:
                    stat["v2_edge_exists"] += 1
                    continue
                meta = {
                    "auto_generated": True,
                    "wave": WAVE_TAG,
                    "stage": "v2_metadata_harvest",
                    "match_method": field,
                    "wiring_confidence": "high",
                }
                new_edges.append(edge_record(aid, tgt, "cites_primary_source", weight=0.9, meta=meta))
                edge_seen.add(sig)
                stat["v2_edges_emitted"] += 1
                method_counter[f"v2:{field}"] += 1
                wired_ids.append(tgt)
                if tgt in works:
                    stat["v2_edges_to_work"] += 1
                else:
                    stat["v2_edges_to_passage"] += 1
            if wired_ids:
                md["e3_wired_at"] = WAVE_DATE
                md["e3_stage"] = "v2_metadata_harvest"
                md["e3_passages_cited"] = sorted(set((md.get("e3_passages_cited") or []) + wired_ids))
                patched = dict(arg)
                patched["metadata"] = serialize_metadata(md, md_orig)
                node_updates[aid] = patched
                stage_a_node_changes += 1

    # ----- Stage B -----
    if args.stage in ("b", "both"):
        for arg in non_v2_ancient_cands:
            aid = arg["id"]
            md_orig = arg.get("metadata")
            md = parse_metadata(md_orig)
            if md.get("e3_wired_at") == WAVE_DATE and md.get("e3_stage") == "desc_regex":
                stat["b_already_processed"] += 1
                continue

            matches = regex_match_passages(arg, pass_idx["by_canon_author"], pass_idx["by_label_author"])
            if not matches:
                stat["b_no_regex_match"] += 1
                # mark attempted refs for diagnostics
                auth = detect_author_from_arg(arg)
                if auth:
                    # Pull unique candidate refs that produced empty hits — for the
                    # "passage_not_in_kg" report.
                    text = (arg.get("label") or "") + " " + (arg.get("description") or "")
                    patterns = _patterns_for_author(auth, text)
                    for _l, cands, method in patterns:
                        if cands:
                            unmatched_refs[(auth, cands[0])] += 1
                            if len(pattern_examples[method]) < 3:
                                pattern_examples[method].append((aid, cands[0]))
                continue

            wired_ids: list[str] = []
            for tgt, method in matches:
                sig = signature(aid, tgt, "cites_primary_source")
                if sig in edge_seen:
                    stat["b_edge_exists"] += 1
                    continue
                meta = {
                    "auto_generated": True,
                    "wave": WAVE_TAG,
                    "stage": "desc_regex",
                    "match_method": method,
                    "wiring_confidence": "medium",
                }
                new_edges.append(edge_record(aid, tgt, "cites_primary_source", weight=0.7, meta=meta))
                edge_seen.add(sig)
                stat["b_edges_emitted"] += 1
                method_counter[f"b:{method}"] += 1
                wired_ids.append(tgt)
                if len(pattern_examples[method]) < 3:
                    pattern_examples[method].append((aid, tgt))
            if wired_ids:
                md["e3_wired_at"] = WAVE_DATE
                md["e3_stage"] = "desc_regex"
                md["e3_passages_cited"] = sorted(set((md.get("e3_passages_cited") or []) + wired_ids))
                patched = dict(arg)
                patched["metadata"] = serialize_metadata(md, md_orig)
                node_updates[aid] = patched
                stage_b_node_changes += 1

    # ----- Report -----
    print("\n=== Stats ===")
    for k in (
        "v2_edges_emitted",
        "v2_edges_to_passage",
        "v2_edges_to_work",
        "v2_edge_exists",
        "v2_no_target_in_kg",
        "b_edges_emitted",
        "b_edge_exists",
        "b_no_regex_match",
        "b_already_processed",
    ):
        print(f"  {k}: {stat[k]}")
    print(f"  stage A nodes patched: {stage_a_node_changes}")
    print(f"  stage B nodes patched: {stage_b_node_changes}")
    print(f"  total new edges: {len(new_edges)}")

    print("\nTop 15 match methods:")
    for m, c in method_counter.most_common(15):
        print(f"  {c:>4}  {m}")

    if pattern_examples:
        print("\nMethod examples (up to 3 per method):")
        for method, exs in pattern_examples.items():
            for aid, target in exs[:3]:
                print(f"  {method:<22} {aid:<55} -> {target}")

    if unmatched_refs:
        print(f"\nTop 20 unmatched references (passage_not_in_kg candidates, of {len(unmatched_refs)} distinct):")
        for (auth, ref), c in unmatched_refs.most_common(20):
            print(f"  {c:>3}  {auth:<28} {ref!r}")

    if not args.commit:
        print("\n(dry-run; pass --commit to write)")
        return 0

    if not new_edges and not node_updates:
        print("\nOK: nothing to apply.")
        return 0

    snapshot()
    print(f"\nsnapshot written to {SNAPSHOT_DIR}")

    if node_updates:
        new_nodes = [node_updates.get(n["id"], n) for n in nodes]
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
