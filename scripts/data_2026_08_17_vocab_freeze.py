#!/usr/bin/env python3
"""Frozen decisions and evidence for the 2026-08-17 vocabulary cleanup.

This module contains data only.  The executable, precondition checks,
idempotence logic, backup handling, and invariants live in
``apply_2026_08_17_vocab_freeze.py``.
"""

from __future__ import annotations

STAMP_KEY = "vocab_freeze_2026_08_17"
SCHEME_VERSION = "1.0.0"
BACKUP_SUFFIX = ".bak-vocab"

SOURCE_NODES_SHA256_AT_INVENTORY = (
    "f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888"
)

PERIOD_COUNTS = {
    "Roman Imperial": 11220,
    "Late Antiquity": 2101,
    "Classical Greek": 2089,
    "Contemporary": 1514,
    "Patristic": 1362,
    "Hellenistic": 465,
    "Roman Republican": 408,
    "Modern": 362,
    "Early Modern": 79,
    "Medieval": 54,
    "Second Temple Judaism": 29,
    "Presocratic": 13,
    "Cross-period": 11,
    "Rabbinic": 2,
    "First Temple / Pre-exilic Judaism": 2,
}

SCHOOL_COUNTS_BEFORE = {
    "Stoic": 3524,
    "Christian Platonism": 2640,
    "Neoplatonist": 1524,
    "Platonist": 1381,
    "Doxographer": 1203,
    "Peripatetic": 968,
    "Apologetic": 931,
    "Apostolic Fathers": 831,
    "Christian Apologetics": 745,
    "Christian": 694,
    "Skeptic": 534,
    "Epicurean": 496,
    "Latin Patristic": 245,
    "Patristic": 222,
    "Antiochene School": 53,
    "Various": 49,
    "Middle Platonist": 29,
    "Eclectic": 2,
    "Academic (New Academy)": 1,
    "Cynicism": 1,
    "None (doxographer)": 1,
    "Cappadocian Fathers": 1,
    "Nicene orthodoxy": 1,
    "Presocratic": 1,
    "Neo-Chalcedonian / Byzantine Patristic": 1,
}

SCHOOL_COUNTS_AFTER = {
    "Stoic": 3524,
    "Christian Platonism": 2642,
    "Christian Apologetics": 1676,
    "Neoplatonist": 1524,
    "Platonist": 1381,
    "Doxographer": 1205,
    "Peripatetic": 968,
    "Apostolic Fathers": 831,
    "Christian": 694,
    "Skeptic": 535,
    "Epicurean": 496,
    "Latin Patristic": 245,
    "Patristic": 223,
    "Antiochene School": 53,
    "Various": 50,
    "Middle Platonist": 29,
    "Cynic": 1,
    "Presocratic Philosophy": 1,
}

# The 931 IDs are frozen by count and sorted-ID digest rather than copied into
# this file.  This keeps the plan reviewable while still detecting scope drift.
APOLOGETIC_MERGE = {
    "from": "Apologetic",
    "to": "Christian Apologetics",
    "expected_count": 931,
    "expected_ids_sha256": (
        "9b93f2710582e3a116bb5cf2292e9098bf7acb215a7cbd788d06df1eabf191d7"
    ),
    "expected_type": "passage",
    "expected_period": "Patristic",
    "expected_authors": {"Justin Martyr": 833, "Tatian": 98},
    "expected_works": {
        "Dialogus cum Tryphone": 750,
        "Oratio ad Graecos": 98,
        "Apologia Prima": 68,
        "Apologia Secunda": 15,
    },
    "evidence": (
        "All 931 records are passages from Justin Martyr or Tatian. Standard "
        "historical literature uses the noun phrase 'Christian apologetics' "
        "for this defensive discourse and 'Christian apologists' for its "
        "authors; 'Apologetic' alone is grammatically and taxonomically less "
        "precise."
    ),
    "reference": (
        "Gerhard van den Heever, 'Christian Apologetics', in From Jesus "
        "Christ to Christianity; Edwards et al., Apologetics in the Roman "
        "Empire (Oxford, 1999)."
    ),
    "alternative_labels": ["Apologetic"],
}

# Each rare-value repair is node-specific because ``Eclectic`` has two
# different responsible targets.  ``description_contains`` and
# ``required_edges`` are executable preconditions, not narrative decoration.
SCHOOL_FIXES = [
    {
        "node_id": "person_arcesilaus_316_241bce",
        "from": "Academic (New Academy)",
        "to": "Skeptic",
        "expected_metadata_school": "Academic (Middle Academy)",
        "expected_type": "person",
        "expected_period": "Hellenistic",
        "description_contains": "Founder of the New (skeptical) Academy",
        "required_edges": [
            ["person_arcesilaus_316_241bce", "member_of", "school_academics"],
            [
                "person_arcesilaus_316_241bce",
                "member_of",
                "school_academy_middle",
            ],
        ],
        "evidence": (
            "The node calls Arcesilaus founder of the skeptical Academy and "
            "has member_of edges to both Academy faction nodes; Skeptic is "
            "the retained broad school value, while the New/Middle Academy "
            "labels remain explicit alternatives and graph relations."
        ),
        "alternative_labels": [
            "Academic (New Academy)",
            "Academic (Middle Academy)",
        ],
    },
    {
        "node_id": "person_aulus_gellius_125_180ce",
        "from": "Eclectic",
        "to": "Doxographer",
        "expected_metadata_school": "Eclectic",
        "expected_type": "person",
        "expected_period": "Roman Imperial",
        "description_contains": "Roman miscellanist and doxographer",
        "required_edges": [],
        "evidence": (
            "The node explicitly describes Gellius as a miscellanist and "
            "doxographer, not an original philosopher, and emphasizes his "
            "transmission of Chrysippus; Doxographer is therefore the "
            "existing responsible functional value."
        ),
        "alternative_labels": ["Eclectic"],
    },
    {
        "node_id": "person_galen_pergamon_129_216ce",
        "from": "Eclectic",
        "to": "Various",
        "expected_metadata_school": "Eclectic",
        "expected_type": "person",
        "expected_period": "Roman Imperial",
        "description_contains": "drawing on Plato, Aristotle, and Hippocrates",
        "required_edges": [],
        "evidence": (
            "The node itself presents Galen as drawing on Plato, Aristotle, "
            "and Hippocrates without a single school allegiance; Various is "
            "the retained, explicitly multi-tradition value and Eclectic is "
            "preserved as an alternative label."
        ),
        "alternative_labels": ["Eclectic"],
    },
    {
        "node_id": "person_crescens_cynic_2c_ce",
        "from": "Cynicism",
        "to": "Cynic",
        "expected_metadata_school": "Cynicism",
        "expected_type": "person",
        "expected_period": "Roman Imperial",
        "description_contains": "Cynic philosopher active in Rome",
        "required_edges": [],
        "evidence": (
            "The node label, description, and cited ancient witnesses identify "
            "Crescens as a Cynic philosopher; Cynic is the person-compatible "
            "canonical affiliation, while Cynicism names the doctrine."
        ),
        "alternative_labels": ["Cynicism"],
    },
    {
        "node_id": "person_diogenes_laertius_3c_ce",
        "from": "None (doxographer)",
        "to": "Doxographer",
        "expected_metadata_school": "None (doxographer)",
        "expected_type": "person",
        "expected_period": "Roman Imperial",
        "description_contains": "Greek doxographer",
        "required_edges": [],
        "evidence": (
            "The description and work record identify Diogenes Laertius as a "
            "doxographer; the textual sentinel None (doxographer) is replaced "
            "by the already established Doxographer value."
        ),
        "alternative_labels": ["None (doxographer)"],
    },
    {
        "node_id": "person_gregory_nazianzus_d389",
        "from": "Cappadocian Fathers",
        "to": "Christian Platonism",
        "expected_metadata_school": "Cappadocian Fathers",
        "expected_type": "person",
        "expected_period": "Late Antiquity",
        "description_contains": "with whom he compiled Origen's Philocalia",
        "required_edges": [],
        "evidence": (
            "The node identifies Gregory as a Cappadocian Father and records "
            "his close Origenist collaboration with Basil. To give both "
            "Gregorys one philosophical school label, Christian Platonism is "
            "used; Cappadocian Fathers remains alternative group metadata."
        ),
        "alternative_labels": ["Cappadocian Fathers"],
    },
    {
        "node_id": "person_gregory_nyssa_d395",
        "from": "Nicene orthodoxy",
        "to": "Christian Platonism",
        "expected_metadata_school": "Nicene orthodoxy",
        "expected_type": "person",
        "expected_period": "Patristic",
        "description_contains": "Christian Platonist and mystic of Origenist inspiration",
        "required_edges": [],
        "evidence": (
            "The node explicitly calls Gregory a Christian Platonist of "
            "Origenist inspiration and a Cappadocian Father. Christian "
            "Platonism is therefore the direct evidenced school; Nicene "
            "orthodoxy and Cappadocian Fathers remain alternative metadata."
        ),
        "alternative_labels": ["Nicene orthodoxy", "Cappadocian Fathers"],
    },
    {
        "node_id": "person_heraclitus_fl500bce_a1b2c3d4",
        "from": "Presocratic",
        "to": "Presocratic Philosophy",
        "expected_metadata_school": "Presocratic",
        "expected_type": "person",
        "expected_period": "Presocratic",
        "description_contains": "Presocratic philosopher from Ephesus",
        "required_edges": [
            [
                "person_heraclitus_fl500bce_a1b2c3d4",
                "member_of",
                "school_presocratic",
            ]
        ],
        "evidence": (
            "Presocratic is already Heraclitus's period and should not double "
            "as his school value; his existing member_of edge targets the "
            "Presocratic Philosophy school node, which supplies the canonical "
            "school label."
        ),
        "alternative_labels": ["Presocratic"],
    },
    {
        "node_id": "person_maximus_confessor_d662",
        "from": "Neo-Chalcedonian / Byzantine Patristic",
        "to": "Patristic",
        "expected_metadata_school": "Neo-Chalcedonian / Byzantine Patristic",
        "expected_type": "person",
        "expected_period": "Late Antiquity",
        "description_contains": "Maximus the Confessor",
        "required_edges": [
            [
                "person_maximus_confessor_d662",
                "member_of",
                "school_christian_patristic",
            ]
        ],
        "evidence": (
            "The graph already asserts Maximus's membership in Early "
            "Christian (Patristic) Theology. Patristic is the retained broad "
            "value; Neo-Chalcedonian / Byzantine Patristic is preserved as a "
            "more specific alternative tradition label."
        ),
        "alternative_labels": ["Neo-Chalcedonian / Byzantine Patristic"],
    },
]
