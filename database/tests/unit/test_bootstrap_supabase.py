from database.scripts.bootstrap_supabase import SnapshotData, build_import_payload


def test_build_import_payload_derives_passages_and_citations():
    snapshot = SnapshotData(
        nodes=[
            {
                "id": "work_alex_de_fato",
                "label": "Alexander of Aphrodisias, De Fato",
                "type": "work",
                "description": "Work node",
                "metadata": {},
            },
            {
                "id": "argument_future_contingents",
                "label": "Future contingents",
                "type": "argument",
                "description": "Argument node",
                "metadata": {},
            },
            {
                "id": "passage_alex_fat_10",
                "label": "Alexander of Aphrodisias, De Fato, 10",
                "type": "passage",
                "description": "Greek passage text",
                "period": "Roman Imperial",
                "metadata": {
                    "author": "Alexander of Aphrodisias",
                    "canonical_ref": "De Fato 10",
                    "language": "grc",
                    "work_canonical_id": "tlg0732.tlg014",
                    "work_title": "De Fato",
                },
            },
        ],
        edges=[
            {
                "source": "passage_alex_fat_10",
                "target": "work_alex_de_fato",
                "relation": "part_of",
                "metadata": {},
            },
            {
                "source": "argument_future_contingents",
                "target": "passage_alex_fat_10",
                "relation": "evidenced_by",
                "metadata": {"confidence": 0.8},
            },
        ],
    )

    payload = build_import_payload(snapshot)

    assert len(payload.kg_nodes) == 3
    assert len(payload.kg_edges) == 2
    assert len(payload.ancient_works) == 1
    assert len(payload.passages) == 1
    assert len(payload.passage_citations) == 2

    work = payload.ancient_works[0]
    assert work[2] == "tlg0732_tlg014"
    assert work[3] == "De Fato"
    assert work[4] == "Alexander of Aphrodisias"
    assert work[5] == "grc"

    passage = payload.passages[0]
    assert passage[2] == "De Fato 10"
    assert passage[6] == "10"
    assert passage[8] == "Greek passage text"
    assert passage[12:] == ("original", None)

    citation_node_ids = {row[1] for row in payload.passage_citations}
    assert citation_node_ids == {
        "passage_alex_fat_10",
        "argument_future_contingents",
    }


def test_build_import_payload_preserves_translation_role_and_source_uuid():
    original_uuid = "00000000-0000-0000-0000-000000000001"
    translation_uuid = "00000000-0000-0000-0000-000000000002"
    work = {
        "id": "work_test",
        "label": "Test work",
        "type": "work",
        "metadata": {},
    }
    original = {
        "id": "passage_test_grc_1",
        "label": "Test Greek 1",
        "type": "passage",
        "description": "Greek text",
        "metadata": {
            "author": "Pseudo-Author",
            "canonical_ref": "1",
            "db_passage_id": original_uuid,
            "language": "grc",
            "passage_role": "original",
            "work_canonical_id": "test_work",
            "work_title": "Test work",
        },
    }
    translation = {
        "id": "passage_test_eng_1",
        "label": "Test English 1",
        "type": "passage",
        "description": "English text",
        "metadata": {
            "author": "Pseudo-Author",
            "canonical_ref": "1",
            "db_passage_id": translation_uuid,
            "language": "eng",
            "passage_role": "translation",
            "source_passage_id": original_uuid,
            "translation_type": "published_human",
            "work_canonical_id": "test_work",
            "work_title": "Test work",
        },
    }
    snapshot = SnapshotData(
        nodes=[work, translation, original],
        edges=[
            {
                "source": "passage_test_eng_1",
                "target": "work_test",
                "relation": "part_of",
                "metadata": {},
            },
            {
                "source": "passage_test_grc_1",
                "target": "work_test",
                "relation": "part_of",
                "metadata": {},
            },
        ],
    )

    payload = build_import_payload(snapshot)

    assert str(payload.passages[0][0]) == original_uuid
    by_id = {str(row[0]): row for row in payload.passages}
    assert by_id[original_uuid][12:] == ("original", None)
    assert by_id[translation_uuid][12] == "translation"
    assert str(by_id[translation_uuid][13]) == original_uuid


def test_build_import_payload_preserves_ancient_translation_without_inventing_source():
    latin_uuid = "00000000-0000-0000-0000-000000000003"
    work = {
        "id": "work_irenaeus_book3",
        "label": "Irenaeus, Adversus haereses III",
        "type": "work",
        "metadata": {},
    }
    latin = {
        "id": "passage_irenaeus_iii_20_3_lat",
        "label": "Irenaeus, AH III.20.3, ancient Latin",
        "type": "passage",
        "description": "Ancient Latin version.",
        "metadata": {
            "author": "Irenaeus of Lyon",
            "canonical_ref": "Adversus haereses III.20.3",
            "db_passage_id": latin_uuid,
            "language": "lat",
            "passage_role": "translation",
            "translation_type": "ancient_human_literal",
            "source_passage_status": "lost_continuous_greek_not_mapped",
            "work_canonical_id": "irenaeus_ah_iii_lat",
            "work_title": "Adversus haereses III",
        },
    }
    snapshot = SnapshotData(
        nodes=[work, latin],
        edges=[
            {
                "source": latin["id"],
                "target": work["id"],
                "relation": "part_of",
                "metadata": {},
            }
        ],
    )

    payload = build_import_payload(snapshot)

    assert len(payload.passages) == 1
    assert str(payload.passages[0][0]) == latin_uuid
    assert payload.passages[0][12:] == ("translation", None)
