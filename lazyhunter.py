import os
import subprocess
import shutil
import requests
from config import BOT_TOKEN, CHAT_ID


def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)

def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()
# Diatas adalah fungsi untuk send notif ke tele
# Definisikan tools dan repository instalasinya sesuai dengan GitHub ProjectDiscovery
TOOLS = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx",
    "nuclei": "github.com/projectdiscovery/nuclei/v2/cmd/nuclei"
}
# Folder output
OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
OUTPUT_FOLDER_NUCLEI = "nuclei"
OUTPUT_FOLDER_DORKING = "dorking"
OUTPUT_FOLDER_TAKEOVER = "take_over"
os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_DORKING, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)

def check_go():
    """Memeriksa apakah Go terinstal sebelum menginstal tools."""
    if not shutil.which("go"):
        print("[❌] Go belum terinstal! Silakan instal Go terlebih dahulu.")
        exit(1)

def check_and_install_tools():
    """Memeriksa dan menginstal tools jika belum ada."""
    for tool, repo in TOOLS.items():
        if not shutil.which(tool):
            print(f"[⚠️] {tool} belum terinstall. Menginstall...")
            install_cmd = f"go install -v {repo}@latest"
            result = subprocess.run(install_cmd, shell=True)
            if result.returncode != 0:
                print(f"[❌] Gagal menginstall {tool}. Pastikan Go sudah terinstall dan PATH sudah diset.")
            else:
                print(f"[✅] {tool} berhasil diinstall.")
        else:
            print(f"[✅] {tool} sudah terinstall.")




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
║                    FREE VERSION                        ║
╠════════════════════════════════════════════════════════╣
║ Author     : PHIMS                                     ║
║ GitHub     : github.com/phims403                       ║
║ Instagram  : @aier_phims                               ║
║ Telegram   : @phimssec                                 ║
║ Donate     : Chat with me on Telegram!                 ║
╚════════════════════════════════════════════════════════╝
    """
    print(logo)


def tampilkan_menu():
    print("\n=== Pilih Jenis Scan ===")
    print("1. Light Scan")
    print("2. Deep Scan (Premium Version)")
    print("3. Find Sensitive Data (Premium Version)")
    print("4. Manual Dorking")
    print("5. Check Subdomain Takeover")
    print("Tambahkan akhiran 'i' dibelakang angka untuk informasi tentang fitur dari angka yang dipilih")
    
    while True:
        pilihan = input("Masukkan pilihan (contoh: 1, 2i, 3, 5i): ").strip().lower()
        
        if pilihan.endswith("i") and pilihan[:-1] in FITUR_INFO:
            print(f"\n[ℹ️] Info Fitur {pilihan[:-1]}: {FITUR_INFO[pilihan[:-1]]}\n")
        elif pilihan in ["1", "2", "3", "4", "5"]:
            return pilihan
        else:
            print("[❌] Pilihan tidak valid. Gunakan 1-5 atau 1i-5i untuk info.")
def get_target_input():
    """Meminta input URL target langsung dari pengguna."""
    while True:
        target = input("Masukkan URL target (contoh: example.com): ").strip()
        if target:
            return target
        print("[❌] URL tidak valid! Masukkan URL yang benar.")
        
FITUR_INFO = {
    "1": "Lightscan: scanning cepat yang menggunakan kombinasi subfinder, httpx, dan nuclei untuk menemukan subdomain aktif dan mengecek potensi celah keamanannya.",
    "2": "Deepscan: scanning mendalam yang menggabungkan Subfinder + Assetfinder untuk mencari subdomain sebanyak mungkin, kemudian disaring dengan httpx, dipindai dengan Nuclei, dan dipindai direktori serta endpoint menggunakan Katana dan Grep. Hasil akhirnya diperiksa ulang dengan Nuclei untuk deteksi celah lanjut.",
    "3": "Find Sensitive Data: mencari file atau path sensitif seperti .env, .git, .svn, backup file, credential, dan konfigurasi umum lainnya secara otomatis.",
    "4": "Manual Dorking: memungkinkan kamu untuk melakukan pencarian di mesin pencari menggunakan dork buatan sendiri, cocok untuk hunting informasi spesifik secara manual.",
    "5": "Subdomain Takeover: mengecek apakah subdomain yang ditemukan rentan untuk diambil alih (takeover) menggunakan tools seperti Nuclei dengan template takeover."
}
        
        
        
def cek_takeover_massal():
    nama_file = input("Masukkan nama file yang berisi daftar domain/subdomain (cth: subdomain.txt): ").strip()
    if not os.path.isfile(nama_file):
        print("[❌] File tidak ditemukan.")
        return

    output_nama = input("Masukkan nama output file (tanpa .txt): ").strip()
    if not output_nama:
        print("[❌] Nama file output tidak boleh kosong.")
        return

    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOM_{output_nama}.txt")
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
    domain = input("Masukkan domain (cth: example.com): ").strip()
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
        
        
        
  







# List User-Agent untuk rotasi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X)"
]


    
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
                print(f"[✅] {link}")
                hasil.append(link)
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

def process_domain(target, scan_type):
    """Melakukan scanning untuk satu domain."""
    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
    nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
    if scan_type == "1":
        # Light scan
        print(f"\n[🔎] Mencari subdomain dengan Subfinder untuk: {target}")
        if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
            return
        print("[🌐] Mengecek subdomain yang aktif...")
        if not jalankan_tool(["httpx", "-l", subdomain_file, "-o", active_file], "httpx", target):
            return
        print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
        if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-severity", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot", "-ept", "ssl",
        "-o", nuclei_output_httpx ], "nuclei (HTTPX)", target):
          return
        kirim_laporan_telegram(nuclei_output_httpx, f"{target} (HTTPX)")

    elif scan_type in "2":
      print("Premium Version! buy at https://lynk.id/aier/mloYxRr/")
    elif scan_type == "3":
      print("Premium Version! buy at https://lynk.id/aier/mloYxRr/")
    elif scan_type == "4":
      nama_file = input("Masukkan nama file untuk menyimpan hasil (contoh: hasil_dork.txt): ").strip()
      if not nama_file:
          print("[❌] Nama file tidak boleh kosong.")
      else:
          output_file = os.path.join(OUTPUT_FOLDER_DORKING, nama_file)
          manual_dorking(output_file)
        
    
# def ini untuk send notif ke tele    
def kirim_laporan_telegram(path_file, domain):
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
            isi = f"[ℹ️] Tidak ada kerentanan ditemukan untuk {domain}."

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            'chat_id': CHAT_ID,
            'text': f"[Laporan nuclei untuk {domain}]\n\n{isi}"
        })

        if response.status_code == 200:
            print(f"[✅] Laporan {domain} berhasil dikirim ke Telegram.")
        else:
            print(f"[❌] Gagal kirim laporan Telegram untuk {domain}: {response.text}")
    except Exception as e:
        print(f"[⚠️] Terjadi kesalahan saat mengirim ke Telegram: {e}")

def main():
    print_logo()
    target = get_target_input()
    print(f"\n?? Memproses domain: {target}\n")
    process_domain(target)  # Memproses domain tunggal
    print("[??] Proses selesai untuk domain tersebut!")
    
    
if __name__ == "__main__":
    print_logo()
    scan_type = tampilkan_menu()
    if scan_type in "1":
        target = get_target_input()
        print(f"\n[▶] Memulai proses untuk {target}")
        process_domain(target, scan_type)
    elif scan_type == "2":
        print("Premium Version! buy at https://lynk.id/aier/mloYxRr/")
    elif scan_type == "3":
        print("Premium Version! buy at https://lynk.id/aier/mloYxRr/")
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
