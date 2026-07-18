from src.app.model.enum import ErrorCode, HttpCode
from tests.conftest import auth_headers_for_company


def _create_court(client, headers, **overrides) -> dict:
    payload = {
        "name": "Quadra 1",
        "capacity": 10,
        "photos": [],
        "base_price_hour": 10000,
        "sport_ids": [],
    }
    payload.update(overrides)
    response = client.post("/api/companies/me/courts", json=payload, headers=headers)
    assert response.status_code == HttpCode.CREATED, response.text
    return response.json()["data"]


def test_owner_creates_and_lists_own_courts(client, auth_company):
    _, headers = auth_company
    _create_court(client, headers, name="Quadra A")
    _create_court(client, headers, name="Quadra B")

    response = client.get("/api/companies/me/courts", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    names = {c["name"] for c in response.json()["data"]}
    assert names == {"Quadra A", "Quadra B"}


def test_get_court_detail_is_public(client, auth_company):
    _, headers = auth_company
    court = _create_court(client, headers)

    response = client.get(f"/api/courts/{court['id']}")
    assert response.status_code == HttpCode.OK, response.text
    data = response.json()["data"]
    assert data["id"] == court["id"]
    assert "company" in data


def test_owner_can_patch_own_court(client, auth_company):
    _, headers = auth_company
    court = _create_court(client, headers)

    response = client.patch(
        f"/api/courts/{court['id']}",
        json={"name": "Quadra Renovada"},
        headers=headers,
    )
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]["name"] == "Quadra Renovada"


def test_patch_court_by_non_owner_is_forbidden(client, auth_company, create_company):
    _, headers = auth_company
    court = _create_court(client, headers)

    other_company = create_company()
    other_headers = auth_headers_for_company(other_company)

    response = client.patch(
        f"/api/courts/{court['id']}",
        json={"name": "Hacked"},
        headers=other_headers,
    )
    assert response.status_code == HttpCode.FORBIDDEN, response.text
    assert response.json()["error_code"] == ErrorCode.RESOURCE_NOT_OWNED.value
