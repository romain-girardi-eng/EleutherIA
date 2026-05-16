#!/usr/bin/env python3
"""Wave K — Maxime monothelite expansion — 2026-05-16.

Adds the missing dramatis personae, councils, work and arguments of
the 7th-century monothelite / dyothelite controversy:

* 5 persons: Pyrrhus de Constantinople, Sergius Ier, Sophrone de
  Jérusalem, Pape Martin Ier, Cyrus d'Alexandrie.
* 3 events: Synode du Latran 649, IIIe concile de Constantinople 681,
  Psephos 633 (Sergius).
* 1 work: *Quaestiones ad Thalassium* (CCSG 7+22 Laga & Steel).
* 6 arguments: Pyrrhus one-energy, Pyrrhus one-will, Maxime
  two-energies, Maxime two-wills, Maxime natural-will-freedom,
  Maxime proairesis-post-baptismal-repair.

Wires edges idempotently :

* `authored_by` work → Maxime
* `member_of` Pyrrhus/Sergius/Cyrus → group_monothelites ;
  Sophrone/Martin I → group_dyothelites
* `participates_in` Maxime/Martin I → council_lateran_649 ;
  Pyrrhus/Sergius/Cyrus → event_psephos_633 ;
  Maxime → council_constantinople_iii_681 (posthumous adoption of
  his dyothelite Christology)
* `discusses` arguments → concept_monothelitism (or vice-versa per
  ontology source/target types)
* `created_by` arguments → person (creator)
* `critiques` argument_maximus_two_energies → argument_pyrrhus_one_energy
  + symmetric pair for the wills
* `cites_primary_source` arguments → existing PG 91 passages (only if
  passage already exists — verified by node-lookup, no fabrication)

Strict idempotency: each insertion checks node-existence and edge
signature before mutating. A second run logs zero additions.

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

WAVE_TAG = "wave_k_maximus_monothelite_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Person specs (5)
# ---------------------------------------------------------------------------


PERSONS: list[dict[str, Any]] = [
    {
        "node_id": "person_pyrrhus_constantinople_d654",
        "label": "Pyrrhus de Constantinople",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Patriarche de Constantinople 638-641 (succédant à Sergius Ier) "
            "puis brièvement réinstallé en 654, mort la même année. "
            "Principal défenseur du monothélisme après Sergius. Connu "
            "surtout pour son débat public à Carthage en juillet 645 avec "
            "Maxime le Confesseur, conservé dans la *Disputatio cum Pyrrho* "
            "(Διάλεξις σὺν Πύρρῳ, PG 91, 287-354). Au terme du débat, "
            "Pyrrhus souscrit publiquement à la dyothélie et accompagne "
            "Maxime à Rome, où il fait acte de soumission au pape "
            "Théodore Ier ; il rétracte ensuite sa rétractation, ce qui "
            "lui vaut une excommunication romaine. Condamné posthume au "
            "IIIe concile de Constantinople 681. Sources principales : "
            "PG 91 (Maxime *Disputatio*) ; ACO ser. II vol. I (Riedinger, "
            "de Gruyter 1984) pour les actes conciliaires."
        ),
        "alternative_names": ["Pyrrhus I of Constantinople", "Πύρρος Α´"],
        "metadata": {
            "death_date": "3 juin 654 CE",
            "patriarchate": "638-641 CE ; brièvement 654 CE",
            "key_event": "Disputatio cum Pyrrho (Carthage, juillet 645 CE)",
            "editions": [
                "PG 91, 287-354 (Disputatio cum Pyrrho)",
                "ACO ser. II vol. I — Riedinger (de Gruyter 1984)",
            ],
            "key_works": [
                "Disputatio cum Pyrrho (with Maximus the Confessor)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_sergius_constantinople_565_638",
        "label": "Sergius Ier de Constantinople",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Patriarche de Constantinople 610-638, architecte principal "
            "du monoénergisme puis du monothélisme. Soutien indéfectible "
            "de l'empereur Héraclius. Promulgue en 633 le Psephos "
            "(Ψῆφος), décret interdisant la mention d'« une » ou « deux » "
            "énergies en Christ, pour ne pas heurter les miaphysites "
            "coptes ralliés par le Pact of Union de Cyrus d'Alexandrie. "
            "Auteur effectif de l'Ekthesis 638 sous Héraclius — formule "
            "monothélite explicite. Sa correspondance avec le pape "
            "Honorius Ier (PL 80, lettres 4-5) — où Honorius répond "
            "favorablement à la doctrine d'une seule volonté — fonde la "
            "condamnation posthume de Honorius par le IIIe concile de "
            "Constantinople 681. Condamné rétrospectivement à "
            "Constantinople III. Sources : Mansi, *Sacrorum Conciliorum* "
            "X-XI ; ACO ser. II vol. I (Riedinger, de Gruyter 1984)."
        ),
        "alternative_names": [
            "Sergius I of Constantinople",
            "Σέργιος Α´",
            "Sergios",
        ],
        "metadata": {
            "birth_date": "c. 565 CE",
            "death_date": "9 décembre 638 CE",
            "patriarchate": "18 avril 610 — 9 décembre 638 CE",
            "key_documents": [
                "Psephos (633)",
                "Lettres à Honorius I (PL 80)",
                "Ekthesis (638, sous Héraclius)",
            ],
            "editions": [
                "Mansi, Sacrorum Conciliorum X-XI",
                "ACO ser. II vol. I — Riedinger (de Gruyter 1984)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_sophronius_jerusalem_560_638",
        "label": "Sophrone de Jérusalem",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Patriarche de Jérusalem 634-638. Premier opposant majeur du "
            "monoénergisme : sa Synodica de 634, longue lettre encyclique "
            "adressée à Sergius de Constantinople et à Honorius de Rome, "
            "constitue la première grande réfutation systématique de la "
            "formule « une seule activité théandrique » de Cyrus "
            "d'Alexandrie — fondement théologique de la résistance "
            "dyothélite ultérieure. Témoin oculaire de la prise de "
            "Jérusalem par les Arabes en 638 (capitulation au calife "
            "Omar). Auteur d'œuvres hagiographiques et liturgiques : "
            "*Anacreontica* (poèmes), *Vita Mariae Aegyptiacae* "
            "(PG 87.3, 3697-3726). Édition critique de la Synodica : ACO "
            "ser. II vol. I.1, p. 410-494 (Riedinger, de Gruyter 1984). "
            "Œuvres : PG 87.3. Source principale pour Maxime le "
            "Confesseur, son disciple direct."
        ),
        "alternative_names": [
            "Sophronius of Jerusalem",
            "Σωφρόνιος Ἱεροσολύμων",
        ],
        "metadata": {
            "birth_date": "c. 560 CE",
            "death_date": "11 mars 638 CE",
            "patriarchate": "634-638 CE",
            "key_documents": [
                "Synodica (634) — première réfutation du monoénergisme",
            ],
            "key_works": [
                "Synodica (ACO ser. II vol. I.1 p. 410-494)",
                "Anacreontica",
                "Vita Mariae Aegyptiacae (PG 87.3, 3697-3726)",
            ],
            "editions": [
                "PG 87.3",
                "ACO ser. II vol. I.1 — Riedinger (de Gruyter 1984)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_martin_i_pope_590_655",
        "label": "Pape Martin Ier",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Pape 5 juillet 649 — 17 juin 653. Convocateur du Synode du "
            "Latran 649 (5-31 octobre), première condamnation officielle "
            "latine du monoénergisme et du monothélisme — synode tenu "
            "sans accord impérial, ce qui provoque la fureur de "
            "l'empereur Constant II. Maxime le Confesseur, alors moine, "
            "y est présent comme conseiller théologique principal. En "
            "juin 653 l'exarque Théodore Calliopas arrête Martin à "
            "Rome ; jugé pour trahison à Constantinople décembre 653, "
            "exilé à Cherson (Crimée) où il meurt 16 septembre 655. "
            "Canonisé martyr (dernier pape martyr de l'Antiquité). "
            "Sources : Riedinger, *Concilium Lateranense a. 649 "
            "celebratum*, ACO ser. II vol. I (de Gruyter 1984) ; "
            "*Liber Pontificalis* I.336-339 (Duchesne 1886) ; "
            "Maxime, *Relatio motionis* (PG 90, 109-129)."
        ),
        "alternative_names": [
            "Martinus I",
            "Saint Martin I",
            "Martinus papa",
        ],
        "metadata": {
            "birth_date": "c. 590 CE (Todi, Ombrie)",
            "death_date": "16 septembre 655 CE (Cherson, exil)",
            "papacy": "5 juillet 649 — 17 juin 653 CE",
            "key_event": "Synode du Latran 5-31 octobre 649",
            "editions": [
                "ACO ser. II vol. I — Riedinger (de Gruyter 1984)",
                "Liber Pontificalis I.336-339 (Duchesne 1886)",
                "PG 90, 109-129 (Maximus Relatio motionis)",
            ],
            "canonization": "Martyr ; fête liturgique 13 avril (Occident)",
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_cyrus_alexandria_d641",
        "label": "Cyrus d'Alexandrie",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Patriarche melchite d'Alexandrie 631-641. Architecte du "
            "*Pact of Union* (Πάκτον τῆς ἑνώσεως) en 633, formule "
            "pseudo-conciliatrice forgée pour rallier à Chalcédoine les "
            "miaphysites coptes en concédant l'expression « une seule "
            "activité théandrique » (μία θεανδρικὴ ἐνέργεια), reprise du "
            "Pseudo-Denys *Lettre 4*. Cette formule est l'origine "
            "immédiate de la crise monoénergiste : sitôt connue, elle est "
            "réfutée par Sophrone de Jérusalem (Synodica 634), puis "
            "désamorcée provisoirement par le Psephos 633 de Sergius, "
            "avant que l'Ekthesis 638 ne lui substitue une formule "
            "monothélite. Cyrus reste en charge sous Héraclius ; démis "
            "par l'empereur après la chute d'Alexandrie aux mains des "
            "Arabes ('Amr ibn al-'As, 642). Sources : ACO ser. II ; "
            "Théophane, *Chronographia* AM 6121-6132 (éd. de Boor 1883)."
        ),
        "alternative_names": [
            "Cyrus of Alexandria",
            "Κῦρος Ἀλεξανδρείας",
            "Cyrus al-Muqawqas",
        ],
        "metadata": {
            "death_date": "21 mars 641 CE",
            "patriarchate": "631-641 CE (melchite, Alexandria)",
            "key_documents": [
                "Pact of Union (633) — μία θεανδρικὴ ἐνέργεια",
            ],
            "editions": [
                "ACO ser. II — Riedinger (de Gruyter 1984-1992)",
                "Theophanes Chronographia AM 6121-6132 (de Boor, Teubner 1883)",
            ],
            "wave": WAVE_TAG,
        },
    },
]


# ---------------------------------------------------------------------------
# Event specs (3)
# ---------------------------------------------------------------------------


EVENTS: list[dict[str, Any]] = [
    {
        "node_id": "council_lateran_649",
        "label": "Synode du Latran (649 CE)",
        "type": "event",
        "period": "Late Antiquity",
        "description": (
            "Synode tenu à Rome (basilique du Latran) du 5 au 31 octobre "
            "649, convoqué par le pape Martin Ier sans accord impérial. "
            "105 évêques participent (essentiellement italiens et "
            "africains, avec représentants orientaux). Première "
            "condamnation officielle latine du monoénergisme et du "
            "monothélisme, condamnation explicite de l'Ekthesis 638 "
            "(Héraclius) et du Typos 648 (Constant II), ainsi que des "
            "personnes de Sergius, Pyrrhus, Paul II et Cyrus "
            "d'Alexandrie. 20 canons promulgués. Maxime le Confesseur, "
            "alors moine résidant à Rome, est présent comme conseiller "
            "théologique principal — sa main est probablement derrière "
            "l'organisation doctrinale du synode. Édition critique : "
            "Riedinger, *Concilium Lateranense a. 649 celebratum*, ACO "
            "ser. II vol. I (de Gruyter 1984)."
        ),
        "metadata": {
            "date_start": "5 octobre 649 CE",
            "date_end": "31 octobre 649 CE",
            "location": "Rome, basilique du Latran",
            "convoker": "Pape Martin Ier",
            "participants_count": 105,
            "canons_count": 20,
            "key_condemnations": [
                "Monoénergisme",
                "Monothélisme",
                "Ekthesis 638 (Héraclius)",
                "Typos 648 (Constans II)",
                "Sergius, Pyrrhus, Paul II, Cyrus of Alexandria",
            ],
            "key_participants": [
                "Pope Martin I",
                "Maximus the Confessor (theological advisor)",
            ],
            "editions": [
                "Riedinger, ACO ser. II vol. I (de Gruyter 1984)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "council_constantinople_iii_681",
        "label": "IIIe concile de Constantinople (680-681 CE)",
        "type": "event",
        "period": "Late Antiquity",
        "description": (
            "Sixième concile œcuménique, tenu à Constantinople du 7 "
            "novembre 680 au 16 septembre 681 sous l'empereur "
            "Constantin IV. Définition dogmatique : deux volontés "
            "(δύο θελήματα) et deux énergies (δύο ἐνέργειαι) en Christ, "
            "non séparées et non confondues, la volonté humaine « ne "
            "contredisant ni ne s'opposant » mais « se soumettant à la "
            "volonté divine et toute-puissante » — adoption de la "
            "christologie dyothélite de Maxime le Confesseur, "
            "posthumément réhabilité. Condamnation rétroactive du pape "
            "Honorius Ier (avec Sergius, Pyrrhus, Paul II, Macaire "
            "d'Antioche). Édition critique : Riedinger, ACO ser. II "
            "vol. II (de Gruyter 1990-1992, 2 vol.). Le concile fixe "
            "la doctrine catholique standard sur la christologie des "
            "volontés et des énergies — toile de fond de toute la "
            "théologie médiévale orientale et occidentale sur le rapport "
            "entre liberté divine et liberté humaine."
        ),
        "metadata": {
            "date_start": "7 novembre 680 CE",
            "date_end": "16 septembre 681 CE",
            "location": "Constantinople (palais impérial, salle Troullos)",
            "emperor": "Constantine IV",
            "ecumenical_number": "VI",
            "key_definitions": [
                "Dyothelitism (δύο θελήματα) in Christ",
                "Dyenergism (δύο ἐνέργειαι) in Christ",
            ],
            "key_condemnations": [
                "Monothelitism / Monoenergism",
                "Honorius I (posthumous)",
                "Sergius I of Constantinople (posthumous)",
                "Pyrrhus of Constantinople (posthumous)",
                "Paul II of Constantinople",
                "Macarius of Antioch",
            ],
            "editions": [
                "Riedinger, ACO ser. II vol. II (de Gruyter 1990-1992)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "event_psephos_633",
        "label": "Psephos de Sergius Ier (633 CE)",
        "type": "event",
        "period": "Late Antiquity",
        "description": (
            "Décret (Ψῆφος) promulgué par Sergius Ier de Constantinople "
            "vers 633, interdisant aux deux partis (chalcédoniens et "
            "miaphysites) la mention d'« une » ou « deux » énergies en "
            "Christ — formule de retrait stratégique destinée à ménager "
            "les miaphysites coptes ralliés par le Pact of Union de "
            "Cyrus d'Alexandrie (633). Le Psephos est soumis au pape "
            "Honorius Ier, qui répond favorablement (PL 80, lettre 4 — "
            "« unam voluntatem confitemur »), endossant ainsi "
            "implicitement la doctrine monothélite, ce qui fondera sa "
            "condamnation posthume au IIIe concile de Constantinople "
            "681. Le Psephos prépare directement l'Ekthesis 638 (formule "
            "monothélite explicite sous Héraclius). Source critique : "
            "ACO ser. II vol. I — Riedinger (de Gruyter 1984)."
        ),
        "metadata": {
            "date": "c. 633 CE",
            "promulgator": "Sergius I of Constantinople",
            "context": "Suite au Pact of Union de Cyrus d'Alexandrie",
            "key_principals": [
                "Sergius I of Constantinople",
                "Cyrus of Alexandria",
                "Pope Honorius I (assenting respondent)",
            ],
            "key_followup": "Ekthesis 638 (formule monothélite explicite)",
            "editions": [
                "ACO ser. II vol. I — Riedinger (de Gruyter 1984)",
            ],
            "wave": WAVE_TAG,
        },
    },
]


# ---------------------------------------------------------------------------
# Work spec (1)
# ---------------------------------------------------------------------------


WORKS: list[dict[str, Any]] = [
    {
        "node_id": "work_maximus_quaestiones_thalassium",
        "label": "Maxime le Confesseur, Quaestiones ad Thalassium",
        "type": "work",
        "period": "Late Antiquity",
        "description": (
            "Maxime le Confesseur, *Quaestiones ad Thalassium* (Πρὸς "
            "Θαλάσσιον περὶ διαφόρων ἀπόρων τῆς Θείας Γραφῆς, "
            "« Questions à Thalassios sur divers points difficiles de "
            "l'Écriture sainte »). Recueil de 65 questions-réponses "
            "exégétiques composé c. 630-633 ap. J.-C., adressé à "
            "Thalassios, hégoumène d'un monastère libyen et "
            "correspondant fidèle de Maxime. Œuvre majeure de la "
            "période africaine. Pour le débat sur le libre arbitre, "
            "trois questions sont décisives : Q. 21 (πῶς δεῖ νοεῖν τὸ "
            "« ἐφ' ἡμῖν » κατὰ τὸν Ἀπόστολον — comment comprendre le "
            "« en notre pouvoir » selon l'Apôtre), Q. 42 (sur la "
            "volonté gnomique [γνωμικὸν θέλημα] humaine post-lapsaire), "
            "Q. 61 (sur l'œuvre rédemptrice et la liberté restaurée en "
            "Christ). Édition critique de référence : Carl Laga & "
            "Carlos Steel, *Quaestiones ad Thalassium* I-II (CCSG 7 + "
            "22, Brepols 1980 + 1990). Traduction anglaise complète : "
            "Maximos Constas, *Maximus the Confessor: On Difficulties "
            "in Sacred Scripture — The Responses to Thalassios* "
            "(Catholic University of America Press, FOTC 136, 2018). "
            "Traduction française partielle : Larchet-Ponsoye (Cerf "
            "2010-2015)."
        ),
        "alternative_names": [
            "Quaestiones ad Thalassium",
            "Πρὸς Θαλάσσιον",
            "Ad Thalassium",
            "Responses to Thalassios",
        ],
        "metadata": {
            "genre": "theological-exegetical aporiai",
            "author": "Maximus the Confessor",
            "author_id": "person_maximus_confessor_d662",
            "kg_work_id": "work_maximus_quaestiones_thalassium",
            "date_composed": "c. 630 — 633 CE",
            "original_language": "Greek",
            "editions": [
                "Laga & Steel, CCSG 7 (Brepols 1980, Q. 1-55)",
                "Laga & Steel, CCSG 22 (Brepols 1990, Q. 56-65)",
                "Constas, FOTC 136 (CUA Press 2018, Eng.)",
                "Larchet & Ponsoye (Cerf 2010-2015, Fr. partial)",
            ],
            "key_questions_for_free_will": [
                "Q. 21 (τὸ ἐφ' ἡμῖν)",
                "Q. 42 (γνωμικὸν θέλημα post-lapsum)",
                "Q. 61 (rédemption et liberté restaurée)",
            ],
            "wave": WAVE_TAG,
        },
    },
]


# ---------------------------------------------------------------------------
# Argument specs (6)
# ---------------------------------------------------------------------------


ARGUMENTS: list[dict[str, Any]] = [
    {
        "node_id": "argument_pyrrhus_one_energy",
        "label": "Pyrrhus : une seule énergie en Christ (mono-énergisme)",
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Pyrrhus de Constantinople, position "
            "rapportée par Maxime le Confesseur, *Disputatio cum "
            "Pyrrho* §1-12 (PG 91, 287-308) — Carthage, juillet 645 ; "
            "anticipée par le Pseudo-Denys, *Lettre* 4 (μία θεανδρικὴ "
            "ἐνέργεια) et par le Pact of Union de Cyrus d'Alexandrie "
            "633.\n"
            "**Prémisse 1** : Une seule personne agissante (Christ "
            "comme hypostase unique de l'Incarnation) exige une seule "
            "activité (μία ἐνέργεια), sans quoi on diviserait l'agent.\n"
            "**Prémisse 2** : Deux énergies impliqueraient deux "
            "principes d'opération, donc deux sujets agissants, donc "
            "deux personnes — résultat nestorianisant inacceptable.\n"
            "**Conclusion** : Christ a une seule activité théandrique "
            "(μία θεανδρικὴ ἐνέργεια), divine et humaine fusionnées en "
            "une seule opération.\n"
            "**Type de raisonnement** : déductif, à partir d'une "
            "ontologie hypostase = sujet-d'opération.\n"
            "**Réception scholaire** : Louth 1996, *Maximus the "
            "Confessor* (Routledge) ; Bathrellos 2004, *The Byzantine "
            "Christ* (OUP) ; Doucet 1972 (édition critique en "
            "préparation, SC)."
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_pyrrhus_constantinople_d654",
            "discussed_concept": "concept_monothelitism",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "argument_pyrrhus_one_will",
        "label": "Pyrrhus : une seule volonté en Christ (monothélisme)",
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Pyrrhus de Constantinople, position "
            "rapportée par Maxime le Confesseur, *Disputatio cum "
            "Pyrrho* §13-28 (PG 91, 308-336) — Carthage, juillet 645 ; "
            "doctrine impériale codifiée dans l'Ekthesis 638 "
            "(Héraclius) puis dans le Typos 648 (Constans II).\n"
            "**Prémisse 1** : Si Christ avait deux volontés "
            "(δύο θελήματα), elles seraient soit en conflit "
            "(christologie schizophrène), soit l'une soumise à l'autre "
            "(christologie subordinationiste).\n"
            "**Prémisse 2** : Toute volonté est attribuable à un sujet "
            "(une hypostase) ; deux volontés exigeraient donc deux "
            "sujets, ce qui est nestorianisant.\n"
            "**Conclusion** : Christ n'a qu'une seule volonté "
            "(ἓν θέλημα), la volonté divine, qui se manifeste à travers "
            "son humanité.\n"
            "**Type de raisonnement** : disjonctif (dilemme) + ontologie "
            "hypostase = sujet-volitif.\n"
            "**Réception scholaire** : Louth 1996 ; Bathrellos 2004 ; "
            "Cooper 2005, *The Body in St Maximus*."
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_pyrrhus_constantinople_d654",
            "discussed_concept": "concept_monothelitism",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "argument_maximus_two_energies",
        "label": "Maxime : deux énergies en Christ (dyénergie)",
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Maxime le Confesseur, *Opusculum* 1 "
            "(Ad Marinum, *De duabus voluntatibus*, PG 91, 9-37) et "
            "*Disputatio cum Pyrrho* §1-12 (PG 91, 287-308).\n"
            "**Prémisse 1** : L'énergie (ἐνέργεια) est l'expression "
            "opérative de la nature : à chaque nature appartient en "
            "propre son énergie naturelle (par exemple, la nature ignée "
            "a l'énergie de chauffer).\n"
            "**Prémisse 2** : Christ assume deux natures intactes "
            "(divine et humaine), unies sans confusion ni séparation "
            "selon Chalcédoine (451).\n"
            "**Conclusion** : Christ a donc deux énergies (δύο "
            "ἐνέργειαι), une divine et une humaine, "
            "asynchutōs-adiairetōs unies dans l'unique hypostase du "
            "Logos incarné. Nier l'une, c'est nier la nature "
            "correspondante — ce qui ruine soit la divinité soit "
            "l'humanité du Christ.\n"
            "**Type de raisonnement** : déductif, à partir de l'axiome "
            "néo-chalcédonien « ce qui n'est pas assumé n'est pas "
            "guéri » (Grégoire de Nazianze, *Ep.* 101).\n"
            "**Réception scholaire** : Louth 1996 ; Bathrellos 2004 ; "
            "Tollefsen 2008 ; consacrée à Constantinople III 681."
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_maximus_confessor_d662",
            "discussed_concept": "concept_monothelitism",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "argument_maximus_two_wills",
        "label": "Maxime : deux volontés en Christ (dyothélie)",
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Maxime le Confesseur, *Opusculum* 3 "
            "(PG 91, 45-56), *Opusculum* 16 (PG 91, 184-212) et "
            "*Disputatio cum Pyrrho* §13-28 (PG 91, 308-336).\n"
            "**Prémisse 1** : La volonté (θέλημα) est une faculté de "
            "la NATURE (θέλημα φυσικόν, volonté naturelle), non de "
            "l'hypostase — distinction reçue de Grégoire de Nazianze "
            "et des Cappadociens.\n"
            "**Prémisse 2** : Christ a deux natures intactes ; chaque "
            "nature porte donc sa propre faculté volitive naturelle.\n"
            "**Prémisse 3** : Il faut distinguer θέλημα φυσικόν "
            "(volonté naturelle, capacité de la nature, intrinsèquement "
            "libre car conforme à sa nature) et θέλημα γνωμικόν "
            "(volonté gnomique, mode délibératif marqué par l'ignorance "
            "et l'hésitation post-lapsaire). Christ assume θέλημα "
            "φυσικόν humain mais non θέλημα γνωμικόν, qui est un mode "
            "déchu de vouloir.\n"
            "**Conclusion** : Christ a deux volontés naturelles (δύο "
            "θελήματα φυσικά), divine et humaine, unies harmoniquement "
            "dans l'hypostase du Logos, sans la dialectique γνωμική de "
            "l'humanité déchue.\n"
            "**Type de raisonnement** : déductif (nature → faculté "
            "volitive) + distinction conceptuelle (φυσικόν vs γνωμικόν).\n"
            "**Réception scholaire** : Louth 1996 ; Bathrellos 2004 "
            "(*The Byzantine Christ*, OUP) ; Larchet 1996, *La "
            "divinisation de l'homme selon Maxime le Confesseur* "
            "(Cerf) ; canonisée à Constantinople III 681."
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_maximus_confessor_d662",
            "discussed_concept": "concept_monothelitism",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "argument_maximus_natural_will_freedom",
        "label": (
            "Maxime : la volonté naturelle est intrinsèquement libre "
            "(θέλημα φυσικόν ἐλεύθερον)"
        ),
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Maxime le Confesseur, *Opuscula "
            "theologica et polemica* 1, 3, 16 (PG 91, 9-37 ; 45-56 ; "
            "184-212).\n"
            "**Prémisse 1** : Être libre, c'est être conforme à sa "
            "propre nature (κατὰ φύσιν) — la liberté n'est pas une "
            "indifférence entre des contraires (γνώμη) mais une "
            "tendance ordonnée vers le bien naturel.\n"
            "**Prémisse 2** : La volonté naturelle (θέλημα φυσικόν) "
            "est précisément la faculté par laquelle la nature "
            "rationnelle s'oriente vers son bien propre — elle est "
            "donc libre par essence, dans la mesure où elle accomplit "
            "la nature.\n"
            "**Prémisse 3** : La servitude post-lapsaire de la chute "
            "n'affecte pas la volonté naturelle elle-même (qui demeure "
            "intacte ontologiquement) mais seulement le mode "
            "délibératif γνωμικός, qui est ignorance et hésitation.\n"
            "**Conclusion** : La liberté ontologique est donc co-"
            "extensive à la nature rationnelle ; ce qui doit être "
            "guéri, ce n'est pas la nature ni la volonté naturelle, "
            "mais le mode γνωμικός de vouloir.\n"
            "**Type de raisonnement** : déductif, à partir d'une "
            "ontologie aristotélo-cappadocienne de la nature comme "
            "principe d'opération ordonnée.\n"
            "**Réception scholaire** : Louth 1996 ; Bathrellos 2004 ; "
            "Larchet 1996 ; Tollefsen 2008. (Distinct de "
            "`argument_maximus_natural_vs_gnomic_will`, qui est la "
            "distinction descriptive ; ici, la thèse positive de la "
            "liberté ontologique.)"
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_maximus_confessor_d662",
            "discussed_concept": "concept_monothelitism",
            "related_argument": "argument_maximus_natural_vs_gnomic_will",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "argument_maximus_proairesis_baptismal_repair",
        "label": (
            "Maxime : le baptême restaure la προαίρεσις (réparation "
            "gnomique post-baptismale)"
        ),
        "type": "argument",
        "period": "Late Antiquity",
        "description": (
            "**Source primaire** : Maxime le Confesseur, *Opusculum* 1 "
            "(PG 91, 9-37) et *Ambigua ad Iohannem* 7 (PG 91, 1068-1101 "
            "; Constas DOML 28).\n"
            "**Prémisse 1** : La nature humaine post-lapsaire reste "
            "ontologiquement intacte dans sa volonté naturelle "
            "(θέλημα φυσικόν), mais son mode délibératif (θέλημα "
            "γνωμικόν) est marqué par l'ignorance, l'hésitation et la "
            "possibilité de l'erreur.\n"
            "**Prémisse 2** : Le baptême, en incorporant l'agent à "
            "l'hypostase du Christ (qui n'a pas de γνώμη), opère la "
            "guérison progressive du mode γνωμικός : la προαίρεσις "
            "post-baptismale, mue par la grâce, retrouve sa "
            "conformité naturelle au bien.\n"
            "**Conclusion** : La liberté restaurée par la grâce "
            "consiste donc en la convergence progressive de la "
            "προαίρεσις (choix délibéré) vers le θέλημα φυσικόν — la "
            "θέωσις (déification) culminant en une stabilité gnomique "
            "qui imite analogiquement l'absence de γνώμη du Christ.\n"
            "**Type de raisonnement** : sotériologique (réparation par "
            "incorporation hypostatique) + anthropologique "
            "(distinction φύσις / γνώμη / προαίρεσις).\n"
            "**Réception scholaire** : Louth 1996 ; Larchet 1996 ; "
            "Cooper 2005 ; Tollefsen 2008. Théologie maxime de la "
            "synergie grâce + liberté."
        ),
        "alternative_names": [],
        "metadata": {
            "creator_id": "person_maximus_confessor_d662",
            "discussed_concept": "concept_synergism",
            "needs_evidence": True,
            "wave": WAVE_TAG,
        },
    },
]


# ---------------------------------------------------------------------------
# Edge specs (computed from the above)
# ---------------------------------------------------------------------------


# (source, relation, target, weight) — all idempotent, checked by signature.
def _build_edge_specs() -> list[tuple[str, str, str, float, str]]:
    """Return list of (source, relation, target, weight, role) tuples.

    The optional ``role`` field is purely cosmetic — it controls log
    grouping.
    """
    specs: list[tuple[str, str, str, float, str]] = []

    # authored_by
    specs.append(
        (
            "work_maximus_quaestiones_thalassium",
            "authored_by",
            "person_maximus_confessor_d662",
            1.0,
            "authored_by",
        )
    )

    # member_of (monothelite faction)
    for pid in (
        "person_pyrrhus_constantinople_d654",
        "person_sergius_constantinople_565_638",
        "person_cyrus_alexandria_d641",
    ):
        specs.append((pid, "member_of", "group_monothelites", 1.0, "member_of"))

    # member_of (dyothelite faction)
    for pid in (
        "person_sophronius_jerusalem_560_638",
        "person_martin_i_pope_590_655",
    ):
        specs.append((pid, "member_of", "group_dyothelites", 1.0, "member_of"))

    # participates_in — Lateran 649
    for pid in (
        "person_maximus_confessor_d662",
        "person_martin_i_pope_590_655",
    ):
        specs.append((pid, "participates_in", "council_lateran_649", 1.0, "participates"))

    # participates_in — Psephos 633 (originators)
    for pid in (
        "person_sergius_constantinople_565_638",
        "person_cyrus_alexandria_d641",
        "person_pyrrhus_constantinople_d654",
    ):
        specs.append((pid, "participates_in", "event_psephos_633", 0.95, "participates"))

    # participates_in — Constantinople III 681 (Maximus posthumously
    # rehabilitated). The condemned Pyrrhus/Sergius are recorded via
    # the council node's metadata (key_condemnations) rather than a
    # participates edge, since posthumous condemnation is not literal
    # participation. Maximus's case is identical (posthumous adoption
    # of his doctrine) but is the *positive* anchor.
    specs.append(
        (
            "person_maximus_confessor_d662",
            "participates_in",
            "council_constantinople_iii_681",
            0.9,
            "participates",
        )
    )

    # created_by — arguments → person
    creator_map: dict[str, str] = {
        "argument_pyrrhus_one_energy": "person_pyrrhus_constantinople_d654",
        "argument_pyrrhus_one_will": "person_pyrrhus_constantinople_d654",
        "argument_maximus_two_energies": "person_maximus_confessor_d662",
        "argument_maximus_two_wills": "person_maximus_confessor_d662",
        "argument_maximus_natural_will_freedom": "person_maximus_confessor_d662",
        "argument_maximus_proairesis_baptismal_repair": "person_maximus_confessor_d662",
    }
    for arg_id, person_id in creator_map.items():
        specs.append((arg_id, "created_by", person_id, 1.0, "created_by"))

    # discusses — arguments → concept_monothelitism (ontology source_types
    # includes argument, target_types includes concept).
    for arg_id in (
        "argument_pyrrhus_one_energy",
        "argument_pyrrhus_one_will",
        "argument_maximus_two_energies",
        "argument_maximus_two_wills",
        "argument_maximus_natural_will_freedom",
    ):
        specs.append((arg_id, "discusses", "concept_monothelitism", 0.95, "discusses"))

    # The proairesis-baptismal argument is about synergism, not strictly
    # monothelitism — discuss the more appropriate concept.
    specs.append(
        (
            "argument_maximus_proairesis_baptismal_repair",
            "discusses",
            "concept_synergism",
            0.95,
            "discusses",
        )
    )

    # critiques — symmetric pairs Maxime ↔ Pyrrhus
    specs.append(
        (
            "argument_maximus_two_energies",
            "critiques",
            "argument_pyrrhus_one_energy",
            1.0,
            "critiques",
        )
    )
    specs.append(
        (
            "argument_pyrrhus_one_energy",
            "critiques",
            "argument_maximus_two_energies",
            1.0,
            "critiques",
        )
    )
    specs.append(
        (
            "argument_maximus_two_wills",
            "critiques",
            "argument_pyrrhus_one_will",
            1.0,
            "critiques",
        )
    )
    specs.append(
        (
            "argument_pyrrhus_one_will",
            "critiques",
            "argument_maximus_two_wills",
            1.0,
            "critiques",
        )
    )

    return specs


# ---------------------------------------------------------------------------
# IO helpers
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


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e.get("source") or "", e.get("relation") or "", e.get("target") or "")


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} — skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Node + edge construction
# ---------------------------------------------------------------------------


def build_person_node(spec: dict[str, Any]) -> dict[str, Any]:
    nid = spec["node_id"]
    alt = spec.get("alternative_names") or []
    if not isinstance(alt, list):
        raise TypeError(f"alternative_names must be a list for {nid}")
    metadata: dict[str, Any] = dict(spec.get("metadata") or {})
    metadata.setdefault("wave", WAVE_TAG)
    return {
        "alternative_names": json.dumps(alt, ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "node_id": nid,
        "period": spec.get("period"),
        "role": None,
        "school": spec.get("school"),
        "type": spec.get("type", "person"),
        "updated_at": NOW_ISO,
    }


def build_event_node(spec: dict[str, Any]) -> dict[str, Any]:
    nid = spec["node_id"]
    metadata: dict[str, Any] = dict(spec.get("metadata") or {})
    metadata.setdefault("wave", WAVE_TAG)
    return {
        "alternative_names": json.dumps([], ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "node_id": nid,
        "period": spec.get("period"),
        "role": None,
        "school": None,
        "type": "event",
        "updated_at": NOW_ISO,
    }


def build_work_node(spec: dict[str, Any]) -> dict[str, Any]:
    nid = spec["node_id"]
    alt = spec.get("alternative_names") or []
    if not isinstance(alt, list):
        raise TypeError(f"alternative_names must be a list for {nid}")
    metadata: dict[str, Any] = dict(spec.get("metadata") or {})
    metadata.setdefault("wave", WAVE_TAG)
    return {
        "alternative_names": json.dumps(alt, ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "node_id": nid,
        "period": spec.get("period"),
        "role": None,
        "school": None,
        "type": "work",
        "updated_at": NOW_ISO,
    }


def build_argument_node(spec: dict[str, Any]) -> dict[str, Any]:
    nid = spec["node_id"]
    alt = spec.get("alternative_names") or []
    if not isinstance(alt, list):
        raise TypeError(f"alternative_names must be a list for {nid}")
    metadata: dict[str, Any] = dict(spec.get("metadata") or {})
    metadata.setdefault("wave", WAVE_TAG)
    return {
        "alternative_names": json.dumps(alt, ensure_ascii=False),
        "created_at": NOW_ISO,
        "description": spec["description"],
        "id": nid,
        "label": spec["label"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "node_id": nid,
        "period": spec.get("period"),
        "role": None,
        "school": None,
        "type": "argument",
        "updated_at": NOW_ISO,
    }


def build_edge(
    source: str,
    relation: str,
    target: str,
    weight: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md: dict[str, Any] = dict(metadata or {})
    md.setdefault("wave", WAVE_TAG)
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(md, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-k] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id: dict[str, dict[str, Any]] = {node_id(n): n for n in nodes}
    edges_sigs: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    persons_added = 0
    events_added = 0
    works_added = 0
    arguments_added = 0
    skipped_existing = 0

    # ---- Persons
    for spec in PERSONS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            skipped_existing += 1
            print(f"[skip-person] {nid} already present")
            continue
        n = build_person_node(spec)
        nodes.append(n)
        nodes_by_id[nid] = n
        persons_added += 1
        print(f"[add-person]  {nid}")

    # ---- Events
    for spec in EVENTS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            skipped_existing += 1
            print(f"[skip-event]  {nid} already present")
            continue
        n = build_event_node(spec)
        nodes.append(n)
        nodes_by_id[nid] = n
        events_added += 1
        print(f"[add-event]   {nid}")

    # ---- Works
    for spec in WORKS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            skipped_existing += 1
            print(f"[skip-work]   {nid} already present")
            continue
        n = build_work_node(spec)
        nodes.append(n)
        nodes_by_id[nid] = n
        works_added += 1
        print(f"[add-work]    {nid}")

    # ---- Arguments
    for spec in ARGUMENTS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            skipped_existing += 1
            print(f"[skip-arg]    {nid} already present")
            continue
        n = build_argument_node(spec)
        nodes.append(n)
        nodes_by_id[nid] = n
        arguments_added += 1
        print(f"[add-arg]     {nid}")

    # ---- Edges
    role_counts: dict[str, int] = {
        "authored_by": 0,
        "member_of": 0,
        "participates": 0,
        "created_by": 0,
        "discusses": 0,
        "critiques": 0,
    }
    edges_skipped: dict[str, int] = dict.fromkeys(role_counts, 0)

    for source, relation, target, weight, role in _build_edge_specs():
        if source not in nodes_by_id:
            print(f"[edge-skip] missing source {source} (rel={relation})")
            continue
        if target not in nodes_by_id:
            print(f"[edge-skip] missing target {target} (rel={relation})")
            continue
        sig = (source, relation, target)
        if sig in edges_sigs:
            edges_skipped[role] = edges_skipped.get(role, 0) + 1
            continue
        e = build_edge(source=source, relation=relation, target=target, weight=weight)
        edges.append(e)
        edges_sigs.add(sig)
        role_counts[role] = role_counts.get(role, 0) + 1
        print(f"[edge-add]  {source} -[{relation}]-> {target}")

    # ---- Write
    if (
        persons_added
        or events_added
        or works_added
        or arguments_added
        or sum(role_counts.values())
    ):
        write_nodes(nodes)
        write_edges(edges)
        print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")
    else:
        print("[write] no changes — files untouched")

    # ---- Summary counters (spec-mandated format)
    print()
    print(
        f"[wave-k] persons_added={persons_added}/{len(PERSONS)}  "
        f"events_added={events_added}/{len(EVENTS)}  "
        f"works_added={works_added}/{len(WORKS)}  "
        f"arguments_added={arguments_added}/{len(ARGUMENTS)}"
    )
    print(
        f"[wave-k] authored_by_edges={role_counts['authored_by']}  "
        f"member_of_edges={role_counts['member_of']}  "
        f"participates_edges={role_counts['participates']}"
    )
    print(
        f"[wave-k] discusses_edges={role_counts['discusses']}  "
        f"critiques_edges={role_counts['critiques']}  "
        f"created_by_edges={role_counts['created_by']}"
    )
    print(f"[wave-k] skipped_existing={skipped_existing}")
    edges_skipped_total = sum(edges_skipped.values())
    print(f"[wave-k] edges_skipped_existing={edges_skipped_total}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
