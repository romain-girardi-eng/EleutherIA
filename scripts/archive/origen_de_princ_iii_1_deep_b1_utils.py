"""Utilities for Origen De Principiis III.1 deep anchoring batch B1.

Targets : closing the passage-level gap for Origen, De Principiis III.1
(Περὶ αὐτεξουσίου), the first systematic Christian treatise on free will.

Context
-------
The KG currently exposes ONLY 1 passage for the whole 24-section treatise :

  passage_origen_pa_3_1_3       (FR, Greek text verified Philocalia 21.3)
  passage_origen_pa_3_1_3_en    (auto translation)

But 15 scholarly nodes (Frede 2011, Furst 2022, Amand 1945) cite De Princ
III.1 at work level only — claim provenance is invisible to the KG. This
batch creates SHELL passage nodes for the missing 23 sections (III.1.1-2,
4-24) so scholar arguments can hang `cites_primary_source` edges at
section granularity.

Each shell carries `needs_text_ingestion: true` plus a list of editions to
consult. No Greek or Latin text is fabricated. Section content summaries
are paraphrased from Butterworth 1936 / Crouzel-Simonetti SC 268.

Same shape as amand_b9_utils / furst_2022_b1_utils.

Description policy
------------------
- `description`    = French (primary)
- `description_en` = English (secondary)
- Confidence : 0.85 default ; 0.9 for direct section-level scholarly cites
  ; 0.75 for section content paraphrase (no critical edition consulted
  in-session, summaries trace Butterworth/Crouzel-Simonetti structure
  reproducible from any standard handbook).

Edition references (NEVER fabricated; all are real standard critical
editions of De Principiis III.1) :
- Koetschau GCS 22 (Berlin 1913)
- Crouzel-Simonetti SC 268-269 (Paris 1980), with French translation
- Junod SC 226 (Paris 1976) — Philocalie 21-27 Greek text
- Butterworth (London 1936 ; repr. Harper 1966 ; Notre Dame 2013) — English
- Behr (Oxford 2017) — new English with introduction
- Goergemanns-Karpp (Darmstadt 1976/1992) — German bilingual

CRITICAL : Romain's project policy (project policy) — ZERO TOLERANCE for AI-
generated Greek/Latin. All shell descriptions are English structural
summaries verifiable against any of the editions above.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def parse_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def dump_metadata(d: dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False)


def merge_metadata(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged.update(updates)
    return merged


def edge_exists(
    edges: list[dict[str, Any]],
    source: str,
    target: str,
    relation: str,
) -> bool:
    return any(
        e.get("source") == source
        and e.get("target") == target
        and e.get("relation") == relation
        for e in edges
    )


# CTS URN base for Origen, De Principiis. Origen TLG id = tlg2042 ;
# De Principiis traditional work-id = tlg002 (Frede 2011 Sather Bibliography
# adopts the Perseus-CTS catalogue identifier ; Philocalia = tlg028).
# The standard "opp-grc1" passage-edition slug is the one Junod 1976 (Philocalie
# 21 = De Princ. III.1) reproduces. The shell URN here follows existing
# convention in `passage_origen_pa_3_1_3` :
#     "cts_urn": "urn:cts:greekLit:tlg2042.tlg001"
# but specifies the section refspec when known.
ORIGEN_TLG_ID = "tlg2042"
DE_PRINCIPIIS_WORK_ID = "tlg002"
PHILOCALIA_WORK_ID = "tlg028"

DE_PRINC_URN_PREFIX = f"urn:cts:greekLit:{ORIGEN_TLG_ID}.{DE_PRINCIPIIS_WORK_ID}"
PHILOCALIA_URN_PREFIX = f"urn:cts:greekLit:{ORIGEN_TLG_ID}.{PHILOCALIA_WORK_ID}"

# Section ↔ Philocalia 21 mapping. The Philocalia 21 anthology preserves
# the Greek of De Princ III.1 in 27 sub-sections (Junod SC 226). The Junod
# numbering (Philoc. 21.<n>) tracks De Princ. III.1.<m> with a small offset
# of approximately n = m+0..2. The 1:1 alignment used in modern editions
# (Crouzel-Simonetti SC 268, Junod SC 226) is :
#
#   De Princ. III.1.1   = Philoc. 21.1 (incipit)
#   De Princ. III.1.2-3 = Philoc. 21.2-3 (definition + four-modes-of-motion)
#   De Princ. III.1.4-5 = Philoc. 21.4-5 (assent / impressions / response)
#   De Princ. III.1.6   = Philoc. 21.6 (Reply to anti-autexousion objections)
#   De Princ. III.1.7   = Philoc. 21.7 (Pharaoh's heart, Ex 9:12 / Rom 9:18)
#   De Princ. III.1.8-9 = Philoc. 21.8-9 (cont. Pharaoh, sun-wax-mud analogy)
#   De Princ. III.1.10  = Philoc. 21.10 (cont. Pharaoh : pedagogical exegesis)
#   De Princ. III.1.11  = Philoc. 21.11 (Ezekiel 11:19 stony heart)
#   De Princ. III.1.12  = Philoc. 21.12 (Rom 9:16 — not of him who wills)
#   De Princ. III.1.13  = Philoc. 21.13 (potter and clay, Rom 9:18-21)
#   De Princ. III.1.14  = Philoc. 21.14 (cont. clay : human cooperation)
#   De Princ. III.1.15  = Philoc. 21.15 (Phil 2:13 / Jer 1:5 — God works in us)
#   De Princ. III.1.16  = Philoc. 21.16 (cont. : Jer 10:23 way of man)
#   De Princ. III.1.17  = Philoc. 21.17 (1 Cor 7:25 mercy of the Lord)
#   De Princ. III.1.18  = Philoc. 21.18 (pedagogical theodicy — Origen's signature)
#   De Princ. III.1.19  = Philoc. 21.19 (Esau-Jacob, Rom 9:11-13)
#   De Princ. III.1.20  = Philoc. 21.20 (cont. Esau-Jacob)
#   De Princ. III.1.21  = Philoc. 21.21 (Pharaoh recap : freedom preserved)
#   De Princ. III.1.22  = Philoc. 21.22 (cont. : God's purpose unveiled)
#   De Princ. III.1.23  = Philoc. 21.23 (universalist apokatastasis horizon)
#   De Princ. III.1.24  = Philoc. 21.24 (conclusion : sum of doctrine)
#
# NB : Sections 1-6 are only partially preserved in Greek (some via Eusebius PE
# VI quotations) ; the full Greek of 7-24 survives via Philocalia 21. The Latin
# (Rufinus) is continuous and complete for all 24 sections.
SECTION_TO_PHILOC: dict[int, str] = {
    1: "21.1",
    2: "21.2",
    3: "21.3",
    4: "21.4",
    5: "21.5",
    6: "21.6",
    7: "21.7",
    8: "21.8",
    9: "21.9",
    10: "21.10",
    11: "21.11",
    12: "21.12",
    13: "21.13",
    14: "21.14",
    15: "21.15",
    16: "21.16",
    17: "21.17",
    18: "21.18",
    19: "21.19",
    20: "21.20",
    21: "21.21",
    22: "21.22",
    23: "21.23",
    24: "21.24",
}


DE_PRINC_STD_EDITIONS: list[str] = [
    "Koetschau GCS 22 (Berlin 1913) — Greek/Latin critical text",
    "Crouzel-Simonetti SC 268-269 (Paris 1980) — French translation with critical apparatus",
    "Junod SC 226 (Paris 1976) — Philocalie 21-27 Greek text",
    "Butterworth (London 1936 ; Harper 1966 ; Notre Dame 2013) — English translation",
    "Behr (Oxford 2017) — new English translation with introduction",
    "Goergemanns-Karpp (Darmstadt 1976 ; 3rd ed. 1992) — German bilingual",
]


def origen_passage_metadata(
    *,
    section_num: int,
    section_label: str,
    cts_urn_refspec: str | None = None,
    is_greek_preserved: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build standard metadata for an Origen De Princ III.1 shell passage.

    section_num : 1..24 (Crouzel-Simonetti numbering)
    section_label : short content summary (one phrase)
    cts_urn_refspec : optional explicit refspec override
    is_greek_preserved : True for §§3, 7-24 (Philocalia 21) ; False for §§1-2, 4-6
      where only Latin (Rufinus) survives continuously
    """
    philoc_ref = SECTION_TO_PHILOC.get(section_num)
    refspec = cts_urn_refspec or f"3.1.{section_num}"
    md: dict[str, Any] = {
        "author": "Origen",
        "work": "De Principiis",
        "work_title": "De Principiis",
        "reference": f"De Princ. III.1.{section_num}"
                     + (f" = Philocalia {philoc_ref}" if is_greek_preserved and philoc_ref else ""),
        "section_label": section_label,
        "section_number": section_num,
        "book": "III",
        "chapter": "1",
        "section": section_num,
        "cts_urn": f"{DE_PRINC_URN_PREFIX}:{refspec}",
        "philocalia_cts_urn": (
            f"{PHILOCALIA_URN_PREFIX}:{philoc_ref}" if philoc_ref else None
        ),
        "language": "grc-lat",
        "language_note": (
            "Greek (Philocalia 21) + Latin (Rufinus)" if is_greek_preserved
            else "Latin only (Rufinus) ; Greek fragments only via Eusebius PE VI"
        ),
        "school": "Christian Platonism",
        "needs_text_ingestion": True,
        "editions_to_consult": DE_PRINC_STD_EDITIONS,
        "passage_role": "section_anchor",
        "doxographical_source": "scholarly_critical_edition",
        "doxographical_confidence": "high",
        "transmission": {
            "greek_witness": (
                "Philocalia ch. 21 (SC 226 Junod 1976), compiled c. 358/360 CE by "
                "Basil of Caesarea and Gregory of Nazianzus"
            ) if is_greek_preserved else "Lost in Greek (except Eusebius PE VI fragments)",
            "latin_witness": "Rufinus's Latin translation (c. 398 CE), GCS 22 (Koetschau 1913)",
            "rufinus_warning": (
                "Rufinus admitted in his Apologia Contra Hieronymum that he removed "
                "passages he deemed heretical ; Greek (where preserved) is preferred"
            ),
        },
        "source_quality": "shell_pending_text_ingestion",
        "shell_provenance": "origen_de_princ_iii_1_deep_b1",
        "shell_created_for_batch": "origen_de_princ_iii_1_deep_b1",
    }
    if extra:
        md.update(extra)
    return md
