# Porte grecque : les 56 séquences en échec hors base — appliqué le 2026-10-02

Scripts : `scripts/data_2026_10_02_greek_gate_adjudication.py` (56 décisions) et `scripts/apply_2026_10_02_greek_gate_adjudication.py`.
Décisions : `data/audit/2026-10-02_greek_gate_adjudication_decisions.jsonl`. Entrées ajoutées : `data/audit/greek_allowlist.json` (50 entrées).

## Le constat

`check_greek_gate.py --all` échouait sur `main` pour 56 séquences grecques, absentes de la base de dette (`greek_gate_baseline.json`). L'échec était identique sur le commit `34ea208`, donc antérieur à la vérification du 2026-09-24. La CI ne le voyait pas, car elle n'examine que les nœuds modifiés.

Ces 56 séquences ne sont pas dans les descriptions publiques. Elles se trouvent :

- 53 dans `metadata.quote_verbatim`, c'est-à-dire des extraits de la littérature secondaire copiés octet pour octet de l'extraction du fonds de thèse ;
- 1 dans `supporting_evidence` ;
- 2 dans le compte rendu d'un audit antérieur.

`quote_verbatim` est par construction une copie de la source, dont `kg_extend_verbatim_quotes.py` interdit de « corriger » le moindre caractère. Aucune citation n'a donc été retouchée. Chaque séquence a été jugée, puis certifiée ou qualifiée dans la liste d'autorisation, avec sa provenance.

## Méthode

Chaque séquence est recherchée lettre à lettre dans le TEI d'une édition critique, en ignorant accents, esprits, casse, espaces et ponctuation, et en ramenant le sigma final à σ. Les corpus utilisés sont OpenGreekAndLatin `canonical-greekLit` (commit `bcc5df0`) et `First1KGreek` (commit `8ee111e`). Le script d'application refait cette recherche avant d'écrire et refuse d'écrire si une seule vérification échoue.

## Résultat

| Catégorie | N | Traitement |
|---|---|---|
| Vérifiée dans l'édition | 35 | entrée `VERIFIED` |
| Composite : deux citations ou lemmes soudés par l'extraction, chaque partie vérifiée | 2 | entrée `VERIFIED, composite` |
| Citation endommagée par l'OCR d'un article ancien | 4 | entrée `OCR-DAMAGED`, non certifiée comme texte grec, et note anglaise sur le nœud (`metadata.quote_greek_note`) |
| Grec propre au savant : étiquette, liste de termes, paraphrase, titre moderne | 9 | entrée `SCHOLAR'S OWN GREEK` |
| Source inaccessible ici | 6 | `needs_romain`, reste en échec |

### Vérifiées (37, composites compris)

Le seul écart avec l'édition est presque toujours la perte des espaces entre les mots à l'extraction du PDF : « Καὶγὰρ ὁχρόνος… ».

- **Aristote** : *Physique* IV.14, 223b28-224a2 (Ross) chez Faure ; *Topiques* VIII.2, 158a15-16 et VIII.7, 160a33-34, et *Réfutations sophistiques* 17, 175b9-176a16 (Bekker) chez Bobzien 2013, aux loci qu'elle donne ; *Poétique* 16, 1455a10-12 (Kassel) chez Koch.
- **Alexandre d'Aphrodise** (Bruns) : *De fato* 1, p. 164 (citation et adresse à Sévère et Caracalla) ; *De mixtione* 3-4, p. 216 (Sosigène ; SVF II 473 chez Ramelli) ; titre du chapitre de la *Mantissa* sur ce qui dépend de nous.
- **Pseudo-Alexandre**, *De febribus* 2.1 (Ideler).
- **Platon**, *Lois* X 904c (Burnet).
- **Josèphe** (Niese) : *AJ* XIII.171-172 chez Maston ; *BJ* VI.267-268 en entier chez Velardo.
- **Philon**, *Her.* 301 (Wendland) chez Vibe.
- **Justin**, *1 Apol.* 43 (Rauschen) chez Fürst, et le lemme d'apparat de Minns-Parvis, privé de ses accents par l'OCR.
- **Origène**, *Hom. in Ier.* 18.3 (Klostermann), en épigraphe chez Fürst.
- **Tatien**, *Or.* 5, 12 et 16 (Otto) chez Crawford.
- **Clément**, *Pédagogue* I.6 et *Stromates* V.13.83 (Stählin) chez Karfíková.
- **Lucien**, *Pérégrinos* 18 (Harmon) chez Whitmarsh.

Le TEI First1KGreek du *De fato* imprime un Δ parasite devant Σεβῆρε : c'est la seule différence avec la citation de Koch.

### Citations endommagées par l'OCR (Müller 1926)

L'article de Müller (*ZNW* 25, 1926) cite correctement trois passages, mais l'OCR a déformé les lettres : υ lu δ, accents perdus, trait d'union inséré. Ces passages sont Épictète, *Diss.* IV.1.56 (Schenkl), Ignace, *Éph.* 14.2 (Lake) et Clément, *Strom.* VI.12.96 (Stählin). Chacun a été retrouvé dans l'édition.

Les séquences restent telles quelles dans `quote_verbatim`, mais leur entrée déclare qu'elles ne doivent pas être citées. Une note anglaise, sans grec, renvoie au locus de l'édition.

### Grec propre au savant (9)

Ces séquences sont versées comme telles, pour qu'aucune ne soit citée comme texte ancien :

- l'étiquette de Koch pour la « reconnaissance par déduction » (*Poét.* 16, 1455a4 n'a que « ἡ ἐκ συλλογισμοῦ »), y compris une version soudée à deux mots de 1455a11 ;
- la liste de termes stoïciens dressée par de Faye (1928) et citée par Tolan ;
- la formule de Tolan, qui adapte la division d'ouverture du *Manuel* d'Épictète ;
- deux « citations » qu'Eugène de Faye prête à Épictète et qui sont introuvables sous cette forme dans les *Entretiens* et le *Manuel* (Schenkl) : ce sont des paraphrases ;
- les deux titres grecs de l'édition Gemoll (1884), Népualios et pseudo-Démocrite, chez Crawford ;
- les trois termes pauliniens de Dettwiler dans le compte rendu d'audit (le fichier source écrit σῶμα avec un signe micro).

## `needs_romain` (6 séquences, 5 vérifications)

Ces séquences continuent d'échouer à `--all` jusqu'à vérification. Sur la machine de Romain, la porte, qui interroge le TLG E, indiquera celles qui y sont attestées.

1. **Koch 2015** (2 nœuds) : titre du traité sur la providence que Cyrille, *Contre Julien*, attribue à Alexandre. Le texte de Cyrille n'est pas dans les corpus ouverts ; vérifier dans le TLG 4090.
2. **Ramelli 2014, p. 259** : Stobée, *Ecl.* I, p. 153 Wachsmuth (SVF II 471). À vérifier dans le TLG 2037.
3. **Tolan 2020, pp. 33-34** : second anathème de 553 contre Origène (ACO IV.1, p. 248, 8). À vérifier dans les ACO.
4. **Tolan / de Faye** : formule attribuée à Origène, *De principiis* III.1.3. Le grec de Koetschau n'est pas dans les corpus ouverts ; vérifier dans la Philocalie 21 ou le TLG.
5. **Crawford 2021, p. 41** : Tatien, *Or.* 9. La citation est identique à Otto, sauf un mot : Otto lit « πράξεις », Crawford « τάξεις ». Cette leçon vient vraisemblablement de Trelenberg 2012, que Crawford cite ; à vérifier dans Trelenberg ou Schwartz 1888.

## Contrôles

- Relance : aucune modification.
- `check_greek_gate.py --all` : 6 échecs, soit exactement les `needs_romain` (contre 56 avant). La dette de la base est passée de 1 758 à 1 757, une séquence de la base étant désormais couverte par une entrée vérifiée.
- `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict` et `check_kg_work_child_canonical` : OK.
