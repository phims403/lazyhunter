# LAZYHUNTER
is an automation tool for recon and scanning, designed for bug hunters who want to work quickly and efficiently. Suitable for both beginners and professionals.

---

## Main Features
### 1. Light Scan (Quick Scanning)
 - Subfinder → find subdomains from the target domain.

 - Httpx → filter active subdomains (HTTP response).

 - Nuclei → scan active subdomains using common templates such as:misconfiguration, exposure, default-login, panel, CVEs, CMS, files, DNS, SSL, token, backup, etc.

 - Scan speed can be adjusted (low/standard/fast).

 - Scan results are automatically sent to Telegram.

---

### 2. Deep Scan (In-depth Scanning)
   - Subfinder + Assetfinder → find as many subdomains as possible from the target.
   - Merge and remove duplicate results.
   - Httpx → validate active subdomains.
   - Nuclei stage 1 → initial scan using common templates such as:misconfiguration
   exposure, default-login, panel, CVEs, CMS, files, DNS, SSL, token, backup, etc.
   - Katana → URL crawling to find parameters from active subdomains.
   - Grep → filter URLs that have parameters (?key=value).
   - Nuclei stage 2 → scan crawled URLs to detect vulnerabilities such as XSS, SQLi, LFI.
   - Scan speed can be adjusted (low/standard/fast).
   - All nuclei results are automatically sent to Telegram.

---

### 3. Find Sensitive Data (Automatically Search for Sensitive Data)
 - Uses automatic duckduckgo dorking.
 - Dorks such as: site:target ext:env, .git/config, DB_PASSWORD, API_KEY, etc.
 - Detects configuration files, credentials, or important backups exposed to the
 public.
 - Results are saved to a text file.

---


### 4. Manual Dorking
 - Users input dorks manually.
 -  Performs search on duckduckgo.
 - Suitable for OSINT, specific searches, or unique files.
 - Results are saved to a file.
---

### 5. Subdomain Takeover Checker
Has two modes:
• Bulk → from subdomain list file.
• Wildcard → auto subdomain with subfinder.

 - Uses Nuclei with takeovers template to check for possible takeovers.
 - Scan results are sent to Telegram.

---

### 6. Generate Vulnerability Report
 - Input vulnerability title and validation steps (PoC).
 - Uses GPT API from OpenRouter to generate bug report.
 - Report includes: Title, Description, PoC, Impact, Mitigation, and Reporter Identity.
 - Report is sent to Telegram and saved.

---

### 7. Generate Report + Send via Email
 - Same as feature #6 but the report is not sent to Telegram, instead:
 - Report is directly sent via Gmail SMTP to a specified email address.
 - Suitable for direct reports to vendors/security teams.
---

• Telegram notifications• Automatic folder structure for scan results• Access to target lists from bug bounty platforms such as:
 - HackerOne
 - Bugcrowd
 - YesWeHack
 - Intigriti
 - HackenProof
# How to Use LAZYHUNTER
## 📦 1. Initial Requirements (Manual Installation)
Make sure you have installed:
- Go (Golang)
- Python 3
- pip

For Debian/Kali Linux:
```bash
sudo apt update
sudo apt install golang-go python3 python3-pip -y
```

---

📥 2. Install Python Dependencies
Install required Python libraries:
```bash
pip install -r requirements.txt
```

---

## ⚙️ 3. Install External Tools (ProjectDiscovery and others)
Use the setup.sh script to install tools automatically:
```bash
chmod +x setup.sh
./setup.sh
```
This script will:
Install:
- subfinder
- httpx
- nuclei
- katana
- assetfinder
- Automatically add Go binary path to your shell (permanent)

---

## 🚀 4. Jalankan LAZYHUNTER
Run LAZYHUNTER
Once everything is ready, run the tool with:
```bash
python lazyhunter.py
```
choose the desired feature

---

# DISCLAIMER!!!
## All activities performed by users of this tool are outside my responsibility. I am not responsible for any misuse of LAZYHUNTER for illegal or harmful activities.

## Users who use this tool are fully responsible for any actions performed with LAZYHUNTER. Use it wisely and responsibly.

---

##  • how to create a Telegram bot and get the token and chat id
### watch this
#### https://drive.google.com/file/d/1Kcy_tZXyWV4TxLk5Vq4pfyyiRkyKHxGo/view?usp=drivesdk

## • how to create a Gmail password for config.py
 - coming soon
