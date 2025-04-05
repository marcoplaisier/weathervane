#!/bin/bash

home_dir="/home/pi"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root. Sudo !!"
  exit
fi

echo "Making sure time and timezones are set correctly..."
sudo timedatectl set-timezone Europe/Amsterdam
sudo timedatectl set-ntp True

echo "Checking python version..."
py_version=$(python3 --version) >/dev/null 2>&1
if [  "$py_version"  ]; then
  echo "Python 3 found."
else
  echo "Error: No valid Python interpreter found"
  echo "Install with 'sudo apt install python3'"
  exit 1
fi

echo "Enabling SPI..."
raspi-config nonint do_spi 0
echo "SPI enabled."

echo "Checking Git installation..."
apt install git git-man -y
echo "Git installed."
echo "Validating requirements done."

echo "Installing weathervane..."
cd /home/pi || exit
git clone https://github.com/marcoplaisier/weathervane.git
cd weathervane || exit
apt install python3-venv -y
python3 -m venv venv
apt install python3-httpx -y
echo "Weathervane installed."

echo "Installing weathervane as a service..."
cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service
echo "Reloading systemd daemon (this may take a while)"
systemctl daemon-reload
echo "Enabling and starting Weathervane service (this may take a while)"
systemctl enable weathervane.service --now
echo "Weathervane configured and started. It should be running now!"
