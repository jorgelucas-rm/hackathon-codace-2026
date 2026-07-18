from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateDTO(BaseModel):
    """`POST /api/bookings/{id}/reviews` — corpo da avaliação."""

    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReviewReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    booking_id: int
    user_id: int
    user_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    helpful_count: int
    created_at: datetime
