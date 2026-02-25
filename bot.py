import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CONFIG_FILE = "config.json"
RECITERS_FOLDER = "reciters"

def get_reciters():
    return os.listdir(RECITERS_FOLDER)

def set_reciter(name):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"reciter": name}, f)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    await update.message.reply_text(f"Current reciter: {config['reciter']}")

async def setreciter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setreciter sudais")
        return

    name = context.args[0]

    if name not in get_reciters():
        await update.message.reply_text("Reciter not found.")
        return

    set_reciter(name)
    await update.message.reply_text(f"Switched to {name}")




import requests
import tempfile
import os
from datetime import datetime

API_URL = "https://mp3quran.net/api/v3/reciters?language=ar"

async def buildreciter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("غير مصرح.")
        return

    if not context.args:
        await update.message.reply_text("استخدم:\n/buildreciter اسم_القارئ")
        return

    target_name = " ".join(context.args).strip()

    await update.message.reply_text("⏳ جاري البحث عن القارئ...")

    try:
        response = requests.get(API_URL, timeout=20)
        data = response.json()
        reciters = data.get("reciters", [])

        reciter_data = None

        # البحث المطابق
        for r in reciters:
            if target_name in r["name"]:
                reciter_data = r
                break

        if not reciter_data:
            await update.message.reply_text("❌ لم يتم العثور على القارئ.")
            return

        # اختيار مصحف حفص إن وجد
        moshaf_list = reciter_data.get("moshaf", [])

        selected_moshaf = None
        for m in moshaf_list:
            if "حفص" in m.get("name", ""):
                selected_moshaf = m
                break

        # إن لم يوجد حفص نأخذ أول مصحف متاح
        if not selected_moshaf and moshaf_list:
            selected_moshaf = moshaf_list[0]

        if not selected_moshaf:
            await update.message.reply_text("⚠️ لا يوجد مصحف متاح لهذا القارئ.")
            return

        server = selected_moshaf.get("server")

        if not server:
            await update.message.reply_text("⚠️ لا يوجد رابط سيرفر صالح.")
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

        await update.message.reply_document(
            document=open(tmp_path, "rb"),
            filename=f"{reciter_data['name']}.txt"
        )

        os.remove(tmp_path)

        await update.message.reply_text("✅ تم إنشاء الملف بنجاح.")

    except requests.exceptions.RequestException:
        await update.message.reply_text("❌ خطأ في الاتصال بالـ API.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ غير متوقع: {str(e)}")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("setreciter", setreciter))
app.add_handler(CommandHandler("buildreciter", buildreciter))
def start_bot():
    app.run_polling()
