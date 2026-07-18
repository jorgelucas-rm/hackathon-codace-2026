"""`service/booking_payment_effects.py` — handlers registrados para
`reference_type="booking"` (contrato Onda 2). Testados chamando as funções
diretamente com a `Session` de teste, do mesmo jeito que
`PaymentService.confirm` faria (T-B2 ainda não implementou o corpo de
`confirm`/`refund`, então não dá pra testar a cadeia via
`POST /api/payments/{id}/confirm` ainda)."""

from datetime import date, timedelta

from src.app.model.entity.booking import Booking
from src.app.model.enum.booking_status import BookingStatus
from src.app.service.booking_payment_effects import (
    on_booking_approved,
    on_booking_denied,
)
from src.app.service.booking_service import BookingService
from src.app.model.dto.booking import BookingCreateDTO
from tests.booking_test_setup import create_test_court, full_week_opening_hours

FUTURE_DATE = date.today() + timedelta(days=2)


def _create_pending_booking(db_session, create_company, user) -> Booking:
    from src.app.repository.booking_repository import BookingRepository
    from src.app.repository.payment_repository import PaymentRepository
    from src.app.service.payment_service import PaymentService

    company = create_company(opening_hours=full_week_opening_hours())
    court = create_test_court(db_session, company, base_price_hour=10000)

    booking_repository = BookingRepository(session=db_session)
    payment_repository = PaymentRepository(session=db_session)
    payment_service = PaymentService(payment_repository=payment_repository)
    service = BookingService(
        booking_repository=booking_repository,
        payment_repository=payment_repository,
        payment_service=payment_service,
    )
    dto = BookingCreateDTO(
        court_id=court.id, date=FUTURE_DATE, start_time="18:00", end_time="19:00"
    )
    booking, _ = service.create_closed_booking(user_id=user.id, dto=dto)
    return booking


def test_on_booking_approved_confirms_pending_booking(db_session, create_company, create_user):
    user = create_user()
    booking = _create_pending_booking(db_session, create_company, user)

    on_booking_approved(booking.id, db_session)
    db_session.commit()

    refreshed = db_session.get(Booking, booking.id)
    assert refreshed.status == BookingStatus.CONFIRMED


def test_on_booking_denied_cancels_pending_booking_with_reason(db_session, create_company, create_user):
    user = create_user()
    booking = _create_pending_booking(db_session, create_company, user)

    on_booking_denied(booking.id, db_session)
    db_session.commit()

    refreshed = db_session.get(Booking, booking.id)
    assert refreshed.status == BookingStatus.CANCELED
    assert refreshed.reason == "payment_denied"


def test_effects_are_idempotent_noop_on_already_resolved_booking(db_session, create_company, create_user):
    user = create_user()
    booking = _create_pending_booking(db_session, create_company, user)

    on_booking_approved(booking.id, db_session)
    db_session.commit()

    # Segunda chamada (ex.: reprocessamento) não deve regredir o estado.
    on_booking_denied(booking.id, db_session)
    db_session.commit()

    refreshed = db_session.get(Booking, booking.id)
    assert refreshed.status == BookingStatus.CONFIRMED
