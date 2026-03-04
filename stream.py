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
from flask import render_template
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
SURA_NAMES = {
    "001": "الفاتحة",
    "002": "البقرة",
    "003": "آل عمران",
    "004": "النساء",
    "005": "المائدة",
    "006": "الأنعام",
    "007": "الأعراف",
    "008": "الأنفال",
    "009": "التوبة",
    "010": "يونس",
    "011": "هود",
    "012": "يوسف",
    "013": "الرعد",
    "014": "إبراهيم",
    "015": "الحجر",
    "016": "النحل",
    "017": "الإسراء",
    "018": "الكهف",
    "019": "مريم",
    "020": "طه",
    "021": "الأنبياء",
    "022": "الحج",
    "023": "المؤمنون",
    "024": "النور",
    "025": "الفرقان",
    "026": "الشعراء",
    "027": "النمل",
    "028": "القصص",
    "029": "العنكبوت",
    "030": "الروم",
    "031": "لقمان",
    "032": "السجدة",
    "033": "الأحزاب",
    "034": "سبأ",
    "035": "فاطر",
    "036": "يس",
    "037": "الصافات",
    "038": "ص",
    "039": "الزمر",
    "040": "غافر",
    "041": "فصلت",
    "042": "الشورى",
    "043": "الزخرف",
    "044": "الدخان",
    "045": "الجاثية",
    "046": "الأحقاف",
    "047": "محمد",
    "048": "الفتح",
    "049": "الحجرات",
    "050": "ق",
    "051": "الذاريات",
    "052": "الطور",
    "053": "النجم",
    "054": "القمر",
    "055": "الرحمن",
    "056": "الواقعة",
    "057": "الحديد",
    "058": "المجادلة",
    "059": "الحشر",
    "060": "الممتحنة",
    "061": "الصف",
    "062": "الجمعة",
    "063": "المنافقون",
    "064": "التغابن",
    "065": "الطلاق",
    "066": "التحريم",
    "067": "الملك",
    "068": "القلم",
    "069": "الحاقة",
    "070": "المعارج",
    "071": "نوح",
    "072": "الجن",
    "073": "المزمل",
    "074": "المدثر",
    "075": "القيامة",
    "076": "الإنسان",
    "077": "المرسلات",
    "078": "النبأ",
    "079": "النازعات",
    "080": "عبس",
    "081": "التكوير",
    "082": "الانفطار",
    "083": "المطففين",
    "084": "الانشقاق",
    "085": "البروج",
    "086": "الطارق",
    "087": "الأعلى",
    "088": "الغاشية",
    "089": "الفجر",
    "090": "البلد",
    "091": "الشمس",
    "092": "الليل",
    "093": "الضحى",
    "094": "الشرح",
    "095": "التين",
    "096": "العلق",
    "097": "القدر",
    "098": "البينة",
    "099": "الزلزلة",
    "100": "العاديات",
    "101": "القارعة",
    "102": "التكاثر",
    "103": "العصر",
    "104": "الهمزة",
    "105": "الفيل",
    "106": "قريش",
    "107": "الماعون",
    "108": "الكوثر",
    "109": "الكافرون",
    "110": "النصر",
    "111": "المسد",
    "112": "الإخلاص",
    "113": "الفلق",
    "114": "الناس"
}



START_TIME = time.time()
from threading import Lock
config_lock = Lock()
ffmpeg_process = None


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

    if not os.path.exists(sura_list):
        print("❌ suras.txt غير موجود")
        return

    with open(sura_list, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        filename = url.split("/")[-1]
        filepath = os.path.join(audio_folder, filename)

        if os.path.exists(filepath):
            continue

        for attempt in range(3):
            try:
                print(f"[{reciter}] Downloading {filename} (attempt {attempt+1})...")
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()

                with open(filepath, "wb") as out:
                    for chunk in r.iter_content(chunk_size=8192):
                        out.write(chunk)

                print(f"✅ تم تحميل {filename}")
                break

            except Exception as e:
                print(f"❌ محاولة فاشلة: {e}")
                time.sleep(3)

        else:
            print(f"⚠️ فشل تحميل {filename} بعد 3 محاولات — سيتم تجاوزه")
            
# ====== إنشاء قائمة تشغيل لقارئ ======
def create_playlist(reciter):
    audio_folder = os.path.join(RECITERS_FOLDER, reciter, "audio")
    files = sorted(f for f in os.listdir(audio_folder) if f.endswith(".mp3"))
    return [os.path.join(audio_folder, f) for f in files]

# ====== البث الذكي ======
def stream_loop():
    """
    حلقة البث المحسنة:
    - أي تغيير للقارئ أو السورة يحدث فورًا
    - التعامل مع الأخطاء المتوقعة
    - دعم استمرارية البث مع حفظ current_index
    """
    global ffmpeg_process
    current_reciter = None
    playlist = []
    index = 0

    while True:
        try:
            # جلب config بأمان
            try:
                with config_lock:
                    with open(CONFIG_FILE, "r") as f:
                        config = json.load(f)
            except Exception as e:
                print(f"⚠️ خطأ قراءة config: {e}")
                time.sleep(5)
                continue

            # قارئ وسورة من config
            config_reciter = config.get("reciter")
            config_index = config.get("current_index", 0)

            # ===== تحقق من تغيير القارئ أو السورة =====
            if config_reciter != current_reciter or config_index != index:
                print(f"🔄 Detected change -> reciter: {config_reciter}, index: {config_index} (was {current_reciter}, {index})")

                # قتل ffmpeg الحالي فورًا
                if ffmpeg_process and ffmpeg_process.poll() is None:
                    try:
                        ffmpeg_process.kill()
                        print("⛔ تم إيقاف البث الحالي لتطبيق التغيير")
                    except Exception as e:
                        print(f"⚠️ خطأ عند قتل ffmpeg: {e}")

                current_reciter = config_reciter
                index = config_index

                # تحميل السور وإنشاء قائمة التشغيل
                download_suras(current_reciter)
                playlist = create_playlist(current_reciter)

                if not playlist:
                    print("⚠️ لا توجد ملفات صوتية للقارئ الحالي — انتظار 10 ثواني")
                    time.sleep(10)
                    continue

            # ===== التحقق من نهاية القائمة =====
            if index >= len(playlist):
                print("🎉 اكتملت الختمة — إعادة من البداية")
                index = 0
                with config_lock:
                    config["current_index"] = 0
                    config["khatmat"] = config.get("khatmat", 0) + 1
                    try:
                        with open(CONFIG_FILE, "w") as f:
                            json.dump(config, f)
                    except Exception as e:
                        print(f"⚠️ خطأ عند تحديث config بعد الختمة: {e}")
                continue

            # ===== تشغيل السورة الحالية =====
            filepath = playlist[index]

            if not os.path.exists(filepath):
                print(f"⚠️ الملف غير موجود: {filepath} — سيتم تخطيه")
                index += 1
                with config_lock:
                    config["current_index"] = index
                    try:
                        with open(CONFIG_FILE, "w") as f:
                            json.dump(config, f)
                    except Exception as e:
                        print(f"⚠️ خطأ تحديث config بعد تخطي الملف: {e}")
                continue

            filename = os.path.basename(filepath)
            sura_number = filename.split(".")[0]
            sura_name = SURA_NAMES.get(sura_number, sura_number)

            print(f"📖 الآن بث سورة {sura_name} — القارئ: {current_reciter}")

            # أمر FFmpeg للبث
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
                ffmpeg_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # انتظار العملية مع فحص التغييرات كل ثانية
                while True:
                    # إذا تغير القارئ أو السورة في config -> أوقف فورًا
                    with config_lock:
                        with open(CONFIG_FILE, "r") as f:
                            cfg = json.load(f)
                    if cfg.get("reciter") != current_reciter or cfg.get("current_index", 0) != index:
                        print("🔁 تغيير تم أثناء البث — إيقاف FFmpeg لتطبيقه فورًا")
                        ffmpeg_process.kill()
                        break

                    if ffmpeg_process.poll() is not None:
                        break
                    time.sleep(1)

                # قراءة stderr بعد انتهاء ffmpeg
                try:
                    stderr_output = ffmpeg_process.stderr.read().decode(errors="ignore")
                    if ffmpeg_process.returncode != 0:
                        print(f"❌ FFmpeg error في {filename}")
                        print(stderr_output)
                    else:
                        print(f"✅ انتهت سورة {sura_name}")
                except Exception as e:
                    print(f"⚠️ خطأ قراءة stderr: {e}")

            except Exception as e:
                print(f"🔥 FFmpeg crash: {e}")

            finally:
                ffmpeg_process = None

            # الانتقال للسورة التالية
            index += 1
            with config_lock:
                config["current_index"] = index
                try:
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(config, f)
                except Exception as e:
                    print(f"⚠️ خطأ تحديث config بعد السورة: {e}")

        except Exception as e:
            print(f"💥 خطأ عام في stream_loop: {e}")
            time.sleep(5)



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
    uptime_seconds = int(time.time() - START_TIME)
    uptime_hours = uptime_seconds // 3600
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    reciter = config.get("reciter", "غير معروف")
    index = config.get("current_index", 0)

    sura_number = str(index + 1).zfill(3)
    sura_name = SURA_NAMES.get(sura_number, sura_number)

    khatmat = config.get("khatmat", 0)

    bot.reply_to(message, f"""
    📖 الحالة الحالية:

    القارئ: {reciter}
    السورة: {sura_name}

    عدد الختمات: {khatmat}
    ساعات البث: {uptime_hours} ساعة
    """)

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

    with config_lock:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        config["reciter"] = name
        # لا تعيد index = 0
        # config["current_index"] = 0  ← هذا يحذف

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    bot.reply_to(message, f"Switched to {name}")



@bot.message_handler(commands=['setsura'])
def setsura(message):
    global ffmpeg_process

    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مصرح.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /setsura 2")
        return

    try:
        sura_number = int(parts[1])
        if not (1 <= sura_number <= 114):
            raise ValueError

        new_index = sura_number - 1

        with config_lock:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            config["reciter"] = name

        

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

        # 🔥 قتل ffmpeg الحالي فوراً
        if ffmpeg_process and ffmpeg_process.poll() is None:
            ffmpeg_process.kill()
            print("⛔ تم إيقاف السورة الحالية")

        bot.reply_to(message, f"✅ سيتم الانتقال إلى سورة {SURA_NAMES[str(sura_number).zfill(3)]}")

    except:
        bot.reply_to(message, "رقم سورة غير صحيح.")



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


@app.route("/mushaf")
def mushaf():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    reciter = config.get("reciter", "غير معروف")
    index = config.get("current_index", 0)

    # رقم السورة = index + 1
    sura_number = index + 1

    return render_template(
        "mushaf.html",
        reciter=reciter,
        sura_number=sura_number
    )
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

