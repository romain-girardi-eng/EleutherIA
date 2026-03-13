# KG Quality Audit

Generated: 2026-03-10T17:42:36.173338+00:00

## Snapshot

- Audited live PostgreSQL KG, not a checked-in export.
- Nodes: 17396
- Edges: 42161
- Passage citations: 13293
- Claim-bearing nodes audited for provenance risk: 410

## What Is Already Clean

- Orphan edges: 0
- Orphan passage citations: 0
- Isolated / no-edge nodes: 3
- Duplicate edge triples: 0
- Self-loops: 0

## Priority Fixes

1. Provenance gaps: 69/410 (16.8%) claim-bearing nodes have no passage citation, no evidence relation, and no direct passage edge.
2. Unsupported-claim candidates: 30/410 (7.3%) claim-bearing nodes still use assertive language despite lacking any evidence anchor.
3. Ontology drift: 0 live relations are missing from the ontology, and 3 edges violate the current relation type constraints.
4. Thin node records: 11 nodes have empty metadata and 0 nodes have no description at all.
5. Incomplete authorship / structure: 14 work nodes, 34 publication nodes, 2 quote nodes, and 62 passage nodes lack `authored_by`.
6. Formatting drift: 167 non-passage node descriptions contain markdown or list markup, and 56 passage labels still expose importer-style `chap.: / par.: / verset.:` strings.

## Provenance / Hallucination Risk

- Heuristic used here:
  A node is flagged when it is a claim-bearing type and has zero passage citations, zero `evidenced_by` / `source_for` / `grounded_in` relations, and zero direct graph edges to passage nodes.
- Higher-risk subset:
  Same rule as above, plus assertive wording in the description (`argues`, `shows`, `foundational`, `central`, etc.).

- Claim nodes without any evidence anchor: 69
- `argument`: 39
- `concept`: 18
- `controversy`: 5
- `school`: 3
- `debate`: 2
- `group`: 2

- Assertive claim candidates without evidence: 30
- `argument`: 21
- `concept`: 5
- `controversy`: 2
- `school`: 2

- Representative assertive examples:
- type=argument, period=Early Modern, label=Cartesian Dualism and Agent Causation, node_id=argument_cartesian_dualism_and_agent_causation_b637cc75
- type=argument, period=Early Modern, label=Conatus Doctrine, node_id=argument_conatus_doctrine_1588d13c
- type=argument, period=Early Modern, label=Erasmus's Defense of Free Will, node_id=argument_erasmian_free_will_7s1n2o80
- type=argument, period=Early Modern, label=Hobbes's Rejection of Immaterial Soul, node_id=argument_hobbess_rejection_of_immaterial_soul_02b7bcda
- type=argument, period=Early Modern, label=Human Will Lacks Efficacy, node_id=argument_human_will_lacks_efficacy_45522d03
- type=argument, period=Early Modern, label=Infinite Will Argument, node_id=argument_infinite_will_argument_f19a66ed
- type=argument, period=Early Modern, label=Liberty as Absence of External Impediment, node_id=argument_liberty_as_absence_of_external_impediment_4587b29b
- type=argument, period=Early Modern, label=Locke's Analysis of Freedom, node_id=argument_lockean_analysis_2x6s7t35
- type=argument, period=Early Modern, label=Locke's Suspension of Desire, node_id=argument_lockes_suspension_of_desire_e45dc337
- type=argument, period=Early Modern, label=Molinism and Middle Knowledge, node_id=argument_molinism_and_middle_knowledge_3d718eca
- type=argument, period=Early Modern, label=Reid's Agent Causation Argument, node_id=argument_reidian_agent_causation_4z8u9v57
- type=argument, period=Early Modern, label=Spinoza's Free Man Ethics, node_id=argument_spinozas_free_man_ethics_b0940e69

## Ontology Drift

- Live relations missing from `kg/ontology/edge_types.json`:
- None

- Invalid relation/type combinations:
- `source_for` from `source_collection` -> `person`: 2
- `part_of` from `work` -> `source_collection`: 1

- Invalid period labels:
- `Imperial`: 6488
- `Classical`: 2059
- `Early Christian`: 931
- `Late Republic`: 472

## Thin / Incomplete Nodes

- Nodes with empty metadata: 11
- `debate`: 6
- `school`: 3
- `person`: 2

- Nodes without description: 0

- Nodes with null period: 30
- `passage`: 25
- `conceptual_evolution`: 3
- `source_collection`: 1
- `work`: 1

- Weakly connected nodes (degree 1-2): 10924
- `passage`: 10666
- `person`: 98
- `publication`: 59
- `concept`: 40
- `work`: 32
- `argument`: 15
- `quote`: 4
- `synthesis`: 3

## Authorship / Structure Gaps

- Work nodes missing `authored_by`: 14/144 (9.7%)
- Publication nodes missing `authored_by`: 34/81 (42.0%)
- Quote nodes missing `authored_by`: 2/14 (14.3%)
- Passage nodes missing `authored_by`: 62/16540 (0.4%)
- Passage nodes missing `part_of`: 6/16540 (0.0%)
- Translation integrity: 2952 English passage nodes, 0 missing `translation_of`, 0 source nodes incorrectly using `translation_of`.

- Representative missing authorship examples:
- label=Il volontario e la scelta in Aspasio, node_id=pub_alberti_1999_aspasius
- label=Fatalisme et liberté dans l'antiquité grecque, node_id=pub_amand_1945_fatalisme
- label=Nature and Fate according to the Aristotelian Tradition: Alexander of Aphrodisia's Exegesis, node_id=pub_astolfi_2015_alexander_fate
- label=Human Autonomy and Divine Revelation in Origen, node_id=pub_boys_stones_2007_origen
- label=Middle Platonists on Fate and Human Autonomy, node_id=pub_boysstones_2007_middle_platonists
- label=Why neuroscience does not disprove free will, node_id=pub_brass_2019_neuroscience_free_will
- label=The Meaning of Prohairesis in Aristotle's Ethics, node_id=pub_chamberlain_1984_prohairesis
- label=La défense argumentée du libre arbitre dans la tradition musulmane, node_id=pub_comerro_2013_libre_arbitre_islam
- label=Théologie de l'image de Dieu chez Origène, node_id=pub_crouzel_1956_origine
- label=Extending Compatibilism: Control, Responsibility, And Blame, node_id=pub_deery_2007_compatibilism

## Formatting / Title Issues

- Non-passage descriptions with markdown or list formatting: 167
- `argument`: 56
- `publication`: 38
- `concept`: 26
- `person`: 16
- `work`: 13
- `synthesis`: 11
- `debate`: 6
- `school`: 1

- Non-passage descriptions with raw newlines: 209
- `argument`: 83
- `concept`: 41
- `publication`: 38
- `person`: 16
- `synthesis`: 12
- `work`: 12
- `debate`: 6
- `school`: 1

- Passage labels with raw importer-style `chap.: / par.: / verset.:`: 56
- Passage labels still containing underscores in the display title: 1624
- Suspicious ID/type prefix mismatches (e.g. `concept_*` typed as `synthesis`): 5

- Representative suspicious ID/type mismatches:
- type=synthesis, prefix=concept, label=Cicero De Fato: In Nostra Potestate - Complete Latin Doctrine Synthesis, node_id=concept_cic_fat_synthesis
- type=synthesis, prefix=concept, label=Cicero De Fato: Thematic Index for Cross-Reference, node_id=concept_cic_fat_index
- type=synthesis, prefix=concept, label=Epictetus ἐφ' ἡμῖν Doctrine: Thematic Index, node_id=concept_epict_thematic_index
- type=synthesis, prefix=concept, label=Epictetus: τὸ ἐφ' ἡμῖν - Complete Doctrine Synthesis (185 Passages), node_id=concept_epict_eph_hemin_synthesis
- type=synthesis, prefix=concept, label=διττὴ ἁμαρτία (Double Sin) - Plotinus's Synthesis of Embodiment Doctrines, node_id=concept_ditte_hamartia_double_sin_plotinus

## Duplication

- Exact duplicate label groups: 4
- `person` / `Cleanthes of Assos`: 2 nodes
- `person` / `Flavius Josephus`: 2 nodes
- `person` / `Maximus the Confessor`: 2 nodes
- `person` / `Philo of Alexandria`: 2 nodes

- Likely near-duplicate groups: 1
- `debate`: `Intellectualism vs Voluntarism Debate` vs `Intellectualism vs Voluntarism`

## Scope Drift Question

- Nodes outside the ancient timeline (`Medieval`, `Early Modern`, `Modern`, `Contemporary`): 338/17396 (1.9%)
- `Contemporary`: 196
- `Early Modern`: 79
- `Medieval`: 54
- `Modern`: 9

## Suggested Fix Order

1. Keep the ontology and live relation inventory aligned, including `translation_of`, canonical semantic/debate relation names, and the live `passage -> debate` use of `contributes_to`.
2. Repair the remaining provenance gaps on claim-bearing nodes, starting with the assertive claims that still lack evidence anchors.
3. Fill remaining missing descriptions and empty metadata records, using only source-backed or metadata-backed content.
4. Add the remaining missing `authored_by` links where a unique author can be proven from existing metadata, labels, or inherited work structure.
5. Normalize the remaining raw importer-style passage labels and markdown-heavy node descriptions.
6. Review the remaining duplicate candidates and scope-drift nodes that still require editorial judgment.

## Artifacts

- Full machine-readable details are in the sibling JSON report.
