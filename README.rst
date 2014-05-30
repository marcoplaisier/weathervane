Weathervane for the Raspberry Pi
================================

Status
-----------
.. image:: https://travis-ci.org/marcofinalist/weathervane.svg?branch=master
    :target: https://travis-ci.org/marcofinalist/weathervane

Requirements
-----------
* BeautifulSoup 3.2.1
* Mock 1.0.1

Installation
------------
1. Update and upgrade the Raspberry Pi

   ::

      sudo apt-get update
      sudo apt-get upgrade

2. Install and run rpi-update

   ::

      sudo wget http://goo.gl/1BOfJ -O /usr/bin/rpi-update && sudo chmod +x /usr/bin/rpi-update

   To then update your firmware, simply run the following command:

   ::

      sudo rpi-update

   `More information`_:

.. _`More information`: https://github.com/Hexxeh/rpi-update

3. Install WiringPi_

.. _WiringPi: https://projects.drogon.net/raspberry-pi/wiringpi/download-and-install/

   Note: the Python wrapper for WiringPi doesn't work for the SPI protocol. The function 'wiringPiSPIDataRW()' throws an exception, no matter what kind of input is supplied. So, ctypes are used.

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

Running the program automatically after boot
--------------------------------------------
Edit /etc/rc.local

   ::
         
         sudo nano /etc/rc.local
         
Add the following line at the bottom (include the ampersand)

   ::
   
      python /home/pi/weathervane/weathervane.py &

Testing
-------
Run the tests in the folder tests.

Hardware
--------
This program does nothing really interesting on its own. It will be connected to a real weathervane that continuously displays the wind direct, wind speed and air pressure. Images will follow.
