"""Generate publication-quality figures for the DHQ Amand 1945 article.

Reads the provenance matrix produced by ``scripts/analyze_amand_stoic_provenance.py``
(``docs/papers/2026-05-amand-piste1-data/provenance-matrix-6x4.json``) and emits:

  1. ``heatmap-6x4.png`` / ``.svg`` — 6×4 colored heatmap of ``total_score`` cells.
  2. Three case-study deep-dives (``case-virtue_vice``, ``case-piety``,
     ``case-general_theme``) — stacked bar charts breaking down the thematic /
     conceptual / textual hits for the four primary Stoics on the chosen pivot.

Outputs land in ``docs/papers/2026-05-amand-piste1-figures/`` (PNG dpi=300 + SVG).

Tasks 11-12 of the article workflow. Read-only on KG and matrix JSON.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Display labels — kept in sync with analyze_amand_stoic_provenance.py
# ---------------------------------------------------------------------------

PIVOT_LABELS: dict[str, str] = {
    "argument_carneadean_general_theme_amand1945": "I. General theme",
    "argument_carneadean_legislation_amand1945": "II. Legislation",
    "argument_carneadean_virtue_vice_amand1945": "III. Virtue & vice",
    "argument_carneadean_incentives_amand1945": "IV. Incentives",
    "argument_carneadean_action_futility_amand1945": "V. Action futility",
    "argument_carneadean_piety_amand1945": "VI. Piety",
}

STOIC_LABELS: dict[str, str] = {
    "person_chrysippus_280_206bce_i9j0k1l2": "Chrysippus",
    "person_cleanthes_assos_330_230bce": "Cleanthes",
    "person_posidonius_apameia_135_51bce": "Posidonius",
    "person_panaetius_rhodes_185_109bce": "Panaetius",
}

PIVOT_ORDER: list[str] = list(PIVOT_LABELS.keys())
STOIC_ORDER: list[str] = list(STOIC_LABELS.keys())

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs" / "papers" / "2026-05-amand-piste1-data" / "provenance-matrix-6x4.json"
FIGURES_DIR = ROOT / "docs" / "papers" / "2026-05-amand-piste1-figures"


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def _flatten_matrix(payload: dict) -> list[dict]:
    """Flatten the nested ``matrix`` field of the analyzer's JSON output."""
    nested = payload["matrix"]
    return [cell for row in nested for cell in row]


def _save(fig: Figure, out: Path) -> None:
    """Save a matplotlib figure to PNG (dpi=300) and matching SVG. Closes fig."""
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1: 6×4 heatmap of total_score
# ---------------------------------------------------------------------------


def generate_heatmap(matrix_data: Iterable[dict], out: Path) -> None:
    """Render a 6×4 ``YlOrRd`` heatmap of ``total_score`` for all pivot/Stoic pairs.

    Args:
        matrix_data: flat iterable of ``{pivot, stoic, total_score, ...}`` dicts.
            Cells missing from the input fall back to score ``0``.
        out: PNG output path. The SVG counterpart is written next to it.
    """
    rows = list(matrix_data)
    score_lookup: dict[tuple[str, str], int] = {
        (cell["pivot"], cell["stoic"]): int(cell.get("total_score", 0)) for cell in rows
    }

    grid = np.array(
        [
            [score_lookup.get((pivot, stoic), 0) for stoic in STOIC_ORDER]
            for pivot in PIVOT_ORDER
        ],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    norm = Normalize(vmin=0, vmax=3)
    im = ax.imshow(grid, cmap="YlOrRd", norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(STOIC_ORDER)))
    ax.set_xticklabels([STOIC_LABELS[s] for s in STOIC_ORDER], fontsize=11)
    ax.set_yticks(np.arange(len(PIVOT_ORDER)))
    ax.set_yticklabels([PIVOT_LABELS[p] for p in PIVOT_ORDER], fontsize=11)

    ax.set_xlabel("Primary Stoic source", fontsize=12, labelpad=8)
    ax.set_ylabel("Amand 1945 moral pivot", fontsize=12, labelpad=8)
    ax.set_title(
        "Stoic primary parallels for Amand 1945's six moral pivots\n"
        "(thematic + conceptual + textual)",
        fontsize=13,
        pad=14,
    )

    # Annotate each cell with the integer score. Choose dark text on light bg,
    # white on dark bg, using the same threshold ``YlOrRd`` itself uses.
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            score = int(grid[i, j])
            color = "white" if score >= 2 else "black"
            ax.text(
                j,
                i,
                str(score),
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=color,
            )

    # Subtle gridlines between cells
    ax.set_xticks(np.arange(-0.5, len(STOIC_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(PIVOT_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Total score (0–3)", fontsize=11)
    cbar.set_ticks([0, 1, 2, 3])

    _save(fig, out)


# ---------------------------------------------------------------------------
# Figure 2: per-pivot case-study deep-dive
# ---------------------------------------------------------------------------


def generate_case_study(matrix_data: Iterable[dict], pivot_id: str, out: Path) -> None:
    """Render a stacked-bar case-study for one Amand pivot across the 4 Stoics.

    Each Stoic gets a column with three stacked segments: thematic / conceptual /
    textual hit counts. The bar height equals the total raw hits (not the bounded
    ``total_score``) so readers can see corroboration density at a glance.

    Args:
        matrix_data: flat iterable; rows where ``pivot != pivot_id`` are ignored.
        pivot_id: one of the six Amand pivot node ids.
        out: PNG output path. SVG counterpart written alongside.
    """
    if pivot_id not in PIVOT_LABELS:
        raise ValueError(f"unknown pivot id: {pivot_id!r}")

    by_stoic: dict[str, dict] = {
        cell["stoic"]: cell
        for cell in matrix_data
        if cell.get("pivot") == pivot_id and cell.get("stoic") in STOIC_LABELS
    }

    stoic_labels = [STOIC_LABELS[s] for s in STOIC_ORDER]
    thematic = np.array([len(by_stoic.get(s, {}).get("thematic_hits", [])) for s in STOIC_ORDER])
    conceptual = np.array(
        [len(by_stoic.get(s, {}).get("conceptual_hits", [])) for s in STOIC_ORDER]
    )
    textual = np.array([len(by_stoic.get(s, {}).get("textual_hits", [])) for s in STOIC_ORDER])
    totals = np.array([int(by_stoic.get(s, {}).get("total_score", 0)) for s in STOIC_ORDER])

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    x = np.arange(len(stoic_labels))
    width = 0.62

    p_th = ax.bar(x, thematic, width, label="Thematic hits", color="#fdae61", edgecolor="white")
    p_co = ax.bar(
        x,
        conceptual,
        width,
        bottom=thematic,
        label="Conceptual hits",
        color="#f46d43",
        edgecolor="white",
    )
    p_tx = ax.bar(
        x,
        textual,
        width,
        bottom=thematic + conceptual,
        label="Textual hits",
        color="#a50026",
        edgecolor="white",
    )

    # Annotate the totals on top of each stack, plus the bounded score in parens.
    tops = thematic + conceptual + textual
    for xi, top, score in zip(x, tops, totals, strict=True):
        ax.text(
            xi,
            top + max(0.15, tops.max() * 0.02),
            f"score {score}/3",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#444",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(stoic_labels, fontsize=11)
    ax.set_ylabel("Raw hit count (per test)", fontsize=12)
    ax.set_xlabel("Primary Stoic source", fontsize=12, labelpad=8)
    ax.set_title(
        f"Case-study deep-dive — {PIVOT_LABELS[pivot_id]}\n"
        "Thematic / conceptual / textual corroboration",
        fontsize=13,
        pad=12,
    )

    headroom = max(1.0, float(tops.max()) * 0.25 + 0.5)
    ax.set_ylim(0, float(tops.max()) + headroom)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.legend(loc="upper right", frameon=False, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)

    # Silence unused references
    del p_th, p_co, p_tx

    _save(fig, out)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


CASE_STUDIES: list[tuple[str, str]] = [
    ("argument_carneadean_virtue_vice_amand1945", "case-virtue_vice.png"),
    ("argument_carneadean_piety_amand1945", "case-piety.png"),
    ("argument_carneadean_general_theme_amand1945", "case-general_theme.png"),
]


def main() -> int:
    if not DATA_PATH.exists():
        print(f"error: provenance matrix not found at {DATA_PATH}", file=sys.stderr)
        return 1

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    flat_matrix = _flatten_matrix(payload)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    heatmap_out = FIGURES_DIR / "heatmap-6x4.png"
    generate_heatmap(flat_matrix, heatmap_out)
    print(f"wrote {heatmap_out.relative_to(ROOT)}")
    print(f"wrote {heatmap_out.with_suffix('.svg').relative_to(ROOT)}")

    for pivot_id, filename in CASE_STUDIES:
        out = FIGURES_DIR / filename
        generate_case_study(flat_matrix, pivot_id, out)
        print(f"wrote {out.relative_to(ROOT)}")
        print(f"wrote {out.with_suffix('.svg').relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
