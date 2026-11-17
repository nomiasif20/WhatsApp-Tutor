"""Conversational replies. Gemini is the default. Groq or xAI is the backup."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import db

XAI_MODEL = "grok-4.7"
XAI_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def _saved(conn, name: str, env_name: str) -> str:
    saved = db.setting(conn, name)
    if saved:
        return saved
    import os
    return os.environ.get(env_name, "").strip()


def _provider(conn) -> tuple[str, str, str, str]:
    gemini = _saved(conn, "gemini_api_key", "GEMINI_API_KEY")
    if gemini:
        return gemini, GEMINI_ENDPOINT, GEMINI_MODEL, "gemini"
    grok = _saved(conn, "grok_api_key", "GROK_API_KEY")
    if grok.startswith("gsk_"):
        return grok, GROQ_ENDPOINT, GROQ_MODEL, "groq"
    if grok:
        return grok, XAI_ENDPOINT, XAI_MODEL, "grok"
    return "", "", "", ""


def configured(conn) -> bool:
    return bool(_provider(conn)[0])


def reply(conn, student: dict, text: str, recent: list[dict], note: str = "") -> str:
    key, endpoint, model, provider = _provider(conn)
    if not key:
        return (
            "I can chat once an administrator adds a Gemini key. "
            "A mathematics question still works now, for example: add 2+3."
        )
    first = student["name"].split()[0]
    guidance = (
        f"You are {first}'s mathematics tutor for Grade {student['grade']}, "
        "CAPS Senior Phase. Speak like a calm, capable teacher: warm, clear, and brief.\n"
        "Greetings, including hy, hii, and helo, get a greeting and one offer to help with today's mathematics.\n"
        "Write plain sentences, usually under 70 words. Do not use a command menu.\n"
        "Write numbers and algebra in plain text, without dollar signs or markup.\n"
        "The earlier messages are this same conversation, from the desk and from WhatsApp. Remember them when the student refers back.\n"
        "Do not mention a product, company, or API."
    )
    if note:
        guidance += f"\n{note}"
    messages = [{"role": "system", "content": guidance}]
    for item in recent[-20:]:
        role = "user" if item["direction"] == "in" else "assistant"
        messages.append({"role": role, "content": item["body"][:1200]})
    messages.append({"role": "user", "content": text[:2000]})
    try:
        if provider == "gemini":
            text_out = _gemini(key, model, messages)
        else:
            text_out = _chat(key, endpoint, messages, model)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:240]
        print(f"Conversation request failed: {error.code} {detail}")
        return "The conversation service did not answer. Send the mathematics question again, or try in a moment."
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"Conversation request failed: {error}")
        return "The conversation service did not answer. Send the mathematics question again, or try in a moment."
    except (KeyError, IndexError, TypeError):
        return "The conversation service did not answer. Send the mathematics question again."
    return text_out[:1800] or "I could not form a reply. Try asking the question another way."


def _post(url: str, payload: dict, key: str, gemini: bool = False, timeout: int = 25) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", "Mozilla/5.0")
    if gemini:
        request.add_header("x-goog-api-key", key)
    else:
        request.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def _gemini(key: str, model: str, messages: list[dict]) -> str:
    names = []
    for name in ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", model):
        if name and name not in names:
            names.append(name)
    last = None
    for name in names:
        try:
            return _gemini_once(key, name, messages)
        except urllib.error.HTTPError as error:
            last = error
            if error.code not in (404, 429, 500, 503):
                raise
        except (TimeoutError, urllib.error.URLError, OSError) as error:
            last = error
            print(f"Conversation request failed: {name} {error}")
    if last:
        raise last
    raise RuntimeError("Gemini did not answer.")


def _gemini_once(key: str, model: str, messages: list[dict]) -> str:
    contents = []
    for item in messages[1:]:
        role = "model" if item["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})
    data = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {
            "systemInstruction": {"parts": [{"text": messages[0]["content"]}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 400,
            },
        },
        key,
        gemini=True,
        timeout=25,
    )
    parts = data["candidates"][0]["content"].get("parts") or []
    texts = [part.get("text", "") for part in parts if not part.get("thought")]
    return " ".join(piece.strip() for piece in texts if piece.strip())


def _chat(key: str, endpoint: str, messages: list[dict], model: str) -> str:
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.4,
        "max_tokens": 700,
    }
    data = _post(endpoint, body, key, gemini=False)
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content or "").strip()
