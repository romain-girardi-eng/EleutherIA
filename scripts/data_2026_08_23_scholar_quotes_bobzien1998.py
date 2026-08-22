"""Scholar-quote wave 1 — Bobzien 1998, "The Inadvertent Conception and Late
Birth of the Free-Will Problem", Phronesis 43/2, pp. 133-175.

Attaches ``metadata.quote_verbatim`` (+ ``quote_page``, ``quote_source``) to
existing scholarly_argument_bobzien_* nodes so the GraphRAG synthesis can quote
Bobzien's OWN words with a page reference instead of paraphrasing.

Every quote below was verified 2026-08-23 against BOTH:
  - the curated extraction: ~/Desktop/DOCTORAT/Doctorat SHAL/
    04_Littérature_secondaire/Extractions_articles/Bobzien_1998_Inadvertent.md
  - the raw full-text extraction of the article itself (same folder,
    01_Philosophie_antique/"Bobzien - 1998 - The Inadvertent Conception and
    Late Birth of the F.md"), whitespace-insensitively.

House rules: one quote per node, only unambiguous node<->quote matches; the
quote is copied byte-for-byte from the curated extraction (including the
printed article's own "what depends us" at p. 144 — the raw extraction shows
the same reading; we never edit a quotation). ``precondition_description`` must
be a substring of the node's current description at apply time, or the edit is
skipped and logged.
"""

SOURCE = (
    "Bobzien 1998, The Inadvertent Conception and Late Birth of the Free-Will "
    "Problem, Phronesis 43/2"
)

WAVE_STAMP = "scholar_quotes_2026_08_23"

EDITS = [
    {
        # Main thesis of the article (Abstract) — the node states exactly this.
        "node_id": "scholarly_argument_bobzien_origin_of_free_will_problem_in_0",
        "precondition_description": "origin of free-will problem in antiquity",
        "quote_verbatim": (
            "the 'discovery' of the problem of causal determinism and freedom "
            "of decision in Greek philosophy is the result of a mix-up of "
            "Aristotelian and Stoic thought in later antiquity; more "
            "precisely, a (mis-)interpretation of Aristotle's philosophy of "
            "deliberate choice and action in the light of Stoic theory of "
            "determinism and moral responsibility"
        ),
        "quote_page": "p. 133",
    },
    {
        # ἐλευθερία vs ἐφ' ἡμῖν — the node's claim verbatim in the article.
        "node_id": "scholarly_argument_bobzien_greek_terminology_for_freedom_1",
        "precondition_description": "Greek terminology for freedom",
        "quote_verbatim": (
            "ἐλευθερία played no role in the discussion of determinism and "
            "moral responsibility up to the 2nd century A.D. In particular, "
            "the term ἐλευθερία is *not* involved in the development of the "
            "concept of freedom to do otherwise. Rather it is the conceptual "
            "development of the phrase ἐφ' ἡμῖν that is pertinent here, and "
            "which has an altogether different history."
        ),
        "quote_page": "p. 135",
    },
    {
        # Sub-thesis 1: Alexander as first unambiguous evidence.
        "node_id": "scholarly_argument_bobzien_alexander_of_aphrodisias_as_fi_3",
        "precondition_description": (
            "Alexander of Aphrodisias as first evidence for free-will problem"
        ),
        "quote_verbatim": (
            "The earliest unambiguous evidence for the awareness of any kind "
            "of 'free-will problem' occurs in Alexander of Aphrodisias."
        ),
        "quote_page": "pp. 136-137",
    },
    {
        # Sub-thesis 2: no indeterminist two-sided ἐφ' ἡμῖν in the early Stoa.
        "node_id": "scholarly_argument_bobzien_chrysippus_and_early_stoics_on_1",
        "precondition_description": "Chrysippus and early Stoics on",
        "quote_verbatim": (
            "The early Stoics, in particular Chrysippus, clearly did not have "
            "an indeterminist two-sided conception of what depends on us."
        ),
        "quote_page": "p. 142",
    },
    {
        # Sub-thesis 3: Aristotle's ἐφ' ἡμῖν does not entail indeterminism.
        # "what depends us" is the printed article's own reading (verified in
        # the raw extraction) — reproduced verbatim, never corrected.
        "node_id": "scholarly_argument_bobzien_aristotle_s_conception_of_2",
        "precondition_description": "Aristotle's conception of",
        "quote_verbatim": (
            "Aristotle's concept of what depends us does not entail "
            "indeterminism. We have no reason to assume that he has anything "
            "more in mind than that the things that depends on us are those "
            "which on a generic level it is possible for us to do and not to "
            "do, given that we are not externally prevented from doing them."
        ),
        "quote_page": "p. 144",
    },
    {
        # Sub-thesis 5: the historical marginality of freedom-to-do-otherwise.
        "node_id": "scholarly_argument_bobzien_historical_marginality_of_libe_7",
        "precondition_description": "historical marginality of libertarian freedom",
        "quote_verbatim": (
            "at his time Alexander is almost an isolated case, and that "
            "concepts of freedom to do otherwise are a rather marginal "
            "phenomenon without a clear philosophical context."
        ),
        "quote_page": "p. 167",
    },
]
