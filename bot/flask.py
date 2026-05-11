from flask import Flask, jsonify, render_template, request, Response

import json

app = Flask(__name__)

CURRENT_SURAH = 1
CURRENT_AYAH = 1

@app.route("/mushaf")
def mushaf():

    with open("quran/1.json", "r", encoding="utf-8") as f:
        surah_data = json.load(f)

    return render_template(
        "mushaf.html",
        surah=surah_data,
        current_ayah=CURRENT_AYAH
    )

@app.route("/current")
def current():
    return jsonify({
        "surah": CURRENT_SURAH,
        "ayah": CURRENT_AYAH
    })

app.run(debug=True)



#-----------------------------
#-----------------------------
#-----------------------------
#-----------------------------
#-----------------------------



# ====== Flask uptime ======
@app.route("/")
def home():
    return "Alive", 200


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

