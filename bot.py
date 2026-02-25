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

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("setreciter", setreciter))

def start_bot():
    app.run_polling()
