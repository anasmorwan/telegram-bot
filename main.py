import threading
from schedule import scheduler
from contents import send_messages, send_daily_post

# الجمعة
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=9, minute=0)
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=16, minute=30)
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=20, minute=0)

# كل يومين
scheduler.add_job(send_daily_post, 'interval', days=2, hour=10, minute=0)

scheduler.start()



  # تعيين webhook قبل بدء الخادم
set_webhook()
    
# تشغيل Flask في thread منفصل
t1 = Thread(target=run_flask)
t1.daemon = True
t1.start()
    
# تشغيل البث في thread منفصل
t2 = Thread(target=stream_loop)
t2.daemon = True
  
t2.start()

    
print("Bot started with Webhook...")
    
    

 # ====== Main ======
if __name__ == "__main__":   
  # إبقاء البرنامج قيد التشغيل
  try:
      while True:
          time.sleep(1)
  except KeyboardInterrupt:
      print("🛑 إيقاف البوت...")
      bot.remove_webhook()

