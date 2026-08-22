# config.py
# Telegram Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"



KATANA_LIMIT = 5

# Resume scan configuration
# Options: "ask" (always ask), "continue" (auto continue), "restart" (auto restart)
RESUME_SCAN_MODE = "ask"

# Scan speed
SCAN_SPEED = "standard"

# Storage mode configuration
# Options: "by_type" (each type in separate folder) or "by_target" (all files in one folder per target)
STORAGE_MODE = "by_target"


# SecretFinder mode: "direct" (scan URL directly) or "local" (download JS to js-saved/ folder)
SECRETFINDER_MODE = "direct"

# NOTE: DO NOT CHANGE ABOVE THIS!!!
# GitHub Configuration (for tool updates)
GITHUB_USER = "phims403"
GITHUB_REPO = "lazyhunter"

