import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
import paho.mqtt.client as mqtt

class DoorUnlockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Door Control Panel")
        self.unlocked = False
        self.running = True

        # Status Label
        self.status_label = tk.Label(root, text="Visitor at the Door", font=("Arial", 18))
        self.status_label.pack(pady=10)

        # Camera display
        self.video_label = tk.Label(root)
        self.video_label.pack(pady=10)

        # Unlock Button
        self.unlock_button = tk.Button(root, text="Unlock Door", font=("Arial", 16),
                                       bg="#008080", fg="white", command=self.manual_unlock)
        self.unlock_button.pack(pady=20, ipadx=10, ipady=5)

        # Start video and MQTT
        self.cap = cv2.VideoCapture(0)
        self.update_video()
        self.start_mqtt()

    def manual_unlock(self):
        if not self.unlocked:
            self.unlock_door()

    def unlock_door(self):
        self.unlocked = True
        self.status_label.config(text="Door is Unlocked")
        self.unlock_button.config(text="Door Unlocked!", bg="#009900")
        print("🔓 Door unlocked")

    def lock_door(self):
        if self.unlocked:
            self.unlocked = False
            self.status_label.config(text="Door is Locked")
            self.unlock_button.config(text="Unlock Door", bg="#008080")
            print("🔒 Door locked")
            self.running = False
            self.cap.release()
            self.root.after(1000, self.root.destroy)

    def update_video(self):
        if self.running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            self.root.after(10, self.update_video)

    def handle_mqtt_message(self, payload):
        payload = payload.strip().lower()
        if payload == "unlock" and not self.unlocked:
            self.root.after(0, self.unlock_door)
        elif payload == "lock" and self.unlocked:
            self.root.after(0, self.lock_door)

    def start_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            print("✅ Connected to MQTT broker")
            client.subscribe("home/door/unlock")

        def on_message(client, userdata, msg):
            payload = msg.payload.decode().strip()
            print("📩 MQTT Message Received:", payload)
            self.handle_mqtt_message(payload)

        def mqtt_thread():
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect("broker.hivemq.com", 1883, 60)
            client.loop_forever()

        threading.Thread(target=mqtt_thread, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DoorUnlockApp(root)
    root.mainloop()
