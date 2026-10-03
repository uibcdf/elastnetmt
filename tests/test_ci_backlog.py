"""Skipped pushes remain due until an executed full Linux matrix passes."""

import importlib.util
import subprocess
from pathlib import Path
from urllib.error import URLError

SPEC = importlib.util.spec_from_file_location(
    "ci_backlog", Path(__file__).resolve().parents[1] / "devtools/ci_backlog.py"
)
assert SPEC is not None and SPEC.loader is not None
ci_backlog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci_backlog)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def test_skipped_commit_stays_due_after_ordinary_commits(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "commit", "--allow-empty", "-qm", "full matrix passed")
    anchor = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "commit", "--allow-empty", "-qm", "iteration [skip ci]")
    skipped = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "commit", "--allow-empty", "-qm", "ordinary change")
    head = git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.chdir(tmp_path)
    assert ci_backlog.skipped_commits_after(anchor, head) == [skipped]
    assert ci_backlog.skipped_commits_after(head, head) == []
    assert ci_backlog.SKIP_MARKER.search("message\n\nskip-checks: true")


def jobs(prefix=""):
    return [
        {
            "name": f"{prefix}Test on ubuntu-latest, Python {version}",
            "conclusion": "success",
            "steps": [{"name": "Run tests", "conclusion": "success"}],
        }
        for version in ci_backlog.PYTHON_VERSIONS
    ]


def test_every_python_minor_must_execute_the_full_suite(monkeypatch):
    evidence = jobs()
    monkeypatch.setattr(ci_backlog, "api_json", lambda *_: {"jobs": evidence})
    assert ci_backlog.full_linux_passed("uibcdf/elastnetmt", 1, "token")
    evidence[0]["steps"][0]["conclusion"] = "skipped"
    assert not ci_backlog.full_linux_passed("uibcdf/elastnetmt", 1, "token")
    evidence = jobs()[:-1]
    assert not ci_backlog.full_linux_passed("uibcdf/elastnetmt", 1, "token")


def test_full_push_clears_debt_but_probe_pr_feature_and_failure_do_not(monkeypatch):
    def run(run_id, event, commit, branch="main", conclusion="success"):
        return {
            "id": run_id,
            "event": event,
            "head_sha": commit,
            "head_branch": branch,
            "conclusion": conclusion,
        }

    def fake_api(path, _token):
        if "/workflows/" in path:
            assert "branch=main" not in path
            return {
                "workflow_runs": [
                    run(9, "schedule", "red", conclusion="failure"),
                    run(2, "workflow_dispatch", "probe"),
                    run(4, "workflow_dispatch", "feature", branch="feature"),
                    run(5, "pull_request", "pr"),
                    run(3, "push", "push"),
                    run(1, "schedule", "full"),
                ]
            }
        assert "/runs/4/" not in path and "/runs/5/" not in path
        evidence = jobs()
        if "/runs/2/" in path:
            evidence[0]["steps"][0]["conclusion"] = "skipped"
        return {"jobs": evidence}

    monkeypatch.setattr(ci_backlog, "api_json", fake_api)
    monkeypatch.setattr(
        ci_backlog, "is_ancestor", lambda left, right: (left, right) != ("push", "full")
    )
    assert ci_backlog.last_full_success("uibcdf/elastnetmt", "head", "token") == "push"


def test_uncertain_history_runs_full_matrix(tmp_path, monkeypatch, capsys):
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_REPOSITORY", "uibcdf/elastnetmt")
    monkeypatch.setenv("GITHUB_SHA", "head")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr(
        ci_backlog,
        "last_full_success",
        lambda *_: (_ for _ in ()).throw(URLError("offline")),
    )
    assert ci_backlog.main() == 0
    assert "running full matrix" in capsys.readouterr().out
    assert "run_full=true" in output.read_text(encoding="utf-8")


def test_a_previous_three_minor_matrix_cannot_clear_314_debt(monkeypatch):
    evidence = [job for job in jobs() if "Python 3.14" not in job["name"]]
    monkeypatch.setattr(ci_backlog, "api_json", lambda *_: {"jobs": evidence})
    assert not ci_backlog.full_linux_passed("uibcdf/elastnetmt", 1, "token")
