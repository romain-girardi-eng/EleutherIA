# Plan éditorial des six débats centraux — correctif H-06

**Date :** 17 août 2026  
**Statut :** delta validé en dry-run ; rien appliqué  
**Finding traité :** H-06 de `data/audit/2026-08-17_cold_audit_sol.md`

## Résultat exécutif

Le modèle éditorial « débat → positions atomiques → relations attestées →
passages contestés » est proposé pour les six fault lines les plus centrales à
la thèse sur l’émergence du libre arbitre libertarien dans le christianisme
ancien :

1. naissance/découverte de la volonté ;
2. liberté chrétienne contre déterminisme gnostique/valentinien ;
3. grâce et liberté, sur l’axe Origène → Augustin ;
4. Alexandre contre les Stoïciens ;
5. tradition carnéadienne anti-fataliste/anti-astrologique ;
6. sens et portée de la `prohairesis`.

Le delta comprend **6 nœuds de position** et **42 arêtes** :

- 6 `has_position` ;
- 6 `argues_for` qui rattachent chaque nouvelle position à son ou ses nœuds
  argumentatifs lus ;
- 20 `contributes_to`, dont les passages contestés ;
- 6 `responds_to` directement incidents aux débats, tous attestés ;
- 3 `contrasts_with` entre positions atomiques, tous attestés ;
- 1 `opposes` entre arguments savants, attesté.

Le gate d’ingestion sur la copie temporaire donne **BLOCK 0 / WARN 0**. Le
renderer réel `build_controversy_frame.py`, exécuté avant puis après fusion du
delta dans une copie temporaire du KG, passe de la branche lexicale à la
branche directe pour **6 débats sur 6**. Les sept relations positionnelles
échantillonnées — quatre nouvelles et trois réutilisées — sont toutes
retrouvées par le même renderer et toutes marquées `attested=true`.

Le mode `--apply` a été testé volontairement : il refuse l’écriture, car le
delta porterait le nombre de `opposes` de **21 à 22** tandis que le pin G6 reste
à 21. Les empreintes des deux JSONL KG sont inchangées et aucun backup
`*.bak-central_debates` n’a été créé.

## Principes de sélection

La centralité est ici éditoriale, non une simple centralité de degré. Un débat
est prioritaire s’il commande une articulation de la thèse : conditions
hellénistiques du problème, vocabulaire de l’agence, construction d’un pôle
libertarien, transposition chrétienne anti-déterministe, puis reconfiguration
par la grâce. Un grand nombre d’arêtes ne remplace donc pas la couverture d’une
fault line savante précise.

Les 25 nœuds `debate|controversy` ont été recomptés dans l’état actif
(19 994 nœuds, 49 468 arêtes). Dans le tableau suivant, `←` signifie une arête
entrante vers le débat et `→` une arête sortante. Les nombres agrègent
exhaustivement les arêtes incidentes par direction et relation ; la colonne
« dialectique directe » utilise exactement l’ensemble rendu par Scholar-RAG :
`opposes|critiques|responds_to|refutes|contrasts_with|agrees_with|supports`.

| Rang | Nœud | Incidentes actuelles | Dialectique directe | Décision éditoriale |
|---:|---|---|---:|---|
| 1 | `debate_discovery_of_will` | 47 : ←`contributes_to` 37 ; ←`discusses` 3 ; ←`participates_in` 4 ; →`discusses` 1 ; →`has_position` 2 | 0 | **Retenu** : fault line historiographique qui formule directement la question d’émergence. |
| 2 | `debate_christian_gnostic_freedom` | 6 : ←`participates_in` 1 ; ←`source_for` 1 ; →`discusses` 1 ; →`has_position` 3 | 0 | **Retenu** : transposition chrétienne décisive contre les natures fixes. |
| 3 | `debate_augustine_pelagius_grace` | 16 : ←`contributes_to` 4 ; ←`discusses` 6 ; ←`participates_in` 2 ; ←`source_for` 1 ; →`discusses` 1 ; →`has_position` 2 | 0 | **Retenu** : terme de l’axe Origène–Augustin, où la liberté est reconfigurée par la priorité de la grâce. |
| 4 | `debate_alexander_stoics_determinism` | 46 : ←`contributes_to` 41 ; ←`discusses` 1 ; ←`participates_in` 1 ; →`discusses` 1 ; →`has_position` 2 | 0 | **Retenu** : première construction antique systématique du pôle incompatibiliste/libertarien. |
| 5 | `debate_carneadean_antiastrology_tradition` | 15 : ←`discusses` 1 ; ←`participates_in` 14 | 0 | **Retenu** : matrice dialectique des topoi moraux anti-fatalistes transmis aux chrétiens. |
| 6 | `debate_prohairesis_meaning` | 27 : ←`contributes_to` 10 ; ←`discusses` 13 ; ←`participates_in` 1 ; →`discusses` 1 ; →`has_position` 2 | 0 | **Retenu** : articulation lexicale et psychologique entre choix aristotélicien, Épictète et histoire de la volonté. |
| 7 | `debate_origins_notion_of_will_modern_paradigm` | 5 : ←`contributes_to` 5 | 0 | Rejeté : doublon éditorial beaucoup plus pauvre de `debate_discovery_of_will`. |
| 8 | `debate_stoic_academic_hellenistic` | 17 : ←`contributes_to` 4 ; ←`discusses` 4 ; ←`participates_in` 2 ; ←`source_for` 3 ; →`discusses` 1 ; →`has_position` 3 | 0 | Rejeté : dossier de fond absorbé par Carnéade et Alexandre ; l’ajouter aurait recompté la même fault line. |
| 9 | `debate_stoic_compatibilism` | 32 : ←`contributes_to` 21 ; ←`discusses` 3 ; ←`participates_in` 3 ; ←`responds_to` 1 ; →`discusses` 1 ; →`has_position` 3 | 1 (`1aa811eb-…`) | Rejeté : essentiel en amont mais déjà doté d’une arête dialectique incidente ; moins directement centré sur l’émergence chrétienne. |
| 10 | `debate_intellectualism_vs_voluntarism_w3x4y5z6` | 15 : ←`contains` 1 ; ←`contributes_to` 5 ; ←`discusses` 1 ; ←`participates_in` 2 ; ←`source_for` 1 ; →`contains` 2 ; →`discusses` 1 ; →`has_position` 2 | 0 | Rejeté : catégorie transhistorique trop large ; ses enjeux datables sont couverts par « discovery » et `prohairesis`. |
| 11 | `debate_divine_foreknowledge_235f2530` | 13 : ←`contributes_to` 5 ; ←`discusses` 5 ; →`contains` 1 ; →`has_position` 2 | 0 | Rejeté : très pertinent pour Origène, mais plus étroit que l’axe grâce-liberté choisi. |
| 12 | `debate_middle_platonist_fate_interpretation` | 8 : ←`defines` 1 ; ←`represents` 2 ; ←`source_for` 3 ; →`has_position` 2 | 0 | Rejeté : médiation importante mais dossier de contexte, déjà couvert et traversable dans le corridor. |
| 13 | `debate_compatibility_question_ea55e118` | 24 : ←`contributes_to` 10 ; ←`discusses` 9 ; →`discusses` 1 ; →`has_position` 4 | 0 | Rejeté : question générique, sans localisation historique ou chrétienne propre. |
| 14 | `debate_source_of_action_90c57974` | 9 : ←`contributes_to` 5 ; ←`discusses` 1 ; →`discusses` 1 ; →`has_position` 2 | 0 | Rejeté : sous-problème causal déjà contenu dans Alexandre/Stoïciens. |
| 15 | `debate_lazy_argument` | 16 : ←`contributes_to` 2 ; ←`discusses` 5 ; ←`grounded_in` 1 ; ←`source_for` 3 ; →`discusses` 2 ; →`has_position` 3 | 0 | Rejeté : objection particulière, réutilisée par Origène mais non structurante à l’échelle de la thèse. |
| 16 | `debate_epicurus_free_will` | 9 : ←`contributes_to` 1 ; ←`discusses` 1 ; ←`participates_in` 1 ; ←`source_for` 3 ; →`has_position` 3 | 0 | Rejeté : généalogie concurrente importante, mais moins directement transmise au corridor chrétien retenu. |
| 17 | `debate_divine_foreknowledge_future_contingents_a7b8c9d0` | 12 : ←`contributes_to` 3 ; ←`discusses` 1 ; ←`responds_to` 5 ; →`has_position` 3 | 5 | Rejeté : déjà directement dialectique et surtout médiéval dans sa population actuelle. |
| 18 | `debate_randomness_objection_ae34a974` | 3 : →`discusses` 1 ; →`has_position` 2 | 0 | Rejeté : objection analytique transhistorique, périphérique au corridor antique-chrétien. |
| 19 | `debate_monothelite_dyothelite_controversy` | 16 : ←`contributes_to` 13 ; →`discusses` 3 | 0 | Rejeté : important pour l’histoire ultérieure de la volonté, mais VIIe siècle et christologie, donc hors noyau d’émergence. |
| 20 | `controversy_de_auxiliis_2n6i7j35` | 3 : ←`participates_in` 2 ; →`influences` 1 | 0 | Rejeté : controverse moderne catholique très aval. |
| 21 | `controversy_luther_erasmus_1m5h6i24` | 4 : ←`influences` 1 ; ←`participates_in` 2 ; →`influences` 1 | 0 | Rejeté : Réforme, hors période de la thèse. |
| 22 | `controversy_synod_of_dort_5q9l0m68` | 3 : ←`critiques` 1 ; ←`influences` 1 ; ←`participates_in` 1 | 1 (`8fb6c19a-…`) | Rejeté : déjà dialectique et très aval. |
| 23 | `debate_occasionalism_vs_secondary_causation_e1f2g3h4` | 7 : ←`exemplifies` 1 ; ←`participates_in` 1 ; ←`source_for` 1 ; →`contains` 1 ; →`has_position` 3 | 0 | Rejeté : médiéval islamo-chrétien, sans rôle direct dans l’émergence étudiée. |
| 24 | `controversy_hobbes_bramhall_3o7j8k46` | 2 : ←`participates_in` 2 | 0 | Rejeté : moderne et sans continuité directe documentée avec le corridor. |
| 25 | `controversy_hume_reid_4p8k9l57` | 2 : ←`participates_in` 2 | 0 | Rejeté : moderne et sans rôle généalogique direct dans la thèse. |

Ce recomptage retrouve le diagnostic H-06 : seules trois unités possèdent une
relation dialectique directement incidente dans l’état courant — le Synode de
Dort, les futurs contingents et le compatibilisme stoïcien. Les six unités
retenues en ont toutes zéro avant delta.

## Construction des positions atomiques

Les nœuds argumentatifs existants sont réutilisés dès qu’ils formulent déjà une
position suffisamment atomique. Six nouveaux nœuds seulement sont nécessaires
pour éviter de faire porter la controverse par un argument composite ou par une
catégorie générique.

| Nouvelle position | Source(s) KG lue(s) | Justification de la création |
|---|---|---|
| `position_linjamaa_valentinian_ethics_and_self_determination` | `scholarly_argument_linjamaa_free_will_and_moral_accountabi_1` | Isole la thèse « le *Tripartite Tractate* conserve autodétermination et responsabilité ». |
| `position_telfer_valentinian_natural_determinism` | `scholarly_argument_telfer_gnostic_rejection_of_free_will_1` | Isole la thèse adverse « les natures fixes valentiniennes excluent l’`autexousia` ». |
| `position_long_epictetan_freedom_compliance_with_fate` | `scholarly_argument_long_2002_freedom_not_freedom_from_fate` et `…bobzien_not_compatibilist_but_ethical` | Isole la lecture éthique : conformité au lot, non-exemption causale. |
| `position_dobbin_epictetan_inner_preserve_immune_to_fate` | `scholarly_argument_dobbin_1991_preserve_of_freedom_bounded_by_self` | Isole la lecture métaphysique du « preserve » intérieur hors du nexus externe. |
| `position_furst_carneades_proto_voluntarist_self_motion` | `argument_furst_2022_carneades_voluntary_self_motion` | Isole la lecture positive/proto-volontariste du mouvement volontaire carnéadien. |
| `position_bobzien_carneades_dialectical_not_positive_doctrine` | `argument_bobzien_2001_b1_rise_fall_freedom_problem` | Isole la lecture dialectique : argument contre les Stoïciens, non doctrine propre. |

Chaque nœud porte `metadata.provenance.source_node_ids`, le locus paginé déjà
présent et un résumé sans ajout doctrinal. L’ontologie active ne permet pas
`grounded_in` ou `evidenced_by` de `position` vers `argument` : `grounded_in`
vise un `debate|passage`, et `evidenced_by` vise un `passage`. Le delta emploie
donc la relation active et typée `argument --argues_for--> position`, tandis que
`debate --has_position--> position` porte l’appartenance éditoriale. Ce choix
évite de créer une arête contraire à `edge_types.json` tout en conservant la
provenance explicite demandée.

## Carte des six débats

### 1. Naissance/découverte de la volonté

**Positions réutilisées**

- `scholarly_position_dihle_will_christian_innovation` : volonté autonome
  principalement augustinienne et chrétienne ;
- `scholarly_position_frede_will_originates_epictetus` : première notion chez
  Épictète, puis transmission à Origène et Augustin ;
- `scholarly_argument_irwin_greek_concept_of_the_will_0` : le concept peut déjà
  être attribué aux Grecs, notamment à Aristote.

**Relations attestées réutilisées**

- Frede `opposes` Dihle, `526b2160-…`, Frede 2011, pp. 5-7 ;
- Irwin `opposes` Frede, `b01bc633-…`, Irwin 1992, p. 455 ;
- Irwin `opposes` Dihle, `df2df6bf-…`, Irwin 1992, p. 454 n. 5 et n. 7.

Le delta ne duplique aucune de ces relations. Il ajoute les trois
`contributes_to`, puis l’arête incidente attestée
`central-debates-20260817-008` (Frede `responds_to` le débat), nécessaire au
chemin direct du renderer.

**Passages contestés**

- ajout explicite de `passage_epictetus_disc_i_1_23`, le locus grec de la
  `prohairesis` non contrainte déjà cité par les arguments Frede/Bobzien ;
- maintien des loci alexandriniens déjà incidents : `passage_alex_fat_12`,
  `_14`, `_18`, `_19`, `_20` notamment.

### 2. Liberté chrétienne et déterminisme gnostique/valentinien

**Positions atomiques créées**

- Linjamaa : le *Tripartite Tractate* conserve volonté, autodétermination et
  responsabilité dans un cosmos pédagogique ;
- Telfer : Basilide et Valentin rejettent l’`autexousia`, les inclinations étant
  fixées par nature.

`central-debates-20260817-014` les relie par `contrasts_with`, attesté par
Linjamaa 2019, pp. 112-158 (surtout 133 et 146), et Telfer 1957,
pp. 124-125. Löhr fournit la position méthodologique directement incidente :
la charge de déterminisme doit être contrôlée comme construction hérésiologique
(`central-debates-20260817-015`, Löhr 1992, pp. 381-382).

**Passage contesté**

- `passage_irenaeus_ah_4_37`, fragment grec authentique de *Haer.* IV.37.1,
  relié à `argument_irenaeus_adv_haer_iv_37_praise_blame_transposed`.

Les absents signalés par le corridor restent absents : aucune création pour
IV.38-39 ; aucun shell ou traduction seule de *Princ.* III.1.6 n’est promu en
preuve ; aucun faux passage du *Tripartite Tractate* n’est inventé.

### 3. Grâce et liberté, axe Origène → Augustin

**Positions réutilisées**

- `scholarly_argument_moller_origen_propositum_compatibilizes_foreknowledge_and_choice` :
  l’élection répond aux choix prévus et la coopération humaine reste possible ;
- `scholarly_argument_moller_augustine_target_plausible_not_decisive` : chez
  Augustin, la grâce doit d’abord assister la volonté pour qu’elle veuille.

Leur `opposes` existant `furst-markschies-126` est conservé et réutilisé ; il
est attesté par Møller 2021, pp. 213-214. Le delta rattache la position
origénienne au débat et ajoute le `responds_to` incident
`central-debates-20260817-038`.

**Passages contestés**

- `passage_aug_grat_1_2` : affirmation du libre arbitre ;
- `passage_aug_grat_1_4` : laisser place à la grâce dans la défense du libre
  arbitre ;
- `passage_aug_grat_1_13` : refus du mérite préalable de la bonne volonté ;
- `passage_aug_grat_1_16` : Dieu prépare la volonté et coopère à son
  accomplissement.

Les quatre passages contiennent le latin original. Le commentaire d’Origène
sur Romains reste lié comme œuvre aux positions Møller ; aucun passage
origénien n’est ajouté, car le corridor constate précisément l’absence d’un
passage authentique complet pour Romains 7/9. Cette asymétrie documentée vaut
mieux qu’un faux équilibre textuel.

### 4. Alexandre contre les Stoïciens

**Positions réutilisées**

- `scholarly_argument_ramelli_alexander_s_concept_of_to_eph__5` : le
  compatibilisme stoïcien échoue à sauver le `to eph’ hêmin` et la
  responsabilité ;
- `scholarly_argument_salles_stoic_compatibilism_1` : la nécessitation
  antérieure n’exclut pas à elle seule la louange et le blâme mérités.

`central-debates-20260817-004` ajoute leur `opposes` comme conflit
propositionnel, avec les deux attestations : Ramelli 2014, pp. 237-289, et
Salles 2005, pp. xiii-xiv. La note de portée précise qu’il ne s’agit pas d’un
échange direct entre auteurs. L’arête incidente
`central-debates-20260817-003` fait passer le renderer par la branche directe.

**Passages contestés**

Le débat possède déjà les 39 chapitres grecs `passage_alex_fat_1..39`. Aucun
doublon n’est ajouté. Les loci précisément attachés à la position Ramelli et
mis en avant dans la carte sont *De fato* 12, 14, 16 et 22 ; le chapitre 14 est
le locus contrôlé TLG du corridor.

### 5. Tradition carnéadienne anti-fataliste/anti-astrologique

**Positions atomiques créées**

- Fürst : le mouvement volontaire de soi-même est un moment positif,
  proto-volontariste ;
- Bobzien : Carnéade emploie la liberté bilatérale dialectiquement contre le
  Portique sans en faire sa doctrine.

Leur `contrasts_with`, `central-debates-20260817-029`, est attesté par Fürst
2022, pp. 96-100, et Bobzien 2001, pp. 396-412. Amand fournit le contrôle
méthodologique directement incident (`central-debates-20260817-030`) : la
reconstruction à partir des témoins est conjecturale, puisque Carnéade n’a rien
écrit et Clitomaque est perdu (Amand 1945, p. 572).

**Passages contestés**

- Cicéron, *De fato* 23-25 : `passage_cic_fat_23`, `_24`, `_25` ;
- Cicéron, *De fato* 31-33 : `passage_cic_fat_31`, `_32`, `_33`.

Ce sont les témoins latins indiqués par le corridor ; aucun « original grec de
Carnéade » n’est fabriqué.

### 6. Sens et portée de la `prohairesis`

**Positions atomiques créées**

- Long : liberté intérieure et éthique, conformité volontaire au destin, non
  exemption à la causalité antécédente ;
- Dobbin : réserve intérieure de liberté, étroitement bornée mais immune au
  nexus causal extérieur.

Une ancienne arête Long `critiques` Dobbin (`bdea8722-…`) contient une note
substantielle mais pas de `metadata.attested_by` ; elle relève donc de la dette
R16 et ne peut pas être réutilisée comme relation rendue attestée. Le delta ne
réinsère ni cette triple ni son inverse. Il normalise les deux thèses dans des
positions atomiques et ajoute `central-debates-20260817-021`
(`contrasts_with`), attesté par Long 2002, pp. 221 et 229, et Dobbin 1991,
p. 133. Le `responds_to` incident `central-debates-20260817-022` est fondé sur
Long 2002, p. 230.

**Passages contestés**

- `passage_epictetus_disc_i_1_1` : les choses qui dépendent de nous ;
- `passage_epictetus_disc_i_1_23` : `prohairesis` non contrainte.

Ces deux passages grecs possèdent leurs traductions anglaises `_en` et sont
déjà cités par la lecture Bobzien du dossier épictétéen.

## Vérification par le renderer réel

Le chemin de code contrôlé est celui de
`graphrag/src/eleutheria_graphrag/agents/tools/build_controversy_frame.py` :

- sans relation dialectique incidente au nœud-débat, `direct_links` est vide et
  les lignes 249-263 déclenchent le *lexical participant/argument cluster
  fallback* ;
- avec un `responds_to` attesté directement incident, `direct_links` n’est plus
  vide et la branche directe est utilisée.

Le renderer n’a pas été modifié. Les six `responds_to` du delta sont nécessaires
parce qu’un simple `has_position`/`contributes_to` ne désactive pas le fallback.
Dans la branche directe actuelle, le renderer ne ré-ensemence pas ensuite sur
les relations entre positions : c’est pourquoi les frames de débat affichent
une seule relation directe, le `responds_to` incident. Un second contrôle a donc
construit des frames depuis les positions elles-mêmes et retrouvé **7/7**
relations attestées — les quatre relations centrales nouvelles et trois
relations existantes réutilisées. Cette vérification respecte l’interdiction de
modifier le renderer tout en contrôlant les deux couches du modèle.

| Débat | Avant | Après delta en copie temporaire | Positions après | Liens directs après | Passages citables après |
|---|---|---|---:|---:|---:|
| Alexandre/Stoïciens | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 5 | 1 | 9 |
| Découverte de la volonté | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 28 | 1 | 9 |
| Chrétiens/Gnostiques | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 7 | 1 | 11 |
| `prohairesis` | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 18 | 1 | 7 |
| Carnéade/anti-astrologie | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 17 | 1 | 12 |
| Grâce et liberté | `fallback=True` — participant/argument lexical | `fallback=False` — relation dialectique incidente directe | 10 | 1 | 10 |

Les nombres de positions ne sont pas des scores de couverture : le renderer
inclut aussi les ponts déjà incidents au débat. La couverture éditoriale est
évaluée par les fault lines décrites ci-dessus, pas par ces totaux.

### Précondition d’exécution Python constatée

Trois dépendances directes du renderer contiennent actuellement la syntaxe
Python-2 invalide `except TypeError, ValueError:` : `citability.py`,
`dialectical_relations.py` et `thesis_equivalence.py`. L’interpréteur système
ne peut donc pas importer le renderer tel quel ; l’environnement `uv` local
n’est pas lisible sous le sandbox courant.

L’ingesteur effectue uniquement, pour la vérification, la normalisation
parser-compatible `except (TypeError, ValueError):` :

- en mémoire pour les trois dépendances du renderer ;
- dans la copie temporaire de `dialectical_relations.py` utilisée par le gate.

Le fichier `build_controversy_frame.py` chargé est bien le fichier réel du
dépôt (chemin résolu vérifié), et aucun fichier source n’est écrit ou modifié.
Les sorties annoncent explicitement 3 normalisations en mémoire et 1 dans le
miroir du gate.

## Gate, dry-run et refus G6

### Validation syntaxique des livrables

```text
$ python3 -m json.tool scripts/data_2026_08_17_central_debates.json
json: valid

$ python3 -m py_compile scripts/ingest_2026_08_17_central_debates.py
py_compile: ok
```

Le `.pyc` produit par ce contrôle a été supprimé ; il ne fait pas partie des
livrables.

### Sortie complète du dry-run final

```text
$ python3 scripts/ingest_2026_08_17_central_debates.py --dry-run
delta: 6 nodes / 42 edges
ontology endpoint typing: 42/42 active and valid
novel: 6 nodes / 42 edges (skipped existing: 0 nodes, 0 edges)
relations: argues_for=6, contrasts_with=3, contributes_to=20, has_position=6, opposes=1, responds_to=6
opposes: current=21, novel=1, post-apply=22, g6-pin=21
--- check_ingestion_rules.py --new-only (temporary mirror) ---
temporary parser normalisations: 1 (shared dependency only; repository unchanged)
ingestion-rules: delta of 6 nodes / 42 edges
  no violations

BLOCK: 0   WARN: 0
renderer dependency parser normalisations: 3 (in memory only; renderer unchanged)
--- build_controversy_frame.py before/after ---
renderer: graphrag/src/eleutheria_graphrag/agents/tools/build_controversy_frame.py
debate_alexander_stoics_determinism: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=5; links=1; passages=9
debate_discovery_of_will: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=28; links=1; passages=9
debate_christian_gnostic_freedom: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=7; links=1; passages=11
debate_prohairesis_meaning: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=18; links=1; passages=7
debate_carneadean_antiastrology_tradition: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=17; links=1; passages=12
debate_augustine_pelagius_grace: before fallback=True path=lexical-participant fallback; after fallback=False path=direct incident-dialectical path; positions=10; links=1; passages=10
renderer gate: 6/6 direct path; 6/6 with >=2 positions; 6/6 citable passages
position-link gate: 7/7 attested position relations retrievable (reused and novel)
dry-run: nothing written; future apply refused until G6 opposes pin changes from 21 to 22
```

### Test volontaire du refus `--apply`

```text
renderer gate: 6/6 direct path; 6/6 with >=2 positions; 6/6 citable passages
position-link gate: 7/7 attested position relations retrievable (reused and novel)
FATAL: G6 opposes pin is 21, but post-apply count is 22; update the pin in the same change before --apply
nothing written
apply-exit=1
```

### Preuve de non-écriture

Empreintes calculées avant le test `--apply`, puis retrouvées après son refus :

```text
33cc28709c4288625278e69d8ea4c37d8c123e0987d96418c1ac2ed8f57c14ba  data/kg/nodes.jsonl
d93ffc920afe05013ec9cd0da3660fc7c5a5220e5be7c77978bcd028f55cd7db  data/kg/edges.jsonl
```

Aucun fichier `*.bak-central_debates` n’existe sous `data/kg` ou
`data/corpus`. Aucun fichier de ces deux répertoires n’a été écrit.

## Livrables additifs

- `scripts/data_2026_08_17_central_debates.json` ;
- `scripts/ingest_2026_08_17_central_debates.py` ;
- `data/audit/2026-08-17_central_debates_plan.md`.

Aucun fichier `scripts/data_2026_08_17_reading_wave_*` n’a été touché ; aucune
commande git n’a été exécutée.
