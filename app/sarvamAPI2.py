from flask import Flask, render_template, jsonify,request
from flask_socketio import SocketIO, emit
import requests
import base64
import tempfile
import os
import uuid
import json
import sys
import atexit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

SARVAM_API_KEY = "Your sarvam key"
SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text-translate"

# Smart home state
smart_home_state = {
    "light": False,
    "fan": False,
    "AC": False
}

APPLIANCE_PINS = {
    "fan": 27,
    "light": 17,
    "ac": 22
}

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/voice")
def voice_page():
    return render_template("voice_page.html")


@socketio.on("audio_data")
def handle_audio_data(data):
    try:
        audio_data = data.get("audio_data")
        mime_type = data.get("mime_type", "audio/wav")
        
        if not audio_data:
            emit("error", {"message": "No audio data received"})
            return
        
        # Convert base64 to binary
        binary_audio = base64.b64decode(audio_data)
        
        # Create a unique temporary file name
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())
        temp_file_path = os.path.join(temp_dir, f"audio_{unique_id}.wav")
        
        # Write audio data to the temporary file
        with open(temp_file_path, "wb") as f:
            f.write(binary_audio)
            
        # Prepare the multipart/form-data request
        files = {
            'file': ('audio.wav', open(temp_file_path, 'rb'), 'audio/wav')
        }
        
        payload = {
            'model': 'saaras:v2',
            'with_diarization': 'false'
        }
        
        headers = {
            "api-subscription-key": SARVAM_API_KEY
        }

        response = requests.post(
            SARVAM_API_URL, 
            files=files,
            data=payload,
            headers=headers
        )
        
        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass

        if response.status_code == 200:
            result = response.json()
            global last_transcript
            last_transcript = result.get("transcript", "No text detected")

            # 🔥 Save it to a file too
            with open("last_command.txt", "w") as f:
                f.write(last_transcript)
            
            def clear_command_file():
                with open("last_command.txt", "w") as f:
                    f.write("")

            atexit.register(clear_command_file)

            # Emit transcript to frontend
            emit("transcription", {"text": last_transcript})

        else:
            error_message = f"API error: {response.status_code}"
            try:
                error_detail = response.text
                error_message += f" - {error_detail}"
            except:
                pass
            emit("error", {"message": error_message})
            
    except Exception as e:
        emit("error", {"message": f"Server error: {str(e)}"})

@app.route("/sensor")
def get_sensor_data():
    try:
        with open("DHT11/dht_data.json", "r",encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)  
    except Exception as e:
        return jsonify({"error": f"Could not read sensor data: {str(e)}"}), 500
    
            
APPLIANCE_FILE = os.path.join(os.path.dirname(__file__), "appliance_status.json")
@app.route('/get_status', methods=['GET'])
def get_appliance_status():
    try:
        with open(APPLIANCE_FILE, 'r') as f:
            status = json.load(f)
        return jsonify(status), 200  # Status code 200 for successful GET
    except Exception as e:
        return jsonify({"error": f"Could not read appliance status: {e}"}), 500  # Status code 500 for server error

@app.route('/update_status', methods=['POST'])
def update_appliance_status():
    try:
        data = request.get_json()  # Get JSON data from POST request
        with open(APPLIANCE_FILE, 'w') as f:
            normalized_data = {k.lower(): v for k, v in data.items()}
            json.dump(normalized_data, f, indent=4)
        return jsonify({"message": "Appliance status updated."}), 200  # Status code 200 for successful POST
    except Exception as e:
        return jsonify({"error": f"Failed to update appliance status: {e}"}), 500  # Status code 500 for server error


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/last_command")
def last_command():
    path = "last_command.txt"
    try:
         with open(path, 'r',encoding='utf-8') as f:
            command = f.read().strip()
            print(f"[DEBUG] Decoded command: {command}")
            return jsonify({"last_command": command})
    except:
        return jsonify({"last_command": "No command received yet."})

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5001, debug=True)
    except KeyboardInterrupt:
        print("Shutting down server...")
        try:
            socketio.stop()
        except Exception as e:
            print(f"Error while shutting down: {e}")
        sys.exit(0)  # Ensure a clean exit
