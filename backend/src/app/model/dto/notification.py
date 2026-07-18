from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    body: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    read: bool
    created_at: datetime


class NotificationMarkReadDTO(BaseModel):
    """`POST /api/notifications/read` — `{"ids": [...]}` marca só os ids
    informados (que pertençam ao usuário logado); `{"all": true}` marca
    todas as notificações do usuário. `all=True` tem precedência sobre
    `ids` se ambos vierem preenchidos."""

    ids: Optional[list[int]] = Field(default=None)
    all: bool = Field(default=False)
