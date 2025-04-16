import json
import os
import time

COMMAND_FILE = os.path.join(os.path.dirname(__file__), "last_command.txt")
STATUS_FILE = os.path.join(os.path.dirname(__file__), "appliance_status.json")

# Mapping of keywords to appliance keys
COMMANDS = {
    "fan": "fan",
    "light": "light",
    "AC": "ac",
}

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"fan": False, "light": False, "AC": False}

def save_status(status):
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)

def process_command(command_text):
    command_text = command_text.lower()
    print(f"[DEBUG] Processing command: {command_text}")
    status = load_status()

    for appliance, key in COMMANDS.items():
        if appliance in command_text:
            if "on" in command_text:
                status[key] = True
                print(f"[INFO] Turning ON {appliance}")
            elif "off" in command_text:
                status[key] = False
                print(f"[INFO] Turning OFF {appliance}")

    save_status(status)

def monitor_commands():
    print("[INFO] Voice command handler started.")
    last_command = ""
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                    command = f.read().strip()

                if command and command != last_command:
                    process_command(command)
                    last_command = command

            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n[INFO] Program stopped by user")
            break

if __name__ == "__main__":
    monitor_commands()
