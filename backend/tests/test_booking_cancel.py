"""`POST /api/bookings/{id}/cancel` — política de reembolso
(backend-api-e-fluxos.md §3.5).

`PaymentService.refund` ainda é `raise NotImplementedError` (T-B2 em
andamento) — os testes usam `monkeypatch` para simular o contrato descrito
no esqueleto (`add()` sem commit, status -> REFUNDED, `refunded_at` setado),
conforme instruído para T-B1 não esperar o merge de T-B2.
"""

from datetime import date, datetime, timedelta, timezone

from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode, HttpCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.payment_status import PaymentStatus
from src.app.service.payment_service import PaymentService
from tests.booking_test_setup import (
    create_test_court,
    ensure_booking_routes_registered,
    full_week_opening_hours,
)

ensure_booking_routes_registered()

FUTURE_DATE = (date.today() + timedelta(days=5)).isoformat()


def _fake_refund(self, payment_id):
    """Stub do contrato descrito em `payment_service.py`: `add()` sem
    commit, `status=REFUNDED`, `refunded_at=now`."""
    payment = self.payment_repository.get_by_pk(pk=payment_id)
    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = datetime.now(timezone.utc)
    return self.payment_repository.add(entity=payment)


def _setup_confirmed_booking(client, auth_user, create_company, db_session, game_start_offset_hours):
    """Cria um booking via API (PENDING) e promove manualmente para
    CONFIRMED + Payment APPROVED, com o horário do jogo a
    `game_start_offset_hours` de distância — simula o que
    `booking_payment_effects.on_booking_approved` faria depois de um
    `PaymentService.confirm` aprovado (ainda não implementado por T-B2)."""
    _, headers = auth_user
    company = create_company(opening_hours=full_week_opening_hours())
    court = create_test_court(db_session, company, base_price_hour=10000)

    payload = {
        "court_id": court.id,
        "date": FUTURE_DATE,
        "start_time": "10:00",
        "end_time": "11:00",
    }
    created = client.post("/api/bookings", json=payload, headers=headers)
    assert created.status_code == HttpCode.CREATED, created.text
    booking_id = created.json()["data"]["booking"]["id"]

    game_start = datetime.now(timezone.utc) + timedelta(hours=game_start_offset_hours)

    from src.app.model.entity.booking import Booking

    booking = db_session.get(Booking, booking_id)
    booking.status = BookingStatus.CONFIRMED
    booking.date = game_start.date()
    booking.start_time = game_start.time()
    booking.end_time = (game_start + timedelta(hours=1)).time()

    payment = (
        db_session.query(Payment)
        .filter(Payment.reference_type == "booking", Payment.reference_id == booking_id)
        .first()
    )
    payment.status = PaymentStatus.APPROVED

    db_session.commit()
    return headers, booking_id


def test_cancel_before_deadline_refunds_in_full(client, auth_user, create_company, db_session, monkeypatch):
    monkeypatch.setattr(PaymentService, "refund", _fake_refund)

    headers, booking_id = _setup_confirmed_booking(
        client, auth_user, create_company, db_session, game_start_offset_hours=48
    )

    response = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    data = response.json()["data"]
    assert data["refunded"] is True
    assert data["booking"]["status"] == "CANCELED"
    assert data["booking"]["reason"] == "canceled_by_client"

    payment = (
        db_session.query(Payment)
        .filter(Payment.reference_type == "booking", Payment.reference_id == booking_id)
        .first()
    )
    assert payment.status == PaymentStatus.REFUNDED
    assert payment.refunded_at is not None


def test_cancel_after_deadline_does_not_refund(client, auth_user, create_company, db_session, monkeypatch):
    called = {"refund": False}

    def _spy_refund(self, payment_id):
        called["refund"] = True
        return _fake_refund(self, payment_id)

    monkeypatch.setattr(PaymentService, "refund", _spy_refund)

    # Jogo em 2h — dentro das 24h de REFUND_DEADLINE_HOURS, não elegível.
    headers, booking_id = _setup_confirmed_booking(
        client, auth_user, create_company, db_session, game_start_offset_hours=2
    )

    response = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    assert response.status_code == HttpCode.OK, response.text
    data = response.json()["data"]
    assert data["refunded"] is False
    assert data["booking"]["status"] == "CANCELED"
    assert called["refund"] is False

    payment = (
        db_session.query(Payment)
        .filter(Payment.reference_type == "booking", Payment.reference_id == booking_id)
        .first()
    )
    assert payment.status == PaymentStatus.APPROVED  # não foi mexido


def test_cancel_twice_is_invalid_state(client, auth_user, create_company, db_session, monkeypatch):
    monkeypatch.setattr(PaymentService, "refund", _fake_refund)

    headers, booking_id = _setup_confirmed_booking(
        client, auth_user, create_company, db_session, game_start_offset_hours=48
    )

    first = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    assert first.status_code == HttpCode.OK, first.text

    second = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    assert second.status_code == HttpCode.CONFLICT, second.text
    assert second.json()["error_code"] == ErrorCode.INVALID_STATE.value


def test_cancel_by_non_owner_is_forbidden(client, auth_user, create_company, create_user, db_session, monkeypatch):
    from tests.conftest import auth_headers_for_user

    monkeypatch.setattr(PaymentService, "refund", _fake_refund)

    _, booking_id = _setup_confirmed_booking(
        client, auth_user, create_company, db_session, game_start_offset_hours=48
    )

    other_user = create_user()
    other_headers = auth_headers_for_user(other_user)

    response = client.post(f"/api/bookings/{booking_id}/cancel", headers=other_headers)
    assert response.status_code == HttpCode.FORBIDDEN, response.text
    assert response.json()["error_code"] == ErrorCode.RESOURCE_NOT_OWNED.value
