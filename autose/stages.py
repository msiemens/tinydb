"""The model stages: analyst (1, 2), builder (3, 4), reviewer (6). See ADR-001..009."""
import os
import subprocess

from . import FLASH, PRO, checks, llm, tools

PROMPTS = os.path.join(os.path.dirname(__file__), "prompts")
MAX_RETRIES = 2          # implementer retries after pytest fails (ADR-009)
MAX_DESIGN_RETURNS = 1   # returns from test failure to the analyst (ADR-009)
MAX_DIFF_CHARS = 60_000


class StageFailed(Exception):
    """A check did not pass. `artifact` is the file that records why."""

    def __init__(self, artifact, message):
        super().__init__(message)
        self.artifact = artifact
        self.message = message


def _prompt(name):
    with open(os.path.join(PROMPTS, name), encoding="utf-8") as fh:
        return fh.read()


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def fence(issue_text):
    """Issue text is data. It is never put into a shell command or a branch name."""
    return f"<<<UNTRUSTED ISSUE\n{issue_text}\nUNTRUSTED ISSUE>>>"


def _git(work, *args):
    proc = subprocess.run(["git", *args], cwd=work, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


# ---------------------------------------------------------------- stages 1, 2

def _generate(role, system, user, tools_, check, artifact, out):
    """One generation plus at most one regeneration when the script check fails."""
    text = llm.run_agent(role, FLASH, system, user, tools_)
    ok, msg = check(text)
    if not ok:
        retry = (f"{user}\n\nYour previous attempt failed an automatic check: {msg}\n"
                 f"Previous attempt:\n{text}\n\nWrite the document again and fix that.")
        text = llm.run_agent(role, FLASH, system, retry, tools_)
        ok, msg = check(text)
    if not ok:
        _write(os.path.join(out, artifact), f"# FAILED: {msg}\n\n{text}\n")
        raise StageFailed(artifact, msg)
    _write(os.path.join(out, artifact), text + "\n")
    return text


def analyst(work, out, issue_text, feedback=""):
    system = _prompt("analyst.md")
    tools_ = tools.toolset("analyst", work)
    arch = _read(os.path.join(work, "ARCHITECTURE.md"))
    extra = f"\n\nA later stage reported this problem. Take it into account:\n{feedback}" if feedback else ""
    base = f"{fence(issue_text)}\n\nARCHITECTURE.md:\n{arch}{extra}"
    spec = _generate("analyst", system, base + "\n\nTask 1 only: write spec.md.",
                     tools_, checks.check_spec, "spec.md", out)
    _generate("analyst", system,
              base + f"\n\nspec.md:\n{spec}\n\nTask 2 only: write design.md.",
              tools_, lambda t: checks.check_design(t, work), "design.md", out)


# ---------------------------------------------------------------- stages 3, 4

def _implement(work, out, feedback):
    spec, design = _read(os.path.join(out, "spec.md")), _read(os.path.join(out, "design.md"))
    extra = f"\n\nFix this:\n{feedback}" if feedback else ""
    llm.run_agent("implementer", FLASH, _prompt("implementer.md"),
                  f"spec.md:\n{spec}\n\ndesign.md:\n{design}{extra}",
                  tools.toolset("implementer", work))


def _diff(work):
    _git(work, "add", "-A")  # .venv ignores itself, .coverage is in .gitignore
    return _git(work, "diff", "--cached", "--binary", "origin/master")


def _test(work, out, issue_number, pytest_log):
    spec, design = _read(os.path.join(out, "spec.md")), _read(os.path.join(out, "design.md"))
    extra = f"\n\nLast pytest log:\n{pytest_log}" if pytest_log else ""
    llm.run_agent("tester", FLASH, _prompt("tester.md"),
                  f"Issue number: {issue_number}\n\nspec.md:\n{spec}\n\ndesign.md:\n{design}"
                  f"\n\nImplementer diff:\n{_diff(work)[:MAX_DIFF_CHARS]}{extra}",
                  tools.toolset("tester", work))


def _builds(work):
    for cmd in (["uv", "sync", "--group", "dev"],
                ["uv", "run", "python", "-c", "import tinydb"]):
        proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True,
                              env=tools.clean_env())
        if proc.returncode:
            return False, (proc.stdout + proc.stderr)[-3000:]
    return True, ""


def builder(work, out, issue_number, issue_text, start="builder", feedback=""):
    if start == "analyst":
        analyst(work, out, issue_text, feedback)
        feedback = ""
    attempts = returns = 0
    log = feedback
    while True:
        _implement(work, out, log)
        ok, detail = _builds(work)
        if not ok:  # stage 3 check: no regeneration, the run stops (ADR-007)
            _write(os.path.join(out, "diff.patch"), f"# FAILED: build\n{detail}\n")
            raise StageFailed("diff.patch", "the code does not build")
        _test(work, out, issue_number, log if attempts or returns else "")
        code, output = tools.run_pytest(work)
        tail = output[-6000:]
        _write(os.path.join(out, "test_report.md"),
               f"# Test report\n\nexit code: {code}\nattempts: {attempts}\n"
               f"design returns: {returns}\n\n```\n{tail}\n```\n")
        if code == 0:
            break
        log = tail
        attempts += 1
        if attempts <= MAX_RETRIES:
            continue
        if returns < MAX_DESIGN_RETURNS:
            returns += 1
            attempts = 0
            analyst(work, out, issue_text, "Tests keep failing:\n" + tail)
            continue
        raise StageFailed("test_report.md", "tests still fail after the retry budget")
    _write(os.path.join(out, "diff.patch"), _diff(work))


# -------------------------------------------------------------------- stage 6

def review(work, out, issue_text, round_no):
    diff = _git(work, "diff", "origin/master...HEAD")
    files = checks.diff_files(diff)
    base = (f"{fence(issue_text)}\n\nReview round {round_no}.\n\n"
            f"Diff against master:\n{diff[:MAX_DIFF_CHARS]}")
    system = _prompt("reviewer.md")
    tools_ = tools.toolset("reviewer", work)
    model = os.environ.get("AUTOSE_REVIEWER_MODEL") or PRO  # ADR-022 experiments only
    text = llm.run_agent("reviewer", model, system, base, tools_)
    verdict, msg = checks.check_verdict(text, files)
    if verdict is None:  # rejected empty or malformed review: ask once more (ADR-008)
        text = llm.run_agent("reviewer", model, system,
                             base + f"\n\nYour previous review was rejected: {msg}. "
                             "Review again, starting with the verdict line.", tools_)
        verdict, msg = checks.check_verdict(text, files)
    if verdict is None:
        _write(os.path.join(out, "review.md"),
               f"verdict: none\n\nReview rejected by the script: {msg}\n\n{text}\n")
        raise StageFailed("review.md", msg)
    _write(os.path.join(out, "review.md"), text + "\n")
    return verdict
