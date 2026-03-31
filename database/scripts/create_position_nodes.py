#!/usr/bin/env python3
"""
Create position nodes and holds_position edges for core philosophical
positions on free will, determinism, and fate.

Usage:
    set -a; source .env; set +a
    python database/scripts/create_position_nodes.py
"""

from __future__ import annotations

import json
import os
import sys

import psycopg2
import psycopg2.extras

SCHEMA = "free_will"

SCHOLARLY_NOTE = (
    "Note: this is a modern scholarly characterization; "
    "ancient philosophers did not use this terminology."
)


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    return url


# ── Position nodes ──────────────────────────────────────────────────

POSITION_NODES: list[dict[str, str]] = [
    {
        "node_id": "position_compatibilism",
        "label": "Compatibilism",
        "description": (
            "What modern scholars term compatibilism: the view that causal "
            "determinism and moral responsibility are compatible. Ancient "
            "Stoics, especially Chrysippus, are often characterized in these "
            "terms for distinguishing types of causes while maintaining both "
            "fate and responsibility. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_hard_determinism",
        "label": "Hard determinism",
        "description": (
            "What modern scholars term hard determinism: the view that all "
            "events are causally necessitated and that genuine free will or "
            "moral responsibility is an illusion. Cleanthes is sometimes "
            "read in this direction, insofar as his Stoicism places greater "
            "emphasis on fate's inescapability than on the agent's rational "
            "assent. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_libertarianism_freewill",
        "label": "Libertarian free will",
        "description": (
            "What modern scholars term libertarian free will: the view that "
            "genuine freedom requires the ability to do otherwise and is "
            "incompatible with causal determinism. Alexander of Aphrodisias "
            "and (early) Origen are often characterized as holding views "
            "that anticipate this position. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_fatalism",
        "label": "Fatalism",
        "description": (
            "Fatalism: the view that future events are fixed regardless of "
            "human deliberation or action. Distinguished from determinism in "
            "that fatalism concerns the fixity of outcomes irrespective of "
            "causal chains. Diodorus Cronus's Master Argument is often "
            "taken to support a fatalist conclusion. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_soft_determinism",
        "label": "Soft determinism",
        "description": (
            "What modern scholars term soft determinism: the view that "
            "determinism is true but compatible with a useful notion of "
            "freedom, typically defined as acting from one's own nature "
            "without external compulsion. Seneca's ethical writings are "
            "sometimes read in this register, emphasizing inner freedom "
            "within a determined cosmos. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_theological_determinism",
        "label": "Theological determinism",
        "description": (
            "Theological determinism: the view that God's foreknowledge, "
            "providence, or predestination determines all events. The late "
            "Augustine, especially in the anti-Pelagian writings, is widely "
            "characterized as holding this position with his doctrines of "
            "irresistible grace and predestination. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_indeterminism",
        "label": "Indeterminism",
        "description": (
            "Indeterminism: the view that not all events are causally "
            "determined, leaving room for genuine contingency. Epicurus's "
            "doctrine of the atomic swerve (clinamen/parenklisis) is the "
            "most prominent ancient articulation of this view, positing a "
            "minimal indeterminacy at the physical level to ground free "
            "volition. " + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
    {
        "node_id": "position_academic_skepticism_fate",
        "label": "Academic skeptical suspension on fate",
        "description": (
            "The Academic skeptical stance of withholding assent (epochē) "
            "on whether fate governs all things. Carneades is reported to "
            "have argued against both Stoic fate and Epicurean indeterminism, "
            "maintaining that voluntary action can be explained without "
            "appealing to either causal necessitation or atomic swerves. "
            + SCHOLARLY_NOTE
        ),
        "period": "Cross-period",
    },
]


# ── holds_position edges ────────────────────────────────────────────
# Each tuple: (source_id, target_position_id, metadata_dict)

HOLDS_POSITION_EDGES: list[tuple[str, str, dict[str, str]]] = [
    # Stoic compatibilism
    (
        "person_chrysippus_280_206bce_i9j0k1l2",
        "position_compatibilism",
        {"note": "Chrysippus's causal taxonomy (principal vs. auxiliary causes) "
         "is widely characterized by modern scholars as a form of compatibilism "
         "(cf. Bobzien 1998, Frede 2011)."},
    ),
    (
        "person_epictetus_of_hierapolis_3c385bc2",
        "position_compatibilism",
        {"note": "Epictetus's dichotomy of control (ta eph' hēmin) preserves "
         "moral agency within a determined cosmos, often read as compatibilist "
         "(cf. Long 2002)."},
    ),
    (
        "person_boethius_480_524ce_w3x4y5z6",
        "position_compatibilism",
        {"note": "Boethius's solution in Consolation V — God's eternal 'nunc stans' "
         "seeing all times at once — is widely read as reconciling divine "
         "foreknowledge with human freedom (cf. Marenbon 2003)."},
    ),
    (
        "school_stoics",
        "position_compatibilism",
        {"note": "The Stoic school as a whole is commonly characterized as "
         "compatibilist in modern scholarship, though individual Stoics "
         "varied in emphasis (cf. Bobzien 1998)."},
    ),
    # Hard determinism
    (
        "person_cleanthes_assos_330_230bce",
        "position_hard_determinism",
        {"note": "Cleanthes's Hymn to Zeus and reported views suggest a stronger "
         "emphasis on fate's necessity than Chrysippus's nuanced causal "
         "distinctions; some scholars read him as closer to hard determinism "
         "(cf. Long & Sedley 1987)."},
    ),
    # Indeterminism
    (
        "person_epicurus_341_270bce_j0k1l2m3",
        "position_indeterminism",
        {"note": "Epicurus introduced the atomic swerve (parenklisis) to break "
         "the chain of necessity and ground voluntary action "
         "(cf. Sedley 1983, O'Keefe 2005)."},
    ),
    (
        "school_epicureans",
        "position_indeterminism",
        {"note": "The Epicurean school maintained that atomic indeterminacy "
         "via the swerve provides the physical basis for free volition."},
    ),
    # Libertarian free will
    (
        "person_alexander_aphrodisias_fl200ce_n5o6p7q8",
        "position_libertarianism_freewill",
        {"note": "Alexander's De Fato argues that humans possess genuine "
         "alternative possibilities, which modern scholars often characterize "
         "as anticipating libertarian incompatibilism (cf. Sharples 1983, "
         "Bobzien 1998). The anachronism of the label is debated."},
    ),
    (
        "person_origen_alexandria_185_254ce_s9t0u1v2",
        "position_libertarianism_freewill",
        {"note": "Origen's De Principiis III.1 argues for genuine self-determination "
         "(autexousion), often characterized by scholars as proto-libertarian, "
         "though the anachronism of the label is debated "
         "(cf. Bobzien 2014, Frede 2011)."},
    ),
    # Augustine: early libertarian, late theological determinist
    (
        "person_augustine_hippo_d430",
        "position_libertarianism_freewill",
        {"note": "The early Augustine (De Libero Arbitrio, c. 388-395) defends "
         "genuine human free will and moral responsibility for sin, a position "
         "sometimes characterized as proto-libertarian."},
    ),
    (
        "person_augustine_hippo_d430",
        "position_theological_determinism",
        {"note": "The late Augustine (anti-Pelagian writings, c. 412-430) "
         "increasingly emphasizes irresistible grace and predestination, "
         "a position widely characterized as theological determinism "
         "(cf. Stump 2001, Wetzel 1992)."},
    ),
    # Soft determinism
    (
        "person_seneca_4bce_65ce_a1b2c3d4",
        "position_soft_determinism",
        {"note": "Seneca's emphasis on inner freedom and willing acceptance of "
         "fate (amor fati) within a determined cosmos is sometimes read as "
         "a form of what modern scholars call soft determinism."},
    ),
    # Academic skepticism on fate
    (
        "person_carneades_214_129bce_l2m3n4o5",
        "position_academic_skepticism_fate",
        {"note": "Carneades argued against both Stoic fate and Epicurean "
         "indeterminism, maintaining voluntary action needs neither "
         "necessitation nor swerves (reported by Cicero, De Fato)."},
    ),
    # Fatalism
    (
        "person_diodorus_cronus_48ef6200",
        "position_fatalism",
        {"note": "Diodorus Cronus's Master Argument is widely taken to yield "
         "a fatalist conclusion: if only what is or will be true is possible, "
         "the future is fixed (cf. Prior 1967, Bobzien 1998)."},
    ),
]


def main() -> None:
    db_url = get_db_url()
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")

    # ── Verify all referenced source nodes exist ────────────────────
    source_ids = {e[0] for e in HOLDS_POSITION_EDGES}
    for sid in sorted(source_ids):
        cur.execute("SELECT node_id FROM kg_nodes WHERE node_id = %s", (sid,))
        if not cur.fetchone():
            print(f"ERROR: Source node '{sid}' not found in kg_nodes.")
            conn.close()
            sys.exit(1)
    print(f"All {len(source_ids)} source nodes verified.")

    # ── Insert position nodes ───────────────────────────────────────
    node_values = [
        (
            n["node_id"],
            n["label"],
            "position",
            n["description"],
            n["period"],
            json.dumps({"position_type": "philosophical_stance"}),
        )
        for n in POSITION_NODES
    ]

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO kg_nodes (node_id, label, type, description, period, metadata)
        VALUES %s
        ON CONFLICT (node_id) DO NOTHING
        """,
        node_values,
        template="(%s, %s, %s, %s, %s, %s::jsonb)",
    )
    print(f"Inserted {cur.rowcount} position nodes.")

    # ── Insert holds_position edges ─────────────────────────────────
    edge_values = [
        (src, tgt, "holds_position", json.dumps(meta))
        for src, tgt, meta in HOLDS_POSITION_EDGES
    ]

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO kg_edges (source_id, target_id, relation, metadata)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        edge_values,
        template="(%s, %s, %s, %s::jsonb)",
    )
    print(f"Inserted {cur.rowcount} holds_position edges.")

    conn.commit()
    print("COMMITTED successfully.")
    conn.close()


if __name__ == "__main__":
    main()
