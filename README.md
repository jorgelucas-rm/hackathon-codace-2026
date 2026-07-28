# Reservaê

🥇 **Projeto vencedor do 1º Hackathon da Coda.ce**

Reservaê é um Hub que conecta pessoas que querem praticar esportes — como
Beach Tênis, Vôlei e Futevôlei — às arenas e estabelecimentos que oferecem
quadras para locação.

Pela plataforma, o usuário se cadastra, descobre as arenas mais próximas,
filtra por modalidade e horário, visualiza o perfil de cada espaço e
finaliza o agendamento em poucos cliques, eliminando a demora e a
burocracia de negociar reservas manualmente por WhatsApp ou telefone.

Para as arenas, o Reservaê funciona como uma plataforma completa de vendas,
com gestão de quadras, agendamentos e pagamentos integrados em um só
lugar. Estabelecimentos que buscam ir além também podem contar com o plano
Premium, que inclui gestão financeira e inteligência de dados baseada no
perfil de consumo dos atletas da região, ajudando as arenas a entender
melhor seu público e tomar decisões mais estratégicas.

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React, TypeScript
- **Armazenamento de arquivos**: MinIO (S3-compatible)
- **Infra**: Docker / Docker Compose

## Estrutura do repositório

```
.
├── backend/    # API (FastAPI)
├── frontend/   # SPA (React)
├── docs/       # Documentação de domínio, API e planejamento
├── docker-compose.dev.yml   # ambiente de desenvolvimento
└── docker-compose.yml       # ambiente de produção
```

## Pré-requisitos

- Docker e Docker Compose
- Um arquivo `.env` em `backend/src/environments/.env` com as variáveis
  abaixo (usadas pelo backend, pelo Postgres e pelo MinIO):

  ```
  # Segurança
  JWT_SECRET=
  JWT_ALGORITHM=
  JWT_TOKEN_EXPIRE=

  # Banco de dados
  DATABASE_HOST=
  DATABASE_PORT=
  POSTGRES_DB=
  POSTGRES_USER=
  POSTGRES_PASSWORD=

  # Frontend
  FRONTEND_URL=

  # MinIO
  MINIO_HOST=
  MINIO_ROOT_USER=
  MINIO_ROOT_PASSWORD=
  MINIO_SECURE=
  MINIO_DEFAULT_BUCKET=
  MINIO_PUBLIC_HOST=
  MINIO_PUBLIC_SECURE=
  ```

## Rodando em desenvolvimento

O ambiente de dev sobe os serviços com hot-reload (bind mount do código-fonte).

```bash
docker compose -f docker-compose.dev.yml up --build
```

Serviços expostos:

| Serviço       | URL                     |
| ------------- | ----------------------- |
| Frontend      | <http://localhost:8080> |
| Backend       | <http://localhost:8081> |
| Database      | localhost:5432          |
| MinIO API     | <http://localhost:9000> |
| MinIO Console | <http://localhost:9001> |

Alterações em `backend/` e `frontend/` são refletidas automaticamente nos
containers (sem precisar rebuildar a imagem).

## Rodando em produção

O ambiente de produção builda as imagens de `backend` e `frontend` (sem
bind mount de código) e persiste os dados de `database` e `minio` em
caminhos fixos no host.

```bash
docker compose up -d --build
```

Serviços expostos:

| Serviço       | URL                     |
| ------------- | ----------------------- |
| Frontend      | <http://localhost:8080> |
| Backend       | <http://localhost:8081> |
| Database      | localhost:5433          |
| MinIO API     | <http://localhost:9000> |
| MinIO Console | <http://localhost:9001> |

> Os volumes de `database` e `minio` apontam para
> `/data/projects/reservae/database` e `/data/projects/reservae/minio` no
> host — garanta que esses diretórios existam (e tenham permissão de
> escrita) antes de subir o ambiente.

## Time

| Nome            | Papel                  | GitHub          |
| --------------- | ---------------------- | --------------- |
| Gisele Alencar  | Designer               | @Gisele-Alencar |
| Guilherme Lemos | Analista de Negócios   | @Guilhermnxs    |
| Jorge Lucas     | Desenvolvedor Backend  | @jorgelucas-rm  |
| Luan Kaio       | DevOps                 | @Luankaio       |
| Matheus Batista | Desenvolvedor Frontend | @matheustsx     |
