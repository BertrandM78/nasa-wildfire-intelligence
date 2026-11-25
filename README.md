# NASA Wildfire Intelligence

Projet final — *Programming for Data Science* (ESILV).
Analyse KDD des détections de feux actifs **NASA FIRMS / MODIS** sur les États-Unis (2010-09 → 2020-09) et dashboard de visualisation.

## Équipe
- Bertrand MAIGRE (chef d'équipe)
- Victor MICHELON
- Jean Baptiste PASTEAU
- Oscar DUJARDIN

## Dataset
| Fichier | Période | Lignes | Description |
|---|---|---|---|
| `data/raw/fire_archive_M6_156000.csv.gz` | 2010-09-27 → 2020-06-30 | ~1,18 M | MODIS C6 qualité standard (MCD14ML) |
| `data/raw/fire_nrt_M6_156000.csv.gz` | 2020-07-01 → 2020-09-27 | ~66 k | MODIS C6 Near Real-Time (MCD14DL) |

Dimensions : **temporelle** (`acq_date`, `acq_time`), **spatiale** (`latitude`, `longitude`, WGS84), **analytique** (`brightness`, `frp`, `confidence`, `daynight`, `satellite`, `type`…).
Documentation source : [`data/raw/FIRMS_README.md`](data/raw/FIRMS_README.md).

**Dataset externe** : limites des États américains, US Census Bureau 2018 (`data/external/cb_2018_us_state_20m.zip`, [source](https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip)). Sert à rattacher chaque détection à un État et à une région.

## Structure
```
data/raw/         données brutes NASA (non modifiées, compressées gzip)
data/external/    datasets externes (limites des États US, météo…)
data/processed/   cache parquet généré par le notebook (non versionné)
docs/             consignes du projet
notebooks/        notebook livrable (autonome : contient le code de toutes les fonctions)
src/wildfire/     code source par module (chargement, exploration, requêtes, dashboard)
scripts/          build_notebook.py (recopie src/ dans le notebook), run_dashboard.py
reports/          figures, export du dashboard, slides
```

## Code : `src/` et notebook
Le code est écrit dans `src/wildfire/` (un module par étape, plus simple pour travailler à plusieurs).
Le notebook livrable doit être **autonome** : `scripts/build_notebook.py` y recopie toutes les fonctions
(cellules « Function definitions ») et vérifie que chacune a son en-tête *Function / Input / Output*.

**Après toute modification d'un fichier de `src/wildfire/`** :
```bash
.venv/bin/python scripts/build_notebook.py
```
Seules les cellules générées (tag `generated`) sont remplacées ; le texte et les cellules de résultats ne sont pas touchés.

## Installation
```bash
python3.12 -m venv .venv        # Python 3.12 recommandé (compatibilité geopandas / statsmodels)
source .venv/bin/activate        # fish : source .venv/bin/activate.fish
pip install -r requirements.txt
jupyter notebook notebooks/
```

## Dashboard
- **Dans le notebook** : exécuter tout le notebook ; le bloc `main` final lance le dashboard sous la cellule.
- **Hors notebook** (démo) : `python scripts/run_dashboard.py`, puis ouvrir http://127.0.0.1:8050 (ou le port suivant s'il est déjà pris : l'adresse s'affiche au lancement). Ce script nécessite `data/processed/fires_clean.parquet`, créé par la section 2 du notebook.
- **Preuve de fonctionnement** : [`reports/Maigre_dashboard.html`](reports/Maigre_dashboard.html) (version statique, s'ouvre sans Python ni internet), [`reports/Maigre_dashboard.pdf`](reports/Maigre_dashboard.pdf) et [`reports/figures/dashboard_screenshot.png`](reports/figures/dashboard_screenshot.png).

## Avancement
- [x] 0. Setup — structure du repo, données rangées
- [x] 1. Chargement & exploration
- [x] 2. Nettoyage & enrichissement (dataset externe : États US)
- [x] 3. Requêtes — Q1 agrégation · Q2 motifs fréquents · Q3 prévision · Q4 clustering spatial
- [x] 4. Dashboard Dash + export HTML/PDF
- [x] 5. Notebook final autonome
- [ ] 6. Slides & répétition de la démo
