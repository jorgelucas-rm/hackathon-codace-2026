from enum import IntEnum


class GroupStatus(IntEnum):
    """Máquina de estados do Grupo Aberto (modelo-de-dominio.md §6).

    aberto -> completo | confirmado | cancelado ; completo -> confirmado.
    """

    OPEN = 1
    FULL = 2
    CONFIRMED = 3
    CANCELED = 4
