Weathervane for the Raspberry Pi
================================

Requirements
-----------
BeautifulSoup 3.2.1
Mock 1.0.1

Installation
------------
1. Update and upgrade the Raspberry Pi ::

   sudo apt-get update
   sudo apt-get upgrade

2. Install and run rpi-update

   ::

      sudo wget http://goo.gl/1BOfJ -O /usr/bin/rpi-update && sudo chmod +x /usr/bin/rpi-update

   To then update your firmware, simply run the following command:

   ::

      sudo rpi-update

   Source: https://github.com/Hexxeh/rpi-update

3. Install WiringPi

   https://projects.drogon.net/raspberry-pi/wiringpi/download-and-install/

   Note: the Python wrapper for WiringPi doesn't work for the SPI protocol. The function 'wiringPiSPIDataRW()' throws an exception, no matter what kind of input is supplied. So, we use ctypes.

4. Install the program

   ::

      pip install weathervane

Running
-------
1. Load the SPI drivers from WiringPi

   ::

      gpio load spi

2. Start the program

   ::

      python weathervane.py

Running the program after boot
------------------------------
#TODO

Testing
-------
Run the tests in the folder tests.

Hardware
--------
This program does nothing really interesting on its own. It will be connected to a real weathervane that continuously displays the wind direct, wind speed and air pressure. Images will follow.