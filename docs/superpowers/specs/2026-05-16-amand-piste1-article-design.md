---
date: 2026-05-16
status: design v3 — scope tightened to 6 moral pivots, technical title, broadened bibliography, DH-arbiter meta-thesis explicit
title: "Algorithmic provenance analysis of six moral anti-fatalist pivots: testing Amand 1945's Carneadean attribution against the primary Stoic corpus"
author: Romain Girardi
affiliation: CEPAM-UMR 7264 (Université Côte d'Azur)
target_venue: Digital Humanities Quarterly (DHQ) primary; Digital Scholarship in the Humanities (DSH) secondary
target_length: 7,500-9,000 words + technical appendix (~1,500 words)
language: EN (DHQ-style, technical, international audience)
contribution_kind: scholarly arbitration via algorithmic provenance test
relates_to: Piste 1 (project memory) — "reproduire ET DÉPASSER Amand 1945"
meta_thesis: the digital humanities scholar with a structured corpus is a quantifiable arbiter between prose-based historiographical positions
---

# Design : article scholarly Carnéade vs Chrysippe

## 0. Pourquoi cette v2 (justification du pivot)

Le design v1 proposait de vérifier algorithmiquement *une* assertion isolée d'Amand (Phil 23 ↔ PE VI.11, p. 366). Cible : ~7-8k mots, modeste mais épistémiquement honnête.

Romain a objecté que cette v1 **n'incarne pas l'ambition originelle de Piste 1** telle que formulée en mémoire projet : « cartographier l'héritage anti-fataliste carnéadéen dans la patristique en quantifiant les chaînes de transmission via OWL-RL inference + proof chains. Reproduire **et dépasser** Amand 1945 par quantification mécanique des filiations qu'il assertait en prose discursive. »

**Pivot v2** : challenger directement une *thèse* d'Amand (pas une assertion isolée), avec un finding qui arbitrera entre deux scholars majeurs (Amand 1945 et Bobzien 1998) plutôt que de simplement opérationnaliser Amand. Le finding n'est plus *vérification* mais **arbitrage scholarly**.

## 1. Thèse centrale v3 (scope tightened)

Amand 1945 reconstruit six pivots moraux anti-fatalistes attribués à Carnéade (général, législation, vertu/vice, stimulants, futilité de l'action, piété). Cette attribution **académicienne externe** est partiellement contestée par Bobzien (1998, 2000, 2014) qui soutient que les arguments anti-fatalistes ont une **origine stoïcienne interne** plus ancienne, comme auto-critique de Chrysippe et de la tradition stoïcienne d'avant Carnéade.

Nous testons cette tension algorithmiquement en cherchant, pour chacun des six pivots moraux d'Amand, des parallèles antérieurs ou contemporains chez les stoïciens primaires (Chrysippe en priorité, Cleanthes, Posidonius, Panaetius) dans le KG EleutherIA. Le résultat — quel(s) pivot(s) ont un parallèle stoïcien net — arbitre empiriquement le débat Amand vs Bobzien sur le scope précis (les six topoi moraux) où les deux convergent comme objet.

**Hors scope (intentionnel)** : les cinq arguments antiastrologiques d'Amand (intro §II) et le septième pivot d'auto-réfutation pragmatique stoïcienne. Les premiers ciblent l'astrologie spécifiquement (peu de parallèle stoïcien attendu) ; le second est par construction stoïcien (un argument *contre* le stoïcisme depuis le stoïcisme lui-même), donc circulaire pour ce test.

## 1bis. Méta-thèse épistémologique (explicit)

L'article pose en outre que **le scholar DH avec un corpus structuré et une méthode quantifiable peut arbitrer entre des positions historiographiques prose-fondées qui n'ont jamais été départagées par l'argumentation philologique seule**. Là où Amand 1945 et Bobzien 1998 débattent en prose depuis 28 ans (Bobzien 1998 → reprises 2000, 2014, 2021), une matrice de provenance quantifiable peut trancher empiriquement sur les claims où les données du corpus existent. Cette méta-posture épistémologique transforme le rôle du scholar : ni juste compilateur (état antérieur des DH), ni juste outil (état usuel), mais **arbitre quantifiable** entre scholarly positions classiques. La validité de cette posture est testée dans l'article même : si la matrice produit un résultat clair, la méta-thèse est validée ; si la matrice est ambiguë, la méta-thèse trouve ses limites.

## 2. Pourquoi c'est un finding non-circulaire et publiable

| Élément | Cadre | Statut épistémique |
|---|---|---|
| Le pivot d'Amand (e.g., « III. Vertu & vice ») | défini par Amand | **donnée d'entrée**, pas testée |
| L'attribution carnéadienne de ce pivot | défendue par Amand | **hypothèse à tester** |
| L'attribution stoïcienne alternative | défendue par Bobzien | **hypothèse alternative** |
| Notre matrice (pivot × stoïcien primaire avec parallèle) | construite indépendamment | **non-circulaire** — elle ne suppose ni Amand ni Bobzien |
| L'arbitrage final | dérivé de la matrice | **contribution scholarly** |

Aucune circularité : on ne prend pas les attributions d'Amand pour les valider ; on les confronte à un dataset Stoïcien indépendant (Chrysippe SVF + autres) construit dans le KG sans référence à la thèse carnéadienne.

## 3. Audience et venue

- **Audience primaire** : historiens de la philosophie antique + patristiciens + DH praticiens
- **Audience secondaire** : philosophes du libre arbitre contemporains (le débat Bobzien continue dans les revues philosophiques)
- **Venue cible** : DHQ ou DSH (DH-leaning) ; alternative *Phronesis* ou *Apeiron* si jugé suffisamment philosophique
- **Longueur** : ~7,500-9,000 mots + annexe technique
- **Langue** : décision déférée — FR pour DSH, EN pour DHQ/Phronesis

## 4. Plan d'article v2 (sections + word counts indicatifs)

### §1. Introduction (~800 mots)

- La controverse historiographique : 80 ans après Amand 1945, 28 ans après Bobzien 1998, le débat sur l'origine du discours anti-fataliste antique reste ouvert en prose.
- Amand 1945 : externe (Carnéade Académicien, témoins canoniques, règle 3/6).
- Bobzien 1998, 2000, 2014 : interne (auto-critique stoïcienne primaire — Chrysippe, antérieur à Carnéade).
- L'enjeu philosophique : la chronologie de l'émergence du « problème du libre arbitre » dans l'antiquité.
- La question opérationnelle : pour les six pivots moraux d'Amand, existe-t-il des parallèles stoïciens primaires antérieurs ou contemporains, mesurables dans un corpus structuré ?
- Méta-thèse : le scholar DH peut arbitrer là où la prose seule a échoué.

### §2. Background (~1,000 mots)

État du champ couvert : pas seulement Amand vs Bobzien, mais l'ensemble des positions pertinentes.

- **Amand 1945** : reconstruction du corpus carnéadien à partir des 6 témoins canoniques + règle 3/6. Six pivots moraux ciblés dans cet article (général, législation, vertu/vice, stimulants, futilité, piété).
- **Bobzien 1998** (*Determinism and Freedom in Stoic Philosophy*) : Chrysippe répond à des objections **internes** au stoïcisme (Diodore Cronos, Cleanthes lui-même), pas seulement à Carnéade. Le « problème » du libre arbitre comme tel émerge chez Alexandre d'Aphrodise (IIᵉ s. CE) en réaction au stoïcisme tardif, pas chez Carnéade.
- **Bobzien 2000** (*Did Epicurus Discover the Free Will Problem?*) : pas de problème du libre arbitre chez Épicure ; renforce la chronologie tardive de l'émergence.
- **Bobzien 2014** (*Choice and Moral Responsibility in NE III*) : Aristote a déjà la matière de l'« ἐφ' ἡμῖν » sans la transformer en « problem ». Mention contextuelle dans l'article — Aristote n'est pas le « père de tout » selon Bobzien, mais l'origine pré-stoïcienne du vocabulaire moral pertinent.
- **Frede 2011** (*A Free Will: Origins of the Notion in Ancient Thought*) : position médiane — pas chez Aristote, pas chez Carnéade, mais émergence stoïcienne post-Chrysippe puis fixation chez Alexandre + Origène.
- **Dihle 1982** (*The Theory of Will in Classical Antiquity*) : le concept de « volonté » émerge chez Augustin, pas avant. Position complémentaire qui structure la profondeur diachronique du débat.
- **Sharples 1983, 2001** (Alexander of Aphrodisias) : témoignage philologique sur la transmission Alexandre → tradition postérieure.
- **Long 1986, Sedley 1987, Inwood 1985** : histoire de la philosophie hellénistique (manuel & textes), arrière-plan obligé.
- **Eliasson 2008** : Plotinus et l'« ἐφ' ἡμῖν » néoplatonicien.
- **Kane 2011 éd.** (*Oxford Handbook of Free Will*) : actuel contemporain analytique.

Le point de divergence précis testable dans cet article : **les six pivots moraux anti-fatalistes d'Amand sont-ils originairement carnéadiens (externe) ou stoïciens-primaires (interne) ?**

### §3. Méthode (~1,400 mots)

- **Construction du dataset** :
  - Pivots d'Amand : 6 nodes Amand-tagged (les 6 moraux : `argument_carneadean_general_theme_amand1945`, `_legislation_`, `_virtue_vice_`, `_incentives_`, `_action_futility_`, `_piety_`), tels que reconstruits dans le KG EleutherIA (commits B1-B9, audit-verifié)
  - Dataset stoïcien primaire : Chrysippe (`person_chrysippus_*` + 32 arguments + 18 passages SVF + concepts associés), Cleanthes (1 argument + 2 passages), Posidonius (1 argument + 1 concept), Panaetius (1 argument)
  - Stoïciens tardifs (Epictète 694 passages, Sénèque 2339 passages, Marc Aurèle 615 passages) — utilisés comme contre-test : si un pivot a un parallèle SEULEMENT chez les stoïciens tardifs (post-Carnéade), ça n'arbitre pas — le parallèle peut être post-carnéadien.
  - **Hors scope** : 5 pivots antiastrologiques (Carnéade arg. I-V, ciblent l'astrologie) + 1 pivot auto-réfutation pragmatique stoïcienne (par construction stoïcien).
- **Algorithme de détection de parallèles** : pour chaque pair (pivot d'Amand, argument stoïcien), trois tests cumulatifs :
  1. **Test thématique** : tags concept partagés + chevauchement métadonnée `amand_pivot_label` vs argument stoïcien topic
  2. **Test conceptuel** : présence d'un concept commun (e.g., `concept_synkatathesis`, `concept_eph_hemin`, `concept_heimarmene_stoic`) discuté par les deux
  3. **Test textuel partiel** (optionnel) : si passages disponibles, recherche de termes-clés partagés (e.g., εἱμαρμένη, εφ' ἡμῖν, νόμος, ψόγος) avec normalisation polytonique
- Score par pivot : 0 (aucun parallèle stoïcien primaire), 1 (parallèle thématique seul), 2 (thématique + conceptuel), 3 (les trois).
- **Décision de classification** : un pivot est « possiblement non-exclusivement-carnéadien » si score ≥ 2 chez Chrysippe OU score ≥ 1 chez ≥ 2 stoïciens primaires distincts.
- **Reproductibilité** : code public + KG snapshot Zenodo. Le pipeline est déterministe (pas de LLM dans l'algorithme final).

### §4. Résultats (~1,800 mots)

- **Matrice principale** : 6 pivots moraux × 4 stoïciens primaires (Chrysippe, Cleanthes, Posidonius, Panaetius). Heatmap (figure principale).
- Pour chaque pivot, score par stoïcien primaire + score agrégé.
- **Classification per pivot** :
  - Pivots **clairement carnéadiens** (score ≤ 1 avec aucun stoïcien primaire) — Amand strictement défendable
  - Pivots **hybrides** (score ≥ 2 avec exactement 1 stoïcien primaire) — Bobzien partiellement défendable
  - Pivots **stoïciens d'origine** (score ≥ 2 chez ≥ 2 stoïciens primaires) — Bobzien fortement défendable
- **Cas-pivots détaillés** (zoom in sur 2-3 pivots où Amand et Bobzien divergent le plus nettement) :
  - Pivot III. Vertu & vice — Chrysippe SVF II (Galien, *De plac. Hipp. et Plat.*) discute déjà praise/blame sous déterminisme cylindrique
  - Pivot VI. Piété & religion — Cleanthes *Hymne à Zeus* contient-il déjà l'argument de la providence-fatum tension morale ?
  - Pivot I. Thème général — Posidonius (Diogène Laërce VII.149) sur l'εἱμαρμένη comme principe du cosmos
- **Sub-finding contextuel** : mention brève des contre-test (Epictète, Sénèque, Marc Aurèle) — si un pivot a un parallèle SEULEMENT chez les stoïciens tardifs, l'origine stoïcienne primaire n'est PAS établie (résultat compatible avec Amand).

### §5. Discussion (~1,500 mots)

- **Arbitrage Amand vs Bobzien sur les six pivots moraux testés** : sur les 6 pivots, M penchent vers Bobzien (parallèle stoïcien net), K penchent vers Amand (pas de parallèle stoïcien primaire), Z restent ambigus.
- **Croisement avec Frede 2011** : la matrice atteste-t-elle la position médiane de Frede (émergence stoïcienne post-Chrysippe + fixation chez Alexandre/Origène) ? L'ambiguïté est en soi un finding compatible avec Frede.
- **Croisement avec Dihle 1982** : pour les pivots qui touchent à la « volonté » (pivot III vertu/vice, pivot VI piété), Dihle pose Augustin comme origine. Notre matrice n'invalide pas — elle teste l'antériorité, pas l'émergence conceptuelle.
- **Implications philosophiques** : qu'est-ce que ça change pour la chronologie du libre arbitre antique ? Si certains arguments anti-fatalistes moraux ont un parallèle stoïcien primaire net, le « problème » émerge dans le stoïcisme avant Carnéade — confirmant Bobzien sur ces pivots précis. Si aucun parallèle, Amand est défendu pour ces pivots.
- **Reconnaissance des subtilités** : Amand ne nie pas tout précédent stoïcien ; il pose que **Carnéade systématise** l'argumentation. Notre matrice ne peut pas tester l'origine de la *systématisation* — seulement l'antériorité des matériaux. C'est une limite scholarly réelle qu'il faut nommer.
- **Méta-thèse en discussion** : la matrice est-elle un *arbitre* (validation de la méta-thèse) ou un *complément* (la méta-thèse trouve ses limites) ? Selon la clarté du résultat sortant. À discuter honnêtement.
- **Limites techniques** :
  1. Le dataset stoïcien primaire dans le KG (Chrysippe 32 args, Cleanthes 1, Posidonius 1, Panaetius 1) est **incomplet** par rapport à SVF intégral. Une partie du finding peut être due à l'incomplétude, pas à l'absence réelle. Mitigation : ingestion supplémentaire SVF avant submission.
  2. La notion de « parallèle » est définie par 3 tests cumulés mais reste flou philologiquement. Un philologue conservateur peut contester chaque match. Mitigation : publish per-pivot scores + validation manuelle d'échantillon.
  3. Le KG est construit par l'auteur ; les choix d'ingestion ne sont pas neutres épistémiquement. À discuter avec honneur.
  4. Bobzien 2014 sur Aristote *NE* III : Aristote n'est PAS « père de tout » selon Bobzien — juste origine du vocabulaire « ἐφ' ἡμῖν ». Notre matrice ne teste pas Aristote ; mention contextuelle seulement.
- **Open questions** :
  - Une 3ᵉ pôle d'arbitrage (Frede 2011) pour réduire la binarité Amand-Bobzien ?
  - Extension future à Alexandre d'Aphrodise (le « lieu d'émergence » de Bobzien) ?

### §6. Conclusion (~400 mots)

- L'algorithme arbitre empiriquement entre Amand 1945 et Bobzien 1998 sur N des 12 pivots testables.
- Le finding : Amand a raison sur K pivots, Bobzien sur M, avec une zone grise pour P pivots.
- Ce que ça apporte au débat ouvert sur la chronologie du libre arbitre antique.
- Future work : ingestion SVF intégrale, extension à d'autres traditions philosophiques antiques (Aristote *NE* III, Epicure, Néoplatoniciens), application à d'autres scholars (Frede 2011, Dihle 1982).

### §7. Annexe technique : template reproductible (~1,500 mots)

- Architecture du KG EleutherIA + couche néurosymbolique RDF/OWL/SHACL (mention brève)
- Pipeline d'algorithme de parallèle conceptuel pseudo-code
- FAIR data : KG snapshot Zenodo + code public
- Comment refaire pour un autre couple Source A / Source B :
  1. Identifier les corpus pertinents (e.g., Aristote *NE* vs Amand pivots)
  2. Ingestion indépendante depuis éditions critiques
  3. Configurer les tests thématique/conceptuel/textuel
  4. Lancer la matrice + interprétation scholarly
- Limites de la méthode + recommandations pour les utiliser

## 5. Données disponibles dans le KG actuel

| Dataset | Volume | Status |
|---|---|---|
| Amand 1945 (12 pivots) | 12 envelope nodes + sub-args + matrice 6/7 | Complet (commits B1-B9 + audits + patches) |
| Chrysippe | 32 arguments + 18 passages + 1 work SVF II + 2 concepts | Substantiel, mais SVF intégral à ingérer pour exhaustivité |
| Cleanthes | 1 argument + 2 passages + 1 work | Léger — Cleanthes *Hymne* + fragments à enrichir |
| Posidonius | 1 argument + 1 concept + 2 passages | Léger — fragments Edelstein-Kidd à ingérer |
| Panaetius | 1 argument | Très léger |
| SVF collection | 1 source_collection node + 1 work | Existe comme cadre mais peu de passages individuels ingérés |
| Bobzien | 82 nodes (1 person + 3 publications + 78 scholar_arguments/positions) | Massive — Bobzien 1998 + 2000 + 2014 tous présents |
| Epictète / Sénèque / Marc Aurèle | 694 + 2339 + 615 passages | Substantiels pour contre-test stoïcien tardif |

## 6. Travail à faire avant submission

1. **Ingestion supplémentaire SVF** : von Arnim *Stoicorum Veterum Fragmenta* est public domain (volumes I-IV publiés 1903-1924). Ingérer au moins les sections II (Logica + Physica) et III (Moralia) qui couvrent Chrysippe en détail. Estimation : ~500 fragments supplémentaires à structurer en `passage_chrysippus_svf_*`.
2. **Enrichir Cleanthes** : Hymne à Zeus + fragments SVF I.486-619.
3. **Enrichir Posidonius** : fragments Edelstein-Kidd 1972 (Brepols, peut-être en bibliothèque).
4. **Audit philologique** des matches algorithmiques : sur les pivots qui basculent vers Bobzien, vérifier manuellement les 3-5 parallèles les plus forts.
5. **Discussion explicite avec Bobzien 1998** : reprendre les passages où Bobzien argumente contre Amand (chapitre 8 *Inadvertent Conception*) et croiser avec notre matrice.
6. **Figure principale** : heatmap 12 × 4 (pivots × stoïciens primaires) avec scores. Outil : plotly ou matplotlib.
7. **Zenodo DOI** pour KG snapshot + code à publier.
8. **Bibliographie élargie** (au-delà d'Amand + Bobzien) :
   - **Primaires Amand vs Bobzien** : Amand 1945 ; Bobzien 1998, 2000, 2014, 2021
   - **Émergence du libre arbitre antique** : Frede 2011 ; Dihle 1982 ; Kane 2011 (éd. *Oxford Handbook of Free Will*)
   - **Stoïcisme** : Long 1986 (*Hellenistic Philosophy*) ; Long & Sedley 1987 (*The Hellenistic Philosophers*) ; Inwood 1985 (*Ethics and Human Action in Early Stoicism*)
   - **Alexandre d'Aphrodise** : Sharples 1983 (Loeb *De Fato*) ; Sharples 2001 (*Modus Operandi*)
   - **Néoplatoniciens** : Eliasson 2008 (*The Notion of ἐφ' ἡμῖν in Plotinus*)
   - **Sources primaires** : von Arnim SVF (édition Stoïciens primaires) ; Edelstein-Kidd 1972 (Posidonius)
   - **Méthode DH** : références DHQ articles méthodes proches (clustering scholarly texts, computational provenance) à identifier en revue de littérature
9. La langue est désormais fixée à EN (DHQ-style technique).

## 7. Risks & open questions

- **R1** : la définition algorithmique du « parallèle » (thématique + conceptuel + textuel) est arbitraire. Un philologue conservateur peut contester chaque match. **Mitigation** : publier les scores per pivot avec validation manuelle d'un échantillon.
- **R2** : le dataset stoïcien primaire est incomplet. Un finding « pas de parallèle stoïcien » peut être un artefact d'ingestion. **Mitigation** : ingérer SVF II et III avant submission ; documenter explicitement les fragments non couverts.
- **R3** : Bobzien 1998 est *l'autorité absolue* contemporaine. La contester risque de provoquer une réception négative. **Mitigation** : framing « arbitrage empirique » plutôt que « réfutation » ; reconnaître les forces de Bobzien explicitement.
- **R4** : la matrice peut produire un résultat ambigu (e.g., 4 pivots Amand, 4 pivots Bobzien, 4 pivots zone grise). **Mitigation** : l'ambiguïté est un finding scholarly légitime ; ne pas forcer la conclusion.
- **R5** : risque de **sur-interprétation** d'un dataset KG fini. Le KG ne contient pas tous les fragments stoïciens jamais écrits. **Mitigation** : documenter explicitement la couverture, énoncer ce qui n'est PAS testé.

## 8. Timeline indicatif v2

- **2026-05-16** : design v2 approuvé
- **2026-05-17 → 2026-05-30** (~2 semaines) : ingestion supplémentaire SVF + Cleanthes + Posidonius + audits philologiques
- **2026-06-01 → 2026-06-15** (~2 semaines) : exécution de la matrice + validation manuelle des matches + sélection des cas-pivots
- **2026-06-15 → 2026-07-10** (~4 semaines) : rédaction §1-§7
- **2026-07-10 → 2026-07-25** : relectures internes (directeur thèse Romain)
- **2026-07-25** : décision langue + reformatage venue cible
- **2026-08-01** : Zenodo DOI publié, soumission DHQ / DSH / Phronesis

## 9. Decision points encore ouverts

1. **Co-authorship** : Romain solo ou avec son directeur de thèse ? Standard académique varie.
2. **Inclusion de la transmission Phil 23 ↔ PE VI.11** comme cas secondaire (méthode adjacente) ou exclusion totale ? Décision après V1.
3. **3ᵉ pôle d'arbitrage Frede 2011** : explicite dans la matrice (Amand vs Bobzien vs Frede) ou contextuel en discussion ? À choisir selon clarté des findings.
4. **Aristote NE III.1-5** : mention contextuelle seule (Bobzien 2014 pose Aristote comme origine du vocabulaire, pas comme « père du libre arbitre »). Pas dans la matrice principale.
5. **Frontières du « parallèle stoïcien primaire »** : strict (Chrysippe + Cleanthes + Zenon + Posidonius + Panaetius) ou élargi (incl. Diogène de Babylone, Antipater de Tarse) ? À nuancer per pivot.

## 10. Articulation avec Paper A

Cet article reste Paper B (philosophique avec dimension méthodologique). Paper A (méthodologique sur l'infrastructure EleutherIA) reste en attente. Une fois Paper B soumis, Paper A peut s'écrire en référençant Paper B comme un *premier résultat applicatif* du système.

---

**Status** : design v2 (pivot Carneades-or-Chrysippus) approuvé verbalement par Romain (2026-05-16). Prochaine étape : self-review (corriger placeholders/contradictions/scope/ambiguïté), puis user review, puis transition vers `writing-plans` skill pour le plan d'implémentation détaillé (incluant les ingestions SVF supplémentaires + la rédaction §1-§7).
