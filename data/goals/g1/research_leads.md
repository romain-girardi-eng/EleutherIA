# G1 Research Leads — EleutherIA KG

_Generated 2026-06-15 11:20 UTC_

Mechanically surfaced from the KG snapshot (data/kg/nodes.jsonl + edges.jsonl). All entries are grounded in actual node/edge data. Modern labels (libertarian / compatibilist / 'invention of the will') are attributed to scholars, never asserted as historical fact.

## Summary statistics

| Metric | Count |
|--------|-------|
| Total argument nodes | 1418 |
| Ancient arguments (Presocratic–Late Antiquity) | 258 |
| Ancient arguments with ≥1 passage grounding | 169 (65 %) |
| Ancient arguments with ZERO grounding | 89 (35 %) |
| Ancient args with ≥1 concept edge | 182 |
| Ancient ungrounded args with ≥1 concept edge | 43 |
| Arg–arg dialectical pairs in KG | 81 |
| Candidate unmodeled debates (≥2 shared concepts) | 104 |
| Transmission gap leads | 5 |

## (i) Grounding Gaps

Ancient arguments with high concept-degree but zero passage grounding. A concept-degree ≥ 2 means the argument is connected to ≥ 2 thematic nodes, signalling scholarly consensus that it matters — yet no primary-text edge (`cites_primary_source` / `evidenced_by` / `grounded_in` / `advanced_in`) links it to a corpus passage.

### GG-1. Epictetus' Prohairesis Argument

**Node:** `argument_epictetus_prohairesis_argument_aa13b932`  
**Period:** Roman Imperial  
**Concept-degree:** 3  
**Total KG degree:** 9

**Connected concepts:** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** This argument shapes 3 thematic nodes (total 9 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Represents mature Roman Stoicism's focus on the inner citadel of the mind. Prohairesis is the core of the self and the locus of freedom. Even under external constraint (slavery, imprisonment), one's prohairesis remains free.…

**Suggested next step:** Discourses I.1, I.2, II.23 and IV.1 are the primary loci. Epictetus is in the corpus via TLG (tlg0557.tlg001). Run `scripts/tlg_search.py` for ἡ προαίρεσις in Discourses, ingest the relevant passage, and add a `cites_primary_source` edge.

### GG-2. The Practical Syllogism

**Node:** `argument_the_practical_syllogism_1d2e7506`  
**Period:** Classical Greek  
**Concept-degree:** 3  
**Total KG degree:** 8

**Connected concepts:** Βούλησις (Boulēsis) - Rational Desire/Will, Hekousion (Ἑκούσιον) - Voluntary, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** This argument shapes 3 thematic nodes (total 8 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Aristotle's account of practical reasoning connects thought about an end with desire and action. In De Anima III.10 and Nicomachean Ethics VII.3 practical intellect is oriented toward action rather than contemplation, and action issues when thought a…

**Suggested next step:** De Anima III.10 (433a9-b30) and NE VII.3 (1147a24-b5) are the loci. Both Aristotle works should be in the corpus; query `read_passages(work='aristotle_de_anima', section='3.10')` to confirm, then add a `cites_primary_source` edge from this argument node.

### GG-3. Maximus the Confessor: Natural Will vs. Gnomic Will (Disp. Pyrrh.; Opusc. 1, 3)

**Node:** `argument_maximus_natural_vs_gnomic_will`  
**Period:** Late Antiquity  
**Concept-degree:** 3  
**Total KG degree:** 7

**Connected concepts:** Gnomic will (γνώμη / θέλημα γνωμικόν), Monothelitism (μονοθελητισμός), Natural will (θέλημα φυσικόν / θέλησις φυσική)

**Why it's a lead:** This argument shapes 3 thematic nodes (total 7 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Maximus the Confessor's distinction between the natural will (φυσικὸν θέλημα) and the gnomic will (γνωμικὸν θέλημα), articulated at the Disputatio cum Pyrrho (645 CE, PG 91, 287–354) and in Opuscula theologica et polemica 1, 3, 16 (PG 91, 9–286). Str…

**Suggested next step:** Disputatio cum Pyrrho (PG 91, 287–354) and Opusc. 1, 3 (PG 91, 9–286) are the loci. Maximus is not in the current corpus. Check `~/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/` for a Maximus SC edition; if absent, flag for Scaife/TLG ingestion (tlg2892.tlg007).

### GG-4. Qumran Predestinarian Argument (Two Spirits)

**Node:** `argument_qumran_predestination_c3d4e5f6`  
**Period:** Second Temple Judaism  
**Concept-degree:** 2  
**Total KG degree:** 13

**Connected concepts:** Choice/Free Will (Bechirah), Divine Providence (Hashgachah)

**Why it's a lead:** This argument shapes 2 thematic nodes (total 13 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** The Treatise of the Two Spirits (1QS III.13–IV.26) constitutes the most sustained and philosophically explicit predestinarian text in Second Temple Judaism. Embedded within the Community Rule (Serek HaYahad), the Treatise presents a cosmological dual…

**Suggested next step:** 1QS III.13–IV.26 (Community Rule / Serek HaYahad). The Dead Sea Scrolls are not in the ancient-texts corpus. Add a `passage_1qs_iii_13_iv_26` node with content from García Martínez 1994 or Lohse 1964 (Hebrew critical edition), then link via `cites_primary_source`.

### GG-5. Maxime : deux volontés en Christ (dyothélie)

**Node:** `argument_maximus_two_wills`  
**Period:** Late Antiquity  
**Concept-degree:** 2  
**Total KG degree:** 11

**Connected concepts:** Monothelitism (μονοθελητισμός), Natural will (θέλημα φυσικόν / θέλησις φυσική)

**Why it's a lead:** This argument shapes 2 thematic nodes (total 11 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** **Source primaire** : Maxime le Confesseur, *Opusculum* 3 (PG 91, 45-56), *Opusculum* 16 (PG 91, 184-212) et *Disputatio cum Pyrrho* §13-28 (PG 91, 308-336). **Prémisse 1** : La volonté (θέλημα) est une faculté de la NATURE (θέλημα φυσικόν, volonté n…

**Suggested next step:** Opusculum 3 (PG 91, 45-56) and Disputatio cum Pyrrho §13-28 (PG 91, 308-336). Same corpus gap as GG-3. If Maximus passages are ingested for GG-3, add `cites_primary_source` from this argument to those same passage nodes.

### GG-6. Two-Way Powers (Rational Potentialities) Argument

**Node:** `argument_two_way_powers_aristotle_i9j0k1l2`  
**Period:** Classical Greek  
**Concept-degree:** 2  
**Total KG degree:** 9

**Connected concepts:** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** This argument shapes 2 thematic nodes (total 9 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** In Metaphysics IX Aristotle distinguishes non-rational powers, each ordered to one effect, from rational powers, which are of opposites. In IX.5 he adds that the exercise of rational powers depends on desire or choice, making this distinction importa…

**Suggested next step:** Metaphysics IX.5 (1048a5-b9) is the primary locus. Check `search_passages(work_id='work_aristotle_metaphysics')` — if Metaphysics IX is in the corpus, add `cites_primary_source`. If not, ingest from Scaife (tlg0086.tlg025).

### GG-7. Némésios Nat. Hom. 35 — résumé sec de l'argumentation morale carnéadienne

**Node:** `argument_nemesius_nat_hom_35_carneadean_summary_amand1945`  
**Period:** Late Antiquity  
**Concept-degree:** 2  
**Total KG degree:** 9

**Connected concepts:** Heimarmenê (Εἱμαρμένη) - Stoic Fate, To eph' hemin (τὸ ἐφ᾽ ἡμῖν) — Nemesius

**Why it's a lead:** This argument shapes 2 thematic nodes (total 9 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Résumé sec et squelettique de l'argumentation morale antifataliste de Carnéade inséré par Némésios au début du chapitre 35 du Peri physeos anthropou (PG 40, 741 BC, l. 18-33). Pour Amand 1945 (Livre II Ch. XIV §IV, p. 568-569), le passage énumère cin…

**Suggested next step:** Nemesius De Natura Hominis ch. 35 (PG 40, 741BC, l. 18-33). Check TLG E (`scripts/tlg_search.py`, tlg0743.tlg001) for this passage. Ingest using `scripts/ingest_scaife_work.py` if on Scaife, else from PG 40.

### GG-8. Gregory of Nyssa Disc. Cat. 31 — argument carnéadien moral comme topos scolaire

**Node:** `argument_gregory_disccat31_carneadean_moral_amand1945`  
**Period:** Late Antiquity  
**Concept-degree:** 2  
**Total KG degree:** 8

**Connected concepts:** Αὐτεξούσιον (Autexousion) - Christian Self-Determination, Prohairesis (προαίρεσις) — Gregory of Nyssa

**Why it's a lead:** This argument shapes 2 thematic nodes (total 8 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Argument du Discours catéchétique 31 de Grégoire de Nysse (ed. Srawley p. 113-114 ; PG 45, 77BD), encadré par une aporie théologique : pourquoi Dieu ne force-t-il pas les incrédules à embrasser la foi ? Réponse de Grégoire (résumant un ou deux argume…

**Suggested next step:** Discours catéchétique 31 (ed. Srawley p. 113-114; PG 45, 77BD). Gregory of Nyssa may be in the corpus; query `search_passages(work_id='work_gregory_nyssa_*')`. If absent, ingest from Scaife (tlg2017.tlg049) and add `cites_primary_source`.

### GG-9. Augustine's Anti-Pelagian Argument (Grace Necessity)

**Node:** `argument_augustines_antipelagian_argument_grace_necessity_0b29401f`  
**Period:** Patristic  
**Concept-degree:** 2  
**Total KG degree:** 8

**Connected concepts:** Gratia Operans (Operating Grace), Pelagianism

**Why it's a lead:** This argument shapes 2 thematic nodes (total 8 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** **Avertissement méthodologique** : la terminologie « compatibiliste / libertarienne / agent-causation / etc. » employée ci-dessous appartient au vocabulaire de la philosophie analytique moderne (Frankfurt 1969, Kane 1996, Pereboom 2001). Ces étiquett…

**Suggested next step:** De Correptione et Gratia 2.3 and De Spiritu et Littera 3.5 are primary loci. Augustine is heavily represented in the corpus; query `search_passages(q='gratia', work_id='work_augustine_*')` to find overlapping passages and add `cites_primary_source` edges.

### GG-10. Aristotle's Potentiality-Actuality Argument

**Node:** `argument_aristotles_potentialityactuality_argument_20c5ac91`  
**Period:** Classical Greek  
**Concept-degree:** 2  
**Total KG degree:** 7

**Connected concepts:** Ananke (Ἀνάγκη) - Necessity/Determinism, To Endechomenon (Τὸ ἐνδεχόμενον) - The Contingent

**Why it's a lead:** This argument shapes 2 thematic nodes (total 7 KG edges) but has no primary-text anchor in the corpus. Any claim made through this node is unverified against a source passage.

**Description excerpt:** Aristotle distinguishes potentiality from actuality and argues against the Megarian claim that a thing has a capacity only when it is actually exercising it. In Metaphysics IX.3-4 he treats unexercised capacities as real and uses them to explain poss…

**Suggested next step:** Metaphysics IX.3-5 (1046b28-1048b9). Same work as GG-6 (argument_two_way_powers_aristotle_i9j0k1l2). Check if Aristotle Metaphysics is in corpus; if so, add passages from IX.3-5 and link both GG-6 and GG-10 via `cites_primary_source`.

## (ii) Unmodeled Debates

Pairs of arguments sharing ≥ 2 concept nodes but lacking any dialectical edge (`critiques` / `responds_to` / `supports` / `opposes` / `extends` / `parallel_to`). Ancient–ancient pairs are listed first as primary thesis leads; cross-period pairs follow.

### UD-1. Agent Causation Argument (Alexander) ↔ Common Cause vs Chain Cause Model (Alexander)

**Argument 1:** `argument_agent_causation_alex` [Roman Imperial]  
**Argument 2:** `argument_common_cause_alex` [Roman Imperial]  
**Shared concepts (2):** Archē (ἀρχή) - Origin/Principle, Prohairesis (προαίρεσις) - Alexander

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (Archē (ἀρχή) - Origin/Principle, Prohairesis (προαίρεσις) - Alexander) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Examine primary sources where both arguments appear in proximity. Add the appropriate dialectical edge (`responds_to` / `critiques` / `supports` / `parallel_to`) with a passage citation grounding the relationship.

### UD-2. Alexander's Agent Causation via Two-Way Powers Argument ↔ Deliberate Choice (Prohairesis) Analysis Argument

**Argument 1:** `argument_agent_causation_two_way_powers_alexander_q8r9s0t1` [Roman Imperial]  
**Argument 2:** `argument_deliberate_choice_analysis_aristotle_h8i9j0k1` [Classical Greek]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Trace how 'Alexander's Agent Causation via Two-Way ' [Roman Imperial] influenced 'Deliberate Choice (Prohairesis) Analysis' [Classical Greek] via the prohairesis concept. Gourinat 2002 and Dobbin 1991 discuss this transmission; add a `precedes` or `extends` edge with the passage where the borrowing is most explicit.

### UD-3. Alexander's Agent Causation via Two-Way Powers Argument ↔ Epictetus' Prohairesis Argument

**Argument 1:** `argument_agent_causation_two_way_powers_alexander_q8r9s0t1` [Roman Imperial]  
**Argument 2:** `argument_epictetus_prohairesis_argument_aa13b932` [Roman Imperial]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments are Roman Imperial. They share eph' hēmin vocabulary. Determine if one logically presupposes the other (add `supports` / `presupposes`) or if they are independent complementary arguments for the same conclusion (add `parallel_to`). Check Alexander De Fato for the co-occurrence.

### UD-4. Alexander's Agent Causation via Two-Way Powers Argument ↔ Alexander's Incompatibilist Argument (Fate Destroys Freedom)

**Argument 1:** `argument_agent_causation_two_way_powers_alexander_q8r9s0t1` [Roman Imperial]  
**Argument 2:** `argument_incompatibilism_alexander_p7q8r9s0` [Roman Imperial]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Prohairesis (Προαίρεσις) - Deliberate Choice) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments are Roman Imperial. They share eph' hēmin vocabulary. Determine if one logically presupposes the other (add `supports` / `presupposes`) or if they are independent complementary arguments for the same conclusion (add `parallel_to`). Check Alexander De Fato for the co-occurrence.

### UD-5. CAFMA Argument I: Futility of Effort and Labor ↔ CAFMA Argument II: Futility of Legislation and Justice

**Argument 1:** `argument_cafma_futility_of_effort_8c3d5f21` [Hellenistic]  
**Argument 2:** `argument_cafma_futility_of_legislation_9d4e6g32` [Hellenistic]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments are Hellenistic. They share eph' hēmin vocabulary. Determine if one logically presupposes the other (add `supports` / `presupposes`) or if they are independent complementary arguments for the same conclusion (add `parallel_to`). Check Alexander De Fato for the co-occurrence.

### UD-6. CAFMA Argument I: Futility of Effort and Labor ↔ Cleanthes' Hymn to Zeus Argument

**Argument 1:** `argument_cafma_futility_of_effort_8c3d5f21` [Hellenistic]  
**Argument 2:** `argument_cleanthes_hymn_to_zeus_argument_f71f5b37` [Hellenistic]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments are Hellenistic. They share eph' hēmin vocabulary. Determine if one logically presupposes the other (add `supports` / `presupposes`) or if they are independent complementary arguments for the same conclusion (add `parallel_to`). Check Alexander De Fato for the co-occurrence.

### UD-7. CAFMA Argument I: Futility of Effort and Labor ↔ Epictetus' Prohairesis Argument

**Argument 1:** `argument_cafma_futility_of_effort_8c3d5f21` [Hellenistic]  
**Argument 2:** `argument_epictetus_prohairesis_argument_aa13b932` [Roman Imperial]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments engage Stoic fate (εἱμαρμένη). Determine whether 'CAFMA Argument I: Futility of Effort and' responds to the same fatalist target as 'Epictetus' Prohairesis Argument' (→ `parallel_to`) or one extends the other (→ `extends`). Amand 1945 Livre I catalogues the anti-fatalist pivots and may indicate the relation.

### UD-8. CAFMA Argument II: Futility of Legislation and Justice ↔ Cleanthes' Hymn to Zeus Argument

**Argument 1:** `argument_cafma_futility_of_legislation_9d4e6g32` [Hellenistic]  
**Argument 2:** `argument_cleanthes_hymn_to_zeus_argument_f71f5b37` [Hellenistic]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments are Hellenistic. They share eph' hēmin vocabulary. Determine if one logically presupposes the other (add `supports` / `presupposes`) or if they are independent complementary arguments for the same conclusion (add `parallel_to`). Check Alexander De Fato for the co-occurrence.

### UD-9. CAFMA Argument II: Futility of Legislation and Justice ↔ Epictetus' Prohairesis Argument

**Argument 1:** `argument_cafma_futility_of_legislation_9d4e6g32` [Hellenistic]  
**Argument 2:** `argument_epictetus_prohairesis_argument_aa13b932` [Roman Imperial]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments engage Stoic fate (εἱμαρμένη). Determine whether 'CAFMA Argument II: Futility of Legislati' responds to the same fatalist target as 'Epictetus' Prohairesis Argument' (→ `parallel_to`) or one extends the other (→ `extends`). Amand 1945 Livre I catalogues the anti-fatalist pivots and may indicate the relation.

### UD-10. Cleanthes' Hymn to Zeus Argument ↔ Epictetus' Prohairesis Argument

**Argument 1:** `argument_cleanthes_hymn_to_zeus_argument_f71f5b37` [Hellenistic]  
**Argument 2:** `argument_epictetus_prohairesis_argument_aa13b932` [Roman Imperial]  
**Shared concepts (2):** To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate

**Why it's a lead:** Both arguments engage the same 2 thematic concepts (To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power, Heimarmenê (Εἱμαρμένη) - Stoic Fate) but the KG records no dialectical relationship between them. This gap may reflect an unmodelled ancient debate, a documented influence, or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.

**Suggested next step:** Both arguments engage Stoic fate (εἱμαρμένη). Determine whether 'Cleanthes' Hymn to Zeus Argument' responds to the same fatalist target as 'Epictetus' Prohairesis Argument' (→ `parallel_to`) or one extends the other (→ `extends`). Amand 1945 Livre I catalogues the anti-fatalist pivots and may indicate the relation.

## (iii) Transmission Gaps

Concept nodes attested by arguments from period N and N+2 but absent from N+1. A gap indicates either (a) the concept existed in N+1 but no argument node encodes it, or (b) genuine historical discontinuity — a thesis question either way.

### TG-1. To Endechomenon (Τὸ ἐνδεχόμενον) - The Contingent

**Concept node:** `concept_endechomenon_contingent_aristotle_e5f6g7h8`  
**Attested in:** Presocratic → Classical Greek → Late Antiquity  
**Gap (missing):** Hellenistic, Patristic, Roman Imperial  
**Gap span:** 3 period(s)

**Arguments by period:**

  - [Classical Greek] Aristotle's Potentiality-Actuality Argument
  - [Classical Greek] Sea Battle Argument (Future Contingents)
  - [Late Antiquity] Boethian Solution: Divine Timeless Eternity
  - [Presocratic] Parmenides' Necessity Argument

**Description excerpt:** **Étymologie** : τὸ ἐνδεχόμενον, participe présent neutre substantivé du verbe ἐνδέχομαι (« admettre, accepter, être possible »), littéralement « ce qui admet d'être (autrement) » — concept modal central d'Aristote (*De Int.* 9, *An. Pr.* I.13).  To…

**Why it's a lead:** The concept bridges Presocratic and Late Antiquity with a 3-period lacuna in between. No argument node connects this concept to Hellenistic, Patristic, Roman Imperial sources. This may flag a transmission route (doxographic, commentary, or indirect) that the KG has not yet modelled.

**Suggested next step:** A 3-period gap is the largest in the dataset. Hellenistic Stoics extensively debated contingency (Chrysippus's response to the Master Argument; Diodorus Cronus). Roman Imperial: Alexander De Fato §§10-13 uses ἐνδεχόμενον explicitly. Patristic: Origen De Principiis III.1.2 invokes contingency of rational natures. Each period needs ≥1 argument node connected via `discusses` to this concept.

### TG-2. Prohairesis (Προαίρεσις) - Deliberate Choice

**Concept node:** `concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6`  
**Attested in:** Classical Greek → Roman Imperial  
**Gap (missing):** Hellenistic  
**Gap span:** 1 period(s)

**Arguments by period:**

  - [Roman Imperial] Alexander's Agent Causation via Two-Way Powers Argument
  - [Roman Imperial] Epictetus's Freedom Through Renunciation (Discourses IV.1)
  - [Roman Imperial] Epictetus' Prohairesis Argument
  - [Roman Imperial] Alexander's Incompatibilist Argument (Fate Destroys Freedom)
  - [Classical Greek] Deliberate Choice (Prohairesis) Analysis Argument
  - [Classical Greek] The Practical Syllogism
  - [Classical Greek] Two-Way Powers (Rational Potentialities) Argument

**Description excerpt:** **Étymologie** : προαίρεσις < πρό- (« avant ») + αἵρεσις (« choix, prise », de αἱρέω « prendre, saisir »), littéralement « choix préalable / antérieur ». Premier emploi technique chez Aristote, *Éthique à Nicomaque* III.4 (1112a15).  Prohairesis (προ…

**Why it's a lead:** The concept bridges Classical Greek and Roman Imperial with a 1-period lacuna in between. No argument node connects this concept to Hellenistic sources. This may flag a transmission route (doxographic, commentary, or indirect) that the KG has not yet modelled.

**Suggested next step:** Hellenistic authors using prohairesis include early Stoics (Diogenes Laertius VII reports Chrysippus on deliberate choice) and Peripatetics (Theophrastus). Check TLG E for Hellenistic uses of προαίρεσις; add argument node(s) with `precedes` edge to the Roman Imperial cluster and `cites_primary_source` to a passage.

### TG-3. Levels of Providence (Proclean)

**Concept node:** `concept_pronoia_levels_proclus_a6d8c9b4`  
**Attested in:** Hellenistic → Patristic → Late Antiquity  
**Gap (missing):** Roman Imperial  
**Gap span:** 1 period(s)

**Arguments by period:**

  - [Hellenistic] CAFMA Argument V: Futility of Piety and Prayer
  - [Late Antiquity] Proclus's Hierarchical Providence and Fate Argument
  - [Patristic] Pseudo-Dionysius's Hierarchical Causation Argument

**Description excerpt:** Proclus's hierarchical theory of providence operating at multiple levels. Primary providence concerns eternal Ideas and universals; secondary providence concerns particular souls and events; tertiary providence operates through natural processes. Hig…

**Why it's a lead:** The concept bridges Hellenistic and Late Antiquity with a 1-period lacuna in between. No argument node connects this concept to Roman Imperial sources. This may flag a transmission route (doxographic, commentary, or indirect) that the KG has not yet modelled.

**Suggested next step:** Roman Imperial Middle Platonists (Plutarch, Alcinous Didaskalikos ch. 12, Apuleius De Platone I.12) distinguish levels of providence. Add argument nodes from these authors and connect via `employs` / `precedes` to fill the gap between the CAFMA anti-prayer argument and the Proclean hierarchy.

### TG-4. Clinamen / Parenklisis (Atomic Swerve)

**Concept node:** `concept_clinamen_atomic_swerve_epicurus_m3n4o5p6`  
**Attested in:** Presocratic → Hellenistic  
**Gap (missing):** Classical Greek  
**Gap span:** 1 period(s)

**Arguments by period:**

  - [Hellenistic] Carneades' Autonomous Mental Causation Argument
  - [Hellenistic] Epicurean Atomic Swerve Argument for Freedom
  - [Presocratic] Democritean Atomistic Determinism

**Description excerpt:** **Étymologie** : *clinamen* < lat. *clinare* (« incliner, pencher »), néologisme lucrétien (DRN II.292) calque du grec παρέγκλισις (Épicure, fr. ap. Diog. Laert. X) ; *parenklisis* < παρά- + ἐγκλίνω.  The clinamen or atomic swerve is the Epicurean do…

**Why it's a lead:** The concept bridges Presocratic and Hellenistic with a 1-period lacuna in between. No argument node connects this concept to Classical Greek sources. This may flag a transmission route (doxographic, commentary, or indirect) that the KG has not yet modelled.

**Suggested next step:** The gap is expected: Epicurus developed the swerve as a response to Democritus, not adopted by Classical authors. Still, Aristotle's Physics II.4-6 discusses spontaneity and chance (τύχη / τὸ αὐτόματον) in a way that may bridge the two. Consider adding an argument node for Aristotle's critique of Democritean necessity and linking it via `critiques` to Democritean Atomistic Determinism.

### TG-5. Αὐτεξούσιον (Autexousion) - Christian Self-Determination

**Concept node:** `concept_autexousion_christian`  
**Attested in:** Roman Imperial → Late Antiquity  
**Gap (missing):** Patristic  
**Gap span:** 1 period(s)

**Arguments by period:**

  - [Late Antiquity] Chrysostome — libre arbitre comme ressort de l'apostolat oratoire
  - [Late Antiquity] Gregory of Nyssa Disc. Cat. 31 — argument carnéadien moral comme topos scolaire
  - [Roman Imperial] Methodius's Free Will Theodicy: Evil from Human Choice, Not Matter

**Description excerpt:** The key Greek term for free will/self-determination in early Christian theology. Derived from αὐτός (self) + ἐξουσία (power, authority), meaning 'having power over oneself,' 'self-determining,' 'possessing free will.' The term was used by Patristic w…

**Why it's a lead:** The concept bridges Roman Imperial and Late Antiquity with a 1-period lacuna in between. No argument node connects this concept to Patristic sources. This may flag a transmission route (doxographic, commentary, or indirect) that the KG has not yet modelled.

**Suggested next step:** The Patristic gap is significant: Justin Martyr (2 Apol. 6.5), Tatian, Irenaeus (Adv. Haer. IV.37), and Clement (Strom. II.4) all use αὐτεξούσιον — yet no Patristic argument node is connected to this concept node. Wire `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920` and the Justin autexousion argument to `concept_autexousion_christian` via `employs`.

