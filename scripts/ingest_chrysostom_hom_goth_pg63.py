"""Ingestion de l'Homélie de Jean Chrysostome après le discours du prêtre Goth, ch. 6.

Source : Patrologia Graeca, vol. 63 (Migne, 1859), colonnes 500-510 approx.
URL djvu.txt : https://archive.org/download/patrologiae_cursus_completus_gr_vol_063/patrologiae_cursus_completus_gr_vol_063_djvu.txt
URL PDF      : https://archive.org/details/patrologiae_cursus_completus_gr_vol_063

Contexte scholarly :
  Témoin n°5 d'Amand 1945 — courte homélie après le discours du prêtre goth (CPG 4441.10).
  Le passage VI (= ch. 6 de l'homélie) reproduit l'argumentation antifatale standard
  qu'Amand identifie comme tradition carnéadienne via Eusèbe→Chrysostome.

État au 2026-05-16 :
  - PG 63 djvu.txt disponible archive.org (9.8 MB total, OCR grec polytonique ~60-75%)
  - Pas de TEI canonique connu pour cette homélie spécifique
  - Édition critique moderne : SC 188 (« Œuvres oratoires » t. III, Cerf 1972) — INACCESSIBLE
  - Édition Migne XIXe siècle hors copyright, sur archive.org

Workflow recommandé (à valider par Romain) :
  1. Télécharger PG 63 djvu.txt en local (data/scholarly_sources/ocr/patristic_2026_05_16/)
  2. Localiser l'homélie (colonnes Migne 499-510 environ — CPG 4441.10)
  3. OCR re-process avec Tesseract polytonic-grc OU MaT 2.0 OU EasyOCR pour qualité supérieure
  4. Verbatim humain-vérifier le chapitre 6 (courtest, ~3-5 paragraphes)
  5. Créer passages `passage_chrysostom_hom_goth_6_N` (paragraphe-level)
  6. Edges :
     - part_of → work à créer (`work_chrysostom_hom_goth_acti_in_exsilium`)
     - authored_by → person_john_chrysostom (vérifier ID exact)
  7. Ancrer le `argument_carneadean_*` Amand B1 témoin n°5 si applicable

NE PAS EXÉCUTER sans extraction manuelle préalable. Migne OCR brut = pas suffisant
pour académique-grade verbatim.

Pour télécharger l'OCR (1.1 MB djvu compressed = 9.8 MB raw) :
    python scripts/ingest_chrysostom_hom_goth_pg63.py --fetch-only
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OCR_ROOT = Path(__file__).resolve().parent.parent / "data" / "scholarly_sources" / "ocr" / "patristic_2026_05_16"

PG63_DJVU_URL = (
    "https://archive.org/download/patrologiae_cursus_completus_gr_vol_063/"
    "patrologiae_cursus_completus_gr_vol_063_djvu.txt"
)
PG63_LOCAL_DJVU = OCR_ROOT / "pg63_chrysostom_djvu.txt"

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "chrysostom_hom_goth_pg63_ingestion_2026-05-16"

# Approximate Migne column range for the homily (to verify on actual scan)
MIGNE_COL_RANGE = (499, 510)


def fetch_pg63_djvu() -> Path:
    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    if PG63_LOCAL_DJVU.exists() and PG63_LOCAL_DJVU.stat().st_size > 100_000:
        print(f"  Already present: {PG63_LOCAL_DJVU}")
        return PG63_LOCAL_DJVU
    print(f"  Fetching {PG63_DJVU_URL}")
    with urllib.request.urlopen(PG63_DJVU_URL, timeout=180) as resp:
        data = resp.read()
    PG63_LOCAL_DJVU.write_bytes(data)
    print(f"  Saved {len(data):,} bytes → {PG63_LOCAL_DJVU}")
    return PG63_LOCAL_DJVU


def main() -> int:
    if "--fetch-only" in sys.argv:
        fetch_pg63_djvu()
        return 0
    print("== CHRYSOSTOM HOMILY AFTER GOTH PRIEST (PG 63) — PREP ONLY ==")
    print("This script DOES NOT ingest passages yet.")
    print(f"Migne column range (approx): {MIGNE_COL_RANGE[0]}-{MIGNE_COL_RANGE[1]}")
    print()
    print("To fetch OCR locally: python scripts/ingest_chrysostom_hom_goth_pg63.py --fetch-only")
    print()
    print("Workflow once OCR fetched + cleaned :")
    print("  1. Locate homily VI (ch. 6) in djvu.txt")
    print("  2. Verbatim humain-vérifier le grec polytonique")
    print("  3. Create passages `passage_chrysostom_hom_goth_6_N`")
    print("  4. Create work + edges (see docstring)")
    print()
    print("Edition critique moderne (référence) : SC 188 (Cerf 1972)")
    print("Édition Migne XIXe siècle : domaine public")
    return 0


if __name__ == "__main__":
    sys.exit(main())
