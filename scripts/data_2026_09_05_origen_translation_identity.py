"""Three existing translations used in gold: identity, not new ancient prose.

The nodes already declare French and identify their published translations.
The corpus incorrectly inherited English/Greek language from old work IDs.
"""

CASES = [
    (
        "ae853539-5bf0-592e-9323-f4dad81d7fc8",
        "passage_origen_pa_3_1_5",
        "origen_principiis_sc268_fra",
        "De Princ. 3.1.5",
    ),
    (
        "5d4a53e1-3e27-5179-98b4-1aa1231218f3",
        "passage_origen_pa_3_1_6",
        "origen_principiis_sc268_fra",
        "De Princ. 3.1.6",
    ),
    (
        "481e3e44-0c73-54f3-9190-73f09e332def",
        "passage_origen_philocalia_23_1",
        "origen_philocalia_sc226_fra",
        "Philocalia 23.1",
    ),
]
MANIFESTS = {
    "origen_principiis_sc268_fra": {
        "title": "De Principiis III.1.5–6 — French translation",
        "edition": "H. Crouzel and M. Simonetti, Origène, Traité des principes, tome III, SC 268 (Cerf, 1980)",
        "source": "SC 268, book III, existing source-declared French translation; conventional loci III.1.5–6",
    },
    "origen_philocalia_sc226_fra": {
        "title": "Philocalia 23.1 — French translation",
        "edition": "É. Junod, Origène, Philocalie 21–27, SC 226 (Cerf, 1976)",
        "source": "SC 226 Junod 1976, existing source-declared French translation, Philocalia 23.1 (Comm. Gen. III excerpt)",
    },
}
