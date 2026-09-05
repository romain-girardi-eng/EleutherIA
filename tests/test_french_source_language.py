"""The actual SQL schema and JSON RPCs must accept French source witnesses."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_french_language_migration_is_atomic_and_preserves_existing_languages():
    sql = (ROOT / 'database/migrations/20260906_01_french_source_language.sql').read_text()
    assert 'BEGIN;' in sql and 'COMMIT;' in sql
    assert "('grc', 'lat', 'eng', 'fra', 'hbo', 'ara')" in sql
    assert 'ALTER TABLE free_will.ancient_works' in sql
    assert 'public.search_passages(payload JSONB)' in sql
    assert 'public.search_passages_simple(payload JSONB)' in sql
    assert 'SECURITY INVOKER' in sql


def test_fresh_schema_and_rpc_filters_use_the_same_language_vocabulary():
    vocabulary = "('grc', 'lat', 'eng', 'fra', 'hbo', 'ara')"
    assert vocabulary in (ROOT / 'database/schema/schema.sql').read_text()
    assert (ROOT / 'database/schema/supabase_functions.sql').read_text().count(vocabulary) == 2
