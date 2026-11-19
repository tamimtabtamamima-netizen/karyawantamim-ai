"""LLM client dengan multi-provider support.

Auto-detect provider berdasarkan env vars:
    - GEMINI_API_KEY di-set → pakai Google Gemini (recommended)
    - GROQ_API_KEY di-set → pakai Groq
    - Keduanya di-set → prefer Gemini
    - Tidak ada → raise RuntimeError
"""
import json
import random
import time
import urllib.error
import urllib.request

import config
from log import warn, info


def _groq_chat(prompt: str, system: str) -> str:
    payload = json.dumps({
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system or "Anda asisten AI yang disiplin."},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.LLM_TEMPERATURE,
        "max_tokens": config.LLM_MAX_TOKENS,
    }).encode("utf-8")

    req = urllib.request.Request(
        config.GROQ_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_SEC) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        raise RuntimeError("Groq returned empty content")
    return content.strip()


def _gemini_chat(prompt: str, system: str) -> str:
    url = f"{config.GEMINI_URL_BASE}/models/{config.GEMINI_MODEL}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": config.LLM_TEMPERATURE,
            "maxOutputTokens": config.LLM_MAX_TOKENS,
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "x-goog-api-key": config.GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_SEC) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "error" in data:
        err = data["error"]
        raise RuntimeError(
            f"Gemini error: {err.get('message', 'unknown')} "
            f"(code {err.get('code', '?')})"
        )

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    content = "".join(p.get("text", "") for p in parts)
    if not content or not content.strip():
        finish_reason = candidates[0].get("finishReason", "?")
        raise RuntimeError(
            f"Gemini empty content (finishReason={finish_reason})"
        )
    return content.strip()


def chat(prompt: str, system: str = "") -> str:
    if not prompt or not prompt.strip():
        raise RuntimeError("prompt empty")

    if config.GEMINI_API_KEY:
        provider = "gemini"
        call_fn = _gemini_chat
        model_name = config.GEMINI_MODEL
    elif config.GROQ_API_KEY:
        provider = "groq"
        call_fn = _groq_chat
        model_name = config.GROQ_MODEL
    else:
        raise RuntimeError(
            "no LLM API key set. Set GEMINI_API_KEY (recommended) "
            "atau GROQ_API_KEY sebagai environment variable."
        )

    info("LLM call", provider=provider, model=model_name)

    last_err: str = "unknown"
    for attempt in range(1, config.LLM_MAX_RETRIES + 1):
        try:
            return call_fn(prompt, system)
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.reason}"
            if e.code == 401:
                raise RuntimeError(f"{provider} auth failed (401)")
            if e.code == 403:
                raise RuntimeError(
                    f"{provider} HTTP 403 Forbidden. Ganti provider/model."
                )
            if e.code == 400:
                body = e.read().decode("utf-8", errors="replace")[:300]
                raise RuntimeError(f"{provider} HTTP 400. Body: {body}")
            if e.code == 429 or 500 <= e.code < 600:
                wait = random.uniform(0, min(2 ** attempt, 30))
                warn("LLM retry", provider=provider, attempt=attempt,
                     max=config.LLM_MAX_RETRIES, wait_sec=round(wait, 1),
                     err=last_err)
                time.sleep(wait)
                continue
            raise RuntimeError(f"{provider} HTTP error: {last_err}")
        except urllib.error.URLError as e:
            last_err = f"network: {e.reason}"
            wait = random.uniform(0, min(2 ** attempt, 30))
            warn("LLM network retry", provider=provider, attempt=attempt,
                 wait_sec=round(wait, 1), err=last_err)
            time.sleep(wait)
            continue
        except json.JSONDecodeError as e:
            last_err = f"json decode: {e}"
            warn("LLM JSON decode error", provider=provider,
                 attempt=attempt, err=last_err)
            time.sleep(random.uniform(0, 2 ** attempt))
            continue

    raise RuntimeError(
        f"{provider} exhausted {config.LLM_MAX_RETRIES} retries: {last_err}"
    )
