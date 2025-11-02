from celery import Celery
from services.smtp import send_email

app = Celery("email_tasks", broker="redis://localhost:6379/0")

@app.task
def send_daily_email():
    print("Email sent successfully")
    send_email()