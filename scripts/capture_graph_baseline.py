"""Capture Cosmograph baseline screenshots/video with browser-use.

Prereqs:
- Frontend running locally (e.g. `cd frontend && npm run dev`)
- `pip install browser-use langchain-anthropic`
- Anthropic auth configured for `ChatAnthropic`
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from browser_use import Agent
from langchain_anthropic import ChatAnthropic


def build_task(base_url: str, engine: str, out_dir: Path) -> str:
    return f"""
Open {base_url}/visualizer?engine={engine}.
Wait until the graph is fully rendered and stable.
Capture and save screenshots with these exact names in {out_dir}:
- 01-default-overview.png
- 02-search-result-selected.png (after selecting a search result)
- 03-focus-mode.png (after double-clicking a node)
- 04-filters-types-schools.png (after enabling one type and one school filter)
- 05-clusters-mode.png (after switching to clusters mode)
- 06-legend-stats-controls.png (legend, stats pill, controls visible)
Then record a short interaction video (pan, zoom, pause/play, rectangle selection, keyboard shortcuts)
and save it as baseline-interactions.mp4 in {out_dir}.
""".strip()


async def run_capture(base_url: str, engine: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    agent = Agent(
        task=build_task(base_url, engine, out_dir),
        llm=ChatAnthropic(model="claude-sonnet-4-6"),
    )

    await agent.run()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture graph baseline artifacts with browser-use"
    )
    parser.add_argument("--base-url", default="http://localhost:5173")
    parser.add_argument("--engine", default="cosmograph", choices=["cosmograph", "d3"])
    parser.add_argument(
        "--out-dir",
        default="docs/assets/graph-baseline",
        help="Output directory for screenshots/video",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_capture(args.base_url, args.engine, Path(args.out_dir)))
