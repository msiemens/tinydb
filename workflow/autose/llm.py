"""Minimal Gemini client with a function-calling loop (ADR-005, ADR-006, ADR-009).
Groq is a fallback when Gemini stays unavailable (ADR-017)."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
GROQ_API = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"
# Tried in order after the requested model stays unavailable (ADR-018).
GEMINI_FALLBACKS = ("gemini-3.1-flash-lite",)
# Groq free tier counts max_tokens against an 8000 tokens-per-minute limit.
GROQ_MAX_OUTPUT_TOKENS = 2048
RETRY_CODES = (429, 500, 502, 503)
MAX_TOOL_ROUNDS = 16
MAX_OUTPUT_TOKENS = 8192


class BudgetExceeded(Exception):
    pass


class ProviderError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def redact(text):
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY"):
        key = os.environ.get(name)
        if key:
            text = text.replace(key, "***")
    return text


def _http(provider, url, headers, body, retries):
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        # Groq sits behind Cloudflare, which rejects the default
        # Python-urllib User-Agent with 403 "error code: 1010".
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "autose/1.0", **headers})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code in RETRY_CODES and attempt < retries:
                time.sleep(5 * 2 ** attempt)
                continue
            detail = redact(err.read().decode(errors="replace"))[:500]
            raise ProviderError(err.code, f"{provider} HTTP {err.code}: {detail}") from None


def _post(model, body, retries=3):
    """Call Gemini. If the model stays overloaded or out of quota, try the
    other Gemini lite model (ADR-018), then Groq if GROQ_API_KEY is set (ADR-017).
    A model named `groq:<id>` goes straight to Groq. AUTOSE_NO_FALLBACK=1 calls only
    the named model, for experiments that compare models (ADR-022)."""
    if model.startswith("groq:"):
        return _post_groq(body, retries, model[len("groq:"):])
    no_fallback = os.environ.get("AUTOSE_NO_FALLBACK") == "1"
    key = os.environ["GEMINI_API_KEY"]
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    names = (model,) if no_fallback else (
        (model,) + tuple(m for m in GEMINI_FALLBACKS if m != model))
    last = None
    for name in names:
        try:
            resp = _http("Gemini", API.format(name), headers, body, retries)
            if name != model:
                resp["servedBy"] = name
            return resp
        except ProviderError as err:
            if err.code not in RETRY_CODES:
                raise
            last = err
            print(f"::warning::Gemini {name} HTTP {err.code} after {retries} retries",
                  file=sys.stderr)
    if no_fallback or not os.environ.get("GROQ_API_KEY"):
        raise last
    print(f"::warning::falling back to Groq {GROQ_MODEL}", file=sys.stderr)
    return _post_groq(body, retries)


def _post_groq(body, retries=3, model=GROQ_MODEL):
    resp = _http("Groq", GROQ_API,
                 {"Content-Type": "application/json",
                  "Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
                 to_openai(body, model), retries)
    return from_openai(resp, model)


def _json_schema(schema):
    """Gemini schemas use upper-case type names; OpenAI-style APIs want JSON Schema."""
    if isinstance(schema, dict):
        return {k: (v.lower() if k == "type" and isinstance(v, str) else _json_schema(v))
                for k, v in schema.items()}
    if isinstance(schema, list):
        return [_json_schema(v) for v in schema]
    return schema


def to_openai(body, model):
    """Translate a Gemini generateContent body into a chat-completions body."""
    messages = []
    system = "".join(p.get("text", "")
                     for p in body.get("systemInstruction", {}).get("parts", []))
    if system:
        messages.append({"role": "system", "content": system})
    pending, n = [], 0
    for content in body.get("contents", []):
        parts = content.get("parts", [])
        if content.get("role") == "model":
            text = "".join(p.get("text", "") for p in parts)
            calls, pending = [], []
            for p in parts:
                if "functionCall" in p:
                    n += 1
                    call_id = f"call_{n}"
                    pending.append(call_id)
                    calls.append({"id": call_id, "type": "function", "function": {
                        "name": p["functionCall"]["name"],
                        "arguments": json.dumps(p["functionCall"].get("args", {}))}})
            msg = {"role": "assistant", "content": text or None}
            if calls:
                msg["tool_calls"] = calls
            messages.append(msg)
            continue
        replies = [p["functionResponse"] for p in parts if "functionResponse" in p]
        for i, reply in enumerate(replies):
            result = reply.get("response", {}).get("result", "")
            messages.append({"role": "tool",
                             "tool_call_id": pending[i] if i < len(pending) else f"call_x{i}",
                             "content": result if isinstance(result, str) else json.dumps(result)})
        text = "".join(p.get("text", "") for p in parts)
        if text:
            messages.append({"role": "user", "content": text})
    out = {"model": model, "messages": messages,
           "max_tokens": min(GROQ_MAX_OUTPUT_TOKENS,
                             body.get("generationConfig", {}).get("maxOutputTokens",
                                                                  MAX_OUTPUT_TOKENS))}
    decls = [d for t in body.get("tools", []) for d in t.get("functionDeclarations", [])]
    if decls:
        out["tools"] = [{"type": "function", "function": _json_schema(d)} for d in decls]
    return out


def from_openai(resp, model):
    """Translate a chat-completions response back into Gemini's response shape."""
    choices = resp.get("choices") or []
    if not choices:
        return {"candidates": [], "servedBy": model}
    msg = choices[0].get("message", {})
    parts = []
    if msg.get("content"):
        parts.append({"text": msg["content"]})
    for call in msg.get("tool_calls") or []:
        fn = call.get("function", {})
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        parts.append({"functionCall": {"name": fn.get("name", ""), "args": args}})
    if not parts:
        parts.append({"text": ""})
    usage = resp.get("usage", {})
    return {"candidates": [{"content": {"role": "model", "parts": parts}}],
            "usageMetadata": {"promptTokenCount": usage.get("prompt_tokens", 0),
                              "candidatesTokenCount": usage.get("completion_tokens", 0),
                              "totalTokenCount": usage.get("total_tokens", 0)},
            "servedBy": model}


def _log_usage(role, model, resp):
    path = os.environ.get("AUTOSE_USAGE")
    if not path:
        return
    meta = resp.get("usageMetadata", {})
    row = {"role": role, "model": resp.get("servedBy", model),
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
