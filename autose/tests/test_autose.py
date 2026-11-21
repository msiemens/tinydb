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


def test_ci_regression_vs_baseline():
    from autose.release import judge_ci
    checks_ = [{"name": "a", "bucket": "fail"}, {"name": "b", "bucket": "pass"},
               {"name": "c", "bucket": "fail"}]
    assert judge_ci(checks_, {"a", "c"}) == (False, [], ["a", "c"])      # all inherited
    assert judge_ci(checks_, {"a"}) == (False, ["c"], ["a"])             # c is new
    assert judge_ci([{"name": "a", "bucket": "pending"}], set())[0] is True


def test_groq_translation_round_trip():
    body = {"systemInstruction": {"parts": [{"text": "sys"}]},
            "generationConfig": {"maxOutputTokens": 100},
            "tools": [{"functionDeclarations": [{"name": "read_file", "description": "d",
                       "parameters": {"type": "OBJECT",
                                      "properties": {"path": {"type": "STRING"}}}}]}],
            "contents": [
                {"role": "user", "parts": [{"text": "go"}]},
                {"role": "model", "parts": [{"functionCall": {"name": "read_file",
                                                              "args": {"path": "a"}}}]},
                {"role": "user", "parts": [{"functionResponse": {
                    "name": "read_file", "response": {"result": "text"}}}]}]}
    out = llm.to_openai(body, "g")
    roles = [m["role"] for m in out["messages"]]
    assert roles == ["system", "user", "assistant", "tool"]
    call_id = out["messages"][2]["tool_calls"][0]["id"]
    assert out["messages"][3]["tool_call_id"] == call_id
    assert out["tools"][0]["function"]["parameters"]["type"] == "object"
    assert out["max_tokens"] == 100
    body["generationConfig"]["maxOutputTokens"] = 8192
    assert llm.to_openai(body, "g")["max_tokens"] == llm.GROQ_MAX_OUTPUT_TOKENS
    resp = llm.from_openai({"choices": [{"message": {"content": None, "tool_calls": [
        {"id": "x", "type": "function",
         "function": {"name": "read_file", "arguments": "{\"path\": \"b\"}"}}]}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}}, "g")
    part = resp["candidates"][0]["content"]["parts"][0]
    assert part["functionCall"] == {"name": "read_file", "args": {"path": "b"}}
    assert resp["servedBy"] == "g"


def test_gemini_overload_falls_back_to_groq(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.setenv("GROQ_API_KEY", "k2")
    seen = []

    def fake_http(provider, url, headers, body, retries):
        seen.append(provider if provider == "Groq" else url.split("/")[-1].split(":")[0])
        if provider == "Gemini":
            raise llm.ProviderError(503, "Gemini HTTP 503: busy")
        return {"choices": [{"message": {"content": "done"}}]}
    monkeypatch.setattr(llm, "_http", fake_http)
    resp = llm._post("m", {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]})
    assert seen == ["m", "gemini-3.1-flash-lite", "Groq"]
    assert resp["candidates"][0]["content"]["parts"][0]["text"] == "done"


def test_no_groq_key_keeps_gemini_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def fake_http(provider, url, headers, body, retries):
        raise llm.ProviderError(503, "Gemini HTTP 503: busy")
    monkeypatch.setattr(llm, "_http", fake_http)
    with pytest.raises(llm.ProviderError):
        llm._post("m", {"contents": []})


def test_second_gemini_model_answers_before_groq(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.setenv("GROQ_API_KEY", "k2")
    seen = []

    def fake_http(provider, url, headers, body, retries):
        seen.append(url)
        if "gemini-3.1-flash-lite" in url:
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        raise llm.ProviderError(503, "busy")
    monkeypatch.setattr(llm, "_http", fake_http)
    resp = llm._post("gemini-3.5-flash-lite", {"contents": []})
    assert resp["servedBy"] == "gemini-3.1-flash-lite"
    assert len(seen) == 2


def test_replace_in_file_edits_one_exact_match(tmp_path):
    (tmp_path / "tinydb").mkdir()
    f = tmp_path / "tinydb" / "a.py"
    f.write_text("x = 1\ny = 1\n")
    replace = tools.toolset("implementer", str(tmp_path))["replace_in_file"][1]
    assert "replaced" in replace("tinydb/a.py", "x = 1", "x = 2")
    assert f.read_text() == "x = 2\ny = 1\n"
    assert "found 2 matches" in replace("tinydb/a.py", "= ", "=")
    assert "found 0 matches" in replace("tinydb/a.py", "z = 9", "z = 0")
    with pytest.raises(PermissionError):
        replace("tests/t.py", "a", "b")


def test_clean_env_drops_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "secret")
    assert "GROQ_API_KEY" not in tools.clean_env()


def test_groq_prefix_goes_straight_to_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k2")
    seen = []

    def fake_http(provider, url, headers, body, retries):
        seen.append((provider, body.get("model")))
        return {"choices": [{"message": {"content": "ok"}}]}
    monkeypatch.setattr(llm, "_http", fake_http)
    resp = llm._post("groq:openai/gpt-oss-20b", {"contents": []})
    assert seen == [("Groq", "openai/gpt-oss-20b")]
    assert resp["servedBy"] == "openai/gpt-oss-20b"


def test_no_fallback_calls_only_the_named_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.setenv("GROQ_API_KEY", "k2")
    monkeypatch.setenv("AUTOSE_NO_FALLBACK", "1")
    seen = []

    def fake_http(provider, url, headers, body, retries):
        seen.append(url)
        raise llm.ProviderError(503, "busy")
    monkeypatch.setattr(llm, "_http", fake_http)
    with pytest.raises(llm.ProviderError):
        llm._post("gemini-3.5-flash-lite", {"contents": []})
    assert len(seen) == 1
