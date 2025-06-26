import os
import subprocess
import shutil
import requests
import tempfile
import random
import time
import json
import smtplib
import base64
import sys
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs, unquote
from config import BOT_TOKEN, CHAT_ID, EMAIL_PENGIRIM, EMAIL_PASSWORD, NAMA_PELAPOR
from env import GITHUB_TOKEN, GITHUB_USER, GITHUB_REPO, OPENROUTER_API_KEY




def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)
def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()
    
    

    
    
OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "crawled"
OUTPUT_FOLDER_NUCLEI = "nuclei"
OUTPUT_FOLDER_CRAWLED = "crawled"
OUTPUT_FOLDER_SENSITIVE_DATA = "sensitive_data"
OUTPUT_FOLDER_DORKING = "dorking"
OUTPUT_FOLDER_GREP = "crawled_filtered"
OUTPUT_FOLDER_TAKEOVER = "take_over"
OUTPUT_FOLDER_REPORT = "reports"
os.makedirs(OUTPUT_FOLDER_REPORT, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_GREP, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_DORKING, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_CRAWLED, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SENSITIVE_DATA, exist_ok=True)

LOCAL_VERSION = "1.2.0"
def get_status_version():
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/version.txt"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            encoded_content = data.get("content", "")
            decoded = base64.b64decode(encoded_content).decode("utf-8").strip()
            if decoded == LOCAL_VERSION:
                return f"{LOCAL_VERSION} (\033[92mupdated\033[0m)"  # green
            else:
                return f"{LOCAL_VERSION} (\033[91moutdate\033[0m)"  # red
        else:
            print("[DEBUG] Failed to get content.")
            return f"{LOCAL_VERSION} (\033[93munknown\033[0m)"
    except Exception as e:
        print("[DEBUG] Exception:", e)
        return f"{LOCAL_VERSION} (\033[93moffline\033[0m)"








def print_logo():
    version_status = get_status_version().ljust(43)
    red = "\033[91m"
    reset = "\033[0m"
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
"""
    print(red + logo + reset)
    
    
    print(f"                                LAZYHUNTER v{version_status}")
    print("Author     : PHIMS                Status      : $$PREMIUM$$")
    print("Instagram  : @aier_phims          GitHub      : github.com/phims403")
    print("Youtube    : elphims              Telegram    : @phimssec")
                    
def tampilkan_menu():
    print("\n    Choose Feature:")
    print("  [0]  Feature Information")
    print("  [1]  Light Scan")
    print("  [2]  Dark Scan (\033[92mNEW\033[0m)")
    print("  [3]  Deep Scan (\033[91mTOP FEATURE\033[0m)")
    print("  [4]  Find Sensitive Data")
    print("  [5]  Manual Dorking")
    print("  [6]  Scan Subdomain Takeover")
    print("  [7]  Generate Report -> Send To Telegram")
    print("  [8]  Generate Report -> Send To Email Target (\033[91mTOP FEATURE\033[0m)")
    print("  [99] Out ")
    print("  [999] Update Tool")
    print("──────────────────────────────────────────────────────────────────────────────")
    while True:
        pilihan = input("Choose Feature (0-8, 99, or 999): ").strip()
        if pilihan in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "99", "999"]:
            return pilihan
        print("[❌] Pilihan tidak valid. Masukkan angka 0-8, 99, atau 999")
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

4. Find Sensitive Data (Cari Data Sensitif Otomatis)
   - Menggunakan duckduckgo dork otomatis.
   - Dork seperti: site:target ext:env, .git/config, DB_PASSWORD, API_KEY, dll.
   - Mendeteksi file konfigurasi, kredensial, atau backup penting yang terbuka ke publik.
   - Hasil disimpan ke file teks.

5. Manual Dorking
   - Pengguna masukkan dork secara manual.
   - Melakukan pencarian di duckduckgo.
   - Cocok untuk OSINT, pencarian spesifik, atau file unik.
   - Hasil disimpan ke file.

6. Subdomain Takeover Checker
   - Memiliki dua mode:
     • Massal → dari file list subdomain.
     • Wildcard → auto subdomain dengan subfinder.
   - Menggunakan Nuclei dengan template `takeovers` untuk memeriksa kemungkinan takeover.
   - Hasil scan dikirim ke Telegram.

7. Buat Laporan Kerentanan
   - Input judul kerentanan dan langkah validasi (PoC).
   - Gunakan API GPT dari OpenRouter untuk membuat laporan bug.
   - Laporan berisi: Judul, Deskripsi, PoC, Dampak, Mitigasi, dan Identitas pelapor.
   - Laporan dikirim ke Telegram dan disimpan.

8. Buat Laporan + Kirim via Email
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
    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{domain}.txt")
    print(f"[🔍] Mencari subdomain dengan Subfinder untuk: {domain}")
    if not jalankan_tool(["subfinder", "-d", domain, "-o", subdomain_file], "subfinder", domain):
        return
    gabungkan_subdomain(subdomain_file, domain)
    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{domain}.txt")
    print(f"[🚨] Menjalankan nuclei takeover scan untuk: {domain}")
    cmd = [
        "nuclei", "-l", subdomain_file,
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Mozilla/5.0 (X11; Linux x86_64)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
    'Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X)',
   #Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
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

def tanya_kecepatan_scan():
    pilihan = input("\nSelect Scanning Speed: 1.Low, 2.Standar, 3.Fast: ").strip()
    if pilihan == "1":
        return ["-c", "10", "--max-host-error", "20"]
    elif pilihan == "2":
        return ["-c", "25", "--max-host-error", "30"]
    elif pilihan == "3":
        return ["-c", "40", "--max-host-error", "50"]
    else:
        print("[❌] Pilihan tidak valid. Default ke Standar.")
        return ["-c", "25", "--max-host-error", "30"]





def process_domain(target, scan_type):
    """Melakukan scanning untuk satu domain."""
    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
    nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
    katana_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_katana_{target}.txt")
    gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"{target}_gau.txt")
    nuclei_output_crawled = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_{target}_crawled.txt")
    crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
    temp_crawled_filtered_output = os.path.join (OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt")
    
    if scan_type == "1":
        scan_args = tanya_kecepatan_scan()
        print(f"\n[▶] Memulai proses untuk {target}")
        print(f"\n[🔎] Mencari subdomain dengan Subfinder untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return

        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-mc", "200", "-t", "100", "-o", active_file], "httpx", target):
            return
        print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
        if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-severity", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot", "-timeout", "5", "-retries", "1", "-ept", "ssl", *scan_args, "-o", nuclei_output_httpx ], "nuclei (HTTPX)", target):
          return
        kirim_laporan_telegram(nuclei_output_httpx, f"{target} (WITHOUT PARAMETER)")
    elif scan_type == "2":
        scan_args = tanya_kecepatan_scan()
        print(f"\n[▶] Memulai proses untuk {target}")
        print(f"\n[🔎] Mencari subdomain (Subfinder, Assetfinder) untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return
        gabungkan_subdomain(subdomain_file, target)
       
        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-mc", "200", "-t", "100", "-o", active_file], "httpx", target):
            return
        
        print("[🕷️] Menjalankan crawling dengan Katana...")
        if not jalankan_tool(["katana", "-list", active_file,"-jc" , "-d", "3", "-fs", "fqdn", "-f", "qurl", "-o", katana_output], "katana", target):
            return
        
        print("[🕷️] Menjalankan crawling dengan gau...")
        
        # Jalankan gau
        try:
            with open(gau_output, "w") as outfile:
                subprocess.run([
                    "gau", target,
                    "--subs",
                    "--threads", "20",
                    "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico,txt,json",
                    "--verbose"
                ], stdout=outfile)
        except Exception as e:
            print(f"[⚠️] Gagal menjalankan gau: {e}")
            return
        
        print("[📦] Menggabungkan hasil crawling...")
        
        all_urls = set()
        
        # Ambil dari output katana
        if os.path.exists(katana_output):
            with open(katana_output, "r") as f:
                for line in f:
                    if "http" in line:
                        all_urls.add(line.strip())
        
        # Ambil dari output gau
        if os.path.exists(gau_output):
            with open(gau_output, "r") as f:
                for line in f:
                    url = line.strip()
                    if "http" in url and ("?" in url or url.endswith(".js")):
                        all_urls.add(url)
        
        print("[🧹] Menyimpan hasil gabungan yang sudah difilter (tanpa duplikat)...")
        with open(crawled_filtered_output, "w") as f:
            for url in sorted(all_urls):
                f.write(url + "\n")        
       
        print("[🌐] Mengecek url yang aktif...")
        if not jalankan_tool(["httpx", "-l", crawled_filtered_output, "-mc", "200", "-t", "100", "-o", temp_crawled_filtered_output], "httpx", target):
            return
        
        shutil.move(temp_crawled_filtered_output, crawled_filtered_output)
       

       
       
        print(f"[✅] Hasil akhir disimpan di {crawled_filtered_output}")
        
        print("[🚨] Menjalankan Nuclei scan (Crawled result)...")
        if not jalankan_tool([ "nuclei", "-l", crawled_filtered_output, "-dast", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", nuclei_output_crawled ], "nuclei (Katana)", target):
          return
        kirim_laporan_telegram(nuclei_output_crawled, f"{target} (WITH PARAMETER)")
        print(f"[✅] Scanning selesai untuk: {target}\n")
    

    elif scan_type == "3":
        scan_args = tanya_kecepatan_scan()
        print(f"\n[▶] Memulai proses untuk {target}")
        print(f"\n[🔎] Mencari subdomain (Subfinder, Assetfinder) untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return
        gabungkan_subdomain(subdomain_file, target)
     
        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-mc", "200", "-t", "100", "-o", active_file], "httpx", target):
            return
          
        print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
        if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-s", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot,xss", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", nuclei_output_httpx ], "nuclei (HTTPX)", target):
          return
        kirim_laporan_telegram(nuclei_output_httpx, f"{target} (WITHOUT PARAMETER)")
       
        print("[🕷️] Menjalankan crawling dengan Katana...")
        if not jalankan_tool(["katana", "-list", active_file, "-jc" , "-d", "3", "-fs", "fqdn", "-f", "qurl", "-o", katana_output], "katana", target):
            return
        
        print("[🕷️] Menjalankan crawling dengan gau...")
        
        # Jalankan gau
        try:
            with open(gau_output, "w") as outfile:
                subprocess.run([
                    "gau", target,
                    "--subs",
                    "--threads", "20",
                    "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico,txt,json",
                    "--verbose"
                ], stdout=outfile)
        except Exception as e:
            print(f"[⚠️] Gagal menjalankan gau: {e}")
            return
        
        print("[📦] Menggabungkan hasil crawling...")
        
        all_urls = set()
        
        # Ambil dari output katana
        if os.path.exists(katana_output):
            with open(katana_output, "r") as f:
                for line in f:
                    if "http" in line:
                        all_urls.add(line.strip())
        
        # Ambil dari output gau
        if os.path.exists(gau_output):
            with open(gau_output, "r") as f:
                for line in f:
                    url = line.strip()
                    if "http" in url and ("?" in url or url.endswith(".js")):
                        all_urls.add(url)
        
        print("[🧹] Menyimpan hasil gabungan yang sudah difilter (tanpa duplikat)...")
        with open(crawled_filtered_output, "w") as f:
            for url in sorted(all_urls):
                f.write(url + "\n")        
               
        print("[🌐] Mengecek url yang aktif...")
        if not jalankan_tool(["httpx", "-l", crawled_filtered_output, "-mc", "200", "-t", "100", "-o", temp_crawled_filtered_output], "httpx", target):
            return        
        shutil.move(temp_crawled_filtered_output, crawled_filtered_output)
        
       
        print(f"[✅] Hasil akhir disimpan di {crawled_filtered_output}")    
    
        print("[🚨] Menjalankan Nuclei scan (Crawled result)...")
        if not jalankan_tool([ "nuclei", "-l", crawled_filtered_output, "-dast", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", nuclei_output_crawled ], "nuclei (Katana)", target):
          return
        kirim_laporan_telegram(nuclei_output_crawled, f"{target} (WITH PARAMETER)")
        print(f"[✅] Scanning selesai untuk: {target}\n")
    
    elif scan_type == "4":
      output_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sensitivedata_{target}.txt")
      google_dork_search(target, output_file)
    elif scan_type == "5":
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
            lines = [f"[❌] Tidak ada kerentanan ditemukan untuk {domain}.\n"]
        header = f"[Laporan untuk {domain}]\n\n"
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
        
def fitur_update_tool():

    FILELIST_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/file_list.txt"
    VERSION_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/version.txt"
    TEMP_FOLDER = "temp_update"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(VERSION_API_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            remote_version = base64.b64decode(r.json()['content']).decode().strip()
        else:
            print("[❌] Gagal cek versi (status {})".format(r.status_code))
            return
    except Exception as e:
        print("[❌] Error saat cek versi:", e)
        return
    

    

    try:
        print("[⚙️] Mengecek versi terbaru dari GitHub...")
        

        if remote_version == LOCAL_VERSION:
            print(f"[✅] Tool sudah versi terbaru: v{LOCAL_VERSION}")
            return

        print(f"[⬆️] Tersedia versi baru: v{remote_version}")
        # Ambil daftar file yang akan diupdate dari file_list.txt (via GitHub API)
        r = requests.get(FILELIST_API_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            file_list_content = base64.b64decode(r.json()['content']).decode().strip()
            file_list = file_list_content.splitlines()
        else:
            print(f"[❌] Gagal mengambil file_list.txt (status {r.status_code})")
            return

        # Buat folder sementara
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        # Download tiap file ke folder sementara
        for file in file_list:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{file}"
            print(f"[↓] Mengunduh: {file}")
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                save_path = os.path.join(TEMP_FOLDER, file)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(r.text)
            else:
                print(f"[⚠️] Gagal mengunduh {file} (status {r.status_code})")

        # Overwrite file lama dengan versi baru
        for file in file_list:
            source = os.path.join(TEMP_FOLDER, file)
            destination = file
            if os.path.exists(source):
                shutil.copy(source, destination)
                print(f"[✔] Diperbarui: {file}")

        shutil.rmtree(TEMP_FOLDER)
        print(f"[✅] Update berhasil ke versi v{remote_version}")
        print("[🔁] Merestart tool...")
        time.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)

    except Exception as e:
        print(f"[❌] Gagal melakukan update: {e}")
        
        
        
        

if __name__ == "__main__":
    print_logo()
    while True:
        scan_type = tampilkan_menu()
        if scan_type == "99":
            print("[✔] Keluar dari program. Terima kasih!")
            break
        if scan_type in ["1", "2", "3", "4"]:
            target = get_target_input()
            process_domain(target, scan_type)
        elif scan_type == "5":
            process_domain(None, "5")
        elif scan_type == "6":
            print("\n=== Mode Takeover ===")
            print("1. Massal (from file)")
            print("2. Wildcard (find subdomain otomatis)")
            sub_mode = input("Choose Mode (1/2): ").strip()
            if sub_mode == "1":
                cek_takeover_massal()
            elif sub_mode == "2":
                cek_takeover_wildcard()
            else:
                print("[❌] Pilihan tidak valid.")
        elif scan_type == "0":
            fitur_info()
        elif scan_type == "7":
            buat_laporan_kerentanan()
        elif scan_type == "8":
            buat_laporan_dan_kirim_email() 
        elif scan_type == "999":
            fitur_update_tool()
