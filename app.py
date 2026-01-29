import streamlit as st
import pandas as pd
import pydeck as pdk
from pathlib import Path

st.set_page_config(page_title="Carte des stations", layout="wide")
st.title("🗺️ Carte des stations Météo-France")

# ---------- CONFIG ----------
ALL_STATIONS_FILE = Path("stations_coordonnees_tout.csv")
BASE_DIR = Path("sortie_par_annees")
TYPICAL_FILE = Path("stations_typiques_coordonnees.csv")
FRANCE_DIR = Path("FRANCE")

# ---------- CHOIX DU MODE ----------
mode = st.selectbox("Afficher :", ["Année", "Typique", "Toutes les stations"])

# ---------- CHOIX DU CSV ----------
year = None

if mode == "Année":
    year = st.selectbox("Choisir l'année :", list(range(2000, 2020)))
    csv_file = BASE_DIR / f"stations_{year}.csv"
elif mode == "Typique":
    csv_file = TYPICAL_FILE
else:
    csv_file = ALL_STATIONS_FILE

if not csv_file.exists():
    st.error(f"Fichier introuvable : {csv_file}")
    st.stop()

df = pd.read_csv(csv_file)

# ---------- COLONNES ----------
if mode == "Toutes les stations":
    required_cols = ["station", "longitude", "latitude", "altitude", "departement", "id", "annees", "typique"]
else:
    required_cols = ["station", "longitude", "latitude", "altitude", "departement", "id"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Colonne manquante : {col}")
        st.stop()

df_map = df[required_cols].dropna()

# ---------- RECHERCHE ----------
st.subheader("🔎 Rechercher une station")
search = st.text_input("Nom de la station :", "")

df_search = pd.DataFrame()
if search:
    df_search = df_map[df_map["station"].str.contains(search, case=False, na=False)]

# ---------- SÉLECTION ----------
selected_station = None

if not df_search.empty:
    selected_station = df_search.iloc[0]["station"]
    st.success(f"Station sélectionnée : {selected_station}")

elif mode == "Année":
    selected_station = st.selectbox(
        "Ou choisir une station :",
        sorted(df_map["station"].unique())
    )

# ---------- CARTE ----------
layer_all = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=1500,
    get_fill_color=[200, 30, 0, 255],
    pickable=True,
)

layers = [layer_all]

view_state = pdk.ViewState(latitude=46.6, longitude=2.2, zoom=5)

if not df_search.empty:
    lat = df_search.iloc[0]["latitude"]
    lon = df_search.iloc[0]["longitude"]

    view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=9)

    layer_selected = pdk.Layer(
        "ScatterplotLayer",
        data=df_search,
        get_position='[longitude, latitude]',
        get_radius=3500,
        get_fill_color=[30, 100, 255, 255],
        pickable=True,
    )

    layers.append(layer_selected)

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

# ---------- AFFICHAGE CARTE ----------
deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip=tooltip)
st.pydeck_chart(deck, height=750)

# ---------- TÉLÉCHARGEMENT ----------
if mode == "Année" and selected_station is not None:

    file_path = FRANCE_DIR / str(year) / f"{selected_station}.csv"

    st.markdown("---")
    st.subheader("⬇️ Téléchargement")

    if file_path.exists():
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"Télécharger {file_path.name}",
                data=f,
                file_name=file_path.name,
                mime="text/csv"
            )
    else:
        st.error(f"Fichier introuvable : {file_path}")
