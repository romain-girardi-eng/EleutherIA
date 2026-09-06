"""
Claim-clause extraction for the v2 citation verifier.

A scholarly sentence ordinarily carries several citations, one per
proposition: ``X argues A [P1], whereas Y argues B [P2].`` Handing the whole
sentence to the auditor of ``[P1]`` and asking it to refute produces the
false rejection "the record says nothing about Y/B" — the auditor is blamed
for a proposition another citation carries.

This module isolates, for one citation marker, the PROPOSITION the marker is
attached to: the text segment running from the previous marker group (or the
sentence start) up to this marker group. Adjacent markers (``[P1] [P2]``,
``[P3, N1]``) form one group and share the clause. Trailing text after the
last marker belongs to no marker: it is the writer's own inference and is
handed to the auditor as context only.

Marker grammar is the publication gate's (``[P1]`` / ``[N3]`` / ``[2]`` /
``[P1-P3]`` / ``[P3, N1]`` / ``[P_<id>: …]`` / ``[passage_<id>: …]``), and
sentence boundaries are the gate's too — a marker sitting after the period
(``… held X. [P1] Cleanthes …``) cites the sentence it follows.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable
from dataclasses import dataclass

from eleutheria_graphrag.agents.publication_gate import (
    _BRACKET_RE,
    _LINE_PREFIX_RE,
    _MARKER_BODY_RE,
    _PURE_REF_LIST_RE,
    _is_blockquote,
    _is_ref_marker,
    _ref_tokens,
    _split_line,
)

#: Whitespace and light punctuation allowed between two bracket blocks of the
#: same marker group (``[P1], [P2]`` / ``[P1] [P2]`` / ``[P1]; [P2]``).
_GROUP_GAP_RE = re.compile(r"^[\s,;]*$")
#: Leading connective punctuation stripped from a clause (``, whereas Y …``).
_LEADING_PUNCT_RE = re.compile(r"^[\s,;:—–\-]+")
#: Trailing punctuation stripped from a clause (the comma before a marker).
_TRAILING_PUNCT_RE = re.compile(r"[\s,;:—–\-]+$")
_WORD_RE = re.compile(r"\w+", re.UNICODE)
#: Whitespace left behind by a removed marker (``Bobzien [N3].`` → ``Bobzien .``).
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,;:!?)»”])")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
#: A clause with fewer words than this is a fragment (``Ibid.``, ``and``),
#: not a proposition: the whole sentence is audited instead.
_MIN_CLAUSE_WORDS = 2
#: Paragraph context window handed to the judge, in characters.
DEFAULT_CONTEXT_CHARS = 2500


@dataclass(frozen=True)
class MarkerGroup:
    """A run of adjacent citation markers inside one sentence.

    ``units`` are the citations of the group, one token tuple each: a pure
    reference list contributes one unit per reference (``[P3, N1]`` → two
    units), a body marker contributes one unit holding its body and bare id.
    """

    start: int
    end: int
    units: tuple[tuple[str, ...], ...]

    @property
    def tokens(self) -> tuple[str, ...]:
        return tuple(token for unit in self.units for token in unit)


@dataclass(frozen=True)
class ClaimClause:
    """The proposition one citation marker is attached to."""

    clause: str
    sentence: str
    marker_found: bool
    own_tokens: tuple[str, ...] = ()
    companion_tokens: tuple[str, ...] = ()


def marker_units(block: str) -> list[tuple[str, ...]]:
    """Citations carried by one bracket body, one token tuple each.

    ``P3, N1`` yields ``[("P3",), ("N1",)]``; ``P1-P3`` expands; ``P_frede:
    Frede 2011, p. 44`` and ``passage_<id>: Origen`` yield one unit holding
    the body and the bare id (matched against the citation id, as the
    publication gate does); any other body is one unit holding it verbatim
    so a literal ``[A1]`` / ``[<id>]`` still keys. Prose yields ``[]``.
    """
    stripped = block.strip()
    if not stripped:
        return []
    if _PURE_REF_LIST_RE.match(block):
        return [(token,) for token in _ref_tokens(block)]
    tokens = [stripped]
    marker = _MARKER_BODY_RE.match(stripped)
    if marker is not None:
        head = stripped.split(":", 1)[0].strip()
        if head not in tokens:
            tokens.append(head)
        ref_id = marker.group("body").split(":", 1)[0].strip().lstrip("_")
        if ref_id:
            tokens.append(ref_id)
    else:
        head = stripped.split(":", 1)[0].strip()
        if head and head != stripped:
            tokens.append(head)
    return [tuple(tokens)]


def marker_tokens(block: str) -> list[str]:
    """Every reference key carried by one bracket body (see :func:`marker_units`)."""
    return [token for unit in marker_units(block) for token in unit]


def _cites(tokens: Iterable[str], keys: Collection[str]) -> bool:
    return any(token in keys for token in tokens)


def find_marker_groups(
    sentence: str, *, known: Collection[str] = ()
) -> list[MarkerGroup]:
    """Bracket markers of ``sentence`` grouped by adjacency, in order.

    A bracket block is a marker when the publication gate recognises it or
    when one of its tokens is a ``known`` citation key (``[A1]``, a literal
    id); bracketed prose (``[sic]``) is not a marker and never cuts a clause.
    """
    groups: list[MarkerGroup] = []
    for match in _BRACKET_RE.finditer(sentence):
        body = match.group(1)
        units = tuple(marker_units(body))
        tokens = tuple(token for unit in units for token in unit)
        if not units or not (_is_ref_marker(body) or _cites(tokens, known)):
            continue
        if groups and _GROUP_GAP_RE.match(sentence[groups[-1].end : match.start()]):
            last = groups[-1]
            groups[-1] = MarkerGroup(last.start, match.end(), last.units + units)
        else:
            groups.append(MarkerGroup(match.start(), match.end(), units))
    return groups


def _clean_clause(text: str) -> str:
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", _MULTI_SPACE_RE.sub(" ", text))
    text = _LEADING_PUNCT_RE.sub("", text)
    return _TRAILING_PUNCT_RE.sub("", text).strip()


def extract_claim_clause(
    sentence: str,
    *,
    keys: Collection[str],
    known: Collection[str] = (),
) -> ClaimClause:
    """Isolate the proposition cited by the marker matching one of ``keys``.

    ``keys`` are the citation's own reference keys (its ``ref`` and its id);
    ``known`` are the keys of every citation of the answer, so that a
    non-standard companion marker (``[A1]``) still counts as a marker.
    When no marker matches — a ledger sentence with no marker, a label
    fallback — the whole sentence is the clause and ``marker_found`` is
    False. A clause that is a bare fragment falls back to the sentence too.
    Companion tokens are the keys of every other citation of the sentence —
    other groups, and the other citations of the audited citation's own group
    (``[P1] [P2]`` and ``[P3, N1]`` share a clause but are two sources) — in
    order of appearance, deduplicated.
    """
    sentence = sentence or ""
    groups = find_marker_groups(sentence, known=set(known) | set(keys))
    own: MarkerGroup | None = None
    previous_end = 0
    for group in groups:
        if _cites(group.tokens, keys):
            own = group
            break
        previous_end = group.end

    companions: list[str] = []
    for group in groups:
        for unit in group.units:
            if _cites(unit, keys):
                continue
            for token in unit:
                if token not in companions:
                    companions.append(token)

    if own is None:
        return ClaimClause(
            clause=_clean_clause(_BRACKET_RE.sub("", sentence)) or sentence.strip(),
            sentence=sentence.strip(),
            marker_found=False,
            companion_tokens=tuple(companions),
        )

    clause = _clean_clause(sentence[previous_end : own.start])
    # A citation can follow an introductory locus rather than the assertion:
    # "In De fato 41 [P1], Cicero distinguishes two kinds of causes."
    # With one marker group, the rest of that sentence belongs to this source.
    from eleutheria_graphrag.services.citation_verifier_v2 import _is_bare_label_claim

    if len(_WORD_RE.findall(clause)) < _MIN_CLAUSE_WORDS or (
        len(groups) == 1 and _is_bare_label_claim(clause)
    ):
        clause = _clean_clause(_BRACKET_RE.sub("", sentence)) or sentence.strip()
    return ClaimClause(
        clause=clause,
        sentence=sentence.strip(),
        marker_found=True,
        own_tokens=own.tokens,
        companion_tokens=tuple(companions),
    )


def _line_body(line: str) -> str:
    if _is_blockquote(line):
        return line.lstrip()[1:]
    prefix = _LINE_PREFIX_RE.match(line)
    return line[len(prefix.group(1)) :] if prefix else line


def enumerate_sentences(answer_text: str) -> list[tuple[int, str]]:
    """Every non-empty sentence of ``answer_text`` with its index.

    The traversal is the publication gate's (line by line, blockquote and
    list prefixes stripped, the gate's sentence splitter), so the index is
    the position of the sentence in the sequence the gate withholds from — a
    marker placed after the period is attributed to the sentence it follows,
    abbreviations (``p. 330``) do not cut, and a marker body is never split
    in two. Sentence texts are stripped.
    """
    sentences: list[tuple[int, str]] = []
    if not answer_text:
        return sentences
    for line in answer_text.split("\n"):
        for part in _split_line(_line_body(line))[0::2]:
            if part.strip():
                sentences.append((len(sentences), part.strip()))
    return sentences


def cited_sentences(
    answer_text: str, *, known: Collection[str]
) -> list[tuple[int, str, tuple[str, ...]]]:
    """Every sentence carrying a citation marker, with the keys it carries.

    Returns ``(index, sentence, tokens)`` triples in document order, where
    ``tokens`` are the reference keys of the sentence's marker groups in
    order of appearance (deduplicated). This is the enumeration of the
    (sentence, citation) pairs the verifier audits: one pair per key of
    ``known`` present in ``tokens``.
    """
    known = set(known)
    result: list[tuple[int, str, tuple[str, ...]]] = []
    for index, sentence in enumerate_sentences(answer_text):
        tokens: list[str] = []
        for group in find_marker_groups(sentence, known=known):
            for token in group.tokens:
                if token not in tokens:
                    tokens.append(token)
        if any(token in known for token in tokens):
            result.append((index, sentence, tuple(tokens)))
    return result


def sentence_for_citation(answer_text: str, *, keys: Collection[str]) -> str | None:
    """First sentence of ``answer_text`` carrying a marker for ``keys``.

    See :func:`enumerate_sentences` for the sentence boundaries.
    """
    for _index, sentence, tokens in cited_sentences(answer_text, known=keys):
        if _cites(tokens, keys):
            return sentence
    return None


def paragraph_context(
    answer_text: str,
    sentence: str,
    *,
    max_chars: int = DEFAULT_CONTEXT_CHARS,
) -> str:
    """The paragraph of ``answer_text`` holding ``sentence``, windowed.

    Returns ``""`` when the sentence is not found verbatim. The window is
    centred on the sentence so a long paragraph still shows what precedes and
    follows it.
    """
    needle = (sentence or "").strip()
    if not answer_text or not needle:
        return ""
    position = answer_text.find(needle)
    if position < 0:
        return ""
    start = answer_text.rfind("\n\n", 0, position)
    start = 0 if start < 0 else start + 2
    end = answer_text.find("\n\n", position + len(needle))
    end = len(answer_text) if end < 0 else end
    paragraph = answer_text[start:end].strip()
    if len(paragraph) <= max_chars:
        return paragraph
    local = paragraph.find(needle)
    if local < 0:
        return paragraph[:max_chars]
    spare = max(0, max_chars - len(needle))
    window_start = max(0, local - spare // 2)
    window_end = min(len(paragraph), window_start + max_chars)
    window_start = max(0, window_end - max_chars)
    return paragraph[window_start:window_end].strip()
