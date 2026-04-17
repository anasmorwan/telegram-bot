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

# أمر إيقاف البث
@bot.message_handler(commands=['stopstream'])
def stop_stream(message):
    if not is_admin(message.from_user.id): return
    
    with config_lock:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        config["is_streaming"] = False
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
            
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.kill()
    
    bot.reply_to(message, "🛑 تم إيقاف البث بنجاح. لن يتم تحميل أي سور جديدة.")

# أمر تشغيل البث
@bot.message_handler(commands=['startstream'])
def start_stream(message):
    if not is_admin(message.from_user.id): return
    
    with config_lock:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        config["is_streaming"] = True
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
            
    bot.reply_to(message, "▶️ تم تفعيل البث. سيبدأ العمل خلال لحظات...")

# أمر إعادة التشغيل (في حال حدوث مشكلة)
@bot.message_handler(commands=['restartstream'])
def restart_stream(message):
    if not is_admin(message.from_user.id): return
    
    bot.reply_to(message, "🔄 جاري إعادة تشغيل عملية البث...")
    
    # قتل العملية الحالية لإجبار Loop البث على البدء من جديد
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.kill()
    else:
        # إذا كانت العملية متوقفة أصلاً، نتأكد من تفعيل العلم في config
        with config_lock:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            config["is_streaming"] = True
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)





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
