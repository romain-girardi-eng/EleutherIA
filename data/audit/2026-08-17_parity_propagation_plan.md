# Plan de propagation de parité KG ↔ corpus

Date : 17 août 2026  
Statut : **dry-run seulement ; aucune donnée KG ou corpus appliquée**  
Périmètre d’écriture futur : `data/corpus/passages.jsonl` uniquement ;
`data/kg/*`, les textes anciens et `data/audit/kg_corpus_parity_baseline.json`
restent hors périmètre.

## Résultat exécutif

La jointure du contrôle de déploiement a été reproduite hors ligne : un nœud KG
`type=passage` déclare son jumeau par `metadata.db_passage_id`; ce UUID est joint
à `corpus/passages.jsonl`, puis la paire exacte `(passage_id, kg_node_id)` est
recherchée dans `corpus/citations.jsonl`. `canonical_ref` et `cts_urn` sont enfin
comparés à l’identique. Le calcul reproduit exactement le constat du staged
deploy :

- 11 011 twins déclarés, dont 10 933 résolus ;
- 4 535 violations : 2 640 `cts_urn`, 1 817 `canonical_ref`, 78 twins absents ;
- aucune citation jumelle manquante parmi les 10 933 twins résolus.

Le plan sélectionne 812 lignes de corpus, famille par famille. Il corrige 1 484
violations : 812 URN et 672 références canoniques. Il retire aussi 44
`work_canonical_id` tertullianiques explicitement invalidés par la vague
dialectique. Après application future, 3 051 violations resteront : 1 828 URN,
1 145 références canoniques et 78 twins absents.

## Tableau complet des buckets

`Nœuds` désigne les nœuds KG en violation. Un même passage de corpus peut être
partagé par plusieurs nœuds KG, notamment les paires original/traduction SC.
Dans les colonnes tripartites, l’ordre est `canonical_ref / cts_urn / twin
absent`.

| Famille | Nœuds | Avant (ref / URN / abs.) | Corrigé | Dette conservée (ref / URN / abs.) |
|---|---:|---:|---:|---:|
| Justin Martyr — *Dialogus cum Tryphone* | 750 | 750 / 750 / 0 | 0 | 750 / 750 / 0 |
| Sextus Empiricus — *Against the Professors and Outlines of Pyrrhonism* | 532 | 532 / 532 / 0 | 1 064 | 0 / 0 / 0 |
| Plotin — *Enneades* | 646 | 0 / 646 / 0 | 0 | 0 / 646 / 0 |
| Boèce — *De Consolatione Philosophiae* | 128 | 127 / 128 / 0 | 0 | 127 / 128 / 0 |
| Philon d’Alexandrie — *De Opificio Mundi* | 172 | 1 / 172 / 0 | 0 | 1 / 172 / 0 |
| Platon — *Timaeus* | 76 | 76 / 76 / 0 | 0 | 76 / 76 / 0 |
| Origène — *Exhortatio ad martyrium* | 51 | 51 / 51 / 0 | 102 | 0 / 0 / 0 |
| Augustin — *De Libero Arbitrio* | 93 | 0 / 93 / 0 | 93 | 0 / 0 / 0 |
| Épictète — *Discourses and Enchiridion* | 46 | 46 / 46 / 0 | 91 | 1 / 0 / 0 |
| Justin Martyr — *Apologia Prima* | 68 | 68 / 0 / 0 | 0 | 68 / 0 / 0 |
| Tertullien — *Adversus Praxean* | 31 | 31 / 31 / 0 | 62 | 0 / 0 / 0 |
| Tatien — *Oratio ad Graecos* | 59 | 3 / 0 / 56 | 0 | 3 / 0 / 56 |
| Cicéron — *De Fato* | 48 | 0 / 48 / 0 | 0 | 0 / 48 / 0 |
| Plutarque — *De Stoicorum Repugnantiis* | 47 | 47 / 0 / 0 | 0 | 47 / 0 / 0 |
| Tertullien — *De exhortatione castitatis* | 13 | 13 / 13 / 0 | 26 | 0 / 0 / 0 |
| Augustin — *De Gratia et Libero Arbitrio* | 25 | 0 / 25 / 0 | 25 | 0 / 0 / 0 |
| Augustin — *De Correptione et Gratia* | 21 | 0 / 21 / 0 | 21 | 0 / 0 / 0 |
| Athénagore — *Supplique au sujet des chrétiens* | 20 | 20 / 0 / 0 | 0 | 20 / 0 / 0 |
| Ps.-Plutarque — *De fato* | 19 | 0 / 0 / 19 | 0 | 0 / 0 / 19 |
| Justin Martyr — *Apologia Secunda* | 15 | 15 / 0 / 0 | 0 | 15 / 0 / 0 |
| Aristote — *Éthique à Nicomaque* | 12 | 12 / 2 / 0 | 0 | 12 / 2 / 0 |
| Augustin — *De Civitate Dei* V/XII/XIV | 9 | 5 / 6 / 3 | 0 | 5 / 6 / 3 |
| Aspasius — *In Ethica Nicomachea Commentaria* | 6 | 6 / 0 / 0 | 0 | 6 / 0 / 0 |
| Plutarque — *De Communibus Notitiis adversus Stoicos* | 6 | 6 / 0 / 0 | 0 | 6 / 0 / 0 |
| Aristote — *De Generatione et Corruptione* | 3 | 3 / 0 / 0 | 0 | 3 / 0 / 0 |
| Anonyme — *Épître de Barnabé* | 2 | 2 / 0 / 0 | 0 | 2 / 0 / 0 |
| Clément de Rome — *Épître aux Corinthiens* | 2 | 2 / 0 / 0 | 0 | 2 / 0 / 0 |
| Hégésippe — *Hypomnemata* | 1 | 1 / 0 / 0 | 0 | 1 / 0 / 0 |
| **Total** | **2 901** | **1 817 / 2 640 / 78** | **1 484** | **1 145 / 1 828 / 78** |

## Direction de vérité retenue

| Famille de réparation | Lignes | Violations corrigées | Preuve et décision |
|---|---:|---:|---|
| Sextus, remappage TLG E | 532 | 1 064 | `data/audit/primary_wave/chunk_locus_changelog.jsonl` porte pour chaque nœud le couple `from`/`to` et la méthode « TLG E multi-probe text alignment ». Le KG est exactement au `to`; le corpus suit le KG. |
| Épictète, loci TLG E résolus | 45 | 90 | Même journal et même précondition exacte `KG == to`; le corpus suit le KG. |
| Épictète 185, URN défaké | 1 | 1 | Le journal porte `action=locus_defaked` et seulement un `to.urn=urn:cts:greekLit:tlg0557`. L’URN suit ce verdict; la référence `Epict. 185` reste en dette, car le journal dit que le locus n’est pas résolu. |
| Augustin, *De libero arbitrio* | 93 | 93 | L’adjudication dans `scripts/data_2026_08_17_semantic_merges.py` établit les 170 URN `passage_aug_dla_*` comme correctes 170/170 et comme jumeaux primaires. Les 93 URN de corpus en mauvais livre suivent ces nœuds. |
| Augustin, *De gratia* | 25 | 25 | `urn_fix_changelog.jsonl`, `kind=book_section_style`; le KG est exactement au `to`. |
| Augustin, *De correptione* | 21 | 21 | `urn_fix_changelog.jsonl`, `kind=pl44_prefix`; `PL44` est un repère éditorial retiré du composant passage. |
| Origène, *Exhortatio ad martyrium* | 51 | 102 | Stamp `linguistic_repairs_2026_08_17=reattribute_exhortatio`, TLG2042.IDT œuvre 007 et formule d’adresse unique à Ambroise et Protoctète. Les valeurs `Protr. N` du corpus sont l’ancien classement Clément; le corpus reçoit `Exh. mart. N` et l’URN KG. Aucun basculement vers `tlg0555` n’est permis. |
| Tertullien, deux réattributions | 44 | 88 | Stamp `dialectical_repairs_2026_08_17=tert_reattribute`. Les 13 *De exhortatione castitatis* ont été collationnés contre SC 319; les 31 *Adversus Praxean* sont établis par contenu, structure et collation négative contre *De anima*. Les anciens URN et `work_canonical_id` ont été explicitement retirés du KG faute d’identifiant vérifié; le corpus suit ce retrait. |

Le total comporte 812 lignes distinctes : aucune ligne n’est sélectionnée par
deux familles. Les changements sont limités à `canonical_ref`, `cts_urn`, au
retrait de `work_canonical_id` pour les 44 lignes tertullianiques, et au stamp
idempotent `parity_propagation_2026_08_17`. `text_content` n’est jamais modifié.

## Familles auditées déjà à parité

- Le remappage Plotin `passage_plotinus_vi_9_*` : 709/709 twins déclarés sont
  déjà alignés. Les 646 écarts Plotin du tableau appartiennent à l’ancienne
  famille `passage_plotinus_i_*`–`vi_*`, dont l’URN KG est souvent limitée au
  livre alors que le corpus porte le passage complet; ils ne portent pas le
  stamp du remappage du 17 août.
- Magna Moralia : 434/434 twins alignés.
- Suppression des placeholders `:?.` de Platon : 445/445 twins alignés; les 152
  écarts du *Timée* sont une autre famille (préfixe de titre et version
  d’édition), sans stamp de cette réparation.
- Méthode : 97 twins déclarés sur 111 nœuds sont alignés sur l’URN d’œuvre
  `tlg2959.tlg002` plus `source_span_id`; cette démotion est intentionnelle et
  n’est pas remontée vers un faux URN de passage. Les 14 autres nœuds ne
  déclarent pas de `db_passage_id`.
- Les six nœuds authentiquement clémentins en `tlg0555` ne déclarent pas de
  twin corpus et sont donc hors cohorte de parité.

## Dette conservée et raisons

- *Dialogus cum Tryphone* : `_` côté KG contre `.` côté corpus dans 750 loci.
  Aucun stamp n’adjuge la syntaxe; pas de normalisation globale.
- Ancienne famille Plotin : URN de livre/chapitre côté KG contre URN de passage
  côté corpus. Elle ne doit pas être confondue avec les 709 fragments remappés.
- Boèce : le stamp de fusion sémantique prouve une fusion de nœuds, pas une
  autorité de locus. Les UUID portés mettent `Cons. N` en face de divisions
  `book.M/P`; sans collation locale disponible, aucune direction n’est sûre.
- Philon : divergence de version `opp-grc1` / `1st1K-grc1`; le locus numérique
  est généralement identique, mais choisir une édition est une décision
  bibliographique non estampillée.
- *Timée*, Justin I/II, Plutarque, Aspasius et les passages SC : différences de
  forme courte/longue ou de version d’édition. Les références SC peuvent en
  outre relier deux nœuds KG linguistiques au même passage de corpus. La parité
  exacte ne suffit pas à établir quelle représentation doit gagner.
- Cicéron : conflit réel `phi0474.phi056` / `phi0474.phi054`; aucun registre
  local audité n’est attaché à ces lignes. Il est laissé ouvert.
- Aristote : les références Bekker détaillées du corpus et les numéros de
  chapitres KG ne sont pas interchangeables sans décision de précision; les
  trois *De generatione* opposent même des chunks `1..3` aux loci II.9–11.
- Augustin, *De civitate Dei* : cinq formats de référence, six URN nulles ou
  divergentes et trois déclarations vers des lignes supprimées. Les nœuds sont
  déjà signalés comme contenu non textuel ou non collationné; aucune valeur
  n’est inventée.
- Hégésippe : la correction de mauvais auteur/ouvrage ne prouve pas que
  `Didasc. 1` soit la référence canonique du nœud, actuellement nulle.

## Les 78 twins absents

| Cause | Nœuds | État observé | Décision |
|---|---:|---|---|
| Tatien, segmentation fine | 56 | Les 56 UUID `db_passage_id` sont absents du corpus courant et des cinq sauvegardes disponibles. Chaque nœud a une citation vers une ligne actuelle; ces citations convergent vers 37 passages plus grossiers, généralement au chapitre. | Dette documentée. Réparer exigerait de modifier `data/kg` ou de dupliquer/resegmenter le texte ancien, tous deux hors périmètre. |
| Ps.-Plutarque, nœuds `_sN` | 19 | Les 19 UUID déclarés sont absents du corpus et des sauvegardes. Les citations existantes convergent vers 11 passages plus grossiers. | Dette documentée pour la même raison; la correction TLG `tlg0007.tlg108` reste valide mais ne résout pas l’identité du twin. |
| Augustin, *De civitate Dei* | 3 | Les trois lignes existaient dans `passages.jsonl.bak-primary_wave`; `restore_changelog.jsonl` enregistre leur suppression comme footer-junk (« Augustine Christian Latin The Latin Library The Classics Page »). Aucune citation actuelle ne les vise. | Suppression intentionnelle confirmée; les pointeurs KG sont obsolètes. Ne pas restaurer du faux texte. |

Il n’existe donc pas de rewire sûr limité à `passages.jsonl` et
`citations.jsonl`. Le bon correctif futur est une opération KG explicite sur
`db_passage_id` après décision de granularité; ce plan n’y touche pas.

## Applicateur et invariants

Les livrables sont :

- `scripts/data_2026_08_17_parity_propagation.py` : décisions de famille,
  preuves, cardinalités, empreintes de l’état audité et construction du plan;
- `scripts/apply_2026_08_17_parity_propagation.py` : dry-run par défaut,
  `--write` explicite, préconditions par ligne, stamp idempotent et sauvegarde
  `passages.jsonl.bak-parity_prop`.

Avant toute écriture, l’applicateur contrôle les empreintes des trois fichiers,
le couple KG attendu, le UUID corpus, l’unique citation jumelle, les anciennes
valeurs de locus et le SHA-256 de `text_content`. Après simulation il contrôle :

- même nombre, même ordre et mêmes `passage_id`;
- aucun champ hors locus/stamp modifié;
- digest de tous les textes anciens inchangé;
- citations byte pour byte inchangées;
- seconde passe entièrement idempotente;
- recomptage complet de parité égal aux valeurs attendues.

En mode `--write`, la sauvegarde est créée avant remplacement atomique. Si elle
existe déjà, l’applicateur s’arrête au lieu de l’écraser. Le fichier de citations
n’étant pas modifié, il n’est ni réécrit ni sauvegardé.

## Sortie du dry-run

Commande exécutée :

```text
python3 scripts/apply_2026_08_17_parity_propagation.py
```

Sortie :

```text
mode: dry-run
source state: baseline
before: violations=4535 (cts_urn=2640, canonical_ref=1817, missing_twins=78, missing_citations=0), declared=11011, shared=10933
plan: rows=812, changed=812, already_applied=0
  augustine_de_correptione_urn: 21 changed
  augustine_de_gratia_urn: 25 changed
  augustine_de_libero_arbitrio: 93 changed
  epictetus_tlge_locus: 45 changed
  epictetus_unresolved_urn_defake: 1 changed
  origen_exhortatio: 51 changed
  sextus_tlge_locus: 532 changed
  tertullian_reattributions: 44 changed
fields: canonical_ref=672, cts_urn=812, work_canonical_id_removed=44
after: violations=3051 (cts_urn=1828, canonical_ref=1145, missing_twins=78, missing_citations=0), declared=11011, shared=10933
invariants: OK (text_digest=c3f1201f0cd3d896205025694bb284dac94fa024a3a6bfa50398fbebbae73ac1; citations_changed=0; second_pass_changed=0; output_sha256=2252296708f07b8cad68cd4a3517d52416586afd84ca25c7c1356028588bbd01)
write: disabled (--dry-run default; use --write to apply)
```

Les lignes `evidence=...` imprimées par le programme ont été omises ci-dessus
pour garder le bloc lisible; elles figurent dans la sortie réelle et reprennent
les preuves du tableau de décision.

## Régénération future de la baseline

Ce travail ne crée ni ne modifie
`data/audit/kg_corpus_parity_baseline.json`. Après une application approuvée, le
job propriétaire de cette baseline devra la régénérer depuis les données
effectivement écrites, après exécution du contrôle complet. Les comptes attendus
sont :

```json
{
  "declared_twins": 11011,
  "shared_twins": 10933,
  "violations": 3051,
  "missing_twins": 78,
  "missing_citations": 0,
  "canonical_ref_mismatches": 1145,
  "cts_urn_mismatches": 1828
}
```

Ces nombres sont une attente de régénération, pas une autorisation de masquer
une différence : si le recomptage post-application diverge, l’application ou la
régénération doit s’arrêter.
