"""Tools yang bisa dipakai AI employee.

Setiap tool return Tuple[bool, str/data]:
    (True, result)  jika sukses
    (False, reason) jika gagal atau skip — selalu dengan alasan eksplisit.
Tidak ada silent fallback.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any

import config
from log import info, warn, error


def fetch_hackernews_top(n: int = 0) -> Tuple[bool, List[Dict[str, Any]]]:
    """Ambil top N cerita Hacker News. Gratis, tanpa auth.

    Pre: n >= 1 (jika 0, pakai config.HN_TOP_N).
    Post: return (True, list) atau (False, []).
    Complexity: O(n) HTTP calls.
    """
    if n <= 0:
        n = config.HN_TOP_N
    n = max(1, min(n, 10))  # bound 1..10

    try:
        with urllib.request.urlopen(
            f"{config.HN_API_BASE}/topstories.json",
            timeout=config.HN_TIMEOUT_SEC,
        ) as r:
            ids = json.loads(r.read())[:n]
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        error("HN topstories fetch failed", err=str(e))
        return False, []

    stories: List[Dict[str, Any]] = []
    for sid in ids:
        try:
            with urllib.request.urlopen(
                f"{config.HN_API_BASE}/item/{sid}.json",
                timeout=config.HN_TIMEOUT_SEC,
            ) as r:
                item = json.loads(r.read())
            stories.append({
                "title": item.get("title", "(no title)"),
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                "score": item.get("score", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={sid}",
            })
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            warn("HN item fetch skipped", id=sid, err=str(e))
            continue

    info("HN fetched", count=len(stories))
    return True, stories


def save_report(title: str, content: str) -> Tuple[bool, str]:
    """Simpan laporan markdown ke reports/YYYY-MM-DD.md. Atomic write.

    Pre: title & content non-empty.
    Post: file ada di disk, return (True, path).
    """
    if not title or not content:
        return False, "title or content empty"

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = config.REPORTS_DIR / f"{date_str}.md"

    body = (
        f"# {title}\n\n"
        f"_Generated {datetime.now(timezone.utc).isoformat()}_\n\n"
        f"---\n\n{content}\n"
    )
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)
    info("report saved", path=str(path))
    return True, str(path)


def send_email(subject: str, body: str) -> Tuple[bool, str]:
    """Kirim email via Resend. Skip dengan log eksplisit kalau belum dikonfigurasi.

    Pre: subject & body non-empty.
    Post: (True, id) jika terkirim, (False, reason) jika skip/gagal.
    """
    if not subject or not body:
        return False, "subject or body empty"
    if not config.RESEND_API_KEY:
        warn("email skipped", reason="RESEND_API_KEY not set")
        return False, "not_configured"
    if not config.EMAIL_TO:
        warn("email skipped", reason="EMAIL_TO not set")
        return False, "no_recipient"

    payload = json.dumps({
        "from": config.RESEND_FROM,
        "to": [config.EMAIL_TO],
        "subject": subject,
        "text": body,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        info("email sent", id=str(data.get("id", "?")))
        return True, str(data.get("id", "ok"))
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:200]
        error("email HTTP error", code=e.code, body=body_err)
        return False, f"http_{e.code}"
    except urllib.error.URLError as e:
        error("email network error", err=str(e.reason))
        return False, "network_error"


def post_slack(message: str) -> Tuple[bool, str]:
    """Post pesan ke Slack via incoming webhook. Skip dengan log kalau belum dikonfigurasi.

    Pre: message non-empty.
    Post: (True, resp) atau (False, reason).
    """
    if not message:
        return False, "message empty"
    if not config.SLACK_WEBHOOK_URL:
        warn("slack skipped", reason="SLACK_WEBHOOK_URL not set")
        return False, "not_configured"

    # Slack cap ~3000 chars
    truncated = message[:2900] + ("..." if len(message) > 2900 else "")
    payload = json.dumps({"text": truncated}).encode("utf-8")

    try:
        req = urllib.request.Request(
            config.SLACK_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = r.read().decode("utf-8")
        if resp != "ok":
            warn("slack non-ok response", resp=resp[:100])
        info("slack posted")
        return True, resp
    except urllib.error.HTTPError as e:
        error("slack HTTP error", code=e.code)
        return False, f"http_{e.code}"
    except urllib.error.URLError as e:
        error("slack network error", err=str(e.reason))
        return False, "network_error"
