import cv2
import mediapipe as mp
import numpy as np
import pickle
import time
import tensorflow as tf
import RPi.GPIO as GPIO
from collections import Counter

# ========== HARDWARE SETUP ==========
RELAY_PINS = {
    'light': 17,     # GPIO17
    'fan': 27,       # GPIO27
    'curtain': 22    # GPIO22
}

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in RELAY_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)  # Active LOW: set HIGH = OFF initially

def cleanup_gpio():
    GPIO.cleanup()

def control_device(gesture):
    if gesture == 'A':  # Turn on lights
        GPIO.output(RELAY_PINS['light'], GPIO.LOW)
    elif gesture == 'B':  # Turn off lights
        GPIO.output(RELAY_PINS['light'], GPIO.HIGH)
    elif gesture == 'L':  # Turn on fan
        GPIO.output(RELAY_PINS['fan'], GPIO.LOW)
    elif gesture == 'V':  # Turn off fan
        GPIO.output(RELAY_PINS['fan'], GPIO.HIGH)
    elif gesture == 'W':  # Open curtains
        GPIO.output(RELAY_PINS['curtain'], GPIO.LOW)
    elif gesture == 'Y':  # Close curtains
        GPIO.output(RELAY_PINS['curtain'], GPIO.HIGH)

# ========== ML + CV SETUP ==========
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

ACTION_MAP = {
    'A': "Turn on lights",
    'B': "Turn off lights",
    'L': "Turn on fan",
    'V': "Turn off fan",
    'W': "Open curtains",
    'Y': "Close curtains"
}

# UI colors
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
PURPLE = (255, 0, 255)
ORANGE = (0, 165, 255)

def load_tflite_model(model_path='asl_model.tflite'):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    print("TFLite model loaded.")
    return interpreter

def load_preprocessing_data():
    with open('asl_label_encoder.pickle', 'rb') as f:
        label_encoder = pickle.load(f)
    with open('asl_normalization.pickle', 'rb') as f:
        norm_data = pickle.load(f)
    with open('asl_class_mapping.pickle', 'rb') as f:
        class_mapping = pickle.load(f)
    return label_encoder, norm_data['min'], norm_data['max'], class_mapping

def process_input_data(landmarks, X_min, X_max):
    if len(landmarks) < 42:
        return None
    arr = np.array(landmarks[:42], dtype=np.float32).reshape(1, 42)
    normalized = (arr - X_min) / (X_max - X_min + 1e-7)
    return normalized

def predict_with_tflite(interpreter, input_data):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    return np.argmax(output[0]), output[0][np.argmax(output[0])]

# ========== MAIN DETECTION FUNCTION ==========
def real_time_detection():
    interpreter = load_tflite_model()
    label_encoder, X_min, X_max, class_mapping = load_preprocessing_data()
    setup_gpio()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)

    detection_history = []
    last_prediction = None
    prediction_count = 0
    action_triggered = False
    last_action_time = 0
    cooldown_period = 2.0
    prev_frame_time = 0

    print("ASL detection started. Press 'q' to quit.")

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            fps = 1 / (current_time - prev_frame_time + 1e-7)
            prev_frame_time = current_time

            H, W, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb, 1)
            results = hands.process(frame_rgb)
            frame_display = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            if action_triggered and (current_time - last_action_time < cooldown_period):
                cv2.putText(frame_display, f"Cooldown: {cooldown_period - (current_time - last_action_time):.1f}s",
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)
            else:
                action_triggered = False

            current_prediction = None
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame_display, hand, mp_hands.HAND_CONNECTIONS)

                data_aux, x_coords, y_coords = [], [], []
                for lm in hand.landmark:
                    data_aux += [lm.x, lm.y]
                    x_coords.append(lm.x)
                    y_coords.append(lm.y)

                x1, y1 = max(0, int(min(x_coords) * W) - 20), max(0, int(min(y_coords) * H) - 20)
                x2, y2 = min(W, int(max(x_coords) * W) + 20), min(H, int(max(y_coords) * H) + 20)
                cv2.rectangle(frame_display, (x1, y1), (x2, y2), GREEN, 2)

                processed = process_input_data(data_aux, X_min, X_max)
                if processed is not None:
                    pred_class, confidence = predict_with_tflite(interpreter, processed)
                    current_prediction = class_mapping[pred_class]
                    detection_history.append(current_prediction)
                    if len(detection_history) > 5:
                        detection_history.pop(0)

                    if current_prediction == last_prediction:
                        prediction_count += 1
                    else:
                        prediction_count = 1

                    if prediction_count >= 3:
                        stable_prediction = Counter(detection_history).most_common(1)[0][0]
                        action = ACTION_MAP.get(stable_prediction, "Unknown")
                        cv2.rectangle(frame_display, (x1, y1 - 60), (x2, y1 - 10), PURPLE, -1)
                        cv2.putText(frame_display, f"{stable_prediction} - {action}",
                                    (x1 + 10, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        cv2.putText(frame_display, f"Conf: {confidence:.2f}",
                                    (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                        if not action_triggered and stable_prediction in ACTION_MAP:
                            print(f"Action: {action}")
                            control_device(stable_prediction)
                            action_triggered = True
                            last_action_time = current_time

                    last_prediction = current_prediction

            cv2.putText(frame_display, "ASL Smart Home", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, BLUE, 2)
            cv2.putText(frame_display, f"FPS: {fps:.1f}", (W - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
            cv2.putText(frame_display, "Press 'q' to quit", (10, H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)
            cv2.imshow("ASL Smart Home", frame_display)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    cleanup_gpio()
    print("Smart home system exited.")

if __name__ == "__main__":
    real_time_detection()
