"""Konfigurasi & konstanta. Semua secret wajib dari environment variable.

Auto-detect provider:
    - Kalau GEMINI_API_KEY di-set → pakai Google Gemini (recommended, free, available di Indonesia)
    - Kalau hanya GROQ_API_KEY di-set → pakai Groq
"""
import os
from pathlib import Path

# === LLM Provider: Google Gemini (recommended) ===
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
GEMINI_URL_BASE: str = "https://generativelanguage.googleapis.com/v1beta"

# === LLM Provider: Groq (fallback) ===
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY") or ""
GROQ_MODEL: str = os.environ.get("GROQ_MODEL") or "llama-3.1-8b-instant"
GROQ_URL: str = "https://api.groq.com/openai/v1/chat/completions"

# === LLM common ===
LLM_TIMEOUT_SEC: int = 60
LLM_MAX_RETRIES: int = 3
LLM_TEMPERATURE: float = 0.3
LLM_MAX_TOKENS: int = 2048

# === Memori ===
MEMORY_PATH: Path = Path("memory.json")
MEMORY_MAX_CONTEXT_CHARS: int = 2000
MEMORY_MAX_TASKS: int = 100

# === Laporan ===
REPORTS_DIR: Path = Path("reports")

# === Tool: Email (Resend, opsional) ===
RESEND_API_KEY: str = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM: str = os.environ.get("RESEND_FROM", "AI Employee <onboarding@resend.dev>")
EMAIL_TO: str = os.environ.get("EMAIL_TO", "")

# === Tool: Slack (opsional) ===
SLACK_WEBHOOK_URL: str = os.environ.get("SLACK_WEBHOOK_URL", "")

# === Tool: Hacker News ===
HN_TOP_N: int = 5
HN_TIMEOUT_SEC: int = 15
HN_API_BASE: str = "https://hacker-news.firebaseio.com/v0"

# === Logging ===
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
