import asyncio
from pathlib import Path

import asyncpg

from app.config import settings


def _asyncpg_dsn(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    return database_url


async def run_migrations() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"No migration files found in {migrations_dir}")

    conn = await asyncpg.connect(_asyncpg_dsn(settings.DATABASE_URL))
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        for migration_file in migration_files:
            already_applied = await conn.fetchval(
                "SELECT 1 FROM schema_migrations WHERE filename = $1",
                migration_file.name,
            )
            if already_applied:
                print(f"Skipping {migration_file.name}", flush=True)
                continue

            sql = migration_file.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            print(f"Applying {migration_file.name}", flush=True)
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)",
                    migration_file.name,
                )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
