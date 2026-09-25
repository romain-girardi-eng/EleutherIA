# C1 : liens passage → concept contredits — appliqué le 2026-09-24

Scripts : `scripts/data_2026_09_24_c1_contradictions.py` (96 décisions) et `scripts/apply_2026_09_24_c1_contradictions.py`.
Décisions : `data/audit/2026-09-24_c1_contradictions_decisions.jsonl`. Quarantaine : `data/audit/2026-09-24_c1_contradictions_quarantine.jsonl` (4 arêtes, 4 citations de corpus miroirs).

## Périmètre et méthode

Le fichier `queue_contradictions.csv` recense 96 liens passage → concept existants que Jev contredit. Ils se répartissent ainsi : 84 chapitres d'Alexandre, *De fato*, 10 passages d'Augustin, *De libero arbitrio*, et 2 passages d'Aristote, *EN* III.

Pour Alexandre, le test ne porte pas sur le texte stocké, car certains chapitres sont abrégés (« [...] »). Il porte sur le chapitre complet du TEI First1KGreek `tlg0732.tlg014.1st1K-grc1` (Bruns 1892, commit `8ee111eb`, SHA-256 épinglé). Les 38 chapitres stockés coïncident avec les sections du TEI. Pour chaque lien, je cherche dans le chapitre le radical du concept.

Un lien n'est retiré que si sa justification nomme le terme (« κύριος appears throughout », « σῴζουσα διδασκαλία in these chapters », etc.) et que le chapitre ne le contient pas. Quand la justification est conceptuelle, l'absence du mot ne réfute rien. Par exemple, le ch. 13 critique la « nature interne » stoïcienne sans nommer le cylindre, qui n'apparaît qu'au ch. 11.

## Résultat

| Verdict | N |
|---|---|
| `removed` | 8 (4 arêtes encore présentes ; les 4 autres avaient été retirées par le lot `c3_discusses_edges`) |
| `false_positive` : conservé, radical présent dans le chapitre, ou locus canonique | 25 |
| `needs_romain` | 63 |

Retraits :

- Alexandre, *Fat.* 31 → « enseignement qui sauve » : la justification annonce σῴζουσα διδασκαλία, et le ch. 31 ne contient aucune forme de διδασκαλία.
- *Fat.* 5 → « pluralité des biens » : déjà retiré au lot C3, pour la même raison.
- Augustin, *De lib. arb.* II.11.31, II.13.35 et II.16.44 → *liberum arbitrium* et *voluntas* : ces passages relèvent de la preuve de Dieu du livre II. Les arêtes vers *voluntas* avaient déjà été retirées au lot C3.

`needs_romain` :

- 45 liens générés automatiquement sans justification, vers ἐνδεχόμενον, ἐφ' ἡμῖν et εἱμαρμένη, lorsque le radical manque dans le chapitre ;
- 2 liens d'Augustin, *De lib. arb.* II.16.43 (sur l'amour des signes plutôt que de ce qu'ils signifient : la volonté peut y être en jeu) ;
- 16 liens à justification conceptuelle : cylindre, ἡγεμονικόν, λόγος κριτής, assentiment rationnel, destin hypothétique, quatre catégories d'événements, asymétrie causale, etc.

## Contrôles

- Relance : aucune modification.
- Portes OK : `check_corpus_invariants --strict`, `check_greek_gate`, `check_citations_gate`, `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`, `check_kg_work_child_canonical`.
- `check_snapshot_passage_integrity` : ensemble des violations identique à celui du commit de base.
