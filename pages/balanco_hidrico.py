import streamlit as st
from components.graficos import grafico_oferta_hidrica
import plotly.express as px
import pandas as pd

st.title("📉 Balanço Hídrico do Sistema")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Oferta Hídrica Estimada")
    st.plotly_chart(grafico_oferta_hidrica())

    st.markdown("### Distribuição da Demanda")
    fig2 = px.pie(values=[12.3, 87.7], names=["Abastecimento Humano", "Usos Múltiplos"])
    st.plotly_chart(fig2)

with col2:
    st.markdown("### Superávit / Déficit Hídrico")
    fig3 = px.bar(x=["Q90", "Q95", "Q98"], y=[150, 20, -80], color=["Q90", "Q95", "Q98"],
                  labels={"x": "Garantia", "y": "Superávit / Déficit (l/s)"})
    st.plotly_chart(fig3)

    st.markdown("### Relação Oferta vs Demanda")
    st.markdown("""
    - Q90: atende com folga  
    - Q95: quase limite  
    - Q98: sistema entra em déficit (-80 l/s)
    """)
