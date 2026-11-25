"""Phase 1 — exploration / résumé du dataset (tâche 1 du barème)."""
import matplotlib.pyplot as plt
import numpy as np
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


# ---------------------------------------------------------------------------
# Graphiques d'exploration
# ---------------------------------------------------------------------------
# Function: plot_frp_distribution
# Histogramme de la Fire Radiative Power (intensité du feu, en MW).
# Échelle log sur l'axe x car la distribution est très asymétrique
# (médiane ~23 MW, mais quelques feux dépassent 10 000 MW).
# Input:  df (DataFrame) avec une colonne `frp`
# Output: figure matplotlib
def plot_frp_distribution(df):
    frp = df.loc[df["frp"] > 0, "frp"]  # log impossible pour frp <= 0 (cas traités en phase 2)
    bins = np.logspace(np.log10(frp.min()), np.log10(frp.max()), 60)  # classes régulières en échelle log
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(frp, bins=bins, color="#d95f02")
    ax.set_xscale("log")
    ax.axvline(frp.median(), color="black", ls="--", label=f"médiane = {frp.median():.0f} MW")
    ax.set(xlabel="FRP (MW, échelle log)", ylabel="Nombre de détections",
           title="Distribution de l'intensité des feux (FRP)")
    ax.legend()
    fig.tight_layout()
    return fig


# Function: plot_monthly_detections
# Nombre de détections par mois, en distinguant archive et NRT,
# pour visualiser la saisonnalité et la couverture temporelle.
# Input:  df (DataFrame) avec les colonnes `acq_date` et `source`
# Output: figure matplotlib
def plot_monthly_detections(df):
    month = pd.to_datetime(df["acq_date"]).dt.to_period("M").dt.to_timestamp()  # 1er jour du mois
    counts = df.groupby([month.rename("month"), "source"]).size().unstack("source")
    fig, ax = plt.subplots(figsize=(11, 4))
    for source, color in [("archive", "#1b9e77"), ("nrt", "#d95f02")]:
        if source in counts:
            ax.plot(counts.index, counts[source], color=color, label=source)
    ax.set(xlabel="Mois", ylabel="Nombre de détections",
           title="Détections de points chauds par mois (2010-09 → 2020-09)")
    ax.legend(title="Fichier")
    fig.tight_layout()
    return fig


# Function: plot_spatial_distribution
# Carte des détections (longitude / latitude), colorées par `type`.
# Les 1,25 M points sont tracés en très petit et semi-transparents.
# Input:  df (DataFrame) avec `latitude`, `longitude`, `type`
#         sample (int | None) — nombre de points tirés au hasard (None = tous)
# Output: figure matplotlib
def plot_spatial_distribution(df, sample=None):
    if sample is not None and sample < len(df):
        df = df.sample(sample, random_state=42)  # graine fixe : figure reproductible
    # Ordre de tracé : du plus fréquent au plus rare, pour que les types rares
    # (volcans, sources statiques, offshore) ne soient pas masqués par la végétation.
    # (type, libellé, couleur, taille du point)
    layers = [
        (0, "0 végétation", "#1b9e77", 0.2),
        (None, "NRT (type inconnu)", "grey", 0.2),  # None = lignes NRT sans colonne type
        (2, "2 source statique", "#7570b3", 1.0),
        (1, "1 volcan", "#e7298a", 3.0),
        (3, "3 offshore", "#1f78b4", 3.0),
    ]
    fig, ax = plt.subplots(figsize=(11, 6))
    for t, label, color, size in layers:
        sub = df[df["type"].isna()] if t is None else df[df["type"] == t]
        ax.scatter(sub["longitude"], sub["latitude"], s=size, alpha=0.4, color=color,
                   label=f"{label} ({len(sub):,})".replace(",", " "),
                   rasterized=True)  # rasterized : fichier léger malgré le nombre de points
    ax.set(xlabel="Longitude", ylabel="Latitude", title="Localisation des détections par type")
    ax.legend(markerscale=6, loc="upper right")  # coin vide (océan), ne masque ni Hawaï ni l'Alaska
    fig.tight_layout()
    return fig
