# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse, parse_qsl, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dados_patu.db")
connect_args = {}

# Lógica para lidar com a base de dados de produção (Neon/PostgreSQL)
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Substituímos o protocolo para usar o driver asyncpg
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Esta parte resolve o erro do 'sslmode'
    parsed_url = urlparse(DATABASE_URL)
    query_params = dict(parse_qsl(parsed_url.query))
    
    if 'sslmode' in query_params:
        # Passamos o ssl como um argumento de conexão separado
        connect_args["ssl"] = "require"
        
        # Removemos o sslmode da URL para evitar o erro
        # (Reconstruímos a URL sem os parâmetros de query)
        DATABASE_URL = urlunparse(parsed_url._replace(query=""))

# Criamos o motor da base de dados com os argumentos corretos
engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
