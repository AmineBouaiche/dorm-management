from pathlib import Path


WORKFLOW = Path(".github/workflows/ci.yml")


def test_ci_workflow_runs_tests_and_lint_with_postgres() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "postgres:17-alpine" in workflow
    assert "alembic upgrade head" in workflow
    assert "pytest" in workflow
    assert "ruff check ." in workflow


def test_ci_workflow_targets_supported_python_and_main_branch() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'python-version: "3.13"' in workflow
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "branches: [main]" in workflow
