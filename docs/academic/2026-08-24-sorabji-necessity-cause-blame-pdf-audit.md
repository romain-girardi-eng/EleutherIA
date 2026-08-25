# Audit savant du PDF de Sorabji, *Necessity, Cause and Blame*

Date de l'audit: 2026-08-24  
Portée: lecture savante en écriture documentaire seulement; aucune modification du KG, du corpus, des registres ou des manifestes.  
Source visuelle faisant autorité: `data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf`.  
Convention: `p.` désigne la pagination imprimée du livre; `PDF` désigne le numéro de page du fichier, compté à partir de 1.

## Verdict fail-closed

Le scan est structurellement complet d'après les preuves internes disponibles: couverture, faux-titre, frontispice, titre, copyright, table, liminaires, corps continu, bibliographie, index terminé à l'entrée Zeno, puis quatrième de couverture. Le PDF contient 344 pages et exactement une image raster par page. Aucun défaut de syntaxe PDF n'a été détecté.

L'identité du contenu est certaine: Richard Sorabji, *Necessity, Cause, and Blame: Perspectives on Aristotle's Theory*. L'identité de la manifestation locale doit toutefois rester formulée prudemment. Le titre et le copyright visibles sont ceux de Cornell University Press; le copyright porte 1980 et annonce un premier Cornell Paperback en 1983. La couverture et le dos portent Cornell Paperbacks. En l'absence de numéro d'impression, ce scan est donc très probablement un exemplaire du paperback Cornell de 1983 ou d'un tirage ultérieur, mais son tirage exact n'est pas démontrable. Le scan local ne prouve pas qu'il s'agit de l'édition Duckworth, même si Duckworth appartient à l'histoire bibliographique de l'oeuvre.

Le constat savant central est également sûr, mais il doit être attribué à Sorabji, non transformé en consensus: Sorabji reconstruit Aristote comme indéterministe au sens où les actions humaines peuvent être causées sans avoir été nécessaires depuis toujours. Il refuse de transformer l'`archê` interne en cause non causée. Il soutient aussi qu'Aristote avait déjà aperçu le conflit entre déterminisme et responsabilité; la nouveauté hellénistique aurait été la persistance de Diodore et des Stoïciens dans le déterminisme, puis la recherche de réponses compatibilistes.

## 1. Identité, intégrité et provenance

### 1.1 Fichier source faisant autorité

| Propriété | Valeur contrôlée |
|---|---|
| Chemin | `data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf` |
| SHA-256 | `be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500` |
| MD5, pour comparaison avec d'anciens artefacts seulement | `fad1922c52969d334243888e0f9856a6` |
| Taille | 35,334,906 octets |
| Pages | 344 |
| Format | PDF 1.2, 389.52 x 594.72 points, rotation 0, non chiffré |
| Nature | scan image-only, non balisé, aucune police incorporée |
| Images | 344 images pour 344 pages; le corps est majoritairement en bitonal 600 dpi |
| Contrôle syntaxique | `qpdf --check`: aucun défaut de syntaxe ou d'encodage de flux détecté |
| Métadonnée technique | produit par `libtiff / tiff2pdf - 20250911`; date de conteneur 2026-05-19, sans valeur pour la date d'édition |

L'extraction directe du scan ne contient pas de texte utile: les 344 octets obtenus correspondent essentiellement aux séparateurs de pages. Toutes les décisions visuelles ci-dessous ont donc été prises sur des rendus du scan source, non sur son dérivé OCR.

### 1.2 Dérivé OCR utilisé uniquement comme aide

| Propriété | Valeur contrôlée |
|---|---|
| Chemin | `data/literature_acquisition/sorabji_1980_necessity_cause_blame_ocr.pdf` |
| SHA-256 | `022e9c6440f7a5e43f89c72205795165853ae85b97389b167027a3bf0e38b007` |
| MD5 | `e474ab26adb4f127a0445f1e2628ae28` |
| Taille | 79,185,903 octets |
| Pages | 344 |
| Producteur | OCRmyPDF 17.4.2 / Tesseract 5.5.2 |
| Contrôle syntaxique | `qpdf --check`: aucun défaut détecté |

Le dérivé OCR a servi à rechercher les noms, à suivre les notes et à comparer l'index au corps. Il n'est jamais traité comme autorité pour la mise en page, les numéros imprimés, les diacritiques grecs, les citations ou la présence matérielle d'une page. Les erreurs visibles incluent notamment des chiffres romains confondus, des caractères grecs dégradés et des répétitions locales de blocs lors de l'extraction.

### 1.3 Identité bibliographique visible

Les pages de titre et de copyright établissent visuellement les éléments suivants:

- PDF 4: Richard Sorabji, *Necessity, Cause, and Blame: Perspectives on Aristotle's Theory*, Cornell University Press, Ithaca, New York.
- PDF 5: copyright 1980 par R. Sorabji; première publication Cornell University Press en 1980; premier Cornell Paperbacks en 1983; impression aux États-Unis.
- PDF 5: ISBN `0-8014-1162-9` pour le cartonné et `0-8014-9244-0` pour le paperback; Library of Congress `79-2449`.
- PDF 1 et PDF 344: couverture et quatrième de couverture Cornell Paperbacks.

Conclusion bibliographique minimale autorisée par le scan: `Sorabji, Richard. Necessity, Cause, and Blame: Perspectives on Aristotle's Theory. Ithaca, NY: Cornell University Press, copyright 1980; Cornell paperback first issued 1983.` Le tirage précis reste indéterminé. Il ne faut pas remplacer cette formulation par `London: Duckworth` dans un enregistrement décrivant cette manifestation locale.

## 2. Carte de pagination et complétude

### 2.1 Carte imprimée vers PDF

| PDF | Pagination ou fonction visible | Statut |
|---:|---|---|
| 1 | couverture | visible |
| 2 | faux-titre | visible |
| 3 | frontispice | visible |
| 4 | titre | visible |
| 5 | copyright et données CIP | visible |
| 6 | table, p. v attendue; folio supprimé | p. v inférée par la séquence |
| 7 | table, p. vi | visible |
| 8 | acknowledgments, p. vii attendue; folio supprimé | p. vii inférée par la séquence |
| 9 | acknowledgments, p. viii | visible |
| 10-16 | introduction, p. ix-xv | visible et continue |
| 17 | abbreviations, p. xvi attendue; folio supprimé | p. xvi établie par la table et la séquence |
| 18 | intertitre Part I, p. 1 attendue; folio supprimé | inférence forte, non imprimée |
| 19 | verso blanc, p. 2 attendue | inférence forte, non imprimée |
| 20-343 | p. imprimées 3-326 | règle contrôlée: `PDF = p. imprimée + 17` |
| 344 | quatrième de couverture | visible; ce n'est pas une p. 327 |

La règle arabe a été vérifiée aux débuts et fins de chaque chapitre, sur les pages de transition, au début de la bibliographie et jusqu'à la dernière page de l'index. La seule incertitude concerne les folios supprimés des p. 1-2 et de certaines pages liminaires; leur position est certaine, mais leur chiffre n'est pas imprimé dans l'image.

### 2.2 Localisation des appareils

- Table des matières: PDF 6-7, p. v-vi.
- Bibliographie sélective: PDF 316-328, p. 299-311.
- Index: PDF 329-343, p. 312-326; le titre de l'index est sur p. 312 avec folio supprimé.
- Dernière page imprimée: p. 326, PDF 343; l'index se termine par Xenophon, Zeller et Zeno.

La table annonce dix-huit chapitres, la bibliographie à p. 299 et l'index à p. 312. Les débuts de chapitre visibles concordent tous avec la table. Le calcul de cardinalité concorde aussi: PDF 20-343 fournit exactement 324 pages, soit les p. imprimées 3-326 incluses.

## 3. Inventaire de lecture

### 3.1 Lecture substantielle et contrôle visuel

| Section | Pages imprimées | Pages PDF | Traitement |
|---|---:|---:|---|
| Liminaires, table, introduction, abréviations | v-xvi | 6-17 | lecture visuelle; introduction lue intégralement |
| Ch. 1, coincidences et causes | 3-25 | 20-42 | lecture continue; contrôle visuel de toute la séquence; relecture ciblée p. 18-25 |
| Ch. 2, cause, nécessité, explication | 26-44 | 43-61 | lecture continue; contrôle visuel de toute la séquence; relecture p. 26-32 et 41-44 |
| Ch. 3, nécessité et loi | 45-69 | 62-86 | lecture continue; contrôle visuel de toute la séquence; relecture p. 64-69 |
| Ch. 4, difficulté stoïcienne | 70-88 | 87-105 | deux passes complètes; pages clés relues individuellement en haute résolution |
| Ch. 5, bataille navale | 91-103 | 108-120 | lecture continue et contrôle visuel intégral; relecture p. 91-94 et 100-103 |
| Ch. 6, nécessité du passé | 104-120 | 121-137 | lecture continue et contrôle visuel intégral; relecture p. 104-110 et 119-120 |
| Ch. 7, prescience | 121-127 | 138-144 | lecture intégrale et contrôle individuel de chaque page |
| Ch. 8, possibilité | 128-140 | 145-157 | lecture continue et contrôle visuel intégral; relecture p. 128, 132-140 |
| Ch. 9, nécessité naturelle | 143-154 | 160-171 | lecture intégrale et contrôle visuel intégral |
| Ch. 13, appendice des types de nécessité | 222-224 | 239-241 | lecture et contrôle visuel ciblés |
| Ch. 14, action humaine | 227-242 | 244-259 | deux passes complètes; pages clés relues individuellement |
| Ch. 15, déterminisme et involontaire | 243-256 | 260-273 | deux passes complètes; pages clés relues individuellement |
| Ch. 16, involontaire et équité | 257-271 | 274-288 | lecture intégrale et contrôle visuel intégral; relecture p. 257-262, 266-271 |
| Ch. 17, volontaire, tentation, négligence | 272-287 | 289-304 | lecture intégrale et contrôle visuel intégral; relecture p. 276-281 et 287 |
| Ch. 18, théorie juridique | 288-298 | 305-315 | lecture intégrale et contrôle visuel intégral; relecture p. 288-295 et 298 |
| Bibliographie | 299-311 | 316-328 | lue intégralement; contrôle visuel de chaque page |
| Index | 312-326 | 329-343 | lu intégralement; contrôle visuel de chaque page |

Les p. 89-90, 141-142 et 225-226 sont des transitions, blancs ou intertitres et ont été contrôlées dans la vérification des limites.

### 3.2 Lecture de tri, sans extraction de claims

Les chapitres 10-12 et le corps principal du chapitre 13 ont été parcourus pour déterminer leur pertinence, avec lecture OCR de routage et contrôle visuel des limites:

- Ch. 10, p. 155-174, PDF 172-191: téléologie biologique et explication.
- Ch. 11, p. 175-184, PDF 192-201: sélection naturelle antique et moderne.
- Ch. 12, p. 185-208, PDF 202-225: nécessité analytique ou *de re*.
- Ch. 13, p. 209-221, PDF 226-238: essences et nécessité. Les p. 225-226, PDF 242-243, sont l'intertitre de la Part V et son verso blanc.

Ces pages sont secondaires pour la mission centrée sur libre arbitre, déterminisme, causalité de l'action et responsabilité. Aucun claim ci-dessous ne repose sur elles, sauf la taxonomie de la nécessité des p. 222-224, visuellement relue.

## 4. Claims atomiques, prudemment attribués

Tous les énoncés de cette section sont des paraphrases brèves. `Sorabji:` marque sa propre thèse ou sa reconstruction. `Rapport:` marque une doctrine antique rapportée par lui. Aucun énoncé n'est une vérification indépendante de la source antique.

### 4.1 Cadre et causalité

| ID | Claim atomique | Preuve imprimée / PDF | Loci antiques mobilisés | Qualification |
|---|---|---|---|---|
| SOR-F01 | Sorabji définit le déterminisme par la nécessité depuis toujours de tout ce qui arrive, non par la seule causalité et non par la négation définitionnelle de la responsabilité. | ix-x / PDF 10-11 | aucun locus unique | définition opératoire propre à l'auteur |
| SOR-F02 | Sorabji déclare ne pas être convaincu par les arguments déterministes ni par leur compatibilité avec la responsabilité morale. | ix / PDF 10 | aucun | position philosophique de Sorabji, non thèse historique |
| SOR-C01 | Sorabji lit *Metaph.* VI 3 comme refusant de vraies causes aux coincidences, tout en soutenant lui-même qu'une coincidence peut être nécessitée par ses antécédents. | 3-25, surtout 3-5 et 18-25 / PDF 20-42 | *Metaph.* VI 2-3, 1027a7-8 et 1027a29-b14; *Phys.* II 4-6 | reconstruction disputable de Sorabji |
| SOR-C02 | La thèse philosophique porteuse du livre est qu'un effet peut être causé et expliqué sans être nécessité. | 26-32, 44 / PDF 43-49, 61 | arrière-plan: *NE* III 5; *Int.* 9; *GC* II 11 | Sorabji s'appuie aussi sur Anscombe et Scriven |
| SOR-C03 | Rapport: la doctrine stoïcienne associe la causalité à la répétition sans exception du même effet lorsque la totalité des circonstances se répète, puis à la nécessité. | 64-69 / PDF 81-86 | Alexandre, *De Fato* 10, 15, 22; Plutarque, *De Stoic. Repugn.* 1045b-c; Némésius 35 | doctrine reconstruite via témoins adverses et tardifs |
| SOR-C04 | Sorabji juge incohérentes les formulations aristotéliciennes sur la nécessité naturelle: Aristote admet de nombreuses nécessitations causales tout en limitant ailleurs fortement la nécessité. | 143-154 / PDF 160-171 | *GC* II 11; *PA* I 1; *Phys.* II 9; *An. Post.* II 11-12 | ne pas aplatir en une doctrine unique d'Aristote |
| SOR-C05 | Sorabji refuse que `archê` désigne nécessairement le premier membre non causé d'une chaîne; délibération, choix et action peuvent chacun être une origine intermédiaire. | 228-233 / PDF 245-250 | *Int.* 9, 18b26-19a22; *NE* VI 2, 1139a31-b5; *Phys.* VIII 5-6 | réponse à Ross, Furley et Hardie |
| SOR-C06 | L'enfant qui prend le jouet est un exemple construit par Sorabji d'une action causée par des sentiments internes, sans être nécessitée; ce n'est pas un exemple donné par Aristote. | 232 / PDF 249 | arrière-plan: *NE* III 5 | provenance conceptuelle à conserver explicitement |
| SOR-C07 | Sorabji lit `eph' hêmin` et l'origine interne comme impliquant, pour les humains, la possibilité d'agir ou de s'abstenir. | 233-235 / PDF 250-252 | *NE* III 5, 1113b7-8, 1113b20-21, 1114a18-21; *EE* II 6, 9-10; *NE* V 8 | lecture opposée à Loening; à ne pas déclarer consensus |
| SOR-C08 | Sur cette lecture, une action volontaire ne peut pas avoir été nécessaire depuis toujours, mais peut devenir nécessaire plus tard; la causalité n'est pas niée. | 235-238 / PDF 252-255 | *EE* II 9-10; *NE* V 8; *NE* III 1 et 5 | thèse de Sorabji |
| SOR-C09 | Sorabji traite l'implication de *Metaph.* VI 3, selon laquelle le causé est nécessité, comme une thèse atypique qu'Aristote ne maintient pas dans l'éthique. | 238, 240, 248 / PDF 255, 257, 265 | *Metaph.* VI 3; *NE* III | formulation critique de Sorabji, non auto-correction explicite d'Aristote |
| SOR-C10 | La taxonomie finale distingue notamment nécessité relative, hypothétique, irrévocabilité du passé, nécessité naturelle, force contraire à la nature et nécessité sous menace. | 222-224 / PDF 239-241 | *SE* 4; *GC* II 11; *Cael.* I 12; *NE* III 1; *Rhet.* I 10 | taxonomie reconstruite par Sorabji, non liste aristotélicienne unique |

### 4.2 Stoïciens, Diodore et Épicure

| ID | Claim atomique | Preuve imprimée / PDF | Sources antiques citées | Qualification |
|---|---|---|---|---|
| SOR-S01 | Rapport: Chrysippe aurait affirmé une fatalité universellement nécessaire; le chien attaché au chariot illustre que le consentement volontaire n'empêche pas la nécessité. | 70-71 / PDF 87-88 | Diogénien chez Eusèbe, *PE* VI 8; Hippolyte I 21; Plutarque; Aulu-Gelle VII 2 | rapport doxographique, non fragment autographe |
| SOR-S02 | Sorabji distingue exactement huit tentatives stoïciennes de retrait par rapport à la nécessité. | 71-85 / PDF 88-102 | voir les huit lignes suivantes | son classement analytique |
| SOR-S02a | Tentatives 1-2: Cléanthe nie que tout passé vrai soit nécessaire; Chrysippe nie que l'impossible ne puisse suivre du possible. | 72 / PDF 89 | Épictète, *Diss.* II 19.1-5; Alexandre, *in An. Pr.* 177 | réponses au Maître Argument |
| SOR-S02b | Tentative 3: la nécessité ne se transmettrait pas toujours de l'antécédent au conséquent, avec le cas Dion. | 72-74 / PDF 89-91 | Cicéron, *De Fato* 12-14; Alexandre, *in An. Pr.* | Sorabji préfère l'interprétation orthodoxe mais discute Mignucci |
| SOR-S02c | Tentative 4: les énoncés astrologiques seraient traités comme implications matérielles plutôt que comme conditionnels nécessaires. | 74-78 / PDF 91-95 | Cicéron, *De Fato* 15-16; Sextus; Diogène Laërce VII 73 | interprétation discutée avec Frede, Sambursky et Donini |
| SOR-S02d | Tentative 5: possibilité comme aptitude ou convenance, à la manière de Philon, même si un obstacle externe empêche l'actualisation. | 78-79 / PDF 95-96 | Philon via Alexandre et Boèce; Diogène Laërce VII 75 | Sorabji juge cette possibilité moralement insuffisante |
| SOR-S02e | Tentative 6: distinction des causes externes et internes, illustrée par le cylindre. | 79-83 / PDF 96-100 | Cicéron, *De Fato* 39-45; Aulu-Gelle VII 2; Augustin, *Civ.* V 10 | Sorabji distingue trois interprétations et n'en canonise pas une |
| SOR-S02f | Tentative 7: une possibilité seulement épistémique, fondée sur notre ignorance des facteurs qui empêchent l'alternative. | 83-84 / PDF 100-101 | Alexandre, *De Fato* 10 | Sorabji suit la critique d'Alexandre |
| SOR-S02g | Tentative 8: une proposition future ne serait pas nécessaire parce qu'elle cesse d'être vraie après l'événement. | 84-85 / PDF 101-102 | Alexandre, *De Fato* 10; Cicéron, *De Fato* 17-18 | Sorabji juge le test intenable |
| SOR-S03 | Sorabji conclut que les huit tentatives ne libèrent pas les Stoïciens de leur engagement envers la nécessité. | 85 / PDF 102 | ensemble des témoins précédents | jugement de Sorabji, à modéliser comme tel |
| SOR-S04 | Le cylindre permet au moins trois lectures: échappée à la nécessité; compatibilité de la responsabilité avec la nécessité; ou rejet de la seule nécessité issue des causes externes. | 80-83 / PDF 97-100 | Cicéron, Aulu-Gelle, Augustin; lectures de Donini et Frede | ne pas réduire à une doctrine univoque |
| SOR-S05 | Rapport: une action stoïcienne peut être dite `eph' hêmin` si elle suit l'impulsion et arrive par nous, sans impliquer une alternative réellement ouverte. | 86, 252 / PDF 103, 269 | Alexandre, *De Fato* 13, 26; *Quaest.* II 4; Némésius 35 | présentation compatibiliste rapportée par des adversaires |
| SOR-S06 | Sorabji estime que le déterminisme dur fut rare; la réponse douce n'apparait peut-être qu'avec Chrysippe. | 87-88 / PDF 104-105 | Zénon chez Diogène Laërce VII 23; Épicure; Alexandre | vocabulaire moderne de Sorabji, anachronique mais déclaré |
| SOR-E01 | Sorabji rapporte que le clinamen est présenté, dans l'exposé latin de Lucrèce, comme moyen de défendre la liberté, puis rappelle l'objection selon laquelle l'absence de cause rendrait l'action aléatoire. | 18-19, 86 / PDF 35-36, 103 | Lucrèce, *DRN* II 216-293; Cicéron, *De Fato* 22-23; *Fin.* I 6.19 | attribution à Lucrèce et à une objection, non doctrine épicurienne directement établie |
| SOR-E02 | Épicure aurait refusé que toute proposition future soit déjà vraie ou fausse parce qu'il craignait une conclusion déterministe. | 93-94, 107, 109-110 / PDF 110-111, 124, 126-127 | Cicéron, *De Fato* 17-21, 37-38; *Acad.* II 30.97; *ND* I 25.70 | reconstruction via Cicéron |
| SOR-E03 | Épicure connaissait l'argument selon lequel admonester et être admonesté resteraient inévitables, que la pratique soit justifiée ou non, et s'y opposait. | 87 / PDF 104 | Épicure, *On Nature* 34.27 | reconstruction de Sorabji à partir d'un fragment |
| SOR-E04 | Sorabji cite séparément Épicure parmi les successeurs qui utilisent l'efficacité des sanctions pour attaquer le déterminisme. | 245 / PDF 262 | Épicure, *On Nature* 31.27.3-9 | ne pas confondre ce fragment avec *On Nature* 34.27 |
| SOR-D01 | Diodore définit le possible comme ce qui est ou sera, ou sera vrai; son Maître Argument n'est conservé que très sommairement par Épictète. | 104-108 / PDF 121-125 | Épictète, *Diss.* II 19.1-5; Alexandre, *in An. Pr.* 183-184; Cicéron | toute reconstruction détaillée doit rester hypothétique |
| SOR-D02 | Sorabji juge légèrement plus plausible la reconstruction de Prior, car elle relie Diodore à *Int.* 9 et à la réaction d'Épicure, mais reconnait l'incertitude. | 105-110 / PDF 122-127 | mêmes sources | préférence argumentée, non fait antique |

### 4.3 Aristote, Alexandre et réception antique

| ID | Claim atomique | Preuve imprimée / PDF | Sources antiques citées | Qualification |
|---|---|---|---|---|
| SOR-A01 | Sorabji soutient qu'Aristote connaissait des formes causales et non causales de déterminisme. | 243-244 / PDF 260-261 | *Int.* 9; *Metaph.* VI 3; *Phys.* II 4; *GC* II 11 | thèse contre une orthodoxie moderne composite |
| SOR-A02 | Il soutient qu'Aristote voyait parfois trop vite une incompatibilité entre déterminisme, délibération, effort et responsabilité. | 245-247 / PDF 262-264 | *Int.* 9, 18b31-33, 19a7-8; *NE* III 5, 1113b21-30 | Sorabji juge plusieurs arguments aristotéliciens invalides |
| SOR-A03 | Rapport: Aristote refuse louange et blâme pour ce qui arrive nécessairement. | 246 / PDF 263 | *NE* III 5, 1114a23-29; *EE* II 6, 1223a10; II 11, 1228a5 | le passage distingue aussi honneur et louange |
| SOR-A04 | Selon Sorabji, la nouveauté hellénistique n'est ni l'invention du déterminisme ni la découverte du conflit moral, mais le maintien de Diodore et des Stoïciens dans le déterminisme, puis les nouvelles réponses dure et douce. | 247 / PDF 264 | Zénon, Épicure, Chrysippe et réception citée aux p. 244-247 | claim historique propre à Sorabji, fortement contestable |
| SOR-A05 | Sorabji sépare la liberté politique, le volontaire et la responsabilité; *NE* III traite d'abord du volontaire, pas d'une faculté moderne de volonté. | 249-251, 257 / PDF 266-268, 274 | *NE* III; *Metaph.* XII 10, 1075a19-23 | ne pas transformer en généalogie complète de la volonté |
| SOR-X01 | Alexandre sert de témoin principal pour le principe causal stoïcien et pour plusieurs tentatives de sauver possibilité et responsabilité. | 64-67, 82-86 / PDF 81-84, 99-103 | Alexandre, *De Fato* 10, 13-15, 22, 26, 35-38 | témoignage polémique à recoller dans le grec |
| SOR-X02 | Sorabji pense qu'Alexandre reprend parfois *Metaph.* VI 3 en admettant des événements sans cause plutôt qu'en inventant un argument nouveau. | 19, 86 / PDF 36, 103 | Alexandre, *De Fato* 8; *Mantissa* 170-172, attribution discutée | l'auteur de la section de la *Mantissa* reste incertain |
| SOR-X03 | Alexandre rejette l'assimilation de la prescience à une cause et nie que les futurs contingents puissent être connus. | 122, 124 / PDF 139, 141 | Alexandre, *De Fato* 30-31 | thèses distinctes à ne pas fusionner |
| SOR-X04 | Pour les futurs contingents, Sorabji juge probable qu'Alexandre accepte le refus de la bivalence anticipée, mais signale une lecture différente dans *Quaestiones* I 4 et une attribution possiblement fausse. | 93 / PDF 110 | Alexandre, *De Fato* 10, 16, 17, 27; *Quaest.* I 4 | niveau de confiance explicitement limité |
| SOR-R01 | Sorabji distingue trois familles antiques de réponse à la prescience: nier la connaissance définie des contingents; faire dépendre le mode de connaissance du connaissant; placer la connaissance divine hors du temps. | 123-125 / PDF 140-142 | Carnéade, Cicéron, Alexandre; Jamblique; Proclus; Ammonius; Boèce | schéma historiographique de Sorabji |
| SOR-R02 | Il décrit le passage de Jamblique à Proclus et Ammonius, puis à Boèce, comme une clarification graduelle de la connaissance intemporelle; il réserve à Thomas d'Aquin l'exploitation complète de l'irrévocabilité du passé. | 124-125 / PDF 141-142 | Jamblique via Ammonius; Proclus, *De dec. dub.* et *De providentia*; Boèce, *Cons.* V 6 | dernière étape médiévale, pas strictement antique |
| SOR-R03 | La tradition du Lazy Argument réemploie un motif aristotélicien contre le déterminisme. | 228, 245 / PDF 245, 262 | Cicéron, *De Fato* 28-30; Ps.-Plutarque 574e; Alexandre 16; Origène, *C. Cels.* II 20; Eusèbe VI | filiation proposée, non identité stricte des arguments |

### 4.4 Volontaire, blâme et théorie juridique

| ID | Claim atomique | Preuve imprimée / PDF | Loci antiques mobilisés | Qualification |
|---|---|---|---|---|
| SOR-B01 | Sorabji distingue trois analyses aristotéliciennes du volontaire: *NE* III 1, *EE* II 9 et *NE* V 8 ne sont pas harmonisées. | 257-259, 272-275 / PDF 274-276, 289-292 | *NE* III 1; *EE* II 9; *NE* V 8 | ne pas créer une définition aristotélicienne synthétique sans signaler la reconstruction |
| SOR-B02 | Dans *NE* III 1, les deux excuses structurantes sont la force externe sans contribution de l'agent et l'ignorance causale des circonstances particulières. | 257-258 / PDF 274-275 | *NE* III 1, 1109b35-1111a21 | le regret distingue involontaire et non-volontaire |
| SOR-B03 | *EE* II 9 et *NE* V 8 paraissent admettre davantage de cas de contrainte ou de peur comme involontaires; *NE* III peut plutôt les traiter comme volontaires mais pardonnables par équité. | 259-264 / PDF 276-281 | *EE* II 8-9; *NE* III 1; *NE* V 8 et 10; *Rhet.* I 13 | évolution textuelle, non simple synonymie |
| SOR-B04 | Sorabji estime qu'Aristote sous-évalue folie et éducation défavorable; dans le cas d'un enfant suivant de mauvais éducateurs, la vraie question est l'absence d'occasion équitable, non une cause externe sans contribution. | 265-268 / PDF 282-285 | *NE* II 1-3, III 5, X 9; *Pol.* | critique moderne contextualisée par le droit athénien |
| SOR-B05 | Pour la tentation, *NE* VII conserve une connaissance seulement partielle du cas particulier, tandis que *NE* V semble parfois admettre une transgression en pleine connaissance. | 276-278 / PDF 293-295 | *NE* VII 3, 8, 10; *NE* V 6, 8, 9 | Sorabji souligne une tension entre livres |
| SOR-B06 | La classification de *NE* V 8 va du simple accident à l'erreur négligente, puis à l'injustice consciente sans choix délibéré, enfin à l'injustice issue de `prohairesis`. | 278-281 / PDF 295-298 | *NE* V 8, 1135b10-25; *Rhet.* I 13 | le deuxième degré comme négligence est la lecture défendue par Sorabji contre Daube |
| SOR-B07 | La description de l'action est décisive: frapper un homme en connaissance peut être volontaire, frapper son père sans le savoir ne l'est pas sous cette description. | 279-280 / PDF 296-297 | *NE* V 8, 1135a28-31 | éviter des noeuds qui omettent la description pertinente |
| SOR-B08 | Sorabji place la contribution juridique majeure d'Aristote dans la classification des excuses et degrés de culpabilité, orientée vers l'équité et la justice des peines. | 288-295 / PDF 305-312 | *NE* V 4-5, 8, 10-11; *Rhet.* I 13; droit athénien et Justinien | claim historique de réception, pas preuve directe d'influence romaine |
| SOR-B09 | Il oppose avec prudence la justice et la dissuasion aristotéliciennes à la réforme et à la pollution chez Platon, dont les conséquences peuvent être sévères même pour un non-coupable. | 288-291 / PDF 305-308 | Platon, *Lois* IX; Aristote, *NE* V et X | comparaison de Sorabji |
| SOR-B10 | L'`hamartia` tragique ne doit pas être automatiquement identifiée à l'erreur coupable de *NE* V 8; le cas d'Oedipe dépend de la description de l'acte. | 295-298 / PDF 312-315 | *Poet.* 13; *NE* V 8; Sophocle, *OT* et *OC* | Sorabji refuse une inférence simple de vocabulaire |

## 5. Sources antiques citées à recoller

Cette liste rassemble les témoins les plus importants pour les claims ci-dessus. Elle n'implique aucune vérification primaire dans le présent audit.

| Auteur ou corpus | Loci principaux cités par Sorabji | Usage dans le livre |
|---|---|---|
| Aristote, *Metaphysics* | VI 2-3, 1027a7-b14; IX 3-5; XII 10 | coincidences, causalité, capacités, liberté politique |
| Aristote, *De Interpretatione* | 9, 18b7-19b4, surtout 18b26-19a22 et 19a23-39 | bataille navale, vérité passée, délibération |
| Aristote, *Physics* | II 4-9; VIII 4-6 | hasard, causes, auto-mouvement, nécessité naturelle |
| Aristote, *GC* | II 10-11, 337b1-338b19 | récurrence, nécessité et contingence naturelles |
| Aristote, *NE* | III 1-5; V 4-11; VI 2; VII 3 et 8-10; X 9 | volontaire, `eph' hêmin`, caractère, négligence, responsabilité |
| Aristote, *EE* | II 6-11 | origine interne, contrainte, définition du volontaire |
| Aristote, *Rhetoric* et *Poetics* | *Rhet.* I 10, I 13; *Poet.* 13 | équité, degrés de culpabilité, erreur tragique |
| Chrysippe et Stoa ancienne | *On Fate* I-II via Diogénien/Eusèbe; SVF II 925, 975, 998; doctrine du cylindre | nécessité universelle, causes, consentement |
| Cicéron | *De Fato* 12-23, 28-30, 39-45; *De Divinatione* I 127; *De Natura Deorum* I 25 | Diodore, Chrysippe, Épicure, Lazy Argument, cylindre |
| Alexandre d'Aphrodise | *De Fato* 7-16, 20, 22, 24, 26-27, 30-38; *in An. Pr.* 177-184; *Quaest.* I 4 et II 4 | témoignage anti-stoïcien, modalité, responsabilité, prescience |
| Ps.-Alexandre, *Mantissa* | 170-175 CIAG | causes accidentelles et absence de cause; attribution discutée |
| Plutarque et Ps.-Plutarque | *De Stoicorum Repugnantiis* 1045b-c, 1049f-1050d, 1055d-1057a; *De Fato* 574e-f | critiques du destin stoïcien et possibilité |
| Épictète | *Discourses* II 19.1-5 | seule conservation sommaire du Maître Argument |
| Aulu-Gelle | *Noctes Atticae* VII 2 | cylindre et causalité interne/externe |
| Diogène Laërce | VII 23, 65, 73, 75 | Zénon, bivalence et conditionnels stoïciens |
| Némésius | *De Natura Hominis* 35, 39, 42 | nécessité, `eph' hêmin`, responsabilité et délibération |
| Épicure | *On Nature* 34.27; 31.27.3-9 | admonestation, punition et déterminisme |
| Lucrèce | *De Rerum Natura* II 216-293 | clinamen et liberté dans l'exposé latin |
| Diogène d'Oenoanda | fragment 32 ii-iii | clinamen et absence de cause |
| Simplicius | commentaires aux *Categories* 406-407 et à la *Physics* 732-733 | réception de la bataille navale et retour cyclique |
| Ammonius | *in De Interpretatione* 130-154 CIAG | vérité définie, prescience et présent éternel |
| Boèce | commentaires à *De Interpretatione*; *Consolation* V 3 et V 6 | réception des futurs contingents et connaissance intemporelle |
| Jamblique | témoignage d'Ammonius | connaissance prenant son caractère du connaissant |
| Proclus | *De decem dubitationibus* 6-8; *De providentia* 62-64 | prescience, détermination et connaissance intemporelle |
| Origène | *On Prayer* VI 3; *Commentary on Genesis* II via *Philocalia* 23; *Contra Celsum* II 20 | prescience non causale et Lazy Argument |
| Eusèbe | *Praeparatio Evangelica* VI 6, 8, 11 | fragments stoïciens et réception anti-fataliste |
| Augustin | *City of God* V 9-10; *De Libero Arbitrio* III | réception du cylindre et prescience |
| Calcidius et Jean Damascène | *in Timaeum* 162; *De fide orthodoxa* II 30 | futurs contingents et prescience |

## 6. Candidats KG existants

Les identifiants ci-dessous existaient au moment de l'audit. Ils sont des destinations possibles, jamais des cibles modifiées ici.

| Candidat existant | Correspondance avec le PDF | Action recommandée avant ingestion |
|---|---|---|
| `person_sorabji_richard_contemporary` | auteur | ne pas utiliser sa notice Duckworth pour identifier automatiquement le scan Cornell |
| `pub_sorabji_1980_necessity_cause_blame` | oeuvre secondaire | séparer oeuvre abstraite et manifestation locale Cornell; revoir ISBN et éditeur du fichier |
| `scholarly_position_sorabji_aristotle_indeterminist` | SOR-C02, C05-C09 | meilleur candidat pour le noyau de la lecture; ajouter des ancres visuelles distinctes, sans cause non causée |
| `argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188` | SOR-C07, B01-B03 | conserver les nuances entre *NE*, *EE* et *NE* V; ne pas en faire une synthèse textuelle unique |
| `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` | SOR-C07, S05 | scinder clairement lecture aristotélicienne, lecture stoïcienne et interprétations modernes |
| `argument_voluntary_involuntary_distinction_aristotle_g7h8i9j0` | SOR-B01-B03 | ajouter les variantes et l'équité, sans écraser la chronologie proposée |
| `argument_voluntary_vs_eph_hemin` | Alexandre contre Stoïciens | candidat pour la réception, mais réclame une source primaire séparée |
| `argument_sea_battle_aristotle_f6g7h8i9` et `concept_sea_battle_future_contingents` | SOR-E02, D01-D02, X04 | modéliser la lecture traditionnelle comme interprétation de Sorabji, non solution incontestée d'Aristote |
| `argument_the_master_argument_kurieuon_logos_355f4d3f` | SOR-D01-D02 | retirer ou qualifier l'étiquette d'école mégarique; Sorabji suit Sedley contre cette attribution |
| `argument_chrysippus_causal_taxonomy` | SOR-C03, S04 | corriger la relation entre causes externes nécessaires, causes internes et nécessité globale |
| `concept_stoic_causal_principle` | SOR-C03, X01 | bon candidat, mais l'attestation d'Alexandre doit rester secondaire et polémique |
| `argument_cylinder_analogy_chrysippus_k1l2m3n4`, `concept_cylinder_analogy_chrysippus_e5f6g7h8`, `quote_chrysippus_cylinder_1da2c55b` | SOR-S02e, S04 | ne pas choisir une seule des trois lectures discutées par Sorabji sans attribution |
| `argument_the_dog_and_cart_argument_9ba60714` | SOR-S01 | éviter de transformer le consentement sous nécessité en libre choix alternatif |
| `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6` et `debate_epicurus_free_will` | SOR-E01-E03 | affaiblir toute affirmation d'intention explicite d'Épicure; le livre rapporte surtout Lucrèce et Cicéron |
| `work_de_fato_alexander_c200ce_o6p7q8r9`, `passage_alexander_de_fato_14`, `passage_alexander_de_fato_15` | SOR-X01-X04 | relier comme sources primaires potentielles seulement après recollation grecque et édition Sharples/Bruns |
| `debate_alexander_stoics_determinism` | réception anti-stoïcienne | utile comme débat, mais sa description actuelle est plus affirmative que le présent livre |
| `debate_stoic_compatibilism` | SOR-S03-S06 | stocker `compatibilisme` comme catégorie analytique moderne et conserver le `perhaps` de Sorabji pour Chrysippe |
| `scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4` | contexte partiel en 1980, formulation explicite en 2017 | scinder les preuves et ne pas citer 1980 pour la formulation `Cicéron suit Lucrèce` |
| `scholarly_argument_sorabji_epicurus_on_freedom_and_respon_2` et `scholarly_argument_sorabji_lucretius_on_voluntas_and_the__3` | SOR-E01-E04 | le livre de 1980 apporte seulement les ancres limitées décrites ici; conserver les sources ultérieures séparées |
| `scholarly_argument_sorabji_four_strands_of_the_will_5` et `scholarly_argument_sorabji_freedom_and_the_will_in_ancien_0` | aucune attestation de leur thèse complète dans ce volume | interdire toute propagation automatique depuis la publication de 1980 |

### 6.1 Liste fermée des IDs directement affectés

Les corrections ou réserves de cet audit portent directement sur les IDs suivants, relevés tels quels dans le KG:

- Bibliographie et provenance: `person_sorabji_richard_contemporary`, `pub_sorabji_1980_necessity_cause_blame`.
- Position de Sorabji: `scholarly_position_sorabji_aristotle_indeterminist`.
- Aristote et `eph' hêmin`: `argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188`, `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7`, `argument_voluntary_involuntary_distinction_aristotle_g7h8i9j0`, `argument_voluntary_vs_eph_hemin`.
- Futurs contingents et Diodore: `argument_sea_battle_aristotle_f6g7h8i9`, `concept_sea_battle_future_contingents`, `argument_the_master_argument_kurieuon_logos_355f4d3f`.
- Causalité et compatibilisme stoïciens: `argument_chrysippus_causal_taxonomy`, `concept_stoic_causal_principle`, `argument_cylinder_analogy_chrysippus_k1l2m3n4`, `concept_cylinder_analogy_chrysippus_e5f6g7h8`, `quote_chrysippus_cylinder_1da2c55b`, `argument_the_dog_and_cart_argument_9ba60714`, `debate_stoic_compatibilism`.
- Épicure et Lucrèce: `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`, `debate_epicurus_free_will`, `scholarly_argument_sorabji_epicurus_on_freedom_and_respon_2`, `scholarly_argument_sorabji_lucretius_on_voluntas_and_the__3`.
- Alexandre: `work_de_fato_alexander_c200ce_o6p7q8r9`, `passage_alexander_de_fato_14`, `passage_alexander_de_fato_15`, `debate_alexander_stoics_determinism`.
- Conflation entre oeuvres de Sorabji: `scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4`, `scholarly_argument_sorabji_four_strands_of_the_will_5`, `scholarly_argument_sorabji_freedom_and_the_will_in_ancien_0`.

### 6.2 Nouveaux objets secondaires possibles

Si l'ontologie exige des claims séparés, les unités suivantes éviteraient les conflations:

1. `sorabji_caused_without_necessitated` - thèse philosophique propre, p. 26-32 et 232.
2. `sorabji_aristotle_no_fresh_start` - lecture de l'`archê`, p. 228-233.
3. `sorabji_stoic_eight_retreats` - classement exact, p. 71-85, avec huit enfants ordonnés.
4. `sorabji_chrysippus_cylinder_three_readings` - Augustin, Donini, Frede, p. 80-83.
5. `sorabji_hellenistic_novelty_persistence` - nouveauté hellénistique comme persistance, p. 247.
6. `sorabji_aristotle_three_voluntariness_accounts` - *NE* III, *EE* II, *NE* V, p. 257-259 et 272-275.
7. `sorabji_aristotle_negligence_fourfold` - classification de *NE* V 8, p. 278-281.
8. `sorabji_aristotle_legal_fairness` - contribution juridique, p. 288-295.

Ces objets doivent rester du type `scholarly_argument` ou équivalent, avec Sorabji comme auteur et les textes antiques comme objets discutés, non comme sources directement vérifiées.

## 7. Contradictions et risques observés

### P0 - Provenance et statut de preuve

1. `data/kg/e2_patches/sorabji.json` donne à un chemin se terminant par le nom du scan source un MD5 `e474ab...`, qui est en réalité celui du dérivé OCR de 79.2 MB. Le scan source actuel a le MD5 `fad192...` et 35.3 MB. Le fichier source et son OCR sont donc conflés dans cet artefact.
2. Le même patch marque plusieurs entrées `verified_against_ocr_version: true` et `verification_confidence: high`. Cela ne constitue pas une vérification visuelle. Aucun statut de preuve primaire ou de manifestation ne doit être hérité de ce champ.
3. Le noeud `pub_sorabji_1980_necessity_cause_blame` décrit `London: Duckworth`, alors que la manifestation locale montre Cornell University Press. Le BibTeX courant donne en plus ISBN `978-0226768243`, associé dans les données à une manifestation Chicago et qui n'est aucun des deux ISBN visibles sur le copyright Cornell. Oeuvre abstraite, édition Duckworth, manifestation Chicago et scan Cornell doivent être séparés plutôt que ramenés à une seule notice.

### P1 - Erreurs ou sur-résolutions sémantiques

1. Dans `data/kg/e2_patches/sorabji.json`, le contexte de `new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity` énumère mal les trois dernières stratégies. La sixième est la distinction causes internes/externes; la septième est la possibilité épistémique; la huitième est la non-nécessité par cessation supposée du vrai. Carnéade et la négation générale de l'implication causé-nécessité ne sont pas les stratégies 7 et 8 du classement.
2. `concept_cylinder_analogy_chrysippus_e5f6g7h8` affirme que l'assentiment est fatal mais non nécessaire. Sorabji ne fixe pas cette solution: il distingue trois interprétations, souligne leurs difficultés, et conclut à l'échec des retraits stoïciens.
3. `argument_chrysippus_causal_taxonomy` dit que les actions sont nécessitées seulement par les causes auxiliaires. Chez Sorabji, les causes externes sont des conditions nécessaires, non suffisantes; l'état interne est cause de l'assentiment; la question de la nécessité globale reste précisément litigieuse.
4. `argument_the_master_argument_kurieuon_logos_355f4d3f` classe Diodore dans l'école mégarique. Sorabji, suivant Sedley, dit que cette attribution universelle a été réfutée et préfère `dialecticien`.
5. `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` mélange une lecture aristotélicienne bilatérale, une lecture stoïcienne causative et la thèse moderne selon laquelle Aristote ne serait pas indéterministe. Le présent livre défend justement l'indéterminisme aristotélicien; les attributions doivent être segmentées par auteur moderne.
6. `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6` affirme sans précaution qu'Épicure introduit explicitement le clinamen pour fonder liberté et responsabilité. Le présent livre atteste seulement que le clinamen est ainsi présenté dans Lucrèce, puis rapporte l'objection d'aléatoire; la formulation forte exige d'autres preuves primaires.
7. `argument_the_dog_and_cart_argument_9ba60714` parle d'un choix d'attitude. Le texte de Sorabji parle d'un chien volontaire qui combine son consentement avec la nécessité, ou d'un chien non volontaire tout de même soumis. `Choix` risque d'introduire l'alternative que l'analogie ne garantit pas.
8. `scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4` assemble Sorabji 1980 et Sorabji 2017. Le claim que Cicéron suit Lucrèce appartient explicitement au texte de 2017; le livre de 1980 n'offre que le contexte stoïcien, le clinamen lucrétien et les témoignages cicéroniens. Les deux oeuvres doivent rester distinctes.

### P2 - Risques historiographiques

1. La thèse de la `persistance` hellénistique, p. 247, est une position de Sorabji contre Huby, Ross, Furley et d'autres. Elle ne doit pas devenir une date consensuelle de naissance du problème.
2. La lecture de *De Interpretatione* 9 par un déficit de valeur de vérité est qualifiée de `traditionnelle` par Sorabji, mais il précise que des lectures rivales sont presque aussi anciennes. Le noeud doit porter le désaccord.
3. Les témoignages sur Chrysippe viennent largement de Cicéron, Alexandre, Plutarque, Eusèbe, Némésius et Aulu-Gelle. Leur caractère indirect et parfois hostile doit être encodé.
4. L'attribution de portions de la *Mantissa* et de *Quaestiones* à Alexandre est expressément incertaine dans le livre.
5. L'exemple du jouet est de Sorabji. Le présenter comme passage aristotélicien serait une fabrication de source.
6. La p. 257 permet de dire que Sorabji oppose l'analyse aristotélicienne aux actes stoïciens d'assentiment et aux volitions ultérieures. Elle ne suffit pas, seule, à importer la généalogie des quatre composantes de la volonté exposée dans les écrits ultérieurs de Sorabji.
7. `data/goals/g5_deep/read_sorabji.md` contient un ancien `critical flag` sur Sorabji 2017 qui est explicitement rétracté ailleurs dans `CORRECTIONS_VS_QUICKPASS.md` et `verified_B.md`. Cet ancien dossier ne doit pas servir d'autorité cumulative sans appliquer sa rétractation.

## 8. Lacunes restantes

1. Aucun numéro de tirage n'est visible; la manifestation ne peut être datée plus précisément que `Cornell paperback, 1983 ou après`.
2. Le présent audit n'a pas consulté de catalogue externe pour réconcilier Cornell, Duckworth, Bristol Classical Press et l'ISBN `978-0226768243`.
3. Aucune source antique n'a été recollée ici dans son édition primaire. Les loci sont des pointeurs fournis par Sorabji.
4. Les fragments d'Épicure *On Nature* 31.27 et 34.27 doivent être contrôlés séparément; ils servent à deux arguments différents.
5. La numérotation implicite des p. 1-2 et de certains folios liminaires est certaine par séquence, mais non visible; toute donnée disant `folio imprimé observé` serait fausse.
6. Le grec polytonique de l'OCR n'est pas fiable. Les formes grecques destinées au corpus doivent venir d'une édition primaire ou d'une collation visuelle dédiée.
7. Les chapitres 10-12 n'ont pas fait l'objet d'une extraction de claims, car leur noyau porte sur téléologie biologique, sélection naturelle et nécessité des essences. Une future mission sur causalité naturelle ou téléologie devra les relire visuellement en profondeur.
8. La bibliographie est sélective et Sorabji renvoie aux notes pour le détail. Elle ne doit pas être traitée comme inventaire exhaustif de la littérature en 1980.

## 9. Plan d'ingestion fail-closed

### Étape 0 - Corriger la provenance avant tout contenu

- Conserver deux manifestations distinctes: scan source et dérivé OCR, chacune avec son SHA-256.
- Relier l'OCR par `derivative_of` sans lui transférer l'autorité visuelle.
- Créer ou réparer une manifestation Cornell distincte de l'oeuvre abstraite Sorabji 1980.
- Laisser l'édition/tirage exact en statut incertain jusqu'à preuve catalographique ou numéro d'impression.

### Étape 1 - Ingestion secondaire atomique

Pour chaque ID SOR ci-dessus, stocker au minimum:

- `publication_id`: oeuvre Sorabji 1980;
- `manifestation_sha256`: hash du scan source;
- chapitre;
- page imprimée et page PDF;
- paraphrase courte;
- rôle: `Sorabji_position`, `Sorabji_reconstruction`, `ancient_report` ou `Sorabji_critique`;
- `evidence_mode`: `secondary_visual_page`;
- `primary_source_verified: false`;
- liste des loci antiques comme cibles de recollation, non comme attestations déjà validées.

Priorité d'ingestion: SOR-C02, C05-C09; SOR-S02 à S02g, S03-S05; SOR-A01-A04; SOR-B01-B08; SOR-X01-X04; SOR-E01-E04.

### Étape 2 - Quarantaines sémantiques

- Mettre en revue les noeuds du cylindre avant de leur ajouter une nouvelle preuve.
- Mettre en revue l'énumération erronée des huit stratégies dans le patch Sorabji.
- Mettre en revue le noeud du Maître Argument pour l'attribution mégarique.
- Mettre en revue le noeud de manifestation bibliographique pour Cornell/Duckworth/ISBN.
- Scinder les claims 1980 et 2017 actuellement fusionnés.

### Étape 3 - Recollation primaire

Ordre recommandé:

1. Aristote: *Int.* 9; *Metaph.* VI 2-3; *NE* III 1-5; *EE* II 6-10; *NE* V 8.
2. Cicéron: *De Fato* 12-23, 28-30, 39-45.
3. Alexandre: *De Fato* 8, 10, 13-16, 22, 26, 30-38, avec édition et traduction explicites.
4. Épicure/Lucrèce: *On Nature* 31.27 et 34.27; *DRN* II 216-293.
5. Témoins stoïciens: Aulu-Gelle VII 2; Plutarque; Épictète II 19; Némésius 35.
6. Réception de la prescience: Ammonius, Proclus, Boèce et Origène.

Chaque recollation primaire doit pouvoir confirmer, restreindre ou contredire Sorabji; elle ne doit pas être préjugée par le claim secondaire.

### Étape 4 - Contrôles automatiques

- Test de bijection `printed_page + 17 = pdf_page` pour p. 3-326.
- Test que p. 1-2 et les folios supprimés ne sont jamais déclarés `visually_printed`.
- Test que le hash du scan n'est pas remplacé par le MD5/SHA de l'OCR.
- Test qu'aucun claim de Sorabji ne propage `primary_verified=true` aux loci antiques.
- Test que l'énumération stoïcienne contient exactement huit positions dans le bon ordre.
- Test anti-conflation des oeuvres Sorabji 1980 et 2017.
- Test de longueur des extraits pour rester conforme au droit d'auteur; la présente note ne contient aucune longue citation.

## 10. Conclusion opérationnelle

Le PDF est exploitable comme source secondaire paginée et visuellement contrôlée. Il ne faut pas le traiter comme un texte OCR natif ni comme une preuve primaire des doctrines antiques. Les meilleurs apports à ingérer sont la séparation cause/nécessitation, le refus des `fresh starts`, le classement exact des huit stratégies stoïciennes, la tripartition des lectures du cylindre, la thèse historiographique de la persistance hellénistique et l'analyse différenciée des régimes aristotéliciens du volontaire et du blâme.

Avant ingestion, trois réparations sont impératives: séparer Cornell de Duckworth au niveau manifestation, séparer scan et OCR dans la provenance, et corriger les sur-résolutions actuelles sur les huit stratégies et le cylindre. Jusqu'à ces réparations, aucun statut global `verified` ne devrait être déduit de l'ancien patch OCR.
