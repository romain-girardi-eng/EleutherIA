from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import asyncpg
import pytest
from scripts.deploy_data_staged import (
    STAGING_SUFFIX,
    TARGET_TABLES,
    generate_swap_sql,
    inventory_dependencies,
)

ROOT = Path(__file__).resolve().parents[3]


def _docker_status() -> tuple[bool, str]:
    if shutil.which("docker") is None:
        return False, "commande docker absente"
    probe = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if probe.returncode:
        detail = (probe.stderr or probe.stdout).strip().splitlines()
        return (
            False,
            f"daemon Docker indisponible: {detail[-1] if detail else 'erreur inconnue'}",
        )
    return True, ""


DOCKER_AVAILABLE, DOCKER_SKIP_REASON = _docker_status()
pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason=DOCKER_SKIP_REASON,
)


SCHEMA_SQL = """
CREATE SCHEMA free_will;

CREATE TABLE free_will.ancient_works (
    work_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kg_work_id text,
    canonical_id text NOT NULL UNIQUE,
    title text NOT NULL,
    author text NOT NULL,
    language text NOT NULL,
    period text,
    school text,
    source text,
    cts_urn text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    metadata jsonb,
    updated_at timestamptz DEFAULT now()
);
CREATE TABLE free_will.kg_nodes (
    node_id text PRIMARY KEY,
    label text NOT NULL,
    type text NOT NULL,
    description text,
    period text,
    alternative_names jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    updated_at timestamptz DEFAULT now()
);
CREATE TABLE free_will.passages (
    passage_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id uuid NOT NULL REFERENCES free_will.ancient_works(work_id) ON DELETE CASCADE,
    canonical_ref text NOT NULL,
    cts_urn text,
    book text,
    chapter text,
    section text,
    sequence_number bigint NOT NULL,
    text_content text NOT NULL,
    passage_role text NOT NULL DEFAULT 'original',
    source_passage_id uuid REFERENCES free_will.passages(passage_id),
    char_length integer,
    word_count integer,
    citation_hierarchy jsonb,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(text_content, ''))
    ) STORED
);
CREATE INDEX passages_search_vector_gin
    ON free_will.passages USING gin(search_vector);
CREATE TABLE free_will.kg_edges (
    edge_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id text NOT NULL REFERENCES free_will.kg_nodes(node_id) ON DELETE CASCADE,
    target_id text NOT NULL REFERENCES free_will.kg_nodes(node_id) ON DELETE CASCADE,
    relation text NOT NULL,
    weight double precision DEFAULT 1.0,
    metadata jsonb DEFAULT '{}'::jsonb
);
CREATE TABLE free_will.passage_citations (
    citation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_id uuid NOT NULL REFERENCES free_will.passages(passage_id) ON DELETE CASCADE,
    kg_node_id text NOT NULL REFERENCES free_will.kg_nodes(node_id),
    citation_type text,
    confidence double precision,
    notes text
);
CREATE UNIQUE INDEX citations_unique
    ON free_will.passage_citations(passage_id, kg_node_id, citation_type)
    NULLS NOT DISTINCT;

CREATE TABLE free_will.passage_relationships (
    relationship_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_passage_id uuid NOT NULL REFERENCES free_will.passages(passage_id) ON DELETE CASCADE,
    target_passage_id uuid NOT NULL REFERENCES free_will.passages(passage_id) ON DELETE CASCADE
);
CREATE TABLE free_will.textual_variants (
    variant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_id uuid NOT NULL REFERENCES free_will.passages(passage_id) ON DELETE CASCADE,
    kg_node_id text REFERENCES free_will.kg_nodes(node_id) ON DELETE SET NULL
);
CREATE TABLE free_will.oga_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id uuid NOT NULL REFERENCES free_will.ancient_works(work_id) ON DELETE CASCADE,
    passage_id uuid REFERENCES free_will.passages(passage_id) ON DELETE SET NULL
);

CREATE VIEW free_will.passage_search AS
SELECT p.passage_id, p.canonical_ref, w.canonical_id
FROM free_will.passages p
JOIN free_will.ancient_works w ON w.work_id = p.work_id;

CREATE FUNCTION free_will.touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END
$$;
CREATE TRIGGER ancient_works_touch BEFORE UPDATE ON free_will.ancient_works
FOR EACH ROW EXECUTE FUNCTION free_will.touch_updated_at();

ALTER TABLE free_will.kg_nodes ENABLE ROW LEVEL SECURITY;
CREATE POLICY kg_nodes_read ON free_will.kg_nodes FOR SELECT USING (true);
"""


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=check)


@pytest.fixture(scope="module")
def postgres_url():
    name = f"eleutheria-staged-{uuid.uuid4().hex[:12]}"
    started = _run(
        "docker",
        "run",
        "--detach",
        "--rm",
        "--name",
        name,
        "-e",
        "POSTGRES_PASSWORD=eleutheria-test",
        "-p",
        "127.0.0.1::5432",
        "postgres:16-alpine",
        check=False,
    )
    if started.returncode:
        pytest.skip(
            f"impossible de lancer postgres:16-alpine: {started.stderr.strip()}"
        )
    try:
        port_result = _run("docker", "port", name, "5432/tcp")
        port = port_result.stdout.strip().rsplit(":", 1)[1]
        url = f"postgresql://postgres:eleutheria-test@127.0.0.1:{port}/postgres"
        # The postgres entrypoint boots a TEMPORARY server during initdb, stops
        # it, then starts the real one: pg_isready can succeed against the
        # temporary server and the first host connection then races the
        # restart ("unexpected connection_lost"). Wait for the SECOND
        # "ready to accept connections" in the logs, then prove a real host
        # connection.
        deadline = time.monotonic() + 45
        while True:
            logs = _run("docker", "logs", name, check=False)
            combined = logs.stdout + logs.stderr
            if combined.count("database system is ready to accept connections") >= 2:
                break
            if time.monotonic() >= deadline:
                pytest.fail("PostgreSQL jetable n'est pas devenu prêt en 45 s")
            time.sleep(0.3)

        async def _probe() -> None:
            conn = await asyncpg.connect(url, timeout=5)
            await conn.close()

        while True:
            try:
                asyncio.run(_probe())
                break
            except OSError, asyncpg.PostgresError, ConnectionError:
                if time.monotonic() >= deadline:
                    pytest.fail("connexion hôte au PostgreSQL jetable impossible")
                time.sleep(0.3)
        yield url
    finally:
        _run("docker", "rm", "--force", name, check=False)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _fixture_data(root: Path, *, extra_nodes: int = 0) -> Path:
    passage_id = "00000000-0000-0000-0000-000000000101"
    nodes = [
        {
            "id": "passage_new",
            "label": "New passage 1",
            "type": "passage",
            "description": "new corpus text",
            "metadata": {
                "db_passage_id": passage_id,
                "canonical_ref": "1.1",
                "cts_urn": "urn:cts:test:work_a:1.1",
                "work_canonical_id": "work_a",
                "work_title": "Work A",
                "author": "Author A",
                "language": "eng",
            },
        },
        {
            "id": "concept_new",
            "label": "New concept",
            "type": "concept",
            "description": "new",
            "metadata": {},
        },
    ]
    nodes.extend(
        {
            "id": f"bulk_{index:05d}",
            "label": f"Bulk {index}",
            "type": "concept",
            "description": "bulk",
            "metadata": {},
        }
        for index in range(extra_nodes)
    )
    _write_jsonl(root / "kg/nodes.jsonl", nodes)
    _write_jsonl(
        root / "kg/edges.jsonl",
        [
            {
                "source": "passage_new",
                "target": "concept_new",
                "relation": "discusses",
                "metadata": {},
            }
        ],
    )
    _write_jsonl(
        root / "corpus/manifest.jsonl",
        [
            {
                "canonical_id": "work_a",
                "title": "Work A",
                "author": "Author A",
                "language": "eng",
            }
        ],
    )
    _write_jsonl(
        root / "corpus/passages.jsonl",
        [
            {
                "passage_id": passage_id,
                "work_canonical_id": "work_a",
                "canonical_ref": "1.1",
                "cts_urn": "urn:cts:test:work_a:1.1",
                "sequence_number": 1,
                "text_content": "new corpus text",
            }
        ],
    )
    _write_jsonl(
        root / "corpus/citations.jsonl",
        [
            {
                "passage_id": passage_id,
                "kg_node_id": "passage_new",
                "citation_type": "snapshot_passage_node",
                "confidence": 1.0,
            }
        ],
    )
    return root


def _deploy(url: str, data_root: Path | None = None, *extra: str):
    command = [
        sys.executable,
        str(ROOT / "scripts/deploy_data_staged.py"),
        "--database-url",
        url,
        *extra,
    ]
    if data_root is not None:
        command.extend(["--data-root", str(data_root)])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


async def _scalar(url: str, sql: str):
    conn = await asyncpg.connect(url)
    try:
        return await conn.fetchval(sql)
    finally:
        await conn.close()


async def _seed_old_generation(url: str) -> None:
    conn = await asyncpg.connect(url)
    try:
        await conn.execute(SCHEMA_SQL)
        await conn.execute(
            "INSERT INTO free_will.kg_nodes(node_id,label,type) "
            "VALUES ('old_node','Old node','concept')"
        )
        await conn.execute(
            "INSERT INTO free_will.ancient_works"
            "(work_id,canonical_id,title,author,language) VALUES "
            "('00000000-0000-0000-0000-000000000001','old_work','Old','Old','eng')"
        )
        await conn.execute(
            "INSERT INTO free_will.passages"
            "(passage_id,work_id,canonical_ref,sequence_number,text_content) VALUES "
            "('00000000-0000-0000-0000-000000000002',"
            "'00000000-0000-0000-0000-000000000001','old',1,'old text')"
        )
        await conn.execute(
            "INSERT INTO free_will.passage_citations"
            "(citation_id,passage_id,kg_node_id,citation_type) VALUES "
            "('00000000-0000-0000-0000-000000000003',"
            "'00000000-0000-0000-0000-000000000002','old_node','old')"
        )
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_staged_deploy_kill_atomic_swap_and_rollback(postgres_url, tmp_path):
    await _seed_old_generation(postgres_url)
    small_data = _fixture_data(tmp_path / "small")

    dry_run = _deploy(postgres_url, small_data, "--dry-run")
    assert dry_run.returncode == 0, dry_run.stdout + dry_run.stderr
    assert json.loads(dry_run.stdout.strip().splitlines()[-1])["status"] == "verified"
    assert await _scalar(
        postgres_url, "SELECT node_id = 'old_node' FROM free_will.kg_nodes"
    )
    assert await _scalar(
        postgres_url, "SELECT to_regclass('free_will.kg_nodes__staging') IS NULL"
    )

    large_data = _fixture_data(tmp_path / "large", extra_nodes=12_000)
    command = [
        sys.executable,
        str(ROOT / "scripts/deploy_data_staged.py"),
        "--database-url",
        postgres_url,
        "--data-root",
        str(large_data),
        "--batch-size",
        "1",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail("le chargement long s'est terminé avant le kill de test")
        try:
            staging_exists = await _scalar(
                postgres_url,
                "SELECT to_regclass('free_will.kg_nodes__staging') IS NOT NULL",
            )
            staged_count = (
                await _scalar(
                    postgres_url,
                    "SELECT count(*) FROM free_will.kg_nodes__staging",
                )
                if staging_exists
                else 0
            )
        except asyncpg.PostgresError:
            staged_count = 0
        if staged_count >= 10:
            break
        await asyncio.sleep(0.05)
    else:
        process.kill()
        pytest.fail("aucun lot staging visible avant le délai de 30 s")
    process.kill()
    process.wait(timeout=10)
    assert await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes") == 1
    assert await _scalar(
        postgres_url, "SELECT node_id = 'old_node' FROM free_will.kg_nodes"
    )

    deploy = _deploy(postgres_url, small_data)
    assert deploy.returncode == 0, deploy.stdout + deploy.stderr
    summary = json.loads(deploy.stdout.strip().splitlines()[-1])
    assert summary["status"] == "deployed"
    assert await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes") == 2
    assert (
        await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes__old") == 1
    )
    assert (
        await _scalar(postgres_url, "SELECT count(*) FROM free_will.passage_search")
        == 1
    )
    assert await _scalar(
        postgres_url,
        "SELECT relrowsecurity FROM pg_class WHERE oid='free_will.kg_nodes'::regclass",
    )

    # Prepare a second shadow set, start the generated transactional swap, then
    # terminate its backend after DDL has begun.  PostgreSQL must restore every
    # name and the prior __old generation together.
    prep = await asyncpg.connect(postgres_url)
    try:
        for name in TARGET_TABLES:
            await prep.execute(
                f'CREATE TABLE free_will."{name}{STAGING_SUFFIX}" '
                f'(LIKE free_will."{name}" INCLUDING ALL)'
            )
    finally:
        await prep.close()

    worker = await asyncpg.connect(postgres_url, statement_cache_size=0)
    control = await asyncpg.connect(postgres_url)
    try:
        inventory = await inventory_dependencies(worker, "free_will")
        statements = generate_swap_sql("free_will", inventory)
        backend_pid = await worker.fetchval("SELECT pg_backend_pid()")
        renamed = 0
        for statement in statements:
            await worker.execute(statement)
            if "RENAME TO" in statement:
                renamed += 1
                if renamed == 2:
                    break
        assert await control.fetchval("SELECT pg_terminate_backend($1)", backend_pid)
        # The termination races the protocol state: depending on timing the
        # dead connection surfaces as PostgresConnectionError, a raw
        # ConnectionError/OSError, or asyncpg's InternalClientError ("another
        # operation is in progress"), and the first SELECT may even still
        # succeed before the backend actually dies. Retry until the
        # connection provably fails.
        dead_errors = (
            asyncpg.PostgresConnectionError,
            asyncpg.exceptions.InternalClientError,
            ConnectionError,
            OSError,
        )
        deadline = time.monotonic() + 10
        while True:
            try:
                await worker.execute("SELECT 1")
            except dead_errors:
                break
            if time.monotonic() >= deadline:
                pytest.fail("worker connection survived pg_terminate_backend")
            await asyncio.sleep(0.1)
    finally:
        await control.close()
        if not worker.is_closed():
            await worker.close()

    assert await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes") == 2
    assert (
        await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes__old") == 1
    )
    assert await _scalar(
        postgres_url, "SELECT to_regclass('free_will.kg_nodes__staging') IS NOT NULL"
    )

    rollback = _deploy(postgres_url, None, "--rollback")
    assert rollback.returncode == 0, rollback.stdout + rollback.stderr
    assert (
        json.loads(rollback.stdout.strip().splitlines()[-1])["status"] == "rolled_back"
    )
    assert await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes") == 1
    assert await _scalar(
        postgres_url, "SELECT node_id = 'old_node' FROM free_will.kg_nodes"
    )
    assert (
        await _scalar(postgres_url, "SELECT count(*) FROM free_will.kg_nodes__old") == 2
    )
    assert (
        await _scalar(postgres_url, "SELECT count(*) FROM free_will.passage_search")
        == 1
    )
