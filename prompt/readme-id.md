# AI Bug Bounty Hunting Prompts

Paket prompt untuk menjalankan **AI agent** (Claude Code, Command Code, OpenCode, dll.) sebagai **bug bounty hunter** yang otomatis hunting target kamu dengan exhaustive.

## Isi Folder

| File | Fungsi |
|------|--------|
| `SUPER_PROMPT_BUG_BOUNTY_AI.md` | **Main prompt** — manual lengkap hunting (metodologi, aturan tool, validasi, struktur output). Ini yang di-referensikan oleh goal prompt. |
| `goal-prompt.txt` | **Goal prompt sesi pertama** — untuk memulai hunting baru pada satu target. |
| `goal-prompt-continue-session.txt` | **Goal prompt sesi lanjutan** — untuk melanjutkan hunting yang sudah berjalan (bisa dipakai berulang di sesi AI baru). |

---

## Cara Pakai

### 1. Scan Target Dulu dengan LazyHunter

Sebelum pakai AI, kamu **wajib** menjalankan LazyHunter untuk target yang mau di-hunt:

```bash
python lazyhunter.py -dps -t target.com -s fast
```

> **Disarankan pakai Deep Scan (`-dps`)** karena menghasilkan data paling lengkap: subdomain, active, crawled URLs, param, JS files, sensitive data, nuclei results, dan takeover — semua yang dibutuhkan AI sebagai attack surface.

Output-nya akan tersimpan di folder seperti:
```
target_output/target.com/
├── subdomains.txt
├── active.txt
├── crawled_filtered.txt
├── param.txt
├── js.txt
├── nuc_active.txt / nuc_exp.txt / nuc_dast.txt
├── 200_sens.txt / 403_sens.txt
└── ...
```
(atau folder per-tipe seperti `subdomain/`, `active/`, `crawled_filtered/` dll. jika pakai mode `by_type`).

### 2. Pilih AI Agent

Disarankan memakai AI agent yang punya fitur **`/goal`** (mode autonomous loop), contoh: **Command Code**. Agent lain seperti Claude Code / OpenCode juga bisa, tapi fitur `/goal` membuat AI terus bekerja sampai target tercapai tanpa berhenti.

### 3. Buka Goal Prompt & Sesuaikan Path

Buka file `goal-prompt.txt` (untuk sesi pertama) di editor, lalu ubah **2 bagian**:

**a) Baris pertama — path ke main prompt:**

```
/goal @/home/phims/lazyhunter-update/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
```

Ubah path-nya sesuai lokasi folder prompt di komputer kamu. Contoh:
```
/goal @/home/user/lazyhunter-update/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
/goal @/Users/user/lazyhunter/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
```

**b) Bagian bawah — target & output LazyHunter:**

```
*TARGET: ganti-ini-dengan-domain-target.com
@(mention directory/file output lazyhunter)
```

- Ganti `*TARGET` dengan domain yang mau di-hunt (contoh: `example.com`).
- Ganti bagian `@(mention ...)` dengan **mention folder output LazyHunter** untuk target itu, misalnya:
  ```
  @/home/user/lazyhunter/target_output/example.com
  ```
  atau mention beberapa file sekaligus:
  ```
  @/home/user/lazyhunter/target_output/example.com/subdomains.txt
  @/home/user/lazyhunter/target_output/example.com/param.txt
  ```

### 4. Jalankan

Paste seluruh isi goal prompt yang sudah disesuaikan ke AI agent (atau simpan sebagai file lalu `/goal @file`), lalu Enter. AI akan:
1. Membaca main prompt (manual hunting).
2. Membaca semua file output LazyHunter dari folder yang di-mention.
3. Membuat folder workspace `prompt-engineering-{model}-{timestamp}/`.
4. Hunting secara exhaustive sampai goal (50 critical vulnerabilities) tercapai atau sesi berakhir.

### 5. Sesi Lanjutan (Continue)

Saat sesi AI berhenti (batas turn tercapai) sebelum goal tercapai — ini normal — kamu bisa lanjut:

1. Buka `goal-prompt-continue-session.txt`.
2. Sesuaikan **path main prompt** (baris pertama) dan **target + folder output** (bagian bawah) — **target harus sama** dengan sesi sebelumnya.
3. Jalankan di sesi AI baru.

AI akan otomatis:
- Mencari folder workspace lama (`prompt-engineering-*`) dengan target yang sama.
- Membaca `super-report.md` dan `hunting_log_endpoints_tested.txt` dari sesi sebelumnya.
- **Melanjutkan** dari titik terakhir — tidak mengulang dari nol, tidak menemukan ulang vulnerability yang sudah ada (anti-duplikasi).

---

## Tips Model AI

- **Disarankan pakai model `deepseek-v4-flash`** (atau varian flash-nya) — model ini sudah bagus untuk tugas bug bounty seperti ini tapi **murah**, cocok untuk sesi autonomous yang panjang dan berulang.
- Model yang lebih besar bisa dipakai untuk target yang kompleks, tapi biayanya jauh lebih tinggi karena sesi hunting bisa sangat panjang.

---

## Disclaimer

Hanya gunakan tool dan prompt ini pada target yang **kamu miliki** atau yang **memang mengizinkan** pengujian (bug bounty program). Penyalahgunaan untuk aktivitas ilegal di luar tanggung jawab pemilik tool.
