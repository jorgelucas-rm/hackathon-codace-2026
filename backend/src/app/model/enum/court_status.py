from enum import IntEnum


class CourtStatus(IntEnum):
    """Status operacional de uma quadra.

    Arquivo próprio de T-A1 (não registrado em `model/enum/__init__.py`
    compartilhado) — importe direto deste módulo onde precisar:
    `from src.app.model.enum.court_status import CourtStatus`.
    """

    ACTIVE = 1
    INACTIVE = 2
