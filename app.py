import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Carte des stations", layout="wide")

st.title("🗺️ Carte des stations du réseau Météo-France")

# ---------- CHARGEMENT DES DONNÉES ----------
df = pd.read_csv("stations-meteo-france.csv")

df_map = pd.DataFrame({
    "identifiant": df.iloc[:, 0],
    "nom": df.iloc[:, 1],
    "longitude": df.iloc[:, 6],
    "latitude": df.iloc[:, 7],
    "altitude": df.iloc[:, 8],
    "departement": df.iloc[:, 13],
})

df_map = df_map.dropna()

# ---------- BARRE DE RECHERCHE ----------
st.subheader("🔎 Rechercher une station")
search = st.text_input("Nom de la station :", "")

# ---------- COUCHE PRINCIPALE (toutes les stations) ----------
layer_all = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=1000,
    get_fill_color=[200, 30, 0, 120],
    pickable=True,
)

layers = [layer_all]

# ---------- VUE PAR DÉFAUT ----------
view_state = pdk.ViewState(
    latitude=46.6,
    longitude=2.2,
    zoom=5,
)

# ---------- FILTRAGE ----------
df_search = df_map[df_map["nom"].str.contains(search, case=False, na=False)]

if search and not df_search.empty:
    lat = df_search.iloc[0]["latitude"]
    lon = df_search.iloc[0]["longitude"]

    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=9,
        pitch=0
    )

    layer_selected = pdk.Layer(
        "ScatterplotLayer",
        data=df_search,
        get_position='[longitude, latitude]',
        get_radius=1000,
        get_fill_color=[30, 100, 255, 200],  # 🔵 station trouvée
        pickable=True,
    )

    layers.append(layer_selected)

elif search:
    st.warning("❌ Station non trouvée")

# ---------- TOOLTIP ----------
tooltip = {
    "html": """
    <b>ID :</b> {identifiant} <br/>
    <b>Nom :</b> {nom} <br/>
    <b>Département :</b> {departement} <br/>
    <b>Longitude :</b> {longitude} <br/>
    <b>Latitude :</b> {latitude} <br/>
    <b>Altitude :</b> {altitude} m
    """,
    "style": {"backgroundColor": "white", "color": "black"}
}

# ---------- AFFICHAGE ----------
deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip=tooltip,
)

st.pydeck_chart(deck)
