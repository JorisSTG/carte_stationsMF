# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 10:42:39 2026

@author: joris
"""

import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================

BASE_DIR = Path("annees_typique")
STATION_FILE = Path("stations-meteo-france.csv")
OUTPUT_FILE = Path("trie/stations_typiques_coordonnees.csv")

# =========================
# FONCTION DE NETTOYAGE (IDENTIQUE À TON CODE)
# =========================

def sanitize_station_name(name: str) -> str:
    name = str(name).upper()
    for c in ["/", "\\", " ", "\t"]:
        name = name.replace(c, "_")
    name = "".join(c for c in name if c.isalnum() or c == "_")
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")

# =========================
# 1) LECTURE DU FICHIER STATIONS
# =========================

df = pd.read_csv(STATION_FILE, sep=",", encoding="utf-8", low_memory=False)

df["NOM_CLEAN"] = df["name"].apply(sanitize_station_name)

df = df[[
    "id",
    "lon",
    "lat",
    "alt",
    "department_id",
    "NOM_CLEAN"
]]

station_dict = {
    row["NOM_CLEAN"]: (
        row["id"],
        row["lon"],
        row["lat"],
        row["alt"],
        row["department_id"]
    )
    for _, row in df.iterrows()
}

print("✔ Stations chargées :", len(station_dict))

# =========================
# 2) PARCOURS DES DOSSIERS
# =========================

results = []

for station_folder in BASE_DIR.iterdir():
    if not station_folder.is_dir():
        continue

    station_name = station_folder.name  # le nom du dossier = nom de la station

    if station_name in station_dict:
        sid, lon, lat, alt, dep = station_dict[station_name]
    else:
        print("❌ station non trouvée :", station_name)
        sid, lon, lat, alt, dep = None, None, None, None, None

    results.append([
        station_name,
        sid,
        lon,
        lat,
        alt,
        dep
    ])

# =========================
# 3) SAUVEGARDE
# =========================

out_df = pd.DataFrame(
    results,
    columns=[
        "station",
        "id",
        "longitude",
        "latitude",
        "altitude",
        "departement"
    ]
)

out_df.to_csv(OUTPUT_FILE, index=False)

print("\n✔ Fichier créé :", OUTPUT_FILE)
