#!/usr/bin/env python3
"""Atomically deploy the git KG and corpus mirrors through shadow tables.

The five serving tables remain untouched while ``__staging`` tables are
loaded and verified.  PostgreSQL transactional DDL then switches the complete
set in one transaction.  The previous generation is retained as ``__old`` so
``--rollback`` can swap it back; the next successful deploy replaces it.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database.scripts.bootstrap_supabase import (  # noqa: E402
    ImportTables,
    build_import_payload,
    load_snapshot,
)
from database.scripts.bootstrap_supabase import (  # noqa: E402
    import_payload as import_kg_payload,
)
from scripts.sync_corpus_to_db import (  # noqa: E402
    CorpusPayload,
    import_corpus_payload,
    load_corpus_payload,
)

TARGET_TABLES = (
    "kg_nodes",
    "kg_edges",
    "ancient_works",
    "passages",
    "passage_citations",
)
STAGING_SUFFIX = "__staging"
OLD_SUFFIX = "__old"
ADVISORY_LOCK_KEY = 0x454C455554484552  # "ELEUTHER" as a signed-safe bigint.
PARITY_VIOLATION_CLASSES = (
    "cts_urn_mismatch",
    "canonical_ref_mismatch",
    "missing_twin",
)
PARITY_BASELINE_PATH = REPO_ROOT / "data" / "audit" / "kg_corpus_parity_baseline.json"

# Source-level inventory kept alongside the runtime pg_catalog inventory.  It
# documents dependencies that SQL-language function bodies do not necessarily
# expose through pg_depend because their quoted bodies are parsed on execution.
SOURCE_DEPENDENCY_INVENTORY = {
    "external_foreign_keys": {
        "passage_relationships": ("passages",),
        "textual_variants": ("passages", "kg_nodes"),
        "oga_tokens": ("ancient_works", "passages"),
    },
    "views": {
        "passage_search": ("passages", "ancient_works"),
        "works_statistics": ("ancient_works",),
        "passages_statistics": ("passages",),
        "citation_statistics": ("passage_citations",),
        "oga_tokens_enriched": ("ancient_works",),
        "oga_work_statistics": ("ancient_works",),
    },
    "triggers": {
        "ancient_works": ("update_ancient_works_updated_at",),
        "kg_nodes": ("kg_nodes_bump_version",),
        "kg_edges": ("kg_edges_bump_version",),
        "passage_citations": ("passage_citations_bump_version",),
    },
    "fts": {
        "passages": (
            "search_vector generated column",
            "idx_passages_search_vector_gin",
            "free_will.f_unaccent(text)",
        ),
    },
    "functions_resolved_by_name": (
        "database/schema/supabase_public_api.sql",
        "database/schema/supabase_functions.sql",
        "database/migrations/20260514_01_supabase_rebuild_support.sql",
    ),
}


class StagedDeployError(RuntimeError):
    """Expected operational refusal with a concise message."""


class VerificationError(StagedDeployError):
    """Raised when the shadow generation is not safe to publish."""

    def __init__(self, message: str, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class ForeignKeyDependency:
    source_schema: str
    source_table: str
    name: str
    target_schema: str
    target_table: str
    definition: str
    validated: bool

    @property
    def source_is_target(self) -> bool:
        return self.source_table in TARGET_TABLES

    @property
    def target_is_target(self) -> bool:
        return self.target_table in TARGET_TABLES

    @property
    def internal(self) -> bool:
        return self.source_is_target and self.target_is_target

    @property
    def inbound(self) -> bool:
        return not self.source_is_target and self.target_is_target


@dataclass(frozen=True)
class ViewDependency:
    schema: str
    name: str
    kind: str
    definition: str


@dataclass(frozen=True)
class FunctionDependency:
    schema: str
    name: str
    identity_arguments: str
    definition: str


@dataclass(frozen=True)
class TriggerDependency:
    table: str
    name: str
    definition: str


@dataclass(frozen=True)
class PolicyDefinition:
    name: str
    permissive: bool
    command: str
    roles: tuple[str, ...]
    using: str | None
    check: str | None


@dataclass(frozen=True)
class GrantDefinition:
    grantee: str
    privilege: str
    grantable: bool


@dataclass(frozen=True)
class TableSecurity:
    table: str
    owner: str
    row_security: bool
    force_row_security: bool
    grants: tuple[GrantDefinition, ...] = ()
    policies: tuple[PolicyDefinition, ...] = ()


@dataclass
class DependencyInventory:
    foreign_keys: list[ForeignKeyDependency] = field(default_factory=list)
    views: list[ViewDependency] = field(default_factory=list)
    functions: list[FunctionDependency] = field(default_factory=list)
    triggers: list[TriggerDependency] = field(default_factory=list)
    security: dict[str, TableSecurity] = field(default_factory=dict)
    sequences: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    @property
    def outbound_foreign_keys(self) -> list[ForeignKeyDependency]:
        return [fk for fk in self.foreign_keys if fk.source_is_target]

    @property
    def inbound_foreign_keys(self) -> list[ForeignKeyDependency]:
        return [fk for fk in self.foreign_keys if fk.inbound]

    def summary(self) -> dict[str, Any]:
        return {
            "foreign_keys": {
                "internal_or_outbound": len(self.outbound_foreign_keys),
                "external_inbound": len(self.inbound_foreign_keys),
            },
            "views_rebound": [f"{view.schema}.{view.name}" for view in self.views],
            "functions_recreated": [
                f"{function.schema}.{function.name}({function.identity_arguments})"
                for function in self.functions
            ],
            "triggers_cloned": [
                f"{trigger.table}.{trigger.name}" for trigger in self.triggers
            ],
            "owned_sequences": self.sequences,
            "rls_tables": sorted(
                name for name, item in self.security.items() if item.row_security
            ),
        }


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def qualified(schema: str, table: str) -> str:
    return f"{quote_ident(schema)}.{quote_ident(table)}"


def table_name(base: str, suffix: str = "") -> str:
    return f"{base}{suffix}"


def temporary_constraint_name(name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    stem = name[: 63 - len("__stage_") - len(digest)]
    return f"{stem}__stage_{digest}"


def rewrite_fk_reference(
    definition: str,
    *,
    target_schema: str,
    target_table: str,
    suffix: str,
) -> str:
    """Point the REFERENCES clause at a suffixed copy of its target table."""

    schema_forms = (re.escape(target_schema), re.escape(quote_ident(target_schema)))
    table_forms = (re.escape(target_table), re.escape(quote_ident(target_table)))
    pattern = re.compile(
        r"(REFERENCES\s+)(?:(?:"
        + "|".join(schema_forms)
        + r")\.)?(?:"
        + "|".join(table_forms)
        + r")(?=\s*\()",
        re.IGNORECASE,
    )
    replacement = rf"\1{qualified(target_schema, target_table + suffix)}"
    rewritten, replacements = pattern.subn(replacement, definition, count=1)
    if replacements != 1:
        raise StagedDeployError(
            f"cannot rewrite FK reference {target_schema}.{target_table}: {definition}"
        )
    return rewritten


def rewrite_trigger_target(
    definition: str,
    *,
    schema: str,
    table: str,
    suffix: str,
) -> str:
    pattern = re.compile(
        rf"(\sON\s+){re.escape(qualified(schema, table))}(\s)",
        re.IGNORECASE,
    )
    rewritten, replacements = pattern.subn(
        rf"\1{qualified(schema, table + suffix)}\2", definition, count=1
    )
    if replacements != 1:
        # pg_get_triggerdef(..., true) may choose unquoted identifiers.
        pattern = re.compile(
            rf"(\sON\s+)(?:{re.escape(schema)}\.)?{re.escape(table)}(\s)",
            re.IGNORECASE,
        )
        rewritten, replacements = pattern.subn(
            rf"\1{qualified(schema, table + suffix)}\2", definition, count=1
        )
    if replacements != 1:
        raise StagedDeployError(
            f"cannot rewrite trigger target {schema}.{table}: {definition}"
        )
    return rewritten


def _without_not_valid(definition: str) -> str:
    return re.sub(r"\s+NOT\s+VALID\s*$", "", definition, flags=re.IGNORECASE)


def generate_swap_sql(
    schema: str,
    inventory: DependencyInventory,
    *,
    rollback: bool = False,
    lock_timeout_seconds: int = 10,
) -> list[str]:
    """Generate the complete transactional DDL sequence for deploy/rollback."""

    replacement_suffix = OLD_SUFFIX if rollback else STAGING_SUFFIX
    statements = [
        "BEGIN",
        f"SET LOCAL lock_timeout = '{max(1, lock_timeout_seconds)}s'",
        "LOCK TABLE "
        + ", ".join(qualified(schema, name) for name in TARGET_TABLES)
        + " IN ACCESS EXCLUSIVE MODE",
    ]

    for fk in inventory.inbound_foreign_keys:
        temp_name = temporary_constraint_name(fk.name)
        definition = rewrite_fk_reference(
            _without_not_valid(fk.definition),
            target_schema=fk.target_schema,
            target_table=fk.target_table,
            suffix=replacement_suffix,
        )
        source = qualified(fk.source_schema, fk.source_table)
        statements.extend(
            [
                f"ALTER TABLE {source} ADD CONSTRAINT {quote_ident(temp_name)} "
                f"{definition} NOT VALID",
                f"ALTER TABLE {source} VALIDATE CONSTRAINT {quote_ident(temp_name)}",
            ]
        )

    if not rollback:
        old_tables = ", ".join(
            qualified(schema, table_name(name, OLD_SUFFIX)) for name in TARGET_TABLES
        )
        statements.append(f"DROP TABLE IF EXISTS {old_tables}")

    for fk in inventory.inbound_foreign_keys:
        statements.append(
            f"ALTER TABLE {qualified(fk.source_schema, fk.source_table)} "
            f"DROP CONSTRAINT {quote_ident(fk.name)}"
        )

    if rollback:
        for name in TARGET_TABLES:
            statements.append(
                f"ALTER TABLE {qualified(schema, name)} "
                f"RENAME TO {quote_ident(table_name(name, STAGING_SUFFIX))}"
            )
        for name in TARGET_TABLES:
            statements.append(
                f"ALTER TABLE {qualified(schema, table_name(name, OLD_SUFFIX))} "
                f"RENAME TO {quote_ident(name)}"
            )
        for name in TARGET_TABLES:
            statements.append(
                f"ALTER TABLE {qualified(schema, table_name(name, STAGING_SUFFIX))} "
                f"RENAME TO {quote_ident(table_name(name, OLD_SUFFIX))}"
            )
    else:
        for name in TARGET_TABLES:
            statements.append(
                f"ALTER TABLE {qualified(schema, name)} "
                f"RENAME TO {quote_ident(table_name(name, OLD_SUFFIX))}"
            )
        for name in TARGET_TABLES:
            statements.append(
                f"ALTER TABLE {qualified(schema, table_name(name, STAGING_SUFFIX))} "
                f"RENAME TO {quote_ident(name)}"
            )

    for fk in inventory.inbound_foreign_keys:
        source = qualified(fk.source_schema, fk.source_table)
        statements.append(
            f"ALTER TABLE {source} RENAME CONSTRAINT "
            f"{quote_ident(temporary_constraint_name(fk.name))} TO {quote_ident(fk.name)}"
        )

    for view in inventory.views:
        if view.kind == "m":
            raise StagedDeployError(
                f"materialized view {view.schema}.{view.name} needs an explicit rebuild"
            )
        statements.append(
            f"CREATE OR REPLACE VIEW {qualified(view.schema, view.name)} AS\n"
            f"{view.definition}"
        )
    statements.extend(function.definition for function in inventory.functions)
    statements.append(
        "DO $$ BEGIN "
        "IF to_regclass('free_will.kg_version') IS NOT NULL THEN "
        "UPDATE free_will.kg_version SET version = version + 1, "
        "updated_at = now() WHERE id = 1; END IF; END $$"
    )
    statements.append("COMMIT")
    return statements


async def inventory_dependencies(
    conn: asyncpg.Connection, schema: str
) -> DependencyInventory:
    rows = await conn.fetch(
        """
        SELECT c.oid, c.relname, owner.rolname AS owner,
               c.relrowsecurity, c.relforcerowsecurity
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_roles owner ON owner.oid = c.relowner
        WHERE n.nspname = $1 AND c.relname = ANY($2::text[])
          AND c.relkind IN ('r', 'p')
        """,
        schema,
        list(TARGET_TABLES),
    )
    by_name = {row["relname"]: row for row in rows}
    missing = sorted(set(TARGET_TABLES) - set(by_name))
    if missing:
        raise StagedDeployError(f"missing live tables: {', '.join(missing)}")
    table_oids = [row["oid"] for row in rows]

    fk_rows = await conn.fetch(
        """
        SELECT sn.nspname AS source_schema, sc.relname AS source_table,
               con.conname AS name, tn.nspname AS target_schema,
               tc.relname AS target_table,
               pg_get_constraintdef(con.oid, false) AS definition,
               con.convalidated AS validated
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class sc ON sc.oid = con.conrelid
        JOIN pg_catalog.pg_namespace sn ON sn.oid = sc.relnamespace
        JOIN pg_catalog.pg_class tc ON tc.oid = con.confrelid
        JOIN pg_catalog.pg_namespace tn ON tn.oid = tc.relnamespace
        WHERE con.contype = 'f'
          AND (con.conrelid = ANY($1::oid[]) OR con.confrelid = ANY($1::oid[]))
        ORDER BY sn.nspname, sc.relname, con.conname
        """,
        table_oids,
    )
    foreign_keys = [ForeignKeyDependency(**dict(row)) for row in fk_rows]

    view_rows = await conn.fetch(
        """
        SELECT DISTINCT vn.nspname AS schema, view_class.relname AS name,
               view_class.relkind AS kind,
               pg_get_viewdef(view_class.oid, false) AS definition
        FROM pg_catalog.pg_depend dep
        JOIN pg_catalog.pg_rewrite rewrite ON rewrite.oid = dep.objid
        JOIN pg_catalog.pg_class view_class ON view_class.oid = rewrite.ev_class
        JOIN pg_catalog.pg_namespace vn ON vn.oid = view_class.relnamespace
        WHERE dep.refobjid = ANY($1::oid[])
          AND view_class.relkind IN ('v', 'm')
        ORDER BY vn.nspname, view_class.relname
        """,
        table_oids,
    )
    views = [ViewDependency(**dict(row)) for row in view_rows]

    function_rows = await conn.fetch(
        """
        SELECT DISTINCT pn.nspname AS schema, proc.proname AS name,
               pg_get_function_identity_arguments(proc.oid) AS identity_arguments,
               pg_get_functiondef(proc.oid) AS definition
        FROM pg_catalog.pg_depend dep
        JOIN pg_catalog.pg_proc proc ON proc.oid = dep.objid
        JOIN pg_catalog.pg_namespace pn ON pn.oid = proc.pronamespace
        WHERE dep.refobjid = ANY($1::oid[])
          AND dep.classid = 'pg_catalog.pg_proc'::regclass
        ORDER BY pn.nspname, proc.proname,
                 pg_get_function_identity_arguments(proc.oid)
        """,
        table_oids,
    )
    functions = [FunctionDependency(**dict(row)) for row in function_rows]

    trigger_rows = await conn.fetch(
        """
        SELECT c.relname AS table, trigger.tgname AS name,
               pg_get_triggerdef(trigger.oid, true) AS definition
        FROM pg_catalog.pg_trigger trigger
        JOIN pg_catalog.pg_class c ON c.oid = trigger.tgrelid
        WHERE trigger.tgrelid = ANY($1::oid[]) AND NOT trigger.tgisinternal
        ORDER BY c.relname, trigger.tgname
        """,
        table_oids,
    )
    triggers = [TriggerDependency(**dict(row)) for row in trigger_rows]

    sequence_rows = await conn.fetch(
        """
        SELECT table_class.relname AS table_name,
               sequence_class.relname AS sequence_name,
               dep.deptype AS dependency_type
        FROM pg_catalog.pg_depend dep
        JOIN pg_catalog.pg_class sequence_class ON sequence_class.oid = dep.objid
        JOIN pg_catalog.pg_class table_class ON table_class.oid = dep.refobjid
        WHERE dep.refobjid = ANY($1::oid[])
          AND sequence_class.relkind = 'S' AND dep.deptype IN ('a', 'i')
        ORDER BY table_class.relname, sequence_class.relname
        """,
        table_oids,
    )
    sequences: dict[str, list[dict[str, str]]] = {}
    for row in sequence_rows:
        sequences.setdefault(row["table_name"], []).append(
            {
                "name": row["sequence_name"],
                "kind": "identity" if row["dependency_type"] == "i" else "serial",
            }
        )

    security: dict[str, TableSecurity] = {}
    for name, table_row in by_name.items():
        grants_rows = await conn.fetch(
            """
            SELECT CASE WHEN acl.grantee = 0 THEN 'PUBLIC' ELSE role.rolname END AS grantee,
                   acl.privilege_type AS privilege,
                   acl.is_grantable AS grantable
            FROM pg_catalog.pg_class c
            CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) acl
            LEFT JOIN pg_catalog.pg_roles role ON role.oid = acl.grantee
            WHERE c.oid = $1
              AND c.relacl IS NOT NULL
              AND acl.grantee <> c.relowner
            ORDER BY grantee, privilege
            """,
            table_row["oid"],
        )
        policy_rows = await conn.fetch(
            """
            SELECT policy.polname AS name, policy.polpermissive AS permissive,
                   policy.polcmd AS command,
                   ARRAY(
                       SELECT CASE WHEN role_oid = 0 THEN 'PUBLIC' ELSE role.rolname END
                       FROM unnest(policy.polroles) role_oid
                       LEFT JOIN pg_catalog.pg_roles role ON role.oid = role_oid
                   ) AS roles,
                   pg_get_expr(policy.polqual, policy.polrelid) AS using,
                   pg_get_expr(policy.polwithcheck, policy.polrelid) AS check
            FROM pg_catalog.pg_policy policy
            WHERE policy.polrelid = $1
            ORDER BY policy.polname
            """,
            table_row["oid"],
        )
        security[name] = TableSecurity(
            table=name,
            owner=table_row["owner"],
            row_security=table_row["relrowsecurity"],
            force_row_security=table_row["relforcerowsecurity"],
            grants=tuple(GrantDefinition(**dict(row)) for row in grants_rows),
            policies=tuple(
                PolicyDefinition(
                    name=row["name"],
                    permissive=row["permissive"],
                    command=row["command"],
                    roles=tuple(row["roles"]),
                    using=row["using"],
                    check=row["check"],
                )
                for row in policy_rows
            ),
        )

    return DependencyInventory(
        foreign_keys=foreign_keys,
        views=views,
        functions=functions,
        triggers=triggers,
        security=security,
        sequences=sequences,
    )


async def _drop_generation(conn: asyncpg.Connection, schema: str, suffix: str) -> None:
    tables = ", ".join(
        qualified(schema, table_name(name, suffix)) for name in TARGET_TABLES
    )
    await conn.execute(f"DROP TABLE IF EXISTS {tables}")


async def _create_staging_tables(conn: asyncpg.Connection, schema: str) -> None:
    await _drop_generation(conn, schema, STAGING_SUFFIX)
    for name in TARGET_TABLES:
        await conn.execute(
            f"CREATE TABLE {qualified(schema, name + STAGING_SUFFIX)} "
            f"(LIKE {qualified(schema, name)} INCLUDING ALL)"
        )


async def _recreate_staging_foreign_keys(
    conn: asyncpg.Connection,
    schema: str,
    inventory: DependencyInventory,
) -> None:
    for fk in inventory.outbound_foreign_keys:
        definition = fk.definition
        if fk.target_is_target:
            definition = rewrite_fk_reference(
                definition,
                target_schema=fk.target_schema,
                target_table=fk.target_table,
                suffix=STAGING_SUFFIX,
            )
        await conn.execute(
            f"ALTER TABLE {qualified(schema, fk.source_table + STAGING_SUFFIX)} "
            f"ADD CONSTRAINT {quote_ident(fk.name)} {definition}"
        )


async def _clone_staging_triggers(
    conn: asyncpg.Connection,
    schema: str,
    inventory: DependencyInventory,
) -> None:
    for trigger in inventory.triggers:
        await conn.execute(
            rewrite_trigger_target(
                trigger.definition,
                schema=schema,
                table=trigger.table,
                suffix=STAGING_SUFFIX,
            )
        )


def _policy_command(command: str | bytes) -> str:
    # asyncpg returns the "char" catalog type (pg_policy.polcmd) as bytes.
    key = command.decode() if isinstance(command, bytes) else command
    return {"*": "ALL", "r": "SELECT", "a": "INSERT", "w": "UPDATE", "d": "DELETE"}[key]


async def _clone_staging_security(
    conn: asyncpg.Connection,
    schema: str,
    inventory: DependencyInventory,
) -> None:
    for name in TARGET_TABLES:
        security = inventory.security[name]
        staging = qualified(schema, name + STAGING_SUFFIX)
        current_grantees = await conn.fetch(
            """
            SELECT DISTINCT CASE WHEN acl.grantee = 0 THEN 'PUBLIC' ELSE role.rolname END AS grantee
            FROM pg_catalog.pg_class c
            CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) acl
            LEFT JOIN pg_catalog.pg_roles role ON role.oid = acl.grantee
            WHERE c.oid = $1::regclass
              AND c.relacl IS NOT NULL
              AND acl.grantee <> c.relowner
            """,
            f"{schema}.{name}{STAGING_SUFFIX}",
        )
        await conn.execute(f"REVOKE ALL ON TABLE {staging} FROM PUBLIC")
        for row in current_grantees:
            if row["grantee"] and row["grantee"] != "PUBLIC":
                await conn.execute(
                    f"REVOKE ALL ON TABLE {staging} FROM {quote_ident(row['grantee'])}"
                )
        for grant in security.grants:
            grantee = (
                "PUBLIC" if grant.grantee == "PUBLIC" else quote_ident(grant.grantee)
            )
            option = " WITH GRANT OPTION" if grant.grantable else ""
            await conn.execute(
                f"GRANT {grant.privilege} ON TABLE {staging} TO {grantee}{option}"
            )
        if security.row_security:
            await conn.execute(f"ALTER TABLE {staging} ENABLE ROW LEVEL SECURITY")
        if security.force_row_security:
            await conn.execute(f"ALTER TABLE {staging} FORCE ROW LEVEL SECURITY")
        for policy in security.policies:
            roles = ", ".join(
                "PUBLIC" if role == "PUBLIC" else quote_ident(role)
                for role in policy.roles
            )
            statement = (
                f"CREATE POLICY {quote_ident(policy.name)} ON {staging} AS "
                f"{'PERMISSIVE' if policy.permissive else 'RESTRICTIVE'} "
                f"FOR {_policy_command(policy.command)} TO {roles or 'PUBLIC'}"
            )
            if policy.using is not None:
                statement += f" USING ({policy.using})"
            if policy.check is not None:
                statement += f" WITH CHECK ({policy.check})"
            await conn.execute(statement)


async def _restore_staging_owners(
    conn: asyncpg.Connection,
    schema: str,
    inventory: DependencyInventory,
) -> None:
    for name in TARGET_TABLES:
        await conn.execute(
            f"ALTER TABLE {qualified(schema, name + STAGING_SUFFIX)} "
            f"OWNER TO {quote_ident(inventory.security[name].owner)}"
        )


def _count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON in {path}:{line_number}: {error}"
                ) from error
            if isinstance(row, dict):
                yield row


def _json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _postgres_json_text(value: Any) -> str | None:
    """Mirror PostgreSQL jsonb ``->>`` for the scalar metadata used here."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def collect_jsonl_parity_violations(
    data_root: Path,
) -> dict[str, list[str]]:
    """Compute deploy-equivalent KG/corpus parity classes without a database."""
    root = data_root.expanduser().resolve()
    passages_by_id: dict[str, dict[str, str | None]] = {}
    for index, row in enumerate(_iter_jsonl(root / "corpus" / "passages.jsonl")):
        passage_id = str(row.get("passage_id") or "")
        if not passage_id or passage_id in passages_by_id:
            continue
        sequence = row.get("sequence_number")
        try:
            sequence = int(sequence)
        except (TypeError, ValueError):
            sequence = index + 1
        cts_urn = row.get("cts_urn")
        if cts_urn in ("None", "null", ""):
            cts_urn = None
        passages_by_id[passage_id] = {
            "canonical_ref": str(row.get("canonical_ref") or f"#{sequence}"),
            "cts_urn": None if cts_urn is None else str(cts_urn),
        }

    citation_pairs = {
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
        )
        for row in _iter_jsonl(root / "corpus" / "citations.jsonl")
    }
    violations = {name: set() for name in PARITY_VIOLATION_CLASSES}
    for node in _iter_jsonl(root / "kg" / "nodes.jsonl"):
        if str(node.get("type") or "unknown").lower() != "passage":
            continue
        metadata = _json_mapping(node.get("metadata"))
        passage_id = _postgres_json_text(metadata.get("db_passage_id")) or ""
        if not passage_id:
            continue
        kg_node_id = str(node.get("id") or node.get("node_id") or "")
        if not kg_node_id:
            continue
        passage = passages_by_id.get(passage_id)
        if passage is None or (passage_id, kg_node_id) not in citation_pairs:
            violations["missing_twin"].add(kg_node_id)
        if passage is None:
            continue
        if (
            _postgres_json_text(metadata.get("canonical_ref"))
            != passage["canonical_ref"]
        ):
            violations["canonical_ref_mismatch"].add(kg_node_id)
        if _postgres_json_text(metadata.get("cts_urn")) != passage["cts_urn"]:
            violations["cts_urn_mismatch"].add(kg_node_id)
    return {name: sorted(violations[name]) for name in PARITY_VIOLATION_CLASSES}


def load_parity_baseline(path: Path = PARITY_BASELINE_PATH) -> dict[str, list[str]]:
    if not path.exists():
        raise StagedDeployError(f"parity baseline missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StagedDeployError(
            f"cannot read parity baseline {path}: {error}"
        ) from error
    raw = payload.get("violations") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        raise StagedDeployError(
            f"invalid parity baseline {path}: missing violations object"
        )
    baseline: dict[str, list[str]] = {}
    for name in PARITY_VIOLATION_CLASSES:
        values = raw.get(name)
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise StagedDeployError(
                f"invalid parity baseline {path}: {name} must be a string list"
            )
        if len(values) != len(set(values)):
            raise StagedDeployError(
                f"invalid parity baseline {path}: duplicate ids in {name}"
            )
        baseline[name] = sorted(values)
    return baseline


def render_parity_baseline(violations: dict[str, list[str]]) -> str:
    payload = {
        "_comment": (
            "Known KG/corpus parity debt. Staged deploys warn on these exact "
            "kg_node_ids but fail on any violation not listed in its class. "
            "Shrink this baseline after parity repairs; never grow it without "
            "reviewing the data wave."
        ),
        "generated_by": "scripts/deploy_data_staged.py --write-parity-baseline",
        "violations": {
            name: sorted(set(violations.get(name, [])))
            for name in PARITY_VIOLATION_CLASSES
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def write_parity_baseline(data_root: Path, path: Path) -> dict[str, list[str]]:
    violations = collect_jsonl_parity_violations(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_parity_baseline(violations), encoding="utf-8")
    return violations


def summarize_parity_ratchet(
    violations: dict[str, list[str]], baseline: dict[str, list[str]]
) -> dict[str, Any]:
    legacy_counts: dict[str, int] = {}
    new_ids: dict[str, list[str]] = {}
    fixed_counts: dict[str, int] = {}
    for name in PARITY_VIOLATION_CLASSES:
        current = set(violations.get(name, []))
        known = set(baseline.get(name, []))
        legacy_counts[name] = len(current & known)
        new_ids[name] = sorted(current - known)
        fixed_counts[name] = len(known - current)
    return {
        "legacy_debt": {
            "total": sum(legacy_counts.values()),
            "by_class": legacy_counts,
        },
        "new_violations": {
            "total": sum(len(values) for values in new_ids.values()),
            "by_class": new_ids,
        },
        "fixed_since_baseline": {
            "total": sum(fixed_counts.values()),
            "by_class": fixed_counts,
        },
    }


def expected_source_counts(
    data_root: Path, kg_payload: Any, corpus_payload: CorpusPayload
) -> tuple[dict[str, int], dict[str, int]]:
    raw = {
        "kg_nodes": _count_jsonl(data_root / "kg" / "nodes.jsonl"),
        "kg_edges": _count_jsonl(data_root / "kg" / "edges.jsonl"),
        "ancient_works": _count_jsonl(data_root / "corpus" / "manifest.jsonl"),
        "passages": _count_jsonl(data_root / "corpus" / "passages.jsonl"),
        "passage_citations": _count_jsonl(data_root / "corpus" / "citations.jsonl"),
    }
    expected = {
        "kg_nodes": len(kg_payload.kg_nodes),
        "kg_edges": len(kg_payload.kg_edges),
        "ancient_works": len(corpus_payload.works),
        "passages": len(corpus_payload.passages),
        "passage_citations": len(corpus_payload.citations),
    }
    mismatches = {
        name: {"jsonl": raw[name], "loadable": expected[name]}
        for name in ("kg_nodes", "kg_edges", "passages", "passage_citations")
        if raw[name] != expected[name]
    }
    if mismatches:
        raise VerificationError(
            "local mirror rows are filtered or deduplicated by the loaders",
            {"source_payload_mismatches": mismatches},
        )
    return expected, raw


async def verify_generation(
    conn: asyncpg.Connection,
    schema: str,
    suffix: str,
    expected: dict[str, int],
    source_jsonl_counts: dict[str, int] | None = None,
    parity_baseline: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for name in TARGET_TABLES:
        counts[name] = await conn.fetchval(
            f"SELECT COUNT(*) FROM {qualified(schema, name + suffix)}"
        )
    count_mismatches = {
        name: {"expected": expected[name], "actual": counts[name]}
        for name in TARGET_TABLES
        if counts[name] != expected[name]
    }

    citations = qualified(schema, "passage_citations" + suffix)
    passages = qualified(schema, "passages" + suffix)
    nodes = qualified(schema, "kg_nodes" + suffix)
    edges = qualified(schema, "kg_edges" + suffix)
    works = qualified(schema, "ancient_works" + suffix)
    invariants = dict(
        await conn.fetchrow(
            f"""
            SELECT
              (SELECT COUNT(*) FROM {citations} pc
                 LEFT JOIN {passages} p ON p.passage_id = pc.passage_id
                 WHERE p.passage_id IS NULL) AS citation_to_passage,
              (SELECT COUNT(*) FROM {citations} pc
                 LEFT JOIN {nodes} n ON n.node_id = pc.kg_node_id
                 WHERE n.node_id IS NULL) AS citation_to_kg_node,
              (SELECT COUNT(*) FROM {edges} e
                 LEFT JOIN {nodes} source ON source.node_id = e.source_id
                 LEFT JOIN {nodes} target ON target.node_id = e.target_id
                 WHERE source.node_id IS NULL OR target.node_id IS NULL) AS kg_edges,
              (SELECT COUNT(*) FROM {passages} p
                 LEFT JOIN {works} w ON w.work_id = p.work_id
                 WHERE w.work_id IS NULL) AS passage_to_work,
              (SELECT COUNT(*) FROM (
                 SELECT passage_id, kg_node_id, citation_type
                 FROM {citations}
                 GROUP BY 1, 2, 3 HAVING COUNT(*) > 1
               ) duplicate) AS duplicate_citations
            """
        )
    )
    locus_rows = await conn.fetch(
        f"""
            WITH declared AS (
              SELECT n.node_id, n.metadata,
                     NULLIF(n.metadata ->> 'db_passage_id', '') AS db_passage_id
              FROM {nodes} n
              WHERE n.type = 'passage'
                AND NULLIF(n.metadata ->> 'db_passage_id', '') IS NOT NULL
            ), checked AS (
              SELECT d.node_id, d.metadata, p.passage_id, p.canonical_ref,
                     p.cts_urn,
                     EXISTS (
                       SELECT 1 FROM {citations} pc
                       WHERE pc.passage_id = p.passage_id
                         AND pc.kg_node_id = d.node_id
                     ) AS has_citation
              FROM declared d
              LEFT JOIN {passages} p ON p.passage_id::text = d.db_passage_id
            )
            SELECT node_id, passage_id, has_citation,
                   (passage_id IS NOT NULL
                     AND (metadata ->> 'canonical_ref')
                         IS DISTINCT FROM canonical_ref)
                     AS canonical_ref_mismatch,
                   (passage_id IS NOT NULL
                     AND (metadata ->> 'cts_urn') IS DISTINCT FROM cts_urn)
                     AS cts_urn_mismatch
            FROM checked
            ORDER BY node_id
            """
    )
    parity_violations = {name: [] for name in PARITY_VIOLATION_CLASSES}
    missing_twins = 0
    missing_citations = 0
    for row in locus_rows:
        node_id = row["node_id"]
        if row["passage_id"] is None:
            missing_twins += 1
            parity_violations["missing_twin"].append(node_id)
        elif not row["has_citation"]:
            missing_citations += 1
            parity_violations["missing_twin"].append(node_id)
        if row["canonical_ref_mismatch"]:
            parity_violations["canonical_ref_mismatch"].append(node_id)
        if row["cts_urn_mismatch"]:
            parity_violations["cts_urn_mismatch"].append(node_id)
    ratchet = summarize_parity_ratchet(
        parity_violations,
        parity_baseline if parity_baseline is not None else load_parity_baseline(),
    )
    locus = {
        "declared_twins": len(locus_rows),
        "shared_twins": len(locus_rows) - missing_twins,
        "violations": sum(len(values) for values in parity_violations.values()),
        "missing_twins": missing_twins,
        "missing_citations": missing_citations,
        "canonical_ref_mismatches": len(parity_violations["canonical_ref_mismatch"]),
        "cts_urn_mismatches": len(parity_violations["cts_urn_mismatch"]),
        **ratchet,
    }
    passed = (
        not count_mismatches
        and not any(invariants.values())
        and not ratchet["new_violations"]["total"]
    )
    return {
        "passed": passed,
        "expected_counts": expected,
        "source_jsonl_counts": source_jsonl_counts or expected,
        "actual_counts": counts,
        "count_mismatches": count_mismatches,
        "dangling_and_uniqueness": invariants,
        "kg_corpus_locus_parity": locus,
    }


async def _execute_transactional_swap(
    conn: asyncpg.Connection, statements: Iterable[str]
) -> None:
    started = False
    try:
        for statement in statements:
            await conn.execute(statement)
            if statement == "BEGIN":
                started = True
            elif statement == "COMMIT":
                started = False
    except BaseException:
        if started:
            with contextlib.suppress(Exception):
                await conn.execute("ROLLBACK")
        raise


async def _table_set_exists(
    conn: asyncpg.Connection, schema: str, suffix: str
) -> tuple[bool, list[str]]:
    present = await conn.fetch(
        """
        SELECT c.relname
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = $1 AND c.relname = ANY($2::text[])
          AND c.relkind IN ('r', 'p')
        """,
        schema,
        [name + suffix for name in TARGET_TABLES],
    )
    names = {row["relname"] for row in present}
    missing = [name + suffix for name in TARGET_TABLES if name + suffix not in names]
    return not missing, missing


async def run_deploy(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    conn = await asyncpg.connect(
        dsn=args.database_url,
        statement_cache_size=0,
        timeout=30,
        command_timeout=args.command_timeout,
    )
    lock_acquired = False
    staging_created = False
    try:
        lock_acquired = bool(
            await conn.fetchval("SELECT pg_try_advisory_lock($1)", ADVISORY_LOCK_KEY)
        )
        if not lock_acquired:
            raise StagedDeployError(
                "another staged data deploy holds the advisory lock"
            )

        inventory = await inventory_dependencies(conn, args.schema)
        serial_sequences = {
            table: [item["name"] for item in items if item["kind"] == "serial"]
            for table, items in inventory.sequences.items()
            if any(item["kind"] == "serial" for item in items)
        }
        if serial_sequences:
            raise StagedDeployError(
                "serial sequences are not safe to clone with LIKE INCLUDING ALL: "
                + json.dumps(serial_sequences, sort_keys=True)
            )
        if args.rollback:
            exists, missing = await _table_set_exists(conn, args.schema, OLD_SUFFIX)
            if not exists:
                raise StagedDeployError(
                    "rollback generation is incomplete: " + ", ".join(missing)
                )
            await _drop_generation(conn, args.schema, STAGING_SUFFIX)
            statements = generate_swap_sql(
                args.schema,
                inventory,
                rollback=True,
                lock_timeout_seconds=args.lock_timeout,
            )
            await _execute_transactional_swap(conn, statements)
            counts = {
                name: await conn.fetchval(
                    f"SELECT COUNT(*) FROM {qualified(args.schema, name)}"
                )
                for name in TARGET_TABLES
            }
            return {
                "status": "rolled_back",
                "mode": "rollback",
                "schema": args.schema,
                "counts": counts,
                "dependencies": inventory.summary(),
                "elapsed_seconds": round(time.monotonic() - started_at, 3),
            }

        data_root = args.data_root.resolve()
        snapshot = load_snapshot(data_root / "kg")
        kg_payload = build_import_payload(snapshot)
        corpus_payload = load_corpus_payload(data_root)
        expected, source_jsonl_counts = expected_source_counts(
            data_root, kg_payload, corpus_payload
        )

        await _create_staging_tables(conn, args.schema)
        staging_created = True
        targets = ImportTables.with_suffix(args.schema, STAGING_SUFFIX)
        await import_kg_payload(
            conn,
            kg_payload,
            replace_data=False,
            batch_size=max(1, args.batch_size),
            tables=targets,
        )
        await import_corpus_payload(
            conn,
            corpus_payload,
            tables=targets,
            replace_data=True,
            batch_size=max(1, args.batch_size),
        )
        verification = await verify_generation(
            conn,
            args.schema,
            STAGING_SUFFIX,
            expected,
            source_jsonl_counts,
            load_parity_baseline(args.parity_baseline),
        )
        if not verification["passed"]:
            raise VerificationError(
                "staging verification failed",
                verification,
            )
        await _recreate_staging_foreign_keys(conn, args.schema, inventory)
        await _clone_staging_triggers(conn, args.schema, inventory)
        await _clone_staging_security(conn, args.schema, inventory)
        await _restore_staging_owners(conn, args.schema, inventory)

        if args.dry_run:
            await _drop_generation(conn, args.schema, STAGING_SUFFIX)
            staging_created = False
            return {
                "status": "verified",
                "mode": "dry-run",
                "schema": args.schema,
                "swapped": False,
                "verification": verification,
                "dependencies": inventory.summary(),
                "elapsed_seconds": round(time.monotonic() - started_at, 3),
            }

        statements = generate_swap_sql(
            args.schema,
            inventory,
            lock_timeout_seconds=args.lock_timeout,
        )
        await _execute_transactional_swap(conn, statements)
        staging_created = False
        return {
            "status": "deployed",
            "mode": "deploy",
            "schema": args.schema,
            "swapped": True,
            "rollback_available": True,
            "verification": verification,
            "dependencies": inventory.summary(),
            "elapsed_seconds": round(time.monotonic() - started_at, 3),
        }
    except BaseException:
        if staging_created and not conn.is_closed():
            try:
                await _drop_generation(conn, args.schema, STAGING_SUFFIX)
            except Exception as cleanup_error:
                print(f"staging cleanup failed: {cleanup_error}", file=sys.stderr)
        raise
    finally:
        if lock_acquired and not conn.is_closed():
            await conn.execute("SELECT pg_advisory_unlock($1)", ADVISORY_LOCK_KEY)
        await conn.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="load and verify staging, skip the swap, then drop staging",
    )
    mode.add_argument(
        "--rollback",
        action="store_true",
        help="atomically swap the complete __old generation back into service",
    )
    mode.add_argument(
        "--write-parity-baseline",
        action="store_true",
        help="regenerate the parity-debt baseline from local JSONL and exit",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL"),
        help="maintenance PostgreSQL DSN (or DATABASE_URL/SUPABASE_DATABASE_URL)",
    )
    parser.add_argument("--schema", default="free_will")
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data")
    parser.add_argument(
        "--parity-baseline",
        type=Path,
        default=PARITY_BASELINE_PATH,
        help="committed kg_node_id parity-debt baseline",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--lock-timeout", type=int, default=10)
    parser.add_argument("--command-timeout", type=int, default=600)
    args = parser.parse_args(argv)
    if not args.write_parity_baseline and not args.database_url:
        parser.error("missing --database-url, DATABASE_URL, or SUPABASE_DATABASE_URL")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.schema):
        parser.error("--schema must be an unquoted PostgreSQL identifier")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.write_parity_baseline:
        violations = write_parity_baseline(
            args.data_root.resolve(), args.parity_baseline.resolve()
        )
        print(
            json.dumps(
                {
                    "status": "parity_baseline_written",
                    "path": str(args.parity_baseline.resolve()),
                    "counts": {
                        name: len(violations[name]) for name in PARITY_VIOLATION_CLASSES
                    },
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    try:
        summary = asyncio.run(run_deploy(args))
    except BaseException as error:
        summary = {
            "status": "failed",
            "mode": "rollback"
            if args.rollback
            else "dry-run"
            if args.dry_run
            else "deploy",
            "error": f"{type(error).__name__}: {error}",
        }
        if isinstance(error, VerificationError):
            summary["verification"] = error.details
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
