# Justin, *Dialogue avec Tryphon* : artefacts « &#45; » et un locus mal formé — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_justin_tryph_entities.py` et `scripts/apply_2026_09_24_justin_tryph_entities.py`. Le script prend en argument (`--tei`) une copie locale du TEI de l’édition.
Décisions : `data/audit/2026-09-24_justin_tryph_entities_decisions.jsonl`.

## Point de départ

Jev signale `passage_just_tryph_27_3` comme « texte mêlé d’apparat » (p = 0,93).

## Preuve : l’édition elle-même, niveau 1

Les nœuds déclarent l’édition `tlg0645.tlg003.perseus-grc2` : G. Archambault, *Justin, Dialogue avec Tryphon*, Paris, Picard, 1909, encodée par Perseus et publiée dans OpenGreekAndLatin/First1KGreek, `data/tlg0645/tlg003/tlg0645.tlg003.perseus-grc2.xml`.

- Les renvois scripturaires entre crochets, par exemple « [cf. Is., III, 16] », **figurent dans le texte imprimé d’Archambault** : ils restent. Sur ce point, le signalement de Jev est un faux positif.
- **Défaut réel :** dans 197 nœuds et 196 jumeaux du corpus, le trait d’union de ces renvois est écrit sous la forme de l’entité HTML `&#45;`. On lit « [cf. Ps., XIII, 2 &#45; 3, et Rom., III, 44 &#45; 47] » là où l’édition porte « [cf. Ps., XIII, 2-3, et Rom., III, 44-47] ».
- `passage_just_tryph_140_4` déclare le locus « 140_4 », qui n’est pas une référence CTS. Son texte est celui de la section 140.4 du TEI : le locus devient `140.4`, l’ancien URN est conservé dans `previous_cts_urn`.

## Règle, vérifiée enregistrement par enregistrement

On remplace `&#45;`, avec les espaces qui l’entourent, par « - ». Le texte obtenu doit être **identique, caractère pour caractère une fois les espaces retirés**, à la section TEI du locus du nœud. 197 nœuds et 196 passages du corpus satisfont la règle, aucun n’est écarté. Aucun caractère grec n’est modifié.

## Contrôles

Préconditions, estampille et relance (no-op). Invariants vérifiés. Portes OK : `check_corpus_invariants --strict`, `check_greek_gate` (les nœuds modifiés sont attestés dans le corpus), `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity`, `check_kg_work_child_canonical`.
