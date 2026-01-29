# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 11:07:16 2026

@author: joris
"""

import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================

BASE_DIR = Path("")
STATION_FILE = Path("stations-meteo-france.csv")
OUTPUT_DIR = Path("trie/trie_par_annee")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# FONCTION DE NETTOYAGE
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
# 2) PARCOURS DES DOSSIERS PAR ANNÉE
# =========================

for year in range(2000, 2020):
    folder = BASE_DIR / str(year)
    if not folder.exists():
        print("❌ dossier manquant :", folder)
        continue

    results = []

    for file in folder.glob("*.csv"):
        station_name = file.stem  # ✅ nom du fichier uniquement

        if station_name in station_dict:
            sid, lon, lat, alt, dep = station_dict[station_name]
        else:
            print("❌ station non trouvée :", station_name)
            sid, lon, lat, alt, dep = None, None, None, None, None

        results.append([
            file.stem,
            station_name,
            sid,
            lon,
            lat,
            alt,
            dep
        ])

    # ---------- SAUVEGARDE POUR L’ANNÉE ----------
    if results:
        out_df = pd.DataFrame(
            results,
            columns=[
                "nom_fichier",
                "station",
                "id",
                "longitude",
                "latitude",
                "altitude",
                "departement"
            ]
        )

        out_file = OUTPUT_DIR / f"stations_{year}.csv"
        out_df.to_csv(out_file, index=False)
        print(f"✔ Fichier créé pour {year} : {out_file}")
    else:
        print(f"⚠️ Aucun fichier pour l’année {year}")
