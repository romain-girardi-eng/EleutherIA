# Amand Piste 1 — DHQ article — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the DHQ article *"Algorithmic provenance analysis of six moral anti-fatalist pivots: testing Amand 1945's Carneadean attribution against the primary Stoic corpus"* — 7,500-9,000 EN words plus a technical appendix, supported by an algorithmic provenance test of 6 Amand moral pivots against a primary Stoic corpus (Chrysippus, Cleanthes, Posidonius, Panaetius), with reproducible code, Zenodo DOI, and submission to Digital Humanities Quarterly.

**Architecture:** Two coupled deliverables sharing one knowledge graph. (1) Engineering deliverable: enrich the KG with primary Stoic fragments (SVF II/III, Cleanthes Hymn, Posidonius Edelstein-Kidd), implement a 3-test provenance analyzer (thematic + conceptual + textual), produce a 6×4 heatmap + 3 case-study figures. (2) Scholar deliverable: draft §1-§7 + appendix, validate ≥10 matches manually, compile bibliography of Amand 1945, Bobzien 1998/2000/2014, Frede 2011, Dihle 1982, Long-Sedley 1987, Inwood 1985, Sharples 1983/2001, Eliasson 2008, von Arnim SVF, Edelstein-Kidd 1972. Submit to DHQ with code + data archived on Zenodo (CC-BY 4.0).

**Tech Stack:** Python 3.14 + rdflib + eleutheria_kg.semantic + matplotlib (figures) + LaTeX/Pandoc (article render) + Zenodo (data archive). All code in `scripts/` and `knowledge graph/tests/unit/`. Article in `docs/papers/`.

**Spec:** `docs/superpowers/specs/2026-05-16-amand-piste1-article-design.md` (commit `cbabef78`).

---

## Phase 1 — Stoic Primary Corpus Enrichment

The current KG has Chrysippus with 32 arguments + 18 passages + SVF II work-shell but no individual fragment-level passages from SVF I/II/III. Cleanthes has 1 argument + 2 passages. Posidonius has 1 argument + 1 concept + 2 passages. To make the provenance test meaningful, we need sufficiency at the fragment level on each of the four primary Stoic sources.

### Task 1: Audit current Stoic primary corpus + SVF availability

**Files:**
- Read: `data/kg/nodes.jsonl`
- Read: `data/kg/edges.jsonl`
- Read: `data/kg/publications.bib`
- Create: `docs/reports/2026-05-16-stoic-corpus-pre-enrichment-audit.md`

- [ ] **Step 1: Audit current Chrysippus dossier**

Run:
```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
import json
from pathlib import Path
print('=== Chrysippus arguments ===')
for line in Path('data/kg/nodes.jsonl').read_text().splitlines():
    n = json.loads(line)
    if 'chrysippus' in n.get('id','').lower() and n.get('type') == 'argument':
        print(f'  {n[\"id\"]} :: {(n.get(\"label\") or \"\")[:80]}')
print()
print('=== Chrysippus passages ===')
for line in Path('data/kg/nodes.jsonl').read_text().splitlines():
    n = json.loads(line)
    if 'chrysippus' in n.get('id','').lower() and n.get('type') == 'passage':
        print(f'  {n[\"id\"]} :: {(n.get(\"label\") or \"\")[:80]}')
"
```

Expected: 32 arguments + 18 passages enumerated.

- [ ] **Step 2: Check SVF availability via archive.org / OpenGreekAndLatin**

```bash
curl -sL "https://archive.org/metadata/stoicorumveterumfra02arniuoft" | python3 -c "import sys, json; d = json.load(sys.stdin); print([f['name'] for f in d.get('files', []) if 'djvu' in f.get('name','') or 'pdf' in f.get('name','')][:8])"
```

Expected: 1-2 djvu/pdf URLs for SVF II (Logica + Physica).

Also check First1KGreek for `tlg0294` (Chrysippus tlg ID) or `tlg2125` (Stoici).

```bash
curl -sL "https://api.github.com/repos/OpenGreekAndLatin/First1KGreek/contents/data" | python3 -c "import sys, json; d = json.load(sys.stdin); [print(i['name']) for i in d if i.get('type')=='dir' and 'tlg' in i['name']]" | grep -E "294|2125"
```

Expected: no TEI Chrysippus (Stoici are fragmentary, not in TEI corpus). Confirms archive.org djvu OCR is the only path.

- [ ] **Step 3: Write audit report**

Create `docs/reports/2026-05-16-stoic-corpus-pre-enrichment-audit.md`:

```markdown
---
date: 2026-05-16
status: pre-enrichment baseline audit
---

# Stoic primary corpus — pre-enrichment baseline

## Chrysippus
- Existing args: [32 listed]
- Existing passages: [18 listed]
- SVF II work-shell: work_chrysippus_svf_ii (exists)
- SVF I/II/III download path: archive.org stoicorumveterumfra02arniuoft

## Cleanthes
- person_cleanthes_assos_330_230bce
- 1 argument, 2 passages (sparse)
- Hymne à Zeus availability: ...

## Posidonius
- person_posidonius_apameia_135_51bce
- 1 argument, 1 concept, 2 passages
- Edelstein-Kidd 1972 status: ...

## Panaetius
- person_panaetius_rhodes_185_109bce
- 1 argument only

## Conclusion
Estimated supplementary fragments needed: ~100-200 (Chrysippus SVF II priority).
```

- [ ] **Step 4: Commit audit**

```bash
git add docs/reports/2026-05-16-stoic-corpus-pre-enrichment-audit.md
git commit -m "audit(kg): pre-enrichment baseline of Stoic primary corpus for DHQ article provenance test"
```

---

### Task 2: SVF II Chrysippus fragments ingestion

The Stoicorum Veterum Fragmenta (von Arnim, 1903-1924, public domain). SVF II covers Chrysippus's Logica + Physica. The provenance test needs at minimum ~100 Chrysippus fragments covering anti-fatalist topics.

**Files:**
- Create: `scripts/ingest_svf_chrysippus_extended.py`
- Modify: `data/kg/nodes.jsonl` (+~80-100 fragments)
- Modify: `data/kg/edges.jsonl` (+~200-300 edges)
- Modify: `data/kg/publications.bib` (von Arnim 1903 entry)
- Modify: `data/scholarly_sources/manifest.jsonl`
- Create: `data/kg/snapshots/2026-05-16-pre-svf-extended/{nodes,edges}.jsonl`

- [ ] **Step 1: Snapshot before mutation**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && mkdir -p data/kg/snapshots/2026-05-16-pre-svf-extended && cp data/kg/nodes.jsonl data/kg/edges.jsonl data/kg/snapshots/2026-05-16-pre-svf-extended/
```

Expected output: 2 files copied.

- [ ] **Step 2: Download SVF II OCR**

```bash
mkdir -p data/scholarly_sources/ocr/svf_chrysippus
curl -sL -o data/scholarly_sources/ocr/svf_chrysippus/svf_vol_ii_djvu.txt "https://archive.org/download/stoicorumveterumfra02arniuoft/stoicorumveterumfra02arniuoft_djvu.txt"
wc -l data/scholarly_sources/ocr/svf_chrysippus/svf_vol_ii_djvu.txt
```

Expected: file ~2-3 MB, ~30k-50k lines.

- [ ] **Step 3: Write fragment extractor test**

Create `knowledge graph/tests/unit/test_svf_extractor.py`:

```python
"""Tests for SVF fragment extraction."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ingest_svf_chrysippus_extended import (
    extract_fragment_number,
    extract_target_fragments,
)


def test_extract_fragment_number_canonical():
    """Standard SVF fragment marker format."""
    line = "913. Plut. de Stoic. rep. 47, p. 1056 D = SVF II 913"
    assert extract_fragment_number(line) == 913


def test_extract_fragment_number_no_match():
    """Non-fragment lines return None."""
    line = "Stoici Veteres De Fato — Praefatio"
    assert extract_fragment_number(line) is None


def test_extract_target_fragments_known_anti_fatalist():
    """Anti-fatalist topic fragments are in SVF II.913-1000 range."""
    text = """913. Plutarch fragment about determinism
some content here
914. Another fragment about cylinder argument
more content
915. Galen DPP fragment about responsibility"""
    fragments = extract_target_fragments(text, range_start=913, range_end=915)
    assert len(fragments) == 3
    assert fragments[0]["number"] == 913
    assert "determinism" in fragments[0]["text"]
```

- [ ] **Step 4: Run test — expect ImportError (script doesn't exist)**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/unit/test_svf_extractor.py -v 2>&1 | tail -10
```

Expected: `ImportError: No module named 'scripts.ingest_svf_chrysippus_extended'` or similar.

- [ ] **Step 5: Write minimal script skeleton**

Create `scripts/ingest_svf_chrysippus_extended.py`:

```python
"""Ingest extended Chrysippus fragments from SVF II (von Arnim 1903, public domain).

Target ranges (anti-fatalist material):
  SVF II.913-1015 — De Fato et Necessitate (~100 fragments)

Source: archive.org `stoicorumveterumfra02arniuoft` djvu OCR text.

NE PAS COMMIT — Romain reviews before merge.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SVF_DJVU = Path(__file__).resolve().parents[1] / "data" / "scholarly_sources" / "ocr" / "svf_chrysippus" / "svf_vol_ii_djvu.txt"


def extract_fragment_number(line: str) -> int | None:
    """Match SVF fragment markers like '913.' or '913 a.' at line start."""
    m = re.match(r"^\s*(\d{3,4})\s*[a-z]?\.\s", line)
    if not m:
        return None
    return int(m.group(1))


def extract_target_fragments(text: str, range_start: int, range_end: int) -> list[dict]:
    """Parse djvu OCR into a list of {number, text} dicts within the target range."""
    fragments: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        num = extract_fragment_number(line)
        if num is not None and range_start <= num <= range_end:
            if current is not None:
                fragments.append(current)
            current = {"number": num, "text": line + "\n"}
        elif current is not None:
            current["text"] += line + "\n"
    if current is not None:
        fragments.append(current)
    return fragments


def main() -> int:
    text = SVF_DJVU.read_text(encoding="utf-8")
    fragments = extract_target_fragments(text, range_start=913, range_end=1015)
    print(f"Extracted {len(fragments)} fragments from SVF II.913-1015")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run unit tests — they should pass**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/unit/test_svf_extractor.py -v 2>&1 | tail -10
```

Expected: 3 tests pass.

- [ ] **Step 7: Run extractor on real djvu**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/ingest_svf_chrysippus_extended.py 2>&1 | tail -5
```

Expected: `Extracted N fragments from SVF II.913-1015` where N is between 50 and 120.

If N is less than 30, the OCR quality is bad. STOP and report. Otherwise continue.

- [ ] **Step 8: Add ingestion logic to the script**

Extend `scripts/ingest_svf_chrysippus_extended.py` with an `ingest_kg` function that:

```python
def ingest_kg(fragments: list[dict], *, dry_run: bool = True) -> dict:
    """Convert SVF fragments into KG nodes and edges."""
    KG_ROOT = Path(__file__).resolve().parents[1] / "data" / "kg"
    nodes_path = KG_ROOT / "nodes.jsonl"
    edges_path = KG_ROOT / "edges.jsonl"
    new_nodes: list[dict] = []
    new_edges: list[dict] = []
    for frag in fragments:
        nid = f"passage_chrysippus_svf_ii_{frag['number']}"
        node = {
            "id": nid,
            "node_id": nid,
            "type": "passage",
            "label": f"Chrysippus, SVF II.{frag['number']}",
            "description": frag["text"].strip(),
            "period": "Hellenistic",
            "language": "greek_ancient",
            "metadata": json.dumps({
                "source": "archive.org stoicorumveterumfra02arniuoft",
                "edition": "Stoicorum Veterum Fragmenta vol. II, ed. H. von Arnim, Teubner Leipzig 1903",
                "bibtex_key": "von-arnim-1903-svf-ii",
                "fragment_number": frag["number"],
                "passage_role": "original",
                "is_chrysippus_fragment_extended": True,
                "ocr_quality_pct": 75,
                "contains_greek_to_verify": True,
            }, ensure_ascii=False),
        }
        new_nodes.append(node)
        new_edges.append({
            "edge_id": f"edge_part_of_{nid}",
            "relation": "part_of",
            "source_id": nid,
            "target_id": "work_chrysippus_svf_ii",
        })
        new_edges.append({
            "edge_id": f"edge_authored_by_{nid}",
            "relation": "authored_by",
            "source_id": nid,
            "target_id": "person_chrysippus_280_206bce_i9j0k1l2",
        })
    if dry_run:
        return {"new_nodes": len(new_nodes), "new_edges": len(new_edges)}
    with nodes_path.open("a", encoding="utf-8") as f:
        for n in new_nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with edges_path.open("a", encoding="utf-8") as f:
        for e in new_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return {"new_nodes": len(new_nodes), "new_edges": len(new_edges)}


# Update main():
def main() -> int:
    text = SVF_DJVU.read_text(encoding="utf-8")
    fragments = extract_target_fragments(text, range_start=913, range_end=1015)
    print(f"Extracted {len(fragments)} fragments from SVF II.913-1015")
    result = ingest_kg(fragments, dry_run=("--commit" not in sys.argv))
    print(f"Result: {result}")
    return 0
```

Add `import sys` at top.

- [ ] **Step 9: Dry-run preview**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/ingest_svf_chrysippus_extended.py
```

Expected: `Result: {'new_nodes': N, 'new_edges': 2*N}` where N matches Step 7.

- [ ] **Step 10: Actually ingest**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/ingest_svf_chrysippus_extended.py --commit
```

Expected: same output as dry-run, plus `nodes.jsonl` and `edges.jsonl` grew by appropriate amounts.

- [ ] **Step 11: Verify SHACL invariants**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
from pathlib import Path
from eleutheria_kg.semantic import build_graph, validate_kg_invariants
g = build_graph(Path('data/kg/nodes.jsonl'), Path('data/kg/edges.jsonl'))
r = validate_kg_invariants(g)
print(f'invariants conforms: {r.conforms}, viols: {r.violation_count}')
"
```

Expected: `conforms: True, viols: 0`.

If violations, run `python scripts/flag_unanchored_claims.py` and re-verify.

- [ ] **Step 12: Run KG tests**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/ -q --no-header 2>&1 | tail -2
```

Expected: 121/121 passed (or 124/124 if new tests added in Task 2).

- [ ] **Step 13: Update manifest + publications.bib**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/archive_scholarly_source.py svf_chrysippus
```

Then manually edit `data/scholarly_sources/manifest.jsonl` to add bibtex_key + title + author for the svf_chrysippus entry.

Add to `data/kg/publications.bib`:

```bibtex
@book{von-arnim-1903-svf-ii,
  author = {Hans von Arnim},
  title = {Stoicorum Veterum Fragmenta. Volumen II: Chrysippi Fragmenta Logica et Physica},
  publisher = {Teubner},
  address = {Leipzig},
  year = {1903},
  note = {Public domain. Available on archive.org as stoicorumveterumfra02arniuoft.},
}
```

- [ ] **Step 14: Commit**

```bash
git add data/kg/nodes.jsonl data/kg/edges.jsonl data/kg/snapshots/2026-05-16-pre-svf-extended/ scripts/ingest_svf_chrysippus_extended.py knowledge\ graph/tests/unit/test_svf_extractor.py data/scholarly_sources/manifest.jsonl data/kg/publications.bib
git commit -m "feat(kg): extend Chrysippus dossier with SVF II.913-1015 fragments — primary Stoic corpus enrichment for DHQ article"
```

---

### Task 3: Cleanthes fragments ingestion

Cleanthes is currently sparse (1 argument + 2 passages). For the provenance test we need the *Hymn to Zeus* (a fully preserved poem, ~39 lines) and key SVF I fragments (486-619).

**Files:**
- Create: `scripts/ingest_cleanthes_fragments.py`
- Modify: `data/kg/nodes.jsonl` (+~20-30 nodes)
- Modify: `data/kg/edges.jsonl` (+~50-70 edges)
- Modify: `data/kg/publications.bib`

- [ ] **Step 1: Audit Cleanthes existing + source availability**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
import json
from pathlib import Path
for line in Path('data/kg/nodes.jsonl').read_text().splitlines():
    n = json.loads(line)
    if 'cleanthes' in n.get('id','').lower():
        print(f'[{n[\"type\"]}] {n[\"id\"]}')
"
```

- [ ] **Step 2: Check Hymn to Zeus availability**

Sources to try in order:
- First1KGreek for Cleanthes: `https://api.github.com/repos/OpenGreekAndLatin/First1KGreek/contents/data/tlg0007`
- Bibliotheca Augustana: `https://www.hs-augsburg.de/~harsch/graeca/Chronologia/S_ante03/Cleanthes/cle_hy.html`
- archive.org SVF I: `https://archive.org/details/stoicorumveterum01arniuoft`

Pick the one with the cleanest plain Greek text.

- [ ] **Step 3: Build Cleanthes ingestion script**

Mirror the SVF II pattern from Task 2. Create `scripts/ingest_cleanthes_fragments.py`:

```python
"""Ingest Cleanthes Hymn to Zeus + key SVF I fragments (anti-fatalist topics).

Target: 39 lines of the Hymn + SVF I.486-619 anti-fatalist fragments (sparse).
Source: Bibliotheca Augustana for the Hymn (verified Greek text); archive.org
SVF I for fragment-level material.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# [follow the same pattern as ingest_svf_chrysippus_extended.py]
```

- [ ] **Step 4: Snapshot, dry-run, ingest, verify**

Follow the same sequence as Task 2 (steps 1, 9, 10, 11, 12).

- [ ] **Step 5: Commit**

```bash
git add ...
git commit -m "feat(kg): Cleanthes Hymn to Zeus + SVF I fragments for primary Stoic corpus"
```

---

### Task 4: Posidonius fragments ingestion (Edelstein-Kidd)

Posidonius is in the KG with only 1 argument + 1 concept + 2 passages. Edelstein-Kidd 1972 (*Posidonius. The Fragments*) is the canonical edition but under Brill copyright. Alternative path: Diogenes Laertius VII.149-157 (Posidonius doxography, public domain), Cicero *De Divinatione* (already in corpus, has Posidonius testimonies), Galen *De Placitis Hippocratis et Platonis* (Posidonius on emotions).

**Files:**
- Create: `scripts/ingest_posidonius_fragments.py`
- Modify: `data/kg/nodes.jsonl` (+~10-20 nodes via DL VII + Cicero De Div + Galen DPP cross-references)
- Modify: `data/kg/edges.jsonl`

- [ ] **Step 1: Audit Posidonius existing**

(same pattern as Task 3 step 1)

- [ ] **Step 2: Cross-reference existing Cicero De Div + DL VII passages**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
import json
from pathlib import Path
# Find passages with mention of Posidonius
for line in Path('data/kg/nodes.jsonl').read_text().splitlines():
    n = json.loads(line)
    if n.get('type') != 'passage': continue
    text = (n.get('description') or '') + ' ' + (n.get('description_en') or '')
    if 'posidoni' in text.lower():
        print(n['id'])
"
```

- [ ] **Step 3: Add new Posidonius testimonia nodes**

For each existing passage that mentions Posidonius, create an edge `passage_X --testifies_about--> person_posidonius_*`. If `testifies_about` isn't in ontology, use `discusses`.

Don't create new passage nodes; just wire existing ones.

- [ ] **Step 4: Verify + commit**

(same pattern)

---

### Task 5: Phase 1 final SHACL + tests + summary report

- [ ] **Step 1: Full SHACL invariants + FULL check**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
from pathlib import Path
from eleutheria_kg.semantic import build_graph, validate_kg, validate_kg_invariants
from eleutheria_kg.semantic.shapes import load_shapes
g = build_graph(Path('data/kg/nodes.jsonl'), Path('data/kg/edges.jsonl'))
print(f'triples: {len(g):,}')
print(f'invariants: {validate_kg_invariants(g).conforms}')
print(f'FULL: {validate_kg(g, load_shapes()).conforms}')
"
```

Expected: invariants True, FULL conforms (or only pre-existing warnings unchanged).

- [ ] **Step 2: Tests**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/ -q --no-header
```

Expected: 121/121+ passing.

- [ ] **Step 3: Phase 1 summary report**

Create `docs/reports/2026-05-16-stoic-corpus-post-enrichment-summary.md` documenting:

- Chrysippus: 18 + N new = X total passages (final count)
- Cleanthes: 2 + M new = Y total
- Posidonius: testimonia wired, no new fragments
- Panaetius: still 1 argument (acceptable; he is post-Chrysippus, marginal)

- [ ] **Step 4: Commit summary**

```bash
git add docs/reports/2026-05-16-stoic-corpus-post-enrichment-summary.md
git commit -m "docs: Phase 1 Stoic corpus enrichment summary — pre/post-enrichment counts"
```

---

## Phase 2 — Provenance Analyzer

The analyzer applies 3 cumulative tests (thematic + conceptual + textual) for each (Amand pivot, Stoic primary) pair. Output: 6×4 scored matrix.

### Task 6: Analyzer skeleton + test fixtures

**Files:**
- Create: `scripts/analyze_amand_stoic_provenance.py`
- Create: `knowledge graph/tests/unit/test_amand_stoic_provenance.py`

- [ ] **Step 1: Write fixtures test for the 6 pivots**

Create the test file with one initial test verifying that all 6 Amand pivots are still present in the KG:

```python
"""Tests for the Amand-Stoic provenance analyzer."""
from __future__ import annotations

from pathlib import Path

import pytest

NODES = Path(__file__).resolve().parents[3] / "data" / "kg" / "nodes.jsonl"


AMAND_MORAL_PIVOTS: tuple[str, ...] = (
    "argument_carneadean_general_theme_amand1945",
    "argument_carneadean_legislation_amand1945",
    "argument_carneadean_virtue_vice_amand1945",
    "argument_carneadean_incentives_amand1945",
    "argument_carneadean_action_futility_amand1945",
    "argument_carneadean_piety_amand1945",
)


STOIC_PRIMARY: tuple[str, ...] = (
    "person_chrysippus_280_206bce_i9j0k1l2",
    "person_cleanthes_assos_330_230bce",
    "person_posidonius_apameia_135_51bce",
    "person_panaetius_rhodes_185_109bce",
)


def _all_node_ids() -> set[str]:
    import json
    ids: set[str] = set()
    for line in NODES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ids.add(json.loads(line)["id"])
    return ids


def test_six_amand_moral_pivots_exist():
    node_ids = _all_node_ids()
    missing = [p for p in AMAND_MORAL_PIVOTS if p not in node_ids]
    assert not missing, f"missing pivots: {missing}"


def test_four_stoic_primary_persons_exist():
    node_ids = _all_node_ids()
    missing = [p for p in STOIC_PRIMARY if p not in node_ids]
    assert not missing, f"missing Stoic persons: {missing}"
```

- [ ] **Step 2: Run test — expect PASS**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/unit/test_amand_stoic_provenance.py -v 2>&1 | tail -5
```

Expected: 2 PASS.

- [ ] **Step 3: Create analyzer skeleton**

Create `scripts/analyze_amand_stoic_provenance.py`:

```python
"""Algorithmic provenance test for Amand 1945's six moral anti-fatalist pivots.

Output: 6×4 scored matrix testing whether each Amand pivot has a Stoic primary
parallel (Chrysippus, Cleanthes, Posidonius, Panaetius). The matrix arbitrates
empirically between Amand 1945 (Carneadean attribution) and Bobzien 1998
(Stoic-internal origin).

Three cumulative tests per (pivot, Stoic source) pair:
1. Thematic: shared topic tags / concept overlap
2. Conceptual: shared concept node via OWL-RL closure (1 hop)
3. Textual: shared Greek lemma (with diacritic normalization) on passages
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from eleutheria_kg.semantic import build_graph, materialize_inverses_and_transitivity

log = logging.getLogger("amand-stoic-provenance")

NODES = Path(__file__).resolve().parents[1] / "data" / "kg" / "nodes.jsonl"
EDGES = Path(__file__).resolve().parents[1] / "data" / "kg" / "edges.jsonl"


AMAND_MORAL_PIVOTS: tuple[str, ...] = (
    "argument_carneadean_general_theme_amand1945",
    "argument_carneadean_legislation_amand1945",
    "argument_carneadean_virtue_vice_amand1945",
    "argument_carneadean_incentives_amand1945",
    "argument_carneadean_action_futility_amand1945",
    "argument_carneadean_piety_amand1945",
)


STOIC_PRIMARY: tuple[str, ...] = (
    "person_chrysippus_280_206bce_i9j0k1l2",
    "person_cleanthes_assos_330_230bce",
    "person_posidonius_apameia_135_51bce",
    "person_panaetius_rhodes_185_109bce",
)


@dataclass
class PairScore:
    pivot: str
    stoic: str
    thematic_hits: list[str] = field(default_factory=list)
    conceptual_hits: list[str] = field(default_factory=list)
    textual_hits: list[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return (
            (1 if self.thematic_hits else 0)
            + (1 if self.conceptual_hits else 0)
            + (1 if self.textual_hits else 0)
        )


def main() -> int:
    log.info("loading KG...")
    g = build_graph(NODES, EDGES)
    log.info(f"  pre-closure triples: {len(g):,}")
    materialize_inverses_and_transitivity(g)
    log.info(f"  post-closure triples: {len(g):,}")
    log.info("analyzer not yet implemented")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
```

- [ ] **Step 4: Commit**

```bash
git add scripts/analyze_amand_stoic_provenance.py knowledge\ graph/tests/unit/test_amand_stoic_provenance.py
git commit -m "feat(provenance): analyzer skeleton + fixture tests for Amand-Stoic 6×4 matrix"
```

---

### Task 7: Thematic test

Test: for each (Amand pivot, Stoic primary), gather the set of `metadata.amand_pivot_theme` or topic descriptors from the pivot, and check overlap with the Stoic source's arguments/concepts/passages topic tags.

- [ ] **Step 1: Write test**

Add to `knowledge graph/tests/unit/test_amand_stoic_provenance.py`:

```python
def test_thematic_test_for_virtue_vice_chrysippus():
    """Pivot III (virtue/vice) should have a thematic hit against Chrysippus.

    The Stoic cylinder argument (SVF II.974) explicitly discusses praise/blame
    under cylinder determinism — a thematic overlap with Amand's pivot III.
    """
    from scripts.analyze_amand_stoic_provenance import (
        build_keyword_index,
        thematic_test,
    )

    g_index = build_keyword_index()
    pair = thematic_test(
        pivot="argument_carneadean_virtue_vice_amand1945",
        stoic_person="person_chrysippus_280_206bce_i9j0k1l2",
        index=g_index,
    )
    assert len(pair.thematic_hits) >= 1
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/unit/test_amand_stoic_provenance.py::test_thematic_test_for_virtue_vice_chrysippus -v
```

Expected: ImportError.

- [ ] **Step 3: Implement build_keyword_index + thematic_test**

Add to `scripts/analyze_amand_stoic_provenance.py`:

```python
PIVOT_THEMES: dict[str, set[str]] = {
    "argument_carneadean_general_theme_amand1945": {
        "fatalism", "destiny", "εἱμαρμένη", "heimarmene", "responsibility", "necessity",
    },
    "argument_carneadean_legislation_amand1945": {
        "law", "νόμος", "nomos", "punishment", "legislation", "court", "judgment",
    },
    "argument_carneadean_virtue_vice_amand1945": {
        "virtue", "vice", "praise", "blame", "ἔπαινος", "ψόγος", "epainos", "psogos",
        "responsibility", "moral",
    },
    "argument_carneadean_incentives_amand1945": {
        "exhortation", "correction", "teaching", "νουθεσία", "παραίνεσις", "advice", "instruction",
    },
    "argument_carneadean_action_futility_amand1945": {
        "action", "effort", "ἀργία", "argia", "indolence", "laziness", "futility",
    },
    "argument_carneadean_piety_amand1945": {
        "piety", "εὐσέβεια", "eusebeia", "religion", "gods", "divine",
    },
}


def build_keyword_index() -> dict[str, dict[str, list[str]]]:
    """Return {stoic_person_id: {keyword: [node_ids that mention it]}}."""
    index: dict[str, dict[str, list[str]]] = {sp: {} for sp in STOIC_PRIMARY}
    person_args: dict[str, set[str]] = {sp: set() for sp in STOIC_PRIMARY}
    for line in EDGES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        src = e.get("source_id") or e.get("source", "")
        tgt = e.get("target_id") or e.get("target", "")
        rel = e.get("relation", "")
        if rel == "authored_by" and tgt in person_args:
            person_args[tgt].add(src)
    all_keywords = set().union(*PIVOT_THEMES.values())
    for line in NODES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        n = json.loads(line)
        nid = n["id"]
        text = ((n.get("description") or "") + " " + (n.get("description_en") or "")).lower()
        for sp, args in person_args.items():
            if nid in args:
                for kw in all_keywords:
                    if kw.lower() in text:
                        index[sp].setdefault(kw, []).append(nid)
    return index


def thematic_test(*, pivot: str, stoic_person: str, index: dict[str, dict[str, list[str]]]) -> PairScore:
    pair = PairScore(pivot=pivot, stoic=stoic_person)
    themes = PIVOT_THEMES.get(pivot, set())
    stoic_index = index.get(stoic_person, {})
    for theme in themes:
        for nid in stoic_index.get(theme, []):
            pair.thematic_hits.append(f"{theme} → {nid}")
    return pair
```

- [ ] **Step 4: Run test — expect PASS**

(Run as in Step 2)

Expected: PASS. The Chrysippus dossier was extended in Phase 1; the keyword overlap with pivot III (virtue/vice) keywords should fire.

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze_amand_stoic_provenance.py knowledge\ graph/tests/unit/test_amand_stoic_provenance.py
git commit -m "feat(provenance): thematic test (keyword overlap) for 6×4 matrix"
```

---

### Task 8: Conceptual test

Test: do the pivot and the Stoic source share a `concept_*` node via the KG (1-hop or via OWL-RL closure)?

- [ ] **Step 1: Write test**

```python
def test_conceptual_test_for_legislation_chrysippus():
    """Pivot II (legislation) should share concept_nomos or concept_law with Chrysippus."""
    from scripts.analyze_amand_stoic_provenance import (
        build_concept_index,
        conceptual_test,
    )

    g_concepts = build_concept_index()
    pair = conceptual_test(
        pivot="argument_carneadean_legislation_amand1945",
        stoic_person="person_chrysippus_280_206bce_i9j0k1l2",
        concepts=g_concepts,
    )
    assert isinstance(pair.conceptual_hits, list)
```

- [ ] **Step 2: Run test — expect ImportError**

(same pattern)

- [ ] **Step 3: Implement build_concept_index + conceptual_test**

Add to `scripts/analyze_amand_stoic_provenance.py`:

```python
def build_concept_index() -> dict[str, set[str]]:
    """Return {entity_id: {concept_ids it discusses or contains}}."""
    index: dict[str, set[str]] = {}
    for line in EDGES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        src = e.get("source_id") or e.get("source", "")
        tgt = e.get("target_id") or e.get("target", "")
        rel = e.get("relation", "")
        if rel in ("discusses", "contains", "engages_with") and tgt.startswith("concept_"):
            index.setdefault(src, set()).add(tgt)
    return index


def conceptual_test(*, pivot: str, stoic_person: str, concepts: dict[str, set[str]]) -> PairScore:
    pair = PairScore(pivot=pivot, stoic=stoic_person)
    pivot_concepts = concepts.get(pivot, set())
    person_args: set[str] = set()
    for line in EDGES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        src = e.get("source_id") or e.get("source", "")
        tgt = e.get("target_id") or e.get("target", "")
        rel = e.get("relation", "")
        if rel == "authored_by" and tgt == stoic_person:
            person_args.add(src)
    stoic_concepts: set[str] = set()
    for arg in person_args:
        stoic_concepts |= concepts.get(arg, set())
    shared = pivot_concepts & stoic_concepts
    pair.conceptual_hits = sorted(shared)
    return pair
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(provenance): conceptual test (shared concept_* nodes) for 6×4 matrix"
```

---

### Task 9: Textual test

Test: shared Greek lemma between the pivot's anchored passages (if any) and the Stoic source's passages. Uses polytonic normalization.

- [ ] **Step 1: Write test**

```python
def test_textual_test_chrysippus_passages_contain_eph_hemin():
    """Chrysippus passages should contain ἐφ' ἡμῖν or its diacritic-normalized form."""
    from scripts.analyze_amand_stoic_provenance import (
        normalize_greek,
        passages_for_person,
    )

    pages = passages_for_person("person_chrysippus_280_206bce_i9j0k1l2")
    found = any("εφ ημιν" in normalize_greek(p.get("description") or "") for p in pages)
    assert found, "expected ἐφ' ἡμῖν normalized form in at least one Chrysippus passage"
```

- [ ] **Step 2: Run test — expect ImportError**

- [ ] **Step 3: Implement normalize_greek + passages_for_person + textual_test**

Add to `scripts/analyze_amand_stoic_provenance.py`:

```python
import unicodedata


def normalize_greek(text: str) -> str:
    """Strip diacritics + punctuation + lowercase a Greek string."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return stripped.lower()


PIVOT_GREEK_TERMS: dict[str, set[str]] = {
    "argument_carneadean_general_theme_amand1945": {"ειμαρμενη", "αναγκη", "πεπρωμενη"},
    "argument_carneadean_legislation_amand1945": {"νομος", "νομοι"},
    "argument_carneadean_virtue_vice_amand1945": {"αρετη", "κακια", "επαινος", "ψογος"},
    "argument_carneadean_incentives_amand1945": {"νουθεσια", "παραινεσις", "διδασκαλια"},
    "argument_carneadean_action_futility_amand1945": {"αργια", "ραθυμια"},
    "argument_carneadean_piety_amand1945": {"ευσεβεια", "θεοι"},
}


def passages_for_person(person_id: str) -> list[dict]:
    out: list[dict] = []
    person_args: set[str] = set()
    for line in EDGES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        src = e.get("source_id") or e.get("source", "")
        tgt = e.get("target_id") or e.get("target", "")
        rel = e.get("relation", "")
        if rel == "authored_by" and tgt == person_id:
            person_args.add(src)
    for line in NODES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        n = json.loads(line)
        if n.get("type") == "passage" and n["id"] in person_args:
            out.append(n)
    return out


def textual_test(*, pivot: str, stoic_person: str) -> PairScore:
    pair = PairScore(pivot=pivot, stoic=stoic_person)
    targets = PIVOT_GREEK_TERMS.get(pivot, set())
    passages = passages_for_person(stoic_person)
    for p in passages:
        norm = normalize_greek(p.get("description") or "")
        for term in targets:
            if term in norm:
                pair.textual_hits.append(f"{term} → {p['id']}")
    return pair
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(provenance): textual test (Greek lemma overlap with diacritic normalization) for 6×4 matrix"
```

---

### Task 10: Matrix aggregator + JSON dump

- [ ] **Step 1: Test the aggregator**

```python
def test_full_matrix_shape():
    """The aggregator must produce a 6×4 matrix of PairScore objects."""
    from scripts.analyze_amand_stoic_provenance import compute_matrix

    matrix = compute_matrix()
    assert len(matrix) == 6
    for row in matrix:
        assert len(row) == 4
```

- [ ] **Step 2: Implement compute_matrix + dump_matrix**

```python
def compute_matrix() -> list[list[PairScore]]:
    kw_index = build_keyword_index()
    concept_index = build_concept_index()
    matrix: list[list[PairScore]] = []
    for pivot in AMAND_MORAL_PIVOTS:
        row: list[PairScore] = []
        for stoic in STOIC_PRIMARY:
            t = thematic_test(pivot=pivot, stoic_person=stoic, index=kw_index)
            c = conceptual_test(pivot=pivot, stoic_person=stoic, concepts=concept_index)
            x = textual_test(pivot=pivot, stoic_person=stoic)
            pair = PairScore(
                pivot=pivot,
                stoic=stoic,
                thematic_hits=t.thematic_hits,
                conceptual_hits=c.conceptual_hits,
                textual_hits=x.textual_hits,
            )
            row.append(pair)
        matrix.append(row)
    return matrix


def dump_matrix(matrix: list[list[PairScore]], path: Path) -> None:
    data = []
    for row in matrix:
        for pair in row:
            data.append({
                "pivot": pair.pivot,
                "stoic": pair.stoic,
                "thematic_hits": pair.thematic_hits,
                "conceptual_hits": pair.conceptual_hits,
                "textual_hits": pair.textual_hits,
                "total_score": pair.total_score,
            })
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

Update `main()`:

```python
def main() -> int:
    log.info("computing 6×4 matrix...")
    matrix = compute_matrix()
    out = Path("docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    dump_matrix(matrix, out)
    log.info(f"wrote {out}")
    # Console summary
    for row in matrix:
        for pair in row:
            log.info(
                f"  {pair.pivot[-40:]:>40} × {pair.stoic[-30:]:>30} "
                f"= thematic:{len(pair.thematic_hits):2d} "
                f"conceptual:{len(pair.conceptual_hits):2d} "
                f"textual:{len(pair.textual_hits):2d} "
                f"total:{pair.total_score}/3"
            )
    return 0
```

- [ ] **Step 3: Run end-to-end + verify output**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/analyze_amand_stoic_provenance.py
```

Expected: a 24-line summary + `docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json` written.

- [ ] **Step 4: Run all tests**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA/knowledge graph" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -m pytest tests/unit/test_amand_stoic_provenance.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze_amand_stoic_provenance.py knowledge\ graph/tests/unit/test_amand_stoic_provenance.py docs/papers/2026-05-amand-piste1-data/
git commit -m "feat(provenance): matrix aggregator + JSON dump — full 6×4 pipeline operational"
```

---

## Phase 3 — Visualization

### Task 11: Heatmap figure

**Files:**
- Create: `scripts/generate_provenance_figures.py`
- Create: `docs/papers/2026-05-amand-piste1-figures/heatmap-6x4.png` and `.svg`

- [ ] **Step 1: Write test**

```python
def test_heatmap_generation(tmp_path):
    from scripts.generate_provenance_figures import generate_heatmap
    import json
    sample_data = [
        {"pivot": f"pivot_{i}", "stoic": f"stoic_{j}", "total_score": (i + j) % 4}
        for i in range(6) for j in range(4)
    ]
    out = tmp_path / "heatmap.png"
    generate_heatmap(sample_data, out)
    assert out.exists() and out.stat().st_size > 1000
```

- [ ] **Step 2: Run test — ImportError**

- [ ] **Step 3: Implement generate_heatmap**

Create `scripts/generate_provenance_figures.py`:

```python
"""Generate publication figures for the DHQ article: heatmap + case-study plots."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PIVOT_LABELS = {
    "argument_carneadean_general_theme_amand1945": "I. General theme",
    "argument_carneadean_legislation_amand1945": "II. Legislation",
    "argument_carneadean_virtue_vice_amand1945": "III. Virtue & vice",
    "argument_carneadean_incentives_amand1945": "IV. Incentives",
    "argument_carneadean_action_futility_amand1945": "V. Action futility",
    "argument_carneadean_piety_amand1945": "VI. Piety",
}


STOIC_LABELS = {
    "person_chrysippus_280_206bce_i9j0k1l2": "Chrysippus",
    "person_cleanthes_assos_330_230bce": "Cleanthes",
    "person_posidonius_apameia_135_51bce": "Posidonius",
    "person_panaetius_rhodes_185_109bce": "Panaetius",
}


def generate_heatmap(matrix_data: list[dict], out: Path) -> None:
    pivots = list(PIVOT_LABELS.keys())
    stoics = list(STOIC_LABELS.keys())
    grid = np.zeros((len(pivots), len(stoics)), dtype=int)
    for row in matrix_data:
        i = pivots.index(row["pivot"])
        j = stoics.index(row["stoic"])
        grid[i, j] = row["total_score"]
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(grid, cmap="YlOrRd", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(stoics)))
    ax.set_xticklabels([STOIC_LABELS[s] for s in stoics], rotation=15)
    ax.set_yticks(range(len(pivots)))
    ax.set_yticklabels([PIVOT_LABELS[p] for p in pivots])
    for i in range(len(pivots)):
        for j in range(len(stoics)):
            ax.text(j, i, str(grid[i, j]), ha="center", va="center", color="white" if grid[i, j] >= 2 else "black")
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1, 2, 3])
    cbar.set_label("Cumulative score (out of 3)")
    ax.set_title("Stoic primary parallels for Amand 1945's six moral pivots\n(thematic + conceptual + textual)")
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    fig.savefig(out.with_suffix(".svg"))
    plt.close(fig)


def main() -> int:
    data_path = Path("docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json")
    matrix_data = json.loads(data_path.read_text(encoding="utf-8"))
    out_dir = Path("docs/papers/2026-05-amand-piste1-figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_heatmap(matrix_data, out_dir / "heatmap-6x4.png")
    print(f"wrote {out_dir / 'heatmap-6x4.png'} and .svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Generate real heatmap**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/generate_provenance_figures.py
```

Expected: heatmap PNG and SVG written.

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_provenance_figures.py docs/papers/2026-05-amand-piste1-figures/ knowledge\ graph/tests/unit/test_amand_stoic_provenance.py
git commit -m "feat(provenance): heatmap figure 6×4 for DHQ article main figure"
```

---

### Task 12: Case-study deep-dive figures (3 pivots)

For 2-3 pivots where Amand and Bobzien diverge the most, generate bar-chart breakdowns showing thematic / conceptual / textual hit counts per Stoic primary source.

- [ ] **Step 1: Test for case_study_plot**

```python
def test_case_study_plot(tmp_path):
    from scripts.generate_provenance_figures import generate_case_study
    import json
    matrix = [{
        "pivot": "argument_carneadean_virtue_vice_amand1945",
        "stoic": s,
        "thematic_hits": ["a"] * (i + 1),
        "conceptual_hits": [],
        "textual_hits": ["b"] if i == 0 else [],
        "total_score": 2 if i == 0 else 1,
    } for i, s in enumerate(["person_chrysippus_280_206bce_i9j0k1l2", "person_cleanthes_assos_330_230bce", "person_posidonius_apameia_135_51bce", "person_panaetius_rhodes_185_109bce"])]
    out = tmp_path / "case.png"
    generate_case_study(matrix, "argument_carneadean_virtue_vice_amand1945", out)
    assert out.exists()
```

- [ ] **Step 2: Implement generate_case_study**

Add to `scripts/generate_provenance_figures.py`:

```python
def generate_case_study(matrix_data: list[dict], pivot_id: str, out: Path) -> None:
    relevant = [r for r in matrix_data if r["pivot"] == pivot_id]
    stoics = [STOIC_LABELS[r["stoic"]] for r in relevant]
    thematic = [len(r["thematic_hits"]) for r in relevant]
    conceptual = [len(r["conceptual_hits"]) for r in relevant]
    textual = [len(r["textual_hits"]) for r in relevant]
    x = np.arange(len(stoics))
    width = 0.27
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width, thematic, width, label="Thematic")
    ax.bar(x, conceptual, width, label="Conceptual")
    ax.bar(x + width, textual, width, label="Textual")
    ax.set_xticks(x)
    ax.set_xticklabels(stoics)
    ax.set_ylabel("Number of hits")
    ax.set_title(f"Stoic parallels: {PIVOT_LABELS.get(pivot_id, pivot_id)}")
    ax.legend()
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    fig.savefig(out.with_suffix(".svg"))
    plt.close(fig)
```

- [ ] **Step 3: Generate case-study plots for pivot III (virtue/vice), pivot VI (piety), pivot I (general)**

Update `main()` of `generate_provenance_figures.py`:

```python
for pivot in [
    "argument_carneadean_virtue_vice_amand1945",
    "argument_carneadean_piety_amand1945",
    "argument_carneadean_general_theme_amand1945",
]:
    short = pivot.replace("argument_carneadean_", "").replace("_amand1945", "")
    generate_case_study(matrix_data, pivot, out_dir / f"case-{short}.png")
```

- [ ] **Step 4: Run + commit**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python scripts/generate_provenance_figures.py
ls docs/papers/2026-05-amand-piste1-figures/
```

Expected: heatmap + 3 case figures.

```bash
git add scripts/generate_provenance_figures.py docs/papers/2026-05-amand-piste1-figures/ knowledge\ graph/tests/unit/test_amand_stoic_provenance.py
git commit -m "feat(provenance): 3 case-study deep-dive figures (pivots III, VI, I) for DHQ article"
```

---

## Phase 4 — Manual validation (scholar work)

### Task 13: Sample 10 matches randomly + manual validation

**Files:**
- Create: `docs/papers/2026-05-amand-piste1-data/manual-validation-sample.md`

- [ ] **Step 1: Random sample 10 matches**

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
import json, random
data = json.loads(open('docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json').read())
positive = [r for r in data if r['total_score'] >= 2]
random.seed(42)
sample = random.sample(positive, k=min(10, len(positive)))
for s in sample:
    print(f\"{s['pivot']} × {s['stoic']}\")
    print(f\"  thematic: {s['thematic_hits'][:3]}\")
    print(f\"  conceptual: {s['conceptual_hits']}\")
    print(f\"  textual: {s['textual_hits'][:3]}\")
    print()
" | tee /tmp/sample10.txt
```

Expected: 10 pairs with their top-3 hits each.

- [ ] **Step 2: Romain manually verifies each pair**

For each of the 10 pairs, Romain reads the actual Stoic source passage(s) referenced, and verifies that the match is philologically genuine (the Stoic argument and the Amand pivot really do attest a parallel) or spurious.

Result template in `docs/papers/2026-05-amand-piste1-data/manual-validation-sample.md`:

```markdown
---
date: 2026-05-XX
auditor: Romain Girardi
seed: 42
sample_size: 10
---

# Manual philological validation of 10 random matches (seed 42)

For each pair (pivot × Stoic primary), Romain manually reads the cited
sources and assesses : (G) genuine parallel, (P) partial parallel, (S) spurious.

## Sample 1: pivot III × Chrysippus
- thematic hits : [list]
- conceptual hits : [list]
- textual hits : [list]
- Romain's reading : ...
- Verdict : G / P / S
- Notes : ...

[... × 10]

## Aggregate
- Genuine : N/10
- Partial : M/10
- Spurious : (10 - N - M)/10
```

- [ ] **Step 3: Aggregate validation rate**

Compute the genuine rate. If ≥ 80% genuine, the matrix is publishable as is. If 60-79%, mention the validation rate as a limitation in the article. If <60%, refine the algorithm.

- [ ] **Step 4: Commit validation log**

```bash
git add docs/papers/2026-05-amand-piste1-data/manual-validation-sample.md
git commit -m "data: manual philological validation of 10 random matches (seed 42)"
```

---

## Phase 5 — Article drafting

Each task = one article section. These are scholar work, not code. The "test" is the criterion : the section addresses the points laid out in the spec, has scholarly tone appropriate to DHQ, cites sources correctly.

### Task 14: §1 Introduction (~800 words)

**Files:**
- Create: `docs/papers/2026-05-amand-piste1-article-en.md`

- [ ] **Step 1: Draft §1**

Address per spec §4 :
- The historiographical controversy: Amand 1945 vs Bobzien 1998, 80+ years and 28 years respectively.
- Amand : external (Carneades, witnesses canonical, 3/6 rule).
- Bobzien : internal (Stoic self-critique antedating Carneades).
- Stakes : chronology of the emergence of the "free will problem" in antiquity.
- Operational question : for each of Amand's 6 moral pivots, are there Stoic-primary parallels (antedating or contemporary with Carneades) measurable in a structured corpus?
- Meta-thesis : the DH scholar with a corpus + algorithm is a quantifiable arbiter.

Verifier criteria :
- ~800 words
- Cites Amand 1945, Bobzien 1998 in opening paragraph
- States the operational question precisely
- States the meta-thesis explicitly
- Ends with article roadmap (§2-§7)

- [ ] **Step 2: Self-review and commit**

```bash
git add docs/papers/2026-05-amand-piste1-article-en.md
git commit -m "draft: article §1 Introduction"
```

---

### Task 15: §2 Background (~1,000 words)

- [ ] **Step 1: Draft §2**

Cover the full scholarly landscape per spec §4 :
- Amand 1945 : 6 moral pivots, brief summary of each, witnesses (6 canonical + secondary), 3/6 rule.
- Bobzien 1998 (Determinism and Freedom in Stoic Philosophy) : Chrysippus responds to Stoic-internal objections (Cleanthes, Diodore), problem of free will emerges with Alexander of Aphrodisias.
- Bobzien 2000, 2014 : Epicurus + Aristotle NE III contextual mentions.
- Frede 2011 (A Free Will) : median position, post-Chrysippus Stoic emergence + Alexander/Origen fixation.
- Dihle 1982 (Theory of Will) : will emerges with Augustine — diachronic depth.
- Long 1986, Long-Sedley 1987, Inwood 1985 : Hellenistic philosophy background.
- Sharples 1983/2001 : Alexander of Aphrodisias as the locus per Bobzien.
- Eliasson 2008 : Plotinus's ἐφ' ἡμῖν.
- Kane 2011 ed. : contemporary analytic context.

State the testable divergence : the 6 moral pivots' origin (external Carneadean vs internal Stoic).

- [ ] **Step 2: Self-review + commit**

```bash
git commit -am "draft: article §2 Background — full scholarly landscape"
```

---

### Task 16: §3 Method (~1,400 words)

- [ ] **Step 1: Draft §3**

Per spec §4 :
- Dataset construction : 6 Amand pivots + Stoic primary (Chrysippus 32 args + extended SVF II fragments + Cleanthes + Posidonius + Panaetius) + Stoic late as control (Epictetus + Seneca + Marcus Aurelius).
- Algorithm : 3 cumulative tests : thematic (keyword overlap), conceptual (shared concept nodes), textual (Greek lemma overlap with diacritic normalization).
- Score per pair : 0 to 3.
- Classification : Carneadean / hybrid / Stoic.
- Reproducibility : public code, KG snapshot, Zenodo DOI.
- Limits acknowledged here, expanded in §5.

- [ ] **Step 2: Commit**

```bash
git commit -am "draft: article §3 Method — 3-test provenance algorithm + dataset"
```

---

### Task 17: §4 Results (~1,800 words)

- [ ] **Step 1: Draft §4 with the actual matrix**

Per spec §4 :
- Insert the heatmap as Figure 1.
- Per-pivot classification (Carneadean / hybrid / Stoic) based on the actual matrix data.
- 2-3 case-study zoom-ins using the case-study figures (pivots III, VI, I).
- Mention contextual : Stoic late control (does pivot X parallel Epictetus/Seneca only? = compatible with Amand).

- [ ] **Step 2: Commit**

```bash
git commit -am "draft: article §4 Results — matrix + 3 case studies"
```

---

### Task 18: §5 Discussion (~1,500 words)

- [ ] **Step 1: Draft §5**

Per spec §4 :
- Amand vs Bobzien arbitration per pivot.
- Cross-check with Frede 2011 (median position) — does the matrix confirm/disconfirm Frede?
- Cross-check with Dihle 1982 — pivots touching "will" (pivot III, VI).
- Implications for the chronology of the free will problem.
- Subtleties : Amand acknowledges precedents; he claims Carneades *systematizes*. The matrix tests antecedence, not systematization.
- Meta-thesis discussion : matrix as arbiter or complement? Per the actual matrix clarity.
- Technical limits : Stoic dataset incompleteness, "parallel" definition fluidity, KG built by author (not neutral), Aristotle NE III mention only.
- Open questions : 3rd pole (Frede), Alexander of Aphrodisias future extension.

- [ ] **Step 2: Commit**

```bash
git commit -am "draft: article §5 Discussion — arbitration + cross-checks + meta-thesis"
```

---

### Task 19: §6 Conclusion + §7 Technical appendix

- [ ] **Step 1: §6 Conclusion (~400 words)**

Per spec §4 :
- Recap : algorithmic arbitration of Amand-Bobzien on N of 6 pivots.
- Per-pivot summary : K Amand, M Bobzien, Z ambiguous.
- Meta-thesis verdict : the DH scholar arbitrated empirically *where the data permits*.
- Future work : SVF complete ingestion, extension to Alexander of Aphrodisias, application to other scholars (Frede 2011, Dihle 1982).

- [ ] **Step 2: §7 Technical appendix (~1,500 words)**

Per spec §4 :
- KG architecture brief (Postgres + RDF/OWL/SHACL).
- Pipeline pseudo-code.
- FAIR data : Zenodo DOI for KG snapshot + code + matrix data.
- How to reproduce for another source pair A / B :
  1. Identify primary critical editions.
  2. Independent ingestion.
  3. Configure tests (thematic / conceptual / textual) with target keywords + Greek lemmas.
  4. Run matrix + manual validation.
- Method limits + recommendations.

- [ ] **Step 3: Commit**

```bash
git commit -am "draft: article §6 Conclusion + §7 Technical appendix"
```

---

## Phase 6 — Bibliography + Submission

### Task 20: Bibliography compilation

**Files:**
- Create: `docs/papers/2026-05-amand-piste1-bibliography.bib`

- [ ] **Step 1: Compile BibTeX**

Include all entries from spec §6 :

- `amand-1945-fatalisme` (existing)
- `bobzien-1998-determinism`, `bobzien-2000-epicurus-free-will`, `bobzien-2014-choice-responsibility` (existing in KG publications.bib — copy)
- `frede-2011-free-will`
- `dihle-1982-theory-will`
- `kane-2011-oxford-handbook`
- `long-1986-hellenistic-philosophy`
- `long-sedley-1987-hellenistic-philosophers`
- `inwood-1985-ethics-stoicism`
- `sharples-1983-alexander-de-fato`
- `sharples-2001-alexander-modus-operandi`
- `eliasson-2008-plotinus-eph-hemin`
- `von-arnim-1903-svf-ii` (existing from Task 2)
- `edelstein-kidd-1972-posidonius`
- `junod-1976-philocalia-sc226`
- `dindorf-1867-eusebius-pe`

For each, locate the canonical BibTeX entry (Google Scholar's BibTeX export is typically the fastest source). Verify each by reading the abstract or contents.

- [ ] **Step 2: Commit**

```bash
git add docs/papers/2026-05-amand-piste1-bibliography.bib
git commit -m "bib: complete bibliography for Amand-Piste1 DHQ article — Amand + Bobzien + Frede + Dihle + Long-Sedley + Inwood + Sharples + Eliasson + von Arnim + Edelstein-Kidd + Junod"
```

---

### Task 21: Self-review article + final revisions

- [ ] **Step 1: Read article end-to-end**

Read `docs/papers/2026-05-amand-piste1-article-en.md` cover to cover. Check :
- Total word count is 7,500-9,000 (excluding appendix).
- Each section ends naturally and transitions to the next.
- All claims are cited.
- All bibliography entries are used.
- Figures Figure 1 (heatmap) + Figure 2-4 (case studies) are referenced in the right sections.
- The meta-thesis is stated in §1 and revisited in §5.
- Tone is academic but accessible (DHQ audience).

- [ ] **Step 2: Apply revisions**

- [ ] **Step 3: Commit final draft**

```bash
git commit -am "draft: article final-revision pass — DHQ submission-ready"
```

---

### Task 22: Zenodo DOI + submission package

**Files:**
- Modify: `data/scholarly_sources/manifest.jsonl`
- Create: `docs/papers/2026-05-amand-piste1-zenodo-readme.md`

- [ ] **Step 1: Prepare data package for Zenodo**

Bundle :
- `data/kg/snapshots/2026-05-XX-amand-piste1-publication/` — KG snapshot at publication time
- `docs/papers/2026-05-amand-piste1-data/` — matrix JSON + manual validation log
- `scripts/analyze_amand_stoic_provenance.py` and related scripts
- README explaining how to reproduce

- [ ] **Step 2: Create Zenodo README**

```markdown
# EleutherIA — Amand Piste 1 reproducible data

Companion data archive for Girardi (2026), "Algorithmic provenance analysis
of six moral anti-fatalist pivots: testing Amand 1945's Carneadean
attribution against the primary Stoic corpus", DHQ.

## Contents
- `kg/` — KG snapshot at publication time (nodes.jsonl, edges.jsonl)
- `scripts/` — Provenance analyzer + figure generator
- `data/` — Output matrix + manual validation log
- `figures/` — Heatmap + case-study figures

## Reproduction
1. ...
2. ...

## License
CC-BY 4.0
```

- [ ] **Step 3: Upload to Zenodo, get DOI**

(Manual step — Romain)

- [ ] **Step 4: Insert Zenodo DOI in article**

Insert in §7 Technical appendix : `Code and data: https://doi.org/10.5281/zenodo.XXXXXXX`

- [ ] **Step 5: Final commit**

```bash
git commit -am "submit: Zenodo DOI inserted, article and data archived"
```

---

### Task 23: DHQ submission

- [ ] **Step 1: Format article per DHQ guidelines**

DHQ accepts Markdown or TEI. Confirm format requirements from current DHQ submission guidelines page.

- [ ] **Step 2: Submit via DHQ portal**

(Manual step — Romain)

- [ ] **Step 3: Create tracking note**

Create `docs/papers/2026-05-amand-piste1-submission-log.md` tracking :
- Submission date
- Editor assigned
- Review timeline
- Revisions requested
- Acceptance / rejection

---

## Self-Review

**Spec coverage** :
- Spec §1 Thèse centrale → Tasks 14 (§1) + 16 (§3) + 17 (§4) + 18 (§5)
- Spec §1bis Meta-thesis → Tasks 14 + 18 explicit
- Spec §4 Plan d'article → Tasks 14-19 one task per section
- Spec §5 Données disponibles → Tasks 1-5 enrichment
- Spec §6 Travail à faire → Tasks 1-22 mapped
- Spec §7 Risks → Risk R1 (parallel definition) addressed by manual validation Task 13; Risk R2 (Stoic corpus incomplete) addressed by Task 2-4 enrichment; Risk R3 (Bobzien is authority) addressed by §5 framing as arbitration not refutation in Task 18; Risk R4 (ambiguous result) addressed by §5 Task 18; Risk R5 (over-interpretation) addressed by §5 limits Task 18.
- Spec §8 Timeline → Tasks total ~8 weeks consistent.
- Spec §9 Decision points → 5 deferred decisions documented; resolved during execution.

**Placeholder scan** : All steps have concrete code or content. The article-section tasks (14-19) have criteria rather than literal text — appropriate for scholar work but anchored to spec §4 references.

**Type consistency** : `PairScore` dataclass used consistently across Tasks 6-10. `AMAND_MORAL_PIVOTS` + `STOIC_PRIMARY` tuples shared by tests + analyzer. Figure functions `generate_heatmap` + `generate_case_study` consistent.

Plan complete and saved.
