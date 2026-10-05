# CorpusMap ("Follow the Entities", arXiv:2609.37226) appliqué à EleutherIA — A/B du 2026-10-05

## TL;DR

| | A : outils actuels | B : + CorpusMap | Δ | Significativité |
|---|---|---|---|---|
| Juge aveugle, note globale /10 (30 requêtes) | 7,33 | 7,37 | +0,03 (IC95 ≈ ±0,61) | non significatif (sign test p = 0,84) |
| Préférence du juge | 15 | 13 | 2 égalités | p = 0,85 |
| Tokens d'entrée cumulés sur la trajectoire* | 360 005 | 269 347 | **−25,2 %** | B moins cher sur 21/30 requêtes, p = 0,043 |
| Tokens de sortie d'outils | 141 476 | 108 934 | **−23,0 %** | 22/30, p = 0,008 |
| Appels d'outils / tours LLM | 211 / 111 | 184 / 86 | −13 % / −23 % | |
| IDs cités inexistants | 0 | 1 (sur 245) | | |
| Requêtes de thèse multi-hop (r001–r016), note | 7,06 | 7,38 | +0,31 (7 victoires B / 5 A) | |
| Requêtes de thèse multi-hop, tokens trajectoire | 236 620 | 159 948 | **−32,4 %** | |
| Requêtes mono-passage (release), tokens trajectoire | 15 056 | 29 195 | **+94 %** | candidats inutiles ici |
| **Variante retenue (candidats seulement hors `specific_entity`)**, estimation | | | **−29 % tokens, note 7,40** | estimation, pas un run séparé |

\* Somme sur chaque tour de (brief + sorties d'outils déjà reçues), hors prompt système fixe du runtime. C'est la métrique « input tokens accumulated over the full agent trajectory » du papier. Les `subagent_tokens` bruts du runtime ne baissent que de 2 %, parce qu'ils sont dominés par un prompt système d'environ 45 k tokens propre au harnais de test, qui n'existe pas en production.

**Verdict.**
- Le gain de **coût** du papier se reproduit, avec une amplitude plus faible : −25 à −32 % ici, contre −34 à −57 % dans le papier.
- Le gain de **qualité** (+6,4 à +11,7 points dans le papier) **ne se reproduit pas** : on observe une parité, avec une légère tendance positive sur les questions multi-hop.
- La raison est structurelle. Le baseline du papier est un agent `grep`/`find` sur des fichiers plats. Le nôtre navigue déjà dans un KG curé dont les personnes, œuvres et concepts *sont* les entités résolues de CorpusMap. Il possédait donc déjà la moitié de l'idée.
- Ce que CorpusMap ajoute chez nous : une **consolidation**. Une page = tous les faits sourcés sur une entité, au lieu de `get_neighbors` plafonné à 30 arêtes puis N × `get_node_detail`. S'y ajoutent des **candidats pré-sélectionnés**. Le résultat est le même niveau de qualité pour un quart de tokens en moins.

## 1. Ce que dit le papier (lu en entier depuis le PDF)

- **Méthode.**
  - Graphe biparti G = (E ∪ D, L) entre entités récurrentes et documents. Seules les entités liées à au moins 2 documents sont conservées.
  - Chaque entité a une **Entity Page** : aperçu, alias, faits clés *chacun tagué par son document source*, liens vers tous les documents.
  - Construction hors-ligne en 4 étapes : catalogue de types induit par LLM, extraction, résolution contre un registre, rendu.
- **Navigation.** L'agent garde ses outils shell sur le corpus brut. Il reçoit en plus des **candidats** : top pages par BM25, documents liés reclassés par BM25, *titres et chemins seulement*.
- **Résultats.**
  - 7 LLM et 3 benchmarks (EnterpriseRAG-Bench, WixQA, HERB).
  - Qualité : +6,4 à +11,7 pts. Tokens d'entrée : −34 à −57 % sur les modèles GPT.
  - Bat GraphRAG et HippoRAG en mode retrieve-then-generate.
- **Ablations qui comptent pour nous.**
  - **Table 8** : sans candidats, la qualité monte un peu mais les tokens sont multipliés par 2,4 ; les candidats « documents liés » donnent le meilleur ratio. Nous avons repris ce réglage par défaut.
  - **§B.4** : les **arêtes entité–entité (type KG) n'apportent rien** (rappel de −2,6 à +0,2 pt) et coûtent jusqu'à +28 % de tokens. Les pages n'en contiennent donc pas.
  - **Fig. 4** : une construction **sans LLM** (GLiNER/GLinker et rendu déterministe) est aussi efficace qu'une construction LLM. Chez nous, le KG curé tient lieu d'extraction et de résolution, donc le coût de construction est de **0 $ et 4 s**.

## 2. Ce qui a été implémenté

- `graphrag/src/eleutheria_graphrag/corpusmap/`
  - `builder.py` : rendu des Entity Pages depuis le KG (snapshot JSONL ou `kg_data` en mémoire), plus la couche passages du corpus.
    - Les passages sont repliés sur les `passage_id` du corpus via `citations.jsonl`.
    - La politique de citabilité est respectée : `related_passage_non_exact` est bloqué.
    - Taille : 638 pages et 25 676 documents.
  - `candidates.py` : sélection des candidats du §B.3 (BM25 sur les pages, regroupement des documents liés, reclassement BM25, sortie en ids et titres seulement).
  - `bm25.py` : BM25 sans dépendance, avec repli des diacritiques pour le grec polytonique et le latin.
  - `runtime.py` : flag `ELEUTHERIA_CORPUSMAP` (**OFF par défaut**), cache par KG chargé, et gating par `query_type`. Pas de candidats pour `specific_entity`.
- `agents/tools/entity_pages.py` : outils `search_entity_pages` et `read_entity_page(entity_id, focus)`, enregistrés uniquement sous le flag. Les faits d'une page sont classés par BM25 contre la question.
- `agents/react_loop.py` : le message d'ouverture du `NativeAgentLoop` contient les candidats, à côté des seeds existants.
- Les Entity Pages ne produisent **aucune preuve citable** : l'`EvidenceCollector` les ignore. L'agent doit ouvrir le document pour qu'il entre dans le dossier de preuves, ce qui préserve la publication fail-closed.
- Tests : `graphrag/tests/unit/test_corpusmap.py` (10 tests). Les 35 tests existants des loops agentiques passent toujours.

## 3. Protocole

### 3.1 A/B déterministe de récupération (sans LLM, 56 requêtes gold)

Script : `scripts/corpusmap_ab/retrieval_ab.py`. Il compare ce que chaque bras met devant l'agent avant son premier appel.

| Bras | Rappel entités | Rappel œuvres | Rappel passages | Tokens de handoff |
|---|---|---|---|---|
| A lexical (runner `snapshot-lexical`) | 0,422 | 0,741 | 0,306 | 1 196 |
| A PPR bidirectionnel | 0,753 | 0,741 | 0,274 | 894 |
| B CorpusMap 5 pages + 10 docs | 0,738 | 0,616 | 0,135 | **477** |
| B CorpusMap 10 pages + 20 docs | **0,822** | 0,699 | 0,177 | 928 |
| C PPR + CorpusMap | **0,862** | **0,796** | 0,295 | 1 372 |

- À budget égal (~900 tokens), CorpusMap retrouve **+7 pts d'entités** de plus que le PPR actuel.
- Pour un rappel d'entités équivalent, CorpusMap coûte **2× moins de tokens**.
- Il est en revanche plus faible sur les *passages* nommés par leur locus (« De fato 41 ») : c'est le rôle du BM25 sur les passages, que l'agent conserve.

### 3.2 A/B agentique (60 runs + 30 jugements)

- **Requêtes.** 30 requêtes multi-documents :
  - les 16 requêtes de thèse r001–r016, dont **r016**, la question de référence ;
  - 4 `comparison` et 6 `school-debate` ;
  - les 4 requêtes release en français, dont une non-répondable.
- **Outils.** Serveur d'outils hors-ligne (`scripts/corpusmap_ab/kgtool.py`) qui reproduit `search_nodes`, `get_node_detail`, `get_neighbors` (limite 30), `read_passages`, `search_passages` et `read_passage` sur le snapshot. Le bras B y ajoute `search_entity_pages` et `read_entity_page`, et son brief contient les candidats. La séparation des bras est vérifiée côté serveur.
- **Agent.** Sonnet, même brief et même budget de 15 appels pour les deux bras. Chaque appel est journalisé avec la taille de sa sortie (`calls.jsonl`).
- **Juge.** Opus en aveugle, ordre X/Y tiré au sort (seed 20261005, table dans `judge_mapping.json`). Il peut **vérifier jusqu'à 8 IDs cités** dans le corpus. Il note la correction, la complétude, l'ancrage et une note globale.
- **Statistiques.** Tests de signe appariés.

## 4. Lecture qualitative

- **Où B gagne nettement.**
  - r011 Boèce : 9 contre 5.
  - r005 Méthode : 8 contre 5.
  - q016 Justin : 8 contre 4. A ne trouve jamais Justin ; la page « Justin » et ses faits sourcés le lui donnent immédiatement.
  - Ce sont les cas typiques du papier : l'évidence est dispersée et la requête seule ne l'atteint pas.
- **Où B perd.**
  - r013 et q023 : B s'arrête plus tôt (−0,8 tour en moyenne) et couvre moins.
  - Un agent B a **cité deux documents vus seulement sur une Entity Page, sans les ouvrir**. Il l'a signalé lui-même.
  - Un ID de passage inexistant a été cité (q025-B).
  - Ces deux risques sont couverts en production : les pages ne sont pas des preuves, et le vérificateur de citations v2 bloque la publication.
- **Rappel strict des IDs gold.** Neutre pour les entités (0,26 contre 0,27) et les passages (0,39 contre 0,38). Il baisse pour les **œuvres** (0,39 contre 0,57) : les agents B citent l'argument ou le passage plutôt que le nœud « œuvre ». C'est une différence de style de citation, pas de couverture. Le juge, qui vérifie le contenu, ne pénalise pas B.

## 5. Recommandation

1. **Activer `ELEUTHERIA_CORPUSMAP=1` en pré-production** et lancer `tests/eval/run_eval.py --runner live-http` sur la release figée.
   - Le gain attendu est une baisse des tokens de la phase de récupération, sans perte de qualité mesurée. La phase de synthèse, la vérification et le referee ne sont pas touchés, donc l'économie sur le coût total d'une requête sera **inférieure** à 25 %.
   - À mesurer avec le `TraceWriter` existant.
2. **Ne pas** rendre d'arêtes du KG dans les pages (§B.4, confirmé) et **ne pas** injecter de candidats sur les questions `specific_entity`. Ces deux choix sont déjà codés.
3. Pistes restantes, par ordre de rendement attendu :
   - Ajouter les **N premiers passages BM25** aux candidats. La variante C ci-dessus gagne sur toutes les colonnes.
   - Relancer l'A/B avec le **modèle de production** (gpt-5.6-sol ou kimi-k2.7) via `--runner live-http`. L'A/B présent utilise Sonnet par contrainte d'environnement : aucune clé de fournisseur n'était disponible dans le conteneur.
   - Faire **3 seeds** par bras pour réduire la variance. L'IC actuel est de ±0,6 point sur 10.

## 6. Limites (honnêtement)

- n = 30 requêtes et 1 run par bras. La qualité est à égalité, avec un IC95 de ±0,6 sur 10 : on exclut une régression de plus de 0,6 point, mais un petit gain n'est pas démontré.
- Le juge est un LLM : Opus, aveugle, avec vérification de 1 à 8 IDs par paire. Ce n'est pas une évaluation humaine.
- Les outils A sont une réimplémentation hors-ligne fidèle aux schémas MCP, pas le service Postgres de production : pas de FTS lemmatique ni d'arbre de sections. Les deux bras partagent exactement la même base.
- Les tokens de trajectoire sont estimés à chars/4, avec regroupement des appels par tour (écart d'au moins 1 s).
- 3 lignes de verdict du juge étaient mal formées. Elles ont été réparées de façon déterministe dans `score.py` (accolade manquante ou en trop) ; le fichier brut est conservé.

## Reproduire

```bash
uv venv --python 3.14 .venv && uv pip install --python .venv/bin/python -e . -e ./database -e "./knowledge graph" -e "./graphrag[dev]"
.venv/bin/python scripts/corpusmap_ab/retrieval_ab.py                 # A/B déterministe
.venv/bin/python scripts/corpusmap_ab/kgtool.py serve --log data/eval/corpusmap_ab/calls.jsonl &
.venv/bin/python scripts/corpusmap_ab/make_prompts.py <dir>           # briefs agents A/B
.venv/bin/python scripts/corpusmap_ab/make_judge_prompts.py <dir>     # briefs juge aveugle
.venv/bin/python scripts/corpusmap_ab/score.py                        # agentic_summary.json
```

Artefacts : `briefs/`, `answers/` (60), `calls.jsonl`, `agent_tokens.jsonl`, `judgments_raw.jsonl`, `judgments.jsonl` (dé-aveuglés), `agentic_rows.jsonl`, `agentic_summary.json`, `retrieval_ab_*.json*`.
