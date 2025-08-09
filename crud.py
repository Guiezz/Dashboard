# crud.py (VERSÃO COM CORREÇÃO FINAL NO CÁLCULO DE ESTADO)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import pandas as pd
import numpy as np

import models
import schemas


# (As primeiras funções permanecem exatamente iguais)
async def get_identificacao(db: AsyncSession) -> Optional[models.Identificacao]:
    result = await db.execute(select(models.Identificacao).limit(1))
    return result.scalars().first()


async def get_balanco_mensal(db: AsyncSession) -> List[models.BalancoMensal]:
    result = await db.execute(select(models.BalancoMensal))
    return result.scalars().all()


async def get_composicao_demanda(db: AsyncSession) -> List[models.ComposicaoDemanda]:
    result = await db.execute(select(models.ComposicaoDemanda))
    return result.scalars().all()


async def get_oferta_demanda(db: AsyncSession) -> List[models.OfertaDemanda]:
    result = await db.execute(select(models.OfertaDemanda))
    return result.scalars().all()


async def get_action_plan_filters(db: AsyncSession) -> schemas.ActionPlanFilterOptions:
    query_estados = select(models.PlanoAcao.estado_seca).distinct()
    query_impactos = select(models.PlanoAcao.tipos_impactos).distinct()
    query_problemas = select(models.PlanoAcao.problemas).distinct()
    query_acoes = select(models.PlanoAcao.acoes).distinct()
    estados_res = await db.execute(query_estados)
    impactos_res = await db.execute(query_impactos)
    problemas_res = await db.execute(query_problemas)
    acoes_res = await db.execute(query_acoes)
    return schemas.ActionPlanFilterOptions(
        estados_de_seca=sorted([r for r, in estados_res if r]),
        tipos_de_impacto=sorted([r for r, in impactos_res if r]),
        problemas=sorted([r for r, in problemas_res if r]),
        acoes=sorted([r for r, in acoes_res if r]),
    )


async def get_action_plans(db: AsyncSession, estado: Optional[str] = None, impacto: Optional[str] = None,
                           problema: Optional[str] = None, acao: Optional[str] = None,
                           situacao: Optional[str] = None) -> List[models.PlanoAcao]:
    query = select(models.PlanoAcao)
    if estado: query = query.where(models.PlanoAcao.estado_seca == estado)
    if impacto: query = query.where(models.PlanoAcao.tipos_impactos == impacto)
    if problema: query = query.where(models.PlanoAcao.problemas == problema)
    if acao: query = query.where(models.PlanoAcao.acoes == acao)
    if situacao: query = query.where(models.PlanoAcao.situacao == situacao)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_monitoring_data(db: AsyncSession) -> List[models.Monitoramento]:
    result = await db.execute(select(models.Monitoramento).order_by(models.Monitoramento.data))
    return result.scalars().all()


async def get_all_volume_meta(db: AsyncSession) -> List[models.VolumeMeta]:
    result = await db.execute(select(models.VolumeMeta))
    return result.scalars().all()

async def get_usos_agua(db: AsyncSession) -> List[models.UsoAgua]:
    result = await db.execute(select(models.UsoAgua))
    return result.scalars().all()


# --- FUNÇÃO CORRIGIDA ABAIXO ---
async def get_history_with_status(db: AsyncSession) -> pd.DataFrame:
    #Busca todos os dados de monitoramento e metas
    monitoramento_data = await get_all_monitoring_data(db)
    metas_data = await get_all_volume_meta(db)

    if not monitoramento_data:
        return pd.DataFrame()

    df_monitoramento = pd.DataFrame([m.__dict__ for m in monitoramento_data])
    df_metas = pd.DataFrame([m.__dict__ for m in metas_data])

    if df_monitoramento.empty or df_metas.empty:
        return df_monitoramento

    df_monitoramento['mes_num'] = pd.to_datetime(df_monitoramento['data']).dt.month
    df_merged = pd.merge(df_monitoramento, df_metas, on='mes_num', how='left')

    # --- CORREÇÃO FINAL: Normalizar o valor percentual antes de comparar ---
    # Garante que a coluna não tem valores nulos ou não numéricos antes da divisão
    df_merged['volume_percentual'] = pd.to_numeric(df_merged['volume_percentual'], errors='coerce').fillna(0) / 100

    conditions = [
        (df_merged['volume_percentual'] < df_merged['meta1v']),
        (df_merged['volume_percentual'] < df_merged['meta2v']),
        (df_merged['volume_percentual'] < df_merged['meta3v'])
    ]
    choices = ["SECA SEVERA", "SECA", "ALERTA"]
    df_merged['estado_calculado'] = np.select(conditions, choices, default='NORMAL')

    return df_merged.sort_values(by='data', ascending=False)