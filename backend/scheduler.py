"""
Фоновая авторассылка недельных писем.

Если у лида включена авторассылка, планировщик сам отправляет очередное недельное
письмо, когда подошёл срок. Интервал берётся из настроек. После пятой недели
рассылка останавливается, дальше итог выбирает менеджер вручную. Состояние хранится
в базе, поэтому после перезапуска приложение подхватывает и досылает пропущенное.
"""

import asyncio
import traceback
from datetime import timedelta

from db import session_scope
from models import Lead, utcnow
from notifications import chain
from notifications.service import notification_service, sent_events
from config import settings

CHECK_SECONDS = 60


def tick():
    with session_scope() as session:
        try:
            now = utcnow()
            interval = settings.schedule_interval_days
            leads = (
                session.query(Lead)
                .filter(
                    Lead.auto_active.is_(True),
                    Lead.next_send_at.isnot(None),
                    Lead.next_send_at <= now,
                )
                .all()
            )
            for lead in leads:
                sent = sent_events(session, lead)
                event = chain.next_scheduled(sent)
                if event is None:
                    lead.auto_active = False
                    lead.next_send_at = None
                    session.commit()
                    continue

                notification_service.send_event(session, lead, event)

                sent.add(event)
                if chain.next_scheduled(sent) is None:
                    lead.auto_active = False
                    lead.next_send_at = None
                else:
                    lead.next_send_at = now + timedelta(days=interval)
                session.commit()
        except Exception:
            traceback.print_exc()


async def loop():
    while True:
        await asyncio.to_thread(tick)
        await asyncio.sleep(CHECK_SECONDS)
