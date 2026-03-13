# KG Quality Audit

Generated: 2026-03-06T08:21:52.336112+00:00

## Snapshot

- Audited live PostgreSQL KG, not a checked-in export.
- Nodes: 6444
- Edges: 19956
- Passage citations: 2493
- Claim-bearing nodes audited for provenance risk: 408

## What Is Already Clean

- Orphan edges: 0
- Orphan passage citations: 0
- Isolated / no-edge nodes: 0
- Duplicate edge triples: 0
- Self-loops: 0

## Priority Fixes

1. Provenance gaps: 245/408 (60.0%) claim-bearing nodes have no passage citation, no evidence relation, and no direct passage edge.
2. Unsupported-claim candidates: 106/408 (26.0%) claim-bearing nodes still use assertive language despite lacking any evidence anchor.
3. Ontology drift: 0 live relations are missing from the ontology, and 0 edges violate the current relation type constraints.
4. Thin node records: 44 nodes have empty metadata and 0 nodes have no description at all.
5. Incomplete authorship / structure: 35 work nodes, 34 publication nodes, 2 quote nodes, and 56 passage nodes lack `authored_by`.
6. Formatting drift: 172 non-passage node descriptions contain markdown or list markup, and 56 passage labels still expose importer-style `chap.: / par.: / verset.:` strings.

## Provenance / Hallucination Risk

- Heuristic used here:
  A node is flagged when it is a claim-bearing type and has zero passage citations, zero `evidenced_by` / `source_for` / `grounded_in` relations, and zero direct graph edges to passage nodes.
- Higher-risk subset:
  Same rule as above, plus assertive wording in the description (`argues`, `shows`, `foundational`, `central`, etc.).

- Claim nodes without any evidence anchor: 245
- `argument`: 100
- `concept`: 97
- `quote`: 13
- `synthesis`: 12
- `debate`: 7
- `controversy`: 5
- `school`: 5
- `conceptual_evolution`: 3

- Assertive claim candidates without evidence: 106
- `argument`: 51
- `concept`: 37
- `synthesis`: 6
- `debate`: 3
- `school`: 3
- `controversy`: 2
- `quote`: 2
- `conceptual_evolution`: 1

- Representative assertive examples:
- type=argument, period=Classical Greek, label=Aristotle's Potentiality-Actuality Argument, node_id=argument_aristotles_potentialityactuality_argument_20c5ac91
- type=argument, period=Classical Greek, label=Aristotle's Tripartite Division of Events, node_id=argument_aristotle_event_taxonomy
- type=argument, period=Classical Greek, label=Aristotle's Voluntary Action Argument (Eph' Hemin), node_id=argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188
- type=argument, period=Classical Greek, label=Plato's Laws X Self-Motion Argument, node_id=argument_platos_laws_x_selfmotion_argument_8c31a166
- type=argument, period=Classical Greek, label=Sea Battle Argument (Future Contingents), node_id=argument_sea_battle_aristotle_f6g7h8i9
- type=argument, period=Classical Greek, label=The Practical Syllogism, node_id=argument_the_practical_syllogism_1d2e7506
- type=argument, period=Classical Greek, label=Two-Way Powers (Rational Potentialities) Argument, node_id=argument_two_way_powers_aristotle_i9j0k1l2
- type=argument, period=Contemporary, label=Frankfurt Cases, node_id=argument_frankfurt_cases_1o2p3q4r
- type=argument, period=Early Modern, label=Argument from Animal Rationality, node_id=argument_argument_from_animal_rationality_4629e983
- type=argument, period=Early Modern, label=Best of All Possible Worlds, node_id=argument_best_of_all_possible_worlds_cb9e1741
- type=argument, period=Early Modern, label=Cambridge Platonist Defense of Plastic Nature, node_id=argument_cambridge_platonist_defense_of_plastic_nature_d49aa761
- type=argument, period=Early Modern, label=Cartesian Dualism and Agent Causation, node_id=argument_cartesian_dualism_and_agent_causation_b637cc75

## Ontology Drift

- Live relations missing from `kg/ontology/edge_types.json`:
- None

- Invalid relation/type combinations:
- None

## Thin / Incomplete Nodes

- Nodes with empty metadata: 44
- `concept`: 28
- `debate`: 12
- `person`: 2
- `synthesis`: 1
- `school`: 1

- Nodes without description: 0

- Nodes with null period: 30
- `passage`: 25
- `conceptual_evolution`: 3
- `source_collection`: 1
- `work`: 1

- Weakly connected nodes (degree 1-2): 333
- `person`: 98
- `publication`: 60
- `concept`: 52
- `work`: 39
- `passage`: 31
- `argument`: 25
- `quote`: 14
- `conceptual_evolution`: 3

## Authorship / Structure Gaps

- Work nodes missing `authored_by`: 35/118 (29.7%)
- Publication nodes missing `authored_by`: 34/79 (43.0%)
- Quote nodes missing `authored_by`: 2/14 (14.3%)
- Passage nodes missing `authored_by`: 56/5630 (1.0%)
- Passage nodes missing `part_of`: 6/5630 (0.1%)
- Translation integrity: 2815 English passage nodes, 0 missing `translation_of`, 0 source nodes incorrectly using `translation_of`.

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

- Non-passage descriptions with markdown or list formatting: 172
- `argument`: 59
- `publication`: 38
- `concept`: 26
- `person`: 17
- `work`: 13
- `synthesis`: 11
- `debate`: 7
- `school`: 1

- Non-passage descriptions with raw newlines: 213
- `argument`: 86
- `concept`: 41
- `publication`: 38
- `person`: 16
- `synthesis`: 12
- `work`: 12
- `debate`: 7
- `school`: 1

- Passage labels with raw importer-style `chap.: / par.: / verset.:`: 56
- Passage labels still containing underscores in the display title: 874
- Suspicious ID/type prefix mismatches (e.g. `concept_*` typed as `synthesis`): 5

- Representative suspicious ID/type mismatches:
- type=synthesis, prefix=concept, label=Cicero De Fato: In Nostra Potestate - Complete Latin Doctrine Synthesis, node_id=concept_cic_fat_synthesis
- type=synthesis, prefix=concept, label=Cicero De Fato: Thematic Index for Cross-Reference, node_id=concept_cic_fat_index
- type=synthesis, prefix=concept, label=Epictetus ἐφ' ἡμῖν Doctrine: Thematic Index, node_id=concept_epict_thematic_index
- type=synthesis, prefix=concept, label=Epictetus: τὸ ἐφ' ἡμῖν - Complete Doctrine Synthesis (185 Passages), node_id=concept_epict_eph_hemin_synthesis
- type=synthesis, prefix=concept, label=διττὴ ἁμαρτία (Double Sin) - Plotinus's Synthesis of Embodiment Doctrines, node_id=concept_ditte_hamartia_double_sin_plotinus

## Duplication

- Exact duplicate label groups: 0

- Likely near-duplicate groups: 1
- `debate`: `Intellectualism vs Voluntarism Debate` vs `Intellectualism vs Voluntarism`

## Scope Drift Question

- Nodes outside the ancient timeline (`Medieval`, `Early Modern`, `Modern`, `Contemporary`): 331/6444 (5.1%)
- `Contemporary`: 192
- `Early Modern`: 76
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
