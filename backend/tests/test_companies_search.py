from src.app.model.entity.sport import Sport
from src.app.model.enum import HttpCode
from src.app.service.sport_service import seed_sports
from tests.conftest import auth_headers_for_company


def test_search_by_radius_filters_and_orders_by_distance(client, create_company):
    create_company(name="Na Origem", latitude=0.0, longitude=0.0)
    create_company(name="Perto", latitude=0.05, longitude=0.0)  # ~5.5km
    create_company(name="Longe", latitude=1.0, longitude=0.0)  # ~111km

    response = client.get(
        "/api/companies",
        params={"lat": 0.0, "lng": 0.0, "raio_km": 20},
    )
    assert response.status_code == HttpCode.OK, response.text

    data = response.json()["data"]
    names = [item["name"] for item in data["items"]]

    assert "Longe" not in names
    assert names == ["Na Origem", "Perto"]
    assert data["items"][0]["distance_km"] <= data["items"][1]["distance_km"]


def test_search_only_returns_active_companies(client, create_company):
    create_company(name="Ativa", latitude=0.0, longitude=0.0, situation=True)
    create_company(name="Inativa", latitude=0.0, longitude=0.0, situation=False)

    response = client.get("/api/companies")
    assert response.status_code == HttpCode.OK, response.text

    names = {item["name"] for item in response.json()["data"]["items"]}
    assert "Ativa" in names
    assert "Inativa" not in names


def _create_court(client, headers, sport_ids: list[int], name: str) -> dict:
    payload = {
        "name": name,
        "capacity": 10,
        "photos": [],
        "base_price_hour": 5000,
        "sport_ids": sport_ids,
    }
    response = client.post("/api/companies/me/courts", json=payload, headers=headers)
    assert response.status_code == HttpCode.CREATED, response.text
    return response.json()["data"]


def test_search_by_sport_id_filters_via_join(client, db_session, auth_company, create_company):
    seed_sports(db_session)
    volei = db_session.query(Sport).filter(Sport.name == "Vôlei").one()
    padel = db_session.query(Sport).filter(Sport.name == "Padel").one()

    company_volei, headers_volei = auth_company
    company_padel = create_company(name="Arena Padel")
    headers_padel = auth_headers_for_company(company_padel)

    _create_court(client, headers_volei, [volei.id], "Quadra de Vôlei")
    _create_court(client, headers_padel, [padel.id], "Quadra de Padel")

    response = client.get("/api/companies", params={"sport_id": volei.id})
    assert response.status_code == HttpCode.OK, response.text

    names = {item["name"] for item in response.json()["data"]["items"]}
    assert company_volei.name in names
    assert "Arena Padel" not in names
