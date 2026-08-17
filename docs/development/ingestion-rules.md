# Ingestion rules

Rules for creating nodes in `data/kg/`. Enforced by
`scripts/check_ingestion_rules.py`, not by good intentions.

Every rule exists because the defect it forbids was found in this graph, and the
rule text names the incident. That is the point: this is a list of the ways this
project has actually gone wrong, turned into code.

```bash
python3 scripts/check_ingestion_rules.py                # debt report on the whole graph
python3 scripts/check_ingestion_rules.py --new-only D    # gate a proposed delta — exits 1 on BLOCK
```

`--new-only` takes `{"nodes": [...], "edges": [...]}` of what you intend to add.
**An ingestion script must call it and refuse to write if it fails.** See
`scripts/ingest_2026_08_17_jurasz_bardaisan.py` for the pattern.

`BLOCK` stops the ingestion. `WARN` is a decision you have to make and record —
it is not a free pass, and it is never silently cleared.

---

## The rules

| Rule | Level | Requirement | The incident behind it |
|------|-------|-------------|------------------------|
| **R1** provenance | BLOCK | Every new node carries `metadata.provenance.source` — a DOI, ISBN, CTS URN or on-disk path — plus `ingested_at` and `ingest_script`. | Waves created nodes leaving no trace of where the claim came from, so later audits could not separate fact from guess. |
| **R2** identity | BLOCK | Compute the identity key and search first. If a node holds that key, **attach to it**. Never create a second one. | `pub_long_1996` vs `scholarly_work_long_1996` (a merge recorded in metadata but never executed); Crouzel 1962 forked by accent-slugging; Jewett 2007 twice; two work nodes for the Book of the Laws of the Countries. |
| **R3** one work, one text | BLOCK | A `work` node holds passages of exactly one canonical work. | Eleven work nodes held 30+ works and ~3,350 misfiled passages: Seneca's *Letters* (2,135) under *De Providentia*, Plato's *Apology* under the *Republic*, Epicurus under Epictetus. |
| **R3b** canonical id | WARN | A `work` should carry `cts_urn` or `work_canonical_id`. | Without one, a work can only be deduplicated by title — which is how Clement's *Protrepticus* (51 passages) ended up inside Origen's *Exhortation to Martyrdom*. Both are "Exhortation". |
| **R4** author not inherited | BLOCK | A passage's author is read from its own source, never from its parent work. | 190 passages took their host work's author; 115 of Gregory of Nazianzus were attributed to Augustine. |
| **R5** resolvable URN | BLOCK / WARN | No placeholder (`?`, `TODO`, `unknown`) in a CTS URN (BLOCK); URN matches the grammar (WARN). | 445 Plato passages carried a literal `?`, making the project's own FAIR identifiers unresolvable. |
| **R7** real translations | BLOCK | A node with `passage_role: translation` must resolve `original_node_id` and its text must **differ** from the original. | 340 nodes declared `language: eng` while their text was byte-identical to the Greek or Latin original. The reader was served Latin labelled as English. |
| **R8** sourced claims | BLOCK / WARN | A `scholarly_argument_*` needs a resolving publication reference and a scholar; `page_range` is a WARN. Metadata pointers must resolve. | 73 pointers referenced 11 ids that no longer existed; 81 arguments record their publication under `e2_publication_id` instead of `scholarly_work_id`. |
| **R9** honest ids | WARN | The surname in an id must match a scholar the node is actually attributed to. | 19 ids named the wrong scholar — Gourinat for D'Jeranian, Guyomarc'h for Koch, Cross for Hyatt, Crouzel for Simonetti. |
| **R10** no invented years | BLOCK | Never guess a year. Resolve it against the print, or omit it and set `grey_literature` with a reason. The id year and `metadata.year` must agree. | Ten ids used a `_0_` placeholder; seven embedded a year contradicting their own metadata. |
| **R11/R12** edge hygiene | BLOCK | Relation exists in the ontology, source/target types are allowed, `source == source_id`, `target == target_id`, no self-loops. | Six edges had `target != target_id`: the in-memory loaders and the SQL k-hop CTE returned **different authorship** for the same edge. |
| **R13** chronology | WARN | Directional intellectual relations must respect dates. | Eleven edges said Calvin influenced Augustine, Lucretius influenced Epicurus, Boethius influenced Aristotle. |
| **R14** no orphans | BLOCK | A new node must have at least one edge. | A verified 1,265-word Hegesippus fragment sat with zero edges, unreachable from every retrieval path. |
| **R15** id prefix | WARN | The id prefix must match the node type. | A `work` node under a `passage_` prefix; 22 `argument` nodes under a `scholar_` prefix colliding with the person namespace. |
| **R16** attested dialectic | BLOCK / WARN | Every relation rendered as a Scholar-RAG fault line — `opposes`, `critiques`, `responds_to`, `refutes`, `contrasts_with`, `agrees_with`, `supports` — must carry non-empty `metadata.attested_by` with its page or locus. New edges are BLOCK; existing ones are retained and counted as WARN debt by relation. The gate and frame builder import the same relation constant. | Every measured error in the dialectical layer came from an unattested batch. The original audit covered `opposes`, `agrees_with`, `critiques`; the cold audit then found that `responds_to`, `supports`, and `contrasts_with` could enter the same prose without passing R16. |
| **R17** one inverse direction | BLOCK / WARN | Assert one canonical direction only; `--new-only` blocks an edge whose declared inverse is already materialized, while the whole-graph audit warns on residual pairs. | The 2026-08-17 inverse normalization found 4,692 twin pairs whose independently maintained metadata had begun to drift; loaders and OWL inference now derive the inverse. |
| **R18** controlled vocabularies | BLOCK / WARN | Every non-null `period` and `school` on a new node must be a retained `prefLabel` in `knowledge graph/ontology/period_scheme.json` or `school_scheme.json` (BLOCK). Whole-graph mode groups and reports each off-scheme value with its count and examples (WARN). | The semantic audit found a stale period list and 25 school values, including `None (doxographer)`, a period copied into `school`, split Cappadocian labels, and the `Apologetic` / `Christian Apologetics` duplicate. The versioned schemes now follow the graph's 15 real periods and the evidence-backed school cleanup. |

---

## Identity keys (R2)

Identity differs by type, so the dedup key does too:

- **work** — `cts_urn` or `work_canonical_id`; falling back to author + normalised title, which is deliberately weak (see R3b).
- **publication** — DOI if present, else `(author_id, year, normalised title)`.
- **person** — the ordered, accent-stripped name. Order matters: *Martin Luther* is not *Luther H. Martin*.
- **passage** — `(cts_urn, passage_role)`. The role is part of the key because a translation legitimately shares its original's URN.

---

## Rules that no checker can enforce

These are on you.

- **Never generate ancient Greek or Latin.** Copy verbatim from a named critical edition on disk or in the corpus, or write English instead. Plausible-looking generated Greek in a scholarly database is fraud, not a shortcut. `check_greek_gate.py` catches unattested runs; it cannot catch a plausible fabrication that happens to exist elsewhere.
- **Record disagreement as disagreement.** When your source reports that scholars disagree, create both positions and the edge between them. Do not resolve the dispute yourself and store the winner. The Jurasz ingestion models this: Jurasz accepts Eusebius of Emesa's attribution to Bardaisan, ter Haar Romeny rejects it, and both nodes exist.
- **Attribute the claim to whoever makes it.** A `scholarly_argument` records what a modern scholar says, not what is true, and not what the ancient author says.
- **Match works by canonical id or by text, never by title.** Two different works share a title more often than intuition suggests.
- **When you are unsure, do not write.** An absent node costs nothing. A wrong one is copied into an answer, cited, and believed.

---

## Known debt

The whole-graph run reports pre-existing violations and exits 0 by design — the
rules are stricter than the history. Use `--strict` to fail on them. Current
debt worth naming:

- **~2,774 passage nodes share a locus with another node** (661 groups). Not plain duplicates: one node holds the primary text, the other an English editorial summary — but both are typed `passage` with the same CTS URN, so a summary can be cited as if it were the ancient author. Needs classification, not a mechanical merge.
- **40 translation nodes** have no resolvable `original_node_id`.
- **201 works** have no canonical id (R3b).
- **81 arguments** use the `e2_publication_id` / `page_or_loc` schema instead of the canonical field names.
- **940 school assignments are intentionally still off-scheme in the dry-run deliverable state**: 931 `Apologetic` passages plus nine person records covered by eight rare source values. `scripts/apply_2026_08_17_vocab_freeze.py` simulates their normalization; no canonical KG data is changed by the vocabulary-freeze deliverables themselves.
