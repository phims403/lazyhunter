# LAZYHUNTER
adalah tool otomatisasi recon untuk bug hunter yang ingin kerja cepat dan efisien. Dirancang untuk pemula maupun profesional.

---

## Fitur Utama
### 1. Light Scan (Recon Cepat)
    - Subfinder + Assetfinder → menemukan subdomain
    - Httpx → validasi subdomain aktif (200)
    - Nuclei → scanning subdomain aktif menggunakan template umum seperti:
    misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
    - Kecepatan scan dapat disesuaikan (low/standard/fast).
    - Hasil scan dikirim otomatis ke Telegram.

---

### 2. Dark Scan (Recon menengah)
    - Subfinder + Assetfinder → menemukan subdomain
    - Httpx → validasi subdomain aktif (200)
    - Katana + Gau → Crawling URL berparameter dan .js.
    - Httpx → validasi URL aktif (200)
    - Pisahkan url berparameter dan url (.js)
    - Nuclei tahap 1: scan URL .js (tag exposure).
    - Nuclei tahap 2: scan URL berparameter (template dast).
    - Atur kecepatan scanning (nuclei) → Tersedia 3 opsi: Low, Standard, Fast.
    - Semua hasil dikirim ke Telegram secara otomatis.

---

### 3. Deep Scan (Recon Mendalam)
    - Subfinder + Assetfinder → menemukan subdomain
    - Httpx → validasi subdomain aktif (200)
    - Katana + Gau → Crawling URL berparameter dan .js.
    - Httpx → validasi URL aktif (200)
    - Pisahkan url berparameter dan url (.js)
    - Nuclei tahap 1: scan subdomain aktif (template umum).
    - Nuclei tahap 2: scan URL .js (tag exposure).
    - Nuclei tahap 3: scan URL berparameter (template dast).
    - Nuclei tahap 4: scan subdomain untuk cek potensi takeover.
    - Atur kecepatan scanning (nuclei) → Tersedia 3 opsi: Low, Standard, Fast.
    - Semua hasil dikirim ke Telegram secara otomatis.

---

### 4. Find Sensitive Data (Cari Data Sensitif Otomatis)
    - Menggunakan duckduckgo dork otomatis.
    - Dork seperti: site:target ext:env, .git/config, DB_PASSWORD, API_KEY, dll.
    - Mendeteksi file konfigurasi, kredensial, atau backup penting yang terbuka ke publik.
    - Hasil disimpan ke file teks.

---


### 5. Manual Dorking
    - Pengguna masukkan dork secara manual.
    - Melakukan pencarian di duckduckgo.
    - Cocok untuk OSINT, pencarian spesifik, atau file  unik.
    - Hasil disimpan ke file.

---

### 6. Subdomain Takeover Checker
    - Memiliki dua mode:
      • Massal → dari file list subdomain.
      • Wildcard → auto subdomain dengan subfinder + assetfinder.
    - Menggunakan Nuclei dengan template `takeovers` untuk memeriksa kemungkinan takeover.
    - Hasil scan dikirim ke Telegram.

---

### 7. Buat Laporan Kerentanan
    - Input judul kerentanan dan langkah validasi (PoC).
    - Gunakan API GPT dari OpenRouter untuk membuat laporan bug.
    - Laporan berisi: Judul, Deskripsi, PoC, Dampak, Mitigasi, dan Identitas pelapor.
    - Laporan dikirim ke Telegram dan disimpan.

---

### 8. Buat Laporan + Kirim via Email
    - Seperti fitur #6 namun laporan tidak dikirim ke telegram melainkan:
    - Laporan langsung dikirim via SMTP Gmail ke email tujuan yang ditentukan.
    - Cocok untuk laporan langsung ke vendor/security team.

---

• Notifikasi ke Telegram
• Struktur folder otomatis untuk hasil scanning
• Akses ke list target dari platform bug bounty seperti
- hackerone
- bugcrowd
- yeswehack
- intigriti
- hackenproof

# Cara Penggunaan LAZYHUNTER
## 📦 1. Persyaratan Awal (Install Manual)
Pastikan kamu sudah menginstall:
- Go (Golang) minimal versi 1.24
- Python 3
- pip

Untuk Debian/Kali Linux:
```bash
sudo apt update
sudo apt install golang-go python3 python3-pip -y
```

---

📥 2. Install Dependency Python
Install library Python yang dibutuhkan:
```bash
pip install -r requirements.txt
```

---

## ⚙️ 3. Install Tool Eksternal (ProjectDiscovery dan lainnya)
Gunakan script setup.sh untuk menginstall tool secara otomatis:
```bash
chmod +x setup.sh
./setup.sh
```
Script ini akan:
Menginstall:
- subfinder
- assetfinder
- katana
- gau
- httpx
- nuclei
- Menambahkan path Go binary ke shell kamu secara otomatis (permanen)

---

## 🚀 4. Jalankan LAZYHUNTER
Setelah semuanya siap, jalankan tool dengan:
```bash
python lazyhunter.py
```
pilih fitur yang diiginkan

---

# DISCLAIMER!!!
## Segala aktivitas yang dilakukan oleh pengguna tool ini diluar tanggung jawab saya, Saya tidak bertanggung jawab atas penyalahgunaan LAZYHUNTER untuk aktivitas ilegal dan merugikan orang lain.
## pengguna yang menggunakan tool ini sepenuhnya bertanggung jawab atas tindakan yang dilakukan dengan LAZYHUNTER ini, Gunakan dengan bijak dan penuh tanggung jawab.

---

##  • cara membuat bot  telegram  dan mengambil token dan chat id
### tonton ini
#### https://drive.google.com/file/d/12J-PEJcvJuv7PpX1DXBWQOCIQFcMIyeu/view?usp=drivesdk

## • cara membuat password gmail untuk config.py
### tonton ini
#### https://drive.google.com/file/d/12F5cYBm8b5KVKkKmsa_1Yenfrqvcv5IG/view?usp=drivesdk
