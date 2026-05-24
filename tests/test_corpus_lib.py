import json
from pathlib import Path

from scripts.corpus_lib import canonical_dumps, read_jsonl, write_jsonl


def test_canonical_dumps_is_sorted_and_compact():
    assert canonical_dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_dumps_preserves_unicode():
    assert canonical_dumps({"t": "προαίρεσις"}) == '{"t":"προαίρεσις"}'


def test_write_then_read_roundtrip(tmp_path: Path):
    rows = [{"id": "b"}, {"id": "a"}]
    p = tmp_path / "out.jsonl"
    write_jsonl(p, rows)
    assert p.read_text(encoding="utf-8") == '{"id":"b"}\n{"id":"a"}\n'
    assert read_jsonl(p) == rows
