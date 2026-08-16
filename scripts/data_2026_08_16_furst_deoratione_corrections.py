"""Authored data for the 2026-08-16 Fürst / De oratione node corrections.

Companion data module for `apply_2026_08_16_furst_deoratione_corrections.py`.
It carries four independent corrections mandated by an academic audit of the
Fürst-2022 reception nodes and of the Origen *De oratione* 6 passage node:

1. `scholarly_argument_f_rst_origen_s_libertarian_compatibi_4` — the node
   summarised Fürst's ch. V 3 ("Libertarische Deutung des biblischen
   Determinismus") under the ch. VI 4 title ("Kompatibilistischer
   Libertarismus") and flattened Fürst's deliberately suspended verdict into a
   single thesis. Description, `stance`, `page_range` and `verified_reference`
   are rewritten from the book itself.

2. `concept_kompatibilistischer_libertarismus_origenian` and
   `argument_furst_2022_kompatibilistischer_libertarismus` — both asserted that
   the Origenian libertarianism is compatible with "the Stoic chain of (physical)
   causes". Fürst says the opposite in as many words (p. 288): "Origenes
   konzipierte keinen Kausaldeterminismus, in den Handlungen, für die Menschen
   die Ursache sind, eingereiht werden – das wäre das stoische Modell." The
   claim is replaced by what Fürst actually lists, and his suspended verdict is
   appended. `C. M. Fürst` → `A. Fürst`.

3. `passage_origen_de_orat_6` — ACADEMIC-INTEGRITY violation. The Greek printed
   in the description was a modern recomposition (0 hits in the local TLG E
   corpus, accent-insensitive, via `scripts/tlg_search.py`) while the node
   claimed "GCS 3 Koetschau". It is replaced by the verbatim text of
   De oratione 6,3 copied byte-for-byte out of the local TLG extract
   `02_Corpus/TLG/TLG_tlg2042_De_oratione_6_3.txt` (TLG E tlg2042.008 =
   GCS Orig. 2, p. 313 Koetschau) and re-verified with two distinctive spans
   (1 hit each, Origen only). Its twin `passage_origen_de_orat_6_en`, whose
   description had been left as punctuation debris by an earlier
   Greek-stripping pass, is restored to a plain English rendering.

4. `passage_origen_philocalia_21_23` — the label advertised "Greek text" while
   the payload is the French translation printed in SC 268. Relabelled.

Zero-fabrication rule for this module
-------------------------------------
Every ancient-language string introduced here was copied out of a named local
file and re-verified before being written:

* the De oratione 6,3 span: copied from
  `.../02_Corpus/TLG/TLG_tlg2042_De_oratione_6_3.txt`, lines ..6.3.5–..6.3.13,
  line-joined, no other edit; two distinctive substrings re-checked with
  `scripts/tlg_search.py search … --authors 2042` → 1 hit each;
* `εἱρμός`, `πρόγνωσις`, `τὸ ἐφ' ἡμῖν`: lemma forms of words standing verbatim
  in that same span (`τὸν εἱρμὸν`, `τῆς προγνώσεως`, `τῶν ἐφ' ἡμῖν`).

The unattested Greek that is removed is archived, clearly marked, under
`metadata.removed_unattested_text` — it is never re-asserted as a quotation.

Every German quotation below was re-verified verbatim in the local extraction
`04_Littérature_secondaire/05_Origene/Alfons Fürst - Wege zur Freiheit_ …
Mohr Siebeck (2022).md` (the file soft-hyphenates across line breaks, so the
greps were run on the de-hyphenated context, quoted in the `#` comments).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Verbatim primary text (item 3)
# ---------------------------------------------------------------------------
# Origen, De oratione 6,3 — GCS Orig. 2, p. 313 Koetschau.
# Source file (byte-exact, lines ..6.3.5 → ..6.3.13, line-joined):
#   ~/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/TLG/TLG_tlg2042_De_oratione_6_3.txt
# TLG re-verification 2026-08-16 (scripts/tlg_search.py, --authors 2042):
#   'οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης'  → 1 hit  (TLG2042 @2486744)
#   'ἀπολοῦμεν τὸ τάδε τινὰ ἐνεργήσειν'              → 1 hit  (TLG2042 @2486983)
DE_ORAT_6_3_GREEK = (
    "καὶ ἐν πᾶσιν, οἷς προδιατάσσεται ὁ θεὸς ἀκολούθως οἷς ἑώρακε περὶ ἑκάστου "
    "ἔργου τῶν ἐφ' ἡμῖν, προδιατέτακται κατ' ἀξίαν ἑκάστῳ κινήματι τῶν ἐφ' ἡμῖν "
    "τὸ καὶ ἀπὸ τῆς προνοίας αὐτῷ ἀπαντησόμενον ἔτι δὲ καὶ κατὰ τὸν εἱρμὸν τῶν "
    "ἐσομένων συμβησόμενον, οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης τοῖς "
    "ἐσομένοις πᾶσι καὶ ἐκ τοῦ ἐφ' ἡμῖν κατὰ τὴν ὁρμὴν ἡμῶν ἐνεργηθησομένοις. "
    "εἰ γὰρ καὶ καθ' ὑπόθεσιν μὴ γινώσκοι ὁ θεὸς τὰ ἐσόμενα, οὐ παρὰ τοῦτο "
    "ἀπολοῦμεν τὸ τάδε τινὰ ἐνεργήσειν καὶ τάδε θελήσειν·"
)

DE_ORAT_6_3_ENGLISH = (
    "God's foreknowledge is not the cause of all the things that will be, "
    "including those effected from what is up to us according to our impulse; "
    "even if, per hypothesis, God did not know the future, we would not thereby "
    "lose the power to act and to will."
)

# The two runs removed from passage_origen_de_orat_6. Both are modern
# recompositions: `scripts/tlg_search.py` (whole corpus, accent-insensitive)
# returns 0 hits for each, although the node labelled them "GCS 3 Koetschau".
REMOVED_UNATTESTED_RUNS = [
    "Ἡ πρόγνωσις τοῦ θεοῦ οὐκ ἔστιν αἰτία πάντων τῶν ἐσομένων καὶ τῶν ἀπ' "
    "αὐτεξουσίου κινήσεως ἡμῶν ἀποβησομένων.",
    "οὐχ ὅτι γινώσκει ὁ θεὸς τὸ ἐσόμενον, διὰ τοῦτο καὶ ἔσται· ἀλλ' ὅτι "
    "ἐσόμενόν ἐστι, διὰ τοῦτο γινώσκεται ὑπὸ τοῦ θεοῦ πρὸ τοῦ γενέσθαι.",
    # also removed from metadata.key_terms (0 TLG hits):
    "ἀπ' αὐτεξουσίου κινήσεως",
]

DE_ORAT_6_OLD_DESCRIPTION = (
    "Crucial distinction for reconciling foreknowledge and freedom. Greek (GCS 3 "
    "Koetschau): [6.1] Ἡ πρόγνωσις τοῦ θεοῦ οὐκ ἔστιν αἰτία πάντων τῶν ἐσομένων "
    "καὶ τῶν ἀπ' αὐτεξουσίου κινήσεως ἡμῶν ἀποβησομένων. (\"GOD'S PRESCIENCE IS "
    "NOT THE CAUSE of all future events or of those resulting from our "
    'self-determining motion.") [6.2] οὐχ ὅτι γινώσκει ὁ θεὸς τὸ ἐσόμενον, διὰ '
    "τοῦτο καὶ ἔσται· ἀλλ' ὅτι ἐσόμενόν ἐστι, διὰ τοῦτο γινώσκεται ὑπὸ τοῦ θεοῦ "
    'πρὸ τοῦ γενέσθαι. ("It is NOT BECAUSE God knows that it will be, BUT '
    'BECAUSE it will be, that God knows it beforehand.") Astronomer analogy: '
    "predicting eclipse doesn't cause it. Source: GCS 3."
)

DE_ORAT_6_EN_OLD_DESCRIPTION = (
    "Crucial distinction for reconciling foreknowledge and freedom. Greek (GCS 3 "
    "Koetschau): [6.1] ' . (\"GOD'S PRESCIENCE IS NOT THE CAUSE of all future "
    'events or of those resulting from our self-determining motion.") [6.2] , · '
    "' , . (\"It is NOT BECAUSE God knows that it will be, BUT BECAUSE it will "
    'be, that God knows it beforehand.") Astronomer analogy: predicting eclipse '
    "doesn't cause it. Source: GCS 3."
)

DE_ORAT_6_NOTE = (
    "For the reversed order of knowing ('not because it is known does it happen, "
    "but because it will happen it is known') see Philoc. 23,8 = in Gen. frg. D "
    "7,8 (OWD 1/1, 84) — do not attribute that sentence to De oratione."
)

# ---------------------------------------------------------------------------
# 1. scholarly_argument_f_rst_origen_s_libertarian_compatibi_4
# ---------------------------------------------------------------------------
# Verified verbatim in the local Fürst 2022 extraction (de-hyphenated):
#   p. 289: "…bewegte, ist sein Freiheitskonzept ein Kompatibilismus. Allerdings
#            propagierte er zugleich einen Libertarismus, wie man ihn sich
#            stärker kaum vorstellen kann."
#   p. 289: "…war Origenes ein Libertarist, doch ein Libertarist mit
#            kompatibilistischen Neigungen."
#   p. 289: "Wofür auch immer man eher votiert, mehr für Libertarismus, mehr für
#            Kompatibilismus, aber sicher nicht für Determinismus…"
#   p. 288: "Origenes konzipierte keinen Kausaldeterminismus, in den Handlungen,
#            für die Menschen die Ursache sind, eingereiht werden – das wäre das
#            stoische Modell. Er dachte vielmehr an ein Gewebe von miteinander
#            zusammenhängenden Entscheidungen und Handlungen freier Wesen, die
#            von Gott, einem seinerseits freien Wesen, … gebracht werden."
#   p. 286 f.: εἱρμός quoted from orat. 6,3 (GCS Orig. 2, 313) at 283 n. 101 and
#            287 n. 107, then explicitly re-semanticised at 287.
FURST_ARG_DESCRIPTION = (
    "Origen's kompatibilistischer Libertarismus — Fürst coins 'kompatibilistischer "
    "Libertarismus' (compatibilist libertarianism) as a deliberately double-edged "
    "characterization of Origen. Insofar as Origen frames freedom within the "
    "teleological order of divine providence — on the ground of what Fürst calls "
    "biblical compatibilism — his concept of freedom is a compatibilism ('ist sein "
    "Freiheitskonzept ein Kompatibilismus'); yet he simultaneously propagates a "
    "libertarianism 'as strong as one can imagine' ('einen Libertarismus, wie man "
    "ihn sich stärker kaum vorstellen kann'), making freedom the ontological "
    "principle of rational being. Fürst's own verdict is deliberately suspended: "
    "Origen was 'ein Libertarist, doch ein Libertarist mit kompatibilistischen "
    "Neigungen', and 'wofür auch immer man eher votiert, mehr für Libertarismus, "
    "mehr für Kompatibilismus, aber sicher nicht für Determinismus'. The "
    "compatibility concerns determined aspects of reality (divine foreknowledge, "
    "providential pre-arrangement, reliable regularities) — NOT the Stoic causal "
    "chain, which Origen expressly does not adopt ('Origenes konzipierte keinen "
    "Kausaldeterminismus … das wäre das stoische Modell'): the Stoic term εἱρμός "
    "is retained but re-semanticized as a web (Gewebe) of interconnected free "
    "decisions ordered by a God who is himself free. Distinct from (though "
    "prepared by) Fürst's separate account of Origen's libertarian exegesis of "
    "biblical determinism (Pauline election, Pharaoh) in ch. V.3."
)

FURST_ARG_STANCE = (
    "Coins 'kompatibilistischer Libertarismus' as a deliberately double-edged "
    "characterization of Origen: a compatibilism insofar as freedom is framed "
    "within the teleological order of divine providence (Fürst's 'biblical "
    "compatibilism'), yet at the same time a libertarianism 'wie man ihn sich "
    "stärker kaum vorstellen kann', freedom being the ontological principle of "
    "rational being. The verdict is left suspended — 'ein Libertarist, doch ein "
    "Libertarist mit kompatibilistischen Neigungen' — and the compatibility is "
    "with determined aspects of reality (foreknowledge, providential "
    "pre-arrangement, reliable regularities), expressly not with a Stoic causal "
    "chain."
)

FURST_ARG_VERIFIED_REFERENCE = (
    "Fürst, Wege zur Freiheit (Mohr Siebeck 2022), Kap. VI 4 'Kompatibilistischer "
    "Libertarismus', pp. 282-290 (verdict pp. 289-290); libertarian exegesis of "
    "biblical determinism = Kap. V 3, pp. 217-239; Origen, orat. 6,3 (GCS Orig. 2, "
    "313); princ. II 1,2 (GCS Orig. 5, 107 f.)."
)

# ---------------------------------------------------------------------------
# 2. The two "Stoic chain of causes" nodes
# ---------------------------------------------------------------------------
# Fürst 2022, 287: "Allerdings verwendete Origenes zwar diesen stoischen Begriff
#   [εἱρμός], füllte ihn aber mit einer anderen Bedeutung."
# Fürst 2022, 288: "Origenes konzipierte keinen Kausaldeterminismus … das wäre
#   das stoische Modell. Er dachte vielmehr an ein Gewebe von miteinander
#   zusammenhängenden Entscheidungen und Handlungen freier Wesen, die von Gott,
#   einem seinerseits freien Wesen … in einen sinnvollen Zusammenhang gebracht
#   werden."
# Fürst 2022, 290: "…dass aber dieser Libertarismus mit determinierten Aspekten
#   der Wirklichkeit kompatibel blieb."
STOIC_CHAIN_FIX_EN = (
    "compatible with certain determined aspects of reality (mit determinierten "
    "Aspekten der Wirklichkeit): divine foreknowledge, providential pre-arrangement, "
    "and reliable regularities of the world — expressly NOT the Stoic chain of "
    "physical causes, which Origen does not adopt: he retains the Stoic term "
    "εἱρμός but re-semanticizes it as a web (Gewebe) of interconnected free "
    "decisions of free beings, ordered by a God who is himself free "
    "(Fürst 2022, 286-288)."
)

STOIC_CHAIN_FIX_FR = (
    "compatible avec certains aspects déterminés de la réalité (mit determinierten "
    "Aspekten der Wirklichkeit) : préscience divine, pré-arrangement "
    "providentiel et régularités fiables du monde — expressément PAS la chaîne "
    "stoïcienne des causes physiques, qu'Origène n'adopte pas : il conserve "
    "le terme stoïcien εἱρμός mais le resémantise en un tissu (Gewebe) de "
    "décisions libres interconnectées d'êtres libres, ordonnées par un Dieu "
    "lui-même libre (Fürst 2022, 286-288)."
)

# Fürst 2022, 289-290 (verbatim in the local extraction, de-hyphenated).
SUSPENDED_VERDICT_EN = (
    " Fürst's verdict remains deliberately suspended: 'ein Libertarist, doch ein "
    "Libertarist mit kompatibilistischen Neigungen' (p. 289); he even closes by "
    "suggesting compatibilism may be 'das tragfähigste Konzept' (p. 290), the real "
    "question being which concept of compatibilism one holds — Origen's differing "
    "from the Stoic in asking how free human self-determination coheres with the "
    "providential action of a God who is himself free."
)

SUSPENDED_VERDICT_FR = (
    " Le verdict de Fürst reste délibérément suspendu : « ein Libertarist, "
    "doch ein Libertarist mit kompatibilistischen Neigungen » (p. 289) ; "
    "il va jusqu'à suggérer, en conclusion, que le compatibilisme est peut-être "
    "« das tragfähigste Konzept » (p. 290), la vraie question étant de "
    "savoir quel concept de compatibilisme l'on soutient — celui d'Origène "
    "différant du stoïcien en ce qu'il demande comment la libre autodétermination "
    "humaine s'accorde avec l'action providentielle d'un Dieu lui-même libre."
)

# ---------------------------------------------------------------------------
# Field rewrites: (old, new) spans, each required to occur exactly once
# ---------------------------------------------------------------------------
FIELD_REWRITES: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "concept_kompatibilistischer_libertarismus_origenian": {
        # The em-dash list is the audited claim; Fürst 2022, 288 denies the first item.
        "description": (
            (
                "while remaining compatible with certain determined aspects of "
                "reality—the Stoic chain of causes, divine foreknowledge, providence.",
                "while remaining " + STOIC_CHAIN_FIX_EN,
            ),
        ),
        "metadata.description_en": (
            (
                "while remaining compatible with certain determined aspects of "
                "reality—the Stoic chain of causes, divine foreknowledge, providence.",
                "while remaining " + STOIC_CHAIN_FIX_EN,
            ),
        ),
        "metadata.description_fr": (
            (
                "tout en restant compatible avec des aspects déterminés de la "
                "réalité — chaîne stoïcienne des causes, préscience divine, "
                "providence.",
                "tout en restant " + STOIC_CHAIN_FIX_FR,
            ),
        ),
        # audit: the initial is wrong — the author is Alfons Fürst.
        "metadata.verified_reference": (("C. M. Fürst,", "A. Fürst,"),),
    },
    "argument_furst_2022_kompatibilistischer_libertarismus": {
        "description": (
            (
                "compatible with certain aspects of reality: the Stoic chain of "
                "physical causes, divine foreknowledge, ordered providence.",
                STOIC_CHAIN_FIX_EN,
            ),
        ),
        "metadata.description_en": (
            (
                "compatible with certain aspects of reality: the Stoic chain of "
                "physical causes, divine foreknowledge, ordered providence.",
                STOIC_CHAIN_FIX_EN,
            ),
        ),
        "metadata.description_fr": (
            (
                "compatible avec des aspects déterminés de la réalité : chaîne "
                "stoïcienne des causes physiques, préscience divine, providence "
                "ordonnée.",
                STOIC_CHAIN_FIX_FR,
            ),
        ),
    },
}

# Text appended once at the end of a field (idempotent: skipped if already there).
FIELD_APPENDS: dict[str, dict[str, str]] = {
    "concept_kompatibilistischer_libertarismus_origenian": {
        "description": SUSPENDED_VERDICT_EN,
        "metadata.description_en": SUSPENDED_VERDICT_EN,
        "metadata.description_fr": SUSPENDED_VERDICT_FR,
    },
    "argument_furst_2022_kompatibilistischer_libertarismus": {
        "description": SUSPENDED_VERDICT_EN,
        "metadata.description_en": SUSPENDED_VERDICT_EN,
        "metadata.description_fr": SUSPENDED_VERDICT_FR,
    },
}

# Whole-field replacements (old value recorded in the review file).
FIELD_SETS: dict[str, dict[str, str]] = {
    "scholarly_argument_f_rst_origen_s_libertarian_compatibi_4": {
        "description": FURST_ARG_DESCRIPTION,
        "metadata.stance": FURST_ARG_STANCE,
        "metadata.verified_reference": FURST_ARG_VERIFIED_REFERENCE,
        # ch. VI 4 runs 282-290; "187-282" was the span of the ch. V material the
        # node had actually summarised.
        "metadata.page_range": "282-290",
    },
    "passage_origen_de_orat_6": {
        "description": (
            "Origen's classic statement that divine foreknowledge is not the cause "
            "of what comes to be: God pre-arranges everything in accordance with "
            "what he has foreseen of each act that is up to us (τὸ ἐφ' ἡμῖν), and "
            "the εἱρμός of future events follows, without his foreknowledge being "
            "the cause of them. Greek (Origen, De oratione 6,3 = GCS Orig. 2, p. "
            "313 Koetschau; verbatim from TLG E tlg2042.008): «"
            + DE_ORAT_6_3_GREEK
            + '» English: "'
            + DE_ORAT_6_3_ENGLISH
            + '"'
        ),
        "metadata.note": DE_ORAT_6_NOTE,
        "metadata.work_title": "De Oratione",
        "metadata.reference": "De Orat. 6,3",
        "metadata.source_verified": (
            "GCS Orig. 2, p. 313 (Koetschau 1899); Greek copied byte-exact from the "
            "local TLG E extract TLG_tlg2042_De_oratione_6_3.txt on 2026-08-16"
        ),
        "metadata.external_edition": (
            "GCS Orig. 2 (Koetschau 1899): Origenes Werke II, De oratione, p. 313"
        ),
        "metadata.greek_text_excerpt": (
            "οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης τοῖς ἐσομένοις πᾶσι"
        ),
        "metadata.doxographical_source": "scholarly_critical_edition",
        "metadata.doxographical_confidence": "high",
        "metadata.citation_verdict": "corrected",
        "metadata.verified_reference": (
            "Origen, De oratione 6,3 (GCS Orig. 2, 313 Koetschau) = TLG tlg2042.008; "
            "Greek re-verified 2026-08-16 against the local TLG E corpus with two "
            "distinctive spans (1 hit each, Origen only). Cited for this exact point "
            "by Fürst, Wege zur Freiheit (2022) 283 n. 101 and 287 n. 107."
        ),
    },
    "passage_origen_de_orat_6_en": {
        "description": (
            DE_ORAT_6_3_ENGLISH
            + " (Origen, De oratione 6,3 = GCS Orig. 2, p. 313 Koetschau; English "
            "rendering of the verbatim Greek restored to passage_origen_de_orat_6 "
            "on 2026-08-16.)"
        ),
        "metadata.work_title": "De Oratione",
        "metadata.source_language": "grc",
        "metadata.translation_source": (
            "Re-rendered 2026-08-16 from the verbatim Greek of De oratione 6,3 "
            "(GCS Orig. 2, 313) restored to passage_origen_de_orat_6. Supersedes the "
            "claude-opus-4-6 batch translation, whose stored text had been reduced to "
            "punctuation debris by an earlier Greek-stripping pass."
        ),
        "metadata.citation_verdict": "corrected",
    },
    "passage_origen_philocalia_21_23": {
        "metadata.section_label": (
            "Universalist horizon — French translation (SC 268 Crouzel–Simonetti); "
            "Greek not yet ingested for this section"
        ),
        "metadata.language": "fra",
        "metadata.language_note": (
            "The stored payload is the French translation of Philocalia 21.23 "
            "(= De Princ. III 1,23) printed in SC 268 (Crouzel–Simonetti, 'Extraits "
            "grecs' companion volume), NOT Greek. Philocalia 21 remains the "
            "principal Greek witness for De Princ. III 1, and the Greek of §23 is "
            "available in the same local SC 268 extract file, but it has not been "
            "ingested into this node."
        ),
        "metadata.citation_verdict": "corrected",
    },
}

# `metadata.citation_verified` is set to True on every node that receives a
# verdict above; kept separate so the applier can type it as a bool.
CITATION_VERIFIED_TRUE = (
    "passage_origen_de_orat_6",
    "passage_origen_de_orat_6_en",
    "passage_origen_philocalia_21_23",
)

LABEL_REWRITES: dict[str, tuple[str, str]] = {
    "passage_origen_philocalia_21_23": (
        "Origen, Philocalia 21.23: Universalist horizon — Greek text "
        "(Philocalia 21.23) [= De Princ. III.1.23]",
        "Origen, Philocalia 21.23: Universalist horizon — French translation "
        "(SC 268 Crouzel–Simonetti); Greek not yet ingested for this section "
        "[= De Princ. III.1.23]",
    ),
}

# Structured archive of the removed recomposed Greek (never re-asserted as a
# quotation; kept only so the correction is auditable).
REMOVED_TEXT_ARCHIVE: dict[str, dict] = {
    "passage_origen_de_orat_6": {
        "reason": (
            "Recomposed (not attested) Greek presented as 'GCS 3 Koetschau'. "
            "scripts/tlg_search.py, whole local TLG E corpus, accent- and "
            "sigma-insensitive: 0 hits for each run, 2026-08-16."
        ),
        "removed_on": "2026-08-16",
        "runs": REMOVED_UNATTESTED_RUNS,
        "previous_description": DE_ORAT_6_OLD_DESCRIPTION,
        "replaced_by": (
            "Verbatim De oratione 6,3 (GCS Orig. 2, 313 Koetschau) from the local "
            "TLG E extract TLG_tlg2042_De_oratione_6_3.txt"
        ),
    },
    "passage_origen_de_orat_6_en": {
        "reason": (
            "Description was the Greek node's text with the Greek runs stripped, "
            "leaving punctuation debris; the node is a translation node and now "
            "carries a plain English rendering."
        ),
        "removed_on": "2026-08-16",
        "previous_description": DE_ORAT_6_EN_OLD_DESCRIPTION,
    },
}

# Element-level list edits on metadata.
LIST_SETS: dict[str, dict[str, list]] = {
    "passage_origen_de_orat_6": {
        # "ἀπ' αὐτεξουσίου κινήσεως" came from the recomposed text: 0 TLG hits.
        # The replacements are lemma forms of words standing verbatim in the
        # restored span (τῆς προγνώσεως / τὸν εἱρμὸν / τῶν ἐφ' ἡμῖν / τὴν ὁρμὴν).
        "key_terms": ["πρόγνωσις", "εἱρμός", "τὸ ἐφ' ἡμῖν", "ὁρμή"],
    },
}

# Provenance notes appended to metadata.verification_notes.
VERIFICATION_NOTES: dict[str, tuple[str, ...]] = {
    "scholarly_argument_f_rst_origen_s_libertarian_compatibi_4": (
        "[Vérif. 2026-08-16 : the node summarised Fürst ch. V 3 "
        "('Libertarische Deutung des biblischen Determinismus', pp. 217-239) under "
        "the ch. VI 4 title, and flattened Fürst's suspended verdict into a single "
        "thesis. Description and stance rewritten from the book (Kap. VI 4, "
        "pp. 282-290; verdict pp. 289-290); page_range 187-282 → 282-290. "
        "Previous description: \"Origen's libertarian compatibilism — Develops the "
        "concept of 'kompatibilistischer Libertarismus' (compatibilist "
        "libertarianism) for Origen: Origen maintains genuine libertarian free will "
        "(autexousion) as foundational for Christian theology while also "
        "interpreting biblical determinism (especially Pauline passages on divine "
        "election) in ways that preserve rather than negate human "
        "self-determination\". Previous verified_reference cited 'ch. V §4 … "
        "(p. 282)', which conflated the two chapters.]",
    ),
    "concept_kompatibilistischer_libertarismus_origenian": (
        "[Vérif. 2026-08-16 : the description listed 'the Stoic chain of causes' "
        "among the determined aspects Origen's freedom stays compatible with. Fürst "
        "2022, 288 denies exactly that: 'Origenes konzipierte keinen "
        "Kausaldeterminismus, in den Handlungen, für die Menschen die Ursache sind, "
        "eingereiht werden – das wäre das stoische Modell.' The Stoic term εἱρμός is "
        "kept but re-semanticised (287) as a 'Gewebe' of interconnected free "
        "decisions (288). Claim corrected in description / description_en / "
        "description_fr; Fürst's suspended verdict (289-290) appended; author "
        "initials 'C. M. Fürst' → 'A. Fürst'.]",
    ),
    "argument_furst_2022_kompatibilistischer_libertarismus": (
        "[Vérif. 2026-08-16 : same correction as "
        "concept_kompatibilistischer_libertarismus_origenian — 'the Stoic chain of "
        "physical causes' is not among the determined aspects Fürst names; he "
        "expressly rules out a Kausaldeterminismus (2022, 288). Corrected in "
        "description / description_en / description_fr, with the suspended verdict "
        "of pp. 289-290 appended.]",
    ),
    "passage_origen_de_orat_6": (
        "[Vérif. 2026-08-16 : ACADEMIC-INTEGRITY correction. The Greek printed in "
        "the description was a modern recomposition — 0 hits in the whole local "
        "TLG E corpus (scripts/tlg_search.py, accent-insensitive) — although the "
        "node claimed 'GCS 3 Koetschau'. Replaced by the verbatim text of De "
        "oratione 6,3 (GCS Orig. 2, p. 313) copied byte-exact from the local TLG "
        "extract 02_Corpus/TLG/TLG_tlg2042_De_oratione_6_3.txt and re-verified with "
        "two distinctive spans (1 hit each, TLG2042 only). The removed runs are "
        "archived under metadata.removed_unattested_text. metadata.work_title said "
        "'Contra Celsum' → 'De Oratione'. The sentence 'not because it is known does "
        "it happen…' does not stand in De oratione: it is Philoc. 23,8 = in Gen. "
        "frg. D 7,8 (OWD 1/1, 84), per Fürst 2022, 285 n. 105 — recorded in "
        "metadata.note.]",
    ),
    "passage_origen_de_orat_6_en": (
        "[Vérif. 2026-08-16 : the translation node's description was the Greek "
        "node's text with the Greek runs stripped out, leaving punctuation debris "
        "(\"[6.1] ' . (…) [6.2] , · ' , .\"). Replaced by a plain English rendering "
        "of the restored, TLG-verbatim De oratione 6,3. Old text archived under "
        "metadata.removed_unattested_text; the three edges touching this node "
        "(translation_of, authored_by, part_of) are left intact.]",
    ),
    "passage_origen_philocalia_21_23": (
        "[Vérif. 2026-08-16 : label and section_label advertised 'Greek text "
        "(Philocalia 21.23)' while the stored description is the French translation "
        "printed in SC 268 (Crouzel–Simonetti, 'Extraits grecs' companion) — "
        "verified verbatim in the local file 02_Corpus/Sources chrétiennes txt/"
        "03_Origene/source/SC268_Origenes_Traite_des_Principes_Extraits_grecs_"
        "livre_3_source.txt, §[liv. 3, chap. 1, par. 23], TRADUCTION block. "
        "metadata.language 'grc' → 'fra'. NB: the audit brief named SC 226 (Junod) "
        "as the source of the French; the local evidence points to SC 268 "
        "(Crouzel–Simonetti) instead — the node's own junod_sc226_rtf_status note "
        "already records that SC 226's OCR export lacks Philocalia 21. The Greek of "
        "§23 does exist in that same SC 268 file but has not been ingested here.]",
    ),
}
