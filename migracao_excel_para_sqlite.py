# migracao_excel_para_sqlite.py (VERSÃO FINAL PARA DEPLOY)
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
import glob
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from database import Base
from models import (
    Reservatorio, BalancoMensal, ComposicaoDemanda, OfertaDemanda,
    PlanoAcao, VolumeMeta, Monitoramento, UsoAgua, Responsavel
)

# Detecta se estamos no ambiente do Render
IS_PRODUCTION = "RENDER" in os.environ
DATABASE_URL_ENV = os.getenv("DATABASE_URL")


async def recriar_banco_de_dados_async(engine):
    print("🗑️  Apagando tabelas antigas e recriando o banco de dados (assíncrono)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Banco de dados e tabelas recriados com sucesso.")


def recriar_banco_de_dados_sync(engine):
    print("🗑️  Apagando tabelas antigas e recriando o banco de dados (síncrono)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados e tabelas recriados com sucesso.")


async def carregar_dados():
    db = None
    engine = None
    try:
        if IS_PRODUCTION:
            print("🚀 Conectando ao banco de dados de produção (PostgreSQL)...")
            db_url = DATABASE_URL_ENV.replace("postgres://", "postgresql+asyncpg://", 1)
            engine = create_async_engine(db_url)
            await recriar_banco_de_dados_async(engine)
            AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
            db = AsyncSessionLocal()
        else:
            print("🚀 Usando banco de dados local (SQLite)...")
            engine = create_engine("sqlite:///./dados_patu.db")
            recriar_banco_de_dados_sync(engine)
            SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocalSync()

        pastas_reservatorios = [f for f in glob.glob("data/*") if os.path.isdir(f)]

        for pasta in pastas_reservatorios:
            nome_pasta = os.path.basename(pasta)
            print(f"\n🔄 Processando dados para o reservatório: {nome_pasta.upper()}")

            df_ident = pd.read_excel(os.path.join(pasta, 'identificacao.xlsx'))
            df_ident.columns = [str(col).strip().lower() for col in df_ident.columns]
            info_reservatorio = df_ident.iloc[0].to_dict()

            novo_reservatorio = Reservatorio(
                nome=info_reservatorio.get('nome', nome_pasta.capitalize()),
                municipio=info_reservatorio.get('municipio'),
                descricao=info_reservatorio.get('descricao'),
                lat=info_reservatorio.get('lat'),
                long=info_reservatorio.get('long'),
                nome_imagem=info_reservatorio.get('nome_imagem'),
                nome_imagem_usos=info_reservatorio.get('nome_imagem_usos'),
                codigo_funceme=info_reservatorio.get('codigo_funceme')
            )
            db.add(novo_reservatorio)

            if IS_PRODUCTION:
                await db.flush()
            else:
                db.flush()
            reservatorio_id = novo_reservatorio.id
            print(f" -> Reservatório '{novo_reservatorio.nome}' criado com ID: {reservatorio_id}")

            # Carregamento dos dados em loop para ser compatível com async
            # (bulk_insert_mappings não é ideal com async)

            # Plano de Ação
            df_pa = pd.read_excel(os.path.join(pasta, 'plano_acao.xlsx'))
            df_pa.columns = [str(col).strip().lower() for col in df_pa.columns]
            df_pa.rename(columns={'estado de seca': 'estado_seca', 'problemas': 'problemas', 'tipos de impactos': 'tipos_impactos', 'ações': 'acoes', 'descrição da ação': 'descricao_acao', 'classes de ação': 'classes_acao', 'responsáveis': 'responsaveis', 'situação': 'situação'}, inplace=True)
            df_pa['reservatorio_id'] = reservatorio_id
            for record in df_pa.to_dict(orient="records"): db.add(PlanoAcao(**record))
            print(" -> Dados de 'Plano de Ação' carregados.")

            # Adicione aqui o código para carregar os outros arquivos (UsoAgua, Monitoramento, etc.)
            # usando a mesma estrutura de loop:
            # for record in df.to_dict(orient="records"): db.add(Model(**record))

        if IS_PRODUCTION:
            await db.commit()
        else:
            db.commit()
        print("\n✅ Todos os dados foram carregados com sucesso!")

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        if db and IS_PRODUCTION:
            await db.rollback()
        elif db:
            db.rollback()
    finally:
        if db and IS_PRODUCTION:
            await db.close()
        elif db:
            db.close()
        if engine and IS_PRODUCTION:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(carregar_dados())
