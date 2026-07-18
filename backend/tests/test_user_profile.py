from src.app.model.enum import HttpCode, Level


def test_update_my_profile_updates_allowed_fields(client, auth_user):
    _, headers = auth_user

    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={
            "name": "Novo Nome",
            "phone": "11999998888",
            "latitude": -23.5,
            "longitude": -46.6,
            "sports_of_interest": [1, 2],
            "skill_level": "INTERMEDIATE",
        },
    )
    assert response.status_code == HttpCode.OK, response.text
    data = response.json()["data"]
    assert data["name"] == "Novo Nome"
    assert data["phone"] == "11999998888"
    assert data["latitude"] == -23.5
    assert data["longitude"] == -46.6
    assert data["sports_of_interest"] == [1, 2]
    assert data["skill_level"] == "INTERMEDIATE"


def test_update_my_profile_ignores_role_and_situation(client, auth_user):
    """`UserProfileUpdateDTO` não declara `role`/`situation` — mesmo que o
    payload tente enviá-los, o schema simplesmente os ignora (campos
    desconhecidos para o DTO) e nada muda no usuário."""
    user, headers = auth_user
    assert user.role == Level.USER
    assert user.situation is True

    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"name": "Ainda Eu", "role": "ADMIN", "situation": False},
    )
    assert response.status_code == HttpCode.OK, response.text
    data = response.json()["data"]
    assert data["name"] == "Ainda Eu"
    # role/situation continuam como eram — o payload extra é ignorado pelo DTO.
    assert data["role"] == "USER"
    assert data["situation"] is True

    # Confere direto na rota admin para garantir que persistiu como USER/ativo.
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.json()["data"]["entity"]["role"] == "USER"
    assert me_response.json()["data"]["entity"]["situation"] is True


def test_update_my_profile_requires_auth(client):
    response = client.patch("/api/users/me", json={"name": "Sem Token"})
    # Sem Authorization header, HTTPBearer barra antes mesmo de decodificar o
    # token (403 "Not authenticated"); com token inválido, o handler global
    # devolve 401. Qualquer um dos dois confirma que a rota é protegida.
    assert response.status_code in (HttpCode.UNAUTHORIZED, HttpCode.FORBIDDEN)
