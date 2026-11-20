"""Stage 5 (release) and the review post step. No model is called here (ADR-001, ADR-005)."""
import json
import os
import re
import subprocess
import time

from . import checks
from .stages import StageFailed, _read, _write

UPSTREAM = "msiemens/tinydb"
CI_TIMEOUT_S = 25 * 60
CI_START_GRACE_S = 5 * 60
POLL_S = 30


def _run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"{' '.join(cmd[:3])} failed: {proc.stderr.strip()[:400]}")
    return proc.stdout.strip()


def _title(out):
    first = _read(os.path.join(out, "spec.md")).splitlines()[0]
    return re.sub(r"[^\w .,:()/'-]", "", first.lstrip("# ")).strip()[:72] or "AutoSE change"


def _criteria(out):
    spec = _read(os.path.join(out, "spec.md"))
    match = re.search(r"^#+\s*acceptance criteria\s*$(.*?)(?=^#+\s|\Z)", spec, re.I | re.M | re.S)
    return match.group(1).strip() if match else "(see spec.md artifact)"


def _wait_for_ci(pr):
    start = time.time()
    while True:
        out = _run(["gh", "pr", "checks", pr, "--json", "name,bucket"])
        checks = json.loads(out or "[]")
        elapsed = time.time() - start
        if not checks and elapsed > CI_START_GRACE_S:
            return False, ("no CI check started. A pull request opened with GITHUB_TOKEN does "
                           "not trigger workflows; use the AUTOSE_PAT secret.")
        buckets = {c["bucket"] for c in checks}
        if checks and buckets <= {"pass", "skipping"}:
            return True, f"{len(checks)} checks passed"
        if buckets & {"fail", "cancel"}:
            bad = [c["name"] for c in checks if c["bucket"] in ("fail", "cancel")]
            return False, "CI failed: " + ", ".join(bad[:5])
        if elapsed > CI_TIMEOUT_S:
            return False, "timed out waiting for CI"
        time.sleep(POLL_S)


def release(work, out, issue_number, round_no):
    repo = os.environ["GITHUB_REPOSITORY"]
    if repo.lower() == UPSTREAM:
        raise RuntimeError("refusing to run against the upstream repository")
    report = _read(os.path.join(out, "test_report.md"))
    if "exit code: 0" not in report:
        raise StageFailed("pr.md", "test_report.md does not record a passing run")
    patch = _read(os.path.join(out, "diff.patch"))
    forbidden = [f for f in checks.diff_files(patch)
                 if f.startswith((".github/", "autose/", ".git/"))]
    if forbidden:  # the patch is data from a model; it may not touch the pipeline itself
        raise StageFailed("pr.md", "patch touches protected paths: " + ", ".join(forbidden))
    branch = f"autose/issue-{int(issue_number)}"
    title = _title(out)

    _run(["git", "config", "user.name", "autose-bot"], work)
    _run(["git", "config", "user.email", "autose-bot@users.noreply.github.com"], work)
    _run(["git", "checkout", "-B", branch, "origin/master"], work)
    _run(["git", "apply", "--index", os.path.abspath(os.path.join(out, "diff.patch"))], work)
    _run(["git", "commit", "-m", f"{title} (#{int(issue_number)})"], work)
    subprocess.run(["git", "fetch", "origin", branch], cwd=work, capture_output=True)
    _run(["git", "push", "--force-with-lease", "origin", f"HEAD:refs/heads/{branch}"], work)

    run_url = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}"
               f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}")
    body = (f"Refs #{int(issue_number)}\n\n## Acceptance criteria\n\n{_criteria(out)}\n\n"
            f"## Evidence\n\nTest report, spec, design and review are artifacts of "
            f"[this run]({run_url}). Review round {round_no} of at most 2. "
            "A person decides whether to merge.\n")
    _write(os.path.join(out, "pr.md"), body)

    existing = _run(["gh", "pr", "list", "--head", branch, "--state", "open",
                     "--json", "number", "--jq", ".[0].number // empty"], work)
    if existing:
        number = existing
        _run(["gh", "pr", "comment", number, "--body",
              f"Updated for review round {round_no}. See the [run]({run_url})."], work)
    else:
        _run(["gh", "pr", "create", "--base", "master", "--head", branch,
              "--title", title, "--body-file", os.path.join(out, "pr.md")], work)
        number = _run(["gh", "pr", "view", branch, "--json", "number", "--jq", ".number"], work)
    info = json.loads(_run(["gh", "pr", "view", number, "--json",
                            "url,state,baseRefName,headRefOid"], work))
    if info["state"] != "OPEN" or info["baseRefName"] != "master":
        raise StageFailed("pr.md", f"unexpected PR state {info['state']} base {info['baseRefName']}")
    with open(os.path.join(out, "pr.md"), "a", encoding="utf-8") as fh:
        fh.write(f"\nPR: {info['url']}\n")
    _write(os.path.join(out, "pr.json"), json.dumps(dict(info, number=int(number))))
    out_file = os.environ.get("GITHUB_OUTPUT")
    if out_file:
        with open(out_file, "a", encoding="utf-8") as fh:
            fh.write(f"pr={number}\n")

    ok, msg = _wait_for_ci(number)
    with open(os.path.join(out, "pr.md"), "a", encoding="utf-8") as fh:
        fh.write(f"CI: {msg}\n")
    if not ok:
        raise StageFailed("pr.md", msg)


def post_review(out, pr_number):
    """Post review.md as a comment. The model never runs this step."""
    _run(["gh", "pr", "comment", str(int(pr_number)), "--body-file",
          os.path.join(out, "review.md")])
