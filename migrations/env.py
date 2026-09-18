"""
Alembic migration environment configuration for TrustMoss.
Resolves the database DSN via the TrustMoss secret provider (Vault | AWS | ENV).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─────────────────────────────────────────────────────────────────────────────
# Alembic Config
# ─────────────────────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add apps/api to path for TrustMoss imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ─────────────────────────────────────────────────────────────────────────────
# Resolve Database URL via TrustMoss Secret Provider
# ─────────────────────────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from secret_manager import get_secret as _get_secret
except ImportError:
    _get_secret = lambda k, d=None: os.getenv(k, d)  # noqa: E731

_dsn = (
    _get_secret("POSTGRES_DSN")
    or os.getenv("POSTGRES_DSN", "postgresql://trustmoss:trustmoss@localhost:5432/trustmoss")
)
# Alembic requires postgresql+psycopg2 style DSN for synchronous offline runs
_sync_dsn = _dsn.replace("postgresql+asyncpg://", "postgresql://").replace(
    "postgresql://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", _sync_dsn)

# target_metadata: import your models here when using autogenerate
target_metadata = None


# ─────────────────────────────────────────────────────────────────────────────
# Offline Migration (generates SQL without connecting to DB)
# ─────────────────────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ─────────────────────────────────────────────────────────────────────────────
# Online Migration (connects to DB and runs in transaction)
# ─────────────────────────────────────────────────────────────────────────────
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
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
