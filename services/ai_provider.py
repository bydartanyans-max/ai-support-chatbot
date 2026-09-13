import json
import os
import urllib.error
import urllib.request

SYSTEM_PROMPT = """You are a concise customer support assistant for a Romanian software company.
Answer in the same language as the user when possible. Be helpful, professional and brief.
If a request needs a human agent, clearly say so. Never invent prices or contractual promises."""

FAQ = {
    "program": "Programul de suport este Luni–Vineri, 09:00–18:00.",
    "pret": "Pentru o ofertă, spune-mi serviciul și cerințele principale. Un consultant poate confirma prețul final.",
    "preț": "Pentru o ofertă, spune-mi serviciul și cerințele principale. Un consultant poate confirma prețul final.",
    "contact": "Poți lăsa numele și datele de contact. Un coleg poate prelua solicitarea.",
    "refund": "Pentru rambursări este necesară verificarea comenzii de către un operator uman.",
}


def _mock_reply(message):
    text = message.lower()
    for keyword, answer in FAQ.items():
        if keyword in text:
            return answer
    if any(word in text for word in ["operator", "om", "human", "agent"]):
        return "Sigur. Marchez conversația pentru preluare de către un operator uman."
    return (
        "Mulțumesc pentru mesaj. Acesta este modul demo fără cheie AI. "
        "Pot răspunde la întrebări despre program, preț și contact; pentru alte solicitări, un operator poate prelua conversația."
    )


def _openai_reply(message, history):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history[-8:]:
        role = "assistant" if item.get("sender") == "assistant" else "user"
        messages.append({"role": role, "content": item.get("content", "")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "messages": messages,
            "temperature": 0.3,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError):
        return None


def _anthropic_reply(message, history):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    messages = []
    for item in history[-8:]:
        role = "assistant" if item.get("sender") == "assistant" else "user"
        messages.append({"role": role, "content": item.get("content", "")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps(
        {
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["content"][0]["text"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError):
        return None


def generate_reply(message, history):
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    if provider == "openai":
        result = _openai_reply(message, history)
        if result:
            return result, "openai"
    elif provider == "anthropic":
        result = _anthropic_reply(message, history)
        if result:
            return result, "anthropic"

    return _mock_reply(message), "mock"
