from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def makefile() -> str:
    return (ROOT / "Makefile").read_text(encoding="utf-8")


def test_production_targets_are_bound_to_the_real_platform_compose() -> None:
    source = makefile()

    assert "<deploy-host>" not in source
    assert "PROD_SSH ?= ben@65.108.9.16" in source
    assert "PROD_DIR ?= /home/ben/EleutherIA" in source
    assert "PROD_BACKUP_DIR ?= /home/ben/eleutheria-backups" in source
    assert (
        "PROD_COMPOSE ?= docker compose -p deploy -f deploy/pragma-compose.yml "
        "-f /tmp/eleutheria-compose-runtime.yml"
    ) in source


def test_code_and_data_deploys_require_the_same_immutable_release() -> None:
    source = makefile()

    assert "deploy: require-rc-sha" in source
    assert "deploy-data: require-rc-sha" in source
    assert "deploy-data-dry-run: require-rc-sha" in source
    assert "git checkout -q --detach $(RC_SHA)" in source
    assert 'test "$$(git rev-parse HEAD)" = "$(RC_SHA)"' in source
    assert "git pull -q origin main" not in source


def test_data_runner_derives_the_live_api_network() -> None:
    source = makefile()

    assert '--network app-network' not in source
    assert source.count('docker inspect -f "{{json .NetworkSettings.Networks}}"') >= 3
    assert source.count('docker run --rm --network "$$NETWORK"') >= 3


def test_full_deploy_orders_backup_schema_dry_run_swap_and_recreate() -> None:
    source = makefile()
    deploy_recipe = source.split("deploy: require-rc-sha", 1)[1].split(
        "# Rollback:", 1
    )[0]

    ordered_markers = [
        "pg_dump",
        "build eleutheria-api eleutheria-worker",
        "20260824_01_bobzien_consensus_correction.sql",
        "20260824_02_query_traces_private_by_default.sql",
        "20260824_03_secondary_page_evidence.sql",
        "deploy_data_staged.py --dry-run",
        'python scripts/deploy_data_staged.py"',
        "up -d --force-recreate --no-deps --no-build",
    ]
    offsets = [deploy_recipe.index(marker) for marker in ordered_markers]
    assert offsets == sorted(offsets)
    assert "served_total_nodes" in deploy_recipe
    assert "served_total_edges" in deploy_recipe
    assert 'expected_release_id=$$RELEASE' in deploy_recipe
    assert "public API release verified across 8 probes" in deploy_recipe
    assert deploy_recipe.count('h["status"] == "healthy"') >= 2
    assert deploy_recipe.count('h["database"] == "connected"') >= 2
    assert deploy_recipe.count('h["graphrag"] == "ready"') >= 2


def test_code_rollback_validates_the_recorded_commit_before_ssh() -> None:
    source = makefile()
    rollback_recipe = source.split("rollback:", 1)[1].split(
        "# Deploy data:", 1
    )[0]

    assert "invalid rollback SHA" in rollback_recipe
    assert "'^[0-9a-f]{40}$$'" in rollback_recipe
    assert rollback_recipe.index("invalid rollback SHA") < rollback_recipe.index(
        "rolling back prod"
    )
