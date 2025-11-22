import cv2
import pygame
from pushbullet import Pushbullet
import time

# Pushbullet API key and other required items
API_KEY = "o.nFKqS2ii4UDgPi9NvEBkHFd1tQDCdgeA"
bullet_text = '‼️INTRUSION DETECTED AT THE BACKDOOR‼️'

# Initialize pygame mixer for alert sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound('C:\Users\georg\OneDrive\Documents\Python\Smart_house\Smart_Housing/alert.wav')

# Configuration
MIN_CONTOUR_AREA = 2000  # Minimum area of motion to trigger an alert
FRAME_RESIZE = (640, 480)  # Resize frame to speed up processing
MAX_NOTIFICATIONS = 5  # Maximum notifications before stopping the app

# Variables
notification_count = 0  # Track number of notifications sent

def send_alert():
    """Send push notification using Pushbullet."""
    global notification_count

    if notification_count < MAX_NOTIFICATIONS:
        pb = Pushbullet(API_KEY)
        pb.push_note("SECURITY BREACH:", bullet_text)
        print(f"Alert Sent! ({notification_count + 1}/{MAX_NOTIFICATIONS})")
        notification_count += 1

        if notification_count >= MAX_NOTIFICATIONS:
            print("Maximum notifications reached. Terminating application...")
            return False
    else:
        print("Notification limit reached. No alert sent.")
    return True

def intruApp(cam):
    """Start the motion detection app."""
    while True:
        ret, frame1 = cam.read()
        ret, frame2 = cam.read()

        if not ret:
            print("Failed to grab frames.")
            break

        # Flip the frames if necessary
        frame1 = cv2.flip(frame1, 1)  # Horizontal flip
        frame2 = cv2.flip(frame2, 1)  # Horizontal flip

        # Resize frames for faster processing
        frame1 = cv2.resize(frame1, FRAME_RESIZE)
        frame2 = cv2.resize(frame2, FRAME_RESIZE)

        # Calculate difference between frames
        diff = cv2.absdiff(frame1, frame2)
        grey = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(grey, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilate = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilate, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for c in contours:
            if cv2.contourArea(c) < MIN_CONTOUR_AREA:
                continue

            # Draw bounding box around detected motion
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            motion_detected = True

        # Update status and play sound if motion is detected
        if motion_detected:
            print("Motion Detected!")
            if not pygame.mixer.get_busy():  # Play sound if not already playing
                alert_sound.play()
            if not send_alert():
                break
        else:
            print("Awaiting Motion...")

        # Show the frame with detected motion
        cv2.imshow("Motion Detection", frame1)

        # Press 'q' to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def run():
    """Initialize the camera and start motion detection."""
    # Use the default webcam for video capture
    cam = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cam.isOpened():
        print("Error: Unable to access the camera.")
        exit()

    # Start the motion detection process
    intruApp(cam)

    # Release camera and close all OpenCV windows
    cam.release()
    cv2.destroyAllWindows()



