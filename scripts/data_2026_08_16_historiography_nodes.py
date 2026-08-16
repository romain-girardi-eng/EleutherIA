"""Data for the 2026-08-16 historiography acquisition (Origen + Augustine reception).

Grounding rule applied throughout: a scholar's POSITION is stated here only when
it is supported by text that was actually READ in the local library — either the
scholar's own words quoted inside a held work, or an explicit characterisation of
their thesis by a held author.  Where that evidence is missing the node is a
bibliographic shell and says so in `reference_status`.

None of the six monographs/articles below is held locally.  Every position
statement is therefore *reported*, and each carries the verbatim anchor and the
file + locator it was read at.

Local witnesses used
--------------------
F22   04_Littérature_secondaire/05_Origene/Alfons Fürst - Wege zur Freiheit_
      Menschliche Selbstbestimmung von Homer bis Origenes-Mohr Siebeck (2022).md
      (page markers in the .md; printed pages given below)
F21   04_Littérature_secondaire/05_Origene/fuerst_2021_perspectives_origen_adamantiana21.pdf
GIB   04_Littérature_secondaire/06_Patristique/Gibbons - 2016 - HUMAN AUTONOMY....md
BEL   04_Littérature_secondaire/05_Origene/Belcastro_Predestinazione_Origene.md
TOL   04_Littérature_secondaire/01_Philosophie_antique/Tolan - 2021 - ...ἡγεμονικόν....md
IFB   04_Littérature_secondaire/05_Origene/Kobusch_2023_Metaphysik_der_Freiheit_Adam28_review_IFB.pdf
WET   04_Littérature_secondaire/07_Libre_arbitre_theologie/wetzel_1992_augustine_limits_virtue.pdf
      (the PDF is structurally corrupt with an empty OCR layer; it was rebuilt and
      re-OCR'd for this wave — quotations are OCR and are flagged as such)
BAR   04_Littérature_secondaire/03_Paul/Barclay_2015_Paul_and_the_Gift.md
RAM   08_Présentations/Colloques/Origeniana_XIV_Boston_2026/_acquisitions/
      ramelli_2021_origen_augustine_paradoxical_reception.txt
GOR   04_Littérature_secondaire/03_Paul/Gorday_Principles_Patristic_Exegesis_Romans9-11_1983.md
"""

from __future__ import annotations

WAVE = "historiography_acquisition_2026_08_16"

_NOT_HELD = (
    "the work itself is NOT held in the local library; the position below is "
    "reported from held witnesses, each quoted verbatim in `grounding`"
)

# --------------------------------------------------------------------------
# New nodes
# --------------------------------------------------------------------------

NEW_NODES: list[dict] = [
    # ---- Benjamins ------------------------------------------------------
    {
        "id": "scholar_benjamins_hendrik_s",
        "label": "Hendrik S. Benjamins",
        "type": "person",
        "period": "Contemporary",
        "role": "scholar",
        "school": None,
        "description": (
            "Dutch patristic scholar; author of Eingeordnete Freiheit. Freiheit "
            "und Vorsehung bei Origenes (Supplements to Vigiliae Christianae 28), "
            "Leiden: Brill, 1994 — the standard monograph on the articulation of "
            "human freedom and divine providence in Origen. Fürst 2022 identifies "
            "the problem of that book as whether Origen's thoroughly libertarian "
            "conception does not in the end issue in a determinism."
        ),
        "metadata": {
            "role": "scholar",
            "surname": "Benjamins",
            "given_names": "Hendrik S.",
            "wave": WAVE,
            "key_work": (
                "Eingeordnete Freiheit. Freiheit und Vorsehung bei Origenes "
                "(SVigChr 28), Leiden: Brill, 1994"
            ),
            "specialty": "Origen, providence and freedom, patristic exegesis",
            "source_rank": (
                "person node derived from three independent held witnesses "
                "(Fürst 2022, Gibbons 2016, Belcastro) — " + _NOT_HELD
            ),
            "reference_status": (
                "position sourced from held discussions; monograph not collated"
            ),
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Hendrik S. Benjamins, Eingeordnete Freiheit. Freiheit und "
                "Vorsehung bei Origenes (Supplements to Vigiliae Christianae 28), "
                "Leiden: Brill, 1994. Bibliographic entry read verbatim in Fürst "
                "2022 Literaturverzeichnis, printed p. 302: 'Benjamins, Hendrik "
                "S., Eingeordnete Freiheit. Freiheit und Vorsehung bei Origenes "
                "(SVigChr 28), Leiden 1994.'"
            ),
        },
    },
    {
        "id": "pub_benjamins_1994_eingeordnete_freiheit",
        "label": "Eingeordnete Freiheit. Freiheit und Vorsehung bei Origenes",
        "type": "publication",
        "period": "Contemporary",
        "role": None,
        "school": None,
        "description": (
            "H. S. Benjamins, Eingeordnete Freiheit. Freiheit und Vorsehung bei "
            "Origenes (SVigChr 28), Leiden: Brill, 1994. Reported thesis, on the "
            "converging testimony of three held witnesses: freedom and providence "
            "are the systematic core of Origen's theology (Benjamins p. 1, quoted "
            "by Belcastro: 'Die zwei Themen der menschlichen Freiheit und "
            "göttlichen Vorsehung bilden den Kern der Systematik der Theologie "
            "des Origenes'); human action is not determined by prior causes — as "
            "in Alexander of Aphrodisias — yet God can use his foreknowledge of "
            "human action to arrange for the restoration of all human beings "
            "(Gibbons 2016 n. 3); the resulting problem, which Fürst 2022 names "
            "as the subject of the book, is whether so thoroughly libertarian a "
            "conception does not end in a determinism. The title's 'eingeordnete' "
            "Freiheit names that integration of free acts into a providential "
            "order. NOT HELD LOCALLY: no claim here rests on a reading of the "
            "monograph itself."
        ),
        "metadata": {
            "type": "book",
            "year": 1994,
            "author": "Hendrik S. Benjamins",
            "author_id": "scholar_benjamins_hendrik_s",
            "title": "Eingeordnete Freiheit. Freiheit und Vorsehung bei Origenes",
            "series": "Supplements to Vigiliae Christianae 28",
            "publisher": "Brill",
            "place": "Leiden",
            "language": "de",
            "wave": WAVE,
            "source_rank": "monograph, Brill series volume — " + _NOT_HELD,
            "reference_status": (
                "thesis reported from three independent held witnesses; the "
                "monograph itself was not collated"
            ),
            "held_locally": False,
            "grounding": [
                {
                    "witness": "Fürst 2022, printed p. 283, n. 100 (.md ll. 10176-10179)",
                    "quote_de": (
                        "Diese Problematik, auf die Geyer, Geschichtsphilosophie "
                        "bei Origenes 18, hinweist, ist das Thema der Studie von "
                        "Benjamins, Eingeordnete Freiheit, bes. 71-121."
                    ),
                    "context_de": (
                        "taucht das Problem auf, ob nicht auch dieses durch und "
                        "durch libertarische Konzept am Ende in einen "
                        "Determinismus mündet."
                    ),
                    "supports": (
                        "the book's subject is whether Origen's libertarianism "
                        "collapses into determinism"
                    ),
                },
                {
                    "witness": "Gibbons 2016, n. 3 (.md ll. 55-60)",
                    "quote_en": (
                        "H.S. Benjamins has offered a careful study of the major "
                        "texts of Origen's views on the relationship between "
                        "providence and human freedom, arguing that, while Origen, "
                        "like Alexander of Aphrodisias, was committed to the idea "
                        "that human action is not determined by prior causes, "
                        "nevertheless God can use his foreknowledge of human "
                        "action to arrange for the restoration of all human beings"
                    ),
                    "supports": "the substantive thesis of the book",
                },
                {
                    "witness": "Belcastro, Predestinazione in Origene, n. 27 (.md ll. 287-293)",
                    "quote_de": (
                        "Die zwei Themen der menschlichen Freiheit und göttlichen "
                        "Vorsehung bilden den Kern der Systematik der Theologie "
                        "des Origenes"
                    ),
                    "quote_locus": "Benjamins 1994, p. 1, quoted by Belcastro",
                    "supports": "freedom + providence as the systematic core",
                },
                {
                    "witness": "Tolan 2021, n. 310 (.md l. 4241)",
                    "quote_de": (
                        "Origenes' Gliederung entspricht der stoischen Einteilung "
                        "der Dinge nach der Qualität der pneumaströmungen"
                    ),
                    "quote_locus": "Benjamins 1994, p. 68, quoted by Tolan",
                    "supports": "Benjamins reads De princ. III.1 motion theory as Stoic in structure",
                },
            ],
            "further_citations": [
                "Fürst 2022 p. 249 n. 6: 'siehe auch Benjamins, Eingeordnete Freiheit 58-71'",
                "Fürst 2022 p. 286 n. 106: 'Siehe dazu Benjamins, Eingeordnete Freiheit 92 f. 94.'",
                "Fürst 2021 (Adamantiana 21): 'Hendrik S. Benjamins, Eingeordnete Freiheit... Leiden 1994, 58-70.'",
                "Gibbons 2016 nn. 23, 26, 47 (pp. 61-2, 64-6, 92-8, 99-121)",
            ],
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "H. S. Benjamins, Eingeordnete Freiheit. Freiheit und Vorsehung "
                "bei Origenes (Supplements to Vigiliae Christianae 28), "
                "Leiden - New York - Köln: Brill, 1994. Imprint read verbatim in "
                "Belcastro n. 27 ('Brill, Leiden-New York-Köln 1994') and in "
                "Fürst 2022 Literaturverzeichnis p. 302; page range 50-121 also "
                "given by Markschies 2007 n. 63 (SVigChr 28, Leiden 1994, 50-121)."
            ),
        },
    },
    # ---- Peter Brown ----------------------------------------------------
    {
        "id": "scholar_brown_peter",
        "label": "Peter Brown",
        "type": "person",
        "period": "Contemporary",
        "role": "scholar",
        "school": None,
        "description": (
            "British historian of late antiquity (Princeton, emeritus); author of "
            "Augustine of Hippo: A Biography (Berkeley: University of California "
            "Press, 1967), the biography that established the standard periodised "
            "reading of Augustine in which the answer to the second question of "
            "Ad Simplicianum (396) marks the decisive turn in Augustine's account "
            "of human motivation."
        ),
        "metadata": {
            "role": "scholar",
            "surname": "Brown",
            "given_names": "Peter",
            "wave": WAVE,
            "key_work": "Augustine of Hippo: A Biography (Berkeley 1967)",
            "specialty": "Late antiquity, Augustine, social and religious history",
            "source_rank": (
                "person node derived from held witnesses (Wetzel 1992, Barclay "
                "2015, Gorday 1983, Cary 2000) — " + _NOT_HELD
            ),
            "reference_status": "position sourced from held discussions; biography not collated",
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Peter Brown, Augustine of Hippo: A Biography, Berkeley: "
                "University of California Press, 1967. Imprint read verbatim in "
                "Gorday 1983 ('I am using Peter Brown, Augustine of Hippo: A "
                "Biography (Berkeley: University of California Press, 1967).') "
                "and in Wetzel 1992 p. 87 n. 3."
            ),
        },
    },
    {
        "id": "pub_brown_1967_augustine_of_hippo",
        "label": "Brown 1967 — Augustine of Hippo: A Biography",
        "type": "publication",
        "period": "Contemporary",
        "role": None,
        "school": None,
        "description": (
            "Peter Brown, Augustine of Hippo: A Biography, Berkeley: University "
            "of California Press, 1967 (rev. ed. 2000). The reading commonly "
            "labelled the 'rupture' account of Augustine on free will: the answer "
            "to the second question of Ad Simplicianum (396) is the decisive turn, "
            "after which the will is understood as dependent on delight rather "
            "than on deliberative choice. Brown's own words, quoted by Wetzel "
            "1992 p. 158 n. 82 from Brown p. 170: 'Surprisingly enough... the "
            "austere answer to the Second Problem of the Various Problems for "
            "Simplicianus is the intellectual charter for the Confessions. For "
            "both books faced squarely the central problem of the nature of human "
            "motivation. In both books, the will is now seen as dependent on a "
            "capacity of \"delight\"...'. Barclay 2015 n. 17 records the same "
            "position from the other side, as the target of Carol Harrison's "
            "continuity thesis. NOT HELD LOCALLY."
        ),
        "metadata": {
            "type": "book",
            "year": 1967,
            "author": "Peter Brown",
            "author_id": "scholar_brown_peter",
            "title": "Augustine of Hippo: A Biography",
            "publisher": "University of California Press",
            "place": "Berkeley",
            "language": "en",
            "wave": WAVE,
            "source_rank": "biography, University of California Press — " + _NOT_HELD,
            "reference_status": (
                "position sourced from a verbatim quotation of Brown p. 170 inside "
                "Wetzel 1992 and from Barclay 2015 n. 17; the biography was not collated"
            ),
            "held_locally": False,
            "grounding": [
                {
                    "witness": "Wetzel 1992, p. 158 n. 82 (rebuilt PDF, OCR of img p-173)",
                    "quote_en": (
                        "Brown, Augustine of Hippo, 170: \"Surprisingly enough... "
                        "the austere answer to the Second Problem of the Various "
                        "Problems for Simplicianus is the intellectual charter for "
                        "the Confessions. For both books faced squarely the central "
                        "problem of the nature of human motivation. In both books, "
                        "the will is now seen as dependent on a capacity of "
                        "'delight,'...\""
                    ),
                    "supports": "Brown's reading of the 396 Ad Simplicianum turn",
                    "ocr": True,
                },
                {
                    "witness": "Barclay 2015, Paul and the Gift, n. 17 (.md l. 2214)",
                    "quote_en": (
                        "C. Harrison, Rethinking Augustine's Early Theology: An "
                        "Argument for Continuity (Oxford: Oxford University Press, "
                        "2006) (the latter insisting, against Brown, Fredriksen et "
                        "al., that little actually changes in the Ad Simpl. of 396)."
                    ),
                    "supports": "Brown holds the rupture reading; Harrison opposes him",
                },
            ],
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Peter Brown, Augustine of Hippo: A Biography, Berkeley: "
                "University of California Press, 1967 (imprint verbatim in Gorday "
                "1983 and Wetzel 1992 p. 87 n. 3)."
            ),
        },
    },
    # ---- Carol Harrison --------------------------------------------------
    {
        "id": "scholar_harrison_carol",
        "label": "Carol Harrison",
        "type": "person",
        "period": "Contemporary",
        "role": "scholar",
        "school": None,
        "description": (
            "British patristic scholar (Lady Margaret Professor of Divinity, "
            "Oxford); author of Rethinking Augustine's Early Theology: An Argument "
            "for Continuity (Oxford University Press, 2006), which argues against "
            "the periodised reading of Augustine associated with Peter Brown and "
            "Paula Fredriksen. NOT to be confused with Simon Harrison, Augustine's "
            "Way into the Will (Oxford, 2006), a different author and book cited "
            "elsewhere in this graph's Frede 2011 material."
        ),
        "metadata": {
            "role": "scholar",
            "surname": "Harrison",
            "given_names": "Carol",
            "wave": WAVE,
            "key_works": [
                "Augustine: Christian Truth and Fractured Humanity (Oxford 2000)",
                "Rethinking Augustine's Early Theology: An Argument for Continuity (Oxford 2006)",
            ],
            "specialty": "Augustine, early Christian theology, patristic aesthetics",
            "disambiguation": (
                "distinct from Simon Harrison, Augustine's Way into the Will "
                "(Oxford, 2006) — same year, different scholar; do not merge"
            ),
            "source_rank": (
                "person node derived from two independent held witnesses "
                "(Barclay 2015, Ramelli 2021) — " + _NOT_HELD
            ),
            "reference_status": "position sourced from held discussions; monograph not collated",
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Carol Harrison, Rethinking Augustine's Early Theology: An "
                "Argument for Continuity, Oxford: Oxford University Press, 2006. "
                "Bibliographic entry read verbatim in Ramelli 2021 ('Harrison, "
                "Carol. 2006. Rethinking Augustine's Early Theology: An Argument "
                "for Continuity. Oxford: OUP.') and in Barclay 2015 bibliography."
            ),
        },
    },
    {
        "id": "pub_harrison_2006_rethinking_augustines_early_theology",
        "label": "Harrison 2006 — Rethinking Augustine's Early Theology: An Argument for Continuity",
        "type": "publication",
        "period": "Contemporary",
        "role": None,
        "school": None,
        "description": (
            "Carol Harrison, Rethinking Augustine's Early Theology: An Argument "
            "for Continuity, Oxford: Oxford University Press, 2006. The standard "
            "continuity reading, directed against the rupture account: Barclay "
            "2015 n. 17 summarises it as 'insisting, against Brown, Fredriksen et "
            "al., that little actually changes in the Ad Simpl. of 396'. Ramelli "
            "2021 sets it against Lettieri's 'other Augustine': 'on the other hand, "
            "scholars such as Carol Harrison (2006) stress more the continuity of "
            "Augustine's thought during all of his life'. The thesis is contested "
            "— Ramelli's own note points to Drecoll's 2009 review. NOT HELD "
            "LOCALLY; no claim here rests on a reading of the monograph."
        ),
        "metadata": {
            "type": "book",
            "year": 2006,
            "author": "Carol Harrison",
            "author_id": "scholar_harrison_carol",
            "title": "Rethinking Augustine's Early Theology: An Argument for Continuity",
            "publisher": "Oxford University Press",
            "place": "Oxford",
            "language": "en",
            "wave": WAVE,
            "source_rank": "monograph, Oxford University Press — " + _NOT_HELD,
            "reference_status": (
                "thesis reported from two independent held witnesses; monograph not collated"
            ),
            "held_locally": False,
            "contested": (
                "Ramelli 2021 n. 2 flags the counter-position: 'On the other hand, "
                "see the review by Drecoll 2009.'"
            ),
            "grounding": [
                {
                    "witness": "Barclay 2015, Paul and the Gift, n. 17 (.md l. 2214)",
                    "quote_en": (
                        "C. Harrison, Rethinking Augustine's Early Theology: An "
                        "Argument for Continuity (Oxford: Oxford University Press, "
                        "2006) (the latter insisting, against Brown, Fredriksen et "
                        "al., that little actually changes in the Ad Simpl. of 396)."
                    ),
                    "supports": "the continuity thesis and its opposition to Brown",
                },
                {
                    "witness": "Ramelli 2021, Origen and Augustine (txt ll. 68-71)",
                    "quote_en": (
                        "on the other hand, scholars such as Carol Harrison (2006) "
                        "stress more the continuity of Augustine's thought during "
                        "all of his life."
                    ),
                    "supports": "independent confirmation of the continuity thesis",
                },
            ],
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Carol Harrison, Rethinking Augustine's Early Theology: An "
                "Argument for Continuity, Oxford: Oxford University Press, 2006 "
                "(entry verbatim in Ramelli 2021 and Barclay 2015 bibliographies)."
            ),
        },
    },
    # ---- Rist 1969 -------------------------------------------------------
    {
        "id": "pub_rist_1969_augustine_free_will_predestination",
        "label": "Rist 1969 — Augustine on Free Will and Predestination",
        "type": "publication",
        "period": "Contemporary",
        "role": None,
        "school": None,
        "description": (
            "John M. Rist, 'Augustine on Free Will and Predestination', Journal of "
            "Theological Studies N.S. 20 (1969), 420-47; reprinted in R. A. Markus "
            "(ed.), Augustine: A Collection of Critical Essays, Garden City, NY: "
            "Doubleday, 1972. The critical reading Wetzel 1992 sets himself "
            "against: Rist finds that the Augustinian nuances of necessity do not "
            "compensate for the elimination of choice, holding that what we would "
            "call psychological compulsions are not compulsions for Augustine but "
            "'simply the individual working out his own nature' (quoted Wetzel p. "
            "199); and that if we have no alternative but to will as God would "
            "have us will, freedom from constraint is at best the freedom to be "
            "programmed by God — 'this would make us little more than living "
            "puppets' (quoted Wetzel p. 220). NOT HELD LOCALLY. NB the article, "
            "not the 1994 book Augustine: Ancient Thought Baptized, is the source "
            "of this position; the 1994 book is nowhere attested in the local "
            "library and post-dates Wetzel 1992."
        ),
        "metadata": {
            "type": "article",
            "year": 1969,
            "author": "John M. Rist",
            "author_id": "scholar_rist_john",
            "title": "Augustine on Free Will and Predestination",
            "journal": "Journal of Theological Studies",
            "volume": "N.S. 20",
            "pages": "420-447",
            "language": "en",
            "wave": WAVE,
            "reprint": (
                "R. A. Markus (ed.), Augustine: A Collection of Critical Essays, "
                "Garden City, NY: Doubleday, 1972"
            ),
            "source_rank": (
                "peer-reviewed journal article (JTS) — " + _NOT_HELD
            ),
            "reference_status": (
                "position sourced from Wetzel 1992's extended engagement with it "
                "(pp. 199, 202, 220-221), including two verbatim quotations of "
                "Rist; the article itself was not collated"
            ),
            "held_locally": False,
            "grounding": [
                {
                    "witness": "Wetzel 1992, p. 199 (rebuilt PDF, OCR of img p-214)",
                    "quote_en": (
                        "A less sympathetic interpreter of Augustine, John Rist, "
                        "does not find that the nuances of necessity compensate for "
                        "the elimination of choice. He takes Augustine's claim that "
                        "we cannot be forced to will (cog: velle) to mean that "
                        "compulsion always pits us against an external opposing "
                        "force: \"What we should call psychological compulsions are "
                        "not compulsions for Augustine. They are simply the "
                        "individual working out his own nature.\""
                    ),
                    "supports": "Rist's criticism of Augustinian necessity",
                    "ocr": True,
                },
                {
                    "witness": "Wetzel 1992, p. 220 (rebuilt PDF, OCR of img p-235)",
                    "quote_en": (
                        "His obvious precursor is Rist, who in 1969 deplored in "
                        "print the psychological determinism of Augustine's doctrine "
                        "of grace. If we really have no alternative but to will as "
                        "God would have us will, then, Rist thinks, freedom from "
                        "constraint is at best the freedom to be programmed by God, "
                        "and \"this would make us little more than living puppets.\""
                    ),
                    "supports": "the puppet objection; dates the position to 1969",
                    "ocr": True,
                },
            ],
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "John Rist, 'Augustine on Free Will and Predestination', Journal "
                "of Theological Studies N.S. 20 (1969), 420-47 — reference read "
                "verbatim in Wetzel 1992 p. 199 n. 76; reprint imprint read in "
                "Wang, PhD thesis bibliography (Markus ed., Doubleday, 1972)."
            ),
        },
    },
    # ---- TeSelle ---------------------------------------------------------
    {
        "id": "scholar_teselle_eugene",
        "label": "Eugene TeSelle",
        "type": "person",
        "period": "Contemporary",
        "role": "scholar",
        "school": None,
        "description": (
            "American theologian and Augustine scholar (Vanderbilt Divinity "
            "School); author of Augustine the Theologian (New York: Herder and "
            "Herder, 1970), which Wetzel 1992 names as the only work comparable "
            "in scope to his own on Augustine's moral psychology."
        ),
        "metadata": {
            "role": "scholar",
            "surname": "TeSelle",
            "given_names": "Eugene",
            "wave": WAVE,
            "key_work": "Augustine the Theologian (New York: Herder and Herder, 1970)",
            "specialty": "Augustine, historical theology, Pelagian controversy",
            "source_rank": (
                "person node derived from held witnesses (Wetzel 1992, Gorday "
                "1983) — " + _NOT_HELD
            ),
            "reference_status": "position sourced from held discussions; monograph not collated",
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Eugene TeSelle, Augustine the Theologian, New York: Herder and "
                "Herder, 1970. Imprint read verbatim in Wetzel 1992 p. 56 n. "
                "('Eugene TeSelle, Augustine the Theologian (New York: Herder and "
                "Herder, 1970), 61-73') and in Gorday 1983 bibliography."
            ),
        },
    },
    {
        "id": "pub_teselle_1970_augustine_the_theologian",
        "label": "TeSelle 1970 — Augustine the Theologian",
        "type": "publication",
        "period": "Contemporary",
        "role": None,
        "school": None,
        "description": (
            "Eugene TeSelle, Augustine the Theologian, New York: Herder and "
            "Herder, 1970. Reported position, from Wetzel 1992 p. 198 (n. 75 "
            "referring to TeSelle p. 291): 'TeSelle develops a critique very "
            "similar to Burnaby's. He views Augustine's interest in necessity as "
            "an interest in the motivational constraints on how we will. Because "
            "we are always oriented to act in particular ways and lack the power "
            "to change our fundamental orientations at will, we are incapable of "
            "acting without drawing upon a context of prior motivations.' Wetzel "
            "also holds that TeSelle, like Burnaby, lends Augustine credibility by "
            "attributing a crude libertarian view of freedom to his Pelagian "
            "opponents (p. 199), and that TeSelle wrongly assumes resistibility "
            "must always feature in the appropriation of grace (p. 202). Wetzel "
            "p. 188 n. 58: 'Only TeSelle's work in Augustine the Theologian, "
            "185-338, is comparable.' NOT HELD LOCALLY."
        ),
        "metadata": {
            "type": "book",
            "year": 1970,
            "author": "Eugene TeSelle",
            "author_id": "scholar_teselle_eugene",
            "title": "Augustine the Theologian",
            "publisher": "Herder and Herder",
            "place": "New York",
            "language": "en",
            "wave": WAVE,
            "source_rank": "monograph — " + _NOT_HELD,
            "reference_status": (
                "position sourced from Wetzel 1992 pp. 188, 198-202; the monograph "
                "was not collated"
            ),
            "held_locally": False,
            "grounding": [
                {
                    "witness": "Wetzel 1992, p. 198 with n. 75 (rebuilt PDF, OCR of img p-213)",
                    "quote_en": (
                        "TeSelle develops a critique very similar to Burnaby's. He "
                        "views Augustine's interest in necessity as an interest in "
                        "the motivational constraints on how we will. Because we "
                        "are always oriented to act in particular ways and lack the "
                        "power to change our fundamental orientations at will, we "
                        "are incapable of acting without drawing upon a context of "
                        "prior motivations."
                    ),
                    "quote_locus": "n. 75: 'TeSelle, Augustine the Theologian, 291.'",
                    "supports": "TeSelle's reading of Augustinian necessity",
                    "ocr": True,
                },
                {
                    "witness": "Wetzel 1992, p. 199 (rebuilt PDF, OCR of img p-214)",
                    "quote_en": (
                        "On his interpretation of Pelagius, Rist is surely closer "
                        "to the truth than either Burnaby or TeSelle, who lend "
                        "greater credibility to Augustine by attributing a crude "
                        "libertarian view of freedom to his opponents."
                    ),
                    "supports": "Wetzel's disagreement with TeSelle on Pelagius",
                    "ocr": True,
                },
            ],
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Eugene TeSelle, Augustine the Theologian, New York: Herder and "
                "Herder, 1970 (imprint verbatim in Wetzel 1992 p. 56 n. and Gorday "
                "1983 bibliography); the passage discussed is TeSelle p. 291, the "
                "comparable treatment pp. 185-338."
            ),
        },
    },
]

# --------------------------------------------------------------------------
# Enrichments of existing nodes (metadata only, plus two corrected descriptions)
# --------------------------------------------------------------------------

NODE_ENRICHMENTS: dict[str, dict] = {
    "pub_hengstermann_2016_freiheitsmetaphysik": {
        "description_replace": [
            (
                "Adamantiana 8. Münster: Aschendorff. 386pp.",
                "Adamantiana 8. Münster: Aschendorff. 368 pp.",
            ),
        ],
        "metadata_sets": {
            "page_count_correction_2026_08_16": (
                "the node read '386pp'; Aschendorff's own series list, printed in "
                "fuerst_2021_perspectives_origen_adamantiana21.pdf, gives '2016, "
                "368 Seiten, gebunden, 48,- EUR. ISBN 978-3-402-13719-2'"
            ),
            "author_note": (
                "sole author Christian Hengstermann. Every held witness (Fürst "
                "2022 Literaturverzeichnis p. 305; Fürst in Origeniana Duodecima "
                "n. 35; Aschendorff's own series list; Brouwer/Vimercati 2020) "
                "attributes the volume to Hengstermann alone; Fürst is a "
                "co-editor of other Adamantiana volumes and of OWD, not of this one."
            ),
            "date_note": (
                "2016. Claire Hall 2021 cites it as '(2017a)'; that is an outlier "
                "against five independent local witnesses and is treated as her error."
            ),
            "series": "Adamantiana 8",
            "isbn": "978-3-402-13719-2",
            "pages": "368",
            "source_rank": (
                "monograph, Aschendorff (Adamantiana 8) — NOT held locally; the "
                "position below is reported from Fürst 2022, Fürst 2021, Tolan "
                "2021 and Claire Hall 2021, each quoted verbatim in `grounding`"
            ),
            "reference_status": (
                "position sourced from ~30 citations in Fürst 2022 and from a "
                "verbatim German quotation of p. 17 in Tolan 2021; the monograph "
                "itself was not collated"
            ),
            "held_locally": False,
            "grounding": [
                {
                    "witness": "Fürst 2022, printed p. 247, ch. VI n. 1 (.md ll. 8893-8898)",
                    "quote_de": (
                        "Eine umfassende und grundlegende Studie über Origenes und "
                        "den Ursprung der Freiheitsmetaphysik hat Christian "
                        "Hengstermann 2016 vorgelegt."
                    ),
                    "context_de": (
                        "indem er die Freiheit zum Prinzip der Anthropologie und "
                        "der Metaphysik, kurzum: der ganzen Wirklichkeit machte. "
                        "Das war die grundlegende Innovation des Origenes."
                    ),
                    "supports": (
                        "Fürst footnotes his own governing thesis to Hengstermann "
                        "on its first appearance"
                    ),
                },
                {
                    "witness": "Fürst 2022, printed p. ~189, n. 27 (.md ll. 7142-7144)",
                    "quote_de": (
                        "Siehe dazu die eingehende philosophische Analyse von "
                        "Origenes' Freiheitstraktat bei Hengstermann, "
                        "Freiheitsmetaphysik 13-93"
                    ),
                    "supports": "Hengstermann pp. 13-93 = the analysis of De princ. III.1",
                },
                {
                    "witness": "Fürst 2022, printed p. 210, n. 63 (.md ll. 7583-7585)",
                    "quote_de": (
                        "der jedoch in seiner an sich ausgezeichneten Darstellung "
                        "dazu tendiert, Origenes einen voluntaristischen "
                        "Willensbegriff zuzuschreiben, wogegen Perkams, Ethischer "
                        "Intellektualismus, und Hengstermann, Freiheitsmetaphysik "
                        "49-70, auf die richtige Einordnung hingewiesen haben."
                    ),
                    "supports": "Hengstermann against a voluntarist reading of Origen's will",
                },
                {
                    "witness": "Fürst 2022, printed p. 205, n. 50 (.md ll. 7401-7403)",
                    "quote_de": (
                        "Die Neudeutung, die er Origenes zuschreibt, ist allerdings "
                        "schon in Chrysipps Intellektualismus vorgeprägt."
                    ),
                    "supports": "Fürst's one registered disagreement with Hengstermann",
                },
                {
                    "witness": "Fürst 2022, printed p. 260, n. 42 (.md l. 9358)",
                    "quote_de": "Hengstermann, Freiheitsmetaphysik 284.",
                    "context_de": (
                        "sourcing Fürst's quoted phrase 'der fremdbewegten Natur "
                        "wie des eigenbewegten Geistes'"
                    ),
                    "supports": "God as origin of both moved nature and self-moving mind",
                },
                {
                    "witness": "Fürst 2022, printed p. 267, n. 67 (.md ll. 9606-9607)",
                    "quote_de": (
                        "Eine innovative Darstellung des origeneischen "
                        "Trinitätsdenkens ist Hengstermann, Freiheitsmetaphysik "
                        "168-288."
                    ),
                    "supports": "the Trinitarian section of the monograph",
                },
                {
                    "witness": "Tolan 2021, n. 554 (.md ll. 6318-6322), quoting Hengstermann 2016 p. 17",
                    "quote_de": (
                        "Kraft ihres αὐτεξούσιον, das bereits hier nicht das "
                        "Vermögen einer Wahl zwischen moralisch indifferenten "
                        "Optionen, sondern die Fähigkeit zu einer existentiellen "
                        "Grundwahl zwischen Gut und Böse bezeichnet, muss sich die "
                        "christliche Seele innerhalb des heilsgeschichtlichen "
                        "Kampfes für das eine oder das andere Heerlager entscheiden"
                    ),
                    "supports": (
                        "Hengstermann's own definition of αὐτεξούσιον as an "
                        "existential fundamental option, not indifferent choice"
                    ),
                },
                {
                    "witness": "Fürst 2021 (Adamantiana 21), pdftotext l. 4489",
                    "quote_en": (
                        "See the seminal study of Christian Hengstermann, Origenes "
                        "und der Ursprung der Freiheitsmetaphysik (Adamantiana 8), "
                        "Münster 2016."
                    ),
                    "supports": "Fürst's assessment restated in English, independently of the 2022 book",
                },
            ],
            "contested": (
                "The Freiheitsmetaphysik thesis is a named Münster-school position "
                "(Kobusch, Hengstermann, Fürst), not settled fact. The IFB review "
                "of Kobusch, Metaphysik der Freiheit (Adamantiana 28), after "
                "quoting the school's core claim ('Origenes ist der erste Denker "
                "in der langen Geschichte des Nachdenkens über die Freiheit, der "
                "sie als ontologisches Prinzip begreift', S. 5), adds: 'Wie auch "
                "immer man zu dieser historischen Rekonstruktion stehen mag - man "
                "wird wohl nicht fehlgehen, wenn man vermutet, sie sei durchaus "
                "kontrovers -'. Keep the thesis attributed, never flattened to fact."
            ),
            "citation_verdict": "verified",
        },
        "verification_note": (
            "[Vérif. 2026-08-16 : enriched with the verbatim German anchors that "
            "ground the node's existing summary. All eight anchors were read in "
            "held files (Fürst 2022 .md, Fürst 2021 .pdf, Tolan 2021 .md, "
            "Kobusch_2023 IFB review .pdf) and are stored in metadata.grounding. "
            "The monograph itself is NOT held locally — flagged via held_locally "
            "and source_rank. Sole authorship (Hengstermann, not Fürst/"
            "Hengstermann) and the 2016 date were both re-checked against five "
            "witnesses. The Münster-school thesis is flagged as contested per the "
            "IFB review.]"
        ),
    },
    "scholar_hengstermann_christian": {
        "metadata_sets": {
            "source_rank": (
                "person node; the subject's monograph is NOT held locally — the "
                "description reports Fürst 2022's assessment, anchored verbatim on "
                "pub_hengstermann_2016_freiheitsmetaphysik.metadata.grounding"
            ),
            "reference_status": (
                "position sourced from held discussions (Fürst 2022 ch. VI n. 1 "
                "and passim, Fürst 2021, Tolan 2021, Hall 2021); monograph not collated"
            ),
            "held_locally": False,
            "affiliation_note": (
                "Fürst 2021 names the school explicitly: 'who mentions as the key "
                "figures Theo Kobusch, Christian Hengstermann and myself.'"
            ),
        },
        "verification_note": (
            "[Vérif. 2026-08-16 : source_rank / reference_status / held_locally "
            "added. The claim that Fürst 'describes it as an exhaustive and "
            "fundamental study' is confirmed verbatim at Fürst 2022 p. 247 n. 1: "
            "'Eine umfassende und grundlegende Studie ... hat Christian "
            "Hengstermann 2016 vorgelegt.' The '30 footnotes' figure is consistent "
            "with the count of Hengstermann citations in the held .md.]"
        ),
    },
    "pub_wetzel_1992_augustine_limits_virtue": {
        "description_replace": [
            (
                'Main thesis (overturning the "conventional wisdom" of Brown, '
                "Rist, O'Daly, Burnaby, Arendt): Augustine does NOT break",
                'Main thesis (overturning the "conventional wisdom" of Rist, '
                "O'Daly, Burnaby, Arendt — but NOT of Brown, on whom Wetzel "
                "positively relies): Augustine does NOT break",
            ),
        ],
        "metadata_field_replace": {
            "description_en": [
                (
                    'Main thesis (overturning the "conventional wisdom" of Brown, '
                    "Rist, O'Daly, Burnaby, Arendt): Augustine does NOT break",
                    'Main thesis (overturning the "conventional wisdom" of Rist, '
                    "O'Daly, Burnaby, Arendt — but NOT of Brown, on whom Wetzel "
                    "positively relies): Augustine does NOT break",
                ),
            ],
            "description_fr": [
                (
                    "Thèse principale (renverse la « sagesse conventionnelle » de "
                    "Brown, Rist, O'Daly, Burnaby, Arendt)",
                    "Thèse principale (renverse la « sagesse conventionnelle » de "
                    "Rist, O'Daly, Burnaby, Arendt — mais NON de Brown, dont "
                    "Wetzel se réclame positivement)",
                ),
            ],
        },
        "metadata_sets": {
            "brown_relation_correction_2026_08_16": (
                "Across all 254 pages of the rebuilt+OCR'd local PDF, Peter Brown "
                "appears only as an authority Wetzel relies on, never as a target. "
                "p. 144: 'I owe debts to Brown, Augustine of Hippo, 146-57, Eugene "
                "TeSelle, Augustine the Theologian ... 176-82, J. Patout Burns...'; "
                "p. 110: 'in Peter Brown's memorable words'; p. 88: 'For a "
                "judicious assessment ... see Brown'; p. 158 n. 82 quotes Brown "
                "p. 170 approvingly. Wetzel's 'conventional wisdom' passage (p. 3) "
                "names nobody and concerns the Platonism / two-conversions reading. "
                "The opposition to Rist, O'Daly, Burnaby, TeSelle and Arendt IS "
                "attested (pp. 9, 198-203, 220-221)."
            ),
            "local_pdf_condition": (
                "the held PDF is structurally corrupt (truncated, xref and page "
                "tree destroyed) and its text layer is invisible OCR containing "
                "only spaces; for this wave the catalog/page tree/xref were "
                "rebuilt, the 254 page scans extracted and re-OCR'd with tesseract. "
                "All page quotations added in this wave are OCR (printed page = "
                "image index - 15) and are flagged ocr:true."
            ),
            "citation_verdict": "corrected",
        },
        "verification_note": (
            "[Vérif. 2026-08-16 : the node claimed Wetzel overturns 'the "
            "conventional wisdom of Brown, Rist, O'Daly, Burnaby, Arendt'. Brown "
            "is wrong: the full OCR of the local PDF shows Wetzel relying on Brown "
            "throughout and quoting him approvingly (p. 144 'I owe debts to Brown'; "
            "p. 158 n. 82). Brown removed from the list in description, "
            "description_en and description_fr; evidence stored in "
            "metadata.brown_relation_correction_2026_08_16. The other four names "
            "are attested and are kept.]"
        ),
    },
}

# --------------------------------------------------------------------------
# Edges — created ONLY where a held text attests the relationship
# --------------------------------------------------------------------------

NEW_EDGES: list[dict] = [
    {
        "source": "pub_benjamins_1994_eingeordnete_freiheit",
        "relation": "authored_by",
        "target": "scholar_benjamins_hendrik_s",
        "weight": 1.0,
        "metadata": {"wave": WAVE, "attested_by": "Fürst 2022 Literaturverzeichnis p. 302"},
    },
    {
        "source": "pub_brown_1967_augustine_of_hippo",
        "relation": "authored_by",
        "target": "scholar_brown_peter",
        "weight": 1.0,
        "metadata": {"wave": WAVE, "attested_by": "Gorday 1983; Wetzel 1992 p. 87 n. 3"},
    },
    {
        "source": "pub_harrison_2006_rethinking_augustines_early_theology",
        "relation": "authored_by",
        "target": "scholar_harrison_carol",
        "weight": 1.0,
        "metadata": {"wave": WAVE, "attested_by": "Ramelli 2021 bibliography; Barclay 2015 bibliography"},
    },
    {
        "source": "pub_rist_1969_augustine_free_will_predestination",
        "relation": "authored_by",
        "target": "scholar_rist_john",
        "weight": 1.0,
        "metadata": {"wave": WAVE, "attested_by": "Wetzel 1992 p. 199 n. 76"},
    },
    {
        "source": "pub_teselle_1970_augustine_the_theologian",
        "relation": "authored_by",
        "target": "scholar_teselle_eugene",
        "weight": 1.0,
        "metadata": {"wave": WAVE, "attested_by": "Wetzel 1992 p. 56 n.; Gorday 1983"},
    },
    {
        "source": "pub_harrison_2006_rethinking_augustines_early_theology",
        "relation": "opposes",
        "target": "pub_brown_1967_augustine_of_hippo",
        "weight": 0.9,
        "metadata": {
            "wave": WAVE,
            "stance": "opposes",
            "attested_by": (
                "Barclay 2015 n. 17: 'insisting, against Brown, Fredriksen et al., "
                "that little actually changes in the Ad Simpl. of 396'"
            ),
            "corroborated_by": "Ramelli 2021 (txt ll. 68-71)",
        },
    },
    {
        "source": "pub_wetzel_1992_augustine_limits_virtue",
        "relation": "opposes",
        "target": "pub_rist_1969_augustine_free_will_predestination",
        "weight": 0.9,
        "metadata": {
            "wave": WAVE,
            "stance": "opposes",
            "attested_by": (
                "Wetzel 1992 pp. 202, 220-221 (OCR of rebuilt local PDF): 'But Rist "
                "is no more correct than TeSelle and Burnaby...'; 'Rist and O'Daly "
                "... could do nothing with it.'"
            ),
        },
    },
    {
        "source": "pub_wetzel_1992_augustine_limits_virtue",
        "relation": "opposes",
        "target": "pub_teselle_1970_augustine_the_theologian",
        "weight": 0.85,
        "metadata": {
            "wave": WAVE,
            "stance": "opposes",
            "attested_by": (
                "Wetzel 1992 pp. 198-202 (OCR of rebuilt local PDF): TeSelle 'lends "
                "greater credibility to Augustine by attributing a crude "
                "libertarian view of freedom to his opponents'"
            ),
            "qualification": (
                "Wetzel also credits TeSelle: p. 188 n. 58 'Only TeSelle's work in "
                "Augustine the Theologian, 185-338, is comparable.'"
            ),
        },
    },
    {
        "source": "pub_wetzel_1992_augustine_limits_virtue",
        "relation": "engages_with",
        "target": "pub_brown_1967_augustine_of_hippo",
        "weight": 0.9,
        "metadata": {
            "wave": WAVE,
            "stance": "agrees",
            "attested_by": (
                "Wetzel 1992 p. 144 (OCR of rebuilt local PDF): 'I owe debts to "
                "Brown, Augustine of Hippo, 146-57'; p. 158 n. 82 quotes Brown "
                "p. 170 approvingly"
            ),
            "note": (
                "explicitly NOT an `opposes` edge — see "
                "pub_wetzel_1992_augustine_limits_virtue.metadata."
                "brown_relation_correction_2026_08_16"
            ),
        },
    },
    {
        "source": "pub_furst_2022_wege_freiheit",
        "relation": "engages_with",
        "target": "pub_benjamins_1994_eingeordnete_freiheit",
        "weight": 0.9,
        "metadata": {
            "wave": WAVE,
            "stance": "qualifies",
            "attested_by": (
                "Fürst 2022 p. 283 n. 100: 'ist das Thema der Studie von Benjamins, "
                "Eingeordnete Freiheit, bes. 71-121'; also p. 249 n. 6 and p. 286 n. 106"
            ),
        },
    },
    {
        "source": "pub_furst_2022_wege_freiheit",
        "relation": "engages_with",
        "target": "pub_hengstermann_2016_freiheitsmetaphysik",
        "weight": 1.0,
        "metadata": {
            "wave": WAVE,
            "stance": "agrees",
            "attested_by": (
                "Fürst 2022 p. 247 ch. VI n. 1: 'Eine umfassende und grundlegende "
                "Studie über Origenes und den Ursprung der Freiheitsmetaphysik hat "
                "Christian Hengstermann 2016 vorgelegt.' Fürst adopts "
                "Hengstermann's translations (nn. 31, 34, 49, 60, 62, 67, 68, 71) "
                "and sides with him against a voluntarist reading (p. 210 n. 63), "
                "while registering one disagreement (p. 205 n. 50)."
            ),
        },
    },
    {
        "source": "pub_benjamins_1994_eingeordnete_freiheit",
        "relation": "discusses",
        "target": "work_de_principiis_origen_230s_v2w3x4y5",
        "weight": 0.9,
        "metadata": {
            "wave": WAVE,
            "attested_by": (
                "Fürst 2022 p. 249 n. 6 cites Benjamins 58-71 on the De princ. III.1 "
                "/ De orat. 6,1 doctrine of motion; Gibbons 2016 n. 47 cites "
                "Benjamins 92-8 on the hypothetical-fate argument"
            ),
        },
    },
]
