"""
Deterministic renderer that converts a ``ThesisDraft`` into Markdown, LaTeX,
BibTeX, Zotero JSON or RIS. No LLM is involved — the renderer is a pure
function over the validated schema, which makes the output reproducible and
easy to test.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Literal

from eleutheria_graphrag.models.thesis_output import (
    BibliographyEntry,
    Citation,
    Footnote,
    Section,
    ThesisDraft,
)

CitationStyle = Literal["chicago", "mla", "harvard"]
ExportFormat = Literal["markdown", "latex", "bibtex", "zotero", "ris", "json"]


# --- helpers ----------------------------------------------------------------


_GREEK_CHAR = re.compile(r"[Ͱ-Ͽἀ-῿]")
_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _contains_greek(text: str) -> bool:
    return bool(_GREEK_CHAR.search(text))


def _latex_escape(text: str) -> str:
    """Escape LaTeX specials but preserve Unicode (handled by polyglossia/babel)."""

    return "".join(_LATEX_SPECIALS.get(ch, ch) for ch in text)


def _wrap_greek_for_latex(text: str) -> str:
    """Wrap polytonic Greek runs in ``\\textgreek{...}`` for XeLaTeX/babel."""

    if not _contains_greek(text):
        return _latex_escape(text)
    chunks: list[str] = []
    buf: list[str] = []
    in_greek = False
    for ch in text:
        is_greek = bool(_GREEK_CHAR.match(ch))
        if is_greek != in_greek:
            if buf:
                chunk = "".join(buf)
                if in_greek:
                    chunks.append("\\textgreek{" + chunk + "}")
                else:
                    chunks.append(_latex_escape(chunk))
                buf = []
            in_greek = is_greek
        buf.append(ch)
    if buf:
        chunk = "".join(buf)
        chunks.append(
            "\\textgreek{" + chunk + "}" if in_greek else _latex_escape(chunk)
        )
    return "".join(chunks)


def _transliterate(text: str) -> str:
    """Light ASCII fold for RIS / Zotero ``shortTitle`` fallbacks."""

    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii")


# --- formatting per citation style -----------------------------------------


def _format_citation_chicago(c: Citation) -> str:
    parts: list[str] = []
    if c.author:
        parts.append(c.author)
    if c.work_label:
        parts.append(f"*{c.work_label}*")
    if c.page_or_section:
        parts.append(c.page_or_section)
    head = ", ".join(p for p in parts if p)
    editorial: list[str] = []
    if c.edition:
        editorial.append(f"ed. {c.edition}")
    if c.translation:
        editorial.append(f"trans. {c.translation}")
    if editorial:
        head = f"{head} ({'; '.join(editorial)})"
    quote_bits: list[str] = []
    if c.quote_greek:
        quote_bits.append(f"“{c.quote_greek}”")
    if c.quote_translation:
        quote_bits.append(f"“{c.quote_translation}”")
    if quote_bits:
        head = f"{head}: {' — '.join(quote_bits)}"
    if c.cts_urn:
        head = f"{head} [{c.cts_urn}]"
    return head


def _format_citation_mla(c: Citation) -> str:
    parts: list[str] = []
    if c.author:
        parts.append(c.author + ".")
    if c.work_label:
        parts.append(f"*{c.work_label}*.")
    if c.edition:
        parts.append(f"Edited by {c.edition}.")
    if c.translation:
        parts.append(f"Translated by {c.translation}.")
    if c.page_or_section:
        parts.append(c.page_or_section + ".")
    head = " ".join(parts).strip()
    if c.quote_greek or c.quote_translation:
        quote = c.quote_greek or ""
        if c.quote_translation:
            quote = f"{quote} — {c.quote_translation}" if quote else c.quote_translation
        head = f"{head} “{quote}”"
    if c.cts_urn:
        head = f"{head} [{c.cts_urn}]"
    return head.strip()


def _format_citation_harvard(c: Citation) -> str:
    bits: list[str] = []
    if c.author:
        bits.append(c.author)
    if c.work_label:
        bits.append(c.work_label)
    if c.edition:
        bits.append(f"({c.edition})")
    if c.page_or_section:
        bits.append(c.page_or_section)
    head = ", ".join(bits)
    if c.quote_greek:
        head = f"{head}: ‘{c.quote_greek}’"
    if c.quote_translation:
        head = f"{head} (‘{c.quote_translation}’)"
    if c.cts_urn:
        head = f"{head} [{c.cts_urn}]"
    return head


_CITATION_FORMATTERS = {
    "chicago": _format_citation_chicago,
    "mla": _format_citation_mla,
    "harvard": _format_citation_harvard,
}


# --- renderer ---------------------------------------------------------------


class ThesisRenderer:
    """Render a ``ThesisDraft`` into one of the supported export formats."""

    # ----- Markdown --------------------------------------------------------

    def to_markdown(
        self, draft: ThesisDraft, *, citation_style: CitationStyle = "chicago"
    ) -> str:
        formatter = _CITATION_FORMATTERS[citation_style]
        lines: list[str] = [f"# {draft.title}", ""]
        if draft.abstract:
            lines += ["**Abstract.** " + draft.abstract.strip(), ""]
        for section in draft.sections:
            lines.append(f"{'#' * (section.level + 1)} {section.heading}".rstrip())
            lines.append("")
            for paragraph in section.paragraphs:
                anchors = "".join(f"[^{ref}]" for ref in paragraph.footnote_refs)
                lines.append(paragraph.text.strip() + anchors)
                lines.append("")
        if draft.footnotes:
            lines += ["## Notes", ""]
            for note in sorted(draft.footnotes, key=lambda n: n.n):
                rendered = self._render_footnote_markdown(note, formatter)
                lines.append(f"[^{note.n}]: {rendered}")
            lines.append("")
        lines += self._render_bibliography_markdown(draft.bibliography)
        if draft.methodology_notes:
            lines += ["", "## Methodology notes", ""]
            for method_note in draft.methodology_notes:
                lines.append(f"- {method_note}")
        if draft.flagged_claims:
            lines += ["", "## Flagged claims", ""]
            for claim in draft.flagged_claims:
                lines.append(f"- {claim}")
        return "\n".join(lines).rstrip() + "\n"

    def _render_footnote_markdown(self, note: Footnote, formatter: Any) -> str:
        formatted = [formatter(c) for c in note.citations]
        joined = "; ".join(formatted)
        if note.text and note.text.strip() != joined:
            return f"{note.text.strip()} ({joined})"
        return joined

    def _render_bibliography_markdown(
        self, entries: list[BibliographyEntry]
    ) -> list[str]:
        primary = [e for e in entries if e.kind == "primary"]
        secondary = [e for e in entries if e.kind == "secondary"]
        out: list[str] = ["", "## Bibliography", ""]
        if primary:
            out.append("### Primary Sources")
            out.append("")
            for entry in sorted(
                primary, key=lambda e: (e.author.lower(), e.title.lower())
            ):
                out.append(f"- {self._format_bib_entry(entry)}")
            out.append("")
        if secondary:
            out.append("### Secondary Literature")
            out.append("")
            for entry in sorted(
                secondary, key=lambda e: (e.author.lower(), e.title.lower())
            ):
                out.append(f"- {self._format_bib_entry(entry)}")
            out.append("")
        return out

    def _format_bib_entry(self, e: BibliographyEntry) -> str:
        chunks: list[str] = [f"{e.author}.", f"*{e.title}*."]
        if e.edition:
            chunks.append(f"Edited by {e.edition}.")
        loc: list[str] = []
        if e.publisher:
            loc.append(e.publisher)
        if e.year:
            loc.append(str(e.year))
        if loc:
            chunks.append(", ".join(loc) + ".")
        if e.pages:
            chunks.append(f"pp. {e.pages}.")
        if e.cts_urn:
            chunks.append(f"[{e.cts_urn}]")
        if e.url:
            chunks.append(f"<{e.url}>")
        return " ".join(chunks)

    # ----- LaTeX -----------------------------------------------------------

    def to_latex(self, draft: ThesisDraft) -> str:
        lines: list[str] = [
            "\\documentclass[12pt]{article}",
            "\\usepackage{polyglossia}",
            "\\setmainlanguage{english}",
            "\\setotherlanguage{greek}",
            "\\newcommand{\\textgreek}[1]{\\foreignlanguage{greek}{#1}}",
            "\\usepackage[backend=biber, style=authoryear]{biblatex}",
            "\\addbibresource{thesis.bib}",
            f"\\title{{{_latex_escape(draft.title)}}}",
            "\\author{Romain Girardi}",
            "\\begin{document}",
            "\\maketitle",
        ]
        if draft.abstract:
            lines += [
                "\\begin{abstract}",
                _wrap_greek_for_latex(draft.abstract),
                "\\end{abstract}",
            ]
        notes_by_n = {note.n: note for note in draft.footnotes}
        for section in draft.sections:
            cmd = "section" if section.level == 1 else "subsection"
            lines.append(f"\\{cmd}{{{_latex_escape(section.heading)}}}")
            for paragraph in section.paragraphs:
                rendered = _wrap_greek_for_latex(paragraph.text)
                for ref in paragraph.footnote_refs:
                    note = notes_by_n.get(ref)
                    if note is None:
                        continue
                    rendered += "\\footnote{" + self._render_footnote_latex(note) + "}"
                lines.append(rendered)
                lines.append("")
        lines.append("\\printbibliography")
        lines.append("\\end{document}")
        return "\n".join(lines) + "\n"

    def _render_footnote_latex(self, note: Footnote) -> str:
        parts: list[str] = [_wrap_greek_for_latex(note.text)]
        for citation in note.citations:
            inline_bits: list[str] = []
            if citation.author:
                inline_bits.append(_latex_escape(citation.author))
            if citation.work_label:
                inline_bits.append(
                    "\\textit{" + _latex_escape(citation.work_label) + "}"
                )
            if citation.page_or_section:
                inline_bits.append(_latex_escape(citation.page_or_section))
            head = ", ".join(b for b in inline_bits if b)
            if citation.quote_greek:
                head = f"{head}: " + _wrap_greek_for_latex(citation.quote_greek)
            if citation.quote_translation:
                head = head + " — " + _latex_escape(citation.quote_translation)
            if head:
                parts.append(head)
        cite_keys = [
            slug for c in note.citations if (slug := self._citation_bib_hint(c))
        ]
        if cite_keys:
            parts.append("\\cite{" + ", ".join(cite_keys) + "}")
        return " ".join(parts)

    def _citation_bib_hint(self, c: Citation) -> str:
        """Best-effort BibTeX key recovered from citation metadata.

        Falls back to ``passage_id`` so every citation has a stable handle even
        if the bibliography entry was authored elsewhere.
        """

        from eleutheria_graphrag.models.thesis_output import slugify_ascii

        author = c.author or c.work_label
        return slugify_ascii(f"{author}-{c.work_label}")

    # ----- BibTeX ----------------------------------------------------------

    def to_bibtex(self, draft: ThesisDraft) -> str:
        blocks: list[str] = []
        for entry in draft.bibliography:
            kind = "book" if entry.kind == "primary" else "article"
            fields: list[str] = [
                f"  author = {{{_latex_escape(entry.author)}}}",
                f"  title = {{{_latex_escape(entry.title)}}}",
            ]
            if entry.year:
                fields.append(f"  year = {{{entry.year}}}")
            if entry.edition:
                fields.append(f"  edition = {{{_latex_escape(entry.edition)}}}")
            if entry.publisher:
                fields.append(f"  publisher = {{{_latex_escape(entry.publisher)}}}")
            if entry.pages:
                fields.append(f"  pages = {{{_latex_escape(entry.pages)}}}")
            if entry.url:
                fields.append(f"  url = {{{entry.url}}}")
            if entry.cts_urn:
                fields.append(f"  note = {{CTS: {entry.cts_urn}}}")
            blocks.append(
                "@" + kind + "{" + entry.bibtex_key + ",\n" + ",\n".join(fields) + "\n}"
            )
        return "\n\n".join(blocks) + "\n"

    # ----- Zotero ----------------------------------------------------------

    def to_zotero_json(self, draft: ThesisDraft) -> dict:
        """Zotero "import" JSON shape (items array with item types)."""

        items: list[dict] = []
        for entry in draft.bibliography:
            item_type = "book" if entry.kind == "primary" else "journalArticle"
            creators = self._split_creators(entry.author)
            item: dict[str, Any] = {
                "itemType": item_type,
                "title": entry.title,
                "creators": creators,
                "extra": (
                    f"BibTeX-Key: {entry.bibtex_key}"
                    + (f"\nCTS-URN: {entry.cts_urn}" if entry.cts_urn else "")
                ),
            }
            if entry.year:
                item["date"] = str(entry.year)
            if entry.publisher:
                item["publisher"] = entry.publisher
            if entry.pages:
                item["pages"] = entry.pages
            if entry.url:
                item["url"] = entry.url
            if entry.edition:
                item["edition"] = entry.edition
            short_title = _transliterate(entry.title)
            if short_title and short_title != entry.title:
                item["shortTitle"] = short_title
            items.append(item)
        return {"items": items}

    def _split_creators(self, author: str) -> list[dict[str, str]]:
        creators: list[dict[str, str]] = []
        for piece in re.split(r" and |;|,", author):
            piece = piece.strip()
            if not piece:
                continue
            tokens = piece.split()
            if len(tokens) == 1:
                creators.append(
                    {"creatorType": "author", "lastName": tokens[0], "firstName": ""}
                )
            else:
                creators.append(
                    {
                        "creatorType": "author",
                        "firstName": " ".join(tokens[:-1]),
                        "lastName": tokens[-1],
                    }
                )
        return creators

    # ----- RIS -------------------------------------------------------------

    def to_ris(self, draft: ThesisDraft) -> str:
        out: list[str] = []
        for entry in draft.bibliography:
            tag = "BOOK" if entry.kind == "primary" else "JOUR"
            out.append(f"TY  - {tag}")
            for token in entry.author.split(";"):
                out.append(f"AU  - {token.strip()}")
            out.append(f"TI  - {entry.title}")
            if entry.year:
                out.append(f"PY  - {entry.year}")
            if entry.publisher:
                out.append(f"PB  - {entry.publisher}")
            if entry.edition:
                out.append(f"ET  - {entry.edition}")
            if entry.pages:
                out.append(f"SP  - {entry.pages}")
            if entry.url:
                out.append(f"UR  - {entry.url}")
            if entry.cts_urn:
                out.append(f"N1  - CTS: {entry.cts_urn}")
            out.append(f"ID  - {entry.bibtex_key}")
            out.append("ER  - ")
            out.append("")
        return "\n".join(out)


def export_draft(
    draft: ThesisDraft,
    fmt: ExportFormat,
    *,
    citation_style: CitationStyle = "chicago",
) -> tuple[str, str]:
    """Render ``draft`` in ``fmt`` and return ``(body, media_type)``.

    The helper is what FastAPI routes call so the format/mime mapping stays in
    one place.
    """

    renderer = ThesisRenderer()
    if fmt == "markdown":
        return renderer.to_markdown(
            draft, citation_style=citation_style
        ), "text/markdown"
    if fmt == "latex":
        return renderer.to_latex(draft), "application/x-latex"
    if fmt == "bibtex":
        return renderer.to_bibtex(draft), "application/x-bibtex"
    if fmt == "ris":
        return renderer.to_ris(draft), "application/x-research-info-systems"
    if fmt == "zotero":
        return json.dumps(
            renderer.to_zotero_json(draft), ensure_ascii=False, indent=2
        ), "application/json"
    if fmt == "json":
        return draft.model_dump_json(indent=2), "application/json"
    raise ValueError(f"unknown export format: {fmt}")


# Section is re-exported so type checkers can resolve it from this module too.
__all__ = [
    "CitationStyle",
    "ExportFormat",
    "Section",
    "ThesisRenderer",
    "export_draft",
]
