"""Decisions — withdraw the 29 contaminated ``pub_fedou_2026_*`` bulletin rows.

Evidence (read node by node on 2026-09-24):

* every row's ``label``/``metadata.title`` names a book reviewed in a
  bibliographic bulletin (Dutch Reformation, Levinas, church musicians, the
  1924 Poincaré–Cerretti agreement, "Ouvrages analysés", "Pages de fin", ...);
* every row's ``description`` and ``metadata.abstract`` is one and the same
  text about Origen's *De oratione* in D. Vigne's edition — 28 in French
  ("Le Traité sur la prière d'Origène, désormais accessible dans l'édition
  critique et la traduction de Daniel Vigne ..."; "Origen's Treatise on
  Prayer, now available in Daniel Vigne's critical edition and translation"),
  one in Spanish ("El Tratado sobre la oración de Orígenes ...");
* the author "Michel Fédou" comes from the OpenAlex record of the bulletin,
  not from the reviewed books (Barth, Maritain, Teilhard, Taguieff ... are
  not by Fédou);
* each row carries exactly two edges, ``discusses →
  concept_autexousion_christian_freedom_u1v2w3x4`` and ``discusses →
  person_origen_alexandria_185_254ce_s9t0u1v2``, derived from the wrong
  abstract, not from the reviewed book.

The cold audit (data/audit/2026-08-17_cold_audit_sol.md, H-01) already judged
these rows "Incorrect" and tagged them ``integrity_status =
origenality_bibliographic_span_contamination`` but left the public text and
the edges in place. No row can be repaired without reading the bulletin
itself (not reachable from this environment), so the rows are withdrawn; the
full records are kept in data/audit/2026-09-24_fedou_bulletin_withdrawal_quarantine.jsonl.
"""

REQUIRED_INTEGRITY_STATUS = "origenality_bibliographic_span_contamination"
ABSTRACT_MARKERS = (
    "Le Traité sur la prière d’Origène",
    "El Tratado sobre la oración de Orígenes",
)
ALLOWED_EDGE_TARGETS = {
    "concept_autexousion_christian_freedom_u1v2w3x4",
    "person_origen_alexandria_185_254ce_s9t0u1v2",
}

WITHDRAW = [
    # title: "Adam M. F., Time and Tradition. Temporal Thinking in Ecclesiastes in the Context of Emerging Apocalypticism an"
    "pub_fedou_2026_adam_time_and_tradition_temporal_thinking_in_ecclesiastes_in_the",
    # title: "augustin G. (dir.), Gott in die Mitt e. Damit Glauben gelingen kann. Für Kurt Kardinal Koch, Freiburg, Herder,"
    "pub_fedou_2026_augustin_dir_gott_in_die_mitt_damit_glauben_gelingen_kann_fur_ku",
    # title: "B aümer B. S., The Light In-Between . A journey of Recognition, New Delhi, Aryan Books International, 2025, 37"
    "pub_fedou_2026_aumer_the_light_in_between_journey_of_recognition_new_delhi_arya",
    # title: "L aurens S., Influences et délires d’influences . De la perception à l’interprétation, coll. Travaux de scienc"
    "pub_fedou_2026_aurens_influences_et_delires_influences_de_la_perception_interpr",
    # title: "Barth K., Destin et idée dans la théologie, préf. V. Holzer, postf. C. Chalamet, Paris, Ad Solem, 2024, 128 p."
    "pub_fedou_2026_barth_destin_et_idee_dans_la_theologie_pref_holzer_postf_chalame",
    # title: "Capelle-Dumont P., Emmanuel Levinas et le christianisme, coll. Philosophie et Théologie, Paris, Cerf, 2025, 16"
    "pub_fedou_2026_capelle_dumont_emmanuel_levinas_et_le_christianisme_coll_philoso",
    # title: "Collectif, Le centenaire de l’accord Poincaré-Cerretti de 1924. Actes des colloques de Rome et Paris, 21 mai 2"
    "pub_fedou_2026_collectif_le_centenaire_de_accord_poincare_cerretti_de_1924_acte",
    # title: "Dard O., Dumons B. (dir.), L’ordre moral (1873-1877). Royalisme, catholicisme et conservatisme, Paris, Cerf, 2"
    "pub_fedou_2026_dard_dumons_dir_ordre_moral_1873_1877_royalisme_catholicisme_et",
    # title: "E dart J.-B., Le diable dans ses œuvres . Comprendre l’action invisible du mal et s’en libérer, Perpignan, Art"
    "pub_fedou_2026_dart_le_diable_dans_ses_uvres_comprendre_action_invisible_du_mal",
    # title: "davy-Rigaux a., dompnier B., Gomis s. (dir.), Des musiciens au service des églises (xviie et xviiie siècles). "
    "pub_fedou_2026_davy_rigaux_dompnier_gomis_dir_des_musiciens_au_service_des_egli",
    # title: "de V illeneuve C., Aimer pour rien. La forme intellectuelle de l’amour pur, xii-xx e siècle, Paris, Cerf, 2025"
    "pub_fedou_2026_de_illeneuve_aimer_pour_rien_la_forme_intellectuelle_de_amour_pu",
    # title: "de Segni L., Misère de la condition humaine, intro., trad. et commentaires O. Hanne, coll. La roue à livres 10"
    "pub_fedou_2026_de_segni_misere_de_la_condition_humaine_intro_trad_et_commentair",
    # title: "Delsol C., La tragédie migratoire et la chute des empires. Saint Augustin et nous, Paris, Odile Jacob, 2026, 2"
    "pub_fedou_2026_delsol_la_tragedie_migratoire_et_la_chute_des_empires_saint_augu",
    # title: "V endé Y. (dir.), Souffle, méditation et lecture . À la recherche de résonances, postf. P. Rodrigues, Sion, Pa"
    "pub_fedou_2026_ende_dir_souffle_meditation_et_lecture_la_recherche_de_resonance",
    # title: "Falque E., Nouvelle lettre sur l’apologétique, Paris, Cerf, 2025, 150 p., 16,00 €. ISBN 9782204172783."
    "pub_fedou_2026_falque_nouvelle_lettre_sur_apologetique_paris_cerf_2025_150_16_0",
    # title: "hénin E., salvador x.-l., vermeren P. (dir.), Face à l’obscurantisme woke, Paris, puf, 2025, 454 p., 22,00 €. "
    "pub_fedou_2026_henin_salvador_vermeren_dir_face_obscurantisme_woke_paris_puf_20",
    # title: "Huguenin F., Le Je & le Nous. Une histoire de la pensée politique des origines à nos jours, Paris, Cerf, 2025,"
    "pub_fedou_2026_huguenin_le_je_le_nous_une_histoire_de_la_pensee_politique_des_o",
    # title: "P icard J., Apparition / Disparition. Le statut de la Résurrection dans la théologie de Hans Urs von Balthasar"
    "pub_fedou_2026_icard_apparition_disparition_le_statut_de_la_resurrection_dans_l",
    # title: "Karakash I., Marc : subtilité et surprises du plus ancien des évangiles, préf. F. Vouga, coll. Au fil des Écri"
    "pub_fedou_2026_karakash_marc_subtilite_et_surprises_du_plus_ancien_des_evangile",
    # title: "Kooi C., La Réforme aux Pays-Bas,1500-1620, coll. Bibliothèque de la Revue d’histoire ecclésiastique 120, Turn"
    "pub_fedou_2026_kooi_la_reforme_aux_pays_bas_1500_1620_coll_bibliotheque_de_la_r",
    # title: "Maritain J., Maritain R., 30, Fifth Avenue. Carnets de guerre, Tome i : 1939-1942, éd. D. et R. Mougel, M. Fou"
    "pub_fedou_2026_maritain_maritain_30_fifth_avenue_carnets_de_guerre_tome_1939_19",
    # title: "Ouvrages analysés"
    "pub_fedou_2026_ouvrages_analyses",
    # title: "Pages de fin"
    "pub_fedou_2026_pages_de_fin",
    # title: "Richards E.R., James R., Trompés par notre individualisme, Saint-Légier (Suisse), HET-PRO, 2025, 368p., 25,00€"
    "pub_fedou_2026_richards_james_trompes_par_notre_individualisme_saint_legier_sui",
    # title: "Siret V., Nadeau-Lacour T. (dir.), Marie Guyart de l’Incarnation : « autrement moderne ». Actes du colloque de"
    "pub_fedou_2026_siret_nadeau_lacour_dir_marie_guyart_de_incarnation_autrement_mo",
    # title: "Taguieff P.-A., Du racisme en général et du racisme anti-Blancs en particulier, Saint-Martin-de-Londres, H&O, "
    "pub_fedou_2026_taguieff_du_racisme_en_general_et_du_racisme_anti_blancs_en_part",
    # title: "Teilhard de Chardin P., Le Milieu divin, intro. et notes inédites F. Euvé, préf. A. Leproux, Paris, Éd. Loyola"
    "pub_fedou_2026_teilhard_de_chardin_le_milieu_divin_intro_et_notes_inedites_euve",
    # title: "Trublet J., Les rêves dans l’Ancien Testament, coll. Cahiers Évangile 212, Paris, Cerf - Service biblique cath"
    "pub_fedou_2026_trublet_les_reves_dans_ancien_testament_coll_cahiers_evangile_21",
    # title: "J unod É. (dir.), L’affaire Origène , coll. Les Pères dans la foi 113, Paris, Migne - Cerf, 2025, 346 p., 25,0"
    "pub_fedou_2026_unod_dir_affaire_origene_coll_les_peres_dans_la_foi_113_paris_mi",
]
