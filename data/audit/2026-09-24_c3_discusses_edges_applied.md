# C3 : arêtes `discusses` probablement fausses — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c3_discusses_edges.py` (265 décisions, une note par arête) et `scripts/apply_2026_09_24_c3_discusses_edges.py`.
Décisions : `data/audit/2026-09-24_c3_discusses_edges_decisions.jsonl`. Quarantaine : `data/audit/2026-09-24_c3_discusses_edges_quarantine.jsonl` (124 arêtes, 94 citations de corpus miroirs).

## Méthode

Pour chacune des 265 arêtes `discusses` de `queue_A_likely_wrong.csv`, j'ai lu le texte, ou le résumé, du nœud source, ainsi que la description de la cible et la provenance de l'arête. Une arête n'est retirée que dans l'un de ces cas :

- le texte ou le résumé de la source porte sur autre chose ;
- l'arête est née d'un mot égaré ;
- sa provenance déclare qu'elle ne repose sur aucun contenu ;
- sa justification nomme des mots absents du texte.

L'absence d'un mot-clé dans un simple extrait ne suffit pas.

## Résultat

| Verdict | N |
|---|---|
| `removed` | 124 |
| `false_positive` : conservée | 50 |
| `needs_romain` | 91 |

### Retraits

- **Augustin, *De libero arbitrio* → prescience divine** (56 arêtes, générées automatiquement, confiance 0,5). Tout le livre III avait été relié au concept. Or la prescience n'est traitée qu'en III.2.4-III.4.11, et les passages concernés sont hors de cette section. Leurs résumés portent sur l'âme, le péché, la création ou la théodicée ; Alexandre, *De fato* 27, porte sur l'inamissibilité des vertus.
- **Augustin → *voluntas*** (37 arêtes).
  - Ce sont les passages du livre II, 3-17 : sens externes et sens interne, nombre, sagesse, vérité immuable. C'est la preuve de l'existence de Dieu, comme le montrent leurs propres résumés.
  - S'y ajoutent la synthèse de cette preuve et la liste des références bibliques du *De gratia et libero arbitrio*.
  - Les 43 autres arêtes vers *voluntas* (livres I et III) restent en `needs_romain` : la volonté y est en jeu, mais l'extrait ne le montre pas.
- **« Savant → PAP » par `period_match`** (13 arêtes). La provenance déclare un simple recoupement de dates : Camus, Pohlenz, Hadot, Sedley, Striker, Cooper, etc. sont reliés au principe des possibilités alternatives de Frankfurt.
- **`auto_linked_from_description` sur un mot égaré** (15 arêtes) :
  - « Manuel » renvoyait au *Manuel* d'Épictète, alors qu'il s'agit d'un manuel scolaire (3 synthèses d'Amand) ;
  - « double » renvoyait à Richard Double (2 arêtes) ;
  - « Jérusalem » renvoyait à Sophrone, alors qu'il s'agit de Cyrille ;
  - « Apologie » renvoyait à Lucien, alors qu'il s'agit d'Aristide et d'Athénagore ;
  - « Περὶ εἱμαρμένης » renvoyait à Diogénianos, alors qu'il s'agit d'Alexandre ;
  - « De providentia » renvoyait au Chrysostome de SC 79, alors qu'il s'agit de Philon et de Proclus (2 arêtes) ;
  - « martyr » renvoyait à Justin, alors qu'il s'agit du martyre de Méthode ;
  - Tertullien, Justin et Posidonius étaient reliés à des nœuds qui ne les nomment pas (3 arêtes).
- **Justification contredite par le texte** (3 arêtes) :
  - Alexandre, *De fato* 24 → « cause commune » : la justification annonce κοινὴ αἰτία, mais aucune forme de κοινός ne figure dans le chapitre ;
  - *De fato* 5 → « pluralité des biens » : ni καλόν, ni ἡδύ, ni συμφέρον ;
  - Boèce, *Cons.* 107 → *liberum arbitrium* : le passage est la définition du hasard (*casus*), sans *arbitrium* ni *libertas*.
- **Synthèse augustinienne → « théodicée pédagogique »**, concept que sa propre description attribue à Théophile (1 arête).

### Conservées ou renvoyées

- **Conservées** : les arêtes avec page attestée ; les ouvrages savants reliés aux figures qu'ils étudient (Frede 2011 → Galien, Tatien, Porphyre, etc.) ; les étiquettes thématiques des notices Origenality ; les chapitres d'Alexandre où figure le terme annoncé par la justification (τύχη, κύριος).
- **`needs_romain`** :
  - les 28 arêtes Épictète → ἐφ' ἡμῖν ou προαίρεσις. Les nœuds ne contiennent que des extraits glosés, alors que le chapitre entier peut contenir le terme : `passage_epict_9` est *Diss.* I.1, le chapitre même sur ce qui dépend de nous ;
  - 7 chapitres d'Alexandre sans le terme clé, lorsque la justification ne l'annonce pas ;
  - 2 extraits d'Augustin trop courts pour juger (→ concupiscence) ;
  - 11 liens de provenance faible (mot-clé, titre approximatif) qu'on ne peut trancher à partir des deux nœuds ;
  - les 43 arêtes restantes vers *voluntas* (voir plus haut).

## Défaut systémique

Trois générateurs produisent l'essentiel des retraits :

- le câblage « œuvre entière → concept » (`passage_to_concept`, confiance 0,5), qui relie chaque passage d'une œuvre au thème de l'œuvre ;
- `auto_linked_from_description`, qui relie un nœud à toute entité dont le libellé apparaît dans sa description, y compris un mot commun ;
- `period_match`.

Proposition : marquer `citability: discoverable_only` les arêtes restantes de ces trois générateurs tant qu'elles n'ont pas été lues, et restreindre `auto_linked_from_description` aux libellés de plus d'un mot qui ne sont pas des noms communs.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
- `check_snapshot_passage_integrity` : ensemble des violations identique à celui du commit de base.
- Stats et BibTeX régénérés.
