#!/bin/bash

echo "Updating & upgrading"
sudo apt-get update -y
sudo apt-get upgrade -y

# verify requirements
echo "Validating requirements..."

echo "Running on Raspberry Pi?"
is_pi() {
  ARCH=$(dpkg --print-architecture) >/dev/null 2>&1

  if [ "$ARCH" = "armhf" ] || [ "$ARCH" = "arm64" ]; then
    return 0
  else
    return 1
  fi
}

if is_pi; then
  echo "Running on a Raspberry Pi"
else
  echo "Warning: Not running on a Raspberry Pi"
  echo "Only simulation mode is available"
fi

echo "Checking python version..."
py_version=$(python3 --version) >/dev/null 2>&1
if [  "$py_version"  ]; then
  echo "Python 3 found"
else
  echo "Error: No valid Python interpreter found"
  echo "Install with 'sudo apt install python3.8'"
  exit 1
fi

echo "Checking Python 3 pip presence"
py_pip=$(python3.7 -m pip --version) >/dev/null 2>&1
if [ ! "$py_pip" ]; then
  sudo apt-get install python3-pip -y
fi

# enable SPI
echo "Enabling SPI"
raspi-config nonint do_spi 0

# install wiringpi
gpio_version=$(gpio -v) >/dev/null 2>&1
if [ ! "$gpio_version" ]; then
  echo "Installing wiringPi..."
  sudo apt-get install wiringpi
  echo "Installation done."
fi

has_git = $(git --version) >/dev/null 2>&1
if [ ! "$has_git" ]; then
  sudo apt-get install git-all -y
fi

echo "Validating requirements done"
echo "Requirements satisfied"

echo "Installing weathervane"
# clone repository
git clone https://github.com/marcoplaisier/weathervane.git

echo "Installing weathervane as a service..."
# install as service
sudo cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service
sudo systemctl daemon-reload

echo "Starting service"
# start service
sudo systemctl enable weathervane.service
sudo systemctl start weathervane.service
echo "Weathervane installed."
sudo reboot
# ask for stations
# ask for start and end time

