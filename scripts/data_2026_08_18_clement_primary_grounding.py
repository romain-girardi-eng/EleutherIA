"""Declarative scope for the 2026-08-18 Clement primary-grounding wave.

The Greek itself is never generated here.  The applier extracts these exact
TEI divisions from the hash-pinned local Stahlin/Perseus re-encoding and
copies them verbatim into the KG and corpus mirror.
"""

from __future__ import annotations

WAVE = "clement_primary_grounding_2026_08_18"

XML_SHA256 = "9b0dd0f4728dcbd57ab08231ad7addeb739c8046879dfceae0825b717d753eb1"
XML_RELATIVE_SOURCE = "02_Corpus/TLG/TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml"
PUBLIC_SOURCE_PATH = (
    "[local-path] SHAL/02_Corpus/TLG/TLG_tlg0555_Clemens_Alexandrinus_Stromata.xml"
)

PDF_SHA256 = "58f50e5bf428cd918f8a792586891665196446cbe4b248027eec2e7537d943bb"
PDF_PUBLIC_SOURCE_PATH = (
    "[local-path] SHAL/04_Litterature_secondaire/_acquisitions/"
    "GCS_Staehlin_Clemens_II_Stromata_I-VI_1906.pdf"
)

# (book, XML chapter, continuous Stahlin section, traditional reference note)
#
# The work node and the source study use book.chapter notation for the broad
# ranges: II.6-15 means chapters 6 through 15 (sections 25-71), just as
# IV.23-24 means chapters 23-24 (sections 147-154).  By contrast, Amand's
# abbreviated "II, 11, 1-2" means flat Stahlin section 11, subsections 1-2;
# its unambiguous CTS hierarchy is 2.3.11.  Keeping both forms prevents the
# numbering confusion that caused the 2026-05 evidence-link defect.
_CHAPTER_SECTIONS = {
    (2, 6): range(25, 32),
    (2, 7): range(32, 36),
    (2, 8): range(36, 41),
    (2, 9): range(41, 46),
    (2, 10): range(46, 48),
    (2, 11): range(48, 53),
    (2, 12): range(53, 56),
    (2, 13): range(56, 60),
    (2, 14): range(60, 62),
    (2, 15): range(62, 72),
    (4, 23): range(147, 153),
    (4, 24): range(153, 155),
}

TARGETS = (
    (2, 2, 8, "Strom. II.2.8 (esp. subsections 3-4; GCS II p. 117)"),
    (2, 3, 11, "Strom. II.11.1-2 = CTS 2.3.11 (GCS II pp. 118-119)"),
    *tuple(
        (book, chapter, section, f"Strom. {book}.{chapter}.{section}")
        for (book, chapter), sections in _CHAPTER_SECTIONS.items()
        for section in sections
    ),
    (5, 13, 86, "Strom. V.13.86 (GCS II p. 383)"),
)

WORK_ID = "work_clement_stromateis"
PERSON_ID = "person_clement_alexandria"
CORPUS_WORK_ID = "work_clement_stromateis_grc"
CTS_BASE = "urn:cts:greekLit:tlg0555.tlg004.perseus-grc2"

ARGUMENT_FAITH_NATURE = "argument_clement_alex_carneadean_glissement_faith_unbelief"
ARGUMENT_GRACE_ASSENT = "argument_clement_grace_synergy_assent"

# The exact six KG edges and six corpus citations attached in 2026-05 to the
# wrong text (II.11.50-52).  The applier verifies every triple before removal.
WRONG_EDGE_IDS = {
    "ea1ca4cd-254a-4fe9-a393-5ad7f4a90f07",
    "c8873ffe-f1c6-48aa-8109-f54985038e8a",
    "1d3c01a0-0977-4689-93a9-720277af636a",
    "2f0a0964-8ecf-4a0f-ad79-9805ef2c082d",
    "461ca590-ce9a-41d1-87c9-879ad2ae52f4",
    "21ab42df-f82a-4fc6-9351-247d8ac9937d",
}

WRONG_PASSAGE_IDS = {
    "e19a7f83-2247-590f-a959-8f08bb279101",
    "80d51072-e88a-5700-953d-75d3e5a9cbeb",
    "956b554e-7baf-5049-8b29-ad56f2283f9e",
}

WRONG_ARGUMENT_IDS = {ARGUMENT_FAITH_NATURE, ARGUMENT_GRACE_ASSENT}

# Exact primary passages that substantiate each already-existing argument.
EVIDENCE_TARGETS = {
    ARGUMENT_FAITH_NATURE: ((2, 3, 11),),
    ARGUMENT_GRACE_ASSENT: (
        (2, 2, 8),
        (2, 6, 26),
        (2, 12, 54),
        (2, 12, 55),
        (4, 23, 152),
        (4, 24, 153),
        (5, 13, 86),
    ),
}

REVIEW_QUEUE_IDS = (
    "rq_51ffddfd4448",
    "rq_695597d734fc",
    "rq_4c7d6b616009",
)
