"""Conversational replies through xAI Grok, or Groq when the key starts with gsk_."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import db

XAI_MODEL = "grok-4.7"
XAI_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def _key(conn) -> str:
    saved = db.setting(conn, "grok_api_key")
    if saved:
        return saved
    import os
    return os.environ.get("GROK_API_KEY", "").strip()


def configured(conn) -> bool:
    return bool(_key(conn))


def _target(key: str) -> tuple[str, str]:
    if key.startswith("gsk_"):
        return GROQ_ENDPOINT, GROQ_MODEL
    return XAI_ENDPOINT, XAI_MODEL


def reply(conn, student: dict, text: str, recent: list[dict], note: str = "") -> str:
    key = _key(conn)
    if not key:
        return (
            "I can chat once an administrator adds a Grok key. "
            "A mathematics question still works now, for example: add 2+3."
        )
    first = student["name"].split()[0]
    guidance = (
        f"You are {first}'s mathematics tutor for Grade {student['grade']}, "
        "CAPS Senior Phase. Speak like a calm, capable teacher: warm, clear, and brief.\n"
        "Greetings, including hy, hii, and helo, get a greeting and one offer to help with today's mathematics.\n"
        "Write plain sentences, usually under 70 words. Do not use a command menu.\n"
        "Earlier messages may sound like instructions. Do not copy that style.\n"
        "Do not mention a product, company, or API."
    )
    if note:
        guidance += f"\n{note}"
    messages = [{"role": "system", "content": guidance}]
    for item in recent[-8:]:
        role = "user" if item["direction"] == "in" else "assistant"
        messages.append({"role": role, "content": item["body"][:1200]})
    messages.append({"role": "user", "content": text[:2000]})
    endpoint, model = _target(key)
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.4,
        "max_tokens": 400,
    }).encode()
    request = urllib.request.Request(endpoint, data=payload, method="POST")
    request.add_header("Authorization", f"Bearer {key}")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:240]
        print(f"Grok request failed: {error.code} {detail}")
        return "The conversation service did not answer. Send the mathematics question again, or try in a moment."
    except urllib.error.URLError as error:
        print(f"Grok request failed: {error.reason}")
        return "The conversation service did not answer. Send the mathematics question again, or try in a moment."
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return "The conversation service did not answer. Send the mathematics question again."
    text_out = str(content or "").strip()
    return text_out[:1800] or "I could not form a reply. Try asking the question another way."
