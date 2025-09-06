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
import datetime
import threading
import select
import termios
import tty
import signal
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs, unquote
import config
import re
import importlib

from env import GITHUB_TOKEN, GITHUB_USER, GITHUB_REPO, OPENROUTER_API_KEY
def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)
def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()
OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
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
LOCAL_VERSION = "1.2.1.1"
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
    print("Author     : PHIMS                Status      : \033[95m$\033[93m PREMIUM \033[95m$\033[0m")
    print("Instagram  : @aier_phims          GitHub      : phims403")
    print("Youtube    : elphims              Telegram    : @phimssec")
def tampilkan_menu():
    print("\n    Choose Feature:")
    print("  [0]  Feature Information")
    print("  [1]  Light Scan")
    print("  [2]  Dark Scan")
    print("  [3]  Deep Scan (\033[91mTOP FEATURE\033[0m)")
    print("  [4]  Scan Subdomain Takeover")
    print("  [5]  find Sensitive Data")
    print("  [6]  Manual Dorking")
    print("  [7]  Generate Report -> Send To Telegram")
    print("  [8]  Generate Report -> Send To Email Target (\033[91mTOP FEATURE\033[0m)")
    print("  [9]  Setup Configuration")
    print("  [99] Out ")
    print("  [999] Update Tool")
    print("──────────────────────────────────────────────────────────────────────────────")
    while True:
        pilihan = input("Choose Feature (0-9, 99, or 999): ").strip()
        if pilihan in ["0","1","2","3","4","5","6","7","8","9","99","999"]:
            return pilihan

        print("[❌] Pilihan tidak valid. Masukkan angka 0-9, 99, atau 999")

def setup_menu():
    while True:
        print("\n=== Setup Menu ===")
        print("1. Setup Nama Pelapor")
        print("2. Setup Email")
        print("3. Setup Password Gmail")
        print("4. Setup Bot Token")
        print("5. Setup Chat ID")
        print("6. Setup Scanning Speed")
        print("7. Setup Katana Limit")
        print("8. Setup Semua")
        print("9. Kembali ke menu utama")
        pilih = input("Pilih (1-9): ").strip()
        if pilih == "1":
            cur = getattr(config, "NAMA_PELAPOR", "")
            val = input(f"Nama Pelapor (sekarang: '{cur}'), enter=skip: ").strip()
            if val:
                write_config({"NAMA_PELAPOR": val})
        elif pilih == "2":
            cur = getattr(config, "EMAIL_PENGIRIM", "")
            val = input(f"Email Pengirim (sekarang: '{cur}'), enter=skip: ").strip()
            if val:
                write_config({"EMAIL_PENGIRIM": val})
        elif pilih == "3":
            val = input("Password Gmail (enter=skip): ").strip()
            if val:
                write_config({"EMAIL_PASSWORD": val})
        elif pilih == "4":
            cur = getattr(config, "BOT_TOKEN", "")
            val = input(f"Bot Token (sekarang: '{cur[:6]}...'), enter=skip: ").strip()
            if val:
                write_config({"BOT_TOKEN": val})
        elif pilih == "5":
            cur = getattr(config, "CHAT_ID", "")
            val = input(f"Chat ID (sekarang: '{cur}'), enter=skip: ").strip()
            if val:
                write_config({"CHAT_ID": val})
        elif pilih == "6":
            cur = getattr(config, "SCAN_SPEED", "")
            while True:
                val = input(f"Scan Speed (low/standard/fast) (sekarang: '{cur}'): ").strip().lower()
                if val in ["low", "standard", "fast"]:
                    write_config({"SCAN_SPEED": val})
                    break  # keluar dari loop kalau valid
                else:
                    print("[!] Nilai tidak valid; gunakan low/standard/fast.")

        elif pilih == "7":
            new_limit = input(f"Masukkan limit subdomain untuk Katana (default {getattr(config, 'KATANA_LIMIT', 20)}): ").strip()
            if new_limit.isdigit() and int(new_limit) > 0:
                write_config({"KATANA_LIMIT": int(new_limit)})
                print(f"[✓] Katana limit diubah menjadi {new_limit}")
            else:
                print("[ℹ️] Input kosong atau tidak valid, tidak ada perubahan.")



        elif pilih == "8":
            updates = {}
            v = input(f"Nama Pelapor (sekarang: '{getattr(config,'NAMA_PELAPOR','')}'), enter=skip: ").strip()
            if v: updates["NAMA_PELAPOR"] = v
            v = input(f"Email Pengirim (sekarang: '{getattr(config,'EMAIL_PENGIRIM','')}'), enter=skip: ").strip()
            if v: updates["EMAIL_PENGIRIM"] = v
            v = input("Password Gmail (enter=skip): ").strip()
            if v: updates["EMAIL_PASSWORD"] = v
            v = input(f"Bot Token (sekarang: '{getattr(config,'BOT_TOKEN','')[:6]}...'), enter=skip: ").strip()
            if v: updates["BOT_TOKEN"] = v
            v = input(f"Chat ID (sekarang: '{getattr(config,'CHAT_ID','')}'), enter=skip: ").strip()
            if v: updates["CHAT_ID"] = v
            v = input(f"Scan Speed (low/standard/fast) (sekarang: '{getattr(config,'SCAN_SPEED','')}'), enter=skip: ").strip().lower()
            if v in ["low","standard","fast"]: updates["SCAN_SPEED"] = v
            limit_val = input(f"Masukkan Katana Limit (default {config.KATANA_LIMIT}, Enter skip): ").strip()
            if limit_val.isdigit() and int(limit_val) > 0:
                updates["KATANA_LIMIT"] = int(limit_val)
            
            if updates:
                write_config(updates)
            else:
                print("[ℹ️] Tidak ada perubahan.")
        elif pilih == "9":
            return
        else:
            print("[❌] Pilihan tidak valid.")


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

2. Dark Scan (Recon Menengah)
   - Subfinder + Assetfinder → mencari sebanyak mungkin subdomain dari target.
   - Gabungkan dan hilangkan duplikat hasil.
   - Httpx → validasi subdomain aktif.
   - Katana → crawling URL untuk mencari parameter dari subdomain aktif.
   - Grep → filter URL yang memiliki parameter (?key=value).
   - Nuclei tahap 1 → scan url berparameter untuk deteksi kerentanan seperti xss, sqli, lfi, dll.
   - Nuclei tahap 2 → scan url (.js) untuk deteksi exposure
   - Kecepatan scan dapat disesuaikan (low/standard/fast).
   - Semua hasil dikirim otomatis ke Telegram.
   
3. Deep Scan (Recon Mendalam)
   - Sama seperti Dark Scan dengan perbedaaan:
   - Nuclei tahap 1 → scan awal menggunakan template umum seperti:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, dll.
   - Nuclei tahap 2 → scan url berparameter untuk deteksi kerentanan seperti xss, sqli, lfi, dll.
   - Nuclei tahap 3 → scan url (.js) untuk deteksi exposure
   - Nuclei tahap 4 → scan subdomain untuk deteksi subdomain takeover

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
def buat_prompt_laporan(vuln, validasi):
    return f"""
Buatkan teks laporan kerentanan profesional dalam bahasa Indonesia dengan struktur sebagai berikut:

1. Judul Kerentanan
2. Deskripsi Kerentanan
3. Langkah-langkah Eksploitasi / Validasi
4. Dampak atau Impact dari Kerentanan
5. Rekomendasi Mitigasi / Perbaikan
6. Detail Pelapor (hanya Nama dan Email)

Data Input:
- Nama Pelapor: {config.NAMA_PELAPOR}
- Email Pelapor: {config.EMAIL_PENGIRIM}
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
def buat_laporan_dan_kirim_email():
    print("\n=== Form Kirim Laporan via Email ===")
    vuln = input("Judul / Jenis Kerentanan yang ditemukan  : ").strip()
    validasi = input("Langkah Validasi (PoC)    : ").strip()
    email_tujuan = input("Email tujuan              : ").strip() 
    nama_file = vuln.lower().replace(" ", "_")
    prompt = buat_prompt_laporan(vuln, validasi)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek/deepseek-chat:free",
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
    prompt = buat_prompt_laporan(vuln, validasi)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek/deepseek-chat:free",
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
    else:
        print("[❌] Gagal memproses dengan OpenRouter API.")
        print("Kode:", response.status_code)
        print(response.text)
def takeover():
    while True:
        print("\n=== Mode Takeover ===")
        print("1. Massal (from file)")
        print("2. Wildcard (find subdomain automatic)")
        print("3. Kembali ke menu utama")
        sub_mode = input("Pilih Mode (1/2/3): ").strip()
        if sub_mode in ("1", "2"):
            cek_takeover(sub_mode)
        elif sub_mode == "3":
            return
        else:
            print("[❌] Pilihan tidak valid.")
def cek_takeover(mode):
    if mode == "1":
        nama_file = input("Masukkan nama file yang berisi daftar domain/subdomain (contoh: subdomain.txt): ").strip()
        if not os.path.isfile(nama_file):
            print("[❌] File tidak ditemukan.")
            return
        output_nama = input("Masukkan nama output file (tanpa .txt): ").strip()
        if not output_nama:
            print("[❌] Nama file output tidak boleh kosong.")
            return
        input_file = nama_file
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_nama}.txt")
        label = f"Takeover Massal ({output_nama})"
    else:
        target = get_target_input()
        input_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
        finding_subdomain(target, input_file)
        label = f"Takeover Wildcard ({target})"
    print(f"\033[94m[+] Menjalankan nuclei takeover scan untuk: {input_file}\033[0m")
    try:
        subprocess.run([
            "nuclei", "-l", input_file, "-nh", "-t", "takeovers", "-o", output_path
        ], check=True)
        kirim_laporan_telegram(output_path, label)
        print(f"[✅] Scan selesai. Hasil di: {output_path}")
    except subprocess.CalledProcessError:
        print(f"[❌] Gagal menjalankan nuclei takeover scan untuk: {input_file}")
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Mozilla/5.0 (X11; Linux x86_64)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
    'Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X)',
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

# ----------------- Speed mapping untuk semua tools -----------------
SPEED_ARGS = {
    "low": {
        "nuclei": ["-c", "10", "--max-host-error", "20"],
        "httpx": ["-silent", "-mc", "200", "-t", "50", "-rate-limit", "100", "-retries", "1", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-sc", "-t", "50", "-rate-limit", "100", "-retries", "1", "-timeout", "10"],
        "katana": ["-jc", "5", "-d", "2"],
        "gau": ["--subs", "--threads", "5", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    },
    "standard": {
        "nuclei": ["-c", "25", "--max-host-error", "30"],
        "httpx": ["-silent", "-mc", "200", "-t", "200", "-rate-limit", "500", "-retries", "2", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-sc", "-t", "200", "-rate-limit", "500", "-retries", "2", "-timeout", "10"],
        "katana": ["-jc", "15", "-d", "4"],
        "gau": ["--subs", "--threads", "20", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    },
    "fast": {
        "nuclei": ["-c", "40", "--max-host-error", "50"],
        "httpx": ["-silent", "-mc", "200", "-t", "300", "-rate-limit", "1200", "-retries", "4", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-sc", "-t", "300", "-rate-limit", "1200", "-retries", "4", "-timeout", "10"],
        "katana": ["-jc", "30", "-d", "6"],
        "gau": ["--subs", "--threads", "40", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    }
}

def write_config(updates: dict):
    """
    updates: dict, contohnya {"config.SCAN_SPEED": "fast", "config.EMAIL_PENGIRIM": "a@b.com"}
    Fungsi ini mengubah/menambah nilai di config.py lalu me-reload modul config.
    """
    cfg_path = os.path.join(os.path.dirname(__file__), "config.py")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    for key, val in updates.items():
        if isinstance(val, str):
            replacement = f'{key} = "{val}"'
        else:
            replacement = f'{key} = {val}'
        pattern = rf'^{key}\s*=.*$'
        if re.search(pattern, content, flags=re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            content += "\n" + replacement + "\n"

    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(content)

    # reload module so runtime menggunakan config terkini
    importlib.reload(config)
    print("[✓] config.py diperbarui dan dimuat ulang.")

def get_speed():
    s = getattr(config, "SCAN_SPEED", None)
    if not s:
        return None
    s = s.lower()
    return s if s in SPEED_ARGS else None

def get_tool_args(tool_name: str):
    """
    tool_name: "nuclei" | "httpx" | "httpx_sensitive" | "katana" | "gau"
    -> mengembalikan list args sesuai config.SCAN_SPEED jika ada, else None
    """
    s = get_speed()
    if not s:
        return None
    return SPEED_ARGS[s].get(tool_name)
# --------------------------------------------------------------------


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
def google_dork_search(target, output_file):
    print(f"\033[94m[+] Memulai pencarian dorking untuk: {target}\033[0m")
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
def find_sensitive_data():
      target = get_target_input()
      output_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sensitivedata_{target}.txt")
      google_dork_search(target, output_file)
def dorking_manual():
      nama_file = input("Masukkan nama file untuk menyimpan hasil (contoh: hasil_dork.txt): ").strip()
      if not nama_file:
          print("[❌] Nama file tidak boleh kosong.")
      else:
          output_file = os.path.join(OUTPUT_FOLDER_DORKING, nama_file)
          manual_dorking(output_file)
def tanya_kecepatan_scan():
    # cek config
    speed = get_speed()
    if speed:
        print(f"[ℹ️] SCAN_SPEED sudah diset di config → gunakan '{speed}'")
        return SPEED_ARGS[speed]["nuclei"]

    # kalau belum ada (kosong / None), baru tanya user
    pilihan = input("\nSelect Scanning Speed: 1.Low, 2.Standard, 3.Fast: ").strip()
    if pilihan == "1":
        return SPEED_ARGS["low"]["nuclei"]
    elif pilihan == "2":
        return SPEED_ARGS["standard"]["nuclei"]
    elif pilihan == "3":
        return SPEED_ARGS["fast"]["nuclei"]
    else:
        print("[❌] Pilihan tidak valid. Default ke Standard.")
        return SPEED_ARGS["standard"]["nuclei"]

def log_error(target, proses, error_message, error_log_file="error.log"):
    # Buat file error jika belum ada
    if not os.path.exists(error_log_file):
        with open(error_log_file, "w", encoding="utf-8") as f:
            f.write("=== Log Error Tool ===\n\n")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_text = (
        f"[{now}]\n"
        f"Target     : {target}\n"
        f"Proses     : {proses}\n"
        f"Error      : {error_message}\n"
        f"{'-'*50}\n"
    )

    with open(error_log_file, "a", encoding="utf-8") as f:
        f.write(log_text)

    print("\n[!] Terjadi error:\n")
    print(error_message)

def baca_file_real_time(nama_tool, path_file, label, process):
    stop_evt = threading.Event()

    jumlah = 0
    try:
        # tunggu file muncul
        while not os.path.exists(path_file):
            time.sleep(0.1)


        with open(path_file, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                line = f.readline()
                if not line:
                    if process and process.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue

                jumlah += 1
                msg = f"[+] Menjalankan {nama_tool} ditemukan \033[93m{jumlah}\033[94m {label}..."
                # hapus \n biar gak bikin baris baru
                sys.stdout.write("\r" + msg + " " * 20)  
                sys.stdout.flush()

        if not stop_evt.is_set():
            print(f"\r\033[33m[✓]\033[94m {nama_tool} berhasil menemukan \033[93m{jumlah}\033[94m {label}\033[0m".ljust(100))

    except Exception as e:
        print(f"[!] Gagal membaca file {path_file}: {e}")


        
def finding_subdomain(target, subdomain_file):
    print(f"\n\033[94m[+] Mencari subdomain dengan Subfinder dan Assetfinder untuk: {target}\033[0m")
    print("\033[94m[+] Menjalankan Subfinder...\033[0m")
    try:
        with open(subdomain_file, "w") as f:
            process_subfinder = subprocess.Popen(
                ["subfinder", "-silent", "-all", "-d", target],
                stdout=f,
                stderr=subprocess.DEVNULL
            )
            process_subfinder.wait()
        if process_subfinder.returncode != 0:
            print(f"[!] Gagal menjalankan Subfinder untuk target {target}")
            return
    
    
    except Exception as e:
        print(f"[!] Error saat menjalankan Subfinder: {e}")
        log_error(target, "subfinder", str(e))
        return    
    
    
    print("\033[94m[+] Menjalankan Assetfinder...\033[0m")
    assetfinder_tmp = tempfile.NamedTemporaryFile(delete=False).name
    try:
        with open(assetfinder_tmp, "w") as f:
            process_assetfinder = subprocess.Popen(
                ["assetfinder", "--subs-only", target],
                stdout=f,
                stderr=subprocess.DEVNULL
            )
            process_assetfinder.wait()
        if process_assetfinder.returncode != 0:
            print(f"[!] Gagal menjalankan Assetfinder untuk target {target}")
            return
    except Exception as e:
        print(f"[!] Error saat menjalankan Assetfinder: {e}")
        log_error(target, "assetfinder", str(e))
        return      
  
    all_subs = set()
    for path in [subdomain_file, assetfinder_tmp]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            all_subs.update(line.strip() for line in f if line.strip())
    with open(subdomain_file, "w") as f:
        f.write("\n".join(sorted(all_subs)))
    print(f"\033[33m[✓]\033[94m Ditemukan total \033[92m{len(all_subs)}\033[94m Subdomain\033[0m")

        
def active_check(active_file, subdomain_file, url, target):
    print(f"\033[94m[+] Mengecek {url} yang aktif...\033[0m")
    try:
        httpx_args = get_tool_args("httpx") or ["-silent", "-mc", "200", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
        with open(active_file, "w") as f:
            cmd = ["httpx", *httpx_args, "-l", subdomain_file]
            process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.DEVNULL)
            baca_file_real_time("Httpx", active_file, url, process)

        if process.returncode != 0:
            print(f"[!] Gagal menjalankan httpx")
            return

    except Exception as e:
        print(e)
        log_error(target, "httpx", str(e))
        return

    with open(active_file) as f:
        aktif = len(f.readlines())

        
        
        

def crawling_katana(katana_output, input_file, target):
    print("\033[94m[+] Memulai proses crawling dengan Katana...\033[0m")
    try:
        with open(katana_output, "w") as f:
            katana_args = get_tool_args("katana") or ["-jc", "15", "-d", "4"]
            cmd = ["katana", "-list", input_file, *katana_args, "-f", "qurl", "-fs", "fqdn"]
            process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.DEVNULL)
        baca_file_real_time("Katana", katana_output, "url", process)

        if process.returncode != 0:
            print(f"[!] Gagal menjalankan katana")
            return
    except Exception as e:
        print(e)
        log_error(target, "katana", str(e))
    katana_urls = []
    if os.path.exists(katana_output):
        with open(katana_output, "r") as f:
            katana_urls = [line.strip() for line in f if "http" in line]


def crawling_wayback(wayback_output, active_file, target):
    print("\033[94m[+] Memulai proses crawling dengan Waybackurls...\033[0m")
    try:
        with open(wayback_output, "w") as f:
            process = subprocess.Popen(
                ["waybackurls"],
                stdin=open(active_file, "r"),
                stdout=f,
                stderr=subprocess.DEVNULL
            )
        baca_file_real_time("wayback", wayback_output, "url", process)
        if process.returncode != 0:
            print(f"[!] Gagal menjalankan waybackurls")
            return
    except Exception as e:
        print(e)
        log_error(target, "wayback", str(e))
    wayback_urls = []
    if os.path.exists(wayback_output):
        with open(wayback_output, "r") as f:
            wayback_urls = [line.strip() for line in f if "http" in line]




def crawling_gau(gau_output, target):
    print("\033[94m[+] Memulai proses crawling dengan Gau...\033[0m")
    try:
        gau_args = get_tool_args("gau") or ["--subs", "--threads", "20", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
        with open(gau_output, "w") as outfile:
            cmd = ["gau", target, *gau_args]
            process = subprocess.Popen(cmd, stdout=outfile, stderr=subprocess.DEVNULL)
        baca_file_real_time("Gau", gau_output, "url", process)
        if process.returncode != 0:
            print(f"[!] Gagal menjalankan gau")
            return
    except Exception as e:
        print(e)
        log_error(target, "gau", str(e))
    gau_urls = []
    if os.path.exists(gau_output):
        with open(gau_output, "r") as f:
            gau_urls = [line.strip() for line in f if "http" in line]




def gabungkan_hasil_crawling(wayback_output, gau_output, katana_output, crawled_filtered_output, target):
    katana_urls = []
    if os.path.exists(katana_output):
        with open(katana_output, "r") as f:
            katana_urls = [line.strip() for line in f if "http" in line]
    wayback_urls = []
    if os.path.exists(wayback_output):
        with open(wayback_output, "r") as f:
            wayback_urls = [line.strip() for line in f if "http" in line]
    gau_urls = []
    if os.path.exists(gau_output):
        with open(gau_output, "r") as f:
            gau_urls = [line.strip() for line in f if "http" in line]
    
    all_urls = set()
    sensitive_exts = [
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".bak", ".backup", ".old",
        ".sql", ".db", ".sqlite",
        ".env", ".log",
        ".conf", ".config", ".ini", ".cfg",
        ".xml"
    ]

    for url in wayback_urls + gau_urls + katana_urls:
        if "?" in url or url.endswith(".js") or any(url.endswith(ext) or ext in url for ext in sensitive_exts):
            all_urls.add(url)

   
    with open(crawled_filtered_output, "w") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

def pisahkan_url(crawled_filtered_output, param_output, js_output):
    param_urls = []
    js_urls = []
    with open(crawled_filtered_output, "r") as infile:
        for line in infile:
            url = line.strip()
            if "?" in url:
                param_urls.append(url)
            if url.endswith(".js"):
                js_urls.append(url)
    with open(param_output, "w") as f:
        for url in param_urls:
            f.write(url + "\n")
    with open(js_output, "w") as f:
        for url in js_urls:
            f.write(url + "\n")
    print(f"\033[94m[✓] Ditemukan \033[92m{len(param_urls)}\033[94m URL berparameter\033[0m")
    print(f"\033[94m[✓] Ditemukan \033[92m{len(js_urls)}\033[94m URL .js\033[0m")

def proses_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output):
    crawling_wayback(wayback_output, active_file, target)
    crawling_gau(gau_output, target)
    with open(active_file, "r") as f:
        alive_subs = [line.strip() for line in f if line.strip()]
    limit = getattr(config, "KATANA_LIMIT", 20)

    if len(alive_subs) >= limit:
        limited_file = os.path.join(os.path.dirname(active_file), f"{limit}active_{target}.txt")
        with open(limited_file, "w") as f:
            for sub in alive_subs[:limit]:  # ambil sesuai limit
                f.write(sub + "\n")
        print(f"\033[94m[+] Subdomain aktif ≥ {limit}, hanya menggunakan {limit} subdomain aktif\033[0m")
        input_for_katana = limited_file
    else:
        print(f"\033[94m[+] Subdomain aktif < {limit}, langsung gunakan seluruh file untuk scan Katana\033[0m")
        input_for_katana = active_file
    crawling_katana(katana_output, input_for_katana, target)
    gabungkan_hasil_crawling(wayback_output, gau_output, katana_output, crawled_filtered_output, target)


def kirim_file_telegram(path_file, domain):
    """Kirim file hasil scan ke Telegram (sendDocument)."""
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
        print("[ℹ️] Token bot atau chat_id tidak ditemukan / tidak valid. Melewati pengiriman Telegram.")
        return 
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument"
    if not os.path.exists(path_file) or os.stat(path_file).st_size == 0:
        # Jika file kosong → kirim teks saja
        pesan = f"[❌] Tidak ada path sensitive yang terdeteksi untuk {domain}"
        requests.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
            data={'chat_id': config.CHAT_ID, 'text': pesan}
        )
        print(f"[ℹ️] Tidak ada path sensitive untuk {domain}")
        return
    try:
        with open(path_file, "rb") as f:
            response = requests.post(url, data={'chat_id': config.CHAT_ID}, files={'document': f})
        if response.status_code == 200:
            print(f"[✓] File hasil sensitive path {domain} berhasil dikirim ke Telegram.")
        else:
            print(f"[❌] Gagal mengirim file ke Telegram: {response.text}")
    except Exception as e:
        print(f"[⚠️] Error saat mengirim file ke Telegram: {e}")
def cek_url_sensitif(target, crawled_filtered_output):
    print("\033[94m[+] Mengecek URL yang berpotensi sensitif...\033[0m")
    pot_sen_file = os.path.join("sensitive_data", f"pot_sen_url_{target}.txt")
    sen_file = os.path.join("sensitive_data", f"sen_url_{target}.txt")
    sensitive_exts = [
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".bak", ".backup", ".old",
        ".sql", ".db", ".sqlite",
        ".env", ".log",
        ".conf", ".config", ".ini", ".cfg",
        ".xml", ".json"
    ]

    try:
        urls = []
        if os.path.exists(crawled_filtered_output):
            with open(crawled_filtered_output, "r") as f:
                for line in f:
                    url = line.strip()
                    if any(url.endswith(ext) or ext in url for ext in sensitive_exts):
                        urls.append(url)

        if not urls:
            print(f"[ℹ️] Tidak ada URL sensitif ditemukan untuk {target}")
            return

        with open(pot_sen_file, "w") as f:
            for url in urls:
                f.write(url + "\n")

        print(f"[✓] Ditemukan {len(urls)} URL berpotensi sensitif → {pot_sen_file}")

        # httpx dibuat silent + dipantau real-time
        with open(sen_file, "w") as f:
            httpx_args = get_tool_args("httpx_sensitive") or ["-silent", "-mc", "200,403", "-sc", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
            process = subprocess.Popen(
                ["httpx", *httpx_args, "-l", pot_sen_file],
                stdout=f,
                stderr=subprocess.DEVNULL
            )
        baca_file_real_time("Httpx (Sensitive URL)", sen_file, "url sensitif", process)


        if process.returncode != 0:
            print(f"[!] Gagal menjalankan httpx untuk validasi URL sensitif")
            return

        print(f"[✓] Hasil valid URL sensitif tersimpan → {sen_file}")
        kirim_file_telegram(sen_file, target)

    except Exception as e:
        print(f"[!] Error saat cek URL sensitif: {e}")
        log_error(target, "cek url sensitif", str(e))


def nuclei_without_parameter(target, input_file, output_file, user_agent, scan_args):
    print("\033[94m[+] Menjalankan Nuclei untuk Subdomain yang aktif (Without Parameter)...\033[0m")
    try:
        subprocess.run([
            "nuclei", "-l", input_file, "-s", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot,xss", "-ept", "ssl", "-H", f"User-Agent: {user_agent}", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
        ], check=True)
    

    except subprocess.CalledProcessError as e:
        print("[!] Gagal menjalankan Nuclei (HTTPX)")
        print(e)  # ini akan menampilkan error detail ke terminal
        log_error(target, "nuclei (httpx)", str(e))
        return      
      
      
    kirim_laporan_telegram(output_file, f"{target} (WITHOUT PARAMETER)")
def nuclei_js_exposure(target, input_file, output_file, user_agent, scan_args):
    print("\033[94m[+] Menjalankan Nuclei untuk URL .js (tag: exposure)...\033[0m")
    try:
        subprocess.run([
            "nuclei", "-l", input_file, "-tags", "exposure", "-timeout", "5", "-retries", "1", "-H", f"User-Agent: {user_agent}", *scan_args, "-o", output_file
        ], check=True)
    except subprocess.CalledProcessError as e:
            print("[!] Gagal menjalankan Nuclei (JS Exposure)")
            print(e)  # ini akan menampilkan error detail ke terminal
            log_error(target, "nuclei (JS Exposure)", str(e))
            return            
      
      
    kirim_laporan_telegram(output_file, f"{target} (JS Exposure)")
def nuclei_param_dast(target, input_file, output_file, user_agent, scan_args):
    print("\033[94m[+] Menjalankan Nuclei untuk URL berparameter (-dast)...\033[0m")
    try:
        subprocess.run([
            "nuclei", "-l", input_file, "-dast", "-tags", "xss,sqli,ssrf,rce,lfi,rfi,redirect,crlf,idor,ssti,csrf,file-upload,path-traversal,debug,exposure,auth-bypass,fuzz,generic,web,token-leakage", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", "-H", f"User-Agent: {user_agent}", *scan_args, "-o", output_file
        ], check=True)
    except subprocess.CalledProcessError as e:
            print("[!] Gagal menjalankan Nuclei (Parameter (-dast))")
            print(e)  # ini akan menampilkan error detail ke terminal
            log_error(target, "nuclei (Parameter (-dast))", str(e))
            return            
      
    kirim_laporan_telegram(output_file, f"{target} (Parameter (-dast))")


def light_scan():
        target = get_target_input()
        scan_args = tanya_kecepatan_scan()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        print(f"\n[▶] Memulai proses untuk {target}")
        waktu_mulai_url = time.time()
        finding_subdomain(target, subdomain_file)
        active_check(active_file, subdomain_file, "Subdomain", target)
        waktu_mulai_scan_nuclei = time.time()
        nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
        waktu_selesai_scan_nuclei = time.time()
        durasi_scan = waktu_selesai_scan_nuclei - waktu_mulai_scan_nuclei
        jam, sisa = divmod(int(durasi_scan), 3600)
        menit, detik = divmod(sisa, 60)
        print(f"[⏱️] Proses scanning Nuclei selesai dalam {jam} jam {menit} menit {detik} detik")
        print(f"[✓] Semua proses selesai untuk target: {target}")
        
def dark_deep(mode):
        target = get_target_input()
        scan_args = tanya_kecepatan_scan()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        katana_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"katana_{target}.txt")
        wayback_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"wayback_{target}.txt")
        gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"_gau{target}.txt")
        nuclei_output_crawled = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_{target}_crawled.txt")
        crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
        temp_crawled_filtered_output = os.path.join (OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        param_output = os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt")
        js_output = os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt")
        nuclei_output_js = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt")
        nuclei_output_param = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt")
        print(f"\n[▶] Memulai proses untuk {target}")
        waktu_mulai_url = time.time()
        finding_subdomain(target, subdomain_file)
        active_check(active_file, subdomain_file, "Subdomain", target)
        proses_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)
        active_check(temp_crawled_filtered_output, crawled_filtered_output, "URL", target)
        shutil.move(temp_crawled_filtered_output, crawled_filtered_output)
        pisahkan_url(crawled_filtered_output, param_output, js_output)
        waktu_selesai_url = time.time()
        durasi_url = waktu_selesai_url - waktu_mulai_url
        jam, sisa = divmod(int(durasi_url), 3600)
        menit, detik = divmod(sisa, 60)
        print(f"\033[92m[⏱️] Berhasil mengumpulkan URL dari {target} selama "
            f"\033[93m{jam}\033[92m jam "
            f"\033[93m{menit}\033[92m menit "
            f"\033[93m{detik}\033[92m detik\033[0m")        
        waktu_mulai_scan_nuclei = time.time()
        if mode == "dark":
            nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
        elif mode == "deep":
            nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
            nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
            output_path_takeover = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
            print(f"[🚨] Menjalankan nuclei takeover scan untuk: {target}")
            try:
                subprocess.run([
                    "nuclei", "-l", subdomain_file, "-nh", "-t", "takeovers", "-o", output_path_takeover
                ], check=True)
                kirim_laporan_telegram(output_path_takeover, f"Takeover Wildcard ({target})")
                print(f"[✓] Scan selesai. Hasil di: {output_path_takeover}")
            except subprocess.CalledProcessError:
                print(f"[❌] Gagal menjalankan nuclei takeover scan untuk {target}")
        else:
            print(f"[!] Mode scan tidak dikenal: {mode}")
            return
        waktu_selesai_scan_nuclei = time.time()
        durasi_scan = waktu_selesai_scan_nuclei - waktu_mulai_scan_nuclei
        jam, sisa = divmod(int(durasi_scan), 3600)
        menit, detik = divmod(sisa, 60)
        print(f"[⏱️] Proses scanning Nuclei selesai dalam {jam} jam {menit} menit {detik} detik")
        print(f"[✓] Semua proses selesai untuk target: {target}")
def kirim_laporan_telegram(path_file, domain, max_len=4000):
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
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
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
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
                'chat_id': config.CHAT_ID,
                'text': pesan
            })
            if response.status_code == 200:
                print(f"[✓] Bagian {i+1} laporan {domain} berhasil dikirim.")
            else:
                print(f"[❌] Gagal kirim bagian {i+1} laporan {domain}: {response.text}")
                break
    except Exception as e:
        print(f"[⚠️] Terjadi kesalahan saat mengirim ke Telegram: {e}")
def kirim_laporan_telegram_teks_report(path_file):
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
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
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            'chat_id': config.CHAT_ID,
            'text': f"[Text Report]\n\n{isi}"
        })
        if response.status_code == 200:
            print(f"[✓]  Teks laporan berhasil dikirim ke Telegram.")
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
            print(f"[✓] Tool sudah versi terbaru: v{LOCAL_VERSION}")
            return
        print(f"[⬆️] Tersedia versi baru: v{remote_version}")
        r = requests.get(FILELIST_API_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            file_list_content = base64.b64decode(r.json()['content']).decode().strip()
            file_list = file_list_content.splitlines()
        else:
            print(f"[❌] Gagal mengambil file_list.txt (status {r.status_code})")
            return
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)
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
        for file in file_list:
            source = os.path.join(TEMP_FOLDER, file)
            destination = file
            if os.path.exists(source):
                shutil.copy(source, destination)
                print(f"[✔] Diperbarui: {file}")
        shutil.rmtree(TEMP_FOLDER)
        print(f"[✓] Update berhasil ke versi v{remote_version}")
        print("[🔁] Merestart tool...")
        time.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"[❌] Gagal melakukan update: {e}")
if __name__ == "__main__":
    print_logo()
    while True:
        scan_type = tampilkan_menu()
        if scan_type == "1":
            light_scan()
        elif scan_type == "2":
            dark_deep("dark")
        elif scan_type == "3":
            dark_deep("deep")
        elif scan_type == "4":
            takeover()
        elif scan_type == "5":
            find_sensitive_data()
        elif scan_type == "6":
            dorking_manual()
        elif scan_type == "7":
            buat_laporan_kerentanan()
        elif scan_type == "8":
            buat_laporan_dan_kirim_email()
        elif scan_type == "9":
            setup_menu()

        elif scan_type == "0":
            fitur_info()
        elif scan_type == "99":
            print("[✔] Keluar dari LAZYHUNTER. Terima kasih!")
            break
        elif scan_type == "999": 
            fitur_update_tool()
        else:
            print("[!] Pilihan tidak valid. Coba lagi.")
