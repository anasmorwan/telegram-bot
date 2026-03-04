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
def download_and_prepare_sura(reciter, index):
    """
    تحميل سورة واحدة فقط وتحويلها إلى AAC
    """
    reciter_folder = os.path.join(RECITERS_FOLDER, reciter)
    audio_folder = os.path.join(reciter_folder, "audio")
    suras_file = os.path.join(reciter_folder, "suras.txt")

    os.makedirs(audio_folder, exist_ok=True)

    if not os.path.exists(suras_file):
        print("❌ suras.txt غير موجود")
        return None

    with open(suras_file, "r") as f:
        lines = f.readlines()

    if index >= len(lines):
        return None

    line = lines[index].strip()
    if "|" not in line:
        return None

    filename_mp3, url = line.split("|")
    filename_mp3 = filename_mp3.strip()
    url = url.strip()

    filepath_mp3 = os.path.join(audio_folder, filename_mp3)
    filename_aac = filename_mp3.replace(".mp3", ".aac")
    filepath_aac = os.path.join(audio_folder, filename_aac)

    # إذا موجود مسبقًا لا تعيد تحميله
    if os.path.exists(filepath_aac):
        return filepath_aac

    print(f"⬇️ تحميل سورة {filename_mp3} ...")

    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()

        with open(filepath_mp3, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

        print("🔄 تحويل إلى AAC ...")

        convert_cmd = [
            "ffmpeg", "-y",
            "-i", filepath_mp3,
            "-c:a", "aac",
            "-b:a", "128k",
            filepath_aac
        ]

        result = subprocess.run(convert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if result.returncode != 0:
            print("❌ فشل التحويل:", result.stderr.decode(errors="ignore"))
            os.remove(filepath_mp3)
            return None

        os.remove(filepath_mp3)
        print("✅ جاهزة للبث")

        return filepath_aac

    except Exception as e:
        print("🔥 خطأ في التحميل:", e)
        return None



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
        filename_mp3 = url.split("/")[-1]
        filename_aac = filename_mp3.replace(".mp3", ".aac")
        filepath_mp3 = os.path.join(audio_folder, filename_mp3)
        filepath_aac = os.path.join(audio_folder, filename_aac)

        # إذا كان ملف AAC موجوداً مسبقاً، نتخطى العملية
        if os.path.exists(filepath_aac):
            continue

        for attempt in range(3):
            try:
                print(f"[{reciter}] Downloading {filename_mp3}...")
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()

                with open(filepath_mp3, "wb") as out:
                    for chunk in r.iter_content(chunk_size=8192):
                        out.write(chunk)

                # --- عملية الترميز المسبق (CPU Workaround) ---
                print(f"🔄 جاري تحويل {filename_mp3} إلى AAC لتقليل استهلاك CPU البث...")
                convert_cmd = [
                    "ffmpeg", "-i", filepath_mp3,
                    "-acodec", "aac", "-b:a", "128k", "-ar", "44100",
                    filepath_aac, "-y"
                ]
                res = subprocess.run(convert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    print(f"❌ فشل تحويل {filename_mp3} -> {res.stderr.decode(errors='ignore')}")
                # حذف ملف MP3 الأصلي لتوفير المساحة
                if os.path.exists(filepath_mp3):
                    os.remove(filepath_mp3)
                    continue

                # حذف ملف MP3 الأصلي لتوفير المساحة (بعد نجاح التحويل)
                if os.path.exists(filepath_aac):
                    try:
                        os.remove(filepath_mp3)
                    except Exception:
                        pass
                    print(f"✅ تم التحميل والتحويل: {filename_aac}")
                time.sleep(3)
            except Exception as e:
                print(f"❌ محاولة فاشلة: {e}")
                time.sleep(3)

            
# ====== إنشاء قائمة تشغيل لقارئ ======
def create_playlist(reciter):
    audio_folder = os.path.join(RECITERS_FOLDER, reciter, "audio")
    if not os.path.exists(audio_folder):
        return []
    files = sorted(f for f in os.listdir(audio_folder) if f.endswith((".aac", ".mp3")))
    return [os.path.join(audio_folder, f) for f in files]



def cleanup_old_files(current_index, playlist, keep_backward=2, keep_forward=3):
    """
    تحذف الملفات البعيدة عن السورة الحالية لتوفير المساحة.
    keep_backward: عدد السور السابقة التي تود الاحتفاظ بها.
    keep_forward: عدد السور القادمة التي تود الاحتفاظ بها (مهم لضمان عدم انقطاع البث).
    """
    try:
        for i, filepath in enumerate(playlist):
            # إذا كان الملف خارج نطاق السور التي نريد الاحتفاظ بها
            if i < (current_index - keep_backward) or i > (current_index + keep_forward):
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️ تم حذف ملف قديم لتوفير مساحة: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء تنظيف الملفات: {e}")









# ====== البث الذكي ======
# ====== البث الذكي ======
def stream_loop():
    global ffmpeg_process
    current_reciter = None
    index = 0

    while True:
        try:
            # قراءة الإعدادات
            with config_lock:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)

            config_reciter = config.get("reciter")
            config_index = config.get("current_index", 0)

            # إذا تغير القارئ أو السورة
            if config_reciter != current_reciter or config_index != index:
                print(f"🔄 تغيير مكتشف -> القارئ: {config_reciter}, السورة: {config_index+1}")
                current_reciter = config_reciter
                index = config_index

                # قتل ffmpeg إن كان يعمل
                if ffmpeg_process and ffmpeg_process.poll() is None:
                    try:
                        ffmpeg_process.kill()
                        ffmpeg_process.wait()
                        print("⛔ تم إيقاف البث القديم")
                    except Exception as e:
                        print("⚠️ خطأ أثناء قتل ffmpeg:", e)

            # تحميل سورة واحدة فقط
            filepath = download_and_prepare_sura(current_reciter, index)

            if not filepath:
                print("❌ فشل تحميل السورة — إعادة المحاولة بعد 5 ثواني")
                time.sleep(5)
                continue

            filename = os.path.basename(filepath)
            sura_number = filename.split(".")[0]
            sura_name = SURA_NAMES.get(sura_number, sura_number)
            print("filepath =", filepath)

            print(f"📖 بدء بث سورة {sura_name} — القارئ: {current_reciter}")

            # أمر البث
            command = [
                "ffmpeg",
                "-re",
                "-i", filepath,
                "-vn",
                "-acodec", "copy",
                "-f", "flv",
                FULL_STREAM_URL
            ]

            ffmpeg_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )

            # انتظار انتهاء السورة
            while ffmpeg_process.poll() is None:
                time.sleep(1)

            # فحص الأخطاء
            stderr_output = ffmpeg_process.stderr.read().decode(errors="ignore")
            if ffmpeg_process.returncode != 0:
                print("❌ خطأ في FFmpeg:")
                print(stderr_output)
                time.sleep(3)
                continue

            print(f"✅ انتهت سورة {sura_name}")

            # حذف الملف بعد البث
            try:
                os.remove(filepath)
            except:
                pass

            # الانتقال للسورة التالية
            index += 1

            with config_lock:
                config["current_index"] = index
                with open(CONFIG_FILE, "w") as f:
                    json.dump(config, f)

        except Exception as e:
            print("💥 خطأ عام في stream_loop:", e)
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
@bot.message_handler(commands=['setreciter'])
def setreciter(message):
    global ffmpeg_process  # ضروري للتحكم في العملية

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
        # إذا أردت أن يبدأ القارئ الجديد من الفاتحة دائماً، أزل الـ # من السطر القادم
        # config["current_index"] = 0 

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    # هذا الجزء كان مفقوداً وهو ما يمنع التغيير الفوري
    if ffmpeg_process and ffmpeg_process.poll() is None:
        try:
            ffmpeg_process.kill()
            print("⛔ تم إيقاف السورة لتطبيق القارئ الجديد")
        except Exception as e:
            print(f"⚠️ خطأ عند قتل ffmpeg: {e}")

    bot.reply_to(message, f"✅ تم التغيير فوراً للقارئ: {name}")


@bot.message_handler(commands=['setsura'])
def setsura(message):
    global ffmpeg_process

    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ غير مصرح لك.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ الاستخدام الصحيح: /setsura 2")
        return

    try:
        sura_number = int(parts[1])
        if not (1 <= sura_number <= 114):
            raise ValueError

        new_index = sura_number - 1  # تحويل الرقم إلى فهرس 0-based

        # تحديث config مع index الجديد فقط (لا نغير القارئ هنا)
        with config_lock:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            config["current_index"] = new_index

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)

        # إيقاف البث الحالي فورًا ليبدأ من السورة الجديدة
        if ffmpeg_process and ffmpeg_process.poll() is None:
            try:
                ffmpeg_process.kill()
                print("⛔ تم إيقاف السورة الحالية لتطبيق السورة الجديدة")
            except Exception as e:
                print(f"⚠️ خطأ عند قتل ffmpeg: {e}")

        sura_name = SURA_NAMES.get(str(sura_number).zfill(3), str(sura_number))
        bot.reply_to(message, f"✅ سيتم الانتقال فورًا إلى سورة {sura_name}")

    except ValueError:
        bot.reply_to(message, "❌ رقم سورة غير صحيح. اختر من 1 إلى 114.")
    except Exception as e:
        bot.reply_to(message, f"🔥 خطأ غير متوقع: {e}")

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

