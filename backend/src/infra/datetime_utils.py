"""Fuso do estabelecimento e helper para tornar a hora de parede das reservas
ciente do fuso local.

As reservas guardam `date` + `start_time`/`end_time` como horário de parede
local (o valor que o usuário informa na agenda). Comparar esse valor com
`datetime.now(timezone.utc)` só é correto se ele for tornado ciente no fuso
local — senão a hora é interpretada como UTC e as comparações ficam
deslocadas pelo offset (ex.: uma reserva às 11:00 local seria tratada como
11:00 UTC e marcada como concluída ~3h cedo).
"""

from datetime import date as date_
from datetime import datetime, time, timedelta, timezone

from src.environments.constants import APP_UTC_OFFSET_HOURS

APP_TZ = timezone(timedelta(hours=APP_UTC_OFFSET_HOURS))


def local_datetime(day: date_, moment: time) -> datetime:
    """Combina data + hora de parede local num `datetime` ciente do fuso do
    estabelecimento (comparável com `datetime.now(timezone.utc)`)."""
    return datetime.combine(day, moment, tzinfo=APP_TZ)
