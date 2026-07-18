from fastapi import APIRouter, Body, Depends, Path, Query

from src.app.controller.dependencies import require_roles
from src.app.model.dto import Response
from src.app.model.dto.pagination import Pagination
from src.app.model.dto.review import ReviewCreateDTO, ReviewReadDTO
from src.app.model.enum import HttpCode, Level
from src.app.service.review_service import ReviewService
from src.infra.context import RequestContext

# `POST /api/bookings/{id}/reviews` fica aninhada em `/bookings` (não em
# `/reviews`), seguindo o padrão de `booking_controller.me_router`/
# `court_controller.me_router` (rota de ação sobre um recurso já existente).
bookings_router = APIRouter(prefix="/bookings", tags=["Reviews"])
# `GET /api/companies/{id}/reviews` — pública, paginada.
companies_router = APIRouter(prefix="/companies", tags=["Reviews"])
# `POST /api/reviews/{id}/helpful` — decisão local (T-F): pública, sem
# exigir autenticação nem checar duplicata (o doc não deixa explícito
# controle de voto único no MVP; ver relatório de entrega).
router = APIRouter(prefix="/reviews", tags=["Reviews"])


@bookings_router.post(
    "/{booking_id}/reviews",
    response_model=Response[ReviewReadDTO],
    status_code=HttpCode.CREATED,
)
async def create_review(
    _=Depends(require_roles(Level.USER)),
    service: ReviewService = Depends(ReviewService.get_service),
    booking_id: int = Path(..., ge=1),
    dto: ReviewCreateDTO = Body(...),
):
    review = service.create(
        user_id=RequestContext.get_auth_user().user_id,
        booking_id=booking_id,
        dto=dto,
    )
    return Response(
        code=HttpCode.CREATED,
        message="Review created successfully",
        data=service.to_read_dto(review),
    )


@companies_router.get(
    "/{company_id}/reviews",
    response_model=Response[Pagination[ReviewReadDTO]],
    status_code=HttpCode.OK,
)
async def list_company_reviews(
    service: ReviewService = Depends(ReviewService.get_service),
    company_id: int = Path(..., ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    return Response(
        code=HttpCode.OK,
        message="Reviews retrieved successfully",
        data=service.list_by_company(
            company_id=company_id, page=page, page_size=page_size
        ),
    )


@router.post(
    "/{review_id}/helpful",
    response_model=Response[ReviewReadDTO],
    status_code=HttpCode.OK,
)
async def mark_review_helpful(
    service: ReviewService = Depends(ReviewService.get_service),
    review_id: int = Path(..., ge=1),
):
    review = service.mark_helpful(review_id=review_id)
    return Response(
        code=HttpCode.OK,
        message="Review marked as helpful",
        data=service.to_read_dto(review),
    )
