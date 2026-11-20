"""Stage checks decided by scripts, not by a model (ADR-007)."""
import os
import re

CONDITION = re.compile(r"\b(when|if|given|after|before|calling|called|with|without|on|for)\b", re.I)
RESULT = re.compile(
    r"\b(returns?|raises?|results?|is|are|should|must|equals?|remains?|contains?|"
    r"updates?|removes?|keeps?|stays?|does not|doesn't|no longer)\b", re.I)
VERDICT = re.compile(r"^verdict:\s*(approve|code|approach)\s*$", re.I)


def _section(text, heading):
    pattern = re.compile(rf"^#+\s*{heading}\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        return None
    rest = text[match.end():]
    nxt = re.search(r"^#+\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def check_spec(text):
    """Stage 1. At least two criteria, each with a condition and an observable result."""
    body = _section(text, r"acceptance criteria")
    if body is None:
        return False, "spec.md has no 'Acceptance criteria' heading"
    bullets = [m.group(1).strip() for m in
               re.finditer(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$", body, re.M)]
    if len(bullets) < 2:
        return False, f"need at least 2 acceptance criteria, found {len(bullets)}"
    bad = [b for b in bullets if not (CONDITION.search(b) and RESULT.search(b))]
    if bad:
        return False, "criterion lacks a condition and an observable result: " + bad[0][:120]
    return True, f"{len(bullets)} criteria"


def check_design(text, root):
    """Stage 2. A path that exists, and a function defined in that file."""
    tokens = re.findall(r"`([^`\n]+)`", text)
    paths = [t for t in tokens if re.fullmatch(r"[\w./-]+\.py", t)
             and os.path.isfile(os.path.join(root, t))]
    if not paths:
        return False, "design.md names no existing .py file in backticks"
    names = {re.split(r"[.:]", t.rstrip("()"))[-1] for t in tokens
             if re.fullmatch(r"[A-Za-z_][\w.]*(\(\))?", t)}
    for path in paths:
        with open(os.path.join(root, path), encoding="utf-8") as fh:
            defined = set(re.findall(r"^\s*def\s+(\w+)", fh.read(), re.M))
        hit = names & defined
        if hit:
            return True, f"{path}: {sorted(hit)[0]}"
    return False, "design.md names no function that is defined in a named file"


def diff_files(diff_text):
    return sorted(set(re.findall(r"^diff --git a/(\S+) b/", diff_text, re.M)))


def check_verdict(text, files):
    """Stage 6. First line is the verdict; the review must name a file from the diff."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None, "review.md is empty"
    match = VERDICT.match(lines[0].strip())
    if not match:
        return None, "first line is not 'verdict: approve|code|approach'"
    verdict = match.group(1).lower()
    if not any(f in text for f in files):
        return None, f"verdict '{verdict}' names no file from the diff"
    return verdict, "ok"
