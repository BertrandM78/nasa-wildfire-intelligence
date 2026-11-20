"""Phase 1 — exploration / résumé du dataset (tâche 1 du barème)."""
import pandas as pd


# Function: dataset_shape
# Donne le nombre de lignes et de colonnes.
# Input:  df (DataFrame)
# Output: dict {"rows": int, "columns": int}
def dataset_shape(df):
    return {"rows": df.shape[0], "columns": df.shape[1]}


# Function: column_types
# Liste le type pandas de chaque colonne.
# Input:  df (DataFrame)
# Output: DataFrame (colonne, dtype)
def column_types(df):
    return df.dtypes.astype(str).rename("dtype").to_frame()


# Function: missing_values
# Compte les valeurs manquantes par colonne (absolu et en %).
# Input:  df (DataFrame)
# Output: DataFrame (colonne, n_missing, pct_missing)
def missing_values(df):
    n = df.isna().sum()
    return pd.DataFrame({"n_missing": n, "pct_missing": (n / len(df) * 100).round(2)})


# Function: value_ranges
# Plage de valeurs de chaque variable : min/max pour les numériques,
# modalités distinctes pour les catégorielles.
# Input:  df (DataFrame)
# Output: DataFrame (colonne, min, max, n_unique)
def value_ranges(df):
    rows = {}
    for col in df.columns:
        s = df[col].dropna()
        rows[col] = {
            "min": s.min() if len(s) else None,  # min/max fonctionnent aussi sur dates/texte (ordre lexical)
            "max": s.max() if len(s) else None,
            "n_unique": s.nunique(),
        }
    return pd.DataFrame(rows).T
