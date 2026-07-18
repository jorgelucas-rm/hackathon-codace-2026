from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from src.app.model.entity.base_model import BaseModel
from src.app.model.enum.int_enum_type import IntEnumType
from src.app.model.enum.level import Level


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
        server_default=text("'avatar/default.png'"),
        nullable=False,
    )
