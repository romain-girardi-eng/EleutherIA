# Jev (TypeSafe AI) : ce que ce modèle apporte à EleutherIA et aux projets d'humanités numériques

Note de recherche, 18 septembre 2026. Tout chiffre ci-dessous a été mesuré par moi sur mes données (base de production d'EleutherIA, jeux d'évaluation du dépôt), sauf mention contraire. Dossier de travail : `~/Projects/Veille/2026-09-17-jev-gold/`.

## 1. Ce que c'est, en trois phrases

Jev est un modèle publié le 15 septembre 2026 par TypeSafe AI (Diogo Almeida, co-inventeur du RLHF chez OpenAI). Il lit un texte et répond à des questions fermées, toutes en parallèle, en un seul passage : un choix parmi des options, une note sur une échelle, un vrai ou faux. Il ne génère aucune phrase ; chaque réponse vient avec une probabilité, et un score de confiance calibré (plus la confiance est haute, plus la réponse est juste, en moyenne).

Il coûte 0,04 dollar par million de tokens lus, la réponse est gratuite, et il répond en 300 millisecondes. Il lit le grec polytonique, le latin et le français sans traduction préalable : vérifié.

## 2. La plus-value, très clairement

Sur trois jours de tests, une seule plus-value tient, et elle est nette.

**Trier des passages anciens par pertinence, avec une confiance qu'on peut seuiller.**

Concrètement, dans EleutherIA : quand un chercheur pose une question, le premier étage remonte 150 passages candidats ; il faut en garder 12. Sur les 20 requêtes du jeu d'évaluation qui ont des passages attendus :

| Qui choisit les 12 passages | Part des passages attendus conservés | Requêtes où le bon passage arrive premier |
|---|---|---|
| L'ordre lexical actuel (RRF) | 55 % | 2 sur 20 |
| Le cross-encoder déjà dans le dépôt (bge-reranker-v2-m3) | 30 % | 3 sur 20 |
| Jev | 83 % | 9 sur 20 |

Le cross-encoder générique fait pire que l'ordre lexical sur du grec savant ; Jev fait beaucoup mieux, pour 0,16 dollar les 3 000 paires. C'est la seule des trois options qui améliore le tri, et l'écart est mesuré sur la base de production.

Ce qui rend ce résultat utilisable, c'est la calibration. Sur 360 passages grecs et latins, quand Jev annonce une confiance supérieure à 0,9, il a raison 93 fois sur 100 ; sous 0,3, il a raison 1 fois sur 10 ; l'écart moyen entre confiance annoncée et justesse observée est de 7 points. On peut donc écrire une règle simple : au-dessus d'un seuil, la machine agit seule ; en dessous, un humain relit. Cette règle est exactement le mécanisme dont un projet d'humanités numériques a besoin pour annoter un corpus entier sans prétendre que la machine a toujours raison.

Deux corollaires :

- **Le coût de lecture d'un corpus entier disparaît.** Passer les 15 212 passages originaux d'EleutherIA sur 62 concepts (943 144 jugements) a pris 7 minutes et 3,88 dollars. Un projet de la taille de la carte de la réception paulinienne peut refaire une passe complète à chaque révision de son ontologie pour le prix d'un café.
- **La machine révèle les défauts du graphe.** Cette passe a montré que 362 des 1 008 arêtes « ce passage discute ce concept » sont contredites par le texte, parce qu'elles avaient été posées au niveau de l'œuvre (189 des 202 arêtes « libre choix » sont simplement tous les chapitres du De libero arbitrio d'Augustin). Un audit qu'aucun humain n'aurait fait à la main.

## 3. Les limites du périmètre

- **Le premier étage de la recherche reste lexical.** Le vrai goulot d'EleutherIA était en amont : l'étape de semis de la prod ne remontait que 5 % des passages attendus, parce que les questions sont en anglais ou en français et les passages en grec ou en latin. La correction est lexicale et sans IA : une jambe métadonnées (auteur, œuvre, référence) fusionnée avec la recherche plein texte fait passer le rappel de 17 % à 58 %. Jev ne peut trier que ce qui lui arrive.
- **Aucune position doctrinale attribuée par la machine.** Faire dire à une machine qu'un passage est « libertarien » ou « compatibiliste » serait académiquement indéfendable : 28 des 30 sujets de consensus savant d'EleutherIA sont marqués contestés, et ma thèse porte précisément sur l'émergence d'un vocabulaire que ces étiquettes projettent en arrière. Jev inventorie des faits observables (le mot αὐτεξούσιον est-il présent, le passage argumente-t-il contre l'εἱμαρμένη, cite-t-il Rm 9) ; l'interprétation reste au chercheur, appuyée sur le faisceau d'indices.
- **Aucune génération.** Aucune traduction, aucune paraphrase, aucun résumé. Pour une plateforme qui s'interdit de générer du grec ou du latin, c'est une qualité.
- **Une infrastructure encore jeune.** Entreprise de trois jours, limites de débit « dynamiques », prix que TypeSafe reconnaît ne pas pouvoir prouver non subventionné, pas d'hébergement européen, pas de papier, pas de courbe de calibration publiée (la mienne est la seule que je connaisse). D'où la règle : repli automatique sur l'ordre lexical, version du modèle journalisée à chaque appel, harnais d'évaluation comme porte de non-régression.

## 4. Pour d'autres projets DH

Le même schéma (questions fermées, confiance seuillée, humain sur la tranche incertaine) s'applique dès qu'un projet doit lire beaucoup de texte pour trouver peu de choses :

- **Carte de la réception paulinienne** : typer comment un auteur ancien lit Paul (cite, paraphrase, réfute, allégorise) sur un corpus océanique ; aligner les notices doublonnées ; vérifier qu'une citation soutient bien la lecture qu'on lui attribue. Le jeu étalon de 400 notices en double codage sert à publier l'accord humain par tranche de confiance.
- **Sematika** (OCR du grec) : « cette ligne est-elle du grec polytonique plausible », choix entre variantes de lecture, avant la revue générative.
- **Lemmatika** : désambiguïsation lemme et morphologie parmi les candidats de l'analyseur, avec probabilité ; le comptage et l'alignement restent en code.
- **Revues de littérature** : critères d'inclusion et d'exclusion sur des milliers de résumés, en une passe.
- **Graphes de connaissances** en général : Jev est la fonction de jugement qui type les arêtes, dédoublonne les nœuds, valide ce qu'un LLM a extrait, et produit un graphe où chaque lien porte sa probabilité.

Limites à connaître avant de s'y engager : lecture très littérale (il répond à la question écrite, pas à l'intention), nul en arithmétique, en comptage et en comparaison de dates, sensible aux textes qui plaident pour leur propre classement, contexte de 64 000 tokens, pas d'image. Les questions larges à plusieurs auteurs sont son point faible ; il faut les décomposer par facette.

## 5. Fiche technique

| | |
|---|---|
| Éditeur | TypeSafe AI, San Francisco, 40 M$ levés (DCVC) |
| Modèle | `jev-1.13.0`, alias `jev-latest` ; classe « System One Model » |
| Entraînement | RLCD, Reinforcement Learning for Calibrated Decisions ; architecture non publiée (encodeur à têtes scalaires selon les échanges du fondateur) |
| Primitives | `Choice` (une option parmi 255 au plus, probabilités et confiance), `Score` (niveaux ordonnés décrits, probabilités et confiance), `Noul` ou `boolean` (probabilité que ce soit vrai) |
| Entrée | texte seul : chaîne, objet JSON ou liste ; 64 000 tokens état plus questions, 32 000 pour l'état plus la plus longue question |
| Prix | 0,042 $ par million de tokens en entrée, sortie gratuite |
| Latence | 300 ms en médiane depuis l'Europe via le gateway Vercel (région cdg1) ; 7 minutes pour 15 212 passages avec 16 appels en parallèle |
| Accès direct | `POST https://api.typesafe.ai/v1/systemone`, SDK Python `typesafe-sdk`, JS `@typesafe-ai/sdk`, sur liste d'attente (inscription faite le 17/09 avec l'adresse UCA, mail envoyé à hello@typesafe.ai) |
| Accès immédiat | Vercel AI Gateway, modèle `typesafe-ai/jev`, `experimental_evaluate` de `ai@7.0.105`, ou HTTP brut : `POST https://ai-gateway.vercel.sh/v4/ai/evaluation-model` avec les en-têtes `Authorization: Bearer <clé>`, `ai-model-id: typesafe-ai/jev`, `ai-evaluation-model-specification-version: 4`, `ai-gateway-auth-method: api-key`, `ai-gateway-protocol-version: 0.0.1` ; corps `{state, questions}` |
| Clé | `AI_GATEWAY_API_KEY` dans `~/.config/vercel-ai-gateway/env` (équipe Vercel `romain-girardi-eng`, crédits payés) |
| Données | pas d'entraînement sur les données clients (contrat) ; zéro rétention par requête réservée au plan Vercel Pro ; serveurs américains |
| Contrat de sortie | la réponse ne peut pas sortir du schéma demandé (garantie de forme, pas de vérité) ; le champ `model` de la réponse donne la version qui a répondu |

## 6. Ce que j'ai mesuré, par ordre chronologique

| Date | Test | Résultat |
|---|---|---|
| 17/09 | 4 passages (Justin, Rm 9, Origène, Bobzien), 5 questions | 20 jugements sur 20 justes en grec, latin, français |
| 17/09 | 360 passages, reconnaissance d'école à 9 options | 65 % top-1, 86 % top-2 ; 93 % à confiance ≥ 0,9 (35 % du corpus) ; ECE 0,073 |
| 17/09 | 15 212 passages × 62 concepts | 3,88 $, 7 min ; 362 arêtes existantes contredites, 1 617 nouvelles sûres, 821 lignes à adjuger |
| 18/09 | Reranking, pool BM25 maison, 20 requêtes | MRR 0,71 contre 0,15 pour bge |
| 18/09 | Premier étage de la prod | semis 5 % de rappel, FTS 17 %, jambe métadonnées fusionnée 58 % (H1 vérifiée) |
| 18/09 | Tri des 12 ancres sur le pool de fusion | RRF 55 %, bge 30 %, Jev 83 % (H2 vérifiée, H3 réfutée) |

Reste à tester : H4, la qualité de bout en bout des réponses dans le harnais d'évaluation, avant toute bascule de la bêta.

## 7. Règles que je me donne

1. Hypothèse écrite, test réel, contrôle sans la technologie, et on n'avance que sur du vérifié.
2. Jamais de position doctrinale attribuée par la machine.
3. Toute décision automatique est seuillée sur la confiance, et la tranche incertaine passe par un humain ; l'accord humain par tranche est publié avec les chiffres.
4. Version du modèle journalisée, repli sans IA toujours disponible, harnais d'évaluation comme porte.
5. Le code du graphe n'est modifié qu'après adjudication humaine des arêtes proposées.

## Sources

- Annonce : https://typesafe.ai/blog/introducing-system-one-models-and-jev
- Documentation : https://docs.typesafe.ai/ (primitives, confiance, limites « jaggedness » de jev-1.13, cookbooks reranking, alignement d'entités, vérification de citations)
- Évaluations de l'éditeur : https://evals.typesafe.ai/
- Vercel AI Gateway : https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway
- Discussion Hacker News (483 commentaires, réponses du fondateur) : https://news.ycombinator.com/item?id=49717558
- Rapport de veille complet et scripts : `~/Projects/Veille/2026-09-17-typesafe-jev-system-one.md`
