from typing import Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from src.app.model.entity.base_model import BaseModel
from src.app.model.enum.int_enum_type import IntEnumType
from src.app.model.enum.level import Level
from src.app.model.enum.skill_level import SkillLevel


class User(BaseModel):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    role: Mapped[Level] = mapped_column(
        IntEnumType(Level),
        server_default=text(str(Level.USER.value)),
        nullable=False,
    )
    situation: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    avatar: Mapped[str] = mapped_column(
        String(500),
        server_default=text("'avatar/avatar_00.svg'"),
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sports_of_interest: Mapped[list[int]] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
    """Lista de ids de `Sport` — sem FK (T-A2 não depende de T-A1)."""
    favorite_courts: Mapped[list[int]] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
    """Lista de ids de `Court` — sem FK; leitura ignora ids órfãos (ver
    modelo-de-dominio.md, nota "Favoritos (quadras)")."""
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(
        IntEnumType(SkillLevel), nullable=True
    )
