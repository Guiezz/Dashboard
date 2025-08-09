# main.py (VERSÃO FINAL E CORRIGIDA)
import numpy as np
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from numpy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import httpx
from datetime import date
import pandas as pd
from contextlib import asynccontextmanager

# Importações locais
from utils import crud, models, schemas
from utils.database import engine, get_db


# --- Evento de Inicialização e Finalização da API ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado ANTES da aplicação iniciar
    print("Iniciando a aplicação...")
    async with engine.begin() as conn:
        # CORREÇÃO: Executa a criação de tabelas de forma assíncrona
        # await conn.run_sync(models.Base.metadata.drop_all) # Opcional: para limpar o banco a cada reinício
        await conn.run_sync(models.Base.metadata.create_all)
    print("Aplicação iniciada e tabelas verificadas.")
    yield
    # Código a ser executado DEPOIS da aplicação finalizar
    print("Finalizando a aplicação...")


# Cria a aplicação FastAPI com o evento de lifespan
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


# --- ENDPOINTS DA API (O restante do código permanece o mesmo) ---

@app.get("/")
def read_root():
    return {"status": "API de Monitoramento da Seca está online e conectada ao banco de dados."}


@app.get("/api/identification", response_model=schemas.Identificacao)
async def get_identification_data(db: AsyncSession = Depends(get_db)):
    identificacao = await crud.get_identificacao(db)
    if not identificacao:
        raise HTTPException(status_code=404, detail="Dados de identificação não encontrados.")
    return identificacao

@app.get("/api/dashboard/summary")  # Removido o response_model para controlo manual
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

    # --- Construção Manual da Resposta ---
    # Isto garante que as chaves são exatamente o que o frontend quer.
    medidas_formatadas = [
        {"Ação": m.acoes, "Descrição": m.descricao_acao, "Responsáveis": m.responsaveis}
        for m in medidas
    ]

    return {
        "volumeAtualHm3": ultimo_registro.get("volume_hm3", 0),
        "volumePercentual": ultimo_registro.get("volume_percentual", 0),
        "estadoAtualSeca": estado_atual,
        "dataUltimaMedicao": data_atual,
        "diasDesdeUltimaMudanca": dias_desde_ultima_mudanca,
        "medidasRecomendadas": medidas_formatadas
    }


# COLE ESTE NOVO ENDPOINT DENTRO DO SEU main.py

@app.get("/api/history")  # O endpoint que faltava
async def get_history_data(db: AsyncSession = Depends(get_db)):
    """
    Este endpoint retorna os dados combinados de monitoramento e metas,
    calculando o estado de seca para cada registro, ideal para tabelas de histórico.
    """
    monitoramento_data = await crud.get_all_monitoring_data(db)
    metas_data = await crud.get_all_volume_meta(db)

    if not monitoramento_data:
        return []

    df_monitoramento = pd.DataFrame([m.__dict__ for m in monitoramento_data])
    df_metas = pd.DataFrame([m.__dict__ for m in metas_data])

    if df_monitoramento.empty or df_metas.empty:
        return []

    df_monitoramento['mes_num'] = pd.to_datetime(df_monitoramento['data']).dt.month
    df_merged = pd.merge(df_monitoramento, df_metas, on='mes_num', how='left')

    # Calcula o Estado de Seca para cada linha
    conditions = [
        (df_merged['volume_percentual'] < df_merged['meta1v']),
        (df_merged['volume_percentual'] < df_merged['meta2v']),
        (df_merged['volume_percentual'] < df_merged['meta3v'])
    ]
    choices = ["SECA SEVERA", "SECA", "ALERTA"]
    df_merged['Estado de Seca'] = np.select(conditions, choices, default='NORMAL')

    # Renomeia as colunas para o formato esperado pelo frontend
    df_merged.rename(columns={
        'data': 'Data',
        'volume_hm3': 'Volume (Hm³)'
    }, inplace=True)
    df_merged['Data'] = pd.to_datetime(df_merged['Data']).dt.strftime('%d/%m/%Y')

    # Retorna apenas as colunas que o histórico precisa
    return df_merged[['Data', 'Estado de Seca', 'Volume (Hm³)']].to_dict('records')


@app.get("/api/chart/volume-data")
async def get_chart_data(db: AsyncSession = Depends(get_db)):
    monitoramento_data = await crud.get_all_monitoring_data(db)
    metas_data = await crud.get_all_volume_meta(db)

    if not monitoramento_data:
        return []

    df_monitoramento = pd.DataFrame([m.__dict__ for m in monitoramento_data])
    df_metas = pd.DataFrame([m.__dict__ for m in metas_data])

    if df_monitoramento.empty or df_metas.empty:
        return []

    df_monitoramento['mes_num'] = pd.to_datetime(df_monitoramento['data']).dt.month
    df_merged = pd.merge(df_monitoramento, df_metas, on='mes_num', how='left')

    df_merged.rename(columns={
        'data': 'Data', 'volume_hm3': 'volume', 'meta1v': 'meta1',
        'meta2v': 'meta2', 'meta3v': 'meta3'
    }, inplace=True)
    df_merged['Data'] = pd.to_datetime(df_merged['Data']).dt.strftime('%Y-%m-%d')

    return df_merged[['Data', 'volume', 'meta1', 'meta2', 'meta3']].to_dict('records')


@app.get("/api/ongoing-actions") # Removido o response_model
async def get_ongoing_actions(db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, situacao="Em andamento")
    # --- Construção Manual da Resposta ---
    return [
        {"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao}
        for a in acoes
    ]

@app.get("/api/completed-actions") # Removido o response_model
async def get_completed_actions(db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, situacao="Concluído")
    # --- Construção Manual da Resposta ---
    return [
        {"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao}
        for a in acoes
    ]

@app.get("/api/action-plans/filters", response_model=schemas.ActionPlanFilterOptions)
async def get_action_plan_filters(db: AsyncSession = Depends(get_db)):
    return await crud.get_action_plan_filters(db)


@app.get("/api/action-plans")  # Removido o response_model para controlo manual
async def get_action_plans(
        estado: Optional[str] = None,
        impacto: Optional[str] = None,
        problema: Optional[str] = None,
        acao: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    planos = await crud.get_action_plans(db, estado, impacto, problema, acao)

    # --- Construção Manual da Resposta ---
    # Isto garante que as chaves correspondem exatamente ao que o frontend espera.
    # Com base nos seus ficheiros Excel originais, os nomes prováveis são estes:
    return [
        {
            "DESCRIÇÃO DA AÇÃO": p.descricao_acao,
            "CLASSES DE AÇÃO": p.classes_acao,
            "RESPONSÁVEIS": p.responsaveis,
            # Adicione outras chaves aqui se a sua tabela no frontend precisar delas
            # "PROBLEMAS": p.problemas,
            # "TIPOS DE IMPACTOS": p.tipos_impactos,
        }
        for p in planos
    ]


@app.get("/api/water-balance/static-charts")
async def get_static_balance_charts(db: AsyncSession = Depends(get_db)):
    balanco_mensal = await crud.get_balanco_mensal(db)
    composicao_demanda = await crud.get_composicao_demanda(db)
    oferta_demanda = await crud.get_oferta_demanda(db)

    return {
        "balancoMensal": balanco_mensal,
        "composicaoDemanda": composicao_demanda,
        "ofertaDemanda": oferta_demanda,
    }


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