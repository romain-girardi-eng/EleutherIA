# Sources Chrétiennes Corpus Import — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Import 40 Sources Chrétiennes source files (pure Greek/Latin original texts) into EleutherIA's dual-layer architecture: textual layer (`ancient_works` + `passages`) and knowledge graph layer (`kg_nodes` + `kg_edges` + `passage_citations`).

**Design Document:** `docs/plans/2026-02-21-sc-corpus-import-design.md`

**Architecture:** Option C — Chapter-level KG Passage nodes + paragraph-level `passages` rows. Contre Celse exception: paragraph-level KG nodes (no sub-chapter structure).

**Zero-Hallucination Policy:** ALL text content is script-extracted verbatim. No LLM touches original text. Work descriptions from INDEX.md only.

**Corpus Location:** `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/Sources chrétiennes txt/`

---

## Task 1: Create script directory and data models

**Files:**
- Create: `database/scripts/import_sc/__init__.py`
- Create: `database/scripts/import_sc/models.py`

**Step 1: Create the directory**

```bash
mkdir -p database/scripts/import_sc
```

**Step 2: Create `__init__.py`**

Empty file:
```python
"""Sources Chrétiennes corpus import pipeline."""
```

**Step 3: Create `models.py`**

Define the three core dataclasses:

```python
"""Data models for Sources Chrétiennes import pipeline."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class SCParagraph:
    """A single paragraph block from a source file (delimited by ===== lines)."""
    raw_ref: str           # e.g., "[par.: 1]" or "[chap.: 4, par.: 2-3]"
    chapter: str | None    # Parsed chapter number or name (e.g., "4", "salutation")
    paragraph: str | None  # Parsed paragraph number (e.g., "1", "2-3", None)
    text: str              # Cleaned original text (Greek or Latin)
    sequence: int          # 0-indexed within work
    section_title: str | None = None  # e.g., "### TITLE ###" if extracted


@dataclass
class SCChapter:
    """A chapter-level grouping of paragraphs."""
    chapter_ref: str           # e.g., "1", "salutation", "III.1"
    paragraphs: list[SCParagraph] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenation of all paragraph texts, separated by double newline."""
        return "\n\n".join(p.text for p in self.paragraphs if p.text.strip())

    @property
    def paragraph_count(self) -> int:
        return len(self.paragraphs)


@dataclass
class SCWork:
    """A parsed source file representing one work or book."""
    file_path: str
    file_name: str             # Just the filename (no directory)
    sc_number: str             # e.g., "507", "10bis", "132"
    author: str                # From file header AUTEUR field
    title: str                 # From file header OEUVRE field
    title_original: str        # From file header TITRE ORIGINAL field (may be empty)
    book: str                  # From file header LIVRE field
    declared_paragraphs: int   # From file header PARAGRAPHES field
    language: str              # "grc" or "lat"
    chapters: list[SCChapter] = field(default_factory=list)

    # Populated from WORK_REGISTRY:
    node_id: str = ""
    edition: str = ""
    date_composed: str = ""
    description: str = ""
    period: str = ""
    school: str = ""
    reference_format: str = ""  # "A", "B", "C", or "D"
    author_kg_id: str | None = None
    series_prev: str | None = None
    series_next: str | None = None

    @property
    def total_paragraphs(self) -> int:
        return sum(ch.paragraph_count for ch in self.chapters)

    @property
    def canonical_id(self) -> str:
        return self.node_id  # Same as the KG Work node_id
```

**Step 4: Verify syntax**

Run: `cd database && python -c "from scripts.import_sc.models import SCWork, SCChapter, SCParagraph; print('OK')"`

Expected: `OK`

---

## Task 2: Create the parser module

**Files:**
- Create: `database/scripts/import_sc/parser.py`

This is the most critical module. It reads source files and produces `SCWork` objects. ZERO LLM involvement — pure regex parsing.

**Step 1: Create `parser.py`**

The parser must handle 4 reference format variants:

- **Format A** — Contre Celse: `[par.: N]` — Regex: `^\[par\.\s*:\s*(\d+)\]$`
- **Format B** — De Principiis: `[liv.: N, chap.: N, par.: N]` — Regex: `^\[liv\.\s*:\s*(\d+),\s*chap\.\s*:\s*(\d+),\s*par\.\s*:\s*(\d+)\]$`
- **Format C** — Justin/Apologistes: `[première apologie, chap.: N]` or `[salutation]` — Regex: `^\[.+,\s*chap\.\s*:\s*(\d+)\]$` with fallback `^\[([^\]]+)\]$`
- **Format D** — Ignatius/Clement/Barnabas/Hermas/etc.: `[chap.: N, par.: N-N]` or `[chap.: N]` or `[salutation]` or `[§ N]` — Regex cascade

Key functions:
- `parse_file(file_path: str, registry_entry: dict) -> SCWork` — main entry point
- `_parse_header(lines: list[str]) -> dict` — extract AUTEUR, OEUVRE, TITRE ORIGINAL, LIVRE, PARAGRAPHES
- `_split_blocks(content: str) -> list[str]` — split on `==================================================`
- `_parse_reference(ref_line: str, format_type: str) -> tuple[str|None, str|None]` — returns (chapter, paragraph)
- `_clean_text(raw: str) -> str` — apply the 6-step cleaning pipeline from design doc §7.3
- `_group_into_chapters(paragraphs: list[SCParagraph], format_type: str) -> list[SCChapter]` — group paragraphs by chapter

Text cleaning pipeline (ORDER MATTERS):
1. Remove page number markers: `--- 126 ---` → `re.sub(r'---\s*\d+\s*---', '', raw)`
2. Remove section title markers: `### TITLE ###` → `re.sub(r'###[^#]+###', '', text)` (store as metadata)
3. Strip TRADUCTION sections (SC268 source files only): split on `--- TRADUCTION ---`, keep only first part
4. Remove SOURCE/LATIN markers: `--- SOURCE ---`, `--- LATIN ---` → remove
5. Rejoin hyphenated line breaks: `re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)`
6. Normalize whitespace: `re.sub(r'\n{3,}', '\n\n', text).strip()`

CRITICAL DETAILS from source file inspection:
- Contre Celse (Format A): Paragraphs start with `N.` (e.g., `1. [Πρῶτον...`) — the number prefix is part of the text, keep it
- SC268 (Format B): Each block has `--- SOURCE ---` then Greek text then `--- TRADUCTION ---` then French — strip everything from TRADUCTION onwards
- Justin (Format C): Header has `AUTEUR:` on first line (no `SC XXX` prefix). Chapter refs like `[première apologie, chap.: N]`
- Ignatius (Format D): Has `[salutation]` as first block, then `[chap.: N, par.: N-N]` or just `[chap.: N]`
- Some files have duplicate `[par.: N]` refs (e.g., CC I has two `[par.: 9]` blocks) — both are legitimate, the second is a continuation. Handle by appending `_bis` or making sequence_number unique
- Page markers like `--- 78 ---` appear INLINE within text (not on separate lines) — the regex must handle this

**Step 2: Write tests for the parser**

Create `database/scripts/import_sc/test_parser.py` with tests for:
- Each format variant (A, B, C, D)
- Text cleaning (page markers, section titles, TRADUCTION stripping)
- Chapter grouping
- Edge cases (duplicate refs, salutation, empty blocks)

Run tests: `cd database && python -m pytest scripts/import_sc/test_parser.py -v`

Expected: All tests pass

---

## Task 3: Create the config module (WORK_REGISTRY)

**Files:**
- Create: `database/scripts/import_sc/config.py`

**Step 1: Create `config.py`**

Contains:
- `SC_CORPUS_DIR` — path to the corpus directory
- `WORK_REGISTRY` — dict mapping filename → scholarly metadata for all 40 source files
- `REFERENCE_FORMATS` — dict mapping format letter to regex patterns

Each entry in WORK_REGISTRY must have:
```python
{
    "node_id": "sc507_iustinus_apologia_i",
    "author": "Iustinus Martyr",
    "author_kg_id": "iustinus_martyr",  # or None if no existing Person node
    "title": "Apologie I pour les chrétiens",
    "title_original": "Ἀπολογία ὑπὲρ Χριστιανῶν",
    "language": "grc",  # or "lat"
    "period": "Imperial",
    "school": "Christian Apologetics",
    "date_composed": "c. 150-155 CE",
    "edition": "Ch. Munier, 2006",
    "sc_volume": "SC 507",
    "description": "...",  # From INDEX.md — see design doc §11
    "reference_format": "C",  # A, B, C, or D
    "series_next": None,  # node_id of next book in series, or None
    "series_prev": None,
}
```

All 40 files must be mapped. Group by category:

**01_Peres_apostoliques (14 files):**
- SC10bis × 11 files (Ignatius 7 letters + Martyrium 2 + Appendices 2) — Format D, grc
- SC167 Clement — Format D, grc
- SC172 Barnabas — Format D, grc
- SC53bis Hermas — Format D, grc

**02_Apologistes (13 files):**
- SC123 × 5 files (Melito + Apollinaris) — Format D, grc
- SC20 × 3 files (Theophilus Ad Autolycum I-III) — Format D, grc
- SC31 Melito fragments — Format D, grc
- SC379 Athenagoras — Format C, grc
- SC470 Aristides — Format C, grc
- SC507 Justin — Format C, grc
- SC528 Pseudo-Justin — Format C, grc

**03_Origene (11 files):**
- SC132 × 3 (CC Préface, I, II) — Format A, grc
- SC136 × 2 (CC III, IV) — Format A, grc
- SC147 × 2 (CC V, VI) — Format A, grc
- SC150 × 2 (CC VII, VIII) — Format A, grc
- SC268 × 2 (Peri Archon III, IV extraits grecs) — Format B, grc

**04_Autres (2 files):**
- SC464 Pamphilus — Format D, lat
- SC79 Chrysostome — Format D, grc

**Step 2: Write descriptions from INDEX.md**

For each work, extract description from `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/Sources chrétiennes txt/INDEX.md`. Follow the template from design doc §11.2. Each description should be 100-300 words in English covering: author, dates, work title, genre, edition, relevance to free will debates, key terms.

For works where INDEX.md has minimal info, write a minimal factual description (author, title, edition) without any commentary.

**Step 3: Define series relationships**

Multi-book series need `series_prev`/`series_next`:
- Contre Celse: Préface → I → II → III → IV → V → VI → VII → VIII
- Ad Autolycum: I → II → III
- De Principiis: III → IV

**Step 4: Verify config completeness**

Run: `python -c "from database.scripts.import_sc.config import WORK_REGISTRY; print(f'{len(WORK_REGISTRY)} files mapped')"`

Expected: `40 files mapped`

---

## Task 4: Create the mapper module

**Files:**
- Create: `database/scripts/import_sc/mapper.py`

The mapper transforms `SCWork` objects into database insertion payloads.

**Step 1: Create `mapper.py`**

Key functions:

```python
def to_ancient_work(work: SCWork) -> dict:
    """Map SCWork → ancient_works INSERT payload."""
    # Returns dict with: canonical_id, title, title_original, author, language, period,
    # school, source="sources_chretiennes", division_scheme, metadata (sc_number, edition, etc.)

def to_passages(work: SCWork, work_uuid: uuid.UUID) -> list[dict]:
    """Map SCWork paragraphs → passages INSERT payloads."""
    # One row per SCParagraph. Fields: work_id, canonical_ref, cts_urn, book, chapter,
    # section, sequence_number, text_content, char_length, word_count, citation_hierarchy

def to_work_kg_node(work: SCWork, work_uuid: uuid.UUID, passage_data: list[dict]) -> dict:
    """Map SCWork → kg_nodes INSERT payload (Work type)."""
    # node_id = work.node_id, type = "Work", description = work.description
    # metadata includes page_index tree built from chapters

def to_chapter_kg_nodes(work: SCWork, passage_data: list[dict]) -> list[dict]:
    """Map SCWork chapters → kg_nodes INSERT payloads (Passage type)."""
    # For standard works: one KG node per chapter (text = concatenated paragraphs)
    # For Contre Celse (format A): one KG node per paragraph

def to_kg_edges(work: SCWork) -> list[dict]:
    """Generate all KG edges for this work."""
    # has_chapter/has_section, written_by, continues, belongs_to_corpus

def to_passage_citations(passage_data: list[dict], chapter_nodes: list[dict]) -> list[dict]:
    """Link each passage to its chapter KG node."""
    # confidence = 1.0, citation_type = "primary_source"
```

**Pseudo-URN format:** `urn:sc:{sc_number}:{book}.{chapter}.{paragraph}`
- Justin Apology I ch. 4: `urn:sc:507:1.4`
- CC I par 1: `urn:sc:132:1.1`
- De Principiis III.1.1: `urn:sc:268:3.1.1`
- Ignatius Eph. salutation: `urn:sc:10bis:eph.salutation`

**KG node_id format:**
- Work: `sc{sc_number}_{author_slug}_{work_slug}`
- Chapter: `sc{sc_number}_{work_slug}_chap{N}` (or `_par{N}` for Contre Celse)
- Slug: lowercase, spaces→`_`, accents stripped, special chars removed

**Page-index tree** (in Work node metadata.page_index):
```json
[
  {"chapter_ref": "1", "node_id": "sc507_..._chap1", "sc_urn": "urn:sc:507:1.1", "paragraph_count": 1, "passage_ids": ["uuid"]},
  ...
]
```

**Step 2: Verify mapper output**

Write a quick test: parse one file, run through mapper, print the payloads. Ensure all fields are populated and node_ids are valid.

---

## Task 5: Create the validator module

**Files:**
- Create: `database/scripts/import_sc/validator.py`

**Step 1: Create `validator.py`**

Implements Gate 1 checks from design doc §12:

```python
def validate_work(work: SCWork) -> list[str]:
    """Return list of error/warning messages. Empty = valid."""

def validate_corpus(works: list[SCWork]) -> tuple[list[str], list[str]]:
    """Validate entire corpus. Returns (errors, warnings)."""
```

Checks:
1. All 40 source files found
2. File header has AUTEUR/OEUVRE fields (WARN if missing)
3. Every file has an entry in WORK_REGISTRY (ABORT if missing)
4. No block contains `--- TRADUCTION ---` after cleaning (ABORT — except SC268 handled)
5. No block text is empty after cleaning (WARN)
6. Paragraph count matches header `PARAGRAPHES:` field ±10% (WARN)
7. All `canonical_ref` values unique within a work (ABORT on duplicates — but note legitimate `[par.: 9]` duplication in CC)
8. All `node_id` values globally unique (ABORT)
9. Greek text files contain Greek Unicode range U+0370–U+1FFF (WARN if absent)
10. No text_content exceeds 100KB (WARN — likely a parsing error)

**Step 2: Test validator**

Run dry parse + validation on a sample file:
```python
from database.scripts.import_sc.parser import parse_file
from database.scripts.import_sc.config import WORK_REGISTRY
from database.scripts.import_sc.validator import validate_work

work = parse_file("path/to/SC507...", WORK_REGISTRY["SC507..."])
errors = validate_work(work)
print(errors)  # Should be empty
```

---

## Task 6: Create the importer module

**Files:**
- Create: `database/scripts/import_sc/importer.py`

**Step 1: Create `importer.py`**

Handles actual PostgreSQL insertion using psycopg2/asyncpg.

```python
class SCImporter:
    def __init__(self, db_url: str, dry_run: bool = True):
        self.db_url = db_url
        self.dry_run = dry_run
        self.run_id = str(uuid.uuid4())  # For rollback tracking
        self.stats = ImportStats()

    def import_work(self, work: SCWork) -> None:
        """Insert one work into all 5 tables within a transaction."""
        # 1. INSERT ancient_works → get work_uuid
        # 2. INSERT passages (batch) → get passage_uuids
        # 3. INSERT kg_nodes (Work) with page_index
        # 4. INSERT kg_nodes (Chapter/Paragraph ×N)
        # 5. INSERT kg_edges
        # 6. INSERT passage_citations
        # All within a single transaction — rollback on any error

    def import_corpus(self, works: list[SCWork]) -> ImportStats:
        """Import all works. Returns statistics."""

    def rollback_run(self, run_id: str) -> None:
        """Delete all data created in a specific run."""
```

**Key details:**
- Use transactions: one per work, rollback the entire work on any error
- Store `run_id` in metadata JSONB for each inserted row (for rollback support)
- Use `ON CONFLICT DO NOTHING` for kg_nodes in case of duplicate node_ids
- Batch INSERT passages (500 rows per batch)
- Print progress: `[12/40] Importing SC507 Justin Apologie I... 108 passages, 68 chapter nodes`

**Step 2: Dry-run mode**

When `dry_run=True`, compute all payloads but skip actual SQL execution. Print statistics matching design doc §12 Gate 2 format.

---

## Task 7: Create the Sources Chrétiennes collection node

**Files:**
- Create: `database/scripts/import_sc/collection_node.py` (or add to importer)

**Step 1: Create/verify the SC collection node**

Before importing works, ensure the global SC collection node exists:

```python
KGNode(
    node_id = "sources_chretiennes",
    label = "Sources Chrétiennes (SC)",
    type = "Source_Collection",
    description = "Bilingual critical edition series of early Christian texts, published by Éditions du Cerf, Paris (1942–). Each volume provides the original Greek or Latin text with French translation and critical apparatus.",
    metadata = {
        "publisher": "Éditions du Cerf",
        "location": "Paris",
        "founded": 1942,
        "total_volumes": "600+",
        "phase_1_volumes": ["SC10bis", "SC20", "SC31", "SC53bis", "SC79", "SC123", "SC132", "SC136", "SC147", "SC150", "SC167", "SC172", "SC268", "SC379", "SC464", "SC470", "SC507", "SC528"]
    }
)
```

This node is the target for `belongs_to_corpus` edges from all Work nodes.

---

## Task 8: Create the CLI orchestrator

**Files:**
- Create: `database/scripts/import_sc/run.py`

**Step 1: Create `run.py`**

CLI interface with argparse:

```bash
# Dry run (parse only, no DB writes, show statistics)
python -m database.scripts.import_sc.run --dry-run

# Full import (with confirmation prompt)
python -m database.scripts.import_sc.run --confirm

# Single file (for testing)
python -m database.scripts.import_sc.run --file SC507_Iustinus_martyr_Apologie_livre_1_source.txt --dry-run

# Specific category
python -m database.scripts.import_sc.run --category 02_Apologistes --dry-run

# Rollback (delete all nodes/passages created in last run)
python -m database.scripts.import_sc.run --rollback --run-id <uuid>
```

**Execution flow:**
1. Load WORK_REGISTRY from config.py
2. Discover all `*_source.txt` files in corpus directory
3. For each file: `parser.parse_file()` → `validator.validate_work()`
4. Run `validator.validate_corpus()` — ABORT on errors
5. **DRY RUN:** print statistics, exit
6. **CONFIRMED:** for each validated SCWork → `importer.import_work()`
7. Run Gate 3 post-import verification queries

**Step 2: Test CLI**

```bash
python -m database.scripts.import_sc.run --dry-run --file SC507_Iustinus_martyr_Apologie_livre_1_source.txt
```

Expected: Statistics printed for Justin's Apology (108 paragraphs, 68 chapters, 68 chapter KG nodes + 1 Work KG node)

---

## Task 9: Test on one file per format

**Files:**
- No new files, but run the pipeline end-to-end on test files

**Step 1: Test Format A (Contre Celse)**

```bash
python -m database.scripts.import_sc.run --dry-run --file SC132_Origenes_Contre_Celse_Livre_I_livre_1_source.txt
```

Verify:
- 88 paragraphs parsed
- 88 paragraph-level KG nodes (not chapter-level)
- Page markers removed from text
- Section titles (`### TITLE ###`) extracted as metadata
- No French text in any block

**Step 2: Test Format B (De Principiis)**

```bash
python -m database.scripts.import_sc.run --dry-run --file SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt
```

Verify:
- 35 paragraphs parsed
- TRADUCTION sections completely stripped
- SOURCE markers removed
- Chapters grouped correctly (e.g., chap 1 has multiple paragraphs)

**Step 3: Test Format C (Justin)**

```bash
python -m database.scripts.import_sc.run --dry-run --file SC507_Iustinus_martyr_Apologie_livre_1_source.txt
```

Verify:
- 108 paragraphs parsed
- 68 chapter KG nodes
- Page markers removed from text
- Chapter refs extracted from `[première apologie, chap.: N]`

**Step 4: Test Format D (Ignatius)**

```bash
python -m database.scripts.import_sc.run --dry-run --file SC10bis_Ignatius_Antiochenus_Lettres_authentiques_Lettre_aux_Ephesiens_livre_1_source.txt
```

Verify:
- 23 paragraphs parsed
- `[salutation]` handled correctly
- `[chap.: N, par.: N-N]` parsed (paragraph range)
- `[chap.: N]` parsed (no paragraph sub-number)

**Step 5: Fix any parser errors found during testing**

Iterate until all 4 formats parse cleanly.

---

## Task 10: Full corpus dry run

**Files:**
- No new files

**Step 1: Run full dry run**

```bash
python -m database.scripts.import_sc.run --dry-run
```

**Step 2: Verify statistics match expectations**

Expected (approximate, from design doc Appendix A):
- Files processed: 40
- Works created: 40
- Passages: ~2500–3000
- Chapter KG nodes: ~400–600 (standard works)
- Paragraph KG nodes: ~650–750 (Contre Celse only)
- Total KG nodes: ~1100–1400 (including 40 Work nodes)
- KG edges: ~1500–1800
- Passage citations: ~2500–3000
- Validation errors: 0
- Validation warnings: < 10

**Step 3: Review any warnings**

Fix the root cause of each warning. Common issues:
- Paragraph count mismatch vs header (usually ±1-2, acceptable)
- Empty blocks (usually blank separators at end of file)
- Missing Greek Unicode (for SC464 Latin file — expected, not an error)

**Step 4: Save dry-run output for Romain's review**

```bash
python -m database.scripts.import_sc.run --dry-run > docs/plans/sc-import-dry-run-output.txt 2>&1
```

---

## Task 11: REVIEW CHECKPOINT — Romain approves

**This is a human gate. Do NOT proceed to Task 12 without Romain's explicit approval.**

Present to Romain:
1. Dry-run statistics
2. Sample parsed output for one file per format (text excerpts showing clean extraction)
3. List of all node_ids that will be created
4. All work descriptions from config.py

Romain reviews:
- [ ] Descriptions are accurate and factual
- [ ] Node_ids are sensible
- [ ] Statistics look correct
- [ ] No translation/commentary leaked into any text_content

---

## Task 12: Import to local/staging database

**Files:**
- No new files

**Step 1: Ensure local PostgreSQL is running**

```bash
docker compose -f deploy/docker/docker-compose.yml up -d db
```

**Step 2: Run confirmed import**

```bash
python -m database.scripts.import_sc.run --confirm
```

**Step 3: Run Gate 3 verification queries**

```sql
-- Count works
SELECT COUNT(*) FROM ancient_works WHERE source = 'sources_chretiennes';
-- Expected: 40

-- Count passages
SELECT COUNT(*) FROM passages p
JOIN ancient_works w ON p.work_id = w.work_id
WHERE w.source = 'sources_chretiennes';
-- Expected: ~2500-3000

-- Count KG nodes
SELECT COUNT(*), type FROM kg_nodes
WHERE metadata->>'phase' = '1'
GROUP BY type;
-- Expected: Work=40, Passage=~1100-1400

-- Count edges
SELECT COUNT(*), relation FROM kg_edges e
JOIN kg_nodes n ON e.source_id = n.node_id
WHERE n.metadata->>'phase' = '1'
GROUP BY relation;

-- Count passage_citations
SELECT COUNT(*) FROM passage_citations pc
JOIN passages p ON pc.passage_id = p.passage_id
JOIN ancient_works w ON p.work_id = w.work_id
WHERE w.source = 'sources_chretiennes';
-- Expected: ~2500-3000

-- Spot check: no French text leaked
SELECT passage_id, LEFT(text_content, 100)
FROM passages p
JOIN ancient_works w ON p.work_id = w.work_id
WHERE w.source = 'sources_chretiennes'
AND text_content ~* '(traduction|français|chapitre|livre|page)'
LIMIT 10;
-- Expected: 0 rows (or false positives from legitimate Greek/Latin)

-- Spot check: Greek text is present
SELECT canonical_ref, LEFT(text_content, 80)
FROM passages p
JOIN ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id = 'sc507_iustinus_apologia_i'
ORDER BY sequence_number
LIMIT 5;
```

**Step 4: Spot-check text quality**

Manually compare 3 random passages against the source files:
1. One from Contre Celse (Format A)
2. One from De Principiis (Format B)
3. One from Justin (Format C)

Verify: identical text, no page markers, no translations, diacritics preserved.

---

## Task 13: Commit and document

**Files:**
- Stage: all files in `database/scripts/import_sc/`

**Step 1: Commit**

```bash
git add database/scripts/import_sc/
git commit -m "feat(database): add Sources Chrétiennes corpus import pipeline

Implements Phase 1 import of 40 SC source files (Greek/Latin) into
dual-layer architecture: ancient_works + passages tables, and
kg_nodes + kg_edges knowledge graph layer.

Parses 4 reference format variants (Contre Celse, De Principiis,
Justin/Apologistes, Ignatius/Patristic). Zero-hallucination policy:
all text content script-extracted verbatim."
```

---

## Future Tasks (not part of this plan)

### Phase 2 — Bilingue-Only Latin Works
- SC532–SC555 Commentaire sur Romains (Latin via Rufin)
- SC268 full De Principiis III–IV (Latin via Rufin)
- SC007bis Homélies sur la Genèse (Latin via Rufin)
- Parser addition: detect `--- LATIN ---`, extract Latin, skip `--- FRANCAIS ---`

### Phase 3 — Alexander de Fato Cleanup
- Audit existing de Fato KG nodes
- Remove translations/commentary from `description` fields
- Reparse from clean source if available
- Script: `database/scripts/cleanup_de_fato.py`

### Qdrant Vectorization
- After DB import is verified, vectorize all new passages for semantic search
- Add to existing Qdrant collections
