import streamlit as st
import folium
from streamlit_folium import st_folium

st.title("📍 Identificação do Hidrossistema Patu")

st.markdown("""
O Hidrossistema Patu localiza-se em Senador Pompeu e foi o primeiro a contar com um Plano de Gestão de Seca no Ceará.
""")

st.markdown("### 🌍 Localização no Mapa")
map_patu = folium.Map(location=[-5.58, -39.40], zoom_start=10)
folium.Marker(location=[-5.58, -39.40], popup="Açude Patu").add_to(map_patu)
st_folium(map_patu, width=600)
