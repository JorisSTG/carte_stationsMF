#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 12:59:06 2026

@author: saint-genesj
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
from pathlib import Path

# =========================
# PARAMÈTRES
# =========================

BASE_DIR = Path.cwd()  # dossier contenant les dossiers annuels
OUTPUT_DIR = BASE_DIR / "annees_typiques"
OUTPUT_DIR.mkdir(exist_ok=True)

TEMP_COL_INDEX = 0
EXPECTED_VALUES = 8760

MONTHS = ["Janvier","Fevrier","Mars","Avril","Mai","Juin",
          "Juillet","Aout","Septembre","Octobre","Novembre","Decembre"]

month_hours = [d*24 for d in [31,28,31,30,31,30,31,31,30,31,30,31]]

# =========================
# FONCTION ANNÉES TYPIQUES
# =========================

def generate_typical_years_full(temps_array, month_hours):
    n_years = temps_array.shape[0]
    typical_year, cold_winter_year, hot_summer_year = [], [], []

    start_idx = 0
    for month_idx, hours in enumerate(month_hours):
        end_idx = start_idx + hours
        month_slice = temps_array[:, start_idx:end_idx]
        month_mean = month_slice.mean(axis=1)

        idx_typical = np.argmin(np.abs(month_mean - np.median(month_mean)))
        typical_year.append(month_slice[idx_typical])

        if month_idx in [11,0,1]:
            idx_cold = np.argmin(month_mean)
            cold_winter_year.append(month_slice[idx_cold])
        else:
            cold_winter_year.append(month_slice[idx_typical])

        if month_idx in [5,6,7]:
            idx_hot = np.argmax(month_mean)
            hot_summer_year.append(month_slice[idx_hot])
        else:
            hot_summer_year.append(month_slice[idx_typical])

        start_idx = end_idx

    return (np.concatenate(typical_year),
            np.concatenate(cold_winter_year),
            np.concatenate(hot_summer_year))

# =========================
# 1️⃣ LISTE DES STATIONS
# =========================

stations_years = {}  # {station: {year: filepath}}

for year_dir in sorted(BASE_DIR.iterdir()):
    if not year_dir.is_dir():
        continue
    year = year_dir.name
    for csv_file in year_dir.glob("*.csv"):
        station_name = csv_file.stem.split("_")[0]
        stations_years.setdefault(station_name, {})[year] = csv_file

# =========================
# 2️⃣ TRAITEMENT DES STATIONS
# =========================

typical_years_used = {}
cold_years_used = {}
hot_years_used = {}

for station, year_files in stations_years.items():
    if len(year_files) < 10:
        continue

    print(f"=== Traitement station {station} ===")

    temps_array = []
    years_sorted = []

    for year in sorted(year_files.keys()):
        df = pd.read_csv(year_files[year], header=None)
        temps = df.iloc[:, TEMP_COL_INDEX].dropna().values
        if len(temps) == EXPECTED_VALUES:
            temps_array.append(temps)
            years_sorted.append(year)

    if len(temps_array) < 10:
        continue

    temps_array = np.array(temps_array)
    years_sorted = np.array(years_sorted)

    # Génération des séries horaires (inchangé)
    typical_year, cold_winter_year, hot_summer_year = generate_typical_years_full(temps_array, month_hours)

    station_dir = OUTPUT_DIR / station
    station_dir.mkdir(exist_ok=True)

    pd.DataFrame(typical_year).to_csv(station_dir / f"{station}_typique.csv", index=False, header=False)
    pd.DataFrame(cold_winter_year).to_csv(station_dir / f"{station}_hiver_froid.csv", index=False, header=False)
    pd.DataFrame(hot_summer_year).to_csv(station_dir / f"{station}_ete_chaud.csv", index=False, header=False)

    # =========================
    # Récupération des années mensuelles
    # =========================

    typical_years_used[station] = []
    cold_years_used[station] = []
    hot_years_used[station] = []

    start_idx = 0
    for month_idx, hours in enumerate(month_hours):
        end_idx = start_idx + hours
        month_slice = temps_array[:, start_idx:end_idx]
        month_mean = month_slice.mean(axis=1)

        idx_typical = np.argmin(np.abs(month_mean - np.median(month_mean)))

        typical_years_used[station].append(years_sorted[idx_typical])

        if month_idx in [11,0,1]:
            idx_cold = np.argmin(month_mean)
            cold_years_used[station].append(years_sorted[idx_cold])
        else:
            cold_years_used[station].append(years_sorted[idx_typical])

        if month_idx in [5,6,7]:
            idx_hot = np.argmax(month_mean)
            hot_years_used[station].append(years_sorted[idx_hot])
        else:
            hot_years_used[station].append(years_sorted[idx_typical])

        start_idx = end_idx

# =========================
# 3️⃣ EXPORT EXCEL
# =========================

df_typ = pd.DataFrame.from_dict(typical_years_used, orient="index", columns=MONTHS)
df_cold = pd.DataFrame.from_dict(cold_years_used, orient="index", columns=MONTHS)
df_hot = pd.DataFrame.from_dict(hot_years_used, orient="index", columns=MONTHS)

df_typ.to_excel(OUTPUT_DIR / "annees_sources_typique.xlsx")
df_cold.to_excel(OUTPUT_DIR / "annees_sources_hiver_froid.xlsx")
df_hot.to_excel(OUTPUT_DIR / "annees_sources_ete_chaud.xlsx")

print("\n✅ Terminé : CSV horaires + Excel des années sources générés.")