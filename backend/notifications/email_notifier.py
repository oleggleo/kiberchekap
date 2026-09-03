import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from models import Lead
from notifications.base import BaseNotifier
from notifications.templates import TEMPLATES
from config import settings


class EmailNotifier(BaseNotifier):

    def can_notify(self, lead: Lead) -> bool:
        return bool(lead.email)

    def send(self, lead: Lead, event: str) -> None:
        template = TEMPLATES.get(event)
        if template is None:
            print(f"[EmailNotifier] Нет шаблона для события '{event}'")
            return

        subject, html = template(lead)

        sender = settings.sender_email or settings.smtp_user

        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((settings.sender_name, sender))
        msg["To"] = lead.email
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(sender, lead.email, msg.as_string())