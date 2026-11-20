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

DATASET_NAME = "NASA FIRMS — MODIS Collection 6 Active Fires (USA, 2010-2020)"
