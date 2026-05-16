#!/usr/bin/env python3
"""Wave G — Schools & factions — 2026-05-16.

Add 10 missing organizational nodes:

* 5 philosophical schools (type=school):
  - school_cynics  (Antisthène/Diogène/Cratès)
  - school_megarians  (Euclide/Eubulide/Stilpon/Diodore Cronos)
  - school_academy_old  (Speusippe/Xénocrate/Polémon/Cratès)
  - school_academy_middle  (Arcésilas, Lacydès, transition Carnéade)
  - school_cyrenaics  (Aristippe, Théodore l'Athée, Hégésias)

* 5 theological factions (type=group):
  - group_pelagians           (Pélage, Caelestius, Julien d'Éclane)
  - group_anti_pelagians      (Augustin, Prosper)
  - group_semi_pelagians      (Cassien, Faustus, Vincent de Lérins)
  - group_monothelites        (Sergius, Pyrrhus, Macaire — added Wave K)
  - group_dyothelites         (Maxime, Sophrone, Martin Ier — Wave K)

After insertion, wire ``member_of`` edges from existing person nodes
to each new school/group. Persons that don't yet exist in the KG
(Pyrrhus, Sergius, Sophrone, Martin Ier, etc.) are deferred to
Wave K and counted under ``skipped_member_edges``.

Idempotent: rerun = no-op.
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

WAVE_TAG = "wave_g_schools_factions_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Node specs
# ---------------------------------------------------------------------------


SCHOOLS: list[dict[str, Any]] = [
    {
        "node_id": "school_cynics",
        "type": "school",
        "label": "École cynique",
        "alternative_names": ["Cyniques", "Cynics", "κυνικοί"],
        "period": "Classical Greek",
        "description": (
            "École fondée par Antisthène d'Athènes (vers 445-365 av. J.-C.), "
            "élève de Socrate, et radicalisée par Diogène de Sinope (vers "
            "412/404-323 av. J.-C.). Doctrine de l'αὐτάρκεια (autarcie) "
            "et ascèse vertueuse contre les conventions sociales (νόμος vs "
            "φύσις). Pas d'enseignement systématique sur le libre arbitre, "
            "mais le socle conceptuel direct du stoïcisme : Zénon de Citium "
            "fut élève de Cratès le cynique (élève de Diogène). La transmission "
            "Diogène → Cratès → Zénon → Cléanthe → Chrysippe est la chaîne "
            "fondatrice du Portique. Sources : Diogène Laërce VI (édition "
            "Marcovich, Teubner 1999 ; LCL 184 Hicks 1925) ; Goulet-Cazé, "
            "*Le Cynisme, une philosophie antique* (Vrin 2017)."
        ),
        "metadata": {
            "founded": "c. 4th century BCE (Antisthenes/Diogenes)",
            "location": "Athens",
            "key_figures": [
                "Antisthenes",
                "Diogenes of Sinope",
                "Crates of Thebes",
                "Hipparchia",
            ],
            "free_will_relevance": (
                "Indirect — pre-Stoic ascetic substrate (Diogène → Cratès → "
                "Zénon de Citium)"
            ),
            "editions": [
                "Marcovich, Diogenes Laertius — Teubner BSGRT (1999)",
                "Hicks, Diogenes Laertius — LCL 184-185 (Harvard UP 1925)",
                "Goulet-Cazé, Le Cynisme, une philosophie antique (Vrin 2017)",
            ],
        },
    },
    {
        "node_id": "school_megarians",
        "type": "school",
        "label": "École mégarique",
        "alternative_names": [
            "Mégariques",
            "Megarians",
            "Μεγαρικοί",
            "École de Mégare",
        ],
        "period": "Classical Greek",
        "description": (
            "École fondée par Euclide de Mégare (vers 435-365 av. J.-C.), élève "
            "de Socrate. Eubulide d'Alexandrie (paradoxes : Sorite, Cornu, "
            "Menteur), Stilpon (maître de Zénon de Citium avant Cratès), "
            "Diodore Cronos (Master Argument, modalités temporelles). Le "
            "Master Argument de Diodore Cronos (D. L. VII.16-19 ; Épictète "
            "II.19) — qui démontre l'incompatibilité de trois propositions "
            "modales — est l'origine de toute la discussion hellénistique "
            "sur la nécessité, les futurs contingents et l'εἱμαρμένη. "
            "Sources : Döring, *Die Megariker. Kommentierte Sammlung der "
            "Testimonien* (Grüner 1972) ; SSR (Giannantoni, *Socraticorum "
            "Reliquiae*, Naples 1983-1985, 4 vol.) ; Bobzien, *Die "
            "stoische Modallogik* (Königshausen 1986)."
        ),
        "metadata": {
            "founded": "c. early 4th century BCE",
            "location": "Megara",
            "key_figures": [
                "Euclides of Megara",
                "Eubulides",
                "Stilpon",
                "Diodorus Cronus",
                "Philo the Dialectician",
            ],
            "free_will_relevance": (
                "Foundational — Diodorus' Master Argument is the origin of "
                "Hellenistic modal-fate debate"
            ),
            "editions": [
                "Döring, Die Megariker — Studien zur antiken Philosophie 2 (Grüner 1972)",
                "Giannantoni, Socraticorum Reliquiae I-IV (Naples 1983-1985)",
                "Bobzien, Die stoische Modallogik (Königshausen 1986)",
            ],
        },
    },
    {
        "node_id": "school_academy_old",
        "type": "school",
        "label": "Ancienne Académie",
        "alternative_names": [
            "Vieille Académie",
            "Old Academy",
            "Académie ancienne",
        ],
        "period": "Classical Greek",
        "description": (
            "Académie platonicienne post-mortem 347 av. J.-C., direction "
            "successive de Speusippe (347-339), Xénocrate (339-314), Polémon "
            "(314-269/8), Cratès d'Athènes (269/8-c. 264). Dogmatisme "
            "platonicien systématisé : métaphysique des Idées-Nombres "
            "(Speusippe, Xénocrate), théologie cosmique. Préfigure le "
            "Moyen-Platonisme. Pour le free-will : peu de traces directes "
            "mais antécédents conceptuels via le commentaire du Timée "
            "(providence + nécessité + démiurge). Édition fragments : Lang, "
            "*De Speusippi Academici scriptis* (Bonn 1911) ; Heinze, "
            "*Xenocrates* (Teubner 1892) ; Isnardi Parente, *Speusippo: "
            "Frammenti* (Naples 1980) ; *Senocrate-Ermodoro: Frammenti* "
            "(Naples 1981 ; rééd. Olschki 2012)."
        ),
        "metadata": {
            "founded": "347 BCE (after Plato's death)",
            "location": "Athens",
            "scholarchs_chronology": [
                "Speusippus (347-339 BCE)",
                "Xenocrates (339-314 BCE)",
                "Polemon (314-269/8 BCE)",
                "Crates of Athens (269/8-c. 264 BCE)",
            ],
            "free_will_relevance": (
                "Indirect — providential cosmology + Timaeus exegesis "
                "preluding Middle Platonism"
            ),
            "editions": [
                "Lang, De Speusippi Academici scriptis (Bonn 1911)",
                "Heinze, Xenocrates (Teubner 1892)",
                "Isnardi Parente, Speusippo: Frammenti (Naples 1980)",
                "Isnardi Parente, Senocrate-Ermodoro: Frammenti (Naples 1981, rééd. Olschki 2012)",
            ],
        },
    },
    {
        "node_id": "school_academy_middle",
        "type": "school",
        "label": "Académie moyenne (sceptique)",
        "alternative_names": [
            "Middle Academy",
            "New Academy (early phase)",
            "Académie sceptique d'Arcésilas",
        ],
        "period": "Hellenistic",
        "description": (
            "Phase sceptique de l'Académie inaugurée par Arcésilas de Pitané "
            "(scolarque c. 268-241 av. J.-C.). Rupture avec le dogmatisme de "
            "l'Ancienne Académie : suspension du jugement (ἐποχή), critique "
            "systématique de la καταληπτικὴ φαντασία stoïcienne. Continuée par "
            "Lacydès, puis radicalisée par Carnéade (Nouvelle Académie, "
            "scolarque c. 155-129 av. J.-C.). Pour le free-will : "
            "l'argumentation anti-stoïcienne d'Arcésilas (cf. Cicéron "
            "*Academica*) prépare la critique carnéadienne du destin (cf. "
            "Cicéron *De Fato*). Sources : Long & Sedley LS 68-70 ; "
            "Brittain, *Philo of Larissa: The Last of the Academic "
            "Sceptics* (OUP 2001) ; Mette, *Lustrum* 26-27 (1984-1985)."
        ),
        "metadata": {
            "founded": "c. 268 BCE (Arcesilaus' scholarchate)",
            "location": "Athens",
            "scholarchs_chronology": [
                "Arcesilaus of Pitane (c. 268-241 BCE)",
                "Lacydes of Cyrene (c. 241-215 BCE)",
                "Telecles + Evander (joint, c. 215-167 BCE)",
                "Hegesinus (c. 160-155 BCE)",
            ],
            "key_doctrines": [
                "ἐποχή (suspension of judgement)",
                "Anti-Stoic critique of καταληπτικὴ φαντασία",
            ],
            "free_will_relevance": (
                "Foundational — Arcesilaus prepares Carneades' anti-fatalist "
                "argumentation (Cicero, De Fato + Academica)"
            ),
            "editions": [
                "Long & Sedley, The Hellenistic Philosophers I-II (Cambridge UP 1987) — sections 68-70",
                "Brittain, Philo of Larissa: The Last of the Academic Sceptics (OUP 2001)",
                "Mette, 'Weitere Akademiker heute', Lustrum 26-27 (1984-1985)",
            ],
        },
    },
    {
        "node_id": "school_cyrenaics",
        "type": "school",
        "label": "École cyrénaïque",
        "alternative_names": ["Cyrenaics", "Κυρηναϊκοί"],
        "period": "Classical Greek",
        "description": (
            "École hédoniste fondée par Aristippe de Cyrène (vers 435-355 av. "
            "J.-C.), élève de Socrate. Aristippe le Jeune (petit-fils), "
            "Théodore l'Athée, Hégésias, Anniceris. Doctrine : le plaisir "
            "corporel actuel (ἡδονή ἐν κινήσει) est l'unique bien ; le passé "
            "et le futur sont indifférents. Pour le free-will : peu de traces "
            "directes, mais contraste utile avec l'épicurisme hédoniste "
            "ataraxique. Fragments : Mannebach, *Aristippi et Cyrenaicorum "
            "fragmenta* (Brill 1961) ; SSR IV (Giannantoni 1990)."
        ),
        "metadata": {
            "founded": "c. early 4th century BCE",
            "location": "Cyrene (later Athens)",
            "key_figures": [
                "Aristippus of Cyrene",
                "Aristippus the Younger",
                "Theodorus the Atheist",
                "Hegesias",
                "Anniceris",
            ],
            "key_doctrines": [
                "ἡδονή ἐν κινήσει (kinetic pleasure)",
                "Present-only temporal hedonism",
            ],
            "free_will_relevance": (
                "Indirect — counterpoint to Epicurean ataraxic hedonism"
            ),
            "editions": [
                "Mannebach, Aristippi et Cyrenaicorum fragmenta (Brill 1961)",
                "Giannantoni, Socraticorum Reliquiae IV (Naples 1990)",
            ],
        },
    },
]


GROUPS: list[dict[str, Any]] = [
    {
        "node_id": "group_pelagians",
        "type": "group",
        "label": "Pélagiens",
        "alternative_names": ["Pelagians", "Pelagiani"],
        "period": "Patristic",
        "description": (
            "Mouvement théologique fondé par Pélage (Pelagius, c. 354-c. 420/430 "
            "ap. J.-C.), moine breton/irlandais arrivé à Rome c. 380. Doctrine : "
            "libre arbitre intact post-lapsum, péché originel par imitation et "
            "non par transmission, baptême des enfants non-rémissif, possibilité "
            "de l'impeccabilité par la grâce-révélation (et non par la grâce "
            "intrinsèquement opérante). Disciples principaux : Caelestius (qui "
            "radicalise la doctrine), Julien d'Éclane (qui en donne la défense "
            "philosophique la plus aboutie, 419-454). Condamnés au synode de "
            "Carthage 418, par Zosime *Tractoria* 418, et au concile d'Éphèse "
            "431. Sources primaires : PL 30 (Pélage) ; PL 45 (Julien) ; CSEL "
            "85.1+88 (Julien) ; *Œuvres* éditées par Vallarsi/Migne. "
            "Reconstruction moderne : Bonner, *Augustine and Modern Research "
            "on Pelagianism* (Villanova 1972) ; Rees, *Pelagius: A Reluctant "
            "Heretic* (Boydell 1988)."
        ),
        "metadata": {
            "period": "Patristic",
            "active_period": "c. 380-431 CE (formal) — survives in Britain through 5th c.",
            "key_figures": ["Pelagius", "Caelestius", "Julian of Eclanum"],
            "key_doctrines": [
                "Intact post-lapsarian free will",
                "Original sin by imitation, not transmission",
                "Possible impeccability via grace-as-revelation",
            ],
            "condemnations": [
                "Synod of Carthage 418",
                "Zosimus Tractoria 418",
                "Council of Ephesus 431",
            ],
            "editions": [
                "PL 30 (Pelagius opera) — Migne",
                "PL 45 (Julian opera) — Migne",
                "CSEL 85.1 + 88 (Julian, ed. De Bruyn / Bouhot)",
                "Bonner, Augustine and Modern Research on Pelagianism (Villanova 1972)",
                "Rees, Pelagius: A Reluctant Heretic (Boydell 1988)",
            ],
        },
    },
    {
        "node_id": "group_anti_pelagians",
        "type": "group",
        "label": "Anti-Pélagiens (Augustiniens stricts)",
        "alternative_names": [
            "Anti-Pelagians",
            "Augustinian strict-grace party",
        ],
        "period": "Patristic",
        "description": (
            "Faction théologique autour d'Augustin d'Hippone et de ses alliés "
            "africains et italiens (411-431) puis prosperians (431-455). "
            "Doctrine : grâce prévenante (gratia praeveniens), prédestination "
            "gratuite (gratia gratis data), incapacité radicale de l'arbitre "
            "post-lapsum (peccatum originale comme massa damnata, *De "
            "Correptione et Gratia* 7.16). Principaux porteurs : Augustin, "
            "Prosper d'Aquitaine, Possidius de Calame, Hilaire d'Arles "
            "(jusqu'à son virage semi-pélagien), Fulgence de Ruspe (VIe s.). "
            "Validés à Carthage 418 et Orange 529 (canons 4-7 sur la grâce "
            "prévenante). Sources primaires : CSEL 60 + CCSL 45 + BA 22-24 "
            "(Augustin) ; CCSL 68A (Prosper). Reconstruction : Lamberigts, "
            "*L'augustinisme à la croisée des chemins* (Brepols 2006)."
        ),
        "metadata": {
            "period": "Patristic",
            "active_period": "411-455 CE (Augustinian phase) + 6th c. (Fulgentius)",
            "key_figures": [
                "Augustine of Hippo",
                "Prosper of Aquitaine",
                "Possidius of Calama",
                "Fulgentius of Ruspe",
            ],
            "key_doctrines": [
                "Gratia praeveniens (preceding grace)",
                "Predestination gratuita (gratuitous predestination)",
                "Peccatum originale as massa damnata",
            ],
            "councils_validating": [
                "Carthage 418",
                "Orange II 529 (canons 4-7)",
            ],
            "editions": [
                "CSEL 60 (Augustine, anti-Pelagian) — Vienna",
                "CCSL 45 (Augustine) — Brepols",
                "BA 22-24 — Bibliothèque Augustinienne (Desclée)",
                "CCSL 68A (Prosper) — Brepols",
                "Lamberigts, L'augustinisme à la croisée des chemins (Brepols 2006)",
            ],
        },
    },
    {
        "node_id": "group_semi_pelagians",
        "type": "group",
        "label": "Semi-Pélagiens (Massilianes)",
        "alternative_names": [
            "Semi-Pelagians",
            "Massilianes",
            "Massiliani",
            "Initium fidei party",
        ],
        "period": "Patristic",
        "description": (
            "Mouvement modéré centré à Marseille et Lérins (425-529 ap. J.-C.). "
            "Cassien (Conlatio XIII), Vincent de Lérins (Commonitorium 434), "
            "Faustus de Riez (De gratia 474-475), et plus tard Gennade de "
            "Marseille. Doctrine : l'*initium fidei* (« départ de la foi ») "
            "vient du libre arbitre humain, la grâce qui suit développe ce "
            "premier mouvement (gratia subsequens contre gratia praeveniens). "
            "Position médiane entre Augustin et Pélage. Condamnés au concile "
            "d'Orange 529 sous Césaire d'Arles, dont les canons 4-7 et le "
            "Definitio fidei rappellent la nécessité de la grâce prévenante "
            "pour l'initium fidei lui-même. Sources : SC 42-42bis+54+64 "
            "(Cassien) ; CSEL 21+101 (Faustus, Vincent) ; reconstruction "
            "moderne : Weaver, *Divine Grace and Human Agency: A Study of "
            "the Semi-Pelagian Controversy* (Mercer 1996) ; Ogliari, "
            "*Gratia et Certamen* (Peeters 2003)."
        ),
        "metadata": {
            "period": "Patristic",
            "active_period": "425-529 CE",
            "location_principal": "Marseille (Saint-Victor) and Lérins",
            "key_figures": [
                "John Cassian",
                "Vincent of Lérins",
                "Faustus of Riez",
                "Gennadius of Marseille",
            ],
            "key_doctrines": [
                "Initium fidei from human free will",
                "Gratia subsequens (grace that follows)",
                "Mediating position between Augustine and Pelagius",
            ],
            "condemnations": ["Council of Orange II 529 (canons 4-7)"],
            "editions": [
                "Petschenig, CSEL 13 (Cassian Conlationes, Vienna 1886)",
                "Pichery, SC 42-42bis + 54 + 64 (Cassian, Cerf 1955-1959)",
                "CSEL 21 (Faustus) + CSEL 101 (Vincent, 2017)",
                "Weaver, Divine Grace and Human Agency (Mercer 1996)",
                "Ogliari, Gratia et Certamen (Peeters 2003)",
            ],
        },
    },
    {
        "node_id": "group_monothelites",
        "type": "group",
        "label": "Monothelites / Monoénergistes",
        "alternative_names": [
            "Monothelitism",
            "Monoenergism",
            "Monothelites",
            "μονοθεληταί",
        ],
        "period": "Late Antiquity",
        "description": (
            "Faction christologique impériale du VIIe siècle ap. J.-C., "
            "promue par Héraclius et le patriarche Sergius Ier de "
            "Constantinople (610-638) puis Pyrrhus, Paul II, Macaire "
            "d'Antioche. Doctrine en deux phases : (1) monoénergisme "
            "(Psephos 633 puis Ekthesis 638) — une seule énergie/opération "
            "(μία ἐνέργεια) en Christ ; (2) monothélisme — une seule "
            "volonté (ἓν θέλημα) après le repli sur le Typos de 648. "
            "Visait à réconcilier les miaphysites égyptiens et arméniens "
            "avec Chalcédoine. Opposé farouchement par Sophrone de "
            "Jérusalem, Maxime le Confesseur, le pape Martin Ier. "
            "Condamnés au synode du Latran 649 (sous Martin Ier) et "
            "définitivement au IIIe concile de Constantinople 681 (sous "
            "Constantin IV). Sources : ACO ser. II vol. I-II (Riedinger "
            "1984-1992) ; PG 91 (Maxime *Disputatio cum Pyrrho*)."
        ),
        "metadata": {
            "period": "Late Antiquity",
            "active_period": "c. 633-681 CE",
            "location_principal": "Constantinople / Alexandria / Antioch",
            "key_figures": [
                "Sergius I of Constantinople",
                "Pyrrhus of Constantinople",
                "Paul II of Constantinople",
                "Cyrus of Alexandria",
                "Macarius of Antioch",
                "Heraclius (emperor)",
            ],
            "key_doctrines": [
                "Monoenergism — one energy/operation (μία ἐνέργεια) in Christ",
                "Monothelitism — one will (ἓν θέλημα) in Christ",
            ],
            "imperial_edicts": [
                "Psephos 633 (Sergius)",
                "Ekthesis 638 (Heraclius)",
                "Typos 648 (Constans II)",
            ],
            "condemnations": [
                "Lateran Synod 649 (Pope Martin I)",
                "Constantinople III 681 (Ecumenical Council VI)",
            ],
            "editions": [
                "ACO ser. II vol. I-II — Riedinger (de Gruyter 1984-1992)",
                "PG 91 (Maximus, Disputatio cum Pyrrho)",
            ],
        },
    },
    {
        "node_id": "group_dyothelites",
        "type": "group",
        "label": "Dyothelites",
        "alternative_names": [
            "Dyothelitism",
            "Dyoenergism",
            "δυοθεληταί",
            "Two-wills party",
        ],
        "period": "Late Antiquity",
        "description": (
            "Faction christologique orthodoxe défendant la dyenergie et la "
            "dyothélie en Christ : deux énergies/opérations (δύο ἐνέργειαι) "
            "et deux volontés (δύο θελήματα), une divine et une humaine, "
            "unies sans confusion ni séparation. Principaux porteurs : "
            "Sophrone de Jérusalem (Synodica 634, condamnant le "
            "monoénergisme), Maxime le Confesseur (Opuscula theologica et "
            "polemica, *Disputatio cum Pyrrho* 645), pape Martin Ier "
            "(Latran 649), Anastase le Sinaïte (*Hodegos*), patriarche "
            "Georges Ier de Constantinople (rallié 681). Maxime distingue "
            "θέλημα φυσικόν (volonté naturelle, capacité de la nature, "
            "libre) et θέλημα γνωμικόν (volonté gnomique, mode délibératif "
            "marqué par l'ignorance/péché, absent en Christ). Doctrine "
            "consacrée à Constantinople III 681 (canon 7). Sources : PG 91 "
            "(Maxime) ; ACO ser. II ; édition Janssens, *Maximus the "
            "Confessor: Opuscula* (CCSG en cours)."
        ),
        "metadata": {
            "period": "Late Antiquity",
            "active_period": "c. 634-681 CE",
            "location_principal": "Jerusalem / Africa / Rome",
            "key_figures": [
                "Sophronius of Jerusalem",
                "Maximus the Confessor",
                "Pope Martin I",
                "Anastasius of Sinai",
                "George I of Constantinople",
            ],
            "key_doctrines": [
                "Dyenergy — two energies (δύο ἐνέργειαι) in Christ",
                "Dyothelitism — two wills (δύο θελήματα) in Christ",
                "θέλημα φυσικόν vs θέλημα γνωμικόν (Maximus)",
            ],
            "councils_validating": [
                "Lateran Synod 649",
                "Constantinople III 681 (canon 7)",
            ],
            "editions": [
                "PG 91 (Maximus, Opuscula + Disputatio)",
                "ACO ser. II — Riedinger (de Gruyter 1984-1992)",
                "Janssens, Maximus the Confessor: Opuscula — CCSG (Brepols, en cours)",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# member_of edges — (existing-person-id, school/group-id)
# Person ids verified via pre-flight scan of nodes.jsonl on 2026-05-16.
# Persons not yet in KG (Pyrrhus/Sergius/Sophrone/Martin Ier/etc.) are
# deferred to Wave K and absent from this list.
# ---------------------------------------------------------------------------


MEMBER_EDGES: list[tuple[str, str, str]] = [
    # Schools
    ("person_diodorus_cronus_48ef6200", "school_megarians", "founder/transmitter"),
    ("person_arcesilaus_316_241bce", "school_academy_middle", "scholarch/founder"),
    # Groups (Pelagian / anti-Pelagian / Semi-Pelagian factions)
    ("person_pelagius_d420", "group_pelagians", "founder"),
    ("person_julian_eclanum_d454", "group_pelagians", "leading defender"),
    ("person_augustine_hippo_d430", "group_anti_pelagians", "founder"),
    ("person_prosper_aquitaine_d455", "group_anti_pelagians", "leading disciple"),
    ("person_john_cassian_d435", "group_semi_pelagians", "founder"),
    ("person_faustus_riez_d495", "group_semi_pelagians", "leading defender"),
    ("person_maximus_confessor_d662", "group_dyothelites", "principal theologian"),
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


def get_node_id(n: dict[str, Any]) -> str:
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
# Node + edge construction
# ---------------------------------------------------------------------------


def build_org_node(spec: dict[str, Any]) -> dict[str, Any]:
    """Build a school/group KG node matching existing schema.

    Schema sample (`school_academics`, `group_essenes_e9f0g1h2`):
      ``alternative_names`` and ``metadata`` are JSON-encoded strings;
      ``period`` is a top-level field; ``school``, ``role`` are nullable.
    """
    nid: str = spec["node_id"]
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
        "role": None,
        "school": None,
        "type": spec["type"],
        "updated_at": NOW_ISO,
    }


def build_member_of_edge(
    person_id: str,
    org_id: str,
    role_note: str,
) -> dict[str, Any]:
    """``person → school|group`` member_of edge."""
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(
            {
                "wave": WAVE_TAG,
                "confidence": 0.95,
                "role_note": role_note,
            },
            ensure_ascii=False,
        ),
        "relation": "member_of",
        "source": person_id,
        "source_id": person_id,
        "target": org_id,
        "target_id": org_id,
        "weight": 1.0,
    }


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e.get("source") or "", e.get("relation") or "", e.get("target") or "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-g] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id: dict[str, dict[str, Any]] = {get_node_id(n): n for n in nodes}
    edges_signatures: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    schools_added = 0
    groups_added = 0
    nodes_skipped_existing = 0
    member_of_edges_added = 0
    member_edges_skipped_existing = 0
    member_edges_skipped_missing_person = 0

    # 1) Insert school nodes.
    for spec in SCHOOLS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            nodes_skipped_existing += 1
            print(f"[skip-school] {nid} already present")
            continue
        node = build_org_node(spec)
        nodes.append(node)
        nodes_by_id[nid] = node
        schools_added += 1
        print(f"[school] add: {nid}")

    # 2) Insert group nodes.
    for spec in GROUPS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            nodes_skipped_existing += 1
            print(f"[skip-group] {nid} already present")
            continue
        node = build_org_node(spec)
        nodes.append(node)
        nodes_by_id[nid] = node
        groups_added += 1
        print(f"[group] add: {nid}")

    # 3) Wire member_of edges.
    for person_id, org_id, role_note in MEMBER_EDGES:
        if org_id not in nodes_by_id:
            print(
                f"[member_of] skip: target org {org_id} missing — "
                "(should have been added above; check spec)"
            )
            member_edges_skipped_missing_person += 1
            continue
        if person_id not in nodes_by_id:
            print(f"[member_of] skip: person {person_id} not in KG (deferred to Wave K)")
            member_edges_skipped_missing_person += 1
            continue
        sig = (person_id, "member_of", org_id)
        if sig in edges_signatures:
            print(f"[member_of] skip: {person_id} --member_of--> {org_id} exists")
            member_edges_skipped_existing += 1
            continue
        edge = build_member_of_edge(person_id, org_id, role_note)
        edges.append(edge)
        edges_signatures.add(sig)
        member_of_edges_added += 1
        print(f"[member_of] add: {person_id} --member_of--> {org_id}")

    if schools_added or groups_added or member_of_edges_added:
        write_nodes(nodes)
        write_edges(edges)
        print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")
    else:
        print("[write] no changes — files untouched")

    print()
    print(f"[wave-g] schools_added={schools_added}  groups_added={groups_added}")
    print(
        f"[wave-g] nodes_skipped_existing={nodes_skipped_existing}  "
        f"member_of_edges_added={member_of_edges_added}  "
        f"member_edges_skipped_existing={member_edges_skipped_existing}  "
        f"member_edges_skipped_missing_person={member_edges_skipped_missing_person}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
