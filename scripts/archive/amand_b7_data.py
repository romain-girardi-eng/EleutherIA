"""Amand B7 — UPDATES list (description + metadata enrichments for existing nodes).

Targets: person_gregory_nyssa_d395, work_gregory_contra_fatum, work_gregory_oratio_catechetica,
person_john_chrysostom_d407, sc79_chrysostomus_de_providentia,
person_nemesius_emesa_4c_ce, work_nemesius_de_nat_hom.
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # ---------------------------------------------------------------------------
    # 1. Gregory of Nyssa — enrichissement portrait Amand (Ch. IX, p. 405-422)
    # ---------------------------------------------------------------------------
    {
        "id": "person_gregory_nyssa_d395",
        "description": (
            "Grégoire de Nysse (c. 335-c. 395 CE), évêque de Nysse en Cappadoce, "
            "frère cadet de Basile de Césarée, l'un des trois Pères cappadociens. "
            "Pour Amand 1945 (Livre II Ch. IX, p. 405-439), Grégoire est un "
            "platonicien chrétien et mystique d'inspiration origénienne, doté d'une "
            "connaissance intime et assimilée de la sagesse hellénique sans égal chez "
            "les écrivains ecclésiastiques du IVe siècle (cf. Cherniss 1930). Nature "
            "tranquille et réservée, peu doué pour la vie pratique, contraint à "
            "l'épiscopat par l'impérieux Basile, Grégoire consacra son activité "
            "littéraire surtout après 379 à présenter l'orthodoxie nicéenne dans "
            "les termes d'une théologie savante. Sa méthode rationnelle culmine dans "
            "le Discours catéchétique, qu'Amand qualifie de production systématique "
            "la plus considérable et la plus puissante après le Peri Archon d'Origène. "
            "Pour la question du libre arbitre, Grégoire défend l'autexousion comme "
            "privilège divin concédé à la nature humaine en vertu de l'image de Dieu "
            "(Disc. cat. 30, ed. Srawley p. 112) et identifie ce libre arbitre à la "
            "prohairesis. Pour Amand, ses deux contributions majeures à la transmission "
            "carnéadienne sont (a) le traité Contre le Destin (Kata heimarmenes), opuscule "
            "d'allure néo-académicienne presque entièrement philosophique, et (b) le "
            "chapitre 31 du Discours catéchétique qui résume l'argumentation morale "
            "antifataliste de Carnéade comme lieu commun d'école."
        ),
        "description_en": (
            "Gregory of Nyssa (c. 335-c. 395 CE), bishop of Nyssa in Cappadocia, younger "
            "brother of Basil of Caesarea, one of the three Cappadocian Fathers. For "
            "Amand 1945 (Book II Ch. IX, p. 405-439), Gregory is a Christian Platonist "
            "and mystic of Origenian inspiration, with an intimate and assimilated "
            "knowledge of Hellenic wisdom unmatched among 4th-century ecclesiastical "
            "writers (cf. Cherniss 1930). Quiet and reserved by nature, ill-suited to "
            "practical life, forced into the episcopate by the imperious Basil, Gregory "
            "devoted his literary activity especially after 379 to presenting Nicene "
            "orthodoxy in the terms of a scholarly theology. His rational method "
            "culminates in the Oratio Catechetica, which Amand calls the most "
            "considerable and powerful systematic production after Origen's Peri Archon. "
            "On free will, Gregory defends autexousion as a divine privilege granted to "
            "human nature by virtue of the image of God (Cat. Or. 30, ed. Srawley p. 112) "
            "and identifies this freedom with prohairesis. For Amand, his two major "
            "contributions to the Carneadean transmission are (a) the Contra Fatum (Kata "
            "heimarmenes), a neo-Academic opusculum that is almost entirely "
            "philosophical, and (b) chapter 31 of the Catechetical Discourse, which "
            "summarises Carneades' moral antifatalist argumentation as a schoolroom "
            "commonplace."
        ),
        "metadata_updates": {
            "formation": "Origen via Basil and Gregory of Nazianzus; Cherniss-attested intimate Platonism",
            "amand_chapter_treatment": "Livre II Ch. IX (p. 405-439)",
            "amand_witness_role": "secondary witness via Disc. cat. 31 + Contra Fatum",
            "carneadean_topics_treated": [
                "futility of legislation",
                "absurdity of catastrophes collectives",
                "nomima barbarika (diversity of customs)",
                "useless education",
                "no praise/blame",
            ],
            "literary_works_for_freewill": [
                "Contra Fatum (PG 45, 145C-173D)",
                "Oratio Catechetica 30-31 (ed. Srawley)",
                "De Hominis Opificio 16 (PG 44, 185A)",
                "Dialogue on the Soul and the Resurrection",
            ],
        },
    },
    # ---------------------------------------------------------------------------
    # 2. Contra Fatum — enrichissement (work-shell existant → analyse Amand)
    # ---------------------------------------------------------------------------
    {
        "id": "work_gregory_contra_fatum",
        "description": (
            "Contre le Destin (Kata heimarmenes) de Grégoire de Nysse (PG 45, 145C-173D), "
            "opuscule de polémique antifataliste sous forme de lettre relatant un débat "
            "soutenu à Constantinople avec un philosophe païen stoïcisant défenseur du "
            "fatalisme astrologique intégral. Pour Amand 1945 (Livre II Ch. IX, p. 422-431), "
            "ce traité presque ignoré de la critique mérite une édition critique. Amand le "
            "découpe en deux parties : (1) exposé par le philosophe païen de la doctrine "
            "fataliste astrologique fondée sur la sympatheia universelle de Posidonios "
            "(PG 45, 148B-153C) ; (2) réfutation par Grégoire en 23 arguments accumulés "
            "(PG 45, 153C-173D). Amand identifie au moins deux arguments antiastrologiques "
            "de Carnéade directement transposés : (a) catastrophes et morts collectives "
            "(batailles, tremblements de terre, naufrages, inondations) ; (b) nomima "
            "barbarika (diversité des mœurs et coutumes humaines). L'absence quasi totale "
            "de préoccupations morales et religieuses, étonnante sous la plume du mystique "
            "cappadocien, conduit Amand à formuler l'hypothèse que la plupart des arguments "
            "ont été empruntés à une source littéraire représentant directement ou non la "
            "polémique antifataliste de Carnéade ou de ses disciples. L'argumentation "
            "morale antifataliste de Carnéade est en revanche totalement absente de "
            "l'opuscule — elle apparaîtra séparément dans le Discours catéchétique 31."
        ),
        "description_en": (
            "Gregory of Nyssa's Contra Fatum (Kata heimarmenes, PG 45, 145C-173D), an "
            "antifatalist polemical opusculum in epistolary form recounting a debate held "
            "at Constantinople with a Stoicising pagan philosopher defending integral "
            "astrological fatalism. For Amand 1945 (Book II Ch. IX, p. 422-431), this "
            "almost neglected treatise deserves a critical edition. Amand divides it into "
            "two parts: (1) the pagan philosopher's exposition of astrological fatalism "
            "founded on Posidonian universal sympatheia (PG 45, 148B-153C); (2) Gregory's "
            "refutation in 23 accumulated arguments (PG 45, 153C-173D). Amand identifies "
            "at least two Carneadean anti-astrological arguments transposed directly: "
            "(a) collective catastrophes and deaths (battles, earthquakes, shipwrecks, "
            "floods); (b) nomima barbarika (diversity of human customs and laws). The "
            "near-total absence of moral and religious concerns, striking under the pen of "
            "the Cappadocian mystic, leads Amand to hypothesise that most arguments were "
            "borrowed from a literary source representing directly or indirectly the "
            "Carneadean antifatalist polemic. Carneades' moral antifatalist argumentation "
            "is by contrast totally absent here — it will appear separately in "
            "Catechetical Discourse 31."
        ),
        "metadata_updates": {
            "composition_setting": "Constantinople debate, post-381 CE",
            "amand_argument_count": 23,
            "amand_carneadean_arguments_identified": [
                "collective catastrophes (PG 45, 165AC and 168B-169B)",
                "nomima barbarika (PG 45, 169B)",
            ],
            "amand_witness_rank": "secondary (antiastrological strand, not moral)",
            "amand_hypothesis": (
                "near-total absence of Christian moral concerns suggests dependence on a "
                "literary source representing Carneadean/Clitomachean antifatalism"
            ),
            "additional_editions": [
                {"raw": "Fronton du Duc, Paris 1615 / reprint 1638 (text deplorable per Amand)"},
                {"raw": "Migne PG 45, 145C-173D (mechanical reprint of 1638)"},
            ],
            "edition_status": "no critical edition; Amand calls for one",
        },
    },
    # ---------------------------------------------------------------------------
    # 3. Oratio Catechetica — enrichissement ch. 30-31
    # ---------------------------------------------------------------------------
    {
        "id": "work_gregory_oratio_catechetica",
        "description": (
            "Discours catéchétique de Grégoire de Nysse (Oratio Catechetica Magna, "
            "ed. Srawley 1903 ; PG 45, 9-105), exposition systématique des dogmes "
            "chrétiens à l'usage des catéchistes chargés de l'instruction des "
            "catéchumènes cultivés. Pour Amand 1945 (Livre II Ch. IX, p. 432-435), "
            "deux chapitres intéressent la transmission carnéadienne : Or. cat. 30 "
            "(ed. Srawley p. 109-113 ; PG 45, 76C-77B) où Grégoire définit la liberté "
            "humaine en termes origéniens (autexousion comme privilège divin) avec "
            "renvoi à la prohairesis ; Or. cat. 31 (ed. Srawley p. 113-114 ; PG 45, "
            "77BD) qui résume — à titre de lieu commun scolaire — un ou deux arguments "
            "éthiques de Carnéade : si l'homme est mû par une puissance supérieure, "
            "louange et blâme n'ont plus de sens, la vertu disparaît, l'impunité est "
            "assurée au crime, toute distinction entre genres d'existence est abolie. "
            "Amand note l'encadrement théologique de l'argumentation néo-académicienne "
            "(aporie de départ + réponse finale sur la responsabilité humaine) et "
            "souligne la condensation schématique d'un argument carnéadien intégré "
            "dans la doctrine origénienne du libre arbitre."
        ),
        "description_en": (
            "Gregory of Nyssa's Oratio Catechetica Magna (Catechetical Discourse, ed. "
            "Srawley 1903; PG 45, 9-105), systematic exposition of Christian dogmas for "
            "catechists instructing cultivated catechumens. For Amand 1945 (Book II "
            "Ch. IX, p. 432-435), two chapters bear on the Carneadean transmission: "
            "Or. cat. 30 (ed. Srawley p. 109-113; PG 45, 76C-77B) where Gregory defines "
            "human freedom in Origenian terms (autexousion as divine privilege) by "
            "reference to prohairesis; Or. cat. 31 (ed. Srawley p. 113-114; PG 45, 77BD) "
            "which summarises — as a schoolroom commonplace — one or two ethical "
            "arguments of Carneades: if humans are moved by a superior power, praise and "
            "blame lose meaning, virtue disappears, crime goes unpunished, all "
            "distinction between modes of life is abolished. Amand notes the theological "
            "framing of the neo-Academic argumentation (opening aporia + closing "
            "responsibility statement) and stresses the schematic condensation of a "
            "Carneadean argument embedded in Origenian free-will doctrine."
        ),
        "metadata_updates": {
            "principal_edition": "J. H. Srawley, Cambridge 1903",
            "amand_chapters_treated": ["30 (autexousion definition)", "31 (Carneadean moral argument)"],
            "amand_witness_role": "Or. cat. 31 = schoolroom Carneadean topos, not primary witness",
            "additional_editions": [
                {"raw": "J. H. Srawley, The Catechetical Oration of Gregory of Nyssa, Cambridge 1903"},
                {"raw": "Migne PG 45, 9-105"},
            ],
        },
    },
    # ---------------------------------------------------------------------------
    # 4. John Chrysostom — enrichissement portrait Amand (Ch. XII, p. 480-510)
    # ---------------------------------------------------------------------------
    {
        "id": "person_john_chrysostom_d407",
        "description": (
            "Jean Chrysostome (354-407 CE), prédicateur d'Antioche puis patriarche de "
            "Constantinople (398-404), élève de Libanios (selon une tradition rapportée "
            "par Socrate HE VI.3) et de Diodore de Tarse pour la théologie et l'exégèse. "
            "Pour Amand 1945 (Livre II Ch. XII, p. 480-532), Chrysostome est, parmi tous "
            "les Pères du IVe siècle, peut-être le plus détaché de l'hellénisme (cf. "
            "Puech III, 533). Son hellénisme est purement formel — technique oratoire, "
            "préceptes de composition et de style appris auprès des rhéteurs et "
            "sophistes — et son éloquence puise son âme dans la foi chrétienne et le "
            "zèle apostolique, non dans la Seconde Sophistique. Chrysostome accable de "
            "sarcasmes la philosophie hellénique (triobolimaios), Platon (souteneur de "
            "filles, sépulcre blanchi rempli de pourriture), Pythagore (matérialiste "
            "absurde), Aristote (goûteur de sperme humain), Zénon (incestueux), Diogène "
            "le Cynique (impudique). Mais sa polémique antifataliste contre les "
            "horoscopistes (PG 62, 507-510 et passim) reprend par amplification "
            "oratoire la vieille argumentation morale antifataliste de Carnéade. Pour "
            "Amand, Chrysostome offre, parallèlement à Eusèbe et à son rival "
            "anti-fataliste, l'un des deux textes témoins les plus détaillés et précis "
            "de l'argumentation carnéadienne — paradoxe d'un prédicateur populaire et "
            "anti-philosophe qui transmet plus fidèlement que les théologiens "
            "académiquement formés."
        ),
        "description_en": (
            "John Chrysostom (354-407 CE), preacher at Antioch then patriarch of "
            "Constantinople (398-404), pupil of Libanius (per a tradition reported by "
            "Socrates HE VI.3) and of Diodore of Tarsus for theology and exegesis. For "
            "Amand 1945 (Book II Ch. XII, p. 480-532), Chrysostom is perhaps, among all "
            "4th-century Fathers, the most detached from Hellenism (cf. Puech III, 533). "
            "His Hellenism is purely formal — oratorical technique, rules of composition "
            "and style learnt from rhetors and sophists — and his eloquence draws its "
            "soul from Christian faith and apostolic zeal, not from the Second Sophistic. "
            "Chrysostom heaps sarcasms on Hellenic philosophy (triobolimaios = "
            "three-obol-worth), Plato (procurer of girls, whitewashed tomb full of rot), "
            "Pythagoras (absurd materialist), Aristotle (taster of human sperm), Zeno "
            "(incestuous), Diogenes the Cynic (lewd). But his antifatalist polemic "
            "against horoscope-casters (PG 62, 507-510 and passim) revives by "
            "oratorical amplification Carneades' old moral antifatalist argumentation. "
            "For Amand, Chrysostom offers, alongside Eusebius and against the "
            "antifatalist counter-argument, one of the two most detailed and precise "
            "witness texts of the Carneadean argumentation — paradox of a popular "
            "preacher and anti-philosopher who transmits more faithfully than "
            "academically trained theologians."
        ),
        "metadata_updates": {
            "formation": "Libanius (per Socrates HE VI.3); Diodore of Tarsus (theology/exegesis)",
            "amand_chapter_treatment": "Livre II Ch. XII (p. 480-532)",
            "amand_witness_role": "witness_5 (Hom. after Goth ch. 6 = PG 63, 500-510)",
            "amand_assessment": "purely formal Hellenism; eloquence rooted in Christian zeal",
            "carneadean_amplifications": [
                "Hom. 1 Tim 1.3 (PG 62, 507-508): futility of activity if heimarmene rules",
                "Hom. Goth 6 (PG 63, 509-510): full witness text",
                "Hom. on perfect love 3 (PG 56, 282-283): centonic parallel",
            ],
        },
    },
    # ---------------------------------------------------------------------------
    # 5. SC79 De Providentia (work-shell) — enrichir avec contexte témoin n°6 Ps-Chrys
    # ---------------------------------------------------------------------------
    {
        "id": "sc79_chrysostomus_de_providentia",
        "description": (
            "Les Six Discours sur le Destin et la Providence (Peri heimarmenes te kai "
            "pronoias logoi hex) attribués par la tradition manuscrite à Jean Chrysostome "
            "(PG 50, 749-774). Pour Amand 1945 (Livre II Ch. XII, p. 504-510, 525-532), "
            "ces homélies — d'authenticité non assurée, non démontrablement "
            "inauthentiques non plus — constituent l'un des monuments les plus "
            "considérables de la polémique antifataliste menée par l'Église chrétienne "
            "en Orient aux IVe-Ve siècles. Elles ne réfutent pas l'astrologie savante "
            "ou populaire (différence avec Hex VI.5-7 de Basile) mais offrent une "
            "théodicée populaire et de virulentes attaques contre l'heimarmene. Amand "
            "pencherait personnellement en faveur de l'authenticité, mais traite "
            "néanmoins le Discours V (PG 50, 765-768) comme attribué à un "
            "Pseudo-Chrysostome — d'où le témoin n°6 de la reconstruction carnéadienne. "
            "Les six discours résumés par Amand : I (harmonie de l'âme chrétienne), II "
            "(violente sortie contre les chrétiens fatalistes ; incompatibilité libre "
            "arbitre/heimarmene), III (condamnation énergique de la genesis), IV "
            "(justice divine et jugement dernier), V (texte témoin n°6 = neuf arguments "
            "carnéadiens + récapitulation oratoire 'si genesis est, krisis ouk est…'), "
            "VI (anti-gourmandise, lien lâche)."
        ),
        "description_en": (
            "The Six Discourses on Fate and Providence (Peri heimarmenes te kai pronoias "
            "logoi hex) attributed by manuscript tradition to John Chrysostom (PG 50, "
            "749-774). For Amand 1945 (Book II Ch. XII, p. 504-510, 525-532), these "
            "homilies — of unsecured authenticity, neither demonstrably inauthentic — "
            "constitute one of the most considerable monuments of antifatalist polemic "
            "waged by the Eastern Church in the 4th-5th centuries. They do not refute "
            "scholarly or popular astrology (unlike Basil's Hex VI.5-7) but offer a "
            "popular theodicy and virulent attacks on heimarmene. Amand personally "
            "inclines toward authenticity but nonetheless treats Discourse V (PG 50, "
            "765-768) as attributed to a Pseudo-Chrysostom — hence witness 6 of the "
            "Carneadean reconstruction. The six discourses as summarised by Amand: I "
            "(harmony of the Christian soul), II (violent attack on Christian fatalists; "
            "free-will/heimarmene incompatibility), III (vigorous condemnation of "
            "genesis), IV (divine justice and final judgment), V (witness text n°6 = "
            "nine Carneadean arguments + oratorical recapitulation 'if genesis exists, "
            "judgment does not'…), VI (anti-gluttony, loose connection)."
        ),
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. XII §III (p. 504-510 = witness n°6 at p. 527-532)",
            "amand_authenticity_view": "Amand inclines toward genuine; Montfaucon's negative arguments inconclusive",
            "amand_pseudo_chrysostom_tag": "Discourse V treated as witness n°6 (Ps-Chrys per Amand)",
            "discourses_summary": [
                "I — harmony of the Christian soul",
                "II — attack on Christian fatalists; libre arbitre vs heimarmene",
                "III — condemnation of genesis as diabolical pretext",
                "IV — divine justice and final judgment",
                "V — witness text 6 (9 Carneadean arguments + recapitulation)",
                "VI — anti-gluttony (loosely connected)",
            ],
            "editions": [
                {"raw": "Montfaucon, PG 50, 749-774 (Colbertinus 49 only)"},
                {"raw": "SC 79 (Malingrey, ed. Sources Chrétiennes; ingested as sc79_*)"},
            ],
        },
    },
    # ---------------------------------------------------------------------------
    # 6. Nemesius of Emesa — enrichissement portrait Amand (Ch. XIV)
    # ---------------------------------------------------------------------------
    {
        "id": "person_nemesius_emesa_4c_ce",
        "description": (
            "Némésios d'Émèse (fl. fin IVe / début Ve s. CE), évêque d'Émèse sur "
            "l'Oronte (aujourd'hui Homs en Syrie), auteur du Traité de la nature de "
            "l'homme (Peri physeos anthropou), premier manuel d'anthropologie "
            "systématique dû à une plume chrétienne. Pour Amand 1945 (Livre II Ch. XIV, "
            "p. 549-569), Némésios est un philosophe chrétien éclectique dont la "
            "tendance dominante est néo-platonicienne, d'allure alexandrine ou "
            "scientifique, comparable à Hypatie, Synésios de Cyrène, Hiéroclès "
            "d'Alexandrie. Il s'intéresse vivement à l'anatomie, à la physiologie et "
            "à la médecine sous la direction de Galien. Ses autorités principales : "
            "Platon, Aristote (l'Éthique à Nicomaque III, 1-8 surtout), Posidonios (via "
            "Origène Comm. in Gen. et Galien), Porphyre, Plotin, Numénios, Galien. "
            "Pour la question du libre arbitre, Némésios suit pas à pas un commentaire "
            "péripatéticien perdu sur l'Éthique à Nicomaque (datant probablement du IIe "
            "ou IIIe siècle), interprété en sens indéterministe, qui a aussi fourni une "
            "polémique anti-heimarmene aux chapitres 35-38. Pour Amand, Némésios figure "
            "parmi les témoins secondaires : son chapitre 35 ouvre par un résumé sec "
            "et squelettique de l'argumentation morale antifataliste de Carnéade — "
            "celle-ci étant rapetissée et momifiée par les faiseurs de manuels en une "
            "vulgaire recette d'école."
        ),
        "description_en": (
            "Nemesius of Emesa (fl. late 4th / early 5th c. CE), bishop of Emesa on the "
            "Orontes (modern Homs in Syria), author of De Natura Hominis (Peri physeos "
            "anthropou), the first systematic anthropology manual written by a Christian. "
            "For Amand 1945 (Book II Ch. XIV, p. 549-569), Nemesius is an eclectic "
            "Christian philosopher whose dominant tendency is Neoplatonist of the "
            "Alexandrian or scientific stripe, comparable to Hypatia, Synesius of "
            "Cyrene, Hierocles of Alexandria. He is deeply engaged with anatomy, "
            "physiology and medicine under Galen's guidance. His chief authorities: "
            "Plato, Aristotle (Nicomachean Ethics III, 1-8 especially), Posidonius (via "
            "Origen's Comm. in Gen. and Galen), Porphyry, Plotinus, Numenius, Galen. On "
            "free will, Nemesius follows step by step a lost Peripatetic commentary on "
            "the Nicomachean Ethics (probably 2nd or 3rd century), interpreted "
            "indeterministically, which also supplied an anti-heimarmene polemic in "
            "chapters 35-38. For Amand, Nemesius features among the secondary witnesses: "
            "his chapter 35 opens with a dry skeletal summary of Carneades' moral "
            "antifatalist argumentation — itself shrunken and mummified by manual-makers "
            "into a vulgar schoolroom recipe."
        ),
        "metadata_updates": {
            "amand_chapter_treatment": "Livre II Ch. XIV (p. 549-569)",
            "amand_witness_role": "secondary witness via Nat. Hom. 35 summary",
            "amand_principal_sources": [
                "Aristotle EN III, 1-8 (via lost Peripatetic commentary 2nd-3rd c.)",
                "Origen Comm. in Gen. (for ch. 1 anthropology and the encomium of man)",
                "Galen (Peri apodeixeos, Peri Hippokratous kai Platonos dogmaton)",
                "Posidonius (via Origen and Galen)",
                "Porphyry Symmikta zetemata",
            ],
            "amand_dating_view": "late 4th / early 5th c. (siding with Bardenhewer, Domanski, Skard)",
            "amand_assessment": (
                "first systematic anthropology by a Christian; Aristotelian on free will, "
                "Platonist on soul, eclectic and scientific; transmits Carneades only as "
                "manual-shrunk topos"
            ),
        },
    },
    # ---------------------------------------------------------------------------
    # 7. De Natura Hominis — enrichissement (work-shell)
    # ---------------------------------------------------------------------------
    {
        "id": "work_nemesius_de_nat_hom",
        "description": (
            "Traité de la nature de l'homme (Peri physeos anthropou) de Némésios "
            "d'Émèse (fin IVe / début Ve s.), premier manuel d'anthropologie "
            "systématique chrétien (PG 40, 504-817 ; éd. Matthaei Halle 1802). Pour "
            "Amand 1945 (Livre II Ch. XIV, p. 550-569), l'œuvre couvre : ch. 1 nature "
            "intermédiaire et microcosmique de l'homme ; ch. 2-3 âme et union "
            "âme-corps ; ch. 7-13 fonctions sensorielles, imagination, mémoire, "
            "intelligence (sources Porphyre + Galien) ; ch. 16-28 passions et "
            "physiologie (Posidonios via Galien) ; ch. 29-34 et 39-41 théorie "
            "aristotélicienne du volontaire, de la prohairesis, du libre arbitre "
            "(via commentaire péripatéticien perdu sur EN III) ; ch. 35-38 polémique "
            "antifataliste structurée (anti-fatalisme astrologique intégral avec "
            "résumé sec de l'argumentation morale carnéadienne PG 40, 741BC ; "
            "anti-fatalisme métaphysique de Chrysippe et Philopator ; anti-fatalisme "
            "astrologique mitigé des Égyptiens et leurs rites apotropaïques ; "
            "anti-fatalisme atténué du platonisme moyen pseudo-Plutarque) ; ch. 42-44 "
            "défense de la Providence. L'œuvre, dépourvue de conclusion et apparemment "
            "inachevée, manque parfois d'unité mais constitue un éclectisme "
            "philosophique cohérent fondé sur Aristote + Posidonios + Galien + "
            "Néoplatoniciens, refondu sous norme dogmatique chrétienne."
        ),
        "description_en": (
            "Nemesius of Emesa's On the Nature of Man (Peri physeos anthropou) (late "
            "4th / early 5th c.), the first systematic Christian anthropology manual (PG "
            "40, 504-817; ed. Matthaei Halle 1802). For Amand 1945 (Book II Ch. XIV, "
            "p. 550-569), the work covers: ch. 1 intermediate microcosmic nature of "
            "man; ch. 2-3 soul and soul-body union; ch. 7-13 sense-functions, "
            "imagination, memory, intelligence (sources Porphyry + Galen); ch. 16-28 "
            "passions and physiology (Posidonius via Galen); ch. 29-34 and 39-41 "
            "Aristotelian theory of voluntary, prohairesis, free will (via lost "
            "Peripatetic commentary on EN III); ch. 35-38 structured antifatalist "
            "polemic (anti integral astrological fatalism with dry summary of "
            "Carneadean moral argumentation PG 40, 741BC; anti Chrysippus-Philopator "
            "metaphysical fatalism; anti Egyptian apotropaic-mitigated astrological "
            "fatalism; anti Middle-Platonic Pseudo-Plutarchean attenuated fatalism); "
            "ch. 42-44 defence of Providence. The work, lacking a conclusion and "
            "apparently unfinished, sometimes lacks unity but constitutes a coherent "
            "philosophical eclecticism founded on Aristotle + Posidonius + Galen + "
            "Neoplatonists, recast under Christian doctrinal norm."
        ),
        "metadata_updates": {
            "composition_date": "late 4th / early 5th c. CE (siding with Amand vs late dating)",
            "amand_antifatalism_chapters": ["35 (integral)", "36 (apotropaic)", "37 (Middle Platonist mention)", "38 (Middle Platonist refutation)"],
            "amand_witness_text": "PG 40, 741 BC, l. 18-33 (dry Carneadean summary at Nat. Hom. 35)",
            "principal_source_for_freewill": "lost Peripatetic commentary on EN III, 1-8 (2nd-3rd c., indeterminist)",
            "additional_editions": [
                {"raw": "C. F. Matthaei, Halle 1802 (in-12, 410 + 128 p.)"},
                {"raw": "Migne PG 40, 504-817 (reprints Matthaei)"},
                {"raw": "Edition critique en préparation par F. Lammert (per Skard 1940)"},
            ],
            "absence_of_critical_edition_per_amand": True,
        },
    },
]
