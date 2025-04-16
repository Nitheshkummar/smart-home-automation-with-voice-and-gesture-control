import os
import mediapipe as mp
import cv2
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Reshape
from tensorflow.keras.layers import Conv1D, MaxPooling1D, BatchNormalization
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.9)

# Define dataset directories
data_dir = 'archive/ASL_Dataset'
train_dir = os.path.join(data_dir, 'Train')

# Target letters for our smart home control
TARGET_LETTERS = ['A', 'B', 'L', 'V', 'W', 'Y']

def extract_landmarks(image_path):
    """Extract hand landmarks from an image"""
    data_aux = []
    img = cv2.imread(image_path)
    if img is None:
        print(f"Warning: Could not read image: {image_path}")
        return None
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = hands.process(img_rgb)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for landmark in hand_landmarks.landmark:
                data_aux.append(landmark.x)
                data_aux.append(landmark.y)
        return data_aux
    return None

def process_dataset(directory):
    """Process the dataset and extract features"""
    data = []
    labels = []
    
    for letter in TARGET_LETTERS:
        letter_dir = os.path.join(directory, letter)
        if os.path.isdir(letter_dir):
            print(f"Processing letter: {letter}")
            processed_count = 0
            
            # Process each image in the letter directory
            for img_file in os.listdir(letter_dir):
                if img_file.endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(letter_dir, img_file)
                    landmarks = extract_landmarks(img_path)
                    
                    if landmarks:
                        # Ensure consistent feature length (42 features for one hand)
                        if len(landmarks) >= 42:
                            landmarks = landmarks[:42]  # Take only first 42 features
                            data.append(landmarks)
                            labels.append(letter)
                            processed_count += 1
            
            print(f"  - Processed {processed_count} images for letter {letter}")
                        
    return data, labels

def create_cnn_model(input_shape, num_classes):
    """Create a lightweight CNN model for hand landmark data"""
    model = Sequential([
        # Reshape input to be 3D [batch, timesteps, features] - treating landmarks as a sequence
        Reshape((21, 2), input_shape=(input_shape,)),
        
        # First Conv layer
        Conv1D(32, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling1D(pool_size=2),
        
        # Second Conv layer
        Conv1D(64, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling1D(pool_size=2),
        Dropout(0.25),
        
        # Flatten and dense layers
        Flatten(),
        Dense(128, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])
    
    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_and_convert_to_tflite():
    """Train CNN model and convert to TensorFlow Lite"""
    print("\n=== Starting ASL Smart Home CNN Training Process ===")
    
    # Step 1: Extract features from training dataset
    print("Extracting features from training dataset...")
    data, labels = process_dataset(train_dir)
    
    if not data:
        print("Error: No valid data extracted. Check your dataset.")
        return None
    
    print(f"\nTotal samples collected: {len(data)}")
    
    # Step 2: Preprocess data for CNN
    # Convert to numpy arrays
    X = np.array(data, dtype=np.float32)
    
    # Normalize data between 0 and 1
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    X = (X - X_min) / (X_max - X_min + 1e-7)  # Add small epsilon to avoid division by zero
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(labels)
    num_classes = len(label_encoder.classes_)
    y_categorical = to_categorical(y_encoded, num_classes=num_classes)
    
    # Save label encoder for inference
    with open('asl_label_encoder.pickle', 'wb') as f:
        pickle.dump(label_encoder, f)
    
    # Also save min/max values for normalization during inference
    with open('asl_normalization.pickle', 'wb') as f:
        pickle.dump({'min': X_min, 'max': X_max}, f)
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_categorical, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Step 3: Create and train the CNN model
    print("\nCreating and training CNN model...")
    input_shape = X_train.shape[1]
    model = create_cnn_model(input_shape, num_classes)
    
    # Print model summary
    model.summary()
    
    # Define callbacks for training
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, verbose=1, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, verbose=1, min_lr=1e-6)
    ]
    
    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_test, y_test),
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate model
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"\nTest accuracy: {accuracy*100:.2f}%")
    
    # Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('asl_training_history.png')
    print("Training history saved to asl_training_history.png")
    
    # Save the full model
    model.save('asl_cnn_model.h5')
    print("Full model saved to asl_cnn_model.h5")
    
    # Step 4: Convert to TensorFlow Lite
    print("\nConverting model to TensorFlow Lite...")
    
    # Convert the model to TF Lite format
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Enable optimization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Quantize to reduce model size and improve inference speed on Raspberry Pi
    converter.target_spec.supported_types = [tf.float16]
    
    # Convert the model
    tflite_model = converter.convert()
    
    # Save the model
    with open('asl_model.tflite', 'wb') as f:
        f.write(tflite_model)
        
    print("TFLite model saved to asl_model.tflite")
    
    # Create a dictionary mapping class indices to letter labels
    class_mapping = {i: label for i, label in enumerate(label_encoder.classes_)}
    
    # Save the class mapping
    with open('asl_class_mapping.pickle', 'wb') as f:
        pickle.dump(class_mapping, f)
    
    print("\n=== CNN Training and Conversion Complete ===")
    
    # Return the trained model for further use if needed
    return model, label_encoder, X_min, X_max

if _name_ == "_main_":
    train_and_convert_to_tflite()
