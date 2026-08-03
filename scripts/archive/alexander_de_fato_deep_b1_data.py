"""Alexander De Fato deep-anchor batch B1 — passage-node metadata updates.

For 14 chapters that scholars repeatedly engage, we tag the existing
`passage_alex_fat_<n>` node with the modern scholars who anchor a thesis there.
This makes the passages discoverable via the modern-reception layer without
duplicating content. Each update is idempotent : ``apply_updates`` merges into
the existing metadata dictionary.
"""
from __future__ import annotations

from typing import Any

UPDATES: list[dict[str, Any]] = [
    # Ch. 11 — Argument from deliberation (bouleuesthai)
    {
        "id": "passage_alex_fat_11",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "frede_2011": "Ch. 6 — argument from deliberation cited as Alexander's central anti-Stoic move",
                "sharples_1983": "core libertarian thesis — Bruns 176-178",
                "guyomarc_h_2008": "definition of τὸ ἐφʼ ἡμῖν as δύναμις τῶν ἐναντίων",
            },
            "alex_de_fato_central_chapter": True,
        },
    },
    # Ch. 12 — Eph' hēmin: agent kyrios over doing and not-doing
    {
        "id": "passage_alex_fat_12",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "frede_2011": "Ch. 6 — kyrios formulation cited",
                "guyomarc_h_2008": "ch. on τὸ ἐφʼ ἡμῖν",
                "sharples_1983": "core text of agent-causation reading",
            },
            "alex_de_fato_central_chapter": True,
        },
    },
    # Ch. 13 — Tyche reinterpreted; common notion of eph' hēmin
    {
        "id": "passage_alex_fat_13",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "sharples_1983": "explicit philosophical commentary",
            },
        },
    },
    # Ch. 14 — Eph' hēmin = autexousion (identification)
    {
        "id": "passage_alex_fat_14",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "frede_2011": "Ch. 6 — Alexander's identification of eph'hēmin with autexousion",
                "amand_1945": "Livre I Ch. V — De fato 16-20 sequence (témoin n°2)",
            },
            "alex_de_fato_central_chapter": True,
        },
    },
    # Ch. 15 — 192,22ff: 'could have done otherwise in same circumstances'
    {
        "id": "passage_alex_fat_15",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "frede_2011": "p. 100 + Conclusion p. 177-178 — the '192,22ff' libertarian dead-end formulation",
                "bobzien_1998": "alleged anachronism criticised by Bobzien",
                "guyomarc_h_2008": "δύναμις τῶν ἐναντίων under same circumstances",
                "furst_2022": "Kap. III §3c — Alternativenoffenheit thesis",
            },
            "alex_de_fato_central_chapter": True,
            "modern_scholarship_flashpoint": "192,22ff is the locus classicus for the 'libertarian Alexander' debate (Sharples 1983 vs Bobzien 1998 vs Frede 2011)",
        },
    },
    # Ch. 16 — Stoic eph' hēmin doesn't survive determinism (carnéadien series)
    {
        "id": "passage_alex_fat_16",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "amand_1945": "Livre I Ch. V — De fato 16 = début du témoin n°2 (dossier carnéadien)",
            },
            "amand_witness_n2_start": True,
        },
    },
    # Ch. 17 — providence vs determinism
    {
        "id": "passage_alex_fat_17",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "amand_1945": "Livre I Ch. V — De fato 17 = témoin n°2 §2",
            },
            "amand_witness_n2_part": True,
        },
    },
    # Ch. 18 — Stoics themselves preserve to eleutheron / to autexousion
    {
        "id": "passage_alex_fat_18",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "amand_1945": "Livre I Ch. V — De fato 18 = témoin n°2 §3 ; Stoïciens se contredisent eux-mêmes",
            },
            "amand_witness_n2_part": True,
        },
    },
    # Ch. 19 — common preconceptions of justice
    {
        "id": "passage_alex_fat_19",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "amand_1945": "Livre I Ch. V — De fato 19 = témoin n°2 §4",
            },
            "amand_witness_n2_part": True,
        },
    },
    # Ch. 20 — agent as archē of his actions (end of témoin n°2)
    {
        "id": "passage_alex_fat_20",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "amand_1945": "Livre I Ch. V — De fato 20 = clôture du témoin n°2 (cinq chapitres 16-20)",
                "frede_2011": "Ch. 6 — agent-as-archē formulation",
            },
            "amand_witness_n2_end": True,
        },
    },
    # Ch. 26 — apophthegms / praise-blame
    {
        "id": "passage_alex_fat_26",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "zingano_2014": "Destrée 2014 ch. 13, p. 245-263 — argument §§ 26-29 sur 'agir autrement'",
                "furst_2022": "Kap. III §3c — argument standard 'le déterminisme abolit louange/blâme'",
            },
            "alex_de_fato_central_chapter": True,
            "zingano_2014_anchor": "start of the §§26-29 sequence",
        },
    },
    # Ch. 27 — hexis : virtues are 'up to us' through prior acts
    {
        "id": "passage_alex_fat_27",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "zingano_2014": "Destrée 2014 ch. 13 — argument §§ 26-29 sur acquisition du caractère",
            },
        },
    },
    # Ch. 28 — character / Stoic necessitarian inconsistency
    {
        "id": "passage_alex_fat_28",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "zingano_2014": "Destrée 2014 ch. 13 — argument §§ 26-29 ; distinction liability/possibility",
                "frede_2011": "Ch. 6 — chapter cited in 'XI, XIV, XXVIII, XXXVIII' list",
            },
            "alex_de_fato_central_chapter": True,
        },
    },
    # Ch. 29 — phronimos and character formation (end of Zingano sequence)
    {
        "id": "passage_alex_fat_29",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "zingano_2014": "Destrée 2014 ch. 13 — clôture de la sequence §§ 26-29 ; phronimos comme cas-limite",
            },
            "zingano_2014_anchor": "end of the §§26-29 sequence",
        },
    },
    # Ch. 38 — Stoic horme defence refuted (Frede 'XXXVIII')
    {
        "id": "passage_alex_fat_38",
        "metadata_updates": {
            "scholars_anchoring_here": {
                "frede_2011": "Ch. 6 — chapter cited in 'XI, XIV, XXVIII, XXXVIII' list",
            },
        },
    },
]
