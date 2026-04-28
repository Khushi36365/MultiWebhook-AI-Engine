import smtplib
from email.mime.text import MIMEText
from core.config import EMAIL_USER, EMAIL_PASS


def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        return {"status": "success", "message": "Email sent"}

    except Exception as e:
        return {"status": "error", "message": str(e)}