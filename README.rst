First: update and upgrade 
- sudo apt-get update
- sudo apt-get upgrade

Second: install and run  rpi-update
https://github.com/Hexxeh/rpi-update 

Third: install WiringPi
https://projects.drogon.net/raspberry-pi/wiringpi/download-and-install/
Note: the Python wrapper for WiringPi doesn't work for SPI. The function 
'wiringPiSPIDataRW()' doesn't seem to work, no matter what kind of input is 
supplied. So, we use ctypes. 
