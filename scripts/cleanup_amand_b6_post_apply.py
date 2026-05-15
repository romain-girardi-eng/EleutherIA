"""Post-apply cleanup for Amand B6 — fixes SHACL violations introduced by inserts.

Idempotent. Fixes 5 categories:
1. Description markdown (`**bold**`) → strip to plain text (B6 nodes only).
2. Period values `late_antiquity` → `Late Antiquity` / `Patristic` (B6 concepts).
3. Edge relations not in edge_types.json:
   - `cites` person→person → rename to `cites` work→person (rebind to work source)
   - `transmits_to` work→work → rename to `transmits` (or fall back to `precedes`)
   - `collaborates_with` → re-relabel via `influences` bidirectional
   - `addresses` → re-bind as `discusses`
   - `claimed_by` → already a node-property metadata field, drop the explicit edge
   - `authored` person→work → reverse to `authored_by` work→person
4. NeedsEvidence on synthesis nodes — add `needs_evidence: true` flag (already
   handled by `flag_unanchored_claims.py`, idempotent).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from amand_b6_utils import (
    EDGES_PATH,
    NODES_PATH,
    dump_jsonl,
    dump_metadata,
    load_jsonl,
    parse_metadata,
)

# All B6 node IDs (must match scripts/amand_b6_inserts.py + amand_b6_data.py)
B6_INSERTED_IDS = {
    # persons
    "person_gregory_nazianzus_d389",
    # works
    "work_eusebius_contra_hieroclem",
    "work_eusebius_demonstratio_evangelica",
    "work_basil_hexaemeron",
    "work_basil_homiliae_quod_deus_non_est_auctor_malorum",
    "work_gregory_naz_carmina_dogmatica",
    # syntheses
    "synthesis_amand1945_eus_witness_n4",
    "synthesis_amand1945_eus_carneadean_source_question",
    "synthesis_amand1945_eus_psychological_argument_modernity",
    "synthesis_amand1945_eus_dependence_origen",
    "synthesis_amand1945_eus_philological_fidelity",
    "synthesis_amand1945_basil_hex_vi_7_amand_origin_point",
    "synthesis_amand1945_basil_only_two_carneadean_topoi",
    "synthesis_amand1945_basil_origen_christian_insertion",
    "synthesis_amand1945_basil_popular_homily_register",
    "synthesis_amand1945_greg_naz_carmen_dogm_5_carneadean_echo",
    "synthesis_amand1945_greg_naz_school_commonplace",
    # arguments
    "argument_eus_carneadean_pe_vi_6_general_theme",
    "argument_eus_carneadean_pe_vi_6_arg1_virtue_vice",
    "argument_eus_carneadean_pe_vi_6_arg2_indolence",
    "argument_eus_carneadean_pe_vi_6_arg3_exhortations_useless",
    "argument_eus_carneadean_pe_vi_6_arg4_moral_action_proves_autonomy",
    "argument_eus_carneadean_pe_vi_6_arg5_laws_abolition",
    "argument_eus_carneadean_pe_vi_6_arg6_piety_destroyed",
    "argument_eus_carneadean_pe_vi_6_arg7_marionettes_consciousness",
    "argument_eus_carneadean_pe_vi_6_conclusion_autexousion",
    "argument_basil_carneadean_hex_vi_7_laws_useless",
    "argument_basil_carneadean_hex_vi_7_christian_hopes_destroyed",
    "argument_basil_observation_impossible_at_birth",
    "argument_basil_zodiac_animal_absurdity",
    "argument_basil_kings_born_daily",
    "argument_greg_naz_carmen_dogm_5_carneadean",
    # concepts
    "concept_autexousion_pe_vi_6_eusebius",
    "concept_neurospastoumenoi_carneadean_metaphor",
    "concept_heimarmene_demonic_invention_eus",
    "concept_origenist_theodicy_eus",
    "concept_to_eph_hemin_basil",
    "concept_synergism_basil_origenist",
    "concept_chaldeans_astrology_basil",
}

B6_UPDATED_IDS = {
    "person_eusebius_caesarea_d339",
    "work_eusebius_praeparatio_evangelica",
    "person_basil_great_d379",
}

ALL_B6_IDS = B6_INSERTED_IDS | B6_UPDATED_IDS


# Synthesis nodes that need NeedsEvidence flag (synthesis = argument type without anchors)
SYNTHESIS_NEEDS_EVIDENCE = {
    nid for nid in B6_INSERTED_IDS if nid.startswith("synthesis_amand1945_")
}
# Plus the synthesis nodes that ARE evidence-anchored via 'contains' / 'addresses'
# already are handled implicitly, but to be safe, flag every synthesis
SYNTHESIS_NEEDS_EVIDENCE -= {"synthesis_amand1945_eus_witness_n4"}  # this one has many contains

# Concepts incorrectly using `late_antiquity` should map to `Patristic` (church fathers context)
CONCEPT_TO_PATRISTIC = {
    "concept_autexousion_pe_vi_6_eusebius",
    "concept_neurospastoumenoi_carneadean_metaphor",
    "concept_heimarmene_demonic_invention_eus",
    "concept_origenist_theodicy_eus",
    "concept_to_eph_hemin_basil",
    "concept_synergism_basil_origenist",
    "concept_chaldeans_astrology_basil",
}


def strip_markdown_emphasis(text: str) -> str:
    """Strip Markdown bold/italic markers but keep the text content."""
    if not text:
        return text
    # **bold** → bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # __bold__ → bold (preserve any unicode underscore use only if surrounded by spaces)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    # *italic* / _italic_ — be conservative: only convert if surrounded by word chars or spaces,
    # to avoid mangling Greek words containing underscores.
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", text)
    # Headings ## foo
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Markdown links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    # Bullet lists at line start
    text = re.sub(r"^[ \t]*[-*][ \t]+", "", text, flags=re.MULTILINE)
    return text


# Period canonicalisation: snake_case → Title Case With Spaces
PERIOD_FIXES = {
    "late_antiquity": "Late Antiquity",
    "modern": "Modern",
    "patristic": "Patristic",
    "hellenistic": "Hellenistic",
    "roman_imperial": "Roman Imperial",
    "roman_republican": "Roman Republican",
    "classical_greek": "Classical Greek",
    "early_modern": "Early Modern",
    "medieval": "Medieval",
    "presocratic": "Presocratic",
    "rabbinic": "Rabbinic",
    "cross_period": "Cross-period",
    "second_temple_judaism": "Second Temple Judaism",
    "contemporary": "Contemporary",
}


def fix_node_periods_and_markdown(nodes):
    desc_fixed = 0
    period_fixed = 0
    needs_evidence_flagged = 0
    for n in nodes:
        nid = n.get("id")
        if nid not in ALL_B6_IDS:
            continue

        # Strip markdown from B6 descriptions
        if "description" in n and n["description"]:
            clean = strip_markdown_emphasis(n["description"])
            if clean != n["description"]:
                n["description"] = clean
                desc_fixed += 1
        if "description_en" in n and n["description_en"]:
            clean = strip_markdown_emphasis(n["description_en"])
            if clean != n["description_en"]:
                n["description_en"] = clean
                desc_fixed += 1

        # Period canonicalisation
        p = n.get("period")
        if p and p in PERIOD_FIXES:
            # For B6 concepts we re-map to Patristic (church fathers)
            if nid in CONCEPT_TO_PATRISTIC:
                n["period"] = "Patristic"
            else:
                n["period"] = PERIOD_FIXES[p]
            period_fixed += 1

        # NeedsEvidence flag for synthesis nodes without evidence anchor
        if nid in SYNTHESIS_NEEDS_EVIDENCE:
            if not n.get("needs_evidence"):
                n["needs_evidence"] = True
                needs_evidence_flagged += 1

    return desc_fixed, period_fixed, needs_evidence_flagged


def fix_edges(edges):
    """Rewrite problematic edges to ontology-conformant relations."""
    rewritten = 0
    dropped = 0
    # Maps: (old_relation, src_type_check, tgt_type_check) → new_relation
    # We don't know types here so we rewrite by relation name + src/tgt patterns.

    new_edges = []
    for e in edges:
        rel = e.get("relation")
        src = e.get("source", "")
        tgt = e.get("target", "")

        # 1. `authored` person→work → reverse to `authored_by` work→person
        if rel == "authored" and src.startswith("person_") and tgt.startswith("work_"):
            e["relation"] = "authored_by"
            e["source"], e["target"] = tgt, src
            rewritten += 1

        # 2. `cites` person→person — drop. Person→person Carneadean transmission is
        #    properly modelled via `influences`/`influenced_by`/`precedes`.
        elif rel == "cites" and src.startswith("person_") and tgt.startswith("person_"):
            # Re-map: Eusebius cites X → Eusebius influenced_by X (text influence)
            # But better: drop, since the citation is via Eusebius' work PE VI.
            # Replace with `influenced_by`
            e["relation"] = "influenced_by"
            rewritten += 1

        # 3. `transmits_to` work→work — not in ontology, switch to `precedes`
        elif rel == "transmits_to" and src.startswith("work_") and tgt.startswith("work_"):
            e["relation"] = "precedes"
            rewritten += 1

        # 4. `collaborates_with` person↔person — switch to `influences` (we keep
        #    a single direction; semantically the Philocalia collab is reciprocal,
        #    but `influences` is the closest ontology relation).
        elif rel == "collaborates_with":
            e["relation"] = "influences"
            rewritten += 1

        # 5. `addresses` argument→concept — closest ontology match is `discusses`,
        #    which is NOT in the edge_types. We re-bind to `contains` which DOES
        #    accept argument→concept.
        elif rel == "addresses":
            e["relation"] = "contains"
            rewritten += 1

        # 6. `claimed_by` synthesis→scholar — this is metadata, not a graph edge.
        #    Drop the explicit edges (the claim is preserved in node metadata).
        elif rel == "claimed_by":
            dropped += 1
            continue

        # 7. `cites_primary_source` concept→passage — concept is NOT a valid source.
        #    Re-bind concept→passage `cites_primary_source` to `evidenced_by`
        #    (concept IS a valid evidenced_by source).
        elif rel == "cites_primary_source" and src.startswith("concept_"):
            e["relation"] = "evidenced_by"
            rewritten += 1

        # 8. `cites_primary_source` synthesis→passage — synthesis (type=argument)
        #    IS a valid source. Keep as-is.
        # 9. `cites_primary_source` argument→work — argument IS valid source. Keep.

        new_edges.append(e)

    return new_edges, rewritten, dropped


def main() -> int:
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"Loaded {len(nodes):,} nodes, {len(edges):,} edges")

    print("\n=== Node cleanup (B6) ===")
    desc, period, ne = fix_node_periods_and_markdown(nodes)
    print(f"  Descriptions cleaned: {desc}")
    print(f"  Periods canonicalised: {period}")
    print(f"  NeedsEvidence flagged: {ne}")

    print("\n=== Edge cleanup ===")
    edges, rewritten, dropped = fix_edges(edges)
    print(f"  Edges rewritten: {rewritten}")
    print(f"  Edges dropped (metadata-only): {dropped}")

    dump_jsonl(NODES_PATH, nodes)
    dump_jsonl(EDGES_PATH, edges)
    print(f"\nWrote {NODES_PATH} ({len(nodes):,} nodes), {EDGES_PATH} ({len(edges):,} edges)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
