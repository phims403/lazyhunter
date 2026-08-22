import os
import subprocess
import shutil
import requests
import tempfile
import random
import time
import sys
import datetime
import threading
import select
from urllib.parse import urlparse, parse_qs, unquote
import config
import re
import importlib
import argparse

from rich.console import Console
from rich.status import Status
from rich.live import Live
from rich.text import Text
console = Console()

# Import toleran: config lama mungkin belum punya setting baru.
# Fallback dipakai supaya tool tetap bisa jalan & setting ditambahkan otomatis.
try:
    from config import GITHUB_USER, GITHUB_REPO, BOT_TOKEN, CHAT_ID, KATANA_LIMIT
except ImportError:
    import config as _cfg
    GITHUB_USER = getattr(_cfg, "GITHUB_USER", "phims403")
    GITHUB_REPO = getattr(_cfg, "GITHUB_REPO", "lazyhunter")
    BOT_TOKEN = getattr(_cfg, "BOT_TOKEN", "")
    CHAT_ID = getattr(_cfg, "CHAT_ID", "")
    KATANA_LIMIT = getattr(_cfg, "KATANA_LIMIT", 5)
def token_valid(token):
    return token.startswith("bot") or (len(token) > 30 and ":" in token)
def chat_id_valid(chat_id):
    return chat_id.lstrip("-").isdigit()

# ============ LOG SYSTEM ============
LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

def get_log_path(target):
    """Get log file path for a specific target."""
    return os.path.join(LOG_FOLDER, f"{target}.txt")

def write_log(target, step, status="completed", info="", count=None):
    """
    Write a log entry for a target's scan step.
    - step: name of the process (e.g., 'subdomain_finding', 'httpx', 'nuclei_basic')
    - status: 'completed', 'error', 'skipped'
    - info: additional info (e.g., error message)
    - count: number of results found (e.g., 150 subdomains)
    """
    log_path = get_log_path(target)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count_str = f" | count={count}" if count is not None else ""
    info_str = f" | info={info}" if info else ""
    log_line = f"[{now}] [{status.upper()}] {step}{count_str}{info_str}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)

def read_log(target):
    """
    Read and parse the log file for a target.
    Returns a dict of {step: {status, count, info, timestamp}} for the LAST entry of each step.
    """
    log_path = get_log_path(target)
    if not os.path.exists(log_path):
        return {}
    log_data = {}
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ts_end = line.index(']') + 1
                timestamp = line[1:ts_end-1]
                rest = line[ts_end:].strip()
                status_end = rest.index(']') + 1
                status = rest[1:status_end-1].lower()
                rest = rest[status_end:].strip()
                parts = rest.split(' | ')
                step = parts[0].strip()
                entry = {'status': status, 'count': None, 'info': '', 'timestamp': timestamp}
                for part in parts[1:]:
                    part = part.strip()
                    if part.startswith('count='):
                        try:
                            entry['count'] = int(part[6:])
                        except ValueError:
                            entry['count'] = part[6:]
                    elif part.startswith('info='):
                        entry['info'] = part[5:]
                log_data[step] = entry
            except (ValueError, IndexError):
                continue
    return log_data

def is_step_completed(target, step):
    """Check if a specific step has been completed for a target."""
    log_data = read_log(target)
    return step in log_data and log_data[step]['status'] == 'completed'

def get_step_info(target, step):
    """Get info about a specific step from the log."""
    log_data = read_log(target)
    return log_data.get(step, None)

def print_log_summary(target):
    """Print a summary of completed steps from the log for a target."""
    log_data = read_log(target)
    if not log_data:
        print(f"\033[94m[ℹ️] No previous scan log found for {target}\033[0m")
        return
    processing = {k: v for k, v in log_data.items() if v['status'] == 'processing'}
    completed = {k: v for k, v in log_data.items() if v['status'] == 'completed'}
    errors = {k: v for k, v in log_data.items() if v['status'] == 'error'}
    if not completed and not errors and not processing:
        print(f"\033[94m[ℹ️] No completed steps found in log for {target}\033[0m")
        return
    print(f"\033[94m[ℹ️] Scan log for {target}:\033[0m")
    if completed:
        for step, info in completed.items():
            count_str = f" ({info['count']} found)" if info['count'] is not None else ""
            print(f"\033[93m  [✓]\033[0m \033[94m{step}{count_str}\033[0m")
    if processing:
        for step, info in processing.items():
            print(f"\033[93m  [▶]\033[0m \033[94m{step} (unfinished)\033[0m")
    if errors:
        for step, info in errors.items():
            print(f"\033[91m  [✗]\033[0m \033[94m{step} - {info.get('info', 'unknown error')}\033[0m")

def clear_target_log(target):
    """Clear the log file for a target (used when restarting a scan)."""
    log_path = get_log_path(target)
    if os.path.exists(log_path):
        os.remove(log_path)

def has_previous_scan(target):
    """Check if there's any previous scan log for a target."""
    log_data = read_log(target)
    completed = {k: v for k, v in log_data.items() if v['status'] == 'completed'}
    return len(completed) > 0

def is_target_completed(target):
    """
    Check if a target has been FULLY scanned for its current mode:
    - Log exists
    - Every step in the log has status 'completed' (no processing/error/skipped)
    - At least one step exists
    Used by the CLI batch mode (-tL) to skip already-complete targets.
    """
    log_data = read_log(target)
    if not log_data:
        return False
    has_completed = False
    for step, info in log_data.items():
        if info["status"] == "completed":
            has_completed = True
        else:
            # Any unfinished or errored step means the scan is not done
            return False
    return has_completed

def ask_continue_or_restart(target, log_data=None):
    """
    Ask user whether to continue previous scan or restart.
    Uses log data to show which steps are already completed.
    """
    if log_data is None:
        log_data = read_log(target)

    completed = {k: v for k, v in log_data.items() if v['status'] == 'completed'}
    errors = {k: v for k, v in log_data.items() if v['status'] == 'error'}

    print(f"\n\033[93m  [⚠️ ] Previous scan log found for target '{target}'\033[0m")
    if completed:
        print(f"\033[94m  Completed steps:\033[0m")
        for step, info in completed.items():
            count_str = f" ({info['count']} found)" if info['count'] is not None else ""
            err_info = f" - {info['info']}" if info.get('info') else ""
            print(f"\033[93m    [✓]\033[0m \033[94m{step}{count_str}{err_info}\033[0m")
    if errors:
        print(f"\033[91m  Steps with errors:\033[0m")
        for step, info in errors.items():
            print(f"\033[91m    [✗]\033[0m \033[94m{step} - {info.get('info', 'unknown error')}\033[0m")

    while True:
        choice = input(f"\n[?] Target '{target}' has been partially scanned. Continue previous scan (c), restart (r), or see details (d)? ").strip().lower()
        if choice in ['c', 'continue']:
            return 'continue'
        elif choice in ['r', 'restart']:
            return 'restart'
        elif choice in ['d', 'details']:
            print_log_summary(target)
        else:
            print("[❌] Invalid choice. Please enter 'c' to continue, 'r' to restart, or 'd' for details.")

# ============ END LOG SYSTEM ============

OUTPUT_FOLDER_SUBDO = "subdomain"
OUTPUT_FOLDER_ACTIVE = "active"
OUTPUT_FOLDER_NUCLEI = "nuclei"
OUTPUT_FOLDER_CRAWLED = "crawled"
OUTPUT_FOLDER_SENSITIVE_DATA = "sensitive_data"
OUTPUT_FOLDER_GREP = "crawled_filtered"
OUTPUT_FOLDER_TAKEOVER = "take_over"
OUTPUT_FOLDER_TARGET = "target_output"

def get_storage_mode():
    """Get current storage mode from config. Options: 'by_type' or 'by_target'"""
    importlib.reload(config)
    mode = getattr(config, "STORAGE_MODE", "by_type")
    if mode not in ("by_type", "by_target"):
        mode = "by_type"
    return mode

def get_output_paths(target):
    """
    Return a dictionary of all output file paths based on current storage mode.
    - by_type: files organized by type folder (subdomain/, active/, nuclei/, etc.)
    - by_target: all files for a target in one folder (target_output/{target}/)
    """
    mode = get_storage_mode()

    if mode == "by_target":
        # All files in target_output/{target}/
        target_folder = os.path.join(OUTPUT_FOLDER_TARGET, target)
        paths = {
            'subdomain_file': os.path.join(target_folder, "subdomains.txt"),
            'active_file': os.path.join(target_folder, "active.txt"),
            'nuclei_output': os.path.join(target_folder, "nuc_active.txt"),
            'wayback_output': os.path.join(target_folder, "wayback.txt"),
            'gau_output': os.path.join(target_folder, "gau.txt"),
            'katana_output': os.path.join(target_folder, "katana.txt"),
            'crawled_filtered_output': os.path.join(target_folder, "crawled_filtered.txt"),
            'temp_crawled_filtered_output': os.path.join(target_folder, "temp_crawled_filtered.txt"),
            'param_output': os.path.join(target_folder, "param.txt"),
            'js_output': os.path.join(target_folder, "js.txt"),
            'nuclei_output_js': os.path.join(target_folder, "nuc_exp.txt"),
            'nuclei_output_param': os.path.join(target_folder, "nuc_dast.txt"),
            'output_path_takeover': os.path.join(target_folder, "takeover.txt"),
            'sen_200_file': os.path.join(target_folder, "200_sens.txt"),
            'sen_403_file': os.path.join(target_folder, "403_sens.txt"),
            'sec_finder_file': os.path.join(target_folder, "sec_finder.txt"),
            'pot_sen_url_file': os.path.join(target_folder, "pot_sen_url.txt"),
            'sen_url_file': os.path.join(target_folder, "sen_url.txt"),
        }
    else:
        # Original: files organized by type folder
        paths = {
            'subdomain_file': os.path.join(OUTPUT_FOLDER_SUBDO, f"{target}.txt"),
            'active_file': os.path.join(OUTPUT_FOLDER_ACTIVE, f"active_{target}.txt"),
            'nuclei_output': os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_active_{target}.txt"),
            'wayback_output': os.path.join(OUTPUT_FOLDER_CRAWLED, f"wayback_{target}.txt"),
            'gau_output': os.path.join(OUTPUT_FOLDER_CRAWLED, f"gau_{target}.txt"),
            'katana_output': os.path.join(OUTPUT_FOLDER_CRAWLED, f"katana_{target}.txt"),
            'crawled_filtered_output': os.path.join(OUTPUT_FOLDER_CRAWLED, f"crawled_filtered_{target}.txt"),
            'temp_crawled_filtered_output': os.path.join(OUTPUT_FOLDER_CRAWLED, f"temp_crawled_filtered_{target}.txt"),
            'param_output': os.path.join(OUTPUT_FOLDER_GREP, f"param_{target}.txt"),
            'js_output': os.path.join(OUTPUT_FOLDER_GREP, f"js_{target}.txt"),
            'nuclei_output_js': os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_exp_{target}.txt"),
            'nuclei_output_param': os.path.join(OUTPUT_FOLDER_NUCLEI, f"nuc_dast_{target}.txt"),
            'output_path_takeover': os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TOW_{target}.txt"),
            'sen_200_file': os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"200_sens_{target}.txt"),
            'sen_403_file': os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"403_sens_{target}.txt"),
            'sec_finder_file': os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sec_finder_{target}.txt"),
            'pot_sen_url_file': os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"pot_sen_url_{target}.txt"),
            'sen_url_file': os.path.join(OUTPUT_FOLDER_SENSITIVE_DATA, f"sen_url_{target}.txt"),
        }

    # Ensure output directories exist
    if mode == "by_target":
        os.makedirs(os.path.join(OUTPUT_FOLDER_TARGET, target), exist_ok=True)
    else:
        os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_GREP, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_CRAWLED, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER_SENSITIVE_DATA, exist_ok=True)

    return paths

os.makedirs(OUTPUT_FOLDER_TAKEOVER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_GREP, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SUBDO, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_ACTIVE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_NUCLEI, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_CRAWLED, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_SENSITIVE_DATA, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_TARGET, exist_ok=True)

LOCAL_VERSION = "1.5"
_VERSION_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".version_cache")
_VERSION_CACHE_TTL = 86400  # 24 jam: cek versi remote hanya sekali sehari

def get_status_version():
    # Pakai cache kalau masih fresh (24 jam) -> startup langsung tanpa network.
    try:
        if os.path.exists(_VERSION_CACHE_FILE):
            with open(_VERSION_CACHE_FILE, "r", encoding="utf-8") as f:
                parts = f.read().strip().split("|")
                if len(parts) == 2:
                    cached_time, cached_ver = float(parts[0]), parts[1]
                    if time.time() - cached_time < _VERSION_CACHE_TTL:
                        if cached_ver == LOCAL_VERSION:
                            return f"{LOCAL_VERSION} (\033[92mupdated\033[0m)"
                        else:
                            return f"{LOCAL_VERSION} (\033[91moutdate\033[0m)"
    except Exception:
        pass
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            decoded = response.text.strip()
            # Simpan cache
            try:
                with open(_VERSION_CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(f"{time.time()}|{decoded}")
            except Exception:
                pass
            if decoded == LOCAL_VERSION:
                return f"{LOCAL_VERSION} (\033[92mupdated\033[0m)"
            else:
                return f"{LOCAL_VERSION} (\033[91moutdate\033[0m)"
        else:
            return f"{LOCAL_VERSION} (\033[93munknown\033[0m)"
    except Exception:
        # Offline / timeout / network error: jangan print debug ke stdout
        # (bisa mengganggu otomasi batch). Cukup tandai offline.
        return f"{LOCAL_VERSION} (\033[93moffline\033[0m)"
def print_logo():
    version_status = get_status_version().ljust(25)
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
    print(f"            LAZYHUNTER v{version_status}    Author : PHIMS")
    print("Instagram  : @phimzz instagram.com/phimzz    GitHub      : phims403 github.com/phims403")
    print("YouTube    : elphims youtube.com/@elphims    Telegram    : @phimssec t.me/phimssec")
    print("LinkedIn   : PHIMS SEC linkedin.com/in/phims-sec-47867330b/")
def check_telegram_config():
    """
    Check whether BOT_TOKEN and CHAT_ID are configured.
    If one or both are missing, ask the user whether to continue without
    Telegram or fix them now (press 'f'). English only.
    """
    importlib.reload(config)
    has_token = token_valid(getattr(config, "BOT_TOKEN", ""))
    has_chat = chat_id_valid(getattr(config, "CHAT_ID", ""))

    if has_token and has_chat:
        return True  # All set, no prompt needed

    missing = []
    if not has_token:
        missing.append("Bot Token")
    if not has_chat:
        missing.append("Chat ID")

    print("\n" + "=" * 60)
    print("  [⚠️ ] Telegram configuration incomplete")
    print("=" * 60)
    print(f"  Missing: {', '.join(missing)}")
    print("  Without this, scan results will NOT be sent to Telegram.")
    print("  To set it up, read 'readme.md' for the BotFather & chat ID guide.")
    print()
    while True:
        choice = input("  Press Enter to continue without Telegram, or 'f' to fix it now: ").strip().lower()
        if choice == "":
            print("[ℹ️] Continuing without Telegram notifications.")
            return False
        elif choice == "f":
            _setup_telegram_missing(has_token, has_chat)
            # Re-check after setup
            importlib.reload(config)
            has_token = token_valid(getattr(config, "BOT_TOKEN", ""))
            has_chat = chat_id_valid(getattr(config, "CHAT_ID", ""))
            if has_token and has_chat:
                print("[✓] Telegram configuration complete.")
                return True
            else:
                # Still missing something -> prompt again
                continue
        else:
            print("[❌] Invalid choice. Press Enter to continue, or 'f' to fix.")

def _setup_telegram_missing(has_token, has_chat):
    """Guide the user through setting only the missing Telegram values."""
    print("\n" + "=" * 60)
    print("  Telegram Setup")
    print("=" * 60)
    print("  How to create a Telegram bot:")
    print("    1. Open Telegram and search for @BotFather")
    print("    2. Send /newbot and follow the steps to get a Bot Token")
    print("    3. Add your bot to a chat/group, then send any message")
    print("    4. Get your Chat ID (e.g. via @userinfobot or getUpdates API)")
    print("  Full guide: see 'readme.md' in this repository")
    print("=" * 60)

    if not has_token:
        print("\n  📌 Bot Token format: `123456789:AA...` (digits, colon, letters)")
        print("     It comes from @BotFather when you create a bot with /newbot.")
        cur = getattr(config, "BOT_TOKEN", "")
        while True:
            val = input(f"\nBot Token (current: '{cur[:6]}...' if any, or empty to skip): ").strip()
            if val == "":
                print("[ℹ️] Bot Token not changed.")
                break
            if token_valid(val):
                write_config({"BOT_TOKEN": val})
                print("[✓] Bot Token saved.")
                break
            else:
                print("[❌] The Bot Token you entered looks INVALID.")
                print("     Expected format: 123456789:AA... (numbers, colon, letters)")
                print("     Please read 'readme.md' to see how to get the correct Bot Token from @BotFather.")
    if not has_chat:
        print("\n  📌 Chat ID format: numeric only, e.g. 123456789 or -1001234567890")
        print("     It is your user/group ID (use @userinfobot or Bot API getUpdates).")
        cur = getattr(config, "CHAT_ID", "")
        while True:
            val = input(f"\nChat ID (current: '{cur}' if any, or empty to skip): ").strip()
            if val == "":
                print("[ℹ️] Chat ID not changed.")
                break
            if chat_id_valid(val):
                write_config({"CHAT_ID": val})
                print("[✓] Chat ID saved.")
                break
            else:
                print("[❌] The Chat ID you entered looks INVALID.")
                print("     Expected format: numeric only (e.g. 123456789 or -1001234567890).")
                print("     Please read 'readme.md' to see how to get the correct Chat ID.")

def display_menu():
    print("\n    Choose Feature:")
    print("  [0]  Feature Information")
    print("  [1]  Light Scan")
    print("  [2]  Dark Scan")
    print("  [3]  Deep Scan (TOP FEATURE)")
    print("  [4]  Subdomain Takeover")
    print("  [5]  Find Sensitive Data")
    print("  [9]  Setup Configuration")
    print("  [99] Out")
    print("  [999] Update Tool")
    print("──────────────────────────────────────────────────────────────────────────────")
    while True:
        choice = input("Choose Feature (0-9, 99, or 999): ").strip()
        if choice in ["0","1","2","3","4","5","9","99","999"]:
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
        print("6. Setup Storage Mode")
        print("7. Setup SecretFinder Mode")
        print("8. Setup All")
        print("9. Back to main menu")
        select = input("Select (1-9): ").strip()
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
            current_storage = getattr(config, 'STORAGE_MODE', 'by_type')
            print(f"Current storage mode: {current_storage}")
            print("Select storage mode:")
            print("1. By Type (by_type) - Each type in separate folder (subdomain/, active/, nuclei/, etc.)")
            print("2. By Target (by_target) - All files in one folder per target (target_output/{target}/)")
            while True:
                choice = input(f"Storage mode (current: '{current_storage}'): ").strip()
                if choice == "1":
                    write_config({"STORAGE_MODE": "by_type"})
                    print("[✓] Storage mode set to 'by_type' - Files will be organized by type in separate folders.")
                    break
                elif choice == "2":
                    write_config({"STORAGE_MODE": "by_target"})
                    print("[✓] Storage mode set to 'by_target' - All files will be saved in target_output/{target}/ folder.")
                    break
                else:
                    print("[!] Invalid choice; use 1/2.")

        elif select == "7":
            current_mode = getattr(config, 'SECRETFINDER_MODE', 'direct')
            print(f"\nSecretFinder Mode (current: {current_mode})")
            print("1. Direct (scan URL directly via SecretFinder)")
            print("2. Local (download JS files to js-saved/ folder for offline scan & further analysis)")
            print("3. Skip (enter=skip)")
            mode_choice = input("Enter choice (1-3) or enter=skip: ").strip()
            if mode_choice == "1":
                write_config({"SECRETFINDER_MODE": "direct"})
                print("[✓] SecretFinder mode set to direct.")
            elif mode_choice == "2":
                write_config({"SECRETFINDER_MODE": "local"})
                print("[✓] SecretFinder mode set to local.")

        elif select == "8":
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

            current_storage = getattr(config, 'STORAGE_MODE', 'by_type')
            print(f"Current storage mode: {current_storage}")
            print("Select storage mode:")
            print("1. By Type (by_type)")
            print("2. By Target (by_target)")
            print("3. Skip (enter=skip)")
            storage_choice = input("Enter choice (1-3) or enter=skip: ").strip()
            if storage_choice == "1":
                updates["STORAGE_MODE"] = "by_type"
            elif storage_choice == "2":
                updates["STORAGE_MODE"] = "by_target"

            current_sf = getattr(config, 'SECRETFINDER_MODE', 'direct')
            print(f"\nSecretFinder Mode (current: {current_sf})")
            print("1. Direct (scan URL directly)")
            print("2. Local (download JS to js-saved/)")
            print("3. Skip (enter=skip)")
            sf_choice = input("Enter choice (1-3) or enter=skip: ").strip()
            if sf_choice == "1":
                updates["SECRETFINDER_MODE"] = "direct"
            elif sf_choice == "2":
                updates["SECRETFINDER_MODE"] = "local"

            if updates:
                write_config(updates)
            else:
                print("[ℹ️] No changes made.")
        elif select == "9":
            return
        else:
            print("[❌] Invalid choice.")

STEP_SKIPPED = False
SKIP_HINT_SHOWN = False
LAST_TOOL_EXIT_CODE = 0  # return code of the last completed subprocess (0=ok). None bila di-skip.

def _skip_pressed():
    """
    Non-blocking check if user pressed 's' (+ Enter) to skip current step.
    Returns True only ONCE per keypress, then drains any remaining buffered
    input (e.g. the '\\n' from Enter) so it does not affect later steps.
    """
    try:
        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key.lower() == 's':
                # Buang sisa karakter (mis. '\\n' dari Enter) supaya tidak
                # terbaca oleh step berikutnya dan menyebabkan skip berantai.
                # Hentikan saat EOF ('' dari pipe yang ditutup) agar tidak
                # infinite loop.
                try:
                    while select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1)
                        if ch == '':
                            break
                except (ValueError, TypeError, OSError):
                    pass
                return True
    except (ValueError, TypeError, OSError):
        pass
    return False

def run_with_animation(message, func, *args, **kwargs):
    global STEP_SKIPPED, SKIP_HINT_SHOWN, LAST_TOOL_EXIT_CODE
    # Reset flag global di awal step: skip hanya berlaku untuk step ini,
    # jangan terbawa ke step berikutnya (nuclei membaca global ini).
    STEP_SKIPPED = False
    if not SKIP_HINT_SHOWN:
        console.print("[bright_blue][+] press 's' + Enter to skip a running step[/bright_blue]")
        SKIP_HINT_SHOWN = True
    result = func(*args, **kwargs)
    skipped = False
    rc = 0
    if isinstance(result, subprocess.Popen):
        with Status(f"[bold bright_blue]Running {message}[/bold bright_blue]", console=console) as status:
            # Baca stdout NON-blocking: cek skip setiap 0.1 detik, jadi tombol
            # 's' langsung responsif meski subprocess tidak mengeluarkan output
            # (nuclei sering diam lama antar baris log).
            buf = ""
            while True:
                if _skip_pressed():
                    result.kill()
                    skipped = True
                    break
                # Cek apakah ada data di stdout pipe (non-blocking)
                try:
                    ready, _, _ = select.select([result.stdout.fileno()], [], [], 0)
                except (ValueError, TypeError, OSError):
                    ready = []
                if ready:
                    try:
                        chunk = os.read(result.stdout.fileno(), 4096)
                    except (ValueError, OSError):
                        break
                    if chunk:
                        buf += chunk.decode(errors="replace")
                        while "\n" in buf:
                            line, buf = buf.split("\n", 1)
                            if line.strip():
                                console.print(line.rstrip(), highlight=False)
                        continue
                # Tidak ada baris baru: cek apakah proses sudah selesai
                if result.poll() is not None:
                    break
                time.sleep(0.1)
            # Output sisa yang belum ada newline
            if buf.strip():
                console.print(buf.rstrip(), highlight=False)
            if not skipped:
                rc = result.wait()
    STEP_SKIPPED = skipped
    LAST_TOOL_EXIT_CODE = rc if not skipped else None
    if skipped:
        console.print(f"[yellow][⚠] {message} skipped by user.[/yellow]")
    else:
        console.print(f"[green][✓] {message} completed.[/green]")
        if rc != 0:
            console.print(f"[yellow][!] {message} exited with code {rc} — results may be incomplete.[/yellow]")
    return rc


def get_target_input_enhanced():
    """
    Enhanced target input - supports single domain or file with domain list.
    Returns a list of targets (always a list, even for single domain).
    """
    print("\n  \033[94m[\033[93m!\033[94m] Target Input Mode:\033[0m")
    print("  \033[94m[1] Single Domain\033[0m")
    print("  \033[94m[2] Domain List File (1 domain per line)\033[0m")
    while True:
        choice = input("  Choose (1/2): ").strip()
        if choice == "1":
            target = input("  Enter target URL (example: example.com): ").strip()
            if target:
                return [target]
            print("  \033[91m[❌] Invalid URL!\033[0m")
        elif choice == "2":
            file_path = input("  Enter file path (example: targets.txt): ").strip()
            if not file_path:
                print("  \033[91m[❌] File path cannot be empty!\033[0m")
                continue
            if not os.path.isfile(file_path):
                print(f"  \033[91m[❌] File '{file_path}' not found!\033[0m")
                continue
            targets = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            targets.append(line)
            except Exception as e:
                print(f"  \033[91m[❌] Error reading file: {e}\033[0m")
                continue
            if not targets:
                print("  \033[91m[❌] File is empty or contains no valid domains!\033[0m")
                continue
            print(f"  \033[33m[✓]\033[94m Loaded \033[93m{len(targets)}\033[94m targets from \033[93m{file_path}\033[0m")
            for i, t in enumerate(targets, 1):
                print(f"    \033[94m{i}.\033[0m {t}")
            return targets
        else:
            print("  \033[91m[❌] Invalid choice. Enter 1 or 2.\033[0m")

def load_targets_from_file(file_path):
    """Load targets from a file (1 domain per line, # comments supported)."""
    targets = []
    if not os.path.isfile(file_path):
        print(f"\033[91m[❌] File '{file_path}' not found!\033[0m")
        return targets
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line)
    except Exception as e:
        print(f"\033[91m[❌] Error reading file: {e}\033[0m")
    return targets

def process_target_list(targets, scan_func, scan_name):
    """
    Process a list of targets sequentially through a scan function.
    scan_func signature: scan_func(target, resume=False)
    """
    total = len(targets)
    if total == 0:
        print("\033[91m[❌] No targets to scan!\033[0m")
        return

    print(f"\n\033[94m{'═' * 60}\033[0m")
    print(f"\033[93m[▶]\033[94m Starting \033[93m{scan_name}\033[94m for \033[93m{total}\033[94m targets\033[0m")
    print(f"\033[94m{'═' * 60}\033[0m")

    for i, target in enumerate(targets, 1):
        print(f"\n\033[94m{'─' * 60}\033[0m")
        print(f"\033[93m[{i}/{total}]\033[94m Processing target: \033[93m{target}\033[0m")
        print(f"\033[94m{'─' * 60}\033[0m")

        # Check for previous scan via log
        resume = False
        if has_previous_scan(target):
            resume_action = ask_continue_or_restart(target)
            if resume_action == 'continue':
                resume = True
            elif resume_action == 'restart':
                clear_target_log(target)

        scan_func(target, resume=resume)

        if i < total:
            print(f"\n\033[94m[ℹ️] Target \033[93m{target}\033[94m completed. Moving to next target...\033[0m")

    print(f"\n\033[94m{'═' * 60}\033[0m")
    print(f"\033[33m[✓]\033[94m All \033[93m{total}\033[94m targets processed for \033[93m{scan_name}\033[0m")
    print(f"\033[94m{'═' * 60}\033[0m")
def run_with_animation_no_output(message, func, tool_name=None, label="Item", output_file=None, *args, **kwargs):
    global STEP_SKIPPED, SKIP_HINT_SHOWN
    # Reset flag global di awal step: skip hanya berlaku untuk step ini,
    # jangan terbawa ke step berikutnya.
    STEP_SKIPPED = False
    if not SKIP_HINT_SHOWN:
        console.print("[bright_blue][+] press 's' + Enter to skip a running step[/bright_blue]")
        SKIP_HINT_SHOWN = True
    if tool_name is None:
        tool_name = message.split("With")[-1].strip() if "With" in message else "Tool"

    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner_index = 0
    count = 0
    skipped = False
    rc = 0  # return code of the subprocess (0 = ok)

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
                if _skip_pressed():
                    result.kill()
                    skipped = True
                    break
                time.sleep(0.1)
                spinner_index = (spinner_index + 1) % len(spinner_frames)
                live.update(get_live_text())

            if not skipped:
                try:
                    with open(output_file, 'r', encoding="utf-8", errors="ignore") as f:
                        while result.poll() is None:
                            if _skip_pressed():
                                result.kill()
                                skipped = True
                                break
                            line = f.readline()
                            if line.strip():
                                count += 1

                            spinner_index = (spinner_index + 1) % len(spinner_frames)
                            live.update(get_live_text())

                            if not line:
                                time.sleep(0.05)

                except Exception as e:
                    live.update(Text(f"[!] Failed to read file: {e}", style="red"))

            if not skipped:
                rc = result.wait()
            else:
                rc = result.returncode if result.returncode is not None else -1

        if output_file and os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding="utf-8", errors="ignore") as f:
                    count = len([line for line in f if line.strip()])
            except:
                pass

    if skipped:
        final_text = Text()
        final_text.append("[⚠] ", style="yellow")
        final_text.append(tool_name, style="bright_blue")
        final_text.append(" Found ", style="bright_blue")
        final_text.append(str(count), style="yellow")
        final_text.append(f" {label}", style="bright_blue")
        final_text.append(" (skipped by user)", style="dim")
        console.print(final_text)
    else:
        final_text = Text()
        final_text.append("[✓] ", style="yellow")
        final_text.append(tool_name, style="bright_blue")
        final_text.append(" Found ", style="bright_blue")
        final_text.append(str(count), style="yellow")
        final_text.append(f" {label}", style="bright_blue")
        console.print(final_text)

    STEP_SKIPPED = skipped
    global LAST_TOOL_EXIT_CODE
    LAST_TOOL_EXIT_CODE = rc if not skipped else None
    return rc

def feature_info():
    info = r"""
=== FEATURE INFORMATION ===

1. Light Scan (Fast Scanning)
   - Subfinder + Assetfinder → find subdomains from target domain.
   - Httpx → filter active subdomains (HTTP response).
   - Nuclei → scan active subdomains using common templates like:
     misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, etc.
   - Scan speed can be adjusted (low/standard/fast).
   - Scan results are automatically sent to Telegram.

2. Dark Scan (Medium Recon)
   - Subfinder + Assetfinder → find as many subdomains as possible from target.
   - Combine and remove duplicate results.
   - Httpx → validate active subdomains.
   - Waybackurls + Gau + Katana → crawling URLs with parameters and .js files.
   - Filter URLs that have parameters (?key=value) and .js files.
   - Nuclei stage 1 → scan parameterized URLs for vulnerability detection (DAST templates).
   - Nuclei stage 2 → scan URLs (.js) for exposure detection.
   - Scan speed can be adjusted (low/standard/fast).
   - All results are automatically sent to Telegram.

3. Deep Scan (Deep Recon)
   - Same as Dark Scan with additions:
   - Sensitive data detection → filter sensitive URL extensions (200 + 403).
   - SecretFinder → scan JS URLs for secrets and sensitive information.
   - Nuclei stage 1 → scan active subdomains (common templates).
   - Nuclei stage 2 → scan URLs (.js) for exposure detection.
   - Nuclei stage 3 → scan parameterized URLs for vulnerability detection (DAST).
   - Nuclei stage 4 → scan subdomains for subdomain takeover detection.

4. Find Sensitive Data (Automatic Sensitive Data Search)
   - Subfinder + Assetfinder → find subdomains.
   - Httpx → validate active subdomains.
   - Waybackurls + Gau + Katana → crawling URLs with parameters and .js files.
   - Httpx → filter active URLs (200 + 403).
   - Separate URLs by type: parameters, .js files, sensitive 200 OK, sensitive 403.
   - Send sensitive file lists 200/403 to Telegram.
   - SecretFinder → scan JS URLs for secrets and sensitive information.

5. Subdomain Takeover Checker
   - Has two modes:
     • Mass → from subdomain list file.
     • Wildcard → auto subdomain with subfinder + assetfinder.
   - Uses Nuclei with `takeover` tag (severity low+) to check for possible takeover.
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

# Setting config (beserta default & komentar penjelas) yang WAJIB ada.
# Kalau user pakai config.py versi lama yang belum punya setting baru,
# tool akan menambahkannya otomatis tanpa menyentuh BOT_TOKEN/CHAT_ID.
CONFIG_REQUIRED = [
    ("KATANA_LIMIT", 5, "# Max active subdomains processed by Katana crawl (0 = skip, -1 = unlimited)"),
    ("RESUME_SCAN_MODE", "ask", '# Resume scan configuration\n# Options: "ask" (always ask), "continue" (auto continue), "restart" (auto restart)'),
    ("SCAN_SPEED", "standard", "# Scan speed\n# Options: \"low\", \"standard\", \"fast\""),
    ("STORAGE_MODE", "by_target", '# Storage mode configuration\n# Options: "by_type" (each type in separate folder) or "by_target" (all files in one folder per target)'),
    ("SECRETFINDER_MODE", "direct", '# SecretFinder mode: "direct" (scan URL directly) or "local" (download JS to js-saved/ folder)'),
    ("GITHUB_USER", "phims403", "# GitHub username (for tool updates)"),
    ("GITHUB_REPO", "lazyhunter", "# GitHub repository name (for tool updates)"),
]

def ensure_config_settings():
    """
    Add any missing config settings (with their comment headers) to config.py.
    Never touches BOT_TOKEN / CHAT_ID, so users keep their Telegram credentials.
    Call once at startup (after config is imported).
    """
    cfg_path = os.path.join(os.path.dirname(__file__), "config.py")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    missing = []
    for key, default, comment in CONFIG_REQUIRED:
        if not re.search(rf'^{key}\s*=', content, flags=re.MULTILINE):
            missing.append((key, default, comment))
    if not missing:
        return False
    # Append missing settings di akhir file (sebelum/tanpa mengubah yang ada)
    additions = ["", "# NOTE: DO NOT CHANGE ABOVE THIS!!!",
                 "# Auto-added settings (missing from your config.py) — safe to edit"]
    for key, default, comment in missing:
        if isinstance(default, str):
            val_line = f'{key} = "{default}"'
        else:
            val_line = f"{key} = {default}"
        additions.append("")
        additions.append(comment)
        additions.append(val_line)
    with open(cfg_path, "a", encoding="utf-8") as f:
        f.write("\n".join(additions) + "\n")
    importlib.reload(config)
    print("[ℹ️] config.py: added missing settings -> " + ", ".join(k for k, _, _ in missing))
    return True

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
        print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")
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
    if not os.path.exists(input_file):
        # Source file may not exist if the crawler produced no output (e.g. 0
        # subdomains). Write an empty result instead of crashing.
        open(output_file, 'w', encoding='utf-8').close()
        return 0
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
def find_sensitive_data(target, resume=False):
    """
    Find Sensitive Data - Enhanced Version
    Flow: Crawler → HTTPX Filter → Separate → Send 200/403 → SecretFinder
    """
    speed = get_speed()
    print(f"\033[94m[ℹ️] Scan speed -> {speed}\033[0m")
    print(f"\033[94m[ℹ️] Storage mode -> {get_storage_mode()}\033[0m")

    # Define all output paths
    paths = get_output_paths(target)
    subdomain_file = paths['subdomain_file']
    active_file = paths['active_file']
    wayback_output = paths['wayback_output']
    gau_output = paths['gau_output']
    katana_output = paths['katana_output']
    crawled_filtered_output = paths['crawled_filtered_output']

    # Output files setelah httpx filter
    param_output = paths['param_output']
    js_output = paths['js_output']
    sen_200_file = paths['sen_200_file']
    sen_403_file = paths['sen_403_file']

    if resume:
        print(f"\n\033[94m[▶] Resuming process for {target}\033[0m")

    # STEP 1: Find Subdomains
    if not is_step_completed(target, "subdomain_finding"):
        write_log(target, "subdomain_finding", "processing")
        finding_subdomain(target, subdomain_file)
    else:
        info = get_step_info(target, "subdomain_finding")
        count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mSubdomain finding already completed{count_str}, skipping\033[0m")

    # STEP 2: Active Check
    if not is_step_completed(target, "httpx_subd"):
        write_log(target, "httpx_subd", "processing")
        active_check(active_file, subdomain_file, "Subdomain", target)
    else:
        info = get_step_info(target, "httpx_subd")
        count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mHttpx already completed{count_str}, skipping\033[0m")

    # STEP 3: Crawling (Wayback + GAU + Katana)
    if not is_step_completed(target, "crawling"):
        write_log(target, "crawling", "processing")
        process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)
    else:
        info = get_step_info(target, "crawling")
        count_str = f" ({info['count']} URLs)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mCrawling already completed{count_str}, skipping\033[0m")

    # STEP 4: HTTPX Crawl Filter + Separate
    js_count = 0
    if not is_step_completed(target, "httpx_crawl"):
        write_log(target, "httpx_crawl", "processing")
        js_count = httpx_filter_and_separate(
            target, crawled_filtered_output,
            param_output, js_output,
            sen_200_file, sen_403_file
        )
    else:
        info = get_step_info(target, "httpx_crawl")
        if info and info.get('info'):
            print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed ({info['info']}), skipping\033[0m")
        else:
            print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed, skipping\033[0m")

    # STEP 5: Send 200 and 403 sensitive files to Telegram
    if not is_step_completed(target, "sensitive_data"):
        write_log(target, "sensitive_data", "processing")
        send_sensitive_files_to_telegram(target, sen_200_file, sen_403_file)
        write_log(target, "sensitive_data", count=0, info="sent to telegram")
    else:
        print(f"\033[33m[✓]\033[0m \033[94mSensitive data sending already completed, skipping\033[0m")

    # STEP 6: SecretFinder Scan
    if not is_step_completed(target, "secretfinder"):
        write_log(target, "secretfinder", "processing")
        if os.path.exists(js_output):
            with open(js_output, "r", encoding="utf-8", errors="ignore") as f:
                js_count = sum(1 for line in f if line.strip())
        if js_count > 0:
            secretfinder_text = scan_js_with_secretfinder(target, js_output)
            if secretfinder_text:
                sec_finder_file = paths['sec_finder_file']
                with open(sec_finder_file, "w", encoding="utf-8") as f:
                    f.write(secretfinder_text)
                send_telegram_report(sec_finder_file, f"{target} - SecretFinder Results")
        else:
            write_log(target, "secretfinder", count=0, info="no JS URLs found")
            print(f"\033[94m[ℹ️] No JS URLs found, skipping SecretFinder scan\033[0m")
    else:
        info = get_step_info(target, "secretfinder")
        count_str = f" ({info['count']} secrets found)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mSecretFinder already completed{count_str}, skipping\033[0m")

    print(f"\n[✓] All processes completed for target: {target}")



def log_error(target, process, error_message):
    """Log an error for a target. Writes to the per-target log file."""
    # Write to per-target log file using the new log system
    step_name = process.lower().replace(" ", "_").replace("(", "").replace(")", "")
    write_log(target, step_name, status="error", info=str(error_message))

    print("\n[!] Error occurred:\n")
    print(error_message)


def finding_subdomain(target, subdomain_file):
    temp_subdomain_file = subdomain_file + ".tmp"
    running_subfinder(target, temp_subdomain_file)
    running_assetfinder(target, temp_subdomain_file)
    filter_subdomains_from_file(temp_subdomain_file, target, subdomain_file)
    if os.path.exists(temp_subdomain_file):
        os.remove(temp_subdomain_file)
    # Log: count subdomains found
    sub_count = 0
    if os.path.exists(subdomain_file):
        with open(subdomain_file, "r", encoding="utf-8", errors="ignore") as f:
            sub_count = sum(1 for line in f if line.strip())
    write_log(target, "subdomain_finding", count=sub_count)

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
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Subfinder")
            print(e)
            log_error(target, "Subfinder", str(e))
            return
def running_assetfinder(target, subdomain_file):
    # Gunakan file sementara berbasis string biasa (bukan NamedTemporaryFile) agar
    # handle file tidak "terbuka" — NamedTemporaryFile(delete=False) tanpa variabel
    # handle dapat "file in use" di Windows dan FD leak di Linux.
    assetfinder_tmp = os.path.join(tempfile.gettempdir(), f"assetfinder_{target}_{int(time.time()*1000)}.txt")
    try:
        def run_assetfinder():
            out_fh = open(assetfinder_tmp, "w", encoding="utf-8")
            try:
                proc = subprocess.Popen(
                    ["assetfinder", "-subs-only", target],
                    stdout=out_fh,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except Exception:
                out_fh.close()
                raise
            return proc

        run_with_animation_no_output(
            message="Finding Subdomain With Assetfinder",
            func=run_assetfinder,
            tool_name="Assetfinder",
            label="subdomains",
            output_file=assetfinder_tmp
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Assetfinder")
            print(e)
            log_error(target, "Assetfinder", str(e))
            return
    all_subs = set()
    # Guard: salah satu file dapat tidak ada jika tool sebelumnya (subfinder) gagal
    for path in [subdomain_file, assetfinder_tmp]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                all_subs.update(line.strip() for line in f if line.strip())
    with open(subdomain_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_subs)))
    # Bersihkan file sementara
    if os.path.exists(assetfinder_tmp):
        os.remove(assetfinder_tmp)

def active_check(active_file, subdomain_file, url, target, log_step="httpx_subd"):
    try:
        def run_httpx():
            httpx_args = get_tool_args("httpx") or ["-silent", "-mc", "200", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]
            out_fh = open(active_file, "w", encoding="utf-8")
            try:
                return subprocess.Popen(
                    ["httpx", *httpx_args, "-l", subdomain_file],
                    stdout=out_fh,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except Exception:
                out_fh.close()
                raise
        run_with_animation_no_output(
            message=f"Checking active {url}",
            func=run_httpx,
            tool_name="Httpx",
            label=f"{url} active",
            output_file=active_file
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Httpx")
            print(e)
            log_error(target, "Httpx", str(e))
            return
    active = 0
    if os.path.exists(active_file):
        with open(active_file, "r", encoding="utf-8", errors="ignore") as f:
            active = sum(1 for line in f if line.strip())
    # Kalau user skip step ini, jangan tandai "completed" supaya resume
    # mengulang step ini, bukan melewatkannya.
    if STEP_SKIPPED:
        write_log(target, log_step, status="skipped", info="skipped by user")
    else:
        write_log(target, log_step, count=active)

def crawling_wayback(wayback_output, active_file, target):
    try:
        def run_waybackurls():
            # Gunakan stdin Python (bukan shell True) agar path tidak rentan
            # command injection & file handle tidak bocor.
            with open(active_file, "r", encoding="utf-8", errors="ignore") as in_fh:
                out_fh = open(wayback_output, "w", encoding="utf-8")
                try:
                    return subprocess.Popen(
                        ["waybackurls"],
                        stdin=in_fh,
                        stdout=out_fh,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                except Exception:
                    out_fh.close()
                    raise
        run_with_animation_no_output(
            message="Crawling URLs With Waybackurls",
            func=run_waybackurls,
            tool_name="Waybackurls",
            label="URLs",
            output_file=wayback_output
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Waybackurl")
            print(e)
            log_error(target, "Waybackurl", str(e))
            return

def crawling_gau(gau_output, target):
    try:
        gau_args = get_tool_args("gau") or ["--subs", "--threads", "20", "--blacklist", "png,jpg,jpeg,gif,css,svg,woff,woff2,ttf,eot,ico,ico", "--verbose"]
        def run_gau():
            out_fh = open(gau_output, "w", encoding="utf-8")
            try:
                return subprocess.Popen(
                    ["gau", target, *gau_args],
                    stdout=out_fh,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except Exception:
                out_fh.close()
                raise
        run_with_animation_no_output(
            message="Crawling URLs with Gau",
            func=run_gau,
            tool_name="Gau",
            label="URLs",
            output_file=gau_output
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Gau")
            print(e)
            log_error(target, "Gau", str(e))
            return

def crawling_katana(katana_output, input_file, target):
    try:
        def run_katana():
            katana_args = get_tool_args("katana") or ["-jc", "15", "-d", "4"]
            out_fh = open(katana_output, "w", encoding="utf-8")
            try:
                return subprocess.Popen(
                    ["katana", "-list", input_file, *katana_args, "-f", "qurl", "-fs", "fqdn"],
                    stdout=out_fh,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
            except Exception:
                out_fh.close()
                raise
        run_with_animation_no_output(
            message="Crawling URLs with Katana",
            func=run_katana,
            tool_name="Katana",
            label="URLs",
            output_file=katana_output
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Katana")
            print(e)
            log_error(target, "Katana", str(e))
            return

def has_sensitive_ext(url):
    """
    True jika URL menunjuk ke file dengan ekstensi sensitif (path ends with ext).
    Potong query & fragment dulu agar 'file.zip?download=1' tetap terdeteksi,
    tetapi '/login' atau '/environment' TIDAK salah match sebagai .log/.env.
    """
    from urllib.parse import urlparse
    path = urlparse(url).path.lower()
    sensitive_exts = [
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".bak", ".backup", ".old",
        ".sql", ".db", ".sqlite",
        ".env", ".log",
        ".conf", ".config", ".ini", ".cfg",
        ".xml", ".json"
    ]
    return any(path.endswith(ext) for ext in sensitive_exts)

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
        ".xml", ".json"
    ]

    for url in wayback_urls + gau_urls + katana_urls:
        if "?" in url or url.endswith(".js") or has_sensitive_ext(url):
            all_urls.add(url)

    with open(crawled_filtered_output, "w") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")
def separate_urls(crawled_filtered_output, param_output, js_output, target):
    import re
    # Try to extract target from filename (by_type mode: crawled_filtered_target.txt)
    # In by_target mode, filename is crawled_filtered.txt without target suffix, so use the target parameter directly
    target_match = re.search(r'crawled_filtered_(.+)\.txt', os.path.basename(crawled_filtered_output))
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
    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(param_urls)}\033[94m URLs with parameter\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(js_urls)}\033[94m URLs .js\033[0m")

def process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output):
    if not is_step_completed(target, "wayback"):
        crawling_wayback(wayback_output, active_file, target)
    wayback_count = 0
    if os.path.exists(wayback_output):
        with open(wayback_output, "r", encoding="utf-8", errors="ignore") as f:
            wayback_count = sum(1 for line in f if line.strip() and "http" in line)
    if STEP_SKIPPED:
        write_log(target, "wayback", status="skipped", info="skipped by user")
    else:
        write_log(target, "wayback", count=wayback_count)

    if not is_step_completed(target, "gau"):
        crawling_gau(gau_output, target)
    gau_count = 0
    if os.path.exists(gau_output):
        with open(gau_output, "r", encoding="utf-8", errors="ignore") as f:
            gau_count = sum(1 for line in f if line.strip() and "http" in line)
    if STEP_SKIPPED:
        write_log(target, "gau", status="skipped", info="skipped by user")
    else:
        write_log(target, "gau", count=gau_count)

    if not is_step_completed(target, "katana"):
        with open(active_file, "r", encoding="utf-8", errors="ignore") as f:
            alive_subs = [line.strip() for line in f if line.strip()]
        importlib.reload(config)
        limit = getattr(config, "KATANA_LIMIT", 20)

        if limit == -1:
            print(f"\033[94m[+] Unlimited mode enabled, using all active subdomains for Katana scan\033[0m")
            input_for_katana = active_file
        elif len(alive_subs) >= limit:
            if get_storage_mode() == "by_target":
                limited_file = os.path.join(os.path.dirname(active_file), f"{limit}_active.txt")
            else:
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
    katana_count = 0
    if os.path.exists(katana_output):
        with open(katana_output, "r", encoding="utf-8", errors="ignore") as f:
            katana_count = sum(1 for line in f if line.strip() and "http" in line)
    if STEP_SKIPPED:
        write_log(target, "katana", status="skipped", info="skipped by user")
    else:
        write_log(target, "katana", count=katana_count)

    wayback_filtered = wayback_output + ".tmp"
    gau_filtered = gau_output + ".tmp"
    katana_filtered = katana_output + ".tmp"
    import shutil
    # Guard: crawler tool dapat gagal / menghasilkan 0 baris (mis. 0 subdomain
    # aktif), sehingga file output tidak ada. Jangan biarkan shutil.copy crash.
    for src, dst in [(wayback_output, wayback_filtered),
                     (gau_output, gau_filtered),
                     (katana_output, katana_filtered)]:
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            open(dst, "w", encoding="utf-8").close()
    filter_domains_from_base_domain(wayback_filtered, target, wayback_output)
    filter_domains_from_base_domain(gau_filtered, target, gau_output)
    filter_domains_from_base_domain(katana_filtered, target, katana_output)
    os.remove(wayback_filtered)
    os.remove(gau_filtered)
    os.remove(katana_filtered)
    combine_crawling_results(wayback_output, gau_output, katana_output, crawled_filtered_output, target)
    crawled_count = 0
    if os.path.exists(crawled_filtered_output):
        with open(crawled_filtered_output, "r", encoding="utf-8", errors="ignore") as f:
            crawled_count = sum(1 for line in f if line.strip())
    if STEP_SKIPPED:
        write_log(target, "crawling", status="skipped", info="skipped by user")
    else:
        write_log(target, "crawling", count=crawled_count)

def httpx_filter_and_separate(target, crawled_filtered_output, param_output, js_output, sen_200_file, sen_403_file):
    """
    Filter all crawled URLs with httpx (200 + 403), then separate into 3 categories:
    1. Parameter URLs (only 200, remove [200])
    2. JS URLs (only 200, remove [200])
    3. Sensitive extension URLs (separate 200 and 403)
    """
    httpx_args = ["-silent", "-sc", "-nc", "-mc", "200,403", "-t", "300", "-rate-limit", "1000", "-retries", "3", "-timeout", "10"]

    # Temp file for httpx output
    httpx_output = crawled_filtered_output + ".httpx"

    # Run httpx filter
    print(f"\033[94m[+] Filtering crawled URLs with httpx (200 + 403)... \033[0m")

    def run_httpx():
        # Piping dengan `cat | httpx` (shell=True) rentan command injection lewat
        # path file. Pakai -l parameter httpx yang menerima file list langsung.
        out_fh = open(httpx_output, "w", encoding="utf-8")
        try:
            return subprocess.Popen(
                ["httpx", *httpx_args, "-l", crawled_filtered_output],
                stdin=subprocess.DEVNULL,
                stdout=out_fh,
                stderr=subprocess.DEVNULL,
                text=True
            )
        except Exception:
            out_fh.close()
            raise

    run_with_animation_no_output(
        message="Filtering URLs with httpx",
        func=run_httpx,
        tool_name="Httpx",
        label="URLs",
        output_file=httpx_output
    )

    # Separate hasil httpx filter
    param_urls = []
    js_urls = []
    sens_200_urls = []
    sens_403_urls = []

    sensitive_exts = [
        ".zip", ".tar", ".gz", ".7z", ".rar",
        ".bak", ".backup", ".old",
        ".sql", ".db", ".sqlite",
        ".env", ".log",
        ".conf", ".config", ".ini", ".cfg",
        ".xml", ".json"
    ]

    with open(httpx_output, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse URL dan status code
            # Format: "https://example.com/file.zip [200]" atau "[403]"
            url = line.split()[0] if line.split() else line
            has_200 = '[200]' in line
            has_403 = '[403]' in line

            # Check for JS files (200 only) - for SecretFinder scan
            if has_200 and url.endswith('.js'):
                js_urls.append(url)

            # Check for parameters (hanya 200)
            if has_200 and '?' in url and not url.endswith('.js'):
                param_urls.append(url)

            # Check for sensitive extensions (pisah 200 dan 403)
            if has_sensitive_ext(url):
                if has_200:
                    sens_200_urls.append(url)
                elif has_403:
                    sens_403_urls.append(url)

    # Write parameter URLs (tanpa [200])
    os.makedirs(os.path.dirname(param_output), exist_ok=True)
    with open(param_output, "w") as f:
        for url in param_urls:
            f.write(url + "\n")

    # Write JS URLs (tanpa [200])
    with open(js_output, "w") as f:
        for url in js_urls:
            f.write(url + "\n")

    # Write sensitive 200 (dikelompokkan per extension)
    os.makedirs(os.path.dirname(sen_200_file), exist_ok=True)
    if sens_200_urls:
        with open(sen_200_file, "w", encoding="utf-8") as f:
            f.write(f"Sensitive URLs with 200 OK Response - {target}\n")
            f.write("=" * 60 + "\n\n")
            for ext in sensitive_exts:
                ext_urls = [url for url in sens_200_urls if url.split("?")[0].split("#")[0].lower().endswith(ext)]
                if ext_urls:
                    f.write(f"[{ext.upper()}] - {len(ext_urls)} URLs\n")
                    for url in ext_urls:
                        f.write(url + "\n")
                    f.write("\n")
    else:
        open(sen_200_file, "w").close()

    # Write sensitive 403 (dikelompokkan per extension)
    os.makedirs(os.path.dirname(sen_403_file), exist_ok=True)
    if sens_403_urls:
        with open(sen_403_file, "w", encoding="utf-8") as f:
            f.write(f"Sensitive URLs with 403 Forbidden Response - {target}\n")
            f.write("=" * 60 + "\n\n")
            for ext in sensitive_exts:
                ext_urls = [url for url in sens_403_urls if url.split("?")[0].split("#")[0].lower().endswith(ext)]
                if ext_urls:
                    f.write(f"[{ext.upper()}] - {len(ext_urls)} URLs\n")
                    for url in ext_urls:
                        f.write(url + "\n")
                    f.write("\n")
    else:
        open(sen_403_file, "w").close()

    # Cleanup
    if os.path.exists(httpx_output):
        os.remove(httpx_output)

    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(param_urls)}\033[94m URLs with parameter (200 OK)\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(js_urls)}\033[94m URLs .js (200 OK)\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(sens_200_urls)}\033[94m sensitive URLs including .js (200 OK)\033[0m")
    print(f"\033[33m[✓]\033[94m Successfully found \033[93m{len(sens_403_urls)}\033[94m sensitive URLs (403 Forbidden)\033[0m")

    # Log httpx_filter_and_separate results
    # Kalau user skip step ini, jangan tandai "completed" supaya resume
    # mengulang step ini, bukan melewatkannya.
    if STEP_SKIPPED:
        write_log(target, "httpx_crawl", status="skipped", info="skipped by user")
    else:
        write_log(target, "httpx_crawl", count=len(param_urls) + len(js_urls) + len(sens_200_urls) + len(sens_403_urls),
                  info=f"param={len(param_urls)}, js={len(js_urls)}, sens_200={len(sens_200_urls)}, sens_403={len(sens_403_urls)}")

    return len(js_urls)

def send_sensitive_files_to_telegram(target, sen_200_file, sen_403_file):
    """
    Send sensitive files to Telegram (2 files: 200 and 403)
    Send sensitive files to Telegram immediately (don't wait for SecretFinder)
    """
    importlib.reload(config)
    if not token_valid(config.BOT_TOKEN) or not chat_id_valid(config.CHAT_ID):
        print("[ℹ️] Bot token or chat_id not found / invalid. Skipping Telegram sending.")
        return

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument"

    msg_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"

    # Send 200 OK file
    if os.path.exists(sen_200_file) and os.stat(sen_200_file).st_size > 0:
        try:
            with open(sen_200_file, "rb") as f:
                response = requests.post(
                    url,
                    data={'chat_id': config.CHAT_ID},
                    files={'document': f}
                )
            if response.status_code == 200:
                print(f"[✓] 200 OK sensitive URLs file sent to Telegram")
            else:
                print(f"[❌] Failed to send 200 OK file: {response.text}")
        except Exception as e:
            print(f"[⚠️] Error sending 200 OK file: {e}")
    else:
        try:
            requests.post(msg_url, data={'chat_id': config.CHAT_ID, 'text': f"[{target}] No 200 OK sensitive URLs found (zonk)."})
        except Exception as e:
            print(f"[⚠️] Failed to send 'zonk' message to Telegram: {e}")
        print(f"[ℹ️] No 200 OK sensitive URLs to send")

    # Send 403 Forbidden file
    if os.path.exists(sen_403_file) and os.stat(sen_403_file).st_size > 0:
        try:
            with open(sen_403_file, "rb") as f:
                response = requests.post(
                    url,
                    data={'chat_id': config.CHAT_ID},
                    files={'document': f}
                )
            if response.status_code == 200:
                print(f"[✓] 403 Forbidden sensitive URLs file sent to Telegram")
            else:
                print(f"[❌] Failed to send 403 file: {response.text}")
        except Exception as e:
            print(f"[⚠️] Error sending 403 file: {e}")
    else:
        try:
            requests.post(msg_url, data={'chat_id': config.CHAT_ID, 'text': f"[{target}] No 403 Forbidden sensitive URLs found (zonk)."})
        except Exception as e:
            print(f"[⚠️] Failed to send 'zonk' message to Telegram: {e}")
        print(f"[ℹ️] No 403 sensitive URLs to send")

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
        try:
            requests.post(
                f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
                data={'chat_id': config.CHAT_ID, 'text': message}
            )
        except Exception as e:
            print(f"[⚠️] Failed to send 'no sensitive path' message to Telegram: {e}")
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


def download_js_files(target, js_urls):
    """
    Download JS files from URLs to js-saved/<target>/ directory.
    Preserves URL path structure for easy browsing.
    Returns list of (original_url, local_path) tuples.
    """
    base_dir = os.path.join("js-saved", target)
    downloaded = []
    total = len(js_urls)

    for i, js_url in enumerate(js_urls):
        parsed = urlparse(js_url)
        file_path = parsed.path.lstrip("/")
        if not file_path or file_path.endswith("/"):
            file_path = file_path + "index.js"
        local_path = os.path.join(base_dir, parsed.netloc, file_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            resp = requests.get(js_url, timeout=15, headers={"User-Agent": random.choice(USER_AGENTS)})
            if resp.status_code == 200:
                with open(local_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(resp.text)
                downloaded.append((js_url, local_path))
            else:
                print(f"\033[91m  [!] Failed to download ({resp.status_code}): {js_url}\033[0m")
        except Exception as e:
            print(f"\033[91m  [!] Error downloading {js_url}: {e}\033[0m")

        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"\r\033[94m[+] Downloading JS files {i+1}/{total}...\033[0m", end="", flush=True)

    print(f"\n\033[93m[✓]\033[94m Downloaded {len(downloaded)}/{total} JS files to {base_dir}/\033[0m")
    return downloaded

def scan_js_with_secretfinder(target, js_file):
    """
    Scan JavaScript URLs with SecretFinder.
    Mode "direct": scan URL via SecretFinder directly.
    Mode "local": download JS to js-saved/ first, then scan local files.
    """
    if not os.path.exists(js_file):
        return None

    with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
        js_urls = [line.strip() for line in f if line.strip()]

    if not js_urls:
        return None

    importlib.reload(config)
    sf_mode = getattr(config, "SECRETFINDER_MODE", "direct")

    # SecretFinder command
    secretfinder_path = os.path.expanduser("~/SecretFinder/SecretFinder.py")

    # Check if SecretFinder is installed
    if not os.path.exists(secretfinder_path):
        print(f"[!] SecretFinder not found at {secretfinder_path}")
        print(f"[!] Please run setup.sh to install SecretFinder")
        return None

    # Ignore filters for external libraries (semicolon-separated)
    ignore_list = "jquery;bootstrap;cdnjs.cloudflare.com;unpkg.com;ajax.googleapis.com;googleapis"

    # Characters that indicate the value is NOT a single secret word
    separators = [' ', '=', ':', '{', '}', '(', ')', ';', ',', '\t', '\n']

    # Keyword blacklist - patterns that clearly indicate NOT a real secret
    keyword_blacklist = [
        'function', 'undefined', 'error', 'null', 'true', 'false', 'return',
        'detector', 'structure', 'manager', 'handler', 'builder', 'factory',
        'prototype', 'constructor', 'extends', 'class', 'module', 'export',
        'import', 'require', 'define', 'amd', 'commonjs',
        'your-', 'changeme', 'not_set', 'notconfigured',
        'todo', 'fixme', 'demo_', 'test_', 'xxxx', '****'
    ]

    # If mode is "local", download JS files first
    if sf_mode == "local":
        downloaded = download_js_files(target, js_urls)
        scan_items = [(local_path, url) for url, local_path in downloaded]
        if not scan_items:
            print("[!] No JS files downloaded, skipping SecretFinder scan.")
            return None
    else:
        scan_items = [(url, url) for url in js_urls]

    results = []
    scanned_count = 0
    secrets_found = 0
    current_url = None

    for input_path, display_url in scan_items:
        scanned_count += 1
        print(f"\r\033[94m[+] Scanning JS file {scanned_count}/{len(scan_items)}...\033[0m", end="", flush=True)

        try:
            # Build SecretFinder command with correct flags
            cmd = [
                "python3", secretfinder_path,
                "-i", input_path,
                "-o", "cli",
                "-g", ignore_list,
                "-n", target
            ]

            # Run SecretFinder
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse output - format: [SECRET_TYPE] -> [MATCHED_VALUE]
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                url_has_secrets = False
                for line in lines:
                    line = line.strip()
                    # Check if line contains a URL (starts with http)
                    if line.startswith('http') or line.startswith('[ + ]'):
                        if line.startswith('[ + ] URL:'):
                            current_url = line.split('[ + ] URL:')[1].strip()
                        elif line.startswith('http'):
                            current_url = line
                        url_has_secrets = False
                    elif '->' in line or '=>' in line:
                        # Parse secret type and value
                        parts = line.split('->') if '->' in line else line.split('=>')
                        if len(parts) == 2:
                            secret_type = parts[0].strip().strip('[]')
                            secret_value = parts[1].strip()

                            # Define type_lower and value_lower at the beginning (used by multiple filters)
                            type_lower = secret_type.lower()
                            value_lower = secret_value.lower()

                            # FILTER 1: Blacklist false positive secret types
                            # authorization_basic = enum/property names (basic_info, BASIC_ADDRESS, etc.) - 100% FP
                            # Heroku, Twilio, reCAPTCHA, Square, possible_Creds, generic_api_key = too many FPs
                            if ('heroku' in type_lower or 'twilio' in type_lower or 'google_captcha' in type_lower or
                                'captcha' in type_lower or 'square' in type_lower or 'authorization_api' in type_lower or
                                'authorization_basic' in type_lower or 'generic_api_key' in type_lower or
                                'possible_creds' in type_lower):
                                continue

                            # FILTER 2: Single word only (no separators)
                            has_separator = any(sep in secret_value for sep in separators)
                            if has_separator:
                                continue

                            # FILTER 3: Variable names and HTML fragments (case-insensitive)

                            # HTML fragments - contains HTML tags or markers
                            html_markers = ['<', '>', 'label', 'div', 'span', 'input', 'form', 'button', 'textarea']
                            if any(marker in value_lower for marker in html_markers):
                                continue

                            # Variable/property names - common PREFIX patterns (jelas bukan secret)
                            false_prefixes = ['api_', 'basic-', 'API_', 's3-', 'amazon_aws', 'authorization_', 'auth_',
                                              'user_', 'admin_', 'config_', 'setting_', 'search-', 'list-', 'get_',
                                              'set_', 'is_', 'has_', 'can_', 'should_', 'will_', 'did_']
                            if any(value_lower.startswith(prefix) for prefix in false_prefixes):
                                continue

                            # Variable/property names - common suffixes and patterns
                            var_suffixes = ['_', 'enabled', 'disabled', 'version', 'events', 'properties', 'viewer', 'handler', 'listener', 'detector']
                            if any(value_lower.endswith(suffix) or suffix + '_' in value_lower for suffix in var_suffixes):
                                continue

                            # FILTER 4: Keyword blacklist (case-insensitive)
                            is_blacklisted = any(keyword in value_lower for keyword in keyword_blacklist)
                            if is_blacklisted:
                                continue

                            # FILTER 4.5: Placeholder, URL, and numeric-value checks
                            # Placeholder keywords added on top of FILTER 4
                            placeholder_keywords = ['placeholder', 'not_set', 'notconfigured', 'todo', 'fixme', 'changeme']
                            if any(k in value_lower for k in placeholder_keywords):
                                continue

                            # Value is a URL — clearly not a credential
                            if secret_value.startswith('http://') or secret_value.startswith('https://'):
                                continue

                            # Numeric-only values (e.g. "1234567890") — not credentials
                            if secret_value.isdigit():
                                continue

                            # FILTER 5: Format validation for specific secret types
                            is_valid_format = True

                            # Skip amazon_aws_url2 - these are AWS service names, not credentials
                            if 'amazon_aws_url2' in type_lower:
                                continue

                            # AWS Access Key ID: AKIA/ASIA + 16 chars (total 20)
                            if 'aws_access_key_id' in type_lower or 'amazon_aws_access_key_id' in type_lower:
                                if not ((secret_value.startswith('AKIA') or secret_value.startswith('ASIA')) and len(secret_value) == 20):
                                    is_valid_format = False
                                # Reject keys with repeating chars that look like padding/obfuscation
                                if re.search(r'(.)\1{6,}', secret_value):
                                    is_valid_format = False

                            # Google API key: AIzaSy + 33 chars (total 39)
                            if 'google_api' in type_lower:
                                if not (secret_value.startswith('AIzaSy') and len(secret_value) == 39):
                                    is_valid_format = False

                            # Check if it's a base64 image (common false positive)
                            if secret_value.startswith('EAAAABCAAAAAA') or secret_value.startswith('iVBORw0KGgo') or 'H5BAE' in secret_value:
                                is_valid_format = False

                            if not is_valid_format:
                                continue

                            # Add to results
                            if not url_has_secrets:
                                results.append(f"\n🔍 URL: {display_url}")
                                url_has_secrets = True

                            results.append(f"   🚨 [{secret_type}]")
                            results.append(f"   ✖️ {secret_value}")

                            secrets_found += 1

        except subprocess.TimeoutExpired:
            results.append(f"\n⏱️ URL: {display_url} - Timeout")
        except Exception as e:
            results.append(f"\n❌ URL: {display_url} - Error: {str(e)}")

    print(f"\n\033[33m[✓]\033[94m SecretFinder scan completed for \033[93m{scanned_count}\033[94m JavaScript URLs\033[0m")
    print(f"\033[33m[✓]\033[94m Found \033[93m{secrets_found}\033[94m potential secrets\033[0m")

    # Log secretfinder results
    write_log(target, "secretfinder", count=secrets_found, info=f"scanned={scanned_count}")

    # Format results for Telegram
    saved_note = ""
    if sf_mode == "local":
        base_dir = os.path.join("js-saved", target)
        saved_note = f"\n📁 *JS files saved to:* `{base_dir}/` for further analysis\n"

    if results:
        header = f"""🔐 *SECRETFINDER SCAN RESULTS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 *Target:* {target}
📊 *URLs Scanned:* {scanned_count}
🚨 *Secrets Found:* {secrets_found}
📅 *Date:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{saved_note}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return header + '\n'.join(results)
    else:
        return f"""🔐 *SECRETFINDER SCAN RESULTS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 *Target:* {target}
📊 *URLs Scanned:* {scanned_count}
✅ *No secrets found*
{saved_note}"""


def nuclei_without_parameter(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_basic_scan():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-nh", "-s", "low,medium,high,critical", "-tags", "misconfiguration,exposure,default-login,panel,cves,tech,cms,files,dns,takeover,ssl,token,fuzz,backup,git,iot,xss", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        rc = run_with_animation("Nuclei (Basic scan)", nuclei_basic_scan)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print("[!] Failed to run Nuclei (Basic Scan)")
        print(e)
        log_error(target, "Nuclei (Basic Scan)", str(e))
        return
    # Kalau user skip (STEP_SKIPPED) atau nuclei keluar dengan kode error,
    # jangan tandai "completed" di log (supaya resume tidak melewatkan step ini)
    if STEP_SKIPPED or rc != 0:
        if STEP_SKIPPED:
            write_log(target, "nuclei_basic", status="skipped", info="skipped by user")
        else:
            log_error(target, "Nuclei (Basic Scan)", f"exited with code {rc}")
        return
    nuclei_count = 0
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
            nuclei_count = sum(1 for line in f if line.strip())
    write_log(target, "nuclei_basic", count=nuclei_count)
    if nuclei_count > 0:
        send_telegram_report(output_file, f"{target} (Nuclei Basic Scan)")

def nuclei_js_exposure(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_js_file():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-s", "low,medium,high,critical", "-nh", "-tags", "js,secrets,exposed-credentials", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        rc = run_with_animation("Running Nuclei (JS File)", nuclei_js_file)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Nuclei (JS File)")
            print(e)
            log_error(target, "Nuclei (JS File)", str(e))
            return
    if STEP_SKIPPED or rc != 0:
        if STEP_SKIPPED:
            write_log(target, "nuclei_js", status="skipped", info="skipped by user")
        else:
            log_error(target, "Nuclei (JS File)", f"exited with code {rc}")
        return
    nuc_js_count = 0
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
            nuc_js_count = sum(1 for line in f if line.strip())
    write_log(target, "nuclei_js", count=nuc_js_count)
    if nuc_js_count > 0:
        send_telegram_report(output_file, f"{target} Nuclei (JS File)")

def nuclei_param_dast(target, input_file, output_file, user_agent, scan_args):
    try:
        def nuclei_dast_mode():
            return subprocess.Popen([
                "nuclei", "-l", input_file, "-nh", "-dast", "-fa", "high", "-s", "low,medium,high,critical", "-ept", "ssl", "-timeout", "5", "-retries", "1", *scan_args, "-o", output_file
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        rc = run_with_animation("Nuclei (DAST MODE)", nuclei_dast_mode)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Nuclei (DAST Mode)")
            print(e)
            log_error(target, "Nuclei (DAST Mode)", str(e))
            return
    if STEP_SKIPPED or rc != 0:
        if STEP_SKIPPED:
            write_log(target, "nuclei_dast", status="skipped", info="skipped by user")
        else:
            log_error(target, "Nuclei (DAST Mode)", f"exited with code {rc}")
        return
    nuc_dast_count = 0
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
            nuc_dast_count = sum(1 for line in f if line.strip())
    write_log(target, "nuclei_dast", count=nuc_dast_count)
    if nuc_dast_count > 0:
        send_telegram_report(output_file, f"{target} Nuclei (DAST Mode)")

def nuclei_takeover(subdomain_file, output_path_takeover, target):
    scan_args = get_tool_args("nuclei")
    cmd = ["nuclei", "-l", subdomain_file, "-nh", "-s", "low,medium,high,critical", "-tags", "takeover", "-o", output_path_takeover]
    if scan_args:
        cmd.extend(scan_args)

    try:
        def nuclei_takeover_scan():
            return subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
        rc = run_with_animation("Nuclei (Takeover Wildcard)", nuclei_takeover_scan)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print("[!] Failed to run Nuclei (Takeover Wildcard)")
            print(e)
            log_error(target, "Nuclei (Takeover Wildcard)", str(e))
            return
    if STEP_SKIPPED or rc != 0:
        if STEP_SKIPPED:
            write_log(target, "nuclei_takeover", status="skipped", info="skipped by user")
        else:
            log_error(target, "Nuclei (Takeover Wildcard)", f"exited with code {rc}")
        return
    tow_count = 0
    if os.path.exists(output_path_takeover):
        with open(output_path_takeover, "r", encoding="utf-8", errors="ignore") as f:
            tow_count = sum(1 for line in f if line.strip())
    write_log(target, "nuclei_takeover", count=tow_count)
    if tow_count > 0:
        send_telegram_report(output_path_takeover, f"({target}) Nuclei (Takeover Wildcard)")

def takeover_mass_file(file_path, output_name=None):
    """Perform takeover check on a list of subdomains from a file"""
    if not os.path.isfile(file_path):
        print(f"[❌] File {file_path} not found.")
        return

    if not output_name:
        output_name = os.path.basename(file_path).replace('.txt', '').replace('.', '_')

    # For by_target mode with mass file, use target_output folder if output_name looks like a target
    if get_storage_mode() == "by_target" and output_name:
        target_folder = os.path.join(OUTPUT_FOLDER_TARGET, output_name)
        os.makedirs(target_folder, exist_ok=True)
        output_path = os.path.join(target_folder, "takeover.txt")
    else:
        output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_name}.txt")

    speed = get_speed()
    print(f"\033[94m[ℹ️ ] Scan speed -> {speed}\033[0m")

    print(f"\n\033[94m[▶] Starting process for file {file_path} (TAKEOVER MASSAL)\033[0m")

    scan_args = get_tool_args("nuclei")
    cmd = ["nuclei", "-l", file_path, "-nh", "-s", "low,medium,high,critical", "-tags", "takeover", "-o", output_path]
    if scan_args:
        cmd.extend(scan_args)

    def run_nuc_takeover():
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        rc = run_with_animation(f"Nuclei (Takeover Mass - {output_name})", run_nuc_takeover)
    # Hanya kirim & log jika tidak di-skip dan nuclei tidak error
    if not STEP_SKIPPED and rc == 0:
        send_telegram_report(output_path, f"({output_name}) Nuclei (Takeover Mass)")
    elif STEP_SKIPPED:
        write_log(output_name, "nuclei_takeover_mass", status="skipped", info="skipped by user")
    else:
        log_error(output_name, "Nuclei (Takeover Mass)", f"exited with code {rc}")
    # Log the takeover mass scan
    tow_count = 0
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
            tow_count = sum(1 for line in f if line.strip())
    if not STEP_SKIPPED:
        write_log(output_name, "nuclei_takeover_mass", count=tow_count)

def takeover_single(target, resume=False):
    """Perform takeover check on a single target"""
    paths = get_output_paths(target)
    input_file = paths['subdomain_file']
    output_path = paths['output_path_takeover']

    speed = get_speed()
    print(f"\033[94m[ℹ️ ] Scan speed -> {speed}\033[0m")
    print(f"\033[94m[ℹ️ ] Storage mode -> {get_storage_mode()}\033[0m")

    if resume:
        print(f"\n\033[94m[▶] Resuming process for {target}\033[0m")

    print(f"\n\033[94m[▶] Starting process for {target} (TAKEOVER)\033[0m")

    # STEP 1: Subdomain Finding
    if not is_step_completed(target, "subdomain_finding"):
        write_log(target, "subdomain_finding", "processing")
        finding_subdomain(target, input_file)
    else:
        info = get_step_info(target, "subdomain_finding")
        count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mSubdomain finding already completed{count_str}, skipping\033[0m")

    # STEP 2: Nuclei Takeover
    if not is_step_completed(target, "nuclei_takeover"):
        write_log(target, "nuclei_takeover", "processing")
        scan_args = get_tool_args("nuclei")
        cmd = ["nuclei", "-l", input_file, "-nh", "-s", "low,medium,high,critical", "-tags", "takeover", "-o", output_path]
        if scan_args:
            cmd.extend(scan_args)

        def run_nuc_takeover():
            return subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )

        rc = run_with_animation(f"Nuclei (Takeover Single - {target})", run_nuc_takeover)
        if STEP_SKIPPED:
            write_log(target, "nuclei_takeover", status="skipped", info="skipped by user")
        elif rc == 0:
            send_telegram_report(output_path, f"({target}) Nuclei (Takeover Single)")
        else:
            log_error(target, "Nuclei (Takeover Single)", f"exited with code {rc}")
    else:
        info = get_step_info(target, "nuclei_takeover")
        count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
        print(f"\033[33m[✓]\033[0m \033[94mNuclei takeover scan already completed{count_str}, skipping\033[0m")

def takeover():
    while True:
        print("\n  \033[94m=== Takeover Mode ===\033[0m")
        print("  \033[94m[1] Mass (from file)\033[0m")
        print("  \033[94m[2] Wildcard (find subdomain automatic)\033[0m")
        print("  \033[94m[3] Back to main menu\033[0m")
        sub_mode = input("\033[94mSelect Mode (1/2/3): \033[0m").strip()
        if sub_mode in ("1", "2"):
            check_takeover(sub_mode)
        elif sub_mode == "3":
            return
        else:
            print("\033[91m[❌] Invalid choice.\033[0m")
def check_takeover(mode):
    speed = get_speed()
    print(f"\033[94m[ℹ️ ] Scan speed -> {speed}\033[0m")

    if mode == "1":
        file_name = input("\n\033[94mEnter file name containing domain/subdomain list (example: subdomain.txt): \033[0m").strip()
        if not os.path.isfile(file_name):
            print("\033[91m[❌] File not found.\033[0m")
            return
        output_name = input("\033[94mEnter output file name (without .txt): \033[0m").strip()
        if not output_name:
            print("\033[91m[❌] Output file name cannot be empty.\033[0m")
            return
        input_file = file_name
        # For by_target mode, use target_output folder
        if get_storage_mode() == "by_target" and output_name:
            target_folder = os.path.join(OUTPUT_FOLDER_TARGET, output_name)
            os.makedirs(target_folder, exist_ok=True)
            output_path = os.path.join(target_folder, "takeover.txt")
        else:
            output_path = os.path.join(OUTPUT_FOLDER_TAKEOVER, f"TO_{output_name}.txt")
        print(f"\n\033[94m[▶] Starting process for file {file_name} (TAKEOVER MASSAL)\033[0m")

        scan_args = get_tool_args("nuclei")
        cmd = ["nuclei", "-l", input_file, "-nh", "-s", "low,medium,high,critical", "-tags", "takeover", "-o", output_path]
        if scan_args:
            cmd.extend(scan_args)

        def run_nuc_takeover():
            return subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
        run_with_animation(f"Nuclei Takeover Mass ({output_name})", run_nuc_takeover)
        send_telegram_report(output_path, f"({output_name}) Nuclei (Takeover Mass)")
    else:
        # Wildcard mode - find subdomains then check takeover
        targets = get_target_input_enhanced()

        if len(targets) == 1:
            # Single target - original behavior
            target = targets[0]
            resume = False
            if has_previous_scan(target):
                resume_action = ask_continue_or_restart(target)
                if resume_action == 'continue':
                    resume = True
                elif resume_action == 'restart':
                    clear_target_log(target)
            takeover_single(target, resume=resume)
        else:
            # Multiple targets - sequential scan
            process_target_list(targets, takeover_single, "Subdomain Takeover")


def light_scan_target(target, resume=False):
        scan_args = ask_scan_speed()
        paths = get_output_paths(target)
        subdomain_file = paths['subdomain_file']
        active_file = paths['active_file']
        nuclei_output_httpx = paths['nuclei_output']
        user_agent = random.choice(USER_AGENTS)
        print(f"\033[94m[ℹ️ ] Storage mode -> {get_storage_mode()}\033[0m")

        if resume:
            print(f"\n\033[94m[▶] Resuming process for {target}\033[0m")

        # STEP 1: Subdomain Finding
        if not is_step_completed(target, "subdomain_finding"):
            write_log(target, "subdomain_finding", "processing")
            finding_subdomain(target, subdomain_file)
        else:
            info = get_step_info(target, "subdomain_finding")
            count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mSubdomain finding already completed{count_str}, skipping\033[0m")

        # STEP 2: HTTPX Subdomain Active Check
        if not is_step_completed(target, "httpx_subd"):
            write_log(target, "httpx_subd", "processing")
            active_check(active_file, subdomain_file, "Subdomain", target)
        else:
            info = get_step_info(target, "httpx_subd")
            count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mHttpx subdomain already completed{count_str}, skipping\033[0m")

        # STEP 3: Nuclei Basic Scan
        if not is_step_completed(target, "nuclei_basic"):
            write_log(target, "nuclei_basic", "processing")
            start_time_nuclei_scan = time.time()
            nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
            end_time_nuclei_scan = time.time()
            scan_duration = end_time_nuclei_scan - start_time_nuclei_scan
            hours, remaining = divmod(int(scan_duration), 3600)
            minutes, seconds = divmod(remaining, 60)
            print(f"[⏱️] Nuclei scanning process completed in {hours} hours {minutes} minutes {seconds} seconds")
        else:
            info = get_step_info(target, "nuclei_basic")
            count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mNuclei basic scan already completed{count_str}, skipping\033[0m")

        print(f"[✓] All processes completed for target: {target}")

def light_scan():
        targets = get_target_input_enhanced()
        if len(targets) == 1:
            # Single target - original behavior
            target = targets[0]
            resume = False
            if has_previous_scan(target):
                resume_action = ask_continue_or_restart(target)
                if resume_action == 'continue':
                    resume = True
                elif resume_action == 'restart':
                    clear_target_log(target)
            light_scan_target(target, resume=resume)
        else:
            # Multiple targets - sequential scan
            process_target_list(targets, light_scan_target, "Light Scan")
def dark_deep_target(mode, target, resume=False):
        scan_args = ask_scan_speed()
        paths = get_output_paths(target)
        subdomain_file = paths['subdomain_file']
        active_file = paths['active_file']
        nuclei_output_httpx = paths['nuclei_output']
        katana_output = paths['katana_output']
        wayback_output = paths['wayback_output']
        gau_output = paths['gau_output']
        crawled_filtered_output = paths['crawled_filtered_output']
        temp_crawled_filtered_output = paths['temp_crawled_filtered_output']
        user_agent = random.choice(USER_AGENTS)
        param_output = paths['param_output']
        js_output = paths['js_output']
        nuclei_output_js = paths['nuclei_output_js']
        nuclei_output_param = paths['nuclei_output_param']
        output_path_takeover = paths['output_path_takeover']
        sen_200_file = paths['sen_200_file']
        sen_403_file = paths['sen_403_file']

        print(f"\033[94m[ℹ️ ] Storage mode -> {get_storage_mode()}\033[0m")

        if resume:
            print(f"\n\033[94m[▶] Resuming process for {target}\033[0m")

        # STEP 1: Subdomain Finding
        if not is_step_completed(target, "subdomain_finding"):
            write_log(target, "subdomain_finding", "processing")
            finding_subdomain(target, subdomain_file)
        else:
            info = get_step_info(target, "subdomain_finding")
            count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mSubdomain finding already completed{count_str}, skipping\033[0m")

        # STEP 2: HTTPX Subdomain Active Check
        if not is_step_completed(target, "httpx_subd"):
            write_log(target, "httpx_subd", "processing")
            active_check(active_file, subdomain_file, "Subdomain", target)
        else:
            info = get_step_info(target, "httpx_subd")
            count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mHttpx subdomain already completed{count_str}, skipping\033[0m")

        # STEP 3: Crawling (Wayback + GAU + Katana + filter + combine)
        if not is_step_completed(target, "crawling"):
            write_log(target, "crawling", "processing")
            process_crawling(target, active_file, wayback_output, gau_output, katana_output, crawled_filtered_output)
        else:
            info = get_step_info(target, "crawling")
            count_str = f" ({info['count']} URLs)" if info and info['count'] is not None else ""
            print(f"\033[33m[✓]\033[0m \033[94mCrawling already completed{count_str}, skipping\033[0m")

        # STEP 4: HTTPX Crawl Filter + Separate
        if mode == "deep":
            # Deep scan uses httpx_filter_and_separate which also produces sensitive data files
            if not is_step_completed(target, "httpx_crawl"):
                write_log(target, "httpx_crawl", "processing")
                httpx_filter_and_separate(
                    target, crawled_filtered_output,
                    param_output, js_output,
                    sen_200_file, sen_403_file
                )
            else:
                info = get_step_info(target, "httpx_crawl")
                if info and info.get('info'):
                    print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed ({info['info']}), skipping\033[0m")
                else:
                    print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed, skipping\033[0m")
        else:
            # Dark scan uses active_check + separate_urls (200 only, no sensitive data)
            if not is_step_completed(target, "httpx_crawl"):
                write_log(target, "httpx_crawl", "processing")
                active_check(temp_crawled_filtered_output, crawled_filtered_output, "URL", target, log_step="httpx_crawl")
                # Guard: httpx dapat menghasilkan 0 URL (crawled_filtered kosong),
                # sehingga file temp tidak ada. Jangan biarkan shutil.move crash.
                if os.path.exists(temp_crawled_filtered_output):
                    shutil.move(temp_crawled_filtered_output, crawled_filtered_output)
                separate_urls(crawled_filtered_output, param_output, js_output, target)
            else:
                info = get_step_info(target, "httpx_crawl")
                if info and info.get('info'):
                    print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed ({info['info']}), skipping\033[0m")
                else:
                    print(f"\033[33m[✓]\033[0m \033[94mHttpx crawl already completed, skipping\033[0m")

        # STEP 5: Sensitive Data (Deep Scan Only)
        if mode == "deep":
            if not is_step_completed(target, "sensitive_data"):
                write_log(target, "sensitive_data", "processing")
                send_sensitive_files_to_telegram(target, sen_200_file, sen_403_file)
                write_log(target, "sensitive_data", count=0, info="sent to telegram")
            else:
                print(f"\033[33m[✓]\033[0m \033[94mSensitive data sending already completed, skipping\033[0m")

        # STEP 6: SecretFinder Scan (Deep Scan Only)
        if mode == "deep":
            if not is_step_completed(target, "secretfinder"):
                write_log(target, "secretfinder", "processing")
                js_count = 0
                if os.path.exists(js_output):
                    with open(js_output, "r", encoding="utf-8", errors="ignore") as f:
                        js_count = sum(1 for line in f if line.strip())
                if js_count > 0:
                    secretfinder_text = scan_js_with_secretfinder(target, js_output)
                    if secretfinder_text:
                        sec_finder_file = paths['sec_finder_file']
                        with open(sec_finder_file, "w", encoding="utf-8") as f:
                            f.write(secretfinder_text)
                        send_telegram_report(sec_finder_file, f"{target} - SecretFinder Results")
                else:
                    write_log(target, "secretfinder", count=0, info="no JS URLs found")
                    print(f"\033[94m[ℹ️] No JS URLs found, skipping SecretFinder scan\033[0m")
            else:
                info = get_step_info(target, "secretfinder")
                count_str = f" ({info['count']} secrets found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mSecretFinder already completed{count_str}, skipping\033[0m")

        # STEP 7: Nuclei Scans
        if mode == "dark":
            if not is_step_completed(target, "nuclei_js"):
                write_log(target, "nuclei_js", "processing")
                nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            else:
                info = get_step_info(target, "nuclei_js")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei JS scan already completed{count_str}, skipping\033[0m")

            if not is_step_completed(target, "nuclei_dast"):
                write_log(target, "nuclei_dast", "processing")
                nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
            else:
                info = get_step_info(target, "nuclei_dast")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei DAST scan already completed{count_str}, skipping\033[0m")

        elif mode == "deep":
            if not is_step_completed(target, "nuclei_basic"):
                write_log(target, "nuclei_basic", "processing")
                start_time = time.time()
                nuclei_without_parameter(target, active_file, nuclei_output_httpx, user_agent, scan_args)
                duration = time.time() - start_time
                hours, rem = divmod(int(duration), 3600)
                mins, secs = divmod(rem, 60)
                print(f"[⏱️] Nuclei basic scan completed in {hours}h {mins}m {secs}s")
            else:
                info = get_step_info(target, "nuclei_basic")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei basic scan already completed{count_str}, skipping\033[0m")

            if not is_step_completed(target, "nuclei_js"):
                write_log(target, "nuclei_js", "processing")
                nuclei_js_exposure(target, js_output, nuclei_output_js, user_agent, scan_args)
            else:
                info = get_step_info(target, "nuclei_js")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei JS scan already completed{count_str}, skipping\033[0m")

            if not is_step_completed(target, "nuclei_dast"):
                write_log(target, "nuclei_dast", "processing")
                nuclei_param_dast(target, param_output, nuclei_output_param, user_agent, scan_args)
            else:
                info = get_step_info(target, "nuclei_dast")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei DAST scan already completed{count_str}, skipping\033[0m")

            if not is_step_completed(target, "nuclei_takeover"):
                write_log(target, "nuclei_takeover", "processing")
                nuclei_takeover(subdomain_file, output_path_takeover, target)
            else:
                info = get_step_info(target, "nuclei_takeover")
                count_str = f" ({info['count']} found)" if info and info['count'] is not None else ""
                print(f"\033[33m[✓]\033[0m \033[94mNuclei takeover scan already completed{count_str}, skipping\033[0m")
        else:
            print(f"[!] Unknown scan mode: {mode}")
            return

        print(f"[✓] All processes completed for target: {target}")

def dark_deep(mode):
        targets = get_target_input_enhanced()

        # Create a wrapper function that includes the mode parameter
        def scan_wrapper(target, resume=False):
            dark_deep_target(mode, target, resume=resume)

        if len(targets) == 1:
            # Single target - original behavior
            target = targets[0]
            resume = False
            if has_previous_scan(target):
                resume_action = ask_continue_or_restart(target)
                if resume_action == 'continue':
                    resume = True
                elif resume_action == 'restart':
                    clear_target_log(target)
            dark_deep_target(mode, target, resume=resume)
        else:
            # Multiple targets - sequential scan
            scan_name = "Dark Scan" if mode == "dark" else "Deep Scan"
            process_target_list(targets, scan_wrapper, scan_name)

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
        # Simpan BOT_TOKEN & CHAT_ID lokal SEBELUM config.py ditimpa,
        # supaya kredensial tiap user tetap dipertahankan setelah update.
        saved_token = ""
        saved_chat = ""
        if os.path.exists("config.py"):
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    old_cfg = f.read()
                m = re.search(r'^BOT_TOKEN\s*=\s*"([^"]*)"', old_cfg, flags=re.MULTILINE)
                if m:
                    saved_token = m.group(1)
                m = re.search(r'^CHAT_ID\s*=\s*"([^"]*)"', old_cfg, flags=re.MULTILINE)
                if m:
                    saved_chat = m.group(1)
            except Exception:
                pass
        for file in file_list:
            source = os.path.join(TEMP_FOLDER, file)
            destination = file
            if os.path.exists(source):
                shutil.copy(source, destination)
                print(f"[✔] Updated: {file}")
        # Setelah config.py baru dari GitHub ditimpa, pulihkan BOT_TOKEN &
        # CHAT_ID milik user (kalau sebelumnya sudah terisi & bukan placeholder).
        if os.path.exists("config.py") and (saved_token or saved_chat):
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    new_cfg = f.read()
                if saved_token:
                    if re.search(r'^BOT_TOKEN\s*=\s*"([^"]*)"', new_cfg, flags=re.MULTILINE):
                        new_cfg = re.sub(r'^BOT_TOKEN\s*=\s*"[^"]*"',
                                         f'BOT_TOKEN = "{saved_token}"', new_cfg, flags=re.MULTILINE)
                    else:
                        new_cfg += f'\nBOT_TOKEN = "{saved_token}"\n'
                if saved_chat:
                    if re.search(r'^CHAT_ID\s*=\s*"([^"]*)"', new_cfg, flags=re.MULTILINE):
                        new_cfg = re.sub(r'^CHAT_ID\s*=\s*"[^"]*"',
                                         f'CHAT_ID = "{saved_chat}"', new_cfg, flags=re.MULTILINE)
                    else:
                        new_cfg += f'\nCHAT_ID = "{saved_chat}"\n'
                with open("config.py", "w", encoding="utf-8") as f:
                    f.write(new_cfg)
                print("[✔] config.py updated (BOT_TOKEN & CHAT_ID preserved)")
            except Exception as e:
                print(f"[⚠️] Could not restore config credentials: {e}")
        shutil.rmtree(TEMP_FOLDER)
        print(f"[✓] Update successful to version v{remote_version}")
        print("[🔁] Restarting tool...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"[❌] Failed to update: {e}")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LAZYHUNTER - Automation Recon Tool')
    parser.add_argument('--lightscan', '-lts', action='store_true', help='Run Light Scan (Subdomain + Httpx + Nuclei basic)')
    parser.add_argument('--darkscan', '-dks', action='store_true', help='Run Dark Scan (Subdomain + Httpx + Crawl + Nuclei js+DAST)')
    parser.add_argument('--deepscan', '-dps', action='store_true', help='Run Deep Scan (Subdomain + Httpx + Crawl + SensitiveData + SecretFinder + Nuclei 4 stages)')
    parser.add_argument('--takeover', '-tov', action='store_true', help='Run Subdomain Takeover Check')
    parser.add_argument('--sensitive', '-sens', action='store_true', help='Find Sensitive Data (Crawl + Httpx + Sensitive URLs + SecretFinder)')
    parser.add_argument('-t', '--target', type=str, help='Target domain for scanning')
    parser.add_argument('-tL', '--target-list', type=str, dest='target_list', help='File containing list of target domains (1 per line)')
    parser.add_argument('-list', '-l', type=str, help='File containing list of subdomains for takeover check')
    parser.add_argument('-speed', '-s', type=str, help='Scanning speed: low/standard/fast or 1/2/3')
    parser.add_argument('-ac', '--auto-continue', action='store_true', help='Auto continue previous scan if exists')
    parser.add_argument('-ar', '--auto-restart', action='store_true', help='Auto restart scan even if previous files exist')

    args = parser.parse_args()

    print_logo()
    # Pastikan setting config baru ada (tidak menyentuh BOT_TOKEN/CHAT_ID)
    ensure_config_settings()

    if any([args.lightscan, args.darkscan, args.deepscan, args.takeover, args.sensitive]):
        # Validate: need either -t (single target) or -tL (target list file)
        if args.takeover and args.list:
            pass  # Takeover mass mode uses -list flag, target not required
        elif not args.target and not args.target_list:
            print("[❌] Target is required when using scan options. Use -t/--target for single domain or -tL/--target-list for domain list file.")
            sys.exit(1)

        # Build targets list from -t or -tL
        cli_targets = []
        if args.target:
            cli_targets = [args.target]
        elif args.target_list:
            cli_targets = load_targets_from_file(args.target_list)
            if not cli_targets:
                print("[❌] No valid targets found in the target list file.")
                sys.exit(1)
            print(f"\033[33m[✓]\033[94m Loaded \033[93m{len(cli_targets)}\033[94m targets from \033[93m{args.target_list}\033[0m")

        speed_map = {'1': 'low', '2': 'standard', '3': 'fast'}
        speed_value = args.speed
        if speed_value in speed_map:
            speed_value = speed_map[speed_value]

        if speed_value:
            if speed_value not in ['low', 'standard', 'fast']:
                print("[❌] Invalid speed value. Use low/standard/fast or 1/2/3.")
                sys.exit(1)
            CMD_LINE_SPEED = speed_value

        # Helper: process single target with resume handling
        def _cli_single_scan(target, scan_func):
            resume_action = None
            if not args.auto_continue and not args.auto_restart:
                if has_previous_scan(target):
                    resume_mode = getattr(config, 'RESUME_SCAN_MODE', 'ask')
                    if resume_mode == 'ask':
                        resume_action = ask_continue_or_restart(target)
                    elif resume_mode == 'continue':
                        resume_action = 'continue'
                    elif resume_mode == 'restart':
                        resume_action = 'restart'
            elif args.auto_continue:
                resume_action = 'continue'
            elif args.auto_restart:
                resume_action = 'restart'

            if resume_action == 'restart':
                clear_target_log(target)
                scan_func(target, resume=False)
            elif resume_action == 'continue':
                scan_func(target, resume=True)
            else:
                scan_func(target, resume=False)

        # Helper: process multiple targets via process_target_list
        def _cli_multi_scan(targets, scan_func, scan_name):
            # For multi-target, use auto-resume mode if specified
            if args.auto_continue or args.auto_restart:
                resume_mode = 'continue' if args.auto_continue else 'restart'
                for target in targets:
                    # Skip target yang sudah selesai penuh (semua step completed).
                    # Dengan ini, batch scan ribuan target tak perlu menjalankan
                    # process yang sama dua kali, hanya karena resume step.
                    if resume_mode == 'continue' and not args.auto_restart and is_target_completed(target):
                        print(f"\033[33m[✓]\033[94m Target '{target}' sudah selesai, skipping.\033[0m")
                        continue
                    if resume_mode == 'restart' and has_previous_scan(target):
                        clear_target_log(target)
                    scan_func(target, resume=(resume_mode == 'continue'))
            else:
                process_target_list(targets, scan_func, scan_name)

        if args.lightscan:
            if len(cli_targets) == 1:
                _cli_single_scan(cli_targets[0], light_scan_target)
            else:
                _cli_multi_scan(cli_targets, light_scan_target, "Light Scan")
        elif args.darkscan or args.deepscan:
            mode = "dark" if args.darkscan else "deep"
            def scan_wrapper(target, resume=False):
                dark_deep_target(mode, target, resume=resume)
            if len(cli_targets) == 1:
                _cli_single_scan(cli_targets[0], scan_wrapper)
            else:
                scan_name = "Dark Scan" if mode == "dark" else "Deep Scan"
                _cli_multi_scan(cli_targets, scan_wrapper, scan_name)
        elif args.takeover:
            if args.list:
                output_name = args.target if args.target else None
                takeover_mass_file(args.list, output_name)
            else:
                if len(cli_targets) == 1:
                    _cli_single_scan(cli_targets[0], takeover_single)
                else:
                    _cli_multi_scan(cli_targets, takeover_single, "Subdomain Takeover")
        elif args.sensitive:
            if len(cli_targets) == 1:
                _cli_single_scan(cli_targets[0], find_sensitive_data)
            else:
                _cli_multi_scan(cli_targets, find_sensitive_data, "Find Sensitive Data")
    else:
        # Interactive mode: cek konfigurasi Telegram dulu sebelum menu
        check_telegram_config()
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
                targets = get_target_input_enhanced()
                if len(targets) == 1:
                    # Single target - original behavior
                    target = targets[0]
                    resume = False
                    if has_previous_scan(target):
                        resume_action = ask_continue_or_restart(target)
                        if resume_action == 'continue':
                            resume = True
                        elif resume_action == 'restart':
                            clear_target_log(target)
                    find_sensitive_data(target, resume=resume)
                else:
                    # Multiple targets - sequential scan
                    process_target_list(targets, find_sensitive_data, "Find Sensitive Data")
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

# ==============================================================================
# CHANGELOG
# ==============================================================================
# Update ke 1: Tambah by_target storage mode, hapus prefix target dari filename
# Update ke 2: Tambah comprehensive logging system, log-based resume, error logging
# Update ke 3: Fix httpx step naming (httpx_subd & httpx_crawl), tambah sensitive data + SecretFinder di deep scan, update menu deskripsi, update readme
# Update ke 4: Tambah lhmon.py (LazyHunter Monitor) - real-time process & network monitoring tool
# Update ke 5: Tambah list domain input support - semua scan mode support input file daftar domain (1 per line), scan berurutan per target. CLI flag -tL/--target-list. Interactive mode pilih Single Domain atau Domain List File.
