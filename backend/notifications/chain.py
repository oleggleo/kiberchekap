"""
Цепочка писем: порядок, ветвление и расписание.

Порядок писем задан здесь, панель по нему решает, какое письмо можно отправить
следующим. Есть развилка по итогу проверки: событие достижимо или не реализовано.
Ветку выбирает менеджер, после первого письма ветки вторая закрывается.
"""

# Темы писем. Берутся в тему письма и показываются в панели.
SUBJECTS = {
    "lead_created": "Заявка на КиберЧекап получена",
    "lead_approved": "Ваша компания допущена к проверке",
    "check_started": "Проверка началась",
    "week_1": "КиберЧекап: итоги первой недели",
    "week_2": "КиберЧекап: итоги второй недели",
    "week_3": "КиберЧекап: итоги третьей недели",
    "week_4": "КиберЧекап: месяц проверки",
    "week_5": "КиберЧекап: пятая неделя проверки",
    "scenario_found": "КиберЧекап: обнаружен потенциальный сценарий",
    "finished_reachable": "Проверка завершена: недопустимое событие достижимо",
    "finished_not_reached": "Проверка завершена: недопустимое событие не реализовано",
    "report_ready": "Итоговый отчёт готов",
    "final_not_reached": "Проверка завершена: итог",
    "final_summary": "КиберЧекап: главный итог",
}

# Линейная часть цепочки по порядку.
SPINE = [
    "lead_created", "lead_approved", "check_started",
    "week_1", "week_2", "week_3", "week_4", "week_5",
]

# Недельные письма, которые может рассылать расписание после старта проверки.
SCHEDULED = ["week_1", "week_2", "week_3", "week_4", "week_5"]

# Развилка по итогу проверки. Выбор ветки за менеджером.
BRANCHES = {
    "reachable": ["scenario_found", "finished_reachable", "report_ready"],
    "not_reached": ["finished_not_reached", "final_not_reached"],
}

BRANCH_TITLES = {
    "reachable": "Событие достижимо",
    "not_reached": "Событие не реализовано",
}

# Общее завершающее письмо, шлётся после любой из веток.
CLOSING = "final_summary"

ALL_EVENTS = SPINE + BRANCHES["reachable"] + BRANCHES["not_reached"] + [CLOSING]


def detect_branch(sent):
    """Ветка, которую менеджер уже начал, или None."""
    for name, letters in BRANCHES.items():
        if any(e in sent for e in letters):
            return name
    return None


def next_scheduled(sent):
    """Следующее недельное письмо, которое ещё не отправлено, или None."""
    for event in SCHEDULED:
        if event not in sent:
            return event
    return None


def available_events(sent):
    """Множество писем, которые можно отправить сейчас, с учётом порядка и веток."""
    sent = set(sent)
    avail = set()

    # Линейная часть: первое несланное письмо, если предыдущее уже ушло.
    for i, event in enumerate(SPINE):
        if event in sent:
            continue
        if i == 0 or SPINE[i - 1] in sent:
            avail.add(event)
        break

    # Ветки открываются после старта проверки.
    if "check_started" in sent:
        branch = detect_branch(sent)
        for name, letters in BRANCHES.items():
            if branch and branch != name:
                continue
            for i, event in enumerate(letters):
                if event in sent:
                    continue
                if i == 0 or letters[i - 1] in sent:
                    avail.add(event)
                break

    # Завершающее письмо после конца выбранной ветки.
    branch = detect_branch(sent)
    if branch and BRANCHES[branch][-1] in sent and CLOSING not in sent:
        avail.add(CLOSING)

    return avail


def event_status(event, sent):
    if event in sent:
        return "sent"
    if event in available_events(sent):
        return "available"
    return "locked"


def timeline(sent):
    """Группы писем для панели: (заголовок группы, [(событие, статус), ...])."""
    sent = set(sent)

    def rows(events):
        return [(e, event_status(e, sent)) for e in events]

    return [
        ("Первичные письма", rows(["lead_created", "lead_approved"])),
        ("Ход проверки", rows(["check_started"] + SCHEDULED)),
        ("Итог: событие достижимо", rows(BRANCHES["reachable"])),
        ("Итог: событие не реализовано", rows(BRANCHES["not_reached"])),
        ("Завершение", rows([CLOSING])),
    ]
