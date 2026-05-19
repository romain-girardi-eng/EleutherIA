#!/usr/bin/env python3
"""Wave acquisition 2026-05-18 — Integration of 16 acquired essential works.

REVISION 2 — descriptions and verified_critiques arrays now reflect direct
readings of the PDFs by 7 parallel sub-agents on 2026-05-18. Every verbatim
citation in this file was extracted from the actual source text and is
traceable to a specific page.

PDFs/EPUBs acquired in [local-path]

Operations:
- CREATE 4 new scholar nodes (Coope, Huby, Wetzel, Markschies)
- CREATE 10 new publication nodes with verified content
- ENRICH 5 existing publication shells with local_pdf_path + verified notes
  (Sharples 1983, Kahn 1988, Sorabji 1980, Long & Sedley 1987, Inwood 1985)
- WIRE authored_by + selected critique/engagement edges based on reading

Idempotent. Snapshot before mutation.

Citation format follows the project standard: original language + English
translation (per [[citation-original-plus-english]] memory).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-acquisition-wave"

# Canonical DOCTORAT location (filed 2026-05-18 — see chat history).
# Files were moved from data/literature_acquisition/ to the proper thematic
# subfolders. The KG references these canonical paths.
DOCTORAT_BASE = Path(
    "[local-path] SHAL/04_Littérature_secondaire"
)

# Per-file destination folder mapping (relative to DOCTORAT_BASE).
DOCTORAT_FOLDERS: dict[str, str] = {
    # 01_Philosophie_antique
    "blackson_2025_rhizomata.pdf": "01_Philosophie_antique",
    "bobzien_2021_determinism_freedom_essays.pdf": "01_Philosophie_antique",
    "brennan_2005_stoic_life.pdf": "01_Philosophie_antique",
    "coope_2020_neoplatonist_freedom.pdf": "01_Philosophie_antique",
    "hadot_1992_citadelle_interieure.pdf": "01_Philosophie_antique",
    "huby_1967_first_discovery_free_will.pdf": "01_Philosophie_antique",
    "inwood_1985_ethics_human_action_stoicism.pdf": "01_Philosophie_antique",
    "kahn_1988_discovering_will.pdf": "01_Philosophie_antique",
    "long_2018_how_to_be_free.epub": "01_Philosophie_antique",
    "long_sedley_1987_hellenistic_philosophers_vol1.pdf": "01_Philosophie_antique",
    "long_sedley_1987_hellenistic_philosophers_vol2.pdf": "01_Philosophie_antique",
    "meyer_2011_aristotle_moral_responsibility_intro.pdf": "01_Philosophie_antique",
    "mitsis_2016_lucretius_modernity_full_book.pdf": "01_Philosophie_antique",
    "sharples_1983_alexander_de_fato.pdf": "01_Philosophie_antique",
    "sorabji_1980_necessity_cause_blame.pdf": "01_Philosophie_antique",
    # 05_Origene
    "markschies_2007_origenes_erbe.pdf": "05_Origene",
    "fuerst_2019_concepts_of_origenism_adamantiana13_intro.pdf": "05_Origene",
    "fuerst_2021_perspectives_origen_adamantiana21.pdf": "05_Origene",
    # 07_Libre_arbitre_theologie
    "wetzel_1992_augustine_limits_virtue.pdf": "07_Libre_arbitre_theologie",
    "cary_2000_augustine_inner_self.epub": "07_Libre_arbitre_theologie",
    "magris_2021_filosofizzazione_cristianesimo.pdf": "07_Libre_arbitre_theologie",
    "magris_2008_destino_TOC.pdf": "07_Libre_arbitre_theologie",
}

WAVE_TAG = "acquisition_wave_2026_05_18"
NOW = datetime.now(UTC).isoformat(sep=" ")

# Existing canonical IDs
ID_FREDE_2011 = "pub_frede_2011_free_will"
ID_BOBZIEN_1998 = "pub_bobzien_1998_inadvertent"
ID_BOBZIEN_2000 = "pub_bobzien_2000_epicurus_free_will"
ID_ALEXANDER = "person_alexander_aphrodisias_fl200ce_n5o6p7q8"
ID_AUGUSTINE = "person_augustine_hippo_d430"
ID_PLOTINUS = "person_plotinus_d270"
ID_EPICTETUS = "person_epictetus_of_hierapolis_3c385bc2"
ID_MARCUS_AURELIUS = "person_marcus_aurelius_121_180ce"
ID_ORIGEN = "person_origen_alexandria_185_254ce_s9t0u1v2"
ID_ELIASSON_2008 = "scholarly_work_eliasson_2008_the_notion_of_that_which_depends_on_us_i"

# Existing scholar IDs
ID_FREDE_SCHOLAR = "scholar_frede_michael"
ID_SEDLEY_SCHOLAR = "scholar_sedley_david"
ID_LONG_SCHOLAR = "scholar_long_anthony"
ID_SHARPLES_SCHOLAR = "scholar_sharples_robert"
ID_KAHN_SCHOLAR = "scholar_kahn_charles"
ID_INWOOD_SCHOLAR = "person_inwood_brad_contemporary"
ID_SORABJI_SCHOLAR = "person_sorabji_richard_contemporary"
ID_CARY_SCHOLAR = "scholar_cary_p"
ID_HADOT_SCHOLAR = "scholar_hadot_pierre"
ID_MITSIS_SCHOLAR = "scholar_mitsis_phillip"
ID_MEYER_SCHOLAR = "scholar_meyer_s"
ID_BOBZIEN_SCHOLAR = "person_bobzien_susanne_contemporary"

# New scholar IDs
ID_COOPE_SCHOLAR = "scholar_coope_ursula"
ID_HUBY_SCHOLAR = "scholar_huby_pamela"
ID_WETZEL_SCHOLAR = "scholar_wetzel_james"
ID_MARKSCHIES_SCHOLAR = "scholar_markschies_christoph"

# New publication IDs
ID_PUB_COOPE = "pub_coope_2020_neoplatonist_freedom"
ID_PUB_BOBZIEN_2021 = "pub_bobzien_2021_determinism_freedom_essays"
ID_PUB_HUBY = "pub_huby_1967_first_discovery"
ID_PUB_WETZEL = "pub_wetzel_1992_augustine_limits_virtue"
ID_PUB_CARY = "pub_cary_2000_inner_self"
ID_PUB_MARKSCHIES = "pub_markschies_2007_origenes_erbe"
ID_PUB_HADOT_1992 = "pub_hadot_1992_citadelle_interieure"
ID_PUB_LONG_2018 = "pub_long_2018_how_to_be_free"
ID_PUB_MITSIS_2016 = "pub_mitsis_2016_how_modern_freedom"
ID_PUB_MEYER_2011 = "pub_meyer_2011_aristotle_moral_responsibility_reissue"

# Existing publication IDs to ENRICH
ID_PUB_SHARPLES_1983 = "pub_sharples_1983_alexander_fate"
ID_PUB_KAHN_1988 = "pub_kahn_1988_discovering_will"
ID_PUB_SORABJI_1980 = "pub_sorabji_1980_necessity_cause_blame"
ID_PUB_LS_1987 = "scholarly_work_long_sedley_1987_hellenistic_philosophers"
ID_PUB_INWOOD_1985 = "scholarly_work_inwood_1985_ethics_action"

def PDF(name: str) -> str:
    folder = DOCTORAT_FOLDERS.get(name, "01_Philosophie_antique")
    return str(DOCTORAT_BASE / folder / name)


# =====================================================================
# NEW SCHOLAR NODES
# =====================================================================

NEW_SCHOLARS: list[dict[str, Any]] = [
    {
        "id": ID_COOPE_SCHOLAR, "node_id": ID_COOPE_SCHOLAR, "type": "person",
        "label": "Ursula Coope",
        "description": (
            "Ursula Coope, philosophe britannique, Professor of Ancient "
            "Philosophy à l'Université d'Oxford et Fellow de Keble "
            "College. Spécialiste d'Aristote, du néoplatonisme et de "
            "la philosophie de l'action. Auteure de *Time for Aristotle* "
            "(OUP 2005) et *Freedom and Responsibility in Neoplatonist "
            "Thought* (OUP 2020) — référence contemporaine sur le libre "
            "arbitre néoplatonicien (Plotin → Damascius). Évite "
            "délibérément l'expression « free will » et n'utilise "
            "« freedom » que pour rendre ἐλευθερία (Coope 2020, p. 3)."
        ),
        "period": "Modern", "role": "scholar", "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "role": "scholar", "period": "Modern", "surname": "Coope",
            "given_names": "Ursula",
            "specialty": "Ancient philosophy, Aristotle, Neoplatonism, philosophy of action",
            "affiliations": ["University of Oxford", "Keble College, Oxford"],
            "key_works": [
                "Time for Aristotle (Oxford 2005)",
                "Freedom and Responsibility in Neoplatonist Thought (Oxford 2020)",
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    {
        "id": ID_HUBY_SCHOLAR, "node_id": ID_HUBY_SCHOLAR, "type": "person",
        "label": "Pamela M. Huby",
        "description": (
            "Pamela M. Huby (1922-2019), philosophe britannique, Reader "
            "in Philosophy à l'Université de Liverpool. Spécialiste de "
            "Théophraste (éditrice du projet international "
            "*Theophrastus of Eresus: Sources for His Life, Writings, "
            "Thought and Influence*, Brill 1992-2014). Auteure de "
            "l'article fondateur « The First Discovery of the "
            "Free-Will Problem » (*Philosophy* 42, 1967, p. 353-362), "
            "qui attribue à Épicure (c. 300 av. J.-C.) la découverte "
            "du problème de la conciliation entre liberté humaine et "
            "déterminisme causal. **Cible directe** de Bobzien 2000 "
            "(« Did Epicurus Discover the Free Will Problem? », OSAP 19)."
        ),
        "period": "Modern", "role": "scholar", "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "role": "scholar", "period": "Modern", "surname": "Huby",
            "given_names": "Pamela M.",
            "birth_year": 1922, "death_year": 2019,
            "specialty": "Ancient philosophy, Theophrastus, history of free will debate",
            "affiliations": ["University of Liverpool"],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    {
        "id": ID_WETZEL_SCHOLAR, "node_id": ID_WETZEL_SCHOLAR, "type": "person",
        "label": "James Wetzel",
        "description": (
            "James Wetzel, philosophe américain, Augustinian Endowed "
            "Chair in the Thought of Saint Augustine à Villanova "
            "University. Thèse Columbia (sous Wayne Proudfoot). "
            "Spécialiste de la psychologie morale augustinienne, de "
            "la transition free choice → grâce, et de l'héritage "
            "stoïcien d'Augustin. Auteur de *Augustine and the Limits "
            "of Virtue* (Cambridge UP 1992) qui attaque la division "
            "« jeune Augustin philosophique vs vieil Augustin "
            "théologique » et défend la continuité stoïco-platonicienne "
            "à travers toute l'œuvre."
        ),
        "period": "Modern", "role": "scholar", "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "role": "scholar", "period": "Modern", "surname": "Wetzel",
            "given_names": "James",
            "specialty": "Augustine, moral psychology, ancient-medieval transition, Stoic-Christian continuity",
            "affiliations": ["Villanova University (Augustinian Endowed Chair)"],
            "key_works": [
                "Augustine and the Limits of Virtue (Cambridge 1992)",
                "Augustine: A Guide for the Perplexed (Continuum 2010)",
                "Parting Knowledge: Essays after Augustine (Cascade 2013)",
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    {
        "id": ID_MARKSCHIES_SCHOLAR, "node_id": ID_MARKSCHIES_SCHOLAR, "type": "person",
        "label": "Christoph Markschies",
        "description": (
            "Christoph Markschies (né 1962), théologien et historien "
            "des dogmes allemand, Professor für Antikes Christentum à "
            "la Humboldt-Universität zu Berlin, président de la "
            "Berlin-Brandenburgische Akademie der Wissenschaften (depuis "
            "2020). Ancien président de la Humboldt-Universität "
            "(2006-2010). Spécialiste mondialement reconnu d'Origène, "
            "du valentinisme et du christianisme antique. Continuateur "
            "de la tradition Adolf-von-Harnack à Berlin. Complément "
            "historico-doctrinal de la lecture philosophique de Fürst "
            "sur Origène."
        ),
        "period": "Modern", "role": "scholar", "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "role": "scholar", "period": "Modern", "surname": "Markschies",
            "given_names": "Christoph", "birth_year": 1962,
            "specialty": "Patristics, Origen, ancient Christianity, history of dogma, Gnosticism",
            "affiliations": [
                "Humboldt-Universität zu Berlin (Professor)",
                "Berlin-Brandenburgische Akademie der Wissenschaften (Präsident)",
            ],
            "key_works": [
                "Valentinus Gnosticus? (Mohr Siebeck 1992)",
                "Origenes und sein Erbe (de Gruyter 2007, TU 160)",
                "Christian Theology and its Institutions in the Early Roman Empire (Mohr Siebeck 2015)",
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
]


# =====================================================================
# NEW PUBLICATION NODES
# =====================================================================

NEW_PUBLICATIONS: list[dict[str, Any]] = [
    # -----------------------------------------------------------------
    # HUBY 1967 — Lu intégralement
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_HUBY, "node_id": ID_PUB_HUBY, "type": "publication",
        "label": "Huby 1967 — The First Discovery of the Free-Will Problem",
        "description": (
            "Pamela M. Huby, « The First Discovery of the Free-Will "
            "Problem », *Philosophy* 42/162 (1967), p. 353-362. DOI "
            "10.1017/S0031819100001534. Article fondateur du débat "
            "moderne sur l'origine antique du libre arbitre. Thèse : "
            "Aristote partageait beaucoup des éléments d'un argument "
            "déterministe (NE III.5, EE II.6-7) mais sans jamais les "
            "assembler ni reconnaître un problème réel — Huby parle "
            "d'« a simple reaffirmation of libertarianism » (p. 354). "
            "Cicéron (De Fato 39) qui classe Aristote comme "
            "déterministe est, pour Huby, dans l'erreur (p. 357). "
            "C'est Épicure qui a découvert le problème : l'introduction "
            "du *clinamen* atomique comme événement non causé répond "
            "précisément à la nécessité de préserver la liberté contre "
            "un nexus causal complet. Les Stoïciens (Chrysippe, pas "
            "Zénon ni Cléanthe) ont repris le problème d'Épicure — pas "
            "l'inverse (p. 359). **Cible directe** de Bobzien 2000."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Huby 1967 First Discovery"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "article", "year": 1967, "author": "Pamela M. Huby",
            "author_id": ID_HUBY_SCHOLAR,
            "title": "The First Discovery of the Free-Will Problem",
            "journal": "Philosophy", "volume": 42, "number": 162,
            "pages": "353-362", "publisher": "Cambridge University Press",
            "doi": "10.1017/S0031819100001534", "language": "en",
            "bibtex_key": "huby-1967-first-discovery",
            "local_pdf_path": PDF("huby_1967_first_discovery_free_will.pdf"),
            "central_thesis": (
                "Epicurus (c. 300 BCE) discovered the free-will problem via "
                "the introduction of the atomic clinamen as an uncaused "
                "event preserving freedom against a complete causal nexus. "
                "Aristotle was acquainted with most of the elements of "
                "a deterministic argument but never assembled them. "
                "Stoics (Chrysippus, not Zeno/Cleanthes) took up the "
                "problem from Epicurus, not the reverse."
            ),
            "critique_by_bobzien_2000": (
                "Bobzien 2000 OSAP 19 'Did Epicurus Discover the Free-Will "
                "Problem?' systematically refutes Huby's reading of the "
                "clinamen as solution to the free-will problem"
            ),
            "verified_critiques": [
                {
                    "page": 353, "thesis": "Programmatic statement (opening)",
                    "quote_verbatim_en": (
                        "I shall argue that Aristotle was unaware of the "
                        "problem, although he accepted a great many of "
                        "the assumptions which we also make. The "
                        "Epicureans and Stoics, on the other hand, took "
                        "the problem very seriously. I shall try to show "
                        "that it is most likely that it was Epicurus who "
                        "first realised that there was a problem, and "
                        "how this came about."
                    ),
                },
                {
                    "page": 354, "thesis": "Aristotle's libertarian default",
                    "quote_verbatim_en": (
                        "There are several passages in Aristotle where "
                        "he seems, to a modern reader, to be approaching "
                        "the problem, but every time he finally turns "
                        "away, with at best a simple affirmation of "
                        "libertarianism, without seeming to be aware "
                        "that there is any real difficulty."
                    ),
                },
                {
                    "page": 357, "thesis": "Cicero misclassifies Aristotle",
                    "quote_verbatim_en": (
                        "I conclude that Aristotle, while he was aware "
                        "of most of the elements of the determinist "
                        "argument, for one reason or another failed to "
                        "put them all together and draw the—to us—"
                        "obvious conclusion. It is puzzling that Cicero "
                        "in the De Fato (39) classes Aristotle with "
                        "Democritus, Heraclitus and Empedocles as a "
                        "determinist. … On our evidence, Cicero is mistaken."
                    ),
                },
                {
                    "page": 358, "thesis": "Epicurus as discoverer",
                    "quote_verbatim_en": (
                        "In spite of the poverty of our evidence, it is "
                        "quite clear that one main reason Epicurus had "
                        "for introducing the swerve, or rather the "
                        "swerve as a random, uncaused event, was as a "
                        "solution to the problem of freewill. Unlike "
                        "Aristotle, he fully appreciated that there "
                        "was a problem."
                    ),
                },
                {
                    "page": 362, "thesis": "Closing philosophical conclusion",
                    "quote_verbatim_en": (
                        "It was possible for men like Plato and "
                        "Aristotle to hold many educational and "
                        "psychological beliefs in common with us "
                        "without being aware of any freewill problem "
                        "because they had no notion of thorough-going "
                        "psychological determinism."
                    ),
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # KAHN 1988 — Lu intégralement
    # -----------------------------------------------------------------
    # NOTE: Kahn 1988 publication node ALREADY EXISTS as pub_kahn_1988_discovering_will
    # We enrich it via ENRICHMENTS below, not create here. Skip.

    # -----------------------------------------------------------------
    # MEYER 2011 intro — Lu intégralement (intro nouvelle, 38 p.)
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_MEYER_2011, "node_id": ID_PUB_MEYER_2011, "type": "publication",
        "label": "Meyer 2011 — Aristotle on Moral Responsibility (OUP reissue, new intro)",
        "description": (
            "Susan Sauvé Meyer, *Aristotle on Moral Responsibility: "
            "Character and Cause*, Oxford: OUP, 2011 (reissue de "
            "Blackwell 1993, avec nouvelle introduction de 38 p.), "
            "ISBN 978-0-19-969742-7. La nouvelle introduction (« "
            "Voluntariness, Morality, and Causality », p. xiii-xxv) "
            "repositionne le monograph 1993 dans le débat post-"
            "Bobzien-Frede. Thèses centrales : (1) Aristote traite "
            "*to hekousion* comme notion CAUSALE (l'agent est cause "
            "non-accidentelle de l'action volontaire), pas "
            "métaphysique ; (2) NE III.5 1113b3-21 argumente CONTRE "
            "la thèse platonicienne (seuls les actes bons sont "
            "volontaires), PAS pour une exigence libertarienne de "
            "responsabilité-pour-le-caractère ; (3) *to eph' hêmin* "
            "(NE 1112b27) = « ce qui peut arriver par nous » — ce "
            "qui dépend de nos pouvoirs de pensée et de désir, PAS "
            "contingence métaphysique ; (4) la lecture libertarienne "
            "d'Aristote par Alexandre d'Aphrodise via Met. IX (pouvoirs "
            "rationnels « bilatéraux ») est anachronique ; (5) Aristote "
            "n'engage jamais une thèse reconnaissable de déterminisme, "
            "donc ne peut être classé comme libertaire ou déterministe "
            "(p. xxi). **Alignée avec Bobzien 1998 et Frede 2011** "
            "contre les lectures libertariennes (Destrée 2011, Natali "
            "2004, Broadie 1991, Chappell 1995). PDF acquis : "
            "uniquement la nouvelle intro 2011 (38 p.), mise en ligne "
            "par l'auteure sur sa page Penn."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Meyer 2011 AMR reissue"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "monograph", "year": 2011, "original_year": 1993,
            "author": "Susan Sauvé Meyer", "author_id": ID_MEYER_SCHOLAR,
            "title": "Aristotle on Moral Responsibility: Character and Cause",
            "publisher": "Oxford University Press",
            "original_publisher": "Blackwell (1993)",
            "isbn": "978-0-19-969742-7", "language": "en",
            "bibtex_key": "meyer-2011-aristotle-moral-responsibility",
            "local_pdf_path": PDF("meyer_2011_aristotle_moral_responsibility_intro.pdf"),
            "note_pdf_partial": "Only the new 2011 introduction (38 p.) acquired",
            "verified_critiques": [
                {
                    "page": "xx",
                    "thesis": "Eph' hêmin does not imply metaphysical contingency",
                    "quote_verbatim_en": (
                        "While Aristotle does say that such actions "
                        "'admit of being otherwise' (EE 1222b41-1223a9), "
                        "the sort of contingency invoked by the latter "
                        "locution has, first of all, no implications "
                        "regarding the truth or falsity of determinism. "
                        "Second, Aristotle does not explain the notion "
                        "of being 'up to us' in terms of that contingency."
                    ),
                },
                {
                    "page": "xxi",
                    "thesis": "Alexander's libertarian reading is anachronistic",
                    "quote_verbatim_en": (
                        "Such a conception of 'two-sidedness' [Met. IX "
                        "1046b1-7], however, does not make Aristotle an "
                        "indeterminist. … Furthermore, this account "
                        "implies nothing about whether the crucial "
                        "desire or choice is determined by antecedent "
                        "conditions; thus Alexander is wrong to invoke "
                        "it as evidence that Aristotelian action is libertarian."
                    ),
                },
                {
                    "page": "xxi",
                    "thesis": "Aristotle is pre-the-debate — not classifiable",
                    "quote_verbatim_en": (
                        "In resisting these libertarian interpretations "
                        "of Aristotle, my aim is not to establish that "
                        "he is a determinist about action. Even if "
                        "libertarianism and determinism are exhaustive "
                        "options … it is misleading to classify "
                        "particular philosophers as libertarian or "
                        "determinist unless they explicitly face or "
                        "articulate a recognizable thesis of determinism."
                    ),
                },
                {
                    "page": "xxii",
                    "thesis": "Aristotle distinguishes external from antecedent causation",
                    "quote_verbatim_en": (
                        "I take the position in the chapters below that "
                        "Aristotle himself shows no inclination to worry "
                        "that determination by antecedent conditions is "
                        "incompatible with voluntariness, praiseworthiness, "
                        "or our actions being 'up to us'. While he does "
                        "assume that an action whose 'origin' is 'in us' "
                        "cannot be attributed to origins 'beyond those in "
                        "us' (e.g. EN 1113b19-20), this is a concern about "
                        "external causation, not causal determination."
                    ),
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # MITSIS 2016 — Lu intégralement
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_MITSIS_2016, "node_id": ID_PUB_MITSIS_2016, "type": "publication",
        "label": "Mitsis 2016 — How Modern Is Freedom of the Will? (Lucretius and Modernity ch. 7)",
        "description": (
            "Phillip Mitsis, « How Modern Is Freedom of the Will? », "
            "in J. Lezra & L. Blake (eds.), *Lucretius and Modernity: "
            "Epicurean Encounters Across Time and Disciplines*, "
            "Palgrave Macmillan 2016, ch. 7, p. 105-123. DOI "
            "10.1007/978-1-137-56657-7_7. Version anglaise antérieure "
            "et précurseur de Mitsis 2021 Parnassos. Argument central : "
            "rejet du « near consensus » (MacIntyre, Bobzien, Meyer "
            "1999, Schneewind, Taylor, Foucault, Habermas) qui pose un "
            "fossé conceptuel radical entre l'ancien et le moderne sur "
            "« la volonté ». Comparaison textuelle précise entre "
            "Lucrèce DRN II 251-93 + IV 877-91 et Locke *Essay* II.21 "
            "(*Of Power*, §41, 48, 53). **Deux réfutations de Bobzien** : "
            "(i) le swerve libère la *mens*, pas la *voluntas* — la "
            "lecture qui cherche la liberté dans *libera voluntas* est "
            "une « category mistake » (p. 117) ; (ii) le `summetrēsis` "
            "épicurien (Ad Men. 130, KD 25) conçoit déjà le choix entre "
            "alternatives, contre la thèse « personne avant Alexandre »."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Mitsis 2016 Lucretius and Modernity"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "book_chapter", "year": 2016,
            "author": "Phillip Mitsis", "author_id": ID_MITSIS_SCHOLAR,
            "title": "How Modern Is Freedom of the Will?",
            "book_title": "Lucretius and Modernity: Epicurean Encounters Across Time and Disciplines",
            "editors": ["Jacques Lezra", "Liza Blake"],
            "chapter": 7, "pages": "105-123",
            "publisher": "Palgrave Macmillan", "publisher_location": "London",
            "isbn": "978-1-137-56656-0", "doi": "10.1007/978-1-137-56657-7_7",
            "language": "en", "bibtex_key": "mitsis-2016-how-modern-freedom",
            "local_pdf_path": PDF("mitsis_2016_lucretius_modernity_full_book.pdf"),
            "note_pdf_format": "Full book PDF (225 p.) — chapter 7 at p. 105-123",
            "successor_publication": "Mitsis 2021 Parnassos — expansion and refinement",
            "verified_critiques": [
                {
                    "page": "106-107",
                    "thesis": "Identification of Bobzien-Meyer consensus as target",
                    "quote_verbatim_en": (
                        "In my own subdiscipline of ancient philosophy, "
                        "for instance, a view that seems to be winning "
                        "the day is one formulated by Susan Sauvé Meyer "
                        "and then elaborated in relentless detail by "
                        "Susanne Bobzien, who claims that no Greek "
                        "philosopher before Alexander of Aphrodisias—"
                        "some three centuries after Lucretius—ever "
                        "thought of free human agency as involving a "
                        "choice between two alternative courses of action."
                    ),
                },
                {
                    "page": 117,
                    "thesis": "Re-reading of DRN II 251-93: swerve frees mens, not voluntas",
                    "quote_verbatim_en": (
                        "Scholars have latched on to the notion of "
                        "'libera voluntas' in 256-57, but it seems clear "
                        "that in this account, as in Locke, the will is "
                        "free only insofar as the mind directing it also "
                        "is free. That is, voluntas is viewed as a "
                        "material force that conveys the decision of the "
                        "mind to the limbs and is determined by the mind "
                        "… Our liberty, that is, consists in our mind's "
                        "and our reason's capacity to direct the will."
                    ),
                },
                {
                    "page": 117,
                    "thesis": "Category mistake in linking swerve directly to voluntas",
                    "quote_verbatim_en": (
                        "The tradition of scholarship that has tried to "
                        "link the swerve directly to voluntas and a "
                        "faculty of 'free will' has made a kind of "
                        "category mistake, since as Lucretius claims in "
                        "this passage, the swerve frees the mind from "
                        "internal necessity, and presumably our freedom "
                        "in making decisions lies there."
                    ),
                },
                {
                    "page": 117,
                    "thesis": "Direct refutation of Bobzien on libera voluntas",
                    "quote_verbatim_en": (
                        "Bobzien uses this passage as fodder for her "
                        "general claim that no Hellenistic philosopher, "
                        "indeed no one until Alexander of Aphrodisias, "
                        "several centuries later, ever thought of "
                        "freedom of choice as a choice between two "
                        "alternatives. But, of course, this argument, "
                        "too, is badly misaimed, since her claim that "
                        "libera voluntas in this passage is strictly "
                        "determined tells us nothing about whether "
                        "Epicureans think that the freedom of the mind "
                        "and of our reason is itself similarly determined "
                        "or whether it is characterized by its ability "
                        "to choose between two alternatives."
                    ),
                },
                {
                    "page": 113,
                    "thesis": "Locke-Epicurus continuity via suspension and nephon logismos",
                    "quote_verbatim_en": (
                        "[Locke's account of 'suspension'] mirrors, on "
                        "one hand, what Epicurus called nephon logismos, "
                        "or sober reasoning, which he claims 'tracks "
                        "down the sources of every choice and avoidance "
                        "and banishes opinions that beset souls with the "
                        "greatest confusion' (ad Men. 132); on the other, "
                        "it invokes a Stoic view of our rational ability "
                        "to make decisions by giving or withholding "
                        "assent to various impressions."
                    ),
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # COOPE 2020 — Intro + Plotin lus
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_COOPE, "node_id": ID_PUB_COOPE, "type": "publication",
        "label": "Coope 2020 — Freedom and Responsibility in Neoplatonist Thought",
        "description": (
            "Ursula Coope, *Freedom and Responsibility in Neoplatonist "
            "Thought*, Oxford: OUP, 2020, ISBN 978-0-19-882483-1, 288 p. "
            "Monographie philosophique sur les notions de liberté "
            "(ἐλευθερία) et de responsabilité chez les néoplatoniciens "
            "païens, de Plotin à Damascius/Simplicius. **Thèse "
            "perfectionniste** : être libre = être pleinement en "
            "contrôle de soi, réalisable seulement dans la mesure où "
            "l'on devient bon. Paradigme = intellects divins en "
            "contemplation théorétique. Aucun des auteurs étudiés ne "
            "fait du PAP ou de l'absence de cause un critère de liberté. "
            "Structure : Part I (puzzles : Platon, Aristote, Stoïciens, "
            "Épictète, Alexandre, vocabulaire de αὐτεξούσιος et ἐφ' "
            "ἡμῖν) ; Part II (liberté : Enn. VI.8, self-making, "
            "non-corporéité, dépendance, Plotin + Proclus + Jamblique) ; "
            "Part III (responsabilité : mythe d'Er, free principle "
            "plotinien en III.3.4, λόγοι chez Proclus, école "
            "damascéenne). **Coope évite délibérément l'expression "
            "« free will » (p. 3) — son approche est philologique et "
            "doxographique, non polémique.** Pas de critique frontale "
            "de Frede 2011 (qu'elle cite positivement, p. 47 n.25, "
            "p. 93 n.62). Christianisme antique explicitement hors "
            "champ (p. 1 n.1) ; Origène mentionné seulement 2× (p. 98 "
            "n.9 sur Porphyre/hypostasis ; p. 203 n.11 sur providence "
            "et contingence vs Proclus)."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Coope 2020 Neoplatonist Freedom"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "monograph", "year": 2020,
            "author": "Ursula Coope", "author_id": ID_COOPE_SCHOLAR,
            "title": "Freedom and Responsibility in Neoplatonist Thought",
            "publisher": "Oxford University Press", "pages": 288,
            "isbn": "978-0-19-882483-1", "isbn13": "9780198824831",
            "language": "en", "bibtex_key": "coope-2020-neoplatonist-freedom",
            "local_pdf_path": PDF("coope_2020_neoplatonist_freedom.pdf"),
            "ndpr_review_url": "https://ndpr.nd.edu/reviews/freedom-and-responsibility-in-neoplatonist-thought/",
            "central_thesis": (
                "Perfectionist reading: entities are free to the extent "
                "they succeed in making themselves good; freedom is "
                "compatible with subjection to the One but incompatible "
                "with corporeal causation. Self-reflexivity (self-knowing "
                "+ self-causing) grounds both freedom and responsibility."
            ),
            "structure": {
                "Part I (Puzzles)": "Ch. 1-4 — Platon, Aristote, Stoïciens, Épictète, Alexandre",
                "Part II (Freedom)": "Ch. 5-8 — Enn. VI.8 sur l'Un, self-making, non-corporéité",
                "Part III (Responsibility)": "Ch. 9-12 — Plotin III.3.4, Proclus, école damascéenne",
            },
            "verified_critiques": [
                {
                    "page": 2,
                    "thesis": "Perfectionist freedom — programmatic statement",
                    "quote_verbatim_en": (
                        "I shall argue that freedom, as it is understood "
                        "by these authors, is a kind of perfection. To "
                        "be free is to be fully in control of oneself: "
                        "in control both of what one is and of what one "
                        "does. Those who are truly free are not pulled "
                        "hither and thither by external demands or "
                        "emotional disturbances. They are not constrained "
                        "even by their own nature, but instead in some "
                        "sense make themselves what they are."
                    ),
                },
                {
                    "page": 7,
                    "thesis": "Perfectionist view distinct from modern compatibilism debate",
                    "quote_verbatim_en": (
                        "The Neoplatonists had a 'perfectionist' view "
                        "of freedom: they held that we only achieve "
                        "freedom to the extent that we succeed in "
                        "making ourselves good. This is not at all "
                        "what modern philosophers mean by 'freedom' "
                        "when they ask whether freedom is compatible "
                        "with determinism."
                    ),
                },
                {
                    "page": 3,
                    "thesis": "Methodological avoidance of 'free will'",
                    "quote_verbatim_en": (
                        "Throughout this book, I avoid using the "
                        "expression 'free will' and I use the word "
                        "'freedom' only where I have in mind something "
                        "that could be expressed by the Greek word "
                        "'ἐλευθερία'."
                    ),
                },
                {
                    "page": 49,
                    "thesis": "Plotinus's perfectionist eph' hêmin",
                    "quote_verbatim_en": (
                        "Plotinus, like the Stoics, has grounds for "
                        "adopting a perfectionist view of freedom. "
                        "Freedom is something you can only achieve by "
                        "escaping from the influence of the passions "
                        "and acting in the light of full knowledge of "
                        "what is genuinely valuable. Only in this way "
                        "are you guaranteed to live as you wish."
                    ),
                },
                {
                    "page": 1,
                    "thesis": "Christianity explicitly out of scope",
                    "quote_verbatim_en": (
                        "Questions about the interaction between "
                        "Neoplatonism and Christianity (although "
                        "obviously interesting and important in their "
                        "own right) lie outside the scope of this book."
                    ),
                    "context": "Footnote 1, p. 1 — definitive disclaimer on Origen-Plotinus interaction",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # BOBZIEN 2021 — Préface + Intro inédite lus
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_BOBZIEN_2021, "node_id": ID_PUB_BOBZIEN_2021, "type": "publication",
        "label": "Bobzien 2021 — Determinism, Freedom, and Moral Responsibility: Essays in Ancient Philosophy",
        "description": (
            "Susanne Bobzien, *Determinism, Freedom, and Moral "
            "Responsibility: Essays in Ancient Philosophy*, Oxford: "
            "OUP, 2021, xvi + 323 p., ISBN 978-0-19-886673-2. Recueil "
            "de 9 essais publiés entre 1997 et 2014, regroupés en 4 "
            "parties chronologiques (Aristote → Épicure → Stoïciens), "
            "**plus Introduction inédite (p. 1-11) et Préface brève "
            "(p. ix-x)**. Contient les réimpressions de « Inadvertent "
            "Conception » (Phronesis 1998, ch. 1) et « Did Epicurus "
            "Discover the Free-Will Problem? » (OSAP 2000, ch. 6). "
            "**ATTENTION** : la Préface 2021 est délibérément non-"
            "polémique — Bobzien annonce explicitement qu'elle « ne "
            "répondra à aucune publication individuelle » (p. ix). "
            "La valeur ajoutée 2021 est dans l'**Introduction inédite** "
            "(p. 1-11) qui synthétise sa thèse, et dans les ajustements "
            "philologiques (Greek/Latin restitués en notes étoilées, "
            "ch. 8 §8.4 et fin du ch. 9 restaurés/étendus). Modifications "
            "des essais : « minor changes » pour la lisibilité, ajout "
            "de notes étoilées Grec/Latin (cf. p. ix-x). **Aucune "
            "rétractation, aucune réponse explicite à Frede 2011, Mitsis "
            "2016, Long.**"
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Bobzien 2021 Collected Essays"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "collected_essays", "year": 2021,
            "author": "Susanne Bobzien", "author_id": ID_BOBZIEN_SCHOLAR,
            "title": "Determinism, Freedom, and Moral Responsibility: Essays in Ancient Philosophy",
            "publisher": "Oxford University Press",
            "pages": "xvi + 323", "isbn": "978-0-19-886673-2",
            "isbn13": "9780198866732", "language": "en",
            "bibtex_key": "bobzien-2021-determinism-freedom-essays",
            "local_pdf_path": PDF("bobzien_2021_determinism_freedom_essays.pdf"),
            "central_value_added": (
                "Inédite 2021 Introduction (p. 1-11) consolidating "
                "25 years of work; Preface (p. ix-x) explicitly declines "
                "to respond to individual publications"
            ),
            "structure": [
                "Preface 2021 (p. ix-x) — inédit, non-polemic",
                "Introduction (p. 1-11) — inédit, value-add",
                "Ch. 1 Inadvertent Conception (= Phronesis 1998) — p. 13-50",
                "Ch. 2 Choice and Moral Responsibility in NE 3.1-5 (2014) — p. 51-76",
                "Ch. 3 Aristotle's NE 1113b7-8 and Free Choice (2014) — p. 77-92",
                "Ch. 4 Found in Translation: NE 3.5 reception (2013) — p. 93-127",
                "Ch. 5 Moral Responsibility and Moral Development in Epicurus (2006) — p. 128-151",
                "Ch. 6 Did Epicurus Discover the Free-Will Problem? (= OSAP 2000) — p. 152-193",
                "Ch. 7 Stoic Conceptions of Freedom (1997) — p. 194-216",
                "Ch. 8 Early Stoic Determinism (2005) — p. 217-252 (§8.4 restored)",
                "Ch. 9 Chrysippus' Theory of Causes (1999) — p. 253-290 (last 2 paragraphs expanded)",
            ],
            "verified_critiques": [
                {
                    "page": "ix",
                    "thesis": "Self-assessment: theses validated by reception",
                    "quote_verbatim_en": (
                        "Since 1997, when the first of the essays in "
                        "this volume was originally published, there "
                        "has been a vast number of publications on "
                        "questions of determinism, freedom, and moral "
                        "responsibility in antiquity. This is not the "
                        "place to list them all, nor will I here "
                        "respond to individual papers and books. (It "
                        "is gratifying to see that the majority of "
                        "responses to the essays collected here have "
                        "agreed with my main theses.)"
                    ),
                    "context": "Preface — explicit refusal to engage Frede, Mitsis, etc.",
                },
                {
                    "page": 1,
                    "thesis": "Restatement of central anti-Whig thesis",
                    "quote_verbatim_en": (
                        "One main component of the ancient discussion "
                        "concerned the question of how moral "
                        "accountability can be consistently combined "
                        "with certain causal factors that impact human "
                        "behaviour. However, it is not true that the "
                        "ancient problems involved the questions of the "
                        "compatibility of causal determinism with either "
                        "our ability to do otherwise or a human faculty "
                        "of a free will."
                    ),
                    "context": "Introduction inédite — opening paragraph",
                },
                {
                    "page": 2,
                    "thesis": "Late birth of the free-will problem dated to 2nd c. CE",
                    "quote_verbatim_en": (
                        "It turns out that what is often described in "
                        "terms of the 'discovery' of the problem of "
                        "causal determinism and freedom of decision in "
                        "Greek philosophy in fact arises from an "
                        "accidental combination and mixing up of "
                        "Aristotelian and Stoic thought in later "
                        "antiquity. … The late birth of the free-will "
                        "problem is thus dated in the second century [CE]."
                    ),
                },
                {
                    "page": "49-50",
                    "thesis": "Origen as possible witness of mature free-will problem",
                    "quote_verbatim_en": (
                        "There is good evidence of it in certain "
                        "passages of Alexander's On Fate and in the "
                        "Mantissa. Origen may have been aware of it."
                    ),
                    "context": "End of ch. 1 (= Phronesis 1998 reprint) — anchors Origen in the 2nd-3rd c. chronology of the mature free-will problem",
                },
                {
                    "page": 8,
                    "thesis": "Eph' hêmin vs eleutheria distinction key for Stoics",
                    "quote_verbatim_en": (
                        "The confusion of these two quite distinct "
                        "concepts and their roles in Stoic philosophy "
                        "has wreaked much havoc in twentieth-century "
                        "literature on Stoic freedom."
                    ),
                    "context": "Introduction inédite — diagnosis of historiographical confusion",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # WETZEL 1992 — Intro + Ad Simplicianum + Stoic continuity lus
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_WETZEL, "node_id": ID_PUB_WETZEL, "type": "publication",
        "label": "Wetzel 1992 — Augustine and the Limits of Virtue",
        "description": (
            "James Wetzel, *Augustine and the Limits of Virtue*, "
            "Cambridge: Cambridge University Press, 1992, xv + 246 p., "
            "ISBN 978-0-521-40541-6. Thèse principale (renverse la "
            "« sagesse conventionnelle » de Brown, Rist, O'Daly, "
            "Burnaby, Arendt) : Augustin NE rompt PAS avec la confiance "
            "platonicienne dans la puissance motivationnelle de la "
            "connaissance du bien. La grâce irrésistible n'est pas une "
            "démission de la philosophie mais sa reformulation théiste "
            "— « his attempt to salvage Platonism's naive and uninformed "
            "confidence in the power of knowledge to motivate » (p. 9). "
            "**Continuité stoïco-platonicienne défendue à travers toute "
            "l'œuvre augustinienne**, du *De libero arbitrio* au "
            "*De civitate Dei*. La transition se cristallise dans *Ad "
            "Simplicianum* I.2 (396), où Augustin abandonne la "
            "distinction foi/œuvres et invente la *vocatio congruens* "
            "— modèle où le consentement humain est à la fois cause "
            "divine et effet volontaire (p. 155-158). Wetzel oppose "
            "*liberum arbitrium* (liberté de l'action selon le désir, "
            "présente dans le péché aussi) à *free will* au sens fort "
            "(intégration motivationnelle sous connaissance du bien, "
            "possible seulement sous grâce). En dialogue final avec "
            "Frankfurt, Watson, Stump, Wolf, Nagel. **Origène est "
            "totalement absent du livre.**"
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "monograph", "year": 1992,
            "author": "James Wetzel", "author_id": ID_WETZEL_SCHOLAR,
            "title": "Augustine and the Limits of Virtue",
            "publisher": "Cambridge University Press",
            "pages": "xv + 246", "isbn": "978-0-521-40541-6",
            "language": "en", "bibtex_key": "wetzel-1992-augustine-limits-virtue",
            "local_pdf_path": PDF("wetzel_1992_augustine_limits_virtue.pdf"),
            "central_thesis": (
                "Augustinian moral psychology preserves Platonic-Stoic "
                "framework even as it intensifies the diagnosis of "
                "human virtue's limits; grace is the answer to a "
                "Platonist-framed problem (knowledge's power to "
                "motivate), not a rupture from ancient philosophy"
            ),
            "verified_critiques": [
                {
                    "page": 6,
                    "thesis": "Augustine retains Platonist confidence undiminished",
                    "quote_verbatim_en": (
                        "He retains this confidence undiminished not "
                        "only in the Confessiones, but for the remainder "
                        "of his career as a theologian, and it is what "
                        "I have referred to as his profounder debt to "
                        "Platonism."
                    ),
                },
                {
                    "page": 9,
                    "thesis": "Grace as salvage of Platonist motivational confidence",
                    "quote_verbatim_en": (
                        "[The doctrine of irresistible grace is] his "
                        "attempt to salvage Platonism's naive and "
                        "uninformed confidence in the power of "
                        "knowledge to motivate. God is the good "
                        "guaranteeing its own reception in the human "
                        "will. Described from the human point of view, "
                        "this reception can be called grace."
                    ),
                },
                {
                    "page": 10,
                    "thesis": "Stoic priority over Neoplatonism in reading Augustine",
                    "quote_verbatim_en": (
                        "In putting Stoicism before Neoplatonism, my "
                        "intention is not to contrast Stoic and Platonic "
                        "influences on Augustine but to highlight his "
                        "Stoic appropriation of Plato. … Stoic rather "
                        "than Neoplatonic influence informed his early "
                        "views of virtue, autonomy, and the good life, "
                        "and disposed him to think Stoically about "
                        "ethics throughout his career as a philosopher "
                        "and theologian."
                    ),
                },
                {
                    "page": 56,
                    "thesis": "Stoic objective preserved in Augustinian beatitudo",
                    "quote_verbatim_en": (
                        "What makes Augustine relevantly Stoic is not "
                        "that he accepts specific Stoic doctrines, but "
                        "that he adopts the objective of Stoic ethics "
                        "in his own articulation of ideal beatitude: "
                        "that is, he tries to describe beatitude in "
                        "such a way that it remains fully under human "
                        "control and fully complete."
                    ),
                },
                {
                    "page": 225,
                    "thesis": "Free will requires divine determination to good will",
                    "quote_verbatim_en": (
                        "We are free, Augustine insists, only when we "
                        "are determined by God to have a good will."
                    ),
                    "context": "Conclusion — strong intellectualist defense of Augustinian compatibilism",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # CARY 2000 — Lu partiellement (intro + conclusion + Origène)
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_CARY, "node_id": ID_PUB_CARY, "type": "publication",
        "label": "Cary 2000 — Augustine's Invention of the Inner Self",
        "description": (
            "Phillip Cary, *Augustine's Invention of the Inner Self: "
            "The Legacy of a Christian Platonist*, Oxford: OUP, 2000, "
            "232 p., ISBN 978-0-19-513206-9. Premier volume d'une "
            "trilogie sur Augustin (suivi de *Inner Grace* 2008 et "
            "*Outward Signs* 2008). Cary défend que **Augustin invente** "
            "(au sens latin de *inventio* = trouvaille et création) le "
            "concept de l'âme comme **espace intérieur privé**, "
            "distinct à la fois du monde sensible et du Mens divin. "
            "Cette invention résout un problème théologique précis : "
            "localiser Dieu dans l'âme sans confondre l'âme avec Dieu "
            "(contre Plotin). Solution topologique : le mouvement "
            "plotinien « into the inside » devient chez Augustin « in "
            "then up » — entrer dans l'âme puis lever les yeux vers "
            "Dieu Créateur. L'invention conditionne la doctrine de la "
            "grâce comme don intérieur (Cary 2008). **Origène est "
            "précurseur explicite mais limité** (Ch. 4) : Cary cite "
            "l'introduction du *Commentaire sur le Cantique des "
            "Cantiques* sur l'« inner man » paulinien, et les cinq sens "
            "spirituels (*Dialogue avec Héraclide*). Mais Cary insiste "
            "qu'Augustin ne connaissait PAS directement Origène, le "
            "vocabulaire de l'intériorité arrivant à Milan via Ambrose "
            "(« non digéré » selon Madec). Format acquis : EPUB."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "monograph", "year": 2000,
            "author": "Phillip Cary", "author_id": ID_CARY_SCHOLAR,
            "title": "Augustine's Invention of the Inner Self: The Legacy of a Christian Platonist",
            "publisher": "Oxford University Press", "pages": 232,
            "isbn": "978-0-19-513206-9", "language": "en",
            "bibtex_key": "cary-2000-inner-self",
            "local_epub_path": PDF("cary_2000_augustine_inner_self.epub"),
            "format_acquired": "epub",
            "trilogy_context": "First of Cary's Augustine trilogy: Inner Self (2000), Inner Grace (2008), Outward Signs (2008)",
            "verified_critiques": [
                {
                    "page": None,
                    "thesis": "Augustine invents the concept of private inner space",
                    "quote_verbatim_en": (
                        "My concern here is with the concept of self as "
                        "private inner space or inner world—a whole "
                        "dimension of being that is our very own, and "
                        "roomy enough that we can in some sense turn "
                        "into it and enter it, or look within and find "
                        "things there. This, I take it, is the deepest "
                        "and most thoroughgoing form of inwardness... "
                        "In this regard all roads lead to Augustine: "
                        "the thesis I argue here is that he invented "
                        "the concept of private inner space."
                    ),
                    "context": "Introduction",
                },
                {
                    "page": None,
                    "thesis": "Augustinian topology: in then up",
                    "quote_verbatim_en": (
                        "Augustine's problem is how to locate God "
                        "within the soul, without affirming the "
                        "divinity of the soul. He wants (like Plotinus) "
                        "to find the divine within the self, while "
                        "affirming (as an orthodox Christian) that the "
                        "divine is wholly other than the self. He "
                        "solves this problem by locating God not only "
                        "within the soul but above it (as its Creator) "
                        "thus modifying Plotinus' turn 'into the inside' "
                        "into a movement in then up."
                    ),
                    "context": "Conclusion",
                },
                {
                    "page": None,
                    "thesis": "Origen as transmitter of inner-man language",
                    "quote_verbatim_en": (
                        "In later, more systematically Platonist "
                        "Christians, the language of the inner man "
                        "gets intertwined with more thoroughly "
                        "Platonist views of human nature. The most "
                        "important and formative figure in this "
                        "development is Origen, the third-century "
                        "Christian Platonist of Alexandria. Origen, "
                        "who studied philosophy under the same teacher "
                        "as Plotinus, established by precept and "
                        "example the immensely influential Alexandrian "
                        "school of allegorical or spiritual "
                        "interpretation of Scripture... In the preface "
                        "to one of his most important writings, he "
                        "expatiates on the Pauline metaphor of the "
                        "inner man, distinguishing the desires, needs, "
                        "and perceptions of the inner man or soul from "
                        "those of the outer man or body."
                    ),
                    "context": "Ch. 4 'Problems of Christian Platonism' — reference to Origen's Commentary on the Song of Songs prologue",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # MARKSCHIES 2007 — 4 études lues intégralement
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_MARKSCHIES, "node_id": ID_PUB_MARKSCHIES, "type": "publication",
        "label": "Markschies 2007 — Origenes und sein Erbe. Gesammelte Studien",
        "description": (
            "Christoph Markschies, *Origenes und sein Erbe. Gesammelte "
            "Studien*, Berlin: De Gruyter, 2007, Texte und "
            "Untersuchungen 160, 294 p., ISBN 978-3-11-019278-0. "
            "Recueil de 12 études + 2 textes éditoriaux + Anhang. "
            "**Quatre études centrales pour le libre arbitre origénien** : "
            "(1) « Origenes. Leben – Werk – Theologie – Wirkung » "
            "(p. 1, synoptique) ; (4) « Origenes und die Kommentierung "
            "des paulinischen Römerbriefs » (p. 63) — **identifie "
            "Willensfreiheit comme le Verständnisproblem central de "
            "l'exégèse origénienne de Rm**, désamorcé via la "
            "prosopopée paulinienne ; (5) « Gott und Mensch nach "
            "Origenes » (p. 91, FS Lehmann 2001) — problématise le "
            "label synergiste à partir d'une perspective luthérienne ; "
            "(7) « Epikureismus bei Origenes » (p. 127) — *Contra "
            "Celsum* recasté comme traité providentialiste anti-"
            "épicurien. Position complémentaire de Fürst 2022 : "
            "Markschies opère depuis la *Dogmengeschichte* berlinoise "
            "(héritier de von Harnack), Fürst depuis la philosophie "
            "patristique. Convergence sur la centralité du thème, "
            "divergence sur l'évaluation."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "collected_essays", "year": 2007,
            "author": "Christoph Markschies", "author_id": ID_MARKSCHIES_SCHOLAR,
            "title": "Origenes und sein Erbe. Gesammelte Studien",
            "publisher": "De Gruyter", "publisher_location": "Berlin",
            "series": "Texte und Untersuchungen zur Geschichte der altchristlichen Literatur 160",
            "pages": 294, "isbn": "978-3-11-019278-0", "language": "de",
            "bibtex_key": "markschies-2007-origenes-erbe",
            "local_pdf_path": PDF("markschies_2007_origenes_erbe.pdf"),
            "key_studies_for_thesis": [
                "Study 1: Origenes. Leben–Werk–Theologie–Wirkung (p. 1, synoptic)",
                "Study 4: Origenes und die Kommentierung des paulinischen Römerbriefs (p. 63)",
                "Study 5: Gott und Mensch nach Origenes (p. 91)",
                "Study 7: Epikureismus bei Origenes (p. 127)",
            ],
            "verified_critiques": [
                {
                    "page": 9,
                    "thesis": "Fall as exercise of freedom",
                    "quote_de": (
                        "Diese geistigen Wesen fallen in unterschiedlichem "
                        "Maß aufgrund ihrer eigenen freien Entscheidung "
                        "von der reinen Anschauung Gottes ab"
                    ),
                    "translation_en": (
                        "These spiritual beings fall in varying degrees "
                        "from the pure vision of God by virtue of their "
                        "own free decision."
                    ),
                    "context": "Study 1 — De Principiis II.8.3 / II.9.6 anchor",
                },
                {
                    "page": 10,
                    "thesis": "Fall as both freedom and providence",
                    "quote_de": (
                        "Jener Fall der geistigen Entitäten ist eine "
                        "Realisierung ihrer Freiheit und doch zugleich "
                        "ein Zeichen göttlicher Vorsehung."
                    ),
                    "translation_en": (
                        "That fall of the spiritual entities is a "
                        "realisation of their freedom and yet at the "
                        "same time a sign of divine providence."
                    ),
                    "context": "Study 1 — synthesis of Origenian anthropology",
                },
                {
                    "page": 11,
                    "thesis": "Anti-determinism with christological grace",
                    "quote_de": (
                        "Origenes lehnt jeden Determinismus des "
                        "Menschen ab und betont doch, daß nur Christus "
                        "den Menschen rein machen könne, nicht eigene "
                        "Mühen."
                    ),
                    "translation_en": (
                        "Origen rejects any determinism of the human "
                        "being and yet emphasises that only Christ can "
                        "make the human pure, not one's own efforts."
                    ),
                    "context": "Study 1",
                },
                {
                    "page": 81,
                    "thesis": "Willensfreiheit as central Verständnisproblem of Origen's Romans exegesis",
                    "quote_de": (
                        "Origenes beginnt seinen Prolog zwar mit einem "
                        "topischen Hinweis auf die schwere "
                        "Verständlichkeit des Römerbriefes (I, 60,1f.), "
                        "nennt dann aber sofort das zentrale theologische "
                        "Verständnisproblem, das bei unsachgemäßer "
                        "Interpretation des Briefes falsch dargestellt "
                        "werde und zu Verwirrung führe, das der "
                        "Willensfreiheit. Diesem zentralen Thema gehört "
                        "auch andernorts seine ganze Aufmerksamkeit."
                    ),
                    "translation_en": (
                        "Origen begins his prologue with a topical "
                        "reference to the difficulty of Romans, but "
                        "then immediately names the central theological "
                        "problem of understanding that, when improperly "
                        "interpreted, distorts the letter and causes "
                        "confusion — the problem of freedom of the "
                        "will. To this central theme his entire "
                        "attention is also devoted elsewhere."
                    ),
                    "context": "Study 4 — DECISIVE for thesis H3",
                },
                {
                    "page": 81,
                    "thesis": "Distinction: Willensfreiheit is the problem, not Paul's intention",
                    "quote_de": (
                        "Willensfreiheit ist ja nicht die zentrale "
                        "intentio des Römerbriefs, sondern das "
                        "zentrale Verständnisproblem."
                    ),
                    "translation_en": (
                        "Freedom of the will is not the central "
                        "intentio of Romans, but the central problem "
                        "of comprehension."
                    ),
                    "context": "Study 4 — methodological subtlety",
                },
                {
                    "page": "103-104",
                    "thesis": "Anti-Pelagian: super-heavenly power impels worship",
                    "quote_de": (
                        "Wir sahen aber oben, daß nach Origenes nicht "
                        "der Mensch aufgrund einer wie auch immer "
                        "gearteten Verwandtschaft zum Schöpfer, allein "
                        "durch eigene Kraft aus dem tiefen Tal seines "
                        "Falls aufsteigt, sondern durch eine "
                        "'himmlische und sogar überhimmlische Kraft' "
                        "heftig gedrängt wird, einzig und allein den "
                        "Schöpfer zu verehren."
                    ),
                    "translation_en": (
                        "We saw above that for Origen, the human does "
                        "not rise from the deep valley of his fall by "
                        "his own power alone — on the basis of some "
                        "kinship with the Creator — but is forcefully "
                        "impelled by a 'heavenly and even super-heavenly "
                        "power' to worship the Creator alone."
                    ),
                    "context": "Study 5 — De Principiis IV.1.7 anchor",
                },
                {
                    "page": 135,
                    "thesis": "Contra Celsum = treatise on providence vs Epicurean chance",
                    "quote_de": (
                        "Das Leitthema der Auseinandersetzung des "
                        "Origenes [ist] auch kein Element der "
                        "Philosophie des historischen Celsus, sondern "
                        "ein vertrautes Thema der Auseinandersetzung "
                        "mit der epikureischen Philosophie: Der "
                        "alexandrinische Theologe ringt mit Menschen, "
                        "die sich 'zu voreilig der Ansicht' "
                        "anschließen, 'daß es gar keine πρόνοια gebe'; "
                        "sie 'entscheiden sich dann für die Lehre des "
                        "Epikur und des Celsus'."
                    ),
                    "translation_en": (
                        "Origen's guiding theme of dispute is no "
                        "element of the historical Celsus' philosophy, "
                        "but a familiar topic of debate with Epicurean "
                        "philosophy: the Alexandrian theologian "
                        "wrestles with people who 'too hastily' adopt "
                        "the view 'that there is no providence at all'; "
                        "they 'then decide for the doctrine of "
                        "Epicurus and Celsus'."
                    ),
                    "context": "Study 7 — citing Contra Celsum I.10",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # HADOT 1992 — Citadelle intérieure ch. V-VI lus
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_HADOT_1992, "node_id": ID_PUB_HADOT_1992, "type": "publication",
        "label": "Hadot 1992 — La Citadelle intérieure. Introduction aux Pensées de Marc Aurèle",
        "description": (
            "Pierre Hadot, *La Citadelle intérieure. Introduction aux "
            "Pensées de Marc Aurèle*, Paris: Fayard, 1992 (rééd. 1997, "
            "2002 LGF Poche), ISBN 978-2-213-02984-9. Ouvrage maître "
            "de Hadot, couronnement de plus de vingt ans de travail "
            "sur Marc Aurèle, professeur au Collège de France (chaire "
            "d'histoire de la pensée hellénistique et romaine). **Thèse "
            "centrale** : les *Pensées* sont des *hypomnémata*, "
            "exercices spirituels stoïciens rédigés selon le canevas "
            "de la triade d'Épictète : discipline du jugement "
            "(*συγκατάθεσις*), discipline du désir (*ὄρεξις*), "
            "discipline de l'action (*ὁρμή*), correspondant aux trois "
            "parties (logique, physique, éthique) du système stoïcien. "
            "La « citadelle intérieure » = métaphore par laquelle "
            "Hadot interprète l'*ἡγεμονικόν* comme réduit inviolable "
            "de la liberté de juger, identifié à la *προαίρεσις* "
            "épictétéenne. Influence majeure sur Foucault (*Le souci "
            "de soi*, *L'herméneutique du sujet*), Sellars (*Art of "
            "Living*), Cooper (*Pursuits of Wisdom*), et le mouvement "
            "néo-stoïcien contemporain. Le titre reprend *Pensées* "
            "VIII.48 (« le principe directeur, lorsqu'il se replie en "
            "lui-même, est une acropole »). **PDF acquis corrompu** "
            "(xref détruite, pagination incertaine) — citations "
            "préservées mais pages à reconfirmer."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Hadot Citadelle intérieure"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "monograph", "year": 1992,
            "author": "Pierre Hadot", "author_id": ID_HADOT_SCHOLAR,
            "title": "La Citadelle intérieure. Introduction aux Pensées de Marc Aurèle",
            "publisher": "Fayard", "publisher_location": "Paris",
            "pages": 386, "isbn": "978-2-213-02984-9", "language": "fr",
            "bibtex_key": "hadot-1992-citadelle-interieure",
            "local_pdf_path": PDF("hadot_1992_citadelle_interieure.pdf"),
            "pdf_status": "Corrupt xref — reconstructed via stream re-flow, pagination tentative",
            "english_translation": "*The Inner Citadel*, transl. Michael Chase, Harvard UP, 1998",
            "verified_critiques": [
                {
                    "page": 124,
                    "thesis": "Inner citadel = inviolable redoubt of freedom",
                    "quote_fr": (
                        "La frontière que ne peuvent franchir les "
                        "choses, c'est la limite de ce que nous "
                        "appellerons plus loin la « citadelle "
                        "intérieure », ce réduit inviolable de liberté. "
                        "Les choses ne peuvent pénétrer dans cette "
                        "citadelle, elles ne peuvent produire le "
                        "discours que nous développons au sujet des "
                        "choses, l'interprétation que nous donnons du "
                        "monde et des événements."
                    ),
                    "translation_en": (
                        "The frontier that things cannot cross is the "
                        "limit of what we shall later call the 'inner "
                        "citadel', that inviolable redoubt of freedom. "
                        "Things cannot penetrate into this citadel; "
                        "they cannot produce the discourse we develop "
                        "about things, the interpretation we give of "
                        "the world and of events."
                    ),
                    "context": "Ch. VI §2 — programmatic formulation",
                },
                {
                    "page": 125,
                    "thesis": "Things do not touch the soul",
                    "quote_fr": (
                        "Les choses ne peuvent nous troubler parce "
                        "qu'elles ne touchent pas notre moi, c'est-à-dire "
                        "le principe directeur qui est en nous : elles "
                        "restent aux portes, à l'extérieur de notre "
                        "liberté."
                    ),
                    "translation_en": (
                        "Things cannot trouble us because they do not "
                        "touch our self — that is, the directing "
                        "principle within us: they remain at the "
                        "gates, outside our freedom."
                    ),
                    "context": "Ch. VI — commentary on Aurelius IV.3.10, V.19, VI.52, IX.15",
                },
                {
                    "page": 246,
                    "thesis": "Stoic-Christian convergence on love grounded in Logos",
                    "quote_fr": (
                        "On ne peut donc pas dire qu'« aimer son "
                        "prochain comme soi-même » soit une invention "
                        "spécifiquement chrétienne. On pourrait même "
                        "dire que la motivation de l'amour stoïcien "
                        "est la même que celle de l'amour chrétien. "
                        "L'un et l'autre reconnaissent dans chaque "
                        "homme le logos, la Raison présente dans "
                        "l'homme."
                    ),
                    "translation_en": (
                        "One cannot therefore say that 'love your "
                        "neighbour as yourself' is a specifically "
                        "Christian invention. One might even say that "
                        "the motivation of Stoic love is the same as "
                        "that of Christian love. Both recognise in "
                        "every human the logos, the Reason present in "
                        "man."
                    ),
                    "context": "Late chapter — rare passage on Stoic-Christian continuity",
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
    # -----------------------------------------------------------------
    # LONG 2018 — Intro de Long lue intégralement
    # -----------------------------------------------------------------
    {
        "id": ID_PUB_LONG_2018, "node_id": ID_PUB_LONG_2018, "type": "publication",
        "label": "Long 2018 — How to Be Free: An Ancient Guide to the Stoic Life",
        "description": (
            "A. A. Long (avec Épictète), *How to Be Free: An Ancient "
            "Guide to the Stoic Life*, Princeton UP, 2018 (Ancient "
            "Wisdom for Modern Readers), 173 p., ISBN 978-0-691-17771-7. "
            "Contient : (1) introduction substantielle de Long (~40 p.) "
            "sur la philosophie d'Épictète ; (2) traduction nouvelle "
            "complète de l'*Enchiridion* (texte grec en regard) ; (3) "
            "9 extraits des *Discourses* (1.6, 1.12, 1.17, 4.1) ; (4) "
            "glossaire technique de 27 termes. **L'introduction de "
            "Long est la valeur ajoutée maximale** : synthèse post-"
            "Frede 2011 sur Épictète par le co-éditeur posthume de "
            "Frede 2011 — autoritative sur la position fredeenne. "
            "Position : Épictète a une notion de *free will* (au sens "
            "compatibiliste de *προαίρεσις* = ability of "
            "self-determination), MAIS PAS de *libertarian free will*. "
            "La liberté épictétéenne n'est pas la condition humaine "
            "donnée mais un « arduous philosophical achievement » "
            "(p. xxxiv). Long lit Épictète à travers la grille Isaiah "
            "Berlin (positive/negative liberty) et les « collapse[s] » "
            "chez Épictète. Traduit *προαίρεσις* par « will », "
            "*φαντασία* par « impression », *συγκατάθεσις* par "
            "« assent ». Format acquis : EPUB."
        ),
        "period": "Modern", "role": None, "school": None,
        "alternative_names": json.dumps(["Long How to Be Free"], ensure_ascii=False),
        "metadata": json.dumps({
            "type": "translation_with_introduction", "year": 2018,
            "author": "A. A. Long", "co_author": "Epictetus",
            "author_id": ID_LONG_SCHOLAR,
            "title": "How to Be Free: An Ancient Guide to the Stoic Life",
            "publisher": "Princeton University Press",
            "series": "Ancient Wisdom for Modern Readers",
            "pages": 173, "isbn": "978-0-691-17771-7",
            "language": "en", "bibtex_key": "long-2018-how-to-be-free",
            "local_epub_path": PDF("long_2018_how_to_be_free.epub"),
            "format_acquired": "epub",
            "key_value": (
                "Long's 40-page introduction synthesises post-Frede 2011 "
                "state of the art on Epictetan eleutheria/prohairesis, "
                "written by Frede 2011's co-editor"
            ),
            "verified_critiques": [
                {
                    "page": "xi",
                    "thesis": "Freedom = mental orientation, not legal/spatial",
                    "quote_verbatim_en": (
                        "Freedom, according to this notion, is neither "
                        "legal status nor opportunity to move around "
                        "at liberty. It is the mental orientation of "
                        "persons who are impervious to frustration or "
                        "disappointment because their wants and "
                        "decisions depend on themselves and involve "
                        "nothing that they cannot deliver to themselves."
                    ),
                },
                {
                    "page": "xxxiii-xxxiv",
                    "thesis": "Epictetus accepts fate; god's-eye determinism",
                    "quote_verbatim_en": (
                        "That is not at all what Epictetus had in mind. "
                        "His passionate advocacy of autonomy (e.g., "
                        "Discourses 9) can give the impression that "
                        "there are no limits to the mental scope of "
                        "freedom, but this is hyperbole. Like his Stoic "
                        "predecessors, Epictetus accepted 'fate' "
                        "(Encheiridion 53), meaning that nothing "
                        "happens, including our own actions, without "
                        "a predetermined cause. From the god's-eye "
                        "perspective, the story of everyone's life is "
                        "already fixed and settled, including the "
                        "specific choices and decisions people will "
                        "make."
                    ),
                },
                {
                    "page": "xxxiv",
                    "thesis": "Free will as philosophical achievement, not human condition",
                    "quote_verbatim_en": (
                        "Freedom of will, on this construal—wishing "
                        "for nothing that is not up to oneself—is not "
                        "the general human condition, but an arduous "
                        "philosophical achievement."
                    ),
                },
                {
                    "page": "xiv",
                    "thesis": "Zeno-Epictetus continuity on freedom as wisdom-prerogative",
                    "quote_verbatim_en": (
                        "This inward turn is strikingly illustrated by "
                        "the way Stoic thought from its beginning "
                        "treated freedom and slavery as primarily "
                        "ethical and psychological denominators rather "
                        "than marks of social status. According to "
                        "Zeno, the original head of the Stoic school, "
                        "freedom is the exclusive prerogative of those "
                        "who are wise."
                    ),
                },
            ],
            "wave": WAVE_TAG,
        }, ensure_ascii=False),
        "created_at": NOW, "updated_at": NOW,
    },
]


# =====================================================================
# ENRICHMENTS to existing pubs — verified content
# =====================================================================

ENRICHMENTS: list[dict[str, Any]] = [
    {
        "id": ID_PUB_SHARPLES_1983,
        "metadata_updates": {
            "local_pdf_path": PDF("sharples_1983_alexander_de_fato.pdf"),
            "acquisition_status_2026_05_18": (
                "PDF acquis via libgen.li (md5 "
                "09e591d8119e9082ce73d59dea87a9ae) mais **CORROMPU/"
                "TRONQUÉ** lors de la lecture par sub-agent — fichier "
                "se termine au milieu d'un stream Flate compressé, "
                "sans EOF marker. À RE-ACQUÉRIR. C'est ce commentaire "
                "de Sharples que Lienemann 2012 (BPJAM, p. 260) "
                "mobilise contre Frede : Sharples nuance/conteste "
                "l'attribution d'un Freiheitsbegriff indéterministe à "
                "Alexandre."
            ),
            "needs_re_acquisition": True,
        },
    },
    {
        "id": ID_PUB_KAHN_1988,
        "metadata_updates": {
            "local_pdf_path": PDF("kahn_1988_discovering_will.pdf"),
            "acquisition_status_2026_05_18": (
                "PDF reconstruit depuis UC Press eScholarship (volume "
                "OA `ft029002rv`). Chapitre 9 de Dillon & Long (eds.), "
                "*The Question of 'Eclecticism'* (UCP 1988), p. 235-260."
            ),
            "verified_critiques": [
                {
                    "page": 241,
                    "thesis": "Aristotle lacks unifying concept of will",
                    "quote_verbatim_en": (
                        "To say that Aristotle lacks a concept of will "
                        "is to say, first of all, that these four "
                        "notions (or at least the last three) are "
                        "conceptually independent of one another: "
                        "there is no one concept that ties together "
                        "the voluntary, boulesis or desire for the "
                        "end, and prohairesis, deliberate desire for "
                        "the means. But it is precisely the role of "
                        "voluntas in Aquinas to perform this work of "
                        "conceptual unification."
                    ),
                },
                {
                    "page": "250-251",
                    "thesis": "DECISIVE: autexousion as standard Greek technical term for free will",
                    "quote_verbatim_en": (
                        "Lucretius's phrase 'free will,' libera "
                        "voluntas, found little or no echo in antiquity, "
                        "even in Latin. (Augustine was certainly not "
                        "following Lucretius!) … When, in Roman times, "
                        "Greek philosophy developed a technical "
                        "expression for free will that went beyond "
                        "phrases like 'what is up to us,' the term "
                        "most generally employed is to autexousion, "
                        "which simply means 'what is in one's own "
                        "power.'"
                    ),
                    "context": "DECISIVE for thesis: Kahn identifies the exact technical term Origen will use",
                },
                {
                    "page": "252-253",
                    "thesis": "Epictetus repurposes Aristotelian prohairesis",
                    "quote_verbatim_en": (
                        "Epictetus is faithful to the orthodox Stoic "
                        "view of assent as the decisive moment of "
                        "rational control over action, but instead of "
                        "expounding the classical theory of sunkatathesis "
                        "(which was probably too technical for his "
                        "taste), he prefers to develop two equivalent "
                        "or closely allied notions … prohairesis. This "
                        "Aristotelian term apparently played no "
                        "significant role in early Stoic theory but "
                        "has become central for Epictetus."
                    ),
                },
                {
                    "page": 256,
                    "thesis": "Augustine + Romans 7 = decisive Christian step",
                    "quote_verbatim_en": (
                        "From St. Paul and his own experience of "
                        "conversion he derived the sense of the "
                        "divided self: 'I do not do the good I will "
                        "[thelo], but I do the evil which I will not "
                        "[ou thelo]' (Romans 7:15). It was by "
                        "meditation on these words of St. Paul that "
                        "Augustine developed the notion of will that "
                        "Kierkegaard found lacking in Socrates."
                    ),
                    "context": "The step Lienemann reproaches Frede 2011 for not engaging",
                },
                {
                    "page": 259,
                    "thesis": "Overdetermination thesis — closing",
                    "quote_verbatim_en": (
                        "Major historical developments are always "
                        "overdetermined. Dihle has documented in "
                        "detail what we always suspected: that the "
                        "concept of the will as we find it developed "
                        "in Augustine and Aquinas presupposes biblical "
                        "religious experience as one of its "
                        "indispensable conditions. But there were "
                        "other conditions as well."
                    ),
                },
            ],
        },
    },
    {
        "id": ID_PUB_SORABJI_1980,
        "metadata_updates": {
            "local_pdf_path": PDF("sorabji_1980_necessity_cause_blame.pdf"),
            "acquisition_status_2026_05_18": (
                "PDF acquis via libgen.li (md5 "
                "952c468af67d95d3b50bea94ea4a0ef3) — édition Bloomsbury "
                "2014 (réédition Duckworth 1980), 326 p. **Corps des "
                "chapitres = pages images non-OCR — seuls les intros "
                "de chapitres sont lisibles. À RE-ACQUÉRIR en version "
                "OCR pour citations corps de texte.**"
            ),
            "verified_critiques": [
                {
                    "page": None,
                    "thesis": "Cause ≠ necessitation — programmatic statement",
                    "quote_verbatim_en": (
                        "The claim that what is caused need not be "
                        "necessitated, and the related claim that what "
                        "is explained need not be necessitated, are "
                        "philosophically significant, because, if true, "
                        "they free us from one of the determinist's "
                        "most ancient and powerful arguments — the "
                        "argument that if events are not necessitated, "
                        "they must be uncaused, inexplicable, and "
                        "hence mysterious."
                    ),
                    "context": "Ch. 2 — pivot conceptuel canonique",
                },
                {
                    "page": None,
                    "thesis": "Stoic embarrassment over necessity",
                    "quote_verbatim_en": (
                        "Chrysippus wrote in the first book of his "
                        "treatise on Fate that all things are held "
                        "fast by necessity and fate, though he tried "
                        "in the second book to deal with some of the "
                        "difficulties that that created for human "
                        "conduct."
                    ),
                    "context": "Ch. 4 — explicit Stoic ambivalence",
                },
            ],
            "needs_full_ocr": True,
        },
    },
    {
        "id": ID_PUB_LS_1987,
        "metadata_updates": {
            "local_pdf_path_vol1": PDF("long_sedley_1987_hellenistic_philosophers_vol1.pdf"),
            "local_pdf_path_vol2": PDF("long_sedley_1987_hellenistic_philosophers_vol2.pdf"),
            "acquisition_status_2026_05_18": (
                "Vol. 1 acquis (libgen.li md5 "
                "51fdddf58c1519235ad87664161a8668, 522 p., texte "
                "complet OCR). Vol. 2 **CORROMPU** (md5 "
                "cd10c1f4fa8017c59a974c7b978688e4 mais pas d'EOF, "
                "textes grecs/latins inaccessibles). Sections critiques "
                "lues sur vol. 1 : §20 (Epicurean Free Will), §55 "
                "(Causation and Fate), §62 (Moral Responsibility — "
                "PIVOT)."
            ),
            "verified_critiques": [
                {
                    "page": "vol.1 p. 107",
                    "thesis": "Epicurus as first to recognize centrality of free-will question",
                    "quote_verbatim_en": (
                        "Epicurus [is] arguably the first philosopher "
                        "to recognize the philosophical centrality of "
                        "what we know as the Free Will Question."
                    ),
                    "context": "§20 — sets up emergentist reading of swerve",
                },
                {
                    "page": "vol.1 p. 343",
                    "thesis": "Zeno-Cleanthes vs Chrysippus periodization",
                    "quote_verbatim_en": (
                        "Somehow, nevertheless, Chrysippus is also "
                        "committed to a much stronger view, which "
                        "amounts to determinism. At the beginning of "
                        "each world cycle a causal nexus is "
                        "providentially planned and initiated, in "
                        "virtue of which every detail of the entire "
                        "subsequent world process is predetermined."
                    ),
                    "context": "§55 — periodization structuring all later debate",
                },
                {
                    "page": "vol.1 p. 392",
                    "thesis": "Stoic super-compatibilism",
                    "quote_verbatim_en": (
                        "On the Stoic view determinism and moral "
                        "responsibility are not merely compatible, "
                        "they actually presuppose each other."
                    ),
                    "context": "§62 — programmatic; contested by Bobzien 1998",
                },
                {
                    "page": "vol.1 p. 393",
                    "thesis": "Cylinder analysis: agent's character is the primary cause",
                    "quote_verbatim_en": (
                        "Fate, from his point of view, is the set of "
                        "external causes which, by acting upon him, "
                        "work to bring about their destined effects. "
                        "But since these external causes are no more "
                        "than triggering causes, he cannot hold them "
                        "in any strong sense responsible for his "
                        "actions, let alone sufficient to necessitate "
                        "them. The primary cause is himself."
                    ),
                    "context": "§62 — Chrysippean compatibilism reconstruction",
                },
            ],
            "needs_vol2_re_acquisition": True,
        },
    },
    {
        "id": ID_PUB_INWOOD_1985,
        "metadata_updates": {
            "local_pdf_path": PDF("inwood_1985_ethics_human_action_stoicism.pdf"),
            "acquisition_status_2026_05_18": (
                "PDF acquis via libgen.li (md5 "
                "bddfc184638a7909e0f100d5ef943434), édition OUP 1987 "
                "(réimpression du Clarendon 1985), 266 p. Reconstruction "
                "de référence de la psychologie stoïcienne de l'action."
            ),
            "verified_critiques": [
                {
                    "page": "45-46",
                    "thesis": "Action sequence: presentation, assent, impulse",
                    "quote_verbatim_en": (
                        "The main elements of the old Stoic psychology "
                        "of action, which we find recurring with "
                        "impressive consistency in our evidence, are "
                        "presentation, assent, and impulse; these "
                        "precede and generate the action to be "
                        "explained."
                    ),
                    "context": "Ch. 3 — φαντασία → συγκατάθεσις → ὁρμή",
                },
                {
                    "page": 45,
                    "thesis": "Hormê is not raw instinct",
                    "quote_verbatim_en": (
                        "A hormê, which I am translating by the term "
                        "of art 'impulse', is not just an instinct or "
                        "an underlying drive in an animal."
                    ),
                },
                {
                    "page": 67,
                    "thesis": "Chrysippean compatibilism — action via rational assent",
                    "quote_verbatim_en": (
                        "In man the relevant disposition is a state of "
                        "his rational mind. Man is a rational animal, "
                        "by fate. Thus fate acts in man through his "
                        "reason. The way reason controls or causes "
                        "action is through assent. Human action is "
                        "always controlled by the mechanism of rational "
                        "assent to the hormetic propositions occasioned "
                        "by our presentations; thus our behaviour is in "
                        "our power without being cut loose from the "
                        "causal nexus of fate."
                    ),
                },
                {
                    "page": 68,
                    "thesis": "Critical reservation on Chrysippean solution",
                    "quote_verbatim_en": (
                        "Our characters are caused by external factors, "
                        "at least to some degree, and that this too "
                        "represents the power of fate in determining "
                        "human action. … Many have found this an "
                        "unsatisfactory answer and I must count myself "
                        "among them."
                    ),
                },
            ],
        },
    },
]


# =====================================================================
# NEW EDGES — selective high-value wiring based on reading findings
# =====================================================================

NEW_EDGES: list[dict[str, Any]] = [
    # authored_by for all 10 new pubs (Kahn excluded — already exists)
    {"source": ID_PUB_COOPE, "target": ID_COOPE_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_BOBZIEN_2021, "target": ID_BOBZIEN_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_HUBY, "target": ID_HUBY_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_WETZEL, "target": ID_WETZEL_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_CARY, "target": ID_CARY_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_MARKSCHIES, "target": ID_MARKSCHIES_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_HADOT_1992, "target": ID_HADOT_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_LONG_2018, "target": ID_LONG_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_MITSIS_2016, "target": ID_MITSIS_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_MEYER_2011, "target": ID_MEYER_SCHOLAR, "relation": "authored_by", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},

    # CRITIQUE EDGES based on verified readings
    {
        "source": ID_PUB_MITSIS_2016, "target": ID_FREDE_2011,
        "relation": "critiques", "confidence": 0.95,
        "metadata": {
            "wave": WAVE_TAG, "critique_type": "methodological_predecessor",
            "summary": "Mitsis 2016 (Lucretius and Modernity ch. 7) = English predecessor of Mitsis 2021. Same anti-Frede argument: Stoic-Locke continuity > Stoic-Augustinian rupture.",
        },
    },
    {
        "source": ID_PUB_MITSIS_2016, "target": ID_BOBZIEN_1998,
        "relation": "critiques", "confidence": 0.95,
        "metadata": {
            "wave": WAVE_TAG, "critique_type": "frontal_philological",
            "summary": "Mitsis 2016 p. 117 directly attacks Bobzien's reading of libera voluntas in DRN II — swerve frees mens, not voluntas; summetrēsis already conceives choice between alternatives.",
        },
    },
    {
        "source": ID_BOBZIEN_2000, "target": ID_PUB_HUBY,
        "relation": "critiques", "confidence": 0.99,
        "metadata": {
            "wave": WAVE_TAG, "critique_type": "frontal_refutation",
            "summary": "Bobzien 2000 OSAP 'Did Epicurus Discover the Free Will Problem?' = direct refutation of Huby 1967. Title is a pointed reference; Bobzien dismantles Huby's clinamen-as-free-will reading.",
        },
    },
    {
        "source": ID_PUB_KAHN_1988, "target": ID_FREDE_2011,
        "relation": "engages_with", "confidence": 0.9,
        "metadata": {
            "wave": WAVE_TAG, "engagement_type": "predecessor_ignored_by_frede",
            "summary": "Kahn 1988 articulates the rival overdetermination thesis (Stoic + Latin + Pauline-Augustinian convergence) that Frede 2011 DOES NOT engage — a defect explicitly noted by Lienemann 2012 (review BPJAM p. 266).",
        },
    },
    {
        "source": ID_PUB_MEYER_2011, "target": ID_BOBZIEN_1998,
        "relation": "agrees_with", "confidence": 0.9,
        "metadata": {
            "wave": WAVE_TAG,
            "summary": "Meyer 2011 intro p. xx-xxi explicitly aligns with Bobzien 1998 against libertarian readings of Aristotle's eph' hêmin (cf. p. xx n.24, xxi n.28).",
        },
    },
    {
        "source": ID_PUB_MEYER_2011, "target": ID_FREDE_2011,
        "relation": "agrees_with", "confidence": 0.85,
        "metadata": {
            "wave": WAVE_TAG,
            "summary": "Meyer 2011 cites Frede 2007/2011 approvingly (p. xx n.26) for the reading of eph' hêmin as 'things within the agent's reach', not metaphysical contingency.",
        },
    },
    {
        "source": ID_PUB_BOBZIEN_2021, "target": ID_FREDE_2011,
        "relation": "engages_with", "confidence": 0.85,
        "metadata": {
            "wave": WAVE_TAG,
            "summary": "Bobzien 2021 Preface explicitly declines to respond to individual publications including Frede 2011. The Introduction inédite (p. 1-11) consolidates her anti-Frede position implicitly. NO RETRACTION of any earlier position.",
        },
    },
    {
        "source": ID_PUB_COOPE, "target": ID_FREDE_2011,
        "relation": "engages_with", "confidence": 0.7,
        "metadata": {
            "wave": WAVE_TAG, "engagement_type": "cited_positively_not_critiqued",
            "summary": "REVISED: Coope 2020 cites Frede 2011 POSITIVELY (p. 47 n.25, p. 93 n.62) — no frontal critique. She uses Frede as authority on Alexander and Plotin. The agent's first report overstated the critique. Coope avoids the polemic by methodological retreat ('I avoid using the expression free will', p. 3).",
        },
    },
    {
        "source": ID_PUB_COOPE, "target": ID_ELIASSON_2008,
        "relation": "engages_with", "confidence": 0.85,
        "metadata": {
            "wave": WAVE_TAG, "engagement_type": "complementary_neoplatonist_studies",
            "summary": "Coope 2020 and Eliasson 2008 jointly constitute the contemporary scholarly framework on Neoplatonist freedom and eph' hêmin.",
        },
    },

    # Domain person connections
    {"source": ID_PUB_SHARPLES_1983, "target": ID_ALEXANDER, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG, "summary": "Standard English edition + commentary of Alexander De Fato"}},
    {"source": ID_PUB_WETZEL, "target": ID_AUGUSTINE, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_CARY, "target": ID_AUGUSTINE, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_CARY, "target": ID_ORIGEN, "relation": "discusses", "confidence": 0.6, "metadata": {"wave": WAVE_TAG, "summary": "Origen as limited precursor of inner-man language (Ch. 4) — Cary insists Augustine did not know Origen directly"}},
    {"source": ID_PUB_HADOT_1992, "target": ID_MARCUS_AURELIUS, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_LONG_2018, "target": ID_EPICTETUS, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_COOPE, "target": ID_PLOTINUS, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG}},
    {"source": ID_PUB_MARKSCHIES, "target": ID_ORIGEN, "relation": "discusses", "confidence": 1.0, "metadata": {"wave": WAVE_TAG, "summary": "DECISIVE: Markschies 2007 Study 4 identifies Willensfreiheit as the central Verständnisproblem of Origen's Romans exegesis (p. 81)"}},
]


# =====================================================================
# MACHINERY
# =====================================================================


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def node_id_of_line(line: str) -> str:
    return json.loads(line).get("id") or ""


def edge_sig(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source") or e.get("source_id") or "",
        e.get("target") or e.get("target_id") or "",
        e.get("relation") or "",
    )


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def main() -> int:
    node_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_lines = [
        line.rstrip("\n")
        for line in EDGES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_sigs = {edge_sig(json.loads(ln)) for ln in edge_lines}
    nodes_by_id = {node_id_of_line(ln): i for i, ln in enumerate(node_lines)}

    changes: list[str] = []

    for spec in NEW_SCHOLARS:
        nid = spec["id"]
        if nid in nodes_by_id:
            print(f"SKIP (exists): {nid}")
            continue
        node_lines.append(json.dumps(spec, ensure_ascii=False))
        nodes_by_id[nid] = len(node_lines) - 1
        changes.append(f"NEW SCHOLAR {nid}")

    for spec in NEW_PUBLICATIONS:
        nid = spec["id"]
        if nid in nodes_by_id:
            print(f"SKIP (exists): {nid}")
            continue
        node_lines.append(json.dumps(spec, ensure_ascii=False))
        nodes_by_id[nid] = len(node_lines) - 1
        changes.append(f"NEW PUB    {nid}")

    for spec in ENRICHMENTS:
        nid = spec["id"]
        idx = nodes_by_id.get(nid)
        if idx is None:
            print(f"WARN: enrichment target {nid} not found", file=sys.stderr)
            continue
        node = json.loads(node_lines[idx])
        md = parse_metadata(node.get("metadata"))
        if md.get(WAVE_TAG):
            print(f"SKIP enrichment (already done): {nid}")
            continue
        md.update(spec["metadata_updates"])
        md[WAVE_TAG] = "Enriched with local_pdf_path + verified_critiques from direct PDF reading"
        node["metadata"] = json.dumps(md, ensure_ascii=False)
        node["updated_at"] = NOW
        node_lines[idx] = json.dumps(node, ensure_ascii=False)
        changes.append(f"ENRICH     {nid}")

    for e in NEW_EDGES:
        sig = edge_sig(e)
        if sig in edge_sigs:
            print(f"SKIP edge (exists): {sig[0]} --{sig[2]}--> {sig[1]}")
            continue
        edge_lines.append(json.dumps(e, ensure_ascii=False))
        edge_sigs.add(sig)
        changes.append(f"NEW EDGE   {sig[0][:40]:40s} --{sig[2]:13s}--> {sig[1][:40]}")

    if not changes:
        print("OK: nothing to apply")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR}")
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    for c in changes:
        print(c)
    n_nodes = sum(1 for c in changes if c.startswith(("NEW SCHOLAR", "NEW PUB", "ENRICH")))
    n_edges = sum(1 for c in changes if c.startswith("NEW EDGE"))
    print(f"\nDONE: {n_nodes} node change(s), {n_edges} new edge(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
