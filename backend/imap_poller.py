import asyncio
import imaplib
import email
import traceback
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from datetime import timedelta, timezone

from db import session_scope
from models import Lead, Reply, utcnow
from config import settings

CHECK_SECONDS = 120


def _decode(value):
    if not value:
        return ""
    parts = []
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            parts.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(text)
    return "".join(parts)


def _body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace").strip()


def _received(msg):
    try:
        dt = parsedate_to_datetime(msg.get("Date"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return utcnow()


def poll():
    if not settings.imap_ready():
        return

    server = None
    try:
        with session_scope() as session:
            leads = {}
            for lead in session.query(Lead).all():
                if lead.email:
                    leads[lead.email.strip().lower()] = lead.id
            if not leads:
                return

            server = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
            server.login(settings.imap_user, settings.imap_password)
            server.select("INBOX", readonly=True)

            since = (utcnow() - timedelta(days=30)).strftime("%d-%b-%Y")
            typ, data = server.search(None, f"(SINCE {since})")
            if typ != "OK":
                return

            for num in data[0].split()[-100:]:
                typ, fetched = server.fetch(num, "(BODY.PEEK[])")
                if typ != "OK" or not fetched or not fetched[0]:
                    continue
                msg = email.message_from_bytes(fetched[0][1])
                from_addr = parseaddr(msg.get("From"))[1].strip().lower()
                lead_id = leads.get(from_addr)
                if not lead_id:
                    continue

                message_id = (msg.get("Message-ID") or "").strip() or f"{from_addr}:{num.decode()}"
                if session.query(Reply).filter(Reply.message_id == message_id).first():
                    continue

                reply = Reply(
                    lead_id=lead_id,
                    from_email=from_addr,
                    subject=_decode(msg.get("Subject")),
                    body=_body(msg),
                    message_id=message_id,
                    received_at=_received(msg),
                )
                session.add(reply)
                try:
                    session.commit()
                except Exception:
                    session.rollback()
    except Exception:
        traceback.print_exc()
    finally:
        if server is not None:
            try:
                server.logout()
            except Exception:
                pass


async def loop():
    while True:
        await asyncio.to_thread(poll)
        await asyncio.sleep(CHECK_SECONDS)
