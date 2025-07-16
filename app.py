import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Gestão da Seca - Hidrossistema Patu")

# ======= Sidebar e Navegação =======
st.sidebar.title("🔍 Navegação")
aba = st.sidebar.radio("Selecione a seção:", [
    "Identificação do Hidrossistema",
    "Estado da Seca",
    "Planos de Ação",
    "Impacto das Secas na Região",
    "Usos do Hidrossistema",
    "Balanço Hídrico"
])

# ======= Aba 1: Identificação do Hidrossistema =======
if aba == "Identificação do Hidrossistema":
    st.title("📍 Hidrossistema Patu")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
O Plano de Gestão Proativa de Seca do Hidrossistema Patu foi o primeiro do Ceará e do Brasil, destacando-se por sua metodologia inovadora desenvolvida no âmbito do Programa Cientista Chefe – Recursos Hídricos. Sua elaboração, concluída em 2022, baseou-se em uma construção coletiva e interdisciplinar, envolvendo universidades, colegiados de participação social (como o Comitê de Bacia do Banabuiú e a Comissão Gestora do Açude Patu) e gestores públicos. Esse plano estabeleceu um modelo metodológico que serviu de base para a criação dos demais planos de seca no estado.
O Hidrossistema Patu está localizado na Região Hidrográfica do Banabuiú, parte da Bacia do Rio Jaguaribe, no município de Senador Pompeu, no Sertão Central do Ceará, uma área severamente afetada pela seca. Seu principal reservatório, o Açude Patu, foi construído em 1987 pelo DNOCS e tem capacidade máxima de 65.103.000 m³, com uma área de drenagem de 993,50 km². O hidrossistema é utilizado para abastecimento humano, irrigação, dessedentação animal e agropecuária. A seca de 2012 impactou significativamente a disponibilidade hídrica e a dinâmica do sistema, levando a restrições de uso e afetando três municípios: Senador Pompeu, Milhã e Quixeramobim. 
O Sistema de Suporte à Decisão do Plano de Seca do Hidrossistema Patu objetiva ser instrumento de monitoramento, acompanhamento e divulgação das ações pensadas no âmbito do Plano de Seca do Hidrossistema Patu, permitindo uma interface simples, didática e acessível aos distintos atores sociais envolvidos, sobretudo a Câmara Técnica Permanente de Gestão Proativa de Seca da Região Hidrográfica do Banabuiú e a Gerência Regional da Cogerh da Bacia do Banabuiú. 
Com essa interface, é possível conhecer e acompanhar os distintos estados de seca definidos no plano, as ações sugeridas para serem implementadas em cada um desses estados e a inclusão de novas ações e informações relevantes sobre o estado de seca no hidrossistema.
        """)

    with col2:
        st.markdown("### 🌍 Localização no Mapa")
        map_patu = folium.Map(location=[-5.58194444,-39.40250000], zoom_start=10)
        folium.Marker(
            location=[-5.58194444,-39.40250000],
            popup="Açude Patu",
            tooltip="Clique para detalhes"
        ).add_to(map_patu)
        st_folium(map_patu, width=400, height=800)

# ======= Aba 2: Estado da Seca =======
elif aba == "Estado da Seca":
    st.title("📊 Monitoramento do Estado da Seca")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="💧 Volume Atual (hm³)", value="36,84", delta="Normal")
        st.info("Estamos nesse estado há **1233 dias**.")
        st.caption("Data da última mudança: 25/02/2022")

    with col2:
        st.subheader("📋 Medidas Recomendadas")
        medidas = pd.DataFrame({
            "Ação": [
                "Irrigação econômica",
                "Fontes alternativas urbanas",
                "Tratamento eficaz"
            ],
            "Descrição": [
                "Uso de métodos de irrigação com economia",
                "Uso de fontes alternativas no meio urbano",
                "Tratamento da água nas comunidades"
            ]
        })
        st.table(medidas)

    st.subheader("🚧 Ações em Andamento (em situação de Seca Severa)")
    acoes = pd.DataFrame({
        "Ação": [
            "Poços de abastecimento", "Reuniões comunitárias", "Fiscalização ambiental",
            "Compartilhamento de experiências", "Controle de desmatamento", "Rodízio urbano"
        ],
        "Situação": ["Em andamento"] * 6
    })
    st.dataframe(acoes)

# ======= Aba 3: Planos de Ação =======
elif aba == "Planos de Ação":
    st.title("📒 Planos de Ação para Seca")

    st.markdown("### Selecione os filtros:")
    col1, col2, col3, col4 = st.columns(4)
    with col1: estado_selecionado = st.selectbox("Estado de Seca", ["Todos", "Normal", "Severa"])
    with col2: problema = st.selectbox("Problemas", ["Todos", "Abastecimento", "Saúde", "Desmatamento"])
    with col3: impacto = st.selectbox("Tipo de Impacto", ["Todos", "Ambiental", "Social", "Econômico"])
    with col4: acao_tipo = st.selectbox("Ações", ["Todos", "Gestão", "Infraestrutura", "Social"])

    st.markdown("### 📋 Ações Planejadas")
    tabela_planos = pd.DataFrame({
        "Descrição da Ação": ["Irrigação eficiente", "Fontes alternativas", "Tratamento da água"],
        "Classe da Ação": ["Operação e gestão", "Infraestrutura", "Social"],
        "Responsáveis": ["Cogerh, Comitê", "SOHIDRA", "SAAE, SISAR"]
    })
    st.dataframe(tabela_planos)

# ======= Aba 4: Impacto das Secas na Região =======
elif aba == "Impacto das Secas na Região":
    st.title("🌾 Impactos das Secas na Região")

    st.markdown("""
    O Hidrossistema Patu, em Senador Pompeu (CE), enfrenta desafios severos em períodos de seca.  
    A participação da população é essencial para identificar impactos reais.
    """)
    st.markdown("👉 [**Acesse o formulário aqui**](#)")

    st.subheader("📊 Principais Impactos")
    st.image("https://img.icons8.com/color/480/drought.png", width=100)
    st.markdown("""
    - 🔥 Ambientais: redução dos estoques de água  
    - 💰 Econômicos: prejuízos na produção agrícola  
    - 👨‍👩‍👧‍👦 Sociais: aumento da pobreza e insegurança hídrica
    """)

# ======= Aba 5: Usos do Hidrossistema =======
elif aba == "Usos do Hidrossistema":
    st.title("💧 Usos do Hidrossistema Patu")

    st.markdown("### Diagrama de Usos")
    st.markdown("CAGECE, COSENA, Irrigação, Comunidades SISAR, SAAE")

    st.markdown("### Vazão Operada")
    st.markdown("**Em Condições de Normalidade:**")
    st.bar_chart(pd.Series([40, 16, 3, 20, 400, 1], index=["CAGECE", "SAAE", "SISAR", "Montante", "Jusante", "COSENA"]))

    st.markdown("**Em Condições de Escassez:**")
    st.bar_chart(pd.Series([40, 16, 3, 10, 50, 1], index=["CAGECE", "SAAE", "SISAR", "Montante", "Jusante", "COSENA"]))

# ======= Aba 6: Balanço Hídrico =======
elif aba == "Balanço Hídrico":
    st.title("📉 Balanço Hídrico do Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Oferta Hídrica Estimada")
        fig1 = px.bar(x=["Q90", "Q95", "Q98"], y=[688.8, 520.8, 400.2], labels={"x": "Nível de Garantia", "y": "Oferta (l/s)"})
        st.plotly_chart(fig1)

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


