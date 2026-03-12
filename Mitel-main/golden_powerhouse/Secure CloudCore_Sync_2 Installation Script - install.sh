#!/bin/bash
# =============================================================================
# CloudCore_Sync_2 - Secure Linux Installation Script
# KK&GDevOps - Production Cybersecurity Engine Deployment
# 
# This script securely installs CloudCore_Sync_2 with proper user isolation,
# directory permissions, Python environment, and systemd service integration.
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# CONFIGURATION VARIABLES
# =============================================================================
readonly SCRIPT_NAME="CloudCore_Sync_2 Installer"
readonly SCRIPT_VERSION="2.0.0"
readonly SERVICE_USER="cloudcore"
readonly SERVICE_GROUP="cloudcore"
readonly SERVICE_NAME="cloudcore-sync"

# Directory paths
readonly INSTALL_DIR="/opt/cloudcore_sync_2"
readonly CONFIG_DIR="/etc/cloudcore_sync_2"
readonly LOG_DIR="/var/log/cloudcore_sync_2"
readonly DATA_DIR="/var/lib/cloudcore_sync_2"
readonly SYSTEMD_DIR="/etc/systemd/system"

# File paths
readonly SERVICE_FILE="${SYSTEMD_DIR}/${SERVICE_NAME}.service"
readonly CONFIG_FILE="${CONFIG_DIR}/cloudcore.conf"
readonly REQUIREMENTS_FILE="requirements.txt"
readonly VENV_DIR="${INSTALL_DIR}/venv"

# Python requirements
readonly PYTHON_MIN_VERSION="3.8"
readonly PIP_MIN_VERSION="20.0"

# =============================================================================
# COLOR CODES FOR OUTPUT
# =============================================================================
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# =============================================================================
# LOGGING AND OUTPUT FUNCTIONS
# =============================================================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1" >&2
    fi
}

print_banner() {
    echo -e "${BLUE}"
    echo "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—"
    echo "â•‘                  ${SCRIPT_NAME}                   â•‘"
    echo "â•‘                    Version ${SCRIPT_VERSION}                       â•‘"
    echo "â•‘                     KK&GDevOps                              â•‘"
    echo "â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
    echo -e "${NC}"
}

print_step() {
    echo -e "${WHITE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}âœ“${NC} $1"
}

print_failure() {
    echo -e "${RED}âœ—${NC} $1"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
cleanup_on_error() {
    local exit_code=$?
    log_error "Installation failed with exit code ${exit_code}"
    log_info "Cleaning up partial installation..."
    
    # Stop service if it was started
    systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
    
    # Remove service file if created
    [[ -f "${SERVICE_FILE}" ]] && rm -f "${SERVICE_FILE}"
    
    # Remove directories if they were created and empty
    for dir in "${DATA_DIR}" "${LOG_DIR}"; do
        if [[ -d "${dir}" ]] && [[ -z "$(ls -A "${dir}" 2>/dev/null)" ]]; then
            rmdir "${dir}" 2>/dev/null || true
        fi
    done
    
    # Reload systemd if we modified it
    systemctl daemon-reload 2>/dev/null || true
    
    log_error "Installation cleanup completed"
    exit "${exit_code}"
}

# Set trap for cleanup on error
trap cleanup_on_error ERR

check_root_privileges() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo privileges"
        log_info "Usage: sudo ./install.sh"
        exit 1
    fi
}

check_system_compatibility() {
    local os_release="/etc/os-release"
    
    if [[ ! -f "${os_release}" ]]; then
        log_warning "Cannot detect Linux distribution"
        return 0
    fi
    
    local distro
    distro=$(grep '^ID=' "${os_release}" | cut -d'=' -f2 | tr -d '"')
    
    case "${distro}" in
        ubuntu|debian|centos|rhel|fedora|suse|opensuse*)
            log_info "Detected compatible Linux distribution: ${distro}"
            ;;
        *)
            log_warning "Untested Linux distribution: ${distro}"
            log_warning "Proceeding anyway, but issues may occur"
            ;;
    esac
}

get_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v zypper >/dev/null 2>&1; then
        echo "zypper"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

version_compare() {
    # Compare two version strings (returns 0 if v1 >= v2)
    local v1="$1" v2="$2"
    
    if [[ "$v1" == "$v2" ]]; then
        return 0
    fi
    
    local IFS=.
    local i ver1=($v1) ver2=($v2)
    
    # Fill empty fields with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=${#ver2[@]}; i<${#ver1[@]}; i++)); do
        ver2[i]=0
    done
    
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]:-} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 0
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 1
        fi
    done
    
    return 0
}

# =============================================================================
# SYSTEM USER AND GROUP MANAGEMENT
# =============================================================================
create_service_user() {
    print_step "Creating dedicated system user and group"
    
    # Check if group already exists
    if getent group "${SERVICE_GROUP}" >/dev/null 2>&1; then
        log_info "Group '${SERVICE_GROUP}' already exists"
    else
        log_info "Creating system group: ${SERVICE_GROUP}"
        groupadd --system "${SERVICE_GROUP}"
        print_success "System group created: ${SERVICE_GROUP}"
    fi
    
    # Check if user already exists
    if id "${SERVICE_USER}" >/dev/null 2>&1; then
        log_info "User '${SERVICE_USER}' already exists"
        
        # Verify user configuration
        local user_shell user_home
        user_shell=$(getent passwd "${SERVICE_USER}" | cut -d: -f7)
        user_home=$(getent passwd "${SERVICE_USER}" | cut -d: -f6)
        
        # Update user if necessary
        if [[ "${user_shell}" != "/bin/false" ]] && [[ "${user_shell}" != "/usr/sbin/nologin" ]]; then
            log_warning "User '${SERVICE_USER}' has shell access, fixing..."
            usermod --shell /bin/false "${SERVICE_USER}"
            log_info "Disabled shell access for user '${SERVICE_USER}'"
        fi
        
        # Ensure user is in correct group
        if ! groups "${SERVICE_USER}" | grep -q "${SERVICE_GROUP}"; then
            usermod --gid "${SERVICE_GROUP}" "${SERVICE_USER}"
            log_info "Added user '${SERVICE_USER}' to group '${SERVICE_GROUP}'"
        fi
    else
        log_info "Creating system user: ${SERVICE_USER}"
        useradd \
            --system \
            --gid "${SERVICE_GROUP}" \
            --home-dir "${INSTALL_DIR}" \
            --shell /bin/false \
            --comment "CloudCore_Sync_2 Service Account" \
            --no-create-home \
            "${SERVICE_USER}"
        print_success "System user created: ${SERVICE_USER}"
    fi
    
    # Verify user creation
    if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
        log_error "Failed to create or verify system user: ${SERVICE_USER}"
        exit 1
    fi
    
    log_debug "User verification: $(id "${SERVICE_USER}")"
}

# =============================================================================
# DIRECTORY STRUCTURE CREATION
# =============================================================================
create_directory_structure() {
    print_step "Creating directory structure"
    
    local directories=(
        "${INSTALL_DIR}"
        "${INSTALL_DIR}/bin"
        "${INSTALL_DIR}/lib" 
        "${INSTALL_DIR}/config"
        "${INSTALL_DIR}/logs"
        "${INSTALL_DIR}/temp"
        "${CONFIG_DIR}"
        "${LOG_DIR}"
        "${DATA_DIR}"
        "${DATA_DIR}/sessions"
        "${DATA_DIR}/metrics"
        "${DATA_DIR}/backups"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "${dir}" ]]; then
            log_info "Creating directory: ${dir}"
            mkdir -p "${dir}"
        else
            log_debug "Directory already exists: ${dir}"
        fi
    done
    
    print_success "Directory structure created"
}

set_directory_permissions() {
    print_step "Setting secure directory permissions"
    
    # Set ownership
    log_info "Setting directory ownership..."
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${LOG_DIR}"
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${DATA_DIR}"
    chown -R root:"${SERVICE_GROUP}" "${CONFIG_DIR}"
    
    # Set permissions
    log_info "Setting directory permissions..."
    
    # Application directory - service user full access
    chmod 755 "${INSTALL_DIR}"
    find "${INSTALL_DIR}" -type d -exec chmod 755 {} \;
    
    # Temporary directory - service user only
    chmod 700 "${INSTALL_DIR}/temp"
    
    # Configuration directory - root write, group read
    chmod 750 "${CONFIG_DIR}"
    
    # Log directory - service user write access
    chmod 755 "${LOG_DIR}"
    
    # Data directory - service user full access
    chmod 755 "${DATA_DIR}"
    find "${DATA_DIR}" -type d -exec chmod 755 {} \;
    
    print_success "Directory permissions configured"
    log_debug "Permission verification:"
    log_debug "$(ls -la "${INSTALL_DIR%/*}" | grep "${INSTALL_DIR##*/}")"
    log_debug "$(ls -la "${CONFIG_DIR%/*}" | grep "${CONFIG_DIR##*/}")"
}

# =============================================================================
# PYTHON ENVIRONMENT SETUP
# =============================================================================
detect_python() {
    local python_cmd=""
    local python_version=""
    
    # Try different Python commands
    for cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            python_version=$("$cmd" -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null || echo "0.0")
            if version_compare "$python_version" "$PYTHON_MIN_VERSION"; then
                python_cmd="$cmd"
                break
            fi
        fi
    done
    
    echo "$python_cmd|$python_version"
}

install_python_dependencies() {
    print_step "Installing Python dependencies"
    
    local pkg_manager
    pkg_manager=$(get_package_manager)
    
    case "$pkg_manager" in
        apt)
            log_info "Installing Python via apt..."
            apt-get update -qq
            apt-get install -y python3 python3-pip python3-venv python3-dev build-essential
            ;;
        yum|dnf)
            log_info "Installing Python via ${pkg_manager}..."
            "$pkg_manager" install -y python3 python3-pip python3-devel gcc gcc-c++ make
            ;;
        zypper)
            log_info "Installing Python via zypper..."
            zypper install -y python3 python3-pip python3-devel gcc gcc-c++ make
            ;;
        pacman)
            log_info "Installing Python via pacman..."
            pacman -S --noconfirm python python-pip base-devel
            ;;
        *)
            log_error "Unsupported package manager. Please install Python 3.8+ manually."
            exit 1
            ;;
    esac
    
    print_success "Python dependencies installed"
}

setup_python_environment() {
    print_step "Setting up Python environment"
    
    local python_info python_cmd python_version
    python_info=$(detect_python)
    python_cmd=${python_info%|*}
    python_version=${python_info#*|}
    
    if [[ -z "$python_cmd" ]]; then
        log_warning "No suitable Python found, attempting to install..."
        install_python_dependencies
        
        # Re-detect after installation
        python_info=$(detect_python)
        python_cmd=${python_info%|*}
        python_version=${python_info#*|}
        
        if [[ -z "$python_cmd" ]]; then
            log_error "Failed to install suitable Python version (>= ${PYTHON_MIN_VERSION})"
            exit 1
        fi
    fi
    
    log_info "Using Python: $python_cmd (version $python_version)"
    
    # Create virtual environment
    log_info "Creating Python virtual environment..."
    if [[ -d "$VENV_DIR" ]]; then
        log_warning "Virtual environment already exists, removing..."
        rm -rf "$VENV_DIR"
    fi
    
    sudo -u "$SERVICE_USER" "$python_cmd" -m venv "$VENV_DIR"
    
    # Verify virtual environment
    if [[ ! -f "$VENV_DIR/bin/python" ]]; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Upgrade pip in virtual environment
    log_info "Upgrading pip in virtual environment..."
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
    
    print_success "Python virtual environment created: $VENV_DIR"
    log_debug "Virtual environment Python: $(sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" --version)"
}

install_python_requirements() {
    print_step "Installing Python requirements"
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_warning "Requirements file not found: $REQUIREMENTS_FILE"
        log_info "Creating minimal requirements file..."
        
        # Create minimal requirements for basic functionality
        cat > "$REQUIREMENTS_FILE" << 'EOF'
# CloudCore_Sync_2 Minimal Requirements
pyyaml>=6.0
asyncio-mqtt>=0.11.0
aiohttp>=3.8.0
cryptography>=40.0.0
click>=8.1.0
rich>=13.0.0
tabulate>=0.9.0
psutil>=5.9.0
structlog>=23.0.0
EOF
        log_info "Created minimal requirements file"
    fi
    
    log_info "Installing Python packages from requirements..."
    if ! sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"; then
        log_error "Failed to install Python requirements"
        log_info "Requirements file contents:"
        cat "$REQUIREMENTS_FILE" >&2
        exit 1
    fi
    
    # Verify critical packages
    log_info "Verifying critical package installations..."
    local critical_packages=("yaml" "asyncio" "aiohttp" "cryptography")
    for package in "${critical_packages[@]}"; do
        if ! sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" -c "import $package" 2>/dev/null; then
            log_warning "Critical package '$package' may not be properly installed"
        else
            log_debug "Verified package: $package"
        fi
    done
    
    print_success "Python requirements installed successfully"
    log_debug "Installed packages: $(sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" list --format=freeze | wc -l) total"
}

# =============================================================================
# APPLICATION INSTALLATION
# =============================================================================
install_application_files() {
    print_step "Installing application files"
    
    local source_files=(
        "main.py"
        "engine_core.py"
        "sp_subsystem_v5_complete.py"
        "subsystem_scaffolds.py"
    )
    
    for file in "${source_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_info "Installing: $file"
            cp "$file" "$INSTALL_DIR/"
            chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/$file"
            
            # Make main.py executable
            if [[ "$file" == "main.py" ]]; then
                chmod 755 "$INSTALL_DIR/$file"
            else
                chmod 644 "$INSTALL_DIR/$file"
            fi
        else
            log_error "Required file not found: $file"
            log_error "Please ensure all application files are in the current directory"
            exit 1
        fi
    done
    
    print_success "Application files installed"
}

create_default_configuration() {
    print_step "Creating default configuration"
    
    if [[ -f "$CONFIG_FILE" ]]; then
        log_warning "Configuration file already exists, backing up..."
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    cat > "$CONFIG_FILE" << 'EOF'
# CloudCore_Sync_2 Configuration
# KK&GDevOps Production Deployment

[core]
log_level = INFO
log_file = /var/log/cloudcore_sync_2/cloudcore.log
data_dir = /var/lib/cloudcore_sync_2
temp_dir = /opt/cloudcore_sync_2/temp
max_workers = 4
enable_metrics = true
startup_timeout = 60

[network]
bind_host = 127.0.0.1
bind_port = 8443
management_port = 8444
max_connections = 1000
timeout = 30
tls_enabled = false

[security]
enable_encryption = true
session_timeout = 3600
max_failed_attempts = 5
lockout_duration = 300
audit_logging = true

[subsystems]
sync_protocol = enabled
security_subsystem = enabled
session_control = enabled
event_bus = enabled
auth_subsystem = enabled
ao_subsystem = enabled

[logging]
rotation_size = 100MB
rotation_count = 10
syslog_enabled = true
audit_enabled = true
console_output = false

[monitoring]
health_check_interval = 60
metrics_collection = true
anomaly_detection = true
performance_monitoring = true
EOF
    
    # Set configuration file permissions
    chown root:"$SERVICE_GROUP" "$CONFIG_FILE"
    chmod 640 "$CONFIG_FILE"
    
    print_success "Default configuration created: $CONFIG_FILE"
}

# =============================================================================
# SYSTEMD SERVICE MANAGEMENT
# =============================================================================
install_systemd_service() {
    print_step "Installing systemd service"
    
    if [[ ! -f "systemd/${SERVICE_NAME}.service" ]]; then
        log_error "Systemd service file not found: systemd/${SERVICE_NAME}.service"
        log_info "Creating default service file..."
        
        mkdir -p systemd
        cat > "systemd/${SERVICE_NAME}.service" << EOF
[Unit]
Description=CloudCore_Sync_2 Cybersecurity Engine
Documentation=https://github.com/KKGDevOps/CloudCore_Sync_2
After=network-online.target multi-user.target
Wants=network-online.target
StartLimitIntervalSec=30
StartLimitBurst=5

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=CLOUDCORE_ENV=production
Environment=CLOUDCORE_LOG_LEVEL=INFO
ExecStart=$VENV_DIR/bin/python -u $INSTALL_DIR/main.py --daemon --config $CONFIG_FILE
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill -TERM \$MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
Restart=always
RestartSec=10
RestartPreventExitStatus=255

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$LOG_DIR $DATA_DIR /tmp
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictNamespaces=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryHigh=1G
MemoryMax=2G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudcore-sync
SyslogFacility=daemon

[Install]
WantedBy=multi-user.target
EOF
    fi
    
    log_info "Installing systemd service file..."
    cp "systemd/${SERVICE_NAME}.service" "$SERVICE_FILE"
    chmod 644 "$SERVICE_FILE"
    
    # Reload systemd daemon
    log_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_success "Systemd service installed: $SERVICE_FILE"
}

enable_and_start_service() {
    print_step "Enabling and starting service"
    
    # Enable service for auto-start
    log_info "Enabling service for automatic startup..."
    systemctl enable "$SERVICE_NAME"
    
    # Test configuration before starting
    log_info "Testing service configuration..."
    if ! systemd-analyze verify "$SERVICE_FILE" 2>/dev/null; then
        log_warning "Service file validation warnings detected"
    fi
    
    # Start the service
    log_info "Starting CloudCore_Sync_2 service..."
    if systemctl start "$SERVICE_NAME"; then
        print_success "Service started successfully"
        
        # Wait a moment and check status
        sleep 3
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_info "Service is running and active"
        else
            log_warning "Service may have issues, checking status..."
            systemctl status "$SERVICE_NAME" --no-pager --lines=10 || true
        fi
    else
        log_error "Failed to start service"
        log_info "Checking service status..."
        systemctl status "$SERVICE_NAME" --no-pager --lines=10 || true
        exit 1
    fi
}

# =============================================================================
# FIREWALL AND SECURITY SETUP
# =============================================================================
setup_firewall_rules() {
    print_step "Setting up firewall rules"
    
    local port=8443
    
    if command -v ufw >/dev/null 2>&1; then
        log_info "Configuring UFW firewall..."
        if ufw status | grep -q "Status: active"; then
            ufw allow "$port"/tcp comment "CloudCore_Sync_2" >/dev/null 2>&1 || true
            log_info "UFW rule added for port $port"
        else
            log_warning "UFW is not active, skipping firewall configuration"
        fi
    elif command -v firewall-cmd >/dev/null 2>&1; then
        log_info "Configuring firewalld..."
        if systemctl is-active --quiet firewalld; then
            firewall-cmd --permanent --add-port="$port"/tcp >/dev/null 2>&1 || true
            firewall-cmd --reload >/dev/null 2>&1 || true
            log_info "Firewalld rule added for port $port"
        else
            log_warning "Firewalld is not active, skipping firewall configuration"
        fi
    else
        log_warning "No supported firewall found (ufw/firewalld)"
        log_info "Please manually configure firewall to allow port $port"
    fi
    
    print_success "Firewall configuration completed"
}

setup_selinux_policy() {
    print_step "Setting up SELinux policy"
    
    if ! command -v selinuxenabled >/dev/null 2>&1; then
        log_info "SELinux not available on this system"
        return 0
    fi
    
    if ! selinuxenabled 2>/dev/null; then
        log_info "SELinux is not enabled, skipping policy setup"
        return 0
    fi
    
    log_info "SELinux is enabled, creating policy..."
    
    # Create temporary SELinux policy
    local policy_file="/tmp/cloudcore-sync.te"
    cat > "$policy_file" << 'EOF'
module cloudcore-sync 1.0;

require {
    type unconfined_t;
    type bin_t;
    type usr_t;
    type tmp_t;
    type var_log_t;
    class file { read write execute };
    class dir { search };
}

# Allow CloudCore_Sync_2 to execute binaries
allow unconfined_t bin_t:file { read execute };
allow unconfined_t usr_t:file { read execute };

# Allow access to temp and log directories
allow unconfined_t tmp_t:dir search;
allow unconfined_t var_log_t:dir search;
EOF
    
    # Compile and install policy
    if command -v checkmodule >/dev/null 2>&1 && command -v semodule >/dev/null 2>&1; then
        local policy_mod="/tmp/cloudcore-sync.mod"
        local policy_pkg="/tmp/cloudcore-sync.pp"
        
        if checkmodule -M -m -o "$policy_mod" "$policy_file" 2>/dev/null; then
            if semodule_package -o "$policy_pkg" -m "$policy_mod" 2>/dev/null; then
                if semodule -i "$policy_pkg" 2>/dev/null; then
                    log_info "SELinux policy installed successfully"
                else
                    log_warning "Failed to install SELinux policy"
                fi
            fi
        fi
        
        # Cleanup temporary files
        rm -f "$policy_file" "$policy_mod" "$policy_pkg"
    else
        log_warning "SELinux policy tools not found, skipping policy creation"
    fi
    
    print_success "SELinux policy configuration completed"
}

# =============================================================================
# LOG ROTATION SETUP
# =============================================================================
setup_log_rotation() {
    print_step "Setting up log rotation"
    
    local logrotate_file="/etc/logrotate.d/cloudcore-sync"
    
    cat > "$logrotate_file" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload $SERVICE_NAME >/dev/null 2>&1 || true
    endscript
}
EOF
    
    chmod 644 "$logrotate_file"
    
    # Test logrotate configuration
    if command -v logrotate >/dev/null 2>&1; then
        if logrotate -d "$logrotate_file" >/dev/null 2>&1; then
            log_info "Log rotation configuration validated"
        else
            log_warning "Log rotation configuration may have issues"
        fi
    fi
    
    print_success "Log rotation configured"
}

# =============================================================================
# POST-INSTALLATION VERIFICATION
# =============================================================================
verify_installation() {
    print_step "Verifying installation"
    
    local errors=0
    
    # Check user and group
    if ! id "$SERVICE_USER" >/dev/null 2>&1; then
        log_error "Service user '$SERVICE_USER' not found"
        ((errors++))
    else
        log_debug "âœ“ Service user exists: $SERVICE_USER"
    fi
    
    # Check directories
    local required_dirs=("$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR" "$VENV_DIR")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory missing: $dir"
            ((errors++))
        else
            log_debug "âœ“ Directory exists: $dir"
        fi
    done
    
    # Check application files
    local required_files=("$INSTALL_DIR/main.py" "$CONFIG_FILE" "$SERVICE_FILE")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file missing: $file"
            ((errors++))
        else
            log_debug "âœ“ File exists: $file"
        fi
    done
    
    # Check Python environment
    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        log_error "Python virtual environment not properly created"
        ((errors++))
    else
        log_debug "âœ“ Python virtual environment: $VENV_DIR"
    fi
    
    # Check service status
    if ! systemctl is-enabled --quiet "$SERVICE_NAME"; then
        log_error "Service is not enabled"
        ((errors++))
    else
        log_debug "âœ“ Service is enabled: $SERVICE_NAME"
    fi
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_warning "Service is not currently active"
        log_info "Service status:"
        systemctl status "$SERVICE_NAME" --no-pager --lines=5 || true
    else
        log_debug "âœ“ Service is active: $SERVICE_NAME"
    fi
    
    if [[ $errors -eq 0 ]]; then
        print_success "Installation verification completed successfully"
    else
        log_error "Installation verification found $errors error(s)"
        return 1
    fi
}

# =============================================================================
# MAIN INSTALLATION FUNCTION
# =============================================================================
main() {
    print_banner
    
    log_info "Starting CloudCore_Sync_2 installation..."
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Configuration directory: $CONFIG_DIR"
    log_info "Log directory: $LOG_DIR"
    
    # Pre-installation checks
    check_root_privileges
    check_system_compatibility
    
    # Core installation steps
    create_service_user
    create_directory_structure
    set_directory_permissions
    setup_python_environment
    install_python_requirements
    install_application_files
    create_default_configuration
    install_systemd_service
    
    # Security and system integration
    setup_firewall_rules
    setup_selinux_policy
    setup_log_rotation
    
    # Service activation
    enable_and_start_service
    
    # Post-installation verification
    verify_installation
    
    # Installation complete
    echo
    echo -e "${GREEN}â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—${NC}"
    echo -e "${GREEN}â•‘              Installation Completed Successfully             â•‘${NC}"
    echo -e "${GREEN}â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•${NC}"
    echo
    
    # Print next steps
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "1. Review configuration: ${YELLOW}$CONFIG_FILE${NC}"
    echo -e "2. Check service status: ${YELLOW}systemctl status $SERVICE_NAME${NC}"
    echo -e "3. View service logs: ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
    echo -e "4. Test service health: ${YELLOW}curl -s http://localhost:8443/health${NC}"
    echo
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "  Start:   ${YELLOW}systemctl start $SERVICE_NAME${NC}"
    echo -e "  Stop:    ${YELLOW}systemctl stop $SERVICE_NAME${NC}"
    echo -e "  Restart: ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
    echo -e "  Status:  ${YELLOW}systemctl status $SERVICE_NAME${NC}"
    echo -e "  Logs:    ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
    echo
    
    log_info "CloudCore_Sync_2 installation completed successfully!"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
# Enable debug mode if DEBUG environment variable is set
if [[ "${DEBUG:-0}" == "1" ]]; then
    log_info "Debug mode enabled"
    set -x
fi

# Run main function
main "$@"

exit 0
