"""
EleutherIA Database Package

Ancient Greek/Latin texts corpus for the EleutherIA knowledge graph.
"""

from eleutheria_database.models.works import AncientWork, Passage, PassageCitation
from eleutheria_database.services.db import DatabaseService

__version__ = "2.0.0"
__all__ = [
    "DatabaseService",
    "AncientWork",
    "Passage",
    "PassageCitation",
]
