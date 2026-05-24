# RESUME — Article DHQ « Algorithmic provenance analysis of six moral anti-fatalist pivots »

> Point d'entrée unique pour reprendre le travail de l'article (Paper B) à froid.
> Dernière mise à jour : 2026-05-24. Auteur : Romain Girardi (CEPAM-UMR 7264).

---

## 0. TL;DR — où on en est

L'**ingénierie est finie** (Phase 1-3, tâches T1-T12). Il reste la **rédaction scholarly** (Phase 4-6, T13-T23), qui demande la lecture philologique et la plume de Romain.

Tout est prêt : corpus stoïcien enrichi + analyzer + matrice 6×4 + figures. Le **finding scholarly central est acquis** et reproductible.

**Prochaine action concrète** : T13 = validation philologique manuelle de 10 matches de la matrice (échantillon aléatoire seed 42), puis rédaction §1-§7.

---

## 1. Identité de l'article

- **Titre** : *Algorithmic provenance analysis of six moral anti-fatalist pivots: testing Amand 1945's Carneadean attribution against the primary Stoic corpus*
- **Auteur** : Romain Girardi, CEPAM-UMR 7264 (Université Côte d'Azur)
- **Langue** : EN (DHQ-style technique)
- **Venue cible** : Digital Humanities Quarterly (DHQ) ; secondaire DSH (Oxford)
- **Longueur** : 7 500-9 000 mots + annexe technique (~1 500 mots)
- **Type** : case study méthodologique avec finding empirique non-circulaire

### Thèse centrale

Amand 1945 attribue à Carnéade six pivots moraux anti-fatalistes (général, législation, vertu/vice, stimulants, futilité de l'action, piété) — attribution **externe** (académicienne). Bobzien 1998/2000/2014 conteste partiellement : origine **interne** stoïcienne (auto-critique chrysippéenne avant Carnéade). On teste algorithmiquement, pour chacun des 6 pivots, l'existence de parallèles stoïciens primaires (Chrysippe, Cleanthes, Posidonius, Panaetius). La matrice résultante **arbitre empiriquement** entre Amand et Bobzien pivot par pivot.

### Méta-thèse épistémologique

Le scholar DH avec corpus structuré + méthode quantifiable est un **arbitre quantifiable** entre positions historiographiques prose-fondées que 28+ ans de débat philologique n'ont pas tranchées. L'article *teste* cette méta-thèse : résultat clair → validée ; résultat ambigu → limites trouvées.

### Pourquoi non-circulaire

On ne valide PAS les attributions d'Amand avec son propre cadre. On confronte ses 6 pivots à un dataset stoïcien indépendant (Chrysippe SVF + autres) construit sans référence à la thèse carnéadienne. Voir spec §2.

---

## 2. LE FINDING (matrice 6×4)

Données : `docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json` (générée 2026-05-16).
Régénérer : `python scripts/analyze_amand_stoic_provenance.py`

Score = nombre de tests positifs (thématique + conceptuel + textuel), max 3 par cellule.
Vote = un stoïcien « vote » pour un pivot si score ≥ 1. Pivot PASS si ≥ 3/4 votes.

| Pivot moral Amand | Chrysippe | Cleanthes | Posidonius | Panaetius | Votes | Verdict |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| I. Thème général | 2 | 2 | 1 | 0 | 3/4 | **PASS** |
| II. Législation | 0 | 1 | 1 | 0 | 2/4 | fail |
| III. Vertu & vice | 2 | 1 | 1 | 1 | 4/4 | **PASS** |
| IV. Stimulants | 1 | 0 | 0 | 0 | 1/4 | fail |
| V. Futilité de l'action | 1 | 1 | 0 | 0 | 2/4 | fail |
| VI. Piété & religion | 1 | 1 | 1 | 0 | 3/4 | **PASS** |

### Interprétation philosophique (le cœur de l'article)

- **3 pivots PASS (I, III, VI)** = lexique fondamental stoïcien (εἱμαρμένη, ἀρετή/κακία, εὐσέβεια). Ces topoi ont des parallèles stoïciens primaires nets → **partiellement Bobzien 1998** : matériel pré-carnéadien existe dans le stoïcisme.
- **3 pivots fail (II, IV, V)** = *reductiones ad absurdum* anti-stoïciennes (absurdité de la législation, futilité des stimulants, inaction). Pas de parallèle stoïcien primaire → **partiellement Amand 1945** : ce sont les attaques externes carnéadiennes par construction, pas des thèses stoïciennes positives.

**Conclusion arbitrale** : la dette stoïcienne se situe au niveau du *vocabulaire moral partagé*, pas au niveau des *mouvements anti-fatalistes* eux-mêmes, qui restent carnéadiens. Ni Amand ni Bobzien n'ont entièrement raison ; la frontière est mesurable et passe entre lexique (stoïcien) et argumentation polémique (carnéadienne).

### Figures (prêtes)

`docs/papers/2026-05-amand-piste1-figures/` :
- `heatmap-6x4.{png,svg}` — figure principale (Figure 1)
- `case-virtue_vice.{png,svg}` — pivot III, le PASS le plus fort (4/4)
- `case-piety.{png,svg}` — pivot VI, PASS nuancé (3/4)
- `case-general_theme.{png,svg}` — pivot I
Régénérer : `python scripts/generate_provenance_figures.py`

---

## 3. CAVEATS à traiter dans la rédaction (§5 Discussion)

1. **Conceptual test = 0/24 partout.** Les pivots Amand sont reliés à des `passage_*` (evidenced_by / cites_primary_source), PAS à des `concept_*`. Le test conceptuel est donc inactif sur le KG actuel. C'est un sub-finding honnête (topologie du KG) → soit le mentionner comme limite méthodologique, soit faire une passe d'enrichissement pivot→concept avant re-run. Le signal vient du thématique + textuel, suffisant pour la règle 3/4.
2. **Posidonius corpus skew.** 66 testimonia : 21 Seneca (Latin), 37 Diogène Laërce VII (Greek), 4 Cicéron De Fato, reste divers. Seneca domine → c'est de la réception impériale, pas du Posidonius primaire pur. Defendable (Seneca = transmetteur majeur de Posidonius, cf. Kidd) mais à signaler explicitement en §3 (Méthode).
3. **Greek lemma matching par substring** (NFD-strip + lowercase). Déterministe mais matche les formes fléchies (`αρετη` matche `αρετην`). OK pour décision binaire hit/no-hit ; insuffisant pour statistiques token-level.
4. **Panaetius extrêmement sparse** (1 argument). Acceptable : il est post-Chrysippe, marginal pour la question pré-carnéadienne. Vote quasi-systématiquement 0.
5. **Le KG est construit par l'auteur** — choix d'ingestion non neutres épistémiquement. À discuter avec honneur.
6. **Amand ne nie pas tout précédent stoïcien** ; il pose que Carnéade *systématise*. La matrice teste l'antériorité des matériaux, PAS l'origine de la systématisation. Limite réelle à nommer.
7. **matplotlib pas dans pyproject** — ajouter aux dev-extras pour reproductibilité CI des figures.

---

## 4. CE QUI EST FAIT (Phase 1-3, T1-T12)

### Phase 1 — Enrichissement corpus stoïcien primaire

| Source | Avant | Après | Commit |
|---|---|---|---|
| Chrysippe | 19 args, 0 passages | + **88 passages SVF II** (§913-1000, εἱμαρμένη core) | `a076cea1` + polish `b270afed` |
| Cleanthes | 1 arg, 0 passages | + **51 passages** (Hymne 39 lignes + 11 SVF I + 1 complete) | `77d33907` |
| Posidonius | 0 testimonia | + **66 testimonia** (27 Latin `68f00997` + 37 Greek DL VII `573b0515`) | `68f00997`, `573b0515` |
| Panaetius | 1 arg | inchangé (sparse acceptable) | — |

Sources : OGL First1KGreek TEI (`tlg1264.tlg001` Chrysippe, `tlg1269.tlg002` Cleanthes), wiring testimonia depuis passages existants (Seneca, DL VII, Cicéron).
Reports : `docs/reports/2026-05-16-stoic-corpus-pre-enrichment-audit.md` + `...-post-enrichment-summary.md`.

### Phase 2 — Analyzer provenance

`scripts/analyze_amand_stoic_provenance.py` (commit `03821acb`) :
- 3 tests cumulatifs : thématique (keyword overlap), conceptuel (shared concept_* nodes), textuel (Greek lemma + diacritic normalization)
- `compute_matrix()` → 6×4 PairScore objects → dump JSON
- Tests : `knowledge graph/tests/unit/test_amand_stoic_provenance.py`
- READ-ONLY sur le KG, déterministe (pas de LLM)

### Phase 3 — Figures

`scripts/generate_provenance_figures.py` (commit `0da13571`) : heatmap + 3 case studies, matplotlib, PNG dpi=300 + SVG.

**Tests au moment de la livraison : 153/153 ✓. SHACL invariants ✓.**

---

## 5. CE QUI RESTE (Phase 4-6, T13-T23 — tâches scholar de Romain)

Plan détaillé : `docs/superpowers/plans/2026-05-16-amand-piste1-article-implementation.md`

| Tâche | Description | Livrable |
|---|---|---|
| **T13** | Validation philologique manuelle de 10 matches aléatoires (seed 42) | `docs/papers/2026-05-amand-piste1-data/manual-validation-sample.md` |
| **T14** | §1 Introduction (~800 mots) — controverse Amand vs Bobzien + question opérationnelle + méta-thèse | article EN |
| **T15** | §2 Background (~1000 mots) — champ complet (Amand, Bobzien, Frede, Dihle, Long-Sedley, Inwood, Sharples, Eliasson, Kane) | |
| **T16** | §3 Méthode (~1400 mots) — dataset + 3 tests + reproductibilité | |
| **T17** | §4 Résultats (~1800 mots) — matrice (Fig 1) + 3 case studies + classification per pivot | |
| **T18** | §5 Discussion (~1500 mots) — arbitrage + cross-check Frede/Dihle + méta-thèse + limites (cf. §3 caveats ci-dessus) | |
| **T19** | §6 Conclusion + §7 Annexe technique reproductible | |
| **T20** | Bibliographie BibTeX complète | `docs/papers/2026-05-amand-piste1-bibliography.bib` |
| **T21** | Self-review article + révisions | |
| **T22** | Zenodo DOI (KG snapshot + code + matrix data) | |
| **T23** | Soumission DHQ | `docs/papers/2026-05-amand-piste1-submission-log.md` |

### Démarrage T13 (commande prête)

```bash
cd "/Users/romaingirardi/Projects/EleutherIA" && /Users/romaingirardi/Projects/EleutherIA/.venv/bin/python -c "
import json, random
data = json.loads(open('docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json').read())
flat = [p for row in data['matrix'] for p in row]
positive = [r for r in flat if r['total_score'] >= 2]
random.seed(42)
sample = random.sample(positive, k=min(10, len(positive)))
for s in sample:
    print(f\"{s['pivot']} × {s['stoic']}  score={s['total_score']}\")
    print(f\"  thematic: {s['thematic_hits']}\")
    print(f\"  textual: {s['textual_hits']}\")
    print()
"
```

Pour chaque match : lire la (les) source(s) stoïcienne(s) citée(s), juger G (genuine) / P (partial) / S (spurious). Si ≥80% genuine → matrice publiable telle quelle. 60-79% → mentionner comme limite. <60% → raffiner l'algorithme.

---

## 6. CARTE DES FICHIERS

```
docs/superpowers/specs/2026-05-16-amand-piste1-article-design.md     ← spec v3 (titre, thèse, plan §1-§7, caveats)
docs/superpowers/plans/2026-05-16-amand-piste1-article-implementation.md  ← plan 23 tâches
docs/papers/2026-05-amand-piste1-RESUME.md                           ← CE FICHIER
docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json     ← LE finding
docs/papers/2026-05-amand-piste1-figures/*.{png,svg}                 ← 4 figures
scripts/analyze_amand_stoic_provenance.py                            ← analyzer (re-run pour régénérer matrice)
scripts/generate_provenance_figures.py                              ← figures (re-run après matrice)
scripts/ingest_chrysippus_svf_first1kgreek.py                       ← T2 ingestion
scripts/ingest_cleanthes_fragments.py                              ← T3 ingestion
scripts/wire_posidonius_testimonia.py                              ← T4 wiring
knowledge graph/tests/unit/test_amand_stoic_provenance.py          ← tests analyzer
docs/reports/2026-05-16-stoic-corpus-*.md                          ← audits Phase 1
docs/reports/2026-05-16-piste1-carneadean-transmission-analysis.md ← rapport Piste 1 (matrice témoins 6×7, distinct du Stoic test)
docs/reports/2026-05-16-amand-coherence-audit.md                   ← audit cohérence intégration Amand
```

---

## 7. CONTEXTE PROFOND (à savoir pour reprendre)

### Genèse du pivot de scope

- **v1** (abandonnée) : vérifier l'assertion Phil 23 ↔ PE VI.11 (Amand p. 366) en alignement verbatim. Trop modeste (1 transmission isolée).
- **v2** : pivot Carnéade-vs-Chrysippe origine. Romain a poussé pour « dépasser Amand » (mémoire Piste 1).
- **v3** (actuelle) : 6 pivots moraux only (antiastrologiques + auto-réfutation hors scope), bibliographie élargie, méta-thèse DH-arbiter explicite, titre EN technique.

### Le KG contient AUSSI (pour référence, pas le finding principal)

- **Intégration Amand 1945 intégrale** (B1-B9, ~310 nodes) : tout le livre est dans le KG, audit-vérifié, 3 patches structurels appliqués.
- **6 témoins canoniques d'Amand** + matrice témoins×pivots 6×7 (distincte de la matrice Stoic test) : voir `docs/reports/2026-05-16-piste1-carneadean-transmission-analysis.md`. CETTE matrice est circulaire (reproduit Amand avec son cadre) — c'est pourquoi l'article pivote sur le Stoic test non-circulaire.
- **Transmission Phil 23 ↔ PE VI.11** : 70 edges `parallel_to`, 84% verbatim — finding v1 conservé, mentionnable en §5 comme méthode adjacente.

### Décisions tranchées (mémoires sauvegardées)

- `feedback_critical_editions_only` : éditions critiques uniquement, jamais de manuscrits primaires.
- `project_philo_de_providentia_pending` : témoin n°1 Philon attend SC 35bis Hadas-Lebel.

### Points de décision encore ouverts (spec §9)

1. Co-authorship : Romain solo ou avec directeur de thèse ?
2. Inclure Phil 23 ↔ PE VI.11 comme cas secondaire ou pas ?
3. Frede 2011 comme 3ᵉ pôle explicite dans la matrice, ou contextuel en discussion ?
4. Aristote NE III : mention contextuelle seule (Bobzien 2014 le pose comme origine du vocabulaire ἐφ' ἡμῖν, pas père du problème) — PAS dans la matrice.
5. Frontières du « parallèle stoïcien primaire » : strict (Chrysippe+Cleanthes+Zénon+Posidonius+Panaetius) ou élargi (Diogène de Babylone, Antipater de Tarse) ?

---

## 8. COMMENT REPRODUIRE TOUT LE PIPELINE

```bash
cd "/Users/romaingirardi/Projects/EleutherIA"
PY=/Users/romaingirardi/Projects/EleutherIA/.venv/bin/python

# 1. Vérifier le KG est sain
$PY -c "from pathlib import Path; from eleutheria_kg.semantic import build_graph, validate_kg_invariants; g=build_graph(Path('data/kg/nodes.jsonl'),Path('data/kg/edges.jsonl')); print(len(g),'triples, invariants', validate_kg_invariants(g).conforms)"

# 2. (Re)générer la matrice
$PY scripts/analyze_amand_stoic_provenance.py

# 3. (Re)générer les figures
$PY scripts/generate_provenance_figures.py

# 4. Tests
cd "knowledge graph" && $PY -m pytest tests/unit/test_amand_stoic_provenance.py -v
```

Les scripts d'ingestion (T2-T4) sont idempotents et déjà appliqués — ne pas re-run sauf si le KG est réinitialisé. Snapshots sous `data/kg/snapshots/2026-05-16-pre-*/`.

---

## 9. BIBLIOGRAPHIE À COMPILER (T20)

Présents dans le KG (`data/kg/publications.bib`) : Amand 1945, Bobzien 1998/2000/2014, von Arnim 1903 SVF I/II.
À ajouter : Frede 2011, Dihle 1982, Kane 2011 éd., Long 1986, Long-Sedley 1987, Inwood 1985, Sharples 1983/2001, Eliasson 2008, Edelstein-Kidd 1972, Junod 1976 SC 226, Dindorf 1867.
+ références méthode DH (clustering scholarly texts, computational provenance) à identifier en revue de littérature.

---

## 10. ÉTAT GIT (au 2026-05-24)

HEAD : `63f8f25e feat(corpus): Scaife ingestion feasibility scan` (travail parallèle Romain, sans rapport avec l'article).
KG actuel : 210 180 triples (a grandi via ingestions Scaife parallèles), invariants ✓.

Commits article (engineering Phase 1-3) :
- `05a5532e` / `da9815f9` — T1 audit + fix
- `a076cea1` / `b270afed` — T2 Chrysippe SVF II
- `77d33907` — T3 Cleanthes
- `68f00997` — T4 Posidonius Latin
- `573b0515` — T5 closure + Greek pass
- `03821acb` — T6-T10 analyzer
- `0da13571` — T11-T12 figures
- `a3ec8c42` / `cbabef78` — spec v2 / v3
- `08c8c2e4` — plan

Tout est sur `main`, poussé.
