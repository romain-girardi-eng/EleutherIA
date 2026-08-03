"""Amand 1945 B3 — Consolidation: réparation des 18 nœuds défectueux + inserts complémentaires + edges.

Run-once script. READ-WRITE sur data/kg/nodes.jsonl et edges.jsonl.

Étapes :
1. Reprise des 18 nœuds B3 défectueux (metadata=dict {needs_evidence:true}) :
   restaure metadata complète (string JSON conforme) + period/school + tous les champs Amand1945.
2. Ajoute ~12 nœuds complémentaires (Maxime de Tyr person + work, 3 work-shells Favorinus,
   3 concepts, 4 syntheses, 1 argument-envelope Philon).
3. Ajoute ~25 edges (evidenced_by Cicéron→passages, transmits_to Carnéade→Cicéron→Philon,
   discusses, member_of, etc).

Idempotent : déjà-faits sont skip.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"
TIMESTAMP = "2026-05-15 19:30:00.000000+00:00"

SCHOLAR_ID = "scholar_amand_de_mendieta_e"
PUB_ID = "pub_amand_1945_fatalisme"
BIBTEX = "amand-1945-fatalisme-et-liberte-dans-l-antiquite-grecque"
AMAND_BOOK = "Fatalisme et liberté dans l'antiquité grecque"
AMAND_YEAR = 1945
AMAND_REPRINT = "Hakkert Amsterdam 1973"
WAVE_TAG = "B3_2026-05-15"


def md_base(
    *,
    page_range: str,
    md_line_range: str,
    chapter: str,
    chapter_actual: str,
    confidence: float,
    source_quality: str = "paraphrase_from_md_ocr_95pc",
    contains_greek: bool = True,
    contains_latin: bool = False,
    evidence_pending: bool = False,
    evidence_pending_reason: str = "",
    cited_editions: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md = {
        "claimed_by": SCHOLAR_ID,
        "publication": PUB_ID,
        "bibtex_key": BIBTEX,
        "source_quality": source_quality,
        "amand_book": AMAND_BOOK,
        "amand_book_year": AMAND_YEAR,
        "amand_book_reprint": AMAND_REPRINT,
        "wave": WAVE_TAG,
        "amand_location": {
            "page_range": page_range,
            "md_line_range": md_line_range,
            "chapter": chapter,
        },
        "amand_chapter_actual": chapter_actual,
        "confidence": confidence,
        "contains_greek_to_verify": contains_greek,
    }
    if contains_latin:
        md["contains_latin_to_verify"] = True
    if cited_editions:
        md["amand_cited_edition_unverified"] = cited_editions
    if evidence_pending:
        md["evidence_pending"] = True
        md["evidence_pending_reason"] = evidence_pending_reason
    if extra:
        md.update(extra)
    return md


# --------------------------------------------------------------------------
# REPAIRS : 18 nodes that currently have broken metadata=dict {needs_evidence:true}
# --------------------------------------------------------------------------

REPAIRS: dict[str, dict[str, Any]] = {
    "synthesis_amand1945_cicero_defato_moral_lacuna": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 78-79",
            md_line_range="ll. 5135-5158",
            chapter="Livre I Ch. II §I (Cicéron)",
            chapter_actual="Livre I Ch. II §I — Cicéron, état lacunaire du De fato",
            confidence=0.85,
            cited_editions=[
                "Cicéron, De fato, éd. A. Yon, Collection des Universités de France, Paris 1933",
            ],
            extra={
                "amand_thesis_type": "philological_reconstruction_lacuna",
                "amand_judgement_register": "haute_probabilite_reconnue",
                "lacuna_estimate_yon_1933": "p. XXXIX-XL et p. XXXIII",
            },
        ),
    ),
    "synthesis_amand1945_philo_early_period_school_compilation": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 81-83",
            md_line_range="ll. 5232-5360",
            chapter="Livre I Ch. II §II (Philon) — Les écrits philosophiques",
            chapter_actual="Livre I Ch. II §II.1 — La période grecque de Philon",
            confidence=0.85,
            cited_editions=[
                "P. Wendland, Philos Schrift über die Vorsehung, Berlin 1892",
                "W. Bousset, Jüdisch-Christlicher Schulbetrieb in Alexandria und Rom, Göttingen 1915",
                "Christ-Schmid-Stählin, Geschichte der griechischen Litteratur, II/1, München 1920, p. 629-630",
                "K. Gronau, Poseidonios und die jüdisch-christliche Genesisexegese, Leipzig 1914",
            ],
            extra={
                "amand_thesis_type": "philological_characterisation_youth_writings",
                "engages_with_scholars": ["Wendland", "Bousset", "Pohlenz", "Bréhier", "Völker", "Gronau"],
                "pohlenz_counterposition": "Pohlenz 1942 conteste la thèse 'oeuvres de jeunesse mécaniques' et propose contemporanéité aux commentaires bibliques",
            },
        ),
    ),
    "synthesis_amand1945_philo_de_providentia_authenticity": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 82",
            md_line_range="ll. 5273-5347",
            chapter="Livre I Ch. II §II (Philon) — La diatribe antiastrologique",
            chapter_actual="Livre I Ch. II §II.2 — Authenticité philonienne du De providentia (Wendland)",
            confidence=0.9,
            cited_editions=[
                "P. Wendland, Philos Schrift über die Vorsehung, Berlin 1892",
            ],
            extra={
                "amand_thesis_type": "philological_authenticity",
                "consensus_status": "authentic_per_Wendland_1892_uncontested",
            },
        ),
    ),
    "synthesis_amand1945_philo_de_providentia_carneadean_strata": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 83-85",
            md_line_range="ll. 5361-5410",
            chapter="Livre I Ch. II §II (Philon) — La diatribe antiastrologique",
            chapter_actual="Livre I Ch. II §II.2 — Deux couches carnéadiennes (Wendland)",
            confidence=0.8,
            cited_editions=[
                "P. Wendland, Philos Schrift über die Vorsehung, Berlin 1892, p. 24-37, 47-50, 83",
            ],
            extra={
                "amand_thesis_type": "philological_stratigraphy",
                "stratum_1_locus": "Περὶ προνοίας I, 77-88 (diatribe antiastrologique)",
                "stratum_2_locus": "Περὶ προνοίας II, 3-11 (objections contre la Providence stoïcienne, attestation croisée De natura deorum III, 32-39)",
                "engages_with_scholars": ["Wendland"],
            },
        ),
    ),
    "argument_philo_de_providentia_moral_responsibility_amand1945": dict(
        period="Hellenistic",
        school="school_academy",
        md=md_base(
            page_range="p. 85-93, p. 92-95 (texte latin Aucher)",
            md_line_range="ll. 5395-5759",
            chapter="Livre I Ch. II §II.5 (Philon) — analyse argumentation morale",
            chapter_actual="Livre I Ch. II §II.5 — Premier argument (chef moral)",
            confidence=0.85,
            cited_editions=[
                "Philon, De providentia I, 79-83, éd. J.-B. Aucher, Venise 1822, t. I, p. 36-39",
            ],
            evidence_pending=True,
            evidence_pending_reason="Philon De Providentia I, 79-83 absent du corpus EleutherIA (work-shell partiel, ingestion en cours, see docs/reports/2026-05-15-amand-six-witnesses-audit.md)",
            extra={
                "amand_witness_rank": "primary_witness_n1",
                "argument_category": "argument_carneadean_moral_reconstruction_via_witness_philo",
                "transmits_argument_pivots_b1": [
                    "argument_carneadean_legislation_amand1945",
                    "argument_carneadean_virtue_vice_amand1945",
                ],
                "amand_judgement_quote_fr": "la preuve la plus puissante, la plus décisive contre le fatalisme",
                "philo_section_locus": "Περὶ προνοίας I, 79-87",
                "sub_arguments": [
                    {"locus": "§§79-81", "topic": "magistrat ne peut juger sans liberté"},
                    {"locus": "§82", "topic": "loi+droit+vertu+châtiment vidés de sens"},
                    {"locus": "§83", "topic": "fait psychologique : la peur du châtiment dissuade"},
                ],
            },
        ),
    ),
    "argument_philo_de_providentia_ethnic_customs_amand1945": dict(
        period="Hellenistic",
        school="school_academy",
        md=md_base(
            page_range="p. 85",
            md_line_range="ll. 5403-5419",
            chapter="Livre I Ch. II §II.5 (Philon) — analyse argumentation morale",
            chapter_actual="Livre I Ch. II §II.5 — Deuxième argument (coutumes ethniques)",
            confidence=0.8,
            cited_editions=[
                "Philon, De providentia I, 84-86, éd. J.-B. Aucher, Venise 1822, t. I",
            ],
            evidence_pending=True,
            evidence_pending_reason="Philon De Providentia I, 84-86 absent du corpus EleutherIA",
            extra={
                "amand_witness_rank": "primary_witness_n1",
                "argument_category": "argument_carneadean_antiastrological_via_witness_philo",
                "anticipates_b2_arg": "argument_carneadean_antiastrological_nomima_barbarika_amand1945",
                "philo_section_locus": "Περὶ προνοίας I, 84-86",
                "ethnic_groups_cited": ["Juifs (circoncision 8e jour, sabbat)", "Scythes/Perses (incestes rituels)", "Égyptiens (zoolâtrie)"],
            },
        ),
    ),
    "argument_philo_de_providentia_collective_death_amand1945": dict(
        period="Hellenistic",
        school="school_academy",
        md=md_base(
            page_range="p. 85",
            md_line_range="ll. 5420-5424",
            chapter="Livre I Ch. II §II.5 (Philon) — analyse argumentation morale",
            chapter_actual="Livre I Ch. II §II.5 — Troisième argument (mort collective)",
            confidence=0.75,
            cited_editions=[
                "Philon, De providentia I, 87 (début), éd. J.-B. Aucher, Venise 1822, t. I",
            ],
            evidence_pending=True,
            evidence_pending_reason="Philon De Providentia I, 87 absent du corpus EleutherIA",
            extra={
                "amand_witness_rank": "primary_witness_n1",
                "argument_category": "argument_carneadean_antiastrological_via_witness_philo",
                "anticipates_b2_arg": "argument_carneadean_antiastrological_collective_death_amand1945",
                "amand_note_on_brehier": "Bréhier 1925 attribue à tort la réfutation à Panétius via Cic. De div. II.47.97 — Amand corrige cette attribution",
            },
        ),
    ),
    "argument_philo_de_providentia_conception_moment_amand1945": dict(
        period="Hellenistic",
        school="school_academy",
        md=md_base(
            page_range="p. 85",
            md_line_range="ll. 5425-5428",
            chapter="Livre I Ch. II §II.5 (Philon) — analyse argumentation morale",
            chapter_actual="Livre I Ch. II §II.5 — Quatrième argument (moment de la conception)",
            confidence=0.8,
            cited_editions=[
                "Philon, De providentia I, 87, éd. J.-B. Aucher, Venise 1822, t. I",
            ],
            evidence_pending=True,
            evidence_pending_reason="Philon De Providentia I, 87 absent du corpus EleutherIA",
            extra={
                "amand_witness_rank": "primary_witness_n1",
                "argument_category": "argument_carneadean_antiastrological_via_witness_philo",
                "anticipates_b2_arg": "argument_carneadean_antiastrological_horoscope_impossibility_amand1945",
            },
        ),
    ),
    "synthesis_amand1945_philo_resolute_defender_human_freedom": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 85-87",
            md_line_range="ll. 5429-5517",
            chapter="Livre I Ch. II §II.3 (Philon) — Philon défenseur résolu de la liberté",
            chapter_actual="Livre I Ch. II §II.3 — Cadre théologique du témoin n°1",
            confidence=0.9,
            cited_editions=[
                "Philon, Quod Deus sit immutabilis 47-51, éd. Wendland, t. II 1897, p. 66-67",
                "Philon, De specialibus legibus I (De monarchia) 1, éd. Cohn, t. V 1906, p. 3-5",
                "Zeller, Philosophie der Griechen III/2/4, 1903, p. 442-444",
                "Völker, Fortschritt und Vollendung bei Philo, Leipzig 1938, p. 58-63",
                "Bréhier, Les idées philosophiques et religieuses de Philon, Paris 1925, p. 261-271",
            ],
            extra={
                "amand_thesis_type": "doctrinal_portrait",
                "engages_with_scholars": ["Zeller", "Bréhier", "Völker", "Wiggers"],
                "philo_concept_keys": ["ἐλευθερία", "τὸ ἑκούσιον", "ἄφετον καὶ ἐλεύθερον", "image de Dieu (εἰκών)"],
                "biblical_locus_quoted_by_philo": "Deutéronome 30, 15.19 ('vois j'ai mis devant toi la vie et la mort')",
            },
        ),
    ),
    "synthesis_amand1945_philo_attitude_astrology_signs_not_causes": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 87-90",
            md_line_range="ll. 5518-5656",
            chapter="Livre I Ch. II §II.4 (Philon) — attitude envers les astres",
            chapter_actual="Livre I Ch. II §II.4 — Astrologie purgée du fatalisme",
            confidence=0.85,
            cited_editions=[
                "Philon, De opificio mundi 55, 58, 73, 144, éd. Cohn, t. I 1896",
                "Philon, De specialibus legibus I (De monarchia) 13-19, 66, éd. Cohn, t. V 1906",
                "Philon, De specialibus legibus I (De sacerdotibus) 89-92, éd. Cohn, t. V 1906",
                "Philon, Quaestiones in Exodum II, 74, 78, 81 (texte arménien)",
                "Philon, De congressu eruditionis gratia §50, éd. Wendland (passage Bousset 1915 p. 101-102)",
                "Bousset, Jüdisch-Christlicher Schulbetrieb, Göttingen 1915, p. 21-23, 36-37, 134-152",
                "Bréhier, Les idées philosophiques et religieuses de Philon, Paris 1925, p. 165-167",
            ],
            extra={
                "amand_thesis_type": "doctrinal_portrait_position_intermediate",
                "philo_position_summary": "monothéisme oblige à proscrire astrolâtrie ; mais astres = ζῷα νοερά, êtres divins secondaires, signes (σημεῖα) des événements futurs, causes secondes, non causes du destin humain",
                "philo_dogma_kept_partial": "sympathie universelle (συμπάθεια τῶν ὅλων) admise tout en rejetant l'εἱμαρμένη stoïcienne",
                "engages_with_scholars": ["Bousset", "Bréhier"],
            },
        ),
    ),
    "synthesis_amand1945_philo_de_providentia_literary_source_uncertain": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 91-92",
            md_line_range="ll. 5675-5705",
            chapter="Livre I Ch. II §II.5 (Philon) — texte de l'argumentation morale",
            chapter_actual="Livre I Ch. II §II.5 — Aveu méthodologique d'incertitude sur la source",
            confidence=0.95,
            cited_editions=[],
            extra={
                "amand_thesis_type": "methodological_admission",
                "amand_position": "Source littéraire immédiate inconnue (Clitomaque OU sous-produit/manuel scolaire alexandrin) — peu importe car objectif = reconstituer l'argumentation carnéadienne, pas reconstituer la source de Philon",
                "verbatim_quote_fr": "Nous ignorons quelle fut la source littéraire immédiate de cette argumentation amplement développée",
            },
        ),
    ),
    "synthesis_amand1945_favorinus_loose_neoacademic_skeptic": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 96-98",
            md_line_range="ll. 5919-6000",
            chapter="Livre I Ch. II §III (Favorinus) — la polémique antiastrologique",
            chapter_actual="Livre I Ch. II §III.1 — Caractérisation : sophiste plus que philosophe",
            confidence=0.8,
            cited_editions=[
                "Ueberweg-Praechter, Philosophie des Altertums, p. 547",
                "W. Schmid, art. Favorinus, in Pauly-Wissowa RE VI 1909, col. 2078-2084",
                "Christ-Schmid-Stählin, G. Gr. Lit. II/2 1924, p. 764-766",
                "M. Norsa & G. Vitelli, Φαβωρίνου Περὶ φυγῆς, Studi e testi 53, Vatican 1931",
                "W. Schmid, art. Favorinus (Suppl.) in Pauly-Wissowa RE Suppl. VI 1935, col. 65-70",
            ],
            extra={
                "amand_thesis_type": "doctrinal_characterisation",
                "amand_judgement_register": "evaluation_negative_assumée",
                "favorinus_school_amand": "scepticisme néo-académicien (lâche, peu rigoureux)",
                "favorinus_polygraph_topics": ["lieux communs moraux", "dialectique", "grammaire", "style", "critique d'authenticité", "histoire anecdotique", "droit", "jurisprudence", "sciences naturelles", "rhétorique"],
            },
        ),
    ),
    "synthesis_amand1945_favorinus_fourteen_arguments_cadre": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 98-100",
            md_line_range="ll. 6001-6128",
            chapter="Livre I Ch. II §III.1 (Favorinus) — la polémique antiastrologique",
            chapter_actual="Livre I Ch. II §III.1 — Les 14 arguments antiastrologiques d'Aulu-Gelle NA XIV.1.2-31",
            confidence=0.85,
            cited_editions=[
                "Aulu-Gelle, Noctium atticarum libri XX, livre XIV, 1, 1-36, éd. C. Hosius, Leipzig Teubner 1903, t. II, p. 102-110",
            ],
            extra={
                "amand_thesis_type": "philological_inventory",
                "amand_gellius_summary_note": "Aulu-Gelle prévient (NA XIV.1.32) qu'il ne rapporte qu'un 'sec résumé' (Haec nos sicca et incondita et propemodum ieiuna oratione adtingimus)",
                "favorinus_polemic_target": "γενεθλιαλογία des Chaldéens",
                "list_of_14_topics": [
                    "1. antiquité fausse des Chaldéens",
                    "2. axiome astrologique absurde (transposition marées→tout)",
                    "3. brièveté de vie humaine vs sympathie cosmique",
                    "4. latitude/zones célestes limitent la science",
                    "5. inconséquence des effets simultanés (gel/chaud)",
                    "6. étoiles fixes plus nombreuses que dit",
                    "7. observation = infinité de siècles",
                    "8. conception vs naissance : 2 horoscopes ?",
                    "9. observation de tous les ancêtres requise (regressus)",
                    "10. PREUVE MORALE (argument carnéadien — détaillé séparément)",
                    "11. dispropotion humain/cosmos",
                    "12. instant naissance insaisissable",
                    "13. mort collective vs constellations différentes",
                    "14. animaux exclus ? incohérence",
                ],
            },
        ),
    ),
    "argument_favorinus_moral_proof_via_gellius_amand1945": dict(
        period="Roman Imperial",
        school="school_academy",
        md=md_base(
            page_range="p. 100",
            md_line_range="ll. 6129-6145",
            chapter="Livre I Ch. II §III.2 (Favorinus) — la preuve morale",
            chapter_actual="Livre I Ch. II §III.2 — Dixième argument de Favorinus",
            confidence=0.75,
            contains_latin=True,
            cited_editions=[
                "Aulu-Gelle, NA XIV, 1, 23, éd. C. Hosius, Leipzig 1903, t. II, p. 106 l. 31 — p. 107 l. 12",
            ],
            extra={
                "argument_category": "argument_carneadean_moral_reconstruction_via_witness_favorinus",
                "primary_witness_passage": "absent du corpus (NA XIV.1 non ingéré ; seul NA VII.2 présent)",
                "amand_witness_rank": "secondary_witness_indirect",
                "transmits_argument_pivots_b1": [
                    "argument_carneadean_virtue_vice_amand1945",
                    "argument_carneadean_action_futility_amand1945",
                ],
                "amand_judgement_quote_fr": "Cet argument n'est qu'une libre et brève adaptation d'une preuve de Carnéade. Il ne peut servir directement à la reconstitution",
                "favorinus_key_terms_latin": ["λογικὰ ζῷα (homines rationnels)", "νευρόσπαστα (marionnettes ridicules)", "ducentibus stellis et aurigantibus (planètes-charretiers)"],
                "evidence_pending": True,
                "evidence_pending_reason": "Aulu-Gelle NA XIV.1 absent du corpus (seul NA VII.2 ingéré)",
            },
        ),
    ),
    "synthesis_amand1945_favorinus_partial_astral_concession": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 100",
            md_line_range="ll. 6112-6128",
            chapter="Livre I Ch. II §III.2 (Favorinus) — la preuve morale",
            chapter_actual="Livre I Ch. II §III.2 — Concession astrale partielle",
            confidence=0.8,
            cited_editions=[
                "Sextus Empiricus, Adversus mathematicos V, 101 (parallèle)",
            ],
            extra={
                "amand_thesis_type": "doctrinal_observation",
                "amand_general_note": "Faiblesse fondamentale chez les adversaires païens de l'astrologie (et plusieurs chrétiens) : concessions successives aux principes et méthodes des astrologues",
                "favorinus_position": "antifatalisme limité à l'âme/volonté humaine ; astrologie tolérée pour les événements externes (météorologie, climat, marées)",
            },
        ),
    ),
    "synthesis_amand1945_maximus_tyre_mantike_freedom_reconciliation": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 101-103",
            md_line_range="ll. 6160-6276",
            chapter="Livre I Ch. II — Note supplémentaire (Maxime de Tyr)",
            chapter_actual="Livre I Ch. II — Note supplémentaire I : Maxime de Tyr",
            confidence=0.8,
            cited_editions=[
                "Maxime de Tyr, 13e discours (Dübner 19), éd. H. Hobein, Leipzig Teubner 1910, p. 158-170",
                "Maxime de Tyr, 5e discours (Dübner 11) Εἰ δεῖ εὔχεσθαι, éd. Hobein, p. 58-60",
                "Zeller, Philosophie der Griechen III/2/4 1903, p. 219-225, 229-231",
                "Ueberweg-Praechter, Philosophie des Altertums, p. 555-556",
                "E. de Faye, Origène II — L'ambiance philosophique, Paris 1927, p. 154-164",
            ],
            extra={
                "amand_thesis_type": "no_carneadean_trace_observation",
                "amand_finding": "Maxime de Tyr (sophiste-philosophe-platonicien éclectique, contemporain de Commode) ne porte AUCUNE trace de l'argumentation morale de Carnéade",
                "maximus_position_summary": "Concilie mantique oraculaire et liberté humaine ; pas d'incompatibilité ; mantique = oracle ; εἱμαρμένη régit l'ensemble, τὸ ἐφ' ἡμῖν est partie intégrante de l'εἱμαρμένη ; vie 'amphibie' (ἀμφίβιος) mélange de liberté et nécessité",
                "maximus_key_quote_gr": "εἰ δὲ ἀνακέκραται τὸ ἐφ' ἡμῖν τοῖς ὅλοις, μέρος ὅσον καὶ τοῦτο τῆς εἱμαρμένης",
                "engages_with_scholars": ["Zeller", "Hobein", "de Faye", "Praechter"],
            },
        ),
    ),
    "synthesis_amand1945_pseudo_plutarch_de_fato_conditional_heimarmene": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 104-106",
            md_line_range="ll. 6277-6411",
            chapter="Livre I Ch. II — Note supplémentaire (Pseudo-Plutarque)",
            chapter_actual="Livre I Ch. II — Note supplémentaire II : Pseudo-Plutarque",
            confidence=0.85,
            cited_editions=[
                "Pseudo-Plutarque, Περὶ εἱμαρμένης (De fato), §§1, 4, 6, 8, 11, éd. Bernardakis (Moralia, Teubner) Leipzig 1891, t. III, p. 467-484",
                "Xylander, Moralia, p. 568-575",
                "Döhner-Dübner (Coll. Didot), Paris 1885, t. I, p. 686-694",
                "Albinus, Διδασκαλικὸς τῶν Πλάτωνος δογμάτων ch. 26, éd. Dübner (Coll. Didot) Paris 1882, p. 250",
                "Zeller, Ph. Gr. III/2/4 1903, p. 229-231",
                "Ueberweg-Praechter, p. 555-556",
                "E. de Faye, Origène II, Paris 1927, p. 128-130",
            ],
            extra={
                "amand_thesis_type": "doctrinal_compromise_observation",
                "pseudo_plutarch_position_summary": "εἱμαρμένη = émanation de la Providence, λόγος θεῖος ἀπαράβατος ; s'applique aux êtres raisonnables ἐξ ὑποθέσεως ; tire les conséquences inéluctables des actions (consécution causale) mais ne produit pas ces actions ; sauvegarde le τὸ ἐφ' ἡμῖν ; Πάντα ἐν εἱμαρμένῃ ≠ Πάντα καθ' εἱμαρμένην",
                "pseudo_plutarch_school": "école d'Albinos et Atticos (platonisme moyen)",
                "pseudo_plutarch_authorship_status": "pseudépigraphe certain ; peut-être disciple de Plutarque",
                "albinus_parallel": "Didaskalikos ch. 26 — même doctrine 'πάντα ἐν εἱμαρμένῃ εἶναι, οὐ μὴν πάντα καθειμάρθαι'",
                "carneadean_traces": "le rédacteur mentionne les principaux arguments de Carnéade contre Chrysippe (sympathie, mantique, prière, responsabilité, hasard) mais sans dépendance textuelle",
            },
        ),
    ),
    "synthesis_amand1945_transmission_carneades_to_philo_chain": dict(
        period=None,
        school=None,
        md=md_base(
            page_range="p. 78-95 (synthèse transversale B3)",
            md_line_range="ll. 5159-5917",
            chapter="Livre I Ch. II §§I-II — synthèse de chaîne",
            chapter_actual="Synthèse transversale B3 : chaîne de transmission Carnéade→Philon",
            confidence=0.65,
            cited_editions=[
                "P. Wendland, Philos Schrift über die Vorsehung, Berlin 1892",
            ],
            extra={
                "amand_thesis_type": "transmission_chain_conjecture",
                "amand_judgement_register": "haute_probabilite_avoue",
                "chain_steps": [
                    "Carnéade (214/213-129/128 BCE) — Académie, n'écrit rien",
                    "Clitomaque (187/186-110/109 BCE) — disciple de Carnéade, 400+ livres perdus",
                    "ὑπόμνημα alexandrin (manuel scolaire perdu, contenu carnéadien condensé)",
                    "Philon d'Alexandrie (~25 BCE - ~50 CE), De providentia I, 79-87",
                ],
                "parallel_chain_via_cicero": [
                    "Carnéade → Clitomaque → Antiochus d'Ascalon (?) → Cicéron (De fato, De divinatione II) — voie latine indépendante",
                ],
                "amand_specific_claim": "L'argumentation carnéadienne morale n'est jamais transmise directement à la Patristique grecque (qui ne lit pas Cicéron) mais via les manuels scolaires alexandrins (ὑπομνήματα) et la chaîne Eusèbe → Chrysostome",
            },
        ),
    ),
}


# --------------------------------------------------------------------------
# NEW INSERTS : nodes additionnels manquants
# --------------------------------------------------------------------------

NEW_INSERTS: list[dict[str, Any]] = []


def make_node(
    *,
    nid: str,
    ntype: str,
    label: str,
    period: str | None,
    school: str | None,
    role: str | None,
    description: str,
    description_en: str,
    md: dict[str, Any],
    alternative_names: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": nid,
        "node_id": nid,
        "type": ntype,
        "label": label,
        "description": description,
        "description_en": description_en,
        "period": period,
        "role": role,
        "school": school,
        "alternative_names": json.dumps(alternative_names or []),
        "metadata": json.dumps(md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


# --- Person Maxime de Tyr ---
NEW_INSERTS.append(make_node(
    nid="person_maximus_of_tyre_125_185ce",
    ntype="person",
    label="Maximus of Tyre",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Maxime de Tyr (Μάξιμος ὁ Τύριος, c. 125 - c. 185 CE), sophiste-philosophe et platonicien éclectique "
        "contemporain de l'empereur Commode (règne 180-192 CE). Amand 1945 (p. 101-103) le caractérise comme un "
        "« prédicateur populaire de la philosophie », plus rhéteur que penseur original. Son corpus conservé consiste "
        "en 41 (selon Hobein) ou 40 (selon Dübner) διαλέξεις ou discours-conférences. Le 13e discours (Hobein) / 19e "
        "(Dübner), intitulé Εἰ μαντικῆς οὔσης, ἔστιν τι ἐφ' ἡμῖν ; (Si la mantique est réelle, y a-t-il encore quelque "
        "chose qui soit vraiment en notre pouvoir ?), pose la conciliation entre divination et liberté humaine. "
        "Maxime soutient que τὸ ἐφ' ἡμῖν est mêlé (ἀνακέκραται) à l'εἱμαρμένη, en est une partie intégrante, et que la "
        "vie humaine est « amphibie » (ἀμφίβιος) — mélange de liberté et de nécessité. Selon Amand, Maxime ne porte "
        "aucune trace de l'argumentation morale carnéadienne ; il représente plutôt un platonisme éclectique "
        "conciliant le déterminisme cosmique stoïcisant avec la liberté humaine, en évitant le débat antifataliste "
        "frontal."
    ),
    description_en=(
        "Maximus of Tyre (Μάξιμος ὁ Τύριος, c. 125 - c. 185 CE), sophistic philosopher and eclectic Platonist, "
        "contemporary of emperor Commodus (reign 180-192 CE). Amand 1945 (p. 101-103) characterizes him as a "
        "'popular preacher of philosophy', more rhetorician than original thinker. His extant corpus consists of 41 "
        "(Hobein) or 40 (Dübner) διαλέξεις or lecture-discourses. The 13th discourse (Hobein) / 19th (Dübner), "
        "entitled 'If mantic is real, is anything still in our power?' (Εἰ μαντικῆς οὔσης, ἔστιν τι ἐφ' ἡμῖν;), poses "
        "the reconciliation between divination and human freedom. Maximus holds that τὸ ἐφ' ἡμῖν is interwoven "
        "(ἀνακέκραται) with εἱμαρμένη and forms an integral part of it, and that human life is 'amphibious' "
        "(ἀμφίβιος) — a mixture of freedom and necessity. According to Amand, Maximus shows no trace of Carneades' "
        "moral argumentation; rather he represents an eclectic Platonism reconciling Stoicizing cosmic determinism "
        "with human freedom, while avoiding the frontal anti-fatalist debate."
    ),
    md=md_base(
        page_range="p. 101-103",
        md_line_range="ll. 6160-6276",
        chapter="Livre I Ch. II — Note supplémentaire I (Maxime de Tyr)",
        chapter_actual="Livre I Ch. II — Note supplémentaire I (Maxime de Tyr) — portrait",
        confidence=0.85,
        cited_editions=[
            "Hobein, Maximi Tyrii Philosophoumena, Leipzig Teubner 1910",
            "Dübner, Coll. Didot, Paris 1882",
        ],
        extra={
            "birth_date": "c. 125 CE",
            "death_date": "c. 185 CE",
            "amand_judgement_register": "evaluation_negative_assumée",
            "works": ["Διαλέξεις / Philosophoumena (41 ou 40 discours)"],
        },
    ),
    alternative_names=["Maximus Tyrius", "Maxime de Tyr", "Μάξιμος ὁ Τύριος"],
))


# --- Work Maxime de Tyr 13e discours ---
NEW_INSERTS.append(make_node(
    nid="work_maximus_tyre_dissertation_13",
    ntype="work",
    label="Maxime de Tyr, Dissertation 13 (Hobein) / 19 (Dübner) — Si la mantique est réelle, y a-t-il quelque chose en notre pouvoir ?",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "13e discours de Maxime de Tyr (numérotation Hobein 1910) = 19e (numérotation Dübner). Titre grec : "
        "Εἰ μαντικῆς οὔσης, ἔστιν τι ἐφ' ἡμῖν ; Édition de référence : Hobein, Maximi Tyrii Philosophoumena, "
        "Leipzig Teubner 1910, p. 158-170. La dissertation pose la conciliation entre divination oraculaire et "
        "liberté humaine. Maxime soutient (a) la réalité de la divination, (b) la liberté humaine (τὸ ἐφ' ἡμῖν) "
        "comme partie intégrante de l'εἱμαρμένη et non pas comme un domaine séparé, (c) la vie « amphibie » "
        "(ἀμφίβιος καὶ κεκραμένη ὁμοῦ ἐξουσίᾳ καὶ ἀνάγκῃ). Il condamne les termes populaires de la fatalité "
        "(πεπρωμένη, Ἐρινύς, Aἶσα, Μοῖρα) comme prétextes au vice. Position finale : nous sommes la cause de nos "
        "misères morales, pas Dieu, pas l'εἱμαρμένη. Aucune trace de l'argumentation morale carnéadienne selon "
        "Amand 1945, p. 101-103."
    ),
    description_en=(
        "Dissertation 13 (Hobein numbering) = 19 (Dübner) of Maximus of Tyre. Greek title: "
        "Εἰ μαντικῆς οὔσης, ἔστιν τι ἐφ' ἡμῖν; Reference edition: Hobein, Maximi Tyrii Philosophoumena, "
        "Leipzig Teubner 1910, p. 158-170. The dissertation poses the reconciliation between oracular divination "
        "and human freedom. Maximus argues (a) the reality of divination, (b) human freedom (τὸ ἐφ' ἡμῖν) as an "
        "integral part of εἱμαρμένη rather than a separate domain, (c) the 'amphibious' life (ἀμφίβιος καὶ "
        "κεκραμένη ὁμοῦ ἐξουσίᾳ καὶ ἀνάγκῃ). He condemns popular fate terms (πεπρωμένη, Ἐρινύς, Aἶσα, Μοῖρα) as "
        "pretexts for vice. Final position: we are the cause of our moral misery, not God, not εἱμαρμένη. No trace "
        "of Carneades' moral argumentation according to Amand 1945, p. 101-103."
    ),
    md=md_base(
        page_range="p. 101-103",
        md_line_range="ll. 6160-6276",
        chapter="Livre I Ch. II — Note supplémentaire I (Maxime de Tyr)",
        chapter_actual="Livre I Ch. II — Note supplémentaire I (œuvre-shell)",
        confidence=0.85,
        cited_editions=[
            "Hobein, Maximi Tyrii Philosophoumena, Leipzig Teubner 1910, p. 158-170",
        ],
        evidence_pending=True,
        evidence_pending_reason="Maxime de Tyr Dissertation 13 absente du corpus EleutherIA",
        extra={
            "title_greek": "Εἰ μαντικῆς οὔσης, ἔστιν τι ἐφ' ἡμῖν ;",
            "title_french": "Si la mantique est réelle, y a-t-il encore quelque chose qui soit vraiment en notre pouvoir ?",
            "hobein_numbering": "13",
            "dubner_numbering": "19",
        },
    ),
))


# --- Favorinus works shells (3) ---
NEW_INSERTS.append(make_node(
    nid="work_favorinus_pyrrhoneioi_tropoi",
    ntype="work",
    label="Favorinus, Pyrrhoneioi tropoi (Πυρρώνειοι τρόποι)",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Œuvre perdue de Favorinus d'Arles, titre grec Πυρρώνειοι τρόποι (Tropes pyrrhoniens), mentionnée par "
        "Aulu-Gelle (NA XI, 5) et par Diogène Laërce (IX, 78, 87). Selon Amand 1945 (p. 96-100, qui rattache "
        "Favorinus au scepticisme néo-académicien plus qu'au pyrrhonisme strict), cet ouvrage témoigne du caractère "
        "éclectique et de la perméabilité de Favorinus aux courants sceptiques tardifs. Aucun fragment substantiel "
        "n'est conservé."
    ),
    description_en=(
        "Lost work by Favorinus of Arles, Greek title Πυρρώνειοι τρόποι (Pyrrhonian Modes), mentioned by Aulus "
        "Gellius (NA XI.5) and Diogenes Laertius (IX.78, 87). According to Amand 1945 (p. 96-100, who attaches "
        "Favorinus to neo-Academic skepticism more than strict Pyrrhonism), this work attests Favorinus' eclectic "
        "character and his permeability to late skeptical currents. No substantial fragments are preserved."
    ),
    md=md_base(
        page_range="p. 96-97",
        md_line_range="ll. 5919-6000",
        chapter="Livre I Ch. II §III (Favorinus)",
        chapter_actual="Livre I Ch. II §III — Favorinus (work-shell)",
        confidence=0.85,
        evidence_pending=True,
        evidence_pending_reason="Œuvre perdue ; aucun fragment substantiel conservé",
        extra={
            "preservation_status": "lost",
            "title_greek": "Πυρρώνειοι τρόποι",
            "title_french": "Tropes pyrrhoniens",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="work_favorinus_peri_phyges",
    ntype="work",
    label="Favorinus, Peri phygēs (Περὶ φυγῆς)",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Traité de Favorinus d'Arles intitulé Περὶ φυγῆς (Sur l'exil), partiellement retrouvé en 1931 dans le "
        "Papyrus Vaticano Greco 11 publié par M. Norsa et G. Vitelli (Studi e testi 53, Rome, Cité du Vatican, "
        "1931). Selon Amand 1945 (p. 97 note 2), cette « récente découverte » a « encore mieux permis de mesurer "
        "[le] peu de profondeur intellectuelle » de Favorinus. W. Schmid a consacré au papyrus un long article dans "
        "le Supplementband VI de la Real-Encyclopädie (1935, col. 65-70). L'œuvre traite des thèmes de la "
        "consolation philosophique en exil — Favorinus a lui-même connu un exil sous Hadrien à Chios."
    ),
    description_en=(
        "Treatise by Favorinus of Arles entitled Περὶ φυγῆς (On Exile), partially recovered in 1931 in Papyrus "
        "Vaticano Greco 11 published by M. Norsa and G. Vitelli (Studi e testi 53, Rome, Vatican City, 1931). "
        "According to Amand 1945 (p. 97 fn. 2), this 'recent discovery' has 'allowed us to gauge even better [the] "
        "intellectual shallowness' of Favorinus. W. Schmid devoted a long article to the papyrus in Supplement VI "
        "of the Real-Encyclopädie (1935, col. 65-70). The work addresses themes of philosophical consolation in "
        "exile — Favorinus himself experienced exile under Hadrian on Chios."
    ),
    md=md_base(
        page_range="p. 97",
        md_line_range="ll. 5985-5995",
        chapter="Livre I Ch. II §III (Favorinus)",
        chapter_actual="Livre I Ch. II §III — Favorinus (work-shell)",
        confidence=0.9,
        evidence_pending=True,
        evidence_pending_reason="Texte papyrologique partiel ; non ingéré dans EleutherIA",
        cited_editions=[
            "Norsa & Vitelli, Φαβωρίνου Περὶ φυγῆς (Pap. Vat. Greco 11), Studi e testi 53, Rome 1931",
            "Schmid, RE Suppl. VI, Stuttgart 1935, col. 65-70",
        ],
        extra={
            "preservation_status": "papyrological_partial",
            "title_greek": "Περὶ φυγῆς",
            "title_french": "Sur l'exil",
            "papyrus_id": "Papyrus Vaticano Greco 11",
        },
    ),
))

# Note: Favorinus n'a pas de Peri heimarmenes nommément ; je laisse tomber cet ID candidat


# --- Concepts ---
NEW_INSERTS.append(make_node(
    nid="concept_heimarmene_conditional_amand1945",
    ntype="concept",
    label="εἱμαρμένη conditionnelle (ἐξ ὑποθέσεως) — platonisme moyen (Pseudo-Plutarque, Albinus)",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Concept doctrinal du platonisme moyen identifié par Amand 1945 (p. 104-106) dans la dissertation "
        "Pseudo-Plutarque, Περὶ εἱμαρμένης (De fato), et son parallèle chez Albinus, Didaskalikos ch. 26. "
        "Définition technique : l'εἱμαρμένη est une loi cosmique (λόγος θεῖος ἀπαράβατος) qui s'applique aux "
        "êtres raisonnables ἐξ ὑποθέσεως, c'est-à-dire conditionnellement. Elle tire les conséquences "
        "inéluctables des actions humaines libres (consécution nécessaire) mais ne produit pas ces actions "
        "(causation antécédente). Distinction technique : Πάντα ἐν εἱμαρμένῃ εἶναι (tout est dans le destin) "
        "≠ Πάντα καθ' εἱμαρμένην (tout est par le destin). Cette doctrine sauvegarde le τὸ ἐφ' ἡμῖν et le hasard. "
        "Elle constitue le compromis platonicien moyen contre le fatalisme absolu de Chrysippe, tout en "
        "concédant la majorité des thèses stoïciennes (Providence, ordre cosmique, sympathie universelle, "
        "principe du tiers exclu, mantique). Position dialectique intermédiaire entre stoïcisme et "
        "antifatalisme académicien."
    ),
    description_en=(
        "Doctrinal concept of Middle Platonism identified by Amand 1945 (p. 104-106) in Pseudo-Plutarch's "
        "treatise Περὶ εἱμαρμένης (De fato) and its parallel in Albinus, Didaskalikos ch. 26. Technical "
        "definition: εἱμαρμένη is a cosmic law (λόγος θεῖος ἀπαράβατος) that applies to rational beings "
        "ἐξ ὑποθέσεως, conditionally. It draws the inescapable consequences from free human actions (necessary "
        "consecution) but does not produce these actions (antecedent causation). Technical distinction: "
        "Πάντα ἐν εἱμαρμένῃ εἶναι (all is within fate) ≠ Πάντα καθ' εἱμαρμένην (all is by fate). This doctrine "
        "preserves τὸ ἐφ' ἡμῖν and chance. It constitutes the Middle Platonist compromise against Chrysippus' "
        "absolute fatalism, while conceding most Stoic theses (Providence, cosmic order, universal sympathy, "
        "principle of excluded middle, mantic). Intermediate dialectical position between Stoicism and Academic "
        "anti-fatalism."
    ),
    md=md_base(
        page_range="p. 104-106",
        md_line_range="ll. 6277-6411",
        chapter="Livre I Ch. II — Note supplémentaire II (Pseudo-Plutarque)",
        chapter_actual="Livre I Ch. II — concept-clef du Pseudo-Plutarque",
        confidence=0.85,
        cited_editions=[
            "Pseudo-Plutarque, Περὶ εἱμαρμένης, §§1, 4, 6, 8, 11",
            "Albinus, Didaskalikos ch. 26",
        ],
        extra={
            "concept_key_terms": ["ἐξ ὑποθέσεως", "ἀπαράβατος", "Πάντα ἐν εἱμαρμένῃ vs Πάντα καθ' εἱμαρμένην"],
            "doctrinal_school": "platonisme moyen (Albinos, Atticus, Pseudo-Plutarque)",
            "saves": ["τὸ ἐφ' ἡμῖν", "le hasard", "le possible (τὸ ἐνδεχόμενον)", "la prière", "la responsabilité morale"],
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="concept_signs_not_causes_philo_amand1945",
    ntype="concept",
    label="Astres signes (σημεῖα) plutôt que causes — position philonienne",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Concept identifié par Amand 1945 (p. 87-90, ll. 5518-5656) dans le corpus philonien : Philon adopte "
        "une position doctrinale intermédiaire à l'égard de l'astrologie. (a) Son monothéisme juif l'oblige "
        "à proscrire l'adoration des astres (astrolâtrie) ; (b) mais il accepte que les astres soient des "
        "« vivants intellectuels » (ζῷα νοερά) doués d'intelligence et d'une perfection morale, dieux "
        "secondaires soumis au Démiurge ; (c) il accepte que les astres soient causes efficientes secondes de "
        "certains changements sublunaires ; (d) surtout, il interprète Genèse 1, 14 (« qu'ils servent de signes ») "
        "comme autorisant une astrologie-divination par les signes (σημεῖα μελλόντων προφαίνωσιν) sans "
        "déterminisme astral absolu. Les astres font connaître à l'avance les événements terrestres par "
        "observations répétées, sans que les humains soient nécessités. Cette position « concessive » est "
        "typique selon Amand des adversaires païens et chrétiens (jusqu'à Origène et Bardesane) qui tolèrent "
        "une astrologie purgée du fatalisme absolu. Source matérielle : De opificio mundi 55, 58, 73 ; "
        "De specialibus legibus I.13-19, 66, 89-92 ; De congressu eruditionis gratia §50 ; Quaestiones in "
        "Exodum II, 74-81."
    ),
    description_en=(
        "Concept identified by Amand 1945 (p. 87-90, ll. 5518-5656) in the Philonic corpus: Philo adopts an "
        "intermediate doctrinal position vis-à-vis astrology. (a) His Jewish monotheism obliges him to "
        "proscribe star-worship (astrolatry); (b) but he accepts that stars are 'intellectual living beings' "
        "(ζῷα νοερά) endowed with intelligence and moral perfection, secondary gods subject to the Demiurge; "
        "(c) he accepts that stars are second-order efficient causes of some sublunary changes; (d) most "
        "importantly, he interprets Genesis 1:14 ('let them serve as signs') as authorizing astrology-as-"
        "divination via signs (σημεῖα μελλόντων προφαίνωσιν) without absolute astral determinism. Stars "
        "foretell terrestrial events through repeated observation, without humans being necessitated. According "
        "to Amand this 'concessive' position is typical of pagan and Christian adversaries (up to Origen and "
        "Bardesanes) who tolerate astrology purged of absolute fatalism. Source material: De opificio mundi 55, "
        "58, 73; De specialibus legibus I.13-19, 66, 89-92; De congressu §50; Quaestiones in Exodum II.74-81."
    ),
    md=md_base(
        page_range="p. 87-90",
        md_line_range="ll. 5518-5656",
        chapter="Livre I Ch. II §II (Philon) — attitude envers les astres",
        chapter_actual="Livre I Ch. II §II.4 — concept de l'astrologie comme signes",
        confidence=0.85,
        cited_editions=[
            "Philon, De opificio mundi 55, 58, 73, 144 (éd. Cohn t. I 1896)",
            "Philon, De specialibus legibus I (De monarchia + De sacerdotibus), éd. Cohn t. V 1906",
            "Philon, De congressu §50, éd. Wendland",
            "Philon, Quaestiones in Exodum II, 74, 78, 81 (texte arménien)",
        ],
        extra={
            "concept_key_terms": ["σημεῖα μελλόντων", "ζῷα νοερά", "δοῦλα δευτερότητος (causes secondes)"],
            "philo_biblical_anchor": "Genèse 1, 14",
            "tradition_lineage": "position concessive partagée par Origène, Bardesane (astrologie sans fatalisme absolu)",
        },
    ),
))

NEW_INSERTS.append(make_node(
    nid="concept_polymathy_favorinus_amand1945",
    ntype="concept",
    label="Polymathie sophistique (Favorinus) — érudition encyclopédique sans rigueur",
    period="Roman Imperial",
    school=None,
    role=None,
    description=(
        "Concept identifié par Amand 1945 (p. 97-98, ll. 5950-5988) dans le portrait de Favorinus d'Arles : "
        "la « polymathie » (πολυμάθεια) au sens péjoratif d'érudition encyclopédique étalée sans rigueur "
        "philosophique. Selon Amand, Favorinus incarne le type de la « commère savante » qui « se drape dans "
        "un vêtement d'orateur ou de philosophe », fondateur de la polygraphie déversant des encyclopédies dans "
        "des Mélanges, des Στρώματα ou des Συμπόσια. Le concept articule trois traits : (1) topiques multiples "
        "(lieux communs moraux, grammaire, jurisprudence, sciences naturelles, etc.) ; (2) niveau de profondeur "
        "faible (« peu de profondeur intellectuelle » selon Amand, confirmé par la découverte du Περὶ φυγῆς) ; "
        "(3) instabilité doctrinale (« changea de système philosophique aussi souvent qu'il lui prit fantaisie "
        "de toucher à des sujets nouveaux »). C'est dans ce cadre que s'inscrivent les 14 arguments "
        "antiastrologiques d'Aulu-Gelle NA XIV.1 : « peu originaux », « jetés en vrac, et la plupart simplement "
        "esquissés »."
    ),
    description_en=(
        "Concept identified by Amand 1945 (p. 97-98, ll. 5950-5988) in his portrait of Favorinus of Arles: "
        "'polymathy' (πολυμάθεια) in the pejorative sense of encyclopedic erudition displayed without "
        "philosophical rigor. According to Amand, Favorinus embodies the 'learned gossip' type who 'drapes "
        "himself in the cloak of orator or philosopher', a founder of polygraphy pouring encyclopedias into "
        "Miscellanies, Στρώματα or Συμπόσια. The concept articulates three features: (1) multiple topics "
        "(moral commonplaces, grammar, jurisprudence, natural sciences, etc.); (2) shallow depth ('little "
        "intellectual depth' per Amand, confirmed by the discovery of Περὶ φυγῆς); (3) doctrinal instability "
        "('changed philosophical system as often as he fancied to touch a new subject'). In this frame Amand "
        "places the 14 anti-astrological arguments of Aulus Gellius NA XIV.1: 'unoriginal', 'tossed pell-mell, "
        "most simply sketched'."
    ),
    md=md_base(
        page_range="p. 97-98",
        md_line_range="ll. 5950-5988",
        chapter="Livre I Ch. II §III (Favorinus) — la polémique antiastrologique",
        chapter_actual="Livre I Ch. II §III — concept de polymathie sophistique",
        confidence=0.75,
        cited_editions=[],
        extra={
            "concept_key_term_greek": "πολυμάθεια",
            "register": "evaluation_negative_dom_amand",
            "context_of_application": "polygraphie de la Seconde Sophistique",
        },
    ),
))


# --- Syntheses additionnelles ---

NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_cicero_ch2i_cadre",
    ntype="synthesis",
    label="Amand 1945 — Cadre Cicéron : transmetteur latin indirect du De fato carnéadien",
    period=None,
    school=None,
    role=None,
    description=(
        "Cadre synthétique d'Amand 1945 (p. 78-80, ll. 5159-5230) sur le rôle de Cicéron dans la transmission "
        "de l'argumentation antifataliste carnéadienne. Position d'Amand : Cicéron est le « traducteur "
        "romain » qui ne reconstitue pas en latin une discussion grecque mais qui (1) abrège un dossier "
        "carnéadien préexistant — probablement issu d'Antiochus d'Ascalon ou de Posidonius ; (2) place ce "
        "dossier dans la première partie du De fato, aujourd'hui presque entièrement perdue (lacune estimée "
        "par A. Yon 1933 à 30+ pages CUF) ; (3) en conserve un fragment résiduel au §17.40 (chaîne fatale "
        "assentiment-tendance-action) ; (4) en signale un autre fragment dans le De divinatione II.8.21 "
        "(argument anti-mantique). Selon Amand, la Patristique grecque ne lit pas directement Cicéron mais "
        "reçoit le même fonds carnéadien par les ὑπομνήματα alexandrins (manuels scolaires perdus). Cicéron "
        "est donc un témoin parallèle, non un transmetteur direct vers Eusèbe-Chrysostome. Confidence "
        "modérée : la reconstruction de la source d'Antiochus est conjecturale."
    ),
    description_en=(
        "Synthetic framework from Amand 1945 (p. 78-80, ll. 5159-5230) on Cicero's role in transmitting "
        "Carneades' anti-fatalist argumentation. Amand's position: Cicero is the 'Roman translator' who does "
        "not reconstruct in Latin a Greek discussion but rather (1) abridges a pre-existing Carneadean "
        "dossier — probably from Antiochus of Ascalon or Posidonius; (2) places this dossier in the first part "
        "of De fato, now almost entirely lost (lacuna estimated by A. Yon 1933 at 30+ CUF pages); (3) "
        "preserves a residual fragment at §17.40 (the fatal chain assent-impulse-action); (4) signals another "
        "fragment in De divinatione II.8.21 (anti-mantic argument). According to Amand, Greek Patristics does "
        "not read Cicero directly but receives the same Carneadean fund via Alexandrian ὑπομνήματα (lost "
        "scholastic manuals). Cicero is thus a parallel witness, not a direct transmitter to Eusebius-"
        "Chrysostom. Moderate confidence: the Antiochus source reconstruction is conjectural."
    ),
    md=md_base(
        page_range="p. 78-80",
        md_line_range="ll. 5159-5230",
        chapter="Livre I Ch. II §I (Cicéron) — cadre du chapitre",
        chapter_actual="Livre I Ch. II §I — Cicéron : cadre transversal",
        confidence=0.75,
        cited_editions=[
            "Cicéron, De fato, éd. A. Yon, CUF Paris 1933",
            "Cicéron, De divinatione II, éd. W. Ax",
        ],
        extra={
            "amand_thesis_type": "transmission_framework",
            "amand_judgement_register": "haute_probabilite_avoue",
            "transmission_status": "parallel_witness_not_direct_to_patristic",
        },
    ),
))


NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_pseudo_plutarch_albinus_parallel",
    ntype="synthesis",
    label="Amand 1945 — Parallèle Pseudo-Plutarque ↔ Albinus (Didaskalikos ch. 26) sur εἱμαρμένη conditionnelle",
    period=None,
    school=None,
    role=None,
    description=(
        "Synthèse d'Amand 1945 (p. 106 note 3, ll. 6404-6411) établissant le parallèle doctrinal entre le "
        "Pseudo-Plutarque (De fato §§1, 4, 6, 8, 11) et Albinus (Didaskalikos ch. 26 — Εἰσαγωγὴ εἰς τὴν "
        "φιλοσοφίαν Πλάτωνος). Les deux auteurs partagent la même position de platonisme moyen : πάντα ἐν "
        "εἱμαρμένῃ εἶναι, οὐ μὴν πάντα καθειμάρθαι. L'εἱμαρμένη tire les conséquences nécessaires de nos "
        "actions libres sans les produire. Liberté totale, responsabilité morale, éloge/blâme parfaitement "
        "sauvegardés. L'âme n'a pas de maître. Comme le Pseudo-Plutarque (3), Albinus refuse de voir dans "
        "l'εἱμαρμένη un ἄπειρον (infini illimité). Selon Amand, cette convergence doctrinale atteste un fonds "
        "scolaire commun de l'école d'Albinos et Atticos, contemporain ou postérieur de Plutarque. La doctrine "
        "préfigure le compromis qu'Origène utilisera dans son Commentaire sur la Genèse pour gérer la mantique "
        "biblique sans fatalisme. Référence édition : Platonis opera ex recensione Dübneri, Coll. Didot, Paris "
        "1882, p. 250, ll. 11-28."
    ),
    description_en=(
        "Synthesis from Amand 1945 (p. 106 fn. 3, ll. 6404-6411) establishing the doctrinal parallel between "
        "Pseudo-Plutarch (De fato §§1, 4, 6, 8, 11) and Albinus (Didaskalikos ch. 26 — Introduction to Plato's "
        "Philosophy). The two authors share the same Middle Platonist position: πάντα ἐν εἱμαρμένῃ εἶναι, οὐ "
        "μὴν πάντα καθειμάρθαι. εἱμαρμένη draws the necessary consequences from our free actions without "
        "producing them. Total freedom, moral responsibility, praise/blame perfectly preserved. The soul has "
        "no master. Like Pseudo-Plutarch (§3), Albinus refuses to see εἱμαρμένη as an ἄπειρον (unlimited "
        "infinite). According to Amand, this doctrinal convergence attests a common scholastic background of "
        "the Albinus-Atticus school, contemporary or posterior to Plutarch. The doctrine prefigures the "
        "compromise Origen will use in his Commentary on Genesis to handle biblical mantic without fatalism. "
        "Edition reference: Platonis opera ex recensione Dübneri, Coll. Didot, Paris 1882, p. 250, lines 11-28."
    ),
    md=md_base(
        page_range="p. 106",
        md_line_range="ll. 6404-6411",
        chapter="Livre I Ch. II — Note supplémentaire II (Pseudo-Plutarque)",
        chapter_actual="Livre I Ch. II — parallèle Pseudo-Plutarque/Albinus",
        confidence=0.85,
        cited_editions=[
            "Albinus, Didaskalikos ch. 26, éd. Dübner, Coll. Didot, Paris 1882, p. 250, ll. 11-28",
            "Praechter, in Ueberweg-Praechter, Philosophie des Altertums, p. 541-545",
        ],
        extra={
            "amand_thesis_type": "doctrinal_parallel",
            "doctrine_shared": "εἱμαρμένη conditionnelle (ἐξ ὑποθέσεως)",
            "key_quote_greek": "πάντα ἐν εἱμαρμένῃ εἶναι, οὐ μὴν πάντα καθειμάρθαι",
        },
    ),
))


NEW_INSERTS.append(make_node(
    nid="synthesis_amand1945_philo_de_providentia_witness_n1_status",
    ntype="synthesis",
    label="Amand 1945 — Statut philologique du témoin n°1 (Philon, De prov. I, 79-87) : préservation arménienne",
    period=None,
    school=None,
    role=None,
    description=(
        "Synthèse philologique d'Amand 1945 (p. 91, 93-95, ll. 5710-5917) sur le statut du témoin n°1. (a) Le "
        "texte grec original du De providentia philonien est presque entièrement perdu ; (b) seule la "
        "traduction arménienne mékhitariste de J.-B. Aucher (Venise, Saint-Lazare, 1822) en restitue le "
        "contenu — paginée I à 121 du tome I ; (c) Eusèbe de Césarée préserve dans la Préparation évangélique "
        "VII, 21 et VIII, 14 des extraits grecs partiels mais NON les sections 79-87 du livre I (Amand est "
        "explicite : « les §79-83 ne sont pas dans le matériel restitué par Eusèbe »). (d) La citation "
        "qu'Amand publie dans son texte (p. 93-95) est en latin (Aucher 1822) — Amand n'invente aucun grec et "
        "reproduit fidèlement le latin philologique mékhitariste. Conséquence pour la KG EleutherIA : tout "
        "claim qui invoque Philon De providentia I, 79-83 est en evidence_pending tant que ces passages ne "
        "sont pas ingérés (ingestion en cours, cf. docs/reports/2026-05-15-amand-six-witnesses-audit.md). "
        "Statut épistémique : témoin n°1 chronologiquement premier mais textuellement le plus médié."
    ),
    description_en=(
        "Philological synthesis from Amand 1945 (p. 91, 93-95, ll. 5710-5917) on the status of witness no. 1. "
        "(a) The original Greek text of Philo's De providentia is almost entirely lost; (b) only the Armenian "
        "Mekhitarist translation by J.-B. Aucher (Venice, Saint-Lazare, 1822) restores its content — paginated "
        "I to 121 of tome I; (c) Eusebius of Caesarea preserves in Praeparatio evangelica VII.21 and VIII.14 "
        "partial Greek extracts but NOT sections 79-87 of book I (Amand is explicit: 'sections 79-83 are not "
        "in the material restored by Eusebius'). (d) The quotation Amand publishes in his text (p. 93-95) is "
        "in Latin (Aucher 1822) — Amand invents no Greek and faithfully reproduces the Mekhitarist "
        "philological Latin. Consequence for the EleutherIA KG: every claim invoking Philo De providentia I, "
        "79-83 is in evidence_pending status until these passages are ingested (ingestion in progress, see "
        "docs/reports/2026-05-15-amand-six-witnesses-audit.md). Epistemic status: witness no. 1 "
        "chronologically first but textually the most mediated."
    ),
    md=md_base(
        page_range="p. 91, 93-95",
        md_line_range="ll. 5710-5917",
        chapter="Livre I Ch. II §II.5 (Philon) — analyse argumentation morale",
        chapter_actual="Livre I Ch. II §II.5 — statut philologique du témoin n°1",
        confidence=0.95,
        cited_editions=[
            "Philonis Iudaei sermones tres hactenus inediti, I. et II. de providentia et III. de animalibus, ex Armena versione antiquissima ab ipso originali textu Graeco ad verbum stricte exsequuta, … per P. Io. Baptistam Aucher, Venise, Saint-Lazare, 1822, t. I p. 1-121",
            "Eusèbe, Préparation évangélique VII.21 et VIII.14 (extraits grecs)",
        ],
        extra={
            "amand_thesis_type": "philological_status",
            "preservation_status": "armenian_translation_aucher_1822",
            "witness_rank": "primary_n1",
            "evidence_pending": True,
            "evidence_pending_reason": "Philon De Providentia I, 79-87 absent du corpus EleutherIA (ingestion Aucher en cours)",
        },
    ),
))


# --- Argument-envelope Philon : cadre des 4 arguments ---
NEW_INSERTS.append(make_node(
    nid="argument_philo_de_providentia_argument_envelope_amand1945",
    ntype="argument",
    label="Argument-cadre Philon De prov. I.77-88 — l'enveloppe quadripartite de la diatribe antifataliste",
    period="Hellenistic",
    school="school_academy",
    role=None,
    description=(
        "Enveloppe argumentative générale identifiée par Amand 1945 (p. 84-85, ll. 5371-5394) à l'intérieur du "
        "Περὶ προνοίας I, 77-88 de Philon. Selon Amand, Philon « met en ligne des arguments dont Wendland a "
        "décelé l'origine néo-académicienne et dont il a prouvé la provenance carnéadienne » (p. 84). La "
        "diatribe antiastrologique s'organise en 4 points (4 sub-arguments distincts, traités séparément dans "
        "les nœuds argument_philo_de_providentia_*_amand1945) : (1) chef moral §§78-83 — fatalisme rend "
        "magistrats et lois absurdes ; (2) chef ethnographique §§84-86 — uniformité des coutumes nationales ; "
        "(3) chef mort collective §87(début) — multiples destins/une seule mort ; (4) chef moment de la "
        "conception §87(fin) — instant insaisissable. Cadre rhétorique : Philon expose en français/arménien "
        "philosophique mais le squelette argumentatif vient d'un ὑπόμνημα scolaire alexandrin qui condense "
        "Carnéade. Le §77-78 (« l'homme rejette le frein de la Providence ») constitue un cadrage théologique "
        "philonien propre, étranger à Carnéade, par lequel Philon réinscrit l'argumentation sceptique dans une "
        "théologie monothéiste."
    ),
    description_en=(
        "General argumentative envelope identified by Amand 1945 (p. 84-85, ll. 5371-5394) inside Philo's "
        "Περὶ προνοίας I, 77-88. According to Amand, Philo 'aligns arguments whose neo-Academic origin "
        "Wendland has detected and whose Carneadean provenance he has proved' (p. 84). The anti-astrological "
        "diatribe is organized in 4 points (4 distinct sub-arguments, treated separately in the "
        "argument_philo_de_providentia_*_amand1945 nodes): (1) moral head §§78-83 — fatalism renders "
        "magistrates and laws absurd; (2) ethnographic head §§84-86 — uniformity of national customs; (3) "
        "collective death head §87(opening) — multiple destinies/one death; (4) moment of conception head "
        "§87(end) — unseizable instant. Rhetorical frame: Philo expounds in philosophical French/Armenian, but "
        "the argumentative skeleton comes from an Alexandrian scholastic ὑπόμνημα condensing Carneades. "
        "§§77-78 ('man rejects Providence's bridle') constitutes a Philonic theological framing proper, "
        "foreign to Carneades, by which Philo reinscribes the skeptical argumentation in a monotheist theology."
    ),
    md=md_base(
        page_range="p. 84-85",
        md_line_range="ll. 5371-5394",
        chapter="Livre I Ch. II §II.4 (Philon) — analyse argumentation morale",
        chapter_actual="Livre I Ch. II §II.5 — enveloppe des 4 arguments philoniens",
        confidence=0.85,
        cited_editions=[
            "Philon, De providentia I, 77-88, éd. Aucher 1822",
            "Wendland, Philos Schrift über die Vorsehung, Berlin 1892, p. 24-37",
        ],
        evidence_pending=True,
        evidence_pending_reason="Philon De Providentia I, 77-88 absent du corpus EleutherIA",
        extra={
            "envelope_for_sub_arguments": [
                "argument_philo_de_providentia_moral_responsibility_amand1945",
                "argument_philo_de_providentia_ethnic_customs_amand1945",
                "argument_philo_de_providentia_collective_death_amand1945",
                "argument_philo_de_providentia_conception_moment_amand1945",
            ],
            "argument_category": "argument_carneadean_moral_reconstruction_envelope",
            "amand_witness_rank": "primary_witness_n1_structure",
        },
    ),
))


# --------------------------------------------------------------------------
# EDGES : evidenced_by + transmits_to + discusses + cites
# --------------------------------------------------------------------------

NEW_EDGES: list[dict[str, Any]] = []


def make_edge(*, src: str, tgt: str, relation: str, confidence: float, md: dict[str, Any] | None = None) -> dict[str, Any]:
    edge_md = md.copy() if md else {}
    edge_md.setdefault("wave", WAVE_TAG)
    edge_md.setdefault("claimed_by", SCHOLAR_ID)
    edge_md.setdefault("publication", PUB_ID)
    edge_md.setdefault("bibtex_key", BIBTEX)
    edge_id = f"{src}__{relation}__{tgt}"[:200]
    return {
        "id": edge_id,
        "edge_id": edge_id,
        "source": src,
        "target": tgt,
        "source_node_id": src,
        "target_node_id": tgt,
        "relation": relation,
        "type": relation,
        "confidence": confidence,
        "metadata": json.dumps(edge_md, ensure_ascii=False),
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    }


# Cicero De fato §17 et §40 : evidenced_by pour l'argument carnéadien
NEW_EDGES.append(make_edge(
    src="argument_carneadean_assent_chain_via_cicero_amand1945",
    tgt="passage_cic_fat_17",
    relation="evidenced_by",
    confidence=0.95,
    md={"source_text_role": "primary_witness_residual_fragment", "amand_page": "p. 79"},
))
NEW_EDGES.append(make_edge(
    src="argument_carneadean_assent_chain_via_cicero_amand1945",
    tgt="passage_cic_fat_40",
    relation="evidenced_by",
    confidence=0.95,
    md={"source_text_role": "primary_witness_residual_fragment", "amand_page": "p. 79"},
))

# Cicero De div II.8.21 (numéroté passage_cic_div_21 dans EleutherIA)
NEW_EDGES.append(make_edge(
    src="argument_cicero_de_div_anti_mantike_amand1945",
    tgt="passage_cic_div_21",
    relation="evidenced_by",
    confidence=0.9,
    md={"source_text_role": "primary_witness_anti_mantic_fragment", "amand_page": "p. 80 fn. 1"},
))

# Authorship work-shells
NEW_EDGES.append(make_edge(
    src="work_maximus_tyre_dissertation_13",
    tgt="person_maximus_of_tyre_125_185ce",
    relation="authored_by",
    confidence=1.0,
))
NEW_EDGES.append(make_edge(
    src="work_favorinus_pyrrhoneioi_tropoi",
    tgt="person_favorinus_of_arles_9n4o6q32",
    relation="authored_by",
    confidence=1.0,
))
NEW_EDGES.append(make_edge(
    src="work_favorinus_peri_phyges",
    tgt="person_favorinus_of_arles_9n4o6q32",
    relation="authored_by",
    confidence=1.0,
))

# Discusses edges : pseudo-Plutarque / Albinus / Maxime de Tyr
NEW_EDGES.append(make_edge(
    src="person_pseudo_plutarch_2c_ce",
    tgt="concept_heimarmene_conditional_amand1945",
    relation="discusses",
    confidence=0.95,
    md={"amand_locus": "De fato §§1, 4, 6, 8, 11"},
))
NEW_EDGES.append(make_edge(
    src="work_plutarch_de_fato_complete",
    tgt="concept_heimarmene_conditional_amand1945",
    relation="discusses",
    confidence=0.95,
))
NEW_EDGES.append(make_edge(
    src="person_maximus_of_tyre_125_185ce",
    tgt="concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
    relation="discusses",
    confidence=0.8,
    md={"amand_locus": "13e discours / Dübner 19"},
))
NEW_EDGES.append(make_edge(
    src="person_philo_alexandria_a1b2c3d4",
    tgt="concept_signs_not_causes_philo_amand1945",
    relation="discusses",
    confidence=0.95,
))
NEW_EDGES.append(make_edge(
    src="person_favorinus_of_arles_9n4o6q32",
    tgt="concept_polymathy_favorinus_amand1945",
    relation="discusses",
    confidence=0.7,
    md={"amand_judgement_register": "evaluation_negative_assumée"},
))

# Influence / transmission
NEW_EDGES.append(make_edge(
    src="person_carneades_214_129bce_l2m3n4o5",
    tgt="person_cicero_marcus_tullius_106_43bce_a8f3d2c1",
    relation="influences",
    confidence=0.85,
    md={"transmission_path": "via Clitomaque + Antiochus d'Ascalon (conjectural)", "amand_page": "p. 78-80"},
))
NEW_EDGES.append(make_edge(
    src="person_carneades_214_129bce_l2m3n4o5",
    tgt="person_philo_alexandria_a1b2c3d4",
    relation="influences",
    confidence=0.7,
    md={"transmission_path": "via Clitomaque + ὑπόμνημα alexandrin (conjectural)", "amand_page": "p. 83-85"},
))
NEW_EDGES.append(make_edge(
    src="person_carneades_214_129bce_l2m3n4o5",
    tgt="person_favorinus_of_arles_9n4o6q32",
    relation="influences",
    confidence=0.65,
    md={"transmission_path": "via Aulu-Gelle NA XIV.1.23 (libre adaptation rhétorique)", "amand_page": "p. 100"},
))

# Member_of school for Maximus of Tyre
NEW_EDGES.append(make_edge(
    src="person_maximus_of_tyre_125_185ce",
    tgt="school_academics",
    relation="influenced_by",
    confidence=0.55,
    md={"amand_note": "Platonicien éclectique, ne porte pas trace de Carnéade"},
))

# Argument-envelope Philon (cadre quadripartite) — utilise `contains` (envelope → sub)
# car part_of ne supporte pas argument→argument (target_types limités à concept/passage/work/source_collection).
for sub in [
    "argument_philo_de_providentia_moral_responsibility_amand1945",
    "argument_philo_de_providentia_ethnic_customs_amand1945",
    "argument_philo_de_providentia_collective_death_amand1945",
    "argument_philo_de_providentia_conception_moment_amand1945",
]:
    NEW_EDGES.append(make_edge(
        src="argument_philo_de_providentia_argument_envelope_amand1945",
        tgt=sub,
        relation="contains",
        confidence=0.95,
    ))

# Argument-envelope Philon → person Philon
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_argument_envelope_amand1945",
    tgt="person_philo_alexandria_a1b2c3d4",
    relation="claimed_by",
    confidence=1.0,
))

# Transmission edges : carneadean assent chain → arguments B1 pivots (cf. metadata transmits_argument_pivots_b1)
NEW_EDGES.append(make_edge(
    src="argument_carneadean_assent_chain_via_cicero_amand1945",
    tgt="argument_carneadean_virtue_vice_amand1945",
    relation="evidence_for",
    confidence=0.8,
    md={"amand_witness": "Cicéron De fato 17.40 = témoin résiduel"},
))
NEW_EDGES.append(make_edge(
    src="argument_carneadean_assent_chain_via_cicero_amand1945",
    tgt="argument_carneadean_incentives_amand1945",
    relation="evidence_for",
    confidence=0.8,
))

# Argument moral Philon → arguments pivots B1
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_moral_responsibility_amand1945",
    tgt="argument_carneadean_legislation_amand1945",
    relation="evidence_for",
    confidence=0.85,
    md={"amand_witness_rank": "primary_witness_n1"},
))
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_moral_responsibility_amand1945",
    tgt="argument_carneadean_virtue_vice_amand1945",
    relation="evidence_for",
    confidence=0.85,
    md={"amand_witness_rank": "primary_witness_n1"},
))

# Argument ethnographique Philon → arguments antiastrologiques B2 (anticipation textuelle)
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_ethnic_customs_amand1945",
    tgt="argument_carneadean_antiastrological_nomima_barbarika_amand1945",
    relation="evidence_for",
    confidence=0.85,
    md={"amand_witness_rank": "primary_witness_n1_for_antiastrological_arg"},
))
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_collective_death_amand1945",
    tgt="argument_carneadean_antiastrological_collective_death_amand1945",
    relation="evidence_for",
    confidence=0.85,
))
NEW_EDGES.append(make_edge(
    src="argument_philo_de_providentia_conception_moment_amand1945",
    tgt="argument_carneadean_antiastrological_horoscope_impossibility_amand1945",
    relation="evidence_for",
    confidence=0.85,
))

# Favorinus moral argument → arguments pivots B1
NEW_EDGES.append(make_edge(
    src="argument_favorinus_moral_proof_via_gellius_amand1945",
    tgt="argument_carneadean_virtue_vice_amand1945",
    relation="evidence_for",
    confidence=0.55,
    md={"amand_witness_rank": "secondary_witness_indirect"},
))


# --------------------------------------------------------------------------
# APPLICATION
# --------------------------------------------------------------------------

def main() -> int:
    print("== Loading current KG ==")
    with NODES_PATH.open() as f:
        nodes = [json.loads(line) for line in f]
    with EDGES_PATH.open() as f:
        edges = [json.loads(line) for line in f]
    print(f"  Nodes loaded: {len(nodes)}")
    print(f"  Edges loaded: {len(edges)}")

    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}
    edge_by_id = {e.get("id", e.get("edge_id", "")): i for i, e in enumerate(edges)}

    # 1) Repairs
    print("\n== REPAIR PHASE ==")
    repaired_count = 0
    for nid, repair in REPAIRS.items():
        if nid not in node_by_id:
            print(f"  MISSING (skip): {nid}")
            continue
        n = nodes[node_by_id[nid]]
        n["period"] = repair["period"]
        n["school"] = repair["school"]
        n["metadata"] = json.dumps(repair["md"], ensure_ascii=False)
        n["updated_at"] = TIMESTAMP
        if not isinstance(n.get("alternative_names"), str):
            n["alternative_names"] = json.dumps(n.get("alternative_names") or [])
        repaired_count += 1
    print(f"  Repaired: {repaired_count} nodes")

    # 2) Inserts
    print("\n== INSERT PHASE ==")
    inserted_count = 0
    for ins in NEW_INSERTS:
        if ins["id"] in node_by_id:
            print(f"  SKIP exists: {ins['id']}")
            continue
        nodes.append(ins)
        node_by_id[ins["id"]] = len(nodes) - 1
        inserted_count += 1
    print(f"  Inserted: {inserted_count} nodes")

    # 3) Edges
    print("\n== EDGE PHASE ==")
    edge_inserted = 0
    for e in NEW_EDGES:
        if e["id"] in edge_by_id:
            print(f"  SKIP exists: {e['id']}")
            continue
        # Vérifier source et target existent (sinon skip)
        if e["source"] not in node_by_id:
            print(f"  SKIP source missing: {e['source']} -> {e['target']}")
            continue
        if e["target"] not in node_by_id:
            print(f"  SKIP target missing: {e['source']} -> {e['target']}")
            continue
        edges.append(e)
        edge_by_id[e["id"]] = len(edges) - 1
        edge_inserted += 1
    print(f"  Edges inserted: {edge_inserted}")

    # 4) Write back
    print("\n== WRITING BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)} nodes")
    print(f"  edges.jsonl: {len(edges)} edges")

    print("\n== B3 CONSOLIDATION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
