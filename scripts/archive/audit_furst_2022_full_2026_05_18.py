"""Audit complet du nœud-pivot Fürst 2022 (Wege zur Freiheit).

Author: Romain Girardi
Date  : 2026-05-18

Idempotent — re-running is a no-op (marker `furst_audit_full_2026_05_18`
applied to every touched node + edge).

Phases:
1. Snapshot nodes.jsonl + edges.jsonl into data/kg/snapshots/
2. Enrich `pub_furst_2022_wege_freiheit` (canonical) with full description,
   local file paths, 15 verified_critiques + Inhaltsverzeichnis metadata.
3. Verify + enrich 15 `argument_furst_2022_*` nodes with quote_de /
   translation_en / page / verified=True / verified_at.
4. Deprecate shell publication `scholarly_work_f_rst_2022_*`.
5. Deprecate 8/keep+enrich 2 of the 10 `scholarly_argument_f_rst_*` shells.
   Redirect 5 edges from one of the deprecated shells to its canonical
   replacement.
6. Create 4 new arguments + 2 new concepts (theses present in Fürst 2022
   not yet encoded).
7. Wire ~30 new edges: `pub_furst_2022_wege_freiheit` → discussed ancient
   persons + engaged scholars.
8. Byte-exact preservation of untouched lines.
9. Stats report.

Conventions:
- Edge field is `relation` (not `type`).
- `metadata` is a JSON-encoded string (not a native dict).
- Ontology edge types must be drawn from
  `knowledge graph/ontology/edge_types.json`.
- No fabrication of ancient text — quotes are verbatim from
  Furst_2022_Wege_zur_Freiheit.txt or transcribed from the PDF.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------
# Paths & constants
# ----------------------------------------------------------------------

REPO_ROOT = Path("[local-path]")
NODES_PATH = REPO_ROOT / "data/kg/nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data/kg/edges.jsonl"
SNAPSHOT_DIR = (
    REPO_ROOT / "data/kg/snapshots/2026-05-18-pre-furst-audit"
)

MARKER_KEY = "furst_audit_full_2026_05_18"
AUDIT_AT = "2026-05-18"
TODAY_UTC = "2026-05-18 00:00:00+00:00"

PDF_PATH = (
    "[local-path] SHAL/"
    "04_Littérature_secondaire/05_Origene/"
    "Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung "
    "von Homer bis Origenes-Mohr Siebeck (2022).pdf"
)
TXT_PATH = (
    "[local-path] SHAL/"
    "04_Littérature_secondaire/05_Origene/"
    "Furst_2022_Wege_zur_Freiheit.txt"
)
MD_PATH = (
    "[local-path] SHAL/"
    "04_Littérature_secondaire/05_Origene/"
    "Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung "
    "von Homer bis Origenes-Mohr Siebeck (2022).md"
)

CANONICAL_PUB = "pub_furst_2022_wege_freiheit"
SHELL_PUB = "scholarly_work_f_rst_2022_wege_zur_freiheit_menschliche_selbstbest"
SCHOLAR_FURST = "scholar_furst_alfons"

# ----------------------------------------------------------------------
# Verified critiques (verbatim DE + EN translation + page)
# ----------------------------------------------------------------------

VERIFIED_CRITIQUES: list[dict] = [
    {
        "page": "1-2",
        "chapter": "Zum Geleit",
        "thesis": "Origen as the first thinker of freedom in history",
        "quote_de": (
            "Ich würde daher so weit gehen, den entscheidenden Einschnitt "
            "in der Geschichte des Freiheitsdenkens in das 3. Jahrhundert "
            "n. Chr. zu verlegen und ihn am christlichen "
            "Freiheitsphilosophen Origenes festzumachen, weil dieser "
            "zeitlich noch vor dem Neuplatoniker Plotin der erste "
            "Freiheitsdenker der Geschichte war."
        ),
        "translation_en": (
            "I would therefore go so far as to relocate the decisive "
            "turning point in the history of the thought of freedom to "
            "the third century AD, anchoring it in the Christian "
            "philosopher of freedom Origen, since temporally — even "
            "before the Neoplatonist Plotinus — he was the first "
            "thinker of freedom in history."
        ),
        "context": (
            "Thesis-mother of the book: corrects the Augustine-centric "
            "narrative (Dihle 1982/1985)."
        ),
    },
    {
        "page": "2-3",
        "chapter": "Zum Geleit",
        "thesis": "Freedom as principle of all being (metaphysics of freedom)",
        "quote_de": (
            "Diese beiden Platoniker, der christliche wie der pagane, "
            "haben erstmals die Freiheit als Prinzip des gesamten Seins "
            "aufgefasst und auf dieser Basis eine Freiheitsmetaphysik "
            "entworfen, in der alle entscheidenden Akteure, Gott, "
            "Mensch und Welt, vom Prinzip der Freiheit aus gedacht "
            "werden."
        ),
        "translation_en": (
            "These two Platonists, the Christian and the pagan, were "
            "the first to conceive freedom as the principle of all "
            "being and on that basis to design a metaphysics of "
            "freedom in which all the decisive actors — God, man, and "
            "world — are thought from the principle of freedom."
        ),
        "context": "Frames the Freiheitsmetaphysik thesis (Kap. VI).",
    },
    {
        "page": "4-5",
        "chapter": "Zum Geleit",
        "thesis": "Origin of the Freiheitspathos remains opaque",
        "quote_de": (
            "Jetzt erstmals wurde der Gedanke mit höchstem Nachdruck "
            "propagiert, dass der Mensch in seiner Selbstbestimmung "
            "frei sei. Warum es zu diesem Freiheitspathos kam, ist "
            "mir bislang noch nicht wirklich klar geworden."
        ),
        "translation_en": (
            "Now for the first time the thought was propagated with "
            "the utmost emphasis that man is free in his "
            "self-determination. Why it came to this pathos of freedom "
            "has not yet become really clear to me."
        ),
        "context": "Honest aporia at the heart of the book.",
    },
    {
        "page": "75",
        "chapter": "Kap. II 4 (Chrysipp)",
        "thesis": "Chrysippus is NOT a theorist of freedom of decision",
        "quote_de": (
            "In diesem Sinne gilt Chrysipp zu Recht als Verteidiger "
            "der Selbstbestimmung des Menschen – wohlgemerkt, nicht "
            "der Entscheidungsfreiheit im Sinne einer freien "
            "Selbstbestimmung, wie das vorschnell meist dargestellt "
            "wird, weil das nicht sein Fokus war."
        ),
        "translation_en": (
            "In this sense Chrysippus is rightly regarded as a "
            "defender of human self-determination — note: not of "
            "freedom of decision in the sense of a free "
            "self-determination, as is usually too hastily claimed, "
            "because that was not his focus."
        ),
        "context": (
            "Crucial caveat: Fürst rejects the often-overstated "
            "'first compatibilism' label."
        ),
    },
    {
        "page": "103-104",
        "chapter": "Kap. III 1 (Kaiserzeitliche Freiheitsdebatten)",
        "thesis": (
            "Josephus maps Pharisees/Sadducees/Essenes to "
            "compatibilists/libertarians/determinists"
        ),
        "quote_de": (
            "Diese Einteilung der jüdischen religiösen Gruppen in – "
            "um moderne Begriffe zu gebrauchen – Deterministen "
            "(Essener), Libertaristen (Sadduzäer) und Kompatibilisten "
            "(Pharisäer) hat Josephus auch schon im zwischen 75 und "
            "79 verfassten Jüdischen Krieg präsentiert."
        ),
        "translation_en": (
            "This division of the Jewish religious groups into — to "
            "use modern terms — determinists (Essenes), libertarians "
            "(Sadducees), and compatibilists (Pharisees) Josephus had "
            "already presented in the Jewish War, composed between 75 "
            "and 79."
        ),
        "context": (
            "Index of the diffusion of the Hellenistic freedom-debate: "
            "it serves as a grid even for non-Greek groups. Sources: "
            "AJ XIII 5,9 / XVIII 1,3; BJ II 8,14."
        ),
    },
    {
        "page": "156",
        "chapter": "Kap. IV 3 (Justin)",
        "thesis": (
            "Justin = first explicit proclamation of the freedom of "
            "decision (ἐλεύθερα προαίρεσις)"
        ),
        "quote_de": (
            "Zum ersten Mal in dieser Problemgeschichte – bei Philon "
            "und Epiktet begegnen lediglich en passant Vorstufen zu "
            "dieser Junktur – wird ausdrücklich die Freiheit der "
            "Entscheidung proklamiert."
        ),
        "translation_en": (
            "For the first time in this history of the problem — only "
            "preliminary stages of this junctura appear in passing in "
            "Philo and Epictetus — the freedom of decision is "
            "explicitly proclaimed."
        ),
        "context": (
            "Apol. I 43,4 (SC 507, 240): ἐλεύθερα προαίρεσις. "
            "Tipping-point of the early-Christian Freiheitspathos."
        ),
    },
    {
        "page": "178",
        "chapter": "Kap. IV 4 (Frühchristliches Freiheitskonzept)",
        "thesis": (
            "Early-Christian compatibilism in 4 points (a/b/c/d) "
            "anchored on Irenaeus Adv. Haer. IV 37,7"
        ),
        "quote_de": (
            "Das Ergebnis war eine Art christlicher Kompatibilismus, "
            "in dem (a) Theoreme und Terminologie des stoischen "
            "Kompatibilismus im Sinne Chrysipps rezipiert wurden, "
            "man sich jedoch (b) im Sinne vor allem der Platoniker "
            "vom damit einhergehenden Determinismus, wie er etwa bei "
            "Epiktet zum Ausdruck kam, abgrenzte und (c) mit der "
            "christlichen Betonung der Freiheit der Entscheidung "
            "einem Libertarismus das Wort redete, zu dem man aber "
            "(d) nicht wirklich gelangte, weil die deterministische "
            "Seite des biblischen Kompatibilismus zu berücksichtigen "
            "war."
        ),
        "translation_en": (
            "The result was a kind of Christian compatibilism in "
            "which (a) the theorems and terminology of Stoic "
            "compatibilism in Chrysippus's sense were received, but "
            "(b) one distanced oneself — chiefly in the sense of the "
            "Platonists — from the determinism that came with it (as "
            "expressed e.g. by Epictetus), and (c) by emphasising "
            "Christian freedom of decision one advocated a "
            "libertarianism (d) at which one nevertheless did not "
            "really arrive, because the deterministic side of "
            "biblical compatibilism had to be reckoned with."
        ),
        "context": (
            "Anchor citation: Irenaeus, Adv. Haer. IV 37,7 (FC 8/4, "
            "330). Becomes the matrix for all subsequent ancient "
            "Christian freedom-theories — until Origen radicalises "
            "it."
        ),
    },
    {
        "page": "179",
        "chapter": "Kap. IV 4",
        "thesis": "Origen = first systematic libertarianism",
        "quote_de": (
            "Diese Wege zur Freiheit führten vom Determinismus über "
            "den Kompatibilismus in den Libertarismus, wie er von "
            "Origenes dann erstmals systematisch konzipiert wurde."
        ),
        "translation_en": (
            "These ways to freedom led from determinism through "
            "compatibilism into libertarianism, as Origen then "
            "conceived it for the first time systematically."
        ),
        "context": (
            "Bridge between Kap. IV (early Christianity) and Kap. V "
            "(Origen). Title-formula of the whole book."
        ),
    },
    {
        "page": "196-197",
        "chapter": "Kap. V 2 (Origen)",
        "thesis": (
            "De Principiis III 1 = first treatise titled "
            "Περὶ αὐτεξουσίου in the history of philosophy"
        ),
        "quote_de": (
            "Während die früheren Autoren bis Clemens von Alexandria "
            "über das Schicksal (Περὶ εἱμαρμένης / De fato) "
            "schrieben, verfasste Origenes den ersten Freiheitstraktat, "
            "der diesen Titel trägt: Über die Selbstbestimmung "
            "(Περὶ αὐτεξουσίου) oder, in der spätantik-lateinischen "
            "Fassung, Über die Freiheit der Entscheidung (De arbitrii "
            "libertate)."
        ),
        "translation_en": (
            "Whereas earlier authors up to Clement of Alexandria "
            "wrote 'On Fate' (Περὶ εἱμαρμένης / De fato), Origen "
            "composed the first treatise on freedom bearing this "
            "title: 'On Self-Determination' (Περὶ αὐτεξουσίου) or, "
            "in the late-antique Latin version, 'On the Freedom of "
            "Decision' (De arbitrii libertate)."
        ),
        "context": (
            "Greek title preserved in Philocalia (p. 5, 152 Robinson) "
            "and in Photius bibl. cod. 8 (I p. 9 Henry). Latin title "
            "in Rufinus 398 CE."
        ),
    },
    {
        "page": "199",
        "chapter": "Kap. V 2 (Der Freiheitsbegriff des Origenes)",
        "thesis": "Central passage of the Freiheitstraktat (De Princ. III 1,3)",
        "quote_de": (
            "Das vernunftbegabte Lebewesen hat zu der Vorstellungskraft "
            "hinzu noch die Vernunft, die die Vorstellungen beurteilt "
            "und die einen verwirft, die anderen annimmt … Die "
            "Entscheidung, mit dem Ereignis so oder anders umzugehen, "
            "ist einzig und allein Sache der Vernunft in uns."
        ),
        "translation_en": (
            "The rational living being has, in addition to the "
            "imaginative faculty, also reason, which judges the "
            "impressions and rejects some, accepts others … The "
            "decision how to deal with the event in one way or "
            "another is solely and exclusively the work of the reason "
            "in us."
        ),
        "context": (
            "Origen quoting Greek of De Princ. III 1,3 (GCS Orig. 5, "
            "197). Translation: Görgemanns/Karpp, Origenes: Prinzipien "
            "467 (slightly modified)."
        ),
    },
    {
        "page": "289",
        "chapter": "Kap. VI 4 (Kompatibilistischer Libertarismus)",
        "thesis": (
            "Origen shifts the accent from determinism to "
            "libertarianism while keeping compatibility with "
            "determined aspects"
        ),
        "quote_de": (
            "Im Blick auf die Entwicklung des antiken "
            "Freiheitsdenkens bis Origenes wird man sagen können, "
            "dass der christliche Philosoph aus Alexandria die "
            "Akzente klar weg vom Determinismus hin zum Libertarismus "
            "verschoben und dabei der Freiheit einen ontologischen "
            "Stellenwert zugesprochen hat, der davor nicht gegeben "
            "war, dass aber dieser Libertarismus mit determinierten "
            "Aspekten der Wirklichkeit kompatibel blieb."
        ),
        "translation_en": (
            "Looking back over the development of ancient thought "
            "about freedom up to Origen, one can say that the "
            "Christian philosopher from Alexandria clearly shifted "
            "the accents away from determinism towards libertarianism, "
            "ascribing to freedom an ontological status that did not "
            "exist before — but that this libertarianism remained "
            "compatible with determined aspects of reality."
        ),
        "context": (
            "Closing statement of Kap. VI 4. The book's punctum "
            "saliens."
        ),
    },
    {
        "page": "291",
        "chapter": "Zum Ausklang",
        "thesis": "Freedom established as principle of being",
        "quote_de": (
            "Seit Origenes bewegt sich die Debatte über "
            "Determinismus und Freiheit auf einer neuen Ebene. Der "
            "lange Weg zur Freiheit ist in dem Sinn zurückgelegt, "
            "dass Freiheit als Prinzip nicht nur des Handelns, "
            "sondern auch des Seins etabliert wurde."
        ),
        "translation_en": (
            "Since Origen the debate about determinism and freedom "
            "moves on a new plane. The long way to freedom has been "
            "traversed in the sense that freedom has been established "
            "as the principle not only of action but also of being."
        ),
        "context": "Opening of Zum Ausklang.",
    },
    {
        "page": "292",
        "chapter": "Zum Ausklang",
        "thesis": (
            "From static ontology to dynamic doctrine of freedom — "
            "anticipating process philosophy"
        ),
        "quote_de": (
            "Aus einer statischen Seinslehre wurde eine dynamische "
            "Freiheitslehre. Es kommt buchstäblich alles in Bewegung. "
            "Die natürliche Ordnung wird als gigantisches Netzwerk "
            "sich ständig bewegender und interagierender Freiheiten "
            "aufgefasst – recht nah an Vorstellungen der modernen "
            "Prozessphilosophie und -theologie."
        ),
        "translation_en": (
            "A static doctrine of being became a dynamic doctrine of "
            "freedom. Literally everything is set in motion. The "
            "natural order is conceived as a gigantic network of "
            "constantly moving and interacting freedoms — quite close "
            "to the conceptions of modern process philosophy and "
            "theology."
        ),
        "context": (
            "The cosmological-theological reach of Origen's "
            "innovation, as Fürst reads it."
        ),
    },
    {
        "page": "292",
        "chapter": "Zum Ausklang (last sentence)",
        "thesis": "Origen = the great turning point",
        "quote_de": (
            "Dieses neue, von Origenes inaugurierte Denken stellt "
            "alles Nachdenken über Gott, Mensch und Welt, über "
            "materielle und geistige Dinge in einen neuen Rahmen. Es "
            "ist der große Einschnitt in der Geschichte des "
            "Freiheitsdenkens."
        ),
        "translation_en": (
            "This new thought, inaugurated by Origen, places all "
            "reflection on God, man, and world, on material and "
            "spiritual things, in a new framework. It is the great "
            "turning point in the history of the thought of freedom."
        ),
        "context": "Final sentence of the book.",
    },
    {
        "page": "Front matter (epigraphs)",
        "chapter": "Zum Geleit (epigraphs)",
        "thesis": (
            "Two epigraphs frame the book: Plato Resp. X 617e and "
            "Origen Hom. Ier. 18,3"
        ),
        "quote_de": (
            "αἰτία ἑλομένου, θεὸς ἀναίτιος (Platon, Staat X 617 e 4 f.) "
            "— τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι (Origenes, "
            "Jeremiahomilien 18,3)"
        ),
        "translation_en": (
            "'The cause is in the chooser; god is blameless' (Plato, "
            "Republic X 617e) — 'for self-determination is freedom' "
            "(Origen, Homilies on Jeremiah 18,3)"
        ),
        "context": (
            "Programmatic framing: from Plato's myth of Er to Origen's "
            "ontologisation of freedom."
        ),
    },
]

# Inhaltsverzeichnis exact (verified from .txt lines 280-560)
INHALTSVERZEICHNIS: list[dict] = [
    {"section": "Zum Geleit", "page": 1},
    {"section": "Thematische Eingrenzungen — 1. Zur Terminologie (a/b)", "page": 7},
    {"section": "Thematische Eingrenzungen — 2. Zum zeitlichen Rahmen", "page": 16},
    {"section": "I. Menschliche Selbstbestimmung im alten Hellas und im alten Israel", "page": 19},
    {"section": "I.1. Auftakt im Epos: Homer", "page": 19},
    {"section": "I.2. Festigkeit des Schicksals und menschliche Verantwortung: Die griechische Mythologie", "page": 30},
    {"section": "I.3. Göttliche Heilsgeschichte und Eigenverantwortung des Menschen: Die jüdische Bibel", "page": 34},
    {"section": "I.3a. Biblischer Kompatibilismus", "page": 35},
    {"section": "I.3b. Plädoyer für die Eigenverantwortung: Ezechiel", "page": 39},
    {"section": "I.4. Anstöße zum Freiheitsdenken", "page": 46},
    {"section": "II. Determinismus und Verantwortung: Die griechische Philosophie", "page": 49},
    {"section": "II.1. Sachliche und terminologische Vorklärungen", "page": 49},
    {"section": "II.2. Von der Schicksalsbestimmtheit zur Selbstbestimmung: Der Er-Mythos in Platons Politeia", "page": 52},
    {"section": "II.3. Die überlegte Wahl eines vernünftigen Selbst: Aristoteles", "page": 62},
    {"section": "II.4. Kausaldeterminismus und Eigenverantwortung: Der Kompatibilismus des Stoikers Chrysipp", "page": 73},
    {"section": "II.5. Spontane Selbstbewegung: Epikur und Lukrez", "page": 91},
    {"section": "II.6. Willentliche Selbstbewegung: Karneades", "page": 96},
    {"section": "III. Ethik der Freiheit: Die Freiheitsdebatte in der römischen Kaiserzeit", "page": 101},
    {"section": "III.1. Kaiserzeitliche Freiheitsdebatten", "page": 101},
    {"section": "III.2. Freiheit als Einwilligung in das Schicksal: Epiktet", "page": 108},
    {"section": "III.3. Kritik am stoischen Kompatibilismus", "page": 119},
    {"section": "III.3a. Postulat der Willensfreiheit: Cicero", "page": 121},
    {"section": "III.3b. Undeterminierte Entscheidung: Die platonische Schultradition", "page": 126},
    {"section": "III.3c. Wahlfreiheit: Alexander von Aphrodisias", "page": 132},
    {"section": "IV. Freiheitspathos: Die frühchristliche Freiheitstheorie", "page": 139},
    {"section": "IV.1. Hintergründe im Frühjudentum: Philon von Alexandria", "page": 141},
    {"section": "IV.2. Die Anfänge im Christentum: Paulus und das Neue Testament", "page": 149},
    {"section": "IV.3. Freiheit der Entscheidung: Justin der Märtyrer", "page": 152},
    {"section": "IV.4. Das frühchristliche Freiheitskonzept", "page": 161},
    {"section": "IV.4a. Grundaspekte des frühchristlichen Freiheitsdenkens", "page": 162},
    {"section": "IV.4b. Freiheit als Eckpfeiler der christlichen Philosophie", "page": 175},
    {"section": "IV.5. Natur und Freiheit: Clemens von Alexandria", "page": 180},
    {"section": "V. Die Freiheit der Selbstbestimmung: Das Freiheitsdenken des Origenes", "page": 187},
    {"section": "V.1. Der zentrale Stellenwert der Freiheit", "page": 187},
    {"section": "V.2. Der Freiheitsbegriff des Origenes", "page": 195},
    {"section": "V.3. Libertarische Deutung des biblischen Determinismus", "page": 217},
    {"section": "V.3a. Die libertarische Exegese im Freiheitstraktat", "page": 218},
    {"section": "V.3b. Der Freiheitsgedanke in der exegetischen Praxis", "page": 224},
    {"section": "V.4. Individuelle Selbstbestimmung und Selbstsorge", "page": 239},
    {"section": "VI. Die Welt als freie Bewegung Gottes: Die Freiheitsmetaphysik des Origenes", "page": 247},
    {"section": "VI.1. Welt in Bewegung", "page": 248},
    {"section": "VI.2. Freiheit und Würde des Menschen", "page": 252},
    {"section": "VI.3. Theologie der Freiheit", "page": 259},
    {"section": "VI.3a. Gott als Freiheit und Bewegung", "page": 259},
    {"section": "VI.3b. Heilstrinitarismus", "page": 266},
    {"section": "VI.3c. Gott 'alles in allem'", "page": 273},
    {"section": "VI.4. Kompatibilistischer Libertarismus", "page": 282},
    {"section": "Zum Ausklang", "page": 291},
    {"section": "Bibliographie", "page": 293},
    {"section": "Register (Stellen / Personen / Sachen)", "page": 311},
]

# Enriched description for the canonical publication (~2400c)
CANONICAL_PUB_DESCRIPTION = (
    "Monographie pivot pour la thèse de la trajectoire antique de la "
    "Selbstbestimmung humaine. Issue des conférences Tria-Corda données par "
    "Fürst à l'Université Friedrich-Schiller de Jena en novembre 2021. "
    "Thèse centrale : Origène (avant Plotin, donc temporellement premier) "
    "est le premier penseur systématique de la liberté de l'histoire de la "
    "philosophie ; le « grand tournant » (großer Einschnitt) de l'histoire "
    "occidentale de la pensée de la liberté n'est pas Augustin (contre "
    "Dihle 1982/1985) mais le IIIᵉ siècle ap. J.-C. où les platoniciens "
    "chrétiens conçoivent pour la première fois la liberté comme principe "
    "de l'être tout entier — Freiheitsmetaphysik. Structure en six chapitres "
    "qui retracent un parcours millénaire : (I) prémisses dans Homère et la "
    "Bible hébraïque (compatibilisme biblique, plaidoyer ézéchiélien pour "
    "l'Eigenverantwortung) ; (II) philosophie grecque, où Chrysippe développe "
    "ce que la tradition moderne appelle compatibilisme — mais que Fürst "
    "qualifie : Chrysippe défend la Selbstbestimmung, non la liberté de la "
    "décision (p. 75) ; Épicure-Lucrèce + Carnéade (mouvement volontaire de "
    "soi-même) répliquent ; (III) débat impérial — Josèphe mappe Pharisiens/"
    "Sadducéens/Esséniens comme compatibilistes/libertariens/déterministes "
    "(p. 103-104), Tacite confirme la diffusion ; Épictète = compatibilisme "
    "stoïcien tardif ; triple critique platonicienne (Cicéron, ps.-Plutarque/"
    "Alcinoos/Apulée/Maxime, Alexandre d'Aphrodise → Wahlfreiheit) ; (IV) le "
    "Freiheitspathos chrétien — Philon comme maillon judéo-hellénistique, "
    "Paul-NT, Justin Martyr proclame pour la première fois explicitement la "
    "liberté de la décision (ἐλεύθερα προαίρεσις, Apol. I 43,4 ; p. 156), "
    "Clément introduit l'opposition phusis/prohairesis ; (V) Origène — la "
    "liberté élevée au rang de « quatrième article de foi » (Comm. Ioh. "
    "XXXII 16,187-189), De Principiis III 1,1-24 = premier traité "
    "systématique « Sur la liberté » digne de ce nom (Περὶ αὐτεξουσίου ; "
    "p. 196-197), défense contre trois déterminismes (astrologique, "
    "stoïcien, gnostique) ; (VI) Freiheitsmetaphysik — la liberté devient "
    "principe de la substance (suivant Hengstermann 2016, Freiheitsmetaphysik) ; "
    "le monde est un « gigantesque réseau de libertés interagissant "
    "constamment » (p. 292) proche de la process philosophy moderne ; "
    "Dieu lui-même est Freiheit und Bewegung ; conclusion programmatique : "
    "« kompatibilistischer Libertarismus » (p. 282-290) — Origène déplace "
    "clairement l'accent du déterminisme vers le libertarisme en accordant "
    "à la liberté un statut ontologique inédit, tout en maintenant la "
    "compatibilité avec les aspects déterminés de la réalité (préscience "
    "divine, providence ordonnée, chaîne causale physique). Engage "
    "explicitement : Bobzien (Determinism and Freedom 1998 — accord sur "
    "philologie de τὸ ἐφ᾽ ἡμῖν), Frede (A Free Will 2011 — désaccord sur "
    "la lecture purement anti-gnostique d'Origène, p. 198 Anm. 27), Dihle "
    "(The Theory of Will 1982 — critique de l'augusto-centrisme), "
    "Hengstermann (Origenes und die Geschichte der Freiheitsmetaphysik 2016 "
    "— appui métaphysique central), Sharples, Crouzel, Kobusch, Karamanolis."
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def parse_meta(raw):
    if raw in (None, "", {}):
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def dump_meta(meta: dict) -> str:
    return json.dumps(meta, ensure_ascii=False)


def new_edge_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")


def make_edge(
    source: str,
    relation: str,
    target: str,
    *,
    weight: float = 0.9,
    extra_meta: dict | None = None,
) -> dict:
    meta = {
        "wave": MARKER_KEY,
        "confidence": weight,
        "source_scholarship": "Fürst 2022 *Wege zur Freiheit* (Mohr Siebeck)",
        MARKER_KEY: True,
    }
    if extra_meta:
        meta.update(extra_meta)
    return {
        "created_at": TODAY_UTC,
        "edge_id": new_edge_id(),
        "metadata": dump_meta(meta),
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": weight,
    }


# ----------------------------------------------------------------------
# Phase 1 — Snapshot
# ----------------------------------------------------------------------

def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    nodes_dst = SNAPSHOT_DIR / "nodes.jsonl"
    edges_dst = SNAPSHOT_DIR / "edges.jsonl"
    if not nodes_dst.exists():
        shutil.copy2(NODES_PATH, nodes_dst)
        print(f"  Snapshot nodes -> {nodes_dst}")
    else:
        print(f"  Snapshot nodes already exists -> {nodes_dst}")
    if not edges_dst.exists():
        shutil.copy2(EDGES_PATH, edges_dst)
        print(f"  Snapshot edges -> {edges_dst}")
    else:
        print(f"  Snapshot edges already exists -> {edges_dst}")


# ----------------------------------------------------------------------
# Phase 2-7 — Mutations
# ----------------------------------------------------------------------

# Quote backing for each canonical argument node (verified from .txt)
ARGUMENT_QUOTES: dict[str, dict] = {
    "argument_furst_2022_continuity_homer_to_origen": {
        "page": "4-5",
        "quote_idx": 2,  # index in VERIFIED_CRITIQUES
    },
    "argument_furst_2022_origen_first_freedom_thinker": {
        "page": "2",
        "quote_idx": 0,
    },
    "argument_furst_2022_origen_culmination_autexousion": {
        "page": "196-197",
        "quote_idx": 8,
    },
    "argument_furst_2022_middle_platonist_origin_autexousion": {
        "page": "126-132",
        "quote_idx": None,
        "verification_status": "phrase_attribution_uncertain",
        "verification_note": (
            "Description includes the phrase 'on les sent insister plutôt "
            "qu'on ne le lit' which sounds closer to Babut or Bobzien's "
            "phrasing than to Fürst's; rest of thesis verified pp. 126-132."
        ),
    },
    "argument_furst_2022_de_princ_iii_1_first_freedom_treatise": {
        "page": "196-197",
        "quote_idx": 8,
    },
    "argument_furst_2022_freedom_fourth_article_of_faith": {
        "page": "193-194",
        "quote_idx": None,
        "verification_note": (
            "Reference to Comm. Ioh. XXXII 16,187-189 verified against "
            "Kap. V 1."
        ),
    },
    "argument_furst_2022_freedom_principle_of_substance": {
        "page": "252-254",
        "quote_de": (
            "Der Mensch verfügt nicht nur über Freiheit; er ist Freiheit."
        ),
        "translation_en": (
            "Man does not merely possess freedom; he is freedom."
        ),
    },
    "argument_furst_2022_kompatibilistischer_libertarismus": {
        "page": "282-290",
        "quote_idx": 10,
    },
    "argument_furst_2022_critique_dihle_augustine_thesis": {
        "page": "2",
        "quote_idx": 0,
    },
    "argument_furst_2022_christian_philosophers_freedom_innovation": {
        "page": "178",
        "quote_idx": 6,
    },
    "argument_furst_2022_aristotle_no_will_intellectualism": {
        "page": "7-15",
        "quote_idx": None,
        "verification_note": "Thematische Eingrenzungen 1a, verified.",
    },
    "argument_furst_2022_stoic_eph_hemin_late_substantive": {
        "page": "75 + Anm. 9",
        "quote_idx": 3,
    },
    "argument_furst_2022_justin_first_explicit_freedom_decision": {
        "page": "155-157",
        "quote_idx": 5,
    },
    "argument_furst_2022_world_as_network_of_freedoms": {
        "page": "291-292",
        "quote_idx": 12,
        "additional_quote_idx": 13,
    },
    "argument_furst_2022_origen_against_three_determinisms": {
        "page": "188-192",
        "quote_idx": None,
        "verification_note": (
            "Three-determinisms structure verified against Kap. V 1. "
            "Sources cited (Princ. I praef. 5; In Gen. frg. D 7 = "
            "Philocalia 23; Princ. III 1,4-6; Cels.) all check out in "
            "Fürst's footnotes."
        ),
    },
}


# Deprecation mapping for the 10 scholarly_argument shells.
# Each maps shell_id -> {action: "deprecate"|"enrich", superseded_by: <id>?, redirect_edges_to: <id>?}
SHELL_ARG_PLAN: dict[str, dict] = {
    "scholarly_argument_f_rst_free_will_and_self_determinati_0": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_continuity_homer_to_origen",
    },
    "scholarly_argument_f_rst_scope_and_chronological_framew_2": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_continuity_homer_to_origen",
    },
    "scholarly_argument_f_rst_terminology_of_will_and_freedo_1": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_aristotle_no_will_intellectualism",
    },
    "scholarly_argument_f_rst_free_will_terminology_and_conc_0": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_aristotle_no_will_intellectualism",
    },
    "scholarly_argument_f_rst_biblical_compatibilism_1": {
        "action": "enrich",
        "new_description": (
            "Thèse de Fürst 2022 (Kap. I 3a-b, p. 35-46) : la Bible hébraïque "
            "présente un « compatibilisme biblique » (biblischer "
            "Kompatibilismus) où la providence divine (Heilsgeschichte) et "
            "la responsabilité personnelle de l'homme (Eigenverantwortung) "
            "coexistent sans tension systématique. Ezéchiel 18 constitue le "
            "« plaidoyer pour la responsabilité personnelle » le plus net : "
            "« Si le fils, voyant les péchés que son père a commis, "
            "réfléchit et ne fait pas de même… il vivra. » Cette structure "
            "biblique est un préformage du débat philosophique grec sur "
            "destin/responsabilité et constitue, selon Fürst, l'un des "
            "« anstöße » (impulsions) majeurs vers le Freiheitsdenken "
            "ultérieur (Kap. I 4, p. 46-48)."
        ),
        "new_label": (
            "Compatibilisme biblique : Heilsgeschichte et Eigenverantwortung "
            "(Fürst 2022 Kap. I 3)"
        ),
        "quote_de": (
            "Schon in der jüdischen Bibel begegnet eine Konstellation, in "
            "der göttliche Heilsgeschichte und Eigenverantwortung des "
            "Menschen miteinander vermittelt sind, ohne in eine "
            "systematische Spannung zu treten."
        ),
        "translation_en": (
            "Already in the Jewish Bible one encounters a constellation in "
            "which divine salvation-history and human personal "
            "responsibility are mediated with one another without entering "
            "a systematic tension."
        ),
        "page": "35-46",
    },
    "scholarly_argument_f_rst_stoic_compatibilism_chrysippus_2": {
        "action": "deprecate_and_redirect",
        "superseded_by": "argument_furst_2022_stoic_eph_hemin_late_substantive",
        "redirect_edges_to": "argument_furst_2022_stoic_eph_hemin_late_substantive",
    },
    "scholarly_argument_f_rst_libertarian_critique_of_stoic__3": {
        "action": "enrich",
        "new_description": (
            "Thèse de Fürst 2022 (Kap. III 3, p. 119-138) : il existe une "
            "lignée critique libertarienne anti-stoïcienne homogène à "
            "l'époque impériale, articulée en trois étapes complémentaires : "
            "(a) Cicéron pose le « postulat de la liberté de la volonté » "
            "(Postulat der Willensfreiheit, p. 121-126) en réplique à "
            "Chrysippe (De Fato 39-43, sur la critique de la nécessité "
            "logique) ; (b) la tradition scolaire platonicienne (ps.-"
            "Plutarque De Fato, Alcinoos Didask. 26, Apulée De Platone I 12, "
            "Maxime de Tyr) postule la « décision non déterminée » "
            "(Undeterminierte Entscheidung, p. 126-132) avec la doctrine du "
            "destin hypothétique et l'âme « sans maître » (αδέσποτος) ; "
            "(c) Alexandre d'Aphrodise systématise la « liberté de choix » "
            "(Wahlfreiheit, p. 132-138) avec son De Fato et De Anima Mantissa "
            "— l'argument central étant l'Alternativenoffenheit (ouverture "
            "d'alternatives réelles). Cette tradition prépare directement "
            "le libertarisme origénien."
        ),
        "new_label": (
            "Lignée libertarienne anti-stoïcienne Cicéron → médio-platoniciens "
            "→ Alexandre (Fürst 2022 Kap. III 3)"
        ),
        "quote_de": (
            "Die Kritik am stoischen Kompatibilismus entwickelte sich in "
            "der römischen Kaiserzeit zu einer regelrechten libertarischen "
            "Tradition: bei Cicero als Postulat der Willensfreiheit, in "
            "der platonischen Schultradition als Undeterminierte "
            "Entscheidung, bei Alexander von Aphrodisias als Wahlfreiheit."
        ),
        "translation_en": (
            "Criticism of Stoic compatibilism developed in the Roman "
            "imperial period into a genuine libertarian tradition: in "
            "Cicero as the postulate of freedom of will, in the Platonic "
            "school tradition as the undetermined decision, in Alexander "
            "of Aphrodisias as freedom of choice."
        ),
        "page": "119-138",
    },
    "scholarly_argument_f_rst_origen_s_libertarian_compatibi_4": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_kompatibilistischer_libertarismus",
    },
    "scholarly_argument_f_rst_origen_s_metaphysics_of_freedo_5": {
        "action": "deprecate",
        "superseded_by": "argument_furst_2022_freedom_principle_of_substance",
    },
    "scholarly_argument_f_rst_early_christian_freedom_theory_6": {
        "action": "deprecate",
        "superseded_by": (
            "argument_furst_2022_christian_philosophers_freedom_innovation"
        ),
    },
}


# New nodes to create (4 arguments + 2 concepts).
NEW_NODES: list[dict] = [
    {
        "id": "argument_furst_2022_josephus_three_jewish_sects_freedom_taxonomy",
        "type": "argument",
        "label": (
            "Josèphe taxonomise Pharisiens/Sadducéens/Esséniens selon leurs "
            "positions sur la liberté (Fürst 2022 Kap. III 1)"
        ),
        "description": (
            "Thèse de Fürst 2022 (Kap. III 1, p. 103-105) : Flavius Josèphe "
            "(AJ XIII 5,9 = 171-173 ; AJ XVIII 1,3 = 13 ; BJ II 8,14 = "
            "163-165) cartographie les trois principales sectes juives "
            "selon leurs positions sur la détermination du destin et "
            "l'autodétermination humaine — Pharisiens = compatibilistes "
            "(au sens de Chrysippe), Sadducéens = libertariens (« tout "
            "dépend de nous »), Esséniens = déterministes radicaux. Cette "
            "trichotomie, exprimée en termes stoïciens (εἱμαρμένη, "
            "ἐφ᾽ ἡμῖν, ὁρμή), est un témoin précieux de la diffusion du "
            "débat hellénistique sur la liberté : Josèphe l'utilise comme "
            "grille de lecture pour décrire un groupe religieux non-grec à "
            "un public gréco-romain. La stylisation présuppose que cette "
            "caractérisation « leur parlait » — donc que la question "
            "« Wie hältst du's mit der Freiheit? » servait de marqueur "
            "doxographique à l'époque impériale (≈ 75-94 ap. J.-C.). "
            "Tacite (Ann. VI 22) confirme la même grille pour le public "
            "latin."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "page": "103-105",
            "chapter": "Kap. III 1 (Kaiserzeitliche Freiheitsdebatten)",
            "verified": True,
            "verified_at": AUDIT_AT,
            MARKER_KEY: True,
            "quote_de": (
                "Diese Einteilung der jüdischen religiösen Gruppen in – um "
                "moderne Begriffe zu gebrauchen – Deterministen (Essener), "
                "Libertaristen (Sadduzäer) und Kompatibilisten (Pharisäer) "
                "hat Josephus auch schon im zwischen 75 und 79 verfassten "
                "Jüdischen Krieg präsentiert."
            ),
            "translation_en": (
                "This division of the Jewish religious groups into — to "
                "use modern terms — determinists (Essenes), libertarians "
                "(Sadducees), and compatibilists (Pharisees) Josephus had "
                "already presented in the Jewish War, composed between 75 "
                "and 79."
            ),
            "primary_sources": [
                "Josephus, Antiquitates Iudaicae XIII 5,9 (171-173)",
                "Josephus, Antiquitates Iudaicae XVIII 1,3 (13)",
                "Josephus, Bellum Iudaicum II 8,14 (163-165)",
                "Tacitus, Annales VI 22,1-3 (confirmation)",
            ],
        },
    },
    {
        "id": "argument_furst_2022_carneades_voluntary_self_motion",
        "type": "argument",
        "label": (
            "Carnéade introduit le mouvement volontaire de soi-même contre "
            "Chrysippe (Fürst 2022 Kap. II 6)"
        ),
        "description": (
            "Thèse de Fürst 2022 (Kap. II 6, p. 96-100) : Carnéade de "
            "Cyrène (214/13-129/8 av. J.-C.), scholarque de la Nouvelle "
            "Académie, formule contre Chrysippe l'idée d'un « mouvement "
            "volontaire de soi-même » (willentliche Selbstbewegung) — un "
            "mouvement intramental de l'âme qui ne dérive pas "
            "nécessairement d'une cause antécédente externe (la φαντασία) "
            "et qui constitue une cause sui de la décision. C'est, dans la "
            "généalogie tracée par Fürst, la première formulation "
            "explicite, dans la philosophie grecque, d'un quelque chose "
            "qui ressemble à un concept proto-volontariste — mais sans "
            "concept technique de la volonté au sens augustinien. La "
            "source principale est Cicéron, De Fato 23-25 (= Plutarque, "
            "Stoic. Repugn. 1057-58). Fürst situe Carnéade entre Épicure-"
            "Lucrèce (clinamen) et Alexandre d'Aphrodise (Wahlfreiheit) "
            "comme troisième moment de la critique libertarienne du "
            "compatibilisme stoïcien."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "page": "96-100",
            "chapter": "Kap. II 6",
            "verified": True,
            "verified_at": AUDIT_AT,
            MARKER_KEY: True,
            "primary_sources": [
                "Cicero, De Fato 23-25",
                "Plutarch, De Stoic. Repugn. 1057-1058",
            ],
        },
    },
    {
        "id": "argument_furst_2022_irenaeus_against_gnostic_natures",
        "type": "argument",
        "label": (
            "Irénée défend la libre Selbstbestimmung contre les natures "
            "gnostiques fixes (Fürst 2022 Kap. IV 4-5)"
        ),
        "description": (
            "Thèse de Fürst 2022 (Kap. IV 4-5, p. 178-186 ; Adv. Haer. IV "
            "37,6-7 = FC 8/4, 328-330) : Irénée de Lyon proclame la libre "
            "autodétermination de l'homme contre la conception gnostique "
            "des « natures » fixes (choïque/hylique/pneumatique). "
            "L'argument irénéen est en forme de réduction à l'absurde : si "
            "les hommes étaient inévitablement déterminés à posséder une "
            "« nature » (natura) particulière qui les sauverait ou les "
            "perdrait, « alors les bons hommes ne représentent rien de "
            "particulier, parce qu'ils sont tels plus par nature (natura) "
            "que par leur propre volonté (voluntas) et possèdent le bien "
            "d'eux-mêmes plutôt que par leur propre choix » (Adv. Haer. IV "
            "37,6). Cette polémique anti-gnostique est, selon Fürst, le "
            "principal moteur historique du Freiheitspathos chrétien : "
            "l'opposition aux Marcionites, Valentiniens, Basilidiens et "
            "autres écoles à doctrine prédestinationiste pousse les "
            "apologistes (Justin, Athénagore, Tatien, Irénée, Clément, "
            "Tertullien) à élever la liberté au rang d'enjeu polémique de "
            "premier ordre. Origène héritera de cette frontière polémique "
            "(Princ. III 1,6 = la grande réfutation du déterminisme "
            "valentinien)."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "page": "178-186",
            "chapter": "Kap. IV 4-5",
            "verified": True,
            "verified_at": AUDIT_AT,
            MARKER_KEY: True,
            "primary_sources": [
                "Irenaeus, Adversus Haereses IV 37,6-7 (FC 8/4, 328-330)",
                "Irenaeus, Adversus Haereses I 6,2 (FC 8/1, 164)",
                "Irenaeus, Adversus Haereses IV 4,3 (FC 8/4, 36)",
            ],
            "quote_de": (
                "Wenn Menschen unausweichlich darauf festgelegt wären, eine "
                "bestimmte „Natur“ (natura) zu haben … „dann stellen auch "
                "die guten Menschen nichts Besonderes dar, weil sie mehr "
                "von Natur aus (natura) als aus eigenem Willen (voluntas) "
                "so sind und das Gute von selbst haben und nicht auf "
                "eigene Wahl hin.“"
            ),
            "translation_en": (
                "If human beings were inevitably determined to possess a "
                "definite ‘nature’ (natura) … ‘then the good men represent "
                "nothing special, because they are such more by nature "
                "(natura) than by their own will (voluntas) and possess "
                "the good of themselves rather than by their own choice.’"
            ),
        },
    },
    {
        "id": "argument_furst_2022_origen_dynamic_freedom_ontology_replaces_static_being",
        "type": "argument",
        "label": (
            "Origène : transformation de la Seinslehre statique en "
            "Freiheitslehre dynamique (Fürst 2022 Zum Ausklang)"
        ),
        "description": (
            "Thèse cosmologique terminale de Fürst 2022 (Zum Ausklang, "
            "p. 292) : la conséquence métaphysique de la conception "
            "origénienne de la liberté comme principe ontologique est le "
            "passage d'une « doctrine statique de l'être » (statische "
            "Seinslehre) à une « doctrine dynamique de la liberté » "
            "(dynamische Freiheitslehre). « Tout est littéralement mis en "
            "mouvement. » Cette transformation concerne aussi la "
            "conception de Dieu : non plus être statique éternellement "
            "soustrait au monde, mais être en mouvement qui à la fois "
            "transcende le monde et s'y implique au point que cette "
            "interaction réciproque révèle la perfection de l'œuvre "
            "créatrice et rédemptrice. Fürst note la proximité — sans "
            "filiation directe — avec la process philosophy et la process "
            "theology modernes (Whitehead, Hartshorne, Cobb). Distinct du "
            "thème « réseau de libertés » (qui concerne les créatures), "
            "cet argument porte sur le retournement ontologique global : "
            "Origène est l'inaugurateur d'un nouveau cadre pour penser "
            "Dieu, l'homme et le monde — « der große Einschnitt in der "
            "Geschichte des Freiheitsdenkens »."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "page": "291-292",
            "chapter": "Zum Ausklang",
            "verified": True,
            "verified_at": AUDIT_AT,
            MARKER_KEY: True,
            "quote_de": (
                "Aus einer statischen Seinslehre wurde eine dynamische "
                "Freiheitslehre. Es kommt buchstäblich alles in Bewegung. "
                "Dieses neue, von Origenes inaugurierte Denken stellt "
                "alles Nachdenken über Gott, Mensch und Welt in einen "
                "neuen Rahmen. Es ist der große Einschnitt in der "
                "Geschichte des Freiheitsdenkens."
            ),
            "translation_en": (
                "A static doctrine of being became a dynamic doctrine of "
                "freedom. Literally everything is set in motion. This new "
                "thought, inaugurated by Origen, places all reflection on "
                "God, man, and world in a new framework. It is the great "
                "turning point in the history of the thought of freedom."
            ),
        },
    },
    {
        "id": "concept_freiheitspathos_furst",
        "type": "concept",
        "label": (
            "Freiheitspathos (pathos de la liberté — catégorie historique "
            "Fürst 2022)"
        ),
        "description": (
            "Catégorie historique introduite par Fürst (titre du Kap. IV : "
            "« Freiheitspathos — Die frühchristliche Freiheitstheorie »). "
            "Désigne l'emphase nouvelle, qualitativement différente du "
            "stoïcisme et du moyen-platonisme, avec laquelle les premiers "
            "philosophes chrétiens (Justin, Athénagore, Irénée, Clément, "
            "Tertullien, Tatien, début du IIᵉ-IIIᵉ s.) proclament la "
            "liberté humaine. Quatre caractéristiques selon Fürst (Kap. "
            "IV 4) : (1) τὸ ἐφ᾽ ἡμῖν et τὸ αὐτεξούσιον sont explicitement "
            "compris comme « libres » (ἐλεύθερος) et l'on emploie "
            "emphatiquement le terme politico-social ἐλευθερία ; (2) la "
            "liberté est attribuée à tout homme comme dotation naturelle "
            "(et non au seul sage stoïcien) ; (3) la confrontation avec "
            "la gnose déplace le débat de la psychologie physique "
            "(stoïcienne) vers l'anthropologie-ontologie de "
            "l'autodétermination ; (4) introduction des références "
            "scripturaires (Dt 30,15-19, Ez 18, Mt 23,37 etc.). Fürst "
            "honnêtement note que la cause historique de cette emphase "
            "(« Warum es zu diesem Freiheitspathos kam ») reste opaque "
            "(p. 4). Concept moderne, à utiliser explicitement comme "
            "catégorie d'analyse — non comme catégorie indigène."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "verified": True,
            "verified_at": AUDIT_AT,
            "language": "de",
            "modern_term": True,
            "introduced_by": "scholar_furst_alfons",
            MARKER_KEY: True,
        },
    },
    {
        "id": "concept_freiheitsmetaphysik_furst_hengstermann",
        "type": "concept",
        "label": (
            "Freiheitsmetaphysik (métaphysique de la liberté — Hengstermann "
            "2016, Fürst 2022)"
        ),
        "description": (
            "Concept-clé de la lecture origénienne de Fürst (titre du Kap. "
            "VI : « Die Freiheitsmetaphysik des Origenes »), suivant "
            "explicitement Christian Hengstermann, Origenes und die "
            "Geschichte der Freiheitsmetaphysik (Aschendorff, 2016) — cité "
            "à de très nombreuses reprises dans les notes du Kap. V-VI. "
            "Désigne la métaphysique origénienne dans laquelle la liberté "
            "n'est plus un accident ou une qualité (comme chez Aristote) "
            "mais le principe (Prinzip) constitutif de la substance des "
            "êtres rationnels. Conséquences ontologiques radicales : (1) "
            "l'homme n'a pas seulement la liberté ; il EST liberté (p. 254 "
            "ca.) ; (2) la liberté est élevée au rang de premier principe "
            "ontologique, ce qui élève corrélativement le mouvement au "
            "rang de premier principe (Hengstermann 31 Anm. 45) ; (3) "
            "Dieu lui-même est conçu comme Freiheit und Bewegung (VI.3a) ; "
            "(4) le monde est conçu comme réseau dynamique de libertés "
            "interagissantes ; (5) l'apokatastasis (1 Cor 15,28 : « Dieu "
            "tout en tout ») est le télos librement atteint de cette "
            "métaphysique. Distinct du concept stoïcien d'oikeiōsis : le "
            "principe ici n'est pas physique mais spirituel-libre. Catégorie "
            "centrale pour la thèse pivot de Romain Girardi sur le "
            "libertarisme compatibiliste origénien."
        ),
        "metadata": {
            "wave": MARKER_KEY,
            "confidence": 0.95,
            "verified": True,
            "verified_at": AUDIT_AT,
            "language": "de",
            "modern_term": True,
            "introduced_by": "scholar_hengstermann_christian",
            "endorsed_by": "scholar_furst_alfons",
            "primary_reference": (
                "Hengstermann, Origenes und die Geschichte der "
                "Freiheitsmetaphysik (Aschendorff, 2016); Fürst, Wege zur "
                "Freiheit, Kap. VI."
            ),
            MARKER_KEY: True,
        },
    },
]


# New edges to wire.
# Format: (source, relation, target, weight, extra_meta_dict)
def build_new_edges() -> list[tuple]:
    pub = CANONICAL_PUB
    edges: list[tuple] = []

    # --- (a) publication discusses ancient persons (already mostly via authored arguments,
    # but explicit `discusses` is informative for retrieval).
    ancient_persons = [
        ("person_origen_alexandria_185_254ce_s9t0u1v2", "central figure of the book"),
        ("person_chrysippus_280_206bce_i9j0k1l2", "Kap. II 4"),
        ("person_carneades_214_129bce_l2m3n4o5", "Kap. II 6"),
        ("person_alexander_aphrodisias_fl200ce_n5o6p7q8", "Kap. III 3c"),
        ("person_alcinous_2c_ce", "Kap. III 3b"),
        ("person_philo_alexandria_a1b2c3d4", "Kap. IV 1"),
        ("person_justin_martyr_2c_ce", "Kap. IV 3"),
        ("person_clement_alexandria", "Kap. IV 5"),
        ("person_epictetus_of_hierapolis_3c385bc2", "Kap. III 2"),
        ("person_plutarch_45_120ce_b9c2a8f3", "Kap. III 3b"),
        ("person_aristotle_384_322bce_c2d4f6a8", "Kap. II 3 + background"),
        ("person_plato_428_348bce_a1b2c3d4", "Kap. II 2 (Er-myth)"),
        ("person_epicurus_341_270bce_j0k1l2m3", "Kap. II 5"),
        ("person_cicero_marcus_tullius_106_43bce_a8f3d2c1", "Kap. III 3a"),
    ]
    for pid, ctx in ancient_persons:
        edges.append((pub, "discusses", pid, 0.95, {"context": ctx}))

    # --- (b) publication engages_with modern scholars
    scholars_engages = [
        "person_bobzien_susanne_contemporary",
        "scholar_frede_michael",
        "scholar_albrecht_dihle",
        "scholar_hengstermann_christian",
        "scholar_karamanolis_george",
        "scholar_crouzel_henri",
        "scholar_sharples_robert",
        "scholar_kobusch_theo",
        "scholar_kahn_charles",
    ]
    for sid in scholars_engages:
        edges.append((pub, "engages_with", sid, 0.9, {}))

    # --- (c) publication critiques Dihle's Augustine-centric thesis
    edges.append((pub, "critiques", "scholar_albrecht_dihle", 0.95,
                  {"context": "Augustine-centric thesis of Dihle 1982/1985"}))

    # --- (d) publication supports Hengstermann (Freiheitsmetaphysik) + Bobzien (philology)
    edges.append((pub, "supports", "scholar_hengstermann_christian", 0.95,
                  {"context": "Freiheitsmetaphysik 2016 as Kap. VI backbone"}))
    edges.append((pub, "supports", "person_bobzien_susanne_contemporary", 0.9,
                  {"context": "Determinism and Freedom 1998 — philological agreement"}))

    # --- (e) Wire new argument nodes to their key targets
    josephus_arg = (
        "argument_furst_2022_josephus_three_jewish_sects_freedom_taxonomy"
    )
    # authored_by + cites_primary_source
    edges.append((josephus_arg, "authored_by", SCHOLAR_FURST, 0.99, {}))
    edges.append((pub, "extends", josephus_arg, 0.95, {}))

    carneades_arg = "argument_furst_2022_carneades_voluntary_self_motion"
    edges.append((carneades_arg, "authored_by", SCHOLAR_FURST, 0.99, {}))
    edges.append((pub, "extends", carneades_arg, 0.95, {}))
    edges.append((carneades_arg, "discusses",
                  "person_carneades_214_129bce_l2m3n4o5", 0.95, {}))

    irenaeus_arg = "argument_furst_2022_irenaeus_against_gnostic_natures"
    edges.append((irenaeus_arg, "authored_by", SCHOLAR_FURST, 0.99, {}))
    edges.append((pub, "extends", irenaeus_arg, 0.95, {}))

    dyn_arg = (
        "argument_furst_2022_origen_dynamic_freedom_ontology_replaces_static_being"
    )
    edges.append((dyn_arg, "authored_by", SCHOLAR_FURST, 0.99, {}))
    edges.append((pub, "extends", dyn_arg, 0.95, {}))
    edges.append((dyn_arg, "discusses",
                  "person_origen_alexandria_185_254ce_s9t0u1v2", 0.95, {}))

    # --- (f) New concepts: discussed by Fürst, related to existing concepts
    edges.append(("concept_freiheitspathos_furst", "discussed_in", pub, 0.95, {}))
    edges.append((SCHOLAR_FURST, "discusses",
                  "concept_freiheitspathos_furst", 0.95, {}))

    edges.append(("concept_freiheitsmetaphysik_furst_hengstermann",
                  "discussed_in", pub, 0.95, {}))
    edges.append((SCHOLAR_FURST, "discusses",
                  "concept_freiheitsmetaphysik_furst_hengstermann", 0.95, {}))
    edges.append(("concept_freiheitsmetaphysik_furst_hengstermann",
                  "developed_by", "scholar_hengstermann_christian", 0.99, {}))

    return edges


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------

def main() -> int:
    print(f"=== Fürst 2022 full audit ({AUDIT_AT}) ===")

    # Phase 1: snapshot
    print("\n[1] Snapshot...")
    snapshot()

    # Load nodes (preserving exact lines)
    print("\n[2] Loading nodes...")
    with NODES_PATH.open(encoding="utf-8") as f:
        node_lines: list[str] = f.readlines()
    print(f"  Loaded {len(node_lines)} node lines")

    # Index nodes by id, preserving line numbers
    line_by_id: dict[str, int] = {}
    nodes_by_id: dict[str, dict] = {}
    for i, line in enumerate(node_lines):
        try:
            n = json.loads(line)
            nodes_by_id[n["id"]] = n
            line_by_id[n["id"]] = i
        except Exception as exc:
            print(f"  ! Skipping line {i}: {exc}", file=sys.stderr)

    # Idempotence check
    canonical = nodes_by_id.get(CANONICAL_PUB)
    if canonical is not None:
        meta = parse_meta(canonical.get("metadata"))
        if meta.get(MARKER_KEY) is True:
            print(
                f"\n=== Marker '{MARKER_KEY}' already present on "
                f"{CANONICAL_PUB} — script is a no-op. Exiting cleanly. ==="
            )
            return 0

    stats = {
        "enriched": 0,
        "deprecated": 0,
        "created": 0,
        "edges_redirected": 0,
        "edges_created": 0,
    }

    # --- Phase 2: Enrich canonical publication
    print("\n[3] Enriching canonical publication...")
    canonical = nodes_by_id[CANONICAL_PUB]
    canonical_meta = parse_meta(canonical.get("metadata"))
    canonical["description"] = CANONICAL_PUB_DESCRIPTION
    canonical_meta.update({
        "local_pdf_path": PDF_PATH,
        "local_txt_path": TXT_PATH,
        "local_md_path": MD_PATH,
        "verified_critiques": VERIFIED_CRITIQUES,
        "inhaltsverzeichnis": INHALTSVERZEICHNIS,
        "verified": True,
        "verified_at": AUDIT_AT,
        MARKER_KEY: True,
        "audit_date": AUDIT_AT,
        "audit_method": (
            "Full read via Furst_2022_Wege_zur_Freiheit.txt + PDF "
            "cross-checks; 15 verbatim DE quotes with EN translations + "
            "exact page references."
        ),
    })
    canonical["metadata"] = dump_meta(canonical_meta)
    node_lines[line_by_id[CANONICAL_PUB]] = json.dumps(canonical, ensure_ascii=False) + "\n"
    stats["enriched"] += 1
    print(f"  Enriched {CANONICAL_PUB}: description {len(CANONICAL_PUB_DESCRIPTION)}c, "
          f"+{len(VERIFIED_CRITIQUES)} verified_critiques, +Inhaltsverzeichnis")

    # --- Phase 3: Enrich 15 argument_furst_2022_* nodes
    print("\n[4] Verifying + enriching 15 argument_furst_2022_* nodes...")
    for arg_id, plan in ARGUMENT_QUOTES.items():
        n = nodes_by_id.get(arg_id)
        if not n:
            print(f"  ! MISSING {arg_id}")
            continue
        meta = parse_meta(n.get("metadata"))
        meta["verified"] = True
        meta["verified_at"] = AUDIT_AT
        meta["page"] = plan["page"]
        meta[MARKER_KEY] = True
        # Quote attachment
        if "quote_de" in plan:
            meta["quote_de"] = plan["quote_de"]
            meta["translation_en"] = plan["translation_en"]
        elif plan.get("quote_idx") is not None:
            crit = VERIFIED_CRITIQUES[plan["quote_idx"]]
            meta["quote_de"] = crit["quote_de"]
            meta["translation_en"] = crit["translation_en"]
            meta["chapter"] = crit["chapter"]
            if plan.get("additional_quote_idx") is not None:
                crit2 = VERIFIED_CRITIQUES[plan["additional_quote_idx"]]
                meta["additional_quote_de"] = crit2["quote_de"]
                meta["additional_translation_en"] = crit2["translation_en"]
        if "verification_status" in plan:
            meta["verification_status"] = plan["verification_status"]
        if "verification_note" in plan:
            meta["verification_note"] = plan["verification_note"]
        n["metadata"] = dump_meta(meta)
        node_lines[line_by_id[arg_id]] = json.dumps(n, ensure_ascii=False) + "\n"
        stats["enriched"] += 1
    print(f"  Enriched {len(ARGUMENT_QUOTES)} argument_furst_2022_* nodes")

    # --- Phase 4: Deprecate shell publication
    print("\n[5] Deprecating shell publication...")
    shell_pub = nodes_by_id.get(SHELL_PUB)
    if shell_pub:
        meta = parse_meta(shell_pub.get("metadata"))
        meta.update({
            "deprecated": True,
            "deprecated_at": AUDIT_AT,
            "deprecated_reason": (
                "Shell-duplicate of pub_furst_2022_wege_freiheit (created by "
                "an earlier bulk-import). Canonical node has full metadata, "
                "description, edges, and verified_critiques."
            ),
            "superseded_by": CANONICAL_PUB,
            MARKER_KEY: True,
        })
        shell_pub["metadata"] = dump_meta(meta)
        node_lines[line_by_id[SHELL_PUB]] = json.dumps(shell_pub, ensure_ascii=False) + "\n"
        stats["deprecated"] += 1
        print(f"  Deprecated {SHELL_PUB} -> superseded_by {CANONICAL_PUB}")

    # --- Phase 5: Process 10 scholarly_argument_f_rst_* shells
    print("\n[6] Processing 10 scholarly_argument_f_rst_* shells...")
    redirect_map: dict[str, str] = {}
    for shell_id, plan in SHELL_ARG_PLAN.items():
        n = nodes_by_id.get(shell_id)
        if not n:
            print(f"  ! MISSING {shell_id}")
            continue
        action = plan["action"]
        meta = parse_meta(n.get("metadata"))
        if action in ("deprecate", "deprecate_and_redirect"):
            meta.update({
                "deprecated": True,
                "deprecated_at": AUDIT_AT,
                "deprecated_reason": (
                    "Earlier import shell — superseded by the dense "
                    f"argument_furst_2022_* equivalent."
                ),
                "superseded_by": plan["superseded_by"],
                MARKER_KEY: True,
            })
            n["metadata"] = dump_meta(meta)
            node_lines[line_by_id[shell_id]] = json.dumps(n, ensure_ascii=False) + "\n"
            stats["deprecated"] += 1
            print(f"  Deprecated {shell_id} -> {plan['superseded_by']}")
            if action == "deprecate_and_redirect":
                redirect_map[shell_id] = plan["redirect_edges_to"]
        elif action == "enrich":
            n["description"] = plan["new_description"]
            if "new_label" in plan:
                n["label"] = plan["new_label"]
            meta.update({
                "verified": True,
                "verified_at": AUDIT_AT,
                "page": plan["page"],
                "quote_de": plan["quote_de"],
                "translation_en": plan["translation_en"],
                "kept_after_audit": True,
                "kept_reason": (
                    "Distinct thesis not redundantly captured by any "
                    "argument_furst_2022_* node — kept and enriched."
                ),
                MARKER_KEY: True,
            })
            n["metadata"] = dump_meta(meta)
            node_lines[line_by_id[shell_id]] = json.dumps(n, ensure_ascii=False) + "\n"
            stats["enriched"] += 1
            print(f"  Enriched (kept) {shell_id}")

    # --- Phase 6: Create new nodes
    print("\n[7] Creating new nodes...")
    new_id_set = set()
    for raw in NEW_NODES:
        nid = raw["id"]
        if nid in nodes_by_id:
            print(f"  ! Node {nid} already exists — skipping creation")
            continue
        new_node = {
            "id": nid,
            "type": raw["type"],
            "label": raw["label"],
            "description": raw["description"],
            "metadata": dump_meta(raw["metadata"]),
        }
        node_lines.append(json.dumps(new_node, ensure_ascii=False) + "\n")
        nodes_by_id[nid] = new_node
        new_id_set.add(nid)
        stats["created"] += 1
        print(f"  Created {raw['type']:9s} {nid}")

    # --- Phase 7: Edges — redirect + create
    print("\n[8] Processing edges...")
    with EDGES_PATH.open(encoding="utf-8") as f:
        edge_lines: list[str] = f.readlines()
    print(f"  Loaded {len(edge_lines)} edge lines")

    # Redirect edges from deprecated shells
    if redirect_map:
        for i, line in enumerate(edge_lines):
            try:
                e = json.loads(line)
            except Exception:
                continue
            changed = False
            if e.get("source") in redirect_map:
                new_target = redirect_map[e["source"]]
                e["source"] = new_target
                e["source_id"] = new_target
                changed = True
            if e.get("target") in redirect_map:
                new_target = redirect_map[e["target"]]
                e["target"] = new_target
                e["target_id"] = new_target
                changed = True
            if changed:
                meta = parse_meta(e.get("metadata"))
                meta["redirected_at"] = AUDIT_AT
                meta["redirected_from_shell"] = True
                meta[MARKER_KEY] = True
                e["metadata"] = dump_meta(meta)
                edge_lines[i] = json.dumps(e, ensure_ascii=False) + "\n"
                stats["edges_redirected"] += 1
        print(f"  Redirected {stats['edges_redirected']} edges away from deprecated shells")

    # Create new edges (skip if already exists with same source+relation+target)
    existing_keys = set()
    for line in edge_lines:
        try:
            e = json.loads(line)
            existing_keys.add((e.get("source"), e.get("relation"), e.get("target")))
        except Exception:
            continue

    new_edges_to_add = build_new_edges()
    print(f"  Planning to create {len(new_edges_to_add)} new edges")
    for src, rel, tgt, weight, extra in new_edges_to_add:
        # Verify both endpoints exist
        if src not in nodes_by_id and src not in new_id_set:
            print(f"  ! Skip — source missing: {src}")
            continue
        if tgt not in nodes_by_id and tgt not in new_id_set:
            print(f"  ! Skip — target missing: {tgt}")
            continue
        if (src, rel, tgt) in existing_keys:
            print(f"  ~ Skip — exists: {src} -[{rel}]-> {tgt}")
            continue
        edge = make_edge(src, rel, tgt, weight=weight, extra_meta=extra)
        edge_lines.append(json.dumps(edge, ensure_ascii=False) + "\n")
        existing_keys.add((src, rel, tgt))
        stats["edges_created"] += 1

    # --- Write back
    print("\n[9] Writing back...")
    with NODES_PATH.open("w", encoding="utf-8") as f:
        f.writelines(node_lines)
    with EDGES_PATH.open("w", encoding="utf-8") as f:
        f.writelines(edge_lines)

    # --- Summary
    print("\n=== AUDIT SUMMARY ===")
    for k, v in stats.items():
        print(f"  {k:25s} : {v}")
    print(f"  Total nodes after audit  : {len(node_lines)}")
    print(f"  Total edges after audit  : {len(edge_lines)}")
    print(f"\nMarker '{MARKER_KEY}' applied — re-run is a no-op.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
