from config import ENV_PATH

KEYS = [
    "DATABASE_URL",
    "CORS_ORIGINS",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SENDER_NAME",
    "SENDER_EMAIL",
    "SITE_URL",
    "IMAP_HOST",
    "IMAP_PORT",
    "IMAP_USER",
    "IMAP_PASSWORD",
    "SCHEDULE_INTERVAL_DAYS",
    "ADMIN_LOGIN",
    "ADMIN_PASSWORD",
]


def read_env():
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def write_env(new_values):
    values = read_env()
    for key, value in new_values.items():
        if value is not None:
            values[key] = str(value)

    lines = []
    for key in KEYS:
        if key in values:
            lines.append(f"{key}={values[key]}")
    for key, value in values.items():
        if key not in KEYS:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
