# main.py (Versão com correção no endpoint do gráfico)
from typing import Optional
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from datetime import datetime
import numpy as np

# --------------------------------------------------------------------------
# --- CARREGAMENTO DE DADOS ---
# --------------------------------------------------------------------------

# Carrega df_monitoramento
try:
    from utils.helpers import carregar_dados_monitoramento

    df_monitoramento = carregar_dados_monitoramento()
    df_monitoramento["Data"] = pd.to_datetime(df_monitoramento["Data"], errors="coerce")
    df_monitoramento.sort_values("Data", inplace=True)
    print("✅ Dados de MONITORAMENTO carregados.")
except Exception as e:
    df_monitoramento = pd.DataFrame()
    print(f"❌ ERRO ao carregar dados de monitoramento: {e}")

# Carrega df_identificacao
df_identificacao = pd.DataFrame()
df_lat_long = pd.DataFrame()
try:
    caminho_arquivo = 'data/identificacao_patu.xlsx'
    df_completo = pd.read_excel(caminho_arquivo, sheet_name=0)
    df_identificacao = df_completo.iloc[:, 0].to_frame()
    df_lat_long = df_completo.iloc[:, 1:3]
    df_identificacao.columns = ['identificacao']
    df_lat_long.columns = ['lat', 'lon']
    print("✅ Dados de IDENTIFICAÇÃO carregados.")
except Exception as e:
    print(f"❌ ERRO ao carregar dados de identificação: {e}")

# Carrega df_planos
try:
    caminho_arquivo_planos = 'data/plano_acao_patu_junto.xlsx'
    df_planos = pd.read_excel(caminho_arquivo_planos, sheet_name='Junto')
    df_planos.columns = [col.strip() for col in df_planos.columns]
    df_planos = df_planos.fillna('')
    print("✅ Dados de PLANOS DE AÇÃO carregados.")
except Exception as e:
    df_planos = pd.DataFrame()
    print(f"❌ ERRO ao carregar dados de planos de ação: {e}")

# Carrega dados estáticos do balanço hídrico
df_balanco_mensal = pd.DataFrame()
df_composicao = pd.DataFrame()
df_oferta = pd.DataFrame()
try:
    caminho_arquivo_balanco = 'data/balanco_hidrico_patu.xlsx'
    df_balanco_mensal = pd.read_excel(caminho_arquivo_balanco, sheet_name='Balanço Mensal')
    df_composicao = pd.read_excel(caminho_arquivo_balanco, sheet_name='Composição Demanda')
    df_oferta = pd.read_excel(caminho_arquivo_balanco, sheet_name='Oferta Demanda')
    print("✅ Dados de BALANÇO HÍDRICO (Gráficos Estáticos) carregados.")
except Exception as e:
    print(f"❌ ERRO ao carregar dados de balanço hídrico: {e}")

# Pré-processa dados gerais do monitoramento
estado_atual = "Indisponível"
volume_atual = 0
dias_desde_ultima_mudanca = 0
data_ultima_mudanca = datetime.now()

if not df_monitoramento.empty:
    try:
        ultimo_registro = df_monitoramento.iloc[-1]
        estado_atual = ultimo_registro["Estado de Seca"]
        volume_atual = ultimo_registro["Volume (Hm³)"]
        df_monitoramento["estado_anterior"] = df_monitoramento["Estado de Seca"].shift(1)
        mudancas = df_monitoramento[df_monitoramento["Estado de Seca"] != df_monitoramento["estado_anterior"]].copy()
        if not mudancas.empty:
            data_ultima_mudanca = mudancas.iloc[-1]["Data"]
        else:
            data_ultima_mudanca = df_monitoramento.iloc[0]["Data"]
        dias_desde_ultima_mudanca = (datetime.now().date() - data_ultima_mudanca.date()).days
    except Exception as e:
        print(f"❌ ERRO durante o processamento do DataFrame de monitoramento: {e}")

# --- CRIAÇÃO DA API ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# --- ENDPOINTS DA API ---

@app.get("/")
def read_root():
    return {"status": "API de Monitoramento da Seca está online"}


@app.get("/api/identification")
def get_identification_data():
    if df_identificacao.empty or df_lat_long.empty: return {"error": "Dados não disponíveis."}
    identificacao_texto = df_identificacao.iloc[0, 0] if not df_identificacao.empty else ""
    location_data = df_lat_long.head(1).to_dict('records')
    return {"identification_text": identificacao_texto, "location_data": location_data}


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    # ... (código sem alteração)
    if df_monitoramento.empty: return {"error": "Dados não disponíveis."}
    medidas = []
    if not df_planos.empty:
        try:
            recomendacoes_df = df_planos[df_planos['ESTADO DE SECA'] == estado_atual]
            medidas_df = recomendacoes_df[['AÇÕES', 'DESCRIÇÃO DA AÇÃO']].rename(
                columns={'AÇÕES': 'Ação', 'DESCRIÇÃO DA AÇÃO': 'Descrição'})
            medidas = medidas_df.to_dict('records')
            if not medidas:
                medidas = [{"Ação": "Nenhuma medida específica",
                            "Descrição": f"Não foram encontradas recomendações para o estado '{estado_atual}'."}]
        except Exception as e:
            medidas = [{"Ação": "Erro", "Descrição": "Não foi possível carregar as recomendações."}]
    return {
        "volumeAtualHm3": round(volume_atual, 2),
        "estadoAtualSeca": estado_atual,
        "diasDesdeUltimaMudanca": dias_desde_ultima_mudanca,
        "dataUltimaMudanca": data_ultima_mudanca.strftime('%d/%m/%Y'),
        "medidasRecomendadas": medidas
    }


@app.get("/api/history")
def get_history_table():
    # ... (código sem alteração)
    if df_monitoramento.empty: return {"error": "Dados não disponíveis."}
    tabela = df_monitoramento[["Data", "Estado de Seca", "Volume (%)", "Volume (Hm³)"]].copy()
    tabela = tabela.sort_values("Data", ascending=False).head(80)
    tabela["Data"] = tabela["Data"].dt.strftime("%d/%m/%Y")
    tabela["Volume (%)"] = tabela["Volume (%)"].round(2)
    tabela["Volume (Hm³)"] = tabela["Volume (Hm³)"].round(2)
    return tabela.to_dict('records')


# --- ENDPOINT CORRIGIDO ---
@app.get("/api/chart/volume-data")
def get_chart_data():
    if df_monitoramento.empty: return {"error": "Dados não disponíveis."}
    grafico_df = df_monitoramento[["Data", "Volume (Hm³)", "Meta1v", "Meta2v", "Meta3v"]].copy()
    grafico_df["Data"] = grafico_df["Data"].dt.strftime('%Y-%m-%d')

    # CORREÇÃO: Removemos o dois-pontos (:) extra de "Volume (Hm³):"
    grafico_df.rename(columns={"Volume (Hm³)": "volume", "Meta1v": "meta1", "Meta2v": "meta2", "Meta3v": "meta3"},
                      inplace=True)

    return grafico_df.to_dict('records')


# ... (resto dos endpoints sem alteração)

@app.get("/api/ongoing-actions")
def get_ongoing_actions():
    if df_planos.empty: return {"error": "Dados de planos de ação não disponíveis."}
    try:
        ongoing_df = df_planos[df_planos['SITUAÇÃO'] == 'Em andamento']
        return ongoing_df[['AÇÕES', 'RESPONSÁVEIS', 'SITUAÇÃO']].to_dict('records')
    except Exception as e:
        return {"error": f"Erro: {e}"}


@app.get("/api/completed-actions")
def get_completed_actions():
    if df_planos.empty: return {"error": "Dados de planos de ação não disponíveis."}
    try:
        completed_df = df_planos[df_planos['SITUAÇÃO'] == 'Concluído']
        return completed_df[['AÇÕES', 'RESPONSÁVEIS', 'SITUAÇÃO']].to_dict('records')
    except Exception as e:
        return {"error": f"Erro ao processar ações concluídas: {e}"}


@app.get("/api/action-plans/filters")
def get_action_plan_filters():
    if df_planos.empty: return {"error": "Dados não disponíveis."}
    estados = sorted([e for e in df_planos['ESTADO DE SECA'].unique() if e])
    impactos = sorted([i for i in df_planos['TIPOS DE IMPACTOS'].unique() if i])
    problemas = sorted([p for p in df_planos['PROBLEMAS'].unique() if p])
    acoes = sorted([a for a in df_planos['AÇÕES'].unique() if a])
    return {"estados_de_seca": estados, "tipos_de_impacto": impactos, "problemas": problemas, "acoes": acoes}


@app.get("/api/action-plans")
def get_action_plans(estado: Optional[str] = None, impacto: Optional[str] = None, problema: Optional[str] = None,
                     acao: Optional[str] = None):
    if df_planos.empty: return {"error": "Dados não disponíveis."}
    filtered_df = df_planos.copy()
    if estado: filtered_df = filtered_df[filtered_df['ESTADO DE SECA'] == estado]
    if impacto: filtered_df = filtered_df[filtered_df['TIPOS DE IMPACTOS'] == impacto]
    if problema: filtered_df = filtered_df[filtered_df['PROBLEMAS'] == problema]
    if acao: filtered_df = filtered_df[filtered_df['AÇÕES'] == acao]
    return filtered_df[['DESCRIÇÃO DA AÇÃO', 'CLASSES DE AÇÃO', 'RESPONSÁVEIS']].to_dict('records')


@app.get("/api/water-balance/static-charts")
def get_static_balance_charts():
    if df_balanco_mensal.empty or df_composicao.empty or df_oferta.empty:
        return {"error": "Dados para os gráficos de balanço hídrico não foram carregados."}
    try:
        return {
            "balancoMensal": df_balanco_mensal.to_dict('records'),
            "composicaoDemanda": df_composicao.to_dict('records'),
            "ofertaDemanda": df_oferta.to_dict('records')
        }
    except Exception as e:
        return {"error": f"Erro ao converter dados dos gráficos para JSON: {e}"}