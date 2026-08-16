#!/usr/bin/env python3
"""Data for ``apply_2026_08_17_factual_corrections.py`` (wave 4).

Wave 3 split the twelve conflated ``work`` nodes. Splitting them exposed a second
layer of defects that the conflation had been masking: passages inherited the
*host* work's author, so 190 passages were attributed to the wrong ancient
author. This wave fixes those, plus the reversed influence edges, the
unresolvable CTS URNs and the period-vocabulary drift.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Reversed `influences` edges.
#
# The ontology defines `influences` as "source intellectually influences target",
# i.e. the source is the EARLIER thinker. Checked against the dates embedded in
# the node ids, 22 person->person `influences` edges run early->late and these 11
# run late->early: they assert that a later thinker influenced an earlier one.
#
# Each is corrected by changing the predicate to its declared inverse,
# `influenced_by`, which keeps the same pair and the same arrow and simply states
# the relation the right way round. No edge is deleted and no direction is
# guessed: in every case the target is the earlier figure by a wide margin.
REVERSED_INFLUENCES: list[tuple[str, str]] = [
    (
        "554dc681-7aa2-4304-93e6-6975d357105d",
        "Boethius (c. 477-524) cannot influence Aristotle (384-322 BCE)",
    ),
    (
        "c8e828d9-2319-40cb-b0d1-ec321af7d0c6",
        "Boethius (c. 477-524) cannot influence Plato (428-348 BCE)",
    ),
    (
        "c6564f02-9573-448a-937d-3b757239fb2a",
        "Jansen (1585-1638) cannot influence Luther (1483-1546)",
    ),
    (
        "f7b87f27-a358-4f0a-bafc-139b6e645515",
        "Cyril of Alexandria (c. 376-444) cannot influence Irenaeus (d. c. 202)",
    ),
    (
        "1e810798-7e8c-469b-9d50-0a011d40ca8e",
        "Gersonides (1288-1344) cannot influence Averroes (1126-1198)",
    ),
    (
        "4cf28e24-7e38-407a-ab39-d246d7438928",
        "Calvin (1509-1564) cannot influence Augustine (354-430)",
    ),
    (
        "70d41955-64b5-48cb-a275-fa80e9c94715",
        "Edwards (1703-1758) cannot influence Augustine (354-430)",
    ),
    (
        "f3bf215b-0765-42a2-b1cc-e5a639a1a2a2",
        "Edwards (1703-1758) cannot influence Locke (1632-1704)",
    ),
    (
        "3e71849d-7a3f-4da4-b39d-653503bbf614",
        "Lucretius (c. 99-55 BCE) cannot influence Epicurus (341-270 BCE)",
    ),
    (
        "ca372454-1064-459f-82ed-1fc16e52dfa9",
        "Maimonides (1138-1204) cannot influence Avicenna (980-1037)",
    ),
    (
        "1c00ac85-3794-4e35-a509-0bcf93cc28e9",
        "Luther (1483-1546) cannot influence Augustine (354-430)",
    ),
]

# Two further chronology alerts were checked and are FALSE POSITIVES of the
# detector, not data errors; they are recorded here so a later pass does not
# "fix" them:
#   * Augustine -[critiques]-> Julian of Eclanum. Augustine (354-430) and Julian
#     (c. 386-c. 455) were contemporaries and the Contra Iulianum is real; the
#     alert came from comparing Augustine's birth with Julian's death.
#   * Irenaeus -[precedes]-> Bardaisan. Irenaeus (c. 130-202) does precede
#     Bardaisan (154-222); the alert came from a mis-parsed floruit.


# ---------------------------------------------------------------------------
# 2. Works that hold only passages belonging to another work.
#
# work_origen_exhortation_martyrdom carried the 51 passages of Clement's
# Protrepticus and nothing else — a title collision ("Exhortation"). All 51 are
# already `part_of work_clement_protrepticus`, so the edges to Origen's work are
# simply deleted. Origen's Exhortation to Martyrdom then has no text of its own,
# which is the truth: it was never ingested.
WHOLLY_FOREIGN_WORKS: dict[str, tuple[str, str]] = {
    "work_origen_exhortation_martyrdom": (
        "work_clement_protrepticus",
        "All 51 children are passage_clement_protr_* (Clement, Protrepticus, "
        "urn:cts:greekLit:tlg0555.tlg001 content) and are already parented to "
        "work_clement_protrepticus. Origen's Exhortation to Martyrdom has no ingested text.",
    ),
}


# ---------------------------------------------------------------------------
# 3. Passages attributed to the wrong ancient author.
#
# These passages sat inside a conflated host work and were wired to the HOST's
# author. Splitting the works in wave 3 exposed the mismatch. The correct author
# is the one named by the passage's own label and work_title.
#
# host-work key -> (wrong author node, right author node, right author string, why)
PASSAGE_AUTHOR_REPOINT: list[dict] = [
    {
        "work": "work_gregory_naz_oratio_27",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_gregory_nazianzus_d389",
        "author": "Gregory of Nazianzus",
        "why": "passages labelled 'Gregory of Nazianzus, Adversus Eunomianos (orat. 27)', tlg2022.tlg007",
    },
    {
        "work": "work_gregory_naz_oratio_28",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_gregory_nazianzus_d389",
        "author": "Gregory of Nazianzus",
        "why": "passages labelled 'Gregory of Nazianzus, De Theologia (Orat. 28)', tlg2022.tlg008",
    },
    {
        "work": "work_gregory_naz_oratio_29",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_gregory_nazianzus_d389",
        "author": "Gregory of Nazianzus",
        "why": "passages labelled 'Gregory of Nazianzus, De Filio (Orat. 29)', tlg2022.tlg009",
    },
    {
        "work": "work_gregory_naz_oratio_30",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_gregory_nazianzus_d389",
        "author": "Gregory of Nazianzus",
        "why": "passages labelled 'Gregory of Nazianzus, De Filio (Orat. 30)', tlg2022.tlg010",
    },
    {
        "work": "work_gregory_naz_oratio_31",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_gregory_nazianzus_d389",
        "author": "Gregory of Nazianzus",
        "why": "passages labelled 'Gregory of Nazianzus, De Spiritu Sancto (Orat. 31)', tlg2022.tlg011",
    },
    {
        "work": "work_evodius_de_fide_contra_manichaeos",
        "wrong": "person_augustine_hippo_d430",
        "right": "person_evodius_uzalis_d424",
        "author": "Evodius of Uzalis",
        "why": "passages labelled 'Evodius Bishop of Uzalis, De fide Contra Manicheos', cpl:evodius.de_fide",
    },
    {
        "work": "work_gellius_na_vii_2",
        "wrong": "person_diogenes_laertius_3c_ce",
        "right": "person_aulus_gellius_125_180ce",
        "author": "Aulus Gellius",
        "why": "passage labelled 'Aulus Gellius, Noctes Atticae, 7.2', urn:cts:latinLit:phi1254.phi001",
    },
    {
        "work": "work_plutarch_de_fato_complete",
        "wrong": "person_plutarch_45_120ce_b9c2a8f3",
        "right": "person_pseudo_plutarch_2c_ce",
        "author": "Pseudo-Plutarch",
        "why": (
            "De Fato is pseudonymous. The work node's own description records the reasoning: "
            "'The manuscripts attribute it to Plutarch of Chaeronea, but hiatus statistics and "
            "doctrinal divergence' place it outside the genuine corpus. The manuscript "
            "attribution is preserved in metadata.manuscript_attribution rather than asserted."
        ),
        "keep_ms_attribution": "Plutarch of Chaeronea (manuscript attribution)",
    },
]


# ---------------------------------------------------------------------------
# 4. CTS URNs containing a literal '?' placeholder.
#
# 445 passages carry e.g. `urn:cts:greekLit:tlg0059.tlg002.perseus-grc2:?.17a`.
# '?' is a reserved URI character, so these URNs are unresolvable. All 445 belong
# to Plato works cited by flat Stephanus pagination (Apology tlg002, Phaedo
# tlg004, Phaedrus tlg012), which have no book division: the canonical Perseus
# form is `…perseus-grc2:17a`. The fix removes the empty `?.` segment only; the
# Stephanus reference itself is untouched.
CTS_PLACEHOLDER_PREFIX = ":?."


# ---------------------------------------------------------------------------
# 5. Period vocabulary.
PERIOD_FIXES: dict[str, tuple[str, str, str]] = {
    "person_salles_ricardo_contemporary": (
        "Modern",
        "Contemporary",
        "birth_date is 'fl. 21st c.'; Ricardo Salles is a living scholar",
    ),
}
# Deliberately EMPTY. The first pass proposed normalising "Classical Greek" to
# "Classical" on the strength of CLAUDE.md's period list. Checked before applying:
# "Classical Greek" is carried by 2,089 nodes and is a coherent, established label,
# and the graph legitimately uses other values outside that list too ("Patristic"
# 1,361, "Second Temple Judaism" 29, "Cross-period" 11, "Rabbinic" 2). Renaming it
# would be a taxonomy decision, not a factual correction, so it is left to the
# maintainer and recorded as a recommendation instead.
PERIOD_VOCAB_FIXES: dict[str, str] = {}


# ---------------------------------------------------------------------------
# 6. Date fields holding the wrong kind of value.
DATE_FIELD_FIXES: list[dict] = [
    {
        "node": "person_celestius_d430s",
        "from_field": "birth_date",
        "to_field": "floruit",
        "value": "fl. early 5th c. CE",
        "why": "a floruit was stored in birth_date, making birth appear to fall after death (c. 430 CE)",
    },
]
