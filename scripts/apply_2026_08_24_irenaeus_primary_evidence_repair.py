#!/usr/bin/env python3
"""Repair the Irenaeus AH III.20.3 / IV.37 primary-evidence boundary.

The legacy cohort contained four citable KG/corpus twins that were actually
editorial English dossiers, unattested Greek retroversion, a byte-identical
non-translation, and machine prose.  This migration quarantines those records
and installs six witness-specific citation units:

* AH III.20.3, ancient Latin version, visually collated in SC 211;
* AH IV.37.1 and IV.37.2, ancient Latin version, SC 100;
* Greek fragment 20, transmitted by John of Damascus, Sacra Parallela;
* the two discontinuous segments of Greek fragment 21 (IV.37.2 / IV.37.4).

The split of fragment 21 is deliberate: SC 100 prints lines 1-19 at IV.37.2
and lines 20-29 at IV.37.4.  Joining them into one continuous passage would be
a new textual error.  No modern translation or editorial Greek retroversion
is ingested.  Dry-run is the default; ``--write`` is explicit.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import uuid
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "irenaeus_primary_evidence_repair_2026_08_24"
MIGRATION_TIME = "2026-08-24T06:30:00Z"
MIGRATION_SQL_TIME = "2026-08-24 06:30:00+00:00"

AUTHOR_NODE = "person_irenaeus_d202"
TRANSMITTER_NODE = "person_john_damascene_d749"
BOOK3_WORK_NODE = "work_irenaeus_adversus_haereses_book3"
BOOK4_WORK_NODE = "work_irenaeus_adversus_haereses_book4"
WORK_URN = "urn:cts:greekLit:tlg1447.tlg003"

LEGACY_NODE_IDS = frozenset(
    {
        "passage_irenaeus_ah_3_20",
        "passage_irenaeus_ah_3_20_en",
        "passage_irenaeus_ah_4_37",
        "passage_irenaeus_ah_4_37_en",
    }
)
LEGACY_PASSAGE_IDS = frozenset(
    {
        "02ba0ce3-5810-5bed-860d-5f45de51f4f2",
        "e565acd2-c206-5491-bca7-7f85d964b702",
        "4b7e7f9b-c7ef-5c62-b62f-6be046bdaffa",
        "00164aae-dd76-5d71-b526-b530fd715fa3",
    }
)
LEGACY_MANIFEST_IDS = frozenset(
    {
        "work_irenaeus_adversus_haereses_book3_grc",
        "work_irenaeus_adversus_haereses_book3_eng",
        "work_irenaeus_adversus_haereses_book4_grc",
        "work_irenaeus_adversus_haereses_book4_eng",
    }
)

LAT3_MANIFEST = "irenaeus_ah_iii_20_3_lat_sc211_collated"
LAT4_MANIFEST = "irenaeus_ah_iv_37_1_2_lat_sc100"
GRC4_MANIFEST = "irenaeus_ah_iv_grc_frag20_21_sc100"

SC211_SCAN_SHA256 = "1a0e4876113d65e70cc7282b84094fa731ebb7933c5860a0d1954abb08fa0b67"
SC100_SCAN_SHA256 = "81b1204de818ad9c06891f354f3b1728007c36a2f49abe40d6f835b0db194917"
SCO_BOOK3_LAT_SHA256 = "2e404c862ffb19b9aa954bf5ad660b95584d273ec9d59ffe33a36714cba556fc"
SCO_BOOK4_LAT_SHA256 = "33220a5e4d8033d42c2907e7f99f271c25d09fabb8797e06c62e203688e64359"
SCO_BOOK4_GRC_SHA256 = "7dc29c3512848ee1520a1cdff260d9a36f94c46e66eb3bb1b63e8af9e43b3dba"

SC100_CATALOG_URL = (
    "https://www.editionsducerf.fr/librairie/"
    "sc-100-contre-les-heresies-livre-iv-1/"
)
SCO_BOOK3_LAT_LOCATOR = (
    "SCO:Irenaeus_Lugdunensis_sec_transl/"
    "Aduersus_haereses_Liber_III_ed_Sagnard_Versio_Latina"
)
SCO_BOOK4_LAT_LOCATOR = (
    "SCO:Irenaeus_Lugdunensis_auctor_trad_indirecta_sec_transl/"
    "Aduersus_haereses_Liber_IV_Versio_Latina"
)
SCO_BOOK4_GRC_LOCATOR = (
    "SCO:Irenaeus_Lugdunensis_auctor_trad_indirecta_sec_transl/"
    "Aduersus_haereses_Liber_IV_Fragmenta_Graeca"
)

TEXTS = {
    "iii_20_3_lat": """
        Propter hoc ergo signum salutis nostrae eum qui ex Virgine Emmanuel est,
        ipse <dedit> Dominus, quoniam ipse Dominus erat qui saluabat eos, quia per
        semetipsos non habebant saluari ; et propter hoc Paulus infirmitatem hominis
        adnuntians ait : Scio enim quoniam non inhabitat in carne mea bonum,
        significans quoniam non a nobis sed a Deo est bonum salutis nostrae ; et
        iterum : Miser ego homo, quis me liberabit de corpore mortis huius ? deinde
        infert Liberatorem ; Gratia Iesu Christi Domini nostri. Hoc autem et Esaias :
        Confortamini (inquit) manus resolutae et genua debilia, adhortamini,
        pusillanimes sensu, confortamini, ne timeatis ! Ecce, Deus noster iudicium
        retribuit et retributurus est. ipse ueniet et saluabit nos ; - hoc quoniam
        non a nobis sed a Dei adiumento habuimus saluari.
    """,
    "iv_37_1_lat": """
        Illud autem quod ait : Quotiens volui colligere filios tuos et noluisti,
        veterem legem libertatis hominis manifestavit, quia liberum eum Deus fecit,
        ab initio habentem suam potestatem sicut et suam animam, ad utendum sententia
        Dei voluntarie, et non coactum ab eo. Vis enim a Deo non fit, sed bona
        sententia adest illi semper. Et propter hoc consilium quidem bonum dat
        omnibus ; posuit autem in homine potestatem electionis, quemadmodum et in
        angelis - etenim angeli rationabiles -, uti hi quidem qui obaudissent juste
        bonum sint possidentes, datum quidem a Deo, servatum vero ab ipsis ; qui autem
        non obaudierunt juste non invenientur cum bono et meritam poenam percipient,
        quoniam Deus quidem dedit benigne bonum, ipsi vero non custodierunt diligenter
        illud neque pretiosum arbitrati sunt, sed supereminentiam bonitatis
        contempserunt. Abjicientes igitur bonum et quasi respuentes, merito omnes
        <in> justum judicium incident Dei, quemadmodum et Apostolus Paulus in ea
        epistola quae est ad Romanos testificatus est, dicens ita : An divitias
        bonitatis ejus et patientiae et longanimitatis contemnis, ignorans quoniam
        bonitas Dei in paenitentiam te adducit ? Secundum autem duritiam tuam et cor
        impaenitens thesaurizas tibimetipsi iram in die irae et revelationis justi
        judicii Dei. Gloria autem et honor, inquit, omni operanti bonum. Dedit ergo
        Deus bonum, quemadmodum et Apostolus testificatur in eadem epistola, et qui
        operantur quidem illud gloriam et honorem percipient, quoniam operati sunt
        bonum cum possint non operari illud, hi autem qui illud non operantur judicium
        justum excipient Dei, quoniam non sunt operati bonum cum possint operari illud.
    """,
    "iv_37_2_lat": """
        Si autem naturaliter quidam boni, quidam vero mali facti fuissent, neque hi
        laudabiles essent quia boni sunt, tales enim facti fuerant, sed neque illi
        vituperabiles, et ipsi enim tales fuerant instituti. Sed quoniam omnes ejusdem
        sunt naturae, et potentes retinere et operari bonum, et potentes rursum
        amittere id et non facere, juste etiam apud homines sensatos - quanto magis
        apud Deum - alii quidem laudantur et dignum percipiunt testimonium electionis
        bonae et perseverantiae, alii vero accusantur et dignum percipiunt damnum eo
        quod justum et bonum reprobaverint. Et ideo prophetae [bonum quoque]
        hortabantur homines justitiam agere bonumque operari, sicut per multa
        ostendimus, quia in nobis sit hoc et propter multam neglegentiam in oblivionem
        inciderimus et consilio egeamus bono ; propter quod bonus Deus praestabat
        bonum consilium per prophetas.
    """,
    "iv_37_1_grc_frag20": """
        Βία Θεῷ οὐ πρόσεστιν, ἀγαθὴ δὲ γνώμη πάντοτε συμπάρεστιν αὐτῷ.
    """,
    "iv_37_2_grc_frag21_seg1": """
        Εἰ φύσει οἱ μὲν φαῦλοι, οἱ δὲ ἀγαθοὶ γεγόνασιν, οὐθ' οὗτοι ἐπαινετοὶ ὄντες
        ἀγαθοί, τοιοῦτοι γὰρ κατεσκευάσθησαν, οὔτ' ἐκεῖνοι μεμπτοί, οὕτως γεγονότες.
        Ἀλλ' ἐπεὶ οἱ πάντες τῆς αὐτῆς εἰσι φύσεως, δυνάμενοί τε κατασχεῖν καὶ πρᾶξαι
        τὸ ἀγαθόν, καὶ δυνάμενοι πάλιν ἀποβαλεῖν αὐτὸ καὶ μὴ ποιῆσαι, δικαίως καὶ
        παρὰ ἀνθρώποις τοῖς εὐνομουμένοις, καὶ πολὺ πρότερον παρὰ θεῷ, οἱ μὲν
        ἐπαινοῦνται καὶ ἀξίας τυγχάνουσι μαρτυρίας τῆς τοῦ καλοῦ [καθόλου] ἐκλογῆς
        καὶ ἐπιμονῆς, οἱ δὲ καταιτιῶνται καὶ ἀξίως τυγχάνουσι ζημίας τῆς τοῦ καλοῦ
        καὶ ἀγαθοῦ ἀποβολῆς. Καὶ διὰ τοῦτο οἱ προφῆται παρῇνουν τοῖς ἀνθρώποις
        δικαιοπραγεῖν καὶ τὸ ἀγαθὸν ἐξεργάζεσθαι, ὡς ἐφ' ἡμῖν ὄντος τοῦ τοιούτου καὶ
        διὰ τὴν πολλὴν ἀμέλειαν εἰς λήθην ἐκπεπτωκότων καὶ γνώμης δεομένων ἀγαθῆς,
        ἣν ὁ ἀγαθὸς Θεὸς παρεῖχεν γνώμην διὰ τῶν προφητῶν. Ταῦτα γὰρ πάντα τὸ
        αὐτεξούσιον ἐπιδείκνυσι τοῦ ἀνθρώπου καὶ τὸ συμβουλευτικὸν τοῦ Θεοῦ
        ἀποτρέποντὸς μὲν τοῦ ἀπειθεῖν αὐτῷ, ἀλλὰ μὴ βιαζομένου.
    """,
    "iv_37_4_grc_frag21_seg2": """
        Καὶ γὰρ αὐτὸ τὸ εὐαγγέλιον εἰ μὴ βούλοιτό τις ἕπεσθαι, ἐξὸν μὲν αὐτῷ
        ἐστιν, ἀσύμφερον δέ · ἡ γὰρ παρακοὴ τοῦ Θεοῦ καὶ ἀποβολὴ τοῦ ἀγαθοῦ ἔστιν
        μὲν ἐν τῷ ἀνθρώπῳ, βλάβην δὲ καὶ ζημίαν οὐ τὴν τυχοῦσαν φέρει. Καὶ διὰ
        τοῦτο ὁ Παῦλός φησιν · « Πάντα μοι ἔξεστιν, ἀλλ' οὐ πάντα συμφέρει. » Τὸ
        ἐλεύθερον τοῦ ἀνθρώπου ἐξηγούμενος, διὸ πάντα ἔξεστιν, μὴ καταναγκάζοντος
        αὐτὸν τοῦ Θεοῦ, καὶ τὸ συμφέρον δείκνυσιν, ἵνα μὴ εἰς ἐπικάλυμμα κακίας
        καταχρησώμεθα τῇ ἐλευθερίᾳ, ἀσύμφορον γὰρ τοῦτό γε.
    """,
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


TEXTS = {key: normalize_text(value) for key, value in TEXTS.items()}


def stable_passage_id(key: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://eleutheria.example/corpus/irenaeus/{key}",
        )
    )


PASSAGE_IDS = {key: stable_passage_id(key) for key in TEXTS}
NODE_IDS = {
    "iii_20_3_lat": "passage_irenaeus_ah_3_20_3_lat_sc211",
    "iv_37_1_lat": "passage_irenaeus_ah_4_37_1_lat_sc100",
    "iv_37_2_lat": "passage_irenaeus_ah_4_37_2_lat_sc100",
    "iv_37_1_grc_frag20": "passage_irenaeus_ah_4_37_1_grc_frag20",
    "iv_37_2_grc_frag21_seg1": "passage_irenaeus_ah_4_37_2_grc_frag21_seg1",
    "iv_37_4_grc_frag21_seg2": "passage_irenaeus_ah_4_37_4_grc_frag21_seg2",
}

PASSAGE_SPECS: dict[str, dict[str, Any]] = {
    "iii_20_3_lat": {
        "canonical_ref": "Irenaeus, Adversus haereses III.20.3",
        "locus": "III.20.3",
        "language": "lat",
        "role": "translation",
        "manifest": LAT3_MANIFEST,
        "work_node": BOOK3_WORK_NODE,
        "sequence": 320003,
        "printed_pages": "392",
        "pdf_pages": "196",
        "source_sha": SCO_BOOK3_LAT_SHA256,
        "scan_sha": SC211_SCAN_SHA256,
        "source_locator": SCO_BOOK3_LAT_LOCATOR,
        "transmission": "ancient_latin_translation",
        "label": "Irenaeus, Adversus haereses III.20.3 (ancient Latin; SC 211)",
    },
    "iv_37_1_lat": {
        "canonical_ref": "Irenaeus, Adversus haereses IV.37.1",
        "locus": "IV.37.1",
        "language": "lat",
        "role": "translation",
        "manifest": LAT4_MANIFEST,
        "work_node": BOOK4_WORK_NODE,
        "sequence": 437001,
        "printed_pages": "918-922",
        "pdf_pages": "459-461",
        "source_sha": SCO_BOOK4_LAT_SHA256,
        "scan_sha": SC100_SCAN_SHA256,
        "source_locator": SCO_BOOK4_LAT_LOCATOR,
        "transmission": "ancient_latin_translation",
        "label": "Irenaeus, Adversus haereses IV.37.1 (ancient Latin; SC 100)",
    },
    "iv_37_2_lat": {
        "canonical_ref": "Irenaeus, Adversus haereses IV.37.2",
        "locus": "IV.37.2",
        "language": "lat",
        "role": "translation",
        "manifest": LAT4_MANIFEST,
        "work_node": BOOK4_WORK_NODE,
        "sequence": 437002,
        "printed_pages": "922-926",
        "pdf_pages": "461-463",
        "source_sha": SCO_BOOK4_LAT_SHA256,
        "scan_sha": SC100_SCAN_SHA256,
        "source_locator": SCO_BOOK4_LAT_LOCATOR,
        "transmission": "ancient_latin_translation",
        "label": "Irenaeus, Adversus haereses IV.37.2 (ancient Latin; SC 100)",
    },
    "iv_37_1_grc_frag20": {
        "canonical_ref": "Irenaeus, Adversus haereses IV.37.1, fr. gr. 20",
        "locus": "IV.37.1",
        "language": "grc",
        "role": "original",
        "manifest": GRC4_MANIFEST,
        "work_node": BOOK4_WORK_NODE,
        "sequence": 437120,
        "printed_pages": "920",
        "pdf_pages": "460",
        "source_sha": SCO_BOOK4_GRC_SHA256,
        "scan_sha": SC100_SCAN_SHA256,
        "source_locator": SCO_BOOK4_GRC_LOCATOR,
        "transmission": "indirect_greek_fragment",
        "fragment": 20,
        "segment": 1,
        "segment_count": 1,
        "fragment_lines": "complete",
        "witness_sigla": ["C", "OAPM", "R", "E f.233r", "V f.280r"],
        "label": "Irenaeus, Adversus haereses IV.37.1 (Greek fr. 20; John Damascene)",
    },
    "iv_37_2_grc_frag21_seg1": {
        "canonical_ref": "Irenaeus, Adversus haereses IV.37.2, fr. gr. 21.1-19",
        "locus": "IV.37.2",
        "language": "grc",
        "role": "original",
        "manifest": GRC4_MANIFEST,
        "work_node": BOOK4_WORK_NODE,
        "sequence": 437211,
        "printed_pages": "922-928",
        "pdf_pages": "461-464",
        "source_sha": SCO_BOOK4_GRC_SHA256,
        "scan_sha": SC100_SCAN_SHA256,
        "source_locator": SCO_BOOK4_GRC_LOCATOR,
        "transmission": "indirect_greek_fragment",
        "fragment": 21,
        "segment": 1,
        "segment_count": 2,
        "fragment_lines": "1-19",
        "witness_sigla": ["K"],
        "label": "Irenaeus, Adversus haereses IV.37.2 (Greek fr. 21.1-19)",
    },
    "iv_37_4_grc_frag21_seg2": {
        "canonical_ref": "Irenaeus, Adversus haereses IV.37.4, fr. gr. 21.20-29",
        "locus": "IV.37.4",
        "language": "grc",
        "role": "original",
        "manifest": GRC4_MANIFEST,
        "work_node": BOOK4_WORK_NODE,
        "sequence": 437421,
        "printed_pages": "928-930",
        "pdf_pages": "464-465",
        "source_sha": SCO_BOOK4_GRC_SHA256,
        "scan_sha": SC100_SCAN_SHA256,
        "source_locator": SCO_BOOK4_GRC_LOCATOR,
        "transmission": "indirect_greek_fragment",
        "fragment": 21,
        "segment": 2,
        "segment_count": 2,
        "fragment_lines": "20-29",
        "witness_sigla": ["K"],
        "label": "Irenaeus, Adversus haereses IV.37.4 (Greek fr. 21.20-29)",
    },
}

DEPENDENT_NODE_IDS = frozenset(
    {
        AUTHOR_NODE,
        "argument_irenaeus_recapitulation_theodicy",
        "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
        "argument_irenaeuss_antignostic_argument_for_free_will_f54fe920",
        "argument_furst_2022_irenaeus_against_gnostic_natures",
    }
)

ISSUE_ID = "issue_irenaeus_false_primary_twins_and_witness_conflation"
SOURCE_ID = "src_anc_irenaeus_adversus_haereses"
EVIDENCE_IDS = frozenset(
    {
        "ev_anc_irenaeus_ah_iii_20_3_lat_sc211",
        "ev_anc_irenaeus_ah_iv_37_1_4_lat_grc_fragments",
    }
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def edge_id(edge: dict[str, Any]) -> str:
    return str(edge.get("edge_id") or "")


def edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source") or edge.get("source_id") or "")


def edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target") or edge.get("target_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        node["metadata"] = value


def sha256_text(value: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def citation_key(row: dict[str, Any]) -> str:
    return "\x1f".join(
        (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
    )


def stable_edge_id(label: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://eleutheria.example/kg/edge/irenaeus-2026-08-24/{label}",
        )
    )


def make_passage(key: str) -> dict[str, Any]:
    spec = PASSAGE_SPECS[key]
    row: dict[str, Any] = {
        "canonical_ref": spec["canonical_ref"],
        "canonical_locus": spec["locus"],
        "cts_status": "work_level_identifier_only; no passage/version CTS URN minted",
        "language": spec["language"],
        "manifestation_id": spec["manifest"],
        "passage_id": PASSAGE_IDS[key],
        "passage_role": spec["role"],
        "pdf_page_range": spec["pdf_pages"],
        "printed_page_range": spec["printed_pages"],
        "review_status": "independently_collated",
        "scan_page_map_visually_verified": True,
        "scan_sha256": spec["scan_sha"],
        "sequence_number": spec["sequence"],
        "source_artifact_sha256": spec["source_sha"],
        "source_locator": spec["source_locator"],
        "text_content": TEXTS[key],
        "text_sha256": sha256_text(TEXTS[key]),
        "transmission_class": spec["transmission"],
        "work_canonical_id": spec["manifest"],
        "work_urn": WORK_URN,
    }
    if spec["role"] == "translation":
        row.update(
            {
                "source_language": "grc",
                "source_passage_status": "lost_continuous_greek_not_mapped",
                "translation_type": "ancient_human_literal",
                "translator": "anonymous ancient Latin translator; date disputed",
            }
        )
    else:
        row.update(
            {
                "attestation_type": "indirect_fragment",
                "fragment_number": spec["fragment"],
                "fragment_lines": spec["fragment_lines"],
                "fragment_segment_count": spec["segment_count"],
                "fragment_segment_index": spec["segment"],
                "transmitting_author": "John of Damascus",
                "transmitting_author_node_id": TRANSMITTER_NODE,
                "transmitting_work": "Sacra Parallela",
                "transmitting_witness_sigla": spec["witness_sigla"],
                "witness_reference": "K. Holl, TU 20.2 (1899), p. 63",
            }
        )
    return row


def make_node(key: str) -> dict[str, Any]:
    passage = make_passage(key)
    spec = PASSAGE_SPECS[key]
    data = {k: copy.deepcopy(v) for k, v in passage.items() if k != "text_content"}
    data.update(
        {
            "author": "Irenaeus of Lyon",
            "author_node_id": AUTHOR_NODE,
            "citability": "citable",
            "citable_as_primary": True,
            "db_passage_id": passage["passage_id"],
            "text_content_sha256_nfc": passage["text_sha256"],
            "word_count": len(TEXTS[key].split()),
            "char_length": len(TEXTS[key]),
            # KG passage nodes describe the intellectual work.  The corpus row
            # below points to the concrete language/witness manifestation.
            # Keeping these two identities separate prevents the work-id gate
            # from mistaking two manifestations for two different works.
            "work_canonical_id": WORK_URN,
            "work_id": spec["work_node"],
            STAMP: True,
        }
    )
    return {
        "alternative_names": "[]",
        "created_at": MIGRATION_SQL_TIME,
        "description": TEXTS[key],
        "id": NODE_IDS[key],
        "label": spec["label"],
        "metadata": data,
        "node_id": NODE_IDS[key],
        "period": "Patristic",
        "role": None,
        "school": None,
        "type": "passage",
        "updated_at": MIGRATION_SQL_TIME,
    }


def make_manifests() -> list[dict[str, Any]]:
    rights = (
        "Ancient text only; SC/SCO critical-edition reuse rights are not "
        "adjudicated. No apparatus or modern translation is included."
    )
    return [
        {
            "artifact_sha256": SCO_BOOK3_LAT_SHA256,
            "artifact_status": "local_fingerprinted",
            "author": "Irenaeus of Lyon; anonymous ancient Latin translator",
            "canonical_id": LAT3_MANIFEST,
            "cts_urn": "",
            "cts_status": "underlying work only: " + WORK_URN,
            "edition": (
                "Latin wording machine-read from SCO's Sagnard stream and "
                "visually collated at AH III.20.3 in Rousseau-Doutreleau, SC 211 (1974)"
            ),
            "ingest_class": "local_machine_text_with_visual_critical_scan_collation",
            "language": "lat",
            "license": rights,
            "passages": 1,
            "period": "Patristic",
            "review_status": "independently_collated",
            "scan_pdf_page_count": 254,
            "scan_sha256": SC211_SCAN_SHA256,
            "source": SCO_BOOK3_LAT_LOCATOR,
            "status": "in_corpus",
            "title": "Adversus haereses III.20.3, ancient Latin version",
            "transmission_class": "ancient_latin_translation",
            "work_urn": WORK_URN,
        },
        {
            "artifact_sha256": SCO_BOOK4_LAT_SHA256,
            "artifact_status": "local_fingerprinted",
            "author": "Irenaeus of Lyon; anonymous ancient Latin translator",
            "canonical_id": LAT4_MANIFEST,
            "catalog_url": SC100_CATALOG_URL,
            "cts_urn": "",
            "cts_status": "underlying work only: " + WORK_URN,
            "edition": "Rousseau et al., SC 100, Latin version, IV.37.1-2",
            "ingest_class": "local_machine_text_with_visual_critical_scan_collation",
            "language": "lat",
            "license": rights,
            "passages": 2,
            "period": "Patristic",
            "review_status": "independently_collated",
            "scan_pdf_page_count": 503,
            "scan_sha256": SC100_SCAN_SHA256,
            "source": SCO_BOOK4_LAT_LOCATOR,
            "status": "in_corpus",
            "title": "Adversus haereses IV.37.1-2, ancient Latin version",
            "transmission_class": "ancient_latin_translation",
            "work_urn": WORK_URN,
        },
        {
            "artifact_sha256": SCO_BOOK4_GRC_SHA256,
            "artifact_status": "local_fingerprinted",
            "author": "Irenaeus of Lyon; transmitted by John of Damascus",
            "canonical_id": GRC4_MANIFEST,
            "catalog_url": SC100_CATALOG_URL,
            "cts_urn": "",
            "cts_status": "underlying work only: " + WORK_URN,
            "edition": (
                "Rousseau et al., SC 100, Greek fragments 20-21; "
                "Holl, TU 20.2 (1899), p. 63"
            ),
            "fragment_segmentation": {
                "20": ["IV.37.1:complete"],
                "21": ["IV.37.2:lines1-19", "IV.37.4:lines20-29"],
            },
            "ingest_class": "indirect_greek_fragments_visually_collated",
            "language": "grc",
            "license": rights,
            "passages": 3,
            "period": "Patristic",
            "review_status": "independently_collated",
            "scan_pdf_page_count": 503,
            "scan_sha256": SC100_SCAN_SHA256,
            "source": SCO_BOOK4_GRC_LOCATOR,
            "status": "in_corpus",
            "title": "Adversus haereses IV, Greek fragments 20-21 (Sacra Parallela)",
            "transmission_class": "indirect_greek_fragment",
            "transmitting_author": "John of Damascus",
            "transmitting_work": "Sacra Parallela",
            "work_urn": WORK_URN,
        },
    ]


def make_edge(source: str, relation: str, target: str, label: str, **metadata_values: Any) -> dict[str, Any]:
    return {
        "created_at": MIGRATION_TIME,
        "edge_id": stable_edge_id(label),
        "metadata": {STAMP: True, **metadata_values},
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


def make_edges() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, wanted_node in NODE_IDS.items():
        rows.append(
            make_edge(
                wanted_node,
                "authored_by",
                AUTHOR_NODE,
                f"{key}:authored_by",
                authorship_scope="underlying_work; translation wording remains anonymous"
                if PASSAGE_SPECS[key]["role"] == "translation"
                else "fragment attributed to Irenaeus in the transmitting witness",
            )
        )
        rows.append(
            make_edge(
                wanted_node,
                "part_of",
                PASSAGE_SPECS[key]["work_node"],
                f"{key}:part_of",
                exact_locus=PASSAGE_SPECS[key]["locus"],
            )
        )

    frag21 = NODE_IDS["iv_37_2_grc_frag21_seg1"]
    rows.extend(
        [
            make_edge(
                frag21,
                "employs",
                "concept_autexousion_christian_freedom_u1v2w3x4",
                "frag21:employs:autexousion",
                exact_term="τὸ αὐτεξούσιον",
            ),
            make_edge(
                frag21,
                "employs",
                "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
                "frag21:employs:eph_hemin",
                exact_term="ὡς ἐφ' ἡμῖν ὄντος τοῦ τοιούτου",
            ),
            make_edge(
                "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
                "evidenced_by",
                frag21,
                "amand_argument:evidenced_by:frag21",
                entailment_scope=(
                    "ancient praise/blame wording only; the Carneadean genealogy "
                    "and Christian-transposition reading remain secondary claims"
                ),
            ),
            make_edge(
                "concept_autexousion_christian_freedom_u1v2w3x4",
                "evidenced_by",
                frag21,
                "concept_autexousion:evidenced_by:frag21",
                exact_term="τὸ αὐτεξούσιον",
            ),
            make_edge(
                "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
                "evidenced_by",
                frag21,
                "concept_eph_hemin:evidenced_by:frag21",
                exact_term="ὡς ἐφ' ἡμῖν ὄντος τοῦ τοιούτου",
            ),
        ]
    )
    return rows


def make_citations() -> list[dict[str, Any]]:
    rows = [
        {
            "citation_type": "snapshot_passage_node",
            "confidence": 1.0,
            "kg_node_id": NODE_IDS[key],
            "passage_id": PASSAGE_IDS[key],
            "source_release": STAMP,
        }
        for key in TEXTS
    ]
    frag21_uuid = PASSAGE_IDS["iv_37_2_grc_frag21_seg1"]
    rows.extend(
        [
            {
                "citation_type": "partial_primary_support",
                "confidence": 0.75,
                "kg_node_id": "argument_irenaeus_recapitulation_theodicy",
                "notes": (
                    "III.20.3 directly supports human inability to save itself and "
                    "need for divine aid; it does not by itself entail the reconstructed "
                    "recapitulation/free-will synthesis."
                ),
                "passage_id": PASSAGE_IDS["iii_20_3_lat"],
            },
            {
                "citation_type": "primary_source",
                "confidence": 1.0,
                "kg_node_id": "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
                "notes": (
                    "Exact Greek praise/blame wording only; Amand's historical "
                    "genealogy still requires its secondary page evidence."
                ),
                "passage_id": frag21_uuid,
            },
            {
                "citation_type": "discusses",
                "confidence": 1.0,
                "kg_node_id": "concept_autexousion_christian_freedom_u1v2w3x4",
                "notes": "Fragment 21.1-19 explicitly contains τὸ αὐτεξούσιον.",
                "passage_id": frag21_uuid,
            },
            {
                "citation_type": "evidenced_by",
                "confidence": 1.0,
                "kg_node_id": "concept_autexousion_christian_freedom_u1v2w3x4",
                "notes": "Fragment 21.1-19 explicitly contains τὸ αὐτεξούσιον.",
                "passage_id": frag21_uuid,
            },
            {
                "citation_type": "evidenced_by",
                "confidence": 1.0,
                "kg_node_id": "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
                "notes": "Fragment 21.1-19 explicitly contains ὡς ἐφ' ἡμῖν ὄντος.",
                "passage_id": frag21_uuid,
            },
        ]
    )
    return rows


def quarantine_record(record_type: str, reason: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "reason": reason,
        "record": copy.deepcopy(record),
    }


def _repair_dependent_node(node: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(node)
    wanted_id = node_id(wanted)
    data = metadata(wanted)

    if wanted_id == AUTHOR_NODE:
        wanted["description"] = (
            "Bishop of Lyon (second century CE), originally from Asia Minor, and "
            "author of the five-book Adversus haereses. AH IV.37 preserves distinct "
            "witness strata: the ancient Latin version and Greek fragments transmitted "
            "in John of Damascus's Sacra Parallela. Greek fragment 21 at IV.37.2 "
            "contains τὸ αὐτεξούσιον and ὡς ἐφ' ἡμῖν, while AH III.20.3 is represented "
            "here only by the ancient Latin version; no continuous Greek retroversion "
            "is quoted as Irenaeus. Broader claims about recapitulation, moral growth, "
            "and anti-Gnostic argument remain attached to their exact primary and "
            "secondary loci rather than to a mixed passage dossier."
        )
        data["transmission_note_2026_08_24"] = (
            "III.20.3 ancient Latin; IV.37.1-2 ancient Latin; Greek frr. 20-21 "
            "indirectly transmitted in Sacra Parallela; SC retroversion excluded"
        )
    elif wanted_id == "argument_irenaeus_recapitulation_theodicy":
        exact = NODE_IDS["iii_20_3_lat"]
        for premise in data.get("premises", []):
            premise_id = premise.get("id")
            if premise_id in {"P2", "P3", "P5"}:
                premise["primary_sources"] = [exact]
            elif premise_id == "P1":
                premise["primary_sources"] = []
                premise["verification_status"] = "needs_exact_iii_18_2"
            if premise_id == "P3":
                premise["text"] = (
                    "Paul's testimony in Romans 7:18 and 7:24-25 is introduced as "
                    "announcing human weakness; the witness is ancient Latin, not a "
                    "transmitted continuous Greek text."
                )
        if isinstance(data.get("conclusion"), dict):
            data["conclusion"]["primary_sources"] = []
            data["conclusion"]["verification_status"] = (
                "reconstructed synthesis needs exact III.18-20 and secondary support"
            )
        data["ancient_attestation_locus_classicus"] = exact
        data["evidence_status"] = "partial_exact_primary_support_not_full_argument"
        data["primary_grounding_issue"] = (
            "III.20.3 entails only the incapacity/divine-aid components; P1, P4, P6 "
            "and the conclusion remain ungrounded at claim level"
        )
        wanted["needs_evidence"] = True
    elif wanted_id == "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed":
        exact = NODE_IDS["iv_37_2_grc_frag21_seg1"]
        data["primary_attestation"] = {
            "passage_node_id": exact,
            "locus": "Adversus haereses IV.37.2",
            "witness": "Greek fr. 21 lines 1-19 via John of Damascus, Sacra Parallela",
        }
        data["primary_entailment_scope"] = (
            "praise/blame wording only; the Carneadean genealogy and transposition "
            "interpretation require Amand pp. 222-223"
        )
        data["secondary_page_status"] = "not_registered_in_secondary_page_store"
        data["amand_text_preservation"] = (
            "Greek fr. 21 is discontinuous: IV.37.2 lines 1-19 and IV.37.4 "
            "lines 20-29, transmitted in John of Damascus, Sacra Parallela"
        )
        wanted["needs_evidence"] = True
    elif wanted_id == "argument_irenaeuss_antignostic_argument_for_free_will_f54fe920":
        data["primary_grounding_status"] = (
            "partial: IV.37.1-2 exact witnesses now available; remaining IV.37-39/V "
            "premises require premise-level collation"
        )
        data["exact_primary_support"] = [
            NODE_IDS["iv_37_1_lat"],
            NODE_IDS["iv_37_2_lat"],
            NODE_IDS["iv_37_2_grc_frag21_seg1"],
        ]
        wanted["needs_evidence"] = True
    elif wanted_id == "argument_furst_2022_irenaeus_against_gnostic_natures":
        data["primary_locus_grounding_status"] = (
            "blocked_pending_exact_AH_IV.37.6-7; the repaired IV.37.1-2 cohort "
            "does not entail the natura/voluntas claim"
        )
        data["removed_false_primary_dependency"] = "passage_irenaeus_ah_4_37"
        wanted["needs_evidence"] = True
    else:
        raise RuntimeError(f"unexpected dependent Irenaeus node: {wanted_id}")

    data[STAMP] = True
    set_metadata(wanted, data)
    wanted["updated_at"] = MIGRATION_SQL_TIME
    return wanted


def _registry_records() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    exact_nodes = list(NODE_IDS.values())
    issue = {
        "record_type": "issue",
        "issue_id": ISSUE_ID,
        "issue_type": "source_text_divergence",
        "severity": "critical",
        "factual_risk": True,
        "status": "open",
        "summary": (
            "The four false Irenaeus passage twins and every active dependency on "
            "their UUIDs are quarantined. Six exact witness units now cover III.20.3 "
            "Latin, IV.37.1-2 Latin, Greek fr.20, and both discontinuous segments of "
            "fr.21. The issue remains open because Armenian/Syriac witnesses, a "
            "reviewed modern translation, IV.37.3-7/38-39, and several reconstructed "
            "argument premises are not yet complete."
        ),
        "affected_ids": [SOURCE_ID, BOOK3_WORK_NODE, BOOK4_WORK_NODE, *exact_nodes],
        "historical_quarantined_ids": sorted(LEGACY_NODE_IDS),
        "affected_count": 3 + len(exact_nodes),
        "evidence_artifacts": [
            {"locator": "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md", "role": "audit_report"},
            {"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_quarantine.jsonl", "role": "audit_report"},
            {"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json", "role": "audit_report"},
            {"locator": "tests/test_irenaeus_primary_evidence_repair.py", "role": "test_report"},
        ],
        "resolution_criteria": (
            "P0 false twins and their active dependencies are repaired. Full closure "
            "still requires separately fingerprinted Armenian and any used Syriac "
            "witnesses, a reviewed published translation, exact IV.37.3-7/38-39 "
            "coverage, premise-level secondary evidence, and independent human sign-off."
        ),
        "progress": {
            "p0_false_twins_quarantined": True,
            "exact_passage_units": 6,
            "legacy_active_citation_count": 0,
            "fragment_21_discontinuity_preserved": True,
            "modern_translation_ingested": False,
            "armenian_ingested": False,
            "full_free_will_locus_coverage": False,
        },
    }
    source = {
        "record_type": "source",
        "source_id": SOURCE_ID,
        "source_kind": "ancient_work",
        "display_label": "Irenaeus, Adversus haereses",
        "canonical_title": "Adversus haereses / Ἔλεγχος καὶ ἀνατροπὴ τῆς ψευδωνύμου γνώσεως",
        "creators": ["Irenaeus of Lyon"],
        "date_display": "late 2nd century CE; transmission through ancient Latin, Armenian and fragments",
        "languages": ["grc", "lat", "arm", "syr"],
        "traditions": ["greek_christian", "latin_christian"],
        "topics": ["choice_will", "moral_responsibility", "evil_theodicy", "grace_predestination", "gnostic_determinism"],
        "scope_decision": "include_core",
        "identity_status": "provisional",
        "canonical_identifiers": {
            "kg_work_ids": [BOOK3_WORK_NODE, BOOK4_WORK_NODE],
            "work_level_cts_urn": WORK_URN,
            "cts_scope_warning": "work-level identifier only; no passage/version URN asserted",
        },
        "acquisition": {
            "status": "local_unregistered",
            "manifest_publication_dirs": [],
            "artifacts": [
                {"locator": "data/corpus/manifest.jsonl", "role": "catalog_record"},
                {"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json", "role": "audit_report"},
            ],
        },
        "coverage": {
            "state": "partial",
            "kg_node_ids": exact_nodes,
            "basis": (
                "Six exact, hashed and visually page-mapped citation units cover "
                "III.20.3 Latin, IV.37.1-2 Latin, Greek fr.20, and both discontinuous "
                "segments of fr.21. Armenian, Syriac, modern translation and the "
                "remaining free-will loci are not ingested."
            ),
            "last_audited": "2026-08-24",
        },
        "provenance": [
            {"locator": "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md", "role": "audit_report"},
            {"accessed_at": MIGRATION_TIME, "locator": SC100_CATALOG_URL, "role": "catalog_record"},
        ],
        "notes": (
            "Continuous Greek retroversion, ancient Latin, transmitted Greek "
            "fragments, Armenian/Syriac witnesses and modern translations remain "
            "separate manifestations. Identity remains provisional pending a full "
            "authority and transmission inventory."
        ),
    }
    evidence = [
        {
            "record_type": "evidence",
            "evidence_id": "ev_anc_irenaeus_ah_iii_20_3_lat_sc211",
            "source_id": SOURCE_ID,
            "evidence_kind": "ancient_passage",
            "claim_text": (
                "In the ancient Latin witness of AH III.20.3, Irenaeus says that "
                "salvation's good is not from us but from God and that salvation was "
                "obtained through God's aid."
            ),
            "attestation": "ancient_latin_translation",
            "claim_status": "verified",
            "locator": {
                "canonical_locus": "Adversus haereses III.20.3",
                "edition_or_witness": "SC 211 visually collated; SCO Sagnard Latin stream fingerprinted",
                "printed_pages": {"start": 392, "end": 392},
                "pdf_pages": {"start": 196, "end": 196},
                "page_map_status": "visually_verified",
            },
            "quotation": {
                "status": "collated",
                "language": "lat",
                "corpus_passage_ids": [PASSAGE_IDS["iii_20_3_lat"]],
                "text_sha256": sha256_text(TEXTS["iii_20_3_lat"]),
            },
            "kg_targets": [NODE_IDS["iii_20_3_lat"]],
            "required_verification": ["source_identity", "locus_or_page", "textual_exactness", "attribution", "independent_review", "adversarial_review"],
            "notes": "No continuous Greek and no modern translation is asserted.",
        },
        {
            "record_type": "evidence",
            "evidence_id": "ev_anc_irenaeus_ah_iv_37_1_4_lat_grc_fragments",
            "source_id": SOURCE_ID,
            "evidence_kind": "ancient_passage",
            "claim_text": (
                "AH IV.37.1-2 in the ancient Latin version argues for voluntary "
                "choice, non-coercion, and praise/blame; Greek fragments 20-21 "
                "independently preserve non-coercion, eph' hemin and autexousion. "
                "Fragment 21 is discontinuous between IV.37.2 and IV.37.4."
            ),
            "attestation": "ancient_latin_translation_and_indirect_greek_fragments",
            "claim_status": "verified",
            "locator": {
                "canonical_locus": "Adversus haereses IV.37.1-2 and IV.37.4 segment",
                "edition_or_witness": "SC 100; Greek frr. 20-21 via John of Damascus, Sacra Parallela, Holl p.63",
                "printed_pages": {"start": 918, "end": 930},
                "pdf_pages": {"start": 459, "end": 465},
                "page_map_status": "visually_verified",
            },
            "quotation": {
                "status": "collated",
                "languages": ["lat", "grc"],
                "corpus_passage_ids": [PASSAGE_IDS[key] for key in TEXTS if key != "iii_20_3_lat"],
                "text_sha256": {key: sha256_text(TEXTS[key]) for key in TEXTS if key != "iii_20_3_lat"},
            },
            "kg_targets": [NODE_IDS[key] for key in TEXTS if key != "iii_20_3_lat"],
            "required_verification": ["source_identity", "locus_or_page", "textual_exactness", "semantic_entailment", "attribution", "independent_review", "adversarial_review"],
            "notes": "No Armenian, Syriac, editorial retroversion, or modern translation is implied by this evidence unit.",
        },
    ]
    verifications = [
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_primary_source_audit_20260824",
            "target_type": "issue",
            "target_id": ISSUE_ID,
            "stage": "independent",
            "verifier": {
                "verifier_id": "agent_graphrag_engine_audit_read_only_source_chain",
                "kind": "agent",
                "independence_group": "irenaeus_sc_sco_read_only_audit_before_repair_20260824",
            },
            "method": (
                "Independently inventory every active Irenaeus node/passage/citation/"
                "manifest, hash three SCO streams and two SC scans, visually collate "
                "III.20.3 and IV.37.1-4, and seek witness-conflation counterexamples."
            ),
            "checked_locators": [
                "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md",
                SCO_BOOK3_LAT_LOCATOR,
                SCO_BOOK4_LAT_LOCATOR,
                SCO_BOOK4_GRC_LOCATOR,
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md", "role": "audit_report"}],
            "notes": (
                "The review exposed the two-segment structure of fragment 21. It "
                "does not close the broader issue or verify unregistered witnesses."
            ),
        },
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_p0_regression_20260824",
            "target_type": "issue",
            "target_id": ISSUE_ID,
            "stage": "adversarial",
            "verifier": {
                "verifier_id": "irenaeus_primary_evidence_regression_suite",
                "kind": "deterministic_tool",
                "independence_group": "irenaeus_role_language_witness_snapshot_loader_policy_gates_20260824",
            },
            "method": (
                "Reject any legacy UUID, false twin, retroversion/machine prose, "
                "fragment-21 concatenation, missing hash/page/witness, non-bijective "
                "snapshot, loader role drift, verifier mistrust, or dangling citation."
            ),
            "checked_locators": [
                "tests/test_irenaeus_primary_evidence_repair.py",
                "graphrag/tests/unit/test_verifier_v2_wiring.py",
                "database/tests/unit/test_bootstrap_supabase.py",
                "database/tests/unit/test_deploy_data_staged.py",
                "scripts/check_snapshot_passage_integrity.py",
                "scripts/check_corpus_invariants.py",
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json", "role": "test_report"}],
            "notes": "Pass is limited to the repaired six-unit P0 cohort; the issue remains open.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_iii_20_3_independent_20260824",
            "target_type": "evidence",
            "target_id": "ev_anc_irenaeus_ah_iii_20_3_lat_sc211",
            "stage": "independent",
            "verifier": {
                "verifier_id": "agent_graphrag_engine_audit_read_only_source_chain",
                "kind": "agent",
                "independence_group": "irenaeus_sc211_sco_read_only_collation_20260824",
            },
            "method": "Visually collate AH III.20.3 Latin in SC 211 against the fingerprinted SCO stream and reject continuous Greek retroversion.",
            "checked_locators": [
                "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md",
                SCO_BOOK3_LAT_LOCATOR,
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json", "role": "audit_report"}],
            "notes": "Pass is limited to the registered ancient Latin III.20.3 witness.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_iii_20_3_adversarial_20260824",
            "target_type": "evidence",
            "target_id": "ev_anc_irenaeus_ah_iii_20_3_lat_sc211",
            "stage": "adversarial",
            "verifier": {
                "verifier_id": "irenaeus_primary_evidence_regression_suite",
                "kind": "deterministic_tool",
                "independence_group": "irenaeus_text_role_snapshot_loader_policy_gates_20260824",
            },
            "method": "Reject text/hash/page drift, non-Latin language, original-role mislabelling, source UUID invention, retroversion and snapshot non-bijection.",
            "checked_locators": [
                "tests/test_irenaeus_primary_evidence_repair.py",
                "graphrag/tests/unit/test_verifier_v2_wiring.py",
                "database/tests/unit/test_bootstrap_supabase.py",
                "database/tests/unit/test_deploy_data_staged.py",
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "tests/test_irenaeus_primary_evidence_repair.py", "role": "test_report"}],
            "notes": "Deterministic pass for the one registered III.20.3 Latin citation unit.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_iv_37_fragments_independent_20260824",
            "target_type": "evidence",
            "target_id": "ev_anc_irenaeus_ah_iv_37_1_4_lat_grc_fragments",
            "stage": "independent",
            "verifier": {
                "verifier_id": "agent_graphrag_engine_audit_read_only_source_chain",
                "kind": "agent",
                "independence_group": "irenaeus_sc100_sco_read_only_collation_20260824",
            },
            "method": "Visually collate IV.37.1-2 Latin and Greek fragments 20-21, including the discontinuity of fragment 21 between IV.37.2 and IV.37.4.",
            "checked_locators": [
                "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md",
                SCO_BOOK4_LAT_LOCATOR,
                SCO_BOOK4_GRC_LOCATOR,
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "data/audit/2026-08-24_irenaeus_primary_evidence_repair.json", "role": "audit_report"}],
            "notes": "Pass covers only the registered Latin and indirect Greek units, not Armenian/Syriac or modern translation.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_irenaeus_iv_37_fragments_adversarial_20260824",
            "target_type": "evidence",
            "target_id": "ev_anc_irenaeus_ah_iv_37_1_4_lat_grc_fragments",
            "stage": "adversarial",
            "verifier": {
                "verifier_id": "irenaeus_primary_evidence_regression_suite",
                "kind": "deterministic_tool",
                "independence_group": "irenaeus_fragment_segmentation_entailment_snapshot_gates_20260824",
            },
            "method": "Reject fragment-21 concatenation, witness/hash/page drift, language-role conflation, false Fürst rewiring, non-bijective snapshots and loader/policy regressions.",
            "checked_locators": [
                "tests/test_irenaeus_primary_evidence_repair.py",
                "scripts/check_snapshot_passage_integrity.py",
                "scripts/check_kg_corpus_locus_parity.py",
                "scripts/check_kg_work_id_uniqueness.py",
            ],
            "verdict": "pass",
            "created_at": MIGRATION_TIME,
            "artifacts": [{"locator": "tests/test_irenaeus_primary_evidence_repair.py", "role": "test_report"}],
            "notes": "Deterministic pass for the five registered IV.37.1-4 Latin/Greek citation units.",
        },
    ]
    return issue, source, evidence, verifications


def _replace_registry_record(rows: list[dict[str, Any]], id_field: str, wanted: dict[str, Any]) -> tuple[list[dict[str, Any]], bool, dict[str, Any] | None]:
    output: list[dict[str, Any]] = []
    found: dict[str, Any] | None = None
    for row in rows:
        if row.get(id_field) != wanted[id_field]:
            output.append(row)
            continue
        if found is not None:
            raise RuntimeError(f"duplicate registry {id_field}={wanted[id_field]}")
        found = row
        output.append(copy.deepcopy(wanted))
    if found is None:
        output.append(copy.deepcopy(wanted))
    return output, found != wanted, found


def transform_registry(
    issues: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    issue, source, wanted_evidence, wanted_verifications = _registry_records()
    quarantine: list[dict[str, Any]] = []
    changed: list[str] = []
    issues, did_change, old = _replace_registry_record(issues, "issue_id", issue)
    if did_change:
        changed.append("registry_issue:" + ISSUE_ID)
        if old is not None:
            quarantine.append(quarantine_record("registry_issue_before", "P0 repair progress recorded without closing the broader issue", old))
    sources, did_change, old = _replace_registry_record(sources, "source_id", source)
    if did_change:
        changed.append("registry_source:" + SOURCE_ID)
        if old is not None:
            quarantine.append(quarantine_record("registry_source_before", "source coverage advanced from none to partial", old))
    for row in wanted_evidence:
        evidence, did_change, old = _replace_registry_record(evidence, "evidence_id", row)
        if did_change:
            changed.append("registry_evidence:" + row["evidence_id"])
            if old is not None:
                quarantine.append(quarantine_record("registry_evidence_before", "evidence record updated", old))
    for row in wanted_verifications:
        verifications, did_change, old = _replace_registry_record(verifications, "verification_id", row)
        if did_change:
            changed.append("registry_verification:" + row["verification_id"])
            if old is not None:
                quarantine.append(quarantine_record("registry_verification_before", "verification record updated", old))
    return issues, sources, evidence, verifications, quarantine, changed


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    issues: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    verifications: list[dict[str, Any]] | None = None,
) -> tuple[Any, ...]:
    issues = list(issues or [])
    sources = list(sources or [])
    evidence = list(evidence or [])
    verifications = list(verifications or [])
    active_node_ids = {node_id(row) for row in nodes}
    legacy_present = active_node_ids & LEGACY_NODE_IDS
    exact_present = active_node_ids & set(NODE_IDS.values())
    if legacy_present and exact_present:
        raise RuntimeError("mixed legacy/exact Irenaeus state; refusing a partial repair")
    if legacy_present != LEGACY_NODE_IDS and (
        exact_present != set(NODE_IDS.values()) or legacy_present
    ):
        raise RuntimeError(
            "Irenaeus cohort is neither the complete legacy state nor the complete repaired state"
        )

    quarantine: list[dict[str, Any]] = []
    changed: list[str] = []
    if legacy_present:
        nodes_out: list[dict[str, Any]] = []
        seen_dependents: set[str] = set()
        for row in nodes:
            wanted_id = node_id(row)
            if wanted_id in LEGACY_NODE_IDS:
                quarantine.append(quarantine_record("kg_node", "false citable passage twin removed", row))
                changed.append("remove_node:" + wanted_id)
                continue
            if wanted_id in DEPENDENT_NODE_IDS:
                replacement = _repair_dependent_node(row)
                seen_dependents.add(wanted_id)
                if replacement != row:
                    quarantine.append(quarantine_record("kg_node_before", "dependent claim/transmission metadata narrowed", row))
                    changed.append("repair_dependent_node:" + wanted_id)
                nodes_out.append(replacement)
            else:
                nodes_out.append(row)
        missing_dependents = DEPENDENT_NODE_IDS - seen_dependents
        if missing_dependents:
            raise RuntimeError(f"missing dependent Irenaeus nodes: {sorted(missing_dependents)}")
        nodes_out.extend(make_node(key) for key in TEXTS)
        changed.extend("add_node:" + NODE_IDS[key] for key in TEXTS)

        edges_out: list[dict[str, Any]] = []
        for row in edges:
            if edge_source(row) in LEGACY_NODE_IDS or edge_target(row) in LEGACY_NODE_IDS:
                quarantine.append(quarantine_record("kg_edge", "edge depended on a false Irenaeus passage twin", row))
                changed.append("remove_edge:" + edge_id(row))
                continue
            edges_out.append(row)
        existing_edge_ids = {edge_id(row) for row in edges_out}
        for row in make_edges():
            if edge_id(row) in existing_edge_ids:
                raise RuntimeError(f"new Irenaeus edge id already exists: {edge_id(row)}")
            edges_out.append(row)
            existing_edge_ids.add(edge_id(row))
            changed.append("add_edge:" + edge_id(row))

        passages_out: list[dict[str, Any]] = []
        seen_legacy_passages: set[str] = set()
        for row in passages:
            passage_id = str(row.get("passage_id") or "")
            if passage_id in LEGACY_PASSAGE_IDS:
                seen_legacy_passages.add(passage_id)
                quarantine.append(quarantine_record("corpus_passage", "false KG/corpus twin removed", row))
                changed.append("remove_passage:" + passage_id)
                continue
            passages_out.append(row)
        if seen_legacy_passages != LEGACY_PASSAGE_IDS:
            raise RuntimeError(f"missing legacy corpus passages: {sorted(LEGACY_PASSAGE_IDS - seen_legacy_passages)}")
        passages_out.extend(make_passage(key) for key in TEXTS)
        changed.extend("add_passage:" + PASSAGE_IDS[key] for key in TEXTS)

        citations_out: list[dict[str, Any]] = []
        removed_citations: list[dict[str, Any]] = []
        for row in citations:
            if str(row.get("passage_id") or "") in LEGACY_PASSAGE_IDS:
                removed_citations.append(row)
                quarantine.append(quarantine_record("citation", "citation depended on a false Irenaeus corpus twin", row))
                changed.append("remove_citation:" + citation_key(row))
                continue
            citations_out.append(row)
        if len(removed_citations) != 10:
            raise RuntimeError(f"expected exactly 10 legacy Irenaeus citations, found {len(removed_citations)}")
        new_citations = make_citations()
        citations_out.extend(new_citations)
        changed.extend("add_citation:" + citation_key(row) for row in new_citations)

        manifest_out: list[dict[str, Any]] = []
        for row in manifest:
            if str(row.get("canonical_id") or "") in LEGACY_MANIFEST_IDS:
                quarantine.append(quarantine_record("manifest", "thin/false legacy manifestation removed", row))
                changed.append("remove_manifest:" + str(row.get("canonical_id")))
                continue
            manifest_out.append(row)
        manifest_out.extend(make_manifests())
        changed.extend("add_manifest:" + row["canonical_id"] for row in make_manifests())
    else:
        nodes_out = []
        for row in nodes:
            wanted_id = node_id(row)
            if wanted_id not in set(NODE_IDS.values()):
                nodes_out.append(row)
                continue
            wanted = copy.deepcopy(row)
            data = metadata(wanted)
            if data.get("work_canonical_id") == WORK_URN:
                nodes_out.append(row)
                continue
            quarantine.append(
                quarantine_record(
                    "kg_node_before_followup",
                    (
                        "separate intellectual-work identity from the concrete "
                        "language/witness manifestation id"
                    ),
                    row,
                )
            )
            data["work_canonical_id"] = WORK_URN
            data["manifestation_id"] = PASSAGE_SPECS[
                next(key for key, value in NODE_IDS.items() if value == wanted_id)
            ]["manifest"]
            set_metadata(wanted, data)
            nodes_out.append(wanted)
            changed.append("repair_exact_node_work_identity:" + wanted_id)
        edges_out, passages_out, citations_out, manifest_out = (
            edges,
            passages,
            citations,
            manifest,
        )

    registry_result = transform_registry(issues, sources, evidence, verifications)
    issues_out, sources_out, evidence_out, verifications_out, registry_quarantine, registry_changed = registry_result
    quarantine.extend(registry_quarantine)
    changed.extend(registry_changed)
    validate(nodes_out, edges_out, passages_out, citations_out, manifest_out)
    quarantine.sort(
        key=lambda row: (
            str(row.get("record_type") or ""),
            json.dumps(row.get("record"), ensure_ascii=False, sort_keys=True),
        )
    )
    return (
        nodes_out,
        edges_out,
        passages_out,
        citations_out,
        manifest_out,
        issues_out,
        sources_out,
        evidence_out,
        verifications_out,
        quarantine,
        changed,
    )


def validate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    by_node = {node_id(row): row for row in nodes}
    by_passage = {str(row.get("passage_id") or ""): row for row in passages}
    if len(by_node) != len(nodes) or len(by_passage) != len(passages):
        raise RuntimeError("duplicate node or passage id after Irenaeus repair")
    if LEGACY_NODE_IDS & set(by_node):
        raise RuntimeError("legacy Irenaeus nodes remain active")
    if LEGACY_PASSAGE_IDS & set(by_passage):
        raise RuntimeError("legacy Irenaeus passage UUIDs remain active")
    if any(
        edge_source(row) in LEGACY_NODE_IDS or edge_target(row) in LEGACY_NODE_IDS
        for row in edges
    ):
        raise RuntimeError("an active edge still references a legacy Irenaeus node")
    if any(str(row.get("passage_id") or "") in LEGACY_PASSAGE_IDS for row in citations):
        raise RuntimeError("an active citation still references a legacy Irenaeus UUID")

    for key, wanted_node_id in NODE_IDS.items():
        node = by_node.get(wanted_node_id)
        passage = by_passage.get(PASSAGE_IDS[key])
        if node is None or passage is None:
            raise RuntimeError(f"missing exact Irenaeus unit: {key}")
        data = metadata(node)
        if node.get("description") != TEXTS[key] or passage.get("text_content") != TEXTS[key]:
            raise RuntimeError(f"KG/corpus exact text mismatch: {key}")
        expected_hash = sha256_text(TEXTS[key])
        if (
            data.get("db_passage_id") != PASSAGE_IDS[key]
            or data.get("text_content_sha256_nfc") != expected_hash
            or passage.get("text_sha256") != expected_hash
            or data.get("language") != PASSAGE_SPECS[key]["language"]
            or passage.get("language") != PASSAGE_SPECS[key]["language"]
            or data.get("passage_role") != PASSAGE_SPECS[key]["role"]
            or passage.get("passage_role") != PASSAGE_SPECS[key]["role"]
            or data.get("scan_page_map_visually_verified") is not True
            or data.get("source_artifact_sha256") != PASSAGE_SPECS[key]["source_sha"]
            or data.get("scan_sha256") != PASSAGE_SPECS[key]["scan_sha"]
            or data.get("citability") != "citable"
            or data.get("work_canonical_id") != WORK_URN
            or data.get("manifestation_id") != PASSAGE_SPECS[key]["manifest"]
            or passage.get("work_canonical_id") != PASSAGE_SPECS[key]["manifest"]
        ):
            raise RuntimeError(f"incomplete exact Irenaeus provenance: {key}")
        if PASSAGE_SPECS[key]["role"] == "translation":
            if (
                data.get("translation_type") != "ancient_human_literal"
                or passage.get("translation_type") != "ancient_human_literal"
                or data.get("source_passage_id")
                or passage.get("source_passage_id")
            ):
                raise RuntimeError(f"ancient Latin role/source mapping is dishonest: {key}")
        else:
            if (
                data.get("attestation_type") != "indirect_fragment"
                or data.get("transmitting_author_node_id") != TRANSMITTER_NODE
                or not data.get("fragment_number")
            ):
                raise RuntimeError(f"Greek fragment witness metadata incomplete: {key}")

    snapshots = [
        row
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("kg_node_id") in set(NODE_IDS.values())
    ]
    pairs = {(row.get("kg_node_id"), row.get("passage_id")) for row in snapshots}
    expected_pairs = {(NODE_IDS[key], PASSAGE_IDS[key]) for key in TEXTS}
    if len(snapshots) != len(TEXTS) or pairs != expected_pairs:
        raise RuntimeError("Irenaeus exact snapshots are not bijective")

    by_manifest = {str(row.get("canonical_id") or ""): row for row in manifest}
    expected_counts = {LAT3_MANIFEST: 1, LAT4_MANIFEST: 2, GRC4_MANIFEST: 3}
    for manifest_id, count in expected_counts.items():
        row = by_manifest.get(manifest_id)
        actual = sum(1 for passage in passages if passage.get("work_canonical_id") == manifest_id)
        if (
            row is None
            or row.get("status") != "in_corpus"
            or row.get("passages") != count
            or actual != count
            or not row.get("artifact_sha256")
            or not row.get("scan_sha256")
            or row.get("review_status") != "independently_collated"
        ):
            raise RuntimeError(f"Irenaeus manifestation incomplete: {manifest_id}")
    if set(LEGACY_MANIFEST_IDS) & set(by_manifest):
        raise RuntimeError("legacy Irenaeus manifestation remains active")

    frag21_rows = [
        by_passage[PASSAGE_IDS["iv_37_2_grc_frag21_seg1"]],
        by_passage[PASSAGE_IDS["iv_37_4_grc_frag21_seg2"]],
    ]
    if [row["fragment_segment_index"] for row in frag21_rows] != [1, 2]:
        raise RuntimeError("fragment 21 segment order was lost")
    if any("Καὶ γὰρ αὐτὸ τὸ εὐαγγέλιον" in row["text_content"] for row in frag21_rows[:1]):
        raise RuntimeError("fragment 21 IV.37.2 falsely concatenates the IV.37.4 segment")

    expected_dependency_pairs = {
        (
            "argument_irenaeus_adv_haer_iv_37_praise_blame_transposed",
            PASSAGE_IDS["iv_37_2_grc_frag21_seg1"],
            "primary_source",
        ),
        (
            "concept_autexousion_christian_freedom_u1v2w3x4",
            PASSAGE_IDS["iv_37_2_grc_frag21_seg1"],
            "evidenced_by",
        ),
        (
            "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7",
            PASSAGE_IDS["iv_37_2_grc_frag21_seg1"],
            "evidenced_by",
        ),
    }
    active_triplets = {
        (row.get("kg_node_id"), row.get("passage_id"), row.get("citation_type"))
        for row in citations
    }
    if not expected_dependency_pairs <= active_triplets:
        raise RuntimeError("directly entailed Irenaeus dependencies were not rewired")
    if any(
        row.get("kg_node_id") == "argument_furst_2022_irenaeus_against_gnostic_natures"
        and row.get("passage_id") in set(PASSAGE_IDS.values())
        for row in citations
    ):
        raise RuntimeError("Fürst IV.37.6 claim was wrongly grounded in IV.37.1-2")

    serialized = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True)
        for row in [*(by_node[node_id] for node_id in NODE_IDS.values()), *(by_passage[passage_id] for passage_id in PASSAGE_IDS.values())]
    )
    forbidden = (
        "source_model\": \"claude",
        "translation_type\": \"machine",
        "τοὺς μὴ δυναμένους σῴζειν ἑαυτούς",
        "Textus_reconstructus",
        "editorial_reconstruction",
    )
    if any(marker in serialized for marker in forbidden):
        raise RuntimeError("machine prose or Greek retroversion entered the exact cohort")


def _jsonl_bytes(rows: Iterable[dict[str, Any]], *, compact: bool = True) -> bytes:
    separators = (",", ":") if compact else None
    return (
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=separators) + "\n"
            for row in rows
        ).encode("utf-8")
    )


def render_preserving(
    path: Path,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> bytes:
    original_lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate identity in rendered {path}")
    output: list[str] = []
    seen: set[str] = set()
    for line in original_lines:
        old = json.loads(line)
        wanted_key = key(old)
        if wanted_key not in desired:
            continue
        new = desired[wanted_key]
        compact = ": " not in line
        output.append(
            line
            if old == new
            else json.dumps(new, ensure_ascii=False, sort_keys=True, separators=(",", ":") if compact else None)
        )
        seen.add(wanted_key)
    for wanted_key in sorted(desired.keys() - seen):
        compact = path.name in {"passages.jsonl", "citations.jsonl", "manifest.jsonl"}
        output.append(json.dumps(desired[wanted_key], ensure_ascii=False, sort_keys=True, separators=(",", ":") if compact else None))
    return ("\n".join(output) + "\n").encode("utf-8")


def write_transaction(payloads: dict[Path, bytes], expected_hashes: dict[Path, str]) -> None:
    for path, expected in expected_hashes.items():
        if sha256_file(path) != expected:
            raise RuntimeError(f"concurrent drift detected before write: {path}")
    staged: dict[Path, Path] = {}
    originals: dict[Path, bytes | None] = {}
    try:
        for path, payload in payloads.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None
            with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                staged[path] = Path(handle.name)
        replaced: list[Path] = []
        try:
            for path, tmp in staged.items():
                os.replace(tmp, path)
                replaced.append(path)
        except Exception:
            for path in reversed(replaced):
                old = originals[path]
                if old is None:
                    path.unlink(missing_ok=True)
                    continue
                with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
                    handle.write(old)
                    handle.flush()
                    os.fsync(handle.fileno())
                    restore = Path(handle.name)
                os.replace(restore, path)
            raise
    finally:
        for tmp in staged.values():
            tmp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
        "issues": data_root / "goals/sota/registry/issues/irenaeus_20260824.jsonl",
        "sources": data_root / "goals/sota/registry/sources/irenaeus_20260824.jsonl",
        "evidence": data_root / "goals/sota/registry/evidence/irenaeus_20260824.jsonl",
        "verifications": data_root / "goals/sota/registry/verifications/irenaeus_20260824.jsonl",
    }
    inputs = {name: read_jsonl(path) for name, path in paths.items()}
    expected_hashes = {path: sha256_file(path) for path in paths.values() if path.exists()}
    result = transform(
        inputs["nodes"], inputs["edges"], inputs["passages"], inputs["citations"],
        inputs["manifest"], inputs["issues"], inputs["sources"],
        inputs["evidence"], inputs["verifications"],
    )
    (*datasets, quarantine, changed) = result
    print("Irenaeus primary-evidence repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("operations recorded:", len(changed))
    print("records quarantined:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0

    rendered = {
        paths["nodes"]: render_preserving(paths["nodes"], datasets[0], node_id),
        paths["edges"]: render_preserving(paths["edges"], datasets[1], edge_id),
        paths["passages"]: render_preserving(paths["passages"], datasets[2], lambda row: str(row.get("passage_id") or "")),
        paths["citations"]: render_preserving(paths["citations"], datasets[3], citation_key),
        paths["manifest"]: render_preserving(paths["manifest"], datasets[4], lambda row: str(row.get("canonical_id") or "")),
        paths["issues"]: render_preserving(paths["issues"], datasets[5], lambda row: str(row.get("issue_id") or "")),
        paths["sources"]: render_preserving(paths["sources"], datasets[6], lambda row: str(row.get("source_id") or "")),
        paths["evidence"]: render_preserving(paths["evidence"], datasets[7], lambda row: str(row.get("evidence_id") or "")),
        paths["verifications"]: render_preserving(paths["verifications"], datasets[8], lambda row: str(row.get("verification_id") or "")),
    }
    quarantine_path = data_root / "audit/2026-08-24_irenaeus_primary_evidence_quarantine.jsonl"
    report_path = data_root / "audit/2026-08-24_irenaeus_primary_evidence_repair.json"
    existing_quarantine = read_jsonl(quarantine_path)
    previous_report = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if report_path.exists()
        else None
    )
    reconciliation = [
        {
            "legacy_node": row["record"].get("kg_node_id"),
            "legacy_passage_id": row["record"].get("passage_id"),
            "legacy_citation_type": row["record"].get("citation_type"),
            "action": (
                "quarantined_and_reconciled_by_claim_level_rules; see active citations "
                "and dependent-node primary_grounding_status"
            ),
        }
        for row in quarantine
        if row.get("record_type") == "citation"
    ]
    operation_breakdown = dict(
        sorted(Counter(item.split(":", 1)[0] for item in changed).items())
    )
    legacy_manifests_before = {
        str(row.get("canonical_id") or "")
        for row in inputs["manifest"]
        if str(row.get("canonical_id") or "") in LEGACY_MANIFEST_IDS
    }
    report = {
        "status": "p0_false_twins_repaired_broader_irenaeus_issue_remains_open",
        "operations_recorded": len(changed),
        "operations_breakdown": operation_breakdown,
        "quarantined_records": len(quarantine),
        "legacy_nodes_removed": sorted(LEGACY_NODE_IDS),
        "legacy_passage_ids_removed": sorted(LEGACY_PASSAGE_IDS),
        "exact_nodes_added": list(NODE_IDS.values()),
        "exact_passage_ids": PASSAGE_IDS,
        "manifests": [row["canonical_id"] for row in make_manifests()],
        "legacy_manifests": {
            "removed_because_present": sorted(legacy_manifests_before),
            "already_absent_before_migration": sorted(
                LEGACY_MANIFEST_IDS - legacy_manifests_before
            ),
        },
        "source_hashes": {
            "sc211_scan": SC211_SCAN_SHA256,
            "sc100_scan": SC100_SCAN_SHA256,
            "sco_book3_latin": SCO_BOOK3_LAT_SHA256,
            "sco_book4_latin": SCO_BOOK4_LAT_SHA256,
            "sco_book4_greek_fragments": SCO_BOOK4_GRC_SHA256,
        },
        "fragment_21": {
            "status": "preserved_as_two_discontinuous_passage_units",
            "segment_1": "IV.37.2, lines 1-19, printed 922-928",
            "segment_2": "IV.37.4, lines 20-29, printed 928-930",
        },
        "citation_reconciliation": reconciliation,
        "deliberately_not_ingested": [
            "SC Greek editorial retroversion",
            "SC French translation",
            "any invented English translation",
            "unverified Armenian or Syriac text",
        ],
        "independent_review": {
            "artifact": "docs/data-audit/2026-08-24-irenaeus-free-will-data-audit.md",
            "scope": "source hashes, visual page collation, active-data adversarial inventory",
            "verdict": "pass_for_six_registered_units_only",
        },
        "remaining_blockers": [
            "Armenian and any used Syriac witness manifestations",
            "reviewed published modern translation",
            "exact AH IV.37.3-7 and IV.38-39",
            "premise-level secondary evidence for reconstructed argument nodes",
            "independent human scholarly sign-off",
        ],
    }
    if previous_report is not None:
        followup = {
            "at": MIGRATION_TIME,
            "operations_recorded": len(changed),
            "operations_breakdown": operation_breakdown,
            "quarantined_records": len(quarantine),
            "reason": (
                "Separate KG intellectual-work identity from corpus "
                "language/witness manifestation identity after the work-id gate."
            ),
        }
        report = previous_report
        report.setdefault("followup_repairs", []).append(followup)
        report["quarantined_records"] = len(existing_quarantine) + len(quarantine)
        report["latest_validation_status"] = "work_identity_and_manifestation_identity_separated"
    rendered[quarantine_path] = _jsonl_bytes(
        [*existing_quarantine, *quarantine], compact=False
    )
    rendered[report_path] = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_transaction(rendered, expected_hashes)
    print("wrote:", *rendered.keys())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
