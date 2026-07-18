from typing import Optional

from fastapi import Depends

from src.app.model.dto.group import GroupPanelSummaryDTO
from src.app.repository.group_repository import GroupRepository

# Contrato Onda 3 (T-C<->T-D) — esqueleto commitado pelo orquestrador.
#
# T-C é dono deste arquivo e implementa os corpos abaixo — pode reescrever
# `__init__`/`get_service` para injetar o que precisar (GroupMemberRepository,
# BookingRepository, PaymentRepository, PaymentService, etc.), mas não deve
# quebrar as duas assinaturas públicas usadas por T-D: `get_panel_summary` e
# `cancel_group`.


class GroupService:

    def __init__(self, group_repository: GroupRepository):
        self.group_repository = group_repository

    def get_panel_summary(self, booking_id: int) -> Optional[GroupPanelSummaryDTO]:
        """Usado por T-D (`GET /api/companies/me/schedule`) para embutir os
        dados do grupo num booking `type=GROUP`, e por T-C no slot
        `open_group` da disponibilidade. Retorna `None` se o booking não tem
        grupo associado. TODO(T-C): implementar (`filled_spots` = contagem
        de `GroupMember` com status `PENDING` não expirado + `CONFIRMED`,
        mesmo critério de "vaga ocupada" usado no booking)."""
        raise NotImplementedError("T-C implementa o corpo desta função")

    def cancel_group(self, group_id: int, reason: str, commit: bool = True) -> None:
        """Estorna todas as cotas com pagamento `APPROVED`
        (`payment_service.refund`, via `add()` sem commit) e marca
        `OpenGroup.status = CANCELED` + o `Booking` associado como
        `CANCELED` (mesmo `reason`). Chamado por T-D (cancelamento pelo
        estabelecimento cascateando pro grupo) e internamente por
        `process_deadline`/saída do criador (Onda 3 ainda).

        `commit=False` permite compor dentro de uma transação maior já
        aberta pelo caller; por padrão (`True`) finaliza sozinho — é chamado
        como operação independente na maioria dos casos. TODO(T-C):
        implementar corpo completo."""
        raise NotImplementedError("T-C implementa o corpo desta função")

    @staticmethod
    def get_service(
        group_repository: GroupRepository = Depends(GroupRepository.get_instance()),
    ) -> "GroupService":
        return GroupService(group_repository=group_repository)
