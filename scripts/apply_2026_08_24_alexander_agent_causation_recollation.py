#!/usr/bin/env python3
"""Recollate and atomize Alexander's agent-causation claim cluster.

Scope is deliberately limited to ``argument_agent_causation_alex``, its De
fato 12/20 witnesses, exact source edges, two erroneous machine-translation
snapshot citations, and the corresponding SOTA registry records.

The migration distinguishes direct authorial text, rational reconstruction,
and Sharples's modern taxonomy.  It is a dry-run by default, writes a
before-image quarantine, and is idempotent.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import unicodedata
import uuid
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "alexander_agent_causation_recollation_2026_08_24"
UPDATED_AT = "2026-08-24 03:30:00+00:00"
DECIDED_AT = "2026-08-24T03:30:00Z"

ARGUMENT_ID = "argument_agent_causation_alex"
WORK_ID = "work_de_fato_alexander_c200ce_o6p7q8r9"
DF12_NODE = "passage_alex_fat_12"
DF20_NODE = "passage_alex_fat_20"
DF12_EN_NODE = "passage_alex_fat_12_en"
DF20_EN_NODE = "passage_alex_fat_20_en"
DF12_PASSAGE = "28bc2223-dabd-4bb0-933f-faa0fbcc2ef9"
DF20_PASSAGE = "d570b896-73be-45f2-bd92-de1ace50cd0b"
SHARPLES_PUB = "pub_sharples_1983_alexander_fate"
SHARPLES_POSITION = "scholarly_position_sharples_alexander_libertarian_unsupported"
TRANSMITTER_ID = "person_alexander_aphrodisias_fl200ce_n5o6p7q8"

DF12_CTS = "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:12"
DF20_CTS = "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:20"
DF12_BRUNS = "180.3-181.7"
DF20_BRUNS = "190.19-191.2"
DF12_TEXT_HASH = "434bba3b94f3e7e27d9ef72b29732e14259db01e09edf2a794d1c380150d57c2"
DF20_TEXT_HASH = "c80ca54f158191d8c0038b2aa5e53d2bf5e2491af8545d3b2c72ab30076181a7"

TEI_RELATIVE = (
    "data/audit/primary_fetch/"
    "alexander_of_aphrodisias_alexander_of_aphrodisias_de_fato/"
    "tlg0732.tlg014.1st1K-grc1.xml"
)
TEI_SHA256 = "184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f"
SHARPLES_SCAN = "data/literature_acquisition/sharples_1983_alexander_de_fato.pdf"
SHARPLES_SCAN_SHA256 = "7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638"
SHARPLES_OCR = (
    "data/literature_acquisition/sharples_1983_alexander_de_fato_ocr.pdf"
)
SHARPLES_OCR_SHA256 = "ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb"
BRUNS_SCAN_URL = (
    "https://archive.org/download/alexandriaphrodi00alex/"
    "alexandriaphrodi00alex.pdf"
)
BRUNS_SCAN_SHA256 = "41e86a6e8767acf1a8528527e8ca60841bba33b797564c0c1069086b9a380a60"

ISSUE_ID = "issue_alexander_agent_causation_reconstruction"
EVIDENCE_ID = "ev_anc_alexander_agent_origin_df12_20"
SOURCE_ID = "src_anc_alexander_de_fato"
REPORT_RELATIVE = (
    "data/audit/2026-08-24_alexander_agent_causation_recollation.json"
)
QUARANTINE_RELATIVE = (
    "data/audit/2026-08-24_alexander_agent_causation_quarantine.jsonl"
)
SCRIPT_RELATIVE = (
    "scripts/apply_2026_08_24_alexander_agent_causation_recollation.py"
)
TEST_RELATIVE = "tests/test_alexander_agent_causation_recollation.py"

EDGE_ARGUMENT_DF12 = "362d78f7-ebd9-4195-b301-829022562010"
EDGE_ARGUMENT_DF20 = "0ed1600b-aa14-45b6-9e71-bd9f2b347950"
EDGE_DF12_ARGUMENT = "62b127f9-a3be-4ecf-81a7-17d06cb26d4b"
EDGE_DF20_ARGUMENT = "b3cddbe6-d43f-4ad6-a5ed-aaed9d4d6168"
EDGE_MODERN_CONCEPT = "edae8009-83c9-41a6-8396-084ed5f5b78f"
EDGE_SHARPLES_DF12 = "9b2fe157-b7d2-4619-a0f6-ada72b7699a5"
EDGE_SHARPLES_DF20 = "81992ddc-c56a-42a4-a1ed-4404beb94f62"
TOUCHED_EDGE_IDS = {
    EDGE_ARGUMENT_DF12,
    EDGE_ARGUMENT_DF20,
    EDGE_DF12_ARGUMENT,
    EDGE_DF20_ARGUMENT,
    EDGE_MODERN_CONCEPT,
    EDGE_SHARPLES_DF12,
    EDGE_SHARPLES_DF20,
}


def stable_edge_id(source: str, relation: str, target: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://eleutheria.example/kg/edge/{source}/{relation}/{target}",
        )
    )


INTERPRETS_EDGE_ID = stable_edge_id(
    SHARPLES_POSITION, "interprets", ARGUMENT_ID
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
    return str(node.get("id") or node.get("node_id") or "")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_nfc(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def primary_source(
    *,
    node: str,
    passage: str,
    cts: str,
    bruns: str,
    sharples_printed: str,
    sharples_pdf: str,
) -> dict[str, Any]:
    return {
        "attestation": "direct_authorial_text",
        "bruns_page_lines": bruns,
        "corpus_passage_id": passage,
        "cts_urn": cts,
        "edition": (
            "I. Bruns (ed.), Alexandri Aphrodisiensis praeter commentaria "
            "scripta minora, Supplementum Aristotelicum II.2 (Berlin, 1892)"
        ),
        "kg_passage_id": node,
        "sharples_1983_translation": {
            "pdf_pages": sharples_pdf,
            "printed_pages": sharples_printed,
            "publication_id": SHARPLES_PUB,
            "scan_sha256": SHARPLES_SCAN_SHA256,
        },
        "transmitter_id": TRANSMITTER_ID,
        "transmitter_role": "author_of_direct_treatise",
    }


DIRECT_TEXT_CLAIMS = [
    {
        "id": "D12.1",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "Alexander says that on the determinists' account abolishing "
            "deliberation manifestly abolishes what depends on us."
        ),
        "verbatim_anchor_grc": (
            "Ἀναιρουμένου ... τοῦ βουλεύσασθαι ... ἀναιρεῖται καὶ τὸ ἐφ’ "
            "ἡμῖν προδήλως"
        ),
        "primary_sources": [
            primary_source(
                node=DF12_NODE,
                passage=DF12_PASSAGE,
                cts=DF12_CTS,
                bruns="180.3-4",
                sharples_printed="57",
                sharples_pdf="33",
            )
        ],
    },
    {
        "id": "D12.2",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "He reports the ordinary conception of what depends on us as the "
            "domain in which we control both doing and not doing, without "
            "following surrounding external causes wherever they lead."
        ),
        "verbatim_anchor_grc": (
            "οὗ ἡμεῖς ... καὶ τοῦ πραχθῆναι καὶ τοῦ μὴ πραχθῆναι κύριοι"
        ),
        "primary_sources": [
            primary_source(
                node=DF12_NODE,
                passage=DF12_PASSAGE,
                cts=DF12_CTS,
                bruns="180.4-7",
                sharples_printed="57",
                sharples_pdf="33",
            )
        ],
    },
    {
        "id": "D12.3",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "Choice concerns the same domain: it is the impulse with desire "
            "toward what deliberation preferred, and applies to acts through us "
            "over which we control both acting and not acting."
        ),
        "verbatim_anchor_grc": (
            "ἡ ... ἐκ τῆς βουλῆς μετὰ ὀρέξεως ὁρμὴ προαίρεσις"
        ),
        "primary_sources": [
            primary_source(
                node=DF12_NODE,
                passage=DF12_PASSAGE,
                cts=DF12_CTS,
                bruns="180.7-13",
                sharples_printed="57",
                sharples_pdf="33",
            )
        ],
    },
    {
        "id": "D12.4",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "Alexander appeals to deliberation, regret, reproach and advice as "
            "evidence that agents take themselves to be able to choose opposites "
            "rather than to have every choice fixed by pre-established causes."
        ),
        "verbatim_anchor_grc": (
            "μὴ πᾶν ὃ αἱρούμεθα ἔχειν προκαταβεβλημένας αἰτίας"
        ),
        "primary_sources": [
            primary_source(
                node=DF12_NODE,
                passage=DF12_PASSAGE,
                cts=DF12_CTS,
                bruns="180.18-181.7",
                sharples_printed="57-58",
                sharples_pdf="33-34",
            )
        ],
        "philological_caveat": (
            "At 180.19 Sharples, commentary p.142, takes the neuter 'starting "
            "point of actions' as the last point reached in deliberation, not as "
            "a direct assertion here that the agent initiates action."
        ),
    },
    {
        "id": "D20.1",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "Alexander explicitly denies that the alternative power makes acts "
            "causeless: the human being is the cause of things arising in this "
            "way, being an origin of what comes about through himself."
        ),
        "verbatim_anchor_grc": (
            "οὐ ... ἀναιτίως τι γίνεται ... αἴτιον τὸν ἄνθρωπον εἶναι, "
            "ἀρχὴν αὐτὸν ὄντα"
        ),
        "primary_sources": [
            primary_source(
                node=DF20_NODE,
                passage=DF20_PASSAGE,
                cts=DF20_CTS,
                bruns="190.19-22",
                sharples_printed="69",
                sharples_pdf="39",
            )
        ],
    },
    {
        "id": "D20.2",
        "claim_role": "direct_text",
        "attestation": "direct",
        "text": (
            "He argues ad hominem that denying the power not to act conflicts "
            "with reproach, praise, advice, exhortation, prayer and gratitude, "
            "without which human life would be unlivable."
        ),
        "verbatim_anchor_grc": (
            "οὐκ ἐπιτιμῆσαί ... οὐκ ἐπαινέσαι ... ἀβίωτος ὁ τῶν ἀνθρώπων βίος"
        ),
        "primary_sources": [
            primary_source(
                node=DF20_NODE,
                passage=DF20_PASSAGE,
                cts=DF20_CTS,
                bruns="190.22-191.2",
                sharples_printed="69",
                sharples_pdf="39",
            )
        ],
    },
]

RECONSTRUCTED_INFERENCES = [
    {
        "id": "R1",
        "claim_role": "reconstructed_inference",
        "status": "contested_interpretive_synthesis",
        "text": (
            "Reading De fato 12's two-way control together with De fato 20's "
            "agent-as-cause/origin formula as an 'agent-causation' model is a "
            "modern synthesis, not Alexander's named technical taxonomy."
        ),
        "basis_claim_ids": ["D12.2", "D12.3", "D12.4", "D20.1"],
        "secondary_sources": [
            {
                "assertor_id": "scholar_sharples_robert",
                "pdf_pages": "9; 15-16; 76; 80",
                "printed_pages": "9; 21-22; 142; 150-151",
                "publication_id": SHARPLES_PUB,
                "role": "taxonomy_and_critical_limit",
                "scan_sha256": SHARPLES_SCAN_SHA256,
            }
        ],
        "caveat": (
            "Sharples calls Alexander's conception libertarian but stresses that "
            "the ancient debate is framed as responsibility, and that Alexander "
            "does not really solve how libertarian alternatives combine with a "
            "rational account of action."
        ),
    }
]

MODERN_TAXONOMY = [
    {
        "id": "M1",
        "claim_role": "modern_taxonomy",
        "assertor_id": "scholar_sharples_robert",
        "text": (
            "Sharples classifies Alexander's conception of responsibility as "
            "libertarian rather than soft-determinist and reads the repeated "
            "power for opposites as unqualified and unrestricted."
        ),
        "secondary_sources": [
            {
                "publication_id": SHARPLES_PUB,
                "printed_pages": "9; 21-22",
                "pdf_pages": "9; 15-16",
                "scan_sha256": SHARPLES_SCAN_SHA256,
            }
        ],
        "attribution_guard": (
            "'Libertarian', 'soft determinist', 'freedom' and 'agent causation' "
            "are modern analytic labels here, not Alexander's Greek vocabulary."
        ),
    },
    {
        "id": "M2",
        "claim_role": "modern_taxonomy",
        "assertor_id": "scholar_sharples_robert",
        "text": (
            "Sharples judges the practical argument in chapters 16-21 to rely on "
            "a libertarian reading rejected by Stoic soft determinism; he calls "
            "its praise/blame form a standard anti-determinist argument, probably "
            "popularized by Carneades, and identifies fatalistic assumptions."
        ),
        "secondary_sources": [
            {
                "publication_id": SHARPLES_PUB,
                "printed_pages": "150-151",
                "pdf_pages": "80",
                "scan_sha256": SHARPLES_SCAN_SHA256,
            }
        ],
        "attribution_guard": "This is Sharples's assessment, not direct ancient text.",
    },
]

WITHDRAWN_CLAIMS = [
    {
        "id": "W1",
        "active": False,
        "former_claim": (
            "Being an origin proves that the causal regress terminates at the "
            "agent and excludes prior sufficient causes."
        ),
        "reason": "Not stated or established by De fato 12 or 20.",
    },
    {
        "id": "W2",
        "active": False,
        "former_claim": "Agent causation is superior to fate causation.",
        "reason": "No such comparative premise occurs at either collated locus.",
    },
    {
        "id": "W3",
        "active": False,
        "former_claim": (
            "αἴτιον οὐκ ἀναγκαστικόν is Alexander's technical expression."
        ),
        "reason": (
            "The Greek formula is unattested in De fato; it is a modern back-"
            "translation and cannot function as direct evidence."
        ),
    },
    {
        "id": "W4",
        "active": False,
        "former_claim": "The cluster is a formally valid complex modus tollens.",
        "reason": (
            "The two chapters supply distinct dialectical moves, not the stored "
            "formal derivation; Sharples also disputes their dialectical force."
        ),
    },
]

ARGUMENT_DESCRIPTION = (
    "Direct text. In De fato 12 (Bruns 180.3-181.7), Alexander connects what "
    "depends on us with deliberation, control of doing and not doing, choice, "
    "regret and the assumed availability of opposites. In De fato 20 (Bruns "
    "190.19-191.2), he explicitly says that this power does not make action "
    "causeless, because the human being is cause and origin of what comes about "
    "through himself; he then invokes ordinary practices of praise, blame, "
    "advice, prayer and gratitude. Interpretive limit. These passages support "
    "the minimal agent-as-cause/origin reading, but do not by themselves prove "
    "termination of every prior causal explanation or supply a Greek technical "
    "term for a non-necessitating cause. Modern taxonomy. Sharples labels "
    "Alexander's conception libertarian while warning that the label is modern, "
    "the argument is not a complete causal analysis, and its force against Stoic "
    "soft determinism is contested."
)

FORBIDDEN_ACTIVE_TEXT = (
    "αἴτιον οὐκ ἀναγκαστικόν",
    "regress of causes stops",
    "superior to fate causation",
    "formally valid as a complex modus tollens",
    "first cause",
)


def desired_argument_metadata(old: dict[str, Any]) -> dict[str, Any]:
    preserved = {
        key: copy.deepcopy(old[key])
        for key in ("created_by", "wave")
        if key in old
    }
    preserved.update(
        {
            STAMP: True,
            "argument_form": "source_critical_claim_cluster",
            "argument_type": "ancient_text_with_modern_reconstruction",
            "ancient_attestation_locus_classicus": (
                "Alexander, De fato 20, Bruns 190.19-191.2"
            ),
            "bruns_page_lines": [DF12_BRUNS, DF20_BRUNS],
            "citation_verdict": "corrected",
            "citation_verified": True,
            "conclusion": {
                "claim_role": "minimal_textual_conclusion",
                "text": (
                    "Alexander directly combines two-way control with the claim "
                    "that the human agent is a cause and origin, so this agency "
                    "is not presented as causeless. Stronger libertarian causal "
                    "claims remain modern and contested."
                ),
                "support_claim_ids": ["D12.2", "D12.3", "D20.1", "D20.2"],
                "primary_sources": [DF12_NODE, DF20_NODE],
            },
            "engaged_by_scholars": [SHARPLES_POSITION],
            "modern_taxonomy": copy.deepcopy(MODERN_TAXONOMY),
            "premises": copy.deepcopy(DIRECT_TEXT_CLAIMS),
            "reconstructed_inferences": copy.deepcopy(RECONSTRUCTED_INFERENCES),
            "scholarly_refs": [
                "R. W. Sharples, Alexander of Aphrodisias on Fate (1983), "
                "pp. 9, 21-22, 142, 150-151"
            ],
            "source_work": "De fato",
            "source_work_id": WORK_ID,
            "structured_v3": True,
            "transmission": {
                "ancient_author_id": TRANSMITTER_ID,
                "attestation_type": "direct_authorial_treatise",
                "cts_edition_urn": "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1",
                "editor": "Ivo Bruns",
                "edition": "Supplementum Aristotelicum II.2 (Berlin, 1892)",
                "local_tei": TEI_RELATIVE,
                "local_tei_sha256": TEI_SHA256,
                "sharples_scan": SHARPLES_SCAN,
                "sharples_scan_sha256": SHARPLES_SCAN_SHA256,
            },
            "validity_assessment": {
                "formally_valid": "not_formalized",
                "rationale": (
                    "The stored material is a source-critical cluster of textual "
                    "claims. Sharples, pp.150-151, treats the practical argument "
                    "as depending on a libertarian interpretation that Stoic "
                    "soft determinism rejects and identifies fatalistic defects."
                ),
                "scholarly_consensus": "contested",
            },
            "verified_reference": (
                "Alexander of Aphrodisias, De fato 12 (Bruns 180.3-181.7; "
                "Sharples 1983 trans. 57-58, comm. 142) and 20 (Bruns "
                "190.19-191.2; Sharples trans. 69, comm. 150-151)."
            ),
            "withdrawn_claims": copy.deepcopy(WITHDRAWN_CLAIMS),
        }
    )
    return preserved


def validate_argument_node(node: dict[str, Any]) -> None:
    if node_id(node) != ARGUMENT_ID:
        raise RuntimeError("wrong node passed to Alexander argument validator")
    data = metadata(node)
    if not data.get("structured_v3"):
        raise RuntimeError("Alexander argument is not structured_v3")
    premises = data.get("premises")
    if not isinstance(premises, list) or len(premises) != len(DIRECT_TEXT_CLAIMS):
        raise RuntimeError("Alexander direct claims are not fully atomized")
    ids: set[str] = set()
    for claim in premises:
        if claim.get("claim_role") != "direct_text" or claim.get("attestation") != "direct":
            raise RuntimeError("non-direct claim flattened into direct ancient text")
        if not claim.get("primary_sources"):
            raise RuntimeError(f"direct claim {claim.get('id')} lacks primary source")
        for source in claim["primary_sources"]:
            required = {
                "bruns_page_lines",
                "corpus_passage_id",
                "cts_urn",
                "edition",
                "kg_passage_id",
                "transmitter_id",
                "transmitter_role",
            }
            if not required <= source.keys():
                raise RuntimeError(f"direct claim {claim.get('id')} lacks source fields")
        ids.add(str(claim.get("id") or ""))
    if len(ids) != len(premises):
        raise RuntimeError("duplicate direct claim ids")

    reconstructions = data.get("reconstructed_inferences")
    if not isinstance(reconstructions, list):
        raise RuntimeError("missing reconstructed inference partition")
    for claim in reconstructions:
        if claim.get("claim_role") != "reconstructed_inference":
            raise RuntimeError("reconstructed claim has wrong role")
        if claim.get("status") != "withdrawn" and not claim.get("secondary_sources"):
            raise RuntimeError("active reconstruction lacks secondary support")
        if not set(claim.get("basis_claim_ids") or []) <= ids:
            raise RuntimeError("reconstruction points to unknown direct claims")

    taxonomy = data.get("modern_taxonomy")
    if not isinstance(taxonomy, list) or not taxonomy:
        raise RuntimeError("missing modern taxonomy partition")
    for claim in taxonomy:
        if claim.get("claim_role") != "modern_taxonomy":
            raise RuntimeError("modern taxonomy has wrong role")
        if claim.get("assertor_id") != "scholar_sharples_robert":
            raise RuntimeError("modern taxonomy is misattributed to Alexander")
        if not claim.get("secondary_sources"):
            raise RuntimeError("modern taxonomy lacks page-grounded source")

    withdrawn = data.get("withdrawn_claims")
    if not isinstance(withdrawn, list) or any(
        claim.get("active") is not False or not claim.get("reason")
        for claim in withdrawn
    ):
        raise RuntimeError("withdrawn claims are not explicitly inactive and reasoned")
    active_blob = json.dumps(
        {
            "description": node.get("description"),
            "premises": premises,
            "reconstructed_inferences": reconstructions,
            "conclusion": data.get("conclusion"),
        },
        ensure_ascii=False,
    ).lower()
    for forbidden in FORBIDDEN_ACTIVE_TEXT:
        if forbidden.lower() in active_blob:
            raise RuntimeError(f"unsupported claim remains active: {forbidden}")
    if data.get("argument_form") == "modus_tollens":
        raise RuntimeError("unsupported formalization remains active")


def normalize_df12_text(value: str) -> tuple[str, bool]:
    bad = "ἀναιρεῖται 40 καὶ"
    good = "ἀναιρεῖται καὶ"
    if bad in value:
        if value.count(bad) != 1:
            raise RuntimeError("unexpected multiplicity of Bruns marginal 40 artifact")
        return value.replace(bad, good), True
    if good not in value or sha256_nfc(value) != DF12_TEXT_HASH:
        raise RuntimeError("unexpected De fato 12 text state")
    return value, False


def desired_passage_metadata(
    node: dict[str, Any], *, locus: str, text_hash: str
) -> dict[str, Any]:
    data = metadata(node)
    data.pop("doxographical_confidence", None)
    data.pop("doxographical_source", None)
    is_df12 = node_id(node) == DF12_NODE
    data.update(
        {
            STAMP: True,
            "attestation_type": "direct",
            "bruns_page_lines": DF12_BRUNS if is_df12 else DF20_BRUNS,
            "citation_verdict": "corrected",
            "citation_verified": True,
            "edition": "Bruns 1892, Supplementum Aristotelicum II.2",
            "sharples_1983_translation": {
                "pdf_pages": "33-34" if is_df12 else "39",
                "printed_pages": "57-58" if is_df12 else "69",
                "scan_sha256": SHARPLES_SCAN_SHA256,
            },
            "text_content_sha256_nfc": text_hash,
            "textual_collation": {
                "bruns_scan_sha256": BRUNS_SCAN_SHA256,
                "bruns_scan_url": BRUNS_SCAN_URL,
                "local_tei_sha256": TEI_SHA256,
                "locus": locus,
                "status": "visually_collated",
            },
            "transmitter": {
                "id": TRANSMITTER_ID,
                "role": "author_of_direct_treatise",
            },
        }
    )
    if is_df12:
        data["char_length"] = 2441
        data["word_count"] = 405
        data["textual_correction"] = (
            "Removed marginal line-number '40' absorbed into the OGL/TEI text "
            "after ἀναιρεῖται; Bruns p.180 image and Sharples p.57 show it is "
            "not part of Alexander's sentence."
        )
    return data


def edge_metadata_for_argument(
    edge: dict[str, Any], *, claim_ids: list[str], locus: str, pages: str
) -> dict[str, Any]:
    return {
        **(edge.get("metadata") or {}),
        STAMP: True,
        "auto_generated": False,
        "bruns_page_lines": locus,
        "sharples_1983_printed_pages": pages,
        "source_text_role": "direct_text",
        "supports_claim_ids": claim_ids,
        "verification_basis": "visual Bruns/Sharples collation plus exact KG/corpus twin",
    }


def make_interpretation_edge() -> dict[str, Any]:
    return {
        "created_at": UPDATED_AT,
        "edge_id": INTERPRETS_EDGE_ID,
        "metadata": {
            STAMP: True,
            "assertor": "R. W. Sharples",
            "modern_taxonomy_only": True,
            "publication": SHARPLES_PUB,
            "sharples_1983_printed_pages": "9; 21-22; 142; 150-151",
        },
        "relation": "interprets",
        "source": SHARPLES_POSITION,
        "source_id": SHARPLES_POSITION,
        "target": ARGUMENT_ID,
        "target_id": ARGUMENT_ID,
        "weight": 1.0,
    }


def transform_graph_corpus(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    passages = copy.deepcopy(passages)
    citations = copy.deepcopy(citations)
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    by_node = {node_id(node): node for node in nodes}
    required = {
        ARGUMENT_ID,
        DF12_NODE,
        DF20_NODE,
        DF12_EN_NODE,
        DF20_EN_NODE,
        SHARPLES_PUB,
        SHARPLES_POSITION,
    }
    if len(by_node) != len(nodes) or not required <= by_node.keys():
        raise RuntimeError("required Alexander/Sharples KG nodes are missing or duplicated")

    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    if len(corpus_by_id) != len(passages):
        raise RuntimeError("duplicate corpus passage ids")
    for passage_id in (DF12_PASSAGE, DF20_PASSAGE):
        if passage_id not in corpus_by_id:
            raise RuntimeError(f"missing Alexander corpus passage {passage_id}")

    df12_node = by_node[DF12_NODE]
    df12_corpus = corpus_by_id[DF12_PASSAGE]
    node_text, _ = normalize_df12_text(str(df12_node.get("description") or ""))
    corpus_text, _ = normalize_df12_text(str(df12_corpus.get("text_content") or ""))
    if node_text != corpus_text:
        raise RuntimeError("De fato 12 KG/corpus texts differ before repair")
    wanted_df12 = copy.deepcopy(df12_node)
    wanted_df12["description"] = node_text
    wanted_df12["updated_at"] = UPDATED_AT
    set_metadata(
        wanted_df12,
        desired_passage_metadata(
            wanted_df12, locus="De fato 12; Bruns 180.3-181.7", text_hash=DF12_TEXT_HASH
        ),
    )
    if df12_node != wanted_df12:
        quarantine.append({"record_type": "kg_node_before", "record": df12_node})
        df12_node.clear()
        df12_node.update(wanted_df12)
        counts["passage_node_corrected"] += 1

    wanted_corpus = copy.deepcopy(df12_corpus)
    wanted_corpus["text_content"] = corpus_text
    wanted_corpus["textual_correction_2026_08_24"] = {
        "action": "removed_spurious_marginal_line_number_40",
        "authority": "Bruns 1892 p.180 scan; Sharples 1983 p.57 scan",
        "new_text_sha256_nfc": DF12_TEXT_HASH,
    }
    if df12_corpus != wanted_corpus:
        quarantine.append(
            {"record_type": "corpus_passage_before", "record": df12_corpus}
        )
        df12_corpus.clear()
        df12_corpus.update(wanted_corpus)
        counts["corpus_passage_corrected"] += 1

    df20_node = by_node[DF20_NODE]
    df20_corpus = corpus_by_id[DF20_PASSAGE]
    if df20_node.get("description") != df20_corpus.get("text_content"):
        raise RuntimeError("De fato 20 KG/corpus texts differ")
    if sha256_nfc(str(df20_node.get("description") or "")) != DF20_TEXT_HASH:
        raise RuntimeError("unexpected De fato 20 text hash")
    wanted_df20 = copy.deepcopy(df20_node)
    wanted_df20["updated_at"] = UPDATED_AT
    set_metadata(
        wanted_df20,
        desired_passage_metadata(
            wanted_df20, locus="De fato 20; Bruns 190.19-191.2", text_hash=DF20_TEXT_HASH
        ),
    )
    if df20_node != wanted_df20:
        quarantine.append({"record_type": "kg_node_before", "record": df20_node})
        df20_node.clear()
        df20_node.update(wanted_df20)
        counts["passage_node_corrected"] += 1

    argument = by_node[ARGUMENT_ID]
    wanted_argument = copy.deepcopy(argument)
    wanted_argument["description"] = ARGUMENT_DESCRIPTION
    wanted_argument["label"] = (
        "Alexander, De fato 12 & 20: two-way control and the human as cause/origin"
    )
    wanted_argument["updated_at"] = UPDATED_AT
    set_metadata(wanted_argument, desired_argument_metadata(metadata(argument)))
    validate_argument_node(wanted_argument)
    if argument != wanted_argument:
        quarantine.append({"record_type": "kg_node_before", "record": argument})
        argument.clear()
        argument.update(wanted_argument)
        counts["argument_corrected"] += 1

    by_edge = {str(edge.get("edge_id") or ""): edge for edge in edges}
    if len(by_edge) != len(edges) or not by_edge.keys() >= TOUCHED_EDGE_IDS:
        raise RuntimeError("required Alexander source edges are missing or duplicated")
    edge_specs = {
        EDGE_ARGUMENT_DF12: (["D12.1", "D12.2", "D12.3", "D12.4"], DF12_BRUNS, "57-58"),
        EDGE_DF12_ARGUMENT: (["D12.1", "D12.2", "D12.3", "D12.4"], DF12_BRUNS, "57-58"),
        EDGE_ARGUMENT_DF20: (["D20.1", "D20.2"], DF20_BRUNS, "69"),
        EDGE_DF20_ARGUMENT: (["D20.1", "D20.2"], DF20_BRUNS, "69"),
    }
    for edge_id, (claim_ids, locus, pages) in edge_specs.items():
        edge = by_edge[edge_id]
        wanted = copy.deepcopy(edge)
        wanted["metadata"] = edge_metadata_for_argument(
            edge, claim_ids=claim_ids, locus=locus, pages=pages
        )
        if edge != wanted:
            quarantine.append({"record_type": "kg_edge_before", "record": edge})
            edge.clear()
            edge.update(wanted)
            counts["source_edge_corrected"] += 1

    concept_edge = by_edge[EDGE_MODERN_CONCEPT]
    wanted_concept_edge = copy.deepcopy(concept_edge)
    wanted_concept_edge["relation"] = "discusses"
    wanted_concept_edge["metadata"] = {
        **(concept_edge.get("metadata") or {}),
        STAMP: True,
        "correction": (
            "The non-necessitating-cause concept and its Greek back-translation "
            "are modern reconstructions; Alexander does not define the term."
        ),
        "previous_relation": "defines",
        "source_text_role": "modern_taxonomy",
    }
    if concept_edge != wanted_concept_edge:
        quarantine.append({"record_type": "kg_edge_before", "record": concept_edge})
        concept_edge.clear()
        concept_edge.update(wanted_concept_edge)
        counts["modern_concept_edge_corrected"] += 1

    sharples_specs = {
        EDGE_SHARPLES_DF12: {
            "alex_de_fato_bruns_pages": DF12_BRUNS,
            "note": (
                "De fato 12: Bruns 180.3-181.7; Sharples translation pp.57-58 "
                "(PDF 33-34), commentary p.142 (PDF 76)."
            ),
            "sharples_1983_commentary_pages": "142",
            "sharples_1983_translation_pages": "57-58",
        },
        EDGE_SHARPLES_DF20: {
            "alex_de_fato_bruns_pages": DF20_BRUNS,
            "note": (
                "De fato 20: Bruns 190.19-191.2; Sharples translation p.69 "
                "(PDF 39), commentary pp.150-151 (PDF 80)."
            ),
            "sharples_1983_commentary_pages": "150-151",
            "sharples_1983_translation_pages": "69",
        },
    }
    for edge_id, correction in sharples_specs.items():
        edge = by_edge[edge_id]
        wanted = copy.deepcopy(edge)
        wanted["metadata"] = {
            **(edge.get("metadata") or {}),
            **correction,
            STAMP: True,
            "scan_sha256": SHARPLES_SCAN_SHA256,
        }
        if edge != wanted:
            quarantine.append({"record_type": "kg_edge_before", "record": edge})
            edge.clear()
            edge.update(wanted)
            counts["sharples_locus_edge_corrected"] += 1

    triples = {
        (str(edge.get("source")), str(edge.get("relation")), str(edge.get("target")))
        for edge in edges
    }
    interpretation_triple = (SHARPLES_POSITION, "interprets", ARGUMENT_ID)
    if interpretation_triple not in triples:
        edges.append(make_interpretation_edge())
        counts["modern_interpretation_edge_added"] += 1

    machine_snapshots = {
        (DF12_EN_NODE, DF12_PASSAGE),
        (DF20_EN_NODE, DF20_PASSAGE),
    }
    retained_citations: list[dict[str, Any]] = []
    removed_pairs: set[tuple[str, str]] = set()
    for row in citations:
        pair = (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        if row.get("citation_type") == "snapshot_passage_node" and pair in machine_snapshots:
            quarantine.append({"record_type": "corpus_citation_before", "record": row})
            removed_pairs.add(pair)
            counts["machine_snapshot_removed"] += 1
            continue
        retained_citations.append(row)
    if removed_pairs not in (set(), machine_snapshots):
        raise RuntimeError(f"partial machine-snapshot state: {sorted(removed_pairs)}")
    citations = retained_citations

    validate_graph_corpus(nodes, edges, passages, citations)
    return nodes, edges, passages, citations, quarantine, counts


def validate_graph_corpus(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    validate_argument_node(by_node[ARGUMENT_ID])
    corpus = {str(row.get("passage_id") or ""): row for row in passages}
    for node, passage, cts, locus, text_hash in (
        (DF12_NODE, DF12_PASSAGE, DF12_CTS, DF12_BRUNS, DF12_TEXT_HASH),
        (DF20_NODE, DF20_PASSAGE, DF20_CTS, DF20_BRUNS, DF20_TEXT_HASH),
    ):
        data = metadata(by_node[node])
        if data.get("attestation_type") != "direct":
            raise RuntimeError(f"{node} is still typed as indirect testimony")
        if data.get("cts_urn") != cts or data.get("bruns_page_lines") != locus:
            raise RuntimeError(f"{node} locus is not exact")
        if data.get("text_content_sha256_nfc") != text_hash:
            raise RuntimeError(f"{node} text hash is not declared")
        if sha256_nfc(str(by_node[node].get("description") or "")) != text_hash:
            raise RuntimeError(f"{node} KG text hash differs")
        if sha256_nfc(str(corpus[passage].get("text_content") or "")) != text_hash:
            raise RuntimeError(f"{node} corpus text hash differs")
        if by_node[node].get("description") != corpus[passage].get("text_content"):
            raise RuntimeError(f"{node} is not an exact corpus twin")
    if "ἀναιρεῖται 40 καὶ" in str(by_node[DF12_NODE].get("description") or ""):
        raise RuntimeError("Bruns marginal 40 remains in De fato 12 text")

    triples = Counter(
        (str(edge.get("source")), str(edge.get("relation")), str(edge.get("target")))
        for edge in edges
    )
    if any(count > 1 for count in triples.values()):
        raise RuntimeError("duplicate KG edge triples after Alexander recollation")
    if triples[(SHARPLES_POSITION, "interprets", ARGUMENT_ID)] != 1:
        raise RuntimeError("Sharples modern interpretation edge is missing")
    if triples[(ARGUMENT_ID, "defines", "concept_non_necessitating_cause_alex")]:
        raise RuntimeError("Alexander still directly defines the modern cause concept")
    if triples[(ARGUMENT_ID, "discusses", "concept_non_necessitating_cause_alex")] != 1:
        raise RuntimeError("modern cause concept is not safely retyped")

    by_edge = {str(edge.get("edge_id") or ""): edge for edge in edges}
    if (by_edge[EDGE_SHARPLES_DF12].get("metadata") or {}).get(
        "alex_de_fato_bruns_pages"
    ) != DF12_BRUNS:
        raise RuntimeError("Sharples-De fato 12 edge retains false locus")
    if (by_edge[EDGE_SHARPLES_DF20].get("metadata") or {}).get(
        "alex_de_fato_bruns_pages"
    ) != DF20_BRUNS:
        raise RuntimeError("Sharples-De fato 20 edge retains false locus")

    snapshots = [
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and (
            row.get("kg_node_id") in {DF12_NODE, DF20_NODE, DF12_EN_NODE, DF20_EN_NODE}
            or row.get("passage_id") in {DF12_PASSAGE, DF20_PASSAGE}
        )
    ]
    expected = {(DF12_NODE, DF12_PASSAGE), (DF20_NODE, DF20_PASSAGE)}
    if set(snapshots) != expected or len(snapshots) != 2:
        raise RuntimeError(f"Alexander 12/20 snapshots are not bijective: {snapshots}")


def replace_registry_record(
    records: list[dict[str, Any]], field: str, wanted: str, transform: Callable
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    records = copy.deepcopy(records)
    matches = [row for row in records if row.get(field) == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"expected one registry {field}={wanted}, got {len(matches)}")
    old = matches[0]
    new = transform(copy.deepcopy(old))
    if new == old:
        return records, None
    records[records.index(old)] = new
    return records, old


def transform_source(record: dict[str, Any]) -> dict[str, Any]:
    record["canonical_identifiers"] = {
        "bruns_edition": "Supplementum Aristotelicum II.2 (1892), pp.164-212",
        "cts_edition_urn": "urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1",
        "cts_work_urn": "urn:cts:greekLit:tlg0732.tlg014",
        "kg_work_id": WORK_ID,
    }
    record["acquisition"] = {
        "status": "archived_verified",
        "manifest_publication_dirs": [],
        "artifacts": [
            {"locator": TEI_RELATIVE, "role": "tei", "sha256": TEI_SHA256},
            {
                "locator": SHARPLES_SCAN,
                "role": "source_file",
                "sha256": SHARPLES_SCAN_SHA256,
            },
            {
                "locator": SHARPLES_OCR,
                "role": "ocr",
                "sha256": SHARPLES_OCR_SHA256,
            },
        ],
    }
    record["coverage"] = {
        "state": "partial",
        "kg_node_ids": [WORK_ID, ARGUMENT_ID, DF12_NODE, DF20_NODE],
        "basis": (
            "The De fato 12/20 agent-causation cluster is textually collated and "
            "claim-role atomized. Other De fato coverage remains outside this repair."
        ),
        "last_audited": "2026-08-24",
    }
    record["provenance"] = [
        {"locator": TEI_RELATIVE, "role": "tei", "sha256": TEI_SHA256},
        {"locator": REPORT_RELATIVE, "role": "audit_report"},
        {
            "accessed_at": DECIDED_AT,
            "locator": BRUNS_SCAN_URL,
            "role": "source_file",
            "sha256": BRUNS_SCAN_SHA256,
        },
    ]
    record["notes"] = (
        "Alexander is the direct authorial transmitter. Bruns 1892 is the Greek "
        "edition; Sharples 1983 supplies translation/commentary. Modern labels are "
        "kept distinct from ancient wording."
    )
    return record


def transform_evidence(record: dict[str, Any]) -> dict[str, Any]:
    record.update(
        {
            "claim_text": (
                "De fato 12 directly ties what depends on us to control of doing "
                "and not doing; De fato 20 directly denies that this makes acts "
                "causeless because the human being is cause and origin of what "
                "comes about through himself. Stronger agent-causal metaphysics "
                "is a contested reconstruction."
            ),
            "attestation": "direct",
            "claim_status": "verified",
            "locator": {
                "canonical_locus": (
                    "De fato 12, Bruns 180.3-181.7; De fato 20, Bruns 190.19-191.2"
                ),
                "edition_or_witness": (
                    "I. Bruns, Supplementum Aristotelicum II.2 (1892); "
                    "OGL/First1KGreek tlg0732.tlg014.1st1K-grc1; Sharples 1983 "
                    "translation pp.57-58, 69 and commentary pp.142, 150-151"
                ),
                "page_map_status": "not_applicable",
            },
            "quotation": {
                "status": "collated",
                "language": "grc",
                "corpus_passage_ids": [DF12_PASSAGE, DF20_PASSAGE],
            },
            "kg_targets": [ARGUMENT_ID, DF12_NODE, DF20_NODE],
            "required_verification": [
                "locus_or_page",
                "textual_exactness",
                "semantic_entailment",
                "attribution",
                "independent_review",
                "adversarial_review",
            ],
            "notes": (
                "Verified only at the minimal direct-text scope. The formal "
                "third-option, causal-regress and non-necessitating-cause claims "
                "are not upgraded to ancient attestation."
            ),
        }
    )
    return record


def transform_issue(record: dict[str, Any]) -> dict[str, Any]:
    record.update(
        {
            "status": "adjudicated",
            "summary": (
                "The Alexander agent-causation node is now atomized into direct "
                "text, contested reconstruction and Sharples's modern taxonomy. "
                "Unsupported premises are inactive, exact Bruns/Sharples loci are "
                "recorded, and a marginal '40' accidentally ingested into De fato "
                "12 has been removed."
            ),
            "affected_ids": [ARGUMENT_ID, EVIDENCE_ID, DF12_NODE, DF20_NODE],
            "evidence_artifacts": [
                {"locator": REPORT_RELATIVE, "role": "audit_report"},
                {"locator": TEI_RELATIVE, "role": "tei", "sha256": TEI_SHA256},
                {
                    "locator": SHARPLES_SCAN,
                    "role": "source_file",
                    "sha256": SHARPLES_SCAN_SHA256,
                },
                {
                    "accessed_at": DECIDED_AT,
                    "locator": BRUNS_SCAN_URL,
                    "role": "page_image",
                    "sha256": BRUNS_SCAN_SHA256,
                },
            ],
            "resolution_criteria": (
                "Adjudicated: every active direct claim has an exact primary "
                "locus and transmitter; every active reconstruction has secondary "
                "support and a contested status; modern taxonomy is attributed; "
                "withdrawn claims remain inactive; regression tests enforce this."
            ),
            "adjudication": {
                "decision": (
                    "Publish only the minimal combined reading: two-way control in "
                    "De fato 12 and the human as non-causeless cause/origin in 20. "
                    "Treat 'agent causation' and 'libertarian' as modern, contested "
                    "taxonomies, and withdraw the unsourced stronger premises."
                ),
                "rationale": (
                    "Visual collation of Bruns pp.180-181 and 190-191 and Sharples "
                    "translation/commentary pp.57-58, 69, 142, 150-151 confirms "
                    "the direct wording and exposes the inferential overreach."
                ),
                "decided_at": DECIDED_AT,
            },
        }
    )
    return record


def verification(
    *,
    suffix: str,
    target_type: str,
    target_id: str,
    stage: str,
    verifier_id: str,
    kind: str,
    group: str,
    method: str,
    locators: list[str],
    artifacts: list[dict[str, Any]],
    notes: str,
    minute: int,
) -> dict[str, Any]:
    return {
        "record_type": "verification",
        "verification_id": f"ver_alexander_agent_{suffix}_20260824",
        "target_type": target_type,
        "target_id": target_id,
        "stage": stage,
        "verifier": {
            "verifier_id": verifier_id,
            "kind": kind,
            "independence_group": group,
        },
        "method": method,
        "checked_locators": locators,
        "verdict": "pass",
        "created_at": f"2026-08-24T03:{minute:02d}:00Z",
        "artifacts": artifacts,
        "notes": notes,
    }


VERIFICATIONS = [
    verification(
        suffix="issue_primary",
        target_type="issue",
        target_id=ISSUE_ID,
        stage="primary",
        verifier_id="agent_ancient_source_coverage",
        kind="agent",
        group="visual_bruns_sharples_recollation_20260824",
        method=(
            "Visual page-by-page collation of Bruns 180-181/190-191 and Sharples "
            "57-58/69/142/150-151 against KG, corpus, OCR and edge locators"
        ),
        locators=[BRUNS_SCAN_URL, SHARPLES_SCAN, TEI_RELATIVE],
        artifacts=[{"locator": REPORT_RELATIVE, "role": "audit_report"}],
        notes="Established direct text, page maps, the marginal 40 artifact and limits.",
        minute=30,
    ),
    verification(
        suffix="issue_independent",
        target_type="issue",
        target_id=ISSUE_ID,
        stage="independent",
        verifier_id="alexander_df12_20_exact_collation_gate",
        kind="deterministic_tool",
        group="nfc_text_locus_and_edge_contract_20260824",
        method=(
            "Independent NFC hash, CTS, corpus-twin, exact-locus, source-edge and "
            "registry-schema validation"
        ),
        locators=[SCRIPT_RELATIVE, TEI_RELATIVE, SHARPLES_SCAN],
        artifacts=[{"locator": TEST_RELATIVE, "role": "test_report"}],
        notes="Rejects any missing locus, transmitter, text hash or wrong Sharples edge.",
        minute=31,
    ),
    verification(
        suffix="issue_adversarial",
        target_type="issue",
        target_id=ISSUE_ID,
        stage="adversarial",
        verifier_id="alexander_claim_role_adversarial_gate",
        kind="deterministic_tool",
        group="unsupported_reconstruction_negative_tests_20260824",
        method=(
            "Negative mutation tests for unsourced reconstruction, modern-to-ancient "
            "misattribution, pseudo-Greek terminology and false formalization"
        ),
        locators=[TEST_RELATIVE, SCRIPT_RELATIVE],
        artifacts=[{"locator": TEST_RELATIVE, "role": "test_report"}],
        notes="Every formerly active unsupported premise is explicitly withdrawn.",
        minute=32,
    ),
    verification(
        suffix="evidence_primary",
        target_type="evidence",
        target_id=EVIDENCE_ID,
        stage="primary",
        verifier_id="agent_ancient_source_coverage",
        kind="agent",
        group="visual_bruns_sharples_recollation_20260824",
        method="Direct Greek/translation collation and semantic-scope adjudication",
        locators=[BRUNS_SCAN_URL, SHARPLES_SCAN, "data/corpus/passages.jsonl"],
        artifacts=[{"locator": REPORT_RELATIVE, "role": "audit_report"}],
        notes="Evidence is verified only for the minimal direct-text claim.",
        minute=33,
    ),
    verification(
        suffix="evidence_independent",
        target_type="evidence",
        target_id=EVIDENCE_ID,
        stage="independent",
        verifier_id="alexander_df12_20_exact_collation_gate",
        kind="deterministic_tool",
        group="nfc_text_locus_and_edge_contract_20260824",
        method="Exact passage UUID, CTS, NFC text and source-target contract tests",
        locators=[TEST_RELATIVE, "data/kg/nodes.jsonl", "data/corpus/passages.jsonl"],
        artifacts=[{"locator": TEST_RELATIVE, "role": "test_report"}],
        notes="The two Greek passages remain exact, direct and separately located.",
        minute=34,
    ),
    verification(
        suffix="evidence_adversarial",
        target_type="evidence",
        target_id=EVIDENCE_ID,
        stage="adversarial",
        verifier_id="alexander_claim_role_adversarial_gate",
        kind="deterministic_tool",
        group="unsupported_reconstruction_negative_tests_20260824",
        method=(
            "Fail closed if the verified evidence inherits regress termination, "
            "causal superiority, pseudo-Greek or a formal modus-tollens claim"
        ),
        locators=[TEST_RELATIVE],
        artifacts=[{"locator": TEST_RELATIVE, "role": "test_report"}],
        notes="The verified evidence cannot silently widen beyond direct entailment.",
        minute=35,
    ),
]


def ensure_exact_shard(
    existing: list[dict[str, Any]], desired: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    if not existing:
        return copy.deepcopy(desired), True
    if existing != desired:
        raise RuntimeError("unexpected pre-existing Alexander verification shard")
    return copy.deepcopy(existing), False


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    sources, old = replace_registry_record(
        sources, "source_id", SOURCE_ID, transform_source
    )
    if old:
        quarantine.append({"record_type": "registry_source_before", "record": old})
        counts["registry_source_corrected"] += 1
    evidence, old = replace_registry_record(
        evidence, "evidence_id", EVIDENCE_ID, transform_evidence
    )
    if old:
        quarantine.append({"record_type": "registry_evidence_before", "record": old})
        counts["registry_evidence_verified"] += 1
    issues, old = replace_registry_record(
        issues, "issue_id", ISSUE_ID, transform_issue
    )
    if old:
        quarantine.append({"record_type": "registry_issue_before", "record": old})
        counts["registry_issue_adjudicated"] += 1
    verifications, changed = ensure_exact_shard(verifications, VERIFICATIONS)
    if changed:
        counts["registry_verifications_added"] += len(VERIFICATIONS)
    result = {
        "sources": sources,
        "evidence": evidence,
        "issues": issues,
        "verifications": verifications,
    }
    validate_registry(result)
    return result, quarantine, counts


def validate_registry(result: dict[str, list[dict[str, Any]]]) -> None:
    source = next(row for row in result["sources"] if row.get("source_id") == SOURCE_ID)
    if source["acquisition"]["status"] != "archived_verified":
        raise RuntimeError("Alexander source archive is not verified")
    evidence = next(
        row for row in result["evidence"] if row.get("evidence_id") == EVIDENCE_ID
    )
    if evidence.get("claim_status") != "verified":
        raise RuntimeError("Alexander evidence was not verified")
    if evidence["quotation"].get("corpus_passage_ids") != [
        DF12_PASSAGE,
        DF20_PASSAGE,
    ]:
        raise RuntimeError("registry quotation points to node ids instead of corpus UUIDs")
    issue = next(row for row in result["issues"] if row.get("issue_id") == ISSUE_ID)
    if issue.get("status") != "adjudicated" or not issue.get("adjudication"):
        raise RuntimeError("Alexander issue is not adjudicated")
    if result["verifications"] != VERIFICATIONS:
        raise RuntimeError("Alexander review shard differs from audited reviews")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def write_by_key(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> None:
    original_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if len(original_lines) != len(before):
        raise RuntimeError(f"concurrent rewrite detected for {path}")
    desired = {key(row): row for row in after}
    if len(desired) != len(after):
        raise RuntimeError(f"duplicate desired keys for {path}")
    seen: set[str] = set()
    output: list[str] = []
    for line, old in zip(original_lines, before, strict=True):
        if json.loads(line) != old:
            raise RuntimeError(f"concurrent content change detected for {path}")
        old_key = key(old)
        if old_key not in desired:
            continue
        new = desired[old_key]
        compact = ": " not in line
        output.append(
            line
            if old == new
            else json.dumps(
                new,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
        seen.add(old_key)
    for new_key in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[new_key], ensure_ascii=False, sort_keys=True))
    atomic_write(path, "\n".join(output) + "\n")


def serialize_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in records
    )


def citation_key(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(field) or "")
        for field in ("passage_id", "kg_node_id", "citation_type")
    )


def verify_artifacts(repo_root: Path) -> None:
    expected = {
        TEI_RELATIVE: TEI_SHA256,
        SHARPLES_SCAN: SHARPLES_SCAN_SHA256,
        SHARPLES_OCR: SHARPLES_OCR_SHA256,
    }
    for relative, wanted_hash in expected.items():
        path = repo_root / relative
        if not path.exists() or sha256_file(path) != wanted_hash:
            raise RuntimeError(f"missing or changed collation artifact: {relative}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    repo_root = data_root.parent
    verify_artifacts(repo_root)

    nodes_path = data_root / "kg/nodes.jsonl"
    edges_path = data_root / "kg/edges.jsonl"
    passages_path = data_root / "corpus/passages.jsonl"
    citations_path = data_root / "corpus/citations.jsonl"
    registry = data_root / "goals/sota/registry"
    sources_path = registry / "sources/seed_priority_20260824.jsonl"
    evidence_path = registry / "evidence/seed_priority_20260824.jsonl"
    issues_path = registry / "issues/seed_known_20260824.jsonl"
    verification_path = (
        registry / "verifications/alexander_agent_causation_20260824.jsonl"
    )
    report_path = repo_root / REPORT_RELATIVE
    quarantine_path = repo_root / QUARANTINE_RELATIVE

    before_nodes = read_jsonl(nodes_path)
    before_edges = read_jsonl(edges_path)
    before_passages = read_jsonl(passages_path)
    before_citations = read_jsonl(citations_path)
    nodes, edges, passages, citations, quarantine, graph_counts = (
        transform_graph_corpus(
            before_nodes, before_edges, before_passages, before_citations
        )
    )
    before_sources = read_jsonl(sources_path)
    before_evidence = read_jsonl(evidence_path)
    before_issues = read_jsonl(issues_path)
    registry_result, registry_quarantine, registry_counts = transform_registry(
        before_sources,
        before_evidence,
        before_issues,
        read_jsonl(verification_path),
    )
    quarantine.extend(registry_quarantine)
    counts = graph_counts + registry_counts
    changed = bool(counts)
    print("Alexander agent-causation recollation")
    print("mode:", "write" if args.write else "dry-run")
    print("changed:", changed)
    print("counts:", dict(sorted(counts.items())))
    print("quarantine records:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("write: no-op (already applied)")
        return 0
    if report_path.exists() or quarantine_path.exists():
        raise RuntimeError("refusing to overwrite Alexander audit/quarantine")

    report = {
        "artifacts": {
            "bruns_1892_scan": {
                "pdf_pages_inspected": "236-237; 246-247",
                "printed_pages": "180-181; 190-191",
                "sha256": BRUNS_SCAN_SHA256,
                "url": BRUNS_SCAN_URL,
            },
            "first1k_tei": {"path": TEI_RELATIVE, "sha256": TEI_SHA256},
            "sharples_1983_ocr": {
                "path": SHARPLES_OCR,
                "sha256": SHARPLES_OCR_SHA256,
            },
            "sharples_1983_scan": {
                "path": SHARPLES_SCAN,
                "sha256": SHARPLES_SCAN_SHA256,
            },
        },
        "claim_partitions": {
            "direct_text": [claim["id"] for claim in DIRECT_TEXT_CLAIMS],
            "modern_taxonomy": [claim["id"] for claim in MODERN_TAXONOMY],
            "reconstructed_inference": [
                claim["id"] for claim in RECONSTRUCTED_INFERENCES
            ],
            "withdrawn": [claim["id"] for claim in WITHDRAWN_CLAIMS],
        },
        "loci": {
            "De fato 12": {
                "bruns_page_lines": DF12_BRUNS,
                "corpus_passage_id": DF12_PASSAGE,
                "cts_urn": DF12_CTS,
                "sharples_pdf_pages": "33-34; commentary 76",
                "sharples_printed_pages": "57-58; commentary 142",
                "text_sha256_nfc": DF12_TEXT_HASH,
            },
            "De fato 20": {
                "bruns_page_lines": DF20_BRUNS,
                "corpus_passage_id": DF20_PASSAGE,
                "cts_urn": DF20_CTS,
                "sharples_pdf_pages": "39; commentary 80",
                "sharples_printed_pages": "69; commentary 150-151",
                "text_sha256_nfc": DF20_TEXT_HASH,
            },
        },
        "textual_correction": {
            "action": "removed_spurious_marginal_line_number_40",
            "locus": "De fato 12, Bruns 180.3",
            "previous_fragment": "ἀναιρεῖται 40 καὶ",
            "corrected_fragment": "ἀναιρεῖται καὶ",
        },
        "verdict": "pass",
        "verified_at": DECIDED_AT,
    }

    atomic_write(quarantine_path, serialize_jsonl(quarantine))
    write_by_key(nodes_path, before_nodes, nodes, node_id)
    write_by_key(
        edges_path, before_edges, edges, lambda row: str(row.get("edge_id") or "")
    )
    write_by_key(
        passages_path,
        before_passages,
        passages,
        lambda row: str(row.get("passage_id") or ""),
    )
    write_by_key(citations_path, before_citations, citations, citation_key)
    write_by_key(
        sources_path,
        before_sources,
        registry_result["sources"],
        lambda row: str(row.get("source_id") or ""),
    )
    write_by_key(
        evidence_path,
        before_evidence,
        registry_result["evidence"],
        lambda row: str(row.get("evidence_id") or ""),
    )
    write_by_key(
        issues_path,
        before_issues,
        registry_result["issues"],
        lambda row: str(row.get("issue_id") or ""),
    )
    atomic_write(verification_path, serialize_jsonl(registry_result["verifications"]))
    atomic_write(
        report_path, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print("write: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
