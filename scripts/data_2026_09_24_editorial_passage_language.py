"""Decisions — English editorial passages declared as Greek or Latin.

Source: data/quality/jev_2026_09_24/c1_passage_concepts/queue_quality_flags.csv
("mostly modern-language text": passage_arist_en_3_2, _3_3, _3_12, p 0.72-0.83) and
queue_language_mismatch.csv (meta=grc, Jev says not Greek: passage_arist_en_3_2/3/4/12), extended
to every passage whose own metadata already says it is an editorial product
(passage_role = editorial_synthesis or summary) but whose metadata.language is grc or lat.

Each of the 46 nodes below was read on 2026-09-24: all are English prose written by an editor
(headings such as "ARISTOTLE ON ...", "Opening section where Augustine ...", "A key passage on
moral psychology. Marcus argues ..."), quoting short Greek or Latin phrases. metadata.language
describes the language of the text a reader gets, so it becomes "eng"; the quoted language is
kept in metadata.quoted_language and the old value in metadata.language_before_2026_09_24.
The texts themselves are not touched.

Not included: passage_arist_en_3_5 (already "mul" and self-labelled "EDITORIAL SYNTHESIS — NOT A
PRIMARY-SOURCE TRANSCRIPT").
"""

PASSAGES = {
    # Aristotle, EN III — English chapter syntheses with Greek excerpts
    "passage_arist_en_3_1": "grc", "passage_arist_en_3_2": "grc", "passage_arist_en_3_3": "grc",
    "passage_arist_en_3_4": "grc", "passage_arist_en_3_6": "grc", "passage_arist_en_3_7": "grc",
    "passage_arist_en_3_8": "grc", "passage_arist_en_3_9": "grc", "passage_arist_en_3_10": "grc",
    "passage_arist_en_3_11": "grc", "passage_arist_en_3_12": "grc",
    # Augustine, De gratia et libero arbitrio I — English summaries quoting the Latin
    **{f"passage_aug_gla_1_{i}": "lat" for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 17, 18,
                                                  19, 20, 22, 23, 24)},
    # Epictetus — English outlines of Greek key phrases
    "passage_epict_159": "grc", "passage_epict_160": "grc", "passage_epict_181": "grc",
    # Justin, 1 Apology 43-44 — English syntheses
    "passage_justin_1apol_43": "grc", "passage_justin_1apol_44": "grc",
    # Lucretius II — English summaries quoting the Latin
    "passage_lucretius_2_250": "lat", "passage_lucretius_2_275": "lat",
    # Marcus Aurelius — English syntheses quoting single Greek terms
    "passage_ma_med_11_16": "grc", "passage_ma_med_4_39": "grc", "passage_ma_med_5_26": "grc",
    "passage_ma_med_5_8": "grc", "passage_ma_med_6_41": "grc", "passage_ma_med_7_16": "grc",
    "passage_ma_med_8_7": "grc",
    # Plotinus — English synthesis quoting the Greek
    "passage_plotinus_enn_4_4_30": "grc",
}
