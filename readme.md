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
- **Waybackurls + Katana + Gau** → Crawling URLs with parameters and .js.
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
- **Httpx** → validate active URLs (200 + 403)
- **Separate URLs** with parameters, URLs (.js), and sensitive URLs (200/403)
- **Send sensitive data** → Send 200 OK and 403 Forbidden sensitive URLs to Telegram
- **SecretFinder** → Scan JS URLs for secrets and sensitive information
- **Nuclei stage 1** → scan active subdomains (common templates).
- **Nuclei stage 2** → scan URLs .js (exposure tag).
- **Nuclei stage 3** → scan URLs with parameters (dast templates).
- **Nuclei stage 4** → scan subdomains to check takeover potential.
- **Adjust scanning speed** (nuclei) → Available 3 options: Low, Standard, Fast.
- **Telegram notification** → All results are automatically sent to Telegram.

### 4. Find Sensitive Data (Automatic Sensitive Data Search)
- **Subfinder + Assetfinder** → find subdomains
- **Httpx** → validate active subdomains (200)
- **Waybackurls + Katana + Gau** → Crawling URLs with parameters and .js.
- **Httpx** → validate active URLs (200 + 403)
- **Separate URLs** into param, js, sensitive 200 OK, and sensitive 403
- **Send sensitive files** → Send 200 OK and 403 Forbidden sensitive URLs to Telegram
- **SecretFinder** → Scan JS URLs for secrets and sensitive information

### 5. Subdomain Takeover Checker
- **Has two modes**:
  - Mass → from subdomain list file.
  - Wildcard → auto subdomain with subfinder + assetfinder.
- **Using Nuclei** with `takeover` tag (severity low+) to check for possible takeover.
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
- **Batch Scan from File**: `python lazyhunter.py -dps -tL targets.txt -s standard`

### Available Flags
- `--lightscan` or `-lts`: Run Light Scan (Subdomain + Httpx + Nuclei basic)
- `--darkscan` or `-dks`: Run Dark Scan (Subdomain + Httpx + Crawl + Nuclei js+DAST)
- `--deepscan` or `-dps`: Run Deep Scan (Subdomain + Httpx + Crawl + SensitiveData + SecretFinder + Nuclei 4 stages)
- `--takeover` or `-tov`: Run Subdomain Takeover Check
- `--sensitive` or `-sens`: Find Sensitive Data (Crawl + Httpx + Sensitive URLs + SecretFinder)
- `-t` or `--target`: Specify target domain for scanning
- `-list` or `-l`: Specify file containing list of subdomains for takeover check
- `-speed` or `-s`: Specify scanning speed (low/standard/fast or 1/2/3)
- `-ac` or `--auto-continue`: Auto continue previous scan if exists
- `-ar` or `--auto-restart`: Auto restart scan even if previous files exist
- `-tL` or `--target-list`: File containing list of target domains (1 per line) for batch scanning

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

- **Telegram Notification**: All scan results are automatically sent to Telegram
- **Log-based Resume System**: Every scan step is logged with completion status and result counts. On resume, the tool checks logs (not file existence) to skip completed steps. Logs are stored in `logs/` folder, one file per target. Steps marked as "processing" (incomplete) are automatically retried on resume.
- **SecretFinder Dual Mode**: Choose between direct URL scanning or local download to `js-saved/` folder for offline analysis with AI/other tools.
- **Storage Mode**: Two modes available, configurable via Setup menu or config.py:
  - **by_type** (default): Files organized by type in separate folders (subdomain/, active/, nuclei/, etc.)
  - **by_target**: All files for a target in one folder (target_output/{target}/)
- **Automatic folder structure**: Organized results in dedicated folders
- **Access to target lists**: From bug bounty platforms such as:
  - hackerone
  - bugcrowd
  - yeswehack
  - intigriti
  - hackenproof

---

## Output File Structure

LAZYHUNTER supports two storage modes. The output structure depends on the selected mode:

### Mode: by_type (default)

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
│   ├── 📄 wayback_redacted.com.txt             → URLs from Wayback Machine
│   ├── 📄 gau_redacted.com.txt                 → URLs from GAU (GetAllUrls)
│   ├── 📄 katana_redacted.com.txt              → URLs from Katana crawler
│   └── 📄 crawled_filtered_redacted.com.txt    → Combined & filtered crawled URLs
│
├── 📁 crawled_filtered/
│   ├── 📄 param_redacted.com.txt               → URLs with parameters
│   └── 📄 js_redacted.com.txt                  → JavaScript files (.js)
│
├── 📁 nuclei/
│   ├── 📄 nuc_active_redacted.com.txt          → Common vulnerabilities found (Light/Deep)
│   ├── 📄 nuc_exp_redacted.com.txt             → JS exposure scan results
│   ├── 📄 nuc_dast_redacted.com.txt            → DAST vulnerabilities (param-based)
│   └── 📄 TOW_redacted.com.txt                 → Subdomain takeover results (Deep only)
│
├── 📁 take_over/
│   └── 📄 takeover_redacted.com.txt             → Takeover scan results
│
├── 📁 sensitive_data/
│   ├── 📄 200_sens_redacted.com.txt            → Sensitive URLs (HTTP 200)
│   ├── 📄 403_sens_redacted.com.txt            → Sensitive URLs (HTTP 403)
│   ├── 📄 sec_finder_redacted.com.txt          → SecretFinder scan results
│   ├── 📄 pot_sen_url_redacted.com.txt         → Potential sensitive URLs
│   └── 📄 sen_url_redacted.com.txt             → Active sensitive URLs
│
└── 📁 logs/
    └── 📄 redacted.com.txt                     → Scan progress log (resume data)
```

### Mode: by_target

```
lazyhunter/
│
└── 📁 target_output/
    └── 📁 redacted.com/
        ├── 📄 subdomains.txt                   → All discovered subdomains
        ├── 📄 active.txt                       → Active subdomains (HTTP 200)
        ├── 📄 wayback.txt                      → URLs from Wayback Machine
        ├── 📄 gau.txt                          → URLs from GAU (GetAllUrls)
        ├── 📄 katana.txt                       → URLs from Katana crawler
        ├── 📄 crawled_filtered.txt             → Combined & filtered crawled URLs
        ├── 📄 param.txt                        → URLs with parameters
        ├── 📄 js.txt                           → JavaScript files (.js)
        ├── 📄 nuc_active.txt                   → Common vulnerabilities found
        ├── 📄 nuc_exp.txt                      → JS exposure scan results
        ├── 📄 nuc_dast.txt                     → DAST vulnerabilities (param-based)
        ├── 📄 takeover.txt                     → Subdomain takeover results
        ├── 📄 200_sens.txt                     → Sensitive URLs (HTTP 200)
        ├── 📄 403_sens.txt                     → Sensitive URLs (HTTP 403)
        ├── 📄 sec_finder.txt                   → SecretFinder scan results
        ├── 📄 pot_sen_url.txt                  → Potential sensitive URLs
        ├── 📄 sen_url.txt                      → Active sensitive URLs
        │
        └── 📁 ../logs/
            └── 📄 redacted.com.txt             → Scan progress log (resume data)
```

### Mode: local (SecretFinder only)

When `SECRETFINDER_MODE` is set to `local`, JS files are downloaded into:

```
lazyhunter/
│
└── 📁 js-saved/
    └── 📁 redacted.com/
        └── 📁 sub.domain.com/
            ├── 📄 static/js/app.js             → Downloaded JS file (original URL path preserved)
            └── 📄 _next/static/chunks/abc.js   → Can be analyzed with AI / grep / manual review
```

### 🔧 How to Reuse Output Files

The generated files are designed for **reusability in further reconnaissance**:

| File Type | Use Case | Tools |
|-----------|----------|-------|
| **active.txt** | Target list for additional scans | nuclei, ffuf, naabu |
| **param.txt** | Parameter-based vulnerability scanning | dalfox, qxref, arjun |
| **js.txt** | JavaScript analysis for sensitive info | JSLinkScan, GAP |
| **wayback/gau/katana.txt** | URL enumeration & endpoint discovery | Additional analysis |
| **nuc_*.txt** | Vulnerability triage & prioritization | Manual testing |
| **200_sens/403_sens.txt** | Sensitive data exposure investigation | Manual testing |
| **sec_finder.txt** | Secret/credential leak analysis | Manual testing |

**Examples of further analysis:**
```bash
# Check for XSS in parameter URLs
cat target_output/example.com/param.txt | dalfox pipe

# Find sensitive info in JavaScript files
cat target_output/example.com/js.txt | while read url; do curl -s $url | grep -i "api_key\|token\|password"; done

# Fuzzing active subdomains
cat target_output/example.com/active.txt | ffuf -w - -u http://FUZZ -mc 200
```

### 🤖 Hunting with AI Agents

The output files are also perfect as an **attack surface for AI-powered bug bounty hunting**. Instead of manually analyzing every file, you can let an AI agent (Claude Code, Command Code, OpenCode, etc.) do the exhaustive hunting for you.

**Quick start:**
1. Run a Deep Scan on your target: `python lazyhunter.py -dps -t example.com -s fast`
2. Open the bundled AI hunting prompts in the **`prompt/`** folder
3. Follow the instructions in **`prompt/readme.md`** (or `prompt/readme-id.md` for Indonesian) — adjust the main prompt path & target, then run it with an AI agent that supports the `/goal` autonomous-loop feature (e.g. Command Code)

The AI will read the LazyHunter output files (subdomains, active hosts, crawled URLs, params, JS files, sensitive data, nuclei results) as its attack surface, create a workspace, and hunt exhaustively — with support for continuing across multiple sessions.

> 📌 **Tip:** for long autonomous hunting sessions, use a cost-effective model like `deepseek-v4-flash` — good quality, low cost.

---

### 📊 Public Bug Bounty Programs Domains

| File                             | Number of domains |
|----------------------------------|-------------------|
| hackerone_bounty.txt             | 769 domains       |
| hackerone_swag_vdp.txt           | 656 domains       |
| bugcrowd_bounty.txt              | 255 domains       |
| bugcrowd_swag_vdp.txt            | 183 domains       |
| hackenproof_bounty.txt           | 86 domains        |
| yeswehack_bounty.txt             | 68 domains        |
| intigriti_bounty.txt             | 45 domains        |
| intigriti_swag_vdp.txt           | 23 domains        |
| immunefi_bounty.txt              | 5 domains         |
| bugv_bounty.txt                  | 8 domains         |
| bugbase_bounty.txt               | 3 domains         |
| self_hosted_program_bounty.txt   | 354 domains       |
| self_hosted_program_swag_vdp.txt | 1,625 domains     |

Total: 4,080 domains across 13 files

Source: [https://github.com/projectdiscovery/public-bugbounty-programs](https://github.com/projectdiscovery/public-bugbounty-programs)

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
Then select the desired feature:
```
  [0]  Feature Information
  [1]  Light Scan
  [2]  Dark Scan
  [3]  Deep Scan (TOP FEATURE)
  [4]  Subdomain Takeover
  [5]  Find Sensitive Data
  [9]  Setup Configuration
  [99] Out
  [999] Update Tool
```

On first run, if the Telegram **Bot Token** and/or **Chat ID** are not set yet, the tool shows a confirmation before the menu:
- Press **Enter** → continue without Telegram notifications
- Press **f** → go straight to setup the missing values (with format validation and a pointer to `readme.md` for the BotFather guide)

### Skip Current Step
While a scan step is running (subfinder, httpx, crawler, nuclei, etc.), you can **skip it** and keep partial data:
- Press **`s`** then **Enter** while a step is running.
- The running tool is killed, partial results are kept, and the scan moves to the next step.
- Skipped steps are logged as `skipped` (not `completed`), so a resume will re-run them.
- The skip key is polled non-blockingly, so it responds instantly even when the tool prints nothing.

### Command Line Mode
For quick scans without entering the menu:
```bash
python lazyhunter.py -dps -t example.com -s fast
```

### Resume Scan
If a previous scan exists for the same target, the tool will ask whether to **continue** (resume from last step) or **restart** (clear logs and start over). This works for all scan types.

You can also use flags:
```bash
# Auto continue previous scan
python lazyhunter.py -dps -t example.com -ac

# Auto restart scan
python lazyhunter.py -dps -t example.com -ar
```

---

## ⚙️ Setup Configuration

The tool provides a Setup menu (option 9) with the following settings:

| Setting | Description | Options |
|---------|-------------|---------|
| **Bot Token** | Telegram bot token for notifications | Your Telegram bot token |
| **Chat ID** | Telegram chat ID for notifications | Your Telegram chat ID |
| **Scan Speed** | Default scanning speed | low / standard / fast |
| **Katana Limit** | Max subdomains processed by Katana | Number or "00" for unlimited |
| **Resume Mode** | What to do when previous scan exists | ask / continue / restart |
| **Storage Mode** | How output files are organized | by_type / by_target |
| **SecretFinder Mode** | How JS secrets scanning works | direct (scan URL) / local (download to js-saved/) |

---

## 📝 Changelog

### v1.5 (latest)
- **Telegram config check at startup**: if Bot Token / Chat ID are missing, the tool asks before the menu — continue without Telegram (Enter) or fix now (`f`)
- **Setup format validation**: invalid Bot Token / Chat ID are rejected with a clear warning + pointer to `readme.md`, and re-prompted until correct or skipped
- **Skip step (`s` + Enter)**: skip any running step and keep partial data; skipped steps are logged as `skipped` (not `completed`) so resume re-runs them; non-blocking key polling — responds instantly even when a tool prints nothing
- **Batch skip of finished targets** in `-tL` mode (`is_target_completed()`)
- **Crash-proof Telegram**: all `requests.post` calls to Telegram are wrapped in try/except — an offline/blocked Telegram no longer kills the whole scan
- **Stricter sensitive-extension matching**: `has_sensitive_ext()` matches extension at end of URL path only (no more `/login` → `.log` false positives)
- **Error-handling hardening**: `FileNotFoundError`/`OSError` caught for all external tools; `shutil.copy/move` guarded when crawler output files are missing; return codes of nuclei/takeover are checked (failures no longer logged as completed)
- **Menu cleanup**: feature descriptions removed; social media URLs in the banner shown without protocol (`instagram.com/phimzz`, `t.me/phimssec`, ...)
- **Misc fixes**: `os.execv` uses `sys.executable`; version check timeout reduced (3s) and no longer spams debug output; file-handle leaks in `Popen` stdout closed properly

### v1.4 (initial public)
- Light / Dark / Deep scans, Sensitive Data finder, Subdomain Takeover checker
- Log-based resume system, storage modes (`by_type`/`by_target`), SecretFinder dual mode, CLI flags, setup menu, auto-update

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