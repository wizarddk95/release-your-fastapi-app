import asyncio

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.engine import Connection

from alembic import context

from appserver.apps.account import models # 4
from appserver.apps.calendar import models # 4
from sqlmodel import SQLModel # 1
from appserver.db import DSN # 2

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata # 3

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# ==== 기존 마이그레이션 처리 함수 ====
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# ==== 비동기로 동작하는 수행 함수 추가 ====
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {}) # alembic.ini 설정 로드
    configuration["sqlalchemy.url"] = DSN # DB URL을 동기 URL이 아닌 async DNS으로 교체

    connectable = AsyncEngine( # 아래 동기 Engine을 비동기 래퍼로 감쌈
        engine_from_config( # 동기 Engine 생성 ↑
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    async with connectable.connect() as connection: # 비동기 커넥션 획득 → event loop를 block하지 않음
        await connection.run_sync(do_run_migrations) # 비동기 맥락(context)에서 do_run_migrations() 실행
    await connectable.dispose()


# ==== 기존 로직에 asyncio.run() 추가 ====
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())


