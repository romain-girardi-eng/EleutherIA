# Ancrage primaire de Clément - Stromates (2026-08-18)

## Résultat appliqué

La vague ferme le déficit textuel documenté pour les loci centraux de Clément
d'Alexandrie. Elle ajoute 55 sections grecques au KG et au miroir corpus,
conserve les trois sections déjà présentes dans le périmètre et relie désormais
les 61 passages clémentins du snapshot à leurs jumeaux corpus explicites.

État avant/après :

| Mesure | Avant | Après | Delta net |
|---|---:|---:|---:|
| Nœuds KG | 20 216 | 20 271 | +55 |
| Arêtes KG assertées | 50 057 | 50 169 | +112 |
| Passages corpus | 21 103 | 21 158 | +55 |
| Citations corpus | 19 779 | 19 836 | +57 |
| Passages des *Stromates* dans le corpus | 6 | 61 | +55 |

Le delta brut contient 118 nouvelles arêtes : 110 arêtes structurelles
(`part_of` et `authored_by`) et huit preuves précises. Six anciennes arêtes de
preuve erronées ont été supprimées, d'où +112 net. De même, 63 citations ont
été ajoutées et six retirées, d'où +57 net.

## Sources et contrôle visuel

Texte copié, jamais généré :

- TEI local `TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml` ;
- CTS `urn:cts:greekLit:tlg0555.tlg004.perseus-grc2` ;
- SHA-256 `9b0dd0f4728dcbd57ab08231ad7addeb739c8046879dfceae0825b717d753eb1` ;
- édition : Otto Stählin, *Clemens Alexandrinus II: Stromata I-VI*, GCS 15
  (Leipzig, 1906), réencodage TEI ;
- PDF de contrôle SHA-256
  `58f50e5bf428cd918f8a792586891665196446cbe4b248027eec2e7537d943bb`.

Les pages imprimées 117-119, 126-127, 142-143, 151, 313-317 et 383 ont été
rendues et inspectées. L'extracteur TEI retient la leçon éditée (`lem`, `corr`,
`reg`, `add`) et exclut les suppressions (`del`) et notes ; un test empêche le
retour à la concaténation de variantes incompatibles.

## Correction décisive de numérotation

La référence d'Amand/Stählin `Strom. II, 11, 1-2` désigne la section continue
11, paragraphes 1-2, et non le chapitre 11. Sa hiérarchie CTS complète est :

```text
Strom. II.3.11.1-2
urn:cts:greekLit:tlg0555.tlg004.perseus-grc2:2.3.11
passage_clement_strom_2_3_11
GCS 15, p. 118, l. 21 - p. 119, l. 3
```

Le texte contient le reductio attendu : si la foi était un avantage naturel,
elle ne serait plus un accomplissement de la `proairesis`; louange, blâme,
repentance et foi volontaire deviendraient incohérents. L'ancienne estimation
`II.11.48-49` était donc elle-même une confusion entre section continue et
hiérarchie CTS.

## Périmètre canonique

Le périmètre documenté représente 58 divisions :

- `II.2.8` ;
- `II.3.11` (section continue `II, 11, 1-2`) ;
- chapitres `II.6-15`, soit `2.6.25` à `2.15.71` ;
- chapitres `IV.23-24`, soit `4.23.147` à `4.24.154` ;
- `V.13.86`.

Les nœuds `2.11.50-52` existaient déjà et ont été conservés : ils appartiennent
au vaste périmètre `II.6-15`, mais ne portent pas l'argument précis sur foi
naturelle et responsabilité. Les 55 autres divisions ont été créées. Les
sous-sections Stählin restent des `milestone` de métadonnées ; elles ne sont pas
inventées comme niveaux CTS supplémentaires.

## Réparation des preuves

Six arêtes et six citations `evidenced_by` associaient à tort les deux arguments
suivants à `II.11.50-52` :

- `argument_clement_alex_carneadean_glissement_faith_unbelief` ;
- `argument_clement_grace_synergy_assent`.

Elles ont été retirées sans supprimer les trois passages ni leurs citations
`snapshot_passage_node`.

Nouveaux ancrages :

- argument foi/nature -> `II.3.11` uniquement ;
- argument grâce/assentiment -> `II.2.8`, `II.6.26`, `II.12.54`, `II.12.55`,
  `IV.23.152`, `IV.24.153`, `V.13.86`.

Le second argument n'est volontairement pas relié à `II.3.11` : ce locus porte
le reductio anti-basilidien distinct. Les trois entrées différées de la file de
revue (`rq_51ffddfd4448`, `rq_695597d734fc`, `rq_4c7d6b616009`) ont été
adjudiquées individuellement comme `fixed`. Les entrées gold `cg025`, `cg027`
et `cg028` pointent maintenant vers le jumeau corpus de `II.3.11`, UUID
`5a221307-b0c5-5f9a-87b3-771fbd2f312b`.

## Autres corrections contenues dans la vague

- le nœud œuvre `work_clement_stromateis` possède désormais son CTS canonique
  `urn:cts:greekLit:tlg0555.tlg004` et son identifiant corpus ;
- les six anciens passages ont reçu un `db_passage_id` explicite ;
- les numéros de séquence des 61 passages encodent livre, chapitre et section,
  au lieu d'ignorer le numéro du livre ;
- les références de vérification tronquées des nœuds œuvre et
  `argument_clement_grace_synergy_assent` ont été remplacées par des références
  complètes ;
- le manifeste de source savante enregistre 61 nœuds et les deux vagues
  d'ingestion.

## Vérifications

Dry-run puis application :

```text
R1-R18 --new-only: BLOCK 0, WARN 0
55 nouveaux nœuds / 118 nouvelles arêtes / 6 arêtes retirées
55 nouveaux passages / 63 nouvelles citations / 6 citations retirées
```

Après application :

```text
idempotence: 0 nœud, 0 arête, 0 passage, 0 citation supplémentaire
corpus: 0 référence pendante, 0 passage dupliqué, 0 triplet dupliqué
parité: 10 994 jumeaux partagés; 3 051 violations historiques; 0 régression
tests ciblés: 46 réussis
Ruff: vert
```

Les sauvegardes pré-vague portent le suffixe
`.bak-clement_grounding_2026_08_18` dans `data/kg` et `data/corpus`.

Le contrôle de reproductibilité a aussi retrouvé une régression de formatage :
`dialectical_relations.py`, importé par le gate R1-R18, contenait à nouveau la
syntaxe `except A, B` propre à Python 3.14. Le tuple parenthésé compatible 3.12
a été restauré, le fichier est ciblé `py312` dans les deux configurations Ruff,
et le test de compatibilité couvre désormais explicitement cette dépendance.

## Dette restante prioritaire

Cette vague ne réduit pas artificiellement la baseline historique de parité :
les 3 051 violations restent inchangées et aucun nouvel identifiant fautif
n'apparaît. Les travaux suivants les plus solides sont :

1. réingérer les 24 passages de Sextus dont les omissions internes ont été
   confirmées par la re-collation ;
2. le split Plutarque `tlg135`/`tlg138` a depuis été adjudiqué et réparé ; le
   prochain dossier d'identité sans texte reste Tertullien *De monogamia* ;
3. poursuivre l'ancrage primaire avec Irénée IV.38-39 ou le *Commentaire sur
   Romains* d'Origène.
