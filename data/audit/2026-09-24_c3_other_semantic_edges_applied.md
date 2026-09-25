# C3 : autres arêtes sémantiques — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c3_other_semantic_edges.py` (41 décisions) et `scripts/apply_2026_09_24_c3_other_semantic_edges.py`.
Décisions : `data/audit/2026-09-24_c3_other_semantic_edges_decisions.jsonl`. Quarantaine : `data/audit/2026-09-24_c3_other_semantic_edges_quarantine.jsonl` (2 arêtes).

## Périmètre

Ce lot traite les 41 arêtes restantes de `queue_A_likely_wrong.csv` : `influences`, `extends`, `critiques`, `influenced_by`, `interprets`, `has_position`, `employs`, `contributes_to`, `supports`, `presupposes`, `same_thesis_as` et `exemplifies`.

## Résultat

| Verdict | N |
|---|---|
| `removed` | 2 |
| `false_positive` : conservée (page ou source attestée, ou relation plausible) | 30 |
| `needs_romain` | 9 |

Retraits :

- **Diogène Laërce → « paradigme olympien » (`influences`).** La source est une doxographie du III<sup>e</sup> siècle. La cible décrit une conception de la religion grecque archaïque et qualifie elle-même « paradigme olympien » d'étiquette heuristique moderne. Aucune provenance n'est donnée.
- **Justin → « théodicée pédagogique » (`extends`).** Le concept est décrit comme « l'innovation de Théophile ». Justin, antérieur à Théophile, ne peut pas le prolonger. L'arête ne cite qu'un « Anonymous (2011) ».

`needs_romain` : 9 arêtes sans provenance ou fondées sur une source anonyme :

- Sextus Empiricus → Galen Strawson ;
- Tatien → apocatastase ;
- Alexandre → argument du Pseudo-Plutarque ;
- Épictète → Frankfurt ;
- Esséniens → nomisme d'alliance ;
- deux câblages débat → position de la vague `wave_i` ;
- un lien contextuel généré automatiquement ;
- « paradigme olympien » → Jamblique.

Les 30 arêtes conservées portent une attestation (Amand, Fürst, Boulnois, pages imprimées, etc.) ou sont plausibles d'après les deux nœuds.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
