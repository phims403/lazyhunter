#!/bin/bash

echo "══════════════════════════════════════════════"
echo " LAZYHUNTER Setup Script - Install Tools"
echo "══════════════════════════════════════════════"

# 1. Cek apakah Go sudah terinstal
echo "[*] Memastikan Go terinstal..."
if ! command -v go &> /dev/null; then
    echo "[❌] Go belum terinstal. Silakan install Go terlebih dahulu."
    exit 1
fi

# 2. Install semua tool berbasis Go
echo "[*] Menginstall tools ProjectDiscovery dan lainnya..."

GO_TOOLS=(
    "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    "github.com/projectdiscovery/httpx/cmd/httpx@latest"
    "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    "github.com/projectdiscovery/katana/cmd/katana@latest"
    "github.com/tomnomnom/assetfinder@latest"
)

for tool in "${GO_TOOLS[@]}"; do
    echo "[+] Installing: $tool"
    go install -v "$tool"
done

# 3. Tambahkan $HOME/go/bin ke PATH sementara
GO_BIN_PATH="$HOME/go/bin"
export PATH="$PATH:$GO_BIN_PATH"

# 4. Deteksi shell dan tambahkan PATH secara permanen
echo "[*] Mendeteksi shell untuk menambahkan PATH permanen..."

SHELL_NAME=$(basename "$SHELL")
USER_HOME="$HOME"

case "$SHELL_NAME" in
  bash)
    CONFIG_FILE="$USER_HOME/.bashrc"
    ;;
  zsh)
    CONFIG_FILE="$USER_HOME/.zshrc"
    ;;
  fish)
    CONFIG_FILE="$USER_HOME/.config/fish/config.fish"
    ;;
  *)
    echo "[⚠] Shell '$SHELL_NAME' tidak dikenali. Tambahkan PATH secara manual:"
    echo "    export PATH=\$PATH:$GO_BIN_PATH"
    CONFIG_FILE=""
    ;;
esac

if [ -n "$CONFIG_FILE" ]; then
  if ! grep -q "$GO_BIN_PATH" "$CONFIG_FILE"; then
    echo "[+] Menambahkan PATH ke $CONFIG_FILE"
    if [ "$SHELL_NAME" = "fish" ]; then
      echo "set -gx PATH \$PATH $GO_BIN_PATH" >> "$CONFIG_FILE"
    else
      echo "export PATH=\$PATH:$GO_BIN_PATH" >> "$CONFIG_FILE"
    fi
    echo "[✔] PATH berhasil ditambahkan ke $CONFIG_FILE (permanen)"
  else
    echo "[✓] PATH ke $GO_BIN_PATH sudah ada di $CONFIG_FILE"
  fi
fi

echo "══════════════════════════════════════════════"
echo "[✔] Setup selesai. Tools sudah terinstal."
echo "[!] Buka ulang terminal atau jalankan:"
echo "    source $CONFIG_FILE"
echo "untuk mengaktifkan PATH permanen."
echo "══════════════════════════════════════════════"
