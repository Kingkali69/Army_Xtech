#!/bin/bash
# GhostHUD Android - One-Click Startup
# Works from ANY directory, ANY folder name
# Auto-detects master IP and creates desktop shortcut

# Get absolute path of script location (works even if moved/renamed)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Auto-detect master IP on local network
detect_master_ip() {
    # Try known IPs first (faster)
    local known_ips=("192.168.1.116" "192.168.1.235" "192.168.1.14")
    
    for ip in "${known_ips[@]}"; do
        if timeout 1 bash -c "echo >/dev/tcp/$ip/7890" 2>/dev/null; then
            echo "[*] Found master at $ip:7890"
            echo "$ip"
            return 0
        fi
    done
    
    # If not found, scan subnet (slower)
    echo "[*] Scanning local network for master..."
    local local_ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
    if [ -n "$local_ip" ]; then
        local subnet=$(echo "$local_ip" | cut -d. -f1-3)
        for i in {1..255}; do
            test_ip="$subnet.$i"
            if [ "$test_ip" != "$local_ip" ]; then
                if timeout 0.3 bash -c "echo >/dev/tcp/$test_ip/7890" 2>/dev/null; then
                    echo "[*] Found master at $test_ip:7890"
                    echo "$test_ip"
                    return 0
                fi
            fi
        done
    fi
    
    echo "192.168.1.116"  # Default fallback
}

# Create desktop shortcut (Android/Termux)
create_desktop_shortcut() {
    # Try multiple desktop locations
    local desktops=(
        "$HOME/Desktop"
        "$HOME/desktop"
        "/sdcard/Download"
        "$HOME"
    )
    
    for desktop in "${desktops[@]}"; do
        if [ -d "$desktop" ] && [ ! -f "$desktop/GhostHUD.sh" ]; then
            cat > "$desktop/GhostHUD.sh" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/START_GHOSTHUD_ANDROID.sh"
EOF
            chmod +x "$desktop/GhostHUD.sh"
            echo "[+] Desktop shortcut created at: $desktop/GhostHUD.sh"
            return 0
        fi
    done
}

# Main execution
clear
echo "========================================"
echo "   GHOSTHUD ANDROID - STARTING"
echo "========================================"
echo ""
echo "[*] Script location: $SCRIPT_DIR"
echo "[*] Auto-detecting master IP..."

MASTER_IP=$(detect_master_ip)
echo "[*] Master IP: $MASTER_IP"
echo "[*] Port: 7892"
echo ""

# Create desktop shortcut
create_desktop_shortcut

# Start the server
echo "[*] Starting GhostHUD server..."
echo ""

python3 "$SCRIPT_DIR/android.py" "$MASTER_IP"

echo ""
echo "[!] Server stopped. Press Enter to exit..."
read

