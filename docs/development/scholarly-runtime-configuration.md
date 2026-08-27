# Configuration runtime de la synthèse savante

Cette page inventorie les variables d’environnement effectivement lues par le
chemin Scholar‑RAG. Les trois interrupteurs sont volontairement explicites dans
les fichiers `.env.example`; leur état effectif, ainsi que le modèle de
synthèse résolu, est observable dans `GET /api/graphrag/health` sous
`scholarly_configuration`.

## Interrupteurs

| Variable | Défaut code | Effet |
|---|---:|---|
| `ELEUTHERIA_SCHOLAR_RAG` | `false` | Active le plan débat-first, `find_debates`, `build_controversy_frame`, le context pack dialectique et la synthèse Scholar‑RAG. À `false`, le chemin historique reste propriétaire du rendu. |
| `ELEUTHERIA_REFEREE` | `false` | Active le referee post-synthèse et, en cas d’échec, au plus une révision locale. Sans Scholar‑RAG assemblé, il n’a pas de carte à arbitrer. |
| `ELEUTHERIA_RELEVANCE_TRIAGE` | `false` | Active le classement de pertinence par modèle utilitaire avant que le fitter réduise positions et passages. Un échec conserve l’ordre déterministe existant. |

Les valeurs vraies reconnues sont `1`, `true`, `yes` et `on` (insensibles à la
casse). Toute autre valeur vaut `false`.

## Amorçage déterministe du graphe

| Variable | Défaut code | Effet |
|---|---:|---|
| `ELEUTHERIA_GRAPH_SEED` | `true` | Avant le premier tour du ReAct, lance la découverte de graines de la stratégie de récupération puis une traversée pondérée (`WeightedTraversal`, 30 nœuds, seuil 0,05) depuis ces graines ; nœuds et passages liés entrent dans l’évidence par les mêmes chemins que les outils, sans doublon. Seules `0`, `false`, `no` et `off` désactivent. Le résultat est consigné dans `metadata.graph_seed` (`seed_nodes`, `expanded_nodes`, `edges_followed`, `ms`, `truncated`, `passages`, `status`). |
| `ELEUTHERIA_GRAPH_SEED_BUDGET_MS` | `2000` | Budget mural de l’étape (découverte + traversée + lectures de passages), borné à 50–30000 ms. Dépassé, l’étape rend ce qu’elle a et marque `truncated` ; toute erreur va dans `metadata.retrieval_errors` sans interrompre la requête. |

## Modèle et budgets Scholar‑RAG

| Variable | Défaut code | Effet |
|---|---:|---|
| `SCHOLAR_SYNTHESIS_MODEL` | `gpt-5.6-sol` | Premier modèle de la chaîne de synthèse dialectique; accepte un identifiant nu ou `provider:model`. Les fallbacks restent Claude puis Gemini résolu par la configuration fournisseur. |
| `SCHOLAR_SYNTHESIS_REASONING_EFFORT` | non défini | Épingle `none`, `low`, `medium` ou `high` pour le rung Codex. Non défini hérite de la politique du fournisseur (`CODEX_REASONING_EFFORT`). |
| `ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS` | quick `12`, standard `24`, deep `45` | Remplace le plafond de tool calls de tous les tiers lorsqu’il contient un entier strictement positif. |
| `ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT` | `360` s | Timeout par appel de synthèse, borné à 120–900 s. |
| `ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS` | quick `9000`, standard `12000`, deep `14000` | Remplace le plafond de rendu du tier, borné à 8000–24000 tokens. |
| `ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET` | `18` | Nombre maximal de passages contestés demandé par frame, borné à 6–24. |

## Triage de pertinence

| Variable | Défaut code | Effet |
|---|---:|---|
| `ELEUTHERIA_TRIAGE_MODEL` | non défini | Modèle utilitaire épinglé. Non défini utilise Gemini light quand son proxy est actif, sinon le routage utility standard. |
| `ELEUTHERIA_TRIAGE_TIMEOUT` | `25` s | Budget mural de l’étape, borné à 0,1–120 s. |
| `ELEUTHERIA_TRIAGE_MAX_ITEMS` | `4800` | Plafond d’items scorés, borné à 150–6000; la queue non scorée garde son ordre déterministe. |

## Referee

| Variable | Défaut code | Effet |
|---|---:|---|
| `ELEUTHERIA_REFEREE_TIMEOUT` | `90` s | Timeout du verdict, borné à 30–300 s. |
| `ELEUTHERIA_REVISION_TIMEOUT` | `240` s | Timeout de l’unique révision éventuelle, borné à 60–600 s. |
| `ELEUTHERIA_REFEREE_MAP_TOKENS` | `30000` | Budget de carte fourni au referee, borné à 2000–200000 tokens. |

## Fenêtre du context pack

| Variable | Défaut code | Effet |
|---|---:|---|
| `ELEUTHERIA_SYNTH_CONTEXT_TOKENS` | `1000000` | Plafond global du contexte de synthèse; une valeur inférieure à 8192 est ignorée. |
| `ELEUTHERIA_SYNTH_CONTEXT_TOKENS_QUICK` | `120000` | Cap du tier quick, sous le plafond global. |
| `ELEUTHERIA_SYNTH_CONTEXT_TOKENS_STANDARD` | `250000` | Cap du tier standard, sous le plafond global. Le tier deep conserve le plafond global. |

## Observation

Exemple de payload partiel :

```json
{
  "status": "healthy",
  "scholarly_configuration": {
    "scholar_rag": false,
    "referee": false,
    "relevance_triage": false,
    "graph_seed": true,
    "synthesis_model": "gpt-5.6-sol"
  }
}
```

Une modification du fichier d’environnement nécessite une recréation du
conteneur pour être effective; un simple restart ne recharge pas les valeurs.
