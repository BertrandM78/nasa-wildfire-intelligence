"""Phase 2 — nettoyage des détections."""
import pandas as pd

# Seuil de confiance par défaut : FIRMS classe les détections MODIS en
# "faible" (< 30 %), "nominale" (30–79 %) et "haute" (>= 80 %).
MIN_CONFIDENCE = 30

# Colonnes retirées et pourquoi (voir drop_useless_columns)
USELESS_COLUMNS = {
    "instrument": "toujours 'MODIS' : n'apporte aucune information",
    "version": "redondant avec `source` (6.03 = archive, 6.0NRT = nrt)",
    "type": "toujours 0 après le filtre végétation",
    "acq_time": "fusionné avec acq_date dans `acq_datetime`",
}


# Function: infer_nrt_type
# Le fichier NRT n'a pas de colonne `type`. On la reconstitue à partir de l'archive :
# si une détection NRT tombe dans une case de ~1 km où l'archive a déjà vu un volcan,
# une source statique ou une plateforme offshore, elle reçoit ce type ; sinon type 0.
# Input:  df (DataFrame fusionné archive + nrt, colonnes `latitude`, `longitude`, `type`, `source`)
#         decimals (int) — arrondi des coordonnées définissant la case (2 décimales ≈ 1 km)
# Output: DataFrame avec `type` rempli pour les lignes NRT
def infer_nrt_type(df, decimals=2):
    df = df.copy()
    cell = df["latitude"].round(decimals).astype(str) + "_" + df["longitude"].round(decimals).astype(str)
    # Type non-végétation le plus fréquent observé dans chaque case de l'archive
    known = df["source"].eq("archive") & df["type"].ne(0)
    cell_type = df.loc[known, "type"].groupby(cell[known]).agg(lambda s: s.mode().iloc[0])
    is_nrt = df["source"].eq("nrt")
    # Case connue -> type de l'archive ; case inconnue -> 0 (végétation)
    df.loc[is_nrt, "type"] = cell[is_nrt].map(cell_type).fillna(0)
    df["type"] = df["type"].astype(int)
    return df


# Function: filter_vegetation
# Ne garde que les feux de végétation (type 0), sujet du projet.
# Input:  df (DataFrame avec `type` complet)
# Output: DataFrame filtré
def filter_vegetation(df):
    return df[df["type"] == 0]


# Function: remove_invalid_frp
# Retire les détections dont l'intensité (FRP) vaut 0 ou est négative :
# une puissance négative est impossible, et 0 signifie que la FRP n'a pas été calculée.
# Input:  df (DataFrame)
# Output: DataFrame avec frp > 0
def remove_invalid_frp(df):
    return df[df["frp"] > 0]


# Function: filter_confidence
# Retire les détections de faible confiance (fausses alertes probables).
# Input:  df (DataFrame), min_confidence (int, %) — seuil minimum conservé
# Output: DataFrame avec confidence >= min_confidence
def filter_confidence(df, min_confidence=MIN_CONFIDENCE):
    return df[df["confidence"] >= min_confidence]


# Function: add_time_features
# Crée une vraie date-heure UTC et des colonnes temporelles utiles aux requêtes.
# Input:  df (DataFrame avec `acq_date` "AAAA-MM-JJ" et `acq_time` "HHMM")
# Output: DataFrame avec acq_datetime, year, month, season
def add_time_features(df):
    df = df.copy()
    df["acq_datetime"] = pd.to_datetime(df["acq_date"] + " " + df["acq_time"],
                                        format="%Y-%m-%d %H%M", utc=True)
    df["acq_date"] = df["acq_datetime"].dt.normalize().dt.tz_localize(None)  # date seule, type datetime
    df["year"] = df["acq_datetime"].dt.year
    df["month"] = df["acq_datetime"].dt.month
    # Saisons météorologiques de l'hémisphère Nord (déc-jan-fév = hiver, etc.)
    seasons = {12: "hiver", 1: "hiver", 2: "hiver", 3: "printemps", 4: "printemps", 5: "printemps",
               6: "été", 7: "été", 8: "été", 9: "automne", 10: "automne", 11: "automne"}
    df["season"] = df["month"].map(seasons)
    return df


# Function: drop_useless_columns
# Supprime les colonnes qui n'apportent plus d'information (raisons dans USELESS_COLUMNS).
# Input:  df (DataFrame)
# Output: DataFrame sans ces colonnes
def drop_useless_columns(df):
    return df.drop(columns=[c for c in USELESS_COLUMNS if c in df.columns])


# Function: clean_data
# Enchaîne toutes les étapes de nettoyage et note le nombre de lignes après chacune.
# Input:  df (DataFrame brut fusionné), min_confidence (int, %)
# Output: (DataFrame nettoyé, DataFrame-journal des étapes : lignes restantes / retirées)
def clean_data(df, min_confidence=MIN_CONFIDENCE):
    log = [("Données brutes (archive + NRT)", len(df))]
    df = infer_nrt_type(df)
    df = filter_vegetation(df);                     log.append(("Feux de végétation uniquement (type 0)", len(df)))
    df = remove_invalid_frp(df);                    log.append(("FRP > 0", len(df)))
    df = filter_confidence(df, min_confidence);     log.append((f"Confiance >= {min_confidence} %", len(df)))
    df = add_time_features(df)
    df = drop_useless_columns(df).reset_index(drop=True)
    log = pd.DataFrame(log, columns=["étape", "lignes restantes"])
    log["lignes retirées"] = (-log["lignes restantes"].diff()).fillna(0).astype(int)
    return df, log
