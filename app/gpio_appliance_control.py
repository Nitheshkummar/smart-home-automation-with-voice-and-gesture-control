import RPi.GPIO as GPIO
import time
import json
import os

# Define GPIO pin mappings
APPLIANCE_PINS = {
    "fan": 27,
    "light": 17,
    "ac": 22
}

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in APPLIANCE_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

STATUS_FILE = os.path.join(os.path.dirname(__file__), "appliance_status.json")

# Initialize status file if not present
if not os.path.exists(STATUS_FILE):
    default_status = {name: False for name in APPLIANCE_PINS}
    with open(STATUS_FILE, "w") as f:
        json.dump(default_status, f)

print("Appliance control started. Watching for status updates...")

try:
    while True:
        try:
            with open(STATUS_FILE, "r") as f:
                status_data = json.load(f)
            
            for appliance, pin in APPLIANCE_PINS.items():
                GPIO.output(pin, GPIO.LOW if status_data.get(appliance, False) else GPIO.HIGH)

        except Exception as e:
            print(f"[ERROR] Could not read or apply appliance status: {e}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n[INFO] Program stopped by user")
    GPIO.cleanup()
except Exception as e:
    print(f"[ERROR] An unexpected error occurred: {e}")
finally:
    GPIO.cleanup()
    print("[INFO] GPIO cleaned up and program terminated.")