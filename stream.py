import os
import json
import telebot
import requests
import subprocess
import time
from dotenv import load_dotenv
from threading import Thread
from flask import Flask
import asyncio
import requests
import tempfile
import os
from datetime import datetime

load_dotenv()
API_URL = "https://mp3quran.net/api/v3/reciters?language=ar"

RTMP_URL = os.getenv("RTMP_URL")
STREAM_KEY = os.getenv("STREAM_KEY")
FULL_STREAM_URL = f"{RTMP_URL}/{STREAM_KEY}"

RECITERS_FOLDER = "reciters"
CONFIG_FILE = "config.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
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

        # إذا تغير القارئ
        if reciter != current_reciter:
            print(f"Switching to reciter: {reciter}")
            download_suras(reciter)
            playlist = create_playlist(reciter)
            current_reciter = reciter

        # قراءة المؤشر الحالي
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        index = config.get("current_index", 0)

        # إذا المؤشر أكبر من عدد السور (حالة نادرة)
        if index >= len(playlist):
            index = 0

        while index < len(playlist):

            # تحقق إذا تغير القارئ أثناء التشغيل
            if get_current_reciter() != current_reciter:
                print("Reciter changed أثناء التشغيل")
                break

            filepath = playlist[index]
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

            try:
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                if process.returncode != 0:
                    print("⚠️ فشل تشغيل السورة — سيتم تجاوزها")

            except Exception as e:
                print(f"FFmpeg crash: {e}")

            # الانتقال للسورة التالية
            index += 1

            # تحديث المؤشر في config
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            config["current_index"] = index

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

        # ✅ هنا فقط نعيد المؤشر إلى صفر بعد اكتمال القائمة
        if index >= len(playlist):
            print("🎉 اكتملت الختمة — إعادة من البداية")

            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            config["current_index"] = 0

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

        time.sleep(1)


def is_admin(user_id):
    return user_id == ADMIN_ID


@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return
    bot.reply_to(message, "البوت يعمل ✅")


@bot.message_handler(commands=['status'])
def status(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    bot.reply_to(message, f"Current reciter: {config.get('reciter')}")


@bot.message_handler(commands=['setreciter'])
def setreciter(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /setreciter sudais")
        return

    name = parts[1]

    if not os.path.exists(os.path.join(RECITERS_FOLDER, name)):
        bot.reply_to(message, "Reciter not found.")
        return

    with open(CONFIG_FILE, "w") as f:
        json.dump({"reciter": name, "current_index": 0}, f)

    bot.reply_to(message, f"Switched to {name}")



@bot.message_handler(commands=['buildreciter'])
def buildreciter(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "استخدم:\n/buildreciter اسم_القارئ")
        return

    target_name = " ".join(parts[1:]).strip()

    bot.reply_to(message, "⏳ جاري البحث عن القارئ...")

    try:
        response = requests.get(API_URL, timeout=20)
        data = response.json()
        reciters = data.get("reciters", [])

        reciter_data = None

        # البحث عن القارئ
        for r in reciters:
            if target_name in r["name"]:
                reciter_data = r
                break

        if not reciter_data:
            bot.reply_to(message, "❌ لم يتم العثور على القارئ.")
            return

        # اختيار مصحف حفص إن وجد
        moshaf_list = reciter_data.get("moshaf", [])
        selected_moshaf = None
        for m in moshaf_list:
            if "حفص" in m.get("name", ""):
                selected_moshaf = m
                break

        if not selected_moshaf and moshaf_list:
            selected_moshaf = moshaf_list[0]

        if not selected_moshaf:
            bot.reply_to(message, "⚠️ لا يوجد مصحف متاح لهذا القارئ.")
            return

        server = selected_moshaf.get("server")
        if not server:
            bot.reply_to(message, "⚠️ لا يوجد رابط سيرفر صالح.")
            return

        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(f"# reciter: {reciter_data['name']}\n")
            tmp.write(f"# moshaf: {selected_moshaf.get('name','unknown')}\n")
            tmp.write(f"# generated: {datetime.now()}\n\n")

            for i in range(1, 115):
                s_num = str(i).zfill(3)
                link = f"{server}{s_num}.mp3"
                tmp.write(link + "\n")

            tmp_path = tmp.name

        # إرسال الملف للمستخدم
        with open(tmp_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"{reciter_data['name']}.txt")

        os.remove(tmp_path)
        bot.reply_to(message, "✅ تم إنشاء الملف بنجاح.")

    except requests.exceptions.RequestException:
        bot.reply_to(message, "❌ خطأ في الاتصال بالـ API.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ غير متوقع: {str(e)}")

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

    # Flask
    t1 = Thread(target=run_flask)
    t1.daemon = True
    t1.start()

    # Stream
    t2 = Thread(target=stream_loop)
    t2.daemon = True
    t2.start()

    # Bot polling (في Main Thread)
    print("Bot started...")
    bot.infinity_polling()
    stream_loop()
