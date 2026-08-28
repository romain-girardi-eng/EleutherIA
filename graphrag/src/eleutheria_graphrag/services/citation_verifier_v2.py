"""
Citation Verifier v2 — adversarial post-synthesis audit.

Replaces the disabled v1 verifier (false-positive issues per project memory).
The contract is different by design:

* v1 was a soft confirmation pass on the synthesizer's own evidence cache. It
  asked "does the evidence text we already have support the claim?" — which
  fails silently when the synthesizer pulled the wrong passage in the first
  place.
* **v2 is adversarial.** For every (claim, citation_id) pair it re-fetches
  the passage *fresh* from the corpus (the synthesizer's text is never
  trusted), reads the verbatim content, and returns one of four statuses:
  ``VERIFIED`` / ``WEAK`` / ``REJECTED`` / ``MISSING``. The matching opencode
  agent (.opencode/agent/citation-verifier.md) carries the same instructions
  when this runs as an opencode subagent.
* **Two evidence kinds.** A citation that resolves to a corpus passage is
  audited against the verbatim passage text (``evidence_kind="passage"``).
  A citation that resolves to a knowledge-graph node with no corpus passage
  behind it — a scholarly argument, a scholar's position, a person — is
  audited against the node's own curated statement (``evidence_kind="node"``),
  with the prompt saying plainly that the evidence is a secondary-layer KG
  record, not a primary text. Nodes with too little text to audit stay
  ``MISSING``. Node evidence is never a fallback for a passage citation.

Concurrency is capped via ``asyncio.Semaphore`` to avoid hammering the LLM
provider. The verifier degrades gracefully: if its own LLM call fails after
retries, the citation is marked ``WEAK`` (never silently passed) so a human
or a downstream pass can re-examine it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.agents.citability import CitabilityTier, evidence_policy
from eleutheria_graphrag.agents.prompts import delimit_retrieved_text
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    DraftClaim,
    SynthesizedDraft,
    VerificationReport,
)
from eleutheria_graphrag.services.json_extractor import extract_json_object
from eleutheria_graphrag.services.secondary_evidence import (
    SecondaryPageFetcher,
    build_db_secondary_page_fetcher,
)
from eleutheria_graphrag.services.snapshot_retrieval import normalize_mapping

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Adversarial verification prompt — note the framing ("find why this is bad").
VERIFY_PROMPT = """\
You are an ADVERSARIAL citation auditor for ancient philosophy. Your job is \
NOT to confirm citations — it is to find reasons to REJECT them. The \
synthesizer is downstream; you must not trust its account of the passage.

Claim being audited:
{claim}

Verbatim evidence fetched independently from the corpus or a page-grounded \
scholarly position record:
{passage_text}

Decide one of four statuses:

- VERIFIED: the evidence explicitly supports the claim. A specific clause \
asserts what the claim asserts.
- WEAK: the evidence is on the same topic and consistent with the claim, but \
does not explicitly assert it. The synthesizer extrapolated.
- REJECTED: the evidence does not support the claim, contradicts it, or is \
about a different author/topic than the claim attributes.
- MISSING: the passage is empty, unintelligible, or otherwise unusable.

Bias: when in doubt between VERIFIED and WEAK, choose WEAK. When in doubt \
between WEAK and REJECTED, choose REJECTED. False approvals defeat the \
verifier; false rejections merely send the draft back for a better citation.

For REJECTED or WEAK, you MUST supply a verbatim quote from the evidence above \
showing the mismatch, in the ``evidence_quote`` field (NOT inside \
``reasoning``). No quote, no rejection.

Output format — CRITICAL. Respond with ONLY a single strict JSON object. No \
markdown fence, no prose before or after. Inside the ``reasoning`` string, do \
NOT use double-quote characters: write any quoted phrase with single quotes \
('like this'). Put the verbatim evidence quote in ``evidence_quote`` only.

{{"status": "VERIFIED" | "WEAK" | "REJECTED" | "MISSING",
  "reasoning": "<one sentence, no double-quote characters inside>",
  "evidence_quote": "<verbatim passage quote for WEAK/REJECTED, else empty>",
  "suggested_action": "<optional remediation, or empty string>"}}"""

# Same adversarial contract, different evidence layer: the text under audit is
# the knowledge graph's own curated statement of a scholar's argument /
# position (or an entity record), not a primary passage. The model must judge
# whether that statement supports the claim *as attributed* — a verbatim
# ancient quote is not expected here, and its absence is not a reason to
# reject.
NODE_VERIFY_PROMPT = """\
You are an ADVERSARIAL citation auditor for ancient philosophy. Your job is \
NOT to confirm citations — it is to find reasons to REJECT them. The \
synthesizer is downstream; you must not trust its account of the evidence.

Claim being audited:
{claim}

The evidence below is NOT a primary passage. It is a curated knowledge-graph \
record (node type: {node_type}) fetched independently from the graph: the \
graph's own statement of a scholar's argument or position, or of an entity, \
as entered by the curators — a secondary layer. Judge whether this statement \
supports the claim AS ATTRIBUTED (right scholar, right position, right \
scope). Do not look for a verbatim ancient quotation; its absence is not a \
defect of this evidence.

Knowledge-graph record:
{node_text}

Decide one of four statuses:

- VERIFIED: the record explicitly states what the claim attributes. A \
specific sentence of the record asserts what the claim asserts, about the \
same scholar or entity.
- WEAK: the record is on the same topic and consistent with the claim, but \
does not explicitly state it. The synthesizer extrapolated.
- REJECTED: the record does not support the claim, contradicts it, or is \
about a different scholar/author/topic than the claim attributes.
- MISSING: the record is empty, unintelligible, or otherwise unusable.

Bias: when in doubt between VERIFIED and WEAK, choose WEAK. When in doubt \
between WEAK and REJECTED, choose REJECTED. False approvals defeat the \
verifier; false rejections merely send the draft back for a better citation.

For REJECTED or WEAK, you MUST supply a verbatim quote from the record above \
showing the mismatch, in the ``evidence_quote`` field (NOT inside \
``reasoning``). No quote, no rejection.

Output format — CRITICAL. Respond with ONLY a single strict JSON object. No \
markdown fence, no prose before or after. Inside the ``reasoning`` string, do \
NOT use double-quote characters: write any quoted phrase with single quotes \
('like this'). Put the verbatim evidence quote in ``evidence_quote`` only.

{{"status": "VERIFIED" | "WEAK" | "REJECTED" | "MISSING",
  "reasoning": "<one sentence, no double-quote characters inside>",
  "evidence_quote": "<verbatim record quote for WEAK/REJECTED, else empty>",
  "suggested_action": "<optional remediation, or empty string>"}}"""

# How many verifier calls may run in parallel against the LLM.
DEFAULT_CONCURRENCY = 10
# How many times we retry a verifier LLM call before giving up and marking WEAK.
DEFAULT_RETRIES = 3
# Max passage chars sent to the LLM (long passages get truncated, but the
# *verbatim* prefix is preserved so the LLM can still quote it).
PASSAGE_TRUNCATE_CHARS = 4000

# Strict server-side JSON schema for the verdict. On Fireworks/Kimi this is
# enforced as ``response_format={"type": "json_schema", ...}`` so the model is
# constrained to a valid verdict object instead of free-running a meta-monologue
# (F1 root cause: kimi-k2p7-code rambling instead of emitting JSON). On providers
# that only support ``json_object`` the LLMService degrades gracefully; the
# tolerant parser is the second line of defence.
VERDICT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["VERIFIED", "WEAK", "REJECTED", "MISSING"],
        },
        "reasoning": {"type": "string"},
        "evidence_quote": {"type": "string"},
        "suggested_action": {"type": "string"},
    },
    "required": ["status", "reasoning"],
}

# Env knob: an explicit model for the verifier call (e.g. ``gpt-5.6-sol`` when a
# heavier head is wanted than the utility tier). Unset → the LLMService utility
# tier on the default provider chain. Read at call time so deployments can flip
# it without a code change.
_VERIFIER_MODEL_ENV = "ELEUTHERIA_VERIFIER_MODEL"

# A claim payload that is just a bare node label ("Susanne Bobzien",
# "Robert F. Dobbin, 121") is NOT auditable: there is no assertion to test
# against the passage, only a name. Feeding it to the adversarial auditor is what
# produced the "Wait, the claim is just 'Susanne Bobzien'?" monologue (F1c). We
# detect it deterministically and FAIL CLOSED instead of calling the LLM.
_BARE_LABEL_MAX_WORDS = 6
_CLAIM_VERB_RE = re.compile(
    r"\b(?:is|are|was|were|be|been|being|holds?|held|argues?|argued|claims?|"
    r"claimed|asserts?|asserted|maintains?|maintained|denies?|denied|says?|"
    r"said|states?|stated|contends?|defends?|rejects?|distinguishes?|"
    r"believes?|thinks?|shows?|implies|entails?|means?|has|have|had|"
    r"requires?|presupposes?|originat\w+|reads?|interprets?)\b",
    re.IGNORECASE,
)


# A bare label looks like a proper name (Title-Case tokens, optionally with
# initials) possibly trailed by a bare page/line number — exactly the
# ``citation.label`` fallback the synthesis path leaks ("Susanne Bobzien",
# "Robert F. Dobbin, 121"). It is NOT a generic short string ("Claim.", "c0").
_PROPER_NAME_RE = re.compile(r"[A-Z][a-zA-Z.''-]+")
_NAME_PLUS_NUMBER_RE = re.compile(r"^[A-Z].*?,?\s*\d+\s*$")

# Corpus/KG resolution policy.  A slug is not evidence; it must resolve to one
# exact corpus UUID through a declared twin or an exact passage_citations link.
_PASSAGE_NODE_TYPES = frozenset({"passage", "quote"})
_POSITION_NODE_TYPES = frozenset({"position", "argument"})
_PUBLICATION_NODE_TYPES = frozenset({"publication", "scholarly_work"})
_PASSAGE_ID_PREFIXES = ("passage_", "quote_")
_POSITION_ID_PREFIXES = (
    "position_",
    "scholar_position_",
    "scholarly_argument_",
    "argument_",
)
_CORPUS_ID_FIELDS = ("db_passage_id", "corpus_passage_id", "passage_id")
_EXACT_CITATION_TYPES = frozenset(
    {
        "snapshot_passage_node",
        "direct_quote",
        "primary_source",
        "evidenced_by",
        "source_for",
        "grounded_in",
        "testimonium",
    }
)
_ANCIENT_ORIGINAL_LANGUAGES = frozenset(
    {"grc", "lat", "hbo", "ara", "syr", "cop", "arm", "gez"}
)
_TRUSTED_TRANSLATION_TYPES = frozenset(
    {
        "ancient_human_literal",
        "human",
        "published_human",
        "scholarly",
        "published_public_domain",
        "published_scholarly_translation",
    }
)
_POSITION_PAGE_FIELDS = (
    "quote_page",
    "page_grounding",
    "page_range",
    "pages",
    "page",
    "page_or_loc",
    "claim_pages",
    "locus",
    "page_reference",
)
_POSITION_PUBLICATION_FIELDS = (
    "scholarly_work_id",
    "e2_publication_id",
    "publication_id",
    "publication",
)

# Node-evidence policy. A KG node with no corpus passage behind it is auditable
# only when it carries a substantive curated statement. The threshold is
# measured on the *substantive* fields (description plus the textual metadata
# fields below, whitespace-collapsed) — never on the label, which is identity,
# not evidence. 80 characters is roughly one full sentence: a person record
# with a one-line bio ("German philologist, 1870-1945") or a work title stays
# below it and therefore stays MISSING; the ~200-900 character argument
# statements the curators write for scholarly_argument_* nodes clear it.
NODE_TEXT_MIN_CHARS = 80
# Metadata fields that carry the node's own statement (counted toward the
# threshold), in prompt order. ``quote_verbatim`` is the curators' transcribed
# quotation from the publication — still a KG record, not a reviewed page.
_NODE_STATEMENT_FIELDS: tuple[tuple[str, str], ...] = (
    ("argument", "Argument"),
    ("claim", "Claim"),
    ("summary", "Summary"),
    ("position_statement", "Position"),
    ("stance", "Stance"),
    ("quote_verbatim", "Curated quotation"),
)
# Bibliographic anchors shown for attribution only (NOT counted).
_NODE_REFERENCE_FIELDS: tuple[tuple[str, str], ...] = (
    ("quote_source", "Source"),
    ("verified_reference", "Reference"),
    ("quote_page", "Page"),
    ("page_range", "Pages"),
)


def _is_bare_label_claim(claim: str) -> bool:
    """True when ``claim`` is a bare label/name, not an auditable assertion.

    Deterministic, zero-fabrication. A real claim predicates something (it
    carries a verb). The degenerate input the synthesis path leaks is the bare
    ``citation.label``: a proper name, or a name + page number, with no verb —
    "Susanne Bobzien", "Robert F. Dobbin, 121". We flag ONLY that shape so a
    short test stub or a verbless noun-phrase claim is left to the auditor.
    """
    stripped = (claim or "").strip()
    if not stripped:
        return True
    if _CLAIM_VERB_RE.search(stripped):
        return False
    words = re.findall(r"\w+", stripped)
    if not words or len(words) > _BARE_LABEL_MAX_WORDS:
        return False
    # name + trailing page/line number ("Robert F. Dobbin, 121")
    if _NAME_PLUS_NUMBER_RE.match(stripped):
        return True
    # ≥2 Title-Case tokens and (nearly) every word capitalised → a proper name
    proper = _PROPER_NAME_RE.findall(stripped)
    alpha_words = [w for w in words if w[:1].isalpha()]
    return len(proper) >= 2 and len(proper) >= len(alpha_words)


PassageFetcher = Callable[[str], Awaitable[dict[str, Any] | None]]
"""Async callable: ``citation_id -> {text, label, urn, ...} | None``.

A ``None`` return (or empty ``text``) means MISSING. Implementations must
re-fetch each call — caching defeats the v2 contract.
"""


def _node_type(node: dict[str, Any] | None) -> str:
    return str((node or {}).get("type") or "").strip().lower()


def _is_passage_identifier(citation_id: str, node: dict[str, Any] | None) -> bool:
    return _node_type(node) in _PASSAGE_NODE_TYPES or citation_id.startswith(
        _PASSAGE_ID_PREFIXES
    )


def _is_position_identifier(citation_id: str, node: dict[str, Any] | None) -> bool:
    return _node_type(node) in _POSITION_NODE_TYPES or citation_id.startswith(
        _POSITION_ID_PREFIXES
    )


def _collapse_ws(value: object) -> str:
    return " ".join(str(value or "").split())


def node_statement(node: dict[str, Any]) -> tuple[str, int]:
    """Render a KG node's curated statement for audit.

    Returns ``(text, substantive_chars)``. ``text`` is the labelled record
    (label, type, statement fields, bibliographic anchors) handed to the
    auditor; ``substantive_chars`` counts only the description and the
    :data:`_NODE_STATEMENT_FIELDS` — the figure compared against
    :data:`NODE_TEXT_MIN_CHARS`. Label and reference lines are identity, not
    evidence, and never count.
    """
    metadata = normalize_mapping(node.get("metadata"))
    lines: list[str] = []
    substantive = 0

    label = _collapse_ws(node.get("label"))
    if label:
        lines.append(f"Label: {label}")
    node_type = _node_type(node)
    if node_type:
        lines.append(f"Type: {node_type}")

    description = _collapse_ws(node.get("description"))
    if description:
        lines.append(f"Statement: {description}")
        substantive += len(description)
    for field, heading in _NODE_STATEMENT_FIELDS:
        value = _collapse_ws(metadata.get(field))
        if value and value != description:
            lines.append(f"{heading}: {value}")
            substantive += len(value)
    for field, heading in _NODE_REFERENCE_FIELDS:
        value = _collapse_ws(metadata.get(field))
        if value:
            lines.append(f"{heading}: {value}")
    return "\n".join(lines), substantive


def _declared_corpus_uuid(node: dict[str, Any] | None) -> uuid.UUID | None:
    metadata = normalize_mapping((node or {}).get("metadata"))
    declared: set[uuid.UUID] = set()
    for field in _CORPUS_ID_FIELDS:
        candidate = _try_parse_uuid(metadata.get(field))
        if candidate is not None:
            declared.add(candidate)
    # Conflicting pointers are data debt, not a basis for choosing one text.
    return next(iter(declared)) if len(declared) == 1 else None


def _first_text(metadata: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = metadata.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _publication_id(metadata: dict[str, Any]) -> str:
    for field in _POSITION_PUBLICATION_FIELDS:
        value = metadata.get(field)
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if candidate.startswith(("pub_", "publication_", "scholarly_work_")):
            return candidate
    return ""


def _position_page(metadata: dict[str, Any]) -> str:
    return _first_text(metadata, _POSITION_PAGE_FIELDS)


def _translation_is_authoritative(
    node: dict[str, Any] | None,
    *,
    passage_role: str,
) -> bool:
    metadata = normalize_mapping((node or {}).get("metadata"))
    translation_type = str(metadata.get("translation_type") or "").strip().lower()
    declared_role = str(metadata.get("passage_role") or "").strip().lower()

    if translation_type == "machine" or declared_role == "editorial_synthesis":
        return False
    if passage_role == "translation":
        return translation_type in _TRUSTED_TRANSLATION_TYPES
    # An original corpus row linked from a translation node is a parity error.
    return not translation_type and declared_role not in {"translation", "paraphrase"}


def build_db_passage_fetcher(
    db: Any,
    *,
    schema: str | None = None,
    node_lookup: dict[str, dict[str, Any]] | None = None,
    secondary_page_fetcher: SecondaryPageFetcher | None = None,
) -> PassageFetcher:
    """Production :data:`PassageFetcher` with independent source re-fetch.

    Passage slugs are handles, never evidence. They must resolve to exactly one
    corpus UUID through snapshot metadata or an exact ``passage_citations`` row,
    after which only ``passages.text_content`` is audited. A KG passage
    description is deliberately never a fallback.

    Modern positions are re-fetched by *position id*, then resolved to a real
    publication id plus an independently reviewed page in
    ``secondary_evidence_pages`` when one exists. Holder biographies never
    substitute for that page evidence.

    A node that resolves to no corpus passage and no reviewed page — a
    scholarly argument, a position, a scholar — is returned as ``kind="node"``
    evidence carrying the node's own curated statement (see
    :func:`node_statement`), provided it is citable and clears
    :data:`NODE_TEXT_MIN_CHARS`. The verifier audits it with the node-framed
    prompt and records ``evidence_kind="node"``; it is never used for a
    passage slug. Any ambiguous or missing passage mapping, blocked
    citability marker, non-primary role, unauthorized translation, or
    too-thin node record returns ``None`` / empty text and therefore becomes
    a fail-closed ``MISSING`` verdict.
    """
    resolved_schema = schema or os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
    resolved_secondary_page_fetcher = (
        secondary_page_fetcher
        if secondary_page_fetcher is not None
        else build_db_secondary_page_fetcher(db, schema=resolved_schema)
    )

    async def fresh_node(node_id: str) -> dict[str, Any] | None:
        try:
            rows = await db.fetch(
                f"""
                SELECT node_id, label, type, description, metadata
                FROM {resolved_schema}.kg_nodes
                WHERE node_id = $1
                """,
                node_id,
            )
        except Exception:
            logger.debug(
                "Fresh KG metadata fetch failed for %s", node_id, exc_info=True
            )
            return None
        if not rows:
            return None
        node = dict(rows[0])
        node["metadata"] = normalize_mapping(node.get("metadata"))
        return node

    async def mapped_corpus_uuid(kg_node_id: str) -> uuid.UUID | None:
        try:
            rows = await db.fetch(
                f"""
                SELECT passage_id::text AS passage_id, citation_type, confidence
                FROM {resolved_schema}.passage_citations
                WHERE kg_node_id = $1
                ORDER BY confidence DESC NULLS LAST, passage_id
                """,
                kg_node_id,
            )
        except Exception:
            logger.debug(
                "Fresh passage mapping fetch failed for %s",
                kg_node_id,
                exc_info=True,
            )
            return None
        candidates = {
            parsed
            for row in rows
            if str(row.get("citation_type") or "") in _EXACT_CITATION_TYPES
            and (parsed := _try_parse_uuid(row.get("passage_id"))) is not None
        }
        return next(iter(candidates)) if len(candidates) == 1 else None

    async def corpus_passage(
        passage_uuid: uuid.UUID,
        *,
        source_node: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        try:
            rows = await db.fetch(
                f"""
                SELECT
                    p.passage_id::text AS passage_id,
                    p.text_content,
                    p.canonical_ref,
                    p.cts_urn,
                    p.passage_role,
                    w.title,
                    w.author,
                    w.language
                FROM {resolved_schema}.passages p
                LEFT JOIN {resolved_schema}.ancient_works w
                    ON p.work_id = w.work_id
                WHERE p.passage_id = $1::uuid
                """,
                str(passage_uuid),
            )
        except Exception:
            logger.debug(
                "Fresh corpus passage fetch failed for %s",
                passage_uuid,
                exc_info=True,
            )
            return None
        if not rows:
            return None

        row = dict(rows[0])
        role = str(row.get("passage_role") or "").strip().lower()
        language = str(row.get("language") or "").strip().lower()
        text = str(row.get("text_content") or "").strip()
        if not text or role not in {"original", "translation"}:
            return None
        if (
            source_node is not None
            and evidence_policy(source_node).tier is not CitabilityTier.CITABLE
        ):
            return None
        if not _translation_is_authoritative(source_node, passage_role=role):
            return None
        if role == "original" and language not in _ANCIENT_ORIGINAL_LANGUAGES:
            return None

        return {
            "text": text,
            "label": row.get("canonical_ref") or str(passage_uuid),
            "passage_id": str(passage_uuid),
            "cts_urn": row.get("cts_urn"),
            "passage_role": role,
            "work_title": row.get("title"),
            "author": row.get("author"),
            "language": language,
            "source": "passages",
        }

    async def position_evidence(
        position_id: str, position: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        # A snapshot may identify the node kind, but page evidence itself must
        # be freshly read from the DB position/publication records.
        if position is None or not _is_position_identifier(position_id, position):
            return None
        if evidence_policy(position).tier is not CitabilityTier.CITABLE:
            return None

        metadata = normalize_mapping(position.get("metadata"))
        publication_id = _publication_id(metadata)
        page_ref = _position_page(metadata)
        if not publication_id or not page_ref:
            return None

        publication = await fresh_node(publication_id)
        if (
            publication is None
            or _node_type(publication) not in _PUBLICATION_NODE_TYPES
            or evidence_policy(publication).tier is not CitabilityTier.CITABLE
        ):
            return None

        page_evidence = await resolved_secondary_page_fetcher(publication_id, page_ref)
        if (
            page_evidence is None
            or page_evidence.get("publication_id") != publication_id
            or not str(page_evidence.get("text") or "").strip()
        ):
            return None

        return {
            **page_evidence,
            "label": " — ".join(
                part
                for part in (
                    str(position.get("label") or position_id),
                    str(publication.get("label") or publication_id),
                    page_ref,
                )
                if part
            ),
            "position_id": position_id,
            "publication_id": publication_id,
            "page_ref": page_ref,
            "source": "secondary_evidence_pages",
        }

    def node_evidence(
        citation_id: str, node: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        # The node's own curated statement, read fresh from kg_nodes, audited
        # as an explicitly secondary layer (``kind="node"``). Blocked and
        # discovery-only nodes stay MISSING. A node below the text threshold
        # is returned with an empty ``text`` so the verifier can say *why* it
        # is MISSING instead of "could not be re-fetched".
        if node is None:
            return None
        if evidence_policy(node).tier is not CitabilityTier.CITABLE:
            return None
        text, substantive = node_statement(node)
        return {
            "kind": "node",
            "text": text if substantive >= NODE_TEXT_MIN_CHARS else "",
            "label": str(node.get("label") or citation_id),
            "node_id": str(node.get("node_id") or node.get("id") or citation_id),
            "node_type": _node_type(node),
            "text_chars": substantive,
            "source": "kg_nodes",
        }

    async def fetch(citation_id: str) -> dict[str, Any] | None:
        snapshot_node = (node_lookup or {}).get(citation_id)
        direct_uuid = _try_parse_uuid(citation_id)
        if direct_uuid is not None:
            return await corpus_passage(direct_uuid, source_node=snapshot_node)

        fresh: dict[str, Any] | None = None
        node = snapshot_node
        if node is None:
            fresh = await fresh_node(citation_id)
            node = fresh

        if _is_passage_identifier(citation_id, node):
            # A passage slug resolves to corpus text or to nothing: its KG
            # description is deliberately never audited in its place.
            if node is None or evidence_policy(node).tier is not CitabilityTier.CITABLE:
                return None
            passage_uuid = _declared_corpus_uuid(node)
            if passage_uuid is None:
                passage_uuid = await mapped_corpus_uuid(citation_id)
            if passage_uuid is None:
                return None
            return await corpus_passage(passage_uuid, source_node=node)

        # Node evidence is always read fresh from the DB — a snapshot node is a
        # handle, never the audited text.
        if fresh is None:
            fresh = await fresh_node(citation_id)

        if _is_position_identifier(citation_id, node):
            # Page-grounded evidence (a reviewed page of the publication) wins
            # whenever the position resolves to one.
            evidence = await position_evidence(citation_id, fresh)
            if evidence is not None:
                return evidence

        # Scholarly arguments / positions without a reviewed page, scholars,
        # and other entity records: audit the node's curated statement as
        # secondary-layer evidence, or fail closed when it is too thin.
        return node_evidence(citation_id, fresh)

    return fetch


class CitationVerifierV2:
    """Adversarial citation verifier.

    Args:
        llm: LLM service used for the verification calls (low temperature).
        passage_fetcher: Async callable that re-fetches a passage by id. The
            verifier intentionally takes this as a dependency so it is not
            coupled to the DB layer — production wires it to a fresh DB
            query, tests inject a mock.
        emitter: Optional SSE emitter. When supplied, emits one
            ``citation_verified`` event per check (matches the frontend
            protocol in ``frontend/src/types/agent-events.ts``).
        concurrency: Max parallel verifier LLM calls.
        retries: Per-citation LLM retries before falling back to WEAK.
        warn_threshold: Fraction of failed citations that triggers a warning
            in the aggregate report.
        abort_threshold: Fraction of failed citations that triggers
            ``aborted=True`` (orchestrator should discard the draft).
    """

    def __init__(
        self,
        llm: LLMService,
        passage_fetcher: PassageFetcher,
        *,
        emitter: SSEEmitter | None = None,
        concurrency: int = DEFAULT_CONCURRENCY,
        retries: int = DEFAULT_RETRIES,
        warn_threshold: float = 0.20,
        abort_threshold: float = 0.50,
        verifier_model: str | None = None,
    ) -> None:
        self._llm = llm
        self._fetch = passage_fetcher
        self._emitter = emitter
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._retries = max(1, retries)
        self._warn_threshold = warn_threshold
        self._abort_threshold = abort_threshold
        # Explicit > env > default-chain. A reasoning model that returns
        # parseable verdicts (e.g. deepseek-v4-pro) can be pinned here without
        # touching the shared LLMService provider chain.
        self._verifier_model = verifier_model or os.getenv(_VERIFIER_MODEL_ENV) or None

    # ------------------------------------------------------------------ API

    async def verify_draft(self, draft: SynthesizedDraft) -> VerificationReport:
        """Verify every claim/citation pair in ``draft`` in parallel."""
        if not draft.claims:
            return VerificationReport.from_checks(
                [],
                warn_threshold=self._warn_threshold,
                abort_threshold=self._abort_threshold,
            )

        tasks = [
            asyncio.create_task(self._verify_with_semaphore(claim))
            for claim in draft.claims
        ]
        checks: list[CitationCheck] = list(await asyncio.gather(*tasks))

        report = VerificationReport.from_checks(
            checks,
            warn_threshold=self._warn_threshold,
            abort_threshold=self._abort_threshold,
        )
        logger.info(
            "CitationVerifierV2: %d total | %d verified | %d weak | %d rejected | %d missing",
            report.total,
            report.verified,
            report.weak,
            report.rejected,
            report.missing,
        )
        return report

    async def verify_one(self, claim: str, passage_id: str) -> CitationCheck:
        """Single-shot helper (also used by tests). Re-fetches the passage."""
        return await self._verify_one(
            DraftClaim(claim=claim, citation_id=passage_id, citation_kind="passage")
        )

    # -------------------------------------------------------------- internals

    async def _verify_with_semaphore(self, claim: DraftClaim) -> CitationCheck:
        async with self._semaphore:
            return await self._verify_one(claim)

    async def _verify_one(self, claim: DraftClaim) -> CitationCheck:
        # 0) Guard the auditor input itself (F1c). A bare node label
        # ("Susanne Bobzien", "Robert F. Dobbin, 121") is not an auditable
        # claim — there is no assertion to test. Fail CLOSED (WEAK, flagged as a
        # verifier issue, never a clean VERIFIED) instead of feeding the
        # adversarial model a name it can only ramble about.
        if _is_bare_label_claim(claim.claim):
            logger.warning(
                "Verifier received a bare-label claim for %s (%r) — not an "
                "auditable claim+passage pair; failing closed to WEAK.",
                claim.citation_id,
                (claim.claim or "")[:120],
            )
            check = CitationCheck(
                citation_id=claim.citation_id,
                status=CitationStatus.WEAK,
                reasoning=(
                    "Verifier could not audit: the claim payload was a bare "
                    "label/name, not a claim+passage pair. Citation left "
                    "UNVERIFIED pending a real claim sentence."
                ),
                claim=claim.claim,
                passage_excerpt="",
                suggested_action="supply the claim sentence for this citation",
                parse_error=True,
            )
            await self._emit(check)
            return check

        # 1) Re-fetch — no caching, no trust of upstream paraphrase.
        try:
            fetched = await self._fetch(claim.citation_id)
        except Exception:
            logger.warning(
                "Passage fetch raised for %s — marking MISSING",
                claim.citation_id,
                exc_info=True,
            )
            fetched = None

        evidence_kind = "node" if (fetched or {}).get("kind") == "node" else "passage"

        if not fetched or not (fetched.get("text") or "").strip():
            if evidence_kind == "node":
                # The node exists but is an identity record (a name, a title,
                # a one-line bio) — nothing substantive to audit the claim
                # against. Say so; "could not be re-fetched" would be false.
                reasoning = (
                    f"Knowledge-graph node {fetched.get('label')!r} "
                    f"({fetched.get('node_type') or 'unknown type'}) carries "
                    f"only {int(fetched.get('text_chars') or 0)} characters of "
                    f"curated text (minimum {NODE_TEXT_MIN_CHARS}); an identity "
                    "record is not auditable evidence."
                )
            else:
                reasoning = "Passage could not be re-fetched from the corpus."
            check = CitationCheck(
                citation_id=claim.citation_id,
                status=CitationStatus.MISSING,
                reasoning=reasoning,
                claim=claim.claim,
                passage_excerpt="",
                suggested_action="remove citation",
                evidence_kind=evidence_kind,
            )
            await self._emit(check)
            return check

        passage_text = str(fetched.get("text", "")).strip()
        truncated = passage_text[:PASSAGE_TRUNCATE_CHARS]

        # 2) Ask the LLM to find why the citation is bad (adversarial framing).
        verdict = await self._ask_llm(
            claim.claim,
            claim.citation_id,
            truncated,
            evidence_kind=evidence_kind,
            node_type=str(fetched.get("node_type") or ""),
        )

        status = verdict["status"]
        check = CitationCheck(
            citation_id=claim.citation_id,
            status=status,
            reasoning=verdict["reasoning"],
            claim=claim.claim,
            passage_excerpt=truncated,
            suggested_action=verdict.get("suggested_action") or None,
            parse_error=bool(verdict.get("parse_error", False)),
            evidence_kind=evidence_kind,
        )
        await self._emit(check)
        return check

    async def _ask_llm(
        self,
        claim: str,
        citation_id: str,
        passage_text: str,
        *,
        evidence_kind: str = "passage",
        node_type: str = "",
    ) -> dict[str, Any]:
        if evidence_kind == "node":
            delimited_node = delimit_retrieved_text(
                passage_text,
                data_id=f"node:{citation_id}",
                tag="kg-node",
            )
            prompt = NODE_VERIFY_PROMPT.format(
                claim=claim,
                node_type=node_type or "unknown",
                node_text=delimited_node,
            )
        else:
            delimited_passage = delimit_retrieved_text(
                passage_text,
                data_id=f"citation:{citation_id}",
                tag="passage",
            )
            prompt = VERIFY_PROMPT.format(
                claim=claim,
                passage_text=delimited_passage,
            )

        last_error: Exception | None = None
        last_raw: str | None = None
        for attempt in range(1, self._retries + 1):
            try:
                raw = await self._llm.generate(
                    prompt,
                    temperature=0.1,
                    # Reasoning models need headroom to emit reasoning AND the
                    # verdict object; 400 truncated the JSON on the rambling
                    # path. The schema keeps the visible output tight.
                    max_tokens=700,
                    response_mime_type="application/json",
                    response_json_schema=VERDICT_JSON_SCHEMA,
                    model_override=self._verifier_model,
                    # SYNTHESIS tier on purpose: this is the anti-hallucination
                    # gate. A cheap utility model that misreads a Greek passage
                    # passes a fabricated citation through, which is exactly the
                    # failure this project cannot afford — the extra cost per
                    # verdict is the point. ELEUTHERIA_VERIFIER_MODEL still pins
                    # a specific model when an operator wants one.
                    tier="synthesis",
                )
                last_raw = raw
                parsed = _parse_verdict(raw)
                if parsed is not None:
                    return parsed
                last_error = ValueError("verifier LLM returned unparseable JSON")
                # A parse failure is NOT a verdict — log the raw output so the
                # format drift is debuggable instead of vanishing into a WEAK.
                logger.warning(
                    "Verifier could not parse LLM output for %s (attempt %d/%d). "
                    "Raw output: %r",
                    citation_id,
                    attempt,
                    self._retries,
                    (raw or "")[:1000],
                )
            except Exception as exc:  # noqa: BLE001 — third-party LLM client
                last_error = exc
                logger.debug(
                    "Verifier LLM attempt %d/%d failed: %s",
                    attempt,
                    self._retries,
                    exc,
                )

        # Genuine failure after retries. Default to WEAK (adversarial bias:
        # never silently pass), but flag it as a verifier error, not a real
        # "consistent-but-not-asserted" WEAK verdict, so it can be distinguished
        # downstream and in benchmarks.
        logger.warning(
            "Verifier unable to assess citation %s after %d attempts (%s) — "
            "falling back to WEAK. Last raw output: %r",
            citation_id,
            self._retries,
            last_error,
            (last_raw or "")[:1000],
        )
        return {
            "status": CitationStatus.WEAK,
            "reasoning": (
                "Verifier unable to assess: LLM call failed or returned "
                "unparseable output after retries."
            ),
            "suggested_action": "manual review",
            "parse_error": True,
        }

    async def _emit(self, check: CitationCheck) -> None:
        if self._emitter is None:
            return
        try:
            await self._emitter.emit_citation_verified(
                passage_id=check.citation_id,
                status=check.status.value,
                verified=check.is_passing,
                reason=check.reasoning,
            )
        except AttributeError:
            # Older emitter (no emit_citation_verified). Don't crash the
            # pipeline over a telemetry-only call.
            logger.debug("SSE emitter lacks emit_citation_verified — skipping")
        except Exception:
            logger.warning(
                "SSE emit failed for citation %s — continuing",
                check.citation_id,
                exc_info=True,
            )


# --------------------------------------------------------------------- helpers


def _try_parse_uuid(value: object) -> uuid.UUID | None:
    """Parse ``value`` as a UUID, or ``None`` for node-shaped ids."""
    if isinstance(value, uuid.UUID):
        return value
    if not isinstance(value, str):
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):  # fmt: skip
        return None


_VALID_STATUSES = {s.value for s in CitationStatus}

# Field-name variants the model drifts to, mapped to our canonical fields.
_STATUS_KEYS = ("status", "verdict", "judgment", "judgement", "result", "label")
_REASONING_KEYS = ("reasoning", "rationale", "reason", "explanation", "justification")
_QUOTE_KEYS = ("evidence_quote", "quote", "verbatim_quote", "evidence", "passage_quote")
_ACTION_KEYS = ("suggested_action", "action", "remediation", "suggestion")

# Loose status-token map (handles the model answering with a bare word or a
# near-synonym instead of the exact enum value).
_STATUS_ALIASES = {
    "VERIFIED": "VERIFIED",
    "VERIFY": "VERIFIED",
    "SUPPORTED": "VERIFIED",
    "PASS": "VERIFIED",
    "WEAK": "WEAK",
    "PARTIAL": "WEAK",
    "CONSISTENT": "WEAK",
    "REJECTED": "REJECTED",
    "REJECT": "REJECTED",
    "UNSUPPORTED": "REJECTED",
    "CONTRADICTED": "REJECTED",
    "FAIL": "REJECTED",
    "MISSING": "MISSING",
    "EMPTY": "MISSING",
    "UNUSABLE": "MISSING",
}


def _iter_json_objects(text: str) -> list[str]:
    """Return every top-level balanced ``{...}`` block, in source order.

    Brace counting that respects JSON string literals, so a quote containing
    ``{`` / ``}`` does not corrupt the boundaries. A reasoning model emits a
    meta-monologue (often with stray braces) and only THEN the real verdict
    object; returning all candidates lets the caller prefer the LAST one that
    actually parses to a verdict (F1: reasoning-then-JSON).
    """
    blocks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        start = i
        depth = 0
        in_string = False
        escape = False
        closed = False
        while i < n:
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start : i + 1])
                    i += 1
                    closed = True
                    break
            i += 1
        if not closed:
            # Unbalanced tail (truncated final object) — keep it so the repair
            # pass below still gets a shot at it, then stop.
            blocks.append(text[start:])
            break
    return blocks


def _extract_first_json_object(text: str) -> str | None:
    """Return the first balanced ``{...}`` block (brace-counting, string-aware).

    A greedy ``\\{.*\\}`` regex grabs from the first ``{`` to the *last* ``}``,
    which swallows trailing prose and any second object. Brace counting that
    respects JSON string literals returns exactly the first object.
    """
    blocks = _iter_json_objects(text)
    return blocks[0] if blocks else None


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas before ``}`` / ``]`` (a very common LLM slip)."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _repair_inner_quotes(block: str) -> str:
    """Best-effort repair of unescaped double-quotes *inside* string values.

    The single biggest source of unparseable verdicts: the model embeds a
    verbatim ``"quote"`` inside the ``reasoning`` value, producing
    ``"reasoning": "... says "x" ..."``. We walk the JSON char-by-char and,
    once inside a string value, escape any ``"`` that is not the genuine
    closing quote (i.e. not followed by ``:``, ``,`` or a closing brace).
    """
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    n = len(block)
    while i < n:
        ch = block[i]
        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue
        if escape:
            out.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            i += 1
            continue
        if ch == '"':
            # Is this the real closing quote? Peek past whitespace.
            j = i + 1
            while j < n and block[j] in " \t\r\n":
                j += 1
            nxt = block[j] if j < n else ""
            if nxt in (":", ",", "}", "]", ""):
                out.append(ch)
                in_string = False
            else:
                # Stray inner quote — escape it.
                out.append('\\"')
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _loads_tolerant(block: str) -> Any | None:
    """Try increasingly aggressive repairs to parse ``block`` as JSON."""
    for candidate in (
        block,
        _strip_trailing_commas(block),
        _strip_trailing_commas(_repair_inner_quotes(block)),
    ):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):  # fmt: skip
            continue
    # Last resort: the repo's hardened extractor (strips raw control characters
    # inside string values, smart quotes, NaN — the shapes the repairs above do
    # not cover). Never raises out of here: a failure stays a ``None`` parse.
    try:
        return extract_json_object(block)
    except Exception:  # noqa: BLE001 — any extraction failure is just "unparseable"
        return None


def _first_present(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return the first value among ``keys`` (case-insensitive) present in ``obj``."""
    lowered = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        if key in lowered:
            return lowered[key]
    return None


def _coerce_status(value: Any) -> str | None:
    """Map a raw status value to a canonical enum value, or ``None``.

    EXACT matches only (enum value or alias). The former loose word-scan
    fallback ("pick the first known token in the sentence") failed OPEN: it read
    "NOT VERIFIED" / "cannot verify" / "not supported" as VERIFIED because it
    scanned for the positive token and ignored the negation. ``None`` routes to
    the WEAK/parse_error fallback — the adversarial bias: never silently pass.
    """
    token = str(value or "").strip().upper()
    if token in _VALID_STATUSES:
        return token
    if token in _STATUS_ALIASES:
        return _STATUS_ALIASES[token]
    return None


def _verdict_from_block(block: str) -> dict[str, Any] | None:
    """Parse ONE balanced ``{...}`` block into a verdict dict, or ``None``."""
    obj = _loads_tolerant(block)
    if not isinstance(obj, dict):
        return None

    status_canonical = _coerce_status(_first_present(obj, _STATUS_KEYS))
    if status_canonical is None:
        return None

    reasoning = str(_first_present(obj, _REASONING_KEYS) or "").strip()
    quote = str(_first_present(obj, _QUOTE_KEYS) or "").strip()
    # Fold the evidence quote back into reasoning so downstream consumers (which
    # expect the verbatim quote in `reasoning` for WEAK/REJECTED) keep working.
    if quote and quote not in reasoning:
        reasoning = f'{reasoning} "{quote}"'.strip() if reasoning else f'"{quote}"'

    action_raw = _first_present(obj, _ACTION_KEYS)
    suggested_action = (
        action_raw.strip() or None if isinstance(action_raw, str) else None
    )

    return {
        "status": CitationStatus(status_canonical),
        "reasoning": reasoning,
        "suggested_action": suggested_action,
    }


# A leading meta-monologue (the reasoning/code model's failure mode) is "prose"
# when there is a substantial run of words before the first JSON object.
_PROSE_PREFIX_MIN_CHARS = 80


def _parse_verdict(raw: str) -> dict[str, Any] | None:
    """Extract the JSON verdict from the LLM response. Returns ``None`` on failure.

    Resilient to: ```` ```json ```` fences, prose before/after the object, a
    trailing second object, trailing commas, status field-name variants
    (``verdict``/``result``/...), unescaped double-quotes embedded inside string
    values (the G2 benchmark killer), AND a reasoning-then-JSON response where a
    non-reasoning code model rambles a meta-monologue and only THEN emits the
    real verdict object (F1).

    Selection rule (honours both failure shapes):

    * if the response *opens* with the JSON (no substantial leading prose), take
      the FIRST parseable verdict — guards against ``{verdict}{noise}``;
    * if a meta-monologue precedes the first object, take the LAST parseable
      verdict — the rambling model's real answer is at the end.
    """
    if not raw:
        return None
    text = raw.strip()
    # Strip markdown fences anywhere (opening ```json / ``` and closing ```).
    text = re.sub(r"```(?:json|JSON)?", "", text)
    text = text.strip()

    blocks = _iter_json_objects(text)
    if not blocks:
        return None

    parsed = [(b, _verdict_from_block(b)) for b in blocks]
    valid = [(b, v) for b, v in parsed if v is not None]
    if not valid:
        return None

    first_block = valid[0][0]
    prefix = text[: text.find(first_block)]
    # A short prefix (fence remnants, "Here is the verdict:") keeps the FIRST
    # object; a long meta-monologue flips to the LAST parseable verdict.
    if len(prefix.strip()) >= _PROSE_PREFIX_MIN_CHARS:
        return valid[-1][1]
    return valid[0][1]
