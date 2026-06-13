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
