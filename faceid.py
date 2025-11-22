# Import kivy dependencies first
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

# Import kivy UX components
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label

# Import other kivy stuff
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window

# Import other dependencies
import cv2
import tensorflow as tf
from layers import L1Dist
import os
import time
import numpy as np
from pushbullet import Pushbullet

# Pushbullet API key
API_KEY = "XYZ"
bullet_text = "You may Enter"
bullet_text1 = "Intruder Detected"
pb = Pushbullet(API_KEY)

# Disable window close button
Window.close = lambda: None

# Build app and layout 
class CamApp(App):

    def build(self):
        # Main layout components 
        self.web_cam = Image(size_hint=(1,.8))
        self.button = Button(text="Verify", on_press=self.verify, size_hint=(1,.1))
        self.verification_label = Label(text="Verification Uninitiated", size_hint=(1,.1))

        # Add items to layout
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.web_cam)
        layout.add_widget(self.button)
        layout.add_widget(self.verification_label)

        # Load tensorflow/keras model
        self.model = tf.keras.models.load_model('/Users/nikhiltripathi/Desktop/Face_detection/app/siamesemodel.h5', custom_objects={'L1Dist':L1Dist})

        # Setup video capture device
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0/33.0)

        return layout

    def update(self, *args):
        # Read frame from opencv
        ret, frame = self.capture.read()
        frame = frame[120:120+250, 500:500+250, :]

        # Flip horizontally and convert image to texture
        buf = cv2.flip(frame, 0).tostring()
        img_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        img_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.web_cam.texture = img_texture

    def preprocess(self, file_path):
        try:
            byte_img = tf.io.read_file(file_path)
            img = tf.io.decode_jpeg(byte_img)
            img = tf.image.resize(img, (100, 100))
            img = img / 255.0
            return img
        except Exception as e:
            Logger.error(f"Error decoding image {file_path}: {e}")
            return None

    def show_backup_auth_popup(self):
        """Shows a popup for backup authentication."""
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
    
        label = Label(text="Enter Backup Password:")
        password_input = TextInput(password=True, multiline=False, size_hint=(1, 0.6))
        submit_button = Button(text="Submit", size_hint=(1, 0.6))

        popup_layout.add_widget(label)
        popup_layout.add_widget(password_input)
        popup_layout.add_widget(submit_button)

        self.popup = Popup(
            title="Backup Authentication",
            content=popup_layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )

        def authenticate(instance):
            backup_password = "12345"
            if password_input.text == backup_password:
                self.verification_label.text = "Backup Verified"
                pb.push_note("Sorry For Inconvenience: ", bullet_text)
                self.popup.dismiss()
                self.switch_to_emodet()  # Transition to emodet mode after backup verification
            else:
                self.verification_label.text = "Backup Failed"
                if hasattr(self, 'SAVE_PATH') and os.path.exists(self.SAVE_PATH):
                    with open(self.SAVE_PATH, "rb") as intruder_image:
                        file_data = pb.upload_file(intruder_image, "Intruder.jpg")
                        pb.push_file(**file_data, body=bullet_text1, title="SECURITY ALERT")
                        self.popup.dismiss()
                        exit()

        submit_button.bind(on_press=authenticate)
        self.popup.open()

    def switch_to_emodet(self):
        """This method switches to the emodet mode."""
        # You can implement your transition to "emodet" here
        self.verification_label.text = "Entering Emotion Detection Mode..."
        # Add any additional logic for transitioning to the "emodet" functionality
        Clock.schedule_once(self.transition_to_emodet, 7)

    def transition_to_emodet(self, *args):
        """Perform the actual transition."""
        # Implement the logic to transition to emotion detection mode
        print("Switched to Emotion Detection mode!")
        # Example: Switch to another screen or update the UI
        # If exiting is necessary, do it gracefully
        CamApp.get_running_app().stop()  # Stops the Kivy app gracefully

    def verify(self, *args):
        detection_threshold = 0.99
        verification_threshold = 0.7
        app_data = '/Users/nikhiltripathi/Desktop/Face_detection/app/application_data/'

        # Capture input image from webcam
        self.SAVE_PATH = os.path.join(app_data, 'input_image', 'input_image.jpg')
        ret, frame = self.capture.read()
        frame = frame[120:120+250, 500:500+250, :]
        cv2.imwrite(self.SAVE_PATH, frame)

        # Build results array
        results = []
        for image in os.listdir(os.path.join(app_data, 'verification_images')):
            input_img = self.preprocess(os.path.join(app_data, 'input_image', 'input_image.jpg'))
            validation_img = self.preprocess(os.path.join(app_data, 'verification_images', image))

            if validation_img is None:
                continue

            result = self.model.predict(list(np.expand_dims([input_img, validation_img], axis=1)))
            results.append(result)

        detection = np.sum(np.array(results) > detection_threshold)
        verification = detection / len(os.listdir(os.path.join(app_data, 'verification_images')))
        verified = verification > verification_threshold

        if verified:
            self.verification_label.text = 'Verified'
            self.switch_to_emodet()  # Automatically switch to emodet mode upon successful verification
        else:
            self.verification_label.text = 'Unverified'
            self.show_backup_auth_popup()

        Logger.info(results)
        Logger.info(detection)
        Logger.info(verification)
        Logger.info(verified)

        return verified

def run():
    CamApp().run()


