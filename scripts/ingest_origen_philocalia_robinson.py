"""Ingestion de la Philocalie d'Origène — chapitre 23 (antifatalisme) prioritaire.

Source : Robinson, J. Armitage. *The Philocalia of Origen*. Cambridge University Press, 1893.
URL djvu.txt : https://archive.org/download/philocalia-of-origen-1893/Philocalia%20of%20Origen%2C%201893_djvu.txt
URL PDF     : https://archive.org/download/philocalia-of-origen-1893/Philocalia%20of%20Origen%2C%201893.pdf
URL backup  : https://archive.org/details/philocalia00origuoft (Robinson 1893 reprint)

Contexte scholarly :
  Amand 1945, p. 366 affirme que **Philocalia 23 ≈ PE VI.11 verbatim** — c'est la
  transmission canonique de l'antifatalisme origénien chez Eusèbe. Une fois ce script
  exécuté + l'ingestion PE VI.11 (commit 309cbfb7 + scripts/ingest_eusebius_pe11_*),
  on peut créer des edges `parallel_to` ou `cited_by` entre les passages parallèles.

État au 2026-05-16 :
  - PE VI.11 : ingéré (83 sections) ✓
  - Philocalia 23 : work-shell seulement (`work_origen_philocalia`), AUCUN passage
  - First1KGreek `tlg2042.tlg028` est en latin (Comm. Matth.), PAS la Philocalia
  - Source canonique grec : Robinson 1893 OCR archive.org (qualité ~70-80%, grec polytonique)

Workflow recommandé (à valider par Romain) :
  1. Romain télécharge Robinson 1893 djvu.txt (1.1 MB)
  2. Romain extrait manuellement les sections du chapitre 23 (10-20 sections estimées)
  3. Vérifier la qualité OCR section par section, marquer `contains_greek_to_verify: true`
  4. Optionnel: utiliser le PDF avec un OCR neural (Tesseract polytonic-grc, MaT 2.0, ou EasyOCR)
     pour ré-OCR de qualité supérieure → markdown dans `data/scholarly_sources/ocr/`

Pour l'instant, ce script :
  - DOCUMENTE le path de téléchargement
  - PRÉPARE la structure `passage_origen_philocalia_23_*` pour ingestion future
  - NE CRÉE PAS de passages (texte grec doit être verbatim humain-vérifié)

NE PAS EXÉCUTER sans extraction manuelle préalable du texte Robinson 1893.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
OCR_ROOT = Path(__file__).resolve().parent.parent / "data" / "scholarly_sources" / "ocr" / "patristic_2026_05_16"

ROBINSON_DJVU_URL = (
    "https://archive.org/download/philocalia-of-origen-1893/"
    "Philocalia%20of%20Origen%2C%201893_djvu.txt"
)
ROBINSON_PDF_URL = (
    "https://archive.org/download/philocalia-of-origen-1893/"
    "Philocalia%20of%20Origen%2C%201893.pdf"
)
ROBINSON_LOCAL_DJVU = OCR_ROOT / "philocalia_robinson_1893_djvu.txt"
ROBINSON_LOCAL_PDF = OCR_ROOT / "philocalia_robinson_1893.pdf"

WORK_ID = "work_origen_philocalia"
PERSON_ID = "person_origen"  # to verify in KG

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
CREATED_BY = "origen_philocalia_robinson_ingestion_2026-05-16"


def fetch_djvu_only() -> Path:
    """Fetch the OCR djvu.txt (1.1 MB, lighter than full PDF 48 MB).

    Run this once manually before any ingestion. Romain then manually extracts
    Philocalia 23 sections from the djvu output (likely needs cleaning).
    """
    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    if ROBINSON_LOCAL_DJVU.exists() and ROBINSON_LOCAL_DJVU.stat().st_size > 100_000:
        print(f"  Already present: {ROBINSON_LOCAL_DJVU}")
        return ROBINSON_LOCAL_DJVU
    print(f"  Fetching {ROBINSON_DJVU_URL}")
    with urllib.request.urlopen(ROBINSON_DJVU_URL, timeout=120) as resp:
        data = resp.read()
    ROBINSON_LOCAL_DJVU.write_bytes(data)
    print(f"  Saved {len(data):,} bytes → {ROBINSON_LOCAL_DJVU}")
    return ROBINSON_LOCAL_DJVU


def main() -> int:
    print("== ORIGEN PHILOCALIA INGESTION (PREP ONLY) ==")
    print("This script DOES NOT ingest passages yet.")
    print()
    print("Phase 1: Fetch djvu OCR locally (1.1 MB)")
    fetch_djvu_only()
    print()
    print("Phase 2: Manual extraction required.")
    print("  Locate Philocalia 23 section in djvu.txt (search 'CAP. XXIII' or similar).")
    print("  Clean OCR (greek polytonic ~70-80% accuracy expected).")
    print("  Write cleaned passages to a JSONL file.")
    print()
    print("Phase 3: Once verified, extend this script to:")
    print("  - Create passage_origen_philocalia_23_N nodes")
    print("  - Create part_of (→ work_origen_philocalia)")
    print("  - Create authored_by (→ person_origen)")
    print("  - Create parallel_to edges to passage_eusebius_praep_ev_6_11_N (Amand p.366)")
    print()
    print(f"PDF backup (48 MB, full scan): {ROBINSON_PDF_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
