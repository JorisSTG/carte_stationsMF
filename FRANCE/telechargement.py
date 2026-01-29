#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 09:53:39 2026

@author: saint-genesj
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import shutil
import requests
import pandas as pd
from pathlib import Path
import tempfile
import time

#lien internet : https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires


# ============================================================
# CONFIGURATION
# ============================================================

PERIODES = [
    ("2000-2009", range(2000, 2010)),
    ("2010-2019", range(2010, 2020)),
]

TARGET_YEARS = list(range(2000, 2020))

URL_TEMPLATE = (
    "https://object.files.data.gouv.fr/meteofrance/data/"
    "synchro_ftp/BASE/HOR/H_{dept}_{periode}.csv.gz"
)

CHUNKSIZE = 200_000

DATETIME_COL = "AAAAMMJJHH"
STATION_COL = "NOM_USUEL"
TEMP_COL = "T"

OUTPUT_BASE = Path.cwd()

TMP_DIR = Path(tempfile.gettempdir()) / f"mf_tmp_{int(time.time())}"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# UTILITAIRES
# ============================================================

def sanitize_station_name(name: str) -> str:
    name = str(name).upper()
    for c in ["/", "\\", " ", "\t"]:
        name = name.replace(c, "_")
    name = "".join(c for c in name if c.isalnum() or c == "_")
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")


def find_period(year: int):
    for p, years in PERIODES:
        if year in years:
            return p
    return None

# ============================================================
# TELECHARGEMENT + DECOMPRESSION
# ============================================================

def download_and_decompress(dept: str, periode: str) -> Path:
    url = URL_TEMPLATE.format(dept=dept, periode=periode)
    gz_path = Path(f"H_{dept}_{periode}.csv.gz")

    print(f"Téléchargement {gz_path.name}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    with open(gz_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)

    csv_path = gz_path.with_suffix("")
    with gzip.open(gz_path, "rb") as f_in, open(csv_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    gz_path.unlink()
    return csv_path

# ============================================================
# CSV -> FICHIERS TEMPORAIRES (STRICT)
# ============================================================

def process_csv_to_temp(csv_path: Path, dept: str):
    reader = pd.read_csv(
        csv_path,
        sep=";",
        chunksize=CHUNKSIZE,
        low_memory=True
    )

    tmp_files = set()

    for chunk in reader:
        # renommage + forçage string (corrige définitivement l'erreur .str)
        chunk = chunk.rename(columns={DATETIME_COL: "dt"})
        chunk["dt"] = chunk["dt"].astype(str)

        # année
        chunk["year"] = chunk["dt"].str[:4].astype(int)
        chunk = chunk[chunk["year"].isin(TARGET_YEARS)]
        if chunk.empty:
            continue

        # suppression 29 février
        chunk = chunk[~(chunk["dt"].str[4:8] == "0229")]
        if chunk.empty:
            continue

        # température strictement valide
        chunk[TEMP_COL] = pd.to_numeric(chunk[TEMP_COL], errors="coerce")
        chunk = chunk.dropna(subset=[TEMP_COL])
        if chunk.empty:
            continue

        chunk[STATION_COL] = chunk[STATION_COL].str.upper()

        # écriture : 1 ligne = 1 température
        for (station, year), g in chunk.groupby([STATION_COL, "year"]):
            fname = f"tmp_{year}_{dept}_{sanitize_station_name(station)}.csv"
            fpath = TMP_DIR / fname

            g[TEMP_COL].to_csv(
                fpath,
                mode="a",
                index=False,
                header=False
            )

            tmp_files.add(fpath)

    return tmp_files

# ============================================================
# TEMP -> CSV FINAL (TEST 8760 STRICT)
# ============================================================

def temp_to_final(csv_tmp: Path):
    parts = csv_tmp.name.split("_")
    year = parts[1]
    station = "_".join(parts[3:]).replace(".csv", "")

    df = pd.read_csv(csv_tmp, header=None)

    # CRITÈRE UNIQUE ET STRICT
    if len(df) != 8760:
        print(f"❌ rejet {station} {year} ({len(df)} valeurs)")
        return

    out_dir = OUTPUT_BASE / year
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{station}.csv"
    df.to_csv(out_path, index=False, header=False)

    print(f"✔ écrit {out_path}")

# ============================================================
# PIPELINE PAR DÉPARTEMENT
# ============================================================

def process_department(dept: str):
    periodes = sorted({find_period(y) for y in TARGET_YEARS})

    for p in periodes:
        csv_path = download_and_decompress(dept, p)
        try:
            tmp_files = process_csv_to_temp(csv_path, dept)

            for tmp in tmp_files:
                temp_to_final(tmp)
                tmp.unlink()

        finally:
            csv_path.unlink(missing_ok=True)

# ============================================================
# MAIN
# ============================================================

def main():
    deps = input("Départements (ex: 67,68 ou 'ALL') : ").strip()

    if deps.upper() == "ALL":
        Liste_dept = [k for k in range (1,95+1)] + [971,972,973,974,975,984,986,987,988] 
        print(Liste_dept)
        deps = [f"{i:02d}" for i in Liste_dept]
    else:
        deps = [d.strip().zfill(2) for d in deps.split(",")]

    for dept in deps:
        print(f"\n=== Département {dept} ===")
        process_department(dept)

    try:
        TMP_DIR.rmdir()
    except Exception:
        pass

    print("\nTerminé.")

if __name__ == "__main__":
    main()