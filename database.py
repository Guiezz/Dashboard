# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Pega a URL do banco de dados de uma variável de ambiente.
# Se não encontrar, usa o SQLite local como padrão.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dados_patu.db")

# Adicione esta verificação para ajustar a URL em produção
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session