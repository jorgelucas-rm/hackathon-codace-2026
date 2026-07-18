from typing import Optional, Type

from src.app.model.entity.payment import Payment
from src.app.repository.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):

    @property
    def model(self) -> Type[Payment]:
        return Payment

    def get_by_reference(
        self, reference_type: str, reference_id: int
    ) -> Optional[Payment]:
        return (
            self.session.query(Payment)
            .filter(
                Payment.reference_type == reference_type,
                Payment.reference_id == reference_id,
            )
            .order_by(Payment.id.desc())
            .first()
        )

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Payment.id,
            "amount": Payment.amount,
            "status": Payment.status,
            "created_at": Payment.created_at,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "reference_type": Payment.reference_type,
            "reference_id": Payment.reference_id,
            "status": Payment.status,
        }
