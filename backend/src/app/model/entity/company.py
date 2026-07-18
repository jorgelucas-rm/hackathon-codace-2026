from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from src.app.model.entity.base_model import BaseModel


class Company(BaseModel):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cnpj: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    street: Mapped[str] = mapped_column(String(250), nullable=False)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(150), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    situation: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    # Onda 1 (T-A1, catálogo) — campos de perfil da arena. Todos nullable ou
    # com server_default para não quebrar o fixture `create_company` do
    # conftest, que não passa esses campos.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    photos: Mapped[list] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
    amenities: Mapped[list] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
    opening_hours: Mapped[list] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
