"""Suporte compartilhado pelos testes de booking/availability (T-B1).

Não é um módulo `test_*` — pytest não o coleta como suíte de testes, só é
importado pelos módulos que precisam dele.

**Nota para o orquestrador**: `booking_controller.router`/`me_router` e
`availability_controller.router` ainda não estão registrados em
`src.app.controller` (arquivo compartilhado, fora do escopo de T-B1 — ver
REGISTRAR no relatório da task). `ensure_booking_routes_registered()`
inclui esses routers diretamente na instância `app` só para os testes desta
task rodarem via `TestClient` antes desse registro acontecer; depois que o
orquestrador plugar os routers em `controller/__init__.py`, esta função
continua segura (checa se a rota já existe antes de incluir de novo).
"""

from src.app.controller import availability_controller, booking_controller
from src.app.main import app

_WEEKDAY_CODES = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def ensure_booking_routes_registered() -> None:
    existing_paths = {getattr(r, "path", "") for r in app.routes}

    if "/api/bookings" not in existing_paths:
        app.include_router(booking_controller.router, prefix="/api")
        app.include_router(booking_controller.me_router, prefix="/api")

    if "/api/courts/{court_id}/availability" not in existing_paths:
        app.include_router(availability_controller.router, prefix="/api")


def full_week_opening_hours(opening: str = "06:00", closing: str = "23:00") -> list[dict]:
    """`Company.opening_hours` todo aberto — evita depender de qual dia da
    semana cai a data usada no teste."""
    return [
        {"dia_semana": code, "abertura": opening, "fechamento": closing, "fechado": False}
        for code in _WEEKDAY_CODES
    ]


def create_test_court(db_session, company, **overrides):
    from src.app.model.entity.court import Court

    defaults = dict(
        company_id=company.id,
        name="Quadra de Teste",
        capacity=10,
        photos=[],
        base_price_hour=10000,
    )
    defaults.update(overrides)
    court = Court(**defaults)
    db_session.add(court)
    db_session.commit()
    db_session.refresh(court)
    return court
