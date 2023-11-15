#!/bin/bash

home_dir="/home/pi"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root. Sudo !!"
  exit
fi

read -r -p 'Password: ' password

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

echo "Checking wiringPi installation..."
gpio_version=$(gpio -v) >/dev/null 2>&1
if [ ! "$gpio_version" ]; then
  echo "wiringPi not found; installing wiringPi..."
  cd /tmp || return
  wget https://github.com/WiringPi/WiringPi/releases/download/2.61-1/wiringpi-2.61-1-armhf.deb
  dpkg -i wiringpi-2.61-1-armhf.deb
  cd $home_dir || exit
  echo "wiringPi installed."
fi
echo "wiringPi done."

echo "Checking Git installation..."
has_git=$(git --version) >/dev/null 2>&1
if [ ! "$has_git" ]; then
  echo "Git not found; installing Git..."
  apt-get install git -y
  echo "Git installed."
fi
echo "Git done"
echo "Validating requirements done."

echo "Installing logging..."
promtail_dir=/etc/promtail
promtail_version=v2.9.2
filename=promtail-linux-arm
cd /tmp || exit
curl -O -L "https://github.com/grafana/loki/releases/download/$promtail_version/$filename.zip"
unzip $filename.zip
mkdir $promtail_dir
cp $filename $promtail_dir
rm -f $filename.zip
cd $promtail_dir || exit
chmod a+x $filename
openssl enc -d -pbkdf2 -aes-256-cbc -salt -in /home/pi/weathervane/promtail-config-encrypted.yaml -out $promtail_dir/promtail-config.yaml -k "$password"
unset password
cp /home/pi/weathervane/promtail.service /etc/systemd/system/promtail.service
echo "Reloading systemd daemon (this may take a while)"
systemctl daemon-reload
echo "Enabling and starting Promtail logging service (this may take a while)"
systemctl enable promtail.service --now
echo "Logging installed."

echo "Installing weathervane..."
cd /home/pi || exit
git clone https://github.com/marcoplaisier/weathervane.git
cd weathervane || exit
apt install python3.11-venv -y
python3 -m venv venv
./venv/bin/pip3 install -r requirements.txt
echo "Weathervane installed."

echo "Installing weathervane as a service..."
cp /home/pi/weathervane/weathervane.service /etc/systemd/system/weathervane.service
echo "Reloading systemd daemon (this may take a while)"
systemctl daemon-reload
echo "Enabling and starting Weathervane service (this may take a while)"
systemctl enable weathervane.service --now
echo "Weathervane configured and started. It should be running now!"
