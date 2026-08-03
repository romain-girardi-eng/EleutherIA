#!/usr/bin/env python3
"""Wave F — Missing work nodes — 2026-05-16.

Add up to 17 missing work nodes flagged by the KG audit:

P0 (high-priority free-will sources):
  * 3 Plutarch / Pseudo-Plutarch works:
    - De Fato authentique (Lamprias 58, disputed)
    - De Stoicorum Repugnantiis
    - De Communibus Notitiis
  * Alexander of Aphrodisias, De Fato (standalone — checked
    against existing duplicate; ENRICH path chosen, see below)
  * 3 Second Temple Judaism collections:
    - Wisdom of Solomon (Sap.)
    - 4 Maccabees
    - Qumran Hodayot (1QH^a) — SKIPPED, existing
      ``work_dss_hodayot_i1j2k3l4`` covers it (description enriched
      with DJD critical-edition metadata)

P1 (Patristic + Aristote/Platon + Hellenistic-Roman):
  * Lactance, Divinarum Institutionum
  * Tertullien, De Anima — SKIPPED, exists
  * Augustin, Retractationes
  * Cassien, Conlatio XIII
  * Aristote, Éthique à Eudème — SKIPPED, exists
  * Platon, Sophiste
  * Théodoret, Graecarum Affectionum Curatio
  * Apulée, De Platone et eius dogmate
  * Cléanthe, Hymne à Zeus
  * Origène, De Oratione — SKIPPED, exists (Wave B touched metadata)

For each created node we also wire an ``authored_by`` edge to the
existing author person node (verified pre-flight: all 13 needed
author nodes exist).

Alexander De Fato: existing ``work_de_fato_alexander_c200ce_o6p7q8r9``
already has rich edition metadata (Bruns 1892 / Thillet 1984 / Sharples
1983) and dense Amand/Frede/Bobzien/Destrée annotations. Per spec, we
prefer enriching over creating new — we add ``language: grc``,
``cts_urn`` (already set), and an audit flag ``wave_f_canonical_id``
so downstream pipelines can resolve the spec's ``work_alexander_de_fato_standalone``
alias to the canonical id.

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

WAVE_TAG = "wave_f_missing_works_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")

# ---------------------------------------------------------------------------
# Pre-flight identifiers verified on 2026-05-16 against nodes.jsonl
# ---------------------------------------------------------------------------

AUTHOR_IDS: dict[str, str] = {
    "plutarch": "person_plutarch_45_120ce_b9c2a8f3",
    "pseudo_plutarch": "person_pseudo_plutarch_2c_ce",
    "alexander_aphrodisias": "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
    "lactantius": "person_lactantius_250_325ce",
    "tertullian": "person_tertullian_d220",
    "augustine": "person_augustine_hippo_d430",
    "cassian": "person_john_cassian_d435",
    "aristotle": "person_aristotle_384_322bce_c2d4f6a8",
    "plato": "person_plato_428_348bce_a1b2c3d4",
    "theodoret": "person_theodoret_cyrrhus_393_466ce",
    "apuleius": "person_apuleius_madauros_124_170",
    "cleanthes": "person_cleanthes_assos_330_230bce",
    "origen": "person_origen_alexandria_185_254ce_s9t0u1v2",
}

# Identifiers that already exist and should be skipped entirely.
SKIP_ALREADY_PRESENT: dict[str, str] = {
    "work_tertullian_de_anima": "exists (Wave-A or earlier ingestion)",
    "work_aristotle_eudemian_ethics": "exists (rich metadata)",
    "work_origen_de_oratione": "exists (Wave-B touched metadata)",
}

# Alias map: spec node_id → canonical existing id (no new node created).
ALIAS_TO_EXISTING: dict[str, str] = {
    "work_alexander_de_fato_standalone": "work_de_fato_alexander_c200ce_o6p7q8r9",
    "work_qumran_hodayot": "work_dss_hodayot_i1j2k3l4",
}


# ---------------------------------------------------------------------------
# Work specs (only specs that produce a NEW node)
# ---------------------------------------------------------------------------

WORKS: list[dict[str, Any]] = [
    # -------------------------------------------------------------------
    # P0 — Plutarch trio
    # -------------------------------------------------------------------
    {
        "node_id": "work_plutarch_de_fato_authentic",
        "label": "Plutarque, De Fato (authentique disputé)",
        "type": "work",
        "period": "Roman Imperial",
        "school": "Middle Platonism",
        "author_key": "plutarch",
        "description": (
            "Plutarque (?), *De Fato* (Περὶ εἱμαρμένης), Moralia 568b-574f. "
            "Bref traité épitomé doctrinal sur le destin, attribué dans le "
            "Catalogue de Lamprias (n° 58) à Plutarque de Chéronée mais dont "
            "l'authenticité est massivement contestée depuis Wyttenbach : "
            "statistiques de hiatus, divergences doctrinales (théorie de la "
            "providence-εἱμαρμένη comme âme du monde, hiérarchie des trois "
            "providences) et style philosophique scolaire pointent vers un "
            "Middle Platonist anonyme du IIᵉ siècle. Le KG conserve deux "
            "nœuds distincts : (a) ce nœud (``work_plutarch_de_fato_authentic``) "
            "réservé à l'hypothèse minoritaire d'authenticité plutarchéenne ; "
            "(b) ``work_plutarch_de_fato_complete`` qui consigne le consensus "
            "pseudépigraphique. Pour le KG free-will : argumentation classique "
            "Middle Platonist contre le déterminisme stoïcien total, défense "
            "d'un τὸ ἐφ' ἡμῖν résiduel + théorie de la providence hiérarchique. "
            "Édition critique : Hubert, *Plutarchi Moralia* III (Teubner BSGRT "
            "1929 — éd. mineure) ; pour le texte autonomement de Pseudo-Plutarque "
            "De Fato : Hubert, *Plutarchi Moralia* III (Teubner 1929) ; "
            "De Lacy & Einarson, *Moralia* VII, LCL 405 (Harvard 1959)."
        ),
        "alternative_names": ["Περὶ εἱμαρμένης (Lamprias 58)"],
        "metadata": {
            "cts_urn": "urn:cts:greekLit:tlg0007.tlg103",
            "language": "grc",
            "authenticity": "disputed",
            "lamprias_catalogue": "58",
            "moralia_pages": "568B-574F",
            "editions": [
                "Hubert, Plutarchi Moralia III (Teubner BSGRT 1929)",
                "De Lacy & Einarson, Moralia VII — LCL 405 (Harvard UP 1959)",
            ],
            "related_node": "work_plutarch_de_fato_complete",
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_plutarch_stoic_repugnantiis",
        "label": "Plutarque, De Stoicorum Repugnantiis",
        "type": "work",
        "period": "Roman Imperial",
        "school": "Middle Platonism",
        "author_key": "plutarch",
        "description": (
            "Plutarque de Chéronée, *De Stoicorum Repugnantiis* (Περὶ Στωϊκῶν "
            "ἐναντιωμάτων), Moralia 1033a-1057c. Critique systématique en 47 "
            "chapitres des contradictions internes du système chrysippéen. "
            "Source majeure — souvent la seule — pour la reconstruction de "
            "la doctrine stoïcienne du destin et de l'assentiment : "
            "Mor. 1056b-d (la comparaison du cylindre roulant et de l'âne), "
            "Mor. 1052c-d (sur l'ekpyrosis), Mor. 1052d-e (sur la συμπάθεια "
            "cosmique). Texte clef pour Bobzien 1998 (chap. 6 : reconstruction "
            "de la causalité chrysippéenne contre le déterminisme dur), "
            "Frede 2011 et tout le débat compatibilisme stoïcien. "
            "Le ton est polémique mais les citations directes de Chrysippe "
            "sont en général jugées fiables par les éditeurs de SVF. "
            "Éditions critiques : Pohlenz, *Plutarchi Moralia* VI.2 (Teubner "
            "BSGRT 1959, rééd. 1995) ; Cherniss, *Plutarch's Moralia* XIII.2 "
            "— LCL 470 (Harvard 1976)."
        ),
        "alternative_names": [
            "Περὶ Στωϊκῶν ἐναντιωμάτων",
            "On Stoic Self-Contradictions",
        ],
        "metadata": {
            "cts_urn": "urn:cts:greekLit:tlg0007.tlg152",
            "language": "grc",
            "lamprias_catalogue": "76",
            "moralia_pages": "1033A-1057C",
            "editions": [
                "Pohlenz, Plutarchi Moralia VI.2 (Teubner BSGRT 1959, rééd. 1995)",
                "Cherniss, Moralia XIII.2 — LCL 470 (Harvard UP 1976)",
            ],
            "key_passages": [
                "Mor. 1056b-d (cylindre)",
                "Mor. 1052c-d (ekpyrosis)",
                "Mor. 1052d-e (sympatheia)",
            ],
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_plutarch_de_communibus_notitiis",
        "label": "Plutarque, De Communibus Notitiis adversus Stoicos",
        "type": "work",
        "period": "Roman Imperial",
        "school": "Middle Platonism",
        "author_key": "plutarch",
        "description": (
            "Plutarque de Chéronée, *De Communibus Notitiis adversus Stoicos* "
            "(Περὶ τῶν κοινῶν ἐννοιῶν πρὸς τοὺς Στωϊκούς), Moralia 1058e-1086b. "
            "Pendant polémique du *De Stoicorum Repugnantiis*, structuré en "
            "85 sections. Plutarque y attaque la doctrine stoïcienne par "
            "l'arme dialectique des κοιναὶ ἔννοιαι (notions communes) : "
            "il prétend montrer que la physique, la cosmologie et l'éthique "
            "stoïciennes contreviennent aux préconceptions naturelles "
            "universellement partagées. Pour le KG free-will : Mor. 1075a-1077d "
            "concentre la critique du déterminisme stoïcien par les notions "
            "communes de responsabilité et de mérite ; Mor. 1076d-e sur le "
            "destin et la moralité. Le texte préserve nombreux fragments "
            "chrysippéens (SVF II, III). Éditions critiques : Pohlenz, "
            "*Plutarchi Moralia* VI.2 (Teubner BSGRT 1959, rééd. 1995) ; "
            "Cherniss, *Moralia* XIII.2 — LCL 470 (Harvard UP 1976)."
        ),
        "alternative_names": [
            "Περὶ τῶν κοινῶν ἐννοιῶν πρὸς τοὺς Στωϊκούς",
            "On Common Conceptions against the Stoics",
        ],
        "metadata": {
            "cts_urn": "urn:cts:greekLit:tlg0007.tlg153",
            "language": "grc",
            "lamprias_catalogue": "78",
            "moralia_pages": "1058E-1086B",
            "editions": [
                "Pohlenz, Plutarchi Moralia VI.2 (Teubner BSGRT 1959, rééd. 1995)",
                "Cherniss, Moralia XIII.2 — LCL 470 (Harvard UP 1976)",
            ],
            "key_passages": [
                "Mor. 1075a-1077d (notions communes vs déterminisme)",
                "Mor. 1076d-e (destin et moralité)",
            ],
            "needs_text_ingestion": True,
        },
    },
    # -------------------------------------------------------------------
    # P0 — Second Temple Judaism (Wisdom of Solomon + 4 Maccabees)
    # Hodayot skipped — existing work_dss_hodayot_i1j2k3l4 enriched separately.
    # -------------------------------------------------------------------
    {
        "node_id": "work_wisdom_of_solomon",
        "label": "Sagesse de Salomon (Σοφία Σαλωμῶνος)",
        "type": "work",
        "period": "Second Temple Judaism",
        "school": None,
        "author_key": None,  # pseudépigraphe — pas de personne réelle
        "description": (
            "*Sagesse de Salomon* (Σοφία Σαλωμῶνος ; Liber Sapientiae), "
            "livre deutérocanonique en grec composé à Alexandrie au IIᵉ-Iᵉʳ "
            "siècle av. J.-C., pseudépigraphe attribué à Salomon. Trois "
            "blocs majeurs pour le débat libre arbitre / providence : "
            "(1) Sap. 1-2 — discours de l'impie qui nie la providence et "
            "professe un hédonisme nihiliste (Sap. 2.1-9), suivi de "
            "l'argumentaire judéo-stoïcien sur l'immortalité ; (2) Sap. 7-9 "
            "— éloge poétique de la Sagesse comme πνεῦμα νοερόν régissant "
            "l'âme du juste qui choisit librement la vertu (Sap. 7.27-28, "
            "8.21) ; (3) Sap. 11-12 — thématique du πειρασμός pédagogique : "
            "Dieu châtie progressivement et pédagogiquement pour permettre "
            "la μετάνοια (Sap. 11.23-12.2, 12.10-22) — texte clé pour la "
            "tradition patristique grecque (Origène) sur la liberté humaine "
            "et la providence éducative. Texte canonique pour les Pères "
            "grecs (au contraire de la tradition rabbinique qui le rejette "
            "du canon hébraïque). Édition critique de référence : "
            "*Sapientia Salomonis*, Septuaginta Vetus Testamentum Graecum "
            "auctoritate Academiae Scientiarum Gottingensis editum, vol. "
            "XII.1, éd. Joseph Ziegler (Vandenhoeck & Ruprecht, Göttingen "
            "1962, réimpr. 1980). Bilingue latin : *Vulgata Stuttgartensia*, "
            "éd. Weber-Gryson, 5e éd. 2007."
        ),
        "alternative_names": [
            "Σοφία Σαλωμῶνος",
            "Sapientia Salomonis",
            "Liber Sapientiae",
            "Wisdom of Solomon",
        ],
        "metadata": {
            "language": "grc",
            "approximate_date": "2nd-1st century BCE",
            "place_of_composition": "Alexandria (Egypt)",
            "canonical_status": "deuterocanonical (Catholic/Orthodox); apocryphal (Protestant); accepted by Greek Fathers",
            "editions": [
                "Ziegler, Sapientia Salomonis — Septuaginta XII.1 (Göttingen 1962, réimpr.)",
                "Vulgata Stuttgartensia (Weber-Gryson, 5e éd. 2007)",
            ],
            "key_passages": [
                "Sap. 1-2 (discours de l'impie + immortalité)",
                "Sap. 7-9 (la Sagesse régissant l'âme)",
                "Sap. 11-12 (πειρασμός pédagogique)",
            ],
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_4_maccabees",
        "label": "4 Maccabées (4 Makkabees)",
        "type": "work",
        "period": "Second Temple Judaism",
        "school": None,
        "author_key": None,  # pseudépigraphe Pseudo-Josèphe
        "description": (
            "*4 Maccabées* (4 Makkabees), traité philosophico-rhétorique "
            "judéo-grec en 18 chapitres, composé probablement au Iᵉʳ siècle "
            "ap. J.-C. (entre 18 et 70 CE), faussement attribué à Flavius "
            "Josèphe par Eusèbe et Jérôme. Pivot doctrinal exposé en 4 Macc. "
            "1.1-3 : « ὁ εὐσεβὴς λογισμός — la raison pieuse — est maître "
            "absolu des passions ». Exemple narratif : martyre d'Éléazar et "
            "des sept frères Maccabées avec leur mère (4 Macc. 5-18), "
            "présenté comme illustration concrète de la maîtrise stoïcienne "
            "des πάθη par la λογισμός informée par la Loi mosaïque. Pour "
            "le KG : (a) source-pivot pour la christianisation du stoïcisme "
            "via Justin Martyr, Clément d'Alexandrie et Origène qui "
            "reconnaissent l'« autexousion » du martyr juif comme prototype "
            "du martyr chrétien ; (b) texte fondateur de la théorie de la "
            "παιδεία ascétique comme exercice de la liberté. Texte transmis "
            "dans le corpus septuagintal (canon orthodoxe-éthiopien). "
            "Édition critique : *Maccabaeorum Liber IV*, Septuaginta IX.1, "
            "éd. Robert Hanhart (Vandenhoeck & Ruprecht, Göttingen 1960). "
            "Trad. anglaise commentée : David A. deSilva, *4 Maccabees: "
            "Introduction and Commentary on the Greek Text in Codex Sinaiticus* "
            "(Septuagint Commentary Series, Brill 2006)."
        ),
        "alternative_names": [
            "4 Makkabees",
            "Quartus Liber Maccabaeorum",
            "Pseudo-Josephus, De Maccabaeis",
        ],
        "metadata": {
            "language": "grc",
            "approximate_date": "1st century CE (c. 18-70 CE)",
            "canonical_status": "Orthodox/Ethiopian canon appendix; rejected Catholic/Protestant",
            "editions": [
                "Hanhart, Maccabaeorum Liber IV — Septuaginta IX.1 (Göttingen 1960)",
                "deSilva, 4 Maccabees — Septuagint Commentary Series (Brill 2006)",
            ],
            "key_thesis": "ὁ εὐσεβὴς λογισμός — pious reason — masters the passions (4 Macc. 1.1-3)",
            "needs_text_ingestion": True,
        },
    },
    # -------------------------------------------------------------------
    # P1 — Lactance, Augustin, Cassien (Tertullien skipped, exists)
    # -------------------------------------------------------------------
    {
        "node_id": "work_lactantius_divinarum_institutionum",
        "label": "Lactance, Divinarum Institutionum libri VII",
        "type": "work",
        "period": "Patristic",
        "school": None,
        "author_key": "lactantius",
        "description": (
            "Lactance, *Divinarum Institutionum libri VII* (303-313 CE), "
            "première synthèse apologétique chrétienne latine en sept livres : "
            "I. *De falsa religione* ; II. *De origine erroris* ; III. *De "
            "falsa sapientia philosophorum* ; IV. *De vera sapientia et "
            "religione* ; V. *De iustitia* ; VI. *De vero cultu* ; VII. "
            "*De vita beata*. Pour le débat libre arbitre : (a) Inst. III "
            "(sur la fausse sagesse des philosophes) discute Cicéron, "
            "Sénèque, Lucrèce et opère une rétroprojection chrétienne de "
            "la critique stoïco-académicienne du destin ; (b) Inst. VII "
            "*De vita beata* développe une eschatologie où la liberté humaine "
            "est posée comme condition métaphysique du salut. Lactance "
            "introduit aussi la fameuse alternative épicurienne du problème "
            "du mal (Inst. VII.5 + Epitome, repris par Hume Dialogues X) "
            "en y répondant par la défense de la liberté. Épitomé "
            "auto-rédigé : *Epitome divinarum institutionum*. Éditions "
            "critiques : Brandt & Laubmann, CSEL 19 (Vienne 1890, "
            "*Institutiones*) + CSEL 27 (1893, *Epitome* + *De ira* + "
            "*De opificio*) ; Heck & Wlosok, *Lactanti Divinae Institutiones*, "
            "Teubner BSGRT (Berlin/Boston : de Gruyter, 5 vol. 2005-2011). "
            "Sources Chrétiennes en cours : SC 204-205 (Inst. I, éd. Monat "
            "1973-1974) ; SC 326 (Inst. II) ; SC 337 (Inst. IV) ; SC 377 "
            "(Inst. V, éd. Monat 1992) ; SC 509 + 547 (Inst. VI-VII, "
            "éd. Ingremeau 2007 + 2014)."
        ),
        "alternative_names": [
            "Divinae Institutiones",
            "Institutionum divinarum libri septem",
            "Lactantius, Inst.",
        ],
        "metadata": {
            "language": "lat",
            "approximate_date": "303-313 CE",
            "editions": [
                "Brandt & Laubmann, CSEL 19 (Vienne 1890) + CSEL 27 (1893, Epitome)",
                "Heck & Wlosok, Teubner BSGRT (de Gruyter 2005-2011, 5 vol.)",
                "SC 204-205, 326, 337, 377, 509, 547 (Monat, Ingremeau, 1973-2014)",
            ],
            "books_count": 7,
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_augustine_retractationes",
        "label": "Augustin, Retractationes",
        "type": "work",
        "period": "Patristic",
        "school": None,
        "author_key": "augustine",
        "description": (
            "Augustin d'Hippone, *Retractationes libri duo* (426-427 CE), "
            "catalogue critique auto-rédigé de ses 93 œuvres antérieures, "
            "présentées dans l'ordre chronologique avec autocritique "
            "doctrinale. Document philologique et théologique sans "
            "équivalent dans l'Antiquité tardive. Pour le KG free-will, "
            "trois rétractations sont pivots : (a) *Retract.* I.9.3-6 — "
            "réflexion critique sur le *De Libero Arbitrio* (388-395), "
            "Augustin nuance la portée semi-pélagienne potentielle de son "
            "argumentation de jeunesse contre les Manichéens ; (b) "
            "*Retract.* I.22(23) — sur *Ad Simplicianum de diversis "
            "quaestionibus* I.2 (396), passage que tout le monde considère "
            "comme le pivot 396 du tournant augustinien vers la "
            "prédestination antécédente (« in respondendo... pro libero "
            "arbitrio voluntatis humanae laboravi, sed vicit Dei gratia ») ; "
            "(c) *Retract.* II.66(92) — sur *De Gratia et Libero Arbitrio* "
            "(c. 426-427), traité de coordination anti-pélagienne. Pièce "
            "essentielle pour reconstruire la chronologie interne de la "
            "doctrine augustinienne de la grâce et du libre arbitre. "
            "Édition critique : Mutzenbecher, *S. Aurelii Augustini "
            "Retractationum libri II*, CCSL 57 (Brepols, Turnhout 1984) ; "
            "édition antérieure CSEL 36 (Knöll 1902, obsolète). Trad. "
            "française : Bardy et al., *Les Révisions*, BA 12, Bibliothèque "
            "Augustinienne (Desclée de Brouwer 1950, rééd. en cours). "
            "Trad. anglaise : Bogan, *The Retractations*, FOTC 60 (CUA "
            "Press 1968, rééd. 1999)."
        ),
        "alternative_names": [
            "Retractationum libri II",
            "Augustin, Révisions",
            "Augustine, Retractations",
        ],
        "metadata": {
            "language": "lat",
            "approximate_date": "426-427 CE",
            "editions": [
                "Mutzenbecher, CCSL 57 (Brepols, Turnhout 1984)",
                "Knöll, CSEL 36 (Vienne 1902, obsolète)",
                "BA 12 — Bibliothèque Augustinienne (Desclée 1950, rééd. en cours)",
                "Bogan, FOTC 60 (CUA Press 1968, rééd. 1999, English)",
            ],
            "books_count": 2,
            "works_reviewed": 93,
            "key_passages": [
                "Retract. I.9.3-6 (De Libero Arbitrio)",
                "Retract. I.22 (Ad Simplicianum I.2 — pivot 396)",
                "Retract. II.66 (De Gratia et Libero Arbitrio)",
            ],
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_cassian_conlationes_13",
        "label": "Cassien, Conlatio XIII (De protectione Dei)",
        "type": "work",
        "period": "Late Antiquity",
        "school": None,
        "author_key": "cassian",
        "description": (
            "Jean Cassien, *Conlatio XIII — De protectione Dei* (« Sur la "
            "protection divine », c. 425-428 CE), treizième conférence "
            "monastique du second recueil des *Conlationes Patrum* (= Conf. "
            "XI-XVII, prononcées au monastère de Saint-Victor à Marseille). "
            "Pièce centrale et la plus controversée du semi-pélagianisme "
            "massilien (qualificatif rétrospectif et critique, popularisé "
            "au XVIᵉ siècle ; les protagonistes contemporains se voyaient "
            "comme un milieu théologique entre Augustin et Pélage). Cassien "
            "y développe, à travers le personnage de l'abba Chérémon, une "
            "doctrine de la συνεργία (synergeia) entre grâce divine "
            "préveniente et coopération libre de la volonté humaine — "
            "explicitement critique de la formulation maximaliste "
            "augustinienne de *De Correptione et Gratia* (426). Pour le "
            "KG : pièce-clé du débat post-augustinien sur la grâce et le "
            "libre arbitre, source directe de la condamnation rétroactive "
            "des « erreurs marseillaises » par Prosper d'Aquitaine et de "
            "la décision conciliaire du IIᵉ concile d'Orange (529). "
            "Éditions critiques : Petschenig, *Iohannis Cassiani "
            "Conlationes XXIIII*, CSEL 13 (Vienne 1886, réimpr.) ; Pichery, "
            "*Conférences I-VII*, SC 42 + 42bis (Cerf 1955, rééd.) ; "
            "*Conférences VIII-XVII*, SC 54 (Cerf 1958) ; *Conférences "
            "XVIII-XXIV*, SC 64 (Cerf 1959). Trad. anglaise : Ramsey, "
            "*John Cassian: The Conferences*, ACW 57 (Paulist 1997)."
        ),
        "alternative_names": [
            "De protectione Dei",
            "Cassian, Conference XIII",
            "Conlatio Chaeremonis tertia",
        ],
        "metadata": {
            "language": "lat",
            "approximate_date": "c. 425-428 CE",
            "editions": [
                "Petschenig, CSEL 13 (Vienne 1886, réimpr.)",
                "Pichery, SC 54 (Cerf 1958) — Conf. VIII-XVII",
                "Ramsey, ACW 57 (Paulist 1997, English)",
            ],
            "speaker_persona": "abba Chaeremon",
            "doctrinal_role": "semi-Pelagian controversy — critique of Augustine, De Correptione",
            "needs_text_ingestion": True,
        },
    },
    # -------------------------------------------------------------------
    # P1 — Platon (Sophiste)
    # Aristote EE skipped — exists.
    # -------------------------------------------------------------------
    {
        "node_id": "work_plato_sophist",
        "label": "Platon, Sophiste (Σοφιστής)",
        "type": "work",
        "period": "Classical Greek",
        "school": None,
        "author_key": "plato",
        "description": (
            "Platon, *Sophiste* (Σοφιστής), dialogue tardif (c. 360-347 av. "
            "J.-C.), suite formelle du *Théétète* et préfigurant le "
            "*Politique*. Conversation pilotée par l'Étranger d'Élée (et non "
            "Socrate, qui n'intervient que dans le prologue), avec Théétète "
            "comme interlocuteur. Le dialogue articule deux questions : "
            "(a) définition du sophiste par la méthode dichotomique des "
            "divisions répétées (216a-236d) ; (b) résolution du paradoxe "
            "parménidien du non-être : pour expliquer que le sophiste "
            "produit des images et des discours faux, il faut admettre une "
            "altérité ontologique (Soph. 254d-259d : θάτερον / ταὐτόν comme "
            "γένη μέγιστα). Pour le KG free-will, la pertinence est "
            "indirecte : (a) la dialectique du non-être ouvre l'espace "
            "conceptuel pour la contingence et le possible-autrement (lu "
            "ainsi par Plotin et la tradition néoplatonicienne) ; (b) le "
            "dialogue est intégré comme partie du corpus platonicien complet "
            "pour la couverture lemmatique du KG (recherche par "
            "indexation grammaticale). Éditions critiques : Burnet, "
            "*Platonis Opera* vol. I (OCT, Oxford 1900, réimpr.) ; Robin, "
            "*Platon, Œuvres complètes* II (Bibliothèque de la Pléiade, "
            "Gallimard 1925, rééd.) ; Diès, *Le Sophiste*, Budé Œuvres "
            "complètes VIII.3 (Belles Lettres 1925, réimpr. 2003)."
        ),
        "alternative_names": ["Σοφιστής", "Sophist"],
        "metadata": {
            "cts_urn": "urn:cts:greekLit:tlg0059.tlg007",
            "language": "grc",
            "approximate_date": "c. 360-347 BCE",
            "editions": [
                "Burnet, Platonis Opera I — OCT (Oxford 1900, réimpr.)",
                "Robin, Pléiade II (Gallimard 1925, rééd.)",
                "Diès, Budé VIII.3 (Belles Lettres 1925, réimpr. 2003)",
            ],
            "free_will_relevance": "indirect — μέγιστα γένη + ontology of non-being",
            "needs_text_ingestion": True,
        },
    },
    # -------------------------------------------------------------------
    # P1 — Patristique grecque manquante + Apulée + Cléanthe
    # -------------------------------------------------------------------
    {
        "node_id": "work_theodoret_graecarum_affectionum_curatio",
        "label": "Théodoret, Graecarum Affectionum Curatio",
        "type": "work",
        "period": "Patristic",
        "school": None,
        "author_key": "theodoret",
        "description": (
            "Théodoret de Cyr, *Graecarum Affectionum Curatio* (Ἑλληνικῶν "
            "θεραπευτικὴ παθημάτων, Therapeutic of Greek Affections), "
            "c. 437 CE. Apologétique chrétienne en 12 livres, structurés "
            "comme une réponse antithétique aux « maladies » philosophiques "
            "grecques. Pour le KG free-will : Théodoret exploite "
            "systématiquement la chaîne doxographique anti-fataliste "
            "héritée d'Eusèbe de Césarée (*Préparation Évangélique* VI), "
            "elle-même nourrie d'Origène, de Diogénien et indirectement "
            "de Carnéade et de l'Académie. Livres VI (sur la providence) "
            "et X (sur les oracles + le destin) consignent une mosaïque de "
            "fragments stoïciens et péripatéticiens autrement perdus. "
            "Source précieuse pour la reconstruction de la doctrine "
            "stoïcienne de la συγκατάθεσις chez les commentateurs "
            "chrétiens grecs du Vᵉ siècle. Éditions critiques : Canivet, "
            "*Thérapeutique des maladies helléniques*, SC 57 (Cerf 1958, "
            "2 vol., gr.-fr.) ; Raeder, *Theodoreti Graecarum affectionum "
            "curatio*, Teubner BSGRT (Leipzig 1904, réimpr. 1969). "
            "Trad. anglaise commentée : Halton, *A Cure of Pagan Maladies*, "
            "ACW 67 (Newman Press / Paulist 2013)."
        ),
        "alternative_names": [
            "Ἑλληνικῶν θεραπευτικὴ παθημάτων",
            "Therapeutic of Greek Affections",
            "Théodoret, Thérapeutique",
        ],
        "metadata": {
            "cts_urn": "urn:cts:greekLit:tlg4089.tlg031",
            "language": "grc",
            "approximate_date": "c. 437 CE",
            "editions": [
                "Canivet, SC 57 (Cerf 1958, 2 vol.)",
                "Raeder, Teubner BSGRT (Leipzig 1904, réimpr. 1969)",
                "Halton, ACW 67 (Paulist 2013, English)",
            ],
            "books_count": 12,
            "doxographic_chain": "Eusebius PE VI → Diogenian → Carneades / Academy",
            "key_books": [
                "Livre VI (providence)",
                "Livre X (oracles + destin)",
            ],
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_apuleius_de_platone",
        "label": "Apulée, De Platone et eius dogmate",
        "type": "work",
        "period": "Roman Imperial",
        "school": "Middle Platonism",
        "author_key": "apuleius",
        "description": (
            "Apulée de Madaure, *De Platone et eius dogmate libri II* "
            "(c. 150-170 CE), manuel doxographique latin Middle-Platonist "
            "sur la philosophie de Platon. Structure : Livre I = physique "
            "+ théologie + démonologie ; Livre II = éthique + politique. "
            "Pour le KG free-will : Livre II.11-12 articule une "
            "doctrine tripartite *providentia / fatum / casus* "
            "structurellement parallèle à Pseudo-Plutarque *De Fato* "
            "(hiérarchie des trois providences) et à *Didaskalikos* "
            "d'Alcinoos — confirmation indépendante de la position "
            "Middle-Platonist standardisée du IIᵉ siècle sur la coexistence "
            "providence-fatum-libre arbitre humain. Texte latin de "
            "transmission directe, contemporain mais formellement distinct "
            "des œuvres rhétoriques d'Apulée (*Apologie*, *Florida*, "
            "*Métamorphoses*). Authenticité parfois contestée au XIXᵉ "
            "siècle mais aujourd'hui largement admise (Beaujeu, Moreschini). "
            "Éditions critiques : Beaujeu, *Apulée. Opuscules philosophiques "
            "(Du dieu de Socrate, Platon et sa doctrine, Du monde) et "
            "fragments*, Budé (Belles Lettres 1973, réimpr.) ; Moreschini, "
            "*Apulei Platonici Madaurensis Opera quae supersunt* III — "
            "*De Philosophia libri*, Teubner BSGRT (Stuttgart/Leipzig 1991)."
        ),
        "alternative_names": [
            "Apuleius, De Platone et eius dogmate",
            "De dogmate Platonis",
        ],
        "metadata": {
            "language": "lat",
            "approximate_date": "c. 150-170 CE",
            "editions": [
                "Beaujeu, Budé (Belles Lettres 1973, réimpr.)",
                "Moreschini, Teubner BSGRT (1991, vol. III)",
            ],
            "books_count": 2,
            "key_passages": [
                "II.11-12 (providentia/fatum/casus tripartition)",
            ],
            "doctrinal_parallels": [
                "Pseudo-Plutarch De Fato",
                "Alcinoos Didaskalikos",
            ],
            "needs_text_ingestion": True,
        },
    },
    {
        "node_id": "work_cleanthes_hymn_to_zeus",
        "label": "Cléanthe, Hymne à Zeus (Ὕμνος εἰς Δία)",
        "type": "work",
        "period": "Hellenistic",
        "school": "Stoics",
        "author_key": "cleanthes",
        "description": (
            "Cléanthe d'Assos, *Hymne à Zeus* (Ὕμνος εἰς Δία), 39 hexamètres "
            "dactyliques en stoïque archaïque — seul texte poétique stoïcien "
            "conservé entièrement. Transmis par Stobée, *Anthologium* I.1.12 "
            "(SVF I.537). Théodicée stoïcienne condensée : Zeus identifié "
            "au λόγος universel, νόμος cosmique et destin (vv. 1-9), tout "
            "événement du monde — y compris le mal apparent — orchestré "
            "par sa providence (vv. 10-21), l'action mauvaise des humains "
            "présentée comme παρεπόμενον (« conséquence collatérale », "
            "vv. 22-31) — figure littéraire majeure de la théodicée "
            "stoïcienne par συμπλοκή des causes. Texte essentiel pour la "
            "discussion patristique grecque (Justin, Clément, Origène) "
            "sur la providence et le mal moral, et pour l'argumentation "
            "de Bobzien 1998 sur la doctrine stoïcienne de la "
            "co-fatalité. Éditions critiques : Powell, *Collectanea "
            "Alexandrina* (Clarendon Press, Oxford 1925, réimpr. 1981) ; "
            "Thom, *Cleanthes' Hymn to Zeus: Text, Translation, and "
            "Commentary*, Studien und Texte zu Antike und Christentum 33 "
            "(Mohr Siebeck, Tübingen 2005) — édition de référence "
            "philologique + commentaire."
        ),
        "alternative_names": [
            "Ὕμνος εἰς Δία",
            "Hymnus in Iovem",
            "Hymn to Zeus",
        ],
        "metadata": {
            "language": "grc",
            "approximate_date": "c. 280-260 BCE",
            "transmission": "Stobaeus, Anth. I.1.12 (= SVF I.537)",
            "metre": "dactylic hexameter",
            "verse_count": 39,
            "editions": [
                "Powell, Collectanea Alexandrina (Clarendon Press, Oxford 1925, réimpr. 1981)",
                "Thom, Cleanthes' Hymn to Zeus — STAC 33 (Mohr Siebeck 2005)",
            ],
            "key_passages": [
                "vv. 1-9 (Zeus = logos/nomos/destiny)",
                "vv. 22-31 (evil as parepomenon)",
            ],
            "needs_text_ingestion": True,
        },
    },
]


# ---------------------------------------------------------------------------
# Enrichment specs for existing nodes flagged in ALIAS_TO_EXISTING.
# ---------------------------------------------------------------------------

EXISTING_NODE_ENRICHMENTS: dict[str, dict[str, Any]] = {
    "work_de_fato_alexander_c200ce_o6p7q8r9": {
        # Already rich; just stamp the canonical-id mapping + ensure language set.
        "metadata_patch": {
            "language": "grc",
            "wave_f_canonical_id": "work_de_fato_alexander_c200ce_o6p7q8r9",
            "wave_f_spec_alias": "work_alexander_de_fato_standalone",
            "wave_f_review_2026_05_16": (
                "Verified existing node is canonical; Bruns 1892 / Thillet 1984 "
                "Budé / Sharples 1983 Duckworth editions already recorded."
            ),
        },
    },
    "work_dss_hodayot_i1j2k3l4": {
        # Existing description is thin; enrich with DJD critical edition refs.
        "metadata_patch": {
            "language": "hbo",  # Hebrew (Biblical, Dead Sea Scrolls Hebrew)
            "editions": [
                "Schuller & Newsom, Hodayot: A Study Edition (1997) + DJD XL — 1QHodayot a (OUP 2009)",
                "Dupont-Sommer, Les Écrits Esséniens (Payot 1959, rééd. Pléiade 1987)",
            ],
            "djd_volume": "DJD XL (Oxford 2009)",
            "key_passages": [
                "1QH 7.27-31 (predestination + election)",
                "1QH 9.21-23 (divine election)",
                "1QH 12.31-33 (cosmic dualism)",
            ],
            "wave_f_canonical_id": "work_dss_hodayot_i1j2k3l4",
            "wave_f_spec_alias": "work_qumran_hodayot",
            "wave_f_review_2026_05_16": (
                "Enriched metadata with DJD XL critical edition + key passages; "
                "kept canonical node id, no duplicate created."
            ),
        },
    },
}


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
# Node construction
# ---------------------------------------------------------------------------


def build_work_node(spec: dict[str, Any]) -> dict[str, Any]:
    """Convert a WORKS spec into a KG work node matching existing schema.

    Existing convention (sampled from `sc_origenes_contra_celsum`):
    fields ``alternative_names`` and ``metadata`` are JSON-encoded
    strings; the dict is alphabetic-leaning with ``id`` and ``node_id``
    paired and equal.
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
        "school": spec.get("school"),
        "type": spec.get("type", "work"),
        "updated_at": NOW_ISO,
    }


def build_authored_by_edge(
    work_id: str,
    person_id: str,
) -> dict[str, Any]:
    """Construct an ``authored_by`` edge (work → person) matching schema."""
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(
            {
                "wave": WAVE_TAG,
                "confidence": 1.0,
                "source": "biographical_tradition",
            },
            ensure_ascii=False,
        ),
        "relation": "authored_by",
        "source": work_id,
        "source_id": work_id,
        "target": person_id,
        "target_id": person_id,
        "weight": 1.0,
    }


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e.get("source") or "", e.get("relation") or "", e.get("target") or "")


def patch_existing_metadata(node: dict[str, Any], patch: dict[str, Any]) -> bool:
    """Merge `patch` into node['metadata'] (JSON-encoded string). Returns True
    if anything changed; idempotent (no-op if already merged)."""
    raw = node.get("metadata") or "{}"
    if isinstance(raw, dict):
        md: dict[str, Any] = dict(raw)
    else:
        md = json.loads(raw)

    changed = False
    for k, v in patch.items():
        if md.get(k) != v:
            md[k] = v
            changed = True
    if not changed:
        return False
    node["metadata"] = json.dumps(md, ensure_ascii=False)
    node["updated_at"] = NOW_ISO
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-f] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id: dict[str, dict[str, Any]] = {get_node_id(n): n for n in nodes}
    edges_signatures: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    works_added = 0
    works_skipped_existing = 0
    authored_by_added = 0
    enrichments_applied = 0

    # 1) Skip flagged already-present targets explicitly (sanity).
    for skip_nid, why in SKIP_ALREADY_PRESENT.items():
        if skip_nid in nodes_by_id:
            print(f"[skip] {skip_nid} :: {why}")
            works_skipped_existing += 1
        else:
            print(
                f"[warn] {skip_nid} flagged as skip-already-present but NOT in KG — "
                "spec drift; treat as missing in future wave"
            )

    # 2) Apply enrichment patches to existing nodes (Alexander, Hodayot).
    for ex_nid, patch_spec in EXISTING_NODE_ENRICHMENTS.items():
        if ex_nid not in nodes_by_id:
            print(f"[enrich] skip: {ex_nid} not present in KG")
            continue
        if patch_existing_metadata(nodes_by_id[ex_nid], patch_spec["metadata_patch"]):
            enrichments_applied += 1
            print(f"[enrich] {ex_nid} :: metadata patched")
        else:
            print(f"[enrich] {ex_nid} :: already up-to-date (no-op)")

    # 3) Insert new work nodes + wire authored_by edges.
    for spec in WORKS:
        nid = spec["node_id"]
        if nid in nodes_by_id:
            works_skipped_existing += 1
            print(f"[skip] {nid} already present")
            continue

        new_node = build_work_node(spec)
        nodes.append(new_node)
        nodes_by_id[nid] = new_node
        works_added += 1
        print(f"[work] add: {nid}")

        author_key = spec.get("author_key")
        if not author_key:
            print(f"[authored_by] {nid} :: no author key (pseudépigraphe/anon)")
            continue
        author_id = AUTHOR_IDS.get(author_key)
        if not author_id:
            print(f"[authored_by] skip: author_key={author_key} not in AUTHOR_IDS map")
            continue
        if author_id not in nodes_by_id:
            print(f"[authored_by] skip: author node {author_id} not in KG")
            continue

        sig = (nid, "authored_by", author_id)
        if sig in edges_signatures:
            print(f"[authored_by] skip: {nid} --authored_by--> {author_id} exists")
            continue

        edge = build_authored_by_edge(nid, author_id)
        edges.append(edge)
        edges_signatures.add(sig)
        authored_by_added += 1
        print(f"[authored_by] add: {nid} --authored_by--> {author_id}")

    if works_added or authored_by_added or enrichments_applied:
        write_nodes(nodes)
        write_edges(edges)
        print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")
    else:
        print("[write] no changes — files untouched")

    print()
    alex_path = (
        "enriched_existing"
        if "work_de_fato_alexander_c200ce_o6p7q8r9" in nodes_by_id
        else "missing"
    )
    origen_path = (
        "skipped_existing"
        if "work_origen_de_oratione" in nodes_by_id
        else "missing"
    )
    print(
        f"[wave-f] works_added={works_added}  "
        f"works_skipped_existing={works_skipped_existing}  "
        f"authored_by_added={authored_by_added}"
    )
    print(f"[wave-f] enrichments_applied={enrichments_applied}")
    print(f"[wave-f] alexander_de_fato_path={alex_path}")
    print(f"[wave-f] origen_de_oratione_path={origen_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
