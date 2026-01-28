import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path

st.set_page_config(page_title="Carte des stations", layout="wide")
st.title("🗺️ Carte des stations Météo-France")

# ---------- CONFIG ----------
BASE_DIR = Path("sortie_par_annee")  # dossier contenant tous les CSV par année
TYPICAL_DIR = Path("stations_typiques")  # dossier contenant stations typiques

# ---------- CHOIX DU TYPE ----------
station_type = st.selectbox(
    "Afficher :",
    ["Toutes les stations", "Stations typiques"]
)

# ---------- CHOIX DE L'ANNÉE ----------
if station_type == "Toutes les stations":
    year = st.selectbox("Choisir l'année :", options=list(range(2000, 2020)))
    csv_file = BASE_DIR / f"stations_{year}.csv"
else:
    # Pour les stations typiques, on suppose un seul CSV
    csv_file = TYPICAL_DIR / "stations_typiques_coordonnees.csv"

if not csv_file.exists():
    st.warning(f"⚠️ Fichier introuvable : {csv_file}")
    st.stop()

# ---------- CHARGEMENT DES DONNÉES ----------
df = pd.read_csv(csv_file)

# Colonnes attendues
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
