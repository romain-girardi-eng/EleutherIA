# Audit savant du PDF de Sharples, *Alexander of Aphrodisias on Fate*

Date de l'audit: 2026-08-24  
Portée: audit documentaire et lecture savante; aucune mutation du KG, du corpus, du registre ou des manifestes.  
Source visuelle: `data/literature_acquisition/sharples_1983_alexander_de_fato.pdf`.  
OCR de navigation: `data/literature_acquisition/sharples_1983_alexander_de_fato_ocr.pdf`.  
Convention: les pages PDF sont des scans de doubles pages après la couverture. Pour les folios arabes vérifiés, `PDF = floor(page imprimée / 2) + 5`.

## Verdict fail-closed

Le volume de Sharples est central et matériellement complet de la couverture à la fin de l'index. Il contient une traduction anglaise de l'ensemble du *De fato*, des traductions de textes connexes, un commentaire, puis une reproduction photographique du texte grec de Bruns et des notes textuelles où Sharples indique ses lectures préférées. Il n'est pas, contrairement au nœud public actuel, une nouvelle « standard critical edition »: Sharples explique qu'il reproduit photographiquement Bruns et qu'il n'a pas pu modifier ce texte lorsque sa traduction suit une autre lecture.

La recollation 2026-08-24 de *De fato* 12 et 20 a correctement corrigé `argument_agent_causation_alex`, mais elle n'a pas couvert plusieurs doublons actifs. `argument_agent_causation_two_way_powers_alexander_q8r9s0t1`, `argument_incompatibilism_alexander_p7q8r9s0`, la description du work, le nœud « common cause » et plusieurs arguments dérivés présentent encore comme texte direct une théorie complète d'agent causation: choix non déterminé, absence de causes antérieures suffisantes, agent ultime et template de toutes les théories libertariennes. Sharples ne valide pas cette reconstruction. Il qualifie certes la conception alexandrine de « libertarian » dans son vocabulaire moderne, mais souligne que le débat grec porte sur la responsabilité, que le traité est dialectique et morcelé, qu'Alexandre ne fournit pas l'analyse causale nécessaire et qu'il ne résout pas la tension entre alternatives, raisons, caractère et absence d'événements sans cause.

L'issue `issue_alexander_agent_causation_reconstruction` ne peut donc plus rester adjudicated comme si tous les nœuds actifs étaient sûrs. Son affected-set omet au moins les anciens doublons et la description du work. Une seconde réparation P0 est nécessaire.

## 1. Identité, intégrité et droits

| Propriété | Scan source | Dérivé OCR |
|---|---|---|
| Chemin | `data/literature_acquisition/sharples_1983_alexander_de_fato.pdf` | `data/literature_acquisition/sharples_1983_alexander_de_fato_ocr.pdf` |
| SHA-256 | `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638` | `ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb` |
| Taille | 17,913,871 octets | 78,655,916 octets |
| Pages PDF | 161 | 161 |
| Nature | scan de couverture puis doubles pages | même scan avec OCRmyPDF/Tesseract |
| Autorité | pagination, texte visible, apparat et mise en page | recherche/navigation seulement |

Identité visible:

- auteur moderne: R. W. Sharples;
- titre: *Alexander of Aphrodisias on Fate*;
- sous-titre/fonction: *Text, translation and commentary*;
- éditeur: Gerald Duckworth & Co. Ltd., London;
- première publication et copyright: 1983;
- ISBN cased: `0-7156-1589-0`;
- ISBN paper: `0-7156-1739-7`;
- droits: tous droits réservés; reproduction, stockage et transmission interdits sans autorisation.

Le scan est un support de vérification interne. Ni la traduction anglaise, ni le commentaire, ni les notes textuelles ne doivent être republiés. Le grec ancien du corpus doit continuer à provenir du TEI Bruns/OGL épinglé, non d'une OCR du livre sous copyright.

## 2. Carte matérielle et fonction des parties

| Objet | Pages imprimées | Pages PDF | Statut |
|---|---:|---:|---|
| Couverture | sans folio | 1 | visible |
| Titre | sans folio | 2 | visible |
| Copyright et table | sans folio / v-vi | 3 | visible |
| Préface | vii-ix | 4-5 | continue |
| Abréviations | x-xi environ | 5 | continue |
| Introduction | 3-32 | 6-21 | contrôlée; sections clés lues intégralement |
| Analyse de l'argument | 33-40 | 21-25 | lue intégralement |
| Traduction du *De fato* | 41-93 | 25-51 | chapitres I-XXXVIII routés; chapitres prioritaires relus |
| *Mantissa* XXII-XXV | 94-115 | 52-62 | routage et loci relatifs au pouvoir des opposés contrôlés |
| *Quaestiones* et *Topics* | 116-124 | 63-67 | routage contrôlé |
| Commentaire | 125-178 | 67-94 | commentaires prioritaires lus intégralement |
| Reproduction grecque de Bruns | 179-230 | 94-120 | limites visuelles contrôlées |
| Sigla | 231-234 | 120-122 | limites contrôlées |
| Notes textuelles | 235-281 | 122-145 | routage ciblé; elles portent les écarts à Bruns |
| Bibliographie | 282-288 | 146-149 | lue/routée |
| Index des passages | 289-303 | 149-157 | limites contrôlées |
| Index général | 304-310 | 157-161 | dernière page visible p. 310; verso droit blanc attendu |

La préface interdit une confusion essentielle: le grec est un fac-similé de Bruns. Les astérisques marginaux signalent les endroits où la traduction suit une lecture différente; ces différences sont justifiées dans les notes textuelles après le fac-similé.

## 3. Structure exacte du *De fato*

| Ensemble | Chapitres | Fonction selon l'analyse de Sharples |
|---|---|---|
| Dédicace et programme | I | opinion attribuée à Aristote et critique de positions adverses |
| Théorie positive du destin | II-VI | destin comme cause efficiente et nature individuelle; ce qui advient naturellement survient le plus souvent, non toujours |
| Difficultés du déterminisme | VII-XXI | hasard, contingence, possibilité, délibération, responsabilité, pratiques humaines, puis argument de risque de XXI |
| Arguments déterministes et réponses | XXII-XXV | causalité, unité du cosmos et absence de mouvements sans cause |
| Action et caractère | XXVI-XXXII | formation du caractère, rareté du sage, action contraire à la disposition, prescience |
| Arguments divers | XXXIII-XXXVIII | conséquences, logique des chaînes, loi, responsabilité et définitions |

Cette structure est surtout polémique. Sharples avertit que les arguments sont souvent dialectiques et que le work ne construit pas partout une théorie positive systématique.

## 4. Claims secondaires atomiques de Sharples

Les énoncés suivants sont des positions ou évaluations de Sharples, non des paroles directes d'Alexandre.

| ID | Claim attribué à Sharples | Pages imprimées / PDF | Qualification |
|---|---|---:|---|
| SHA-01 | Le *De fato* est l'un des traitements antiques conservés les plus complets de responsabilité et déterminisme, et un témoin important mais hostile pour la Stoa. | 3, 19-21 / 6, 14-15 | témoin secondaire à utiliser avec grande prudence |
| SHA-02 | Il serait trompeur de projeter automatiquement le problème moderne sur Platon ou Aristote; chez Aristote, la différence entre absence de prédétermination et simple irrégularité n'est pas toujours claire. | 3-7 / 6-8 | cadrage historiographique de 1983 |
| SHA-03 | Le débat grec est conduit en termes de responsabilité (`to eph' hêmin`), non de liberté ou free will; Sharples emploie néanmoins « libertarian » et « freedom » comme taxonomie moderne. | 8-9 / 9 | garde d'attribution obligatoire |
| SHA-04 | Alexandre isole souvent le déterminisme du système stoïcien et donne une présentation partielle ou hostile; ses rapports sur la Stoa doivent être vérifiés contre d'autres témoins. | 18-21 / 14-15 | critique de source |
| SHA-05 | Sharples classe la conception d'Alexandre comme libertarienne et lit ses pouvoirs pour les opposés comme non qualifiés; Alexandre refuse cependant le mouvement sans cause. | 21-22 / 15-16 | taxonomie moderne, non terme grec |
| SHA-06 | Alexandre ne résout pas réellement la combinaison d'alternatives libertariennes avec une explication rationnelle de l'action. | 22, 146-149, 163-164 / 16, 78-79, 86-87 | limite décisive contre l'ancien nœud agent-causal |
| SHA-07 | La théorie II-VI du destin comme nature individuelle est présentée comme aristotélicienne, mais elle formule une opinion qu'Aristote n'avait pas lui-même consciemment développée; le passage espèce→individu est tendu. | 23-24 / 16-17 | ne pas attribuer directement à Aristote |
| SHA-08 | Au chapitre XIV, Alexandre néglige ou déforme l'accent stoïcien sur la raison et l'assentiment; il distingue responsabilité rationnelle et volontaire d'une façon potentiellement paradoxale. | 144-146 / 77-78 | polémique, non réfutation acquise |
| SHA-09 | Au chapitre XV, dire que l'agent est une origine ne suffit pas à résoudre le dilemme déterminisme/événement sans cause; Alexandre ne développe pas l'analyse causale requise. | 146-149 / 78-79 | aucune théorie complète d'agent causation établie |
| SHA-10 | Les chapitres XVI-XXI confondent souvent déterminisme et fatalisme en supposant que des actions prédéterminées ne changeraient rien; leur force dépend d'une lecture libertarienne de la responsabilité que la Stoa refuse. | 150-152 / 80-81 | plusieurs arguments sont explicitement jugés erronés |
| SHA-11 | L'argument de XXI est un `tour de force` comparable à un pari de Pascal, pas une démonstration déclarée valide. | 152 / 81 | Hildebrandt 2022 en propose une défense ultérieure distincte |
| SHA-12 | Au chapitre XXII, Alexandre peut écarter les distinctions de causes pour son objection, mais cela ne fournit pas sa propre analyse positive de la causation. | 152-153 / 81 | ne pas convertir en modèle agent-causal positif |
| SHA-13 | Les chapitres XXVI-XXIX rencontrent un regress sur la responsabilité du caractère; les réponses finales sont négatives et la relation entre choix rationnel, caractère et alternatives reste non résolue. | 159-164 / 84-87 | l'ancien nœud « two-way powers » masque cette dette |
| SHA-14 | La prescience divine que XXX autorise hypothétiquement porte sur le fait que l'agent pourra choisir d'une façon ou de l'autre, pas sur le choix effectif futur. | 164-165 / 87 | limite importante pour les nœuds foreknowledge |

## 5. Recollation primaire prioritaire

| Locus | Traduction Sharples | Commentaire | Usage sûr |
|---|---:|---:|---|
| *De fato* 8-9 | 48-53 / PDF 29-31 | 131-136 / PDF 70-73 | hasard et contingent; les critiques peuvent jouer sur les sens |
| 11-12 | 56-60 / PDF 33-35 | 139-143 / PDF 74-76 | délibération, contrôle des opposés; 12/20 déjà atomisés |
| 13-15 | 60-64 / PDF 34-36 | 143-150 / PDF 76-80 | responsabilité stoïcienne rapportée, raison et agent comme origine; causalité non résolue |
| 16-21 | 64-70 / PDF 37-40 | 150-152 / PDF 80-81 | arguments pratiques, louange/blâme, fatalisme et risque |
| 22-25 | 70-75 / PDF 40-42 | 152-158 / PDF 81-84 | unité et classifications causales stoïciennes; réponses d'Alexandre |
| 26-29 | 75-80 environ / PDF 42-45 | 159-164 / PDF 84-87 | caractère, apprentissage, regress, alternatives |
| 30-32 | 80-85 environ / PDF 45-47 | 164-168 / PDF 87-89 | prescience et retour au caractère |
| 33-38 | 85-93 / PDF 47-51 | 168-173 / PDF 89-91 | logique, loi et clôture polémique |

Les numéros de chapitre dans le corpus OGL sont fiables comme route, mais plusieurs lignes portent encore `language=null`, `passage_role=null` et des artefacts textuels déjà observés dans 8 et 11. Toute promotion à exactitude doit être recollée au TEI Bruns épinglé et, si nécessaire, au fac-similé grec.

## 6. Défauts factuels et d'attribution du KG

### 6.1 Nœuds contradictoires actifs

`argument_agent_causation_alex` est prudent. Les nœuds suivants contredisent encore ses limites:

- `argument_agent_causation_two_way_powers_alexander_q8r9s0t1`;
- `argument_incompatibilism_alexander_p7q8r9s0`;
- `argument_common_cause_alex`;
- `work_de_fato_alexander_c200ce_o6p7q8r9`;
- `passage_alexander_de_fato_15` si son texte enrichi/identité n'est pas un twin exact;
- les arguments dérivés `argument_power_contraries_alex`, `argument_praise_blame_alex`, `argument_reactive_attitudes_alex`, `argument_moral_assessment_alex`, `argument_deliberation_alex`, `argument_providence_freedom_alex`, `argument_saving_teaching_alex` et `argument_performative_contradiction_alex` doivent être reclassés claim par claim.

Assertions à retirer comme directes jusqu'à preuve secondaire atomique:

- le choix d'Alexandre serait lui-même non causé par des événements antérieurs;
- l'agent serait une `substance-cause` ou une cause ultime au sens technique moderne;
- *De fato* 12 établirait seul la différence pouvoir rationnel bilatéral/pouvoir naturel unilatéral;
- les mêmes circonstances internes et externes laisseraient directement deux choix sans aucun caveat textuel;
- le common-cause model serait la théorie positive alexandrine qui remplace la chaîne stoïcienne;
- l'agent causation alexandrine serait devenue le template de toutes les théories ultérieures;
- l'influence médiévale générale affirmée par la description du work serait acquise sans unités bibliographiques.

### 6.2 Publication Sharples mal typée

`pub_sharples_1983_alexander_fate` déclare `type=critical edition with commentary` et appelle le livre « the standard critical edition ». Le rôle correct est plus précis: traduction et commentaire avec fac-similé de Bruns 1892, plus notes de lectures divergentes. Les affirmations « transformed Alexander », « universally regarded » et « virtually all subsequent scholarship » sont promotionnelles et non vérifiées.

### 6.3 Source secondaire non enregistrée

Le scan et son OCR figurent au manifeste d'acquisition, mais aucune source `src_sec_sharples_1983_alexander_on_fate` ni manifestation page-level n'existe dans le registre/manifeste savant. L'actuelle source antique mélange donc le TEI primaire et le livre secondaire sans identité secondaire autonome.

### 6.4 Issue faussement bornée

L'issue adjudicated `issue_alexander_agent_causation_reconstruction` n'affecte que quatre IDs et affirme que les unsupported premises sont inactives. Les anciens nœuds montrent que ce n'est pas vrai globalement. L'issue doit être rouverte ou complétée par une nouvelle issue critique liée, avec tous les doublons actifs et leurs arêtes/citations.

## 7. Réparation P0 recommandée

1. Ajouter Sharples 1983 comme source secondaire et manifestation distincte, avec page-map des doubles pages, SHA-256 et droits `unverified_do_not_republish`.
2. Corriger le nœud publication et le BibTeX: titre/sous-titre, London, Duckworth, deux ISBN; ne pas l'appeler nouvelle édition critique.
3. Inventorier tous les nœuds/edges qui exposent une agent causation forte; fusionner leurs claims directs dans `argument_agent_causation_alex`, conserver les reconstructions attribuées comme discovery-only, et désactiver les doublons incompatibles.
4. Réécrire la description du work en distinguant: théorie II-VI du destin; critique VII-XXXVIII; taxonomie moderne de Sharples; limites causales; réception encore à vérifier.
5. Atomiser les arguments 8-11, 13-16, 21-22 et 26-29; typer `direct`, `reported_stoic`, `dialectical`, `Sharples_interpretation` et `modern_reconstruction`.
6. Relire les passages OGL correspondants, corriger les corruptions et enrichir langue/rôle/hash sans copier la traduction Sharples.
7. Mettre à jour le registre: issue critique ouverte; preuves Sharples `in_review`; ancienne issue 12/20 conservée comme résolution locale, non comme clôture globale.
8. Revue indépendante d'un second scholar/agent sur chaque reconstruction; aucun `verified_reference` global tant que la source exacte et les pages ne sont pas structurées.

## 8. Gates d'acceptation

- zéro nœud actif affirmant une cause ultime/non causée comme texte direct d'Alexandre;
- tous les claims forts reliés à une source secondaire, des pages et un statut contesté;
- `pub_sharples_1983` décrit comme traduction/commentaire avec fac-similé Bruns;
- manifestation 161 pages, page-map et droits vérifiés;
- exact changed-node set; aucun doublon contradictoire citable;
- corpus/OGL et traduction Sharples jamais fusionnés;
- passages 8, 11 et autres loci touchés recollés et sans artefacts OCR;
- issue globale ouverte jusqu'à revue indépendante/humaine;
- corpus, snapshot, parité, work-child, work-ID, manifeste, schéma normatif, BibTeX/report, registry et evals stricts verts;
- transaction idempotente avec before-images, drift abort et rollback durable.

## 9. Statut de sortie

- Identité physique/bibliographique: **pass**.
- Complétude matérielle du scan: **pass** de la couverture à p. 310; verso final blanc.
- Lecture structurelle complète: **pass**.
- Lecture substantielle des loci prioritaires: **pass**.
- Réutilisation publique du texte Sharples: **interdite sans permission démontrée**.
- Fidélité du nouveau nœud 12/20: **pass local**.
- Cohérence factuelle globale des nœuds Alexandre: **fail P0**.
- Autorisation de clore l'issue agent causation: **refusée**.
