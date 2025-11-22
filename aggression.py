import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
import pygame
import threading
import h5py
import json
import time
from pushbullet import Pushbullet
import os

# Pushbullet setup
PUSHBULLET_API_KEY = "o.nFKqS2ii4UDgPi9NvEBkHFd1tQDCdgeA"
pb = Pushbullet(PUSHBULLET_API_KEY)

# Pygame setup for alert sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound('C:\Users\georg\OneDrive\Documents\Python\Smart_house\Smart_Housing/alert.wav')

# OpenCV setup
cap = cv2.VideoCapture(0)

# Mediapipe pose setup
mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils

# Load the LSTM model
custom_objects = {'Orthogonal': tf.keras.initializers.Orthogonal, 'Sequential': Sequential}
with h5py.File("/Users/nikhiltripathi/Desktop/george/LSTM-Actions-Recognition-main/lstm-model.h5", 'r') as f:
    model_config = f.attrs.get('model_config')
    model_config = json.loads(model_config)

    # Remove unsupported attributes
    for layer in model_config['config']['layers']:
        if 'time_major' in layer['config']:
            del layer['config']['time_major']

    model_json = json.dumps(model_config)
    model = tf.keras.models.model_from_json(model_json, custom_objects=custom_objects)

    weights_group = f['model_weights']
    for layer in model.layers:
        layer_name = layer.name
        if layer_name in weights_group:
            weight_names = weights_group[layer_name].attrs['weight_names']
            layer_weights = [weights_group[layer_name][weight_name] for weight_name in weight_names]
            layer.set_weights(layer_weights)

# Landmark list and labels
lm_list = []
label = "aggression"
neutral_label = "no action"
last_alert_time = time.time() - 60

# Frame buffer (10 seconds max)
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # Default to 30 FPS if unavailable
buffer_size = fps * 10  # 10-second buffer
frame_buffer = []

# Create directory for video storage
video_dir = "/Users/nikhiltripathi/Desktop/george/VideoSegments"
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Helper functions
def make_landmark_timestep(results):
    c_lm = []
    for lm in results.pose_landmarks.landmark:
        c_lm.append(lm.x)
        c_lm.append(lm.y)
        c_lm.append(lm.z)
        c_lm.append(lm.visibility)
    return c_lm

def draw_landmark_on_image(mpDraw, results, frame):
    mpDraw.draw_landmarks(frame, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
    return frame

def draw_class_on_image(label, img):
    font = cv2.FONT_HERSHEY_SIMPLEX
    position = (10, 30)
    font_scale = 1
    font_color = (0, 255, 0) if label == neutral_label else (0, 0, 255)
    thickness = 2
    line_type = 2
    cv2.putText(img, str(label), position, font, font_scale, font_color, thickness, line_type)
    return img

def save_video(frames, frame_size, label, part_number):
    """Save video frames into a single file."""
    file_name = os.path.join(video_dir, f"{label}_part{part_number}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_name, fourcc, fps, frame_size)
    for frame in frames:
        out.write(frame)
    out.release()
    return file_name

def handle_video_saving(frame_buffer, frame_size, label):
    """Handle saving and splitting video into manageable parts."""
    current_time = time.strftime("%Y%m%d-%H%M%S")
    part_number = 1

    # Save frames in parts if buffer exceeds split duration
    buffer_frames = frame_buffer.copy()
    while len(buffer_frames) > 0:
        segment_frames = buffer_frames[:buffer_size]
        buffer_frames = buffer_frames[buffer_size:]

        video_path = save_video(segment_frames, frame_size, f"{label}_{current_time}", part_number)
        part_number += 1

        # Send notification and video via Pushbullet
        pb.push_file(
            file_name=os.path.basename(video_path),
            file_type="video/mp4",
            file_path=video_path
        )

def detect(model, lm_list, frame, frame_size):
    """Perform detection and save video if aggression is detected."""
    global label, last_alert_time, frame_buffer

    lm_list = np.array(lm_list)
    lm_list = np.expand_dims(lm_list, axis=0)
    result = model.predict(lm_list)

    current_time = time.time()
    if result[0][0] < 0.5:
        label = "no aggression"
    else:
        label = "aggression"
        if current_time - last_alert_time > 30:  # Minimum 30 seconds between alerts
            last_alert_time = current_time
            threading.Thread(target=handle_video_saving, args=(frame_buffer, frame_size, label)).start()
            pb.push_note("Alert: Aggression Detected!", "Aggressive behavior has been detected by the system!")
            alert_sound.play()

    return str(label)

def run():
    global frame_buffer, lm_list, label

    # Main loop
    i = 0
    warm_up_frames = 60

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frameRGB)

        # Add frame to buffer
        if len(frame_buffer) >= buffer_size:
            frame_buffer.pop(0)
        frame_buffer.append(frame)

        i += 1
        if i > warm_up_frames:
            if results.pose_landmarks:
                lm = make_landmark_timestep(results)
                lm_list.append(lm)
                if len(lm_list) == 20:  # Predict after every 20 timesteps
                    t1 = threading.Thread(target=detect, args=(model, lm_list, frame, (frame.shape[1], frame.shape[0])))
                    t1.start()
                    lm_list = []
                frame = draw_landmark_on_image(mpDraw, results, frame)
            frame = draw_class_on_image(label, frame)
            cv2.imshow("Pose Detection", frame)
            if cv2.waitKey(1) == ord('q'):
                break

    # Save remaining landmarks to a file
    df = pd.DataFrame(lm_list)
    df.to_csv(f"{label}.csv")

    cap.release()
    cv2.destroyAllWindows()