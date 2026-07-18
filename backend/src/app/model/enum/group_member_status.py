from enum import IntEnum


class GroupMemberStatus(IntEnum):
    """modelo-de-dominio.md §7 lista só `confirmado`/`saiu`, mas a contagem
    de vagas ("confirmados + pendentes válidos", backend-api-e-fluxos.md
    §3.3) exige um terceiro estado — mesmo padrão já usado em
    `BookingStatus.PENDING`: a vaga é reservada assim que o membro entra
    (`PENDING`, cota com `Payment` pendente dentro do TTL) e só vira
    `CONFIRMED` quando a cota é aprovada. `LEFT` cobre tanto quem saiu por
    vontade própria quanto quem teve a cota recusada/expirada (T-C decide o
    tratamento exato de recusa/expiração)."""

    PENDING = 1
    CONFIRMED = 2
    LEFT = 3
