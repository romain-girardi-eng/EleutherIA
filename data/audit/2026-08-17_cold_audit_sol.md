# Audit à froid d’EleutherIA après v5.2.0

**Date de l’état audité :** 17 août 2026  
**Périmètre :** `data/kg/*.jsonl`, `data/corpus/*.jsonl`, pipeline GraphRAG, gates/CI, opérations de déploiement et bibliothèque secondaire locale.  
**Méthode :** lecture seule ; recomptages directs des JSONL ; traçage statique des chemins snapshot/SQL ; exécution en lecture seule des gates `check_corpus_invariants --strict`, `check_ingestion_rules --strict` et `check_citations_gate --all` ; inventaire récursif de la bibliothèque locale. Aucun fichier de données, de code ou de configuration n’a été modifié.

## 1. Contrôle de dix affirmations des rapports `applied.md`

Le résultat brut est **9 affirmations encore vraies aujourd’hui, 1 affirmation qui ne décrit plus l’état actif**. Cela confirme que le cycle précédent a réellement appliqué l’essentiel de ses corrections mécaniques. Le problème résiduel n’est pas une annulation générale de ces réparations : ce sont surtout des synchronisations partielles entre couches, des gates non exécutoires et des consommateurs qui ignorent les nouveaux marqueurs.

| # | Affirmation échantillonnée | Résultat aujourd’hui | Preuve directe |
|---:|---|---|---|
| 1 | Le placeholder Fee a été supprimé, avec ses trois arêtes (`2026-08-14_curation_artifact_cleanup_applied.md:15,61,69-73`). | **TIENT** | `scholarly_argument_fee_determinism_and_predestination_1` est absent de `nodes.jsonl`; zéro arête active ne le mentionne. |
| 2 | L’année de Craig a été corrigée de 1990 à 1991 (`2026-08-16_deep_audit_bibliographic_applied.md:24`). | **TIENT** | `pub_craig_1991_divine_foreknowledge_human_freedom`, `metadata.year=1991`. |
| 3 | L’encodage de l’arête `2958afb3-…` a été normalisé (`2026-08-16_deep_audit_structural_applied.md:653`). | **TIENT** | `data/kg/edges.jsonl:43068` : `source=source_id` et `target=target_id`. Le recomptage global donne zéro paire désaccordée. |
| 4 | 596 nœuds portent la traduction anglaise appliquée (`2026-08-16_french_translation_applied.md:29`) et chaque nœud touché porte le stamp annoncé (`:15-16`). | **NE TIENT PLUS AUJOURD’HUI** | Seulement **573** nœuds actifs portent `metadata.translation_2026_08_16="gpt-5.6-terra"`. L’écart de 23 est compatible avec les fusions/suppressions ultérieures, mais le rapport ne peut plus servir de statistique courante. |
| 5 | La prémisse P2 de l’argument de Sénèque pointe désormais `passage_sen_prov_2_4` (`2026-08-16_second_sweep_applied.md:251-256`). | **TIENT** | `data/kg/nodes.jsonl:1`, `metadata.legacy_premises[P2].primary_sources`. |
| 6 | Les 11 œuvres conflationnées ont été ramenées à zéro (`2026-08-17_work_conflation_applied.md:4-6`). | **TIENT selon la métrique annoncée** | Recalcul de R3 : aucune œuvre ne contient aujourd’hui des enfants `passage` portant plusieurs `work_canonical_id`. Cette réussite masque toutefois deux identifiants internes contradictoires (H-05). |
| 7 | L’arête Boèce → Aristote a été retournée en `influenced_by` (`2026-08-17_factual_corrections_applied.md:5`). | **TIENT** | `data/kg/edges.jsonl:30473`, arête `554dc681-…`, relation `influenced_by`. |
| 8 | L’arête Salles/Bobzien `c6393385-…` est devenue `opposes` (`2026-08-17_dialectical_repairs_applied.md:7`). | **TIENT** | `data/kg/edges.jsonl:47847`, relation `opposes`. |
| 9 | Les 82 segments Methodius ont été requalifiés comme apparatus à remapper (`2026-08-17_linguistic_repairs_applied.md:255-336`). | **TIENT** | 82 nœuds portent `needs_locus_mapping=true`, tous de type `passage`, avec `content_kind=apparatus_gcs`. |
| 10 | La vague sémantique a créé 1 arête `same_thesis_as` au lot 5 et 53 au lot 6 (`2026-08-17_semantic_merges_applied.md:12-14`). | **TIENT** | 54 arêtes `same_thesis_as` actives, réparties en 33 composantes de taille 2 à 4. |

### Conclusion du spot-check

Les affirmations mécaniques choisies ne révèlent pas de rollback caché. En revanche, le contrôle #4 confirme qu’un `applied.md` est une photographie d’application, pas un registre d’état. Il faut cesser d’en réutiliser les totaux sans les régénérer, et publier un manifest courant séparé.

## 2. Verdict exécutif

L’état v5.2.0 n’est pas prêt à être qualifié de « cohérent de bout en bout » pour la synthèse savante. Les réparations du KG sont souvent justes **dans `nodes.jsonl`/`edges.jsonl`**, mais plusieurs ne sont pas propagées au miroir corpus ni réellement consommées par le runtime.

Les cinq risques dominants sont :

1. un **split-brain KG/corpus** de grande ampleur, notamment les 709 passages Plotin remappés dans le KG mais tous laissés avec les anciens loci dans le corpus ;
2. les couches Scholar-RAG, referee et triage sont **désactivées par défaut et non documentées dans les `.env.example`** ;
3. les marqueurs d’honnêteté et de dette sont **invisibles aux filtres de retrieval**, alors même que les nœuds marqués restent citables ;
4. le gate dialectique R16 omet plusieurs classes de relations que la carte de controverse traite pourtant comme des fault lines ;
5. la procédure de déploiement hôte recommandée ouvre une fenêtre de tables vides/partielles et finit par réinjecter le miroir corpus périmé.

## 3. Findings classés par sévérité

## CRITICAL

### C-01 — Le remap Plotin n’a pas été propagé au corpus ; snapshot et SQL citent deux loci différents

**Lentilles : DATA, RETRIEVAL, OPS.** Les 709 nœuds `passage_plotinus_vi_9_*` ont un `canonical_ref` et un `cts_urn` corrigés dans le KG, mais chacune des 709 lignes correspondantes de `data/corpus/citations.jsonl` mène à une ligne corpus portant encore l’ancien faux locus. Exemple :

- `data/kg/nodes.jsonl:10599` : `passage_plotinus_vi_9_267`, `canonical_ref="Enn. V.9.6"`, `cts_urn=…:5.9.6` ;
- `data/corpus/citations.jsonl:12` : ce nœud pointe sur `001aba70-…` ;
- `data/corpus/passages.jsonl:12209` : le passage se présente comme `Enn. VI.9.267`, `cts_urn=…:6.9.267`.

Ce n’est pas un accident isolé : **709/709** paires Plotin ont les deux champs divergents. L’applier n’ouvre que `nodes.jsonl` et `edges.jsonl` et ses invariants ne regardent pas le corpus (`scripts/apply_2026_08_17_plotinus_remap.py:259-308`).

L’impact est dépendant de l’environnement : le fallback snapshot fabrique la référence depuis le nœud corrigé (`graphrag/src/eleutheria_graphrag/services/snapshot_retrieval.py:81-125`), tandis que le chemin DB rend `p.canonical_ref` depuis les tables corpus (`graphrag/src/eleutheria_graphrag/agents/tools/read_passages.py:223-293`). Le même appel peut donc donner une bonne ou une mauvaise référence selon la disponibilité de PostgreSQL.

**Action cadrée :** construire un gate de parité `citation passage-node → corpus passage` comparant `canonical_ref`, `cts_urn`, rôle et work id ; remapper atomiquement les 709 lignes corpus Plotin et leurs lignes DB ; ajouter un test exécutant le même échantillon en `SnapshotStrategy` et `SQLStrategy` et exigeant des sorties identiques.

### C-02 — La couche Scholar-RAG nouvellement construite est inactive dans la configuration reproductible

**Lentille : RETRIEVAL/PIPELINE.** `scholar_rag_enabled()` est explicitement « default OFF » (`graphrag/src/eleutheria_graphrag/agents/state.py:175-184`). Le referee (`dialectical_synthesis.py:1614-1621`) et la relevance triage (`relevance_triage.py:186-193`) sont eux aussi off par défaut. Les variables `ELEUTHERIA_SCHOLAR_RAG`, `ELEUTHERIA_REFEREE` et `ELEUTHERIA_RELEVANCE_TRIAGE` sont absentes de `.env.example` et `deploy/production/.env.example`; elles sont également absentes du `.env` local inspecté par noms de clés.

Le résultat est net : le chemin documenté et reproductible n’emploie ni `find_debates`, ni `build_controversy_frame`, ni le referee. Les 77 arêtes corridor/faultlines ajoutées et les 54 liens `same_thesis_as` n’améliorent donc pas la synthèse par défaut.

**Action cadrée :** décision explicite de Romain : (a) activer Scholar-RAG et referee en production, avec canary et métriques, ou (b) annoncer qu’ils sont expérimentaux. Dans le cas (a), ajouter les trois variables aux deux exemples, un endpoint de health indiquant les flags effectifs et un smoke test de prod qui échoue si une question dialectique ne passe pas par la carte.

### C-03 — Les marqueurs d’honnêteté et de dette ne protègent pas la synthèse

**Lentilles : DATA, RETRIEVAL.** Aucun code runtime ne lit `citation_verdict`, `bibliographic_import`, `needs_reocr`, `needs_locus_mapping`, `needs_text_ingestion`, `needs_reference_remapping`, `translation_blocked_ocr` ou `origenality_relevance`. La recherche dans `graphrag/src`, `backend`, `knowledge graph/src` et `database/src` ne trouve aucun consommateur de ces clés. Le seul filtre de description repose sur `metadata.integrity_status` (`agents/graph_helpers.py:21-45`), champ actuellement absent de tous les nœuds.

La dette reste activement exposée :

- 136 nœuds marqués `needs_text_ingestion` ont 137 lignes dans `citations.jsonl` ;
- les 82 `needs_locus_mapping` ont chacun une citation active ;
- les 4 `needs_reocr` ont 7 lignes de citation ;
- les 2 `translation_blocked_ocr` ont chacun une citation active.

Exemples : `passage_aristide_sc470_5_en` (`nodes.jsonl:2609`) est un faux doublon non traduit, bloqué par OCR, mais sa citation mène à un corpus de 280 caractères disloqués ; `passage_boethius_cons_23` (`nodes.jsonl:3409`) porte `needs_reocr=true` mais reste citée ; les 82 apparatus Methodius sont tous servis comme passages.

**Action cadrée :** définir une fonction centrale `evidence_policy(metadata)` avec trois statuts (`citable`, `discoverable_only`, `blocked`) ; l’appliquer dans `search_nodes`, `search_passages`, `read_passages`, `passage_row_from_node`, le packer et le referee. La présence d’une dette doit empêcher la citation, tout en laissant le nœud découvrable avec une explication.

### C-04 — Le gate dialectique omet les classes que le pipeline rend comme désaccords

**Lentilles : DATA, PIPELINE, GATES.** R16 ne couvre que `opposes`, `agrees_with`, `critiques` (`scripts/check_ingestion_rules.py:163-165,666-701`). La carte de controverse traite en plus `responds_to`, `refutes`, `contrasts_with` et `supports` comme fault lines (`agents/tools/build_controversy_frame.py:104-115`) et les sérialise ensuite sans autre attestation (`controversy_map.py:297-299`).

Population aujourd’hui : 60 `responds_to` (1 avec `attested_by`), 181 `supports` (0), 5 `contrasts_with` (0). Ce sont **245 arêtes non attestées** dans des classes capables d’entrer dans la prose dialectique. Le referee déterministe valide un marqueur `[P_*]` dès que l’id se résout (`scholar_verification.py:251-285`) et ne vérifie pas la vérité de `[edge:*]`.

**Action cadrée :** une seule constante de relations dialectiques partagée par gate, collector, frame builder et referee ; R16 doit exiger `attested_by` + proposition paginée pour toute arête narrée comme relation savante. Ajouter une résolution déterministe des marqueurs `[edge:*]` contre la carte et refuser toute relation non attestée.

### C-05 — Le déploiement hôte recommandé n’est ni atomique ni sans interruption

**Lentille : OPS.** Le workflow désactivé indique comme chemin hôte : `bootstrap_supabase.py --replace-data && sync_corpus_to_db.py --commit` (`.github/workflows/kg-deploy.yml:33-38`). Or :

- `bootstrap_supabase.py` exécute le `TRUNCATE` puis plusieurs lots sans transaction englobante (`database/scripts/bootstrap_supabase.py:222-365,849-879`) ;
- `sync_corpus_to_db.py` affirme dans sa docstring opérer « inside one transaction » (`:2-8`), mais tronque volontairement dans une transaction séparée puis charge par lots implicitement commités (`:88-99,128-167`) ;
- la seconde commande remplace justement les tables corrigées depuis le KG par `data/corpus/*.jsonl`, où le remap Plotin est périmé.

Une panne entre deux lots laisse donc un corpus partiel, visible par le backend. Le `--replace-data` crée aussi une fenêtre où le KG est vide.

**Action cadrée :** déploiement blue/green de tables versionnées (`kg_nodes_next`, `passages_next`) avec validation complète, puis swap transactionnel de vues/schémas ; à défaut, mettre le backend en maintenance et charger dans des tables staging. Interdire la séquence hôte actuelle tant que la parité KG/corpus n’est pas verte.

## HIGH

### H-01 — L’import Origenality contient un bloc de faux « core » et un doublon déjà lu

**Lentilles : DATA, SCHOLARLY VALUE.** Les 198 nouveaux records portent tous `origenality_relevance="core"`, ce qui ne constitue plus une densité mais une constante. Plus grave : 29 records attribués à Michel Fédou sont des lignes d’un bulletin bibliographique. Vingt-huit ont exactement le même abstract sur le *Traité de la prière* alors que les titres portent sur la Réforme néerlandaise, Levinas, les musiciens d’église, le wokisme, etc. Exemple manifeste : `pub_fedou_2026_kooi_la_reforme…` (`nodes.jsonl:19866`) est classé `anthropology.free-will` avec un abstract sur Origène.

L’import a aussi créé `pub_sytsma_2018_reconciling…` (`nodes.jsonl:19978`) comme record « unread », alors que la même dissertation est déjà le témoin effectivement lu derrière `pub_sytsma_2020_universal_salvation_origen` (`nodes.jsonl:18906`) et porte 12 arguments paginés (`nodes.jsonl:1295-1306`).

**Action cadrée :** quarantaine immédiate des 29 records Fédou ; merge Sytsma 2018 dans le record 2020 avec alias d’édition ; relancer le matching sur DOI/ISBN + titre alternatif + `phd_version`, et rendre `origenality_relevance` gradué (`core`, `adjacent`, `background`, `reject`) avec justification.

### H-02 — `same_thesis_as` n’est consommé nulle part et peut compter une thèse plusieurs fois

**Lentilles : RETRIEVAL, SCHOLARLY VALUE.** Les 54 arêtes forment 33 composantes, mais `same_thesis_as` n’apparaît dans aucun fichier GraphRAG. `build_controversy_frame` ne le traverse pas, la triage identifie chaque `position_id` séparément (`controversy_map.py:500-539`), la complétude recompte chaque position et le referee considère chaque id résolu comme une source indépendante.

Deux liens de l’échantillon sont eux-mêmes trop larges :

- `argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction` ↔ `scholarly_argument_bobzien_chrysippus_compatibilism_fate__1` (`edges.jsonl:48662`) confond l’analogie causale du cylindre avec la théorie distincte des co-fated events ;
- `argument_frede_2011_notion_is_technical_and_datable` ↔ `scholarly_argument_frede_origin_of_free_will_0` (`edges.jsonl:48675`) confond la databilité générale du concept avec la conclusion spécifique « première chez Épictète ».

**Action cadrée :** transformer `same_thesis_as` en composantes d’équivalence utilisées pour dédupliquer le prompt, le comptage de witnesses et le ranking ; conserver un seul représentant par auteur/publication et exposer les variantes comme extractions parallèles. Revoir les deux arêtes trop larges en `related_to` ou les scinder en thèses atomiques.

### H-03 — Neuf citations pendantes échouent en mode strict mais passent la CI

**Lentilles : DATA, GATES.** `check_corpus_invariants --strict` donne 9 `citation->passage` et 9 `citation->kg_node` pendantes, toutes `passage_simpl_in_ench_1..9` (`citations.jsonl:845,1137,2596,3632,7315,7532,7804,13321,13894`). Ces nœuds et passages ont été supprimés lors de la correction Simplicius/Theophraste, sans nettoyage du miroir citation.

La CI appelle le gate sans `--strict` (`.github/workflows/ci.yml:91-95`) ; le script annonce lui-même qu’en mode report il retourne toujours 0 (`scripts/check_corpus_invariants.py:1-6,30-42`). Le rouge est donc connu mais non bloquant.

**Action cadrée :** supprimer/remapper ces neuf citations ; passer la CI à `--strict` ; ajouter les trois unicités `(passage_id)`, `(kg_node_id)` résoluble et paire citation unique.

### H-04 — Le gate d’ingestion principal n’est pas dans la CI et son mode global n’est pas exécutoire

**Lentille : GATES.** `.github/workflows/ci.yml:66-105` exécute SHACL, le corpus en mode report et le gate de manifest bibliographique, mais jamais `check_ingestion_rules.py`. En mode global, ce dernier retourne 0 par défaut malgré les BLOCK (`scripts/check_ingestion_rules.py:777-835`). L’exécution `--strict` sur l’état actuel remonte 1 854 BLOCK et 1 051 WARN ; une partie des BLOCK R2 est du bruit, car l’identité de passage sur `cts_urn+role` est trop grossière pour les chunks, ce qui explique probablement pourquoi le gate n’a pas été activé.

**Action cadrée :** séparer les règles réellement bloquantes des audits de dette ; corriger R2 en incorporant un span/sequence ou un id de chunk ; intégrer ensuite le mode global strict dans CI. Aucun applier ne doit être la seule porte d’entrée du gate.

### H-05 — Les réparations d’identifiants d’œuvre ont créé deux contradictions internes

**Lentille : DATA.** `work_simplicius_in_enchiridion` (`nodes.jsonl:19503`) affirme correctement dans `canonical_id` et `verified_reference` que Simplicius est `tlg4013.tlg001`, mais conserve `work_canonical_id=tlg0093.tlg001` dérivé des neuf passages Theophraste désormais supprimés. `work_galen_de_placitis` (`nodes.jsonl:19408`) juxtapose de même `canonical_id=tlg0057.tlg032`, déclaré correct, et `work_canonical_id=tlg0057.tlg010`, dérivé de trois enfants.

R3 ne voit rien : ces œuvres n’ont plus plusieurs classes d’enfants. Il vérifie la pluralité externe, pas la contradiction interne du nœud.

**Action cadrée :** gate d’égalité sémantique entre `canonical_id`, `work_canonical_id`, `cts_urn` et les enfants, après normalisation des formats. Pour Simplicius, supprimer la valeur dérivée Theophraste ; pour Galien, réadjudication des trois passages avant toute réécriture.

### H-06 — La couche dialectique reste très peu représentative des débats du graphe

**Lentille : SCHOLARLY VALUE.** Sur 25 nœuds `debate|controversy`, 22 n’ont aucune arête dialectique incidente au sens large ; seuls `debate_divine_foreknowledge_future_contingents`, `debate_stoic_compatibilism` et `controversy_synod_of_dort` en ont directement. Les grands hubs — Alexander/Stoics, discovery of will, Christian/Gnostic freedom, prohairesis, Carneadean anti-astrology — dépendent tous du fallback lexical (`build_controversy_frame.py:241-256,346-387`).

Les 21 `opposes` sont concentrés sur l’origine de la volonté et quelques controverses modernes ; ils ne constituent pas encore une carte représentative de la controverse chrétienne anti-gnostique, de la grâce, de l’astrologie ou de l’appropriation médio-platonicienne.

**Action cadrée :** modèle éditorial « débat → positions atomiques → relations attestées → passages contestés » pour les six débats centraux de la thèse, sans accroître d’abord le nombre brut d’arêtes. La couverture doit être mesurée par fault line savante, pas par total relationnel.

### H-07 — Le déploiement par défaut peut laisser les corrections de métadonnées hors production

**Lentille : OPS.** Le workflow KG choisit `only-new` par défaut (`.github/workflows/kg-deploy.yml:59-66,254-278`) : les corrections de métadonnées sur des nœuds existants ne sont donc pas poussées. La parité post-déploiement est `continue-on-error: true` et ne fait qu’émettre un warning (`:280-307`). C’est précisément la classe de changements réalisée massivement en v5.2.0.

**Action cadrée :** défaut `smart-diff`, avec batchs et retry ; rendre rouge toute divergence résiduelle qui n’est pas explicitement allowlistée. Le mode `only-new` doit devenir un escape hatch nommé, jamais le défaut.

### H-08 — Les identifiants CTS du corpus ne sont ni uniques ni cohérents avec leurs loci

**Lentilles : DATA, GATES.** Les 97 lignes corpus Methodius `PG 18.1..97` ont toutes le même `cts_urn=urn:cts:greekLit:tlg0338.tlg307.perseus-grc1:1.1`, malgré 97 textes et références distincts et un `work_canonical_id` de famille `tlg2959`. Exemple `passages.jsonl:12871`, relié par `citations.jsonl:3009`. Au total, 97 groupes de CTS URN associent simultanément plusieurs `canonical_ref` et plusieurs textes ; certains sont des chunks légitimes, mais le cas Methodius est indéfendable comme identifiant de passage.

**Action cadrée :** gate `cts_urn → locus stable` : soit l’URN est au niveau œuvre et doit être stocké comme tel, soit il identifie un passage et ne peut désigner 97 loci. Ajouter `source_span_id` pour les fragments/appareils qui ne possèdent pas de CTS canonique au lieu de fabriquer une précision.

## MEDIUM

### M-01 — 129 lignes de citation sont des doublons exacts

**Lentille : DATA.** `citations.jsonl` contient 129 paires strictement dupliquées jusque dans `citation_type` et `confidence`. Exemple : les lignes 120 et 121 sont identiques pour `passage_boethius_cons_76`. En ignorant le type, 411 paires `(passage_id,kg_node_id)` sont répétées.

**Action cadrée :** contrainte unique DB et gate JSONL sur `(passage_id, kg_node_id, citation_type)` ; déduplication déterministe en conservant la meilleure confiance et en fusionnant les notes.

### M-02 — Le vocabulaire d’honnêteté est typé comme prose, pas comme politique queryable

**Lentille : DATA.** `citation_verdict` est relativement propre (2232 `verified`, 569 `corrected`, 198 `bibliographic_import`, 16 `false_positive_attested`), mais 124 nœuds ont `citation_verified=true` sans verdict. `source_rank` compte 237 valeurs mais est une phrase libre très longue, dont 198 copies identiques ; `provenance` est un objet sur 352 nœuds et une chaîne sur 6. La politique est donc difficile à requêter et impossible à ordonner de façon stable.

**Action cadrée :** schéma versionné : `evidence_status` enum, `source_kind` enum, `peer_review_status`, `read_status`, `local_copy_status`, `verification_date`, `provenance[]`. Conserver la prose dans `honesty_note`, pas dans le champ de décision.

### M-03 — `needs_evidence` existe dans deux emplacements et n’est honoré par aucun consommateur

**Lentilles : DATA, PIPELINE.** Neuf arguments portent `needs_evidence=true` au top level (`nodes.jsonl:247,366,375,385,495,496,898,1267,1318`) ; sept autres le portent dans metadata. L’export RDF ne lit que metadata (`knowledge graph/src/eleutheria_kg/semantic/rdf_export.py:275-282`) et le runtime ne lit ni l’un ni l’autre.

**Action cadrée :** migration vers `metadata.evidence_status="needed"` et suppression du top-level après gate de parité ; blocage de citation identique à C-03.

### M-04 — Les fichiers de stats livrent trois états différents

**Lentille : DATA/OPS.** Fichiers actifs : 19 994 nœuds et 49 468 arêtes. `data/stats.json` en annonce 49 391 (avant les 77 arêtes corridor/faultlines) ; `data/kg/stats.json` annonce 20 060/56 448 ; `data/kg/_snapshot.json` 20 060/56 734. Aucun workflow ne lance `scripts/gen_stats.py --check`.

**Action cadrée :** une seule statistique générée depuis les fichiers actifs ; `--check` obligatoire en CI ; traiter `_snapshot.json` comme manifest historique nommé/daté ou le régénérer avec chaque snapshot.

### M-05 — Dérive d’environnement et runbooks non reproductibles

**Lentille : OPS.** Soixante et une variables utilisées par le runtime/compose ne figurent dans aucun des deux `.env.example`. Les plus importantes ici sont `ELEUTHERIA_SCHOLAR_RAG`, `ELEUTHERIA_REFEREE`, `ELEUTHERIA_DB_SCHEMA`, `ELEUTHERIA_SYNTH_CONTEXT_TOKENS`, `ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS` et `DB_POOL_ACQUIRE_TIMEOUT`. Inversement, plusieurs clés documentées ne sont plus lues sous ce nom.

`docs/development/auto-deploy.md:47,60-63` et le playbook d’incident renvoient à `deploy/deploy-compose.yml`, fichier absent du dépôt ; le label Watchtower annoncé n’apparaît dans aucun compose. `deploy/production/README.md:126-127` recommande `docker compose restart backend`, commande qui ne recharge ni image ni `env_file`.

**Action cadrée :** générer les `.env.example` depuis un registre typé ; test CI des clés compose/code ; remplacer les références au compose absent par le vrai propriétaire de configuration ; documenter `up -d --force-recreate` pour toute modification d’environnement/image.

### M-06 — Le pin G6 reste un couplage textuel fragile et partiel

**Lentille : GATES.** `test_reachability_probe.py:199-212` impose exactement 21 `opposes`. L’applier faultlines lit ce nombre en regex dans le code du test (`scripts/ingest_2026_08_17_faultlines_wiring.py:130-135`) et ne refuse l’écriture que dans ce seul script (`:216-266`). Une autre ingestion ou un edit de données peut modifier `opposes` sans passer par ce mécanisme. Le test écrit en outre un rapport dans le dépôt (`test_reachability_probe.py:372-405`).

**Action cadrée :** remplacer le nombre magique par un fixture JSON versionné listant les edge ids attendus et les contrats de reachability ; gate global sur tout diff KG ; aucun test ne doit écrire dans l’arbre source.

### M-07 — La bibliothèque locale a dépassé son inventaire publié

**Lentille : INGESTION.** Inventaire réel : **758 fichiers**, dont 396 PDF, 270 Markdown et 56 TXT, pour 3,83 Go. Le `MANIFEST.md` local, daté du 2 juillet, annonce encore 288 PDF, 241 Markdown et 52 TXT. Le sous-dossier `_acquisitions` contient 108 fichiers et concentre la majorité des prochaines lectures utiles.

**Action cadrée :** régénérer le manifest avant chaque décision d’ingestion ; y ajouter le mapping vers publication node, nombre d’arguments, statut lu/non lu et motif de priorité.

### M-08 — Les quatre grandes lacunes du corridor restent ouvertes

**Lentille : SCHOLARLY VALUE.** Le rapport corridor est juste sur ce point (`golden_corridor_report.md:599-624`) : Tatien Or. 7/10 n’a pas de lecture argumentative propre ; Irénée IV.38-39 manque en texte/arguments ; Clément n’a que six passages grecs et deux arguments sont ancrés sur les mauvais II.11.50-52 (`:419-449`) ; Philocalie 22-27 et le Commentaire sur Romains 7/9 restent incomplets (`:466-532`). Aucun développement postérieur ne ferme ces quatre dossiers.

**Action cadrée :** quatre projets séparés avec leurs propres gates de texte, d’argument et de réception ; ne pas les masquer par davantage de wiring secondaire.

## LOW

### L-01 — Les conventions de sérialisation restent hétérogènes mais sont actuellement normalisées par les loaders

**Lentille : DATA.** `metadata` est un objet pour 4 458 nœuds et une chaîne JSON pour 15 536 ; `alternative_names` est presque toujours la chaîne `"[]"`, parfois une liste, parfois `null`; les timestamps mélangent espace/`+00:00` et ISO `T+00:00`. Les loaders corrigent `metadata` (`knowledge graph/src/eleutheria_kg/services/snapshot.py:232-273`; `graphrag_service.py:401-441`), d’où une sévérité basse, mais les scripts ad hoc ne le font pas tous.

**Action cadrée :** format canonique JSONL unique à la prochaine réécriture globale, puis gate de type par champ.

### L-02 — Les `applied.md` sont pris à tort pour des manifests courants

**Lentille : OPS/AUDIT.** Le décompte de traduction 596 → 573 et les counts de nœuds/arêtes historiques illustrent une ambiguïté documentaire, pas une corruption à eux seuls.

**Action cadrée :** en-tête standard `snapshot_before`, `snapshot_after`, `still_current=false`; publier séparément `data/audit/current_state.json` dérivé à chaque release.

## 4. Échantillon de 15 éléments des nouvelles couches

### 4.1 Origenality / `bibliographic_import` (5)

| Élément | Verdict | Justification |
|---|---|---|
| `pub_achternkamp_2019_natural_law_in_origen_anthropology` (`nodes:19797`) | **Correct comme notice non lue** | Auteur, année, titre, DOI et abstract sont cohérents ; `citation_verdict` et `source_rank` disent honnêtement « unread ». |
| `pub_alviar_2022_origen_theological_anthropology` (`nodes:19798`) | **Correct comme chapitre non lu** | DOI de chapitre et référence à l’*Oxford Handbook of Origen* ; pas de prétention à une lecture locale. |
| `pub_bagby_2023_origen_and_prophecy…` (`nodes:19804`) | **Partiel** | C’est un compte rendu de Hall, non le livre de Hall. Le record est bibliographiquement honnête, mais son tag `core` et son wiring au concept de liberté favorisent une confusion auteur de review/auteur de thèse. |
| `pub_fedou_2026_kooi_la_reforme…` (`nodes:19866`) | **Incorrect** | Livre sur la Réforme néerlandaise, mais abstract sur le *De oratione* et thèmes `free-will/prayer`; contamination de span. |
| `pub_sytsma_2018_reconciling…` (`nodes:19978`) | **Incorrect comme nouveau record** | Doublon de la dissertation déjà lue sous `pub_sytsma_2020…` (`nodes:18906`) et de ses 12 arguments. |

### 4.2 `same_thesis_as` (5)

| Arête | Verdict | Justification |
|---|---|---|
| Dihle Greek intellectualism ↔ `concept_greek_intellectualism_dihle` (`edges:48692`) | **Correct** | Même thèse et même formulation structurante, granularité concept/argument. |
| Fürst Christian innovation ↔ `concept_freiheitspathos_furst` (`edges:48649`) | **Correct** | Les quatre propriétés et le périmètre Kap. IV sont les mêmes. |
| CAFMA sanctions ↔ Amand incentives (`edges:48644`) | **Partiel** | Amand dit que IV est un cas particulier de III ; le nœud CAFMA conflue déjà les deux. Le lien est utile mais ne doit pas signifier identité totale. |
| Bobzien cylinder ↔ Bobzien compatibilism/co-fated (`edges:48662`) | **Trop large** | Analogie des causes internes et théorie des événements cofatals sont compatibles mais distinctes. |
| Frede technical/datability ↔ Frede Epictetus-first (`edges:48675`) | **Trop large** | La première est un argument méthodologique général, la seconde une localisation historique spécifique. |

### 4.3 Corridor / faultlines (5)

| Arête | Verdict | Justification |
|---|---|---|
| `corridor-wiring-001` (`edges:49392`) | **Correct** | L’argument Irénée et le passage IV.37.1 nomment le même locus. |
| `corridor-wiring-002` (`edges:49393`) | **Correct** | Le `verified_reference` du CAFMA inclut explicitement Cicéron *De fato* 31, dont le latin est présent (`nodes:3695`). |
| `corridor-wiring-026` (`edges:49417`) | **Incorrect/insuffisant** | Le nœud Sagnard est fondé sur SC 34, livre III, et reconnaît lui-même qu’IV.37-39 appartient au livre IV « forthcoming ». Cela ne justifie pas `cites_primary_source` vers l’œuvre IV comme lecture directe. |
| `corridor-wiring-038` (`edges:49429`) | **Correct mais à garder comme réception savante** | Löhr p. 385 atteste l’extension Clément → Origène ; il ne faut pas transformer cette arête en dépendance textuelle primaire. |
| `faultlines-20260817-001` (`edges:49437`) | **Correct** | Le nœud Acosta (`nodes:429`) et ses pages 32-35 critiquent explicitement la méthode/datation de Frede. |

**Bilan de l’échantillon :** 8 corrects, 2 partiels, 5 à corriger ou resserrer. La nouvelle couche n’est donc pas un simple succès quantitatif : ses erreurs se concentrent exactement dans les classes « notice de review prise pour l’objet », « span de bulletin propagé », « identité de thèse trop large » et « source secondaire qui ne lit pas le livre invoqué ».

## 5. Valeur savante et épaisseur réelle du graphe

### Stations encore minces

1. **Clément d’Alexandrie** est désormais la station la plus coûteuse pour la thèse : texte sous-ingéré, deux mauvais ancrages, réception déjà mieux câblée que le socle ancien. C’est la priorité intellectuelle principale.
2. **Tatien Or. 7 et 10** : le texte est là, mais la lecture argumentative manque. Il faut distinguer création des êtres αὐτεξούσιοι, prohairesis, chute angélique et polémique astrale, sans résumer tout Tatien sous « anti-fatalisme ».
3. **Irénée IV.38-39** : le danger est double, lacune textuelle et rétroprojection de la soul-making theodicy de Hick. La croissance/immaturité et la responsabilité doivent être reconstruites depuis SC 100 avant de les transformer en argument moderne.
4. **Origène hors *De principiis* III.1** : le graphe est très épais sur III.1 et la réception générale, mais mince sur *Contra Celsum* IV.45/V.21, *Commentaire sur Romains* 7/9 et Philocalie 22-27.
5. **La controverse chrétienne/gnostique** est sous-modélisée comme débat réel : les arguments existent par fragments, mais les camps Basilide/Valentin/Marcion et les réponses précises de Clément/Irénée/Origène ne sont pas reliés à des fault lines attestées.

### Ce qui est déjà suffisamment épais

Alexandre, le stoïcisme déterministe, Bobzien/Frede/Dihle, Hall 2021, Sytsma et Gibbons sur Origène ont désormais une couverture qui rend une nouvelle ingestion intégrale peu rentable. Leur priorité est la déduplication et l’exploitation correcte, pas l’ajout de nœuds.

## 6. Priorités d’ingestion documentaire

### Méthode de classement

Le classement croise :

- les cinq besoins de lecture du corridor (`golden_corridor_report.md:599-614`) ;
- l’inventaire réel de 758 fichiers de la bibliothèque et le nombre de nœuds-arguments reliés à la publication ; une monographie à ≤2 arguments est traitée comme non lue ;
- les 198 notices Origenality, en privilégiant les records `core` dont un PDF exact est local et non déjà converti en arguments.

Les rendements sont des ordres de grandeur éditoriaux, pas des quotas. Un bon nœud-argument doit être atomique, paginé et porteur d’une opposition ou d’une prémisse utile ; il ne faut pas découper artificiellement un article pour atteindre un nombre.

### TOP 10 — à faire ensuite

| Rang | Auteur, année, titre | Pourquoi pour la thèse | Chemin local | Rendement attendu | Effort |
|---:|---|---|---|---:|---|
| 1 | **Peter Karavites, 1999, *Evil, Freedom, and the Road to Perfection in Clement of Alexandria*** | Ferme directement le trou Clément : mal, autexousion, paideia, perfection et polémique anti-gnostique, avec potentiel de fault lines contre les lectures « soft synergism ». | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Karavites_1999_Evil_Freedom_Perfection_Clement.pdf` | 14–20 | lourd |
| 2 | **Fredrik Nilsen, 2025, « Den frie viljens opphav hos Clemens av Alexandria »** | Proposition récente et falsifiable : Clément serait le premier concept adéquat de libre volonté via prohairesis ; alimente directement la fault line Dihle/Frede/Clément. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Nilsen_2025_Clement_free_will.pdf` | 5–7 | moyen (norvégien) |
| 3 | **Lenka Karfíková, 2025, « Pojem autexúsios u Klementa Alexandrijského »** | Cartographie lexicale précise des occurrences de αὐτεξούσιος, prohairesis, eph’ hēmin et eleutheria chez Clément ; corrige la minceur terminologique du corridor. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Karfikova_2025_Autexusios_Klement_Reflexe68.pdf` | 5–7 | moyen (tchèque) |
| 4 | **Ph. J. van der Eijk, 1988, « Origenes’ Verteidigung des freien Willens in De oratione 6,1-2 »** | PDF local exact d’un record Origenality non lu ; donne la structure argumentative du locus grec déjà présent sur prescience, providence et non-causalité. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/vanderEijk_1988_Origenes_Freier_Wille_De_Oratione_VC42.pdf` | 5–7 | moyen (allemand) |
| 5 | **Matthew R. Crawford, 2021, « The Hostile Devices of the Demented Demons: Tatian on Astrology and Pharmacology »** | Lit réellement la logique de l’*Oratio* 8-9 et sépare démonologie, astrologie et destin ; complète Tatien sans fabriquer un argument pour Or. 10. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Crawford_2021_Tatian_Astrology_Pharmacology_JECS29.pdf` | 6–8 | faible |
| 6 | **Michael Müller, 1926, « Freiheit. Über Autonomie und Gnade von Paulus bis Clemens von Alexandrien »** | Étude longitudinale directement ajustée au corridor Paul → Clément ; utile pour distinguer vocabulaire, autonomie et grâce sans forcer une continuité linéaire. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Mueller_1926_Freiheit_Autonomie_Gnade_ZNW25.pdf` | 9–13 | lourd (allemand, 60 p.) |
| 7 | **Theodor Nikolaou, 1977, « Die Willensfreiheit bei Klemens von Alexandrien »** | Étude ciblée et actuellement absente du KG ; fournit un contrepoint historique aux lectures Havrda, Nilsen et Karfíková. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Nikolaou_1977_Der_Begriff_der_Freiheit_bei_Clemens.pdf` | 5–7 | moyen (OCR allemand) |
| 8 | **Éric Junod, 1989, « Des apologètes à Origène : aux origines d’une forme de théologie critique »** | Porte sur la continuité du corridor en tant que méthode critique/apologétique, sans forcer Tatien ou Irénée vers Clément. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Junod_1989_Des_apologetes_a_Origene_theologie_critique_RTP121.pdf` | 4–6 | faible |
| 9 | **Sidnei Francisco do Nascimento, 2020, « A noção de livre-arbítrio em Orígenes frente à polêmica antignóstica »** | Renforce la fault line Origène/Valentiniens et la motivation anti-natures, station terminale explicitement centrale. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Nascimento_2020_Livre_arbitrio_Origenes_Hypnos45.pdf` | 4–6 | moyen (portugais) |
| 10 | **Thomas P. Scheck, 2008, *Origen and the History of Justification*** | Monographie locale non ingérée sur la réception du *Commentaire sur Romains* ; fournit le cadre savant nécessaire avant de modéliser Rom 7/9. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Scheck_2008_Origen_History_of_Justification.pdf` | 10–15 | lourd |

### NEXT 15 — file d’attente

| Rang | Auteur, année, titre | Pourquoi | Chemin local | Rendement | Effort |
|---:|---|---|---|---:|---|
| 11 | **J. Wytzes, 1955, « Paideia and Pronoia in the Works of Clemens Alexandrinus »** | Paideia/providence chez Clément, continuité contrôlée vers Origène. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Wytzes_1955_Paideia_Pronoia_Clemens_VC9.pdf` | 4–5 | faible |
| 12 | **Judith L. Kovacs, 2001, « Divine Pedagogy and the Gnostic Teacher according to Clement »** | Pédagogie, perfection et gnosticisme : précisément la zone IV.38-39/Clément à ne pas réduire à Hick. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Kovacs_2001_Divine_Pedagogy_Gnostic_Teacher_Clement.pdf` | 5–7 | faible |
| 13 | **Jon D. Ewing, 2005, *The Christianization of Pronoia: Clement’s Conception of Providence*** | Monographie/thèse non lue sur l’articulation providence-liberté chez Clément. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Ewing_2005_Christianization_of_pronoia_Clement_These_GTU.pdf` | 12–18 | lourd |
| 14 | **Hildegard König, 2010, *Clemens von Alexandrien als Seelsorger*** | Éclaire la fonction pastorale des exhortations et sanctions, utile contre une lecture purement métaphysique du corridor. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Koenig_2010_Freiheit_und_Seelsorge_Clemens.pdf` | 8–12 | lourd (allemand) |
| 15 | **Uwe Kühneweg, 1988, « Die griechischen Apologeten und die Ethik »** | Cadre comparatif Justin/Tatien/Athénagore/Théophile, sans présupposer une théorie homogène du libre arbitre. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Kuehneweg_1988_Griechische_Apologeten_und_die_Ethik_VC42.pdf` | 4–6 | moyen |
| 16 | **Elaine Pagels, 1985, « Christian Apologists and the Fall of the Angels »** | Donne le contexte politique et démonologique de la liberté angélique chez Justin/Tatien ; utile à Or. 7. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Pagels_1985_Christian_Apologists_Fall_of_the_Angels_HTR78.pdf` | 5–7 | faible |
| 17 | **Tim Whitmarsh, 2024, « Justin, Tatian and the Forging of a Christian Voice »** | Corrige une lecture doctrinale trop plate en ajoutant la stratégie rhétorique et l’auto-positionnement apologétique. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Whitmarsh_2024_Justin_Tatian_Forging_Christian_Voice_ZAC28.pdf` | 4–5 | faible |
| 18 | **Harald Holz, 1970, « Über den Begriff des Willens und der Freiheit bei Origenes »** | PDF exact d’un record Origenality non lu ; utile pour le statut systématique de volonté/liberté, mais à confronter aux lectures anti-anachroniques récentes. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Holz_1970_Wille_Freiheit_Origenes_NZSTh.pdf` | 5–7 | moyen |
| 19 | **Lisa R. Holliday, 2009 [record Origenality : 2008], « Will Satan Be Saved? »** | Fault line nette entre possibilité technique, volonté du diable et apokatastase ; réconcilier d’abord l’année 2008/2009. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Holliday_2009_Will_Satan_Be_Saved_VC63.pdf` | 5–7 | faible |
| 20 | **Carl Fries, 1930, « Zur Willensfreiheit bei Origenes »** | Lecture courte de la taxonomie mouvement externe/spontané/rationnel de *De principiis* III.1 ; utile comme témoin historiographique, pas comme autorité décisive. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Fries_1930_Zur_Willensfreiheit_bei_Origenes_AGPh39.pdf` | 3–5 | moyen (OCR) |
| 21 | **Hermut Löhr, 2007, « Paulus und der Wille zur Tat »** | Améliore la station Paul en termes d’action et volonté, sans transformer ἐλευθερία en αὐτεξούσιον. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Loehr_2007_Paulus_und_der_Wille_zur_Tat_ZNW98.pdf` | 5–7 | moyen |
| 22 | **A. et T. Van den Beld, 1985, « Romans 7:14-25 and the Problem of Akrasia »** | Prépare la lecture de Romains 7 et de sa réception origénienne par une fault line akrasia/volonté divisée. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/VanDenBeld_1985_Romans_7_14-25_Akrasia.pdf` | 4–6 | faible |
| 23 | **Horace Jeffery Hodges, 1997, « Gnostic Liberation from Astrological Determinism »** | Donne au camp gnostique une position positive et évite de le réduire à la caricature chrétienne des « natures fixes ». | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Hodges_1997_Gnostic_Liberation_Astrological_Determinism_VC51.pdf` | 4–6 | faible |
| 24 | **Marguerite Harl, 1960, « Problèmes pour l’histoire du mot τὸ αὐτεξούσιον »** | Priorité lexicale pour l’émergence du terme ; le PDF local est seulement le compte rendu d’une communication, donc rendement limité mais stratégique. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Harl_1960_Problemes_histoire_du_mot_to_autexousion_REG73_ActesXXVII-XXVIII.pdf` | 2–4 | faible |
| 25 | **Ky Heinze, 2026, « Origen on Demonic Executioners and the Problem of Evil »** | PDF exact d’un record Origenality non lu ; utile à la théodicée et aux médiations démoniques, mais adjacent plutôt que central à la liberté. | `/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/_acquisitions/Heinze_2026_Origen_Demonic_Executioners_CUP.pdf` | 4–6 | faible |

### Prérequis textuels hors classement secondaire

Trois objets doivent alimenter des projets de **texte primaire**, pas être transformés en arguments savants : SC 100 livre IV d’Irénée (`10_Ouvrages_reference/(Sources Chrétiennes 100,1)…`), GCS Stählin II pour les *Stromates* I–VI (`_acquisitions/GCS_Staehlin_Clemens_II_Stromata_I-VI_1906.pdf`) et les deux volumes Scheck FOTC 103/104 pour le *Commentaire sur Romains*. Leur ingestion doit précéder l’écriture des arguments anciens correspondants.

### Ce qui n’est pas rentable maintenant, même si c’est célèbre

- **Frede 2011, Bobzien 2001, Dihle 1982, Amand 1945/1973** : déjà très denses ; corriger l’exploitation de `same_thesis_as` avant d’ajouter une nouvelle extraction.
- **Hall 2021, *Origen and Prophecy*** : déjà 15 arguments ; ne pas réingérer les chapitres Origenality comme témoins indépendants.
- **Sytsma 2018/2020** : déjà 12 arguments et actuellement dupliqué par Origenality ; fusionner, ne pas lire-ingérer à nouveau.
- **Hick, *Evil and the God of Love*** : célèbre, mais déjà modélisé et dangereux comme grille rétroactive pour Irénée IV.38-39.
- **Arendt, Frankfurt, van Inwagen, Sapolsky** : importants pour l’histoire moderne ou analytique, mais ne ferment aucune station du corridor ; ne pas forcer leur pertinence au libre arbitre ancien.
- **Gibbons 2016, *Moral Psychology of Clement*** : essentiel en principe, mais le fichier local `_acquisitions/...PARTIEL_liminaires_intro_biblio_index.pdf` ne contient pas le corps nécessaire ; attendre une copie complète.
- **Koch 1932** et **Völker 1952** dans `_acquisitions` : fichiers limités au front matter/TOC/bibliographie, impropres à une ingestion argumentative.
- **Cocchini, *Il Paolo di Origene*** : le PDF local ne fait que deux pages d’images ; acquérir le texte complet avant toute ingestion.

## 7. Top 10 des améliorations prioritaires

| Priorité | Type | Amélioration | Résultat attendu |
|---:|---|---|---|
| 1 | **Quick win** | Passer `check_corpus_invariants` en strict et retirer les 9 citations Simplicius pendantes. | CI réellement verte sur les références. |
| 2 | **Projet lourd** | Réconcilier les 709 passages Plotin et construire le gate KG↔corpus. | Même locus en snapshot et en DB. |
| 3 | **Décision Romain** | Activer ou déclarer expérimental Scholar-RAG/referee ; rendre l’état visible au healthcheck. | Les nouveaux assets cessent d’être du code mort implicite. |
| 4 | **Projet lourd** | Politique centrale d’honnêteté `citable/discoverable_only/blocked`. | Aucune dette OCR/texte/locus ne peut être citée. |
| 5 | **Quick win** | Mettre en quarantaine les 29 records Fédou, fusionner Sytsma 2018/2020. | Origenality redevient une bibliographie exploitable. |
| 6 | **Projet lourd** | Étendre R16 à toutes les relations rendues par la carte et vérifier `[edge:*]`. | La prose dialectique ne repose plus sur 245 relations non attestées. |
| 7 | **Projet lourd** | Remplacer le déploiement destructif par staging + swap transactionnel. | Pas de fenêtre vide ni de DB partielle. |
| 8 | **Quick win** | Dédupliquer 129 citations, régénérer les trois stats, activer `gen_stats --check`. | Manifests et comptages fiables. |
| 9 | **Projet lourd** | Exploiter les composantes `same_thesis_as` dans triage, prompt et comptage des witnesses. | Pas de faux consensus par double extraction. |
| 10 | **Décision éditoriale** | Lancer la vague Clément/Tatien du TOP 10, avec SC 100/GCS en prérequis primaires. | Le corridor gagne de la substance ancienne plutôt que du câblage supplémentaire. |

## Conclusion

Le cycle v5.2.0 a bien corrigé une grande quantité de défauts réels. Ce qui reste est moins visible et plus dangereux : **les réparations ne traversent pas toutes les couches, les gates ne couvrent pas les mêmes classes que les consommateurs, et la configuration par défaut n’active pas les actifs savants nouvellement créés**. La prochaine phase doit donc privilégier les contrats de parité et les politiques de citation, puis investir dans Clément, Tatien, Irénée IV.38-39 et Origène hors III.1. Ajouter encore des arêtes ou des notices avant ces deux étapes augmenterait surtout le volume de dette interprétative.
