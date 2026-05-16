"""[LEGACY / FALLBACK] Ingestion de Clément d'Alexandrie, Stromateis I.82-84 + II.11-12.

REMPLACÉ PAR : `scripts/ingest_clement_stromateis_tlg_local.py` (2026-05-16)
  → version locale critique TLG XML (Stählin GCS, perseus-grc2 re-encoding)
  → utilisez le script TLG en priorité. Ce script reste comme fallback documenté.

Sources :
  - PG 8 (Migne 1857) : Stromata Books I-IV
  - PG 9 (Migne 1857) : Stromata Books V-VIII

URLs djvu :
  - https://archive.org/download/patrologiae_cursus_completus_gr_vol_008_clemens_alexandrinus_1/patrologiae_cursus_completus_gr_vol_008_clemens_alexandrinus_1_djvu.txt
  - https://archive.org/download/patrologiae_cursus_completus_gr_vol_009_clemens_alexandrinus_2/patrologiae_cursus_completus_gr_vol_009_clemens_alexandrinus_2_djvu.txt

Édition critique moderne (référence) :
  Stählin, O. *Clemens Alexandrinus, Band 2: Stromata Buch I-VI*. GCS 15 (Leipzig 1906) — INACCESSIBLE
  Stählin/Früchtel, GCS 52 (2e éd. Berlin 1960) — INACCESSIBLE

Contexte scholarly :
  Anchors B9 — passages de Clément cités systématiquement par Amand et la critique
  patristique pour l'argument antifatalisme stoïcien :
    - Stromata I.82-84 (livre I, ch. 17.82.4 — 17.84.5) : critique de l'εἱμαρμένη
    - Stromata II.11-12 (livre II, ch. 11.51 — 12.55) : libre arbitre et conversion

État au 2026-05-16 :
  - First1KGreek N'A PAS les Stromata (manque tlg0555.tlg004)
  - PG 8 et PG 9 djvu.txt sur archive.org (qualité OCR grec polytonique ~60-75%)
  - Alternative : Bibliotheca Augustana possible mais à vérifier
  - Alternative : Sources Chrétiennes (SC 30, 38, 278, 463, 446) — INACCESSIBLES

Workflow recommandé (à valider par Romain) :
  1. Télécharger PG 8 (livres I-IV) en priorité — contient Strom. I et II
  2. Localiser :
     - Strom. I.82-84 (Migne PG 8, col. 884-892 approx — vérifier)
     - Strom. II.11-12 (Migne PG 8, col. 985-994 approx — vérifier)
  3. OCR re-process / verbatim humain-vérifier
  4. Créer 7+ passages atomiques (Strom I.82.1-4 + I.83.1-5 + I.84.1-4 + II.11.x + II.12.x)
  5. Edges :
     - part_of → work_clement_stromateis (vérifier ID dans KG)
     - authored_by → person_clement_alexandria (vérifier ID)
     - evidenced_by depuis pivots carnéadiens si pertinent

NE PAS EXÉCUTER sans extraction manuelle préalable.

Pour télécharger les OCR :
    python scripts/ingest_clement_stromateis_pg8_9.py --fetch-only
"""
from __future__ import annotations

import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OCR_ROOT = Path(__file__).resolve().parent.parent / "data" / "scholarly_sources" / "ocr" / "patristic_2026_05_16"

PG8_DJVU_URL = (
    "https://archive.org/download/patrologiae_cursus_completus_gr_vol_008_clemens_alexandrinus_1/"
    "patrologiae_cursus_completus_gr_vol_008_clemens_alexandrinus_1_djvu.txt"
)
PG9_DJVU_URL = (
    "https://archive.org/download/patrologiae_cursus_completus_gr_vol_009_clemens_alexandrinus_2/"
    "patrologiae_cursus_completus_gr_vol_009_clemens_alexandrinus_2_djvu.txt"
)
PG8_LOCAL = OCR_ROOT / "pg8_clement_djvu.txt"
PG9_LOCAL = OCR_ROOT / "pg9_clement_djvu.txt"


def fetch(url: str, dest: Path) -> Path:
    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100_000:
        print(f"  Already present: {dest}")
        return dest
    print(f"  Fetching {url}")
    with urllib.request.urlopen(url, timeout=180) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"  Saved {len(data):,} bytes → {dest}")
    return dest


def main() -> int:
    if "--fetch-only" in sys.argv:
        fetch(PG8_DJVU_URL, PG8_LOCAL)
        fetch(PG9_DJVU_URL, PG9_LOCAL)
        return 0
    print("== CLEMENT STROMATEIS I.82-84 + II.11-12 (PG 8) — PREP ONLY ==")
    print("Fetch: python scripts/ingest_clement_stromateis_pg8_9.py --fetch-only")
    print()
    print("Target passages :")
    print("  Strom. I.82.1 — I.84.5 (~ PG 8 cols 884-892)")
    print("  Strom. II.11 — II.12 (~ PG 8 cols 985-994)")
    print()
    print("PG 8 (livres I-IV) prioritaire, PG 9 (V-VIII) optionnel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
