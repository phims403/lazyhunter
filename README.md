# LAZYHUNTER
adalah tool otomatisasi recon dan scanning untuk bug hunter yang ingin kerja cepat dan efisien. Dirancang untuk pemula maupun profesional.

---

## Fitur Utama
### 1. Light Scan (Pemindaian Cepat)
   - Subfinder → mencari subdomain dari target domain.
   - Httpx → memfilter subdomain aktif (respon HTTP).
   - Nuclei → scanning subdomain aktif menggunakan template umum seperti:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
   - Kecepatan scan dapat disesuaikan (low/standard/fast).
   - Hasil scan dikirim otomatis ke Telegram.

---

### 2. Deep Scan (Pemindaian Mendalam)
   - Subfinder + Assetfinder → mencari sebanyak mungkin subdomain dari target.
   - Gabungkan dan hilangkan duplikat hasil.
   - Httpx → validasi subdomain aktif.
   - Nuclei tahap 1 → scan awal menggunakan template umum seperti:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
   - Katana → crawling URL untuk mencari parameter dari subdomain aktif.
   - Grep → filter URL yang memiliki parameter (?key=value).
   - Nuclei tahap 2 → scan url hasil crawling dengan template DAST (Dynamic Analysis) untuk deteksi kerentanan seperti xss, sqli, lfi.
   - Kecepatan scan dapat disesuaikan (low/standard/fast).
   - Semua hasil dikirim otomatis ke Telegram.

---

### 3. Find Sensitive Data (Cari Data Sensitif Otomatis)
   - Menggunakan duckduckgo dork otomatis.
   - Dork seperti: site:target ext:env, .git/config, DB_PASSWORD, API_KEY, dll.
   - Mendeteksi file konfigurasi, kredensial, atau backup penting yang terbuka ke publik.
   - Hasil disimpan ke file teks.

---


### 4. Manual Dorking
   - Pengguna masukkan dork secara manual.
   - Melakukan pencarian di duckduckgo.
   - Cocok untuk OSINT, pencarian spesifik, atau file unik.
   - Hasil disimpan ke file.

---

### 5. Subdomain Takeover Checker
   - Memiliki dua mode:
     • Massal → dari file list subdomain.
     • Wildcard → auto subdomain dengan subfinder.
   - Menggunakan Nuclei dengan template `takeovers` untuk memeriksa kemungkinan takeover.
   - Hasil scan dikirim ke Telegram.

---

### 6. Buat Laporan Kerentanan
   - Input judul kerentanan dan langkah validasi (PoC).
   - Gunakan API GPT dari OpenRouter untuk membuat laporan bug.
   - Laporan berisi: Judul, Deskripsi, PoC, Dampak, Mitigasi, dan Identitas pelapor.
   - Laporan dikirim ke Telegram dan disimpan.

---

### 7. Buat Laporan + Kirim via Email
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
- Go (Golang)
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
- httpx
- nuclei
- katana
- assetfinder
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
#### https://drive.google.com/file/d/1Kcy_tZXyWV4TxLk5Vq4pfyyiRkyKHxGo/view?usp=drivesdk

## • cara membuat password gmail untuk config.py
