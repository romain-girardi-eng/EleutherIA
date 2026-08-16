"""Authored data for the 2026-08-16 second curation sweep.

Companion data module for `apply_2026_08_16_second_sweep.py`. It carries five
independent bodies of work, all derived item-by-item from evidence already
stored on the node itself (its `metadata.verification_notes`,
`metadata.verified_reference`) or re-verified against a named local source
(the TLG E corpus via `scripts/tlg_search.py`, the local .md extraction of
Destrée–Salles–Zingano 2014, `data/corpus/manifest.jsonl`):

1. `METADATA_OPS` — metadata-field defects that the archived `[Vérif.]` tags
   name but the 2026-08-14 cleanup left untouched, because that pass stayed
   inside the reader-facing fields.
2. `DESCRIPTION_REWRITES` / `DESCRIPTION_EN_REWRITES` / `LABEL_REWRITES` —
   completions of prose corrections the 2026-08-14 pass had to leave
   conservative, plus the merges for the curator brackets of §3.
3. `BRACKET_NODES` — nodes still carrying a curator bracket of a shape the
   first sweep did not target; the bracket text is moved verbatim to
   `metadata.verification_notes`.
4. `ALCINOUS_*` — the corpus-integrity escalation of the 2026-08-14 review.
5. `GREEK_ALLOWLIST_ADDITIONS` — the two TLG-attested runs that keep the
   zero-fabrication gate red.

Zero-fabrication rule: no ancient-language string is introduced that is not
already verbatim somewhere in the same node (description, label,
`verified_reference`) or quoted in the `#` comment from a named edition.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Metadata-field defects named by an archived [Vérif.] tag
# ---------------------------------------------------------------------------
# op vocabulary understood by the applier:
#   {"op": "set",           "key": K, "value": V}          — set metadata[K]
#   {"op": "set_if",        "key": K, "old": O, "value": V}— set only if == O
#   {"op": "delete",        "key": K}                      — drop metadata[K]
#   {"op": "list_remove",   "key": K, "value": V}          — drop one element
#   {"op": "list_set",      "key": K, "value": [...]}      — replace the list
#   {"op": "list_replace",  "key": K, "old": O, "value": V}— swap one element
#   {"op": "premise_clear_sources", "key": K, "ids": [...]}— clear
#        primary_sources / set attestation="unverified" on the listed premises
#   {"op": "str_replace",   "key": K, "old": O, "new": N}  — in a string field
METADATA_OPS: dict[str, tuple[dict, ...]] = {
    # --- fabricated / non-existent passage ids in `sources` -----------------
    # Verified: none of passage_alex_fat_6xx / 5xx exists in nodes.jsonl, while
    # the small-numbered ids the premises use (…_11, _12, _16, _19, _26) all do.
    "argument_human_dignity_alex": (
        # tag: "The description states the Bruns loci 'Fat. 628-636' were 'removed
        #   as fabricated', yet metadata.sources still lists the corresponding
        #   fabricated passage ids passage_alex_fat_633/634/635/636/628/629/63[0]"
        {"op": "list_set", "key": "sources", "value": ["passage_alex_fat_19"]},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.sources previously listed passage_alex_fat_628/629/630/"
                "633/634/635/636 — none of these nodes exists in the graph and the "
                "Bruns loci Fat. 628-636 they encode are impossible (De Fato ends at "
                "Bruns 212). Removed 2026-08-16; the surviving grounding is "
                "passage_alex_fat_19, the locus every premise already cites."
            ),
        },
    ),
    "argument_deliberation_complete_alex": (
        # tag: "The 'sources' array lists passage_alex_fat_554..558, but the premises
        #   are all grounded in passage_alex_fat_11/12; the 5xx passage ids appear to
        #   be a stale/spurious scheme"
        {
            "op": "list_set",
            "key": "sources",
            "value": ["passage_alex_fat_11", "passage_alex_fat_12"],
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.sources previously listed passage_alex_fat_554-558, none of "
                "which exists in the graph; replaced 2026-08-16 by the loci the "
                "premises themselves cite (De Fato 11-12 = Bruns 178-180)."
            ),
        },
    ),
    "argument_reactive_attitudes_alex": (
        # tag: "'Marmodoro & Bobzien 2015' … could not be confirmed as a real joint
        #   publication; likely a garbled citation."  The same node's `sources` array
        #   points at passage_alex_fat_611-616, none of which exists in the graph,
        #   while every premise cites passage_alex_fat_16 / _26, which do.
        {
            "op": "list_set",
            "key": "sources",
            "value": ["passage_alex_fat_16", "passage_alex_fat_26"],
        },
        {
            "op": "str_replace",
            "key": "validity_assessment.scholarly_consensus",
            "old": "Marmodoro & Bobzien 2015",
            "new": "Bobzien 1998",
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.sources previously listed passage_alex_fat_611-616, none of "
                "which exists in the graph; replaced 2026-08-16 by the loci the "
                "premises cite (De Fato 16 and 26). The unconfirmable joint "
                "publication 'Marmodoro & Bobzien 2015' was replaced by Bobzien 1998, "
                "the work actually discussed."
            ),
        },
    ),
    # --- Bruns page references outside De Fato (Bruns 164-212) --------------
    "argument_future_contingents_alex": (
        # tag: "'471-480' does not correspond to Bruns pagination, to De Fato chapter
        #   numbers, or to any standard reference scheme for this text; it appears
        #   spurious/unexplained. Either remove or replace with a genui[ne one]"
        {"op": "delete", "key": "key_passages"},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages ['471-480'] removed 2026-08-16: outside Bruns "
                "164-212 and matching no De Fato citation scheme. The surviving locus "
                "is bruns_pages '200-201' (De Fato 30), which the tag confirms."
            ),
        },
    ),
    "concept_arche_alex": (
        # tag: "The page-references 'Fat. 233', 'Fat. 235', 'Fat. 246', 'Fat. 247',
        #   'Fat. 253', 'Fat. 254' fall outside De Fato's Bruns pagination (Suppl.
        #   Arist. II.2, pp. 164–212). Only 'Fat. 180' is a valid De Fato [locus]"
        {"op": "list_set", "key": "key_passages", "value": ["Fat. 180"]},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages: Fat. 233/235/246/247/253/254 removed "
                "2026-08-16 as outside Bruns 164-212; only Fat. 180 survives, plus the "
                "verified locus De Fato 15 (Bruns 185) in verified_reference."
            ),
        },
    ),
    "concept_synkatathesis_logike_alex": (
        # tag: "key_passages ['Fat. 230-231', 'Fat. 257'] fall outside the De Fato,
        #   whose Bruns pagination ends at 212 … these references do not correspond to
        #   any De Fato locus".  verified_reference supplies the real one.
        {
            "op": "list_set",
            "key": "key_passages",
            "value": ["De anima libri mantissa, Bruns 184.11 (Περὶ τοῦ ἐφ' ἡμῖν)"],
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages ['Fat. 230-231', 'Fat. 257'] removed 2026-08-16 "
                "as impossible De Fato loci; replaced by the locus this node's own "
                "verified_reference confirms verbatim in TLG0732."
            ),
        },
    ),
    "concept_common_cause_alex": (
        # The node's own bruns_pages ('194-195') and verified_reference locate the
        # doctrine at Bruns 194-195; key_passages ['351-370'] is outside Bruns
        # 164-212 and belongs to the same spurious numbering family as the tags'
        # other rejected loci on Alexander nodes.
        {"op": "delete", "key": "key_passages"},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages ['351-370'] removed 2026-08-16: outside Bruns "
                "164-212. The node's own bruns_pages '194-195' and verified_reference "
                "(TLG-E collation, Bruns 192.23-195.28) carry the real locus."
            ),
        },
    ),
    "concept_non_necessitating_cause_alex": (
        # tag: "'459-462' does not correspond to any standard citation system for
        #   Alexander's De Fato … And bruns_pages '211-212' is the peroration (ch. 38),
        #   not [the locus]".  verified_reference: "esp. chs. 22-26 and 33-38".
        {"op": "delete", "key": "key_passages"},
        {"op": "delete", "key": "bruns_pages"},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages ['459-462'] and bruns_pages '211-212' removed "
                "2026-08-16: the first matches no Alexander citation scheme, the second "
                "is the peroration (ch. 38) rather than the locus of the doctrine. The "
                "adjudicated loci are in verified_reference (De Fato chs. 22-26, 33-38)."
            ),
        },
    ),
    "concept_self_happiness_alex": (
        # tags (3, incl. 2026-08-03 TLG0732): «δι᾽ αὑτῶν εὐδαιμονεῖν» is a modern
        # reconstruction, zero occurrences of εὐδαιμον- in the De fato.
        {"op": "delete", "key": "transliteration"},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.transliteration 'di hautōn eudaimonein' removed 2026-08-16: "
                "it transliterates a phrase the node's own greek_attestation field "
                "records as unattested in Alexander (εὐδαιμον-: 0 occurrences in the "
                "De fato). No replacement invented."
            ),
        },
    ),
    "argument_lazy_argument_alex": (
        # tag: "The page references 'Fat. 260', 'Fat. 265', 'Fat. 267', 'Fat. 268',
        #   'Fat. 284' fall outside the pagination of Alexander's De Fato, which
        #   occupies pp. 164-212 in Bruns"
        {"op": "delete", "key": "key_passages"},
        {
            "op": "set",
            "key": "greek_status",
            "value": (
                "«ἀργὸς λόγος» is the name of a different argument (the fatalist "
                "sophism at Cic. Fat. 28-30 / Orig. C. Cels. II.20), not of the "
                "consequences-for-motivation argument this node reconstructs"
            ),
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "metadata.key_passages ['Fat. 260/265/267/268/284'] removed "
                "2026-08-16: all outside Bruns 164-212. The tag gives no replacement, "
                "so none was invented; the confirmed locus is De Fato 11 "
                "(ancient_attestation_locus_classicus = passage_alex_fat_11)."
            ),
        },
    ),
    # --- period / label / vocabulary fields ---------------------------------
    "concept_external_principle_action": (
        # tag: "Period 'Classical Greek' fits the Aristotelian root (Physics II.1) but
        #   the cited text is Alexander of Aphrodisias' De Fato (Roman Imperial, c. 200
        #   CE)."  'Roman Imperial' is the graph's dominant vocabulary item.
        {"op": "node_set", "key": "period", "value": "Roman Imperial"},
    ),
    "work_exodus_c9d0e1f2": (
        # tag: "Period tagged 'Second Temple Judaism', but Exodus is a Pentateuchal/
        #   pre-exilic-to-Persian composition … Second Temple … is the reception
        #   context, not the wo[rk's period]".  'First Temple / Pre-exilic Judaism' is
        #   already in the graph's period vocabulary (work_jeremiah_k7l8m9n0).
        {
            "op": "node_set",
            "key": "period",
            "value": "First Temple / Pre-exilic Judaism",
        },
    ),
    "concept_intellectualism_medieval_i3j4k5l6": (
        # tag: "'intellectualismus' is a modern (post-medieval) coinage, not a term
        #   used by Aquinas or his contemporaries. Acceptable as a label but not an
        #   authentic medieval Latin term."  Mirrors the existing `greek_status`
        #   convention used on concept_gratia_cooperans / concept_self_happiness_alex.
        {
            "op": "set",
            "key": "latin_status",
            "value": (
                "modern_scholarly_coinage — 'intellectualismus' is post-medieval and "
                "is NOT a term used by Aquinas or his contemporaries"
            ),
        },
    ),
    "concept_libertas_spontaneitatis_5g9b0c68": (
        # tag: "The claim that Kant, in the Kritik der praktischen Vernunft at Ak.
        #   V:96, reports the term 'libertas spontaneitatis' could not be confirmed.
        #   KpV Ak V:96-97 is the 'turnspit' (Bratenwender) passage on c[ausality]"
        {
            "op": "set",
            "key": "latin_locus",
            "value": (
                "Leibniz / Wolffian scholasticism; contrast 'libertas indifferentiae'"
            ),
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "The attribution of the term to Kant, KpV Ak. V:96, was removed from "
                "latin_locus 2026-08-16: that passage is the Bratenwender/turnspit "
                "argument and does not report 'libertas spontaneitatis'. No "
                "replacement locus invented."
            ),
        },
    ),
    "concept_gratia_cooperans": (
        # tag: "The coinage_note text is truncated mid-sentence ('Keep \\'gratia
        #   cooperans\\' as the re'). Data-quality defect … should be completed or
        #   trimmed."  Trimmed to the last complete sentence; the greek_term is
        #   relabelled as the coinage_note itself instructs.
        {
            "op": "str_replace",
            "key": "coinage_note",
            "old": (" Keep 'gratia cooperans' as the re"),
            "new": "",
        },
        {
            "op": "set",
            "key": "greek_term",
            "value": (
                "χάρις συνεργοῦσα (charis synergousa) — modern scholarly rendering of "
                "the Latin, NOT an attested ancient term"
            ),
        },
    ),
    "concept_gratia_operans": (
        # tag: "'χάρις ἐνεργοῦσα' is a modern scholarly back-translation of the Latin,
        #   NOT an attested Augustinian/ancient Greek term, but is pr[esented as one]"
        #   — the sibling node concept_gratia_cooperans already carries a
        #   `greek_status` field saying exactly this.
        {
            "op": "set",
            "key": "greek_term",
            "value": (
                "χάρις ἐνεργοῦσα (charis energousa) — modern scholarly rendering of "
                "the Latin, NOT an attested ancient term"
            ),
        },
        {
            "op": "set",
            "key": "greek_status",
            "value": "modern_scholarly_rendering — NOT an attested ancient term",
        },
    ),
    # --- counts, dates, identifiers -----------------------------------------
    "sc379_athenagoras_legatio": (
        # tag: "the Legatio has 37 chapters; metadata records 38 … (the field looks
        #   like a count of page_index entries, so verify before editing)".  Verified:
        #   page_index has 38 entries, of which 37 carry a numeric chapter_ref and one
        #   is the 'dédication'.
        {"op": "set_if", "key": "total_chapters", "old": 38, "value": 37},
    ),
    "pub_amand_1945_fatalisme": (
        # tag: "ISBN 9789025606466 belongs to the 1973 Amsterdam (A. M. Hakkert)
        #   REPRINT, not the 1945 Louvain original … ISBNs did not exist in 1945"
        {"op": "delete", "key": "isbn"},
        {
            "op": "set",
            "key": "reprint",
            "value": "Amsterdam: A. M. Hakkert, 1973 (ISBN 9789025606466)",
        },
    ),
    "person_ekstrom_laura_1u2v3w4x": (
        # tag: "Birth year 'fl. late 20th-21st c.' could not be confirmed from any
        #   biographical source … no published birth year".  verified_reference:
        #   "Wikidata Q113828985 … no date of birth recorded".
        {"op": "set", "key": "birth_date", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "birth_date cleared 2026-08-16: the placeholder 'fl. late 20th-21st c.' "
                "was unverifiable and Wikidata Q113828985 records no date of birth."
            ),
        },
    ),
    "person_ginet_carl_0t1u2v3w": (
        # tag: "death_date '2017 CE' could not be independently verified from a
        #   critical/biographical source. Carl Ginet (b. 1932, Cornell emeritus) — the
        #   year of death should be confirmed before asserting it"
        {"op": "set", "key": "death_date", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "death_date '2017 CE' cleared 2026-08-16 as unverified; birth_date "
                "1932 is retained (Cornell emeritus). No replacement asserted."
            ),
        },
    ),
    "scholar_jacobsen_a": (
        # tag: "birth-year inconsistency … at least one of the two values is wrong"
        #   + "No 'Universal Salvation: The Current Debate' (Cambridge University
        #   Press, 2019) edited by Jacobsen could be found. The title matches R. Parry
        #   & C. Pa[rtridge]"
        {
            "op": "list_remove",
            "key": "key_works",
            "value": "Universal Salvation: The Current Debate (CUP 2019, ed.)",
        },
        {"op": "set", "key": "birth_date", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "birth_date cleared 2026-08-16 (metadata said 1963, the prose 1962; "
                "neither could be confirmed). key_works: 'Universal Salvation: The "
                "Current Debate (CUP 2019, ed.)' removed — the title belongs to Parry "
                "& Partridge, not to Jacobsen."
            ),
        },
    ),
    "scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th": (
        # tag: "This is a Modern Scholar / Recorded Books audio lecture course with a
        #   printed course guide, not a conventional 'monograph'. 'audio lecture
        #   course' / 'course guide' would be more precise."
        {
            "op": "set_if",
            "key": "type",
            "old": "monograph",
            "value": "audio_lecture_course",
        },
    ),
    "work_salles_stoics_determinism_2008": (
        # tag: "the monograph appeared as Ashgate, 2005 (Ashgate New Critical Thinking
        #   in Philosophy), not 2008 as the node id ('_2008') implies. metadata omits
        #   year and publisher → add year: 2005, publisher: Ashgate"
        {"op": "set", "key": "year", "value": 2005},
        {"op": "set", "key": "publisher", "value": "Ashgate"},
        {
            "op": "set",
            "key": "series",
            "value": "Ashgate New Critical Thinking in Philosophy",
        },
        {"op": "delete", "key": "needs_edition_metadata"},
        {
            "op": "set",
            "key": "node_id_note",
            "value": (
                "The node id carries '_2008', which is wrong: the monograph is Ashgate "
                "2005. The id is left unchanged because edges and citations reference "
                "it; the bibliographic fields are authoritative."
            ),
        },
    ),
    "work_tertullian_adv_marcionem": (
        # tag: "the description text ends 'CTS URN: stoa0275.stoa006' while
        #   metadata.canonical_id = 'urn:cts:latinLit:stoa0275.stoa015'. Both cannot be
        #   right".  Adjudicated against data/corpus/manifest.jsonl, which ingests
        #   Adversus Marcionem from scaife:urn:cts:latinLit:stoa0275.stoa015.opp-lat1
        #   (stoa0275.stoa007 being De Anima): stoa015 is correct.
        {
            "op": "set",
            "key": "cts_urn_note",
            "value": (
                "stoa006-vs-stoa015 adjudicated 2026-08-16 in favour of "
                "urn:cts:latinLit:stoa0275.stoa015: that is the URN under which the "
                "project corpus ingests Adversus Marcionem "
                "(scaife:urn:cts:latinLit:stoa0275.stoa015.opp-lat1, "
                "data/corpus/manifest.jsonl). The description's stoa0275.stoa006 was "
                "the erroneous value and had already been dropped from the prose."
            ),
        },
    ),
    "work_gregory_de_anima_resurrectione": (
        # tag: "'Maraval, SC 614 (Cerf 2022)' cannot be verified: Pierre Maraval died
        #   in 2017, and there is no known Sources Chrétiennes edition of De anima et
        #   resurrectione".  verified_reference lists the real editions and gives
        #   Terrieux (Cerf 1995) as the French translation.
        {
            "op": "list_remove",
            "key": "editions",
            "value": "Maraval, SC 614 (Cerf 2022)",
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "editions: 'Maraval, SC 614 (Cerf 2022)' removed 2026-08-16 as "
                "unverifiable (Maraval d. 2017; no SC edition of this work). The "
                "French translation actually used is Terrieux, Cerf 1995, recorded in "
                "verified_reference."
            ),
        },
    ),
    # --- DOI fields holding something that is not a DOI ---------------------
    "scholarly_work_dettwiler_2008_l_p_tre_aux_eph_siens": (
        # tag: "The 'doi' field holds a UNIGE Archive ouverte repository handle/URL
        #   (unige:39485), which is NOT a DOI … the value should be moved to a URL
        #   field and the doi left null."
        {
            "op": "set",
            "key": "url",
            "value": "http://archive-ouverte.unige.ch/unige:39485",
        },
        {"op": "set", "key": "doi", "value": None},
    ),
    "scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens": (
        # tag: same, unige:39486
        {
            "op": "set",
            "key": "url",
            "value": "http://archive-ouverte.unige.ch/unige:39486",
        },
        {"op": "set", "key": "doi", "value": None},
    ),
    "scholarly_work_sharples_2003_threefold_providence_the_history_and_bac": (
        # tag: "The 'doi' field holds a JSTOR stable URL … which is a stable-link not a
        #   DOI. Content is correct … but it is mislabelled as a DOI."
        {"op": "set", "key": "url", "value": "https://www.jstor.org/stable/43767935"},
        {"op": "set", "key": "doi", "value": None},
    ),
    "scholarly_work_velardo_2013_notas_teol_gicas_de_bellum_judaicum": (
        # tag: "The DOI 10.2307/25930006008 is fabricated: 10.2307/ is the JSTOR
        #   prefix, but this article is not on JSTOR. The number 25930006008 is the
        #   redalyc.org article id (redalyc.org/articulo.oa?id=25930006008)"
        {"op": "set", "key": "doi", "value": None},
        {
            "op": "set",
            "key": "url",
            "value": "https://www.redalyc.org/articulo.oa?id=25930006008",
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "doi '10.2307/25930006008' cleared 2026-08-16 as fabricated: the "
                "number is the redalyc.org article id, not a JSTOR DOI. The article "
                "(Enfoques XXV.1, 2013, 127-136) has no registered DOI."
            ),
        },
    ),
    # --- page_range fields holding markdown extraction line numbers ---------
    "scholarly_argument_bobzien_middle_platonist_synthesis_4": (
        # tag: "'905-922' is the character-offset marker [Bobzien - 1998:905-922] from
        #   the summary, not a page. Article is 133-175, so 905-922 is impossible. The
        #   synthesis discussion falls within 133-175"
        {"op": "set_if", "key": "page_range", "old": "905-922", "value": "133-175"},
    ),
    "scholarly_argument_bobzien_origin_of_the_free_will_proble_0": (
        # tag: "None of these are page numbers: they are the summary's character-offset
        #   markers … The article is Phronesis 43.2:133-175"
        {
            "op": "set_if",
            "key": "page_range",
            "old": "22-31, 187-194, 905-922",
            "value": "133-175",
        },
    ),
    "scholarly_argument_bobzien_justin_martyr_on_fate_9": (
        # tag: "'6801-6802' is a character-offset marker … not a page. The book has
        #   ~440 pages. Exact book page for the Justin mention could not be confirmed"
        {"op": "set", "key": "page_range", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "page_range '6801-6802' cleared 2026-08-16: a character-offset marker "
                "from the local summary file, not a page range. The real page could "
                "not be recovered, so none was invented."
            ),
        },
    ),
    "scholarly_argument_fee_absence_of_libertarian_free_wi_2": (
        # tag: "page_range '681-687, 912-915, 15682-15694' — the values are extraction
        #   MARKDOWN line-numbers … '15682-15694' is impossible f[or a 992-page book]"
        {"op": "set", "key": "page_range", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "page_range '681-687, 912-915, 15682-15694' cleared 2026-08-16: "
                "markdown line numbers from Fee_1994.summary.md, not book pages "
                "(the book has 992 pp.). No replacement invented."
            ),
        },
    ),
    "scholarly_argument_list_epistemological_foundation_of__2": (
        # tag: "'429-431' are line numbers in the local extraction … the article runs
        #   Vigiliae Christianae (2024) pp.1-21, so a page_range of 429-431 is out of
        #   range"
        {"op": "set", "key": "page_range", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "page_range '429-431' cleared 2026-08-16: extraction line numbers, not "
                "journal pages (List, VC 78, 2024, runs pp. 1-21). No replacement "
                "invented."
            ),
        },
    ),
    "scholarly_argument_list_justin_martyr_s_anti_heresiolo_1": (
        # tag: "'480-481, 785-787, 952-954' are extraction line-numbers … the article
        #   is Vigiliae Christianae (2024) pp.1-21, so these figures are impossible"
        {"op": "set", "key": "page_range", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "page_range '480-481, 785-787, 952-954' cleared 2026-08-16: extraction "
                "line numbers, not journal pages (List, VC 78, 2024, pp. 1-21)."
            ),
        },
    ),
    "scholarly_argument_bird_paul_s_view_of_salvation_and_d_0": (
        # tag: "page_range is 'Introduction', but the cited substance … comes from
        #   Schreiner's own essay".  verified_reference locates it at "pp. ~19-50",
        #   an approximation, so the field is cleared rather than filled with it.
        {"op": "set", "key": "page_range", "value": None},
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "page_range 'Introduction' cleared 2026-08-16: the substance cited "
                "comes from Schreiner's own essay in the volume, not from Bird's "
                "introduction. verified_reference gives only an approximate span "
                "(pp. ~19-50), so no exact range was asserted."
            ),
        },
    ),
    # --- supporting_evidence / engages_with_scholars containing bad items ---
    "scholarly_argument_hick_free_will_and_moral_evil_0": (
        # tag: "Erroneous engagement entry: Alvin Plantinga appears 0 times in the
        #   cited 1966 text; his free-will defense (God and Other Minds 1967; The
        #   Nature of Necessity 1974) postdates the 1966 first edition"
        {
            "op": "list_remove",
            "key": "engages_with_scholars",
            "value": {
                "note": "contemporary advocate of Augustinian free-will defense discussed in chapter 17",
                "stance": "cites",
                "scholar": "Alvin Plantinga",
            },
        },
    ),
    "scholarly_argument_telfer_free_will_and_determinism_in_e_0": (
        # tag: "engages_with_scholars attributes an E.C. Hoskyns citation ('three days'
        #   significance) to Telfer's autexousia argument. That Hoskyns/'three days'
        #   reference belongs to the PRECEDING, unrelated article"
        {
            "op": "list_remove",
            "key": "engages_with_scholars",
            "value": {
                "note": "cited for interpretation of 'three days' significance in preceding note by B.M. Metzger",
                "stance": "cites",
                "scholar": "E.C. Hoskyns",
            },
        },
    ),
    "scholarly_argument_dihle_greek_philosophical_theology_a_0": (
        # tag: "'Cleanthes ap. Seneca Epistulae 41.1' is a doubtful pairing: Seneca Ep.
        #   41.1 ('prope est a te deus, tecum est, intus est') is Seneca's own Stoic
        #   formulation, not a fragment quoted from Cleanthes"
        {
            "op": "list_replace",
            "key": "supporting_evidence",
            "old": "Cleanthes ap. Seneca Epistulae 41.1, Quaestiones naturales 2.35",
            "value": (
                "Seneca, Epistulae 41.1 (Seneca's own Stoic formulation, not a "
                "Cleanthes fragment); Seneca, Quaestiones naturales 2.35"
            ),
        },
    ),
    "scholarly_argument_jourdan_determinism_and_fate_vs_free_w_2": (
        # tag: "Two of the Clement citations are malformed and could not be confirmed
        #   against Jourdan's text: 'Stromates I 2,19.94,1-7' and 'Stromates I
        #   3,26.1-27.3' mix chapter/section numbering incoherently"
        {
            "op": "list_remove",
            "key": "supporting_evidence",
            "value": "Clement of Alexandria, Stromates I 2,19.94,1-7",
        },
        {
            "op": "list_remove",
            "key": "supporting_evidence",
            "value": "Clement of Alexandria, Stromates I 3,26.1-27.3",
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "Two malformed Clement citations ('Stromates I 2,19.94,1-7' and "
                "'Stromates I 3,26.1-27.3') removed from supporting_evidence "
                "2026-08-16; the tag gives no well-formed replacement, so none was "
                "invented."
            ),
        },
    ),
    "scholarly_argument_linjamaa_cosmos_as_school_and_community_4": (
        # tag: "All five TriTrac loci … are fabricated/invalid. The Tripartite Tractate
        #   (NHC I,5) runs only to codex page 138:27"
        {
            "op": "list_set",
            "key": "supporting_evidence",
            "value": [
                "TriTrac (NHC I,5) 71:22-23 ('school of conduct')",
                "TriTrac (NHC I,5) 123:12 ('a place of instruction')",
                "Linjamaa 2019, ch. 5 'The Cosmos as a School' (pp. 185-226)",
            ],
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "supporting_evidence: the five TriTrac loci '140:32-144:16', "
                "'144:17-148:21', '148:22-152:26', '152:27-156:31', '156:32-160:36' "
                "removed 2026-08-16 as impossible (the tractate ends at 138:27); "
                "replaced by the loci this node's own verified_reference confirms."
            ),
        },
    ),
    "scholarly_argument_linjamaa_social_and_political_involveme_5": (
        # tag: "The four TriTrac codex citations 'TriTrac 160:37-164:41',
        #   '164:42-168:46', '168:47-172:51', '172:52-176:56' are impossible"
        {
            "op": "list_set",
            "key": "supporting_evidence",
            "value": [
                "1 Cor 7:17-24 on remaining in one's calling",
                "Rom 13:1-7 on obedience to authorities",
                "Linjamaa 2019, ch. 6 'Honor and Attitudes toward Social and Political Involvement' (pp. 227-258)",
            ],
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "supporting_evidence: the four impossible TriTrac codex citations "
                "(160:37-176:56, beyond the tractate's extent) removed 2026-08-16; the "
                "biblical loci and the chapter reference from verified_reference are "
                "retained. No replacement codex locus invented."
            ),
        },
    ),
    "scholarly_argument_prigent_determinism_and_predestination_1": (
        # tag: "Malformed citation range 'Barnabas 4.9-5' (chapter.verse-chapter with
        #   no closing verse). Should be a well-formed range within the eschatological/
        #   last-days material of Barn. 4-5 … cannot [be determined more precisely]"
        {
            "op": "list_replace",
            "key": "supporting_evidence",
            "old": "Barnabas 4.9-5",
            "value": "Barnabas 4-5 (eschatological / last-days material)",
        },
    ),
    "argument_cafma_futility_of_sanctions_0e5f7h43": (
        # tag: "Aulus Gellius NA VII.2 is Chrysippus's compatibilist cylinder defense,
        #   not a witness to the Carneadean praise/blame reductio."
        {
            "op": "list_remove",
            "key": "ancient_sources",
            "value": "Aulus Gellius, Noctes Atticae VII.2.1-15",
        },
    ),
    "argument_sea_battle_aristotle_f6g7h8i9": (
        # tag: "bobzien_2001_chapter title 'Ch. 2 Two Chrysippean Arguments for Causal
        #   Determinism' could not be confirmed as the exact chapter heading of
        #   Bobzien, Determinism and Freedom in Stoic Philosophy"
        {
            "op": "set_if",
            "key": "bobzien_2001_chapter",
            "old": "Ch. 2 Two Chrysippean Arguments for Causal Determinism",
            "value": "Ch. 2",
        },
    ),
    "argument_tertullians_antimarcionite_argument_for_free_will_f49cad73": (
        # tag: "Premises P1-P4 (unus deus omnipotens mundi conditor; Father/Son/Spirit
        #   as oikonomia; the Word sent into the Virgin; 'the devil emulates truth to
        #   shake it') are verbatim from [a different work]" — the tag truncates before
        #   naming it, so the false groundings are cleared, not re-pointed.
        {
            "op": "premise_clear_sources",
            "key": "premises",
            "ids": ["P1", "P2", "P3", "P4"],
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "primary_sources cleared on premises P1-P4 2026-08-16: the tag records "
                "that these four premises are verbatim from a different Tertullianic "
                "work than the Adversus Marcionem / De anima loci they were anchored "
                "to, but truncates before naming it. No replacement locus invented; "
                "the node's genuine anti-Marcionite grounding is Adv. Marc. II.5-7 "
                "(verified_reference)."
            ),
        },
    ),
    "argument_plutarch_providence_cooperation_8c5a9d3f": (
        # tag: "The tripartite-providence doctrine occurs only in the pseudonymous De
        #   Fato (correctly signalled 'Pseudo-Plutarch' in the label), yet formulator
        #   is set to 'Plutarch'."
        {
            "op": "set_if",
            "key": "formulator",
            "old": "Plutarch",
            "value": "Pseudo-Plutarch",
        },
    ),
    "argument_adversity_exercise_seneca_g8h9i0j1": (
        # tag: "The pivot maxim 'Marcet sine adversario virtus' is at De Prov 2.4 …
        #   the node anchors it to passage_sen_prov_2_3."  The prose was relocated to
        #   2.4 by the 2026-08-14 pass; the metadata anchor is fixed here.
        #   Verified: passage_sen_prov_2_4 exists in nodes.jsonl.
        {
            "op": "str_replace",
            "key": "legacy_premises.1.primary_sources.0",
            "old": "passage_sen_prov_2_3",
            "new": "passage_sen_prov_2_4",
        },
        {
            "op": "set",
            "key": "needs_evidence_note",
            "value": (
                "legacy_premises P2 ('Virtue languishes without an opponent') was "
                "re-anchored 2026-08-16 from passage_sen_prov_2_3 to "
                "passage_sen_prov_2_4, matching the 2.3→2.4 relocation of the maxim "
                "already applied to the prose. The other premises keep their own "
                "anchors: the tag flags only the maxim."
            ),
        },
    ),
    "scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v": (
        # tag: "The article is co-authored by Fabienne Pironet AND Christine Tappolet …
        #   the single author_id scholar_pironet_f omits the co-author Tappolet."
        #   No scholar node exists for Tappolet, so the co-author is recorded by name.
        {"op": "set", "key": "additional_authors", "value": ["Christine Tappolet"]},
    ),
    "scholarly_work_pouderon_2003_aristide_apologie": (
        # tag: "SC 470 is edited by Bernard Pouderon AND Marie-Joseph Pierre (with B.
        #   Outtier and M. Guiorgadzé for the Armenian/Georgian); single author_id
        #   scholar_pouderon_b omits co-editor Pierre."
        {
            "op": "set",
            "key": "additional_authors",
            "value": ["Marie-Joseph Pierre", "Bernard Outtier", "Manana Guiorgadzé"],
        },
    ),
    "sc79_chrysostomus_de_providentia": (
        # tag: "the SC number (79), the Malingrey edition, and the inge[sted text]" do
        #   not match the six Discourses on Fate and Providence (PG 50, 749-774) the
        #   node describes.  SC 79 = Ad eos qui scandalizati sunt = PG 52:479-528, a
        #   different work.  Recorded rather than silently resolved.
        {
            "op": "set",
            "key": "work_identity_conflict",
            "value": (
                "UNRESOLVED (recorded 2026-08-16): the node id and sc_number/sc_volume/"
                "sc_edition fields identify SC 79 = Malingrey, Sur la providence de "
                "Dieu (Ad eos qui scandalizati sunt) = PG 52:479-528, while the "
                "description and the ingested passages are the six Discourses on Fate "
                "and Providence, PG 50:749-774 — a different work of disputed "
                "authenticity. Both cannot describe the same text; the corpus rows "
                "must be re-homed before either field is changed."
            ),
        },
    ),
    "concept_carneadean_probabilism_amand1945": (
        # tag: "the description cites Amand '1945, p. 65, Intro §II ch. III §III', while
        #   metadata.amand_location gives 'Introduction §II Ch. II, p. 41-58'. Chapter
        #   (III vs II) and page ([differ])" — the tag truncates before adjudicating.
        # Adjudicated 2026-08-16 against the local OCR of Amand 1945/1973: the section
        # heading «III. SA CONCEPTION PRAGMATISTE DE LA LIBERTÉ» stands under
        # «CHAPITRE III. L'argumentation éthique de Carnéade contre le fatalisme
        # astrologique», and the nearest page marker above it is 65. The description
        # was right; the backfilled metadata was wrong.
        {
            "op": "set",
            "key": "amand_location",
            "value": {
                "chapter": "Introduction, Chapitre III §III (« Sa conception pragmatiste de la liberté »)",
                "page_range": "p. 65",
            },
        },
    ),
    "synthesis_amand1945_plato_partial_anti_fatalism": (
        # tag: "metadata gives 'Introduction §I (Platon), p. 20-40' while the description
        #   gives 'Intro §II ch. I §II, p. 31-33'. Both correctly place the treatment
        #   i[n the Introduction]".  Adjudicated 2026-08-16 against the local OCR:
        #   Plato is section III of «CHAPITRE PREMIER. La polémique antifataliste avant
        #   Carnéade», and the «Αἰτία ἑλομένου· θεὸς ἀναίτιος / ἀρετὴ ἀδέσποτον» passage
        #   the node quotes sits under the page marker 32 — i.e. inside the p. 31-33 the
        #   description and verified_reference give, not the metadata's p. 20-40.
        {
            "op": "set",
            "key": "amand_location",
            "value": {
                "chapter": "Introduction, Chapitre Premier §III (« Platon »)",
                "page_range": "p. 31-33",
            },
        },
    ),
    "scholarly_argument_crouzel_manuscript_tradition_and_textu_1": (
        # tag: "scholar_id points to scholar_crouzel_henri, but the cited textual-
        #   critical section is Simonetti's … REMAINING: metadata.scholar_id still
        #   reads scholar_crouzel_henri because the KG contains no person/scholar node
        #   for Manlio Simonetti; creating one and re-pointing scholar_id (and the
        #   created_by edge) is the outstanding step."
        {"op": "set", "key": "scholar_id", "value": "scholar_simonetti_m"},
    ),
}

# ---------------------------------------------------------------------------
# New node created so that a corrected `scholar_id` has a real referent.
# Every assertion is taken from the SC 312 Avant-Propos quoted in the tag and
# in the node's own `verified_reference`; no biographical data is invented.
# ---------------------------------------------------------------------------
NEW_NODES: tuple[dict, ...] = (
    {
        "node_id": "scholar_simonetti_m",
        "id": "scholar_simonetti_m",
        "type": "person",
        "label": "Manlio Simonetti",
        "role": "scholar",
        "school": None,
        "period": "Contemporary",
        "alternative_names": "[]",
        "description": (
            "Italian patristics scholar. In Sources Chrétiennes 312 (Origène, "
            "Traité des principes, tome V, Cerf 1984) he is the author of the "
            "«Compléments sur la tradition manuscrite du Traité des Principes» "
            "(pp. 11-17), the section that argues against Koetschau's preference "
            "for the lectio facilior; the Addenda et Corrigenda and the indices of "
            "that volume are Henri Crouzel's, per the volume's own Avant-Propos."
        ),
        "metadata": {
            "role": "scholar",
            "surname": "Simonetti",
            "given_names": "Manlio",
            "node_origin": "second_sweep_2026_08_16",
            "citation_verified": True,
            "verified_reference": (
                "SC 312 = Origène, Traité des principes, tome V (Crouzel & "
                "Simonetti, Cerf, 1984), Avant-Propos: «Ce tome V… contient surtout "
                'les index. Ceux-ci sont précédés par des "compléments sur la '
                'tradition manuscrite" rédigés par M. Simonetti et par quelques '
                '"Addenda et Corrigenda" qui, avec les index, sont l\'œuvre de H. '
                "Crouzel.»"
            ),
            "needs_evidence_note": (
                "Created 2026-08-16 solely so that "
                "scholarly_argument_crouzel_manuscript_tradition_and_textu_1 could "
                "point its scholar_id / created_by at the right person. Biographical "
                "data (dates, affiliations, other works) is deliberately absent: none "
                "was verifiable from the sources in hand."
            ),
        },
    },
)

# Edge whose `target_id` must follow the corrected scholar_id.
EDGE_RETARGETS: tuple[dict, ...] = (
    {
        "edge_id": "950a2601-bf64-4059-8530-b9ecda110622",
        "field": "target_id",
        "old": "scholar_crouzel_henri",
        "new": "scholar_simonetti_m",
    },
)

# ---------------------------------------------------------------------------
# 2. Reader-facing prose: completions + curator-bracket merges
# ---------------------------------------------------------------------------
DESCRIPTION_REWRITES: dict[str, tuple[tuple[str, str], ...]] = {
    # --- §3 curator brackets of other shapes --------------------------------
    "argument_aquinass_intellectualism_f0058bf9": (
        # bracket: "[Correction 2026-08-02 : ST I-II qq.1-5 traitent de la fin
        #   ultime/béatitude ; l'action volontaire et humaine est aux qq.6-17. Les
        #   textes intellectualistes les plus nets : ST I q.82-83 et I-II q.9-10.]"
        (
            "Key texts: Summa Theologica I-II, q.1-5 (on happiness and voluntary action); "
            "De Veritate q.24, a.1-2 (on liberum arbitrium)",
            "Key texts: Summa Theologica I-II, qq.1-5 (on the ultimate end and beatitude) "
            "and qq.6-17 (on the voluntary and on human action); the sharpest "
            "intellectualist texts are ST I, qq.82-83 and I-II, qq.9-10; "
            "De Veritate q.24, a.1-2 (on liberum arbitrium)",
        ),
    ),
    "argument_gersonides_limited_omniscience_s9t0u1v2": (
        # bracket: "[Correction 2026-08-02 : ne pas dire que Dieu « apprend » quand
        #   Pierre pèche (savoir temporel acquis) — cela contredit Gersonide ; Dieu
        #   connaît le particulier seulement en tant qu'ordonné par l'ordre naturel
        #   général.]"
        (
            "When Peter sins, God knows it. Omniscience is perfect knowledge of all "
            "knowables; but indeterminate futures aren't yet knowable.",
            "God is not said to *learn* anything when Peter sins — ascribing acquired "
            "temporal knowledge to God contradicts Gersonides; God knows the particular "
            "only in so far as it is ordered by the general natural order. Omniscience "
            "is perfect knowledge of all knowables; but indeterminate futures aren't yet "
            "knowable.",
        ),
    ),
    "argument_moral_assessment_alex": (
        # bracket: "[Précision philologique 2026-08-03 : la définition ἕξις προαιρετική
        #   est aristotélicienne (EN II.6, 1106b36) ; dans le corpus d'Alexandre, la
        #   formule n'apparaît que dans l'In Topica et les Problèmes éthiques (Bruns
        #   143), jamais dans le De fato — P1 est donc doctrinal, non verbatim. Ce qui
        #   est verbatim au De fato 19-20 (Bruns 189-191) est l'argument de l'éloge, du
        #   blâme et du châtiment, et au De fato 26-29 (Bruns 196.24-197.3) celui de la
        #   vertu et du vice.]"
        # The Greek formula itself is deliberately NOT moved into the description:
        # the prose already carries its transliteration, and the bracket is preserved
        # verbatim in metadata.verification_notes.
        (
            "Sources: Fat. 19-20: Virtue presupposes choice; necessity undermines "
            "voluntariness; virtue's existence refutes determinism\n"
            "Fat. 28: Vices also presuppose freedom; moral assessment is universal human practice",
            "Sources: the definition of virtue as a hexis proairetikē (P1) is "
            "Aristotelian (EN II.6, 1106b36); in Alexander's corpus the formula occurs "
            "only in the In Topica and the Ethical Problems (Bruns 143), never in the "
            "De fato, so P1 is doctrinal rather than verbatim. What the De fato does "
            "carry verbatim is the praise/blame/punishment argument at De fato 19-20 "
            "(Bruns 189-191) and the virtue-and-vice argument at De fato 26-29 "
            "(Bruns 196.24-197.3).",
        ),
    ),
    "argument_pascals_wager_and_voluntarism_4519ad75": (
        # bracket: "[Correction 2026-08-02 : le fragment du Pari (Laf. 418) porte
        #   « vous fera croire » (futur), non l'impératif « abêtissez-vous », qui est
        #   une reformulation.]"
        (
            '"Abêtissez-vous" (Make yourself stupid/dull your reason): Participate in '
            "religious practices (Mass, holy water, etc.).",
            'The traditional catchphrase "abêtissez-vous" ("make yourself stupid", i.e. '
            "dull your reason) is a later reformulation: the Wager fragment (Laf. 418) "
            'has the future indicative "vous fera croire". Pascal\'s point is practical: '
            "participate in religious practices (Mass, holy water, etc.).",
        ),
    ),
    # --- §2 completions now supported by re-verified evidence ---------------
    "argument_lazy_argument_alex": (
        # tag: "The 'Lazy Argument' (ἀργὸς λόγος) is a fatalist SOPHISM … [not this
        #   argument]".  verified_reference names both the node's real locus (De Fato
        #   ch. 11) and the ἀργὸς λόγος proper (Cic. Fat. 28-30; Orig. C. Cels. II.20).
        (
            "This is a PRAGMATIC argument: even if determinism were true, believing it "
            "would be catastrophic. The Stoics famously tried to answer this argument - "
            "Alexander thinks they failed.",
            "This is a PRAGMATIC argument: even if determinism were true, believing it "
            "would be catastrophic. The Stoics famously tried to answer this argument - "
            "Alexander thinks they failed.\n\n"
            'Terminological caveat: this is not the ἀργὸς λόγος ("Lazy Argument") '
            "proper. That is a fatalist sophism — if it is fated that you will recover, "
            "you will recover whether or not you call the doctor, so effort is idle — "
            "attested at Cicero, De fato 28-30 and Origen, Contra Celsum II.20, and "
            "answered by Chrysippus through co-fated events. What this node "
            "reconstructs is Alexander's deliberation-in-vain / consequences-for-"
            "motivation argument of De fato 11.",
        ),
    ),
    "argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will": (
        # tag doubted that Wildberg contributed to the volume at all.  Re-verified
        # against the local .md extraction of Destrée–Salles–Zingano 2014: his chapter
        # "The will and its freedom: Epictetus and Simplicius on what is up to us"
        # opens at p. 329 and is the 21st contribution (Michael Frede's opens at 351).
        (
            "Argument scholarly attribué à Wildberg (Destrée 2014, chapitre non identifié) : "
            "deux thèses.",
            "Argument scholarly de Christian Wildberg, « The will and its freedom: "
            "Epictetus and Simplicius on what is up to us », 21e contribution du volume "
            "Destrée–Salles–Zingano 2014 (p. 329-349) : deux thèses.",
        ),
    ),
    "scholar_wildberg_christian": (
        (
            "Auteur du chapitre « The will and its freedom: Epictetus and Simplicius on "
            "what is up to us » du volume Destrée 2014,",
            "Auteur du chapitre « The will and its freedom: Epictetus and Simplicius on "
            "what is up to us » (ch. 21, p. 329-349) du volume Destrée 2014,",
        ),
    ),
    "argument_gomez_2014_chrysippus_reactive_compatibilism": (
        # tag: "The modern-scholarship attribution to a contributor named 'Gómez' with a
        #   chapter ('ch. 8') in Destrée 2014 could not be confirmed."  Re-verified:
        #   Laura Liliana Gómez, 'Chrysippean compatibilistic theory of fate, what is up
        #   to us, and moral responsibility', opens at p. 121 and is the 8th
        #   contribution (Gourinat's opens at 141).
        (
            ", dont l'auteur du chapitre n'a pu être confirmé : ",
            " — chapitre de Laura Liliana Gómez, « Chrysippean compatibilistic theory of "
            "fate, what is up to us, and moral responsibility » (8e contribution, "
            "p. 121-139) : ",
        ),
    ),
    "synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate": (
        # tag: "Page locus unreliab[le]" — the correct span was not recoverable then.
        #   Re-verified: Bonazzi's chapter opens at p. 283, Horn's at p. 295.
        (
            "Synthèse du ch. 18 (Bonazzi) :",
            "Synthèse du ch. 18 (Bonazzi, p. 283-293) :",
        ),
    ),
    "person_cyrus_alexandria_d641": (
        # tag: "he did not survive to be 'dé[…]'" — truncated.  The node's own
        # verified_reference supplies the chronology: "negotiated the Treaty of
        # Alexandria 8 Nov 641 and died 21 March 642 (before the Arab entry,
        # 29 Sept 642); cf. Theophanes, Chronographia AM 6133-6134".
        (
            "puis réhabilité ; Alexandrie tombe aux mains des Arabes ('Amr ibn al-'As) "
            "en 642. Sources : ACO ser. II ; Théophane, *Chronographia* AM 6121-6132 "
            "(éd. de Boor 1883).",
            "puis réhabilité ; il négocie le traité d'Alexandrie le 8 novembre 641 et "
            "meurt le 21 mars 642, avant l'entrée des Arabes ('Amr ibn al-'As) dans la "
            "ville le 29 septembre 642. Sources : ACO ser. II ; Théophane, "
            "*Chronographia* AM 6121-6134 (éd. de Boor 1883) ; P. Booth, *Crisis of "
            "Empire* (2014).",
        ),
    ),
    "work_augustine_retractationes": (
        # tag truncated after "De correptione et gratia," — the two treatises the tag
        # does name are added; the rest of its list is not guessed at.
        (
            "Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le "
            "*De Gratia et Libero Arbitrio* (426/427) — ne figurent pas",
            "Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le "
            "*De Gratia et Libero Arbitrio* (426/427) et le *De Correptione et Gratia* "
            "— ne figurent pas",
        ),
    ),
    "person_porphyry": (
        # The node's verified_reference names the securely attested Porphyrian material
        # on what is up to us (frr. 268-271 Smith = Stobaeus II.8.39-42), which the
        # hedged To-Nemertius paragraph left unmentioned.
        (
            "Editions: Ad Marcellam (ed. des Places, Les Belles Lettres, 1982); "
            "To Nemertius fragments in Boulnois (2000), reconstructed from Cyril's "
            "Contra Iulianum.",
            "The securely attested Porphyrian material on what is up to us is the set of "
            "fragments 268-271 Smith (= Stobaeus, Anthologium II.8.39-42), from a work "
            "Περὶ τοῦ ἐφ' ἡμῖν. Editions: Ad Marcellam (ed. des Places, Les Belles "
            "Lettres, 1982); To Nemertius fragments in Boulnois (2000), reconstructed "
            "from Cyril's Contra Iulianum.",
        ),
    ),
    "synthesis_frede2011_ch6_platonist_peripatetic_criticisms": (
        # tag: "the tag is truncated before giving Frede's actual sentence".  The
        # node's verified_reference now carries it: "'it is in Alexander that we find
        # the ancestor of the notion that to have a free will is to be able… to choose
        # between doing A and doing B' p. 99-100".
        (
            "et 'in Alexander that we find the ancestor of the notion' modern "
            "voluntariste critiquée par Ryle, Williams et Frede.",
            "et « it is in Alexander that we find the ancestor of the notion that to "
            "have a free will is to be able… to choose between doing A and doing B » "
            "(p. 99-100) — la notion moderne volontariste critiquée par Ryle, Williams "
            "et Frede.",
        ),
    ),
    "argument_pseudo_chrysostom_de_fato_v_witness6_amand1945": (
        # tag: "the sub-page spans for the French translation and the Greek text are
        #   lost".  The node's verified_reference now carries them: "French translation
        #   pp. 520-527, Greek text after Montfaucon pp. 527-532".
        (
            "Amand publie d'abord la traduction française intégrale, puis le texte grec "
            "original d'après Montfaucon (l'ensemble p. 519-532).",
            "Amand publie d'abord la traduction française intégrale (p. 520-527), puis "
            "le texte grec original d'après Montfaucon (p. 527-532), l'ensemble occupant "
            "p. 519-532.",
        ),
    ),
    "concept_providentia_stoic_seneca_b3c4d5e6": (
        # tag: "the other two phrases attributed to '(1.1)' … [flagged]" — the loci were
        # dropped.  The node's verified_reference quotes the whole De prov. 1.1 period
        # and both phrases stand inside it, so the loci are restored.
        (
            '• "praeesse universis providentiam" - providence presides over all\n'
            '• "interesse nobis deum" - god is involved in our affairs',
            '• "praeesse universis providentiam" (1.1) - providence presides over all\n'
            '• "interesse nobis deum" (1.1) - god is involved in our affairs',
        ),
    ),
    "concept_fortuna_boethius_j5k6l7m8": (
        # tag: "Only minor: 'inconstantia mea' at 'II.1.10' … [truncated]".  The node's
        # verified_reference gives the full Fortuna sentence and its locus (II pr. 2).
        (
            'Latin texts: • "Haec nostra vis est, hunc continuum ludum ludimus: rotam '
            'volubili orbe versamus"\n (This is my power, this is the game I play: I '
            "turn the wheel with its spinning circle)",
            'Latin texts: • "Haec nostra vis est, hunc continuum ludum ludimus; rotam '
            'volubili orbe versamus, infima summis summa infimis mutare gaudemus" '
            "(II, pr. 2)\n (This is my power, this is the game I play: I turn the wheel "
            "with its spinning circle, and delight to change the lowest for the highest "
            "and the highest for the lowest)",
        ),
    ),
    "argument_clement_grace_synergy_assent": (
        # tag: "'Stromateis II.2.8 (faith as consent of soul)' — Clement's definition of
        #   πίστις as συγκατάθεσις is real but its exact section … [truncated]"; the
        #   companion tag then records "the II.2.8 question is now settled", and
        #   verified_reference gives the decoded citation "Stromateis 2.2.8.3–4".
        (
            "θεοσεβείας συγκατάθεσις, Strom. II)",
            "θεοσεβείας συγκατάθεσις, Strom. II.2.8.3-4)",
        ),
    ),
    "scholarly_argument_telfer_christian_autexousia_and_jewis_2": (
        # tag: "The attested form is undeterminable from the truncated tag (the prose
        #   had γένεα, the tag records γένη on both sides of the arrow)".  The node's
        #   verified_reference settles it by quoting Telfer p. 124 verbatim: γένεα, and
        #   marks it as Telfer's own gloss rather than a phrase of Justin.
        (
            "In Justin, autexousia applies equally to angels and humans, creating a parity",
            "In Justin, autexousia applies equally to angels and humans — Telfer's own "
            "compressed Greek gloss «γένεα αὐτεξούσια» (JTS n.s. 8, 1957, p. 124), not a "
            "verbatim phrase of Justin — creating a parity",
        ),
    ),
    "scholar_list_n": (
        # tag: "the tag is truncated before naming the other scholar, so the node label
        #   'Nicholas List' could not be verified".  The node's verified_reference now
        #   identifies him: Nicholas List, 'Justin Martyr's Problem with Platonism',
        #   Vigiliae Christianae 78 (2024).  The node therefore does not need splitting.
        (
            "Research fields recorded as Early Christian studies, Middle Platonism and "
            "Justin Martyr. These belong to a different scholar than the List discussed "
            "by Fürst 2022, which is Christian List,",
            "Nicholas List — Early Christian studies, Middle Platonism and Justin "
            "Martyr; author of 'Justin Martyr's Problem with Platonism', Vigiliae "
            "Christianae 78 (2024). Not to be confused with the List discussed by Fürst "
            "2022, who is Christian List,",
        ),
    ),
    "collection_ls": (
        # tag: "'57 (impulsion et oikeiôsis) et 65 (passions)' is doubtful: in LS the
        #   [numbering …]" — truncated, so both numbers were deleted on 2026-08-14.
        # Re-verified 2026-08-16 against the printed Contents of Long & Sedley vol. 1
        # (local PDF pp. viii-ix): 57 = "Impulse and appropriateness" (p. 346) and
        # 65 = "The passions" (p. 410). Both node numbers were right; restored.
        (
            "Sections-clés pour le KG : 20 (clinamen épicurien), 55 (causalité et "
            "destin), 62 (responsabilité morale), 68–70 (scepticisme académique, y "
            "compris Carnéade), 71–72 (renouveau pyrrhonien : Énésidème).",
            "Sections-clés pour le KG : 20 (« Free will » — clinamen épicurien, p. 102), "
            "55 (« Causation and fate », p. 333), 57 (« Impulse and appropriateness » — "
            "impulsion et oikeiôsis, p. 346), 62 (« Moral responsibility », p. 386), "
            "65 (« The passions », p. 410), 68–70 (les Académiciens, y compris Carnéade, "
            "p. 438-467), 71–72 (renouveau pyrrhonien, p. 468-488).",
        ),
    ),
    "argument_bardesanes_nomima_barbarika_amplified": (
        # tag: "The specific attributed quotation and page ('Selon Amand p. 243, …')
        #   could not be located verbatim at p. 243 in Amand".  Re-verified 2026-08-16
        #   in the local OCR of Amand 1945/1973, page header «243» immediately above:
        #   «…que Bardesane est peut-être le premier à avoir mis en œuvre avec une telle
        #   profusion et une telle exactitude documentaire».  The wording and the page
        #   are both restored; the Greek νόμιμα βαρβαρικά of the printed text is NOT
        #   restored, the OCR of that phrase being corrupt.
        (
            "Selon Amand, Bardesane serait l'un des premiers à mettre en œuvre "
            "l'argument carnéadien des nomima barbarika avec une profusion et une "
            "exactitude documentaires remarquables.",
            "Selon Amand (1945, p. 243), on reconnaît là l'argument antiastrologique "
            "carnéadien tiré des *nomima barbarika*, « fondé cette fois sur une ample "
            "moisson de renseignements ethnographiques, que Bardesane est peut-être le "
            "premier à avoir mis en œuvre avec une telle profusion et une telle "
            "exactitude documentaire ».",
        ),
    ),
    "scholar_tomberlin_j": (
        # §6.6: the residual text was stripped, leaving a bare keyword line.  The node's
        # verified_reference supplies a proper description.
        (
            "philosophy of religion, free will defence",
            "James E. Tomberlin — philosophy of religion, free-will defence. Co-author, "
            "with F. McGuinness, of 'God, Evil, and the Free Will Defence', Religious "
            "Studies 13 (1977), 455-475 (esp. pp. 456-458, engaging Plantinga's God and "
            "Other Minds and Rowe).",
        ),
    ),
}

# `metadata.description_en` counterparts of the same corrections: the 2026-08-14
# pass edited the French prose but left the English metadata carrying the error.
DESCRIPTION_EN_REWRITES: dict[str, tuple[tuple[str, str], ...]] = {
    "scholar_wildberg_christian": (
        # tag: "metadata.description_en says ch. 18 where the French said ch. 21".
        # Re-verified against the volume: Wildberg is the 21st contribution, p. 329-349.
        (
            "Author of ch. 18 of Destrée 2014",
            "Author of ch. 21 (pp. 329-349) of Destrée 2014",
        ),
    ),
    "synthesis_amand1945_origen_pivot_witness": (
        # tag: "text says « 6 témoins » but lists 7 items" + "Same spurious 7th witness
        #   in English metadata" + "'Origène = 1er témoin patristique' overstates".
        #   The French prose was corrected on 2026-08-14; the English was not.
        (
            "Amand's synthesis: Origen = 1st patristic witness of the Carneadean "
            "anti-fatalist lineage, historiographical pivot of Amand's Book II. "
            "Structural position: bridge between (a) the 6 witnesses of the Carneadean "
            "reconstruction (",
            "Amand's synthesis: Origen, the historiographical pivot of Amand's Book II "
            "in the Carneadean anti-fatalist lineage — he does not open the patristic "
            "series, since Justin (Ch. I), Tatian (Ch. II), Bardesanes (Ch. III) and "
            "Clement of Alexandria (Ch. IV) precede him. Structural position: bridge "
            "between (a) the witnesses of the Carneadean reconstruction (",
        ),
    ),
    "synthesis_furst2022_carneades_will_innovation": (
        # tag: "'libertarischer Kompatibilismus' does not occur anywhere in [Fürst
        #   2022]".  The French prose dropped the Schallenberg sentence on 2026-08-14;
        #   the English metadata kept it.  verified_reference: "'kompatibilistischer
        #   Libertarismus' is Fürst's own coinage for ORIGEN (chapter heading VI.4,
        #   p. 282)".
        (
            " Schallenberg qualifies Carneades-Cicero as 'libertarischer Kompatibilismus' "
            "(mirror parallel to the 'kompatibilistischer Libertarismus' Fürst attributes "
            "to Origen)",
            " Fürst for his part characterizes Origen's own position as a "
            "'kompatibilistischer Libertarismus' — his own coinage, chapter heading VI.4, "
            "p. 282.",
        ),
    ),
    "synthesis_frede2011_ch6_platonist_peripatetic_criticisms": (
        (
            "Frede concludes (p. 100, and Conclusion p. 177-178): Alexander 'is the only "
            "major ancient philosopher' whose conception is basically flawed, and 'it is "
            "in Alexander that we find the ancestor of the notion' of free will criticized "
            "by Ryle, Williams, and Frede",
            "Frede concludes (p. 100, and Conclusion p. 177-178) that Alexander's "
            "conception is basically flawed — a compressed paraphrase, not a verbatim "
            "quotation — and that 'it is in Alexander that we find the ancestor of the "
            "notion that to have a free will is to be able… to choose between doing A and "
            "doing B' (p. 99-100), the notion of free will criticized by Ryle, Williams, "
            "and Frede",
        ),
    ),
    "person_hippolytus_rome_d235": (
        # tag: "the description gives 'Adv. Math. V, 50-105' while amand_note_on_copying
        #   gives 'Adv. Math. V.37-105' … at least one is imprecise".  The French prose
        #   was reduced to the book number on 2026-08-14; the English was not.
        (
            "a near-textual transcription of Sextus Empiricus Adv. Math. V, 50-105 "
            "(with poor personal supplements)",
            "a near-textual transcription of Sextus Empiricus Adv. Math. V "
            "(with poor personal supplements)",
        ),
    ),
    "work_maximus_tyre_dissertation_13": (
        # tag: "The claimed Hobein-13 = Dübner-19 equivalence is not confirmable".  The
        #   label was fixed on 2026-08-14; metadata.description_en was not.
        (
            "Dissertation 13 (Hobein numbering) = 19 (Dübner) of Maximus of Tyre.",
            "Dissertation 13 (Hobein numbering) of Maximus of Tyre.",
        ),
    ),
    "synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate": (
        (
            "Synthesis of ch. 18 (Bonazzi):",
            "Synthesis of ch. 18 (Bonazzi, pp. 283-293):",
        ),
    ),
    "synthesis_amand1945_cicero_ch2i_cadre": (
        # tag: "The node lists the possible source as 'Antiochus of Ascalon OR
        #   Posidonius'; Amand's candidates (following Lörcher 1907) are
        #   Clitomachus/Antiochus".  The French prose was corrected on 2026-08-14; the
        #   English metadata still carried the rejected pairing.
        (
            "probably from Antiochus of Ascalon or Posidonius;",
            "probably from Clitomachus or Antiochus of Ascalon — the candidates Amand "
            "retains, following Lörcher 1907;",
        ),
    ),
}

LABEL_REWRITES: dict[str, tuple[str, str]] = {
    # §6.3 label-level residue: the tag rejects the conflation of Alexander's
    # consequences-for-motivation argument with the ἀργὸς λόγος, and the node's own
    # verified_reference assigns the ἀργὸς λόγος proper to Cicero and Origen instead.
    "argument_lazy_argument_alex": (
        "Lazy Argument (Argos Logos) in Alexander",
        "Consequences-for-Motivation Argument (Alexander, De Fato 11 — not the argos logos)",
    ),
    # tag: "The label presents «αἴτιον οὐκ ἀναγκαστικόν» as if it were Alexander's own
    # technical term. The metadata itself admits this is a modern back-translation
    # unattested in TLG, but the label/heading still d[oes]".
    "concept_non_necessitating_cause_alex": (
        "Non-Necessitating Cause (αἴτιον οὐκ ἀναγκαστικόν)",
        "Non-Necessitating Cause (modern rendering: αἴτιον οὐκ ἀναγκαστικόν — not Alexander's own term)",
    ),
}

# Nodes whose description still carries a curator bracket of a shape the 2026-08-14
# sweep did not target.  The applier strips every bracket introduced by one of
# BRACKET_MARKERS and appends it verbatim to `metadata.verification_notes`.
BRACKET_NODES: tuple[str, ...] = (
    "argument_anselms_necessity_of_the_past_f7947dab",  # [Vérifié 2026-08-02 : …]
    "argument_aquinass_intellectualism_f0058bf9",  # [Correction 2026-08-02 : …]
    "argument_civilization_alex",  # [Greek removed: …]
    "argument_gersonides_limited_omniscience_s9t0u1v2",  # [Correction 2026-08-02 : …]
    "argument_human_constitution_alex",  # [Bruns page…], [The node previously…]
    "argument_moral_assessment_alex",  # [Précision philologique 2026-08-03 : …]
    "argument_pascals_wager_and_voluntarism_4519ad75",  # [Correction 2026-08-02 : …]
)

BRACKET_MARKERS: tuple[str, ...] = (
    "[Vérifié",
    "[Correction 20",
    "[Précision",
    "[Greek removed",
    "[Bruns page",
    "[The node previously",
)

# The two nodes whose description repeats byte-identical paragraph blocks (an
# extraction artifact predating this sweep).  Deduplication keeps the first
# occurrence of each block, in order.
DEDUPE_BLOCKS: tuple[str, ...] = (
    "argument_civilization_alex",
    "argument_human_constitution_alex",
)

# NOT a bracket move: `argument_cafma_framework_5a7b9e12.attribution_review` matches a
# "[Vérif." grep, but the string there is a *mention* ("This node carried no [Vérif.]
# note but was flagged uncertain"), not a tag, and the first-person `RESOLVED
# 2026-08-03 (adjudication des 85 « incertains » …)` stamp is a graph-wide convention
# on that metadata field. Left untouched deliberately.

# ---------------------------------------------------------------------------
# 4. The Alcinous escalation
# ---------------------------------------------------------------------------
# Evidence (all re-verified 2026-08-16):
#  * `scripts/tlg_search.py` on 'ἀπεσκληκέναι τὰ γόνατα αὐτοῦ δίκην καμήλου' →
#    TLG1398 (Hegesippus), TLG2018 (Eusebius, HE II.23), TLG3045 (Syncellus);
#    on 'ἦσαν δὲ γνῶμαι διάφοροι ἐν τῇ περιτομῇ' → TLG2018 (Eusebius, HE IV.22);
#    on 'Μακάριοι οἱ ὀφθαλμοὶ ὑμῶν οἱ βλέποντες' → TLG1398 and TLG4040 (Photius,
#    Bibl. cod. 232, Stephanus Gobarus) — a combination found only in the
#    Hegesippus fragment collection, TLG 1398.
#  * `data/audit/primary_wave/urn_fix_changelog.jsonl` records the node's original
#    CTS URN as `urn:cts:greekLit:tlg1398:passage1` — tlg1398 IS Hegesippus.
#  * `data/corpus/manifest.jsonl` shows the ingest bug: the work row
#    `urn_cts_greeklit_tlg0720_tlg001` ("Alcinous, Handbook of Platonism") has
#    `source: "scaife:urn:cts:greekLit:tlg1398"` — the Alcinous shelf was filled
#    from the Hegesippus URN.
# No correct Alcinous passage node exists elsewhere in the graph, and the node is
# the sole referent of one row of `data/corpus/citations.jsonl`, so it is relabelled
# truthfully rather than deleted; the two edges that assert the false attribution
# are removed.
ALCINOUS_NODE_ID = "passage_alcin_alcinous_untitled_full_text"

ALCINOUS_NODE_FIELDS: dict = {
    "label": (
        "Hegesippus, Hypomnemata (fragments ap. Eusebius, HE II.23 / III.32 / IV.22 "
        "and ap. Photius) — mis-ingested under Alcinous"
    ),
    "school": None,
    "period": "Roman Imperial",
}

ALCINOUS_METADATA_OPS: tuple[dict, ...] = (
    {"op": "set", "key": "author", "value": "Hegesippus"},
    {"op": "set", "key": "school", "value": None},
    {
        "op": "set",
        "key": "work_title",
        "value": "Hypomnemata (fragments, ed. as TLG 1398)",
    },
    {"op": "set", "key": "canonical_ref", "value": None},
    {"op": "set", "key": "work_canonical_id", "value": "urn:cts:greekLit:tlg1398"},
    {"op": "set", "key": "doxographical_source", "value": None},
    {"op": "set", "key": "doxographical_confidence", "value": None},
    {"op": "set", "key": "attestation_type", "value": "fragment_collection"},
    {
        "op": "set",
        "key": "cts_urn_note",
        "value": (
            "Original value was urn:cts:greekLit:tlg1398:passage1 (Hegesippus); it was "
            "cleared as a fake placeholder during the primary-source wave, after which "
            "the node was left filed under Alcinous. tlg1398 is the correct author "
            "number; no edition locus is known for this extraction."
        ),
    },
    {
        "op": "set",
        "key": "mislabel_correction_2026_08_16",
        "value": (
            "This node was labelled 'Alcinous, Handbook of Platonism (Didaskalikos), "
            "Didasc. 1' with work_canonical_id urn:cts:greekLit:tlg0720.tlg001. Its "
            "8,218-character Greek payload is in fact the Hegesippus fragment "
            "collection (TLG 1398): the martyrdom of Symeon son of Clopas under Trajan "
            "and the consular Atticus (= Eusebius, HE III.32), the account of James the "
            "Just (= Eusebius, HE II.23, incl. 'ἀπεσκληκέναι τὰ γόνατα αὐτοῦ δίκην "
            "καμήλου'), the list of Jewish sects (= Eusebius, HE IV.22, 'ἦσαν δὲ γνῶμαι "
            "διάφοροι ἐν τῇ περιτομῇ'), and the fragment transmitted by Photius from "
            "Stephanus Gobarus ('Μακάριοι οἱ ὀφθαλμοὶ ὑμῶν οἱ βλέποντες'). Verified "
            "2026-08-16 with scripts/tlg_search.py against TLG1398, TLG2018 and "
            "TLG4040. Root cause: data/corpus/manifest.jsonl records the Alcinous work "
            "row urn_cts_greeklit_tlg0720_tlg001 as ingested from "
            "'scaife:urn:cts:greekLit:tlg1398'. The edges asserting authorship by "
            "Alcinous and membership in the Didaskalikos were deleted."
        ),
    },
    {
        "op": "set",
        "key": "needs_evidence_note",
        "value": (
            "Text quality: the stored payload is a lossy, line-shredded extraction with "
            "broken beta-code diacritics (e.g. '*̓ιάκωβος', 'τινε\\ς') and dropped words; "
            "it must not be quoted. Re-ingest from a critical edition (Eusebius, HE, "
            "GCS 9 Schwartz, or the Hegesippus fragments) before any use. The node id "
            "still carries the legacy 'alcin' prefix because "
            "data/corpus/citations.jsonl and the corpus passage row reference it."
        ),
    },
)

ALCINOUS_DELETE_EDGE_IDS: tuple[str, ...] = (
    "75cb6e7d-eca1-4409-becd-4f7247ccaaef",  # -authored_by-> person_alcinous_2c_ce
    "256726d2-1fdc-419b-bd7a-09cd1778428d",  # -part_of-> work_didaskalikos_alcinous_2nd_ce_q7r8s9t0
)

# ---------------------------------------------------------------------------
# 5. Greek gate allowlist
# ---------------------------------------------------------------------------
# Both runs are byte-identical to their committed text and were re-confirmed
# against the local TLG E corpus with `scripts/tlg_search.py` on 2026-08-16.
GREEK_ALLOWLIST_ADDITIONS: dict[str, tuple[dict, ...]] = {
    "concept_axia_biblos_tou_theou_origen_amand1945": (
        {
            "hash": "076cbcdc1b8b6830",
            "excerpt": "τὰ σημεῖα τοῦ θεοῦ",
            "source": (
                "Origène, Philocalie 23.20 (= Commentaire sur la Genèse III) : "
                "«…ἀναγινώσκειν τὰ σημεῖα τοῦ θεοῦ» — attesté verbatim dans le TLG E "
                "(TLG2042 Origenes, 3 occurrences ; vérifié via scripts/tlg_search.py "
                "le 2026-08-16). Absent du corpus local ingéré, qui ne contient pas ce "
                "chapitre de la Philocalie ; provenance enregistrée pour lever le gate "
                "— aucune fabrication. Cf. Amand 1945, p. 315-316."
            ),
        },
    ),
    "concept_inner_freedom_alex": (
        {
            "hash": "bab1627d58b40847",
            "excerpt": (
                "ἐνταῦθα λῃσταὶ καὶ κλέπται καὶ δικαστήρια καὶ οἱ καλούμενοι τύραννοι "
                "δοκοῦντες ἔχειν τινὰ ἐφ' ἡμῖν ἐξουσίαν διὰ τὸ σωμάτ"
            ),
            "source": (
                "Épictète, Dissertationes I.9 (le nœud cite I.9.12-17), éd. Schenkl, "
                "Teubner — attesté verbatim dans le TLG E (TLG0557, hit unique ; "
                "vérifié via scripts/tlg_search.py le 2026-08-16). Le corpus local "
                "contient les Discourses mais pas cette section ; provenance "
                "enregistrée pour lever le gate — aucune fabrication."
            ),
        },
    ),
}
