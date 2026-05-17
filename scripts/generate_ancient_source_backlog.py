#!/usr/bin/env python3
"""Generate an ancient-source passage gap inventory for EleutherIA.

The inventory is intentionally reproducible: it depends only on the checked-in
KG JSONL files and the static source seed list below.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_NODES = Path("data/kg/nodes.jsonl")
DEFAULT_EDGES = Path("data/kg/edges.jsonl")
DEFAULT_JSON = Path("data/quality/ancient_source_backlog.json")
DEFAULT_MD = Path("data/quality/ancient_source_backlog.md")

STATUS_ORDER = {
    "missing_work_node": 0,
    "blocker": 1,
    "metadata_only": 2,
    "no_passages": 3,
    "kg_only": 4,
    "partial": 5,
    "covered": 6,
}


@dataclass(frozen=True)
class SourceItem:
    priority: str
    label: str
    source_route: str
    recommended_next_step: str
    notes: str
    expected_passages: int | None = None
    work_node_ids: tuple[str, ...] = ()
    match: tuple[str, ...] = ()
    blocker: bool = False


SOURCE_ITEMS: tuple[SourceItem, ...] = (
    # Passage expansion plan, Tier 1.
    SourceItem("P0", "Marcus Aurelius, Meditations", "db_reconciliation", "Reconcile old KG nodes to DB passages, then create missing passage nodes.", "Tier 1 in the 2026-02-25 passage expansion plan; old-pipeline nodes were previously unlinked.", 577, ("work_marcus_aurelius_meditations",), ("marcus aurelius meditations",)),
    SourceItem("P0", "Seneca, Epistulae Morales", "db_reconciliation", "Create or repair the Epistulae work node and retarget Epistulae passage part_of edges away from De Providentia.", "Tier 1 in the passage expansion plan; current graph may conflate Epistulae with De Providentia.", 2135, (), ("seneca epistulae morales", "epistulae morales")),
    SourceItem("P0", "Seneca, De Providentia", "db_reconciliation", "Separate true De Providentia passages from Seneca Epistulae passages before judging coverage.", "Tier 1 in the passage expansion plan; count should be near 68 after reconciliation.", 68, ("work_de_providentia_seneca_a2b3c4d5",), ("seneca de providentia", "de providentia on providence")),
    SourceItem("P0", "Lucretius, De Rerum Natura", "db_reconciliation", "Verify passage count against DB and add translations where missing.", "Tier 1 Epicurean source for clinamen and anti-determinism.", 300, ("work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",), ("lucretius de rerum natura",)),
    SourceItem("P0", "Aristotle, Nicomachean Ethics", "db_reconciliation", "Split any mislinked Magna Moralia passages out of the Nicomachean Ethics work node.", "Tier 1 for voluntary action; current graph should be checked for work-node granularity.", 116, ("work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",), ("nicomachean ethics aristotle",)),
    SourceItem("P0", "Aristotle, Eudemian Ethics", "db_reconciliation", "Attach existing EE passages to the dedicated Eudemian Ethics work node or ingest missing passages.", "Tier 1 and explicit key gap; expected 41 passages in the passage expansion plan.", 41, ("work_aristotle_eudemian_ethics",), ("aristotle eudemian ethics", "ethica eudemia", "tlg0086 tlg009")),
    SourceItem("P0", "Aristotle, De Interpretatione", "db_reconciliation", "Verify chapter 9 coverage and add translations where missing.", "Tier 1 future-contingents source.", 29, ("work_de_interpretatione_aristotle_c350bce_e4f6g8h0",), ("aristotle de interpretatione",)),
    SourceItem("P0", "Epicurus, Letters and Fragments", "json_mirror", "Consolidate Epicurus letters, Principal Doctrines, Vatican Sayings, and fragments under citable work nodes.", "Tier 1 and explicit key gap; use verified Greek text mirrors or manual Usener/Arrighetti coverage.", 193, ("work_epicurus_letters_fragments", "work_epicurus_kuriai_doxai", "work_epicurus_letter_herodotus", "work_epicurus_letter_menoeceus"), ("epicurus letter", "principal doctrines", "kuriai doxai", "epicurus fragments")),
    SourceItem("P0", "Cicero, De Fato", "db_reconciliation", "Verify existing passage nodes and translation coverage.", "Tier 1 locus classicus for Hellenistic fate debates.", 48, ("work_de_fato_cicero_44bce_b9c4e5d2",), ("cicero de fato",)),
    SourceItem("P0", "Plutarch, De Stoicorum Repugnantiis", "db_reconciliation", "Attach or ingest passages for the dedicated work node.", "Tier 1 and explicit key gap.", 47, ("work_plutarch_stoic_repugnantiis",), ("plutarch stoicorum repugnantiis", "stoic repugnantiis")),
    SourceItem("P0", "Pseudo-Plutarch, De Fato", "db_reconciliation", "Verify whether complete De Fato coverage should be split from authentic/disputed Plutarch nodes.", "Tier 1 Platonist fate text.", 19, ("work_plutarch_de_fato_complete", "work_plutarch_de_fato_authentic"), ("plutarch de fato",)),
    SourceItem("P0", "Methodius, De Libero Arbitrio", "db_reconciliation", "Create or retarget passages for Methodius instead of sharing Augustine work nodes.", "Tier 1 early Christian free-will treatise.", 97, ("work_methodius_de_libero_arbitrio",), ("methodius de libero arbitrio",)),
    SourceItem("P0", "Augustine, De Libero Arbitrio", "db_reconciliation", "Reconcile old KG nodes to DB passages and split unrelated works from the De Libero Arbitrio node.", "Tier 1; old-pipeline nodes were previously unlinked.", 170, ("work_de_libero_arbitrio", "work_augustine_de_libero_arbitrio"), ("augustine de libero arbitrio",)),
    SourceItem("P0", "Augustine, De Civitate Dei V/XII/XIV", "db_reconciliation", "Verify selected-book coverage and add DB passage IDs where missing.", "Tier 1 for fate, foreknowledge, and original sin.", 158, ("work_augustine_de_civitate_dei",), ("augustine de civitate dei",)),
    SourceItem("P0", "Augustine, De Gratia et Libero Arbitrio", "db_reconciliation", "Verify the dedicated work node and reconcile existing passages.", "Tier 1 grace/free-will source.", 25, ("work_augustine_de_gratia_la",), ("de gratia et libero arbitrio",)),
    SourceItem("P0", "Boethius, De Consolatione Philosophiae", "db_reconciliation", "Reconcile old KG nodes to DB passage IDs.", "Tier 1 for providence and foreknowledge.", 129, ("work_consolatio_philosophiae_boethius_524ce_f1g2h3i4",), ("boethius consolatione philosophiae",)),
    SourceItem("P0", "Epictetus, Discourses and Enchiridion", "db_reconciliation", "Reconcile old KG nodes to DB passage IDs and verify work split.", "Tier 1 Stoic prohairesis source.", 185, ("work_epictetus_discourses",), ("epictetus discourses enchiridion",)),
    # Passage expansion plan, Tier 2.
    SourceItem("P1", "Plotinus, Enneads", "db_reconciliation", "Verify whether all Enneads passages should remain under the current IV.8-labeled node.", "Tier 2; VI.8 and III.1 are key for freedom and fate.", 1355, ("work_plotinus_enneads_iv_8", "work_plotinus_enn_iii_1"), ("plotinus enneads",)),
    SourceItem("P1", "Sextus Empiricus, PH and Against the Professors", "db_reconciliation", "Verify work split and passage counts for PH versus M.", "Tier 2 skeptical context.", 534, ("work_sextus_outlines_pyrrhonism_f9a7c8e4",), ("sextus empiricus", "outlines pyrrhonism")),
    SourceItem("P1", "Diogenes Laertius, Vitae Philosophorum", "db_reconciliation", "Verify DB reconciliation and book-level passage counts.", "Tier 2 doxographic source for all schools.", 1203, ("work_diogenes_laertius_lives",), ("diogenes laertius lives",)),
    SourceItem("P1", "Plato, Phaedrus", "db_reconciliation", "Ingest or reconcile Phaedrus passages.", "Tier 2 source for soul self-motion.", 261, ("work_plato_phaedrus",), ("plato phaedrus",)),
    SourceItem("P1", "Plato, Phaedo", "db_reconciliation", "Verify passage coverage.", "Tier 2 source for soul, immortality, and choice.", 59, ("work_plato_phaedo",), ("plato phaedo",)),
    SourceItem("P1", "Plato, Timaeus", "db_reconciliation", "Verify passage coverage and translations.", "Tier 2 cosmology, necessity, and demiurge source.", 76, ("work_plato_timaeus",), ("plato timaeus",)),
    SourceItem("P1", "Plato, Apology", "db_reconciliation", "Ingest or reconcile Apology passages.", "Tier 2 Socratic moral autonomy source.", 125, ("work_plato_apology",), ("plato apology", "tlg0059 tlg002")),
    SourceItem("P1", "Aristotle, De Anima", "scaife_library", "Ingest from First1K/Scaife and connect to Aristotle work metadata.", "Tier 2 and explicit key gap.", 30, ("work_aristotle_de_anima",), ("aristotle de anima",)),
    SourceItem("P1", "Aristotle, Physics", "scaife_library", "Ingest from OGA/Scaife and verify causal vocabulary coverage.", "Tier 2 and explicit key gap.", 71, ("work_aristotle_physics",), ("aristotle physics", "aristotle physica", "tlg0086 tlg031")),
    SourceItem("P1", "Aristotle, Metaphysics", "db_reconciliation", "Verify whether current Book Theta-only node satisfies the intended work scope.", "Tier 2; potentiality and actuality.", 142, ("work_metaphysics_theta_aristotle_c350bce_f5g7h9i1",), ("aristotle metaphysics",)),
    SourceItem("P1", "Aristotle, Magna Moralia", "db_reconciliation", "Create a dedicated Magna Moralia work node and retarget current MM passages.", "Tier 2 and explicit key gap; current passages may be attached to Nicomachean Ethics.", 434, ("work_aristotle_magna_moralia",), ("aristotle magna moralia",)),
    SourceItem("P1", "Porphyry, Ad Marcellam", "db_reconciliation", "Verify passage coverage.", "Tier 2 Neoplatonist ethics source.", 35, ("work_porphyry_ad_marcellam",), ("porphyry ad marcellam",)),
    SourceItem("P1", "Aspasius, In Ethica Nicomachea", "db_reconciliation", "Verify commentary passages on voluntary action.", "Tier 2 earliest EN commentary.", 6, ("text_aspasius_in_en",), ("aspasius in ethica nicomachea",)),
    SourceItem("P1", "Calcidius, In Timaeum", "json_mirror", "Verify DLT source and add passage nodes.", "Tier 2 Latin Platonist source on fate/providence.", 5, ("work_calcidius_in_timaeum",), ("calcidius in timaeum",)),
    SourceItem("P1", "Alcinous, Didaskalikos", "db_reconciliation", "Verify the single existing passage and translation.", "Tier 2 Middle Platonist handbook.", 1, ("work_didaskalikos_alcinous_2nd_ce_q7r8s9t0",), ("alcinous didaskalikos",)),
    # 2026-03-10 Scaife matrix and alternative-source gaps.
    SourceItem("P1", "Nemesius, De Natura Hominis", "scaife_library", "Use generic Scaife CTS fetcher, then create KG passages.", "Verified available on Scaife in the 2026-03-10 gap plan; explicit key gap.", None, ("work_nemesius_de_nat_hom",), ("nemesius de natura hominis",)),
    SourceItem("P1", "Cicero, De Divinatione", "scaife_library", "Verify current Scaife ingestion and complete missing passages.", "Verified available on Scaife in the gap plan.", 130, ("work_de_divinatione_cicero",), ("cicero de divinatione",)),
    SourceItem("P1", "Cicero, De Natura Deorum", "scaife_library", "Verify current Scaife ingestion and complete missing passages.", "Verified available on Scaife in the gap plan.", 200, ("work_de_natura_deorum_cicero",), ("cicero de natura deorum",)),
    SourceItem("P1", "Plato, Republic Book X", "scaife_library", "Slice or tag Book X passages from Republic coverage.", "Verified available on Scaife in the gap plan for Myth of Er priority.", 30, ("work_republic_plato_c380bce_c3d4e5f6",), ("plato republic",)),
    SourceItem("P1", "Plato, Laws Book X", "scaife_library", "Slice or tag Book X passages from Laws coverage.", "Verified available on Scaife in the gap plan.", 40, ("work_laws_plato_c350bce_d4e5f6g7",), ("plato laws",)),
    SourceItem("P1", "Aristotle, De Generatione et Corruptione", "scaife_library", "Verify current Scaife ingestion and translation coverage.", "Verified available on Scaife in the gap plan.", 50, ("work_de_gen_corr_aristotle",), ("aristotle de generatione et corruptione",)),
    SourceItem("P1", "Cleanthes, Hymn to Zeus", "scaife_library", "Verify the single passage and connect to Stoic fragment collection.", "Verified available on Scaife in the gap plan.", 1, ("work_cleanthes_hymn_to_zeus",), ("cleanthes hymn to zeus",)),
    SourceItem("P2", "Galen, De Placitis Hippocratis et Platonis", "scaife_library", "Ingest from Scaife CTS and create work/passages.", "Verified available on Scaife in the gap plan.", None, ("work_galen_de_placitis",), ("galen de placitis hippocratis platonis",)),
    SourceItem("P2", "Clement of Alexandria, Stromata", "scaife_library", "Compare existing Clement/SC coverage, then ingest missing passages from Scaife.", "Verified available on Scaife in the gap plan.", 500, ("work_clement_stromata", "work_clement_stromateis"), ("clement stromata", "clement stromateis", "clement of alexandria stromata", "clement of alexandria stromateis")),
    SourceItem("P2", "Simplicius, In Epicteti Enchiridion", "scaife_library", "Complete Scaife ingestion and verify commentary passage granularity.", "Verified available on Scaife in the gap plan.", 100, ("work_simplicius_in_enchiridion",), ("simplicius in epicteti enchiridion",)),
    SourceItem("P2", "Basil, Hexaemeron", "scaife_library", "Ingest from Scaife CTS if needed.", "Verified available on Scaife in the gap plan.", 80, ("work_basil_hexaemeron",), ("basil hexaemeron",)),
    SourceItem("P2", "Tertullian, Adversus Marcionem", "scaife_library", "Ingest from Scaife/CSEL and prioritize Book II if splitting by book.", "Verified available on Scaife and explicit key gap.", 150, ("work_tertullian_adv_marcionem",), ("tertullian adversus marcionem",)),
    SourceItem("P2", "Tertullian, De Anima", "scaife_library", "Ingest from Scaife/CCSL and add translations.", "Verified available on Scaife and explicit key gap.", 58, ("work_tertullian_de_anima",), ("tertullian de anima",)),
    SourceItem("P2", "Clement of Alexandria, Protrepticus", "scaife_library", "Ingest from Scaife CTS if not covered elsewhere.", "Verified available on Scaife in the gap plan.", 120, ("work_clement_protrepticus",), ("clement protrepticus",)),
    SourceItem("P2", "Josephus, Bellum Judaicum", "json_mirror", "Use Perseus XML or another verified Greek source and target fate passages first.", "Not available on Scaife per gap plan; alternative Perseus source listed.", None, ("work_josephus_bellum_jud",), ("josephus bellum judaicum",)),
    SourceItem("P2", "Josephus, Antiquitates Judaicae", "json_mirror", "Use Perseus XML or another verified Greek source and target sectarian fate passages first.", "Not available on Scaife per gap plan; alternative Perseus source listed.", None, ("work_josephus_antiquitates",), ("josephus antiquitates judaicae",)),
    SourceItem("P2", "Philo, De Opificio Mundi", "manual_critical_edition", "Source Cohn-Wendland/Loeb-aligned Greek before passage ingestion.", "Not available on Scaife per gap plan.", None, ("work_philo_de_opificio",), ("philo de opificio mundi",), True),
    SourceItem("P2", "Philo, De Providentia", "manual_critical_edition", "Source Cohn-Wendland/Armenian/Greek-fragment evidence before passage ingestion.", "Not available on Scaife per gap plan.", None, ("work_philo_de_providentia",), ("philo de providentia",), True),
    SourceItem("P2", "Aristotle, De Motu Animalium", "json_mirror", "Use First1K/TLG or Nussbaum-aligned critical text and add passages.", "Not available on Scaife per gap plan; explicit key gap.", None, ("work_aristotle_de_motu",), ("aristotle de motu animalium",)),
    SourceItem("P2", "Gregory of Nyssa, Contra Fatum", "manual_critical_edition", "Source GNO III.2 or another verified edition before ingestion.", "Not available on Scaife per gap plan; explicit key gap.", None, ("work_gregory_contra_fatum",), ("gregory of nyssa contra fatum",), True),
    SourceItem("P2", "Gregory of Nyssa, De Hominis Opificio", "manual_critical_edition", "Source GNO/PG text and create passages.", "Not available on Scaife per gap plan; part of explicit Gregory of Nyssa core gap.", None, ("work_gregory_de_hom_opif",), ("gregory de hominis opificio",), True),
    SourceItem("P2", "John of Damascus, De Fide Orthodoxa", "manual_critical_edition", "Source Kotter PTS or verified Greek text before passage ingestion.", "Not available on Scaife per gap plan; explicit key gap.", None, ("work_john_damascus_de_fide",), ("john of damascus de fide orthodoxa",), True),
    SourceItem("P2", "Iamblichus, De Mysteriis", "manual_critical_edition", "Source a verified edition before ingestion.", "Not available on Scaife per gap plan.", None, ("work_iamblichus_de_mysteriis",), ("iamblichus de mysteriis",), True),
    # Additional explicit gaps from the task.
    SourceItem("P1", "Porphyry, Peri tou eph' hemin", "manual_critical_edition", "Create passages from a verified critical edition or fragment witness.", "Explicit key gap.", None, ("work_porphyry_peri_tou_eph_hemin",), ("porphyry peri tou eph hemin",)),
    SourceItem("P1", "Proclus, De Providentia/Fato/In Nobis", "manual_critical_edition", "Use Boese/Isaac-aligned evidence and distinguish Greek fragments from Latin translation.", "Explicit key gap; gap plan notes partial Latin/fragmentary evidence.", None, ("work_proclus_de_providentia_fato_in_nobis", "work_proclus_tria_opuscula_c9a8e4b3"), ("proclus de providentia fato in nobis", "proclus tria opuscula"), True),
    SourceItem("P1", "Plutarch, De Communibus Notitiis adversus Stoicos", "db_reconciliation", "Attach or ingest passages for the dedicated work node.", "Explicit key gap.", None, ("work_plutarch_de_communibus_notitiis",), ("plutarch de communibus notitiis",)),
    SourceItem("P1", "Stobaeus, Anthologium/Eclogae", "manual_critical_edition", "Create a source-collection/work node and ingest priority fate/free-will excerpts.", "Explicit key gap and witness for many fragments.", None, ("work_stobaeus_anthologium",), ("stobaeus anthologium", "stobaeus eclogae")),
    SourceItem("P1", "Zeno, SVF I fragments", "manual_critical_edition", "Add SVF collection anchors and Zeno fragment passage nodes from verified edition.", "Explicit key gap.", None, ("work_zeno_svf_i_fragments",), ("zeno svf i fragments",)),
    SourceItem("P1", "Diogenes of Oenoanda, Inscription", "manual_critical_edition", "Source Smith edition and create inscription fragment passages.", "Explicit key gap; gap plan treats it as description-only until a digital edition is sourced.", None, ("work_diogenes_oenoanda_inscription",), ("diogenes of oenoanda",), True),
    SourceItem("P1", "Diogenianus, Anti-Stoic Fragments", "manual_critical_edition", "Create fragment collection/work node and ingest verified testimonia.", "Explicit key gap.", None, ("work_diogenianus_fragments",), ("diogenianus",), True),
    SourceItem("P1", "Oenomaus of Gadara, Fragments", "manual_critical_edition", "Create fragment collection/work node and ingest verified testimonia.", "Explicit key gap.", None, ("work_oenomaus_fragments",), ("oenomaus",), True),
    SourceItem("P2", "Gregory of Nyssa, De Anima et Resurrectione", "manual_critical_edition", "Source GNO/PG text and create passages.", "Explicit Gregory of Nyssa core-work gap.", None, ("work_gregory_de_anima_resurrectione",), ("gregory de anima resurrectione",), True),
    SourceItem("P2", "Gregory of Nyssa, Oratio Catechetica Magna", "manual_critical_edition", "Source GNO/PG text and create passages.", "Explicit Gregory of Nyssa core-work gap.", None, ("work_gregory_oratio_catechetica",), ("gregory oratio catechetica magna",), True),
    SourceItem("P2", "Gregory of Nyssa, Contra Eunomium", "manual_critical_edition", "Source GNO text and create passages.", "Explicit Gregory of Nyssa core-work gap.", None, ("work_gregory_contra_eunomium",), ("gregory contra eunomium",), True),
    SourceItem("P2", "Lactantius, Divine Institutes", "manual_critical_edition", "Source a verified Latin edition and create passage nodes.", "Explicit key gap.", None, ("work_lactantius_divinarum_institutionum",), ("lactantius divine institutes", "lactantius divinae institutiones"), True),
    SourceItem("P2", "Theodoret, Graecarum Affectionum Curatio", "manual_critical_edition", "Source verified Greek edition and create passages.", "Explicit key gap.", None, ("work_theodoret_graecarum_affectionum_curatio",), ("theodoret graecarum affectionum curatio",)),
    SourceItem("P2", "Diodore of Tarsus, Fragments", "manual_critical_edition", "Consolidate the existing metadata work nodes and ingest only verified fragment witnesses.", "Explicit key gap.", None, ("work_diodore_tarsus_contra_astronomos_heimarmenen", "work_diodore_tarsus_commentary_romans"), (), True),
    # Biblical targets from the passage plan and explicit task list.
    SourceItem("P3", "Romans", "db_reconciliation", "Split Romans from the generic New Testament node or create a dedicated work node.", "Tier 4 plus explicit key gap.", 430, ("work_romans", "work_new_testament"), ("romans", "new testament")),
    SourceItem("P3", "Galatians", "db_reconciliation", "Split Galatians from the generic New Testament node or create a dedicated work node.", "Tier 4 plus explicit key gap.", 149, ("work_galatians", "work_new_testament"), ("galatians", "new testament")),
    SourceItem("P3", "John", "db_reconciliation", "Split Gospel of John from the generic New Testament node or create a dedicated work node.", "Tier 4 plus explicit key gap.", 866, ("work_john_gospel", "work_new_testament"), ("gospel john", "new testament")),
    SourceItem("P3", "Sirach / Ecclesiasticus", "db_reconciliation", "Ingest or reconcile Septuagint/Vulgate Sirach passages, prioritizing Sirach 15.", "Tier 4 plus explicit key gap.", 67, ("work_sirach_a3b4c5d6",), ("sirach ecclesiasticus",)),
    SourceItem("P3", "Wisdom of Solomon", "db_reconciliation", "Ingest or reconcile Wisdom passages from Septuagint source.", "Explicit key gap.", None, ("work_wisdom_of_solomon",), ("wisdom of solomon",)),
    SourceItem("P3", "Genesis", "db_reconciliation", "Ingest or reconcile Genesis passages relevant to creation, fall, and responsibility.", "Explicit key gap.", None, ("work_genesis_u1v2w3x4",), ("genesis bereshit",)),
    SourceItem("P3", "Exodus", "db_reconciliation", "Ingest or reconcile Exodus passages relevant to hardening and divine agency.", "Explicit key gap.", None, ("work_exodus_c9d0e1f2",), ("exodus shemot",)),
    SourceItem("P3", "Ezekiel", "db_reconciliation", "Ingest or reconcile Ezekiel passages relevant to responsibility and new heart language.", "Explicit key gap.", None, ("work_ezekiel_g3h4i5j6",), ("ezekiel yechezkel",)),
    SourceItem("P3", "Septuagint Psalms", "db_reconciliation", "Split Psalms from generic Septuagint coverage and create priority passage nodes.", "Tier 4 background source.", 729, ("work_psalms", "work_septuagint"), ("psalms septuagint",)),
)


def parse_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def text_matches_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = normalize(phrase)
    if not normalized_phrase:
        return False
    if normalized_phrase in text:
        return True
    phrase_tokens = normalized_phrase.split()
    text_tokens = set(text.split())
    return all(token in text_tokens for token in phrase_tokens)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_nodes(path: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            node = json.loads(line)
            node_id = node.get("node_id") or node.get("id")
            if not node_id:
                raise ValueError(f"{path}:{line_no}: node has no node_id/id")
            node["metadata"] = parse_metadata(node.get("metadata"))
            nodes[node_id] = node
    return nodes


def is_original_passage(node_id: str, node: dict[str, Any]) -> bool:
    if node.get("type") != "passage":
        return False
    if node_id.endswith("_en"):
        return False
    metadata = node.get("metadata") or {}
    if metadata.get("translation_of") or metadata.get("source_language") == "en":
        return False
    language = str(metadata.get("language", "")).lower()
    if language in {"en", "eng", "english"}:
        return False
    return True


def count_passages_by_work(path: Path, nodes: dict[str, dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            edge = json.loads(line)
            if edge.get("relation") != "part_of":
                continue
            source_id = edge.get("source_id") or edge.get("source")
            target_id = edge.get("target_id") or edge.get("target")
            if not source_id or not target_id:
                raise ValueError(f"{path}:{line_no}: part_of edge missing source/target")
            source = nodes.get(source_id)
            if source and is_original_passage(source_id, source):
                counts[target_id] += 1
    return counts


def work_search_text(node: dict[str, Any]) -> str:
    pieces = [
        node.get("node_id", ""),
        node.get("id", ""),
        node.get("label", ""),
    ]
    return normalize(" ".join(pieces))


def find_work_nodes(item: SourceItem, nodes: dict[str, dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for node_id in item.work_node_ids:
        node = nodes.get(node_id)
        if node and node.get("type") == "work":
            found.append(node_id)
    if found:
        return found

    work_text = {
        node_id: work_search_text(node)
        for node_id, node in nodes.items()
        if node.get("type") == "work"
    }
    for phrase in item.match:
        for node_id, text in work_text.items():
            if text_matches_phrase(text, phrase):
                found.append(node_id)
    return sorted(set(found))


def derive_status(item: SourceItem, work_ids: list[str], passage_count: int) -> str:
    if item.blocker and passage_count == 0:
        return "blocker"
    if not work_ids:
        return "missing_work_node"
    if passage_count == 0:
        return "metadata_only"
    if item.expected_passages is not None and item.expected_passages <= passage_count <= int(item.expected_passages * 1.25) + 1:
        return "covered"
    return "partial"


def build_inventory(nodes_path: Path, edges_path: Path) -> dict[str, Any]:
    nodes = load_nodes(nodes_path)
    counts = count_passages_by_work(edges_path, nodes)
    entries: list[dict[str, Any]] = []

    for item in SOURCE_ITEMS:
        work_ids = find_work_nodes(item, nodes)
        passage_count = sum(counts[work_id] for work_id in work_ids)
        status = derive_status(item, work_ids, passage_count)
        labels = [nodes[work_id].get("label", work_id) for work_id in work_ids]
        notes = item.notes
        if labels and labels != [item.label]:
            notes = f"{notes} Matched KG label(s): {', '.join(labels)}."
        if item.expected_passages is not None:
            notes = f"{notes} Expected passages from plan/seed: {item.expected_passages}."

        entries.append(
            {
                "priority": item.priority,
                "status": status,
                "work_node_id": work_ids[0] if len(work_ids) == 1 else work_ids,
                "label": item.label,
                "passage_count": passage_count,
                "source_route": item.source_route,
                "recommended_next_step": item.recommended_next_step,
                "notes": notes,
            }
        )

    entries.sort(
        key=lambda row: (
            row["priority"],
            STATUS_ORDER.get(row["status"], 99),
            row["label"].lower(),
        )
    )

    status_counts = Counter(entry["status"] for entry in entries)
    return {
        "generator": "scripts/generate_ancient_source_backlog.py",
        "inputs": {
            str(nodes_path): file_sha256(nodes_path),
            str(edges_path): file_sha256(edges_path),
        },
        "entry_count": len(entries),
        "status_counts": dict(sorted(status_counts.items())),
        "entries": entries,
    }


def _db_work_search_text(row: dict[str, Any]) -> str:
    return normalize(
        " ".join(
            str(row.get(key) or "")
            for key in ("canonical_id", "title", "author", "kg_work_id")
        )
    )


def find_db_works(
    item: SourceItem,
    kg_work_ids: list[str],
    db_works: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    kg_id_set = set(kg_work_ids)
    if kg_id_set:
        found.extend(
            row for row in db_works if row.get("kg_work_id") in kg_id_set
        )
    found_ids = {row["work_id"] for row in found}

    for phrase in item.match:
        for row in db_works:
            if row["work_id"] in found_ids:
                continue
            if text_matches_phrase(_db_work_search_text(row), phrase):
                found.append(row)
                found_ids.add(row["work_id"])
    return sorted(found, key=lambda row: (row.get("author") or "", row.get("title") or ""))


def derive_live_status(
    item: SourceItem,
    work_ids: list[str],
    kg_passage_count: int,
    corpus_passage_count: int,
) -> str:
    if item.blocker and corpus_passage_count == 0 and kg_passage_count == 0:
        return "blocker"
    if corpus_passage_count > 0:
        if (
            item.expected_passages is not None
            and item.expected_passages <= corpus_passage_count <= int(item.expected_passages * 1.25) + 1
        ):
            return "covered"
        return "partial"
    if kg_passage_count > 0:
        return "kg_only"
    if work_ids:
        return "metadata_only"
    return "missing_work_node"


async def build_db_inventory(database_url: str) -> dict[str, Any]:
    import asyncpg

    conn = await asyncpg.connect(
        dsn=database_url,
        statement_cache_size=0,
        timeout=30,
        command_timeout=300,
    )
    try:
        node_rows = await conn.fetch(
            """
            SELECT node_id, node_id AS id, label, type, description, period, metadata
            FROM free_will.kg_nodes
            ORDER BY node_id
            """
        )
        nodes: dict[str, dict[str, Any]] = {}
        for row in node_rows:
            node = dict(row)
            node["metadata"] = parse_metadata(node.get("metadata"))
            nodes[node["node_id"]] = node

        kg_count_rows = await conn.fetch(
            """
            SELECT e.target_id AS work_node_id, COUNT(*)::int AS passage_count
            FROM free_will.kg_edges e
            JOIN free_will.kg_nodes p ON p.node_id = e.source_id
            WHERE e.relation = 'part_of'
              AND p.type = 'passage'
              AND p.node_id NOT LIKE '%\\_en' ESCAPE '\\'
              AND LOWER(COALESCE(p.metadata->>'language', '')) NOT IN ('en', 'eng', 'english')
            GROUP BY e.target_id
            """
        )
        kg_counts = Counter(
            {row["work_node_id"]: int(row["passage_count"]) for row in kg_count_rows}
        )

        db_works = [
            dict(row)
            for row in await conn.fetch(
                """
                SELECT
                    w.work_id::text,
                    w.kg_work_id,
                    w.canonical_id,
                    w.title,
                    w.author,
                    w.language,
                    COUNT(p.passage_id)::int AS passage_count
                FROM free_will.ancient_works w
                LEFT JOIN free_will.passages p ON p.work_id = w.work_id
                GROUP BY w.work_id, w.kg_work_id, w.canonical_id, w.title, w.author, w.language
                ORDER BY w.author, w.title, w.language
                """
            )
        ]
    finally:
        await conn.close()

    entries: list[dict[str, Any]] = []
    for item in SOURCE_ITEMS:
        work_ids = find_work_nodes(item, nodes)
        kg_passage_count = sum(kg_counts[work_id] for work_id in work_ids)
        matched_db_works = find_db_works(item, work_ids, db_works)
        corpus_passage_count = sum(
            int(row["passage_count"]) for row in matched_db_works
        )
        status = derive_live_status(
            item, work_ids, kg_passage_count, corpus_passage_count
        )

        kg_labels = [nodes[work_id].get("label", work_id) for work_id in work_ids]
        db_labels = [
            f"{row['author']}, {row['title']} [{row['language']}]"
            for row in matched_db_works
        ]
        notes = item.notes
        if kg_labels:
            notes = f"{notes} Matched KG label(s): {', '.join(kg_labels)}."
        if db_labels:
            notes = f"{notes} Matched DB work(s): {', '.join(db_labels)}."
        if item.expected_passages is not None:
            notes = f"{notes} Expected passages from plan/seed: {item.expected_passages}."

        entries.append(
            {
                "priority": item.priority,
                "status": status,
                "work_node_id": work_ids[0] if len(work_ids) == 1 else work_ids,
                "db_work_id": (
                    matched_db_works[0]["work_id"]
                    if len(matched_db_works) == 1
                    else [row["work_id"] for row in matched_db_works]
                ),
                "label": item.label,
                "passage_count": corpus_passage_count,
                "kg_passage_count": kg_passage_count,
                "source_route": item.source_route,
                "recommended_next_step": item.recommended_next_step,
                "notes": notes,
            }
        )

    entries.sort(
        key=lambda row: (
            row["priority"],
            STATUS_ORDER.get(row["status"], 99),
            row["label"].lower(),
        )
    )

    status_counts = Counter(entry["status"] for entry in entries)
    return {
        "generator": "scripts/generate_ancient_source_backlog.py",
        "source": "live_db",
        "inputs": {
            "database": "free_will schema",
            "kg_nodes": len(nodes),
            "ancient_works": len(db_works),
        },
        "entry_count": len(entries),
        "status_counts": dict(sorted(status_counts.items())),
        "entries": entries,
    }


def markdown_table(rows: list[dict[str, Any]]) -> str:
    header = "| Priority | Status | Work node | Label | DB passages | KG passages | Route | Next step |\n"
    sep = "|---|---|---:|---|---:|---:|---|---|\n"
    body = []
    for row in rows:
        work_node_id = row["work_node_id"]
        if isinstance(work_node_id, list):
            work_node = ", ".join(work_node_id) if work_node_id else ""
        else:
            work_node = work_node_id or ""
        body.append(
            "| {priority} | {status} | `{work}` | {label} | {count} | {kg_count} | {route} | {step} |".format(
                priority=row["priority"],
                status=row["status"],
                work=escape_md(work_node),
                label=escape_md(row["label"]),
                count=row["passage_count"],
                kg_count=row.get("kg_passage_count", ""),
                route=row["source_route"],
                step=escape_md(row["recommended_next_step"]),
            )
        )
    return header + sep + "\n".join(body) + "\n"


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_outputs(inventory: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Ancient Source Backlog",
        "",
        (
            "Reproducible passage-gap inventory generated from `data/kg/nodes.jsonl` "
            "and `data/kg/edges.jsonl`."
            if inventory.get("source") != "live_db"
            else "Passage-gap inventory generated from the live `free_will` Postgres schema."
        ),
        "",
        f"- Entries: {inventory['entry_count']}",
    ]
    for status, count in inventory["status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", markdown_table(inventory["entries"])])
    md_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["snapshot", "db"], default="snapshot")
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="PostgreSQL DSN for --source db. Defaults to SUPABASE_DATABASE_URL or DATABASE_URL, then the repo's audit fallback DSN.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.source == "db":
        database_url = args.database_url
        if not database_url:
            from database.scripts.philological_audit._common import dsn as default_dsn

            database_url = default_dsn()
        inventory = asyncio.run(build_db_inventory(database_url))
    else:
        inventory = build_inventory(args.nodes, args.edges)
    write_outputs(inventory, args.json_out, args.md_out)
    print(f"Wrote {args.json_out} and {args.md_out} ({inventory['entry_count']} entries)")


if __name__ == "__main__":
    main()
