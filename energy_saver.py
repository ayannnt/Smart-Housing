import cv2
from tkinter import *
from tkinter import ttk
from threading import Thread
from PIL import Image, ImageTk
import time
from datetime import datetime

# Configuration
MIN_CONTOUR_AREA = 2000
FRAME_RESIZE = (640, 480)


class SmartHomeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏠 Smart Home Control Panel")
        self.root.geometry("1100x600")
        self.root.configure(bg="#f0f0f0")

        # Title banner
        title = Label(root, text="Smart Home Security & Automation", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", pady=10)
        title.pack(fill=X)

        self.video_frame = Label(root, bg="black")
        self.video_frame.pack(side=LEFT, padx=20, pady=20)

        self.status_label = Label(root, text="Status: Initializing...", font=("Helvetica", 24), bg="#f0f0f0")
        self.status_label.pack(anchor='nw', padx=30)

        self.control_frame = Frame(root, bg="#f0f0f0")
        self.control_frame.pack(side=RIGHT, fill=Y, padx=30, pady=30)

        # Manual override main switch
        self.manual_mode = IntVar()
        self.main_cb = ttk.Checkbutton(self.control_frame, text="🔧 Manual Override", variable=self.manual_mode, command=self.toggle_manual_mode)
        self.main_cb.pack(pady=30)

        # Smart switches
        self.fan = IntVar()
        self.light = IntVar()
        self.curtain = IntVar()

        self.fan_cb = ttk.Checkbutton(self.control_frame, text="Fan", variable=self.fan)
        self.fan_cb.pack(pady=20)

        self.light_cb = ttk.Checkbutton(self.control_frame, text="Light", variable=self.light, command=self.enforce_curtain_light_logic)
        self.light_cb.pack(pady=20)

        self.curtain_cb = ttk.Checkbutton(self.control_frame, text="Curtain", variable=self.curtain, command=self.enforce_curtain_light_logic)
        self.curtain_cb.pack(pady=20)

        self.set_switch_controls(False)

        # Camera setup
        self.cam = cv2.VideoCapture(0)
        self.last_motion_time = time.time()
        self.running = True

        # Thread for camera
        self.video_thread = Thread(target=self.video_loop)
        self.video_thread.daemon = True
        self.video_thread.start()

        self.root.after(1000, self.check_motion_timeout)
        self.root.after(1000, self.schedule_time_based_actions)

    def set_switch_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        for cb in [self.fan_cb, self.light_cb, self.curtain_cb]:
            cb.config(state=state)

    def toggle_manual_mode(self):
        self.set_switch_controls(self.manual_mode.get() == 1)

    def enforce_curtain_light_logic(self):
        if self.manual_mode.get() == 1:
            if self.curtain.get() == 1:
                self.light.set(0)
            elif self.light.get() == 1:
                self.curtain.set(0)

    def video_loop(self):
        while self.running:
            ret, frame1 = self.cam.read()
            ret, frame2 = self.cam.read()

            if not ret:
                self.status_label.config(text="Status: Camera error.")
                break

            frame1 = cv2.flip(frame1, 1)
            frame2 = cv2.flip(frame2, 1)

            frame1 = cv2.resize(frame1, FRAME_RESIZE)
            frame2 = cv2.resize(frame2, FRAME_RESIZE)

            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilate = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilate, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            motion = any(cv2.contourArea(c) >= MIN_CONTOUR_AREA for c in contours)

            self.motion_status = Label(self.control_frame, text="✅ No Motion", font=("Arial", 24), fg="black")
            #self.motion_status.pack(pady=30)

            if self.manual_mode.get() == 0:
                if motion:
                    self.last_motion_time = time.time()
                    self.fan.set(1)
                    """self.motion_status.config(text="🔴 Motion Detected!", fg="black")
                else:
                    self.motion_status.config(text="✅ No Motion", fg="black")"""

            # Update status label
            status_text = "🔴 Motion Detected!" if motion else "✅ No Motion"
            self.status_label.config(text=f"Status: {status_text}")

            # Show frame
            img = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(img))
            self.video_frame.config(image=img)
            self.video_frame.image = img

    def check_motion_timeout(self):
        if self.manual_mode.get() == 0:
            if time.time() - self.last_motion_time > 10:
                self.fan.set(0)
                current_hour = datetime.now().hour
                is_day = 6 <= current_hour < 18

                if is_day:
                    self.curtain.set(1)
                    self.light.set(0)
                else:
                    self.curtain.set(0)
                    self.light.set(1)
        self.root.after(1000, self.check_motion_timeout)

    def schedule_time_based_actions(self):
        if self.manual_mode.get() == 0:
            current_hour = datetime.now().hour
            is_day = 6 <= current_hour < 18

            if is_day:
                self.curtain.set(1)
                self.light.set(0)
            else:
                self.curtain.set(0)
                self.light.set(1)
        self.root.after(60000, self.schedule_time_based_actions)

    def on_close(self):
        self.running = False
        self.cam.release()
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    style = ttk.Style()
    style.configure("TCheckbutton", font=("Helvetica", 13))
    app = SmartHomeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
