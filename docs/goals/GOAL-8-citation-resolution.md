# GOAL 8 — Real academic citations (kill the node-ID leak)

## Problem
The "citation generator" emits raw KG node IDs instead of academic references. Observed
output for a real answer:
```
b_2dceaab7
b_44fcc123
scholarly_argument_long_2002_aristotelian_tie_to_what_is_up_to_us
scholarly_argument_dobbin_1991_preserve_of_freedom_bounded_by_self
concept_praebere_se_fato_seneca_d5e6f7g8
```
This is embarrassing for a scholarly tool. Each cited node must resolve to a proper,
copy-pasteable academic citation.

## Done = perfect
- Secondary literature → full academic citation: Author, Year. *Title*. Publisher/Journal
  (+ page if known) — e.g. "Long, A.A. (2002). *Epictetus: A Stoic and Socratic Guide to
  Life*. Oxford: Clarendon Press." Resolved from KG bibliographic metadata (and the
  scholarly_work_/publication_ shells), never the node ID.
- Primary sources → standard classical citation: Author, *Work* locus (CTS/edition) +
  original-language note, e.g. "Epictetus, *Discourses* I.1.23 (Schenkl, Teubner)."
- Inline citation badges in the answer are clickable footnotes that open the resolved
  reference (and, for primary, the in-context passage reader).
- A "References" / bibliography section lists the resolved citations, deduplicated,
  alphabetical by author — zero raw node IDs anywhere in the UI.
- Clicking a source opens exactly ONE panel (fix the current double-open bug).
- Verified live on a real answer: every citation is a real reference, no `b_…`/`*_argument_*`
  /`concept_*` IDs visible.
