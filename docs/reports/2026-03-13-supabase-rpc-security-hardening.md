# Supabase/Postgres prod hardening

## 1. Diagnostic initial

### Etat reel de prod observe

- `search_passages` et `search_passages_simple` existent en `public`, pas en `free_will`.
- `list_ancient_works`, `count_ancient_works`, `get_ancient_work`, `get_ancient_work_by_kg_id` existent en `public` et `free_will`.
- `list_passages`, `get_passage`, `get_text_stats` existent en `public`.
- `free_will.get_ancient_work(...)` et `free_will.get_ancient_work_by_kg_id(...)` sont casses en prod: ils referencent `full_text_normalized`, colonne absente de `free_will.ancient_works`.
- Le schema prod est plus riche que `database/schema/schema.sql`: colonnes et fonctions ne sont pas totalement synchronisees avec le repo.

### Plans / mesures releves en prod avant correctif

- `public.search_passages('καὶ', 20)`:
  - plan: `Bitmap Index Scan` sur `idx_passages_fts`, puis `Parallel Bitmap Heap Scan`, puis tri sur `ts_rank(to_tsvector(...))`
  - temps observe: `2108.824 ms`
  - cause: la GIN filtre bien, mais le classement recalcule `to_tsvector(...)` sur ~8.7k lignes larges.
- Variante a tri etroit sans materialisation du vecteur:
  - temps observe: `1271.583 ms`
  - gain partiel, mais le recalcul `to_tsvector(...)` reste dominant.
- Variante avec vecteur materialise + meme logique de tri:
  - temps observe: `120.058 ms`
  - conclusion: le gain principal vient bien de l'arret du recalcul `to_tsvector(...)`.
- Fallback `ILIKE` / REST (`text_content ILIKE '%...%' OR canonical_ref ILIKE '%...%'`):
  - avant index trigram: `239.571 ms`, `Seq Scan`
  - avec indexes trigram: `3.468 ms`, `BitmapOr`
- `list_ancient_works` tri auteur:
  - avant: `229.024 ms`
  - cause: comptage des citations pour toutes les oeuvres a chaque appel
  - requete ciblee sur la page courante: `17.346 ms`
- `list_ancient_works` tri `most_cited`:
  - variante ciblee: `39.821 ms`
- Fonctions deja saines:
  - `count_ancient_works`: `0.350 ms`
  - `get_ancient_work_by_kg_id`: `0.134 ms`
  - `get_ancient_work`: `0.050 ms`
  - `list_passages`: `4.859 ms`
  - `get_passage`: `0.059 ms`
  - `get_text_stats`: `38.822 ms`

### Exposition securite avant correctif

- `free_will.ancient_works`, `free_will.passages`, `free_will.passage_citations` etaient ouverts a `PUBLIC` avec `SELECT/INSERT/UPDATE/DELETE`.
- `free_will.users` donnait `SELECT/INSERT/UPDATE` a `authenticated`.
- `free_will.auth_audit_log` donnait `SELECT/INSERT` a `authenticated`.
- `free_will.dictionary_lsj` et `free_will.dictionary_lewis_short` donnaient `SELECT` a `PUBLIC`.
- Aucune RLS active sur les tables exposees.
- La plupart des RPC gardaient aussi `EXECUTE` pour `PUBLIC`.
- Plusieurs `SECURITY DEFINER` utilisaient un `search_path` explicite mais non minimal, typiquement `free_will, public`.

## 2. Changements SQL exacts

### Migrations ajoutees

- `database/migrations/20260313_01_passage_search_storage.sql`
- `database/migrations/20260313_02_passage_search_indexes.sql`
- `database/migrations/20260313_03_rpc_perf_and_security.sql`
- `database/migrations/20260313_04_frontend_rpc_bridges.sql`
- `database/migrations/20260313_05_work_kg_nodes_paging.sql`

### Correctifs performance

- Ajout de `free_will.passages.search_vector` en colonne `tsvector` stockee:
  - base: `to_tsvector('english', coalesce(text_content, ''))`
  - objectif: reutiliser un vecteur stable et ne plus recalculer `to_tsvector(...)` dans le hot path RPC.
- Ajout des indexes:
  - `idx_passages_search_vector_gin`
  - `idx_passages_text_content_trgm`
  - `idx_passages_canonical_ref_trgm`
- Remplacement de `public.search_passages(text, integer)`:
  - nouveau chemin en 2 etapes
  - classement sur un jeu etroit de candidats
  - jointure vers `passages` / `ancient_works` seulement apres le `LIMIT`
- Ajout de `public.search_passages(jsonb)`:
  - compatibilite noms de params: `query_text`, `p_query_text`, `queryText`, `q`, `query`, `search_query`, `max_results`, `p_max_results`, `maxResults`, `limit`, `filter_author`, `p_filter_author`, `author`, `filter_period`, `p_filter_period`, `period`, `filter_language`, `p_filter_language`, `search_language`, `language`
  - `search_language` est traite comme filtre de langue de corpus, pas comme `tsconfig` dynamique
- Remplacement de `public.search_passages_simple(text, integer)`:
  - fallback indexable via trigram
  - recherche sur `text_content` et `canonical_ref`
- Ajout de `public.search_passages_simple(jsonb)` pour la compatibilite RPC
- Refonte de `public.list_ancient_works` et `free_will.list_ancient_works`:
  - chemin rapide pour `author` / `title`: pagination d'abord, agregat citations ensuite seulement pour la page courante
  - chemin `most_cited`: agregat global unique puis tri
- `public.list_passages`:
  - limitation defensive de `p_limit`
  - `search_path` securise
- `public.get_text_stats`:
  - simplification du `COUNT(DISTINCT work_id)` en `COUNT(*)`

### Correctifs compatibilite

- `free_will.get_ancient_work(...)` et `free_will.get_ancient_work_by_kg_id(...)` sont repares sans changer leur contrat:
  - conservation de la colonne legacy `full_text_normalized`
  - valeur renvoyee: `NULL::text`
- Ajout de wrappers JSONB pour les RPC sensibles appeles avec conventions heterogenes:
  - `public.count_ancient_works(jsonb)`
  - `public.list_ancient_works(jsonb)`
  - `public.get_ancient_work(jsonb)`
  - `public.get_ancient_work_by_kg_id(jsonb)`
  - `public.list_passages(jsonb)`
  - `public.get_passage(jsonb)`
  - `public.search_passages(jsonb)`
  - `public.search_passages_simple(jsonb)`
- Ajout de RPC publics pour les chemins worker/front qui ne doivent plus dependre du REST direct sur `free_will`:
  - `public.search_passages_filtered(...)`
  - `public.search_passages_simple_filtered(...)`
  - `public.list_passage_refs(...)`
  - `public.list_passages_window(...)`
  - `public.count_passages_for_work(...)`
  - `public.get_best_passage_for_kg_node(...)`
  - `public.get_work_kg_nodes(...)`
  - `public.list_work_kg_nodes(...)`

## 3. Changements securite exacts

### Durcissement des fonctions

- `search_path` resserre sur les `SECURITY DEFINER` critiques:
  - `public.search_passages*`
  - `public.search_passages_simple*`
  - `public.list_passages*`
  - `public.get_passage*`
  - `public.get_text_stats`
  - `public.get_ancient_work*`
  - `public.list_ancient_works*`
  - `public.count_ancient_works*`
  - `public.get_passage_by_reference`
  - dictionnaires / autocompletion exposes via RPC
  - `free_will.autocomplete_lemmas_fuzzy`
- Politique suivie:
  - `pg_catalog, free_will` pour les fonctions de lecture
  - `pg_catalog, free_will, extensions` seulement quand l'extension est necessaire

### Durcissement des grants

- Revocation de l'`EXECUTE` implicite pour `PUBLIC` sur les RPC utilises par l'app.
- Regrant explicite uniquement a:
  - `anon`
  - `authenticated`
  - `service_role`
- Revocation des droits table trop larges:
  - `ancient_works`, `passages`, `passage_citations`, `kg_nodes`, `kg_edges` remis en lecture seule pour `anon/authenticated/service_role`
  - `users`, `auth_audit_log`, `dictionary_lsj`, `dictionary_lewis_short` fermes aux roles API

### RLS

- Activation de la RLS sur les tables exposees en lecture:
  - `ancient_works`
  - `passages`
  - `passage_citations`
  - `kg_nodes`
  - `kg_edges`
- Policies `SELECT USING (true)` pour `anon, authenticated` sur ces tables
- Activation de la RLS sans policy d'ouverture sur:
  - `users`
  - `auth_audit_log`
  - `dictionary_lsj`
  - `dictionary_lewis_short`

### Privileges par defaut

- Revocation des privileges par defaut qui recreent des expositions `PUBLIC`:
  - `EXECUTE` sur les fonctions de `public`
  - `EXECUTE` sur les fonctions de `free_will`
  - droits table/sequences `PUBLIC` dans `free_will`

### Tableau final

| Objet | Risque | Correctif applique | Impact compatibilite |
| --- | --- | --- | --- |
| `public.search_passages` | timeout sur requetes larges, tri couteux | `search_vector` stocke + nouveau plan en 2 etapes + wrapper JSONB | contrat legacy conserve, params alternatifs acceptes |
| `public.search_passages_simple` + fallback REST | `ILIKE '%...%'` en `Seq Scan` | indexes trigram `text_content` + `canonical_ref` + wrapper JSONB | comportement conserve, plus robuste |
| `public/free_will.list_ancient_works` | agregat citations global a chaque page | fast path pagine puis agrege seulement la page | meme shape de retour |
| `free_will.get_ancient_work*` | RPC casse sur colonne absente | `NULL::text AS full_text_normalized` | contrat conserve, plus d'erreur runtime |
| Tables corpus (`ancient_works`, `passages`, `passage_citations`) | ecriture publique et aucune RLS | revoke write + read-only grants + RLS read policies | lectures REST conservees |
| Tables KG (`kg_nodes`, `kg_edges`) | pas de RLS | RLS read policies | lectures REST conservees |
| `users`, `auth_audit_log` | acces direct `authenticated` injustifie | revoke direct access + RLS activee | pas d'usage app repo casse attendu |
| Dictionnaires | lecture directe `PUBLIC` inutile | revoke table access, conservation des RPC `SECURITY DEFINER` | routes lemma conservent les RPC |
| RPC exposes | `EXECUTE` implicite `PUBLIC` | revoke `PUBLIC`, grant explicite roles API | aucun impact pour l'app |
| `SECURITY DEFINER` critiques | `search_path` trop large | `pg_catalog` + schemas minimaux | aucun impact fonctionnel attendu |

## 4. Risques / compatibilite

- Risque principal evite:
  - ne pas creer `free_will.search_passages` en prod, pour ne pas introduire d'ambiguite de resolution entre `public` et `free_will`
- Compatibilite preservee:
  - signatures exactes actuelles conservees
  - wrappers JSONB ajoutes pour les variantes de noms de parametres
  - shape legacy de `free_will.get_ancient_work*` conservee
- Changement comportemental volontaire:
  - `search_language` ne pilote plus de `tsconfig` dynamique; il devient au mieux un filtre de langue de corpus quand la valeur est une langue connue
  - motivation: ne plus casser l'utilisation de l'index GIN stable
- Point de vigilance hors SQL:
  - la configuration "exposed schemas" PostgREST/Supabase n'est pas modifiable depuis ces migrations
  - verification manuelle recommandee pour s'assurer que seuls les schemas voulus sont exposes

## 5. Plan de deploiement

1. Appliquer `20260313_01_passage_search_storage.sql`
   - ajout de colonne sur `free_will.passages`
   - lock DDL court attendu vu le volume actuel (~13.5k passages)
2. Appliquer `20260313_02_passage_search_indexes.sql`
   - hors transaction
   - utilise `CREATE INDEX CONCURRENTLY`
   - pas de blocage long en ecriture attendu
3. Appliquer `20260313_03_rpc_perf_and_security.sql`
   - remplace les fonctions
   - durcit grants / RLS / default privileges
4. Invalider / recharger le schema cache PostgREST si necessaire
   - selon la config Supabase, cela peut etre automatique

## 6. Verifications post-deploiement

### Fonctionnelles

- `select count(*) from public.search_passages('καὶ', 20);`
- `select count(*) from public.search_passages(jsonb_build_object('q', 'καὶ', 'limit', 20));`
- `select count(*) from public.search_passages_simple(jsonb_build_object('query', 'ἐλευθερία', 'limit', 20));`
- `select count(*) from public.list_ancient_works(jsonb_build_object('author', 'Seneca', 'limit', 20));`
- `select count(*) from public.list_passages(jsonb_build_object('work_id', 'f0974fac-00e5-4a91-98d4-c0a5f406a37d', 'limit', 20));`
- `select * from free_will.get_ancient_work('f0974fac-00e5-4a91-98d4-c0a5f406a37d'::uuid) limit 1;`

### Performance

- `EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM public.search_passages('καὶ', 20);`
- `EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM public.search_passages_simple('ἐλευθερία', 20);`
- `EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM public.list_ancient_works(NULL, NULL, 'author', 50, 0);`
- verifier que:
  - `search_passages` ne recalcule plus `to_tsvector(...)` sur le hot path
  - `search_passages_simple` / fallback REST utilisent les indexes trigram
  - `list_ancient_works` ne fait plus l'agregat citations global pour un tri simple

### Securite

- `select has_table_privilege('anon', 'free_will.users', 'select');` doit renvoyer `false`
- `select has_table_privilege('authenticated', 'free_will.auth_audit_log', 'insert');` doit renvoyer `false`
- `select relrowsecurity from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'free_will' and c.relname in ('ancient_works','passages','passage_citations','kg_nodes','kg_edges','users','auth_audit_log');`
- `select has_function_privilege('anon', 'public.search_passages(text, integer)', 'execute');` doit renvoyer `true`
- `select has_function_privilege('anon', 'public.clean_expired_cache()', 'execute');`
  - a verifier manuellement si vous souhaitez aussi restreindre les RPC non couverts par cette intervention

## 7. Validation prod apres application

### Migrations appliquees

- `20260313_01_passage_search_storage.sql` appliquee en prod le `2026-03-13`
- `20260313_02_passage_search_indexes.sql` appliquee en prod le `2026-03-13`
- `20260313_03_rpc_perf_and_security.sql` appliquee en prod le `2026-03-13`
- correctif complementaire applique en prod le `2026-03-13` sur les wrappers JSONB `public.search_passages(jsonb)` et `public.search_passages_simple(jsonb)` pour couvrir aussi `p_query_text` / `p_max_results`
- `20260313_04_frontend_rpc_bridges.sql` appliquee en prod le `2026-03-13`
- `20260313_05_work_kg_nodes_paging.sql` appliquee en prod le `2026-03-13`
- worker Cloudflare redeploye le `2026-03-13` pour aligner les routes front:
  - alias `/api/works/search`
  - `/api/works/:workId/table-of-contents`
  - `/api/works/:workId/passages/by-reference`
  - `/api/works/:workId/kg-nodes`
  - `/api/texts/passage/:id/context` via RPC publics

### Resultats SQL observes apres application

- `free_will.passages.search_vector` present
- indexes presents:
  - `idx_passages_search_vector_gin`
  - `idx_passages_text_content_trgm`
  - `idx_passages_canonical_ref_trgm`
- compatibilite RPC confirmee:
  - `public.search_passages(text, integer)` et `public.search_passages(jsonb)` OK
  - `public.search_passages(jsonb)` accepte maintenant `query_text` et `p_query_text`
  - `public.search_passages_simple(jsonb)` accepte maintenant `query_text` et `p_query_text`
  - `public.list_ancient_works(jsonb)`, `public.count_ancient_works(jsonb)`, `public.get_ancient_work(jsonb)`, `public.get_ancient_work_by_kg_id(jsonb)`, `public.list_passages(jsonb)`, `public.get_passage(jsonb)` OK
- securite confirmee:
  - `anon` / `authenticated` n'ont plus `SELECT` sur `free_will.users`
  - `anon` n'a plus d'ecriture sur `free_will.passages`
  - `anon` garde `EXECUTE` sur les RPC publics critiques

### Mesures apres application

- benchmark a chaud:
  - `public.search_passages('καὶ', 20)`: ~`230 ms`
  - `public.search_passages('ἐλευθερία', 20)`: ~`44 ms`
  - `public.search_passages_simple('ἐλευθερία', 20)`: ~`122 ms`
  - `public.list_ancient_works(NULL, NULL, 'author', 50, 0)`: ~`60 ms`
  - `public.count_ancient_works(NULL, NULL)`: ~`40 ms`
  - `public.get_text_stats()`: ~`44 ms`
- plan confirme pour une recherche selective (`ἐλευθερία`):
  - `Bitmap Index Scan` sur `idx_passages_search_vector_gin`
  - plus aucun recalcul `to_tsvector(...)` dans le hot path
- pour une requete tres large (`καὶ`):
  - le planner choisit encore un `Seq Scan`, ce qui est cohérent vu la tres faible selectivite
  - temps observe reste largement sous le seuil qui provoquait les `57014`

### Verification via free-will.app

- OK:
  - `GET /api/works`
  - `GET /api/works?language=grc&limit=5`
  - `GET /api/works/stats`
  - `GET /api/works/stats/overview`
  - `GET /api/texts/stats/overview`
  - `GET /api/works/:workId`
  - `GET /api/works/:workId/passages`
  - `GET /api/works/passage/:passageId`
  - `GET /api/works/by-kg/:kgWorkId`
  - `GET /api/works/search/passages?q=ἐλευθερία`
  - `GET /api/works/search/passages?q=καὶ`
  - `GET /api/works/search?query=ἐλευθερία`
  - `GET /api/works/:workId/table-of-contents`
  - `GET /api/works/:workId/passages/by-reference?reference=...`
  - `GET /api/works/:workId/kg-nodes`
  - `GET /api/texts/passage/:passageId/context`
  - `GET /api/texts/passage/:kgNodeId/context`
  - `GET /api/lemma/dictionary/search/λογος?language=grc`
  - `GET /api/lemma/dictionary/λογος?language=grc`
- Etat final:
  - plus aucun endpoint front critique verifie n'est en echec
  - le lecteur de contexte (`/api/texts/passage/:id/context`) est retabli
  - la recherche avancee front (`/api/works/search`) est retablie
  - `CanonicalTextReader` a maintenant ses routes `table-of-contents` et `by-reference`
  - `AncientWorksListingPage` recupere de nouveau les `kg_nodes` du work complet sans troncature a 1000
