---
date: 2026-05-16
status: Phase 1 closure
context: Stoic primary corpus enrichment for DHQ article on Carneadean attribution test
relates_to: docs/superpowers/plans/2026-05-16-amand-piste1-article-implementation.md
---

# Stoic primary corpus — Phase 1 enrichment summary

Phase 1 du plan d'article DHQ vise à combler les manques du corpus stoïcien
primaire afin que l'algorithme de provenance Carnéade→patristique (Phase 2)
ait des données suffisantes pour produire la matrice 6×4 attendue.

## Pre-enrichment baseline (T1, commit `05a5532e`)

| Auteur | Args | Passages | Shells de travail | Notes |
| --- | --- | --- | --- | --- |
| Chrysippus | 19 | 0 | 1 (SVF II vide) | aucune fragment ingéré |
| Cleanthes | 1 | 0 | 1 (Hymn vide) | aucun texte primaire |
| Posidonius | — | 0 testimonia wirés | — | edelstein-kidd sous copyright |
| Panaetius | 1 | — | — | corpus quasi inexistant |

État jugé bloquant pour l'algorithme : le test conceptuel et le test textuel
ne pouvaient pas s'appuyer sur des passages primaires côté source.

## Post-enrichment final state

### Chrysippus (T2)

- 19 args + **88 SVF II passages** (§913-1000)
- Source : OGL First1KGreek TEI `tlg1264.tlg001` (Stoicorum Veterum
  Fragmenta II, von Arnim 1903)
- Couvre les fragments centraux sur la συμπάθεια, la συγκατάθεσις, le
  destin, le cylindre, la causalité enchaînée
- Commits : `cca8141a` (ingestion) + `de108e0e` (polish edges)

### Cleanthes (T3)

- 1 arg + **51 passages** :
  - 1 passage Hymn complet (`passage_cleanthes_hymn_complete`)
  - 39 lignes Hymn individuelles
  - 11 fragments SVF I (§493 sq.)
- Source : OGL First1KGreek TEI `tlg1269.tlg002`
- Le pont est désormais fait entre le matériau de la première Stoa et les
  testimonia plus tardifs (Plutarque, Sextus, DL VII)
- Commit : `77d33907`

### Posidonius (T4 + T5)

- T4 : 0 → 27 testimonia (commit `68f00997`, keyword Latin `posidoni`)
- T5 (Greek pass) : 27 → **64 testimonia** wirés par script
  (`scripts/wire_posidonius_testimonia.py`) + 2 testimonia pré-existants
  hors keyword (1 synthèse Amand 1945, 1 fragment SVF II citant
  Posidonius en grec polytonic)
- Total final : **66 edges `discusses → person_posidonius_apameia_135_51bce`**

Distribution finale :

| Auteur cité | Nb testimonia |
| --- | --- |
| Diogène Laërce VII (DL Lives) | 32 |
| Sénèque | 21 |
| Cicéron | 5 |
| Augustin | 2 |
| Sextus Empiricus | 2 |
| Eusèbe (PE XV) | 1 |
| Plutarque (CN) | 1 |
| Chrysippus SVF II §915 | 1 |
| Synthèse Amand 1945 | 1 |

Ajouts T5 : 37 nouveaux edges, dont l'essentiel vient de DL VII (déjà
ingéré dans le KG mais introuvable au keyword Latin parce que le nom de
Posidonius y est toujours écrit en grec, `Ποσειδώνιος` / `Ποσειδωνίου` /
`Ποσειδωνίῳ` / `Ποσειδώνιον`).

#### Keyword design (T5)

Le keyword Greek discriminant est **`ποσειδωνι`** (et sa variante accentuée
`ποσειδώνι`). Ce stem `-ωνι-` distingue le **philosophe** (déclinaison du
suffixe `-ώνι-ος`) du **dieu Poséidon** (`Ποσειδῶν` / `Ποσειδῶνος` /
`Ποσειδῶνι`, où `ω` est toujours suivi directement d'un `ν`).

Sur les 41 matches Greek bruts, 2 faux positifs identifiés et exclus
manuellement :

- `passage_dl_lives_5_4_73` : esclave affranchi nommé Posidonius dans le
  testament de Lycon de Troas.
- `sc20_theophilus_ad_autolycum_…_chap_7` : Théophile énumère des noms
  dérivés de divinités (« Apolloniuses, Posidoniuses… »).

Les deux sont consignés dans `_EXCLUDED_PASSAGE_IDS` du script.

#### Sources non ingérées (gap documenté)

- **Diogène Laërce livre VII (passages `passage_dl_lives_7_*`)** est en
  réalité présent dans le KG (vérifié à T5) — c'est le keyword Latin
  qui manquait, pas la source.
- **Galen DPP** : 3 passages présents (`passage_galen_plac_1..3`) mais
  aucun ne mentionne Posidonius (extraits sur l'âme/nutrition sans
  référence onomastique). Pas de wiring possible sans ingérer les livres
  IV-V de De Placitis (où Galien discute la psychologie posidonienne).
- **Edelstein-Kidd 1972** : sous copyright, exclu.

### Panaetius

- Toujours 1 arg seul. Decision : **acceptable pour le scope de l'article.**
- Panaetius (c. 185-c. 109 BCE) est post-Carnéade (214-129 BCE) et donc
  hors du test de transmission Carnéade→patristique côté source.
- Sa rareté documentaire (perte quasi totale de l'œuvre) ne peut pas être
  comblée sans ingérer Cicéron *De Officiis* (déjà partiellement présent)
  comme conteneur de testimonia, hors scope de Phase 1.

## Final KG totals

```
Triples : 200,234
Nodes   : 20,071
Edges   : 47,518
```

(comptés via `eleutheria_kg.semantic.build_graph` sur les snapshots JSONL
post-T5)

## Validation

| Check | Résultat |
| --- | --- |
| SHACL invariants (`invariants/`) | conforms ✓ |
| SHACL FULL (`invariants/` + `quality/`) | non-conforming — 128 warnings (severity `warning`) |
| Tests KG (`knowledge graph/tests/`) | **141 passed** in 10.13s |

### Détail des 128 warnings SHACL

Tous sont severity `warning` (donc backlog qualité, pas blocking) :

| Count | Shape |
| --- | --- |
| 58 | `Shape_Passage_PassageRoleProp` (passages sans rôle déclaré) |
| 28 | `Shape_Argument_DescriptionHygieneProp` |
| 28 | `Shape_Concept_DescriptionHygieneProp` |
| 5 | `Shape_School_NeedsEvidence` |
| 5 | `Shape_Group_NeedsEvidence` |
| 3 | `Shape_Synthesis_DescriptionHygieneProp` |
| 1 | `Shape_Debate_DescriptionHygieneProp` |

Aucune violation n'est introduite par Phase 1 : ces warnings sont
préexistants à T1 (vérifié comparativement, distribution stable depuis
`05a5532e`).

## Next : Phase 2 (Provenance Analyzer T6-T10)

Le corpus stoïcien primaire est désormais suffisant pour les 3 tests de
l'algorithme de provenance Carnéadienne :

1. **Test thématique** : intersection topic Carnéade ↔ topic patristique,
   contrôlée contre Chrysippus/Cleanthes/Posidonius/Panétius (Phase 1
   garantit le corpus de contrôle existe).
2. **Test conceptuel** : surface des concepts spécifiques (`prohairesis`,
   `synkatathesis`, `eph'hēmin`, swerve, `συμπάθεια`) côté témoin et
   côté Carnéade ; les passages SVF II / Hymn / DL VII fournissent
   l'ancrage stoïcien.
3. **Test textuel** : matchs lemmatiques sur les passages primaires
   (SVF II §913-1000 + Cleanthes Hymn + 66 testimonia Posidonius).

Phase 2 produira la matrice 6×4 (6 patristiques × 4 catégories de
preuve) et le draft des figures heatmap (T11) et case study (T12).
