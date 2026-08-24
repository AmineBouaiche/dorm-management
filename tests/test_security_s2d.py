from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dependabot_monitors_python_actions_and_docker() -> None:
    config = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert "version: 2" in config
    assert 'package-ecosystem: "pip"' in config
    assert 'package-ecosystem: "github-actions"' in config
    assert 'package-ecosystem: "docker"' in config
    assert config.count('interval: "weekly"') == 3


def test_ci_runs_dependency_vulnerability_audit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"pip-audit>=2.10,<3.0"' in pyproject
    assert '"pytest>=9.0.3,<10.0"' in pyproject
    assert "python -m pip_audit --skip-editable" in workflow


def test_checkout_does_not_persist_github_token_credentials() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow


def test_dependabot_limits_version_update_pr_volume() -> None:
    config = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert config.count("open-pull-requests-limit: 5") == 3
