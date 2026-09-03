import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import session_scope
import okved_search

FORMAL = [
    ("разработка программного обеспечения", {"62.01", "62.02"}),
    ("производство хлеба и кондитерских изделий", {"10.71"}),
    ("услуги парикмахерских и салонов красоты", {"96.02"}),
    ("аренда недвижимого имущества", {"68.20"}),
    ("бухгалтерский учёт и аудит", {"69.20"}),
    ("деятельность рекламных агентств", {"73.11"}),
    ("техническое обслуживание и ремонт автомобилей", {"45.20"}),
    ("производство рабочей одежды", {"14.12"}),
    ("профессиональное обучение", {"85.30"}),
    ("деятельность фитнес-центров", {"93.13"}),
]

COLLOQUIAL = [
    ("пишу программы на заказ", {"62.01", "62.02"}),
    ("делаю мобильные приложения", {"62.01", "62.02"}),
    ("пеку хлеб и торты", {"10.71"}),
    ("стригу людей", {"96.02"}),
    ("вожу пассажиров по городу", {"49.31", "49.32", "49.39"}),
    ("сдаю офисы в аренду", {"68.20"}),
    ("веду бухгалтерию для ИП", {"69.20"}),
    ("чиню машины в сервисе", {"45.20"}),
    ("продаю продукты в магазине", {"47.11", "47.19", "47.29"}),
    ("держу кафе", {"56.10", "56.29"}),
    ("шью рабочую одежду", {"14.12"}),
    ("убираю офисы", {"81.21"}),
    ("торгую через интернет-магазин", {"47.91"}),
]


def run(session, cases, title):
    top1 = 0
    top5 = 0
    print(title)
    for query, accepted in cases:
        results = okved_search.search(session, query, limit=5)
        codes = [row["code"] for row in results]
        hit1 = bool(codes) and codes[0] in accepted
        hit5 = bool(accepted & set(codes))
        top1 += hit1
        top5 += hit5
        mark = "1" if hit1 else ("5" if hit5 else "-")
        print(f"  [{mark}] {query:38} {', '.join(codes)}")
    print(f"  top-1 {top1}/{len(cases)}   top-5 {top5}/{len(cases)}")
    print()
    return top1, top5


def main():
    with session_scope() as session:
        formal = run(session, FORMAL, "Формулировки как в справочнике")
        colloquial = run(session, COLLOQUIAL, "Разговорные формулировки")

    total = len(FORMAL) + len(COLLOQUIAL)
    top1 = formal[0] + colloquial[0]
    top5 = formal[1] + colloquial[1]
    print(f"Всего {total} запросов")
    print(f"top-1: {top1}/{total} = {round(100 * top1 / total)}%")
    print(f"top-5: {top5}/{total} = {round(100 * top5 / total)}%")


if __name__ == "__main__":
    main()
