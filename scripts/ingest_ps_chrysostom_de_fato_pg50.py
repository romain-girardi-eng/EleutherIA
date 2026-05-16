"""Ingestion de Pseudo-Chrysostome, De Fato et Providentia V — PG 50, 765-768.

Source : Patrologia Graeca, vol. 50 (Migne, 1859), colonnes 765-768.
URL djvu.txt : https://archive.org/download/patrologiae_cursus_completus_gr_vol_050/patrologiae_cursus_completus_gr_vol_050_djvu.txt
URL PDF      : https://archive.org/details/patrologiae_cursus_completus_gr_vol_050

Contexte scholarly :
  Témoin n°6 d'Amand 1945 — *De Fato et Providentia* (CPG 4366), 6 sermons pseudo-
  chrysostomiens. Le sermon V (PG 50, 765-768) reproduit verbatim plusieurs arguments
  d'Eusèbe PE VI.6 (témoin n°4) selon Amand p. 367-372.

État au 2026-05-16 :
  - PG 50 djvu.txt disponible archive.org (4.7 MB total)
  - Édition critique moderne : aucune ; Migne 1859 reste l'édition de référence
  - Court (~3 colonnes Migne, ~1500-2000 mots grec)
  - Auteur : anonyme, IVe-Ve siècles, école antiochienne

Workflow recommandé (à valider par Romain) :
  1. Télécharger PG 50 djvu.txt en local
  2. Localiser le sermon V dans le bloc « De Fato et Providentia » (cols 749-774)
  3. OCR re-process si nécessaire (Tesseract polytonic-grc)
  4. Verbatim humain-vérifier
  5. Créer work `work_pseudo_chrysostom_de_fato_et_providentia`
  6. Créer person `person_pseudo_chrysostom_de_fato` (anonyme 4-5e s.)
  7. Créer 6 sermons comme passages (ou sub-works) — focus sur sermon V
  8. Ancrer témoin n°6 Amand B1 via `evidenced_by` depuis pivots carnéadiens
     vers `passage_pseudo_chrysostom_de_fato_5_*`

NE PAS EXÉCUTER sans extraction manuelle préalable.

Pour télécharger l'OCR :
    python scripts/ingest_ps_chrysostom_de_fato_pg50.py --fetch-only
"""
from __future__ import annotations

import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OCR_ROOT = Path(__file__).resolve().parent.parent / "data" / "scholarly_sources" / "ocr" / "patristic_2026_05_16"

PG50_DJVU_URL = (
    "https://archive.org/download/patrologiae_cursus_completus_gr_vol_050/"
    "patrologiae_cursus_completus_gr_vol_050_djvu.txt"
)
PG50_LOCAL_DJVU = OCR_ROOT / "pg50_ps_chrysostom_djvu.txt"

CREATED_BY = "ps_chrysostom_de_fato_pg50_ingestion_2026-05-16"
MIGNE_COL_RANGE_FULL = (749, 774)  # De Fato et Providentia, 6 sermons
MIGNE_COL_RANGE_SERMON_V = (765, 768)  # specifically


def fetch_pg50_djvu() -> Path:
    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    if PG50_LOCAL_DJVU.exists() and PG50_LOCAL_DJVU.stat().st_size > 100_000:
        print(f"  Already present: {PG50_LOCAL_DJVU}")
        return PG50_LOCAL_DJVU
    print(f"  Fetching {PG50_DJVU_URL}")
    with urllib.request.urlopen(PG50_DJVU_URL, timeout=180) as resp:
        data = resp.read()
    PG50_LOCAL_DJVU.write_bytes(data)
    print(f"  Saved {len(data):,} bytes → {PG50_LOCAL_DJVU}")
    return PG50_LOCAL_DJVU


def main() -> int:
    if "--fetch-only" in sys.argv:
        fetch_pg50_djvu()
        return 0
    print("== PSEUDO-CHRYSOSTOM DE FATO ET PROVIDENTIA V (PG 50) — PREP ONLY ==")
    print(f"Migne sermon V col. {MIGNE_COL_RANGE_SERMON_V[0]}-{MIGNE_COL_RANGE_SERMON_V[1]}")
    print(f"Full De Fato et Providentia col. {MIGNE_COL_RANGE_FULL[0]}-{MIGNE_COL_RANGE_FULL[1]}")
    print()
    print("Fetch: python scripts/ingest_ps_chrysostom_de_fato_pg50.py --fetch-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
