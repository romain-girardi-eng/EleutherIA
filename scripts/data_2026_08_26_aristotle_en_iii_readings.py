#!/usr/bin/env python3
"""WHAT: two Aristotle passage nodes store Greek that no edition prints.

Companion to ``apply_2026_08_26_aristotle_en_iii_readings.py``.

Both nodes name **Bywater (OCT)** as their edition and carry a French
translation attributed to Girardi and stamped ``VERIFIED``. Neither Greek
string exists. In both the substance is right and the syntax has been
re-fronted — a genuine Aristotelian clause with a rewritten opening, which is
the most dangerous shape a fabrication can take, because everything around it
checks out.

Found only because the zero-fabrication gate was extended to passage nodes; it
had never inspected one. Four nodes in the graph carry that translator block,
all four failed the corpus check, and each was then checked individually
against TLG E: two are genuine (``…en_iii_1_1110a4``, ``…plato_timaeus_28a``)
and are left untouched. These are the other two.

──────────────────────────────────────────────────────────────────────────────
1. passage_aristotle_en_iii_1_1111a22
──────────────────────────────────────────────────────────────────────────────
stored:     δοκεῖ δὴ ἑκούσιον εἶναι οὗ ἡ ἀρχὴ ἐν αὐτῷ εἰδότι τὰ καθ' ἕκαστα
            ἐν οἷς ἡ πρᾶξις.
            -> 0 hits in TLG0086

attested:   τὸ ἑκούσιον δόξειεν ἂν εἶναι οὗ ἡ ἀρχὴ ἐν αὐτῷ εἰδότι τὰ καθ'
            ἕκαστα ἐν οἷς ἡ πρᾶξις.
            -> TLG0086 @byte 1351441, in the sentence "Ὄντος δ' ἀκουσίου τοῦ
               βίᾳ καὶ δι' ἄγνοιαν, τὸ ἑκούσιον δόξειεν ἂν εἶναι …"

The tail is verbatim; `τὸ ἑκούσιον δόξειεν ἂν εἶναι` was replaced by
`δοκεῖ δὴ ἑκούσιον εἶναι`.

──────────────────────────────────────────────────────────────────────────────
2. passage_aristotle_en_iii_3_1112b11
──────────────────────────────────────────────────────────────────────────────
stored:     δοκεῖ δ' ἀρχὴ ὁ ἄνθρωπος εἶναι τῶν πράξεων.
            -> 0 hits in TLG0086, and 0 for the distinctive word order
               `ἀρχὴ ὁ ἄνθρωπος εἶναι τῶν πράξεων`

attested:   ἔοικε δή, καθάπερ εἴρηται, ἄνθρωπος εἶναι ἀρχὴ τῶν πράξεων
            -> TLG0086 @byte 1359161

`ἔοικε δή, καθάπερ εἴρηται,` was replaced by `δοκεῖ δ'` and ἀρχή/ἄνθρωπος
were transposed.

The French already in the node — "L'homme semble donc être principe de ses
actes" — renders `ἔοικε` ("semble"), which the stored Greek does not contain.
The translation appears to have been made from the real line and the Greek
back-generated to match it.

──────────────────────────────────────────────────────────────────────────────
What this script does NOT do
──────────────────────────────────────────────────────────────────────────────
The Bekker reference on node 2 says 1112b11-12, while the attested sentence
sits later in the chapter. Correcting a Bekker number is an editorial decision
about which line the node is meant to carry, and inferring it from proximity is
the same reasoning-backwards that produced the defect. The reference is left
alone and flagged in metadata for a human to settle.

Nothing here is composed: both replacement strings are copied from a printed
TLG E hit whose byte offset is recorded above.
"""

from __future__ import annotations

TLG_AUTHOR = "0086"

REPAIRS = [
    {
        "node_id": "passage_aristotle_en_iii_1_1111a22",
        "stored": (
            "δοκεῖ δὴ ἑκούσιον εἶναι οὗ ἡ ἀρχὴ ἐν αὐτῷ εἰδότι "
            "τὰ καθ' ἕκαστα ἐν οἷς ἡ πρᾶξις."
        ),
        "attested": (
            "τὸ ἑκούσιον δόξειεν ἂν εἶναι οὗ ἡ ἀρχὴ ἐν αὐτῷ εἰδότι "
            "τὰ καθ' ἕκαστα ἐν οἷς ἡ πρᾶξις."
        ),
        "attestation": "TLG0086 @byte 1351441 (Aristotle, EN III.1)",
        "bekker_ok": True,
    },
    {
        "node_id": "passage_aristotle_en_iii_3_1112b11",
        "stored": "δοκεῖ δ' ἀρχὴ ὁ ἄνθρωπος εἶναι τῶν πράξεων.",
        "attested": "ἔοικε δή, καθάπερ εἴρηται, ἄνθρωπος εἶναι ἀρχὴ τῶν πράξεων·",
        "attestation": "TLG0086 @byte 1359161 (Aristotle, EN III.3)",
        "bekker_ok": False,
    },
]

# Verified genuine in the same cohort — recorded so nobody re-opens them.
LEFT_ALONE = {
    "passage_aristotle_en_iii_1_1110a4": "attested, TLG0086 @byte 1345556",
    "passage_plato_timaeus_28a": "attested, TLG0059 @byte 3213126",
}

METADATA_STAMP = "greek_reading_repair_2026_08_26"

BEKKER_FLAG = (
    "Bekker reference NOT verified. The stored Greek was unattested and has "
    "been replaced with the transmitted text (see greek_reading_repair note); "
    "the attested sentence does not sit at the line number this node claims. "
    "Which line the node is meant to carry is an editorial decision — do not "
    "infer it from proximity."
)
