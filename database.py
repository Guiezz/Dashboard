# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base # <-- LINHA CORRIGIDA
from urllib.parse import urlparse, parse_qsl, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dados_patu.db")
connect_args = {}

# Lógica para lidar com a base de dados de produção (Neon/PostgreSQL)
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed_url = urlparse(DATABASE_URL)
    query_params = dict(parse_qsl(parsed_url.query))

    if 'sslmode' in query_params:
        connect_args["ssl"] = "require"
        DATABASE_URL = urlunparse(parsed_url._replace(query=""))

engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
