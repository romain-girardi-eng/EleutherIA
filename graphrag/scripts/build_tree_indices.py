#!/usr/bin/env python3
"""Run the repository-level tree index builder from the GraphRAG package."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    runpy.run_path(
        str(repo_root / "scripts" / "build_work_tree_indices.py"),
        run_name="__main__",
    )
