"""Evidence-bound edition decisions; no ancient wording is generated."""

STAMP = "augustine_dihle_adjudication_2026_09_05"
# Augustinus.it labels this work PL 32. The University of Fribourg catalogue
# identifies the edition as Migne, Paris 1841, and the work as CPL 260.
DLA_AUTHORITY = "https://bkv.unifr.ch/fr/works/cpl-260"
DLA_EDITION = "Augustine, De libero arbitrio, PL 32 (Migne, Paris 1841); transcription Augustinus.it"
DLA_HASHES = {
    1: "ed2897d82bb5fdea6212f965157c6b7a4a6d5e93f44e9850e904a214ccdfad0f",
    2: "a02a47976bf2e411aab3f75888d2f3f47c8f846c5e7ca2c26f30100b549879a4",
    3: "9d73de54a70dc33a472415320eb5f0236f50a62dd5fb0581c39a517c7bfdf5d9",
}
# Hoffmann's CSEL 40 edition is declared in the pinned OGL TEI sourceDesc.
CIV_SOURCE = {
    "file": "stoa0040.stoa003.opp-lat3.xml",
    "sha256": "ee65f8941721f4ccb9425ea90412581334c075238102986c9978fda503a716f4",
    "url": "https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev/a930441f99e57a62724991a91d102bf2053635c7/data/stoa0040/stoa003/stoa0040.stoa003.opp-lat3.xml",
    "edition": "E. Hoffmann, De civitate Dei, CSEL 40.1–2 (1899–1900); Open Greek and Latin",
    "urn": "urn:cts:latinLit:stoa0040.stoa003.opp-lat3",
    "manifest": "augustine_civitate_hoffmann_selected_lat",
    "license": "CC-BY-SA-4.0",
}
# Visual reading of PDF page 75: printed page 68, chapter IV opening. The
# existing quotation is confirmed there; old 3054... values are file offsets.
DIHLE_NODE = "scholarly_argument_dihle_greek_concept_of_will_0"
DIHLE_PAGE = "68"
