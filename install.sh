#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root. Sudo !!"
  exit
fi

echo "Updating & upgrading"
apt-get update -y
apt-get upgrade -y
apt --fix-broken -y

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

echo "Make sure time and timezones are set correctly"
sudo timedatectl set-timezone Europe/Amsterdam
sudo timedatectl set-ntp True

echo "Checking python version..."
py_version=$(python3 --version) >/dev/null 2>&1
if [  "$py_version"  ]; then
  echo "Python 3 found"
else
  echo "Error: No valid Python interpreter found"
  echo "Install with 'sudo apt install python3'"
  exit 1
fi

echo "Checking Python 3 pip presence"
py_pip=$(python3 -m pip --version) >/dev/null 2>&1
if [ ! "$py_pip" ]; then
  apt-get install python3-pip -y
fi

# enable SPI
echo "Enabling SPI"
raspi-config nonint do_spi 0

# install wiringpi
gpio_version=$(gpio -v) >/dev/null 2>&1
if [ ! "$gpio_version" ]; then
  echo "Installing wiringPi..."
  cd /tmp || return
  wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-armhf.deb
  dpkg -i wiringpi-2.61-1-armhf.deb
  cd /home/pi || exit
  echo "Installation done."
fi

has_git=$(git --version) >/dev/null 2>&1
if [ ! "$has_git" ]; then
  apt-get install git -y
fi

echo "Validating requirements done"
echo "Requirements satisfied"

echo "Installing weathervane"
# clone repository
git clone https://github.com/marcoplaisier/weathervane.git
apt install python3-requests
apt install python3-bitstring

echo "Installing logging"
promtail_dir=/etc/promtail
promtail_version=v2.9.2
mkdir $promtail_dir
cd $promtail_dir || exit
curl -O -L "https://github.com/grafana/loki/releases/download/$promtail_version/promtail-linux-arm.zip"
unzip "promtail-linux-arm.zip"
chmod a+x "promtail-linux-arm"
cp /home/pi/weathervane/promtail.service /etc/systemd/system/promtail.service
cp /home/pi/weathervane/promtail-config.yaml $promtail_dir/promtail/config.yaml
serial_number=$(cat /sys/firmware/devicetree/base/serial-number) >/dev/null 2>&1
grep -qxF "SERIAL_NUMBER=$serial_number" /etc/environment || echo "SERIAL_NUMBER=$serial_number" >> /home/pi/.profile

cd /home/pi || exit

echo "Installing weathervane as a service..."
# install as service
cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service
systemctl daemon-reload

echo "Starting service"
# start service
systemctl enable weathervane.service
systemctl start weathervane.service
echo "Weathervane installed."
# reboot
