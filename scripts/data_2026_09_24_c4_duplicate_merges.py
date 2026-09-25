"""Decisions — the eight C4 "likely duplicate" pairs (Jev p ≥ 0.9).

Source queue: data/quality/jev_2026_09_24/c4_dedup_schools/queue_likely_duplicates.csv.
Each pair was re-read in full (label, description, metadata, every edge) on
2026-09-24. Seven are one entity under two ids and are merged below; the
eighth (Bobzien/PHILOPATOR) is already modelled on purpose as two
granularities joined by ``same_thesis_as`` and is NOT merged.

MERGES: (survivor, absorbed, reason). The survivor is the node that carries
the structure (chapters, passages, pointers) or the verifiable identifier
(DOI); the absorbed id is kept in ``metadata.merged_from`` and
``metadata.previous_node_id``.
"""

MERGES = [
    # Same homily, same edition. Survivor holds the 109 SC 123 chapters and
    # 328 metadata pointers; absorbed says "Critical edition: Perler (SC 123,
    # 1966)" and holds passage_melito_pasch_47_49 / _49_54 (+ _en).
    (
        "sc123_melito_peri_pascha",
        "work_melito_peri_pascha",
        "same work: Melito, Peri Pascha, ed. Perler SC 123 (both nodes name it)",
    ),
    # Same Syriac dialogue. Survivor: "Book of the Laws of the Countries
    # (Ktābā d-nāmōsē d-aṯrawātā) ... composed by Philippus, a disciple of
    # Bardaisan"; absorbed: "Bardesane (et Philippe), Le Livre des lois des
    # pays (Liber Legum Regionum) ... composed ... by his disciple Philip".
    # docs/development/ingestion-rules.md R2 names this very incident.
    (
        "work_bardaisan_book_of_laws",
        "work_bardesanes_liber_legum_regionum",
        "same work: Book of the Laws of the Countries / Liber Legum Regionum",
    ),
    # Same apology, same SC volume. Survivor holds the 38 chapters.
    (
        "sc379_athenagoras_legatio",
        "work_athenagoras_legatio_sc379",
        "same work: Athenagoras, Legatio pro Christianis, SC 379",
    ),
    # Same monograph. Survivor carries the DOI 10.1163/9789004407763 and the
    # seven scholarly_work_id pointers; absorbed: "Linjamaa, P. (2019). The
    # Ethics of The Tripartite Tractate (NHC I, 5). Brill (NHMS 95)".
    (
        "scholarly_work_linjamaa_2019_the_ethics_of_the_tripartite_tractate_nh",
        "pub_linjamaa_2019_ethics_tripartite_tractate",
        "same publication: Linjamaa 2019, Brill NHMS 95",
    ),
    # Same treatise. Survivor: "Irenaeus, Epideixis (Demonstration of
    # Apostolic Preaching)"; absorbed: "Irenee de Lyon, Demonstration de la
    # predication apostolique (Epideixis)".
    (
        "work_irenaeus_epideixis",
        "work_irenaeus_demonstratio_apostolic",
        "same work: Irenaeus, Epideixis / Demonstratio apostolicae praedicationis",
    ),
    # Same apology, same SC volume. Survivor holds the 24 chapters.
    (
        "sc470_aristides_apologia",
        "work_aristides_apology_sc470",
        "same work: Aristides, Apologia, SC 470",
    ),
    # Same article. Survivor carries DOI 10.1017/S0034412500010350 and the
    # two scholarly_work_id pointers. The absorbed id names Plantinga (R9):
    # its own label reads "Tomberlin, J.E. & McGuinness, F. (1977). God, Evil,
    # and the Free Will Defence. Religious Studies 13: 455-475".
    (
        "scholarly_work_tomberlin_1977_god_evil_and_the_free_will_defence",
        "pub_plantinga_god_evil_free_will_defence",
        "same publication: Tomberlin & McGuinness 1977, Religious Studies 13",
    ),
]

# When the survivor's public description is only its bare title, the
# absorbed node's fuller description (already public on the absorbed node)
# becomes the survivor's description.
TAKE_DESCRIPTION_IF_SURVIVOR_IS_TITLE = {
    "scholarly_work_linjamaa_2019_the_ethics_of_the_tripartite_tractate_nh",
    "scholarly_work_tomberlin_1977_god_evil_and_the_free_will_defence",
}

# Edges of absorbed nodes that are wrong in themselves and are dropped, not
# redirected. (source, relation, target) on the ORIGINAL ids.
DROP_EDGES = {
    # Plantinga is the author discussed, not an author of the article: the
    # node's own metadata.author reads "James E. Tomberlin and Frank McGuinness".
    (
        "pub_plantinga_god_evil_free_will_defence",
        "authored_by",
        "scholar_plantinga_a",
    ): "Plantinga is the subject of the article, not its author (metadata.author)",
}

NOT_MERGED = {
    (
        "argument_bobzien_2001_b1_philopator_late_compatibilism",
        "scholarly_argument_bobzien_later_stoic_compatibilism_phil_6",
    ): (
        "already joined by same_thesis_as (semantic_merges_2026_08_17, DAS-001): "
        "deliberately kept as two granularities; their page references disagree "
        "(ch. 8 pp. 358-412 vs page_range 216-225 / quote_page p. 372), which a "
        "merge would hide — needs_romain"
    ),
}
