import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import YOUR_EMAIL, YOUR_NAME, GMAIL_APP_PASSWORD


def send_email(to_email: str, subject: str, body_html: str, body_text: str = None):
    """Send a single email via Gmail SMTP using an App Password."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{YOUR_NAME} <{YOUR_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = YOUR_EMAIL

    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(YOUR_EMAIL, to_email, msg.as_string())
