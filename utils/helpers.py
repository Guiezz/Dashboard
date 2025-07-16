import pandas as pd
import streamlit as st

@st.cache_data
def carregar_dados_monitoramento(caminho="data/monitoramento_patu.xlsx"):
    df = pd.read_excel(caminho)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df.sort_values("Data", inplace=True)
    return df