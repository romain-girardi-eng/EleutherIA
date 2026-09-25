#!/usr/bin/env python3
"""Apply the follow-up of the C2 translation review. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c2_translation_followup.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c2_translation_followup.py --apply

Same mechanics as apply_2026_09_24_c2_misaligned_translations.py (same stamp, so a pair
reviewed in either batch is never touched twice).
"""

from scripts.apply_2026_09_24_c2_misaligned_translations import run
from scripts.data_2026_09_24_c2_translation_followup import DECISIONS, NOTES

if __name__ == "__main__":
    run(DECISIONS, NOTES, "c2_translation_followup",
        "c2 results_a (Jev same_content < 0.7) in works with confirmed batch defects; editor-voice synopses")
