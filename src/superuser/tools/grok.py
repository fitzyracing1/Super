"""Call Grok (xAI) via the official chat completions API.

Phone-first design: pure requests + stdlib, zero extra dependencies,
runs cleanly in Termux / proot-distro on phone.
"""

from __future__ import annotations

import os
from typing import Any

import requests

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-3"


def call_grok(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Send a prompt to Grok and return the response + metadata.

    Requires XAI_API_KEY (or GROK_API_KEY) in the environment.
    """
    key = api_key or os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not key:
        return {
            "status": "error",
            "error": "XAI_API_KEY or GROK_API_KEY not set",
            "hint": "export XAI_API_KEY=... before starting the superuser MCP server",
        }

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, min(max_tokens, 8192)),
        "temperature": max(0.0, min(temperature, 2.0)),
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(XAI_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Grok API timed out after 60s"}
    except requests.exceptions.HTTPError as e:
        detail = ""
        if e.response is not None:
            detail = e.response.text[:500]
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code if e.response is not None else '?'}",
            "detail": detail or str(e),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

    try:
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        return {
            "status": "ok",
            "model": data.get("model", model),
            "content": content,
            "finish_reason": choice.get("finish_reason"),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "id": data.get("id"),
        }
    except (KeyError, IndexError, TypeError) as e:
        return {
            "status": "error",
            "error": f"Unexpected response shape: {e}",
            "raw": data,
        }
