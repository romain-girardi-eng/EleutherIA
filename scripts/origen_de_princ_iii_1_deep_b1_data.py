"""Origen De Princ III.1 deep batch B1 — UPDATES list.

Only one update : enrich the metadata of the already-existing
passage_origen_pa_3_1_3 to make it consistent with the shell convention
introduced by this batch (section_number, section_label, book, chapter,
philocalia_cts_urn). The verified Greek text and the existing description
are preserved (only metadata fields are merged, never overwritten when they
already carry the verbatim Junod text).

The English-translation variant passage_origen_pa_3_1_3_en is left
untouched (auto-translation lineage preserved).

No update on work_de_principiis_origen_230s_v2w3x4y5 — its rich Frede /
Furst metadata is already complete (verified above at audit step).
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    {
        "id": "passage_origen_pa_3_1_3",
        "metadata_updates": {
            "section_number": 3,
            "section_label": "Self-determining judgment (αὐτεξούσιος κρίσις) — distinction between external events and internal response (Epictetan)",
            "book": "III",
            "chapter": "1",
            "section": 3,
            "philocalia_cts_urn": "urn:cts:greekLit:tlg2042.tlg028:21.3",
            "philocalia_reference": "Philocalia 21.3",
            "source_quality": "greek_verified_sc226_junod",
            "shell_provenance": "origen_de_princ_iii_1_deep_b1_kept",
            "is_anchor_for_batch": "origen_de_princ_iii_1_deep_b1",
            "anchor_role": "preexisting_canonical_passage_iii_1_3",
            "editions_to_consult": [
                "Koetschau GCS 22 (Berlin 1913) — Greek/Latin critical text",
                "Crouzel-Simonetti SC 268 (Paris 1980) — French translation with critical apparatus",
                "Junod SC 226 (Paris 1976) — Philocalie 21-27 Greek text — used for the verified Greek above",
                "Butterworth (London 1936 ; Harper 1966 ; Notre Dame 2013) — English translation",
                "Behr (Oxford 2017) — new English translation with introduction",
                "Goergemanns-Karpp (Darmstadt 1976 ; 3rd ed. 1992) — German bilingual",
            ],
        },
    },
    {
        "id": "passage_origen_pa_3_1_3_en",
        "metadata_updates": {
            "section_number": 3,
            "section_label": "Self-determining judgment — English translation pair",
            "book": "III",
            "chapter": "1",
            "section": 3,
            "shell_provenance": "origen_de_princ_iii_1_deep_b1_kept",
            "anchor_role": "preexisting_canonical_passage_iii_1_3_en",
        },
    },
]
