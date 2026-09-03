import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


class Settings:
    def __init__(self):
        self.reload()

    def reload(self):
        load_dotenv(ENV_PATH, override=True)

        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://kiberchekap:kiberchekap@localhost:5432/kiberchekap",
        )

        local_origins = [
            "http://localhost:8090",
            "http://127.0.0.1:8090",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
        ]
        configured = [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "").split(",")
            if origin.strip()
        ]
        self.cors_origins = configured + [
            origin for origin in local_origins if origin not in configured
        ]

        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        self.sender_name = os.getenv("SENDER_NAME", "Киберчекап")
        self.sender_email = os.getenv("SENDER_EMAIL", "") or self.smtp_user
        self.site_url = os.getenv("SITE_URL", "")

        self.imap_host = os.getenv("IMAP_HOST", "")
        self.imap_port = int(os.getenv("IMAP_PORT", 993))
        self.imap_user = os.getenv("IMAP_USER", "")
        self.imap_password = os.getenv("IMAP_PASSWORD", "")

        self.admin_login = os.getenv("ADMIN_LOGIN", "")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "")

        try:
            self.schedule_interval_days = int(os.getenv("SCHEDULE_INTERVAL_DAYS", 7))
        except ValueError:
            self.schedule_interval_days = 7
        if self.schedule_interval_days < 1:
            self.schedule_interval_days = 1

    def is_configured(self):
        return bool(self.admin_login and self.admin_password)

    def imap_ready(self):
        return bool(self.imap_host and self.imap_user and self.imap_password)


settings = Settings()
