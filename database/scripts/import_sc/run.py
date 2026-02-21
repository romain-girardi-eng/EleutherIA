"""CLI orchestrator for the SC corpus import pipeline.

Usage:
    # Dry run (parse only, no DB writes, show statistics)
    python -m database.scripts.import_sc.run --dry-run

    # Single file dry run
    python -m database.scripts.import_sc.run --dry-run --file SC507_Iustinus_martyr_Apologie_livre_1_source.txt

    # Specific category
    python -m database.scripts.import_sc.run --dry-run --category 02_Apologistes

    # Full import (with confirmation prompt)
    python -m database.scripts.import_sc.run --confirm

    # Rollback
    python -m database.scripts.import_sc.run --rollback --run-id <uuid>
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .config import SC_CATEGORIES, SC_CORPUS_DIR, WORK_REGISTRY
from .importer import SCImporter
from .models import SCWork
from .parser import parse_file
from .validator import validate_corpus, validate_work

logger = logging.getLogger(__name__)


def discover_files(
    category: str | None = None,
    single_file: str | None = None,
) -> list[tuple[str, str]]:
    """Discover source files to process.

    Returns list of (filename, absolute_path) tuples.
    """
    if single_file:
        # Find this file across all categories
        for cat_name, cat_subdir in SC_CATEGORIES.items():
            path = Path(SC_CORPUS_DIR) / cat_subdir / single_file
            if path.exists():
                return [(single_file, str(path))]
        # Not found — try the registry
        if single_file in WORK_REGISTRY:
            # Search all category dirs
            for cat_name, cat_subdir in SC_CATEGORIES.items():
                path = Path(SC_CORPUS_DIR) / cat_subdir / single_file
                if path.exists():
                    return [(single_file, str(path))]
        print(f"ERROR: File not found: {single_file}")
        sys.exit(1)

    # Discover from categories
    categories = SC_CATEGORIES
    if category:
        if category not in SC_CATEGORIES:
            print(f"ERROR: Unknown category: {category}")
            print(f"Available: {', '.join(SC_CATEGORIES.keys())}")
            sys.exit(1)
        categories = {category: SC_CATEGORIES[category]}

    files: list[tuple[str, str]] = []
    for cat_name, cat_subdir in categories.items():
        cat_dir = Path(SC_CORPUS_DIR) / cat_subdir
        if not cat_dir.exists():
            print(f"WARN: Category directory not found: {cat_dir}")
            continue
        for p in sorted(cat_dir.glob("*_source.txt")):
            if p.name in WORK_REGISTRY:
                files.append((p.name, str(p)))
            else:
                print(f"WARN: File {p.name} not in WORK_REGISTRY, skipping")

    return files


def parse_all(files: list[tuple[str, str]]) -> list[SCWork]:
    """Parse all discovered files into SCWork objects."""
    works: list[SCWork] = []

    for filename, filepath in files:
        if filename not in WORK_REGISTRY:
            print(f"WARN: {filename} not in WORK_REGISTRY, skipping")
            continue

        registry = WORK_REGISTRY[filename]
        try:
            work = parse_file(filepath, registry)
            works.append(work)
        except Exception as exc:
            print(f"ERROR parsing {filename}: {exc}")

    return works


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sources Chrétiennes corpus import pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate only, no database writes",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Run full import with database writes",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Process a single file (by filename)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Process files from a specific category only",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback a previous import run",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID to rollback (required with --rollback)",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )

    # Determine DB URL
    db_url = args.db_url or os.environ.get("DATABASE_URL", "")

    # Handle rollback
    if args.rollback:
        if not args.run_id:
            print("ERROR: --run-id required with --rollback")
            sys.exit(1)
        if not db_url:
            print("ERROR: DATABASE_URL required for rollback")
            sys.exit(1)
        importer = SCImporter(db_url, dry_run=False)
        importer.rollback_run(args.run_id)
        return

    # Must specify either --dry-run or --confirm
    if not args.dry_run and not args.confirm:
        print("ERROR: Specify --dry-run or --confirm")
        sys.exit(1)

    # Step 1: Discover files
    print("=" * 60)
    print("Sources Chrétiennes Import Pipeline")
    print("=" * 60)
    files = discover_files(category=args.category, single_file=args.file)
    print(f"\nDiscovered {len(files)} source file(s)")

    if not files:
        print("No files to process. Exiting.")
        return

    # Step 2: Parse all files
    print("\nParsing files...")
    works = parse_all(files)
    print(f"Successfully parsed {len(works)}/{len(files)} file(s)")

    if not works:
        print("No works parsed. Exiting.")
        sys.exit(1)

    # Step 3: Validate
    print("\nValidating corpus...")
    errors, warnings = validate_corpus(works)

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print("\nABORTING: Fix errors before import.")
        sys.exit(1)
    else:
        print("Validation passed: 0 errors")

    # Step 4: Import (dry-run or confirmed)
    is_dry = args.dry_run and not args.confirm

    if is_dry:
        print("\n--- DRY RUN (no database writes) ---")
        importer = SCImporter("", dry_run=True)
    else:
        if not db_url:
            print("ERROR: DATABASE_URL required for confirmed import")
            sys.exit(1)

        # Check for existing duplicates before import
        print("\n--- CHECKING FOR EXISTING DUPLICATES ---")
        importer = SCImporter(db_url, dry_run=False)
        dupes = importer.find_duplicates(works)

        existing_works = dupes["all_existing_works"]
        existing_nodes = dupes["existing_kg_nodes"]
        exact_matches = dupes["exact_canonical_matches"]

        # Build a mapping of SC node_ids for quick lookup
        sc_node_ids = {w.node_id for w in works}

        # Find works to remove: exact canonical_id matches
        to_remove = []
        if exact_matches:
            print(f"\nFound {len(exact_matches)} exact canonical_id match(es):")
            for w in exact_matches:
                print(f"  {w['canonical_id']} — {w['author']}, {w['title']} "
                      f"(source={w['source']})")
                to_remove.append(w)

        # Also find works by overlapping kg_work_id
        if existing_works:
            # Check if any existing work's kg_work_id matches an SC node_id
            for w in existing_works:
                kg_id = w.get("kg_work_id", "")
                if kg_id in sc_node_ids and w not in to_remove:
                    print(f"  kg_work_id match: {kg_id} — {w['author']}, "
                          f"{w['title']} (source={w['source']})")
                    to_remove.append(w)

        if existing_nodes:
            print(f"\nFound {len(existing_nodes)} existing KG node(s) with "
                  f"matching node_ids (will use ON CONFLICT DO NOTHING):")
            for n in existing_nodes:
                print(f"  {n['node_id']} ({n['type']})")

        if to_remove:
            print(f"\n{len(to_remove)} existing work(s) will be REMOVED "
                  f"(replaced by SC editions):")
            for w in to_remove:
                print(f"  - {w['canonical_id']}: {w['author']}, {w['title']}")

            confirm_rm = input("\nRemove these duplicates and proceed? "
                             "Type 'yes': ")
            if confirm_rm.strip().lower() != "yes":
                print("Aborted.")
                return

            for w in to_remove:
                print(f"  Removing {w['canonical_id']}...")
                importer.remove_work(str(w["work_id"]), w["canonical_id"])
            print(f"Removed {len(to_remove)} duplicate(s).")
        else:
            print("No duplicates found.")

        print(f"\n--- CONFIRMED IMPORT (run_id: {importer.run_id}) ---")
        print("WARNING: This will write to the database!")
        confirm = input("Type 'yes' to proceed: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    print(f"\nRun ID: {importer.run_id}")
    print()

    stats = importer.import_corpus(works)
    print()
    print(stats.summary())

    if is_dry:
        print("\n(Dry run — no data was written to the database)")
    else:
        print(f"\nImport complete. Run ID: {importer.run_id}")
        print("Use --rollback --run-id to undo if needed.")


if __name__ == "__main__":
    main()
