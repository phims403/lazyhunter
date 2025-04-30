import os
import subprocess
import shutil
import requests

from config import BOT_TOKEN, CHAT_ID

def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)

def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()
    
TOOLS = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx",
    "nuclei": "github.com/projectdiscovery/nuclei/v2/cmd/nuclei",
}

OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
OUTPUT_FOLDER_NUCLEI = "nuclei"
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

def update_tools():
    """Memperbarui tools sebelum digunakan."""
    print("[??] Mengecek update untuk semua tools...")
    for tool in TOOLS:
        update_cmd = f"{tool} -update"
        subprocess.run(update_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    subprocess.run("nuclei -update-templates", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[✅] Semua tools telah diperbarui.")

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
                                                                                        
    Free Version: 1.1
    Premium Version? Buy at:
    http://lynk.id/aier/mloYxRr/  
    Author? PHIMS
    Github? phims403
    Instagram? @aier_phims
    Telegram? @phimssec
    Donate? chat with me on telegram
    """
def get_target_input():
    """Meminta input URL target langsung dari pengguna."""
    while True:
        target = input("Masukkan URL target (contoh: example.com): ").strip()
        if target:
            return target
        print("[❌] URL tidak valid! Masukkan URL yang benar.")

def detect_protocol(target):
    """Mendeteksi apakah domain mendukung HTTPS atau hanya HTTP."""
    try:
        result = subprocess.run(["httpx", "-silent", "-u", f"https://{target}"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return "https"
    except subprocess.TimeoutExpired:
        pass
    return "http"

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


def process_domain(target):
    """Melakukan scanning untuk satu domain."""
    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
    nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
    katana_output = os.path.join(OUTPUT_FOLDER_ACTIVE, f"katana_{target}.txt")

    print(f"\n[🔎] Mencari subdomain untuk: {target}")
    if not jalankan_tool(["subfinder", "-d", target, "-o", subdomain_file], "subfinder", target):
        return

    print("[🌐] Mengecek subdomain yang aktif...")
    if not jalankan_tool(["httpx", "-l", subdomain_file, "-o", active_file], "httpx", target):
        return
        
    print("[🚨] Menjalankan Nuclei scan (HTTPX result)...")
    if not jalankan_tool([
        "nuclei", "-l", active_file,
        "-severity", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot", "-as", "-ept", "ssl",
        "-o", nuclei_output_httpx
    ], "nuclei (HTTPX)", target):
        return
    

    kirim_laporan_telegram(nuclei_output_httpx, f"{target} ")

    print(f"[✅] Scanning selesai untuk: {target}\n")

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
    check_go()
    check_and_install_tools()
    update_tools()

    target = get_target_input()
    print(f"\n?? Memproses domain: {target}\n")

    process_domain(target)
    print("[??] Proses selesai untuk domain tersebut!")


if __name__ == "__main__":
    main()

