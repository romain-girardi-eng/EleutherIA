# GOAL 7 — Primary-source grounding of the dialectical synthesis

## Problem
The Scholar-RAG answer cites scholars' arguments ABOUT ancient authors but does NOT
quote the ancient authors' own texts, even when the corpus holds them in bulk. Live
example: a question on Epictetus' prohairesis produced the self-incriminating limitation
"the map does not contain a direct citation of Epictetus' Discourses or Manual" — yet the
corpus holds **~560 Epictetus passages** (Discourses 235+187+137, Enchiridion, Simplicius).
The ControversyMap retrieves scholar positions/arguments but fails to attach the contested
PRIMARY passages to the frames, so the synthesis never sees the Greek text.

## Done = perfect
- A question about a well-attested ancient author (Epictetus, Alexander, Chrysippus, Origen…)
  yields an answer that QUOTES the primary text directly: original Greek/Latin + English,
  with a correct locus (CTS/standard ref), woven into the dialectic.
- The ControversyMap's `contested_primary_passages` are populated from the corpus for the
  entities in the debate (via passage_citations + lemmatic/tree retrieval), not left empty.
- The synthesis prompt surfaces those passages; the model is instructed to quote them.
- No fabricated Greek/Latin — only verbatim corpus passages with verifiable passage_id.
- The "no direct citations" limitation never appears when the corpus DOES hold the texts.
- Verified live: the Epictetus question returns ≥2 verbatim Epictetus quotes (orig+EN).
