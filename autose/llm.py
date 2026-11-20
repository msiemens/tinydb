"""Minimal Gemini client with a function-calling loop (ADR-005, ADR-006, ADR-009)."""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
MAX_TOOL_ROUNDS = 8
MAX_OUTPUT_TOKENS = 8192


class BudgetExceeded(Exception):
    pass


def redact(text):
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        text = text.replace(key, "***")
    return text


def _post(model, body, retries=3):
    key = os.environ["GEMINI_API_KEY"]
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            API.format(model), data=data,
            headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(5 * 2 ** attempt)
                continue
            detail = redact(err.read().decode(errors="replace"))[:500]
            raise RuntimeError(f"Gemini HTTP {err.code}: {detail}") from None


def _log_usage(role, model, resp):
    path = os.environ.get("AUTOSE_USAGE")
    if not path:
        return
    meta = resp.get("usageMetadata", {})
    row = {"role": role, "model": model,
           "prompt": meta.get("promptTokenCount", 0),
           "output": meta.get("candidatesTokenCount", 0),
           "thoughts": meta.get("thoughtsTokenCount", 0),
           "total": meta.get("totalTokenCount", 0)}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def run_agent(role, model, system, user_text, tools=None, post=_post):
    """Run one agent to completion. `tools` maps name -> (declaration, callable)."""
    tools = tools or {}
    contents = [{"role": "user", "parts": [{"text": user_text}]}]
    body_base = {"systemInstruction": {"parts": [{"text": system}]},
                 "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS}}
    if tools:
        body_base["tools"] = [{"functionDeclarations": [d for d, _ in tools.values()]}]
    for _ in range(MAX_TOOL_ROUNDS + 1):
        resp = post(model, dict(body_base, contents=contents))
        _log_usage(role, model, resp)
        cands = resp.get("candidates") or []
        if not cands or "content" not in cands[0]:
            raise RuntimeError("Gemini returned no content: "
                               + redact(json.dumps(resp)[:300]))
        content = cands[0]["content"]
        contents.append(content)
        parts = content.get("parts", [])
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if not calls:
            return "".join(p.get("text", "") for p in parts).strip()
        replies = []
        for call in calls:
            name, args = call["name"], call.get("args", {})
            try:
                if name not in tools:
                    raise ValueError(f"unknown tool {name}")
                result = tools[name][1](**args)
            except Exception as exc:  # reported to the model, not fatal
                result = f"ERROR: {type(exc).__name__}: {exc}"
            replies.append({"functionResponse": {
                "name": name, "response": {"result": result}}})
        contents.append({"role": "user", "parts": replies})
    raise BudgetExceeded(f"{role}: more than {MAX_TOOL_ROUNDS} tool rounds")
