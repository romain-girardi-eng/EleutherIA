# Audit savant du PDF de Boys-Stones, *Platonist Philosophy 80 BC to AD 250*

Date de l'audit: 2026-08-24  
Portée: audit structurel, bibliographique et savant complet des parties pertinentes pour la causalité, le destin, la providence, la liberté, la responsabilité, l'auto-mouvement, le choix et la volonté. Lecture seule de toutes les données; aucun nœud, arête, citation, manifeste, registre ou fichier de corpus n'a été modifié.  
Source: `data/literature_acquisition/boys_stones_2018_platonist.pdf`.  
Convention de pagination: pour tout le corps numéroté, `page imprimée = page PDF - 16`.

## Verdict fail-closed

Le fichier est une manifestation éditoriale complète, techniquement saine et très bien exploitable. Il contient la couverture, les liminaires `i-xiv`, les pages imprimées `1-648`, les vingt chapitres, le glossaire, les références modernes, le catalogue des Platoniciens et les deux index annoncés. Aucun défaut de syntaxe PDF, aucune lacune matérielle et aucun défaut visuel décisif n'ont été constatés.

La représentation savante n'est toutefois pas prête à être promue comme preuve entièrement vérifiée. Les huit nœuds modernes attribués au livre conservent généralement le noyau de l'interprétation de Boys-Stones, mais quatre défauts bloquent une promotion:

1. la manifestation locale n'est pas identifiée au niveau requis: le nœud KG porte uniquement l'ISBN du paperback, alors que le copyright de ce PDF porte l'ISBN hardback et le DOI de la manifestation numérique;
2. le registre conserve une unique evidence unit candidate pour les p. 344-364, sans citation secondaire capturée, et omet donc le claim déjà publié sur les p. 326-329;
3. le nœud de récurrence cyclique transforme une reconstruction explicitement disputée en doctrine générale à confiance élevée;
4. plusieurs arêtes attribuent à Celsus, Numenius, Atticus ou Proclus des positions que ce livre ne leur attribue pas sous cette forme.

Le verdict est donc: **PDF PASS; claims modernes globalement utiles mais PARTIAL; provenance et wiring FAIL-CLOSED; aucune ingestion ou promotion sans réparation et revue indépendante.**

## 1. Identité, manifestation et droits

| Propriété | Résultat contrôlé |
|---|---|
| SHA-256 | `055c525d36794c8477615130cf1fea937a450d03f5ace92ae7327abdede157ac` |
| Taille | 4,375,219 octets |
| Format | PDF 1.6, 664 pages physiques, 407.04 x 614.4 pt, rotation 0 |
| Intégrité | `qpdf --check`: aucune erreur de syntaxe ou d'encodage de flux |
| Chiffrement / scripts | non chiffré; aucun JavaScript; aucun formulaire |
| Accessibilité | non tagué; texte natif présent sur toutes les pages substantielles |
| Titre complet | *Platonist Philosophy 80 BC to AD 250: An Introduction and Collection of Sources in Translation* |
| Auteur | George Boys-Stones |
| Éditeur | Cambridge University Press |
| Copyright / première publication | 2018 |
| DOI | `10.1017/9781139050203` |
| ISBN visible dans le PDF | `978-0-521-83858-0` hardback |
| ISBN paperback officiel | `978-0-521-54739-0` |
| Étendue bibliographique | `xiv + 648` pages; les deux pages physiques supplémentaires sont la couverture et son verso |
| Droits visibles | tous droits réservés; reproduction seulement sous exception légale, licence collective ou autorisation de CUP |
| Statut de réutilisation du dépôt | `unverified_do_not_republish`, approprié et à conserver |

La [notice officielle Cambridge Core](https://www.cambridge.org/core/books/platonist-philosophy-80-bc-to-ad-250/973AF95ACA8E5C1AE3102A33D825546A) réunit correctement les trois identifiants de manifestation: ISBN numérique `9781139050203`, hardback `9780521838580` et paperback `9780521547390`. Le copyright du fichier local identifie le hardback et le DOI. Le nœud `pub_boys_stones_2018_platonist_philosophy` n'est donc pas faux au niveau de l'objet intellectuel, mais il confond actuellement:

- une référence bibliographique au paperback;
- une étendue de 664 pages qui est en réalité le compte physique du PDF;
- un fichier local dont les liminaires identifient le hardback et le DOI.

La manifestation locale doit être enregistrée séparément avec son hash, son compte PDF, sa règle de pagination, son ISBN visible, son DOI et ses droits. La date `2018` reste la date bibliographique justifiée par le fichier; la mise en ligne Cambridge de décembre 2017 est une date de manifestation en ligne, pas une raison suffisante pour réécrire l'année de publication du livre.

Le manifeste d'acquisition est prudent sur les droits, mais il ne conserve ni DOI, ni ISBN de manifestation, ni source d'acquisition. La présence locale n'établit aucune licence de redistribution.

## 2. Carte matérielle et complétude

| Bloc | Pages imprimées | Pages PDF | Contrôle |
|---|---:|---:|---|
| Couverture et verso | sans numéro | 1-2 | couverture raster complète; verso blanc intentionnel |
| Faux-titre, série, titre, copyright | sans numéro | 3-6 | complets |
| Table des matières | v-xi | 7-13 | vingt chapitres et tout le back matter annoncés |
| Remerciements | xii | 14 | complet |
| Abréviations | xiii-xiv | 15-16 | complet |
| Introduction | 1-23 | 17-39 | continu |
| Chapitres 1-2 | 24-80 | 40-96 | continu; p. 80 blanche de fin de partie |
| Partie I, *Cosmology* | 81-82 | 97-98 | faux-titre et verso blanc intentionnels |
| Chapitres 3-12 | 83-364 | 99-380 | continu |
| Partie II, *Dialectic* | 365-366 | 381-382 | faux-titre et verso blanc intentionnels |
| Chapitres 13-16 | 367-456 | 383-472 | continu; p. 456 blanche de fin de partie |
| Partie III, *Ethics* | 457-458 | 473-474 | faux-titre et verso blanc intentionnels |
| Chapitres 17-20 | 459-531 | 475-547 | continu |
| Glossaire | 532-535 | 548-551 | complet |
| Références modernes | 536-592 | 552-608 | de `aa.vv.` à Zumpt; complet |
| Catalogue des Platoniciens | 593-617 | 609-633 | complet |
| Index des sources et références | 618-645 | 634-661 | éditions et loci antiques; complet |
| Index des Notes and Further Reading | 646-648 | 662-664 | complet jusqu'à la dernière entrée |

La pagination arabe est continue de 1 à 648 avec un décalage constant de 16 pages PDF. Les seules pages presque ou entièrement blanches sont les versos et séparateurs de parties attendus. Le document possède 241 signets couvrant les chapitres et sous-sections; les blocs de back matter ont au minimum un signet de tête.

Il n'existe pas d'index thématique général distinct. L'ouvrage propose à la place un index exhaustif des sources et références, puis un index thématique limité aux sections Notes and Further Reading. Cette distinction doit être conservée dans toute description de complétude.

## 3. Contrôle visuel et qualité d'extraction

Trente-six pages ont été rendues et inspectées, notamment la couverture, le titre, le copyright, le sommaire pertinent, les pages imprimées 252, 327-329, 347-351, 353-357, 363, 483, 524, 532, 536, 592, 593, 618, 646 et 648, ainsi que les feuilles blanches et les trois séparateurs de parties.

Résultats:

- aucune coupe de texte, superposition, page manquante ou glyphe noir;
- grec polytonique, italiques, petites capitales, notes et renvois lisibles;
- marges, folios et transitions de sections cohérents;
- couverture nette et pages internes typographiquement uniformes;
- texte natif de bonne qualité pour la navigation et la recherche;
- certaines fontes ont des tables Unicode incomplètes, de sorte que toute citation grecque exacte devrait encore être contrôlée visuellement ou contre une édition primaire.

Le texte extrait a servi uniquement à naviguer. Les conclusions structurales et les pages décisives ont été vérifiées sur le rendu.

## 4. Carte complète des contenus pertinents

| Cluster | Pages imprimées | Pages PDF | Apport pour EleutherIA |
|---|---:|---:|---|
| Introduction, méthode et périmètre | 1-23 | 17-39 | statut de Middle Platonism, prudence envers les témoins tardifs et distinction entre source ancienne et reconstruction moderne |
| Matière, auto-mouvement et mal | 103-116 | 119-132 | la matière dynamique, le mouvement comme source de désordre et le problème de l'imputation du mal |
| Dieu, intellect et volition divine | 147-183, surtout 169-170 | 163-199 | causalité du créateur et langage de volonté divine; pas de faculté humaine de volonté déduite de ce vocabulaire |
| Création et providence | 184-211, surtout 191-192 | 200-227 | articulation entre causalité métaphysique, bonté et soin providentiel |
| Âme du monde et auto-mouvement | 212-249, surtout 215-217 | 228-265 | âme comme moteur auto-mû, coordination causale du cosmos et distribution des conditions sublunaires |
| Âmes individuelles et agency | 250-287, surtout 251-253 et 258-260 | 266-303 | âme individuelle comme principe autonome de mouvement, décision pratique, impulsion et contrôle rationnel |
| Descente, corps et choix de vie | 288-322, surtout 290-295 et 299-302 | 304-338 | choix du corps, caractère, influence céleste, transmigration et responsabilité diachronique |
| Providence | 323-343 | 339-359 | providence par intermédiaires, âme du monde, dieux célestes, daimons, humains vertueux et théodicée |
| Fate | 344-364 | 360-380 | responsabilité, causalité, destin hypothétique, récurrence, choix de l'âme désincarnée, prophétie et alternatives interprétatives |
| Éthique comme médiation providentielle | 459-478 | 475-494 | assimilation à dieu, vie pratique, choix et formation du caractère |
| Passions, akrasia et volonté | 479-488, surtout 483-484 | 495-504 | absence de faculté autonome de volonté; conflit entre raison et impulsions; naissance, habitude et éducation |
| Oracles chaldaïques | 519-531, surtout 524-525 | 535-547 | rapport tardif entre nature, destin, théurgie et liberté; témoin distinct, non preuve immédiate du Middle Platonism antérieur |
| Glossaire | 532-535 | 548-551 | `ἐφ' ἡμῖν` rendu par ce qui dépend de nous et `πρόνοια` par providence/foresight; glossaire sélectif, non lexique complet de la volonté |

Le nœud publication limite actuellement les chapitres pertinents à 11 et 12. Ce choix capture le noyau, mais omet le soubassement causal et psychologique indispensable des chapitres 4, 7-10, ainsi que les conséquences éthiques des chapitres 17-18 et le contrepoint chaldaïque du chapitre 20.

## 5. Synthèse savante contrôlée

La reconstruction propre à Boys-Stones peut être résumée ainsi, sans la transformer en consensus:

- la providence divine produit et maintient l'ordre général, tandis que l'existence et les caractères des individus ne sont pas planifiés comme tels;
- l'âme du monde transmet l'ordre du créateur; les dieux célestes et les daimons peuvent en être des relais;
- l'application du langage providentiel aux humains vertueux est une inférence de l'auteur: le livre souligne qu'aucun témoin ne les appelle techniquement agents de `pronoia`;
- l'autonomie d'un choix incarné réside, sur cette lecture, dans sa provenance interne plutôt que dans une rupture indéterminée de la chaîne causale;
- le destin hypothétique n'oppose pas un choix libre à des conséquences nécessaires: il décrit l'inévitabilité de chaque chaîne causale sans faire de chaque individu l'objet d'un plan providentiel;
- l'âme désincarnée pourrait, en principe, disposer d'une latitude non déterminée, mais Boys-Stones doute que les Platoniciens aient réellement voulu soutenir cette innovation;
- l'ouvrage refuse de traduire automatiquement `τὸ ἐφ' ἡμῖν` par libre arbitre et refuse également d'analyser l'akrasia comme faiblesse d'une faculté indépendante de volonté;
- la récurrence historique exacte est une reconstruction avancée à partir de ps.-Plutarque et d'Origène, mais le livre expose lui-même des lectures rivales qui la refusent.

Ces propositions sont des résultats de lecture secondaire. Elles ne doivent pas être présentées comme si les fragments antiques employaient déjà les catégories analytiques modernes d'autonomie, déterminisme ou libre arbitre.

## 6. Loci antiques: routes de contrôle, pas substituts à la source primaire

| Dossier | Loci signalés par le livre | Statut dans cet audit |
|---|---|---|
| Auto-mouvement de l'âme | Platon, *Phaedrus* 245c-d; *Laws* 892b-c | leads; contrôler grec, contexte et édition indépendamment |
| Lois du destin | Platon, *Phaedrus* 248c-249d; *Timaeus* 41d-42e; *Republic* 10, 614b-fin | leads majeurs; ne pas confondre mythe platonicien et interprétation médio-platonicienne |
| Ps.-Plutarque, destin | *De fato* 568C-E, 569A-C, 570B-D, 571B-D, 572F-574D | plusieurs passages grecs sont déjà fingerprintés dans le corpus; la portée doctrinale reste disputée |
| Alcinous | *Didaskalikos* 16 et 26 | source centrale pour descente, lois du destin, `eph' hēmin` et conséquences; non encore citée directement par les claims 2018 |
| Apulée | *De Platone* 1.12, 205-206 | providence, destin et niveaux d'intermédiaires; à recoller contre l'édition indiquée dans l'index |
| Plutarque | *Table-Talk* 9.5, 740C-D; *Delayed Punishment* 558B-562C | routes pour choix de vie, chance, caractère et responsabilité |
| Origène | *Contra Celsum* 5.21; *De principiis* 1.8.1; 3.5.2 | 5.21 est un témoignage origénien sur Pythagoriciens/Platoniciens; 1.8.1 porte le corollaire de souffrance; 3.5.2 est cité ici pour l'infini, pas pour ce corollaire |
| Celsus chez Origène | *Contra Celsum* 5.14; 7.68; 8.33; 8.45; 4.69 | fragments de Celsus sur ordre, daimons et providence; ne pas lui attribuer *Contra Celsum* 5.21 |
| Aristides Quintilianus | *On Music* 3.26, 131.20-132.30 | modalité, nécessité et contingence; lead à vérifier dans l'édition source |
| Nicostratus | fr. 25F chez Simplicius, *In Cat.* 406.13-16 | futur contingent et bataille navale; lead indirect transmis par Simplicius |
| Maximus de Tyr | *Oration* 13.4f-k | prédiction et intégration de ce qui dépend de nous dans le tout causal |
| Atticus | fragments 3 et 8 chez Eusèbe, *Praeparatio evangelica* 15 | critique de la providence aristotélicienne et rôle de l'âme cosmique; ne fonde pas directement le claim universel sur les individus |
| Philo | *On Dreams* 1.140-143; *On Providence* fr. 2 | intermédiaires et théodicée; dossier distinct à recoller |
| Oracles chaldaïques | fragments 102 et 153 transmis par Proclus et Lydus | réception tardive; ne pas rétroprojeter sans argument sur tout le Middle Platonism |

Le volume traduit et organise ces loci, mais demeure une source secondaire. Une traduction de Boys-Stones n'est pas une nouvelle collation critique. Les loci servent de routes de recherche jusqu'à vérification autonome de la langue, de l'édition, du contexte et de la transmission.

## 7. Manifestations KG et registre existants

### 7.1 Nœuds et arêtes

L'état courant contient:

- 1 publication: `pub_boys_stones_2018_platonist_philosophy`;
- 8 nœuds `scholarly_argument_boys_stones_2018_*`;
- 8 arêtes `advanced_in` vers la publication;
- 8 arêtes `created_by` vers `scholar_boys_stones_g`;
- 40 arêtes `discusses`;
- 1 arête `authored_by` pour la publication;
- 20 citations de passages antiques réparties sur les huit claims.

Les huit `advanced_in` et l'`authored_by` sont structurellement correctes. Les huit `created_by` expriment l'auteur de l'argument moderne; elles ne doivent pas être comprises comme une attribution antique.

### 7.2 Registre

`src_sec_boys_stones_2018_platonist` possède le bon titre, le bon auteur, le bon hash et le bon nœud de publication. Mais son état est stale:

- `acquisition.status=local_unregistered`, alors que `data/literature_acquisition/manifest.jsonl` enregistre déjà le fichier;
- `coverage.state=partial`, avec seulement le nœud publication dans `kg_node_ids`, alors que huit claims existent;
- aucun ISBN, DOI, identifiant de manifestation, page-map vérifié ou état de droits détaillé;
- aucun record correspondant dans `data/scholarly_sources/manifest.jsonl`.

L'unique evidence unit `ev_sec_boys_stones_platonist_pp344_364` reste `candidate`, couvre un bloc de 21 pages, porte `page_map_status=provisional` et `quotation.status=not_captured`. Elle omet entièrement `scholarly_argument_boys_stones_2018_secondary_tertiary_providence`, situé aux p. 326-329.

Le high issue `issue_secondary_archive_manifest_gap_20260824` décrit donc correctement le problème de fond, même si son comptage du manifeste savant est désormais stale.

## 8. Audit claim par claim

| ID | Pages exactes | Verdict | Constat |
|---|---:|---|---|
| `scholarly_argument_boys_stones_2018_autonomy_as_external_independence` | 347-349, noyau p. 347-348 | PASS attribué | Paraphrase fidèle de la reconstruction de Boys-Stones. Garder la formule comme interprétation moderne; les citations antiques sont des discussions, non une preuve directe de la catégorie moderne. |
| `scholarly_argument_boys_stones_2018_cyclical_recurrence_no_astral_determinism` | 350-351; controverse p. 355 | **FAIL overclaim** | Le livre parle de certains Platoniciens, admet que le cycle n'est pas démontré et expose des lectures niant la récurrence. Le label et `confidence=high` généralisent excessivement. Le champ `quote_verbatim` contient en outre une ellipse éditoriale et n'est pas verbatim continu. |
| `scholarly_argument_boys_stones_2018_eph_hemin_not_free_will` | p. 354 | PASS avec locator | Le fond est fidèle. Le locus exact est p. 354, pas l'ensemble 353-355. Les deux citations ps.-plutarquéennes illustrent l'usage antique, mais ne démontrent pas le jugement moderne sur la traduction. |
| `scholarly_argument_boys_stones_2018_hypothetical_fate` | 349-350 | PASS/PARTIAL | Restitution fidèle de l'interprétation de 2018. Elle doit être reliée comme critique de la lecture conventionnelle, non simplement `discusses` vers un concept affirmant que les choix restent libres et seuls leurs effets sont nécessaires. Alcinous 26 manque comme evidence primaire directe. |
| `scholarly_argument_boys_stones_2018_myth_of_er_discarnate_indeterminacy` | 351-353; alternatives p. 355 | PASS/PARTIAL | La description conserve utilement le doute de l'auteur. Le label doit toutefois maintenir le caractère seulement possible et contesté. L'arête vers Numenius ne prouve pas que Numenius défend DCD3. |
| `scholarly_argument_boys_stones_2018_no_divine_determination_individuals` | 345-347 | PASS/PARTIAL | Fidèle comme résumé de Boys-Stones. Ne pas transformer ce résumé en attribution directe à Atticus. L'argument de l'infini est une reconstruction secondaire, même si plusieurs loci antiques sont pertinents. |
| `scholarly_argument_boys_stones_2018_origen_platonists_no_better_than_stoics` | 349 et 356 | **FAIL locator/entailment** | Le claim moderne est bien présent, mais la description rattache `De principiis` 3.5.2 au corollaire de souffrance. Dans le PDF, ce corollaire est référé seulement à 1.8.1; 3.5.2 apparaît p. 346 pour la limite de calcul de l'infini. *Contra Celsum* 5.21 demeure un point de discussion, pas l'énoncé littéral de toute la reconstruction. |
| `scholarly_argument_boys_stones_2018_secondary_tertiary_providence` | 326-329; noyau p. 327-328 | **FAIL qualification/wiring** | L'âme du monde et les daimons sont correctement représentés. Pour les humains, Boys-Stones dit explicitement qu'aucun témoin ne les nomme techniquement providentiels; il propose une inférence `de facto`. Le label actuel les met au même niveau que les daimons. Le passage enregistré comme p. 328 se trouve p. 327. |

Sept des huit champs `metadata.verified_reference` ont exactement 300 caractères et se terminent au milieu d'une phrase ou d'un mot. Ils ne constituent donc pas des références humaines fiables. Le huitième contient l'erreur de page 328/327. Les huit claims ne doivent pas conserver un statut de vérification supérieur à celui des evidence units du registre.

Les huit métadonnées portent aussi `ingestion_debt_2026_08_17_schema_normalised`, qui affirme que le locus a été copié vers le champ canonique `page_range`. Aucun de ces huit nœuds ne possède actuellement `metadata.page_range`; seul l'ancien champ `metadata.page` existe. Le commentaire de normalisation est donc factuellement faux et doit être réparé avec la donnée elle-même.

## 9. Attributions et arêtes à corriger

| Arête ou nœud | Problème | Réparation recommandée |
|---|---|---|
| `db20a7f2-873e-4920-aa60-ceffe95d0d04`: récurrence -> `person_celsus_platonist_2c_ce` | *Contra Celsum* 5.21 est un exposé d'Origène sur Pythagoriciens et Platoniciens, pas un fragment de Celsus | supprimer ou remplacer par une relation vers Origène et le work exact |
| `4d5314bf-f0c3-44a2-9e35-bf7e8691115a`: DCD3 -> `person_numenius_apamea_2c_ce` | le livre signale seulement que Numenius commenta le mythe d'Er; il ne lui attribue pas cette lecture indéterministe | supprimer; au besoin créer une relation prudente au dossier de commentaire, après vérification |
| `ae2e6f8c-a63e-441d-9014-75c57b80375b`: non-détermination des individus -> `person_atticus_2c_ce` | Atticus est central pour la providence, mais n'est pas le témoin direct de ce claim dans le ch. 12 | supprimer ou abaisser vers contexte, avec locus exact |
| `c9353ef5-2895-4bb0-b129-bb2fe43174e8`: providence secondaire/tertiaire -> Numenius | le fragment de Numenius sert d'analogie sur la transmission de la connaissance, pas de témoin de la doctrine à trois niveaux | supprimer comme attribution doctrinale |
| `c30a751b-6ef4-4c90-aed6-1de126f89ae9`: claim 2018 -> `concept_pronoia_levels_proclus_a6d8c9b4` | conflation entre structure médio-platonicienne et théorie proclusienne tardive; les niveaux et leur contenu ne correspondent pas | supprimer ou relier par réception/comparaison explicitement qualifiée |
| claim providence -> `concept_triple_providence_plut` | le concept cible ajoute un déterminisme décroissant, tandis que Boys-Stones insiste sur une même providence non diluée | réparer le concept cible avant de conserver l'arête |
| claim hypothétique -> `concept_conditional_fate_9a5c8b4d` | le concept cible affirme la lecture choix libre/effets nécessaires que Boys-Stones rejette p. 349-350 | remplacer `discusses` par `critiques` ou une arête vers un nœud de débat |
| claim providence, sources directes | Ps.-Plutarque, Celsus et Philo sont absents des arêtes de personnes; Numenius est présent à tort | privilégier des arêtes vers les œuvres/loci exacts plutôt que multiplier les personnes |

Trois nœuds de personne dérivés du livre doivent aussi être revus:

- `person_atticus_2c_ce` dit que Boys-Stones en fait une source clef de la non-détermination divine des individus; le PDF en fait surtout une source de la critique de la providence aristotélicienne;
- `person_celsus_platonist_2c_ce` présente Celsus comme témoin de la récurrence exacte; le locus utilisé pour ce point est la voix d'Origène à 5.21;
- `person_numenius_apamea_2c_ce` lui attribue la providence par proxy et une lecture du mythe d'Er plus déterminées que les données du livre.

`person_nicostratus_2c_ce` et l'arête `e654d227-66f1-4862-9680-03fed1c6c901` vers les futurs contingents sont, en revanche, cohérents avec le texte E du chapitre 12, sous réserve de la vérification primaire de Simplicius.

## 10. Audit des vingt citations antiques

| Claim | Passage IDs actuels | Verdict de sémantique |
|---|---|---|
| autonomie | `4edfbd91-c78b-473a-a942-590912277595`, `f7ce09d8-54e2-4ff0-9606-2421badd2018` | `discussion` approprié; ne pas promouvoir en entailment de l'analyse moderne |
| récurrence | `4edfbd91-c78b-473a-a942-590912277595`, `31c7f3b8-f60c-4603-ba33-4e6c31d8d63c` | le testimonium origénien est pertinent; la `paraphrase` ps.-plutarquéenne doit porter la controverse de traduction et de portée |
| `eph' hēmin` | `15cd3c13-ae01-43e2-b89f-724c52ac3894`, `821bd3e4-c529-4553-9665-5b920143a140` | discussions pertinentes, mais absence d'evidence secondaire de la thèse terminologique |
| destin hypothétique | `f31dc55d-6240-48eb-8017-4155e1b92978`, `821bd3e4-c529-4553-9665-5b920143a140`, `1ff2e855-0550-4906-a5eb-e38ab2aa6550`, `c52dd6fb-b3a5-408b-a2d0-7a4f0e6b4117` | bons anchors ps.-plutarquéens; Alcinous 26 manque; ne pas laisser les passages porter seuls la reconstruction de 2018 |
| mythe d'Er | `9c4fdc4f-411d-5505-9a7f-5e7349e14b77`, `e2810d26-6e24-448c-8f06-46c79ca5ccd6`, `9d34c80c-f53a-4cab-9d1a-6a7e4f04adbf` | le type `direct_quote` du premier passage est inadapté au claim moderne; utiliser `discussion` ou `testimonium`; ajouter Plutarque 740C-D |
| pas de détermination individuelle | `4edfbd91-c78b-473a-a942-590912277595`, `f31dc55d-6240-48eb-8017-4155e1b92978`, `f7ce09d8-54e2-4ff0-9606-2421badd2018` | discussions plausibles; la conclusion générale reste celle de Boys-Stones |
| Origène contre les Platoniciens | `31c7f3b8-f60c-4603-ba33-4e6c31d8d63c` | `discussion` correct; ajouter 1.8.1 seulement après vérification primaire; ne pas lui adjoindre 3.5.2 pour la souffrance |
| providence secondaire/tertiaire | `0b6bfaef-6e09-481f-babb-b918b83c9597`, `35c49908-8ebf-5113-8f2c-dd90798f0291`, `f7ce09d8-54e2-4ff0-9606-2421badd2018` | les doublons grec/anglais de *De fato* 10 et le ch. 9 sont utiles; ils ne prouvent pas l'inférence spécifique sur les humains ni tout le rôle de l'âme du monde |

Les vingt champs `notes` ont exactement 202 caractères et sont tous tronqués. Les trois `repair_note` de la providence sont lisibles, mais ne compensent pas cette perte. Il faut remplacer ces notes à longueur fixe par des records atomiques non tronqués, avec rôle de passage, attestation et portée explicites.

Le corpus possède des manifestations grecques fingerprintées pour plusieurs passages de ps.-Plutarque, ainsi que des passages de Platon et d'Origène. Cela vérifie l'existence de routes primaires; cela ne crée pas automatiquement une citation secondaire au livre de Boys-Stones et ne tranche pas les controverses d'interprétation signalées p. 355.

## 11. Gaps de couverture

Au-delà des défauts de wiring, cinq lacunes empêchent de qualifier la couverture de complète:

1. aucune evidence unit atomique ne capture directement les huit claims modernes avec SHA, page imprimée et page PDF;
2. le cluster providence p. 323-343 est absent de l'evidence unit du registre;
3. Alcinous 26, Plutarque 740C-D, Apulée 1.12, Aristides Quintilianus 3.26, Nicostratus 25F et Maximus 13.4 ne sont pas tous raccordés aux claims qu'ils éclairent;
4. la controverse p. 355 sur la récurrence et les trois familles DCD n'a aucun nœud ou edge dialectique propre;
5. le soubassement des chapitres 8-10 et la négation d'une faculté indépendante de volonté p. 483 ne sont pas représentés dans la couverture déclarée de la publication.

Il n'est pas nécessaire de créer un nœud pour chaque section. Il est nécessaire, en revanche, que les claims existants pointent vers la manifestation secondaire exacte et que les objections internes au livre soient conservées lorsque leur omission change le degré de certitude.

## 12. Réparation recommandée et gates

1. Créer une manifestation secondaire dédiée au PDF local: hash, taille, 664 pages PDF, étendue `xiv + 648`, règle `printed = PDF - 16`, DOI, ISBN hardback visible, ISBN paperback connexe, droits et provenance d'accès si connue.
2. Réconcilier `data/literature_acquisition/manifest.jsonl`, `data/scholarly_sources/manifest.jsonl` et `src_sec_boys_stones_2018_platonist`; supprimer le statut stale `local_unregistered`.
3. Atomiser `ev_sec_boys_stones_platonist_pp344_364` en evidence units secondaires par claim; ajouter le cluster p. 326-329 et enregistrer uniquement des paraphrases.
4. Remplacer les références tronquées de 300 et 202 caractères par des locators structurés; créer les vrais `page_range`; supprimer le faux commentaire de normalisation; corriger p. 327/328, p. 354 et `De principiis` 1.8.1/3.5.2.
5. Rétrograder le claim de récurrence à une reconstruction attribuée et disputée; encoder les objections d'Opsomer/Eliasson comme lectures rivales rapportées par Boys-Stones.
6. Préserver l'inférence humaine comme `de_facto_inference`, pas comme attestation technique de providence tertiaire.
7. Supprimer ou retyper les arêtes Celsus, Numenius, Atticus et Proclus identifiées en section 9; préférer des liens vers œuvres et loci.
8. Rendre dialectique la relation entre la lecture de Boys-Stones et les nœuds conventionnels de destin conditionnel au lieu d'un simple `discusses`.
9. Revoir indépendamment chaque evidence unit et recoller les loci antiques avant toute promotion de `discussion` vers `paraphrase` ou `direct_quote`.
10. Tests minimaux: identité des trois ISBN/DOI; page-map; 8 claims liés à une manifestation; aucune référence tronquée; aucune attribution de 5.21 à Celsus; aucun Numenius-DCD3; aucune conflation Proclus/Middle Platonism; droits fail-closed; idempotence et rollback.

## 13. Statut de sortie

- Intégrité et complétude du PDF: **PASS**.
- Carte de pagination: **PASS, visuellement vérifiée**.
- TOC, glossaire, références, catalogue et index: **PASS**.
- Identité de l'objet intellectuel: **PASS**.
- Identité de la manifestation locale: **PARTIAL**.
- Droits de republication: **non établis; fail-closed**.
- Fidélité générale des huit claims: **PARTIAL**, avec deux overclaims et deux erreurs de locator/qualification importantes.
- Citations antiques: **routes utiles mais insuffisantes pour prouver les claims secondaires**.
- Registre et manifeste savant: **FAIL/PARTIAL**.
- Revue indépendante/adversariale et sign-off humain: **non effectués**.
- Autorisation de mutation KG/corpus/registre: **aucune; refus de promotion en l'état**.
