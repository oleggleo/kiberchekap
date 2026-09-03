from models import Lead


def test_create_lead_saves_okved(client, session):
    response = client.post(
        "/leads",
        json={
            "name": "Иван",
            "phone": "+79990000000",
            "email": "ivan@example.com",
            "inn": "7707083893",
            "okved_code": "62.01",
            "okved_name": "Разработка компьютерного программного обеспечения",
        },
    )
    assert response.status_code == 200

    lead = session.query(Lead).filter(Lead.id == response.json()["lead_id"]).one()
    assert lead.okved_code == "62.01"
    assert lead.okved_name.startswith("Разработка")


def test_create_lead_without_okved(client, session):
    response = client.post(
        "/leads",
        json={"name": "Пётр", "phone": "+79990000001", "email": "petr@example.com"},
    )
    assert response.status_code == 200

    lead = session.query(Lead).filter(Lead.id == response.json()["lead_id"]).one()
    assert lead.okved_code is None


def test_create_lead_requires_email(client):
    response = client.post("/leads", json={"name": "Без почты", "phone": "+79990000002"})
    assert response.status_code == 422


def test_update_lead_changes_problem(client, session):
    created = client.post(
        "/leads",
        json={"name": "Анна", "phone": "+79990000003", "email": "anna@example.com"},
    ).json()

    response = client.patch(
        f"/leads/{created['lead_id']}",
        json={"cyber_problem": "утечка базы"},
    )
    assert response.status_code == 200

    session.expire_all()
    lead = session.query(Lead).filter(Lead.id == created["lead_id"]).one()
    assert lead.cyber_problem == "утечка базы"


def test_update_missing_lead_returns_404(client):
    response = client.patch("/leads/9999", json={"cyber_problem": "нет такого"})
    assert response.status_code == 404
