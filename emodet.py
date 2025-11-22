from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.core.window import Window
import cv2
import numpy as np
from keras.models import model_from_json, Sequential
import pygame
import time
import threading

# Load the model
json_file = open("/Users/nikhiltripathi/Downloads/facialemotionmodel.json", "r")
model_json = json_file.read()
json_file.close()
model = model_from_json(model_json, custom_objects={'Sequential': Sequential})
model.load_weights("/Users/nikhiltripathi/Downloads/facialemotionmodel.h5")

# Load Haar Cascade
haar_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haar_file)

# Emotion labels
labels = {0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy', 4: 'neutral', 5: 'sad', 6: 'surprise'}

# Function to extract features for the model
def extract_features(image):
    feature = np.array(image)
    feature = feature.reshape(1, 48, 48, 1)
    return feature / 255.0

# Function to determine light settings
# Function to determine light settings (modified to remove immediate song playback)
# Initialize pygame mixer
pygame.mixer.init()

# Modify your control_lights function to use pygame for playing sound
def control_lights(emotion):
    if emotion == 'happy':
        return "/Users/nikhiltripathi/Downloads/music/Naina_Da.mp3", "Warm Yellow"
    elif emotion == 'sad':
        return "/Users/nikhiltripathi/Downloads/music/Tum_Ho.mp3", "Cool Blue"
    elif emotion == 'angry':
        return "/Users/nikhiltripathi/Downloads/music/rain_sound.mp3", "Dimmed Lights"
    elif emotion == 'surprise':
        return "/Users/nikhiltripathi/Downloads/music/George_Benson_Affirmation.mp3", "Flashing Lights"
    else:
        return None, "Neutral White"

# Main App Class
class EmotionDetectionApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Webcam feed display area
        self.video_feed = Image(size_hint=(1, 0.8))
        self.layout.add_widget(self.video_feed)

        # Light recommendation display area
        self.light_label = Label(text="Light: None", size_hint=(1, 0.2))
        self.layout.add_widget(self.light_label)

        # Start webcam
        self.capture = cv2.VideoCapture(0)
        self.is_running = True  # Flag to control loop
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS

        # Bind key events
        Window.bind(on_key_down=self.on_key_down)

        # Store the current song to play on exit
        self.exit_song = None

        # Flag to control song playback
        self.is_song_playing = False

        return self.layout

    def update(self, dt):
        if self.is_running:
            ret, frame = self.capture.read()
            if not ret:
                self.light_label.text = "Failed to capture video"
                return

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            emotion_detected = "None"
            for (x, y, w, h) in faces:
                face = gray[y:y + h, x:x + w]
                face = cv2.resize(face, (48, 48))
                features = extract_features(face)
                prediction = model.predict(features)
                emotion_detected = labels[np.argmax(prediction)]

                # Draw rectangle and label
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, emotion_detected, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

            # Update light settings and store song
            song, light = control_lights(emotion_detected)
            self.exit_song = song  # Store the song for playback on exit
            self.light_label.text = f"Light: {light}"

            # If a song is not playing, start playing the song
            if song and not self.is_song_playing:
                self.is_song_playing = True
                threading.Thread(target=self.play_song, args=(song,)).start()

            # Convert frame to texture and display it
            buffer = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
            self.video_feed.texture = texture

    def play_song(self, song_path):
        """Function to play the song using pygame mixer"""
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()

    def on_key_down(self, window, key, *args):
        if key == ord('q'):  # Stop scanning on 'q'
            self.is_running = False
            self.stop()  # Triggers `on_stop`

        if key == ord('s'):  # Stop the song on 's'
            self.stop_song()

    def stop_song(self):
        """Function to stop the song playback using pygame"""
        if self.is_song_playing:
            pygame.mixer.music.stop()
            self.is_song_playing = False
            print("Song stopped")

    def on_stop(self):
        self.capture.release()
        cv2.destroyAllWindows()
        if self.exit_song and self.is_song_playing:
            self.is_song_playing = False
            # Stop the song before exit (Handled by pygame)
            print("Exiting, song stopped")

# Run the App
def run():
    EmotionDetectionApp().run()

