#!/bin/bash
set -e

echo "Making sure time and timezones are set correctly..."
sudo timedatectl set-timezone Europe/Amsterdam
sudo timedatectl set-ntp True

echo "Enabling SPI..."
raspi-config nonint do_spi 0
echo "SPI enabled."

#echo "Checking HTTPX installation..."
#apt install python3-httpx -y
#echo "Validating requirements done."

echo "Installing weathervane as a service..."
cp weathervane.service /etc/systemd/system/
echo "Reloading systemd daemon (this may take a while)"
systemctl daemon-reload
echo "Enabling and starting Weathervane service (this may take a while)"
systemctl enable weathervane.service --now
echo "Weathervane configured and started. It should be running now!"
echo "Check status with: sudo systemctl status weathervane.service"
echo "Find error details with: sudo journalctl -u weathervane.service"