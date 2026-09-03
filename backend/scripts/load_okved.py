import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from db import session_scope
from models import Okved
from okved_search import encode_passages

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "okved_data.json"


def load_items():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    items = load_items()
    print(f"Справочник: {len(items)} кодов")

    names = [item["name"] for item in items]
    vectors = encode_passages(names)

    rows = [
        {"code": item["code"], "name": item["name"], "embedding": vector}
        for item, vector in zip(items, vectors)
    ]

    with session_scope() as session:
        statement = insert(Okved).values(rows)
        statement = statement.on_conflict_do_update(
            index_elements=["code"],
            set_={"name": statement.excluded.name, "embedding": statement.excluded.embedding},
        )
        session.execute(statement)
        session.commit()
        total = session.query(Okved).count()

    print(f"В базе кодов: {total}")


if __name__ == "__main__":
    main()
