# Prompt — Implementar o backend do MVP sobre o código existente

> Prompt pronto para colar em um agente de código trabalhando no repositório
> `hackathon-codace-2026` (branch base: `develop`). Junto com este prompt, forneça ao
> agente os três documentos de referência:
> [modelo-de-dominio.md](modelo-de-dominio.md),
> [backend-api-e-fluxos.md](backend-api-e-fluxos.md) e
> [backend-plano-implementacao.md](backend-plano-implementacao.md)
> (copie-os para `docs/` no repositório ou anexe ao contexto).

---

## Prompt

Você vai implementar o backend do MVP de um marketplace de agendamento de quadras
esportivas ("iFood das quadras") **sobre um backend FastAPI que já existe e funciona**.
Não é um projeto novo: há fundação pronta (auth, camadas, infra) e você deve
estendê-la seguindo à risca as convenções existentes.

### 1. Documentos de referência (leia antes de codar)

1. `modelo-de-dominio.md` — entidades, atributos, relacionamentos e máquinas de
   estado (Agendamento, Grupo, Pagamento). É a fonte de verdade do domínio.
2. `backend-api-e-fluxos.md` — todas as rotas com regras de negócio por endpoint,
   fluxos de ponta a ponta e regras transversais (exclusividade de horário, TTL de
   pendentes, job de pendências, política de cancelamento).
3. `backend-plano-implementacao.md` — fases de implementação e diretrizes.

**Regra de precedência**: onde esses documentos conflitarem com o código existente
(estrutura de pastas, stack, convenções), **o código existente vence**. Os documentos
mandam no *quê* (domínio, regras, rotas); o repositório manda no *como*. As
divergências já mapeadas estão na seção 3 deste prompt — siga-as.

### 2. O que já existe no repositório (não recriar, não reescrever)

Backend em `backend/src/`, arquitetura em camadas com injeção de dependência:

- **Camadas**: `app/controller/` (routers finos) → `app/service/` (regras de
  negócio, factory `get_service`) → `app/repository/` (`BaseRepository` genérico com
  paginação/filtros/ordenação) → `app/model/entity/` (SQLAlchemy 2.0 `Mapped`).
- **DTOs**: `app/model/dto/` (Pydantic), com envelope de resposta
  `Response[T] { code, message, data }` e `Pagination[T]` para listagens.
- **Enums**: `app/model/enum/` — `Level` (ADMIN/USER/COMPANY), `ErrorCode`,
  `HttpCode`, `AuthType` (USER/COMPANY), `IntEnumType` para persistir enums.
- **Auth**: JWT com `auth_type` distinguindo dois atores — `User` (jogador, login em
  `POST /api/auth/user-login`) e `Company` (estabelecimento, login em
  `POST /api/auth/company-login`) — com `require_auth`, `require_roles(...)` e
  `RequestContext` para acessar o ator logado. `GET /api/auth/me` pronto.
- **Entidades existentes**: `User` (id int, name, email, password, role, situation)
  e `Company` (id int, cnpj, name, email, password, endereço em campos soltos,
  situation). CRUDs básicos de ambos prontos (`/api/users`, `/api/companies`,
  rotas admin em `/api/admin/...`).
- **Infra**: exceções de domínio (`DomainException` + subclasses + handler global),
  middleware CORS, rate limiter (slowapi), Postgres + Alembic (migração inicial já
  existe), MinIO adapter (não usar no MVP — ver 3.4), Docker/docker-compose.
- **Prefixo das rotas**: `/api` (não `/api/v1`). Rotas administrativas ficam em
  router separado com prefixo `/admin`.

Estude `user_controller.py`, `user_service.py`, `base_repository.py` e
`auth_controller.py` como gabarito de estilo antes de escrever qualquer arquivo novo.

### 3. Decisões de reconciliação (documentos × código) — já tomadas, não rediscutir

1. **Estabelecimento = `Company`**. O modelo de domínio previa
   `Estabelecimento` + vínculo `EstabelecimentoAdmin` com usuários. No repositório o
   estabelecimento é um **ator autenticado próprio** (`Company`, login separado).
   Adote isso: **não crie `EstabelecimentoAdmin`**. Toda rota que os docs marcam como
   "admin" vira rota autenticada com `require_auth` + `auth_type=COMPANY`, e o
   recurso deve pertencer à company logada (`RequestContext`), senão
   `ForbiddenException` com `ErrorCode.RESOURCE_NOT_OWNED`. Estenda `Company` com os
   campos que faltam do domínio: `description`, `phone`, `latitude`, `longitude`,
   `photos` (JSON), `amenities` (JSON), `opening_hours` (JSON, formato do
   modelo de domínio).
2. **IDs**: inteiros autoincrementais, como as entidades existentes (os docs dizem
   UUID — ignore).
3. **Nomes em inglês**, seguindo o padrão do código: `Sport`, `Court`, `Booking`
   (Agendamento), `OpenGroup` (Grupo), `GroupMember` (Participante), `Payment`,
   `Review` (Avaliação), `Notification`. Rotas idem: `/api/sports`, `/api/courts`,
   `/api/bookings`, `/api/groups`, `/api/payments`, `/api/reviews`,
   `/api/notifications`, `/api/companies/{id}/...`. Os nomes PT das rotas nos docs
   são especificação, não literal — traduza mantendo verbo/semântica
   (ex.: `POST /agendamentos/{id}/cancelar` → `POST /api/bookings/{id}/cancel`).
4. **Fotos**: base64 no banco (coluna JSON/Text), conforme decisão do modelo de
   domínio. O MinIO adapter existe mas **não** entra no MVP. Limite ~500KB por foto
   validado no DTO; listagens retornam só a foto de capa.
5. **Formato de erro**: use a hierarquia `DomainException` + `ErrorCode` existente
   (o envelope `{codigo, mensagem}` dos docs equivale ao formato do handler global).
   Adicione ao `ErrorCode` os códigos de negócio novos:
   `SLOT_UNAVAILABLE`, `GROUP_FULL`, `INVALID_STATE`, `ALREADY_MEMBER`,
   `BOOKING_NOT_REFUNDABLE` (e o que mais precisar, seguindo o padrão).
6. **Paginação**: use `Pagination[T]` e os filtros do `BaseRepository` existentes,
   não o formato `{items, total}` dos docs.
7. **Dinheiro em centavos (int)** e **datas em UTC** — igual nos docs, sem exceção.
8. **Config**: novas constantes em `src/environments/constants.py` seguindo o padrão
   `get_env` (com defaults sensatos via `os.getenv(name, default)` para não quebrar
   o compose): `PAYMENT_TTL_MINUTES=15`, `REFUND_DEADLINE_HOURS=24`,
   `PLATFORM_FEE_PCT=10`, `GATEWAY_FEE_PCT=2`, `GROUP_RISK_HOURS=6`,
   `REMINDER_HOURS=2`, `SEED_DEMO=false`.
9. **Migrações**: toda entidade nova entra via migração Alembic (uma por fase, não
   uma por tabela). Seed de esportes idempotente (na migração ou no startup).

### 4. O que implementar (ordem obrigatória)

Siga as fases abaixo — são as fases 2–7 do plano, ajustadas ao que já existe (as
fases 0–1 do plano estão prontas no repositório). **Cada fase deve terminar com o
app subindo, migração aplicada e testes passando antes de começar a próxima.**

#### Fase A — Catálogo (plano: fase 2)

- Entidades + migração: `Sport` (com seed), `Court` (company_id, name, capacity,
  photos, base_price_hour em centavos, status) e junção `court_sport`.
- Campos novos de `Company` (item 3.1) + campos de perfil de `User` que faltam:
  `phone`, `photo`, `latitude`, `longitude`, `sports_of_interest` (JSON),
  `favorite_courts` (JSON), `skill_level`.
- Rotas: `GET /api/sports`; CRUD de courts da company logada
  (`POST/GET /api/companies/me/courts`, `PATCH /api/courts/{id}`);
  `GET /api/courts/{id}` público; **busca pública**
  `GET /api/companies` com filtros `lat/lng/raio_km` (Haversine em Python),
  `sport_id`, `amenities`, `q` — card com distância, menor preço e nota média;
  `GET /api/companies/{id}` público (detalhe completo); `PATCH /api/companies/me`.
- Favoritos: `GET/POST/DELETE /api/users/me/favorites/{court_id}` (idempotentes,
  IDs órfãos ignorados na leitura).

#### Fase B — Disponibilidade + Reserva fechada + Pagamento simulado (plano: fase 3) ⚠️ coração

- Entidades + migração: `Booking` (court_id, creator_user_id nullable,
  creator_company_id nullable — para bloqueio/reserva manual —, date, start_time,
  end_time, type `closed|group`, status
  `pending|confirmed|canceled|completed|blocked`, reason, total_price,
  customer_name/customer_phone para reserva manual) e `Payment` (referência
  polimórfica `booking|group_member`, valor, meio, status, split, refunded_at).
- `AvailabilityService.generate_slots(...)` como **função pura testável** + rota
  `GET /api/courts/{id}/availability?date=` retornando slots
  `free|busy|open_group` exatamente como especificado na seção 2.5 do doc de API.
- `POST /api/bookings` (tipo `closed` nesta fase): transação com lock
  (`SELECT ... FOR UPDATE` na court) + validação de sobreposição
  (seção 4.1 do doc de API) → `SLOT_UNAVAILABLE` em conflito. Preço calculado no
  servidor (`base_price_hour × duração`), nunca vindo do cliente.
- `POST /api/payments/{id}/confirm` (simulador de gateway — seção 2.8): aprovação
  grava split e confirma o booking; recusa cancela; **idempotente**.
- Expiração preguiçosa de `pending` (TTL 15 min) nas checagens de disponibilidade.
- `GET /api/bookings/{id}`, `GET /api/users/me/bookings?escopo=`,
  `POST /api/bookings/{id}/cancel` com política de reembolso (seção 3.5).
- **Atenção ao padrão de transação**: o `BaseRepository.save()` commita a cada
  chamada. Operações multi-entidade (booking+payment, cadeias de efeitos) precisam
  de transação única — adicione ao repositório/serviço um caminho de trabalho em
  transação (ex.: métodos `add` sem commit + commit no fim do service) sem quebrar
  os usos existentes.

#### Fase C — Grupos abertos (plano: fase 4) ⚠️ diferencial do produto

- Entidades + migração: `OpenGroup` (booking_id, total_spots, min_spots,
  spot_price, visibility `public|link`, closing_deadline, leftover_rule,
  status `open|full|confirmed|canceled`) e `GroupMember` (group_id, user_id,
  payment_id, status `confirmed|left`, joined_at).
- `POST /api/bookings` com `type=group`: cria booking + group + member do criador +
  payment da cota **na mesma transação**. Validar `total_spots ≤ capacity`,
  `min_spots ≤ total_spots`; cota = `ceil(total / spots)` em centavos.
- `GET /api/groups` (busca "jogos precisando de gente": filtros geo/esporte/data,
  só `open` + `public` com prazo futuro), `GET /api/groups/{id}` (funciona para
  `link` — o id é o convite), `POST /api/groups/{id}/join` (lock do grupo, vaga
  reservada por pendente válido, `GROUP_FULL`/`ALREADY_MEMBER`),
  `POST /api/groups/{id}/leave` (reembolso conforme prazo, vaga reabre,
  `full` regride para `open`).
- Efeitos em cadeia no pagamento da cota: aprovado → member confirmado → se lotou:
  group `full` + booking `confirmed` + notificações.
- `GroupService.process_deadline(group)` idempotente (confirmação com mínimo OK
  aplicando `leftover_rule` conforme decisão da seção 3.4 do doc de API;
  cancelamento com estorno de todas as cotas e liberação do horário).
- Slot `open_group` na disponibilidade (com dados do grupo embutidos).

#### Fase D — Painel do estabelecimento (plano: fase 5)

- `GET /api/companies/me/schedule?date=` — grade do dia de todas as courts com
  bookings ativos, dados do cliente e do grupo (uma chamada monta a tela).
- Bloqueios: `POST /api/courts/{id}/blocks` (booking `blocked` + reason, mesma
  validação de exclusividade) e `DELETE /api/bookings/{id}/block`.
- Reserva manual: `POST /api/companies/me/manual-bookings` (nasce `confirmed`,
  sem payment, customer_name/phone livres).
- Cancelamento pelo estabelecimento: reuso do cancel com estorno integral em cadeia
  (inclusive grupo inteiro).
- `GET /api/companies/me/report?from=&to=` — ocupação, receita confirmada, picos.

#### Fase E — Notificações + job (plano: fase 6)

- Entidade + migração: `Notification` (user_id, type, title, body, reference_type,
  reference_id, read).
- `NotificationService.create(...)` chamado pelos services nos eventos: reserva
  confirmada, entrou/saiu do grupo, grupo completo, jogo confirmado, risco de
  cancelamento, grupo cancelado, lembrete.
- Rotas: `GET /api/notifications?apenas_nao_lidas=` e `POST /api/notifications/read`
  (`{ids: []}` ou `{all: true}`).
- **Job**: loop asyncio no lifespan do app (60s) chamando `process_pending()`:
  expira pendentes → processa prazos de grupo → marca `confirmed → completed` de
  horários passados → notificações de risco/lembrete. Cada passo idempotente.

#### Fase F — Avaliações + seed de demo (plano: fase 7)

- Entidade + migração: `Review` (company_id, booking_id, user_id, rating 1–5,
  comment, helpful_count). Travas: booking `completed` + usuário jogou (criador ou
  member confirmado) + uma review por usuário/booking.
- Rotas: `POST /api/bookings/{id}/reviews`, `GET /api/companies/{id}/reviews`
  (paginada), `POST /api/reviews/{id}/helpful`. Nota média agregada nos cards da
  busca e no detalhe da company.
- **Seed de demo** (flag `SEED_DEMO`): 3–4 companies geolocalizadas próximas entre
  si, courts com fotos pequenas, bookings variados, 2 grupos abertos com vagas,
  reviews — idempotente (rodar duas vezes não duplica).

### 5. Regras de trabalho

- **Siga o gabarito**: controller fino com `Response[...]` + `HttpCode`, service com
  factory `get_service`, repository herdando `BaseRepository` (declare
  `orderable_fields`/`equal_filters`/`like_filters` quando a listagem pedir),
  exceções sempre via `DomainException` + `ErrorCode`. Nada de regra de negócio em
  controller; nada de query solta em service.
- **Máquinas de estado explícitas**: transições válidas por entidade num dict
  `de → {para}` no service; transição inválida → `INVALID_STATE`. As máquinas estão
  desenhadas no `modelo-de-dominio.md`.
- **Testes com pytest + TestClient** (crie a base de testes se ainda não houver,
  com banco descartável): priorize exclusividade de horário (corrida pelo mesmo
  slot → um leva `SLOT_UNAVAILABLE`), TTL de pendente, cadeia de aprovação de
  pagamento, grupos (última vaga, completo, prazo com/sem mínimo + estornos,
  sair antes/depois do prazo), idempotência do job. CRUDs simples não precisam de
  teste.
- **Uma migração Alembic por fase**, testada com upgrade a partir do banco da fase
  anterior.
- **Commits por fase** (ou menores), mensagens no padrão do histórico
  (`feat: ...`). Não commitar `.env`.
- **Não refatore o que existe** além do necessário (exceção única: o caminho de
  transação da Fase B). Não adicione dependências novas sem necessidade real —
  o job usa asyncio puro, sem Celery/Redis/APScheduler.
- Rode o app (docker-compose dev) e confira o Swagger `/docs` ao fim de cada fase;
  os exemplos dos DTOs devem deixar o Swagger utilizável como demo.

### 6. Critério de pronto (geral)

O MVP está pronto quando este roteiro roda de ponta a ponta só pelo Swagger:
registrar user → registrar company + court → buscar companies por localização →
ver disponibilidade → criar booking fechado → confirmar pagamento → aparecer na
agenda da company; criar booking `group` → segundo user entra e paga cota → grupo
lota → todos notificados; um grupo com prazo vencido sem mínimo é cancelado pelo
job com estornos; booking passado vira `completed` e aceita review que aparece na
média da busca. Tudo isso com os testes da seção 5 verdes.
