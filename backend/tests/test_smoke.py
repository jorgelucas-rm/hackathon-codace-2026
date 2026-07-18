from src.app.model.enum import HttpCode


def test_root(client):
    response = client.get("/api")
    assert response.status_code == HttpCode.OK


def test_register_and_login_user(client):
    response = client.post(
        "/api/users",
        json={"name": "Jorge", "email": "jorge@test.com", "password": "Str0ng!Pass1"},
    )
    assert response.status_code == HttpCode.CREATED, response.text

    response = client.post(
        "/api/auth/user-login",
        json={"email": "jorge@test.com", "password": "Str0ng!Pass1"},
    )
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]


def test_auth_user_fixture_hits_protected_route(client, auth_user):
    _, headers = auth_user
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]["auth_type"] == "USER"
