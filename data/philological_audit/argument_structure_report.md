# Argument Structure Enrichment Report

Generated against the live `free_will` Supabase schema. Model: Kimi K2.6 via Fireworks. Validation: zero-fabrication — every premise either grounded in a primary-source `kg_nodes` row (attestation `direct`/`doxographical`) or explicitly `reconstructed`. Premises lacking a primary anchor that were originally tagged `direct`/`doxographical` were salvaged by automatic downgrade to `reconstructed` (preserves the original tag in `downgraded_from`).

## Totals
- **Argument nodes total**: 220
- **Structured (`metadata.structured_v2 = true`)**: 217 (98%)
  - Ancient arguments: 181
  - Modern scholarly positions: 36
- **Flagged `needs_review`**: 3
- **Salvage downgrades** (`direct`/`doxographical` → `reconstructed` with empty primary_sources): 6 premises

## Distribution of `argument_form`
- `explicit_premise_conclusion`: 149
- `modus_tollens`: 45
- `modus_ponens`: 11
- `reductio_ad_absurdum`: 5
- `constructive_dilemma`: 4
- `modal_argument`: 1
- `dilemma`: 1
- `syllogism`: 1

## Validity assessment
- `disputed`: 217

(All assessments came back `disputed` — appropriate for ancient dialectical material where Bobzien/Frede-style scholarship contests both the reconstruction and the formal status. The `scholarly_consensus` sub-field of each node carries the actual nuance.)

## New edges added by enrichment
- `created_by`: 36
- **Total new edges**: 36

## Top 10 newly structured ancient arguments
- **Theodicy Skepticism** (`argument_theodicy_skepticism_6c745d6f`) — _explicit_premise_conclusion_ × 18 premises → Rational theodicy fails: no orthodox theistic account successfully reconciles God's omnipotence, omniscience, and perfect goodness with the existence of evil, leaving fideism (faith without rational j
- **Adversity-as-Exercise Argument (Seneca)** (`argument_adversity_exercise_seneca_g8h9i0j1`) — _explicit_premise_conclusion_ × 16 premises → Under divine providence, apparent evils that befall good men are not genuine harms but beneficent exercises (exercitationes) assigned by God to actualize and demonstrate virtue, such that no bad thing
- **Freedom of Indifference** (`argument_freedom_of_indifference_dab82dcc`) — _explicit_premise_conclusion_ × 14 premises → Freedom of indifference, as the paradigm libertarian position requiring categorical alternative possibilities under identical conditions, faces a fundamental dilemma: if the choice is determined by pr
- **Origen's De Principiis Argument for Free Will** (`argument_origens_de_principiis_argument_for_free_will_93d043fc`) — _explicit_premise_conclusion_ × 13 premises → Therefore, autexousion (αὐτεξούσιον) is an inalienable, metaphysically fundamental property of all rational creatures, grounding divine justice, the meaningfulness of Scripture, the possibility of uni
- **Deliberate Choice (Prohairesis) Analysis Argument** (`argument_deliberate_choice_analysis_aristotle_h8i9j0k1`) — _explicit_premise_conclusion_ × 12 premises → Prohairesis is the specific locus of rational agency in human beings, constituted by deliberative desire for means within our power, and thereby serves as the foundation for moral responsibility and v
- **John Chrysostom's Homiletic Argument for Free Will** (`argument_john_chrysostoms_homiletic_argument_for_free_will_ea97cb61`) — _explicit_premise_conclusion_ × 12 premises → Human beings possess autexousion (self-determination) such that moral choices are genuinely voluntary, not determined by fate or necessity, and this free will is compatible with divine providence, gra
- **Pre-established Harmony** (`argument_preestablished_harmony_957f794d`) — _explicit_premise_conclusion_ × 12 premises → Human freedom is genuine (consisting in rational spontaneity and contingent sourcehood) and compatible with complete pre-determination of all volitions in the complete individual concept, because free
- **Qumran Predestinarian Argument (Two Spirits)** (`argument_qumran_predestination_c3d4e5f6`) — _explicit_premise_conclusion_ × 12 premises → The Treatise of the Two Spirits presents a cosmological dualism in which God predestines every human being to either truth or injustice through creation and assignment to one of two spirits, thereby g
- **Scotus's Voluntarism** (`argument_scotuss_voluntarism_501f1bf6`) — _explicit_premise_conclusion_ × 12 premises → Moral responsibility requires that the will, not the intellect, has ultimate control over human action.
- **Conatus Doctrine** (`argument_conatus_doctrine_1588d13c`) — _explicit_premise_conclusion_ × 11 premises → Human freedom is not libertarian indifference but compatibilist self-determination through reason: the human being is most free when acting from adequate ideas according to the necessity of its own ra

## Top 10 newly structured modern scholarly positions
- **Discovery of the will from Aristotle to Augustine** (`scholar_position_kahn_will_emerges_seneca_epictetus`) — _explicit_premise_conclusion_ × 8 premises → The concept of 'will' as an independent psychological faculty, culminating in the Augustinian synthesis, emerged through a developmental trajectory from Aristotle's fragmented volitional concepts thro
- **Modern libertarian free will** (`scholar_position_kane_libertarian_self_forming`) — _explicit_premise_conclusion_ × 8 premises → Libertarian incompatibilism can be defended without appeal to obscure or mysterious agency through the notion of self-forming actions (SFAs).
- **Justin Martyr and Middle Platonism** (`scholar_position_andresen_justin_middle_platonist`) — _explicit_premise_conclusion_ × 7 premises → Justin Martyr's doctrine of the Logos and of human autonomy is substantially shaped by his Middle Platonic philosophical formation, and both his theological construction and his apologetic strategy ar
- **Dihle: Greek philosophical theology from Plato and Aristotle onward did not conceive of** (`scholarly_argument_dihle_greek_philosophical_theology_a_0`) — _explicit_premise_conclusion_ × 7 premises → Greek philosophical theology from Plato and Aristotle onward did not conceive of divine will as arbitrary or unpredictable intention; rather, divine activity manifests perfect rationality, order, and 
- **Emergence of will as distinct faculty** (`scholar_position_dihle_will_christian_innovation`) — _explicit_premise_conclusion_ × 6 premises → The concept of will as a distinct, autonomous faculty of the soul, irreducible to reason and desire and bearing independent moral-theological accountability, emerges principally with Augustine and the
- **Origen's relation to Platonism** (`scholar_position_edwards_origen_anti_platonist`) — _explicit_premise_conclusion_ × 6 premises → The standard 'Origen-as-Platonist' reading is unwarranted; Origen's philosophy is fundamentally anti-Platonist in its anthropological foundations and programmatic intent.
- **Origin of the notion of free will** (`scholar_position_frede_will_originates_epictetus`) — _explicit_premise_conclusion_ × 6 premises → The notion of 'free will' as a distinct philosophical concept originates with the Stoic Epictetus, was transmitted through late Platonism to Origen, and was substantially adopted by Augustine from thi
- **Stoic theory of action and psychology** (`scholar_position_inwood_stoic_action_theory`) — _explicit_premise_conclusion_ × 6 premises → Stoic action is generated through a unified intellectualist psychology in which rational assent (synkatathesis) to impression (phantasia) constitutes the necessary and sufficient condition for impulse
- **Early Christian philosophical engagement with Greek thought** (`scholar_position_karamanolis_early_christian_engagement`) — _explicit_premise_conclusion_ × 6 premises → Early Christian thinkers of the 2nd-4th centuries (Justin, Origen, the Cappadocians) should be read as philosophers engaged in substantive philosophical debate with Greek philosophical traditions, not
- **Origin of free will problem** (`scholar_position_long_sedley_epicurus_first_freewill`) — _explicit_premise_conclusion_ × 6 premises → Epicurus was the first ancient thinker to recognize explicitly the 'Free Will Question' as an incompatibilist problem and to propose the atomic swerve as a physical solution to atomic determinism.

## Flagged for review
- `argument_democritean_atomistic_determinism_c52067ec` — kimi-error: Expecting ',' delimiter: line 9 column 15294 (char 15543)
- `argument_parmenides_necessity_argument_4e8e0f34` — kimi-error: Expecting ',' delimiter: line 9 column 15309 (char 15516)
- `argument_the_master_argument_kurieuon_logos_355f4d3f` — kimi-error: Expecting value: line 9 column 15326 (char 15489)

## Scholar engagement map (new `created_by` edges from this pass)

Each modern scholarly position is now linked to its author person node:

- **person_bobzien_susanne_contemporary**:
  - `scholar_position_bobzien_no_free_will_problem_ancients`
- **person_frankfurt_harry_1929_2023**:
  - `scholar_position_frankfurt_pap_false`
- **person_frede_michael_1940_2007**:
  - `scholar_position_frede_will_originates_epictetus`
- **person_inwood_brad_contemporary**:
  - `scholar_position_inwood_stoic_action_theory`
- **person_kane_robert_1938_2022**:
  - `scholar_position_kane_libertarian_self_forming`
- **person_salles_ricardo_contemporary**:
  - `scholar_position_salles_chrysippus_frankfurt_style`
- **person_sorabji_richard_contemporary**:
  - `scholar_position_sorabji_aristotle_indeterminist`
- **person_strawson_galen_contemporary**:
  - `scholar_position_strawson_basic_argument`
- **person_van_inwagen_peter_9s0t1u2v**:
  - `scholar_position_van_inwagen_consequence_argument`
- **scholar_andresen_carl**:
  - `scholar_position_andresen_justin_middle_platonist`
- **scholar_brennan_tad**:
  - `scholar_position_brennan_stoic_emotions_beliefs`
- **scholar_dihle_albrecht**:
  - `scholar_position_dihle_will_christian_innovation`
  - `scholarly_argument_dihle_absence_of_will_as_arbitrary_i_2`
  - `scholarly_argument_dihle_greek_philosophical_theology_a_0`
  - `scholarly_argument_dihle_greek_philosophical_theology_v_0`
  - `scholarly_argument_dihle_jewish_and_christian_conceptio_1`
  - `scholarly_argument_dihle_monotheistic_convergence_with__3`
  - `scholarly_argument_dihle_prayer_and_divine_immutability_2`
  - `scholarly_argument_dihle_prayer_and_divine_rationality_1`
- **scholar_donini_p**:
  - `scholarly_argument_donini_aristotle_s_principle_of_corre_0`
  - `scholarly_argument_donini_aristotle_s_response_to_determ_1`
  - `scholarly_argument_donini_status_of_future_contingents_a_2`
- **scholar_edwards_mark**:
  - `scholar_position_edwards_origen_anti_platonist`
- **scholar_faure_r**:
  - `scholarly_argument_faure_cyclical_vs_linear_time_in_gre_0`
  - `scholarly_argument_faure_g_del_s_relativity_based_chall_2`
  - `scholarly_argument_faure_linguistic_categories_and_temp_3`
  - `scholarly_argument_faure_time_and_eternity_1`
- **scholar_furley_david**:
  - `scholar_position_furley_epicurus_swerve_indirect`
- **scholar_gill_christopher**:
  - `scholar_position_gill_structured_self_stoicism`
- **scholar_hadot_pierre**:
  - `scholar_position_hadot_philosophy_as_practice`
- **scholar_hankinson_rj**:
  - `scholar_position_hankinson_stoic_causation_compatibilist`
- **scholar_kahn_charles**:
  - `scholar_position_kahn_will_emerges_seneca_epictetus`
- **scholar_karamanolis_george**:
  - `scholar_position_karamanolis_early_christian_engagement`
- **scholar_long_anthony**:
  - `scholar_position_long_sedley_epicurus_first_freewill`
- **scholar_rist_john**:
  - `scholar_position_rist_augustine_platonized_christian`
- **scholar_sharples_robert**:
  - `scholar_position_sharples_chrysippus_early_compatibilist`

## Idempotency

Re-running `database/scripts/enrich_arguments.py` is a no-op: nodes with `metadata.structured_v2 = 'true'` are skipped unless `--force` is passed. The script writes the prior unstructured `premises` (flat-string array) to `metadata.legacy_premises` to preserve curatorial history. Edges are created only if a duplicate doesn't already exist.

## Method

1. For each argument node, fetched all primary-source neighbors (passage/work/quote via `source_for`, `evidenced_by`, `attested_in`, `cites_primary_source`, `grounded_in`, `discusses`, `contains`, `part_of`) and all linked scholarly positions.
2. Sent the description + indexed primary-source texts to Kimi K2.6 (Fireworks, JSON-schema response format with strict enum for `argument_form`).
3. Validated every premise: if marked `direct` or `doxographical`, must cite a valid primary-source index; otherwise marked `reconstructed` (with optional scholarly source).
4. Materialized indices into KG node IDs and applied via JSONB merge.
5. Linked modern scholarly positions to their author person node via new `created_by` edges (`provenance: structured_v2_linker`).
