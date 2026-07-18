from fastapi import APIRouter, Depends

from src.app.model.dto import Response
from src.app.model.dto.sport import SportReadDTO
from src.app.model.enum import HttpCode
from src.app.service.sport_service import SportService

router = APIRouter(prefix="/sports", tags=["Sports"])


@router.get(
    "",
    response_model=Response[list[SportReadDTO]],
    status_code=HttpCode.OK,
)
async def list_sports(
    service: SportService = Depends(SportService.get_service),
):
    return Response(
        code=HttpCode.OK,
        message="Sports retrieved successfully",
        data=service.list_all(),
    )
