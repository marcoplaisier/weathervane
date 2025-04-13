Weathervane for the Raspberry Pi
================================

Installation
------------
1. Update and upgrade the Raspberry Pi

   ::

      sudo curl https://raw.githubusercontent.com/marcoplaisier/weathervane/master/install.sh | sudo bash

Running
-------
1. The application is installed as a systemd service. It automatically starts up after boot

Testing
-------
Run the tests in the folder tests.

Hardware
--------
This program does nothing really interesting on its own. It will be connected to a real weathervane that continuously displays the wind direct, wind speed and air pressure.
