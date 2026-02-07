# LAZYHUNTER
is an automation recon tool for bug hunters who want to work fast and efficiently. Designed for both beginners and professionals.

---

## Main Features

### 1. Light Scan (Fast Recon)
- **Subfinder + Assetfinder** → find subdomains
- **Httpx** → validate active subdomains (200)
- **Nuclei** → scanning active subdomains using common templates like: misconfiguration, exposure, default-login, panel, cves, cms, files, dns, ssl, token, backup, etc.
- **Scan speed** can be adjusted (low/standard/fast).
- **Telegram notification** → Scan results are automatically sent to Telegram.

### 2. Dark Scan (Medium Recon)
- **Subfinder + Assetfinder** → find subdomains
- **Httpx** → validate active subdomains (200)
- **Katana + Gau** → Crawling URLs with parameters and .js.
- **Httpx** → validate active URLs (200)
- **Separate URLs** with parameters and URLs (.js)
- **Nuclei stage 1** → scan URLs .js (exposure tag).
- **Nuclei stage 2** → scan URLs with parameters (dast templates).
- **Adjust scanning speed** (nuclei) → Available 3 options: Low, Standard, Fast.
- **Telegram notification** → All results are automatically sent to Telegram.

### 3. Deep Scan (In-depth Recon)
- **Subfinder + Assetfinder** → find subdomains
- **Httpx** → validate active subdomains (200)
- **Waybackurls + Katana + Gau** → Crawling URLs with parameters and .js.
- **Httpx** → validate active URLs (200)
- **Separate URLs** with parameters and URLs (.js)
- **Nuclei stage 1** → scan active subdomains (common templates).
- **Nuclei stage 2** → scan URLs .js (exposure tag).
- **Nuclei stage 3** → scan URLs with parameters (dast templates).
- **Nuclei stage 4** → scan subdomains to check takeover potential.
- **Adjust scanning speed** (nuclei) → Available 3 options: Low, Standard, Fast.
- **Telegram notification** → All results are automatically sent to Telegram.

### 4. Find Sensitive Data (Automatic Sensitive Data Search)
- **Crawling URLs** using gau to collect URLs with sensitive extensions.
- **Filter URLs** containing extensions: .zip, .tar, .gz, .7z, .rar, .bak, .backup, .old, .sql, .db, .sqlite, .env, .log, .conf, .config, .ini, .cfg, .xml, .json, .js
- **Test filtered URLs** with Httpx to identify active sensitive resources.
- **Detect configuration files**, credentials, or important backups that are publicly exposed.
- **Results** are saved to text file.

### 5. Subdomain Takeover Checker
- **Has two modes**:
  - Mass → from subdomain list file.
  - Wildcard → auto subdomain with subfinder + assetfinder.
- **Using Nuclei** with `takeovers` template to check for possible takeover.
- **Telegram notification** → Scan results sent to Telegram.

---

## Command Line Interface (CLI) Features

### Quick Scanning with Flags
The tool now supports command-line flags for quick scanning without entering the interactive menu:

- **Light Scan**: `python lazyhunter.py -lts -t example.com -s fast`
- **Dark Scan**: `python lazyhunter.py -dks -t example.com -s standard`
- **Deep Scan**: `python lazyhunter.py -dps -t example.com -s low`
- **Takeover Check**: 
  - Wildcard: `python lazyhunter.py -tov -t example.com -s fast`
  - Mass from file: `python lazyhunter.py -tov -l subdomains.txt -s standard`
- **Sensitive Data**: `python lazyhunter.py -sens -t example.com -s fast`

### Available Flags
- `--lightscan` or `-lts`: Run Light Scan
- `--darkscan` or `-dks`: Run Dark Scan
- `--deepscan` or `-dps`: Run Deep Scan
- `--takeover` or `-tov`: Run Subdomain Takeover Check
- `--sensitive` or `-sens`: Find Sensitive Data
- `-t` or `--target`: Specify target domain for scanning
- `-list` or `-l`: Specify file containing list of subdomains for takeover check
- `-speed` or `-s`: Specify scanning speed (low/standard/fast or 1/2/3)

### Flexible Speed Control
- **Session-based speed**: Use `-s` flag to set speed only for the current session without modifying config.py
- **Config-based speed**: If no speed flag is provided, the tool uses the speed setting from config.py
- **Fallback**: If no speed is configured, defaults to "standard" speed

### Dynamic Configuration Updates
- **Real-time config reload**: The tool reloads config.py before sending Telegram notifications and before crawling with Katana
- **On-the-fly changes**: Users can modify bot token, chat ID, and Katana limit while the tool is running
- **Unlimited Katana**: Use value "00" for unlimited subdomain processing (stored as -1 in config)

---

## Key Features

• **Telegram Notification**: All scan results are automatically sent to Telegram
• **Automatic folder structure**: Organized results in dedicated folders
• **Access to target lists**: From bug bounty platforms such as:
  - hackerone
  - bugcrowd
  - yeswehack
  - intigriti
  - hackenproof

---

## Output File Structure

LAZYHUNTER creates organized output files for each scan. Here's the structure:

```
lazyhunter/
│
├── 📁 subdomain/
│   └── 📄 redacted.com.txt                    → All discovered subdomains
│
├── 📁 active/
│   └── 📄 active_redacted.com.txt              → Active subdomains (HTTP 200)
│
├── 📁 crawled/
│   ├── 📄 katana_redacted.com.txt             → URLs from Katana crawler
│   ├── 📄 gau_redacted.com.txt                → URLs from GAU (GetAllUrls)
│   └── 📄 wayback_redacted.com.txt             → URLs from Wayback Machine (Deep Scan only)
│
├── 📁 crawled_filtered/
│   ├── 📄 param_redacted.com.txt              → URLs with parameters
│   └── 📄 js_redacted.com.txt                 → JavaScript files (.js)
│
├── 📁 nuclei/
│   ├── 📄 nuclei_common_redacted.com.txt      → Common vulnerabilities found
│   ├── 📄 nuclei_exposure_redacted.com.txt    → Sensitive data exposures
│   ├── 📄 nuclei_dast_redacted.com.txt        → DAST vulnerabilities (param-based)
│   └── 📄 nuclei_takeover_redacted.com.txt     → Subdomain takeover results (Deep Scan only)
│
├── 📁 take_over/
│   └── 📄 takeover_redacted.com.txt            → Takeover scan results
│
└── 📁 sensitive_data/
    └── 📄 sensitive_redacted.com.txt           → Discovered sensitive files
```

### 🔧 How to Reuse Output Files

The generated files are designed for **reusability in further reconnaissance**:

| File Type | Use Case | Tools |
|-----------|----------|-------|
| **active_redacted.com.txt** | Target list for additional scans | nuclei, ffuf, naabu |
| **param_redacted.com.txt** | Parameter-based vulnerability scanning | dalfox, qxref, arjun |
| **js_redacted.com.txt** | JavaScript analysis for sensitive info | JSLinkScan, GAP |
| **katana/gau/wayback_*.txt** | URL enumeration & endpoint discovery | Additional analysis |
| **nuclei_*.txt** | Vulnerability triage & prioritization | Manual testing |

**Examples of further analysis:**
```bash
# Check for XSS in parameter URLs
cat crawled_filtered/param_redacted.com.txt | dalfox pipe

# Find sensitive info in JavaScript files
cat crawled_filtered/js_redacted.com.txt | while read url; do curl -s $url | grep -i "api_key\|token\|password"; done

# Fuzzing active subdomains
cat active/active_redacted.com.txt | ffuf -w - -u http://FUZZ -mc 200
```

---

### 📊 Public Bug Bounty Programs Domains

| File                             | Number of domains |
|----------------------------------|-------------------|
| hackerone_bounty.txt             | 769 domains       |
| hackerone_swag_vdp.txt           | 656 domains       |
| bugcrowd_bounty.txt              | 255 domains       |
| bugcrowd_swag_vdp.txt            | 183 domains       |
| hackenproof_bounty.txt           | 86 domains        |
| hackenproof_swag_vdp.txt         | 0 domains (empty) |
| yeswehack_bounty.txt             | 68 domains        |
| yeswehack_swag_vdp.txt           | 0 domains (empty) |
| intigriti_bounty.txt             | 45 domains        |
| intigriti_swag_vdp.txt           | 23 domains        |
| immunefi_bounty.txt              | 5 domains         |
| immunefi_swag_vdp.txt            | 0 domains (empty) |
| bugv_bounty.txt                  | 8 domains         |
| bugv_swag_vdp.txt                | 0 domains (empty) |
| bugbase_bounty.txt               | 3 domains         |
| bugbase_swag_vdp.txt             | 0 domains (empty) |
| self_hosted_program_bounty.txt   | 354 domains       |
| self_hosted_program_swag_vdp.txt | 1,625 domains     |

Total: 4,430 domains across 18 files

source: https://github.com/projectdiscovery/public-bugbounty-programs

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
  - waybackurls
  - httpx
  - nuclei
- Add Go binary path to your shell automatically (permanently)

---

## 🚀 3. Run LAZYHUNTER

### Interactive Mode
Once everything is ready, run the tool with:
```bash
python lazyhunter.py
```
select the desired feature

### Command Line Mode
For quick scans without entering the menu:
```bash
python lazyhunter.py -dps -t example.com -s fast
```

---

# DISCLAIMER!!!
## Any activities carried out by users of this tool are outside my responsibility. I am not responsible for any misuse of LAZYHUNTER for illegal and harmful activities to others.
## Users who use this tool are fully responsible for the actions taken with LAZYHUNTER, Use it wisely and responsibly.

---

## • How to create Telegram bot and get token and chat id
### watch this
#### https://drive.google.com/file/d/12J-PEJcvJuv7PpX1DXBWQOCIQFcMIyeu/view?usp=drivesdk

## • How to create Gmail password for config.py
### watch this
#### https://drive.google.com/file/d/12F5cYBm8b5KVKkKmsa_1Yenfrqvcv5IG/view?usp=drivesdk

---

## Join Our Community

![Discord QR Code](img/discord-lazyhunter.jpg)

**Join our Discord community to:**
- Get help with LAZYHUNTER
- Share your findings and techniques
- Connect with other bug hunters
- Stay updated with latest features

[**Join Discord Server**](https://discord.gg/3CCMExvAZ)

---

## Support This Project
If you find this tool useful and want to support its development, you can contribute via Bitcoin:

**Bitcoin Address**: `bc1qlnqz4gfp454ym46km9v8hlmsqhj6g3p5fkqhm0`

Your support helps maintain and improve this open-source tool for the bug bounty community!

Note: This repository is maintained by volunteers and donations are appreciated but not required to use the tool.
