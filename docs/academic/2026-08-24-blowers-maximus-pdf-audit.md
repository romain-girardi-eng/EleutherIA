# Audit savant du PDF de Paul M. Blowers, *Maximus the Confessor*

Date de l'audit: 2026-08-24  
Portee: lecture savante et controle documentaire du PDF local; aucune modification du KG, du corpus, des registres, des manifestes, des patches ou des donnees d'audit.  
Source visuelle faisant autorite: `data/literature_acquisition/blowers_2016_maximus.pdf`.  
Convention: `p.` designe la pagination imprimee d'Oxford; `PDF` designe la page physique du fichier comptee a partir de 1. Les extractions de texte ont servi uniquement a la navigation. Les decisions sensibles reposent sur les pages rendues.

## Verdict fail-closed

L'objet intellectuel est identifie sans ambiguite: Paul M. Blowers, *Maximus the Confessor: Jesus Christ and the Transfiguration of the World*, Oxford University Press, 2016, DOI `10.1093/acprof:oso/9780199673940.001.0001`, ISBN imprime `978-0-19-967394-0`. Le copyright visible declare une premiere edition de 2016, impression 1. La notice officielle OUP confirme l'auteur, le titre, le DOI, l'ISBN imprime, l'ISBN en ligne `9780191815829`, la date du 1er fevrier 2016 et l'architecture du livre: [notice du livre chez Oxford Academic](https://academic.oup.com/book/25823).

La manifestation locale n'est pas un fac-simile d'un exemplaire relie. C'est une epreuve OUP corrigee et finale, dont les en-tetes portent les dates des 24 et 28 decembre 2015, recomposee en 128 pages PDF tres denses avec marqueurs verts de pagination imprimee. Le fichier Adobe a ete cree en juillet 2016. Il reproduit le corps savant continu de l'Introduction a l'Epilogue, p. 1-334, ainsi que les notes de chaque chapitre, mais il omet des elements physiques attestes dans l'edition publiee: dedication, acknowledgments, liste des abreviations, bibliographie selective et index. La notice OUP enumere explicitement ces preliminaires et cet end matter; la [liste des abreviations](https://academic.oup.com/book/25823/chapter-abstract/193458101), la [bibliographie selective](https://academic.oup.com/book/25823/chapter-abstract/193472020) et l'[index](https://academic.oup.com/book/25823/chapter-abstract/193472277) existent dans l'objet publie mais sont absents du fichier local.

La valeur actuelle `content_completeness: full` dans le manifeste d'acquisition est donc acceptable seulement si elle est explicitement bornee au corps savant principal et aux notes de chapitres. Elle est fausse si elle signifie completude materielle de l'edition. Le titre du manifeste, reduit a `Maximus the Confessor`, est incomplet, et le role generique `source_file` ne distingue pas cette epreuve corrigee d'une manifestation commerciale.

Le statut de droits est strict: copyright Paul M. Blowers 2016, tous droits reserves, interdiction explicite de circulation sous une autre forme sans permission. `reuse_status: unverified_do_not_republish` est prudent. La manifestation doit rester reservee a la verification interne, avec pointeurs et paraphrases seulement; aucune image, page ou longue citation ne doit etre republiee.

Sur le fond, le livre soutient solidement, comme interpretation secondaire attribuee, les distinctions suivantes:

1. la liberte creaturelle est un processus teleologique complexe qui mobilise raison, desir, volition, choix et usage, et non une simple capacite ponctuelle de choisir autrement;
2. la volonte naturelle et la volonte ou modalite gnomique ne sont pas deux facultes symetriques: la premiere appartient a la nature rationnelle, tandis que `gnome` change de fonction et de sens selon les contextes et selon le developpement de Maxime;
3. les ecrits precoces peuvent attribuer une `gnome` vertueuse au Christ, alors que la christologie mature la refuse en la reclassant comme qualite ou mode d'usage, non principe naturel;
4. l'obeissance du Christ a Gethsemani ne supprime pas sa volonte humaine naturelle; Blowers traite toutefois comme un vrai probleme soteriologique la facon dont le Christ peut guerir la vacillation gnomique sans l'assumer lui-meme;
5. la providence, la passivite creaturelle, le mouvement, l'`autexousia` et une necessite dite bienveillante sont articules teleologiquement, non comme une autonomie sans cause;
6. la faute d'Adam est relue comme echec de `gnome` et abus de l'autodetermination, sans transmission genetique de culpabilite;
7. la responsabilite morale est liee a l'usage des facultes et des passions, lesquelles ne sont pas toutes mauvaises par nature;
8. Blowers ne tranche pas Maxime en universaliste simple: la restauration demeure une esperance disputee, tenue avec jugement, libre choix et diversite des destins.

Les principaux risques du KG sont egalement confirmes:

- la serie bibliographique est erronee: le KG dit `Oxford Early Christian Studies`, tandis que les acknowledgments officiels placent le livre dans `Christian Theology in Context` ([page OUP](https://academic.oup.com/book/25823/chapter-abstract/193458016));
- le noeud publication place la chute adamique au chapitre 5, alors que le dossier se trouve au chapitre 6, et place la bataille technique sur les volontes uniquement au chapitre 7, alors qu'elle est exposee d'abord au chapitre 4 puis reprise sous l'angle soteriologique au chapitre 7;
- plusieurs noeuds publient comme conclusion de Blowers ce qu'il rapporte de Sorabji, de von Balthasar, de Doucet, de Schwager, de Larchet ou d'autres interlocuteurs;
- tous les noeuds Blowers examines sont actuellement `citable` par defaut, faute de `metadata.citability`, alors que le registre maintient la source en `local_unregistered`, l'evidence en `candidate`, l'issue de provenance ouverte et aucune verification independante achevee;
- les cinq citations de corpus rattachees a trois arguments Blowers pointent vers Jean Damascene, temoin posterieur de la tradition maximienne, non vers Blowers ni vers une manifestation primaire de Maxime;
- aucun texte primaire de Maxime le Confesseur n'est actuellement ingere dans le corpus sous les IDs de travaux concernes. Les loci antiques de ce rapport sont donc des pistes de recollation, non des sources primaires verifiees.
- cinq des huit `verified_reference` d'arguments sont tronques exactement a
  300 caracteres et les cinq notes de citations a 202 caracteres; la personne
  Maxime et plusieurs `verification_notes` de concepts/travaux presentent la
  meme dette de troncature;
- les huit arguments manquent tous de `page` et de `page_range`, bien qu'une
  note hereditee affirme a tort que `page_range` a ete normalise;
- `work_maximus_quaestiones_thalassium` transforme *Q. Thal.* 21 en locus du
  dossier `eph' hemin`; dans le PDF audite, Blowers l'emploie ici pour la
  passibilite, la generation et les consequences de la chute;
- `issue_secondary_archive_manifest_gap_20260824` parle encore de six lignes
  du scholarly manifest, alors que l'etat courant en contient dix.

## 1. Integrite, identite, manifestation et droits

### 1.1 Controles techniques

| Propriete | Valeur controlee |
|---|---|
| Chemin | `data/literature_acquisition/blowers_2016_maximus.pdf` |
| SHA-256 | `30ccbf8cebb1d9152eff63324d664e68d05a3b0f5605506fd3240dcfe4a92425` |
| Taille | 2,746,710 octets |
| Pages PDF | 128 |
| Format | PDF 1.6, 382.677 x 612.284 points, rotation 0 |
| Chiffrement | aucun |
| Texte | epreuve numerique avec couche textuelle, non scan OCR |
| Producteur | Adobe Acrobat Pro 10.0.0 |
| Dates techniques | creation 2016-07-11; modification 2016-07-14; sans valeur d'edition |
| Balises | document non balise |
| Formulaire | AcroForm declare; aucun JavaScript |
| Controle syntaxique | `qpdf --check`: aucune erreur de syntaxe ou d'encodage de flux |
| Extraction | environ 128,830 mots; utile pour navigation, avec quelques mots concatenes et marqueurs de page intrusifs |

L'extraction est de bonne qualite pour l'anglais et conserve generalement le grec polytonique. Elle ne doit cependant pas servir de preuve autonome: la recomposition rassemble plusieurs pages imprimees sur une page PDF, les marqueurs verts interrompent parfois les mots, et quelques espacements disparaissent.

### 1.2 Identite visible et identite officielle

Les deux premieres pages etablissent visuellement:

- auteur: Paul M. Blowers;
- titre complet: *Maximus the Confessor: Jesus Christ and the Transfiguration of the World*;
- editeur: Oxford University Press;
- copyright: Paul M. Blowers, 2016;
- edition: premiere edition publiee en 2016;
- impression: 1;
- ISBN imprime: `978-0-19-967394-0` (hardback);
- statut de production: `OUP CORRECTED PROOF - FINAL`.

La notice officielle ajoute, pour l'objet publie, le DOI `10.1093/acprof:oso/9780199673940.001.0001`, l'ISBN en ligne `9780191815829` et la date de publication du 1er fevrier 2016. Le fichier local ne suffit pas a prouver un exemplaire physique hardback: il reproduit la ligne ISBN hardback, mais il reste une epreuve numerique sans couverture ni reliure.

Trois niveaux doivent etre conserves:

| Niveau | Identite |
|---|---|
| Oeuvre intellectuelle | monographie de Paul M. Blowers, publiee par OUP en 2016 dans la serie *Christian Theology in Context* |
| Edition commerciale | premiere edition, impression 1, ISBN imprime `9780199673940`, DOI OUP et ISBN en ligne distincts |
| Manifestation locale | epreuve corrigee finale OUP, 128 pages PDF recomposees, main text p. 1-334 avec notes, preliminaires et end matter incomplets |

### 1.3 Droits et politique de citation

La page de copyright interdit la reproduction et la circulation non autorisees. Aucun statut open access ni licence de reutilisation n'est visible. Politique fail-closed:

- usage interne de verification seulement;
- paraphrases originales, titres de sections, pages, loci et empreintes autorises dans les donnees d'audit;
- aucune image de page dans le produit;
- aucune longue citation dans le KG public, les prompts, les sorties GraphRAG ou les manifests;
- les `verbatim_anchors` existants doivent rester dans un artefact interne protege ou etre remplaces par des empreintes/pointeurs, non exposes comme texte public.

## 2. Pagination, structure et completude

### 2.1 Nature de la pagination

Les PDF 3-8 reproduisent l'Introduction dans une mise en page proche du livre, p. 1-6. A partir de PDF 9, l'epreuve est recomposee: chaque page PDF contient plusieurs pages imprimees et des marqueurs verts `(p.N)`. Il n'existe donc aucune formule lineaire du type `PDF = imprime + constante`.

Carte de structure verifiee par signets, extraction page par page et rendu visuel:

| Objet imprime | Pages imprimees officielles | Pages PDF locales | Notes |
|---|---:|---:|---|
| Titre | sans folio | 1 | visible |
| Copyright | sans folio | 2 | visible |
| Introduction | 1-6 | 3-8 | continue |
| Ch. 1, contexte historique | 9-63 | 9-19 | notes recomposees en PDF 20-28 |
| Ch. 2, ecriture theologique | 64-98 | 29-36 | notes en PDF 37-41 |
| Ch. 3, liberte et creation | 101-134 | 42-49 | notes en PDF 50-53 |
| Ch. 4, christologie et volontes | 135-165 | 54-61 | notes en PDF 62-66 |
| Ch. 5, Eglise et liturgie | 166-196 | 67-73 | notes en PDF 74-77 |
| Ch. 6, nature, chute et esperance | 198-224 | 78-83 | notes en PDF 84-87 |
| Ch. 7, passion et liberte | 225-253 | 88-94 | notes en PDF 95-98 |
| Ch. 8, desir, vertu, responsabilite | 254-284 | 99-106 | notes en PDF 107-111 |
| Ch. 9, receptions | 287-328 | 112-120 | notes en PDF 121-126 |
| Epilogue | 329-334 | 127-128 | notes terminees dans PDF 128 |

Les folios intermediaires 7-8, 99-100, 197 et 285-286 correspondent aux divisions de parties ou aux transitions de l'objet imprime; leur contenu est absorbe dans la recomposition. Les pages de notes n'ont pas conserve une etiquette imprimee page par page, mais leurs suites numerotees se poursuivent jusqu'au chapitre suivant.

### 2.2 Preliminaires et end matter

| Composant de l'edition publiee | Manifestation locale | Verdict |
|---|---|---|
| Copyright | present | complet |
| Dedication | absente | manque physique confirme |
| Acknowledgments | absents | manque physique confirme |
| Liste des abreviations, p. xv-xvi | absente | manque physique confirme |
| Table des matieres imprimee | absente; signets PDF seulement | manque physique confirme |
| Introduction, neuf chapitres, Epilogue | presents | corps intellectuel continu |
| Notes de chapitres | presentes | suites visibles completes |
| Bibliographie selective | absente | manque physique confirme |
| Index | absent | manque physique confirme |

Conclusion: `scholarly_main_content_complete`, mais `physical_completeness: incomplete`. Le manifeste ne doit pas inventer une nouvelle valeur enumeree si le schema ne l'accepte pas; il peut conserver `content_completeness: full` seulement avec un champ de portee explicite et une liste `physically_missing`.

### 2.3 Pages thematiques rendues et lues

| Theme | Pages imprimees | Pages PDF | Controle |
|---|---:|---:|---|
| titre, copyright, debut et fin | sans folio, 1-6, 329-334 | 1-3, 8, 127-128 | rendu et lecture visuelle |
| mode des volontes dans la controverse | 49-53 | 17 | rendu 300 dpi et lecture visuelle |
| mouvement, logoi, providence | 110-124 | 44-47 | rendu 300 dpi et lecture visuelle |
| repetition du mouvement providentiel | 140-144 | 55 | rendu 300 dpi et lecture visuelle |
| bataille des volontes, figure 3 | 155-165 | 58-61 | rendu 300 dpi et lecture visuelle integrale |
| nature, passibilite, chute, `autexousia` | 198-224 | 78-83 | rendu 300 dpi et lecture visuelle integrale |
| Gethsemani, liberte, cout soteriologique | 230-253 | 89-94 | rendu 300 dpi et lecture visuelle integrale |
| desir, passions, figure 4, responsabilite | 254-284 | 99-106 | rendu 300 dpi et lecture visuelle integrale |
| reception nature/personne/liberte | 312-328 | 117-120 | rendu 300 dpi et lecture visuelle integrale |

La navigation a egalement parcouru l'ensemble des 128 pages et toutes les occurrences de `freedom`, `gnome`, `natural will`, `self-determination`, `self-moved`, `providence`, `evil`, `responsibility`, `choice` et `necessity`.

## 3. Inventaire atomique des claims de Blowers

Chaque claim ci-dessous est une paraphrase de l'analyse secondaire de Blowers. Les loci antiques cites dans la derniere colonne sont des leads a recoller, non des textes primaires verifies par le present audit.

| ID | Claim atomique paraphrase | Pages imprimees / PDF | Loci ou attribution a conserver |
|---|---|---|---|
| BL-01 | Les creatures rationnelles ne sont ni auto-originaires ni auto-motrices au sens metaphysique absolu; leur mouvement vers leur fin depend de l'activite divine. | 115-118 / PDF 45 | *Amb. Jo.* 7; Blowers contre l'interpretation origeniste |
| BL-02 | La liberte creaturelle reunit raison, volition et desir; elle doit etre eduquee et actualisee plutot que posee comme capacite brute. | 120-121 / PDF 46 | lecture Blowers; influence aristotelicienne attribuee |
| BL-03 | La passivite est une capacite positive a etre mue; l'agent rationnel peut neanmoins agir par desir et choix dans son actualisation. | 120-121 / PDF 46 | Aristote, *Metaph.* 1048a; *Amb. Jo.* 7 |
| BL-04 | La providence vise a harmoniser les particuliers et le tout, en unissant l'inclination volontaire au logos universel et en rendant les creatures automotrices les unes par rapport aux autres. | 121-122 et 142 / PDF 46, 55 | *Q. Thal.* 2, CCSG 7:51 |
| BL-05 | La `gnome` tardive est definie comme desir profond ou disposition portant sur ce qui depend de nous et menant au choix. | 122 / PDF 46 | *Opusc.* 1, PG 91:17C; definition secondairement reconstruite |
| BL-06 | Blowers resume la volonte gnomique comme l'experience ordinaire de deliberation et de choix des creatures rationnelles; elle est moralement ambivalente et doit etre formee. | 122-124 / PDF 46-47 | Blowers; *Amb. Jo.* 8; *Q. Thal.* 1, 21, 61 |
| BL-07 | La `gnome` conserve une valeur positive dans les ecrits precoces comme ressource de l'existence historique, meme si elle n'est pas une faculte naturelle stricte. | 123-124 / PDF 46-47 | jugement propre de Blowers, non consensus maximien direct |
| BL-08 | Dans la controverse mature, Maxime distingue les volontes naturelles du mode ou de la qualite de vouloir, rattache a l'hypostase et a l'usage. | 52, 164-165 / PDF 17, 61 | *Disp. Pyrr.*; `to pos thelein`, `tropos tes chreseos` |
| BL-09 | La volonte humaine est reconstruite comme processus physio-psychologique complet, et non comme seul jugement rationnel. | 159-162 / PDF 58-60 | *Opusc.* 1; *Disp. Pyrr.*; figure 3 de Blowers |
| BL-10 | La definition de la volonte comme puissance appetitive conforme a la nature est rapprochee de Clement et de l'`oikeiosis` stoicienne; Blowers rapporte ici une these de Sorabji sur une notion chretienne de la faculte de vouloir. | 160-161 / PDF 59-60 | Sorabji est l'auteur de la these de nouveaute; Bathrellos nuance par les appetits non rationnels |
| BL-11 | Les ecrits precoces peuvent faire agir une `gnome` vertueuse au Christ; les textes matures la refusent en la reclassant comme mode faillible incompatible avec le Christ sans peche. | 157-165 / PDF 58-61 | *Or. dom.*; *Disp. Pyrr.*; *Opusc.* 3, 6, 7, 16 |
| BL-12 | Gethsemani montre une volonte humaine naturelle reelle, differente mais non opposee a la volonte divine; la resistance a la mort appartient a l'humanite du Christ. | 156-164 / PDF 58-61 | Matt. 26:36-42; *Opusc.* 6-7; Doucet et von Balthasar doivent rester distingues |
| BL-13 | Pour Blowers, la liberte parfaite ne se reduit pas a deliberer ou choisir: elle consiste dans l'usage de l'ensemble des facultes naturelles en direction de leur fin. | 164-165 / PDF 61 | interpretation secondaire; ne prouve pas une theorie formelle de liberte d'indifference |
| BL-14 | La nature n'est pas, chez Blowers lisant Maxime, une necessite oppressante univoque; elle est aussi principe donne, mobile et ouvert a la grace. | 198-210 / PDF 78-80 | *Amb. Jo.* 31; dialogue critique avec Zizioulas |
| BL-15 | La necessite dite bienveillante exprime la permanence du logos naturel et l'activite divine; du point de vue de l'`autexousia`, elle est predisposition a la fin plutot que contrainte externe. | 209-211 / PDF 80 | Gregoire de Nysse, *Hexaemeron*; *Amb. Jo.* 31 et 7 |
| BL-16 | Blowers nomme `gnomic surrender` la remise de l'inclination interessee a la finalite naturelle et a l'activite de Dieu. | 121-122, 210-211, 265 / PDF 46, 80, 102 | terme interpretatif de Blowers; *Amb. Jo.* 7, PG 91:1076B-C |
| BL-17 | La chute d'Adam est attribuee principalement a un echec de `gnome`, egalement appele abus d'`autexousia`; la `gnome` reste toutefois moralement neutre en elle-meme. | 213-214 / PDF 81 | *Q. Thal.* 1 et 61; *Amb. Jo.* 7 |
| BL-18 | Adam transmet passion, mort et consequences historiques, non sa culpabilite personnelle; les lois postlapsaires de la nature sont dites circonstancielles, non genetiques. | 216-217 / PDF 81-82 | *Q. Thal.* 21 et 42; dialogue critique avec Larchet |
| BL-19 | L'abus de liberte reste imputable: les facultes et passions ne deviennent moralement mauvaises que par leur orientation et leur usage. | 263-270 / PDF 101-104 | *Car.* 2.16, 2.26, 2.31, etc.; figure 4 |
| BL-20 | Une passion coupable est un mouvement de l'ame contraire a la nature; le travail moral consiste aussi a convertir ou bien employer des impulsions initialement neutres. | 268-270 / PDF 103-104 | *Car.* 2.16; tradition evagrienne et stoicienne |
| BL-21 | Le bapteme donne la grace en puissance et reoriente activement le libre choix selon la `gnome`; la formation communautaire prolonge cette conversion. | 283-284 / PDF 106 | *Q. Thal.* 6, CCSG 7:69; *Myst.* 24 et 9 |
| BL-22 | La question de la restauration universelle reste ouverte et dialectique: textes de jugement, resurrection universelle, transformation du choix et esperance de salut ne se reduisent pas a un universalisme automatique. | 248-253 / PDF 93-94 | *Amb.* 65; *Exp. Ps.* 59; *Q. Thal.* 47; *Questions and Uncertainties* |
| BL-23 | Les lectures personnalistes ou theodramatiques modernes de la liberte ne doivent pas etre retroprojetees sur Maxime sans attribution. | 312-328 / PDF 117-120 | Bulgakov, Zizioulas, Yannaras, Loudovikos, von Balthasar, Jenkins |

## 4. Loci antiques et patristiques comme leads de recollation

Le PDF de Blowers est une source secondaire. La table suivante inventorie les principaux loci qu'il mobilise; elle ne certifie ni leur texte grec ni leur numerotation contre une edition critique independante.

| Theme | Loci cites par Blowers | Statut |
|---|---|---|
| mouvement naturel, providence et liberte | *Amb. Jo.* 7, PG 91:1073B-C, 1076B-D, 1084A-B, 1085D-1088A; *Q. Thal.* 2, CCSG 7:51; *Amb. Jo.* 31, PG 91:1280A | leads; aucune manifestation primaire maximienne dans le corpus |
| definition de `gnome` et processus de la volonte | *Opusc.* 1, PG 91:12C-24A, notamment 17C; *Disp. Pyrr.*, PG 91:293B-C | leads; figure 3 est une reconstruction de Blowers |
| pluralite des sens de `gnome` | *Disp. Pyrr.*, PG 91:312B-C affirme la pluralite; l'enumeration detaillee est principalement *Opusc.* 14, PG 91:151C-153A | ne pas confondre annonce et enumeration |
| `gnome` precoce du Christ | *Or. dom.*, CCSG 23:34-35; *Exp. Ps.* 59, CCSG 23:3 | leads; developpement chronologique requis |
| deux volontes, difference sans opposition | *Opusc.* 3, PG 91:48B-C; 6, 65A-68D; 7, 80C-84C; 16, 193A; *Disp. Pyrr.*, 297B-300A, 308C-D, 345D | leads; oeuvres et transmetteurs a recoller separement |
| chute gnomique et `autexousia` | *Q. Thal.* 1, CCSG 7:47; 61, CCSG 22:85-89; *Amb. Jo.* 7, PG 91:1092C-D | leads |
| culpabilite et consequences de la chute | *Q. Thal.* 21, CCSG 7:127-131; 42, CCSG 7:285-289 | leads; ne pas transformer en doctrine genetique simple |
| passion, usage et responsabilite | *Car.* 2.16, PG 90:988D-989A; 2.26, 2.31, 2.71-73, 2.78, 2.84; *Th. Oec.* 2.33 | leads |
| bapteme et libre choix | *Q. Thal.* 6, CCSG 7:69; *Myst.* 24, CCSG 69:66 | le noeud KG correspondant dispose d'une verification primaire locale distincte; Blowers n'en est pas la source primaire |
| jugement et apokatastasis | *Amb.* 65, PG 91:1392A-C; *Exp. Ps.* 59; *Q. Thal.* 47, CCSG 7:325; *Questions and Uncertainties*, loci variables | dossier contradictoire a conserver ouvert |

## 5. Comparaison avec le KG, les citations, les manifestes et le registre SOTA

### 5.1 Empreintes et inventaire courant

Empreintes globales au moment de l'audit:

| Artefact | SHA-256 |
|---|---|
| `data/kg/nodes.jsonl` | `92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817` |
| `data/kg/edges.jsonl` | `b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a` |
| `data/corpus/citations.jsonl` | `5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a` |
| manifeste acquisition | `e1a5c1bf0ed25615005c9cd3107f3be25235b535faa563e5fa847eb5e9522933` |
| manifeste scholarly sources | `c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e` |
| registre sources seed | `511a4550dd3d61c36e5fa2b85fb0e0ad66f055141ba5ee4829256b62ea2e7d46` |
| registre evidence seed | `165e13fb58e951c76b2efbdcfa17c1938166677af8f60b1d8e2fa5390d84c23c` |
| `data/kg/publications.bib` | `3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825` |

Le cluster Blowers comporte:

- 1 scholar: `scholar_blowers_paul`;
- 1 publication: `pub_blowers_2016_maximus_confessor`;
- 8 arguments secondaires `scholarly_argument_blowers_*`;
- 35 edges incidents: 1 `authored_by`, 8 `advanced_in`, 8 `created_by` et 18 `discusses`;
- 5 citations de corpus, toutes rattachees a trois arguments seulement et toutes vers Jean Damascene;
- 0 passage primaire de Maxime le Confesseur dans le corpus sous les travaux annonces.

### 5.2 Publication et scholar

#### `pub_blowers_2016_maximus_confessor` - REVISE avant publication

Exact:

- auteur, titre, OUP, 2016 et ISBN imprime;
- la monographie suit bien le developpement de la doctrine de `gnome` et la controverse monothelete;
- l'edge `authored_by -> scholar_blowers_paul` est exact.

Incorrect ou incomplet:

- `series: Oxford Early Christian Studies (OECS)` est faux; la serie est *Christian Theology in Context*;
- DOI et ISBN en ligne manquent;
- `local_pdf_path` pointe vers un ancien chemin externe au lieu de la manifestation repo avec hash;
- l'etat `citation_verified: true` ne distingue pas identite bibliographique et verification des interpretations;
- la description dit chapitre 5 pour la chute adamique, au lieu du chapitre 6;
- elle reduit la bataille des volontes au chapitre 7, alors que le chapitre 4 en donne l'expose technique et le chapitre 7 la reprise soteriologique;
- le PDF local n'est pas decrit comme corrected proof incomplet physiquement.

Le bloc BibTeX correspondant est aussi defectueux: il n'a pas de champ `author`, son `title` contient le label KG `Blowers 2016 - ...` plutot que le titre bibliographique nu, et il omet serie et DOI.

#### `scholar_blowers_paul` - REVISE metadata

OUP confirme l'affiliation et la chaire au moment de publication. Le PDF ne confirme pas l'annee de naissance ni la formule evaluative `among the leading`. La description repete la mauvaise serie OECS. Conserver les champs `needs_verification` pour les donnees biographiques externes et corriger seulement ce qui est reproduit par une autorite explicite.

### 5.3 Arguments secondaires Blowers

| ID | Verdict de lecture | Correction fail-closed |
|---|---|---|
| `scholarly_argument_blowers_natural_vs_gnomic_will` | PASS comme paraphrase secondaire | ajouter page map et `citability=discoverable_only`; les definitions grecques restent leads primaires |
| `scholarly_argument_blowers_wills_vs_mode_of_willing` | PASS comme paraphrase secondaire | distinguer `p.52` historique et `p.164` developpement doctrinal; pas de citation primaire tant que Maxime manque |
| `scholarly_argument_blowers_adamic_fall_gnomic_failure` | PASS comme paraphrase secondaire | corriger le chapitre 6; garder distinction consequence/culpabilite |
| `scholarly_argument_blowers_denial_gnomic_will_soteriological_cost` | PASS comme question critique de Blowers | ne pas convertir la question en conclusion historique sur Maxime |
| `scholarly_argument_blowers_gethsemane_dyothelite_locus` | REVISE leger | attribuer explicitement a Doucet l'analyse du conflit interne instinct/volonte; Blowers la discute et la qualifie, il ne la presente pas comme resolution incontestee |
| `scholarly_argument_blowers_will_as_natural_faculty` | REVISE | remplacer `Following Sorabji, Blowers holds` par `Blowers reports Sorabji's thesis`; la proximite avec `oikeiosis` interdit l'opposition simple a la Stoa |
| `scholarly_argument_blowers_freedom_not_reducible_to_choice` | REVISE | conserver la non-reduction au choix; retirer l'equivalence non demontree entre toute capacite de choisir autrement et la chute |
| `scholarly_argument_blowers_gnomic_surrender_freedom` | REVISE | marquer `gnomic surrender` et `benevolent necessity` comme lexique interpretatif de Blowers; retirer ou attribuer la comparaison moderne avec libertarianisme/liberte d'indifference |

Tous les huit records ont `citation_verified: true` et aucun champ `citability`; la politique runtime les rend donc citables. Or le registre les maintient a juste titre en evidence `candidate`. Tant que le source manifest, les evidence units, les droits et la revue independante ne sont pas materialises, ils doivent rester `discoverable_only`.

Les huit records manquent simultanement de `page` et de `page_range`. Leur note
`ingestion_debt_2026_08_17_schema_normalised`, lorsqu'elle affirme une copie
vers `page_range`, est donc factuellement fausse. Cinq `verified_reference`
sur huit sont coupes a 300 caracteres et ne constituent pas des references
humaines completes. La transaction doit remplacer ces chaines par pages,
manifestation, source hash, claim status et review states types.

### 5.4 Concepts et arguments maximiens affectes

Les noeuds suivants utilisent Blowers tout en presentant souvent des syntheses comme si elles etaient des propositions primaires deja recollees:

| ID | Risque |
|---|---|
| `concept_gnomic_will_gnome` | fusion des usages moraux precoces, de la definition tardive et du refus christologique mature; `citation_verified=true` sans Maxime dans le corpus |
| `concept_thelema_physikon_natural_will` | `intrinsically free because conformity to nature is what freedom is` est une synthese moderne, non univoque chez Blowers |
| `argument_maximus_natural_vs_gnomic_will` | la structure dyothelite mature est plausible, mais `principal Greek answer` et l'analogie de l'univocite depassent le PDF |
| `argument_maximus_natural_will_freedom` | le label signale deja que `intrinsically free` est une paraphrase moderne; le corps la publie pourtant comme deduction primaire |
| `argument_maximus_two_wills` | Blowers soutient la dyothelie et ses loci, mais ne remplace pas une collation de l'*Opuscula* et de la *Disputatio* |
| `person_maximus_confessor_d662` | la biographie privilegie encore la carriere de cour transmise par la Vie grecque et simplifie la chronologie de `gnome`; Blowers insiste sur l'incertitude biographique et le developpement doctrinal |
| `work_maximus_quaestiones_thalassium` | la description attribue a *Q. Thal.* 21 un dossier `eph' hemin`; le livre l'utilise ici pour passibilite/generation et consequences de la chute. Ce locus doit etre corrige sans traiter Blowers comme texte primaire. |

Travaux deja presents mais sans manifestation primaire dans le corpus:

- `work_maximus_disp_pyrrho`;
- `work_maximus_opuscula`;
- `work_maximus_ambigua_iohannem`;
- `work_maximus_quaestiones_thalassium`.

Le PDF Blowers ne doit pas etre transforme en source primaire substitutive pour ces quatre oeuvres.

### 5.5 Edges et citations

Edges exacts a conserver en principe:

- `pub_blowers_2016_maximus_confessor authored_by scholar_blowers_paul`;
- les huit `scholarly_argument_blowers_* advanced_in pub_blowers_2016_maximus_confessor`;
- les huit `created_by scholar_blowers_paul`;
- les `discusses person_maximus_confessor_d662`;
- les liens vers `argument_maximus_two_wills`, `concept_prohairesis...`, `concept_autexousion...`, `concept_original_sin` lorsque l'evidence secondaire exacte est page-pointee.

Edges a mettre en quarantaine ou a retaper:

- `scholarly_argument_blowers_will_as_natural_faculty discusses concept_voluntas_y7z8a9b0`: Blowers compare les histoires de la faculte de vouloir et rapporte Sorabji, mais ne traite pas directement le lexeme latin `voluntas` comme objet du noeud;
- `scholarly_argument_blowers_freedom_not_reducible_to_choice discusses concept_libertas_indifferentiae_4f8a9b57`: la liberte d'indifference est une comparaison moderne ajoutee par le patch, non une categorie analysee par Blowers dans ces pages;
- tout edge faisant de la serie `autexousion -> natural will -> libertas` une genealogie lineaire doit rester une lead attribuee, non un lien historique exact.

Les cinq citations de corpus actuelles pointent vers:

- Jean Damascene, *Expositio fidei* 58 (III.14), passage `c965411f-3801-46c3-a8a0-0d5c9883b23d`;
- Jean Damascene, *Expositio fidei* 36 (II.22), passage `73381bda-d2e7-4914-8340-4a1dddb786e6`.

Elles sont utiles comme testimonia posterieurs d'une tradition maximienne, mais ne prouvent ni la lecture de Blowers ni le texte exact de Maxime. Elles ne doivent pas rendre les noeuds secondaires citables. Options P0: les deplacer vers les noeuds doctrinaux primaires appropries, ou les conserver uniquement avec un statut `related_passage_non_exact`/`discoverable_only` et une note explicite de transmission indirecte.

Les cinq notes de citations sont tronquees exactement a 202 caracteres. Elles
doivent devenir des metadonnees courtes et structurees (`citation_role`,
transmetteur, locus, raison de non-equivalence), non de nouvelles chaines libres
susceptibles d'etre recoupees.

### 5.6 Manifestes et registre SOTA

#### Manifeste d'acquisition

La ligne `lit_blowers_2016_maximus` a le bon hash, la bonne taille, le bon nombre de pages PDF, l'auteur et l'annee. Elle doit corriger ou completer:

- titre complet;
- DOI, ISBN imprime et ISBN en ligne;
- manifestation locale `publisher_corrected_proof_final`, ou note equivalente sans inventer une enum non supportee;
- portee de completude savante;
- `physical_completeness: incomplete` et liste des elements absents;
- page map non lineaire et plages thematiques;
- rights statement et politique de paraphrase.

#### Scholarly source manifest

Aucune ligne Blowers n'existe. C'est le gap principal. Une future entree doit rester `kg_ingestion_status: partial`, puisque huit arguments ont ete lus et page-mappes mais que le livre entier n'a pas ete transforme en evidence claim par claim et que les primaires maximiennes manquent.

#### Registre SOTA

Etat actuel correctement prudent:

- source `src_sec_blowers_2016_maximus` avec identite `bibliography_verified`;
- acquisition `local_unregistered`;
- couverture `partial`;
- evidence unique `ev_sec_blowers_maximus_priority_pages`, `claim_status: candidate`;
- issue `issue_secondary_archive_manifest_gap_20260824` ouverte;
- wave `wave_02_wire_existing_scholarship` planifiee;
- aucune verification independante Blowers inventee.

Defauts a corriger:

- l'evidence unique fusionne la plage 121-246 tout en precisant dans une note que les clusters ne sont pas continus;
- les `kg_targets` se limitent a la publication et a `work_maximus_ambigua_iohannem`, omettant les huit arguments et les autres travaux cites;
- le registre omet p. 52, 115-120, 248-253, 263-284 et 312-328;
- la page map reste `provisional` malgre le controle visuel de ce rapport;
- le source record ne distingue pas oeuvre et corrected-proof manifestation.
- le resume de `issue_secondary_archive_manifest_gap_20260824` conserve un
  comptage stale de six lignes scholarly manifest; l'etat courant en contient
  dix. Recalculer le nombre ou supprimer ce detail volatil.

## 6. Erreurs, contradictions et surinterpretations prioritaires

### P0 - bloque la citabilite publique

1. **Serie bibliographique fausse.** `Oxford Early Christian Studies` doit devenir `Christian Theology in Context`.
2. **Manifestation non enregistree.** Le hash existe dans le manifeste d'acquisition, mais pas dans le scholarly source manifest; le registre reste donc justement `local_unregistered`.
3. **Citabilite runtime trop permissive.** Les records Blowers sont `citation_verified=true` sans `citability`, donc citable par defaut malgre evidence candidate, droits stricts et absence de revue independante.
4. **Chapitres faux.** Chute adamique = chapitre 6, non 5. Expose technique des volontes = chapitre 4, repris soteriologiquement au chapitre 7.
5. **Source secondaire et primaire fusionnees.** Les cinq citations Jean Damascene ne sont pas des citations de Blowers ni des textes exacts de Maxime.
6. **BibTeX incomplet.** Auteur absent, titre pollue par le label KG, serie et DOI absents.
7. **Provenance tronquee et pages absentes.** Cinq `verified_reference`, les
   cinq notes de citations, la personne Maxime et plusieurs notes de
   concept/work sont coupees; les huit arguments n'ont aucun champ de page
   reel.
8. **Locus de travail faux.** `work_maximus_quaestiones_thalassium` decrit
   *Q. Thal.* 21 comme dossier `eph' hemin`, contrairement a son usage dans le
   PDF audite.
9. **Issue stale.** Le comptage de six lignes scholarly manifest n'est plus
   vrai (dix lignes courantes).

### P1 - surinterpretations semantiques

1. La these d'une faculte de volonte `uniquely Christian` est celle de Sorabji rapportee par Blowers, non une conclusion autonome et non contestee de Blowers.
2. `Natural will intrinsically free` est une synthese moderne utile, mais trop forte comme formulation primaire neutre.
3. La non-reduction de la liberte au choix ne permet pas d'identifier toute capacite d'alternative a la chute ni de faire de Maxime un theoricien explicite anti-libertarien.
4. `Gnomic surrender` est le lexique interpretatif de Blowers; il ne doit pas etre cite comme terme technique maximien sans recollation.
5. L'analyse du conflit interne a Gethsemani doit conserver l'attribution a Doucet et les reserves de Blowers.
6. La formule de `terminal pivot of the ancient autexousion debate` dans le patch d'acquisition est une these de cadrage EleutherIA, non un claim etabli par ce livre.
7. Les lectures de Zizioulas, Yannaras, von Balthasar, Schwager, Larchet et Farrell sont des receptions modernes contradictoires, non des formulations de Maxime.

### P2 - gaps de couverture

1. Aucun texte primaire maximien n'est ingere.
2. Le dossier responsabilite/passion/usage p. 263-284 manque au registre.
3. Le dossier apokatastasis p. 248-253 manque au registre.
4. La reception moderne p. 312-328, indispensable pour empecher les retroprojections, manque au registre.
5. Le fichier local manque des preliminaires, de la bibliographie selective et de l'index.

## 7. Plan P0 transactionnel et fail-closed

Ce plan n'autorise aucun write; il definit une future transaction a soumettre a revue independante.

### Etape A - manifestation et bibliographie

1. Figer Snapshot-A des fichiers touches et des 20 records listes dans cet audit.
2. Corriger seulement le bloc Blowers dans `scripts/build_literature_acquisition_manifest.py` et regenerer exactement `data/literature_acquisition/manifest.jsonl`.
3. Ajouter titre complet, DOI, ISBN imprime/en ligne, corrected-proof status, droits, page map par plages, completude savante bornee et incompletude physique.
4. Ajouter une ligne schema-valide a `data/scholarly_sources/manifest.jsonl`, statut `partial`, portee exacte et politique `paraphrase_only`.
5. Corriger le noeud publication: serie *Christian Theology in Context*, chapitres 3/4/6/7/8 exacts, DOI, ISBNs et manifestation locale hash-pointee.
6. Ajouter l'auteur bibliographique dans les metadonnees canoniques puis regenerer le bloc BibTeX et le rapport compagnon avec l'exporteur, sans correction manuelle divergente.

### Etape B - evidence secondaire atomique

Scinder `ev_sec_blowers_maximus_priority_pages` en unites au moins egales aux dossiers suivants:

- identite/droits/completude;
- p. 115-124, mouvement, providence et structure de la liberte;
- p. 121-123, volonte naturelle et `gnome`;
- p. 52 et 156-165, volontes et mode de vouloir;
- p. 198-217, nature, necessite, `autexousia`, chute et responsabilite;
- p. 225-246, Gethsemani et cout soteriologique;
- p. 248-253, apokatastasis disputee;
- p. 254-284, passions, usage, vertu et libre choix;
- p. 312-328, receptions modernes a ne pas retroprojeter.

Chaque unite doit porter pages imprimees, pages PDF, claim paraphrase, KG targets exacts, `attestation=reported_interpretation`, absence de quote publique et requirement de primary recollation quand un locus antique est invoque.

### Etape C - KG et politique de citation

1. Corriger les huit arguments secondaires selon le tableau 5.3, sans creer de nouveaux noeuds doctrinaux. Ajouter a chacun un `page_range` reel et une carte imprime/PDF; supprimer la fausse note de normalisation et remplacer toute reference tronquee par une provenance typee et complete.
2. Mettre `metadata.citability=discoverable_only` sur la publication, le scholar et les huit arguments tant que l'issue de provenance et la revue independante restent ouvertes.
3. Remplacer les longues citations et `verbatim_anchors` runtime par paraphrases et pointeurs internes; conserver les before-images en quarantaine transactionnelle.
4. Conserver les edges bibliographiques exacts; mettre en quarantaine les mappings `voluntas` et `libertas indifferentiae` comme comparaisons modernes non exactes.
5. Reparer uniquement la provenance tronquee de
   `concept_gnomic_will_gnome` (note coupee) et
   `person_maximus_confessor_d662` (`verified_reference` coupe a 300), sans
   reecrire leur doctrine/biographie au-dela de ce que les autorites etablissent.
   Pour `concept_thelema_physikon_natural_will`,
   `argument_maximus_natural_vs_gnomic_will`,
   `argument_maximus_natural_will_freedom` et
   `argument_maximus_two_wills`, ouvrir seulement des issues ciblees sauf
   nouveau mandat de recollation primaire independamment revu.
6. Corriger chirurgicalement `work_maximus_quaestiones_thalassium`: retirer
   l'attribution de *Q. Thal.* 21 au dossier `eph' hemin`, conserver son role
   exact de lead sur passibilite/generation et consequences de la chute, et
   ouvrir la recollation primaire correspondante.
7. Les cinq citations de Jean Damascene doivent etre relues comme testimonia indirects, jamais comme preuve de lecture de Blowers; remplacer leurs notes tronquees par des champs structures.
8. Mettre a jour l'issue de manifest sans figer l'ancien compte de six lorsque
   le manifeste courant en contient dix.

### Etape D - primaires et ingestion ulterieure

1. Ne creer aucun passage de Maxime depuis le PDF Blowers.
2. Acquerir ou pointer des editions autorisees des *Ambigua*, *Opuscula*, *Disputatio cum Pyrrho*, *Quaestiones ad Thalassium*, *Capita de caritate*, *Oratio dominica* et *Expositio Psalmi 59*.
3. Recoler chaque locus grec, auteur, oeuvre et pagination critique independamment.
4. Distinguer le Maxime precoce, les textes de transition et la phase anti-monothelete mature.
5. Reviser alors seulement `citation_verified` et la citabilite des noeuds doctrinaux.

### Etape E - transaction, tests et revue

La future implementation doit fournir:

- before hashes et after hashes canoniques pour chaque record touche;
- exact changed-record set et exact output path set;
- immutabilite byte-exacte de tout noeud/edge/citation hors set;
- snapshot, journal durable, fsync, quarantaine, rollback et recovery apres crash;
- idempotence premier write / repeat write / dry-run deja applique;
- validation du schema du registre sans nouvelle erreur;
- parite builder-manifest et scholarly manifest;
- export BibTeX/reporte reproductible;
- gates registry, manifest, KG, citations, rights et work-child;
- test explicite qu'aucun corpus passage n'est cree;
- review independante et adversariale reelles avant tout apply.

Touched set minimal obligatoire, a figer exactement dans le preview; toute
extension exige un diff et une revue separes:

- `scripts/build_literature_acquisition_manifest.py`;
- `data/literature_acquisition/manifest.jsonl`;
- `data/scholarly_sources/manifest.jsonl`;
- source/evidence/issues/wave/verifications du registre SOTA;
- `data/kg/nodes.jsonl`: publication, scholar, huit arguments,
  `work_maximus_quaestiones_thalassium`, `concept_gnomic_will_gnome` et
  `person_maximus_confessor_d662` (13 records minimum); les autres
  concepts/personnes recoivent seulement des issues sauf nouveau mandat
  independamment revu;
- `data/kg/edges.jsonl`: uniquement les mappings `voluntas` et
  `libertas_indifferentiae` si le preview en fige les IDs exacts;
- `data/corpus/citations.jsonl`: exactement les cinq routes Jean Damascene pour
  retypage ou quarantaine, sans creation de passage;
- `data/kg/publications.bib` et `data/kg/publications_bibtex_report.json`;
- applier, tests et artefacts d'audit Blowers.

`data/corpus/passages.jsonl` et le corpus textuel restent hors scope jusqu'a recollation primaire.

## 8. Etat final de l'audit

- PDF lu sur l'ensemble de sa structure de 128 pages, avec recherche exhaustive des themes demandes.
- Pages decisives rendues et verifiees visuellement a 300 dpi.
- Les 180 fichiers temporaires d'extraction et de rendu ont ete retires du workspace et places dans la Corbeille.
- Identite intellectuelle, edition, impression, DOI, ISBNs, manifestation et droits distingues.
- Carte imprime/PDF reconstruite par chapitres et clusters prioritaires.
- Corps savant principal juge continu; objet physique juge incomplet.
- 23 claims secondaires atomises et 9 familles de loci enregistrees comme leads seulement.
- 20 noeuds directement affectes inventories, 35 edges et 5 citations controles.
- Registre, manifests, BibTeX et politique runtime compares.
- Aucun write KG/corpus/registre/manifeste/patch/audit JSON effectue.
