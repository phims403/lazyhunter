import os
import subprocess
import shutil
import requests
import tempfile
import random
import time 
import json 
import base64
import sys
import datetime
import threading
import select
import termios
import tty
import signal
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import socket
import config
import re
import importlib

from rich.console import Console
from rich.status import Status
from rich.live import Live
from rich.text import Text
console = Console()

from config import GITHUB_USER, GITHUB_REPO, BOT_TOKEN, CHAT_ID, KATANA_LIMIT
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
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            decoded = response.text.strip()
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
                 ░         ░                                                          
"""
    print(red + logo + reset)
    print(f"                                LAZYHUNTER v{version_status}")
    print("Author     : PHIMS                Linkedin    : PHIMS SEC")
    print("Instagram  : @aier_phims          GitHub      : phims403")
    print("Youtube    : elphims              Telegram    : @phimssec")
def display_menu():
    print("\n    Choose Feature:")
    print("  [0]  Feature Information")
    print("  [1]  Light Scan")
    print("  [2]  Dark Scan")
    print("  [3]  Deep Scan (\033[91mTOP FEATURE\033[0m)")
    print("  [4]  Scan Subdomain Takeover")
    print("  [5]  find Sensitive Data")
    print("  [9]  Setup Configuration")
    print("  [99] Out ")
    print("  [999] Update Tool")
    print("──────────────────────────────────────────────────────────────────────────────")
    while True:
        choice = input("Choose Feature (0-9, 99, or 999): ").strip()
        if choice in ["0","1","2","3","4","5","8","9","99","999"]:
            return choice

        print("[❌] Invalid choice. Enter number 0-9, 99, or 999")

def setup_menu():
    while True:
        print("\n=== Setup Menu ===")
        print("1. Setup Bot Token")
        print("2. Setup Chat ID")
        print("3. Setup Scanning Speed")
        print("4. Setup Katana Limit")
        print("5. Setup All")
        print("6. Back to main menu")
        select = input("Select (1-6): ").strip()
        if select == "1":
            cur = getattr(config, "BOT_TOKEN", "")
            val = input(f"Bot Token (current: '{cur[:6]}...'), enter=skip: ").strip()
            if val:
                write_config({"BOT_TOKEN": val})
        elif select == "2":
            cur = getattr(config, "CHAT_ID", "")
            val = input(f"Chat ID (current: '{cur}'), enter=skip: ").strip()
            if val:
                write_config({"CHAT_ID": val})
        elif select == "3":
            cur = getattr(config, "SCAN_SPEED", "")
            print("Select scanning speed:")
            print("1. Low")
            print("2. Standard")
            print("3. Fast")
            while True:
                choice = input(f"Scan Speed (current: '{cur}'): ").strip()
                if choice == "1":
                    write_config({"SCAN_SPEED": "low"})
                    break
                elif choice == "2":
                    write_config({"SCAN_SPEED": "standard"})
                    break
                elif choice == "3":
                    write_config({"SCAN_SPEED": "fast"})
                    break
                else:
                    print("[!] Invalid choice; use 1/2/3.")

            
        elif select == "4":
            print("\nKatana crawling can take a very long time if there are many active subdomains.")
            print("Limit the number of active subdomains used to avoid very long processing times.")
            print("Enter 0 to skip the crawling process with Katana.")
            print("Enter 00 (double zero) to make Katana unlimited (no limit).")
            current_limit = getattr(config, 'KATANA_LIMIT', 20)
            new_limit = input(f"Enter subdomain limit for Katana (currently {current_limit}): ").strip()
            if new_limit.isdigit():
                if new_limit == "00":
                    write_config({"KATANA_LIMIT": 0})  # 0 means unlimited in the application logic
                    print("[✓] Katana set to unlimited mode (limit set to 00).")
                else:
                    new_limit_int = int(new_limit)
                    write_config({"KATANA_LIMIT": new_limit_int})
                    if new_limit_int == 0:
                        print("[✓] Katana crawling will be skipped (limit set to 0).")
                    else:
                        print(f"[✓] Katana limit changed to {new_limit_int}")
            else:
                print("[ℹ️] Invalid input, no changes made.")



        elif select == "5":
            updates = {}
            v = input(f"Bot Token (current: '{getattr(config,'BOT_TOKEN','')[:6]}...'), enter=skip: ").strip()
            if v: updates["BOT_TOKEN"] = v
            v = input(f"Chat ID (current: '{getattr(config,'CHAT_ID','')}'), enter=skip: ").strip()
            if v: updates["CHAT_ID"] = v
            print("Select scanning speed (current: '{}'):".format(getattr(config,'SCAN_SPEED','')))
            print("1. Low")
            print("2. Standard") 
            print("3. Fast")
            speed_choice = input("Enter choice (1-3) or enter=skip: ").strip()
            if speed_choice == "1":
                updates["SCAN_SPEED"] = "low"
            elif speed_choice == "2":
                updates["SCAN_SPEED"] = "standard"
            elif speed_choice == "3":
                updates["SCAN_SPEED"] = "fast"
            current_limit = getattr(config, 'KATANA_LIMIT', 20)
            limit_val = input(f"Enter Katana Limit (currently {current_limit}, Enter skip): ").strip()
            if limit_val.isdigit():
                if limit_val == "00":
                    updates["KATANA_LIMIT"] = 0
                else:
                    updates["KATANA_LIMIT"] = int(limit_val)
            
            if updates:
                write_config(updates)
            else:
                print("[ℹ️] No changes made.")
        elif select == "6":
            return
        else:
            print("[❌] Invalid choice.")

def run_with_animation(message, func, *args, **kwargs):
    console.print(f"[bright_blue][+] {message}...[/bright_blue]")
    result = func(*args, **kwargs)
    if isinstance(result, subprocess.Popen):
        # Use rich status while process is running
        with Status(f"[bold bright_blue]Running {message}[/bold bright_blue]", console=console) as status:
            for line in iter(result.stdout.readline, ''):
                if line:
                    # Display original output without additional colors (highlight=False)
                    console.print(line.rstrip(), highlight=False)
            result.wait()
    else:
        pass
    console.print(f"[green][✓] {message} completed.[/green]")
def get_target_input():
    """Ask for target URL input directly from user."""
    while True:
        target = input("Enter target URL (example: example.com): ").strip()
        if target:
            return target
        print("[❌] Invalid URL! Enter the correct URL.")
def run_with_animation_no_output(message, func, tool_name=None, label="Item", output_file=None, *args, **kwargs):
    if tool_name is None:
        tool_name = message.split("With")[-1].strip() if "With" in message else "Tool"
    
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner_index = 0
    count = 0

    def get_live_text():
        spinner = spinner_frames[spinner_index]
        base_text = Text(f"{spinner} {message}...", style="bright_blue")
        
        if count > 0:
            found_text = Text()
            found_text.append(" Found ", style="bright_blue")
            found_text.append(str(count), style="yellow")  # Yellow number
            found_text.append(f" {label}", style="bright_blue")
            base_text.append(found_text)
        
        return base_text

    with Live(get_live_text(), console=console, refresh_per_second=10, transient=True) as live:
        result = func(*args, **kwargs)
        
        if isinstance(result, subprocess.Popen) and output_file:
            while not os.path.exists(output_file) and result.poll() is None:
                time.sleep(0.1)
                spinner_index = (spinner_index + 1) % len(spinner_frames)
                live.update(get_live_text())

            try:
                with open(output_file, 'r', encoding="utf-8", errors="ignore") as f:
                    while result.poll() is None:
                        line = f.readline()
                        if line.strip():
                            count += 1
                        
                        spinner_index = (spinner_index + 1) % len(spinner_frames)
                        live.update(get_live_text())
                        
                        if not line:
                            time.sleep(0.05)
            except Exception as e:
                live.update(Text(f"[!] Failed to read file: {e}", style="red"))

            result.wait()

        # Final verification
        if output_file and os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding="utf-8", errors="ignore") as f:
                    count = len([line for line in f if line.strip()])
            except:
                pass

    # === FINAL MESSAGE: COLORS AS DESIRED ===
    final_text = Text()
    final_text.append("[✓] ", style="yellow")                    # Green checkmark
    final_text.append(tool_name, style="bright_blue")                  # Blue tool name
    final_text.append(" Found ", style="bright_blue")     # Blue text
    final_text.append(str(count), style="yellow")               # Yellow number (same as checkmark)
    final_text.append(f" {label}", style="bright_blue")                # Blue label
    console.print(final_text)

def feature_info():
    info = r"""
=== FEATURE INFORMATION ===

1. Light Scan (Fast Scanning)
   - Subfinder → find subdomains from target domain.
   - Httpx → filter active subdomains (HTTP response).
   - Nuclei → scan active subdomains using common templates like:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, etc.
   - Scan speed can be adjusted (low/standard/fast).
   - Scan results are automatically sent to Telegram.

2. Dark Scan (Medium Recon)
   - Subfinder + Assetfinder → find as many subdomains as possible from target.
   - Combine and remove duplicate results.
   - Httpx → validate active subdomains.
   - Katana → crawling URLs to find parameters from active subdomains.
   - Grep → filter URLs that have parameters (?key=value).
   - Nuclei stage 1 → scan parameterized URLs for vulnerability detection like xss, sqli, lfi, etc.
   - Nuclei stage 2 → scan URLs (.js) for exposure detection
   - Scan speed can be adjusted (low/standard/fast).
   - All results are automatically sent to Telegram.
    
3. Deep Scan (Deep Recon)
   - Same as Dark Scan with differences:
   - Nuclei stage 1 → initial scan using common templates like:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, etc.
   - Nuclei stage 2 → scan parameterized URLs for vulnerability detection like xss, sqli, lfi, etc.
   - Nuclei stage 3 → scan URLs (.js) for exposure detection
   - Nuclei stage 4 → scan subdomains for subdomain takeover detection

4. Find Sensitive Data (Automatic Sensitive Data Search)
   - Uses crawling results from previous gau process to identify URLs with sensitive extensions.
   - Filters URLs that contain extensions: .zip, .tar, .gz, .7z, .rar, .bak, .backup, .old, 
     .sql, .db, .sqlite, .env, .log, .conf, .config, .ini, .cfg, .xml, .json, .js
   - Tests filtered URLs with Httpx to identify active sensitive resources.
   - Detects configuration files, credentials, or important backups that are publicly exposed.
   - Results are saved to text file.

5. Subdomain Takeover Checker
   - Has two modes:
     • Mass → from subdomain list file.
     • Wildcard → auto subdomain with subfinder.
   - Uses Nuclei with `takeovers` template to check for possible takeover.
   - Scan results are sent to Telegram.
"""
    print(info)




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

SPEED_ARGS = {
    "low": {
        "nuclei": ["-c", "10", "--max-host-error", "20"],
        "httpx": ["-silent", "-mc", "200", "-t", "50", "-rate-limit", "100", "-retries", "1", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-t", "50", "-rate-limit", "100", "-retries", "1", "-timeout", "10"],
        "katana": ["-jc", "5", "-d", "2"],
        "gau": ["--subs", "--threads", "5", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    },
    "standard": {
        "nuclei": ["-c", "25", "--max-host-error", "30"],
        "httpx": ["-silent", "-mc", "200", "-t", "200", "-rate-limit", "500", "-retries", "2", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-t", "200", "-rate-limit", "500", "-retries", "2", "-timeout", "10"],
        "katana": ["-jc", "15", "-d", "4"],
        "gau": ["--subs", "--threads", "20", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    },
    "fast": {
        "nuclei": ["-c", "40", "--max-host-error", "50"],
        "httpx": ["-silent", "-mc", "200", "-t", "300", "-rate-limit", "1200", "-retries", "4", "-timeout", "10"],
        "httpx_sensitive": ["-silent", "-mc", "200,403", "-t", "300", "-rate-limit", "1200", "-retries", "4", "-timeout", "10"],
        "katana": ["-jc", "30", "-d", "6"],
        "gau": ["--subs", "--threads", "40", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
    }
}

def write_config(updates: dict):
    """
    updates: dict, example {"SCAN_SPEED": "fast"}
    This function changes/adds values in config.py then reloads the config module.
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
    # reload module so runtime uses current config
    importlib.reload(config)
    print("[✓] config.py updated and reloaded.")

def get_speed():
    s = getattr(config, "SCAN_SPEED", None)
    if not s:
        return None
    s = s.lower()
    return s if s in SPEED_ARGS else None

def get_tool_args(tool_name: str):
    """
    tool_name: "nuclei" | "httpx" | "httpx_sensitive" | "katana" | "gau"
    -> returns list args according to config.SCAN_SPEED if exists, else None
    """
    s = get_speed()
    if not s:
        return None
    return SPEED_ARGS[s].get(tool_name)
# --------------------------------------------------------------------

def ask_scan_speed():
    # check config
    speed = get_speed()
    if speed:
        print(f"[ℹ️] Scan speed ->{speed}")
        return SPEED_ARGS[speed]["nuclei"]
    # if not exists (empty / None), then ask user
    choice = input("\nSelect Scanning Speed: 1.Low, 2.Standard, 3.Fast: ").strip()
    if choice == "1":
        return SPEED_ARGS["low"]["nuclei"]
    elif choice == "2":
        return SPEED_ARGS["standard"]["nuclei"]
    elif choice == "3":
        return SPEED_ARGS["fast"]["nuclei"]
    else:
        print("[❌] Invalid choice. Defaulting to Standard.")
        return SPEED_ARGS["standard"]["nuclei"]

def clean_link(link):
    if link.startswith("//"):
        link = "https:" + link
    parsed = urlparse(link)
    if 'duckduckgo.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        if 'uddg' in qs:
            return unquote(qs['uddg'][0])
    return link

def extract_domain_from_url(url):
    """Extract domain from URL without subdomain"""
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    # Remove port if present
    domain = domain.split(':')[0]
    return domain

def is_subdomain_of_base_domain(domain, base_domain):
    """Check if domain is subdomain of base_domain"""
    domain = domain.lower()
    base_domain = base_domain.lower()
    
    # Direct match
    if domain == base_domain:
        return True
    
    # Subdomain match (e.g., app.example.com is subdomain of example.com)
    if domain.endswith('.' + base_domain):
        return True
    
    return False

def filter_domains_from_base_domain(input_file, base_domain, output_file):
    """Filter domains/URLs to only include those from the base domain or its subdomains"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract domain from URL or use as-is for subdomain
        if line.startswith(('http://', 'https://')):
            domain = extract_domain_from_url(line)
        else:
            domain = line
        
        # Check if it's subdomain of base domain
        if is_subdomain_of_base_domain(domain, base_domain):
            filtered_lines.append(line)
    
    # Write filtered results to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in filtered_lines:
            f.write(line + '\n')
    
    return len(filtered_lines)

def filter_subdomains_from_file(input_file, base_domain, output_file):
    """Filter subdomains file to only include those from the base domain"""
    return filter_domains_from_base_domain(input_file, base_domain, output_file)
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
    print(f"\033[94m[+] Starting dorking search for: {target}\033[0m")
    results = []
    for dork_template in SENSITIVE_DORKS:
        dork = dork_template.format(target=target)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        url = f"https://html.duckduckgo.com/html?q={dork}"
        print(f"[⚙️] Searching: {dork}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for result in soup.find_all('a', class_='result__a'):
                link = result.get('href')
                if link:
                  clean = clean_link(link)
                  print(f"[✅] {clean}")
                  results.append(clean)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"[❌] Error searching dork '{dork}': {e}")
    with open(output_file, "w") as f:
        for url in results:
            f.write(url + "\n")
    print(f"[📁] Dork results saved at: {output_file}")
def manual_dorking(output_file):
    dork = input("Enter manual dork: ").strip()
    if not dork:
        print("[❌] Dork cannot be empty.")
        return
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    url = f"https://html.duckduckgo.com/html?q={dork}"
    print(f"[🔍] Searching: {dork}")
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for result in soup.find_all('a', class_='result__a'):
            link = result.get('href')
            if link:
              clean = clean_link(link)
              print(f"[✅] {clean}")
              results.append(clean)
        time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"[❌] Search failed: {e}")
    with open(output_file, "w") as f:
        for url in results:
            f.write(url + "\n")
    print(f"[📁] Results saved at: {output_file}")
def find_sensitive_data(target):
    gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau_{target}.txt")
    crawling_gau(gau_output, target)
    
    # Filter the gau output to only include URLs from the target domain
    gau_filtered = gau_output + ".tmp"
    import shutil
    shutil.copy(gau_output, gau_filtered)
    filter_domains_from_base_domain(gau_filtered, target, gau_output)
    os.remove(gau_filtered)
    
    check_sensitive_urls(target, gau_output)

def check_sensitive_urls(target, input_file):
    httpx_args = get_tool_args("httpx_sensitive") or ["-silent", "-mc", "200,403", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
    
    # First, filter the input file to only include URLs from the target domain
    filtered_input_file = input_file + ".filtered"
    filter_domains_from_base_domain(input_file, target, filtered_input_file)
    
    pot_sen_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"pot_sen_url_{target}.txt")
    sen_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sen_url_{target}.txt")
    sensitive_exts = [
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".bak", ".backup", ".old",
        ".sql", ".db", ".sqlite",
        ".env", ".log",
        ".conf", ".config", ".ini", ".cfg",
        ".xml", ".json", ".js"
    ]
    try:
        urls = []
        if os.path.exists(filtered_input_file):
            with open(filtered_input_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    url = line.strip()
                    if any(url.endswith(ext) or ext in url for ext in sensitive_exts):
                        urls.append(url)
        if not urls:
            print(f"[ℹ️] No sensitive URLs found for {target}")
            # Clean up temporary file
            if os.path.exists(filtered_input_file):
                os.remove(filtered_input_file)
            return []  # Return empty list if none

        with open(pot_sen_file, "w") as f:
            for url in urls:
                f.write(url + "\n")

        def run_find_sensitive_data():
            cmd = f"cat {pot_sen_file} | httpx {' '.join(httpx_args)}"
            return subprocess.Popen(
                cmd,
                shell=True,
                stdout=open(sen_file, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL
            )
        run_with_animation_no_output(
            message="Checking URLs with sensitive potential",
            func=run_find_sensitive_data,
            tool_name="Httpx",
            label="Potential Sensitive URLs",
            output_file=sen_file
        )
        # Read active sensitive URLs from sen_file
        sensitive_urls = []
        if os.path.exists(sen_file):
            with open(sen_file, "r", encoding="utf-8", errors="ignore") as f:
                sensitive_urls = [line.strip() for line in f if line.strip()]
        
        # Clean up temporary file
        if os.path.exists(filtered_input_file):
            os.remove(filtered_input_file)
        
        return sensitive_urls  # Return URL list for further processing
    except subprocess.CalledProcessError as e:
        print("[!] Failed running Httpx")
        print(e)
        log_error(target, "Httpx sensitive data", str(e))
        # Clean up temporary file
        if os.path.exists(filtered_input_file):
            os.remove(filtered_input_file)
        return []
    send_file_telegram(sen_file, target)




def log_error(target, process, error_message, error_log_file="error.log"):
    # Create error file if not exists
    if not os.path.exists(error_log_file):
        with open(error_log_file, "w", encoding="utf-8") as f:
            f.write("=== Tool Error Log ===\n\n")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_text = (
        f"[{now}]\n"
        f"Target     : {target}\n"
        f"Process    : {process}\n"
        f"Error      : {error_message}\n"
        f"{'-'*50}\n"
    )

    with open(error_log_file, "a", encoding="utf-8") as f:
        f.write(log_text)

    print("\n[!] Error occurred:\n")
    print(error_message)

def read_file_real_time(tool_name, file_path, label, process):
    stop_evt = threading.Event()

    count = 0
    try:
        # wait for file to appear
        while not os.path.exists(file_path):
            time.sleep(0.1)


        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                line = f.readline()
                if not line:
                    if process and process.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue

                count += 1
                msg = f"[+] Running {tool_name} found \033[93m{count}\033[94m {label}..."
                # remove \n to prevent new lines
                sys.stdout.write("\r" + msg + " " * 20)  
                sys.stdout.flush()

        if not stop_evt.is_set():
            print(f"\r\033[33m[✓]\033[94m {tool_name} successfully found \033[93m{count}\033[94m {label}\033[0m".ljust(100))

    except Exception as e:
        print(f"[!] Failed to read file {file_path}: {e}")


        
def finding_subdomain(target, subdomain_file):
    temp_subdomain_file = subdomain_file + ".tmp"
    running_subfinder(target, temp_subdomain_file)
    running_assetfinder(target, temp_subdomain_file)
    
    # Filter the subdomains to only include those from the base target domain
    filter_subdomains_from_file(temp_subdomain_file, target, subdomain_file)
    
    # Remove temporary file
    if os.path.exists(temp_subdomain_file):
        os.remove(temp_subdomain_file) 

def running_subfinder(target, subdomain_file):
    try:
        def run_subfinder():
            return subprocess.Popen([
                "subfinder", "-silent", "-all", "-d", target, "-o", subdomain_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_with_animation_no_output(
            message="Finding Subdomain With Subfinder",
            func=run_subfinder,
            tool_name="Subfinder",
            label="subdomains",
            output_file=subdomain_file
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Subfinder")
            print(e)
            log_error(target, "Subfinder", str(e))
            return
def running_assetfinder(target, subdomain_file):
    assetfinder_tmp = tempfile.NamedTemporaryFile(delete=False).name
    try:
        def run_assetfinder():
            return subprocess.Popen(
                ["assetfinder", "-subs-only", target],
                stdout=open(assetfinder_tmp, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL,
                text=True
            )
        run_with_animation_no_output(
            message="Finding Subdomain With Assetfinder",
            func=run_assetfinder,
            tool_name="Assetfinder",
            label="subdomains",
            output_file=assetfinder_tmp
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Assetfinder")
            print(e)
            log_error(target, "Assetfinder", str(e))
            return  
    all_subs = set()
    for path in [subdomain_file, assetfinder_tmp]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            all_subs.update(line.strip() for line in f if line.strip())
    # --- ADD MAIN DOMAIN TO SUBDOMAIN FILE ---
    subdomain_set = set()
    # Read existing subdomains
    if os.path.exists(subdomain_file):
        with open(subdomain_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                sub = line.strip()
                if sub:
                    subdomain_set.add(sub)
    # Add main domain (only host, without http/https/path/port)
    target_clean = target.split("://")[-1].split("/")[0].split(":")[0]
    subdomain_set.add(target_clean)
    # Rewrite subdomain file
    with open(subdomain_file, "w", encoding="utf-8") as f:
        for sub in sorted(subdomain_set):
            f.write(sub + "\n")        
    with open(subdomain_file, "w") as f:
        f.write("\n".join(sorted(all_subs)))
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(all_subs)}\033[94m subdomains\033[0m")

def active_check(active_file, subdomain_file, url, target):
    #[+] Checking active {url}...
    try:
        def run_httpx():
            httpx_args = get_tool_args("httpx") or ["-silent", "-mc", "200", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
            return subprocess.Popen(
                ["httpx", *httpx_args, "-l", subdomain_file],
                stdout=open(active_file, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL,
                text=True
            )
        run_with_animation_no_output(
            message=f"Checking active {url}",
            func=run_httpx,
            tool_name="Httpx",
            label=f"{url} active",
            output_file=active_file
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Httpx")
            print(e)
            log_error(target, "Httpx", str(e))
            return 
    with open(active_file) as f:
        active = len(f.readlines())

def process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output):
    crawling_wayback(wayback_output, active_file, target)
    crawling_gau(gau_output, target)
    crawling_katana(katana_output, active_file, target)
    combine_crawling_results(wayback_output, gau_output, katana_output, crawled_filtered_output, target)

def crawling_wayback(wayback_output, active_file, target):
    try:
        def run_waybackurls():
            # Command as STRING + shell=True
            cmd = f"cat {active_file} | waybackurls"
            return subprocess.Popen(
                cmd,
                shell=True,  # <--- REQUIRED!
                stdout=open(wayback_output, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL
            )
        run_with_animation_no_output(
            message="Crawling URLs With Waybackurls",
            func=run_waybackurls,
            tool_name="Waybackurls",
            label="URLs",
            output_file=wayback_output
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Waybackurl")
            print(e)
            log_error(target, "Waybackurl", str(e))
            return  
    wayback_urls = []
    if os.path.exists(wayback_output):
        with open(wayback_output, "r", encoding="utf-8", errors="ignore") as f:
            wayback_urls = [line.strip() for line in f if "http" in line]

def crawling_gau(gau_output, target):
    try:
        gau_args = get_tool_args("gau") or ["--subs", "--threads", "20", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,otf,ico", "--verbose"]
        def run_gau():
            return subprocess.Popen(
                ["gau", target, *gau_args],
                stdout=open(gau_output, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL,
                text=True
            )
        run_with_animation_no_output(
            message="Crawling URLs with Gau",
            func=run_gau,
            tool_name="Gau",
            label="URLs",
            output_file=gau_output
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Gau")
            print(e)
            log_error(target, "Gau", str(e))
            return
    gau_urls = []
    if os.path.exists(gau_output):
        with open(gau_output, "r", encoding="utf-8", errors="ignore") as f:
            gau_urls = [line.strip() for line in f if "http" in line]

def crawling_katana(katana_output, input_file, target):
    limit = getattr(config, "KATANA_LIMIT", 20)
    if limit == 0:
        print(f"\033[94m[ℹ️] Katana limit set to 0, skipping crawling process with Katana for {target}\033[0m")
        with open(katana_output, "w") as f:
            f.write("")  # Create empty file for consistency
        return

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        alive_subs = [line.strip() for line in f if line.strip()]

    if len(alive_subs) >= limit:
        limited_file = os.path.join(os.path.dirname(input_file), f"{limit}active_{target}.txt")
        with open(limited_file, "w") as f:
            for sub in alive_subs[:limit]:
                f.write(sub + "\n")
        #[+] Active subdomains ≥ {limit}, only using {limit} active subdomains
        #print(f"\033[94m[+] Active subdomains ≥ {limit}, only using {limit} active subdomains\033[0m")
        input_for_katana = limited_file
    else:
        #[+] Active subdomains < {limit}, directly use entire file for Katana scan
        input_for_katana = input_file

    #[+] Starting crawling process with Katana...

    try:
        def run_katana():
            katana_args = get_tool_args("katana") or ["-jc", "15", "-d", "4"]
            return subprocess.Popen(
                ["katana", "-list", input_for_katana, *katana_args, "-f", "qurl", "-fs", "fqdn"],
                stdout=open(katana_output, "w", encoding="utf-8"),
                stderr=subprocess.DEVNULL,
                text=True
            )
        run_with_animation_no_output(
            message="Crawling URLs with Katana",
            func=run_katana,
            tool_name="Katana",
            label="URLs",
            output_file=katana_output
        )
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Katana")
            print(e)
            log_error(target, "Katana", str(e))
            return  

def combine_crawling_results(wayback_output, gau_output, katana_output, crawled_filtered_output, target):
    katana_urls = []
    if os.path.exists(katana_output):
        with open(katana_output, "r", encoding="utf-8", errors="ignore") as f:
            katana_urls = [line.strip() for line in f if "http" in line]
    wayback_urls = []
    if os.path.exists(wayback_output):
        with open(wayback_output, "r", encoding="utf-8", errors="ignore") as f:
            wayback_urls = [line.strip() for line in f if "http" in line]
    gau_urls = []
    if os.path.exists(gau_output):
        with open(gau_output, "r", encoding="utf-8", errors="ignore") as f:
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
 
def separate_urls(crawled_filtered_output, param_output, js_output, target):
    # Extract target from output file path to get target domain
    # The target is the domain part from the crawled_filtered_output path
    import re
    target_match = re.search(r'crawled_filtered_(.*)\.txt', os.path.basename(crawled_filtered_output))
    if target_match:
        actual_target = target_match.group(1)
    else:
        actual_target = target  # fallback to provided target
    
    # Filter the crawled URLs to only include those from the target domain
    filtered_crawled_file = crawled_filtered_output + ".filtered"
    filter_domains_from_base_domain(crawled_filtered_output, actual_target, filtered_crawled_file)
    
    param_urls = []
    js_urls = []
    with open(filtered_crawled_file, "r", encoding="utf-8", errors="ignore") as infile:
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
    
    # Clean up temporary file
    if os.path.exists(filtered_crawled_file):
        os.remove(filtered_crawled_file)
    
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(param_urls)}\033[94m URLs with parameter\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(js_urls)}\033[94m URLs .js\033[0m")

def process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output):
    # Process crawling for each tool
    crawling_wayback(wayback_output, active_file, target)
    crawling_gau(gau_output, target)
    with open(active_file, "r", encoding="utf-8", errors="ignore") as f:
        alive_subs = [line.strip() for line in f if line.strip()]
    limit = getattr(config, "KATANA_LIMIT", 20)

    if len(alive_subs) >= limit:
        limited_file = os.path.join(os.path.dirname(active_file), f"{limit}active_{target}.txt")
        with open(limited_file, "w") as f:
            for sub in alive_subs[:limit]:  # take according to limit
                f.write(sub + "\n")
        print(f"\033[94m[+] Active subdomains ≥ {limit}, only using {limit} active subdomains\033[0m")
        input_for_katana = limited_file
    else:
        print(f"\033[94m[+] Active subdomains < {limit}, directly use entire file for Katana scan\033[0m")
        input_for_katana = active_file
    crawling_katana(katana_output, input_for_katana, target)
    
    # Filter each crawling result to only include URLs from the target domain
    wayback_filtered = wayback_output + ".tmp"
    gau_filtered = gau_output + ".tmp"
    katana_filtered = katana_output + ".tmp"
    
    # Copy original files to temporary files for filtering
    import shutil
    shutil.copy(wayback_output, wayback_filtered)
    shutil.copy(gau_output, gau_filtered)
    shutil.copy(katana_output, katana_filtered)
    
    # Filter each crawling result
    filter_domains_from_base_domain(wayback_filtered, target, wayback_output)
    filter_domains_from_base_domain(gau_filtered, target, gau_output)
    filter_domains_from_base_domain(katana_filtered, target, katana_output)
    
    # Remove temporary files
    os.remove(wayback_filtered)
    os.remove(gau_filtered)
    os.remove(katana_filtered)
    
    combine_crawling_results(wayback_output, gau_output, katana_output, crawled_filtered_output, target)


def send_file_telegram(file_path, domain):
    """Send scan result file to Telegram (sendDocument)."""
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
        print("[ℹ️] Bot token or chat_id not found / invalid. Skipping Telegram sending.")
        return 
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument"
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        # If file empty → send text only
        message = f"[❌] No sensitive path detected for {domain}"
        requests.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
            data={'chat_id': config.CHAT_ID, 'text': message}
        )
        print(f"[ℹ️] No sensitive path for {domain}")
        return
    try:
        with open(file_path, "rb") as f:
            response = requests.post(url, data={'chat_id': config.CHAT_ID}, files={'document': f})
        if response.status_code == 200:
            print(f"[✓] Sensitive path result file {domain} successfully sent to Telegram.")
        else:
            print(f"[❌] Failed to send file to Telegram: {response.text}")
    except Exception as e:
        print(f"[⚠️] Error sending file to Telegram: {e}")



def nuclei_without_parameter(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_basic_scan():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-nh", "-s", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot,xss", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        run_with_animation("Nuclei (Basic scan)", nuclei_basic_scan)
    except subprocess.CalledProcessError as e:
        print("[!] Failed to run Nuclei (Basic Scan)")
        print(e)
        log_error(target, "Nuclei (Basic Scan)", str(e))
        return      
    send_telegram_report(output_file, f"{target} (Nuclei Basic Scan)")      

def nuclei_js_exposure(target, input_file, output_file, user_agent, scan_args):
    try: 
        def nuclei_js_file():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-s", "low,medium,high,critical", "-nh", "-tags", "js,secrets,exposed-credentials", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        run_with_animation("Running Nuclei (JS File)", nuclei_js_file)
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Nuclei (JS File)")
            print(e)
            log_error(target, "Nuclei (JS File)", str(e))
            return            
    send_telegram_report(output_file, f"{target} (JS File)")            

def nuclei_param_dast(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_dast_mode():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-nh", "-dast", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        run_with_animation("Nuclei DAST MODE", nuclei_dast_mode)
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Nuclei DAST Mode)")
            print(e)
            log_error(target, "Nuclei DAST Mode)", str(e))
            return            
    send_telegram_report(output_file, f"{target} Nuclei DAST Mode)")            

def nuclei_takeover(subdomain_file, output_path_takeover, target):
    try:
        def nuclei_takeover_scan():
            return subprocess.Popen([
                "nuclei", "-l", subdomain_file, "-nh", "-tags", "takeover", "-o", output_path_takeover
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        run_with_animation("Nuclei Takeover Wildcard", nuclei_takeover_scan)
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Nuclei Takeover Wildcard)")
            print(e)
            log_error(target, "Nuclei Takeover Wildcard)", str(e))
            return            
    send_telegram_report(output_path_takeover, f"Takeover Wildcard ({target})")            
def takeover():
    while True:
        print("\n=== Takeover Mode ===")
        print("1. Mass (from file)")
        print("2. Wildcard (find subdomain automatic)")
        print("3. Back to main menu")
        sub_mode = input("Select Mode (1/2/3): ").strip()
        if sub_mode in ("1", "2"):
            check_takeover(sub_mode)
        elif sub_mode == "3":
            return
        else:
            print("[❌] Invalid choice.")
def check_takeover(mode):
    if mode == "1":
        file_name = input("Enter file name containing domain/subdomain list (example: subdomain.txt): ").strip()
        if not os.path.isfile(file_name):
            print("[❌] File not found.")
            return
        output_name = input("Enter output file name (without .txt): ").strip()
        if not output_name:
            print("[❌] Output file name cannot be empty.")
            return
        input_file = file_name
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_name}.txt")
        label = f"Takeover Mass ({output_name})"
    else:
        target = get_target_input()
        input_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
        finding_subdomain(target, input_file)
        label = f"Takeover Wildcard ({target})"
    def run_nuc_takeover():
        return subprocess.Popen([
            "nuclei", "-l", input_file, "-nh", "-tags", "takeover", "-o", output_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    run_with_animation(f"Nuclei {label}", run_nuc_takeover)
    send_telegram_report(output_path, label)    


def light_scan():
        target = get_target_input()
        scan_args = ask_scan_speed()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        print(f"\n[▶] Starting process for {target}")
        start_time_url = time.time()
        finding_subdomain(target, subdomain_file)
        active_check(active_file, subdomain_file, "Subdomain", target)
        start_time_nuclei_scan = time.time()
        nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
        end_time_nuclei_scan = time.time()
        scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
        hours, remaining = divmod(int(scan_duration), 3600)
        minutes, seconds = divmod(remaining, 60)
        print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
        print(f"[✓] All processes completed for target: {target}")
        
def dark_deep(mode):
        target = get_target_input()
        scan_args = ask_scan_speed()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        katana_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"katana_{target}.txt")
        wayback_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"wayback_{target}.txt")
        gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau{target}.txt")
        nuclei_output_crawled = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_{target}_crawled.txt")
        crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
        temp_crawled_filtered_output = os.path.join (OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        param_output = os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt")
        js_output = os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt")
        nuclei_output_js = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt")
        nuclei_output_param = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt")
        print(f"\n[▶] Starting process for {target}")
        start_time_url = time.time()
        finding_subdomain(target, subdomain_file)
        active_check(active_file, subdomain_file, "Subdomain", target)
        process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)
        active_check(temp_crawled_filtered_output, crawled_filtered_output, "URL", target)
        shutil.move(temp_crawled_filtered_output, crawled_filtered_output)
        separate_urls(crawled_filtered_output, param_output, js_output, target)
        end_time_url = time.time()
        url_duration = end_time_url - start_time_url
        hours, remaining = divmod(int(url_duration), 3600)
        minutes, seconds = divmod(remaining, 60)
        print(f"\033[92m[⏱️] Successfully collected URLs from {target} for "
            f"\033[93m{hours}\033[92m hours "
            f"\033[93m{minutes}\033[92m minutes "
            f"\033[93m{seconds}\033[92m seconds\033[0m")        
        start_time_nuclei_scan = time.time()
        if mode == "dark":
            nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
        elif mode == "deep":
            nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
            nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
            output_path_takeover = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
            print(f"[🚨] Running nuclei takeover scan for: {target}")
            try:
                subprocess.run([
                    "nuclei", "-l", subdomain_file, "-nh", "-t", "takeovers", "-o", output_path_takeover
                ], check=True)

                print(f"[✓] Scan completed. Results at: {output_path_takeover}")
                send_telegram_report(output_path_takeover, f"{target} (Deep Scan - Takeover)")
            except subprocess.CalledProcessError:
                print(f"[❌] Failed to run nuclei takeover scan for {target}")
        else:
            print(f"[!] Unknown scan mode: {mode}")
            return
        end_time_nuclei_scan = time.time()
        scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
        hours, remaining = divmod(int(scan_duration), 3600)
        minutes, seconds = divmod(remaining, 60)
        print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
        print(f"[✓] All processes completed for target: {target}")


def feature_update_tool():
    VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
    FILELIST_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/file_list.txt"
    TEMP_FOLDER = "temp_update"
    try:
        r = requests.get(VERSION_URL, timeout=5)
        if r.status_code == 200:
            remote_version = r.text.strip()
        else:
            print("[❌] Failed to check version (status {})".format(r.status_code))
            return
    except Exception as e:
        print("[❌] Error checking version:", e)
        return
    try:
        print("[⚙️] Checking latest version from GitHub...")
        if remote_version == LOCAL_VERSION:
            print(f"[✓] Tool already latest version: v{LOCAL_VERSION}")
            return
        print(f"[⬆️] New version available: v{remote_version}")
        r = requests.get(FILELIST_URL, timeout=5)
        if r.status_code == 200:
            file_list_content = r.text.strip()
            file_list = file_list_content.splitlines()
        else:
            print(f"[❌] Failed to get file_list.txt (status {r.status_code})")
            return
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        for file in file_list:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{file}"
            print(f"[↓] Downloading: {file}")
            r = requests.get(url)
            if r.status_code == 200:
                save_path = os.path.join(TEMP_FOLDER, file)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(r.text)
            else:
                print(f"[⚠️] Failed to download {file} (status {r.status_code})")
        for file in file_list:
            source = os.path.join(TEMP_FOLDER, file)
            destination = file
            if os.path.exists(source):
                shutil.copy(source, destination)
                print(f"[✔] Updated: {file}")
        shutil.rmtree(TEMP_FOLDER)
        print(f"[✓] Update successful to version v{remote_version}")
        print("[🔁] Restarting tool...")
        time.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"[❌] Failed to update: {e}")
if __name__ == "__main__":
    print_logo()
    while True:
        scan_type = display_menu()
        if scan_type == "1":
            light_scan()
        elif scan_type == "2":
            dark_deep("dark")
        elif scan_type == "3":
            dark_deep("deep")
        elif scan_type == "4":
            takeover()  
        elif scan_type == "5":
            target = get_target_input()
            find_sensitive_data(target)
        elif scan_type == "9":
            setup_menu()
        elif scan_type == "0":
            feature_info()
        elif scan_type == "99":
            print("[✔] Exiting LAZYHUNTER. Thank you!")
            break
        elif scan_type == "999": 
            feature_update_tool()
        else:
            print("[!] Invalid choice. Try again.")  
