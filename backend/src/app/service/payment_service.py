from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.model.dto.payment import PaymentSummaryDTO
from src.app.model.entity.payment import Payment
from src.app.model.enum import ErrorCode
from src.app.model.enum.payment_method import PaymentMethod
from src.app.model.enum.payment_status import PaymentStatus
from src.app.repository.payment_repository import PaymentRepository
from src.environments import GATEWAY_FEE_PCT, PAYMENT_TTL_MINUTES, PLATFORM_FEE_PCT
from src.infra.exception import NotFoundException

# Contrato Onda 2 (B1<->B2) — esqueleto commitado pelo orquestrador.
#
# Registro de efeitos por `reference_type`: quem possui o domínio referenciado
# registra aqui, na importação do seu próprio módulo, como despachar a
# aprovação/recusa de um pagamento para o recurso dono. `booking` é
# registrado por T-B1 (`service/booking_payment_effects.py`); `group_member`
# será registrado por T-C na Onda 3 (`service/group_payment_effects.py`).
# O import desses módulos (para o registro rodar) é feito por quem os cria —
# REGISTRAR aponta onde o orquestrador precisa plugar o import, se o próprio
# executor não o fizer num arquivo que já é carregado no boot da app.
#
# Assinatura do handler: recebe `reference_id` e a `Session` corrente (a
# mesma sessão do repositório de payment nesta chamada) para poder buscar/
# atualizar a entidade dona *na mesma transação* — `PaymentService.confirm`
# faz um único commit no final, cobrindo o update do Payment e o efeito.
EffectHandler = Callable[[int, Session], None]

_on_approved_handlers: dict[str, EffectHandler] = {}
_on_denied_handlers: dict[str, EffectHandler] = {}


def register_effect_handler(
    reference_type: str,
    on_approved: EffectHandler,
    on_denied: EffectHandler,
) -> None:
    _on_approved_handlers[reference_type] = on_approved
    _on_denied_handlers[reference_type] = on_denied


class PaymentService:

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def to_summary_dto(self, payment: Payment) -> PaymentSummaryDTO:
        return PaymentSummaryDTO.model_validate(payment)

    def get_by_id(self, payment_id: int) -> Payment:
        payment = self.payment_repository.get_by_pk(pk=payment_id)
        if not payment:
            raise NotFoundException(resource="Payment", error_code=ErrorCode.NOT_FOUND)
        return payment

    def create_pending(
        self, reference_type: str, reference_id: int, amount: int
    ) -> Payment:
        """Cria `Payment(status=PENDING)` via `add()` — **sem commit**. O
        caller (booking_service/group_service) chama isto no meio de uma
        transação multi-entidade e finaliza com um único `commit()` no fim
        do próprio método de service (mesmo padrão do caminho de transação
        da Onda 0)."""
        payment = Payment(
            reference_type=reference_type,
            reference_id=reference_id,
            amount=amount,
            status=PaymentStatus.PENDING,
        )
        return self.payment_repository.add(entity=payment)

    def is_expired(self, payment: Payment) -> bool:
        """TTL de pendente (`PAYMENT_TTL_MINUTES`). Só faz sentido para
        `status == PENDING`; usado na expiração preguiçosa da disponibilidade
        (T-B1) e das vagas de grupo (T-C)."""
        if payment.status != PaymentStatus.PENDING:
            return False
        deadline = payment.created_at + timedelta(minutes=PAYMENT_TTL_MINUTES)
        return datetime.now(timezone.utc) >= deadline

    def confirm(
        self,
        payment_id: int,
        result: str,
        method: Optional[PaymentMethod] = None,
    ) -> Payment:
        """`POST /api/payments/{id}/confirm` — simulador de gateway.

        `result` é `"approved"` ou `"denied"`. **Idempotente**: se o
        pagamento já não está `PENDING`, retorna o estado atual sem
        reprocessar (sem levantar erro — condição do doc de API, seção 2.8).
        Na aprovação, grava o split (`company_payout`/`platform_fee`/
        `gateway_fee` com `PLATFORM_FEE_PCT`/`GATEWAY_FEE_PCT`) e despacha
        `on_approved(reference_id, session)` do handler registrado para
        `reference_type`; na recusa, despacha `on_denied`. TODO(T-B2):
        implementar corpo completo (split, dispatch, commit único no fim
        cobrindo Payment + efeito)."""
        raise NotImplementedError("T-B2 implementa o corpo desta função")

    def refund(self, payment_id: int) -> Payment:
        """Estorna um pagamento `APPROVED` (`status=REFUNDED`,
        `refunded_at=now`). Via `add()` — **sem commit**: o caller (cancel de
        booking/group) finaliza a transação. TODO(T-B2): implementar corpo
        completo (validar estado, `PAYMENT_ALREADY_RESOLVED` se não
        aplicável)."""
        raise NotImplementedError("T-B2 implementa o corpo desta função")

    @staticmethod
    def get_service(
        payment_repository: PaymentRepository = Depends(
            PaymentRepository.get_instance()
        ),
    ) -> "PaymentService":
        return PaymentService(payment_repository=payment_repository)
