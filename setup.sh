#!/bin/bash

echo "══════════════════════════════════════════════"
echo " LAZYHUNTER Setup Script - Install Tools"
echo "══════════════════════════════════════════════"


version_lt() {
    [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" != "$2" ]
}


detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        elif [ -f /etc/arch-release ]; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}


install_python_pip() {
    echo "[*] Installing Python & pip..."
    OS=$(detect_os)
    
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        "redhat")
            sudo yum install -y python3 python3-pip
            ;;
        "arch")
            sudo pacman -S --noconfirm python python-pip
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install python3
            else
                echo "[!] Homebrew not found. Please install Homebrew first:"
                echo "    /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                return 1
            fi
            ;;
        *)
            echo "[!] OS not supported for automatic installation. Please install Python & pip manually."
            echo "    Python: https://www.python.org/downloads/"
            return 1
            ;;
    esac
    
    if command -v python3 &> /dev/null && command -v pip3 &> /dev/null; then
        echo "[✓] Python & pip successfully installed"
        python3 --version
        pip3 --version
    else
        echo "[❌] Failed to install Python & pip"
        return 1
    fi
}


install_golang() {
    echo "[*] Installing latest Golang from official website..."
    
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        armv7l) ARCH="armv6l" ;;
        *) 
            echo "[!] Architecture $ARCH not supported. Install manually from: https://go.dev/dl/"
            return 1
            ;;
    esac
    
    OS=$(detect_os)
    case $OS in
        "debian"|"redhat"|"arch"|"linux")
            OS="linux"
            ;;
        "macos")
            OS="darwin"
            ;;
        *)
            echo "[!] OS not supported for automatic installation. Install manually from: https://go.dev/dl/"
            return 1
            ;;
    esac
    
    echo "[*] Checking latest Go version..."
    LATEST_VERSION=$(curl -s https://go.dev/VERSION?m=text)
    if [ -z "$LATEST_VERSION" ]; then
        echo "[!] Failed to get latest version. Using default."
        LATEST_VERSION="go1.23.4"
    fi
    
    VERSION_NUM=${LATEST_VERSION#go}
    FILENAME="${LATEST_VERSION}.${OS}-${ARCH}.tar.gz"
    DOWNLOAD_URL="https://go.dev/dl/${FILENAME}"
    
    echo "[*] Downloading Go ${LATEST_VERSION} for ${OS}-${ARCH}..."
    echo "    URL: $DOWNLOAD_URL"
    
    if ! wget --quiet --show-progress "$DOWNLOAD_URL" -O "/tmp/${FILENAME}"; then
        echo "[❌] Failed to download Go. Check internet connection or try manually:"
        echo "    $DOWNLOAD_URL"
        return 1
    fi
    
    echo "[✓] Download successful"
    
    if [ -d "/usr/local/go" ]; then
        echo "[*] Removing old Go installation..."
        sudo rm -rf /usr/local/go
    fi
    
    echo "[*] Extracting Go to /usr/local..."
    if ! sudo tar -C /usr/local -xzf "/tmp/${FILENAME}"; then
        echo "[❌] Failed to extract Go"
        return 1
    fi
    
    echo "[*] Adding Go to PATH..."
    
    USER_HOME=$(eval echo ~$(logname 2>/dev/null || echo $USER))
    
    GO_PATH_EXPORT='export PATH=$PATH:/usr/local/go/bin'
    SHELL_RC=""
    
    CURRENT_SHELL=$(basename "$SHELL")
    case "$CURRENT_SHELL" in
        "bash")
            SHELL_RC="$USER_HOME/.bashrc"
            ;;
        "zsh")
            SHELL_RC="$USER_HOME/.zshrc"
            ;;
        "fish")
            SHELL_RC="$USER_HOME/.config/fish/config.fish"
            GO_PATH_EXPORT='set -gx PATH $PATH /usr/local/go/bin'
            ;;
    esac
    
    if [ "$CURRENT_SHELL" = "fish" ]; then
        mkdir -p "$(dirname "$SHELL_RC")"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        if [ -f "$SHELL_RC" ]; then
            if ! grep -q "/usr/local/go/bin" "$SHELL_RC"; then
                echo "$GO_PATH_EXPORT" >> "$SHELL_RC"
                echo "[✓] Go added to $SHELL_RC"
            else
                echo "[✓] Go already in PATH"
            fi
        else
            echo "$GO_PATH_EXPORT" > "$SHELL_RC"
            echo "[✓] Go added to new $SHELL_RC"
        fi
    fi
    
    export PATH="/usr/local/go/bin:$PATH"
    
    if /usr/local/go/bin/go version &> /dev/null; then
        echo "[✓] Go active in current session"
    else
        echo "[⚠] Go not active, restart terminal or manually set PATH"
    fi
    
    rm -f "/tmp/${FILENAME}"
    
    if command -v go &> /dev/null; then
        INSTALLED_VERSION=$(go version | awk '{print $3}')
        echo "[✓] Golang successfully installed: $INSTALLED_VERSION"
        echo "[✓] PATH configured for current session"
        echo "[!] For new sessions, Go will be automatically available"
        echo "[!] If Go is not found, run: source $SHELL_RC"
        return 0
    else
        echo "[❌] Failed to install Golang"
        return 1
    fi
}


check_and_install_golang() {
    MIN_GO_VERSION="1.24"
    
    if ! command -v go &> /dev/null; then
        echo "[❌] Go not installed. Installing..."
        install_golang
        return $?
    fi

    GO_VERSION_RAW=$(go version | awk '{print $3}')
    GO_VERSION=${GO_VERSION_RAW#go}

    if version_lt "$GO_VERSION" "$MIN_GO_VERSION"; then
        echo "[❌] Current Go version is $GO_VERSION, less than $MIN_GO_VERSION"
        echo "[*] Updating Go to latest version..."
        install_golang
        return $?
    fi

    echo "[✓] Go version $GO_VERSION detected and meets requirements."
    return 0
}


install_python_dependencies() {
    echo "[*] Installing Python dependencies from requirements.txt..."
    
    if [ ! -f "requirements.txt" ]; then
        echo "[❌] File requirements.txt not found!"
        return 1
    fi
    
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        echo "[❌] pip not found. Please install pip first."
        return 1
    fi
    
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    $PIP_CMD install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "[✓] Python dependencies successfully installed"
    else
        echo "[❌] Failed to install Python dependencies"
        return 1
    fi
}


check_system_httpx() {
    echo "[*] Checking httpx installed on system..."
    
    if command -v httpx &> /dev/null; then
        HTTPX_PATH=$(which httpx)
        HTTPX_VERSION=$(httpx -version 2>/dev/null | head -1)
        
        echo "[!] Httpx found on system:"
        echo "    Location: $HTTPX_PATH"
        echo "    Version: $HTTPX_VERSION"
        
        if echo "$HTTPX_PATH" | grep -q "python\|pip\|site-packages" || ! echo "$HTTPX_VERSION" | grep -q "projectdiscovery"; then
            echo ""
            echo "[⚠️]  WARNING: Detected httpx that is not from ProjectDiscovery!"
            echo "    LazyHunter requires httpx from ProjectDiscovery (Go-based)."
            echo "    System httpx (Python-based) is not compatible with LazyHunter features."
            echo ""
            echo "    Reasons for difference:"
            echo "    • httpx ProjectDiscovery (Go): Full feature support, high performance"
            echo "    • System httpx (Python): Limited features, doesn't support required parameters"
            echo ""
            read -p "    Do you want to remove system httpx and replace with httpx ProjectDiscovery? (y/N): " confirm
            echo ""
            
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo "[*] Removing system httpx..."
                if command -v pip3 &> /dev/null; then
                    pip3 uninstall -y httpx 2>/dev/null
                fi
                if command -v pip &> /dev/null; then
                    pip uninstall -y httpx 2>/dev/null
                fi
                
                if command -v apt &> /dev/null; then
                    sudo apt remove -y httpx 2>/dev/null
                elif command -v yum &> /dev/null; then
                    sudo yum remove -y httpx 2>/dev/null
                elif command -v pacman &> /dev/null; then
                    sudo pacman -R --noconfirm httpx 2>/dev/null
                fi
                
                if command -v httpx &> /dev/null; then
                    echo "[!] httpx still found. You may need to remove manually:"
                    echo "    sudo rm -f $(which httpx)"
                    read -p "    Continue installing httpx ProjectDiscovery? (y/N): " continue_install
                    if [[ ! "$continue_install" =~ ^[Yy]$ ]]; then
                        return 1
                    fi
                else
                    echo "[✓] System httpx successfully removed"
                fi
            else
                echo "[!] System httpx not removed. LazyHunter may not function optimally."
                echo "    Recommended to manually reinstall httpx ProjectDiscovery."
                return 1
            fi
        else
            echo "[✓] httpx from ProjectDiscovery detected, continuing installation..."
        fi
    else
        echo "[✓] httpx not installed, will install ProjectDiscovery version"
    fi
    
    return 0
}


check_all_tools() {
    echo "[*] Checking availability of all required tools..."
    
    TOOLS_STATUS=()
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        TOOLS_STATUS+=("Python3: ✓ $PYTHON_VERSION")
    else
        TOOLS_STATUS+=("Python3: ✗ Not installed")
    fi
    
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version 2>&1)
        TOOLS_STATUS+=("pip3: ✓ $PIP_VERSION")
    elif command -v pip &> /dev/null; then
        PIP_VERSION=$(pip --version 2>&1)
        TOOLS_STATUS+=("pip: ✓ $PIP_VERSION")
    else
        TOOLS_STATUS+=("pip: ✗ Not installed")
    fi
    
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version 2>&1)
        GO_PATH=$(which go)
        TOOLS_STATUS+=("Go: ✓ $GO_VERSION")
        TOOLS_STATUS+=("Go Path: ✓ $GO_PATH")
    else
        TOOLS_STATUS+=("Go: ✗ Not installed")
    fi
    
    for tool in subfinder httpx nuclei katana assetfinder gau waybackurls; do
        if command -v "$tool" &> /dev/null; then
            TOOL_VERSION=$("$tool" -version 2>/dev/null | head -1 || echo "Unknown version")
            TOOLS_STATUS+=("$tool: ✓ $TOOL_VERSION")
        else
            TOOLS_STATUS+=("$tool: ✗ Not installed")
        fi
    done
    
    echo ""
    echo "══════════════════════════════════════════════"
    echo "LAZYHUNTER TOOLS STATUS:"
    echo "══════════════════════════════════════════════"
    for status in "${TOOLS_STATUS[@]}"; do
        echo "$status"
    done
    echo "══════════════════════════════════════════════"
    echo ""
}


check_all_tools() {
    echo "[*] Mengecek ketersediaan semua tools yang dibutuhkan..."
    
    TOOLS_STATUS=()
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        TOOLS_STATUS+=("Python3: ✓ $PYTHON_VERSION")
    else
        TOOLS_STATUS+=("Python3: ✗ Tidak terinstall")
    fi
    
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version 2>&1)
        TOOLS_STATUS+=("pip3: ✓ $PIP_VERSION")
    elif command -v pip &> /dev/null; then
        PIP_VERSION=$(pip --version 2>&1)
        TOOLS_STATUS+=("pip: ✓ $PIP_VERSION")
    else
        TOOLS_STATUS+=("pip: ✗ Tidak terinstall")
    fi
    
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version 2>&1)
        GO_PATH=$(which go)
        TOOLS_STATUS+=("Go: ✓ $GO_VERSION")
        TOOLS_STATUS+=("Go Path: ✓ $GO_PATH")
    else
        TOOLS_STATUS+=("Go: ✗ Tidak terinstall")
    fi
    
    for tool in subfinder httpx nuclei katana assetfinder gau waybackurls; do
        if command -v "$tool" &> /dev/null; then
            TOOL_VERSION=$("$tool" -version 2>/dev/null | head -1 || echo "Unknown version")
            TOOLS_STATUS+=("$tool: ✓ $TOOL_VERSION")
        else
            TOOLS_STATUS+=("$tool: ✗ Tidak terinstall")
        fi
    done
    
    echo ""
    echo "══════════════════════════════════════════════"
    echo "STATUS TOOLS LAZYHUNTER:"
    echo "══════════════════════════════════════════════"
    for status in "${TOOLS_STATUS[@]}"; do
        echo "$status"
    done
    echo "══════════════════════════════════════════════"
    echo ""
}


install_additional_tools() {
    echo "[*] Installing additional Go-based tools..."
    
    if ! check_and_install_golang; then
        echo "[❌] Failed to ensure Go is installed. Cannot continue with tools installation."
        return 1
    fi
    
    if ! check_system_httpx; then
        echo "[❌] Installation cancelled due to httpx conflict"
        return 1
    fi
    
    GO_TOOLS=(
        "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
        "github.com/projectdiscovery/httpx/cmd/httpx@latest"
        "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
        "github.com/projectdiscovery/katana/cmd/katana@latest"
        "github.com/tomnomnom/assetfinder@latest"
        "github.com/lc/gau/v2/cmd/gau@latest"
        "github.com/tomnomnom/waybackurls@latest"
    )

    for tool in "${GO_TOOLS[@]}"; do
        echo "[+] Installing: $tool"
        go install -v "$tool"
        if [ $? -eq 0 ]; then
            echo "[✓] $tool successfully installed"
        else
            echo "[❌] Failed to install $tool"
        fi
    done
    
    echo "[*] Updating nuclei templates..."
    if command -v nuclei &> /dev/null; then
        nuclei -update-templates
        echo "[✓] Nuclei templates successfully updated"
    else
        echo "[!] Nuclei not found, skipping template update"
    fi
    
    add_go_to_path
}


add_go_to_path() {
    GO_BIN_PATH="$HOME/go/bin"
    export PATH="$PATH:$GO_BIN_PATH"
    
    echo "[*] Detecting shell to add PATH permanently..."
    
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
        echo "[⚠] Shell '$SHELL_NAME' not recognized. Add PATH manually:"
        echo "    export PATH=\$PATH:$GO_BIN_PATH"
        CONFIG_FILE=""
        ;;
    esac

    if [ -n "$CONFIG_FILE" ]; then
      if ! grep -q "$GO_BIN_PATH" "$CONFIG_FILE" 2>/dev/null; then
        echo "[+] Adding PATH to $CONFIG_FILE"
        mkdir -p "$(dirname "$CONFIG_FILE")"
        if [ "$SHELL_NAME" = "fish" ]; then
          echo "set -gx PATH \$PATH $GO_BIN_PATH" >> "$CONFIG_FILE"
        else
          echo "export PATH=\$PATH:$GO_BIN_PATH" >> "$CONFIG_FILE"
        fi
        echo "[✔] PATH successfully added to $CONFIG_FILE (permanent)"
      else
        echo "[✓] PATH to $GO_BIN_PATH already exists in $CONFIG_FILE"
      fi
    fi
}


install_all() {
    echo "[*] Starting complete LazyHunter installation..."
    
    echo "[1/4] Install Python & pip"
    if ! install_python_pip; then
        echo "[❌] Failed to install Python & pip"
        return 1
    fi
    
    echo "[2/4] Install Golang"
    if ! check_and_install_golang; then
        echo "[❌] Failed to install Golang"
        return 1
    fi
    
    echo "[3/4] Install Python dependencies"
    if ! install_python_dependencies; then
        echo "[❌] Failed to install Python dependencies"
        return 1
    fi
    
    echo "[4/4] Install additional tools"
    if ! install_additional_tools; then
        echo "[❌] Failed to install additional tools"
        return 1
    fi
    
    echo ""
    echo "══════════════════════════════════════════════"
    echo "[✔] COMPLETE INSTALLATION FINISHED!"
    echo "[✔] All tools successfully installed"
    echo "[!] Restart terminal or run:"
    if [ -n "$CONFIG_FILE" ]; then
        echo "    source $CONFIG_FILE"
    fi
    echo "to activate permanent PATH."
    echo "══════════════════════════════════════════════"
}




show_menu() {
    echo ""
    echo "Select installation option:"
    echo "1. Install Python & pip"
    echo "2. Install latest Golang"
    echo "3. Install requirements.txt (dependencies)"
    echo "4. Install additional tools (nuclei, subfinder, etc)"
    echo "5. Install All (Python + Golang + dependencies + tools)"
    echo "6. Check status of all tools"
    echo "7. Exit"
    echo ""
}


main() {
    while true; do
        show_menu
        read -p "Enter choice (1-7): " choice
        
        case $choice in
            1)
                install_python_pip
                ;;
            2)
                check_and_install_golang
                ;;
            3)
                install_python_dependencies
                ;;
            4)
                install_additional_tools
                ;;
            5)
                install_all
                ;;
            6)
                check_all_tools
                ;;
            7)
                echo "[✔] Exiting setup script. Thank you!"
                exit 0
                ;;
            *)
                echo "[❌] Invalid choice. Enter number 1-7"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

main
