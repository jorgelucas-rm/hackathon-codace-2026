from enum import IntEnum


class PaymentStatus(IntEnum):
    """Máquina de estados do Pagamento (modelo-de-dominio.md §8).

    pending -> approved | denied ; approved -> refunded.
    """

    PENDING = 1
    APPROVED = 2
    DENIED = 3
    REFUNDED = 4
