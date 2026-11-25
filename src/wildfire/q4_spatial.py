"""Q4 — Requête spatiale : regroupement des détections en foyers d'incendie (DBSCAN)."""
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0


# Function: select_points
# Choisit les détections à regrouper : une période courte et une confiance haute.
# Période courte : DBSCAN ne regarde que la position ; sur une année entière il fusionnerait
# des feux différents survenus au même endroit à des mois d'écart.
# Confiance haute (>= 80 %) : on ne garde que les points les plus fiables.
# Input:  df (DataFrame nettoyé), start / end (str "AAAA-MM-JJ", inclus), min_confidence (int, %)
# Output: DataFrame filtré
def select_points(df, start="2020-08-01", end="2020-09-30", min_confidence=80):
    mask = df["acq_date"].between(start, end) & (df["confidence"] >= min_confidence)
    return df[mask].reset_index(drop=True)


# Function: spatial_clustering
# DBSCAN avec la distance de haversine (distance réelle sur la sphère terrestre).
# Un foyer = un groupe d'au moins `min_samples` détections, chacune à moins de `eps_km`
# d'une autre. Les points isolés sont du "bruit" (cluster = -1).
# Input:  points (DataFrame avec latitude/longitude), eps_km (float), min_samples (int)
# Output: DataFrame avec la colonne `cluster`
def spatial_clustering(points, eps_km=5, min_samples=20):
    coords = np.radians(points[["latitude", "longitude"]].to_numpy())  # haversine attend des radians
    labels = DBSCAN(eps=eps_km / EARTH_RADIUS_KM,  # km -> angle en radians
                    min_samples=min_samples, metric="haversine", algorithm="ball_tree").fit_predict(coords)
    return points.assign(cluster=labels)


# Function: summarize_clusters
# Décrit chaque foyer : taille, énergie, dates, durée, position et État principal.
# Input:  clustered (DataFrame de spatial_clustering)
# Output: DataFrame, une ligne par foyer, trié par énergie décroissante
def summarize_clusters(clustered):
    c = clustered[clustered["cluster"] >= 0]
    summary = c.groupby("cluster").agg(
        n_detections=("frp", "size"),
        total_frp_gw=("frp", lambda s: s.sum() / 1000),
        start=("acq_date", "min"), end=("acq_date", "max"),
        latitude=("latitude", "mean"), longitude=("longitude", "mean"),
        state=("state", lambda s: s.mode().iloc[0]),  # État le plus représenté
    )
    summary["duration_days"] = (summary["end"] - summary["start"]).dt.days + 1
    summary = summary.round({"total_frp_gw": 1, "latitude": 2, "longitude": 2})
    summary = summary.sort_values("total_frp_gw", ascending=False).reset_index()
    summary.insert(0, "rank", range(1, len(summary) + 1))
    return summary


# Function: plot_clusters
# Carte interactive : les `top` foyers les plus énergétiques en couleur,
# les autres foyers en gris clair, le bruit masqué.
# Carte vectorielle (scatter_geo) : pas de fond de carte à télécharger ni de WebGL,
# donc elle s'affiche hors ligne, dans tout navigateur et dans les exports HTML/PDF.
# Le cadrage est calculé sur les `top` foyers, avec une marge de 2 degrés.
# Input:  clustered (DataFrame), summary (DataFrame de summarize_clusters), top (int)
# Output: figure plotly
def plot_clusters(clustered, summary, top=10):
    # Nom de chaque foyer : rang + État principal (celui du résumé, pas celui de chaque point)
    names = "#" + summary["rank"].astype(str) + " " + summary["state"]
    name_of = pd.Series(np.where(summary["rank"] <= top, names, "autres foyers"), index=summary["cluster"])
    pts = clustered[clustered["cluster"] >= 0].copy()
    pts["rank"] = pts["cluster"].map(summary.set_index("cluster")["rank"])
    pts["foyer"] = pts["cluster"].map(name_of)
    order = list(names.head(top))
    pts["date"] = pts["acq_date"].dt.strftime("%d/%m/%Y")  # date lisible au survol
    top_pts = pts[pts["rank"] <= top]
    fig = px.scatter_geo(pts.sort_values("rank", ascending=False), lat="latitude", lon="longitude",
                         color="foyer", category_orders={"foyer": order + ["autres foyers"]},
                         color_discrete_map={"autres foyers": "lightgrey"},
                         hover_data={"date": True, "frp": True, "foyer": False,
                                     "latitude": False, "longitude": False},
                         height=600)
    fig.update_traces(marker=dict(size=4, line=dict(width=0)))
    fig.update_geos(scope="north america", projection_type="mercator",
                    resolution=50, showsubunits=True, subunitcolor="#999",  # frontières des États
                    showland=True, landcolor="#f4f4f4", showlakes=False,
                    lonaxis_range=[top_pts["longitude"].min() - 2, top_pts["longitude"].max() + 2],
                    lataxis_range=[top_pts["latitude"].min() - 2, top_pts["latitude"].max() + 2])
    fig.update_layout(title=f"Q4 — Foyers d'incendie détectés par DBSCAN (top {top} en couleur)",
                      margin=dict(l=0, r=0, t=50, b=0))
    return fig
