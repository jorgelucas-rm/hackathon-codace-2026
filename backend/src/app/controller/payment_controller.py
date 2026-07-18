from fastapi import APIRouter, Body, Depends, Path

from src.app.controller.dependencies import require_roles
from src.app.model.dto.payment import PaymentConfirmDTO, PaymentReadDTO
from src.app.model.dto.response import Response
from src.app.model.enum import HttpCode, Level
from src.app.service.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get(
    "/{payment_id}",
    response_model=Response[PaymentReadDTO],
    status_code=HttpCode.OK,
)
async def get_payment(
    _=Depends(require_roles(Level.USER)),
    service: PaymentService = Depends(PaymentService.get_service),
    payment_id: int = Path(..., ge=1),
):
    payment = service.get_by_id(payment_id=payment_id)
    return Response(
        code=HttpCode.OK,
        message="Payment retrieved successfully",
        data=service.to_read_dto(payment),
    )


@router.post(
    "/{payment_id}/confirm",
    response_model=Response[PaymentReadDTO],
    status_code=HttpCode.OK,
)
async def confirm_payment(
    _=Depends(require_roles(Level.USER)),
    service: PaymentService = Depends(PaymentService.get_service),
    payment_id: int = Path(..., ge=1),
    dto: PaymentConfirmDTO = Body(...),
):
    """Simulador de gateway (`backend-api-e-fluxos.md` §2.8). Qualquer
    usuário autenticado pode confirmar qualquer pagamento pendente — não há
    checagem de posse aqui de propósito (evita acoplar este módulo ao dono
    real da referência, ex.: booking); é só o simulador do lado do cliente
    disparando o webhook."""
    payment = service.confirm(payment_id=payment_id, result=dto.result, method=dto.method)
    return Response(
        code=HttpCode.OK,
        message="Payment confirmed successfully",
        data=service.to_read_dto(payment),
    )
