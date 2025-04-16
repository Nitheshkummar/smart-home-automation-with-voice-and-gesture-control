import board
import adafruit_dht
import time
import json
import os

dht_device = adafruit_dht.DHT11(board.D4)
DATA_FILE = os.path.join(os.path.dirname(__file__), "dht_data.json")

while True:
    try:
            temperature_c = dht_device.temperature
            humidity = dht_device.humidity
            if temperature_c is not None and humidity is not None:
                print(f"Temp: {temperature_c}°C  Humidity: {humidity}%")
                data = {
                    "temperature": temperature_c,
                    "humidity": humidity
                }
            else:
                print("Sensor failure. Check wiring.")
            time.sleep(2.0)
    except KeyboardInterrupt:  
            print("Program stopped by user")

    with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    time.sleep(2)
