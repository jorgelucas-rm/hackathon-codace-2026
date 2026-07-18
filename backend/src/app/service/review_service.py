from typing import Optional

from fastapi import Depends

from src.app.model.dto.pagination import Pagination
from src.app.model.dto.review import ReviewCreateDTO, ReviewReadDTO
from src.app.model.entity.review import Review
from src.app.model.enum import ErrorCode
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.repository.booking_repository import BookingRepository
from src.app.repository.group_member_repository import GroupMemberRepository
from src.app.repository.group_repository import GroupRepository
from src.app.repository.review_repository import ReviewRepository
from src.infra.exception import ConflictException, NotFoundException


class ReviewService:
    """`ReviewService` (Fase F) — cria/lista avaliações e calcula a média
    (`nota_media`) usada por `CompanyService`.

    Elegibilidade (backend-api-e-fluxos.md §3.7): o booking precisa estar
    `COMPLETED` e o usuário precisa ter jogado — `creator_user_id` do
    booking, ou (para `type=GROUP`) `GroupMember` com `status=CONFIRMED`
    daquele grupo. `GroupRepository`/`GroupMemberRepository` são só lidos
    aqui (donos: T-C, Onda 3) — nunca editados por este arquivo.
    """

    def __init__(
        self,
        review_repository: ReviewRepository,
        booking_repository: BookingRepository,
        group_repository: GroupRepository,
        group_member_repository: GroupMemberRepository,
    ):
        self.review_repository = review_repository
        self.booking_repository = booking_repository
        self.group_repository = group_repository
        self.group_member_repository = group_member_repository

    def create(self, user_id: int, booking_id: int, dto: ReviewCreateDTO) -> Review:
        booking = self.booking_repository.get_by_pk(pk=booking_id)
        if not booking:
            raise NotFoundException(resource="Booking", error_code=ErrorCode.NOT_FOUND)

        if not self._is_eligible(booking, user_id):
            raise ConflictException(
                message="Booking is not eligible for review",
                error_code=ErrorCode.BOOKING_NOT_ELIGIBLE_FOR_REVIEW,
            )

        existing = self.review_repository.get_by_booking_and_user(
            booking_id=booking_id, user_id=user_id
        )
        if existing:
            raise ConflictException(
                message="Booking already reviewed by this user",
                error_code=ErrorCode.ALREADY_REVIEWED,
            )

        review = Review(
            company_id=booking.court.company_id,
            booking_id=booking_id,
            user_id=user_id,
            rating=dto.rating,
            comment=dto.comment,
        )
        return self.review_repository.save(entity=review)

    def _is_eligible(self, booking, user_id: int) -> bool:
        if booking.status != BookingStatus.COMPLETED:
            return False

        if booking.creator_user_id == user_id:
            return True

        if booking.type == BookingType.GROUP:
            group = self.group_repository.get_by_booking(booking.id)
            if not group:
                return False
            member = self.group_member_repository.get_active_member(
                group_id=group.id, user_id=user_id
            )
            # `get_active_member` também retorna `PENDING` — só `CONFIRMED`
            # conta como "jogou de fato" para fins de avaliação.
            return bool(member and member.status == GroupMemberStatus.CONFIRMED)

        return False

    def mark_helpful(self, review_id: int) -> Review:
        """MVP: sem controle de voto único (documentado no relatório de
        entrega) — qualquer chamada incrementa o contador."""
        review = self.review_repository.get_by_pk(pk=review_id)
        if not review:
            raise NotFoundException(resource="Review", error_code=ErrorCode.NOT_FOUND)

        review.helpful_count += 1
        return self.review_repository.save(entity=review)

    def list_by_company(
        self, company_id: int, page: int = 1, page_size: int = 10
    ) -> Pagination[ReviewReadDTO]:
        items, total, total_filtered = self.review_repository.get_paginated(
            page=page,
            page_size=page_size,
            order_by="created_at",
            order_direction="desc",
            filters={"company_id": company_id},
        )
        return Pagination[ReviewReadDTO](
            items=[self.to_read_dto(r) for r in items],
            total=total,
            total_filtered=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    def get_average(self, company_id: int) -> Optional[float]:
        """Usado por `CompanyService._to_search_card`/`get_detail` para
        preencher `nota_media`. Retorna `None` se a company não tem
        avaliações (em vez de 0.0, para o front distinguir "sem nota" de
        "nota zero")."""
        average, count = self.review_repository.get_average_and_count(company_id)
        if count == 0:
            return None
        return round(average, 2) if average is not None else None

    @staticmethod
    def to_read_dto(review: Review) -> ReviewReadDTO:
        return ReviewReadDTO(
            id=review.id,
            company_id=review.company_id,
            booking_id=review.booking_id,
            user_id=review.user_id,
            user_name=review.user.name if review.user else None,
            rating=review.rating,
            comment=review.comment,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
        )

    @staticmethod
    def get_service(
        review_repository: ReviewRepository = Depends(ReviewRepository.get_instance()),
        booking_repository: BookingRepository = Depends(
            BookingRepository.get_instance()
        ),
        group_repository: GroupRepository = Depends(GroupRepository.get_instance()),
        group_member_repository: GroupMemberRepository = Depends(
            GroupMemberRepository.get_instance()
        ),
    ) -> "ReviewService":
        return ReviewService(
            review_repository=review_repository,
            booking_repository=booking_repository,
            group_repository=group_repository,
            group_member_repository=group_member_repository,
        )
