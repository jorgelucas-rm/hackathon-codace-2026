from src.app.model.enum import HttpCode


def test_list_favorites_starts_empty(client, auth_user):
    _, headers = auth_user

    response = client.get("/api/users/me/favorites", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]["court_ids"] == []


def test_add_favorite_twice_does_not_duplicate(client, auth_user):
    _, headers = auth_user

    first = client.post("/api/users/me/favorites/7", headers=headers)
    assert first.status_code == HttpCode.OK, first.text
    assert first.json()["data"]["court_ids"] == [7]

    second = client.post("/api/users/me/favorites/7", headers=headers)
    assert second.status_code == HttpCode.OK, second.text
    assert second.json()["data"]["court_ids"] == [7]

    listing = client.get("/api/users/me/favorites", headers=headers)
    assert listing.json()["data"]["court_ids"] == [7]


def test_remove_favorite_never_added_is_idempotent(client, auth_user):
    _, headers = auth_user

    response = client.delete("/api/users/me/favorites/999", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]["court_ids"] == []

    listing = client.get("/api/users/me/favorites", headers=headers)
    assert listing.json()["data"]["court_ids"] == []


def test_favorites_reflect_state_after_add_and_remove(client, auth_user):
    _, headers = auth_user

    client.post("/api/users/me/favorites/1", headers=headers)
    client.post("/api/users/me/favorites/2", headers=headers)
    client.post("/api/users/me/favorites/3", headers=headers)

    listing = client.get("/api/users/me/favorites", headers=headers)
    assert sorted(listing.json()["data"]["court_ids"]) == [1, 2, 3]

    remove_response = client.delete("/api/users/me/favorites/2", headers=headers)
    assert remove_response.status_code == HttpCode.OK, remove_response.text
    assert sorted(remove_response.json()["data"]["court_ids"]) == [1, 3]

    listing_after = client.get("/api/users/me/favorites", headers=headers)
    assert sorted(listing_after.json()["data"]["court_ids"]) == [1, 3]


def test_favorites_are_scoped_per_user(client, auth_user, create_user):
    from tests.conftest import auth_headers_for_user

    _, headers = auth_user
    other_user = create_user()
    other_headers = auth_headers_for_user(other_user)

    client.post("/api/users/me/favorites/5", headers=headers)

    own_listing = client.get("/api/users/me/favorites", headers=headers)
    assert own_listing.json()["data"]["court_ids"] == [5]

    other_listing = client.get("/api/users/me/favorites", headers=other_headers)
    assert other_listing.json()["data"]["court_ids"] == []
