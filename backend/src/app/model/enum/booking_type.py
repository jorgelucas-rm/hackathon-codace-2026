from enum import IntEnum


class BookingType(IntEnum):
    """Tipo do Agendamento (modelo-de-dominio.md §5).

    `GROUP` é gancho para a Onda 3 (T-C) — nesta fase `POST /api/bookings`
    só aceita `CLOSED` e levanta `INVALID_STATE` se o payload pedir grupo.

    Arquivo próprio de T-B1 (não registrado em `model/enum/__init__.py`
    compartilhado) — importe direto deste módulo onde precisar:
    `from src.app.model.enum.booking_type import BookingType`.
    """

    CLOSED = 1
    GROUP = 2
