"""Phase 2 — enrichissement géographique avec un dataset externe :
limites des États US (US Census Bureau, cartographic boundary files 2018, 1:20 000 000)."""
import geopandas as gpd
import pandas as pd

# Régions officielles du US Census Bureau (Alaska et Hawaï font partie de "West")
CENSUS_REGIONS = {
    "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
    "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South": ["DE", "DC", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN",
              "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}


# Function: load_states
# Charge les polygones des États américains.
# Input:  file_path (str | Path) — shapefile zippé du Census
# Output: GeoDataFrame (state = code à 2 lettres, state_name, geometry) en WGS84
def load_states(file_path):
    states = gpd.read_file(file_path)[["STUSPS", "NAME", "geometry"]]
    states = states.rename(columns={"STUSPS": "state", "NAME": "state_name"})
    return states.to_crs("EPSG:4326")  # même système de coordonnées que les données FIRMS


# Function: add_state
# Associe chaque détection à l'État qui la contient (jointure spatiale).
# Les contours du Census sont simplifiés : quelques points côtiers tombent juste
# à l'extérieur. Ils sont rattachés à l'État le plus proche s'il est à moins de max_km.
# Input:  df (DataFrame avec latitude/longitude), states (GeoDataFrame de load_states),
#         max_km (float) — distance maximale pour le rattachement des points côtiers
# Output: DataFrame avec les colonnes `state` et `state_name` (NaN si hors des États)
def add_state(df, states, max_km=10):
    points = gpd.GeoDataFrame(df[[]], geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                              crs="EPSG:4326")
    # 1) point à l'intérieur d'un État
    joined = gpd.sjoin(points, states, how="left", predicate="within")
    joined = joined[~joined.index.duplicated()]  # sécurité si un point touche deux polygones
    # 2) points non trouvés : État le plus proche, en projection métrique (Albers USA, EPSG:5070)
    missing = joined["state"].isna()
    if missing.any():
        near = gpd.sjoin_nearest(points[missing].to_crs("EPSG:5070"), states.to_crs("EPSG:5070"),
                                 how="left", max_distance=max_km * 1000)
        near = near[~near.index.duplicated()]
        joined.loc[missing, ["state", "state_name"]] = near[["state", "state_name"]]
    df = df.copy()
    df["state"] = joined["state"]
    df["state_name"] = joined["state_name"]
    return df


# Function: add_region
# Ajoute la grande région du Census (Northeast, Midwest, South, West) à partir de l'État.
# Input:  df (DataFrame avec `state`)
# Output: DataFrame avec la colonne `region`
def add_region(df):
    state_to_region = {s: r for r, codes in CENSUS_REGIONS.items() for s in codes}
    df = df.copy()
    df["region"] = df["state"].map(state_to_region)
    return df
