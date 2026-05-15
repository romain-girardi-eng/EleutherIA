# Scholarly Sources Archive

Centralized OCR'd text of scholarly publications cited in the EleutherIA KG.
Acts as the single source of truth for raw OCR output, so each batch of
KG ingestion does not redo OCR from the PDF.

## Why

The OCR pipeline for a 600-page scholarly French book is expensive (engine
runtime + manual proofreading + Greek/Latin polytonic quality control).
Once a source is OCR'd at acceptable quality, the raw text becomes a
reusable artifact: future agents (or other contributors on a fresh clone)
should consume the archived `.md` directly, not the PDF.

The PDF and OCR'd text are tracked **only** through `manifest.jsonl`
(metadata + md5 fingerprint). The actual text files live under `ocr/`
which is gitignored — most sources are still under copyright (e.g. Amand
de Mendieta died in 2004, his thesis enters public domain c. 2074).

## Structure

```
data/scholarly_sources/
├── manifest.jsonl              # tracked: one JSON line per publication
├── README.md                   # tracked: this file
└── ocr/                        # gitignored: raw OCR artifacts
    └── {publication_dir}/
        ├── source.md           # canonical OCR text (Markdown)
        ├── source.html         # optional formatted variant
        ├── source.pdf          # optional symlink to original PDF
        └── ocr_meta.json       # OCR engine + run details + per-section quality
```

## Conventions

- **`publication_dir`** — short concat slug, ASCII only. Pattern:
  `{author_lastname_lower}{year}{title_first_word_lower}`. Example:
  `amand1945fatalisme`, `bobzien1998determinism`, `frede2011free`.
- **`bibtex_key`** — matches the entry in `data/kg/publications.bib`
  (often a longer kebab-cased form). Both keys live in the manifest;
  the short `publication_dir` is filesystem-friendly, the long
  `bibtex_key` is the canonical scholarly identifier.
- **`kg_publication_id`** — matches the `id` of the corresponding
  `publication` node in `data/kg/nodes.jsonl`. Example:
  `pub_amand_1945_fatalisme`.

## Manifest schema

Each line of `manifest.jsonl` is a JSON object with:

| field | type | description |
|---|---|---|
| `publication_dir` | string | short slug, matches the `ocr/{dir}/` name |
| `bibtex_key` | string | canonical bibtex key in `publications.bib` |
| `kg_publication_id` | string | KG publication node `id` |
| `title` | string | full title |
| `subtitle` | string \| null | subtitle if any |
| `author` | string | author full name |
| `year_original` | int | year of first publication |
| `year_edition_used` | int | year of the edition actually OCR'd |
| `edition_used` | string | publisher + city of the edition OCR'd |
| `isbn` | string \| null | ISBN of the edition OCR'd |
| `pdf_md5` | string | md5 of the source PDF (32 hex) |
| `md_md5` | string | md5 of `source.md` (32 hex) |
| `pdf_size_bytes` | int | size of source PDF |
| `md_size_bytes` | int | size of source.md |
| `ocr_engine` | string | OCR engine name + version (or `"unknown"`) |
| `ocr_quality_pct_fr` | int | estimated French OCR quality % |
| `ocr_quality_pct_grc` | int | estimated Greek OCR quality % (if applicable) |
| `ocr_quality_pct_lat` | int | estimated Latin OCR quality % (if applicable) |
| `word_count` | int | total word count of source.md |
| `line_count` | int | total line count of source.md |
| `page_count` | int | page count of original PDF |
| `language_primary` | string | ISO 639-1 (`fr`, `en`, `de`, `it`, ...) |
| `languages_secondary` | list[string] | ISO 639-1 codes of secondary languages (`el`, `la`, ...) |
| `kg_ingestion_status` | string | `pending` \| `in_progress` \| `complete` |
| `kg_ingestion_batches` | list[string] | ordered list of batches that touched this source (e.g. `["B0", "B1", ...]`) |
| `kg_node_count` | int \| null | number of KG nodes derived from this source |
| `notes` | string \| null | free text |
| `added_to_archive` | string | YYYY-MM-DD of archive entry creation |
| `last_updated` | string | YYYY-MM-DD of last manifest mutation |

## Adding a new source

1. Place OCR'd files in `ocr/{publication_dir}/`. Use `source.md` for the
   canonical Markdown variant. Add `source.html` and `ocr_meta.json` if
   available.
2. Run `python scripts/archive_scholarly_source.py {publication_dir}`
   (idempotent script). It computes md5s, word/line counts, and writes
   or updates a line in `manifest.jsonl`.
3. (Optional) Update the KG `publication` node metadata to include
   `scholarly_source_dir: "{publication_dir}"` so the GraphRAG layer
   can surface the archived text in scholarly Q&A.

## Linking from the KG

The KG `publication` nodes carry a `metadata.scholarly_source_dir` field
when an archived text exists. The GraphRAG retrieval layer can resolve
this to `data/scholarly_sources/ocr/{dir}/source.md` on the local clone.
For contributors without local access to the OCR archive (because their
clone does not have the gitignored files), the manifest provides md5
and edition metadata sufficient to procure the same source.
