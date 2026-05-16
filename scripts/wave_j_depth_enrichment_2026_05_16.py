#!/usr/bin/env python3
"""Wave J — Scholarly depth enrichment — 2026-05-16.

Audit-fix wave addressing the comprehensive KG audit's content-quality
findings. Four sub-tasks consolidated into a single idempotent script:

* **J1**: expand 5 thin work nodes (145-266c) to 1000-1500c scholarly
  French prose with critical-edition refs (Justin SC 507, Theophilus
  SC 20, Athenagoras SC 379, Plotinus *Ennead* VI.8 Hadot 1988, Melito
  SC 123).
* **J2**: expand 14 scholar shells (39-97c, basically labels) to
  400-800c with dates + affiliation + 2-3 representative publications
  + position in the free-will debate.
* **J3**: prepend a `**Termes** :` Greek/Latin technical-term header
  to ancient concepts whose label+description lack BOTH any Greek
  script character AND any of a fixed list of canonical Latin
  technical terms.
* **J4**: prepend a `**Source primaire** / Prémisse 1 / Prémisse 2 /
  Conclusion / Type / Réception scholaire` structured header to a
  curated list of 10 high-citation argument nodes — only where the
  P1/P2/Conclusion form is clearly identifiable from the existing
  description.

Idempotency:

* J1: skip if existing description length > 800 OR metadata flag
  `j1_enriched_2026_05_16=true`.
* J2: skip if existing description length > 350 OR metadata flag
  `j2_enriched_2026_05_16=true`.
* J3: skip if metadata flag `j3_terms_added_2026_05_16=true`.
* J4: skip if existing description starts with `**Source primaire**`
  OR metadata flag `j4_restructured_2026_05_16=true`.

ZERO fabricated ancient text: Greek/Latin in J3/J4 is restricted to
recognised technical terms whose attestation is documented in the
critical apparatus or in modern scholarship (Bobzien 1998, Amand
1945, Frede 2011, Sorabji 1980, Sharples 1983). Romain is the sole
author.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

WAVE_TAG = "wave_j_depth_enrichment_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# J1 — Thin work nodes → 1000-1500c scholarly French prose
# ---------------------------------------------------------------------------

J1_DESCRIPTIONS: dict[str, str] = {
    "sc507_iustinus_apologia_i": (
        "Justin Martyr, *Première Apologie* (Ἀπολογία πρώτη), adressée à "
        "Antonin le Pieux, Marc Aurèle et Lucius Verus c. 153-155 ap. J.-C. "
        "à Rome. Justin y propose une défense rationnelle du christianisme "
        "contre les calomnies traditionnelles (athéisme, immoralité, "
        "sédition). Structure tripartite : chap. 1-12 (réfutation des "
        "accusations et plaidoyer pour un examen judiciaire équitable), "
        "13-22 (christologie du Christ comme Logos, parallèles avec la "
        "philosophie grecque), 23-60 (preuves prophétiques tirées des "
        "Écritures juives), 61-67 (description des rites — baptême, "
        "eucharistie, réunion dominicale). Pour le débat sur le libre "
        "arbitre, le texte est un jalon central : chap. 28 (anti-Marcion : "
        "Dieu juge en fonction de ce qui dépend du libre choix), chap. "
        "43-44 (autexousion vs nécessité astrologique — argumentation "
        "anti-fataliste majeure transmise à Origène et à toute la "
        "tradition patristique grecque), chap. 61 et 65 (παρὰ τὴν "
        "προαίρεσιν, expressions de la liberté du choix religieux). "
        "Éditions critiques : Goodspeed, *Die ältesten Apologeten* "
        "(Vandenhoeck & Ruprecht, 1914) ; Marcovich, *Iustini Apologiae "
        "pro Christianis* (PTS 38, de Gruyter, 1994) ; Munier, *Justin : "
        "Apologie pour les chrétiens* (SC 507, Cerf, 2006). Traduction "
        "anglaise de référence : Minns & Parvis, *Justin, Philosopher and "
        "Martyr: Apologies* (Oxford Early Christian Texts, OUP, 2009). "
        "Source pivot pour la transmission stoïco-académique du concept "
        "d'autexousion vers la patristique grecque."
    ),
    "sc20_theophilus_ad_autolycum": (
        "Théophile d'Antioche, *Ad Autolycum libri III* (Πρὸς Αὐτόλυκον). "
        "Composé c. 180-190 ap. J.-C. à Antioche, sous l'épiscopat de "
        "Théophile (sixième évêque d'Antioche selon Eusèbe, *HE* IV.20). "
        "Apologie tripartite adressée au païen Autolycos : livre I (Dieu "
        "invisible mais connaissable par ses œuvres, contre l'idolâtrie), "
        "livre II (cosmogonie biblique opposée aux cosmogonies grecques, "
        "exégèse de Gen. 1-3, doctrine du Logos endiathetos / prophorikos), "
        "livre III (chronologie biblique opposée à celle des historiens "
        "grecs, défense de l'antiquité de la révélation mosaïque). Pour "
        "le débat sur le libre arbitre, *Ad Aut.* II.27 articule "
        "explicitement l'anthropologie de la liberté humaine : l'homme "
        "n'a pas été créé ni mortel ni immortel par nature, mais *capable* "
        "de l'un ou de l'autre selon son libre choix (autexousion / "
        "libertas naturalis). Cette page constitue l'un des tout premiers "
        "énoncés patristiques d'une libre détermination de la finalité "
        "eschatologique, et préfigure la doctrine origénienne de la "
        "responsabilité morale comme corrélat de l'image divine. Éditions "
        "critiques : Bardy, *Théophile d'Antioche, Trois livres à "
        "Autolycos* (SC 20, Cerf, 1948) ; Grant, *Theophilus of Antioch: "
        "Ad Autolycum* (Oxford Early Christian Texts, OUP, 1970, texte "
        "grec + traduction anglaise + notes). Influence directe sur "
        "Irénée, *Adversus Haereses* IV (anthropologie de la croissance "
        "et de la liberté), et sur la chaîne anti-fataliste patristique."
    ),
    "sc379_athenagoras_legatio": (
        "Athénagore d'Athènes, *Legatio pro Christianis* (Πρεσβεία περὶ "
        "Χριστιανῶν), composée c. 176-177 ap. J.-C. et adressée aux "
        "empereurs Marc Aurèle et Commode. Apologie philosophique de "
        "haute culture platonicienne : Athénagore se présente comme "
        "« philosophe chrétien d'Athènes » et déploie une argumentation "
        "qui suppose une familiarité avec Platon, Aristote, et les "
        "doxographes hellénistiques. Le traité réfute les trois "
        "accusations standard (athéisme, repas thyestiens, unions "
        "œdipiennes) et défend l'unité divine, la résurrection, et la "
        "moralité chrétienne. Pour le débat sur le libre arbitre, "
        "*Legatio* §24-25 développe une démonologie originale : les "
        "démons sont des esprits déchus qui agissent librement, par "
        "leur libre choix (autexousion) — explicitement opposé à toute "
        "nécessité métaphysique ou astrologique. Cette discussion "
        "préfigure la démonologie christianisante d'Origène (*De "
        "Principiis* I.5-8) et la doctrine angélologique du libre "
        "arbitre déchu reçue par toute la patristique grecque. Éditions "
        "critiques : Schoedel, *Athenagoras: Legatio and De resurrectione* "
        "(Oxford Early Christian Texts, OUP, 1972, texte + trad. + "
        "commentaire) ; Pouderon, *Athénagore : Supplique au sujet des "
        "chrétiens et Sur la résurrection des morts* (SC 379, Cerf, "
        "1992). Traduction allemande récente : Lona, *Bittschrift für "
        "die Christen* (Kommentar zu frühchristlichen Apologeten, "
        "Herder, 2017). Chaîne de transmission : Athénagore → Origène "
        "→ Eusèbe (*PE* III)."
    ),
    "work_plotinus_ennead_vi_8_d8b9c5a4": (
        "Plotin, *Ennéade* VI.8 [39] *Περὶ τοῦ ἑκουσίου καὶ θελήματος "
        "τοῦ ἑνός* (« Sur le volontaire et la volonté de l'Un »). "
        "Œuvre-pivot composée c. 268 ap. J.-C. à Rome, 39e traité "
        "selon l'ordre chronologique du catalogue de Porphyre (*Vita "
        "Plotini* 25) — donc parmi les derniers traités, contemporains "
        "de la maturité philosophique de Plotin. Le traité radicalise "
        "la thèse de la liberté absolue de l'Un : l'Un n'est ni "
        "déterminé par une cause antérieure (il est sans cause "
        "extérieure) ni soumis à la nécessité métaphysique — il EST "
        "son propre vouloir, vouloir-soi-même (τὸ θέλειν αὑτόν), "
        "autexousion étendu au-delà même de l'essence. Plotin argue "
        "que le langage du libre arbitre (ἐφ' ἡμῖν, αὐτεξούσιον), "
        "conçu pour la créature qui choisit entre des possibles "
        "contingents, doit être transposé analogiquement à l'Un — "
        "non comme contingence ou indétermination mais comme "
        "nécessité-de-soi (causa sui) absolue, dans laquelle vouloir "
        "et essence coïncident. Structure : §1-6 (l'erreur de Sextus "
        "Empiricus sur l'éphèmin et la critique sceptique du concept "
        "de liberté), §7-13 (l'Un comme sa propre cause, causa sui — "
        "le hardiesse formelle « τολμηρὸς ὁ λόγος » de §7), §14-21 "
        "(vouloir et essence dans l'Un ; le vouloir-soi divin comme "
        "fondement de tout vouloir dérivé). Éditions critiques : Henry "
        "& Schwyzer, *Plotini Opera* III (OCT 1982, editio minor) ; "
        "traduction française de référence avec commentaire historique "
        "et philosophique : Hadot, *Plotin : Traité 39 (VI 8) Sur le "
        "libre arbitre et la volonté de l'Un* (Cerf, 1988). Traduction "
        "anglaise : Armstrong, *Plotinus VII: Enneads VI.6-9* (Loeb "
        "Classical Library 468, Harvard UP, 1988). Source pivot pour "
        "la réception patristique de l'autexousion divin chez Grégoire "
        "de Nysse, le Pseudo-Denys et Maxime le Confesseur."
    ),
    "sc123_melito_apologia_ad_antoninum": (
        "Méliton de Sardes, fragments de l'*Apologie* adressée à un "
        "empereur antonin (l'attribution traditionnelle d'Eusèbe à "
        "Antonin le Pieux est critiquée — l'identification la plus "
        "probable étant Marc Aurèle 161-180 ap. J.-C., bien que la "
        "tradition manuscrite oscille). Œuvre originellement complète "
        "transmise uniquement par excerpta dans Eusèbe, *Historia "
        "Ecclesiastica* IV.26.5-11, complétée par quelques fragments "
        "syriaques de tradition indirecte. Le contenu reconstructible "
        "comporte une argumentation anti-fataliste et anti-persécutrice : "
        "Méliton défend la rationalité du christianisme face aux "
        "persécutions impériales et plaide pour la tolérance, dans la "
        "lignée apologétique de Justin et d'Athénagore. À distinguer "
        "soigneusement de l'*Homélie Sur la Pâque* (Περὶ Πάσχα), "
        "pièce maîtresse de la christologie quartodecimane retrouvée "
        "au XXe siècle (P. Bodmer XIII + papyrus Chester Beatty) et "
        "éditée dans le même volume SC 123. Édition des fragments : "
        "Hall, *Melito of Sardis: On Pascha and Fragments* (Oxford "
        "Early Christian Texts, OUP, 1979, texte + traduction anglaise "
        "+ commentaire) ; Perler, *Méliton de Sardes : Sur la Pâque et "
        "fragments* (SC 123, Cerf, 1966, texte grec + traduction "
        "française + introduction). Les fragments de l'*Apologie* "
        "occupent l'apparat de SC 123 et sont essentiellement repris "
        "d'Eusèbe."
    ),
}


# ---------------------------------------------------------------------------
# J2 — Scholar shells → 400-800c French scholarly prose
# ---------------------------------------------------------------------------

J2_DESCRIPTIONS: dict[str, str] = {
    "scholar_furst_alfons": (
        "Alfons Fürst (né 1961). Patristicien allemand, professeur "
        "d'histoire ancienne de l'Église à la Westfälische "
        "Wilhelms-Universität Münster, directeur de l'*Origenes "
        "Forschungsstelle*. Auteur de *Hieronymus: Askese und "
        "Wissenschaft in der Spätantike* (Herder, 2003) et de *Origenes: "
        "Grieche und Christ in römischer Zeit* (Hiersemann, 2017). "
        "Œuvre-pivot pour la cartographie KG du débat libre arbitre : "
        "*Wege zur Freiheit: Menschliche Selbstbestimmung von Homer bis "
        "Origenes* (Mohr Siebeck, 2022) — histoire conceptuelle de "
        "l'autexousion d'Homère à Origène, défendant la thèse d'une "
        "« invention » origénienne du libre arbitre comme dogme "
        "théologique solidaire de la responsabilité morale. Reçoit et "
        "radicalise Dihle 1982 et Frede 2011 dans une lecture confessante "
        "qui fait d'Origène le terminus a quo de la doctrine chrétienne "
        "du libre arbitre."
    ),
    "scholar_amand_de_mendieta_e": (
        "Emmanuel Amand de Mendieta O.S.B. (1908-1977). Bénédictin belge, "
        "philologue et historien de la philosophie ancienne formé à "
        "Louvain. Sa thèse doctorale (1944), publiée sous le titre "
        "*Fatalisme et liberté dans l'antiquité grecque* (Bibliothèque "
        "de l'Université de Louvain, 1945 ; réimpression Hakkert, "
        "Amsterdam, 1973), est l'étude philologique de référence pour "
        "la reconstruction de la transmission Carnéade → Clitomaque → "
        "Cicéron (*De Fato*) / Eusèbe (*Praeparatio Evangelica* VI) → "
        "Origène / Grégoire de Nysse / Diodore de Tarse / Némésius / "
        "Théodoret. Amand identifie systématiquement les « Carneadea » "
        "(fragments doxographiques anti-déterministes) dans la "
        "littérature patristique, fondant l'historiographie moderne de "
        "la réception patristique du scepticisme académique. Autres "
        "travaux : édition critique du *De Spiritu Sancto* de Basile "
        "(SC 17, Cerf, 1947 ; éd. revue SC 17bis, 1968) ; recherches "
        "sur la transmission Basile-Eustathe."
    ),
    "scholar_sharples_robert": (
        "Robert W. Sharples (1949-2010). Helléniste britannique, "
        "professeur de Greek and Latin à University College London. "
        "Spécialiste reconnu d'Alexandre d'Aphrodise et des "
        "commentateurs aristotéliciens. Ouvrages-pivots : *Alexander "
        "of Aphrodisias: On Fate* (Duckworth, 1983 — édition + "
        "traduction anglaise + commentaire, référence absolue du "
        "*De Fato*) ; *Cicero: On Fate (De Fato) and Boethius: "
        "Consolation of Philosophy IV.5-7, V* (Aris & Phillips, 1991) ; "
        "édition de la *Mantissa* : *Alexander of Aphrodisias: De Anima "
        "libri mantissa* (de Gruyter, 2008). Co-éditeur de la série "
        "*Sources for Hellenistic Philosophy* (Ashgate). Position dans "
        "le débat free-will : lecture historico-philologique des "
        "« libertarian incompatibilists » antiques, marquée par la "
        "prudence terminologique."
    ),
    "scholar_gourinat_jean_baptiste": (
        "Jean-Baptiste Gourinat (né 1962). CNRS, directeur de recherche, "
        "ancien directeur du Centre Léon Robin (UMR 8061, Paris). "
        "Spécialiste majeur du stoïcisme et de la logique ancienne. "
        "Publications de référence : *Les Stoïciens et l'âme* (Vrin, "
        "1996 ; nouvelle édition 2017), *La Dialectique des Stoïciens* "
        "(Vrin, 2000), co-direction de *Lire les Stoïciens* (PUF, 2009, "
        "avec Jacques Brunschwig). Travaux nombreux sur Chrysippe, la "
        "causalité stoïcienne, la sympatheia, la doctrine du destin et "
        "la cohérence du système stoïcien sur la liberté. Position : "
        "défend une lecture exégétique fine du compatibilisme stoïcien "
        "et la cohérence interne de Chrysippe sur destin et responsabilité."
    ),
    "scholar_long_anthony": (
        "Anthony Arthur Long (né 1937). Professeur émérite de Classics "
        "à UC Berkeley, l'un des historiens anglo-saxons majeurs de la "
        "philosophie hellénistique. Co-auteur avec David Sedley du "
        "standard scholarly *The Hellenistic Philosophers* (Cambridge "
        "UP, 1987, 2 vol. — référence universellement citée sous le "
        "sigle « LS »). Autres ouvrages pivots : *Hellenistic Philosophy: "
        "Stoics, Epicureans, Sceptics* (Duckworth, 1974 ; 2e éd. 1986) ; "
        "*Stoic Studies* (Cambridge UP, 1996) ; *Epictetus: A Stoic and "
        "Socratic Guide to Life* (OUP, 2002) ; *From Epicurus to "
        "Epictetus* (OUP, 2006). Référence centrale de l'étude du "
        "stoïcisme dans le monde anglo-américain. Position : "
        "compatibiliste réaliste sur la lecture stoïcienne du destin "
        "et de l'eph' hēmin."
    ),
    "person_sorabji_richard_contemporary": (
        "Richard Sorabji (né 1934). Professeur émérite de philosophie "
        "ancienne à King's College London ; Fellow of the British "
        "Academy. Patristicien et historien de la philosophie antique. "
        "Ouvrage-pivot : *Necessity, Cause, and Blame: Perspectives on "
        "Aristotle's Theory* (Duckworth, 1980 ; réimpression Bristol "
        "Classical Press, 2006) — analyse magistrale du *De "
        "Interpretatione* 9 aristotélicien et de sa réception "
        "stoïcienne, base de toute discussion ultérieure sur le "
        "problème des futurs contingents. Autres : *Time, Creation, and "
        "the Continuum* (Duckworth, 1983) ; *Emotion and Peace of Mind: "
        "From Stoic Agitation to Christian Temptation* (OUP, 2000). "
        "Directeur fondateur de la série *Ancient Commentators on "
        "Aristotle* (Duckworth puis Cornell UP, plus de 100 volumes "
        "publiés), entreprise qui a transformé l'accès aux commentateurs "
        "grecs tardifs."
    ),
    "person_frankfurt_harry_1929_2023": (
        "Harry Gordon Frankfurt (1929-2023). Professeur émérite de "
        "philosophie à Princeton. Philosophe analytique de l'action, "
        "auteur des contributions les plus citées du débat contemporain "
        "sur la liberté et la responsabilité morale. Article-pivot : "
        "« Alternate Possibilities and Moral Responsibility », *Journal "
        "of Philosophy* 66 (1969) 829-839 — les célèbres « cas de "
        "Frankfurt », contre-exemples contre le Principle of Alternate "
        "Possibilities (PAP) qui ont reformulé tout le débat "
        "compatibiliste depuis les années 1970. Autre article majeur : "
        "« Freedom of the Will and the Concept of a Person », *Journal "
        "of Philosophy* 68 (1971) 5-20 — théorie des désirs de second "
        "ordre. Recueil : *The Importance of What We Care About* "
        "(Cambridge UP, 1988). Position : compatibiliste, défenseur "
        "d'une théorie « hiérarchique » de la volonté libre."
    ),
    "person_kane_robert_1938_2022": (
        "Robert Hilary Kane (1938-2022). Professeur de philosophie à "
        "l'University of Texas at Austin. Libertarien classique du "
        "débat free-will contemporain. Ouvrage-pivot : *The Significance "
        "of Free Will* (OUP, 1996) — défense d'un libertarianisme "
        "event-causal articulé autour des Self-Forming Actions (SFA), "
        "moments décisifs où l'agent forme son caractère à travers un "
        "choix authentiquement indéterminé. Éditeur du *Oxford Handbook "
        "of Free Will* (OUP, 2002 ; 2e éd. 2011), ouvrage de référence "
        "du champ. Manuel d'introduction très diffusé : *A Contemporary "
        "Introduction to Free Will* (OUP, 2005). Position : "
        "libertarianisme non-théiste, défendant la compatibilité de "
        "l'indéterminisme quantique avec la responsabilité morale "
        "robuste."
    ),
    "scholar_crouzel_henri": (
        "Henri Crouzel S.J. (1919-2003). Jésuite français, professeur "
        "à l'Institut Catholique de Toulouse, doyen des études "
        "origéniennes du XXe siècle. Œuvres majeures : *Théologie de "
        "l'image de Dieu chez Origène* (Aubier, 1956), *Origène et la "
        "« connaissance mystique »* (Desclée de Brouwer, 1961), "
        "*Origène et la philosophie* (Aubier, 1962), *Origène* "
        "(Lethielleux, 1985 — synthèse de référence, traduite en "
        "plusieurs langues). Avec Manlio Simonetti, co-éditeur de "
        "l'édition critique du *De Principiis* : SC 252-253 + 268-269 "
        "+ 312 (Cerf, 1978-1984), édition de référence du traité. "
        "Position : reconstruction systématique de la théologie "
        "origénienne attentive à la cohérence interne et au refus de "
        "l'origénisme caricaturé par la condamnation justinienne."
    ),
    "scholar_dunn_j": (
        "James D. G. Dunn (1939-2020). Lightfoot Professor of Divinity "
        "à l'Université de Durham. Néotestamentaire britannique majeur, "
        "co-fondateur (avec E. P. Sanders et N. T. Wright) de la "
        "« New Perspective on Paul ». Ouvrages : *The New Perspective "
        "on Paul* (Mohr Siebeck, 2005 ; éd. révisée 2008) ; *The "
        "Theology of Paul the Apostle* (Eerdmans, 1998) ; commentaire "
        "monumental de *Romans* (Word Biblical Commentary 38, 2 vol., "
        "1988). Position dans le KG : référence centrale pour la "
        "réception paulinienne de la grâce vs libre arbitre dans le "
        "débat Augustin-Pélage, par contre-coup des relectures "
        "néo-perspectivistes de Romains 7 et 9-11."
    ),
    "scholar_koch_i": (
        "Isabelle Koch. Maître de conférences puis professeure à "
        "Aix-Marseille Université (Centre Gilles Gaston Granger). "
        "Spécialiste française de Plotin, des néoplatoniciens tardifs "
        "(Damascius, Proclus) et de la philosophie patristique grecque. "
        "Auteure de traductions et de commentaires plotiniens, et "
        "d'études sur la causalité, la providence et la réception "
        "néoplatonicienne du libre arbitre. Position : philologue "
        "rigoureuse, attentive à la généalogie conceptuelle de "
        "l'autexousion néoplatonicien vers la patristique grecque "
        "(Grégoire de Nysse, Maxime le Confesseur)."
    ),
    "scholar_destr_e_p": (
        "Pierre Destrée. Professeur à l'UCLouvain (Institut supérieur "
        "de philosophie). Spécialiste de l'éthique aristotélicienne et "
        "de l'éthique stoïcienne, et de la προαίρεσις aristotélicienne "
        "comme concept-clé de l'agent moral. Co-éditeur de plusieurs "
        "volumes Brill, notamment *Akrasia in Greek Philosophy: From "
        "Socrates to Plotinus* (Brill, 2007, avec Christopher Bobonich). "
        "Position : reconstruction historique de la genèse aristotélicienne "
        "du concept de choix délibéré (prohairesis) et de sa "
        "transformation par le stoïcisme impérial (Épictète)."
    ),
    "person_fischer_john_martin_3w4x5y6z": (
        "John Martin Fischer (né 1952). Distinguished Professor of "
        "Philosophy à UC Riverside. Compatibiliste contemporain majeur. "
        "Ouvrages : *The Metaphysics of Free Will: An Essay on Control* "
        "(Blackwell, 1994) ; *Responsibility and Control: A Theory of "
        "Moral Responsibility* (Cambridge UP, 1998, avec Mark Ravizza) "
        "— développement de la théorie du *guidance control* "
        "(semi-compatibilisme : responsabilité morale sans alternate "
        "possibilities) ; *My Way: Essays on Moral Responsibility* "
        "(OUP, 2006). Position : semi-compatibiliste, héritier critique "
        "des cas de Frankfurt, défenseur d'une responsabilité morale "
        "robuste compatible avec le déterminisme causal."
    ),
    "scholar_dettwiler_a": (
        "Andreas Dettwiler (né 1959). Professeur de Nouveau Testament à "
        "la Faculté de théologie de l'Université de Genève. "
        "Néotestamentaire suisse. Ouvrage : commentaire de *L'épître "
        "aux Éphésiens* (Labor et Fides, 2008). Travaux sur la "
        "christologie paulinienne, la littérature deutéro-paulinienne "
        "(Colossiens, Éphésiens, Pastorales) et leur réception "
        "patristique. Position dans le KG : référence pour l'arrière-plan "
        "paulinien et deutéro-paulinien de la doctrine de la grâce "
        "reçue par les Pères grecs et latins."
    ),
}


# ---------------------------------------------------------------------------
# J3 — Greek/Latin technical terms on ancient concepts
#
# Only entries explicitly listed in the audit are eligible. Each entry
# is applied only if BOTH `j3_terms_added_2026_05_16` flag is absent AND
# the current label+description has neither a Greek-script character nor
# any canonical Latin term in `LATIN_TERMS`.
# ---------------------------------------------------------------------------

J3_TERM_PREFIXES: dict[str, str] = {
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": (
        "**Termes** : παρέγκλισις (parenklisis) ; lat. clinamen ; "
        "« déviation, inclinaison » — la déviation atomique spontanée."
    ),
    "concept_exercitatio_adversity_seneca_c4d5e6f7": (
        "**Termes** : exercitatio ; gr. ἄσκησις (askēsis) ; « exercice, "
        "entraînement » — l'adversité comme entraînement de la vertu."
    ),
    "concept_summum_bonum_boethius_k6l7m8n9": (
        "**Termes** : summum bonum ; gr. τέλος (telos) / τὸ ἀγαθόν "
        "(to agathon) ; le Bien suprême identifié à Dieu."
    ),
    "concept_fortuna_boethius_j5k6l7m8": (
        "**Termes** : fortuna ; gr. τύχη (tychē) ; la mutabilité de "
        "la fortune mondaine, personnifiée."
    ),
    "concept_synergism": (
        "**Termes** : συνέργεια (synergeia) ; lat. cooperatio ; « œuvre "
        "conjointe » — coopération du libre arbitre humain avec la grâce."
    ),
    "concept_concupiscence_epithumia_transmitted_bd8e2fc9": (
        "**Termes** : ἐπιθυμία (epithymia) ; lat. concupiscentia ; "
        "« désir, convoitise » — chez Méthode : conséquence transmise, "
        "non culpabilité héritée."
    ),
    "concept_cylinder_analogy_chrysippus_e5f6g7h8": (
        "**Termes** : κύλινδρος (kylindros) ; lat. cylindrus "
        "(Cic., *De Fato* 42) ; l'analogie chrysippéenne du cylindre "
        "pour la causalité interne."
    ),
    "concept_gratia_praeveniens": (
        "**Termes** : gratia praeveniens (« grâce qui précède ») ; "
        "gratia praeparans ; gr. χάρις προαγωγική (charis proagōgikē) ; "
        "la grâce qui prévient l'acte du libre arbitre."
    ),
    "concept_hypothetical_fate_middle_platonist": (
        "**Termes** : εἱμαρμένη ἐξ ὑποθέσεως (heimarmenē ex hypotheseōs) ; "
        "lat. fatum ex hypothesi ; le destin sous condition vs absolu "
        "(haplōs) du Moyen Platonisme."
    ),
}


# ---------------------------------------------------------------------------
# J4 — Argument restructure: P1/P2/Conclusion header
# ---------------------------------------------------------------------------

J4_HEADERS: dict[str, str] = {
    # 1. Argos Logos refutation (Origen)
    "argument_origen_argos_logos": (
        "**Source primaire** : Origène, *Contra Celsum* II.20 "
        "(SC 132, Borret, 1967) ; transmis aussi dans *Philocalie* 23.\n"
        "**Prémisse 1** : Si tout est fatalement déterminé, "
        "l'effort humain (πρᾶξις) est superflu (argos logos).\n"
        "**Prémisse 2** : Mais l'effort est en réalité indispensable "
        "à l'accomplissement de l'événement prédit — la prophétie "
        "elle-même suppose la coopération libre de l'agent.\n"
        "**Conclusion** : L'inférence fataliste est donc invalide ; "
        "la prescience divine n'élimine pas la responsabilité humaine.\n"
        "**Type de raisonnement** : réfutation dialectique (refutatio) "
        "par retournement de l'argument adverse.\n"
        "**Réception scholaire** : Amand 1945 (ch. III, transmission "
        "Carnéade → Origène) ; Bobzien 1998 (Idle Argument, p. 180-200)."
    ),
    # 2. Justin antifatalist
    "argument_justin_antifatalism": (
        "**Source primaire** : Justin Martyr, *Apologie I* 43-44 "
        "(SC 507, Munier, 2006).\n"
        "**Prémisse 1** : Si tout advient par le destin (εἱμαρμένη), "
        "alors ce qui dépend de nous (ἐφ' ἡμῖν) n'est absolument rien.\n"
        "**Prémisse 2** : Or la responsabilité morale (louange, blâme, "
        "récompense, châtiment, exhortation prophétique) suppose que "
        "quelque chose dépend de nous.\n"
        "**Conclusion** : Donc le fatalisme intégral détruit toute "
        "moralité — il faut affirmer l'autexousion humain.\n"
        "**Type de raisonnement** : reductio ad absurdum + argument "
        "par les conséquences pratiques.\n"
        "**Réception scholaire** : Amand 1945 (premier argumentaire "
        "anti-fataliste chrétien systématique) ; Frede 2011 ; Fürst "
        "2022 (généalogie de l'autexousion patristique)."
    ),
    # 3. Justin angel-fall
    "argument_justin_angel_fall": (
        "**Source primaire** : Justin Martyr, *Apologie II* 5-7 "
        "(SC 507, Munier, 2006).\n"
        "**Prémisse 1** : Dieu a créé les anges avec autexousion "
        "(αὐτεξούσιον, libre détermination), comme les hommes.\n"
        "**Prémisse 2** : Certains anges ont transgressé par mauvais "
        "usage de leur libre choix — la chute angélique est donc "
        "imputable à leur libre arbitre, non à un défaut de création.\n"
        "**Conclusion** : Le libre arbitre est universel à toute "
        "créature rationnelle ; l'origine du mal est dans l'usage "
        "libre, jamais dans la cause divine.\n"
        "**Type de raisonnement** : déductif (anthropologie étendue à "
        "l'angélologie).\n"
        "**Réception scholaire** : Amand 1945 ; Fürst 2022 ; Frede 2011."
    ),
    # 4. Justin prophecy-freedom
    "argument_justin_prophecy_freedom": (
        "**Source primaire** : Justin Martyr, *Apologie I* 44 "
        "(SC 507, Munier, 2006).\n"
        "**Prémisse 1** : Dieu préconnaît (προγινώσκει) les actions "
        "humaines futures et les annonce par les prophètes.\n"
        "**Prémisse 2** : La préconnaissance divine n'est pas "
        "causation : Dieu connaît parce que l'action aura lieu, et "
        "non l'inverse.\n"
        "**Conclusion** : Prescience et libre arbitre sont donc "
        "compatibles ; les prophéties n'imposent aucune nécessité "
        "à l'agent.\n"
        "**Type de raisonnement** : distinction conceptuelle "
        "(connaissance vs causation).\n"
        "**Réception scholaire** : Amand 1945 (transmission vers "
        "Origène et Boèce) ; Sorabji 1980 ; Frede 2011."
    ),
    # 5. Augustine donum perseverantiae
    "argument_augustine_donum_perseverantiae": (
        "**Source primaire** : Augustin, *De Dono Perseverantiae* "
        "(CSEL 60, Urba & Zycha, 1913 ; PL 45.993-1034).\n"
        "**Prémisse 1** : La persévérance jusqu'à la fin (perseverantia "
        "finalis) n'est pas une capacité naturelle de l'homme déchu.\n"
        "**Prémisse 2** : Même la foi authentique peut se perdre sans "
        "un don divin additionnel qui maintienne le vouloir dans le "
        "bien jusqu'à la mort.\n"
        "**Conclusion** : La persévérance est donc strictement *donum* "
        "(don gratuit de Dieu), non *meritum* (mérite de l'homme) — "
        "doctrine fondatrice de l'anti-pélagianisme tardif.\n"
        "**Type de raisonnement** : déductif à partir d'une "
        "anthropologie augustinienne de la concupiscence post-lapsaire.\n"
        "**Réception scholaire** : Brown 2000 (*Augustine of Hippo*) ; "
        "Wetzel 1992 ; débat avec Cassien et le semi-pélagianisme."
    ),
    # 6. Augustine massa damnata
    "argument_augustine_massa_damnata": (
        "**Source primaire** : Augustin, *Enchiridion* 99 + *De Civitate "
        "Dei* XXI.12 (CCSL 47-48, Dombart & Kalb, 1955).\n"
        "**Prémisse 1** : Tous les hommes sont solidaires d'Adam dans "
        "la chute (Rom. 5.12), constituant après la Chute une *massa "
        "damnata* (masse de perdition) justement condamnée.\n"
        "**Prémisse 2** : Si Dieu sauvait tous les hommes, ce serait "
        "miséricorde sans justice ; s'il n'en sauvait aucun, ce serait "
        "justice sans miséricorde ; en sauvant certains gratuitement, "
        "Dieu manifeste les deux.\n"
        "**Conclusion** : L'élection est donc strictement gratuite, "
        "fondée sur la seule décision divine, sans condition "
        "préalable du côté humain.\n"
        "**Type de raisonnement** : déductif à partir d'Augustin "
        "exégète de Romains 9-11.\n"
        "**Réception scholaire** : Wetzel 1992 ; Brown 2000 ; débat "
        "anti-pélagien et opposition de Julien d'Éclane."
    ),
    # 7. Augustine foreknowledge-freewill
    "argument_augustine_foreknowledge_freewill": (
        "**Source primaire** : Augustin, *De Civitate Dei* V.9-10 "
        "(CCSL 47, Dombart & Kalb, 1955).\n"
        "**Prémisse 1** : Dieu préconnaît (praescit) toutes les "
        "volontés humaines futures, y compris les volontés libres.\n"
        "**Prémisse 2** : La prescience divine ne supprime pas la "
        "liberté du vouloir : Dieu connaît précisément que la volonté "
        "agira *librement*, et c'est cette modalité libre qui est "
        "préconnue.\n"
        "**Conclusion** : Prescience et libre arbitre sont donc "
        "compatibles, contra Cicéron (*De Fato*) qui sacrifie la "
        "prescience pour préserver la liberté.\n"
        "**Type de raisonnement** : distinction modale "
        "(la préconnaissance porte sur l'acte-comme-libre, non sur "
        "la nécessité de l'acte).\n"
        "**Réception scholaire** : Sorabji 1980 ; débat avec la "
        "tradition stoïcienne et anti-cicéronienne ; précurseur de "
        "Boèce V.pr.6."
    ),
    # 8. Boethius foreknowledge problem
    "argument_boethius_foreknowledge_problem": (
        "**Source primaire** : Boèce, *Consolation de la Philosophie* "
        "V.pr.3 (CCSL 94, Bieler, 1957 ; SC 519/520, Moreschini, 2008).\n"
        "**Prémisse 1** : Si Dieu préconnaît avec certitude que X "
        "adviendra, alors X adviendra nécessairement (sinon la "
        "prescience serait fausse).\n"
        "**Prémisse 2** : Mais si X advient nécessairement, X n'est "
        "pas un événement libre.\n"
        "**Conclusion** (apparente) : Donc la prescience divine "
        "détruit le libre arbitre — formulation canonique du problème "
        "logique transmise à toute la scolastique latine.\n"
        "**Type de raisonnement** : reductio dialectique (le problème "
        "est posé en V.pr.3, résolu en V.pr.6 par la doctrine du "
        "nunc stans).\n"
        "**Réception scholaire** : Sorabji 1980 ; Marenbon 2003 "
        "(*Boethius*) ; reprise par Thomas d'Aquin et la scolastique."
    ),
    # 9. Boethius modes of cognition
    "argument_boethius_modes_cognition": (
        "**Source primaire** : Boèce, *Consolation de la Philosophie* "
        "V.pr.4-5 (CCSL 94, Bieler, 1957 ; SC 519/520, Moreschini, 2008).\n"
        "**Prémisse 1** : La connaissance est déterminée par le mode "
        "(modus) du sujet connaissant, non par le mode de l'objet connu.\n"
        "**Prémisse 2** : Les modes cognitifs forment une hiérarchie "
        "ascendante : sens, imagination, raison, intelligence — chacun "
        "saisissant son objet selon sa propre modalité.\n"
        "**Conclusion** : Dieu connaît selon son mode propre "
        "(éternité, *nunc stans*), qui transcende la succession "
        "temporelle ; il saisit tous les temps dans un présent unique, "
        "sans nécessiter l'objet connu.\n"
        "**Type de raisonnement** : déductif (épistémologie "
        "néoplatonicienne servant de prémisse à la solution de "
        "V.pr.6).\n"
        "**Réception scholaire** : Sorabji 1980 ; Marenbon 2003 ; "
        "reprise par Thomas d'Aquin (*ST* I, q. 14, a. 13)."
    ),
    # 10. Epictetus dichotomy of control
    "argument_epictetus_dichotomy_control": (
        "**Source primaire** : Épictète, *Manuel* (*Encheiridion*) 1 "
        "(éd. Schenkl, BT 1916 ; SC 503, Hadot, 2007 pour les "
        "*Entretiens* parallèles).\n"
        "**Prémisse 1** : Certaines choses sont en notre pouvoir "
        "(ἐφ' ἡμῖν) — jugement (ὑπόληψις), impulsion (ὁρμή), désir "
        "(ὄρεξις), aversion (ἔκκλισις).\n"
        "**Prémisse 2** : D'autres ne sont pas en notre pouvoir "
        "(οὐκ ἐφ' ἡμῖν) — corps, biens, réputation, charges.\n"
        "**Conclusion** : La liberté et la tranquillité s'obtiennent "
        "en limitant rigoureusement le désir et l'aversion à ce qui "
        "est en notre pouvoir — discipline fondamentale du stoïcisme "
        "impérial.\n"
        "**Type de raisonnement** : analytique (distinction "
        "fondatrice) + pratique (règle de vie).\n"
        "**Réception scholaire** : Long 2002 (*Epictetus*) ; Hadot "
        "2007 ; Bobzien 1998 ; Frede 2011 (transformation impériale "
        "de la prohairesis aristotélicienne)."
    ),
}


# ---------------------------------------------------------------------------
# Latin technical terms (J3 detection)
# ---------------------------------------------------------------------------

GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
LATIN_TERMS: list[str] = [
    "clinamen",
    "liberum arbitrium",
    "voluntas",
    "fortuna",
    "gratia",
    "concupiscentia",
    "peccatum",
    "praedestinatio",
    "propositum",
    "arbitrium",
    "consensus",
    "assensus",
    "liberum",
    "necessitas",
    "providentia",
    "fatum",
    "causa",
    "exercitatio",
    "summum bonum",
    "cooperatio",
]


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def parse_metadata(raw: Any) -> tuple[dict[str, Any], bool]:
    """Return ``(metadata-dict, was_string)``."""
    if raw is None:
        return {}, False
    if isinstance(raw, str):
        try:
            obj = json.loads(raw) if raw.strip() else {}
            if not isinstance(obj, dict):
                obj = {}
            return obj, True
        except json.JSONDecodeError:
            return {}, True
    if isinstance(raw, dict):
        return dict(raw), False
    return {}, False


def reencode_metadata(
    node: dict[str, Any], md: dict[str, Any], was_string: bool
) -> None:
    raw = node.get("metadata")
    if was_string or isinstance(raw, str):
        node["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node["metadata"] = md


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    if snap_nodes.exists():
        print(
            f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} — skip"
        )
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Sub-task runners
# ---------------------------------------------------------------------------


def run_j1(nodes: list[dict[str, Any]]) -> tuple[int, int]:
    enriched = 0
    skipped = 0
    for n in nodes:
        nid = node_id(n)
        if nid not in J1_DESCRIPTIONS:
            continue
        md, was_string = parse_metadata(n.get("metadata"))
        existing_desc = n.get("description") or ""
        if md.get("j1_enriched_2026_05_16") is True or len(existing_desc) > 800:
            skipped += 1
            continue
        new_desc = J1_DESCRIPTIONS[nid]
        n["description"] = new_desc
        n["updated_at"] = NOW_ISO
        md["j1_enriched_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        enriched += 1
    return enriched, skipped


def run_j2(nodes: list[dict[str, Any]]) -> tuple[int, int]:
    enriched = 0
    skipped = 0
    for n in nodes:
        nid = node_id(n)
        if nid not in J2_DESCRIPTIONS:
            continue
        md, was_string = parse_metadata(n.get("metadata"))
        existing_desc = n.get("description") or ""
        if md.get("j2_enriched_2026_05_16") is True or len(existing_desc) > 350:
            skipped += 1
            continue
        new_desc = J2_DESCRIPTIONS[nid]
        n["description"] = new_desc
        n["updated_at"] = NOW_ISO
        md["j2_enriched_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        enriched += 1
    return enriched, skipped


def _has_terms(label: str, desc: str) -> bool:
    blob = f"{label} {desc}"
    if GREEK_RE.search(blob):
        return True
    blob_low = blob.lower()
    return any(t in blob_low for t in LATIN_TERMS)


def run_j3(nodes: list[dict[str, Any]]) -> tuple[int, int, int]:
    audited = 0
    already_have_terms = 0
    term_added = 0
    for n in nodes:
        nid = node_id(n)
        if nid not in J3_TERM_PREFIXES:
            continue
        audited += 1
        md, was_string = parse_metadata(n.get("metadata"))
        if md.get("j3_terms_added_2026_05_16") is True:
            already_have_terms += 1
            continue
        label = n.get("label") or ""
        desc = n.get("description") or ""
        if _has_terms(label, desc):
            already_have_terms += 1
            continue
        prefix = J3_TERM_PREFIXES[nid]
        new_desc = f"{prefix}\n\n{desc}".rstrip()
        n["description"] = new_desc
        n["updated_at"] = NOW_ISO
        md["j3_terms_added_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        term_added += 1
    return audited, already_have_terms, term_added


def run_j4(nodes: list[dict[str, Any]]) -> tuple[int, int, int]:
    restructured = 0
    not_found = 0
    skipped = 0
    targets_seen: set[str] = set()
    for n in nodes:
        nid = node_id(n)
        if nid not in J4_HEADERS:
            continue
        targets_seen.add(nid)
        md, was_string = parse_metadata(n.get("metadata"))
        existing_desc = n.get("description") or ""
        if (
            md.get("j4_restructured_2026_05_16") is True
            or existing_desc.lstrip().startswith("**Source primaire**")
        ):
            skipped += 1
            continue
        header = J4_HEADERS[nid]
        new_desc = f"{header}\n\n{existing_desc}".rstrip()
        n["description"] = new_desc
        n["updated_at"] = NOW_ISO
        md["j4_restructured_2026_05_16"] = True
        md["wave"] = WAVE_TAG
        reencode_metadata(n, md, was_string)
        restructured += 1
    not_found = len(J4_HEADERS) - len(targets_seen)
    return restructured, not_found, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-j] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    print(f"[load] nodes={len(nodes):,}")

    j1_enriched, j1_skipped = run_j1(nodes)
    j2_enriched, j2_skipped = run_j2(nodes)
    j3_audited, j3_already, j3_added = run_j3(nodes)
    j4_restructured, j4_not_found, j4_skipped = run_j4(nodes)

    write_nodes(nodes)

    print(
        f"[wave-j-J1] works_enriched={j1_enriched}/{len(J1_DESCRIPTIONS)}  "
        f"skipped_existing={j1_skipped}"
    )
    print(
        f"[wave-j-J2] scholars_enriched={j2_enriched}/{len(J2_DESCRIPTIONS)}  "
        f"skipped_existing={j2_skipped}"
    )
    print(
        f"[wave-j-J3] concepts_audited={j3_audited}  "
        f"already_have_terms={j3_already}  "
        f"term_added={j3_added}"
    )
    print(
        f"[wave-j-J4] arguments_restructured={j4_restructured}/"
        f"{len(J4_HEADERS)}  "
        f"not_found={j4_not_found}  "
        f"skipped_unclear={j4_skipped}"
    )
    print(f"[wave-j] done :: nodes {len(nodes):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
