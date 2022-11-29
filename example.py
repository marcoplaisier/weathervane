import os

from weathervane.parser import BuienradarParser

a = {
    "bits": [
        {"key": "winddirection", "length": "4"},
        {"key": "windspeed", "length": "6", "max": "63", "min": "0", "step": "1"},
        {"key": "windgusts", "length": "6", "max": "63", "min": "0", "step": "1"},
        {"key": "windspeedBft", "length": "4", "max": "12", "min": "1", "step": "1"},
        {"key": "airpressure", "length": "8", "max": "1155", "min": "900", "step": "1"},
        {
            "key": "temperature",
            "length": "10",
            "max": "49.9",
            "min": "-39.9",
            "step": "0.1",
        },
        {
            "key": "feeltemperature",
            "length": "10",
            "max": "49.9",
            "min": "-39.9",
            "step": "0.1",
        },
        {"key": "humidity", "length": "7", "max": "100", "min": "0", "step": "1"},
        {"key": "service_byte", "length": "5"},
        {"key": "DUMMY_BYTE", "length": "4"},
    ],
    "channel": 0,
    "extended-error-mode": False,
    "frequency": 250000,
    "interval": 300,
    "library": "wiringPi",
    "source": "buienradar",
    "stations": [6320, 6321, 6310, 6312, 6308, 6311, 6331, 6316],
}

file_path = os.path.join(os.getcwd(), "tests", "buienradar.json")

with open(
    file_path, "r", encoding="utf-8"
) as f:  # rU opens file with line endings from different platforms correctly
    data = f.read()
    bp = BuienradarParser(**a)
    wd = bp.parse(data=data)

bits = a["bits"]
fmt = ""
for i, data in enumerate(bits):
    formatting = bits[i]
    s = "hex:{0}, ".format(formatting["length"])
    fmt += s
hexstring = fmt[:-1]

if __name__ == "__main__":
    print(hexstring)
