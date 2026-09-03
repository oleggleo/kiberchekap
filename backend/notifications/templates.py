"""
Готовые HTML-письма цепочки лежат рядом, в папке letters.

Вёрстка писем менять не нужно. В тексте стоят метки, они подставляются при отправке:
  #NAME#  имя клиента из заявки
  #NS#    недопустимое событие (поле «выявленная проблема» лида)
Пустая ссылка кнопки в первом письме ведёт на адрес сайта из настроек.
"""

from pathlib import Path
from html import escape

from models import Lead
from config import settings
from notifications.chain import SUBJECTS

LETTERS_DIR = Path(__file__).resolve().parent / "letters"

_cache = {}


def _raw(event: str) -> str:
    if event not in _cache:
        path = LETTERS_DIR / f"{event}.html"
        _cache[event] = path.read_text(encoding="utf-8") if path.exists() else ""
    return _cache[event]


def render(event: str, lead: Lead) -> tuple[str, str]:
    subject = SUBJECTS.get(event, event)
    html = _raw(event)
    html = html.replace("#NAME#", escape(lead.name or ""))
    html = html.replace("#NS#", escape(lead.cyber_problem or ""))
    if settings.site_url:
        html = html.replace('href=""', f'href="{escape(settings.site_url)}"')
    return subject, html


def _make(event):
    def _render(lead: Lead) -> tuple[str, str]:
        return render(event, lead)
    return _render


# Реестр шаблонов по событию цепочки
TEMPLATES = {event: _make(event) for event in SUBJECTS}
