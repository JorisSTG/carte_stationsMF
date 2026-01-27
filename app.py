import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Carte des stations", layout="wide")

st.title("🗺️ Carte des stations du réseau Météo-France 🗺️")

# Charger le CSV depuis le repo GitHub
df = pd.read_csv("stations-meteo-france.csv")

# Sélection des colonnes par index
df_map = pd.DataFrame({
    "identifiant": df.iloc[:, 0],
    "nom": df.iloc[:, 1],
    "longitude": df.iloc[:, 6],
    "latitude": df.iloc[:, 7],
    "altitude": df.iloc[:, 8],
    "departement": df.iloc[:, 13],
})

df_map = df_map.dropna()


# Nettoyage (au cas où)
df_map = df_map.dropna()

# Carte pydeck
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=1000,
    get_fill_color=[200, 30, 0, 160],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=46.6,
    longitude=2.2,
    zoom=5,
)

tooltip = {
    "html": """
    <b>ID :</b> {identifiant} <br/>
    <b>Nom :</b> {nom} <br/>
    <b>Département :</b> {departement} <br/>
    <b>Longitude :</b> {longitude} <br/>
    <b>Latitude :</b> {latitude} <br/>
    <b>Altitude :</b> {altitude} m
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black"
    }
}


deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
)

st.pydeck_chart(deck)
