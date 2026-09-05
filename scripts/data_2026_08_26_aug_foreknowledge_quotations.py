#!/usr/bin/env python3
"""WHAT: `synthesis_aug_foreknowledge` presents unattested Latin as quotation.

Companion to ``apply_2026_08_26_aug_foreknowledge_quotations.py``.

This is a breach of the project's own Golden Rule ("If it's not in the database
with a verifiable source, it doesn't exist"), and the node was flagged
``citation_verified: true`` while breaching it. Its own metadata already knew:

    latin_locus:   "… (argument genuine; this exact Latin is a compressed
                    paraphrase, not the transmitted text)"
    latin_verdict: "false_positive"

but ``citation_verdict: "verified"`` sat on top and certified the whole node.

Three Latin strings appear inside quotation marks in the description. Each was
checked individually against ``data/corpus/passages.jsonl`` — the transmitted
text of De libero arbitrio, work ``urn_cts_latinlit_stoa0040_stoa003_lat``:

┌───────────────────────────────────────────────┬────────┬─────────────────────┐
│ quoted string                                 │ hits   │ verdict             │
├───────────────────────────────────────────────┼────────┼─────────────────────┤
│ "si praescivit, necessario futurum erat"      │      0 │ NOT transmitted     │
│ "mea voluntate futurum" / "non voluntate…"    │      0 │ NOT transmitted     │
│ "sicut tu memoria tua non cogis…"             │      0 │ altered quotation   │
│   transmitted form, with `enim`               │      2 │ attested at 3.4.11  │
└───────────────────────────────────────────────┴────────┴─────────────────────┘

So the repairs are, in order of what the evidence permits:

1. **3.4.11 — restore the transmitted wording.** The node dropped ``enim`` and
   turned a semicolon into a comma. The real sentence is in the corpus and is
   copied verbatim below. The cited locus also narrows from "3.4.10-11" to
   3.4.11, which is where it actually stands.

2. **3.2.4 — replace the paraphrase with transmitted text.** The compression
   ``si praescivit, necessario futurum erat`` is nowhere in the work; the
   sentence it was compressing IS in the corpus and is copied verbatim.

3. **3.5.14 — delete the quotation, substitute nothing.** Neither string occurs
   anywhere in the corpus, and the passage at that locus is the analogy of the
   round nut and the sinless angels, which is not about that distinction at
   all. Hunting through the work for some other sentence that would justify the
   claim would be reasoning backwards from a conclusion. It goes, and if the
   distinction is wanted it comes back later with a real locus.

No Latin is composed here. Every replacement string is copied out of an
attested corpus row, and where no attested row supports the claim, the claim is
removed rather than re-sourced by guesswork.
"""

from __future__ import annotations

NODE_ID = "synthesis_aug_foreknowledge"
# The 2026-09-05 source adjudication preserved these loci and text while
# correcting the legacy CTS identity, which actually designates De civitate Dei.
WORK = "augustine_de_libero_arbitrio_migne_lat"

# ── 1. The memory analogy, transmitted form ──────────────────────────────────
# Copied verbatim from the corpus row `3.4.11` of the work above.
ALTERED_MEMORY_QUOTE = (
    "sicut tu memoria tua non cogis facta esse quae praeterierunt, "
    "sic Deus praescientia sua non cogit facienda quae futura sunt"
)
TRANSMITTED_MEMORY_QUOTE = (
    "Sicut enim tu memoria tua non cogis facta esse quae praeterierunt; "
    "sic Deus praescientia sua non cogit facienda quae futura sunt."
)

# ── 2. The problem stated, transmitted form ──────────────────────────────────
# Copied verbatim from the corpus row `3.2.4`.
PARAPHRASED_PROBLEM = '"si praescivit, necessario futurum erat" - the problem stated'
TRANSMITTED_PROBLEM = (
    '"quoniam peccaturum esse praesciverat, necesse erat id fieri, quod futurum '
    'esse praesciebat Deus" - the problem stated'
)

# ── 3. The unsupported distinction, removed ──────────────────────────────────
UNATTESTED_DISTINCTION = (
    " 3.5.14 (passage_aug_lib_arb_3_5_14): Key distinction between "
    '"mea voluntate futurum" and "non voluntate futurum".'
)
REMOVAL_REPLACEMENT = ""

# The locus for the memory analogy is 3.4.11, not the pair.
OLD_MEMORY_LOCUS = "3.4.10-11 (passage_aug_lib_arb_3_4_10, passage_aug_lib_arb_3_4_11)"
NEW_MEMORY_LOCUS = "3.4.11 (passage_aug_lib_arb_3_4_11)"

# ── Metadata: the flag that certified the breach ─────────────────────────────
#
# `latin_verdict: "false_positive"` was right and was overridden. After the
# repair the quotations ARE transmitted text, so the node can be marked
# verified again — but honestly, and with the audit recorded.
METADATA_UPDATES = {
    "citation_verdict": "corrected",
    "latin_verified": True,
    "latin_verdict": "verified",
    "latin_locus": (
        "Augustine, De libero arbitrio III.2.4 and III.4.11 — quotations "
        "restored to the transmitted text (corpus work "
        "augustine_de_libero_arbitrio_migne_lat); the III.5.14 quotation was "
        "unattested and has been removed."
    ),
    "quotation_audit_2026_08_26": (
        "Three quoted Latin strings checked individually against the corpus: "
        "'si praescivit, necessario futurum erat' 0 hits (replaced with the "
        "transmitted sentence at III.2.4); 'mea voluntate futurum' / 'non "
        "voluntate futurum' 0 hits (removed, not re-sourced); the memory "
        "analogy was an altered quotation (restored verbatim from III.4.11, "
        "which is its real locus). No Latin was composed."
    ),
}
