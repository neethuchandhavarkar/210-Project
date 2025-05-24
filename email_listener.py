import imaplib
import email
from email.header import decode_header
import serial
import time
from datetime import datetime

# --- CONFIG ---
EMAIL = "neethuchandhavarkar2003@gmail.com"
APP_PASSWORD = "jszhcsrcncbqczqp"
IMAP_SERVER = "imap.gmail.com"
TRUSTED_SENDER = "nchandhavarkar03@gmail.com"
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600

# --- LOGGING ---
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- CONNECT SERIAL ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    log("[Serial] Connected to Nano 33.")
except Exception as e:
    log(f"[Serial ERROR] {repr(e)}")
    ser = None

# --- EMAIL HANDLING ---
def connect_email():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, APP_PASSWORD)
        return mail
    except Exception as e:
        log(f"[Email ERROR] {repr(e)}")
        return None

def get_subject(msg):
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        return subject.decode(encoding or "utf-8", errors="ignore")
    return subject

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in (part.get("Content-Disposition") or ""):
                return part.get_payload(decode=True).decode(errors="ignore")
    return msg.get_payload(decode=True).decode(errors="ignore")

# --- WAIT FOR NANO RESPONSE ---
def wait_for_ack(timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ser.in_waiting:
            response = ser.readline().decode(errors="ignore").strip()
            log(f"[Nano] {response}")
            if "$ALARM_OFF" in response:
                return True
        time.sleep(0.1)
    return False

# --- PROCESS EMAIL ---
def check_email_for_off_command(mail):
    try:
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return
        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            sender = email.utils.parseaddr(msg["From"])[1]
            subject = get_subject(msg).strip()
            body = get_body(msg).strip()

            if sender.lower() == TRUSTED_SENDER.lower() and subject.lower() == "feedback":
                if "alarm off" in body.lower() or "it's me" in body.lower():
                    log("[Email] Valid alarm off command received.")
                    if ser:
                        ser.reset_input_buffer()
                        ser.write(b"$AOFF\n")
                        ser.flush()
                        log("[Serial] Sent $AOFF command.")
                        time.sleep(0.5)
                        if wait_for_ack():
                            log("âœ… Alarm successfully deactivated.")
                        else:
                            log("âš ï¸ No confirmation from Nano.")
    except Exception as e:
        log(f"[Email ERROR] {repr(e)}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    mail = connect_email()
    if not mail:
        log("[Startup ERROR] Failed to log in to Gmail.")
        exit(1)

    log("[System] Email listener running...")

    try:
        while True:
            check_email_for_off_command(mail)
            time.sleep(5)  # check every 5 seconds
    except KeyboardInterrupt:
        log("User interrupted.")
    finally:
        if ser:
            ser.close()
        if mail:
            mail.logout()
        log("[System] Shutdown complete.")
