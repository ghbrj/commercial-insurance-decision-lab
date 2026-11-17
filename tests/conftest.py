import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def task_dir():
    d = REPO_ROOT / "specs" / "tasks" / "property_triage_v01"
    assert d.is_dir(), "registered task missing"
    return d
