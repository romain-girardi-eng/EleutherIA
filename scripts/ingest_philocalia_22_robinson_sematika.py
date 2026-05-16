"""Ingest Philocalia 22 (10 sections = Origen, Contra Celsum V.25-32 excerpts)
from the verified Sematika Robinson 1893 text.

CONTEXT
Philocalia 22 is titled "On the dispersion of rational, i.e. human souls, cryptically
signified through the building of the Tower [of Babel] and the consequent confusion
of tongues. In which also concerning many lords appointed to the scattered ones
according to the analogy of their condition" (Robinson). It excerpts Origen's
Contra Celsum Book V (chapters ~25-32, on Celsus's claim that nations should observe
their ancestral laws because regions were distributed to different cosmic overseers
— epoptai — at creation).

Why it matters for the free-will project:
  - §§1-5: Origen quotes + critiques Celsus's argument that ancestral custom is
    inviolable (Celsus is implicitly determinist: each region predestined to its
    laws via its appointed overseer).
  - §§6-10: Origen's mystical re-interpretation of Babel — souls retain their
    rational orientation toward truth (autexousion in cosmic context); Deut 32:8's
    "boundaries of nations" reflects providential ordering that respects free choice.

This material has NEVER been in the KG before. 10 new passage nodes + 10 part_of
edges to work_origen_philocalia.

SOURCE
  Sematika Philocalia.txt (verified-authentic Robinson 1893 OCR — see memory
  reference_sematika_philocalia_verified.md). Modern standard re-edition:
  Junod 1976 SC 226 chapter 22.

This script:
  1. Reads Sematika lines 3872-4090 (chapter 22 block, 219 lines, ~46KB Greek).
  2. Splits into 10 Robinson sections via "\b{n}\.\s+(?:[‘'\"\(]\s*)?[Α-ΩἈ-Ὦ]" regex.
  3. Cleans each section's Greek (strips MS sigla AB/ABC, biblical refs, line refs,
     page-number anchors, U+XXXX placeholders) and preserves the raw text with
     apparatus as a separate field.
  4. Creates a passage node per section with content-accurate editorial English
     summary (derived from reading the actual Greek, NOT speculation).
  5. Adds part_of edge to work_origen_philocalia.

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

SEMATIKA_PHILOC = Path("[local-path]")
CHAPTER_22_START_LINE = 3872  # 1-indexed: "αὐτεξουσίου. XXII. Τίς ἡ τῶν ἐπὶ τῆς λογικῶν…"
CHAPTER_22_END_LINE = 4091    # exclusive: line 4091 = "XXIII." (chap 23 start)

ROBINSON_EDITION = (
    "J. A. Robinson (ed.), The Philocalia of Origen, Cambridge: Cambridge University Press, 1893."
)
JUNOD_EDITION = (
    "É. Junod (ed.), Origène, Philocalie 21–27 (Sur le libre arbitre), "
    "Sources Chrétiennes 226, Paris: Cerf, 1976."
)

# Content-accurate English summaries (derived from reading each Greek section,
# verified against the apparatus references to Contra Celsum V.25 ff.).
EN_SUMMARIES: dict[int, dict[str, str]] = {
    1: {"label": "Celsus quoted: each nation's ancestral laws (CC V.25)",
        "summary": "Philocalia 22.1 = Contra Celsum V.25 ad init. Origen reproduces Celsus's text: 'The Jews became a peculiar nation, established laws according to local custom, and still keep them in private; they preserve whatever ancestral religion they happen to have — like all other men.' Sets up Celsus's culturally-relativist argument that every nation should retain its own customs."},
    2: {"label": "Celsus's cosmic claim: regions distributed to appointed overseers (epoptai)",
        "summary": "Philocalia 22.2. Celsus's deeper claim, quoted by Origen: laws must be kept 'not only because different peoples have come to think differently and one must observe what has been publicly sanctioned, but also because, as is likely, the parts of the earth were from the beginning distributed to different overseers (epoptai), apportioned by jurisdictions, and are administered in this way.' Celsus thereby attempts to ground regional law in a cosmic determinism (each region's law fixed by its assigned daimon)."},
    3: {"label": "Origen's challenge: explain HOW regions are governed by overseers, and what about Scythian patricide?",
        "summary": "Philocalia 22.3. Origen demands specificity from Celsus: explain HOW exactly the regions are partitioned to their overseers, and HOW each people's deeds are 'rightly done.' Test case: are the Scythians right (per their custom) to kill their fathers? Origen sets up the reductio: cultural relativism + cosmic-overseer determinism cannot justify every regional custom."},
    4: {"label": "The pious / impious paradox of cultural relativism",
        "summary": "Philocalia 22.4. Origen presses the paradox of Celsus's position: keeping one's ancestral laws is called pious, even when those laws sanction what another culture deems impious; conversely, the same act counts as impious among one people and not-impious among another, depending on whose ancestral laws are observed."},
    5: {"label": "Celsus's anti-Christian conclusion drawn out",
        "summary": "Philocalia 22.5. Origen extracts Celsus's hidden anti-Christian conclusion: 'all men ought to live according to their ancestral laws and would not be blamed for it; but Christians, who have abandoned their ancestral customs and are not even one homogeneous people like the Jews, are blameworthy for joining the teaching of Jesus.' Origen will deny that conserving ancestral custom is always pious."},
    6: {"label": "Transition to Origen's mystical response (Babel as cosmic theology)",
        "summary": "Philocalia 22.6. Origen judges the surface-level rebuttal sufficient for 'simpler' readers but indicates that more searching readers will be interested in a 'deeper, more mystical, hidden contemplation' (mystikē kai apporrētos theōria) about the dispersion of nations from creation. He now turns from refutation to constructive cosmic-theology."},
    7: {"label": "Deuteronomy 32:8 — boundaries of nations set by angels",
        "summary": "Philocalia 22.7. Origen cites Deuteronomy 32:8-9 (LXX text): 'When the Most High divided the nations, when he dispersed the sons of Adam, he set the boundaries of nations according to the number of the angels of God; and the Lord's portion became his people Jacob.' This becomes the scriptural anchor for Origen's theology of nations: each people is set under angelic guardianship by divine providence, NOT by autonomous cosmic powers as Celsus claims."},
    8: {"label": "The mystery of dispersion — explicit warning against vulgar reading",
        "summary": "Philocalia 22.8. Origen warns that the doctrine of soul-dispersion is 'mystical, and to it applies the saying It is well to keep the secret of a king (Tobit 12:7)' — a typically Origenian gesture protecting esoteric teaching. Critically: he denies metempsychōsis (souls do NOT enter bodies via transmigration), distancing his theology from the metempsychotic reading later interpreters would impose."},
    9: {"label": "The original unity: a single divine language oriented toward light",
        "summary": "Philocalia 22.9. The mystical reading of pre-Babel humanity: imagine all on earth using 'one divine tongue,' agreeing with each other, remaining unmoved from 'the East' (anatolē, with full cosmic-symbolic weight — toward Christ, the dawn). This is the soul's natural orientation; the dispersion happens when souls 'move from the East' (depart from their original contemplative orientation)."},
    10: {"label": "Allegorical reading of Babel: only the East-oriented are 'the Lord's portion'",
         "summary": "Philocalia 22.10. The allegorical historical reading: those who 'preserved the original language by not moving from the East' became 'the Lord's portion' (Deut 32:9). The Babel narrative, on this reading, depicts a moral-cosmic descent: only the souls that maintained their orientation toward the divine source remain in the Lord's direct allotment; the rest fall under angelic-overseer mediation."},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def extract_chapter(path: Path, start: int, end: int) -> str:
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[start - 1:end - 1])


def split_sections(text: str) -> dict[int, str]:
    """Split Robinson chapter 22 into 10 sections by " N. <Greek-cap or quote-then-Greek-cap>"."""
    markers: list[tuple[int, int]] = []
    for n in range(1, 11):
        pat = re.compile(rf"\b{n}\.\s+(?:[‘'\"\(]\s*)?([Α-ΩἈ-Ὦ])")
        m = pat.search(text)
        if not m:
            print(f"  [!] section {n} marker not found")
            continue
        markers.append((n, m.start()))
    section_texts: dict[int, str] = {}
    for i, (sec, pos) in enumerate(markers):
        end_pos = markers[i + 1][1] if i + 1 < len(markers) else len(text)
        section_texts[sec] = text[pos:end_pos].strip()
    return section_texts


# Same cleanup heuristic as Phase 1 (chap 21)
APPARATUS_RUN = re.compile(
    r"(?:"
    r"\s\d+(?:,\s\d+)*\s+[Α-ωἀ-ᾼ]+\s+(?:AB|ABC|ABD|ABCD|BC|BD|cat|Ru\.|Hier\.|Koe\.)\b[^.]{0,80}\.?|"
    r"\b(?:deest folium|rursus incipit|restitui|post|ante|om\.|hic desinit|cat|plura habent|cf\.|U\+[0-9A-Fa-f]+)\b[^.]{0,120}\.?"
    r")"
)


def clean_greek(raw: str) -> tuple[str, list[str]]:
    text = raw
    text = re.sub(r"^\s*\d+\.\s+", "", text)
    fragments: list[str] = []
    def _cap(m: re.Match) -> str:
        fragments.append(m.group(0).strip())
        return " "
    text = APPARATUS_RUN.sub(_cap, text)
    text = re.sub(r"\b(?:AB|ABC|ABD|ABCD|BC|BD|cat|Ru\.|Hier\.|Koe\.|Coisl\.)\b", " ", text)
    text = re.sub(r"U\+[0-9A-Fa-f]+", " ", text)
    text = re.sub(r"\b\d?\s?(?:Ro|Cor|Tim|Ge|Ex|Mt|Lk|Jn|Ru|cf|cat|Heb|Phil|Eph|Gal|Col|Th|Pe|Ja|Re|Acts|Tob|Wisd|Deut|Ps|Mc|C\.\s*Cels\.)\s+[ivxlcdmIVXLCDM]+(?:\s+\d+(?:,\s?\d+)?)?", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, fragments


def make_passage(par: int, greek_clean: str, greek_raw: str, apparatus: list[str]) -> dict[str, Any]:
    info = EN_SUMMARIES.get(par, {})
    label = info.get("label", f"Philocalia 22.{par}")
    summary = info.get("summary", f"Origen, Philocalia 22.{par}.")
    nid = f"passage_origen_philocalia_22_{par}"
    md = {
        "cts_urn": f"urn:cts:greekLit:tlg2042.tlg028:22.{par}",
        "source_quality": "critical_edition_robinson_1893_via_sematika",
        "primary_source_used": ROBINSON_EDITION,
        "principal_edition_modern": JUNOD_EDITION,
        "philocalia_chapter": 22,
        "philocalia_paragraph": par,
        "underlying_origen_source": "Contra Celsum, Book V (chapters ~25-32, on Celsus's argument that nations must follow ancestral law)",
        "critical_apparatus_robinson": apparatus,
        "ingested_from": {"sematika_file": str(SEMATIKA_PHILOC), "verified": True, "verification_memory": "reference_sematika_philocalia_verified.md"},
    }
    return {
        "id": nid,
        "type": "passage",
        "label": f"Origen, Philocalia 22.{par}: {label}",
        "description_grc": greek_clean,
        "description_grc_robinson_with_apparatus": greek_raw,
        "description_en": summary,
        "period": "Patristic",
        "confidence": 0.95,
        "metadata": json.dumps(md, ensure_ascii=False),
    }


def make_part_of_edge(passage_id: str, par: int) -> dict[str, Any]:
    return {
        "source": passage_id,
        "target": "work_origen_philocalia",
        "relation": "part_of",
        "confidence": 0.95,
        "metadata": {
            "anchor_kind": "philocalia_chapter_paragraph",
            "philocalia_chapter": 22,
            "philocalia_paragraph": par,
            "edition": "Robinson 1893 / Junod 1976 SC 226",
        },
    }


def edge_exists(edges: list[dict[str, Any]], src: str, tgt: str, rel: str) -> bool:
    return any(e.get("source") == src and e.get("target") == tgt and e.get("relation") == rel for e in edges)


def main() -> int:
    print(f"Reading Sematika Philocalia chapter 22 (lines {CHAPTER_22_START_LINE}-{CHAPTER_22_END_LINE - 1}) …")
    chapter_text = extract_chapter(SEMATIKA_PHILOC, CHAPTER_22_START_LINE, CHAPTER_22_END_LINE)
    print(f"  raw chapter length: {len(chapter_text)} chars")

    sections = split_sections(chapter_text)
    print(f"  detected sections: {sorted(sections.keys())}")

    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    by_id = {n["id"]: n for n in nodes}
    print(f"Loaded {len(nodes):,} nodes, {len(edges):,} edges")

    added_nodes = 0
    added_edges = 0
    skipped_existing = 0
    for par in sorted(sections.keys()):
        nid = f"passage_origen_philocalia_22_{par}"
        if nid in by_id:
            skipped_existing += 1
            print(f"  [skip-exists] {nid}")
            continue
        raw = sections[par]
        clean, app = clean_greek(raw)
        passage = make_passage(par, clean, raw, app)
        nodes.append(passage)
        by_id[nid] = passage
        added_nodes += 1
        # Edge
        edge = make_part_of_edge(nid, par)
        if not edge_exists(edges, edge["source"], edge["target"], edge["relation"]):
            edges.append(edge)
            added_edges += 1
        print(f"  [new] {nid}  (grc_clean={len(clean)} app_fragments={len(app)} raw={len(raw)} chars)")

    print(f"\nAdded: {added_nodes} passages, {added_edges} part_of edges  |  skipped (existing): {skipped_existing}")
    print(f"Final: {len(nodes):,} nodes, {len(edges):,} edges")
    dump_jsonl(NODES_PATH, nodes)
    dump_jsonl(EDGES_PATH, edges)
    print(f"Wrote {NODES_PATH} and {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
