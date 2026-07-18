from datetime import date as date_
from datetime import datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.app.model.dto.payment import PaymentSummaryDTO

# Contrato Onda 3 (T-C<->T-D) — esqueleto commitado pelo orquestrador.
# Além do contrato (GroupCreateDTO/GroupPanelSummaryDTO), T-C estende este
# arquivo com os DTOs de leitura/resposta das rotas de grupo.


class GroupCreateDTO(BaseModel):
    """Payload embutido em `POST /api/bookings` quando `type=group`
    (`backend-api-e-fluxos.md` §2.6). T-C adiciona o campo
    `group: Optional[GroupCreateDTO] = None` em `BookingCreateDTO`
    (`dto/booking.py`) — extensão pontual autorizada nesta onda (arquivo
    de T-B1, Onda 2 já fechada, sem conflito com T-D)."""

    total_spots: int = Field(..., ge=1)
    min_spots: int = Field(..., ge=1)
    visibility: Literal["public", "link"] = "public"
    closing_deadline: datetime
    leftover_rule: Literal["creator_absorbs", "recalculate_quota"] = "creator_absorbs"


class GroupPanelSummaryDTO(BaseModel):
    """Retornada por `GroupService.get_panel_summary(booking_id)`. Usada por
    T-C (slot `open_group` da disponibilidade, mapeada para
    `AvailabilityGroupDTO` em `dto/booking.py`) e por T-D (grade do painel,
    `GET /api/companies/me/schedule`) — é o contrato que evita T-D precisar
    conhecer `OpenGroup`/`GroupMember` diretamente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    total_spots: int
    min_spots: int
    filled_spots: int
    spot_price: int
    visibility: str
    closing_deadline: datetime


class GroupMemberReadDTO(BaseModel):
    """Item de participante embutido em `GroupReadDTO` — o doc pede
    "participantes confirmados (nome + foto)" no detalhe do grupo
    (`backend-api-e-fluxos.md` §2.7); `user_avatar` acompanha `user_name`
    pelo mesmo motivo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    status: str
    joined_at: datetime


class GroupReadDTO(BaseModel):
    """Forma completa de um grupo aberto — usada tanto por
    `GET /api/groups/{id}` (detalhe, inclui `members`) quanto por
    `GET /api/groups` (busca pública, mesmo shape reaproveitado: a busca só
    filtra `status=open` + `visibility=public` + `closing_deadline` futuro,
    não reduz os campos). `members` só lista participantes `CONFIRMED`
    (mesmo critério do doc: "participantes confirmados")."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    court_id: int
    court_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    date: date_
    start_time: time
    end_time: time
    status: str
    total_spots: int
    min_spots: int
    filled_spots: int
    spot_price: int
    visibility: str
    closing_deadline: datetime
    leftover_rule: str
    members: list[GroupMemberReadDTO] = Field(default_factory=list)


class GroupJoinResponseDTO(BaseModel):
    """Resposta de `POST /api/groups/{id}/join`: o membro recém-criado
    (`PENDING`), o pagamento pendente da cota (mesmo padrão de
    `BookingCreateResponseDTO`) e o resumo atualizado do grupo."""

    member: GroupMemberReadDTO
    payment: PaymentSummaryDTO
    group: GroupPanelSummaryDTO


class GroupLeaveResponseDTO(BaseModel):
    group: GroupPanelSummaryDTO
    refunded: bool
