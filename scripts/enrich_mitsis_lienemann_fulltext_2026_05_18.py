#!/usr/bin/env python3
"""Enrichissement Mitsis + Lienemann avec citations vérifiées sur PDF intégral.

Suite à l'acquisition manuelle par Romain :
- [local-path] SHAL/04_Littérature_secondaire/
  01_Philosophie_antique/Mitsis-AncientGreekPhilosophers-2021.pdf
- [local-path] SHAL/04_Littérature_secondaire/
  01_Philosophie_antique/lienemann2012.pdf

Le patch :
- Remplace les citations « via_blackson » de Mitsis 2021 par les citations
  verbatim avec pages exactes (extraites directement du PDF original)
- Remplit le shell Lienemann 2012 avec 4 citations critiques vérifiées
- Lève le flag `needs_text_acquisition`
- Pose les chemins locaux dans metadata
- Wire une nouvelle edge Lienemann → critique d'Alexandre (puisqu'elle conteste
  explicitement l'attribution d'indéterminisme à Alexandre par Frede, citant
  Sharples)

Idempotent : marker `enrich_mitsis_lienemann_fulltext_2026_05_18` posé. Snapshot
avant mutation. Préservation byte-exact des autres nodes.
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
SNAPSHOT_DIR = (
    ROOT / "data" / "kg" / "snapshots"
    / "2026-05-18-pre-enrich-mitsis-lienemann-fulltext"
)

WAVE_TAG = "enrich_mitsis_lienemann_fulltext_2026_05_18"
NOW = datetime.now(UTC).isoformat(sep=" ")

ID_MITSIS_2021 = "pub_mitsis_2021_improper_questions"
ID_LIENEMANN_2012 = "pub_lienemann_2012_review_frede"
ID_FREDE_2011 = "pub_frede_2011_free_will"
ID_ALEXANDER = "person_alexander_aphrodisias_fl200ce_n5o6p7q8"

DOCTORAT_BASE = (
    "[local-path] SHAL/"
    "04_Littérature_secondaire/01_Philosophie_antique"
)
MITSIS_PDF_PATH = f"{DOCTORAT_BASE}/Mitsis-AncientGreekPhilosophers-2021.pdf"
LIENEMANN_PDF_PATH = f"{DOCTORAT_BASE}/lienemann2012.pdf"


# ===== ENRICHED MITSIS METADATA =====

MITSIS_VERIFIED_CITATIONS = [
    {
        "page": 264,
        "thesis": (
            "Frede argue qu'on trouve l'origine d'un concept de libre "
            "arbitre chez Épictète — thèse contestée par Mitsis"
        ),
        "quote_verbatim": (
            "I will turn to the Stoics and the influential discussion "
            "by Michael Frede, who argues that we can find the origins "
            "of a conception of free will in Epictetus. Although I "
            "disagree with Frede's claim that Epictetus can take "
            "credit for getting there first, my goal is not so much to "
            "pinpoint origins and hand out ribbons, but instead to "
            "expand the range of conceptions of free will beyond "
            "Dihle's and Frede's \"sheer volition\" view, and also to "
            "widen their historical story"
        ),
        "context": "Section 'Stoic Free Will', début de la critique anti-Frede",
    },
    {
        "page": 265,
        "thesis": (
            "Frede focalise indûment sur Augustin et exclut Épicure du "
            "récit du libre arbitre antique"
        ),
        "quote_verbatim": (
            "[the historical story] focusses too narrowly, I think, on "
            "Augustine's account and his particular influences. For "
            "instance, Epicurus drops out of both their accounts, "
            "whereas, in my view, his non-providential materialist "
            "theory actually provides more fertile ground for a theory "
            "of free will than the kinds of theological frameworks "
            "that structure Stoic and Christian thought"
        ),
        "context": "Critique du périmètre du débat tel que cadré par Dihle-Frede",
    },
    {
        "page": "265-266",
        "thesis": (
            "Méthodologie « quasi-hégélienne » du développement interne "
            "fermé des idées philosophiques"
        ),
        "quote_verbatim": (
            "Much of this strikes me as rather questionable "
            "methodologically, from the quasi-Hegelian notion of the "
            "internal hermetic development of philosophical ideas "
            "toward a particular end, to the assumption that "
            "philosophical discourse and terminology are somehow "
            "sealed off from \"the plain man's\" beliefs and speech, "
            "which actually seems to be more a feature of contemporary "
            "philosophical discourse than ancient philosophical "
            "investigation, especially where ethics and questions of "
            "practical action are concerned."
        ),
        "context": (
            "Critique méthodologique principale — concerne le récit "
            "téléologique de Frede sur prohairesis comme aboutissement "
            "interne hellénistique"
        ),
    },
    {
        "page": 266,
        "thesis": (
            "Frede suppose une conception fodorienne (mentaliste) des "
            "concepts plutôt qu'une conception dummettienne "
            "(capacitaire-pragmatique)"
        ),
        "quote_verbatim": (
            "More dubious, I think, is Frede's apparent assumption "
            "that concepts are some kind of mental particulars or "
            "word-like entities in a language of thought, rather than, "
            "say, as Dummett and others have argued, abilities "
            "peculiar to cognitive agents—even fictional ones such as "
            "Achilles's."
        ),
        "context": (
            "Critique épistémologique : Frede présuppose Fodor implicite, "
            "Mitsis défend Dummett"
        ),
    },
    {
        "page": 268,
        "thesis": (
            "Critique philologique directe : Frede réifie la prohairesis "
            "épictétéenne en une entité agentive, ce que le texte grec "
            "ne supporte pas"
        ),
        "quote_verbatim": (
            "Epictetus here characterizes prohairesis as a something "
            "that an individual works on or cultivates "
            "(ἐξεργάζεσθαι). [...] Prohairesis is not merely a "
            "free-floating ability or disposition. Clearly, for "
            "Epictetus it is an ability exercised and worked on by an "
            "individual, and in technical Stoic terms, individuals are "
            "to be identified with their logikē psychē or hegemonikon, "
            "which is entirely rational. Thus, if prohairesis is a "
            "disposition or ability of our reason, it is hard to see "
            "how it can be a separate or prior non-cognitive element "
            "in the Stoic psyche that serves a harbinger of "
            "Augustine's \"pure volition\""
        ),
        "context": (
            "Analyse de Diss. 1.4.18 — démonte la lecture libertaire "
            "de Frede en la rendant philologiquement insoutenable"
        ),
    },
    {
        "page": 269,
        "thesis": (
            "Frede paraphrase « rather loosely » Épictète Diss. 3.5.7 — "
            "le texte ne dit rien d'une « volonté libre »"
        ),
        "quote_verbatim": (
            "Epictetus here says nothing about his main concern being "
            "that his will be free. He wishes to be overtaken by "
            "disease or death when he is looking after only his own "
            "prohairesis, so that he can be free. [...] For Locke, and "
            "perhaps for the Stoics—at least to the extent that "
            "volition can be identified with prohairesis—volition "
            "proper ensues upon reason's assent. But it is not a "
            "separate entity that exercises powers of sheer volition "
            "on its own."
        ),
        "context": (
            "Analyse de Diss. 3.5.7 — Mitsis montre que Frede sur-traduit "
            "le texte grec ; et propose continuité Stoïciens-Locke "
            "comme alternative à la rupture Stoïciens-Augustin de Frede"
        ),
    },
]


# ===== ENRICHED LIENEMANN METADATA =====

LIENEMANN_VERIFIED_CITATIONS = [
    {
        "page": 257,
        "thesis": (
            "Frede attribue à Aristote responsabilité morale + "
            "louange/blâme pour les enfants et animaux — contredit la "
            "lecture standard de NE III 1-7"
        ),
        "quote_verbatim_de": (
            "fällt an Fredes Interpretation auf, dass er die "
            "Unterschiede hinsichtlich der Erkenntnis- und "
            "Handlungsfähigkeit von Tieren, Kindern und erwachsenen "
            "Menschen nur als graduell betrachtet. [...] Diese Aussage "
            "Fredes verwundert, weil Aristoteles nach verbreitetem "
            "Verständnis in NE III 1–7 Lob und Tadel mit moralischer "
            "Verantwortung verbindet und diese Kindern und Tieren "
            "nicht sinnvoll zugesprochen werden kann."
        ),
        "translation_fr": (
            "Il est frappant dans l'interprétation de Frede qu'il "
            "considère les différences cognitives entre animaux, "
            "enfants et adultes comme seulement graduelles. [...] "
            "Cette affirmation de Frede surprend, car selon la lecture "
            "courante d'Aristote en NE III 1-7, louange et blâme sont "
            "liés à la responsabilité morale, qui ne peut être "
            "raisonnablement attribuée aux enfants et aux animaux."
        ),
        "section": "1. Einleitung und Aristoteles' Verständnis von Prohairesis",
    },
    {
        "page": 260,
        "thesis": (
            "CITATION DÉCISIVE : l'attribution d'un Freiheitsbegriff "
            "indéterministe à Alexandre par Frede est philologiquement "
            "infondée — Lienemann cite Sharples (l'éditeur du *De Fato*) "
            "à l'appui"
        ),
        "quote_verbatim_de": (
            "Sharples bemerkt zu Recht in den angefügten Endnoten, "
            "dass sich bei Alexander kein so eindeutiger Beleg für "
            "die Zuschreibung eines indeterministischen "
            "Freiheitsbegriffs findet, wie es Fredes Darstellung "
            "suggeriert."
        ),
        "translation_fr": (
            "Sharples remarque à juste titre dans les notes finales "
            "qu'on ne trouve pas chez Alexandre de preuve aussi "
            "univoque pour l'attribution d'un concept indéterministe "
            "de liberté que ce que la présentation de Frede suggère."
        ),
        "section": "3. Ursprung des freien Willens bei den Stoikern und ihre Kritiker",
    },
    {
        "page": 266,
        "thesis": (
            "Verdict final mitigé : la thèse Frede « Alexandre = premier "
            "indéterminisme » reste douteuse + absence problématique "
            "d'engagement avec Kahn 1988"
        ),
        "quote_verbatim_de": (
            "Allerdings hätte man sich bei manchen Aussagen auch für "
            "den mündlichen Vortrag ein genaueres Belegen gewünscht: "
            "Ein Beispiel ist das Nicht-Erwähnen des Aufsatzes von "
            "Charles Kahn von 1988, ein anderes der indeterministische "
            "Willensbegriff, den Frede Alexander zuschreibt, bei dem "
            "aber fraglich ist, ob er Alexanders Ausführungen "
            "entspricht."
        ),
        "translation_fr": (
            "On aurait néanmoins souhaité, pour certaines affirmations "
            "même à l'oral, un étayage plus précis : un exemple est "
            "l'absence de mention de l'article de Charles Kahn de "
            "1988, un autre le concept indéterministe de volonté que "
            "Frede attribue à Alexandre, mais dont il est douteux "
            "qu'il corresponde aux développements d'Alexandre."
        ),
        "section": "Schlussbewertung (p. 265-266)",
    },
    {
        "page": 266,
        "thesis": (
            "Le mérite de Frede : relativiser la thèse de Dihle "
            "(Augustin = créateur radical) en pointant l'origine "
            "stoïcienne (Épictète)"
        ),
        "quote_verbatim_de": (
            "Das Verdienst von Fredes Untersuchung ist, diese neue "
            "Perspektive mit Hilfe von Rekonstruktionen und "
            "Quervergleichen verschiedener antiker, spätantiker und "
            "kaiserzeitlicher Autoren zu untermauern. [...] Fredes "
            "Interpretationen sind in besonderer Weise geeignet, "
            "antike Positionen als systematisch relevante "
            "Auffassungen in heutigen Diskursen zur Geltung zu "
            "bringen."
        ),
        "translation_fr": (
            "Le mérite de l'étude de Frede est de soutenir cette "
            "nouvelle perspective à l'aide de reconstructions et de "
            "comparaisons croisées entre divers auteurs antiques, "
            "tardo-antiques et impériaux. [...] Les interprétations "
            "de Frede sont particulièrement aptes à faire valoir les "
            "positions antiques comme conceptions systématiquement "
            "pertinentes dans les débats contemporains."
        ),
        "section": (
            "Verdict positif d'ensemble — Lienemann est largely "
            "favorable malgré les réserves ponctuelles"
        ),
    },
]


# ===== NEW EDGE =====

# Lienemann conteste explicitement l'Alexandre-indéterministe de Frede,
# citant Sharples. Wire engagement edge → Alexandre.
NEW_EDGES: list[dict[str, Any]] = [
    {
        "source": ID_LIENEMANN_2012,
        "target": ID_ALEXANDER,
        "relation": "discusses",
        "confidence": 0.9,
        "metadata": {
            "wave": WAVE_TAG,
            "discussion_type": "contests_frede_attribution",
            "summary": (
                "Lienemann conteste l'attribution par Frede d'un "
                "concept indéterministe de liberté à Alexandre "
                "d'Aphrodise — citation de Sharples à l'appui "
                "(Lienemann 2012, p. 260 + p. 266)"
            ),
            "key_quote_de": (
                "der indeterministische Willensbegriff, den Frede "
                "Alexander zuschreibt, bei dem aber fraglich ist, ob "
                "er Alexanders Ausführungen entspricht"
            ),
            "pages": "p. 260, p. 266",
        },
    },
]


# ===== MACHINERY =====


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def edge_sig(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source") or e.get("source_id") or "",
        e.get("target") or e.get("target_id") or "",
        e.get("relation") or "",
    )


def node_id_of_line(line: str) -> str:
    return json.loads(line).get("id") or ""


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)


def enrich_mitsis(node: dict[str, Any]) -> dict[str, Any]:
    md = parse_metadata(node.get("metadata"))
    md["verified_critiques_direct"] = MITSIS_VERIFIED_CITATIONS
    md["acquisition_status"] = (
        "PDF intégral acquis manuellement par Romain le 2026-05-18 "
        "à " + MITSIS_PDF_PATH + ". Citations vérifiées en lecture "
        "directe (pdftotext). Citations indirectes via Blackson "
        "conservées dans verified_theses pour traçabilité."
    )
    md["local_pdf_path"] = MITSIS_PDF_PATH
    md["needs_text_acquisition"] = False
    md[WAVE_TAG] = (
        "Citations Mitsis 2021 enrichies via lecture directe du PDF — "
        "6 citations verbatim avec pages, sections, contexte. Remplace "
        "la chaîne d'attribution via Blackson 2025 qui n'avait que 3 "
        "citations partielles"
    )
    # Refresh description briefly to mention direct verification
    base_desc = node.get("description") or ""
    if "PDF intégral vérifié" not in base_desc:
        # Append a short note
        node["description"] = base_desc.rstrip() + (
            " [Acquisition full-text 2026-05-18 : PDF intégral vérifié, "
            "6 citations verbatim directes intégrées dans "
            "metadata.verified_critiques_direct — voir notamment p. 265-266 "
            "(critique quasi-hégélienne + Fodor/Dummett) et p. 268-269 "
            "(critique philologique directe sur Diss. 1.4.18 et 3.5.7).]"
        )
    node["metadata"] = json.dumps(md, ensure_ascii=False)
    node["updated_at"] = NOW
    return node


def enrich_lienemann(node: dict[str, Any]) -> dict[str, Any]:
    md = parse_metadata(node.get("metadata"))
    md["verified_critiques"] = LIENEMANN_VERIFIED_CITATIONS
    md["acquisition_status"] = (
        "PDF intégral acquis manuellement par Romain le 2026-05-18 "
        "à " + LIENEMANN_PDF_PATH + ". Citations vérifiées en lecture "
        "directe (pdftotext)."
    )
    md["local_pdf_path"] = LIENEMANN_PDF_PATH
    md["needs_text_acquisition"] = False
    md["review_verdict"] = (
        "Praise-with-reservations. Largely favorable to Frede "
        "(« Verdienst » explicitement reconnu, p. 266) mais réserves "
        "ponctuelles sérieuses : (1) lecture aristotélicienne de "
        "responsabilité étendue aux enfants/animaux problématique "
        "(p. 257) ; (2) attribution d'un Freiheitsbegriff indéterministe "
        "à Alexandre philologiquement contestable, Sharples à l'appui "
        "(p. 260 + p. 266) ; (3) absence d'engagement avec Kahn 1988 "
        "(p. 266) ; (4) défauts formels de la posthumie (fil "
        "argumentatif obscur, manque de notes)"
    )
    md["bobzien_reference"] = (
        "Lienemann cite Bobzien 1998 Determinism and Freedom dans une "
        "note (« Vgl. auch S. Bobzien, Determinism and Freedom in "
        "Stoic Philosophy, Oxford 1998 », n. à p. 261). Pas de "
        "polémique avec Bobzien — référence d'appui sur la "
        "reconstruction stoïcienne du compatibilisme"
    )
    md["structure"] = {
        "1": "Einleitung und Aristoteles' Verständnis von Prohairesis als Vorläufer (p. 252-257)",
        "2": "Der Ursprung des Willensbegriffs bei den Stoikern und dessen Kritiker (p. 257-260)",
        "3": "Ursprung des freien Willens bei den Stoikern und ihre Kritiker (p. 260-261)",
        "4": "Frühchristliche Vorstellung vom freien Willen bei Origenes (p. 261-?)",
        "5": "Reaktionen auf den stoischen Begriff des freien Willens bei Plotin",
        "6": "Augustinus als Vertreter eines radikal neuen Begriffs",
        "Schluss": "Verdict (p. 265-266)",
    }
    md[WAVE_TAG] = (
        "Citations Lienemann 2012 verbatim (allemand + traduction "
        "française) extraites du PDF intégral — 4 citations clés. "
        "Flag needs_text_acquisition levé"
    )
    # Refresh description
    node["description"] = (
        "Béatrice Lienemann, recension critique de Michael Frede, "
        "*A Free Will. Origins of the Notion in Ancient Thought* "
        "(University of California Press, 2011), parue dans "
        "*Bochumer Philosophisches Jahrbuch für Antike und "
        "Mittelalter* 15/1 (2012), p. 252-266. DOI 10.1075/bpjam.15."
        "09lie. Seule review longue (15 p.) de Frede 2011 en langue "
        "germanique. **Verdict global** : praise-with-reservations. "
        "Largely favorable à Frede (« Das Verdienst von Fredes "
        "Untersuchung… », p. 266) mais réserves ponctuelles sérieuses "
        "— notamment la critique philologique décisive sur "
        "l'attribution d'un *indeterministischer Freiheitsbegriff* "
        "à Alexandre d'Aphrodise : « Sharples bemerkt zu Recht in den "
        "angefügten Endnoten, dass sich bei Alexander kein so "
        "eindeutiger Beleg für die Zuschreibung eines "
        "indeterministischen Freiheitsbegriffs findet, wie es Fredes "
        "Darstellung suggeriert » (p. 260). Autres griefs : "
        "(a) attribution erronée à Aristote (NE III 1-7) de la "
        "responsabilité pour enfants/animaux ; (b) absence "
        "d'engagement avec Kahn 1988 ; (c) défauts formels de la "
        "posthumie. Lienemann cite Bobzien 1998 comme référence "
        "d'appui en note (p. 261). Texte intégral acquis : "
        + LIENEMANN_PDF_PATH
    )
    node["metadata"] = json.dumps(md, ensure_ascii=False)
    node["updated_at"] = NOW
    return node


def main() -> int:
    node_lines = [
        line.rstrip("\n")
        for line in NODES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_lines = [
        line.rstrip("\n")
        for line in EDGES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_sigs = {edge_sig(json.loads(ln)) for ln in edge_lines}

    changes: list[str] = []

    # Find + enrich Mitsis
    for i, ln in enumerate(node_lines):
        nid = node_id_of_line(ln)
        if nid == ID_MITSIS_2021:
            node = json.loads(ln)
            md = parse_metadata(node.get("metadata"))
            if md.get(WAVE_TAG):
                print(f"SKIP {nid} (already enriched)")
                break
            node = enrich_mitsis(node)
            node_lines[i] = json.dumps(node, ensure_ascii=False)
            changes.append(f"ENRICH {nid} (Mitsis fulltext)")
            break
    else:
        print(f"ERROR: {ID_MITSIS_2021} not found", file=sys.stderr)
        return 2

    # Find + enrich Lienemann
    for i, ln in enumerate(node_lines):
        nid = node_id_of_line(ln)
        if nid == ID_LIENEMANN_2012:
            node = json.loads(ln)
            md = parse_metadata(node.get("metadata"))
            if md.get(WAVE_TAG):
                print(f"SKIP {nid} (already enriched)")
                break
            node = enrich_lienemann(node)
            node_lines[i] = json.dumps(node, ensure_ascii=False)
            changes.append(f"ENRICH {nid} (Lienemann fulltext)")
            break
    else:
        print(f"ERROR: {ID_LIENEMANN_2012} not found", file=sys.stderr)
        return 2

    # New edges
    for e in NEW_EDGES:
        sig = edge_sig(e)
        if sig in edge_sigs:
            print(f"SKIP edge (exists): {sig[0]} --{sig[2]}--> {sig[1]}")
            continue
        edge_lines.append(json.dumps(e, ensure_ascii=False))
        edge_sigs.add(sig)
        changes.append(f"NEW EDGE {sig[0]} --{sig[2]}--> {sig[1]}")

    if not changes:
        print("OK: nothing to apply")
        return 0

    snapshot()
    print(f"snapshot: {SNAPSHOT_DIR}")
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    for c in changes:
        print(c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
