from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()



# صباح الجمعة
scheduler.add_job(
    send_messages,
    trigger='cron',
    day_of_week='fri',
    hour=9,
    minute=0
)

# بعد العصر
scheduler.add_job(
    send_messages,
    trigger='cron',
    day_of_week='fri',
    hour=16,
    minute=30
)

# مساء
scheduler.add_job(
    send_messages,
    trigger='cron',
    day_of_week='fri',
    hour=20,
    minute=0
)


scheduler.add_job(
    send_daily_post,
    trigger='interval',
    days=2,
    hour=10,
    minute=0
)
