"""Mass map Diogenes Laertius VII (and X) sections to SVF / LS / Usener via Kimi.

For each DL VII section (Stoics) — and optionally Book X (Epicurus) — we send
the Greek text to Kimi K2.5 with a strict JSON Schema asking for the von Arnim
SVF correlation if known, plus optional Long-Sedley and Usener references.

Confidence policy:
  - Kimi marks every output as ``confidence: medium`` and ``needs_review: true``.
  - When Kimi answers ``no_known_correlation: true`` we skip the row entirely
    rather than invent a number (zero-tolerance for fabrication).

Output: data/doxographical_audit/kimi_dl_mappings.jsonl
(One row per (passage_id, ref) — compatible with fragment_mappings.jsonl.)

Usage:
  MOONSHOT_API_KEY=... python -m database.scripts.kimi_map_dl_to_svf \\
      [--book 7] [--limit 50] [--resume]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from openai import APIError, OpenAI, RateLimitError

logger = logging.getLogger("kimi_map_dl_to_svf")

ROOT = Path(__file__).resolve().parents[2]
NODES_JSONL = ROOT / "data" / "kg" / "nodes.jsonl"
OUTPUT = ROOT / "data" / "doxographical_audit" / "kimi_dl_mappings.jsonl"

SYSTEM_PROMPT = """You are a classical philology assistant specialising in Hellenistic doxography.

You are given a section of Diogenes Laertius (DL) in Greek and asked whether
von Arnim's Stoicorum Veterum Fragmenta (SVF) collects this passage, and
whether Long-Sedley (LS) prints it as a numbered text.

Critical rules:
1. Only return SVF / LS / Usener numbers you are confident actually exist in
   the printed editions of von Arnim (1903-1905) and Long-Sedley (1987).
2. NEVER invent a fragment number. If you are not confident, set
   ``no_known_correlation`` to true and leave the lists empty.
3. SVF I = Zeno + early Stoa, SVF II = Chrysippus (logic + physics),
   SVF III = Chrysippus (ethics) + younger Stoics.
4. The text may be a doxographical report; that is fine — von Arnim still
   collects it as a fragment with a number (e.g. DL VII.149 = SVF II.913).
5. Return strict JSON matching the schema. No prose, no commentary."""


def build_user_prompt(book: int, section: int, greek: str) -> str:
    return (
        f"Diogenes Laertius, Vitae Philosophorum, Book {book}, section {section}:\n\n"
        f"{greek.strip()}\n\n"
        "Does von Arnim collect this section as an SVF fragment? "
        "If so, which SVF volume.number(s)? Long-Sedley correlation if any. "
        "If unsure, answer no_known_correlation = true. JSON only."
    )


# JSON Schema for tool-strict output
RESPONSE_SCHEMA: dict[str, Any] = {
    "name": "fragment_correlation",
    "schema": {
        "type": "object",
        "properties": {
            "no_known_correlation": {"type": "boolean"},
            "svf_refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "volume": {"type": "string", "enum": ["I", "II", "III"]},
                        "number": {"type": "string", "pattern": r"^\d+[a-z]?$"},
                        "fragmented_philosopher": {
                            "type": "string",
                            "enum": [
                                "Zeno",
                                "Cleanthes",
                                "Chrysippus",
                                "Aristo",
                                "Posidonius",
                                "Antipater",
                                "Diogenes of Babylon",
                                "Stoics (general)",
                            ],
                        },
                    },
                    "required": ["volume", "number", "fragmented_philosopher"],
                    "additionalProperties": False,
                },
            },
            "ls_refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "chapter": {"type": "string", "pattern": r"^\d{1,3}$"},
                        "letter": {"type": "string", "pattern": r"^[A-Z]$"},
                    },
                    "required": ["chapter", "letter"],
                    "additionalProperties": False,
                },
            },
            "usener_refs": {
                "type": "array",
                "items": {"type": "string", "pattern": r"^\d+$"},
            },
            "topic": {"type": "string", "maxLength": 120},
        },
        "required": ["no_known_correlation", "svf_refs", "ls_refs", "usener_refs"],
        "additionalProperties": False,
    },
    "strict": True,
}


def load_dl_sections(book: int) -> list[dict[str, Any]]:
    prefix = f"passage_dl_lives_{book}_1_"
    out: list[dict[str, Any]] = []
    with NODES_JSONL.open() as fh:
        for line in fh:
            n = json.loads(line)
            if n.get("type") != "passage":
                continue
            nid = n["node_id"]
            if not nid.startswith(prefix):
                continue
            try:
                sec = int(nid[len(prefix) :])
            except ValueError:
                continue
            out.append(
                {
                    "passage_id": nid,
                    "section": sec,
                    "greek": n.get("description") or "",
                    "label": n.get("label") or "",
                }
            )
    out.sort(key=lambda r: r["section"])
    return out


def already_mapped(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open() as fh:
        for line in fh:
            try:
                row = json.loads(line)
                seen.add(row["passage_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


SCHEMA_TEXT = """{
  "no_known_correlation": <bool>,
  "svf_refs": [{"volume": "I"|"II"|"III", "number": "<digits>", "fragmented_philosopher": "Zeno"|"Cleanthes"|"Chrysippus"|"Posidonius"|"Antipater"|"Diogenes of Babylon"|"Aristo"|"Stoics (general)"}],
  "ls_refs": [{"chapter": "<digits>", "letter": "<A-Z>"}],
  "usener_refs": ["<digits>"],
  "topic": "<short string, <=120 chars>"
}"""


def _strip_codeblock(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # remove ```json ... ``` wrappers
        s = s.split("```", 2)[1] if s.count("```") >= 2 else s.lstrip("`")
        if s.startswith("json"):
            s = s[4:]
        s = s.strip()
        if s.endswith("```"):
            s = s[:-3].strip()
    return s


def kimi_call(
    client: OpenAI, model: str, book: int, section: int, greek: str, retries: int = 3
) -> dict[str, Any] | None:
    user = build_user_prompt(book, section, greek[:3500])  # truncate very long sections
    user += (
        "\n\nReturn JSON matching this shape exactly (no other keys, no markdown):\n"
        + SCHEMA_TEXT
    )
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=900,
            )
            content = resp.choices[0].message.content or "{}"
            content = _strip_codeblock(content)
            return json.loads(content)
        except RateLimitError:
            wait = 8 * (attempt + 1)
            logger.warning("Rate-limited, sleeping %ds", wait)
            time.sleep(wait)
        except (APIError, json.JSONDecodeError) as exc:
            logger.warning("attempt %d failed: %s", attempt + 1, exc)
            time.sleep(2 * (attempt + 1))
    return None


def emit_rows(
    passage_id: str, book: int, section: int, k: dict[str, Any]
) -> list[dict[str, Any]]:
    if k.get("no_known_correlation"):
        return []
    rows: list[dict[str, Any]] = []
    collections: list[dict[str, Any]] = []
    philos: set[str] = set()
    for svf in k.get("svf_refs", []) or []:
        collections.append(
            {
                "collection": "SVF",
                "reference": f"{svf['volume']}.{svf['number']}",
                "editor": "von Arnim",
                "year": 1903,
                "verification_source": "Kimi K2.5 prior (needs_review)",
                "auto_extracted": True,
                "fragmented_philosopher": svf.get("fragmented_philosopher"),
            }
        )
        if svf.get("fragmented_philosopher"):
            philos.add(svf["fragmented_philosopher"])
    for ls in k.get("ls_refs", []) or []:
        collections.append(
            {
                "collection": "LS",
                "reference": f"{ls['chapter']}{ls['letter']}",
                "editor": "Long-Sedley",
                "year": 1987,
                "verification_source": "Kimi K2.5 prior (needs_review)",
                "auto_extracted": True,
            }
        )
    for un in k.get("usener_refs", []) or []:
        collections.append(
            {
                "collection": "Usener",
                "reference": un,
                "editor": "Usener",
                "year": 1887,
                "verification_source": "Kimi K2.5 prior (needs_review)",
                "auto_extracted": True,
            }
        )
    if not collections:
        return []

    # Pick primary philosopher: prefer Chrysippus > Zeno > Cleanthes > Posidonius > Stoics
    priority = [
        "Chrysippus",
        "Zeno",
        "Cleanthes",
        "Posidonius",
        "Antipater",
        "Diogenes of Babylon",
        "Aristo",
        "Stoics (general)",
    ]
    primary_philo = next((p for p in priority if p in philos), None)
    philo_to_node = {
        "Chrysippus": ("Chrysippus", "person_chrysippus_280_206bce_i9j0k1l2"),
        "Zeno": ("Zeno of Citium", "person_zeno_citium_334_262bce"),
        "Cleanthes": ("Cleanthes", "person_cleanthes_assos_330_230bce"),
        "Posidonius": ("Posidonius", "person_posidonius_apameia_135_51bce"),
    }
    philo_name, philo_node = philo_to_node.get(primary_philo, (primary_philo, None))

    rows.append(
        {
            "passage_id": passage_id,
            "attestation_type": "doxographical_fragment",
            "primary_attestation": {
                "transmitting_author": "person_diogenes_laertius_3c_ce",
                "transmitting_work": "work_dl_lives_eminent_philosophers",
                "transmitting_passage": passage_id,
            },
            "fragment_collections": collections,
            "extant_in_original": False,
            "extant_in_translation_only": False,
            "confidence": "medium",
            "fragmented_philosopher": philo_name,
            "philosopher_node_id": philo_node,
            "note": f"Kimi K2.5 von Arnim correlation for DL {book}.1.{section} — flagged needs_review for manual verification",
            "needs_review": True,
            "doxographical_source": "kimi_dl_svf",
            "kimi_topic": k.get("topic"),
        }
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--book", type=int, default=7, help="DL book (7=Stoics, 10=Epicurus)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap number of sections processed"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Skip passages already in output"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default="kimi-latest")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    key = os.environ.get("MOONSHOT_API_KEY")
    if not key:
        print("MOONSHOT_API_KEY not set", file=sys.stderr)
        return 2
    base = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
    client = OpenAI(api_key=key, base_url=base)

    sections = load_dl_sections(args.book)
    logger.info("Loaded %d sections for DL Book %d", len(sections), args.book)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    done = already_mapped(OUTPUT) if args.resume else set()
    if done:
        sections = [s for s in sections if s["passage_id"] not in done]
        logger.info("Resume: %d already mapped, %d remaining", len(done), len(sections))

    if args.limit:
        sections = sections[: args.limit]

    written = 0
    skipped = 0
    fh = OUTPUT.open("a", encoding="utf-8")
    try:
        for i, s in enumerate(sections):
            greek = s["greek"]
            if not greek or len(greek) < 30:
                skipped += 1
                continue
            if args.dry_run:
                logger.info("[DRY] would map %s", s["passage_id"])
                continue
            k = kimi_call(client, args.model, args.book, s["section"], greek)
            if k is None:
                logger.warning("no response for %s", s["passage_id"])
                skipped += 1
                time.sleep(args.delay)
                continue
            rows = emit_rows(s["passage_id"], args.book, s["section"], k)
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if rows:
                written += 1
            else:
                skipped += 1
            if (i + 1) % 20 == 0:
                logger.info(
                    "processed %d/%d (written=%d, skipped=%d)",
                    i + 1,
                    len(sections),
                    written,
                    skipped,
                )
            time.sleep(args.delay)
    finally:
        fh.close()

    print(
        json.dumps(
            {
                "book": args.book,
                "written": written,
                "skipped": skipped,
                "total": len(sections),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
