from models import Lead, EmailLog
from notifications.email_notifier import EmailNotifier
from notifications.templates import TEMPLATES
from notifications.chain import SUBJECTS


class NotificationService:

    def __init__(self):
        self.email = EmailNotifier()
        self.notifiers = [self.email]

    def notify(self, lead: Lead, event: str) -> None:
        for notifier in self.notifiers:
            try:
                notifier.notify(lead, event)
            except Exception as e:
                print(f"[{notifier.__class__.__name__}] Ошибка отправки: {e}")

    def send_event(self, session, lead: Lead, event: str) -> EmailLog:
        """Отправляет письмо цепочки и записывает результат в журнал."""
        log = EmailLog(
            lead_id=lead.id,
            event=event,
            subject=SUBJECTS.get(event, event),
            status="sent",
        )
        if not lead.email:
            log.status = "error"
            log.error = "У лида нет email"
        elif event not in TEMPLATES:
            log.status = "error"
            log.error = "Нет шаблона письма"
        else:
            try:
                self.email.send(lead, event)
            except Exception as e:
                log.status = "error"
                log.error = str(e)[:500]
                print(f"[send_event] {event} -> {lead.email}: {e}")
        session.add(log)
        session.commit()
        return log


notification_service = NotificationService()


def sent_events(session, lead) -> set:
    """Письма лида, которые действительно ушли. Неудачную отправку можно повторить."""
    rows = (
        session.query(EmailLog)
        .filter(EmailLog.lead_id == lead.id, EmailLog.status == "sent")
        .all()
    )
    return {r.event for r in rows}
