"""SC 226 (Junod 1976) Philocalia ingestion — phase 2.

Phase-1 (`ingest_origen_philocalia_sc226_junod.py`) handled:
  - 4 Philocalia 21 sub-anchor shells via SC 268 Greek extracts (RTF gap)
  - 22 existing Philocalia 23 paragraph passages + 23_titulus_1

Phase 2 closes the remaining gaps:
  A) The 3 mis-prefixed titulus passages (23_titulus_12 / _14 / _22) — regex
     bug in phase 1 only caught `_titulus_1$`. Same enrichment as phase-1 Part B
     using the paragraph-N text from RTF (the existing description already holds
     the start of §N — confirmed accurate).
  B) Create 21 new passage nodes for Junod's chap 25/26/27 paragraphs that
     have no KG representation yet:
       - Philocalia 25 §§1-4              (4 passages)
       - Philocalia 26 §§1-8              (8 passages)
       - Philocalia 27 §§1-8 + §12        (9 passages)
     Each new passage gets: description (French Junod), description_grc (Greek
     Junod), description_en (English summary I provide here from the content),
     part_of → work_origen_philocalia edge, full SC 226 citation metadata.

Idempotent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"

SC226_TXT = Path("/tmp/sc226_junod.txt")
SC226_RTF = "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf"

JUNOD_EDITION = (
    "É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre), "
    "Sources Chrétiennes 226, Paris: Cerf, 1976."
)

PAGE_MARKER = re.compile(r"---\s*\d+\s*---")
HEADER_PAR_RE = re.compile(r"cap\.\s*:\s*(\d+),\s*par\.\s*:\s*(\d+)")
JUNK_LINE_RE = re.compile(r"^\s*(Origenes|Origène|Philocalia|Philocalie|<<.*Previous.*Next.*>>|<<.*Précédent.*Suivant.*>>)\s*$")
GREEK_CHARS = re.compile(r"[Α-Ωα-ωἀ-ᾼ]")


def _strip_line_number(line: str) -> str:
    parts = line.split("\t", 1)
    if len(parts) == 2 and parts[0].strip().isdigit():
        return parts[1]
    return line


def _clean(s: str) -> str:
    s = PAGE_MARKER.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_sc226_paragraphs(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    """Return {(chap, par): {greek, french}} — paragraphs only (no titulus).
    Concatenates multiple blocks per (chap, par)."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    out: dict[tuple[int, int], dict[str, str]] = {}
    current: tuple[int, int] | None = None
    buf = {"greek": [], "french": []}

    def flush():
        nonlocal current
        if current is None:
            return
        slot = out.setdefault(current, {"greek": "", "french": ""})
        gk = _clean(" ".join(buf["greek"]))
        fr = _clean(" ".join(buf["french"]))
        if gk:
            slot["greek"] = (slot["greek"] + " " + gk).strip() if slot["greek"] else gk
        if fr:
            slot["french"] = (slot["french"] + " " + fr).strip() if slot["french"] else fr
        buf["greek"].clear()
        buf["french"].clear()

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if JUNK_LINE_RE.match(line):
            continue
        m_par = HEADER_PAR_RE.search(line)
        # Treat titulus markers as block boundaries but don't accumulate them
        is_titulus = "titulus ante par" in line
        if is_titulus:
            flush()
            current = None
            continue
        if m_par:
            flush()
            current = (int(m_par.group(1)), int(m_par.group(2)))
            continue
        if current is None:
            continue
        cleaned = _strip_line_number(line).strip()
        if not cleaned:
            continue
        if GREEK_CHARS.search(cleaned):
            buf["greek"].append(cleaned)
        else:
            cleaned = re.sub(r"<[^>]+>", " ", cleaned).strip()
            cleaned = _clean(cleaned)
            if cleaned and not cleaned.startswith("---"):
                buf["french"].append(cleaned)

    flush()
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def parse_md(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


# Brief English summaries for the 21 new passages — keep them schematic and
# clearly editorial; they DO NOT translate Junod's French, they describe the
# thematic content of the section so future search/navigation works.
NEW_PASSAGE_EN_SUMMARIES: dict[tuple[int, int], dict[str, str]] = {
    (25, 1): {"label_en": "Whence God's hardening of Pharaoh's heart — opening",
              "summary": "Philocalia 25.1. Opens the second great theodicy question: how can Scripture say God 'hardens' a heart, if our actions remain ours? Excerpt from Origen's Commentary on Exodus."},
    (25, 2): {"label_en": "Hardening as withdrawal of grace, not direct causation",
              "summary": "Philocalia 25.2. Origen's first solution: God 'hardens' by withdrawing the help his providence would normally extend; the agent's own disposition then completes the hardening."},
    (25, 3): {"label_en": "Comparison with the sun softening wax / hardening clay",
              "summary": "Philocalia 25.3. The famous solar analogy: the same divine action softens the well-disposed (wax) and hardens the ill-disposed (clay). The cause of the differing effect is in the recipient, not the action."},
    (25, 4): {"label_en": "Hardening preserves human freedom",
              "summary": "Philocalia 25.4. Closing: this reading reconciles Exodus's language with the doctrine of free will; hardening is consequent on prior choices, not antecedent divine determination."},

    (26, 1): {"label_en": "Why God's hardening serves the hardened person's good — opening",
              "summary": "Philocalia 26.1. Origen's third move: even where hardening is genuinely God's pedagogical act, it is for the agent's eventual good. From the Commentary on Romans / Exodus exegesis."},
    (26, 2): {"label_en": "Pedagogical analogy: parent + child",
              "summary": "Philocalia 26.2. The parent who lets the child experience the consequence of obstinacy in order to break it. Hardening as paideia."},
    (26, 3): {"label_en": "Physician/sickness analogy",
              "summary": "Philocalia 26.3. The physician who lets a disease run its course so the patient finally seeks cure. Pharaoh's hardening fits this pattern."},
    (26, 4): {"label_en": "Soul-corrupting indulgence is worse than hardening",
              "summary": "Philocalia 26.4. To never feel divine pressure is more spiritually dangerous than to suffer it; complacency is the real loss."},
    (26, 5): {"label_en": "The 'sleep of the soul' as the worse alternative",
              "summary": "Philocalia 26.5. Origen invokes scriptural images of spiritual sleep / numbness as the result of un-disturbed sinfulness."},
    (26, 6): {"label_en": "Hardening as protection from greater evil",
              "summary": "Philocalia 26.6. Sometimes hardening prevents a soul from compounding ruin — a temporary pedagogical brake."},
    (26, 7): {"label_en": "Scriptural confirmations",
              "summary": "Philocalia 26.7. Origen catalogs further OT/NT passages that fit the same logic (Isaiah, Romans 9-11)."},
    (26, 8): {"label_en": "Conclusion: hardening serves freedom + restoration",
              "summary": "Philocalia 26.8. Synthesis: hardening, properly understood, is always provisional, pedagogical, and ordered to the eventual restoration of the will (apokatastasis seeds)."},

    (27, 1): {"label_en": "On 'I will harden Pharaoh's heart' (Ex 4:21) — opening",
              "summary": "Philocalia 27.1. The most pointed scriptural difficulty for free will: God's first-person announcement that he will harden Pharaoh's heart. Origen begins by stating the apparent contradiction."},
    (27, 2): {"label_en": "Same divine action, different responses (Pharaoh vs the elect)",
              "summary": "Philocalia 27.2. The same plagues that hardened Pharaoh softened others; cause of differing response lies in the recipient."},
    (27, 3): {"label_en": "God's foreknowledge does not cause Pharaoh's choice",
              "summary": "Philocalia 27.3. Origen distinguishes prognosis (foreknowledge) from causal predestination. God foresees, does not compel."},
    (27, 4): {"label_en": "Scripture's mode of speech: God 'does' what he permits",
              "summary": "Philocalia 27.4. Hebrew idiom: Scripture attributes to God what he permits to occur; this is a stylistic, not metaphysical, ascription."},
    (27, 5): {"label_en": "Pharaoh's own prior hardening sets up the divine 'hardening'",
              "summary": "Philocalia 27.5. Origen carefully reads Exodus's sequence: Pharaoh hardens his OWN heart first; God's later 'hardening' confirms what Pharaoh has chosen."},
    (27, 6): {"label_en": "Comparison with the sun (continued — recapitulation)",
              "summary": "Philocalia 27.6. Returns to the solar analogy: divine action is uniform, recipients differ."},
    (27, 7): {"label_en": "The clay/brick simile from Exodus's narrative",
              "summary": "Philocalia 27.7. The Hebrews labor in clay and brick; their cry rises to God because of WORKS, not because of the clay. Echoes Origen's reading of Rom 9:21 (potter/clay)."},
    (27, 8): {"label_en": "Closing: free will preserved through the entire Pharaoh narrative",
              "summary": "Philocalia 27.8. Synthesis of chapter 27: nothing in Exodus's hardening language requires denying autexousion; the doctrine of free will reads the narrative consistently."},
    (27, 12): {"label_en": "Closing of the entire 'Sur le libre arbitre' anthology",
               "summary": "Philocalia 27.12. The final section of Junod's anthology — recapitulation of Origen's anti-determinist doctrine: signs not causes, foreknowledge not coercion, hardening not predestination."},
}


def make_new_passage(chap: int, par: int, greek: str, french: str) -> dict[str, Any]:
    info = NEW_PASSAGE_EN_SUMMARIES.get((chap, par), {})
    label_en = info.get("label_en", f"Philocalia {chap}.{par}")
    summary = info.get("summary", f"Origen, Philocalia {chap}.{par} (Junod 1976 SC 226).")
    nid = f"passage_origen_philocalia_{chap}_{par}"
    md = {
        "cts_urn": f"urn:cts:greekLit:tlg2042.tlg028:{chap}.{par}",
        "source_quality": "critical_edition_sc226_junod_1976",
        "principal_edition": JUNOD_EDITION,
        "greek_witness": "Junod 1976 SC 226 (direct)",
        "ingested_from": {"sc226_txt_export": str(SC226_TXT), "sc226_rtf_source": SC226_RTF},
        "philocalia_chapter": chap,
        "philocalia_paragraph": par,
    }
    return {
        "id": nid,
        "type": "passage",
        "label": f"Origen, Philocalia {chap}.{par}: {label_en}",
        "description": french,  # French primary
        "description_grc": greek,
        "description_en": summary,
        "period": "Patristic",
        "confidence": 0.95,
        "metadata": json.dumps(md, ensure_ascii=False),
    }


def make_part_of_edge(passage_id: str) -> dict[str, Any]:
    return {
        "source": passage_id,
        "target": "work_origen_philocalia",
        "relation": "part_of",
        "confidence": 0.95,
        "metadata": {
            "anchor_kind": "philocalia_chapter_paragraph",
            "edition": "Junod 1976 SC 226",
        },
    }


def edge_exists(edges: list[dict[str, Any]], src: str, tgt: str, rel: str) -> bool:
    return any(e.get("source") == src and e.get("target") == tgt and e.get("relation") == rel for e in edges)


def main() -> int:
    print(f"Parsing {SC226_TXT.name} …")
    junod = parse_sc226_paragraphs(SC226_TXT)
    print(f"  parsed {len(junod)} (chap, par) blocks")

    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    by_id = {n["id"]: n for n in nodes}
    print(f"Loaded {len(nodes):,} nodes, {len(edges):,} edges")

    # ==========================================================================
    # Part A — fix the 3 mis-prefixed titulus passages
    # ==========================================================================
    print("\n=== Part A: enrich 23_titulus_12 / _14 / _22 ===")
    titulus_count = 0
    for par_anchor in [12, 14, 22]:
        nid = f"passage_origen_philocalia_23_titulus_{par_anchor}"
        node = by_id.get(nid)
        if node is None:
            print(f"  [missing] {nid}")
            continue
        entry = junod.get((23, par_anchor))
        if not entry:
            print(f"  [no-junod] {nid}")
            continue
        greek = entry.get("greek", "")
        french = entry.get("french", "")
        if not (greek or french):
            print(f"  [empty] {nid}")
            continue
        existing_greek = node.get("description") or ""
        existing_is_greek = bool(GREEK_CHARS.search(existing_greek))

        if french:
            node["description"] = french
        if greek:
            node["description_grc"] = greek
            if existing_is_greek and existing_greek and existing_greek != greek:
                md = parse_md(node)
                md.setdefault("alt_greek_pre_junod_ingest", existing_greek)
                node["metadata"] = md  # re-serialized below

        md = parse_md(node)
        md["source_quality"] = "critical_edition_sc226_junod_1976"
        md["principal_edition"] = JUNOD_EDITION
        md["greek_witness"] = "Junod 1976 SC 226 (direct)"
        md["philocalia_titulus_for_par"] = par_anchor
        md["ingested_from"] = {"sc226_txt_export": str(SC226_TXT)}
        md.pop("needs_text_ingestion", None)
        node["metadata"] = json.dumps(md, ensure_ascii=False)
        node.pop("needs_evidence", None)
        node["confidence"] = max(node.get("confidence", 0.0) or 0.0, 0.95)
        titulus_count += 1
        print(f"  [enriched] {nid}  (grc={len(greek)} fr={len(french)} chars)")

    # ==========================================================================
    # Part B — create new Philocalia 25/26/27 passages
    # ==========================================================================
    print("\n=== Part B: create new Philocalia 25/26/27 passages ===")
    targets = (
        [(25, p) for p in range(1, 5)]
        + [(26, p) for p in range(1, 9)]
        + [(27, p) for p in [1, 2, 3, 4, 5, 6, 7, 8, 12]]
    )
    new_passages = 0
    new_edges = 0
    skipped_existing = 0
    skipped_no_text = 0

    for chap, par in targets:
        nid = f"passage_origen_philocalia_{chap}_{par}"
        if nid in by_id:
            skipped_existing += 1
            continue
        entry = junod.get((chap, par))
        if not entry or not (entry.get("greek") or entry.get("french")):
            skipped_no_text += 1
            print(f"  [no-text] Philocalia {chap}.{par}")
            continue
        passage = make_new_passage(chap, par, entry.get("greek", ""), entry.get("french", ""))
        nodes.append(passage)
        by_id[nid] = passage
        new_passages += 1
        # part_of edge
        edge = make_part_of_edge(nid)
        if not edge_exists(edges, edge["source"], edge["target"], edge["relation"]):
            edges.append(edge)
            new_edges += 1
        if new_passages <= 5:
            print(f"  [new] {nid}  (grc={len(entry.get('greek') or '')} fr={len(entry.get('french') or '')} chars)")

    if new_passages > 5:
        print(f"  ... ({new_passages - 5} more)")
    print(
        f"\nPart A titulus enrichments: {titulus_count}\n"
        f"Part B new passages: {new_passages}  | new part_of edges: {new_edges}\n"
        f"  skipped (already exist): {skipped_existing}\n"
        f"  skipped (no text in Junod): {skipped_no_text}"
    )
    print(f"\nFinal counts: {len(nodes):,} nodes, {len(edges):,} edges")
    dump_jsonl(NODES_PATH, nodes)
    dump_jsonl(EDGES_PATH, edges)
    print(f"Wrote {NODES_PATH} and {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
