# Passages éditoriaux anglais déclarés grecs ou latins, et revue de la file C1 « qualité du texte » — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_editorial_passage_language.py` et `scripts/apply_2026_09_24_editorial_passage_language.py`.
Décisions : `data/audit/2026-09-24_editorial_passage_language_decisions.jsonl` (46 corrections) et `data/audit/2026-09-24_c1_quality_flags_review_decisions.jsonl` (les 20 lignes des files C1 `queue_quality_flags` et `queue_language_mismatch`).

## Correction appliquée

46 nœuds `passage` se déclarent eux-mêmes produits éditoriaux (`passage_role` = `editorial_synthesis` ou `summary`), mais portent `metadata.language` = `grc` ou `lat`. Je les ai tous lus : ce sont des textes anglais d’éditeur qui citent de courtes phrases grecques ou latines, par exemple « ARISTOTLE ON WISH AND THE APPEARANCE OF THE GOOD… ». Les nœuds concernés : Aristote EN III (11), Augustin *De gratia et libero arbitrio* I (20), Épictète (3), Justin *1 Apol.* 43-44 (2), Lucrèce II (2), Marc Aurèle (7), Plotin (1).

- `language` passe à `eng`.
- La langue citée est gardée dans `quoted_language`, l’ancienne valeur dans `language_before_2026_09_24`.
- Aucun texte n’est modifié.

## Revue des 20 signalements C1

- **Faux positifs (8)** :
  - *Magna Moralia* : les crochets sont les signes éditoriaux de Susemihl ;
  - Alexandre, *De fato* 11 et 14 : ⟨ ⟩ marque un supplément de Bruns ;
  - Aspasius 1 : « ἠθικὴ] » figure tel quel dans le TEI First1KGreek ;
  - EN 10.3 : texte propre.
- **Corrigés (6)** : les synthèses EN III et le résumé d’Augustin (ce lot), et Justin 27.3 (lot `justin_tryph_entities`).
- **Défauts confirmés, non corrigés ici (3), parce qu’ils sont systémiques** :
  1. **Références Perseus insérées dans le grec.** Dans 105 passages grecs, les éléments `<bibl>` et `<note>` du TEI se retrouvent au milieu du texte, par exemple « Parmenides Fr. 13 (Diels) » dans la *Métaphysique* 1.4 ou « Hom. Od. 12.219 » dans EN II.9. Une règle stricte, vérifiée contre le TEI, ne permet d’en réparer que 18, parce que la plupart des nœuds sont des sous-parties de sections TEI. Proposition : écarter `<bibl>` et `<note>` à l’extraction, puis redériver les passages.
  2. **Boèce, *Consolation*.** Les 129 passages et leurs traductions partagent un seul URN, `urn:cts:latinLit:lat7127.011.perseus-lat1:1`, qui n’est pas un identifiant Perseus, et leur latin est un OCR non corrigé : « {contraque} », « quo -: », « Liquet igitur. I quam ». Proposition : réingérer depuis le TEI Perseus `stoa0058.stoa001.perseus-lat2`, avec des loci livre.section.

## needs_romain

- *Magna Moralia* 1.6.2 et 2.6.21 : les nœuds viennent du TLG E, non de First1KGreek. En 2.6.21, le supplément de Susemihl 〈ἂν〉 apparaît sous la forme [ ἂν], signe d’athétèse. À vérifier sur le TLG E local.

## Contrôles

Préconditions (langue et rôle inchangés), estampille, relance no-op. Portes OK : `check_greek_gate`, `check_citations_gate`, `check_kg_corpus_locus_parity`, `check_corpus_invariants --strict`.
