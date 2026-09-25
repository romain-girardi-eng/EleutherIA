"""Decisions — Justin, Dialogue with Trypho: HTML entity artefacts and one malformed locus.

Source queue: data/quality/jev_2026_09_24/c1_passage_concepts/queue_quality_flags.csv
(passage_just_tryph_27_3, "text mixed with critical apparatus", p = 0.93), extended to every
node carrying the same artefact.

Evidence (level 1): the Perseus/First1KGreek TEI of the edition the nodes declare,
tlg0645.tlg003.perseus-grc2 = G. Archambault, Justin, Dialogue avec Tryphon, Paris, Picard, 1909
(OpenGreekAndLatin/First1KGreek, data/tlg0645/tlg003/tlg0645.tlg003.perseus-grc2.xml).

* 197 KG passage nodes (and 196 corpus twins) write the hyphen of Archambault's scripture
  references as the HTML entity "&#45;" (e.g. "[cf. Ps., XIII, 2 &#45; 3, et Rom., III, 44 &#45; 47]"
  for "[cf. Ps., XIII, 2-3, et Rom., III, 44-47]"). The bracketed references themselves ARE in the
  edition's printed text and are kept.
* Rule, checked per record at run time: after replacing "\\s*&#45;\\s*" by "-", the text must equal
  the TEI section of the node's own CTS locus character for character once whitespace is removed.
  All 197 + 196 pass; a record that does not is skipped, never forced.
* passage_just_tryph_140_4 declares the locus "140_4" (cts_urn ...:140_4). Its text equals TEI
  section 140.4; the locus becomes "140.4".
"""

ENTITY = "&#45;"
TEI_RELATIVE = "OpenGreekAndLatin/First1KGreek/data/tlg0645/tlg003/tlg0645.tlg003.perseus-grc2.xml"
LOCUS_FIXES = {
    # text == TEI 140.4 (verified); "140_4" is not a CTS passage reference
    "passage_just_tryph_140_4": ("140_4", "140.4"),
}
