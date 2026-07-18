# STATUS — Orquestração multiagente do backend MVP

Rastreio de ondas, propriedade de arquivos e contratos, mantido pelo
orquestrador conforme `docs/prompt-orquestrador.md`. Branch de integração:
`feat/mvp` (a partir de `develop`).

## Quadro de ondas

| Onda | Escopo | Status |
|---|---|---|
| 0 | Fundação (constantes, ErrorCodes, transação, tests/conftest.py) | ✅ concluída |
| 1 | T-A1 Catálogo ∥ T-A2 Perfil+Favoritos | ✅ concluída |
| 2 | T-B1 Booking+Disponibilidade ∥ T-B2 Pagamento | ⏳ em andamento |
| 3 | T-C Grupos ∥ T-D Painel | ⏳ pendente |
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
