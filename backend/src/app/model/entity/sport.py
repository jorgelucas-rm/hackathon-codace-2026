from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.model.entity.base_model import BaseModel


class Sport(BaseModel):
    __tablename__ = "sport"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
