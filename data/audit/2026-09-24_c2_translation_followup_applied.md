# Traductions machine : suite de la revue C2 — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c2_translation_followup.py` (93 décisions) et `scripts/apply_2026_09_24_c2_translation_followup.py`, qui reprend la mécanique et l’estampille du lot `c2_misaligned_translations`.
Décisions : `data/audit/2026-09-24_c2_translation_followup_decisions.jsonl`. Quarantaine : `data/audit/2026-09-24_c2_translation_followup_quarantine.jsonl`.

## Pourquoi un second passage

Le premier lot a établi des défauts de lot, et non des erreurs isolées, dans le même lot machine : décalages chez Méliton, Barnabé et Théophile ; pseudo-traductions hybrides dans *Contre Celse* V-VI ; synopsis à la voix de l’éditeur dans le *Pasteur*. La file Jev s’arrêtait à p ≤ 0,3. J’ai donc relu, dans ces mêmes œuvres, les paires restantes avec 0,3 < p < 0,7 (88 paires), plus les synopsis à la voix de l’éditeur hors file (Chrysostome, Hermas).

Au-dessus de 0,7, un échantillon (Méliton 18 paires, *Contre Celse* V-VI 40 paires) ne montre que des traductions fidèles : le seuil de 0,7 discrimine bien ici.

## Résultat

| Verdict | N |
|---|---|
| Retirées : hybrides (*Contre Celse* V-VI, 16), décalées (Méliton 2, Barnabé 3), synopsis mal cadré (Hermas 1) | 22 |
| Synopsis du même chapitre, requalifié `machine_paraphrase` (Chrysostome 4, Hermas 2) | 6 |
| Fidèles, couverture partielle (Théophile II-III, Barnabé, Méliton, *Contre Celse* V-VI) | 62 |
| Fidèles, débordant sur les versets suivants | 3 |

Bilan : −22 nœuds, 71 nœuds estampillés ou requalifiés, −66 arêtes, −22 passages et −22 citations du corpus.

## Contrôles

Préconditions et invariants identiques au premier lot. Relance : no-op. Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity`, `check_kg_work_child_canonical`. Stats et BibTeX régénérés.
