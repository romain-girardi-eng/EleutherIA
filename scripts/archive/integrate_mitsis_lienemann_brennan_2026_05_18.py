#!/usr/bin/env python3
"""Integration des sources critiques Mitsis 2021 / Lienemann 2012 / Brennan 2005 — 2026-05-18

Contexte : débat Bobzien-Frede sur l'origine du libre arbitre antique. Romain a
demandé d'intégrer trois voix tierces critiques :

1. **Mitsis 2021** ("Did Ancient Greek Philosophers Have A Concept of Free Will?",
   in *The Poetry in Philosophy*, Parnassos Press) — critique méthodologique
   anti-Frede. Citations verbatim extraites via Blackson 2025 (PDF intégral
   dans /tmp/blackson_2025.txt).

2. **Lienemann 2012** (review de Frede 2011 dans *BPJAM* 15, John Benjamins) —
   seule review longue (15 p.) en langue germanique. Texte intégral derrière
   paywall ; on insère le node-shell avec abstract bibliographique.

3. **Brennan 2005** (*The Stoic Life*, OUP) — Part IV (chap. 14-17, p. 233-305)
   sur fate/responsabilité/évolution-de-la-volonté. PDF intégral disponible
   (data/literature_acquisition/brennan_2005_stoic_life.pdf). Citations
   verbatim extraites du chap. 17 "The Evolution of the Will".

Le script :
- Crée nodes Mitsis (person + publication) — n'existent pas
- Crée nodes Lienemann (person + publication) — n'existent pas
- ENRICHIT le node Brennan 2005 existant (`scholarly_work_brennan_2005_stoic_life`)
  avec sa thèse Part IV + 3 citations verbatim
- Wire les edges critiques vers Frede 2011 / Bobzien 1998 / Bobzien 2001

Idempotent : marker `mitsis_lienemann_brennan_integration_2026_05_18` posé sur
chaque node créé/enrichi + edge metadata.

Snapshot avant mutation. Préservation byte-exacte du formatage des autres
nodes (seuls les nodes touchés sont re-sérialisés).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-mitsis-lienemann-brennan"

WAVE_TAG = "mitsis_lienemann_brennan_integration_2026_05_18"
NOW = datetime.now(UTC).isoformat(sep=" ")

# Canonical existing IDs (verified by inspection).
ID_FREDE_2011 = "pub_frede_2011_free_will"
ID_BOBZIEN_1998 = "pub_bobzien_1998_inadvertent"
ID_BOBZIEN_2001_BOOK = "scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso"
ID_BRENNAN_2005_BOOK = "scholarly_work_brennan_2005_stoic_life"
ID_BRENNAN_PERSON = "scholar_brennan_tad"

# New IDs to create.
ID_MITSIS_PERSON = "scholar_mitsis_phillip"
ID_MITSIS_2021 = "pub_mitsis_2021_improper_questions"
ID_LIENEMANN_PERSON = "scholar_lienemann_beatrice"
ID_LIENEMANN_2012 = "pub_lienemann_2012_review_frede"


# ===== NEW NODES =====

NEW_NODES: list[dict[str, Any]] = [
    {
        "id": ID_MITSIS_PERSON,
        "node_id": ID_MITSIS_PERSON,
        "type": "person",
        "label": "Phillip Mitsis",
        "description": (
            "Phillip Mitsis (b. 1953), helléniste américain, A. S. Onassis "
            "Professor of Hellenic Culture and Civilization à New York "
            "University. Spécialiste de l'éthique hellénistique (Épicure "
            "en particulier), de la réception de l'antiquité grecque dans "
            "la philosophie moderne et du débat antique-moderne sur le "
            "libre arbitre. Critique méthodologique de Frede 2011 dans "
            "son chapitre de 2021 « Did Ancient Greek Philosophers Have A "
            "Concept of Free Will? (and Other Improper Questions) »."
        ),
        "period": "Modern",
        "role": "scholar",
        "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps(
            {
                "role": "scholar",
                "period": "Modern",
                "surname": "Mitsis",
                "given_names": "Phillip",
                "specialty": (
                    "Hellenistic philosophy, Epicurus, ancient ethics, "
                    "ancient-modern continuity"
                ),
                "affiliations": [
                    "New York University (A. S. Onassis Professor)",
                    "Academy of Athens (foreign member)",
                ],
                "key_works": [
                    "Epicurus' Ethical Theory (Cornell, 1988)",
                    "How Modern Is Freedom of the Will? (in Lezra & Blake eds., Palgrave 2016)",
                    "Did Ancient Greek Philosophers Have A Concept of Free Will? (Parnassos 2021)",
                    "Le libre arbitre est-il moderne? (Brepols 2021, Appendice II)",
                ],
                "wave": WAVE_TAG,
            },
            ensure_ascii=False,
        ),
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": ID_MITSIS_2021,
        "node_id": ID_MITSIS_2021,
        "type": "publication",
        "label": (
            "Mitsis 2021 — Did Ancient Greek Philosophers Have A Concept "
            "of Free Will? (and Other Improper Questions)"
        ),
        "description": (
            "Chapitre 16 de Phillip Mitsis & Heather L. Reid (eds.), *The "
            "Poetry in Philosophy. Essays in Honor of Christos C. "
            "Evangeliou*, Sioux City: Parnassos Press / Fonte Aretusa, "
            "2021, p. 243-282. DOI 10.2307/j.ctv1ks0b70.16. Critique "
            "méthodologique de Michael Frede, *A Free Will* (2011). Trois "
            "griefs centraux selon le compte rendu de Blackson 2025 : "
            "(1) Frede présuppose sans argument que les concepts sont "
            "des « particuliers mentaux ou entités quasi-linguistiques » "
            "plutôt que des « capacités propres aux agents cognitifs » "
            "(p. 266) ; (2) Frede emploie une notion de « sheer volition » "
            "que Mitsis identifie à Frede (à tort selon Blackson — c'est "
            "plutôt la position de Dihle, p. 264) ; (3) Frede opère selon "
            "une « notion quasi-hégélienne du développement interne "
            "hermétique des idées philosophiques vers une fin "
            "particulière » que Mitsis juge « méthodologiquement "
            "douteuse » (p. 266). Existe aussi en version française "
            "comme Appendice II de *Natura aut voluntas? Recherches sur "
            "la pensée politique et éthique hellénistique et romaine et "
            "son influence* (Brepols 2021, ISBN 9782503589459), sous le "
            "titre « Le libre arbitre est-il moderne ? »."
        ),
        "period": "Modern",
        "role": None,
        "school": None,
        "alternative_names": json.dumps(
            [
                "Did Ancient Greek Philosophers Have A Concept of Free Will?",
                "Improper Questions",
                "Le libre arbitre est-il moderne?",
                "Mitsis 2021 anti-Frede",
            ],
            ensure_ascii=False,
        ),
        "metadata": json.dumps(
            {
                "type": "book_chapter",
                "year": 2021,
                "author": "Phillip Mitsis",
                "title": (
                    "Did Ancient Greek Philosophers Have A Concept of "
                    "Free Will? (and Other Improper Questions)"
                ),
                "editors": ["Phillip Mitsis", "Heather L. Reid"],
                "book_title": (
                    "The Poetry in Philosophy. Essays in Honor of "
                    "Christos C. Evangeliou"
                ),
                "publisher": "Parnassos Press / Fonte Aretusa",
                "publisher_location": "Sioux City, Iowa",
                "pages": "243-282",
                "isbn": "9781942495413",
                "doi": "10.2307/j.ctv1ks0b70.16",
                "language": "en",
                "bibtex_key": "mitsis-2021-improper-questions",
                "french_companion": (
                    "Mitsis 2021 (Brepols ISBN 9782503589459) — "
                    "Appendice II « Le libre arbitre est-il moderne? »"
                ),
                "ancestor_english": (
                    "Mitsis 2016 'How Modern Is Freedom of the Will?' "
                    "in Lezra & Blake (eds.) *Lucretius and Modernity*, "
                    "Palgrave Macmillan, p. 105-123, DOI 10.1007/"
                    "978-1-137-56657-7_7"
                ),
                "engages_with_frede": True,
                "critique_summary": (
                    "Three methodological objections: (1) Frede's "
                    "implicit Fodorian conception of 'concepts as mental "
                    "particulars'; (2) misattribution to Frede of a "
                    "'sheer volition' view (which Blackson contests); "
                    "(3) Frede's 'quasi-Hegelian' teleological "
                    "narrative of conceptual development"
                ),
                "verified_critiques": [
                    {
                        "page": "266",
                        "thesis": "Frede relies on unargued Fodorian assumption about concepts",
                        "quote_via_blackson": (
                            "assumption that concepts are some kind of "
                            "mental particulars or word-like entities "
                            "in a language of thought, rather than, "
                            "say, as Dummett and others have argued, "
                            "abilities peculiar to cognitive agents"
                        ),
                        "source_verification": (
                            "Cited verbatim by Blackson 2025 (Rhizomata) "
                            "p. 84 n. 9 — PDF dans "
                            "data/literature_acquisition/blackson_2025_"
                            "rhizomata.pdf l. 199-201"
                        ),
                    },
                    {
                        "page": "264",
                        "thesis": "Frede defends a 'sheer volition' view of free will",
                        "quote_via_blackson": (
                            "Frede's 'sheer volition' view"
                        ),
                        "source_verification": (
                            "Cited Blackson 2025 p. 84 n. 9, l. 203-204. "
                            "Blackson conteste cette attribution : "
                            "« Dihle seems to have this sort of view, "
                            "but Frede does not »"
                        ),
                    },
                    {
                        "page": "266",
                        "thesis": "Frede employs a quasi-Hegelian teleological framework",
                        "quote_via_blackson": (
                            "quasi-Hegelian notion of the internal "
                            "hermetic development of philosophical "
                            "ideas toward a particular end [...] "
                            "questionable methodologically"
                        ),
                        "source_verification": (
                            "Cited Blackson 2025 p. ~90 n. 23, l. 417-419"
                        ),
                    },
                ],
                "acquisition_status": (
                    "Citations via Blackson 2025 (vérifiées). PDF "
                    "Mitsis 2021 non téléchargé (JSTOR reCAPTCHA + "
                    "ResearchGate Cloudflare). Acquisition manuelle "
                    "possible : https://www.jstor.org/stable/"
                    "j.ctv1ks0b70.16 (OA chapter, login non requis "
                    "depuis Safari)."
                ),
                "wave": WAVE_TAG,
            },
            ensure_ascii=False,
        ),
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": ID_LIENEMANN_PERSON,
        "node_id": ID_LIENEMANN_PERSON,
        "type": "person",
        "label": "Béatrice Lienemann",
        "description": (
            "Béatrice Lienemann, philosophe allemande, ancienne titulaire "
            "à Goethe-Universität Frankfurt, désormais à FAU "
            "Erlangen-Nürnberg (chaire de philosophie théorique). "
            "Spécialiste de la philosophie ancienne (Aristote, "
            "Néoplatonisme) et de la théorie de l'action. Auteure de la "
            "seule review longue (15 p.) de Frede 2011 en langue "
            "germanique, parue dans *Bochumer Philosophisches Jahrbuch "
            "für Antike und Mittelalter* 15 (2012)."
        ),
        "period": "Modern",
        "role": "scholar",
        "school": None,
        "alternative_names": json.dumps([], ensure_ascii=False),
        "metadata": json.dumps(
            {
                "role": "scholar",
                "period": "Modern",
                "surname": "Lienemann",
                "given_names": "Béatrice",
                "specialty": (
                    "Ancient philosophy (Aristotle, Neoplatonism), "
                    "philosophy of action, free will"
                ),
                "affiliations": [
                    "Goethe-Universität Frankfurt (former)",
                    "FAU Erlangen-Nürnberg (current, philosophie théorique)",
                ],
                "key_works": [
                    "Die Argumente für die Existenz Gottes in Anselms 'Proslogion' (Berlin: De Gruyter, 2009)",
                    "Review of Frede 2011 (BPJAM 15, 2012, p. 252-266)",
                ],
                "philpapers_url": "https://philpeople.org/profiles/beatrice-lienemann",
                "wave": WAVE_TAG,
            },
            ensure_ascii=False,
        ),
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": ID_LIENEMANN_2012,
        "node_id": ID_LIENEMANN_2012,
        "type": "publication",
        "label": (
            "Lienemann 2012 — Review of M. Frede, A Free Will (Sather, "
            "2011) — BPJAM 15"
        ),
        "description": (
            "Béatrice Lienemann, recension critique de Michael Frede, "
            "*A Free Will. Origins of the Notion in Ancient Thought* "
            "(University of California Press, 2011), parue dans "
            "*Bochumer Philosophisches Jahrbuch für Antike und "
            "Mittelalter* 15/1 (2012), p. 252-266. DOI 10.1075/bpjam.15."
            "09lie. Éditeur John Benjamins. Seule review longue (15 p.) "
            "de Frede 2011 en langue germanique. Texte intégral derrière "
            "paywall John Benjamins (£15). Contenu non extrait à ce jour "
            "— node créé en shell bibliographique, à enrichir après "
            "acquisition manuelle (tiré-à-part à demander à l'auteure : "
            "beatrice.lienemann@fau.de)."
        ),
        "period": "Modern",
        "role": None,
        "school": None,
        "alternative_names": json.dumps(
            [
                "Lienemann 2012 BPJAM",
                "Lienemann review Frede",
            ],
            ensure_ascii=False,
        ),
        "metadata": json.dumps(
            {
                "type": "review_article",
                "year": 2012,
                "author": "Béatrice Lienemann",
                "title": (
                    "Michael Frede (2011): A Free Will. Origins of the "
                    "Notion in Ancient Thought"
                ),
                "journal": "Bochumer Philosophisches Jahrbuch für Antike und Mittelalter",
                "journal_short": "BPJAM",
                "volume": 15,
                "number": 1,
                "pages": "252-266",
                "publisher": "John Benjamins",
                "doi": "10.1075/bpjam.15.09lie",
                "language": "de",
                "bibtex_key": "lienemann-2012-review-frede",
                "engages_with_frede": True,
                "acquisition_status": (
                    "Texte intégral non acquis — paywall John Benjamins, "
                    "aucun mirror OA (HAL, BORIS Bern, ZORA Zürich, "
                    "DepositOnce Berlin, philarchive testés). Référence "
                    "bibliographique vérifiée via Crossref + PhilPapers "
                    "(LIEROF). Acquisition recommandée : email à "
                    "l'auteure pour tiré-à-part."
                ),
                "verified_critiques": [],
                "wave": WAVE_TAG,
                "needs_text_acquisition": True,
            },
            ensure_ascii=False,
        ),
        "created_at": NOW,
        "updated_at": NOW,
    },
]


# ===== ENRICHMENTS TO EXISTING NODES =====
# Each entry: { id: ..., description_append: str, metadata_updates: dict }

ENRICHMENTS: list[dict[str, Any]] = [
    {
        "id": ID_BRENNAN_2005_BOOK,
        "description": (
            "Tad Brennan, *The Stoic Life: Emotions, Duties, and Fate*, "
            "Oxford: Clarendon Press / OUP, 2005 (paperback 2007), "
            "ISBN 9780199217052. Monographie de référence sur l'éthique "
            "stoïcienne, structurée en quatre parties (Introduction, "
            "Psychology, Ethics, Fate). **Part IV (chap. 14-17, "
            "p. 233-305) — « Fate »** : analyse systématique du "
            "compatibilisme chrysippéen et de l'évolution antique-moderne "
            "des conceptions de responsabilité morale, en dialogue "
            "explicite et nourri avec Bobzien 1998. Brennan reconnaît "
            "une dette massive (« I could not have written this part, "
            "nor would I have attempted it, without the immense "
            "assistance provided by Bobzien (1998a). She has brought "
            "order, clarity, rigor, and understanding, to a topic that "
            "has long been a sink of ignorance and confusion », p. 305 "
            "Further Reading) mais **diverge sur le verdict** : « Here "
            "I rely on the reconstruction of Chrysippus' compatibilism "
            "in Bobzien (1998a), though I diverge from her assessment "
            "and verdict » (p. 268 n. 11). Le chap. 17 « The Evolution "
            "of the Will » (p. 288-305) propose une **troisième voie "
            "explicite contre Bobzien** : la différence ancien/moderne "
            "n'est PAS un contraste entre autonomie (ancien) et "
            "capacité d'agir autrement (moderne), comme Bobzien le "
            "soutient. Brennan : « I think Bobzien is right to draw "
            "our attention to this difference in conceptions of moral "
            "responsibility, but I also think that a slight shift of "
            "emphasis can help us see how this historical difference "
            "arose. […] People were always interested in the ability "
            "to do otherwise—just as much in antiquity as today. And "
            "people have always been interested in the agent's autonomy, "
            "and still are today. **What has changed, instead, is the "
            "conception of the agent** with respect to whom these other "
            "distinctions are made » (p. 292). Sa thèse-pivot : "
            "shrinkage of the self — de la « thick ball of psychology » "
            "antique au « point-like ego/will » moderne — héritage "
            "néoplatonicien (Platon → Plotin → chrétiens). Brennan "
            "anticipe partiellement Frede 2011 sur Épictète tout en le "
            "critiquant implicitement : la lecture « libertaire » "
            "d'Épictète repose sur une « misunderstanding of Epictetus "
            "[that] became influential » (chap. 17, p. 296), Épictète "
            "lui-même restant fidèle au déterminisme chrysippéen. "
            "Texte intégral PDF acquis dans "
            "data/literature_acquisition/brennan_2005_stoic_life.pdf."
        ),
        "metadata_updates": {
            "url": "https://archive.org/details/Stoic-Life",
            "year": 2005,
            "publisher": "Oxford: Clarendon Press / OUP",
            "isbn": "9780199217052",
            "isbn_paperback": "9780199217052",
            "isbn_hardback": "9780199256266",
            "pages": "353",
            "language": "en",
            "key_chapter_for_free_will_debate": "Part IV (ch. 14-17, p. 233-305)",
            "part_iv_chapters": {
                "14": "God and Fate (p. 235-241)",
                "15": "Necessity and Responsibility (p. 242-269)",
                "16": "The Lazy Argument (p. 270-287)",
                "17": "The Evolution of the Will (p. 288-305)",
            },
            "engages_with_bobzien_1998": True,
            "engages_with_frede_2011": (
                "Implicitement — Brennan 2005 antérieur à Frede 2011 "
                "mais critique la lecture libertaire d'Épictète qui "
                "deviendra le pivot du livre de Frede"
            ),
            "central_brennan_thesis_part_iv": (
                "Anti-Bobzien on framing : la différence ancien/moderne "
                "n'est pas autonomie vs ability-to-do-otherwise mais "
                "shrinkage of the self (thick psychological ball → "
                "point-like will/ego). Héritage néoplatonicien et "
                "chrétien plutôt que stoïco-péripatéticien"
            ),
            "verified_brennan_citations_on_bobzien": [
                {
                    "location": "p. 305 (Further Reading Part IV, head note)",
                    "thesis": "Massive intellectual debt to Bobzien 1998",
                    "quote": (
                        "I could not have written this part, nor would I have "
                        "attempted it, without the immense assistance provided "
                        "by Bobzien (1998a). She has brought order, clarity, "
                        "rigor, and understanding, to a topic that has long "
                        "been a sink of ignorance and confusion, and I am "
                        "indebted both to her book and to our conversations "
                        "for much of what I say here"
                    ),
                },
                {
                    "location": "p. 268 n. 11 (chap. 15 Necessity and Responsibility)",
                    "thesis": "Divergence from Bobzien on verdict re Chrysippus' compatibilism",
                    "quote": (
                        "Here I rely on the reconstruction of Chrysippus' "
                        "compatibilism in Bobzien (1998a), though I diverge "
                        "from her assessment and verdict. Her book is the "
                        "best source for a full discussion of this material; "
                        "for a slightly more tractable presentation of her "
                        "findings, along with fuller accounts of my "
                        "criticisms of Chrysippus, see Brennan (2001)"
                    ),
                },
                {
                    "location": "p. 292 (chap. 17 The Evolution of the Will)",
                    "thesis": "Anti-Bobzien on framing of ancient/modern divide — third way",
                    "quote": (
                        "I think Bobzien is right to draw our attention to "
                        "this difference in conceptions of moral "
                        "responsibility, but I also think that a slight "
                        "shift of emphasis can help us see how this "
                        "historical difference arose. […] People were always "
                        "interested in the ability to do otherwise—just as "
                        "much in antiquity as today. And people have always "
                        "been interested in the agent's autonomy, and still "
                        "are today. What has changed, instead, is the "
                        "conception of the agent with respect to whom these "
                        "other distinctions are made"
                    ),
                },
                {
                    "location": "p. 296 (chap. 17, on Epictetus)",
                    "thesis": (
                        "Anti-Frede implicit : libertarian reading of "
                        "Epictetus is a 'misunderstanding that became "
                        "influential'"
                    ),
                    "quote": (
                        "When we read Epictetus, it may seem that a change "
                        "has occurred; and here the mere appearance of a "
                        "change in time leads to a real change, as a "
                        "misunderstanding of Epictetus became influential. "
                        "Chrysippus is quite clear about the fact that "
                        "impressions come from outside, that they are not "
                        "up to the agent, and that they are not desires. "
                        "We do not have a desire unless and until we assent "
                        "to an impression"
                    ),
                },
            ],
            "local_pdf_path": (
                "data/literature_acquisition/brennan_2005_stoic_life.pdf"
            ),
            "wave": WAVE_TAG,
        },
    },
    {
        "id": ID_BRENNAN_PERSON,
        "description": (
            "Tad Brennan, philosophe américain, Susan Linn Sage Professor "
            "of Philosophy and Classics à Cornell University. Spécialiste "
            "de l'éthique stoïcienne, de la théorie stoïcienne de "
            "l'action, des émotions et du compatibilisme antique. Auteur "
            "de *The Stoic Life: Emotions, Duties, and Fate* (Oxford "
            "2005), monographie de référence dont la Part IV constitue "
            "une troisième voie explicite dans le débat Bobzien-Frede "
            "sur l'origine du libre arbitre. Brennan reconnaît la dette "
            "massive envers Bobzien 1998 sur la reconstruction du "
            "compatibilisme chrysippéen mais diverge sur le verdict "
            "philosophique et propose, dans le chap. 17 « The Evolution "
            "of the Will », un cadrage alternatif : le contraste "
            "ancien/moderne n'est pas autonomie vs capacité d'agir "
            "autrement mais un changement dans la conception du soi "
            "(shrinkage de la « thick psychological ball » antique au "
            "« point-like will » moderne)."
        ),
        "metadata_updates": {
            "affiliation": "Cornell University, Sage School of Philosophy",
            "title": "Susan Linn Sage Professor of Philosophy and Classics",
            "specialty": "Stoic ethics, action theory, emotions, compatibilism",
            "key_works": [
                "Reason and Emotion: A Common Stoic Theory (1998)",
                "The Stoic Life: Emotions, Duties, and Fate (Oxford 2005)",
                "Stoic Moral Psychology (in Cambridge Companion to Stoics, 2003)",
            ],
            "position_in_bobzien_frede_debate": (
                "Third way. Acknowledges massive debt to Bobzien 1998 on "
                "Stoic compatibilism reconstruction but diverges on "
                "philosophical verdict (Brennan 2005 ch.15 n.11). "
                "Critiques Bobzien's framing of ancient/modern moral "
                "responsibility divide as autonomy vs ability-to-do-"
                "otherwise (Brennan 2005 ch.17 p.292). Anticipates "
                "Frede 2011 critique : libertarian reading of Epictetus "
                "is a misunderstanding (Brennan 2005 ch.17 p.296)"
            ),
            "wave": WAVE_TAG,
        },
    },
]


# ===== NEW EDGES =====

NEW_EDGES: list[dict[str, Any]] = [
    # Authorship
    {
        "source": ID_MITSIS_2021,
        "target": ID_MITSIS_PERSON,
        "relation": "authored_by",
        "confidence": 1.0,
        "metadata": {"wave": WAVE_TAG},
    },
    {
        "source": ID_LIENEMANN_2012,
        "target": ID_LIENEMANN_PERSON,
        "relation": "authored_by",
        "confidence": 1.0,
        "metadata": {"wave": WAVE_TAG},
    },
    # Critique edges
    {
        "source": ID_MITSIS_2021,
        "target": ID_FREDE_2011,
        "relation": "critiques",
        "confidence": 0.95,
        "metadata": {
            "wave": WAVE_TAG,
            "critique_type": "methodological",
            "summary": (
                "Mitsis raises three methodological objections to Frede's "
                "argumentative framework: (1) unargued Fodorian assumption "
                "about concepts; (2) attribution of 'sheer volition' view; "
                "(3) quasi-Hegelian teleological narrative"
            ),
            "verification_source": (
                "Citations vérifiées via Blackson 2025 (Rhizomata) p. 84 "
                "n. 9 et p. ~90 n. 23. PDF: data/literature_acquisition/"
                "blackson_2025_rhizomata.pdf"
            ),
        },
    },
    {
        "source": ID_LIENEMANN_2012,
        "target": ID_FREDE_2011,
        "relation": "critiques",
        "confidence": 0.7,
        "metadata": {
            "wave": WAVE_TAG,
            "critique_type": "long_review",
            "summary": (
                "Seule review longue (15 p.) de Frede 2011 en langue "
                "germanique. Contenu non vérifié — node créé en shell "
                "bibliographique, edge en confidence réduite jusqu'à "
                "acquisition du texte intégral"
            ),
            "needs_verification": True,
        },
    },
    # Brennan engagement edges
    {
        "source": ID_BRENNAN_2005_BOOK,
        "target": ID_BOBZIEN_1998,
        "relation": "engages_with",
        "confidence": 0.95,
        "metadata": {
            "wave": WAVE_TAG,
            "engagement_type": "substantive_third_way",
            "summary": (
                "Brennan 2005 Part IV (esp. ch.17 'The Evolution of the "
                "Will') engage massivement Bobzien 1998 'Inadvertent "
                "Conception' : reconnaît la dette intellectuelle mais "
                "diverge sur le verdict philosophique sur le "
                "compatibilisme chrysippéen et propose un cadrage "
                "alternatif de l'évolution ancien/moderne (shrinkage of "
                "the self plutôt que autonomy vs ability-to-do-otherwise)"
            ),
            "key_pages": "p. 268 n. 11, p. 292, p. 305 (Further Reading)",
        },
    },
    {
        "source": ID_BRENNAN_2005_BOOK,
        "target": ID_BOBZIEN_2001_BOOK,
        "relation": "engages_with",
        "confidence": 0.95,
        "metadata": {
            "wave": WAVE_TAG,
            "engagement_type": "substantive_third_way",
            "summary": (
                "Même que pour pub_bobzien_1998_inadvertent — Brennan "
                "cite 'Bobzien (1998a)' qui = le livre Determinism and "
                "Freedom in Stoic Philosophy (Oxford 1998, paperback "
                "2001). L'article Phronesis du même millésime est "
                "'Bobzien (1998b)' dans Brennan"
            ),
        },
    },
]


# ===== IDEMPOTENT MACHINERY =====


def node_id_of_line(line: str) -> str:
    n = json.loads(line)
    return n.get("id") or n.get("node_id") or ""


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source") or e.get("source_id") or "",
        e.get("target") or e.get("target_id") or "",
        e.get("relation") or "",
    )


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def main() -> int:
    # Load
    node_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    nodes_by_id = {node_id_of_line(ln): i for i, ln in enumerate(node_lines)}

    edge_lines = [
        line.rstrip("\n")
        for line in EDGES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_sigs = {edge_signature(json.loads(ln)) for ln in edge_lines}

    changes_nodes: list[str] = []
    changes_edges: list[str] = []

    # 1. NEW NODES — skip if id already exists
    for spec in NEW_NODES:
        nid = spec["id"]
        if nid in nodes_by_id:
            print(f"SKIP (exists): {nid}")
            continue
        node_lines.append(json.dumps(spec, ensure_ascii=False))
        nodes_by_id[nid] = len(node_lines) - 1
        changes_nodes.append(f"NEW    {nid}")

    # 2. ENRICHMENTS — update description + merge metadata; check marker for idempotence
    for spec in ENRICHMENTS:
        nid = spec["id"]
        idx = nodes_by_id.get(nid)
        if idx is None:
            print(f"WARN: enrichment target {nid} not found", file=sys.stderr)
            continue
        node = json.loads(node_lines[idx])
        md = parse_metadata(node.get("metadata"))
        if md.get("wave") == WAVE_TAG or md.get(WAVE_TAG):
            print(f"SKIP (already enriched): {nid}")
            continue
        # Replace description outright if provided (description is fresh, not append)
        if "description" in spec:
            node["description"] = spec["description"]
        if "metadata_updates" in spec:
            md.update(spec["metadata_updates"])
            md[WAVE_TAG] = (
                "Brennan 2005 Part IV enriched with Bobzien-engagement "
                "thesis + 4 verified verbatim citations"
            )
            node["metadata"] = json.dumps(md, ensure_ascii=False)
        node["updated_at"] = NOW
        node_lines[idx] = json.dumps(node, ensure_ascii=False)
        changes_nodes.append(f"ENRICH {nid}")

    # 3. NEW EDGES — skip if (source, target, relation) already present
    for e in NEW_EDGES:
        sig = edge_signature(e)
        if sig in edge_sigs:
            print(f"SKIP edge (exists): {sig[0]} --{sig[2]}--> {sig[1]}")
            continue
        edge_lines.append(json.dumps(e, ensure_ascii=False))
        edge_sigs.add(sig)
        changes_edges.append(f"NEW EDGE  {sig[0]} --{sig[2]}--> {sig[1]}")

    if not changes_nodes and not changes_edges:
        print("OK: nothing to apply (already integrated)")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR}")

    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")

    for c in changes_nodes:
        print(c)
    for c in changes_edges:
        print(c)
    print(
        f"DONE: {len(changes_nodes)} node change(s), "
        f"{len(changes_edges)} new edge(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
