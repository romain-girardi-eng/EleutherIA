from __future__ import annotations

import copy
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


def test_manifestation_bound_entries_are_concrete_and_reproducible() -> None:
    mod = _load_module()
    entries = mod.publication_entries_to_bibtex(
        {
            "id": "pub_work_level",
            "label": "A Work-Level Title",
            "type": "publication",
            "metadata": {
                "author": "Author Example",
                "title": "A Work-Level Title",
                "type": "book",
                "bibtex_manifestations": [
                    {
                        "manifestation_id": "manifestation_one",
                        "bibtex_key": "example-1980-one",
                        "year": 1980,
                        "publisher": "Publisher One",
                        "address": "London",
                    },
                    {
                        "manifestation_id": "manifestation_two",
                        "bibtex_key": "example-2006-two",
                        "year": 2006,
                        "publisher": "Publisher Two",
                        "address": "Chicago",
                    },
                ],
            },
        }
    )

    assert len(entries) == 2
    assert [manifestation for _entry, _missing, manifestation in entries] == [
        "manifestation_one",
        "manifestation_two",
    ]
    assert all(missing == [] for _entry, missing, _manifestation in entries)
    assert "publisher = {Publisher One}" in entries[0][0]
    assert "manifestation: manifestation_one" in entries[0][0]
    assert "publisher = {Publisher Two}" in entries[1][0]


def test_export_and_companion_report_are_deeply_pure() -> None:
    mod = _load_module()
    node = {
        "id": "pub_pure_work",
        "label": "Pure Work",
        "type": "publication",
        "metadata": {
            "author": "Author Example",
            "year": 1980,
            "type": "book",
            "nested_unrelated": {"values": [1, {"keep": True}]},
            "bibtex_manifestations": [
                {
                    "manifestation_id": "pure_manifestation",
                    "bibtex_key": "pure-1980",
                    "publisher": "Pure Press",
                    "year": 1980,
                    "nested": {"must_remain": ["byte", "stable"]},
                }
            ],
        },
    }
    before = copy.deepcopy(node)
    metadata_identity = id(node["metadata"])
    manifestation_identity = id(node["metadata"]["bibtex_manifestations"][0])

    entries = mod.publication_entries_to_bibtex(node)
    canonical_text, _report = mod.build_publication_export([node])
    companion = mod.build_companion_report(
        [node], canonical_text, generation_mode="purity_test"
    )
    clone_entries = mod.publication_entries_to_bibtex(copy.deepcopy(node))

    assert entries == clone_entries
    assert companion["entries_written"] == 1
    assert node == before
    assert id(node["metadata"]) == metadata_identity
    assert id(node["metadata"]["bibtex_manifestations"][0]) == (
        manifestation_identity
    )
    assert "title" not in node["metadata"]
