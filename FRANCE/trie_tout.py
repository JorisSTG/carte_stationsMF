import pandas as pd
from pathlib import Path
import re

# =========================
# CONFIG
# =========================

BASE_DIR = Path("")
STATION_FILE = Path("stations-meteo-france.csv")
OUTPUT_FILE = Path("trie/stations_coordonnees_tout.csv")

# =========================
# FONCTION DE NETTOYAGE (identique à ton code)
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

df_stations = pd.read_csv(STATION_FILE, sep=",", encoding="utf-8", low_memory=False)
df_stations["NOM_CLEAN"] = df_stations["name"].apply(sanitize_station_name)

df_stations = df_stations[[
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
    for _, row in df_stations.iterrows()
}

print("✔ Stations chargées :", len(station_dict))

# =========================
# 2) PARCOURS DES DOSSIERS PAR ANNÉE
# =========================

station_years = {}

for year in range(2000, 2020):
    folder = BASE_DIR / str(year)
    if not folder.exists():
        print("❌ dossier manquant :", folder)
        continue

    for file in folder.glob("*.csv"):
        station_name = file.stem  # <-- correction ici

        if station_name not in station_years:
            station_years[station_name] = set()

        station_years[station_name].add(year)


# =========================
# 3) CRÉATION DU CSV FINAL
# =========================

results = []

for station_name, years in station_years.items():
    years_sorted = sorted(list(years))
    annees_str = ",".join(str(y) for y in years_sorted)
    typique = "oui" if len(years) > 10 else "non"

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
        dep,
        annees_str,
        typique
    ])

# ---------- SAUVEGARDE ----------
out_df = pd.DataFrame(
    results,
    columns=[
        "station",
        "id",
        "longitude",
        "latitude",
        "altitude",
        "departement",
        "annees",
        "typique"
    ]
)

out_df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✔ Fichier créé : {OUTPUT_FILE}")
