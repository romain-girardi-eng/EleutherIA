# Passage-corpus integrity issues (2026-06-13)

Found while manually grounding free-will arguments. These need re-ingestion
from critical editions (Goal C), NOT a blind merge — text differs per node.

## 1. Plotinus Ennead VI.8 — WRONG TEXT (flagged needs_reingest)
`passage_plotinus_vi_8_*` (21 nodes) carry Greek that is NOT Enn VI.8
("On Free Will and the Will of the One"): no ἐφ' ἡμῖν / βούλησις / αὐτεξ
vocabulary anywhere; vi_8_1 is soul-immortality material from another
Ennead. Flagged `text_integrity=misaligned_wrong_work`. Re-ingest VI.8
(Henry–Schwyzer / Armstrong LCL) and re-point the 1 citing argument
(argument_plotinus_freedom_argument) — which is currently (correctly)
grounded in Enn III.1.10 instead.

## 2. Plotinus Ennead III.1 — TWO namespaces, alignment differs
- `passage_plotinus_enn_iii_1_3_1_*` (10): has the CORRECT III.1.1 opening
  ("Ἅπαντα τὰ γινόμενα καὶ τὰ ὄντα ἤτοι κατ' αἰτίας…").
- `passage_plotinus_iii_1_*` (10): iii_1_1 is offset (mid-treatise text),
  but iii_1_10 IS the correct III.1.10 charioteer/self-determination passage
  (used for grounding). The namespace is internally inconsistent.
Action: reconcile to one correctly-aligned III.1 from a critical edition.

## 3. Augustine De Libero Arbitrio — TWO namespaces, format differs
- `passage_aug_lib_arb_*` (170, 1213 edge-refs): English summary + Latin
  excerpt; canonical (grounding target).
- `passage_aug_dla_*` (170, 344 edge-refs): raw continuous Latin.
Same loci, same work, different ingestion style. Reconcile (keep aug_lib_arb
as canonical; fold aug_dla's raw Latin into text_content) — careful merge,
not blind.

## 4. Full passage-corpus anomaly scan (2026-06-13, deterministic over 14,183 passages)
- **12 empty passages** (no text): `passage_origen_philocalia_22_1..10` (Philocalia 22 ingestion produced blanks — re-ingest from SC 226 Junod), `passage_dl_lives_3_1_16`, `passage_dl_lives_8_2_75` (near-empty fragment connectors). None are cited by grounding edges (no broken groundings).
- **~193 apparatus-OCR-contaminated** passages (critical apparatus mixed into text): all 76 `passage_meth_dla_*` (German GCS apparatus — SUPERSEDED for grounding by clean Scaife `passage_meth_autex_*`), `passage_aspasius_*`, scattered `aug_civ`/`aug_corrept`. Degraded but contain real text; re-ingest from clean sources when convenient.
- 122 "lang_mismatch" flags were FALSE POSITIVES (heuristic miscategorized Boethius/Calcidius as Greek authors — they are correctly Latin). No real language mismatches found.

## 5. De Dono Perseverantiae — still blocked (PDF-only)
Located in PL 45 cols 993-1035 (Documenta Catholica Omnia, PDF-only wrapper — no inline text) and CSEL 105 (Hombert 2018). Not on Latin Library / Scaife / augustinus.it as clean fetchable text. Needs the DCO PDF parsed or library access to ground argument_augustine_donum_perseverantiae.
