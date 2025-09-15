# crud.py (VERSÃO FINAL MULTI-RESERVATÓRIO)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import pandas as pd
import numpy as np

import models


# --- NOVA FUNÇÃO ---
async def get_reservatorios(db: AsyncSession) -> List[models.Reservatorio]:
    """Busca uma lista de todos os reservatórios disponíveis."""
    result = await db.execute(select(models.Reservatorio).order_by(models.Reservatorio.nome))
    return result.scalars().all()


# --- FUNÇÕES ATUALIZADAS PARA FILTRAR POR reservatorio_id ---

async def get_identificacao(db: AsyncSession, reservatorio_id: int) -> Optional[models.Reservatorio]:
    result = await db.execute(select(models.Reservatorio).where(models.Reservatorio.id == reservatorio_id))
    return result.scalars().first()


async def get_balanco_mensal(db: AsyncSession, reservatorio_id: int) -> List[models.BalancoMensal]:
    result = await db.execute(
        select(models.BalancoMensal).where(models.BalancoMensal.reservatorio_id == reservatorio_id))
    return result.scalars().all()


async def get_composicao_demanda(db: AsyncSession, reservatorio_id: int) -> List[models.ComposicaoDemanda]:
    result = await db.execute(
        select(models.ComposicaoDemanda).where(models.ComposicaoDemanda.reservatorio_id == reservatorio_id))
    return result.scalars().all()


async def get_oferta_demanda(db: AsyncSession, reservatorio_id: int) -> List[models.OfertaDemanda]:
    result = await db.execute(
        select(models.OfertaDemanda).where(models.OfertaDemanda.reservatorio_id == reservatorio_id))
    return result.scalars().all()


async def get_usos_agua(db: AsyncSession, reservatorio_id: int) -> List[models.UsoAgua]:
    result = await db.execute(select(models.UsoAgua).where(models.UsoAgua.reservatorio_id == reservatorio_id))
    return result.scalars().all()


async def get_responsaveis(db: AsyncSession, reservatorio_id: int) -> List[models.Responsavel]:
    result = await db.execute(
        select(models.Responsavel)
        .where(models.Responsavel.reservatorio_id == reservatorio_id)
        .order_by(
            models.Responsavel.grupo,
            models.Responsavel.organizacao,
            models.Responsavel.nome
        )
    )
    return result.scalars().all()


# Arquivo: crud.py

async def get_action_plans(db: AsyncSession, reservatorio_id: int, estado: Optional[str] = None,
                           impacto: Optional[str] = None, problema: Optional[str] = None, acao: Optional[str] = None,
                           situacao: Optional[str] = None) -> List[models.PlanoAcao]:
    query = select(models.PlanoAcao).where(models.PlanoAcao.reservatorio_id == reservatorio_id)

    if estado:
        query = query.where(models.PlanoAcao.estado_seca == estado)

    if impacto:
        query = query.where(models.PlanoAcao.tipos_impactos == impacto)

    if problema:
        query = query.where(models.PlanoAcao.problemas == problema)

    if acao:
        query = query.where(models.PlanoAcao.acoes == acao)

    if situacao:
        query = query.where(models.PlanoAcao.situacao == situacao)

    result = await db.execute(query)
    return result.scalars().all()

# Arquivo: crud.py

async def get_action_plan_filters(db: AsyncSession, reservatorio_id: int) -> dict:
    query = select(
        models.PlanoAcao.estado_seca,
        models.PlanoAcao.tipos_impactos,
        models.PlanoAcao.problemas,
        models.PlanoAcao.acoes
    ).where(models.PlanoAcao.reservatorio_id == reservatorio_id).distinct()

    result = await db.execute(query)
    records = result.all()

    estados = sorted(list(set([r.estado_seca for r in records if r.estado_seca])))
    impactos = sorted(list(set([r.tipos_impactos for r in records if r.tipos_impactos])))
    problemas = sorted(list(set([r.problemas for r in records if r.problemas])))
    acoes = sorted(list(set([r.acoes for r in records if r.acoes])))

    return {
        "estados": estados,
        "impactos": impactos,
        "problemas": problemas,
        "acoes": acoes,
    }

async def get_all_monitoring_data(db: AsyncSession, reservatorio_id: int) -> List[models.Monitoramento]:
    result = await db.execute(
        select(models.Monitoramento).where(models.Monitoramento.reservatorio_id == reservatorio_id).order_by(
            models.Monitoramento.data))
    return result.scalars().all()


async def get_all_volume_meta(db: AsyncSession, reservatorio_id: int) -> List[models.VolumeMeta]:
    result = await db.execute(select(models.VolumeMeta).where(models.VolumeMeta.reservatorio_id == reservatorio_id))
    return result.scalars().all()

async def get_reservatorio_by_id(db: AsyncSession, reservatorio_id: int) -> Optional[models.Reservatorio]:
    """Busca um reservatório específico pelo seu ID primário para obter detalhes como o código da FUNCEME."""
    query = select(models.Reservatorio).where(models.Reservatorio.id == reservatorio_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_history_with_status(db: AsyncSession, reservatorio_id: int) -> pd.DataFrame:
    monitoramento_data = await get_all_monitoring_data(db, reservatorio_id)
    metas_data = await get_all_volume_meta(db, reservatorio_id)

    if not monitoramento_data or not metas_data:
        return pd.DataFrame()

    df_monitoramento = pd.DataFrame([m.__dict__ for m in monitoramento_data])
    df_metas = pd.DataFrame([m.__dict__ for m in metas_data])

    if df_monitoramento.empty or df_metas.empty:
        return df_monitoramento

    df_monitoramento['mes_num'] = pd.to_datetime(df_monitoramento['data']).dt.month
    df_merged = pd.merge(df_monitoramento, df_metas, on='mes_num', how='left')

    df_merged['volume_percentual'] = pd.to_numeric(df_merged['volume_percentual'], errors='coerce').fillna(0) / 100
    conditions = [
        (df_merged['volume_percentual'] < df_merged['meta1v']),
        (df_merged['volume_percentual'] < df_merged['meta2v']),
        (df_merged['volume_percentual'] < df_merged['meta3v'])
    ]
    choices = ["SECA SEVERA", "SECA", "ALERTA"]
    df_merged['estado_calculado'] = np.select(conditions, choices, default='NORMAL')

    return df_merged.sort_values(by='data', ascending=False)
