# Audit savant du PDF de Long et Sedley, *The Hellenistic Philosophers*, volume 2

Date de l'audit: 2026-08-24  
Portee: lecture savante en ecriture documentaire seulement; aucune modification du KG, du corpus, des registres, des manifestes, des patches ou des donnees d'audit.  
Source visuelle faisant autorite: `data/literature_acquisition/long_sedley_1987_hellenistic_philosophers_vol2.pdf`.  
Convention: `p.` designe la pagination imprimee; `PDF` designe la page du fichier comptee a partir de 1. `LS 20E`, par exemple, designe l'unite editoriale de Long et Sedley, non une oeuvre antique autonome.

## Verdict fail-closed

L'identite intellectuelle est certaine: A. A. Long et D. N. Sedley, *The Hellenistic Philosophers*, volume 2, *Greek and Latin texts with notes and bibliography*, Cambridge University Press. Le fichier n'est toutefois pas le fac-simile d'un exemplaire de la premiere impression de 1987. La page de copyright visible enumere une premiere publication en 1987, une reimpression en 1988, une premiere edition paperback en 1989, puis des reimpressions en 1992, 1995 et 1998. La manifestation scannee est donc l'impression de 1998 ou, au minimum, une impression non anterieure a 1998 reproduisant cette ligne d'impression. La couverture absente ne permet pas de determiner la reliure.

Le contenu intellectuel allant de la page de titre a la fin de la bibliographie est continu: 520 pages PDF, une image raster par page, corps imprime 1-512 sans lacune detectee, table des matieres complete et bibliographie terminee a p. 512. La completude physique de l'exemplaire n'est pas prouvee. Le scan commence a la page de titre et omet la couverture ainsi que, tres probablement, le faux-titre et son verso correspondant aux preliminaires i-ii. La valeur `content_completeness: full` du manifeste est donc acceptable seulement au sens de contenu savant principal, non au sens d'une reproduction integrale de l'objet imprime.

Le volume 2 se declare explicitement auxiliaire du volume 1 et non concu pour etre lu seul. Le volume 1 porte les traductions et les commentaires philosophiques suivis; le volume 2 porte les textes grecs et latins, des notes textuelles et contextuelles, un apparat selectif et la bibliographie. Toute proposition philosophique attribuee a Long et Sedley doit conserver cette frontiere. Le PDF audite ne peut pas, a lui seul, verifier une assertion dont la reference declaree est le commentaire du volume 1.

Trois risques substantiels sont confirmes:

1. Le volume 2 ne soutient pas directement l'assertion selon laquelle Epicure aurait ete le premier penseur antique a poser explicitement la question moderne du libre arbitre. A p. 489, Long et Sedley renvoient leur propre analyse a une etude de Sedley sur la refutation epicurienne du determinisme, puis renvoient separement a Huby pour l'importance historique d'Epicure. La priorite historique reste une these secondaire a verifier dans le volume 1 et chez Huby.
2. Le clinamen ne doit pas etre modele comme cause suffisante, cause directe necessaire de chaque volition, ni explication complete de l'action. La note de LS 20F a p. 111 le limite au plus a une condition necessaire de la volition libre. La note de LS 20E a p. 110 dissocie en outre la doctrine expresse d'Epicure des deductions de ses critiques et fait dependre une lecture causale forte de l'interpretation non reductionniste developpee dans le volume 1.
3. Les textes stoiciens ne livrent pas un compatibilisme univoque. LS 62C et 62D offrent la distinction entre causes externes et constitution interne de l'agent, mais Cicero formule une defense qualifiee et Aulu-Gelle transmet une construction chrysippeenne. LS 62G-H sont des reconstructions critiques d'Alexandre. LS 62K appartient a Epictete et a une phase plus tardive. Il faut donc separer doctrine attribuee, transmetteur, polemique et reconstruction moderne.

## 1. Integrite, identite et qualite du scan

### 1.1 Controles techniques

| Propriete | Valeur controlee |
|---|---|
| Chemin | `data/literature_acquisition/long_sedley_1987_hellenistic_philosophers_vol2.pdf` |
| SHA-256 | `af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8` |
| Taille | 24,371,131 octets |
| Pages | 520 |
| Format | PDF 1.6, 263.08 x 378.4 points, rotation 0, non chiffre |
| Producteur | ABBYY FineReader 9.0 Professional Edition |
| Date technique | creation 2009-04-22; modification 2009-04-23; sans valeur bibliographique |
| Nature | scan bitonal avec couche OCR; document non balise |
| Images | exactement 520 images pour 520 pages, generalement 450 ppi, compression CCITT |
| Controle syntaxique | `qpdf --check`: aucun defaut de syntaxe ni d'encodage de flux detecte |
| Formulaire | un AcroForm est declare; aucun JavaScript; aucun effet sur la lecture |

La couche OCR a servi uniquement a rechercher les titres, les noms et les renvois. Elle deforme regulierement le grec, les chiffres, les sigles et les espacements. Les decisions sur l'identite, les folios, les limites de section, les lectures sensibles et les notes reposent sur les pages rendues du scan.

### 1.2 Identite bibliographique visible

Les pages de titre et de copyright etablissent visuellement:

- auteurs: A. A. Long et D. N. Sedley;
- titre d'ensemble: *The Hellenistic Philosophers*;
- volume: 2;
- sous-titre: *Greek and Latin texts with notes and bibliography*;
- editeur: Cambridge University Press;
- copyright: Cambridge University Press, 1987;
- histoire d'impression: premiere publication 1987; reimpression 1988; premiere edition paperback 1989; reimpressions 1992, 1995 et 1998;
- ISBN cartonne: `0-521-25562-7`;
- ISBN paperback: `0-521-27557-1`.

Formulation bibliographique minimale autorisee pour le fichier local: `Long, A. A., and D. N. Sedley. The Hellenistic Philosophers. Vol. 2, Greek and Latin Texts with Notes and Bibliography. Cambridge: Cambridge University Press, first published 1987; local scan of the 1998 reprint or a later unchanged impression.` La reliure doit rester `indeterminee`.

Il faut distinguer trois niveaux:

| Niveau | Identite |
|---|---|
| Oeuvre abstraite | *The Hellenistic Philosophers*, ensemble en deux volumes, 1987 |
| Volume intellectuel | volume 2, textes grecs et latins, notes et bibliographie |
| Manifestation locale | scan d'une impression portant la ligne de 1998, sans couverture, produit par ABBYY en 2009 |

## 2. Pagination, appareils et completude

### 2.1 Carte imprimee vers PDF

| PDF | Fonction ou folio visible | Statut |
|---:|---|---|
| 1 | page de titre, folio non imprime | visible; vraisemblablement p. iii |
| 2 | copyright et donnees CIP, folio non imprime | visible; vraisemblablement p. iv |
| 3-5 | table des matieres, p. v-vii | visible et continue |
| 6 | page blanche correspondant a p. viii | blanc attendu |
| 7-8 | note introductive, p. ix-x | visible et continue |
| 9-520 | p. 1-512 | regle continue `PDF = p. imprimee + 8` |

La page de titre venant directement en PDF 1 alors que la table commence a p. v indique vraisemblablement l'absence des preliminaires i-ii. Cette inférence ne permet pas de reconstruire leur contenu exact. Elle interdit seulement de qualifier le fichier de reproduction materiellement exhaustive.

### 2.2 Table, bibliographie et index

- Table des matieres: PDF 3-5, p. v-vii. Elle annonce 72 sections et toutes leurs pages de debut.
- Bibliographie: PDF 484-520, p. 476-512. Limites visibles: General p. 476; Early Pyrrhonism p. 479; Epicureanism p. 480; Stoicism p. 491; The Academics p. 510; The Pyrrhonist revival p. 511; fin p. 512.
- Index: aucun index n'est present dans le volume 2. La note introductive indique que l'Index of sources est annexe au volume 1. L'information CIP selon laquelle l'ensemble contient des index ne doit pas etre transformee en affirmation d'un index propre au volume 2.

Un balayage visuel des 520 miniatures n'a revele aucun blanc inattendu apres PDF 6 ni aucune rupture grossiere du corps. Aucun raster rendu n'est un doublon binaire exact d'un autre. Ce controle exclut les omissions evidentes et les duplications exactes, mais il ne remplace pas une collation bibliographique feuille a feuille contre un exemplaire physique independant.

### 2.3 Limites des sections prioritaires

| Section | Pages imprimees completes | Pages PDF completes | Observation |
|---|---:|---:|---|
| 20, *Free will* | 104-113 | 112-121 | debut et fin nets |
| 55, *Causation and fate* | 332-341 | 340-349 | LS 55S se termine en haut de p. 341 avant LS 56 |
| 62, *Moral responsibility* | 382-389 | 390-397 | LS 62K se termine en haut de p. 389 avant LS 63 |

La plage de registre `332-388` ne couvre donc ni la fin de LS 55 a p. 341 comme unite autonome, ni la fin de LS 62K a p. 389; elle englobe en revanche les sections 56-61 qui ne font pas partie de ces deux unites.

## 3. Fonction exacte du volume 2

La note introductive, p. ix-x, impose les distinctions suivantes:

- le volume 2 est strictement auxiliaire aux traductions et commentaires du volume 1;
- son objet principal est de fournir les originaux des textes traduits dans le volume 1;
- certains extraits sont plus longs que dans le volume 1; les ajouts sont signales typographiquement;
- les notes ne constituent pas un commentaire systematique ou exhaustif;
- elles servent aux renvois, au contexte, aux textes paralleles et aux points obscurs ou controverses, notamment pour justifier les traductions et interpretations du volume 1;
- sauf rares exceptions, Long et Sedley n'ont pas recolle les manuscrits originaux et reposent sur des editions standard listees dans l'Index of sources du volume 1;
- l'apparat est selectif et vise surtout les lectures qui affectent l'interpretation philosophique.

Consequences pour EleutherIA:

1. Le volume 2 peut attester le choix d'un texte grec ou latin par Long et Sedley, leurs conjectures, leurs notes et leur organisation LS.
2. Il ne doit pas etre cite comme s'il contenait les traductions anglaises du volume 1.
3. Il ne suffit pas a transformer un locus antique imprime en source primaire verifiee. Les textes papyrologiques, les temoins hostiles et les traductions medievales demandent une nouvelle collation dans leurs editions ou supports propres.
4. Une page du volume 1 et une page du volume 2 portant la meme section LS ne sont pas interchangeables.

## 4. Inventaire de lecture visuelle

| Ensemble | Pages imprimees | Pages PDF | Traitement |
|---|---:|---:|---|
| Titre, copyright, table, note introductive | titre-x | 1-8 | lecture visuelle integrale |
| Section 20 | 104-113 | 112-121 | deux passes visuelles completes, page par page |
| Section 55 | 332-341 | 340-349 | deux passes visuelles completes, page par page |
| Section 62 | 382-389 | 390-397 | deux passes visuelles completes, page par page |
| Renvoi 33I, impulsion et assentiment | 200 | 208 | lecture visuelle ciblee |
| Renvoi 38G-H, bivalence, cause et modalite | 236-237 | 244-245 | lecture visuelle ciblee |
| Renvoi 67M, definition stoicienne de la liberte | 426 | 434 | lecture visuelle ciblee |
| Renvoi 70G, Carneade et causalite antecedente | 456-457 | 464-465 | lecture visuelle ciblee |
| Bibliographie de LS 20 | 489 | 497 | lecture visuelle complete de la page |
| Bibliographie de LS 55 et LS 62 | 505, 508 | 513, 516 | lecture visuelle complete des pages |
| Limites de la bibliographie | 476, 479, 480, 491, 510-512 | 484, 487, 488, 499, 518-520 | controle visuel |
| Ensemble du fichier | toutes | 1-520 | sweep visuel des miniatures pour ruptures et blancs |

Il n'existe pas d'index dans ce volume a parcourir. Les renvois ci-dessus ont ete selectionnes a partir des renvois internes des sections prioritaires et de la bibliographie thematique.

## 5. Carte exacte des temoins et loci LS

Les loci antiques de cette section sont des pistes de recollation. Le present audit verifie leur presence et leur etiquette dans Long et Sedley, non leur texte primaire contre une edition critique independante.

### 5.1 LS 20

| Unite | Auteur ou transmetteur affiche | Locus affiche | Pages imprimees de l'unite et de ses notes |
|---|---|---|---:|
| 20A | Epicure, lettre transmise dans la tradition de Diogene Laerce | *Ep. Men.* 133-134 | 104 |
| 20B | Epicure, *On Nature*, papyrus d'Herculanum | livre incertain, 34.21-22 | 104-105 |
| 20C | Epicure, *On Nature*, papyrus d'Herculanum | livre incertain, 34.26-30 | 105-108 |
| 20D | Epicure | *Vatican Saying* 40 | 108 |
| 20E | Ciceron transmettant Epicure, Carneade et Chrysippe | *De fato* 21-25 | 108-110 |
| 20F | Lucrece | *De rerum natura* 2.251-293 | 110-112 |
| 20G | Diogene d'Oenoanda | 32.1.14-3.14 | 112 |
| 20H | Ciceron | *De fato* 37 | 112-113 |
| 20I | Ciceron | *Academica* 2.97 | 113 |
| 20j | Epicure, *On Nature*, papyrus d'Herculanum | livre incertain, 34.25.21-34 | 113 |

Pour 20B, 20C et 20j, Long et Sedley donnent comme temoins PHerc. 697, 1056 ou 1191 et les apographes d'Oxford et de Naples; ils precisent que les lectures proviennent de Sedley [260]. Les lacunes, supplements et lectures incertaines interdisent toute extraction non qualifiee.

Numerotation parallele affichee: 20I porte `Usener 376`. Les autres unites de LS 20 n'affichent pas de numero SVF dans leur titre. Cette absence ne signifie pas absence de paralleles; elle decrit seulement l'etiquette imprimee.

### 5.2 LS 55

| Unite | Transmetteur affiche | Locus affiche | Pages imprimees |
|---|---|---|---:|
| 55A | Stobee, attribuant des theses a Zenon et Chrysippe | 1.138.14-139.4 | 332-333 |
| 55B | Sextus Empiricus | *M.* 9.211 | 333 |
| 55C | Clement d'Alexandrie | *Strom.* 8.9.26.3-4 | 333-334 |
| 55D | Clement d'Alexandrie | *Strom.* 8.9.30.1-3 | 334 |
| 55E | Seneque | *Ep.* 65.2 | 334 |
| 55F | Galien, conserve en arabe et en latin medieval | *Caus. cont.* 1.1-2.4 | 334-336 |
| 55G | Aetius | 1.11.5 | 336 |
| 55H | Galien | *Syn. puls.* 9.458.8-14 | 336 |
| 55I | Clement d'Alexandrie | *Strom.* 8.9.33.1-9 | 336-337 |
| 55J | Aetius | 1.28.4 | 337 |
| 55K | Aulu-Gelle | 7.2.3 | 337 |
| 55L | Ciceron | *De divinatione* 1.125-126 | 337 |
| 55M | Stobee | 1.79.1-12 | 337-338 |
| 55N | Alexandre d'Aphrodise | *De fato* 191.30-192.28 | 338-339 |
| 55O | Ciceron | *De divinatione* 1.127 | 339 |
| 55P | Diogenien via Eusebe | *Praeparatio evangelica* 4.3.1 | 339 |
| 55Q | Ciceron | *De fato* 7-8 | 339-340 |
| 55R | Plutarque | *De Stoicorum repugnantiis* 1056B-C | 340 |
| 55S | Ciceron | *De fato* 28-30 | 340-341 |

LS 55F demande une prudence supplementaire: l'oeuvre de Galien n'est conservee qu'en traductions arabe et latine; le volume 2 imprime le latin medieval, tandis que la traduction du volume 1 est adaptee de l'arabe. Une manifestation grecque directe ne doit pas etre inventee.

Numerotation SVF affichee, non verifiee independamment ici: `55A = SVF I.89 et II.336`; `55B = II.341`; `55D = II.349`; `55G = II.340`; `55H = II.356`; `55I = II.351`; `55J = II.917`; `55K = II.1000, part`; `55L = II.921`; `55M = II.913, part`; `55N = II.945`; `55O = II.944`; `55P = II.939, part`; `55R = II.997, part`.

### 5.3 LS 62

| Unite | Auteur ou transmetteur affiche | Locus affiche | Pages imprimees |
|---|---|---|---:|
| 62A | Hippolyte | *Haer.* 1.21 | 382 |
| 62B | Cleanthe via Epictete | *Enchiridion* 53 | 383 |
| 62C | Ciceron | *De fato* 39-43 | 383-384 |
| 62D | Aulu-Gelle | 7.2.6-13 | 384-385 |
| 62E | Diogene Laerce | 7.23 | 385 |
| 62F | Diogenien via Eusebe | *Praeparatio evangelica* 6.8.25-29 | 385-386 |
| 62G | Alexandre d'Aphrodise | *De fato* 181.13-182.20 | 386-387 |
| 62H | Alexandre d'Aphrodise | *De fato* 185.7-11 | 387 |
| 62I | Alexandre d'Aphrodise | *De fato* 205.24-206.2 | 387-388 |
| 62J | Alexandre d'Aphrodise | *De fato* 207.5-21 | 388 |
| 62K | Epictete | *Discourses* 1.1.7-12 | 388-389 |

Numerotation SVF affichee, non verifiee independamment ici: `62A = SVF II.975`; `62B = I.527`; `62C = II.974`; `62D = II.1000, part`; `62F = II.998`; `62G = II.979`; `62H = II.982`; `62I = II.1002`; `62J = II.1003`.

## 6. Claims atomiques, paraphrases seulement

Chaque claim ci-dessous decrit ce que le volume 2 imprime ou ce que Long et Sedley y proposent. Aucun claim ne constitue une verification primaire independante du locus antique.

### 6.1 Epicure, action et clinamen

| ID | Claim atomique | Preuve imprimee / PDF | Qualification |
|---|---|---|---|
| LS2-E01 | 20A oppose necessite, hasard et ce qui depend de l'agent; l'imputation morale accompagne la troisieme categorie. | 104 / PDF 112 | texte d'Epicure transmis, lecture Long-Sedley |
| LS2-E02 | 20B et 20C attribuent au developpement de l'individu une causalite qui n'est pas reductible a sa constitution atomique initiale ni aux seules influences externes. | 104-108 / PDF 112-116 | papyrus tres lacunaire; plusieurs supplements et interpretations incertains |
| LS2-E03 | 20C et 20D opposent au deterministe sa propre pratique d'admonester, de blamer ou de soutenir qu'il raisonne correctement. | 106-108 / PDF 114-116 | argument de retournement; ne prouve pas a lui seul une metaphysique complete de l'action |
| LS2-E04 | La note a 20C relie la prise d'attitudes critiques envers autrui a la conception de soi comme responsable. | 107 / PDF 115 | commentaire Long-Sedley, non proposition litterale du papyrus |
| LS2-E05 | 20E transmet une solution carneadeenne selon laquelle le mouvement volontaire peut ne pas avoir de cause externe antecedente sans etre absolument sans cause. | 108-110 / PDF 116-118 | Ciceron et Carneade sont des transmetteurs dialectiques, non Epicure parlant directement |
| LS2-E06 | Long et Sedley distinguent l'absence de cause physique du clinamen et la causalite attribuee au soi ou a la volition dans leur lecture non reductionniste. | 110 / PDF 118 | interpretation declaree dependante du volume 1 |
| LS2-E07 | Long et Sedley jugent que le temoignage carneadeen affaiblit fortement l'idee selon laquelle le clinamen constituerait l'analyse meme de la volition. | 110 / PDF 118 | jugement moderne des editeurs |
| LS2-E08 | La note a 20F limite le clinamen au plus a une condition necessaire de la volition libre; elle n'en fait ni une condition suffisante ni une explication complete. | 111 / PDF 119 | point de securite principal pour le KG |
| LS2-E09 | Une autre note admet seulement que le langage de Lucrece peut suggerer une implication directe du clinamen dans chaque nouvelle action autonome. | 111 / PDF 119 | possibilite interpretative, non conclusion certaine |
| LS2-E10 | 20G relie le mouvement atomique libre a la survie de l'admonestation et du blame. | 112 / PDF 120 | inscription fragmentaire; apparat complet renvoye a Chilton |
| LS2-E11 | 20H et 20I traitent la bivalence des futurs; ils appartiennent au dossier du determinisme logique et ne doivent pas etre fondus avec la causalite physique du clinamen. | 112-113 / PDF 120-121 | rapports ciceroniens |
| LS2-E12 | 20j oppose les animaux traites comme automates et ceux auxquels une correction ou un blame peut etre adresse. | 113 / PDF 121 | papyrus fragmentaire; extension au-dela des humains incertaine |

### 6.2 Causalite et destin stoiciens

| ID | Claim atomique | Preuve imprimee / PDF | Qualification |
|---|---|---|---|
| LS2-S01 | 55A-C presentent une cause corporelle produisant, dans le vocabulaire stoicien, un effet incorporel exprime comme predicat. | 332-334 / PDF 340-342 | doxographie; Clement n'est pas lui-meme un Stoicien |
| LS2-S02 | 55D-I distinguent causes completes ou sustentatrices, preliminaires, auxiliaires et conjointes. | 334-337 / PDF 342-345 | terminologie variable selon transmetteurs et contexte medical |
| LS2-S03 | 55J-M decrivent le destin comme ordre, enchainement causal, raison cosmique, nature ou necessite. | 337-338 / PDF 345-346 | formulations doxographiques non uniformes |
| LS2-S04 | 55N expose une chaine causale sans evenement sans cause et l'identification du destin a l'ordre naturel et divin. | 338-339 / PDF 346-347 | Alexandre est un critique peripateticien; ne pas effacer sa position polemique |
| LS2-S05 | La note a 55N rapporte une reponse chrysippeenne selon laquelle un choix apparemment spontane demeure cause meme si sa cause echappe a la conscience. | 338-339 / PDF 346-347 | reconstruction a partir de Plutarque; adversaires possiblement academiciens, non surement epicuriens |
| LS2-S06 | 55O-P lient la doctrine du destin a la possibilite de la divination, puis signalent le risque de circularite. | 339 / PDF 347 | argument et critique transmis par Ciceron et Diogenien |
| LS2-S07 | 55R formule une objection: si les impressions ne sont que des causes preliminaires mais que le destin est irresistible, la distinction ne suffit pas manifestement a eviter la contrainte. | 340 / PDF 348 | objection de Plutarque, non aveu de Chrysippe |
| LS2-S08 | 55S repond au Lazy Argument en rendant co-destines l'issue et les actions necessaires a cette issue. | 340-341 / PDF 348-349 | solution chrysippeenne transmise par Ciceron |

### 6.3 Responsabilite, `eph' hemin` et cylindre

| ID | Claim atomique | Preuve imprimee / PDF | Qualification |
|---|---|---|---|
| LS2-R01 | 62A-B distinguent suivre volontairement le destin et y etre entraine, sans proposer une sortie hors du destin. | 382-383 / PDF 390-391 | Hippolyte et Cleanthe via Epictete; chronologies distinctes |
| LS2-R02 | 62C distingue causes antecedente-proche et complete-principale afin de maintenir que l'impression declenche l'assentiment sans determiner a elle seule son mode. | 383-384 / PDF 391-392 | Long et Sedley qualifient le passage de defense limitee de Chrysippe; Ciceron en souligne les difficultes |
| LS2-R03 | Dans l'analogie du cylindre, la poussee externe initie le mouvement et la forme propre explique la maniere de rouler. | 384 / PDF 392 | analogie de causalite conjointe; aucune capacite alternative n'est etablie |
| LS2-R04 | 62D attribue l'action a la constitution et aux dispositions de l'agent tout en maintenant l'ordre necessaire du destin. | 384-385 / PDF 392-393 | Aulu-Gelle transmet Chrysippe; ne pas transformer la nature de l'agent en cause non causee |
| LS2-R05 | 62D refuse que le destin soit une excuse automatique pour la faute. | 385 / PDF 393 | preservation de l'imputation, non preuve independante de desert moral |
| LS2-R06 | 62F presente comme co-destinees les actions humaines requises et leurs issues; l'effort n'est donc pas rendu inutile. | 385-386 / PDF 393-394 | Diogenien est un adversaire rapportant la reponse chrysippeenne |
| LS2-R07 | 62G reconstruit la position stoicienne: l'action est dite par nous parce qu'elle passe par la nature, l'impulsion et l'assentiment de l'agent, bien que les causes externes et le resultat appartiennent a la chaine necessaire. | 386-387 / PDF 394-395 | reconstruction hostile d'Alexandre |
| LS2-R08 | 62H objecte que cette reconstruction ne sauvegarde pas la capacite d'accomplir l'oppose dans les memes circonstances. | 387 / PDF 395 | critique d'Alexandre; ne pas l'attribuer aux Stoiciens |
| LS2-R09 | 62I-J soutiennent que fautes, reussites, louange, blame, honneur et correction restent integres a l'ordre du destin. | 387-388 / PDF 395-396 | arguments stoiciens rapportes par Alexandre; chaine normative a atomiser |
| LS2-R10 | 62K reserve ce qui depend de nous au bon usage des impressions et exclut le corps, les possessions et les contraintes externes. | 388-389 / PDF 396-397 | Epictete, couche imperiale plus tardive; ne pas retroprojeter sans preuve sur Chrysippe |

### 6.4 Renvois internes pertinents

| Unite | Claim de routage | Pages imprimees / PDF | Qualification |
|---|---|---|---|
| 33I | Toute impulsion pratique est analysee comme assentiment, mais tout assentiment n'est pas une impulsion. | 200 / PDF 208 | texte declare corrompu et obscur par Long et Sedley |
| 38G-H | Le raisonnement chrysippeen relie bivalence, impossibilite d'un mouvement sans cause, causalite antecedente et destin; Alexandre critique la compatibilite avec l'experience humaine. | 236-237 / PDF 244-245 | separer argument stoicien et objection d'Alexandre |
| 67M | La liberte est definie comme pouvoir d'agir par soi-meme et attribuee au sage. | 426 / PDF 434 | liberte ethico-politique; ne prouve pas une indetermination metaphysique |
| 70G | Carneade distingue verite des futurs, necessite et chaines de causes antecedente; il oppose l'existence de choses en notre pouvoir au fatalisme universel. | 456-457 / PDF 464-465 | argument academicien transmis par Ciceron |

## 7. Adjudication des trois risques de claim

### 7.1 Priorite historique de la question du libre arbitre

Verdict: `non verifie par le volume 2`.

- Le titre editorial de LS 20 est une categorie moderne de classement; il ne constitue pas une preuve qu'Epicure a formule le premier une question moderne.
- Les textes de LS 20 attestent une opposition entre necessite, action dependante de l'agent, admonestation et blame.
- La note a 20H reconnait un precedent aristotelicien apparent sur les futurs contingents, sans en tirer une genealogie generale du libre arbitre.
- A p. 489, Long et Sedley identifient leur propre developpement a Sedley [260], consacre a la refutation du determinisme. Ils renvoient separement a Huby [262] pour l'importance historique d'Epicure. La formulation actuelle du KG attribue donc trop directement a Long et Sedley une these dont ce volume ne fait qu'indiquer une etude externe.
- Verification requise: volume 1, commentaire de la section 20, puis Huby 1967, avec comparaison aux objections de Bobzien et O'Keefe.

### 7.2 Clinamen necessaire, suffisant ou cause directe

Verdict: `condition necessaire au plus; suffisance rejetee; implication directe seulement envisagee`.

- LS 20F ne permet pas de faire du clinamen une condition suffisante de la volition libre.
- LS 20E distingue le clinamen cosmologique, les mouvements des atomes de l'esprit et la causalite non physique attribuee au soi dans la lecture du volume 1.
- La possibilite d'une implication directe dans chaque nouvelle action autonome n'est qu'une suggestion de lecture du langage de Lucrece.
- Carneade, tel que transmis en 20E, sert precisement a montrer qu'une defense du mouvement volontaire peut etre formulee sans clinamen.
- Ingestion sure: `clinamen_breaks_physical_deterministic_closure` et `volition_has_no_external_antecedent_cause` doivent rester deux claims distincts et contestes.

### 7.3 Compatibilisme stoicien

Verdict: `famille de strategies compatibilistes, pas doctrine univoque directement attestee`.

- LS 62C-D fournit le noyau causal: cause externe declenchante plus nature interne de l'agent.
- LS 62G montre comment un adversaire comprend `eph' hemin` de facon unilaterale, comme action produite par l'agent selon sa nature, non comme pouvoir bilateral de faire ou ne pas faire.
- LS 62H formule l'objection incompatibiliste; elle ne doit pas etre fusionnee avec le noyau stoicien.
- LS 62I-J preservent les pratiques normatives dans l'ordre fatal, ce qui n'est pas encore une theorie complete de la justification du blame.
- LS 62K est une doctrine epicteteenne centree sur l'usage des impressions. Elle doit etre datee et separee du dispositif chrysippeen du cylindre.

## 8. Comparaison avec le depot

### 8.1 Manifestes et registre SOTA

| Enregistrement | Constat | Action future recommandee |
|---|---|---|
| `lit_long_sedley_1987_hellenistic_philosophers_vol2` dans `data/literature_acquisition/manifest.jsonl` | hash, taille, createurs et 520 pages exacts | conserver; ajouter l'impression 1998, les ISBN du volume 2 et une completude `title_page_through_bibliography` |
| meme enregistrement | `year_display: 1987` decrit l'oeuvre mais pas la manifestation | conserver 1987 au niveau oeuvre; ajouter 1998 au niveau manifestation |
| meme enregistrement | `derivative_of: null` ne relie pas le scan a l'impression | creer une manifestation imprimee intermediaire ou une note de provenance |
| `src_sec_long_sedley_1987_hp2` | titre canonique et createurs corrects; `canonical_identifiers` vide | ajouter les deux ISBN visibles et distinguer work/volume/scan |
| `src_sec_long_sedley_1987_hp2` | `acquisition.status: local_unregistered` est desormais en tension avec le manifeste d'acquisition, mais le fichier reste absent de `data/scholarly_sources/manifest.jsonl` | reconcilier les deux registres sans declarer a tort une ingestion savante complete |
| `src_sec_long_sedley_1987_hp2` | `coverage.state: none` et `kg_node_ids: []`, alors que des candidats KG existent | mapper explicitement le source ID au work, au volume et a `collection_ls` apres correction |
| `ev_sec_long_sedley_section20_pp104_113` | plage exacte; `page_map_status: provisional` peut etre leve apres revue independante | passer a `verified` seulement apres seconde revue documentaire |
| `ev_sec_long_sedley_sections55_62_pp332_388` | unite fusionnee et borne finale fausse | scinder en LS55 p.332-341 et LS62 p.382-389; ne pas ingerer p.342-381 sous ce label |
| `issue_secondary_archive_manifest_gap_20260824` | le gap demeure reel pour `src_sec_long_sedley_1987_hp2` | le fermer seulement apres manifestation, pages et evidence units atomisees |

### 8.2 Noeuds et aretes bibliographiques KG

Noeuds directement concernes:

- `scholarly_work_long_sedley_1987_hellenistic_philosophers`;
- `collection_ls`;
- `scholarly_position_long_sedley_epicurus_first_freewill`;
- `scholar_long_anthony`;
- `scholar_sedley_david`;
- `scholarly_argument_cary_hellenistic_positions_on_deter_6`.

Constats exacts:

1. `scholarly_work_long_sedley_1987_hellenistic_philosophers` porte les deux `author_ids`, mais `data/kg/publications.bib` omet le champ `author`; `data/kg/publications_bibtex_report.json` le signale. Son ISBN `978-0521275569` est celui du volume 1, pas celui du volume 2 audite.
2. L'arete `19c5f906-84c0-4b28-a942-6eab6e1a6ff4` relie le work a Long par `authored_by`; aucune arete parallele ne relie le work a Sedley, malgre la co-signature visible.
3. L'arete `7ba4e8ef-035a-49a9-84f3-2a1cdb92159c` relie la position de priorite a Long seul par `created_by`; le noeud mentionne Sedley dans ses metadonnees mais sans arete equivalente.
4. L'arete `ag_026_advanced_in` declare explicitement que la position de priorite est avancee dans le volume 1. Le present audit du volume 2 ne peut ni verifier ni invalider cette reference; elle doit rester fail-closed jusqu'a l'audit du volume 1.
5. L'arete `faultlines-20260817-030` conserve utilement l'opposition d'O'Keefe, mais ne constitue pas une verification de la these attribuee a Long et Sedley.
6. L'arete `98546e85-672b-4db9-9b62-09892ae1cc97` note un desaccord general de Bobzien avec l'ouvrage; elle est trop large pour servir de preuve d'un claim precis.
7. `collection_ls` distingue correctement les fonctions des deux volumes, mais ses pages de sections clefs sont les pages du volume 1. Elles doivent etre explicitement marquees `vol.1` pour ne pas etre appliquees au PDF local. Exemples: LS20 p.102 dans le volume 1 contre p.104 dans le volume 2; LS55 p.333 contre p.332; LS62 p.386 contre p.382.

### 8.3 Position `Epicure premier` et patch E2 Cary

Le noeud `scholarly_position_long_sedley_epicurus_first_freewill` contient six premisses et une conclusion sans ancre de passage. Le volume 2 permet seulement de soutenir les elements anti-deterministes et responsabilistes de LS 20, avec les restrictions deja donnees. Il ne verifie pas:

- la priorite absolue d'Epicure;
- l'absence de toute formulation incompatibiliste anterieure;
- le clinamen comme solution suffisante ou complete;
- l'attribution conjointe et explicite de cette genealogie a Long et Sedley.

Le patch `data/kg/e2_patches/cary.json` affecte `scholarly_argument_cary_hellenistic_positions_on_deter_6`. Cary cite Long et Sedley, volume 1, p. 102-112, pour opposer une physique epicurienne indeterministe a une strategie stoicienne compatibiliste. Ce patch est verifie contre Cary, non contre le volume 2. Il doit rester un claim attribue a Cary et ne jamais etre remappe automatiquement vers p. 102-112 du PDF local, qui correspondent a d'autres pages et a un autre volume.

Aucun patch dedie a Long et Sedley n'existe dans `data/kg/e2_patches/` ni dans `data/kg/acquisition_patches/`. Le manifeste d'acquisition et les enregistrements SOTA cites plus haut sont les enregistrements directs du fichier local.

### 8.4 Citations LS et aretes `part_of collection_ls`

Le KG contient 182 aretes vers `collection_ls`; 54 portent une reference commencant par 20, 38, 55, 62, 67 ou 70. Les erreurs ci-dessous ont ete controlees contre les etiquettes visibles du volume 2.

#### Aretes ou citations contradictoires

| Noeud ou arete | Reference actuelle | Verdict visuel |
|---|---|---|
| `passage_dl_lives_10_1_129` et `deepaudit-passage_dl_lives_10_1_129-partof-collection_ls` | 20A | faux: 20A est *Ep. Men.* 133-134; les noeuds exacts existants sont `passage_dl_lives_10_1_133` et `passage_dl_lives_10_1_134` |
| `passage_cic_fat_48` et `deepaudit-passage_cic_fat_48-partof-collection_ls` | 20E | faux comme manifestation exacte: 20E imprime *De fato* 21-25; 48 n'est qu'un locus parallele mentionne dans une note |
| `passage_alex_fat_2` et `deepaudit-passage_alex_fat_2-partof-collection_ls` | 55N | faux: 55N est Alexandre, *De fato* 191.30-192.28, correspondant au dossier transmis aussi comme SVF II.945, non au chapitre 2 |
| `passage_cic_fat_34` et `deepaudit-passage_cic_fat_34-partof-collection_ls` | 55J | faux: 55J est Aetius 1.28.4; la metadonnee 55N du meme noeud est egalement fausse |
| `passage_dl_lives_7_1_99` et `deepaudit-passage_dl_lives_7_1_99-partof-collection_ls` | 55A | faux: 55A est Stobee 1.138.14-139.4 |
| `passage_dl_lives_7_1_116` et `deepaudit-passage_dl_lives_7_1_116-partof-collection_ls` | 55F | faux: 55F est Galien, *Caus. cont.* 1.1-2.4; la reference LS65A egalement presente sur le noeud appartient a un autre dossier |
| `passage_dl_lives_7_1_79` et `deepaudit-passage_dl_lives_7_1_79-partof-collection_ls` | 38G | faux: 38G est Ciceron, *De fato* 20-21 |
| `passage_dl_lives_7_1_82` | metadonnee 20A | faux; l'arete vers `collection_ls` porte actuellement 65G et ne materialise pas cette erreur secondaire |
| `passage_dl_lives_7_1_104` | metadonnee 55D | faux: 55D est Clement, *Strom.* 8.9.30.1-3 |
| `passage_dl_lives_7_1_156` | metadonnee 62G | faux: 62G est Alexandre, *De fato* 181.13-182.20 |

La famille Aulu-Gelle demande une reparation de plage exacte:

- LS 55K = Aulu-Gelle 7.2.3;
- LS 62D = Aulu-Gelle 7.2.6-13;
- les aretes `deepaudit-passage_gellius_na_vii_2_7_2_1-partof-collection_ls` a `..._15-partof-collection_ls` marquent actuellement les quinze paragraphes comme 62D;
- seules les aretes pour les paragraphes 6-13 correspondent a 62D;
- les paragraphes 1-5 et 14-15 doivent etre retires de cette manifestation;
- `passage_gellius_na_vii_2_7_2_3` doit porter 55K;
- les metadonnees 55K presentes sur `passage_gellius_na_vii_2_7_2_4` et `passage_gellius_na_vii_2_7_2_13` sont fausses.

Les noeuds ciceroniens suivants ont une arete principale correcte mais des references LS supplementaires fausses dans `metadata.fragment_collections`:

- `passage_cic_fat_12`: conserver 38E; retirer 38H, 55K, 55L, 55R et 62H comme manifestations exactes;
- `passage_cic_fat_39`: conserver 62C; retirer 38E, 38H, 55I, 55K, 55L, 55N, 55R, 62B, 62D et 62H;
- `passage_cic_fat_41`: conserver 62C; retirer 62D;
- `passage_cic_fat_42`: conserver 62C; retirer 62D et 62G.

#### Aretes confirmees mais manifestations incompletes

| Unite LS | Aretes confirmees | Manque exact |
|---|---|---|
| 20E | `deepaudit-passage_cic_fat_22-partof-collection_ls`, `..._23-partof-collection_ls` | ajouter les paragraphes 21, 24 et 25; ne pas ajouter 48 comme membre exact |
| 55S | `deepaudit-passage_cic_fat_28-partof-collection_ls`, `..._30-partof-collection_ls` | ajouter `passage_cic_fat_29` |
| 62C | `deepaudit-passage_cic_fat_39-partof-collection_ls` a `..._43-partof-collection_ls` | plage complete pour le texte ciceronien |
| 62D | aretes Aulu-Gelle 7.2.6 a 7.2.13 | retirer le surcodage hors plage |
| 62G | `deepaudit-passage_alex_fat_13-partof-collection_ls` | correspondance exacte confirmee |
| 38E | `deepaudit-passage_cic_fat_12-partof-collection_ls` | 38E couvre 12-15; les paragraphes 13-15 restent a verifier dans la couche granulaire |
| 67M | `deepaudit-passage_dl_lives_7_1_121-partof-collection_ls` | correspondance exacte confirmee; retirer l'autre metadonnee LS59A du noeud |
| 70G | `deepaudit-passage_cic_fat_26-partof-collection_ls`, `..._31-partof-collection_ls` | 70G couvre 26-33 et incorpore 55S par renvoi; la manifestation granulaire est partielle |

#### Unites prioritaires sans manifestation exacte correcte dans `collection_ls`

- LS 20B, 20C, 20D, 20F, 20G, 20H, 20I et 20j;
- LS 55A-55R, sauf les recoupements partiels ou errones decrits ci-dessus; 55S est seulement partiel;
- LS 62A, 62B, 62E, 62F, 62H, 62I, 62J et 62K;
- LS 55K doit etre cree sur Aulu-Gelle 7.2.3;
- LS 55N doit viser le vrai passage alexandrin ou une manifestation SVF II.945, pas *De fato* 2.

Des noeuds SVF existants peuvent servir de pistes de manifestation, notamment `passage_chrysippus_svf_ii_913`, `_917`, `_921`, `_939`, `_944`, `_945`, `_974`, `_975`, `_979`, `_982`, `_997`, `_998` et `_1000`. Leur existence ne vaut pas recollation primaire; aucun n'est actuellement relie a `collection_ls` dans les aretes controlees.

## 9. Lacunes fail-closed et plan d'ingestion

### 9.1 Lacunes a conserver ouvertes

1. Le tirage exact au-dela de la ligne 1998 et la reliure ne sont pas demonstrables sans couverture.
2. Les preliminaires i-ii et la couverture ne sont pas dans le scan.
3. Le volume 1 n'a pas ete audite dans cette mission; ses traductions, commentaires, pages et index ne sont donc pas verifies ici.
4. Les sources papyrologiques de LS 20 n'ont pas ete recollees contre les PHerc., leurs apographes ou une edition papyrologique recente.
5. Les fragments stoiciens transmis par des auteurs hostiles ou tardifs n'ont pas ete recolles contre les editions critiques de leurs oeuvres.
6. Le texte de Galien en LS 55F n'est pas un original grec conserve; les voies arabe et latine doivent etre modelees.
7. Le statut de la these historique sur la premiere question du libre arbitre reste ouvert.
8. Le passage de condition necessaire du clinamen a une causalite directe de chaque action reste explicitement non etabli.

### 9.2 Plan d'ingestion recommande

1. Creer ou normaliser trois identites: ensemble en deux volumes, volume 2 intellectuel, manifestation scannee de l'impression 1998.
2. Ajouter les deux ISBN du volume 2 et conserver l'ISBN du volume 1 uniquement sur sa manifestation propre.
3. Relier le work aux deux auteurs avec deux aretes `authored_by` explicites.
4. Scinder les evidence units du registre en `LS20`, `LS55` et `LS62`, puis en une unite par lettre LS.
5. Pour chaque unite, enregistrer: lettre LS, page imprimee, page PDF, auteur antique revendique, transmetteur reel, oeuvre transmettante, locus, collection parallele SVF ou Usener, statut textuel et niveau de confiance.
6. Corriger ou mettre en quarantaine les references `fragment_collections` contradictoires avant toute nouvelle propagation automatique d'aretes.
7. Modeliser les relations distinctes `printed_as_exact_excerpt`, `parallel_locus_mentioned_in_note` et `modern_interpretation`; ne plus utiliser `part_of collection_ls` pour un simple parallele.
8. Verifier LS 20A avec Diogene Laerce 10.133-134, LS 20E avec Ciceron 21-25, LS 55K avec Aulu-Gelle 7.2.3, LS 55N avec Alexandre 191.30-192.28, LS 55S avec Ciceron 28-30, LS 62C avec Ciceron 39-43, LS 62D avec Aulu-Gelle 7.2.6-13 et LS 62G avec Alexandre, chapitre 13.
9. Recoller ensuite chaque locus a une edition critique ou a une source numerique identifiee; jusque-la, marquer `ancient_locus_lead_not_primary_verified`.
10. Soumettre les claims historiques et interpretatifs a une seconde revue independante et a une passe adversariale, particulierement `first free-will question`, `clinamen causes volition` et `Stoic compatibilism`.
11. Auditer separement le volume 1 avant de publier tout claim attribue au commentaire philosophique de Long et Sedley.

## 10. Regle de reutilisation et droit d'auteur

Le PDF est un ouvrage moderne sous droit d'auteur. Le present rapport ne reproduit ni traduction, ni passage grec ou latin, ni note substantielle verbatim. Les claims sont des paraphrases courtes et les loci ne sont donnes que comme identifiants de recherche. Le statut `reuse_status: unverified_do_not_republish` du manifeste doit etre conserve. Toute ingestion publique doit stocker des pointeurs, des metadonnees et des paraphrases, non des images de pages ou de longs extraits.

## 11. Conclusion operationnelle

Le scan est suffisamment lisible et structurellement continu pour servir de source savante secondaire du volume 2, a condition de le decrire comme manifestation portant une ligne d'impression jusqu'en 1998 et incomplete en couverture et preliminaires. Les sections 20, 55 et 62 sont desormais localisees et doublement relues visuellement. Elles permettent de corriger les limites de pages et d'identifier plusieurs erreurs exactes de sigles LS dans le KG.

Elles ne permettent pas encore de publier comme faits etablis la priorite historique d'Epicure, une causalite suffisante du clinamen ou un compatibilisme stoicien unitaire. Ces trois propositions doivent rester attribuees, atomisees et fail-closed jusqu'a l'audit du volume 1 et a la recollation des sources antiques.
