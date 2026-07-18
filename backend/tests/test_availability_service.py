"""`AvailabilityService.generate_slots` — função pura, sem DB/HTTP
(backend-api-e-fluxos.md §2.5)."""

from datetime import date, datetime, time, timezone

from src.app.service.availability_service import AvailabilityService

MONDAY = date(2026, 1, 5)  # "seg"
OPENING_HOURS = [
    {"dia_semana": "seg", "abertura": "08:00", "fechamento": "12:00", "fechado": False},
]


def test_generate_slots_all_free_when_no_busy_and_no_past():
    now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)  # bem antes da data
    slots = AvailabilityService.generate_slots(
        opening_hours=OPENING_HOURS,
        busy_intervals=[],
        base_price_hour=10000,
        date=MONDAY,
        now=now,
    )
    assert [(s["start_time"], s["end_time"]) for s in slots] == [
        (time(8, 0), time(9, 0)),
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
    ]
    assert all(s["status"] == "free" for s in slots)
    assert all(s["price"] == 10000 for s in slots)
    assert all(s["group"] is None for s in slots)


def test_generate_slots_marks_past_and_busy_slots():
    # 09:30 do dia — slots com início antes disso contam como passado.
    now = datetime(2026, 1, 5, 9, 30, tzinfo=timezone.utc)
    # Sobrepõe só o slot 10:00-11:00.
    busy_intervals = [(time(10, 15), time(10, 45))]

    slots = AvailabilityService.generate_slots(
        opening_hours=OPENING_HOURS,
        busy_intervals=busy_intervals,
        base_price_hour=10000,
        date=MONDAY,
        now=now,
    )

    statuses = {(s["start_time"], s["end_time"]): s["status"] for s in slots}
    assert statuses[(time(8, 0), time(9, 0))] == "busy"  # passado
    assert statuses[(time(9, 0), time(10, 0))] == "busy"  # passado
    assert statuses[(time(10, 0), time(11, 0))] == "busy"  # sobreposição
    assert statuses[(time(11, 0), time(12, 0))] == "free"


def test_generate_slots_empty_when_closed_that_day():
    opening_hours = [
        {"dia_semana": "seg", "abertura": None, "fechamento": None, "fechado": True},
    ]
    slots = AvailabilityService.generate_slots(
        opening_hours=opening_hours,
        busy_intervals=[],
        base_price_hour=10000,
        date=MONDAY,
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert slots == []


def test_generate_slots_empty_when_weekday_not_configured():
    opening_hours = [
        {"dia_semana": "ter", "abertura": "08:00", "fechamento": "12:00", "fechado": False},
    ]
    slots = AvailabilityService.generate_slots(
        opening_hours=opening_hours,
        busy_intervals=[],
        base_price_hour=10000,
        date=MONDAY,  # é "seg", não "ter"
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert slots == []


def test_generate_slots_never_returns_open_group_in_this_phase():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    slots = AvailabilityService.generate_slots(
        opening_hours=OPENING_HOURS,
        busy_intervals=[(time(8, 0), time(12, 0))],  # tudo ocupado
        base_price_hour=10000,
        date=MONDAY,
        now=now,
    )
    assert all(s["status"] in ("free", "busy") for s in slots)
    assert any(s["status"] == "busy" for s in slots)
