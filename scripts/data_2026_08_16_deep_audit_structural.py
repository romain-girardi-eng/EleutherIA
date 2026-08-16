#!/usr/bin/env python3
"""Data for ``apply_2026_08_16_deep_audit_structural.py``.

One ``#`` comment per operation, quoting the evidence *already in the data* that
justifies it. Nothing here encodes the model's own beliefs about ancient texts.

A deliberate exclusion: the elision-mark and NFC normalisation is applied to
``edges.jsonl`` only. ``nodes.jsonl`` carries the ancient Greek and Latin
payload, and although NFC is a canonical (loss-free) normalisation, rewriting
17,108 passages of critical-edition text is a corpus-level act that belongs to
its own reviewed wave, not to a structural audit. The node-side variance is
reported in the findings file instead.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Six edges carry ``target != target_id``.
#
# In-memory loaders (graphrag agents, semantic/rdf_export.py, services/snapshot.py)
# read ``target`` first; the recursive k-hop CTE in
# ``knowledge graph/src/eleutheria_kg/services/db_traversal.py`` reads ``target_id``.
# The two retrieval paths therefore return *different authorship* for the same
# scholarship. In each cluster ``target`` holds the post-correction value:
#
#   * scholar_djeranian_o — the node description names the exact article,
#     « Responsabilité morale et destin : une réponse possible chez Épictète à
#     l'objection anti-stoïcienne de Cicéron (De fato 39-45) », and the arguments
#     concerned carry cites_primary_source edges to passage_cic_fat_39 … _45.
#     The id slug "gourinat" is the stale pre-correction value.
#   * scholar_hall_sg — "Stuart George Hall … editor and translator of Melito of
#     Sardis, On Pascha and Fragments (Oxford Early Christian Texts, Clarendon
#     Press, 1979)". scholar_hall_c is Claire Hall (Origen), a different person.
#   * scholar_koch_i — Isabelle Koch, "studies on causality, providence, and the
#     Neoplatonic reception of free will", for « La causalité humaine : sur le De
#     fato d'Alexandre d'Aphrodise ».
#
# (edge_id, correct target, stale target_id, reason)
EDGE_FIELD_DIVERGENCE: list[tuple[str, str, str, str]] = [
    (
        "2fe09122-45fa-4611-9077-28fa8c206ed4",
        "scholar_djeranian_o",
        "scholar_gourinat_jean_baptiste",
        "D'Jeranian's node names the article; the argument cites De fato 39-45.",
    ),
    (
        "07ed26a7-e8d1-4d18-8234-7e118100d56c",
        "scholar_djeranian_o",
        "scholar_gourinat_jean_baptiste",
        "D'Jeranian's node names the article; the argument cites De fato 39-45.",
    ),
    (
        "6928636c-5811-4df5-8df7-f18ba57fc8a1",
        "scholar_djeranian_o",
        "scholar_gourinat_jean_baptiste",
        "authored_by for the article D'Jeranian's node description names verbatim.",
    ),
    (
        "e61f8cc0-5b24-4a07-b6e4-40f209248572",
        "scholar_koch_i",
        "scholar_guyomarc_h_g",
        "Koch is the author of « La causalité humaine : sur le De fato d'Alexandre d'Aphrodise ».",
    ),
    (
        "1093cf67-79e4-4068-8d29-2b9a6357d6bf",
        "scholar_koch_i",
        "scholar_guyomarc_h_g",
        "authored_by for the same Koch article.",
    ),
    (
        "2ab6cca0-2ce1-4698-9b28-ec28b7ff9c47",
        "scholar_hall_sg",
        "scholar_hall_c",
        "S.G. Hall edited/translated Melito, On Pascha and Fragments (OECT 1979); Claire Hall is a different scholar.",
    ),
]


# ---------------------------------------------------------------------------
# 2. 73 metadata pointers reference 9 node ids that no longer exist. Each stale
# id has exactly one surviving counterpart, verified field by field (same
# person / same title / same year / same verified_reference). These are
# leftovers from de-duplication waves that rewrote edges but not metadata.
METADATA_POINTER_FIELDS = (
    "scholar_id",
    "author_id",
    "scholarly_work_id",
    "publication",
)

METADATA_POINTER_REMAP: dict[str, str] = {
    # "Michael Frede (Berlin, 31 May 1940 – drowned near Itea, 11 Aug 2007)" — same person.
    "person_frede_michael_1940_2007": "scholar_frede_michael",
    # "Albrecht Dihle" — same person, id order inverted by a later wave.
    "scholar_dihle_albrecht": "scholar_albrecht_dihle",
    # "The Theory of Will in Classical Antiquity", Sather Classical Lectures 48, 1982.
    "pub_dihle_1982_theory_will": "pub_dihle_1982_theory_of_will",
    # Eliasson, "The Notion of That Which Depends on Us in Plotinus and Its
    # Background", Philosophia Antiqua 113, 2008.
    "scholarly_work_eliasson_2008_the_notion_of_that_which_depends_on_us_i": (
        "pub_eliasson_2008_notion_eph_hemin_plotinus"
    ),
    # Karamanolis, "The Philosophy of Early Christianity", 2nd ed., Routledge 2021.
    "scholarly_work_karamanolis_2021_the_philosophy_of_early_christianity": (
        "pub_karamanolis_2021_philosophy_early_christianity"
    ),
    # Sharples, « L'accident du déterminisme. Alexandre d'Aphrodise dans son
    # contexte historique », Les Études philosophiques, 2008.
    "scholarly_work_sharples_2008_l_accident_du_d_terminisme_alexandre_d_a": (
        "pub_sharples_2008_accident_determinisme"
    ),
    # Voelke, « L'idée de volonté dans le stoïcisme », PUF 1973.
    "scholarly_work_voelke_1973_l_id_e_de_volont_dans_le_sto_cisme": "pub_voelke_1973_idee_volonte",
    # Destrée, Salles & Zingano (eds.), "What is Up to Us?", 2014.
    "scholarly_work_destr_e_2014_what_is_up_to_us_studies_on_agency_and_r": (
        "pub_destree_salles_zingano_2014_what_is_up_to_us"
    ),
    # Blackson, "Epictetus, the Early Stoics, and Frede's Argument for the First
    # Notion of a Will", Rhizomata 2025.
    "pub_blackson_epictetus_frede_argument": (
        "scholarly_work_blackson_2025_epictetus_the_early_stoics_and_frede_s_a"
    ),
}


# ---------------------------------------------------------------------------
# 3. Confirmed duplicate clusters. ``proof`` re-checks the evidence at run time;
# if it no longer holds the merge is skipped rather than applied blind.
def _same_work_uuid(keep, drop, km, dm) -> bool:
    return bool(km.get("work_id")) and km.get("work_id") == dm.get("work_id")


def _declared_previous(keep, drop, km, dm) -> bool:
    # The survivor itself records that it replaced the loser.
    return km.get("previous_node_id") == (drop.get("node_id") or drop.get("id"))


def _same_bibtex_key(keep, drop, km, dm) -> bool:
    return bool(km.get("bibtex_key")) and km.get("bibtex_key") == dm.get("bibtex_key")


def _identical_description(keep, drop, km, dm) -> bool:
    return (keep.get("description") or "").strip() == (
        drop.get("description") or ""
    ).strip()


def _merge_declared_in_metadata(keep, drop, km, dm) -> bool:
    # keep.metadata literally records that drop "was merged into this canonical entry".
    drop_id = drop.get("node_id") or drop.get("id")
    return any(
        drop_id in str(v) and "merged into this canonical entry" in str(v)
        for v in km.values()
    )


def _same_scholar_and_pages(keep, drop, km, dm) -> bool:
    return (
        km.get("scholar_id") == dm.get("scholar_id")
        and bool(km.get("scholar_id"))
        and km.get("page_range") == dm.get("page_range")
    )


def _same_scholar(keep, drop, km, dm) -> bool:
    return bool(km.get("scholar_id")) and km.get("scholar_id") == dm.get("scholar_id")


NODE_MERGES: list[dict] = [
    # -- Melito SC 31: a 2026-05-16 rename wave created the new node and left the
    # old one behind. Same metadata.work_id UUID d36f61c9-…, same run_id, same
    # page_index passage UUID f067ea48-…, and the survivor declares
    # previous_node_id = sc31_melito_peri_pascha_iv. Both carried 5 edges, so the
    # same SC 31 work was counted twice in the 242-work catalogue.
    {
        "keep": "passage_eusebius_he_iv_26_melito_fr_iv",
        "drop": "sc31_melito_peri_pascha_iv",
        "proof": _declared_previous,
        "port_meta": ["citation_verdict", "citation_verified", "verified_reference"],
        "reason": "same work_id UUID and run_id; survivor declares previous_node_id = the dropped node",
    },
    # -- The same rename wave duplicated the work's two children as well; both
    # pairs have byte-identical descriptions.
    {
        "keep": "passage_eusebius_he_iv_26_melito_fr_iv_chap3",
        "drop": "sc31_melito_peri_pascha_iv_chap3",
        "proof": _identical_description,
        "port_meta": ["citation_verdict", "citation_verified", "verified_reference"],
        "reason": "byte-identical description; child of the duplicated SC 31 Melito work",
    },
    {
        "keep": "passage_eusebius_he_iv_26_melito_fr_iv_chap3_en",
        "drop": "sc31_melito_peri_pascha_iv_chap3_en",
        "proof": _identical_description,
        "port_meta": ["citation_verdict", "citation_verified", "verified_reference"],
        "reason": "byte-identical description; child of the duplicated SC 31 Melito work",
    },
    # -- Long, Stoic Studies 1996. The survivor's own metadata states: "Audit
    # 2026-05-16: duplicate pub_long_1996_stoic_studies (incorrectly listed
    # California UP) was merged into this canonical entry" — but the merge was
    # never executed. The dropped node holds the richer content (description 580
    # chars vs 13) and cited_in "Frede 2011, note 1, p. 184", both ported.
    {
        "keep": "scholarly_work_long_1996_stoic_studies",
        "drop": "pub_long_1996_stoic_studies",
        "proof": _merge_declared_in_metadata,
        "port_meta": ["cited_in", "place", "type"],
        "port_description": True,
        "reason": "merge declared in the survivor's own metadata on 2026-05-16 but never applied",
    },
    # -- Crouzel, Origène et la philosophie (Aubier 1962). Identical
    # bibtex_key "publication-1962-origene-et-la-philosophie": a hard duplicate-key
    # signal. The fork is purely a slugifier artefact (accent-stripped "orig_ne"
    # vs transliterated "origene"). The survivor has the 7 advanced_in edges; the
    # loser has the better-formatted publisher and blank-not-"UNKNOWN" doi/isbn.
    {
        "keep": "scholarly_work_crouzel_1962_origene_et_la_philosophie",
        "drop": "scholarly_work_crouzel_1962_orig_ne_et_la_philosophie",
        "proof": _same_bibtex_key,
        "port_meta_overwrite": ["publisher", "doi", "isbn"],
        "reason": "identical bibtex_key; id forked by accent-stripping vs transliteration",
    },
    # -- Dihle 1982, one claim ingested twice. Same scholar_id, same underlying
    # thesis (Greek philosophical theology: order/regularity/beauty vs the
    # Biblical creator acting from arbitrary will). The survivor carries the
    # structured_v2 premise array; the loser only a summary-file provenance.
    {
        "keep": "scholarly_argument_dihle_greek_philosophical_theology_v_0",
        "drop": "scholarly_argument_dihle_greek_vs_biblical_cosmology_an_4",
        "proof": _same_scholar,
        "port_meta": ["page_range", "supporting_evidence", "verified_reference"],
        "reason": "same scholar_id and same Dihle 1982 thesis, ingested twice",
    },
    # -- Double 1994, the same claim ingested twice from the SAME file in two OCR
    # passes: "R. Double-How to Frame the Free Will Problem .md" and the
    # "…_OCR.md" variant. Same scholar_id, same page_range 149-150.
    {
        "keep": "scholarly_argument_double_methodological_reframing_of_fr_1",
        "drop": "scholarly_argument_double_taxonomy_of_free_will_position_1",
        "proof": _same_scholar_and_pages,
        "port_meta": ["supporting_evidence", "verified_reference"],
        "reason": "same scholar_id and page_range; the two source_file values are one file in two OCR passes",
    },
]


# ---------------------------------------------------------------------------
# 5. Scraped navigation chrome found in place of passage text.
CHROME_MARKERS = (
    "The Latin Library",
    "The Classics Page",
    "Perseus Digital Library",
)


# ---------------------------------------------------------------------------
# 8. Id prefixes that contradict the node's own type.
#
# ``scholar_position_*`` (22 nodes) are typed ``argument`` and are structurally
# arguments: they carry premises, 23 cites_primary_source, 22 created_by, plus
# advanced_in / agrees_with / opposes edges. Retyping them to ``position`` would
# break domain/range on every one of those relations (``position`` is not an
# allowed source type for any of them), so the TYPE is right and the ID is
# wrong. Renaming ``scholar_`` -> ``scholarly_`` removes the collision with the
# person-id namespace (``scholar_*`` is otherwise exclusively persons) while
# keeping the readable "position" sense. The old id is preserved in
# ``metadata.previous_node_id``.
_SCHOLAR_POSITION_SLUGS = (
    "andresen_justin_middle_platonist",
    "bobzien_no_free_will_problem_ancients",
    "brennan_stoic_emotions_beliefs",
    "dihle_will_christian_innovation",
    "edwards_origen_anti_platonist",
    "frankfurt_pap_false",
    "frede_will_originates_epictetus",
    "furley_epicurus_swerve_indirect",
    "gill_structured_self_stoicism",
    "hadot_philosophy_as_practice",
    "hankinson_stoic_causation_compatibilist",
    "inwood_stoic_action_theory",
    "kahn_will_emerges_seneca_epictetus",
    "kane_libertarian_self_forming",
    "karamanolis_early_christian_engagement",
    "long_sedley_epicurus_first_freewill",
    "rist_augustine_platonized_christian",
    "salles_chrysippus_frankfurt_style",
    "sharples_chrysippus_early_compatibilist",
    "sorabji_aristotle_indeterminist",
    "strawson_basic_argument",
    "van_inwagen_consequence_argument",
)

ID_RENAMES: dict[str, str] = {
    # A ``work`` node under a ``passage_`` prefix — the 2026-05-16 rename wave
    # moved the SC 31 Melito work to a passage-style id. Its two children stay
    # ``passage_*`` (they really are passages) and keep the same stem.
    "passage_eusebius_he_iv_26_melito_fr_iv": "work_eusebius_he_iv_26_melito_fr_iv",
    # The single ``argument_framework`` instance under an ``argument_`` prefix.
    "argument_cafma_framework_5a7b9e12": "framework_cafma_5a7b9e12",
    # The node whose label already declares the correction: "Hegesippus,
    # Hypomnemata (fragments ap. Eusebius, HE II.23 / III.32 / IV.22 and ap.
    # Photius) — mis-ingested under Alcinous". metadata.author = Hegesippus,
    # work_canonical_id = urn:cts:greekLit:tlg1398, TLG-verified 2026-08-16. Only
    # the id still said Alcinous.
    "passage_alcin_alcinous_untitled_full_text": "passage_hegesippus_hypomnemata_fragments",
}
ID_RENAMES.update(
    {
        f"scholar_position_{slug}": f"scholarly_position_{slug}"
        for slug in _SCHOLAR_POSITION_SLUGS
    }
)
