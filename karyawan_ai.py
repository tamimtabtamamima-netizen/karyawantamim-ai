"""Entrypoint: orchestrator AI employee harian.

Pipeline:
    1. Fetch top Hacker News stories (input)
    2. Panggil LLM untuk membuat digest Bahasa Indonesia
    3. Simpan laporan markdown ke reports/
    4. Distribusi opsional: Slack + Email
    5. Update memori JSON
    6. Log structured output

Exit code:
    0 = sukses penuh
    1 = input fetch gagal
    2 = LLM gagal
    3 = save report gagal
"""
import json
import sys
from datetime import datetime, timezone

import config
import llm
import memory
import tools
from log import info, error


TASK_PROMPT = """Buat ringkasan harian teknologi dalam Bahasa Indonesia dari top stories Hacker News berikut.

Untuk SETIAP story, buat:
- **Judul** (terjemahkan ke Bahasa Indonesia jika perlu, tulis judul asli dalam tanda kurung)
- **Ringkasan 2 kalimat** tentang kenapa ini penting untuk developer/CTO
- **Link asli**

Di akhir, tambahkan section:
## Top 2 Hari Ini
Pilih 2 story paling penting dengan alasan 1 kalimat masing-masing.

Format: Markdown bersih, siap dibaca. Jangan mengarang URL.

Stories (JSON):
{stories_json}
"""

SYSTEM_PROMPT = """Anda adalah AI employee teknis yang tugasnya membuat digest berita teknologi harian dalam Bahasa Indonesia.

Aturan ketat:
- Output WAJIB Markdown valid
- Bahasa Indonesia natural, bukan terjemahan kaku
- Jangan mengarang URL yang tidak diberikan di input
- Jika story tidak punya URL eksternal, pakai HN item URL yang diberikan
- Jangan tambahkan preamble seperti "Berikut ringkasan..." — langsung ke konten"""


def _exit(code: int, reason: str) -> int:
    error("run aborting", code=code, reason=reason)
    return code


def run() -> int:
    start = datetime.now(timezone.utc)
    info("run started", at=start.isoformat())

    # 1. Input
    ok, stories = tools.fetch_hackernews_top()
    if not ok or not stories:
        return _exit(1, "no input data")
    info("input ready", count=len(stories))

    # 2. LLM call
    stories_compact = json.dumps(
        [{
            "title": s["title"],
            "url": s["url"],
            "score": s["score"],
            "hn_url": s["hn_url"],
        } for s in stories],
        ensure_ascii=False,
        indent=2,
    )
    prompt = TASK_PROMPT.format(stories_json=stories_compact)

    try:
        digest = llm.chat(prompt, system=SYSTEM_PROMPT)
    except RuntimeError as e:
        return _exit(2, str(e))
    info("digest generated", chars=len(digest))

    # 3. Save report
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ok_save, save_result = tools.save_report(
        f"Digest Teknologi {date_str}", digest
    )
    if not ok_save:
        return _exit(3, save_result)

    # 4. Distribute (opsional, gagal tidak fatal — tapi selalu di-log)
    short = digest[:500] + ("..." if len(digest) > 500 else "")
    slack_ok, slack_msg = tools.post_slack(
        f"*Digest Teknologi {date_str}*\n\n{short}"
    )
    email_ok, email_msg = tools.send_email(
        f"[AI Employee] Digest Teknologi {date_str}", digest
    )

    info("distribution done",
         slack_ok=slack_ok, slack_msg=slack_msg,
         email_ok=email_ok, email_msg=email_msg)

    # 5. Update memory
    state = memory.load()
    memory.append_task(state, "daily_digest", digest[:300])
    memory.save(state)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    info("run completed", elapsed_sec=round(elapsed, 1),
         report_path=save_result)
    return 0


if __name__ == "__main__":
    sys.exit(run())
