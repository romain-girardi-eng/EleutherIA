"""Alexander De Fato deep-anchor batch B1 — NEW_EDGES list.

Anchors 12 scholar arguments/syntheses/publications + 20 legacy
`scholarly_argument_*_alexander*` nodes to passage-level chapter nodes of
Alexander's De Fato.

Allowed relations per `knowledge graph/ontology/edge_types.json` (the subset
we use here) :

  cites_primary_source : src argument / publication / person -> tgt passage / work
  evidenced_by         : src argument / concept / group / school -> tgt passage
  interprets           : src argument / person / publication / modern_interpretation / work
                          -> tgt argument / argument_framework / concept / passage / person / school / work
  discusses            : src argument / argument_framework / concept / conceptual_evolution / debate /
                          passage / person / publication / synthesis / work
                          -> tgt argument / concept / debate / group / person / school / synthesis / work
  part_of              : src argument / concept / passage / synthesis / text_fragment / work
                          -> tgt concept / passage / work / source_collection

Synthesis-type nodes CANNOT use `cites_primary_source` (per ontology). They
use `part_of` (synthesis -> passage is allowed) or `discusses` (when the
target is a work or argument). For synthesis -> passage anchoring we use
`part_of` with metadata explaining the scholar's engagement.
"""
from __future__ import annotations

from typing import Any

from alexander_de_fato_deep_b1_utils import (
    ALEX_DE_FATO_WORK_ID,
    BRUNS_PAGES,
    cite_edge,
    passage,
)

# ----------------------------------------------------------------------------
# Stable IDs we reference repeatedly
# ----------------------------------------------------------------------------
PUB_SHARPLES_1983 = "pub_sharples_1983_alexander_fate"
PUB_FREDE_2011 = "pub_frede_2011_free_will"
PUB_AMAND_1945 = "pub_amand_1945_fatalisme"
PUB_DESTREE_2014 = "pub_destree_salles_zingano_2014_what_is_up_to_us"
PUB_FURST_2022 = "pub_furst_2022_wege_freiheit"
PUB_RAMELLI_2014 = "pub_ramelli_2014_alexander_origen"
PUB_KOCH_1932 = "pub_koch_1932_pronoia"
PUB_BOBZIEN_1998 = "pub_bobzien_1998_inadvertent"

ARG_FREDE_DEAD_END = "argument_frede_2011_alexander_libertarian_dead_end"
ARG_ZINGANO_LIAB = "argument_zingano_2014_alexander_liability_vs_possibility"
ARG_FURST_FIRST_FREEDOM = "argument_furst_2022_de_princ_iii_1_first_freedom_treatise"

SYNTH_AMAND_TRIPLE = "synthesis_amand1945_alexander_de_fato_triple_composition"
SYNTH_AMAND_N2 = "synthesis_amand1945_alexander_witness_n2_identification"
SYNTH_FREDE_CH6 = "synthesis_frede2011_ch6_platonist_peripatetic_criticisms"
SYNTH_DESTREE_CH13 = "synthesis_destree2014_ch13_zingano_alexander_character_action"
SYNTH_FURST_ALEX = "synthesis_furst2022_alexander_alternativenoffenheit"


NEW_EDGES: list[dict[str, Any]] = []


# ============================================================================
# 1. SHARPLES 1983 — critical edition + commentary on the entire treatise
# ============================================================================
# Publication-level: cites the whole work (already in KG, presumably) +
# anchor key chapters that Sharples's commentary highlights as load-bearing.
SHARPLES_KEY_CHAPTERS = {
    7:  "Bruns 171-172 — setup of opponents' theses (Sharples Comm. ad loc.)",
    11: "Bruns 176-178 — argument from deliberation (Sharples Comm. p. 137-140)",
    12: "Bruns 178-180 — definition of τὸ ἐφʼ ἡμῖν as kyrios over A and not-A",
    13: "Bruns 180-182 — chance / common preconceptions",
    14: "Bruns 182-184 — identification eph'hēmin = autexousion (Sharples Comm. p. 142-145)",
    15: "Bruns 184-186 — 'same circumstances, different outcomes' (192,22ff in older Bruns numbering refers to ch. XV-XX)",
    16: "Bruns 186-188 — refutation of Stoic preservation of eph'hēmin",
    19: "Bruns 191-192 — judgement and forgiveness require open alternatives",
    20: "Bruns 192-194 — agent as ἀρχή (Sharples Comm. p. 153-155)",
    22: "Bruns 195-196 — examination of Stoic doctrine of fate begins",
    26: "Bruns 201-203 — virtues and vices not inalienable",
    27: "Bruns 203-204 — habit (hexis) and virtue acquisition",
    28: "Bruns 204-205 — Stoic necessitarian inconsistency",
    29: "Bruns 205-207 — phronimos and character formation",
    30: "Bruns 207-209 — divine foreknowledge vs determinism",
    31: "Bruns 209-210 — divination utility argument",
    33: "Bruns 211-213 — Stoic horme defence",
    34: "Bruns 213-214 — Stoic self-refutation",
    37: "Bruns 217-218 — 'co-fated events' / Lazy Argument adjacent",
    38: "Bruns 218-220 — Stoic horme cycle revisited",
    39: "Bruns 220-221 — closing address to emperors",
}
for ch, note in SHARPLES_KEY_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_SHARPLES_1983, ch,
            relation="cites_primary_source",
            confidence=0.95,
            scholar="scholar_sharples_robert",
            publication=PUB_SHARPLES_1983,
            original_citation=f"Sharples 1983 Comm. on De Fato ch. {ch}",
            note=note,
        )
    )

# Sharples also INTERPRETS the work as a whole (publication -> work is allowed
# via `interprets`).
NEW_EDGES.append({
    "source": PUB_SHARPLES_1983,
    "target": ALEX_DE_FATO_WORK_ID,
    "relation": "interprets",
    "confidence": 0.99,
    "metadata": {
        "scholar": "scholar_sharples_robert",
        "note": "Standard critical edition + commentary; transforms Alexander from a neglected figure into a central topic of scholarship on ancient determinism",
        "bibtex_key": "sharples-1983-alexander-of-aphrodisias-on-fate",
    },
})


# ============================================================================
# 2. AMAND 1945 — Livre I Ch. V on Alexander's De Fato
# ============================================================================
# Amand's "triple composition" thesis covers the whole work, but the WITNESS N°2
# argument identifies De Fato 16-20 (five chapters) as the rigorous Carnéadean
# dossier. Syntheses -> passages use `part_of` (allowed); pubs -> passages use
# `cites_primary_source`.

# 2a. Publication-level : Amand 1945 cites the De Fato chapters of interest.
AMAND_KEY_CHAPTERS = {
    11: "Livre I Ch. V — argument from bouleuesthai noted in triple-composition analysis",
    12: "Livre I Ch. V — τὸ ἐφʼ ἡμῖν definition",
    14: "Livre I Ch. V — autexousion identification",
    15: "Livre I Ch. V — 192,22ff Carnéadean argument",
    16: "Livre I Ch. V §III.1, p. 143-145 — début du témoin n°2",
    17: "Livre I Ch. V §III.1 — témoin n°2 §2 (providence)",
    18: "Livre I Ch. V §III.1 — témoin n°2 §3 (Stoic auto-contradiction)",
    19: "Livre I Ch. V §III.1 — témoin n°2 §4 (justice)",
    20: "Livre I Ch. V §III.1 — fin du témoin n°2 (agent comme ἀρχή)",
    22: "Livre I Ch. V §II.2 — examen direct des œuvres de Chrysippe",
    25: "Livre I Ch. V §II.2 — passages chrysippéens conservés",
}
for ch, note in AMAND_KEY_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_AMAND_1945, ch,
            relation="cites_primary_source",
            confidence=0.92,
            scholar="scholar_amand_de_mendieta_e",
            publication=PUB_AMAND_1945,
            original_citation="Amand 1945, Livre I Ch. V",
            note=note,
        )
    )

# 2b. Synthesis "triple composition" anchored to Bruns chapters cited by Amand
TRIPLE_COMPO_CHAPTERS = [11, 12, 14, 15, 16, 17, 18, 19, 20, 22, 25]
for ch in TRIPLE_COMPO_CHAPTERS:
    NEW_EDGES.append({
        "source": SYNTH_AMAND_TRIPLE,
        "target": passage(ch),
        "relation": "part_of",
        "confidence": 0.85,
        "metadata": {
            "alex_de_fato_chapter": ch,
            "alex_de_fato_bruns_pages": BRUNS_PAGES[ch],
            "scholar": "scholar_amand_de_mendieta_e",
            "publication": PUB_AMAND_1945,
            "note": "Synthesis of Amand's three-fold composition thesis (péripatétisme + Carnéade via Clitomaque + Chrysippe direct) — anchored to chapters cited in Livre I Ch. V",
        },
    })

# 2c. Synthesis "témoin n°2" anchored strictly to De Fato 16-20
WITNESS_N2_CHAPTERS = [16, 17, 18, 19, 20]
for ch in WITNESS_N2_CHAPTERS:
    NEW_EDGES.append({
        "source": SYNTH_AMAND_N2,
        "target": passage(ch),
        "relation": "part_of",
        "confidence": 0.95,
        "metadata": {
            "alex_de_fato_chapter": ch,
            "alex_de_fato_bruns_pages": BRUNS_PAGES[ch],
            "scholar": "scholar_amand_de_mendieta_e",
            "publication": PUB_AMAND_1945,
            "note": "Amand 1945 témoin n°2 = De Fato 16-20 (cinq chapitres) = dossier carnéadien le plus rigoureux des six témoins (p. 144)",
            "amand_witness_n2_identification": True,
        },
    })


# ============================================================================
# 3. FREDE 2011 — Ch. 6 on Alexander
# ============================================================================
# Frede 2011 cites by Roman numerals : XI, XIV, XXVIII, XXXVIII + the famous
# "192,22ff" formulation (Bruns p. 192). The latter maps to De Fato ch. XV
# (the prohairesis-and-same-circumstances argument).

# 3a. Publication-level anchors (Frede's explicit chapter list)
FREDE_KEY_CHAPTERS = {
    11: "Frede 2011 Ch. 6 — 'De fato XI' cited (deliberation argument)",
    12: "Frede 2011 Ch. 6 — kyrios over A and not-A (background to XIV)",
    14: "Frede 2011 Ch. 6 — 'De fato XIV' cited (eph'hēmin = autexousion)",
    15: "Frede 2011 Ch. 6, p. 100 + Conclusion p. 177-178 — '192,22ff' = the libertarian-dead-end formulation",
    20: "Frede 2011 Ch. 6 — agent as archē, end of antifatalist sequence",
    28: "Frede 2011 Ch. 6 — 'De fato XXVIII' cited (Stoic necessitarian inconsistency)",
    38: "Frede 2011 Ch. 6 — 'De fato XXXVIII' cited (Stoic horme cycle)",
}
for ch, note in FREDE_KEY_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_FREDE_2011, ch,
            relation="cites_primary_source",
            confidence=0.95,
            scholar="scholar_frede_michael",
            publication=PUB_FREDE_2011,
            original_citation=f"Frede 2011 Ch. 6, cit. 'De fato {['?','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI','XXII','XXIII','XXIV','XXV','XXVI','XXVII','XXVIII','XXIX','XXX','XXXI','XXXII','XXXIII','XXXIV','XXXV','XXXVI','XXXVII','XXXVIII','XXXIX'][ch]}'",
            note=note,
        )
    )

# 3b. Frede's flagship argument 'libertarian dead end' -> the specific
# 192,22ff passage (= De Fato ch. XV) — flagship anchor.
NEW_EDGES.append(
    cite_edge(
        ARG_FREDE_DEAD_END, 15,
        relation="cites_primary_source",
        confidence=0.98,
        scholar="scholar_frede_michael",
        publication=PUB_FREDE_2011,
        original_citation="Frede 2011 p. 100 + Conclusion p. 177-178 — Alexander 'De fato 192, 22ff'",
        note="THE locus classicus for Frede's 'Alexander = ancestor of the modern voluntarist notion attacked by Ryle and Williams' thesis",
    )
)
for ch in (11, 14, 20):
    NEW_EDGES.append(
        cite_edge(
            ARG_FREDE_DEAD_END, ch,
            relation="cites_primary_source",
            confidence=0.9,
            scholar="scholar_frede_michael",
            publication=PUB_FREDE_2011,
            original_citation=f"Frede 2011 Ch. 6 — De fato ch. {ch} as part of the libertarian-dead-end dossier",
        )
    )

# 3c. Frede synthesis Ch. 6 anchored to the chapters analysed
FREDE_CH6_ANCHOR_CHAPTERS = [11, 14, 15, 20, 28, 38]
for ch in FREDE_CH6_ANCHOR_CHAPTERS:
    NEW_EDGES.append({
        "source": SYNTH_FREDE_CH6,
        "target": passage(ch),
        "relation": "part_of",
        "confidence": 0.9,
        "metadata": {
            "alex_de_fato_chapter": ch,
            "alex_de_fato_bruns_pages": BRUNS_PAGES[ch],
            "scholar": "scholar_frede_michael",
            "publication": PUB_FREDE_2011,
            "note": "Frede 2011 Ch. 6 synthesis - chapter anchor",
        },
    })


# ============================================================================
# 4. DESTRÉE / SALLES / ZINGANO 2014 — ch. 13 Zingano on Alexander
# ============================================================================
# Zingano (Destrée 2014 ch. 13, p. 245-263) focuses on De Fato §§ 26-29.

# 4a. Publication-level (whole volume) anchors the four chapters Zingano studies
DESTREE_2014_CHAPTERS = {
    26: "Destrée/Salles/Zingano 2014, ch. 13 (Zingano), p. 245-263 — De fato § 26",
    27: "Destrée/Salles/Zingano 2014, ch. 13 (Zingano) — De fato § 27 (hexis)",
    28: "Destrée/Salles/Zingano 2014, ch. 13 (Zingano) — De fato § 28 (Stoic inconsistency)",
    29: "Destrée/Salles/Zingano 2014, ch. 13 (Zingano) — De fato § 29 (phronimos)",
}
for ch, note in DESTREE_2014_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_DESTREE_2014, ch,
            relation="cites_primary_source",
            confidence=0.95,
            scholar="scholar_zingano_marco",
            publication=PUB_DESTREE_2014,
            original_citation="Destrée/Salles/Zingano 2014 ch. 13, p. 245-263",
            note=note,
        )
    )

# 4b. Zingano's specific argument on liability vs possibility
ZINGANO_ARG_CHAPTERS = {
    26: "Zingano 2014 — entry point of the §§ 26-29 analysis",
    27: "Zingano 2014 — hexis acquisition by 'could have done otherwise' (strong sense)",
    28: "Zingano 2014 — distinction liability vs possibility introduced",
    29: "Zingano 2014 — phronimos case: 'cannot do contraries in strong sense'",
}
for ch, note in ZINGANO_ARG_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            ARG_ZINGANO_LIAB, ch,
            relation="cites_primary_source",
            confidence=0.97,
            scholar="scholar_zingano_marco",
            publication=PUB_DESTREE_2014,
            original_citation=f"Zingano in Destrée 2014, p. 245-263 — De fato § {ch}",
            note=note,
        )
    )

# 4c. Destrée synthesis ch. 13 anchored to §§ 26-29
for ch in [26, 27, 28, 29]:
    NEW_EDGES.append({
        "source": SYNTH_DESTREE_CH13,
        "target": passage(ch),
        "relation": "part_of",
        "confidence": 0.9,
        "metadata": {
            "alex_de_fato_chapter": ch,
            "alex_de_fato_bruns_pages": BRUNS_PAGES[ch],
            "scholar": "scholar_zingano_marco",
            "publication": PUB_DESTREE_2014,
            "note": "Zingano in Destrée 2014 ch. 13 - synthesis anchor for §§ 26-29",
        },
    })


# ============================================================================
# 5. FÜRST 2022 — Kap. III §3c on Alexander
# ============================================================================
# Fürst's argument: Alexander demands open alternatives (Alternativenoffenheit).
# Standard argument repeated: determinism abolishes praise/blame/punishment/reward.
# Cited chapters: the 'common notions' antifatalist series (16-20) + praise-blame (26-29).

FURST_KEY_CHAPTERS = {
    11: "Fürst 2022, Kap. III §3c, p. 132-138 — argument from deliberation",
    12: "Fürst 2022, Kap. III §3c — definition of eph'hēmin",
    14: "Fürst 2022, Kap. III §3c — autexousion identification",
    15: "Fürst 2022, Kap. III §3c — Alternativenoffenheit demanded",
    19: "Fürst 2022, Kap. III §3c — judges treat agents as responsible",
    20: "Fürst 2022, Kap. III §3c — agent as archē",
    26: "Fürst 2022, Kap. III §3c — 'das Determinismus-Argument' (Lob/Tadel)",
    27: "Fürst 2022, Kap. III §3c — virtues require prior power",
    28: "Fürst 2022, Kap. III §3c — Stoic inconsistency on virtue",
}
for ch, note in FURST_KEY_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_FURST_2022, ch,
            relation="cites_primary_source",
            confidence=0.92,
            scholar="scholar_furst_alfons",
            publication=PUB_FURST_2022,
            original_citation="Fürst 2022, Kap. III §3c, p. 132-138",
            note=note,
        )
    )

# Fürst Alexander synthesis -> the same anchoring chapters
FURST_ALEX_SYNTH_CHAPTERS = [11, 12, 14, 15, 19, 20, 26, 27, 28]
for ch in FURST_ALEX_SYNTH_CHAPTERS:
    NEW_EDGES.append({
        "source": SYNTH_FURST_ALEX,
        "target": passage(ch),
        "relation": "part_of",
        "confidence": 0.9,
        "metadata": {
            "alex_de_fato_chapter": ch,
            "alex_de_fato_bruns_pages": BRUNS_PAGES[ch],
            "scholar": "scholar_furst_alfons",
            "publication": PUB_FURST_2022,
            "note": "Fürst 2022 Kap. III §3c - Alternativenoffenheit synthesis anchor",
        },
    })

# Fürst's "De Princ. III 1 = first treatise on freedom" argument :
# Alexander is the *precursor* with the title "Περὶ εἱμαρμένης". Anchor the
# argument on Alexander's chapter 1 (which addresses Severus + Caracalla and
# announces the topic by name) + chapter 39 (the closing programmatic
# statement on 'fate and what depends on us').
for ch, note in [
    (1, "Fürst 2022 Kap. V §2, p. 196-197 — Alexander's title Περὶ εἱμαρμένης is the precursor that Origen renames"),
    (39, "Fürst 2022 Kap. V §2 — closing programmatic statement on εἱμαρμένη + τὸ ἐφʼ ἡμῖν"),
]:
    NEW_EDGES.append(
        cite_edge(
            ARG_FURST_FIRST_FREEDOM, ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_furst_alfons",
            publication=PUB_FURST_2022,
            original_citation="Fürst 2022 Kap. V §2, p. 196-197",
            note=note,
        )
    )


# ============================================================================
# 6. RAMELLI 2014 — Alexander as source for Origen
# ============================================================================
# Targets the same anti-determinist arguments Origen reuses.
RAMELLI_CHAPTERS = {
    11: "Ramelli 2014 — argument from deliberation reused by Origen",
    12: "Ramelli 2014 — eph'hēmin definition parallels Origen Princ. III.1",
    14: "Ramelli 2014 — autexousion = source for Origen's αὐτεξούσιον",
    15: "Ramelli 2014 — open alternatives in De Princ. III.1.6",
    26: "Ramelli 2014 — praise/blame argument parallels Origen Princ. III.1.7",
}
for ch, note in RAMELLI_CHAPTERS.items():
    NEW_EDGES.append(
        cite_edge(
            PUB_RAMELLI_2014, ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_ramelli_ilaria",
            publication=PUB_RAMELLI_2014,
            original_citation="Ramelli 2014 (Alexander and Origen)",
            note=note,
        )
    )


# ============================================================================
# 7. LEGACY scholarly_argument_*_alexander* nodes
# ============================================================================
# Twenty legacy nodes from earlier ingestion phases — anchored to the chapters
# their content actually engages.

# 7a. Bobzien 'as first evidence for free-will problem' — anchors on the
# 'libertarian' formulations (XV) + the deliberation argument (XI).
for nid in (
    "scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_3",
    "scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_4",
):
    for ch in (11, 12, 14, 15, 20):
        NEW_EDGES.append(
            cite_edge(
                nid, ch,
                relation="cites_primary_source",
                confidence=0.85,
                scholar="person_bobzien_susanne_contemporary",
                publication=PUB_BOBZIEN_1998,
                original_citation="Bobzien 1998 — Determinism and Freedom in Stoic Philosophy, ch. 6 on Alexander",
                note=f"Bobzien's argument that Alexander provides 'earliest unambiguous evidence' anchors on De fato ch. {ch}",
            )
        )

# 7b. Eliasson on eph' hēmin
for ch in (11, 12, 14, 15):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_eliasson_alexander_of_aphrodisias_on_2", ch,
            relation="cites_primary_source",
            confidence=0.8,
            scholar="scholar_eliasson_erik",
            original_citation="Eliasson on Alexander's distinctive notion of τὸ ἐφʼ ἡμῖν",
            note="Eliasson's 'distinctive notion' thesis maps onto Alexander's central definition chapters",
        )
    )

# 7c. Frede on target / method (Stoic critique)
for nid in (
    "scholarly_argument_frede_alexander_of_aphrodisias_targe_1",
    "scholarly_argument_frede_alexander_s_critique_of_stoic__2",
):
    for ch in (7, 16, 22, 33, 34, 38):
        NEW_EDGES.append(
            cite_edge(
                nid, ch,
                relation="cites_primary_source",
                confidence=0.8,
                scholar="scholar_frede_michael",
                publication=PUB_FREDE_2011,
                original_citation="Frede on Alexander's target and reductio method",
                note=f"Frede's analysis of Alexander's anti-Stoic strategy at De fato ch. {ch}",
            )
        )

# 7d. Frede on Alexander's treatment of fate (efficient cause identification)
# These cite the early-chapter causal taxonomy (3-6) + the identification of
# fate with nature at Bruns 169,18 (= ch. 6).
for nid in (
    "scholarly_argument_frede_alexander_of_aphrodisias_treat_1",
    "scholarly_argument_frede_alexander_s_identification_of__2",
    "scholarly_argument_frede_alexander_s_shift_to_efficient_4",
):
    for ch in (3, 4, 5, 6, 7):
        NEW_EDGES.append(
            cite_edge(
                nid, ch,
                relation="cites_primary_source",
                confidence=0.85,
                scholar="scholar_frede_michael",
                publication=PUB_FREDE_2011,
                original_citation="Frede — Alexander identifies fate with nature, restricts it to the efficient cause (Bruns 169.18ff)",
                note=f"De fato ch. {ch} contains the four-cause taxonomy and the fate-as-nature identification",
            )
        )

# 7e. Guyomarc'h family — uses chapters across the work
for ch in (1, 2, 3, 39):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_alexander_of_aphrodisias_de_fa_0", ch,
            relation="cites_primary_source",
            confidence=0.7,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h 2008 — global appreciation of De fato",
            note="Guyomarc'h's overall evaluation of the treatise's philosophical success",
        )
    )

# Aristotelian sources (texts cited by Alexander himself — Magna Moralia, etc.)
for ch in (3, 4, 5, 6):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_alexander_s_aristotelian_sourc_5", ch,
            relation="cites_primary_source",
            confidence=0.75,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h on Alexander's Aristotelian sources for contingency analysis",
            note="The four-cause taxonomy chapters where Alexander mobilises (pseudo-)Aristotelian doctrine",
        )
    )

# τὸ ἐφʼ ἡμῖν definition through δύναμις τῶν ἐναντίων
for ch in (11, 12, 14, 15, 20):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_alexander_s_conception_of_what_2", ch,
            relation="cites_primary_source",
            confidence=0.9,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h on Alexander's δύναμις τῶν ἐναντίων",
            note=f"Indeterminist power-of-opposites formulated at De fato ch. {ch}",
        )
    )

# Rhetorical strategy / political caution — anchor on prooemium (ch.1) and Stoic-attack chapters
for ch in (1, 7, 16, 22, 33):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_alexander_s_rhetorical_strateg_6", ch,
            relation="cites_primary_source",
            confidence=0.75,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h on Alexander's rhetorical strategy of anonymising contemporary Stoics",
            note=f"De fato ch. {ch} — anonymous polemic against unnamed Stoic targets",
        )
    )

# Stoic-determinism target
for ch in (7, 16, 22, 33, 34, 35, 36, 37):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_alexander_s_target_stoic_deter_1", ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h on Alexander's reconstructed Stoic target",
            note=f"De fato ch. {ch} — Alexander's polemical reconstruction of Stoic doctrine",
        )
    )

# Necessity vs fate (Stoic distinction critiqued)
for ch in (22, 23, 24, 25):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_guyomarc_h_necessity_and_fate_alexander_s_3", ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_guyomarc_h_gweltaz",
            original_citation="Guyomarc'h on Alexander's critique of Stoic fate-vs-necessity distinction",
            note=f"De fato ch. {ch} — exposition + critique of Stoic distinction",
        )
    )

# 7f. Hall on eph' hēmin and divine foreknowledge
for ch in (12, 14, 30):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_hall_alexander_of_aphrodisias_on_ep_3", ch,
            relation="cites_primary_source",
            confidence=0.8,
            scholar="scholar_hall_robert_g",
            original_citation="Hall on Alexander's eph'hēmin + divine probabilistic foreknowledge",
            note=f"De fato ch. {ch} — eph'hēmin definition or divine-foreknowledge argument",
        )
    )

# 7g. Koch 1932 — Alexander's doxographic method
for ch in (1, 2, 3, 7, 39):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_koch_alexander_of_aphrodisias_s_met_0", ch,
            relation="cites_primary_source",
            confidence=0.75,
            scholar="person_koch_hal",
            publication=PUB_KOCH_1932,
            original_citation="Koch 1932 — Alexander's doxographic dissensus method",
            note=f"De fato ch. {ch} — doxographic framing / methodological chapters",
        )
    )

# 7h. Ramelli — already covered above by PUB_RAMELLI_2014; also anchor legacy
# argument nodes.
for ch in (11, 12, 14, 15, 26):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_ramelli_alexander_of_aphrodisias_as_so_0", ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_ramelli_ilaria",
            publication=PUB_RAMELLI_2014,
            original_citation="Ramelli 2014 — Alexander as philosophical source for Origen",
            note=f"De fato ch. {ch} — anti-determinist argument paralleled in Origen Princ. III.1",
        )
    )

for ch in (12, 14, 16, 22):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_ramelli_alexander_s_concept_of_to_eph__5", ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_ramelli_ilaria",
            publication=PUB_RAMELLI_2014,
            original_citation="Ramelli on Alexander's critique of Stoic compatibilism re: τὸ ἐφʼ ἡμῖν",
            note=f"De fato ch. {ch} — eph'hēmin against Stoic compatibilism",
        )
    )

# 7i. Sharples (legacy nodes) — providence + scholarship survey
for ch in (4, 5, 6, 17, 30, 31):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_sharples_alexander_of_aphrodisias_on_pr_2", ch,
            relation="cites_primary_source",
            confidence=0.85,
            scholar="scholar_sharples_robert",
            publication=PUB_SHARPLES_1983,
            original_citation="Sharples 1983 (commentary) + Sharples on Alexander's providence ['position D']",
            note=f"De fato ch. {ch} — providence/fate causal economy",
        )
    )

# Sharples on scholarship history (anchor on the dedicatory ch.1 + closing ch.39 + central XV)
for ch in (1, 15, 39):
    NEW_EDGES.append(
        cite_edge(
            "scholarly_argument_sharples_alexander_of_aphrodisias_schol_2", ch,
            relation="cites_primary_source",
            confidence=0.7,
            scholar="scholar_sharples_robert",
            publication=PUB_SHARPLES_1983,
            original_citation="Sharples — history of the determinism problem culminating with Alexander's De fato",
            note=f"De fato ch. {ch} — dedicatory / programmatic statement of the problem",
        )
    )


# ============================================================================
# 8. Alexander as person/work — top-level scholar interpretive edges (work-level)
# ============================================================================
# These are *complement* to the passage-level edges, declaring scholar
# interpretations of the work as a whole. Person->work via `interprets`.
NEW_EDGES.extend([
    {
        "source": "scholar_sharples_robert",
        "target": ALEX_DE_FATO_WORK_ID,
        "relation": "interprets",
        "confidence": 0.99,
        "metadata": {
            "note": "Standard critical edition + commentary 1983; via media reading between Stoic determinism and Epicurean anti-providentialism",
        },
    },
    {
        "source": "scholar_frede_michael",
        "target": ALEX_DE_FATO_WORK_ID,
        "relation": "interprets",
        "confidence": 0.97,
        "metadata": {
            "note": "Frede 2011 Ch. 6 — Alexander = 'libertarian dead end' / ancestor of modern voluntarism",
        },
    },
    {
        "source": "scholar_zingano_marco",
        "target": ALEX_DE_FATO_WORK_ID,
        "relation": "interprets",
        "confidence": 0.95,
        "metadata": {
            "note": "Zingano in Destrée 2014 ch. 13 — libertarianism on character formation compatible with psychological determinism for the phronimos",
        },
    },
    {
        "source": "scholar_furst_alfons",
        "target": ALEX_DE_FATO_WORK_ID,
        "relation": "interprets",
        "confidence": 0.95,
        "metadata": {
            "note": "Fürst 2022 Kap. III §3c — Alexander requires Alternativenoffenheit; Origen will inherit this in Princ. III 1",
        },
    },
    {
        "source": "scholar_amand_de_mendieta_e",
        "target": ALEX_DE_FATO_WORK_ID,
        "relation": "interprets",
        "confidence": 0.97,
        "metadata": {
            "note": "Amand 1945 Livre I Ch. V — three-fold composition (Peripatetic tradition + Carnéade via Clitomaque + direct Chrysippean reading); De fato 16-20 = témoin n°2 (Carnéade)",
        },
    },
])
