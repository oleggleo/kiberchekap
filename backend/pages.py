from html import escape


def _layout(title, body):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; background: #f4f6f8;
         color: #1a1a1a; margin: 0; padding: 40px 16px; }}
  .box {{ max-width: 620px; margin: 0 auto; background: #fff; border: 1px solid #e2e6ea;
         border-radius: 10px; padding: 28px 32px; }}
  .box + .box {{ margin-top: 18px; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; }}
  h2 {{ font-size: 17px; margin: 0 0 4px; }}
  p.sub {{ color: #5a636c; margin: 0 0 22px; font-size: 14px; }}
  label {{ display: block; font-size: 13px; font-weight: bold; margin: 16px 0 6px; }}
  input {{ width: 100%; box-sizing: border-box; padding: 9px 11px; font-size: 14px;
          border: 1px solid #cfd6dd; border-radius: 6px; }}
  .hint {{ font-size: 12px; color: #8a929b; margin-top: 4px; }}
  .group {{ border-top: 1px solid #eef1f4; margin-top: 24px; padding-top: 8px; }}
  .group-title {{ font-size: 13px; font-weight: bold; color: #1f6feb; text-transform: uppercase;
                 letter-spacing: 0.5px; }}
  button {{ margin-top: 26px; width: 100%; padding: 12px; font-size: 15px; font-weight: bold;
           color: #fff; background: #1f6feb; border: none; border-radius: 7px; cursor: pointer; }}
  button.small {{ margin: 0; width: auto; padding: 7px 14px; font-size: 13px; }}
  button.danger {{ background: #d64545; }}
  .msg {{ background: #e6f5ec; border: 1px solid #b7e0c4; color: #1a7f4b; border-radius: 7px;
         padding: 12px 14px; font-size: 14px; margin-bottom: 20px; }}
  .err {{ background: #fdecec; border: 1px solid #f2c2c2; color: #b23a3a; border-radius: 7px;
         padding: 12px 14px; font-size: 14px; margin-bottom: 20px; }}
  ol {{ font-size: 14px; line-height: 1.7; padding-left: 20px; }}
  code {{ background: #f0f3f7; border: 1px solid #e2e6ea; border-radius: 4px; padding: 1px 5px;
         font-family: monospace; font-size: 13px; }}
  a {{ color: #1f6feb; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
  td, th {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid #eef1f4; }}
  .row {{ display: flex; gap: 10px; align-items: flex-end; }}
  .row > div {{ flex: 1; }}
  .row label {{ margin-top: 0; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _field(label, name, value="", hint="", type_="text", placeholder=""):
    return f"""<label for="{name}">{escape(label)}</label>
<input id="{name}" name="{name}" type="{type_}" value="{escape(value)}" placeholder="{escape(placeholder)}">
{f'<div class="hint">{escape(hint)}</div>' if hint else ''}"""


def login_page(error=""):
    err = f'<div class="err">{escape(error)}</div>' if error else ""
    body = f"""<div class="box">
<h1>Вход</h1>
<p class="sub">Введите логин и пароль.</p>
{err}
<form method="post" action="/login">
{_field("Логин", "login")}
{_field("Пароль", "password", type_="password")}
<button type="submit">Войти</button>
</form>
</div>"""
    return _layout("Вход", body)


def _managers_block(managers):
    if managers:
        rows = "".join(
            f"""<tr>
<td>{escape(m.login)}</td>
<td style="text-align:right">
<form method="post" action="/setup/users/delete" style="margin:0">
<input type="hidden" name="user_id" value="{m.id}">
<button class="small danger" type="submit">Удалить</button>
</form>
</td></tr>"""
            for m in managers
        )
        table = f"<table><tr><th>Логин менеджера</th><th></th></tr>{rows}</table>"
    else:
        table = '<p class="hint">Менеджеров пока нет.</p>'

    return f"""<div class="box">
<h2>Менеджеры</h2>
<p class="sub">Менеджер видит только «Заявки», без доступа к настройке. Логин и пароль передайте ему вместе с ярлыком «Заявки».</p>
{table}
<form method="post" action="/setup/users" class="row">
<div>{_field("Логин", "login")}</div>
<div>{_field("Пароль", "password", type_="password")}</div>
<div style="flex:0"><button class="small" type="submit">Добавить</button></div>
</form>
</div>"""


def setup_page(values, managers, first_run=False, message=""):
    msg = f'<div class="msg">{escape(message)}</div>' if message else ""
    intro = (
        "Первый запуск. Заполните поля, приложение сохранит их в файл .env."
        if first_run
        else "Измените нужные поля и сохраните."
    )
    pw_hint = "" if first_run else "Пусто — оставить прежний."

    steps = """<div class="box">
<h1>Настройка</h1>
<p class="sub">Здесь задаётся всё, что нужно, чтобы подключить приложение к вашему серверу.</p>
<ol>
<li>Заведите поддомен для бэкенда, например <code>api.вашдомен.ру</code>, и направьте его A-записью на IP сервера.</li>
<li>Настройте https через nginx и certbot (пример конфига в <code>frontend/BACKEND_API.md</code>).</li>
<li>Заполните поля ниже и нажмите «Сохранить».</li>
<li>В лендинге на Тильде в блоке <code>0_config</code> впишите адрес бэкенда в строку <code>apiUrl</code>.</li>
</ol>
</div>"""

    form = f"""<div class="box">
{msg}
<form method="post" action="/setup">

<div class="group"><div class="group-title">Сайт</div></div>
{_field("Адрес лендинга", "CORS_ORIGINS", values.get("CORS_ORIGINS", ""), "Откуда сайт шлёт заявки. Пример: https://вашсайт.ру")}
{_field("Адрес сайта в письмах", "SITE_URL", values.get("SITE_URL", ""), "Ставится ссылкой внутри писем. Пример: https://вашсайт.ру")}

<div class="group"><div class="group-title">Почта для отправки (SMTP)</div></div>
{_field("Хост", "SMTP_HOST", values.get("SMTP_HOST", "smtp.gmail.com"))}
{_field("Порт", "SMTP_PORT", values.get("SMTP_PORT", "587"))}
{_field("Логин", "SMTP_USER", values.get("SMTP_USER", ""), "Обычно адрес почты, с которой уходят письма.")}
{_field("Пароль", "SMTP_PASSWORD", "", pw_hint, "password")}
{_field("Имя отправителя", "SENDER_NAME", values.get("SENDER_NAME", "Киберчекап"))}
{_field("Адрес отправителя", "SENDER_EMAIL", values.get("SENDER_EMAIL", ""), "Если пусто, берётся SMTP логин.")}

<div class="group"><div class="group-title">Приём ответов (IMAP)</div></div>
{_field("Хост", "IMAP_HOST", values.get("IMAP_HOST", ""), "Ящик, куда приходят ответы клиентов. Пример: imap.gmail.com")}
{_field("Порт", "IMAP_PORT", values.get("IMAP_PORT", "993"))}
{_field("Логин", "IMAP_USER", values.get("IMAP_USER", ""))}
{_field("Пароль", "IMAP_PASSWORD", "", pw_hint, "password")}

<div class="group"><div class="group-title">Расписание</div></div>
{_field("Интервал недельных писем, дней", "SCHEDULE_INTERVAL_DAYS", values.get("SCHEDULE_INTERVAL_DAYS", "7"), "Через сколько дней уходит следующее письмо о ходе проверки при включённой авторассылке.")}

<div class="group"><div class="group-title">Администратор</div></div>
{_field("Логин", "ADMIN_LOGIN", values.get("ADMIN_LOGIN", ""))}
{_field("Пароль", "ADMIN_PASSWORD", "", pw_hint, "password")}

<button type="submit">Сохранить</button>
</form>
</div>"""

    return _layout("Настройка", steps + form + _managers_block(managers))


def saved_page():
    body = """<div class="box">
<h1>Сохранено</h1>
<div class="msg">Значения записаны в .env.</div>
<ol>
<li>Перезапустите бэкенд, чтобы настройки применились.</li>
<li>В лендинге на Тильде в блоке <code>0_config</code> укажите адрес бэкенда в строке <code>apiUrl</code>.</li>
<li>Проверьте, что поддомен работает по https.</li>
</ol>
<p><a href="/setup">Вернуться к настройке</a> · <a href="/admin">Заявки</a></p>
</div>"""
    return _layout("Готово", body)
