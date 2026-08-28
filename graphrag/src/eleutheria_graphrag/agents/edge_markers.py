"""The dialectical ``[edge: …]`` marker grammar — ONE parser, ONE scrubber.

The Scholar-RAG synthesis prompt asks the model to cite a dialectical link it
invokes as ``[edge: <relation> P_<from>->P_<to>]``.  That marker is an
INTERNAL citation scheme: the provenance ledger, the content gate and the
referee read it off the draft prose.  It is never meant for the reader, and
the models do not write it uniformly — production answers carried ``edge_``
for ``edge:``, a line break inside the marker, spaces around the arrow,
``-->``/``→`` for ``->``, a hyphenated relation, and punctuation before the
closing bracket.  Every consumer therefore goes through this module:

* :data:`EDGE_MARKER_RE` locates a marker (any of those spellings);
* :func:`parse_edge_marker` reads ``(relation, from_id, to_id)`` off its body;
* :func:`strip_edge_markers` removes every marker from a text, tidying the
  whitespace it sat in, and reports what it removed.

Dependency-free on purpose: the publication gate, the synthesis module and the
referee all import it without a cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "EDGE_MARKER_RE",
    "EdgeMarkerScrub",
    "EdgeRef",
    "parse_edge_marker",
    "strip_edge_markers",
]

#: A closed marker.  The body may span lines and hold any character but a
#: bracket, so a marker can never swallow the ``[P_*]`` cite next to it.
EDGE_MARKER_RE = re.compile(r"\[\s*edge\s*[:_]?\s*(?P<body>[^\[\]]*)\]", re.IGNORECASE)
#: A marker the model never closed (a cut-off answer): ``[edge: …`` to the end
#: of its line.  Only the scrubber uses it — nothing citable can be read off it.
_UNCLOSED_EDGE_MARKER_RE = re.compile(
    r"\[\s*edge\s*[:_][^\[\]\n]*(?=\n|$)", re.IGNORECASE
)

_ARROW = r"(?:-+>|→|⟶|=>)"
_ID = r"[\w.-]+?"
_TAIL = r"[\s.,;:!?)»”\"']*$"
#: ``<relation> P_<from> -> P_<to>`` — the prompted form, tolerant of spacing,
#: line breaks, arrow spelling, a colon after the relation and trailing
#: punctuation inside the bracket.
_PROMPTED_BODY_RE = re.compile(
    rf"^\s*:?\s*(?P<relation>[A-Za-z][\w-]*)\s*:?\s+"
    rf"P_(?P<from>{_ID})\s*{_ARROW}\s*P_(?P<to>{_ID}){_TAIL}",
    re.DOTALL,
)
#: ``P_<from> <relation> P_<to>`` — the subject-verb-object form some models
#: fall back to.
_SVO_BODY_RE = re.compile(
    rf"^\s*:?\s*P_(?P<from>{_ID})\s+(?P<relation>[A-Za-z][\w-]*)\s+"
    rf"P_(?P<to>{_ID}){_TAIL}",
    re.DOTALL,
)
_HORIZONTAL_WS = " \t "
_CLOSING_PUNCTUATION = frozenset(".,;:!?)]»”\"'")


@dataclass(frozen=True, slots=True)
class EdgeRef:
    """A dialectical link read off one marker body."""

    relation: str
    from_id: str
    to_id: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.relation, self.from_id, self.to_id)


def normalise_relation(relation: str) -> str:
    """Map relation vocabulary — knowledge-graph edges are lower snake_case."""
    return relation.strip().lower().replace("-", "_")


def parse_edge_marker(body: str) -> EdgeRef | None:
    """Read ``(relation, from_id, to_id)`` off a marker body, or ``None``.

    ``body`` is what :data:`EDGE_MARKER_RE` captured — the text after the
    ``edge:`` prefix, or the whole bracket content minus ``edge`` (the ledger's
    generic marker regex leaves the leading colon in).
    """
    match = _PROMPTED_BODY_RE.match(body) or _SVO_BODY_RE.match(body)
    if match is None:
        return None
    return EdgeRef(
        relation=normalise_relation(match.group("relation")),
        from_id=match.group("from"),
        to_id=match.group("to"),
    )


@dataclass(frozen=True, slots=True)
class EdgeMarkerScrub:
    """The result of :func:`strip_edge_markers`."""

    text: str
    #: Every marker removed, verbatim (closed or not), in document order.
    markers: tuple[str, ...]
    #: The links that could be read off the removed markers.
    edges: tuple[EdgeRef, ...]

    @property
    def count(self) -> int:
        return len(self.markers)


def _cut_span(text: str, start: int, end: int) -> str:
    """Remove ``text[start:end]`` and the whitespace the marker sat in.

    ``argue [edge: …] over`` → ``argue over``; ``positions [edge: …].`` →
    ``positions.``; a marker opening a line loses its trailing spaces; a
    marker alone on its line takes the line with it.  Prose on either side
    is kept byte for byte.
    """
    pre = start
    while pre > 0 and text[pre - 1] in _HORIZONTAL_WS:
        pre -= 1
    post = end
    while post < len(text) and text[post] in _HORIZONTAL_WS:
        post += 1
    prev_char = text[pre - 1] if pre > 0 else ""
    next_char = text[post] if post < len(text) else ""
    at_line_start = prev_char in ("", "\n")
    at_line_end = next_char in ("", "\n")

    if at_line_start and at_line_end:
        # The marker was the whole line: drop the line break it leaves behind.
        if next_char == "\n":
            post += 1
        elif prev_char == "\n":
            pre -= 1
        return text[:pre] + text[post:]
    if at_line_end or next_char in _CLOSING_PUNCTUATION:
        # ``X [m].`` / ``X [m]\n``: the space before the marker goes with it.
        return text[:pre] + text[post:]
    if at_line_start:
        # ``[m] Y``: the spaces after the marker go with it.
        return text[:start] + text[post:]
    # ``X [m] Y``: keep one side's whitespace; ``X[m]Y`` gets one space.
    if pre < start:
        return text[:start] + text[post:]
    if post > end:
        return text[:start] + text[end:]
    return text[:start] + " " + text[end:]


def strip_edge_markers(text: str) -> EdgeMarkerScrub:
    """Remove every ``[edge: …]`` marker — closed or cut off — from ``text``.

    Idempotent; a text without ``[edge`` is returned unchanged.  The links
    read off the removed markers travel in :attr:`EdgeMarkerScrub.edges` so a
    consumer can keep them (metadata, a controversy map) after the prose is
    clean.
    """
    if not text or "[" not in text:
        return EdgeMarkerScrub(text, (), ())
    markers: list[str] = []
    edges: list[EdgeRef] = []
    while True:
        match = EDGE_MARKER_RE.search(text)
        if match is None:
            break
        markers.append(match.group(0))
        edge = parse_edge_marker(match.group("body"))
        if edge is not None:
            edges.append(edge)
        text = _cut_span(text, match.start(), match.end())
    while True:
        match = _UNCLOSED_EDGE_MARKER_RE.search(text)
        if match is None:
            break
        markers.append(match.group(0))
        text = _cut_span(text, match.start(), match.end())
    return EdgeMarkerScrub(text, tuple(markers), tuple(edges))
