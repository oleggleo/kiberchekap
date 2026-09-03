from html import escape

from notifications import chain

STATUS = {
    "new": ("Новая", "#b45309", "#fef3c7"),
    "approved": ("Одобрена", "#047857", "#d1fae5"),
    "rejected": ("Отклонена", "#b91c1c", "#fee2e2"),
}


def _status_pill(status):
    label, color, bg = STATUS.get(status, (status or "new", "#475569", "#e2e8f0"))
    return (
        f'<span style="display:inline-block;padding:3px 11px;border-radius:999px;'
        f'font-size:12px;font-weight:600;color:{color};background:{bg};'
        f'font-family:Manrope,sans-serif;white-space:nowrap;">{escape(label)}</span>'
    )


def _okved(lead):
    if not lead.okved_code:
        return ""
    code = f'<span class="mono">{escape(lead.okved_code)}</span>'
    return f"{code} {escape(lead.okved_name or '')}"


def _fmt_date(value):
    if not value:
        return ""
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except AttributeError:
        return str(value)


HEAD = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Unbounded:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:#0f1729; --muted:#64748b; --faint:#94a3b8;
    --line:#e6eaf1; --card:#ffffff; --app:#eef1f6;
    --accent:#0a9396; --accent-dark:#087f82; --accent-soft:#e0f2f2;
    --sidebar:#0f1729; --sidebar-soft:#1b2740;
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; height:100%; }}
  body {{
    font-family:Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    color:var(--ink); background:var(--app);
    font-size:14px; line-height:1.5;
    -webkit-font-smoothing:antialiased;
  }}
  .shell {{ display:flex; min-height:100vh; }}

  .side {{
    width:236px; flex:0 0 236px; background:var(--sidebar); color:#cbd5e1;
    display:flex; flex-direction:column; padding:22px 16px;
    position:sticky; top:0; height:100vh;
  }}
  .brand {{
    font-family:Unbounded,sans-serif; font-weight:700; font-size:19px;
    color:#fff; letter-spacing:-0.01em; padding:0 8px 22px;
    display:flex; align-items:center; gap:9px;
  }}
  .brand .dot {{ width:10px; height:10px; border-radius:3px; background:var(--accent); box-shadow:0 0 12px var(--accent); }}
  .nav a {{
    display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:9px;
    color:#aab6c9; text-decoration:none; font-weight:600; font-size:14px; margin-bottom:3px;
  }}
  .nav a:hover {{ background:var(--sidebar-soft); color:#fff; }}
  .nav a.active {{ background:var(--accent); color:#fff; }}
  .side-foot {{ margin-top:auto; padding:0 8px; }}
  .side-foot a {{ color:var(--faint); text-decoration:none; font-size:13px; }}
  .side-foot a:hover {{ color:#fff; }}

  .main {{ flex:1; min-width:0; display:flex; flex-direction:column; }}
  .top {{
    display:flex; align-items:baseline; gap:14px; padding:26px 34px 0;
  }}
  .top h1 {{ font-family:Unbounded,sans-serif; font-weight:700; font-size:25px; margin:0; letter-spacing:-0.02em; }}
  .top .count {{ color:var(--muted); font-size:14px; font-weight:500; }}
  .content {{ padding:22px 34px 40px; }}

  .stats {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:22px; }}
  .stat {{
    background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:16px 20px; min-width:150px; flex:1;
  }}
  .stat .k {{ font-size:12px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.05em; }}
  .stat .v {{ font-family:"JetBrains Mono",monospace; font-size:28px; font-weight:500; margin-top:6px; font-variant-numeric:tabular-nums; }}
  .stat.a .v {{ color:var(--accent); }}

  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; }}
  .table-wrap {{ overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{
    text-align:left; font-size:11.5px; font-weight:700; color:var(--muted);
    text-transform:uppercase; letter-spacing:0.05em; padding:14px 18px;
    border-bottom:1px solid var(--line); background:#fafbfd; white-space:nowrap;
  }}
  td {{ padding:14px 18px; border-bottom:1px solid var(--line); vertical-align:middle; }}
  tr:last-child td {{ border-bottom:none; }}
  tr.row:hover td {{ background:#f8fafc; }}
  .id {{ font-family:"JetBrains Mono",monospace; color:var(--faint); font-size:13px; }}
  .name {{ font-weight:700; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .open {{
    color:var(--accent); font-weight:700; text-decoration:none; font-size:13px; white-space:nowrap;
  }}
  .open:hover {{ text-decoration:underline; }}
  .empty {{ padding:56px 20px; text-align:center; color:var(--muted); }}

  a.back {{ color:var(--muted); text-decoration:none; font-size:13px; font-weight:600; }}
  a.back:hover {{ color:var(--ink); }}
  .detail {{ display:grid; grid-template-columns:2fr 1fr; gap:18px; align-items:start; }}
  @media (max-width:820px) {{ .detail {{ grid-template-columns:1fr; }} .side {{ display:none; }} }}
  .field {{ display:flex; justify-content:space-between; gap:16px; padding:13px 0; border-bottom:1px solid var(--line); }}
  .field:last-child {{ border-bottom:none; }}
  .field .l {{ color:var(--muted); font-size:13px; font-weight:600; }}
  .field .r {{ text-align:right; font-weight:600; word-break:break-word; }}
  .field .r.mono {{ font-family:"JetBrains Mono",monospace; font-weight:500; }}
  .pad {{ padding:20px 22px; }}
  .pad h2 {{ font-family:Unbounded,sans-serif; font-size:15px; margin:0 0 4px; font-weight:600; }}
  .pad .hint {{ color:var(--muted); font-size:13px; margin:0 0 14px; }}
  label {{ display:block; font-size:12.5px; font-weight:700; color:var(--muted); margin-bottom:6px; }}
  textarea, input.text {{
    width:100%; border:1px solid #cfd8e3; border-radius:9px; padding:10px 12px;
    font-family:Manrope,sans-serif; font-size:14px; resize:vertical;
  }}
  textarea:focus, input.text:focus {{ outline:2px solid var(--accent-soft); border-color:var(--accent); }}
  .btn {{
    display:inline-flex; align-items:center; justify-content:center; gap:8px;
    padding:11px 18px; border-radius:9px; border:none; cursor:pointer;
    font-family:Manrope,sans-serif; font-weight:700; font-size:14px; text-decoration:none;
  }}
  .btn-primary {{ background:var(--accent); color:#fff; width:100%; }}
  .btn-primary:hover {{ background:var(--accent-dark); }}
  .btn-ghost {{ background:#eef2f7; color:var(--ink); }}
  .btn-ghost:hover {{ background:#e3e9f1; }}
  .btn:disabled {{ opacity:0.5; cursor:default; }}
  .done {{
    display:flex; align-items:center; gap:8px; justify-content:center;
    padding:11px; border-radius:9px; background:var(--accent-soft); color:var(--accent-dark);
    font-weight:700; font-size:14px;
  }}
  .mb {{ margin-bottom:18px; }}

  .tl-group h3 {{ font-family:Unbounded,sans-serif; font-size:12px; margin:20px 0 4px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:0.05em; }}
  .tl-group:first-child h3 {{ margin-top:2px; }}
  .tl-item {{ display:flex; align-items:center; gap:12px; padding:11px 0; border-bottom:1px solid var(--line); }}
  .tl-item:last-child {{ border-bottom:none; }}
  .tl-item .t {{ flex:1; min-width:0; font-weight:600; }}
  .tl-item.locked .t {{ color:var(--faint); font-weight:500; }}
  .tl-item .err-note {{ color:#b91c1c; font-weight:500; font-size:12.5px; margin-top:2px; }}
  .tl-actions {{ display:flex; align-items:center; gap:10px; white-space:nowrap; }}
  .pill {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }}
  .pill.ok {{ color:#047857; background:#d1fae5; }}
  .pill.wait {{ color:var(--accent-dark); background:var(--accent-soft); }}
  .pill.off {{ color:#64748b; background:#eef2f7; }}
  .pill.err {{ color:#b91c1c; background:#fee2e2; }}
  .mini {{ font-size:12.5px; color:var(--accent); text-decoration:none; font-weight:600; }}
  .mini:hover {{ text-decoration:underline; }}
  .btn-sm {{ padding:7px 14px; font-size:13px; width:auto; }}
  .auto-box {{ background:#f8fafc; border:1px solid var(--line); border-radius:10px; padding:12px 14px; margin:2px 0 10px; font-size:13px; color:var(--muted); line-height:1.5; }}
  .auto-box form {{ display:inline; }}
  .auto-box .btn {{ margin-top:8px; }}
  form.inline {{ display:inline; }}
</style>
</head>
<body>"""


def _layout(title, active, body, role="admin"):
    def cls(name):
        return "active" if name == active else ""
    setup_link = f'<a class="{cls("setup")}" href="/setup">Настройки</a>' if role == "admin" else ""
    return HEAD.format(title=escape(title)) + f"""
<div class="shell">
  <aside class="side">
    <div class="brand"><span class="dot"></span>Киберчекап</div>
    <nav class="nav">
      <a class="{cls('leads')}" href="/admin">Заявки</a>
      {setup_link}
    </nav>
    <div class="side-foot"><a href="/logout">Выйти</a></div>
  </aside>
  <main class="main">
    {body}
  </main>
</div>
</body></html>"""


def leads_list(leads, role="admin", message=""):
    total = len(leads)
    new_count = sum(1 for l in leads if (l.status or "new") == "new")
    approved_count = sum(1 for l in leads if l.status == "approved")

    if leads:
        rows = "".join(
            f"""<tr class="row">
  <td class="id">#{l.id}</td>
  <td><div class="name">{escape(l.name or '')}</div>
      <div class="sub">{escape(l.segment or '')}</div></td>
  <td><div>{escape(l.email or '')}</div><div class="sub">{escape(l.phone or '')}</div></td>
  <td>{_status_pill(l.status or 'new')}</td>
  <td class="sub">{_fmt_date(l.created_at)}</td>
  <td><a class="open" href="/admin/leads/{l.id}">Открыть</a></td>
</tr>"""
            for l in leads
        )
        table = f"""<div class="card"><div class="table-wrap"><table>
<thead><tr>
  <th>ID</th><th>Клиент</th><th>Контакты</th><th>Статус</th><th>Дата</th><th></th>
</tr></thead>
<tbody>{rows}</tbody>
</table></div></div>"""
    else:
        table = '<div class="card"><div class="empty">Заявок пока нет</div></div>'

    msg = f'<div class="done mb">{escape(message)}</div>' if message else ""
    body = f"""
<div class="top"><h1>Заявки</h1><span class="count">всего {total}</span></div>
<div class="content">
  {msg}
  <div class="stats">
    <div class="stat"><div class="k">Всего</div><div class="v">{total}</div></div>
    <div class="stat"><div class="k">Новые</div><div class="v">{new_count}</div></div>
    <div class="stat a"><div class="k">Одобрены</div><div class="v">{approved_count}</div></div>
  </div>
  {table}
</div>"""
    return _layout("Заявки", "leads", body, role)


def _auto_box(lead, sent, interval_days):
    if "check_started" not in sent:
        return ('<div class="auto-box">Авторассылка недельных писем станет доступна '
                'после письма «Проверка началась».</div>')
    if chain.next_scheduled(sent) is None:
        return '<div class="auto-box">Все недельные письма отправлены.</div>'
    if lead.auto_active:
        when = _fmt_date(lead.next_send_at)
        return f"""<div class="auto-box">Авторассылка включена. Следующее письмо уйдёт примерно {when} (интервал {interval_days} дн.).<br>
<form method="post" action="/admin/leads/{lead.id}/auto"><input type="hidden" name="action" value="stop">
<button class="btn btn-ghost btn-sm" type="submit">Выключить</button></form></div>"""
    return f"""<div class="auto-box">Недельные письма можно рассылать автоматически, раз в {interval_days} дн.<br>
<form method="post" action="/admin/leads/{lead.id}/auto"><input type="hidden" name="action" value="start">
<button class="btn btn-primary btn-sm" type="submit">Включить авторассылку</button></form></div>"""


def _tl_item(lead, event, status, last_log):
    title = escape(chain.SUBJECTS.get(event, event))
    lg = last_log.get(event)
    preview = (f'<a class="mini" href="/admin/leads/{lead.id}/preview/{event}" '
               f'target="_blank">Просмотр</a>')
    err_note = ""
    if status == "sent":
        when = _fmt_date(lg.created_at) if lg else ""
        pill = f'<span class="pill ok">Отправлено{(" " + when) if when else ""}</span>'
        actions = preview
        cls = "tl-item"
    elif status == "available":
        pill = '<span class="pill wait">Можно отправить</span>'
        if lg and lg.status == "error":
            err_note = f'<div class="err-note">Прошлая попытка не удалась: {escape(lg.error or "ошибка")}</div>'
        send = (f'<form class="inline" method="post" action="/admin/leads/{lead.id}/send" '
                f'onsubmit="return confirm(\'Отправить это письмо клиенту?\')">'
                f'<input type="hidden" name="event" value="{event}">'
                f'<button class="btn btn-primary btn-sm" type="submit">Отправить</button></form>')
        actions = preview + send
        cls = "tl-item"
    else:
        pill = '<span class="pill off">—</span>'
        actions = preview
        cls = "tl-item locked"
    return f"""<div class="{cls}">
  <div class="t">{title}{err_note}</div>
  <div class="tl-actions">{pill}{actions}</div>
</div>"""


def _replies_block(replies):
    if not replies:
        return '<p class="hint">Ответов от клиента пока нет.</p>'
    items = ""
    for r in replies:
        body = escape((r.body or "").strip())[:1500]
        items += f"""<div style="border-top:1px solid var(--line);padding:12px 0;">
<div style="font-size:12.5px;color:var(--muted);">{_fmt_date(r.received_at)} · {escape(r.from_email or '')}</div>
<div style="font-weight:600;margin:3px 0;">{escape(r.subject or '(без темы)')}</div>
<div style="white-space:pre-wrap;font-size:13.5px;color:var(--ink);line-height:1.5;">{body}</div>
</div>"""
    return items


def lead_detail(lead, sent, logs, replies, interval_days, role="admin", message=""):
    sent = set(sent)
    last_log = {}
    for lg in logs:
        last_log[lg.event] = lg

    groups_html = ""
    for title, rows in chain.timeline(sent):
        items = "".join(_tl_item(lead, ev, st, last_log) for ev, st in rows)
        extra = _auto_box(lead, sent, interval_days) if title == "Ход проверки" else ""
        groups_html += f'<div class="tl-group"><h3>{escape(title)}</h3>{extra}{items}</div>'

    fields = f"""
<div class="field"><span class="l">Имя</span><span class="r">{escape(lead.name or '')}</span></div>
<div class="field"><span class="l">Телефон</span><span class="r mono">{escape(lead.phone or '')}</span></div>
<div class="field"><span class="l">Email</span><span class="r mono">{escape(lead.email or '')}</span></div>
<div class="field"><span class="l">ИНН</span><span class="r mono">{escape(lead.inn or '')}</span></div>
<div class="field"><span class="l">Сегмент</span><span class="r">{escape(lead.segment or '')}</span></div>
<div class="field"><span class="l">ОКВЭД</span><span class="r">{_okved(lead)}</span></div>
<div class="field"><span class="l">Статус</span><span class="r">{_status_pill(lead.status or 'new')}</span></div>
<div class="field"><span class="l">Создана</span><span class="r mono">{_fmt_date(lead.created_at)}</span></div>
<div class="field"><span class="l">Одобрена</span><span class="r mono">{_fmt_date(lead.approved_at)}</span></div>"""

    msg = f'<div class="done mb">{escape(message)}</div>' if message else ""

    body = f"""
<div class="top"><h1>Заявка #{lead.id}</h1></div>
<div class="content">
  <div class="mb"><a class="back" href="/admin">← ко всем заявкам</a></div>
  {msg}
  <div class="detail">
    <div class="card pad">
      <h2>Цепочка писем</h2>
      <p class="hint">Письма отправляются по порядку. Итог проверки выбирает менеджер, после первого письма ветки вторая закрывается.</p>
      {groups_html}
    </div>
    <div>
      <div class="card pad mb">
        <h2>Данные клиента</h2>
        <p class="hint">Информация из анкеты с сайта.</p>
        {fields}
      </div>
      <div class="card pad mb">
        <h2>Недопустимое событие</h2>
        <p class="hint">Подставляется в письма вместо метки #NS#.</p>
        <form method="post" action="/admin/leads/{lead.id}/update">
          <textarea name="cyber_problem" rows="3" placeholder="Опишите недопустимое событие">{escape(lead.cyber_problem or '')}</textarea>
          <div style="height:12px"></div>
          <button class="btn btn-ghost" type="submit">Сохранить</button>
        </form>
      </div>
      <div class="card pad">
        <h2>Ответы клиента</h2>
        <p class="hint">Входящие письма с адреса клиента.</p>
        {_replies_block(replies)}
      </div>
    </div>
  </div>
</div>"""
    return _layout(f"Заявка #{lead.id}", "leads", body, role)
