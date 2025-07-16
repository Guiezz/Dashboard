import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.helpers import carregar_dados_monitoramento

df = carregar_dados_monitoramento()

# Converter datas
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
df.sort_values("Data", inplace=True)

# Último registro
ultimo = df.iloc[-1]
estado_atual = ultimo["Estado de Seca"]
volume_atual = ultimo["Volume (Hm³)"]

# Última mudança de estado
df["estado_anterior"] = df["Estado de Seca"].shift(1)
mudancas = df[df["Estado de Seca"] != df["estado_anterior"]].copy()
data_ultima_mudanca = mudancas.iloc[-1]["Data"]
dias_desde_ultima_mudanca = (datetime.now().date() - data_ultima_mudanca.date()).days

# === Interface ===
st.title("📊 Monitoramento do Estado da Seca")

col1, col2 = st.columns([1, 2])
with col1:
    st.metric(label="💧 Volume Atual (hm³)", value=f"{volume_atual:.2f}")
    st.info(f"⏱ Estamos nesse estado há **{dias_desde_ultima_mudanca} dias**.")
    st.caption(f"📅 Última mudança: {data_ultima_mudanca.strftime('%d/%m/%Y')}")

with col2:
    st.subheader("📋 Medidas Recomendadas")
    if estado_atual == "Severa":
        medidas = {
            "Ação": [
                "Poços de abastecimento", "Reuniões comunitárias", "Rodízio urbano"
            ],
            "Descrição": [
                "Implantar poços em áreas críticas",
                "Reforçar comunicação com a população",
                "Reduzir consumo nos bairros por rodízio"
            ]
        }
    elif estado_atual == "Normal":
        medidas = {
            "Ação": [
                "Manutenção preventiva", "Capacitações técnicas", "Monitoramento contínuo"
            ],
            "Descrição": [
                "Garantir operação dos sistemas",
                "Treinamentos com operadores locais",
                "Análises periódicas de volume e uso"
            ]
        }
    else:
        medidas = {
            "Ação": ["Ação genérica"],
            "Descrição": ["Sem recomendações específicas"]
        }
    st.table(medidas)

# === TABELA DE HISTÓRICO ===
st.subheader("📋 Histórico de Seca e Volume")

tabela = df[["Data", "Estado de Seca", "Volume (%)", "Volume (Hm³)"]].copy()

# Garante ordenação crescente
tabela = tabela.sort_values("Data", ascending=False)

# Formata a data para exibir como string no final
tabela["Data"] = tabela["Data"].dt.strftime("%d/%m/%Y")

# Exibe os 20 registros mais recentes
st.dataframe(tabela.head(80), use_container_width=True)


# === GRÁFICO DE VOLUME x METAS ===
st.subheader("📈 Volume (Hm³) comparado com Metas")

grafico_df = df[["Data", "Volume (Hm³)", "Meta1v", "Meta2v", "Meta3v"]].copy()

# Cria colunas nomeadas para melt
grafico_df.rename(columns={
    "Volume (Hm³)": "Volume",
    "Meta1v": "Meta 1",
    "Meta2v": "Meta 2",
    "Meta3v": "Meta 3"
}, inplace=True)

grafico_melt = grafico_df.melt(id_vars="Data", var_name="Indicador", value_name="Valor")

# Cria o gráfico
import plotly.graph_objects as go

fig = go.Figure()

# Adiciona metas como linhas tracejadas mais discretas
for meta_nome, cor in zip(["Meta 1", "Meta 2", "Meta 3"], ["crimson", " darkgoldenrod", " darkorange"]):
    fig.add_trace(go.Scatter(
        x=grafico_df["Data"],
        y=grafico_df[meta_nome],
        name=meta_nome,
        mode="lines",
        line=dict(dash="dash", width=2, color=cor)
    ))
# Adiciona linha do Volume com destaque
fig.add_trace(go.Scatter(
    x=grafico_df["Data"],
    y=grafico_df["Volume"],
    name="Volume",
    mode="lines+markers",
    line=dict(color="blue", width=3)
))

fig.update_layout(
    title="Volume em Hm³ comparado com Metas",
    xaxis_title="Data",
    yaxis_title="Volume (Hm³)",
    legend_title="Indicador",
    template="simple_white"
)

st.plotly_chart(fig, use_container_width=True)

