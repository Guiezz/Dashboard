# main.py (Versão com endpoint de Identificação CORRIGIDO)

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# --- BLOCO DE CARREGAMENTO: DADOS DE MONITORAMENTO ---
try:
    from utils.helpers import carregar_dados_monitoramento

    print("✅ Carregando dados de MONITORAMENTO...")
    df_monitoramento = carregar_dados_monitoramento()
    print("Dados de monitoramento carregados com sucesso.")
except Exception as e:
    print(f"❌ ERRO ao carregar dados de monitoramento: {e}")
    df_monitoramento = pd.DataFrame()

# --- BLOCO DE CARREGAMENTO: DADOS DE IDENTIFICAÇÃO (COM NOVA CORREÇÃO) ---
df_identificacao = pd.DataFrame()
df_lat_long = pd.DataFrame()
try:
    caminho_arquivo = 'data/identificacao_patu.xlsx'
    print(f"✅ Carregando dados de IDENTIFICAÇÃO de '{caminho_arquivo}'...")

    # CORREÇÃO: Lendo apenas a primeira (e única) aba do arquivo.
    df_completo = pd.read_excel(caminho_arquivo, sheet_name=0)

    # Agora, vamos recriar os dataframes que o resto do código espera
    # a partir deste dataframe completo.
    # Esta abordagem é mais segura e assume que o arquivo tem apenas uma aba.

    # Assumimos que o texto de identificação está na primeira coluna.
    # O .to_frame() garante que o resultado seja um DataFrame.
    df_identificacao = df_completo.iloc[:, 0].to_frame()

    # Assumimos que a latitude e longitude estão na segunda e terceira colunas.
    df_lat_long = df_completo.iloc[:, 1:3]

    # Para garantir, vamos nomear as colunas como o resto do código poderia esperar
    df_identificacao.columns = ['identificacao']
    df_lat_long.columns = ['lat', 'lon']

    print("Dados de identificação extraídos da única planilha com sucesso.")

except FileNotFoundError:
    print(f"❌ ERRO: Arquivo de identificação não encontrado em '{caminho_arquivo}'.")
except Exception as e:
    # Este erro agora pode indicar um problema com o formato da única planilha.
    print(f"❌ ERRO ao carregar ou processar dados de identificação: {e}")

# --- PROCESSAMENTO DOS DADOS DE MONITORAMENTO ---
# (Nenhuma alteração neste bloco)
if not df_monitoramento.empty:
    try:
        df_monitoramento["Data"] = pd.to_datetime(df_monitoramento["Data"], errors="coerce")
        df_monitoramento.sort_values("Data", inplace=True)
        ultimo_registro = df_monitoramento.iloc[-1]
        estado_atual = ultimo_registro["Estado de Seca"]
        volume_atual = ultimo_registro["Volume (Hm³)"]
        df_monitoramento["estado_anterior"] = df_monitoramento["Estado de Seca"].shift(1)
        mudancas = df_monitoramento[df_monitoramento["Estado de Seca"] != df_monitoramento["estado_anterior"]].copy()
        if not mudancas.empty:
            data_ultima_mudanca = mudancas.iloc[-1]["Data"]
            dias_desde_ultima_mudanca = (datetime.now().date() - data_ultima_mudanca.date()).days
        else:
            data_ultima_mudanca = df_monitoramento.iloc[0]["Data"]
            dias_desde_ultima_mudanca = (datetime.now().date() - data_ultima_mudanca.date()).days
    except Exception as e:
        print(f"❌ ERRO durante o processamento do DataFrame de monitoramento: {e}")
        df_monitoramento = pd.DataFrame()
else:
    print("API iniciada sem dados de monitoramento. Endpoints relacionados retornarão erro.")

# --- CRIAÇÃO DA API ---
# (Nenhuma alteração neste bloco)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --- ENDPOINTS DA API ---
# (Nenhuma alteração nos endpoints)

@app.get("/")
def read_root():
    return {"status": "API de Monitoramento da Seca está online"}


@app.get("/api/identification")
def get_identification_data():
    if df_identificacao.empty or df_lat_long.empty:
        return {"error": "Dados de identificação não disponíveis. Verifique os logs da API."}

    # O .iloc[0,0] pega o texto da primeira linha, primeira coluna
    identificacao_texto = df_identificacao.iloc[0, 0] if not df_identificacao.empty else ""

    # Pega a primeira linha de coordenadas
    location_data = df_lat_long.head(1).to_dict('records')

    return {
        "identification_text": identificacao_texto,
        "location_data": location_data
    }


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    if df_monitoramento.empty:
        return {"error": "Dados de monitoramento não disponíveis."}
    if estado_atual == "Severa":
        medidas = [{"Ação": "Poços de abastecimento", "Descrição": "Implantar poços em áreas críticas"}]
    elif estado_atual == "Normal":
        medidas = [{"Ação": "Manutenção preventiva", "Descrição": "Garantir operação dos sistemas"}]
    else:
        medidas = [{"Ação": "Ação genérica", "Descrição": "Sem recomendações específicas"}]
    return {
        "volumeAtualHm3": round(volume_atual, 2),
        "estadoAtualSeca": estado_atual,
        "diasDesdeUltimaMudanca": dias_desde_ultima_mudanca,
        "dataUltimaMudanca": data_ultima_mudanca.strftime('%d/%m/%Y'),
        "medidasRecomendadas": medidas
    }


@app.get("/api/history")
def get_history_table():
    if df_monitoramento.empty:
        return {"error": "Dados não disponíveis."}
    tabela = df_monitoramento[["Data", "Estado de Seca", "Volume (%)", "Volume (Hm³)"]].copy()
    tabela = tabela.sort_values("Data", ascending=False).head(80)
    tabela["Data"] = tabela["Data"].dt.strftime("%d/%m/%Y")
    tabela["Volume (%)"] = tabela["Volume (%)"].round(2)
    tabela["Volume (Hm³)"] = tabela["Volume (Hm³)"].round(2)
    return tabela.to_dict('records')


@app.get("/api/chart/volume-data")
def get_chart_data():
    if df_monitoramento.empty:
        return {"error": "Dados não disponíveis."}
    grafico_df = df_monitoramento[["Data", "Volume (Hm³)", "Meta1v", "Meta2v", "Meta3v"]].copy()
    grafico_df["Data"] = grafico_df["Data"].dt.strftime('%Y-%m-%d')
    grafico_df.rename(columns={"Volume (Hm³)": "volume", "Meta1v": "meta1", "Meta2v": "meta2", "Meta3v": "meta3"},
                      inplace=True)
    return grafico_df.to_dict('records')
