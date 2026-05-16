"""Dihle 1982 B1 — NEW_INSERTS (new nodes).

Bilingual FR/EN descriptions. Greek terms in transliteration where the source
uses Greek; original polytonic only when verbatim in the MD. Types match the
ontology in `knowledge graph/ontology/node_types.json`.

Sections :
  - PERSONS    : scholar_albrecht_dihle (only new person — Dihle himself)
  - WORKS      : (none — Dihle's volume is a `publication`, not a `work`)
  - PUBLICATIONS : pub_dihle_1982_theory_of_will
  - CONCEPTS   : concept_greek_intellectualism_dihle
  - SYNTHESES  : 6 lecture syntheses + 2 thematic syntheses = 8
  - ARGUMENTS  : 12 scholarly arguments

Note: PUBLICATIONS are merged into NEW_WORKS bucket only in the apply script
(both are top-level new nodes); we keep them separate here to mirror the
node-type partitioning of the ontology.
"""
from __future__ import annotations

from typing import Any

from dihle_1982_b1_utils import dihle_metadata, dump_metadata


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
    if period is not None:
        n["period"] = period
    if needs_evidence:
        n["needs_evidence"] = True
    n.update(extra)
    return n


# =============================================================================
# PERSONS (1) — Dihle himself
# =============================================================================

NEW_PERSONS: list[dict[str, Any]] = [
    _node(
        id="scholar_albrecht_dihle",
        type="person",
        label="Albrecht Dihle",
        description=(
            "Albrecht Dihle (10 mars 1923 - 22 janvier 2020), philologue "
            "classique allemand et historien des religions, professeur a "
            "Cologne (1958-1968), Heidelberg (1968-1991, Chaire de "
            "philologie classique) et professeur honoraire a Munich. "
            "Polymathe atypique : helleniste, indianiste (forme aupres de "
            "Paul Hacker), specialiste de la patristique grecque, des "
            "rapports entre culture grecque et christianisme primitif, et "
            "des contacts greco-indiens. Membre de la Heidelberger Akademie "
            "der Wissenschaften (1966) et de plusieurs academies "
            "etrangeres. Ses Sather Classical Lectures (Berkeley 1974), "
            "publiees en 1982 sous le titre *The Theory of Will in Classical "
            "Antiquity*, soutiennent une these celebre et tres controversee : "
            "la notion philosophique de volonte (Wille / voluntas) est une "
            "invention chretienne, plus precisement augustinienne, etrangere "
            "a l'intellectualisme grec. Cette these s'inscrit dans la "
            "lignee de Pohlenz, Snell et Frankel mais radicalise leur "
            "position. Elle a ete contestee par Michael Frede (qui place "
            "la genese plutot chez Epictete) et par Susanne Bobzien (qui "
            "refuse la categorie meme de 'volonte' comme grille de lecture "
            "anachronique). Autres ouvrages majeurs : *Die goldene Regel* "
            "(1962), *Der Prolog des Ovid und das antike Propemptikon* "
            "(1971), *Die griechische und lateinische Literatur der "
            "Kaiserzeit* (1989), *Die Griechen und die Fremden* (1994), "
            "ainsi que de nombreux travaux indologiques et patristiques"
        ),
        description_en=(
            "Albrecht Dihle (10 March 1923 - 22 January 2020), German "
            "classical philologist and historian of religion, professor at "
            "Cologne (1958-1968), Heidelberg (1968-1991, Chair of "
            "classical philology) and honorary professor at Munich. "
            "Atypical polymath : Hellenist, Indologist (trained under "
            "Paul Hacker), specialist of Greek patristic literature, of the "
            "relations between Greek culture and early Christianity, and "
            "of Greco-Indian contacts. Member of the Heidelberger Akademie "
            "der Wissenschaften (1966) and of several foreign academies. "
            "His Sather Classical Lectures (Berkeley 1974), published in "
            "1982 as *The Theory of Will in Classical Antiquity*, defend "
            "a famous and highly controversial thesis : the philosophical "
            "notion of will (Wille / voluntas) is a Christian, more "
            "specifically Augustinian invention, foreign to Greek "
            "intellectualism. This thesis follows the lineage of Pohlenz, "
            "Snell and Frankel but radicalises their position. It has been "
            "contested by Michael Frede (who locates the genesis rather in "
            "Epictetus) and by Susanne Bobzien (who rejects the very "
            "category of 'will' as an anachronistic reading grid). Other "
            "major works : *Die goldene Regel* (1962), *Der Prolog des "
            "Ovid und das antike Propemptikon* (1971), *Die griechische "
            "und lateinische Literatur der Kaiserzeit* (1989), *Die "
            "Griechen und die Fremden* (1994), and numerous Indological "
            "and patristic studies"
        ),
        period="Contemporary",
        metadata={
            "role": "scholar",
            "period": "Contemporary",
            "surname": "Dihle",
            "given_name": "Albrecht",
            "birth_date": "1923-03-10",
            "death_date": "2020-01-22",
            "nationality": "German",
            "wikidata_qid": "Q60648",
            "affiliations": [
                "University of Cologne (1958-1968)",
                "University of Heidelberg, Chair of Classical Philology (1968-1991)",
                "Heidelberger Akademie der Wissenschaften (1966-)",
                "Honorary professor, LMU Munich",
            ],
            "specialty": (
                "Classical philology, Greek patristics, Indology, history "
                "of religion, relations between Greek thought and Christianity"
            ),
            "key_books": [
                "Die goldene Regel (Gottingen 1962)",
                "The Theory of Will in Classical Antiquity, Sather Classical Lectures 48 (Berkeley 1982)",
                "Die griechische und lateinische Literatur der Kaiserzeit (Munich 1989)",
                "Die Griechen und die Fremden (Munich 1994)",
            ],
            "central_thesis_1982": (
                "The philosophical concept of will (Wille / voluntas) is a "
                "Christian, more specifically Augustinian invention, alien "
                "to Greek intellectualism : Greek moral psychology explains "
                "action through rational cognition of means and ends, not "
                "through an autonomous voluntary faculty."
            ),
            "historiographical_lineage": [
                "scholar_pohlenz_max (precursor : Stoicism without 'will')",
                "scholar_snell_bruno (precursor : discovery of mind, evolution of self)",
                "scholar_voelke_andre_jean (predecessor : L'idee de volonte dans le stoicisme 1973)",
                "scholar_kahn_charles (broad agreement on Greek terms vs voluntas)",
            ],
            "main_interlocutors_disagreeing": [
                "person_frede_michael_1940_2007 (locates genesis in Epictetus, not Augustine)",
                "person_bobzien_susanne_contemporary (rejects 'will' as anachronistic category)",
            ],
            "confidence": 0.95,
            "verified": True,
        },
        confidence=0.95,
    ),
]


# =============================================================================
# WORKS (0) — Dihle is modern; his book is a publication, not an ancient work.
# =============================================================================

NEW_WORKS: list[dict[str, Any]] = []


# =============================================================================
# PUBLICATIONS (1)
# =============================================================================

NEW_PUBLICATIONS: list[dict[str, Any]] = [
    _node(
        id="pub_dihle_1982_theory_of_will",
        type="publication",
        label="Dihle 1982, The Theory of Will in Classical Antiquity",
        description=(
            "Dihle, Albrecht. *The Theory of Will in Classical Antiquity*. "
            "Sather Classical Lectures, vol. 48. Berkeley / Los Angeles / "
            "London : University of California Press, 1982. xi + 276 p. "
            "Reedition souple en 2020 (meme pagination). Six conferences "
            "prononcees a Berkeley en automne 1974, profondement remaniees "
            "pour la publication. Note bibliographique : ISBN 978-0-520-"
            "04059-5 (1982 hardcover), 978-0-520-30681-3 (2020 paperback "
            "reprint). These principale : 'the Greeks, in their attempts "
            "to analyze and to evaluate human action, never developed a "
            "distinct concept of will' (p. 20 / md ll. 3055-3057). "
            "Argument : la psychologie morale grecque est intellectualiste "
            "(connaissance du bien -> action) ; l'experience biblique "
            "(soumission a Yahveh) introduit une notion non-cognitive de "
            "volonte ; Paul l'utilise implicitement (Rom 7 ; usage "
            "indifferencie de theleo / ginosko) sans terme dedie ; "
            "Augustin, sous le double aiguillon du manicheisme et du "
            "pelagianisme, forge l'instrument philosophique : 'the notion "
            "of will, as it is used as a tool of analysis and description "
            "in many philosophical doctrines from the early Scholastics "
            "to Schopenhauer and Nietzsche, was invented by St. Augustine' "
            "(p. 144 / md ll. 5426-5428). Structure : Lect. I Cosmologies "
            "du IIe siecle ap. J.-C. ; Lect. II-III The Greek View of "
            "Human Action ; Lect. IV St. Paul and Philo ; Lect. V "
            "Philosophy and Religion in Late Antiquity ; Lect. VI St. "
            "Augustine and His Concept of Will. Receptions divergentes : "
            "Frede 2011 (39 citations, interlocuteur central, situe la "
            "genese chez Epictete) ; Bobzien 1998 / 2001 (refus de la "
            "categorie) ; Sorabji (mediation : Augustin unique synthese "
            "responsabilite morale + willpower) ; Cary 2007, Karamanolis "
            "2021, Hausmann & Noller 2021 (heritage continu)"
        ),
        description_en=(
            "Dihle, Albrecht. *The Theory of Will in Classical Antiquity*. "
            "Sather Classical Lectures, vol. 48. Berkeley / Los Angeles / "
            "London : University of California Press, 1982. xi + 276 pp. "
            "Paperback reprint 2020 (same pagination). Six lectures "
            "delivered at Berkeley in autumn 1974, thoroughly reworked for "
            "publication. ISBN 978-0-520-04059-5 (1982 hardcover), 978-0-"
            "520-30681-3 (2020 paperback reprint). Central thesis : 'the "
            "Greeks, in their attempts to analyze and to evaluate human "
            "action, never developed a distinct concept of will' (p. 20). "
            "Argument : Greek moral psychology is intellectualist "
            "(knowledge of the good -> action) ; biblical experience "
            "(obedience to Yahweh) introduces a non-cognitive notion of "
            "will ; Paul uses it implicitly (Rom 7 ; undifferentiated use "
            "of thelo / ginosko) without a dedicated term ; Augustine, "
            "under the double prod of Manicheism and Pelagianism, forges "
            "the philosophical instrument : 'the notion of will, as it is "
            "used as a tool of analysis and description in many "
            "philosophical doctrines from the early Scholastics to "
            "Schopenhauer and Nietzsche, was invented by St. Augustine' "
            "(p. 144). Structure : Lect. I Cosmological Conceptions in the "
            "2nd c. AD ; Lect. II-III The Greek View of Human Action ; "
            "Lect. IV St. Paul and Philo ; Lect. V Philosophy and Religion "
            "in Late Antiquity ; Lect. VI St. Augustine and His Concept of "
            "Will. Divergent receptions : Frede 2011 (39 citations, "
            "central interlocutor, locates genesis in Epictetus) ; Bobzien "
            "1998 / 2001 (rejection of the category) ; Sorabji (mediation : "
            "Augustine uniquely synthesises moral responsibility + "
            "willpower) ; Cary 2007, Karamanolis 2021, Hausmann & Noller "
            "2021 (continuous reception history)"
        ),
        period="Contemporary",
        metadata={
            "author": "Albrecht Dihle",
            "year": 1982,
            "publisher": "University of California Press",
            "series": "Sather Classical Lectures",
            "volume": 48,
            "isbn_hardcover_1982": "978-0-520-04059-5",
            "isbn_paperback_2020_reprint": "978-0-520-30681-3",
            "pages": "xi + 276",
            "lectures_delivered_at": "University of California, Berkeley, autumn 1974",
            "bibtex_key": "dihle-1982-theory-of-will-classical-antiquity",
            "zotero_key": "dihle1982theoryofwill",
            "key_claim": (
                "The philosophical concept of will is a Christian "
                "(Augustinian) invention, foreign to Greek "
                "intellectualism."
            ),
            "central_quotations_md_lines": {
                "greeks_no_distinct_concept_of_will_p20": "ll. 3054-3057",
                "augustine_inventor_p144": "ll. 5425-5428",
                "paul_implicit_will_p84": "ll. 3719-3726",
                "paul_no_term_for_will_p84": "ll. 3727-3734",
                "conscience_pauline_p77_78": "ll. 3577-3609",
            },
            "structure": [
                {"lecture": "I", "title": "Cosmological Conceptions in the Second Century A.D.", "md_lines": "63-67, ~165"},
                {"lecture": "II", "title": "The Greek View of Human Action I", "md_lines": "~920"},
                {"lecture": "III", "title": "The Greek View of Human Action II", "md_lines": "7799+"},
                {"lecture": "IV", "title": "St. Paul and Philo", "md_lines": "8073+, ~3050"},
                {"lecture": "V", "title": "Philosophy and Religion in Late Antiquity", "md_lines": "8892+, ~4300"},
                {"lecture": "VI", "title": "St. Augustine and His Concept of Will", "md_lines": "9890+, ~5420"},
            ],
            "cited_by_core_works": {
                "frede_2011_free_will": 39,
                "bobzien_1998_determinism": 2,
                "eliasson_2008_freedom_in_the_hellenistic_world": 3,
            },
            "claimed_by": "scholar_albrecht_dihle",
            "publication_status": "monograph",
        },
        confidence=0.99,
    ),
]


# =============================================================================
# CONCEPTS (1) — Dihle's organising category of Greek intellectualism
# =============================================================================

NEW_CONCEPTS: list[dict[str, Any]] = [
    _node(
        id="concept_greek_intellectualism_dihle",
        type="concept",
        label="Intellectualisme grec (categorie organisatrice de Dihle 1982)",
        description=(
            "Categorie historiographique organisatrice de Dihle 1982 : "
            "l'intellectualisme grec designe le trait structurel commun "
            "qui rendrait la pensee grecque incapable de developper un "
            "concept autonome de volonte. Selon Dihle, dans toutes les "
            "ecoles de l'ethique antique (Socrate, Platon, Aristote, "
            "Stoa, Epicure, Plotin), l'action humaine s'explique par la "
            "cognition rationnelle des fins et des moyens : 'intention was "
            "always an intellectual phenomenon, and striving was attributed "
            "to instinct or emotion' (Dihle 1982 p. 20). Le choix delibere "
            "(prohairesis) presuppose la connaissance d'un objet "
            "determine ; le desir rationnel (boulesis) reste un acte de "
            "l'intellect saisissant le bien ; l'assentiment stoicien "
            "(synkatathesis) est lui aussi cognitif, meme s'il presente "
            "une apparence quasi-volontariste (Lect. III, p. 60 / md ll. "
            "2549-2580). Cette categorie n'est pas presente sous ce nom "
            "chez les Anciens : c'est un construit scolaire moderne dont "
            "Snell, Pohlenz et Voelke avaient prepare la voie. Dihle la "
            "radicalise en la posant comme veritable cesure entre paganisme "
            "et christianisme augustinien. Position contestee : Frede 2011 "
            "y voit une caricature ; Bobzien 1998 considere que projeter "
            "l'antithese 'intellectualisme vs volontarisme' sur le materiau "
            "hellenistique est anachronique. Dans le KG, le concept "
            "fonctionne comme grille analytique (Dihle's interpretive lens) "
            "plutot que comme position doctrinale d'un ancien"
        ),
        description_en=(
            "Historiographical organising category of Dihle 1982 : Greek "
            "intellectualism designates the structural feature shared "
            "across Greek ethical schools (Socrates, Plato, Aristotle, "
            "Stoa, Epicurus, Plotinus) that allegedly made Greek thought "
            "incapable of developing an autonomous concept of will. For "
            "Dihle, human action is everywhere explained by rational "
            "cognition of ends and means : 'intention was always an "
            "intellectual phenomenon, and striving was attributed to "
            "instinct or emotion' (Dihle 1982 p. 20). Deliberate choice "
            "(prohairesis) presupposes knowledge of a definite object ; "
            "rational desire (boulesis) remains an intellectual act "
            "grasping the good ; Stoic assent (synkatathesis) is itself "
            "cognitive, despite its quasi-voluntarist appearance (Lect. "
            "III, p. 60). The category is not present under this name in "
            "ancient sources : it is a modern scholarly construct prepared "
            "by Snell, Pohlenz and Voelke. Dihle radicalises it as a "
            "genuine caesura between paganism and Augustinian Christianity. "
            "Contested : Frede 2011 sees a caricature ; Bobzien 1998 views "
            "projecting the antithesis 'intellectualism vs voluntarism' "
            "onto Hellenistic material as anachronistic. In the KG, the "
            "concept functions as an analytical grid (Dihle's interpretive "
            "lens) rather than as the doctrinal position of any ancient "
            "thinker"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 20-30, 49-90 (Lect. II-III)",
            md_line_range="ll. 3054-3127, 2549-2580",
            lecture="II-III (Greek View of Human Action)",
            dihle_section="Categorie organisatrice de l'ensemble du volume",
            extra={
                "category_type": "scholarly_interpretive_framework",
                "anchor_quotation": (
                    "the Greeks, in their attempts to analyze and to "
                    "evaluate human action, never developed a distinct "
                    "concept of will (Dihle 1982 p. 20)"
                ),
                "preceded_by_scholarly_lineage": [
                    "Pohlenz, Die Stoa (1948-49) - Stoa without 'will'",
                    "Snell, Die Entdeckung des Geistes (1946) - evolution of self",
                    "Voelke, L'idee de volonte dans le stoicisme (1973)",
                ],
                "contested_by": [
                    "Frede 2011 (genesis at Epictetus, not Augustine)",
                    "Bobzien 1998 (anachronistic projection)",
                    "Kenny (Aristotle has theory of will)",
                    "Inwood (proto-voluntarist Seneca)",
                ],
                "german_label": "griechischer Intellektualismus",
                "english_label": "Greek intellectualism",
            },
        ),
        confidence=0.9,
    ),
]


# =============================================================================
# SYNTHESES (8) — 6 per-lecture + 2 thematic
# =============================================================================

NEW_SYNTHESES: list[dict[str, Any]] = [
    _node(
        id="synthesis_dihle1982_lec1_cosmology_second_century",
        type="synthesis",
        label="Dihle 1982 Lect. I — Cosmologies du IIe siecle : volonte divine vs ordre rationnel",
        description=(
            "Synthese de la premiere conference des Sather (Dihle 1982 p. "
            "1-19 / md ll. ~139-2789). Dihle oppose deux modeles "
            "cosmologiques au IIe siecle ap. J.-C. : (1) le modele grec "
            "philosophique (stoiciens, platoniciens, peripateticiens), pour "
            "qui le cosmos est ordre, regularite, beaute, etabli par une "
            "activite divine ou aucune volonte separee ne s'insere "
            "spontanement dans des processus cosmiques rationnels ('no "
            "separate will spontaneously interferes', md ll. 178-181) ; "
            "(2) le modele biblique (judaisme hellenistique puis "
            "christianisme), pour qui l'univers procede de l'intention "
            "arbitraire et volontaire du createur divin (ll. 229-243). "
            "Dihle annonce ici la categorie qui guidera tout le volume : "
            "l'intellectualisme grec, herite de la theologie philosophique, "
            "n'a pas besoin d'un concept autonome de volonte parce que "
            "l'ordre du monde se deduit deja de la raison divine. Le "
            "modele biblique l'exige au contraire, parce que la creation "
            "est libre, ex nihilo, et susceptible de revocation. Ce chapitre "
            "introductif pose ainsi la base cosmologique de toute la these"
        ),
        description_en=(
            "Synthesis of Sather Lecture I (Dihle 1982 p. 1-19). Dihle "
            "contrasts two cosmological models in the 2nd c. AD : (1) the "
            "Greek philosophical model (Stoics, Platonists, Peripatetics), "
            "for which the cosmos is order, regularity, beauty, established "
            "by divine activity where 'no separate will spontaneously "
            "interferes with rational cosmic processes' (p. 4) ; (2) the "
            "biblical model (Hellenistic Judaism then Christianity), for "
            "which the universe proceeds from the arbitrary and "
            "voluntary intention of the divine creator (p. 8-10). Dihle "
            "thereby introduces the category that guides the entire "
            "volume : Greek intellectualism, inherited from philosophical "
            "theology, has no need for an autonomous concept of will "
            "because the order of the world already follows from divine "
            "reason. The biblical model, by contrast, requires it because "
            "creation is free, ex nihilo, and revocable. This introductory "
            "lecture thus lays the cosmological foundation of the whole "
            "thesis"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 1-19",
            md_line_range="ll. ~139-2789",
            lecture="I (Cosmological Conceptions in the Second Century A.D.)",
            dihle_section="Lect. I, introduction du contraste structurel",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "Greek philosophical theology",
                    "biblical cosmology",
                    "divine will vs rational order",
                    "creation ex nihilo",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_dihle1982_lec2_greek_intellectualism_action",
        type="synthesis",
        label="Dihle 1982 Lect. II — Vue grecque de l'action humaine (intellectualisme socratico-platonicien)",
        description=(
            "Synthese de la deuxieme conference (Dihle 1982 p. 20-47 / md "
            "ll. ~3050-7079). Dihle commence par la formulation centrale : "
            "'the Greeks, in their attempts to analyze and to evaluate "
            "human action, never developed a distinct concept of will' "
            "(p. 20). Trois moments : (a) le paradoxe socratique 'nul ne "
            "fait le mal volontairement' (Protagoras 358c-d) reduit "
            "l'action a la cognition du bien ; (b) Aristote (Ethique a "
            "Nicomaque III, VII) introduit la deliberation, la prohairesis "
            "(choix delibere) et la boulesis (volition rationnelle), mais "
            "ces concepts restent intellectuels : ils presupposent toujours "
            "la saisie cognitive de quelque chose de determine ; (c) "
            "l'akrasia (ll. 7933 - 'incontinence') n'est pas une "
            "decision contre la raison mais une defaillance de la cognition. "
            "Dihle reconnait que l'akrasia ouvre theoriquement un espace "
            "pour 'quelque chose comme' une faculte de la volonte, mais "
            "Aristote ne franchit jamais ce pas. Le projet pratique grec "
            "passe par l'eudaimonia, la phronesis et l'arete — non par "
            "l'obeissance volontaire a un commandement"
        ),
        description_en=(
            "Synthesis of Sather Lecture II (Dihle 1982 p. 20-47). Dihle "
            "opens with the volume's central formulation : 'the Greeks, in "
            "their attempts to analyze and to evaluate human action, never "
            "developed a distinct concept of will' (p. 20). Three moments : "
            "(a) the Socratic paradox 'no one does wrong willingly' "
            "(Protagoras 358c-d) reduces action to cognition of the good ; "
            "(b) Aristotle (Nicomachean Ethics III, VII) introduces "
            "deliberation, prohairesis (deliberate choice) and boulesis "
            "(rational volition), but these concepts remain intellectual : "
            "they always presuppose cognitive grasp of something definite ; "
            "(c) akrasia ('incontinence') is not a decision against reason "
            "but a failure of cognition. Dihle concedes that akrasia "
            "theoretically opens space for 'something like' a faculty of "
            "will, but Aristotle never takes this step. The Greek practical "
            "project runs through eudaimonia, phronesis and arete — not "
            "through voluntary obedience to a commandment"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 20-47",
            md_line_range="ll. 3050-7079",
            lecture="II (Greek View of Human Action I)",
            dihle_section="Lect. II, Socrate-Platon-Aristote",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "Greek intellectualism",
                    "prohairesis",
                    "boulesis",
                    "akrasia",
                    "Socratic paradox",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_dihle1982_lec3_stoic_assent_cognitive",
        type="synthesis",
        label="Dihle 1982 Lect. III — Stoa, Epicure, Plotin : l'assentiment reste cognitif",
        description=(
            "Synthese de la troisieme conference (Dihle 1982 p. 48-89 / md "
            "ll. 7799-8892). Examen detaille des theories hellenistiques et "
            "imperiales. Dihle concede que la synkatathesis stoicienne "
            "'seems to fit in with a voluntaristic theory' (p. 60 / md "
            "ll. 2549-2580), mais demontre qu'elle reste fondamentalement "
            "cognitive : l'assentiment a une impression est decrit "
            "rigoureusement comme un acte de la raison qui evalue une "
            "phantasia kataleptike. Toutes les phases de l'action stoicienne "
            "(perception, imagination, assentiment, impulsion) sont "
            "entierement rationnelles. La 'faible assentiment' (asthenes "
            "synkatathesis, SVF 3.172, 3.548) ne brise pas le caractere "
            "cognitif. Cleanthe (ap. Sen. ep. 41.1 / quaest. nat.) montre "
            "qu'on peut etre 'mene par les dieux' tout en assentissant — "
            "fata volentem ducunt. Plotin (Enn. III.1, IV.8, VI.8) accentue "
            "encore l'intellectualisme : la liberte est synonyme de retour "
            "a l'Un par la nous. Conclusion : aucun courant grec, meme "
            "tardif, n'echappe a la cesure intellectualiste"
        ),
        description_en=(
            "Synthesis of Sather Lecture III (Dihle 1982 p. 48-89). "
            "Detailed examination of Hellenistic and imperial theories. "
            "Dihle concedes that Stoic synkatathesis 'seems to fit in with "
            "a voluntaristic theory' (p. 60), but demonstrates that it "
            "remains fundamentally cognitive : assent to an impression is "
            "rigorously described as an act of reason evaluating a "
            "phantasia kataleptike. All phases of Stoic action (perception, "
            "imagination, assent, impulse) are entirely rational. 'Weak "
            "assent' (asthenes synkatathesis, SVF 3.172, 3.548) does not "
            "break the cognitive character. Cleanthes (ap. Sen. ep. 41.1) "
            "shows that one can be 'led by the gods' while assenting — "
            "fata volentem ducunt. Plotinus (Enn. III.1, IV.8, VI.8) "
            "further intensifies intellectualism : freedom is synonymous "
            "with return to the One through nous. Conclusion : no Greek "
            "current, however late, escapes the intellectualist caesura"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 48-89",
            md_line_range="ll. 7799-8892",
            lecture="III (Greek View of Human Action II)",
            dihle_section="Lect. III, Stoa, Epicure, Plotin",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "synkatathesis (assent)",
                    "Stoic cognitive psychology",
                    "Plotinian intellectualism",
                    "asthenes synkatathesis",
                    "fata volentem ducunt (Cleanthes apud Seneca)",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_dihle1982_lec4_paul_philo_implicit_will",
        type="synthesis",
        label="Dihle 1982 Lect. IV — Paul et Philon : volonte implicite sans terme dedie",
        description=(
            "Synthese de la quatrieme conference (Dihle 1982 p. 75-100 / "
            "md ll. 8073-8892). Coeur de la these. Paul (lecture de Rom 7, "
            "Gal 5, 1 Cor) emploie 'thelo' et 'ginosko' de maniere "
            "indifferenciee, sans terme dedie pour la volonte (p. 84 / md "
            "ll. 3727-3734) : 'There is no such term in the language of "
            "St. Paul and his contemporaries'. Pourtant, le contenu "
            "conceptuel est present de facon implicite : 'it is a will, "
            "as distinguished from all intellectual achievements [...] as "
            "well as from all unconscious and spontaneous emotions, which "
            "responds to the commandment of God' (p. 84 / md ll. 3721-"
            "3726). Le conflit de Rom 7,15-24 ('je ne fais pas ce que je "
            "veux, mais je fais ce que je hais') n'est plus une akrasia "
            "cognitive aristotelicienne mais l'experience d'une faculte "
            "volitionnelle scindee. La doctrine de la conscience (syneidesis) "
            "p. 77-78 est distinctive : elle ne provient pas de l'intellect "
            "examinant la conduite (comme dans la philosophie grecque), mais "
            "temoigne subjectivement et spontanement de l'accomplissement "
            "de la loi de Dieu, jusque chez les paiens qui ignorent la "
            "Torah (Rom 2,14-15). Philon represente le pendant judeo-"
            "hellenistique : la theologie biblique de la volonte divine "
            "(theleo, boulesis) se concilie avec le langage philosophique "
            "(p. 91-100 / md ll. 3717-3735)"
        ),
        description_en=(
            "Synthesis of Sather Lecture IV (Dihle 1982 p. 75-100). Core "
            "of the thesis. Paul (reading Rom 7, Gal 5, 1 Cor) uses 'thelo' "
            "and 'ginosko' indiscriminately, without a dedicated term for "
            "will (p. 84) : 'There is no such term in the language of "
            "St. Paul and his contemporaries'. Yet the conceptual content "
            "is implicitly present : 'it is a will, as distinguished from "
            "all intellectual achievements [...] as well as from all "
            "unconscious and spontaneous emotions, which responds to the "
            "commandment of God' (p. 84). The conflict of Rom 7,15-24 ('I "
            "do not do what I want, but I do the very thing I hate') is no "
            "longer an Aristotelian cognitive akrasia but the experience of "
            "a split volitional faculty. The doctrine of conscience "
            "(syneidesis) p. 77-78 is distinctive : it does not originate "
            "from the intellect examining conduct (as in Greek philosophy), "
            "but testifies subjectively and spontaneously to fulfilment of "
            "God's law, even among gentiles who never knew the Torah (Rom "
            "2,14-15). Philo represents the Judeo-Hellenistic counterpart"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 75-100",
            md_line_range="ll. 8073-8892",
            lecture="IV (St. Paul and Philo)",
            dihle_section="Lect. IV, naissance implicite du concept",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "Paul Rom 7",
                    "thelo / ginosko indistinct",
                    "syneidesis (conscience)",
                    "Hebrew obedience to commandment",
                    "Philo of Alexandria",
                    "implicit concept without dedicated term",
                ],
                "key_anchor_quote_md_lines": "ll. 3719-3734, ll. 3577-3609",
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="synthesis_dihle1982_lec5_late_antiquity_plotinus_no_will",
        type="synthesis",
        label="Dihle 1982 Lect. V — Antiquite tardive : Plotin et neoplatoniciens restent intellectualistes",
        description=(
            "Synthese de la cinquieme conference (Dihle 1982 p. 101-122 / "
            "md ll. 8892-9890). Dihle montre que la transition vers "
            "l'antiquite tardive ne produit pas spontanement le concept de "
            "volonte du cote grec : Plotin (Enn. VI.8 *Sur le libre arbitre "
            "et la volonte de l'Un*), bien qu'il introduise une terminologie "
            "qu'on pourrait croire voluntariste (autexousios, boulesis), "
            "reduit en derniere instance la liberte a la coincidence de "
            "l'agent avec sa nature intellective. Pour Plotin la 'tolma' "
            "designe la chute de l'ame (md ll. 4645-4671) mais l'ascension "
            "demeure une affaire de nous, non de volonte autonome. Porphyre "
            "et Iamblique heritent de cette structure. La 'volonte de l'Un' "
            "que Plotin propose (Enn. VI.8) reste sous forte tutelle "
            "intellectualiste : 'will = activity of nous'. En parallele, "
            "le christianisme grec (Origene, Gregoire de Nysse, Nemese "
            "d'Emese) commence a parler de proairesis, autexousion et "
            "thelesis, mais reste tributaire des categories grecques. Le "
            "concept proprement philosophique de volonte n'emerge pas en "
            "milieu grec — la rupture viendra du cote latin et chretien"
        ),
        description_en=(
            "Synthesis of Sather Lecture V (Dihle 1982 p. 101-122). Dihle "
            "shows that the transition to late antiquity does not "
            "spontaneously produce the concept of will on the Greek side : "
            "Plotinus (Enn. VI.8 *On Free Will and the Will of the One*), "
            "though introducing seemingly voluntarist terminology "
            "(autexousios, boulesis), ultimately reduces freedom to the "
            "agent's coincidence with intellective nature. For Plotinus, "
            "'tolma' designates the soul's fall (p. 117) but ascent remains "
            "a matter of nous, not autonomous will. Porphyry and Iamblichus "
            "inherit this structure. The 'will of the One' Plotinus "
            "proposes (Enn. VI.8) remains under strong intellectualist "
            "tutelage : 'will = activity of nous'. In parallel, Greek "
            "Christianity (Origen, Gregory of Nyssa, Nemesius of Emesa) "
            "begins to use proairesis, autexousion, thelesis — but remains "
            "tributary to Greek categories. The properly philosophical "
            "concept of will does not emerge in Greek milieu — the rupture "
            "will come from the Latin and Christian side"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 101-122",
            md_line_range="ll. 8892-9890",
            lecture="V (Philosophy and Religion in Late Antiquity)",
            dihle_section="Lect. V, neoplatoniciens et patristique grecque",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "Plotinus Enn. VI.8",
                    "tolma (soul's fall)",
                    "autexousion (Greek patristic)",
                    "proairesis (Greek patristic)",
                    "intellectualist reduction of freedom",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="synthesis_dihle1982_lec6_augustine_invents_voluntas",
        type="synthesis",
        label="Dihle 1982 Lect. VI — Augustin invente le concept philosophique de voluntas",
        description=(
            "Synthese de la sixieme conference (Dihle 1982 p. 123-150 / md "
            "ll. 9890-11043). Conclusion du volume. Augustin, sous la "
            "double pression de la polemique anti-manicheenne (volonte "
            "responsable du mal sans nature mauvaise substantielle, p. 128 / "
            "md ll. 5185-5202) et de la querelle pelagienne (grace vs "
            "liberum arbitrium, p. 137-140 / md ll. 5271-5360), forge "
            "l'instrument philosophique : 'the notion of will, as it is "
            "used as a tool of analysis and description in many "
            "philosophical doctrines from the early Scholastics to "
            "Schopenhauer and Nietzsche, was invented by St. Augustine' "
            "(p. 144 / md ll. 5425-5428). Trois sources convergentes : (1) "
            "anthropologie biblique (homo imago Dei, capacite de reponse "
            "obeissante) ; (2) ontologie neoplatonicienne (le mal comme "
            "privation, la volonte comme orientation de l'amour) ; (3) "
            "introspection psychologique (Confessiones VIII : la division "
            "interieure du vouloir/non-vouloir). Le terme voluntas existait "
            "en latin (Ciceron, Seneque) mais sans valeur technique : il "
            "designait souvent l'oppe stoicienne ou le velle ordinaire. "
            "Augustin lui confere un statut de faculte mentale autonome, "
            "irreductible a l'intellect comme a l'emotion. Innovation "
            "decisive : la theologie trinitaire (De Trinitate IX-X) lie "
            "directement memoria-intellectus-voluntas, faisant de la "
            "volonte une faculte au meme rang ontologique que la memoire "
            "et l'intelligence. C'est cette doctrine qui se transmettra "
            "via les scolastiques jusqu'a Schopenhauer et Nietzsche"
        ),
        description_en=(
            "Synthesis of Sather Lecture VI (Dihle 1982 p. 123-150). "
            "Conclusion of the volume. Augustine, under the double pressure "
            "of anti-Manichean polemic (will responsible for evil without "
            "substantial evil nature, p. 128) and Pelagian controversy "
            "(grace vs liberum arbitrium, p. 137-140), forges the "
            "philosophical instrument : 'the notion of will, as it is used "
            "as a tool of analysis and description in many philosophical "
            "doctrines from the early Scholastics to Schopenhauer and "
            "Nietzsche, was invented by St. Augustine' (p. 144). Three "
            "converging sources : (1) biblical anthropology (homo imago "
            "Dei, capacity for obedient response) ; (2) Neoplatonic "
            "ontology (evil as privation, will as direction of love) ; (3) "
            "psychological introspection (Confessions VIII : interior "
            "division of willing / not-willing). The Latin term voluntas "
            "existed (Cicero, Seneca) but without technical value : it "
            "often designated Stoic horme or ordinary velle. Augustine "
            "gives it the status of an autonomous mental faculty, "
            "irreducible to intellect or emotion. Decisive innovation : "
            "Trinitarian theology (De Trinitate IX-X) directly links "
            "memoria-intellectus-voluntas, placing will at the same "
            "ontological rank as memory and intelligence"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 123-150",
            md_line_range="ll. 9890-11043",
            lecture="VI (St. Augustine and His Concept of Will)",
            dihle_section="Lect. VI, conclusion : Augustin inventeur",
            extra={
                "synthesis_type": "lecture_synthesis",
                "themes": [
                    "voluntas as autonomous faculty",
                    "anti-Manichean polemic",
                    "Pelagian controversy",
                    "De Trinitate IX-X (memoria-intellectus-voluntas)",
                    "Confessiones VIII (divided will)",
                    "biblical anthropology + Neoplatonic ontology",
                ],
                "key_anchor_quote_md_lines": "ll. 5425-5428",
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="synthesis_dihle1982_indian_excursus_intellectualism_parallel",
        type="synthesis",
        label="Dihle 1982 — Excursus indien : parallele indologique de l'intellectualisme",
        description=(
            "Synthese transversale du volume : Dihle, indianiste forme aupres "
            "de Paul Hacker, glisse plusieurs excursus sur les Brahmanes et "
            "les Mages (p. 13-15 / md ll. 312, 404, 6639). Il suggere un "
            "parallele structurel : la pensee indienne (vedanta, karma) "
            "developpe elle aussi une morale fondee sur la connaissance, "
            "ou l'action correcte decoule de la comprehension du dharma "
            "(loi cosmique) — sans concept autonome de volonte au sens "
            "augustinien. Ce parallele indologique sert d'argument indirect "
            "a la these centrale : l'absence d'un concept de volonte n'est "
            "pas un manque accidentel des Grecs, mais une caracteristique "
            "structurelle des cultures intellectualistes (Inde, Grece, "
            "Iran zoroastrien). Reciproquement, la specificite du "
            "monotheisme volontariste biblique (Yahveh comme volonte "
            "souveraine arbitraire) trouve sa contrepartie dans "
            "l'augustinisme. Pour Dihle, l'invention chretienne de la "
            "volonte est ainsi unique dans l'histoire de la pensee mondiale. "
            "Reception controverse : Cary 2007 a contre-argue que la "
            "specificite augustinienne tient surtout a l'introspection "
            "personnelle (Confessiones)"
        ),
        description_en=(
            "Cross-lecture synthesis : Dihle, an Indologist trained under "
            "Paul Hacker, inserts several excursus on the Brahmans and "
            "Magi (p. 13-15 / md ll. 312, 404, 6639). He suggests a "
            "structural parallel : Indian thought (Vedanta, karma) also "
            "develops a morality grounded in knowledge, where right "
            "action follows from understanding of dharma (cosmic law) — "
            "without an autonomous concept of will in the Augustinian "
            "sense. This Indological parallel serves as indirect argument "
            "for the central thesis : the absence of a concept of will is "
            "not an accidental Greek shortcoming, but a structural feature "
            "of intellectualist cultures (India, Greece, Zoroastrian Iran). "
            "Conversely, the specificity of biblical voluntarist monotheism "
            "(Yahweh as sovereign arbitrary will) finds its counterpart in "
            "Augustinianism. For Dihle, the Christian invention of will is "
            "thus unique in the history of world thought. Contested "
            "reception : Cary 2007 counter-argued that Augustinian "
            "specificity rather lies in personal introspection (Confessions)"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 13-15, p. 165 (n. 18)",
            md_line_range="ll. 312, 404, 6639",
            lecture="cross-cutting excursus (Lect. I, II, V)",
            dihle_section="Excursus indologique",
            extra={
                "synthesis_type": "thematic_synthesis",
                "themes": [
                    "Indian parallel",
                    "Brahmans",
                    "Magi",
                    "dharma vs will",
                    "Paul Hacker (Dihle's Indological mentor)",
                ],
            },
        ),
        confidence=0.8,
    ),
    _node(
        id="synthesis_dihle1982_methodological_thesis_summary",
        type="synthesis",
        label="Dihle 1982 — Synthese methodologique : invention chretienne du concept de volonte",
        description=(
            "Synthese methodologique globale du volume. Trois axes : (1) "
            "*Methode philologique* — Dihle reconstruit l'histoire d'un "
            "concept en suivant les occurrences terminologiques (boulesis, "
            "thelesis, hekousios, autexousios, prohairesis, synkatathesis ; "
            "voluntas, liberum arbitrium) et en montrant comment leur "
            "champ semantique ne recouvre pas la voluntas augustinienne. "
            "(2) *Methode comparative* — opposition systematique entre "
            "univers intellectualiste grec et univers volontariste biblique. "
            "(3) *Methode genealogique* — l'invention augustinienne n'est "
            "pas creatio ex nihilo : Augustin recoit le terme voluntas du "
            "latin classique, les distinctions psychologiques du stoicisme, "
            "l'ontologie de la privation du neoplatonisme, et "
            "l'anthropologie biblique de l'obeissance volontaire. Critique "
            "principale qu'on peut adresser a Dihle : la categorie de "
            "volonte qu'il presuppose (faculte autonome, distincte de "
            "l'intellect ET de l'emotion) est elle-meme post-cartesienne, "
            "et pourrait ne pas etre exactement celle d'Augustin. "
            "Frede 2011 lui repondra en distinguant 'free will' et 'will' : "
            "Epictete aurait introduit le premier (eleuthera prohairesis) ; "
            "Augustin n'invente que la systematisation latine"
        ),
        description_en=(
            "Methodological synthesis of the volume. Three axes : (1) "
            "*Philological method* — Dihle reconstructs the history of a "
            "concept by tracking terminological occurrences (boulesis, "
            "thelesis, hekousios, autexousios, prohairesis, synkatathesis ; "
            "voluntas, liberum arbitrium) and showing that their semantic "
            "field does not cover Augustinian voluntas. (2) *Comparative "
            "method* — systematic opposition between Greek intellectualist "
            "universe and biblical voluntarist universe. (3) *Genealogical "
            "method* — Augustinian invention is not creatio ex nihilo : "
            "Augustine inherits the term voluntas from classical Latin, "
            "psychological distinctions from Stoicism, ontology of "
            "privation from Neoplatonism, and biblical anthropology of "
            "voluntary obedience. Main critique that can be addressed to "
            "Dihle : the category of will he presupposes (autonomous "
            "faculty, distinct from intellect AND emotion) is itself "
            "post-Cartesian, and may not be precisely Augustinian. Frede "
            "2011 responds by distinguishing 'free will' from 'will' : "
            "Epictetus introduced the first (eleuthera prohairesis) ; "
            "Augustine merely systematised in Latin"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 1-150 (volume entier)",
            md_line_range="ll. 139-11043",
            lecture="cross-cutting (entire volume)",
            dihle_section="Synthese methodologique globale",
            extra={
                "synthesis_type": "methodological_synthesis",
                "themes": [
                    "philological method",
                    "comparative method",
                    "genealogical method",
                    "Frede's counter-thesis (Epictetus)",
                    "post-Cartesian presupposition critique",
                ],
            },
        ),
        confidence=0.88,
    ),
]


# =============================================================================
# ARGUMENTS (12) — scholarly arguments
# =============================================================================

NEW_ARGUMENTS: list[dict[str, Any]] = [
    _node(
        id="argument_dihle_1982_greek_intellectualism_thesis",
        type="argument",
        label="Dihle 1982 — These centrale : les Grecs n'ont pas developpe de concept de volonte",
        description=(
            "Argument central de Dihle 1982 (p. 20 / md ll. 3054-3057) : "
            "'the Greeks, in their attempts to analyze and to evaluate "
            "human action, never developed a distinct concept of will'. "
            "Sous-arguments : (1) la psychologie morale grecque explique "
            "l'action par la cognition rationnelle ; (2) l'intention est "
            "toujours un phenomene intellectuel et le striving est attribue "
            "a l'instinct ou a l'emotion ; (3) le choix delibere "
            "(prohairesis) presuppose la connaissance d'un objet "
            "determine ; (4) il n'existe pas de terme unique grec recouvrant "
            "exactement la voluntas augustinienne — pluralite eparpillee "
            "entre boulesis, thelesis, hekousios, prohairesis, synkatathesis. "
            "These radicale dans la lignee de Pohlenz, Snell, Voelke, mais "
            "presentee de maniere plus tranchee : c'est une absence "
            "structurelle, non un retard. La these est l'organisateur de "
            "tout le volume"
        ),
        description_en=(
            "Central argument of Dihle 1982 (p. 20) : 'the Greeks, in "
            "their attempts to analyze and to evaluate human action, never "
            "developed a distinct concept of will'. Sub-arguments : (1) "
            "Greek moral psychology explains action through rational "
            "cognition ; (2) intention is always an intellectual "
            "phenomenon and striving is attributed to instinct or emotion ; "
            "(3) deliberate choice (prohairesis) presupposes knowledge of "
            "a definite object ; (4) there is no single Greek term covering "
            "Augustinian voluntas — scattered plurality among boulesis, "
            "thelesis, hekousios, prohairesis, synkatathesis. Radical "
            "thesis in the lineage of Pohlenz, Snell, Voelke, but stated "
            "more sharply : a structural absence, not a lag. The thesis "
            "organises the entire volume"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 20-30",
            md_line_range="ll. 3054-3127",
            lecture="II (Greek View of Human Action I)",
            dihle_section="Lect. II, formulation initiale",
            extra={
                "argument_type": "scholarly_thesis_central",
                "argument_role": "central_organizing_thesis",
                "anchor_quote": "the Greeks ... never developed a distinct concept of will (p. 20)",
                "lineage": ["Pohlenz 1948", "Snell 1946", "Voelke 1973"],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_dihle_1982_hebrew_obedience_non_cognitive_will",
        type="argument",
        label="Dihle 1982 — La Bible hebraique introduit une volonte non-cognitive d'obeissance",
        description=(
            "Argument de Dihle 1982 (Lect. IV, p. 75-83 / md ll. 3050-"
            "3060). Yahveh dans la tradition hebraique commande sans "
            "donner de raison rationnelle accessible a la deliberation ; "
            "l'obeissance ('shema' = 'ecoute / obeis') precede la "
            "comprehension ('si vous n'avez pas confiance [ta'amenu], "
            "vous n'avez pas de fondement [tdaminu]', Is 7,9 / md ll. "
            "3065-3070). Termes-cles : ratzon (volonte / faveur divine), "
            "kavod (gloire / poids), 'emunah (fidelite), yir'ah (crainte), "
            "mibtah (confiance). Ces termes installent une categorie de "
            "soumission volontaire qui n'a pas d'equivalent grec : 'human "
            "knowledge or wisdom thus depends on the previous activity of "
            "the will, which has to turn towards God and to give an "
            "initial response to a very definite divine order' (p. 76 / "
            "md ll. 3061-3063). Le bon ordre cognitif est *renverse* par "
            "rapport au modele grec : l'obeissance precede la "
            "comprehension, et non l'inverse"
        ),
        description_en=(
            "Argument of Dihle 1982 (Lect. IV, p. 75-83). Yahweh in the "
            "Hebrew tradition commands without giving a rational reason "
            "accessible to deliberation ; obedience ('shema' = 'hear / "
            "obey') precedes understanding ('if you have no confidence "
            "[ta'amenu], you have no firm stand [tdaminu]', Is 7,9). "
            "Key terms : ratzon (will / divine favour), kavod (glory / "
            "weight), 'emunah (faithfulness), yir'ah (fear), mibtah "
            "(trust). These terms install a category of voluntary "
            "submission without Greek equivalent : 'human knowledge or "
            "wisdom thus depends on the previous activity of the will, "
            "which has to turn towards God and to give an initial response "
            "to a very definite divine order' (p. 76). The good cognitive "
            "order is *reversed* relative to the Greek model : obedience "
            "precedes understanding, and not the other way around"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 75-83",
            md_line_range="ll. 3050-3070",
            lecture="IV (St. Paul and Philo)",
            dihle_section="Lect. IV §I-II, fondement biblique",
            extra={
                "argument_type": "scholarly_sub_thesis",
                "hebrew_terms_attested_in_md": [
                    "ratzon",
                    "kavod",
                    "'emunah (fidelity)",
                    "yir'ah (fear of God)",
                    "mibtah (trust)",
                ],
                "is_7_9_polyptoton_hebrew": "ta'amenu / tdaminu",
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="argument_dihle_1982_paul_romans_7_split_will",
        type="argument",
        label="Dihle 1982 — Romains 7 manifeste la scission volonte/non-volonte chez Paul",
        description=(
            "Argument de Dihle 1982 (Lect. IV §II-III, p. 84-87 / md "
            "ll. 3480-3609, 3719-3734). Le passage cle est Rom 7,15-24 : "
            "'je ne fais pas ce que je veux, mais je fais ce que je hais' "
            "(thelo / poio / miso). Dihle conteste que ce conflit puisse "
            "s'expliquer par l'akrasia aristotelicienne (defaillance "
            "cognitive) : 'the conflict which is spoken of in Rom. 7:7ff "
            "cannot be' reduit a l'incontinence grecque (md l. 3555). Il "
            "s'agit d'une experience nouvelle : la volonte humaine, "
            "scindee par le peche (hamartia), veut le bien (consent a la "
            "Loi) mais ne peut l'accomplir. Cette scission revele "
            "implicitement une faculte distincte du jugement intellectuel "
            "ET de l'emotion spontanee. Pourtant Paul, n'ayant pas de "
            "terme dedie, utilise 'thelo' (vouloir) et 'ginosko' "
            "(connaitre) de facon presque indifferenciee. Dihle conclut "
            "(p. 84 / md ll. 3721-3726) : 'it is, in his view, a will, "
            "as distinguished from all intellectual achievements [...] as "
            "well as from all unconscious and spontaneous emotions, which "
            "responds to the commandment of God'. Innovation conceptuelle "
            "implicite sans innovation terminologique"
        ),
        description_en=(
            "Argument of Dihle 1982 (Lect. IV §II-III, p. 84-87). Key "
            "passage Rom 7,15-24 : 'I do not do what I want, but I do the "
            "very thing I hate' (thelo / poio / miso). Dihle contests "
            "that this conflict can be explained by Aristotelian akrasia "
            "(cognitive failure) : 'the conflict which is spoken of in "
            "Rom. 7:7ff cannot be' reduced to Greek incontinence. This is "
            "a new experience : the human will, split by sin (hamartia), "
            "wants the good (consents to the Law) but cannot accomplish "
            "it. This split implicitly reveals a faculty distinct from "
            "intellectual judgement AND from spontaneous emotion. Yet "
            "Paul, lacking a dedicated term, uses 'thelo' (to want) and "
            "'ginosko' (to know) almost indiscriminately. Dihle concludes "
            "(p. 84) : 'it is, in his view, a will, as distinguished from "
            "all intellectual achievements [...] as well as from all "
            "unconscious and spontaneous emotions, which responds to the "
            "commandment of God'. Implicit conceptual innovation without "
            "terminological innovation"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 84-87",
            md_line_range="ll. 3480-3609, 3719-3734",
            lecture="IV (St. Paul and Philo)",
            dihle_section="Lect. IV §II-III, exegese de Rom 7",
            extra={
                "argument_type": "scholarly_sub_thesis",
                "key_biblical_loci": [
                    "Rom 7,7ff",
                    "Rom 7,15",
                    "Rom 7,24",
                    "Rom 8,1-2",
                    "Gal 5,17",
                ],
                "key_greek_terms_attested": [
                    "thelo (Rom 7,15)",
                    "ginosko (Rom 7,15)",
                    "thelema (1 Cor / Rom 1,28 noos)",
                    "syneidesis (Rom 2,14-15)",
                ],
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="argument_dihle_1982_paul_no_dedicated_term_for_will",
        type="argument",
        label="Dihle 1982 — Paul n'a aucun terme dedie pour la volonte (humaine ou divine)",
        description=(
            "Argument philologique de Dihle 1982 (Lect. IV §III, p. 84 / "
            "md ll. 3727-3734) : 'There is no such term in the language "
            "of St. Paul and his contemporaries'. Pour la volonte humaine, "
            "Paul utilise indifferemment thelo (Rom 7,15), thelema, "
            "boule, eudokia. Pour la volonte divine egalement : 'thelesis, "
            "thelema, boule, boulesis, eudokia, gnome are used almost as "
            "synonyms' (md ll. 3727-3734). Cette absence terminologique "
            "est cruciale pour la these : Paul *experimente* la volonte "
            "comme faculte distincte (cf. argument Rom 7) mais ne la "
            "*thematise* pas conceptuellement. Le travail terminologique "
            "se fera plus tard : autexousion chez Justin, "
            "thelesis/thelematikon chez les Cappadociens, voluntas chez "
            "Augustin. L'argument permet a Dihle de defendre "
            "simultanement : (a) Paul est decisif pour l'emergence "
            "conceptuelle ; (b) Paul n'est pas encore le 'createur' du "
            "concept au sens propre — ce sera Augustin"
        ),
        description_en=(
            "Philological argument of Dihle 1982 (Lect. IV §III, p. 84) : "
            "'There is no such term in the language of St. Paul and his "
            "contemporaries'. For human will, Paul uses indiscriminately "
            "thelo (Rom 7,15), thelema, boule, eudokia. For divine will "
            "as well : 'thelesis, thelema, boule, boulesis, eudokia, "
            "gnome are used almost as synonyms'. This terminological "
            "absence is crucial for the thesis : Paul *experiences* will "
            "as a distinct faculty (cf. Rom 7 argument) but does not "
            "*thematise* it conceptually. Terminological work comes later : "
            "autexousion in Justin, thelesis/thelematikon in the "
            "Cappadocians, voluntas in Augustine. The argument allows "
            "Dihle to defend simultaneously : (a) Paul is decisive for "
            "conceptual emergence ; (b) Paul is not yet the 'creator' of "
            "the concept proper — that will be Augustine"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 84",
            md_line_range="ll. 3727-3734",
            lecture="IV (St. Paul and Philo)",
            dihle_section="Lect. IV §III, argument terminologique",
            extra={
                "argument_type": "scholarly_philological",
                "key_greek_terms_scattered": [
                    "thelo / thelema (most frequent)",
                    "boule / boulesis",
                    "eudokia",
                    "gnome",
                    "thelesis (rare in Paul)",
                ],
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="argument_dihle_1982_pauline_conscience_distinctive",
        type="argument",
        label="Dihle 1982 — La syneidesis paulinienne n'est pas grecque",
        description=(
            "Argument de Dihle 1982 (Lect. IV §II, p. 77-78 / md ll. "
            "3577-3609, 3278-3337). La conscience (syneidesis) chez Paul "
            "(Rom 2,14-15 ; Rom 13,5 ; 1 Cor 8,7-13 ; 10,25-29) ne "
            "fonctionne pas comme la conscience socratique-stoicienne "
            "(co-savoir reflexif issu de l'examen rationnel) : elle "
            "temoigne subjectivement et spontanement de la loi de Dieu "
            "inscrite au coeur — 'the work of the Law inscribed in their "
            "heart, their conscience also bearing witness' (Rom 2,15 / md "
            "ll. 3277-3278). Cette conscience est universelle (jusque "
            "chez les paiens) mais aussi faillible ('weak conscience', 1 "
            "Cor 8,7 / md ll. 3322-3325). Dihle insiste : nul n'a le "
            "droit de surclasser la conscience d'autrui par sa propre "
            "connaissance superieure (md ll. 3328-3331). Cette doctrine "
            "rompt avec le modele grec : la conscience n'est plus le "
            "produit final de la deliberation rationnelle, mais une "
            "instance autonome qui en precede et en juge l'usage moral. "
            "Anticipe l'instance volitionnelle qu'Augustin thematisera"
        ),
        description_en=(
            "Argument of Dihle 1982 (Lect. IV §II, p. 77-78). Conscience "
            "(syneidesis) in Paul (Rom 2,14-15 ; Rom 13,5 ; 1 Cor 8,7-13 ; "
            "10,25-29) does not function like Socratic-Stoic conscience "
            "(reflexive co-knowledge produced by rational examination) : "
            "it witnesses subjectively and spontaneously to the law of "
            "God inscribed in the heart — 'the work of the Law inscribed "
            "in their heart, their conscience also bearing witness' (Rom "
            "2,15). This conscience is universal (even among gentiles) but "
            "fallible ('weak conscience', 1 Cor 8,7). Dihle insists : no "
            "one has the right to override another's conscience by "
            "superior knowledge. This doctrine breaks with the Greek "
            "model : conscience is no longer the final product of "
            "rational deliberation, but an autonomous instance that "
            "precedes and judges its moral use. Anticipates the "
            "volitional instance Augustine will thematise"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 77-78",
            md_line_range="ll. 3577-3609, 3278-3337",
            lecture="IV (St. Paul and Philo)",
            dihle_section="Lect. IV §II, conscience paulinienne",
            extra={
                "argument_type": "scholarly_sub_thesis",
                "key_pauline_loci": [
                    "Rom 2,14-15",
                    "Rom 13,5 (dia ten syneidesin)",
                    "1 Cor 8,7-13 (weak conscience)",
                    "1 Cor 10,25-29",
                ],
                "key_greek_term": "syneidesis (συνείδησις)",
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_dihle_1982_augustine_invents_philosophical_voluntas",
        type="argument",
        label="Dihle 1982 — Augustin invente le concept philosophique de voluntas",
        description=(
            "Argument central de la Lect. VI (p. 123-144 / md ll. 9890-"
            "11043). Augustin, sous le double aiguillon de la polemique "
            "anti-manicheenne et de la querelle pelagienne, transforme "
            "le terme latin classique voluntas (jusqu'alors flou : tantot "
            "horme stoicienne, tantot velle ordinaire, cf. p. 138 / md "
            "ll. 5420-5435) en faculte mentale autonome, irreductible a "
            "l'intellect comme a l'emotion. Trois mouvements : (1) contre "
            "les Manicheens, montrer que la cause du mal est dans la "
            "volonte deficiente, sans nature mauvaise substantielle (p. "
            "128 / md ll. 5185-5202) ; (2) contre les Pelagiens, montrer "
            "que la volonte humaine est blessee par le peche originel et "
            "ne peut se relever sans la grace prevenante (p. 137-140 / md "
            "ll. 5271-5360) ; (3) dans le De Trinitate IX-X, integrer "
            "voluntas a la triade ontologique memoria-intellectus-voluntas, "
            "lui donnant statut de faculte fondamentale au meme rang que "
            "la memoire et l'intelligence. Resultat synthetique p. 144 / "
            "md ll. 5425-5428 : 'the notion of will, as it is used as a "
            "tool of analysis and description in many philosophical "
            "doctrines from the early Scholastics to Schopenhauer and "
            "Nietzsche, was invented by St. Augustine'"
        ),
        description_en=(
            "Central argument of Lect. VI (p. 123-144). Augustine, under "
            "the double prod of anti-Manichean polemic and Pelagian "
            "controversy, transforms the classical Latin term voluntas "
            "(until then loose : sometimes Stoic horme, sometimes ordinary "
            "velle, p. 138) into an autonomous mental faculty irreducible "
            "to intellect or emotion. Three moves : (1) against the "
            "Manicheans, show that the cause of evil is in the deficient "
            "will, without substantial evil nature (p. 128) ; (2) against "
            "the Pelagians, show that the human will is wounded by original "
            "sin and cannot recover without prevenient grace (p. 137-140) ; "
            "(3) in De Trinitate IX-X, integrate voluntas into the "
            "ontological triad memoria-intellectus-voluntas, giving it "
            "the status of a fundamental faculty alongside memory and "
            "intelligence. Synthetic result p. 144 : 'the notion of will, "
            "as it is used as a tool of analysis and description in many "
            "philosophical doctrines from the early Scholastics to "
            "Schopenhauer and Nietzsche, was invented by St. Augustine'"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 123-144",
            md_line_range="ll. 9890-11043",
            lecture="VI (St. Augustine and His Concept of Will)",
            dihle_section="Lect. VI, conclusion : Augustin inventeur",
            extra={
                "argument_type": "scholarly_thesis_central",
                "anchor_quote": "the notion of will ... was invented by St. Augustine (p. 144)",
                "augustinian_loci": [
                    "Confessiones VIII (divided will)",
                    "De Trinitate IX-X (memoria-intellectus-voluntas)",
                    "De libero arbitrio (anti-Manichean)",
                    "De gratia et libero arbitrio (anti-Pelagian)",
                    "De spiritu et littera",
                ],
                "polemical_contexts": [
                    "anti-Manichean (will not substance)",
                    "anti-Pelagian (will wounded, needs grace)",
                ],
            },
        ),
        confidence=0.95,
    ),
    _node(
        id="argument_dihle_1982_plotinus_remains_intellectualist",
        type="argument",
        label="Dihle 1982 — Plotin n'echappe pas a l'intellectualisme grec",
        description=(
            "Argument de Dihle 1982 (Lect. V, p. 101-122 / md ll. 4607-"
            "4671, 2170-2790). Plotin (Enneades III.1 ; IV.8 ; VI.8 *Sur "
            "le libre arbitre et la volonte de l'Un*) introduit une "
            "terminologie qu'on pourrait juger voluntariste (autexousios, "
            "boulesis, ephesis tou agathou) et discute frontalement la "
            "liberte de l'Un et de l'ame. Mais Dihle demontre qu'in fine, "
            "la liberte plotinienne se ramene a la coincidence de l'agent "
            "avec sa nature intellective — le nous. La 'tolma' designe la "
            "chute de l'ame dans la multiplicite (md ll. 4645-4671) ; "
            "l'ascension est une matter de retour cognitif a l'Un. Meme "
            "la 'volonte de l'Un' (boulesis du Premier, Enn. VI.8) reste "
            "intellectualiste : 'la volonte = activite du nous'. Plotin "
            "ne franchit donc pas le pas qu'Augustin franchira : "
            "thematiser une faculte volontaire distincte de l'intellect. "
            "Implication : meme en philosophie tardive paienne, "
            "l'intellectualisme grec reste structurel, confirmant la these "
            "que la rupture sera latine et chretienne"
        ),
        description_en=(
            "Argument of Dihle 1982 (Lect. V, p. 101-122). Plotinus "
            "(Enneads III.1 ; IV.8 ; VI.8 *On Free Will and the Will of "
            "the One*) introduces seemingly voluntarist terminology "
            "(autexousios, boulesis, ephesis tou agathou) and frontally "
            "discusses freedom of the One and of the soul. But Dihle "
            "demonstrates that in the end, Plotinian freedom reduces to "
            "the agent's coincidence with intellective nature — nous. "
            "'Tolma' designates the soul's fall into multiplicity ; "
            "ascent is a matter of cognitive return to the One. Even the "
            "'will of the One' (boulesis of the First, Enn. VI.8) remains "
            "intellectualist : 'will = activity of nous'. Plotinus thus "
            "does not take the step Augustine will take : thematising a "
            "voluntary faculty distinct from intellect. Implication : "
            "even in late pagan philosophy, Greek intellectualism remains "
            "structural, confirming that the rupture will be Latin and "
            "Christian"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 101-122",
            md_line_range="ll. 4607-4671, 2170-2790",
            lecture="V (Philosophy and Religion in Late Antiquity)",
            dihle_section="Lect. V, Plotin et neoplatoniciens",
            extra={
                "argument_type": "scholarly_sub_thesis",
                "plotinus_loci": [
                    "Enn. III.1 (Peri Heimarmenes)",
                    "Enn. IV.8 (Descent of the soul)",
                    "Enn. VI.8 (On Free Will and the Will of the One)",
                ],
                "key_terms_examined": [
                    "autexousios",
                    "boulesis tou Henos",
                    "tolma (soul's fall)",
                    "ephesis tou agathou",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_dihle_1982_synkatathesis_is_cognitive_not_volitional",
        type="argument",
        label="Dihle 1982 — La synkatathesis stoicienne reste cognitive, non volitionnelle",
        description=(
            "Argument important de Dihle 1982 (Lect. III, p. 60-64 / md "
            "ll. 2549-2580). L'objection la plus forte contre la these de "
            "Dihle vient de la psychologie stoicienne : la synkatathesis "
            "(assentiment a une impression) semble fournir un acte "
            "volontaire distinct de la cognition pure. Dihle repond "
            "longuement : (1) 'the assent ... is voluntary, yet "
            "necessitated' (md ll. 2563-2564) — son caractere voluntary "
            "ne lui enleve pas son caractere intellectuel ; (2) les quatre "
            "phases (perception, imagination, assentiment, impulsion) "
            "sont 'entirely rational' (md ll. 2569-2570) ; (3) la 'weak "
            "assent' (asthenes synkatathesis, SVF 3.172, 3.548, md l. "
            "2572) confirme que la defaillance volitionnelle est analysee "
            "en termes cognitifs (faiblesse du jugement) ; (4) la phrase "
            "celebre 'fata volentem ducunt, nolentem trahunt' (Cleanthe "
            "ap. Sen. ep. 41.1 / md l. 219) ne demontre pas un "
            "voluntarisme metaphysique : volentem y signifie *aligne avec* "
            "le destin, et le 'consentement' (Sen. ep. : 'Non pareo deo "
            "sed assentior', md l. 840) reste l'acte par lequel la raison "
            "embrasse l'ordre du logos. Pour Dihle, la synkatathesis "
            "n'invalide donc pas la these de l'intellectualisme grec"
        ),
        description_en=(
            "Important argument of Dihle 1982 (Lect. III, p. 60-64). The "
            "strongest objection against Dihle's thesis comes from Stoic "
            "psychology : synkatathesis (assent to an impression) seems "
            "to provide a voluntary act distinct from pure cognition. "
            "Dihle replies at length : (1) 'the assent ... is voluntary, "
            "yet necessitated' — its voluntary character does not remove "
            "its intellectual character ; (2) the four phases (perception, "
            "imagination, assent, impulse) are 'entirely rational' ; (3) "
            "'weak assent' (asthenes synkatathesis, SVF 3.172, 3.548) "
            "confirms that volitional failure is analysed in cognitive "
            "terms (weakness of judgement) ; (4) the famous phrase 'fata "
            "volentem ducunt, nolentem trahunt' (Cleanthes apud Sen. ep. "
            "41.1) does not demonstrate metaphysical voluntarism : "
            "volentem means *aligned with* fate, and 'consent' (Sen. ep. : "
            "'Non pareo deo sed assentior') remains the act by which "
            "reason embraces the logos's order. Synkatathesis therefore "
            "does not invalidate the thesis of Greek intellectualism"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 60-64",
            md_line_range="ll. 2549-2580",
            lecture="III (Greek View of Human Action II)",
            dihle_section="Lect. III §III, examen de la synkatathesis stoicienne",
            extra={
                "argument_type": "scholarly_defense_against_objection",
                "stoic_loci": [
                    "SVF 3.172 (asthenes synkatathesis)",
                    "SVF 3.548 (asthenes synkatathesis)",
                    "Sen. ep. 41.1 (Non pareo deo sed assentior)",
                    "Sen. quaest. nat.",
                ],
                "key_term": "synkatathesis (συγκατάθεσις)",
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="argument_dihle_1982_critique_anachronism_in_attribution_will_to_greeks",
        type="argument",
        label="Dihle 1982 — Critique de l'attribution anachronique de 'volonte' a la pensee grecque",
        description=(
            "Argument metahistorique de Dihle 1982 (Lect. II-III, "
            "discussion methodologique p. 27-30, 49-55 / md ll. 3110-"
            "3130, 7799-7950). La litterature philosophique du XXe siecle "
            "(notamment anglo-saxonne : Kenny, Hardie, Joseph) a "
            "tendance a *attribuer* aux Grecs un concept de 'will' qu'ils "
            "n'ont pas. Dihle critique : (1) traduire prohairesis par "
            "'will' est anachronique — c'est plutot 'deliberate choice "
            "based on prior knowledge' ; (2) traduire boulesis par "
            "'volition' efface la composante cognitive ; (3) traduire "
            "hekousios par 'voluntary' au sens augustinien est une "
            "projection retrospective. Dihle plaide pour une histoire "
            "philologique stricte : laisser les termes grecs dans leur "
            "champ semantique propre, et ne pas projeter sur eux une "
            "categorie post-augustinienne. Cette critique vise notamment "
            "Anthony Kenny (*Aristotle's Theory of the Will*, 1979) qui "
            "soutenait l'existence d'une theorie aristotelicienne de la "
            "volonte. Frede 2011 retournera l'argument contre Dihle "
            "lui-meme : la categorie de 'will' que Dihle presuppose "
            "(faculte autonome) serait encore plus moderne (post-"
            "cartesienne) que celle d'Augustin"
        ),
        description_en=(
            "Meta-historical argument of Dihle 1982 (Lect. II-III, "
            "methodological discussion p. 27-30, 49-55). 20th-century "
            "philosophical literature (especially anglophone : Kenny, "
            "Hardie, Joseph) tends to *attribute* to the Greeks a concept "
            "of 'will' they did not have. Dihle critiques : (1) translating "
            "prohairesis as 'will' is anachronistic — it is rather "
            "'deliberate choice based on prior knowledge' ; (2) translating "
            "boulesis as 'volition' erases the cognitive component ; (3) "
            "translating hekousios as 'voluntary' in the Augustinian sense "
            "is retrospective projection. Dihle pleads for strict "
            "philological history : leave Greek terms in their own "
            "semantic field, do not project a post-Augustinian category "
            "onto them. The critique particularly targets Anthony Kenny "
            "(*Aristotle's Theory of the Will*, 1979). Frede 2011 will "
            "return the argument against Dihle himself : the category of "
            "'will' Dihle presupposes (autonomous faculty) is even more "
            "modern (post-Cartesian) than Augustine's"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 27-30, 49-55",
            md_line_range="ll. 3110-3130, 7799-7950",
            lecture="II-III (Greek View of Human Action)",
            dihle_section="Lect. II-III, discussion methodologique",
            extra={
                "argument_type": "scholarly_methodological",
                "critiqued_translations": [
                    "prohairesis -> 'will'",
                    "boulesis -> 'volition'",
                    "hekousios -> 'voluntary' (Augustinian sense)",
                ],
                "polemical_targets": [
                    "Anthony Kenny, Aristotle's Theory of the Will (1979)",
                ],
                "is_self_undermining_per_frede_2011": True,
            },
        ),
        confidence=0.88,
    ),
    _node(
        id="argument_dihle_1982_voluntas_latin_pre_augustine_loose_semantics",
        type="argument",
        label="Dihle 1982 — Le terme voluntas chez Ciceron / Seneque a une semantique floue",
        description=(
            "Argument philologique de Dihle 1982 (Lect. VI, p. 137-140 / "
            "md ll. 5420-5435). Avant Augustin, le terme latin voluntas "
            "*existe* mais n'a pas de valeur philosophique technique. "
            "Chez Ciceron, voluntas est utilise comme equivalent libre "
            "de prohairesis ou boulesis grecs ; parfois designe le "
            "desir ou souhait spontane plutot que l'intention deliberee "
            "(md ll. 5426-5428) ; parfois designe l'impulsion (horme) "
            "elle-meme issue de la deliberation ou de l'attitude morale "
            "(md ll. 5428-5430). 'The large semantic area which is "
            "apparently attached to the word in Cicero's philosophical "
            "vocabulary corresponds to the general usage of his time' "
            "(md ll. 5430-5431). Seneque commence a percevoir les "
            "implications voluntaristes (md ll. 5433-5435) sans aller au "
            "bout du chemin. C'est Augustin qui transforme ce mot souple "
            "en concept technique strict : faculte autonome, irreductible "
            "a l'intellect ou a l'emotion. L'argument permet a Dihle de "
            "montrer que la nouveaute augustinienne n'est pas dans le "
            "*mot* (qui prexiste) mais dans le *concept* (qui est invente)"
        ),
        description_en=(
            "Philological argument of Dihle 1982 (Lect. VI, p. 137-140). "
            "Before Augustine, the Latin term voluntas *exists* but has "
            "no technical philosophical value. In Cicero, voluntas is "
            "used as a free equivalent of Greek prohairesis or boulesis ; "
            "sometimes designates desire or spontaneous wish rather than "
            "deliberate intention ; sometimes designates the impulse "
            "(horme) issuing from deliberation or moral attitude. 'The "
            "large semantic area which is apparently attached to the word "
            "in Cicero's philosophical vocabulary corresponds to the "
            "general usage of his time'. Seneca begins to perceive the "
            "voluntarist implications without going all the way. Augustine "
            "transforms this loose word into a strict technical concept : "
            "autonomous faculty, irreducible to intellect or emotion. The "
            "argument allows Dihle to show that the Augustinian novelty "
            "is not in the *word* (which pre-exists) but in the *concept* "
            "(which is invented)"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 137-140",
            md_line_range="ll. 5420-5435",
            lecture="VI (St. Augustine and His Concept of Will)",
            dihle_section="Lect. VI §I, prehistoire latine de voluntas",
            extra={
                "argument_type": "scholarly_philological",
                "latin_term_examined": "voluntas",
                "key_loci": [
                    "Cicero (multiple philosophical works)",
                    "Seneca, ep. 41.1",
                    "Seneca, late writings on voluntas / velle",
                ],
            },
        ),
        confidence=0.9,
    ),
    _node(
        id="argument_dihle_1982_augustine_responds_to_manichean_and_pelagian",
        type="argument",
        label="Dihle 1982 — La voluntas augustinienne nait du double aiguillon manicheen et pelagien",
        description=(
            "Argument genealogique de Dihle 1982 (Lect. VI §II, p. 128-"
            "140 / md ll. 5185-5360). La construction du concept de "
            "voluntas chez Augustin ne procede pas d'une speculation "
            "metaphysique abstraite mais de deux conflits doctrinaux "
            "concrets : (1) *anti-manicheisme* (374-396, *De libero "
            "arbitrio* I-III, *De moribus Manichaeorum*, *Contra "
            "Faustum*) — il faut maintenir que le mal n'est pas une "
            "nature substantielle (les tenebres manicheennes) mais le "
            "fruit d'une volonte humaine deficiente : 'evil ... was "
            "present ... by no means the cause of evil ... as the "
            "Manicheans believed' (md ll. 5185-5187, 5202). Cela exige "
            "un sujet volitif libre, capable de defection. (2) *anti-"
            "pelagianisme* (411-430, *De spiritu et littera*, *De "
            "gratia et libero arbitrio*, *De correptione et gratia*, "
            "*De praedestinatione sanctorum*) — contre Pelage qui exalte "
            "la liberte naturelle de la volonte (md ll. 5271-5360), "
            "Augustin doit montrer que la volonte est blessee par le "
            "peche originel et a besoin de la grace prevenante. Ce double "
            "front explique la complexite finale du concept augustinien : "
            "volonte libre (contre manicheisme) ET volonte blessee, "
            "incapable du bien sans grace (contre pelagianisme). C'est "
            "cette synthese paradoxale qui constitue la veritable "
            "invention selon Dihle"
        ),
        description_en=(
            "Genealogical argument of Dihle 1982 (Lect. VI §II, p. 128-"
            "140). The construction of the concept of voluntas in "
            "Augustine proceeds not from abstract metaphysical speculation "
            "but from two concrete doctrinal conflicts : (1) *anti-"
            "Manicheism* (374-396, *De libero arbitrio* I-III, *De moribus "
            "Manichaeorum*, *Contra Faustum*) — must maintain that evil "
            "is not a substantial nature (Manichean darkness) but the "
            "fruit of a deficient human will. This requires a free "
            "volitional subject capable of defection. (2) *anti-"
            "Pelagianism* (411-430, *De spiritu et littera*, *De gratia "
            "et libero arbitrio*, *De correptione et gratia*, *De "
            "praedestinatione sanctorum*) — against Pelagius who exalts "
            "the natural freedom of the will, Augustine must show that "
            "the will is wounded by original sin and needs prevenient "
            "grace. This double front explains the final complexity of "
            "the Augustinian concept : free will (against Manicheism) AND "
            "wounded will, incapable of the good without grace (against "
            "Pelagianism). This paradoxical synthesis constitutes the real "
            "invention according to Dihle"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 128-140",
            md_line_range="ll. 5185-5360",
            lecture="VI (St. Augustine and His Concept of Will)",
            dihle_section="Lect. VI §II, genealogie polemique",
            extra={
                "argument_type": "scholarly_genealogical",
                "augustinian_polemical_works_per_dihle": [
                    "De libero arbitrio (anti-Manichean)",
                    "De moribus Manichaeorum",
                    "Contra Faustum",
                    "De spiritu et littera (anti-Pelagian)",
                    "De gratia et libero arbitrio",
                    "De correptione et gratia",
                    "De praedestinatione sanctorum",
                ],
                "synthetic_paradox": "free will + wounded will needing grace",
            },
        ),
        confidence=0.92,
    ),
    _node(
        id="argument_dihle_1982_indian_parallel_dharma_intellectualism",
        type="argument",
        label="Dihle 1982 — Parallele indologique : la pensee indienne du dharma est aussi intellectualiste",
        description=(
            "Argument comparatif de Dihle 1982 (Lect. I et passim, p. "
            "13-15 / md ll. 312, 404, 6639). En tant qu'indianiste, Dihle "
            "signale que la pensee indienne classique (vedanta, "
            "buddhisme, jainisme) developpe une psychologie de l'action "
            "fondee sur la connaissance (jnana, vidya) et la loi cosmique "
            "(dharma) : 'the Greeks had not been previously formulated "
            "by the Indian Brahmans or the [Magi]' (md ll. 6639). "
            "L'absence d'un concept autonome de volonte n'est donc pas "
            "une particularite des Grecs mais une caracteristique "
            "structurelle des cultures intellectualistes (Inde, Grece, "
            "Iran zoroastrien). L'argument comparatif a deux fonctions : "
            "(1) renforcer la these centrale en montrant que "
            "l'intellectualisme grec n'est pas un accident historique "
            "mais une logique culturelle profonde ; (2) accentuer "
            "l'exceptionnalite biblique-augustinienne — la volonte "
            "autonome serait une innovation unique au sein de la "
            "Mediterranee chretienne. Reception : peu reprise par les "
            "specialistes ulterieurs (Frede 2011, Bobzien, Sorabji n'y "
            "consacrent que des notes), mais conservee comme trait "
            "distinctif du polymathisme de Dihle"
        ),
        description_en=(
            "Comparative argument of Dihle 1982 (Lect. I and passim, p. "
            "13-15). As an Indologist, Dihle signals that classical "
            "Indian thought (Vedanta, Buddhism, Jainism) develops a "
            "psychology of action grounded in knowledge (jnana, vidya) "
            "and cosmic law (dharma) : 'the Greeks had not been previously "
            "formulated by the Indian Brahmans or the [Magi]'. The "
            "absence of an autonomous concept of will is thus not a Greek "
            "peculiarity but a structural feature of intellectualist "
            "cultures (India, Greece, Zoroastrian Iran). The comparative "
            "argument has two functions : (1) reinforce the central "
            "thesis by showing that Greek intellectualism is not a "
            "historical accident but a deep cultural logic ; (2) accentuate "
            "biblical-Augustinian exceptionalism — autonomous will would "
            "be a unique innovation within Christian Mediterranean. "
            "Reception : rarely taken up by later specialists (Frede 2011, "
            "Bobzien, Sorabji devote only footnotes), but preserved as a "
            "distinctive trait of Dihle's polymathism"
        ),
        period="Contemporary",
        metadata=dihle_metadata(
            page_range="p. 13-15, p. 165 (n.18)",
            md_line_range="ll. 312, 404, 6639",
            lecture="I and passim (Cosmological Conceptions / cross-cutting)",
            dihle_section="Excursus indologique",
            extra={
                "argument_type": "scholarly_comparative_indological",
                "comparanda": [
                    "Indian Brahmans (Vedanta, dharma)",
                    "Persian Magi (Zoroastrian intellectualism)",
                ],
                "dihle_indological_lineage": "trained under Paul Hacker",
            },
        ),
        confidence=0.82,
    ),
]
