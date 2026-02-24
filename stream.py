import os
import requests
import subprocess
import time
from dotenv import load_dotenv
from threading import Thread
from flask import Flask

# ====== تحميل متغيرات البيئة ======
load_dotenv()

RTMP_URL = os.getenv("RTMP_URL")
STREAM_KEY = os.getenv("STREAM_KEY")
FULL_STREAM_URL = f"{RTMP_URL}/{STREAM_KEY}"

AUDIO_FOLDER = "audio"
SURA_LIST = "suras.txt"

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ====== تحميل السور ======
def download_suras():
    with open(SURA_LIST, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        filename = url.split("/")[-1]
        filepath = os.path.join(AUDIO_FOLDER, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                r = requests.get(url, stream=True, timeout=30)
                with open(filepath, "wb") as out:
                    for chunk in r.iter_content(chunk_size=8192):
                        out.write(chunk)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")

# ====== إنشاء قائمة تشغيل ======
def create_playlist():
    files = sorted(f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".mp3"))
    playlist = [os.path.join(AUDIO_FOLDER, f) for f in files]
    return playlist

# ====== تشغيل البث مع مراقبة FFmpeg ======
def stream_loop():
    playlist = create_playlist()
    while True:
        for filepath in playlist:
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
            while True:
                try:
                    process = subprocess.run(command)
                    break  # انتهى البث للسورة وانتقل للسورة التالية
                except Exception as e:
                    print(f"FFmpeg crashed: {e}")
                    print("Restarting FFmpeg in 5 seconds...")
                    time.sleep(5)
        print("Completed playlist, restarting from first sura...")
        time.sleep(2)  # فاصل قصير قبل إعادة الختمة

# ====== إضافة Flask لمراقبة uptime ======
app = Flask(__name__)

@app.route("/")
def home():
    return "Alive", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ====== Main ======
if __name__ == "__main__":
    # تشغيل Flask في Thread منفصل
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # تحميل السور وإنشاء قائمة التشغيل
    download_suras()
    create_playlist()

    # تشغيل البث المستمر
    stream_loop()
