import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path

st.set_page_config(page_title="Carte des stations", layout="wide")
st.title("🗺️ Carte des stations Météo-France")

# ---------- CONFIG ----------
ALL_STATIONS_FILE = Path("stations_coordonnees_tout.csv")  # CSV complet toutes stations
BASE_DIR = Path("sortie_par_annees")                            # dossiers par année
TYPICAL_FILE = Path("stations_typiques_coordonnees.csv")       # CSV stations typiques

# ---------- CHOIX DU MODE ----------
mode = st.selectbox(
    "Afficher :",
    ["Année", "Typique", "Toutes les stations"]
)

# ---------- CHARGEMENT DU CSV ----------
if mode == "Année":
    year = st.selectbox("Choisir l'année :", options=list(range(2000, 2020)))
    csv_file = BASE_DIR / f"stations_{year}.csv"
elif mode == "Typique":
    csv_file = TYPICAL_FILE
else:  # Toutes les stations
    csv_file = ALL_STATIONS_FILE

if not csv_file.exists():
    st.warning(f"⚠️ Fichier introuvable : {csv_file}")
    st.stop()

df = pd.read_csv(csv_file)

# Colonnes attendues
if mode == "Toutes les stations":
    required_cols = ["station", "longitude", "latitude", "altitude", "departement", "id", "annees", "typique"]
else:
    required_cols = ["station", "longitude", "latitude", "altitude", "departement", "id"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Colonne manquante dans le CSV : {col}")
        st.stop()

df_map = df[required_cols].dropna()

# ---------- BARRE DE RECHERCHE ----------
st.subheader("🔎 Rechercher une station")
search = st.text_input("Nom de la station :", "")

# ---------- COUCHE PRINCIPALE ----------
layer_all = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=1000,
    get_fill_color=[200, 30, 0, 255],  # rouge opaque
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
if search:
    df_search = df_map[df_map["station"].str.contains(search, case=False, na=False)]
    if not df_search.empty:
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
            get_fill_color=[30, 100, 255, 255],  # bleu opaque pour la station trouvée
            pickable=True,
        )

        layers.append(layer_selected)
    else:
        st.warning("❌ Station non trouvée")

# ---------- TOOLTIP ----------
if mode == "Toutes les stations":
    tooltip = {
        "html": """
        <b>ID :</b> {id} <br/>
        <b>Nom :</b> {station} <br/>
        <b>Département :</b> {departement} <br/>
        <b>Longitude :</b> {longitude} <br/>
        <b>Latitude :</b> {latitude} <br/>
        <b>Altitude :</b> {altitude} m <br/>
        <b>Années :</b> {annees} <br/>
        <b>Typique :</b> {typique}
        """,
        "style": {"backgroundColor": "white", "color": "black"}
    }
else:
    tooltip = {
        "html": """
        <b>ID :</b> {id} <br/>
        <b>Nom :</b> {station} <br/>
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

st.pydeck_chart(deck, height=800)
