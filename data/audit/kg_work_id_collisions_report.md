# kg_work_id collision report

One KG work node claimed by several distinct corpus works (`work_canonical_id` of its `part_of` passages). Each group below needs manual per-work remediation: keep the passages that truly belong to the work node, re-home the rest under their own work node, then remove the group from `data/audit/kg_work_id_known_collisions.json`.

Generated read-only by `scripts/check_kg_work_id_uniqueness.py --report` from `data/kg/nodes.jsonl` + `data/kg/edges.jsonl`.

**Colliding KG work nodes: 11**

## `sc172_epistula_barnabae`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `sc172_epistula_barnabae` | Anonymous (Pseudo-Barnabas) | Epistula Barnabae | 176 |
| `urn:cts:greekLit:tlg1311.tlg001` | Didache | Didache - Complete Works | 6 |

## `work_de_interpretatione_aristotle_c350bce_e4f6g8h0`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `first1k:tlg0086.tlg002.1st1K-grc1` | Aristotle | De anima | 30 |
| `first1k:tlg0086.tlg017.1st1K-grc1` | Aristotle | De interpretatione | 29 |

## `work_de_libero_arbitrio`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `cpl:evodius.de_fide` | Evodius Bishop of Uzalis -424 | De fide Contra Manicheos | 36 |
| `urn:cts:greekLit:tlg2022.tlg007` | Gregory of Nazianzus | Adversus Eunomianos (orat. 27) | 9 |
| `urn:cts:greekLit:tlg2022.tlg008` | Gregory of Nazianzus | De Theologia (Orat. 28) | 31 |
| `urn:cts:greekLit:tlg2022.tlg009` | Gregory of Nazianzus | De Filio (Orat. 29) | 21 |
| `urn:cts:greekLit:tlg2022.tlg010` | Gregory of Nazianzus | De Filio (Orat. 30) | 21 |
| `urn:cts:greekLit:tlg2022.tlg011` | Gregory of Nazianzus | De Spiritu Sancto (Orat. 31) | 33 |
| `urn:cts:latinLit:stoa0040.adv_fulg` | Augustine | Libellus Adversus Fulgentium Donatistam | 26 |
| `urn:cts:latinLit:stoa0040.stoa003` | Augustine | De Libero Arbitrio | 510 |
| `urn:cts:latinLit:stoa0040.stoa045` | Augustine | De Correptione et Gratia | 21 |
| `urn:cts:latinLit:stoa0040.stoa054` | Augustine | De Natura Boni | 39 |

## `work_de_providentia_seneca_a2b3c4d5`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:latinLit:phi1017.phi015` | Seneca | Epistulae Morales ad Lucilium | 2135 |
| `urn:cts:latinLit:stoa0255.stoa012` | Seneca | De Providentia | 204 |

## `work_diogenes_laertius_lives`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:greekLit:tlg0004.tlg001` | Diogenes Laertius | Vitae Philosophorum (Lives of Eminent Philosophers) | 1203 |
| `urn:cts:latinLit:phi1254.phi001` | Diogenes Laertius | Noctes Atticae | 1 |

## `work_epictetus_fragments`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:greekLit:tlg0557` | Epictetus | Discourses | 22 |
| `usener:epicurus` | Epicurus | Letters and Fragments | 193 |

## `work_justin_first_apology`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:greekLit:tlg0645.tlg001` | Justin Martyr | Apologia Prima | 72 |
| `urn:cts:greekLit:tlg0645.tlg002` | Justin Martyr | Apologia Secunda | 15 |

## `work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `first1k:tlg0086.tlg022.1st1K-grc1` | Aristotle | Magna Moralia | 434 |
| `oga:tlg0086.tlg009.perseus-grc2` | Aristotle | Ἠθικὰ Εὐδήμεια | 41 |
| `oga:tlg0086.tlg010.perseus-grc2` | Aristotle | Ἠθικὰ Νικομάχεια | 153 |
| `oga:tlg0086.tlg031.1st1K-grc1` | Aristotle | Physica | 71 |

## `work_plato_timaeus`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `digiliblt:DLT000607` | Calcidius | Commentarius in Platonis Timaeum | 5 |
| `urn:cts:greekLit:tlg0059.tlg031` | Plato | Τίμαιος (Timaeus) | 78 |

## `work_plutarch_de_fato_complete`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:greekLit:tlg0007.tlg108` | Plutarch | De fato | 57 |
| `urn:cts:greekLit:tlg0007.tlg135` | Plutarch | De Communibus Notitiis adversus Stoicos | 6 |
| `urn:cts:greekLit:tlg0007.tlg136` | Plutarch | De Stoicorum Repugnantiis (On Stoic Self-Contradictions) | 47 |

## `work_republic_plato_c380bce_c3d4e5f6`

| work_canonical_id | author | title | passages |
|---|---|---|---|
| `urn:cts:greekLit:tlg0059.tlg002` | Plato | Ἀπολογία Σωκράτους | 125 |
| `urn:cts:greekLit:tlg0059.tlg030` | Plato | Republic (Πολιτεία) | 278 |
