"""Philo of Alexandria, De Providentia I — Aucher 1822 Latin fallback ingestion.

PREFERRED SOURCE: SC 35bis Hadas-Lebel (Cerf 1973), accessible via Romain's
institutional library. This script is a DEFERRED FALLBACK to be used only
if SC 35bis remains unobtainable.

Reasons for deferral:
- The Greek original is entirely lost; only the Armenian survives.
- Aucher 1822 (`philonisjudaeis00judgoog` on archive.org) provides the canonical
  Armenian + Latin parallel printing but uses an antique paragraph numbering
  scheme. Modern citations follow Mras / Hadas-Lebel section numbering §79-83
  which has no one-to-one correspondence with Aucher's pagination. Ingesting
  Aucher verbatim without collation against Mras would force either (a) a
  single continuous macro-passage with no Amand-grain anchoring, or (b) costly
  manual philological collation.
- SC 35bis already encodes Mras numbering, includes apparatus and a French
  parallel — the canonical scholarly path.

Until SC 35bis access is resolved, this script remains executable for a
last-resort fallback ingestion. It requires the explicit `--confirm-fallback`
flag to prevent accidental execution. See:
- ~/.claude/projects/.../memory/project_philo_de_providentia_pending.md
- docs/plans/2026-05-15-amand-integration-plan.md (witness n°1 entry)

Bibliographic metadata captured for the eventual SC 35bis ingestion:
- Hadas-Lebel, Mireille (ed./tr.), *Philon d'Alexandrie. De Providentia I-II*,
  Sources Chrétiennes 35bis (révision posthume), Paris, Cerf, 1973.
- bibtex_key target: ``hadas-lebel-1973-philon-de-providentia-sc35bis``

Aucher 1822 metadata (fallback only):
- Aucher, Jean-Baptiste (Awgerean, Mkrtich'), ed./tr. (1822). *Philonis
  Judaei Sermones tres hactenus inediti, I. et II. De providentia, III. De
  animalibus, ex Armena versione antiquissima ab ipso originali textu
  graeco ad verbum stricte exequuta, nunc primum in Latium fideliter
  translati per P. Jo. Baptistam Aucher.* Venezia: Lazare.
- archive.org volume: ``philonisjudaeis00judgoog``
- bibtex_key target: ``aucher-1822-philonis-judaei-sermones-tres``

When SC 35bis is obtained, a fresh `scripts/ingest_philo_de_providentia_sc35bis_local.py`
should be written instead (pattern: scripts/ingest_origen_philocalia_sc226_local.py).
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_ROOT = ROOT / "data" / "scholarly_sources" / "ocr" / "philo_de_providentia_aucher_1822"

AUCHER_VOLUME = "philonisjudaeis00judgoog"
AUCHER_DJVU_URL = (
    f"https://archive.org/download/{AUCHER_VOLUME}/{AUCHER_VOLUME}_djvu.txt"
)
AUCHER_PDF_URL = f"https://archive.org/download/{AUCHER_VOLUME}/{AUCHER_VOLUME}.pdf"
AUCHER_LOCAL_DJVU = OCR_ROOT / "source_djvu.txt"


def fetch_aucher_djvu() -> Path:
    """Download Aucher 1822 djvu OCR text for offline inspection."""
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


def ingest_fallback() -> int:
    """Last-resort fallback ingestion path. Requires --confirm-fallback flag.

    This function is intentionally left as a NotImplementedError so that
    fallback ingestion requires a deliberate authoring pass aligned with
    the eventual SC 35bis schema (Mras section numbers §79-83). When the
    user is ready to accept Aucher Latin as a permanent record:

    1. Fetch the djvu via fetch_aucher_djvu().
    2. Manually collate Aucher's paragraph divisions against Mras §79-83
       (this is the philological work that cannot be automated cleanly).
    3. Create passage nodes with id pattern `passage_philo_de_providentia_1_79..83`
       carrying:
         - text_lat: verbatim Aucher Latin
         - description: brief English paraphrase (no fabricated Greek)
         - passage_role: "translation"
         - language: "latin_aucher_1822"
         - metadata.no_greek_available: true
         - metadata.translation_chain: "Armenian (Aucher 1822) ← Greek (lost)"
         - metadata.requires_sc35bis_replacement: true
         - period: "Hellenistic" (Philo's period)
         - part_of → work_philo_de_providentia
         - authored_by → person_philo_alexandria_a1b2c3d4
    4. Create evidenced_by edges from the 4 Amand B3 witness-n°1 arguments
       (argument_philo_de_providentia_*_amand1945) to the new passages.
    5. Run SHACL invariants + FULL + kg test suite.

    Run with: ``python scripts/ingest_philo_de_providentia_aucher.py --confirm-fallback``
    """
    raise NotImplementedError(
        "Aucher 1822 ingestion deferred. Preferred source is SC 35bis Hadas-Lebel "
        "(awaiting access via Romain's institutional library). See module docstring "
        "and memory project_philo_de_providentia_pending for the path forward."
    )


def main(argv: list[str]) -> int:
    if "--fetch-only" in argv:
        fetch_aucher_djvu()
        return 0
    if "--confirm-fallback" in argv:
        return ingest_fallback()
    print("== Philo De Providentia I.79-83 — Aucher 1822 fallback ==")
    print()
    print("Preferred source: SC 35bis Hadas-Lebel (deferred until accessible).")
    print()
    print("Available modes:")
    print("  --fetch-only         Download Aucher 1822 djvu OCR to data/scholarly_sources/")
    print("  --confirm-fallback   Run the fallback ingestion (currently raises")
    print("                       NotImplementedError pending manual Mras collation).")
    print()
    print("See module docstring for full rationale and Mras collation guidance.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
