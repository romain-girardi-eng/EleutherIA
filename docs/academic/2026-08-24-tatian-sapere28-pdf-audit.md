# Audit savant du PDF de Tatien, *Rede an die Griechen* (SAPERE 28)

Date de l'audit: 2026-08-24  
Portée: lecture savante et audit en écriture documentaire seulement; aucune modification du KG, du corpus, du registre ou des manifestes.  
Source visuelle faisant autorité pour la collation et les pages: `data/literature_acquisition/SAPERE28_Tatian_Rede_an_die_Griechen_2016_OA.pdf`.  
Convention: `p.` désigne la pagination imprimée; `PDF` désigne la page physique du fichier, comptée à partir de 1.

## Verdict fail-closed

Le volume établit avec une précision suffisante les loci centraux de Tatien sur l'`autexousion`, la responsabilité, la prescience, l'astrologie et l'`heimarmene`. Il révèle toutefois un défaut P0 dans EleutherIA: les trois lignes de corpus censées représenter les chapitres grecs 7, 8 et 11 contiennent actuellement des synthèses éditoriales bilingues et des traductions machine. Six nœuds les revendiquent simultanément comme snapshots exacts, dont trois nœuds anglais. Ces lignes ne sont donc pas des preuves primaires publiables.

Le défaut ne se limite pas au rôle textuel. Plusieurs notices publiques déplacent les sous-loci: l'`eleutheria tes prohaireseos` est en 7.2 dans la présente édition, la formule «au-dessus de l'heimarmene» en 9.3, et la formule selon laquelle l'`autexousion` a causé la perte humaine en 11.4. Les notices affichent respectivement 7.1, 9.1 et 11.2. Le nœud d'argument «Above Fate» réduit en outre l'efficacité astrologique à une simple tromperie. L'essai d'Andrei Timotin précise au contraire que Tatien ne nie pas l'influence des horoscopes et des planètes; il la subordonne à une puissance démonique dont la conversion au Dieu unique délivre les chrétiens.

Aucune extraction substantielle du grec, de la traduction allemande ou des essais ne doit être republiée depuis ce PDF. La page de copyright interdit explicitement la reproduction, la traduction et l'intégration électronique hors des limites légales. Le volume sert ici à vérifier la pagination, les sous-loci, les variantes visibles et les interprétations attribuées. La restauration du texte grec doit repartir d'une manifestation antique distincte, libre et épinglée, par exemple l'édition Otto 1851 exposée par Scaife/Perseus, puis être recollée aux pages SAPERE sans fusionner les éditions.

## 1. Identité, intégrité et droits

| Propriété | Valeur contrôlée |
|---|---|
| Chemin | `data/literature_acquisition/SAPERE28_Tatian_Rede_an_die_Griechen_2016_OA.pdf` |
| SHA-256 | `33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db` |
| Taille | 3,063,004 octets |
| Pages | 345 |
| Titre PDF | *Gegen falsche Götter und falsche Bildung* |
| Auteur PDF | Tatian |
| Format | PDF 1.7, 411.075 × 637.876 points, rotation 0, non chiffré |
| Nature | texte incorporé, non balisé; AcroForm déclaré; aucun JavaScript |
| Titre éditorial | *Gegen falsche Götter und falsche Bildung. Tatian, Rede an die Griechen* |
| Série | SAPERE, Band XXVIII |
| Direction | Heinz-Günther Nesselrath |
| Éditeur | Mohr Siebeck, Tübingen |
| Année et identifiants | 2016; ISBN `978-3-16-152821-7`; eISBN `978-3-16-156427-7` |
| Droits visibles | copyright Mohr Siebeck 2016; aucune licence ouverte déclarée |

Le PDF est une édition, une traduction allemande annotée et un recueil d'essais. Il ne constitue pas une simple reproduction d'une édition ancienne. La préface précise que la constitution grecque de Nesselrath suit parfois sa propre voie face aux divergences entre Marcovich, Whittaker et Trelenberg. Une variante visible dans ce volume ne doit donc pas être injectée silencieusement dans la manifestation Perseus/Otto.

## 2. Carte de pagination vérifiée

| Objet | Pages imprimées | Pages PDF | Contrôle |
|---|---:|---:|---|
| Titre, copyright, préface et table | liminaires | 1-12 | lecture visuelle; droits et identité confirmés |
| Début du texte grec/allemand | 38 | 49 | début contrôlé |
| Or. 7.1-7.5 | 48-50 | 59-61 | contrôle visuel individuel; 7.2 et 7.3 relus |
| Or. 8.1-8.5 | 50-52 | 61-63 | contrôle visuel individuel; 8.1 relu |
| Or. 9.1-9.3 | 52-54 | 63-65 | contrôle visuel; 9.3 relu |
| Or. 11.1-11.4 | 56-58 | 67-69 | contrôle visuel individuel; la phrase clé continue en haut de p. 58 |
| Or. 15.8-15.10 | 66 | 77 | contrôle visuel individuel |
| Strutwolf/Lakmann, liberté après la chute | 233-234 | 244-245 | contrôle visuel individuel |
| Timotin, astrologie et démons | 278-281 | 289-292 | extraction continue et contrôle visuel p. 278-280 |
| Bibliographie | 307-314 | 318-325 | limites contrôlées par la table et l'extraction |
| Indices | 315-332 | 326-343 | limites contrôlées |
| Notices d'auteurs | 333-334 | 344-345 | fin du fichier contrôlée |

Sur le corps arabe vérifié, la règle est `PDF = p. imprimée + 11`.

## 3. Loci primaires atomiques

Les formulations ci-dessous sont des paraphrases minimales de Tatien. Elles ne convertissent pas un terme grec ancien en théorie moderne de la volonté sans attribution.

| ID | Locus exact | Page imprimée / PDF | Contenu minimal vérifié | Limite interprétative |
|---|---|---:|---|---|
| TAT-P01 | Or. 7.2 | 48 / 59 | Anges et humains relèvent d'une création `autexousios`; le bien n'est pas leur nature et l'accomplissement humain est relié à la liberté de la `prohairesis`; blâme et louange sont explicitement motivés. | Ne pas traduire automatiquement par une faculté augustinienne ou moderne de «volonté». |
| TAT-P02 | Or. 7.3 | 48 / 59 | Le Logos prévoit les issues non selon l'`heimarmene`, mais en fonction du jugement de ceux qui choisissent de manière autonome. | La prescience non fatale n'est pas ici une théorie complète de la modalité. |
| TAT-P03 | Or. 8.1 | 50 / 61 | Les démons introduisent l'`heimarmene` par une représentation astrale; Tatien la dit injuste et met en série juge/jugé, meurtrier/tué, riche/pauvre. | La conséquence précise pour la responsabilité est une reconstruction, même si l'injustice est directe. |
| TAT-P04 | Or. 9.3 | 52 / 63 | Le locuteur chrétien se dit «au-dessus de l'heimarmene», connaît l'unique maître non errant et refuse les législateurs du destin. | Le moyen est décrit religieusement; ne pas le réduire sans preuve à une `gnosis` technique ou à une négation de toute efficacité astrale. |
| TAT-P05 | Or. 11.4 | 56-58 / 67-69 | Les humains ne furent pas faits pour mourir, meurent par eux-mêmes, furent perdus par l'`autexousion`, mais ceux qui ont manifesté le mal peuvent de nouveau le refuser. | Le texte ne dit pas à lui seul que «le libre arbitre est le moyen du salut» ni qu'il oppose une anthropologie chrétienne unifiée à Paul. |
| TAT-P06 | Or. 15.9 | 66 / 77 | Les démons donnent des lois de mort conformément à leur `autexousion`; les humains reçoivent un appel à la conversion. | Distinguer agent démonique, agent humain, foi et repentance. |

### Corrections de sous-loci certaines

- `person_tatian` donne actuellement 7.1, 9.1 et 11.2 pour TAT-P01, P04 et P05; les sous-loci contrôlés sont 7.2, 9.3 et 11.4.
- `passage_tatian_orat_7.metadata.canonical_ref` donne `Orat. 7.1` alors que son texte synthétique mélange 7.1-7.5.
- `passage_tatian_orat_8_9.metadata.canonical_ref` donne `Orat. 8.1` alors que son contenu mélange 8.1, 9.1-9.3 et de l'anglais.
- `passage_tatian_orat_11.metadata.canonical_ref` donne `Orat. 11.1` alors que son contenu mélange 11.1-11.4 et de l'anglais.
- Les découpages `passage_tatian_7_1`, `7_2`, `8_1`-`8_5`, `9_1`, `9_2`, `11_1`, `11_2` ne suivent pas les paragraphes numérotés de SAPERE; leurs identifiants ne doivent pas être assimilés sans table de concordance à cette numérotation imprimée.

## 4. Bibliographie secondaire du volume

### 4.1 Strutwolf et Lakmann, p. 233-234 / PDF 244-245

L'essai soutient explicitement, comme lecture moderne attribuée, que la liberté de l'âme subsiste dans une certaine mesure après la chute et fonde imputabilité et culpabilité. Il relie cette persistance à la possibilité de revenir vers l'état originel, tout en signalant une aporie entre liberté et anthropologie pessimiste. L'essai ne justifie donc ni une auto-rédemption simple ni la conclusion publique actuelle selon laquelle le même pouvoir serait sans réserve «le moyen du salut».

### 4.2 Timotin, p. 278-281 / PDF 289-292

Timotin lit l'anti-astrologie de Tatien comme un argument démonologique dans une controverse plus large avec le déterminisme stoïcien. Point décisif: Tatien ne nie pas l'influence des horoscopes et des planètes; il l'attribue à la domination et à la diversion démoniques. La formule «au-dessus de l'heimarmene» est reliée à la vénération du Dieu unique. Timotin rapproche prudemment ce remède religieux de Theodote et de Plotin. Cela contredit deux formulations trop fortes du KG: la puissance démonique comme simple tromperie dépourvue d'efficacité, et l'unicité de cet antifatalisme parmi les Apologistes.

Ces essais sont sous copyright. Le registre peut conserver des paraphrases page-pinnées et des hashes d'artefact; les textes et traductions ne doivent pas être redistribués.

## 5. Défauts factuels et textuels du snapshot courant

### P0-A — trois passages du corpus grec sont éditoriaux et bilingues

| UUID de corpus | Référence annoncée | Défaut |
|---|---|---|
| `a36c2d9d-9306-4b6f-979a-b8922f7e5d04` | `Orat. 7.1` | 2,361 caractères de titre anglais, extraits grecs, ellipses, deux traductions machine et glossaire; aucun rôle/langue/citability explicite |
| `8ac4c3f3-aab5-4680-80fc-5bc76ee466b0` | `Orat. 8.1` | 1,893 caractères de synthèse anglaise, fragments des chapitres 8 et 9, traductions machine et glossaire |
| `f8ceab87-f393-4ca6-aceb-e28dd1346abe` | `Orat. 11.1` | 2,192 caractères de synthèse anglaise, fragments de 11.1-11.4, traduction machine et interprétation |

Ces trois lignes sont membres de la manifestation `urn_cts_greeklit_tlg1766_tlg001_grc`, que le manifeste décrit comme la version Scaife grecque de l'*Oratio*. Les 39 autres lignes commencent par du grec ancien, mais une vérification ultérieure de la granularité officielle a montré qu'elles correspondent au **premier segment TEI** de chaque chapitre, non nécessairement au chapitre complet; seuls cinq chapitres n'ont qu'un segment. Le corpus déclare donc trois faux originaux et, pour les 39 autres, des extraits exacts dont la couverture doit rester partielle.

### P0-B — six faux snapshots exacts

Chaque UUID P0-A porte deux citations `snapshot_passage_node`: le nœud synthétique dit grec et son nœud de traduction machine anglais. Un texte grec ne peut pas avoir pour twin exact simultanément une synthèse bilingue et sa traduction machine. Les trois arêtes `translation_of` restent utiles seulement comme relations vers des records éditoriaux explicitement bloqués, non comme preuves.

### P0-C — variantes non attribuées et dérives dans les nœuds fins

- `passage_tatian_7_1` contient `τῶν ἀνδρῶν κατασκευῆς`; la page SAPERE 48 lit `τῶν ἀνθρώπων κατασκευῆς`. Le TEI Otto/Perseus épinglé conserve toutefois `ἀνδρῶν`: il s'agit donc d'une divergence d'édition, pas d'une correction universelle à injecter dans Otto.
- `passage_tatian_11_1` contient la duplication `τελευτῶσιν οἱ πλουσιώτατοι σιώτατοι`; SAPERE 56 ne contient pas le second fragment, tandis que la manifestation Otto/Perseus le conserve. Toute correction doit rester rattachée à Nesselrath/SAPERE et ne pas normaliser silencieusement Otto.
- Les claims `source_verified: Whittaker OECT 1982` ne fournissent ni artefact, ni hash, ni page-map; ils ne prouvent pas que la leçon interne vient de Whittaker plutôt que d'un mélange Otto/Marcovich/SAPERE.

### P0-D — surinterprétations des arguments

`argument_tatian_above_fate` doit perdre ou rétrograder les assertions suivantes tant qu'elles ne sont pas page-pinnées:

- la libération viendrait d'une connaissance suffisante parce que le pouvoir des démons serait seulement trompeur;
- l'antifatalisme démonologique serait unique aux Apologistes;
- la position serait un incompatibilisme plus fort établi comme consensus;
- Barnard 1966, Whittaker 1982 et Rankin 2009 soutiendraient précisément l'évaluation logique donnée, sans pages ni manifestation.

`argument_tatian_freewill_paradox` doit distinguer le texte direct de 11.4 de la reconstruction Strutwolf/Lakmann:

- TAT-P05 est direct;
- la persistance post-lapsaire de la liberté est une interprétation secondaire page-pinnée;
- «free will as the means of salvation», le contraste fort avec Paul et le «standard scholarly topos» ne sont pas vérifiés par la source actuelle.

### P1 — identité et complétude de manifestation

La ligne de manifeste Tatien a `cts_urn` vide, `language` absent et aucun artefact épinglé. La route officielle a depuis été identifiée dans la release OGL/Scaife `1.1.32401591783`, objet de tag annoté `1c0e443edec985b9834db888b21d73cde35315ec`, commit `78f9df37d694a9e0e92de2963f2fa8852e49efb6`. Le TEI a pour SHA-256 `bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a`; le catalogue CTS `df7b14a2b0db327787fea20a6a659104808f87a07e8c9017fec0e7a5775579d8`. Le header donne Otto 1851 et CC BY-SA 4.0. Le TEI possède exactement 42 divisions de chapitre, subdivisées en plusieurs segments pour 37 d'entre elles. La réparation doit déclarer cette granularité et ne jamais appeler « chapitre complet » une ligne qui ne représente que le premier segment.

## 6. Réparation P0 recommandée

1. Archiver un TEI grec Otto/Perseus à commit ou release fixe, avec SHA-256 et licence explicite; ne pas dériver le texte du PDF SAPERE sous copyright.
2. Restaurer les trois UUID P0-A en texte grec intégral des chapitres 7, 8 et 11, sans modifier leurs UUID. Pour les 39 autres UUID, conserver les bytes et les typer honnêtement `exact_first_tei_segment_legacy_chapter_excerpt`. Enrichir les 42 lignes avec langue, rôle, manifestation, hash, provenance et granularité explicite.
3. Transformer les trois nœuds `passage_tatian_orat_7`, `passage_tatian_orat_8_9`, `passage_tatian_orat_11` en synthèses éditoriales discovery-only, ou les remplacer comme twins par trois nœuds de chapitre grec exacts. Le nœud 8-9 ne peut pas rester un twin du seul chapitre 8.
4. Supprimer les trois snapshots des nœuds `_en`; conserver ces traductions machine uniquement comme `translation_type=machine`, `passage_role=editorial_translation`, `citability=blocked`, sans corpus UUID primaire.
5. Re-collation ciblée des sous-loci 7.2, 7.3, 8.1, 9.3, 11.4 et 15.9. Créer des evidence units atomiques avec page-map SAPERE et courts extraits hashés, sans republier le volume.
6. Réécrire les deux arguments en séparant `direct`, `reported_interpretation` et `reconstructed`; ajouter les deux unités secondaires Strutwolf/Lakmann 233-234 et Timotin 278-281 comme `in_review`, puis exiger revue indépendante et adversariale.
7. Revalider toutes les citations/arêtes connectées aux trois synthèses, notamment les assertions Crawford/Secord et les relations Justin→Tatien. Les locators externes à ce PDF ne doivent pas être promus sans leurs propres artefacts.
8. Ajouter un issue critique au registre et laisser la source Tatien en couverture `partial` jusqu'à ingestion/collation de tous les segments des 42 chapitres, vérification des variantes d'édition, traduction humaine autorisée et sign-off savant.

## 7. Gates d'acceptation

- zéro texte anglais ou éditorial dans la manifestation grecque Tatien;
- 42/42 lignes identiques à leur unité TEI déclarée: trois chapitres complets et 39 premiers segments; aucune prétention de complétude élargie;
- un seul snapshot exact par UUID et par nœud; aucune traduction machine comme twin primaire;
- zéro sous-locus 7.1/9.1/11.2 pour les phrases contrôlées en 7.2/9.3/11.4;
- aucune normalisation inter-édition silencieuse de `ἀνδρῶν`/`ἀνθρώπων` ou de la duplication Otto; chaque leçon reste rattachée à sa manifestation;
- runtime `evidence_policy` bloque les six synthèses/traductions non exactes;
- les deux arguments n'exposent que les prémisses directes ou des interprétations attribuées et page-pinnées;
- tests adversariaux contre retour des faux snapshots, mélange d'édition, repagination, propagation de traduction machine et republication SAPERE;
- corpus, snapshot, parité, work-child, work-ID, manifeste, registre et eval stricts verts;
- aucune clôture du problème avant deux revues indépendantes et une validation humaine.

## 8. Sources externes de contrôle

- [Scaife/Perseus, notice de l'*Oratio ad Graecos*](https://scaife.perseus.org/library/urn%3Acts%3AgreekLit%3Atlg1766.tlg001/) — identifie Tatien, l'œuvre, Otto 1851 et la version grecque.
- [Scaife/Perseus, exemple de passage et CTS](https://scaife.perseus.org/reader/urn%3Acts%3AgreekLit%3Atlg1766.tlg001.perseus-grc1%3A25) — confirme la granularité de chapitre et le CTS de la version.
- [Perseus, politique des URI CTS stables](https://sites.tufts.edu/perseusupdates/beta-features/perseus-stable-uris/) — décrit la relation entre CTS URN, version et édition.

Ces pages servent à établir l'identité et la route d'acquisition. Le PDF local reste l'autorité visuelle de cet audit pour les pages SAPERE.
