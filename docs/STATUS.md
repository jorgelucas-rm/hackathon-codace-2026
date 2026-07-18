# STATUS — Orquestração multiagente do backend MVP

Rastreio de ondas, propriedade de arquivos e contratos, mantido pelo
orquestrador conforme `docs/prompt-orquestrador.md`. Branch de integração:
`feat/mvp` (a partir de `develop`).

## Quadro de ondas

| Onda | Escopo | Status |
|---|---|---|
| 0 | Fundação (constantes, ErrorCodes, transação, tests/conftest.py) | ✅ concluída |
| 1 | T-A1 Catálogo ∥ T-A2 Perfil+Favoritos | ✅ concluída |
| 2 | T-B1 Booking+Disponibilidade ∥ T-B2 Pagamento | ✅ concluída |
| 3 | T-C Grupos ∥ T-D Painel | ⏳ em andamento |
| 4 | T-E Notif+Job ∥ T-F Reviews+Seed | ⏳ pendente |

## Matriz-resumo de propriedade

| Área / arquivo | Dono |
|---|---|
| Arquivos compartilhados (`__init__`, `main.py`, constants, error_code, Alembic) | Orquestrador |
| `tests/conftest.py`, caminho de transação | Orquestrador (Onda 0) |
| sport / court / company (catálogo) | T-A1 |
| user (perfil, favoritos) | T-A2 |
| booking / availability / efeitos de booking | T-B1 (depois: T-E só instrumenta) |
| payment (entidade, simulador, split, registro de efeitos) | T-B2 (depois: T-E só instrumenta) |
| open_group / group_member / efeitos de cota | T-C |
| agenda / bloqueio / manual / relatório | T-D |
| notification / jobs | T-E |
| review / seed de demo | T-F |

## Onda 0 — Fundação (concluída)

O que foi feito nesta branch (`feat/mvp`), fora do escopo de qualquer
executor:

1. **`src/environments/constants.py`**: `load_dotenv()` agora usa caminho
   absoluto (`Path(__file__).resolve().parent / ".env"`) — antes dependia do
   cwd do processo e não encontrava o `.env` quando rodado fora do dir
   `src/environments/`. Adicionado `get_env_default(name, default)` (não
   quebra se a var não existir) e as constantes novas: `PAYMENT_TTL_MINUTES`
   (15), `REFUND_DEADLINE_HOURS` (24), `PLATFORM_FEE_PCT` (10),
   `GATEWAY_FEE_PCT` (2), `GROUP_RISK_HOURS` (6), `REMINDER_HOURS` (2),
   `SEED_DEMO` (false). Reexportadas em `src/environments/__init__.py`.
2. **`src/app/model/enum/error_code.py`**: novos códigos — booking/
   disponibilidade (`SLOT_UNAVAILABLE`, `INVALID_STATE`,
   `INVALID_TIME_RANGE`, `OUTSIDE_OPENING_HOURS`, `BOOKING_NOT_REFUNDABLE`),
   pagamento (`PAYMENT_ALREADY_RESOLVED`), grupos (`GROUP_FULL`,
   `ALREADY_MEMBER`, `NOT_GROUP_MEMBER`, `CAPACITY_EXCEEDED`,
   `INVALID_GROUP_CONFIG`), reviews (`ALREADY_REVIEWED`,
   `BOOKING_NOT_ELIGIBLE_FOR_REVIEW`). Se uma task precisar de um código que
   não está aqui, ela **para e reporta** — o orquestrador adiciona.
3. **Caminho de transação** (`src/app/repository/base_repository.py`):
   `BaseRepository.save()` continua commitando a cada chamada (não mexer —
   usos existentes de User/Company dependem disso). Para operações
   multi-entidade que precisam de uma única transação (booking+payment,
   cadeias de efeito, criação de grupo), dois métodos novos:
   - `repository.add(entity) -> T`: `session.add()` + `session.flush()`
     (PK disponível, sem commit).
   - `repository.commit() -> None`: `session.commit()`.
   Padrão de uso no service: chame `add()` em cada repositório envolvido
   (pode ser em repositórios diferentes, mesma `Session` via injeção) e
   finalize com **um único** `algum_repository.commit()` no final do método
   de service. Se uma exceção de domínio for levantada no meio, a sessão é
   revertida automaticamente pelo `get_session` (rollback no `except` do
   generator) — não precisa de try/except manual no service.
4. **`tests/conftest.py`**: banco descartável real (Postgres do
   docker-compose, database dedicado `<POSTGRES_DB>_test`, criado
   automaticamente). Fixtures disponíveis: `client` (TestClient com sessão
   injetada), `db_session`, `create_user`/`create_company` (factories),
   `auth_user`/`auth_company` (entidade + headers `Authorization` prontos).
   Tabelas truncadas após cada teste (autouse). `tests/test_smoke.py` cobre
   o caminho de auth existente como baseline. Rode com
   `.venv/bin/python -m pytest` a partir de `backend/`.
5. **Sem migração nesta onda** — nenhuma entidade nova ainda.

## Onda 1 — Catálogo (spec para T-A1 e T-A2)

Interseção zero por construção: T-A1 é dono de tudo em `sport`/`court`/
`company`; T-A2 é dono de tudo em `user`. Nenhum arquivo compartilhado
precisa de registro nesta onda (não há `__init__.py` novo a tocar — os dois
entity módulos, `company.py` e `user.py`, já existem e são editados
diretamente pelo dono).

### Campos novos — `Company` (T-A1, `entity/company.py`)

| Campo | Tipo | Notas |
|---|---|---|
| `description` | `Text`, nullable | |
| `phone` | `String(20)`, nullable | |
| `latitude` | `Numeric` ou `Float`, nullable | |
| `longitude` | `Numeric` ou `Float`, nullable | |
| `photos` | `JSON`, `server_default='[]'`, not null | lista de base64 |
| `amenities` | `JSON`, `server_default='[]'`, not null | lista de strings (valores livres, sem enum fixo) |
| `opening_hours` | `JSON`, `server_default='[]'`, not null | lista `{dia_semana, abertura, fechamento, fechado}` — ver `modelo-de-dominio.md` §2 |

Todas nullable ou com `server_default` — **obrigatório**, para não quebrar o
fixture `create_company` do conftest (que só passa os campos que já
existiam antes desta onda).

### Entidades novas — T-A1

- `Sport(id, name, icon nullable)` + seed idempotente (rodar no startup ou
  numa função chamada pela migração — decisão do executor) com pelo menos:
  Beach Tênis, Futebol Society, Vôlei, Padel, Basquete.
- `Court(id, company_id FK, name, capacity int, photos JSON, base_price_hour
  int centavos, status enum ativa/inativa via `IntEnumType` — criar
  `CourtStatus` em `model/enum/` **próprio arquivo**, não em `error_code.py`
  nem `__init__.py` compartilhado; registre no seu próprio módulo e importe
  direto onde precisar, sem editar `model/enum/__init__.py`)`.
- Tabela de junção `court_sport` (court_id, sport_id) — relação N:N real
  (não JSON), conforme decisão do plano.

### Rotas — T-A1

`GET /api/sports`; `POST/GET /api/companies/me/courts`; `PATCH
/api/courts/{id}`; `GET /api/courts/{id}` (público); `GET /api/companies`
(busca pública — Haversine em Python, filtros `lat/lng/raio_km`, `sport_id`,
`amenities`, `q`); `GET /api/companies/{id}` (público, detalhe completo);
`PATCH /api/companies/me`.

### Campos novos — `User` (T-A2, `entity/user.py`)

| Campo | Tipo | Notas |
|---|---|---|
| `phone` | `String(20)`, nullable | |
| `latitude` | `Numeric`/`Float`, nullable | |
| `longitude` | `Numeric`/`Float`, nullable | |
| `sports_of_interest` | `JSON`, `server_default='[]'`, not null | lista de ids de `Sport` — **não** FK, T-A2 não depende de T-A1 |
| `favorite_courts` | `JSON`, `server_default='[]'`, not null | lista de ids de `Court` — idem, sem FK; leitura ignora ids órfãos |
| `skill_level` | `String` ou `IntEnum` próprio (`model/enum/` arquivo próprio de T-A2), nullable | iniciante/intermediário/avançado |

Mesma regra: nullable/`server_default` obrigatório.

### Rotas — T-A2

`PATCH /api/users/me`; `GET/POST/DELETE
/api/users/me/favorites/{court_id}` (idempotentes).

### Migração da onda

Uma revisão Alembic **gerada pelo orquestrador** depois do merge de T-A1 e
T-A2, cobrindo as duas entidades novas + as duas extensões de tabela
existente. Ordem de merge: **T-A1 → T-A2 → migração**.

## Onda 1 — concluída

Merge `T-A1 → T-A2` sem conflitos (arquivos disjuntos, como esperado pela
interseção zero). REGISTRAR aplicado pelo orquestrador:

- `controller/__init__.py`: registrados `sport_controller.router`,
  `court_controller.router` e `court_controller.me_router`.
- `model/entity/__init__.py`: registrados `Sport`, `Court`, `court_sport`
  (consistência do metadata para Alembic autogenerate — não estritamente
  necessário para os testes, que importam as entidades diretamente).
- `main.py`: lifespan novo (`asynccontextmanager`) chamando
  `seed_sports(session)` no startup do app (sessão própria via
  `session_maker()`, fechada no `finally`). T-A1 tinha deixado isso opcional
  fora do escopo dele; decisão do orquestrador foi plugar, já que o doc pede
  seed idempotente "no startup ou na migração".
- Migração `0d5b73afd62a_onda_1_...` (Alembic, autogenerate + revisão manual
  do import duplicado): tabelas `sport`, `court`, `court_sport` novas;
  `company` e `user` com as colunas descritas nas tabelas acima. Aplicada e
  testada (`alembic upgrade head` a partir da revisão anterior, banco dev).

**Achado do executor T-A2, corrigido pelo orquestrador**: o banco de teste
(`codace_test`) é compartilhado entre worktrees/execuções contra o mesmo
Postgres do compose. `tests/conftest.py` fazia só `create_all` — se um
executor anterior já tinha criado uma tabela com schema mais antigo (menos
colunas), o `create_all` do executor seguinte não adicionava as colunas
faltantes, e a suíte quebrava com `UndefinedColumn`. Corrigido: a fixture de
sessão agora faz `drop_all` + `create_all` a cada sessão de teste. Isso vale
para todas as ondas seguintes — não deve se repetir.

**Verificação de pronto da onda**: `pytest` (20 passed), app sobe
(`python run.py`), `/docs` e `/openapi.json` respondem 200, seed de sports
aparece em `GET /api/sports` (5 esportes), `GET /api/companies` responde
paginação vazia (sem companies cadastradas ainda no banco dev).

## Onda 2 — Booking + Disponibilidade ∥ Pagamento (contrato + spec)

Onda mais delicada (coração transacional). Contrato B1↔B2 commitado pelo
orquestrador **antes** de despachar os executores — os dois codificam contra
isto, nenhum dos dois o altera.

### Contrato B1↔B2 (já commitado)

- **`entity/payment.py`**: `Payment(id, reference_type: str, reference_id:
  int, amount: int, method: PaymentMethod|None, status: PaymentStatus,
  company_payout|platform_fee|gateway_fee: int|None, refunded_at:
  datetime|None, created_at)`. `reference_type` é string livre por design
  ("booking"/"group_member") — evita acoplar este arquivo compartilhado a um
  enum fechado que mudaria a cada onda nova.
- **`enum/payment_method.py`** (`PIX=1, CARD=2`) e **`enum/payment_status.py`**
  (`PENDING=1, APPROVED=2, DENIED=3, REFUNDED=4`) — arquivos próprios do
  módulo de payment, não tocam `model/enum/__init__.py`.
- **`repository/payment_repository.py`**: `PaymentRepository` (herda
  `BaseRepository`) + `get_by_reference(reference_type, reference_id) ->
  Payment|None` (pega o pagamento mais recente da referência — usado por
  T-B1 para achar o payment de um booking pendente e checar TTL).
- **`dto/payment.py`**: `PaymentSummaryDTO` (forma mínima para embutir
  referência a um payment fora do módulo — ex.: resposta de `POST
  /api/bookings`). T-B2 é dono do arquivo e pode adicionar
  `PaymentReadDTO`/`PaymentConfirmDTO`/etc., mas não remove nem quebra este
  DTO.
- **`service/payment_service.py`** (esqueleto — T-B2 completa os corpos):
  - `PaymentService.create_pending(reference_type: str, reference_id: int,
    amount: int) -> Payment` — **implementado**: `add()` sem commit (caller
    finaliza a transação com um único `commit()`).
  - `PaymentService.is_expired(payment: Payment) -> bool` — **implementado**:
    TTL (`PAYMENT_TTL_MINUTES`) sobre `created_at`, só relevante para
    `PENDING`.
  - `PaymentService.confirm(payment_id: int, result: str, method:
    PaymentMethod|None) -> Payment` — **T-B2 implementa**: idempotente (já
    resolvido → retorna estado atual, sem erro, sem reprocessar); na
    aprovação grava split (`PLATFORM_FEE_PCT`/`GATEWAY_FEE_PCT`) e despacha
    o efeito registrado para o `reference_type`; commit único no fim.
  - `PaymentService.refund(payment_id: int) -> Payment` — **T-B2
    implementa**: `add()` sem commit (caller finaliza a transação).
  - `register_effect_handler(reference_type: str, on_approved:
    Callable[[int, Session], None], on_denied: Callable[[int, Session],
    None]) -> None` — registro de efeitos. Handler recebe `reference_id` e a
    `Session` corrente (a mesma do payment nesta chamada) para buscar/mutar a
    entidade dona **na mesma transação**. T-B1 registra `"booking"` no
    próprio `service/booking_payment_effects.py`; T-C registrará
    `"group_member"` na Onda 3. Import do módulo de efeitos (para o registro
    rodar no boot) é aplicado pelo orquestrador em `service/__init__.py`
    (REGISTRAR pós-merge).
- **`ErrorCode.PAYMENT_ALREADY_RESOLVED`** (já existe desde a Onda 0) — livre
  para T-B2 usar onde fizer sentido (ex.: `refund()` chamado sobre pagamento
  que não está `APPROVED`).

### Task cards da onda

| Task | Escopo | Arquivos que possui | Não toca |
|---|---|---|---|
| **T-B1 Booking + Disponibilidade** | `Booking` (court_id, creator_user_id nullable, creator_company_id nullable, date, start_time, end_time, type `closed\|group`, status `pending\|confirmed\|canceled\|completed\|blocked`, reason, total_price, customer_name/customer_phone), `AvailabilityService.generate_slots(...)` pura + `GET /api/courts/{id}/availability?date=`, `POST /api/bookings` (só `type=closed` nesta fase — `type=group` levanta `INVALID_STATE`, gancho para Onda 3) com lock (`SELECT...FOR UPDATE` na court) + sobreposição → `SLOT_UNAVAILABLE`, preço no servidor, expiração preguiçosa via `payment_service.is_expired`, `GET /api/bookings/{id}`, `GET /api/users/me/bookings?scope=upcoming\|history`, `POST /api/bookings/{id}/cancel` com política de reembolso (chama `payment_service.refund` do contrato; parametrizar por ator — user vs. company — com gancho de cascata para grupo na Onda 3) | `entity/booking.py`, `dto/booking.py`, `repository/booking_repository.py`, `service/availability_service.py`, `service/booking_service.py`, `service/booking_payment_effects.py` (handler `"booking"`), `controller/booking_controller.py`, `controller/availability_controller.py`, `model/enum/booking_status.py` (próprio, não tocar `model/enum/__init__.py`), `model/enum/booking_type.py` (próprio), testes próprios | arquivos de payment (usa só `payment_service`/`Payment`/`PaymentSummaryDTO` do contrato; até o merge de T-B2, testa com stub/monkeypatch de `PaymentService.confirm`/`refund`) |
| **T-B2 Pagamento** | Completar `payment_service.py` (contrato acima), simulador de gateway `POST /api/payments/{id}/confirm` **idempotente**, `GET /api/payments/{id}`, split, estorno, extensão de `dto/payment.py` com os DTOs de leitura/confirmação que faltarem, testes próprios (efeitos testados com handler fake registrado via `register_effect_handler`) | `entity/payment.py` (extensão fina se precisar), `dto/payment.py`, `repository/payment_repository.py`, `service/payment_service.py`, `controller/payment_controller.py`, testes próprios | arquivos de booking |

Regras de exclusividade/TTL/cancelamento: seções 4.1–4.3 do
`backend-api-e-fluxos.md`; máquinas de estado: seção 5 (Agendamento) e 8
(Pagamento) do `modelo-de-dominio.md`.

Ordem de merge: **T-B2 → T-B1** → migração única da onda (tabelas `payment`
e `booking`) → teste de integração da cadeia completa, escrito pelo
orquestrador: criar booking fechado → confirmar pagamento aprovado →
booking `confirmed`; pagamento recusado → booking `canceled` e horário
liberado; pendente expirado (mock de `created_at` no passado) some da
disponibilidade; corrida de dois bookings no mesmo slot → um leva
`SLOT_UNAVAILABLE`.

## Onda 2 — concluída

Merge `T-B2 → T-B1` sem conflitos (arquivos disjuntos por construção — T-B2
só tocou `payment_service.py`/`payment_controller.py`/`dto/payment.py`;
T-B1 só tocou os arquivos de `booking`/`availability`). Ambos entregaram
qualidade alta: T-B2 implementou `confirm`/`refund` exatamente contra o
contrato (idempotência, split, `PAYMENT_ALREADY_RESOLVED`); T-B1 implementou
lock por `SELECT...FOR UPDATE` na `Court`, `generate_slots` como função pura
testada isoladamente, e já deixou o gancho de `type=group` (`INVALID_STATE`)
e o cancelamento parametrizado por ator, prontos para a Onda 3.

REGISTRAR aplicado pelo orquestrador:

- `controller/__init__.py`: registrados `booking_controller.router`,
  `booking_controller.me_router`, `availability_controller.router`,
  `payment_controller.router`.
- `model/entity/__init__.py`: registrado `Booking`.
- `repository/__init__.py`: registrado `BookingRepository`.
- `service/__init__.py`: `from . import booking_payment_effects  # noqa: F401`
  — necessário para o `register_effect_handler("booking", ...)` rodar no
  boot da app (import side-effect); sem isso, `PaymentService.confirm`
  levantaria `KeyError` ao tentar aprovar/recusar um pagamento de booking.
- Migração `1aef7416bb48_onda_2_payment_booking` (Alembic, autogenerate +
  correção manual do import duplicado de `sqlalchemy`, mesmo problema já
  visto na migração da Onda 1): tabelas `payment` e `booking` novas
  (`ix_booking_court_id_date` para as queries de sobreposição/disponibilidade).
  Aplicada e testada (`alembic upgrade head` a partir de `0d5b73afd62a`).
- `tests/test_onda2_integration.py` (novo, escrito pelo orquestrador): cadeia
  completa via rotas reais — aprovação confirma booking e grava split
  íntegro (`platform_fee + gateway_fee + company_payout == amount`); recusa
  cancela booking (`reason=payment_denied`) e libera o slot na
  disponibilidade; confirmação é idempotente mesmo tentando um `result`
  diferente na segunda chamada (mantém o primeiro estado resolvido). Esses
  cenários não podiam ser testados por nenhum executor sozinho (cada um só
  tinha o outro lado como contrato/stub).

**Verificação de pronto da onda**: `pytest` (54 passed — 45 de T-B1, 6 de
T-B2, 3 de integração), app sobe (`uvicorn`) contra o banco dev com a
migração aplicada, `/docs` e `/openapi.json` respondem 200, `/api/sports`
ok. Rotas novas confirmadas no `openapi.json`: `/api/bookings`,
`/api/bookings/{id}`, `/api/bookings/{id}/cancel`, `/api/users/me/bookings`,
`/api/courts/{id}/availability`, `/api/payments/{id}`,
`/api/payments/{id}/confirm`.

## Onda 3 — Grupos ∥ Painel (contrato + spec)

Contrato T-C↔T-D commitado antes de despachar, no mesmo espírito da Onda 2:
como `group_service` só é consumido por T-D em dois pontos, o esqueleto é
enxuto (duas assinaturas + os DTOs/entidades que sustentam o schema), mas
precisa existir **antes** dos dois branches divergirem — do contrário T-D
não teria nem o módulo para importar/stubar.

### Contrato T-C↔T-D (já commitado)

- **`entity/open_group.py`** (`OpenGroup`) e **`entity/group_member.py`**
  (`GroupMember`) — campos conforme `modelo-de-dominio.md` §6-7, traduzidos
  (decisão #3 do `prompt.md`). `GroupMemberStatus` ganhou um terceiro valor
  (`PENDING`) além dos dois do modelo de domínio (`CONFIRMED`/`LEFT`) — é o
  mesmo padrão já usado em `BookingStatus.PENDING`, necessário pra contagem
  "confirmados + pendentes válidos" (`backend-api-e-fluxos.md` §3.3) sem
  inventar um enum incompatível com o domínio.
- **`enum/group_status.py`**, **`enum/group_visibility.py`**,
  **`enum/group_leftover_rule.py`**, **`enum/group_member_status.py`** —
  arquivos próprios, não tocam `model/enum/__init__.py`.
- **`repository/group_repository.py`**: `GroupRepository` (herda
  `BaseRepository`) + `get_by_booking(booking_id) -> OpenGroup|None`.
- **`dto/group.py`**: `GroupCreateDTO` (payload do grupo embutido em `POST
  /api/bookings`) e `GroupPanelSummaryDTO` (retorno de
  `get_panel_summary`, forma que T-D embute na agenda e T-C reaproveita no
  slot `open_group` da disponibilidade).
- **`service/group_service.py`** (esqueleto — T-C completa os corpos, pode
  reescrever `__init__`/`get_service` à vontade, só não quebra as
  assinaturas públicas):
  - `GroupService.get_panel_summary(booking_id: int) ->
    GroupPanelSummaryDTO | None` — **T-C implementa**. É todo o
    conhecimento que T-D precisa do domínio de grupo (nunca importa
    `OpenGroup`/`GroupMember` diretamente).
  - `GroupService.cancel_group(group_id: int, reason: str, commit: bool =
    True) -> None` — **T-C implementa**: estorna cotas aprovadas, marca
    grupo e booking como `CANCELED`. `commit=False` para compor dentro de
    uma transação maior já aberta pelo caller.

### Extensão pontual autorizada em arquivos de T-B1 (Onda 2, já fechada)

Como no plano original, T-C precisa ligar a criação de grupo ao fluxo de
booking — e Onda 2 já mergeou e fechou. Não há conflito de paralelismo
(T-D não toca nesses arquivos), então **T-C tem autorização pontual e
aditiva** (não remover/quebrar o caminho `type=closed` existente, suíte
inteira de T-B1 tem que continuar verde) para estender:

- `model/dto/booking.py`: adicionar `group: Optional[GroupCreateDTO] =
  None` em `BookingCreateDTO`.
- `controller/booking_controller.py`: em `create_booking`, ramificar por
  `dto.type` — `"group"` chama o novo método de `GroupService` (T-C decide o
  nome, ex. `create_group_booking`), `"closed"` mantém a chamada atual a
  `BookingService.create_closed_booking`.
- `service/availability_service.py`: popular o slot `open_group` (usando
  `AvailabilityGroupDTO`, já existente em `dto/booking.py`) quando o
  booking sobreposto for `type=GROUP` com grupo `OPEN`+`PUBLIC` — hoje o
  slot só alterna `free`/`busy`.

### Task cards da onda

| Task | Escopo | Arquivos que possui | Não toca |
|---|---|---|---|
| **T-C Grupos** | Fase C inteira (`docs/prompt.md`): `POST /api/bookings` com `type=group` cria booking+group+member do criador+payment da cota (`reference_type="group_member"`) na mesma transação (`total_spots ≤ capacity`, `min_spots ≤ total_spots`, cota = `ceil(total/spots)`); `GET /api/groups` (busca pública, só `open`+`public` com prazo futuro), `GET /api/groups/{id}` (funciona para `link`), `POST /api/groups/{id}/join` (lock do grupo, `GROUP_FULL`/`ALREADY_MEMBER`), `POST /api/groups/{id}/leave` (reembolso conforme prazo, vaga reabre); handler `"group_member"` no registro de efeitos de payment (aprovado → membro `CONFIRMED`, se lotou → grupo `FULL` + booking `CONFIRMED`); `GroupService.process_deadline(group)` idempotente (mínimo OK → `CONFIRMED`; senão → `CANCELED` via `cancel_group`); slot `open_group` na disponibilidade | `entity/open_group.py`, `entity/group_member.py` (contrato, pode estender), `dto/group.py` (contrato, pode estender), `repository/group_repository.py` (contrato, pode estender), `repository/group_member_repository.py` (novo), `service/group_service.py` (contrato, completa os corpos), `service/group_payment_effects.py` (novo, handler `"group_member"`), `controller/group_controller.py` (novo), testes próprios, **+ extensão pontual aditiva** em `model/dto/booking.py`, `controller/booking_controller.py`, `service/availability_service.py` (ver seção acima) | `service/booking_service.py`, `service/payment_service.py` (usa só os hooks/contrato); arquivos do painel (`company_schedule_*`, `booking_admin_service.py`) |
| **T-D Painel** | Fase D inteira: `GET /api/companies/me/schedule?date=` (grade do dia de todas as courts com bookings ativos; embute cliente — `creator_user_id`/`customer_name`+`customer_phone` — e, se `type=GROUP`, `group_service.get_panel_summary(booking.id)`); bloqueios `POST /api/courts/{id}/blocks` (booking `BLOCKED`+`reason`, mesma validação de exclusividade — lock+overlap reimplementados aqui via os métodos públicos de `BookingRepository`, sem editar `booking_service.py`) e `DELETE /api/bookings/{id}/block`; reserva manual `POST /api/companies/me/manual-bookings` (nasce `CONFIRMED`, sem payment, `customer_name`/`customer_phone` livres, mesma exclusividade); cancelamento pelo estabelecimento reaproveitando `BookingService.cancel_by_company` (já existe, Onda 2) + cascata: se `booking.type==GROUP`, chama `group_service.cancel_group(group_id, reason="canceled_by_company")` (o `group_id` vem do `.id` de `get_panel_summary`); `GET /api/companies/me/report?from=&to=` (ocupação, receita confirmada, picos) | `service/company_schedule_service.py`, `controller/company_schedule_controller.py`, `service/booking_admin_service.py` (bloqueios/manual/cancelamento — arquivo próprio, não é `booking_service.py`), testes próprios | `service/group_service.py`/entidades de grupo (usa só `get_panel_summary`/`cancel_group` do contrato; até o merge de T-C, testa com stub/monkeypatch), `service/booking_service.py` (só chama `cancel_by_company`, não edita) |

Regras: seções 2.7 (rotas de grupo), 3.3/3.4 (fluxos de entrada/fechamento
por prazo), 3.6 (painel) do `backend-api-e-fluxos.md`; máquinas de estado
do Grupo/Participante: `modelo-de-dominio.md` §6-7.

Ordem de merge: **T-C → T-D** → migração única da onda (`open_group`,
`group_member`) → teste de integração da cascata, escrito pelo
orquestrador: criar grupo → segundo user entra e paga cota → grupo lota →
booking `confirmed`; cancelamento pelo estabelecimento de um booking com
grupo real estorna todas as cotas aprovadas e libera o horário.
