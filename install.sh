#!/bin/sh

# verify requirements
## python 3
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
if [ "$py_version" =~ Python ]; then
  echo "Python 3 found"
else
  echo "Error: No valid Python interpreter found"
  echo "Install with 'sudo apt install python3.8'"
  exit 1
fi

echo "Checking Python 3 pip presence"
py_pip=$(python3.7 -m pip --version) >/dev/null 2>&1
if [ "$py_pip" =~ pip ]; then
  sudo apt-get install python3-pip -y
fi

## expanded disk
can_expand=raspi-config nonint get_can_expand >/dev/null 2>&1
if [ "$can_expand" ]; then
  raspi-config nonint do_expand_rootfs
fi

# enable SPI
spi_enabled = raspi-config nonint do_spi 0
# install wiringpi
gpio_version=$(gpio -v) >/dev/null 2>&1
if [ ! "$gpio_version" ]; then
  echo "Installing wiringPi..."
  wget https://project-downloads.drogon.net/wiringpi-latest.deb -o /tmp/wiringpi.deb
  sudo dpkg -i /tmp/wiringpi-latest.deb
  rm /tmp/wiringpi.deb
  echo "Installation done."
fi

echo "Validating requirements done"
echo "Requirements satisfied"

# clone repository
git clone https://github.com/marcoplaisier/weathervane.git
# install requirements
cd weathervane
sudo python3 main.py
# ask for stations
# ask for start and end time
# install as service
# start service
