from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_FILE = ROOT / "tests/local_artifact_suite.txt"

EXPECTED_LOCAL_ARTIFACT_TESTS = {
    "tests/test_alexander_sharples_global_p0.py",
    "tests/test_hildebrandt_p0_repair.py",
    "tests/test_literature_acquisition_manifest.py",
    "tests/test_long_sedley_vol2_p0_repair.py",
    "tests/test_sorabji_p0_repair.py",
    "tests/test_tatian_p0_repair.py",
}


def test_local_artifact_suite_is_explicit_complete_and_present() -> None:
    listed = {
        line.strip()
        for line in SUITE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert listed == EXPECTED_LOCAL_ARTIFACT_TESTS
    assert all((ROOT / path).is_file() for path in listed)


def test_local_artifact_suite_is_not_silently_selected_by_pytest_markers() -> None:
    # CI excludes exact paths. The immutable RC proof still runs `pytest tests`
    # with the fingerprinted local archive present; no skip marker can turn
    # this scholarly evidence suite green without opening those artifacts.
    for path in EXPECTED_LOCAL_ARTIFACT_TESTS:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.skip" not in source
