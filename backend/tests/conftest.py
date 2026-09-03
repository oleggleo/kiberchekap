import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from db import Base, get_db
from models import Okved, EMBEDDING_DIM
import main
import okved_search

ADMIN_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://kiberchekap:kiberchekap@localhost:5432/kiberchekap",
)
TEST_DB = "kiberchekap_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB


def unit_vector(position):
    vector = [0.0] * EMBEDDING_DIM
    vector[position] = 1.0
    return vector


SAMPLE = [
    ("62.01", "Разработка компьютерного программного обеспечения", unit_vector(0)),
    ("10.71", "Производство хлеба и мучных кондитерских изделий", unit_vector(1)),
    ("96.02", "Предоставление услуг парикмахерскими и салонами красоты", unit_vector(2)),
]


@pytest.fixture(scope="session")
def engine():
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        connection.execute(text(f"CREATE DATABASE {TEST_DB}"))
    admin.dispose()

    engine = create_engine(TEST_URL)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
    admin.dispose()


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"TRUNCATE {table.name} RESTART IDENTITY CASCADE"))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def okved_rows(session):
    for code, name, vector in SAMPLE:
        session.add(Okved(code=code, name=name, embedding=vector))
    session.commit()
    return SAMPLE


@pytest.fixture
def many_okved_rows(session):
    for number in range(15):
        session.add(
            Okved(
                code=f"99.{number:02d}",
                name=f"Производство изделий номер {number}",
                embedding=unit_vector(number),
            )
        )
    session.commit()


@pytest.fixture
def fake_query_vector(monkeypatch):
    holder = {"vector": unit_vector(0)}

    def encode_query(text):
        return holder["vector"]

    monkeypatch.setattr(okved_search, "encode_query", encode_query)
    return holder


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setattr(main, "_send_lead_created_email", lambda lead_id: None)
    main.app.dependency_overrides[get_db] = lambda: session
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
