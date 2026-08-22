"""Bobzien 1998/2001 disambiguation — two different works, one convention.

Romain's convention (2026-08-23, and already used by the argument_bobzien_2001_b1_*
family): **Bobzien 1998** = the Phronesis 43/2 article "The Inadvertent
Conception and Late Birth of the Free-Will Problem" (pp. 133-175);
**Bobzien 2001** = the monograph *Determinism and Freedom in Stoic Philosophy*
(Oxford, first published 1998, cited from the 2001 paperback).

Four verified repairs (evidence checked 2026-08-23 against the raw full-text
extractions in 04_Littérature_secondaire):

1. RELABEL the monograph node "Bobzien 1998 — …" -> "Bobzien 2001 — …" and set
   metadata.year = 2001, keeping year_first_published = 1998 (bibliographic
   truth preserved). bibtex_key untouched (it is a join key).
2. RELINK scholarly_argument_bobzien_eph_hemin_what_depends_on_us_3
   (page_range 375-412 — outside the article's 133-175; the monograph's ch. 8
   runs 358-412) from the article to the monograph: its advanced_in edge's
   target/target_id move to the monograph node. The monograph already
   `discusses` this node, so the pair stays coherent and no duplicate triple
   is created.
3. FIX page_range on scholarly_argument_bobzien_exousia_and_conceptual_shift_t_5
   from '1504-1611' (Kindle locations, not pages) to '164-167' — the article's
   Section XI "ἐξουσία in accounts of ἐφ' ἡμῖν" is pp. 164-167 (extraction TOC
   and terminology table both attest it). Node stays linked to the article.
4. FIX page_range on scholarly_argument_bobzien_origen_s_response_to_the_idle__8
   from '173' to '205-208' — the article mentions Origen only incidentally
   (n. 48 and one aside); the monograph's §5.2.2 treatment of Origen's Cels.
   II 20 reply spans pp. 205-208 (book index: Origen 180-208 …; §5.2.2.2 note
   at p. 207; matches argument_bobzien_2001_b1_origen_idle_argument_reply).
   Node is already linked to the monograph.
"""

WAVE_STAMP = "bobzien_disambiguation_2026_08_23"

BOOK_ID = "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso"
ARTICLE_ID = "pub_bobzien_1998_inadvertent"

BOOK_OLD_LABEL = "Bobzien 1998 — Determinism and Freedom in Stoic Philosophy"
BOOK_NEW_LABEL = "Bobzien 2001 — Determinism and Freedom in Stoic Philosophy"

RELINK_NODE = "scholarly_argument_bobzien_eph_hemin_what_depends_on_us_3"

PAGE_FIXES = [
    {
        "node_id": "scholarly_argument_bobzien_exousia_and_conceptual_shift_t_5",
        "old_page_range": "1504-1611",
        "new_page_range": "164-167",
    },
    {
        "node_id": "scholarly_argument_bobzien_origen_s_response_to_the_idle__8",
        "old_page_range": "173",
        "new_page_range": "205-208",
    },
]
