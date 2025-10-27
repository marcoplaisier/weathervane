Weathervane for the Raspberry Pi
================================

Requirements
-----------
* requests


Installation
------------
1. Update and upgrade the Raspberry Pi

   ::

      sudo curl https://raw.githubusercontent.com/marcoplaisier/weathervane/master/install.sh | sudo bash

Running
-------
1. The application is installed as a systemd service. It automatically starts up after boot

WiFi Watchdog
-------------
The installation includes a WiFi watchdog service that monitors network connectivity and automatically reboots the Raspberry Pi if WiFi connection is lost. This is particularly useful for older Raspberry Pi models that may have difficulty maintaining stable WiFi connections.

**Configuration:**

* Check interval: 60 seconds
* Failure threshold: 3 consecutive failures before reboot
* The watchdog pings the default gateway or falls back to 8.8.8.8

**Management:**

* Check status: ``sudo systemctl status wifi-watchdog.service``
* View logs: ``sudo journalctl -u wifi-watchdog.service -f``
* Disable: ``sudo systemctl disable --now wifi-watchdog.service``
* Enable: ``sudo systemctl enable --now wifi-watchdog.service``

Testing
-------
Run the tests in the folder tests.

Hardware
--------
This program does nothing really interesting on its own. It will be connected to a real weathervane that continuously displays the wind direct, wind speed and air pressure.

Encryption of promtail config
--------
openssl enc -pbkdf2 -aes-256-cbc -salt -in promtail-config-decrypted.yaml -out promtail-config-encrypted.yaml -k "<password>"
