"""Item-by-item gold repairs. Existing exact identities are not fuzzy aliases.

Each record is (case, old channel, old id, new channel, exact target id).
The apply report binds target labels and hashes, and preserves all passage gold.
"""

# The full Christian-autexousion node label explicitly matches the abbreviated id.
AUTEXOUSION = "concept_autexousion_christian_freedom_u1v2w3x4"
REPAIRS = [
    ("q006", "entity", "concept_autexousion_christian", "entity", AUTEXOUSION),
    # This exact Cicero id already exists as type=work, not as a non-work entity.
    (
        "q020",
        "entity",
        "work_de_fato_cicero_44bce_b9c4e5d2",
        "work",
        "work_de_fato_cicero_44bce_b9c4e5d2",
    ),
    ("q026", "entity", "concept_autexousion_christian", "entity", AUTEXOUSION),
    # Gellius VII.2 and Cicero De Fato are both existing works.
    ("q028", "entity", "work_gellius_na_vii_2", "work", "work_gellius_na_vii_2"),
    (
        "q028",
        "entity",
        "work_de_fato_cicero_44bce_b9c4e5d2",
        "work",
        "work_de_fato_cicero_44bce_b9c4e5d2",
    ),
    (
        "q029",
        "entity",
        "work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",
        "work",
        "work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",
    ),
    ("r001", "entity", "concept_autexousion_christian", "entity", AUTEXOUSION),
    # Justin work metadata resolves respectively to tlg0645.tlg001 and tlg002.
    ("r001", "work", "work_justin_1apol", "work", "work_justin_first_apology"),
    ("r001", "work", "work_justin_2apol", "work", "work_justin_second_apology_sc507"),
    # The anti-astrological dossier is Comm. Gen. III / Philocalia 23, NOT a
    # second textual witness of De Princ. III.1. The query is corrected below.
    (
        "r002",
        "entity",
        "argument_origen_anti_astrology_de_princ",
        "entity",
        "argument_origen_anti_astrological",
    ),
    ("r003", "entity", "work_ben_sira_sirach", "work", "work_sirach_a3b4c5d6"),
    ("r004", "entity", "person_tertullian", "entity", "person_tertullian_d220"),
    ("r004", "entity", "work_tertullian_de_anima", "work", "work_tertullian_de_anima"),
    (
        "r005",
        "entity",
        "person_methodius_olympus",
        "entity",
        "person_methodius_olympus_d311",
    ),
    (
        "r005",
        "entity",
        "work_methodius_de_libero_arbitrio",
        "work",
        "work_methodius_de_libero_arbitrio",
    ),
    # Recognitiones is the Rufinus Latin transmission, distinct from Homiliae.
    (
        "r006",
        "entity",
        "work_pseudo_clementine_recognitions",
        "work",
        "work_ps_clement_recognitiones",
    ),
    ("r007", "entity", "work_clement_stromateis", "work", "work_clement_stromateis"),
    # VI.8 (freedom of the One), not the similarly named IV.8 (descent of soul).
    (
        "r008",
        "entity",
        "work_plotinus_enneads_vi_8",
        "work",
        "work_plotinus_ennead_vi_8_d8b9c5a4",
    ),
    ("r009", "entity", "concept_autexousion_christian", "entity", AUTEXOUSION),
    (
        "r010",
        "entity",
        "work_1qs_community_rule",
        "work",
        "work_dss_community_rule_e7f8g9h0",
    ),
    (
        "r011",
        "entity",
        "concept_eternity_boethius",
        "entity",
        "concept_aeternitas_boethius_g2h3i4j5",
    ),
    (
        "r011",
        "entity",
        "argument_eternity_solution_boethius",
        "entity",
        "argument_boethian_solution_divine_eternity_k1l2m3n4",
    ),
    (
        "r011",
        "work",
        "work_boethius_consolatio_philosophiae",
        "work",
        "work_consolatio_philosophiae_boethius_524ce_f1g2h3i4",
    ),
    ("r012", "entity", "work_de_libero_arbitrio", "work", "work_de_libero_arbitrio"),
    ("r013", "entity", "person_irenaeus_lyons", "entity", "person_irenaeus_d202"),
    # The question specifically asks IV.37–39; use the existing Book IV work.
    (
        "r013",
        "entity",
        "work_irenaeus_adversus_haereses",
        "work",
        "work_irenaeus_adversus_haereses_book4",
    ),
    # The missing work is added from pinned Perseus metadata + Romans 9 TEI,
    # not created as a fictitious alias just to satisfy the evaluator.
    (
        "r014",
        "entity",
        "work_pauline_epistle_romans",
        "work",
        "work_pauline_epistle_romans",
    ),
    (
        "r015",
        "entity",
        "person_maximus_confessor",
        "entity",
        "person_maximus_confessor_d662",
    ),
    (
        "r015",
        "entity",
        "work_maximus_disputatio_cum_pyrrho",
        "work",
        "work_maximus_disp_pyrrho",
    ),
]
ORIGEN_QUERY = (
    "Compare Origen's responsibility argument in De Principiis III.1.5–6 with the "
    "anti-astrological argument from Commentary on Genesis III preserved in Philocalia 23.1. "
    "Use the available translations, distinguish the two works and their transmission, "
    "and do not present these French corpus translations as Latin or Greek witnesses."
)

# Exact French corpus passage 481e3e44... says that determinism excuses human
# wrongdoers and imputes their wrongdoing to God. The old gold reversed this.
CLAIM_CORRECTIONS = {
    "In the Greek catena witness (Philocalia 23), Origen argues that astral determinism would abolish divine judgment, rewards and punishments, and render faith and Christ's coming pointless.": "In the Commentary on Genesis excerpt preserved in Philocalia 23, Origen argues that astral determinism would abolish divine judgment, rewards and punishments, and render faith and Christ's coming pointless.",
    "Origen reduces astrological fatalism to absurdity: it would make God, not the stars, blameless for evil deeds while crediting the stars even with Christ's powers.": "Origen argues that astrological fatalism excuses human wrongdoers while imputing responsibility for their actions to God, and credits the stars rather than God with Christ's powers.",
}
