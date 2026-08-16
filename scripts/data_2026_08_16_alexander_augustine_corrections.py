"""Authored data for the 2026-08-16 Alexander/Augustine correction pass.

Companion data module for `apply_2026_08_16_alexander_augustine_corrections.py`.
It carries the five bodies of work mandated by the double audit of 2026-08-16,
each item verified individually before being written here:

1. `DESCRIPTION_SPANS` — mechanical OCR / transmission defects in four passage
   descriptions, every one re-verified against a named witness (the local TLG E
   corpus via `scripts/tlg_search.py`, von Arnim's SVF TEI OCR, or the node's
   own cited OCR source file).
2. `DESCRIPTION_SET` — `passage_aug_civ_21_12`, whose description was absent.
3. `METADATA_OPS` — provenance repairs, the id/label incoherences of §3, the
   Frede wording warning, and the new `source_rank` convention of §4.
4. `APOSTROPHE_*` — the U+02BC → U+2019 normalisation sweep.
5. `SKIPPED` — items the audit mandated that verification did *not* support,
   recorded here with the counter-evidence rather than applied.

Zero-fabrication rule: no ancient-language string is introduced that is not
already verbatim in the same node or quoted below from a named local witness.
Every replacement below only *removes* characters that the witness does not
have, or restores characters the witness does have; nothing is composed.

The new convention established here:

    metadata.source_rank — a short, machine-readable statement of the
    bibliographic rank of a secondary-literature node (peer-reviewed
    monograph / journal article / dissertation / MA thesis / online essay,
    plus "[unverified]" when the record could not be collated against a
    copy). Synthesis layers must disclose it when citing the node.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Mechanical OCR / transmission defects in passage descriptions
# ---------------------------------------------------------------------------
# Each entry: node id -> tuple of (old, new) spans. The applier requires each
# `old` to occur EXACTLY ONCE in the node's description; otherwise it reports
# and skips, never applies blind.

DESCRIPTION_SPANS: dict[str, tuple[tuple[str, str], ...]] = {
    # --- Gellius, NA VII.2.5 -------------------------------------------------
    # "quicquid futurumfiturum est" is a TEI <choice> flattening artefact of the
    # Perseus latinLit phi1254.phi001.perseus-lat2 source, not a reading: the
    # corrected form and the manuscript sic-form were concatenated on ingestion.
    # The same file shows the identical artefact elsewhere — "scriptumscripturm"
    # (1.7.7), "futurumfuturunm" (1.7.13), "tumTurn" (1.14.2), "eamearn"
    # (1.14.2) — see data/corpus/_audit_cache/
    # urn_cts_latinLit_phi1254.phi001.perseus-lat2.json.
    # Independent local witness for the reading: von Arnim, SVF II.1000, in the
    # local TEI OCR data/scholarly_sources/ocr/svf_chrysippus/svf_ii_tei.xml
    # line 3189: "per quam necesse sit fieri, quicquid futurum est".
    "passage_gellius_na_vii_2_7_2_5": (
        ("quicquid futurumfiturum est", "quicquid futurum est"),
    ),
    # --- Firmicus Maternus, Mathesis I.2.5 -----------------------------------
    # Both corrections are named explicitly in the node's OWN cited source file,
    # data/scholarly_sources/ocr/firmicusmathesis/source.md, section
    # "### Math I.2.5", block "Anomalies OCR observées":
    #   - `bumanis` → canon. `humanis` (confusion `h` → `b`, fréquente sur la
    #     fonte Teubner ancienne)
    #   - `secarus` → canon. `securus` (confusion `u` → `a`)
    # The OCR (archive.org DjVu of Kroll–Skutsch, Teubner t. I, 1897) was
    # deliberately ingested verbatim including its residues; this pass applies
    # the two corrections the source file had already adjudicated.
    "passage_firmicus_math_1_2_5": (
        ("omnia ex rebus bumanis virtutum", "omnia ex rebus humanis virtutum"),
        ("cupiditates secarus stellarum", "cupiditates securus stellarum"),
    ),
    # --- Eusebius, Praeparatio Evangelica VI.6.17 ----------------------------
    # (a) dittography "ἐξουσίας σίας": TLG2018 (Eusebius) @byte 528481 reads
    #     "ἀλλ' αὐτοτελῶς ἐκ τῆς ἰδίας ἐξουσίας εἰς τὰς τοιαύτας κινήσεις
    #     ἀφικνουμένων" — 1 hit; the doubled form "ἐξουσίας σίας" gets 0 hits.
    # (b) "οὕτω γὰρ ἐπεὶ ἐναργῶς" gets 0 hits; TLG2018 @byte 528238 reads
    #     "οὕτως γὰρ ἐπεὶ ἐναργῶς ἑαυτῶν αἰσθανόμεθα" — 1 hit.
    # Verified 2026-08-16 with scripts/tlg_search.py against the local TLG E.
    "passage_eusebius_praep_ev_6_6_17": (
        # NOTE ON ENCODING: this node's Greek uses the "oxia" precomposed forms
        # (\u1f77 GREEK SMALL LETTER IOTA WITH OXIA), not the "tonos" forms a
        # keyboard produces (\u03af), so the span below is written with explicit
        # escapes copied out of the file itself. Deleting " \u03c3\u1f77\u03b1\u03c2"
        # is the whole edit \u2014 every surviving character is the node's own byte.
        # old: "\u1f10\u03be\u03bf\u03c5\u03c3\u1f77\u03b1\u03c2 \u03c3\u1f77\u03b1\u03c2 \u03b5\u1f30\u03c2"  (exousias sias eis)
        # new: "\u1f10\u03be\u03bf\u03c5\u03c3\u1f77\u03b1\u03c2 \u03b5\u1f30\u03c2"        (exousias eis)
        (
            "\u1f10\u03be\u03bf\u03c5\u03c3\u1f77\u03b1\u03c2 \u03c3\u1f77\u03b1\u03c2 \u03b5\u1f30\u03c2",
            "\u1f10\u03be\u03bf\u03c5\u03c3\u1f77\u03b1\u03c2 \u03b5\u1f30\u03c2",
        ),
        ("οὕτω γὰρ ἐπεὶ ἐναργῶς", "οὕτως γὰρ ἐπεὶ ἐναργῶς"),
    ),
    # --- Alexander of Aphrodisias, De fato 19 (the Phalaris sentence) --------
    # TLG0732 @byte 7373803 reads: "ἀλλ' οὐδεὶς Φάλαρις οὕτως ὠμός τε καὶ
    # ἀνόητος, ὡς ἐπί τινι τῶν οὕτως γινο-μένων κολάζειν τὸ ποιήσαντα."
    # Searching "κολάζειν τὸν ποιήσαντα" returns 0 hits in the whole TLG E;
    # "κολάζειν τὸ ποιήσαντα" returns exactly this Alexander locus (Bruns).
    # Verified 2026-08-16 with scripts/tlg_search.py.
    "passage_alex_fat_19": (("κολάζειν τὸν ποιήσαντα", "κολάζειν τὸ ποιήσαντα"),),
}

# ---------------------------------------------------------------------------
# 2. passage_aug_civ_21_12 — description was absent
# ---------------------------------------------------------------------------
# Library survey 2026-08-16: no critical text of De ciuitate Dei is held
# locally. Checked and ruled out: 02_Corpus/LLT_brepols/ (no Augustinus author
# directory at all), 02_Corpus/SCO_brepols/, 02_Corpus/Editions_critiques/
# (LXX Göttingen, Vulgate, NA28 only), 03_Sources_critiques/ (one Augustine
# file, and it is De peccatorum meritis on Rom 5:12, CSEL 60), ~/Desktop/Romain/
# TLGE (Greek TLG-E only, no PHI Latin corpus anywhere on disk).
# The Latin already stored in this node's `text_content` therefore stays as it
# is — it is not fabricated — but it is a partial excerpt (it begins and ends
# mid-sentence, carries no chapter boundary) whose traceable provenance is
# thelatinlibrary.com/augustine/civ21.shtml, recorded in
# data/audit/primary_wave/description_patches.json, and NOT Dombart–Kalb. The
# description below is therefore locus-only, and the node is put under the
# established `needs_text_ingestion` convention (metadata flag + a stated
# ingestion_blocked_reason, as on work_apuleius_de_platone).
# The two Latin words quoted below are verbatim from this node's own
# text_content; nothing is composed.
DESCRIPTION_SET: dict[str, str] = {
    "passage_aug_civ_21_12": (
        "Augustine, *De ciuitate Dei* XXI.12 — the *massa damnata* chapter. "
        "Augustine argues that the greater the good Adam enjoyed, the greater "
        "the impiety of abandoning God, and that from that first transgression "
        "the whole human race becomes a condemned mass (*uniuersa generis "
        "humani massa damnata*), from which no one is delivered except by "
        "merciful and undeserved grace — so that in some God shows what mercy "
        "can do and in the rest what just retribution is. The locus is one of "
        "the two anchors (with *Enchiridion* 99) of the mature Augustinian "
        "position that the will's freedom after the fall is freedom only to sin.\n\n"
        "LOCUS ONLY — TEXT NOT YET COLLATED. No critical edition of *De "
        "ciuitate Dei* is held in the local library (survey 2026-08-16: CCSL "
        "47-48 Dombart–Kalb and CSEL 40 Hoffmann are both absent; the Brepols "
        "LLT harvest under 02_Corpus/ carries no Augustinus directory; there is "
        "no PHI Latin corpus on disk). The Latin in this node's `text_content` "
        "is a partial excerpt that begins and ends mid-sentence and whose "
        "traceable provenance is thelatinlibrary.com, not Dombart–Kalb; it must "
        "be collated against CCSL 48 (Dombart–Kalb, 1955) before being quoted "
        "as a critical text. See metadata.ingestion_blocked_reason."
    ),
}

# ---------------------------------------------------------------------------
# 3. Metadata operations
# ---------------------------------------------------------------------------
# op vocabulary understood by the applier:
#   {"op": "set",         "key": K, "value": V}        — set metadata[K]
#   {"op": "set_if",      "key": K, "old": O, "value": V}
#                                                      — set only if currently O
#   {"op": "note",        "value": "..."}              — append to the
#                         metadata.verification_notes list (created if absent)
NOTE_KEY = "verification_notes"

_KOCH_WORK_ID = (
    "scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale"
)
_KOCH_DANGLING_ID = (
    "scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre"
)

_GUYOMARCH_ARGUMENT_IDS = (
    "scholarly_argument_guyomarc_h_alexander_of_aphrodisias_de_fa_0",
    "scholarly_argument_guyomarc_h_alexander_s_aristotelian_sourc_5",
    "scholarly_argument_guyomarc_h_alexander_s_conception_of_what_2",
    "scholarly_argument_guyomarc_h_alexander_s_rhetorical_strateg_6",
    "scholarly_argument_guyomarc_h_alexander_s_target_stoic_deter_1",
    "scholarly_argument_guyomarc_h_necessity_and_fate_alexander_s_3",
    "scholarly_argument_guyomarc_h_the_human_problem_of_free_will_4",
)

METADATA_OPS: dict[str, tuple[dict, ...]] = {
    # --- §1 provenance stamps for the four OCR corrections -----------------
    "passage_gellius_na_vii_2_7_2_5": (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] description read 'quicquid futurumfiturum est'. "
                "That is a TEI <choice> flattening artefact of the Perseus "
                "phi1254.phi001.perseus-lat2 ingestion (the same cache shows "
                "'scriptumscripturm', 'futurumfuturunm', 'tumTurn', 'eamearn'), not a "
                "transmitted reading. Corrected to 'quicquid futurum est' on the "
                "authority of von Arnim, SVF II.1000, local TEI OCR "
                "data/scholarly_sources/ocr/svf_chrysippus/svf_ii_tei.xml l. 3189: "
                "'per quam necesse sit fieri, quicquid futurum est'."
            ),
        },
        {"op": "set", "key": "ocr_correction_2026_08_16", "value": True},
    ),
    "passage_firmicus_math_1_2_5": (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] description reproduced two OCR residues of the "
                "archive.org DjVu scan of Kroll–Skutsch (Teubner t. I, 1897): "
                "'ex rebus bumanis' and 'cupiditates secarus'. Both are adjudicated "
                "in the node's own cited source file, "
                "data/scholarly_sources/ocr/firmicusmathesis/source.md, section "
                "'### Math I.2.5' > 'Anomalies OCR observées': `bumanis` → canon. "
                "`humanis` (confusion h → b); `secarus` → canon. `securus` "
                "(confusion u → a). Applied. The remaining sections I.2.6-11 of the "
                "same OCR still carry their documented residues and are NOT touched "
                "by this pass."
            ),
        },
        {"op": "set", "key": "ocr_correction_2026_08_16", "value": True},
    ),
    "passage_eusebius_praep_ev_6_6_17": (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16, TLG E via scripts/tlg_search.py] two readings "
                "corrected against TLG2018 (Eusebius, Praep. Ev.): (a) the "
                "dittography 'ἐκ τῆς ἰδίας ἐξουσίας σίας' (0 hits in TLG E) → "
                "'ἐκ τῆς ἰδίας ἐξουσίας' (TLG2018 @byte 528481, 1 hit, in this exact "
                "sentence); (b) 'οὕτω γὰρ ἐπεὶ ἐναργῶς' (0 hits) → 'οὕτως γὰρ ἐπεὶ "
                "ἐναργῶς' (TLG2018 @byte 528238, 1 hit). The First1KGreek TEI "
                "re-encoding of Dindorf t. I (1867) that this node was ingested from "
                "carried both defects."
            ),
        },
        {"op": "set", "key": "ocr_correction_2026_08_16", "value": True},
    ),
    "passage_alex_fat_19": (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16, TLG E via scripts/tlg_search.py] the Phalaris "
                "sentence read 'κολάζειν τὸν ποιήσαντα'. That form returns 0 hits in "
                "the whole TLG E; the Bruns text as carried by TLG0732 @byte 7373803 "
                "reads 'ὡς ἐπί τινι τῶν οὕτως γινομένων κολάζειν τὸ ποιήσαντα' "
                "(1 hit, this locus). Aligned to the TLG/Bruns reading. NOT touched "
                "in this pass, and left for a later item-by-item review: the node "
                "also reads 'ἐπὶ τίσιν οὐν αἱ κολάσεις' where TLG reads 'οὖν'."
            ),
        },
        {"op": "set", "key": "ocr_correction_2026_08_16", "value": True},
    ),
    # --- §2 Augustine, De ciuitate Dei XXI.12 -------------------------------
    "passage_aug_civ_21_12": (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] metadata.source read 'Dombart-Kalb (CCSL 47-48 "
                "basis)' and metadata.note read 'verbatim excerpt'. Both overstate "
                "the provenance: no critical De ciuitate Dei exists in the local "
                "library (LLT_brepols has no Augustinus directory; no CCSL/CSEL/PHI "
                "on disk), and the audit trail at "
                "data/audit/primary_wave/description_patches.json records the "
                "evidence actually used as thelatinlibrary.com/augustine/civ21.shtml, "
                "which carries no apparatus. The Latin in text_content is left "
                "untouched (it is a genuine excerpt, not a fabrication) but is "
                "re-described as partial and uncollated, and the node is put under "
                "the needs_text_ingestion convention."
            ),
        },
        {
            "op": "set_if",
            "key": "source",
            "old": "Dombart-Kalb (CCSL 47-48 basis)",
            "value": (
                "thelatinlibrary.com/augustine/civ21.shtml (no apparatus, uncollated) "
                "— target critical edition: CCSL 48, Dombart–Kalb, 1955"
            ),
        },
        {
            "op": "set_if",
            "key": "note",
            "old": "verbatim excerpt",
            "value": (
                "partial verbatim excerpt — begins and ends mid-sentence, no chapter "
                "boundary; provenance uncollated (see verification_notes)"
            ),
        },
        {"op": "set", "key": "needs_text_ingestion", "value": True},
        {
            "op": "set",
            "key": "ingestion_blocked_reason",
            "value": (
                "No critical edition of De ciuitate Dei is held locally (survey "
                "2026-08-16: CCSL 47-48 Dombart–Kalb absent, CSEL 40 Hoffmann absent, "
                "no PHI Latin corpus on disk, Brepols LLT harvest carries no "
                "Augustinus author directory). The stored text is a partial "
                "non-critical excerpt from thelatinlibrary.com. Unblocking requires "
                "CCSL 48 pp. 778-779 (Dombart–Kalb 1955) or CSEL 40/2 (Hoffmann)."
            ),
        },
        {"op": "set", "key": "text_excerpt_partial", "value": True},
        {"op": "set", "key": "canonical_ref", "value": "De ciu. Dei XXI.12"},
    ),
    # --- §3a Koch 2019 vs Guyomarc'h 2015 -----------------------------------
    # VERIFIED, and conclusively, from local evidence only:
    #   (i) the work itself cites Guyomarc'h in the third person in its own
    #       footnotes — 04_Littérature_secondaire/01_Philosophie_antique/
    #       La_Causalite_humaine_Sur_le_De_fato_dAle.md ll. 648-649, 917, 1039,
    #       1082, 1489: "comme le note Gweltaz Guyomarc'h … (Guyomarc'h, 2015,
    #       p. 32)". An author does not cite himself that way; the extraction
    #       pipeline mistook the most-cited footnote author for the author.
    #  (ii) the local bibliography records the file with authors: null, year:
    #       null (04_Littérature_secondaire/biblio_overrides.json) — it never
    #       attributed the volume to anyone.
    # (iii) Isabelle Koch is independently present in the local library on
    #       exactly this topic (Koch_2011_Le_Destin_OCR.txt, Vrin 2011), and
    #       Guyomarc'h appears locally only as a metaphysics/De anima
    #       specialist (Ramelli 2014 bibliography: GUYOMARC'H, G. 2008).
    #  (iv) the repo's own prior adjudication, data/audit/wave3/
    #       J4_misattribution__scholarly_work_guyomarc_h_2015_…json, verdict
    #       "confirmed", and data/audit/citations_manifest.json l. 111.
    # The label and every metadata field already say Koch 2019. Only the id is
    # stale — and the id is kept, because edges and seven argument nodes point
    # at it; the discrepancy is recorded instead.
    _KOCH_WORK_ID: (
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] id/node_id slug still encodes the superseded "
                "attribution 'guyomarc_h_2015'. The volume is by Isabelle Koch "
                "(Classiques Garnier 2019) — established from local evidence alone: "
                "the work cites 'Guyomarc'h, 2015' in its own footnotes in the third "
                "person (La_Causalite_humaine_Sur_le_De_fato_dAle.md ll. 648-649, "
                "917, 1039, 1082, 1489); biblio_overrides.json records the file with "
                "authors: null; Koch is separately attested locally on the same topic "
                "(Le Destin, Vrin 2011). Guyomarc'h's own 2015 book is a different "
                "title (L'unité de la métaphysique selon Alexandre d'Aphrodise, Vrin) "
                "and has no node. The id is DELIBERATELY NOT RENAMED: edges and the "
                "seven scholarly_argument_guyomarc_h_* nodes resolve through it."
            ),
        },
        {
            "op": "set",
            "key": "id_attribution_note",
            "value": (
                "id slug says 'guyomarc_h_2015'; the verified attribution is Isabelle "
                "Koch, 2019, Classiques Garnier. id kept for referential stability — "
                "cite the label/verified_reference, never the slug."
            ),
        },
        {"op": "set", "key": "attribution_conflict_resolved", "value": "2026-08-16"},
    ),
    # The seven argument nodes point at a work node that does not exist. Fix the
    # dangling reference to the node that actually carries the record.
    **{
        arg_id: (
            {
                "op": "set_if",
                "key": "scholarly_work_id",
                "old": _KOCH_DANGLING_ID,
                "value": _KOCH_WORK_ID,
            },
            {
                "op": "note",
                "value": (
                    "[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at "
                    f"'{_KOCH_DANGLING_ID}', which is not a node in the graph "
                    "(dangling reference left behind when the Koch attribution was "
                    "corrected on the label only). Retargeted to the node that "
                    f"actually carries the record, '{_KOCH_WORK_ID}', whose id slug is "
                    "stale but whose label and metadata are correct (Koch 2019)."
                ),
            },
        )
        for arg_id in _GUYOMARCH_ARGUMENT_IDS
    },
    # Guyomarc'h's own scholar node still claimed Koch's book, and was flagged
    # "verified" while doing so — the most dangerous residue of the conflict.
    "scholar_guyomarc_h_g": (
        {
            "op": "set_if",
            "key": "verified_reference",
            "old": (
                "Gweltaz Guyomarc'h, work on Alexander of Aphrodisias' De fato "
                "('La causalité humaine. Sur le De fato d'Alexandre d'Aphrodise'); "
                "Guyomarc'h is MCF at Université Jean Moulin Lyon 3, specialist of "
                "Aristotle/Alexander."
            ),
            "value": (
                "Gweltaz Guyomarc'h, MCF at Université Jean Moulin Lyon 3, specialist "
                "of Aristotle and Alexander of Aphrodisias (Wikidata Q110853446). He "
                "is NOT the author of 'La causalité humaine. Sur le De fato "
                "d'Alexandre d'Aphrodise' — that volume is by Isabelle Koch "
                "(Classiques Garnier 2019) and cites Guyomarc'h 2015 in its own "
                "footnotes. His 2015 book is 'L'unité de la métaphysique selon "
                "Alexandre d'Aphrodise' (Vrin), which is not held locally and has no "
                "node in this graph."
            ),
        },
        {
            "op": "set_if",
            "key": "citation_verdict",
            "old": "verified",
            "value": "corrected",
        },
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] verified_reference attributed Isabelle Koch's "
                "2019 Classiques Garnier volume to Guyomarc'h and was flagged "
                "citation_verdict='verified'. Corrected; verdict downgraded to "
                "'corrected'. Evidence: the volume cites 'Guyomarc'h, 2015' in the "
                "third person in its own footnotes (local .md, ll. 648-649, 917, "
                "1039, 1082, 1489)."
            ),
        },
    ),
    # --- §3b Bonaiuti — id says 1924, the article is HTR 10 (1917) ----------
    # The label and metadata.year already carry 1917 (a previous pass fixed
    # them). What remains is the id slug and the bibtex_key, both encoding 1924,
    # plus a missing `author` field that leaves the exported BibTeX entry
    # authorless. The id is kept — edges reference it.
    "scholarly_work_bonaiuti_1924_the_genesis_of_st_augustine_s_idea_of_or": (
        {
            "op": "set",
            "key": "author",
            "value": "Ernesto Bonaiuti",
        },
        # @article wants `journal`, not `publisher`; the old publisher value was
        # the journal name, so it is moved rather than duplicated.
        {"op": "set", "key": "journal", "value": "Harvard Theological Review"},
        {"op": "delete", "key": "publisher", "expect": "Harvard Theological Review"},
        {"op": "set", "key": "volume", "value": "10"},
        {"op": "set", "key": "number", "value": "2"},
        {"op": "set", "key": "pages", "value": "159-175"},
        {
            "op": "set",
            "key": "id_year_discrepancy",
            "value": (
                "id slug and bibtex_key encode 1924; the article is Harvard "
                "Theological Review 10.2 (1917) 159-175, trans. Giorgio La Piana. "
                "Both kept for referential stability (edges and the exported .bib key "
                "resolve through them) — cite the label/year, never the slug."
            ),
        },
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] label and metadata.year already read 1917; only "
                "the id slug and bibtex_key still say 1924, and metadata carried no "
                "`author`, so the exported BibTeX entry was authorless (flagged in "
                "data/kg/publications_bibtex_report.json). Added author/journal/"
                "volume/number from the node's own verified_reference (local source "
                "file: 06_Patristique/genesis_of_st_augustines_idea_of_original_sin.md). "
                "Id and bibtex_key deliberately unchanged."
            ),
        },
    ),
    # --- §3c Frede 2011: the slug is not a quotation -------------------------
    # Verified 2026-08-16 against the local extraction
    # 04_Littérature_secondaire/01_Philosophie_antique/Frede_2011_Free_Will.txt
    # (page markers present; ligatures ﬁ/ﬂ must be normalised before grepping):
    #   - p. 100, ll. 3488-3492, VERBATIM EXACT: "it is in Alexander that we
    #     ﬁnd the ancestor of the notion that to have a free will is to be able,
    #     in the very same circumstances, to choose between doing A and doing B".
    #   - "fundamentally flawed": NOT IN FREDE. "fundamentally" occurs exactly
    #     once in the whole book, in A. A. Long's foreword, about Frede's prose.
    #     Frede's adjective is "basically", pp. 177-178: "…notions of a free will
    #     which … do not seem to be basically ﬂawed in the way a notion like
    #     Alexander's is" — predicated obliquely, of the OTHER authors.
    #   - "dead end": ZERO occurrences in Frede 2011 (also zero for "impasse",
    #     "blind alley"). His metaphor is "a hopeless tangle" (p. 97) /
    #     "Alexander got into this tangle" (p. 100). Sorabji 2017 independently
    #     quotes Frede as "a hopeless tangle".
    "argument_frede_2011_alexander_libertarian_dead_end": (
        {
            "op": "set",
            "key": "id_slug_warning",
            "value": (
                "'dead end' is NOT Frede's phrase — it is this node's id slug. The "
                "phrase occurs nowhere in Frede 2011. Never quote the slug as Frede's "
                "words."
            ),
        },
        {
            "op": "set",
            "key": "frede_verified_wording",
            "value": {
                "p_100_ancestor": (
                    "the ancestor of the notion that to have a free will is to be "
                    "able, in the very same circumstances, to choose between doing A "
                    "and doing B"
                ),
                "p_100_ancestor_status": "verbatim exact (Frede 2011, p. 100, on Alexander)",
                "pp_177_178_flawed": (
                    "do not seem to be basically flawed in the way a notion like "
                    "Alexander's is"
                ),
                "pp_177_178_status": (
                    "Frede writes 'basically flawed', NOT 'fundamentally flawed', and "
                    "predicates it obliquely — of the other authors, from whom "
                    "Alexander is the single exception carved out of an otherwise "
                    "negative answer to 'was the notion of a free will flawed from its "
                    "very beginning?'"
                ),
                "p_97_metaphor": "In trying to explicate this, Alexander seems to be driven into a hopeless tangle.",
                "dead_end": "absent from Frede 2011 — zero occurrences",
            },
        },
        {"op": "set", "key": "wording_verified_2026_08_16", "value": True},
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16, local Frede_2011_Free_Will.txt] The audit brief "
                "asked for 'fundamentally flawed (pp. 177-178)' to be recorded as "
                "Frede's verified wording. It is NOT: 'fundamentally' occurs once in "
                "the whole book, in A. A. Long's foreword. Frede writes 'basically "
                "flawed'. The description and metadata.frede_verified_wording carry "
                "the corrected reading. The p. 100 'ancestor' sentence is confirmed "
                "verbatim and exact. 'dead end' is a slug artefact, absent from the "
                "book; Frede's metaphor is 'a hopeless tangle' (p. 97, p. 100)."
            ),
        },
    ),
    # --- §4 Sorabji 2017 — the audit's "title-only shell" is resolvable ------
    # The brief mandated metadata.reference_status="unverified — title-only
    # shell…". Verification refutes that premise, so the marking is NOT applied
    # (see SKIPPED). The chapter is held locally, filed under the EDITORS, which
    # is why `find -iname "*sorabji*"` misses it:
    # 01_Philosophie_antique/"Seaford, Richard_ Wilkins, John_ Wright, Matthew
    # Ephraim (eds.) - Selfhood and the soul…(2017).md", chapter head at l. 2126,
    # TOC at l. 83. The four-strands thesis is at §3 "WILL: FOUR
    # CHARACTERISTICS" (l. 2358): rationality (2378), freedom (2431), will power
    # (2437), will perverted by pride (2480), assembled only in Augustine
    # (2488). Sorabji credits the "different strands" point to Charles Kahn
    # (1988) and to his own Emotion and Peace of Mind (2000) ch. 21.
    "scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins": (
        {"op": "set", "key": "author", "value": "Richard Sorabji"},
        {
            "op": "set",
            "key": "booktitle",
            "value": (
                "Selfhood and the Soul: Essays on Ancient Thought and Literature in "
                "Honour of Christopher Gill"
            ),
        },
        {
            "op": "set",
            "key": "editor",
            "value": "Richard Seaford, John Wilkins and Matthew Wright",
        },
        {"op": "set", "key": "pages", "value": "49-66"},
        {
            "op": "set",
            "key": "reference_status",
            "value": (
                "verified 2026-08-16 — chapter located and collated in the local "
                "library; title, chapter number, page range, editors, publisher and "
                "ISBN all match the source file"
            ),
        },
        {
            "op": "set",
            "key": "source_rank",
            "value": "peer-reviewed volume chapter — Oxford University Press Festschrift, 2017",
        },
        {
            "op": "set",
            "key": "four_strands_provenance",
            "value": (
                "The four strands (rationality, freedom, will power, will perverted by "
                "pride, assembled only in Augustine) are set out in §3 'WILL: FOUR "
                "CHARACTERISTICS'. Sorabji credits the underlying 'different strands' "
                "point to Charles Kahn (1988) and to his own Emotion and Peace of Mind "
                "(2000) ch. 21 — the thesis is restated in 2017, not first stated."
            ),
        },
        {
            "op": "set",
            "key": "homonym_warning",
            "value": (
                "A SECOND, DISTINCT Sorabji 2017 exists: 'A Neglected Strategy of the "
                "Aristotelian Alexander on Necessity and Responsibility', in V. Harte "
                "and R. Woolf (eds.), Rereading Ancient Philosophy (Cambridge). That "
                "is where Sorabji defends Alexander against Frede. It is NOT held "
                "locally and must not be conflated with this chapter."
            ),
        },
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] The audit brief classed this node as an "
                "unresolvable title-only shell and asked for reference_status="
                "'unverified'. That was refuted: the chapter is held locally (filed "
                "under the editors Seaford/Wilkins/Wright, which defeats a filename "
                "search on 'sorabji'), and the node's title, chapter, pages 49-66, "
                "editors, publisher and ISBN all check out against it. The 'unverified' "
                "marking was therefore NOT applied; the description was expanded from "
                "the title alone, and author/booktitle/editor/pages were added so the "
                "exported BibTeX entry stops being an authorless @incollection."
            ),
        },
    ),
    # --- §4 source_rank — the convention established by this pass ------------
    "scholarly_work_nagasawa_2013_human_free_will_and_god_s_grace_in_the_e": (
        {
            "op": "set",
            "key": "source_rank",
            "value": "online essay — not peer-reviewed [unverified]",
        },
        {
            "op": "set",
            "key": "synthesis_disclosure_required",
            "value": (
                "Any synthesis citing this node must disclose its rank: it is a New "
                "Humanity Institute web essay, with no publisher, no DOI, no page "
                "range and no peer review. It may be used for orientation, never as "
                "the authority for a contested claim."
            ),
        },
        {"op": "set", "key": "author", "value": "Mako A. Nagasawa"},
        {
            "op": "set_if",
            "key": "citation_verdict",
            "old": "verified",
            "value": "corrected",
        },
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] node was flagged citation_verdict='verified' with "
                "metadata.type='article' while its own verified_reference identifies "
                "it as a New Humanity Institute web essay with no publisher, no DOI "
                "and no page range. Rank recorded in the new machine-readable field "
                "metadata.source_rank; verdict downgraded to 'corrected'. The node is "
                "kept — the essay is real and locally held "
                "(06_Patristique/Mako-Nagasawa-free-will-in-patristics.md) — but it is "
                "grey literature."
            ),
        },
    ),
    "scholarly_work_moon_2016_a_history_of_interpretation_of_romans_in": (
        {
            "op": "set",
            "key": "source_rank",
            "value": (
                "MA thesis — University of British Columbia (Classical, Near Eastern "
                "and Religious Studies), December 2016; not peer-reviewed"
            ),
        },
        {
            "op": "set",
            "key": "synthesis_disclosure_required",
            "value": (
                "Any synthesis citing this node must disclose that it is an unpublished "
                "master's thesis, not a peer-reviewed publication."
            ),
        },
        {"op": "set", "key": "author", "value": "John Moon"},
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] the MA-thesis caveat was present only inside the "
                "prose of metadata.verified_reference ('MA thesis …, The University of "
                "British Columbia, Vancouver, December 2016, 115 pp.'). Copied into "
                "the machine-readable metadata.source_rank field established by this "
                "pass."
            ),
        },
    ),
    "pub_sytsma_2020_universal_salvation_origen": (
        {
            "op": "set",
            "key": "source_rank",
            "value": (
                "PhD dissertation — Marquette University, May 2018, no. 769 (this is "
                "the copy actually held and collated); the 2020 Gorgias Press "
                "monograph is bibliographically attested (ISBN/DOI checked) but no "
                "copy was collated [unverified as monograph]"
            ),
        },
        {
            "op": "set",
            "key": "synthesis_disclosure_required",
            "value": (
                "Any synthesis citing this node must disclose that the verifiable "
                "object behind it is the 2018 Marquette dissertation, not the claimed "
                "2020 monograph; page references taken from the local PDF are "
                "dissertation pages."
            ),
        },
        {
            "op": "note",
            "value": (
                "[Vérif. 2026-08-16] the dissertation-vs-monograph caveat already "
                "existed in the description and in metadata.phd_version / "
                "metadata.isbn_doi_note, but only as prose. Copied into the "
                "machine-readable metadata.source_rank field established by this pass. "
                "No bibliographic value changed."
            ),
        },
    ),
}

# ---------------------------------------------------------------------------
# 3bis. Description spans that are not OCR fixes
# ---------------------------------------------------------------------------
# Frede: the description itself repeated the audit's inexact "fundamentally
# flawed" and stated it flatly, where Frede's own sentence is oblique.
DESCRIPTION_SPANS_PROSE: dict[str, tuple[tuple[str, str], ...]] = {
    "argument_frede_2011_alexander_libertarian_dead_end": (
        (
            "Conclusion: Alexander the only major ancient philosopher whose notion "
            "is fundamentally flawed, and he is precisely",
            "Conclusion: Frede's headline answer to 'was the notion of a free will "
            "flawed from its very beginning?' is NEGATIVE, and Alexander is the "
            "single exception he carves out of it — all the other authors have "
            "notions that 'do not seem to be basically flawed in the way a notion "
            "like Alexander's is' (pp. 177-178; Frede's adjective is 'basically', "
            "not 'fundamentally', and the verdict on Alexander is delivered "
            "obliquely). Alexander is precisely",
        ),
        (
            "the notion attacked by Ryle, Williams, and Frede",
            "the notion attacked by Ryle, Williams, and Frede.\n\n"
            "WORDING WARNING (verified 2026-08-16 against the local extraction of "
            "Frede 2011): 'dead end' is NOT Frede's phrase — it is this node's id "
            "slug (argument_frede_2011_alexander_libertarian_dead_end) and occurs "
            "nowhere in the book. Never quote the slug as Frede's words. Frede's "
            "verified wording is: (i) p. 100, verbatim and exact, 'the ancestor of "
            "the notion that to have a free will is to be able, in the very same "
            "circumstances, to choose between doing A and doing B'; (ii) pp. "
            "177-178, 'basically flawed' — NOT 'fundamentally flawed' — and said of "
            "the other authors, not predicated directly of Alexander; (iii) the "
            "metaphor Frede actually applies to Alexander is 'a hopeless tangle' "
            "(p. 97; 'Alexander got into this tangle', p. 100), the phrase Sorabji "
            "also quotes back at him.",
        ),
    ),
    # Sorabji 2017: description was the bare title.
    "scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins": (
        (
            "Freedom and Will: Graeco-Roman Origins",
            "Richard Sorabji, 'Freedom and Will: Graeco-Roman Origins', ch. 3 "
            "(pp. 49-66) in R. Seaford, J. Wilkins and M. Wright (eds.), *Selfhood "
            "and the Soul: Essays on Ancient Thought and Literature in Honour of "
            "Christopher Gill*, Oxford: Oxford University Press, 2017. Section 3 "
            "('WILL: FOUR CHARACTERISTICS') distinguishes the four strands that make "
            "up the ancient idea of the will — rationality, freedom, will power, and "
            "will perverted by pride — each found separately in earlier thinkers and "
            "assembled only in Augustine; Sorabji credits the underlying point to "
            "Charles Kahn (1988) and to his own *Emotion and Peace of Mind* (2000) "
            "ch. 21. Against Frede 2011 he argues that none of the four strands is "
            "present in Epictetus. Verified 2026-08-16 against the local copy of the "
            "volume (filed under the editors, not under Sorabji).",
        ),
    ),
    # Nagasawa: description was the bare title.
    "scholarly_work_nagasawa_2013_human_free_will_and_god_s_grace_in_the_e": (
        (
            "Human Free Will and God's Grace in the Early Church Fathers",
            "Mako A. Nagasawa, 'Human Free Will and God's Grace in the Early Church "
            "Fathers' (New Humanity Institute, 2013). A patristic survey arguing that "
            "the early Fathers — Justin (1 Apol. 43-44, against heimarmene: if all "
            "happens by fate, praise and blame are unjust), Irenaeus, Origen, and "
            "others — held human self-determination together with divine grace. "
            "SOURCE RANK: online essay, not peer-reviewed, no publisher, no DOI, no "
            "page range (see metadata.source_rank). Usable for orientation; not an "
            "authority for a contested claim.",
        ),
    ),
}

# ---------------------------------------------------------------------------
# 4. U+02BC → U+2019 normalisation sweep
# ---------------------------------------------------------------------------
# passage_arist_en_3_5 uses U+02BC MODIFIER LETTER APOSTROPHE ("ἐφʼ") where the
# rest of the corpus uses U+2019 RIGHT SINGLE QUOTATION MARK ("ἐφ’"), so the
# quote-gate's string comparison never matches it and scripts/check_greek_gate.py
# splits its Greek runs at every elision.
#
# The sweep is graph-wide, and it is safe to make it graph-wide because it was
# measured first: of the 18,104 U+02BC occurrences in data/kg/nodes.jsonl, ZERO
# sit between two Latin-script letters (no "Guyomarc'h"-style name is affected),
# 18,016 are elision apostrophes directly after a Greek letter, and the
# remaining 88 are the closing member of the ʽ…ʼ quotation pairs used by the
# Marcus Aurelius / Plotinus / Diogenes Laertius TEI sources — where U+2019 is
# the correct closing mark anyway.
#
# Scope: data/kg/nodes.jsonl only. data/kg/edges.jsonl carries 12 further
# occurrences (all "ἐφʼ ἡμῖν" inside edge metadata notes); they are deliberately
# left alone because this pass is not authorised to rewrite edges, and they are
# reported as a follow-up instead.
APOSTROPHE_FROM = "ʼ"  # MODIFIER LETTER APOSTROPHE
APOSTROPHE_TO = "’"  # RIGHT SINGLE QUOTATION MARK

# ---------------------------------------------------------------------------
# 5. Mandated items NOT applied, with the counter-evidence
# ---------------------------------------------------------------------------
SKIPPED: tuple[dict[str, str], ...] = (
    {
        "item": "Frede node: record 'fundamentally flawed' (pp. 177-178) as Frede's verified wording",
        "verdict": "SKIPPED — the phrase is not Frede's",
        "evidence": (
            "Local extraction 04_Littérature_secondaire/01_Philosophie_antique/"
            "Frede_2011_Free_Will.txt: 'fundamentally' occurs exactly once in the "
            "whole book (l. 166), in A. A. Long's editorial foreword, about Frede's "
            "prose style. Frede's adjective is 'basically', four times, and the "
            "pp. 177-178 sentence predicates it of the OTHER authors: '…notions of a "
            "free will which … do not seem to be basically flawed in the way a "
            "notion like Alexander's is'. The corrected wording was written to the "
            "node instead."
        ),
    },
    {
        "item": (
            "Sorabji 2017: set metadata.reference_status='unverified — title-only "
            "shell; four-strands thesis authentic to Sorabji but this 2017 citation "
            "could not be confirmed'"
        ),
        "verdict": "SKIPPED — the citation was confirmed locally",
        "evidence": (
            "The chapter is held locally as ch. 3, pp. 49-66 of Seaford/Wilkins/"
            "Wright (eds.), Selfhood and the Soul (OUP 2017) — the file is catalogued "
            "under the editors, which is why a filename search on 'sorabji' misses "
            "it. Title, chapter number, page range, editors, publisher and ISBN all "
            "match the node. reference_status was set to 'verified 2026-08-16' "
            "instead, and the description was expanded from the bare title."
        ),
    },
    {
        "item": "Alexander De fato 19: 'ἐπὶ τίσιν οὐν αἱ κολάσεις' vs TLG 'οὖν'",
        "verdict": "OBSERVED, NOT APPLIED — outside the audited item list",
        "evidence": (
            "Noticed while verifying the Phalaris sentence. TLG0732 reads 'ἐπὶ τίσιν "
            "οὖν αἱ κολάσεις εὔλογοι'. Recorded in the node's verification_notes for "
            "a later item-by-item pass rather than fixed in this one."
        ),
    },
    {
        "item": "data/corpus/passages.jsonl carries the same 'futurumfiturum' defect",
        "verdict": "OBSERVED, NOT APPLIED — outside the declared file scope",
        "evidence": (
            "The Gellius NA VII.2.5 record in data/corpus/passages.jsonl (and the "
            "Perseus audit cache it came from) still reads 'quicquid futurumfiturum "
            "est'. This pass was scoped to data/kg/nodes.jsonl + publications.bib; "
            "the corpus copy needs the same correction in a corpus-scoped pass."
        ),
    },
    {
        "item": "data/kg/edges.jsonl carries 12 U+02BC occurrences",
        "verdict": "OBSERVED, NOT APPLIED — outside the declared file scope",
        "evidence": (
            "All 12 are 'ἐφʼ ἡμῖν' inside edge metadata notes. The pass was "
            "authorised to touch edges only for id retargeting, and no id was "
            "renamed, so edges were left byte-identical."
        ),
    },
)
