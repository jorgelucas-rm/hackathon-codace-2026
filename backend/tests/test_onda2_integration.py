"""Teste de integração da Onda 2, escrito pelo orquestrador após o merge de
T-B1 (Booking + Disponibilidade) e T-B2 (Pagamento): cobre a cadeia completa
via as rotas reais (`/api/bookings` -> `/api/payments/{id}/confirm`), algo
que nenhum dos dois executores podia testar sozinho (cada um só tinha o
outro lado como contrato/stub).

Critério de pronto da onda (docs/STATUS.md): criar booking fechado ->
confirmar pagamento aprovado -> booking `confirmed`; pagamento recusado ->
booking `canceled` e horário liberado; idempotência do confirm.
"""

from datetime import date, timedelta

from src.app.model.enum import HttpCode
from tests.booking_test_setup import create_test_court, full_week_opening_hours

FUTURE_DATE = (date.today() + timedelta(days=2)).isoformat()


def _setup_court(create_company, db_session):
    company = create_company(opening_hours=full_week_opening_hours())
    court = create_test_court(db_session, company, base_price_hour=10000)
    return company, court


def _create_booking(client, headers, court_id, start_time="18:00", end_time="19:00"):
    payload = {
        "court_id": court_id,
        "date": FUTURE_DATE,
        "start_time": start_time,
        "end_time": end_time,
    }
    return client.post("/api/bookings", json=payload, headers=headers)


def _find_slot(slots, start_time_str):
    for slot in slots:
        if slot["start_time"] == start_time_str:
            return slot
    raise AssertionError(f"slot {start_time_str} not found in {slots}")


def test_approved_payment_confirms_booking_and_grants_split(
    client, auth_user, create_company, db_session
):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id)
    assert created.status_code == HttpCode.CREATED, created.text
    body = created.json()["data"]
    payment_id = body["payment"]["id"]
    booking_id = body["booking"]["id"]

    confirm = client.post(
        f"/api/payments/{payment_id}/confirm",
        json={"result": "approved", "method": "PIX"},
        headers=headers,
    )
    assert confirm.status_code == HttpCode.OK, confirm.text
    payment = confirm.json()["data"]
    assert payment["status"] == "APPROVED"
    assert payment["method"] == "PIX"
    assert payment["platform_fee"] + payment["gateway_fee"] + payment["company_payout"] == payment["amount"]

    booking = client.get(f"/api/bookings/{booking_id}", headers=headers)
    assert booking.status_code == HttpCode.OK, booking.text
    assert booking.json()["data"]["status"] == "CONFIRMED"


def test_denied_payment_cancels_booking_and_frees_slot(
    client, auth_user, create_company, db_session
):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id, start_time="10:00", end_time="11:00")
    assert created.status_code == HttpCode.CREATED, created.text
    body = created.json()["data"]
    payment_id = body["payment"]["id"]
    booking_id = body["booking"]["id"]

    confirm = client.post(
        f"/api/payments/{payment_id}/confirm",
        json={"result": "denied", "method": "PIX"},
        headers=headers,
    )
    assert confirm.status_code == HttpCode.OK, confirm.text
    assert confirm.json()["data"]["status"] == "DENIED"

    booking = client.get(f"/api/bookings/{booking_id}", headers=headers)
    assert booking.status_code == HttpCode.OK, booking.text
    assert booking.json()["data"]["status"] == "CANCELED"
    assert booking.json()["data"]["reason"] == "payment_denied"

    availability = client.get(
        f"/api/courts/{court.id}/availability", params={"date": FUTURE_DATE}
    )
    slot = _find_slot(availability.json()["data"]["slots"], "10:00:00")
    assert slot["status"] == "free"

    # Horário livre de novo: outro booking no mesmo slot deve ser aceito.
    second = _create_booking(client, headers, court.id, start_time="10:00", end_time="11:00")
    assert second.status_code == HttpCode.CREATED, second.text


def test_confirm_is_idempotent_on_already_resolved_payment(
    client, auth_user, create_company, db_session
):
    _, headers = auth_user
    _, court = _setup_court(create_company, db_session)

    created = _create_booking(client, headers, court.id, start_time="14:00", end_time="15:00")
    payment_id = created.json()["data"]["payment"]["id"]

    first = client.post(
        f"/api/payments/{payment_id}/confirm",
        json={"result": "approved", "method": "PIX"},
        headers=headers,
    )
    assert first.status_code == HttpCode.OK, first.text

    # Repetir com um resultado diferente não reprocessa nem levanta erro —
    # apenas retorna o estado já resolvido (idempotência, §2.8 do doc de API).
    second = client.post(
        f"/api/payments/{payment_id}/confirm",
        json={"result": "denied", "method": "CARD"},
        headers=headers,
    )
    assert second.status_code == HttpCode.OK, second.text
    assert second.json()["data"]["status"] == "APPROVED"
    assert second.json()["data"]["method"] == "PIX"
