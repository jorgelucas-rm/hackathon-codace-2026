from enum import IntEnum


class GroupLeftoverRule(IntEnum):
    """`backend-api-e-fluxos.md` §3.4: decisão de MVP — `CREATOR_ABSORBS` não
    exige ação (cotas pagas ficam como estão); `RECALCULATE_QUOTA` é só
    registrada/comunicada na notificação, sem ajuste financeiro real
    (estorno parcial fica para v2)."""

    CREATOR_ABSORBS = 1
    RECALCULATE_QUOTA = 2
