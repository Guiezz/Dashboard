import plotly.express as px
import pandas as pd

def grafico_oferta_hidrica():
    dados = pd.DataFrame({
        "Garantia": ["Q90", "Q95", "Q98"],
        "Oferta (l/s)": [688.8, 520.8, 400.2]
    })
    fig = px.bar(dados, x="Garantia", y="Oferta (l/s)", title="Oferta Hídrica Estimada")
    return fig
