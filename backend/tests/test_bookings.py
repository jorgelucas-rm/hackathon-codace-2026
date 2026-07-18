"""`POST /api/bookings`, `GET /api/courts/{id}/availability`,
`GET /api/bookings/{id}`, `GET /api/users/me/bookings` (T-B1).

Cobre: exclusividade de horário (corrida pelo mesmo slot -> SLOT_UNAVAILABLE),
sobreposição parcial, fora do horário de funcionamento, TTL de pendente
(disponibilidade volta a `free` após expirar), autorização de leitura.
"""

from datetime import date, datetime, timedelta, timezone

from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode, HttpCode
from tests.booking_test_setup import (
    create_test_court,
    ensure_booking_routes_registered,
    full_week_opening_hours,
)

ensure_booking_routes_registered()

FUTURE_DATE = (date.today() + timedelta(days=2)).isoformat()


def _setup_court(create_company, db_session):
    company = create_company(opening_hours=full_week_opening_hours())
    court = create_test_court(db_session, company, base_price_hour=10000)
    return company, court


def _create_booking(client, headers, court_id, start_time="18:00", end_time="19:00", **overrides):
    payload = {
        "court_id": court_id,
        "date": FUTURE_DATE,
        "start_time": start_time,
        "end_time": end_time,
    }
    payload.update(overrides)
    return client.post("/api/bookings", json=payload, headers=headers)


def test_create_booking_success_computes_price_on_server(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    response = _create_booking(client, headers, court.id, start_time="18:00", end_time="20:00")
    assert response.status_code == HttpCode.CREATED, response.text
    data = response.json()["data"]

    assert data["booking"]["status"] == "PENDING"
    assert data["booking"]["type"] == "CLOSED"
    assert data["booking"]["total_price"] == 20000  # 2h * 10000
    assert data["payment"]["amount"] == 20000
    assert data["payment"]["reference_type"] == "booking"
    assert data["payment"]["reference_id"] == data["booking"]["id"]
    assert data["payment"]["status"] == "PENDING"


def test_second_booking_on_same_slot_gets_slot_unavailable(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    first = _create_booking(client, headers, court.id)
    assert first.status_code == HttpCode.CREATED, first.text

    second = _create_booking(client, headers, court.id)
    assert second.status_code == HttpCode.CONFLICT, second.text
    assert second.json()["error_code"] == ErrorCode.SLOT_UNAVAILABLE.value


def test_overlapping_booking_gets_slot_unavailable(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    first = _create_booking(client, headers, court.id, start_time="18:00", end_time="19:00")
    assert first.status_code == HttpCode.CREATED, first.text

    overlapping = _create_booking(client, headers, court.id, start_time="18:30", end_time="19:30")
    assert overlapping.status_code == HttpCode.CONFLICT, overlapping.text
    assert overlapping.json()["error_code"] == ErrorCode.SLOT_UNAVAILABLE.value


def test_adjacent_booking_does_not_conflict(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    first = _create_booking(client, headers, court.id, start_time="18:00", end_time="19:00")
    assert first.status_code == HttpCode.CREATED, first.text

    adjacent = _create_booking(client, headers, court.id, start_time="19:00", end_time="20:00")
    assert adjacent.status_code == HttpCode.CREATED, adjacent.text


def test_booking_outside_opening_hours_is_rejected(client, auth_user, create_company, db_session):
    _, headers = auth_user
    company = create_company(
        opening_hours=full_week_opening_hours(opening="08:00", closing="10:00")
    )
    court = create_test_court(db_session, company, base_price_hour=10000)

    response = _create_booking(client, headers, court.id, start_time="18:00", end_time="19:00")
    assert response.status_code == HttpCode.UNPROCESSABLE_ENTITY, response.text
    assert response.json()["error_code"] == ErrorCode.OUTSIDE_OPENING_HOURS.value


def test_booking_with_start_after_end_is_invalid_time_range(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    response = _create_booking(client, headers, court.id, start_time="19:00", end_time="18:00")
    assert response.status_code == HttpCode.UNPROCESSABLE_ENTITY, response.text
    assert response.json()["error_code"] == ErrorCode.INVALID_TIME_RANGE.value


def test_booking_in_the_past_is_invalid_time_range(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    payload = {
        "court_id": court.id,
        "date": (date.today() - timedelta(days=1)).isoformat(),
        "start_time": "18:00",
        "end_time": "19:00",
    }
    response = client.post("/api/bookings", json=payload, headers=headers)
    assert response.status_code == HttpCode.UNPROCESSABLE_ENTITY, response.text
    assert response.json()["error_code"] == ErrorCode.INVALID_TIME_RANGE.value


def test_group_type_is_not_supported_yet(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    response = _create_booking(client, headers, court.id, type="group")
    assert response.status_code == HttpCode.CONFLICT, response.text
    assert response.json()["error_code"] == ErrorCode.INVALID_STATE.value


def test_expired_pending_booking_frees_the_slot_in_availability(
    client, auth_user, create_company, db_session
):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id, start_time="18:00", end_time="19:00")
    assert created.status_code == HttpCode.CREATED, created.text
    booking_id = created.json()["data"]["booking"]["id"]

    availability = client.get(f"/api/courts/{court.id}/availability", params={"date": FUTURE_DATE})
    assert availability.status_code == HttpCode.OK, availability.text
    slot = _find_slot(availability.json()["data"]["slots"], "18:00:00")
    assert slot["status"] == "busy"

    # Expira o pagamento manualmente (mesma sessão do db_session, que o
    # `client` também usa via override de `get_session`).
    payment = (
        db_session.query(Payment)
        .filter(Payment.reference_type == "booking", Payment.reference_id == booking_id)
        .first()
    )
    payment.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    availability_after_ttl = client.get(
        f"/api/courts/{court.id}/availability", params={"date": FUTURE_DATE}
    )
    assert availability_after_ttl.status_code == HttpCode.OK, availability_after_ttl.text
    slot_after = _find_slot(availability_after_ttl.json()["data"]["slots"], "18:00:00")
    assert slot_after["status"] == "free"

    # E o horário volta a estar disponível para um novo booking.
    second = _create_booking(client, headers, court.id, start_time="18:00", end_time="19:00")
    assert second.status_code == HttpCode.CREATED, second.text


def test_get_booking_by_creator(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id)
    booking_id = created.json()["data"]["booking"]["id"]

    response = client.get(f"/api/bookings/{booking_id}", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    assert response.json()["data"]["id"] == booking_id


def test_get_booking_by_owning_company(client, auth_user, create_company, db_session):
    from tests.conftest import auth_headers_for_company

    _, headers = auth_user
    company, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id)
    booking_id = created.json()["data"]["booking"]["id"]

    company_headers = auth_headers_for_company(company)
    response = client.get(f"/api/bookings/{booking_id}", headers=company_headers)
    assert response.status_code == HttpCode.OK, response.text


def test_get_booking_forbidden_for_unrelated_user(client, auth_user, create_company, create_user, db_session):
    from tests.conftest import auth_headers_for_user

    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id)
    booking_id = created.json()["data"]["booking"]["id"]

    other_user = create_user()
    other_headers = auth_headers_for_user(other_user)

    response = client.get(f"/api/bookings/{booking_id}", headers=other_headers)
    assert response.status_code == HttpCode.FORBIDDEN, response.text
    assert response.json()["error_code"] == ErrorCode.RESOURCE_NOT_OWNED.value


def test_list_my_bookings_upcoming_scope(client, auth_user, create_company, db_session):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    _create_booking(client, headers, court.id)

    response = client.get("/api/users/me/bookings", params={"scope": "upcoming"}, headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    assert len(response.json()["data"]) == 1

    history_response = client.get(
        "/api/users/me/bookings", params={"scope": "history"}, headers=headers
    )
    assert history_response.status_code == HttpCode.OK, history_response.text
    assert history_response.json()["data"] == []


def _find_slot(slots, start_time_str):
    for slot in slots:
        if slot["start_time"] == start_time_str:
            return slot
    raise AssertionError(f"slot {start_time_str} not found in {slots}")
