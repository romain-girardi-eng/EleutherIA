"""Track B1 — Parse local academic library and extract scholar/argument/edge patches.

Inputs:
  - [local-path] SHAL/04_Littérature_secondaire/
    (PDFs + MD summaries + TXT extractions)

Outputs:
  - data/kg_enrichment/from_local_library.jsonl  (patches — appended, idempotent)
  - data/kg_enrichment/from_local_library_report.md

Methodology:
  1. Inventory MD/TXT (preferred) + PDF metadata-only fallback.
  2. For each file: read up to ~12k chars; send to Fireworks/Kimi K2 with response_format=json_object.
  3. Emit idempotent patches keyed on `scholar_<surname>_<firstinitial>`.
  4. Reconcile with existing KG (nodes.jsonl snapshot) and prior web/local research JSONLs.
  5. Resume: skip files whose basenames already appear in source_files of prior patches.

Constraints:
  - Zero fabrication: low-confidence extractions get `needs_review=True`.
  - Greek/Latin quotes preserved only if present in source text.
  - Idempotent node_ids; re-running merges instead of duplicating.

Environment:
  - .venv-py314/bin/python
  - FIREWORKS_API_KEY (read from [local-path])
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LIBRARY_ROOT = Path(
    "[local-path] SHAL/04_Littérature_secondaire"
)
PROJECT_ROOT = Path("[local-path]")
OUTPUT_DIR = PROJECT_ROOT / "data" / "kg_enrichment"
OUTPUT_JSONL = OUTPUT_DIR / "from_local_library.jsonl"
OUTPUT_REPORT = OUTPUT_DIR / "from_local_library_report.md"
WEB_JSONL = OUTPUT_DIR / "from_web_research.jsonl"
LOG_FILE = OUTPUT_DIR / "extract_log.txt"
FAILURE_FILE = OUTPUT_DIR / "from_local_library_failures.jsonl"
ENV_CANDIDATES = [
    Path("[local-path]"),
    Path("[local-path]"),
]

KIMI_MODEL = "accounts/fireworks/models/kimi-k2p6"
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
MAX_FILE_CHARS = 12_000
DEFAULT_MAX_FILES = 600

EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["scholar_identity", "work_metadata", "key_positions"],
    "properties": {
        "scholar_identity": {
            "type": "object",
            "required": ["surname"],
            "additionalProperties": False,
            "properties": {
                "surname": {"type": "string"},
                "given_names": {"type": "string"},
                "affiliations": {"type": "array", "items": {"type": "string"}},
                "specialty": {"type": "string"},
                "confidence": {"type": "number"},
            },
        },
        "work_metadata": {
            "type": "object",
            "required": ["title"],
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "year": {"type": "integer"},
                "publisher": {"type": "string"},
                "type": {"type": "string", "enum": ["monograph", "article", "chapter", "edited_volume", "unknown"]},
                "doi": {"type": "string"},
                "isbn": {"type": "string"},
                "page_range": {"type": "string"},
                "confidence": {"type": "number"},
            },
        },
        "key_positions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["topic", "stance"],
                "additionalProperties": False,
                "properties": {
                    "topic": {"type": "string"},
                    "stance": {"type": "string"},
                    "supporting_evidence": {"type": "array", "items": {"type": "string"}},
                    "engages_with_scholars": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["scholar", "stance"],
                            "properties": {
                                "scholar": {"type": "string"},
                                "stance": {"type": "string", "enum": ["agrees", "critiques", "qualifies", "builds_on", "cites"]},
                                "note": {"type": "string"},
                            },
                        },
                    },
                    "confidence": {"type": "number"},
                    "page_range": {"type": "string"},
                },
            },
        },
    },
}


def slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z]", "_", name.strip().lower())
    return re.sub(r"_+", "_", s).strip("_")


def scholar_id(surname: str, given_names: str = "") -> str:
    initial = given_names.strip()[:1].lower() if given_names else "x"
    return f"scholar_{slug(surname)}_{initial}"


def work_id(scholar: str, year: int | None, title: str) -> str:
    y = year or 0
    t = slug(title)[:40]
    return f"scholarly_work_{slug(scholar)}_{y}_{t}"


def argument_id(scholar: str, topic: str, idx: int) -> str:
    return f"scholarly_argument_{slug(scholar)}_{slug(topic)[:30]}_{idx}"


def load_fireworks_key() -> str | None:
    if os.environ.get("FIREWORKS_API_KEY"):
        return os.environ["FIREWORKS_API_KEY"]
    for env_path in ENV_CANDIDATES:
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
            if line.startswith("FIREWORKS_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return None


def load_existing_kg_scholars(nodes_path: Path) -> dict[str, str]:
    """Return surname_lower -> existing_node_id for modern/contemporary persons in KG snapshot."""
    mapping: dict[str, str] = {}
    if not nodes_path.exists():
        return mapping
    for line in nodes_path.read_text(encoding="utf-8").splitlines():
        try:
            n = json.loads(line)
        except json.JSONDecodeError:
            continue
        if n.get("type") != "person":
            continue
        md = n.get("metadata") or {}
        if isinstance(md, str):
            try:
                md = json.loads(md)
            except json.JSONDecodeError:
                md = {}
        period = str(md.get("period") or n.get("period") or "").lower()
        role = str(md.get("scholarly_role") or md.get("role") or "").lower()
        if not ("modern" in period or "contemporary" in period or "scholar" in role):
            continue
        label = n.get("label") or ""
        words = [w for w in re.split(r"[\s().,;:/\-]+", label) if w.isalpha()]
        if not words:
            continue
        surname = words[-1].lower()
        mapping.setdefault(surname, n.get("id") or n.get("node_id") or "")
    return mapping


def load_prior_patches(*paths: Path) -> tuple[dict[str, str], set[str]]:
    """Scan prior JSONL outputs to extract:
       - surname_lower -> canonical_node_id (for cross-source dedup)
       - set of basenames that have already been processed
    """
    surname_map: dict[str, str] = {}
    processed: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = obj.get("kind")
            if kind == "scholar":
                nid = obj.get("node_id") or obj.get("id") or ""
                label = obj.get("label") or ""
                md = obj.get("metadata") or {}
                surname = md.get("surname") if isinstance(md, dict) else None
                if not surname:
                    # try from label
                    words = [w for w in re.split(r"[\s().,;:/\-]+", label) if w.isalpha()]
                    if words:
                        surname = words[-1]
                if surname and nid:
                    surname_map.setdefault(surname.lower(), nid)
            # collect source_files for resume
            md = obj.get("metadata") or {}
            if isinstance(md, dict):
                sf = md.get("source_file") or md.get("source_files")
                if isinstance(sf, list):
                    for x in sf:
                        if isinstance(x, str):
                            processed.add(Path(x).name)
                elif isinstance(sf, str):
                    processed.add(Path(sf).name)
    return surname_map, processed


@dataclass
class FileResult:
    path: Path
    status: str  # ok | skip | error
    reason: str = ""
    payload: dict[str, Any] | None = None


EXCLUDED_FILENAMES = {
    "CITATIONS.md", "CONCEPTS.md", "INDEX.md", "MANIFEST.md",
    "THESIS_MAP.md", "THESIS_MAP_ANNOTATED.md", "TREE_INDEX.md",
    "page_map_remaining_failures.txt", "README.md",
}
EXCLUDED_DIRS = {"_duplicates", ".claude", ".git", "node_modules"}


def inventory(root: Path) -> dict[str, list[Path]]:
    by_cat: dict[str, list[Path]] = {}
    if not root.exists():
        return by_cat
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".txt", ".pdf"}:
            continue
        if p.name in EXCLUDED_FILENAMES:
            continue
        try:
            rel_parts = p.relative_to(root).parts
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        cat = rel_parts[0] if rel_parts else "_root"
        if len(rel_parts) == 1 and p.is_file():
            if p.suffix.lower() != ".pdf":
                continue
        by_cat.setdefault(cat, []).append(p)
    return by_cat


def read_file_text(p: Path, max_chars: int = MAX_FILE_CHARS) -> str | None:
    suf = p.suffix.lower()
    try:
        if suf in {".md", ".txt"}:
            return p.read_text(encoding="utf-8", errors="ignore")[:max_chars]
        if suf == ".pdf":
            try:
                from pypdf import PdfReader  # type: ignore
            except ImportError:
                return (
                    f"[PDF metadata-only — no text extraction available]\n"
                    f"Filename: {p.name}\nFolder: {p.parent.name}\n"
                )
            reader = PdfReader(str(p))
            chunks: list[str] = []
            for page in reader.pages[:2]:
                chunks.append(page.extract_text() or "")
            txt = "\n".join(chunks).strip()
            if not txt:
                return (
                    f"[PDF text extraction empty]\nFilename: {p.name}\nFolder: {p.parent.name}\n"
                )
            return txt[:max_chars]
    except Exception as e:
        return f"__ERROR__:{e}"
    return None


def prioritize(by_cat: dict[str, list[Path]], skip_pdf: bool, processed: set[str]) -> list[Path]:
    """Sort by category priority + format preference; exclude already-processed."""
    priority_cats = [
        "01_Philosophie_antique",
        "07_Libre_arbitre_theologie",
        "Extractions_articles",
        "05_Origene",
        "04_Apologistes_Justin",
        "06_Patristique",
        "02_Judaisme_Second_Temple",
        "03_Paul",
        "10_Ouvrages_reference",
        "08_Commentaires_NT",
        "09_Methodologie",
    ]
    cat_rank = {c: i for i, c in enumerate(priority_cats)}

    def file_rank(p: Path) -> tuple[int, int, str]:
        try:
            cat = p.relative_to(LIBRARY_ROOT).parts[0]
        except ValueError:
            cat = "_root"
        cat_score = cat_rank.get(cat, 99)
        suf_score = {".md": 0, ".txt": 1, ".pdf": 2}.get(p.suffix.lower(), 3)
        return (cat_score, suf_score, p.name)

    all_files: list[Path] = []
    for paths in by_cat.values():
        for p in paths:
            if skip_pdf and p.suffix.lower() == ".pdf":
                continue
            if p.name in processed:
                continue
            all_files.append(p)
    all_files.sort(key=file_rank)
    return all_files


SYSTEM_PROMPT = """You are a scholarly metadata extractor for a knowledge graph on free will in antiquity.

Read the provided text (a secondary-literature summary, article, or PDF excerpt) and extract:
1. The scholar's identity (surname is required; given names + affiliations if available).
2. The work's metadata (title required; year/publisher/type if available).
3. Key positions the scholar takes on free will, determinism, fate, moral responsibility, or related topics.

Rules:
- NEVER invent facts. If you cannot identify the scholar or work, set surname/title to "UNKNOWN" and confidence to 0.0.
- Each "key_position" must cite the scholar's actual stance (paraphrase only, no fabricated quotes).
- "supporting_evidence" should list primary-source citations the scholar references (CTS URN, author+work+passage, or descriptive locator).
- "engages_with_scholars" lists other modern scholars the author cites/critiques/builds on.
- Confidence scores: 0.95+ for explicit, 0.7-0.9 for clear inference, <0.6 for uncertain.
- Stay focused on free-will-relevant content. Ignore tangential material.
- Return strictly valid JSON conforming to the schema."""


def call_kimi(api_key: str, text: str, file_hint: str, timeout: int = 120) -> tuple[dict[str, Any] | None, str]:
    """Call Fireworks-hosted Kimi K2 with JSON enforcement. Returns (payload, error_msg)."""
    import urllib.error
    import urllib.request

    schema_instruction = (
        "Return ONLY a valid JSON object matching this schema (no prose):\n"
        + json.dumps({k: v for k, v in EXTRACTION_SCHEMA["properties"].items()})
    )
    body = {
        "model": KIMI_MODEL,
        "max_tokens": 3072,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + schema_instruction},
            {"role": "user", "content": f"Source file: {file_hint}\n\n---\n\n{text}"},
        ],
    }
    last_err = ""
    for attempt in range(3):
        req = urllib.request.Request(
            FIREWORKS_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content), ""
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="ignore")[:300]
            last_err = f"HTTP {e.code}: {body_text}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep((2 ** attempt) + 0.5 * attempt)
                continue
            return None, last_err
        except json.JSONDecodeError as e:
            last_err = f"JSON parse: {e}"
            time.sleep(1)
            continue
        except Exception as e:
            last_err = f"Error: {e}"
            time.sleep(1)
            continue
    return None, last_err or "unknown"


@dataclass
class PatchAccumulator:
    scholars: dict[str, dict[str, Any]] = field(default_factory=dict)
    works: dict[str, dict[str, Any]] = field(default_factory=dict)
    arguments: dict[str, dict[str, Any]] = field(default_factory=dict)  # keyed by node_id
    edges: dict[str, dict[str, Any]] = field(default_factory=dict)      # keyed by (type, src, tgt)

    def add_scholar(self, node_id: str, label: str, metadata: dict[str, Any]) -> None:
        if node_id in self.scholars:
            existing = self.scholars[node_id]["metadata"]
            existing.setdefault("source_files", [])
            for sf in metadata.get("source_files", []):
                if sf not in existing["source_files"]:
                    existing["source_files"].append(sf)
            # keep highest confidence
            existing["confidence"] = max(
                float(existing.get("confidence") or 0),
                float(metadata.get("confidence") or 0),
            )
            return
        self.scholars[node_id] = {
            "kind": "scholar",
            "node_id": node_id,
            "label": label,
            "metadata": metadata,
        }

    def add_work(self, node_id: str, label: str, metadata: dict[str, Any]) -> None:
        if node_id not in self.works:
            self.works[node_id] = {
                "kind": "scholarly_work",
                "node_id": node_id,
                "label": label,
                "metadata": metadata,
            }

    def add_argument(self, patch: dict[str, Any]) -> None:
        nid = patch.get("node_id")
        if nid and nid not in self.arguments:
            self.arguments[nid] = patch

    def add_edge(self, edge_type: str, source_id: str, target_id: str, metadata: dict[str, Any]) -> None:
        key = f"{edge_type}|{source_id}|{target_id}"
        if key not in self.edges:
            self.edges[key] = {
                "kind": "edge",
                "edge_type": edge_type,
                "source_id": source_id,
                "target_id": target_id,
                "metadata": metadata,
            }

    def write_append(self, path: Path) -> dict[str, int]:
        """Write all patches to a JSONL file, deduplicated against existing content."""
        path.parent.mkdir(parents=True, exist_ok=True)
        existing_keys: set[str] = set()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                existing_keys.add(_patch_key(obj))

        counts = {"scholar": 0, "scholarly_work": 0, "scholarly_argument": 0, "edge": 0}
        new_lines: list[str] = []
        for p in self.scholars.values():
            if _patch_key(p) not in existing_keys:
                new_lines.append(json.dumps(p, ensure_ascii=False))
                counts["scholar"] += 1
        for p in self.works.values():
            if _patch_key(p) not in existing_keys:
                new_lines.append(json.dumps(p, ensure_ascii=False))
                counts["scholarly_work"] += 1
        for p in self.arguments.values():
            if _patch_key(p) not in existing_keys:
                new_lines.append(json.dumps(p, ensure_ascii=False))
                counts["scholarly_argument"] += 1
        for p in self.edges.values():
            if _patch_key(p) not in existing_keys:
                new_lines.append(json.dumps(p, ensure_ascii=False))
                counts["edge"] += 1

        if new_lines:
            with path.open("a", encoding="utf-8") as f:
                for line in new_lines:
                    f.write(line + "\n")
        return counts


def _patch_key(obj: dict[str, Any]) -> str:
    kind = obj.get("kind", "?")
    if kind == "edge":
        return f"edge|{obj.get('edge_type')}|{obj.get('source_id')}|{obj.get('target_id')}"
    return f"{kind}|{obj.get('node_id') or obj.get('id') or ''}"


def integrate_extraction(
    acc: PatchAccumulator,
    src_file: Path,
    payload: dict[str, Any],
    existing_scholars: dict[str, str],
    confidence_threshold: float = 0.5,
) -> tuple[bool, str]:
    """Returns (added_anything, reason_if_skipped)."""
    si = payload.get("scholar_identity") or {}
    wm = payload.get("work_metadata") or {}
    surname = (si.get("surname") or "").strip()
    title = (wm.get("title") or "").strip()
    scholar_conf = float(si.get("confidence") or 0)
    work_conf = float(wm.get("confidence") or 0)

    if not surname or surname.upper() == "UNKNOWN" or not title or title.upper() == "UNKNOWN":
        return False, "unknown scholar/title"
    if max(scholar_conf, work_conf) < confidence_threshold:
        return False, f"low confidence ({scholar_conf:.2f}/{work_conf:.2f})"

    existing_id = existing_scholars.get(surname.lower())
    sid = existing_id or scholar_id(surname, si.get("given_names", ""))
    scholar_label = (si.get("given_names", "") + " " + surname).strip()
    scholar_md = {
        "period": "Modern",
        "specialty": si.get("specialty"),
        "affiliations": si.get("affiliations") or [],
        "given_names": si.get("given_names", ""),
        "surname": surname,
        "source_files": [str(src_file)],
        "confidence": scholar_conf or 0.8,
        "merge_into_existing_node": bool(existing_id),
    }
    acc.add_scholar(sid, scholar_label, scholar_md)

    # If new surname, register it so subsequent files in this run also merge.
    existing_scholars.setdefault(surname.lower(), sid)

    wid = work_id(surname, wm.get("year"), title)
    work_md = {
        "author_id": sid,
        "year": wm.get("year"),
        "publisher": wm.get("publisher"),
        "type": wm.get("type", "unknown"),
        "doi": wm.get("doi"),
        "isbn": wm.get("isbn"),
        "page_range": wm.get("page_range"),
        "title": title,
        "source_file": str(src_file),
        "confidence": work_conf or 0.8,
    }
    work_label = f"{surname} {wm.get('year') or '?'} — {title[:80]}"
    acc.add_work(wid, work_label, work_md)
    acc.add_edge("authored_by", wid, sid, {"confidence": 0.99})

    for idx, kp in enumerate(payload.get("key_positions") or []):
        if not isinstance(kp, dict):
            continue
        topic = (kp.get("topic") or "").strip()
        stance = (kp.get("stance") or "").strip()
        if not topic or not stance:
            continue
        conf = float(kp.get("confidence") or 0.7)
        aid = argument_id(surname, topic, idx)
        arg_md = {
            "scholarly_work_id": wid,
            "scholar_id": sid,
            "topic": topic,
            "stance": stance,
            "page_range": kp.get("page_range"),
            "engages_with_scholars": kp.get("engages_with_scholars") or [],
            "supporting_evidence": kp.get("supporting_evidence") or [],
            "confidence": conf,
            "needs_review": conf < 0.7,
            "source_file": str(src_file),
        }
        acc.add_argument({
            "kind": "scholarly_argument",
            "node_id": aid,
            "label": f"{surname}: {stance[:80]}",
            "metadata": arg_md,
        })
        acc.add_edge("wrote_about", sid, f"topic:{slug(topic)}", {"confidence": conf, "via_argument": aid})
        for ev in kp.get("supporting_evidence") or []:
            if not isinstance(ev, str):
                continue
            acc.add_edge(
                "cites_primary_source",
                aid,
                f"primary_source_hint:{slug(ev)[:60]}",
                {"role": "supporting_evidence", "raw_citation": ev, "needs_review": True},
            )
        for ew in kp.get("engages_with_scholars") or []:
            if not isinstance(ew, dict):
                continue
            other = ew.get("scholar", "")
            if not other or not isinstance(other, str):
                continue
            parts = other.split()
            other_surname = parts[-1] if parts else other
            other_initial = parts[0] if len(parts) > 1 else ""
            oid = existing_scholars.get(other_surname.lower()) or scholar_id(other_surname, other_initial)
            acc.add_edge(
                "engages_with",
                sid,
                oid,
                {"stance": ew.get("stance", "cites"), "scope": topic, "note": ew.get("note", ""), "needs_review": True},
            )
    return True, "ok"


def process_one(args: tuple[Path, str]) -> tuple[Path, dict[str, Any] | None, str]:
    """Worker: read file + call LLM. Returns (path, payload_or_None, status)."""
    fp, api_key = args
    text = read_file_text(fp)
    if text is None:
        return fp, None, "skip:unsupported"
    if text.startswith("__ERROR__:"):
        return fp, None, f"error:read:{text[10:][:120]}"
    if len(text.strip()) < 200:
        return fp, None, "skip:too_short"
    payload, err = call_kimi(api_key, text, fp.name)
    if payload is None:
        return fp, None, f"error:llm:{err[:160]}"
    return fp, payload, "ok"


def log_line(msg: str) -> None:
    print(msg, flush=True)


def write_failure(fp: Path, status: str) -> None:
    FAILURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FAILURE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"file": str(fp), "status": status}, ensure_ascii=False) + "\n")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract scholar patches from local academic library.")
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="Skip files already in existing JSONL outputs.")
    ap.add_argument("--include-pdf", action="store_true", help="Include PDFs (default: skip).")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--checkpoint-every", type=int, default=20)
    ap.add_argument("--confidence-threshold", type=float, default=0.5)
    args = ap.parse_args(argv)

    by_cat = inventory(LIBRARY_ROOT)
    total_inv = sum(len(v) for v in by_cat.values())
    log_line(f"Inventory: {total_inv} files across {len(by_cat)} categories")
    for cat, paths in sorted(by_cat.items()):
        kinds = {".md": 0, ".txt": 0, ".pdf": 0}
        for p in paths:
            kinds[p.suffix.lower()] = kinds.get(p.suffix.lower(), 0) + 1
        log_line(f"  {cat}: {len(paths)} ({kinds})")

    if total_inv == 0:
        return 2

    # Cross-source dedup: load surname->id from prior JSONLs + KG snapshot.
    kg_scholars = load_existing_kg_scholars(PROJECT_ROOT / "data" / "kg" / "nodes.jsonl")
    prior_surnames, processed_basenames = load_prior_patches(OUTPUT_JSONL, WEB_JSONL)
    # Merge: prior_surnames takes priority over kg_scholars only when there's no entry.
    existing_scholars = dict(kg_scholars)
    for k, v in prior_surnames.items():
        existing_scholars.setdefault(k, v)
    log_line(
        f"Loaded {len(kg_scholars)} KG modern scholars, "
        f"{len(prior_surnames)} prior-patch scholars, "
        f"{len(processed_basenames)} basenames already processed."
    )

    skip_pdf = not args.include_pdf
    files = prioritize(by_cat, skip_pdf=skip_pdf, processed=processed_basenames if args.resume else set())
    files = files[: args.max_files]
    log_line(f"\nWill process {len(files)} files (skip_pdf={skip_pdf}, resume={args.resume}, max={args.max_files})")

    if args.dry_run:
        for fp in files[:30]:
            log_line(f"  - {fp.relative_to(LIBRARY_ROOT)}")
        if len(files) > 30:
            log_line(f"  ... and {len(files) - 30} more")
        return 0

    api_key = load_fireworks_key()
    if not api_key:
        log_line("FIREWORKS_API_KEY not found.")
        return 1

    acc = PatchAccumulator()
    results: list[FileResult] = []
    file_status: dict[str, str] = {}
    payloads_collected = 0
    last_checkpoint = 0

    log_line(f"Starting extraction with concurrency={args.concurrency}, checkpoint_every={args.checkpoint_every}")
    start = time.time()
    tasks = [(fp, api_key) for fp in files]

    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        future_to_fp = {ex.submit(process_one, t): t[0] for t in tasks}
        done_count = 0
        for fut in cf.as_completed(future_to_fp):
            fp = future_to_fp[fut]
            done_count += 1
            try:
                rfp, payload, status = fut.result()
            except Exception as e:
                status = f"error:exception:{e}"
                payload = None
            file_status[fp.name] = status
            elapsed = time.time() - start
            rate = done_count / elapsed if elapsed > 0 else 0
            if payload is None:
                log_line(f"[{done_count}/{len(files)}] {fp.name} -> {status}  ({rate:.2f} f/s)")
                write_failure(fp, status)
                results.append(FileResult(fp, status.split(":")[0], status))
                continue
            added, reason = integrate_extraction(
                acc, fp, payload, existing_scholars, confidence_threshold=args.confidence_threshold
            )
            if not added:
                status = f"skip:{reason}"
                file_status[fp.name] = status
                write_failure(fp, status)
                log_line(f"[{done_count}/{len(files)}] {fp.name} -> {status}  ({rate:.2f} f/s)")
                results.append(FileResult(fp, "skip", reason))
                continue
            payloads_collected += 1
            results.append(FileResult(fp, "ok", "", payload=payload))
            log_line(f"[{done_count}/{len(files)}] {fp.name} -> ok  ({rate:.2f} f/s)")

            if payloads_collected - last_checkpoint >= args.checkpoint_every:
                counts = acc.write_append(OUTPUT_JSONL)
                last_checkpoint = payloads_collected
                log_line(f"  >>> checkpoint: wrote {sum(counts.values())} new patches ({counts})")
                # reset acc to avoid re-writing same patches; existing JSONL is the source of truth
                acc = PatchAccumulator()

    # Final flush
    counts = acc.write_append(OUTPUT_JSONL)
    log_line(f"\nFinal flush: {counts}")

    # Build report
    write_report(results, file_status, total_inv)
    log_line(f"\nDone. Report: {OUTPUT_REPORT}")
    return 0


def write_report(results: list[FileResult], file_status: dict[str, str], total_inv: int) -> None:
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    # Re-read the final JSONL to compute aggregates over ALL prior + current patches
    by_kind: dict[str, int] = {}
    scholars: dict[str, str] = {}  # node_id -> label
    primary_source_counts: dict[str, int] = {}
    for line in OUTPUT_JSONL.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = obj.get("kind", "?")
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind == "scholar":
            scholars[obj.get("node_id") or "?"] = obj.get("label") or "?"
        if kind == "edge" and obj.get("edge_type") == "cites_primary_source":
            tgt = obj.get("target_id") or ""
            md = obj.get("metadata") or {}
            raw = md.get("raw_citation") if isinstance(md, dict) else None
            key = raw or tgt
            primary_source_counts[key] = primary_source_counts.get(key, 0) + 1

    top10 = sorted(primary_source_counts.items(), key=lambda x: -x[1])[:10]

    # Summarise file outcomes
    status_counts: dict[str, int] = {}
    failures: list[tuple[str, str]] = []
    for fp, st in file_status.items():
        bucket = st.split(":")[0] if ":" in st else st
        status_counts[bucket] = status_counts.get(bucket, 0) + 1
        if st.startswith("error") or st.startswith("skip:low"):
            failures.append((fp, st))

    with OUTPUT_REPORT.open("w", encoding="utf-8") as f:
        f.write("# Track B1 — Library extraction report\n\n")
        f.write(f"- Library root: `{LIBRARY_ROOT}`\n")
        f.write(f"- Files inventoried: {total_inv}\n")
        f.write(f"- Files attempted this run: {len(file_status)}\n")
        for k, v in sorted(status_counts.items()):
            f.write(f"  - {k}: {v}\n")
        f.write("\n## Patches in `from_local_library.jsonl` (cumulative)\n\n")
        for k in ("scholar", "scholarly_work", "scholarly_argument", "edge"):
            f.write(f"- {k}: {by_kind.get(k, 0)}\n")
        f.write(f"\n## Scholars ({len(scholars)})\n\n")
        for sid, label in sorted(scholars.items(), key=lambda x: x[1].lower()):
            f.write(f"- `{sid}` — {label}\n")
        f.write("\n## Top 10 most-cited primary sources\n\n")
        for src, n in top10:
            f.write(f"- {n}× `{src}`\n")
        f.write(f"\n## Failures / low-confidence this run ({len(failures)})\n\n")
        for fp, st in failures[:200]:
            f.write(f"- `{fp}` — {st}\n")
        if len(failures) > 200:
            f.write(f"- ... and {len(failures) - 200} more\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
