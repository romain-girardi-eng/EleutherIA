#!/usr/bin/env python3
"""Data for ``apply_2026_08_16_deep_audit_bibliographic.py`` (wave 2).

Wave 1 (``*_deep_audit_structural``) fixed everything provable from the data
itself. This wave carries the items that required an external bibliographic
check. Every entry below cites the source that settles it; anything that came
back UNVERIFIED is deliberately left alone and recorded as such.

Two results overturned a wave-1 hypothesis and are worth stating plainly:

* ``Bobichon 2003`` was flagged in the findings file as a "near-certain merge".
  It is NOT. The critical edition (Paradosis 47/1-2, Fribourg, 1125 pp., two
  physical volumes of ONE edition) and « Œuvres de Justin martyr : le manuscrit
  Loan 36/13 de la British Library », *Scriptorium* 57/2 (2003), 157-172, are
  different publications. No merge. (Persée; the author's own listing dates the
  Scriptorium fascicle 2004, Persée gives 2003 — 2003 is used.)
* ``La causalité humaine`` is a BOOK by Isabelle Koch (Classiques Garnier,
  2019, 533 pp., ISBN 978-2-406-08559-7), and Gweltaz Guyomarc'h wrote the
  REVIEW of it (*Philosophie antique* 20, 2020, 287-290). The KG had conflated
  reviewer with author — the same failure mode as the D'Jeranian/Gourinat case.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Ids whose embedded surname contradicts the scholar the node is actually
# attributed to. The rename is DERIVED at run time from the node's own
# created_by / authored_by edge (already verified correct), so it cannot drift;
# this table only declares the surname substitution and its source.
#
# Only the arguments that hang off the misattributed publication are renamed.
# The five genuine Gourinat arguments (advanced_in pub_gourinat_2005_prohairesis,
# created_by scholar_gourinat_jean_baptiste) keep their ids.
SURNAME_FIXES: dict[str, tuple[str, str]] = {
    # J. Philip Hyatt, "The View of Man in the Qumran 'Hodayot'", NTS 2/4 (May
    # 1956) 276-284. Frank Moore Cross is not the author.
    # https://www.cambridge.org/core/journals/new-testament-studies/article/abs/view-of-man-in-the-qumran-hodayot/432B94B1CB7D8BA20220BDAA773B5109
    "scholar_hyatt_jp": ("cross", "hyatt"),
    # Olivier D'Jeranian, « Responsabilité morale et destin : une solution
    # possible chez Épictète à l'objection de Cicéron (De fato 39-45) ».
    # https://www.academia.edu/36278404/ — author certain; venue/year UNVERIFIED,
    # so no year is assigned to the id (see YEAR_BACKFILL, which omits it).
    "scholar_djeranian_o": ("gourinat", "djeranian"),
    # Isabelle Koch, La Causalité humaine. Sur le De fato d'Alexandre
    # d'Aphrodise, Classiques Garnier, 2019. Guyomarc'h wrote the review.
    # https://classiques-garnier.com/la-causalite-humaine-sur-le-de-fato-d-alexandre-d-aphrodise-bibliographie.html
    "scholar_koch_i": ("guyomarc_h", "koch"),
    # SC 312 (Cerf 1984) title page: « COMPLÉMENTS ET INDEX par Henri CROUZEL et
    # Manlio SIMONETTI »; the Avant-propos assigns the « compléments sur la
    # tradition manuscrite » to Simonetti and the Addenda/Corrigenda + indexes to
    # Crouzel. Verified verbatim in the local volume at
    # 04_Littérature_secondaire/10_Ouvrages_reference/(Sources Chrétiennes 312)….md
    "scholar_simonetti_m": ("crouzel", "simonetti"),
}

# Slug normalisation only: the publication id said "boysstones", the person node
# is scholar_boys_stones_g. Same scholar, no attribution change.
SLUG_FIXES: dict[str, str] = {
    "pub_boysstones_2007_middle_platonists": "pub_boys_stones_2007_middle_platonists",
}


# ---------------------------------------------------------------------------
# 2. Ids whose embedded year is wrong. Renaming the id, metadata.year is right.
# (old_id, new_id, source)
ID_YEAR_FIXES: list[tuple[str, str, str]] = [
    # Alfons Fürst (ed.), Perspectives on Origen and the History of his
    # Reception, Adamantiana 21, Aschendorff 2021. NB a DIFFERENT Fürst volume
    # is Adamantiana 13/14 (2019) — pub_furst_2019_concepts_origenism_ad13 is
    # deliberately left untouched.
    (
        "pub_furst_2019_perspectives_origen_ad21",
        "pub_furst_2021_perspectives_origen_ad21",
        "Adamantiana 21, Aschendorff 2021, ISBN 978-3-402-13752-9 (degruyterbrill.com/document/doi/10.1515/zac-2023-0033)",
    ),
    # Barclay & Gathercole (eds.), Divine and Human Agency in Paul and his
    # Cultural Environment, LNTS 335, T&T Clark 2006. The 2008 paperback
    # reissue is the source of the 2007/2008 noise. The "Introduction" is a
    # chapter of the 2006 volume.
    (
        "scholarly_work_barclay_2007_introduction",
        "scholarly_work_barclay_2006_introduction",
        "LNTS 335, T&T Clark 2006; 2008 is the paperback reissue",
    ),
    # Bonaiuti (trans. La Piana), "The Genesis of St. Augustine's Idea of
    # Original Sin", HTR X/2 (April 1917) 159-175.
    (
        "scholarly_work_bonaiuti_1924_the_genesis_of_st_augustine_s_idea_of_or",
        "scholarly_work_bonaiuti_1917_the_genesis_of_st_augustine_s_idea_of_or",
        "HTR 10/2 (1917) 159-175, jstor.org/stable/1507550",
    ),
    # Wolfson, "Philo on Free Will: And the Historical Influence of His View",
    # HTR 35/2 (1942) 131-169. 1947 is his Philo monograph, a different work.
    (
        "scholarly_work_wolfson_1947_philo_on_free_will_and_the_historical_in",
        "scholarly_work_wolfson_1942_philo_on_free_will_and_the_historical_in",
        "HTR 35/2 (1942) 131-169, DOI 10.1017/S001781600000523X",
    ),
    # Salles, The Stoics on Determinism and Compatibilism, Ashgate 2005.
    # 2008 corresponds to no edition; 2017 is the Routledge reissue.
    (
        "work_salles_stoics_determinism_2008",
        "work_salles_stoics_determinism_2005",
        "Ashgate 2005, ISBN 0754639762 (bmcr.brynmawr.edu/2007/2007.03.02)",
    ),
    # Koch, La Causalité humaine, Classiques Garnier 2019 (the id said 2015).
    # Renamed for the year here; the surname is fixed by SURNAME_FIXES.
    (
        "scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale",
        "scholarly_work_koch_2019_la_causalit_humaine_sur_le_de_fato_d_ale",
        "Classiques Garnier 2019, 533 pp., ISBN 978-2-406-08559-7",
    ),
]


# ---------------------------------------------------------------------------
# 3. metadata.year corrections where the ID was right and the metadata wrong.
META_YEAR_FIXES: dict[str, tuple[int, int, str]] = {
    # Craig, Divine Foreknowledge and Human Freedom, Brill's Studies in
    # Intellectual History 19, Leiden: E.J. Brill, 1991. Copyright page reads
    # "Copyright 1991 by E.J. Brill". Some retailers list 1990 in error.
    "pub_craig_1991_divine_foreknowledge_human_freedom": (
        1990,
        1991,
        "Brill 1991, brill.com/display/title/2069",
    ),
}


# ---------------------------------------------------------------------------
# 4. Ids carrying a `_0_` year placeholder, now resolved.
# (old_id, new_id, year, source)
YEAR_BACKFILL: list[tuple[str, str, int, str]] = [
    # Dettwiler, Kaestli & Marguerat (dir.), Paul, une théologie en construction,
    # Le Monde de la Bible 51, Labor et Fides 2004. NB Dettwiler is co-EDITOR.
    (
        "scholarly_work_dettwiler_0_une_th_ologie_en_construction",
        "scholarly_work_dettwiler_2004_une_th_ologie_en_construction",
        2004,
        "Labor et Fides 2004, Le Monde de la Bible 51 (persee.fr rhpr 2006)",
    ),
    # Hendriksen, NT Commentary: Exposition of Paul's Epistle to the Romans,
    # combined ch. 1-16 edition, Baker 1981, ISBN 0-8010-4265-8 (vol. 1, 1980).
    (
        "scholarly_work_hendriksen_0_new_testament_commentary_romans",
        "scholarly_work_hendriksen_1981_new_testament_commentary_romans",
        1981,
        "Baker Book House 1981 (combined edition), ISBN 0-8010-4265-8",
    ),
    # Luther H. Martin, "Josephus' Use of Heimarmene in the Jewish Antiquities
    # XIII, 171-3", Numen 28/2 (1981) 127-137.
    (
        "scholarly_work_martin_0_josephus_use_of_heimarmene_in_the_jewish",
        "scholarly_work_martin_1981_josephus_use_of_heimarmene_in_the_jewish",
        1981,
        "Numen 28/2 (1981) 127-137",
    ),
    # Michon, « Je ne fais pas ce que je veux, mais je fais ce que je hais »,
    # in Lefebvre & Tordesillas (éds.), Faiblesse de la volonté et maîtrise de
    # soi, PUR 2009, 175-189.
    (
        "scholarly_work_michon_0_je_ne_fais_pas_ce_que_je_veux_mais_je_fa",
        "scholarly_work_michon_2009_je_ne_fais_pas_ce_que_je_veux_mais_je_fa",
        2009,
        "PUR, coll. Philosophica, 2009 (pur-editions.fr/product/1624)",
    ),
    # Micah Currado, "Early Church Fathers on the Freedom of the Will and
    # Romans 9", Society of Evangelical Arminians, 14 Oct 2014. GREY LITERATURE
    # (web essay, not peer-reviewed) — flagged as such below.
    (
        "scholarly_work_currado_0_early_church_fathers_on_the_freedom_of_t",
        "scholarly_work_currado_2014_early_church_fathers_on_the_freedom_of_t",
        2014,
        "evangelicalarminians.org, 14 October 2014",
    ),
    # Beverly Roberts Gaventa, Romans: A Commentary, New Testament Library,
    # Westminster John Knox 2024, ISBN 978-0-664-22100-3.
    (
        "scholarly_work_gaventa_0_romans",
        "scholarly_work_gaventa_2024_romans",
        2024,
        "NTL, Westminster John Knox 2024, ISBN 978-0-664-22100-3",
    ),
]

# scholarly_work_gourinat_0_… is deliberately NOT year-backfilled: D'Jeranian's
# paper does not appear in his official publication list and has no traceable
# venue or year. It is renamed for the surname only, and flagged unpublished.
# scholarly_work_oropeza_0_… is likewise left without a year: the bibliography
# exists only as a self-posted Academia.edu document with no stated year.


# ---------------------------------------------------------------------------
# 5. Confirmed merges from the external check.
BIBLIOGRAPHIC_MERGES: list[dict] = [
    # Jewett, Romans: A Commentary, Hermeneia, Fortress 2007. "Hermeneia" is
    # only the series name — one book, two nodes.
    {
        "keep": "scholarly_work_jewett_2007_romans_a_commentary",
        "drop": "scholarly_work_jewett_2007_romans_a_commentary_hermeneia_series",
        "reason": "one book: Hermeneia is the series name (Fortress 2007, ISBN 978-0-8006-6084-0)",
    },
    # The two "Gaventa" section nodes are internal division headings of the 2024
    # NTL commentary, verified against its table of contents — not separate
    # publications.
    {
        "keep": "scholarly_work_gaventa_2024_romans",
        "drop": "scholarly_work_gaventa_0_romans_all_israel",
        "reason": "internal heading 'Romans 9:1-11:36: All Israel' of the 2024 NTL commentary, per its TOC",
    },
    {
        "keep": "scholarly_work_gaventa_2024_romans",
        "drop": "scholarly_work_gaventa_0_romans_christ_cosmos_and_consequences",
        "reason": "internal heading 'Romans 5:1-8:39: Christ, Cosmos, and Consequences' of the same commentary",
    },
]


# ---------------------------------------------------------------------------
# 6. Editor recorded as author. Boys-Stones' chapter appeared in a volume
# Sharples co-edited with Sorabji; he is not a co-author of the chapter.
# G. Boys-Stones, "'Middle' Platonists on Fate and Human Autonomy", ch. XXII in
# R.W. Sharples & R. Sorabji (eds.), Greek and Roman Philosophy 100 BC-200 AD,
# vol. II, BICS Suppl. 94 (2007) 431-448, DOI 10.1111/j.2041-5370.2007.tb02440.x
EDITOR_NOT_AUTHOR: list[tuple[str, str]] = [
    ("pub_boys_stones_2007_middle_platonists", "scholar_sharples_robert"),
]


# ---------------------------------------------------------------------------
# 7. Grey literature: not peer-reviewed scholarship. Flagged so confidence
# scoring and citation rendering can demote them.
GREY_LITERATURE: dict[str, str] = {
    "scholarly_work_currado_2014_early_church_fathers_on_the_freedom_of_t": (
        "Web essay posted on the Society of Evangelical Arminians site "
        "(evangelicalarminians.org, 14 October 2014); not peer-reviewed."
    ),
    "scholarly_work_oropeza_0_paul_within_judaism_bibliography": (
        "Self-posted Academia.edu document (id 41971697) with no publisher, "
        "journal or stated year; not indexed in any catalogue. Year deliberately "
        "left unassigned rather than inferred from the upload date."
    ),
    "scholarly_work_djeranian_0_responsabilit_morale_et_destin_une_r_pon": (
        "Does not appear in D'Jeranian's official publication list (41 entries, "
        "olivierdjeranian.fr); traceable only as an Academia.edu paper "
        "(id 36278404, posted c. March 2018). Treated as an unpublished paper: "
        "venue and year deliberately left unassigned."
    ),
}


# ---------------------------------------------------------------------------
# 8. Label corrections from the external check.
LABEL_FIXES: dict[str, tuple[str, str, str]] = {
    # The KG title said "une réponse possible"; the paper reads "une solution
    # possible … à l'objection de Cicéron".
    "scholarly_work_djeranian_0_responsabilit_morale_et_destin_une_r_pon": (
        "D'Jeranian — Responsabilité morale et destin : une réponse possible chez Épictète à l'objecti",
        "D'Jeranian — Responsabilité morale et destin : une solution possible chez Épictète "
        "à l'objection de Cicéron (De fato 39-45)",
        "academia.edu/36278404",
    ),
}
