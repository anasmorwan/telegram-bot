import os
import requests
import subprocess
import time
from dotenv import load_dotenv
from threading import Thread
from flask import Flask

# تحميل البيانات من ملف .env
load_dotenv()

RTMP_URL = os.getenv("RTMP_URL")
STREAM_KEY = os.getenv("STREAM_KEY")
FULL_STREAM_URL = f"{RTMP_URL}/{STREAM_KEY}"

AUDIO_FOLDER = "audio"
SURA_LIST = "suras.txt"

os.makedirs(AUDIO_FOLDER, exist_ok=True)

def download_suras():
    with open(SURA_LIST, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        filename = url.split("/")[-1]
        filepath = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            r = requests.get(url, stream=True)
            with open(filepath, "wb") as out:
                for chunk in r.iter_content(chunk_size=8192):
                    out.write(chunk)

def create_playlist():
    files = sorted(f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".mp3"))
    with open("playlist.txt", "w") as f:
        for file in files:
            f.write(f"file '{AUDIO_FOLDER}/{file}'\n")

def stream():
    command = [
        "ffmpeg",
        "-re",
        "-f", "concat",
        "-safe", "0",
        "-i", "playlist.txt",
        "-vn",
        "-acodec", "aac",
        "-b:a", "128k",
        "-f", "flv",
        FULL_STREAM_URL
    ]
    while True:
        process = subprocess.Popen(command)
        process.wait()
        time.sleep(5)

# ======== إضافة Flask لعمل Monitor Endpoint ========
app = Flask(__name__)

@app.route("/")
def home():
    return "Alive", 200

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ======================================================

if __name__ == "__main__":
    # تشغيل Flask في Thread منفصل حتى لا يوقف البث
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    download_suras()
    create_playlist()
    stream()
