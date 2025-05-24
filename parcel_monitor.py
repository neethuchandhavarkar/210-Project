import os
import time
import serial
import RPi.GPIO as GPIO
import cv2
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

EMAIL = "neethuchandhavarkar2003@gmail.com"
APP_PASSWORD = "jszhcsrcncbqczqp"
TRUSTED_SENDER = "nchandhavarkar03@gmail.com"
IMAGE_DIR = "images"
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600
LED_PIN = 17

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("[Serial] Connected to Nano 33.")
except Exception as e:
    print(f"[Serial ERROR] {repr(e)}")
    ser = None

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def capture_image():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            log("[Camera ERROR] Not opened.")
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            log("[Camera ERROR] No frame.")
            return None
        filename = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
        path = os.path.join(IMAGE_DIR, filename)
        cv2.imwrite(path, frame)
        log(f"[Image] Saved: {filename}")
        return path
    except Exception as e:
        log(f"[Camera ERROR] {repr(e)}")
        return None

def send_email(image_path):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = TRUSTED_SENDER
        msg["Subject"] = "ALARM TRIGGERED: Package Moved"
        msg.attach(MIMEText("Movement detected. See attached image.", "plain"))

        with open(image_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(image_path)}")
            msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, TRUSTED_SENDER, msg.as_string())

        log("[Email] Alarm email sent.")
    except Exception as e:
        log(f"[Email ERROR] {repr(e)}")

def trigger_alarm():
    log("[Alarm] Motion detected!")
    for _ in range(3):
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.3)
    img_path = capture_image()
    if img_path:
        send_email(img_path)

def check_gui_flag():
    if os.path.exists("aoff_flag.txt"):
        os.remove("aoff_flag.txt")
        if ser:
            ser.write(b"$AOFF\n")
            ser.flush()
            log("[GUI] Sent $AOFF to Nano from GUI.")

if __name__ == "__main__":
    try:
        while True:
            if ser and ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if "$MOVED" in line:
                    trigger_alarm()
                elif "$PLACED" in line:
                    log("[Info] Parcel placed.")
                elif "$ALARM_OFF" in line:
                    log("[Nano] Alarm acknowledged OFF.")

            check_gui_flag()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        if ser:
            ser.close()
        log("[System] Shutdown.")
