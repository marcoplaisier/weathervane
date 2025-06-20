#!/bin/bash

# Weathervane Installation Script
# Usage: curl -s https://raw.githubusercontent.com/marcoplaisier/weathervane/master/install.sh | sudo bash [-v]

set -e

# Configuration
VERBOSE=false
TOTAL_STEPS=8
CURRENT_STEP=0

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

# Execute command with optional output suppression
execute_cmd() {
    local cmd="$1"
    local description="$2"
    
    if [ "$VERBOSE" = true ]; then
        echo "  Running: $cmd"
        eval "$cmd"
    else
        if ! eval "$cmd" >/dev/null 2>&1; then
            echo -e "${RED}Error executing: $description${NC}"
            echo "Run with -v flag for detailed output"
            exit 1
        fi
    fi
}

# User selection menu
show_menu() {
    echo -e "\n${YELLOW}Weathervane Installation Options${NC}"
    echo "Please select the installation components you want:"
    echo
    echo "A) Full installation (recommended)"
    echo "B) Basic installation (no service setup)"
    echo "C) Service setup only"
    echo "D) System configuration only"
    echo "E) Dependencies only"
    echo "F) Custom selection"
    echo
    read -p "Enter your choice (A-F): " choice
    
    case ${choice^^} in
        A) INSTALL_ALL=true ;;
        B) INSTALL_BASIC=true ;;
        C) INSTALL_SERVICE=true ;;
        D) INSTALL_SYSCONFIG=true ;;
        E) INSTALL_DEPS=true ;;
        F) custom_selection ;;
        *) echo -e "${RED}Invalid choice. Using full installation.${NC}"; INSTALL_ALL=true ;;
    esac
}

# Custom selection submenu
custom_selection() {
    echo -e "\n${YELLOW}Custom Installation Components${NC}"
    echo "Select components to install (press Enter after each selection):"
    
    read -p "Install system configuration (timezone, SPI)? (y/N): " sys_config
    read -p "Install dependencies (Git, Python packages)? (y/N): " deps
    read -p "Clone weathervane repository? (y/N): " clone_repo
    read -p "Setup systemd service? (y/N): " setup_service
    
    [[ ${sys_config^^} == "Y" ]] && INSTALL_SYSCONFIG=true
    [[ ${deps^^} == "Y" ]] && INSTALL_DEPS=true
    [[ ${clone_repo^^} == "Y" ]] && INSTALL_CLONE=true
    [[ ${setup_service^^} == "Y" ]] && INSTALL_SERVICE=true
}

# Root check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root. Use sudo!${NC}"
    exit 1
fi

echo -e "${GREEN}🌦️  Weathervane Installation Script${NC}"
echo "=================================="

# Show menu
show_menu

# Initialize installation flags
INSTALL_ALL=${INSTALL_ALL:-false}
INSTALL_BASIC=${INSTALL_BASIC:-false}
INSTALL_SYSCONFIG=${INSTALL_SYSCONFIG:-false}
INSTALL_DEPS=${INSTALL_DEPS:-false}
INSTALL_CLONE=${INSTALL_CLONE:-false}
INSTALL_SERVICE=${INSTALL_SERVICE:-false}

# Set flags based on selection
if [ "$INSTALL_ALL" = true ]; then
    INSTALL_SYSCONFIG=true
    INSTALL_DEPS=true
    INSTALL_CLONE=true
    INSTALL_SERVICE=true
elif [ "$INSTALL_BASIC" = true ]; then
    INSTALL_SYSCONFIG=true
    INSTALL_DEPS=true
    INSTALL_CLONE=true
fi

echo -e "\n${BLUE}Starting installation...${NC}"

# Step 1: System configuration
if [ "$INSTALL_SYSCONFIG" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Configuring system timezone and NTP"
    execute_cmd "timedatectl set-timezone Europe/Amsterdam" "timezone configuration"
    execute_cmd "timedatectl set-ntp True" "NTP configuration"
fi

# Step 2: Python version check
show_progress "Checking Python installation"
if ! python3 --version >/dev/null 2>&1; then
    echo -e "${RED}Error: No valid Python interpreter found${NC}"
    echo "Install with 'sudo apt install python3'"
    exit 1
fi
if [ "$VERBOSE" = true ]; then
    echo "  Python version: $(python3 --version)"
fi

# Step 3: Enable SPI
if [ "$INSTALL_SYSCONFIG" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Enabling SPI interface"
    execute_cmd "raspi-config nonint do_spi 0" "SPI configuration"
fi

# Step 4: Install Git
if [ "$INSTALL_DEPS" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Installing Git"
    execute_cmd "apt update" "package list update"
    execute_cmd "apt install git git-man -y" "Git installation"
fi

# Step 5: Install Python packages
if [ "$INSTALL_DEPS" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Installing Python dependencies"
    execute_cmd "apt install python3-httpx -y" "HTTPX installation"
fi

# Step 6: Clone repository
if [ "$INSTALL_CLONE" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Cloning Weathervane repository"
    execute_cmd "cd /home/pi" "changing to pi home directory"
    if [ -d "/home/pi/weathervane" ]; then
        echo "  Repository already exists, updating..."
        execute_cmd "cd /home/pi/weathervane && git pull" "updating repository"
    else
        execute_cmd "git clone https://github.com/marcoplaisier/weathervane.git" "cloning repository"
    fi
fi

# Step 7: Install service
if [ "$INSTALL_SERVICE" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Installing systemd service"
    execute_cmd "cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service" "copying service file"
    execute_cmd "systemctl daemon-reload" "reloading systemd daemon"
fi

# Step 8: Enable and start service
if [ "$INSTALL_SERVICE" = true ] || [ "$INSTALL_ALL" = true ]; then
    show_progress "Starting Weathervane service"
    execute_cmd "systemctl enable weathervane.service --now" "enabling and starting service"
fi

echo -e "\n${GREEN}✅ Installation completed successfully!${NC}"

if [ "$INSTALL_SERVICE" = true ] || [ "$INSTALL_ALL" = true ]; then
    echo -e "${BLUE}Service Status:${NC}"
    systemctl status weathervane.service --no-pager -l
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "• Check service status: systemctl status weathervane.service"
echo "• View logs: journalctl -u weathervane.service -f"
echo "• Configuration file: /home/pi/weathervane/weathervane.ini"
