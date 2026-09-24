# Campagne Jev — traductions & descriptions (2026‑09‑24)

Campagne « c2_translations_descriptions », menée pendant la fenêtre gratuite Jev (Vercel AI Gateway, `typesafe-ai/jev`). Deux volets, exécutés en parallèle, concurrence 12, coût facturé : **0 $** (fenêtre gratuite confirmée sur chaque appel — `providerMetadata.gateway.cost = "0"`).

Rappel du cadre : ce sont des jugements Jev, donc des **indices probabilistes pour adjudication humaine**, jamais des écritures KG. Rien n'a été modifié dans `data/kg/*` ni `data/corpus/*`.

## Couverture et coût

| Volet | Candidats | Réponses | Erreurs | Tokens en entrée | Coût |
|---|---|---|---|---|---|
| A — alignement traduction ↔ original | 2 607 / 2 607 | 100 % | 0 (21 `429` en première passe, tous rejoués avec succès) | 4 362 278 | 0 $ |
| B — description ↔ identité | 3 205 / 3 205 | 100 % | 0 (19 `429` rejoués) | 2 151 797 | 0 $ |

Couverture totale : **5 812 nœuds/arêtes jugés, 22 questions × candidat en moyenne, 6,5 M tokens d'entrée, 0 $**.

## Où vit le texte (documentation de la construction)

Contrairement à l'hypothèse du brief, il n'a pas été nécessaire d'aller chercher le texte dans `data/corpus/passages.jsonl` : **chaque nœud `passage` de `data/kg/nodes.jsonl` porte son texte intégral dans son propre champ `description`** (vérifié : `related_corpus_passage_id` pointe vers le corpus mais n'est pas nécessaire pour cette tâche). Les 2 607 arêtes `translation_of` (`source` = traduction anglaise, `target` = original) résolvent toutes vers deux nœuds réels, `source`/`source_id` et `target`/`target_id` toujours égaux. Chaque texte a été tronqué à 8 000 caractères par côté (bien en dessous des 64k tokens ; médiane originale 681 car., 964 car. côté traduction — seule une poignée de textes très longs, max 41 689 car., a été tronquée).

Pour le volet B, l'état envoyé à Jev est `{name: label, type, description}` (description tronquée à 6 000 caractères, comme demandé).

## Schéma Jev vérifié par sonde

Une question `choice` attend un champ `criteria` (dictionnaire clé→libellé), pas `options` (confirmé par une requête de sonde qui échoue avec `options` puis réussit avec `criteria`) — documenté dans `run_jev.py` et repris de `jev_reranker.py`/`run_gold.mjs`.

## Partie A — alignement traduction ↔ original (2 607 arêtes `translation_of`)

Distribution de `same_content` (la traduction rend‑elle le même passage ?) :

| Tranche de confiance | N | % |
|---|---|---|
| ≥ 0,9 | 1 079 | 41 % |
| 0,7–0,9 | 582 | 22 % |
| 0,3–0,7 | 485 | 19 % |
| ≤ 0,3 | 461 | 18 % |

**18 % des paires interrogent une désynchronisation probable** — bien plus élevé que ce à quoi on s'attendait pour un corpus déjà audité.

Vérification déterministe (sans Jev) : **0** paire au texte identique ou quasi‑identique octet à octet (seuil ratio ≥ 0,97), **0** traduction ou original vide. Donc les 35 cas « texte identique » remontés par Jev (`p ≥ 0,7`, voir plus bas) ne sont **pas** des doublons bruts — c'est un signal plus fin.

### Files
- `queue_a_misaligned.csv` — 470 lignes, `same_content ≤ 0,3`, triées par p croissant (les plus sûres en tête).
- `queue_a_partial_coverage.csv` — 777 lignes, `coverage = partial` avec `p ≥ 0,7`.
- `queue_a_identical_text.csv` — 35 lignes, `identical_text ≥ 0,7`.
- `queue_a_language_mismatch.csv` — 0 ligne (aucune traduction jugée française avec confiance ≥ 0,7 alors que tout le corpus de traductions est étiqueté `eng` en métadonnée — bon signe, pas de mislabeling détecté par ce test).
- `queue_a_deterministic_flags.csv` — 0 ligne (voir ci‑dessus).

### Exemples vérifiés à la main

1. **Vraie désynchronisation (confirmée)** — `sc123_melito_peri_pascha_chap29` / `..._chap29_en` (`p = 0,01`, `coverage = not_translation`). L'original grec décrit les Égyptiens en deuil de leurs premiers‑nés (« Ἦν δὲ θεάσασθαι φοβερὸν θέαμα... ») ; la « traduction » anglaise donne un tout autre passage de Méliton (« For instead of the lamb there was a Son... »). Même schéma sur 4 autres chapitres consécutifs de Méliton (`chap34`, `chap48`, `chap49`, `chap52`) — un bloc entier de traductions décalées d'un cran, probablement une erreur d'appariement lors de l'ingestion de SC 123.
2. **Faux positif de couverture (verset latin)** — `passage_boethius_cons_47` (`Cons. 47 : Nature's Laws`), `coverage = partial` (`p = 1,0`) mais `same_content = 0,2`. Lecture : la traduction anglaise couvre en fait fidèlement tout le vers latin (« Phoebus sinks into the western waves... » = paraphrase correcte et complète de « Cadit Hesperias Phoebus in undas... »). Le texte source porte des artefacts d'apparat critique (doublons entre accolades `{redituque}`) qui semblent perturber le jugement de Jev sur la poésie latine mise en prose anglaise. **Limite connue : Jev est mal calibré sur les paires vers latin → prose anglaise avec apparat critique visible** — plusieurs entrées `passage_boethius_cons_*` de la file `partial_coverage` sont probablement dans ce cas, à vérifier en priorité par échantillonnage avant adjudication en masse.
3. **Vrai problème structurel (catégorie entière)** — `passage_epict_23` / `..._en` (`identical_text p = 0,81`). Le nœud « original » n'est *pas* un texte grec continu : c'est une liste à puces de termes grecs isolés + un commentaire anglais ; la « traduction » est quasiment le même commentaire anglais reformulé. Ce nœud porte `metadata.passage_role = "vocabulary_gloss"` — **144 nœuds `target` du corpus entier ont ce rôle** (voir `data/kg/nodes.jsonl`), donc la catégorie entière des paires `vocabulary_gloss` mérite un traitement à part : ce ne sont pas des « traductions » au sens strict mais des gloses, et le test `identical_text` les repère correctement.
4. **Autre problème structurel** — `passage_alexander_de_fato_14` (nœud « original », grec) contient en réalité une section `**English Translation (Sharples 1983):**` intégrée à sa propre description, dupliquant presque mot pour mot le nœud `..._en` séparé. Le nœud original n'est donc pas grec‑seul ; `identical_text p = 0,88` a bien détecté ce mélange.

## Partie B — description ↔ identité (3 205 nœuds non‑`passage`, description ≥ 60 car.)

Répartis : argument 1 676, publication 419, person 401, work 251, concept 212, synthesis 155, debate 20, school 16, position 14, quote 14, group 8, source_collection 6, controversy 5, event 5, conceptual_evolution 3.

Distribution de `about_entity` (la description parle‑t‑elle bien de l'entité nommée ?) :

| Tranche | N | % |
|---|---|---|
| ≥ 0,9 | 1 687 | 53 % |
| 0,7–0,9 | 1 224 | 38 % |
| 0,3–0,7 | 263 | 8 % |
| ≤ 0,3 | 31 | 1 % |

### Files
- `queue_b_identity_mismatch.csv` — 33 lignes, `about_entity ≤ 0,3`.
- `queue_b_curator_notes.csv` — 141 lignes, `curator_notes ≥ 0,7`.
- `queue_b_non_english.csv` — 371 lignes au‑dessus du seuil p ≥ 0,7 sur leur langue majoritaire ; répartition complète des 3 205 : `en` 2 620, `fr` 137, `mixed` 386, `de` 19, `it` 24, `other` 19.
- `queue_b_layer_conflicts.csv` — 23 lignes (personnes seulement) — **voir limite ci‑dessous, file à faible fiabilité en l'état**.

### Exemples vérifiés à la main

1. **Vrai bug d'ingestion, un seul nœud vérifié en entraîne 28 autres** — `pub_fedou_2026_adam_time_and_tradition_...` (`about_entity p = 0,01`). Le `label` cite un compte‑rendu de Michel Fédou sur *Adam, Time and Tradition* (Ecclésiaste/apocalyptique) ; la `description` associée parle en réalité du *Traité sur la prière* d'Origène (édition Vigne). Vérification systématique : **28 des 29 nœuds `pub_fedou_2026_*`** portent mot pour mot la même description bidon (« Le Traité sur la prière d'Origène, désormais accessible... »), le 29ᵉ porte une variante espagnole du même texte bidon (« El Tratado sobre la oración de Orígenes... »). C'est un lot entier de comptes‑rendus bibliographiques « Michel Fédou 2026 » dont la description a été écrasée par un texte générique sans rapport — à corriger en priorité, hors périmètre de cette campagne (pas d'écriture KG ici).
2. **Note éditoriale qui a fuité dans la description (vrai positif)** — `scholarly_argument_engberg_pedersen_fate_and_moral_responsibility__2` (`curator_notes p = 0,97`) : « Not verifiable in the fonds: the extraction holds only the first page of each chapter... [pending-acquisition: Engberg-Pedersen 2000, full text] ». C'est bien une remarque de vérification destinée à un curateur, pas un contenu pour lecteur.
3. **Faux positif probable (mise en forme, pas une note)** — `concept_logos_krites_alex` (`curator_notes p = 0,97`) : contenu philosophique légitime sur le logos comme juge chez Alexandre d'Aphrodise, mais rédigé avec des MAJUSCULES d'emphase (« EXAMINES », « OPPOSE ») que Jev semble confondre avec une annotation éditoriale. À vérifier au cas par cas — la file n'est pas homogène.
4. **Limite de conception de la question « conflit de strate »** — les 23 entrées de `queue_b_layer_conflicts.csv` sont *toutes* du même type (`described_as_ancient_but_period_modern`), et ce sont toutes des philosophes modernes incontestables (Harry Frankfurt, Sartre, Libet, Haynes, J.S. Mill, J.L. Austin...) correctement étiquetés `period = Modern/Contemporary`. La question posée à Jev (« présenté comme un savant moderne commentant la philosophie ancienne ») ne mesure pas la même chose que « est une personne moderne » : ces philosophes sont des auteurs primaires du débat moderne sur le libre arbitre, pas des commentateurs de sources anciennes, donc Jev répond correctement « non » à une question qui ne détecte pas ce qu'on voulait. **Zéro cas dans l'autre sens** (nœud de période ancienne dont la description se lirait comme celle d'un savant moderne) n'a été trouvé — donc cette file n'a probablement rien à offrir en l'état ; il faudrait reformuler la question (« cette personne est‑elle elle‑même une source primaire du corpus ancien, ou un commentateur qui en parle ? ») avant de la relancer.

## Limites connues

- Jev sous‑performe sur les paires vers latin/grec ↔ prose anglaise portant des artefacts d'apparat critique visibles (accolades, doublons) — voir exemple Boèce ci‑dessus. Échantillonner avant d'adjuger en masse la file `queue_a_partial_coverage.csv`.
- La catégorie `passage_role = vocabulary_gloss` (144 nœuds originaux) n'est pas une vraie paire texte/traduction ; une bonne partie de `queue_a_identical_text.csv` lui appartient probablement. À filtrer à part plutôt qu'à traiter comme un bug de traduction.
- La question « conflit de strate » (volet B, personnes) est mal calibrée pour distinguer « personne moderne » de « commentateur moderne de l'Antiquité » — voir ci‑dessus. Ne pas adjuger `queue_b_layer_conflicts.csv` telle quelle sans relire la question.
- Comme toujours avec Jev : mauvais en arithmétique/dates/comptage, bon en lecture factuelle fermée sur un texte donné — cohérent avec `BRIEF_COMMON.md`.

## Fichiers livrés

Dans `data/quality/jev_2026_09_24/c2_translations_descriptions/` :
- Construction : `build_a_translations.py`, `build_b_descriptions.py`, `run_jev.py` (lanceur générique, reprise sur erreur, retenté automatiquement sur 429/5xx).
- Données : `candidates_a.jsonl` (2 607), `candidates_b.jsonl` (3 205), `questions_a.json`, `questions_b_base.json`, `questions_b_person_extra.json`, `results_a.jsonl`, `results_b.jsonl`, `determ_flags_a.jsonl` (vide), `errors_a.jsonl`/`errors_b.jsonl` (vides après reprise).
- Analyse : `analyze_a.py`, `analyze_b.py`, `summary_a.json`, `summary_b.json`.
- Files d'adjudication : `queue_a_misaligned.csv`, `queue_a_partial_coverage.csv`, `queue_a_identical_text.csv`, `queue_a_language_mismatch.csv` (vide), `queue_a_deterministic_flags.csv` (vide), `queue_b_identity_mismatch.csv`, `queue_b_curator_notes.csv`, `queue_b_non_english.csv`, `queue_b_layer_conflicts.csv`.

## Reste à faire

- Adjudication humaine des files (rien n'a été écrit dans le KG).
- Corriger hors‑campagne le lot des 29 nœuds `pub_fedou_2026_*` à description erronée (bug confirmé, cf. exemple B‑1).
- Reformuler puis relancer la question « conflit de strate » du volet B avant d'exploiter `queue_b_layer_conflicts.csv`.
- Envisager un passage ciblé sur les 144 nœuds `vocabulary_gloss` pour les sortir du périmètre « traduction » plutôt que de les laisser polluer `queue_a_identical_text.csv`.
