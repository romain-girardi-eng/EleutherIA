# Déploiement atomique des données par tables staging

## But et périmètre

Le déploiement de données publie ensemble les cinq tables servies :

- `free_will.kg_nodes` ;
- `free_will.kg_edges` ;
- `free_will.ancient_works` ;
- `free_will.passages` ;
- `free_will.passage_citations`.

L’ancienne chaîne `bootstrap_supabase.py --replace-data` puis
`sync_corpus_to_db.py --commit` est interdite sur une base servie. Son
`TRUNCATE` et ses commits par lots pouvaient rendre visibles un KG vide, un
corpus partiel ou une combinaison des deux. Les anciens scripts restent utiles
pour une reconstruction initiale ; ils ne sont pas supprimés.

Le point d’entrée courant est `scripts/deploy_data_staged.py`. Il réutilise les
transformations et insertions des deux chargeurs existants en leur injectant les
noms `__staging` ; leur logique n’est pas dupliquée.

## Déroulement et garanties

1. Une session de maintenance prend un verrou consultatif exclusif.
2. Les cinq tables `__staging` sont recréées avec `LIKE … INCLUDING ALL`.
   Les tables sans suffixe restent lisibles et inchangées pendant tout le
   chargement.
3. Le snapshot KG est chargé, puis les trois tables corpus staging sont
   remplacées par le miroir corpus, comme dans l’ordre historique.
4. Les clés étrangères sortantes, triggers, droits, propriétaires, RLS et
   policies sont reproduits sur staging. Les colonnes générées et index,
   notamment le FTS, sont hérités par `LIKE … INCLUDING ALL`.
5. La génération staging doit passer tous les contrôles :
   comptes attendus dérivés des JSONL locaux, absence de citations pendantes,
   absence d’arêtes ou de passages orphelins et unicité des triplets de
   citation. La parité `canonical_ref`/`cts_urn` et la présence de chaque
   jumeau KG/corpus déclaré suivent le cliquet décrit ci-dessous : seule une
   régression nouvelle bloque la publication.
   Les 16 lignes `unresolved_english_research_record` ne sont jamais coercées
   vers `original` ou `translation` : seul leur contrat complet
   `discoverable_only` + `source_identity_unresolved` + anglais non citable
   autorise leur exclusion, ainsi que celle de leurs 16 citations. Le rapport
   conserve les deux effectifs et les SHA-256 déterministes des cohorts.
6. Une seule transaction prend les verrous finaux, valide les clés étrangères
   externes contre staging, remplace la génération `__old`, renomme les cinq
   tables live en `__old`, renomme les cinq staging sans suffixe, rebranche les
   clés étrangères et recrée les vues/fonctions liées. Un échec ou une coupure
   avant `COMMIT` annule tous ces DDL. Après `COMMIT`, les cinq noms désignent
   tous la nouvelle génération.
7. La génération précédente reste sous `__old` pour un rollback immédiat. Le
   déploiement réussi suivant la remplace dans la même transaction ; il n’y a
   donc jamais plus d’une génération de retour.

La garantie atomique concerne l’état PostgreSQL. L’API garde le KG en mémoire :
sa recréation est donc une étape obligatoire, immédiatement après le swap. Si
le processus de déploiement est interrompu après le commit mais avant cette
recréation, relancer seulement la commande de recréation des conteneurs.

`--dry-run` n’est pas un simple calcul local : il construit, charge et vérifie
réellement toutes les tables staging sur la base ciblée, puis les supprime sans
effectuer le swap. Une interruption pendant le chargement peut laisser des
tables `__staging`, mais jamais modifier les tables live ; l’exécution suivante
les nettoie explicitement.

La dernière ligne standard du script est un objet JSON. Le champ `status` vaut
`verified`, `deployed`, `rolled_back` ou `failed`; les comptes, contrôles et
dépendances inventoriées accompagnent le résultat.

## Cliquet de parité KG/corpus

Le fichier versionné
`data/audit/kg_corpus_parity_baseline.json` contient, pour chaque classe
`cts_urn_mismatch`, `canonical_ref_mismatch` et `missing_twin`, la liste triée
des `kg_node_id` déjà en dette. L’identité du nœud est comparée, pas seulement
le nombre de lignes : remplacer une ancienne anomalie par une nouvelle sans
changer le total est donc une régression bloquante.

Pendant la vérification staging :

- une anomalie encore présente dans la même classe du baseline est comptée
  sous `legacy_debt` et ne bloque pas ;
- un identifiant absent de cette classe est renvoyé sous
  `new_violations.by_class` et fait échouer la vérification ;
- un identifiant du baseline qui n’est plus en anomalie est accepté et compté
  sous `fixed_since_baseline`.

Le calcul du baseline est entièrement local : il lit
`data/kg/nodes.jsonl`, `data/corpus/passages.jsonl` et
`data/corpus/citations.jsonl`, sans ouvrir de connexion PostgreSQL. Après une
vague légitime de correction de parité, le régénérer depuis la racine du dépôt
puis vérifier que les listes ont uniquement diminué comme prévu :

```bash
python scripts/deploy_data_staged.py --write-parity-baseline
```

La sortie doit indiquer `status=parity_baseline_written` et les effectifs par
classe. Ne jamais régénérer le fichier pour faire accepter une régression :
toute croissance ou tout remplacement d’identifiant doit être analysé comme
une nouvelle dette.

## Inventaire des dépendances

L’inventaire réel est relu dans `pg_catalog` à chaque exécution. Le déploiement
ne dépend donc pas seulement de cette liste documentaire.

| Élément | Dépendance | Traitement |
|---|---|---|
| `kg_edges` | FK `source_id` et `target_id` → `kg_nodes` | Recréées sur staging en visant `kg_nodes__staging`; elles suivent ensuite les OID renommés. |
| `passages` | FK `work_id` → `ancient_works`; FK auto-référentes de traduction/navigation | Recréées sur staging, avec toutes les cibles staging. |
| `passage_citations` | FK `passage_id` → `passages`; FK durcie `kg_node_id` → `kg_nodes` si la migration est présente | Recréées sur staging et contrôlées par les vérifications de références pendantes. |
| `passage_relationships` | Deux FK externes → `passages` | Une FK temporaire vers staging est ajoutée et validée dans la transaction; l’ancienne est remplacée avant le commit. Les lignes de cette table ne sont pas remplacées. |
| `textual_variants` | FK externes → `passages` et `kg_nodes` | Même rebranchement transactionnel; les variantes restent en place. |
| `oga_tokens` | FK externes → `ancient_works` et, après migration, `passages` | Même rebranchement transactionnel; les tokens restent en place. |
| `passage_search`, `works_statistics`, `passages_statistics`, `citation_statistics` | Vues directes sur les tables remplacées | Définitions capturées par `pg_get_viewdef`, puis `CREATE OR REPLACE VIEW` après les renommages et avant le commit. |
| `oga_tokens_enriched`, `oga_work_statistics` | Vues OGA utilisant `ancient_works` | Même recréation transactionnelle. |
| RPC de `supabase_public_api.sql`, `supabase_functions.sql` et `20260514_01_supabase_rebuild_support.sql` | Fonctions SQL utilisant les noms `free_will.*` | Les fonctions liées par `pg_depend` sont recréées dans la transaction. Les corps SQL textuels sont résolus par nom après invalidation du plan et retrouvent les nouveaux noms live. |
| `update_ancient_works_updated_at`, triggers `*_bump_version` | Triggers utilisateur | Définitions capturées par `pg_get_triggerdef` et recréées sur staging après le chargement, pour éviter les effets de bord pendant les lots. |
| FTS de `passages` | `search_vector` généré, `f_unaccent`, GIN et index trigrammes | La colonne générée et les index sont clonés par `LIKE … INCLUDING ALL`; `f_unaccent` reste une fonction indépendante. Il n’existe pas de trigger FTS actif dans le schéma canonique. |
| Séquences | Aucune sur les cinq tables canoniques : identifiants UUID et colonnes générées | L’inventaire runtime les signale si le schéma dérive. Une identité est recopiée avec sa propre séquence staging; une séquence `SERIAL` est refusée, car `LIKE` partagerait son `DEFAULT nextval` avec l’ancienne table. |
| Grants, RLS, policies, propriétaire | Exposition Supabase directe | Recopiés explicitement sur chaque table staging avant publication. |

Une vue matérialisée directement dépendante est refusée : sa stratégie de
reconstruction doit être ajoutée explicitement avant de reprendre le
déploiement. De même, une dépendance qui empêche la suppression de l’ancienne
génération fait échouer et annuler la transaction au lieu d’employer `CASCADE`.

## Runbook hôte

### Prévalidation

Depuis un poste autorisé, déclencher le dry-run hôte :

```bash
make deploy-data-dry-run RC_SHA=<sha-git-complet-de-40-caracteres>
```

Équivalent à exécuter sur l’hôte, depuis la racine du dépôt :

```bash
docker run --rm --network quirel-hub_quirel-network \
  -v /home/ben/EleutherIA:/repo -w /repo \
  --env-file /home/ben/EleutherIA/.env \
  python:3.12-slim bash -lc \
  'pip install -q asyncpg && python scripts/deploy_data_staged.py --dry-run'
```

Le code de sortie doit être zéro et la dernière ligne JSON doit avoir
`"status":"verified"`. La dette connue apparaît dans `legacy_debt`; toute
entrée de `new_violations` est bloquante. Il faut alors corriger les miroirs,
jamais contourner le contrôle sur la base ni ajouter mécaniquement l’identifiant
au baseline.

### Publication

Le cutover complet normal (sauvegarde, build, migrations, dry-run, swap,
recréation et sondes publiques) est :

```bash
make deploy RC_SHA=<meme-sha-git-complet>
```

Elle refuse tout SHA court ou branche mutable, exige que le checkout hôte soit
exactement ce commit, dérive le réseau Docker du conteneur API courant, lance
`scripts/deploy_data_staged.py` dans le conteneur Python relié à
`eleutheria-db`, puis recrée immédiatement
`eleutheria-api`/`eleutheria-worker` et vérifie `/api/health`. Pour une
exécution manuelle, reprendre la commande du dry-run sans `--dry-run`, puis :

```bash
docker compose -p deploy -f deploy/pragma-compose.yml \
  -f /tmp/eleutheria-compose-runtime.yml \
  up -d --force-recreate --no-deps --no-build \
  eleutheria-api eleutheria-worker
```

`make deploy-data` est réservé à une reprise ciblée du swap/recreate sur un
hôte déjà positionné au même SHA exact. Ne jamais l’exécuter après un
`make deploy` réussi : un deuxième swap remplacerait la génération `__old`
conservée pour rollback.

Contrôler ensuite le JSON `status=deployed`, la santé HTTP et les logs de
démarrage du KG. Ne pas lancer en parallèle un autre import ou une migration de
ces tables.

Le cutover racine lit ensuite `/api/kg/workspace/stats`, exige les mêmes comptes
que `data/stats.json`, puis sonde huit fois
`/api/health?expected_release_id=…`. Toute réplique servant une autre génération
répond 409 et bloque la publication frontend.

Pour le snapshot RC courant, le préflight local attend exactement 23 247
nœuds, 55 724 arêtes assertées, 186 œuvres servables, 23 312 passages servis et
22 772 citations servies. Ces nombres doivent être recalculés depuis le commit
RC ; ils ne constituent pas une constante à contourner.

## Rollback

Le rollback des données est indépendant du rollback de code du Makefile :

```bash
make deploy-data-rollback
```

Il vérifie que les cinq tables `__old` existent, puis échange atomiquement les
générations live et `__old`, rebranche les dépendances et recrée les conteneurs.
La génération retirée devient à son tour `__old`, ce qui permet un retour en
avant par la même commande si nécessaire.

Le rollback refuse une génération `__old` incomplète. Ne jamais renommer ou
supprimer manuellement une partie des cinq tables ; en cas d’inventaire ou de
contrainte inattendue, conserver l’état live et analyser l’erreur JSON.

## Validation locale

Le test d’intégration lance `postgres:16-alpine` avec un port et un nom
éphémères. Il couvre le dry-run, un `SIGKILL` pendant le chargement, une coupure
au milieu des DDL transactionnels, le swap complet, le rebranchement des vues,
RLS et clés externes, puis le rollback. Si le daemon Docker n’est pas
accessible, le test est marqué `SKIP` avec la raison exacte et les tests
unitaires continuent de contrôler la génération SQL et l’inventaire statique :

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  database/tests/unit/test_deploy_data_staged.py \
  database/tests/integration/test_staged_deploy_postgres.py
```
