import os
import telebot
import requests
import random
import schedule
import time
from datetime import datetime

# ========== إعدادات البوت ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@Anwar_Eslam"
bot = telebot.TeleBot(BOT_TOKEN)

# ========== قاعدة البيانات المحلية ==========
HADITHS = [
    {"text": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى", "source": "رواه البخاري ومسلم"},
    {"text": "لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه", "source": "رواه البخاري"},
    {"text": "اتق الله حيثما كنت، وأتبع السيئة الحسنة تمحها، وخالق الناس بخلق حسن", "source": "رواه الترمذي"},
    {"text": "من حسن إسلام المرء تركه ما لا يعنيه", "source": "رواه الترمذي"},
    {"text": "تبسمك في وجه أخيك صدقة", "source": "رواه الترمذي"},
]

QUOTES = [
    "خير الناس أنفعهم للناس",
    "الكلمة الطيبة صدقة",
    "نظافة الجسم من الإيمان",
    "من سار على الدرب وصل",
]
JUMUAH_MORNING = [
    "📖 الجمعة.. لا تنس سورة الكهف\nهل بدأت؟ 👇",
    "📿 أكثر من الصلاة على النبي ﷺ\nاكتب: صليت ✔️",
    "🕌 يوم مبارك بدأ الآن\nاستغفر 10 مرات",
    "📖 الكهف نور لك اليوم\nابدأ ولو بآيات",
    "📿 صلِّ على النبي ﷺ الآن\nثم قل: تم 🤍",
]
JUMUAH_ASR = [
    "🤲 ساعة استجابة الآن\nاكتب دعاءك",
    "🕌 لا تضيع هذه اللحظات\nادعُ بقلب حاضر",
    "📿 أكثر من الذكر الآن\nثم قل: تم ✔️",
    "🤲 اليوم فرصة لا تعوّض\nما دعاؤك الآن؟",
    "📖 إن لم تقرأ الكهف بعد\nابدأ الآن 👇",
]
JUMUAH_EVENING = [
    "📿 هل صليت على النبي ﷺ اليوم؟\nاكتب: تم ✔️",
    "📖 هل أنهيت سورة الكهف؟\nأخبرنا 👇",
    "🤲 اختم يومك بدعاء\nاكتب دعاءك الآن",
    "🕌 الجمعة شارفت على النهاية\nلا تفوّت الأجر",
    "📿 دقيقة ذكر قبل النوم\nابدأ الآن",
]

JUMUAH_REMINDERS = [
    "📿 الجمعة.. أكثر من الصلاة على النبي ﷺ\nاكتب: صليت ✔️",
    "📖 لا تنسوا سورة الكهف\nهل بدأت؟ 👇",
    "🤲 ساعة استجابة.. لا تضيعها\nاكتب دعاءك الآن",
    "🕌 الجمعة فرصة قريبة\nاستغفر الآن 10 مرات",
    "📿 صلِّ على النبي ﷺ\nثم قل: تم 🤍",
    "📖 الكهف نور لك\nارجع بعد ساعة وقل: أنهيت ✔️",
    "🤲 دعوة صادقة قد تغيّر يومك\nادعُ الآن",
    "🕌 اليوم جمعة\nمن ستدعو له اليوم؟",
]
JUMUAH_RANDOMS = [
    "📿 يوم الجمعة.. أكثروا من الصلاة على النبي ﷺ.",
    "🌿 لا تنسوا قراءة سورة الكهف.. نور لكم ما بين الجمعتين.",
    "🕊️ ساعة استجابة اليوم.. لا تضيعوها بالدعاء.",
    "📖 الجمعة فرصة لفتح صفحة جديدة مع الله.",
    "💡 اللهم اجعل لنا في هذا اليوم نورًا وبركة.",
    "🤍 صلّوا على من أُرسل رحمة للعالمين ﷺ.",
    "🌙 اغتنموا هذا اليوم المبارك بالذكر والدعاء.",
    "📿 الجمعة تذكير بأن القلوب تحتاج صيانة.. بالقرآن.",
    "🕌 يوم الجمعة.. جدد نيتك واقترب أكثر.",
    "🌸 دعوة صادقة قد تغيّر كل شيء.. لا تبخل بها اليوم.",
    "📖 لا تنسوا الكهف.. ولو بضع آيات.",
]

# ========== وظائف جلب البيانات ==========

def clean_text_cut(text, max_length=400):
    """تقليل طول النص دون قطع الكلمات في المنتصف"""
    if len(text) <= max_length:
        return text
    # القطع عند آخر مسافة قبل الحد الأقصى
    return text[:max_length].rsplit(' ', 1)[0] + "..."

def get_ayah_with_tafsir():
    try:
        # جلب آية عشوائية (باستخدام معرف عشوائي من 1 إلى 6236)
        random_ayah_id = random.randint(1, 6236)
        
        # طلب نص الآية والتفسير الميسر واسم السورة في طلبات متوازية أو متتالية
        # نستخدم إصدار ar.muyassar للتفسير مباشرة
        url_ayah = f"https://api.alquran.cloud/v1/ayah/{random_ayah_id}/ar.alafasy"
        url_tafsir = f"https://api.alquran.cloud/v1/ayah/{random_ayah_id}/ar.muyassar"
        
        res_ayah = requests.get(url_ayah, timeout=10).json()
        res_tafsir = requests.get(url_tafsir, timeout=10).json()
        
        if res_ayah['code'] == 200 and res_tafsir['code'] == 200:
            ayah_text = res_ayah['data']['text']
            tafsir_text = res_tafsir['data']['text']
            surah_name = res_ayah['data']['surah']['name']
            ayah_num = res_ayah['data']['numberInSurah']
            
            # معالجة طول التفسير
            short_tafsir = clean_text_cut(tafsir_text)
            
            formatted_msg = (
                f"📖 سورة {surah_name} (الآية {ayah_num})\n\n"
                f"« {ayah_text} »\n\n"
                f"🌿 التفسير الميسر:\n{short_tafsir}"
            )
            return formatted_msg
    except Exception as e:
        print(f"Error fetching API: {e}", flush=True)
    return None

def get_random_content():
    choice = random.random()
    

    content = get_ayah_with_tafsir()

    if content:
        return content
    
    else:
        h = random.choice(HADITHS)
        return f"🕌 *حديث نبوي شريف:*\n\n{h['text']}\n\n📚 _{h['source']}_"
    

import random
from datetime import datetime

def get_jumuah_reminders():
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour

    if weekday == 4:  # يوم الجمعة

        # 🟢 صباح الجمعة (5 - 12)
        if 5 <= hour < 12:
            return random.choice(JUMUAH_MORNING)

        # 🟡 بعد العصر (12 - 18)
        elif 12 <= hour < 18:
            return random.choice(JUMUAH_ASR)

        # 🔵 مساء الجمعة (18 - 23)
        elif 18 <= hour < 23:
            return random.choice(JUMUAH_EVENING)

    return None
    
    
# ========== نظام الإرسال ==========

def send_daily_post():
    print(f"[{datetime.now()}] جاري تجهيز المنشور...")
    content = get_random_content()
    
    if content:
        try:
            # استخدام Markdown (V2) أو Markdown العادي لتحسين المظهر
            bot.send_message(CHANNEL_ID, content, parse_mode='Markdown')
            print(f"[{datetime.now()}] تم الإرسال بنجاح ✅")
        except Exception as e:
            print(f"❌ خطأ في الإرسال: {e}")
    else:
        print("❌ فشل في تكوين المحتوى")

# ========== الجدولة الموثوقة ==========
# جدولة الإرسال كل يومين في ساعة محددة (مثلاً 10 صباحاً)
schedule.every(2).days.at("10:00").do(send_daily_post)



def run_task():
    while True:
        try:
            schedule.run_pending()
            time.sleep(60) # فحص المهام كل دقيقة
        except Exception as e:
            print(f"خطأ في نظام الجدولة: {e}")
            time.sleep(10)
