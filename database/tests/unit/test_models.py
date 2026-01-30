"""Tests for Pydantic models."""

from uuid import uuid4

import pytest

from eleutheria_database.models.works import (
    AncientWork,
    Passage,
    PassageCitation,
)


class TestAncientWork:
    """Tests for AncientWork model."""

    def test_create_minimal(self):
        """Test creating work with minimal fields."""
        work = AncientWork(
            work_id=uuid4(),
            canonical_id="test_work",
            title="Test Work",
            author="Test Author",
            language="grc",
        )
        assert work.title == "Test Work"
        assert work.language == "grc"
        assert work.has_morphology is False

    def test_create_full(self):
        """Test creating work with all fields."""
        work = AncientWork(
            work_id=uuid4(),
            canonical_id="chrysippus_on_fate",
            title="On Fate",
            title_original="Περὶ εἱμαρμένης",
            author="Chrysippus",
            author_original="Χρύσιππος",
            language="grc",
            period="Hellenistic",
            date_composed="3rd c. BCE",
            school="Stoic",
            source="svf",
            cts_urn="urn:cts:greekLit:tlg0569.tlg001",
            citation_levels=["book", "section"],
            has_morphology=True,
        )
        assert work.school == "Stoic"
        assert work.citation_levels == ["book", "section"]


class TestPassage:
    """Tests for Passage model."""

    def test_create_passage(self):
        """Test creating a passage."""
        passage = Passage(
            passage_id=uuid4(),
            work_id=uuid4(),
            canonical_ref="3.191",
            sequence_number=1,
            text_content="τὸ ἐφ' ἡμῖν",
        )
        assert passage.canonical_ref == "3.191"
        assert passage.sequence_number == 1

    def test_passage_with_hierarchy(self):
        """Test passage with citation hierarchy."""
        passage = Passage(
            passage_id=uuid4(),
            work_id=uuid4(),
            canonical_ref="Matthew 5:3",
            book="Matthew",
            chapter="5",
            section="3",
            sequence_number=100,
            text_content="Μακάριοι οἱ πτωχοὶ τῷ πνεύματι",
            citation_hierarchy={"book": "Matthew", "chapter": "5", "verse": "3"},
        )
        assert passage.book == "Matthew"
        assert passage.citation_hierarchy["verse"] == "3"


class TestPassageCitation:
    """Tests for PassageCitation model."""

    def test_create_citation(self):
        """Test creating a citation link."""
        citation = PassageCitation(
            citation_id=uuid4(),
            passage_id=uuid4(),
            kg_node_id="stoic_determinism_001",
            citation_type="primary_source",
            confidence=0.95,
        )
        assert citation.confidence == 0.95
        assert citation.citation_type == "primary_source"

    def test_confidence_bounds(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            PassageCitation(
                citation_id=uuid4(),
                passage_id=uuid4(),
                kg_node_id="test",
                confidence=1.5,  # Invalid
            )
