# KG ↔ corpus: extinction de la dette de parité décidable

Date : 18 août 2026  
Statut : **appliqué et vérifié ; parité globale stricte à zéro**

## Résultat

Le reliquat courant est reproduit exactement :

- 11 072 twins déclarés ;
- 10 994 twins résolus et 78 UUID absents ;
- 3 051 violations : 1 145 `canonical_ref`, 1 828 `cts_urn`, 78 twins absents ;
- aucune citation de twin manquante parmi les UUID résolus.

Le plan traite **3 045/3 051 violations** sur **2 084 nœuds**. Après
simulation, il reste exactement six différences, toutes dans la cohorte
Plutarque `tlg135`/`tlg138` explicitement confiée à l'adjudication parallèle.
Il ne reste aucun UUID absent, aucune différence d'URN et aucune nouvelle
violation.

```text
avant : 3 051 = 1 145 ref + 1 828 URN + 78 UUID absents
après :     6 =     6 ref +     0 URN +  0 UUID absent
corrigé : 3 045
```

L'application coordonnée a ensuite réidentifié les six passages Plutarque
`tlg135` comme *Epitome libri de animae procreatione in Timaeo*. Le contrôle
final sur le graphe complet donne :

```text
twins déclarés/résolus : 10 780 / 10 780
violations : 0
missing twins : 0
canonical_ref : 0
cts_urn : 0
```

La baseline versionnée a été régénérée avec trois listes vides et la CI exécute
désormais la parité globale en `--strict`, sans cohorte ni allowlist.

Un contrôle runtime ultérieur a retypé les 289 citations des relations
non-identiques en `related_passage_non_exact`. Leur cardinalité et leur cible
sont conservées, mais elles ne peuvent plus servir de fallback exact ni de
source textuelle citable (`2026-08-18_related_citation_types.md`).

## Principe d'identité

`metadata.db_passage_id` signifie désormais **même témoin et même
segmentation**, pas simplement « texte voisin ». Le plan distingue donc :

1. les vrais twins, dont les métadonnées peuvent suivre une autorité locale
   explicite ;
2. les relations utiles mais non identiques (traduction, extrait, segmentation
   fine/grossière, édition contradictoire) ;
3. les UUID supprimés intentionnellement.

Pour les catégories 2 et 3, le faux `db_passage_id` est retiré. La relation est
conservée sous `related_corpus_passage_id`, ou l'UUID supprimé sous
`former_corpus_passage_id`, avec `parity_status`, `parity_reason` et le stamp
`parity_zero_2026_08_18`. Ce n'est pas un masquage : c'est la correction de la
déclaration d'identité erronée.

## Buckets exhaustifs

| Famille / cause racine | Nœuds | Violations | Décision |
|---|---:|---:|---|
| Justin, *Tryphon*, vrais loci | 748 | 1 496 | KG suit les loci CTS à points du corpus Perseus. |
| Justin, *Tryphon* 88.5 et 140.4 | 2 | 4 | Démotion : corpus composite 88.4-5 / 140.4-141.2. |
| Plotin, URN KG tronquée | 646 | 646 | KG suit l'URN de passage `perseus-grc1` du corpus. |
| Boèce, provenance contradictoire | 128 | 255 | Démotion : KG `lat7127.011`, corpus `stoa0058.stoa001`, work `phi2089.phi002`; le manifeste nomme `lat7127.011`. |
| Philon, *De opificio* | 172 | 173 | Le manifeste impose `opp-grc1`; corpus et KG reçoivent ce témoin, en conservant le locus corpus 163-164 pour le nœud 164. |
| Platon, *Timée*, vrais twins | 75 | 150 | KG suit le titre développé et la version Perseus du corpus. |
| Platon, *Timée* 28 | 1 | 2 | Démotion : 910 lettres KG contre extrait corpus de 89 lettres (`28a`). |
| Justin, *Apologia prima* | 68 | 68 | KG suit la référence corpus ; CTS déjà identique. |
| Justin, *Apologia secunda* | 15 | 15 | Même décision. |
| Cicéron, *De fato* | 48 | 48 | Démotion : mapping critique local `phi054` contre témoin KG `phi056`. |
| Plutarque, *De Stoicorum repugnantiis* (`tlg136`) | 47 | 47 | KG suit le libellé corpus ; CTS et texte concordent. |
| Athénagore anglais | 10 | 10 | Vrai twin byte-identique ; KG suit le locus corpus. |
| Athénagore grec → corpus anglais | 10 | 10 | Démotion cross-language ; relation conservée. |
| Tatien, segmentation fine/grossière | 59 | 59 | 56 UUID supprimés + 3 lignes analytiques partagées : démotion vers les snapshots courants. |
| Ps.-Plutarque, *De fato* (`tlg108`) | 19 | 19 | Démotion de 19 UUID fins vers 11 passages grossiers attestés. |
| Aristote, *Éthique à Nicomaque* | 12 | 14 | Démotion : chapitres KG contre extraits Bekker/analytiques. |
| Augustin, *De civitate Dei* | 9 | 14 | Démotion : six granularités/éditions non collationnées et trois footers supprimés. |
| Aspasius | 6 | 6 | Vrais twins ; texte normalisé et CTS identiques. |
| Aristote, *De generatione* | 3 | 3 | Vrais twins byte-identiques ; le corpus donne II.9-11. |
| Barnabé grec | 1 | 1 | Vrai twin ; KG suit le locus SC. |
| Barnabé anglais → corpus grec | 1 | 1 | Démotion cross-language. |
| Clément de Rome anglais | 1 | 1 | Vrai twin byte-identique. |
| Clément de Rome grec → corpus anglais | 1 | 1 | Démotion cross-language. |
| Hégésippe rangé comme Alcinous | 1 | 1 | Démotion : l'audit prouve Hégésippe, le corpus porte encore `Didasc. 1`. |
| Épictète 185 | 1 | 1 | Démotion : le stamp TLG dit explicitement que le locus reste irrésolu. |
| **Total traité** | **2 084** | **3 045** | 1 620 synchronisations KG, 172 propagations Philon, 292 démotions. |

## Les six lignes volontairement exclues

Ces lignes ne sont pas indécidables quant à leur différence de forme ; elles
sont gelées parce que leur parent et les deux familles corpus doivent d'abord
être adjugés ensemble. Le parent `work_plutarch_de_communibus_notitiis`
déclare `tlg138`, ses six enfants matérialisés déclarent `tlg135`, et le
manifeste contient six passages `tlg135` plus cinquante `tlg138` de même titre.

| Nœud KG | UUID corpus | KG | Corpus |
|---|---|---:|---|
| `passage_plut_cn_1` | `c0460502-4859-4a25-ad61-3e7723937953` | `1` | `De Communibus Notitiis adversus Stoicos 1` |
| `passage_plut_cn_2` | `cbea7bff-8674-4b2a-9e91-2be555ae40c9` | `2` | `De Communibus Notitiis adversus Stoicos 2` |
| `passage_plut_cn_3` | `2236e0eb-3fdb-473f-8053-da7a4d2c042d` | `3` | `De Communibus Notitiis adversus Stoicos 3` |
| `passage_plut_cn_4` | `1491dca2-426f-486a-9340-e1340ce64110` | `4` | `De Communibus Notitiis adversus Stoicos 4` |
| `passage_plut_cn_5` | `06aa0904-ec48-4d51-a70f-f92548670896` | `5` | `De Communibus Notitiis adversus Stoicos 5` |
| `passage_plut_cn_6` | `693256f2-5aa2-4a9e-9cda-6fc00136963a` | `6` | `De Communibus Notitiis adversus Stoicos 6` |

Le plan refuse tout autre résidu : les six IDs, le champ
`canonical_ref`, la raison `locus_mismatch` et le compte sont tous assertés.

## Mutations projetées

- 975 `metadata.canonical_ref` KG ;
- 1 470 `metadata.cts_urn` KG ;
- 172 `cts_urn` corpus (Philon seulement) ;
- 292 retraits de faux `db_passage_id` ;
- 289 `related_corpus_passage_id` et 3 `former_corpus_passage_id` ;
- 2 084 stamps KG et 172 stamps corpus ;
- aucune ligne ajoutée/supprimée, aucun ordre modifié ;
- chaque ligne JSONL inchangée est rendue byte pour byte depuis la source ;
- zéro changement de `description`, `text_content` ou citation.

## Applicateur et garanties

Livrables :

- `scripts/data_2026_08_18_parity_zero.py` : classification, preuves,
  cardinalités, empreintes et plan ;
- `scripts/apply_2026_08_18_parity_zero.py` : dry-run par défaut,
  `--write` explicite, sauvegardes et remplacement atomique par fichier.

L'applicateur vérifie avant mutation les SHA-256 conjoints de `nodes.jsonl`,
`passages.jsonl` et `citations.jsonl`, les empreintes de sept sources d'audit,
la métadonnée complète de chaque nœud, la ligne corpus complète, le texte du
nœud, la citation exacte et le snapshot relié. Après simulation il exige :

- le compte `3 051 → 6` et les six IDs exclus exacts ;
- aucune nouvelle violation ;
- le digest combiné des textes anciens inchangé ;
- `citations.jsonl` byte pour byte inchangé ;
- une seconde passe entièrement no-op ;
- les empreintes d'output déterministes.

En `--write`, les sauvegardes sont :

- `data/kg/nodes.jsonl.bak-parity_zero_2026_08_18` ;
- `data/corpus/passages.jsonl.bak-parity_zero_2026_08_18`.

Les deux doivent être absentes avant écriture. Une erreur pendant le
remplacement restaure automatiquement les deux fichiers depuis ces copies.

## Dry-run vérifié

```text
plan: nodes=2084, violations_fixed=3045
  demote_false_twin: 292
  sync_corpus_from_kg: 172
  sync_node_from_corpus: 1620
after: violations=6 (cts_urn=0, canonical_ref=6, missing_twins=0)
ancient text changed: 0
citations changed: 0
second pass changed: 0
```

Après application coordonnée avec l'adjudication Plutarque, la baseline
`data/audit/kg_corpus_parity_baseline.json` devra être régénérée depuis les
données effectivement écrites ; ce livrable ne modifie pas cette baseline
partagée.
