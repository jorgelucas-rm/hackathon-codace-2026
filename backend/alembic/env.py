from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from src.app.model.entity import BaseModel
from src.app.model.enum.int_enum_type import IntEnumType
from src.environments import DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseModel.metadata

config.set_main_option("sqlalchemy.url", DATABASE_URL)


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        info = getattr(object, "info", {})
        if info.get("is_view") or info.get("is_foreign"):
            return False
    return True


def render_item(type_, obj, autogen_context):
    """Renderiza IntEnumType (TypeDecorator) como sa.Integer() puro nas migrations.

    Sem isso, autogenerate emite o caminho totalmente qualificado da classe
    (ex.: src.app.model.enum.int_enum_type.IntEnumType()) sem importá-la,
    quebrando a migration gerada. A coluna no banco é sempre um inteiro — a
    coerção para o enum é responsabilidade da camada de ORM/aplicação.
    """
    if type_ == "type" and isinstance(obj, IntEnumType):
        autogen_context.imports.add("import sqlalchemy as sa")
        return "sa.Integer()"
    return False


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
