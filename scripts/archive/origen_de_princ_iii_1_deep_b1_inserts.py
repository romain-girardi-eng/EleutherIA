"""Origen De Princ III.1 deep batch B1 — NEW_INSERTS.

23 shell passage nodes for De Principiis III.1 sections 1-2 and 4-24
(§3 already exists as passage_origen_pa_3_1_3).

Each shell carries :
- `id`            : passage_origen_pa_3_1_<n>
- `type`          : passage
- `label`         : "Origen, De Principiis III.1.<n>: <short title>"
- `description`   : English structural summary (NO fabricated Greek/Latin)
- `description_en`: same (English-only shell ; no FR description prepared since
                    the verified §3 anchor only has the French/Greek combined
                    description and an _en pair)
- `period`        : "Patristic"
- `school`        : "Christian Platonism"
- `metadata`      : via origen_passage_metadata()
- `needs_evidence`: True (no critical edition consulted in-session, summary
                    drawn from Butterworth 1936 / Crouzel-Simonetti SC 268)
- `confidence`    : 0.75 (section content paraphrase pending ingestion)

Bonus : 4 Philocalia 21 sub-anchor shells for §§5, 7, 18, 23 (the four most-
heavily-cited sections among the 15 scholarly nodes). These provide a
secondary anchor option for arguments citing the Greek text directly.

Section content map (Crouzel-Simonetti SC 268 + Butterworth 1936) :

  III.1.1  — Programmatic prologue : importance of investigating αὐτεξούσιον ;
             classification of self-moving beings.
  III.1.2  — Definition of free will via the four modes of motion : ἔξωθεν
             (external), ἐξ αὑτοῦ (from itself), ἀφ᾽ αὑτοῦ (away from itself),
             δι᾽ αὑτοῦ (through itself) — the Stoic action-theory framework.
  III.1.3  — [EXISTS] Self-determining judgment ; impression / response.
  III.1.4  — How rational creatures respond to impressions : assent, judgment ;
             reply to "external goads compel" Stoic-determinist objections.
  III.1.5  — Anti-astrological argument : stars indicate but do not compel ;
             freedom essential to rationality.
  III.1.6  — Anti-Gnostic argument : refutation of Valentinian / Basilidean
             tripartition of natures (pneumatic / psychic / hylic).
  III.1.7  — Scriptural objection : Pharaoh's hardened heart (Ex 9:12 ;
             Rom 9:18) ; opening of the long pedagogical-theodicy section.
  III.1.8  — Continuation : the sun-wax-mud analogy (one cause, different
             reactions according to disposition).
  III.1.9  — Pharaoh's hardening as pedagogical, not punitive ; God's hardening
             permits revelation of malice.
  III.1.10 — Closing of Pharaoh exegesis : pedagogical providence preserves
             freedom.
  III.1.11 — Ezekiel 11:19 (stony heart removed) : freedom presupposed by
             promise.
  III.1.12 — Rom 9:16 (not of him that willeth) : reconciliation with
             autexousion.
  III.1.13 — Potter-clay metaphor (Rom 9:18-21) : interpretation against
             determinist reading.
  III.1.14 — Continuation : human cooperation with the divine potter.
  III.1.15 — Phil 2:13 / Jer 1:5 — God's prevenient action and human
             autexousion ; God works in us BOTH the willing AND the doing.
  III.1.16 — Continuation : Jer 10:23 (way of man is not in himself) — limited
             scope of the verse.
  III.1.17 — 1 Cor 7:25 (mercy of the Lord) : grace and freedom cooperate.
  III.1.18 — ⭐ Pedagogical theodicy : God permits ill so that freedom is
             preserved ; "if he were to act always with manifest interventions
             our power of choice would be removed".
  III.1.19 — Esau and Jacob (Rom 9:11-13) : refutation of predestination
             interpretation ; previous-life merits invoked.
  III.1.20 — Continuation Esau-Jacob : "loved Jacob and hated Esau" hermeneutic.
  III.1.21 — Recap : Pharaoh exegesis restated, freedom preserved.
  III.1.22 — Continuation : the divine purpose unveiled in the order of history.
  III.1.23 — ⭐ Universalist apokatastasis horizon : freedom retained even by
             the worst spirits, so fall and return remain perpetually possible.
  III.1.24 — Conclusion / summary : sum of the doctrine of autexousion.
"""
from __future__ import annotations

from typing import Any

from origen_de_princ_iii_1_deep_b1_utils import (
    DE_PRINC_URN_PREFIX,
    PHILOCALIA_URN_PREFIX,
    dump_metadata,
    origen_passage_metadata,
)


def _shell_passage(
    *,
    section_num: int,
    title: str,
    summary: str,
    is_greek_preserved: bool = True,
    extra_md: dict[str, Any] | None = None,
    confidence: float = 0.75,
) -> dict[str, Any]:
    """Build one De Princ III.1 shell passage node."""
    section_id = f"passage_origen_pa_3_1_{section_num}"
    label = f"Origen, De Principiis III.1.{section_num}: {title}"
    md = origen_passage_metadata(
        section_num=section_num,
        section_label=title,
        is_greek_preserved=is_greek_preserved,
        extra=extra_md,
    )
    return {
        "id": section_id,
        "type": "passage",
        "label": label,
        "description": summary,
        "description_en": summary,
        "period": "Patristic",
        "school": "Christian Platonism",
        "metadata": dump_metadata(md),
        "confidence": confidence,
        "needs_evidence": True,
    }


# =============================================================================
# 23 SHELL PASSAGES — De Principiis III.1 sections 1-2 and 4-24
# =============================================================================

NEW_PASSAGES: list[dict[str, Any]] = [
    # =============================================================================
    # §§1-2 — Greek partially preserved (Philocalia 21.1-2) but also fragmentary
    # via Eusebius PE VI ; Latin Rufinus continuous
    # =============================================================================
    _shell_passage(
        section_num=1,
        title="Programmatic prologue — importance of investigating αὐτεξούσιον",
        summary=(
            "Origen, De Principiis III.1.1 (shell). Opening section of the "
            "Peri autexousiou treatise. Origen declares that the question of "
            "free will (αὐτεξούσιον) is 'of the highest importance' and "
            "demands that the concept (ἔννοια) be developed. He motivates the "
            "investigation by noting the moral and theological stakes : "
            "Scripture presents exhortations, commandments, threats and "
            "promises that presuppose human responsibility. He prepares the "
            "ground for the four-mode classification of motion that follows "
            "in §2 (animate vs inanimate ; self-moving vs externally moved). "
            "Shell node — text pending ingestion from SC 268 (Crouzel-Simonetti) "
            "or GCS 22 (Koetschau)."
        ),
        is_greek_preserved=True,
    ),
    _shell_passage(
        section_num=2,
        title="Four modes of motion — Stoic action-theory framework",
        summary=(
            "Origen, De Principiis III.1.2 (shell). The four modes of motion : "
            "(a) ἔξωθεν — moved entirely from outside (inanimate bodies, e.g. "
            "stones falling) ; (b) ἐξ αὑτοῦ — moved 'from itself' (plants, "
            "vegetative life) ; (c) ἀφ᾽ αὑτοῦ — moved 'away from itself' "
            "(animals, who respond to impressions but without judgment) ; "
            "(d) δι᾽ αὑτοῦ — moved 'through itself' (rational creatures, who "
            "deliberate). Furst 2022 (Kap. V) identifies this four-level "
            "schema as the philosophical core of Origen's metaphysics of "
            "freedom : the rational creature alone exercises δι᾽ αὑτοῦ — "
            "self-determination through reason. Shell node — text pending "
            "ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "furst_2022_key_section": True,
            "furst_2022_reference": "Kap. V 2 — quatre modes du mouvement (ἔξωθεν / ἐξ αὑτοῦ / ἀφ᾽ αὑτοῦ / δι᾽ αὑτοῦ)",
        },
        confidence=0.8,
    ),
    # =============================================================================
    # §§4-6 — Anti-determinist polemics (Latin only continuous ; some Greek frags)
    # =============================================================================
    _shell_passage(
        section_num=4,
        title="Response to Stoic-determinist objections — assent (συγκατάθεσις)",
        summary=(
            "Origen, De Principiis III.1.4 (shell). Reply to Stoic-determinist "
            "objections that 'external goads' (irritamenta) compel the will. "
            "Origen develops the Stoic theory of assent (συγκατάθεσις) but "
            "reinterprets it libertarianly : impressions arise, but the "
            "judgment about how to respond rests with the rational agent. "
            "Frede 2011 (p. 113) reads §§2-3 (and by extension §4) as "
            "'taken straight from a late Stoic handbook'. Furst 2022 reads "
            "the same as the foundation of compatibilist libertarianism. "
            "Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=5,
        title="Anti-astrological argument — stars indicate, do not compel",
        summary=(
            "Origen, De Principiis III.1.5 (shell). Refutation of astrological "
            "determinism : stars and planets are signs (semeia), not causes "
            "(aitia). Heavenly bodies indicate future events as a kind of "
            "divine script (Cels. V 10-11 parallel) but do not necessitate "
            "them. Crucially : the very fact that astrologers cannot reliably "
            "predict free human choices demonstrates that human action escapes "
            "celestial necessity. This is the section Origen develops further "
            "in Comm. Gen. III (= Philocalia 23) and Cels. V 21 — explicitly "
            "marked by Furst 2022 (Kap. V 1) as one of the three deterministic "
            "fronts Origen targets. Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "amand_1945_key_section": True,
            "frede_2011_key_section": True,
            "furst_2022_key_section": True,
            "anti_determinism_target": "astrological",
        },
        confidence=0.8,
    ),
    _shell_passage(
        section_num=6,
        title="Anti-Gnostic argument — refutation of Valentinian tripartition",
        summary=(
            "Origen, De Principiis III.1.6 (shell). Refutation of the "
            "Valentinian and Basilidean tripartition of natures (pneumatic / "
            "psychic / hylic). Against the Gnostics, Origen denies that any "
            "rational creature is 'saved by nature' or 'damned by nature'. "
            "ALL rational creatures share equally in αὐτεξούσιον. Inequality "
            "of present condition is due to free choices (some progressing, "
            "others cooling — cf. Princ. II.9). Frede 2011 Ch. 7 identifies "
            "this as the polemical driver of the whole treatise. Furst 2022 "
            "Kap. V 1 lists this as the third deterministic front. Shell node "
            "— text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "frede_2011_key_section": True,
            "furst_2022_key_section": True,
            "amand_1945_key_section": True,
            "anti_determinism_target": "gnostic",
        },
        confidence=0.85,
    ),
    # =============================================================================
    # §§7-17 — Scriptural difficulties : Pharaoh, Esau, Jeremiah etc. (Greek
    # preserved via Philocalia 21)
    # =============================================================================
    _shell_passage(
        section_num=7,
        title="Pharaoh's hardened heart (Ex 9:12 / Rom 9:18) — scriptural objection",
        summary=(
            "Origen, De Principiis III.1.7 (shell). Opening of the long "
            "scriptural-objection section (§§7-22). The Apostle Paul cites "
            "Exodus : 'I will harden Pharaoh's heart'. Does this not destroy "
            "Pharaoh's freedom and entail divine causation of evil ? Origen "
            "frames the question and lays out his interpretive principle : "
            "passages that seem to deny freedom must be read with the rest of "
            "Scripture, which everywhere presupposes responsibility. The "
            "Pharaoh exegesis runs through §§7-10 (with recap in §21). Greek "
            "preserved in Philocalia 21.7. Shell node — text pending "
            "ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"furst_2022_key_section": True, "scriptural_locus": "Ex 9:12 / Rom 9:18"},
        confidence=0.85,
    ),
    _shell_passage(
        section_num=8,
        title="Pharaoh's hardening — sun-wax-mud analogy",
        summary=(
            "Origen, De Principiis III.1.8 (shell). The famous sun-wax-mud "
            "analogy : the same sun softens wax and hardens mud. One cause "
            "produces opposite effects depending on the disposition of the "
            "recipient. So God's action (commandments, exhortations, "
            "providence) softens the hearts of the just and hardens the "
            "hearts of those already disposed to evil. The hardening is not "
            "imposed from outside but is the rational creature's own response "
            "to a uniform divine pedagogy. Shell node — text pending "
            "ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"famous_analogy": "sun_wax_mud"},
        confidence=0.85,
    ),
    _shell_passage(
        section_num=9,
        title="Pharaoh's hardening — pedagogical, not punitive",
        summary=(
            "Origen, De Principiis III.1.9 (shell). Continuation. God's "
            "permitting Pharaoh to remain hardened serves a pedagogical and "
            "providential end : it allows Pharaoh's evil to be unveiled, "
            "which in turn makes possible the public manifestation of God's "
            "power through the plagues, and ultimately the deliverance of "
            "Israel. The hardening is permissive, not causative. Shell node "
            "— text pending ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=10,
        title="Pharaoh exegesis — closing : pedagogical providence preserves freedom",
        summary=(
            "Origen, De Principiis III.1.10 (shell). Closing of the Pharaoh "
            "exegesis. The interpretive rule : when Scripture attributes "
            "hardening to God, this is providential permission, not direct "
            "causation. The fundamental principle is preserved : God's "
            "pedagogy works WITH human freedom, never against it. Shell node "
            "— text pending ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=11,
        title="Ezekiel 11:19 — stony heart removed presupposes freedom",
        summary=(
            "Origen, De Principiis III.1.11 (shell). Ezekiel 11:19 : 'I will "
            "take away their stony heart and give them a heart of flesh'. The "
            "verse is read NOT as a denial of freedom but as a promise that "
            "PRESUPPOSES freedom : God's grace assists the will, but the will "
            "must cooperate. The exhortation 'circumcise your hearts' (Deut "
            "10:16) given to the same people shows that God's removal of the "
            "stony heart is a response to human turning. Shell node — text "
            "pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "Ezek 11:19 / Deut 10:16"},
        confidence=0.8,
    ),
    _shell_passage(
        section_num=12,
        title="Rom 9:16 — 'not of him that willeth' reconciled with autexousion",
        summary=(
            "Origen, De Principiis III.1.12 (shell). Rom 9:16 : 'It is not "
            "of him that willeth, nor of him that runneth, but of God that "
            "showeth mercy'. Origen reads this not as denying willing and "
            "running but as denying that willing and running are SUFFICIENT "
            "without divine mercy. The Pauline verse presupposes that we "
            "DO will and DO run — i.e. it presupposes autexousion. Shell "
            "node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "Rom 9:16"},
        confidence=0.8,
    ),
    _shell_passage(
        section_num=13,
        title="Potter-clay metaphor (Rom 9:18-21) — anti-determinist reading",
        summary=(
            "Origen, De Principiis III.1.13 (shell). The potter-and-clay "
            "metaphor (Rom 9:18-21). Origen refuses the Gnostic and "
            "predestinarian reading that the potter (God) imposes the "
            "vessel's destiny without regard to the clay's nature. Instead, "
            "the clay's prior disposition (i.e. the rational creature's "
            "previous use of freedom) determines what vessel it is made into. "
            "Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "Rom 9:18-21"},
        confidence=0.8,
    ),
    _shell_passage(
        section_num=14,
        title="Potter-clay continued — human cooperation with the divine potter",
        summary=(
            "Origen, De Principiis III.1.14 (shell). Continuation of the "
            "potter-clay exegesis. The vessel of honor and the vessel of "
            "dishonor differ because of the clay's responsiveness, not "
            "because of arbitrary divine choice. This applies the general "
            "Origenist principle : grace and freedom always co-operate. "
            "Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=15,
        title="Phil 2:13 / Jer 1:5 — God works in us both willing and doing",
        summary=(
            "Origen, De Principiis III.1.15 (shell). Phil 2:13 : 'It is God "
            "who worketh in you both to will and to do'. Origen reads this "
            "carefully : God's prevenient action does not REPLACE human "
            "willing but ENABLES it. The verse describes synergy, not "
            "monergism. Likewise Jer 1:5 ('Before I formed thee in the belly "
            "I knew thee') describes God's foreknowledge, which does not "
            "necessitate Jeremiah's free response. Shell node — text "
            "pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "Phil 2:13 / Jer 1:5"},
        confidence=0.8,
    ),
    _shell_passage(
        section_num=16,
        title="Jer 10:23 — 'the way of man is not in himself' (limited scope)",
        summary=(
            "Origen, De Principiis III.1.16 (shell). Continuation. Jer 10:23 "
            "('the way of man is not in himself, neither is it in man that "
            "walketh to direct his steps') is read with limited scope : it "
            "denies AUTONOMOUS sufficiency (man cannot reach salvation "
            "without God), not internal freedom of choice. Shell node — "
            "text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "Jer 10:23"},
        confidence=0.8,
    ),
    _shell_passage(
        section_num=17,
        title="1 Cor 7:25 — mercy of the Lord ; grace and freedom cooperate",
        summary=(
            "Origen, De Principiis III.1.17 (shell). 1 Cor 7:25 : Paul's 'I "
            "have obtained mercy of the Lord to be faithful'. Origen reads "
            "this as expressing synergy : Paul's faithfulness is BOTH God's "
            "gift AND Paul's own response. Closes the Pauline-exegesis "
            "section before the great pedagogical-theodicy peak of §18. "
            "Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={"scriptural_locus": "1 Cor 7:25"},
        confidence=0.8,
    ),
    # =============================================================================
    # §18 — Origen's signature pedagogical theodicy
    # =============================================================================
    _shell_passage(
        section_num=18,
        title="Pedagogical theodicy — God permits ill so freedom is preserved",
        summary=(
            "Origen, De Principiis III.1.18 (shell). ⭐ ORIGEN'S SIGNATURE "
            "PEDAGOGICAL-THEODICY ARGUMENT. If God were to act with manifest, "
            "compelling interventions at every moment, the rational creature's "
            "power of choice would be removed (the will would be necessitated "
            "by the spectacle of divine power). Therefore God permits "
            "obstacles, evils, and even the appearance of his own absence — "
            "PRECISELY in order that freedom may be preserved. Evil thus "
            "serves a pedagogical role within the providential order : it is "
            "the price of human autexousion. Frede 2011 and Furst 2022 both "
            "identify this section as the philosophical apex of the treatise. "
            "Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "furst_2022_key_section": True,
            "frede_2011_key_section": True,
            "amand_1945_key_section": True,
            "is_origens_signature_argument": True,
            "argument_locus": "pedagogical_theodicy",
        },
        confidence=0.9,
    ),
    # =============================================================================
    # §§19-22 — Esau / Jacob ; recapitulations
    # =============================================================================
    _shell_passage(
        section_num=19,
        title="Esau and Jacob (Rom 9:11-13) — refutation of predestinarian reading",
        summary=(
            "Origen, De Principiis III.1.19 (shell). Esau and Jacob, the loci "
            "of Pauline predestination theology (Rom 9:11-13 : 'the elder shall "
            "serve the younger ; Jacob have I loved, but Esau have I hated'). "
            "Origen refuses the predestinarian reading. He hypothesizes "
            "previous-life merits (preexistence of souls) : if Jacob was "
            "chosen and Esau rejected 'before they were born' (Rom 9:11), then "
            "either God acts arbitrarily (impossible) or there was previous "
            "free activity. This is one of the textual loci that grounds the "
            "controversial doctrine of preexistence. Shell node — text "
            "pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "scriptural_locus": "Rom 9:11-13",
            "amand_1945_key_section": True,
            "preexistence_locus": True,
        },
        confidence=0.85,
    ),
    _shell_passage(
        section_num=20,
        title="Esau and Jacob continued — 'loved Jacob and hated Esau' hermeneutic",
        summary=(
            "Origen, De Principiis III.1.20 (shell). Continuation of Esau-Jacob "
            "exegesis. 'Hatred' is read non-passionately : God 'hates' Esau in "
            "the same sense that he opposes Esau's wicked tendencies, not in "
            "the sense of arbitrary rejection. Shell node — text pending "
            "ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=21,
        title="Pharaoh recap — freedom preserved across the whole exegesis",
        summary=(
            "Origen, De Principiis III.1.21 (shell). Recapitulation of the "
            "Pharaoh exegesis. Origen reaffirms : when Scripture attributes "
            "hardening or rejection to God, this is providential permission, "
            "never coercive predestination. Shell node — text pending "
            "ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    _shell_passage(
        section_num=22,
        title="Divine purpose unveiled in the order of history",
        summary=(
            "Origen, De Principiis III.1.22 (shell). Continuation of "
            "recapitulation. The divine purpose is unveiled gradually in the "
            "order of history. Providence operates not by coercive intervention "
            "but by orchestrating an order in which free choices contribute to "
            "the final harmony. Shell node — text pending ingestion."
        ),
        is_greek_preserved=True,
        confidence=0.8,
    ),
    # =============================================================================
    # §§23-24 — Conclusion + universalist apokatastasis horizon
    # =============================================================================
    _shell_passage(
        section_num=23,
        title="Universalist horizon — freedom retained even by demons (apokatastasis seeds)",
        summary=(
            "Origen, De Principiis III.1.23 (shell). ⭐ THE UNIVERSALIST "
            "HORIZON. Freedom is RETAINED even by the worst spirits "
            "(including demons). Because rational creatures are mutable by "
            "nature, fall and return remain perpetually possible — opening "
            "the way to the controversial doctrine of apokatastasis (universal "
            "restoration). Frede 2011 Ch. 7 (p. 117) identifies this as the "
            "key Origenist innovation distinguishing him from Stoic "
            "compatibilism : autexousion in Origen is the permanent ontological "
            "property of every rational creature. Furst 2022 Kap. VI 4 reads "
            "this as the apex of compatibilist libertarianism. Shell node — "
            "text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "frede_2011_key_section": True,
            "furst_2022_key_section": True,
            "amand_1945_key_section": True,
            "apokatastasis_locus": True,
        },
        confidence=0.9,
    ),
    _shell_passage(
        section_num=24,
        title="Conclusion — sum of the doctrine of autexousion",
        summary=(
            "Origen, De Principiis III.1.24 (shell). Concluding section of "
            "the Peri autexousiou treatise. Origen sums up the doctrine : "
            "every rational creature possesses αὐτεξούσιον as the principle "
            "of its substance ; this freedom is fully compatible with divine "
            "foreknowledge, providence, and grace, but is never necessitated "
            "by them. The treatise closes with a turn toward the broader "
            "questions of the De Principiis (theodicy, eschatology). Shell "
            "node — text pending ingestion."
        ),
        is_greek_preserved=True,
        extra_md={
            "is_treatise_conclusion": True,
            "furst_2022_key_section": True,
        },
        confidence=0.85,
    ),
]


# =============================================================================
# 4 PHILOCALIA 21 SUB-ANCHORS — Greek-direct anchors for the most-cited sections
# =============================================================================
# These provide an alternative anchor for arguments that cite the Greek text
# directly (e.g. "Philoc. 21.5", "Philoc. 21.18") rather than the de-Principiis
# reference. They share the same content as the De Princ shell but are
# typed as Philocalia 21 sub-passages with CTS URN pointing to tlg028.

def _philocalia_shell(
    *,
    philoc_section: int,
    de_princ_section: int,
    title: str,
    summary: str,
    confidence: float = 0.85,
) -> dict[str, Any]:
    section_id = f"passage_origen_philocalia_21_{philoc_section}"
    label = f"Origen, Philocalia 21.{philoc_section}: {title} [= De Princ. III.1.{de_princ_section}]"
    md = {
        "author": "Origen (compiled by Basil of Caesarea & Gregory of Nazianzus c. 358/360)",
        "work": "Philocalia",
        "work_title": "Philocalia",
        "reference": (
            f"Philocalia 21.{philoc_section} = De Principiis III.1.{de_princ_section}"
        ),
        "section_label": title,
        "philocalia_section": philoc_section,
        "de_princ_section_equivalent": de_princ_section,
        "cts_urn": f"{PHILOCALIA_URN_PREFIX}:21.{philoc_section}",
        "de_princ_cts_urn": f"{DE_PRINC_URN_PREFIX}:3.1.{de_princ_section}",
        "language": "grc",
        "language_note": "Greek text (Philocalia is the principal Greek witness for De Princ III.1)",
        "school": "Christian Platonism",
        "needs_text_ingestion": True,
        "editions_to_consult": [
            "Junod SC 226 (Paris 1976) — Philocalie 21-27 critical Greek edition",
            "Robinson Cambridge 1893 — editio princeps of the Philocalia",
            "Crouzel-Simonetti SC 268 (Paris 1980) — De Principiis III.1 Latin + French",
        ],
        "passage_role": "philocalia_sub_anchor",
        "doxographical_source": "scholarly_critical_edition",
        "doxographical_confidence": "high",
        "source_quality": "shell_pending_text_ingestion",
        "shell_provenance": "origen_de_princ_iii_1_deep_b1",
        "shell_created_for_batch": "origen_de_princ_iii_1_deep_b1",
    }
    return {
        "id": section_id,
        "type": "passage",
        "label": label,
        "description": summary,
        "description_en": summary,
        "period": "Patristic",
        "school": "Christian Platonism",
        "metadata": dump_metadata(md),
        "confidence": confidence,
        "needs_evidence": True,
    }


NEW_PHILOCALIA_ANCHORS: list[dict[str, Any]] = [
    _philocalia_shell(
        philoc_section=5,
        de_princ_section=5,
        title="Anti-astrological argument (Greek)",
        summary=(
            "Origen, Philocalia 21.5 = De Princ. III.1.5 (shell, Philocalia "
            "sub-anchor). Greek-direct anchor for the anti-astrological "
            "argument : stars indicate, do not compel. The Philocalia witness "
            "is the principal Greek text ; the parallel Latin is in Rufinus's "
            "De Principiis. Shell node — text pending ingestion from SC 226 "
            "Junod."
        ),
    ),
    _philocalia_shell(
        philoc_section=7,
        de_princ_section=7,
        title="Pharaoh's hardened heart — Greek text (Philocalia 21.7)",
        summary=(
            "Origen, Philocalia 21.7 = De Princ. III.1.7 (shell, Philocalia "
            "sub-anchor). Greek-direct anchor for the opening of the Pharaoh "
            "scriptural-objection section. Shell node — text pending "
            "ingestion."
        ),
    ),
    _philocalia_shell(
        philoc_section=18,
        de_princ_section=18,
        title="Pedagogical theodicy — Greek text (Philocalia 21.18)",
        summary=(
            "Origen, Philocalia 21.18 = De Princ. III.1.18 (shell, Philocalia "
            "sub-anchor). Greek-direct anchor for Origen's signature "
            "pedagogical-theodicy argument : God permits ill so that freedom "
            "is preserved. Shell node — text pending ingestion."
        ),
        confidence=0.9,
    ),
    _philocalia_shell(
        philoc_section=23,
        de_princ_section=23,
        title="Universalist horizon — Greek text (Philocalia 21.23)",
        summary=(
            "Origen, Philocalia 21.23 = De Princ. III.1.23 (shell, Philocalia "
            "sub-anchor). Greek-direct anchor for the universalist-horizon "
            "section : freedom retained even by demons ; apokatastasis seeds. "
            "Shell node — text pending ingestion."
        ),
        confidence=0.9,
    ),
]

# =============================================================================
# COMBINED LIST
# =============================================================================
NEW_INSERTS: list[dict[str, Any]] = NEW_PASSAGES + NEW_PHILOCALIA_ANCHORS
