# EleutherIA Methodology Paper Draft

Working target: Digital Scholarship in the Humanities, Open Humanities Data, or
Journal of Open Humanities Data.

## Title

FAIR Knowledge Graphs and Neurosymbolic GraphRAG for Verifiable Ancient
Philosophy: The EleutherIA Corpus on Fate, Agency, and Moral Responsibility

## Abstract

EleutherIA is a FAIR-aligned digital humanities infrastructure for studying
ancient debates about fate, agency, moral responsibility, and what later
traditions call free will. The project combines a curated knowledge graph, a
multi-source Greek and Latin corpus, RDF/OWL/SHACL semantic publication, and a
citation-grounded GraphRAG interface. This paper describes the methodological
problem addressed by the platform: claims about ancient free will are not
atomic facts but historically mediated reconstructions grounded in passages,
editions, translations, fragments, and modern scholarship. We present a data
model that separates ancient persons, works, passages, arguments, concepts,
publications, textual variants, and argument reconstructions; a provenance
policy that distinguishes original text, translation, and paraphrase; and a
validation stack that turns philological quality expectations into auditable
SHACL reports. The contribution is not a replacement for expert judgment, but a
reproducible substrate where scholarly disagreement, source uncertainty, and
evidence anchoring can be inspected, queried, and versioned.

## 1. Research Problem

Ancient discussions of fate and responsibility are distributed across complete
works, fragmentary testimonia, hostile reports, doxographical summaries,
translations, commentaries, and modern reconstructions. A computational system
that treats every relation as equally direct misrepresents this evidence. A
Stoic argument preserved in Cicero, for example, is not identical to an
argument written by Chrysippus; it is an argument reconstructed through a
Latin Academic source. Likewise, an English translation of Aristotle is not an
original Greek witness for linguistic analysis.

The central methodological claim of EleutherIA is therefore that retrieval
quality depends on formalizing philological distinctions before applying neural
retrieval or graph analytics. The graph must know whether a node is an ancient
work, a passage, a translation, a modern publication, a textual variant, or a
polemical reconstruction. The system must expose missing evidence as debt
rather than hide it behind high-level summaries.

## 2. Corpus and Coverage

The corpus target is broad coverage of Greek, Latin, and early Christian
sources relevant to fate, providence, voluntariness, assent, choice, grace, and
responsibility. Perseus/Scaife CTS remains one source, but EleutherIA now treats
it as one loader among several rather than a single point of failure. Latin
works can be restored from PHI Latin Texts, authorized institutional Greek
corpora can be loaded through JSON mirrors, and patristic texts can be tied to
traceable editions or scans.

Coverage is treated as a first-order scholarly metric. A methodology paper or
thesis chapter must report corpus counts, source distribution, language
distribution, and passage-role distribution. The corpus restoration runbook
defines the target baseline, fallback source order, and validation commands.

## 3. Knowledge Graph Model

The graph distinguishes the following scholarly entities:

- `person`: ancient authors, modern scholars, and editors when needed.
- `work`: ancient works, collections, and source corpora.
- `passage`: cited units of original text, translation, or paraphrase.
- `argument`: philosophical claims or argument structures.
- `concept`: technical vocabulary and analytic concepts.
- `publication`: modern books, articles, editions, and datasets.
- `textual_variant`: apparatus criticus entries tied to a passage.
- `argument_reconstruction`: a source-mediated reconstruction of one argument
  by another source.

Edges such as `evidenced_by`, `part_of`, `authored_by`, `variant_of`,
`reconstructs`, and `reconstructed_from` preserve the difference between direct
evidence, containment, authorship, textual tradition, and argumentative
mediation.

## 4. Philological Provenance

Each passage should carry `passage_role`:

- `original`: source-language text usable for linguistic analysis.
- `translation`: a translation linked to a source passage.
- `paraphrase`: a non-verbatim interpretive summary.

Edition metadata is stored as structured records on work and passage nodes. For
ancient sources, the minimum target is editor, series or publisher, year, and
identifier where available. For modern publications, the minimum BibTeX target
is author, title, year, and publication type, with DOI or ISBN when known.

Textual variants are modeled explicitly rather than hidden in prose notes. A
variant node records lemma, principal reading, alternative readings, manuscript
or source labels, and critical source. This matters especially for fragmentary
Stoic material, Origen, Boethius, Tertullian, and Cicero's *De Fato*.

## 5. Evidence Anchoring

Automated linking is useful for triage, but not sufficient for a defensible
scholarly graph. EleutherIA therefore separates invariant validation from
scholarly quality warnings. Arguments flagged as needing evidence remain in the
quality backlog until a reviewer identifies a passage, adds an `evidenced_by`
edge, and records a confidence level. The intended workflow is thematic review:
Augustine on grace and will, Stoic fate and assent, Aristotle on voluntary
action and akrasia, Epicurean swerve, Academic anti-fatalism, and late antique
providence.

Confidence above 0.9 is reserved for direct textual support, not broad
interpretive plausibility. Lower confidence may be valid, but it must be
visible.

## 6. Uncertainty and Reconstruction

Dates and attributions are not always point facts. Person and work metadata can
therefore include `date_uncertainty` records with best estimate, lower and upper
bounds, confidence, and source. This allows chronological queries to include or
exclude uncertain entities explicitly.

The `argument_reconstruction` type records mediated arguments: for example, an
anti-Stoic argument as reconstructed by Cicero, or a Stoic response as reported
by a hostile source. A fidelity score records how directly the source preserves
the target argument.

## 7. Semantic Publication

EleutherIA publishes a derived RDF graph from the canonical JSONL snapshot. RDF
export normalizes stringified metadata, emits typed nodes and object
properties, and surfaces philological fields such as passage role, edition
metadata, date uncertainty, DOI, ISBN, variant lemmas, and reconstruction
fidelity. SHACL shapes are split into:

- invariant shapes, which block CI when domain/range constraints fail.
- quality shapes, which produce warnings for scholarly backlog management.

The public SPARQL sidecar loads the Turtle dump through Fuseki, allowing a
reviewer to reproduce tables with short queries rather than relying on prose
description.

## 8. GraphRAG Interface

The GraphRAG layer is constrained by the graph rather than allowed to invent
citations. Retrieval can combine lexical search, graph neighborhoods, and proof
chain rendering, but answers must surface passages and relations. This is a
neurosymbolic design in a modest sense: neural ranking helps navigate the
archive, while symbolic edges, SHACL constraints, and provenance metadata define
what counts as admissible support.

## 9. Reproducibility

Releases are frozen through Zenodo version DOIs under a stable concept DOI. A
thesis citation should identify the exact version DOI, Git commit, KG snapshot
date, and checksums for `nodes.jsonl`, `edges.jsonl`, RDF Turtle, and BibTeX.
GitHub Actions validates SHACL invariants on pull requests and validates nightly
KG snapshots before committing them.

## 10. Limitations

EleutherIA does not automate philology. It exposes where philological work is
missing. It also does not collapse ancient and modern free-will vocabulary into
a single ahistorical concept. The model is deliberately plural: `to eph hemin`,
`prohairesis`, `assensus`, `liberum arbitrium`, divine grace, providence, and
fate are related but not identical.

## 11. Contribution

The contribution is an open, versioned, queryable research infrastructure for a
domain where scholarly evidence is dense, multilingual, and tradition-mediated.
The system demonstrates that GraphRAG for historical philosophy is only
defensible when it is anchored in corpus coverage, edition metadata, explicit
uncertainty, argument reconstruction, textual variants, and machine-checkable
quality gates.
