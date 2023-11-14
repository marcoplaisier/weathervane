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

# enable SPI
echo "Enabling SPI..."
raspi-config nonint do_spi 0
echo "SPI enabled."

# install wiringpi
gpio_version=$(gpio -v) >/dev/null 2>&1
if [ ! "$gpio_version" ]; then
  echo "wiringPi not found; installing wiringPi..."
  cd /tmp || return
  wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-armhf.deb
  dpkg -i wiringpi-2.61-1-armhf.deb
  cd /home/pi || exit
  echo "wiringPi installed."
fi

has_git=$(git --version) >/dev/null 2>&1
if [ ! "$has_git" ]; then
  echo "Git not found; installing Git..."
  apt-get install git -y
  echo "Git installed."
fi

echo "Validating requirements done; Requirements satisfied"

echo "Installing weathervane..."
cd /home/pi || exit
# clone repository
git clone https://github.com/marcoplaisier/weathervane.git
# creating virtual environment
cd weathervane || exit
apt install python3.11-venv -y
python3 -m venv venv
# install dependencies
./venv/bin/pip3 install -r requirements.txt
echo "Weathervane installed."

echo "Installing logging..."
promtail_dir=/etc/promtail
promtail_version=v2.9.2
mkdir $promtail_dir
cd $promtail_dir || exit
curl -O -L "https://github.com/grafana/loki/releases/download/$promtail_version/promtail-linux-arm.zip"
unzip promtail-linux-arm.zip
chmod a+x promtail-linux-arm
rm -f promtail-linux-arm.zip
read -r -p 'Password: ' password
openssl enc -d -pbkdf2 -aes-256-cbc -salt -in /home/pi/weathervane/promtail-config-encrypted.yaml -out $promtail_dir/promtail-config.yaml -k "$password"
unset password
cp /home/pi/weathervane/promtail.service /etc/systemd/system/promtail.service
systemctl daemon-reload
systemctl enable promtail.service
systemctl start promtail.service
cd /home/pi || exit
echo "Logging installed."

echo "Installing weathervane as a service..."
# install as service
cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service
systemctl daemon-reload

echo "Starting service"
# start service
systemctl enable weathervane.service
systemctl start weathervane.service
echo "Weathervane configured."
# reboot
