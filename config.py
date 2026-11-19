"""Konfigurasi & konstanta. Semua secret wajib dari environment variable."""
import os
from pathlib import Path

# === LLM (Groq) ===
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL: str = "https://api.groq.com/openai/v1/chat/completions"
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
