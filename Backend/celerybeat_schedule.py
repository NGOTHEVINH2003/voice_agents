from celery.schedules import crontab
from tasks import app

app.conf.beat_schedules = {
    "send-email-test": {
        "task": "tasks.send_daily_email",
        "schedule": crontab(hour=16, minute=15),
    },
}