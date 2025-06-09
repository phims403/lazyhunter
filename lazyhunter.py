import os
import subprocess
import shutil
import requests
import tempfile
import random
import time
import json
import smtplib
from config import OPENROUTER_API_KEY
from bs4 import BeautifulSoup
from config import BOT_TOKEN, CHAT_ID
from config import OPENROUTER_API_KEY, EMAIL_PENGIRIM, EMAIL_PASSWORD, NAMA_PELAPOR
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs, unquote
def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)
def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()
OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
OUTPUT_FOLDER_NUCLEI = "nuclei"
OUTPUT_FOLDER_KATANA = "katana"
OUTPUT_FOLDER_SENSITIVE_DATA = "sensitive_data"
OUTPUT_FOLDER_DORKING = "dorking"
OUTPUT_FOLDER_GREP = "grep"
OUTPUT_FOLDER_TAKEOVER = "take_over"
OUTPUT_FOLDER_REPORT = "reports"
os.makedirs(OUTPUT_FOLDER_REPORT, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_GREP, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_DORKING, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_KATANA, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SENSITIVE_DATA, exist_ok=True)

def print_logo():
    logo = r"""
 ██▓    ▄▄▄      ▒███████▒▓██   ██▓ ██░ ██  █    ██  ███▄    █ ▄▄▄█████▓▓█████  ██▀███  
▓██▒   ▒████▄    ▒ ▒ ▒ ▄▀░ ▒██  ██▒▓██░ ██▒ ██  ▓██▒ ██ ▀█   █ ▓  ██▒ ▓▒▓█   ▀ ▓██ ▒ ██▒
▒██░   ▒██  ▀█▄  ░ ▒ ▄▀▒░   ▒██ ██░▒██▀▀██░▓██  ▒██░▓██  ▀█ ██▒▒ ▓██░ ▒░▒███   ▓██ ░▄█ ▒
▒██░   ░██▄▄▄▄██   ▄▀▒   ░  ░ ▐██▓░░▓█ ░██ ▓▓█  ░██░▓██▒  ▐▌██▒░ ▓██▓ ░ ▒▓█  ▄ ▒██▀▀█▄  
░██████▒▓█   ▓██▒▒███████▒  ░ ██▒▓░░▓█▒░██▓▒▒█████▓ ▒██░   ▓██░  ▒██▒ ░ ░▒████▒░██▓ ▒██▒
░ ▒░▓  ░▒▒   ▓▒█░░▒▒ ▓░▒░▒   ██▒▒▒  ▒ ░░▒░▒░▒▓▒ ▒ ▒ ░ ▒░   ▒ ▒   ▒ ░░   ░░ ▒░ ░░ ▒▓ ░▒▓░
░ ░ ▒  ░ ▒   ▒▒ ░░░▒ ▒ ░ ▒ ▓██ ░▒░  ▒ ░▒░ ░░░▒░ ░ ░ ░ ░░   ░ ▒░    ░     ░ ░  ░  ░▒ ░ ▒░
  ░ ░    ░   ▒   ░ ░ ░ ░ ░ ▒ ▒ ░░   ░  ░░ ░ ░░░ ░ ░    ░   ░ ░   ░         ░     ░░   ░ 
    ░  ░     ░  ░  ░ ░     ░ ░      ░  ░  ░   ░              ░             ░  ░   ░     
                 ░         ░ ░                                                          
                                  
╔════════════════════════════════════════════════════════╗
║                    PREMIUM VERSION 1.1.3               ║
╠════════════════════════════════════════════════════════╣
║ Author     : PHIMS                                     ║
║ GitHub     : github.com/phims403                       ║
║ Instagram  : @aier_phims                               ║
║ Telegram   : @phimssec                                 ║
╚════════════════════════════════════════════════════════╝
    """
    print(logo)
def tampilkan_menu():
    print("\n=== Pilih Jenis Scan ===")
    print("0. Informasi fitur")
    print("1. Light Scan")
    print("2. Deep Scan")
    print("3. Find Sensitive Data")
    print("4. Manual Dorking")
    print("5. Check Subdomain Takeover")
    print("6. Buat Laporan Kerentanan dengan AI")
    print("7. Buat Laporan dan Kirim via Email")
    print("99. Keluar")
    while True:
        pilihan = input("Masukkan pilihan (0-7 atau 99 untuk keluar): ").strip()
        if pilihan in ["0", "1", "2", "3", "4", "5", "6", "7", "99"]:
            return pilihan
        print("[❌] Pilihan tidak valid. Masukkan 0-7 atau 99")
def get_target_input():
    """Meminta input URL target langsung dari pengguna."""
    while True:
        target = input("Masukkan URL target (contoh: example.com): ").strip()
        if target:
            return target
        print("[❌] URL tidak valid! Masukkan URL yang benar.")
def fitur_info():
    info = r"""
=== INFORMASI FITUR ===

1. Light Scan (Pemindaian Cepat)
   - Subfinder → mencari subdomain dari target domain.
   - Httpx → memfilter subdomain aktif (respon HTTP).
   - Nuclei → scanning subdomain aktif menggunakan template umum seperti:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
   - Kecepatan scan dapat disesuaikan (low/standard/fast).
   - Hasil scan dikirim otomatis ke Telegram.

2. Deep Scan (Pemindaian Mendalam)
   - Subfinder + Assetfinder → mencari sebanyak mungkin subdomain dari target.
   - Gabungkan dan hilangkan duplikat hasil.
   - Httpx → validasi subdomain aktif.
   - Nuclei tahap 1 → scan awal menggunakan template umum seperti:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
   - Katana → crawling URL untuk mencari parameter dari subdomain aktif.
   - Grep → filter URL yang memiliki parameter (?key=value).
   - Nuclei tahap 2 → scan url hasil crawling untuk deteksi kerentanan seperti xss, sqli, lfi, dll.
   - Kecepatan scan dapat disesuaikan (low/standard/fast).
   - Semua hasil dikirim otomatis ke Telegram.

3. Find Sensitive Data (Cari Data Sensitif Otomatis)
   - Menggunakan duckduckgo dork otomatis.
   - Dork seperti: site:target ext:env, .git/config, DB_PASSWORD, API_KEY, dll.
   - Mendeteksi file konfigurasi, kredensial, atau backup penting yang terbuka ke publik.
   - Hasil disimpan ke file teks.

4. Manual Dorking
   - Pengguna masukkan dork secara manual.
   - Melakukan pencarian di duckduckgo.
   - Cocok untuk OSINT, pencarian spesifik, atau file unik.
   - Hasil disimpan ke file.

5. Subdomain Takeover Checker
   - Memiliki dua mode:
     • Massal → dari file list subdomain.
     • Wildcard → auto subdomain dengan subfinder.
   - Menggunakan Nuclei dengan template `takeovers` untuk memeriksa kemungkinan takeover.
   - Hasil scan dikirim ke Telegram.

6. Buat Laporan Kerentanan
   - Input judul kerentanan dan langkah validasi (PoC).
   - Gunakan API GPT dari OpenRouter untuk membuat laporan bug.
   - Laporan berisi: Judul, Deskripsi, PoC, Dampak, Mitigasi, dan Identitas pelapor.
   - Laporan dikirim ke Telegram dan disimpan.

7. Buat Laporan + Kirim via Email
   - Seperti fitur #6 namun laporan tidak dikirim ke telegram melainkan:
   - Laporan langsung dikirim via SMTP Gmail ke email tujuan yang ditentukan.
   - Cocok untuk laporan langsung ke vendor/security team.

"""
    print(info)
def buat_laporan_dan_kirim_email():
    print("\n=== Form Kirim Laporan via Email ===")
    vuln = input("Judul / Jenis Kerentanan yang ditemukan  : ").strip()
    validasi = input("Langkah Validasi (PoC)    : ").strip()
    email_tujuan = input("Email tujuan              : ").strip()
    nama_file = vuln.lower().replace(" ", "_")
    prompt = f"""
Buatkan teks laporan kerentanan profesional dalam bahasa Indonesia dengan struktur sebagai berikut:

1. Judul Kerentanan
2. Deskripsi Kerentanan
3. Langkah-langkah Eksploitasi / Validasi
4. Dampak atau Impact dari Kerentanan
5. Rekomendasi Mitigasi / Perbaikan
6. Detail Pelapor (hanya Nama dan Email)

Data Input:
- Nama Pelapor: {NAMA_PELAPOR}
- Email Pelapor: {EMAIL_PENGIRIM}
- Jenis Kerentanan: {vuln}
- Langkah Validasi / PoC: {validasi}

Instruksi:
- Deskripsikan dan perjelas kerentanan berdasarkan nama atau tipe yang diberikan, bantu lengkapi eksploitasi dan dampaknya, dan berikan rekomendasi teknis sesuai standar laporan bug hunter.
- Buat laporan formal dan profesional.
- Di bagian *Detail Pelapor*, cukup tuliskan:
  Nama: [nama]
  Email: [email]
- Jangan menambahkan kalimat tambahan seperti “laporan ini disusun dengan tujuan...” atau "saya bersedia memberikan informasi tambahan bla bla bla bla ...." intinya saja
- Gunakan gaya bahasa profesional dan formal sesuai standar bug hunter report. Ringkas, jelas, dan langsung ke inti masalah. Format laporan dalam bentuk teks biasa, tidak ada markdown, tanpa tanggal.

Tulis laporan berdasarkan input di atas.
"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        hasil = response.json()
        pesan_ai = hasil["choices"][0]["message"]["content"]
        if not os.path.exists(OUTPUT_FOLDER_REPORT):
            os.makedirs(OUTPUT_FOLDER_REPORT)
        path_file = os.path.join(OUTPUT_FOLDER_REPORT, f"{nama_file}.txt")
        with open(path_file, "w", encoding="utf-8") as f:
            f.write(pesan_ai)
        print(f"\n[💾] Laporan disimpan: {path_file}")
        print("[📤] Mengirim email...")
        try:
            subject = f"[Laporan Keamanan] - {vuln}"
            msg = MIMEMultipart()
            msg["From"] = EMAIL_PENGIRIM
            msg["To"] = email_tujuan
            msg["Subject"] = subject
            msg.attach(MIMEText(pesan_ai, "plain"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_PENGIRIM, EMAIL_PASSWORD)
                server.sendmail(EMAIL_PENGIRIM, email_tujuan, msg.as_string())
            print("[✅] Laporan berhasil dikirim ke email.")
        except Exception as e:
            print("[❌] Gagal mengirim email.")
            print("Error:", str(e))
    else:
        print("[❌] Gagal memproses OpenRouter API.")
        print("Kode:", response.status_code)
        print(response.text)
def cek_takeover_massal():
    nama_file = input("Masukkan nama file yang berisi daftar domain/subdomain (contoh: subdomain.txt): ").strip()
    if not os.path.isfile(nama_file):
        print("[❌] File tidak ditemukan.")
        return
    output_nama = input("Masukkan nama output file (tanpa .txt): ").strip()
    if not output_nama:
        print("[❌] Nama file output tidak boleh kosong.")
        return
    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_nama}.txt")
    print(f"[🚨] Menjalankan nuclei takeover scan untuk file: {nama_file}")
    cmd = [
        "nuclei", "-l", nama_file,
        "-t", "takeovers",
        "-o", output_path
    ]
    if jalankan_tool(cmd, "nuclei takeover (massal)", nama_file):
        kirim_laporan_telegram(output_path, f"Takeover Massal ({output_nama})")
        print(f"[✅] Scan selesai. Hasil di: {output_path}")
def cek_takeover_wildcard():
    domain = input("Masukkan domain (contoh: example.com): ").strip()
    if not domain:
        print("[❌] Domain tidak boleh kosong.")
        return
    sub_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{domain}.txt")
    print(f"[🔍] Mencari subdomain dengan Subfinder untuk: {domain}")
    if not jalankan_tool(["subfinder", "-d", domain, "-o", sub_file], "subfinder", domain):
        return
    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{domain}.txt")
    print(f"[🚨] Menjalankan nuclei takeover scan untuk: {domain}")
    cmd = [
        "nuclei", "-l", sub_file,
        "-t", "takeovers",
        "-o", output_path
    ]
    if jalankan_tool(cmd, "nuclei takeover (wildcard)", domain):
        kirim_laporan_telegram(output_path, f"Takeover Wildcard ({domain})")
        print(f"[✅] Scan selesai. Hasil di: {output_path}")
def gabungkan_subdomain(subfinder_file, target):
    """Menjalankan assetfinder, lalu gabungkan hasil tanpa duplikat."""
    print("[🔍] Menjalankan Assetfinder...")
    assetfinder_tmp = tempfile.NamedTemporaryFile(delete=False).name
    jalankan_tool(["assetfinder", "--subs-only", target], "assetfinder", target)
    with open(assetfinder_tmp, "w") as out:
        subprocess.run(["assetfinder", "--subs-only", target], stdout=out)
    all_subs = set()
    for path in [subfinder_file, assetfinder_tmp]:
        with open(path, "r") as f:
            all_subs.update(line.strip() for line in f if line.strip())
    with open(subfinder_file, "w") as f:
        f.write("\n".join(sorted(all_subs)))
    print(f"[✅] Subdomain hasil digabung dan disimpan di: {subfinder_file}")
def bersihkan_link(link):
    if link.startswith("//"):
        link = "https:" + link
    parsed = urlparse(link)
    if 'duckduckgo.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        if 'uddg' in qs:
            return unquote(qs['uddg'][0])
    return link
SENSITIVE_DORKS = [
    'site:{target} ext:env',
    'site:{target} ext:log',
    'site:{target} ext:sql',
    'site:{target} ext:bak',
    'site:{target} ext:ini',
    'site:{target} ext:yaml',
    'site:{target} ext:yml',
    'site:{target} inurl:".git/config"',
    'site:{target} inurl:"/phpinfo.php"',
    'site:{target} "DB_PASSWORD"',
    'site:{target} "API_KEY="',
    'site:{target} "api_key="',
    'site:{target} "AWS_SECRET_ACCESS_KEY"',
    'site:{target} "Authorization: Bearer"',
    'site:{target} "PRIVATE KEY-----"',
    'site:{target} "access_token="',
    'site:{target} "smtp_password"',
    'site:{target} "mail_password"',
    'site:{target} "s3.amazonaws.com"'
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X)"
]
def google_dork_search(target, output_file):
    print(f"[🔍] Memulai pencarian dorking untuk: {target}")
    hasil = []
    for dork_template in SENSITIVE_DORKS:
        dork = dork_template.format(target=target)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        url = f"https://html.duckduckgo.com/html?q={dork}"
        print(f"[⚙️] Mencari: {dork}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for result in soup.find_all('a', class_='result__a'):
                link = result.get('href')
                if link:
                  bersih = bersihkan_link(link)
                  print(f"[✅] {bersih}")
                  hasil.append(bersih)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"[❌] Error saat mencari dork '{dork}': {e}")
    with open(output_file, "w") as f:
        for url in hasil:
            f.write(url + "\n")
    print(f"[📁] Hasil dork disimpan di: {output_file}")
def manual_dorking(output_file):
    dork = input("Masukkan dork manual: ").strip()
    if not dork:
        print("[❌] Dork tidak boleh kosong.")
        return
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    url = f"https://html.duckduckgo.com/html?q={dork}"
    print(f"[🔍] Mencari: {dork}")
    hasil = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for result in soup.find_all('a', class_='result__a'):
            link = result.get('href')
            if link:
              bersih = bersihkan_link(link)
              print(f"[✅] {bersih}")
              hasil.append(bersih)
        time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"[❌] Gagal mencari: {e}")
    with open(output_file, "w") as f:
        for url in hasil:
            f.write(url + "\n")
    print(f"[📁] Hasil disimpan di: {output_file}")
def jalankan_tool(command, tool_name, target):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[❌] Error saat menjalankan {tool_name} untuk {target}: {e}")
        return False
    except Exception as e:
        print(f"[⚠️] Kesalahan tidak terduga saat menjalankan {tool_name} untuk {target}: {e}")
        return False
    return True
def buat_laporan_kerentanan():
    print("\n=== Form Laporan Kerentanan ===")
    vuln = input("Judul / Jenis Kerentanan yang ditemukan  : ").strip()
    validasi = input("Langkah Validasi (PoC)    : ").strip()
    nama_file = input("Nama file untuk menyimpan laporan (tanpa .txt): ").strip()
    prompt = f"""
Buatkan teks laporan kerentanan profesional dalam bahasa Indonesia dengan struktur sebagai berikut:

1. Judul Kerentanan
2. Deskripsi Kerentanan
3. Langkah-langkah Eksploitasi / Validasi
4. Dampak atau Impact dari Kerentanan
5. Rekomendasi Mitigasi / Perbaikan
6. Detail Pelapor (hanya Nama dan Email)

Data Input:
- Nama Pelapor: {NAMA_PELAPOR}
- Email Pelapor: {EMAIL_PENGIRIM}
- Jenis Kerentanan: {vuln}
- Langkah Validasi / PoC: {validasi}

Instruksi:
- Deskripsikan dan perjelas kerentanan berdasarkan nama atau tipe yang diberikan, bantu lengkapi eksploitasi dan dampaknya, dan berikan rekomendasi teknis sesuai standar laporan bug hunter.
- Buat laporan formal dan profesional.
- Di bagian *Detail Pelapor*, cukup tuliskan:
  Nama: [nama]
  Email: [email]
- Jangan menambahkan kalimat tambahan seperti “laporan ini disusun dengan tujuan...” atau "saya bersedia memberikan informasi tambahan bla bla bla bla ...." intinya saja
- Gunakan gaya bahasa profesional dan formal sesuai standar bug hunter report. Ringkas, jelas, dan langsung ke inti masalah. Format laporan dalam bentuk teks biasa, tidak ada markdown, tanpa tanggal.

Tulis laporan berdasarkan input di atas.
"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        hasil = response.json()
        pesan_ai = hasil["choices"][0]["message"]["content"]
        print("\n=== Laporan yang Dihasilkan ===")
        print(pesan_ai)
        path_file = os.path.join(OUTPUT_FOLDER_REPORT, f"{nama_file}.txt")
        with open(path_file, "w", encoding="utf-8") as f:
            f.write(pesan_ai)
        print(f"\n[💾] Laporan berhasil disimpan di: {path_file}")
        print("\n[📤] Mengirim ke Telegram...")
        kirim_laporan_telegram_teks_report(path_file)
        print("[✅] Laporan berhasil dikirim ke Telegram.")
    else:
        print("[❌] Gagal memproses dengan OpenRouter API.")
        print("Kode:", response.status_code)
        print(response.text)
def tanya_kecepatan_scan():
    print("\nSeberapa cepat ingin scan?")
    print("1. Low (cocok untuk low device)")
    print("2. Standar (standar nuclei)")
    print("3. Fast (cocok untuk scan banyak target)")
    pilihan = input("Pilih (1/2/3): ").strip()
    if pilihan == "1":
        return ["-c", "10", "--max-host-error", "20"]
    elif pilihan == "2":
        return ["-c", "25", "--max-host-error", "30"]
    elif pilihan == "3":
        return ["-c", "30", "--max-host-error", "40"]
    else:
        print("[❌] Pilihan tidak valid. Default ke Standar.")
        return ["-c", "25", "--max-host-error", "30"]
def process_domain(target, scan_type):
    """Melakukan scanning untuk satu domain."""
    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
    nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
    katana_output = os.path.join(OUTPUT_FOLDER_KATANA, f"katana_{target}.txt")
    nuclei_output_katana = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_{target}_katana.txt")
    katana_filtered_output = os.path.join(OUTPUT_FOLDER_GREP, f"grep_{target}_katana.txt")
    if scan_type == "1":
        scan_args = tanya_kecepatan_scan()
        print(f"\n[▶] Memulai proses untuk {target}")
        print(f"\n[🔎] Mencari subdomain dengan Subfinder untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return
        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-o", active_file], "httpx", target):
            return
        print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
        if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-severity", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot", "-timeout", "5", "-retries", "1", "-ept", "ssl", *scan_args, "-o", nuclei_output_httpx ], "nuclei (HTTPX)", target):
          return
        kirim_laporan_telegram(nuclei_output_httpx, f"{target} (HTTPX)")
    elif scan_type in "2":
        scan_args = tanya_kecepatan_scan()
        print(f"\n[▶] Memulai proses untuk {target}")
        print(f"\n[🔎] Mencari subdomain (Subfinder, Assetfinder) untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return
        gabungkan_subdomain(subdomain_file, target)
        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-o", active_file], "httpx", target):
            return
        print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
        if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-severity", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", nuclei_output_httpx ], "nuclei (HTTPX)", target):
          return
        kirim_laporan_telegram(nuclei_output_httpx, f"{target} (HTTPX)")
        print("[🕷️] Menjalankan crawling dengan Katana...")
        if not jalankan_tool(["katana", "-list", active_file, "-d", "3", "-fs", "fqdn", "-f", "qurl", "-o", katana_output], "katana", target):
          return
        cmd = f'grep -E "\\?.+=" "{katana_output}" > "{katana_filtered_output}"'
        subprocess.run(cmd, shell=True)
        print("[🚨] Menjalankan Nuclei scan (Katana crawled result)...")
        if not jalankan_tool([ "nuclei", "-l", katana_filtered_output, "-dast", "-fa", "high", "-severity", "medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", nuclei_output_katana ], "nuclei (Katana)", target):
          return
        kirim_laporan_telegram(nuclei_output_katana, f"{target} (Katana Crawled domain)")
        print(f"[✅] Scanning selesai untuk: {target}\n")
    elif scan_type == "3":
      output_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sensitivedata_{target}.txt")
      google_dork_search(target, output_file)
    elif scan_type == "4":
      nama_file = input("Masukkan nama file untuk menyimpan hasil (contoh: hasil_dork.txt): ").strip()
      if not nama_file:
          print("[❌] Nama file tidak boleh kosong.")
      else:
          output_file = os.path.join(OUTPUT_FOLDER_DORKING, nama_file)
          manual_dorking(output_file)
def kirim_laporan_telegram(path_file, domain, max_len=4000):
    if not token_valid(BOT_TOKEN) or not chat_id_valid(CHAT_ID):
        print("[ℹ️] Token bot atau chat_id tidak ditemukan / tidak valid. Melewati pengiriman Telegram.")
        return
    if not os.path.exists(path_file):
        print(f"[⚠️] File laporan {path_file} tidak ditemukan.")
        return
    try:
        with open(path_file, "r") as file:
            lines = file.readlines()
        if not lines:
            lines = [f"[ℹ️] Tidak ada kerentanan ditemukan untuk {domain}.\n"]
        header = f"[Laporan nuclei untuk {domain}]\n\n"
        chunks = []
        current_chunk = header
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for line in lines:
            if len(current_chunk) + len(line) > max_len:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line
        if current_chunk.strip():
            chunks.append(current_chunk)
        for i, pesan in enumerate(chunks):
            response = requests.post(url, data={
                'chat_id': CHAT_ID,
                'text': pesan
            })
            if response.status_code == 200:
                print(f"[✅] Bagian {i+1} laporan {domain} berhasil dikirim.")
            else:
                print(f"[❌] Gagal kirim bagian {i+1} laporan {domain}: {response.text}")
                break
    except Exception as e:
        print(f"[⚠️] Terjadi kesalahan saat mengirim ke Telegram: {e}")
def kirim_laporan_telegram_teks_report(path_file):
    if not token_valid(BOT_TOKEN) or not chat_id_valid(CHAT_ID):
        print("[ℹ️] Token bot atau chat_id tidak ditemukan / tidak valid. Melewati pengiriman Telegram.")
        return
    if not os.path.exists(path_file):
        print(f"[⚠️] File laporan {path_file} tidak ditemukan.")
        return
    try:
        with open(path_file, "r") as file:
            isi = file.read()
        if not isi.strip():
            isi = f"[ℹ️] Tidak ada teks laporan."
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            'chat_id': CHAT_ID,
            'text': f"[Text Report]\n\n{isi}"
        })
        if response.status_code == 200:
            print(f"[✅]  Teks laporan berhasil dikirim ke Telegram.")
        else:
            print(f"[❌] Gagal kirim laporan Telegram  {response.text}")
    except Exception as e:
        print(f"[⚠️] Terjadi kesalahan saat mengirim ke Telegram: {e}")
def main():
    print_logo()
    target = get_target_input()
    print(f"\n?? Memproses domain: {target}\n")
    process_domain(target)
    print("[??] Proses selesai untuk domain tersebut!")
if __name__ == "__main__":
    print_logo()
    while True:
        scan_type = tampilkan_menu()
        if scan_type == "99":
            print("[✔] Keluar dari program. Terima kasih!")
            break
        if scan_type in ["1", "2", "3"]:
            target = get_target_input()
            process_domain(target, scan_type)
        elif scan_type == "4":
            process_domain(None, "4")
        elif scan_type == "5":
            print("\n=== Mode Takeover ===")
            print("1. Massal (dari file)")
            print("2. Wildcard (subfinder otomatis)")
            sub_mode = input("Pilih mode (1/2): ").strip()
            if sub_mode == "1":
                cek_takeover_massal()
            elif sub_mode == "2":
                cek_takeover_wildcard()
            else:
                print("[❌] Pilihan tidak valid.")
        elif scan_type == "0":
            fitur_info()
        elif scan_type == "6":
            buat_laporan_kerentanan()
        elif scan_type == "7":
            buat_laporan_dan_kirim_email()
