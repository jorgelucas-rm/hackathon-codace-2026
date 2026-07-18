from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.app.model.entity.base_model import BaseModel
from src.app.model.entity.company import Company
from src.app.model.entity.sport import Sport
from src.app.model.enum.court_status import CourtStatus
from src.app.model.enum.int_enum_type import IntEnumType

# Junção N:N real entre Court e Sport (não JSON) — a busca por esporte filtra
# via join nesta tabela.
court_sport = Table(
    "court_sport",
    BaseModel.metadata,
    Column("court_id", Integer, ForeignKey("court.id"), primary_key=True),
    Column("sport_id", Integer, ForeignKey("sport.id"), primary_key=True),
)


class Court(BaseModel):
    __tablename__ = "court"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("company.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    photos: Mapped[list] = mapped_column(
        JSON, server_default=text("'[]'"), nullable=False
    )
    base_price_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CourtStatus] = mapped_column(
        IntEnumType(CourtStatus),
        server_default=text(str(CourtStatus.ACTIVE.value)),
        nullable=False,
    )

    company: Mapped[Company] = relationship("Company", backref="courts")
    sports: Mapped[list[Sport]] = relationship(
        "Sport", secondary=court_sport, backref="courts"
    )
