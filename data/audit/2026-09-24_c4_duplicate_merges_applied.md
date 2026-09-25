# Fusion des doublons confirmés de la campagne C4 — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c4_duplicate_merges.py` et `scripts/apply_2026_09_24_c4_duplicate_merges.py`.
Décisions : `data/audit/2026-09-24_c4_duplicate_merges_decisions.jsonl`. Nœuds absorbés et arêtes retirées, intégralement conservés : `data/audit/2026-09-24_c4_duplicate_merges_quarantine.jsonl`.

## Point de départ

`data/quality/jev_2026_09_24/c4_dedup_schools/queue_likely_duplicates.csv` : huit paires à p ≥ 0,9. J’ai relu chaque paire en entier (libellé, description, métadonnées, toutes les arêtes). Sept désignent une seule entité sous deux ids, la huitième non.

## Fusions (7)

| Survivant | Absorbé | Preuve d’identité |
|---|---|---|
| `sc123_melito_peri_pascha` | `work_melito_peri_pascha` | Même homélie, même édition : les deux nœuds renvoient à Perler, SC 123 (1966) |
| `work_bardaisan_book_of_laws` | `work_bardesanes_liber_legum_regionum` | *Book of the Laws of the Countries* = *Liber Legum Regionum*, dialogue syriaque de Philippe, disciple de Bardesane (incident déjà nommé par la règle R2) |
| `sc379_athenagoras_legatio` | `work_athenagoras_legatio_sc379` | Même *Legatio*, même volume SC 379 |
| `scholarly_work_linjamaa_2019_the_ethics_of_the_tripartite_tractate_nh` | `pub_linjamaa_2019_ethics_tripartite_tractate` | Même monographie, Brill 2019, NHMS 95. Le survivant porte le DOI 10.1163/9789004407763 |
| `work_irenaeus_epideixis` | `work_irenaeus_demonstratio_apostolic` | *Epideixis* = *Démonstration de la prédication apostolique* |
| `sc470_aristides_apologia` | `work_aristides_apology_sc470` | Même *Apologie*, même volume SC 470 |
| `scholarly_work_tomberlin_1977_god_evil_and_the_free_will_defence` | `pub_plantinga_god_evil_free_will_defence` | Même article, *Religious Studies* 13 (1977), p. 455-475. Le survivant porte le DOI 10.1017/S0034412500010350 |

Survivant choisi : le nœud qui porte la structure (chapitres, passages, pointeurs) ou l’identifiant vérifiable (DOI). Pour chaque fusion :

- l’id absorbé va dans `metadata.merged_from` et `metadata.previous_node_id`, son libellé dans `alternative_names` ;
- les métadonnées absentes du survivant sont reportées. Les variantes de description (`description_*`, `translation_*`) ne sont pas reportées : ce ne sont pas des faits sur le survivant, et l’enregistrement absorbé est conservé tel quel en quarantaine ;
- la description publique du survivant est conservée. Exception : Linjamaa et Tomberlin, dont le survivant n’avait pour description que son titre. Ils reprennent la description de l’absorbé, déjà publique ;
- les arêtes sont redirigées. Sont supprimées celles qui deviennent un doublon (6) ou le jumeau inverse d’une arête du survivant (2, `wrote` face à `authored_by`, règle R17).

Correction d’attribution : l’arête `pub_plantinga_god_evil_free_will_defence authored_by scholar_plantinga_a` est supprimée. Plantinga est le sujet de l’article, non son auteur : la notice elle-même porte `author = "James E. Tomberlin and Frank McGuinness"`. C’est aussi la fin du défaut R9 (id au nom du mauvais savant).

Bilan : −7 nœuds, 7 nœuds modifiés, −10 arêtes, 18 arêtes redirigées. Aucune citation de corpus ni aucun pointeur ne visait les ids absorbés.

## Non fusionné (1) : faux positif pour la fusion

`argument_bobzien_2001_b1_philopator_late_compatibilism` / `scholarly_argument_bobzien_later_stoic_compatibilism_phil_6` : les deux nœuds sont déjà reliés par `same_thesis_as` (vague `semantic_merges_2026_08_17`, DAS-001), qui les garde volontairement comme deux granularités. Surtout, leurs renvois de pages divergent : ch. 8, p. 358-412 d’un côté ; `page_range` 216-225 et `quote_page` p. 372 de l’autre. Une fusion masquerait cette contradiction.

## Contrôles

Préconditions (types identiques, survivant non estampillé, absorbé présent). Invariants vérifiés avant écriture. Relance : no-op. Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity`, `check_kg_work_child_canonical`. Stats et BibTeX régénérés.

## needs_romain

- Bobzien, *Determinism and Freedom in Stoic Philosophy*, chapitre sur PHILOPATOR : vérifier sur le volume les pages exactes de la thèse et de la citation (`page_range` 216-225 contre ch. 8 p. 358-412 ; citation p. 372), puis corriger le nœud fautif.
- Tomberlin & McGuinness 1977 : Frank McGuinness n’a pas de nœud `person`. À créer si l’article est gardé comme co-signé (métadonnées : *Religious Studies* 13/4, p. 455-475, DOI 10.1017/S0034412500010350, non revérifiées en ligne depuis cet environnement).
