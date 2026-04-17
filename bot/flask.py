from flask import Flask, request, Response


app = Flask(__name__)


# ====== Flask uptime ======
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




# ====== Flask Webhook ======
WEBHOOK_URL = "/webhook"

@app.route(WEBHOOK_URL, methods=["POST"])
def webhook():
    """استقبال التحديثات من تيليغرام"""
    if request.headers.get("content-type") == "application/json":
        json_data = request.get_json()
        try:
            # معالجة التحديث
            bot.process_new_updates([telebot.types.Update.de_json(json_data)])
        except Exception as e:
            print(f"خطأ في معالجة webhook: {e}")
        return Response("OK", status=200)
    return Response("Bad Request", status=403)


def set_webhook():
    global base_url
    
    if base_url:
        webhook_url = f"{base_url}{WEBHOOK_URL}"
        try:
            bot.remove_webhook()
            bot.set_webhook(url=webhook_url)
            print(f"✅ Webhook set to: {webhook_url}")
        except Exception as e:
            print(f"❌ فشل تعيين webhook: {e}")
    else:
        print("⚠️ لم يتم العثور على URL للـ webhook، سيتم استخدام polling بدلاً من ذلك")
        # بدء polling كبديل
        threading.Thread(target=bot.infinity_polling, daemon=True).start()


def run_flask():
    """تشغيل خادم Flask"""
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

