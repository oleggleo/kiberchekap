import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import session_scope
from models import Lead


def main():
    with session_scope() as session:
        lead = Lead(
            name="Иван Иванов",
            phone="+79123456789",
            email="ivan@company.ru",
            inn="7700000000",
            segment="Интернет-магазины",
        )
        session.add(lead)
        session.commit()
        print(f"Лид создан, id={lead.id}")


if __name__ == "__main__":
    main()
