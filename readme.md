LazyHunter

LazyHunter adalah tool otomatisasi recon dan scanning untuk bug hunter yang ingin kerja cepat dan efisien. Dirancang untuk pemula maupun profesional.

Fitur Utama
# 1. Lightscan  
   Scanning cepat menggunakan `subfinder`, `httpx`, dan `nuclei`. Cocok untuk pemeriksaan awal terhadap subdomain dan mendeteksi celah umum secara langsung.

# 2. Deepscan  (Premium)
   Scanning mendalam menggunakan kombinasi `Subfinder + Assetfinder -> httpx -> nuclei -> katana -> grep -> nuclei`.  
   Proses ini mencari subdomain sebanyak mungkin, menyaring yang aktif, mendeteksi celah keamanan, dan menemukan endpoint tersembunyi melalui crawling.

# 3. Find Sensitive Data  (Premium)
   Mencari file atau direktori sensitif seperti:
   - `.env`, `.git`, `.svn`
   - File backup (.zip, .bak, .old)
   - File credential atau konfigurasi

# 4. Manual Dorking  
   Melakukan pencarian secara manual di mesin pencari (Google, Bing, dll.) menggunakan teks dork pilihanmu. Cocok untuk hunting data secara spesifik.

# 5. Subdomain Takeover  
   Mengecek apakah subdomain yang ditemukan bisa di-takeover (diambil alih) menggunakan `nuclei` dengan template takeover. Berguna untuk mendeteksi aset yang tidak lagi aktif atau terkonfigurasi dengan buruk.

• Notifikasi ke Telegram
• Struktur folder otomatis untuk hasil scanning
• Akses ke list target dari platform bug bounty seperti
- hackerone
- bugcrowd
- yeswehack
- intigriti
- hackenproof
Cara penggunaan
pastikan go, python, dan requests sudah terinstall dan bisa digunakan
saran untuk install tool secara manual
- Subfinder
- Assetfinder
- httpx
- nuclei
- katana
python lazyhunter.py
(jika belum mengunduh tool tambahan, LazyHunter akan otomatis menginstall, tetapi kemungkinan akan belum bisa digunakan atau error mungkin dikarenakan dibutuhkan untuk pemindahn direktori dari tool yang diinstakk agar bisa digunakan, jika ada error bisa ditanyakan ke PHIMS)

pilih fitur yang diiginkan

# untuk membeli versi premium, kunjungi: https://lynk.id/aier/mloYxRr/

# Disclaimer!!!
Segala aktivitas yang dilakukan oleh pengguna tool ini diluar
tanggung jawab saya, Saya tidak bertanggung jawab atas penyalahgunaan
LazyHunter untuk aktivitas ilegal dan merugikan orang lain.
pengguna yang menggunakan tool ini sepenuhnya bertanggung jawab
atas tindakan yang dilakukan dengan LazyHunter ini
Gunakan dengan bijak dan penuh tanggung jawab.

# cara membuat bot  telegram  dan mengambil token dan chat id
tonton ini https://drive.google.com/file/d/1Kcy_tZXyWV4TxLk5Vq4pfyyiRkyKHxGo/view?usp=drivesdk
