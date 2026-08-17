# EleutherIA: A Reproducibly Curated Knowledge Graph of Ancient Debates on Fate, Freedom, and Moral Responsibility

**Romain Girardi**  
CEPAM–UMR 7264, Université Côte d’Azur, Nice, France  
Sole author and corresponding author

**Article type:** Data paper  
**Draft status:** Complete working draft for submission preparation

## Abstract

EleutherIA is an openly licensed knowledge graph, ancient-text corpus, and modern-reception dataset for the history of debates on fate, freedom, agency, and moral responsibility from the sixth century BCE to the sixth century CE. The current snapshot contains 19,994 nodes, 49,391 asserted edges, 21,103 corpus passages, and 19,917 passage-to-graph citations. Its principal methodological contribution is a reproducible curation cycle combining a four-dimensional audit, source-based human adjudication, dated and idempotent repair programs, incident-derived ingestion gates, and stratified post-repair verification. The data are deposited on Zenodo under a CC BY 4.0 licence and are available as JSONL, JSON, BibTeX, and reproducible RDF/SKOS/SHACL exports. Reuse scenarios include source-grounded question answering, historiographical mapping, and the adaptation of the curation workflow to other knowledge graphs in ancient philosophy.

**Keywords:** ancient philosophy; free will; knowledge graph; corpus; data curation; provenance

### Résumé

EleutherIA est un graphe de connaissances sous licence ouverte, associé à un corpus de textes anciens et à une couche de réception moderne, consacré à l’histoire des débats sur le destin, la liberté, l’agentivité et la responsabilité morale, du VIe siècle avant notre ère au VIe siècle de notre ère. L’instantané actuel contient 19 994 nœuds, 49 391 arêtes assertées, 21 103 passages et 19 917 liens de citation entre corpus et graphe. L’apport méthodologique principal réside dans un cycle de curation reproductible : audit selon quatre dimensions, arbitrage humain sur sources, réparations datées et idempotentes, règles d’ingestion motivées par des incidents réels, puis vérification stratifiée. Les données sont déposées sur Zenodo sous licence CC BY 4.0 et diffusées en JSONL, JSON et BibTeX, avec des exports RDF/SKOS/SHACL reproductibles.

**Author contribution (CRediT):** Romain Girardi: Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration; Resources; Software; Validation; Visualization; Writing – original draft; Writing – review and editing.

## 1. Overview

### Repository location

EleutherIA is maintained at <https://github.com/romain-girardi-eng/EleutherIA> and archived under the Zenodo concept DOI <https://doi.org/10.5281/zenodo.17379489> (Girardi, 2026). The repository states a Creative Commons Attribution 4.0 licence. The `v5.2.0` tag names the release “audited and repaired knowledge graph”; this paper describes the corresponding reproducible curation method and the generated snapshot dated 17 August 2026.

At that snapshot, the graph contains 19,994 nodes and 49,391 asserted edges. The corpus mirror contains 21,103 text passages, and 19,917 records link graph claims or entities to passages. The platform catalogue documents 254 ancient works; the generated graph statistics count 249 nodes of type `work`, while 190 works currently have corpus text. These are deliberately distinguished measures: catalogue coverage, graph modelling, and available full text are not interchangeable.

### Context

EleutherIA addresses a scholarly object that is both diachronic and mediated. Ancient arguments about what depends on us, assent, voluntary action, fate, providence, and responsibility extend from Presocratic and Classical Greek materials through Hellenistic schools, Roman philosophy, early Christianity, and Late Antiquity. The relevant evidence is dispersed across direct works, fragments, testimonia, translations, later reports, and modern reconstructions. A single proposition may consequently connect an ancient term, an argument, its author, a surviving witness, a canonical passage, and several incompatible interpretations.

The modern category “free will” also cannot simply be projected backwards as a stable ancient realia. Dihle (1982), Bobzien (1998), and Frede (2011), for example, offer different accounts of when a recognisable notion or problem of the will emerged. Fürst (2022) gives Origen a central place in a longer history of human self-determination. Such disagreements are data, not noise to be resolved in advance. EleutherIA therefore separates a primary layer—ancient persons, works, passages, concepts, and arguments—from a secondary layer of publications, scholars, attributed theses, syntheses, and dialectical relations. The graph form is appropriate because it retains these many-to-many relations while keeping source, witness, interpretation, and disagreement distinct.

The project is FAIR-aligned in concrete rather than merely declarative terms: a persistent DOI and resource identifiers support findability; the repository, API, and open licence support accessibility; Canonical Text Services (CTS) URNs and RDF-compatible identifiers support interoperability; and documentation, source provenance, audit records, and reusable formats support reuse (Wilkinson et al., 2016). FAIR alignment does not certify the truth of every record. It makes claims findable and inspectable, including the claims still marked as debt.

## 2. Method: Construction

### Primary and secondary sources

Ancient text is ingested only from named editions or registered digital witnesses. The source policy prioritises critical editions and records Sources Chrétiennes (SC), GCS, CCSL, PTS, Bibliotheca Teubneriana, Loeb, and, as a fallback, PG/PL. The working corpus also uses a local TLG E collection, Perseus/Scaife material, and Open Greek and Latin/First1KGreek where the provenance record identifies the witness. SC volumes are particularly important for Origen and other patristic sources. A passage carries a human-readable canonical reference and, where available, a CTS URN; edition information belongs in provenance rather than being guessed from the identifier. Corpus text has an NFC-normalised SHA-256 integrity contract so that silent changes can be detected without treating canonically equivalent Unicode encodings as different texts.

Modern scholarship is modelled as scholarship rather than as direct ancient evidence. Publication nodes may be connected to scholar nodes, attributed argument nodes, ancient sources discussed, concepts, and other scholarly positions. Bibliographic records and OCR-derived working texts remain distinguishable: the tracked scholarly-source manifest records edition and hash information, while copyrighted OCR files are not part of the public repository. This enables another curator to locate or reproduce the working witness without presenting the OCR archive as openly redistributable data.

The reception layer also federates records from the separate Origenality bibliography. Its import policy is intentionally conservative. A newly imported publication receives `citation_verdict: bibliographic_import` and the source-rank statement “unread bibliographic record imported from the Origenality federation—metadata verified against the source catalogues, content not yet read.” Donor abstracts retain their source, rights statement, and URL. The importer does not turn a catalogue record or abstract into a scholarly thesis; it creates no person where authorship cannot be matched unambiguously, and it leaves incomplete identities in a review queue. The current graph contains 198 records bearing the `bibliographic_import` verdict.

### Ontology and semantic layer

The JSON ontology defines 24 node types, of which 16 occur in the current snapshot, and 77 edge types, of which 54 occur. Every edge-type definition declares an inverse. Since storing both directions as independent assertions caused metadata drift, the asserted snapshot now keeps one canonical direction and derives its inverse at load or inference time. Relations cover structural, authorship, citation, argumentative, intellectual, temporal, hermeneutic, affiliation, doctrinal, debate, semantic, and textual functions.

Historical periods and schools are versioned rather than left as uncontrolled strings. The period and school concept schemes are both version 1.0.0, issued on 17 August 2026. They retain 15 period labels and 18 school or intellectual-tradition labels. Together they form 33 controlled concepts in the SKOS export, with preferred labels, definitions, scope notes, notations, and, for periods, explicit date bounds. The schemes acknowledge overlap: “Patristic” is an intellectual-historical category, for instance, while “Roman Imperial” and “Late Antiquity” are chronological categories.

The semantic layer is a read-only derivative of the asserted data. It maps project classes and properties to RDF, CIDOC CRM, FOAF, Dublin Core Terms, BIBO, PROV-O, SKOS, CiTO, and Wikidata identifiers where applicable. The exporter produces Turtle, JSON-LD, and N-Triples. SHACL is divided into blocking invariant shapes and non-blocking quality shapes: the first protect graph validity, while the second expose incomplete scholarly work as a curation backlog (Knublauch & Kontokostas, 2017). Restricted OWL-RL processing derives inverses and selected transitive relations, and proof-chain records can state which asserted triples and inference rule support a derived fact.

### Ingestion pipeline

The release mirror is built from line-oriented JSON records for nodes, edges, passages, citations, and manifests; the operational services load and query these data through PostgreSQL and FastAPI. A proposed ingestion is assembled as a delta, checked before writing, applied through a dated script, and followed by regenerated statistics and derived exports. CTS URNs supply machine-actionable textual loci, while `canonical_ref` stores the concise citation form used by scholars (CITE Architecture, n.d.).

The ingestion gate is not a generic checklist detached from experience. Its rules were named after defects actually found in EleutherIA. The current sequence is numbered R1–R18, with an additional R3b and no R6 in the published rule table: R1 provenance; R2 identity and deduplication; R3 one work, one canonical text; R3b canonical work identifier; R4 passage authorship not inherited from a container; R5 resolvable CTS URNs; R7 genuine translations; R8 sourced scholarly claims; R9 honest identifiers; R10 no invented years; R11 and R12 edge ontology and endpoint hygiene; R13 chronology; R14 no orphan additions; R15 identifier-prefix consistency; R16 attested dialectical relations; R17 one asserted direction per inverse pair; and R18 controlled period and school vocabularies. A blocking failure prevents the delta from being written. A warning remains a decision that must be recorded, not an automatic pass.

## 3. Method: Quality Assurance

### Four-dimensional audit

The audit of 16 August 2026 separates four dimensions so that different failure mechanisms do not collapse into one undifferentiated “quality” score. Structural checks concern identity, types, edge endpoints, orphans, duplicates, and contradictory containers. Linguistic checks detect OCR corruption, mixed scripts, false translations, language-label conflicts, broken encoding, and suspect textual identifiers. Bibliographic checks examine author and year identity, work shells, BibTeX coverage, CTS format and locus reuse, dangling references, quotation verification, and whether prose claims have machine-traversable citations. Semantic checks inspect duplicate or overlapping theses, work and publication duplication, vocabulary drift, category errors, and unjustified dialectical edges.

The four named JSONL files contain a reproducible total of 5,421 line-level findings: 41 structural, 1,589 linguistic, 3,683 bibliographic, and 108 semantic records (Table 1). Equally importantly, a “finding” is a detector or review item, not necessarily a confirmed error. The audit itself contains false-positive classes, and several apparently serious flags were overturned by inspection of the printed or local source.

**Table 1. Findings in the four-dimensional deep-audit corpus.**

| Dimension | Records | Principal scope |
|---|---:|---|
| Structural | 41 | identity, types, graph integrity, duplicates, orphans |
| Linguistic | 1,589 | OCR, script, encoding, language, translation status |
| Bibliographic | 3,683 | identifiers, loci, references, citation materialisation |
| Semantic | 108 | thesis duplication, vocabulary, relation meaning |
| **Total** | **5,421** | line-level findings before source-based adjudication |

### Repair as a replayable scholarly operation

Findings were not bulk-rewritten. Repair waves were documented in dated plans, tested first in dry-run or disposable copies, and recorded in corresponding applied reports where an application occurred. The procedure treats a correction as a small scholarly argument:

1. a data module states the intended item-level change and its evidence;
2. an applier rereads the live record and checks declared preconditions rather than writing blindly;
3. invariant checks reject duplicate identifiers or triples, dangling endpoints, split `source`/`source_id` or `target`/`target_id` fields, and invalid pointers;
4. a wave-specific stamp makes a second execution a no-op;
5. backups are made before atomic replacement and are not overwritten by reruns; and
6. the applied report preserves counts, changed identifiers, deferred items, and the evidence trail.

This approach supports both positive and negative decisions. A candidate may be corrected, merged, retyped, removed, flagged for review, or deliberately left untouched because the necessary source is absent. For example, the Methodius re-ingestion plan found that the required TLG 2959 source files were unavailable; 82 candidates were stamped as blocked in the sandbox verification, while zero descriptions were rewritten. The absence of a witness thus remains visible instead of being filled with a conjectural text.

### Anti-fabrication and textual verification

EleutherIA’s authenticity policy prohibits composed, reconstructed, completed, or paraphrased ancient Greek and Latin from being presented as source text. When an ancient-language text cannot be verified, the permitted substitute is an explicit English paraphrase. The repository gate scans Greek runs in graph descriptions and requires attestation in the corpus, an adjudicated allowlist with provenance, or the local TLG E corpus. An attestation found only in TLG E is not silently accepted: it must be added with edition provenance.

Answer-time verification uses a separate deterministic text verifier. It first compares an ancient-language span against the evidence retrieved for that query using Unicode-, accent-, final-sigma-, punctuation-, and word-boundary-aware matching. Residual spans trigger a bounded corpus probe. Unverified lines are removed by default and the decision is recorded with a reason such as `unattested` or `reference-mismatch`. The gate verifies fidelity to an available witness; it does not decide between critical editions.

### Verification of the dialectical layer

The audit gave special attention to relations such as `opposes`, `agrees_with`, and `critiques`, because these edges make claims about what a scholar holds. Before repair, the complete populations then measured for `opposes` (14 edges) and `agrees_with` (13 edges) contained clear-error rates of 14.3% and 23.1%, respectively. All measured errors came from one ingestion batch, none carried `attested_by`, and every sampled edge that did carry such evidence was correct. Subsequent reading also found an error missed by the mechanical audit: an `agrees_with` edge whose printed source, Salles (2005, pp. 78–81), argued against the recorded target thesis.

The response was not to ban dialectical modelling, but to raise its evidential threshold. R16 now blocks a new dialectical edge unless `metadata.attested_by` names a page or locus. The repair plan reread the nodes and the scholar’s text where available, distinguished explicit criticism from mere propositional tension, and allowed honest statuses such as “unverified” where a source could not be consulted. This matters for a status quaestionis graph: apparent contradiction may disappear when each edge is restricted to the proposition actually attested.

### Stratified post-repair verification

A second exercise measured textual fidelity after the repair waves. A deterministic SHA-256 ordering with seed 20260817 selected 160 passages—40 from each of four ingestion strata—out of approximately 14,900 eligible records. Each JSONL result records the sampled identifier, authority path and locator, comparison method, normalised edit distance, character error rate (CER), and verdict. Wilson 95% confidence intervals were calculated for the mechanically classified substantive-error proportion.

**Table 2. Raw mechanical verdicts by ingestion stratum.**

| Stratum | n | EXACT | MINOR | SUBSTANTIVE | INDISPO (source unavailable) | Wilson 95% CI (substantive) | Median CER |
|---|---:|---:|---:|---:|---:|---|---:|
| SC-series OCR | 40 | 15 | 25 | 0 | 0 | [0.0% ; 8.8%] | 0.0% |
| TLG E realignments | 40 | 5 | 15 | 20 | 0 | [35.2% ; 64.8%] | 1.1% |
| Perseus/web | 40 | 0 | 9 | 12 | 19 | [18.1% ; 45.4%] | 1.8% |
| First1KGreek | 40 | 0 | 3 | 37 | 0 | [80.1% ; 97.4%] | 21.0% |

The raw table cannot be read as four error rates. In the SC stratum, all 40 authorities were the same files used for ingestion; zero substantive differences therefore demonstrate extraction fidelity, not independent editorial correctness. The TLG stratum mixed two populations. Seventeen *Magna Moralia* text re-ingestions produced no substantive difference after inspection, whereas 20 of 23 sampled Plotinus records were mechanically classified as substantive even though their median CER was only 1.1%. Human inspection identified edge truncation and Perseus/TLG edition variants rather than corruption of the text body. In the Perseus/web stratum, 19 sources were locally unavailable; the remaining raw differences broadly reflect inter-edition variance, with one outlier requiring item-level review. In the First1KGreek stratum, modern curated extracts were compared with larger TLG citation blocks. The resulting span misalignment dominated the distance measure; the stratum is non-conclusive until passages are re-collated with aligned spans.

This critical reading preserves a necessary distinction between **fidelity** and **correctness**. A byte-faithful ingest can reproduce a poor or non-independent witness. Conversely, a high edit distance may measure two differently bounded but overlapping passages rather than a corrupt transcription. The sample is also small relative to the eligible population; even the zero-observation SC result retains an upper Wilson bound of 8.8%. The base-letter Levenshtein method cannot itself distinguish copying error from edition variance, and the report was finalised from intact JSONL records after the producing job was interrupted. The seed and unit records make the sample replayable, but they do not remove these inferential limits.

## 4. Dataset Description

### Repository name and objects

The repository and dataset are both named **EleutherIA**. The principal citable objects are:

- `data/kg/nodes.jsonl` and `data/kg/edges.jsonl`: asserted graph records;
- `data/corpus/passages.jsonl`, `citations.jsonl`, and `manifest.jsonl`: the text mirror, passage-to-graph links, and corpus manifest;
- `knowledge graph/ontology/*.json`: node types, edge types, and controlled period and school schemes;
- `knowledge graph/src/eleutheria_kg/semantic/shapes/**/*.ttl`: SHACL invariant and quality shapes;
- `data/kg/publications.bib`: reusable modern bibliography;
- `data/audit/*.jsonl` and `*.md`: machine-readable findings, plans, unit verdicts, and narrative adjudication reports; and
- the semantic exporter, which reproducibly serialises the graph as Turtle, JSON-LD, and N-Triples with SKOS concepts and provenance mappings.

JSONL is used for large append-friendly record collections; JSON is used for ontologies, schemes, manifests, and structured reports; Turtle expresses SHACL and RDF artefacts; Markdown records human-readable decisions; and BibTeX supports bibliographic reuse. The API exposes works, passages, search, graph nodes and edges, neighbours, statistics, communities, centrality, paths, timelines, and source-grounded GraphRAG queries.

### Creation dates, creator, language, licence, and publication date

EleutherIA is an evolving dataset. This paper reports the snapshot generated on 17 August 2026 and the audit-and-repair cycle dated 16–17 August 2026. The dataset creator is Romain Girardi, CEPAM–UMR 7264, Université Côte d’Azur. Ancient-text fields include Greek and Latin; the corpus and descriptive graph layers also contain English and other modern-language material where the source or reception record requires it. The repository licence is CC BY 4.0. The Zenodo concept record is cited as a 2026 publication.

### An honesty vocabulary for incomplete knowledge

The dataset avoids reducing heterogeneous epistemic states to a single Boolean “verified” field. Current `citation_verdict` values include `verified`, `corrected`, `false_positive_attested`, and `bibliographic_import`. The last means that bibliographic metadata has been checked against donor catalogues but the publication’s content has not been read; it must not be treated as support for an attributed thesis. `false_positive_attested` records that a detector raised a concern later disconfirmed by a witness. `corrected` preserves the history that verification required a change.

Likewise, `needs_*` metadata exposes work still owed, including edition metadata, evidence notes, page verification, dates, text ingestion, translations, PDF verification, scholarly splitting, and canonical identifiers. These flags are visible research debt. They allow downstream systems to filter, rank, or display uncertainty without deleting a potentially useful record or representing it as complete.

## 5. Reuse Potential and Limitations

The graph can support source-grounded retrieval and GraphRAG question answering because passages, claims, publications, and relations can be traversed together while keeping primary text distinct from modern interpretation. A question about Chrysippus, for example, can retrieve an ancient witness, the argument reconstructed from it, modern positions by Bobzien or Frede, and explicit relations of agreement or criticism—provided each layer meets its own evidence standard.

A second reuse is the construction of dynamic *status quaestionis* instruments. Researchers can compare attributed positions, locate where a disagreement is explicit rather than inferred, and identify which claims have page-level attestation. Because dialectical relations carry propositions and evidence, a graph view can reveal not merely that two scholars “disagree” but the restricted point on which they do.

A third reuse lies in method transfer. Other projects in ancient philosophy, patristics, or the history of concepts can adapt the incident-to-rule pattern: convert a discovered defect into a named gate, preserve the detector output, make corrections replayable and conditional, and measure the result with a sampling design whose limitations are published alongside its estimates. The method does not require EleutherIA’s exact ontology.

Reuse must nevertheless account for four limitations. First, coverage is asymmetric: the 254-work catalogue, 249 graph work nodes, and 190 works with text show that bibliographic presence, graph representation, and passage availability differ. Second, 198 Origenality imports are explicitly unread bibliographic records; their metadata and donor abstracts support discovery, not content-level claims. Third, source-blocked items remain visible, as in the Methodius case, rather than being completed conjecturally. Fourth, the stratified verification measures witness fidelity under a specific alignment procedure, not universal philological correctness. SC comparisons were not independent; many Perseus/web authorities were unavailable locally; and First1KGreek requires span-aligned re-collation. Users should therefore propagate provenance and debt flags into any analysis rather than interpreting openness, graph connectivity, or a successful string match as a guarantee of historical truth.

## Acknowledgements

[To be completed by the author.]

## Funding statement

[To be completed by the author.]

## Competing interests

[To be confirmed by the author before submission.]

## Data accessibility statement

The EleutherIA dataset is openly available from Zenodo at <https://doi.org/10.5281/zenodo.17379489> and from the public repository at <https://github.com/romain-girardi-eng/EleutherIA>. The deposited data are licensed under CC BY 4.0. The tracked modern-scholarship manifest identifies locally held OCR witnesses, but the copyrighted OCR files themselves are not redistributed.

## References

Bobzien, S. (1998). *Determinism and freedom in Stoic philosophy*. Oxford: Clarendon Press.

CITE Architecture. (n.d.). *Canonical Text Services URN syntax*. <http://cite-architecture.github.io/ctsurn_spec/>.

Dihle, A. (1982). *The theory of will in classical antiquity* (Sather Classical Lectures 48). Berkeley, Los Angeles, and London: University of California Press.

Frede, M. (2011). *A free will: Origins of the notion in ancient thought* (A. A. Long, Ed.; Sather Classical Lectures 68). Berkeley, Los Angeles, and London: University of California Press.

Fürst, A. (2022). *Wege zur Freiheit: Menschliche Selbstbestimmung von Homer bis Origenes* (Tria Corda 15). Tübingen: Mohr Siebeck. <https://doi.org/10.1628/978-3-16-161657-0>.

Girardi, R. (2026). *EleutherIA: An AI-powered scholarly research platform for ancient philosophy on free will* [Dataset and software]. Zenodo. <https://doi.org/10.5281/zenodo.17379489>.

Knublauch, H., & Kontokostas, D. (Eds.). (2017). *Shapes Constraint Language (SHACL)*. W3C Recommendation. <https://www.w3.org/TR/shacl/>.

Miles, A., & Bechhofer, S. (Eds.). (2009). *SKOS Simple Knowledge Organization System reference*. W3C Recommendation. <https://www.w3.org/TR/skos-reference/>.

Salles, R. (2005). *The Stoics on determinism and compatibilism*. Aldershot: Ashgate.

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. <https://doi.org/10.1038/sdata.2016.18>.
