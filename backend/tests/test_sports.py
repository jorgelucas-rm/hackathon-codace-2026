from src.app.model.entity.sport import Sport
from src.app.model.enum import HttpCode
from src.app.service.sport_service import DEFAULT_SPORTS, seed_sports


def test_seed_sports_is_idempotent(db_session):
    seed_sports(db_session)
    seed_sports(db_session)

    count = db_session.query(Sport).count()
    assert count == len(DEFAULT_SPORTS)
    assert count >= 5


def test_list_sports_is_public_and_reflects_seed(client, db_session):
    seed_sports(db_session)

    response = client.get("/api/sports")
    assert response.status_code == HttpCode.OK, response.text

    names = {s["name"] for s in response.json()["data"]}
    assert "Beach Tênis" in names
    assert "Futebol Society" in names
    assert "Vôlei" in names
    assert "Padel" in names
    assert "Basquete" in names
