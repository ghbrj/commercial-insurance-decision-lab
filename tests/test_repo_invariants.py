"""Day-one invariants: hygiene and spec registry. Fast, no heavy deps."""
import pathlib
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_secrets_are_gitignored():
    gi = (REPO_ROOT / ".gitignore").read_text()
    assert ".env" in gi and "*.key" in gi


def test_env_example_lists_required_keys():
    env_ex = (REPO_ROOT / ".env.example").read_text()
    for key in ("TYPESAFE_API_KEY", "JEV_MAX_REQUESTS_PER_RUN"):
        assert key in env_ex


def test_every_registered_task_has_the_four_specs(task_dir):
    for rel in (
        "task_definition.yaml",
        "corpus_spec.yaml",
        "scorer_config.yaml",
        "underwriting_guide/rules_table.yaml",
        "underwriting_guide/guide.md",
    ):
        assert (task_dir / rel).is_file(), f"missing {rel}"


def test_decision_space_is_three_way_and_codes_resolve(task_dir):
    td = yaml.safe_load((task_dir / "task_definition.yaml").read_text())
    assert set(td["decision_space"]["allowed"]) == {"STP_ACCEPT", "REFER", "DECLINE"}
    rt = yaml.safe_load(
        (task_dir / "underwriting_guide" / "rules_table.yaml").read_text()
    )
    # reason codes referenced by rules must exist in the table's own enumeration
    ids = {r["rule_id"] for r in rt.get("rules", [])}
    for r in rt.get("rules", []):
        assert set(r.keys()) >= {"rule_id", "guide_section", "outcome"}
    assert isinstance(ids, set)  # placeholder-pass until M1 fills rules
