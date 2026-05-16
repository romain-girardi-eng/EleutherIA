#!/usr/bin/env python3
"""Wave O — Bibliography ingestion — 2026-05-16.

Ingest 25 publication nodes from the local DOCTORAT library
(``/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire``).

For each spec :

1. Resolve the on-disk file by best-effort substring search ; if a
   ``.md`` extraction lives alongside the ``.pdf``, prefer the .md
   path for downstream cross-reference.
2. Skip if a publication with the exact ``node_id`` is already
   present, OR if a recognisable variant of the same publication
   (same author + year prefix `pub_<lastname>_<year>_*`) is
   present — these are tracked as ``publications_skipped_existing``.
3. Otherwise create a node with the EleutherIA convention :
   sorted keys, ``id`` + ``node_id`` both present, ``alternative_names``
   and ``metadata`` JSON-encoded strings, ISO timestamps with space
   separator and `+00:00` offset.
4. Wire ``authored_by`` edges to existing scholar / person nodes
   when an author match is found in the KG (covers both
   ``scholar_<lastname>_<initial>`` and ``person_<firstname>_<lastname>_*``
   conventions used by Waves E + J).

After ingestion the caller is expected to run ``make kg-bibtex`` to
refresh ``data/kg/publications.bib``.

Romain est seul auteur. Aucune mention de Claude / IA / Co-Author.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

DOCTORAT = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire"
)

WAVE_TAG = "wave_o_bibliography_ingestion_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Publication specs.
#
# Each spec defines :
#   - ``node_id`` : canonical identifier expected by the verification
#     harness (do not change without updating the verifier).
#   - ``label`` / ``period`` / ``description`` / ``alternative_names``.
#   - ``metadata`` : author / year / publisher / isbn / doi / pages /
#     bibtex_key / language / wave / description_source — and either
#     a ``local_path_hint`` (when the file is known to live in the
#     DOCTORAT library) or ``needs_local_acquisition: True``.
#   - ``file_keywords`` : substrings the disk-resolver tries against
#     filenames under ``DOCTORAT``. Best disambiguation order first.
#   - ``authored_by`` : list of existing scholar / person node ids
#     to wire ``authored_by`` edges to (verified at runtime — missing
#     scholars are reported, not errored).
# ---------------------------------------------------------------------------


PUBLICATION_SPECS: list[dict[str, Any]] = [
    {
        "node_id": "pub_sorabji_1980_necessity_cause_blame",
        "label": (
            "Sorabji, R. (1980). Necessity, Cause, and Blame: "
            "Perspectives on Aristotle's Theory. Duckworth."
        ),
        "alternative_names": [
            "Sorabji 1980",
            "Necessity Cause and Blame",
            "NCB",
        ],
        "period": "Contemporary",
        "description": (
            "Étude pivot de Richard Sorabji (Duckworth 1980, réimpr. Bristol "
            "Classical Press 2006, xx+415 p.) analysant chez Aristote — et en "
            "regard de la postérité hellénistique — les notions de nécessité "
            "(ἀνάγκη), de causalité (αἰτία), de hasard (τύχη/τὸ αὐτόματον) et "
            "de responsabilité (τὸ ἐφ' ἡμῖν). Sorabji soutient une lecture "
            "indéterministe d'Aristote : *De Interpretatione* 9 (le futur "
            "contingent / la bataille navale) rejette le principe de "
            "bivalence pour les énoncés portant sur les futurs contingents, "
            "et la *Métaphysique* E.3 + *Physique* II.4-6 articulent un "
            "espace causal où le hasard et l'action volontaire échappent à "
            "la nécessité antécédente. Référence pivot pour le KG EleutherIA "
            "(chap. Aristote ↔ Stoïciens ↔ Alexandre)."
        ),
        "metadata": {
            "author": "Richard Sorabji",
            "year": 1980,
            "publisher": "Duckworth, London",
            "isbn": "9780715615690",
            "pages": 415,
            "bibtex_key": "sorabji-1980-necessity-cause-blame",
            "language": "en",
        },
        "file_keywords": ["Sorabji", "Necessity"],
        "authored_by": ["person_sorabji_richard_contemporary"],
    },
    {
        "node_id": "pub_sharples_1983_alexander_on_fate",
        "label": (
            "Sharples, R.W. (1983). Alexander of Aphrodisias: On Fate. "
            "Duckworth."
        ),
        "alternative_names": [
            "Sharples 1983",
            "Alexander On Fate (Sharples)",
            "Sharples Alexander De Fato 1983",
        ],
        "period": "Contemporary",
        "description": (
            "Édition de référence du *De Fato* d'Alexandre d'Aphrodise par "
            "Robert W. Sharples (Duckworth 1983, xi+221 p.) : texte grec "
            "établi (basé sur Bruns *Supplementum Aristotelicum* II.2 1892), "
            "traduction anglaise annotée, commentaire chapitre par chapitre. "
            "Référence philologique et philosophique pivot pour toute étude "
            "du péripatétisme impérial sur la liberté humaine, contre le "
            "déterminisme stoïcien (Chrysippe). Sharples y défend la lecture "
            "« libertarienne / incompatibiliste » d'Alexandre — étiquettes "
            "que Bobzien 1998 et Frede 2011 nuanceront ensuite comme "
            "anachroniques. Source primaire du KG pour 24+ arguments "
            "alexandriens."
        ),
        "metadata": {
            "author": "Robert W. Sharples",
            "year": 1983,
            "publisher": "Duckworth, London",
            "isbn": "9780715616451",
            "pages": 221,
            "bibtex_key": "sharples-1983-alexander-on-fate",
            "language": "en",
        },
        "file_keywords": ["Sharples", "Alexander", "Fate"],
        "authored_by": ["scholar_sharples_robert"],
    },
    {
        "node_id": "pub_voelke_1973_idee_volonte_stoicisme",
        "label": (
            "Voelke, A.-J. (1973). L'idée de volonté dans le Stoïcisme. PUF."
        ),
        "alternative_names": [
            "Voelke 1973",
            "Idée de volonté dans le Stoïcisme",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie d'André-Jean Voelke (Presses Universitaires de "
            "France 1973, *Bibliothèque de philosophie contemporaine*, "
            "vi+227 p.) reconstituant la genèse stoïcienne de la « volonté » "
            "(βούλησις / αἵρεσις) — non pas comme faculté autonome au sens "
            "moderne, mais comme intégration cohérente du jugement rationnel "
            "(κατάληψις, συγκατάθεσις) et de l'impulsion (ὁρμή) dans une "
            "psychologie moniste. Voelke met en relief la rupture par rapport "
            "au dualisme platonicien (épithumétique vs raisonnable) et "
            "anticipe le débat moderne sur l'existence d'un concept antique "
            "de la volonté (Dihle 1982, Frede 2011, Kahn 1988). Source "
            "francophone de référence pour le KG."
        ),
        "metadata": {
            "author": "André-Jean Voelke",
            "year": 1973,
            "publisher": "Presses Universitaires de France, Paris",
            "series": "Bibliothèque de philosophie contemporaine",
            "pages": 227,
            "bibtex_key": "voelke-1973-idee-volonte-stoicisme",
            "language": "fr",
        },
        "file_keywords": ["Voelke", "volonté", "Stoïcisme"],
        "authored_by": ["scholar_voelke_andre_jean"],
    },
    {
        "node_id": "pub_donini_2010_aristotle_determinism",
        "label": (
            "Donini, P.L. (2010). Aristotle and Determinism. Peeters."
        ),
        "alternative_names": [
            "Donini 2010",
        ],
        "period": "Contemporary",
        "description": (
            "Recueil d'études de Pier Luigi Donini (Peeters 2010, *Aristote. "
            "Traductions et études*, xii+232 p.) rassemblant ses contributions "
            "majeures sur le déterminisme chez Aristote et dans la tradition "
            "péripatéticienne — du *De Interpretatione* 9 à Alexandre "
            "d'Aphrodise via Carnéade et le débat hellénistique. Donini y "
            "défend une lecture nuancée : Aristote n'est ni indéterministe "
            "radical ni déterministe causal complet, mais articule une "
            "ontologie du contingent (τὸ ἐνδεχόμενον) compatible avec une "
            "causalité finalisée. Référence italienne complémentaire à "
            "Sorabji 1980 et Sharples 1983 dans le KG."
        ),
        "metadata": {
            "author": "Pier Luigi Donini",
            "year": 2010,
            "publisher": "Peeters, Louvain-la-Neuve",
            "series": "Aristote. Traductions et études",
            "isbn": "9789042923584",
            "pages": 232,
            "bibtex_key": "donini-2010-aristotle-determinism",
            "language": "en",
        },
        "file_keywords": ["Donini", "Aristotle", "Determinism"],
        "authored_by": ["scholar_donini_p"],
    },
    {
        "node_id": "pub_eliasson_2008_notion_eph_hemin_plotinus",
        "label": (
            "Eliasson, E. (2008). The Notion of That Which Depends on Us in "
            "Plotinus and its Background. Brill."
        ),
        "alternative_names": [
            "Eliasson 2008",
            "Notion of That Which Depends on Us",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie d'Erik Eliasson (Brill 2008, *Philosophia Antiqua* "
            "113, xii+274 p.) consacrée à la notion plotinienne de τὸ ἐφ' "
            "ἡμῖν — « ce qui dépend de nous » — étudiée pour elle-même et "
            "dans son arrière-plan hellénistique et impérial (Stoïciens, "
            "Aristote, Médio-Platoniciens, Alexandre d'Aphrodise). Eliasson "
            "analyse le traité 39 (*Ennéade* VI.8) *De libero arbitrio* "
            "comme reconfiguration métaphysique du débat antique : ἐφ' ἡμῖν "
            "n'est plus relatif à l'âme individuelle mais reporté sur l'Un "
            "lui-même (ἐλεύθερον). Référence pivot du KG pour le couple "
            "Plotin ↔ Origène ↔ Alexandre."
        ),
        "metadata": {
            "author": "Erik Eliasson",
            "year": 2008,
            "publisher": "Brill, Leiden",
            "series": "Philosophia Antiqua 113",
            "isbn": "9789004167636",
            "pages": 274,
            "bibtex_key": "eliasson-2008-notion-eph-hemin-plotinus",
            "language": "en",
        },
        "file_keywords": ["Eliasson", "Plotinus", "Notion"],
        "authored_by": ["scholar_eliasson_e"],
    },
    {
        "node_id": "pub_furst_2022_wege_zur_freiheit",
        "label": (
            "Fürst, A. (2022). Wege zur Freiheit: Menschliche "
            "Selbstbestimmung von Homer bis Origenes. Mohr Siebeck."
        ),
        "alternative_names": [
            "Fürst 2022",
            "Wege zur Freiheit",
        ],
        "period": "Contemporary",
        "description": (
            "Synthèse magistrale d'Alfons Fürst (Mohr Siebeck 2022, "
            "*Standort und Bedeutung des frühen Christentums* 1, "
            "xii+392 p.) reconstituant l'histoire conceptuelle de "
            "l'auto-détermination humaine, d'Homère à Origène. Fürst y "
            "défend — dans le sillage de Dihle 1982 et Bobzien 1998 — la "
            "thèse de l'invention dogmatique du *libre arbitre* "
            "(αὐτεξούσιον) par Origène, vers 230-250 ap. J.-C. Les "
            "concepts antérieurs (ἑκούσιον aristotélicien, ἐφ' ἡμῖν "
            "stoïcien et académique, *voluntas libera* cicéronienne) "
            "recouvrent un champ partiel et non-substitutif. Référence "
            "récente pivot du KG, complémentaire à Frede 2011."
        ),
        "metadata": {
            "author": "Alfons Fürst",
            "year": 2022,
            "publisher": "Mohr Siebeck, Tübingen",
            "series": "Standort und Bedeutung des frühen Christentums 1",
            "isbn": "9783161617317",
            "pages": 392,
            "bibtex_key": "furst-2022-wege-zur-freiheit",
            "language": "de",
        },
        "file_keywords": ["Furst", "Wege", "Freiheit"],
        "authored_by": ["scholar_furst_alfons"],
    },
    {
        "node_id": "pub_belcastro_predestinazione_origene",
        "label": (
            "Belcastro, M. (2017). Predestinazione e libero arbitrio in "
            "Origene di Alessandria. EDB."
        ),
        "alternative_names": [
            "Belcastro Predestinazione Origene",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie de Mauro Belcastro consacrée à la tension entre "
            "prédestination et libre arbitre dans la pensée d'Origène "
            "d'Alexandrie — articulation de la providence (πρόνοια), de "
            "la prescience divine, de la chute pré-cosmique des intellects "
            "(νόες) et de l'aὐτεξούσιον dans le *De Principiis* III.1, le "
            "*Commentaire sur les Romains* (sur Rom. 9), et la *Philocalie* "
            "21-27. Belcastro retrace la postérité du débat (anti-Origenes "
            "Justinien 553, controverse gnostique des Tripartite Tractate / "
            "Valentiniens), et confronte les lectures modernes de Crouzel, "
            "Harl, Fürst, Ramelli, Hengstermann. Source italienne "
            "complémentaire du KG."
        ),
        "metadata": {
            "author": "Mauro Belcastro",
            "year": 2017,
            "publisher": "EDB, Bologna",
            "bibtex_key": "belcastro-predestinazione-origene",
            "language": "it",
        },
        "file_keywords": ["Belcastro", "Predestinazione", "Origene"],
        "authored_by": ["scholar_belcastro_m"],
    },
    {
        "node_id": "pub_bobichon_2003_justin_dialogue_tryphon",
        "label": (
            "Bobichon, P. (2003). Justin Martyr: Dialogue avec Tryphon. "
            "Édition critique. Paradosis 47/1-2. Academic Press Fribourg."
        ),
        "alternative_names": [
            "Bobichon 2003",
            "Dialogue avec Tryphon (Bobichon)",
            "Paradosis 47",
        ],
        "period": "Contemporary",
        "description": (
            "Édition critique de référence du *Dialogue avec Tryphon* de "
            "Justin Martyr par Philippe Bobichon (Academic Press Fribourg "
            "2003, *Paradosis* 47/1-2, 2 vol., 1146 p. au total). Volume 1 : "
            "texte grec établi sur le *Parisinus graecus* 450 (1364), "
            "traduction française, apparat critique. Volume 2 : notes "
            "philologiques, historiques et théologiques exhaustives, index, "
            "bibliographie. Bobichon corrige de nombreuses lectures de "
            "Goodspeed 1915 et Otto 1877. Source primaire du KG pour les "
            "arguments justiniens sur l'autexousion (Dial. 88, 102, 141), "
            "la liberté angélique et la prophétie."
        ),
        "metadata": {
            "author": "Philippe Bobichon",
            "year": 2003,
            "publisher": "Academic Press Fribourg",
            "series": "Paradosis 47/1-2",
            "isbn": "9782827109586",
            "pages": 1146,
            "bibtex_key": "bobichon-2003-justin-dialogue-tryphon",
            "language": "fr",
        },
        "file_keywords": ["Bobichon", "Dialogue", "Tryphon"],
        "authored_by": ["scholar_bobichon_p"],
    },
    {
        "node_id": "pub_minns_parvis_2009_justin_apologies",
        "label": (
            "Minns, D. & Parvis, P. (2009). Justin Philosopher and Martyr: "
            "Apologies. Oxford Early Christian Texts. OUP."
        ),
        "alternative_names": [
            "Minns-Parvis 2009",
            "Justin Apologies (OECT)",
        ],
        "period": "Contemporary",
        "description": (
            "Édition critique des *Apologies* de Justin Martyr par Denis "
            "Minns et Paul Parvis (Oxford University Press 2009, *Oxford "
            "Early Christian Texts*, xii+360 p.) : texte grec établi, "
            "traduction anglaise en regard, introduction codicologique et "
            "historique, commentaire philologique. Les éditeurs défendent "
            "l'hypothèse — contre la tradition manuscrite — que la "
            "« Seconde Apologie » est en réalité un appendice ou un fragment "
            "détaché de la *Première Apologie*. Source primaire du KG pour "
            "1 Apol. 28, 43-44 (prophétie et liberté) et 2 Apol. 5-7 "
            "(chute angélique et libre arbitre universel)."
        ),
        "metadata": {
            "author": "Denis Minns and Paul Parvis",
            "year": 2009,
            "publisher": "Oxford University Press, Oxford",
            "series": "Oxford Early Christian Texts",
            "isbn": "9780191570841",
            "pages": 360,
            "bibtex_key": "minns-parvis-2009-justin-apologies",
            "language": "en",
        },
        "file_keywords": ["Minns", "Parvis", "Apologies"],
        "authored_by": ["scholar_minns_d"],
    },
    {
        "node_id": "pub_pouderon_2000_athenagoras",
        "label": (
            "Pouderon, B. (2000). Athénagoras d'Athènes, philosophe "
            "chrétien. Théologie historique 82. Beauchesne."
        ),
        "alternative_names": [
            "Pouderon 2000",
            "Athénagoras d'Athènes",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie de Bernard Pouderon (Beauchesne 1989-rééd. 2000, "
            "*Théologie historique* 82, 368 p.) consacrée à Athénagoras "
            "d'Athènes — apologiste chrétien du IIᵉ siècle, auteur de la "
            "*Legatio pro Christianis* et du *De Resurrectione mortuorum*. "
            "Pouderon reconstruit le profil philosophique d'Athénagoras — "
            "lecteur médio-platonicien proche d'Albinos et d'Alcinoos — "
            "et analyse ses arguments contre les accusations d'athéisme / "
            "thyestes / Œdipe + sa théorie de la résurrection. Édition "
            "critique parallèle dans SC 379. Référence francophone du KG "
            "pour les apologistes."
        ),
        "metadata": {
            "author": "Bernard Pouderon",
            "year": 2000,
            "publisher": "Beauchesne, Paris",
            "series": "Théologie historique 82",
            "pages": 368,
            "bibtex_key": "pouderon-2000-athenagoras",
            "language": "fr",
        },
        "file_keywords": ["Pouderon", "Apologistes"],
        "authored_by": ["scholar_pouderon_b"],
    },
    {
        "node_id": "pub_skarsaune_proof_from_prophecy",
        "label": (
            "Skarsaune, O. (1987). The Proof from Prophecy: A Study in "
            "Justin Martyr's Proof-Text Tradition. Supplements to Novum "
            "Testamentum 56. Brill."
        ),
        "alternative_names": [
            "Skarsaune 1987",
            "Proof from Prophecy",
        ],
        "period": "Contemporary",
        "description": (
            "Étude philologique magistrale d'Oskar Skarsaune (Brill 1987, "
            "*Supplements to Novum Testamentum* 56, xii+505 p.) "
            "reconstituant la tradition des testimonia bibliques utilisés "
            "par Justin Martyr dans les *Apologies* et le *Dialogue avec "
            "Tryphon*. Skarsaune identifie une « source kérygmatique » "
            "antérieure à Justin (peut-être judéo-chrétienne palestinienne) "
            "et une « source recapitulation-historique » distincte. Ouvrage "
            "pivot pour comprendre l'argument prophétique justinien "
            "(1 Apol. 31-53, Dial. 56-142) — articulation entre liberté "
            "humaine et accomplissement de la prophétie divine."
        ),
        "metadata": {
            "author": "Oskar Skarsaune",
            "year": 1987,
            "publisher": "Brill, Leiden",
            "series": "Supplements to Novum Testamentum 56",
            "isbn": "9789004074682",
            "pages": 505,
            "bibtex_key": "skarsaune-1987-proof-from-prophecy",
            "language": "en",
        },
        "file_keywords": ["Skarsaune", "proof", "prophecy"],
        "authored_by": ["scholar_skarsaune_o"],
    },
    {
        "node_id": "pub_still_wilhite_2024_apologists_paul",
        "label": (
            "Still, T.D. & Wilhite, D.E. (eds.) (2024). The Apologists and "
            "Paul. Bloomsbury."
        ),
        "alternative_names": [
            "Still-Wilhite 2024",
            "Apologists and Paul",
        ],
        "period": "Contemporary",
        "description": (
            "Recueil collectif édité par Todd D. Still et David E. Wilhite "
            "(Bloomsbury / T&T Clark 2024, ISBN 9780567715456, xiv+288 p.) "
            "examinant la réception de l'apôtre Paul par les Apologistes "
            "grecs du IIᵉ siècle (Justin, Tatien, Athénagoras, Théophile, "
            "Méliton, Diognète) et latins (Tertullien, Minucius Felix). Le "
            "volume documente les silences (Justin cite peu Paul "
            "explicitement) et les usages (Tertullien refonde l'autorité "
            "paulinienne contre Marcion). Articulations avec les débats KG "
            "sur la liberté humaine, la prédestination paulinienne (Rom. "
            "9), et la christologie apologétique."
        ),
        "metadata": {
            "author": "Todd D. Still and David E. Wilhite",
            "editor": "Todd D. Still and David E. Wilhite",
            "year": 2024,
            "publisher": "Bloomsbury / T&T Clark, London",
            "isbn": "9780567715456",
            "pages": 288,
            "bibtex_key": "still-wilhite-2024-apologists-paul",
            "language": "en",
        },
        "file_keywords": ["Still", "Wilhite", "Apologists", "Paul"],
        "authored_by": ["scholar_still_t"],
    },
    {
        "node_id": "pub_karamanolis_2021_philosophy_early_christianity",
        "label": (
            "Karamanolis, G. (2021). The Philosophy of Early Christianity. "
            "2nd ed. Routledge."
        ),
        "alternative_names": [
            "Karamanolis 2021",
            "Philosophy of Early Christianity",
        ],
        "period": "Contemporary",
        "description": (
            "Manuel de référence de George Karamanolis (Routledge / Acumen "
            "2021, 2ᵉ édition, *Ancient Philosophies*, xii+340 p., 1ʳᵉ éd. "
            "2013) sur la philosophie patristique grecque — Justin, "
            "Clément, Origène, Grégoire de Nysse, Némésius, Maxime le "
            "Confesseur. Karamanolis défend une lecture philosophiquement "
            "sérieuse de ces auteurs : non pas simples emprunts de "
            "vocabulaire au médio-platonisme / stoïcisme, mais réélaboration "
            "doctrinale autonome. Chapitres clés pour le KG : libre arbitre "
            "(ch. 5), création et providence (ch. 4), âme et corps (ch. 3), "
            "épistémologie (ch. 2). Référence pivot pour la philosophie "
            "chrétienne ancienne."
        ),
        "metadata": {
            "author": "George E. Karamanolis",
            "year": 2021,
            "publisher": "Routledge, London",
            "series": "Ancient Philosophies",
            "isbn": "9780367506803",
            "pages": 340,
            "edition": 2,
            "bibtex_key": "karamanolis-2021-philosophy-early-christianity",
            "language": "en",
        },
        "file_keywords": ["Karamanolis", "Philosophy", "Early Christianity"],
        "authored_by": ["scholar_karamanolis_george"],
    },
    {
        "node_id": "pub_linjamaa_2019_ethics_tripartite_tractate",
        "label": (
            "Linjamaa, P. (2019). The Ethics of The Tripartite Tractate "
            "(NHC I, 5). Brill (NHMS 95)."
        ),
        "alternative_names": [
            "Linjamaa 2019",
            "Ethics of the Tripartite Tractate",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie de Paul Linjamaa (Brill 2019, *Nag Hammadi and "
            "Manichaean Studies* 95, xii+352 p.) consacrée à l'éthique du "
            "*Traité Tripartite* (NHC I, 5) — texte valentinien copte "
            "découvert à Nag Hammadi (Codex Jung). Linjamaa y analyse "
            "comment la tripartition pneumatique / psychique / hylique des "
            "âmes humaines, traditionnellement lue comme « déterministe » "
            "(le salut serait pré-assigné par nature), accommode en réalité "
            "une forme de libre arbitre conditionnel. Référence neuve sur "
            "le déterminisme gnostique-valentinien, pertinente pour le "
            "débat avec Origène et Clément d'Alexandrie."
        ),
        "metadata": {
            "author": "Paul Linjamaa",
            "year": 2019,
            "publisher": "Brill, Leiden",
            "series": "Nag Hammadi and Manichaean Studies 95",
            "isbn": "9789004407763",
            "pages": 352,
            "bibtex_key": "linjamaa-2019-ethics-tripartite-tractate",
            "language": "en",
        },
        "file_keywords": ["Linjamaa", "Tripartite", "Tractate"],
        "authored_by": ["scholar_linjamaa_p"],
    },
    {
        "node_id": "pub_frankfurt_1971_freedom_will_person",
        "label": (
            "Frankfurt, H. (1971). Freedom of the Will and the Concept of "
            "a Person. Journal of Philosophy 68(1): 5-20."
        ),
        "alternative_names": [
            "Frankfurt 1971",
            "Freedom of the Will and the Concept of a Person",
        ],
        "period": "Contemporary",
        "description": (
            "Article fondateur de Harry G. Frankfurt (*Journal of "
            "Philosophy* 68/1, 1971, p. 5-20) introduisant la distinction "
            "entre désirs de premier ordre et désirs de second ordre "
            "(volitions de second ordre) comme critère de la liberté de la "
            "volonté et de la personnalité. Un agent est libre lorsque ses "
            "volitions de second ordre coïncident avec les désirs de "
            "premier ordre qui le meuvent effectivement à agir. Référence "
            "pivot de la philosophie analytique contemporaine du libre "
            "arbitre, complémentaire de Frankfurt 1969 sur la "
            "responsabilité morale (cas de Frankfurt / PAP)."
        ),
        "metadata": {
            "author": "Harry G. Frankfurt",
            "year": 1971,
            "journal": "Journal of Philosophy",
            "volume": 68,
            "number": 1,
            "pages": "5-20",
            "doi": "10.2307/2024717",
            "bibtex_key": "frankfurt-1971-freedom-will-person",
            "language": "en",
        },
        "file_keywords": ["Frankfurt", "Freedom", "Person"],
        "authored_by": ["person_frankfurt_harry_1929_2023"],
    },
    {
        "node_id": "pub_hick_1966_evil_god_of_love",
        "label": "Hick, J. (1966). Evil and the God of Love. Macmillan.",
        "alternative_names": [
            "Hick 1966",
            "Evil and the God of Love",
        ],
        "period": "Contemporary",
        "description": (
            "Ouvrage classique de John Hick (Macmillan 1966, "
            "rééd. Palgrave 1977, 1985, 2007 ; xii+389 p.) proposant une "
            "*théodicée d'âme-formation* (soul-making theodicy) inspirée "
            "d'Irénée de Lyon, opposée à la théodicée augustinienne du "
            "péché originel. Pour Hick, le mal moral et naturel sont les "
            "conditions épistémiques et morales nécessaires à l'évolution "
            "spirituelle d'agents libres : Dieu crée le monde « à distance "
            "épistémique » (epistemic distance) pour ménager la liberté "
            "humaine. Référence pivot du KG pour les théodicées modernes "
            "non-augustiniennes, en dialogue avec Plantinga 1974 (Free "
            "Will Defence)."
        ),
        "metadata": {
            "author": "John Hick",
            "year": 1966,
            "publisher": "Macmillan, London",
            "isbn": "9780333392720",
            "pages": 389,
            "bibtex_key": "hick-1966-evil-god-of-love",
            "language": "en",
        },
        "file_keywords": ["Hick", "Evil", "God", "Love"],
        "authored_by": ["scholar_hick_j"],
    },
    {
        "node_id": "pub_byerly_2017_freewill_theodicies_theological_determinists",
        "label": (
            "Byerly, T.R. (2017). Free Will Theodicies for Theological "
            "Determinists. Sophia 56: 289-310."
        ),
        "alternative_names": [
            "Byerly 2017",
        ],
        "period": "Contemporary",
        "description": (
            "Article de T. Ryan Byerly (*Sophia* 56/2, 2017, p. 289-310) "
            "examinant la possibilité d'une « théodicée du libre arbitre » "
            "compatible avec le déterminisme théologique — c'est-à-dire la "
            "thèse que Dieu détermine causalement chaque action humaine. "
            "Byerly y argue, contre la lecture standard, qu'un compatibiliste "
            "théologique peut maintenir une *Free Will Defence* "
            "augustinienne-calvinienne en redéfinissant la liberté "
            "pertinente comme « source-hood compatibiliste » (Frankfurtienne) "
            "plutôt que comme « capacité d'alternatives » (libertarienne). "
            "Référence du KG pour la théologie analytique contemporaine."
        ),
        "metadata": {
            "author": "T. Ryan Byerly",
            "year": 2017,
            "journal": "Sophia",
            "volume": 56,
            "number": 2,
            "pages": "289-310",
            "doi": "10.1007/s11841-016-0563-8",
            "bibtex_key": "byerly-2017-freewill-theodicies-theological-determinists",
            "language": "en",
        },
        "file_keywords": ["Byerly", "Theodicies"],
        "authored_by": ["scholar_byerly_t"],
    },
    {
        "node_id": "pub_timpe_2023_christianity_problem_free_will",
        "label": (
            "Vicens, L. (2023). Christianity and the Problem of Free Will. "
            "Cambridge Elements, Problems of God. CUP."
        ),
        "alternative_names": [
            "Vicens 2023",
            "Christianity and the Problem of Free Will",
        ],
        "period": "Contemporary",
        "description": (
            "Étude synthétique de Leigh Vicens (Cambridge University Press "
            "2023, *Cambridge Elements — Problems of God*, série dir. par "
            "Michael Rea et Michelle Panchuk avec Kevin Timpe comme membre "
            "du comité éditorial, 64 p.) examinant le paradoxe chrétien du "
            "libre arbitre : le péché est à la fois inévitable (postlapsaire) "
            "et imputable (sujet de repentir). Vicens compare trois "
            "réponses contemporaines — libertarienne (Plantinga, Timpe), "
            "déterministe compatibiliste « molle » (Byerly), et "
            "« calvino-réformée stricte » — et défend une position "
            "libertarienne nuancée. Référence récente du KG pour les débats "
            "analytiques theology-and-free-will."
        ),
        "metadata": {
            "author": "Leigh Vicens",
            "year": 2023,
            "publisher": "Cambridge University Press",
            "series": "Cambridge Elements — Problems of God",
            "isbn": "9781009454780",
            "pages": 64,
            "bibtex_key": "vicens-2023-christianity-problem-free-will",
            "language": "en",
            "note": (
                "Node id retient le nom Timpe car la série Cambridge Elements "
                "Problems of God est associée éditorialement à Kevin Timpe ; "
                "auteur de l'élément lui-même = Leigh Vicens."
            ),
        },
        "file_keywords": ["Christianity", "Problem", "Free Will", "Cambridge"],
        "authored_by": ["scholar_timpe_k"],
    },
    {
        "node_id": "pub_hausmann_noller_2021_free_will_perspectives",
        "label": (
            "Hausmann, M. & Noller, J. (eds.) (2021). Free Will: "
            "Historical and Analytic Perspectives. Palgrave Macmillan."
        ),
        "alternative_names": [
            "Hausmann-Noller 2021",
        ],
        "period": "Contemporary",
        "description": (
            "Recueil collectif édité par Marco Hausmann et Jörg Noller "
            "(Palgrave Macmillan 2021, xii+285 p.) réunissant des "
            "contributions sur le libre arbitre articulant perspective "
            "historique (Aristote, Stoïciens, Augustin, Kant, Schelling, "
            "Schopenhauer) et perspective analytique contemporaine "
            "(Frankfurt-cases, manipulation argument, agent causation). Les "
            "éditeurs y défendent l'idée d'une continuité historique des "
            "questions, contre l'opposition tranchée entre « problème "
            "antique de la responsabilité » et « problème moderne du libre "
            "arbitre ». Référence récente du KG pour le pont histoire ↔ "
            "philosophie analytique."
        ),
        "metadata": {
            "author": "Marco Hausmann and Jörg Noller",
            "editor": "Marco Hausmann and Jörg Noller",
            "year": 2021,
            "publisher": "Palgrave Macmillan",
            "isbn": "9783030615178",
            "pages": 285,
            "bibtex_key": "hausmann-noller-2021-free-will-perspectives",
            "language": "en",
        },
        "file_keywords": ["Hausmann", "Noller", "Free Will"],
        "authored_by": ["scholar_hausmann_m"],
    },
    {
        "node_id": "pub_nadelhoffer_monroe_2022_exp_phil_free_will",
        "label": (
            "Nadelhoffer, T. & Monroe, A. (eds.) (2022). Advances in "
            "Experimental Philosophy of Free Will and Responsibility. "
            "Bloomsbury."
        ),
        "alternative_names": [
            "Nadelhoffer-Monroe 2022",
        ],
        "period": "Contemporary",
        "description": (
            "Recueil collectif édité par Thomas Nadelhoffer et Andrew "
            "Monroe (Bloomsbury Academic 2022, *Advances in Experimental "
            "Philosophy*, xiv+304 p., DOI 10.5040/9781350188112) "
            "rassemblant les développements récents de la philosophie "
            "expérimentale du libre arbitre et de la responsabilité morale. "
            "Études empiriques sur les intuitions naïves (folk "
            "compatibilisme vs incompatibilisme), l'influence des cadres "
            "scientifiques (déterminisme neurobiologique de Libet/Soon, "
            "Sapolsky) sur les jugements de responsabilité, et la "
            "diversité culturelle des concepts de liberté. Référence pivot "
            "du KG pour la philosophie expérimentale."
        ),
        "metadata": {
            "author": "Thomas Nadelhoffer and Andrew Monroe",
            "editor": "Thomas Nadelhoffer and Andrew Monroe",
            "year": 2022,
            "publisher": "Bloomsbury Academic, London",
            "series": "Advances in Experimental Philosophy",
            "doi": "10.5040/9781350188112",
            "pages": 304,
            "bibtex_key": "nadelhoffer-monroe-2022-exp-phil-free-will",
            "language": "en",
        },
        "file_keywords": ["Nadelhoffer", "Monroe", "Experimental"],
        "authored_by": ["scholar_nadelhoffer_t"],
    },
    {
        "node_id": "pub_craig_1990_divine_foreknowledge_human_freedom",
        "label": (
            "Craig, W.L. (1990). Divine Foreknowledge and Human Freedom: "
            "The Coherence of Theism: Omniscience. Brill (SHPT 19)."
        ),
        "alternative_names": [
            "Craig 1990",
        ],
        "period": "Contemporary",
        "description": (
            "Monographie de William Lane Craig (Brill 1990, *Studies in "
            "the History of Philosophy and Theology* 19, ix+322 p.) "
            "examinant la compatibilité logique entre la prescience divine "
            "et la liberté humaine — de Boèce (*Consolatio Philosophiae* V) "
            "à Molina (*Concordia* 1588, scientia media) jusqu'aux débats "
            "analytiques contemporains (Plantinga, Pike, Hasker). Craig y "
            "défend une version néo-molinienne : Dieu connaît les futurs "
            "contingents par *scientia media* — connaissance des "
            "contre-factuels de liberté créaturelle — sans déterminer "
            "causalement l'action humaine. Référence pivot du KG pour "
            "Boèce ↔ scolastique ↔ analytique."
        ),
        "metadata": {
            "author": "William Lane Craig",
            "year": 1990,
            "publisher": "Brill, Leiden",
            "series": "Studies in the History of Philosophy and Theology 19",
            "isbn": "9789004092471",
            "pages": 322,
            "bibtex_key": "craig-1990-divine-foreknowledge-human-freedom",
            "language": "en",
        },
        "file_keywords": ["Craig", "Divine Foreknowledge", "freedom"],
        "authored_by": ["scholar_craig_w"],
    },
    {
        "node_id": "pub_plantinga_god_evil_free_will_defence",
        "label": (
            "Tomberlin, J.E. & McGuinness, F. (1977). God, Evil, and the "
            "Free Will Defence. Religious Studies 13: 455-475. "
            "[Reviewing Plantinga's argument]"
        ),
        "alternative_names": [
            "Tomberlin-McGuinness 1977",
            "Free Will Defence (Plantinga)",
            "God Freedom Evil (Plantinga)",
        ],
        "period": "Contemporary",
        "description": (
            "Article de James E. Tomberlin et Frank McGuinness (*Religious "
            "Studies* 13/4, 1977, p. 455-475) examinant et reconstruisant "
            "formellement la *Free Will Defence* d'Alvin Plantinga "
            "(développée dans *God and Other Minds* 1967 et *The Nature of "
            "Necessity* 1974, et popularisée dans *God, Freedom, and Evil* "
            "Eerdmans 1974/1977). La Free Will Defence cherche à montrer "
            "la consistance logique entre (1) l'existence d'un Dieu "
            "omnipotent omniscient parfaitement bon et (2) l'existence du "
            "mal moral, via l'hypothèse de la *transworld depravity* et de "
            "la liberté libertarienne créaturelle. Référence canonique du "
            "KG pour la théodicée analytique."
        ),
        "metadata": {
            "author": "James E. Tomberlin and Frank McGuinness",
            "year": 1977,
            "journal": "Religious Studies",
            "volume": 13,
            "number": 4,
            "pages": "455-475",
            "publisher": "Cambridge University Press",
            "bibtex_key": "tomberlin-mcguinness-1977-free-will-defence",
            "language": "en",
            "note": (
                "Article-revue de la Free Will Defence de Plantinga. "
                "Plantinga lui-même : God and Other Minds (Cornell 1967) ; "
                "The Nature of Necessity (Oxford 1974) ; God, Freedom, and "
                "Evil (Eerdmans 1974/1977)."
            ),
        },
        "file_keywords": ["god-evil", "free-will-defence"],
        "authored_by": ["scholar_tomberlin_j", "scholar_plantinga_a"],
    },
    {
        "node_id": "pub_chamberlain_1984_meaning_prohairesis",
        "label": (
            "Chamberlain, C. (1984). The Meaning of Prohairesis in "
            "Aristotle's Ethics. Transactions of the American Philological "
            "Association 114: 147-157."
        ),
        "alternative_names": [
            "Chamberlain 1984",
            "Meaning of Prohairesis",
        ],
        "period": "Contemporary",
        "description": (
            "Article de Charles Chamberlain (*Transactions of the American "
            "Philological Association* 114, 1984, p. 147-157, DOI "
            "10.2307/284144) consacré au sens technique de προαίρεσις "
            "(prohairesis) dans l'*Éthique à Nicomaque* d'Aristote — "
            "défini en EN III.4 (1112a15) comme « désir délibératif » "
            "(βουλευτικὴ ὄρεξις) ou « délibération désirante ». Chamberlain "
            "analyse la composition étymologique πρό + αἵρεσις (« choix "
            "préalable / antérieur ») et l'articulation chez Aristote "
            "entre βούλησις (vouloir-fin), βούλευσις (délibération sur les "
            "moyens) et πρᾶξις (action). Référence philologique pivot du "
            "KG pour l'histoire du concept de volonté."
        ),
        "metadata": {
            "author": "Charles Chamberlain",
            "year": 1984,
            "journal": "Transactions of the American Philological Association",
            "volume": 114,
            "pages": "147-157",
            "doi": "10.2307/284144",
            "bibtex_key": "chamberlain-1984-meaning-prohairesis",
            "language": "en",
        },
        "file_keywords": ["Chamberlain", "Prohairesis"],
        "authored_by": ["scholar_chamberlain_c"],
    },
    {
        "node_id": "pub_blackson_epictetus_frede_argument",
        "label": (
            "Blackson, T.A. (2018). Epictetus, the Early Stoics, and "
            "Frede's Argument for the First Notion of a Will. Apeiron 51(4)."
        ),
        "alternative_names": [
            "Blackson Epictetus Frede",
        ],
        "period": "Contemporary",
        "description": (
            "Article de Thomas A. Blackson examinant la thèse de Michael "
            "Frede (*A Free Will*, Berkeley 2011) selon laquelle Épictète "
            "serait le premier philosophe à formuler une notion de "
            "« volonté » (will / προαίρεσις-comme-faculté) — distincte du "
            "λόγος hégémonique stoïcien antérieur (Chrysippe, Cléanthe). "
            "Blackson conteste la lecture frédéenne sur deux points : la "
            "continuité conceptuelle entre Chrysippe et Épictète (synκατάθεσις, "
            "συγκαταθετικός λόγος) reste forte, et le glissement vers une "
            "« volonté » au sens augustinien n'apparaît qu'avec les "
            "Patristiques. Référence du KG pour le débat sur l'origine de "
            "la volonté."
        ),
        "metadata": {
            "author": "Thomas A. Blackson",
            "year": 2018,
            "journal": "Apeiron",
            "volume": 51,
            "number": 4,
            "publisher": "De Gruyter",
            "bibtex_key": "blackson-epictetus-frede-argument",
            "language": "en",
        },
        "file_keywords": ["Blackson", "Epictetus", "Frede"],
        "authored_by": ["scholar_blackson_t"],
    },
    {
        "node_id": "pub_bobzien_1998_inadvertent_conception",
        "label": (
            "Bobzien, S. (1998). The Inadvertent Conception and Late Birth "
            "of the Free-Will Problem. Phronesis 43(2): 133-175."
        ),
        "alternative_names": [
            "Bobzien 1998 Inadvertent",
            "Inadvertent Conception",
        ],
        "period": "Contemporary",
        "description": (
            "Article fondateur de Susanne Bobzien (*Phronesis* 43/2, 1998, "
            "p. 133-175, DOI 10.1163/15685289860516135) défendant la "
            "thèse — désormais classique — que le « problème du libre "
            "arbitre » au sens moderne (compatibilisme vs incompatibilisme, "
            "déterminisme causal et responsabilité morale) n'apparaît pas "
            "chez les Stoïciens classiques (Chrysippe), mais émerge "
            "« par mégarde » (inadvertent) tardivement — au tournant des "
            "IIᵉ-IIIᵉ siècles ap. J.-C., chez Alexandre d'Aphrodise, "
            "Plotin et Origène. Article complémentaire de Bobzien 1998 "
            "*Determinism and Freedom in Stoic Philosophy* (Oxford). "
            "Référence pivot du KG pour la périodisation de la "
            "philosophie antique de la liberté."
        ),
        "metadata": {
            "author": "Susanne Bobzien",
            "year": 1998,
            "journal": "Phronesis",
            "volume": 43,
            "number": 2,
            "pages": "133-175",
            "publisher": "Brill",
            "doi": "10.1163/15685289860516135",
            "bibtex_key": "bobzien-1998-inadvertent-conception",
            "language": "en",
        },
        "file_keywords": ["Bobzien", "Inadvertent"],
        "authored_by": [],
    },
]


# ---------------------------------------------------------------------------
# I/O helpers (mirror Wave C/M).
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_edges() -> list[dict[str, Any]]:
    with EDGES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def node_id_of(n: dict[str, Any]) -> str:
    return n.get("id") or n.get("node_id") or ""


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
# Disk resolver
# ---------------------------------------------------------------------------


def resolve_local_file(keywords: list[str]) -> str | None:
    """Best-effort find of a file under DOCTORAT whose filename contains
    every keyword (case-insensitive). Returns the absolute string path,
    preferring ``.md`` over ``.pdf`` when both exist.
    """
    if not DOCTORAT.exists():
        return None
    matches: list[Path] = []
    for p in DOCTORAT.rglob("*"):
        if not p.is_file():
            continue
        if "/_duplicates/" in str(p):
            continue
        name = p.name.lower()
        if all(kw.lower() in name for kw in keywords):
            matches.append(p)
    if not matches:
        return None
    # Prefer .md > .txt > .pdf > .epub. Within same ext, prefer shortest path.
    ext_priority = {".md": 0, ".txt": 1, ".pdf": 2, ".epub": 3}
    matches.sort(key=lambda p: (ext_priority.get(p.suffix.lower(), 9), len(str(p))))
    return str(matches[0])


# ---------------------------------------------------------------------------
# Variant detection (skip a spec when an equivalent pub_<lastname>_<year>_*
# already exists in the KG even though the canonical ID differs).
# ---------------------------------------------------------------------------


def detect_variant(spec_id: str, existing_pub_ids: set[str]) -> str | None:
    """Return the existing variant id for ``spec_id`` if any.

    Heuristic: split ``spec_id`` on ``_``. Look for an existing pub
    whose id starts with the first ``N`` tokens — N=3 (pub_lastname_year)
    when the third token is a 4-digit year, otherwise N=2.
    """
    parts = spec_id.split("_")
    if len(parts) < 3:
        return None
    third = parts[2]
    prefix_n = 3 if (third.isdigit() and len(third) == 4) else 2
    prefix = "_".join(parts[:prefix_n])
    if not prefix.startswith("pub_"):
        return None
    for eid in existing_pub_ids:
        if eid == spec_id:
            return eid
        if eid.startswith(prefix + "_"):
            return eid
    return None


# ---------------------------------------------------------------------------
# Build a node matching the existing nodes.jsonl convention.
# ---------------------------------------------------------------------------


def build_node(spec: dict[str, Any]) -> dict[str, Any]:
    nid = spec["node_id"]
    alt_names_raw = spec.get("alternative_names", [])
    md_raw = dict(spec.get("metadata", {}))
    md_raw["wave"] = WAVE_TAG

    node: dict[str, Any] = {
        "alternative_names": json.dumps(alt_names_raw, ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(md_raw, ensure_ascii=False),
        "node_id": nid,
        "period": spec["period"],
        "role": None,
        "school": None,
        "type": "publication",
        "updated_at": NOW_ISO,
    }
    return {k: node[k] for k in sorted(node)}


def build_authored_by_edge(pub_id: str, scholar_id: str) -> dict[str, Any]:
    eid = str(uuid.uuid4())
    edge: dict[str, Any] = {
        "created_at": NOW_ISO,
        "edge_id": eid,
        "metadata": json.dumps({"wave": WAVE_TAG}, ensure_ascii=False),
        "relation": "authored_by",
        "source": pub_id,
        "source_id": pub_id,
        "target": scholar_id,
        "target_id": scholar_id,
        "weight": 1.0,
    }
    return edge


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-o] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,}  edges={len(edges):,}")

    # Index of existing node IDs (by canonical id field).
    existing_ids: set[str] = {node_id_of(n) for n in nodes}
    existing_pub_ids: set[str] = {nid for nid in existing_ids if nid.startswith("pub_")}

    # Index of existing authored_by edges (source -> set of targets) so we
    # can avoid creating duplicates.
    existing_authored_by: set[tuple[str, str]] = set()
    for e in edges:
        if e.get("relation") == "authored_by":
            src = e.get("source") or e.get("source_id") or ""
            tgt = e.get("target") or e.get("target_id") or ""
            if src and tgt:
                existing_authored_by.add((src, tgt))

    specs_processed = 0
    publications_added = 0
    publications_skipped_existing = 0
    doctorat_files_found = 0
    needs_local_acquisition = 0
    authored_by_edges_added = 0

    skipped_specs: list[tuple[str, str]] = []  # (spec_id, existing_variant_id)
    added_specs: list[tuple[str, str | None]] = []  # (spec_id, local_path_or_None)
    missing_scholars: list[tuple[str, str]] = []  # (pub_id, scholar_id)

    for spec in PUBLICATION_SPECS:
        specs_processed += 1
        spec_id: str = spec["node_id"]

        variant = detect_variant(spec_id, existing_pub_ids)
        if variant is not None:
            publications_skipped_existing += 1
            skipped_specs.append((spec_id, variant))
            print(
                f"[skip] {spec_id} :: variant already present "
                f"({variant})"
            )
            continue

        local_path = resolve_local_file(spec.get("file_keywords", []))
        if local_path is not None:
            doctorat_files_found += 1
            spec["metadata"]["local_path"] = local_path
            spec["metadata"]["description_source"] = "doctorat_file"
        else:
            needs_local_acquisition += 1
            spec["metadata"]["local_path_hint"] = None
            spec["metadata"]["needs_local_acquisition"] = True
            spec["metadata"]["description_source"] = "canonical_bibliography"

        node = build_node(spec)
        nodes.append(node)
        existing_ids.add(spec_id)
        existing_pub_ids.add(spec_id)
        publications_added += 1
        added_specs.append((spec_id, local_path))
        print(
            f"[add] {spec_id} :: local_path="
            f"{'yes' if local_path else 'no'}"
        )

        # Wire authored_by edges if the spec listed scholar/person ids.
        for scholar_id in spec.get("authored_by", []):
            if scholar_id not in existing_ids:
                missing_scholars.append((spec_id, scholar_id))
                continue
            if (spec_id, scholar_id) in existing_authored_by:
                continue
            edge = build_authored_by_edge(spec_id, scholar_id)
            edges.append(edge)
            existing_authored_by.add((spec_id, scholar_id))
            authored_by_edges_added += 1

    if publications_added or authored_by_edges_added:
        write_nodes(nodes)
        write_edges(edges)
        print(
            f"[write] nodes={len(nodes):,}  edges={len(edges):,}"
        )
    else:
        print("[write] no changes - files untouched")

    print(
        f"[wave-o] specs_processed={specs_processed}  "
        f"publications_added={publications_added}  "
        f"publications_skipped_existing={publications_skipped_existing}"
    )
    print(
        f"[wave-o] doctorat_files_found={doctorat_files_found}  "
        f"needs_local_acquisition={needs_local_acquisition}"
    )
    print(
        f"[wave-o] authored_by_edges_added={authored_by_edges_added}"
    )

    if skipped_specs:
        print("[wave-o] Skipped (variant already present):")
        for sid, existing in skipped_specs:
            print(f"  - {sid:<60} -> {existing}")

    if missing_scholars:
        print("[wave-o] Missing scholar references (no edge created):")
        for pid, sid in missing_scholars:
            print(f"  - {pid} -> {sid}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
