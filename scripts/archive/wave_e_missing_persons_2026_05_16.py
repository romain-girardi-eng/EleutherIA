#!/usr/bin/env python3
"""Wave E — Missing person nodes — 2026-05-16.

Add 20 missing person nodes flagged by the KG audit:

* 3 Patristic Latin Fathers (Athanase, Ambroise, Jérôme)
* 3 Hellenistic Stoa / New Academy (Panétius, Diogène de Babylone,
  Philon de Larissa)
* 4 Origen / Maxime specialists (Harl, Perrone, Daley, Louth)
* 7 modern free-will / patristics scholars (Stump, Vargas, Timpe,
  Plantinga, Tieleman, Daniélou, Jacobsen)
* 3 ancient persons (Apulée, Philopon, Cyrille de Jérusalem)

Also adds:

* 4 teacher-chain ``student_of`` edges (Chrysippe → Diog Bab → Panétius
  → Posidonius ; Clitomaque → Philon de Larissa). The KG convention is
  ``student_of`` from student to teacher (active form, no ``teaches``
  inverse exists).
* 4 ``member_of`` school-membership edges where the school node already
  exists.

Idempotent: rerun = no-op.
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

WAVE_TAG = "wave_e_missing_persons_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Person specs
# ---------------------------------------------------------------------------


PERSONS: list[dict[str, Any]] = [
    # -------------------------------------------------------------------
    # P0 — 3 Patristic Latin Fathers
    # -------------------------------------------------------------------
    {
        "node_id": "person_athanasius_alexandria_298_373",
        "label": "Athanase d'Alexandrie",
        "type": "person",
        "period": "Patristic",
        "school": None,
        "description": (
            "Évêque d'Alexandrie 328-373 (avec cinq exils sous Constance II, "
            "Julien et Valens), docteur de l'Église et principal théoricien "
            "nicéen face à l'arianisme. Pour la problématique du libre arbitre, "
            "trois oeuvres jouent un rôle pivot : (1) Contra Gentes (chap. 25-29) "
            "qui développe une critique anti-fataliste de l'astrologie et défend "
            "l'autodétermination de l'âme rationnelle ; (2) De Incarnatione qui "
            "articule une anthropologie de la liberté κατ' εἰκόνα Θεοῦ, perdue "
            "par le péché et restaurée par le Christ ; (3) Vita Antonii, source "
            "fondatrice du modèle ascétique de la προαίρεσις chrétienne. "
            "Éditions critiques : PG 25-28 ; SC 18bis (CG/DI, éd. Kannengiesser "
            "1973, rééd. Cerf) ; SC 199 (Lettres festales coptes, éd. Camplani "
            "1977) ; SC 400 (Vita Antonii, éd. Bartelink 1994)."
        ),
        "alternative_names": ["Athanasius Alexandrinus", "Ἀθανάσιος Ἀλεξανδρείας"],
        "metadata": {
            "birth_date": "c. 298 CE",
            "death_date": "373 CE",
            "wikidata_qid": "Q44024",
            "episcopate": "328-373 CE",
            "editions": [
                "PG 25-28",
                "SC 18bis (Kannengiesser 1973)",
                "SC 199 (Camplani 1977)",
                "SC 400 (Bartelink 1994)",
            ],
            "key_works": ["Contra Gentes", "De Incarnatione", "Vita Antonii"],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_ambrose_milan_339_397",
        "label": "Ambroise de Milan",
        "type": "person",
        "period": "Patristic",
        "school": None,
        "description": (
            "Évêque de Milan 374-397, médiateur principal du stoïcisme latin "
            "vers Augustin (qu'il baptise en 387) et figure majeure de la "
            "théologie morale latine. Pour le libre arbitre, trois oeuvres "
            "importent : (1) De Officiis ministrorum, réécriture chrétienne "
            "du De Officiis cicéronien — lui-même décalque d'un traité perdu "
            "de Panétius — qui transmet à l'Occident chrétien la doctrine "
            "stoïcienne des personae et du καθῆκον ; (2) Hexaemeron, sur la "
            "liberté de l'âme rationnelle dans l'ordre de la création ; "
            "(3) De Iacob et vita beata, sur la liberté comme imitatio "
            "Christi. Éditions critiques : PL 14-17 ; CSEL 32.1 / 32.2 / 62 / "
            "73 / 78-79 / 82 ; SC 25bis (Hexaemeron, éd. Banterle réed.) ; "
            "SC 488 (De Officiis, éd. Testard 2005)."
        ),
        "alternative_names": ["Ambrosius Mediolanensis", "Sant'Ambrogio"],
        "metadata": {
            "birth_date": "c. 339 CE",
            "death_date": "397 CE",
            "wikidata_qid": "Q44183",
            "episcopate": "374-397 CE",
            "editions": [
                "PL 14-17",
                "CSEL 32.1/32.2/62/73/78-79/82",
                "SC 25bis (Banterle, Hexaemeron)",
                "SC 488 (Testard 2005, De Officiis)",
            ],
            "key_works": [
                "De Officiis ministrorum",
                "Hexaemeron",
                "De Iacob et vita beata",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_jerome_stridon_347_420",
        "label": "Jérôme de Stridon",
        "type": "person",
        "period": "Patristic",
        "school": None,
        "description": (
            "Traducteur de la Vulgate, ascète, polémiste anti-origéniste (à "
            "partir de 393) puis anti-pélagien (à partir de 411). Pour le "
            "libre arbitre, son Dialogus adversus Pelagianos (CCSL 80 ; SC "
            "533, éd. Canellis 2010-2011) constitue la pièce centrale "
            "anti-pélagienne du côté augustinien, avec néanmoins des nuances "
            "semi-pélagiennes en filigrane sur le rôle de la volonté humaine. "
            "Ses traductions sélectives d'Origène (Commentaires sur Jérémie "
            "et Isaïe — CCSL 73-74 et 75-75A) modèlent la réception latine "
            "de l'αὐτεξούσιον origénien. Epistulae : CSEL 54-56. Sa rupture "
            "publique avec Rufin (vers 393-395) cristallise la première crise "
            "origéniste latine."
        ),
        "alternative_names": [
            "Hieronymus Stridonensis",
            "Sophronius Eusebius Hieronymus",
        ],
        "metadata": {
            "birth_date": "c. 347 CE",
            "death_date": "420 CE",
            "wikidata_qid": "Q44248",
            "editions": [
                "PL 22-30",
                "CCSL 72-80",
                "CSEL 54-56 (Epistulae)",
                "SC 533 (Canellis 2010-2011, Adv. Pelagianos)",
            ],
            "key_works": [
                "Dialogus adversus Pelagianos",
                "Vulgata",
                "Commentarii in Hieremiam",
                "Commentarii in Isaiam",
                "Epistulae",
            ],
            "wave": WAVE_TAG,
        },
    },
    # -------------------------------------------------------------------
    # P0 — 3 Hellenistic Stoa / New Academy
    # -------------------------------------------------------------------
    {
        "node_id": "person_panaetius_rhodes_185_109bce",
        "label": "Panétius de Rhodes",
        "type": "person",
        "period": "Hellenistic",
        "school": "Stoics",
        "description": (
            "Scolarque du Portique vers 129-109 av. J.-C., maître de "
            "Posidonius d'Apamée. Source principale (perdue) du De Officiis "
            "cicéronien I-II, via son Περὶ τοῦ καθήκοντος. Théoricien de la "
            "« moyenne stoïcienne » : assouplissement de l'ekpyrosis "
            "stoïcienne, théorie des quatre personae (rôles individuels — "
            "nature commune, nature individuelle, hasard, choix) qui ouvre "
            "l'espace conceptuel d'une responsabilité morale différenciée à "
            "l'intérieur du déterminisme stoïcien orthodoxe. Fragments : "
            "Modestus van Straaten, Panaetii Rhodii Fragmenta (Leiden : "
            "Brill, 3e éd. 1962). Reconstruction : Jean-Baptiste Gourinat, "
            "La Théorie stoïcienne de la sensation (Vrin 1996, chap. sur "
            "Panétius)."
        ),
        "alternative_names": ["Panaetius Rhodius", "Παναίτιος ὁ Ῥόδιος"],
        "metadata": {
            "birth_date": "c. 185 BCE",
            "death_date": "c. 109 BCE",
            "scholarchate": "c. 129-109 BCE",
            "editions": [
                "van Straaten, Panaetii Rhodii Fragmenta (Brill 1952, 3e éd. 1962)",
            ],
            "key_works": [
                "Περὶ τοῦ καθήκοντος (lost, transmitted via Cic. De Officiis I-II)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_diogenes_babylon_240_152bce",
        "label": "Diogène de Babylone",
        "type": "person",
        "period": "Hellenistic",
        "school": "Stoics",
        "description": (
            "Cinquième scolarque du Portique vers 152 av. J.-C., successeur "
            "de Chrysippe puis de Zénon de Tarse. Maître de Panétius de "
            "Rhodes. Membre de l'ambassade philosophique stoïcienne envoyée "
            "à Rome en 155 av. J.-C. avec Carnéade (Académie) et Critolaüs "
            "(Lycée) — épisode décisif pour la diffusion latine de la "
            "philosophie hellénistique. Fragments : SVF III.210-243 (Hans "
            "von Arnim, Stoicorum Veterum Fragmenta, Teubner 1903-1905). "
            "Sources secondaires : David Sedley, « Diogenes of Babylon », "
            "in Algra/Barnes/Mansfeld/Schofield, Cambridge History of "
            "Hellenistic Philosophy (CUP 1999)."
        ),
        "alternative_names": [
            "Diogenes Babylonius",
            "Διογένης Βαβυλώνιος",
            "Diogène de Séleucie",
        ],
        "metadata": {
            "birth_date": "c. 240 BCE",
            "death_date": "c. 152 BCE",
            "scholarchate": "succeeded Zeno of Tarsus, predecessor of Antipater of Tarsus",
            "editions": ["SVF III.210-243 (von Arnim, Teubner 1903-1905)"],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_philo_larissa_159_84bce",
        "label": "Philon de Larissa",
        "type": "person",
        "period": "Hellenistic",
        "school": "Academics",
        "description": (
            "Dernier scolarque de la Nouvelle Académie 110/109-84 av. J.-C., "
            "élève de Clitomaque, maître de Cicéron à Rome 88-87 av. J.-C. "
            "Tournant probabiliste mitigé : abandon partiel de l'ἐποχή "
            "carnéadéenne au profit d'une épistémologie modérée — position "
            "controversée après la publication des « Livres romains » "
            "(87-86 av. J.-C.) attaquée par Antiochus d'Ascalon. Source "
            "directe de Cicéron Academica I-II et de la réception "
            "académique latine. Reconstruction des fragments : "
            "Hans-Joachim Mette, « Weitere Akademiker heute : Von Lakydes "
            "bis zu Kleitomachos », Lustrum 27 (1985) 39-148 ; « Philon "
            "von Larisa und Antiochos von Askalon », Lustrum 28-29 "
            "(1986-1987)."
        ),
        "alternative_names": ["Philo Larissaeus", "Φίλων ὁ Λαρισαῖος"],
        "metadata": {
            "birth_date": "c. 159 BCE",
            "death_date": "c. 84 BCE",
            "scholarchate": "110/109-84 BCE",
            "editions": [
                "Mette, Lustrum 27 (1985) 39-148",
                "Mette, Lustrum 28-29 (1986-1987)",
            ],
            "wave": WAVE_TAG,
        },
    },
    # -------------------------------------------------------------------
    # P0 — 4 Origen / Maxime specialists
    # -------------------------------------------------------------------
    {
        "node_id": "scholar_harl_m",
        "label": "Marguerite Harl",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Helléniste française (1919-2020), professeur à Paris-Sorbonne, "
            "fondatrice de la Bible d'Alexandrie (traduction française "
            "commentée de la Septante, Cerf, série dirigée à partir de "
            "1986). Pivot de la réception française d'Origène — éditrice "
            "de la Philocalie 1-20 d'Origène (SC 302, Cerf 1983). "
            "Ouvrage de référence : Origène et la fonction révélatrice "
            "du Verbe incarné (Patristica Sorbonensia 2, Seuil 1958). "
            "Co-éditrice (avec Doutreleau) des Homélies sur la Genèse "
            "d'Origène (SC 7bis, Cerf 1976, rééd.). Son école a formé "
            "une génération de patristiciens français du judéo-grec."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Harl",
            "given_names": "Marguerite",
            "birth_date": "1919",
            "death_date": "2020",
            "affiliations": ["Université Paris-Sorbonne (Paris IV)"],
            "specialty": "Septante, Origène, philologie grecque biblique et patristique",
            "key_works": [
                "Origène et la fonction révélatrice du Verbe incarné (Seuil 1958)",
                "Origène, Philocalie 1-20 — SC 302 (Cerf 1983)",
                "Origène, Homélies sur la Genèse — SC 7bis (Cerf 1976, avec Doutreleau)",
                "La Bible d'Alexandrie (dir., Cerf 1986–)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_perrone_l",
        "label": "Lorenzo Perrone",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Patristicien italien (né 1948), professeur émérite à "
            "l'Université de Bologne, directeur de la série monographique "
            "Origeniana. Auteur de l'édition critique pivot des nouvelles "
            "homélies sur les Psaumes d'Origène : Die neuen Psalmenhomilien, "
            "GCS NF 19 (de Gruyter 2015) — découverte en 2012 du Codex "
            "Monacensis Graecus 314 (29 homélies grecques inédites), qui "
            "renouvelle profondément l'image de la prédication "
            "origénienne sur le libre arbitre, la providence et la "
            "pédagogie divine. Directeur des actes Origeniana XII "
            "(Leuven, Peeters 2019)."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Perrone",
            "given_names": "Lorenzo",
            "birth_date": "1948",
            "affiliations": ["Università di Bologna"],
            "specialty": "Origen studies, Greek patristics, monastic literature",
            "key_works": [
                "Die neuen Psalmenhomilien — GCS NF 19 (de Gruyter 2015)",
                "Origeniana XII (Peeters 2019, ed.)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_daley_b",
        "label": "Brian E. Daley",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Patristicien jésuite américain (né 1940), Catherine F. "
            "Huisking Professor of Theology à l'Université Notre Dame. "
            "Ouvrage de référence sur l'eschatologie patristique : The "
            "Hope of the Early Church (Cambridge University Press 1991, "
            "réimpr. 2003). Travaux pivots sur Léonce de Byzance, "
            "Grégoire de Nazianze (Gregory of Nazianzus, Routledge 2006) "
            "et la christologie patristique (God Visible: Patristic "
            "Christology Reconsidered, Oxford University Press 2018). "
            "Pour le KG free-will : recoupe Origène et Maxime le "
            "Confesseur sur προαίρεσις et la distinction γνωμικὸν / "
            "φυσικὸν θέλημα."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Daley",
            "given_names": "Brian E.",
            "birth_date": "1940",
            "affiliations": ["University of Notre Dame", "Society of Jesus"],
            "specialty": "Patristic eschatology, Christology, Maximus the Confessor, Gregory of Nazianzus",
            "key_works": [
                "The Hope of the Early Church (CUP 1991)",
                "Gregory of Nazianzus (Routledge 2006)",
                "God Visible: Patristic Christology Reconsidered (OUP 2018)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_louth_a",
        "label": "Andrew Louth",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Patristicien britannique (né 1944), professeur émérite à "
            "Durham University, prêtre orthodoxe. Spécialiste majeur "
            "anglophone de Maxime le Confesseur : Maximus the Confessor "
            "(Routledge 1996), édition + traduction commentée des Opuscula "
            "theologica et polemica. Sa présentation de la distinction "
            "γνωμικὸν vs φυσικὸν θέλημα maximienne — clef de la "
            "controverse monothélite et de la christologie diphysite — y "
            "est exposée magistralement. Autres ouvrages : The Origins of "
            "the Christian Mystical Tradition: From Plato to Denys (OUP "
            "1981, 2e éd. 2007), St John Damascene: Tradition and "
            "Originality in Byzantine Theology (OUP 2002)."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Louth",
            "given_names": "Andrew",
            "birth_date": "1944",
            "affiliations": ["Durham University (emeritus)"],
            "specialty": "Greek patristics, Maximus the Confessor, John of Damascus, mystical theology",
            "key_works": [
                "Maximus the Confessor (Routledge 1996)",
                "The Origins of the Christian Mystical Tradition (OUP 1981, 2e éd. 2007)",
                "St John Damascene (OUP 2002)",
            ],
            "wave": WAVE_TAG,
        },
    },
    # -------------------------------------------------------------------
    # P1 — 7 modern free-will / patristics scholars
    # -------------------------------------------------------------------
    {
        "node_id": "scholar_stump_e",
        "label": "Eleonore Stump",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Philosophe américaine (née 1947), Robert J. Henle Professor "
            "of Philosophy à Saint Louis University. Spécialiste majeure "
            "de Thomas d'Aquin en philosophie analytique. Ouvrages "
            "centraux : Aquinas (Routledge 2003), traité systématique "
            "couvrant métaphysique, théorie de la connaissance, action "
            "humaine et libre arbitre thomistes ; Wandering in Darkness: "
            "Narrative and the Problem of Suffering (Oxford University "
            "Press 2010), théodicée narrative ; Atonement (OUP 2018). "
            "Position : compatibilisme théologique, libre arbitre comme "
            "auto-détermination rationnelle compatible avec la grâce "
            "efficace augustino-thomiste."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Stump",
            "given_names": "Eleonore",
            "birth_date": "1947",
            "affiliations": ["Saint Louis University"],
            "specialty": "Philosophy of religion, Aquinas studies, free will, analytic theology",
            "key_works": [
                "Aquinas (Routledge 2003)",
                "Wandering in Darkness (OUP 2010)",
                "Atonement (OUP 2018)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_vargas_m",
        "label": "Manuel Vargas",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Philosophe américain (né 1971), professeur de philosophie à "
            "UC San Diego. Auteur de Building Better Beings: A Theory of "
            "Moral Responsibility (Oxford University Press 2013), qui "
            "défend une approche révisionniste du libre arbitre et de la "
            "responsabilité morale : nos pratiques de responsabilité "
            "doivent être conservées pour leur fonction sociale de "
            "régulation comportementale, même si la métaphysique "
            "ordinaire qui les sous-tend (libre arbitre libertarien) est "
            "fausse. Position : révisionnisme naturaliste, hériter "
            "contemporain de la stratégie strawsonienne."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Vargas",
            "given_names": "Manuel",
            "birth_date": "1971",
            "affiliations": ["UC San Diego"],
            "specialty": "Free will, moral responsibility, philosophy of agency, Latin American philosophy",
            "key_works": [
                "Building Better Beings (OUP 2013)",
                "Four Views on Free Will (Blackwell 2007, co-author)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_timpe_k",
        "label": "Kevin Timpe",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Philosophe américain (né 1972), William H. Jellema Chair in "
            "Christian Philosophy à Calvin University. Défenseur d'un "
            "libertarianisme vertueux (« virtue libertarianism ») : Free "
            "Will in Philosophical Theology (Bloomsbury 2013). Éditeur de "
            "Free Will and Theism (Oxford University Press 2016) et du "
            "Routledge Companion to Free Will (Routledge 2016). Travaux "
            "sur la disability theology et la philosophie chrétienne "
            "analytique."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Timpe",
            "given_names": "Kevin",
            "birth_date": "1972",
            "affiliations": ["Calvin University"],
            "specialty": "Free will, philosophical theology, virtue ethics, disability theology",
            "key_works": [
                "Free Will in Philosophical Theology (Bloomsbury 2013)",
                "Free Will and Theism (OUP 2016, ed.)",
                "Routledge Companion to Free Will (Routledge 2016, ed.)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_plantinga_a",
        "label": "Alvin Plantinga",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Philosophe américain (né 1932), professeur émérite à "
            "l'Université Notre Dame, figure majeure de la philosophie "
            "analytique de la religion. Auteur de la Free Will Defence "
            "dans God, Freedom, and Evil (Eerdmans 1977), reformulation "
            "logique de la théodicée du libre arbitre s'appuyant sur "
            "l'idée de mondes possibles : Dieu ne pouvait actualiser un "
            "monde contenant à la fois liberté libertarienne et absence "
            "de mal moral, car cela dépend des choix contrefactuels des "
            "créatures libres. Autres ouvrages : The Nature of Necessity "
            "(OUP 1974), Warrant and Proper Function (OUP 1993), Warranted "
            "Christian Belief (OUP 2000). Position : libertarianisme + "
            "épistémologie réformée."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Plantinga",
            "given_names": "Alvin",
            "birth_date": "1932",
            "affiliations": ["University of Notre Dame (emeritus)"],
            "specialty": "Philosophy of religion, modal metaphysics, epistemology, free will",
            "key_works": [
                "God, Freedom, and Evil (Eerdmans 1977)",
                "The Nature of Necessity (OUP 1974)",
                "Warranted Christian Belief (OUP 2000)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_tieleman_t",
        "label": "Teun Tieleman",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Historien de la philosophie hellénistique néerlandais (né "
            "1962), professeur à l'Université d'Utrecht. Spécialiste "
            "majeur de Chrysippe et du stoïcisme moyen. Auteur de "
            "Chrysippus' On Affections: Reconstruction and Interpretation "
            "(Brill, Philosophia Antiqua 94, 2003), reconstruction "
            "philologique systématique du Περὶ παθῶν perdu à partir des "
            "citations galéniques de De Placitis Hippocratis et Platonis. "
            "Précédé de Galen and Chrysippus on the Soul: Argument and "
            "Refutation in the De Placitis Books II-III (Brill, "
            "Philosophia Antiqua 68, 1996)."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Tieleman",
            "given_names": "Teun",
            "birth_date": "1962",
            "affiliations": ["Universiteit Utrecht"],
            "specialty": "Hellenistic philosophy, Stoicism, Chrysippus, Galen",
            "key_works": [
                "Galen and Chrysippus on the Soul — PhA 68 (Brill 1996)",
                "Chrysippus' On Affections — PhA 94 (Brill 2003)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_danielou_j",
        "label": "Jean Daniélou",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Patristicien jésuite français (1905-1974), cardinal, membre "
            "de l'Académie française (1972). Pionnier français de la "
            "patristique alexandrine et de la théologie biblique "
            "patristique. Ouvrages pivots : Origène (Le Génie du "
            "Christianisme, Paris : La Table Ronde 1948), première grande "
            "synthèse française moderne sur Origène ; Sacramentum futuri : "
            "études sur les origines de la typologie biblique "
            "(Beauchesne 1950) ; Théologie du judéo-christianisme "
            "(Desclée 1958 ; rééd. Cerf 1991). Co-fondateur de la "
            "collection Sources Chrétiennes (Cerf 1942) avec Henri de "
            "Lubac, infrastructure éditoriale fondamentale du KG."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Daniélou",
            "given_names": "Jean",
            "birth_date": "1905",
            "death_date": "1974",
            "affiliations": [
                "Institut Catholique de Paris",
                "Society of Jesus",
                "Académie française",
            ],
            "specialty": "Alexandrian patristics, Origen, biblical typology, Judeo-Christianity",
            "key_works": [
                "Origène (La Table Ronde 1948)",
                "Sacramentum futuri (Beauchesne 1950)",
                "Théologie du judéo-christianisme (Desclée 1958)",
                "Sources Chrétiennes — co-fondateur (Cerf 1942)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "scholar_jacobsen_a",
        "label": "Anders-Christian Jacobsen",
        "type": "person",
        "period": "Contemporary",
        "school": None,
        "description": (
            "Patristicien danois (né 1962), professeur de théologie à "
            "Aarhus Universitet. Spécialiste d'Origène et de "
            "l'anthropologie patristique. Ouvrage central : Christ — the "
            "Teacher of Salvation: A Study on Origen's Christology and "
            "Soteriology (Aschendorff, Adamantiana 6, 2015). Directeur "
            "de Universal Salvation: The Current Debate (Cambridge "
            "University Press 2019). Travaux sur la liberté humaine et "
            "la pédagogie divine chez Origène et dans la patristique "
            "grecque."
        ),
        "alternative_names": [],
        "metadata": {
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Jacobsen",
            "given_names": "Anders-Christian",
            "birth_date": "1962",
            "affiliations": ["Aarhus Universitet"],
            "specialty": "Origen, patristic anthropology, soteriology",
            "key_works": [
                "Christ — the Teacher of Salvation (Aschendorff 2015)",
                "Universal Salvation: The Current Debate (CUP 2019, ed.)",
            ],
            "wave": WAVE_TAG,
        },
    },
    # -------------------------------------------------------------------
    # P1 — 3 ancient persons
    # -------------------------------------------------------------------
    {
        "node_id": "person_apuleius_madauros_124_170",
        "label": "Apulée de Madaure",
        "type": "person",
        "period": "Roman Imperial",
        "school": "Middle Platonism",
        "description": (
            "Rhéteur, romancier et philosophe platonisant africain "
            "(c. 124-c. 170 CE). Auteur de l'Apologie (Pro se de magia) "
            "et des Métamorphoses (Asinus aureus). Pour le KG : le De "
            "Platone et eius dogmate constitue un manuel doxographique "
            "Middle Platonist de référence sur la providence, le destin, "
            "les démons et le libre arbitre — proche du Didaskalikos "
            "d'Alcinoos pour la structure tripartite providence / "
            "deuxième providence / fate. Le De Deo Socratis complète "
            "cette démonologie médiateur. Éditions critiques : Beaujeu, "
            "Apulée, Opuscules philosophiques et fragments (Budé 1973, "
            "réimpr. Belles Lettres) ; Moreschini, Apulei Platonici "
            "Madaurensis Opera (Teubner 1991, vol. III)."
        ),
        "alternative_names": [
            "Apuleius Madaurensis",
            "Lucius Apuleius",
        ],
        "metadata": {
            "birth_date": "c. 124 CE",
            "death_date": "c. 170 CE",
            "editions": [
                "Beaujeu — Budé (Belles Lettres 1973)",
                "Moreschini — Teubner (1991)",
            ],
            "key_works": [
                "De Platone et eius dogmate",
                "De Deo Socratis",
                "Apologia (Pro se de magia)",
                "Metamorphoses (Asinus aureus)",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_philoponus_johannes_490_570",
        "label": "Jean Philopon",
        "type": "person",
        "period": "Late Antiquity",
        "school": None,
        "description": (
            "Commentateur alexandrin du VIe siècle (c. 490-c. 570), "
            "chrétien miaphysite, élève d'Ammonius fils d'Hermias. "
            "Auteur de commentaires majeurs sur Aristote (in De Anima, "
            "in Physica, in Meteorologica, in Analytica) — édités dans "
            "la grande Commentaria in Aristotelem Graeca (CAG, Berlin : "
            "Reimer 1882-1909). Critique de l'éternité du monde "
            "aristotélicien : De Aeternitate Mundi contra Proclum (éd. "
            "Rabe, Teubner 1899) et le De Aeternitate Mundi contra "
            "Aristotelem (fragments). Pour le KG free-will : in De "
            "Anima III.4-8 sur νοῦς et autodétermination de l'âme "
            "rationnelle."
        ),
        "alternative_names": [
            "Ioannes Philoponus",
            "Ἰωάννης ὁ Φιλόπονος",
            "John the Grammarian",
        ],
        "metadata": {
            "birth_date": "c. 490 CE",
            "death_date": "c. 570 CE",
            "editions": [
                "CAG XIV-XVII (Reimer 1882-1909)",
                "Rabe, De Aeternitate Mundi contra Proclum (Teubner 1899)",
            ],
            "key_works": [
                "In De Anima (CAG XV)",
                "In Physica (CAG XVI-XVII)",
                "De Aeternitate Mundi contra Proclum",
                "De Aeternitate Mundi contra Aristotelem",
            ],
            "wave": WAVE_TAG,
        },
    },
    {
        "node_id": "person_cyril_jerusalem_315_386",
        "label": "Cyrille de Jérusalem",
        "type": "person",
        "period": "Patristic",
        "school": None,
        "description": (
            "Évêque de Jérusalem c. 350-386. Auteur des Catecheses "
            "(Catéchèses prébaptismales + Catéchèses mystagogiques), "
            "documents pédagogiques fondateurs de l'initiation "
            "chrétienne. Pour le libre arbitre : Catechesis IV traite "
            "explicitement de la liberté et de la providence ; "
            "Catechesis XIII développe une argumentation anti-fataliste "
            "anti-astrologique. Éditions critiques : Reischl & Rupp, "
            "Cyrilli Hierosolymorum archiepiscopi Opera quae supersunt "
            "omnia (Munich 1848-1860, 2 vol., texte de référence) ; "
            "PG 33. Traductions françaises sous-collection SC : SC 126 "
            "(Catéchèses mystagogiques, éd. Piédagnel 1966) ; SC 384 "
            "(Procatéchèse + Cat. I-IV, éd. Bouvet 1992)."
        ),
        "alternative_names": [
            "Cyrillus Hierosolymitanus",
            "Κύριλλος Ἱεροσολύμων",
        ],
        "metadata": {
            "birth_date": "c. 315 CE",
            "death_date": "386 CE",
            "episcopate": "c. 350-386 CE",
            "editions": [
                "Reischl & Rupp (Munich 1848-1860)",
                "PG 33",
                "SC 126 (Piédagnel 1966)",
                "SC 384 (Bouvet 1992)",
            ],
            "key_works": [
                "Catecheses (Procatéchèse + Cat. I-XVIII)",
                "Catecheses mystagogicae I-V",
            ],
            "wave": WAVE_TAG,
        },
    },
]


# ---------------------------------------------------------------------------
# Teacher-chain + school membership edge specs
# ---------------------------------------------------------------------------

# KG convention is ``student_of`` from student to teacher
# (no ``teaches`` inverse exists). See e.g.
# person_aristotle → student_of → person_plato.

TEACHER_EDGES: list[dict[str, str]] = [
    {
        # Chrysippe → maître de Diogène de Babylone
        "student": "person_diogenes_babylon_240_152bce",
        "teacher": "person_chrysippus_280_206bce_i9j0k1l2",
        "chain": "middle_stoa",
    },
    {
        # Diogène de Babylone → maître de Panétius
        "student": "person_panaetius_rhodes_185_109bce",
        "teacher": "person_diogenes_babylon_240_152bce",
        "chain": "middle_stoa",
    },
    {
        # Panétius → maître de Posidonius
        "student": "person_posidonius_apameia_135_51bce",
        "teacher": "person_panaetius_rhodes_185_109bce",
        "chain": "middle_stoa",
    },
    {
        # Clitomaque → maître de Philon de Larissa
        "student": "person_philo_larissa_159_84bce",
        "teacher": "person_clitomachus_of_carthage_7l2m4o10",
        "chain": "new_academy",
    },
]


SCHOOL_EDGES: list[dict[str, str]] = [
    {"person": "person_panaetius_rhodes_185_109bce", "school": "school_stoics"},
    {"person": "person_diogenes_babylon_240_152bce", "school": "school_stoics"},
    {"person": "person_philo_larissa_159_84bce", "school": "school_academics"},
    {
        "person": "person_apuleius_madauros_124_170",
        "school": "school_middle_platonism",
    },
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
# Node construction
# ---------------------------------------------------------------------------


def build_node(spec: dict[str, Any]) -> dict[str, Any]:
    """Convert a PERSONS spec into a KG node dict matching existing schema.

    The existing schema stores ``alternative_names`` as a JSON-encoded
    string and ``metadata`` as a JSON-encoded string. Field order
    follows the dominant convention (alphabetic-ish with ``id`` /
    ``node_id`` paired).
    """
    nid = spec["node_id"]
    alt = spec.get("alternative_names") or []
    if not isinstance(alt, list):
        raise TypeError(f"alternative_names must be a list, got {type(alt).__name__}")

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
        "role": "scholar" if nid.startswith("scholar_") else None,
        "school": spec.get("school"),
        "type": spec.get("type", "person"),
        "updated_at": NOW_ISO,
    }


def build_edge(
    source: str,
    relation: str,
    target: str,
    metadata: dict[str, Any],
    weight: float = 0.95,
) -> dict[str, Any]:
    """Construct an edge dict matching existing schema."""
    import uuid

    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e.get("source") or "", e.get("relation") or "", e.get("target") or "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-e] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id: dict[str, dict[str, Any]] = {node_id(n): n for n in nodes}
    edges_signatures: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    persons_added = 0
    persons_skipped_existing = 0
    doctorat_refs_found = 0

    for spec in PERSONS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            persons_skipped_existing += 1
            print(f"[skip] {nid} already present")
            continue

        new_node = build_node(spec)
        nodes.append(new_node)
        nodes_by_id[nid] = new_node
        persons_added += 1

        md_raw = new_node["metadata"]
        if isinstance(md_raw, str) and "local_path_hint" in md_raw:
            doctorat_refs_found += 1

    teacher_edges_added = 0
    for tspec in TEACHER_EDGES:
        student = tspec["student"]
        teacher = tspec["teacher"]
        chain = tspec["chain"]

        if student not in nodes_by_id:
            print(f"[teacher] skip: student {student} not present")
            continue
        if teacher not in nodes_by_id:
            print(f"[teacher] skip: teacher {teacher} not present")
            continue

        sig = (student, "student_of", teacher)
        if sig in edges_signatures:
            print(f"[teacher] skip: {student} --student_of--> {teacher} already exists")
            continue

        e = build_edge(
            source=student,
            relation="student_of",
            target=teacher,
            metadata={
                "wave": WAVE_TAG,
                "teacher_chain": chain,
                "source": "biographical_tradition",
            },
            weight=0.95,
        )
        edges.append(e)
        edges_signatures.add(sig)
        teacher_edges_added += 1
        print(f"[teacher] add: {student} --student_of--> {teacher} ({chain})")

    school_member_edges_added = 0
    for sspec in SCHOOL_EDGES:
        person = sspec["person"]
        school = sspec["school"]

        if person not in nodes_by_id:
            print(f"[school] skip: person {person} not present")
            continue
        if school not in nodes_by_id:
            print(f"[school] skip: school {school} not present (no node)")
            continue

        sig = (person, "member_of", school)
        if sig in edges_signatures:
            print(f"[school] skip: {person} --member_of--> {school} already exists")
            continue

        e = build_edge(
            source=person,
            relation="member_of",
            target=school,
            metadata={
                "wave": WAVE_TAG,
                "source": "doxographic_tradition",
            },
            weight=1.0,
        )
        edges.append(e)
        edges_signatures.add(sig)
        school_member_edges_added += 1
        print(f"[school] add: {person} --member_of--> {school}")

    if persons_added or teacher_edges_added or school_member_edges_added:
        write_nodes(nodes)
        write_edges(edges)
        print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")
    else:
        print("[write] no changes — files untouched")

    print()
    print(
        f"[wave-e] persons_added={persons_added}  persons_skipped_existing={persons_skipped_existing}"
    )
    print(
        f"[wave-e] teacher_edges_added={teacher_edges_added}  "
        f"school_member_edges_added={school_member_edges_added}"
    )
    print(f"[wave-e] doctorat_refs_found={doctorat_refs_found}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
