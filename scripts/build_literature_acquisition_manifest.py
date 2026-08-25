#!/usr/bin/env python3
"""Build the deterministic manifest for every local literature artifact.

The archive previously contained dozens of PDFs/EPUBs with no machine-readable
fingerprint or manifestation identity.  This script covers every top-level PDF
and EPUB, records scan/OCR relationships, and refuses uncurated files.  It never
extracts or republishes copyrighted text.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/literature_acquisition"
MANIFEST = ARCHIVE / "manifest.jsonl"


def item(
    intellectual_object_id: str,
    title: str,
    creators: list[str],
    year: int,
    *,
    completeness: str = "full",
    role: str = "source_file",
    audit_status: str = "inventoried",
    scope: str = "context",
    derivative_of: str | None = None,
) -> dict[str, Any]:
    return {
        "intellectual_object_id": intellectual_object_id,
        "title": title,
        "creators": creators,
        "year_display": str(year),
        "content_completeness": completeness,
        "manifestation_role": role,
        "audit_status": audit_status,
        "scope": scope,
        "derivative_of": derivative_of,
    }


CURATION: dict[str, dict[str, Any]] = {
    "Fuerst_2019_Freedom_Key_Category_Origen_Adam14_TOC.pdf": item(
        "fuerst_2019_freedom_key_category_origen",
        "Freedom as a Key Category in Origen (table of contents only)",
        ["Alfons Fürst"], 2019, completeness="toc_only"
    ),
    "SAPERE28_Tatian_Rede_an_die_Griechen_2016_OA.pdf": item(
        "tatian_oratio_ad_graecos_sapere_2016",
        "Tatian, Oratio ad Graecos / Rede an die Griechen (SAPERE 28)",
        ["Tatian", "Jörg Trelenberg et al."], 2016, scope="core"
    ),
    "barclay_2020_grace.epub": item(
        "barclay_2020_paul_and_gift_grace",
        "Paul and the Power of Grace", ["John M. G. Barclay"], 2020
    ),
    "blowers_2016_maximus.pdf": item(
        "blowers_2016_maximus", "Maximus the Confessor", ["Paul M. Blowers"],
        2016, audit_status="deep_read_wave1", scope="core"
    ),
    "boys_stones_2018_platonist.pdf": item(
        "boys_stones_2018_platonist_philosophy", "Platonist Philosophy 80 BC to AD 250",
        ["George Boys-Stones"], 2018, audit_status="deep_read_wave1", scope="core"
    ),
    "brand_2013_evil.pdf": item(
        "brand_2013_evil", "Evil Within and Without", ["Matti Eklund Brand"], 2013
    ),
    "carter_2022_fatalism.pdf": item(
        "carter_fatalism_false_futures_author_manuscript",
        "Fatalism and False Futures in De Interpretatione 9", ["John Carter"],
        2024, role="author_manuscript", audit_status="deep_read_wave1", scope="core"
    ),
    "eastman_2017_person.epub": item(
        "eastman_2017_paul_and_person", "Paul and the Person", ["Susan Grove Eastman"], 2017
    ),
    "engberg_2023_paul_philosophy_TOC_sample.pdf": item(
        "engberg_2023_paul_and_philosophy", "Paul and Philosophy (sample)",
        ["David Engberg-Pedersen"], 2023, completeness="sample"
    ),
    "erasmus_luther_winter_discourse_free_will.pdf": item(
        "erasmus_luther_winter_discourse_free_will",
        "Discourse on Free Will", ["Desiderius Erasmus", "Martin Luther", "Ernst F. Winter"],
        1961, scope="reception"
    ),
    "frankfurt_1988_importance_what_we_care_about.pdf": item(
        "frankfurt_1988_importance_what_we_care_about",
        "The Importance of What We Care About", ["Harry G. Frankfurt"], 1988,
        scope="modern_context"
    ),
    "hadot_1992_citadelle_interieure.pdf": item(
        "hadot_1992_citadelle_interieure", "La citadelle intérieure", ["Pierre Hadot"], 1992,
        scope="core"
    ),
    "hildebrandt_2022_alexander_lazy_arguments.pdf": {
        **item(
            "hildebrandt_2022_alexander_lazy_arguments",
            "Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism",
            ["Ronja Hildebrandt"], 2022, role="source_file",
            audit_status="deep_read_wave1", scope="core"
        ),
        "manifestation_id": "hildebrandt_2022_spe15_pdf_pp25_44_eng",
        "doi": "10.12697/spe.2022.15.01",
        "journal": "Studia Philosophica Estonica",
        "volume": 15,
        "printed_page_range": {"start": 25, "end": 44},
        "pdf_page_range": {"start": 1, "end": 20},
        "page_map": "PDF page = printed page - 24",
        "access_status": "open_access",
        "access_url": "https://ojs.utlib.ee/index.php/spe/article/view/22849",
        "rights_statement": "© All Copyright Author",
        "license_status": "no_explicit_reuse_licence_archived",
        "reuse_status": "unverified_do_not_republish",
    },
    "kane_1998_significance_free_will.pdf": item(
        "kane_1998_significance_free_will", "The Significance of Free Will", ["Robert Kane"],
        1998, scope="modern_context"
    ),
    "kiel_adam24_DNB_TOC.pdf": item(
        "kiel_adam24", "Adamantius volume chapter 24 (table of contents only)",
        ["Unknown / catalog record"], 2019, completeness="toc_only"
    ),
    "kiel_review_oleary.pdf": item(
        "kiel_review_oleary", "Review concerning free will scholarship", ["Unknown reviewer"],
        2019, completeness="review_only", role="review"
    ),
    "klawans_2012_josephus.pdf": item(
        "klawans_2012_josephus", "Josephus and the Theologies of Ancient Judaism",
        ["Jonathan Klawans"], 2012, scope="core"
    ),
    "knobe_2003_intentional.pdf": item(
        "knobe_2003_intentional_action", "Intentional Action and Side Effects in Ordinary Language",
        ["Joshua Knobe"], 2003, scope="modern_context"
    ),
    "kobusch_adam28_DNB_TOC.pdf": item(
        "kobusch_adam28", "Adamantius volume chapter 28 (table of contents only)",
        ["Theo Kobusch"], 2019, completeness="toc_only"
    ),
    "kobusch_ifb_review.pdf": item(
        "kobusch_ifb_review", "Review of scholarship on freedom", ["Unknown reviewer"],
        2019, completeness="review_only", role="review"
    ),
    "long_sedley_1987_hellenistic_philosophers_vol2.pdf": {
        **item(
            "long_sedley_1987_hellenistic_philosophers_vol2",
            "The Hellenistic Philosophers, Volume 2: Greek and Latin Texts",
            ["A. A. Long", "D. N. Sedley"], 1987, completeness="full",
            role="source_scan", audit_status="deep_read_wave1", scope="core"
        ),
        "content_completeness_scope": "scholarly main content from title page through bibliography",
        "physical_completeness": "incomplete",
        "physically_missing": ["front cover", "preliminaries i-ii"],
        "intellectual_work_id": "scholarly_work_long_sedley_1987_hellenistic_philosophers",
        "intellectual_volume": 2,
        "visible_reprint_line_latest_year": 1998,
        "exact_local_printing_status": "unknown_not_inferred",
        "binding_status": "unknown_cover_absent",
        "isbn_10_hardback": "0521255627",
        "isbn_10_paperback": "0521275571",
        "page_map": "printed body page = PDF page - 8",
    },
    "maximus_adam35_DNB_TOC.pdf": item(
        "maximus_adam35", "Adamantius volume chapter 35 (table of contents only)",
        ["Unknown / catalog record"], 2019, completeness="toc_only"
    ),
    "mele_2006_free_will_and_luck.pdf": item(
        "mele_2006_free_will_and_luck", "Free Will and Luck", ["Alfred R. Mele"], 2006,
        scope="modern_context"
    ),
    "methodius_adam33_DNB_TOC.pdf": item(
        "methodius_adam33", "Adamantius volume chapter 33 (table of contents only)",
        ["Unknown / catalog record"], 2019, completeness="toc_only"
    ),
    "pereboom_2001_living_without_free_will.pdf": item(
        "pereboom_2001_living_without_free_will", "Living Without Free Will",
        ["Derk Pereboom"], 2001, scope="modern_context"
    ),
    "reid_2010_active_powers_haakonssen.pdf": item(
        "reid_2010_active_powers", "Essays on the Active Powers of Man",
        ["Thomas Reid", "Knud Haakonssen"], 2010, scope="reception"
    ),
    "sharples_1983_alexander_de_fato.pdf": item(
        "sharples_1983_alexander_de_fato", "Alexander of Aphrodisias: On Fate",
        ["R. W. Sharples"], 1983, role="source_scan", scope="core"
    ),
    "sharples_1983_alexander_de_fato_ocr.pdf": item(
        "sharples_1983_alexander_de_fato", "Alexander of Aphrodisias: On Fate (OCR derivative)",
        ["R. W. Sharples"], 1983, completeness="derivative", role="ocr_derivative",
        scope="core", derivative_of="sharples_1983_alexander_de_fato.pdf"
    ),
    "sorabji_1980_necessity_cause_blame.pdf": item(
        "sorabji_1980_necessity_cause_blame", "Necessity, Cause and Blame",
        ["Richard Sorabji"], 1980, role="source_scan", audit_status="deep_read_wave1", scope="core"
    ),
    "sorabji_1980_necessity_cause_blame_ocr.pdf": item(
        "sorabji_1980_necessity_cause_blame", "Necessity, Cause and Blame (OCR derivative)",
        ["Richard Sorabji"], 1980, completeness="derivative", role="ocr_derivative",
        audit_status="deep_read_wave1", scope="core",
        derivative_of="sorabji_1980_necessity_cause_blame.pdf"
    ),
    "spinoza_curley_1985_collected_works.epub": item(
        "spinoza_curley_1985_collected_works", "The Collected Works of Spinoza, Volume I",
        ["Baruch Spinoza", "Edwin Curley"], 1985, scope="reception"
    ),
    "sytsma_2018_dissertation_origen.pdf": item(
        "sytsma_2018_dissertation_origen", "Origen's Theory of Free Will and Universal Salvation",
        ["David Sytsma"], 2018, role="doctoral_dissertation", audit_status="deep_read_wave1", scope="core"
    ),
    "vaninwagen_1983_essay_free_will.pdf": item(
        "van_inwagen_1983_essay_free_will", "An Essay on Free Will", ["Peter van Inwagen"],
        1983, scope="modern_context"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True, check=True
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"pdfinfo returned no page count for {path}")
    return int(match.group(1))


def build_manifest() -> list[dict[str, Any]]:
    paths = sorted(
        path for path in ARCHIVE.iterdir() if path.suffix.lower() in {".pdf", ".epub"}
    )
    actual = {path.name for path in paths}
    curated = set(CURATION)
    if actual != curated:
        raise RuntimeError(
            f"manifest curation mismatch; uncurated={sorted(actual-curated)}, "
            f"missing={sorted(curated-actual)}"
        )
    rows: list[dict[str, Any]] = []
    for path in paths:
        data = dict(CURATION[path.name])
        data.update(
            {
                "artifact_id": "lit_" + re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_"),
                "path": str(path.relative_to(ROOT)),
                "media_type": "application/pdf" if path.suffix.lower() == ".pdf" else "application/epub+zip",
                "sha256": sha256(path),
                "byte_size": path.stat().st_size,
                "page_count": pdf_pages(path) if path.suffix.lower() == ".pdf" else None,
                "reuse_status": "unverified_do_not_republish",
                "registered_at": "2026-08-24",
            }
        )
        rows.append(data)
    return rows


def main() -> int:
    rows = build_manifest()
    MANIFEST.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(
        f"wrote {len(rows)} artifacts / "
        f"{len({row['intellectual_object_id'] for row in rows})} intellectual objects"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
