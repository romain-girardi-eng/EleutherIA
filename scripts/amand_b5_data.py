"""B5 data : REPAIRS (vide pour B5) + UPDATES sur 3 nœuds Origène-native pré-existants."""
from __future__ import annotations
from typing import Any

from amand_b5_utils import md_base  # type: ignore

# ============================================================================
# REPAIRS : Aucun en B5 (pas de run B5 partiel antérieur, working tree propre).
# ============================================================================

REPAIRS: dict[str, dict[str, Any]] = {}


# ============================================================================
# UPDATES : 3 nœuds Origène-native pré-existants enrichis avec B5 metadata Amand
# ============================================================================

UPDATES: dict[str, dict[str, Any]] = {
    "person_origen_alexandria_185_254ce_s9t0u1v2": dict(
        md_additions={
            "amand1945_witness_role": "witness_1_patristic_for_carneadean_moral_reconstruction",
            "amand1945_treated_in": "Livre II Ch. V (p. 275-325, ll. 14740-17120)",
            "amand1945_witness_passages_principal": [
                "Comm. in Gen. III via Philocalie 23 (Robinson 1893, p. 187-212)",
                "De Principiis III.1 (Koetschau Origenes Werke V p. 195-244)",
                "Contra Celsum IV.3 + III.75 + VIII.15 (Koetschau Origenes Werke II)",
                "De Oratione 29.13, 29.15 (Koetschau Origenes Werke II p. 387-391)",
            ],
            "amand1945_judgement_fr": (
                "Origène est le premier témoin patristique de la lignée carnéadienne anti-fataliste. "
                "Sa double polarité Bible-Platon (« la Bible et Platon constituent les pôles de sa vie spirituelle ») "
                "réfute les lectures unilatérales de De Faye/Hal Koch (philosophe-platonicien égaré dans l'Église) et "
                "de Bardy (purement bibliste-ecclésiastique). Origène est pour Amand « le premier maître éminent d'un "
                "système de gnose chrétienne », et le premier théologien à problématiser méthodiquement la conciliation "
                "entre prescience divine et libre arbitre humain. Sa méthode signature : « transposer partout des preuves "
                "philosophiques et abstraites en arguments théologiques » (Amand p. 320), en élargissant la perspective "
                "morale par la considération des sanctions d'outre-tombe."
            ),
            "amand1945_judgement_en": (
                "Origen is the first patristic witness in the Carneadean anti-fatalist lineage. "
                "His Bible-Plato double polarity refutes unilateral readings (De Faye/Hal Koch as Platonist philosopher "
                "stranded in the Church; Bardy as pure ecclesiastical biblicist). For Amand, Origen is the first eminent "
                "master of a Christian gnosis system, and the first theologian to methodically problematize the "
                "reconciliation of divine foreknowledge and human free will. His signature method: 'everywhere transpose "
                "philosophical and abstract proofs into theological arguments' (Amand p. 320), broadening the moral "
                "perspective through the consideration of eschatological sanctions."
            ),
            "amand1945_carneadean_transposition_signature": True,
            "amand1945_first_christian_prescience_problem": True,
            "amand1945_first_precession_polemicist": True,
            "amand1945_double_polarity_bible_plato": True,
            "amand1945_christian_gnosis_master": True,
        },
        description_append=(
            "\n\n**Témoin n°1 patristique (Amand 1945)** — Origène est selon Amand de Mendieta le premier témoin "
            "patristique de la lignée carnéadienne anti-fataliste reconstruite. Sa polémique antiastrologique "
            "(Comm. in Gen. III via Philocalie 23) déploie les arguments moraux de Carnéade transposés sur le plan "
            "théologique chrétien. Origène est aussi le premier théologien chrétien à problématiser méthodiquement "
            "la conciliation entre prescience divine et libre arbitre humain (Philocalie 23.7-11), problème dont "
            "la solution sera entérinée par la théologie ecclésiastique postérieure. Méthode signature : transposition "
            "partout des preuves philosophiques en arguments théologiques, élargie par l'eschatologie chrétienne."
        ),
        description_en_append=(
            "\n\n**Witness n°1 Patristic (Amand 1945)** — Origen is, according to Amand de Mendieta, the first "
            "patristic witness in the reconstructed Carneadean anti-fatalist lineage. His anti-astrological polemic "
            "(Comm. in Gen. III via Philocalia 23) deploys Carneades' moral arguments transposed onto the Christian "
            "theological plane. Origen is also the first Christian theologian to methodically problematize the "
            "reconciliation of divine foreknowledge and human free will (Philocalia 23.7-11), a solution that would "
            "be endorsed by subsequent ecclesiastical theology. Signature method: pervasive transposition of "
            "philosophical proofs into theological arguments, broadened by Christian eschatology."
        ),
    ),
    "argument_origen_anti_astrological": dict(
        md_additions={
            "amand1945_witness_role": "primary_argument_of_witness_1_origen",
            "amand1945_locus": "Comm. in Gen. III via Philocalie 23 (Robinson 1893, p. 187-212)",
            "amand1945_structure_4_problems": [
                "Problème 1 : prescience divine vs libre arbitre (Phil. 23.7-11)",
                "Problème 2 : astres = signes, non causes efficientes (Phil. 23.14-16)",
                "Problème 3 : l'homme ne peut connaître exactement les signes (Phil. 23.17-19)",
                "Problème 4 : connaissance réservée aux anges (Phil. 23.20-21)",
            ],
            "amand1945_structure_3_parts": [
                "Première partie : réfutation par arguments moraux carnéadiens + prescience (Phil. 23.1-2, 7-11)",
                "Deuxième partie : 4 problèmes méthodiques (Phil. 23.6-21)",
                "Troisième partie : citation pseudo-clémentine ch. 14 (Phil. 23.22)",
            ],
            "amand1945_pseudo_clementine_dependency": True,
            "amand1945_eusebius_transcription": "Eusèbe, Préparation évangélique VI.11.1-81 (Dindorf p. 324-343)",
            "amand1945_dating": "Comm. Gen. III achevé vers 220, après De Principiis (Cadiou 1930)",
            "amand_cited_edition_unverified": [
                "Robinson J.A., The Philocalia of Origen, Cambridge University Press 1893, p. 187-212",
                "Koetschau P., Origenes Werke I-II, GCS 2-3, Leipzig 1899",
                "Preuschen E., Origenes Werke IV (Comm. Jean), GCS 10, Leipzig 1903",
            ],
        },
        description_append=(
            "\n\n**Amand 1945 — structure et localisation** — Amand de Mendieta identifie une structure tripartite "
            "soigneusement organisée dans la dissertation antiastrologique d'Origène (Comm. in Gen. III, transmise "
            "par la Philocalie 23 de Basile et Grégoire de Nazianze, Robinson 1893 p. 187-212) : (1) première partie "
            "réfutation par arguments moraux carnéadiens + premier examen de la prescience (Phil. 23.1-2, 7-11) ; "
            "(2) deuxième partie quatre problèmes méthodiques : prescience-libre arbitre, astres-signes-non-causes, "
            "ignorance humaine des signes, connaissance angélique (Phil. 23.6-21) ; (3) troisième partie citation "
            "pseudo-clémentine du ch. 14 (Phil. 23.22). Eusèbe la transcrit quasi-littéralement dans Prép. Évang. "
            "VI.11.1-81. Composition vers 220, après De Principiis (Cadiou)."
        ),
        description_en_append=(
            "\n\n**Amand 1945 — structure and locus** — Amand de Mendieta identifies a carefully organized tripartite "
            "structure in Origen's anti-astrological dissertation (Comm. in Gen. III, transmitted by Basil and Gregory "
            "of Nazianzus's Philocalia 23, Robinson 1893 p. 187-212): (1) first part Carneadean moral refutation + "
            "preliminary foreknowledge discussion (Phil. 23.1-2, 7-11); (2) second part four methodical problems: "
            "foreknowledge-freewill, stars-as-signs-not-causes, human ignorance of signs, angelic knowledge (Phil. "
            "23.6-21); (3) third part pseudo-Clementine citation from ch. 14 (Phil. 23.22). Eusebius transcribes it "
            "almost verbatim in Praep. Evang. VI.11.1-81. Composition c. 220 CE, after De Principiis (Cadiou)."
        ),
    ),
    "argument_origens_de_principiis_argument_for_free_will_93d043fc": dict(
        md_additions={
            "amand1945_witness_role": "principal_doctrinal_basis_of_witness_1_origen",
            "amand1945_locus": "Princ. III.1, 2-5 (Koetschau Origenes Werke V p. 196,3 — 201,6)",
            "amand1945_philosophical_dependencies": [
                "Épictète Manuel et Entretiens (terminologie τὸ ἐφ᾽ ἡμῖν, lutte interne contre représentations)",
                "Alexandre d'Aphrodise De Fato (hiérarchie des êtres, raison comme corollaire de la liberté)",
                "Aristote Eth. Nic. (analyses précises sur l'imputabilité)",
                "Chrysippe (terminologie anthropologique : φαντασία, συγκατάθεσις, τὸ ἐφ᾽ ἡμῖν)",
            ],
            "amand1945_synkatathesis_locus": "Origène localise précisément le libre arbitre dans la συγκατάθεσις : « Ce qui ne dépend pas de nous, c'est la représentation ; ce qui dépend de nous (τὸ ἐφ᾽ ἡμῖν), c'est le jugement et le choix »",
            "amand1945_possibilitas_utriusque_partis": "Propriété essentielle et active de l'être créé raisonnable, qui le rend laudis et culpae capax (Rufin's translation, Princ. I.5,2 Koetschau p. 70,4-7)",
            "amand1945_hierarchy_of_beings": "Minéraux (mouvement externe) → plantes (principe vital sans âme) → animaux (âme + imagination) → homme (raison + liberté). Raison = corollaire inévitable de la liberté chez les créatures.",
            "evidenced_by_passage": [
                "sc268_origenes_peri_archon_iii_chap1",
                "sc268_origenes_peri_archon_iii_chap1_en",
            ],
            "amand_cited_edition_unverified": [
                "Koetschau P., Origenes Werke V. De principiis (Περὶ ἀρχῶν). GCS 22, Leipzig 1913, p. 195-244 (le ch. III.1 περὶ αὐτεξουσίου)",
                "Bardy G., Origène. Coll. Les moralistes chrétiens. Paris 1931, p. 39-40 (trad. fr.)",
            ],
        },
        description_append=(
            "\n\n**Amand 1945 — base doctrinale du témoin n°1** — Amand de Mendieta identifie le ch. III.1 du Περὶ "
            "ἀρχῶν (Koetschau p. 195-244 = 196,3 — 201,6 pour la démonstration philosophique) comme la base éthique "
            "et psychologique de tout le système de philosophie religieuse d'Origène. L'argument procède en quatre "
            "moments : (1) hiérarchie des êtres (minéraux/plantes/animaux/homme) où l'homme seul se règle d'après la "
            "raison ; (2) la raison a pour corollaire inévitable la liberté de choisir entre φαντασίαι ; (3) ce qui "
            "ne dépend pas de nous c'est la représentation, mais le jugement et le choix dépendent de nous (τὸ ἐφ᾽ "
            "ἡμῖν) ; (4) l'expérience interne confirme la déduction (homme chaste peut suivre ou dédaigner la "
            "prostituée). Amand note les dépendances philosophiques précises : Épictète, Alexandre De Fato, et "
            "indirectement Aristote/Chrysippe. La propriété active = *possibilitas utriusque partis* (laudis et "
            "culpae capax, Princ. I.5,2)."
        ),
        description_en_append=(
            "\n\n**Amand 1945 — doctrinal basis of witness n°1** — Amand de Mendieta identifies De Principiis III.1 "
            "(Koetschau pp. 195-244, esp. 196,3—201,6 for the philosophical demonstration) as the ethical and "
            "psychological foundation of Origen's entire religious philosophy. The argument proceeds in four moments: "
            "(1) hierarchy of beings (minerals/plants/animals/humans) where only humans are governed by reason; "
            "(2) reason has as inevitable corollary the freedom to choose among φαντασίαι; (3) what does not depend "
            "on us is the representation, but judgment and choice do depend on us (τὸ ἐφ᾽ ἡμῖν); (4) inner experience "
            "confirms the deduction. Amand identifies precise philosophical dependencies: Epictetus, Alexander De "
            "Fato, indirectly Aristotle/Chrysippus. The active property = *possibilitas utriusque partis* (laudis et "
            "culpae capax, Princ. I.5,2)."
        ),
    ),
}
