# Plan de réparation de la couche de données — audit à froid du 17 août 2026

## Statut et règle d'exécution

Ce lot est **préparé et validé en dry-run uniquement**. Aucun fichier de
`data/kg/` ou `data/corpus/` n'a été écrit. Le script d'application exige
explicitement `--write`; sans cette option, toutes les transformations restent
en mémoire.

Fichiers opérationnels :

- `scripts/data_2026_08_17_cold_audit_data_repairs.py` : preuves, ancres et
  sélecteurs déterministes ;
- `scripts/apply_2026_08_17_cold_audit_data_repairs.py` : applier idempotent,
  dry-run par défaut, préconditions, sauvegardes et invariants ;
- `scripts/check_kg_corpus_locus_parity.py` : gate de parité exacte des loci
  pour les jumeaux déclarés par `metadata.db_passage_id` ;
- `scripts/check_corpus_invariants.py` : gate étendu aux doublons de
  `passage_id` et de triplet de citation.

## Revalidation des constats depuis les données actives

| Finding | Recalcul indépendant | Verdict |
|---|---:|---|
| C-01, Plotin | 709 nœuds remappés, 709 citations une-à-une et 709 jumeaux corpus ; 709 divergences de `canonical_ref` et 709 de `cts_urn` | confirmé |
| H-01, Fédou | 29 lignes redérivées par `author=Michel Fédou` et discordance titre/abstract ; 28 abstracts français identiques sur le *Traité sur la prière*, un abstract espagnol de même sujet, aucun titre correspondant | confirmé sans liste ni total codés en dur |
| H-01, Sytsma | la dissertation 2018 a trois arêtes et l'identifiant Origenality `OR04b4c9130080` ; le nœud 2020 contient déjà `phd_version`, le PDF lu et douze arguments paginés | doublon confirmé |
| H-03, Simplicius | neuf citations pointent à la fois vers neuf passages et neuf nœuds absents, exactement les identifiants Theophraste supprimés par le lot linguistique | suppression, pas repointage |
| H-05, Simplicius | `canonical_id=tlg4013.tlg001`, référence vérifiée TLG 4013, mais `work_canonical_id=tlg0093.tlg001` hérité des passages botaniques supprimés | confirmé |
| H-05, Galien | les trois textes sont les livres complets 1, 2 et 3 du *De naturalibus facultatibus*, TLG 0057.010, et non du *De placitis*, TLG 0057.032 | réadjudication certaine |
| H-08, Methodius | 97 lignes corpus consécutives portent l'URN Sosiphanes `tlg0338.tlg307...:1.1`; elles ont 97 jumeaux KG déclarés. Les 104 liens vus dans un comptage naïf incluent sept seconds nœuds KG, pas sept lignes corpus supplémentaires | population de 97 confirmée |
| M-01, citations | 129 groupes exacts de taille deux, donc 129 lignes excédentaires ; les mêmes 129 violent l'unicité `(passage_id, kg_node_id, citation_type)` | confirmé |
| M-04, stats | `data/stats.json` annonçait 49 391 arêtes au lieu de 49 468 | dérive confirmée |
| M-04, `--check` | le mode existait déjà dans `gen_stats.py`, contrairement à la formulation de la mission ; il ne contrôlait que le JSON et n'était pas appelé par la CI | faux positif partiel, lacune CI confirmée |

### Preuve primaire pour Galien

La table locale `TLG0057.IDT` nomme l'œuvre 010 *De naturalibus
facultatibus*. Le texte primaire OpenGreekAndLatin
[`tlg0057.tlg010.1st1K-grc1.xml`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/master/data/tlg0057/tlg010/tlg0057.tlg010.1st1K-grc1.xml)
porte ce titre dans son en-tête et donne les trois ouvertures conservées dans
le KG :

- livre 1 : `Ἐπειδὴ τὸ μὲν αἰσθάνεσθαί τε...` ;
- livre 2 : `Ὅτι μὲν οὖν ἀναγκαῖόν ἐστιν οὐκ Ἐρασιστράτῳ...` ;
- livre 3 : `Ὅτι μὲν οὖν, ἡ θρέψις ἀλλοιουμένου τε...`.

Les descriptions KG et les textes corpus sont en outre figés par six
SHA-256 distincts dans le payload. La correction peut donc être appliquée
sans conjecture : création de `work_galen_de_naturalibus_facultatibus`,
relogement des trois livres, correction de leurs labels/loci et maintien de
`work_galen_de_placitis` comme œuvre TLG 0057.032 sans texte, marquée
`needs_text_ingestion`.

## Transformations prévues

### 1. Parité Plotin

Pour chacun des 709 records du payload Plotin existant :

1. vérifier le SHA-256 de la description, les offsets TLG demi-ouverts, le
   `db_passage_id` et l'unique citation de jumeau ;
2. recopier dans `passages.jsonl` le `canonical_ref` et le `cts_urn` déjà
   corrigés dans le KG ;
3. ne modifier ni texte grec ni identifiant de citation.

`citations.jsonl` ne possède aucun champ de locus à recopier. Il sert de
précondition de liaison : les 709 couples doivent exister exactement une fois
et sont conservés.

### 2. Quarantaine Origenality et fusion Sytsma

Les notices Fédou ne sont pas supprimées : elles deviennent interrogeables
comme dette mais non utilisables en synthèse, avec :

- `origenality_relevance="reject"` ;
- `integrity_status="origenality_bibliographic_span_contamination"` ;
- motif de quarantaine et stamp daté.

La dissertation Sytsma 2018 est fusionnée au nœud 2020 : transfert de
l'identifiant Origenality, de la notice comme `edition_aliases/phd_version` et
des deux arêtes `discusses`; l'arête `authored_by` devenue dupliquée est
abandonnée. Le nœud 2018 et toute arête résiduelle sont supprimés.

### 3. Citations Simplicius/Theophraste et gate strict

Les neuf citations ne peuvent être repointées : leurs textes étaient
*Historia plantarum* et ont été volontairement retirés du graphe. L'applier
exige que chaque ligne appartienne simultanément aux neuf anciens nœuds et aux
neuf anciens UUID corpus avant suppression.

Le gate strict exige ensuite :

- aucun `citation -> passage` pendant ;
- aucun `citation -> kg_node` pendant ;
- unicité de `passage_id` ;
- unicité de `(passage_id, kg_node_id, citation_type)`.

La CI appelle désormais ce gate avec `--strict`.

### 4. Identifiants d'œuvre

- Simplicius : retrait de `work_canonical_id=tlg0093.tlg001` et de la note de
  dérivation devenue fausse; maintien de `canonical_id=tlg4013.tlg001`.
- Galien : retrait de `work_canonical_id=tlg0057.tlg010` du nœud *De placitis*,
  création de l'œuvre *De naturalibus facultatibus* TLG 0057.010, relogement
  des trois livres et correction identique de leurs jumeaux corpus.

### 5. Methodius : URN d'œuvre et span de source

Les 97 faux URN de passage deviennent
`urn:cts:greekLit:tlg2959.tlg002`, au niveau œuvre. Chaque ligne corpus et son
jumeau KG reçoivent un identifiant stable et unique du type
`gcs27:methodius-de-autexousio:pg18.NNN`. Le `work_canonical_id` est aligné sur
l'œuvre 002, y compris dans le manifest corpus. Aucun locus CTS précis n'est
inventé.

### 6. Dédoublonnage et statistiques

Le premier exemplaire de chaque ligne de citation exacte est conservé dans
l'ordre du fichier; les 129 seconds exemplaires sont retirés. Les notes ou
types différents ne sont pas fusionnés par cette vague.

`gen_stats.py --check` contrôle désormais `data/stats.json` **et**
`data/stats.md`; la CI l'exécute. Les deux fichiers dérivés ont été régénérés
depuis l'état actif non appliqué (19 994 nœuds, 49 468 arêtes, 19 917
citations). Lors d'une future application, l'applier les régénérera dans la
même écriture, avec 19 779 citations.

## Sauvegardes, atomicité et invariants

Avant toute future écriture, l'applier sauvegarde chaque cible existante avec
le suffixe `.bak-cold_audit_data_repairs_2026_08_17`, puis remplace les fichiers
par renommage atomique. Les invariants sont calculés avant l'écriture :

- identifiants de nœuds et de passages uniques ;
- aucune arête pendante, aucun endpoint dédoublé `source/source_id` ;
- aucun triplet d'arête dupliqué ;
- aucune citation pendante ou triplet de citation dupliqué ;
- aucun texte ou description existante modifié ;
- 709 jumeaux Plotin et 97 jumeaux Methodius complets ;
- 809 paires de loci du périmètre strictement identiques ;
- fusion Sytsma, quarantaine Fédou et relogement Galien complets ;
- second passage idempotent à zéro changement.

## Portée du gate de parité

Le mode global en lecture seule trouve actuellement 10 933 jumeaux déclarés,
5 978 divergences de locus et 78 `db_passage_id` sans ligne corpus. Cette dette
historique dépasse la mission. La CI rend donc bloquant le sous-ensemble
explicitement réparé : Plotin, Methodius et Galien, soit 809 jumeaux. Le script
sans `--node-prefix` continue à publier le diagnostic global et permettra de
réduire ensuite la dette sans la masquer.

## Sortie du dry-run du 17 août 2026

```text
mode: dry-run
rows: nodes 19994 -> 19994; edges 49468 -> 49468; passages 21103 -> 21103; citations 19917 -> 19779
changes:
  exact_citation_rows_deduplicated: 129
  fedou_quarantined: 29
  galen_edges_created: 1
  galen_part_of_edges_rewired: 3
  galen_passage_twins_fixed: 3
  galen_work_nodes_created: 1
  methodius_corpus_spans_fixed: 97
  methodius_kg_twins_fixed: 97
  methodius_manifest_fixed: 1
  plotinus_corpus_twins: 709
  simplicius_work_ids_fixed: 1
  sytsma_duplicate_edges_dropped: 1
  sytsma_edges_rewired: 2
  sytsma_nodes_merged: 1
  theophrastus_dangling_citations_removed: 9
derived populations: Fédou=29; Methodius=97; Plotinus=709; Galen=3
invariants: OK (nodes=19994; edges=49468; passages=21103; citations=19779; dangling edges=0; dangling citations=0; duplicate citation rows=0; locus pairs=809; Methodius spans=97)
predicted stats: nodes=19994 edges=49468 works=250 publications=517 passages=21103 citations=19779
idempotence: OK (second pass: 0 changes)
write: disabled (--dry-run default)
```

## Commandes

Validation sans écriture :

```bash
python3 scripts/apply_2026_08_17_cold_audit_data_repairs.py
python3 scripts/gen_stats.py --check
python3 -m pytest tests/test_check_corpus_invariants.py tests/test_check_kg_corpus_locus_parity.py -q
```

Application ultérieure, seulement après validation explicite :

```bash
python3 scripts/apply_2026_08_17_cold_audit_data_repairs.py --write
python3 -m scripts.check_corpus_invariants --strict
python3 scripts/check_kg_corpus_locus_parity.py --strict \
  --node-prefix passage_plotinus_vi_9_ \
  --node-prefix passage_meth_dla_ \
  --node-prefix passage_galen_plac_
python3 scripts/gen_stats.py --check
```
