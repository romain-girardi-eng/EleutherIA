from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_publications_bibtex.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("export_publications_bibtex", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_publication_to_bibtex_normalizes_string_metadata() -> None:
    mod = _load_module()
    entry, missing = mod.publication_to_bibtex(
        {
            "id": "pub_bobzien_1998",
            "label": "The Inadvertent Conception",
            "type": "publication",
            "metadata": (
                '{"author":"Susanne Bobzien","year":1998,'
                '"journal":"Phronesis","pages":"133-180",'
                '"doi":"10.2307/4182566","bibtex_key":"bobzien1998"}'
            ),
        }
    )

    assert missing == []
    assert entry.startswith("@article{bobzien1998")
    assert "doi = {10.2307/4182566}" in entry
    assert "journal = {Phronesis}" in entry


def test_publication_to_bibtex_reports_missing_required_fields() -> None:
    mod = _load_module()
    _entry, missing = mod.publication_to_bibtex(
        {"id": "pub_missing", "label": "Untitled", "type": "publication", "metadata": {}}
    )
    assert missing == ["author", "year"]
