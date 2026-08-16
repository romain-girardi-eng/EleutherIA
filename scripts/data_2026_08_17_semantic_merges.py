#!/usr/bin/env python3
"""Evidence for the 2026-08-17 semantic-merge wave.

This module holds *decisions*, never code. Each entry names the two (or more)
nodes, the survivor, and the reason the pair is a **factual** duplicate — the
same thesis from the same source, or the same text under two ids. Pairs that
merely *look* alike are recorded in ``REJECTED`` with the evidence that keeps
them apart. A scholarly disagreement is never resolved by a merge.

Sources of the findings:
  - ``data/audit/2026-08-16_deep_audit_semantic.jsonl``   (DAS-0xx)
  - ``data/audit/2026-08-16_deep_audit_structural.jsonl``
  - re-verification against the live graph on 2026-08-17 (state has moved:
    five of the twenty-two publication pairs were already merged by earlier waves)
  - for lot 5, the printed book: David Amand (Amand de Mendieta), *Fatalisme et
    liberté dans l'antiquité grecque*, Louvain 1945 (repr. Hakkert, Amsterdam
    1973), read on disk at
    ``~/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/01_Philosophie_antique/``

Applied by ``scripts/apply_2026_08_17_semantic_merges.py``.
"""

from __future__ import annotations

STAMP = "semantic_merges_2026_08_17"
NOW = "2026-08-17 00:00:00+00:00"

# ---------------------------------------------------------------------------
# Ontology (lot 6a) — the single write outside data/kg/ authorised by this wave
# ---------------------------------------------------------------------------
# Symmetry is expressed in this ontology by ``inverse == <self>`` (cf.
# related_to, contrasts_with, parallel_to, contemporary_of, engages_with).
# Category "semantic" is the one used by every "these two nodes say the same
# kind of thing" relation. Only ONE direction is ever stored, as for the other
# symmetric relations (the semantic layer materialises the inverse).
SAME_THESIS_AS = {
    "name": "same_thesis_as",
    "after": "parallel_to",  # inserted next to its semantic siblings
    "definition": {
        "description": (
            "Source and target carry the same scholarly thesis at different "
            "granularity or in different namespaces (chapter synthesis vs "
            "pinpoint argument vs concept shell). Symmetric; stored one way "
            "only. Not a merge: the nodes remain distinct because they are not "
            "interchangeable."
        ),
        "category": "semantic",
        "inverse": "same_thesis_as",
        "source_types": ["argument", "concept", "position", "synthesis"],
        "target_types": ["argument", "concept", "position", "synthesis"],
        "status": "active",
    },
    "version_bump": ("3.0.0", "3.1.0"),
}

# ---------------------------------------------------------------------------
# LOT 1 — Destrée / Salles / Zingano 2014: one chapter, two nodes
# ---------------------------------------------------------------------------
# Both families were created in the SAME ingestion pass (created_at
# 2026-05-16 15:40:14.179759 on every node of both families). For each of the
# 22 chapters the volume holds exactly one ``synthesis_destree2014_chNN_*``
# ("Summary of ch. N (Author, p. a-b): …") and exactly one
# ``argument_<author>_2014_*`` ("<Author>'s scholarly argument (Destrée 2014
# ch. N …)"). Same chapter, same thesis, two node types.
#
# Survivor = the ``argument_*`` node in every case: the synthesis family has
# ZERO inbound edges graph-wide and carries only ``discusses`` + ``authored_by``,
# while the argument family carries the dialectical wiring (responds_to,
# supports, critiques), ``cites_primary_source`` and ``advanced_in``.
#
# The audit reported 19 pairs; re-verification finds 22 (the heuristic missed
# frede_d, sauve_meyer and frede_michael, whose slugs are two tokens long).
# ``synthesis_destree2014_introduction_overview`` has no twin and is kept.
#
# page_range: the synthesis descriptions state a chapter page range. For
# ch02–ch15 the ranges form a perfectly contiguous chain (38→39, 58→59, 74→75,
# 90→91, 106→107, 120→121, 140→141, 150→151, 168→169, 182→183, 198→199,
# 220→221, 234→235) and two are independently corroborated by scholar metadata
# (Destrée p. 25-38 = ch02; Zingano p. 199-220 = ch13): those are written to the
# survivor. ch01 overlaps ch02 (7-30 vs 25-38) and ch16–ch22 are mutually
# contradictory (ch16 301-322 vs ch19 295-310 vs ch20 311-328): those are NOT
# written, only recorded as claimed + flagged needs_page_verification.
LOT1_PAGES_TRUSTED = {"ch02", "ch03", "ch04", "ch05", "ch06", "ch07", "ch08",
                      "ch09", "ch10", "ch11", "ch12", "ch13", "ch14", "ch15"}

# (synthesis_id, argument_id, chapter, page_range_claimed_by_the_synthesis)
LOT1_DESTREE_PAIRS = [
    ("synthesis_destree2014_ch01_johnson_democritus", "argument_johnson_2014_democritus_plasticity_intellectualism", "ch01", "7-30"),
    ("synthesis_destree2014_ch02_destree_plato_er", "argument_destree_2014_plato_er_asymmetry", "ch02", "25-38"),
    ("synthesis_destree2014_ch03_frede_d_aristotle_free_will", "argument_frede_d_2014_aristotle_psychological_determinism", "ch03", "39-58"),
    ("synthesis_destree2014_ch04_bobzien_aristotle_free_choice", "argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "ch04", "59-74"),
    ("synthesis_destree2014_ch05_sauve_meyer_aristotle_eph_hemin_contingent", "argument_sauve_meyer_2014_aristotle_two_sidedness_not_pap", "ch05", "75-90"),
    ("synthesis_destree2014_ch06_echenique_aristotle_double_position", "argument_echenique_2014_aristotle_double_position_appraisals_accountability", "ch06", "91-106"),
    ("synthesis_destree2014_ch07_vogt_stoic_action", "argument_vogt_2014_stoic_cyclic_assent_eph_hemin", "ch07", "107-120"),
    ("synthesis_destree2014_ch08_gomez_chrysippus_compatibilism", "argument_gomez_2014_chrysippus_reactive_compatibilism", "ch08", "121-140"),
    ("synthesis_destree2014_ch09_gourinat_in_nostra_potestate", "argument_gourinat_2014_in_nostra_potestate_not_eph_hemin", "ch09", "141-150"),
    ("synthesis_destree2014_ch10_vimercati_panaetius", "argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence", "ch10", "151-168"),
    ("synthesis_destree2014_ch11_salles_epictetus_causal", "argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus", "ch11", "169-182"),
    ("synthesis_destree2014_ch12_boeri_marcus_aurelius", "argument_boeri_2014_marcus_present_indifferents_eph_hemin", "ch12", "183-198"),
    ("synthesis_destree2014_ch13_zingano_alexander_character_action", "argument_zingano_2014_alexander_liability_vs_possibility", "ch13", "199-220"),
    ("synthesis_destree2014_ch14_morel_epicurus_primary_evidence", "argument_morel_2014_epicurean_eph_hemin_primary_evidence", "ch14", "221-234"),
    ("synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius", "argument_maso_2014_cicero_motus_animi_voluntarius_independence", "ch15", "235-249"),
    ("synthesis_destree2014_ch16_gerson_plotinus_strawson", "argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson", "ch16", "301-322"),
    ("synthesis_destree2014_ch17_taormina_porphyry_myth_er", "argument_taormina_2014_porphyry_eph_hemin_rational_soul_only", "ch17", "323-340"),
    ("synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate", "argument_bonazzi_2014_middle_platonist_hypothetical_fate_partial_solution", "ch18", "283-293"),
    ("synthesis_destree2014_ch19_horn_augustine_liberum_arbitrium", "argument_horn_2014_augustine_liberum_arbitrium_equivalent_plus_eph_hemin", "ch19", "295-310"),
    ("synthesis_destree2014_ch20_steel_proclus_human_or_divine_freedom", "argument_steel_2014_proclus_causal_hierarchy_providence_fate_eph_hemin", "ch20", "311-328"),
    ("synthesis_destree2014_ch21_wildberg_epictetus_simplicius", "argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will", "ch21", "329-350"),
    ("synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview", "argument_frede_michael_2014_eph_hemin_emerges_with_alexander_epictetus_christianity", "ch22", "351-363"),
]

# ---------------------------------------------------------------------------
# LOT 2 — Boethius, Consolatio: passage_boeth_cons_* vs passage_boethius_cons_*
# ---------------------------------------------------------------------------
# 129 loci, 1:1, matched on the trailing number AND re-checked at apply time on
# ``canonical_ref`` + ``cts_urn`` + the DB passage uuid (``db_passage_id`` on the
# short family == ``passage_id`` on the long one).
#
# The Latin is the same text in both, but NOT byte-identical: the
# ``passage_boethius_cons_*`` description wraps it as
#     "Latin: <text>\n\nBoethius, De consolatione philosophiae <n>"
# The survivor is ``passage_boethius_cons_*``: it carries the whole semantic
# layer (discusses 50, source_for 41, cites_primary_source 29, evidenced_by 28)
# and the 129 ``_en`` children, while ``passage_boeth_cons_*`` carries nothing
# but the two structural edges (authored_by + part_of) that the survivor already
# has — 258 edges of which 258 are exact duplicates of existing triples.
#
# TEXT NORMALISATION: the "Latin: " prefix and the trailing self-citation are
# editorial chrome around the reader-facing text. They are stripped ONLY when
# the stripped result equals the deleted twin's description byte for byte. That
# equality is the precondition; no Latin is edited, only unwrapped.
LOT2_BOETHIUS = {
    "short_prefix": "passage_boeth_cons_",
    "long_prefix": "passage_boethius_cons_",
    "expected_pairs": 129,
    "strip_prefix": "Latin: ",
    "strip_tail_pattern": r"\n\nBoethius, De consolatione philosophiae \d+\s*$",
    "port_metadata_keys": ["word_count", "char_length", "db_passage_id"],
    "reason": (
        "Same locus, same CTS URN, same DB passage uuid, same Latin. "
        "passage_boeth_cons_* holds no edge the survivor does not already hold."
    ),
}
# The 129 passage_boethius_cons_*_en nodes are NOT touched: 99 are genuine
# translations and 30 were requalified untranslated_duplicate by the
# 2026-08-16 wave. Both states are preserved.

# ---------------------------------------------------------------------------
# LOT 3 — Augustine, De libero arbitrio
# ---------------------------------------------------------------------------
# 3a. The two work nodes (DAS-087). work_de_libero_arbitrio carries the CTS URN
#     and all 759 passage part_of edges; work_augustine_de_libero_arbitrio
#     carries the editions block and 7 edges, no passage.
LOT3_WORK_MERGE = {
    "survivor": "work_de_libero_arbitrio",
    "absorbed": "work_augustine_de_libero_arbitrio",
    "port_metadata_keys": [
        "genre", "editions", "author_id", "date_composed", "original_language",
        "frede_2011_role", "frede_2011_treatment",
    ],
    # kg_work_id on the absorbed node points at its own (about to vanish) id;
    # it is rewritten to the survivor rather than ported verbatim.
    "rewrite_metadata_keys": {"kg_work_id": "work_de_libero_arbitrio"},
    "reason": (
        "DAS-087: one and the same treatise. The CTS-bearing node keeps every "
        "passage; the other node's only content is its editions block."
    ),
}

# 3b. passage_aug_dla_* (170) vs passage_aug_lib_arb_* (170): MERGE REJECTED.
#     See REJECTED["lot3_dla_vs_lib_arb"]. What IS done instead:
#       - the 93 lib_arb nodes whose cts_urn contradicts their own
#         canonical_ref get the URN of their dla twin (which is correct on
#         170/170);
#       - the 116 lib_arb nodes still claiming passage_role="original" are
#         requalified "summary" (54 of the family already are);
#       - every lib_arb node gets metadata.primary_text_node_id pointing at its
#         dla twin, so a reader can never mistake the apparatus for the text.
LOT3_LIB_ARB_APPARATUS = {
    "text_prefix": "passage_aug_dla_",
    "apparatus_prefix": "passage_aug_lib_arb_",
    "expected_pairs": 170,
    "role_from": "original",
    "role_to": "summary",
    "pointer_key": "primary_text_node_id",
    "reason": (
        "The lib_arb node is an editorial apparatus: English summary + a short "
        "Latin excerpt with ellipses + an English translation + a key-terms "
        "glossary. The dla node is the continuous Latin paragraph. They are not "
        "duplicates; but only one of them is the ancient author, and only the "
        "dla URNs are correct (170/170 vs 77/170)."
    ),
}

# 3c. passage_aug_lib_arb_*_en (170): true zero-information duplicates.
#     All 170 are byte-identical to their parent AND all 170 parents already
#     contain a "Translation:" block, so the needs_translation flag they carry
#     is false. They hold no unique edge: 340 structural edges duplicating the
#     parent's, plus 4 cites_primary_source that are repointed to the parent.
LOT3_EN_DUPLICATES = {
    "prefix": "passage_aug_lib_arb_",
    "suffix": "_en",
    "expected": 170,
    "require_role": "untranslated_duplicate",
    "require_parent_contains": "Translation:",
    "reason": (
        "Byte-identical copy of a parent that already carries its own English "
        "translation inline. Unlike the other untranslated_duplicate nodes kept "
        "as a visible backlog, these have nothing to translate."
    ),
}

# ---------------------------------------------------------------------------
# LOT 4 — duplicate publications (DAS-089 / DAS-090)
# ---------------------------------------------------------------------------
# Already executed by earlier waves, re-verified absent on 2026-08-17:
#   pub_long_1996_stoic_studies, scholarly_work_wolfson_1947_*,
#   scholarly_work_crouzel_1962_orig_ne_*, scholarly_work_jewett_2007_*_hermeneia_series,
#   work_salles_stoics_determinism_2008
#
# Default rule: keep the ``pub_*`` node. It carries the full bibliographic
# description and the citation_verdict, and the structural audit's own
# stale-pointer mapping shows ``pub_*`` is the live namespace
# (pub_eliasson_*, pub_karamanolis_*, pub_sharples_*, pub_voelke_*, pub_destree_*).
# Two documented exceptions, both for scholarly-integrity reasons, below.
#
# Modern scholarship typed ``work``: the survivor is always the ``publication``
# node, whatever its degree. A modern monograph inside the ancient ``work``
# catalogue inflates the work count and breaks R3.
#
# (survivor, absorbed, reason)
LOT4_PUBLICATION_MERGES = [
    ("pub_frede_2011_free_will", "work_frede_free_will_2011",
     "Same book (Sather 68, UCP 2011). The absorbed node is a modern monograph "
     "typed `work`; its long description is ported."),
    ("scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso", "work_bobzien_determinism_freedom_1998",
     "Same OUP monograph typed twice, once `publication` once `work`. The "
     "publication node keeps the 57 edges; the work node's 1471-char "
     "description is ported."),
    ("scholarly_work_frankfurt_1969_alternate_possibilities", "work_frankfurt_alternate_possibilities_1969",
     "Same 1969 JPhil article; the `work`-typed twin is modern scholarship."),
    ("scholarly_work_kane_1996_significance_free_will", "work_significance_of_free_will_kane_1i2j3k4l",
     "Same OUP 1996 monograph; the `work`-typed twin is modern scholarship."),
    ("scholarly_work_van_inwagen_1983_essay_free_will", "work_essay_on_free_will_van_inwagen_8f9g0h1i",
     "Same OUP 1983 monograph; the `work`-typed twin is modern scholarship."),
    ("pub_belcastro_predestinazione_origene", "scholarly_work_belcastro_2016_la_predestinazione_nel_commento_alla_let",
     "Same 2016 study; pub_* holds the 635-char bibliographic description."),
    ("pub_craig_1991_divine_foreknowledge_human_freedom", "scholarly_work_craig_1991_divine_foreknowledge_and_human_freedom_t",
     "Same Brill 1991 monograph; both now agree on year 1991."),
    ("pub_byerly_2017_freewill_theodicies_theological_determinists", "scholarly_work_byerly_2017_free_will_theodicies_for_theological_det",
     "Same 2017 study."),
    ("pub_hick_1966_evil_god_of_love", "scholarly_work_hick_1966_evil_and_the_god_of_love",
     "Same Macmillan 1966 monograph."),
    ("pub_skarsaune_proof_from_prophecy", "scholarly_work_skarsaune_1987_the_proof_from_prophecy_a_study_in_justi",
     "Same Brill 1987 monograph (NovTSup 56)."),
    ("pub_hausmann_noller_2021_free_will_perspectives", "scholarly_work_hausmann_2021_free_will_historical_and_analytic_perspe",
     "Same 2021 edited volume."),
    ("pub_nadelhoffer_monroe_2022_exp_phil_free_will", "scholarly_work_nadelhoffer_2022_advances_in_experimental_philosophy_of_f",
     "Same 2022 edited volume."),
    ("pub_still_wilhite_2024_apologists_paul", "scholarly_work_still_2024_the_apologists_and_paul",
     "Same 2024 edited volume."),
    ("pub_frankfurt_1971_freedom_will_person", "scholarly_work_frankfurt_1971_freedom_of_the_will_and_the_concept_of_a",
     "Same 1971 JPhil article."),
    # --- exception 1: the pub_* id names the wrong author (R9 honest ids) ---
    ("scholarly_work_vicens_2023_christianity_and_the_problem_of_free_wil", "pub_timpe_2023_christianity_problem_free_will",
     "DAS-090: the pub_* id says Timpe while its own label, description and "
     "content are Leigh Vicens's. Ids are the public attribution surface, so "
     "the correctly-named node survives and the rich description is ported."),
    # --- exception 2: the pub_* id carries a year its own metadata refutes ---
    ("scholarly_work_pouderon_1989_ath_nagore_d_ath_nes_philosophe_chr_tien", "pub_pouderon_2000_athenagoras",
     "DAS-090: same monograph (Théologie historique 82, Beauchesne). The "
     "pub_* node's own verification_notes state '1989 Beauchesne first edition; "
     "the 2000 traces to a libgen file mislabel, no distinct 2000 edition is "
     "attested' — yet its id and metadata.year still say 2000. The 1989 node "
     "(ISBN 2-7010-1190-6) survives and the rich description is ported."),
]

# Merging a modern monograph out of the `work` namespace into `publication`
# leaves seven edges whose relation is not declared for a publication endpoint.
# Rather than drop them silently, each is repaired against the node's own
# content, or dropped with its reason. Format:
#   (src, relation, tgt) -> (new_src, new_relation, new_tgt, reason) | None
LOT4_EDGE_REPAIRS = {
    ("argument_consequence_argument_0n1o2p3q", "cites_primary_source", "scholarly_work_van_inwagen_1983_essay_free_will"):
        ("argument_consequence_argument_0n1o2p3q", "advanced_in", "scholarly_work_van_inwagen_1983_essay_free_will",
         "An Essay on Free Will is where the Consequence Argument is advanced; it "
         "is modern scholarship, not a primary source."),
    ("argument_frankfurt_cases_1o2p3q4r", "cites_primary_source", "scholarly_work_frankfurt_1969_alternate_possibilities"):
        ("argument_frankfurt_cases_1o2p3q4r", "advanced_in", "scholarly_work_frankfurt_1969_alternate_possibilities",
         "Frankfurt 1969 is where the Frankfurt cases are advanced, not a primary source."),
    ("scholarly_work_frankfurt_1969_alternate_possibilities", "contains", "argument_frankfurt_cases_1o2p3q4r"):
        ("argument_frankfurt_cases_1o2p3q4r", "advanced_in", "scholarly_work_frankfurt_1969_alternate_possibilities",
         "`contains` has no publication source; the declared direction for "
         "argument-in-publication is advanced_in."),
    ("scholarly_work_frankfurt_1969_alternate_possibilities", "contains", "concept_principle_alternative_possibilities_5s6t7u8v"):
        ("scholarly_work_frankfurt_1969_alternate_possibilities", "discusses", "concept_principle_alternative_possibilities_5s6t7u8v",
         "`contains` has no publication source; discusses is the minimal true claim."),
    ("argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "discusses", "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso"):
        ("argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist", "extends", "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso",
         "The node's own description reads 'Extends Bobzien 1998 (chapter on "
         "Aristotle)'; `extends` accepts argument -> publication."),
    ("pub_bobzien_1998_inadvertent", "precedes", "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso"):
        None,  # `precedes` has no publication target; nothing in the ontology
               # expresses publication-precedes-publication. Dropped.
    ("pub_bobzien_1998_inadvertent", "responds_to", "pub_frede_2011_free_will"):
        None,  # R13 chronology: a 1998 Phronesis article cannot respond to a
               # 2011 book. Dropped rather than reversed by guesswork.
}

# ---------------------------------------------------------------------------
# LOT 5 — CAFMA / Amand 1945
# ---------------------------------------------------------------------------
# ARBITRATION AGAINST THE PRINTED BOOK. The volume was located on disk (Hakkert
# 1973 anastatic reprint of Louvain 1945, 644 pp. PDF + page-preserving .md
# extraction; printed page + 32 = PDF page). Its analytic table of contents
# reads, verbatim:
#
#   « CONCLUSION — RECONSTITUTION CONJECTURALE DE L'ARGUMENTATION DE CARNÉADE … 571-586
#     Introduction … 571-573
#     I. Les arguments carnéadiens dans les «textes témoins» … 573-581
#     II. Reconstitution conjecturale et fragmentaire de la contexture de
#        l'argumentation morale antifataliste de Carnéade … 581-584
#        Thème général et cinq arguments reconstitués.
#     III. De quelques arguments attestés par Alexandre d'Aphrodise … 584-586 »
#
# VERDICT: the two paginations are NOT contradictory. p. 573-581 is section I
# (the synoptic dossier of the witnesses, six headings); p. 581-584 is section II
# (the same six items as a reconstructed synthesis). Both series cite a real
# locus. Nothing needs re-paginating.
#
# The real defects are elsewhere:
#   (a) the cafma_* numbering does not match Amand's. Amand: 1 thème général,
#       2 législation, 3 vertu/vice, 4 encouragements/châtiments, 5 futilité de
#       l'action et de l'effort, 6 piété. The cafma series numbers I effort,
#       II législation, III louange/blâme/sanctions, IV character contradiction,
#       V piété — and argument_cafma_futility_of_effort_8c3d5f21 contradicts its
#       own label in its own description ("Amand reconstructs it as argument
#       no. 5").
#   (b) argument_cafma_character_contradiction_1f6g8i54 is not in Amand's series
#       at all: it appears in neither the six headings of section I nor the six
#       reconstructed items of section II. It is an anti-astrological argument
#       (natal horoscope), belonging to a different chapter.
#   (c) the framework node's witness list is wrong: Amand's six "textes témoins"
#       (p. 571-572) are Philo, Alexander, Firmicus Maternus, Eusebius, John
#       Chrysostom, Ps.-Chrysostom. The node omits Philo and adds ps.-Plutarch;
#       Bardaisan/Basil/Nemesius are "cf." confirmations in Amand, not witnesses.
AMAND_1945 = {
    "citation": ("David Amand [Amand de Mendieta], Fatalisme et liberté dans "
                 "l'antiquité grecque, Louvain 1945 (repr. Hakkert, Amsterdam 1973)"),
    "conclusion_pages": "571-586",
    "section_I_pages": "573-581",
    "section_II_pages": "581-584",
    "headings": [
        ("I", "Thème général de l'argumentation", "573-574", "582"),
        ("II", "Dans l'hypothèse du fatalisme astrologique, la législation et la répression pénale sont inutiles et doivent être supprimées", "574-576", "582"),
        ("III", "Dans l'hypothèse du fatalisme absolu, la vertu et le vice, la louange et le blâme sont inutiles", "576-577", "582-583"),
        ("IV", "Dans l'hypothèse du fatalisme absolu, encouragements et récompenses, reproches, réprimandes et châtiments sont inutiles", "577-578", "583"),
        ("V", "Si le fatalisme astrologique est vrai, toute action, morale ou non, devient inutile", "578-580", "583-584"),
        ("VI", "Le fatalisme absolu ruine la piété à l'égard de la divinité", "580-581", "584"),
    ],
    "witnesses": [
        "Philon d'Alexandrie, De providentia I, 79-83",
        "Alexandre d'Aphrodise, De fato 16-20",
        "Firmicus Maternus, Mathesis I, 2, 5-11",
        "Eusèbe de Césarée, Praeparatio evangelica VI, 6, 4-21",
        "Jean Chrysostome, Hom. post concionem presbyteri Gothi 6",
        "Ps.-Jean Chrysostome, De fato et providentia V",
    ],
    "witnesses_page": "571-572",
    "iron_rule": "Est censé carnéadien tout argument attesté par 3 témoins au moins sur 6 (p. 573).",
}

# (survivor, absorbed, reason) — the survivor is always the amand1945 series,
# which reproduces Amand item by item and page by page.
LOT5_CAFMA_MERGES = [
    ("argument_carneadean_action_futility_amand1945", "argument_cafma_futility_of_effort_8c3d5f21",
     "Amand's 5th head (p. 578-580, recap 583-584). The absorbed node's own "
     "description says 'Amand reconstructs it as argument no. 5', contradicting "
     "its label 'Argument I'. Both cite Eusebius PE VI.6.8-10."),
    ("argument_carneadean_legislation_amand1945", "argument_cafma_futility_of_legislation_9d4e6g32",
     "Amand's 2nd head (p. 574-576, recap 582). Both cite Eusebius PE VI.6.18."),
    ("argument_carneadean_piety_amand1945", "argument_cafma_futility_of_piety_2g7h9j65",
     "Amand's 6th head (p. 580-581, recap 584). Both cite Eusebius PE VI.6.19."),
    ("argument_cafma_carneades_m3n4o5p6", "framework_cafma_5a7b9e12",
     "Two frame nodes for one object: 'CAFMA - Carneades' Anti-Fatalist Moral "
     "Argumentation' and 'CAFMA: Carneadean Anti-Fatalist Moral Argumentation', "
     "sharing 44 edges. The surviving node is the `argument`-typed one because "
     "every one of the framework's 20 edges is ontology-legal on an `argument`, "
     "whereas keeping the framework would forfeit 9 edges illegal for "
     "`argument_framework` — including all 8 cites_primary_source. The "
     "framework's false witness list is NOT ported; the verified list from the "
     "book is written instead."),
]

# Edges deleted with this wave, each with its finding.
LOT5_EDGE_DROPS = [
    ("argument_cafma_futility_of_piety_2g7h9j65", "supports", "concept_pronoia_levels_proclus_a6d8c9b4",
     "DAS-098: a 2nd-c. BCE Carneadean argument cannot support Proclus's 5th-c. CE "
     "hierarchy of providence. Dropped rather than re-targeted by guesswork."),
]

# Not a member of Amand's series (see (b) above): kept, re-scoped, un-numbered.
LOT5_RESCOPE = {
    "node": "argument_cafma_character_contradiction_1f6g8i54",
    "old_label": "CAFMA Argument IV: Contradiction of Character Change",
    "new_label": "Anti-astrological argument: moral character changes, the natal horoscope cannot fix it",
    "drop_edge": ("argument_cafma_character_contradiction_1f6g8i54", "contains", "framework_cafma_5a7b9e12"),
    "metadata": {
        "amand_1945_series_member": False,
        "amand_1945_verification": (
            "Absent from both lists in Amand's Conclusion: not one of the six "
            "headings of section I (p. 573-581) nor of the six reconstructed "
            "items of section II (p. 581-584). Full-text search of the local "
            "OCR for 'changement de caractère' / 'du vice à la vertu' returns no "
            "relevant hit. This is an anti-astrological argument (natal "
            "horoscope), not part of the reconstructed moral series."
        ),
    },
}

# Straddles two of Amand's heads: NOT merged, linked instead.
LOT5_DEFERRED = {
    "node": "argument_cafma_futility_of_sanctions_0e5f7h43",
    "same_thesis_as": "argument_carneadean_incentives_amand1945",
    "reason": (
        "'CAFMA Argument III' conflates Amand's head III (vertu/vice, louange/"
        "blâme, p. 576-577) and head IV (encouragements, récompenses, châtiments, "
        "p. 577-578) — which Amand himself calls 'un cas particulier du "
        "précédent' (p. 577 n. 1). Its label points at III, its evidence "
        "(Eusebius PE VI.6.12-16) at IV. A merge would have to pick one; it is "
        "linked to IV (4 of its 5 citations) and flagged instead."
    ),
    "flag": "needs_scholarly_split",
}

# The correction of the framework's witness list, written on the survivor.
LOT5_WITNESS_FIX = {
    "node": "argument_cafma_carneades_m3n4o5p6",
    "wrong_list": "ps.-Plutarch, Alexander of Aphrodisias, Firmicus Maternus, "
                  "Eusebius, Nemesius, John Chrysostom, Bardesanes",
    "reason": (
        "Amand's six 'textes témoins' are listed verbatim at p. 571-572. Philo "
        "was omitted and ps.-Plutarch wrongly added; Bardaisan, Basil, Nemesius "
        "and the Arian commentator are 'cf.' confirmations in Amand, not witnesses."
    ),
}

# ---------------------------------------------------------------------------
# LOT 6 — same_thesis_as families and double-extraction duplicates
# ---------------------------------------------------------------------------
# Merge rule, applied uniformly and never by eye:
#   MERGE two ``scholarly_argument_*`` nodes iff
#     (1) same scholar, and
#     (2) their ``source_file`` values resolve to the SAME publication (the same
#         book/article extracted twice: full text vs .summary.md, .md vs .txt,
#         OCR vs non-OCR), and
#     (3) their ``page_range`` values overlap or nest.
#   Everything else gets ``same_thesis_as``.
# (2) is what separates a double extraction from two genuine claims; (3) is what
# stops a whole-chapter claim being merged with a claim about another chapter of
# the same book.
LOT6_PUBLICATION_KEYS = {
    "bobzien1998": ["Bobzien - 1998 - The Inadvertent", "Bobzien_1998.summary", "Bobzien_1998_Inadvertent"],
    "bobzien2001": ["Bobzien - 2001 - Determinism", "Bobzien_2001.summary", "Bobzien_2001_Determinism"],
    "frede2011": ["Frede_2011.summary", "Frede_2011_Free_Will", "Sather Classical Lectures, Vol. 68"],
    "dfrede1982": ["Frede - 1982 - The Dramatization", "The Dramatization of Determinism-"],
    "dihle1982": ["Sather Classical Lectures_ 48", "Albrecht Dihle - The Theory of Will", "Dihle_1982.summary", "Dihle_1982_Theory_Will"],
    "furst2022": ["Wege zur Freiheit"],
    "double_frame": ["How to Frame the Free Will Problem"],
    "belcastro2016": ["Belcastro_Predestinazione_Origene"],
    "byerly2017": ["Byerly_2017_Free_Will_Theodicies"],
    "hick1966": ["Hick_1966_Evil_and_the_God_of_Love"],
    "ramelli2014": ["Ramelli - 2014 -", "Ramelli_2014.summary"],
    "eliasson2009": ["Eliasson - 2009 -", "Sur la conception plotinienne du destin dans le trait"],
    "telfer1957": ["TELFER, W. (1957)", "Telfer_1957.summary"],
    "sharples2008": ["accident du d"],
    "minns2009": ["Justin, Philosopher and Martyr"],
    "pouderon_culture_grecque": ["Les Apologistes chr", "Pouderon_Apologistes_Culture_Grecque"],
    "pouderon_apologistes_grecs": ["Les Apologistes grecs du II", "Apologistes grecs du IIe si"],
    "boysstones2007": ["BoysStones_2007_MiddlePlatonists", "Middle_Platonists_on_Fate_and_Human_Aut"],
}

# (survivor, [absorbed…], publication_key, cluster_title)
LOT6_MERGES = [
    ("scholarly_argument_bobzien_origin_of_free_will_problem_in_0", ["scholarly_argument_bobzien_origin_of_the_free_will_proble_0"], "bobzien1998", "Cluster Bobzien — Origine du problème du libre arbitre"),
    ("scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_3", ["scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_4"], "bobzien1998", "Cluster Bobzien — Alexandre = première attestation non ambiguë"),
    ("scholarly_argument_bobzien_types_of_freedom_1", ["scholarly_argument_bobzien_types_of_freedom_and_moral_res_2"], "bobzien1998", "Cluster Bobzien — Sept types de liberté"),
    ("scholarly_argument_bobzien_greek_terminology_for_freedom_1", ["scholarly_argument_bobzien_vs_6"], "bobzien1998", "Cluster Bobzien — ἐλευθερία absente des débats jusqu'au IIe s."),
    ("scholarly_argument_bobzien_historical_marginality_of_libe_7", ["scholarly_argument_bobzien_marginality_of_freedom_to_do_o_5"], "bobzien1998", "Cluster Bobzien — Marginalité de la liberté de faire autrement"),
    ("scholarly_argument_bobzien_middle_platonists_on_contingen_7", ["scholarly_argument_bobzien_development_of_two_sided_indet_3", "scholarly_argument_bobzien_middle_platonist_synthesis_4"], "bobzien1998", "Cluster Bobzien — Synthèse médio-platonicienne"),
    ("scholarly_argument_bobzien_chrysippus_compatibilism_fate__1", ["scholarly_argument_bobzien_chrysippus_psychology_of_actio_5"], "bobzien2001", "Cluster Bobzien — Compatibilisme chrysippéen / analogie du cylindre"),
    ("scholarly_argument_frede_platonist_and_peripatetic_resp_3", ["scholarly_argument_frede_platonist_and_peripatetic_resp_4"], "frede2011", "Cluster Frede 2011 — Réponses platoniciennes et péripatéticiennes"),
    ("scholarly_argument_frede_origin_of_free_will_0", ["scholarly_argument_frede_historical_origin_of_free_will_0"], "frede2011", "Cluster Frede 2011 — Notion technique et historiquement datable"),
    ("scholarly_argument_frede_stoic_origin_of_the_will_2", ["scholarly_argument_frede_stoic_psychology_and_assent_2", "scholarly_argument_frede_stoic_theory_of_assent_and_wil_2"], "frede2011", "Cluster Frede 2011 — L'assentiment stoïcien"),
    ("scholarly_argument_frede_methodology_8", ["scholarly_argument_frede_methodology_for_studying_free__5"], "frede2011", "Cluster Frede 2011 — Méthodologie"),
    ("scholarly_argument_dihle_greek_philosophical_theology_a_0", ["scholarly_argument_dihle_greek_philosophical_theology_v_0"], "dihle1982", "Cluster Dihle 1982 — Cosmologie grecque vs biblique"),
    ("scholarly_argument_dihle_prayer_and_divine_immutability_2", ["scholarly_argument_dihle_prayer_and_divine_rationality_1"], "dihle1982", "Cluster Dihle 1982 — Prière et immutabilité/rationalité divine"),
    ("scholarly_argument_sharples_free_will_and_determinism_in_a_1", ["scholarly_argument_sharples_historical_determinism_0"], "sharples2008", "Sharples 2008 — deux extractions du même fichier"),
    ("scholarly_argument_ramelli_alexander_of_aphrodisias_as_so_0", ["scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0"], "ramelli2014", "Ramelli 2014 — Origène connaissait Alexandre"),
    ("scholarly_argument_ramelli_anti_determinism_and_free_will_1", ["scholarly_argument_ramelli_determinism_and_free_will_stoi_1"], "ramelli2014", "Ramelli 2014 — anti-déterminisme partagé"),
    ("scholarly_argument_double_definition_of_free_will_free_c_2", ["scholarly_argument_double_placeholder_definition_of_free_3"], "double_frame", "Double — définition 'placeholder' (OCR vs non-OCR)"),
    ("scholarly_argument_minns_free_will_and_determinism_in_j_0", ["scholarly_argument_minns_free_will_in_justin_martyr_0"], "minns2009", "Minns — libre arbitre chez Justin"),
    ("scholarly_argument_pouderon_formation_of_christian_intelle_1", ["scholarly_argument_pouderon_intellectual_formation_of_chri_3"], "pouderon_culture_grecque", "Pouderon — formation de l'élite intellectuelle"),
    ("scholarly_argument_pouderon_free_will_in_early_christian_a_0", ["scholarly_argument_pouderon_free_will_and_moral_responsibi_0"], "pouderon_apologistes_grecs", "Pouderon — libre arbitre chez les apologistes"),
    ("scholarly_argument_eliasson_plotinus_s_treatise_iii_on_fat_0", ["scholarly_argument_eliasson_the_scope_and_target_of_plotin_1"], "eliasson2009", "Eliasson 2009 — portée du traité III.1"),
    ("scholarly_argument_frede_alexander_of_aphrodisias_targe_1", ["scholarly_argument_frede_alexander_of_aphrodisias_treat_1"], "dfrede1982", "D. Frede 1982 — cible et méthode d'Alexandre"),
    ("scholarly_argument_frede_tensions_in_aristotle_on_causa_3", ["scholarly_argument_frede_tensions_in_aristotle_s_own_po_4"], "dfrede1982", "D. Frede 1982 — tensions chez Aristote"),
    ("scholarly_argument_belcastro_free_will_libero_arbitrio_and__2", ["scholarly_argument_belcastro_relationship_between_divine_om_2"], "belcastro2016", "Belcastro — libre arbitre et toute-puissance"),
    ("scholarly_argument_byerly_compatibilist_molinism_1", ["scholarly_argument_byerly_molinism_and_theological_deter_2"], "byerly2017", "Byerly — molinisme et déterminisme théologique"),
    ("scholarly_argument_telfer_origen_s_systematization_and_i_4", ["scholarly_argument_telfer_origen_s_determinism_and_its_r_3"], "telfer1957", "Telfer 1957 — rejet du système origénien"),
    ("scholarly_argument_hick_moral_responsibility_and_soul__4", ["scholarly_argument_hick_moral_responsibility_2"], "hick1966", "Hick 1966 — responsabilité morale et soul-making"),
]

# Edges removed because the merge makes them meaningless.
LOT6_EDGE_DROPS = [
    ("scholarly_argument_sharples_accident_of_determinism_2008", "agrees_with", "scholarly_argument_sharples_free_will_and_determinism_in_a_1",
     "DAS-094: a dialectical relation posed between two nodes of the same "
     "article by the same author. Replaced by same_thesis_as."),
]

# Clusters linked rather than merged. The applier reads the cluster membership
# from the audit file, drops members that no longer exist or were just absorbed,
# and builds a star from the audit's own best_member (or, failing that, the
# highest-degree survivor).
LOT6_LINK_SOURCE = "data/audit/2026-08-16_deep_audit_semantic.jsonl"

# Page ranges that stopped a merge and are themselves suspect: recorded on the
# node so the next wave can resolve them against the print.
LOT6_PAGE_RANGE_CONFLICTS = [
    ("scholarly_argument_bobzien_eph_hemin_what_depends_on_us_3", "375-412", "Bobzien 1998 = Phronesis 43, pp. 133-175; 375-412 lies outside the article."),
    ("scholarly_argument_frede_epictetus_as_originator_of_fre_3", "2770-2779", "Four-digit value in a book of ~200 pages: a character or line offset, not a page range."),
    ("scholarly_argument_frede_origen_s_doctrine_of_free_will_5", "3855-3924", "Four-digit value: offset, not page range."),
    ("scholarly_argument_frede_origen_s_differences_from_stoi_6", "4158-4175", "Four-digit value: offset, not page range."),
    ("scholarly_argument_dihle_greek_concept_of_will_0", "3054-3057, 3110-3127", "Four-digit values: offsets, not page ranges."),
]

# ---------------------------------------------------------------------------
# LOT 7 — the three-person "editors" node (DAS-091)
# ---------------------------------------------------------------------------
# scholar_destr_e_p_salles_zingano_eds is typed `person` but denotes three
# people. It has exactly three inbound edges and no outbound edge. Note that
# its metadata.members still lists `scholar_salles_ricardo`, which no longer
# exists (merged into person_salles_ricardo_contemporary).
LOT7_EDITORS = {
    "node": "scholar_destr_e_p_salles_zingano_eds",
    "members": ["scholar_destr_e_p", "person_salles_ricardo_contemporary", "scholar_zingano_marco"],
    "stale_member_in_metadata": "scholar_salles_ricardo",
    "rewire": [
        # (source, old_relation, new_relation, reason)
        ("pub_destree_salles_zingano_2014_what_is_up_to_us", "authored_by", "edited_by",
         "The volume is metadata.type=edited_volume and metadata.editors names "
         "exactly these three. The ontology has publication→person `edited_by` "
         "and the structural audit asks it to absorb the editor-as-author cases. "
         "The three existing pub→authored_by→<editor> edges are retyped too."),
        ("synthesis_destree2014_introduction_overview", "authored_by", "authored_by",
         "The volume introduction (p. 1-6) is signed by the three editors; the "
         "single edge to the collective node becomes three edges to the persons."),
    ],
    # Also retype the three individual authored_by edges on the volume.
    "retype_volume_authorship": True,
    "drop_edges": [
        ("scholar_frede_michael", "influences", "scholar_destr_e_p_salles_zingano_eds",
         "Empty metadata, no attestation, and a target that is an editorial "
         "artifact rather than a person. Splitting it into three individual "
         "influence claims would be an inference, not a port. Dropped and "
         "recorded (DAS-100: the un-attested dialectical edges are the "
         "error-prone class)."),
    ],
}

# Merges declared in metadata by earlier waves and verified EXECUTED on
# 2026-08-17 (nothing to do):
LOT7_ALREADY_DONE = [
    ("pub_long_1996_stoic_studies", "scholarly_work_long_1996_stoic_studies", "absent — merge executed"),
    ("scholarly_work_crouzel_1962_orig_ne_et_la_philosophie", "scholarly_work_crouzel_1962_origene_et_la_philosophie", "absent — merge executed"),
    ("scholarly_work_wolfson_1947_philo_on_free_will_and_the_historical_in", "pub_wolfson_1942_philo_free_will", "absent — merge executed, year 1942 kept"),
    ("scholarly_work_jewett_2007_romans_a_commentary_hermeneia_series", "scholarly_work_jewett_2007_romans_a_commentary", "absent — merge executed"),
    ("work_salles_stoics_determinism_2008", "scholarly_work_salles_2005_the_stoics_on_determinism_and_compatibil", "absent — merge executed, year 2005 kept"),
]

# ---------------------------------------------------------------------------
# REJECTED — pairs the audit flagged that are NOT duplicates
# ---------------------------------------------------------------------------
REJECTED = {
    "lot3_dla_vs_lib_arb": (
        "passage_aug_dla_* (170) vs passage_aug_lib_arb_* (170). NOT a merge. "
        "The audit's bibliographic pass saw 170/170 canonical_ref overlap and "
        "inferred duplication; the texts are different objects. dla holds the "
        "continuous Latin paragraph (median 1388 chars); lib_arb holds an "
        "English summary + an elided Latin excerpt + an English translation + a "
        "key-terms glossary. Deleting lib_arb would destroy the only English "
        "translation of these 170 loci; folding its description into dla would "
        "put editorial prose inside the ancient author's text — the exact defect "
        "docs/development/ingestion-rules.md names as known debt ('one node "
        "holds the primary text, the other an English editorial summary … needs "
        "classification, not a mechanical merge'). Corrective operations are "
        "applied instead: see LOT3_LIB_ARB_APPARATUS."
    ),
    "bobichon_2003": (
        "scholarly_work_bobichon_2003_..._le_tryphon_d vs ..._tryphon_diti are "
        "the TWO VOLUMES of one critical edition, not one book twice: their own "
        "verified_reference fields read 'vol. 2, coll. Paradosis 47/2' and "
        "'vol. 1 (Introduction, texte grec, traduction), coll. Paradosis 47/1'. "
        "The structural audit's 'near-certain merge' is a false positive. Their "
        "labels are disambiguated instead."
    ),
    "gill_2014": (
        "scholarly_work_gill_2014_a_free_will_origins_of_the_notion_in_anc is "
        "NOT a duplicate of pub_frede_2011_free_will and must not be merged into "
        "it. Diagnosis: it is Christopher Gill's REVIEW of Frede's book (The "
        "European Legacy 19.6, 2014, 797-798, DOI 10.1080/10848770.2014.949953) "
        "— its verified_reference already says so correctly. The defect is "
        "cosmetic and real: title, label and description are the reviewed book's "
        "title with '(review)' appended, so a reader sees Gill as the author of "
        "Frede's book. Fixed by rewriting title/label/description to 'Review of "
        "M. Frede, A Free Will…'; the node, its author and its five arguments "
        "stay."
    ),
    "crouzel_arguments": (
        "scholarly_argument_crouzel_free_will_and_determinism_in_o_0 and "
        "..._free_will_libre_arbitre_in_ori_1 come from two DIFFERENT books: "
        "Théologie de l'image de Dieu chez Origène (Théologie 34, Aubier 1956) "
        "and Origène et la philosophie (1962). same_thesis_as, not merge."
    ),
    "bobichon_arguments": (
        "The two Bobichon arguments cite the Dialogue critical edition vol. 2 and "
        "the separate 'manuscrit' study. Two publications. same_thesis_as."
    ),
    "fitzmyer": "Two different sections of one commentary (Rom 9:1-5 and 9:6-29). same_thesis_as.",
    "gaventa": "Three different sections of one commentary (Rom 5, 8, 9-10:21). same_thesis_as.",
    "dettwiler": (
        "Three different publications on Colossians (p. 26-28, p. 308, p. 287-288). "
        "No evidence that any two are the same print. same_thesis_as."
    ),
    "boys_stones": (
        "Same article, but disjoint loci and different objects: 'Justin Martyr as "
        "Middle Platonist on fate' (p. 434 n.9) vs 'Middle Platonist theory of "
        "fate' (p. 431-433). same_thesis_as."
    ),
    "bobzien_page_conflicts": (
        "Eleven scholarly_argument_bobzien_* pairs from the same publication were "
        "left unmerged because their page ranges are disjoint or unparseable "
        "('Chapter 3' vs '97-143'). Merging them would silently pick one locus "
        "over another. Linked and flagged instead — see LOT6_PAGE_RANGE_CONFLICTS."
    ),
}
