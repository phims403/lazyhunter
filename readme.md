# LAZYHUNTER
is an automation recon tool for bug hunters who want to work fast and efficiently. Designed for both beginners and professionals.
 
---
 
## Main Features
### 1. Light Scan (Fast Recon)
    - Subfinder + Assetfinder → find subdomains
    - Httpx → validate active subdomains (200)
    - Nuclei → scanning active subdomains using common templates like:
    misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, etc.
    - Scan speed can be adjusted (low/standard/fast).
    - Scan results are automatically sent to Telegram.

---

### 2. Dark Scan (Medium Recon)
    - Subfinder + Assetfinder → find subdomains
    - Httpx → validate active subdomains (200)
    - Katana + Gau → Crawling URLs with parameters and .js.
    - Httpx → validate active URLs (200)
    - Separate URLs with parameters and URLs (.js)
    - Nuclei stage 1: scan URLs .js (exposure tag).
    - Nuclei stage 2: scan URLs with parameters (dast templates).
    - Adjust scanning speed (nuclei) → Available 3 options: Low, Standard, Fast.
    - All results are automatically sent to Telegram.

---

### 3. Deep Scan (In-depth Recon)
    - Subfinder + Assetfinder → find subdomains
    - Httpx → validate active subdomains (200)
    - Waybackurls + Katana + Gau → Crawling URLs with parameters and .js.
    - Httpx → validate active URLs (200)
    - Separate URLs with parameters and URLs (.js)
    - Nuclei stage 1: scan active subdomains (common templates).
    - Nuclei stage 2: scan URLs .js (exposure tag).
    - Nuclei stage 3: scan URLs with parameters (dast templates).
    - Nuclei stage 4: scan subdomains to check takeover potential.
    - Adjust scanning speed (nuclei) → Available 3 options: Low, Standard, Fast.
    - All results are automatically sent to Telegram.

---

### 4. Find Sensitive Data (Automatic Sensitive Data Search)
    - Using crawling results from previous gau process to identify URLs with sensitive extensions.
    - Filter URLs containing extensions: .zip, .tar, .gz, .7z, .rar, .bak, .backup, .old, .sql, .db, .sqlite, .env, .log, .conf, .config, .ini, .cfg, .xml, .json, .js
    - Test filtered URLs with Httpx to identify active sensitive resources.
    - Detect configuration files, credentials, or important backups that are publicly exposed.
    - Results are saved to text file.

---

### 5. Subdomain Takeover Checker
    - Has two modes:
      • Mass → from subdomain list file.
      • Wildcard → auto subdomain with subfinder + assetfinder.
    - Using Nuclei with `takeovers` template to check for possible takeover.
    - Scan results sent to Telegram.

---

# How to Use LAZYHUNTER
## 📦 1. Installation Using Git Clone
First, clone the repository from GitHub:
```bash
git clone https://github.com/phims403/lazyhunter.git
cd lazyhunter
```

## ⚙️ 2. Automatic Installation Using setup.sh
Simply use the setup.sh script to install all requirements automatically:
```bash
chmod +x setup.sh
./setup.sh
```

The script will:
- Install Python and Go (Golang) if not already installed
- Install all Python dependencies from requirements.txt
- Install required external tools:
  - subfinder
  - assetfinder
  - katana
  - gau
  - httpx
  - nuclei
- Add Go binary path to your shell automatically (permanently)

---

## 🚀 3. Run LAZYHUNTER
Once everything is ready, run the tool with:
```bash
python lazyhunter.py
```
select the desired feature

---

# DISCLAIMER!!!
## Any activities carried out by users of this tool are outside my responsibility. I am not responsible for any misuse of LAZYHUNTER for illegal and harmful activities to others.
## Users who use this tool are fully responsible for the actions taken with LAZYHUNTER, Use it wisely and responsibly.

---

##  • how to create telegram bot and get token and chat id
### watch this
#### https://drive.google.com/file/d/12J-PEJcvJuv7PpX1DXBWQOCIQFcMIyeu/view?usp=drivesdk

## • how to create gmail password for config.py
### watch this
#### https://drive.google.com/file/d/12F5cYBm8b5KVKkKmsa_1Yenfrqvcv5IG/view?usp=drivesdk
---
