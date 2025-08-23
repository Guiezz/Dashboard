# main.py (VERSÃO COMPLETA E OTIMIZADA PARA DEPLOY NO RAILWAY)
import os
import httpx
import pandas as pd
from contextlib import asynccontextmanager
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Importações locais
import crud
import models
import schemas
from database import engine, get_db, Base # Importa a Base que agora vive em database.py

# Função para rodar durante o ciclo de vida da aplicação (startup e shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Aplicação a arrancar...")
    async with engine.begin() as conn:
        # Cria todas as tabelas (se não existirem) a partir dos modelos
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabelas do banco de dados verificadas/criadas.")
    yield
    print("👋 Aplicação a encerrar...")

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="API de Monitoramento de Seca",
    description="API para servir dados sobre reservatórios e monitoramento de seca.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Middlewares ---
# Adiciona o CORS para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja a `["URL_DO_SEU_FRONTEND"]`
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Arquivos Estáticos ---
# Monta o diretório 'static' para servir imagens
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(os.path.join(static_dir, "images"))
app.mount(f"/{static_dir}", StaticFiles(directory=static_dir), name="static")


# --- Endpoints da API ---

@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar o status da API."""
    return {"status": "API de Monitoramento de Seca está online."}


@app.get("/api/reservatorios", response_model=List[schemas.ReservatorioSelecao], tags=["Reservatórios"])
async def get_reservatorios_list(db: AsyncSession = Depends(get_db)):
    """Retorna uma lista de todos os reservatórios disponíveis para o seletor."""
    reservatorios = await crud.get_reservatorios(db)
    if not reservatorios:
        return []
    return reservatorios


@app.get("/api/reservatorios/{reservatorio_id}/identification", response_model=schemas.Reservatorio, tags=["Reservatórios"])
async def get_identification_data(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    """Busca os dados de identificação de um reservatório específico."""
    identificacao = await crud.get_identificacao(db, reservatorio_id=reservatorio_id)
    if not identificacao:
        raise HTTPException(status_code=404, detail="Reservatório não encontrado.")

    # Constrói as URLs das imagens dinamicamente para o ambiente de produção
    url_base = os.getenv("RAILWAY_STATIC_URL", "http://127.0.0.1:8000")
    if "railway.app" in url_base and not url_base.startswith("https://"):
        url_base = "https://" + url_base

    response_data = schemas.Reservatorio.model_validate(identificacao)
    response_data.url_imagem = f"{url_base}/static/images/{identificacao.nome_imagem}" if identificacao.nome_imagem else None
    response_data.url_imagem_usos = f"{url_base}/static/images/{identificacao.nome_imagem_usos}" if identificacao.nome_imagem_usos else None

    return response_data


@app.get("/api/reservatorios/{reservatorio_id}/dashboard/summary", tags=["Dashboard"])
async def get_dashboard_summary(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna um resumo dos dados para o painel principal."""
    historico = await crud.get_history_with_status(db, reservatorio_id=reservatorio_id)
    if historico.empty:
        raise HTTPException(status_code=404, detail="Dados de monitoramento não disponíveis.")

    ultimo_registro = historico.iloc[0]
    estado_atual = ultimo_registro['estado_calculado']
    data_atual = ultimo_registro['data']

    historico_anterior = historico[historico['estado_calculado'] != estado_atual]
    dias = (data_atual - historico_anterior.iloc[0]['data']).days if not historico_anterior.empty else (data_atual - historico.iloc[-1]['data']).days

    medidas = await crud.get_action_plans(db, reservatorio_id=reservatorio_id, estado=estado_atual)
    medidas_formatadas = [{"Ação": m.acoes, "Descrição": m.descricao_acao, "Responsáveis": m.responsaveis} for m in medidas]

    return {
        "volumeAtualHm3": ultimo_registro.get("volume_hm3", 0),
        "volumePercentual": ultimo_registro.get("volume_percentual", 0) * 100,
        "estadoAtualSeca": estado_atual,
        "dataUltimaMedicao": data_atual,
        "diasDesdeUltimaMudanca": dias,
        "medidasRecomendadas": medidas_formatadas
    }

@app.get("/api/reservatorios/{reservatorio_id}/history", tags=["Histórico"])
async def get_history_data(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    historico_com_estado = await crud.get_history_with_status(db, reservatorio_id=reservatorio_id)
    if historico_com_estado.empty: return []
    df_merged = historico_com_estado.copy()
    df_merged.rename(columns={'data': 'Data', 'estado_calculado': 'Estado de Seca', 'volume_hm3': 'Volume (Hm³)'},
                     inplace=True)
    df_merged['Data'] = pd.to_datetime(df_merged['Data']).dt.strftime('%d/%m/%Y')
    return df_merged[['Data', 'Estado de Seca', 'Volume (Hm³)']].to_dict('records')


@app.get("/api/reservatorios/{reservatorio_id}/chart/volume-data", tags=["Gráficos"])
async def get_chart_data(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    historico_com_estado = await crud.get_history_with_status(db, reservatorio_id=reservatorio_id)
    if historico_com_estado.empty: return []
    df_merged = historico_com_estado.copy()
    df_merged = df_merged.sort_values(by='data', ascending=True)
    df_merged.rename(
        columns={'data': 'Data', 'volume_hm3': 'volume', 'meta1v': 'meta1', 'meta2v': 'meta2', 'meta3v': 'meta3'},
        inplace=True)
    df_merged['Data'] = pd.to_datetime(df_merged['Data']).dt.strftime('%Y-%m-%d')
    return df_merged[['Data', 'volume', 'meta1', 'meta2', 'meta3']].to_dict('records')

@app.get("/api/reservatorios/{reservatorio_id}/ongoing-actions", tags=["Planos de Ação"])
async def get_ongoing_actions(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, reservatorio_id=reservatorio_id, situacao="Em andamento")
    return [{"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao} for a in acoes]


@app.get("/api/reservatorios/{reservatorio_id}/completed-actions", tags=["Planos de Ação"])
async def get_completed_actions(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    acoes = await crud.get_action_plans(db, reservatorio_id=reservatorio_id, situacao="Concluído")
    return [{"AÇÕES": a.acoes, "RESPONSÁVEIS": a.responsaveis, "SITUAÇÃO": a.situacao} for a in acoes]


@app.get("/api/reservatorios/{reservatorio_id}/action-plans/filters", response_model=schemas.ActionPlanFilterOptions, tags=["Planos de Ação"])
async def get_action_plan_filters(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_action_plan_filters(db, reservatorio_id=reservatorio_id)


@app.get("/api/reservatorios/{reservatorio_id}/action-plans", tags=["Planos de Ação"])
async def get_action_plans(reservatorio_id: int, estado: Optional[str] = None, impacto: Optional[str] = None,
                           problema: Optional[str] = None, acao: Optional[str] = None,
                           db: AsyncSession = Depends(get_db)):
    planos = await crud.get_action_plans(db, reservatorio_id=reservatorio_id, estado=estado, impacto=impacto,
                                         problema=problema, acao=acao)
    return [{"DESCRIÇÃO DA AÇÃO": p.descricao_acao, "CLASSES DE AÇÃO": p.classes_acao, "RESPONSÁVEIS": p.responsaveis}
            for p in planos]


@app.get("/api/reservatorios/{reservatorio_id}/water-balance/static-charts", tags=["Balanço Hídrico"])
async def get_static_balance_charts(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    balanco_mensal_data = await crud.get_balanco_mensal(db, reservatorio_id=reservatorio_id)
    composicao_demanda_data = await crud.get_composicao_demanda(db, reservatorio_id=reservatorio_id)
    oferta_demanda_data = await crud.get_oferta_demanda(db, reservatorio_id=reservatorio_id)
    balanco_formatado = [
        {"Mês": bm.mes, "Afluência (m³/s)": float(bm.afluencia_m3s or 0), "Demanda (m³/s)": float(bm.demandas_m3s or 0),
         "Balanço (m³/s)": float(bm.afluencia_m3s or 0) - float(bm.demandas_m3s or 0), "Evaporação (m³/s)": float(bm.evaporacao_m3s or 0)} for bm in
        balanco_mensal_data]
    composicao_formatada = [{"Uso": cd.usos, "Vazão (L/s)": float(cd.demandas_hm3 or 0)} for cd in
                            composicao_demanda_data]
    oferta_formatada = [
        {"Cenário": od.cenarios, "Oferta (L/s)": float(od.oferta_m3s or 0), "Demanda (L/s)": float(od.demanda_m3s or 0)}
        for od in oferta_demanda_data]
    return {"balancoMensal": balanco_formatado, "composicaoDemanda": composicao_formatada,
            "ofertaDemanda": oferta_formatada}


@app.get("/api/reservatorios/{reservatorio_id}/usos-agua", response_model=List[schemas.UsoAgua], tags=["Usos da Água"])
async def get_usos_agua(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_usos_agua(db, reservatorio_id=reservatorio_id)


@app.get("/api/reservatorios/{reservatorio_id}/responsaveis", response_model=List[schemas.Responsavel], tags=["Responsáveis"])
async def get_responsaveis(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_responsaveis(db, reservatorio_id=reservatorio_id)


@app.post("/api/reservatorios/{reservatorio_id}/update-funceme-data", tags=["Dados Externos"])
async def update_funceme_data(reservatorio_id: int, db: AsyncSession = Depends(get_db)):
    reservatorio = await crud.get_reservatorio_by_id(db, reservatorio_id=reservatorio_id)
    if not reservatorio:
        raise HTTPException(status_code=404, detail="Reservatório não encontrado na base de dados local.")
    if not reservatorio.codigo_funceme:
        raise HTTPException(status_code=400, detail="Este reservatório não possui um código da FUNCEME associado.")

    print(f"📡 Buscando dados para o reservatório '{reservatorio.nome}' (FUNCEME ID: {reservatorio.codigo_funceme})...")
    hoje = date.today().strftime("%Y-%m-%d")
    url_funceme = f"https://apil5.funceme.br/rpc/v1/reservatorio-series?reservatorio_id={reservatorio.codigo_funceme}&data_inicio=2023-01-01&data_fim={hoje}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_funceme, timeout=30.0)
            response.raise_for_status()
            dados_funceme_raw = response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Erro de conexão ao buscar dados da FUNCEME: {e}")

    dados_reais = dados_funceme_raw.get('data', {}).get('list', [])
    if not dados_reais:
        return {"status": "A API da FUNCEME não retornou novos dados para este reservatório."}

    existing_dates_query = await db.execute(
        select(models.Monitoramento.data).where(models.Monitoramento.reservatorio_id == reservatorio_id)
    )
    existing_dates = {d for d, in existing_dates_query}

    novos_registros = []
    for registro in dados_reais:
        data_registro = date.fromisoformat(registro['data'])
        if data_registro not in existing_dates:
            novos_registros.append(models.Monitoramento(
                data=data_registro,
                volume_hm3=registro.get('volume'),
                volume_percentual=registro.get('volume_perc'),
                reservatorio_id=reservatorio_id
            ))

    if novos_registros:
        db.add_all(novos_registros)
        await db.commit()
        return {
            "status": f"{len(novos_registros)} novos registros de monitoramento foram adicionados para '{reservatorio.nome}'."}

    return {"status": f"Nenhum registro novo para '{reservatorio.nome}'. O banco de dados já está atualizado."}
