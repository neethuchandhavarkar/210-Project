from flask import Flask, render_template_string, redirect, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

IMAGE_DIR = "images"
STATUS_FILE = "status.txt"

@app.route("/")
def index():
    # Read parcel status
    status = "Unknown"
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            status = f.read().strip()

    # List images
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    image_files = sorted(os.listdir(IMAGE_DIR), reverse=True)

    images_with_time = []
    for img in image_files:
        try:
            path = os.path.join(IMAGE_DIR, img)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            images_with_time.append((img, timestamp))
        except:
            continue

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parcel Monitoring Dashboard</title>
        <meta http-equiv="refresh" content="5"> <!-- Auto-refresh every 5 seconds -->
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                padding: 30px;
                text-align: center;
            }
            h1 {
                color: #333;
            }
            .status {
                font-size: 20px;
                margin: 20px 0;
                padding: 10px;
                background-color: #eef;
                border: 1px solid #ccc;
                border-radius: 10px;
                display: inline-block;
            }
            .button {
                padding: 15px 30px;
                background-color: red;
                color: white;
                font-size: 18px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 20px;
            }
            .image-list {
                text-align: left;
                margin: 30px auto;
                max-width: 600px;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .image-list li {
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>Parcel Monitoring Dashboard</h1>
        <div class="status">
            <strong>Status:</strong> {{ status }}
        </div>

        <form action="/deactivate">
            <button class="button" type="submit">Deactivate Alarm</button>
        </form>

        <div class="image-list">
            <h3>Captured Images</h3>
            <ul>
                {% for img, time in images %}
                    <li><a href="/images/{{ img }}" target="_blank">{{ img }}</a> â€” {{ time }}</li>
                {% else %}
                    <li>No images yet.</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, status=status, images=images_with_time)

@app.route("/deactivate")
def deactivate():
    with open("aoff_flag.txt", "w") as f:
        f.write("OFF")
    return redirect("/")

@app.route("/home/s223734279/images")
def get_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
