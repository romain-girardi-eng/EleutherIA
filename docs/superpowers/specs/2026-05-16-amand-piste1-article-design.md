---
date: 2026-05-16
status: design v2 — pivoted from "verbatim Phil 23 ↔ PE VI.11" to "Carneades-or-Chrysippus origin test"
title_fr: "Carnéade ou Chrysippe ? Tester algorithmiquement l'origine des arguments anti-fatalistes attribués à l'Académicien par Amand 1945"
title_en: "Carneades or Chrysippus? Algorithmically Testing the Origin of the Anti-Fatalist Arguments Attributed to the Academic Scholarch by Amand 1945"
author: Romain Girardi
affiliation: CEPAM-UMR 7264 (Université Côte d'Azur)
target_venue: Digital Humanities Quarterly (DHQ) or Digital Scholarship in the Humanities (DSH)
target_length: 7,500-9,000 words + technical appendix (~1,500 words)
language_decision: deferred (FR for DSH, EN for DHQ)
contribution_kind: scholarly arbitration between two major secondary sources via algorithmic test
relates_to: Piste 1 (project memory) — "reproduire ET DÉPASSER Amand 1945"
---

# Design : article scholarly Carnéade vs Chrysippe

## 0. Pourquoi cette v2 (justification du pivot)

Le design v1 proposait de vérifier algorithmiquement *une* assertion isolée d'Amand (Phil 23 ↔ PE VI.11, p. 366). Cible : ~7-8k mots, modeste mais épistémiquement honnête.

Romain a objecté que cette v1 **n'incarne pas l'ambition originelle de Piste 1** telle que formulée en mémoire projet : « cartographier l'héritage anti-fataliste carnéadéen dans la patristique en quantifiant les chaînes de transmission via OWL-RL inference + proof chains. Reproduire **et dépasser** Amand 1945 par quantification mécanique des filiations qu'il assertait en prose discursive. »

**Pivot v2** : challenger directement une *thèse* d'Amand (pas une assertion isolée), avec un finding qui arbitrera entre deux scholars majeurs (Amand 1945 et Bobzien 1998) plutôt que de simplement opérationnaliser Amand. Le finding n'est plus *vérification* mais **arbitrage scholarly**.

## 1. Thèse centrale v2

Amand 1945 attribue à Carnéade un corpus d'arguments anti-fatalistes (5 antiastrologiques + 6 moraux + 1 auto-réfutation pragmatique stoïcienne). Bobzien 1998 (*Determinism and Freedom in Stoic Philosophy*) conteste partiellement cette attribution exclusive en soutenant que certaines critiques du déterminisme stoïcien sont **internes au stoïcisme** (auto-critique chrysippéenne ou post-chrysippéenne) plutôt qu'externes (académiciennes).

Nous testons cette tension algorithmiquement en cherchant, pour chaque pivot anti-fataliste d'Amand, des parallèles antérieurs ou contemporains chez les stoïciens primaires (Chrysippe en priorité, puis Cleanthes, Posidonius, Panaetius) dans le KG EleutherIA. Le résultat — quel(s) pivot(s) ont un parallèle stoïcien net — arbitre empiriquement entre Amand 1945 et Bobzien 1998 sur le scope précis où les deux divergent.

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

- La controverse historique : Amand 1945 vs Bobzien 1998 sur l'origine du discours anti-fataliste.
- Amand : exterieur (Carnéade Académicien attaque les Stoïciens depuis l'extérieur).
- Bobzien : intérieur (auto-critique stoïcienne, le « problème du libre arbitre » avant Carnéade).
- L'enjeu philosophique : la chronologie du « problem of free will » dans l'antiquité. Si Bobzien a raison, Aristote/Chrysippe sont les vrais inventeurs ; si Amand a raison, Carnéade est le pivot.
- La question opérationnelle : pour chaque pivot anti-fataliste d'Amand, existe-t-il un parallèle stoïcien antérieur ou contemporain dans le corpus disponible ?

### §2. Background (~800 mots)

- Amand 1945 : reconstruction du corpus carnéadien à partir des 6 témoins canoniques + règle 3/6. Brève synthèse des 12 pivots reconstructs (5 antiastrologiques en intro §II + 6 moraux dans la Conclusion + 1 auto-réfutation pragmatique).
- Bobzien 1998 + 2000 + 2014 : la position alternative. Bobzien arguments-clés : (a) Aristote *NE* III.1-5 a déjà la matière essentielle de l'« ἐφ' ἡμῖν » ; (b) Chrysippe répond à des objections internes au stoïcisme (Cleanthes, Diodore), pas seulement carnéadiennes ; (c) le « problème » du libre arbitre comme tel émerge chez Alexandre d'Aphrodise, pas chez Carnéade.
- Le point de divergence précis testable : **les pivots anti-fatalistes d'Amand sont-ils carnéadiens ou stoïciens (intra-école) ?**

### §3. Méthode (~1,400 mots)

- **Construction du dataset** :
  - Pivots d'Amand : 12 nodes Amand-tagged (5 antiastro + 6 moraux + 1 auto-réfutation), tels que reconstruits dans le KG EleutherIA (commits B1-B9, audit-verifié)
  - Dataset stoïcien primaire : Chrysippe (`person_chrysippus_*` + 32 arguments + 18 passages SVF + concepts associés), Cleanthes (1 argument + 2 passages), Posidonius (1 argument + 1 concept), Panaetius (1 argument)
  - Stoïciens tardifs (Epictète 694 passages, Sénèque 2339 passages, Marc Aurèle 615 passages) — utilisés comme contre-test : si un pivot a un parallèle SEULEMENT chez les stoïciens tardifs (post-Carnéade), ça n'arbitre pas — le parallèle peut être post-carnéadien.
- **Algorithme de détection de parallèles** : pour chaque pair (pivot d'Amand, argument stoïcien), trois tests cumulatifs :
  1. **Test thématique** : tags concept partagés + chevauchement métadonnée `amand_pivot_label` vs argument stoïcien topic
  2. **Test conceptuel** : présence d'un concept commun (e.g., `concept_synkatathesis`, `concept_eph_hemin`, `concept_heimarmene_stoic`) discuté par les deux
  3. **Test textuel partiel** (optionnel) : si passages disponibles, recherche de termes-clés partagés (e.g., εἱμαρμένη, εφ' ἡμῖν, νόμος, ψόγος) avec normalisation polytonique
- Score par pivot : 0 (aucun parallèle stoïcien primaire), 1 (parallèle thématique seul), 2 (thématique + conceptuel), 3 (les trois).
- **Décision de classification** : un pivot est « possiblement non-exclusivement-carnéadien » si score ≥ 2 chez Chrysippe OU score ≥ 1 chez ≥ 2 stoïciens primaires distincts.
- **Reproductibilité** : code public + KG snapshot Zenodo. Le pipeline est déterministe (pas de LLM dans l'algorithme final).

### §4. Résultats (~1,800 mots)

- **Matrice principale** : 12 pivots × 4 stoïciens primaires (Chrysippe, Cleanthes, Posidonius, Panaetius). Visualisation en heatmap (figure principale).
- Pour chaque pivot, score par stoïcien primaire + score agrégé.
- **Classification** :
  - Pivots **clairement carnéadiens** (score ≤ 1 avec aucun stoïcien primaire) — Amand strictement défendable
  - Pivots **hybrides** (score ≥ 2 avec ≥ 1 stoïcien primaire) — Bobzien partiellement défendable
  - Pivots **stoïciens d'origine** (score ≥ 2 chez ≥ 2 stoïciens primaires) — Bobzien fortement défendable
- **Cas-pivots détaillés** (zoom in sur 2-3 pivots où Amand et Bobzien divergent le plus nettement) :
  - Pivot III. Vertu & vice — Chrysippe SVF II.998 discute-t-il déjà la question praise/blame sous déterminisme ?
  - Pivot VI. Piété & religion — Cleanthes *Hymne à Zeus* + Marc Aurèle II.3 ont-ils l'auto-critique ?
  - Pivot VII. Auto-réfutation pragmatique stoïcienne — c'est par construction stoïcienne (auto-réfutation par dialectique stoïcienne), donc score élevé attendu chez Chrysippe
- **Sub-finding contre-intuitif** : les pivots **antiastrologiques** (Carnéade arg. I-V) ont-ils un parallèle stoïcien ? La cosmologie stoïcienne accepte εἱμαρμένη astrale ; donc un parallèle stoïcien serait surprenant. À vérifier empiriquement.

### §5. Discussion (~1,500 mots)

- **Arbitrage Amand vs Bobzien sur le pivot précis testé** : sur les N pivots testables, M penchent vers Bobzien, K-M penchent vers Amand.
- **Implications philosophiques** : qu'est-ce que ça change pour la chronologie du libre arbitre antique ? Si certains arguments anti-fatalistes sont stoïciens d'origine, alors le « problème » émerge avant Carnéade dans le stoïcisme lui-même — confirmant Bobzien sur ce point.
- **Reconnaissance des subtilités** : Amand ne nie pas l'existence de précédents stoïciens ; il pose que **Carnéade les a systématisés**. Notre matrice ne peut pas tester l'origine de la *systématisation* — seulement l'antériorité des matériaux. C'est une limite réelle.
- **Limites techniques** :
  1. Le dataset stoïcien primaire dans le KG (Chrysippe 32 args, Cleanthes 1, Posidonius 1, Panaetius 1) est **incomplet** par rapport à SVF intégral. Une partie du finding peut être due à l'incomplétude, pas à l'absence réelle.
  2. La notion de « parallèle » est définie par 3 tests cumulés mais reste flou philologiquement. Un philologue conservateur peut contester chaque match.
  3. Le KG est construit par Romain ; les choix d'ingestion ne sont pas neutres. À discuter.
- **Open questions** :
  - Ingestion complète SVF (Stoicorum Veterum Fragmenta — ~1,400 fragments) avant submission ?
  - Comparaison avec une 3ᵉ thèse (Frede 2011 ?) ?

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
8. **Bibliographie** :
   - Amand 1945 (incontournable)
   - Bobzien 1998, 2000, 2014 (tous présents dans le KG)
   - von Arnim SVF (édition de référence Stoïciens primaires)
   - Frede 2011, Dihle 1982, Kane 2011 (contexte philosophique)
   - Références DH (DHQ articles méthodes proches)
9. **Décision langue** (FR ou EN) à arbitrer après squelette V1.

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

1. **Langue de soumission** : FR (DSH) ou EN (DHQ ou Phronesis) — à trancher post-V1.
2. **Co-authorship** : Romain solo ou avec son directeur de thèse ?
3. **Inclusion de la transmission Phil 23 ↔ PE VI.11** comme cas secondaire (méthode adjacente) ou exclusion totale ?
4. **Inclusion de Frede 2011** comme 3ᵉ pôle dans l'arbitrage (au-delà d'Amand-vs-Bobzien) ?
5. **Inclusion d'Aristote NE III.1-5** comme test bonus (Bobzien argument central : Aristote précède Chrysippe) ?

## 10. Articulation avec Paper A

Cet article reste Paper B (philosophique avec dimension méthodologique). Paper A (méthodologique sur l'infrastructure EleutherIA) reste en attente. Une fois Paper B soumis, Paper A peut s'écrire en référençant Paper B comme un *premier résultat applicatif* du système.

---

**Status** : design v2 (pivot Carneades-or-Chrysippus) approuvé verbalement par Romain (2026-05-16). Prochaine étape : self-review (corriger placeholders/contradictions/scope/ambiguïté), puis user review, puis transition vers `writing-plans` skill pour le plan d'implémentation détaillé (incluant les ingestions SVF supplémentaires + la rédaction §1-§7).
