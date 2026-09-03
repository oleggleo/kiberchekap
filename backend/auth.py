import os
import hmac
import base64
import hashlib

from config import settings

COOKIE_NAME = "kc_session"


def _secret():
    return (settings.admin_password + "|" + settings.admin_login).encode("utf-8")


def _sign(payload):
    return hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def authenticate(login, password):
    login = login or ""
    password = password or ""
    if (settings.is_configured()
            and hmac.compare_digest(login, settings.admin_login)
            and hmac.compare_digest(password, settings.admin_password)):
        return "admin"

    from db import session_scope
    from models import User
    with session_scope() as session:
        user = session.query(User).filter(User.login == login).first()
        if user and verify_password(password, user.password_hash):
            return user.role
    return None


def make_session_value(login, role):
    payload = base64.urlsafe_b64encode(f"{login}\t{role}".encode("utf-8")).decode()
    return payload + "." + _sign(payload)


def read_session(request):
    token = request.cookies.get(COOKIE_NAME, "")
    if "." not in token:
        return None
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        login, role = base64.urlsafe_b64decode(payload).decode("utf-8").split("\t", 1)
    except Exception:
        return None
    return {"login": login, "role": role}


def is_logged_in(request):
    return read_session(request) is not None


def is_admin(request):
    session = read_session(request)
    return bool(session and session["role"] == "admin")
