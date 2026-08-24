# Audit savant du PDF de Hildebrandt, « Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism »

Date de l'audit: 2026-08-24  
Portée: lecture intégrale, contrôle visuel et audit documentaire seulement; aucune mutation du KG, du corpus ou du registre.  
Source: `data/literature_acquisition/hildebrandt_2022_alexander_lazy_arguments.pdf`.  
Convention: le fichier commence à la p. imprimée 25; `PDF = p. imprimée - 24`.

## Verdict fail-closed

L'article est déjà représenté par un nœud de publication et huit nœuds d'arguments modernes, et leur noyau sémantique est globalement fidèle. La provenance durable ne l'est pas encore. Le manifeste d'acquisition attribue faussement le PDF à « David Hildebrandt » au lieu de Ronja Hildebrandt; le titre y est abrégé; la manifestation n'existe pas dans le manifeste des sources savantes; le nœud de publication infère une licence `OA` alors que le PDF visible ne donne pas de licence de réutilisation et affiche seulement `© All Copyright Author`.

Les huit arguments portent `citation_verified=true`, mais aucun ne donne le SHA-256 local, une manifestation enregistrée ou un état de revue indépendant. Plusieurs prétendent en outre avoir été normalisés vers `page_range` alors que le champ présent reste `page`. La correction doit donc préserver les paraphrases exactes, réparer l'identité et les droits, puis rétrograder leur statut à `in_review` jusqu'à double vérification.

Deux nuances sémantiques doivent aussi être corrigées. Hildebrandt ne démontre pas qu'un argument d'Alexandre « succeeds » sans réserve: elle le juge plus réussi que les autres et montre qu'une version développée échappe à la réponse chrysippéenne standard. De même, le « scholarly consensus » est sa caractérisation d'une littérature nommée, non un consensus mesuré par EleutherIA.

## 1. Identité et intégrité

| Propriété | Valeur contrôlée |
|---|---|
| SHA-256 | `3a632d61028344ffcba880cebdc6678cfaa22ba456956f55715279928c749717` |
| Taille | 343,020 octets |
| Pages | 20 |
| Format | PDF 1.6, A4, rotation 0, non chiffré, texte incorporé |
| Auteur | Ronja Hildebrandt |
| Titre exact | *Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism* |
| Revue | *Studia Philosophica Estonica* 15 |
| Année / pages | 2022, 25-44 |
| DOI | `10.12697/spe.2022.15.01` |
| ISSN en ligne | `1736-5899` |
| Affiliations affichées | Humboldt University Berlin et Technical University Dortmund, au moment de l'article |
| Droits visibles | `© All Copyright Author`; aucune licence standard explicite dans le PDF |

La disponibilité publique ou le statut éditorial open-access ne valent pas licence de republication. Les `quote_verbatim` doivent rester courts, internes et soumis aux droits; les exports publics privilégieront la paraphrase avec page.

## 2. Carte de lecture intégrale

| Section | Pages imprimées | Pages PDF | Contrôle |
|---|---:|---:|---|
| Résumé et introduction | 25-27 | 1-3 | lecture intégrale; p. 25 rendue visuellement |
| Deux objections par homonymie | 27-30 | 3-6 | lecture intégrale |
| Versions traditionnelles du Lazy Argument | 30-33 | 6-9 | lecture intégrale |
| Co-fatedness et cylindre | 32-37 | 8-13 | lecture intégrale; p. 37 rendue visuellement |
| Argument de risque, De fato XXI | 37-42 | 13-18 | lecture intégrale; p. 39 et 42 rendues visuellement |
| Bibliographie | 42-44 | 18-20 | lecture intégrale; dernière page rendue |

Le fichier ne contient ni couverture, ni liminaires indépendants, ni annexe. Il correspond exactement au tiré à part pagination 25-44.

## 3. Claims atomiques attribués

| ID | Claim de Hildebrandt | Pages | Ancrage antique | Qualification |
|---|---|---:|---|---|
| HIL-01 | Elle présente une version de l'Argument paresseux en *De fato* XXI comme plus réussie que les objections ordinaires d'Alexandre. | 25-27, 37-42 | Alexandre, *De fato* 21, Bruns 191.2-26 | thèse centrale de Hildebrandt, non consensus établi |
| HIL-02 | Les objections de *De fato* 8-9 échoueraient à cause de deux sens de « contingent »: non déterminé par l'essence ou par une cause propre, versus non déterminé par l'état causal du cosmos. | 27-30 | Alexandre, *De fato* 8-9 | reconstruction critique moderne |
| HIL-03 | Les premières versions alexandrines ciblent l'inutilité de la délibération puis de l'effort. | 30-32 | *De fato* 11, 179.12-20; 16, 186.30-187.2 | distinction textuellement étayée |
| HIL-04 | Chrysippe répond à la version traditionnelle par les événements co-fated: actions et délibérations appartiennent au nexus causal. | 32-33 | Cicéron, *De fato* 28-30; parallèles Origène, Sénèque, Eusèbe | réponse chrysippéenne transmise, non autographe |
| HIL-05 | Hildebrandt renforce cette réponse avec le cylindre: impulsion extérieure comme cause précédente, nature individuelle comme cause complète, puis assentiment et action. | 33-37 | Cicéron, *De fato* 42-43; Aulu-Gelle 7.2.11-13; Plutarque 1056a-c | les noms causaux sont reconstruits à partir de plusieurs témoins |
| HIL-06 | L'argument de XXI compare deux erreurs: croire faussement à l'indéterminisme n'altérerait que les mots si tout est fatal; croire faussement au déterminisme pourrait supprimer délibérations et actions bonnes. | 37-40 | Alexandre, *De fato* 21, 191.6-23 | asymétrie directement présente; cadrage « risque » moderne |
| HIL-07 | La cible peut être l'agent rationnel moyen, limité épistémiquement, plutôt que le sage stoïcien idéal. | 39-41 | extension interprétative de Hildebrandt | ne pas attribuer directement à Alexandre |
| HIL-08 | Deux raisons supplémentaires de devenir paresseux — absence de source ultime et ignorance des actions co-fated — sont ajoutées par Hildebrandt, la seconde à partir de Brennan. | 40-41 | Brennan 2005, 275-277 notamment | explicitement au-delà du texte d'Alexandre |
| HIL-09 | Le risque motivationnel subsisterait même si le déterminisme était vrai; aucune réponse stoïcienne à cette nouvelle version n'est transmise. | 41-42 | extension de Hildebrandt | absence de réponse connue, non preuve d'absence absolue |

## 4. État des nœuds existants

Les huit nœuds `scholarly_argument_hildebrandt_*` correspondent à HIL-01 à HIL-09 avec deux regroupements. Les corrections suivantes sont nécessaires:

- `scholarly_argument_hildebrandt_alexander_new_lazy_argument_risk`: remplacer « one succeeds » par « one is argued to be more successful » et attribuer le prétendu consensus à Hildebrandt.
- Tous les nœuds: remplacer le faux commentaire de normalisation par un vrai `page_range`; ajouter `publication_id`, `source_artifact_sha256`, `manifestation_id`, `rights`, `claim_status=in_review` et état de revue.
- Les champs `quote_verbatim` ne doivent pas être la preuve principale ni être exportés sans contrôle de droits; les paraphrases page-pinnées suffisent.
- `pub_hildebrandt_2022_alexander_lazy_arguments`: ajouter un titre exact distinct du label UI; remplacer `license=OA` par `access_status=open_access` et `reuse_status=unverified_do_not_republish` tant qu'une licence explicite n'est pas archivée.
- `scholar_hildebrandt_ronja`: présenter les affiliations comme celles affichées en 2022-2023; supprimer l'adresse postale et l'e-mail du texte public, inutiles à l'identité savante.
- Les arêtes `created_by` de l'ancienne vague doivent suivre l'ontologie directionnelle actuelle (`authored_by` ou relation de position savante vérifiée), sans confondre auteur du nœud et auteur antique.

## 5. Défauts de manifeste et de bibliographie

### Erreur factuelle certaine

`data/literature_acquisition/manifest.jsonl` enregistre actuellement:

```text
creators = ["David Hildebrandt"]
```

Le byline, le DOI et le nœud de publication établissent `Ronja Hildebrandt`. Cette erreur doit être corrigée avec test de non-régression.

### Titre et BibTeX

Le manifeste abrège le titre en *Alexander of Aphrodisias and the Lazy Argument*. Le BibTeX utilise comme titre le label UI préfixé `Hildebrandt 2022 —`. Les deux doivent conserver le titre exact de l'article; le label UI peut rester distinct.

### Manifeste savant absent

Le PDF n'a aucune ligne dans `data/scholarly_sources/manifest.jsonl`. Il faut enregistrer une manifestation page-level avec SHA-256, pages physiques 1-20, pages imprimées 25-44, DOI, droits et état de revue. Le nœud de publication et les huit positions doivent tous pointer vers cette même manifestation.

## 6. Dette de preuve primaire connexe

Les citations des nœuds modernes vers les UUID de *De fato* 8, 9, 11, 16 et 21 sont de bonnes routes de contrôle, mais plusieurs lignes grecques du corpus portent encore `language=null`, `passage_role=null` et des artefacts textuels visibles:

- *De fato* 8 contient au moins `ἀργύριον ριον` et `τὸ τὸ`;
- *De fato* 11 répète un segment final autour de `ὑφ’ ἡμῶν ... ἐξουσίαν`.

Ces défauts sont indépendants de la fidélité de Hildebrandt. Ils interdisent de transformer les citations `discussion/paraphrase` en citations directes entièrement vérifiées avant re-collation Bruns/OGL.

Les notes des citations Cicéron mentionnent encore l'ancien identifiant erroné `phi0474.phi049`; la réparation d'identité du *De fato* a établi `phi0474.phi054`. Les UUID peuvent être bons tandis que la note est stale; elle doit être corrigée sans réécrire le texte latin.

## 7. Réparation recommandée et gates

1. Corriger l'auteur et le titre du manifeste d'acquisition; faire passer `audit_status` à un état de deep-read contrôlé.
2. Ajouter la manifestation au manifeste savant, avec règle `PDF = printed - 24`, droits prudents et provenance hashée.
3. Corriger le nœud publication, le BibTeX et son rapport de reproductibilité dans une transaction unique.
4. Enrichir les huit positions avec les pages exactes, mais garder `in_review`; supprimer les claims de normalisation mensongers et les citations `verified` non structurées.
5. Corriger les overclaims HIL-01 et les données personnelles inutiles.
6. Revoir indépendamment les pages 27-42 et recoller *De fato* 8, 9, 11, 16 et 21 contre Bruns/Sharples/OGL avant promotion des relations primaires.
7. Tests: auteur exact; titre exact; DOI/pages; 20 pages; page-map; zéro licence inférée; 8 positions reliées à une manifestation; aucune citation directe depuis un passage grec non recollé; BibTeX/report cohérents; registre valide; idempotence et rollback.

## 8. Statut de sortie

- Lecture intégrale: **pass**.
- Identité DOI/revue/pages: **pass**.
- Auteur dans le manifeste: **fail**.
- Droits/licence: **fail-closed**, licence non démontrée.
- Manifestation secondaire page-level: **absente**.
- Fidélité générale des huit paraphrases: **pass provisoire**.
- Double vérification et sign-off humain: **non effectués**.
- Autorisation d'ingestion publique comme preuve vérifiée: **refusée en l'état**.

## 9. Contrôle éditorial externe

La [notice officielle de *Studia Philosophica Estonica*](https://ojs.utlib.ee/index.php/spe/article/view/22849) confirme Ronja Hildebrandt, le titre, le DOI, le volume 15, les p. 25-44 et la publication du 31 décembre 2022. Elle reprend prudemment la formulation « more successful », non « conclusive ». La notice ne présente aucun bloc de licence dans son rendu public actuel; elle ne suffit donc pas à remplacer le statut de réutilisation prudent par une licence Creative Commons inférée.
