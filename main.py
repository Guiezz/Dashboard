# main.py (VERSÃO COM CORREÇÃO DE IMPORT)

import numpy as np
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# --- CORREÇÃO: Removida a importação direta de 'select' do numpy ---
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import httpx
from datetime import date
import pandas as pd
from contextlib import asynccontextmanager
import os
from fastapi.staticfiles import StaticFiles
# --- CORREÇÃO: Importação explícita do select do SQLAlchemy ---
from sqlalchemy import select

# Importações locais
import models
import schemas
import crud
from database import engine, get_db


# --- Evento de Inicialização e Finalização da API ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    print("Aplicação iniciada e tabelas verificadas.")
    yield
    print("Finalizando a aplicação...")


app = FastAPI(
    title="API de Monitoramento da Seca - Patu",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- ENDPOINTS DA API ---

@app.get("/")
def read_root():
    return {"status": "API de Monitoramento da Seca está online e conectada ao banco de dados."}


@app.get("/api/identification", response_model=schemas.Identificacao)
async def get_identification_data(db: AsyncSession = Depends(get_db)):
    identificacao = await crud.get_identificacao(db)
    if not identificacao:
        raise HTTPException(status_code=404, detail="Dados de identificação não encontrados.")

    url_base = "http://127.0.0.1:8000/static/images"
    url_imagem_vista = f"{url_base}/{identificacao.nome_imagem}" if identificacao.nome_imagem else None
    url_imagem_usos = f"{url_base}/{identificacao.nome_imagem_usos}" if identificacao.nome_imagem_usos else None

    response_data = schemas.Identificacao.model_validate(identificacao)
    response_data.url_imagem = url_imagem_vista
    response_data.url_imagem_usos = url_imagem_usos
    return response_data


@app.get("/api/usos-agua", response_model=List[schemas.UsoAgua])
async def get_usos_agua(db: AsyncSession = Depends(get_db)):
    return await crud.get_usos_agua(db)


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    historico_com_estado = await crud.get_history_with_status(db)
    if historico_com_estado.empty:
        raise HTTPException(status_code=404, detail="Dados de monitoramento não disponíveis.")

    ultimo_registro = historico_com_estado.iloc[0]
    estado_atual = ultimo_registro['estado_calculado']
    data_atual = ultimo_registro['data']

    historico_anterior = historico_com_estado[historico_com_estado['estado_calculado'] != estado_atual]

    if not historico_anterior.empty:
        data_da_mudanca = historico_anterior.iloc[0]['data']
        dias_desde_ultima_mudanca = (data_atual - data_da_mudanca).days
    else:
        data_mais_antiga = historico_com_estado.iloc[-1]['data']
        dias_desde_ultima_mudanca = (data_atual - data_mais_antiga).days

    medidas = await crud.get_action_plans(db, estado=estado_atual)

    medidas_formatadas = [{"Ação": m.acoes, "Descrição": m.descricao_acao, "Responsáveis": m.responsaveis} for m in
                          medidas]

    return {
        "volumeAtualHm3": ultimo_registro.get("volume_hm3", 0),
        "volumePercentual": ultimo_registro.get("volume_percentual", 0),
        "estadoAtualSeca": estado_atual,
        "dataUltimaMedicao": data_atual,
        "diasDesdeUltimaMudanca": dias_desde_ultima_mudanca,
        "medidasRecomendadas": medidas_formatadas
    }

@app.get("/api/history")
async def get_history_data(db: AsyncSession = Depends(get_db)):
    historico_com_estado = await crud.get_history_with_status(db)

    if historico_com_estado.empty:
        return []

    # A função get_history_with_status() já retorna os dados ordenados do mais novo para o mais antigo.
    # O seu frontend espera que o JSON tenha chaves específicas, então vamos formatar a saída.

    df_formatado = historico_com_estado.copy()

    df_formatado.rename(columns={
        'data': 'Data',
        'estado_calculado': 'Estado de Seca',
        'volume_hm3': 'Volume (Hm³)'
    }, inplace=True)

    df_formatado['Data'] = pd.to_datetime(df_formatado['Data']).dt.strftime('%d/%m/%Y')

    return df_formatado[['Data', 'Estado de Seca', 'Volume (Hm³)']].to_dict('records')


@app.get("/api/chart/volume-data")
async def get_chart_data(db: AsyncSession = Depends(get_db)):
    monitoramento_data = await crud.get_all_monitoring_data(db)
    metas_data = await crud.get_all_volume_meta(db)

    if not monitoramento_data: return []

    df_monitoramento = pd.DataFrame([m.__dict__ for m in monitoramento_data])
    df_metas = pd.DataFrame([m.__dict__ for m in metas_data])

    if df_monitoramento.empty or df_metas.empty: return []

    df_monitoramento['mes_num'] = pd.to_datetime(df_monitoramento['data']).dt.month
    df_merged = pd.merge(df_monitoramento, df_metas, on='mes_num', how='left')

    df_merged.rename(
        columns={'data': 'Data', 'volume_hm3': 'volume', 'meta1v': 'meta1', 'meta2v': 'meta2', 'meta3v': 'meta3'},
        inplace=True)
    df_merged['Data'] = pd.to_datetime(df_merged['Data']).dt.strftime('%Y-%m-%d')

    return df_merged[['Data', 'volume', 'meta1', 'meta2', 'meta3']].to_dict('records')


@app.get("/api/ongoing-actions")
async def get_ongoing_actions(db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, situacao="Em andamento")
    return [{"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao} for a in acoes]


@app.get("/api/completed-actions")
async def get_completed_actions(db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, situacao="Concluído")
    return [{"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao} for a in acoes]


@app.get("/api/action-plans/filters", response_model=schemas.ActionPlanFilterOptions)
async def get_action_plan_filters(db: AsyncSession = Depends(get_db)):
    return await crud.get_action_plan_filters(db)


@app.get("/api/action-plans")
async def get_action_plans(estado: Optional[str] = None, impacto: Optional[str] = None, problema: Optional[str] = None,
                           acao: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    planos = await crud.get_action_plans(db, estado, impacto, problema, acao)
    return [{"DESCRIÇÃO DA AÇÃO": p.descricao_acao, "CLASSES DE AÇÃO": p.classes_acao, "RESPONSÁVEIS": p.responsaveis}
            for p in planos]


@app.get("/api/water-balance/static-charts")
async def get_static_balance_charts(db: AsyncSession = Depends(get_db)):
    balanco_mensal_data = await crud.get_balanco_mensal(db)
    composicao_demanda_data = await crud.get_composicao_demanda(db)
    oferta_demanda_data = await crud.get_oferta_demanda(db)

    balanco_formatado = [
        {"Mês": bm.mes, "Afluência (m³/s)": float(bm.afluencia_m3s) if bm.afluencia_m3s is not None else 0,
         "Demanda (m³/s)": float(bm.demandas_m3s) if bm.demandas_m3s is not None else 0,
         "Balanço (m³/s)": float(bm.balanco_m3s) if bm.balanco_m3s is not None else 0,
         "Evaporação (m³/s)": float(bm.evaporacao_m3s) if hasattr(bm,
                                                                  'evaporacao_m3s') and bm.evaporacao_m3s is not None else 0}
        for bm in balanco_mensal_data]
    composicao_formatada = [
        {"Uso": cd.usos, "Vazão (L/s)": float(cd.demandas_hm3) if cd.demandas_hm3 is not None else 0} for cd in
        composicao_demanda_data]
    oferta_formatada = [
        {"Cenário": od.cenarios, "Oferta (L/s)": float(od.oferta_m3s) if od.oferta_m3s is not None else 0,
         "Demanda (L/s)": float(od.demanda_m3s) if od.demanda_m3s is not None else 0} for od in oferta_demanda_data]

    return {"balancoMensal": balanco_formatado, "composicaoDemanda": composicao_formatada,
            "ofertaDemanda": oferta_formatada}


@app.post("/api/update-funceme-data")
async def update_funceme_data(db: AsyncSession = Depends(get_db)):
    print("📡 Buscando dados históricos da API da FUNCEME...")
    hoje = date.today().strftime("%Y-%m-%d")
    url_funceme = f"https://apil5.funceme.br/rpc/v1/reservatorio-series?reservatorio_id=10&data_inicio=2023-01-01&data_fim={hoje}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_funceme, timeout=30.0)
            response.raise_for_status()
            dados_funceme_raw = response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Erro de conexão ao buscar dados da FUNCEME: {e}")

    dados_reais = dados_funceme_raw.get('data', {}).get('list', [])
    if not dados_reais:
        return {"status": "A API da FUNCEME não retornou novos dados."}

    existing_dates_query = await db.execute(select(models.Monitoramento.data))
    existing_dates = {d for d, in existing_dates_query}

    novos_registros = []
    for registro in dados_reais:
        data_registro = date.fromisoformat(registro['data'])
        if data_registro not in existing_dates:
            novos_registros.append(models.Monitoramento(
                data=data_registro,
                volume_hm3=registro.get('volume'),
                volume_percentual=registro.get('volume_perc')
            ))

    if novos_registros:
        db.add_all(novos_registros)
        await db.commit()
        return {"status": f"{len(novos_registros)} novos registros de monitoramento foram adicionados."}

    return {"status": "Nenhum registro novo para adicionar. O banco de dados já está atualizado."}