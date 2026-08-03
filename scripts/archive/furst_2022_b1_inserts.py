"""Fürst 2022 B1 — NEW_INSERTS list (new nodes).

Bilingual FR/EN plain-text descriptions (occasional `description_de` for
verbatim Fürst phrasing). Type prefixes match `type` field. Metadata via
furst_metadata().

Sections:
  - PERSONS    : (deliberately empty — Fürst treats only ancient persons
                  that already exist densely in KG ; Hengstermann etc. are
                  scholar nodes added directly here)
  - WORKS      : Origen Hom. Jér., Hom. Ézéch., Comm. Cant., Comm. Jn,
                  Comm. Matt., Comm. Genèse, Princ. Freiheitstraktat III 1
                  (subdivision conceptuelle), Plutarque Stoic. repugn.,
                  Apulée De Platone, Lucrèce DRN, Cicéron Stoic. parad.
  - SYNTHESES  : 12 par chapitre/sous-chapitre = 12 syntheses majeures
  - ARGUMENTS  : 15 thèses scholarly principales de Fürst
  - CONCEPTS   : selbstbestimmung (terme allemand moderne) +
                  freiheitsmetaphysik (concept origénien forgé par Fürst/Hengstermann) +
                  kompatibilistischer libertarismus
"""
from __future__ import annotations

from typing import Any

from furst_2022_b1_utils import dump_metadata, furst_metadata


def _node(
    *,
    id: str,
    type: str,
    label: str,
    description: str,
    description_en: str,
    period: str | None,
    metadata: dict[str, Any],
    confidence: float = 0.85,
    needs_evidence: bool = False,
    description_de: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    n: dict[str, Any] = {
        "id": id,
        "type": type,
        "label": label,
        "description": description,
        "description_en": description_en,
        "metadata": dump_metadata(metadata),
        "confidence": confidence,
    }
    if description_de is not None:
        n["description_de"] = description_de
    if period is not None:
        n["period"] = period
    if needs_evidence:
        n["needs_evidence"] = True
    n.update(extra)
    return n


# =============================================================================
# PERSONS (1 — only the contemporary scholar Hengstermann who plays a pivotal
#         role in Fürst's argument and lacks a KG node)
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="scholar_hengstermann_christian",
        type="person",
        label="Christian Hengstermann",
        description=(
            "Christian Hengstermann, patrologue et philosophe allemand "
            "(Münster), spécialiste d'Origène et de la métaphysique de la "
            "liberté. Auteur de Origenes und der Ursprung der "
            "Freiheitsmetaphysik (Aschendorff, 2016), monographie fondatrice "
            "que Fürst 2022 cite constamment comme étude pivot et qu'il "
            "qualifie d'« étude exhaustive et fondamentale ». Collaborateur "
            "de Fürst dans l'édition des Origenes Werke mit deutscher "
            "Übersetzung (OWD). Sa thèse centrale, reprise par Fürst : "
            "Origène a forgé la première métaphysique de la liberté dans "
            "laquelle la liberté est élevée du rang d'accident au rang de "
            "« principe de la substance » des êtres rationnels"
        ),
        description_en=(
            "Christian Hengstermann, German patrologist and philosopher "
            "(Münster), specialist in Origen and the metaphysics of freedom. "
            "Author of *Origenes und der Ursprung der Freiheitsmetaphysik* "
            "(Aschendorff, 2016), a foundational monograph cited constantly "
            "by Fürst 2022 as a pivotal study and described as a "
            "'comprehensive and fundamental study'. Collaborator with Fürst "
            "in the OWD Origen edition. Central thesis adopted by Fürst: "
            "Origen forged the first metaphysics of freedom in which freedom "
            "is elevated from accident to 'principle of substance' of "
            "rational beings"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="passim",
            chapter="Cited throughout Wege zur Freiheit (over 30 footnotes), especially Kap. VI",
            chapter_actual="Hengstermann 2016 = étude pivot pour la thèse origénienne de Fürst",
            extra={
                "role": "scholar",
                "affiliation": "Universität Münster / FORUM ORIGENIANUM",
                "specialization": ["Origenes", "Freiheitsmetaphysik", "patrologie grecque", "philosophie chrétienne primitive"],
                "key_work": "Origenes und der Ursprung der Freiheitsmetaphysik, Münster: Aschendorff, 2016",
                "verified": True,
                "alternative_names": ["Christian Hengstermann"],
                "given_names": "Christian",
                "surname": "Hengstermann",
                "collaboration_with_furst": "co-éditeur OWD (Origenes Werke mit deutscher Übersetzung), notamment OWD 10 Hom. Jes.",
                "central_concept_coined": "Freiheitsmetaphysik (métaphysique de la liberté origénienne)",
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# WORKS (5)
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = [
    _node(
        id="work_origen_homilies_jeremiah",
        type="work",
        label="Origène, Homélies sur Jérémie",
        description=(
            "Recueil d'homélies d'Origène sur le prophète Jérémie, prononcées "
            "à Césarée probablement entre 240 et 245 CE. Conservé en partie "
            "en grec (Homélies 1-20 dans la tradition manuscrite) et en "
            "partie en traduction latine de Jérôme. Texte critique GCS Orig. "
            "3 (Klostermann/Nautin) ; édition allemande Fürst/Lona, OWD 11 "
            "(2018). Pour Fürst 2022, Hom. Jér. 18,3 contient la formule "
            "épigraphique du livre : τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι (« car "
            "l'autodétermination est liberté ») — l'identification origénienne "
            "explicite de l'autexousion avec l'eleutheria, marqueur central "
            "du tournant origénien dans l'histoire du concept de liberté"
        ),
        description_en=(
            "Collection of Origen's homilies on the prophet Jeremiah, "
            "delivered at Caesarea probably between 240 and 245 CE. Preserved "
            "partly in Greek (Homilies 1-20 in MS tradition) and partly in "
            "Latin translation by Jerome. Critical text GCS Orig. 3 "
            "(Klostermann/Nautin); German edition Fürst/Lona, OWD 11 (2018). "
            "For Fürst 2022, Hom. Jer. 18,3 contains the epigraphic formula "
            "of the book: τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι ('for "
            "self-determination is freedom') — Origen's explicit "
            "identification of autexousion with eleutheria, the central "
            "marker of his turn in the history of the concept of freedom"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 187 (épigraphe) + passim",
            chapter="Kap. V passim + épigraphe",
            chapter_actual="Homélies sur Jérémie comme source de l'épigraphe origénienne du livre",
            extra={
                "author": "Origène d'Alexandrie",
                "composition_period": "c. 240-245 CE (Césarée)",
                "language": "grc",
                "principal_edition_cited_by_furst": "GCS Orig. 3 (Klostermann/Nautin) ; OWD 11 (Fürst/Lona, 2018)",
                "preservation_status": "20 homélies en grec + traduction latine de Jérôme",
                "furst_focus_passage": "Hom. Jér. 18,3 (GCS Orig. 32, 154) — épigraphe du livre",
                "alternative_titles": [
                    "Homiliae in Jeremiam",
                    "Ὁμιλίαι εἰς Ἱερεμίαν",
                    "Hom. Jér.",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_origen_commentary_canticles",
        type="work",
        label="Origène, Commentaire sur le Cantique des Cantiques",
        description=(
            "Commentaire d'Origène sur le Cantique des Cantiques en 10 livres, "
            "composé vers 245 CE à Césarée. Conservé en partie : prologue + "
            "livres I-III dans la traduction latine de Rufin (398), plus "
            "homélies sur le même sujet en traduction latine de Jérôme. Texte "
            "critique GCS Orig. 8 (Baehrens) ; édition allemande Fürst/"
            "Strutwolf, OWD 9/1. Pour Fürst 2022, le prologue I 1,9 + le "
            "livre III 15(IV 1),20 + III 17(IV 3),5.21 contiennent les "
            "formulations origéniennes clés sur la « liberté de la "
            "décision » (libertas arbitrii) comme don originel attribué à "
            "chaque âme — « Mitgift » pour le chemin vers l'union "
            "matrimoniale avec le Christ-Époux"
        ),
        description_en=(
            "Origen's commentary on the Song of Songs in 10 books, composed "
            "c. 245 CE at Caesarea. Partly preserved: prologue + books I-III "
            "in Rufinus's Latin translation (398), plus homilies in Jerome's "
            "Latin translation. Critical text GCS Orig. 8 (Baehrens); German "
            "edition Fürst/Strutwolf, OWD 9/1. For Fürst 2022, the prologue "
            "I 1,9 + book III 15(IV 1),20 + III 17(IV 3),5.21 contain Origen's "
            "key formulations on 'freedom of decision' (libertas arbitrii) "
            "as an original gift given to each soul — 'dowry' for the path "
            "to matrimonial union with Christ the Bridegroom"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 187-188",
            chapter="Kap. V 1 — passages cités en exergue de l'analyse",
            chapter_actual="Commentaire sur le Cantique comme témoin de la formule origénienne tardive sur la liberté",
            extra={
                "author": "Origène d'Alexandrie",
                "composition_date": "c. 245 CE (Césarée)",
                "language": "grc original ; latin (Rufin)",
                "principal_edition_cited_by_furst": "GCS Orig. 8 (Baehrens) ; OWD 9/1 (Fürst/Strutwolf)",
                "preservation_status": "prologue + livres I-III en latin (Rufin) ; quelques fragments grecs ; homélies via Jérôme",
                "furst_focus_passages": [
                    "Comm. Cant. I 1,9 (GCS Orig. 8, 91) — la liberté de décision comme « Mitgift »",
                    "Comm. Cant. III 15(IV 1),20 (GCS Orig. 8, 227)",
                    "Comm. Cant. III 17(IV 3),5.21 (GCS Orig. 8, 236. 239)",
                ],
                "alternative_titles": [
                    "Commentarii in Canticum Canticorum",
                    "Hohelied-Kommentar",
                    "Comm. Cant.",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_origen_commentary_john",
        type="work",
        label="Origène, Commentaire sur Jean",
        description=(
            "Commentaire d'Origène sur l'Évangile de Jean en 32 livres, "
            "œuvre exégétique majeure commencée vers 230 à Alexandrie et "
            "poursuivie pendant plusieurs années à Césarée. Conservé en "
            "partie : livres I, II, VI, X, XIII, XIX, XX, XXVIII, XXXII + "
            "fragments. Texte critique GCS Orig. 4 (Preuschen) ; SC 120, "
            "157, 222, 290, 385 (Blanc) ; traduction allemande Gögler. Pour "
            "Fürst 2022, le passage XX 21,174 + XXXII 16,187-189 contient "
            "(1) la formule décisive sur la transformation de l'homme par "
            "ses décisions libres (« il est devenu cela par changement et "
            "décision propre ») et (2) l'élévation de la libre "
            "autodétermination au rang de quatrième article de la foi "
            "(après Père, Fils, Esprit)"
        ),
        description_en=(
            "Origen's commentary on the Gospel of John in 32 books, major "
            "exegetical work begun c. 230 at Alexandria and continued for "
            "many years at Caesarea. Partly preserved: books I, II, VI, X, "
            "XIII, XIX, XX, XXVIII, XXXII + fragments. Critical text GCS "
            "Orig. 4 (Preuschen); SC 120, 157, 222, 290, 385 (Blanc); German "
            "translation Gögler. For Fürst 2022, XX 21,174 + XXXII 16,187-189 "
            "contains (1) the decisive formula on the transformation of man "
            "by his free decisions ('he became this through change and own "
            "decision') and (2) the elevation of free self-determination to "
            "the rank of fourth article of faith (after Father, Son, Spirit)"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 193-194, 253",
            chapter="Kap. V 1 + V 2 + VI 2",
            chapter_actual="Commentaire sur Jean — clé du 4e article de foi et de l'ontologie de la liberté",
            extra={
                "author": "Origène d'Alexandrie",
                "composition_period": "c. 230 - c. 240 CE (commencé à Alexandrie, poursuivi à Césarée)",
                "language": "grc",
                "principal_edition_cited_by_furst": "GCS Orig. 4 (Preuschen) ; SC 120/157/222/290/385 (Blanc) ; traduction Gögler",
                "preservation_status": "9 livres complets sur 32 + fragments",
                "furst_focus_passages": [
                    "Comm. Jn XX 21,174 (GCS Orig. 4, 353) — transformation par décision libre",
                    "Comm. Jn XXXII 16,187-189 (GCS Orig. 4, 451) — 4e article de foi",
                    "Comm. Jn frg. 42 (GCS Orig. 4, 517 f.)",
                ],
                "alternative_titles": [
                    "Commentarii in Joannem",
                    "Johanneskommentar",
                    "Comm. Jn",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_origen_commentary_matthew",
        type="work",
        label="Origène, Commentaire sur Matthieu",
        description=(
            "Commentaire d'Origène sur l'Évangile de Matthieu en 25 livres, "
            "composé à Césarée en 248-249 CE — œuvre tardive contemporaine du "
            "Contra Celsum. Conservé en partie : livres X-XVII en grec + "
            "traduction latine anonyme (Commentariorum series in Matthaeum) "
            "couvrant Mt 22,34-27,65. Texte critique GCS Orig. 10-11 "
            "(Klostermann). Pour Fürst 2022, Comm. Mt X 11 + XVII 21 + XVII "
            "27 contiennent les défenses tardives d'Origène sur l'absence "
            "de contrainte du destin et la permanence du libre arbitre"
        ),
        description_en=(
            "Origen's commentary on the Gospel of Matthew in 25 books, "
            "composed at Caesarea in 248-249 CE — late work contemporary with "
            "Contra Celsum. Partly preserved: books X-XVII in Greek + "
            "anonymous Latin translation (Commentariorum series in Matthaeum) "
            "covering Mt 22,34-27,65. Critical text GCS Orig. 10-11 "
            "(Klostermann). For Fürst 2022, Comm. Mt X 11 + XVII 21 + XVII "
            "27 contain Origen's late defenses on the absence of fate's "
            "compulsion and the permanence of free will"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 188, 254",
            chapter="Kap. V 1 + VI 2",
            chapter_actual="Commentaire sur Matthieu — défenses tardives de la liberté",
            extra={
                "author": "Origène d'Alexandrie",
                "composition_date": "248-249 CE (Césarée)",
                "language": "grc original ; latin pour Commentariorum series",
                "principal_edition_cited_by_furst": "GCS Orig. 10-11 (Klostermann)",
                "preservation_status": "livres X-XVII en grec + Commentariorum series anonyme en latin",
                "furst_focus_passages": [
                    "Comm. Mt X 11 (GCS Orig. 10, 12) — libre arbitre et essence de la vertu",
                    "Comm. Mt XVII 21 (GCS Orig. 10, 642) — nature et liberté",
                    "Comm. Mt XVII 27 (GCS Orig. 10, 659)",
                ],
                "alternative_titles": [
                    "Commentarii in Matthaeum",
                    "Matthäuskommentar",
                    "Comm. Mt.",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="work_origen_commentary_genesis",
        type="work",
        label="Origène, Commentaire sur la Genèse",
        description=(
            "Commentaire d'Origène sur la Genèse en 13 livres, composé vers "
            "230 à Alexandrie. Œuvre perdue en tradition directe. Un large "
            "fragment du livre III est conservé en grec dans la Philocalie "
            "ch. 23 (Junod, SC 226, 130-204) sous le titre Περὶ τῆς εἱμαρμένης "
            "(« Sur le destin ») = polémique antiastrologique cruciale dont "
            "Amand de Mendieta a démontré la centralité dans la transmission "
            "carnéadienne. Édition allemande : Metzler, OWD 1/1 (in Gen. frg. "
            "D 7). Pour Fürst 2022, ce texte (frg. D 7,1-11) est l'une des "
            "premières applications systématiques de la théorie origénienne "
            "de la liberté contre le déterminisme astrologique populaire — "
            "même chez les chrétiens"
        ),
        description_en=(
            "Origen's commentary on Genesis in 13 books, composed c. 230 at "
            "Alexandria. Work lost in direct tradition. A large fragment of "
            "book III is preserved in Greek in Philocalia ch. 23 (Junod, SC "
            "226, 130-204) under the title Περὶ τῆς εἱμαρμένης ('On Fate') = "
            "crucial anti-astrological polemic whose centrality in Carneadean "
            "transmission was demonstrated by Amand de Mendieta. German "
            "edition: Metzler, OWD 1/1 (in Gen. frg. D 7). For Fürst 2022, "
            "this text (frg. D 7,1-11) is one of the first systematic "
            "applications of Origen's theory of freedom against popular "
            "astrological determinism — including among Christians"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 189-191, 285",
            chapter="Kap. V 1 + VI 4",
            chapter_actual="Commentaire sur la Genèse — fragment grec via Philocalie 23 = anti-astrologie",
            extra={
                "author": "Origène d'Alexandrie",
                "composition_date": "c. 230 CE (Alexandrie)",
                "language": "grc",
                "principal_edition_cited_by_furst": "GCS Orig. 6 (Baehrens fragments) ; OWD 1/1 (Metzler) ; SC 226 ch. 23 (Junod)",
                "preservation_status": "perdu en tradition directe ; large fragment du livre III via Philocalie 23",
                "furst_focus_passages": [
                    "In Gen. frg. D 7,1 (OWD 1/1, 70) — Περὶ τῆς εἱμαρμένης titre original",
                    "In Gen. frg. D 7,7-11 (OWD 1/1, 82-90) — préscience et liberté",
                    "In Gen. frg. D 7,11 (OWD 1/1, 90) — l'homme partie du tout",
                ],
                "alternative_titles": [
                    "Commentarii in Genesim",
                    "Genesiskommentar",
                    "Περὶ τῆς εἱμαρμένης (titre du fragment Philocalie 23)",
                ],
                "scholarly_reference_in_furst": "Amand, Fatalisme et liberté 304-325 — analyse du fragment via Philocalie 23",
            },
        ),
        confidence=0.95,
    ),
]


# =============================================================================
# CONCEPTS (3)
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_selbstbestimmung_modern_furst",
        type="concept",
        label="Selbstbestimmung (autodétermination — terme allemand moderne)",
        description=(
            "« Selbstbestimmung » (autodétermination), terme allemand moderne "
            "que Fürst 2022 utilise comme catégorie heuristique pour "
            "désigner la capacité humaine de se déterminer soi-même, en "
            "remontant de Kant et Schiller (« reine Selbstbestimmung » dans "
            "la Critique de la raison pratique et la lettre à Körner du "
            "25 janvier 1793) jusqu'au τὸ αὐτεξούσιον de l'Antiquité grecque "
            "tardive et chrétienne primitive. Fürst justifie ce choix "
            "terminologique : éviter d'introduire anachroniquement la "
            "notion de « volonté » (Wille), qui n'existait pas comme "
            "faculté indépendante chez les Grecs avant Augustin, et se "
            "tenir près du sens originel des termes antiques τὸ ἐφ᾽ ἡμῖν, "
            "προαίρεσις, αὐτεξούσιον. Le sous-titre Menschliche "
            "Selbstbestimmung von Homer bis Origenes traduit ce choix"
        ),
        description_en=(
            "'Selbstbestimmung' (self-determination), modern German term "
            "that Fürst 2022 uses as heuristic category to designate the "
            "human capacity to determine oneself, tracing back from Kant "
            "and Schiller ('reine Selbstbestimmung' in Critique of Practical "
            "Reason and Letter to Körner of 25 Jan 1793) to τὸ αὐτεξούσιον "
            "of late Greek and early Christian antiquity. Fürst justifies "
            "this terminological choice: avoid anachronistically introducing "
            "the notion of 'will' (Wille), which did not exist as an "
            "independent faculty among Greeks before Augustine, and stay "
            "close to the original meaning of ancient terms τὸ ἐφ᾽ ἡμῖν, "
            "προαίρεσις, αὐτεξούσιον. The subtitle Menschliche "
            "Selbstbestimmung von Homer bis Origenes reflects this choice"
        ),
        description_de=(
            "« Selbstbestimmung » = der von Fürst 2022 gewählte "
            "Leitterminus, der nicht den nachaugustinischen Willensbegriff "
            "voraussetzt und nahe an den antiken Begriffen τὸ ἐφ᾽ ἡμῖν, "
            "προαίρεσις, αὐτεξούσιον bleibt"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="Vorwort + Thematische Eingrenzungen p. 7-16 + passim",
            chapter="Thematische Eingrenzungen 1a-b",
            chapter_actual="Justification terminologique de l'usage moderne de Selbstbestimmung pour saisir le τὸ αὐτεξούσιον antique",
            extra={
                "german_term": "Selbstbestimmung",
                "greek_equivalents": ["τὸ αὐτεξούσιον", "τὸ ἐφ᾽ ἡμῖν", "προαίρεσις"],
                "latin_equivalents": ["liberum arbitrium", "in nostra potestate", "voluntas"],
                "modern_genealogy": "Kant (KpV 1788) → Schiller (Brief an Körner 1793, ästhetische Freiheit) → Fürst (Wege zur Freiheit 2022)",
                "furst_methodological_choice": "intentionnellement éviter « Wille / volonté » comme cadre interprétatif",
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="concept_freiheitsmetaphysik_origenian",
        type="concept",
        label="Freiheitsmetaphysik (métaphysique de la liberté origénienne)",
        description=(
            "Freiheitsmetaphysik (« métaphysique de la liberté ») : concept "
            "forgé par Hengstermann 2016 et systématisé par Fürst 2022 pour "
            "désigner l'innovation philosophique fondamentale d'Origène — "
            "l'élévation de la liberté du rang d'accident (Aristote) au "
            "rang de « principe de la substance » (Prinzip der Substanz) "
            "des êtres rationnels. Conséquence ontologique : l'homme n'a pas "
            "seulement la liberté, il est liberté (« Der Mensch verfügt "
            "nicht nur über Freiheit; er ist Freiheit », Fürst p. 254). "
            "Dans cette métaphysique dynamique : (1) toute la réalité est "
            "mouvement ; (2) le mouvement « par soi-même » (δι᾽ αὑτοῦ) est "
            "le caractère propre des êtres rationnels ; (3) chaque être "
            "rationnel détermine librement sa propre place dans la "
            "hiérarchie de l'être ; (4) Dieu lui-même est pensé comme "
            "liberté ; (5) le monde est conçu comme « gigantesque réseau de "
            "libertés s'interagissant constamment » (Fürst p. 292) — proche "
            "des conceptions de la philosophie et théologie processuelles "
            "modernes"
        ),
        description_en=(
            "Freiheitsmetaphysik ('metaphysics of freedom'): concept coined "
            "by Hengstermann 2016 and systematized by Fürst 2022 to "
            "designate Origen's fundamental philosophical innovation — the "
            "elevation of freedom from the rank of accident (Aristotle) to "
            "the rank of 'principle of substance' (Prinzip der Substanz) of "
            "rational beings. Ontological consequence: man does not merely "
            "have freedom, he is freedom ('Der Mensch verfügt nicht nur "
            "über Freiheit; er ist Freiheit', Fürst p. 254). In this "
            "dynamic metaphysics: (1) all reality is movement; (2) movement "
            "'through itself' (δι᾽ αὑτοῦ) is the proper character of "
            "rational beings; (3) each rational being freely determines its "
            "own place in the hierarchy of being; (4) God himself is "
            "thought as freedom; (5) the world is conceived as a 'gigantic "
            "network of constantly interacting freedoms' (Fürst p. 292) — "
            "close to modern process philosophy and theology"
        ),
        description_de=(
            "Freiheitsmetaphysik = die origeneische Innovation, die Freiheit "
            "vom Akzidens zum « Prinzip der Substanz » (Hengstermann) zu "
            "erheben. Der Mensch hat nicht nur Freiheit, er ist Freiheit"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 247-290 + passim",
            chapter="Kap. VI complet — die Freiheitsmetaphysik des Origenes",
            chapter_actual="Métaphysique de la liberté origénienne — innovation conceptuelle pivot du livre",
            extra={
                "german_term": "Freiheitsmetaphysik",
                "english_term": "metaphysics of freedom",
                "key_origenian_passages": [
                    "De Principiis III 1,2-3 (théorie des quatre mouvements)",
                    "Comm. Jn XX 21,174 (libre décision = nature)",
                    "Comm. Rom. VIII 10,11 (arbitrii libertas détermine la nature)",
                    "Princ. II 6,5 (durch Wirkung langer Gewohnheit zur Natur)",
                ],
                "modern_genealogy": "Holz 1970 → Kobusch 1985 → Hengstermann 2016 → Fürst 2022",
                "ontological_status_of_freedom": "Prinzip der Substanz (et non accident)",
                "key_formula": "Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit",
                "parallel_modern_concepts": ["philosophie processuelle (Whitehead)", "théologie processuelle"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="concept_kompatibilistischer_libertarismus_origenian",
        type="concept",
        label="Libertarisme compatibiliste (Kompatibilistischer Libertarismus) — caractérisation origénienne",
        description=(
            "« Libertarisme compatibiliste » (kompatibilistischer "
            "Libertarismus) : caractérisation forgée par Fürst 2022 (Kap. VI "
            "4, p. 282-290) pour qualifier la position philosophique "
            "d'Origène. Origène professe un libertarisme radical (la liberté "
            "comme principe ontologique premier) tout en restant compatible "
            "avec des aspects déterminés de la réalité — chaîne stoïcienne "
            "des causes, préscience divine, providence. Différence majeure "
            "avec le compatibilisme stoïcien : pour les stoïciens, il "
            "s'agissait de concilier déterminisme et responsabilité au "
            "prix de ne pas vraiment pouvoir penser la liberté ; pour "
            "Origène, l'accent est mis sur l'autodétermination libre de "
            "l'homme et la question est de voir comment celle-ci est "
            "compatible avec l'action providentielle d'un Dieu également "
            "libre. Fürst note un parallèle terminologique miroir : "
            "Schallenberg parle de « libertarischer Kompatibilismus » à "
            "propos de Carnéade et Cicéron ; Christian List a employé la "
            "même expression dans Why Free Will is Real (2019)"
        ),
        description_en=(
            "'Compatibilist libertarianism' (kompatibilistischer "
            "Libertarismus): characterization coined by Fürst 2022 (Kap. VI "
            "4, p. 282-290) to qualify Origen's philosophical position. "
            "Origen professes a radical libertarianism (freedom as first "
            "ontological principle) while remaining compatible with "
            "determined aspects of reality — Stoic chain of causes, divine "
            "foreknowledge, providence. Major difference from Stoic "
            "compatibilism: for Stoics, it was about reconciling determinism "
            "and responsibility at the price of not really being able to "
            "think freedom; for Origen, emphasis is on man's free "
            "self-determination and the question is to see how this is "
            "compatible with the providential action of a likewise free God. "
            "Fürst notes a mirror terminological parallel: Schallenberg "
            "speaks of 'libertarischer Kompatibilismus' for Carneades and "
            "Cicero; Christian List used the same expression in Why Free "
            "Will is Real (2019)"
        ),
        description_de=(
            "Kompatibilistischer Libertarismus = Fürsts Charakterisierung "
            "der Position des Origenes: radikaler Libertarismus, der mit "
            "determinierten Aspekten der Wirklichkeit kompatibel bleibt"
        ),
        period="Patristic",
        metadata=furst_metadata(
            page_range="p. 282-290",
            chapter="Kap. VI 4 — Kompatibilistischer Libertarismus",
            chapter_actual="Concept-clé pour caractériser la position philosophique d'Origène — innovation conceptuelle de Fürst",
            extra={
                "german_term": "kompatibilistischer Libertarismus",
                "english_term": "compatibilist libertarianism",
                "applied_to": "Origenes (Fürst 2022) ; Carneades-Cicero (Schallenberg, miroir)",
                "modern_parallel": "Christian List, Warum der freie Wille existiert (2021) / Why Free Will is Real (2019)",
                "key_origenian_passages": [
                    "Princ. II 1,2 (GCS Orig. 5, 107-108) — toute multiplicité ordonnée à l'unité par la sagesse divine",
                    "Orat. 6,3 (GCS Orig. 2, 313) — préscience ne détermine pas",
                    "In Gen. frg. D 7,9 (OWD 1/1, 86) — possible et son contraire",
                    "Comm. Rom. VII 6,5 (SC 543, 318) — préscience suit l'événement",
                ],
                "key_difference_from_stoic_compatibilism": "Pour Origène, accent sur la liberté ; pour les stoïciens, accent sur le déterminisme",
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# ARGUMENTS (14 — Fürst's central scholarly theses)
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_furst_2022_continuity_homer_to_origen",
        type="argument",
        label="Continuité historique d'Homère à Origène (Fürst 2022)",
        description=(
            "Thèse fondamentale de Fürst 2022 : une histoire continue de "
            "plus d'un millénaire conduit la pensée de l'autodétermination "
            "humaine d'Homère (8e s. av. J.-C.) à Origène (3e s. ap. J.-C.). "
            "Six étapes : (1) prémisses dans l'épopée homérique et la "
            "tragédie grecque + Bible hébraïque ; (2) philosophie grecque "
            "classique et hellénistique (Platon, Aristote, Chrysippe, "
            "Épicure, Carnéade) ; (3) époque impériale (Épictète, Cicéron, "
            "médio-platonisme, Alexandre) ; (4) judéo-hellénisme (Philon) ; "
            "(5) christianisme primitif (Paul, Justin, Clément) ; (6) "
            "Origène = couronnement. L'innovation origénienne ne tombe pas "
            "du ciel — elle résulte de cette longue maturation"
        ),
        description_en=(
            "Fürst 2022 fundamental thesis: a continuous history of over a "
            "millennium leads the thought of human self-determination from "
            "Homer (8th c. BCE) to Origen (3rd c. CE). Six stages: (1) "
            "premises in Homeric epic and Greek tragedy + Hebrew Bible; (2) "
            "classical and Hellenistic Greek philosophy (Plato, Aristotle, "
            "Chrysippus, Epicurus, Carneades); (3) imperial period "
            "(Epictetus, Cicero, Middle Platonism, Alexander); (4) "
            "Judeo-Hellenism (Philo); (5) early Christianity (Paul, Justin, "
            "Clement); (6) Origen = culmination. Origen's innovation does "
            "not fall from the sky — it results from this long maturation"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="Zum Geleit p. 1-5 + structure du livre",
            chapter="Préface et Thematische Eingrenzungen + structure globale du livre",
            chapter_actual="Thèse architectonique du livre — continuité historique en 6 étapes",
            extra={
                "thesis_type": "scholarly_historical_claim",
                "confidence_in_furst": 0.95,
                "premises": [
                    "L'autodétermination est une thématique unifiable diachroniquement",
                    "Les concepts antiques τὸ ἐφ᾽ ἡμῖν, προαίρεσις, αὐτεξούσιον forment une famille",
                    "Le christianisme primitif a hérité et transformé l'héritage grec",
                ],
                "conclusion": "Origène est l'aboutissement (Höhepunkt) d'une trajectoire millénaire continue",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_origen_first_freedom_thinker",
        type="argument",
        label="Origène = premier penseur de la liberté de l'histoire (Fürst 2022)",
        description=(
            "Thèse centrale de Fürst 2022 (Kap. VI) : Origène est, "
            "temporellement avant Plotin, le premier penseur de la liberté "
            "de l'histoire. Il a saisi pour la première fois la liberté "
            "comme principe de l'être tout entier et a tracé sur cette "
            "base une métaphysique de la liberté dans laquelle Dieu, "
            "l'homme et le monde sont pensés à partir du principe de "
            "liberté. C'est l'innovation fondamentale d'Origène. « Jamais "
            "auparavant dans l'Antiquité on n'avait parlé de la liberté "
            "avec une exigence aussi haute et on ne lui avait assigné une "
            "place aussi centrale »"
        ),
        description_en=(
            "Fürst 2022 central thesis (Kap. VI): Origen is, temporally "
            "before Plotinus, the first thinker of freedom in history. He "
            "grasped freedom for the first time as principle of being as a "
            "whole and sketched on this basis a metaphysics of freedom in "
            "which God, man and world are thought from the principle of "
            "freedom. This is Origen's fundamental innovation. 'Never before "
            "in Antiquity had one spoken of freedom with such a high "
            "demand and given it such a central place'"
        ),
        description_de=(
            "Origenes ist der erste Freiheitsdenker der Geschichte: "
            "« zeitlich noch vor dem Neuplatoniker Plotin der erste "
            "Freiheitsdenker der Geschichte »"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="Zum Geleit p. 2 + Kap. VI p. 247-290",
            chapter="Zum Geleit + Kap. VI complet",
            chapter_actual="Thèse pivot de Fürst — priorité chronologique d'Origène sur Plotin",
            extra={
                "thesis_type": "scholarly_priority_claim",
                "confidence_in_furst": 0.95,
                "evidence": [
                    "Origène 185-254 CE ; Plotin 204-270 CE",
                    "De Principiis III 1 (Περὶ αὐτεξουσίου) = premier traité Sur la liberté digne de ce nom",
                    "Comm. Jn XXXII 16,187-189 = liberté élevée en 4e article de foi",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_origen_culmination_autexousion",
        type="argument",
        label="Origène = aboutissement du concept d'autexousion (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. V 2, p. 195-216) : Origène est le "
            "premier à faire de τὸ αὐτεξούσιον (« autodétermination ») un "
            "concept technique central. Le mot, attesté pour la première "
            "fois chez Diodore de Sicile XIV 105,4 (1er s. av. J.-C.) et "
            "Josèphe AJ IV 146 dans un sens politique-social, n'avait pénétré "
            "que progressivement le débat philosophique. Origène le transforme "
            "en « question d'importance suprême » dont il faut « développer "
            "le concept (ἔννοια) » (Princ. III 1,1) et lui consacre le "
            "premier traité philosophique systématique — le Περὶ αὐτεξουσίου "
            "(De Princ. III 1) = premier traité « Sur la liberté » digne de "
            "ce nom, là où tous ses prédécesseurs écrivaient « Sur le destin »"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. V 2, p. 195-216): Origen is the first "
            "to make τὸ αὐτεξούσιον ('self-determination') a central "
            "technical concept. The word, first attested in Diodorus "
            "Siculus XIV 105,4 (1st c. BCE) and Josephus AJ IV 146 in a "
            "political-social sense, had only gradually entered "
            "philosophical debate. Origen transforms it into a 'question of "
            "highest importance' for which one must 'develop the concept "
            "(ἔννοια)' (Princ. III 1,1) and dedicates to it the first "
            "systematic philosophical treatise — the Περὶ αὐτεξουσίου (De "
            "Princ. III 1) = first treatise 'On Freedom' worthy of the name, "
            "where all his predecessors wrote 'On Fate'"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 195-216",
            chapter="Kap. V 2 — Der Freiheitsbegriff des Origenes",
            chapter_actual="Première systématisation philosophique du concept d'autexousion par Origène",
            extra={
                "thesis_type": "scholarly_innovation_claim",
                "confidence_in_furst": 0.95,
                "key_passages": [
                    "Origène, Princ. III 1,1 (GCS Orig. 5, 195-196) — autexousion = question d'importance suprême",
                    "Origène, Hom. Jér. 18,3 (GCS Orig. 32, 154) — τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι",
                ],
                "title_innovation": "Περὶ εἱμαρμένης (Sur le destin, prédécesseurs) → Περὶ αὐτεξουσίου (Sur l'autodétermination, Origène)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_middle_platonist_origin_autexousion",
        type="argument",
        label="Origine médio-platonicienne du concept d'autexousion (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. III 3b, p. 126-132) : les "
            "médio-platoniciens (Plutarque, ps.-Plutarque De Fato, Alcinoos "
            "Didask. 26, Apulée De Platone I 12, Maxime de Tyr) développent "
            "contre le compatibilisme stoïcien la doctrine du destin "
            "hypothétique (« si x, alors y ») et postulent l'âme « sans "
            "maître » (αδέσποτος). Ils insistent que la décision est "
            "réellement non déterminée (« on les sent insister plutôt qu'on "
            "ne le lit »). Origène reprend directement cette tradition, "
            "notamment l'exemple du Laios (Cels. II 20)"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. III 3b, p. 126-132): Middle Platonists "
            "(Plutarch, ps.-Plutarch De Fato, Alcinous Didask. 26, Apuleius "
            "De Platone I 12, Maximus of Tyre) develop against Stoic "
            "compatibilism the doctrine of hypothetical fate ('if x, then "
            "y') and posit the 'masterless' (αδέσποτος) soul. They insist "
            "that decision is really not determined ('one feels rather than "
            "reads them insisting'). Origen takes up this tradition "
            "directly, especially the Laios example (Cels. II 20)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 126-132",
            chapter="Kap. III 3b — Undeterminierte Entscheidung",
            chapter_actual="Médio-platonisme comme source directe du libertarisme origénien",
            extra={
                "thesis_type": "scholarly_genealogical_claim",
                "confidence_in_furst": 0.9,
                "transmitters": [
                    "Plutarque, Stoic. repugn. 47, 1056 a-d",
                    "ps.-Plutarque, De Fato 4-11",
                    "Alcinoos, Didask. 26 (p. 54-55 Summerell/Zimmer)",
                    "Apulée, De Platone I 12 (p. 101-102 Moreschini)",
                    "Maxime de Tyr, Diss. 13,5 + 41,5 (Trapp)",
                ],
                "origen_uptake": "Cels. II 20 (Laios) ; Princ. III 1 (Freiheitstraktat)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_de_princ_iii_1_first_freedom_treatise",
        type="argument",
        label="De Principiis III 1 = premier traité Sur la liberté (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. V 2, p. 196-197) : De Principiis III "
            "1,1-24 d'Origène, conservé en grec dans la Philocalie ch. 21-27 "
            "et en latin dans la traduction de Rufin, est le premier "
            "traité philosophique systématique « Sur la liberté » digne de "
            "ce nom dans l'histoire de la philosophie. Tous les prédécesseurs "
            "jusqu'à Alexandre d'Aphrodise inclus écrivaient « Sur le "
            "destin » (Περὶ εἱμαρμένης / De fato) — c'est seulement avec "
            "Origène que le titre change : Περὶ αὐτεξουσίου / De arbitrii "
            "libertate. Méthode d'Olympe, Augustin (De libero arbitrio), "
            "etc. suivront cette nouvelle convention de titre. Diodore de "
            "Tarse et Grégoire de Nysse écriront Καθ᾿ εἱμαρμένης (« Contre "
            "le destin »)"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. V 2, p. 196-197): Origen's De "
            "Principiis III 1,1-24, preserved in Greek in Philocalia ch. "
            "21-27 and in Latin in Rufinus's translation, is the first "
            "systematic philosophical treatise 'On Freedom' worthy of the "
            "name in the history of philosophy. All predecessors up to and "
            "including Alexander of Aphrodisias wrote 'On Fate' (Περὶ "
            "εἱμαρμένης / De fato) — only with Origen does the title change: "
            "Περὶ αὐτεξουσίου / De arbitrii libertate. Methodius of "
            "Olympus, Augustine (De libero arbitrio), etc. will follow this "
            "new title convention. Diodorus of Tarsus and Gregory of Nyssa "
            "will write Καθ᾿ εἱμαρμένης ('Against Fate')"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 196-197",
            chapter="Kap. V 2 — innovation du titre",
            chapter_actual="Innovation génériquement-historique : du De Fato au De Libero Arbitrio",
            extra={
                "thesis_type": "scholarly_genre_history_claim",
                "confidence_in_furst": 0.95,
                "title_sequence_before_origen": [
                    "Chrysippe, Περὶ εἱμαρμένης (SVF II 912-1007)",
                    "Cicéron, De Fato",
                    "ps.-Plutarque, De Fato",
                    "Alexandre d'Aphrodise, De Fato",
                ],
                "title_sequence_after_origen": [
                    "Origène, Περὶ αὐτεξουσίου / De arbitrii libertate (= De Princ. III 1)",
                    "Méthode d'Olympe, Περὶ αὐτεξουσίου (vers 300)",
                    "Augustin, De libero arbitrio (393-395)",
                    "Diodore de Tarse, Καθ᾿ εἱμαρμένης",
                    "Grégoire de Nysse, Καθ᾿ εἱμαρμένης",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_furst_2022_freedom_fourth_article_of_faith",
        type="argument",
        label="Origène élève la liberté en quatrième article de foi (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. V 1, p. 193-194) : dans le "
            "Commentaire sur Jean XXXII 16,187-189, Origène ajoute à la "
            "confession trinitaire de foi (Père créateur, Fils, Esprit "
            "Saint) un quatrième article : « il faut croire que nous, en "
            "tant qu'êtres d'autodétermination (αὐτεξούσιοι), sommes punis "
            "pour ce que nous péchons et récompensés pour le bien que "
            "nous faisons ». La liberté est ainsi élevée au statut de "
            "doctrine fondamentale du christianisme — innovation théologique "
            "sans précédent qui marque la centralité dogmatique de la "
            "Freiheit chez Origène"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. V 1, p. 193-194): in the Commentary on "
            "John XXXII 16,187-189, Origen adds to the trinitarian confession "
            "of faith (Father creator, Son, Holy Spirit) a fourth article: "
            "'one must believe that we, as beings of self-determination "
            "(αὐτεξούσιοι), are punished for what we sin and rewarded for "
            "the good we do'. Freedom is thus elevated to the status of "
            "fundamental doctrine of Christianity — unprecedented theological "
            "innovation marking the dogmatic centrality of Freiheit in Origen"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 193-194",
            chapter="Kap. V 1 — Der zentrale Stellenwert der Freiheit",
            chapter_actual="Innovation dogmatique : liberté = 4e article de foi",
            extra={
                "thesis_type": "scholarly_theological_innovation_claim",
                "confidence_in_furst": 0.9,
                "key_passage": "Origène, Comm. Jn XXXII 16,187-189 (GCS Orig. 4, 451)",
                "innovation_significance": "premier élargissement du symbole de foi trinitaire en symbole quadripartite incluant la liberté",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_freedom_principle_of_substance",
        type="argument",
        label="Liberté = principe de la substance (non accident) chez Origène (Fürst/Hengstermann 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. VI 1, p. 252-254 ; suivant "
            "Hengstermann 2016) : l'innovation révolutionnaire d'Origène est "
            "de ne pas considérer la liberté comme accident à la manière "
            "d'Aristote, mais d'en faire le « principe de la substance » "
            "(Prinzip der Substanz) des êtres rationnels. Conséquence "
            "ontologique radicale : l'homme n'a pas seulement la liberté ; "
            "il EST liberté (« Der Mensch verfügt nicht nur über Freiheit; "
            "er ist Freiheit », Fürst p. 254). À l'ontologisation de la "
            "liberté correspond « l'élévation du mouvement au rang de "
            "premier principe de l'être » (Hengstermann 31 Anm. 45). C'est "
            "le cœur de la Freiheitsmetaphysik"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. VI 1, p. 252-254; following "
            "Hengstermann 2016): Origen's revolutionary innovation is not "
            "to consider freedom as accident in the Aristotelian manner, "
            "but to make it the 'principle of substance' (Prinzip der "
            "Substanz) of rational beings. Radical ontological consequence: "
            "man does not merely have freedom; he IS freedom ('Der Mensch "
            "verfügt nicht nur über Freiheit; er ist Freiheit', Fürst p. "
            "254). To the ontologization of freedom corresponds 'the "
            "elevation of movement to the rank of first principle of being' "
            "(Hengstermann 31 Anm. 45). This is the heart of "
            "Freiheitsmetaphysik"
        ),
        description_de=(
            "Origenes hat die Freiheit nicht als Akzidens, sondern als "
            "« Prinzip der Substanz » verstanden. Der Mensch verfügt nicht "
            "nur über Freiheit; er ist Freiheit"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 252-254",
            chapter="Kap. VI 1 — Welt in Bewegung",
            chapter_actual="Cœur de la Freiheitsmetaphysik origénienne",
            extra={
                "thesis_type": "scholarly_ontological_innovation_claim",
                "confidence_in_furst": 0.9,
                "key_passages": [
                    "Origène, Comm. Jn XX 21,174 (GCS Orig. 4, 353)",
                    "Origène, Princ. II 6,5 (GCS Orig. 5, 145)",
                    "Origène, Comm. Rom. VIII 10,11 (SC 543, 560)",
                ],
                "scholarly_genealogy": "Holz 1970 → Kobusch 1985 → Hengstermann 2016 → Fürst 2022",
                "contrast_with_aristotle": "Aristote : liberté = accident ; Origène : liberté = principe de substance",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_kompatibilistischer_libertarismus",
        type="argument",
        label="Origène = libertarisme compatibiliste (Fürst 2022)",
        description=(
            "Thèse caractéristique de Fürst 2022 (Kap. VI 4, p. 282-290) : "
            "la position philosophique d'Origène est correctement saisie par "
            "la formule « libertarisme compatibiliste » (kompatibilistischer "
            "Libertarismus). Libertarisme radical (la liberté est principe "
            "ontologique premier) compatible avec des aspects déterminés de "
            "la réalité : chaîne stoïcienne des causes physiques, préscience "
            "divine, providence ordonnée. Différence avec le compatibilisme "
            "stoïcien : pour les stoïciens, il s'agissait de concilier "
            "déterminisme et responsabilité au prix de ne pas vraiment "
            "pouvoir penser la liberté ; pour Origène, l'accent est mis "
            "sur la libre autodétermination humaine, et la question est "
            "de voir comment cela reste compatible avec l'action "
            "providentielle d'un Dieu lui-même libre. « Origène a clairement "
            "déplacé les accents loin du déterminisme vers le libertarisme "
            "et a reconnu à la liberté un statut ontologique qui n'existait "
            "pas auparavant »"
        ),
        description_en=(
            "Characteristic Fürst 2022 thesis (Kap. VI 4, p. 282-290): "
            "Origen's philosophical position is correctly grasped by the "
            "formula 'compatibilist libertarianism' (kompatibilistischer "
            "Libertarismus). Radical libertarianism (freedom is first "
            "ontological principle) compatible with determined aspects of "
            "reality: Stoic chain of physical causes, divine foreknowledge, "
            "ordered providence. Difference from Stoic compatibilism: for "
            "Stoics, it was about reconciling determinism and responsibility "
            "at the price of not really being able to think freedom; for "
            "Origen, emphasis is on free human self-determination, and the "
            "question is to see how this remains compatible with the "
            "providential action of a likewise free God. 'Origen clearly "
            "shifted the accents away from determinism toward libertarianism "
            "and granted freedom an ontological status that did not exist "
            "before'"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 282-290",
            chapter="Kap. VI 4 — Kompatibilistischer Libertarismus",
            chapter_actual="Caractérisation conceptuelle pivot de la position d'Origène",
            extra={
                "thesis_type": "scholarly_systematic_characterization",
                "confidence_in_furst": 0.9,
                "parallel_formulation_schallenberg": "« libertarischer Kompatibilismus » (Carnéade-Cicéron)",
                "parallel_formulation_list": "« compatibilist libertarianism » (Christian List, Why Free Will is Real, 2019)",
                "key_origenian_passages": [
                    "Princ. II 1,2 (GCS Orig. 5, 107-108)",
                    "Orat. 6,3 (GCS Orig. 2, 313)",
                    "In Gen. frg. D 7,9 (OWD 1/1, 86)",
                    "Comm. Rom. VII 6,5 (SC 543, 318)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_critique_dihle_augustine_thesis",
        type="argument",
        label="Critique de la thèse augusto-centrique de Dihle (Fürst 2022)",
        description=(
            "Thèse polémique de Fürst 2022 (Zum Geleit p. 2 + Anm. 1) : la "
            "perspective augusto-centrique dominante (Dihle 1982/1985 ; "
            "Warnach, Art. Freiheit ; Rosenberger, Determinismus und "
            "Freiheit) qui place Augustin comme tournant décisif de "
            "l'histoire du concept de liberté est unilatérale. Augustin a "
            "certes apporté une innovation décisive avec sa nouvelle "
            "conceptualisation de la volonté (Wille). Mais avant Augustin, "
            "« il y a eu une phase décisive » liée aux noms d'Origène et "
            "Plotin où la liberté humaine et divine fut placée dans de "
            "nouveaux contextes. Fürst déplace donc le « grand tournant » "
            "(großer Einschnitt) de l'histoire de la pensée de la liberté "
            "vers le 3e siècle ap. J.-C. et l'identifie au christianisme "
            "platonicien d'Origène"
        ),
        description_en=(
            "Polemical Fürst 2022 thesis (Zum Geleit p. 2 + Anm. 1): the "
            "dominant Augustine-centric perspective (Dihle 1982/1985; "
            "Warnach, Art. Freiheit; Rosenberger, Determinismus und "
            "Freiheit) which places Augustine as the decisive turn in the "
            "history of the concept of freedom is one-sided. Augustine did "
            "indeed bring a decisive innovation with his new conceptualization "
            "of the will (Wille). But before Augustine, 'there was a decisive "
            "phase' linked to the names of Origen and Plotinus where human "
            "and divine freedom was placed in new contexts. Fürst thus "
            "shifts the 'great turn' (großer Einschnitt) of the history of "
            "freedom thought to the 3rd century CE and identifies it with "
            "Origen's Platonist Christianity"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="Zum Geleit p. 1-5 + passim",
            chapter="Zum Geleit + Anm. 1 et passim",
            chapter_actual="Thèse polémique contre la marginalisation d'Origène",
            extra={
                "thesis_type": "scholarly_polemical_claim",
                "confidence_in_furst": 0.85,
                "polemical_targets": [
                    "Dihle, Vorstellung vom Willen (1985) / Theory of Will (1982)",
                    "Dihle, Problem der Entscheidungsfreiheit (1980)",
                    "Warnach, Art. Freiheit (RAC)",
                    "Rosenberger, Determinismus und Freiheit (2007)",
                ],
                "allies_cited": [
                    "Holz 1970 — Über den Begriff des Willens und der Freiheit bei Origenes",
                    "Kobusch 1985 — Die philosophische Bedeutung des Kirchenvaters Origenes",
                    "Hengstermann 2016 — Origenes und der Ursprung der Freiheitsmetaphysik",
                    "Perkams (Vortrag inédit) — Historical Origins of Our Concept of Freedom",
                ],
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_furst_2022_christian_philosophers_freedom_innovation",
        type="argument",
        label="Les platoniciens chrétiens primitifs comme innovateurs négligés du concept de liberté (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. IV introduction, p. 139-141) : les "
            "philosophes chrétiens primitifs (Justin, Athénagore, Irénée, "
            "Clément, Tertullien, Tatien) ont apporté une contribution "
            "décisive et largement méconnue au débat sur la liberté. "
            "Innovations identifiables : (1) ils comprennent τὸ ἐφ᾽ ἡμῖν et "
            "τὸ αὐτεξούσιον explicitement comme « libres » (ἐλεύθερος) et "
            "utilisent emphatiquement le terme politico-social ἐλευθερία ; "
            "(2) ils attribuent la libre autodétermination à tout homme "
            "comme dotation naturelle (et non comme but réservé à une élite) ; "
            "(3) la confrontation avec la gnose déplace le débat de la "
            "psychologie physique vers l'anthropologie-ontologie de "
            "l'autodétermination libre ; (4) ils introduisent les références "
            "scripturaires (Dt 30, 15-19 etc.). C'est sur ce terrain "
            "qu'Origène construira sa Freiheitsmetaphysik"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. IV introduction, p. 139-141): early "
            "Christian philosophers (Justin, Athenagoras, Irenaeus, "
            "Clement, Tertullian, Tatian) made a decisive and largely "
            "overlooked contribution to the freedom debate. Identifiable "
            "innovations: (1) they understand τὸ ἐφ᾽ ἡμῖν and τὸ αὐτεξούσιον "
            "explicitly as 'free' (ἐλεύθερος) and emphatically use the "
            "political-social term ἐλευθερία; (2) they attribute free "
            "self-determination to every human as natural endowment (not "
            "only as goal for an elite); (3) confrontation with Gnosis "
            "shifts the debate from physical psychology to anthropology-"
            "ontology of free self-determination; (4) they introduce "
            "scriptural references (Dt 30, 15-19 etc.). It is on this "
            "ground that Origen will build his Freiheitsmetaphysik"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 139-141",
            chapter="Kap. IV introduction — Freiheitspathos",
            chapter_actual="Thèse sur la contribution chrétienne primitive négligée — alignement avec Perkams",
            extra={
                "thesis_type": "scholarly_revisionist_claim",
                "confidence_in_furst": 0.9,
                "innovation_signature": "« Freiheitspathos » — l'enthousiasme pour la liberté propre aux chrétiens primitifs",
                "background_explanation_hypothesis": (
                    "Fürst suggère (sans certitude) que le pathos chrétien pour la liberté "
                    "vient de l'expérience adulte de la conversion : changer de religion "
                    "comme adulte présuppose la liberté"
                ),
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_aristotle_no_will_intellectualism",
        type="argument",
        label="Pas de concept de volonté chez Aristote — intellectualisme grec (Fürst 2022, suivant Frede)",
        description=(
            "Thèse de Fürst 2022 (Thematische Eingrenzungen 1a) reprenant "
            "Frede 2011 et Dihle 1985 : ni Platon ni Aristote ne possèdent "
            "un concept de volonté (Wille) comme force mentale-psychique "
            "indépendante de l'intellect. Domine chez les Grecs "
            "l'intellectualisme socrato-platonicien : l'agir humain découle "
            "directement de la pensée, sans instance supplémentaire pour "
            "traduire le pensé en agi (acte de décision et motif de l'action "
            "coïncident). Conséquence terminologique : Fürst évite "
            "systématiquement le mot « volonté » et reste près du sens "
            "originel de τὸ ἐφ᾽ ἡμῖν, προαίρεσις, αὐτεξούσιον. Les tentatives "
            "(Voelke 1973 sur la Stoa, Kenny 1979 sur Aristote, Irwin 1992) "
            "pour démontrer un proto-concept de volonté antique « ne "
            "peuvent convaincre »"
        ),
        description_en=(
            "Fürst 2022 thesis (Thematische Eingrenzungen 1a) following "
            "Frede 2011 and Dihle 1985: neither Plato nor Aristotle "
            "possesses a concept of will (Wille) as mental-psychic force "
            "independent of intellect. Greek thought is dominated by "
            "Socratic-Platonic intellectualism: human action follows directly "
            "from thinking, without additional instance to translate thought "
            "into deed (decision act and action motive coincide). "
            "Terminological consequence: Fürst systematically avoids the "
            "word 'will' and stays close to the original meaning of τὸ ἐφ᾽ "
            "ἡμῖν, προαίρεσις, αὐτεξούσιον. Attempts (Voelke 1973 on Stoa, "
            "Kenny 1979 on Aristotle, Irwin 1992) to demonstrate an ancient "
            "proto-concept of will 'cannot convince'"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 7-11 (Thematische Eingrenzungen 1a)",
            chapter="Thematische Eingrenzungen 1a — Zum Willensbegriff",
            chapter_actual="Position terminologique fondamentale du livre",
            extra={
                "thesis_type": "scholarly_terminological_position",
                "confidence_in_furst": 0.95,
                "alliance_with": [
                    "Dihle, Vorstellung vom Willen 31-46, 59-78",
                    "Frede, A Free Will 19 (« Neither Plato nor Aristotle has a notion of a will »)",
                    "Kahn, Discovering the Will 234-236",
                    "Pich, Προαίρεσις und Freiheit 94-100",
                    "Pohlenz, Stoa I 124",
                ],
                "opposed_attempts": [
                    "Voelke 1973 — L'idée de volonté dans le stoïcisme",
                    "Kenny 1979 — Aristotle's Theory of the Will",
                    "Irwin 1992 — Who Discovered the Will?",
                    "Frede 2011 sur Épictète",
                    "Karamanolis 135-140",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_furst_2022_stoic_eph_hemin_late_substantive",
        type="argument",
        label="τὸ ἐφ᾽ ἡμῖν substantivé non attesté pour la Vieille Stoa (Fürst 2022, suivant Bobzien)",
        description=(
            "Thèse philologique de Fürst 2022 (Anm. 9 ; suivant Bobzien "
            "Determinism and Freedom 280 Anm. 95) : la forme substantivée "
            "grecque τὸ ἐφ᾽ ἡμῖν n'est pas attestée pour le Vieux-Stoïcisme. "
            "Elle peut tout au plus se trouver derrière les formulations "
            "latines correspondantes in nostra potestate ou sita in nobis. "
            "L'attribution de τὸ αὐτεξούσιον à Zénon et Chrysippe par "
            "Hippolyte (Ref. I 21,2 = SVF II 975, image du chien lié au "
            "chariot) est anachronique — Hippolyte projette dans le texte "
            "ancien le vocabulaire de son temps. Le concept se développe "
            "techniquement seulement à partir du 1er s. ap. J.-C."
        ),
        description_en=(
            "Philological Fürst 2022 thesis (Anm. 9; following Bobzien "
            "Determinism and Freedom 280 Anm. 95): the substantivated Greek "
            "form τὸ ἐφ᾽ ἡμῖν is not attested for Old Stoicism. It can at "
            "most lie behind corresponding Latin formulations in nostra "
            "potestate or sita in nobis. The attribution of τὸ αὐτεξούσιον "
            "to Zeno and Chrysippus by Hippolytus (Ref. I 21,2 = SVF II "
            "975, dog-tied-to-cart image) is anachronistic — Hippolytus "
            "projects into the ancient text the vocabulary of his time. The "
            "concept develops technically only from the 1st c. CE onward"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 10, 90 Anm. 115, Anm. 11 + 9",
            chapter="Thematische Eingrenzungen 1a Anm. 9-11",
            chapter_actual="Thèse philologique de référence pour le statut tardif d'autexousion",
            extra={
                "thesis_type": "scholarly_philological_claim",
                "confidence_in_furst": 0.9,
                "alliance_with_bobzien": "Bobzien, Determinism and Freedom 280 Anm. 95",
                "earliest_attestations_autexousion": [
                    "Diodore de Sicile XIV 105,4 (1er s. av. J.-C., sens politique)",
                    "Josèphe AJ IV 146 + V 13,5 + XV 7,10 (sens politique-social)",
                    "Hippolyte Ref. I 21,2 (anachronisme rétrospectif sur Chrysippe)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_justin_first_explicit_freedom_decision",
        type="argument",
        label="Justin = première proclamation explicite de la liberté de la décision (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. IV 3, p. 155-157) : Justin Martyr "
            "(1 Apol. 43,4 ; SC 507, 240) est le premier dans l'histoire à "
            "proclamer explicitement la « liberté de la décision » (ἐλεύθερα "
            "προαίρεσις). « Dont l'importance ne peut pas être assez "
            "soulignée selon moi : pour la première fois dans cette "
            "histoire de problème — chez Philon et Épictète seules des "
            "préformes en passant — la liberté de la décision est "
            "expressément proclamée ». Innovation décisive qui transforme "
            "le débat hellénistique sur τὸ ἐφ᾽ ἡμῖν et προαίρεσις en débat "
            "sur la « liberté » (ἐλευθερία) au sens emphatique"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. IV 3, p. 155-157): Justin Martyr (1 "
            "Apol. 43,4; SC 507, 240) is the first in history to explicitly "
            "proclaim 'freedom of decision' (ἐλεύθερα προαίρεσις). 'Whose "
            "importance cannot be emphasized strongly enough in my view: "
            "for the first time in this problem-history — Philo and "
            "Epictetus have only en-passant pre-forms — the freedom of "
            "decision is expressly proclaimed'. Decisive innovation that "
            "transforms the Hellenistic debate on τὸ ἐφ᾽ ἡμῖν and "
            "προαίρεσις into a debate on 'freedom' (ἐλευθερία) in the "
            "emphatic sense"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 155-157",
            chapter="Kap. IV 3 — Justin der Märtyrer",
            chapter_actual="Innovation justinienne identifiée par Fürst",
            extra={
                "thesis_type": "scholarly_priority_claim",
                "confidence_in_furst": 0.9,
                "key_passage": "Justin, 1 Apol. 43,4 (SC 507, 240)",
                "preforms": [
                    "Philon, De Deo immut. 114 (II p. 80 Cohn/Wendland)",
                    "Épictète, Diss. I 4,18",
                ],
                "alignment_with": "Andresen, Justin und der mittlere Platonismus 340-345",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_furst_2022_world_as_network_of_freedoms",
        type="argument",
        label="Monde comme réseau dynamique de libertés (Fürst 2022 sur Origène)",
        description=(
            "Thèse cosmologique de Fürst 2022 (Zum Ausklang, p. 291-292 + "
            "Kap. VI 4) : Origène conçoit le monde comme un « gigantesque "
            "réseau de libertés s'interagissant constamment » — non comme "
            "doctrine statique de l'être mais comme doctrine dynamique de "
            "la liberté. Tout se met littéralement en mouvement. L'ordre "
            "naturel est compris comme tissu (εἱρμός) de libertés "
            "interconnectées que Dieu (lui-même libre) ordonne sans "
            "contraindre. Cette « nouvelle conceptualisation » concerne "
            "aussi Dieu : non plus comme être statique éternellement "
            "soustrait au monde, mais comme être en mouvement qui à la "
            "fois transcende le monde et s'y implique. Fürst note la "
            "proximité avec la philosophie et théologie processuelles "
            "modernes"
        ),
        description_en=(
            "Cosmological Fürst 2022 thesis (Zum Ausklang, p. 291-292 + "
            "Kap. VI 4): Origen conceives the world as a 'gigantic network "
            "of constantly interacting freedoms' — not as static doctrine "
            "of being but as dynamic doctrine of freedom. Everything "
            "literally comes into movement. The natural order is understood "
            "as a fabric (εἱρμός) of interconnected freedoms that God "
            "(himself free) orders without compelling. This 'new "
            "conceptualization' also concerns God: no longer as static "
            "being eternally withdrawn from the world, but as moved being "
            "that both transcends the world and involves itself in it. "
            "Fürst notes the proximity to modern process philosophy and "
            "theology"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 287-292",
            chapter="Kap. VI 4 + Zum Ausklang",
            chapter_actual="Conclusion cosmologique-théologique du livre",
            extra={
                "thesis_type": "scholarly_cosmological_interpretation",
                "confidence_in_furst": 0.85,
                "key_origenian_passages": [
                    "Princ. II 1,2 (GCS Orig. 5, 107-108)",
                    "Orat. 6,3 (GCS Orig. 2, 313)",
                ],
                "modern_resonance": "philosophie/théologie processuelle (Whitehead, Hartshorne, Cobb, Moltmann)",
                "innovation_signature": "passage d'une statische Seinslehre à une dynamische Freiheitslehre",
            },
        ),
        confidence=0.85,
    ),
    _node(
        id="argument_furst_2022_origen_against_three_determinisms",
        type="argument",
        label="Origène contre trois déterminismes : astrologique, stoïcien, gnostique (Fürst 2022)",
        description=(
            "Thèse de Fürst 2022 (Kap. V 1, p. 188-192) : Origène a "
            "défendu la liberté humaine contre trois fronts déterministes : "
            "(1) le déterminisme astrologique populaire répandu chez païens "
            "ET chrétiens (Princ. I praef. 5 ; In Gen. frg. D 7 = Philocalie "
            "23) ; (2) le déterminisme causal stoïcien fondé sur l'εἱμαρμένη "
            "(Princ. III 1,4 ss) ; (3) le déterminisme théologique gnostique "
            "qui attribuait la nature spirituelle / hyletique / psychique "
            "selon prédestination (Princ. III 1,6 ; Cels.). Originalité "
            "d'Origène : accepter le cadre stoïcien (la décision est insérée "
            "dans un contexte causal) tout en sauvant les alternatives "
            "réelles — « la nature de ce qui dépend de nous admet des "
            "possibilités différentes » (Cels. V 21)"
        ),
        description_en=(
            "Fürst 2022 thesis (Kap. V 1, p. 188-192): Origen defended "
            "human freedom against three deterministic fronts: (1) popular "
            "astrological determinism widespread among pagans AND "
            "Christians (Princ. I praef. 5; In Gen. frg. D 7 = Philocalia "
            "23); (2) Stoic causal determinism based on εἱμαρμένη (Princ. "
            "III 1,4 ff.); (3) Gnostic theological determinism that "
            "attributed spiritual / hylic / psychic nature by predestination "
            "(Princ. III 1,6; Cels.). Origen's originality: accept the "
            "Stoic frame (decision is inserted in a causal context) while "
            "saving real alternatives — 'the nature of what depends on us "
            "admits different possibilities' (Cels. V 21)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 188-192",
            chapter="Kap. V 1 — Der zentrale Stellenwert der Freiheit",
            chapter_actual="Stratégie polémique tripartite d'Origène",
            extra={
                "thesis_type": "scholarly_polemical_strategy_analysis",
                "confidence_in_furst": 0.9,
                "three_fronts": [
                    "déterminisme astrologique",
                    "déterminisme causal stoïcien (Schicksalsfügung)",
                    "déterminisme théologique gnostique (natures fixes)",
                ],
                "key_origenian_passages": [
                    "Princ. I praef. 5 (GCS Orig. 5, 12-13)",
                    "Princ. III 1,4-6 (GCS Orig. 5, 199-201)",
                    "Cels. V 21 (GCS Orig. 2, 23)",
                    "In Gen. frg. D 7,1 (OWD 1/1, 70-72)",
                ],
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# SYNTHESES (10 — one per main chapter/sub-section)
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_furst2022_homer_origins_selbstbestimmung",
        type="synthesis",
        label="Homère et la Bible hébraïque comme premières amorces de la Selbstbestimmung (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. I (p. 19-48) : dès Homère apparaissent "
            "les premières amorces d'une autodétermination humaine (Iliade I "
            "188-222 : Achille retient sa main au pommeau de son épée). Mais "
            "« chez Homère, l'homme n'est pas encore considéré comme "
            "l'auteur de sa propre décision » (Snell). La tragédie grecque "
            "(Eschyle, Sophocle, Euripide) puis la mythologie thématisent "
            "plus explicitement le rapport entre détermination par le destin "
            "et responsabilité humaine. La Bible hébraïque articule un "
            "« compatibilisme biblique » (histoire du salut + responsabilité "
            "personnelle, notamment chez Ézéchiel)"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. I (p. 19-48): from Homer on, the "
            "first sketches of human self-determination appear (Iliad I "
            "188-222: Achilles holds his hand at the sword pommel). But "
            "'in Homer, man is not yet considered the author of his own "
            "decision' (Snell). Greek tragedy (Aeschylus, Sophocles, "
            "Euripides) then mythology more explicitly thematize the "
            "relation between fate-determination and human responsibility. "
            "The Hebrew Bible articulates a 'biblical compatibilism' "
            "(salvation history + personal responsibility, especially in "
            "Ezekiel)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 19-48",
            chapter="Kap. I — Menschliche Selbstbestimmung im Alten Hellas und im Alten Israel",
            chapter_actual="Synthèse Fürst sur les origines mythiques/bibliques de la pensée de l'autodétermination",
            extra={
                "key_concept_introduced": "biblischer Kompatibilismus",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_chrysippus_compatibilism",
        type="synthesis",
        label="Chrysippe = premier compatibilisme rigoureux (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. II 4 (p. 73-91) : Chrysippe a "
            "développé le premier compatibilisme systématique. "
            "L'assentiment (συγκατάθεσις) est « ce qui dépend de nous » "
            "bien que pleinement inscrit dans la chaîne causale du destin. "
            "La distinction des causes (causae perfectae et principales vs "
            "adiuvantes et proximae) permet de sauver la responsabilité "
            "morale dans un déterminisme causal sans lacune. Limite : "
            "Chrysippe ne peut penser de réelles alternatives — il faudra "
            "Carnéade, les médio-platoniciens, Alexandre et Origène pour "
            "élargir ce cadre. Fürst suit l'analyse pionnière de Bobzien "
            "1998 (Determinism and Freedom in Stoic Philosophy)"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. II 4 (p. 73-91): Chrysippus "
            "developed the first systematic compatibilism. Assent "
            "(συγκατάθεσις) is 'what depends on us' though fully inscribed "
            "in fate's causal chain. The distinction of causes (perfectae "
            "et principales vs adiuvantes et proximae) saves moral "
            "responsibility within seamless causal determinism. Limit: "
            "Chrysippus cannot think real alternatives — Carneades, Middle "
            "Platonists, Alexander and Origen are needed to widen this "
            "frame. Fürst follows Bobzien's pioneering 1998 analysis"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 73-91",
            chapter="Kap. II 4 — Kompatibilismus des Stoikers Chrysipp",
            chapter_actual="Synthèse Fürst sur le compatibilisme chrysippien",
            extra={"primary_modern_source": "Bobzien 1998"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_carneades_will_innovation",
        type="synthesis",
        label="Carnéade introduit la voluntas comme cause non-extérieure (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. II 6 (p. 96-100) : Carnéade (selon "
            "Cicéron De Fato 23-25) introduit pour la première fois la "
            "distinction entre règne du matériel (où règnent nécessité "
            "causale et hasard) et règne du spirituel-psychique (où peut "
            "se penser une auto-motion volontaire). « Il n'y a pour notre "
            "volonté pas de causes extérieures et antécédentes » — la "
            "voluntas a sa cause « dans la nature elle-même » de l'âme. "
            "Pas décisif vers une ontologie dualiste matière/esprit qui "
            "permettra le libertarisme platonicien — voie qui mènera à "
            "Origène. Schallenberg qualifie Carnéade-Cicéron de "
            "« libertarischer Kompatibilismus » (parallèle miroir au "
            "« kompatibilistischer Libertarismus » que Fürst attribue à "
            "Origène)"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. II 6 (p. 96-100): Carneades (per "
            "Cicero De Fato 23-25) first introduces the distinction "
            "between realm of the material (where causal necessity and "
            "chance rule) and realm of the spiritual-psychic (where "
            "voluntary self-motion can be thought). 'For our will there are "
            "no external and antecedent causes' — voluntas has its cause "
            "'in nature itself' of the soul. Decisive step toward a "
            "matter/spirit dualist ontology enabling Platonist "
            "libertarianism — path leading to Origen. Schallenberg "
            "qualifies Carneades-Cicero as 'libertarischer Kompatibilismus' "
            "(mirror parallel to the 'kompatibilistischer Libertarismus' "
            "Fürst attributes to Origen)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 96-100",
            chapter="Kap. II 6 — Karneades",
            chapter_actual="Synthèse Fürst sur Carnéade comme précurseur du libertarisme",
            extra={
                "mirror_concept": "« libertarischer Kompatibilismus » (Schallenberg 302)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_imperial_freedom_debate",
        type="synthesis",
        label="L'omniprésence du débat sur la liberté à l'époque impériale (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. III (p. 101-138) : le débat sur "
            "l'autodétermination devient quasi-omniprésent dans la culture "
            "intellectuelle de l'époque impériale (1er-3e s. ap. J.-C.). "
            "Sources préservées : Épictète (Diatribes IV 1 = Sur la "
            "liberté), Cicéron (De Fato, postulat de la voluntas), "
            "médio-platoniciens (Plutarque Stoic. repugn. 47 ; ps.-Plutarque "
            "De Fato ; Alcinoos Didask. 26 ; Apulée De Platone I 12 ; Maxime "
            "de Tyr Diss. 13 et 41), Galien, Sextus Empiricus (hypot. III "
            "70), le cynique Œnomaos de Gadara, l'épicurien Diogénianos, "
            "le péripatéticien Alexandre d'Aphrodise (De Fato, vers "
            "198-209). Astrologie et fatalisme stoïcien sont les fronts "
            "principaux. C'est sur cet arrière-plan riche qu'apparaissent "
            "les philosophes chrétiens primitifs"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. III (p. 101-138): the debate on "
            "self-determination becomes nearly omnipresent in imperial-age "
            "intellectual culture (1st-3rd c. CE). Preserved sources: "
            "Epictetus (Diatribes IV 1 = On Freedom), Cicero (De Fato, "
            "postulate of voluntas), Middle Platonists (Plutarch Stoic. "
            "repugn. 47; ps.-Plutarch De Fato; Alcinous Didask. 26; "
            "Apuleius De Platone I 12; Maximus of Tyre Diss. 13, 41), "
            "Galen, Sextus Empiricus (hypot. III 70), the Cynic Oenomaos "
            "of Gadara, the Epicurean Diogenianos, the Peripatetic "
            "Alexander of Aphrodisias (De Fato, c. 198-209). Astrology and "
            "Stoic fatalism are the main fronts. It is on this rich "
            "background that early Christian philosophers appear"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 101-138",
            chapter="Kap. III — Ethik der Freiheit in der römischen Kaiserzeit",
            chapter_actual="Synthèse Fürst sur le contexte intellectuel impérial",
            extra={},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_alexander_alternativenoffenheit",
        type="synthesis",
        label="Alexandre d'Aphrodise exige des alternatives ouvertes (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. III 3c (p. 132-138) : Alexandre "
            "d'Aphrodise, péripatéticien titulaire de la chaire "
            "aristotélicienne à Athènes (198-209), produit le seul traité "
            "Sur le destin entièrement conservé de l'époque impériale "
            "(édition Bruns, Suppl. Aristot. II/2 ; trad. Sharples 1983, "
            "Zierl 1995). Son argument central contre Chrysippe : pour que "
            "la décision soit véritablement nôtre, il faut qu'il existe "
            "une alternative réellement ouverte (Alternativenoffenheit). "
            "L'argument standard est repris : le déterminisme abolit "
            "blâme/louange/châtiment/récompense, rendant la vie humaine "
            "impossible. Origène intégrera cette exigence dans Princ. III 1"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. III 3c (p. 132-138): Alexander of "
            "Aphrodisias, Peripatetic holder of the Aristotelian chair at "
            "Athens (198-209), produces the only fully preserved treatise "
            "On Fate of imperial period (Bruns ed., Suppl. Aristot. II/2; "
            "trans. Sharples 1983, Zierl 1995). His central argument "
            "against Chrysippus: for the decision to be truly ours, there "
            "must exist a really open alternative (Alternativenoffenheit). "
            "Standard argument repeated: determinism abolishes "
            "blame/praise/punishment/reward, making human life impossible. "
            "Origen will integrate this requirement in Princ. III 1"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 132-138",
            chapter="Kap. III 3c — Wahlfreiheit : Alexander von Aphrodisias",
            chapter_actual="Synthèse Fürst sur Alexandre",
            extra={"key_innovation": "Alternativenoffenheit (real open alternatives)"},
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_philo_alexandria_pivot",
        type="synthesis",
        label="Philon d'Alexandrie = maillon décisif vers le christianisme primitif (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. IV 1 (p. 141-149) : Philon "
            "d'Alexandrie (30/40 ap. J.-C.) est le maillon décisif entre "
            "philosophie hellénistique et pensée chrétienne primitive de la "
            "liberté. Trois innovations majeures dans son traité De Deo "
            "immut. 47-49 : (1) première occurrence attestée de la syntagme "
            "ἐλεύθερα προαίρεσις ; (2) premier à attribuer la capacité "
            "d'autodétermination libre à chaque homme (pas seulement à "
            "l'élite sage stoïcienne) ; (3) fondation théologique de la "
            "liberté humaine sur Dieu « Père de la liberté » (πατὴρ "
            "ἐλευθερίας). Origène le suivra presque directement"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. IV 1 (p. 141-149): Philo of "
            "Alexandria (30/40 CE) is the decisive link between Hellenistic "
            "philosophy and early Christian thought on freedom. Three "
            "major innovations in his treatise De Deo immut. 47-49: (1) "
            "first attested occurrence of the syntagma ἐλεύθερα προαίρεσις; "
            "(2) first to attribute the capacity of free self-determination "
            "to every human (not only to the Stoic sage elite); (3) "
            "theological grounding of human freedom on God 'Father of "
            "freedom' (πατὴρ ἐλευθερίας). Origen will follow him almost "
            "directly"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 141-149",
            chapter="Kap. IV 1 — Philon von Alexandria",
            chapter_actual="Synthèse Fürst sur Philon comme maillon décisif",
            extra={
                "key_innovations": ["ἐλεύθερα προαίρεσις (première occurrence)", "universalisation à tout homme", "πατὴρ ἐλευθερίας"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_justin_first_christian_freiheits_philosophy",
        type="synthesis",
        label="Justin Martyr = première proclamation chrétienne explicite de la liberté (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. IV 3 (p. 152-161) : Justin Martyr "
            "(Apol. 43-44 + 2 Apol. 6-7, rédigées à Rome entre 150 et 155 "
            "CE) proclame pour la première fois explicitement la « liberté "
            "de la décision » (ἐλεύθερα προαίρεσις). Innovation majeure "
            "dont « l'importance ne peut être assez soulignée ». Quatre "
            "accents nouveaux : (1) répétition emphatique du qualificatif "
            "« libre » ; (2) preuve par le changement moral du même "
            "individu (au lieu d'alternatives synchroniques) ; (3) liaison "
            "avec eschatologie chrétienne (jugement et rétribution) ; (4) "
            "première amorce — que développera Origène — vers l'idée que "
            "la libre décision détermine non seulement comment l'homme est "
            "mais qui il est (ontologie de la liberté). Justin platonicien "
            "chrétien combine critique platonicienne du déterminisme stoïcien "
            "et fondement biblique"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. IV 3 (p. 152-161): Justin Martyr "
            "(Apol. 43-44 + 2 Apol. 6-7, written at Rome 150-155 CE) "
            "explicitly proclaims for the first time 'freedom of decision' "
            "(ἐλεύθερα προαίρεσις). Major innovation whose 'importance "
            "cannot be emphasized strongly enough'. Four new accents: (1) "
            "emphatic repetition of the qualifier 'free'; (2) proof by "
            "moral change of the same individual (instead of synchronic "
            "alternatives); (3) link with Christian eschatology (judgment "
            "and retribution); (4) first hint — that Origen will develop — "
            "toward the idea that free decision determines not only how "
            "man is but who he is (ontology of freedom). Justin the "
            "Christian Platonist combines Platonist critique of Stoic "
            "determinism with biblical grounding"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 152-161",
            chapter="Kap. IV 3 — Justin der Märtyrer",
            chapter_actual="Synthèse Fürst sur Justin",
            extra={
                "primary_modern_sources": ["Andresen, Justin und der mittlere Platonismus 340-345", "Amand, Fatalisme et liberté 201-207"],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_clement_phusis_prohairesis",
        type="synthesis",
        label="Clément d'Alexandrie pose l'opposition phusis/prohairesis (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. IV 5 (p. 180-186) : Clément "
            "d'Alexandrie pose l'opposition φύσις / προαίρεσις qui ouvre "
            "la voie à Origène. Le perfectionnement éthique de l'homme "
            "« devient sa nature » — sa disposition intérieure (διάθεσις) "
            "se transforme en nature seconde. Cette opposition entre nature "
            "et liberté préfigure l'opposition augustinienne natura / "
            "voluntas. Kobusch (Selbstbestimmte Freiheit 51) souligne cette "
            "filiation : « opposition de προαίρεσις et οὐσία chez les Pères "
            "grecs et de natura et voluntas chez Augustin ». Origène "
            "construira systématiquement sur ce terrain en inversant la "
            "relation : la liberté n'est plus contre la nature, elle est "
            "au-dessus d'elle et la détermine"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. IV 5 (p. 180-186): Clement of "
            "Alexandria posits the φύσις / προαίρεσις opposition that "
            "opens the way to Origen. Ethical perfecting of man 'becomes "
            "his nature' — his inner disposition (διάθεσις) transforms "
            "into second nature. This nature/freedom opposition prefigures "
            "the Augustinian natura / voluntas opposition. Kobusch "
            "(Selbstbestimmte Freiheit 51) emphasizes this filiation: "
            "'opposition of προαίρεσις and οὐσία in the Greek Fathers and "
            "of natura and voluntas in Augustine'. Origen will build "
            "systematically on this ground while reversing the relation: "
            "freedom is no longer against nature, it is above it and "
            "determines it"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 180-186",
            chapter="Kap. IV 5 — Clemens von Alexandria",
            chapter_actual="Synthèse Fürst sur Clément comme pivot doctrinal",
            extra={
                "key_opposition": "φύσις vs προαίρεσις",
                "key_passage": "Clément, Strom. II 110,4-111,1 (GCS Clem. Al. 24, 173) = SVF II 714 ; Strom. VII 46,9",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_origen_central_freedom",
        type="synthesis",
        label="Origène — la liberté au centre du dogme et de la philosophie (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. V (p. 187-246) : Origène a fait de la "
            "liberté le pivot central de son système. Quatre traits "
            "définitifs : (1) la libre autodétermination est un article "
            "fondamental de la prédication ecclésiastique (Princ. I praef. "
            "5 ; Comm. Jn XXXII 16 = quatrième article de foi après Père, "
            "Fils, Esprit) ; (2) le premier traité philosophique systématique "
            "« Sur la liberté » de l'histoire (Περὶ αὐτεξουσίου = De Princ. "
            "III 1, conservé en grec dans Philocalie 21-27) ; (3) intégration "
            "philosophique de la théorie stoïcienne de l'action "
            "(Chrysippe-Épictète) avec exigence platonicienne d'alternatives "
            "ouvertes ; (4) défense triple contre déterminisme astrologique, "
            "stoïcien et gnostique. Lebensziel partagé avec Platon : « bien "
            "vivre » (καλῶς βιοῦν, εὖ πράττειν)"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. V (p. 187-246): Origen made freedom "
            "the central pivot of his system. Four defining traits: (1) "
            "free self-determination is a fundamental article of ecclesial "
            "preaching (Princ. I praef. 5; Comm. Jn XXXII 16 = fourth "
            "article of faith after Father, Son, Spirit); (2) the first "
            "systematic philosophical treatise 'On Freedom' in history "
            "(Περὶ αὐτεξουσίου = De Princ. III 1, preserved in Greek in "
            "Philocalia 21-27); (3) philosophical integration of Stoic "
            "action theory (Chrysippus-Epictetus) with Platonist demand for "
            "open alternatives; (4) triple defense against astrological, "
            "Stoic and Gnostic determinism. Lebensziel shared with Plato: "
            "'good living' (καλῶς βιοῦν, εὖ πράττειν)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 187-246",
            chapter="Kap. V — Das Freiheitsdenken des Origenes (complet)",
            chapter_actual="Synthèse Fürst sur le concept de liberté origénien",
            extra={
                "key_origenian_innovation": "élévation de la liberté à article de foi + premier De Libertate de l'histoire",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_origenian_freiheitsmetaphysik",
        type="synthesis",
        label="La métaphysique de la liberté origénienne (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Kap. VI (p. 247-290) : Origène ne s'est "
            "pas contenté d'affirmer la liberté humaine — il en a fait le "
            "principe métaphysique de toute la réalité (Freiheitsmetaphysik). "
            "Six éléments : (1) ontologie du mouvement à quatre degrés "
            "(Princ. III 1,2-3 : ἔξωθεν / ἐξ αὑτοῦ / ἀφ᾽ αὑτοῦ / δι᾽ αὑτοῦ) ; "
            "(2) la liberté = principe de la substance, non accident "
            "(Hengstermann) ; (3) chaque être rationnel détermine librement "
            "son rang ontologique entre animal et Dieu (Hom. Ézéch. 3,8 : "
            "homo homo / tier-mensch) ; (4) Dieu lui-même = liberté ; (5) "
            "monde = réseau dynamique de libertés ordonnées par la "
            "providence sans contrainte ; (6) compatibilité libertarisme-"
            "préscience-providence = « libertarisme compatibiliste ». "
            "Origène fait de la métaphysique statique une métaphysique "
            "dynamique de la liberté — proche des conceptions "
            "processuelles modernes"
        ),
        description_en=(
            "Fürst 2022 synthesis, Kap. VI (p. 247-290): Origen did not "
            "merely affirm human freedom — he made it the metaphysical "
            "principle of all reality (Freiheitsmetaphysik). Six elements: "
            "(1) ontology of movement at four levels (Princ. III 1,2-3: "
            "ἔξωθεν / ἐξ αὑτοῦ / ἀφ᾽ αὑτοῦ / δι᾽ αὑτοῦ); (2) freedom = "
            "principle of substance, not accident (Hengstermann); (3) each "
            "rational being freely determines its ontological rank between "
            "animal and God (Hom. Ezek. 3,8: homo homo / tier-mensch); (4) "
            "God himself = freedom; (5) world = dynamic network of "
            "freedoms ordered by providence without coercion; (6) "
            "compatibility libertarianism-foreknowledge-providence = "
            "'compatibilist libertarianism'. Origen turns static metaphysics "
            "into a dynamic metaphysics of freedom — close to modern "
            "process conceptions"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 247-290",
            chapter="Kap. VI — Die Freiheitsmetaphysik des Origenes (complet)",
            chapter_actual="Synthèse Fürst pivot — la métaphysique de la liberté origénienne",
            extra={
                "key_innovation": "première métaphysique de la liberté de l'histoire",
                "primary_modern_source": "Hengstermann, Freiheitsmetaphysik (2016)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_furst2022_after_origen_new_freedom_debate",
        type="synthesis",
        label="Le débat sur la liberté après Origène — un nouvel horizon (Fürst 2022)",
        description=(
            "Synthèse Fürst 2022, Zum Ausklang (p. 291-292) : depuis "
            "Origène, le débat sur déterminisme et liberté se meut sur un "
            "nouveau niveau. Le long chemin vers la liberté est parcouru "
            "en ce sens que la liberté a été établie comme principe non "
            "seulement de l'agir mais de l'être. À partir du 3e s. ap. "
            "J.-C., le débat qui s'était ouvert au 3e s. av. J.-C. "
            "continue sur de nouvelles voies. Les platoniciens chrétiens "
            "(Origène, Grégoire de Nysse) et païens (Plotin, Porphyre, "
            "Proclus) reprennent le modèle d'action stoïcien mais "
            "transforment l'ordre d'être en concevant la liberté comme "
            "principe. Même Dieu — concept faîtier de la métaphysique de "
            "l'être — est désormais déterminé comme liberté (déjà chez "
            "Irénée et Tertullien en germe)"
        ),
        description_en=(
            "Fürst 2022 synthesis, Zum Ausklang (p. 291-292): since Origen, "
            "the debate on determinism and freedom moves on a new level. "
            "The long road to freedom has been traveled in the sense that "
            "freedom has been established as principle not only of action "
            "but of being. From the 3rd c. CE on, the debate that began "
            "with force in the 3rd c. BCE continues on new paths. Christian "
            "Platonists (Origen, Gregory of Nyssa) and pagan ones "
            "(Plotinus, Porphyry, Proclus) take up the Stoic action model "
            "but transform the order of being by conceiving freedom as "
            "principle. Even God — capstone concept of the metaphysics of "
            "being — is now determined as freedom (already in germ in "
            "Irenaeus and Tertullian)"
        ),
        period="Modern",
        metadata=furst_metadata(
            page_range="p. 291-292",
            chapter="Zum Ausklang",
            chapter_actual="Synthèse-conclusion du livre",
            extra={},
        ),
        confidence=0.9,
    ),
]
