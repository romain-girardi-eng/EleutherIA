# Curator-artifact cleanup — applied

**Date:** 2026-08-14 · **Plan:** `data/audit/2026-08-14_curation_artifact_cleanup_plan.jsonl` (+ `.md`)
**Applied by:** `scripts/apply_2026_08_14_curation_artifact_cleanup.py` + `scripts/data_2026_08_14_curation_rewrites.py`
**Targets:** `data/kg/nodes.jsonl`, `data/kg/edges.jsonl` (working tree, not committed)

---

## 1. Counts

| operation | count |
|---|---|
| planned nodes | 284 |
| nodes rewritten | 281 |
| nodes deleted | 1 (`scholarly_argument_fee_determinism_and_predestination_1`) |
| nodes left untouched — escalation | 1 (`passage_alcin_alcinous_untitled_full_text`) |
| nodes with nothing to change in the description | 1 (`argument_cafma_framework_5a7b9e12`, artifact is in metadata) |
| authored prose span rewrites applied | 188 |
| `metadata.description_en` span rewrites | 15 (6 nodes) |
| label rewrites | 3 |
| metadata fixes | 1 |
| boilerplate paragraphs removed | 33 (27 by the applier + 6 folded into an authored span) |
| `[Vérif. …]` tags moved to `metadata.verification_notes` | 287 (of 289; the 2 remaining were on the deleted node) |
| edges deleted | 3 |

`[Vérif.]` tag classes, as classified by the plan: `confirms_ok` 41, `corrects_content` 113, `flags_spurious_reference` 119, `other` 16. Every one of the 287 surviving tags was removed from the reader-facing description and preserved verbatim in `metadata.verification_notes`.

## 2. Validation

| check | result |
|---|---|
| `nodes.jsonl` reparses, one JSON object per line | 19 991 lines, 0 parse failures |
| node count = before − 1 | 19 992 → 19 991 ✅ |
| duplicate node ids | 0 |
| `edges.jsonl` references to the deleted node | 0 (57 377 → 57 374) |
| any edge endpoint missing from `nodes.jsonl` | 0 |
| `[Vérif.` / `(Phase 12)` / `Avertissement méthodologique` / `Avertissement conceptuel` / `[Wave ` / `[Enrichissement` in any `description`, `label` or `metadata.description_en` | 0 |
| changed nodes with an empty description | 0 |
| `verification_notes` entries after the run | 288 (287 moved + 1 pre-existing) |
| `scripts/audit_structural.py` before vs after | 0 new findings, 1 resolved (`uncited_claim_node` on the deleted node) |
| `scripts/check_citations_gate.py` | OK (208 verified references) |
| `scripts/check_kg_work_id_uniqueness.py` | WARN — only pre-existing allowlisted collisions |
| `python3 -m scripts.check_corpus_invariants` | citations=19 893 passages=21 088, 0 dangling |
| ancient-language fabrication check | 0 — every Greek/Hebrew run in a rewritten span is verbatim from that node's own description or `[Vérif.]` tag |
| re-running the applier | byte-identical output (nodes stamped `metadata.curation_artifact_cleanup_2026_08_14`) |

### `scripts/check_greek_gate.py` — 2 pre-existing failures, not caused by this cleanup

The gate scans nodes whose line differs from `HEAD`, so it now sees two Greek runs that a clean tree never exposed. Both are **byte-identical to their `HEAD` text** — this cleanup did not introduce, alter or move them:

- `concept_axia_biblos_tou_theou_origen_amand1945` — `τὰ σημεῖα τοῦ θεοῦ`
- `concept_inner_freedom_alex` — `ἐνταῦθα λῃσταὶ καὶ κλέπται καὶ δικαστήρια καὶ οἱ καλούμενοι τύραννοι δοκοῦντες ἔχειν…` (Epictetus, *Diss.* I.9.12-17)

Run with `TLGE_DIR=~/Desktop/Romain/TLGE`, the gate reports both as `tlg_only` — **attested in TLG E**, merely missing an allowlist entry. Two follow-ups, both outside this cleanup's target files:

1. add the two runs to `data/audit/greek_allowlist.json` with their edition provenance;
2. `scripts/tlg_search.py` line 20 defaults `TLGE` to the literal string `[local-path]` (scrubbed during the history rewrite), so the gate's TLG fallback is inert unless `TLGE_DIR` is exported.

## 3. The deletion

`scholarly_argument_fee_determinism_and_predestination_1` — label `Fee on Romans 8:28-30 (placeholder — no argument on determinism)`

Removed. Its description states in plain French that the node is an extraction artifact and should be removed from the graph; Fee, *God's Empowering Presence* (1994), pp. 587-591 treats Rom 8:28-30 only on the grammatical subject of συνεργεῖ and advances no thesis on determinism or predestination.

Description as removed:

> Fee, God's Empowering Presence (1994), p. 587-591, traite bien Rm 8,28-30, mais son argumentation porte exclusivement sur le sujet grammatical de συνεργεῖ en 8,28 (l'Esprit, plutôt que « toutes choses » ou « Dieu »). Il n'avance aucune thèse sur le déterminisme ni sur la prédestination. Ce nœud est un artefact d'extraction et devrait être supprimé du graphe. [Vérif. 2026-08-02: Degenerate placeholder: the label/description is a self-referential note ('the table of contents indicates Fee treats Rom 8:28-30, but the provided excerpt does not include his actual argumentation') ] [Vérif. 2026-08-02: Resolved; remove the verification note.]

Edges removed (3):

- `483ba42e-9ab4-4bc8-8aa9-194a1c9c5575` — `scholarly_argument_fee_determinism_and_predestination_1` -created_by-> `scholar_fee_g`
- `51afafba-c8ce-4ead-9b5f-3fb719472be1` — `scholarly_work_fee_1994_god_s_empowering_presence_the_holy_spiri` -discusses-> `scholarly_argument_fee_determinism_and_predestination_1`
- `6efb20b0-6ca2-4e02-8ae6-6f116d168808` — `scholarly_argument_fee_determinism_and_predestination_1` -advanced_in-> `scholarly_work_fee_1994_god_s_empowering_presence_the_holy_spiri`

## 4. High-risk nodes — full before → after spans

The plan lists **83** high-risk lines. `scholarly_argument_fee_determinism_and_predestination_1` was deleted (§3) and `passage_alcin_alcinous_untitled_full_text` was escalated untouched (§6), leaving **81** rewritten here. For each: every authored span pair verbatim, the `[Vérif.]` tags moved to metadata, and any boilerplate paragraph deleted.

### `argument_adversity_exercise_seneca_g8h9i0j1`

- **type** argument · **label** Adversity-as-Exercise Argument (Seneca)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > The pivot is the maxim at 2.3 — "Marcet sine adversario virtus"

  after:

  > The pivot is the maxim at 2.4 — "Marcet sine adversario virtus"
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The pivot maxim 'Marcet sine adversario virtus' is at De Prov 2.4 in Reynolds' OCT and Basore's Loeb, not 2.3; the node anchors it to passage_sen_prov_2_3. Edition numbering varies by a subsection, so]`
- **description length** 2107 → 1885 chars
- **reviewer note** Tag truncated after 'Edition numbering varies by a subsection, so'; only the 2.3->2.4 relocation could be applied. The node's passage anchor (passage_sen_prov_2_3) is metadata and still needs re-pointing.

### `argument_arts_efficacy_alex`

- **type** argument · **label** Arts Efficacy Argument (Alexander)
- **issues** verif_tag · **tag classes** flags_spurious_reference, corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: The citation scheme 'Fat. 559-565' (and sub-references Fat. 560, 561-562, 563-564) does not correspond to any standard numbering of Alexander's De Fato (chapters 1-38; Bruns Suppl. Arist. II.2 pp. 164]`
  - `[Vérif. 2026-08-02: Audit note superseded: the flag is confirmed and now acted on. ; The seven source ids passage_alex_fat_559 ... passage_alex_fat_565 are dangling: no such passage nodes exist in data/kg/nodes.jsonl (each string occurs exactly once, inside this node itself). They sho → sources should be ["passage_alex_fat_11"] (plus passage_alex_fat_4 for the κατὰ λόγον division); delete passage_alex_fat_559 through passage_alex_fat_565]`
- **description length** 1890 → 1225 chars
- **reviewer note** The flagged citation scheme 'Fat. 559-565' and the dangling passage_alex_fat_559-565 source ids occur only in the tag and in the node's sources field, never in the description prose (which cites De Fato 11, Bruns ~178-180, and De Fato 6, Bruns ~169) - no prose edit possible. Tag #1 implies the kata logon division belongs to passage_alex_fat_4; the prose locus 'De Fato 6 (Bruns ~169)' was left untouched since the tag does not state it is wrong.

### `argument_cafma_character_contradiction_1f6g8i54`

- **type** argument · **label** CAFMA Argument IV: Contradiction of Character Change
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: 'Cicero, De Fato 28-33' is the lazy-argument section, not the anti-astrology section. For a natal-astrology refutation the relevant loci are De Fato §§11-17 and, for Carneades specifically, De Divinat]`
- **description length** 433 → 211 chars
- **reviewer note** Tag corrects the locus 'Cicero, De Fato 28-33' (lazy-argument section) to De Fato §§11-17 / De Divinatione, but that locus is not present in the description prose (it lives in node metadata); no prose assertion to fix.

### `argument_cafma_futility_of_effort_8c3d5f21`

- **type** argument · **label** CAFMA Argument I: Futility of Effort and Labor
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > if the outcome is predetermined regardless of effort?

  after:

  > if the outcome is predetermined regardless of effort? This is the moral and practical argument — belief in εἱμαρμένη produces slackening of effort, negligence and indolence — and not the lazy argument (ἀργὸς λόγος) of Cicero, De Fato 28-30, which concludes 'then do not call the doctor' and which Chrysippus rebutted with confatalia. Amand reconstructs it as argument no. 5 of the Carneadean moral anti-fatalist argumentation (Fatalisme et liberté, 583-584), while stressing that the whole reconstruction is conjectural. Its best ancient witness is Alexander of Aphrodisias, De Fato 21 (Bruns 191); Aulus Gellius NA VII.2 is Chrysippus on fate (the cylinder), not a witness to this argument.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03, corrected: this is not simply the ἀργὸς λόγος. The lazy argument (Cicero, De Fato 28-30) concludes 'then do not call the doctor' and is the fatalist sophism Chrysippus rebutted with confatalia — Amand himself treats it separately, as an objection Chrysippus sought to forestall (Fatalisme et liberté, 9 n. 3). The present argument is the moral/practical one: belief in εἱμαρμένη produces slackening of effort, negligence and indolence. Amand reconstructs it as argument no. 5 of the Carneadean moral anti-fatalist argumentation (583-584: 'La croyance à l'εἱμαρμένη entraîne nécessairement avec elle le relâchement de l'effort, la négligence et l'indolence... A quoi bon les peines et les sueurs pour acquérir la vertu ?'), while stressing that the whole reconstruction is conjectural. Its best ancient witness is Alexander of Aphrodisias, De Fato 21 (Bruns 191): under fatalism we would omit much of what ought to be done, becoming ἀργότεροι πρὸς τὸ δι' αὑτῶν τι ποιεῖν and unwilling to face τοὺς ἐπὶ τοῖς πραττομένοις καμάτους (TLG0732 verified). Aulus Gellius NA VII.2 is Chrysippus on fate (the cylinder), not a witness to this argument.]`
- **description length** 1435 → 911 chars

### `argument_cleanthes_hymn_to_zeus_argument_f71f5b37`

- **type** argument · **label** Cleanthes' Hymn to Zeus Argument
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Premise P4 'ducunt volentem fata, nolentem trahunt' is Seneca's own Latin coda (Ep. 107.11), not a line of Cleanthes; presenting it as a premise of Cleanthes' argument is doxographical contamination. ]`
- **description length** 443 → 221 chars
- **reviewer note** Tag corrects premise P4 ('ducunt volentem fata, nolentem trahunt' = Seneca, Ep. 107.11, not Cleanthes), but the premise list is not in the description prose (stored in metadata); the description makes no such attribution.

### `argument_four_categories_alex`

- **type** argument · **label** Four Categories of Being (Alexander)
- **issues** verif_tag · **tag classes** corrects_content, corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: Bruns 207-208 is not the locus of τὸ ἐφ' ἡμῖν. Occurrence-mapping of 'τὸ ἐφ' ἡμῖν' across De Fato in TLG 0732 shows a dense cluster at Bruns ~179-186 (chs. 11-15) and only isolated hits at 207; Bruns  → verified_reference should read: 'τὸ ἐφ' ἡμῖν discussed principally at De Fato 11-15, Bruns ~179-186; Bruns 207-208 (recorded in bruns_pages) is ch. 35, on merits, praise and blame']`
  - `[Vérif. 2026-08-03, TLG0732 : la liste avait été donnée sous forme compressée, qui n'est attestée nulle part. Rétablissement du texte verbatim d'Alexandre, De fato (TLG0732, dans la plage du traité) : « ἅμα δὲ τὸ σῴζειν τό τε ἀπὸ τύχης καὶ αὐτομάτως γίνεσθαί τινα καὶ εἶναι καὶ τὸ ἐφ' ἡμῖν καὶ τὸ ἐνδεχόμενον ἐν τοῖς πράγμασιν ἀλλ' οὐ φωνὴν μόνον » — « et en même temps de sauvegarder que certaines choses adviennent et sont par fortune et spontanément, ainsi que ce qui dépend de nous et le contingent, dans les choses mêmes et non seulement en paroles ».]`
- **description length** 2188 → 1225 chars
- **reviewer note** Both corrects_content tags target fields other than the description: tag #24 corrects the recorded verified_reference/bruns_pages (Bruns 207-208 is ch. 35, not the locus of τὸ ἐφ' ἡμῖν), a locus the prose never asserts; tag #25's restored verbatim Alexander quotation is already present in the prose. No prose edit needed.

### `argument_gerson_2014_plotinus_qualified_moral_responsibility_against_strawson`

- **type** argument · **label** Gerson 2014 — Plotinian qualified moral responsibility against Strawson's Basic Argument
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03: CONFIRMÉ sur le volume (extraction locale du PDF Destrée–Salles–Zingano 2014). Gerson est bien le 16e des 22 contributions ; titre : « Moral responsibility and what is 'up to us' in Plotinus », p. 251-263. Toutes les thèses du nœud sont textuellement dans le chapitre, y compris « Qualified moral responsibility will do the job, so long as the reality of the paradigm of unqualified moral responsibility is intact. That paradigm is the completely unfettered will » (p. 261) et le refus du binaire strawsonien. Seule correction : Gerson ne cite que Strawson 1994.]`
- **description length** 1488 → 904 chars
- **reviewer note** Tag is CONFIRME; its only correction ('Gerson ne cite que Strawson 1994') is already stated verbatim in the prose ('seule reference strawsonienne citee par Gerson'), so no prose change is required.

### `argument_origen_anti_astrological`

- **type** argument · **label** Origen's Anti-Astrological Argument for Free Will
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > in De Principiis III.1.5-6 and the Commentary on Genesis (fragments in Philocalia ch. 23):

  after:

  > in the Commentary on Genesis III (fragments in Philocalia ch. 23):
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Locus imprecision: the specifically anti-astrological arguments (Gen 1:14 'signs not causes'; the Jacob/Esau twin argument) belong to Origen's Commentary on Genesis III / Philocalia 23, NOT to De Prin]`
- **description length** 1741 → 1493 chars

### `argument_origen_argos_logos`

- **type** argument · **label** Origen's Refutation of the Argos Logos (Lazy Argument)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > In Contra Celsum II.20, Origen addresses Celsus's charge that Christian prayer and moral effort are futile if God's will is sovereign.

  after:

  > Contra Celsum II.20 is primarily the passage on foreknowledge and prophecy: Jesus's prediction of Judas's betrayal does not compel the betrayal, so what is foreknown is not thereby necessitated.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Characterization slippage: Contra Celsum II.20 is primarily the 'foreknowledge/prophecy does not necessitate' passage (Jesus's prediction of Judas's betrayal does not compel it) — i.e. the same presci]`
- **description length** 1820 → 1658 chars
- **reviewer note** Tag truncated mid-word ('the same presci'); the corrected characterization was recoverable, but the tag's further point about where the argos logos refutation proper is located was lost. The French header still lists Contra Celsum II.20 as source primaire and was left untouched.

### `argument_plutarch_providence_cooperation_8c5a9d3f`

- **type** argument · **label** Pseudo-Plutarch's Divine-Human Cooperation Argument (De Fato)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Developed to reconcile divine providence with human freedom.

  after:

  > Developed in the pseudonymous De Fato, whose author is conventionally designated Pseudo-Plutarch rather than Plutarch, to reconcile divine providence with human freedom.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The tripartite-providence doctrine occurs only in the pseudonymous De Fato (correctly signalled 'Pseudo-Plutarch' in the label), yet formulator is set to 'Plutarch'. De Sera Numinis Vindicta and De St]`
- **description length** 486 → 373 chars
- **reviewer note** Tag truncated at 'De Sera Numinis Vindicta and De St'; whatever it stated about those authentic works could not be recovered and is not reflected.

### `argument_pseudo_chrysostom_de_fato_v_apologetic_amand1945`

- **type** argument · **label** Pseudo-Chrysostom De Fato V — heimarmene comme barbarie injuste
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > εἰπέ μοι; »

  after:

  > εἰπέ μοι; » Réserve d'attribution : Amand intitule son chapitre « Jean Chrysostome » et attribue le Discours V à Chrysostome lui-même (avec un point d'interrogation), et le CPG 4367 range les six discours De fato et prouidentia parmi les œuvres authentiques ; l'étiquette « Pseudo-Chrysostome » retenue ici est donc une décision éditoriale moderne, non celle d'Amand.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03: RÉSOLU sur le texte d'Amand (extraction locale). L'argumentation (8e argument), les comparaisons du gouffre et de la maîtresse barbare, le pardon des ennemis, la question du bourbier/labyrinthe/tempête et l'Érinnye sont tous confirmés mot pour mot, traduction pp. 525-526, grec pp. 530-531, source PG 50, 765,24–768,44. RÉSERVE D'ATTRIBUTION : Amand intitule son chapitre « Jean Chrysostome » et attribue le Discours V à Chrysostome lui-même (avec un « ? ») ; le CPG 4367 range les six discours De fato et prouidentia parmi les œuvres authentiques. L'étiquette « Pseudo-Chrysostome » du nœud est donc une décision éditoriale moderne, non celle d'Amand.]`
- **description length** 1658 → 1340 chars

### `argument_qumran_predestination_c3d4e5f6`

- **type** argument · **label** Qumran Predestinarian Argument (Two Spirits)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Jörg Frey (1999) contends

  after:

  > Jörg Frey (1997) contends
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Jörg Frey's foundational essay on modified Qumran dualism is 'Different Patterns of Dualistic Thought in the Qumran Library' (1997, STDJ 23), not 1999; the 1999 date could not be confirmed and is like]`
- **description length** 2449 → 2227 chars

### `argument_spontaneity_within_determination_13fcd224`

- **type** argument · **label** Spontaneity within Determination
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (2)**

  before:

  > Prominent in Spinoza, Leibniz, and Hume.

  after:

  > Prominent in Spinoza, Leibniz, and Hume; as set out here the argument is a composite whose opening definitional premises are Spinoza's, its middle premises Leibniz's, and its closing premises Hume's.

  before:

  > Key texts: Spinoza, Ethics I, Def. 7; III, Prop. 2;

  after:

  > Key texts: Spinoza, Ethics I, Def. 7; I, Prop. 17, Cor. 2; III, Prop. 1-3;
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Misattribution at premise level. P1 is a verbatim translation of Spinoza's Ethica I, Definition 7 (and P2-P3 are Spinoza's absolute-freedom / adequate-vs-inadequate-ideas doctrine), yet all three carry primary_sources = work_leibniz_theodicee_1710. Correct grounding for P1-P3 is Spinoza, Ethica I, Def. 7; I, Prop. 17, Cor. 2 (solum Deum esse causam liberam); III, Prop. 1-3 (adequate vs. inadequate ideas). A single formulator 'Composite early-modern compatibilism: Spinoza (P1-P3), Leibniz (P4-P7), Hume (P8-P10)' misrepresents a synthetic argument whose opening definitional premises are Spinoza's, not Leibniz's; formulator and primary_source corrected to the composite Spinoza-Leibniz-Hume attribution (P1-P3 Spinoza, P4-P7 Leibniz Theodicee 288-302, P8-P10 Hume Enquiry VIII). REMAINING: the per-premise primary_sources of P1-P3 (and of P8-P10) still point to work_leibniz_theodicee_1710 because the KG contains no work node for Spinoza's Ethica or Hume's Enquiry; creating those two work nodes and re-pointing the premises is the outstanding step.]`
- **description length** 4365 → 3470 chars
- **reviewer note** The tag's REMAINING item (per-premise primary_sources of P1-P3 and P8-P10 still pointing at work_leibniz_theodicee_1710 for want of Spinoza/Hume work nodes) is metadata-level and cannot be fixed in prose.

### `argument_tatian_freewill_paradox`

- **type** argument · **label** Tatian's Free Will Paradox (Orat. 11.3-4)
- **issues** avertissement_boilerplate, phase_tag, verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > **Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*  
  >   
  > 

  after:

  > *(removed)*
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The anachronism-warning note misattributes the scholarly thesis. Dihle (The Theory of Will in Classical Antiquity, 1982) locates the invention of the concept of will in AUGUSTINE, not Origen. Dating t]`
- **boilerplate paragraph deleted** (`*(Phase 12)*` — misattributes Dihle 1982's Augustine thesis to Origen)
- **description length** 1692 → 660 chars

### `concept_autokrateia_alex`

- **type** concept · **label** Self-Governance / αὐτεξούσιον (Alexander)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The head-term αὐτοκράτεια (and αὐτοκρατής) is unattested in the entire Alexander corpus (0 TLG hits), so labelling this an Alexandrian term is a misattribution. Head term and transliteration are now corrected to αὐτεξούσιον / autexousion, which IS attested in Alexander (TLG0732, 3 hits), e.g. De Fato, Bruns 189.]`
- **description length** 1181 → 846 chars
- **reviewer note** The correction carried by the tag (head term autokrateia -> autexousion) is already applied in the prose, which opens on αὐτεξούσιον (to autexousion) and already flags the unattested formulation; no prose change needed.

### `concept_axia_biblos_tou_theou_origen_amand1945`

- **type** concept · **label** Τὰ σημεῖα τοῦ θεοῦ — le ciel comme livre digne de Dieu (Amand 1945)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > (the signs of God). Amand

  after:

  > (the signs of God), a phrase attested in Origen (TLG2042, Philocalia 23). Amand
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: This stored note falsely asserts the phrase is unattested ('No hit in any form in TLG … incl. Origen TLG2042'). In fact τὰ σημεῖα τοῦ θεοῦ IS attested in Origen (TLG2042, the Philocalia 23 celestial-w]`
- **description length** 903 → 735 chars

### `concept_bechirah_c1d2e3f4`

- **type** concept · **label** Choice/Free Will (Bechirah)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > where bechirah ḥofshit ("free choice") is declared a foundational principle

  after:

  > where free choice — Maimonides' own term in Hilkhot Teshuvah 5:1 is reshut (רשות, "permission/authority"), "bechirah ḥofshit" being the standard modern-Hebrew label rather than his ipsissima verba — is declared a foundational principle
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor precision: Maimonides' own term in Hilkhot Teshuvah 5:1 is reshut (רשות, 'permission/authority'); 'bechirah ḥofshit' is the standard modern-Hebrew label rather than his ipsissima verba, though h]`
- **description length** 2380 → 2318 chars

### `concept_belial_demonic_source_of_sin`

- **type** concept · **label** Belial (Demonic Source of Sin, Second Temple)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > much Second Temple sectarian literature, presented as

  after:

  > much Second Temple sectarian literature (the Qumran sectarian scrolls CD, 1QM, 1QS: 2nd c. BCE-1st c. CE), presented as
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Chronology is miscoded. Belial in the Qumran sectarian scrolls (CD, 1QM, 1QS) is Second Temple / Hellenistic (2nd c. BCE–1st c. CE). The top-level period field 'Late Antiquity' is wrong and contradict]`
- **description length** 1155 → 999 chars
- **reviewer note** The tag's actual target is the top-level `period` field ('Late Antiquity'), which prose edits cannot reach; the correct dating was written into the description so the reader is not misled.

### `concept_bondage_of_will_1c5x6y24`

- **type** concept · **label** Bondage of the Will (Servum Arbitrium)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > predestination and irresistible grace.

  after:

  > predestination and the grace that alone frees the enslaved will.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor characterization: 'irresistible grace' is TULIP/later-Reformed vocabulary; Luther speaks of the enslaved will freed by grace and of the 'beast ridden by God or Satan' rather than using that tech]`
- **description length** 488 → 292 chars

### `concept_boule_practical_wisdom`

- **type** concept · **label** Βουλή - Deliberative Capacity/Practical Wisdom
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > The Magna Moralia divides the rational soul

  after:

  > NE VI.1 (1139a11-15) divides the rational soul
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor: the division of the rational soul into βουλευτικόν and ἐπιστημονικόν is primarily Aristotle NE VI.1 (1139a11-15, logistikon=bouleutikon vs epistēmonikon); attributing it to the Magna Moralia is]`
- **description length** 2043 → 1824 chars

### `concept_concupiscence_epithumia_transmitted_bd8e2fc9`

- **type** concept · **label** Concupiscence (Epithumia) as Transmitted Consequence - Methodian Hamartiology
- **issues** verif_tag · **tag classes** flags_spurious_reference, corrects_content
- **description rewrites (2)**

  before:

  > non culpabilité héritée.

  after:

  > non culpabilité héritée ; le terme grec est toutefois une étiquette moderne et non un terme technique de l'auteur.

  before:

  > Methodius distinguishes inherited consequence from inherited culpability.

  after:

  > Methodius distinguishes inherited consequence from inherited culpability; the doctrine is carried by De resurrectione (Slavonic with Greek fragments) rather than by De autexousio.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: The verbatim Greek quotes — κηλῖδας κακίας ('stains of wickedness') and παρακοή — could not be confirmed as Methodius' exact words (0 hits in the local TLG search; and De resurrectione survives largel]`
  - `[Vérif. 2026-08-02: Audit note half-superseded: παρακοή IS confirmed verbatim; only κηλῖδας κακίας fails. ; ἐπιθυμία is not Methodius' technical term for a transmitted post-lapsarian desire. In De autexousio it occurs only in ordinary senses (§§1, 2, 19: desiring to hear, desire for knowledge of the truth). → Flag greek_term ἐπιθυμία as a modern label, not a Methodian technical term; the hamartiological doctrine is transmitted through De resurrectione (Slavonic + Greek fragments), not De autexousio.]`
- **description length** 1276 → 744 chars
- **reviewer note** The flagged Greek phrase and its gloss 'stains of wickedness' do not occur in the description prose (they sit in metadata greek_quotes), so the spurious-reference removal has no prose target.

### `concept_conditional_fate_9a5c8b4d`

- **type** concept · **label** conditional fate
- **issues** avertissement_boilerplate, phase_tag, verif_tag · **tag classes** flags_spurious_reference, corrects_content
- **description rewrites (2)**

  before:

  > **Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse classique de Dihle 1982 — confirmée et nuancée par Bobzien 1998, Frede 2011, Fürst 2022 — une invention dogmatique chrétienne datant d'Origène (vers 230-250 ap. J.-C.). Les concepts anciens antérieurs — ἑκούσιον (volontaire) chez Aristote, ἐφ' ἡμῖν (ce qui dépend de nous) chez les Stoïciens et Académiques, voluntas libera chez Cicéron — recouvrent un champ conceptuel partiel et non-substitutif. Lorsque la présente description emploie « libre arbitre » / « free will » de manière apparemment naïve, il faut entendre une approximation lexicale moderne ; pour le contenu doctrinal exact de l'auteur ancien, voir le terme grec/latin propre. *(Phase 12)*  
  >   
  > 

  after:

  > *(removed)*

  before:

  > Reconciles fate with free will by making outcomes dependent on free choices.

  after:

  > Reconciles fate with free will by making outcomes dependent on free choices. The compressed form 'εἱμαρμένη ἐξ ὑποθέσεως' is a modern shorthand and is not attested verbatim; the ancient term is ἐξ ὑποθέσεως, applied to εἱμαρμένη by Ps.-Plutarch, De fato 570B-C.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: The citation_corrected field is a no-op / botched patch: it reads "unattested «εἱμαρμένη ἐξ ὑποθέσεως» → attested «εἱμαρμένη ἐξ ὑποθέσεως»" — the 'wrong' and 'corrected' strings are identical, so it r ; The verified_reference field is internally contradictory and truncated: it states the exact Greek phrase 'occurs in no ancient author (0 hits)' and then says 'Ps-Plutarch's actual term for it is εἱμαρ ; greek_term 'εἱμαρμένη ἐξ ὑποθέσεως' is not attested verbatim (confirmed 0 TLG hits); it is a modern reconstruction. The genuinely attested elements are 'ἐξ ὑποθέσεως' and 'καθ' ὑπόθεσιν'. Should be fl]`
  - `[Vérif. 2026-08-03, TLG : la forme compressée « εἱμαρμένη ἐξ ὑποθέσεως » est une abréviation moderne (0 occurrence). Le terme antique est bien ἐξ ὑποθέσεως, appliqué à la εἱμαρμένη par [Plutarque], De fato 570B-C : « οἷον μέν ἐστι τὸ ἐξ ὑποθέσεως, ὅτι δὲ τοιοῦτον καὶ ἡ εἱμαρμένη, ὁριζέσθω· ἐξ ὑποθέσεως δὴ ἔφαμεν τὸ μὴ καθ' ἑαυτὸ τιθέμενον, ἀλλά πως ἑτέρῳ τινὶ ὡς ἀληθῶς ὑποτεθέν » — « ce qu'est le conditionnel, et que la destinée est bien telle, soit maintenant défini : nous avons dit conditionnel ce qui n'est pas posé par soi, mais réellement subordonné à quelque autre chose ». La doctrine est donc authentique.]`
- **boilerplate paragraph deleted** (`*(Phase 12)*` — misattributes Dihle 1982's Augustine thesis to Origen)
- **description length** 2372 → 499 chars
- **reviewer note** The flagged Greek term lives in the node's greek_term / citation_corrected metadata, not in the prose; the correction was added to the prose so it survives tag removal.

### `concept_four_categories_alex`

- **type** concept · **label** Four Categories of Sublunary Events (Alexander)
- **issues** verif_tag · **tag classes** corrects_content, flags_spurious_reference
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-03 : les quatre expressions grecques sont authentiques et toutes présentes chez Alexandre ; la classification quadripartite elle-même est une reconstruction de Sharples 1983, non une liste explicite d'Alexandre. Les key_passages « 422-424, 430 » ne renvoient à rien (hors de la pagination Bruns du De fato, 164-212 ; aucun passage_alex_fat_42x/430 dans le graphe) et ont été retirés. bruns_pages « 207-208 » reste à confirmer contre l'édition Bruns.]`
  - `[Vérif. 2026-08-02: '422-424' and '430' correspond to nothing: they exceed the Bruns range of the De fato (164–212), and no passage_alex_fat_422/423/424/430 exists anywhere in data/kg/nodes.jsonl (grep returns zero). ; Same: unresolvable passage identifier.]`
- **description length** 1624 → 898 chars
- **reviewer note** The correction carried by tag #141 (the quadripartite classification is Sharples's 1983 reconstruction, not an explicit list in Alexander) is already stated in the prose; the flagged '422-424' / '430' occur only in metadata key_passages. No prose edit needed.

### `concept_gnomic_will_gnome`

- **type** concept · **label** Gnomic will (γνώμη / θέλημα γνωμικόν)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Maximus claims to distinguish 28 senses of γνώμη in Scripture and the Fathers (Disp. Pyrr., PG 91:312B–C).

  after:

  > Maximus sets out the many senses of γνώμη in Scripture and the Fathers chiefly in Opusculum 14 (PG 91:151C–153A).
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The enumeration of the many senses of γνώμη is set out chiefly in Opusculum 14 (PG 91:151C–153A); attaching the '28 senses' claim specifically to Disp. Pyrr. PG 91:312B–C is a mislocated locus. The co]`
- **description length** 1367 → 1152 chars
- **reviewer note** The tag is truncated at 'The co…', so whether the figure '28' is itself correct could not be recovered; the count was dropped rather than moved to the new locus.

### `concept_heimarmene_conditional_amand1945`

- **type** concept · **label** εἱμαρμένη conditionnelle (ἐξ ὑποθέσεως) — platonisme moyen (Pseudo-Plutarque, Albinus)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > and its parallel in Albinus, Didaskalikos ch. 26

  after:

  > and its parallel in the Didaskalikos ch. 26 (ascribed to Albinus by Amand 1945, but now generally attributed to Alcinous, Whittaker 1990)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor authorship note: the Didaskalikos is now generally ascribed to Alcinous rather than Albinus (Whittaker 1990). The node follows Amand's 1945 identification ('Albinus'), which is defensible as an ]`
- **description length** 1126 → 993 chars

### `concept_horme_alex`

- **type** concept · **label** Hormē (ὁρμή) - Impulse
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03: RÉSOLU par dépouillement de ὁρμή/προαίρεσις dans le De fato (TLG0732). La définition de la proaíresis est en Bruns ~179 (De fato 11) : « ἡ γὰρ ἐπὶ τὸ προκριθὲν ἐκ τῆς βουλῆς μετὰ ὀρέξεως ὁρμὴ προαίρεσις » — donc « Fat. 175 » est faux. Le passage sur le mouvement animal par impulsion est en Bruns ~181 (De fato 13) et non 199 ; la formule exacte est « τὴν καθ' ὁρμὴν κίνησιν », et Alexandre y RAPPORTE la doctrine stoïcienne, il ne l'énonce pas en son nom.]`
- **description length** 1668 → 1190 chars
- **reviewer note** The tag is a RÉSOLU record: its corrections (proairesis definition at Bruns ~179 / De fato 11, not 'Fat. 175'; animal impulse at Bruns ~181 / De fato 13, not 199; Alexander reporting rather than asserting the Stoic doctrine) are already incorporated verbatim in the description. Nothing left to merge.

### `concept_hypothetical_fate_middle_platonist`

- **type** concept · **label** Hypothetical Fate (ex hypotheseos)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > De Fato 568A-574F

  after:

  > De Fato 568B-574F
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Very minor: the ps.-Plutarch De Fato begins at Stephanus 568B, not 568A (568A closes the preceding treatise). Not worth a hard correction.]`
- **description length** 1423 → 1263 chars

### `concept_metriopatheia_moderation_passions`

- **type** concept · **label** Metriopatheia (Moderation of Passions)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (2)**

  before:

  > (Galen's term is ἡ ἄλογος δύναμις, PHP; the phrase ἐθισμὸς ἄλογος is unattested in Greek and has been removed)

  after:

  > (Galen's term for it is ἡ ἄλογος δύναμις, PHP)

  before:

  > According to Galen's reports (PHP 5.6, Fragment 161 EK), Posidonius taught

  after:

  > According to Galen's reports (PHP 5.6, Fragment 161 EK — reference still to be checked against De Lacy, CMG V.4.1.2, and Edelstein-Kidd II), Posidonius taught
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03 : ἐθισμὸς ἄλογος est inattesté dans tout le TLG (0 occurrence) et a été retiré ; le vocabulaire de Galien pour la partie non rationnelle est ἡ ἄλογος δύναμις (PHP). μετριοπάθεια dans le TLG est philonienne et plutarchéenne, jamais posidonienne. Le renvoi « PHP 5.6, fr. 161 EK » reste à vérifier sur De Lacy (CMG V.4.1.2) et sur Edelstein–Kidd II (commentaire).]`
- **description length** 1915 → 1553 chars

### `concept_occasionalism_a5b6c7d8`

- **type** concept · **label** Occasionalism
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > (Al-Ash'ari, Al-Ghazali)

  after:

  > (Al-Ash'ari, d. 936; Al-Ghazali, d. 1111)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor: period is set to 'Early Modern', but the doctrine described is substantially medieval (Ash'arite kalām: al-Ash'arī d.936, al-Ghazālī d.1111). The node correctly covers both strands; only the si]`
- **description length** 1088 → 883 chars
- **reviewer note** The real error is the node's period field ('Early Modern'), which cannot be fixed from the description; the prose now dates the Ash'arite strand explicitly.

### `concept_original_sin`

- **type** concept · **label** Original Sin (Peccatum Originale)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Broken correction record: the 'unattested → attested' pair is identical on both sides ('προπατορικὴ ἁμαρτία → προπατορικὴ ἁμαρτία'), conveying no correction. The genuine mismatch is Greek-vs-translite ; Field is truncated mid-sentence ('Two further caveats: it') and internally garbled: it labels the displayed feminine ἁμαρτία as 'neuter ἁμάρτημα'. Should read that the feminine προπατορικὴ ἁμαρτία is ]`
- **description length** 1072 → 647 chars
- **reviewer note** The tag concerns a broken correction record about the Greek term προπατορικὴ ἁμαρτία (transliteration mismatch, garbled 'neuter' label). No Greek and no such correction pair appears in the description, which is entirely English prose about Augustine's doctrine. Fix belongs in metadata; the tag is also truncated mid-sentence.

### `concept_patet_exitus_seneca_e6f7g8h9`

- **type** concept · **label** Patet Exitus (The Open Door) - Seneca
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > attested for Zeno and Cleanthes (DL VII.28, 176), but the Greek sources

  after:

  > defined at DL VII.130 (DL VII.28 and VII.176 report instead the self-inflicted deaths of Zeno and Cleanthes), but the Greek sources
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor citation imprecision: the Stoic doctrine/term 'εὔλογος ἐξαγωγή' as such is defined at Diog. Laert. VII.130. DL VII.28 and VII.176 report the (self-inflicted) deaths of Zeno and Cleanthes respect]`
- **description length** 2242 → 2080 chars

### `concept_perfect_vs_antecedent_causes_8w3x5z21`

- **type** concept · **label** Perfect vs. Antecedent Causes (Chrysippean Distinction)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > but cylinder's shape (perfect cause) determines that it rolls rather than slides.

  after:

  > but cylinder's shape (perfect cause, αὐτοτελὲς αἴτιον — a term confirmed in Clement, Stromateis VIII.9, and Ps.-Galen, Definitiones Medicae) determines that it rolls rather than slides.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Broken record: 'unattested «αὐτοτελὲς αἴτιον» → attested «αὐτοτελὲς αἴτιον»' is identical on both sides. In fact αὐτοτελὲς αἴτιον IS attested (Clement Strom.; Ps.-Galen Def. Med.), so the 'unattested' ; Field is truncated mid-word ('confirmed in the corpus: Clement Stro'). Should state that αὐτοτελὲς αἴτιον is confirmed in Clement Stromateis VIII.9 and Ps.-Galen Definitiones Medicae.]`
- **description length** 823 → 519 chars

### `concept_pithanon_8f3a6d2c`

- **type** concept · **label** pithanon (τὸ πιθανόν)
- **issues** verif_tag, wave_tag · **tag classes** corrects_content, confirms_ok
- **description rewrites (2)**

  before:

  > [Wave 7 — résumé initial] L'impression plausible

  after:

  > L'impression plausible

  before:

  > [Enrichissement B2 — Amand 1945, p. 44-45, Intro §II ch. II §III] Amand caractérise

  after:

  > Amand (1945, p. 44-45, Intro §II ch. II §III) caractérise
- **metadata.description_en** cleaned (2 spans)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: The tripartite technical criteria (πιθανή / ἀπερίσπαστος / διεξωδευμένη-περιωδευμένη) are canonically reported by Sextus Empiricus, Adv. Math. 7.166–184, NOT by Cicero, Academica II.34.108. The node/A]`
  - `[Vérif. 2026-08-02: Audit note superseded: the flag is confirmed and now acted on.]`
- **description length** 2009 → 1651 chars
- **reviewer note** The corrects_content tag (criteria are in Sextus, Adv. Math. 7.166–184, not Cicero, Academica II.34.108) is already satisfied by the prose, which credits Sextus Empiricus, Adv. Math. VII 166-189 and never cites the Academica; the small line-range divergence (189 vs 184) was left untouched. metadata.description_en carries the same two markers and cannot be reached by a description edit.

### `concept_thelesis_willing_87d2b3cf`

- **type** concept · **label** Θέλησις (Thelēsis) - Willing/Volition
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Septuagint translators preferred θέλησις over βούλησις for rendering

  after:

  > Septuagint translators preferred the θελ- root — chiefly θέλημα, θέλησις itself remaining rare (Proverbs, Ecclesiastes, 2 Chronicles, Wisdom) — over βούλησις for rendering
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Overstated: the common LXX word for will is θέλημα (frequent), while θέλησις is rare in the LXX (Prov, Eccl, 2 Chr, Wisdom). 'preferred θέλησις over βούλησις' should be softened to the θελ- root / θέλ]`
- **description length** 1184 → 1064 chars

### `concept_tripartite_descent_iamblichus`

- **type** concept · **label** Tripartite Descent Typology - Iamblichus's Rehabilitation of Embodiment
- **issues** verif_tag · **tag classes** corrects_content, confirms_ok
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: Label/description mismatch. The label 'Tripartite Descent Typology' points to Iamblichus's threefold classification of the MODES of descent (souls descend for salvation of this realm / for training an]`
  - `[Vérif. 2026-08-02: Stale note superseded.]`
- **description length** 1316 → 1050 chars
- **reviewer note** Tag #0's correction (the label points to the threefold classification of the MODES of descent, not to the whole-soul-descent thesis) is already applied in the prose, which opens on 'threefold classification of the MODES of the soul's descent' and already parenthesises the whole-soul thesis as a separate matter; tag #1 is a superseded stale note.

### `concept_voluntas_y7z8a9b0`

- **type** concept · **label** Will (Voluntas)
- **issues** verif_tag · **tag classes** corrects_content, confirms_ok
- **description rewrites (1)**

  before:

  > at Ep. 71.36 the same theme appears in verbal form, 'magna pars est profectus velle proficere … volo et mente tota volo'.

  after:

  > at Ep. 71.36 the same theme appears in verbal form, 'magna pars est profectus velle proficere … volo et mente tota volo'; and at Ep. 20.5 wisdom is consistent right willing, 'semper idem velle atque idem nolle… ut rectum sit quod velis'.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: Could not verify 'voluntas recta' at Seneca Ep. 71.36. The locus for wisdom as consistent right willing ('semper idem velle atque idem nolle… ut rectum sit quod velis') is Ep. 20.5, not 71.36. The 71.]`
  - `[Vérif. 2026-08-02: Audit note superseded: the flag is confirmed and now acted on, with an attested replacement locus.]`
- **description length** 2848 → 2622 chars
- **reviewer note** The erroneous 'voluntas recta' @ Ep. 71.36 sits in metadata, not in the prose; the corrected Ep. 20.5 locus and its quotation (both supplied verbatim by the tag) were added instead.

### `passage_eusebius_he_iv_26_melito_fr_iv`

- **type** work · **label** Melito, Peri Pascha fr. IV
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03: RÉSOLU par lecture du fichier de preuve sur disque (SC31_Melito_Sardensis_Fragments_IV…bilingue.txt). Le texte réellement porté par ce nœud est le seul paragraphe d'Eus., HE IV,26,3 (Bardy, SC 31, p. 209) citant l'incipit du Peri Pascha : « Ἐπὶ Σερουιλλίου Παύλου ἀνθυπάτου τῆς Ἀσίας… ». Ce n'est donc pas une « tradition alternative » de l'homélie mais la notice de datation initiale. L'incohérence SC 123 / SC 31 est levée : SC 31 = édition-source du texte ingéré ; SC 123 (Perler) = édition critique de référence du corpus mélitonien.]`
- **description length** 1158 → 599 chars
- **reviewer note** Tag is a RESOLVED note; the description already states exactly what it confirms (Eus. HE IV.26.3 dating notice from the opening of the Peri Pascha, SC 31 Bardy as source edition, SC 123 Perler as reference critical edition).

### `person_boethius_480_524ce_w3x4y5z6`

- **type** person · **label** Boethius (Anicius Manlius Severinus Boethius)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  >  and deeply influenced Islamic philosophy (Al-Farabi, Avicenna, Averroes)

  after:

  > *(removed)*
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Overreach / factual error: Boethius did not 'deeply influence Islamic philosophy.' His Consolatio and logical works belong to the Latin tradition and were not transmitted to the Arabic falsafa; al-Fār]`
- **description length** 2075 → 1780 chars

### `person_cyril_alexandria`

- **type** person · **label** Cyril of Alexandria
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Distinguished plenitudo libertatis (pre-Fall) vs. liberum arbitrium (post-Fall). Source: Boulnois (2000).

  after:

  > The distinction between plenitudo libertatis (pre-Fall) and liberum arbitrium (post-Fall) applies Latin terminology to a Greek author and remains to be documented, as does the reference to Boulnois.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03 : formule grecque authentifiée mot pour mot dans le TLG (Glaphyres sur la Genèse I.4, PG 69, 24-25), mais unique — le qualificatif « récurrent » a été corrigé. La distinction plenitudo libertatis / liberum arbitrium (terminologie latine appliquée à un auteur grec) et la référence « Boulnois (2000) » (ni titre ni page ; la monographie principale de M.-O. Boulnois est Le paradoxe trinitaire chez Cyrille d'Alexandrie, 1994) restent à documenter.]`
- **description length** 1114 → 740 chars
- **reviewer note** The tag notes that Boulnois's principal monograph is Le paradoxe trinitaire chez Cyrille d'Alexandrie (1994); I did not substitute it for '(2000)' because the tag does not assert that this is the work actually meant. The dubious year was dropped instead.

### `person_cyril_jerusalem_315_386`

- **type** person · **label** Cyrille de Jérusalem
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (2)**

  before:

  > Catechesis IV traite explicitement de la liberté et de la providence ; Catechesis XIII développe une argumentation anti-fataliste anti-astrologique.

  after:

  > Catechesis IV traite explicitement de la liberté et de la providence, et c'est là que se trouve l'argumentation anti-fataliste et anti-astrologique (en particulier §18-21 : l'âme se détermine elle-même, le péché ne vient pas des astres) ; la Catechesis XIII, elle, porte sur le Christ crucifié et enseveli.

  before:

  > SC 126 (Catéchèses mystagogiques, éd. Piédagnel 1966) ; SC 384 (Procatéchèse + Cat. I-IV, éd. Bouvet 1992).

  after:

  > SC 126 (Catéchèses mystagogiques, éd. Piédagnel 1966), seul volume cyrillien paru dans cette collection.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The anti-fatalist / anti-astrological argument is located in Catechesis IV (esp. §18-21, the self-determined soul, sin not from the stars), NOT Catechesis XIII. Cat. XIII is 'On Christ Crucified and B ; SC 384 (attributed to 'Bouvet 1992') as the prebaptismal Procatechesis + Cat. I-IV could not be confirmed. In the Sources Chrétiennes series only Cyril's Mystagogical Catecheses are published (SC 126,]`
- **description length** 1078 → 808 chars

### `person_cyrus_alexandria_d641`

- **type** person · **label** Cyrus d'Alexandrie
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Cyrus reste en charge sous Héraclius ; démis par l'empereur après la chute d'Alexandrie aux mains des Arabes ('Amr ibn al-'As, 642).

  after:

  > Cyrus est rappelé et disgracié par Héraclius en 640-641, du vivant de l'empereur, pour avoir négocié avec les Arabes, puis réhabilité ; Alexandrie tombe aux mains des Arabes ('Amr ibn al-'As) en 642.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Chronology of the dismissal is muddled: Cyrus was summoned/disgraced by Heraclius in 640-641 (before Heraclius's death) for negotiating with the Arabs, then rehabilitated; he did not survive to be 'dé]`
- **description length** 1027 → 872 chars
- **reviewer note** Tag truncated at "he did not survive to be 'dé'"; what he did not survive to do could not be recovered, so the incorrect post-conquest dismissal was dropped rather than replaced.

### `person_julian_eclanum_d454`

- **type** person · **label** Julian of Eclanum
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The works list double-counts a single work: 'To Florus' (Ad Florum) IS the eight-book polemic against Augustine, so 'Eight books against Augustine (mostly lost)' is the same work listed a second time ]`
- **description length** 481 → 259 chars
- **reviewer note** The double-counted title ('To Florus' = the eight books against Augustine) is in the node's works list, not in the description prose; no prose change possible. The works metadata still needs de-duplication.

### `person_methodius_olympus_d311`

- **type** person · **label** Methodius of Olympus
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The TLG URN 'TLG 2959.001' is assigned to De autexusio, but 2959.001 is the Symposium (Convivium decem virginum); De autexusio (De libero arbitrio) is TLG 2959.002. The node internally duplicates 2959 → TLG 2959.002 (De autexusio); 2959.001 belongs to the Symposium]`
- **description length** 910 → 623 chars
- **reviewer note** The correction concerns TLG URNs (2959.001 = Symposium, De autexusio = 2959.002) held in the node's metadata; no TLG URN appears in the description prose, which names the three dialogues without work identifiers.

### `person_rene_descartes_1aa22692`

- **type** person · **label** René Descartes
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > is acknowledged as the "lowest degree of freedom" (infimus gradus libertatis).

  after:

  > is acknowledged as the "lowest degree of freedom": the phrase infimus gradus libertatis itself comes from Meditatio IV (AT VII 58: indifferentia illa ... est infimus gradus libertatis), not from the Principia.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The Latin tag 'infimus gradus libertatis' ("lowest degree of freedom") is from Meditatio IV (AT VII 58: 'indifferentia illa ... est infimus gradus libertatis'), NOT from Principia Philosophiae I.39–41]`
- **description length** 3091 → 3000 chars

### `sc123_melito_apologia_ad_antoninum`

- **type** work · **label** Melito, Apologia ad Antoninum (fr.)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > l'identification la plus probable étant Marc Aurèle 161-180 ap. J.-C., bien que la tradition manuscrite oscille

  after:

  > l'excerptum nomme Hadrien comme grand-père du destinataire et Antonin le Pieux comme son père, ce qui identifie ce dernier à Marc Aurèle, 161-180 ap. J.-C.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor: the excerpt itself (verified in the local SC-31 text) names Hadrian as the addressee's grandfather and Antoninus Pius as his father, which identifies the addressee as Marcus Aurelius. Framing t]`
- **description length** 1534 → 1356 chars

### `sc123_melito_de_anima_et_corpore`

- **type** work · **label** Melito, De Anima et Corpore (fr.)
- **issues** verif_tag · **tag classes** corrects_content, confirms_ok
- **description rewrites (1)**

  before:

  >  and should not be stated as settled

  after:

  > *(removed)*
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: The Melitonian authorship of the De anima et corpore homily is disputed in scholarship (widely regarded as spurious / a later Melitonian homily), not the settled fact the flat attribution implies. Can]`
  - `[Vérif. 2026-08-02: Resolved; remove the verification note.]`
- **description length** 851 → 532 chars

### `sc379_athenagoras_legatio`

- **type** work · **label** Athenagoras, Legatio pro Christianis
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor: the Legatio has 37 chapters; metadata records 38. Not in the displayed description.]`
- **description length** 1561 → 1449 chars
- **reviewer note** tag's correction (the Legatio has 37 chapters, metadata records 38) is explicitly 'not in the displayed description' — metadata-only fix

### `scholar_harl_m`

- **type** person · **label** Marguerite Harl
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  >  Co-éditrice (avec Doutreleau) des Homélies sur la Genèse d'Origène (SC 7bis, Cerf 1976, rééd.).

  after:

  > *(removed)*
- **metadata.key_works** — list_remove `Origène, Homélies sur la Genèse — SC 7bis (Cerf 1976, avec Doutreleau)`
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Marguerite Harl did not co-edit SC 7bis (Homélies sur la Genèse). That volume is Doutreleau (Latin text, trans., notes) with an introduction by de Lubac and Doutreleau. Harl's Origen SC work is the Ph ; Same erroneous attribution in key_works list: Harl is not a co-editor of SC 7bis Homélies sur la Genèse. Remove this list element.]`
- **description length** 931 → 480 chars

### `scholar_list_n`

- **type** person · **label** Nicholas List
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Early Christian studies, Middle Platonism, Justin Martyr

  after:

  > Research fields recorded as Early Christian studies, Middle Platonism and Justin Martyr. These belong to a different scholar than the List discussed by Fürst 2022, which is Christian List, the LSE philosopher of 'compatibilist libertarianism' (Why Free Will Is Real, 2019; German edition Warum der freie Wille existiert, 2021).
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: This field conflates two different scholars. Fürst 2022 discusses CHRISTIAN List (LSE philosopher, Why Free Will Is Real 2019 / Warum der freie Wille existiert 2021, 'compatibilist libertarianism') — ]`
- **description length** 278 → 327 chars
- **reviewer note** The tag is truncated before naming the other scholar, so the node label 'Nicholas List' could not be verified or corrected; the description now states the conflation explicitly rather than silently attaching patristic research fields to a philosopher of mind. The node probably needs splitting into two person nodes.

### `scholar_position_karamanolis_early_christian_engagement`

- **type** argument · **label** Early Christian philosophical engagement with Greek thought
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor imprecision. 'Epektasis' (perpetual progress toward God, from Phil 3:13) is distinctively Gregory of Nyssa's doctrine, not a shared Cappadocian tenet, and it is a biblical/theological concept, n]`
- **description length** 576 → 354 chars
- **reviewer note** tag corrects an 'epektasis' claim (Gregory of Nyssa's doctrine, not a shared Cappadocian tenet) that does not occur anywhere in the description; no prose edit possible

### `scholar_wolfson_h`

- **type** person · **label** Harry Austryn Wolfson
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Work/date mismatch. The node links scholarly_work 'wolfson_1947_philo_on_free_will_and_the_historical_influence', but that title and the pagination (131-169 / at 133-134) belong to Wolfson's HTR ARTIC ; The description contains an embedded verification note that is truncated/garbled mid-sentence ('...The 1947 date belongs to his book "Philo", which ha]`
- **description length** 494 → 120 chars
- **reviewer note** The correction concerns the linked scholarly_work id/date (wolfson_1947_... vs the HTR article) and an embedded note in another field; the description prose is only a research-interests list with no date or title to correct.

### `scholarly_argument_crouzel_manuscript_tradition_and_textu_1`

- **type** argument · **label** Simonetti (SC 312): Koetschau's edition prefers the lectio facilior, banalizing Origen's text
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: scholar_id points to scholar_crouzel_henri, but the cited textual-critical section is Simonetti's; attribution should be to Manlio Simonetti. SC 312's Avant-Propos: 'Ce tome V... contient surtout les index. Ceux-ci sont precedes par des "complements sur la tradition manuscrite" rediges par M. Simonetti et par quelques "Addenda et Corrigenda" qui, avec les index, sont l'oeuvre de H. Crouzel.' Label and engages_with_scholars corrected accordingly. REMAINING: metadata.scholar_id still reads scholar_crouzel_henri because the KG contains no person/scholar node for Manlio Simonetti; creating one and re-pointing scholar_id (and the created_by edge) is the outstanding step. scholarly_work_id remains valid, SC 312 being the joint Crouzel-Simonetti volume.]`
- **description length** 1125 → 347 chars
- **reviewer note** Tag's correction (attribution to Manlio Simonetti rather than Crouzel) is already carried by the description prose; the outstanding step is metadata.scholar_id, which still points to scholar_crouzel_henri because no Simonetti node exists.

### `scholarly_argument_f_rst_origen_s_metaphysics_of_freedo_5`

- **type** argument · **label** Fürst: Argues Origen develops a 'theology of freedom' (Theologie der Freiheit) where Go
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor/soft: 'De principiis I.3.8 (God as spirit and movement)' — I.3 is 'De Spiritu Sancto' (participation in the Holy Spirit); Origen's 'God is spirit' (John 4:24, deus spiritus est) is argued in De ]`
- **description length** 594 → 372 chars
- **reviewer note** The corrected locus 'De principiis I.3.8 (God as spirit and movement)' does not occur in the description (which cites only 1 Cor 15:28); it lives in a separate evidence/locus field. The tag is moreover truncated before naming the right De principiis passage, so no replacement locus is recoverable.

### `scholarly_argument_gourinat_chrysippus_s_compatibilism_0`

- **type** argument · **label** D'Jeranian: Chrysippus's attempt to reconcile fate and moral responsibility through the cyli
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Chrysippus's compatibilism — Chrysippus's attempt

  after:

  > Chrysippus's compatibilism (D'Jeranian) — Chrysippus's attempt
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The linked work node is slugged 'scholarly_work_gourinat_0_responsabilit_morale_et_destin_une_r_pon', which attributes this article to Gourinat. The source file confirms the author is Olivier D'Jerani]`
- **description length** 550 → 341 chars
- **reviewer note** the linked work node slug 'scholarly_work_gourinat_0_responsabilit_morale_et_destin_une_r_pon' and this node's id still attribute the article to Gourinat — outside the description field

### `scholarly_argument_gourinat_cicero_s_critique_of_chrysippu_2`

- **type** argument · **label** D'Jeranian: Cicero demonstrates that Chrysippus's strategy of making assent autonomous while
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Cicero's critique of Chrysippus — Cicero demonstrates

  after:

  > Cicero's critique of Chrysippus, as read by Olivier D'Jeranian — Cicero demonstrates
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Same misattribution as the sibling node: scholarly_work_id 'scholarly_work_gourinat_0_...' names Gourinat as author of an article actually written by Olivier D'Jeranian (confirmed in the source file).]`
- **description length** 672 → 481 chars
- **reviewer note** The misattribution itself lives in scholarly_work_id 'scholarly_work_gourinat_0_...' and still needs correcting in metadata.

### `scholarly_argument_gourinat_epictetus_s_original_contribut_1`

- **type** argument · **label** D'Jeranian: Epictetus developed new theoretical elements that allow for an original articula
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: scholarly_work_id 'scholarly_work_gourinat_0_...' misattributes this D'Jeranian article to Gourinat (source file confirms author = Olivier D'Jeranian). Node label/scholar_id correctly credit D'Jerania]`
- **description length** 709 → 487 chars
- **reviewer note** The correction concerns the scholarly_work_id misattributing the article to Gourinat instead of D'Jeranian; the description prose names neither scholar, so no prose edit applies.

### `scholarly_argument_gourinat_the_anti_fatalist_objection_an_4`

- **type** argument · **label** D'Jeranian: The anti-fatalist objection, as reported by Cicero (De fato 40) and Aulus Gelliu
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The argument is correctly attributed to the FIGURE D'Jeranian (label + scholar_id scholar_djeranian_o), but the scholarly_work_id 'scholarly_work_gourinat_0_responsabilit_morale_et_destin_une_r_pon' a]`
- **description length** 620 → 398 chars
- **reviewer note** The correction concerns a mis-set scholarly_work_id ('...gourinat...' on a D'Jeranian argument); Gourinat is nowhere named in the description prose, so this is a metadata fix with no prose target.

### `scholarly_argument_gourinat_the_cylinder_analogy_and_its_l_3`

- **type** argument · **label** D'Jeranian: Chrysippus's cylinder analogy, which makes fate the antecedent and auxiliary cau
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Same provenance issue as node _4: D'Jeranian's article (scholar_djeranian_o) is filed under scholarly_work_id 'scholarly_work_gourinat_0_...' and a 'gourinat'-prefixed node id. Attribution of the argu]`
- **description length** 707 → 485 chars
- **reviewer note** The correction is a provenance/ID issue (D'Jeranian's article filed under a 'gourinat' work id and node id); neither scholar is named in the description prose, and the tag is truncated at 'Attribution of the argu', so no prose edit was made.

### `scholarly_argument_grant_origen_s_self_castration_and_a_0`

- **type** argument · **label** Grant: Grant treats Origen's self-castration and extreme ascetic practices (rejecting G
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The ZKG 71 (1960) study on Origen's life is by Manfred (M.) Hornschuh, not 'G. Hornschuh'. Grant's own footnote 4 as OCR'd reads 'G. Horaschuh', so the KG faithfully copies a source-side error; the co]`
- **description length** 621 → 399 chars
- **reviewer note** The correction concerns the ZKG 71 (1960) attribution 'G. Hornschuh' → Manfred Hornschuh, but neither 'Hornschuh' nor the ZKG reference appears in the description; the error is in the node's metadata/sources and cannot be fixed by a description edit.

### `scholarly_argument_l_hr_clement_of_alexandria_s_adapta_2`

- **type** argument · **label** Löhr: Clement, despite having first-hand knowledge of Valentinian sources and understa
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The author of 'Gnostic Determinism Reconsidered' (VC 46, 1992) is Winrich A. Löhr; the filename renders him 'Alfried Löhr' (his middle name Alfried used as first name). The visible label/description/s → Winrich A. Löhr (not 'Alfried Löhr')]`
- **description length** 749 → 488 chars
- **reviewer note** The correction ('Alfried Löhr' → Winrich A. Löhr) targets the node id/label and author metadata; the name does not occur in the description prose, so no prose edit applies.

### `scholarly_argument_l_hr_clement_s_use_of_stoic_concept_3`

- **type** argument · **label** Löhr: Clement paradoxically employed Stoic philosophical concepts—particularly the fac
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Same author-name issue as the sibling node: the VC 1992 article is by Winrich A. Löhr; the filename reads 'Alfried Löhr'. Cosmetic, in the path only; scholar_id scholar_l_hr_w and label 'Löhr' are cor → Winrich A. Löhr (not 'Alfried Löhr')]`
- **description length** 765 → 504 chars
- **reviewer note** tag's correction (Winrich A. Löhr, not 'Alfried Löhr') is explicitly cosmetic and in the source file path only; the description names no author

### `scholarly_argument_linjamaa_free_will_and_moral_accountabi_1`

- **type** argument · **label** Linjamaa: The Tripartite Tractate employs concepts of will (Greek: thelēma/boulē) and self
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Stance label 'critiques' toward Origen is the wrong direction: Linjamaa situates TriTrac as one of the determinist targets whom Origen polemicized against (De Principiis / Contra Celsum), i.e. Origen ]`
- **description length** 680 → 458 chars
- **reviewer note** The correction concerns the node's stance label toward Origen (metadata); the description prose states no stance toward Origen, so no prose edit applies.

### `scholarly_argument_meyer_epicurean_freedom_from_determi_4`

- **type** argument · **label** Meyer: Epicurus rejects fate as a 'mistress' (Men. 133), not as the modern compatibility question
- **issues** curator_prose · **tag classes** —
- **description rewrites (1)**

  before:

  >  [Re-scopé 2026-08-03 : ce nœud attribuait auparavant à Meyer la thèse doxographique standard selon laquelle Épicure aurait introduit la παρέγκλισις / clinamen pour sauver la liberté contre le déterminisme démocritéen. Meyer n'écrit rien de tel : « swerve », « clinamen » et « declinatio » ont ZÉRO occurrence dans tout Ancient Ethics (2008). Pour cette thèse, voir les nœuds correctement sourcés argument_epicurean_swerve_for_freedom_m4n5o6p7 (Lucrèce DRN II.251-293 ; Cicéron, De fato 22-23 et De nat. deor. I.69-70 ; Fowler 1983, Englert 1987, Purinton 1999) et, pour la position contraire, pub_bobzien_2000_epicurus_free_will, scholarly_argument_o_keefe_role_of_the_swerve_in_epicurus_1 et scholar_position_furley_epicurus_swerve_indirect.]

  after:

  >  Meyer does not advance the standard doxographic thesis that Epicurus introduced the swerve (παρέγκλισις / clinamen) to rescue freedom against Democritean determinism: "swerve", "clinamen" and "declinatio" have zero occurrences anywhere in Ancient Ethics (2008).
- **description length** 1794 → 1312 chars
- **reviewer note** The block's pointers to other KG nodes and the bibliography attached to them (Lucretius DRN II.251-293; Cicero De fato 22-23, De nat. deor. I.69-70; Fowler 1983, Englert 1987, Purinton 1999; Bobzien, O'Keefe, Furley) were dropped from the description per the plan and should be preserved in metadata.rescope_note.

### `scholarly_argument_pouderon_resurrection_and_moral_account_3`

- **type** argument · **label** Pouderon: The Traité sur la résurrection presupposes free moral agency as foundational: re
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: page_range 62-67 of the monograph is the section 'L'authenticité du Traité sur la résurrection' (introduction/authenticity), not where Pouderon analyzes the Traité's justice/free-agency argument (deve]`
- **description length** 529 → 307 chars
- **reviewer note** The faulty page_range 62-67 (= the authenticity section) is metadata and does not appear in the description prose; the tag is truncated before giving the correct pages, so the right range is unrecoverable here.

### `scholarly_argument_rousseau_marcus_s_deterministic_numerol_2`

- **type** argument · **label** Rousseau: The edition presents Irenaeus's report that Marcus the Magician used numerical a
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-03: RÉSOLU par collation de SC 264 (texte et traduction, extraction locale). Loci I.14-16 confirmés (capitula ch. X « per numeros et per syllabas », titre courant « Marc le Magicien : grammatologie et arithmologie »). Le cadrage « détermination des destinées / le nom contient le destin » n'a AUCUN appui dans I.14-16 : il s'agit de la genèse des vingt-quatre éléments et du calcul des noms divins. Reformulé. L'élément fataliste réel est le reproche d'astrologie en I.15.6 (« Astrologiae cognitor et magicae artis ») et la comparaison aux « mathematici » en I.24.7.]`
- **description length** 1156 → 572 chars
- **reviewer note** The tag is marked RÉSOLU / 'Reformulé' and its correction is already in the prose: the grammatology/arithmology is referred to the generation of the Pleroma rather than to individual destinies, with the astrology charge at I.15.6 and the 'mathematici' comparison at I.24.7. No further edit.

### `scholarly_argument_telfer_new_testament_and_autexousia_7`

- **type** argument · **label** Telfer: The notion of autexousia as a prerogative of all men is abundantly present in Sc
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > , though Paul does not use the term αὐτεξούσιος itself

  after:

  > . The added remark that Paul does not use the term αὐτεξούσιος itself is editorial, not Telfer's
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The trailing clause 'though Paul does not use the term αὐτεξούσιος itself' is an editorial addition NOT found in Telfer's article, which does not single out Paul here. It is factually true (αὐτεξούσιο]`
- **description length** 477 → 297 chars

### `scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3`

- **type** argument · **label** Wolfson: Philo's position resembles Plato's Timaeus in structure (universal soul governin
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > (p. 135ff)

  after:

  > (HTR 35, 1942, p. 135ff)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Several Timaeus loci diverge from Wolfson's own footnotes (nn. 20-27, p. 134): Wolfson cites the rational/irrational souls at 'Tim. 42E ff.; 69C' (node has 69C-72D), the conflict between them at 'Tim. ; Linked work is dated 1947 (scholarly_work_wolfson_1947...), but pages 131-134 are the pagination of Wolfson's HTR article of 1942 (HTR 35: 131-169). The 1947 date belongs to his book 'Philo', which ha]`
- **description length** 1071 → 660 chars
- **reviewer note** The Timaeus loci correction (node's '69C-72D' vs Wolfson's 'Tim. 42E ff.; 69C') applies to metadata loci absent from the description, and the tag is truncated on the second locus; the linked work node dated 1947 still needs re-pointing to the 1942 article.

### `synthesis_amand1945_cicero_ch2i_cadre`

- **type** synthesis · **label** Amand 1945 — Cadre Cicéron : transmetteur latin indirect du De fato carnéadien
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > probablement issu d'Antiochus d'Ascalon ou de Posidonius

  after:

  > probablement issu de Clitomaque ou d'Antiochus d'Ascalon (les candidats retenus par Amand, à la suite de Lörcher 1907)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Two soft points not supported by Amand as stated. (1) The node lists the possible source as 'Antiochus of Ascalon OR Posidonius'; Amand's candidates (following Lörcher 1907) are Clitomachus/Antiochus ]`
- **description length** 1260 → 1100 chars
- **reviewer note** The tag announces two soft points but is truncated after the first; point (2) is unrecoverable and no edit was made for it.

### `synthesis_amand1945_hierocles_bizarre_carneadean_inversion`

- **type** synthesis · **label** Hiéroclès et l'inversion bizarre du topos carnéadien (Amand 1945)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  >  — proximité doctrinale qu'Amand juge probable (Phase 9 EleutherIA confirme contact philosophique direct)

  after:

  > , sans qu'il affirme pour autant un contact doctrinal établi
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Editorial overreach. Amand says only that Hierocles's developments 'rappellent singulièrement' Origen's effort (a striking resemblance); he does not assert, and the sources do not establish, confirmed]`
- **description length** 1639 → 1372 chars

### `synthesis_amand1945_origen_pivot_witness`

- **type** synthesis · **label** Amand 1945 — Origène = 1er témoin patristique pivot de la lignée carnéadienne
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (2)**

  before:

  > Synthèse Amand : Origène = 1er témoin patristique de la lignée carnéadienne anti-fataliste, pivot historiographique du Livre II d'Amand.

  after:

  > Synthèse Amand : Origène, pivot historiographique du Livre II d'Amand dans la lignée carnéadienne anti-fataliste — il n'ouvre pas la série patristique, puisque Justin (Ch. I), Tatien (Ch. II), Bardesane (Ch. III) et Clément d'Alexandrie (Ch. IV) le précèdent.

  before:

  > les 6 témoins de la reconstruction carnéadienne

  after:

  > les témoins de la reconstruction carnéadienne
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Count/membership error: text says « 6 témoins » but lists 7 items. Amand's six principal 'textes témoins' of the Carneadean moral argument are Cicéron, Philon, Favorinus (ap. Gellius XIV.1), pseudo-Pl ; Same spurious 7th witness in English metadata. ; Characterization imprecise: 'Origène = 1er témoin patristique' overstates. In Amand's Livre II, Justin (Ch.I), Tatien (Ch.II), Bardesane (Ch.III) and Clément d'Alexandrie (Ch.IV) all precede Origène (]`
- **description length** 1297 → 944 chars
- **reviewer note** The tag names only part of Amand's six textes témoins (Cicéron, Philon, Favorinus ap. Gellius XIV.1, pseudo-Pl…) before truncating, so the spurious 7th list item could not be identified; the erroneous count was removed instead of a witness.

### `synthesis_amand1945_tatian_no_carneadean_link`

- **type** synthesis · **label** Tatien = sans dependance directe ou indirecte de Carneade (Amand 1945)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Tatien est un 'Tertullien des Grecs' violent et fanatique qui puise son antifatalisme

  after:

  > Tatien, dont Amand releve la 'violente polemique' et la 'passion et zele outre', puise son antifatalisme
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The epithet 'Tertullien des Grecs' (in quotes, framed as Amand's characterization) is NOT found in Amand's text. Amand does describe Tatian's 'violente polémique' and 'passion et zèle outré', so 'viol]`
- **description length** 952 → 749 chars
- **reviewer note** Quotations rendered without accents to match this description's existing unaccented French.

### `synthesis_destree2014_ch02_destree_plato_er`

- **type** synthesis · **label** Destrée — How can our fate be up to us? Plato and the myth of Er
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > (Tim. 86b)

  after:

  > (Tim. 86d-e)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor locus imprecision: the 'no one is voluntarily wicked' / vice-as-ignorance claim in the Timaeus is at 86d–e (86b only opens the diseases-of-the-soul discussion). Consider 'Tim. 86b-e' or '86d-e'.]`
- **description length** 855 → 635 chars

### `synthesis_destree2014_ch11_salles_epictetus_causal`

- **type** synthesis · **label** Salles — Epictetus and the causal conception of moral responsibility and what is eph' hêmin
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > (De Fato 40-44)

  after:

  > (De Fato 42-43)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Minor locus imprecision: Cicero's cylinder simile proper is De Fato 42–43 (broader context 39–45); '40–44' is slightly loose but acceptable.]`
- **description length** 988 → 826 chars

### `work_augustine_de_correptione`

- **type** work · **label** De Correptione et Gratia (On Rebuke and Grace)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: CSEL 92 attribution unverified and probably wrong: CSEL 92 (Folliet 2000) contains De perfectione iustitiae hominis, De gestis Pelagii, De gratia Christi et de peccato originali, De natura et origine ]`
- **description length** 618 → 396 chars
- **reviewer note** The doubtful CSEL 92 attribution does not occur in the description prose (it is a metadata edition field), so no prose edit is possible.

### `work_augustine_retractationes`

- **type** work · **label** Augustin, Retractationes
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (2)**

  before:

  > trois rétractations sont pivots

  after:

  > deux rétractations sont pivots

  before:

  >  ; (c) *Retract.* II.66(92) — sur *De Gratia et Libero Arbitrio* (c. 426-427), traité de coordination anti-pélagienne.

  after:

  > . Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le *De Gratia et Libero Arbitrio* (426/427) — ne figurent pas parmi les 93 œuvres passées en revue dans les *Retractationes*.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: De gratia et libero arbitrio (426/427) is NOT among the 93 works reviewed in the Retractationes. The anti-Pelagian treatises to Hadrumetum/Gaul (De gratia et libero arbitrio, De correptione et gratia,]`
- **description length** 1644 → 1499 chars
- **reviewer note** Tag truncated after 'De correptione et gratia,' - the full list of excluded anti-Pelagian treatises could not be reproduced; the Retract. II.66(92) locus given for the removed item was dropped as unverified.

### `work_consolation_v_boethius_524ce_x4y5z6a7`

- **type** work · **label** Consolation of Philosophy Book V - Boethius
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  >  and was transmitted to Islamic philosophy (Avicenna, Averroes)

  after:

  > ; the Latin Consolatio was, however, unknown to the Arabic philosophical tradition — Avicenna and Averroes did not read Boethius, and the foreknowledge/eternity problem was treated independently there
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Historically false: Boethius' Latin Consolatio was unknown to the Arabic philosophical tradition; Avicenna and Averroes did not read Boethius. The foreknowledge/eternity problem was treated independen]`
- **description length** 2130 → 2045 chars

### `work_exodus_c9d0e1f2`

- **type** work · **label** Exodus (Shemot)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Second book of Torah narrating Israel's liberation from Egypt.

  after:

  > Second book of the Torah, narrating Israel's liberation from Egypt; a Pentateuchal composition for which Second Temple Judaism is the reception context rather than the period of composition.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Period tagged 'Second Temple Judaism', but Exodus is a Pentateuchal/pre-exilic-to-Persian composition set in the 2nd millennium BCE — Second Temple (516 BCE–70 CE) is the reception context, not the wo]`
- **description length** 403 → 309 chars
- **reviewer note** The node's period field still reads 'Second Temple Judaism' and needs changing separately; the tag is truncated before naming the replacement period.

### `work_ezekiel_g3h4i5j6`

- **type** work · **label** Ezekiel (Yechezkel)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Major prophetic book emphasizing individual moral responsibility.

  after:

  > Major prophetic book of the exilic period (6th c. BCE) emphasizing individual moral responsibility.
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Period tagged 'Second Temple Judaism' though Ezekiel is exilic (6th c. BCE, pre-Second-Temple). Same systemic bucketing note as Exodus — minor, not a description-level error.]`
- **description length** 427 → 265 chars
- **reviewer note** metadata.period still reads 'Second Temple Judaism'; the tag calls this a systemic bucketing issue shared with Exodus

### `work_maximus_opuscula`

- **type** work · **label** Maximus the Confessor, Opuscula theologica et polemica
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > Opusculum 3, Opusculum 16 (on the Tomos to Marinus).

  after:

  > Opusculum 3, and the Tomus ad Marinum on the two wills, usually identified as Opusculum 20 (the letter to Marinus on the procession of the Spirit being Opusculum 10).
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: The Opusculum-16 identification is doubtful: the 'Tomus ad Marinum' on the two wills is usually Opusc. 20, and the letter to Marinus on the Spirit's procession is Opusc. 10. The parenthetical '(on the]`
- **description length** 984 → 876 chars

### `work_methodius_de_libero_arbitrio`

- **type** work · **label** Methodius, De Libero Arbitrio (Περὶ τοῦ αὐτεξουσίου)
- **issues** verif_tag · **tag classes** corrects_content
- **description rewrites (1)**

  before:

  > between three characters: Orthodox (ΟΡΘΟΔ.), Aglaophon (ΑΓΛΑΟΦΩΝ), and possibly Valentinus (ΟΥΑΛ.)

  after:

  > between an orthodox speaker (ΟΡΘΟΔ.) and his adversaries, one of whom is possibly Valentinus (ΟΥΑΛ.)
- **`[Vérif.]` tags moved to `metadata.verification_notes` (1)**
  - `[Vérif. 2026-08-02: Character conflated with a different work: Aglaophon is the eponymous interlocutor of Methodius's De resurrectione (subtitled 'Aglaophon'), not of De autexusio/De libero arbitrio, whose adversaries ar]`
- **description length** 1146 → 926 chars
- **reviewer note** Tag truncated before naming De autexusio's actual adversaries, so the removed character could not be replaced by the correct one.

### `work_ps_clement_homiliae`

- **type** work · **label** Pseudo-Clement, Homiliae
- **issues** verif_tag · **tag classes** corrects_content, corrects_content
- **description rewrites** none — the flagged item is not asserted in the prose (see note below); only the tag was removed
- **`[Vérif.]` tags moved to `metadata.verification_notes` (2)**
  - `[Vérif. 2026-08-02: Internal loci not independently confirmable and likely imprecise. The fuller nomima barbarika / Book-of-the-Laws-of-Countries (Bardaisan) argument is Recogn. IX.19–29; the Homilies' fate/genesis debat]`
  - `[Vérif. 2026-08-02: Stale note superseded by the two fixes above.]`
- **description length** 1421 → 1132 chars
- **reviewer note** The second tag marks the first as stale and superseded by fixes already present in the prose (Recogn. IX.19–29 for the fuller Bardaisanite argument; 'laws of the countries' rather than 'nomima barbarika'), so no further prose change. The Hom. XIV.3–11 locus remains as stored, since the tag is truncated before stating the corrected reference.
## 5. Mechanical and medium-risk changes — grouped

### 5.1 `*(Phase 12)*` boilerplate paragraphs — 33 nodes, deleted outright

Variant A (`**Avertissement méthodologique**`, 808 chars, byte-identical) on 24 nodes; variant B (`Avertissement conceptuel — anachronisme du « libre arbitre »`) on 9 (8 bolded + `synthesis_cic_fat_in_nostra_potestate` unbolded). Both were deleted, **not** relocated to metadata: variant B attributes to Dihle 1982 the location of the "invention of free will" in Origen, whereas Dihle locates it in Augustine, and it states the contested modern "invention of the will" paradigm as plain fact. `concept_ananke_necessity_democritus_h8i9j0k1` is the one node where the paragraph does not start at offset 0 — its preceding **Étymologie** paragraph is preserved (verified: description 1 246 → 1524 chars, the Étymologie text intact).

- `argument_agent_causation_alex`
- `argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188`
- `argument_augustines_antipelagian_argument_grace_necessity_0b29401f`
- `argument_bobzien_2001_b1_cylinder_in_later_fate_theory`
- `argument_bobzien_2001_b1_philopator_late_compatibilism`
- `argument_bobzien_2001_b1_rise_fall_freedom_problem`
- `argument_divine_hardening_problem_y9z0a1b2`
- `argument_epicurean_swerve_for_freedom_m4n5o6p7`
- `argument_homonymy_alex`
- `argument_irenaeus_recapitulation_theodicy`
- `argument_justin_angel_fall`
- `argument_justin_antifatalism`
- `argument_justin_prophecy_freedom`
- `argument_origen_prescience_causality`
- `argument_tatian_freewill_paradox`
- `concept_academic_skepticism_epoche_n4o5p6q7`
- `concept_ananke_necessity_democritus_h8i9j0k1`
- `concept_causal_asymmetry_alex`
- `concept_causal_conception_eph_hemin_salles`
- `concept_chrysippean_compatibilism_bobzien`
- `concept_conditional_fate_9a5c8b4d`
- `concept_eph_hemin_two_sided_potestative`
- `concept_kompatibilistischer_libertarismus_origenian`
- `concept_mr2_ability_responsibility`
- `concept_pelagianism`
- `concept_philopator_compatibilism_bobzien`
- `concept_saving_teaching_alex`
- `concept_stoic_causal_principle`
- `concept_two_sidedness_eph_hemin`
- `debate_source_of_action_90c57974`
- `synthesis_bobzien2001_ch6_chrysippean_compatibilism`
- `synthesis_bobzien2001_ch8_philopator_late_stoic`
- `synthesis_cic_fat_in_nostra_potestate`

### 5.2 `confirms_ok` tags — tag removed, prose untouched

41 of the 289 tags are `confirms_ok`. On the 6 nodes listed below that class is the node's *only* tag,
so the whole node is a pure strip; the other `confirms_ok` tags sit on nodes that also carry a
`corrects_content` / `flags_spurious_reference` tag and are covered by §4 and §5.4.

Including the 5 the plan singles out as carrying TLG-E collation evidence (`argument_irenaeus_recapitulation_theodicy`, `argument_wager_alex`, `concept_exousia_alex`, `concept_platonic_vs_christian_original_sin`, `concept_practical_life_alex`) — same treatment: the collation evidence now lives in `metadata.verification_notes`, so nothing was destroyed.

- `argument_augustine_deficient_cause`
- `argument_wager_alex`
- `concept_cyclical_return_great_year`
- `concept_exousia_alex`
- `concept_platonic_vs_christian_original_sin`
- `concept_practical_life_alex`

### 5.3 `wave_tag` / `batch_ref` markers — converted to prose citations (11 nodes)

The batch-marker framing was dropped; every real bibliographic locus survives as a normal citation. `argument_carneadean_general_theme_amand1945` is a false positive per the plan and was left alone (it is not in the plan's 284 lines).

| node | before | after |
|---|---|---|
| `argument_aristotelian_legislator_practice_amand1945` | `argument_carneadean_legislation_amand1945` du batch B1) | `argument_carneadean_legislation_amand1945`) |
| `argument_carneades_autonomous_mental_causation_argument_4e7e9250` | [Wave 7 — résumé initial]  | *(removed)* |
| `argument_carneades_autonomous_mental_causation_argument_4e7e9250` | [Enrichissement B2 — Amand 1945, p. 66-68, Intro §II.III.IV] Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion | Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion technique de la doctrine chrysippéenne de l'εἱμαρμένη (Amand |
| `concept_pithanon_8f3a6d2c` | [Wave 7 — résumé initial] L'impression plausible | L'impression plausible |
| `concept_pithanon_8f3a6d2c` | [Enrichissement B2 — Amand 1945, p. 44-45, Intro §II ch. II §III] Amand caractérise | Amand (1945, p. 44-45, Intro §II ch. II §III) caractérise |
| `debate_stoic_academic_hellenistic` | [Wave 7 — résumé initial] La confrontation | La confrontation |
| `debate_stoic_academic_hellenistic` | [Enrichissement B2 — Amand 1945, p. 41-43 + p. 46-48, Intro §II ch. II] Amand caractérise | Amand (1945, p. 41-43 et p. 46-48, Intro §II ch. II) caractérise |
| `debate_stoic_academic_hellenistic` | (les 6 titres argumentatifs reconstruits en Conclusion = matière du batch B1) | (les 6 titres argumentatifs reconstruits dans la Conclusion d'Amand 1945) |
| `person_carneades_214_129bce_l2m3n4o5` | [Wave 7 — résumé initial] Carnéade de Cyrène | Carnéade de Cyrène |
| `person_carneades_214_129bce_l2m3n4o5` | [Enrichissement B2 — Amand 1945, p. 41-46, Intro §II ch. II §I-III] Amand insiste | Amand 1945, p. 41-46 (Introduction §II ch. II §I-III), insiste |
| `person_favorinus_of_arles_9n4o6q32` | [Wave 7 — note] Favorinus est avant tout | Favorinus est avant tout |
| `person_favorinus_of_arles_9n4o6q32` | [Enrichissement B3 — Amand 1945, p. 96-100, ll. 5919-6128] Selon Amand | Selon Amand (1945, p. 96-100, ll. 5919-6128) |
| `person_favorinus_of_arles_9n4o6q32` | (cf. argument dixième B3, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius) | (cf. le dixième argument, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius) |
| `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` | [Résumé initial — Wave 7]  | *(removed)* |
| `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` | [Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15] Thèse centrale | Thèse centrale |
| `scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4` | [Résumé initial — Wave 7] Reconstruction of Carneades' | Reconstruction of Carneades' |
| `scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4` | [Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15] Aveu philologique | Aveu philologique |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` |  du batch B1) | ) |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` | voir nœuds B1 argument_carneadean_*_amand1945 | voir les nœuds argument_carneadean_*_amand1945 |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` |  Annonce explicitement à ne PAS dupliquer avec B1 : ce nœud Ch. III est une porte d'entrée structurelle, B1 est le développement détaillé avec témoins | *(removed)* |
| `work_de_fato_cicero_44bce_b9c4e5d2` | [Enrichissement B3 — Amand 1945, p. 78-80, ll. 5131-5230] D'après Amand, le De Fato | D'après Amand 1945 (p. 78-80), le De Fato |
| `work_philo_de_providentia` | [Enrichissement B3 — Amand 1945, p. 80-95, ll. 5232-5917] D'après Amand (suivant Wendland 1892 et Bousset 1915) | D'après Amand 1945, p. 80-95 (suivant Wendland 1892 et Bousset 1915) |

The same markers were also removed from `metadata.description_en` on 6 nodes (`argument_carneades_autonomous_mental_causation_argument_4e7e9250`, `concept_pithanon_8f3a6d2c`, `debate_stoic_academic_hellenistic`, `person_carneades_214_129bce_l2m3n4o5`, `person_favorinus_of_arles_9n4o6q32`, `synthesis_amand1945_ch3_moral_argument_scheme_announcement`), and the ` = B1` suffix from the last one's label.

### 5.4 Medium/low-risk `corrects_content` and `flags_spurious_reference` merges (101 nodes, 128 spans)

Every span pair is in `scripts/data_2026_08_14_curation_rewrites.py`, each one preceded by a `#` comment quoting the tag that justifies it. Summary of what was changed:

| node | before | after |
|---|---|---|
| `argument_agent_causation_alex` | **Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de  | *(removed)* |
| `argument_aristotelian_legislator_practice_amand1945` | `argument_carneadean_legislation_amand1945` du batch B1) | `argument_carneadean_legislation_amand1945`) |
| `argument_bardesanes_nomima_barbarika_amplified` | Selon Amand p. 243, Bardesane est « peut-être le premier à avoir mis en œuvre » l'argument carnéadien des nomima barbarika « avec une telle profusion et une tel | Selon Amand, Bardesane serait l'un des premiers à mettre en œuvre l'argument carnéadien des nomima barbarika avec une profusion et une exactitude documentaires  |
| `argument_cafma_futility_of_legislation_9d4e6g32` |  (átopoï nómoï) | *(removed)* |
| `argument_cafma_futility_of_piety_2g7h9j65` |  (anóētoï euchaí) | *(removed)* |
| `argument_carneades_autonomous_mental_causation_argument_4e7e9250` | [Wave 7 — résumé initial]  | *(removed)* |
| `argument_carneades_autonomous_mental_causation_argument_4e7e9250` | [Enrichissement B2 — Amand 1945, p. 66-68, Intro §II.III.IV] Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion technique | Amand reconstruit la polémique antifataliste « directe » de Carnéade comme une discussion technique de la doctrine chrysippéenne de l'εἱμαρμένη (Amand 1945, p.  |
| `argument_causal_asymmetry_alex` | Alexander argues for fundamental asymmetry between past and future: | Alexander's text has been read as establishing an asymmetry between past and future: |
| `argument_causal_asymmetry_alex` | Conclusion: Causal relations exhibit temporal asymmetry - necessity runs backward, contingency forward | Conclusion: what the text itself affirms is the fixity of the past (not even the gods can undo what has happened) and the non-necessitation of the future by div |
| `argument_character_change_alex` | Sources: Fat. 511-512: Nature contributes but doesn't necessitate; many change characters Fat. 513-514: Bad become good through philosophy; good become bad thro | Sources: Alexander, De Fato (Bruns, pp. 164-212): nature contributes to character but does not necessitate it, and many people do change their characters; the b |
| `argument_clement_grace_synergy_assent` | , Strom. II.2.8.4) | , Strom. II) |
| `argument_common_cause_alex` | koinē aitia (common cause) is a genuine technical notion in the ancient causal-classification debate. | koinē aitia (common cause) is a modern label for a notion at work in the ancient causal-classification debate; it is not Alexander's own term (no attestation in |
| `argument_common_cause_alex` | [Corrected 2026-08-03 against TLG0732: the argument IS in De Fato (Bruns 195). Alexander's own wording is not κοινὴ αἰτία (0 hits anywhere in his corpus) but τὸ | The argument itself is in De Fato (Bruns 195). Alexander's own wording is τὸ αὐτὸ αἴτιον |
| `argument_common_cause_alex` | And he denies that these events are interlocked ἁλύσεως δίκην, 'after the manner of a chain'.] | And he denies that these events are interlocked ἁλύσεως δίκην, 'after the manner of a chain'. |
| `argument_gomez_2014_chrysippus_reactive_compatibilism` | Argument scholarly de Laura Liliana Gómez, « Chrysippean compatibilistic theory of fate, what is up to us, and moral responsibility », in Destrée/Salles/Zingano | Argument scholarly issu du volume Destrée/Salles/Zingano (éd.), What is Up to Us? (Academia Verlag 2014), sur la théorie chrysippéenne du destin, de ce qui dépe |
| `argument_human_dignity_alex` |  [Specific Bruns/chapter loci 'Fat. 628-636' removed as fabricated: De Fato in Bruns SA 2.2 ends at p. 212.] |  (De Fato in Bruns SA 2.2 ends at p. 212; page-loci beyond that point are spurious.) |
| `argument_irenaeus_recapitulation_theodicy` | **Avertissement conceptuel — anachronisme du « libre arbitre »** : la catégorie de « libre arbitre » (αὐτεξούσιον / liberum arbitrium) est, selon la thèse class | *(removed)* |
| `argument_irenaeus_recapitulation_theodicy` |  (τὴν ἀσθένειαν τοῦ ἀνθρώπου) | *(removed)* |
| `argument_irenaeus_recapitulation_theodicy` |  (ἀνακεφαλαιόω) | *(removed)* |
| `argument_lazy_argument_alex` | Argument: THE LAZY Argument (ἈΡΓῸΣ ΛΌΓΟΣ)  | Argument:  |
| `argument_lazy_argument_alex` | Fat. 265: Choose "pleasures with ease" since outcomes are fixed. Fat. 267: "Neglect of the noble by all". Fat. 268: Noble things require toil; vices come easily | In De Fato Alexander spells out these consequences: choosing "pleasures with ease" since outcomes are fixed; the "Neglect of the noble by all"; noble things req |
| `argument_nemesius_nat_hom_37_38_middle_platonism_critique_amand1945` |  (arrêt du soleil par Josué, conservation en vie d'Énoch et Élie) | *(removed)* |
| `argument_origen_prescience_causality` | **Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de  | *(removed)* |
| `argument_pseudo_chrysostom_de_fato_v_witness6_amand1945` | Amand publie d'abord la traduction française intégrale (p. 520-527), puis le texte grec original d'après Montfaucon (p. 527-532). | Amand publie d'abord la traduction française intégrale, puis le texte grec original d'après Montfaucon (l'ensemble p. 519-532). |
| `argument_regret_alex` | This is an early version of what Peter van Inwagen calls the "Consequence Argument" - if | It is only loosely analogous to what Peter van Inwagen calls the "Consequence Argument", which is a modal transfer argument: if |
| `argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus` | (Destrée 2014 ch. 11) | (Destrée 2014) |
| `argument_saving_teaching_alex` |  [Corrected 2026-06-14: prior 'Fat. 651-659' refs are non-existent — De Fato has 39 chapters / Bruns pp. 164-212.] |  (De Fato comprises 39 chapters, Bruns pp. 164-212.) |
| `argument_skeptical_argument_from_divine_power_d217cdac` | "Rorarius" (animal souls and human freedom) | "Rorarius" (animal souls, occasionalism and Leibniz — not the locus of the divine-omnipotence argument) |
| `argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will` | Argument scholarly de Wildberg (Destrée 2014 ch. 21) : | Argument scholarly attribué à Wildberg (Destrée 2014, chapitre non identifié) : |
| `collection_ls` | 57 (impulsion et oikeiôsis) et 65 (passions),  | *(removed)* |
| `concept_acting_final_cause` | Clement's innovation (modern interpretative label; the attribution formerly given here as 'Jourdan 2011' could not be traced to any publication and has been wit | Clement's innovation (a modern interpretative label, not a term of Clement's own, and as yet without an established secondary source): |
| `concept_autexousion_pe_vi_6_eusebius` | au même titre que la sensation : 'Elle est donc évidente | au même titre que la sensation. La citation n'est ici disponible qu'en traduction, le texte grec correspondant n'ayant pu être collationné : 'Elle est donc évid |
| `concept_carneadean_probabilism_amand1945` | Key concept identified by Amand (1945, p. 65, Intro §II ch. III §III) under the title | Key concept identified by Amand (1945, Introduction §II) under the title |
| `concept_causal_asymmetry_alex` | **Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de  | *(removed)* |
| `concept_causal_asymmetry_alex` | Alexander's doctrine that causal necessity operates asymmetrically across time: | The 'backward necessity / forward contingency' formulation is a modern formalization rather than Alexander's own terminology; on this reading, causal necessity  |
| `concept_eleutheron_kai_autexousion` | Repeated by Irenaeus (Dem. 11): ἐλεύθερον καὶ αὐτεξούσιον. | The same pairing is echoed by Irenaeus (Dem. 11), but the Greek given for that passage is a modern retroversion, not transmitted Greek text. |
| `concept_fate_principle_bobzien` | Formule technique introduite par Bobzien 2001 §1.4.4 (p. 56-58) pour designer | Formule technique introduite par Bobzien 2001 pour designer |
| `concept_fate_principle_bobzien` | une modification anti-stoicienne | une modification anti-stoicienne. |
| `concept_fortuna_boethius_j5k6l7m8` |  • "inconstantia mea" - Fortune's inconstancy (II.1.10) | *(removed)* |
| `concept_frede_inner_life_late_stoic` | (Diss. 1.29.1 : 'c'est ce qui te définit comme personne') | (Diss. 1.29.1, où l'essence du bien est identifiée à une certaine prohairesis ; 'c'est ce qui te définit comme personne' est une paraphrase plus large) |
| `concept_freiheitsmetaphysik_origenian` | (« Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit », Fürst p. 254) | (Fürst 2022) |
| `concept_freiheitsmetaphysik_origenian` | « gigantesque réseau de libertés s'interagissant constamment » (Fürst p. 292) | un gigantesque réseau de libertés en interaction constante (Fürst 2022) |
| `concept_gratia_operans` |  (Deus operatur in homine sine homine) | *(removed)* |
| `concept_inner_freedom_alex` | (no verbatim Greek formulation attested in the Epictetus, Dissertationes / Encheiridion (Stoic topos) — NOT Alexander, De Fato) | (no verbatim Greek formulation attested in Alexander's De Fato; the motif is a Stoic topos at home in Epictetus, Dissertationes / Encheiridion) |
| `concept_inner_freedom_alex` | anywhere in Alexander's Epictetus, Dissertationes / Encheiridion (Stoic topos) — NOT Alexander, De Fato (TLG0732 verified 2026-08-03). | anywhere in Alexander's De Fato (TLG0732 verified 2026-08-03). |
| `concept_non_necessitating_cause_alex` | Causation is broader than determination. | Causation is broader than determination. The Greek formula "αἴτιον οὐκ ἀναγκαστικόν" attached to this distinction is a modern scholarly reconstruction, not Alex |
| `concept_olympic_paradigm_positive_embodiment` | The view in ancient Greek religion that embodiment is natural and good, | The view in ancient Greek religion — 'Olympic paradigm' being a modern heuristic label, not an ancient technical term — that embodiment is natural and good, |
| `concept_orphic_zagreus_dionysus_myth` | Humans are born from the ashes of the Titans who had consumed Zagreus, explaining why humans have both divine (from Zagreus) and titanic (sinful) natures. | On a contested modern reconstruction, humans are born from the ashes of the Titans who had consumed Zagreus, which would explain why humans have both divine (fr |
| `concept_plurality_goods_alex` | (De Fato XV, Bruns 185.30-186.4: « | (De Fato XV, ed. Bruns: « |
| `concept_pneumatic_causation_stoic_bobzien` | reconstruit par Bobzien 2001 (Ch. 1 | reconstruit par Bobzien 1998 (Ch. 1 |
| `concept_providentia_stoic_seneca_b3c4d5e6` | "praeesse universis providentiam" (1.1) - providence presides over all | "praeesse universis providentiam" - providence presides over all |
| `concept_providentia_stoic_seneca_b3c4d5e6` | "interesse nobis deum" (1.1) - god is involved in our affairs | "interesse nobis deum" - god is involved in our affairs |
| `debate_stoic_academic_hellenistic` | [Wave 7 — résumé initial] La confrontation | La confrontation |
| `debate_stoic_academic_hellenistic` | [Enrichissement B2 — Amand 1945, p. 41-43 + p. 46-48, Intro §II ch. II] Amand caractérise | Amand (1945, p. 41-43 et p. 46-48, Intro §II ch. II) caractérise |
| `debate_stoic_academic_hellenistic` | (les 6 titres argumentatifs reconstruits en Conclusion = matière du batch B1) | (les 6 titres argumentatifs reconstruits dans la Conclusion d'Amand 1945) |
| `person_carneades_214_129bce_l2m3n4o5` | [Wave 7 — résumé initial] Carnéade de Cyrène | Carnéade de Cyrène |
| `person_carneades_214_129bce_l2m3n4o5` |  (Désaccord encodé via les arêtes disagrees_with / interprets reliant ce nœud aux nœuds Bobzien et Amand.) | *(removed)* |
| `person_carneades_214_129bce_l2m3n4o5` | [Enrichissement B2 — Amand 1945, p. 41-46, Intro §II ch. II §I-III] Amand insiste | Amand 1945, p. 41-46 (Introduction §II ch. II §I-III), insiste |
| `person_diogenes_babylon_240_152bce` |  Sources secondaires : David Sedley, « Diogenes of Babylon », in Algra/Barnes/Mansfeld/Schofield, Cambridge History of Hellenistic Philosophy (CUP 1999). | *(removed)* |
| `person_favorinus_of_arles_9n4o6q32` | [Wave 7 — note] Favorinus est avant tout | Favorinus est avant tout |
| `person_favorinus_of_arles_9n4o6q32` | [Enrichissement B3 — Amand 1945, p. 96-100, ll. 5919-6128] Selon Amand | Selon Amand (1945, p. 96-100, ll. 5919-6128) |
| `person_favorinus_of_arles_9n4o6q32` | (cf. argument dixième B3, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius) | (cf. le dixième argument, Aulu-Gelle XIV, 1, 23, p. 106 l. 31 — p. 107 l. 12 Hosius) |
| `person_hippolytus_rome_d235` | Sextus Empiricus Adv. Math. V, 50-105 (avec | Sextus Empiricus, Adv. Math. V (avec |
| `person_maximus_of_tyre_125_185ce` | et que la vie humaine est « amphibie » (ἀμφίβιος) — mélange de liberté et de nécessité. | et que la vie humaine est « amphibie », mélange de liberté et de nécessité — cette caractérisation étant moderne, le terme ἀμφίβιος n'étant pas attesté dans le  |
| `person_porphyry` | For the free will debate, Porphyry's most significant contribution is the treatise To Nemertius (Pros Nemertion), on the topic of human freedom, surviving only  | For the free will debate, a treatise To Nemertius (Pros Nemertion) on human freedom, said to survive only as seven fragments preserved and refuted by Cyril of A |
| `pub_belcastro_predestinazione_origene` | Monographie de Mauro Belcastro consacrée à | Article de Mauro Belcastro consacré à |
| `pub_pouderon_2000_athenagoras` | (Beauchesne 1989-rééd. 2000, *Théologie historique* 82, 368 p.) | (Beauchesne 1989, *Théologie historique* 82, 368 p. ; aucune réédition distincte de 2000 n'est attestée) |
| `pub_sytsma_2020_universal_salvation_origen` | Monograph (Gorgias Press, 2020) revising Sytsma's 2018 Marquette dissertation 'Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria'. | Sytsma's 2018 Marquette dissertation 'Reconciling Universal Salvation and Freedom of Choice in Origen of Alexandria' (no. 769), the only verifiable object behin |
| `scholar_jacobsen_a` | Patristicien danois (né 1962), professeur | Patristicien danois, professeur |
| `scholar_jacobsen_a` |  Directeur de Universal Salvation: The Current Debate (Cambridge University Press 2019). | *(removed)* |
| `scholar_perrone_l` | Patristicien italien (né 1948), professeur | Patristicien italien, professeur |
| `scholar_stump_e` | compatibilisme théologique, libre arbitre comme auto-détermination rationnelle compatible avec la grâce efficace augustino-thomiste. | Stump refuse expressément de ranger la lecture thomiste du libre arbitre sous le libertarisme standard comme sous le compatibilisme standard ; elle la qualifie  |
| `scholar_tomberlin_j` | ') that is malformed leftover text and should be cleaned; the substantive point it makes (ar] | *(removed)* |
| `scholar_wildberg_christian` | Auteur du ch. 21 du volume Destrée 2014, « | Auteur du chapitre « |
| `scholar_wildberg_christian` | what is up to us », étudiant | what is up to us » du volume Destrée 2014, étudiant |
| `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` | [Résumé initial — Wave 7]  | *(removed)* |
| `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` | [Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15] Thèse centrale | Thèse centrale |
| `scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4` | [Résumé initial — Wave 7] Reconstruction of Carneades' | Reconstruction of Carneades' |
| `scholarly_argument_amand_de_mendieta_reconstruction_of_carneades_ar_4` | [Enrichissement Conclusion-Épilogue — Patch B1 2026-05-15] Aveu philologique | Aveu philologique |
| `scholarly_argument_bonaiuti_ambrosiaster_s_influence_on_au_1` | and (4) the positive and realistic Scriptural interpretation method | and (4) the positive and realistic Scriptural interpretation method (Bonaiuti, Harvard Theological Review 10, 1917, p. 159–175, translated by Giorgio La Piana) |
| `scholarly_argument_bonaiuti_augustine_s_predestination_and_2` | 'der Paulus nach Paulus und der Luther vor Luther' | 'der Paulus nach Paulus und der Luther vor Luther' (Harvard Theological Review 10.2, April 1917, pp. 159-175) |
| `scholarly_argument_grant_eusebius_s_suppression_of_evid_3` | information about voluntary criticism | information about criticism |
| `scholarly_argument_narbonne_soul_s_descent_and_moral_respo_2` | 'partly undescended soul' (ἀμέθεξις) as | 'partly undescended soul' as |
| `scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1` | The edition presents Irenaeus's critique of Gnostic determinism as implying that Irenaeus himself affirms human moral responsibility and free choice; | Book I of the edition is heresiography, an exposition of the Valentinian and Marcosian systems, so reading it as a presentation of Irenaeus's own positive doctr |
| `scholarly_argument_still_paul_s_role_as_apologist_and_d_0` | ; the editorial framing suggests Pauline theology provided resources for defending Christian moral agency and voluntary faith against fatalistic and determinist | ; the editorial framing (Introduction and Afterword) concerns the categorisation of apologists and the reception of Paul |
| `scholarly_argument_telfer_christian_autexousia_and_jewis_2` |  (γένεα αὐτεξούσια) | *(removed)* |
| `scholarly_argument_tomberlin_divine_omniscience_and_counter_1` | divine omniscience and counterfactuals of freedom — If God is omniscient | divine omniscience and counterfactuals of freedom (James E. Tomberlin and Frank McGuinness, Religious Studies 13, 1977, pp. 455-475) — If God is omniscient |
| `scholarly_argument_tomberlin_free_will_defence_0` | does not exist | does not exist. The argument is advanced by James E. Tomberlin and Frank McGuinness, Religious Studies vol. 13 (1977), pp. 455-475 |
| `scholarly_argument_wolfson_laws_of_nature_and_divine_gove_0` | which is part of the pre-existent incorporeal Logos | which is part of the pre-existent incorporeal Logos (Wolfson, HTR 35 [1942], p. 131-169, at 131-132) |
| `scholarly_argument_wolfson_mind_body_relation_and_human_c_1` | creating an ongoing internal struggle | creating an ongoing internal struggle (Wolfson, Harvard Theological Review 35, 1942, p. 131-133) |
| `scholarly_work_barclay_2006_divine_and_human_agency_in_paul_and_his_` | Divine and Human Agency in Paul and His Cultural Environment | Divine and Human Agency in Paul and His Cultural Environment, co-edited by John M. G. Barclay and Simon J. Gathercole |
| `scholarly_work_breytenbach_2023_early_christianity_in_athens_attica_and_` | Early Christianity in Athens, Attica, and Adjacent Areas: From Paul to Justinian I (1st–6th cent. AD) | Early Christianity in Athens, Attica, and Adjacent Areas: From Paul to Justinian I (1st–6th cent. AD), by Cilliers Breytenbach and Elli Tzavella (Brill, 2023);  |
| `scholarly_work_hendriksen_0_new_testament_commentary_romans` | New Testament Commentary: Romans | New Testament Commentary: Romans (Grand Rapids: Baker Book House / Baker Academic). |
| `scholarly_work_martin_0_josephus_use_of_heimarmene_in_the_jewish` | XIII, 171-3 | XIII, 171-3. Article published in the journal Numen (Brill), vol. 28, fasc. 2 |
| `scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v` | peut-on choisir? | peut-on choisir? Article co-signé par Fabienne Pironet et Christine Tappolet. |
| `scholarly_work_pouderon_1998_les_apologistes_chr_tiens_et_la_culture_` | Les Apologistes chrétiens et la culture grecque | Les Apologistes chrétiens et la culture grecque, volume collectif co-édité par Bernard Pouderon et Joseph Doré. |
| `scholarly_work_pouderon_2003_aristide_apologie` | Aristide. Apologie | Aristide. Apologie — SC 470, édité par Bernard Pouderon et Marie-Joseph Pierre, avec B. Outtier et M. Guiorgadzé pour l'arménien et le géorgien |
| `scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th` | The Dead Sea Scrolls: The Truth Behind the Mystique | The Dead Sea Scrolls: The Truth Behind the Mystique — a Modern Scholar / Recorded Books audio lecture course with a printed course guide, not a conventional mon |
| `scholarly_work_schneider_2010_la_libert_dans_la_philosophie_de_proclus` | La liberté dans la philosophie de Proclus | La liberté dans la philosophie de Proclus — thèse de doctorat (Université de Neuchâtel, 2010). |
| `scholarly_work_tolan_2020_the_contemplation_of_the_transcendent_he` | from the Stoics to Origen | from the Stoics to Origen. Dissertation defended c. 2020 and deposited/dated 2021; '2021' is the more commonly cited year. |
| `synthesis_amand1945_basil_hex_vi_7_amand_origin_point` | Ce nœud constitue donc la racine génétique | Ce passage constitue la racine génétique |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` |  du batch B1) | ) |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` | voir nœuds B1 argument_carneadean_*_amand1945 | voir les nœuds argument_carneadean_*_amand1945 |
| `synthesis_amand1945_ch3_moral_argument_scheme_announcement` |  Annonce explicitement à ne PAS dupliquer avec B1 : ce nœud Ch. III est une porte d'entrée structurelle, B1 est le développement détaillé avec témoins. | *(removed)* |
| `synthesis_amand1945_gregory_nyssa_carneadean_role` | il accumule 23 arguments anti-astrologiques | il accumule une série d'arguments anti-astrologiques |
| `synthesis_amand1945_philo_attitude_astrology_signs_not_causes` | (λογικαὶ καὶ θεῖαι φύσεις, οὐκ ἄνευ σωμάτων ; De opif. 144 | (« natures intellectuelles et divines mais non incorporelles », formule d'Amand p. 88 ; De opif. 144 |
| `synthesis_destree2014_ch10_vimercati_panaetius` | (Némésius Nat. hom. 26 = Panaet. fr. B26 Vim.) | (Némésius, Nat. hom. = Panaet. fr. B26 Vim. ; numéro de chapitre non vérifié) |
| `synthesis_destree2014_ch10_vimercati_panaetius` | la liaison oikéiôsis–prohaïrèsis–responsabilité | la liaison oikéiôsis–prohaïrèsis–responsabilité. |
| `synthesis_destree2014_ch13_zingano_alexander_character_action` | Zingano se concentre sur les §§ 26-29 du De Fato d'Alexandre. | Zingano se concentre sur les chapitres du De Fato d'Alexandre où se regroupe le matériau sur le caractère et la responsabilité (chap. 26-34). |
| `synthesis_destree2014_ch15_maso_cicero_motus_animi_voluntarius` | employée dans quatre passages du De Fato (§§ 23, 25, 39, 48) et une seule fois ailleurs, en Tusculanes 4.79 — c'est en revanche la iunctura in nostra potestate  | employée dans plusieurs passages du De Fato et attestée également en Tusculanes 4.79 ; Maso met en regard la iunctura in nostra potestate, plus fréquente que la |
| `synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate` | (Bonazzi, p. 283-293) | (Bonazzi) |
| `synthesis_destree2014_ch22_frede_michael_eph_hemin_ancient_overview` | Synthèse du ch. 22 (M. Frede, p. 351-363) : article paru en 2007 dans une revue grecque, réimprimé avec permission et préparé pour l'édition par Susan Sauvé Mey | Synthèse du ch. 22 (M. Frede, p. 351-363). Thèses centrales |
| `synthesis_dihle1982_indian_excursus_intellectualism_parallel` | Cary 2007 a contre-argue | Phillip Cary (Augustine's Invention of the Inner Self, 2000) a contre-argue |
| `synthesis_dihle1982_lec1_cosmology_second_century` |  ('no separate will spontaneously interferes', md ll. 178-181) | *(removed)* |
| `synthesis_dihle1982_lec2_greek_intellectualism_action` | never developed a distinct concept of will' (p. 20). | never developed a distinct concept of will'. |
| `synthesis_dihle1982_lec3_stoic_assent_cognitive` | (asthenes synkatathesis, SVF 3.172, 3.548) | (asthenes synkatathesis) |
| `synthesis_frede2011_ch6_platonist_peripatetic_criticisms` | Alexandre 'is the only major ancient philosopher' dont la conception est fondamentalement viciée | Alexandre serait le seul philosophe antique majeur dont la conception soit fondamentalement viciée (paraphrase résumée, non citation littérale) |
| `synthesis_frede2011_ch6_platonist_peripatetic_criticisms` | critiquée par Ryle, Williams et Frede | critiquée par Ryle, Williams et Frede. |
| `synthesis_furst2022_carneades_will_innovation` |  Schallenberg qualifie Carnéade-Cicéron de « libertarischer Kompatibilismus » (parallèle miroir au « kompatibilistischer Libertarismus » que Fürst attribue à Or |  Fürst caractérise pour sa part la position d'Origène comme un « kompatibilistischer Libertarismus ». |
| `work_basil_homiliae_quod_deus_non_est_auctor_malorum` |  avec la formule centrale : τὸ ἐφ' ἡμῖν ἐστι τὸ αὐτεξούσιον (l'autonomie morale, voilà précisément le libre arbitre) |  où l'autonomie morale est présentée comme étant précisément le libre arbitre |
| `work_de_fato_cicero_44bce_b9c4e5d2` | [Enrichissement B3 — Amand 1945, p. 78-80, ll. 5131-5230] D'après Amand, le De Fato | D'après Amand 1945 (p. 78-80), le De Fato |
| `work_maximus_tyre_dissertation_13` |  = 19e (numérotation Dübner) | *(removed)* |
| `work_philo_de_opificio` | Editions: Cohn-Wendland vol. I (1896); Runia (Brill, 2001). | Editions: Cohn-Wendland vol. I (1896); Runia (Brill, 2001). The Greek terms cited above are consistent with Philo's vocabulary but have not been collated verbat |
| `work_philo_de_providentia` | Édition de référence : Cohn-Wendland, vol. VI (Berlin, 1915) pour les fragments grecs ; Aucher 1822 pour la version arménienne intégrale. | Édition de référence : Aucher 1822 pour la version arménienne intégrale ; le volume de l'édition Cohn-Wendland qui imprime les fragments grecs reste à préciser. |
| `work_philo_de_providentia` | [Enrichissement B3 — Amand 1945, p. 80-95, ll. 5232-5917] D'après Amand (suivant Wendland 1892 et Bousset 1915) | D'après Amand 1945, p. 80-95 (suivant Wendland 1892 et Bousset 1915) |
| `work_plutarch_de_communibus_notitiis` | Repugnantiis*, structuré en 50 chapitres. | Repugnantiis*, structuré en une cinquantaine de chapitres. |
| `work_salles_stoics_determinism_2008` | showing parallels and differences. | showing parallels and differences. The monograph appeared as Ashgate, 2005, in the series Ashgate New Critical Thinking in Philosophy. |
| `work_tertullian_adv_marcionem` |  CTS URN: stoa0275.stoa006. | *(removed)* |

### 5.5 Tag removed, prose unchanged — the flagged item is not in the description (100 nodes)

For these the plan's "remove/reword the flagged reference" is not actionable in the prose: the bad citation lives in a **metadata** field (`sources`, `page_range`, `doi`, `premises`, `scholarly_work_id`, `period`, a filename…), the tag is superseded by a later tag on the same node, or the correction was already carried by the prose from an earlier pass. The tag itself is preserved in `metadata.verification_notes`. **These are the metadata follow-ups** — nothing was lost, but the underlying field is still wrong.

| node | risk | why no prose change |
|---|---|---|
| `argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_augustine_deficient_cause` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_augustines_antipelagian_argument_grace_necessity_0b29401f` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_bobzien_2001_b1_cylinder_in_later_fate_theory` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_bobzien_2001_b1_philopator_late_compatibilism` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_bobzien_2001_b1_rise_fall_freedom_problem` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_boeri_2014_marcus_present_indifferents_eph_hemin` | medium | Tag #7 flagged '(Destrée 2014 ch. 12)' as unverified, but tag #8 (same date) explicitly supersedes it: 'the chapter number and all three steps are now confirmed against the volume itself'. No prose change made; removing the citation would delete information the later tag certifies. |
| `argument_boethius_foreknowledge_problem` | medium | Tag flags the locus 'Consolation V.pr.11-12' as non-existent, but that string does not occur in the description (which cites only V.pr.3 and V.pr.6, both compatible with the tag's 'solution is entirely within V.pr.4-6'). The bad locus must live in another field (e.g. metadata/premises) — nothing to  |
| `argument_cafma_framework_5a7b9e12` | medium | Curator first-person log lives in metadata, not in the description; the description already carries Amand 1945, pp. 581-584 as a normal provenance citation, so no prose change is needed. The metadata field still needs the first-person narration stripped. |
| `argument_cafma_futility_of_sanctions_0e5f7h43` | medium | Tag rejects 'Aulus Gellius NA VII.2' as a witness, but that citation appears nowhere in the description prose (it lives in metadata/key_passages), so there is no prose target to remove. |
| `argument_chance_cosmos_middle_platonist` | medium | Tag #16's concern about the De fato 569A 'Great Year' quotation is superseded by tag #17 ('Resolved'); the prose already carries the resolution (the quotation is presented as Boys-Stones' gloss, and the treatise's own terms are given as ἡ ὅλη περίοδος / ὁ σύμπας χρόνος, not μέγας ἐνιαυτός). No prose |
| `argument_deliberation_complete_alex` | medium | flags_spurious_reference targets the node's metadata 'sources' array (passage_alex_fat_554..558); the description itself already cites De Fato 11-12 (Bruns 178-180), which the tag confirms as the correct grounding. No prose change possible or needed. |
| `argument_divine_hardening_problem_y9z0a1b2` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_epicurean_swerve_for_freedom_m4n5o6p7` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_future_contingents_alex` | medium | The spurious reference '471-480' does not occur in the description prose (which cites only Bruns 200-201, De Fato 30, De Fato 10 and De Int. 9); it lives in metadata, so no prose edit is possible. |
| `argument_homonymy_alex` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_justin_angel_fall` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_justin_antifatalism` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_justin_prophecy_freedom` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_reactive_attitudes_alex` | medium | Tag flags 'Marmodoro & Bobzien 2015' as an unconfirmable joint publication, but the tag itself locates it 'in the scholarly_consensus text' — the string does not occur in the description, which cites only 'Alexander, De Fato chs. 16, 26, 35 (Bruns, Suppl. Arist. II.2)'. Fix belongs to the scholarly_ |
| `argument_sea_battle_aristotle_f6g7h8i9` | medium | The flagged reference (bobzien_2001_chapter, 'Ch. 2 Two Chrysippean Arguments for Causal Determinism') does not occur in the description — it lives in the node's metadata. No prose edit possible. |
| `argument_tertullians_antimarcionite_argument_for_free_will_f49cad73` | medium | Tag flags premises P1-P4 (incl. 'the devil emulates truth to shake it') as coming from a different work, but those premises live in metadata, not in the description; the tag is truncated before naming the true source, so no prose edit is recoverable. |
| `argument_wager_alex` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `argument_zeno_paradox_analogy_alex` | medium | Tag #0 is truncated mid-sentence after restating the node's own general move (trusting ἐνάργεια over a σόφισμα, 'saving the phenomena'); no correction is recoverable from it, and the quoted De Fato XXVI, Bruns 196.19-21 lies inside the treatise's real Bruns range. No prose change made. Tag #1 is con |
| `argument_zingano_2014_alexander_liability_vs_possibility` | medium | Both tags are in substance confirmations (tag #0 reads as a plausibility check on Zingano's chapter and the liability/possibility distinction, truncated; tag #1 states chapter, §§26-29 and the distinction are now confirmed). Nothing in the prose is flagged as spurious, so no prose change. |
| `concept_academic_skepticism_epoche_n4o5p6q7` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_ananke_necessity_democritus_h8i9j0k1` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_arche_alex` | medium | The flagged loci ('Fat. 233/235/246/247/253/254') do not occur in the description; the only De Fato page-reference in the prose is 'Fat. 180', which the tag confirms as valid. The out-of-range references are in metadata. |
| `concept_autexousion_methodian_doctrine_141258ec` | medium | The flagged framing ('neither an accident συμβεβηκός nor a quality ποιότης but constitutive of οὐσία') is no longer in the prose: the description already states that Methodius applies the οὐσία/συμβεβηκός distinction to evil rather than to free will, with a sourced quotation. Nothing left to correct |
| `concept_causal_conception_eph_hemin_salles` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_chrysippean_compatibilism_bobzien` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_common_cause_alex` | medium | The correction is already carried by the prose: the opening sentence states that 'common cause' is a modern label and that neither κοινὴ αἰτία nor ἀρχὴ πολλῶν occurs in Alexander, and the sun-on-ecliptic and prohairesis material is now quoted verbatim from De fato, Bruns 194-195. No prose edit neede |
| `concept_cyclical_return_great_year` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_death_therapeutic_remedy_methodius_5eaaf3a2` | medium | Tag targets metadata ('ambiguous: 4 works' work link, and the Greek term for 'remedy' stored there); the description already states the correct locus, Methodius De resurrectione I, so no prose change applies. |
| `concept_eph_hemin_two_sided_potestative` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_evil_quality_accident_methodius_dae1b112` | medium | The extracted spurious_ref "αὐτεξούσιον, contre le dualisme valentinien d'" is a parsing artefact: the extractor took the text between two French apostrophes (l'…d'une) inside the tag. The tag in fact CONFIRMS that core ('solidement méthodien') and denies only the Aristotelian category-vocabulary —  |
| `concept_exercitatio_adversity_seneca_c4d5e6f7` | medium | Tag #1 explicitly retracts tag #0 ('Audit note is wrong... the quotation IS verbatim'), so the 'Omnia adversa exercitationes putat' (2.2) quotation stands unchanged. |
| `concept_exousia_alex` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_external_principle_action` | medium | Tag is a caveat on the node's period field ('Classical Greek' vs Roman Imperial): the prose already attributes the quoted Greek to Alexander's De Fato (Fat. 4) and labels the concept Peripatetic, so no prose change. The period metadata should be reviewed separately. |
| `concept_for_most_part_alex` | medium | The flagged citations ('Fat. 523', 'Fat. 551-552') do not occur in the description, which cites only De Fato VI (Bruns 170.1-19) and XXIV (Bruns 194.20-22). The bad references are in the node's passage ids / metadata. |
| `concept_gratia_cooperans` | medium | Tag reports a truncated `coinage_note` field ('Keep \'gratia cooperans\' as the re'); it is a data-quality defect in that separate field, not in the description, which the tag itself calls free of scholarly error. |
| `concept_hekousion_voluntary_aristotle_a1b2c3d4` | medium | tag asks the Alexander claim to stay hedged as a modern label; the prose already reads 'what modern scholars term libertarian freedom' — no prose change needed |
| `concept_intellectualism_medieval_i3j4k5l6` | medium | Tag is an explicit 'not an error' terminological note about the latin_term 'intellectualismus', a metadata field; the string does not occur in the description prose, so no prose edit is possible. |
| `concept_kompatibilistischer_libertarismus_origenian` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_libertas_spontaneitatis_5g9b0c68` | medium | Tag disputes an attribution of the term to Kant, KpV Ak. V:96; the description never mentions Kant (the claim is in metadata), so no prose edit applies. |
| `concept_matter_adaptability_pneumatic_receptivity` | medium | Tag #155 ('no primary-text locus … source flagged as unclear') is superseded by tag #156 ('Resolved'); the current description already supplies the loci (Adv. haer. V,3,2-3 and IV,38-39) and contains no 'unclear' wording. No prose change needed. |
| `concept_mr2_ability_responsibility` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_peccatum_originans` | medium | Tag is explicitly 'Terminological note (not an error)' about the node label 'peccatum originans'; the term does not occur in the description prose, and the tag is truncated at 'Here it is', so no prose edit was made. |
| `concept_pelagianism` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_philopator_compatibilism_bobzien` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_platonic_vs_christian_original_sin` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_practical_life_alex` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_providentia_fatum_boethius_h3i4j5k6` | medium | The second tag explicitly supersedes the first: both Latin sentences are confirmed verbatim and both attributions (IV pr.6, V pr.1) are correct, so nothing in the prose is spurious and no edit is warranted despite the plan's 'remove the flagged reference' line. |
| `concept_saving_teaching_alex` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_self_happiness_alex` | medium | All three tags flag the phrase 'δι᾽ αὑτῶν εὐδαιμονεῖν' as unattested. The description already states exactly that (not attested anywhere in Alexander, negative TLG search, εὐδαιμονεῖν absent from the De Fato) and supplies the real textual basis (De Fato XXIX plus the ethical corpus). The phrase is n |
| `concept_stoic_causal_principle` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `concept_synkatathesis_logike_alex` | medium | The flagged references 'Fat. 230-231' / 'Fat. 257' are in the node's key_passages metadata, not in the description: the only locus given in the prose is De anima libri mantissa, 184.11 Bruns, which the tag does not question. |
| `concept_two_sidedness_eph_hemin` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `debate_source_of_action_90c57974` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `person_ekstrom_laura_1u2v3w4x` | medium | Tag concerns the unverifiable birth-year field 'fl. late 20th-21st c.' stored in metadata; the description contains no date claim, so no prose edit applies. |
| `person_ginet_carl_0t1u2v3w` | medium | The unverified '2017 CE' is the node's `death_date` field, not prose: the description contains no dates at all. The field should be cleared (Ginet b. 1932, Cornell emeritus, per the tag), which a description edit cannot do. |
| `pub_amand_1945_fatalisme` | medium | The correction concerns the node's ISBN field (9789025606466 belongs to the 1973 Hakkert reprint, not the 1945 Louvain original); no ISBN appears in the description prose, so no prose edit is possible. |
| `sc79_chrysostomus_de_providentia` | medium | The mismatch flagged by the tag (SC number 79, the Malingrey edition, the ingested text) is between the node id / metadata and the content; the description itself consistently cites PG 50, 749-774 and Amand 1945, which the tag endorses. Nothing in the prose to remove. Tag truncated at 'the inge'. |
| `scholar_destr_e_p` | medium | The unconfirmed chapter page range 'p. 25-38' does not occur in the description (it is in the node's bibliographic metadata); the second tag is a plain 'resolved, remove the note'. No prose change. |
| `scholar_djeranian_o` | medium | Tag #288 explicitly supersedes tag #287 ('both items are now confirmed'), so the book title, its 2023 date and the article title stand; no prose change. |
| `scholar_fee_g` | medium | The flagged values are page_range metadata (markdown extraction line numbers from Fee_1994.md); the description prose is only 'New Testament, Pauline pneumatology' and contains no reference to remove - editing it would empty the description. |
| `scholar_position_frede_will_originates_epictetus` | medium | Tag states explicitly that it is a characterization caveat and 'not an error requiring change'; it is also truncated before completing Frede's nuance (emergence within the Stoic tradition, Epictetus as clearest exponent), so that nuance is lost with the tag. |
| `scholarly_argument_bird_paul_s_view_of_salvation_and_d_0` | medium | The flagged 'Introduction' is the node's `page_range` field, not the description — the tag says the cited substance actually comes from Schreiner's own essay, and the description already attributes it to 'Schreiner's Reformed reading'. Fix belongs to page_range. |
| `scholarly_argument_bobzien_justin_martyr_on_fate_9` | medium | The flagged '6801-6802' is a page_range metadata value (a character-offset marker), not present in the description prose; no prose assertion to remove. |
| `scholarly_argument_bobzien_middle_platonist_synthesis_4` | medium | The impossible range '905-922' is a character-offset marker stored in the node's page_range metadata; it does not occur in the description prose, so no prose edit applies. Metadata should be reset to the article's real span 133-175. |
| `scholarly_argument_bobzien_origin_of_the_free_will_proble_0` | medium | the offending markers ('[Bobzien - 1998:22-31]' etc., character offsets mistaken for pages; article = Phronesis 43.2:133-175) are absent from the description — they live in the source-summary/citation metadata |
| `scholarly_argument_bonaiuti_augustine_s_doctrine_of_origin_0` | medium | The correction (HTR 10, 1917, 159–175, not 1924) concerns the linked scholarly_work node's date; the description prose contains no publication year, so there is nothing to rewrite. |
| `scholarly_argument_bonaiuti_manichaean_influence_on_august_3` | medium | The correction (linked work misdated 1924; the HTR article is 1917, vol. 10, pp. 159-175) concerns the linked scholarly_work record; no date appears in the description prose, so no prose edit is possible. |
| `scholarly_argument_dihle_greek_philosophical_theology_a_0` | medium | The flagged reference 'Cleanthes ap. Seneca Epistulae 41.1' does not occur anywhere in the description — it lives in the node's metadata/sources. No prose edit is possible; the metadata pairing remains to be fixed. |
| `scholarly_argument_fee_absence_of_libertarian_free_wi_2` | medium | The flagged values '681-687, 912-915, 15682-15694' are page_range metadata (markdown line numbers), not present in the description prose; the '992-page study' claim is not challenged by the tag. |
| `scholarly_argument_hick_free_will_and_moral_evil_0` | medium | The tag targets an 'engagement' entry naming Alvin Plantinga (absent from the cited 1966 text, and anachronistic for it); Plantinga is not mentioned anywhere in the description, which only refers to Hick's critique of the Augustinian free-will defense. Fix belongs to the engagement/relations field. |
| `scholarly_argument_jourdan_determinism_and_fate_vs_free_w_2` | medium | The two malformed Clement citations ('Stromates I 2,19.94,1-7' and 'Stromates I 3,26.1-27.3') are not in the description prose; they live in the node's citation metadata. |
| `scholarly_argument_linjamaa_cosmos_as_school_and_community_4` | medium | The five fabricated TriTrac loci ('140:32-144:16' etc., all beyond the tractate's extent of 138:27) do not occur in the description; they are in the node's metadata. No prose edit possible. |
| `scholarly_argument_linjamaa_social_and_political_involveme_5` | medium | The four impossible TriTrac codex citations ('160:37-164:41' etc.) do not occur in the description prose; they sit in metadata key_passages, so no prose edit is possible. |
| `scholarly_argument_list_epistemological_foundation_of__2` | medium | '429-431' is a page_range metadata value (extraction line numbers), not a reference in the prose; the description contains no page citation to remove. |
| `scholarly_argument_list_justin_martyr_s_anti_heresiolo_1` | medium | Tag concerns page figures '480-481, 785-787, 952-954' stored in metadata (they are extraction line-numbers, not journal pages); the description carries no page reference, so no prose edit applies. |
| `scholarly_argument_minns_free_will_in_justin_martyr_0` | medium | Tag #0's correction is already incorporated: the description explicitly says 'but their explanatory notes do take substantive positions', i.e. the claim the tag objects to ('do not take a substantive position') is no longer present. Tag #1 confirms the audit note is superseded. |
| `scholarly_argument_prigent_determinism_and_predestination_1` | medium | the malformed range 'Barnabas 4.9-5' does not appear in the description (which says only 'chapter 4'); it lives in the citation metadata |
| `scholarly_argument_telfer_free_will_and_determinism_in_e_0` | medium | Tag concerns a misfiled Hoskyns / 'three days' citation in metadata.engages_with_scholars; the description does not mention it, so no prose edit applies. |
| `scholarly_argument_wolfson_rational_vs_irrational_soul_an_2` | medium | The correction (year 1942, HTR 35: 131-169, not 1947) concerns the linked work's date and page metadata; the description prose contains no date or page reference. |
| `scholarly_work_dettwiler_2008_l_p_tre_aux_eph_siens` | medium | Tag is a pure metadata mislabel (a UNIGE handle stored in the 'doi' field); the description is only the title, and deleting or altering it is not warranted. |
| `scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens` | medium | The correction is purely a metadata mislabel (the 'doi' field holds the UNIGE handle unige:39486); the description is the bare title and needs no prose change. |
| `scholarly_work_munier_1994_l_apologie_de_saint_justin_philosophe_et` | medium | The second tag withdraws the suspicion: 'L. Antipas' is what Munier's own bibliography prints. The description is only the book title and contains nothing flagged, so no edit. |
| `scholarly_work_o_keefe_2005_epicurus_on_freedom` | medium | correction is a DOI fix (10.1017/CBO9780511482571, eISBN 9780511482571; the earlier …182525 was wrong) belonging to metadata; the description is the bare title and has nothing to merge |
| `scholarly_work_sharples_2003_threefold_providence_the_history_and_bac` | medium | The correction is purely a metadata mislabel (the 'doi' field holds a JSTOR stable URL); the description is the bare title and needs no prose change. |
| `scholarly_work_velardo_2013_notas_teol_gicas_de_bellum_judaicum` | medium | The fabricated DOI 10.2307/25930006008 (in fact a redalyc.org article id) is a metadata field, not part of the description prose; it must be cleared outside the description. |
| `scholarly_work_zetterholm_2004_a_feminist_paul_a_hermeneutical_experime` | medium | The missing question mark is in the node id/label/verified_reference; the description already reads 'A feminist Paul?' with the interrogative, so no prose edit applies. |
| `synthesis_amand1945_plato_partial_anti_fatalism` | medium | The flagged 'Introduction §I (Platon), p. 20-40' is the metadata section label; the description gives its own, different label ('Intro §II ch. I §II, p. 31-33'), and the tag says both correctly place the treatment. Nothing to remove from the prose — the metadata label is what should be reconciled. |
| `synthesis_bobzien2001_ch6_chrysippean_compatibilism` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `synthesis_bobzien2001_ch8_philopator_late_stoic` | low | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `synthesis_cic_fat_in_nostra_potestate` | medium | (tag class `confirms_ok` / boilerplate only — nothing to merge) |
| `work_alexander_quaestiones` | medium | The flagged list 'I.4, I.22, and II.21' is the node's key_passages metadata and is not what the prose asserts: the description already cites I.4, I.14, II.4 and II.21 with their SVF identifications. No prose edit needed. |
| `work_consolatio_philosophiae_boethius_524ce_f1g2h3i4` | medium | The spurious edition {editor: Green, 2010, Oxford/Clarendon} is recorded in the node's metadata, not in the description — 'Green' does not occur in the prose, so no description edit is possible. |
| `work_gellius_na_vii_2` | medium | Tag #1 explicitly supersedes tag #0: both Latin quotations are now collated and confirmed verbatim against the OCT. No prose change is warranted despite the PLAN_ACTION's default wording. |
| `work_gregory_de_anima_resurrectione` | medium | The doubtful edition entry 'Maraval, SC 614 (Cerf 2022)' does not occur in the description (it is in the node's editions metadata); the French translation cited in the prose is Terrieux, Cerf 1995, which the tag does not question. |
## 6. Escalations and follow-ups — NOT done here

### 6.1 Escalated, node left byte-identical

- **`passage_alcin_alcinous_untitled_full_text`** — labelled *Alcinous, Handbook of Platonism (Didaskalikos), Didasc. 1* and edged to `person_alcinous_2c_ce` / `work_didaskalikos_alcinous_2nd_ce_q7r8s9t0`, but its 8 218-char payload is Eusebius / Hegesippus on James the Just (HE II.23). Label, edges and content all disagree. This is a corpus-integrity problem, not a curation artifact; it needs its own verification pass. Listed in `SKIP_NODES` in the apply script so a re-run keeps skipping it.

### 6.2 Metadata-level defects the tags report — description cleaned, field still wrong

This cleanup deliberately stayed inside the reader-facing fields (`description`, `label`, `metadata.description_en`). 100 nodes (§5.5) got no prose edit because the flagged item is in metadata. On top of those, 16 tags name a metadata defect explicitly:

| node | metadata defect named by the tag |
|---|---|
| `argument_human_dignity_alex` | `metadata.sources` still lists the fabricated passage ids `passage_alex_fat_628/629/633-636` that the description already declares removed |
| `concept_carneadean_probabilism_amand1945` | `metadata.amand_location` ("Introduction §II Ch. II, p. 41-58") contradicts the description locus |
| `concept_death_therapeutic_remedy_methodius_5eaaf3a2` | `metadata` flags "ambiguous: 4 works"; the Greek term φάρμακον is presented there without a locus |
| `concept_non_necessitating_cause_alex` | the label presents «αἴτιον οὐκ ἀναγκαστικόν» as Alexander's own term; `bruns_pages` "211-212" is the peroration, and "459-462" matches no Alexander citation system |
| `sc379_athenagoras_legatio` | `metadata` records 38 chapters; the Legatio has 37 (the field looks like a count of `page_index` entries, so verify before editing) |
| `scholar_harl_m` | `key_works` SC 7bis element — **fixed** (the one metadata change applied, see §7) |
| `scholar_jacobsen_a` | `metadata.birth_date` 1963 vs prose "né 1962"; an edited volume ("Universal Salvation: The Current Debate", CUP 2019) that could not be found |
| `scholar_wildberg_christian` | `metadata.description_en` says ch. 18 where the French said ch. 21 (the French chapter number was dropped; the English one was not touched) |
| `scholarly_argument_crouzel_manuscript_tradition_and_textu_1` | `metadata.scholar_id` still `scholar_crouzel_henri`; the section is Simonetti's and the KG has no Simonetti node to point at |
| `scholarly_work_dettwiler_2008_l_p_tre_aux_eph_siens` | `doi` holds a UNIGE repository handle (unige:39485), not a DOI |
| `scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens` | `doi` holds unige:39486, not a DOI |
| `synthesis_amand1945_origen_pivot_witness` | the same spurious 7th witness is in the English metadata |
| `synthesis_amand1945_plato_partial_anti_fatalism` | `metadata` section label ("Introduction §I (Platon), p. 20-40") vs description ("Intro §II ch. I §II, p. 31-33") |
| `work_alexander_quaestiones` | the quaestiones cited as treating fate/responsibility ("I.4, I.22, II.21") could not be confirmed |
| `work_salles_stoics_determinism_2008` | metadata omits year/publisher; the monograph is Ashgate 2005, not 2008 (the node id itself carries `_2008`) |
| `work_tertullian_adv_marcionem` | `metadata.canonical_id` `urn:cts:latinLit:stoa0275.stoa015` contradicted the description's `stoa0275.stoa006`; the URN was removed from the prose, the metadata one is untouched and unadjudicated |

Also: **`argument_cafma_framework_5a7b9e12`** — the only planned node whose description needed no change at all. Its curator artifact is a first-person log in `metadata.attribution_review` ("This node carried no [Vérif.] note but was flagged uncertain. I located Amand's actual reconstruction…"). Metadata is allowed to contain such text under the agreed policy, so it was left; flag it if the field is ever surfaced to readers.

### 6.3 Label-level residue

- **`argument_lazy_argument_alex`** — the tag rejects the conflation of Alexander's consequences-for-motivation argument with the ἀργὸς λόγος, but the label still reads "Lazy Argument (Argos Logos) in Alexander". Renaming it is an interpretive call, so it was left. Two other labels flagged by tags **were** fixed (§7).

### 6.4 Greek gate

See §2 — two pre-existing TLG-attested runs need `data/audit/greek_allowlist.json` entries, and `scripts/tlg_search.py` needs its scrubbed `TLGE` default restored (or `TLGE_DIR` exported). Neither file is a target of this cleanup, so neither was touched.

### 6.5 Curator brackets outside this plan's scope

A whole-graph scan after the run finds **8 nodes** still carrying curator brackets of other shapes (`[Vérifié 2026-08-02 : …]`, `[Correction 2026-08-02 : …]`, `[Précision philologique …]`, `[Greek removed: …]`, `[Bruns page references … removed as fabricated]`, `[The node previously embedded …]`). None is in the plan's 284 lines, so none was touched — they warrant a second sweep on the same pattern.

### 6.6 Corrections that could not be completed — truncated tags (44 nodes)

Many stored `[Vérif.]` tags are truncated at ~200 characters mid-sentence, so the correction they carry is only partly recoverable. In every case below the **conservative minimal edit** was made — the incorrect assertion was removed or hedged rather than replaced by a guess — and the full tag is preserved in `metadata.verification_notes` for a later pass with the sources in hand. **No ancient text was reconstructed to fill a gap.**

| node | what could not be recovered |
|---|---|
| `argument_adversity_exercise_seneca_g8h9i0j1` | Tag truncated after 'Edition numbering varies by a subsection, so'; only the 2.3->2.4 relocation could be applied. The node's passage anchor (passage_sen_prov_2_3) is metadata and still needs re-pointing. |
| `argument_bardesanes_nomima_barbarika_amplified` | Verbatim wording and exact page of Amand's judgement are lost; only the paraphrased attribution survives. |
| `argument_clement_grace_synergy_assent` | Tag truncated before naming the alternative section, so the precise locus is lost; only 'Strom. II' is retained. The parallel locus Strom. V.13.86 was not flagged and is kept. |
| `argument_gomez_2014_chrysippus_reactive_compatibilism` | Contributor name and page range removed as unconfirmed; the tag is truncated after naming Gourinat as a verified contributor, so the correct attribution could not be recovered. |
| `argument_lazy_argument_alex` | Page anchors lost: the tag says the given Bruns pages are impossible but does not supply the correct ones. The node label ('Lazy Argument (Argos Logos) in Alexander') still carries the conflation flagged by the tag. |
| `argument_origen_argos_logos` | Tag truncated mid-word ('the same presci'); the corrected characterization was recoverable, but the tag's further point about where the argos logos refutation proper is located was lost. The French header still lists Contra Celsum II.20 as source primaire and was left untouched. |
| `argument_plutarch_providence_cooperation_8c5a9d3f` | Tag truncated at 'De Sera Numinis Vindicta and De St'; whatever it stated about those authentic works could not be recovered and is not reflected. |
| `argument_pseudo_chrysostom_de_fato_v_witness6_amand1945` | The sub-page spans for the French translation and the Greek text are lost; only the overall span p. 519-532 (already in the prose) is retained. |
| `argument_skeptical_argument_from_divine_power_d217cdac` | Tag's main object is the grounding of every premise to work_bayle_rorarius_1702 (metadata); in the prose the only fix available was to stop presenting 'Rorarius' as the locus of the argument. Tag is truncated, so the correct locus could not be substituted. |
| `argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will` | The tag also doubts whether Wildberg authored a chapter in Destrée-Salles-Zingano 2014 at all; the attribution is only hedged ('attribué à'), not removed, since the tag is truncated and does not settle it. |
| `collection_ls` | Both doubtful section numbers removed rather than corrected: the tag is truncated before giving the right LS numbers. |
| `concept_carneadean_probabilism_amand1945` | precise chapter/page dropped: description said 'p. 65, Intro §II ch. III §III', metadata.amand_location says 'Introduction §II Ch. II, p. 41-58'; the tag is truncated before resolving which is correct |
| `concept_fortuna_boethius_j5k6l7m8` | Tag is truncated mid-sentence, so no corrected phrase or locus was recoverable; the whole unverified bullet was dropped rather than kept with a wrong locus. |
| `concept_frede_inner_life_late_stoic` | Tag truncated at 'Chapter numbers' - any correction to the Frede chapter/page loci (Ch. 5 §1 p. 75-79, Ch. 3 p. 44-48, Ch. 9 p. 158-159) is not recoverable and was left as is. |
| `concept_gnomic_will_gnome` | The tag is truncated at 'The co…', so whether the figure '28' is itself correct could not be recovered; the count was dropped rather than moved to the new locus. |
| `concept_gratia_operans` | The other flagged item, the Greek back-translation χάρις ἐνεργοῦσα, does not occur in the description (it is stored elsewhere in the node) and so could not be removed here. |
| `concept_orphic_zagreus_dionysus_myth` | Tag is an interpretive caveat (class=other) and is truncated after 'Olympiodorus (6th c'; the prose was hedged and attributed rather than deleted. |
| `concept_providentia_stoic_seneca_b3c4d5e6` | tag truncated: it flags the two phrases as wrongly attributed to 1.1 but does not give their correct locus, so the locus was removed rather than corrected |
| `person_cyrus_alexandria_d641` | Tag truncated at "he did not survive to be 'dé'"; what he did not survive to do could not be recovered, so the incorrect post-conquest dismissal was dropped rather than replaced. |
| `person_diogenes_babylon_240_152bce` | Tag truncated at 'The CHHP treats' - the correct CHHP locus for Diogenes is not recoverable, so the secondary-literature reference was deleted outright rather than repaired. |
| `person_hippolytus_rome_d235` | Precision lost: the tag says the two ranges must be reconciled but does not say which is right, so only the book number is kept. |
| `person_porphyry` | Tag is truncated; the fragment-based paragraph and the 'Boulnois (2000)' edition line were kept but the attribution is now marked as unconfirmed rather than asserted. |
| `pub_belcastro_predestinazione_origene` | Tag truncated: only the genre error could be recovered; the remainder of the objection (about the loci claimed across De Principiis III.1, Comm. Rom. and Philocalia 21-27) is lost. |
| `scholar_list_n` | The tag is truncated before naming the other scholar, so the node label 'Nicholas List' could not be verified or corrected; the description now states the conflation explicitly rather than silently attaching patristic research fields to a philosopher of mind. The node probably needs splitting into t |
| `scholar_stump_e` | Tag truncated at 'an intellectualist account without '; the missing qualifier could not be recovered, so the prose says only 'conception intellectualiste'. |
| `scholar_tomberlin_j` | The residual text removed here is the tail of a nested/truncated audit note that falls OUTSIDE the tag as delimited in TAGS PRESENT (which closes at 'the argument t]'), so tag-stripping alone would leave it standing; the substantive point it was making is itself truncated ('the substantive point it  |
| `scholar_wildberg_christian` | The chapter number is lost: the tag records the contradiction (ch. 21 vs ch. 18) without resolving it, so neither number could be asserted. |
| `scholarly_argument_bonaiuti_ambrosiaster_s_influence_on_au_1` | Tag truncated at 'The page range'; the wrong year (1924) is encoded in the linked work id and still needs fixing in metadata. |
| `scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1` | Tag truncated at 'the Valentinian/Marcosian systems'; the claim was qualified rather than deleted, per the tag's 'slightly overreaches'. |
| `scholarly_argument_telfer_christian_autexousia_and_jewis_2` | The attested form is undeterminable from the truncated tag (the prose had γένεα, the tag records γένη on both sides of the arrow); the Greek parenthesis was deleted rather than reconstructed, per the zero-fabrication rule. |
| `scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3` | The Timaeus loci correction (node's '69C-72D' vs Wolfson's 'Tim. 42E ff.; 69C') applies to metadata loci absent from the description, and the tag is truncated on the second locus; the linked work node dated 1947 still needs re-pointing to the 1942 article. |
| `scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v` | The co-author is now named in the prose, but author_id scholar_pironet_f still needs a second author entry in metadata. Tag truncated at 'Not an attribution error pe'. |
| `scholarly_work_pouderon_2003_aristide_apologie` | Tag truncated at 'The page_range v'; whatever page-range problem it reported could not be recovered and is not addressed. |
| `scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th` | Tag truncated at 'Author (Schif' - any correction to the author record could not be recovered. |
| `synthesis_amand1945_cicero_ch2i_cadre` | The tag announces two soft points but is truncated after the first; point (2) is unrecoverable and no edit was made for it. |
| `synthesis_amand1945_origen_pivot_witness` | The tag names only part of Amand's six textes témoins (Cicéron, Philon, Favorinus ap. Gellius XIV.1, pseudo-Pl…) before truncating, so the spurious 7th list item could not be identified; the erroneous count was removed instead of a witness. |
| `synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate` | Page locus removed entirely: the tag says it is unreliable but is truncated before giving a correct range. |
| `synthesis_frede2011_ch6_platonist_peripatetic_criticisms` | the tag is truncated before giving Frede's actual sentence, so the claim is paraphrased rather than re-quoted; the second quoted fragment ('in Alexander that we find the ancestor of the notion') was not flagged and is left as is |
| `synthesis_furst2022_carneades_will_innovation` | The Schallenberg attribution was removed entirely (tag: phrase absent from Fürst 2022); the mirror-parallel framing is lost with it. |
| `work_augustine_retractationes` | Tag truncated after 'De correptione et gratia,' - the full list of excluded anti-Pelagian treatises could not be reproduced; the Retract. II.66(92) locus given for the removed item was dropped as unverified. |
| `work_exodus_c9d0e1f2` | The node's period field still reads 'Second Temple Judaism' and needs changing separately; the tag is truncated before naming the replacement period. |
| `work_maximus_tyre_dissertation_13` | The node LABEL still carries '/ 19 (Dübner)'; only the description was in scope. Tag truncated at 'The Hobein ', so no replacement concordance was available. |
| `work_methodius_de_libero_arbitrio` | Tag truncated before naming De autexusio's actual adversaries, so the removed character could not be replaced by the correct one. |
| `work_philo_de_providentia` | The correct Cohn–Wendland volume for the Greek fragments is not recoverable from the truncated tag, so the reference was hedged rather than corrected; the Eusebius fragments (Praep. ev. VII, 21; VIII, 14) already in the prose remain the only concrete Greek witnesses cited. |

## 7. Changes made outside `description`

| field | node | before → after |
|---|---|---|
| `label` | `synthesis_amand1945_ch3_moral_argument_scheme_announcement` | `… reconstruit en Conclusion = B1)` → `… reconstruit en Conclusion)` |
| `label` | `concept_pneumatic_causation_stoic_bobzien` | `… (reconstruction Bobzien 2001)` → `… (reconstruction Bobzien 1998)` |
| `label` | `work_maximus_tyre_dissertation_13` | `Dissertation 13 (Hobein) / 19 (Dübner) — …` → `Dissertation 13 (Hobein) — …` |
| `metadata.key_works` | `scholar_harl_m` | removed `Origène, Homélies sur la Genèse — SC 7bis (Cerf 1976, avec Doutreleau)` (tag: "Harl is not a co-editor of SC 7bis … Remove this list element.") |
| `metadata.description_en` | 6 nodes | Wave/Enrichissement markers converted to prose citations (§5.3) |
| `metadata.verification_notes` | 243 nodes | 287 `[Vérif.]` tags preserved verbatim |
| `metadata.curation_artifact_cleanup_2026_08_14` | 281 nodes | `true` — idempotency stamp read by the apply script |

## 8. Reproducing

```bash
python3 scripts/apply_2026_08_14_curation_artifact_cleanup.py --dry-run   # report only
python3 scripts/apply_2026_08_14_curation_artifact_cleanup.py             # write
```

The rewrite spans live in `scripts/data_2026_08_14_curation_rewrites.py` (`REWRITES` / `DESCRIPTION_EN_REWRITES` / `LABEL_REWRITES` / `METADATA_FIXES`), one `#` comment per pair quoting the tag that justifies it. A span whose `old` text no longer occurs exactly once is reported and skipped rather than applied, and stamped nodes are skipped entirely.
