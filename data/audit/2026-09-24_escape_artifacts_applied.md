# Séquences d'échappement dans les descriptions — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_escape_artifacts.py` et `scripts/apply_2026_09_24_escape_artifacts.py`.
Décisions : `data/audit/2026-09-24_escape_artifacts_decisions.jsonl`.

J'ai recherché, dans toutes les descriptions du KG, les entités HTML et les `\n` imprimés tels quels. Deux notices bibliographiques étaient touchées :

- `pub_arfe_2009_…`, où `&#13;\n` s'affichait au lieu d'un saut de ligne ;
- `pub_fauske_2005_…`, avec six `\n`.

Ces séquences sont remplacées par de vrais sauts de ligne, et l'ancien texte est conservé dans `metadata.description_before_2026_09_24`.

`needs_romain` : dans `passage_sen_ep_15_99_25`, la citation grecque de Sénèque est stockée en Beta Code brut (« *)/estin ga/r tis h(donh\ lu/ph| … »). Le `\` y note un accent grave, et non un saut de ligne. Il faut remplacer la citation par le grec de l'édition.

Contrôles : relance sans modification ; `check_corpus_invariants --strict`, `check_greek_gate` et `check_citations_gate` sont au vert.
