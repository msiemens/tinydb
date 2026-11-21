"""Sandboxed tools handed to the models (ADR-005). No shell, no network."""
import os
import subprocess

MAX_READ = 60_000
# The implementer may edit source, never the workflow, the agent code, git, or tests.
IMPLEMENTER_DENY = (".git", ".github", "autose", "tests")


def _resolve(root, rel):
    root = os.path.realpath(root)
    path = os.path.realpath(os.path.join(root, rel))
    if path != root and not path.startswith(root + os.sep):
        raise PermissionError(f"path outside checkout: {rel}")
    return path, os.path.relpath(path, root).replace(os.sep, "/")


def _decl(name, description, props, required):
    return {"name": name, "description": description,
            "parameters": {"type": "OBJECT",
                           "properties": {k: {"type": "STRING", "description": v}
                                          for k, v in props.items()},
                           "required": required}}


def _guard_git(rel):
    if rel == ".git" or rel.startswith(".git/"):
        raise PermissionError(".git is not accessible")
    # Grading copies live here. They are not a hand-off (ADR-003).
    if rel == "experiment" or rel.startswith("experiment/"):
        raise PermissionError("experiment/ is not available to agents")


def _list_dir(root):
    def list_dir(path="."):
        full, rel = _resolve(root, path)
        _guard_git(rel)
        names = sorted(n + ("/" if os.path.isdir(os.path.join(full, n)) else "")
                       for n in os.listdir(full) if n != ".git")
        return "\n".join(names)
    return (_decl("list_dir", "List a directory inside the repository.",
                  {"path": "Directory relative to the repository root."}, []), list_dir)


def _read_file(root):
    def read_file(path):
        full, rel = _resolve(root, path)
        _guard_git(rel)
        with open(full, encoding="utf-8", errors="replace") as fh:
            text = fh.read(MAX_READ + 1)
        return text[:MAX_READ] + ("\n[truncated]" if len(text) > MAX_READ else "")
    return (_decl("read_file", "Read a text file inside the repository.",
                  {"path": "File relative to the repository root."}, ["path"]), read_file)


def _write_file(root, allow=(), deny=()):
    def write_file(path, content):
        full, rel = _resolve(root, path)
        _guard_git(rel)
        if rel.split("/")[0] in deny:
            raise PermissionError(f"writing {rel} is not allowed for this role")
        if allow and not any(rel.startswith(a) for a in allow):
            raise PermissionError(f"this role may only write under: {', '.join(allow)}")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        return f"wrote {rel} ({len(content)} chars)"
    return (_decl("write_file", "Create or overwrite a file inside the repository.",
                  {"path": "File relative to the repository root.",
                   "content": "Complete new file content."}, ["path", "content"]), write_file)


def _replace_in_file(root, deny=()):
    def replace_in_file(path, old, new):
        full, rel = _resolve(root, path)
        _guard_git(rel)
        if rel.split("/")[0] in deny:
            raise PermissionError(f"writing {rel} is not allowed for this role")
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        count = text.count(old) if old else 0
        if count != 1:
            return (f"not changed: `old` must match exactly once in {rel}, "
                    f"found {count} matches. Read the file and copy the text exactly.")
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text.replace(old, new, 1))
        return f"replaced 1 occurrence in {rel}"
    return (_decl("replace_in_file",
                  "Replace one exact snippet in an existing file. `old` must occur exactly "
                  "once. Use this for changes to existing files (ADR-021).",
                  {"path": "File relative to the repository root.",
                   "old": "Exact existing text, including indentation.",
                   "new": "Replacement text."}, ["path", "old", "new"]), replace_in_file)


SECRET_ENV = ("GEMINI_API_KEY", "GROQ_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "AUTOSE_PAT")


def clean_env():
    """Environment for processes that run model-written code: no secrets."""
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
    env["UV_FROZEN"] = "1"  # never rewrite uv.lock
    return env


def run_pytest(root, timeout=900):
    """The one fixed test command. Used by the workflow and by the reviewer's `run_tests`."""
    proc = subprocess.run(
        ["uv", "run", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=root, capture_output=True, text=True, timeout=timeout, env=clean_env())
    return proc.returncode, proc.stdout + proc.stderr


def _run_tests(root):
    def run_tests():
        code, out = run_pytest(root)
        return f"exit code {code}\n" + out[-6000:]
    return (_decl("run_tests", "Run the repository's test suite. Takes no arguments.",
                  {}, []), run_tests)


def toolset(role, root):
    pairs = {
        "analyst": [_list_dir(root), _read_file(root)],
        "implementer": [_list_dir(root), _read_file(root),
                        _replace_in_file(root, deny=IMPLEMENTER_DENY),
                        _write_file(root, deny=IMPLEMENTER_DENY)],
        "tester": [_list_dir(root), _read_file(root),
                   _write_file(root, allow=("tests/",))],
        "reviewer": [_list_dir(root), _read_file(root), _run_tests(root)],
    }[role]
    return {decl["name"]: (decl, fn) for decl, fn in pairs}
