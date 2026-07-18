from fastapi import APIRouter, Body, Depends, Query

from src.app.controller.dependencies import require_roles
from src.app.model.dto.notification import NotificationMarkReadDTO, NotificationReadDTO
from src.app.model.dto.response import Response
from src.app.model.enum import HttpCode, Level
from src.app.service.notification_service import NotificationService
from src.infra.context import RequestContext

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=Response[list[NotificationReadDTO]],
    status_code=HttpCode.OK,
)
async def list_notifications(
    _=Depends(require_roles(Level.USER)),
    service: NotificationService = Depends(NotificationService.get_service),
    apenas_nao_lidas: bool = Query(default=False),
):
    """`GET /api/notifications?apenas_nao_lidas=` — só as próprias
    notificações do usuário logado, mais recentes primeiro."""
    notifications = service.list_by_user(
        user_id=RequestContext.get_auth_user().user_id,
        unread_only=apenas_nao_lidas,
    )
    return Response(
        code=HttpCode.OK,
        message="Notifications retrieved successfully",
        data=[service.to_read_dto(n) for n in notifications],
    )


@router.post(
    "/read",
    response_model=Response[None],
    status_code=HttpCode.OK,
)
async def mark_notifications_read(
    _=Depends(require_roles(Level.USER)),
    service: NotificationService = Depends(NotificationService.get_service),
    dto: NotificationMarkReadDTO = Body(...),
):
    """`POST /api/notifications/read` — `{"ids": [...]}` ou `{"all": true}`."""
    service.mark_read(
        user_id=RequestContext.get_auth_user().user_id,
        ids=dto.ids,
        all=dto.all,
    )
    return Response(
        code=HttpCode.OK,
        message="Notifications marked as read",
        data=None,
    )
