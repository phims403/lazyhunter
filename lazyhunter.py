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
import argparse

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

def check_previous_scan(target):
    """
    Check if target has been previously scanned by looking for output files
    Returns a dictionary with file status information
    """
    scan_status = {
        'subdomain_file': None,
        'active_file': None,
        'nuclei_output': None,
        'wayback_output': None,
        'gau_output': None,
        'katana_output': None,
        'crawled_filtered_output': None,
        'param_output': None,
        'js_output': None,
        'nuclei_output_js': None,
        'nuclei_output_param': None,
        'output_path_takeover': None,
        'has_any_files': False
    }

    subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    if os.path.exists(subdomain_file):
        scan_status['subdomain_file'] = subdomain_file
        scan_status['has_any_files'] = True

    active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
    if os.path.exists(active_file):
        scan_status['active_file'] = active_file
        scan_status['has_any_files'] = True

    nuclei_output = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
    if os.path.exists(nuclei_output):
        scan_status['nuclei_output'] = nuclei_output
        scan_status['has_any_files'] = True

    wayback_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"wayback_{target}.txt")
    if os.path.exists(wayback_output):
        scan_status['wayback_output'] = wayback_output
        scan_status['has_any_files'] = True

    gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau_{target}.txt")
    if os.path.exists(gau_output):
        scan_status['gau_output'] = gau_output
        scan_status['has_any_files'] = True

    katana_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"katana_{target}.txt")
    if os.path.exists(katana_output):
        scan_status['katana_output'] = katana_output
        scan_status['has_any_files'] = True

    crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
    if os.path.exists(crawled_filtered_output):
        scan_status['crawled_filtered_output'] = crawled_filtered_output
        scan_status['has_any_files'] = True

    param_output = os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt")
    if os.path.exists(param_output):
        scan_status['param_output'] = param_output
        scan_status['has_any_files'] = True

    js_output = os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt")
    if os.path.exists(js_output):
        scan_status['js_output'] = js_output
        scan_status['has_any_files'] = True

    nuclei_output_js = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt")
    if os.path.exists(nuclei_output_js):
        scan_status['nuclei_output_js'] = nuclei_output_js
        scan_status['has_any_files'] = True

    nuclei_output_param = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt")
    if os.path.exists(nuclei_output_param):
        scan_status['nuclei_output_param'] = nuclei_output_param
        scan_status['has_any_files'] = True

    output_path_takeover = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
    if os.path.exists(output_path_takeover):
        scan_status['output_path_takeover'] = output_path_takeover
        scan_status['has_any_files'] = True

    return scan_status

def ask_continue_or_restart(target, scan_status):
    """
    Ask user whether to continue previous scan or restart
    """
    print(f"\n[⚠️] Previous scan files found for target '{target}'")
    print("Files found:")
    for key, value in scan_status.items():
        if key != 'has_any_files' and value is not None:
            file_size = os.path.getsize(value)
            print(f"  - {value} ({file_size} bytes)")

    while True:
        choice = input(f"\n[?] Target '{target}' has been partially scanned. Continue previous scan (c), restart (r), or see details (d)? ").strip().lower()
        if choice in ['c', 'continue']:
            return 'continue'
        elif choice in ['r', 'restart']:
            return 'restart'
        elif choice in ['d', 'details']:
            print("\n[ℹ️] Scan Progress Analysis:")
            if scan_status['output_path_takeover']:
                print("  - Subdomain takeover check completed")
            if scan_status['nuclei_output_param'] or scan_status['nuclei_output_js']:
                print("  - Nuclei scanning (DAST/Exposure) completed")
            if scan_status['param_output'] or scan_status['js_output']:
                print("  - URL separation (parameters/JS) completed")
            if scan_status['crawled_filtered_output']:
                print("  - Crawling filtering completed")
            if scan_status['katana_output'] or scan_status['gau_output'] or scan_status['wayback_output']:
                print("  - Crawling (Katana/GAU/Wayback) completed")
            if scan_status['nuclei_output']:
                print("  - Initial nuclei scanning completed")
            if scan_status['active_file']:
                print("  - Active subdomain validation completed")
            if scan_status['subdomain_file']:
                print("  - Subdomain discovery completed")
        else:
            print("[❌] Invalid choice. Please enter 'c' to continue, 'r' to restart, or 'd' for details.")

OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
OUTPUT_FOLDER_NUCLEI = "nuclei"
OUTPUT_FOLDER_CRAWLED = "crawled"
OUTPUT_FOLDER_SENSITIVE_DATA = "sensitive_data"
OUTPUT_FOLDER_GREP = "crawled_filtered"
OUTPUT_FOLDER_TAKEOVER = "take_over"
os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_GREP, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_CRAWLED, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SENSITIVE_DATA, exist_ok=True)
LOCAL_VERSION = "1.4"
def get_status_version():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            decoded = response.text.strip()
            if decoded == LOCAL_VERSION:
                return f"{LOCAL_VERSION} (\033[92mupdated\033[0m)"
            else:
                return f"{LOCAL_VERSION} (\033[91moutdate\033[0m)"
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
        print("5. Setup Resume Scan Mode")
        print("6. Setup All")
        print("7. Back to main menu")
        select = input("Select (1-7): ").strip()
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
                    write_config({"KATANA_LIMIT": -1})
                    print("[✓] Katana set to unlimited mode (limit set to -1).")
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
                    updates["KATANA_LIMIT"] = -1
                else:
                    updates["KATANA_LIMIT"] = int(limit_val)
            if updates:
                write_config(updates)
            else:
                print("[ℹ️] No changes made.")
        elif select == "6":
            return
        elif select == "5":
            current_mode = getattr(config, 'RESUME_SCAN_MODE', 'ask')
            print(f"Current resume scan mode: {current_mode}")
            print("Select resume scan mode:")
            print("1. Ask every time (ask)")
            print("2. Auto continue (continue)")
            print("3. Auto restart (restart)")
            while True:
                choice = input(f"Resume scan mode (current: '{current_mode}'): ").strip()
                if choice == "1":
                    write_config({"RESUME_SCAN_MODE": "ask"})
                    break
                elif choice == "2":
                    write_config({"RESUME_SCAN_MODE": "continue"})
                    break
                elif choice == "3":
                    write_config({"RESUME_SCAN_MODE": "restart"})
                    break
                else:
                    print("[!] Invalid choice; use 1/2/3.")
        elif select == "6":
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
                    updates["KATANA_LIMIT"] = -1
                else:
                    updates["KATANA_LIMIT"] = int(limit_val)

            current_mode = getattr(config, 'RESUME_SCAN_MODE', 'ask')
            print(f"Current resume scan mode: {current_mode}")
            print("Select resume scan mode:")
            print("1. Ask every time (ask)")
            print("2. Auto continue (continue)")
            print("3. Auto restart (restart)")
            print("4. Skip (enter=skip)")
            mode_choice = input("Enter choice (1-4) or enter=skip: ").strip()
            if mode_choice == "1":
                updates["RESUME_SCAN_MODE"] = "ask"
            elif mode_choice == "2":
                updates["RESUME_SCAN_MODE"] = "continue"
            elif mode_choice == "3":
                updates["RESUME_SCAN_MODE"] = "restart"

            if updates:
                write_config(updates)
            else:
                print("[ℹ️] No changes made.")
        elif select == "7":
            return
        else:
            print("[❌] Invalid choice.")

def run_with_animation(message, func, *args, **kwargs):
    console.print(f"[bright_blue][+] {message}...[/bright_blue]")
    result = func(*args, **kwargs)
    if isinstance(result, subprocess.Popen):
        with Status(f"[bold bright_blue]Running {message}[/bold bright_blue]", console=console) as status:
            for line in iter(result.stdout.readline, ''):
                if line:
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
        nonlocal spinner_index
        spinner = spinner_frames[spinner_index]
        base_text = Text(f"{spinner} {message}...", style="bright_blue")

        if count > 0:
            found_text = Text()
            found_text.append(" Found ", style="bright_blue")
            found_text.append(str(count), style="yellow")
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

        if output_file and os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding="utf-8", errors="ignore") as f:
                    count = len([line for line in f if line.strip()])
            except:
                pass

    final_text = Text()
    final_text.append("[✓] ", style="yellow")
    final_text.append(tool_name, style="bright_blue")
    final_text.append(" Found ", style="bright_blue")
    final_text.append(str(count), style="yellow")
    final_text.append(f" {label}", style="bright_blue")
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
   - Crawling URLs using gau to collect URLs with sensitive extensions.
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
    importlib.reload(config)
    print("[✓] config.py updated and reloaded.")

CMD_LINE_SPEED = None

def get_speed():
    if CMD_LINE_SPEED:
        return CMD_LINE_SPEED
    s = getattr(config, "SCAN_SPEED", None)
    if not s:
        return "standard"  
    s = s.lower()
    return s if s in SPEED_ARGS else "standard"  

def get_tool_args(tool_name: str):
    """
    tool_name: "nuclei" | "httpx" | "httpx_sensitive" | "katana" | "gau"
    -> returns list args according to config.SCAN_SPEED if exists, else None
    """
    s = get_speed()
    if not s:
        return None
    return SPEED_ARGS[s].get(tool_name)


def ask_scan_speed():
    speed = get_speed()
    if speed:
        print(f"[ℹ️] Scan speed ->{speed}")
        return SPEED_ARGS[speed]["nuclei"]
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
    domain = domain.split(':')[0]
    return domain

def is_subdomain_of_base_domain(domain, base_domain):
    """Check if domain is subdomain of base_domain"""
    domain = domain.lower()
    base_domain = base_domain.lower()
    if domain == base_domain:
        return True
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
        if line.startswith(('http://', 'https://')):
            domain = extract_domain_from_url(line)
        else:
            domain = line
        if is_subdomain_of_base_domain(domain, base_domain):
            filtered_lines.append(line)
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in filtered_lines:
            f.write(line + '\n')
    return len(filtered_lines)

def filter_subdomains_from_file(input_file, base_domain, output_file):
    """Filter subdomains file to only include those from the base domain"""
    return filter_domains_from_base_domain(input_file, base_domain, output_file)
def find_sensitive_data(target):
    speed = get_speed()
    print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")

    print(f"\n\033[94m[▶] Starting process for {target} (SENSITIVE DATA)\033[0m")

    gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau_{target}.txt")
    crawling_gau(gau_output, target)
    gau_filtered = gau_output + ".tmp"
    import shutil
    shutil.copy(gau_output, gau_filtered)
    filter_domains_from_base_domain(gau_filtered, target, gau_output)
    os.remove(gau_filtered)
    check_sensitive_urls(target, gau_output)

def check_sensitive_urls(target, input_file):
    httpx_args = ["-silent", "-sc", "-nc", "-mc", "200,403", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
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
            if os.path.exists(filtered_input_file):
                os.remove(filtered_input_file)
            return []

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

        sensitive_exts = [
            ".zip", ".tar", ".gz", ".7z", ".rar",
            ".bak", ".backup", ".old",
            ".sql", ".db", ".sqlite",
            ".env", ".log",
            ".conf", ".config", ".ini", ".cfg",
            ".xml", ".json", ".js"
        ]

        urls_200 = []
        urls_403 = []

        if os.path.exists(sen_file):
            with open(sen_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        url_parts = line.split()
                        if url_parts:
                            url = url_parts[0]

                            if '[403]' in line:
                                urls_403.append((url, url))  
                            elif '[200]' in line:
                                urls_200.append((url, url))

        sensitive_urls = [url_tuple[0] for url_tuple in urls_200 + urls_403]

        if os.path.exists(filtered_input_file):
            os.remove(filtered_input_file)

        sen_200_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"200_sens_{target}.txt")
        with open(sen_200_file, "w", encoding="utf-8") as f:
            for ext in sensitive_exts:
                ext_urls = [url for url, _ in urls_200 if ext in url or url.endswith(ext)]
                if ext_urls:
                    f.write(f"{ext.upper()} URLs 200 OK:\n")
                    for url in ext_urls:
                        f.write(url + "\n")
                    f.write("\n")  

        sen_403_file = os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"403_sens_{target}.txt")
        with open(sen_403_file, "w", encoding="utf-8") as f:
            for ext in sensitive_exts:
                ext_urls = [url for url, _ in urls_403 if ext in url or url.endswith(ext)]
                if ext_urls:
                    f.write(f"{ext.upper()} URLs 403 Forbidden:\n")
                    for url in ext_urls:
                        f.write(url + "\n")
                    f.write("\n")  

        if os.path.getsize(sen_200_file) > 0:  
            send_telegram_report(sen_200_file, f"{target} (200 OK - Sensitive URLs)")
        if os.path.getsize(sen_403_file) > 0:  
            send_telegram_report(sen_403_file, f"{target} (403 Forbidden - Sensitive URLs)")

        return sensitive_urls
    except subprocess.CalledProcessError as e:
        print("[!] Failed running Httpx")
        print(e)
        log_error(target, "Httpx sensitive data", str(e))
        if os.path.exists(filtered_input_file):
            os.remove(filtered_input_file)
        return []




def log_error(target, process, error_message, error_log_file="error.log"):
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
    filter_subdomains_from_file(temp_subdomain_file, target, subdomain_file)
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
    subdomain_set = set()
    if os.path.exists(subdomain_file):
        with open(subdomain_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                sub = line.strip()
                if sub:
                    subdomain_set.add(sub)
    target_clean = target.split("://")[-1].split("/")[0].split(":")[0]
    subdomain_set.add(target_clean)
    with open(subdomain_file, "w", encoding="utf-8") as f:
        for sub in sorted(subdomain_set):
            f.write(sub + "\n")        
    with open(subdomain_file, "w") as f:
        f.write("\n".join(sorted(all_subs)))
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(all_subs)}\033[94m subdomains\033[0m")

def active_check(active_file, subdomain_file, url, target):
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
            cmd = f"cat {active_file} | waybackurls"
            return subprocess.Popen(
                cmd,
                shell=True,
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
    importlib.reload(config)
    limit = getattr(config, "KATANA_LIMIT", 20)
    if limit == 0:
        print(f"\033[94m[ℹ️] Katana limit set to 0, skipping crawling process with Katana for {target}\033[0m")
        with open(katana_output, "w") as f:
            f.write("")
        return
    elif limit == -1:
        input_for_katana = input_file
    else:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            alive_subs = [line.strip() for line in f if line.strip()]

        if len(alive_subs) >= limit:
            limited_file = os.path.join(os.path.dirname(input_file), f"{limit}active_{target}.txt")
            with open(limited_file, "w") as f:
                for sub in alive_subs[:limit]:
                    f.write(sub + "\n")
            input_for_katana = limited_file
        else:
            input_for_katana = input_file

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
    import re
    target_match = re.search(r'crawled_filtered_(.*)\.txt', os.path.basename(crawled_filtered_output))
    if target_match:
        actual_target = target_match.group(1)
    else:
        actual_target = target
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
    if os.path.exists(filtered_crawled_file):
        os.remove(filtered_crawled_file)
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(param_urls)}\033[94m URLs with parameter\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[33m{len(js_urls)}\033[94m URLs .js\033[0m")

def process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output):
    crawling_wayback(wayback_output, active_file, target)
    crawling_gau(gau_output, target)
    with open(active_file, "r", encoding="utf-8", errors="ignore") as f:
        alive_subs = [line.strip() for line in f if line.strip()]
    importlib.reload(config)
    limit = getattr(config, "KATANA_LIMIT", 20)

    if limit == -1:
        print(f"\033[94m[+] Unlimited mode enabled, using all active subdomains for Katana scan\033[0m")
        input_for_katana = active_file
    elif len(alive_subs) >= limit:
        limited_file = os.path.join(os.path.dirname(active_file), f"{limit}active_{target}.txt")
        with open(limited_file, "w") as f:
            for sub in alive_subs[:limit]:
                f.write(sub + "\n")
        print(f"\033[94m[+] Active subdomains ≥ {limit}, only using {limit} active subdomains\033[0m")
        input_for_katana = limited_file
    else:
        print(f"\033[94m[+] Active subdomains < {limit}, directly use entire file for Katana scan\033[0m")
        input_for_katana = active_file
    crawling_katana(katana_output, input_for_katana, target)
    wayback_filtered = wayback_output + ".tmp"
    gau_filtered = gau_output + ".tmp"
    katana_filtered = katana_output + ".tmp"
    import shutil
    shutil.copy(wayback_output, wayback_filtered)
    shutil.copy(gau_output, gau_filtered)
    shutil.copy(katana_output, katana_filtered)
    filter_domains_from_base_domain(wayback_filtered, target, wayback_output)
    filter_domains_from_base_domain(gau_filtered, target, gau_output)
    filter_domains_from_base_domain(katana_filtered, target, katana_output)
    os.remove(wayback_filtered)
    os.remove(gau_filtered)
    os.remove(katana_filtered)
    combine_crawling_results(wayback_output, gau_output, katana_output, crawled_filtered_output, target)

def send_telegram_report(file_path, domain, max_len=4000):
    importlib.reload(config)
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
        print("[ℹ️] Bot token or chat_id not found / invalid. Skipping Telegram sending.")
        return
    if not os.path.exists(file_path):
        print(f"[⚠️] Report file {file_path} not found.")
        return
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
        if not lines:
            lines = [f"[❌] No vulnerabilities found for {domain}.\n"]
        header = f"[Report for {domain}]\n\n"
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
        for i, message in enumerate(chunks):
            response = requests.post(url, data={
                'chat_id': config.CHAT_ID,
                'text': message
            })
            if response.status_code == 200:
                print(f"[✓] Part {i+1} report {domain} successfully sent.")
            else:
                print(f"[❌] Failed to send part {i+1} report {domain}: {response.text}")
                break
    except Exception as e:
        print(f"[⚠️] Error occurred while sending to Telegram: {e}")

def send_file_telegram(file_path, domain):
    """Send scan result file to Telegram (sendDocument)."""
    importlib.reload(config)
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
        print("[ℹ️] Bot token or chat_id not found / invalid. Skipping Telegram sending.")
        return 
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument"
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
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
    send_telegram_report(output_file, f"{target} Nuclei (JS File)")            

def nuclei_param_dast(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_dast_mode():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-nh", "-dast", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        run_with_animation("Nuclei (DAST MODE)", nuclei_dast_mode)
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Nuclei (DAST Mode)")
            print(e)
            log_error(target, "Nuclei (DAST Mode)", str(e))
            return            
    send_telegram_report(output_file, f"{target} Nuclei (DAST Mode)")            

def nuclei_takeover(subdomain_file, output_path_takeover, target):
    scan_args = get_tool_args("nuclei")  
    cmd = ["nuclei", "-l", subdomain_file, "-nh", "-tags", "takeover", "-o", output_path_takeover]
    if scan_args:
        cmd.extend(scan_args)

    try:
        def nuclei_takeover_scan():
            return subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
        run_with_animation("Nuclei (Takeover Wildcard)", nuclei_takeover_scan)
    except subprocess.CalledProcessError as e:
            print("[!] Failed to run Nuclei (Takeover Wildcard)")
            print(e)
            log_error(target, "Nuclei (Takeover Wildcard)", str(e))
            return
    send_telegram_report(output_path_takeover, f"({target}) Nuclei (Takeover Wildcard)")

def takeover_mass_file(file_path, output_name=None):
    """Perform takeover check on a list of subdomains from a file"""
    if not os.path.isfile(file_path):
        print(f"[❌] File {file_path} not found.")
        return

    if not output_name:
        output_name = os.path.basename(file_path).replace('.txt', '').replace('.', '_')

    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_name}.txt")

    speed = get_speed()
    print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")

    print(f"\n\033[94m[▶] Starting process for file {file_path} (TAKEOVER MASSAL)\033[0m")

    scan_args = get_tool_args("nuclei")  
    cmd = ["nuclei", "-l", file_path, "-nh", "-tags", "takeover", "-o", output_path]
    if scan_args:
        cmd.extend(scan_args)

    def run_nuc_takeover():
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

    run_with_animation(f"Nuclei (Takeover Mass - {output_name})", run_nuc_takeover)
    send_telegram_report(output_path, f"({output_name}) Nuclei (Takeover Mass)")

def takeover_single(target):
    """Perform takeover check on a single target"""
    input_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
    output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")

    speed = get_speed()
    print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")

    print(f"\n\033[94m[▶] Starting process for {target} (TAKEOVER)\033[0m")

    finding_subdomain(target, input_file)

    scan_args = get_tool_args("nuclei")  
    cmd = ["nuclei", "-l", input_file, "-nh", "-tags", "takeover", "-o", output_path]
    if scan_args:
        cmd.extend(scan_args)

    def run_nuc_takeover():
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

    run_with_animation(f"Nuclei (Takeover Single - {target})", run_nuc_takeover)
    send_telegram_report(output_path, f"({target}) Nuclei (Takeover Single)")

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
    speed = get_speed()
    print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")

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
        print(f"\n[▶] Starting process for file {file_name} (TAKEOVER MASSAL)")
        label = f"Takeover Mass ({output_name})"
    else:
        target = get_target_input()
        input_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
        print(f"\n[▶] Starting process for {target} (TAKEOVER WILDCARD)")
        finding_subdomain(target, input_file)
        label = f"Takeover Wildcard ({target})"
    scan_args = get_tool_args("nuclei")  
    cmd = ["nuclei", "-l", input_file, "-nh", "-tags", "takeover", "-o", output_path]
    if scan_args:
        cmd.extend(scan_args)

    def run_nuc_takeover():
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
    run_with_animation(f"Nuclei {label}", run_nuc_takeover)
    send_telegram_report(output_path, label)    


def light_scan_target(target, resume=False):
        scan_args = ask_scan_speed()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")

        if resume:
            print(f"\n\033[94m[▶] Resuming process for {target} (LIGHTSCAN)\033[0m")
            if os.path.exists(nuclei_output_httpx):
                nuclei_count = sum(1 for line in open(nuclei_output_httpx, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{nuclei_count}\033[94m Subdomain active\033[0m")
                print(f"[ℹ️] Nuclei scan already completed, scan finished")
            elif os.path.exists(active_file):
                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")
                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scan\033[0m")
                user_agent = random.choice(USER_AGENTS)
                start_time_nuclei_scan = time.time()
                nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            elif os.path.exists(subdomain_file):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip())

                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting active validation\033[0m")
                user_agent = random.choice(USER_AGENTS)
                active_check(active_file, subdomain_file, "Subdomain", target)

                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                start_time_nuclei_scan = time.time()
                nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            else:
                print(f"\n\033[94m[▶] Starting process for {target} (LIGHTSCAN)\033[0m")
                start_time_url = time.time()
                finding_subdomain(target, subdomain_file)
                active_check(active_file, subdomain_file, "Subdomain", target)
                user_agent = random.choice(USER_AGENTS)
                start_time_nuclei_scan = time.time()
                nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
        else:
            print(f"\n[▶] Starting process for {target} (LIGHTSCAN)")
            start_time_url = time.time()
            finding_subdomain(target, subdomain_file)
            active_check(active_file, subdomain_file, "Subdomain", target)
            user_agent = random.choice(USER_AGENTS)
            start_time_nuclei_scan = time.time()
            nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
            end_time_nuclei_scan = time.time()
            scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
            hours, remaining = divmod(int(scan_duration), 3600)
            minutes, seconds = divmod(remaining, 60)
            print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")

        print(f"[✓] All processes completed for target: {target}")

def light_scan():
        target = get_target_input()
        scan_args = ask_scan_speed()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        print(f"\n[▶] Starting process for {target} (LIGHTSCAN)")
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
def dark_deep_target(mode, target, resume=False):
        scan_args = ask_scan_speed()
        subdomain_file = os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt")
        active_file = os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt")
        nuclei_output_httpx = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt")
        katana_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"katana_{target}.txt")
        wayback_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"wayback_{target}.txt")
        gau_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau_{target}.txt")
        crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
        temp_crawled_filtered_output = os.path.join (OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        param_output = os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt")
        js_output = os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt")
        nuclei_output_js = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt")
        nuclei_output_param = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt")
        output_path_takeover = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
        scan_type = "DARKSCAN" if mode == "dark" else "DEEPSCAN"

        speed = get_speed()
        print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")

        if resume:
            print(f"\n\033[94m[▶] Resuming process for {target} ({scan_type})\033[0m")
            if os.path.exists(output_path_takeover if mode == "deep" else nuclei_output_param) and os.path.exists(nuclei_output_js):
                print(f"[ℹ️] All nuclei scans already completed, scan finished")
            elif os.path.exists(param_output) and os.path.exists(js_output):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(subdomain_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")

                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(active_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                wayback_count = sum(1 for line in open(wayback_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(wayback_output) else 0
                gau_count = sum(1 for line in open(gau_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(gau_output) else 0
                katana_count = sum(1 for line in open(katana_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(katana_output) else 0

                if wayback_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mWaybackurls Found \033[93m{wayback_count}\033[94m URLs\033[0m")
                if gau_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mGau Found \033[93m{gau_count}\033[94m URLs\033[0m")
                if katana_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mKatana Found \033[93m{katana_count}\033[94m URLs\033[0m")

                limit = getattr(config, "KATANA_LIMIT", 20)
                if limit == -1:
                    print(f"\033[94m[+]\033[0m \033[94mUnlimited mode enabled, using all active subdomains for Katana scan\033[0m")
                elif limit == 0:
                    print(f"\033[94m[ℹ️]\033[0m \033[94mKatana limit set to 0, skipping crawling process with Katana for {target}\033[0m")

                crawled_count = sum(1 for line in open(crawled_filtered_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(crawled_filtered_output) else 0
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{crawled_count}\033[94m URL active\033[0m")

                param_count = sum(1 for line in open(param_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                js_count = sum(1 for line in open(js_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{param_count}\033[94m URLs with parameter\033[0m")
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{js_count}\033[94m URLs .js\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scans\033[0m")
                start_time_nuclei_scan = time.time()
                if mode == "dark":
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                elif mode == "deep":
                    nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            elif os.path.exists(crawled_filtered_output):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(subdomain_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")

                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(active_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                wayback_count = sum(1 for line in open(wayback_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(wayback_output) else 0
                gau_count = sum(1 for line in open(gau_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(gau_output) else 0
                katana_count = sum(1 for line in open(katana_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(katana_output) else 0

                if wayback_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mWaybackurls Found \033[93m{wayback_count}\033[94m URLs\033[0m")
                if gau_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mGau Found \033[93m{gau_count}\033[94m URLs\033[0m")
                if katana_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mKatana Found \033[93m{katana_count}\033[94m URLs\033[0m")

                limit = getattr(config, "KATANA_LIMIT", 20)
                if limit == -1:
                    print(f"\033[94m[+]\033[0m \033[94mUnlimited mode enabled, using all active subdomains for Katana scan\033[0m")
                elif limit == 0:
                    print(f"\033[94m[ℹ️]\033[0m \033[94mKatana limit set to 0, skipping crawling process with Katana for {target}\033[0m")

                crawled_count = sum(1 for line in open(crawled_filtered_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{crawled_count}\033[94m URL active\033[0m")

                separate_urls(crawled_filtered_output, param_output, js_output, target)
                param_count = sum(1 for line in open(param_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                js_count = sum(1 for line in open(js_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{param_count}\033[94m URLs with parameter\033[0m")
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{js_count}\033[94m URLs .js\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scans\033[0m")
                start_time_nuclei_scan = time.time()
                if mode == "dark":
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                elif mode == "deep":
                    nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            elif os.path.exists(katana_output) or os.path.exists(gau_output) or os.path.exists(wayback_output):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(subdomain_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")

                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(active_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                wayback_count = sum(1 for line in open(wayback_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(wayback_output) else 0
                gau_count = sum(1 for line in open(gau_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(gau_output) else 0
                katana_count = sum(1 for line in open(katana_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(katana_output) else 0

                if wayback_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mWaybackurls Found \033[93m{wayback_count}\033[94m URLs\033[0m")
                if gau_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mGau Found \033[93m{gau_count}\033[94m URLs\033[0m")
                if katana_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mKatana Found \033[93m{katana_count}\033[94m URLs\033[0m")

                limit = getattr(config, "KATANA_LIMIT", 20)
                if limit == -1:
                    print(f"\033[94m[+]\033[0m \033[94mUnlimited mode enabled, using all active subdomains for Katana scan\033[0m")
                elif limit == 0:
                    print(f"\033[94m[ℹ️]\033[0m \033[94mKatana limit set to 0, skipping crawling process with Katana for {target}\033[0m")

                active_check(temp_crawled_filtered_output, crawled_filtered_output, "URL", target)
                shutil.move(temp_crawled_filtered_output, crawled_filtered_output)

                total_crawled = sum(1 for line in open(crawled_filtered_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{total_crawled}\033[94m URL active\033[0m")

                separate_urls(crawled_filtered_output, param_output, js_output, target)
                param_count = sum(1 for line in open(param_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                js_count = sum(1 for line in open(js_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{param_count}\033[94m URLs with parameter\033[0m")
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{js_count}\033[94m URLs .js\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scans\033[0m")

                start_time_nuclei_scan = time.time()
                if mode == "dark":
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                elif mode == "deep":
                    nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            elif os.path.exists(active_file):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(subdomain_file) else 0
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")

                active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting crawling\033[0m")
                process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)

                wayback_count = sum(1 for line in open(wayback_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(wayback_output) else 0
                gau_count = sum(1 for line in open(gau_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(gau_output) else 0
                katana_count = sum(1 for line in open(katana_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(katana_output) else 0

                if wayback_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mWaybackurls Found \033[93m{wayback_count}\033[94m URLs\033[0m")
                if gau_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mGau Found \033[93m{gau_count}\033[94m URLs\033[0m")
                if katana_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mKatana Found \033[93m{katana_count}\033[94m URLs\033[0m")

                limit = getattr(config, "KATANA_LIMIT", 20)
                if limit == -1:
                    print(f"\033[94m[+]\033[0m \033[94mUnlimited mode enabled, using all active subdomains for Katana scan\033[0m")
                elif limit == 0:
                    print(f"\033[94m[ℹ️]\033[0m \033[94mKatana limit set to 0, skipping crawling process with Katana for {target}\033[0m")

                total_crawled = sum(1 for line in open(crawled_filtered_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{total_crawled}\033[94m URL active\033[0m")

                separate_urls(crawled_filtered_output, param_output, js_output, target)
                param_count = sum(1 for line in open(param_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                js_count = sum(1 for line in open(js_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{param_count}\033[94m URLs with parameter\033[0m")
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{js_count}\033[94m URLs .js\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scans\033[0m")
                start_time_nuclei_scan = time.time()
                if mode == "dark":
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                elif mode == "deep":
                    nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            elif os.path.exists(subdomain_file):
                total_count = sum(1 for line in open(subdomain_file, 'r', encoding='utf-8', errors='ignore') if line.strip())
                active_count = 0
                if os.path.exists(active_file):
                    active_count = sum(1 for line in open(active_file, 'r', encoding='utf-8', errors='ignore') if line.strip())

                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{total_count}\033[94m subdomains\033[0m")
                if active_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{active_count}\033[94m Subdomain active\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting active validation and crawling\033[0m")
                active_check(active_file, subdomain_file, "Subdomain", target)

                process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)

                wayback_count = sum(1 for line in open(wayback_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(wayback_output) else 0
                gau_count = sum(1 for line in open(gau_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(gau_output) else 0
                katana_count = sum(1 for line in open(katana_output, 'r', encoding='utf-8', errors='ignore') if line.strip()) if os.path.exists(katana_output) else 0

                if wayback_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mWaybackurls Found \033[93m{wayback_count}\033[94m URLs\033[0m")
                if gau_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mGau Found \033[93m{gau_count}\033[94m URLs\033[0m")
                if katana_count > 0:
                    print(f"\033[93m[✓]\033[0m \033[94mKatana Found \033[93m{katana_count}\033[94m URLs\033[0m")

                limit = getattr(config, "KATANA_LIMIT", 20)
                if limit == -1:
                    print(f"\033[94m[+]\033[0m \033[94mUnlimited mode enabled, using all active subdomains for Katana scan\033[0m")
                elif limit == 0:
                    print(f"\033[94m[ℹ️]\033[0m \033[94mKatana limit set to 0, skipping crawling process with Katana for {target}\033[0m")

                total_crawled = sum(1 for line in open(crawled_filtered_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mHttpx Found \033[93m{total_crawled}\033[94m URL active\033[0m")

                separate_urls(crawled_filtered_output, param_output, js_output, target)
                param_count = sum(1 for line in open(param_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                js_count = sum(1 for line in open(js_output, 'r', encoding='utf-8', errors='ignore') if line.strip())
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{param_count}\033[94m URLs with parameter\033[0m")
                print(f"\033[93m[✓]\033[0m \033[94mSuccessfully found \033[93m{js_count}\033[94m URLs .js\033[0m")

                print(f"\033[94m[+]\033[0m \033[94mStarting nuclei scans\033[0m")
                start_time_nuclei_scan = time.time()
                if mode == "dark":
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                elif mode == "deep":
                    nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                    nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
                    nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
            else:
                print(f"\n\033[94m[▶] Starting process for {target} ({scan_type})\033[0m")
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
                    nuclei_takeover(subdomain_file, output_path_takeover, target)
                else:
                    print(f"[!] Unknown scan mode: {mode}")
                    return
                end_time_nuclei_scan = time.time()
                scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
                hours, remaining = divmod(int(scan_duration), 3600)
                minutes, seconds = divmod(remaining, 60)
                print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
        else:
            print(f"\n[▶] Starting process for {target} ({scan_type})")
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
                nuclei_takeover(subdomain_file, output_path_takeover, target)
            else:
                print(f"[!] Unknown scan mode: {mode}")
                return
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
        crawled_filtered_output = os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt")
        temp_crawled_filtered_output = os.path.join (OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt")
        user_agent = random.choice(USER_AGENTS)
        param_output = os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt")
        js_output = os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt")
        nuclei_output_js = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt")
        nuclei_output_param = os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt")
        output_path_takeover = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt")
        scan_type = "DARKSCAN" if mode == "dark" else "DEEPSCAN"
        print(f"\n[▶] Starting process for {target} ({scan_type})")
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
            nuclei_takeover(subdomain_file, output_path_takeover, target)
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
    parser = argparse.ArgumentParser(description='LAZYHUNTER - Automation Recon Tool')
    parser.add_argument('--lightscan', '-lts', action='store_true', help='Run Light Scan')
    parser.add_argument('--darkscan', '-dks', action='store_true', help='Run Dark Scan')
    parser.add_argument('--deepscan', '-dps', action='store_true', help='Run Deep Scan')
    parser.add_argument('--takeover', '-tov', action='store_true', help='Run Subdomain Takeover Check')
    parser.add_argument('--sensitive', '-sens', action='store_true', help='Find Sensitive Data')
    parser.add_argument('-t', '--target', type=str, help='Target domain for scanning')
    parser.add_argument('-list', '-l', type=str, help='File containing list of subdomains for takeover check')
    parser.add_argument('-speed', '-s', type=str, help='Scanning speed: low/standard/fast or 1/2/3')
    parser.add_argument('-ac', '--auto-continue', action='store_true', help='Auto continue previous scan if exists')
    parser.add_argument('-ar', '--auto-restart', action='store_true', help='Auto restart scan even if previous files exist')

    args = parser.parse_args()

    print_logo()

    if any([args.lightscan, args.darkscan, args.deepscan, args.takeover, args.sensitive]):
        if args.takeover and args.list:
            pass
        elif not args.target:
            print("[❌] Target is required when using scan options. Use -t or --target to specify target.")
            sys.exit(1)

        speed_map = {'1': 'low', '2': 'standard', '3': 'fast'}
        speed_value = args.speed
        if speed_value in speed_map:
            speed_value = speed_map[speed_value]

        if speed_value:
            if speed_value not in ['low', 'standard', 'fast']:
                print("[❌] Invalid speed value. Use low/standard/fast or 1/2/3.")
                sys.exit(1)
            CMD_LINE_SPEED = speed_value

        resume_action = None
        if args.target and not args.auto_continue and not args.auto_restart:
            scan_status = check_previous_scan(args.target)
            if scan_status['has_any_files']:
                resume_mode = getattr(config, 'RESUME_SCAN_MODE', 'ask')
                if resume_mode == 'ask':
                    resume_action = ask_continue_or_restart(args.target, scan_status)
                elif resume_mode == 'continue':
                    resume_action = 'continue'
                elif resume_mode == 'restart':
                    resume_action = 'restart'
        elif args.auto_continue:
            resume_action = 'continue'
        elif args.auto_restart:
            resume_action = 'restart'

        if args.lightscan:
            if resume_action == 'restart' or not resume_action:
                light_scan_target(args.target, resume=False)
            elif resume_action == 'continue':
                light_scan_target(args.target, resume=True)
        elif args.darkscan or args.deepscan:
            mode = "dark" if args.darkscan else "deep"
            if resume_action == 'restart' or not resume_action:
                dark_deep_target(mode, args.target, resume=False)
            elif resume_action == 'continue':
                dark_deep_target(mode, args.target, resume=True)
        elif args.takeover:
            if args.list:
                output_name = args.target if args.target else None
                takeover_mass_file(args.list, output_name)
            else:
                takeover_single(args.target)
        elif args.sensitive:
            find_sensitive_data(args.target)
    else:
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
