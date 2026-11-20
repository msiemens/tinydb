import json
import os

import pytest

from autose import checks, llm, tools

GOOD_SPEC = """# String ids in update

## Problem
x

## Acceptance criteria
- When `update()` is called with `doc_ids=['1']` and document 1 exists, it returns `[1]`.
- After `remove(doc_ids=['1'])`, document 1 is no longer in the table.

## Out of scope
y
"""


def test_spec_passes():
    assert checks.check_spec(GOOD_SPEC)[0]


def test_spec_needs_two_criteria():
    spec = GOOD_SPEC.replace("- After `remove(doc_ids=['1'])`, document 1 is no longer in the table.\n", "")
    ok, msg = checks.check_spec(spec)
    assert not ok and "at least 2" in msg


def test_spec_rejects_adjective_criterion():
    spec = GOOD_SPEC.replace("- After `remove(doc_ids=['1'])`, document 1 is no longer in the table.",
                             "- The code is clean and fast")
    assert not checks.check_spec(spec)[0]


def test_spec_missing_heading():
    assert not checks.check_spec("# t\n- a\n- b")[0]


def test_design_needs_existing_path_and_function(tmp_path):
    (tmp_path / "t.py").write_text("class T:\n    def update(self):\n        pass\n")
    good = "Change `t.py` and `T.update`."
    assert checks.check_design(good, str(tmp_path))[0]
    assert not checks.check_design("Change `missing.py` and `update`.", str(tmp_path))[0]
    assert not checks.check_design("Change `t.py` and `nothing`.", str(tmp_path))[0]


DIFF = "diff --git a/tinydb/table.py b/tinydb/table.py\n+x\n"


def test_verdict_ok_and_needs_file():
    files = checks.diff_files(DIFF)
    assert files == ["tinydb/table.py"]
    assert checks.check_verdict("verdict: approve\nChecked tinydb/table.py", files)[0] == "approve"
    assert checks.check_verdict("verdict: approve\nlooks good", files)[0] is None
    assert checks.check_verdict("approve\ntinydb/table.py", files)[0] is None
    assert checks.check_verdict("verdict: code\ntinydb/table.py: bug", files)[0] == "code"


def test_tools_stay_in_checkout(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tinydb").mkdir()
    impl = tools.toolset("implementer", str(tmp_path))
    write = impl["write_file"][1]
    assert write("tinydb/a.py", "x").startswith("wrote")
    for bad in ("../escape.py", "tests/t.py", ".github/workflows/x.yml", "autose/x.py", ".git/config"):
        with pytest.raises(PermissionError):
            write(bad, "x")
    tester = tools.toolset("tester", str(tmp_path))["write_file"][1]
    assert tester("tests/test_x.py", "x").startswith("wrote")
    with pytest.raises(PermissionError):
        tester("tinydb/a.py", "x")


def test_agents_cannot_read_hidden_tests(tmp_path):
    hidden = tmp_path / "experiment" / "hidden_tests"
    hidden.mkdir(parents=True)
    (hidden / "test_issue1.py").write_text("oracle", encoding="utf-8")
    read = tools.toolset("analyst", str(tmp_path))["read_file"][1]
    with pytest.raises(PermissionError):
        read("experiment/hidden_tests/test_issue1.py")


def test_role_tool_lists(tmp_path):
    root = str(tmp_path)
    assert set(tools.toolset("analyst", root)) == {"list_dir", "read_file"}
    assert "write_file" not in tools.toolset("reviewer", root)
    assert "run_tests" in tools.toolset("reviewer", root)
    assert "run_tests" not in tools.toolset("implementer", root)


def _reply(parts):
    return {"candidates": [{"content": {"role": "model", "parts": parts}}],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 2, "totalTokenCount": 3}}


def test_agent_loop_calls_tool_then_returns_text(tmp_path, monkeypatch):
    (tmp_path / "f.txt").write_text("hello")
    monkeypatch.setenv("AUTOSE_USAGE", str(tmp_path / "u.jsonl"))
    replies = iter([_reply([{"functionCall": {"name": "read_file", "args": {"path": "f.txt"}}}]),
                    _reply([{"text": "done"}])])
    seen = []

    def post(model, body):
        seen.append(json.loads(json.dumps(body)))
        return next(replies)

    out = llm.run_agent("analyst", "m", "sys", "go", tools.toolset("analyst", str(tmp_path)), post)
    assert out == "done"
    result = seen[1]["contents"][-1]["parts"][0]["functionResponse"]["response"]["result"]
    assert result == "hello"
    assert os.path.getsize(tmp_path / "u.jsonl") > 0


def test_agent_loop_budget(tmp_path):
    call = _reply([{"functionCall": {"name": "list_dir", "args": {}}}])
    with pytest.raises(llm.BudgetExceeded):
        llm.run_agent("analyst", "m", "s", "go", tools.toolset("analyst", str(tmp_path)),
                      lambda m, b: call)


def test_unknown_tool_error_goes_back_to_model(tmp_path):
    replies = iter([_reply([{"functionCall": {"name": "shell", "args": {"cmd": "ls"}}}]),
                    _reply([{"text": "ok"}])])
    seen = []

    def post(model, body):
        seen.append(json.loads(json.dumps(body)))
        return next(replies)

    llm.run_agent("analyst", "m", "s", "go", tools.toolset("analyst", str(tmp_path)), post)
    assert "unknown tool" in seen[1]["contents"][-1]["parts"][0]["functionResponse"]["response"]["result"]


def test_redact(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sekret")
    assert llm.redact("a sekret b") == "a *** b"
