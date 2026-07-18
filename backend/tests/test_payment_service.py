"""Testes de `PaymentService` (T-B2, Onda 2).

Não dependem de nenhum controller estar registrado em `main.py` (ainda não
está — isso é REGISTRAR do orquestrador) nem de T-B1/T-C existirem: os
efeitos são exercitados com um handler fake registrado via
`register_effect_handler` neste próprio arquivo, sobre um `reference_type`
exclusivo dos testes deste módulo.
"""

from datetime import datetime, timezone

import pytest

from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode
from src.app.model.enum.payment_method import PaymentMethod
from src.app.model.enum.payment_status import PaymentStatus
from src.app.repository.payment_repository import PaymentRepository
from src.app.service.payment_service import PaymentService, register_effect_handler
from src.environments import GATEWAY_FEE_PCT, PLATFORM_FEE_PCT
from src.infra.exception import ConflictException

FAKE_REFERENCE_TYPE = "fake_ref_type"


@pytest.fixture()
def effect_calls():
    """Registra handlers fake para `FAKE_REFERENCE_TYPE` e devolve o log de
    chamadas (`[(kind, reference_id, session), ...]`) feito por eles."""
    calls: list[tuple[str, int, object]] = []

    def on_approved(reference_id: int, session) -> None:
        calls.append(("approved", reference_id, session))

    def on_denied(reference_id: int, session) -> None:
        calls.append(("denied", reference_id, session))

    register_effect_handler(FAKE_REFERENCE_TYPE, on_approved, on_denied)
    return calls


@pytest.fixture()
def payment_service(db_session):
    return PaymentService(payment_repository=PaymentRepository(session=db_session))


def _create_pending_payment(db_session, amount: int = 10_000) -> Payment:
    payment = Payment(
        reference_type=FAKE_REFERENCE_TYPE,
        reference_id=1,
        amount=amount,
        status=PaymentStatus.PENDING,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


def test_confirm_approved_records_split_and_dispatches_handler(
    db_session, payment_service, effect_calls
):
    payment = _create_pending_payment(db_session, amount=10_000)

    result = payment_service.confirm(
        payment_id=payment.id, result="approved", method=PaymentMethod.PIX
    )

    assert result.status == PaymentStatus.APPROVED
    assert result.method == PaymentMethod.PIX
    assert result.platform_fee == 10_000 * PLATFORM_FEE_PCT // 100
    assert result.gateway_fee == 10_000 * GATEWAY_FEE_PCT // 100
    assert result.company_payout == (
        10_000 - result.platform_fee - result.gateway_fee
    )

    # Persistido (commit único cobre Payment + efeito).
    db_session.refresh(payment)
    assert payment.status == PaymentStatus.APPROVED
    assert payment.company_payout == result.company_payout

    assert effect_calls == [("approved", payment.reference_id, db_session)]


def test_confirm_denied_dispatches_denied_handler_and_leaves_split_empty(
    db_session, payment_service, effect_calls
):
    payment = _create_pending_payment(db_session)

    result = payment_service.confirm(payment_id=payment.id, result="denied")

    assert result.status == PaymentStatus.DENIED
    assert result.platform_fee is None
    assert result.gateway_fee is None
    assert result.company_payout is None

    assert effect_calls == [("denied", payment.reference_id, db_session)]


def test_confirm_is_idempotent_on_already_resolved_payment(
    db_session, payment_service, effect_calls
):
    payment = _create_pending_payment(db_session)

    first = payment_service.confirm(
        payment_id=payment.id, result="approved", method=PaymentMethod.CARD
    )
    assert len(effect_calls) == 1

    # Segunda chamada sobre pagamento já resolvido: não reprocessa, não
    # levanta erro, não dispara o handler de novo.
    second = payment_service.confirm(payment_id=payment.id, result="denied")

    assert second.status == PaymentStatus.APPROVED
    assert second.id == first.id
    assert second.company_payout == first.company_payout
    assert len(effect_calls) == 1  # handler não chamado de novo


def test_refund_only_works_on_approved_payment(db_session, payment_service, effect_calls):
    payment = _create_pending_payment(db_session)
    payment_service.confirm(
        payment_id=payment.id, result="approved", method=PaymentMethod.PIX
    )

    refunded = payment_service.refund(payment_id=payment.id)

    assert refunded.status == PaymentStatus.REFUNDED
    assert refunded.refunded_at is not None
    assert refunded.refunded_at.tzinfo is not None


def test_refund_raises_payment_already_resolved_when_not_approved(
    db_session, payment_service
):
    payment = _create_pending_payment(db_session)

    with pytest.raises(ConflictException) as exc_info:
        payment_service.refund(payment_id=payment.id)

    assert exc_info.value.error_code == ErrorCode.PAYMENT_ALREADY_RESOLVED


def test_refund_raises_payment_already_resolved_when_already_refunded(
    db_session, payment_service
):
    payment = _create_pending_payment(db_session)
    payment_service.confirm(
        payment_id=payment.id, result="approved", method=PaymentMethod.PIX
    )
    payment_service.refund(payment_id=payment.id)

    with pytest.raises(ConflictException) as exc_info:
        payment_service.refund(payment_id=payment.id)

    assert exc_info.value.error_code == ErrorCode.PAYMENT_ALREADY_RESOLVED
