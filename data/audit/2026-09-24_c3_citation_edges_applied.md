# C3 : arêtes de citation probablement fausses — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c3_citation_edges.py` (105 décisions, une note par arête) et `scripts/apply_2026_09_24_c3_citation_edges.py`.
Décisions : `data/audit/2026-09-24_c3_citation_edges_decisions.jsonl`. Quarantaine : `data/audit/2026-09-24_c3_citation_edges_quarantine.jsonl` (26 arêtes, 3 citations de corpus).

## Périmètre

Le périmètre couvre les 105 arêtes de citation de `c3_edges_links/queue_A_likely_wrong.csv` : 58 `cites_primary_source`, 24 `evidenced_by` et 23 `source_for`. Pour chacune, j'ai lu le texte de la cible ainsi que la provenance de l'arête (métadonnées, vague d'origine, justification). Une arête n'est retirée que si le texte cible ou ses propres métadonnées contredisent l'affirmation. Une lecture différente de la mienne ne suffit pas.

## Résultat

| Verdict | N |
|---|---|
| `removed` | 25 (+ 1 arête jumelle) |
| `corrected` : cible déplacée vers la bonne œuvre | 3 |
| `corrected` : texte cible rétabli par le lot Plotin | 2 |
| `false_positive` : conservée | 20 |
| `needs_romain` | 55 |

### Retraits

- **Argument contredit par sa propre description** (lignes 4-6). L'argument carnéadien « les stoïciens punissent pourtant les criminels » repose, selon sa description, « sur le seul témoignage d'Alexandre (Περὶ εἱμαρμένης 19) ». Il citait pourtant Eusèbe, *PE* VI.6.12-15, où il est question de l'inutilité de l'exhortation sous le destin.
- **Mauvaise œuvre** (ligne 8). L'argument de Frede 2011 sur Alexandre (« De fato 192, 22ff », pagination de Bruns) pointait vers le *De fato* de Cicéron. Le même argument cite déjà `work_de_fato_alexander_c200ce_o6p7q8r9`, et l'arête fausse est retirée.
- **Chrysostome** (ligne 58). L'argument antiastrologique renvoie aux homélies sur Col. et sur 1 Tim., tandis que sa justification nomme le « Discours III » du Pseudo-Chrysostome. La cible, SC 79, *De Providentia*, ch. 3, traite des séraphins et ne contient aucun terme de la famille de γένεσις ou d'εἱμαρμένη.
- **Tertullien** (lignes 63-64, générées automatiquement, confiance 0,4). *Adversus Praxean* 1-2 porte sur Praxéas : le Père né de la Vierge et ayant souffert. Marcion n'y est pas nommé et le libre arbitre n'y est pas discuté.
- **Athénagore** (lignes 65-68, 71). La note de l'arête, « applique le libre arbitre à la chute des anges et des démons », ne correspond à aucun des textes cibles : *Legatio* 9.2 (textes-preuves d'Isaïe), 9.3, 10.1 (attributs divins), 26.3-5 (statues de Néryllinos) et 7.1 (monothéisme).
- **Balayage terminologique sur Boèce** (lignes 72-73, 75, 77, plus l'arête `discusses` de même paire).
  - Pour *clinamen*, on ne trouve que « a vitiis declinantes » (« se détournant des vices ») et « indeclinabilem causarum ordinem » (« l'ordre inflexible des causes »).
  - *Cons.* 6, la robe de Philosophie, ne contient pas *fatum*.
  - *Cons.* 106 est le mètre IV.7 sur les travaux d'Hercule.
- **Aristide** (ligne 74). La cible, *Apol.* 11.3-4 (SC 470), porte sur Aphrodite et Adonis. La note de l'arête (« hekousios boulē ») ne correspond pas au texte.
- **Pharisiens → Diogène Laërce 1.22-23** (lignes 80-81, générées automatiquement, confiance 0,4). C'est la vie de Thalès.
- **« Meilleur substitut disponible » avoué** (lignes 94-96, 102). La raison inscrite dans l'arête nomme elle-même d'autres sources :
  - *De divinatione* II ;
  - Aulu-Gelle rapportant Favorinus, et Bardesane chez Eusèbe ;
  - Augustin, *De civitate Dei* V ;
  - pour le mythe de Zagreus, la cible précise que l'anthropogonie n'est attestée qu'« explicitement chez Olympiodore ».
- **Ligne 98.** Diogène Laërce comme source du « paradigme olympien », déduit d'une arête `influences` (« existing edge: influenced »). L'arête `influences` elle-même va en `needs_romain`.
- **Ligne 104.** Proclus comme source d'un concept que la cible décrit comme « innovation de Clément ».

### Cibles déplacées (lignes 60-62)

Les trois arguments du Pseudo-Chrysostome sont situés par leurs propres descriptions dans le *De fato et providentia*, Discours V (PG 50, 765-768). Ils pointaient vers SC 79, *De Providentia*, ch. 5, une autre œuvre dont le texte ne contient aucun terme de la famille de γένεσις ou d'εἱμαρμένη. L'arête 62 portait d'ailleurs la mention « tentative — confirm SC79 chap5 = PG 50 Discourse V mapping ». Les trois arêtes sont déplacées vers `work_pseudo_chrysostom_de_fato_providentia` ; l'ancienne cible est gardée dans `metadata.c3_citation_review_2026_09_24`. Les citations de corpus miroirs vers la ligne SC 79 sont retirées.

### Faux positifs Jev

Les faux positifs sont conservés. Ce sont :

- des arêtes avec `attested_by` et pages imprimées (lignes 43-51, 54-57) ;
- des citations au niveau de l'œuvre, déjà marquées `evidence_pending` ou pourvues du chapitre de l'auteur moderne (lignes 19-20, 24-26) ;
- Aulu-Gelle, *NA* VII.2.15 (ligne 7) ;
- *Legatio* 25.1 sur les anges déchus (ligne 70).

Le score faible s'explique par l'écart entre un résumé moderne et le texte ancien, non par une erreur.

## `needs_romain` (55)

- **Vague `wave_h_anchoring_chrysippe_carneade_cicero_2026_05_16`** (lignes 0-3, 28-42, 52-53). Le chapitre visé est juste (Aulu-Gelle *NA* VII.2, Cicéron *De fato*, Diogène Laërce VII), mais le choix de la section n'est pas donné par la littérature citée dans l'arête.
- **Fürst 2022 et Frede 2011 → Cic. *Fat.* 23-25, 39-41** (lignes 9-14, 27). La page de l'auteur moderne qui cite ces sections n'est pas consignée.
- **Eusèbe, *PE* VI.6** (lignes 15-18).
  - Ligne 15 : la littérature citée dit « *PE* VI.7.35-41 », mais la cible est VI.6.7, et aucun nœud VI.7.35-41 n'existe.
  - Lignes 16-18 : l'attribution de ces sections de VI.6 à Origène n'est pas indiquée.
- **Destrée-Salles-Zingano 2014** (lignes 21-23). Arêtes tirées de la table des matières (chapitre → œuvre) : plausibles, mais à vérifier sur le volume.
- **Philocalie 23.4** (ligne 59). Ancrage « via amand1945_dissertation_structure ».
- **Alexandre, *De fato*** (lignes 82-88, générées automatiquement, confiance 0,5). Le rattachement aux chapitres ne concorde pas toujours : par exemple, un argument du pari daté des ch. 20-21 est rattaché au ch. 36.
- **Lot `kg_manual_review_batch_05` / `kg_provenance_batch_04`** (lignes 89-93, 97, 99-101, 103). Liens de type « meilleure source disponible dans le KG », non démontrablement faux, mais sans locus ancien.
- **Ligne 69.** *Legatio* 24.1-2 introduit les anges, et la chute suit en 24.3-6 : quelle section porte l'affirmation ?
- **Ligne 76.** *Cons.* IV m. 4, « propria fatum sollicitare manu » : *fatum* au sens de la mort. Faut-il y voir le concept stoïcien ?

## Défaut systémique et proposition

Les arêtes retirées viennent de trois générateurs :

- `discovery_method: terminology_scan`, qui fait correspondre un mot sans tenir compte du sens ;
- `auto_generated` à confiance 0,4 ou 0,5 ;
- les liens « meilleur substitut disponible dans le KG » des lots de mars 2026.

Proposition : exiger, pour `cites_primary_source`, `evidenced_by` et `source_for`, un `attested_by` avec locus ou page (sur le modèle de R16), et marquer `citability: discoverable_only` les arêtes de ces trois générateurs qui n'en ont pas.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
- `check_snapshot_passage_integrity` : ensemble des violations identique à celui du commit de base.
- Stats et BibTeX régénérés.
