import os
import json
import requests
import subprocess
import time
from dotenv import load_dotenv
from threading import Thread
from flask import Flask

load_dotenv()

RTMP_URL = os.getenv("RTMP_URL")
STREAM_KEY = os.getenv("STREAM_KEY")
FULL_STREAM_URL = f"{RTMP_URL}/{STREAM_KEY}"

RECITERS_FOLDER = "reciters"
CONFIG_FILE = "config.json"

# ====== قراءة القارئ الحالي ======
def get_current_reciter():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    return config["reciter"]

# ====== تحميل سور قارئ محدد ======
def download_suras(reciter):
    reciter_path = os.path.join(RECITERS_FOLDER, reciter)
    sura_list = os.path.join(reciter_path, "suras.txt")
    audio_folder = os.path.join(reciter_path, "audio")

    os.makedirs(audio_folder, exist_ok=True)

    with open(sura_list, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        filename = url.split("/")[-1]
        filepath = os.path.join(audio_folder, filename)
        if not os.path.exists(filepath):
            print(f"[{reciter}] Downloading {filename}...")
            try:
                r = requests.get(url, stream=True, timeout=30)
                with open(filepath, "wb") as out:
                    for chunk in r.iter_content(chunk_size=8192):
                        out.write(chunk)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")

# ====== إنشاء قائمة تشغيل لقارئ ======
def create_playlist(reciter):
    audio_folder = os.path.join(RECITERS_FOLDER, reciter, "audio")
    files = sorted(f for f in os.listdir(audio_folder) if f.endswith(".mp3"))
    return [os.path.join(audio_folder, f) for f in files]

# ====== البث الذكي ======
def stream_loop():
    current_reciter = None
    playlist = []

    while True:
        reciter = get_current_reciter()

        if reciter != current_reciter:
            print(f"Switching to reciter: {reciter}")
            download_suras(reciter)
            playlist = create_playlist(reciter)
            current_reciter = reciter

        for filepath in playlist:
            # تحقق إذا تغير القارئ أثناء التشغيل
            if get_current_reciter() != current_reciter:
                print("Reciter changed. Reloading...")
                break

            print(f"Streaming {os.path.basename(filepath)}...")

            command = [
                "ffmpeg",
                "-re",
                "-i", filepath,
                "-vn",
                "-acodec", "aac",
                "-b:a", "128k",
                "-f", "flv",
                FULL_STREAM_URL
            ]

            process = subprocess.run(command)

        time.sleep(1)

# ====== Flask uptime ======
app = Flask(__name__)

@app.route("/")
def home():
    return "Alive", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ====== Main ======
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    stream_loop()
