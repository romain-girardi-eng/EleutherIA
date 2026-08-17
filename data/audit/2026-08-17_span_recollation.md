# Re-collation à empans alignés — First1KGreek et Perseus/web (17 août 2026)

## Résultat exécutif

La re-collation lève l'indétermination du rapport stratifié initial. Les 49 passages classés
`SUBSTANTIVE` dans les strates First1KGreek (37) et Perseus/web (12) ont tous reçu un empan
d'autorité crédible : **0 `UNALIGNABLE`**. Les SHA-256 bruts consignés dans l'audit initial
correspondent aux 49 textes de corpus relus.

Le désalignement d'empans expliquait bien plusieurs valeurs extrêmes — le cas témoin Épicure,
*SV* 56, passe de 64,375 % à **0/57 lettres**, sur les octets TLG `[85408, 85491)` — mais il
masquait aussi des divergences internes réelles. En particulier, les 24 passages de Sextus
Empiricus sont des sous-séquences trouées de l'autorité TLG : des ancres exactes ordonnées se
poursuivent avant et après des mots ou propositions absents du corpus. Ce ne sont donc pas de
simples différences de bornes.

Sur les seuls passages re-collationnés :

| Strate | n | ALIGNED_EXACT | ALIGNED_MINOR | ALIGNED_SUBSTANTIVE | UNALIGNABLE | CER médian intra-empan |
|---|---:|---:|---:|---:|---:|---:|
| Perseus/web | 12 | 0 | 4 | 8 | 0 | 1,51 % |
| First1KGreek | 37 | 0 | 4 | 33 | 0 | 11,38 % |

En réintégrant les verdicts `MINOR` de l'audit initial qui n'avaient pas à être re-collationnés
(9 Perseus/web et 3 First1KGreek), le tableau corrigé qui remplace les deux lignes inconclusives
est :

| Strate | n | EXACT | MINOR corrigé | SUBSTANTIVE corrigé | INDISPO | IC Wilson 95 % (subst./n) | CER médian des cas collatables |
|---|---:|---:|---:|---:|---:|---|---:|
| Perseus/web | 40 | 0 | **13** | **8** | 19 | **[10,5 % ; 34,8 %]** | **0,28 %** (n=21) |
| First1KGreek | 40 | 0 | **7** | **33** | 0 | **[68,1 % ; 91,3 %]** | **10,60 %** (n=40) |

`MINOR corrigé` signifie ici « aucun écart lexical non éditorial établi ». `SUBSTANTIVE corrigé`
signifie « au moins une forme lexicale ou un mot diverge à l'intérieur des deux bornes alignées » ;
ce verdict constate une divergence de témoin et ne décide pas, à lui seul, quelle édition a raison.

## Méthode

1. Chaque `corpus_passage_id` a été relu dans `data/corpus/passages.jsonl` et contrôlé contre le
   SHA-256 brut de l'enregistrement initial : 49/49 concordent.
2. Pour les fichiers TLG E, le flux bêta-code a été réduit aux lettres de base avec une table
   lettre→octet, selon l'approche éprouvée des scripts de ré-ingestion : les octets d'état de
   citation, accents et balises ne participent pas à l'ancre. Les autorités latines SCO/LLT ont
   reçu le même traitement lettre→position.
3. Des ancres exactes de 32 lettres ont été cherchées dans le locus déjà enregistré, puis ordonnées.
   Les extrémités ont été affinées par alignement local flou. Les empans publiés sont des intervalles
   d'octets semi-ouverts `[début, fin)` ; ils ne sont jamais extrapolés depuis la seule citation TLG.
   Les deux exports latins locaux sont ASCII : leurs positions de caractères initiales coïncident
   donc exactement avec les octets publiés.
4. Le CER intra-empan vaut distance de Levenshtein des lettres de base / nombre de lettres de base
   de l'autorité alignée. Les accents, esprits, casse, ponctuation, espaces et césures de ligne ne
   contribuent pas à ce CER, mais restent inspectés pour qualifier `ALIGNED_MINOR`.
5. Une différence de balise, d'apparat, d'accent, d'élision, de ponctuation ou d'orthographe
   intralexicale non sémantique est `ALIGNED_MINOR`. L'ajout, la suppression, le déplacement ou la
   substitution d'un mot — y compris un article ou une préposition — est `ALIGNED_SUBSTANTIVE`.
6. Si une borne du corpus tombe au milieu d'un mot de l'autorité, les lettres externes à l'empan
   aligné sont comptées séparément et ne gonflent pas le CER intra-empan.

Les 49 constats complets, avec anciens locators, octets alignés, longueurs, distances, classes de
différence et preuves, sont dans `2026-08-17_span_recollation.jsonl`. Aucun texte du corpus ou de
l'autorité n'a été modifié.

## Troncatures de bornes, séparées du corps du texte

Huit passages First1KGreek tombent au milieu d'un mot TLG ; aucun passage Perseus/web re-collationné
ne le fait. Les formes ci-dessous sont données en lettres de base, sans accents.

| Passage | Borne | Lettres TLG hors empan | Lecture |
|---|---|---:|---|
| `passage_sext_167` | début | 3 `λευ` | le corpus commence à `καντικως` dans `λευκαντικως` |
| `passage_sext_141` | début | 2 `ευ` | le corpus commence à `ρισκομενου` dans `ευρισκομενου` |
| `passage_sext_53` | fin | 7 `κειμενα` | le corpus s'arrête à `υπο` dans `υποκειμενα` |
| `passage_sext_27` | fin | 5 `σουσι` | le corpus s'arrête à `φη` dans `φησουσι` |
| `passage_sext_512` | début | 8 `αρρενογο` | le corpus commence à `νιαν` dans `αρρενογονιαν` |
| `passage_sext_236` | début | 3 `πρω` | le corpus commence à `τως` dans `πρωτως` |
| `passage_sext_505` | début | 5 `καταν` | le corpus commence à `αλισκειν` dans `καταναλισκειν` |
| `passage_sext_142` | fin | 4 `τικη` | le corpus s'arrête à `σωμα` dans `σωματικη` |

Ces défauts de bord doivent être réparés comme tels ; ils ne sont pas la preuve utilisée pour les
verdicts substantiels ci-dessous, qui reposent tous sur au moins une divergence **interne**.

## Cas ALIGNED_MINOR

| Passage | CER | Classes et preuve |
|---|---:|---|
| `passage_just_tryph_43_5` | 0,279 % | orthographe du nom `Δαυΐδ` / `Δαυείδ`; marqueur éditorial `[fol. 93]`; accents et ponctuation |
| `passage_lucr_drn_10511075_s291` | 16,456 % brut, **0 % textuel** | huit cartouches `[lib.: …, versus: …, pag.: …]` et code d'interface `instrumentaModal`; les 924 lettres du poème concordent |
| `passage_plato_laws_6_758` | 0,120 % | les deux lettres sont le sigle de locuteur corpus `ΑΘ.`; de `οὕτω δὴ` à la fin, les lettres de base concordent |
| `passage_dl_lives_2_3_13` | 1,880 % | les onze lettres supplémentaires sont les sigles d'apparat TLG `[φγρη φ]` et `[φηγ iii]` |
| `passage_epicur_71` | 0,195 % | une lettre intralexicale : `παρακολουθοῦντος` / `παρακολυθοῦντος` |
| `passage_arist_phys_7_3` | 0,244 % | onze changements intralexicaux sur 4 522 lettres, p. ex. `παρωνυμιμμάζοντες` / `παρωνυμιάζοντες`; aucune proposition absente |
| `passage_epicur_91` | 2,169 % | conjecture éditoriale corpus `〈καὶ σελήνης〉` absente du TLG, plus accents/ponctuation |
| `passage_epicur_56_s168` | **0 %** | 57/57 lettres : `〈ἢ στρεβλουμένου〉` / `[ἢ στρε-βλουμένου]`; seules les marques éditoriales changent |

### Adjudication de l'outlier Perseus/web à 16,5 %

Le cas est `passage_lucr_drn_10511075_s291`, Lucrèce 6.1051–1075. Le CER brut de **16,455696 %**
est exactement reproductible : 182 lettres existent dans l'export LLT mais pas dans le corpus.
Elles appartiennent toutes aux huit cartouches de navigation et à une chaîne de code d'interface
injectée entre les vers. Après retrait logique de ce matériel non textuel — sans modifier aucun
fichier — les 924 lettres latines du poème concordent exactement, soit un CER textuel de **0 %**.
Verdict : `ALIGNED_MINOR`, pas erreur de Lucrèce. Action recommandée : filtrer ces motifs dans le
comparateur d'autorité, jamais dans le texte-source conservé.

## Cas ALIGNED_SUBSTANTIVE — Perseus/web

Chaque cas est cité individuellement. L'action proposée exige une vérification du témoin déclaré ;
aucun remplacement automatique par TLG n'est recommandé.

- `passage_plotinus_iv_3_10` — CER 1,974 %. Corpus : « πῶς δὲ **καὶ** σύμφωνον
  ἑαυτοῖς **λέγουσι**; λέγουσι γὰρ » ; TLG : « Πῶς δὲ σύμφωνον ἑαυτοῖς; Λέγουσι γὰρ ».
  Action : comparer Perseus à Henry–Schwyzer, puis documenter la variante ou corriger le témoin
  d'ingestion déclaré.
- `passage_plotinus_ii_1_1` — CER 0,894 %. Corpus : « τοῖς μὴ ἀποδεξαμένοις … ἐρῶσι » ;
  TLG : « μὴ τοῖς ἀποδεξαμένοις … ὁρῶσι ». Action : arbitrage d'édition Plotin, sans substitution
  silencieuse.
- `passage_tert_exhort_cast_9` — CER 2,166 %. Corpus : « non suggillaret), **et** de cultu » ;
  autorité SCO : « non suggillaret), **sed** de cultu ». Le `canonical_ref` du passage de corpus
  indique en outre `Adv. Marc. 9`, alors que l'identifiant et l'autorité visent *De exhortatione
  castitatis* 9. Action : contrôler d'abord la provenance/référence, puis la leçon `et/sed`.
- `passage_dl_lives_4_9_62` — CER 7,366 %. Le corpus passe directement à « φιλόπονος δ' ἄνθρωπος » ;
  le TLG porte auparavant « εἰ μὴ γὰρ ἦν Χρύσιππος, οὐκ ἂν ἦν ἐγώ ». Action : vérifier le XML
  Perseus ; réingérer l'unité si la phrase appartient bien au passage déclaré.
- `passage_just_tryph_76_1` — CER 1,355 %. Corpus : « ἐκτετμῆσθαι **δηλοῖ** ὅτι » ; TLG :
  « ἐκτετμῆσθαι, ὅτι ». Action : vérifier l'édition source de Justin et enregistrer la variante.
- `passage_plotinus_i_5_8` — CER 1,669 %. Corpus : « τῶν **ἐναντίων** λυπούντων » ; TLG :
  « τῶν λυπούντων » ; le TLG ajoute aussi `ἄν` après `καταχρώμενος`. Action : arbitrage d'édition.
- `passage_just_tryph_56_3` — CER 0,690 %. Corpus : « **ὑπὸ** τοῦ ἁγίου πνεύματος » ; TLG :
  « **ἀπὸ** τοῦ ἁγίου πνεύματος ». Action : vérifier le témoin Perseus/édition ; la préposition est
  une divergence lexicale malgré le faible CER.
- `passage_plotinus_v_2_2` — CER 0,532 %. Corpus : « πρὸς τὸ κρεῖττον καὶ **τὸ** ἀγαθόν » ; TLG :
  « πρὸς τὸ κρεῖττον καὶ ἀγαθόν » ; autres articles diffèrent près de `ψυχή/ἔρως`. Action :
  arbitrage d'édition et note de variante.

## Cas ALIGNED_SUBSTANTIVE — First1KGreek

Les citations de Sextus données « en base-letter » reproduisent exactement les mots identifiés par
le diff après neutralisation des accents ; l'absence d'accents n'est donc pas une reconstruction.

- `passage_greg_naz_010_5` — CER 0,076 %. Corpus « καὶ Χριστὸς » ; TLG « καὶ **ὁ** Χριστὸς ».
  Action : contrôler le XML First1K et l'article avant toute correction.
- `passage_sext_350` — CER 22,348 %. Corpus ∅ ; TLG « ἡμᾶς πλανᾶν· τὸ γὰρ οὗτοι ἔγημαν δύο
  σημαίνει, ἓν μέν ». Action : réingérer le passage depuis le témoin First1K déclaré, puis recoller.
- `passage_sext_167` — CER 12,624 %. Corpus ∅ ; TLG « φαντασίας καὶ τῆς δόξης, τούτων τὴν
  φαντασίαν ». Action : réingestion First1K ; réparer aussi le début tronqué de 3 lettres.
- `passage_sext_210` — CER 11,919 %. Corpus ∅ ; TLG base-letter « μόνον οὐχ ὑπάρξει δὲ καὶ
  ἄλλως ». Action : réingestion First1K et contrôle de complétude des tokens.
- `passage_sext_207` — CER 14,767 %. Corpus ∅ ; TLG « σχολικῶς ἔοικε πλάττεσθαι ».
  Action : réingestion First1K.
- `passage_sext_141` — CER 8,094 %. Corpus ∅ ; TLG base-letter « τῶν ὑπάρχειν περὶ κριτηρίου ».
  Action : réingestion First1K ; réparer séparément les 2 lettres initiales.
- `passage_sext_53` — CER 17,262 %. Corpus ∅ ; TLG « ἵνα δὲ αἱ διάνοιαι δοκιμασθῶσι ».
  Action : réingestion First1K ; restaurer séparément les 7 lettres finales du mot coupé.
- `passage_sext_27` — CER 10,842 %. Corpus ∅ ; TLG base-letter « περὶ ἀμφοτέρων ἐπέχομεν ».
  Action : réingestion First1K ; restaurer séparément la fin `σουσι`.
- `passage_sext_324` — CER 14,316 %. Corpus ∅ ; TLG « ζητητέον τὸ μῆνιν καὶ τὸ ἄειδε καὶ τὸ θεά
  καὶ τὸ Πηληϊάδεω ». Action : réingestion First1K.
- `passage_sext_512` — CER 15,124 %. Corpus ∅ ; TLG « ταῦρος δέ, φασί, θηλυκόν ».
  Action : réingestion First1K ; restaurer séparément le préfixe initial `αρρενογο`.
- `passage_sext_253` — CER 11,376 %. Corpus ∅ ; TLG base-letter « ἀλλ' ὅτι κατ' ἐπίνοιαν τοιαύτη
  τυγχάνει ». Action : réingestion First1K.
- `passage_epicur_59` — CER 0,677 %. Corpus « πρώτων … ἀμετάβολα » ; TLG « πρῶτον …
  ἀμετάβατα ». Action : vérifier l'édition First1K ; deux flexions/formes lexicales diffèrent.
- `passage_sext_268` — CER 9,938 %. Le corpus seul porte, en base-letter, « μὴν πυροὶ … ὁρῶμεν
  γὰρ … συμπνοίαν ». Action : réingestion First1K après contrôle du locus, car l'écart est ici une
  addition corpus et non seulement une omission.
- `passage_sext_57` — CER 15,874 %. Corpus ∅ ; TLG base-letter « τάδε δὲ ψευδῆ, εἰ μὲν γὰρ
  διαφαινομένου ». Action : réingestion First1K.
- `passage_epicur_3` — CER 18,085 %. Corpus « τὸ δὲ **μέσον** … 〈οὐ〉 … **ὑπάρχει** » ; TLG
  « τὸ δὲ **μόνον** … **συμβαίνει** » et ajoute `συνεχῶς`. Action : collation philologique ciblée ;
  ne pas écraser une éventuelle leçon d'édition sans provenance.
- `passage_just_apol1_40` — CER 1,007 %. Le corpus répète `αἰτῶν` là où le TLG porte `αὐτῶν`,
  avec d'autres formes manifestement dégradées (`τοῖ`, `μσυ`, `ἑν`). Action : réingérer le passage
  depuis le XML First1K et contrôler les entités/diacritiques.
- `passage_sext_295` — CER 10,360 %. Corpus ∅ ; TLG « τῶν ἀνθρώπων μὲν ὑπαρχόντων ».
  Action : réingestion First1K.
- `passage_epicur_43` — CER 0,285 %. Corpus `ἴσχουσαι` ; TLG `ἰσχῦσαι`. Action : contrôler la
  morphologie dans l'édition First1K et consigner la leçon retenue.
- `passage_epicur_100` — CER 0,887 %. Corpus `κινουμένων` ; TLG `κινουμένου`, et le TLG ajoute
  `καί`. Action : arbitrage d'édition ciblé.
- `passage_sext_78` — CER 13,685 %. Corpus ∅ ; TLG base-letter « αἱ εἰσὶν, ἔφη, μὴν
  ἑτεροιούμενα ». Action : réingestion First1K.
- `passage_sext_71` — CER 14,017 %. Corpus ∅ ; TLG base-letter « οὕτω λεγόμενον· ἡ ἡμέρα ἐστὶ
  φῶς ». Action : réingestion First1K.
- `passage_sext_236` — CER 10,268 %. Corpus ∅ ; TLG « οὔτε θερμὸν οὔτε ψυχρὸν οὔτε γλυκὺ
  οὔτε πικρόν ». Action : réingestion First1K ; réparer séparément le préfixe initial `πρω`.
- `passage_sext_529` — CER 9,495 %. Corpus ∅ ; TLG base-letter « οἵ τε δελφῖνες, ὡς λόγος ».
  Action : réingestion First1K.
- `passage_sext_505` — CER 14,323 %. Corpus ∅ ; TLG « οὔτε δὲ σῶμα δύναται τυγχάνειν ».
  Action : réingestion First1K ; réparer séparément le préfixe `καταν`.
- `passage_sext_181` — CER 14,444 %. Corpus ∅ ; TLG « οἷον τὸ σχῆμα, τὸ μέγεθος, τὴν χρόαν —
  ναί, φήσει τις ». Action : réingestion First1K.
- `passage_sext_12` — CER 15,587 %. Corpus ∅ ; TLG base-letter « τὴν θηρευτικήν· ἔστι δὲ οὐδ'
  ἀρετῆς ἐκτός ». Action : réingestion First1K.
- `passage_greg_naz_008_2` — CER 0,122 %. Corpus « τούτων **ἀπ' ἀποχωρήσας** » ; TLG
  « τούτων **ἀποχωρήσας** ». Action : vérifier une duplication d'élision à l'ingestion First1K.
- `passage_sext_244` — CER 16,539 %. Corpus ∅ ; TLG « ἐστὶν, οὐδὲ ἀξίωμα, τὸ σημεῖον. ἄλλως
  τε, καθὼς ». Action : réingestion First1K.
- `passage_eusebius_praep_ev_book_15` — CER 4,022 % sur 95 328 lettres TLG. Corpus
  « οὐ ἀλλὰ … ἐξῆς … ἔπιδ' ἐπιδεικνύς » ; TLG « οὐ μὴν ἀλλὰ … ἑξῆς … ἐπιδεικνύς » ; des titres
  de section TLG sont aussi intercalés. Action : reconstruire le livre depuis le XML First1K en
  séparant titres et texte, puis refaire une collation par chapitres.
- `passage_sext_3` — CER 17,650 %. Corpus ∅ ; TLG « καὶ ἡ “οὐδέν ἐστιν ἀληθές” … καὶ ἡ
  “οὐδὲν μᾶλλον” ». Action : réingestion First1K.
- `passage_sext_85` — CER 16,726 %. Corpus ∅ ; TLG « ἀλλὰ τἀληθῆ ζητεῖν, ὡς ὑπισχνοῦνται,
  προῄρηνται ». Action : réingestion First1K.
- `passage_arist_di_8_2` — CER 2,752 %. Le corpus ajoute une première occurrence de « οὐδὲ
  ἀπόφασις μία » ; `δυοῖν` / `δυεῖν` diffère aussi. Action : vérifier la structure du XML First1K et
  l'apparat avant de supprimer ce qui peut être une leçon éditoriale.
- `passage_sext_142` — CER 12,921 %. Corpus ∅ ; TLG base-letter « ὑφ' οὗ γίνεται ἡ κρίσις ».
  Action : réingestion First1K ; réparer séparément la fin de mot `τικη`.

## Taux corrigé et formulation pour le data paper

Dans l'échantillon stratifié complet de 160 passages, la lecture corrigée compte **41 divergences
lexicales substantielles intra-empan** : 33 First1KGreek, 8 Perseus/web, 0 SC et 0 dans la population
TLG de texte réingéré après la lecture critique déjà publiée. Le taux descriptif est donc
**41/160 = 25,6 %** ; parmi les 141 passages pour lesquels une autorité locale était collatable,
il est **41/141 = 29,1 %**. Ces nombres mesurent la divergence au témoin local, non la « fausseté »
philologique.

La somme des tailles de strate enregistrées dans les 160 lignes est **11 827**
(1 267 + 1 164 + 8 255 + 1 141), et non « environ 14 900 ». Avec ces poids, et en comptant par
convention les 19 autorités Perseus indisponibles comme zéro divergence, l'estimateur pondéré vaut
**21,9 %**. C'est une **borne descriptive basse**, pas un taux d'erreur universel : près de la moitié
de la strate Perseus/web est non observée et les 40 contrôles SC ne sont pas indépendants de
l'ingestion.

Formulation anglaise directement réutilisable :

> Span-aligned adjudication identified substantive within-span lexical divergence in 41 of 160
> sampled passages (25.6%), or 41 of 141 passages with a locally collatable authority (29.1%).
> Using the recorded stratum frame sizes yields a 21.9% design-weighted lower-bound estimate when
> the 19 unavailable Perseus/web authorities are conservatively counted as non-errors. These rates
> measure divergence from the selected local witnesses, not universal philological incorrectness;
> the SC comparisons were non-independent and the unavailable Perseus/web authorities prevent an
> unbiased corpus-wide error estimate.

## Guide exact de mise à jour de `docs/paper/eleutheria_data_paper_draft.md`

Ne pas modifier le papier automatiquement. Les changements à effectuer dans la section
« Stratified post-repair verification » sont les suivants :

1. Paragraphe d'ouverture : remplacer **“approximately 14,900 eligible records”** par
   **“11,827 eligible records across the four recorded sampling frames”**. Les quatre tailles
   inscrites dans le JSONL sont 1 267, 1 164, 8 255 et 1 141.
2. Ligne `Perseus/web` du tableau : remplacer
   `40 | 0 | 9 | 12 | 19 | [18.1% ; 45.4%] | 1.8%`
   par
   `40 | 0 | 13 | 8 | 19 | [10.5% ; 34.8%] | 0.3%`.
3. Ligne `First1KGreek` du tableau : remplacer
   `40 | 0 | 3 | 37 | 0 | [80.1% ; 97.4%] | 21.0%`
   par
   `40 | 0 | 7 | 33 | 0 | [68.1% ; 91.3%] | 10.6%`.
4. Après le tableau, préciser que les colonnes corrigées incorporent l'adjudication humaine à
   empans alignés, alors que les lignes SC et TLG conservent la lecture critique antérieure.
5. Dans le paragraphe interprétatif, remplacer **“one outlier requiring item-level review”** par
   l'adjudication Lucrèce : CER brut 16,5 %, CER textuel 0 %, toutes les 182 éditions venant des
   cartouches LLT et du code d'interface.
6. Remplacer la phrase déclarant First1KGreek « non-conclusive until passages are re-collated » par
   les résultats : **33/40 substantiels**, dont **24/24 Sextus** avec omissions lexicales internes ;
   **7/40 minor** ; **8** troncatures de bord mesurées séparément ; *SV* 56 à **0/57** lettres.
7. Ajouter la formulation de taux corrigé ci-dessus : **41/160 (25,6 %)**, **41/141 (29,1 %)**
   parmi les collatables, et **21,9 %** comme borne basse pondérée sous la convention explicite des
   19 indisponibles.
8. Dans la section des limites, remplacer **“First1KGreek requires span-aligned re-collation”** par
   une phrase indiquant que la re-collation est achevée, que 33 divergences lexicales First1KGreek
   sont établies, et que l'indisponibilité Perseus ainsi que la non-indépendance SC interdisent
   toujours d'interpréter 21,9 % comme un taux universel de correction philologique.

## Décision opérationnelle

- **First1KGreek/Sextus** : priorité haute à une réingestion groupée des 24 passages depuis les XML
  First1K déclarés, avec garde de complétude tokenisée et nouvelle collation TLG ; ne pas combler les
  lacunes en copiant le TLG.
- **Autres First1KGreek substantiels** : contrôles ciblés de source/édition, puis réingestion seulement
  si le témoin déclaré confirme une perte ou une corruption d'extraction.
- **Perseus/web substantiels** : enregistrer les variantes d'édition et corriger uniquement contre la
  source d'ingestion déclarée ; traiter séparément l'anomalie de provenance Tertullien.
- **Bords** : vague indépendante pour les huit troncatures, afin qu'une réparation de limite ne soit
  jamais confondue avec l'arbitrage du corps du texte.
- **Comparateur** : ignorer analytiquement les cartouches LLT et le code d'interface, tout en conservant
  intactes les autorités archivées.
