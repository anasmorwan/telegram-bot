from apscheduler.schedulers.background import BackgroundScheduler
from content import send_smart_message

scheduler = BackgroundScheduler()



# صباح الجمعة
scheduler.add_job(
    send_smart_message,
    trigger='cron',
    day_of_week='fri',
    hour=9,
    minute=0
)

# بعد العصر
scheduler.add_job(
    send_smart_message,
    trigger='cron',
    day_of_week='fri',
    hour=16,
    minute=30
)

# مساء
scheduler.add_job(
    send_smart_message,
    trigger='cron',
    day_of_week='fri',
    hour=20,
    minute=0
)
