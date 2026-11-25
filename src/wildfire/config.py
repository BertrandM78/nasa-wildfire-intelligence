"""Chemins et constantes partagés par tous les modules."""
from pathlib import Path

# Racine du projet (…/nasa-wildfire-intelligence)
ROOT = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT / "data" / "raw"
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

ARCHIVE_FILE = DATA_RAW / "fire_archive_M6_156000.csv.gz"
NRT_FILE = DATA_RAW / "fire_nrt_M6_156000.csv.gz"

# Dataset externe : limites des États (US Census Bureau, 2018, 1:20M)
# Source : https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip
STATES_FILE = DATA_EXTERNAL / "cb_2018_us_state_20m.zip"

# Données nettoyées et enrichies (cache régénéré par le notebook)
CLEAN_FILE = DATA_PROCESSED / "fires_clean.parquet"

DATASET_NAME = "NASA FIRMS — MODIS Collection 6 Active Fires (USA, 2010-2020)"
