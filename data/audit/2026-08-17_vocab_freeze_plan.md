# Gel des vocabulaires `period` et `school` — plan du 17 août 2026

## Statut

**Livrable dry-run uniquement : aucune écriture n'a été faite dans `data/kg/` ni dans `data/corpus/`.** Le fichier canonique `data/kg/nodes.jsonl` conserve son SHA-256 `f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888`. L'application destructive a été exercée seulement sur une copie sous `/tmp`, avec création et vérification de `nodes.jsonl.bak-vocab`.

Les deux vocabulaires sont gelés en version `1.0.0` dans :

- `knowledge graph/ontology/period_scheme.json` ;
- `knowledge graph/ontology/school_scheme.json`.

La photographie courante contient 19 796 nœuds. Parmi eux, 19 711 ont une valeur `period` non nulle et 16 078 une valeur `school` non nulle. Les chiffres ont légèrement évolué depuis `data/audit/2026-08-16_deep_audit_semantic.jsonl` : ce plan décrit et préconditionne l'état réellement lu le 17 août, sans recopier les totaux devenus obsolètes de l'audit.

## 1. Inventaire du vocabulaire `period`

Décision : **aucune migration de période**. Les quinze valeurs observées sont toutes retenues, y compris `First Temple / Pre-exilic Judaism`, absente de l'ancienne liste en dur.

| Valeur retenue | Nœuds | Bornes conventionnelles du schéma |
|---|---:|---|
| Roman Imperial | 11 220 | 31 BCE–284 CE |
| Late Antiquity | 2 101 | 284–641 CE |
| Classical Greek | 2 089 | 480–323 BCE |
| Contemporary | 1 514 | 1945 CE–présent |
| Patristic | 1 362 | c. 100–750 CE |
| Hellenistic | 465 | 323–31 BCE |
| Roman Republican | 408 | 509–31 BCE |
| Modern | 362 | c. 1800–1945 CE |
| Early Modern | 79 | c. 1500–1800 CE |
| Medieval | 54 | c. 500–1500 CE |
| Second Temple Judaism | 29 | 516 BCE–70 CE |
| Presocratic | 13 | c. 600–400 BCE |
| Cross-period | 11 | sans bornes |
| Rabbinic | 2 | c. 70–600 CE |
| First Temple / Pre-exilic Judaism | 2 | c. 1000–586 BCE |
| **Total non nul** | **19 711** | **15 valeurs** |

### Convention historiographique

Le schéma énonce la convention au lieu de présenter les bornes comme universelles. La séquence grecque suit les limites usuelles 480–323 et 323–31 BCE documentées par le Metropolitan Museum : [Classical Greece](https://www.metmuseum.org/essays/the-art-of-classical-greece-ca-480-323-b-c) et [Hellenistic intellectual history](https://www.metmuseum.org/essays/intellectual-pursuits-of-the-hellenistic-age). `Roman Imperial` commence à Actium (31 BCE) afin d'assurer la continuité avec ce terminus hellénistique, bien que les histoires constitutionnelles utilisent souvent 27 BCE. Son terminus 284 CE est l'avènement de Dioclétien, césure décrite comme majeure dans la [Cambridge Ancient History](https://www.cambridge.org/core/books/cambridge-ancient-history/diocletian-and-the-first-tetrarchy-ad-284305/9C09DBBB93CC6D3FB4BE2F8E6FDDA96B). `Late Antiquity` emploie ensuite la convention politico-administrative du projet, 284–641 CE, tout en signalant que des périodisations culturelles plus longues existent. `Second Temple Judaism` suit 516 BCE–70 CE, cadre explicité dans l'[ouvrage de Jodi Magness](https://assets.cambridge.org/97805211/95355/excerpt/9780521195355_excerpt.pdf).

Les catégories ne forment pas une partition disjointe : `Patristic` et `Rabbinic` sont des périodes intellectuelles ou textuelles qui recouvrent les chronologies politiques.

### Cas difficiles

- **Philon d'Alexandrie** reste `Roman Imperial`. Le champ `period` suit sa chronologie politique du Ier siècle ; le contexte juif du Second Temple et son alignement platonicien doivent être portés par les métadonnées de tradition et par `school=Platonist`, non par une seconde période concurrente.
- **Boèce** reste `Late Antiquity`, et non `Medieval`, en raison de sa vie c. 477–524 et de son cadre institutionnel romain tardif. `Neoplatonist` reste son école ; le schéma distingue donc chronologie et affiliation.
- **Cross-period** est une catégorie analytique volontairement sans bornes. Elle est réservée aux positions et synthèses explicitement diachroniques, non aux dates inconnues.
- **First Temple / Pre-exilic Judaism** est conservé parce que les données l'emploient. Sa définition précise qu'il s'agit d'un horizon historique grossier, non d'un verdict automatique sur la date de composition finale de chaque livre biblique.

## 2. Inventaire du vocabulaire `school` avant nettoyage

| Valeur observée | Nœuds | Décision du plan |
|---|---:|---|
| Stoic | 3 524 | retenir |
| Christian Platonism | 2 640 | retenir ; +2 Cappadociens |
| Neoplatonist | 1 524 | retenir |
| Platonist | 1 381 | retenir |
| Doxographer | 1 203 | retenir ; +Diogène Laërce, +Aulu-Gelle |
| Peripatetic | 968 | retenir |
| Apologetic | 931 | fusionner vers `Christian Apologetics` |
| Apostolic Fathers | 831 | retenir |
| Christian Apologetics | 745 | retenir comme cible canonique |
| Christian | 694 | retenir, emploi générique limité |
| Skeptic | 534 | retenir ; +Arcésilas |
| Epicurean | 496 | retenir |
| Latin Patristic | 245 | retenir |
| Patristic | 222 | retenir ; +Maxime |
| Antiochene School | 53 | retenir |
| Various | 49 | retenir ; +Galien |
| Middle Platonist | 29 | retenir |
| Eclectic | 2 | résoudre par nœud, puis supprimer |
| Academic (New Academy) | 1 | `Skeptic` |
| Cynicism | 1 | `Cynic` |
| None (doxographer) | 1 | `Doxographer` |
| Cappadocian Fathers | 1 | `Christian Platonism` |
| Nicene orthodoxy | 1 | `Christian Platonism` |
| Presocratic | 1 | `Presocratic Philosophy` |
| Neo-Chalcedonian / Byzantine Patristic | 1 | `Patristic` |
| **Total non nul** | **16 078** | **25 valeurs avant / 18 après** |

L'audit parlait de « huit hapax » ; techniquement il s'agit de huit **familles rares** et de neuf nœuds, car `Eclectic` est porté par deux personnes. Le plan ne masque pas cette différence.

## 3. Vocabulaire `school` retenu après simulation

| Valeur `1.0.0` | Effectif projeté | Portée résumée |
|---|---:|---|
| Stoic | 3 524 | école stoïcienne |
| Christian Platonism | 2 642 | appropriation chrétienne du platonisme |
| Christian Apologetics | 1 676 | discours et corpus apologétiques chrétiens |
| Neoplatonist | 1 524 | tradition néoplatonicienne tardive |
| Platonist | 1 381 | platonisme large, sans sous-classe assurée |
| Doxographer | 1 205 | rôle de compilation/transmission doxographique |
| Peripatetic | 968 | tradition aristotélicienne/péripatéticienne |
| Apostolic Fathers | 831 | groupement éditorial des Pères apostoliques |
| Christian | 694 | affiliation chrétienne générique mais attestée |
| Skeptic | 535 | scepticismes académique et pyrrhonien, distinctions en métadonnées |
| Epicurean | 496 | école épicurienne |
| Latin Patristic | 245 | branche latine de la tradition patristique |
| Patristic | 223 | tradition patristique large |
| Antiochene School | 53 | réseau/tendance exégétique d'Antioche |
| Various | 50 | pluralité explicitement attestée, jamais « inconnu » |
| Middle Platonist | 29 | phase médio-platonicienne |
| Cynic | 1 | affiliation cynique d'une personne |
| Presocratic Philosophy | 1 | regroupement philosophique présocratique |
| **Total** | **16 078** | **18 valeurs** |

Chaque concept possède dans `school_scheme.json` une définition anglaise en un paragraphe, une note de portée, un effectif avant/après et, lorsque c'est historiographiquement pertinent, une plage chronologique. Les catégories héritées qui ne sont pas des écoles institutionnelles au sens strict (`Doxographer`, `Apostolic Fathers`, `Various`) sont conservées parce qu'elles structurent réellement le corpus, mais leur statut fonctionnel ou éditorial est déclaré explicitement.

## 4. Réparations rares : préconditions et preuves

Toutes les décisions ci-dessous sont des entrées exécutables de `scripts/data_2026_08_17_vocab_freeze.py`. L'applier refuse de continuer si l'identifiant, la valeur source, `metadata.school`, le type, la période, le fragment de description ou une arête probante attendue a changé.

| Nœud | Avant → après | Précondition/preuve décisive | Alternative conservée |
|---|---|---|---|
| `person_arcesilaus_316_241bce` | Academic (New Academy) → Skeptic | description « Founder of the New (skeptical) Academy » ; arêtes `member_of` vers `school_academics` et `school_academy_middle` | Academic (New Academy), Academic (Middle Academy) |
| `person_aulus_gellius_125_180ce` | Eclectic → Doxographer | description « Roman miscellanist and doxographer » et rôle explicite de transmetteur, non de philosophe original | Eclectic |
| `person_galen_pergamon_129_216ce` | Eclectic → Various | description : synthèse de Plato, Aristotle et Hippocrates sans affiliation unique | Eclectic |
| `person_crescens_cynic_2c_ce` | Cynicism → Cynic | label, description « Cynic philosopher active in Rome » et références Justin/Tatien/Eusèbe | Cynicism |
| `person_diogenes_laertius_3c_ce` | None (doxographer) → Doxographer | description « Greek doxographer » ; suppression d'une sentinelle textuelle | None (doxographer) |
| `person_gregory_nazianzus_d389` | Cappadocian Fathers → Christian Platonism | Père cappadocien ; collaboration origénienne avec Basile dans la *Philocalia* | Cappadocian Fathers |
| `person_gregory_nyssa_d395` | Nicene orthodoxy → Christian Platonism | le nœud dit explicitement « Christian Platonist and mystic of Origenist inspiration » et Père cappadocien | Nicene orthodoxy, Cappadocian Fathers |
| `person_heraclitus_fl500bce_a1b2c3d4` | Presocratic → Presocratic Philosophy | `Presocratic` est déjà sa période ; arête `member_of` vers `school_presocratic`, libellé « Presocratic Philosophy » | Presocratic |
| `person_maximus_confessor_d662` | Neo-Chalcedonian / Byzantine Patristic → Patristic | arête probante `member_of` vers `school_christian_patristic` | Neo-Chalcedonian / Byzantine Patristic |

### Choix cappadocien

Les deux Grégoire reçoivent **une seule valeur d'école, `Christian Platonism`**. C'est directement formulé dans le nœud de Grégoire de Nysse ; celui de Nazianze atteste le groupe cappadocien et la collaboration origénienne. `Cappadocian Fathers` désigne plus exactement un groupe historique et `Nicene orthodoxy` une position doctrinale : les deux restent dans `school_alternative_labels` au lieu de concurrencer le champ d'école. La différence de `period` (`Late Antiquity` / `Patristic`) n'est pas touchée par cette opération.

## 5. Fusion `Apologetic` → `Christian Apologetics`

La population source est gelée par quatre préconditions : 931 nœuds, tous de type `passage`, tous `Patristic`, répartition Justin Martyr 833 / Tatian 98, et SHA-256 de la liste triée des identifiants `9b93f2710582e3a116bb5cf2292e9098bf7acb215a7cbd788d06df1eabf191d7`. Les œuvres sont également contrôlées : *Dialogus cum Tryphone* 750, *Oratio ad Graecos* 98, *Apologia Prima* 68, *Apologia Secunda* 15.

Justification terminologique : la littérature de référence emploie le syntagme nominal **Christian apologetics** pour le discours défensif et **Christian apologists** pour les auteurs ; `Apologetic` isolé est adjectival ou désigne un mode argumentatif singulier. Voir le chapitre Cambridge [Christian Apologetics](https://www.cambridge.org/core/books/from-jesus-christ-to-christianity/christian-apologetics/0ED30880C60B5F9FCE6D5235C8D5ED93) et Edwards et al., *Apologetics in the Roman Empire* (Oxford, 1999). La cible est donc `Christian Apologetics`, déjà présent comme taxon structuré pour 745 nœuds avant fusion.

## 6. Contrat de l'applier

`scripts/apply_2026_08_17_vocab_freeze.py` :

- est en dry-run par défaut ; `--apply` est nécessaire pour écrire ;
- accepte `--nodes` et `--edges`, ce qui permet une application entièrement confinée à une copie ;
- ne modifie que `school`, `metadata.school`, `metadata.school_alternative_labels` et le sceau `metadata.vocab_freeze_2026_08_17` des 940 nœuds planifiés ;
- conserve la représentation de `metadata` (`dict` ou chaîne JSON) ;
- refuse un état partiellement appliqué ;
- est idempotent : un second passage valide les 940 sceaux et ne change aucune ligne ;
- conserve nombre, ordre et identifiants des 19 796 nœuds ;
- compare la liste complète des valeurs `period` avant/après et impose zéro migration ;
- exige les inventaires gelés avant ou après nettoyage et zéro valeur hors schéma après simulation ;
- écrit atomiquement et crée une seule sauvegarde `<nodes>.bak-vocab`, sans l'écraser lors d'une relance.

## 7. Couche sémantique SKOS et SHACL

Les fichiers JSON restent les seules sources d'autorité. `knowledge graph/src/eleutheria_kg/semantic/vocab.py` les charge et fournit les ensembles contrôlés et les IRI stables :

- `https://free-will.app/vocabulary/period` ;
- `https://free-will.app/vocabulary/school` ;
- concepts sous `.../period/<id>` et `.../school/<id>`.

`rdf_export.py` émet deux `skos:ConceptScheme`, 33 concepts contrôlés avec `skos:prefLabel`, `skos:definition`, `skos:scopeNote`, `skos:notation` et les bornes datées sérialisées. Les littéraux historiques `kg:period` et `kg:school` restent présents pour compatibilité ; les nouveaux liens objet `kg:periodConcept` et `kg:schoolConcept` pointent vers SKOS. Sur le graphe non appliqué, les 940 valeurs `school` hors schéma restent volontairement sans lien conceptuel ; sur la copie appliquée, les 16 078 valeurs non nulles se résolvent toutes.

Le chargeur RDF matérialise par défaut les inverses d'exécution. Un paramètre rétrocompatible `materialize_runtime_inverses=False` permet désormais aux consommateurs de preuves de demander le graphe asserted-only ; `analyze_carneadean_transmission.py` utilise ce mode avant sa propre closure. Ce petit raccord maintient le contrat de reconstruction des chaînes de preuve et restaure son test CI, sans changer le comportement par défaut du chargeur.

`generate_shapes.py` lit désormais les schémas au lieu de recopier une constante de périodes. `quality/formatting.ttl` inclut la quinzième période et les contraintes `school_scheme.json`. Les cinq fichiers générés ont été réémis conformément à la CI ; seul le contenu contrôlé de `quality/formatting.ttl` reçoit la nouvelle liste et les nouvelles shapes d'école.

Commande exacte :

```bash
python3 "knowledge graph/src/eleutheria_kg/semantic/shapes/generate_shapes.py"
```

Une seconde exécution, comparée par SHA-256 à la première, a produit des fichiers byte-identiques.

## 8. R18 — gate d'ingestion

`scripts/check_ingestion_rules.py` charge les deux schémas à chaque contrôle :

- `--new-only` : une valeur non nulle hors schéma est `BLOCK` et entraîne le statut 1 ;
- graphe entier : les dettes sont `WARN`, regroupées par champ et valeur, avec effectif et exemples ;
- une valeur nulle reste autorisée : l'absence responsable est préférable à une sentinelle textuelle.

La documentation est ajoutée à `docs/development/ingestion-rules.md`. Dans l'état dry-run, le graphe entier rapporte neuf valeurs source hors schéma : les huit familles rares, plus `Apologetic`. Après simulation, il n'en reste aucune.

## 9. Sorties de vérification

### Dry-run sur le graphe canonique

Commande :

```bash
python3 scripts/apply_2026_08_17_vocab_freeze.py
```

Sortie :

```text
vocab-freeze: /Users/romaingirardi/Projects/EleutherIA/data/kg/nodes.jsonl
mode: DRY-RUN
nodes: 19796 -> 19796
planned nodes: 940
school assignments changed: 940
metadata.school values changed: 940
already applied: 0
period assignments changed: 0
school values: 25 -> 18
off-scheme before: school='Apologetic' (931), school='Eclectic' (2), school='Academic (New Academy)' (1), school='Cynicism' (1), school='None (doxographer)' (1), school='Cappadocian Fathers' (1), school='Nicene orthodoxy' (1), school='Presocratic' (1), school='Neo-Chalcedonian / Byzantine Patristic' (1)
off-scheme after: none
invariants: OK
--dry-run: nothing written
```

### Application et idempotence sur copie `/tmp` uniquement

Première exécution : 940 valeurs de niveau supérieur et 940 miroirs de métadonnées modifiés ; `25 -> 18`, zéro période modifiée, sauvegarde `.bak-vocab` créée, invariants OK. Deuxième exécution :

```text
mode: DRY-RUN
nodes: 19796 -> 19796
planned nodes: 940
school assignments changed: 0
metadata.school values changed: 0
already applied: 940
period assignments changed: 0
school values: 18 -> 18
off-scheme before: none
off-scheme after: none
invariants: OK
--dry-run: nothing written
```

La sauvegarde de la copie porte le même SHA-256 que le fichier canonique :

```text
f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888  data/kg/nodes.jsonl
f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888  /tmp/.../nodes.jsonl.bak-vocab
```

### R18 en `--new-only`

Fixture locale : un nouveau concept avec `period=Imperial`, `school=Apologetic` et une arête valide.

```text
ingestion-rules: delta of 1 nodes / 1 edges
  [BLOCK] R18_controlled_vocabulary: 2
        period='Imperial': 1 node(s) use an off-scheme period value; examples: concept_r18_invalid_probe
        school='Apologetic': 1 node(s) use an off-scheme school value; examples: concept_r18_invalid_probe

BLOCK: 2   WARN: 0
exit status: 1
```

### R18 sur le graphe entier

```text
[WARN] R18_controlled_vocabulary: 9
  school='Academic (New Academy)': 1
  school='Apologetic': 931
  school='Cappadocian Fathers': 1
  school='Cynicism': 1
  school='Eclectic': 2
  school='Neo-Chalcedonian / Byzantine Patristic': 1
  school='Nicene orthodoxy': 1
  school='None (doxographer)': 1
  school='Presocratic': 1
whole-graph mode: reporting pre-existing debt, not failing
exit status: 0
```

### RDF/SKOS

```text
RDF build: 914790 triples; SKOS schemes=2; controlled concepts=33; periodConcept links=19711; schoolConcept links=15138/16078 school literals
sandbox RDF after simulated apply: periodConcept=19711; schoolConcept=16078; all non-null controlled values resolve
```

### Tests et formatage

Commandes exactes :

```bash
ruff check scripts/data_2026_08_17_vocab_freeze.py scripts/apply_2026_08_17_vocab_freeze.py scripts/check_ingestion_rules.py scripts/audit_kg_quality.py "knowledge graph/src/eleutheria_kg/semantic/vocab.py" "knowledge graph/src/eleutheria_kg/semantic/rdf_export.py" "knowledge graph/src/eleutheria_kg/semantic/shapes/generate_shapes.py" "knowledge graph/tests/unit/test_generate_shapes.py" "knowledge graph/tests/unit/test_vocab_soundness.py" "knowledge graph/tests/unit/test_rdf_export.py" "knowledge graph/tests/unit/test_ingestion_vocab_gate.py"
ruff format --check scripts/data_2026_08_17_vocab_freeze.py scripts/apply_2026_08_17_vocab_freeze.py scripts/check_ingestion_rules.py scripts/audit_kg_quality.py "knowledge graph/src/eleutheria_kg/semantic/vocab.py" "knowledge graph/src/eleutheria_kg/semantic/rdf_export.py" "knowledge graph/src/eleutheria_kg/semantic/shapes/generate_shapes.py" "knowledge graph/tests/unit/test_generate_shapes.py" "knowledge graph/tests/unit/test_vocab_soundness.py" "knowledge graph/tests/unit/test_rdf_export.py" "knowledge graph/tests/unit/test_ingestion_vocab_gate.py"
cd "knowledge graph" && python3 -m pytest tests/unit/test_vocab_soundness.py tests/unit/test_rdf_export.py tests/unit/test_generate_shapes.py tests/unit/test_ingestion_vocab_gate.py -q
cd "knowledge graph" && MPLBACKEND=Agg python3 -m pytest tests/ -q -k 'not test_validation_report_counters_and_markdown and not test_validate_kg_invariants_clean_graph and not test_validate_kg_invariants_catches_domain_violation'
```

Résultats ciblés :

```text
55 passed in 0.43s
ruff: All checks passed
ruff format --check: 11 files already formatted
```

La suite KG large locale a produit `183 passed, 2 skipped, 3 deselected` en 44,97 s. Les trois tests désélectionnés appellent `pyshacl`, absent de l'environnement système ; une tentative d'installation isolée sous `/tmp` a été refusée par l'absence d'accès réseau. La CI installe explicitement `knowledge graph/[dev,semantic]`, qui fournit `pyshacl>=0.31.0`. Le test carnéadien auparavant incompatible avec la matérialisation récente des inverses repasse après l'ajout du mode asserted-only (`1 passed`, puis inclus dans les 183). Les tests qui couvrent directement les schémas, la génération Turtle, l'export RDF/SKOS et R18 passent tous localement.

## 10. État final dry-run

- Schémas `period` et `school` gelés en `1.0.0` : oui.
- Quinze périodes réelles de la donnée retenues : oui.
- Définitions anglaises en un paragraphe et bornes/notes : oui.
- Cas Philon, Boèce et Cross-period documentés : oui.
- Nettoyage `school` préconditionné, prouvé, idempotent et sauvegardé : oui, simulé seulement.
- Migration de période : **0**.
- Écriture dans `data/kg/` ou `data/corpus/` : **0**.
- SKOS intégré au pipeline RDF et shapes régénérées : oui.
- R18 BLOCK/WARN documenté et testé : oui.
