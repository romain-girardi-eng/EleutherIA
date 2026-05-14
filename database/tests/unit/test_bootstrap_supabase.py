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

    citation_node_ids = {row[1] for row in payload.passage_citations}
    assert citation_node_ids == {
        "passage_alex_fat_10",
        "argument_future_contingents",
    }
