# 2026-08-16 — French → English translation of the analytical KG nodes

Applied by `scripts/apply_2026_08_16_french_translation.py` from the reviewed
payload `data/audit/2026-08-16_french_translations.jsonl`.
Engine: **gpt-5.6-terra** (subscription proxy on the production host), 3 parallel
workers, `reasoning_effort: low`, one completion per field. Wall time ≈ 25 min for
the main pass plus ≈ 3 min for the targeted re-translation pass.

## What was translated

A large part of the analytical layer of the graph was authored in French while the
platform is English. The reader-facing `description` (and, for project-authored
analytic nodes, the `label`) now carries an academic-English rendering; the French
original is archived in `metadata.description_fr` / `metadata.label_fr` and is
never destroyed. Every touched node carries
`metadata.translation_2026_08_16 = "gpt-5.6-terra"`.

`passage` and `quote` nodes were excluded from the scan entirely: French inside
them is edition text (Sources Chrétiennes and comparable bilingual editions),
which is primary material, not project prose.

| | count |
|---|---|
| candidate French-dominant descriptions found (non-passage, non-quote) | 615 |
| candidate French-dominant labels found | 118 |
| items sent to the engine | 602 |
| descriptions applied | **592** |
| labels applied | **80** |
| nodes touched | **596** |
| descriptions deliberately left in French after review | **23** |
| labels deliberately left in French | **37** |

### Descriptions applied, by node type

| type | n |
|---|---|
| argument | 206 |
| synthesis | 164 |
| person | 74 |
| work | 65 |
| publication | 38 |
| concept | 27 |
| group | 5 |
| school | 5 |
| source_collection | 4 |
| event | 3 |
| debate | 1 |
| **total** | **592** |

### Labels applied, by node type

| type | n |
|---|---|
| argument | 47 |
| synthesis | 30 |
| concept | 3 |
| **total** | **80** |

## Method and guarantees

The translator brief required every ancient Greek run, every Latin quotation,
every bibliographic reference (`Amand 1945`, `p. 66-68`, `SC 132`, `PG 40, 749 B`,
`De Fato 20-21`, CTS URNs, node-id tokens) and every markdown structure to be
reproduced verbatim, and forbade any addition, omission or summarising. Names of
ancient figures and schools were put into standard English scholarly form
(Chrysippe → Chrysippus, les Stoïciens → the Stoics); surnames of modern scholars
were kept exactly as spelled.

Every item was validated before being written to the payload:

1. **Greek identity** — the multiset of Greek runs in the translation is identical
   to the source's, character for character. No item with a missing, altered or
   *added* Greek run was applied.
2. **Coverage** — non-empty, length ratio within [0.5, 2.0] of the source.
3. **Citations** — counts of author-year, `p. n`, `SC n`, `PG n`, `§`, `(YYYY)`,
   CTS-URN and node-id patterns preserved or increased.
4. **English dominance** — the French-detection heuristic re-run on the output.

48 items failed a check on the first pass and were re-translated once with the
specific failure named in the prompt; 41 passed on the second attempt. The
remaining 7 were adjudicated by hand (below). Nothing was applied blind.

The check earned its keep: it caught the engine rendering a French adjective *into
Greek* — `un ὑπόμνημα scolaire` → `σχολικό ὑπόμνημα`, and `τόποι scolaires` →
`σχολικοί τόποι`. Both were fabricated Greek and both were rejected, then fixed on
re-translation.

## Nodes deliberately left untouched

### 1 description rejected — source-side Greek corruption

- `argument_carneadean_legislation_amand1945` — the French source contains a
  corrupt mixed-script token, a Latin `e` glued to the Greek `ἱμαρμένη`
  (`de l'e` + `ἱμαρμένη`). Both attempts silently normalised it to `εἱμαρμένη`,
  which changes the Greek. Under the zero-fabrication rule the node keeps its
  French description. **Follow-up:** the corruption is a pre-existing defect in the
  source text; fix it on its own terms, then re-translate the node.

### 22 publication descriptions that are nothing but a French bibliographic title

A title is a citation key, not prose: translating it would break citability.

- `scholarly_work_bardy_1943_ath_nagore_supplique_au_sujet_des_chr_ti` — Athénagore: Supplique au sujet des Chrétiens (Introduction et traduction)
- `scholarly_work_boulnois_2000_libert_origine_du_mal_et_prescience_divi` — Liberté, origine du mal et prescience divine selon Cyrille d'Alexandrie
- `scholarly_work_crubellier_2020_les_d_finitions_de_la_dans_les_thiques` — Les définitions de la προαίρεσις dans les Éthiques
- `scholarly_work_de_monneron_2011_le_d_terminisme_et_la_responsabilit_mora` — Le Déterminisme et la Responsabilité morale
- `scholarly_work_dettwiler_1995_l_p_tre_aux_colossiens_un_exemple_de_r_c` — L'épître aux Colossiens: un exemple de réception de la théologie paulinienne
- `scholarly_work_dettwiler_1998_la_conception_matth_enne_de_la_foi_mt` — La conception matthéenne de la foi (Mt 14,22-33)
- `scholarly_work_dettwiler_2001_la_r_surrection_des_croyants_selon_l_p_t` — La résurrection des croyants selon l'épître aux Colossiens
- `scholarly_work_dettwiler_2007_une_exhortation_de_paul_aux_thessalonici` — Une exhortation de Paul aux Thessaloniciens: "Priez sans cesse"
- `scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens` — La deuxième épître aux Thessaloniciens
- `scholarly_work_eliasson_2009_sur_la_conception_plotinienne_du_destin_` — Sur la conception plotinienne du destin dans le traité 3
- `scholarly_work_koch_2014_distinctions_causales_sto_ciennes_et_aca` — Distinctions causales stoïciennes et académiciennes dans le De fato de Cicéron
- `scholarly_work_koch_2015_le_destin_et_la_providence_sur_deux_trai` — Le destin et la providence : sur deux traités «jumeaux» d'Alexandre d'Aphrodise
- `scholarly_work_koch_piettre_2004_paul_et_les_picuriens_d_ath_nes_entre_po` — Paul et les Épicuriens d'Athènes entre polythéismes, athéismes, et monothéismes
- `scholarly_work_labarri_re_2009_de_ce_qui_d_pend_de_nous` — De « ce qui dépend de nous »
- `scholarly_work_munier_1995_saint_justin_apologie_pour_les_chr_tiens` — Saint Justin: Apologie pour les chrétiens. Édition et traduction
- `scholarly_work_pouderon_2005_les_apologistes_grecs_du_iie_si_cle` — Les Apologistes grecs du IIe siècle
- `scholarly_work_pouderon_2011_l_origine_du_mal_chez_les_apologistes_gr` — L'origine du mal chez les Apologistes grecs : matière et esprit
- `scholarly_work_bobichon_2003_uvres_de_justin_martyr_le_manuscrit_loan` — Œuvres de Justin martyr : le manuscrit Loan 36/13 de la British Library, un apographe…
- `scholarly_work_dettwiler_2009_d_mystification_c_leste_la_fonction_argu` — Démystification céleste. La fonction argumentative de l'hymne au Christ (Col 1,15-20)…
- `scholarly_work_fantino_1998_le_passage_du_premier_adam_au_second_ada` — Le passage du premier Adam au second Adam comme expression du salut chez Irénée de Lyon
- `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale` — La Causalité humaine: Sur le De fato d'Alexandre d'Aphrodise
- `scholarly_work_jourdan_2011_la_th_odic_e_d_velopp_e_sur_le_th_me_du_` — La théodicée développée sur le thème du larcin des Grecs…

### 37 labels not translated

`publication` (29) and `work` (8) labels are bibliographic and work titles used as
citation keys — including genuinely French-language works such as Leibniz's
*Essais de Théodicée sur la bonté de Dieu, la liberté de l'homme et l'origine du
mal*. They are preserved verbatim. Only project-authored analytic labels
(`argument`, `synthesis`, `concept`) were translated.

## Items accepted after manual review of a failed check

- `pub_bobzien_2021_determinism_freedom_essays` — the citation-count check flagged
  `Préface 2021` → `the 2021 Preface`. Correct English word order; the reference is
  intact. Applied.
- `argument_origen_witness_aristotelism_influence_amand1945` and
  `synthesis_amand1945_pseudo_plutarch_albinus_parallel` — the first applied
  version made `scripts/check_greek_gate.py` flag two runs. The Greek characters
  were never altered: English word order removed the French separators (the
  post-posed adjective `rationnelle`, the elided article `L'`) that had kept the
  runs apart, so the gate hashed a *merged* run absent from the corpus. The
  surrounding English was re-worded — `a rational οὐσία, along with ποιότητες,
  ὑποκείμενον` and `καθειμάρθαι. The εἱμαρμένη draws` — to restore the source's own
  segmentation. The gate is green again. No allowlist entry was added.

## Graph validation after apply

| check | result |
|---|---|
| `data/kg/nodes.jsonl` parse | 19,992 nodes, 0 parse failures (count unchanged) |
| `scripts/check_greek_gate.py --all` | output **byte-identical to the pre-apply baseline** — the 2 standing `tlg_only` findings are pre-existing and unrelated to this pass |
| `scripts/audit_structural.py` | output **byte-identical to the pre-apply baseline** (2,321 mechanical findings, no new ones) |
| re-run of the applier | no-op (596 `already_applied`) |
| French originals archived | 592/592 `metadata.description_fr`, 80/80 `metadata.label_fr` |
| residual French-dominant descriptions outside `passage`/`quote` | 23 — exactly the deliberate exclusions above |

## Samples (before → after)

### 1. `argument_furst_2022_freedom_principle_of_substance`

**Label FR** — Liberté = principe de la substance (non accident) chez Origène (Fürst/Hengstermann 2022)

**Label EN** — Freedom as a principle of substance (not accident) in Origen (Fürst/Hengstermann 2022)

**FR** — Thèse de Fürst 2022 (Kap. VI 1, p. 252-254 ; suivant Hengstermann 2016) : l'innovation révolutionnaire d'Origène est de ne pas considérer la liberté comme accident à la manière d'Aristote, mais d'en faire le « principe de la substance » (Prinzip der Substanz) des êtres rationnels. Conséquence ontologique radicale : l'homme n'a pas seulement la liberté ; il EST liberté (« Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit », Fürst p. 254). À l'ontologisation de la liberté correspond « l'élévation du mouvement au rang de premier principe de l'être » (Hengstermann 31 Anm. 45). C'est le cœur de la Freiheitsm …

**EN** — Fürst 2022's thesis (Kap. VI 1, p. 252-254; following Hengstermann 2016): Origen's revolutionary innovation is not to regard freedom as an accident in the manner of Aristotle, but to make it the "principle of substance" (Prinzip der Substanz) of rational beings. The radical ontological consequence is that human beings do not merely possess freedom; they ARE freedom ("Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit", Fürst p. 254). Corresponding to the ontologization of freedom is "the elevation of movement to the status of the first principle of being" (Hengstermann 31 Anm. 45). This is the core of Fr …

### 2. `synthesis_amand1945_pseudo_plutarch_albinus_parallel`

**FR** — Synthèse d'Amand 1945 (p. 106 note 3, ll. 6404-6411) établissant le parallèle doctrinal entre le Pseudo-Plutarque (De fato §§1, 4, 6, 8, 11) et Albinus (Didaskalikos ch. 26 — Εἰσαγωγὴ εἰς τὴν φιλοσοφίαν Πλάτωνος). Les deux auteurs partagent la même position de platonisme moyen : πάντα ἐν εἱμαρμένῃ εἶναι, οὐ μὴν πάντα καθειμάρθαι. L'εἱμαρμένη tire les conséquences nécessaires de nos actions libres sans les produire. Liberté totale, responsabilité morale, éloge/blâme parfaitement sauvegardés. L'âme n'a pas de maître. Comme le Pseudo-Plutarque (3), Albinus refuse de voir dans l'εἱμαρμένη un ἄπειρον (infini illimité) …

**EN** — Synthesis of Amand 1945 (p. 106 note 3, ll. 6404-6411) establishing the doctrinal parallel between Pseudo-Plutarch (De fato §§1, 4, 6, 8, 11) and Albinus (Didaskalikos ch. 26 — Εἰσαγωγὴ εἰς τὴν φιλοσοφίαν Πλάτωνος). The two authors share the same Middle Platonist position: πάντα ἐν εἱμαρμένῃ εἶναι, οὐ μὴν πάντα καθειμάρθαι. The εἱμαρμένη draws the necessary consequences from our free actions without producing them. Total freedom, moral responsibility, praise and blame are perfectly preserved. The soul has no master. Like Pseudo-Plutarch (3), Albinus refuses to regard εἱμαρμένη as an ἄπειρον (unlimited infinite).  …

### 3. `argument_alexander_witness2_ch16_praise_blame_punishment_amand1945`

**FR** — Deuxième argument moral antifataliste reconstruit chez Alexandre De Fato 16 (fin, Bruns p. 187 l. 5-22) par Amand 1945 (analyse p. 145-146, texte grec p. 150-151). Si les circonstances imposent absolument leur action, les Stoïciens qui enseignent ce déterminisme ne peuvent ni blâmer (ψόγος), ni réprimander (ἐπιτιμᾶν), ni encourager (προτροπή), ni récompenser (τιμή), ni punir (κόλασις) ceux qui s'excusent de leurs fautes en prétextant cette doctrine. Exemples mythologiques : comment accuser Pâris d'adultère et Agamemnon d'orgueil si tout est prédéterminé ? « Πῶς γὰρ ἂν ἔτι Ἀλέξανδρος ὁ Πριάμου ἐν αἰτίᾳ εἴη ὡς διαμ …

**EN** — Second anti-fatalist moral argument reconstructed in Alexander De Fato 16 (end, Bruns p. 187 l. 5-22) by Amand 1945 (analysis p. 145-146, Greek text p. 150-151). If circumstances absolutely compel their actions, the Stoics who teach this determinism can neither blame (ψόγος), nor rebuke (ἐπιτιμᾶν), nor exhort (προτροπή), nor reward (τιμή), nor punish (κόλασις) those who excuse their faults by invoking this doctrine. Mythological examples: how can Paris be accused of adultery and Agamemnon of pride if everything is predetermined? « Πῶς γὰρ ἂν ἔτι Ἀλέξανδρος ὁ Πριάμου ἐν αἰτίᾳ εἴη ὡς διαμαρτὼν περὶ τὴν τῆς Ἑλένης ἁ …

### 4. `person_apuleius_madauros_124_170`

**FR** — Rhéteur, romancier et philosophe platonisant africain (c. 124-c. 170 CE). Auteur de l'Apologie (Pro se de magia) et des Métamorphoses (Asinus aureus). Pour le KG : le De Platone et eius dogmate constitue un manuel doxographique Middle Platonist de référence sur la providence, le destin, les démons et le libre arbitre — proche du Didaskalikos d'Alcinoos pour la structure tripartite providence / deuxième providence / fate. Le De Deo Socratis complète cette démonologie médiateur. Éditions critiques : Beaujeu, Apulée, Opuscules philosophiques et fragments (Budé 1973, réimpr. Belles Lettres) ; Moreschini, Apulei Plato …

**EN** — African rhetorician, novelist, and Platonizing philosopher (c. 124-c. 170 CE). Author of the Apology (Pro se de magia) and the Metamorphoses (Asinus aureus). For the KG: De Platone et eius dogmate constitutes a standard Middle Platonist doxographical handbook on providence, fate, demons, and free will—close to Alcinoos' Didaskalikos in its tripartite structure of providence / second providence / fate. De Deo Socratis complements this mediatory demonology. Critical editions: Beaujeu, Apulée, Opuscules philosophiques et fragments (Budé 1973, réimpr. Belles Lettres); Moreschini, Apulei Platonici Madaurensis Opera (T …

### 5. `argument_origen_witness_aristotelism_influence_amand1945`

**FR** — Amand (p. 292) : Influence d'Aristote moins accusée mais réelle. Terminologie d'Origène dérive principalement d'Aristote autant que des Stoïciens. Habitude d'aborder un problème en passant en revue toutes les questions (les ἀπορίαι) = méthode du Stagirite. Origène emprunte la notion d'οὐσία rationnelle, ποιότητες, ὑποκείμενον. Sa psychologie est étroitement apparentée à celle du Περὶ ψυχῆς, et sa théorie du libre arbitre s'appuie en partie sur les analyses précises de l'Éthique Nicomachéenne. E. de Faye a mis cette influence aristotélicienne en lumière. Cf. Bardy, Origène et l'aristotélisme (Mélanges Glotz I, 193 …

**EN** — Amand (p. 292): Aristotle's influence is less pronounced but real. Origen's terminology derives primarily from Aristotle as much as from the Stoics. The habit of approaching a problem by reviewing all the questions (the ἀπορίαι) = the method of the Stagirite. Origen borrows the notion of a rational οὐσία, along with ποιότητες, ὑποκείμενον. His psychology is closely related to that of the Περὶ ψυχῆς, and his theory of free will relies in part on the precise analyses of the Nicomachean Ethics. E. de Faye brought this Aristotelian influence to light. Cf. Bardy, Origène et l'aristotélisme (Mélanges Glotz I, 1932, p.  …

