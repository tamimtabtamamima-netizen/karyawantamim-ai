# Karyawan AI — Digest Teknologi Harian

Karyawan AI gratis yang jalan otomatis tiap hari: ambil top stories Hacker News, ringkas dalam Bahasa Indonesia, simpan sebagai laporan markdown, lalu (opsional) kirim ke Slack & email.

**Biaya tetap: Rp 0.** Tidak perlu kartu kredit. Tidak perlu server.

---

## Cara Kerja

```
[Hacker News API] ──► [Groq LLM] ──► [reports/YYYY-MM-DD.md]
                                    ├─► [Slack] (opsional)
                                    ├─► [Email] (opsional)
                                    └─► [memory.json]
```

Setiap jalan, AI employee:
1. Fetch 5 story teratas dari Hacker News
2. Minta LLM (Groq, gratis) untuk membuat digest Bahasa Indonesia
3. Simpan laporan markdown di `reports/`
4. Kirim ringkasan ke Slack (jika dikonfigurasi)
5. Kirim full digest ke email (jika dikonfigurasi)
6. Update `memory.json` dengan ringkasan task

---

## Struktur File

| File | Tanggung Jawab |
|---|---|
| `karyawan_ai.py` | Orchestrator — koordinasi semua langkah |
| `llm.py` | Client Groq + retry dengan exponential backoff + full jitter |
| `tools.py` | 4 tool: fetch HN, save report, Slack, email |
| `memory.py` | Memori JSON dengan atomic write + size cap |
| `config.py` | Konfigurasi & env vars |
| `log.py` | Structured JSON logging ke stdout |
| `.github/workflows/daily.yml` | Scheduler GitHub Actions |
| `.env.example` | Template env vars |

---

## Setup (15 menit)

### Langkah 1 — Dapatkan API Key Groq (gratis)

1. Buka https://console.groq.com
2. Sign in dengan Google atau GitHub
3. Menu **API Keys** → **Create API Key**
4. Salin key-nya (format: `gsk_...`)

### Langkah 2 — Upload Project ke GitHub

**Opsi A — Upload via web:**
1. Download zip project ini, extract
2. Buat repo baru di GitHub (bisa private)
3. Drag-drop semua file ke repo

**Opsi B — Upload via git:**
```bash
cd karyawan-ai
git init
git add .
git commit -m "init: karyawan AI"
git branch -M main
git remote add origin https://github.com/USERNAME/karyawan-ai.git
git push -u origin main
```

### Langkah 3 — Set Secret WAJIB

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Name | Value |
|---|---|
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxxxxxxx` |

### Langkah 4 — Test Sekarang

1. Buka tab **Actions** di repo Anda
2. Klik workflow **Karyawan AI Harian** di sidebar kiri
3. Tombol **Run workflow** → pilih branch `main` → klik hijau **Run workflow**
4. Tunggu ~30 detik, klik run yang muncul untuk lihat log

Setelah sukses, cek folder `reports/` — file `YYYY-MM-DD.md` sudah ter-commit otomatis.

### Langkah 5 (Opsional) — Aktifkan Email via Resend

1. Daftar https://resend.com (3000 email/bulan gratis, tanpa kartu kredit)
2. Buat API key di dashboard
3. Tambah 3 secret di GitHub:
   - `RESEND_API_KEY` = key Resend Anda
   - `EMAIL_TO` = email tujuan (e.g. `anda@gmail.com`)
   - `RESEND_FROM` = `onboarding@resend.dev` (default free; atau pakai domain sendiri kalau sudah verifikasi)

### Langkah 6 (Opsional) — Aktifkan Slack

1. Buka https://api.slack.com/messaging/webhooks
2. Pilih channel → **Create New Webhook** → salin URL `https://hooks.slack.com/services/...`
3. Tambah secret di GitHub:
   - `SLACK_WEBHOOK_URL` = URL webhook

---

## Test Lokal (sebelum deploy)

```bash
# 1. Set env vars
export GROQ_API_KEY=gsk_xxxxx

# (opsional)
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export RESEND_API_KEY=re_xxxxx
export EMAIL_TO=anda@example.com

# 2. Run
python karyawan_ai.py
```

Output di stdout: log JSON terstruktur, satu event per baris. Contoh:
```json
{"ts": "2026-11-19T09:00:01+00:00", "level": "INFO", "msg": "run started", "at": "..."}
{"ts": "...", "level": "INFO", "msg": "HN fetched", "count": 5}
{"ts": "...", "level": "INFO", "msg": "digest generated", "chars": 1842}
{"ts": "...", "level": "INFO", "msg": "report saved", "path": "reports/2026-11-19.md"}
{"ts": "...", "level": "INFO", "msg": "run completed", "elapsed_sec": 4.2}
```

---

## Customisasi

### Ganti Tugas Utama

Edit `karyawan_ai.py`, ubah `TASK_PROMPT` dan `SYSTEM_PROMPT`. Beberapa ide:

- **Laporan cuaca kota**: ganti `fetch_hackernews_top` dengan call ke Open-Meteo (gratis)
- **Monitor harga produk**: ganti dengan scrape e-commerce
- **Rangkum PR terbuka**: ganti dengan GitHub API call ke repo Anda
- **Riset kompetitor**: ganti input dengan RSS feed blog kompetitor

### Ganti Model LLM

Set env var `GROQ_MODEL` ke salah satu:
- `llama-3.3-70b-versatile` (default, paling cerdas)
- `llama-3.1-8b-instant` (lebih cepat, lebih murah quota)
- `gemma2-9b-it`

### Ubah Jadwal

Edit `.github/workflows/daily.yml`, baris `cron`:
- `0 9 * * *` → jam 09:00 UTC (16:00 WIB) tiap hari
- `0 0,12 * * *` → 2x sehari (07:00 & 19:00 WIB)
- `0 9 * * 1` → tiap Senin jam 16:00 WIB

Generator cron: https://crontab.guru

---

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `GROQ_API_KEY not set` | Secret belum di-set | Settings → Secrets → tambah `GROQ_API_KEY` |
| HTTP 429 dari Groq | Rate limit free tier tercapai | Tunggu 1 menit, atau kurangi frekuensi cron |
| HTTP 401 dari Groq | API key salah/expired | Buat ulang key di console Groq |
| Workflow tidak jalan otomatis | Repo tidak aktif 60 hari | Push commit apa pun, atau trigger manual |
| `git push` gagal di workflow | Token permission kurang | Pastikan `permissions: contents: write` ada di workflow |
| Email tidak terkirim | Config kurang lengkap | Cek 3 secret: `RESEND_API_KEY`, `EMAIL_TO`, `RESEND_FROM` |
| Slack tidak post | Webhook salah channel | Buat ulang webhook di Slack API |

---

## Batasan & Quota Free Tier

| Layanan | Limit Free | Konsumsi Project Ini |
|---|---|---|
| Groq | ~30 req/menit, ~1000/hari (varies) | 1 request per run |
| GitHub Actions (public repo) | Unlimited | ~1 menit per run |
| GitHub Actions (private repo) | 2000 menit/bulan | ~30 menit/bulan |
| Resend | 3000 email/bulan | 30/bulan (jika daily) |
| Slack webhooks | Tidak ada limit publish | Unlimited |

---

## Prinsip Engineering yang Ditegakkan

- **Fail-closed**: jika config wajib hilang, langsung exit — bukan silent skip
- **No silent fallback**: setiap tool yang skip wajib log alasannya
- **Atomic write**: memory & report pakai `tmp + os.replace` untuk mencegah corrupt file
- **Bounded memory**: history di-cap 100 task, context di-cap 2000 chars
- **Retry dengan backoff + jitter**: LLM call tidak spam saat 429/5xx
- **Structured logging**: semua event JSON ke stdout, mudah di-parse di CI log
- **Zero dependency**: tidak perlu `pip install` apa pun, semua stdlib

---

## Lisensi

MIT — pakai bebas, modif bebas, jual bebas.
