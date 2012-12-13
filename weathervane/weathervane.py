import argparse
from time import sleep
from interfaces.weathervaneinterface import WeatherVaneInterface

class WeatherVane(object):
    def test_mode(self):
        """
        Test mode is used to output a predicable sequence of bytes to
        the output pins.
        The program will send 3 bytes every second to the pins.
        - Byte 1: an increasing counter (modulo 255)
        - Byte 2: a decreasing counter (idem)
        - Byte 3: switches between 0x55 and 0xAA

        """
        interface = WeatherVaneInterface()
        counter = 0

        while True:
            counter +=1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter, 255-counter, test]
            interface.send(data)
            sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TBD")
    parser.add_argument('-t', '--test', action='store_true',
    default=False, help="run the program in test mode")
    wv = WeatherVane()

    args = parser.parse_args()
    if args.test:
        wv.test_mode()
