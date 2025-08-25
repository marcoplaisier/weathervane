#!/bin/bash

# Weathervane Installation Script
# Usage: curl -s https://raw.githubusercontent.com/marcoplaisier/weathervane/master/install.sh | sudo bash [-v]

set -e

# Configuration
VERBOSE=false
TOTAL_STEPS=12
CURRENT_STEP=0
WEATHERVANE_USER="weathervane"
WEATHERVANE_HOME="/home/weathervane"
VENV_PATH="$WEATHERVANE_HOME/venv"
LOG_FILE="/var/log/weathervane-install.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
case $1 in
    -v|--verbose)
        VERBOSE=true
        shift
        ;;
    *)
        echo "Unknown option: $1"
        echo "Usage: $0 [-v|--verbose]"
        exit 1
        ;;
esac
done

# Progress indicator function
show_progress() {
CURRENT_STEP=$((CURRENT_STEP + 1))
local message="$1"
local percentage=$((CURRENT_STEP * 100 / TOTAL_STEPS))

printf "${BLUE}[%d/%d]${NC} ${GREEN}%3d%%${NC} %s\n" "$CURRENT_STEP" "$TOTAL_STEPS" "$percentage" "$message"
}

# Execute command with logging and optional output suppression
execute_cmd() {
local cmd="$1"
local description="$2"
local timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$timestamp] Executing: $description" >> "$LOG_FILE"
echo "[$timestamp] Command: $cmd" >> "$LOG_FILE"

if [ "$VERBOSE" = true ]; then
    echo "  Running: $cmd"
    if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
        echo "[$timestamp] SUCCESS: $description" >> "$LOG_FILE"
    else
        local exit_code=$?
        echo "[$timestamp] FAILED: $description (exit code: $exit_code)" >> "$LOG_FILE"
        echo -e "${RED}Error executing: $description${NC}"
        echo "Full log available at: $LOG_FILE"
        exit 1
    fi
else
    if eval "$cmd" >> "$LOG_FILE" 2>&1; then
        echo "[$timestamp] SUCCESS: $description" >> "$LOG_FILE"
    else
        local exit_code=$?
        echo "[$timestamp] FAILED: $description (exit code: $exit_code)" >> "$LOG_FILE"
        echo -e "${RED}Error executing: $description${NC}"
        echo "Run with -v flag for detailed output or check: $LOG_FILE"
        exit 1
    fi
fi
}

# Always do full installation
setup_full_installation() {
echo -e "${GREEN}Performing full Weathervane installation${NC}"
}

# Root check
if [ "$EUID" -ne 0 ]; then
echo -e "${RED}Please run as root. Use sudo!${NC}"
exit 1
fi

echo -e "${GREEN}🌦️  Weathervane Installation Script${NC}"
echo "=================================="


# Initialize log file
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"
echo "Installation started at $(date)" > "$LOG_FILE"
echo "Log file: $LOG_FILE"

# Setup full installation
setup_full_installation

echo -e "\n${BLUE}Starting installation...${NC}"

# Step 1: Create weathervane user and group
show_progress "Creating weathervane system user and group"

# Create weathervane group if it doesn't exist
if ! getent group "$WEATHERVANE_USER" >/dev/null 2>&1; then
execute_cmd "groupadd --system $WEATHERVANE_USER" "creating weathervane group"
fi

# Create weathervane user if it doesn't exist
if ! id "$WEATHERVANE_USER" &>/dev/null; then
execute_cmd "useradd --system --create-home --home-dir $WEATHERVANE_HOME --shell /bin/false --gid $WEATHERVANE_USER --comment 'Weathervane Service User' $WEATHERVANE_USER" "creating weathervane user"
execute_cmd "usermod -a -G gpio,spi $WEATHERVANE_USER" "adding user to gpio and spi groups"
else
# Ensure existing user has correct groups
execute_cmd "usermod -a -G gpio,spi $WEATHERVANE_USER" "ensuring user has gpio and spi group access"
fi

# Ensure weathervane user owns their home directory
execute_cmd "chown $WEATHERVANE_USER:$WEATHERVANE_USER $WEATHERVANE_HOME" "setting home directory ownership"
execute_cmd "chmod 755 $WEATHERVANE_HOME" "setting home directory permissions"

# Add pi user to weathervane group for service management
if id "pi" &>/dev/null; then
    execute_cmd "usermod -a -G $WEATHERVANE_USER pi" "adding pi user to weathervane group"
    if [ "$VERBOSE" = true ]; then
        echo "  Added pi user to weathervane group for service management"
    fi
fi

if [ "$VERBOSE" = true ]; then
    echo "  Created system user: $WEATHERVANE_USER"
    echo "  Created system group: $WEATHERVANE_USER"
    echo "  Home directory: $WEATHERVANE_HOME"
    echo "  Added $WEATHERVANE_USER to groups: gpio, spi"
    echo "  Added pi to group: $WEATHERVANE_USER"
fi

# Step 2: System configuration
show_progress "Configuring system timezone and NTP"
execute_cmd "timedatectl set-timezone Europe/Amsterdam" "timezone configuration"
execute_cmd "timedatectl set-ntp True" "NTP configuration"

# Step 3: Python version check
show_progress "Checking Python installation"
if ! python3 --version >/dev/null 2>&1; then
echo -e "${RED}Error: No valid Python interpreter found${NC}"
echo "Install with 'sudo apt install python3'"
exit 1
fi
if [ "$VERBOSE" = true ]; then
echo "  Python version: $(python3 --version)"
fi

# Step 4: Enable SPI
show_progress "Enabling SPI interface"
execute_cmd "raspi-config nonint do_spi 0" "SPI configuration"


# Step 5: Install system dependencies
show_progress "Installing system dependencies"
execute_cmd "apt-get update" "package list update"
execute_cmd "apt-get install -y git python3-pip python3-venv python3-dev build-essential python3-rpi.gpio" "system dependencies installation"

# Immediate systemd refresh after system package installation to prevent conflicts
execute_cmd "systemctl daemon-reload" "reloading systemd after package installation"

if [ "$VERBOSE" = true ]; then
echo "  System packages installed and systemd refreshed"
fi

# Step 6: Create virtual environment
show_progress "Creating Python virtual environment"

# Remove existing venv if it exists and is corrupted
if [ -d "$VENV_PATH" ]; then
    if ! sudo -u "$WEATHERVANE_USER" "$VENV_PATH/bin/python" --version >/dev/null 2>&1; then
        echo "  Removing corrupted virtual environment..."
        execute_cmd "rm -rf $VENV_PATH" "removing corrupted virtual environment"
    fi
fi

# Create virtual environment as weathervane user
if [ ! -d "$VENV_PATH" ]; then
    execute_cmd "sudo -u $WEATHERVANE_USER python3 -m venv $VENV_PATH --system-site-packages" "creating virtual environment with system packages"
    execute_cmd "chown -R $WEATHERVANE_USER:$WEATHERVANE_USER $VENV_PATH" "setting venv ownership"
fi

# Upgrade pip in virtual environment
execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/pip install --upgrade pip" "upgrading pip in virtual environment"

if [ "$VERBOSE" = true ]; then
    echo "  Created virtual environment at: $VENV_PATH"
    echo "  Virtual environment has access to system GPIO packages"
fi

# Step 7: Clone repository
show_progress "Cloning Weathervane repository"
execute_cmd "cd $WEATHERVANE_HOME" "changing to weathervane home directory"

# Configure Git to prevent hook execution during clone to avoid conflicts
execute_cmd "sudo -u $WEATHERVANE_USER git config --global core.hooksPath /dev/null" "disabling git hooks for safety"

if [ -d "$WEATHERVANE_HOME/weathervane" ]; then
    echo "  Repository already exists, updating..."
    execute_cmd "cd $WEATHERVANE_HOME/weathervane && sudo -u $WEATHERVANE_USER git pull" "updating repository"
else

    execute_cmd "sudo -u $WEATHERVANE_USER git clone --no-hardlinks https://github.com/marcoplaisier/weathervane.git $WEATHERVANE_HOME/weathervane" "cloning repository safely"
fi

# Reset Git hooks configuration after clone
execute_cmd "sudo -u $WEATHERVANE_USER git config --global --unset core.hooksPath" "re-enabling git hooks"

execute_cmd "chown -R $WEATHERVANE_USER:$WEATHERVANE_USER $WEATHERVANE_HOME/weathervane" "setting repository ownership"
execute_cmd "chmod -R 750 $WEATHERVANE_HOME/weathervane" "setting secure permissions"
execute_cmd "find $WEATHERVANE_HOME/weathervane -name '*.py' -exec chmod 640 {} \;" "setting script permissions"
execute_cmd "find $WEATHERVANE_HOME/weathervane -name '*.ini' -exec chmod 640 {} \;" "setting config file permissions"

# Ensure the home directory and weathervane subdirectory are accessible
execute_cmd "chmod 755 $WEATHERVANE_HOME" "setting home directory permissions"
execute_cmd "chmod 755 $WEATHERVANE_HOME/weathervane" "setting weathervane directory permissions"

if [ "$VERBOSE" = true ]; then
    echo "  Set secure permissions: 750 for directories, 640 for Python/config files"
    echo "  Weathervane group can read files but not modify them"
fi

# Step 8: Install Python requirements
show_progress "Installing Python requirements"

if [ -f "$WEATHERVANE_HOME/weathervane/requirements.txt" ]; then
    execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/pip install -r $WEATHERVANE_HOME/weathervane/requirements.txt" "installing requirements.txt"
    
    # Verify critical packages are installed and functional
    execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/python -c 'import httpx; print(f\"httpx version: {httpx.__version__}\")'" "verifying httpx installation"
    execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/python -c 'import spidev; print(\"spidev available\")'" "verifying spidev installation"
    execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/python -c 'import gpiozero; print(\"gpiozero available\")'" "verifying gpiozero installation"
    # Try to verify RPi.GPIO - may not be available on all systems
    if sudo -u "$WEATHERVANE_USER" "$VENV_PATH/bin/python" -c 'import RPi.GPIO; print("RPi.GPIO available from system packages")' >/dev/null 2>&1; then
        if [ "$VERBOSE" = true ]; then
            echo "  RPi.GPIO available from system packages"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            echo "  Warning: RPi.GPIO not available, using fallback GPIO backends"
        fi
    fi
    
    # Test virtual environment can access system GPIO groups
    execute_cmd "sudo -u $WEATHERVANE_USER $VENV_PATH/bin/python -c 'import os; print(f\"User groups: {os.getgroups()}\")'" "verifying group access in venv"
    
    # Check GPIO device permissions (non-fatal check)
    echo "  Checking GPIO device access..."
    if [ -e "/dev/gpiomem" ]; then
        ls -l /dev/gpiomem
        # Note: Group membership changes require logout/login or service restart to take effect
        if [ "$VERBOSE" = true ]; then
            echo "  Note: GPIO access will be available after service starts with proper group membership"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            echo "  Warning: /dev/gpiomem not found - may not be a Raspberry Pi system"
        fi
    fi
    
    # Verify the virtual environment python path is correct for systemd
    execute_cmd "test -x $VENV_PATH/bin/python" "verifying venv python executable"
    
    if [ "$VERBOSE" = true ]; then
        echo "  All requirements installed successfully"
        sudo -u "$WEATHERVANE_USER" "$VENV_PATH/bin/pip" list
    fi
else
    echo -e "${YELLOW}  Warning: requirements.txt not found, skipping Python package installation${NC}"
fi

# Step 9: Install service
show_progress "Installing systemd service"

# Check for existing service conflicts
if systemctl is-enabled --quiet weathervane.service 2>/dev/null; then
    echo -e "${YELLOW}  Service already installed. Updating...${NC}"
    execute_cmd "systemctl stop weathervane.service" "stopping existing service"
    execute_cmd "systemctl disable weathervane.service" "disabling existing service"
fi

execute_cmd "cp $WEATHERVANE_HOME/weathervane/weathervane.service /etc/systemd/system/weathervane.service" "copying service file"
execute_cmd "chmod 644 /etc/systemd/system/weathervane.service" "setting service file permissions"
execute_cmd "chown root:root /etc/systemd/system/weathervane.service" "setting service file ownership"

# Create polkit rule for weathervane group to manage the service
execute_cmd 'cat > /etc/polkit-1/rules.d/10-weathervane.rules << EOF
// Allow members of weathervane group to manage weathervane.service
polkit.addRule(function(action, subject) {
if (action.id == "org.freedesktop.systemd1.manage-units" &&
    action.lookup("unit") == "weathervane.service" &&
    subject.isInGroup("weathervane")) {
    return polkit.Result.YES;
}
});

// Allow members of weathervane group to view weathervane service logs
polkit.addRule(function(action, subject) {
if (action.id == "org.freedesktop.login1.read-system-logs" &&
    subject.isInGroup("weathervane")) {
    return polkit.Result.YES;
}
});
EOF' "creating polkit rules for weathervane group"

# Reload systemd configuration after service file and polkit changes
execute_cmd "systemctl daemon-reload" "reloading systemd daemon after service installation"

# Verify service file is properly recognized by systemd
execute_cmd "systemctl cat weathervane.service" "verifying service file is loaded"

if [ "$VERBOSE" = true ]; then
    echo "  Created polkit rules for weathervane group service management"
    echo "  Service file verified and systemd configuration reloaded"
fi

# Step 10: Add service unmask verification and log rotation
show_progress "Configuring service and log rotation"

# Ensure service is not masked
execute_cmd "systemctl unmask weathervane.service" "ensuring service is not masked"

# Setup log rotation for weathervane logs
execute_cmd 'cat > /etc/logrotate.d/weathervane << EOF
/var/log/weathervane.log {
daily
missingok
rotate 30
compress
notifempty
create 644 weathervane weathervane
su weathervane weathervane
}

/var/log/weathervane-install.log {
monthly
missingok
rotate 12
compress
notifempty
create 644 root root
}
EOF' "creating log rotation configuration"

if [ "$VERBOSE" = true ]; then
    echo "  Service unmask verified"
    echo "  Log rotation configured for /var/log/weathervane.log"
fi

# Step 11: Enable and start service
show_progress "Starting Weathervane service"

# Check if service is already running
if systemctl is-active --quiet weathervane.service; then
    echo -e "${YELLOW}  Service is already running. Restarting...${NC}"
    execute_cmd "systemctl stop weathervane.service" "stopping existing service"
    sleep 2  # Give service time to fully stop
    execute_cmd "systemctl start weathervane.service" "starting service"
else
    # Enable service first (without starting)
    execute_cmd "systemctl enable weathervane.service" "enabling service"
    
    # Check for common issues before starting
    if [ "$VERBOSE" = true ]; then
        echo "  Checking for potential issues..."
        # Check if SPI is enabled
        if ! ls /dev/spidev* >/dev/null 2>&1; then
            echo -e "${YELLOW}  Warning: SPI devices not found. Service may fail.${NC}"
        fi
        # Check if service file exists and is valid
        if ! systemd-analyze verify weathervane.service >/dev/null 2>&1; then
            echo -e "${YELLOW}  Warning: Service file validation failed${NC}"
        fi
    fi
    
    # Final systemd reload before starting service to ensure all changes are recognized
    execute_cmd "systemctl daemon-reload" "final systemd reload before service start"

    # Start service with timeout
    echo "  Starting service (timeout: 30s)..."
    if timeout 30 systemctl start weathervane.service 2>&1; then
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}  Service started successfully${NC}"
        fi
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo -e "${RED}  Error: Service start timed out after 30 seconds${NC}"
            echo "  The service is taking too long to start. This could mean:"
            echo "  • The service is waiting for user input"
            echo "  • There's a deadlock or infinite loop"
            echo "  • Resource conflicts (SPI/GPIO already in use)"
        else
            echo -e "${RED}  Error: Service failed to start (exit code: $EXIT_CODE)${NC}"
        fi
        echo -e "${YELLOW}  Debugging steps:${NC}"
        echo "  1. Check service status: sudo systemctl status weathervane.service"
        echo "  2. View recent logs: sudo journalctl -u weathervane.service -n 50"
        echo "  3. Check for running processes: ps aux | grep weathervane"
        echo "  4. Try manual start: sudo systemctl start weathervane.service"
        echo "  5. Run in foreground: sudo -u weathervane python3 $WEATHERVANE_HOME/weathervane/weathervane.py"
    fi
fi

# Step 12: Installation summary and log management
show_progress "Finalizing installation"

# Add summary to log
{
echo "Installation completed at $(date)"
echo "=== INSTALLATION SUMMARY ==="
echo "Weathervane user: $WEATHERVANE_USER"
echo "Home directory: $WEATHERVANE_HOME"
echo "Virtual environment: $VENV_PATH"
echo "Python version: $(sudo -u "$WEATHERVANE_USER" "$VENV_PATH/bin/python" --version 2>/dev/null || echo 'Not available')"

echo "Service status: $(systemctl is-active weathervane.service 2>/dev/null || echo 'inactive')"
echo "Service enabled: $(systemctl is-enabled weathervane.service 2>/dev/null || echo 'disabled')"

echo "=== END SUMMARY ==="
} >> "$LOG_FILE"
echo -e "\n${GREEN}✅ Installation completed successfully!${NC}"

echo -e "${BLUE}Service Status:${NC}"
systemctl status weathervane.service --no-pager -l


echo -e "\n${YELLOW}Installation Log:${NC}"
echo "• Full installation log: $LOG_FILE"
echo "• Log file size: $(du -h "$LOG_FILE" | cut -f1)"
echo "• To email log file: mail -s 'Weathervane Install Log' your-email@example.com < $LOG_FILE"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "• Check service status: systemctl status weathervane.service"
echo "• View service logs: journalctl -u weathervane.service -f"
echo "• Configuration file: $WEATHERVANE_HOME/weathervane/config.ini"
echo "• Service runs as user: $WEATHERVANE_USER (minimal privileges)"
echo "• Virtual environment: $VENV_PATH"
echo "• Pi user can manage service via weathervane group membership"
echo "• Note: Pi user may need to log out/in for group changes to take effect"
echo "• GPIO access: weathervane service will have proper GPIO permissions when started by systemd"
