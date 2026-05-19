"""Create 18 missing scholar nodes and wire `authored_by` edges from their publications.

Context
-------
A KG audit on 2026-05-18 identified 18 publications without `authored_by` edges,
because their author nodes did not exist. This script verifies each scholar's
identity (per the verification log embedded below) and creates the missing
`scholar_<surname>_<initial>` nodes plus the corresponding `authored_by` edges.

Each scholar entry carries:
- ``verified_at``: ISO date of verification
- ``verification_sources``: URLs used to confirm identity

For Tim O'Keefe, who already exists as ``scholar_o_keefe_t``, we only wire the
three orphan O'Keefe publications.

Run modes
---------
- ``python3 scripts/create_missing_scholars_2026_05_18.py`` (dry-run, default)
- ``python3 scripts/create_missing_scholars_2026_05_18.py --commit``
- ``python3 scripts/create_missing_scholars_2026_05_18.py --report-only``

The script is idempotent:
- a scholar node is skipped if its id is already present in ``nodes.jsonl``
- an ``authored_by`` edge is skipped if an equivalent edge (same source/target/relation)
  already exists in ``edges.jsonl``

Before committing, snapshots are written under ``data/kg/snapshots/``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots"

VERIFIED_AT = "2026-05-18"
WAVE = "wave_missing_scholars_2026_05_18"


# ---------------------------------------------------------------------------
# Verified scholar registry
# ---------------------------------------------------------------------------
# Format:
#   key (scholar id) -> {
#       label, given_names, surname, specialty, affiliations,
#       death (optional), description, verification_sources [URLs],
#       publication_ids: [pub ids to wire via authored_by],
#       merge_existing: bool  (True = do not create node, only wire edges)
#   }

SCHOLARS: dict[str, dict[str, Any]] = {
    "scholar_alberti_a": {
        "label": "Antonina Alberti",
        "given_names": "Antonina",
        "surname": "Alberti",
        "specialty": "Ancient philosophy, Aristotelian commentary tradition, Aspasius",
        "affiliations": ["Università degli Studi di Firenze"],
        "description": (
            "Italian historian of ancient philosophy, specialist of the Aristotelian "
            "commentary tradition. Co-edited with R. W. Sharples the first scholarly "
            "volume devoted to Aspasius, *Aspasius: The Earliest Extant Commentary on "
            "Aristotle's Ethics* (Peripatoi 17, Berlin: De Gruyter, 1999), to which "
            "she contributed the chapter 'Il volontario e la scelta in Aspasio' (pp. 107-141)."
        ),
        "verification_sources": [
            "https://philpapers.org/rec/ALBATE",
            "https://www.degruyterbrill.com/document/doi/10.1515/9783110810196/html?lang=en",
            "https://www.degruyterbrill.com/document/doi/10.1515/9783110810196.107/html?lang=en",
        ],
        "publication_ids": [
            "pub_alberti_1999_aspasius",
            "pub_sharples_alberti_1999_aspasius",  # co-edited with Sharples
        ],
        "merge_existing": False,
    },
    "scholar_astolfi_a": {
        "label": "Antonella Astolfi",
        "given_names": "Antonella",
        "surname": "Astolfi",
        "specialty": "Aristotelian tradition, Alexander of Aphrodisias, Late Antiquity philosophy",
        "affiliations": [],
        "description": (
            "Italian historian of ancient philosophy. Has written on Stoic determinism, "
            "Alexander of Aphrodisias' *De fato* and the foundation of human free will, "
            "and on nature and fate in the Aristotelian tradition. Her 2015 study "
            "'Nature and Fate according to the Aristotelian Tradition: Alexander of "
            "Aphrodisia's Exegesis' appeared in *Rivista di Filosofia Neo-Scolastica*."
        ),
        "verification_sources": [
            "https://www.mdpi.com/2077-1444/17/3/312",
            "https://www.researchgate.net/publication/290977364_Il_capitolo_XXII_del_De_fato_di_Alessandro_di_Afrodisia_e_la_questione_del_determinismo",
        ],
        "publication_ids": ["pub_astolfi_2015_alexander_fate"],
        "merge_existing": False,
    },
    "scholar_brass_m": {
        "label": "Marcel Brass",
        "given_names": "Marcel",
        "surname": "Brass",
        "specialty": "Cognitive neuroscience, social cognition, neuroscience of free will and volition",
        "affiliations": [
            "Humboldt-Universität zu Berlin (Einstein Professor, Social Intelligence)",
            "Berlin School of Mind and Brain",
            "Ghent University (2006-2020)",
        ],
        "description": (
            "German social and cognitive neuroscientist. PhD 2000 at the Max Planck "
            "Institute for Psychological Research (LMU München). Research professor at "
            "Ghent (2006-2020), Einstein Professor for 'Social Intelligence' at Humboldt-"
            "Universität zu Berlin since 2020/21. Works on neuronal and cognitive "
            "foundations of action control, intentional action, and free will. Co-author "
            "with Furstenberg and Mele of 'Why neuroscience does not disprove free will' (2019)."
        ),
        "verification_sources": [
            "https://www.einsteinfoundation.de/en/fellows-projects/einstein-fellows-professors/einstein-strategic-professorship/marcel-brass",
            "https://www.researchgate.net/profile/Marcel-Brass",
            "https://www.researchgate.net/publication/332771780_Why_neuroscience_does_not_disprove_free_will",
        ],
        "publication_ids": ["pub_brass_2019_neuroscience_free_will"],
        "merge_existing": False,
    },
    "scholar_comerro_v": {
        "label": "Viviane Comerro",
        "given_names": "Viviane",
        "surname": "Comerro",
        "specialty": "Islamic studies, Qur'anic studies, Hadith, early Islamic theology",
        "affiliations": ["INALCO (Institut National des Langues et Civilisations Orientales), Paris"],
        "description": (
            "Professor of Islamic studies at INALCO, Paris. Works on Qur'anic traditions "
            "and early Islamic theology. Author of *Les traditions sur la composition du "
            "muṣḥaf de 'Uthmān* (Orient-Institut Beirut, 2012). Her 2013 article 'La "
            "défense argumentée du libre arbitre dans la tradition musulmane' (*Revue de "
            "l'histoire des religions* 230/1) analyses early Muslim debates on free will "
            "via Ḥasan al-Baṣrī and 'Umāra b. Wathīma al-Fārisī."
        ),
        "verification_sources": [
            "https://journals.openedition.org/rhr/8059?lang=en",
            "https://shs.cairn.info/revue-de-l-histoire-des-religions-2013-1-page-37?lang=fr",
            "https://iqsaweb.org/tag/viviane-comerro/",
        ],
        "publication_ids": ["pub_comerro_2013_libre_arbitre_islam"],
        "merge_existing": False,
    },
    "scholar_deery_o": {
        "label": "Oisín Deery",
        "given_names": "Oisín",
        "surname": "Deery",
        "specialty": "Free will, moral responsibility, philosophy of mind, compatibilism",
        "affiliations": [
            "Macquarie University (ARC DECRA Research Fellow, Sydney)",
            "York University (Toronto)",
        ],
        "description": (
            "Analytic philosopher of action and mind, working on free will, moral "
            "responsibility, and the natural-kind interpretation of agency. Author of "
            "*Naturally Free Action* (Oxford University Press, 2021) and co-editor with "
            "Paul Russell of *The Philosophy of Free Will: Essential Readings From the "
            "Contemporary Debates*. His 2007 paper 'Extending Compatibilism: Control, "
            "Responsibility, and Blame' argues that moral responsibility refers to two "
            "concepts, not one."
        ),
        "verification_sources": [
            "https://philpeople.org/profiles/oisin-deery/publications",
            "https://global.oup.com/academic/product/naturally-free-action-9780198789796",
            "https://www.oisindeery.com/research",
        ],
        "publication_ids": ["pub_deery_2007_compatibilism"],
        "merge_existing": False,
    },
    "scholar_di_muzio_g": {
        "label": "Gianluca Di Muzio",
        "given_names": "Gianluca",
        "surname": "Di Muzio",
        "specialty": "Aristotelian ethics, philosophy of action, moral responsibility, metaphysics",
        "affiliations": ["Indiana University Northwest, Department of Philosophy"],
        "description": (
            "Italian-American philosopher at Indiana University Northwest. Works on "
            "Aristotle's ethics, action theory, and moral responsibility. His 2008 paper "
            "'Aristotle's Alleged Moral Determinism in the Nicomachean Ethics' (*Journal "
            "of Philosophical Research* 33: 19-32) argues against deterministic readings "
            "of Aristotle's theory of character and action."
        ),
        "verification_sources": [
            "https://www.iun.edu/faculty/gianluca-dimuzio/publications/index.htm",
            "https://www.pdcnet.org/jpr/content/jpr_2008_0033_0019_0032",
            "https://philpapers.org/rec/DIMAAM-2",
        ],
        "publication_ids": ["pub_dimuzio_2008_aristotle_determinism"],
        "merge_existing": False,
    },
    "scholar_dobbin_r": {
        "label": "Robert F. Dobbin",
        "given_names": "Robert F.",
        "surname": "Dobbin",
        "specialty": "Stoic philosophy, Epictetus, ancient Greek philosophy",
        "affiliations": ["Independent scholar (Northern California)"],
        "description": (
            "Classicist born in New York City (1958). PhD in Classics, University of "
            "California Berkeley (1989). Editor and commentator of *Epictetus: Discourses, "
            "Book 1* (Clarendon Press, Oxford, 1998) in the Clarendon Later Ancient "
            "Philosophers series. Translator of *Epictetus: Discourses and Selected "
            "Writings* (Penguin Classics, 2008). Has also published on Plato, Pythagoras, "
            "and Virgil. His 1991 article 'Prohairesis in Epictetus' (*Ancient Philosophy* "
            "11/1: 111-135) argues that Epictetus expands prohairesis beyond Aristotle "
            "into the centre of Stoic moral psychology."
        ),
        "verification_sources": [
            "https://global.oup.com/academic/product/epictetus-discourses-book-1-9780199235995",
            "https://philpapers.org/rec/DOBEDB",
            "https://www.amazon.com/Discourses-Selected-Writings-Penguin-Classics/dp/0140449469",
        ],
        "publication_ids": ["pub_dobbin_1991_prohairesis_epictetus"],
        "merge_existing": False,
    },
    "scholar_gauthier_r_a": {
        "label": "René-Antoine Gauthier",
        "given_names": "René-Antoine",
        "surname": "Gauthier",
        "death": "1999",
        "specialty": "Aristotle, Thomas Aquinas, medieval philosophy, Aristotelian ethics",
        "affiliations": [
            "Ordre des Prêcheurs (Dominican)",
            "Commissio Leonina (editor of Aquinas' Aristotelian commentaries)",
            "Le Saulchoir; L'Arbresle; Santa Sabina; Grottaferrata",
        ],
        "description": (
            "René-Antoine Gauthier O.P. (1913-1999), French Dominican, philologist and "
            "historian of philosophy. Joined the Dominicans in 1933 (Lyon province). "
            "Dissertation on *magnanimitas* (1942, published 1951) at Le Saulchoir. "
            "Co-author with Jean-Yves Jolif of the standard French critical translation "
            "and commentary on Aristotle's *Éthique à Nicomaque* (Louvain, 1958-1959; 2nd "
            "ed. Louvain-Paris, 1970), 4 vols. Editor of Aquinas' Aristotelian "
            "commentaries for the Leonine Edition."
        ),
        "verification_sources": [
            "https://en.wikipedia.org/wiki/Ren%C3%A9-Antoine_Gauthier",
            "https://www.persee.fr/doc/rhr_0035-1423_1961_num_159_2_7642",
            "http://www.commissio-leonina.org/2014/08/choix-historiques-et-jeu-de-la-sagesse/",
        ],
        "publication_ids": ["pub_gauthier_1970_ethique_nicomaque"],
        "merge_existing": False,
    },
    "scholar_haggard_p": {
        "label": "Patrick Haggard",
        "given_names": "Patrick",
        "surname": "Haggard",
        "specialty": "Cognitive neuroscience, voluntary action, sense of agency, neuroscience of will",
        "affiliations": [
            "University College London (UCL)",
            "UCL Institute of Cognitive Neuroscience (Deputy Director, research group leader)",
        ],
        "description": (
            "British cognitive neuroscientist. Professor at UCL Institute of Cognitive "
            "Neuroscience. PhD 1991. His research investigates the brain activity that "
            "precedes voluntary actions and its relation to conscious experience of "
            "intending, deciding, or wanting to act. His 2008 review 'Human volition: "
            "towards a neuroscience of will' (*Nature Reviews Neuroscience* 9: 934-946) "
            "is a foundational reference for the cognitive-neuroscience study of free will."
        ),
        "verification_sources": [
            "https://www.ucl.ac.uk/icn/people/patrick-haggard",
            "https://www.nature.com/articles/nrn2497",
            "https://neurophil-freewill.org/patrick-haggard/",
        ],
        "publication_ids": ["pub_haggard_2008_human_volition"],
        "merge_existing": False,
    },
    "scholar_hardie_w_f_r": {
        "label": "W. F. R. Hardie",
        "given_names": "William Francis Ross",
        "surname": "Hardie",
        "death": "1990-09-30",
        "specialty": "Ancient philosophy, Aristotelian ethics, Plato",
        "affiliations": [
            "Corpus Christi College, Oxford (Fellow 1926; President 1950-1969)",
        ],
        "description": (
            "William Francis Ross 'Frank' Hardie (25 April 1902 - 30 September 1990), "
            "Scottish classicist and philosopher. Fellow of Corpus Christi College, "
            "Oxford from 1926; President 1950-1969. Tutored Isaiah Berlin and Paul Grice. "
            "His major work *Aristotle's Ethical Theory* (Oxford: Clarendon, 1968) is a "
            "landmark study of the *Nicomachean Ethics*. His 1968 *Philosophy* article "
            "'Aristotle and the Freewill Problem' (43/165: 274-278) examines whether "
            "Aristotle's ethics engages with the modern free-will problem."
        ),
        "verification_sources": [
            "https://en.wikipedia.org/wiki/W._F._R._Hardie",
            "https://philpapers.org/rec/HARAET-8",
            "https://archive.org/details/aristotlesethica0000hard",
        ],
        "publication_ids": ["pub_hardie_1968_aristotle_freewill"],
        "merge_existing": False,
    },
    "scholar_merker_a": {
        "label": "Anne Merker",
        "given_names": "Anne",
        "surname": "Merker",
        "specialty": "Ancient Greek philosophy, Plato, Aristotle, action theory, ancient ethics",
        "affiliations": ["Université de Strasbourg, Faculté de philosophie (professor)"],
        "description": (
            "French historian of ancient philosophy, born 1971. Agrégée de philosophie. "
            "Lecturer at Université de Strasbourg 2003, HDR 2012 (ENS Lyon, under Pierre-"
            "Marie Morel), elected professor at Strasbourg in 2014. Specialist of Plato "
            "and Aristotle. Author of *La vision chez Platon et Aristote* (Academia, 2003), "
            "*Une morale pour les mortels* (Les Belles Lettres, 2011; Prix Joseph-Saillet "
            "2013), *Le principe de l'action humaine selon Démosthène et Aristote – "
            "Hairesis, prohairesis* (Les Belles Lettres, 2016). Her 2013 review of "
            "Michael Frede's *A Free Will: Origins of the Notion in Ancient Thought* "
            "engages with Frede's reconstruction."
        ),
        "verification_sources": [
            "https://philo.unistra.fr/personnels/enseignants-chercheurs/anne-merker/",
            "https://www.fondationostadelahi.fr/anne-merker/",
            "https://www.lesbelleslettres.com/contributeur/anne-merker",
        ],
        "publication_ids": ["pub_merker_2013_frede_review"],
        "merge_existing": False,
    },
    "scholar_muller_j": {
        "label": "Jörn Müller",
        "given_names": "Jörn",
        "surname": "Müller",
        "specialty": "Ancient and medieval philosophy, akrasia, weakness of will, Aristotle, Aquinas",
        "affiliations": [
            "Julius-Maximilians-Universität Würzburg, Institut für Philosophie (Ordinarius for Ancient and Medieval Philosophy, since 2014)",
        ],
        "description": (
            "German historian of ancient and medieval philosophy. PhD Bonn 2001 on the "
            "ethics of Albert the Great. Habilitation 2008 at Bonn on weakness of will "
            "from Socrates to Duns Scotus, published as *Willensschwäche in Antike und "
            "Mittelalter. Eine Problemgeschichte von Sokrates bis Johannes Duns Scotus* "
            "(Leuven University Press, 2009). Ordinarius for ancient and medieval "
            "philosophy at the University of Würzburg since March 2014."
        ),
        "verification_sources": [
            "https://www.philosophie.uni-wuerzburg.de/institut/allelehrsthlefrphilosophie/profdrjrnmller1/",
            "https://de.wikipedia.org/wiki/J%C3%B6rn_M%C3%BCller_(Philosoph)",
            "https://lup.be/book/willensschwache-in-antike-und-mittelalter/",
        ],
        "publication_ids": ["pub_muller_2009_willensschwache"],
        "merge_existing": False,
    },
    # ------------------------------------------------------------------
    # Tim O'Keefe — already exists as scholar_o_keefe_t.
    # Only wire the three orphan publications.
    # ------------------------------------------------------------------
    "scholar_o_keefe_t": {
        "label": "Tim O'Keefe",
        "given_names": "Tim",
        "surname": "O'Keefe",
        "specialty": "Ancient philosophy, Epicureanism, Hellenistic ethics",
        "affiliations": ["Georgia State University, Department of Philosophy"],
        "description": (
            "American philosopher specializing in ancient philosophy, particularly "
            "Epicureanism. Author of *Epicurus on Freedom* (Cambridge University Press, "
            "2005), a study of the relation between Epicurean atomism, the clinamen, and "
            "moral responsibility. Also wrote 'The Reductionist and Compatibilist "
            "Argument of Epicurus' On Nature, Book 25' (2002, Brill)."
        ),
        "verification_sources": [
            "https://philpapers.org/s/tim%20o%27keefe",
            "https://www.cambridge.org/core/books/epicurus-on-freedom/",
        ],
        "publication_ids": [
            "pub_okeefe_2009_epicurus_freedom",  # mistitled as 2009; same book as 2005
            "scholarly_work_o_keefe_2002_the_reductionist_and_compatibilist_argum",
            "scholarly_work_o_keefe_2005_epicurus_on_freedom",
        ],
        "merge_existing": True,
    },
    "scholar_rambaux_c": {
        "label": "Claude Rambaux",
        "given_names": "Claude",
        "surname": "Rambaux",
        "specialty": "Latin literature, Tertullian, Lucretius, Epicureanism in Rome",
        "affiliations": [],
        "description": (
            "French latinist specializing in Tertullian and Lucretius. Author of "
            "*Tertullien face aux morales des trois premiers siècles* (Paris: Les Belles "
            "Lettres, 1979), and (in collaboration) of the revised Ernout edition of "
            "Lucretius (1990). His 1993 article 'Lucrèce, DRN II, 216-291 : le clinamen "
            "n'est-il qu'un artifice ?' (*Vita Latina* 130: 28-34) defends the clinamen "
            "against ancient critics. Numerous publications in *Vita Latina*."
        ),
        "verification_sources": [
            "https://www.persee.fr/doc/vita_0042-7306_1993_num_130_1_896",
            "https://isidore.science/a/rambaux_claude",
            "https://www.lesbelleslettres.com/livre/9782251457987/tertullien-face-aux-morales-des-trois-premiers-siecles",
        ],
        "publication_ids": ["pub_rambaux_1993_clinamen"],
        "merge_existing": False,
    },
    "scholar_renard_m": {
        "label": "Maguelone Renard",
        "given_names": "Maguelone",
        "surname": "Renard",
        "specialty": "Augustine, patristics, late ancient philosophy",
        "affiliations": ["Université Paul Valéry – Montpellier 3 (doctoral candidate)"],
        "description": (
            "French doctoral researcher in patristics and late ancient philosophy, "
            "Université Paul Valéry – Montpellier 3, working on Augustine. Co-director "
            "of *Du Jésus des Écritures au Christ des théologiens: Pères de l'Église, "
            "lecteurs de la vie de Jésus* (2022). Her 2020 article 'De la fatalité "
            "païenne à la Providence chrétienne, Aug., Civ. V, 8-10' (*Vita Latina* 200: "
            "25-42) studies Augustine's reading of the ancient Stoic / Neo-Academic "
            "debate on destiny."
        ),
        "verification_sources": [
            "https://www.persee.fr/doc/vita_0042-7306_2020_num_200_1_2027",
            "https://athar.persee.fr/authority/1731294",
            "https://www.idref.fr/269217991",
        ],
        "publication_ids": ["pub_renard_2020_fatalite_providence"],
        "merge_existing": False,
    },
    "scholar_ryle_g": {
        "label": "Gilbert Ryle",
        "given_names": "Gilbert",
        "surname": "Ryle",
        "death": "1976-10-06",
        "specialty": "Philosophy of mind, ordinary language philosophy, Plato, Aristotle",
        "affiliations": [
            "Magdalen College and Christ Church, Oxford",
            "Waynflete Professor of Metaphysical Philosophy, Oxford (1945-1968)",
            "Editor, *Mind*",
        ],
        "description": (
            "Gilbert Ryle (1900-1976), British philosopher, Waynflete Professor of "
            "Metaphysical Philosophy at Oxford (1945-1968), editor of *Mind*. Principal "
            "author of *The Concept of Mind* (Hutchinson, 1949), in which he attacks "
            "Cartesian dualism (the 'ghost in the machine') and the existence of a mental "
            "faculty of the will. Cited by Frede as influential in changing modern "
            "scholarly opinion about ancient free will."
        ),
        "verification_sources": [
            "https://en.wikipedia.org/wiki/Gilbert_Ryle",
            "https://en.wikipedia.org/wiki/The_Concept_of_Mind",
            "https://plato.stanford.edu/entries/ryle/",
        ],
        "publication_ids": ["pub_ryle_1949_concept_mind"],
        "merge_existing": False,
    },
    "scholar_schockenhoff_e": {
        "label": "Eberhard Schockenhoff",
        "given_names": "Eberhard",
        "surname": "Schockenhoff",
        "death": "2020-07-18",
        "specialty": "Catholic moral theology, natural law, bioethics, patristics (Origen)",
        "affiliations": [
            "Albert-Ludwigs-Universität Freiburg (Professor of Moral Theology, 1994-2020)",
            "German Ethics Council (Deputy Chairman from 2008)",
        ],
        "description": (
            "Eberhard Schockenhoff (1953-2020), German Catholic moral theologian and "
            "priest. Habilitation 1989 at Tübingen under Walter Kasper. Habilitationsschrift "
            "published as *Zum Fest der Freiheit. Theologie des christlichen Handelns bei "
            "Origenes* (Mainz: Grünewald, 1990). From 1994 Professor of Moral Theology at "
            "Albert-Ludwigs-Universität Freiburg. Member of the German Ethics Council "
            "from 2001, Deputy Chairman from 2008."
        ),
        "verification_sources": [
            "https://de.wikipedia.org/wiki/Eberhard_Schockenhoff",
            "https://uni-tuebingen.de/fakultaeten/katholisch-theologische-fakultaet/fakultaet/aktuellesnews/artikel/article/nachruf-auf-eberhard-schockenhoff/",
            "https://shs.cairn.info/journal-revue-d-ethique-et-de-theologie-morale-2021-3-page-89?lang=en",
        ],
        "publication_ids": ["pub_schockenhoff_1990_fest_freiheit"],
        "merge_existing": False,
    },
    "scholar_williams_b": {
        "label": "Bernard Williams",
        "given_names": "Bernard",
        "surname": "Williams",
        "death": "2003-06-10",
        "specialty": "Moral philosophy, ancient philosophy, ethics, philosophy of mind",
        "affiliations": [
            "University of California, Berkeley (Mills Professor of Philosophy)",
            "University of Oxford (White's Professor of Moral Philosophy)",
            "University of Cambridge (Knightbridge Professor of Philosophy)",
        ],
        "description": (
            "Sir Bernard Arthur Owen Williams (1929-2003), British moral philosopher. "
            "Author of *Shame and Necessity* (Sather Classical Lectures 57, University of "
            "California Press, 1993), based on his 1989 Sather Lectures at Berkeley, "
            "which argues that the absence of 'will' from Homer's epics should be "
            "applauded rather than regretted, and that modern ethics still relies on "
            "concepts inherited from archaic Greek poets and tragedians."
        ),
        "verification_sources": [
            "https://philpapers.org/rec/WILSAN-5",
            "https://bmcr.brynmawr.edu/1993/1993.04.20/",
            "https://www.cambridge.org/core/journals/classical-review/article/abs/shame-and-necessity-bernard-williams-shame-and-necessity-sather-classical-lectures-57-berkeley-los-angeles-oxford-university-of-california-press-1993-185025/DBE8F7CACF2B158CCF9C62AE23746E77",
        ],
        "publication_ids": ["pub_williams_1993_shame_necessity"],
        "merge_existing": False,
    },
}


# Publications we intentionally do NOT wire (unverifiable). For this run: none.
UNVERIFIABLE: list[str] = []


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        for rec in records:
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(path)


def _snapshot() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    sub = SNAPSHOT_DIR / f"missing_scholars_{stamp}"
    sub.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, sub / "nodes.jsonl")
    shutil.copy2(EDGES_PATH, sub / "edges.jsonl")
    return sub


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _build_scholar_node(scholar_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    now = dt.datetime.utcnow().isoformat() + "+00:00"
    metadata: dict[str, Any] = {
        "role": "scholar",
        "period": "Modern",
        "surname": payload["surname"],
        "specialty": payload["specialty"],
        "confidence": 0.99,
        "given_names": payload["given_names"],
        "affiliations": payload["affiliations"],
        "verified_at": VERIFIED_AT,
        "verification_sources": payload["verification_sources"],
        "wave": WAVE,
        "source_track": "web_research",
        "merge_into_existing_node": False,
    }
    if "death" in payload:
        metadata["death"] = payload["death"]

    return {
        "alternative_names": "[]",
        "created_at": now,
        "description": payload["description"],
        "id": scholar_id,
        "label": payload["label"],
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "node_id": scholar_id,
        "period": "Modern",
        "role": "scholar",
        "school": None,
        "type": "person",
        "updated_at": now,
    }


def _build_authored_by_edge(pub_id: str, scholar_id: str) -> dict[str, Any]:
    now = dt.datetime.utcnow().isoformat() + "+00:00"
    return {
        "created_at": now,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(
            {
                "confidence": 0.99,
                "wave": WAVE,
                "verified_at": VERIFIED_AT,
            },
            ensure_ascii=False,
        ),
        "relation": "authored_by",
        "source": pub_id,
        "source_id": pub_id,
        "target": scholar_id,
        "target_id": scholar_id,
        "weight": 0.99,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist changes to nodes.jsonl / edges.jsonl (default is dry-run).",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only print the resolution report, do not touch files.",
    )
    args = parser.parse_args()

    nodes = _read_jsonl(NODES_PATH)
    edges = _read_jsonl(EDGES_PATH)

    nodes_by_id = {n["id"]: n for n in nodes}
    edge_key = lambda e: (e.get("source"), e.get("relation"), e.get("target"))
    existing_edge_keys = {edge_key(e) for e in edges}

    new_nodes: list[dict[str, Any]] = []
    new_edges: list[dict[str, Any]] = []
    skipped_existing_scholars: list[str] = []
    skipped_existing_edges: list[tuple[str, str]] = []
    missing_pubs: list[tuple[str, str]] = []

    wired_per_scholar: dict[str, list[str]] = {}
    report_rows: list[dict[str, Any]] = []

    for scholar_id, payload in SCHOLARS.items():
        wired_per_scholar.setdefault(scholar_id, [])
        # Node
        if scholar_id in nodes_by_id:
            skipped_existing_scholars.append(scholar_id)
        elif payload.get("merge_existing"):
            print(
                f"  ! Scholar {scholar_id} marked as merge_existing but not present in nodes.jsonl",
                file=sys.stderr,
            )
            return 2
        else:
            new_nodes.append(_build_scholar_node(scholar_id, payload))

        # Edges
        for pub_id in payload["publication_ids"]:
            if pub_id not in nodes_by_id:
                missing_pubs.append((scholar_id, pub_id))
                continue
            key = (pub_id, "authored_by", scholar_id)
            if key in existing_edge_keys:
                skipped_existing_edges.append((pub_id, scholar_id))
                continue
            edge = _build_authored_by_edge(pub_id, scholar_id)
            new_edges.append(edge)
            existing_edge_keys.add(key)
            wired_per_scholar[scholar_id].append(pub_id)

        report_rows.append(
            {
                "scholar_id": scholar_id,
                "label": payload["label"],
                "publication_ids": payload["publication_ids"],
                "new_node": scholar_id not in nodes_by_id,
                "wired_publications": wired_per_scholar[scholar_id],
                "verification_sources": payload["verification_sources"],
            }
        )

    # -- Report ---------------------------------------------------------------
    print("=" * 80)
    print(f"create_missing_scholars_2026_05_18  (mode={'COMMIT' if args.commit else 'DRY-RUN'})")
    print("=" * 80)
    for row in report_rows:
        print(
            f"\n[{row['scholar_id']}] {row['label']}\n"
            f"  publications targeted : {len(row['publication_ids'])}\n"
            f"  will create node      : {row['new_node']}\n"
            f"  will wire authored_by : {len(row['wired_publications'])}\n"
            f"  sources               : {len(row['verification_sources'])} URLs"
        )

    print("\n--- Summary ---")
    print(f"new scholar nodes        : {len(new_nodes)}")
    print(f"existing scholars kept   : {len(skipped_existing_scholars)} -> {skipped_existing_scholars}")
    print(f"new authored_by edges    : {len(new_edges)}")
    print(f"existing edges kept      : {len(skipped_existing_edges)}")
    if missing_pubs:
        print(f"!!! missing publications : {missing_pubs}")
    if UNVERIFIABLE:
        print(f"unverifiable (skipped)   : {UNVERIFIABLE}")

    if args.report_only:
        return 0

    if not args.commit:
        print("\n(dry-run) no files modified. Re-run with --commit to persist.")
        return 0

    if missing_pubs:
        print("\nRefusing to commit while target publications are missing.", file=sys.stderr)
        return 1

    snap = _snapshot()
    print(f"\nSnapshot written to {snap.relative_to(ROOT)}")

    nodes.extend(new_nodes)
    edges.extend(new_edges)
    _write_jsonl(NODES_PATH, nodes)
    _write_jsonl(EDGES_PATH, edges)

    print(
        f"Committed: +{len(new_nodes)} scholar nodes, +{len(new_edges)} authored_by edges."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
