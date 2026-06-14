# Enrichment proposal spec (shared by all waves)

You READ secondary literature and produce **staged proposals** as JSONL. You do **NOT** edit `nodes.jsonl`, `edges.jsonl`, or the DB. Append one JSON object per line to your assigned output file.

## Hard constraints (academic integrity)
1. **ZERO fabrication of ancient Greek/Latin.** Only transcribe original-language text that *physically appears* in a source file you actually read. If a scholar references a locus but you do not have the verbatim text in front of you, set `"found_verbatim": false` and leave `text_original` empty — never reconstruct it.
2. **Citations = original language + English.** Never French translation. If the source is French, you translate the *English* yourself and set `"translation_source": "agent"`. If the source gives the original Greek/Latin, transcribe it exactly (preserve polytonic diacritics).
3. **Critical editions only** for primary loci (PG/PL, SC, GCS, CCSL, PTS, Loeb, BT, OCT, Teubner). Record the edition.
4. **No duplicate nodes.** Before proposing any node, `grep` `data/kg/nodes.jsonl` for existing `scholarly_work_*`, `scholarly_argument_*`, `scholar_position_*`, `pub_*`, `person_*`, `concept_*`, `argument_*` on that author/work/concept. Prefer referencing/enriching an existing `id`. Note duplicates you find.
5. **Reuse existing ontology predicates** (see EDGE TYPES below). Map any off-ontology relation to the closest existing one.

## Output record kinds (the `"kind"` field)
- `publication_node` — a secondary-lit work. Fields: `proposed_id` (use `pub_<author>_<year>_<slug>`), `label`, `authors`, `year`, `title`, `venue`, `existing_duplicate_ids` (array, may be empty), `source_file`.
- `node` — a new primary-layer node (concept/debate/controversy/work/person/argument). Fields: `proposed_id`, `type`, `label`, `description`, `period`, `existing_duplicate_ids`, `evidence` (which article + page).
- `edge` — Fields: `relation` (must be from EDGE TYPES), `source_id`, `target_id`, `weight` (0–1), `rationale`, `source_file`. Use real existing ids where known; for not-yet-created nodes use the `proposed_id`.
- `quote` — a primary-source quotation a scholar relies on that the corpus may be missing. Fields: `text_original`, `language` (`grc`/`lat`), `translation_en`, `translation_source` (`source`/`agent`), `author`, `work`, `locus`, `critical_edition`, `found_verbatim` (bool), `cited_by` (the scholar/article), `relates_to_argument_id` (KG argument id if applicable).
- `ground_locus` — a primary locus a scholar cites that should ground an existing ungrounded KG argument. Fields: `argument_id`, `author`, `work`, `locus`, `critical_edition`, `cited_by`, `note`.
- `note` — freeform observation (duplication, mistyping, missing person, etc.). Fields: `text`.

## EDGE TYPES (use only these)
argues_for, argues_against, refutes, responds_to, influences, influenced_by, taught_by, teaches, student_of, belongs_to_school, member_of, has_member, founded, wrote, authored_by, created_by, creates, developed_by, cites, cited_by, source_for, evidenced_by, attested_by, attests, preserves, preserved_in, contains, part_of, translation_of, has_translation, has_section, has_chapter, belongs_to_corpus, discusses, discussed_in, defines, related_to, contrasts_with, parallel_to, employs, presupposes, grounded_in, holds_position, endorses, rejects, supports, critiques, extends, participates_in, contributes_to, interprets, interpreted_by, represents, exemplifies, specializes_in, contemporary_of, precedes, follows, wrote_about, engages_with, cites_primary_source, published, agrees_with, opposes, uses_methodology_of, edited_by, variant_of, has_variant

## Method
- Prefer the `.md`/`.txt` extractions (fast) over PDFs; open the PDF with the `pages` param only for a page-specific quote.
- Be precise and conservative. A smaller set of verified, well-sourced proposals beats a large speculative one.
- End your final message with a short summary: counts per record kind, key duplications found, and anything that needs human judgment.
