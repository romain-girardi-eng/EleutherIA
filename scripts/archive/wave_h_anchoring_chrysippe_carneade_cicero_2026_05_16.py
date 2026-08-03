#!/usr/bin/env python3
"""Wave H — Ancrage Chrysippe / Carnéade / Cicéron — 2026-05-16.

Audit-fix wave addressing the comprehensive KG audit's #1 finding:
Chrysippean and Carneadean argument nodes (≈89 total) frequently lack
proper anchoring to specific transmission passages, despite Cicero
(*De Fato* / *De Divinatione* / *De Natura Deorum*), Plutarque (*De
Stoic. Rep.*), Gellius (*NA* VII.2), Diogène Laërce (*Vies* VII), and
Eusèbe (*PE* VI/XV) being the canonical witnesses.

The script:

1. **H1 — Audit**: scans all argument nodes whose id/label contains
   ``chrysipp``, ``carnead`` or ``cafma``; computes for each node the
   number of outgoing ``cites_primary_source`` and ``evidenced_by``
   edges whose target is a passage node. Writes the sorted-ascending
   report to ``data/kg/reports/wave_h_anchoring_audit_2026_05_16.json``.

2. **H2 — Anchor**: for each under-anchored argument, adds
   ``cites_primary_source`` edges to specific, verified transmission
   passage IDs. The mapping is taken from Long-Sedley (LS 1987),
   Bobzien 1998 (*Determinism and Freedom in Stoic Philosophy*), and
   Amand 1945 (*Fatalisme et liberté dans l'Antiquité grecque*).

3. **H3 — Cicero transmission**: for arguments where Cicero's *De
   Fato* / *De Divinatione* is the transmission witness, adds a
   ``person_cicero → discusses → argument`` edge with role=transmitter
   so retrieval queries find Cicero as transmitter of the doctrine.
   The ontology permits ``discusses`` from person to argument.

ZERO fabricated text. All target passage IDs verified to exist in
``data/kg/nodes.jsonl`` BEFORE edge insertion; mismatches are
recorded under ``skipped_no_passage`` and never emitted.

Idempotent: signatures ``(source, relation, target, wave)`` are
deduplicated against existing edges; rerunning the script is a no-op.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
REPORTS_DIR = ROOT / "data" / "kg" / "reports"
REPORT_PATH = REPORTS_DIR / "wave_h_anchoring_audit_2026_05_16.json"

WAVE_TAG = "wave_h_anchoring_chrysippe_carneade_cicero_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")

CICERO_PERSON_ID = "person_cicero_marcus_tullius_106_43bce_a8f3d2c1"


# ---------------------------------------------------------------------------
# Canonical transmission mapping
#
# Each anchor entry binds an argument id (or a doctrinal cluster keyed by id
# prefix) to a list of verified passage ids. Scholarship column documents
# the canonical secondary source justifying the binding. All passage ids in
# this map were verified to exist via grep against data/kg/nodes.jsonl on
# 2026-05-16 prior to encoding.
# ---------------------------------------------------------------------------


def _cic_fat(*paragraphs: int) -> list[str]:
    return [f"passage_cic_fat_{p}" for p in paragraphs]


def _cic_div(*paragraphs: int) -> list[str]:
    return [f"passage_cic_div_{p}" for p in paragraphs]


def _cic_nd(*paragraphs: int) -> list[str]:
    return [f"passage_cic_nat_deor_{p}" for p in paragraphs]


def _gellius_vii_2(*subs: int | str) -> list[str]:
    return [f"passage_gellius_na_vii_2_7_2_{s}" for s in subs]


def _plut_sr(*paragraphs: int) -> list[str]:
    return [f"passage_plut_stoic_rep_{p}" for p in paragraphs]


def _dl_vii(*paragraphs: int) -> list[str]:
    return [f"passage_dl_lives_7_1_{p}" for p in paragraphs]


def _eus_pe_vi_6(*subs: int) -> list[str]:
    return [f"passage_eusebius_praep_ev_6_6_{s}" for s in subs]


# Specific per-argument anchor specs.
# Each tuple: (argument_id, passages, transmission_role, scholarship)
ANCHOR_SPECS: list[tuple[str, list[str], str, str]] = [
    # === CHRYSIPPUS — cylinder analogy / internal vs external causation
    (
        "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "witness",
        "Long-Sedley LS 62C-D (Cic. Fat. 39-43) + LS 62D (Gell. NA VII.2.6-13); Bobzien 1998 ch. 6",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_s_compatibilism_3",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "reconstruction",
        "Bobzien 1998 ch. 6 (cylinder/cone analogy)",
    ),
    (
        "scholarly_argument_uster_chrysippus_s_cylinder_and_cone_0",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "reconstruction",
        "Šuster 2018; Bobzien 1998 ch. 6",
    ),
    (
        "scholarly_argument_gourinat_the_cylinder_analogy_and_its_l_3",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "reconstruction",
        "Gourinat 2014 (Cic. Fat. + Gell. NA VII.2)",
    ),
    # === CHRYSIPPUS — causal taxonomy / co-fated events / anti-Lazy-Argument
    (
        "argument_chrysippus_causal_taxonomy",
        _cic_fat(28, 29, 30, 39, 40, 41, 42, 43),
        "witness",
        "Long-Sedley LS 55N-Q + 62; Bobzien 1998 ch. 6 (causal taxonomy)",
    ),
    (
        "scholarly_argument_koch_stoic_causal_theory_and_human__0",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Koch 2015 (Stoic causal theory)",
    ),
    (
        "scholarly_argument_koch_academic_reactions_to_stoic_ca_1",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Koch 2015 (Academic reactions to Stoic causes)",
    ),
    (
        "scholarly_argument_gourinat_chrysippus_s_compatibilism_0",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Gourinat 2014",
    ),
    (
        "scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Gourinat 2014 (Cicero's critique of Chrysippean assent)",
    ),
    # === CHRYSIPPUS — divination / determinism
    (
        "scholarly_argument_bobzien_divination_and_determinism_5",
        _cic_div(125, 126) + _cic_fat(7, 8),
        "reconstruction",
        "Bobzien 1998 ch. 4 (divination as proof of determinism)",
    ),
    (
        "scholarly_argument_bobzien_divination_and_determinism_the_3",
        _cic_div(125, 126) + _cic_fat(7, 8),
        "reconstruction",
        "Bobzien 1998 ch. 4",
    ),
    # === CHRYSIPPUS — compatibilism / modal system
    (
        "scholarly_argument_bobzien_chrysippus_compatibilism_fate__1",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "reconstruction",
        "Bobzien 1998 chs. 5-6",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_compatibilism_and_m_1",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Bobzien 1998 ch. 6 (compatibilism + moral responsibility)",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_modal_logic_and_con_2",
        _cic_fat(7, 8, 9, 13, 14) + _dl_vii(75, 76),
        "reconstruction",
        "Bobzien 1986 *Die stoische Modallogik* + 1998 ch. 3",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_s_arguments_for_cau_1",
        _cic_fat(20, 21, 22, 27, 28, 29, 30),
        "reconstruction",
        "Bobzien 1998 ch. 5 (Principle of Bivalence + causation)",
    ),
    (
        "scholarly_argument_bobzien_stoic_modal_logic_2",
        _cic_fat(12, 13, 14),
        "reconstruction",
        "Bobzien 1986/1998 (Stoic modal logic)",
    ),
    (
        "scholarly_argument_bobzien_stoic_modal_logic_and_continge_2",
        _cic_fat(12, 13, 14),
        "reconstruction",
        "Bobzien 1986/1998 (modal system preserving contingency)",
    ),
    (
        "scholarly_argument_bobzien_stoic_causal_determinism_vs_fa_0",
        _cic_fat(20, 21, 39, 40),
        "reconstruction",
        "Bobzien 1998 chs. 1-2 (causal determinism vs fatalism)",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_and_early_stoics_on_1",
        _cic_fat(20, 21, 39, 40),
        "reconstruction",
        "Bobzien 1998 (one-sided causative-necessitating reading)",
    ),
    # === CHRYSIPPUS — psychology of action / assent / synkatathesis
    (
        "scholarly_argument_bobzien_chrysippus_psychology_of_actio_5",
        _cic_fat(39, 40, 41, 42, 43) + _dl_vii(49, 50, 51),
        "reconstruction",
        "Bobzien 1998 ch. 6 (impressions/assent/impulse chain)",
    ),
    (
        "scholarly_argument_salles_chrysippus_theory_of_action_an_3",
        _cic_fat(39, 40, 41, 42, 43) + _dl_vii(49, 50, 51),
        "reconstruction",
        "Salles 2005 *The Stoics on Determinism and Compatibilism*",
    ),
    (
        "scholarly_argument_eliasson_chrysippus_and_stoic_3",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Eliasson 2008 (eph' hêmin in early Stoicism)",
    ),
    (
        "scholar_position_salles_chrysippus_frankfurt_style",
        _cic_fat(39, 40, 41, 42, 43) + _gellius_vii_2(*range(1, 16)),
        "reconstruction",
        "Salles 2005 (Frankfurt-style compatibilism reading)",
    ),
    (
        "scholar_position_sharples_chrysippus_early_compatibilist",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Sharples 1983 *Alexander of Aphrodisias On Fate* (intro/notes on Chrysippus)",
    ),
    (
        "scholarly_argument_sharples_stoic_providence_and_determini_1",
        _cic_fat(20, 21, 27, 28, 29, 30, 39, 40),
        "reconstruction",
        "Sharples 1983 (Stoic providence/determinism)",
    ),
    (
        "argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Salles 2014 (Epictetus's causal eph' hêmin in continuity with Chrysippus)",
    ),
    (
        "scholarly_argument_uster_stoic_causal_determinism_and_i_1",
        _cic_fat(20, 21, 39, 40),
        "reconstruction",
        "Šuster 2018 (Stoic causal determinism)",
    ),
    (
        "scholarly_argument_f_rst_stoic_compatibilism_chrysippus_2",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Fürst 2022 *Wege zur Freiheit* (Stoic compatibilism)",
    ),
    (
        "scholarly_argument_hall_fate_vs_free_will_in_greek_phi_1",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Hall (Chrysippean reconciliation of fate and responsibility)",
    ),
    (
        "scholarly_argument_telfer_origin_of_autexousia_terminolo_0",
        _dl_vii(40, 41, 42),
        "reconstruction",
        "Telfer (origin of αὐτεξούσιος terminology); cf. DL VII.40-42 Stoic doctrine",
    ),
    (
        "argument_gomez_2014_chrysippus_reactive_compatibilism",
        _cic_fat(39, 40, 41, 42, 43),
        "reconstruction",
        "Gómez 2014 (Chrysippean reactive compatibilism)",
    ),
    (
        "argument_bobzien_2001_b1_synkatathesis_psychology_action",
        _cic_fat(39, 40, 41, 42, 43) + _dl_vii(49, 50, 51),
        "reconstruction",
        "Bobzien 1998 ch. 6 (synkatathesis at center of action-psychology)",
    ),
    # === CARNEADES — CAFMA cluster (5 arguments, each anchored to PE VI.6 + Cic. Fat. 23-25)
    (
        "argument_cafma_carneades_m3n4o5p6",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(5, 8, 16, 18, 19),
        "reconstruction",
        "Amand 1945 ch. III; Long-Sedley LS 70G (Cic. Fat. 23-25)",
    ),
    (
        "argument_cafma_futility_of_effort_8c3d5f21",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(8, 9, 10),
        "reconstruction",
        "Amand 1945 ch. III §IV.2 (PE VI.6.8-10, indolence/futility)",
    ),
    (
        "argument_cafma_futility_of_legislation_9d4e6g32",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(18),
        "reconstruction",
        "Amand 1945 ch. III (PE VI.6.18, abolition of laws)",
    ),
    (
        "argument_cafma_futility_of_sanctions_0e5f7h43",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(12, 13, 14, 15, 16),
        "reconstruction",
        "Amand 1945 ch. III (PE VI.6.12-16, futility of praise/blame/sanctions)",
    ),
    (
        "argument_cafma_character_contradiction_1f6g8i54",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(5, 6, 7),
        "reconstruction",
        "Amand 1945 ch. III (PE VI.6.5-7, character/virtue change)",
    ),
    (
        "argument_cafma_futility_of_piety_2g7h9j65",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(19),
        "reconstruction",
        "Amand 1945 ch. III (PE VI.6.19, futility of piety/prayer)",
    ),
    # === CARNEADES — autonomous mental causation (Cic. Fat. 23-25)
    (
        "argument_carneades_autonomous_mental_causation_argument_4e7e9250",
        _cic_fat(23, 24, 25),
        "witness",
        "Long-Sedley LS 70G; Bobzien 1998 ch. 4 (CAFMA core text)",
    ),
    # === CARNEADES — Amand1945 thematic reconstructions
    (
        "argument_carneadean_general_theme_amand1945",
        _eus_pe_vi_6(5) + _cic_fat(23, 24, 25),
        "reconstruction",
        "Amand 1945 ch. II §VII.IV.1 (PE VI.6.5 + Cic. Fat.)",
    ),
    (
        "argument_carneadean_legislation_amand1945",
        _eus_pe_vi_6(18),
        "reconstruction",
        "Amand 1945 ch. II §VII.IV (PE VI.6.18)",
    ),
    (
        "argument_carneadean_virtue_vice_amand1945",
        _eus_pe_vi_6(5, 6, 7),
        "reconstruction",
        "Amand 1945 (PE VI.6.5-7, virtue/vice/praise/blame)",
    ),
    (
        "argument_carneadean_incentives_amand1945",
        _eus_pe_vi_6(12, 13, 14, 15),
        "reconstruction",
        "Amand 1945 (PE VI.6.12-15, exhortations/rewards/sanctions)",
    ),
    (
        "argument_carneadean_action_futility_amand1945",
        _eus_pe_vi_6(8, 9, 10),
        "reconstruction",
        "Amand 1945 (PE VI.6.8-10, action becomes useless)",
    ),
    (
        "argument_carneadean_piety_amand1945",
        _eus_pe_vi_6(19),
        "reconstruction",
        "Amand 1945 (PE VI.6.19, piety/religion ruined)",
    ),
    (
        "argument_carneadean_providence_mantike_alexander_amand1945",
        _eus_pe_vi_6(19),
        "reconstruction",
        "Amand 1945 (PE VI.6.19 + Alexander De Fato)",
    ),
    (
        "argument_carneadean_stoic_pragmatic_self_refutation_amand1945",
        _eus_pe_vi_6(8, 9, 10),
        "reconstruction",
        "Amand 1945 (Stoic pragmatic self-refutation via Alexander §18)",
    ),
    (
        "argument_carneadean_stoic_pragmatic_punishment_amand1945",
        _eus_pe_vi_6(12, 13, 14, 15, 16, 17, 18),
        "reconstruction",
        "Amand 1945 (Stoics still punish criminals, Alexander §18)",
    ),
    (
        "argument_carneadean_antiastrological_horoscope_impossibility_amand1945",
        _cic_div(85, 86, 87, 88, 89, 90),
        "reconstruction",
        "Amand 1945 (PE VI.7 fragments; Cic. Div. II.85-90 anti-astrological topos)",
    ),
    (
        "argument_carneadean_antiastrological_twins_amand1945",
        _cic_div(90, 91, 92, 93, 94, 95),
        "reconstruction",
        "Amand 1945 (Carneadean twins argument; cf. Cic. Div. II.90-95)",
    ),
    (
        "argument_carneadean_antiastrological_collective_death_amand1945",
        _cic_div(95, 96, 97),
        "reconstruction",
        "Amand 1945 (collective death of those not born under same star)",
    ),
    (
        "argument_carneadean_antiastrological_nomima_barbarika_amand1945",
        _cic_div(95, 96, 97),
        "reconstruction",
        "Amand 1945 (νόμιμα βαρβαρικά / barbarian customs anti-astrology)",
    ),
    (
        "argument_carneadean_antiastrological_animals_amand1945",
        _cic_div(95, 96, 97),
        "reconstruction",
        "Amand 1945 (animals under destiny)",
    ),
    (
        "argument_carneadean_anti_mantike_amand1945",
        _cic_div(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        "reconstruction",
        "Amand 1945 ch. II §IV (general anti-divination)",
    ),
    (
        "argument_carneadean_anti_teleology_cosmos_amand1945",
        _cic_nd(1, 2, 3),
        "reconstruction",
        "Amand 1945; cf. Cic. ND III for anti-teleology",
    ),
    # === Origen witnesses to Carneadean transposition (Amand1945)
    (
        "argument_origen_witness_carneadean_transposition_envelope_amand1945",
        _eus_pe_vi_6(5, 6, 7, 8, 9, 10),
        "reconstruction",
        "Amand 1945 ch. IV (Origène, transposition théologique des arguments de Carnéade)",
    ),
    (
        "argument_origen_witness_carneades_transposition_theological_method_amand1945",
        _eus_pe_vi_6(5, 6, 7),
        "reconstruction",
        "Amand 1945 ch. IV (méthode signature : philosophique → théologique)",
    ),
    # === Scholarly arguments on Carneades (modern)
    (
        "scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(5, 6, 7, 8, 9, 10),
        "reconstruction",
        "Amand 1945 (anti-fatalist moral argumentation)",
    ),
    (
        "scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4",
        _cic_fat(23, 24, 25) + _eus_pe_vi_6(5, 6, 7, 8, 9, 10, 12, 18, 19),
        "reconstruction",
        "Amand 1945 (reconstruction of Neo-Academic architecture)",
    ),
    (
        "scholarly_argument_minns_justin_martyr_s_anti_stoic_arg_0",
        _cic_fat(23, 24, 25),
        "reconstruction",
        "Minns 2009 *Justin Martyr* (Justin deploys Carneadean anti-Stoic arguments)",
    ),
    # === Christian-witness arguments (Basil, Methodius, Justin, etc.) — anchor to relevant PE
    (
        "argument_basil_carneadean_hex_vi_7_laws_useless",
        _eus_pe_vi_6(18),
        "reformulation",
        "Amand 1945 ch. IV (Basil Hex VI.7 reformulation; PE VI.6.18 source-doxography)",
    ),
    (
        "argument_basil_carneadean_hex_vi_7_christian_hopes_destroyed",
        _eus_pe_vi_6(19),
        "reformulation",
        "Amand 1945 ch. IV (Basil Hex VI.7; PE VI.6.19 piety source)",
    ),
    (
        "argument_methodius_symposium_three_carneadean_syllogisms",
        _eus_pe_vi_6(5, 6, 7),
        "reformulation",
        "Amand 1945 ch. IV (Methodius Symp. VIII.16 — via hypomnemata)",
    ),
    (
        "argument_justin_1apol_43_three_carneadean_topoi",
        _eus_pe_vi_6(5, 12, 18),
        "reformulation",
        "Amand 1945 ch. IV (Justin 1 Apol. 43 — three topoi)",
    ),
    (
        "argument_gregory_disccat31_carneadean_moral_amand1945",
        _eus_pe_vi_6(5, 6, 7),
        "reformulation",
        "Amand 1945 ch. IV (Gregory Nyss. Disc. Cat. 31)",
    ),
    (
        "argument_nemesius_nat_hom_35_carneadean_summary_amand1945",
        _eus_pe_vi_6(5, 6, 7, 8, 9, 10),
        "reformulation",
        "Amand 1945 ch. IV (Nemesius Nat. Hom. 35)",
    ),
    (
        "argument_greg_naz_carmen_dogm_5_carneadean",
        _eus_pe_vi_6(5),
        "reformulation",
        "Amand 1945 ch. IV (Gregory Naz. Carm. dogm. 5)",
    ),
    (
        "argument_lucian_zeus_confutatus_carneadean_topos",
        _eus_pe_vi_6(5, 18),
        "reformulation",
        "Amand 1945 ch. IV (Lucian Iuppiter confutatus 18)",
    ),
    (
        "argument_hierocles_carneadean_inversion_for_providential_heimarmene",
        _eus_pe_vi_6(5, 6, 7),
        "reformulation",
        "Amand 1945 ch. IV (Hieroclès, inversion du topos pour providence)",
    ),
    (
        "argument_basil_observation_impossible_at_birth",
        _cic_div(85, 86, 87, 88, 89, 90),
        "reformulation",
        "Amand 1945 (Basil Hex VI.5; Cic. Div. II.85-90 horoscope impossibility)",
    ),
    (
        "argument_basil_kings_born_daily",
        _cic_div(90, 91, 92, 93, 94, 95),
        "reformulation",
        "Amand 1945 (Basil Hex VI.7 — kings born daily variant)",
    ),
    (
        "argument_diodore_tarsus_impossibility_prediction_carneadean",
        _cic_div(95, 96, 97),
        "reformulation",
        "Amand 1945 ch. IV (Diodore de Tarse Contra heimarmenen VIII.45)",
    ),
    (
        "argument_arian_job_pity_criminals_carneadean_5th_title",
        _eus_pe_vi_6(15, 16, 17),
        "reformulation",
        "Amand 1945 ch. IV (commentateur arien de Job — pitié des criminels)",
    ),
    (
        "argument_oinomaos_carneadean_libre_adaptation",
        _eus_pe_vi_6(5, 6, 7, 8),
        "reformulation",
        "Amand 1945 ch. IV (Oinomaos via PE VI.7.35-41 adaptation)",
    ),
]


# Cicero discusses → argument list (Task H3).
# Restricted to Chrys/Carn arguments whose principal transmission witness IS
# Cicero (De Fato or De Divinatione). This makes Cicero retrievable as the
# transmitter at the person level without depending on multi-hop chains.
CICERO_DISCUSSES_ARGUMENTS: list[tuple[str, str]] = [
    # --- Chrysippean doctrines transmitted by Cicero (De Fato) ---
    ("argument_cylinder_analogy_chrysippus_k1l2m3n4", "Cic. Fat. 39-43 — cylinder analogy"),
    ("argument_chrysippus_causal_taxonomy", "Cic. Fat. 39-43 — causal taxonomy"),
    (
        "scholarly_argument_bobzien_chrysippus_compatibilism_fate__1",
        "Cic. Fat. 39-43 — compatibilism source-text",
    ),
    (
        "scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2",
        "Cic. Fat. 39-43 — Cicero's own critique",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_s_compatibilism_3",
        "Cic. Fat. 39-43 — cylinder/cone analogy",
    ),
    (
        "scholarly_argument_koch_stoic_causal_theory_and_human__0",
        "Cic. Fat. 39-43 — Stoic causal theory source",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_modal_logic_and_con_2",
        "Cic. Fat. 7-14 — modal logic transmission",
    ),
    (
        "scholarly_argument_bobzien_chrysippus_s_arguments_for_cau_1",
        "Cic. Fat. 20-30 — bivalence + causation",
    ),
    (
        "argument_bobzien_2001_b1_synkatathesis_psychology_action",
        "Cic. Fat. 39-43 — synkatathesis source-text",
    ),
    (
        "argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus",
        "Cic. Fat. 39-43 — Stoic causal eph' hêmin source",
    ),
    # --- Carneadean doctrines transmitted by Cicero (De Fato 23-25, De Div II) ---
    (
        "argument_cafma_carneades_m3n4o5p6",
        "Cic. Fat. 23-25 — CAFMA core",
    ),
    (
        "argument_carneades_autonomous_mental_causation_argument_4e7e9250",
        "Cic. Fat. 23-25 — autonomous mental causation",
    ),
    (
        "argument_cafma_futility_of_effort_8c3d5f21",
        "Cic. Fat. 23-25 — CAFMA arg I",
    ),
    (
        "argument_cafma_futility_of_legislation_9d4e6g32",
        "Cic. Fat. 23-25 — CAFMA arg II",
    ),
    (
        "argument_cafma_futility_of_sanctions_0e5f7h43",
        "Cic. Fat. 23-25 — CAFMA arg III",
    ),
    (
        "argument_cafma_character_contradiction_1f6g8i54",
        "Cic. Fat. 23-25 — CAFMA arg IV",
    ),
    (
        "argument_cafma_futility_of_piety_2g7h9j65",
        "Cic. Fat. 23-25 — CAFMA arg V",
    ),
    (
        "argument_carneadean_assent_chain_via_cicero_amand1945",
        "Cic. Fat. — Carneadean assent chain (already work-anchored, person-level link)",
    ),
    (
        "argument_carneadean_antiastrological_horoscope_impossibility_amand1945",
        "Cic. Div. II — anti-astrological topos source",
    ),
    (
        "argument_carneadean_antiastrological_twins_amand1945",
        "Cic. Div. II.90-95 — twins argument source",
    ),
]


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_edges() -> list[dict[str, Any]]:
    with EDGES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def get_node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} - skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source_id") or e.get("source") or "",
        e.get("relation") or "",
        e.get("target_id") or e.get("target") or "",
    )


def build_cites_primary_source_edge(
    arg_id: str,
    passage_id: str,
    transmission_role: str,
    scholarship: str,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "wave": WAVE_TAG,
        "confidence": 0.9,
        "transmission_role": transmission_role,
        "source_scholarship": scholarship,
    }
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": "cites_primary_source",
        "source": arg_id,
        "source_id": arg_id,
        "target": passage_id,
        "target_id": passage_id,
        "weight": 0.9,
    }


def build_cicero_discusses_edge(arg_id: str, role_note: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "wave": WAVE_TAG,
        "confidence": 0.95,
        "role": "transmitter",
        "role_note": role_note,
    }
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": "discusses",
        "source": CICERO_PERSON_ID,
        "source_id": CICERO_PERSON_ID,
        "target": arg_id,
        "target_id": arg_id,
        "weight": 1.0,
    }


# ---------------------------------------------------------------------------
# H1 — Audit
# ---------------------------------------------------------------------------


def collect_argument_universe(
    nodes: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """Return (chrysippean_arg_ids, carneadean_arg_ids)."""
    chrys: set[str] = set()
    carn: set[str] = set()
    for n in nodes:
        if n.get("type") != "argument":
            continue
        nid = get_node_id(n)
        label = (n.get("label") or "").lower()
        nl = nid.lower()
        if "chrysipp" in nl or "chrysipp" in label:
            chrys.add(nid)
        if "carnead" in nl or "carnead" in label or "cafma" in nl:
            carn.add(nid)
    return chrys, carn


def audit_anchoring(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    chrys_ids, carn_ids = collect_argument_universe(nodes)
    node_type: dict[str, str] = {get_node_id(n): (n.get("type") or "") for n in nodes}

    chrys_anchors: dict[str, list[dict[str, str]]] = defaultdict(list)
    carn_anchors: dict[str, list[dict[str, str]]] = defaultdict(list)

    for e in edges:
        rel = e.get("relation") or ""
        s = e.get("source_id") or e.get("source") or ""
        t = e.get("target_id") or e.get("target") or ""
        if rel not in {"cites_primary_source", "evidenced_by"}:
            continue
        if s in chrys_ids:
            chrys_anchors[s].append(
                {"relation": rel, "target": t, "target_type": node_type.get(t, "")}
            )
        if s in carn_ids:
            carn_anchors[s].append(
                {"relation": rel, "target": t, "target_type": node_type.get(t, "")}
            )

    def _summarize(
        ids: set[str], anchors: dict[str, list[dict[str, str]]]
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for aid in ids:
            edges_for_aid = anchors.get(aid, [])
            passage_count = sum(1 for e in edges_for_aid if e["target_type"] == "passage")
            rows.append(
                {
                    "argument_id": aid,
                    "total_anchor_edges": len(edges_for_aid),
                    "passage_anchor_edges": passage_count,
                    "anchors": edges_for_aid,
                }
            )
        rows.sort(key=lambda r: (r["passage_anchor_edges"], r["total_anchor_edges"]))
        return rows

    chrys_rows = _summarize(chrys_ids, chrys_anchors)
    carn_rows = _summarize(carn_ids, carn_anchors)

    return {
        "generated_at": NOW_ISO,
        "wave": WAVE_TAG,
        "totals": {
            "chrysippean_arguments": len(chrys_ids),
            "carneadean_arguments": len(carn_ids),
            "chrysippean_zero_anchor": sum(
                1 for r in chrys_rows if r["passage_anchor_edges"] == 0
            ),
            "carneadean_zero_anchor": sum(
                1 for r in carn_rows if r["passage_anchor_edges"] == 0
            ),
        },
        "chrysippean": chrys_rows,
        "carneadean": carn_rows,
    }


def write_report(report: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-h] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    node_ids: set[str] = {get_node_id(n) for n in nodes}
    node_type: dict[str, str] = {get_node_id(n): (n.get("type") or "") for n in nodes}
    edges_signatures: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    # ---- H1 — audit before
    audit_before = audit_anchoring(nodes, edges)
    write_report(audit_before)
    audit_arguments_scanned = (
        audit_before["totals"]["chrysippean_arguments"]
        + audit_before["totals"]["carneadean_arguments"]
    )
    audit_underanchored = (
        audit_before["totals"]["chrysippean_zero_anchor"]
        + audit_before["totals"]["carneadean_zero_anchor"]
    )
    print(
        f"[audit] arguments_scanned={audit_arguments_scanned} "
        f"underanchored(0-psg)={audit_underanchored}"
    )
    print(
        "[audit] chrys: total={chry_t}  zero_anchor={chry_0}  "
        "| carn: total={car_t}  zero_anchor={car_0}".format(
            chry_t=audit_before["totals"]["chrysippean_arguments"],
            chry_0=audit_before["totals"]["chrysippean_zero_anchor"],
            car_t=audit_before["totals"]["carneadean_arguments"],
            car_0=audit_before["totals"]["carneadean_zero_anchor"],
        )
    )

    # ---- H2 — anchor underrepresented arguments
    cites_primary_source_added = 0
    skipped_no_passage = 0
    skipped_no_argument = 0
    skipped_existing = 0

    for arg_id, passage_ids, role, scholarship in ANCHOR_SPECS:
        if arg_id not in node_ids:
            print(f"[H2] skip: argument {arg_id} not in KG")
            skipped_no_argument += 1
            continue
        if node_type.get(arg_id) != "argument":
            print(
                f"[H2] skip: {arg_id} type={node_type.get(arg_id)} (not 'argument')"
            )
            skipped_no_argument += 1
            continue
        for pid in passage_ids:
            if pid not in node_ids:
                print(f"[H2] skip-no-passage: {arg_id} -> {pid}")
                skipped_no_passage += 1
                continue
            if node_type.get(pid) != "passage":
                print(
                    f"[H2] skip-not-passage: {arg_id} -> {pid} "
                    f"type={node_type.get(pid)}"
                )
                skipped_no_passage += 1
                continue
            sig = (arg_id, "cites_primary_source", pid)
            if sig in edges_signatures:
                skipped_existing += 1
                continue
            edge = build_cites_primary_source_edge(arg_id, pid, role, scholarship)
            edges.append(edge)
            edges_signatures.add(sig)
            cites_primary_source_added += 1
            print(f"[H2] cite: {arg_id} -> {pid}  ({role})")

    # ---- H3 — Cicero discusses transmitted arguments
    cicero_discusses_added = 0
    cicero_discusses_skipped_existing = 0
    cicero_discusses_skipped_no_arg = 0

    if CICERO_PERSON_ID not in node_ids:
        print(f"[H3] ABORT: Cicero person node {CICERO_PERSON_ID} not in KG")
    else:
        for arg_id, role_note in CICERO_DISCUSSES_ARGUMENTS:
            if arg_id not in node_ids:
                cicero_discusses_skipped_no_arg += 1
                print(f"[H3] skip: argument {arg_id} not in KG")
                continue
            if node_type.get(arg_id) != "argument":
                cicero_discusses_skipped_no_arg += 1
                print(
                    f"[H3] skip: {arg_id} type={node_type.get(arg_id)} (not 'argument')"
                )
                continue
            sig = (CICERO_PERSON_ID, "discusses", arg_id)
            if sig in edges_signatures:
                cicero_discusses_skipped_existing += 1
                continue
            edge = build_cicero_discusses_edge(arg_id, role_note)
            edges.append(edge)
            edges_signatures.add(sig)
            cicero_discusses_added += 1
            print(f"[H3] discusses: Cicero -> {arg_id}")

    # ---- Persist
    if cites_primary_source_added or cicero_discusses_added:
        write_edges(edges)
        print(f"[write] edges={len(edges):,}")
    else:
        print("[write] no changes - files untouched")

    # ---- Audit after
    audit_after = audit_anchoring(nodes, edges)
    print()
    print(
        f"[wave-h] audit_arguments_scanned={audit_arguments_scanned}  "
        f"audit_underanchored={audit_underanchored}"
    )
    print(
        f"[wave-h] cites_primary_source_added={cites_primary_source_added}  "
        f"skipped_no_passage={skipped_no_passage}  "
        f"skipped_existing={skipped_existing}  "
        f"skipped_no_argument={skipped_no_argument}"
    )
    print(
        f"[wave-h] cicero_discusses_added={cicero_discusses_added}  "
        f"skipped_existing={cicero_discusses_skipped_existing}  "
        f"skipped_no_argument={cicero_discusses_skipped_no_arg}"
    )
    print(f"[wave-h] report_written={REPORT_PATH.relative_to(ROOT)}")
    print()
    print(
        "[delta] chrys zero-anchor: before={a} -> after={b}".format(
            a=audit_before["totals"]["chrysippean_zero_anchor"],
            b=audit_after["totals"]["chrysippean_zero_anchor"],
        )
    )
    print(
        "[delta] carn  zero-anchor: before={a} -> after={b}".format(
            a=audit_before["totals"]["carneadean_zero_anchor"],
            b=audit_after["totals"]["carneadean_zero_anchor"],
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
