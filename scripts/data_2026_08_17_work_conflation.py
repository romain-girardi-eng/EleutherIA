#!/usr/bin/env python3
"""Data for ``apply_2026_08_17_work_conflation.py``.

Twelve ``work`` nodes were each holding passages from several *different* works.
``scripts/check_kg_work_id_uniqueness.py`` has been reporting them as
"KNOWN (allowlisted) … remediation pending" and passing, so the defect survived
every previous audit. It is the largest factual error in the graph: ~3,200
passages answer the question "which work is this from?" with the wrong work, and
every citation, tree-navigation result and `part_of` traversal built on them is
wrong.

Two shapes of the defect:

* **Double-parented** (the bulk). The passage is already `part_of` its correct
  work AND `part_of` the conflated one. Fixed by deleting the wrong edge — no
  node is created and nothing can be lost, because the correct parent is
  verified to remain.
* **Single-parented**. The passage's only parent is the conflated work, because
  its real work has no node yet. Fixed by re-parenting to an existing work where
  one exists, and otherwise by creating the work node from the passage's own
  `author` / `work_title` / `language` / `work_canonical_id` metadata.

Every label, author and canonical id below is copied from the passages
themselves. No ancient text is generated, and no bibliographic claim is invented.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Foreign passage groups whose correct work node ALREADY EXISTS.
# key = (conflated host work, foreign work_canonical_id) -> correct work node
REPARENT_TO_EXISTING: dict[tuple[str, str], str] = {
    # 21 passages of De Correptione et Gratia sat under De Libero Arbitrio while
    # work_augustine_de_correptione existed with zero children.
    ("work_de_libero_arbitrio", "urn:cts:latinLit:stoa0040.stoa045"): (
        "work_augustine_de_correptione"
    ),
    # 15 passages of the Second Apology sat under the First Apology while
    # work_justin_second_apology_sc507 existed with no passages.
    ("work_justin_first_apology", "urn:cts:greekLit:tlg0645.tlg002"): (
        "work_justin_second_apology_sc507"
    ),
    # A whole-chapter node for Gellius, Noctes Atticae VII.2 was parented to
    # Diogenes Laertius' Lives. work_gellius_na_vii_2 already holds the 16
    # section-level nodes of the same chapter.
    ("work_diogenes_laertius_lives", "urn:cts:latinLit:phi1254.phi001"): (
        "work_gellius_na_vii_2"
    ),
}


# ---------------------------------------------------------------------------
# 2. Foreign passage groups whose work node must be created. Fields are taken
# verbatim from the passages' own metadata; `description` states only what the
# work is, with no interpretative claim.
NEW_WORKS: list[dict] = [
    {
        "host": "work_de_libero_arbitrio",
        "canonical": "urn:cts:latinLit:stoa0040.stoa054",
        "node_id": "work_augustine_de_natura_boni",
        "label": "Augustine, De Natura Boni (On the Nature of the Good)",
        "author_node": "person_augustine_hippo_d430",
        "author": "Augustine",
        "language": "lat",
        "period": "Late Antiquity",
        "description": (
            "Augustine, De natura boni contra Manichaeos. Anti-Manichaean treatise arguing that "
            "every nature is good in so far as it is a nature, and that evil is not a substance but "
            "a privation of good. 39 passages in this corpus."
        ),
    },
    {
        "host": "work_de_libero_arbitrio",
        "canonical": "urn:cts:latinLit:stoa0040.adv_fulg",
        "node_id": "work_augustine_adversus_fulgentium",
        "label": "Augustine, Libellus Adversus Fulgentium Donatistam",
        "author_node": "person_augustine_hippo_d430",
        "author": "Augustine",
        "language": "lat",
        "period": "Late Antiquity",
        "description": (
            "Libellus adversus Fulgentium Donatistam, transmitted in the Augustinian corpus "
            "(CPL 351; its authenticity is debated). Anti-Donatist polemic. 26 passages in this "
            "corpus."
        ),
    },
    {
        "host": "work_de_libero_arbitrio",
        "canonical": "cpl:evodius.de_fide",
        "node_id": "work_evodius_de_fide_contra_manichaeos",
        "label": "Evodius of Uzalis, De fide contra Manichaeos",
        "author_node": "person_evodius_uzalis_d424",
        "author": "Evodius Bishop of Uzalis",
        "language": "lat",
        "period": "Late Antiquity",
        "description": (
            "De fide contra Manichaeos, attributed to Evodius of Uzalis, a correspondent and "
            "associate of Augustine. Transmitted within the Augustinian corpus (CPL 386). "
            "36 passages in this corpus."
        ),
    },
    {
        "host": "sc172_epistula_barnabae",
        "canonical": "urn:cts:greekLit:tlg1311.tlg001",
        "node_id": "work_didache",
        "label": "Didache (Διδαχὴ τῶν δώδεκα ἀποστόλων)",
        "author_node": None,  # anonymous
        "author": "Anonymous",
        "language": "grc",
        "period": "Roman Imperial",
        "description": (
            "Didache, or Teaching of the Twelve Apostles. Anonymous early Christian church order, "
            "opening with the Two Ways (Δύο ὁδοί) material. 6 passages in this corpus."
        ),
    },
]

# Gregory of Nazianzus' five Theological Orations. The person node
# (person_gregory_nazianzus_d389) already exists; only the works were missing.
_GREG = [
    (
        "urn:cts:greekLit:tlg2022.tlg007",
        "work_gregory_naz_oratio_27",
        "Gregory of Nazianzus, Adversus Eunomianos (Oratio 27)",
        "First Theological Oration, against the Eunomians: on who may do theology and under what conditions.",
    ),
    (
        "urn:cts:greekLit:tlg2022.tlg008",
        "work_gregory_naz_oratio_28",
        "Gregory of Nazianzus, De Theologia (Oratio 28)",
        "Second Theological Oration, on theology proper: the incomprehensibility of the divine essence.",
    ),
    (
        "urn:cts:greekLit:tlg2022.tlg009",
        "work_gregory_naz_oratio_29",
        "Gregory of Nazianzus, De Filio (Oratio 29)",
        "Third Theological Oration, on the Son.",
    ),
    (
        "urn:cts:greekLit:tlg2022.tlg010",
        "work_gregory_naz_oratio_30",
        "Gregory of Nazianzus, De Filio (Oratio 30)",
        "Fourth Theological Oration, on the Son, continued.",
    ),
    (
        "urn:cts:greekLit:tlg2022.tlg011",
        "work_gregory_naz_oratio_31",
        "Gregory of Nazianzus, De Spiritu Sancto (Oratio 31)",
        "Fifth Theological Oration, on the Holy Spirit.",
    ),
]
for _canon, _nid, _label, _desc in _GREG:
    NEW_WORKS.append(
        {
            "host": "work_de_libero_arbitrio",
            "canonical": _canon,
            "node_id": _nid,
            "label": _label,
            "author_node": "person_gregory_nazianzus_d389",
            "author": "Gregory of Nazianzus",
            "language": "grc",
            "period": "Late Antiquity",
            "description": _desc + " Delivered at Constantinople, 380 CE.",
        }
    )


# ---------------------------------------------------------------------------
# 3. Person nodes that must exist for the works above.
NEW_PERSONS: list[dict] = [
    {
        "node_id": "person_evodius_uzalis_d424",
        "label": "Evodius of Uzalis",
        "period": "Late Antiquity",
        "description": (
            "Evodius, bishop of Uzalis in proconsular Africa (died c. 424). Friend and "
            "correspondent of Augustine; he is the interlocutor of Augustine's De libero arbitrio "
            "and De quantitate animae, and several letters between them survive."
        ),
        "metadata": {"death_date": "c. 424 CE", "language": "lat"},
    },
]


# ---------------------------------------------------------------------------
# 4. Passage metadata whose `author` field contradicts the passage's own label
# and canonical id.
PASSAGE_AUTHOR_FIXES: dict[str, tuple[str, str, str]] = {
    # label: "Aulus Gellius, Noctes Atticae, 7.2"; cts_urn phi1254.phi001 = Gellius.
    # metadata.author said "Diogenes Laertius" because the node had been filed
    # under Diogenes Laertius' Lives.
    "passage_gellius_7_2": (
        "Diogenes Laertius",
        "Aulus Gellius",
        "label and cts_urn (urn:cts:latinLit:phi1254.phi001:7.2) both identify Aulus Gellius",
    ),
}


# ---------------------------------------------------------------------------
# 5. `work_canonical_id` normalisation.
# work_gellius_na_vii_2 models Noctes Atticae VII.2 as a work in its own right
# (an excerpt-work), and its 16 section nodes carry
# `urn:cts:latinLit:phi1254.phi001.vii.2` accordingly. The whole-chapter node
# re-parented here carried the un-scoped work id `urn:cts:latinLit:phi1254.phi001`,
# which made the work node look conflated when it holds one work at two citation
# depths. Aligned on the scoped id its 16 siblings already use.
PASSAGE_CANONICAL_FIXES: dict[str, tuple[str, str, str]] = {
    "passage_gellius_7_2": (
        "urn:cts:latinLit:phi1254.phi001",
        "urn:cts:latinLit:phi1254.phi001.vii.2",
        "aligned on the 16 sibling section nodes of work_gellius_na_vii_2",
    ),
}
