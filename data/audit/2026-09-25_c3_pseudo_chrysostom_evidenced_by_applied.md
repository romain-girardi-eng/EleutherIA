# Suivi C3 — trois arêtes `evidenced_by` mal typées (Pseudo-Chrysostome) — appliqué le 2026-09-25

Scripts : `scripts/data_2026_09_25_pseudo_chrysostom_evidenced_by.py` (décisions) et `scripts/apply_2026_09_25_pseudo_chrysostom_evidenced_by.py` (application).
Décisions : `data/audit/2026-09-24_c3_pseudo_chrysostom_evidenced_by_decisions.jsonl`. Arêtes retirées, conservées intégralement : `data/audit/2026-09-24_c3_pseudo_chrysostom_evidenced_by_quarantine.jsonl`.

## Ce qui a changé

Trois arêtes `evidenced_by` retirées, des arguments Amand 1945 du Discours V (recapitulation, v_apologetic, v_witness6) vers `work_pseudo_chrysostom_de_fato_providentia`.

## Pourquoi

La revue C3 du 2026-09-24 les avait, à raison, détachées de SC 79, chap. 5 (Jean Chrysostome, *Sur la providence de Dieu*, un autre traité) pour les rattacher au *De fato et providentia* du Pseudo-Chrysostome (PG 50, 765-768), où les descriptions des arguments les situent. Mais `evidenced_by` n'admet qu'un passage pour cible (`knowledge graph/ontology/edge_types.json`) : la porte RDF/SHACL de la CI a relevé trois violations `ClassConstraintComponent`. Chacun de ces arguments porte déjà `cites_primary_source → work_pseudo_chrysostom_de_fato_providentia`, qui énonce la même citation avec un type admis : les trois arêtes étaient redondantes.

## Contrôles

Précondition à l'exécution : l'arête `cites_primary_source` équivalente existe (sinon, refus). Relance : no-op. Portes : `check_corpus_invariants`, `check_kg_work_id_uniqueness`, `check_kg_work_child_canonical`, `check_kg_corpus_locus_parity --strict` OK ; SHACL (profil bloquant) : conforme, 0 violation. `gen_stats.py` et `export_publications_bibtex.py` régénérés.

## needs_romain

Aucun ancrage au niveau du passage n'est possible sans le texte du Discours V (PG 50, 765-768) dans le corpus : à ingérer si l'on veut rétablir des `evidenced_by` au locus.
