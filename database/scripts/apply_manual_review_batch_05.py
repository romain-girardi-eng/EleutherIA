#!/usr/bin/env python3
"""
Batch 05: Manual scholarly review — source_for edges for remaining unsupported nodes.

Each entry below was individually reviewed by examining the node's metadata,
connected persons, ancient sources, and cross-referencing against the KG's
work/publication inventory.

Nodes that cannot be linked to an existing KG work/publication are explicitly
flagged as "flag_manual_review" with a scholarly reason.

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/apply_manual_review_batch_05.py
    uv run --directory database python database/scripts/apply_manual_review_batch_05.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
RUN_TAG = "kg_manual_review_batch_05_2026_03_10"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-10-kg-manual-review-batch-05-results.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-10-kg-manual-review-batch-05-results.md"


@dataclass(frozen=True)
class SourceForEdge:
    """A source_for edge to add: source (work/pub) → target (claim node)."""
    node_id: str          # target claim node
    node_label: str
    source_id: str        # source work/pub node
    source_label: str
    reason: str           # scholarly justification


@dataclass(frozen=True)
class ManualFlag:
    """A node that cannot be automatically sourced."""
    node_id: str
    node_label: str
    reason: str


# ============================================================================
# MANUALLY REVIEWED DECISIONS — Arguments (first 30)
# ============================================================================

EDGES_TO_ADD: list[SourceForEdge] = [
    # --- Anti-astrological arguments (Carneades via Cicero) ---
    SourceForEdge(
        node_id="argument_anti_astrology_impossibility_observation_3h8i0k76",
        node_label="Anti-Astrological Argument I: Impossibility of Exact Observation",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Ancient sources: Cicero De Fato 28-33 / De Divinatione II.87-99. De Fato is the best available KG work preserving Carneadean anti-astrological argumentation.",
    ),
    SourceForEdge(
        node_id="argument_anti_astrology_twins_4i9j1l87",
        node_label="Anti-Astrological Argument II: The Twins Argument",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Ancient sources: Cicero De Divinatione II.90-93, Augustine De Civitate Dei V.1-7. De Fato is the primary KG proxy for Academic anti-fatalist arguments.",
    ),
    SourceForEdge(
        node_id="argument_anti_astrology_collective_catastrophes_5j0k2m98",
        node_label="Anti-Astrological Argument III: Collective Catastrophes",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Ancient sources: Cicero De Divinatione II.97-99. De Fato is the KG proxy for Carneadean anti-astrological arguments.",
    ),
    SourceForEdge(
        node_id="argument_anti_astrology_nomima_barbarika_6k1l3n09",
        node_label="Anti-Astrological Argument IV: Diversity of Customs",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Ancient sources: Aulus Gellius reporting Favorinus, Bardesanes in Eusebius. De Fato is the best KG proxy for Academic anti-astrological argumentation.",
    ),
    # --- CAFMA arguments (Carneades via Cicero De Fato 28-33) ---
    SourceForEdge(
        node_id="argument_cafma_futility_of_effort_8c3d5f21",
        node_label="CAFMA Argument I: Futility of Effort and Labor",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Primary source: Cicero De Fato 28-33. Direct literary source preserving Carneades' CAFMA argumentation.",
    ),
    SourceForEdge(
        node_id="argument_cafma_futility_of_legislation_9d4e6g32",
        node_label="CAFMA Argument II: Futility of Legislation and Justice",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Primary source: Cicero De Fato 28-33.",
    ),
    SourceForEdge(
        node_id="argument_cafma_futility_of_sanctions_0e5f7h43",
        node_label="CAFMA Argument III: Futility of Praise, Blame, and Sanctions",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Primary source: Cicero De Fato 28-33.",
    ),
    SourceForEdge(
        node_id="argument_cafma_character_contradiction_1f6g8i54",
        node_label="CAFMA Argument IV: Contradiction of Character Change",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Primary source: Cicero De Fato 28-33.",
    ),
    SourceForEdge(
        node_id="argument_cafma_futility_of_piety_2g7h9j65",
        node_label="CAFMA Argument V: Futility of Piety and Prayer",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Primary source: Cicero De Fato 28-33.",
    ),
    # --- Augustine ---
    SourceForEdge(
        node_id="argument_augustines_two_wills_argument_confessions_viii_81f95028",
        node_label="Augustine's Two Wills Argument (Confessions VIII)",
        source_id="work_confessions",
        source_label="Confessiones (Confessions)",
        reason="Primary source: Augustine Confessiones VIII.8-10. Direct textual source.",
    ),
    # --- Boethius ---
    SourceForEdge(
        node_id="argument_boethian_solution_divine_eternity_k1l2m3n4",
        node_label="Boethian Solution: Divine Timeless Eternity",
        source_id="work_consolatio_philosophiae_boethius_524ce_f1g2h3i4",
        source_label="De consolatione philosophiae (Consolation of Philosophy)",
        reason="Primary source: Boethius, Consolation of Philosophy V, Prosa 6.",
    ),
    # --- Cleanthes (preserved in Epictetus) ---
    SourceForEdge(
        node_id="argument_cleanthes_hymn_to_zeus_argument_f71f5b37",
        node_label="Cleanthes' Hymn to Zeus Argument",
        source_id="work_epictetus_enchiridion",
        source_label="Enchiridion (Ἐγχειρίδιον) - Epictetus",
        reason="Cleanthes' works survive only in fragments. Epictetus Enchiridion 53 quotes the key formula. Best available KG source.",
    ),
    # --- Van Inwagen ---
    SourceForEdge(
        node_id="argument_consequence_argument_0n1o2p3q",
        node_label="Consequence Argument",
        source_id="work_essay_on_free_will_van_inwagen_8f9g0h1i",
        source_label="An Essay on Free Will",
        reason="Formulator: Peter van Inwagen. Primary source: An Essay on Free Will (1983). Direct match.",
    ),
    # --- Democritus (preserved in Diogenes Laertius) ---
    SourceForEdge(
        node_id="argument_democritean_atomistic_determinism_c52067ec",
        node_label="Democritean Atomistic Determinism",
        source_id="work_diogenes_laertius_lives",
        source_label="Diogenes Laertius, Lives of Eminent Philosophers",
        reason="Ancient source: Diogenes Laertius IX.30-49. Primary doxographic source for Democritean determinism.",
    ),
    # --- Epictetus ---
    SourceForEdge(
        node_id="argument_epictetus_prohairesis_argument_aa13b932",
        node_label="Epictetus' Prohairesis Argument",
        source_id="work_epictetus_discourses",
        source_label="Discourses (Διατριβαί) - Epictetus",
        reason="Primary source: Epictetus Discourses I.1, I.17, II.1-2. Direct textual source for prohairesis doctrine.",
    ),
    # --- Pereboom ---
    SourceForEdge(
        node_id="argument_four_case_manipulation_2p3q4r5s",
        node_label="Four-Case Manipulation Argument",
        source_id="work_living_without_free_will_pereboom_0h1i2j3k",
        source_label="Living Without Free Will",
        reason="Formulator: Derk Pereboom. Primary source: Living Without Free Will (2001). Direct match.",
    ),
]

MANUAL_FLAGS: list[ManualFlag] = [
    ManualFlag(
        node_id="argument_anselms_necessity_of_the_past_f7947dab",
        node_label="Anselm's Necessity of the Past",
        reason="Primary source: Anselm's De Concordia. No works by Anselm in KG.",
    ),
    ManualFlag(
        node_id="argument_aquinass_intellectualism_f0058bf9",
        node_label="Aquinas's Intellectualism",
        reason="Primary source: Aquinas Summa Theologiae I-II. No Aquinas works in KG.",
    ),
    ManualFlag(
        node_id="argument_aquinass_natural_inclination_to_happiness_7a145771",
        node_label="Aquinas's Natural Inclination to Happiness",
        reason="Primary source: Aquinas Summa Theologiae I-II. No Aquinas works in KG.",
    ),
    ManualFlag(
        node_id="argument_aquinass_primary_and_secondary_causation_12f1649a",
        node_label="Aquinas's Primary and Secondary Causation",
        reason="Primary source: Aquinas Summa Theologiae I, SCG III. No Aquinas works in KG.",
    ),
    ManualFlag(
        node_id="argument_basic_argument_3q4r5s6t",
        node_label="Basic Argument (Strawson)",
        reason="Formulator: Galen Strawson. Primary source: 'The Impossibility of Moral Responsibility' (1994). No Galen Strawson works in KG.",
    ),
    ManualFlag(
        node_id="argument_buridans_ass_73a98d20",
        node_label="Buridan's Ass",
        reason="Attributed to Jean Buridan. No Buridan works in KG.",
    ),
    ManualFlag(
        node_id="argument_cartesian_dualism_and_agent_causation_b637cc75",
        node_label="Cartesian Dualism and Agent Causation",
        reason="Primary source: Descartes Meditations on First Philosophy. No Descartes works in KG.",
    ),
    ManualFlag(
        node_id="argument_compatibilism_through_divine_concurrence_d6ce2a0f",
        node_label="Compatibilism through Divine Concurrence",
        reason="Formulator: Francisco Suárez. No Suárez works in KG.",
    ),
    ManualFlag(
        node_id="argument_conatus_doctrine_1588d13c",
        node_label="Conatus Doctrine",
        reason="Formulator: Baruch Spinoza. Primary source: Ethics (1677). No Spinoza works in KG.",
    ),
    ManualFlag(
        node_id="argument_edwardsian_compatibilism_5a9v0w68",
        node_label="Edwards's Compatibilist Defense of Reformed Theology",
        reason="Formulator: Jonathan Edwards. No Edwards works in KG.",
    ),
    ManualFlag(
        node_id="argument_erasmian_free_will_7s1n2o80",
        node_label="Erasmus's Defense of Free Will",
        reason="Primary source: Erasmus De Libero Arbitrio (1524). No Erasmus works in KG.",
    ),
    ManualFlag(
        node_id="argument_freedom_of_indifference_dab82dcc",
        node_label="Freedom of Indifference",
        reason="Primary source: Descartes Meditations, Principles of Philosophy. No Descartes works in KG.",
    ),
    ManualFlag(
        node_id="argument_gersonides_limited_omniscience_s9t0u1v2",
        node_label="Gersonides' Argument: Limited Divine Omniscience",
        reason="Primary source: Wars of the Lord III.4-6. No Gersonides works in KG.",
    ),
    ManualFlag(
        node_id="argument_gregory_of_nyssas_image_of_god_argument_f80938fc",
        node_label="Gregory of Nyssa's Image of God Argument",
        reason="Primary source: Gregory De Hominis Opificio. No Gregory of Nyssa works in KG.",
    ),
    ManualFlag(
        node_id="argument_hobbesian_compatibilism_1w5r6s24",
        node_label="Hobbes's Compatibilist Argument",
        reason="Primary source: Leviathan ch. 21. No Hobbes works in KG.",
    ),
]


# ============================================================================
# Placeholder for remaining entries — will be filled from agent reviews
# ============================================================================

EDGES_BATCH_05B: list[SourceForEdge] = [
    # --- Infant Baptism (Augustine) ---
    SourceForEdge(
        node_id="argument_infant_baptism",
        node_label="Infant Baptism Argument for Original Sin",
        source_id="work_de_libero_arbitrio",
        source_label="De Libero Arbitrio Voluntatis (On Free Choice of the Will)",
        reason="Augustine DLA III.23 discusses infant suffering and original sin. Best available KG proxy for the infant baptism argument.",
    ),
    # --- Irenaeus ---
    SourceForEdge(
        node_id="argument_irenaeuss_antignostic_argument_for_free_will_f54fe920",
        node_label="Irenaeus's Anti-Gnostic Argument for Free Will",
        source_id="work_irenaeus_adversus_haereses_book4",
        source_label="Irenaeus, Adversus Haereses Book 4",
        reason="Primary source: AH IV.37-39. Irenaeus's central free will argument against Gnostic determinism.",
    ),
    # --- Jansenist (draws on Augustine) ---
    SourceForEdge(
        node_id="argument_jansenist_denial_of_liberty_of_indifference_73aa8ce2",
        node_label="Jansenist Denial of Liberty of Indifference",
        source_id="work_augustine_de_gratia_la",
        source_label="De Gratia et Libero Arbitrio (Augustine)",
        reason="Jansenism derives its denial of liberty of indifference from Augustine's De Gratia et Libero Arbitrio. Best KG proxy for the Augustinian foundation of Jansenist theology.",
    ),
    # --- John Chrysostom ---
    SourceForEdge(
        node_id="argument_john_chrysostoms_homiletic_argument_for_free_will_ea97cb61",
        node_label="John Chrysostom's Homiletic Argument for Free Will",
        source_id="sc79_chrysostomus_de_providentia",
        source_label="Chrysostomus, De Providentia",
        reason="Primary source: Chrysostom De Providentia. Direct textual source for his argument that providence presupposes human free will.",
    ),
    # --- Leibniz ---
    SourceForEdge(
        node_id="argument_liberty_of_spontaneity_7e1184bf",
        node_label="Liberty of Spontaneity",
        source_id="work_leibniz_theodicee_1710",
        source_label="Essais de Théodicée",
        reason="Primary source: Leibniz Theodicée §§288-310. Leibniz's canonical articulation of liberty as spontaneity.",
    ),
    # --- Origen ---
    SourceForEdge(
        node_id="argument_origens_de_principiis_argument_for_free_will_93d043fc",
        node_label="Origen's De Principiis Argument for Free Will",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Primary source: Origen De Principiis III.1. Direct textual source.",
    ),
    SourceForEdge(
        node_id="argument_origen_free_will_theodicy_6f9d8a3c",
        node_label="Origen's Free Will Theodicy Against Gnosticism",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Primary source: Origen De Principiis II.9, III.1. Anti-Gnostic theodicy grounded in free will.",
    ),
    # --- Parmenides (preserved in DL) ---
    SourceForEdge(
        node_id="argument_parmenides_necessity_argument_4e8e0f34",
        node_label="Parmenides' Necessity Argument",
        source_id="work_diogenes_laertius_lives",
        source_label="Diogenes Laertius, Lives of Eminent Philosophers",
        reason="Doxographic source: DL IX.21-23. Primary KG proxy preserving Parmenidean metaphysics of necessity.",
    ),
    # --- Plato ---
    SourceForEdge(
        node_id="argument_platos_timaeus_necessity_argument_526846fa",
        node_label="Plato's Timaeus Necessity Argument",
        source_id="work_plato_timaeus",
        source_label="Plato, Timaeus",
        reason="Primary source: Plato Timaeus 47e-48a, 56c-57c. Direct textual source for necessity (ananke) in cosmology.",
    ),
    # --- Stoic (Dog and Cart, preserved in Epictetus) ---
    SourceForEdge(
        node_id="argument_the_dog_and_cart_argument_9ba60714",
        node_label="The Dog and Cart Argument",
        source_id="work_epictetus_enchiridion",
        source_label="Enchiridion (Ἐγχειρίδιον) - Epictetus",
        reason="Ancient source: Hippolytus Refutatio I.21 (original); Epictetus Enchiridion 8 preserves the Stoic compatibilist logic. Best available KG source.",
    ),
    # --- Master Argument (Diodorus, preserved in Cicero/Epictetus) ---
    SourceForEdge(
        node_id="argument_the_master_argument_kurieuon_logos_355f4d3f",
        node_label="The Master Argument (Kurieuon Logos)",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Ancient sources: Cicero De Fato 12-17, Epictetus Discourses II.19. Cicero's De Fato is the best KG proxy for the logical structure of Diodorus' argument.",
    ),
    # --- Zeno paradox analogy (Alexander) ---
    SourceForEdge(
        node_id="argument_zeno_paradox_analogy_alex",
        node_label="Zeno's Paradox Analogy (Alexander)",
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        source_label="De Fato (Περὶ Εἱμαρμένης / On Fate)",
        reason="Primary source: Alexander of Aphrodisias De Fato ch. 25. Direct textual source.",
    ),
]
EDGES_BATCH_05C: list[SourceForEdge] = [
    # --- Proclus ---
    SourceForEdge(
        node_id="concept_acting_final_cause",
        node_label="Acting Final Cause (Providence)",
        source_id="work_proclus_tria_opuscula_c9a8e4b3",
        source_label="Tria Opuscula (Three Essays) - Proclus",
        reason="Proclus Tria Opuscula (De Providentia, De Fato) treats providential final causation directly.",
    ),
    SourceForEdge(
        node_id="concept_pronoia_levels_proclus_a6d8c9b4",
        node_label="Levels of Providence (Proclean)",
        source_id="work_proclus_tria_opuscula_c9a8e4b3",
        source_label="Tria Opuscula (Three Essays) - Proclus",
        reason="Primary source: Proclus De Providentia. Hierarchical providence levels are the central topic.",
    ),
    # --- Alexander of Aphrodisias ---
    SourceForEdge(
        node_id="concept_incompatibilism_ancient_o5p6q7r8",
        node_label="Ancient Incompatibilism",
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        source_label="De Fato (Περὶ Εἱμαρμένης / On Fate)",
        reason="Alexander De Fato is the canonical ancient incompatibilist text, arguing fate is incompatible with moral responsibility.",
    ),
    SourceForEdge(
        node_id="concept_axioma_dignity_alex",
        node_label="Human Dignity / ἀξίωμα (Alexander)",
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        source_label="De Fato (Περὶ Εἱμαρμένης / On Fate)",
        reason="Primary source: Alexander De Fato ch. 15-16. Human dignity requires genuine choice.",
    ),
    SourceForEdge(
        node_id="concept_self_happiness_alex",
        node_label="Self-Achieved Happiness / δι᾽ αὑτῶν εὐδαιμονεῖν (Alexander)",
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        source_label="De Fato (Περὶ Εἱμαρμένης / On Fate)",
        reason="Primary source: Alexander De Fato ch. 20. Self-achieved happiness as argument against fatalism.",
    ),
    SourceForEdge(
        node_id="concept_natural_character_e5f6g7h8",
        node_label="Natural Character (Φύσις, Ingenium)",
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        source_label="De Fato (Περὶ Εἱμαρμένης / On Fate)",
        reason="Alexander De Fato ch. 6-8 discusses natural character (physis) and its role in action without necessitation.",
    ),
    # --- Pseudo-Plutarch ---
    SourceForEdge(
        node_id="concept_apotelesmatic_0y5z7b43",
        node_label="Apotelesmatic Astrology",
        source_id="work_de_fato_pseudo_plutarch_a8c6d4e2",
        source_label="De Fato (On Fate) - Pseudo-Plutarch",
        reason="Pseudo-Plutarch De Fato ch. 2-3 discusses astrological fate and apotelesmatic influence.",
    ),
    SourceForEdge(
        node_id="concept_genethlialogia_9x4y6a32",
        node_label="Natal Astrology (Genethlialogia)",
        source_id="work_de_fato_pseudo_plutarch_a8c6d4e2",
        source_label="De Fato (On Fate) - Pseudo-Plutarch",
        reason="Pseudo-Plutarch De Fato discusses genethlialogical (natal-chart) astrology in the context of fate.",
    ),
    # --- Cicero ---
    SourceForEdge(
        node_id="concept_pithanotes_7v2w4y10",
        node_label="Probability/Plausibility (Pithanotēs)",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Cicero De Fato preserves Carneades' probabilism (pithanon). Also Academica II.",
    ),
    # --- Origen / De Principiis ---
    SourceForEdge(
        node_id="concept_theodicy_christian",
        node_label="Christian Theodicy",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Origen De Principiis II.9, III.1 develops the first systematic Christian theodicy grounded in free will.",
    ),
    SourceForEdge(
        node_id="concept_grace_freedom_synergy",
        node_label="Grace-Freedom Synergy (συνεργία)",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Origen De Principiis III.1 articulates synergy between divine grace and human free will.",
    ),
    SourceForEdge(
        node_id="concept_synergism",
        node_label="Synergism (Synergy)",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Origen De Principiis III.1.18-24. Synergism as cooperation of divine and human agency.",
    ),
    SourceForEdge(
        node_id="concept_pedagogical_theodicy",
        node_label="Pedagogical Theodicy (ἀφορμὴ προκοπῆς)",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Origen De Principiis II.9-11, III.1. Evil as occasion for moral progress in Origen's pedagogical theodicy.",
    ),
    # --- Methodius ---
    SourceForEdge(
        node_id="concept_concupiscence_epithumia_transmitted_bd8e2fc9",
        node_label="Concupiscence (Epithumia) as Transmitted Consequence - Methodian Hamartiology",
        source_id="work_methodius_de_autexusio_4c37c892",
        source_label="De autexusio (On Free Will)",
        reason="Primary source: Methodius De Autexusio. Discusses concupiscence as transmitted consequence without destroying free will.",
    ),
    SourceForEdge(
        node_id="concept_death_therapeutic_remedy_methodius_5eaaf3a2",
        node_label="Death as Therapeutic Remedy (Not Punishment) - Methodian Theodicy",
        source_id="work_methodius_de_autexusio_4c37c892",
        source_label="De autexusio (On Free Will)",
        reason="Primary source: Methodius De Autexusio. Death reinterpreted as divine therapeutic remedy.",
    ),
    SourceForEdge(
        node_id="concept_evil_quality_accident_methodius_dae1b112",
        node_label="Evil as Quality/Accident (Not Substance) - Methodian Theodicy",
        source_id="work_methodius_de_autexusio_4c37c892",
        source_label="De autexusio (On Free Will)",
        reason="Primary source: Methodius De Autexusio. Evil as quality (poiotes) not substance, preserving free will.",
    ),
    # --- Irenaeus ---
    SourceForEdge(
        node_id="concept_dynamic_anthropology_temporal",
        node_label="Dynamic Anthropology - Temporal Development toward Perfection",
        source_id="work_irenaeus_adversus_haereses_book4",
        source_label="Irenaeus, Adversus Haereses Book 4",
        reason="Primary source: Irenaeus AH IV.38. Humans created imperfect but progressing toward perfection.",
    ),
    SourceForEdge(
        node_id="concept_agathos_vs_teleios_distinction",
        node_label="Ἀγαθός vs. Τέλειος Distinction (Good vs. Perfect)",
        source_id="work_irenaeus_adversus_haereses_book4",
        source_label="Irenaeus, Adversus Haereses Book 4",
        reason="Primary source: Irenaeus AH IV.38.3. Distinction between being good (agathos) and being perfect (teleios).",
    ),
    SourceForEdge(
        node_id="concept_nepios_adam_infant_doctrine",
        node_label="Νήπιος Doctrine - Adam as Infant",
        source_id="work_irenaeus_adversus_haereses_book4",
        source_label="Irenaeus, Adversus Haereses Book 4",
        reason="Primary source: Irenaeus AH IV.38.1-2. Adam as nepios (infant) needing growth.",
    ),
    SourceForEdge(
        node_id="concept_anakephalaiosis_recapitulation",
        node_label="Ἀνακεφαλαίωσις - Eschatological Recapitulation",
        source_id="work_irenaeus_adversus_haereses_book3",
        source_label="Irenaeus, Adversus Haereses Book 3",
        reason="Primary source: Irenaeus AH III.18.1, III.21.10-22.4. Foundational recapitulation passages.",
    ),
    SourceForEdge(
        node_id="concept_theosis",
        node_label="Theosis (Deification)",
        source_id="work_irenaeus_adversus_haereses_book5",
        source_label="Irenaeus, Adversus Haereses Book 5",
        reason="Primary source: Irenaeus AH V.Praef, V.6.1. 'God became man so that man might become God.'",
    ),
    # --- Augustine ---
    SourceForEdge(
        node_id="concept_original_sin",
        node_label="Original Sin (Peccatum Originale)",
        source_id="work_de_libero_arbitrio",
        source_label="De Libero Arbitrio Voluntatis (On Free Choice of the Will)",
        reason="Augustine DLA III.19-22 develops the doctrine of original sin. Earliest systematic treatment in KG.",
    ),
    SourceForEdge(
        node_id="concept_peccatum_originans",
        node_label="Peccatum Originans (Originating Sin)",
        source_id="work_de_libero_arbitrio",
        source_label="De Libero Arbitrio Voluntatis (On Free Choice of the Will)",
        reason="Augustine DLA III discusses the originating act of sin (peccatum originans) distinct from inherited guilt.",
    ),
    SourceForEdge(
        node_id="concept_predestination_augustinian",
        node_label="Predestination (Augustinian Double Predestination)",
        source_id="work_ad_simplicianum",
        source_label="Ad Simplicianum (To Simplician)",
        reason="Primary source: Augustine Ad Simplicianum I.2 (396 CE). First articulation of unconditional predestination.",
    ),
    SourceForEdge(
        node_id="concept_gratia_cooperans",
        node_label="Gratia Cooperans (Cooperating Grace)",
        source_id="work_augustine_de_gratia_la",
        source_label="De Gratia et Libero Arbitrio (Augustine)",
        reason="Primary source: Augustine De Gratia et Libero Arbitrio XVII.33. Defines cooperating grace.",
    ),
    SourceForEdge(
        node_id="concept_gratia_operans",
        node_label="Gratia Operans (Operating Grace)",
        source_id="work_augustine_de_gratia_la",
        source_label="De Gratia et Libero Arbitrio (Augustine)",
        reason="Primary source: Augustine De Gratia et Libero Arbitrio XVII.33. Defines operating grace.",
    ),
    # --- Stoic (Bobzien, Epictetus, DL) ---
    SourceForEdge(
        node_id="concept_sympathia_universalis_6u1v3x09",
        node_label="Cosmic Sympathy (Sympathia Universalis)",
        source_id="work_bobzien_determinism_freedom_1998",
        source_label="Determinism and Freedom in Stoic Philosophy",
        reason="Bobzien 1998 ch. 1-3 analyses Stoic cosmic sympathy in the context of determinism. Primary scholarly authority in KG.",
    ),
    SourceForEdge(
        node_id="concept_cyclical_return_great_year",
        node_label="Cyclical Return (Great Year)",
        source_id="work_diogenes_laertius_lives",
        source_label="Diogenes Laertius, Lives of Eminent Philosophers",
        reason="DL VII.156 preserves the Stoic doctrine of cyclical return (ekpyrosis and palingenesis).",
    ),
    SourceForEdge(
        node_id="concept_reservation_exceptio_m3n4o5p6",
        node_label="Reservation Clause (Ὑπεξαίρεσις, Exceptio)",
        source_id="work_epictetus_discourses",
        source_label="Discourses (Διατριβαί) - Epictetus",
        reason="Primary source: Epictetus Discourses II.6.9-10. Stoic reservation clause (hupexairesis).",
    ),
    # --- Sextus Empiricus ---
    SourceForEdge(
        node_id="concept_isostheneia_4b7e9c3a",
        node_label="isostheneia (ἰσοσθένεια)",
        source_id="work_sextus_outlines_pyrrhonism_f9a7c8e4",
        source_label="Outlines of Pyrrhonism (Πυρρώνειοι Ὑποτυπώσεις)",
        reason="Primary source: Sextus PH I.8-10. Equipollence (isostheneia) as foundation of Pyrrhonist suspension.",
    ),
    SourceForEdge(
        node_id="concept_epi_ison_in_equal_parts_9e1e47f1",
        node_label="Ἐπὶ ἴσον (Epi Ison) - In Equal Parts",
        source_id="work_sextus_outlines_pyrrhonism_f9a7c8e4",
        source_label="Outlines of Pyrrhonism (Πυρρώνειοι Ὑποτυπώσεις)",
        reason="Primary source: Sextus PH I.190-191. Equal balance (epi ison) of opposing arguments.",
    ),
    # --- Lucretius ---
    SourceForEdge(
        node_id="concept_kinesis_anaitios_uncaused_motion_a7b8c9d0",
        node_label="Kinesis Anaitios (Κίνησις Ἀναίτιος) - Uncaused Motion",
        source_id="work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",
        source_label="De Rerum Natura (On the Nature of Things)",
        reason="Primary source: Lucretius DRN II.216-293. The clinamen as uncaused atomic swerve.",
    ),
    # --- Maimonides ---
    SourceForEdge(
        node_id="concept_hashgachah_o3p4q5r6",
        node_label="Divine Providence (Hashgachah)",
        source_id="work_guide_for_perplexed_maimonides_u5v6w7x8",
        source_label="Guide for the Perplexed (Moreh Nevukhim)",
        reason="Primary source: Maimonides Guide III.17-18. Systematic treatment of divine providence (hashgachah pratit).",
    ),
    # --- Jewish texts ---
    SourceForEdge(
        node_id="concept_yetzer_ha_tov_y7z8a9b0",
        node_label="Good Inclination (Yetzer Ha-Tov)",
        source_id="work_sirach_a3b4c5d6",
        source_label="Wisdom of Sirach (Ecclesiasticus)",
        reason="Sirach 15:14-17 is the key early text on the yetzer and free choice. Best biblical proxy in KG.",
    ),
    # --- Peripatetic ---
    SourceForEdge(
        node_id="concept_metriopatheia_moderation_passions",
        node_label="Metriopatheia (Moderation of Passions)",
        source_id="text_aspasius_in_en",
        source_label="Aspasius - In Ethica Nicomachea",
        reason="Aspasius' commentary on EN II-III develops the Peripatetic doctrine of moderation of passions (metriopatheia).",
    ),
    SourceForEdge(
        node_id="concept_pathetike_holke_emotional_pull",
        node_label="Emotional Pull (Pathētikē Holkē)",
        source_id="pub_graver_2007_stoicism_emotion",
        source_label="Stoicism and Emotion",
        reason="Graver 2007 analyses the Stoic concept of emotional pull (pathētikē holkē) as discussed in Chrysippus. Best scholarly authority in KG.",
    ),
    # --- Plato ---
    SourceForEdge(
        node_id="concept_orphic_zagreus_dionysus_myth",
        node_label="Orphic Zagreus/Dionysus Myth - Anthropological Dualism",
        source_id="work_plato_phaedo",
        source_label="Plato, Phaedo",
        reason="Plato Phaedo 62b, 69c-d alludes to Orphic doctrines on the soul's divine origin. Best available KG proxy.",
    ),
    SourceForEdge(
        node_id="concept_soma_sema_body_tomb_orphic",
        node_label="σῶμα σῆμα (Body as Tomb) - Orphic Doctrine",
        source_id="work_plato_phaedo",
        source_label="Plato, Phaedo",
        reason="Plato Phaedo 62b and Cratylus 400c transmit the soma-sema doctrine. Phaedo is the best KG proxy.",
    ),
    SourceForEdge(
        node_id="concept_two_source_metaphysics_platonist",
        node_label="Two-Source Metaphysics (Platonist)",
        source_id="work_plato_timaeus",
        source_label="Plato, Timaeus",
        reason="Plato Timaeus 47e-48a: two-source metaphysics of Intellect (nous) and Necessity (ananke).",
    ),
    # --- Plotinus ---
    SourceForEdge(
        node_id="concept_undescended_soul_plotinus",
        node_label="Undescended Soul Doctrine - Plotinus's Preservation of Soul's Divinity",
        source_id="work_plotinus_enneads_iv_8",
        source_label="Plotinus, Enneads IV.8 - On the Descent of the Soul into Bodies",
        reason="Primary source: Plotinus Enneads IV.8.8. The undescended part of the soul.",
    ),
    # --- Alcinous ---
    SourceForEdge(
        node_id="concept_hypomnema_school_handbooks_1z6a8c54",
        node_label="School Handbooks (Hypomnemata)",
        source_id="work_didaskalikos_alcinous_2nd_ce_q7r8s9t0",
        source_label="Didaskalikos (Handbook of Platonism)",
        reason="Alcinous' Didaskalikos is itself a school handbook (hypomnema). Exemplifies the genre directly.",
    ),
    # --- Kane ---
    SourceForEdge(
        node_id="concept_self_forming_actions_4r5s6t7u",
        node_label="Self-Forming Actions (SFAs)",
        source_id="work_significance_of_free_will_kane_1i2j3k4l",
        source_label="The Significance of Free Will",
        reason="Formulator: Robert Kane. Primary source: The Significance of Free Will (1996). Direct match.",
    ),
    SourceForEdge(
        node_id="concept_ultimate_responsibility_kane",
        node_label="Ultimate Responsibility (UR)",
        source_id="work_significance_of_free_will_kane_1i2j3k4l",
        source_label="The Significance of Free Will",
        reason="Formulator: Robert Kane. Primary source: The Significance of Free Will (1996). Direct match.",
    ),
    # --- Scholarly works ---
    SourceForEdge(
        node_id="concept_terminology_evolution_greek_latin_y5z6a7b8",
        node_label="Terminology Evolution: Greek → Latin Free Will Vocabulary",
        source_id="pub_dihle_1982_theory_will",
        source_label="The Theory of Will in Classical Antiquity",
        reason="Dihle 1982 is the seminal study of Greek-to-Latin terminological evolution of will/freedom concepts.",
    ),
    SourceForEdge(
        node_id="concept_thelesis_willing_87d2b3cf",
        node_label="Θέλησις (Thelēsis) - Willing/Volition",
        source_id="pub_dihle_1982_theory_will",
        source_label="The Theory of Will in Classical Antiquity",
        reason="Dihle 1982 traces the development of thelesis/voluntas from Greek to Latin philosophy.",
    ),
    SourceForEdge(
        node_id="concept_platonic_vs_christian_original_sin",
        node_label="Platonic Embodiment-as-Sin vs. Christian Original Sin - Comparative Framework",
        source_id="work_frede_free_will_2011",
        source_label="A Free Will: Origins of the Notion in Ancient Thought",
        reason="Frede 2011 compares Platonic and Christian conceptions of embodiment and sin. Best scholarly framework in KG.",
    ),
]
EDGES_BATCH_05D: list[SourceForEdge] = [
    # --- Conceptual evolution nodes (dual sourcing where appropriate) ---
    SourceForEdge(
        node_id="evolution_will_concept_c68f04bd",
        node_label="Evolution of Will (various terms) - Scholarly Debate",
        source_id="pub_dihle_1982_theory_will",
        source_label="The Theory of Will in Classical Antiquity",
        reason="Dihle 1982 is the foundational study of the evolution of the will concept from Homer to Augustine.",
    ),
    SourceForEdge(
        node_id="evolution_will_concept_c68f04bd",
        node_label="Evolution of Will (various terms) - Scholarly Debate",
        source_id="work_frede_free_will_2011",
        source_label="A Free Will: Origins of the Notion in Ancient Thought",
        reason="Frede 2011 is the major counter-thesis to Dihle, arguing the notion of free will emerged in Stoicism.",
    ),
    SourceForEdge(
        node_id="evolution_heimarmene_2b989ed0",
        node_label="Evolution of εἱμαρμένη (heimarmenê)",
        source_id="work_bobzien_determinism_freedom_1998",
        source_label="Determinism and Freedom in Stoic Philosophy",
        reason="Bobzien 1998 ch. 2 traces the evolution of heimarmene from Homer through Stoic physics.",
    ),
    SourceForEdge(
        node_id="evolution_eph_hemin_6284cf6d",
        node_label="Evolution of τὸ ἐφ' ἡμῖν (to eph' hêmin)",
        source_id="pub_labarriere_2009_eph_hemin",
        source_label="De « ce qui dépend de nous »",
        reason="Labarrière 2009 is a dedicated study of the evolution of to eph' hêmin. Direct match.",
    ),
    # --- Debates ---
    SourceForEdge(
        node_id="debate_christian_gnostic_freedom",
        node_label="Christian-Gnostic Debate on Freedom",
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        source_label="De Principiis (Περὶ Ἀρχῶν) - Origen",
        reason="Origen De Principiis III.1 is the central anti-Gnostic defense of free will. Also Irenaeus AH, but Origen is more systematic.",
    ),
    # --- Schools ---
    SourceForEdge(
        node_id="school_academics",
        node_label="Academic School (Ἀκαδημία) - New Academy",
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        source_label="De Fato (On Fate)",
        reason="Cicero De Fato is the primary source preserving New Academic arguments on fate and free will (Carneades).",
    ),
    SourceForEdge(
        node_id="school_stoicism",
        node_label="Stoicism (Στοά)",
        source_id="work_bobzien_determinism_freedom_1998",
        source_label="Determinism and Freedom in Stoic Philosophy",
        reason="Bobzien 1998 is the authoritative scholarly treatment of Stoic determinism and compatibilism. Primary KG authority.",
    ),
    # --- Synthesis ---
    SourceForEdge(
        node_id="concept_ditte_hamartia_double_sin_plotinus",
        node_label="διττὴ ἁμαρτία (Double Sin) - Plotinus's Synthesis of Embodiment Doctrines",
        source_id="work_plotinus_enneads_iv_8",
        source_label="Plotinus, Enneads IV.8 - On the Descent of the Soul into Bodies",
        reason="Primary source: Plotinus Enneads IV.8.5. The 'double sin' (tolma + embodiment) as synthesis of Platonic doctrines.",
    ),
]

FLAGS_BATCH_05B: list[ManualFlag] = [
    ManualFlag(
        node_id="argument_hobbess_rejection_of_immaterial_soul_02b7bcda",
        node_label="Hobbes's Rejection of Immaterial Soul",
        reason="Primary source: Hobbes Leviathan ch. 34, 46. No Hobbes works in KG.",
    ),
    ManualFlag(
        node_id="argument_human_will_lacks_efficacy_45522d03",
        node_label="Human Will Lacks Efficacy",
        reason="Likely Reformation-era argument (Luther/Calvin). Primary source unidentifiable from metadata alone. Requires editorial review.",
    ),
    ManualFlag(
        node_id="argument_humean_compatibilism_3y7t8u46",
        node_label="Hume's Compatibilist Argument",
        reason="Primary source: Hume Enquiry VIII, Treatise II.iii. No Hume works in KG.",
    ),
    ManualFlag(
        node_id="argument_infinite_will_argument_f19a66ed",
        node_label="Infinite Will Argument",
        reason="Primary source: Descartes Meditations IV. No Descartes works in KG.",
    ),
    ManualFlag(
        node_id="argument_kantian_third_antinomy_6b0w1x79",
        node_label="Kant's Third Antinomy on Freedom",
        reason="Primary source: Kant Critique of Pure Reason A444/B472. No Kant works in KG.",
    ),
    ManualFlag(
        node_id="argument_liberty_as_absence_of_external_impediment_4587b29b",
        node_label="Liberty as Absence of External Impediment",
        reason="Primary source: Hobbes Leviathan ch. 21. No Hobbes works in KG.",
    ),
    ManualFlag(
        node_id="argument_lockean_analysis_2x6s7t35",
        node_label="Locke's Analysis of Freedom",
        reason="Primary source: Locke Essay II.xxi. No Locke works in KG.",
    ),
    ManualFlag(
        node_id="argument_lockes_suspension_of_desire_e45dc337",
        node_label="Locke's Suspension of Desire",
        reason="Primary source: Locke Essay II.xxi.47-52. No Locke works in KG.",
    ),
    ManualFlag(
        node_id="argument_lutheran_bondage_argument_6r0m1n79",
        node_label="Luther's Bondage of Will Argument",
        reason="Primary source: Luther De Servo Arbitrio (1525). No Luther works in KG.",
    ),
    ManualFlag(
        node_id="argument_molinism_and_middle_knowledge_3d718eca",
        node_label="Molinism and Middle Knowledge",
        reason="Primary source: Molina Concordia (1588). No Molina works in KG.",
    ),
    ManualFlag(
        node_id="argument_molinist_middle_knowledge_8t2o3p91",
        node_label="Molinist Middle Knowledge Argument",
        reason="Primary source: Molina Concordia (1588). No Molina works in KG. Possible near-duplicate with argument_molinism_and_middle_knowledge.",
    ),
    ManualFlag(
        node_id="argument_ockhams_divine_power_argument_a0e19729",
        node_label="Ockham's Divine Power Argument",
        reason="Primary source: Ockham Quodlibeta Septem. No Ockham works in KG.",
    ),
    ManualFlag(
        node_id="argument_ockhams_rejection_of_necessitation_33c255bf",
        node_label="Ockham's Rejection of Necessitation",
        reason="Primary source: Ockham Ordinatio I d.38. No Ockham works in KG.",
    ),
    ManualFlag(
        node_id="argument_pascals_wager_and_voluntarism_4519ad75",
        node_label="Pascal's Wager and Voluntarism",
        reason="Primary source: Pascal Pensées §233. No Pascal works in KG.",
    ),
    ManualFlag(
        node_id="argument_pelagiuss_argument_for_human_capacity_006c0a58",
        node_label="Pelagius's Argument for Human Capacity",
        reason="Primary source: Pelagius Ad Demetriadem. No Pelagius works in KG.",
    ),
    ManualFlag(
        node_id="argument_pseudodionysiuss_hierarchical_causation_argument_e0d73eb9",
        node_label="Pseudo-Dionysius's Hierarchical Causation Argument",
        reason="Primary source: Pseudo-Dionysius De Divinis Nominibus IV. No Pseudo-Dionysius works in KG.",
    ),
    ManualFlag(
        node_id="argument_reidian_agent_causation_4z8u9v57",
        node_label="Reid's Agent Causation Argument",
        reason="Primary source: Thomas Reid Essays on Active Powers (1788). No Reid works in KG.",
    ),
    ManualFlag(
        node_id="argument_scotuss_synchronic_contingency_e39fc978",
        node_label="Scotus's Synchronic Contingency",
        reason="Primary source: Duns Scotus Lectura I d.39. No Scotus works in KG.",
    ),
    ManualFlag(
        node_id="argument_scotuss_two_affections_of_the_will_bb060e3d",
        node_label="Scotus's Two Affections of the Will",
        reason="Primary source: Duns Scotus Ordinatio II d.6, drawing on Anselm De Casu Diaboli. No Scotus works in KG.",
    ),
    ManualFlag(
        node_id="argument_scotuss_voluntarism_501f1bf6",
        node_label="Scotus's Voluntarism",
        reason="Primary source: Duns Scotus Ordinatio IV d.49. No Scotus works in KG.",
    ),
    ManualFlag(
        node_id="argument_spinozas_free_man_ethics_b0940e69",
        node_label="Spinoza's Free Man Ethics",
        reason="Primary source: Spinoza Ethics IV P67-73. No Spinoza works in KG.",
    ),
    ManualFlag(
        node_id="argument_spinozan_necessitarianism_9u3p4q02",
        node_label="Spinoza's Necessitarian Argument",
        reason="Primary source: Spinoza Ethics I P29, P33. No Spinoza works in KG.",
    ),
    ManualFlag(
        node_id="argument_tertullians_antimarcionite_argument_for_free_will_f49cad73",
        node_label="Tertullian's Anti-Marcionite Argument for Free Will",
        reason="Primary source: Tertullian Adversus Marcionem II.5-7. No Tertullian works in KG.",
    ),
    ManualFlag(
        node_id="argument_vision_in_god_and_freedom_2a29f35e",
        node_label="Vision in God and Freedom",
        reason="Primary source: Malebranche Recherche de la vérité. No Malebranche works in KG.",
    ),
]
FLAGS_BATCH_05C: list[ManualFlag] = [
    ManualFlag(
        node_id="concept_potentia_absoluta_ordinata_k9l0m1n2",
        node_label="Absolute and Ordained Power (Potentia Absoluta et Ordinata)",
        reason="Medieval concept (Ockham/Scotus). No Ockham or Scotus works in KG.",
    ),
    ManualFlag(
        node_id="concept_kasb_acquisition_e9f0g1h2",
        node_label="Acquisition (Kasb/Iktisab)",
        reason="Islamic theology concept (Al-Ash'ari). No Islamic theological works in KG.",
    ),
    ManualFlag(
        node_id="concept_autonomy_8j2e3f91",
        node_label="Autonomy",
        reason="Modern concept formalized by Kant (Groundwork III). No Kant works in KG.",
    ),
    ManualFlag(
        node_id="concept_bondage_of_will_1c5x6y24",
        node_label="Bondage of the Will (Servum Arbitrium)",
        reason="Primary source: Luther De Servo Arbitrio (1525). No Luther works in KG.",
    ),
    ManualFlag(
        node_id="concept_bypassing_1y2z3a4b",
        node_label="Bypassing",
        reason="Contemporary philosophy of action concept. No relevant contemporary works in KG.",
    ),
    ManualFlag(
        node_id="concept_categorical_imperative_9k3f4g02",
        node_label="Categorical Imperative",
        reason="Primary source: Kant Groundwork of the Metaphysics of Morals. No Kant works in KG.",
    ),
    ManualFlag(
        node_id="concept_diachronic_contingency_w1x2y3z4",
        node_label="Diachronic Contingency",
        reason="Medieval concept (Aquinas/Scotus distinction). No Aquinas or Scotus works in KG.",
    ),
    ManualFlag(
        node_id="concept_intellectus_c1d2e3f4",
        node_label="Intellect (Intellectus)",
        reason="Medieval faculty psychology (Aquinas ST I q.79). No Aquinas works in KG.",
    ),
    ManualFlag(
        node_id="concept_intellectualism_medieval_i3j4k5l6",
        node_label="Intellectualism (Medieval)",
        reason="Medieval doctrine (Aquinas). No Aquinas works in KG.",
    ),
    ManualFlag(
        node_id="concept_scientia_media_2d6y7z35",
        node_label="Middle Knowledge (Scientia Media)",
        reason="Primary source: Molina Concordia (1588). No Molina works in KG.",
    ),
    ManualFlag(
        node_id="concept_matter_adaptability_pneumatic_receptivity",
        node_label="Matter's Adaptability and Pneumatic Receptivity",
        reason="Stoic/Irenaeus concept. Primary textual source unclear from metadata. Requires editorial review.",
    ),
    ManualFlag(
        node_id="concept_praemotio_physica_3e7z8a46",
        node_label="Physical Premotion (Praemotio Physica)",
        reason="Dominican/Thomist doctrine (Bañez). No Bañez or Thomist works in KG.",
    ),
    ManualFlag(
        node_id="concept_readiness_potential_3a4b5c6d",
        node_label="Readiness Potential (Bereitschaftspotential)",
        reason="Neuroscience concept (Libet 1983). No Libet works in KG.",
    ),
    ManualFlag(
        node_id="concept_synchronic_contingency_s7t8u9v0",
        node_label="Synchronic Contingency",
        reason="Primary source: Duns Scotus Lectura I d.39. No Scotus works in KG.",
    ),
    ManualFlag(
        node_id="concept_synderesis_g5h6i7j8",
        node_label="Synderesis",
        reason="Medieval concept (Jerome/Aquinas). No relevant Medieval works in KG.",
    ),
    ManualFlag(
        node_id="concept_transcendental_freedom_7i1d2e80",
        node_label="Transcendental Freedom",
        reason="Primary source: Kant CPR A533/B561. No Kant works in KG.",
    ),
    ManualFlag(
        node_id="concept_voluntarism_medieval_m7n8o9p0",
        node_label="Voluntarism (Medieval)",
        reason="Medieval doctrine (Scotus). No Scotus works in KG.",
    ),
    ManualFlag(
        node_id="concept_theurgical_soteriology_iamblichus",
        node_label="Theurgical Soteriology - Iamblichean Ritual Practice",
        reason="Primary source: Iamblichus De Mysteriis. Only De Anima in KG, which does not directly address theurgy.",
    ),
]
FLAGS_BATCH_05D: list[ManualFlag] = [
    ManualFlag(
        node_id="controversy_de_auxiliis_2n6i7j35",
        node_label="De Auxiliis Controversy",
        reason="16th-century Jesuit-Dominican debate. No Molina, Bañez, or relevant works in KG.",
    ),
    ManualFlag(
        node_id="controversy_hobbes_bramhall_3o7j8k46",
        node_label="Hobbes vs. Bramhall Debate on Liberty and Necessity",
        reason="Primary sources: Hobbes Of Liberty and Necessity, Bramhall Vindication. No Hobbes/Bramhall works in KG.",
    ),
    ManualFlag(
        node_id="controversy_hume_reid_4p8k9l57",
        node_label="Hume vs. Reid on Causation and Free Will",
        reason="Primary sources: Hume Enquiry VIII, Reid Essays on Active Powers. No Hume/Reid works in KG.",
    ),
    ManualFlag(
        node_id="controversy_luther_erasmus_1m5h6i24",
        node_label="Luther vs. Erasmus Debate on Free Will",
        reason="Primary sources: Erasmus De Libero Arbitrio, Luther De Servo Arbitrio. No Luther/Erasmus works in KG.",
    ),
    ManualFlag(
        node_id="controversy_synod_of_dort_5q9l0m68",
        node_label="Synod of Dort",
        reason="1618-19 Reformed synod. No Canons of Dort or related works in KG.",
    ),
    ManualFlag(
        node_id="debate_reason_vs_will_830c90c2",
        node_label="Intellectualism vs Voluntarism",
        reason="Medieval debate (Aquinas vs Scotus). No Aquinas or Scotus works in KG. Possible near-duplicate with 'Intellectualism vs Voluntarism Debate'.",
    ),
    ManualFlag(
        node_id="debate_randomness_objection_ae34a974",
        node_label="The Randomness/Luck Objection to Libertarianism",
        reason="Contemporary analytic debate. No dedicated contemporary works in KG addressing this specific objection.",
    ),
    ManualFlag(
        node_id="group_pharisees_w1x2y3z4",
        node_label="Pharisees",
        reason="Primary sources: Josephus Antiquities XIII, XVIII; Acts 23:8. No Josephus or NT works in KG. Deuteronomy is foundational to Pharisaic interpretation but does not document the Pharisees as a group.",
    ),
    ManualFlag(
        node_id="group_sadducees_a5b6c7d8",
        node_label="Sadducees",
        reason="Primary sources: Josephus Antiquities XIII, XVIII; Acts 23:8. No Josephus or NT works in KG.",
    ),
]


# ============================================================================
# Execution
# ============================================================================

async def ensure_edge(
    conn: asyncpg.Connection, edge: SourceForEdge, confirm: bool
) -> bool:
    """Add a source_for edge if it doesn't already exist."""
    exists = await conn.fetchval(f"""
        SELECT 1 FROM {SCHEMA}.kg_edges
        WHERE source_id = $1 AND target_id = $2 AND relation = 'source_for'
    """, edge.source_id, edge.node_id)
    if exists:
        return False
    if confirm:
        await conn.execute(f"""
            INSERT INTO {SCHEMA}.kg_edges (source_id, target_id, relation, metadata)
            VALUES ($1, $2, 'source_for', $3::jsonb)
        """, edge.source_id, edge.node_id, json.dumps({
            "added_by": RUN_TAG,
            "reason": edge.reason,
        }))
    return True


async def flag_node(
    conn: asyncpg.Connection, flag: ManualFlag, confirm: bool
) -> None:
    """Add provenance_status metadata to a flagged node."""
    if confirm:
        await conn.execute(f"""
            UPDATE {SCHEMA}.kg_nodes
            SET metadata = COALESCE(metadata, '{{}}'::jsonb) || $2::jsonb,
                updated_at = NOW()
            WHERE node_id = $1
        """, flag.node_id, json.dumps({
            "provenance_status": "unsupported - pending manual review",
            "provenance_note": flag.reason,
            "provenance_batch": RUN_TAG,
        }))


def generate_reports(
    all_edges: list[SourceForEdge],
    all_flags: list[ManualFlag],
    edges_added: int,
    edges_skipped: int,
    confirm: bool,
) -> None:
    ts = datetime.now(UTC).isoformat()

    json_data = {
        "generated": ts,
        "run_tag": RUN_TAG,
        "applied": confirm,
        "stats": {
            "edges_added": edges_added,
            "edges_skipped_existing": edges_skipped,
            "flagged_manual_review": len(all_flags),
        },
        "edges": [
            {
                "node_id": e.node_id,
                "node_label": e.node_label,
                "source_id": e.source_id,
                "source_label": e.source_label,
                "reason": e.reason,
            }
            for e in all_edges
        ],
        "flags": [
            {
                "node_id": f.node_id,
                "node_label": f.node_label,
                "reason": f.reason,
            }
            for f in all_flags
        ],
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(json_data, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# KG Manual Review Batch 05 — Provenance Edges",
        "",
        f"Generated: {ts}",
        f"Run tag: `{RUN_TAG}`",
        f"Applied: {confirm}",
        "",
        "## Summary",
        "",
        f"- source_for edges added: {edges_added}",
        f"- Edges skipped (already exist): {edges_skipped}",
        f"- Flagged for manual review: {len(all_flags)}",
        "",
        "## Edges Added",
        "",
    ]
    for e in all_edges:
        lines.append(f"- **{e.node_label}** (`{e.node_id}`)")
        lines.append(f"  - source: `{e.source_label}` (`{e.source_id}`)")
        lines.append(f"  - reason: {e.reason}")

    lines.extend(["", "## Flagged for Manual Review", ""])
    for f in all_flags:
        lines.append(f"- **{f.node_label}** (`{f.node_id}`)")
        lines.append(f"  - reason: {f.reason}")

    REPORT_MD.write_text("\n".join(lines) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    confirm = args.confirm

    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn=dsn, statement_cache_size=0)

    try:
        all_edges = (
            EDGES_TO_ADD + EDGES_BATCH_05B + EDGES_BATCH_05C + EDGES_BATCH_05D
        )
        all_flags = (
            MANUAL_FLAGS + FLAGS_BATCH_05B + FLAGS_BATCH_05C + FLAGS_BATCH_05D
        )

        print(f"{'DRY RUN' if not confirm else 'LIVE RUN'} — {RUN_TAG}")
        print(f"Edges to process: {len(all_edges)}")
        print(f"Flags to process: {len(all_flags)}")

        edges_added = 0
        edges_skipped = 0

        async with conn.transaction():
            for edge in all_edges:
                if await ensure_edge(conn, edge, confirm):
                    edges_added += 1
                else:
                    edges_skipped += 1

            for flag in all_flags:
                await flag_node(conn, flag, confirm)

            if not confirm:
                raise Exception("DRY RUN — rolling back")

    except Exception as e:
        if "DRY RUN" in str(e):
            pass
        else:
            raise
    finally:
        print(f"Edges added: {edges_added}")
        print(f"Edges skipped (existing): {edges_skipped}")
        print(f"Flagged: {len(all_flags)}")

        all_edges_list = (
            EDGES_TO_ADD + EDGES_BATCH_05B + EDGES_BATCH_05C + EDGES_BATCH_05D
        )
        all_flags_list = (
            MANUAL_FLAGS + FLAGS_BATCH_05B + FLAGS_BATCH_05C + FLAGS_BATCH_05D
        )
        generate_reports(all_edges_list, all_flags_list, edges_added, edges_skipped, confirm)
        print(f"Reports: {REPORT_JSON}")

        await conn.close()

    if not confirm:
        print("\nRe-run with --confirm to apply changes.")


if __name__ == "__main__":
    asyncio.run(main())
