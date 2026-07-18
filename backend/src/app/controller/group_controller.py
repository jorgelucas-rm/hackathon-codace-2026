from datetime import date as date_
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.group import (
    GroupJoinResponseDTO,
    GroupLeaveResponseDTO,
    GroupReadDTO,
)
from src.app.model.enum import HttpCode, Level
from src.app.service.group_service import GroupService
from src.infra.context import RequestContext

# Rotas públicas de grupo (`/groups`) + ações do jogador (`join`/`leave`),
# que exigem usuário autenticado.
router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get(
    "",
    response_model=Response[list[GroupReadDTO]],
    status_code=HttpCode.OK,
)
async def list_public_groups(
    service: GroupService = Depends(GroupService.get_service),
    sport_id: Optional[int] = Query(default=None, ge=1),
    court_id: Optional[int] = Query(default=None, ge=1),
    date: Optional[date_] = Query(default=None),
):
    """"Jogos precisando de gente perto de você" (backend-api-e-fluxos.md
    §2.7): só grupos `status=open` + `visibility=public` com
    `closing_deadline` futuro. Filtros opcionais `sport_id`/`court_id`/
    `date` — geolocalização (`lat/lng/raio_km`) fica fora de escopo desta
    task (mesmo padrão de busca por proximidade de `company`, T-A1)."""
    groups = service.search_public(sport_id=sport_id, court_id=court_id, date=date)
    return Response(
        code=HttpCode.OK,
        message="Groups retrieved successfully",
        data=groups,
    )


@router.get(
    "/{group_id}",
    response_model=Response[GroupReadDTO],
    status_code=HttpCode.OK,
)
async def get_group(
    service: GroupService = Depends(GroupService.get_service),
    group_id: int = Path(..., ge=1),
):
    """Funciona também para `visibility=link` — acesso direto por id, sem
    passar pela busca pública (que filtra por visibilidade)."""
    return Response(
        code=HttpCode.OK,
        message="Group retrieved successfully",
        data=service.get_detail(group_id=group_id),
    )


@router.post(
    "/{group_id}/join",
    response_model=Response[GroupJoinResponseDTO],
    status_code=HttpCode.CREATED,
)
async def join_group(
    _=Depends(require_roles(Level.USER)),
    service: GroupService = Depends(GroupService.get_service),
    group_id: int = Path(..., ge=1),
):
    result = service.join(
        group_id=group_id, user_id=RequestContext.get_auth_user().user_id
    )
    return Response(
        code=HttpCode.CREATED,
        message="Joined group successfully",
        data=result,
    )


@router.post(
    "/{group_id}/leave",
    response_model=Response[GroupLeaveResponseDTO],
    status_code=HttpCode.OK,
)
async def leave_group(
    _=Depends(require_roles(Level.USER)),
    service: GroupService = Depends(GroupService.get_service),
    group_id: int = Path(..., ge=1),
):
    result = service.leave(
        group_id=group_id, user_id=RequestContext.get_auth_user().user_id
    )
    return Response(
        code=HttpCode.OK,
        message="Left group successfully",
        data=result,
    )
