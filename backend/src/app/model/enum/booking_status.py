from enum import IntEnum


class BookingStatus(IntEnum):
    """Máquina de estados do Agendamento (modelo-de-dominio.md §5).

    pending -> confirmed | canceled (pagamento aprovado/recusado-expirado)
    confirmed -> canceled | completed
    blocked -> canceled (remoção de bloqueio)

    Arquivo próprio de T-B1 (não registrado em `model/enum/__init__.py`
    compartilhado) — importe direto deste módulo onde precisar:
    `from src.app.model.enum.booking_status import BookingStatus`.
    """

    PENDING = 1
    CONFIRMED = 2
    CANCELED = 3
    COMPLETED = 4
    BLOCKED = 5
