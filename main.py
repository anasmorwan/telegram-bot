from schedule import scheduler
from contents import send_messages, send_daily_post

# الجمعة
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=9, minute=0)
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=16, minute=30)
scheduler.add_job(send_messages, 'cron', day_of_week='fri', hour=20, minute=0)

# كل يومين
scheduler.add_job(send_daily_post, 'interval', days=2, hour=10, minute=0)

scheduler.start()

