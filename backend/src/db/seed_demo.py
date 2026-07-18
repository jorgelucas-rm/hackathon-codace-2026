"""Seed de demonstração (Fase F, T-F) — dados fictícios para a demo do
hackathon: companies geolocalizadas, quadras, agendamentos variados, grupos
abertos e avaliações.

Decisões locais desta task:

- Região: Fortaleza-CE (coordenadas reais de bairros conhecidos) — o
  hackathon é do IFCE/Codace, então mantém a demo "familiar".
- Fotos: nenhuma no seed (`photos=[]`) — companies/courts agora guardam
  object keys do MinIO, não base64; o seed não sobe arquivos reais pro
  bucket, só deixa o campo vazio (mesmo padrão dos testes existentes).
- Idempotência: cada `Booking` semeado carrega uma chave única no campo
  `reason` (`f"seed-demo:{slug}"`) — problema de usar `date`/`start_time`
  como chave natural é que este seed usa datas *relativas a `datetime.now()`*
  (para sempre ter reservas "no passado"/"no futuro" válidas quando a demo
  roda), então a data absoluta muda a cada execução em dias diferentes; a
  chave em `reason` não muda. Antes de criar cada booking, verifica se já
  existe uma linha com aquele `reason` e pula se sim. Companies/users usam
  CNPJ/e-mail fixos como chave natural (mais simples, já são únicos no
  schema). `OpenGroup` é 1:1 com `Booking` (unique em `booking_id`), então
  fica coberto pela mesma checagem do booking correspondente. `Review` usa
  o `UniqueConstraint(booking_id, user_id)` do próprio schema como guarda
  (checagem via `get_by_booking_and_user` antes do insert).
- Preços em centavos (mesmo padrão dos testes/fixtures existentes, ex.
  `tests/booking_test_setup.py`: `base_price_hour=10000` = R$100,00/h).
"""

from datetime import date as date_
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from src.app.model.entity.booking import Booking
from src.app.model.entity.company import Company
from src.app.model.entity.court import Court
from src.app.model.entity.group_member import GroupMember
from src.app.model.entity.open_group import OpenGroup
from src.app.model.entity.payment import Payment
from src.app.model.entity.review import Review
from src.app.model.entity.sport import Sport
from src.app.model.entity.user import User
from src.app.model.enum.booking_status import BookingStatus
from src.app.model.enum.booking_type import BookingType
from src.app.model.enum.group_leftover_rule import GroupLeftoverRule
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.model.enum.group_status import GroupStatus
from src.app.model.enum.group_visibility import GroupVisibility
from src.app.model.enum.level import Level
from src.app.model.enum.payment_method import PaymentMethod
from src.app.model.enum.payment_status import PaymentStatus
from src.app.model.enum.skill_level import SkillLevel
from src.infra.security import hash_password

_DEMO_PASSWORD = "Demo@12345"

_ALL_DAYS_OPEN = [
    {"dia_semana": code, "abertura": "08:00", "fechamento": "22:00", "fechado": False}
    for code in ("seg", "ter", "qua", "qui", "sex", "sab")
] + [{"dia_semana": "dom", "abertura": "08:00", "fechamento": "18:00", "fechado": False}]

# Companies demo — coordenadas reais de bairros de Fortaleza-CE.
_SEED_COMPANIES = [
    {
        "cnpj": "11.111.111/0001-11",
        "name": "Arena Beira-Mar",
        "email": "contato@arenabeiramar.demo",
        "street": "Av. Beira Mar",
        "number": "1000",
        "neighborhood": "Meireles",
        "city": "Fortaleza",
        "state": "CE",
        "zip_code": "60165-121",
        "latitude": -3.7275,
        "longitude": -38.4886,
        "description": "Arena completa à beira-mar, com quadras de areia e cobertas.",
        "phone": "(85) 3000-1111",
        "amenities": ["estacionamento", "vestiario", "wifi", "lanchonete"],
        "courts": [
            {"name": "Quadra 1 - Beach Tênis", "capacity": 4, "base_price_hour": 8000, "sports": ["Beach Tênis"]},
            {"name": "Quadra 2 - Vôlei de Praia", "capacity": 4, "base_price_hour": 7000, "sports": ["Vôlei"]},
        ],
    },
    {
        "cnpj": "22.222.222/0001-22",
        "name": "Society Aldeota",
        "email": "contato@societyaldeota.demo",
        "street": "Rua Barão de Studart",
        "number": "500",
        "neighborhood": "Aldeota",
        "city": "Fortaleza",
        "state": "CE",
        "zip_code": "60120-000",
        "latitude": -3.7386,
        "longitude": -38.5054,
        "description": "Quadras de futebol society com grama sintética.",
        "phone": "(85) 3000-2222",
        "amenities": ["estacionamento", "vestiario", "churrasqueira"],
        "courts": [
            {"name": "Quadra Society 1", "capacity": 14, "base_price_hour": 12000, "sports": ["Futebol Society"]},
        ],
    },
    {
        "cnpj": "33.333.333/0001-33",
        "name": "Padel Center Cocó",
        "email": "contato@padelcoco.demo",
        "street": "Av. Rogaciano Leite",
        "number": "250",
        "neighborhood": "Cocó",
        "city": "Fortaleza",
        "state": "CE",
        "zip_code": "60192-090",
        "latitude": -3.7660,
        "longitude": -38.4787,
        "description": "Especializada em Padel, com quadras profissionais.",
        "phone": "(85) 3000-3333",
        "amenities": ["estacionamento", "wifi", "loja"],
        "courts": [
            {"name": "Quadra Padel 1", "capacity": 4, "base_price_hour": 9000, "sports": ["Padel"]},
            {"name": "Quadra Padel 2", "capacity": 4, "base_price_hour": 9000, "sports": ["Padel"]},
        ],
    },
    {
        "cnpj": "44.444.444/0001-44",
        "name": "Ginásio Basquete Bezerra",
        "email": "contato@ginasiobezerra.demo",
        "street": "Rua Osvaldo Cruz",
        "number": "80",
        "neighborhood": "Bezerra de Menezes",
        "city": "Fortaleza",
        "state": "CE",
        "zip_code": "60355-160",
        "latitude": -3.7420,
        "longitude": -38.5432,
        "description": "Ginásio coberto para basquete e vôlei indoor.",
        "phone": "(85) 3000-4444",
        "amenities": ["estacionamento", "vestiario"],
        "courts": [
            {"name": "Quadra Coberta 1", "capacity": 10, "base_price_hour": 7500, "sports": ["Basquete"]},
        ],
    },
]

# Usuários demo — jogadores que participam das reservas/grupos/avaliações.
_SEED_USERS = [
    {"name": "Ana Souza", "email": "ana.demo@codace.dev", "phone": "(85) 99000-0001", "skill_level": SkillLevel.INTERMEDIATE},
    {"name": "Bruno Lima", "email": "bruno.demo@codace.dev", "phone": "(85) 99000-0002", "skill_level": SkillLevel.BEGINNER},
    {"name": "Carla Dias", "email": "carla.demo@codace.dev", "phone": "(85) 99000-0003", "skill_level": SkillLevel.ADVANCED},
    {"name": "Diego Alves", "email": "diego.demo@codace.dev", "phone": "(85) 99000-0004", "skill_level": SkillLevel.INTERMEDIATE},
    {"name": "Elisa Rocha", "email": "elisa.demo@codace.dev", "phone": "(85) 99000-0005", "skill_level": SkillLevel.BEGINNER},
    {"name": "Felipe Nunes", "email": "felipe.demo@codace.dev", "phone": "(85) 99000-0006", "skill_level": SkillLevel.INTERMEDIATE},
]


def _get_or_create_company(session: Session, data: dict) -> tuple[Company, bool]:
    company = session.query(Company).filter(Company.cnpj == data["cnpj"]).first()
    if company:
        return company, False

    company = Company(
        cnpj=data["cnpj"],
        name=data["name"],
        email=data["email"],
        password=hash_password(_DEMO_PASSWORD),
        street=data["street"],
        number=data["number"],
        neighborhood=data["neighborhood"],
        city=data["city"],
        state=data["state"],
        zip_code=data["zip_code"],
        description=data["description"],
        phone=data["phone"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        photos=[],
        amenities=data["amenities"],
        opening_hours=_ALL_DAYS_OPEN,
    )
    session.add(company)
    session.flush()
    return company, True


def _get_or_create_user(session: Session, data: dict) -> tuple[User, bool]:
    user = session.query(User).filter(User.email == data["email"]).first()
    if user:
        return user, False

    user = User(
        name=data["name"],
        email=data["email"],
        password=hash_password(_DEMO_PASSWORD),
        role=Level.USER,
        phone=data["phone"],
        skill_level=data["skill_level"],
    )
    session.add(user)
    session.flush()
    return user, True


def _get_or_create_court(
    session: Session, company: Company, data: dict, sports_by_name: dict[str, Sport]
) -> tuple[Court, bool]:
    court = (
        session.query(Court)
        .filter(Court.company_id == company.id, Court.name == data["name"])
        .first()
    )
    if court:
        return court, False

    court = Court(
        company_id=company.id,
        name=data["name"],
        capacity=data["capacity"],
        photos=[],
        base_price_hour=data["base_price_hour"],
    )
    court.sports = [
        sports_by_name[name] for name in data["sports"] if name in sports_by_name
    ]
    session.add(court)
    session.flush()
    return court, True


def _get_booking_by_seed_key(session: Session, seed_key: str) -> Booking | None:
    return session.query(Booking).filter(Booking.reason == seed_key).first()


def _create_booking_with_payment(
    session: Session,
    *,
    seed_key: str,
    court: Court,
    creator_user_id: int,
    date: date_,
    start_time: time,
    end_time: time,
    booking_status: BookingStatus,
    booking_type: BookingType = BookingType.CLOSED,
) -> Booking:
    """Cria `Booking` + `Payment(APPROVED)` (quando o status implica
    pagamento resolvido) diretamente via sessão — o seed roda fora da API,
    então não passa pelo `PaymentService`/handlers de efeito (que exigiriam
    registrar o reference_type na inicialização); os totais de split
    (`platform_fee`/`gateway_fee`/`company_payout`) são calculados aqui só
    para consistência visual da demo, sem reusar `PLATFORM_FEE_PCT`/
    `GATEWAY_FEE_PCT` (não é fluxo real de pagamento)."""
    duration_hours = (
        datetime.combine(date_.min, end_time) - datetime.combine(date_.min, start_time)
    ).total_seconds() / 3600
    total_price = round(court.base_price_hour * duration_hours)

    booking = Booking(
        court_id=court.id,
        creator_user_id=creator_user_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        type=booking_type,
        status=booking_status,
        total_price=total_price,
        # Chave de idempotência do seed (ver docstring do módulo) — não é
        # usado como "motivo de cancelamento" real aqui.
        reason=seed_key,
    )
    session.add(booking)
    session.flush()

    if booking_status in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED):
        platform_fee = total_price * 10 // 100
        gateway_fee = total_price * 2 // 100
        payment = Payment(
            reference_type="booking",
            reference_id=booking.id,
            amount=total_price,
            method=PaymentMethod.PIX,
            status=PaymentStatus.APPROVED,
            platform_fee=platform_fee,
            gateway_fee=gateway_fee,
            company_payout=total_price - platform_fee - gateway_fee,
        )
        session.add(payment)
        session.flush()

    return booking


def seed_demo(session: Session) -> None:
    """Seed idempotente dos dados de demonstração — chamado no lifespan do
    app quando `SEED_DEMO=true` (ver `environments.constants.SEED_DEMO`).

    Ordem: sports (assume já semeados por `seed_sports`, chamado antes no
    lifespan) -> companies+courts -> users -> bookings (fechados e de
    grupo) -> reviews nos bookings `COMPLETED`.
    """
    sports_by_name = {s.name: s for s in session.query(Sport).all()}

    companies: list[Company] = []
    courts_by_company: dict[int, list[Court]] = {}
    for company_data in _SEED_COMPANIES:
        company, _created = _get_or_create_company(session, company_data)
        companies.append(company)
        courts_by_company[company.id] = [
            _get_or_create_court(session, company, court_data, sports_by_name)[0]
            for court_data in company_data["courts"]
        ]
    session.commit()

    users: list[User] = []
    for user_data in _SEED_USERS:
        user, _created = _get_or_create_user(session, user_data)
        users.append(user)
    session.commit()

    now = datetime.now(timezone.utc)
    today = now.date()

    # ------------------------------------------------------------------
    # Bookings variados por company: 1 CONFIRMED no futuro (agenda ativa) +
    # 1 COMPLETED no passado (elegível para review).
    # ------------------------------------------------------------------
    completed_bookings: list[Booking] = []
    for c_idx, company in enumerate(companies):
        court = courts_by_company[company.id][0]
        creator = users[c_idx % len(users)]

        future_key = f"seed-demo:{company.cnpj}:upcoming"
        if not _get_booking_by_seed_key(session, future_key):
            _create_booking_with_payment(
                session,
                seed_key=future_key,
                court=court,
                creator_user_id=creator.id,
                date=today + timedelta(days=3 + c_idx),
                start_time=time(18, 0),
                end_time=time(19, 0),
                booking_status=BookingStatus.CONFIRMED,
            )

        past_key = f"seed-demo:{company.cnpj}:completed"
        past_booking = _get_booking_by_seed_key(session, past_key)
        if not past_booking:
            past_booking = _create_booking_with_payment(
                session,
                seed_key=past_key,
                court=court,
                creator_user_id=creator.id,
                date=today - timedelta(days=10 + c_idx),
                start_time=time(19, 0),
                end_time=time(20, 0),
                booking_status=BookingStatus.COMPLETED,
            )
        completed_bookings.append(past_booking)

        # Booking CLOSED simples (sem pagamento aprovado) — histórico
        # variado, mostra reserva pendente/expirada na agenda.
        pending_key = f"seed-demo:{company.cnpj}:pending"
        if not _get_booking_by_seed_key(session, pending_key):
            _create_booking_with_payment(
                session,
                seed_key=pending_key,
                court=court,
                creator_user_id=users[(c_idx + 1) % len(users)].id,
                date=today + timedelta(days=1),
                start_time=time(9, 0),
                end_time=time(10, 0),
                booking_status=BookingStatus.PENDING,
            )
    session.commit()

    # ------------------------------------------------------------------
    # 2 grupos abertos (type=GROUP, status=OPEN) com vagas disponíveis, nas
    # duas primeiras companies.
    # ------------------------------------------------------------------
    for g_idx in range(min(2, len(companies))):
        company = companies[g_idx]
        court = courts_by_company[company.id][0]
        creator = users[g_idx]

        group_key = f"seed-demo:{company.cnpj}:group"
        group_booking = _get_booking_by_seed_key(session, group_key)
        if not group_booking:
            group_booking = _create_booking_with_payment(
                session,
                seed_key=group_key,
                court=court,
                creator_user_id=creator.id,
                date=today + timedelta(days=5 + g_idx),
                start_time=time(20, 0),
                end_time=time(21, 0),
                booking_status=BookingStatus.PENDING,
                booking_type=BookingType.GROUP,
            )

            total_spots = 6
            spot_price = -(-group_booking.total_price // total_spots)
            group = OpenGroup(
                booking_id=group_booking.id,
                total_spots=total_spots,
                min_spots=4,
                spot_price=spot_price,
                visibility=GroupVisibility.PUBLIC,
                closing_deadline=now + timedelta(days=4 + g_idx),
                leftover_rule=GroupLeftoverRule.CREATOR_ABSORBS,
                status=GroupStatus.OPEN,
            )
            session.add(group)
            session.flush()

            creator_member = GroupMember(
                group_id=group.id,
                user_id=creator.id,
                status=GroupMemberStatus.CONFIRMED,
            )
            session.add(creator_member)

            # Mais um membro confirmado, deixando vagas ainda disponíveis.
            second_member_user = users[(g_idx + 2) % len(users)]
            second_member = GroupMember(
                group_id=group.id,
                user_id=second_member_user.id,
                status=GroupMemberStatus.CONFIRMED,
            )
            session.add(second_member)
    session.commit()

    # ------------------------------------------------------------------
    # Reviews nos bookings COMPLETED (só o criador — único jogador
    # garantido nesses bookings fechados simples).
    # ------------------------------------------------------------------
    review_comments = [
        (5, "Quadra excelente, recomendo!"),
        (4, "Muito boa, só faltou um pouco de manutenção no piso."),
        (5, "Estrutura ótima, com certeza volto."),
        (3, "Boa, mas o estacionamento é pequeno."),
    ]
    for idx, booking in enumerate(completed_bookings):
        rating, comment = review_comments[idx % len(review_comments)]
        existing = (
            session.query(Review)
            .filter(
                Review.booking_id == booking.id,
                Review.user_id == booking.creator_user_id,
            )
            .first()
        )
        if existing:
            continue
        review = Review(
            company_id=booking.court.company_id,
            booking_id=booking.id,
            user_id=booking.creator_user_id,
            rating=rating,
            comment=comment,
        )
        session.add(review)
    session.commit()
