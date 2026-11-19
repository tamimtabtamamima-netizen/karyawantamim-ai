"""Groq LLM client dengan retry + exponential backoff + full jitter.

Pre: GROQ_API_KEY ter-set di environment.
Post: return string non-empty dari LLM, atau raise RuntimeError.
"""
import json
import random
import time
import urllib.error
import urllib.request

import config
from log import warn


def chat(prompt: str, system: str = "") -> str:
    """Call Groq chat completion.

    Precondition:
        - config.GROQ_API_KEY non-empty
        - prompt non-empty
    Postcondition:
        - return non-empty string (stripped)
    Complexity: O(1) per call (network bound)
    Pure I/O: ya. Deterministic: tidak (network + LLM).

    Raises:
        RuntimeError: jika auth gagal (401) atau semua retry habis.
    """
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    if not prompt or not prompt.strip():
        raise RuntimeError("prompt empty")

    payload = json.dumps({
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system or "Anda asisten AI yang disiplin."},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.LLM_TEMPERATURE,
        "max_tokens": config.LLM_MAX_TOKENS,
    }).encode("utf-8")

    last_err: str = "unknown"
    for attempt in range(1, config.LLM_MAX_RETRIES + 1):
        try:
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
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            if not content or not content.strip():
                raise RuntimeError("LLM returned empty content")
            return content.strip()
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.reason}"
            # Auth error: jangan retry
            if e.code == 401:
                raise RuntimeError(f"auth failed: {last_err}")
            # Rate limit / server error: retry dengan backoff
            if e.code == 429 or 500 <= e.code < 600:
                wait = random.uniform(0, min(2 ** attempt, 30))
                warn("LLM retry", attempt=attempt, max=config.LLM_MAX_RETRIES,
                     wait_sec=round(wait, 1), err=last_err)
                time.sleep(wait)
                continue
            # Error lain (4xx): tidak retry
            raise RuntimeError(f"LLM HTTP error: {last_err}")
        except urllib.error.URLError as e:
            last_err = f"network: {e.reason}"
            wait = random.uniform(0, min(2 ** attempt, 30))
            warn("LLM network retry", attempt=attempt, wait_sec=round(wait, 1),
                 err=last_err)
            time.sleep(wait)
            continue
        except json.JSONDecodeError as e:
            last_err = f"json decode: {e}"
            warn("LLM JSON decode error", attempt=attempt, err=last_err)
            time.sleep(random.uniform(0, 2 ** attempt))
            continue

    raise RuntimeError(f"LLM exhausted {config.LLM_MAX_RETRIES} retries: {last_err}")
