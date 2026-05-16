"""Ingestion de Philon d'Alexandrie, *De Providentia* I.79-83 — édition Aucher 1826.

Source : Aucher (Mkrtich' Awgerean), J.-B. *Philonis Judaei Paralipomena Armena*.
         Venise : Lazare, 1826. Édition arménien + trad. latine.
URL archive.org : https://archive.org/details/PhiloParalipomenaArm
URL PDF (35 MB) : https://archive.org/download/PhiloParalipomenaArm/Philo_Paralipomena_Arm.pdf
URL djvu.txt    : https://archive.org/download/PhiloParalipomenaArm/Philo_Paralipomena_Arm_djvu.txt

Contexte scholarly :
  Témoin n°1 d'Amand 1945 — le **plus ancien témoin patristique** de l'argument
  antifatalisme reconstruit comme carnéadien. De Providentia I.79-83 expose le
  problème classique de la providence vs déterminisme astral.

**PROBLÈME CRITIQUE — GREC PERDU :**
  Le grec original de Philon, De Providentia est entièrement perdu. Seules subsistent :
    - L'arménien (Aucher 1826) — texte de référence
    - La traduction latine d'Aucher accompagnant l'arménien
    - Quelques fragments grecs cités par Eusèbe PE VIII.13-14 (à vérifier dans KG)
    - Traduction anglaise FH Colson, Loeb 9 (1941) — à chercher sur archive.org

État au 2026-05-16 :
  - Aucher 1826 OCR sur archive.org (djvu.txt 2.2 MB, mais OCR arménien classique ~50-70%)
  - Colson Loeb 9 (1941) à chercher — peut être hors copyright maintenant (US 1996 cutoff)
  - **FLAG STRICT** : `metadata.no_greek_available: true` sur tous les passages
  - Paraphrase EN + texte arménien + latin Aucher en parallel

Workflow recommandé (à valider par Romain) :
  1. Télécharger djvu.txt Aucher 1826 (2.2 MB)
  2. Localiser De Providentia I.79-83 (liber I, par. 79-83)
  3. **PAS de texte grec** — uniquement arménien + latin Aucher
  4. Optionnel : ajouter EN paraphrase depuis Colson Loeb 9 (si trouvé)
  5. Créer passages `passage_philo_de_providentia_1_79` ... `_83` avec :
     - `text_hye` (arménien) + `text_lat` (Aucher) + `text_en` (Colson)
     - **`metadata.no_greek_available: true`** strictement
     - `metadata.translation_chain: armenian (Aucher 1826) ← greek (lost)`
  6. Edges : part_of → work, authored_by → person_philo_alexandria, etc.

NE PAS EXÉCUTER sans :
  (a) localisation manuelle de Lib. I §79-83 dans le djvu
  (b) décision de Romain sur les types `text_*` à privilégier (EleutherIA n'a pas
      historiquement de field `text_hye` — il faudra utiliser `description` brut ou
      `metadata.text_armenian`)

Pour télécharger l'OCR :
    python scripts/ingest_philo_de_providentia_aucher.py --fetch-only
"""
from __future__ import annotations

import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OCR_ROOT = Path(__file__).resolve().parent.parent / "data" / "scholarly_sources" / "ocr" / "patristic_2026_05_16"

AUCHER_DJVU_URL = (
    "https://archive.org/download/PhiloParalipomenaArm/Philo_Paralipomena_Arm_djvu.txt"
)
AUCHER_PDF_URL = (
    "https://archive.org/download/PhiloParalipomenaArm/Philo_Paralipomena_Arm.pdf"
)
AUCHER_LOCAL_DJVU = OCR_ROOT / "philo_aucher_1826_djvu.txt"


def fetch_aucher_djvu() -> Path:
    OCR_ROOT.mkdir(parents=True, exist_ok=True)
    if AUCHER_LOCAL_DJVU.exists() and AUCHER_LOCAL_DJVU.stat().st_size > 100_000:
        print(f"  Already present: {AUCHER_LOCAL_DJVU}")
        return AUCHER_LOCAL_DJVU
    print(f"  Fetching {AUCHER_DJVU_URL}")
    with urllib.request.urlopen(AUCHER_DJVU_URL, timeout=180) as resp:
        data = resp.read()
    AUCHER_LOCAL_DJVU.write_bytes(data)
    print(f"  Saved {len(data):,} bytes → {AUCHER_LOCAL_DJVU}")
    return AUCHER_LOCAL_DJVU


def main() -> int:
    if "--fetch-only" in sys.argv:
        fetch_aucher_djvu()
        return 0
    print("== PHILO DE PROVIDENTIA I.79-83 (Aucher 1826) — PREP ONLY ==")
    print("⚠️  GREC ORIGINAL PERDU — seul arménien + latin Aucher disponibles.")
    print()
    print("Fetch: python scripts/ingest_philo_de_providentia_aucher.py --fetch-only")
    print()
    print("Workflow nécessite décision préalable de Romain sur :")
    print("  - Storage de texte non-grec (armenian + latin) dans le KG")
    print("  - Flag `metadata.no_greek_available: true` cohérent avec la spec")
    print("  - Source de l'EN paraphrase (Colson Loeb 9 1941 si dispo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
