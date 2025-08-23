# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dados_patu.db")
connect_args = {}

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    # O Render não exige SSL para conexões internas, mas pode exigir para externas.
    # Esta abordagem é mais segura.
    connect_args["ssl"] = "require"

engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
