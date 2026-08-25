#!/usr/bin/env python3
"""WHAT: three mechanical text artifacts in the corpus, each with its evidence.

Companion to ``apply_2026_08_26_corpus_text_artifacts.py``, which does the HOW.

Scope is deliberately narrow. Only defects that are **provably artifacts of
ingestion** are listed here — cases where the corrupted string cannot be a
reading of any edition and the correct string is either attested in a source we
opened or is simply the corrupted string with the artifact removed.

Everything that needs an editorial decision, or a critical edition we do not
have on this machine, is recorded in ``NOT_REPAIRED`` and left alone. That
includes every OCR-damaged Latin word in the Consolatio: no Boethius edition
exists on this machine, so ``iutueamur`` stays wrong rather than being
"corrected" from memory. Guessing at a reading is the one failure this project
cannot absorb.
"""

from __future__ import annotations

import re
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# 1. SVF II.931 — a line-join artifact that spliced a modern name into Greek
# ─────────────────────────────────────────────────────────────────────────────
#
# The row reads:
#     Οἱ Στωϊκοὶ δέ φασιν ὡς ταὐAugustinus τὸν εἱμαρμένη καὶ Ζεύς.
#
# This is not a corrupted Greek reading. In von Arnim the printed line breaks
# the word as ταὐ-τὸν, and the NEXT fragment opens "Augustinus de civ. dei V 8";
# the ingester joined the lines and carried the following fragment's first word
# into the middle of the Greek.
#
# EVIDENCE — verified directly in the local TLG E corpus, not from memory:
#   PYTHONPATH=. python3 scripts/tlg_search.py search 'ταὐτὸν εἱμαρμένη καὶ Ζεύς'
#   → 1 hit, TLG5026 (Scholia in Homerum) @byte 1419747:
#     "οἱ Στωϊκοὶ … δέ φασιν ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς."
#   The corpus sentence is that sentence with "Augustinus " spliced in.
#
# The repair therefore ADDS NO GREEK: it deletes eleven Latin-script characters
# and lets ταὐ + τὸν rejoin into the attested form.
SVF_PASSAGE_ID = "a230c68c-c903-5f99-b3aa-71ca5c42ab84"
SVF_ARTIFACT = "ταὐAugustinus τὸν"
SVF_REPAIRED = "ταὐτὸν"
SVF_ATTESTATION = "TLG5026 Scholia in Homerum @byte 1419747 (also TLG1264, SVF itself)"


# ─────────────────────────────────────────────────────────────────────────────
# 2-4. Boethius, De consolatione philosophiae — three ingestion artifacts
# ─────────────────────────────────────────────────────────────────────────────
#
# Work: urn_cts_latinlit_phi2089_phi002_lat, 129 rows.
#
# (2) Every row is prefixed with the literal string "Latin: ". A language label
#     is metadata; the corpus already carries the language on the work record.
#     Counted: 129/129 rows.
#
# (3) Every row ends with "\n\nBoethius, De consolatione philosophiae {n}",
#     a running footer the ingester appended. Counted: 129/129 rows, and in
#     every single one {n} equals the row's own sequence_number — which is what
#     proves it is a generated label and not text.
#
# (4) 481 occurrences of "WORD {WORD}" where the braced token is byte-identical
#     to the word immediately before it. Verified: 481/481 are exact echoes,
#     0 exceptions. No Latin text repeats a word inside braces; this is an
#     enclitic-splitting artifact.
#
# All three are removals of material that is provably not text. None of them
# invents a reading, and none touches a single letter of Latin.
BOETHIUS_WORK = "urn_cts_latinlit_phi2089_phi002_lat"
BOETHIUS_ROW_COUNT = 129

LANGUAGE_PREFIX = re.compile(r"^Latin:\s+")
RUNNING_FOOTER = re.compile(r"\n\nBoethius, De consolatione philosophiae (\d+)\s*$")
ECHOED_BRACE = re.compile(r"(?<=\s)([^\s{}]+) \{\1\}")


def strip_language_prefix(text: str) -> str:
    return LANGUAGE_PREFIX.sub("", text, count=1)


def strip_running_footer(text: str, sequence_number: Any) -> str:
    """Remove the footer ONLY when its number matches the row's own sequence.

    A mismatch would mean the string is something other than the generated
    label we identified, so the precondition fails and the row is left alone.
    """
    match = RUNNING_FOOTER.search(text)
    if match is None:
        return text
    if match.group(1) != str(sequence_number):
        return text
    return text[: match.start()].rstrip()


def collapse_echoed_braces(text: str) -> str:
    """Drop ``{word}`` when it exactly echoes the preceding word."""
    return ECHOED_BRACE.sub(r"\1", text)


# ─────────────────────────────────────────────────────────────────────────────
# Deliberately NOT repaired — recorded so the next auditor does not re-derive it
# ─────────────────────────────────────────────────────────────────────────────
NOT_REPAIRED: list[dict[str, str]] = [
    {
        "locus": "Alexander of Aphrodisias, De fato — whole work (tlg0732_tlg014_grc)",
        "defect": (
            "212 token divergences against Bruns/TLG, 51 dropped supplement "
            "brackets, ~20 dropped secludenda, a leaked apparatus line, a lost "
            "clause at Bruns 184.24. De fato 15 reads ἔχει where Bruns "
            "185.16-18 has ἔχειν, which the syntax requires."
        ),
        "why_not": (
            "This needs re-ingestion from the decoded Bruns text already on "
            "disk, not 212 hand patches. Patching would leave the work half "
            "collated and give a false impression of soundness."
        ),
        "note": (
            "The '[...]' in De fato 15 is NOT a defect: it re-notates the '***' "
            "lacuna sign Bruns himself prints. Do not restore anything there."
        ),
    },
    {
        "locus": "Boethius, Consolatio — OCR-damaged Latin words",
        "defect": (
            "72 hyphenation breaks ('Stoi -. cum'), 'laederenturhunc', "
            "'Draenoscendi'; and in the separate one-row record "
            "boethius_..._simultaneous_and_perfect_possession_o, "
            "'conprehendentimn' and 'iutueamur' plus 9 more damaged tokens."
        ),
        "why_not": (
            "No Boethius edition exists on this machine. Even 'iutueamur' for "
            "'intueamur' is a conjecture without an edition to collate against, "
            "and a conjecture silently written into a scholarly corpus is "
            "indistinguishable from a fabrication."
        ),
    },
    {
        "locus": "work_origen_philocalia_grc and its _eng sibling",
        "defect": (
            "0/30 rows contain a single Greek character; 30/30 are French "
            "(Junod, SC 226); language declared 'lat'; every cts_urn says "
            "greekLit; 24 rows carry the SC running head verbatim."
        ),
        "why_not": (
            "The record is mislabelled, not mistranscribed. The honest fix is "
            "to re-home the French as a declared translation and ingest the "
            "real Greek (available at TLG E TLG2042 and in the SC 226 file) — "
            "a re-ingestion with its own review, not a text patch."
        ),
    },
    {
        "locus": "urn_cts_greeklit_tlg0557_grc (Epictetus) and tlg2959_tlg002_grc (Methodius)",
        "defect": (
            "176 Epictetus rows are generated 'Greek: • term - gloss' bullet "
            "lists rather than text, and 183/235 contain English; the "
            "Methodius rows are apparatus criticus in German."
        ),
        "why_not": (
            "These records do not contain the works they claim to contain. "
            "That is an ingestion question, not a text-repair one."
        ),
    },
]
