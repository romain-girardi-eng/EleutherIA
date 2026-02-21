"""Configuration for Sources Chrétiennes corpus import.

Contains:
- SC_CORPUS_DIR: path to the corpus directory
- WORK_REGISTRY: dict mapping filename -> scholarly metadata for all 40 source files
- Descriptions derived from INDEX.md (no LLM generation)
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Corpus location
# ---------------------------------------------------------------------------

SC_CORPUS_DIR = os.environ.get(
    "SC_CORPUS_DIR",
    "[local-path] SHAL/"
    "02_Corpus/Sources chrétiennes txt",
)

# Category subdirectories
SC_CATEGORIES = {
    "01_Peres_apostoliques": "01_Peres_apostoliques/source",
    "02_Apologistes": "02_Apologistes/source",
    "03_Origene": "03_Origene/source",
    "04_Autres": "04_Autres/source",
}

# ---------------------------------------------------------------------------
# SC Collection node (global)
# ---------------------------------------------------------------------------

SC_COLLECTION_NODE = {
    "node_id": "sources_chretiennes",
    "label": "Sources Chrétiennes (SC)",
    "type": "Source_Collection",
    "description": (
        "Bilingual critical edition series of early Christian texts, "
        "published by Éditions du Cerf, Paris (1942–). Each volume provides "
        "the original Greek or Latin text with French translation and "
        "critical apparatus."
    ),
    "metadata": {
        "publisher": "Éditions du Cerf",
        "location": "Paris",
        "founded": 1942,
        "total_volumes": "600+",
        "phase_1_volumes": [
            "SC10bis", "SC20", "SC31", "SC53bis", "SC79", "SC123",
            "SC132", "SC136", "SC147", "SC150", "SC167", "SC172",
            "SC268", "SC379", "SC464", "SC470", "SC507", "SC528",
        ],
    },
}

# ---------------------------------------------------------------------------
# Work Registry — all 40 source files
# ---------------------------------------------------------------------------

WORK_REGISTRY: dict[str, dict] = {
    # ===================================================================
    # 01_Peres_apostoliques — SC 10bis: Ignatius (7 letters)
    # ===================================================================
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Ephesiens_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_ephesios",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Ephesios",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Ephesios. "
            "Letter written en route to martyrdom in Rome, addressing "
            "the Christian community at Ephesus. Edition: P.-Th. Camelot, "
            "SC 10bis, 1958. Ignatius emphasises obedience to the bishop "
            "and unity of the Church, with implications for moral agency "
            "and voluntary submission to God's will."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Magnesiens_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_magnesios",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Magnesios",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Magnesios. "
            "Letter to the church at Magnesia on the Meander, urging "
            "submission to the bishop and warning against Judaising. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Tralliens_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_trallianos",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Trallianos",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Trallianos. "
            "Letter to the church at Tralles, emphasising Christological "
            "orthodoxy against docetism. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Romains_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_romanos",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Romanos",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Romanos. "
            "Letter imploring the Roman Christians not to prevent his "
            "martyrdom, expressing his voluntary desire for death. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958. "
            "Central text for early Christian understanding of voluntary "
            "martyrdom and the exercise of free will."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Philadelphiens_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_philadelphenos",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Philadelphenos",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Philadelphenos. "
            "Letter to the church at Philadelphia, calling for unity "
            "and warning against schism. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Smyrniotes_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_smyrnaeos",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Smyrnaeos",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Smyrnaeos. "
            "Letter to the church at Smyrna, asserting the reality of "
            "Christ's incarnation and passion against docetism. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_à_Polycarpe_livre_1_source.txt": {
        "node_id": "sc10bis_ignatius_ad_polycarpum",
        "sc_number": "10bis",
        "author": "Ignatius Antiochenus",
        "author_kg_id": None,
        "title": "Epistula ad Polycarpum",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 110-117 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Ignatius of Antioch (c. 35-117 CE), Epistula ad Polycarpum. "
            "Personal letter to Polycarp, bishop of Smyrna, with pastoral "
            "advice on church governance. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 01_Peres_apostoliques — SC 10bis: Martyrium Polycarpi
    # ===================================================================
    "SC10bis_Anonyme_Martyre_de_Polycarpe_Inscription_livre_1_source.txt": {
        "node_id": "sc10bis_martyrium_polycarpi_inscriptio",
        "sc_number": "10bis",
        "author": "Anonymus",
        "author_kg_id": None,
        "title": "Martyrium Polycarpi (Inscriptio)",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 156-167 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Anonymous, Martyrium Polycarpi (Inscriptio). "
            "Opening inscription of the account of Polycarp's martyrdom. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Anonyme_Martyre_de_Polycarpe_Martyre_de_Polycarpe_livre_1_source.txt": {
        "node_id": "sc10bis_martyrium_polycarpi",
        "sc_number": "10bis",
        "author": "Anonymus",
        "author_kg_id": None,
        "title": "Martyrium Polycarpi",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 156-167 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Anonymous, Martyrium Polycarpi. Earliest extant account of "
            "a Christian martyrdom, describing the death of Polycarp, "
            "bishop of Smyrna. Edition: P.-Th. Camelot, SC 10bis, 1958. "
            "Illustrates early Christian conceptions of voluntary martyrdom "
            "and the exercise of moral choice under persecution."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Pionius_Smyrnensis_Martyre_de_Polycarpe_Appendice_I_livre_1_source.txt": {
        "node_id": "sc10bis_martyrium_polycarpi_app1",
        "sc_number": "10bis",
        "author": "Pionius Smyrnensis",
        "author_kg_id": None,
        "title": "Martyrium Polycarpi (Appendix I)",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 250 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Pionius of Smyrna (3rd c. CE), Martyrium Polycarpi Appendix I. "
            "Later appendix to the Martyrium Polycarpi. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC10bis_Pionius_Smyrnensis_Martyre_de_Polycarpe_Appendice_II_du_manuscrit_de__livre_1_source.txt": {
        "node_id": "sc10bis_martyrium_polycarpi_app2",
        "sc_number": "10bis",
        "author": "Pionius Smyrnensis",
        "author_kg_id": None,
        "title": "Martyrium Polycarpi (Appendix II)",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 250 CE",
        "edition": "P.-Th. Camelot, 1958 (3rd ed.)",
        "sc_volume": "SC 10bis",
        "reference_format": "D",
        "description": (
            "Pionius of Smyrna (3rd c. CE), Martyrium Polycarpi Appendix II. "
            "Manuscript appendix to the Martyrium Polycarpi. "
            "Edition: P.-Th. Camelot, SC 10bis, 1958."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 01_Peres_apostoliques — SC 167, SC 172, SC 53bis
    # ===================================================================
    "SC167_Clemens_I_papa_Épître_aux_Corinthiens_livre_1_source.txt": {
        "node_id": "sc167_clemens_epistula_ad_corinthios",
        "sc_number": "167",
        "author": "Clemens Romanus",
        "author_kg_id": None,
        "title": "Epistula ad Corinthios",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 96 CE",
        "edition": "A. Jaubert",
        "sc_volume": "SC 167",
        "reference_format": "D",
        "description": (
            "Clement of Rome (fl. c. 96 CE), Epistula I ad Corinthios. "
            "Letter from the church of Rome to the church of Corinth, "
            "addressing divisions and calling for order and humility. "
            "Edition: A. Jaubert, SC 167. One of the earliest post-apostolic "
            "texts, with implications for ecclesial authority and moral "
            "exhortation."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC172_Anonyme_Épître_de_Barnabé_livre_1_source.txt": {
        "node_id": "sc172_epistula_barnabae",
        "sc_number": "172",
        "author": "Pseudo-Barnabas",
        "author_kg_id": None,
        "title": "Epistula Barnabae",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 130 CE",
        "edition": "P. Prigent and R.A. Kraft",
        "sc_volume": "SC 172",
        "reference_format": "D",
        "description": (
            "Pseudo-Barnabas (early 2nd c. CE), Epistula Barnabae. "
            "Theological treatise presenting a 'Two Ways' moral framework "
            "(Way of Light vs Way of Darkness) with strong ethical "
            "implications for free moral choice. "
            "Edition: P. Prigent and R.A. Kraft, SC 172."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC53bis_Hermas_Pasteur_dHermas_livre_1_source.txt": {
        "node_id": "sc53bis_hermas_pastor",
        "sc_number": "53bis",
        "author": "Hermas",
        "author_kg_id": None,
        "title": "Pastor Hermae",
        "language": "grc",
        "period": "Imperial",
        "school": "Apostolic Fathers",
        "date_composed": "c. 140-150 CE",
        "edition": "SC 53bis",
        "sc_volume": "SC 53bis",
        "reference_format": "D",
        "description": (
            "Hermas (mid-2nd c. CE), Pastor Hermae (Ποιμὴν τοῦ Ἑρμᾶ). "
            "Apocalyptic text composed of Visions, Mandates, and Similitudes. "
            "Edition: SC 53bis. The Mandates section contains significant "
            "discussion of the Two Spirits (good and evil angel attending "
            "each person) and the possibility of post-baptismal repentance, "
            "touching on moral agency and the capacity for moral choice."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 507 Justin
    # ===================================================================
    "SC507_Iustinus_martyr_Apologie_livre_1_source.txt": {
        "node_id": "sc507_iustinus_apologia_i",
        "sc_number": "507",
        "author": "Iustinus Martyr",
        "author_kg_id": "iustinus_martyr",
        "title": "Apologia I pro Christianis",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 150-155 CE",
        "edition": "Ch. Munier, 2006",
        "sc_volume": "SC 507",
        "reference_format": "C",
        "description": (
            "Justin Martyr (c. 100-165 CE), Apologia I pro Christianis "
            "(Ἀπολογία ὑπὲρ Χριστιανῶν). Apologetic address to Emperor "
            "Antoninus Pius, defending Christians against accusations of "
            "atheism and immorality. Edition: Ch. Munier, SC 507, 2006. "
            "Justin is among the earliest explicit defenders of human free "
            "choice (τὸ ἐφ' ἡμῖν) against Stoic fate (εἱμαρμένη), arguing "
            "that Providence and moral responsibility are compatible. "
            "Key terms: ἐφ' ἡμῖν, εἱμαρμένη, προαίρεσις, λόγος."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 528 Pseudo-Justin
    # ===================================================================
    "SC528_Pseudo-Justin_Discours_aux_Grecs_livre_1_source.txt": {
        "node_id": "sc528_pseudo_iustinus_cohortatio",
        "sc_number": "528",
        "author": "Pseudo-Iustinus",
        "author_kg_id": None,
        "title": "Cohortatio ad Graecos",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 3rd century CE",
        "edition": "B. Pouderon et al., 2009",
        "sc_volume": "SC 528",
        "reference_format": "D",  # Uses [chap.: N, par.: N], not Format C
        "description": (
            "Pseudo-Justin (3rd c. CE?), Cohortatio ad Graecos "
            "(Λόγος πρὸς Ἕλληνας). Exhortation to the Greeks to "
            "abandon pagan philosophy in favour of Christian truth. "
            "Edition: B. Pouderon et al., SC 528, 2009."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 379 Athenagoras
    # ===================================================================
    "SC379_Athenagoras_Atheniensis_Supplique_au_sujet_des_chrétiens_éd_Pouderon_livre_1_source.txt": {
        "node_id": "sc379_athenagoras_legatio",
        "sc_number": "379",
        "author": "Athenagoras Atheniensis",
        "author_kg_id": None,
        "title": "Legatio pro Christianis",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 177 CE",
        "edition": "B. Pouderon, 1992",
        "sc_volume": "SC 379",
        "reference_format": "D",  # Uses [chap.: N, par.: N] + [dédication], not Format C
        "description": (
            "Athenagoras of Athens (fl. c. 177 CE), Legatio pro Christianis "
            "(Πρεσβεία περὶ Χριστιανῶν). Apology addressed to Marcus "
            "Aurelius and Commodus, defending Christians against charges "
            "of atheism, cannibalism, and incest. "
            "Edition: B. Pouderon, SC 379, 1992. "
            "Contains significant discussion of divine providence and "
            "the relationship between monotheism, free will, and moral "
            "responsibility."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 470 Aristides
    # ===================================================================
    "SC470_Aristides_Atheniensis_Apologie_Texte_grec_livre_1_source.txt": {
        "node_id": "sc470_aristides_apologia",
        "sc_number": "470",
        "author": "Aristides Atheniensis",
        "author_kg_id": None,
        "title": "Apologia",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 125 CE",
        "edition": "B. Pouderon, M.-J. Pierre, B. Outtier, 2003",
        "sc_volume": "SC 470",
        "reference_format": "D",  # Uses [section, cap.: N, par.: N], not Format C
        "description": (
            "Aristides of Athens (fl. c. 125 CE), Apologia. "
            "One of the earliest known Christian apologies, addressed to "
            "Emperor Hadrian, presenting Christianity as the true religion. "
            "Edition: B. Pouderon, M.-J. Pierre, B. Outtier, SC 470, 2003. "
            "Greek text preserved primarily in the Barlaam and Josaphat "
            "romance."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 20 Theophilus (3 books)
    # ===================================================================
    "SC20_Theophilus_Antiochenus_Trois_livres_à_Autolycus_livre_1_source.txt": {
        "node_id": "sc20_theophilus_ad_autolycum_i",
        "sc_number": "20",
        "author": "Theophilus Antiochenus",
        "author_kg_id": None,
        "title": "Ad Autolycum I",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 180 CE",
        "edition": "G. Bardy and J. Sender, 1948",
        "sc_volume": "SC 20",
        "reference_format": "D",
        "description": (
            "Theophilus of Antioch (fl. c. 180 CE), Ad Autolycum I. "
            "First book of a three-book apology addressed to the pagan "
            "Autolycus, defending Christian monotheism and the doctrine "
            "of creation. Edition: G. Bardy and J. Sender, SC 20, 1948. "
            "Contains discussion of divine providence and free will in "
            "the context of creation theology."
        ),
        "series_prev": None,
        "series_next": "sc20_theophilus_ad_autolycum_ii",
    },
    "SC20_Theophilus_Antiochenus_Trois_livres_à_Autolycus_livre_2_source.txt": {
        "node_id": "sc20_theophilus_ad_autolycum_ii",
        "sc_number": "20",
        "author": "Theophilus Antiochenus",
        "author_kg_id": None,
        "title": "Ad Autolycum II",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 180 CE",
        "edition": "G. Bardy and J. Sender, 1948",
        "sc_volume": "SC 20",
        "reference_format": "D",
        "description": (
            "Theophilus of Antioch (fl. c. 180 CE), Ad Autolycum II. "
            "Second book, presenting a Christian cosmology based on "
            "Genesis and contrasting it with Greek mythology. "
            "Edition: G. Bardy and J. Sender, SC 20, 1948."
        ),
        "series_prev": "sc20_theophilus_ad_autolycum_i",
        "series_next": "sc20_theophilus_ad_autolycum_iii",
    },
    "SC20_Theophilus_Antiochenus_Trois_livres_à_Autolycus_livre_3_source.txt": {
        "node_id": "sc20_theophilus_ad_autolycum_iii",
        "sc_number": "20",
        "author": "Theophilus Antiochenus",
        "author_kg_id": None,
        "title": "Ad Autolycum III",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 180 CE",
        "edition": "G. Bardy and J. Sender, 1948",
        "sc_volume": "SC 20",
        "reference_format": "D",
        "description": (
            "Theophilus of Antioch (fl. c. 180 CE), Ad Autolycum III. "
            "Third book, defending the antiquity and moral superiority "
            "of the Hebrew-Christian tradition over Greek philosophy. "
            "Edition: G. Bardy and J. Sender, SC 20, 1948."
        ),
        "series_prev": "sc20_theophilus_ad_autolycum_ii",
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 123 Melito & Apollinaris
    # ===================================================================
    "SC123_Melito_Sardensis_Sur_la_Pâque_livre_1_source.txt": {
        "node_id": "sc123_melito_peri_pascha",
        "sc_number": "123",
        "author": "Melito Sardensis",
        "author_kg_id": None,
        "title": "Peri Pascha",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 160-170 CE",
        "edition": "O. Perler, 1966",
        "sc_volume": "SC 123",
        "reference_format": "D",
        "description": (
            "Melito of Sardis (fl. c. 160-170 CE), Peri Pascha "
            "(Περὶ Πάσχα). Paschal homily rediscovered in the 20th century, "
            "presenting a typological reading of the Exodus narrative. "
            "Edition: O. Perler, SC 123, 1966."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC123_Melito_Sardensis_Fragments_III_Apologie_à_Antonin_livre_1_source.txt": {
        "node_id": "sc123_melito_apologia_ad_antoninum",
        "sc_number": "123",
        "author": "Melito Sardensis",
        "author_kg_id": None,
        "title": "Apologia ad Antoninum (fragmenta III)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 170 CE",
        "edition": "O. Perler, 1966",
        "sc_volume": "SC 123",
        "reference_format": "D",
        "description": (
            "Melito of Sardis (fl. c. 160-170 CE), Apologia ad Antoninum "
            "(Fragment III). Apologetic fragment preserved in Eusebius. "
            "Edition: O. Perler, SC 123, 1966."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC123_Melito_Sardensis_Fragments_III_Eclogae_livre_1_source.txt": {
        "node_id": "sc123_melito_eclogae",
        "sc_number": "123",
        "author": "Melito Sardensis",
        "author_kg_id": None,
        "title": "Eclogae (fragmenta III)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 170 CE",
        "edition": "O. Perler, 1966",
        "sc_volume": "SC 123",
        "reference_format": "D",
        "description": (
            "Melito of Sardis (fl. c. 160-170 CE), Eclogae (Fragment III). "
            "Excerpts (Ἐκλογαί) from the Old Testament. "
            "Edition: O. Perler, SC 123, 1966."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC123_Melito_Sardensis_Fragments_XIII_Sur_lâme_et_le_corps_livre_1_source.txt": {
        "node_id": "sc123_melito_de_anima_et_corpore",
        "sc_number": "123",
        "author": "Melito Sardensis",
        "author_kg_id": None,
        "title": "De anima et corpore (fragmenta XIII)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 170 CE",
        "edition": "O. Perler, 1966",
        "sc_volume": "SC 123",
        "reference_format": "D",
        "description": (
            "Melito of Sardis (fl. c. 160-170 CE), De anima et corpore "
            "(Fragment XIII). Fragment on the soul and body. "
            "Edition: O. Perler, SC 123, 1966."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC123_Apollinaris_Hierapolitanus_Sur_la_Pâque_livre_1_source.txt": {
        "node_id": "sc123_apollinaris_peri_pascha",
        "sc_number": "123",
        "author": "Apollinaris Hierapolitanus",
        "author_kg_id": None,
        "title": "Peri Pascha (fragmenta)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 170 CE",
        "edition": "O. Perler, 1966",
        "sc_volume": "SC 123",
        "reference_format": "D",
        "description": (
            "Apollinaris of Hierapolis (fl. c. 170 CE), Peri Pascha "
            "(fragments). Fragments of a treatise on the Paschal controversy. "
            "Edition: O. Perler, SC 123, 1966."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 02_Apologistes — SC 31 Melito fragments
    # ===================================================================
    "SC31_Melito_Sardensis_Fragments_IV_Sur_la_Pâque_livre_1_source.txt": {
        "node_id": "sc31_melito_peri_pascha_iv",
        "sc_number": "31",
        "author": "Melito Sardensis",
        "author_kg_id": None,
        "title": "Peri Pascha (fragmenta IV)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Apologetics",
        "date_composed": "c. 170 CE",
        "edition": "SC 31",
        "sc_volume": "SC 31",
        "reference_format": "D",
        "description": (
            "Melito of Sardis (fl. c. 160-170 CE), Peri Pascha Fragment IV. "
            "Additional fragment from an alternative tradition of the Paschal "
            "homily. Edition: SC 31."
        ),
        "series_prev": None,
        "series_next": None,
    },
    # ===================================================================
    # 03_Origene — Contre Celse (SC 132, 136, 147, 150)
    # ===================================================================
    "SC132_Origenes_Contre_Celse_Préface_livre_1_source.txt": {
        "node_id": "sc132_origenes_contra_celsum_praef",
        "sc_number": "132",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum (Praefatio)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 132",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum, Praefatio "
            "(Κατὰ Κέλσου). Preface to the eight-book refutation of Celsus's "
            "True Doctrine (c. 178 CE). Edition: M. Borret, SC 132, 1967."
        ),
        "series_prev": None,
        "series_next": "sc132_origenes_contra_celsum_i",
    },
    "SC132_Origenes_Contre_Celse_Livre_I_livre_1_source.txt": {
        "node_id": "sc132_origenes_contra_celsum_i",
        "sc_number": "132",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum I",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 132",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum I-II "
            "(Κατὰ Κέλσου). Eight-book refutation of the Middle-Platonist "
            "philosopher Celsus's True Doctrine (c. 178 CE). "
            "Edition: M. Borret, SC 132, 136, 147, 150, 1967-1969. "
            "Contains extensive arguments about free will (αὐτεξούσιον, "
            "προαίρεσις), divine providence, and moral responsibility "
            "in response to Celsus's fatalist challenge. "
            "Key terms: αὐτεξούσιον, προαίρεσις, εἱμαρμένη."
        ),
        "series_prev": "sc132_origenes_contra_celsum_praef",
        "series_next": "sc132_origenes_contra_celsum_ii",
    },
    "SC132_Origenes_Contre_Celse_Livre_II_livre_1_source.txt": {
        "node_id": "sc132_origenes_contra_celsum_ii",
        "sc_number": "132",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum II",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 132",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum II. "
            "Second book of the refutation of Celsus. "
            "Edition: M. Borret, SC 132, 1967."
        ),
        "series_prev": "sc132_origenes_contra_celsum_i",
        "series_next": "sc136_origenes_contra_celsum_iii",
    },
    "SC136_Origenes_Contre_Celse_Livre_III_livre_1_source.txt": {
        "node_id": "sc136_origenes_contra_celsum_iii",
        "sc_number": "136",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum III",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 136",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum III. "
            "Third book of the refutation of Celsus. "
            "Edition: M. Borret, SC 136, 1968."
        ),
        "series_prev": "sc132_origenes_contra_celsum_ii",
        "series_next": "sc136_origenes_contra_celsum_iv",
    },
    "SC136_Origenes_Contre_Celse_Livre_IV_livre_1_source.txt": {
        "node_id": "sc136_origenes_contra_celsum_iv",
        "sc_number": "136",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum IV",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 136",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum IV. "
            "Fourth book of the refutation of Celsus. "
            "Edition: M. Borret, SC 136, 1968."
        ),
        "series_prev": "sc136_origenes_contra_celsum_iii",
        "series_next": "sc147_origenes_contra_celsum_v",
    },
    "SC147_Origenes_Contre_Celse_Livre_V_livre_1_source.txt": {
        "node_id": "sc147_origenes_contra_celsum_v",
        "sc_number": "147",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum V",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 147",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum V. "
            "Fifth book of the refutation of Celsus. "
            "Edition: M. Borret, SC 147, 1969."
        ),
        "series_prev": "sc136_origenes_contra_celsum_iv",
        "series_next": "sc147_origenes_contra_celsum_vi",
    },
    "SC147_Origenes_Contre_Celse_Livre_VI_livre_1_source.txt": {
        "node_id": "sc147_origenes_contra_celsum_vi",
        "sc_number": "147",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum VI",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 147",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum VI. "
            "Sixth book of the refutation of Celsus. "
            "Edition: M. Borret, SC 147, 1969."
        ),
        "series_prev": "sc147_origenes_contra_celsum_v",
        "series_next": "sc150_origenes_contra_celsum_vii",
    },
    "SC150_Origenes_Contre_Celse_Livre_VII_livre_1_source.txt": {
        "node_id": "sc150_origenes_contra_celsum_vii",
        "sc_number": "150",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum VII",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 150",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum VII. "
            "Seventh book of the refutation of Celsus. "
            "Edition: M. Borret, SC 150, 1969."
        ),
        "series_prev": "sc147_origenes_contra_celsum_vi",
        "series_next": "sc150_origenes_contra_celsum_viii",
    },
    "SC150_Origenes_Contre_Celse_Livre_VIII_livre_1_source.txt": {
        "node_id": "sc150_origenes_contra_celsum_viii",
        "sc_number": "150",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Contra Celsum VIII",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 248 CE",
        "edition": "M. Borret, 1967-1969",
        "sc_volume": "SC 150",
        "reference_format": "A",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Contra Celsum VIII. "
            "Final book of the refutation of Celsus. "
            "Edition: M. Borret, SC 150, 1969."
        ),
        "series_prev": "sc150_origenes_contra_celsum_vii",
        "series_next": None,
    },
    # ===================================================================
    # 03_Origene — Traité des Principes (SC 268)
    # ===================================================================
    "SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt": {
        "node_id": "sc268_origenes_peri_archon_iii",
        "sc_number": "268",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Peri Archon III (Excerpta graeca)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 229-230 CE",
        "edition": "H. Crouzel and M. Simonetti, 1980",
        "sc_volume": "SC 268",
        "reference_format": "B",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Peri Archon III "
            "(De Principiis III). Greek excerpts preserved in the "
            "Philocalia (ch. 21), covering Book III which is the most "
            "sustained ancient Christian treatment of free will "
            "(αὐτεξούσιον). Edition: H. Crouzel and M. Simonetti, "
            "SC 268-269, 1980. Book III chapters 1-5 contain Origen's "
            "arguments against fatalism (εἱμαρμένη), Gnostic determinism, "
            "and in defence of the autonomy of rational beings. "
            "Key terms: αὐτεξούσιον, ἐφ' ἡμῖν, εἱμαρμένη, συγκατάθεσις."
        ),
        "series_prev": None,
        "series_next": "sc268_origenes_peri_archon_iv",
    },
    "SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_4_source.txt": {
        "node_id": "sc268_origenes_peri_archon_iv",
        "sc_number": "268",
        "author": "Origenes",
        "author_kg_id": "origenes",
        "title": "Peri Archon IV (Excerpta graeca)",
        "language": "grc",
        "period": "Imperial",
        "school": "Christian Platonism",
        "date_composed": "c. 229-230 CE",
        "edition": "H. Crouzel and M. Simonetti, 1980",
        "sc_volume": "SC 268",
        "reference_format": "B",
        "description": (
            "Origen of Alexandria (c. 185-253 CE), Peri Archon IV "
            "(De Principiis IV). Greek excerpts of Book IV, on the "
            "interpretation of Scripture. Edition: H. Crouzel and "
            "M. Simonetti, SC 268-269, 1980."
        ),
        "series_prev": "sc268_origenes_peri_archon_iii",
        "series_next": None,
    },
    # ===================================================================
    # 04_Autres — SC 79 Chrysostome, SC 464 Pamphile
    # ===================================================================
    "SC79_Iohannes_Chrysostomus_Sur_la_providence_de_Dieu_contre_ceux_qui_sont_sca_livre_1_source.txt": {
        "node_id": "sc79_chrysostomus_de_providentia",
        "sc_number": "79",
        "author": "Iohannes Chrysostomus",
        "author_kg_id": None,
        "title": "Ad eos qui scandalizati sunt (De providentia Dei)",
        "language": "grc",
        "period": "Late Antiquity",
        "school": "Antiochene School",
        "date_composed": "c. 400 CE",
        "edition": "A.-M. Malingrey, 1961",
        "sc_volume": "SC 79",
        "reference_format": "D",
        "description": (
            "John Chrysostom (c. 349-407 CE), Ad eos qui scandalizati "
            "sunt (De providentia Dei). Treatise on divine providence "
            "addressed to those scandalised by the apparent prosperity "
            "of the wicked and suffering of the righteous. "
            "Edition: A.-M. Malingrey, SC 79, 1961. "
            "Central text for late antique Christian theology of "
            "providence, free will, and theodicy."
        ),
        "series_prev": None,
        "series_next": None,
    },
    "SC464_Pamphilus_Caesariensis_Apologie_pour_Origène_Paragraphe_1Paragraphe_188_livre_1_source.txt": {
        "node_id": "sc464_pamphilus_apologia_pro_origene",
        "sc_number": "464",
        "author": "Pamphilus Caesariensis",
        "author_kg_id": None,
        "title": "Apologia pro Origene",
        "language": "lat",
        "period": "Late Antiquity",
        "school": "Christian Platonism",
        "date_composed": "c. 309 CE",
        "edition": "R. Amacker and E. Junod, 2002",
        "sc_volume": "SC 464",
        "reference_format": "A",  # Uses [par.: N] like Contre Celse
        "description": (
            "Pamphilus of Caesarea (c. 240-309 CE), Apologia pro Origene. "
            "Defence of Origen's orthodoxy, composed while Pamphilus was "
            "in prison. Latin text transmitted through Rufinus of Aquileia's "
            "translation. Edition: R. Amacker and E. Junod, SC 464, 2002. "
            "Contains extensive defence of Origen's positions on free will "
            "(liberum arbitrium) and the pre-existence of souls."
        ),
        "series_prev": None,
        "series_next": None,
    },
}
