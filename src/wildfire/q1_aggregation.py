"""Q1 — Requête d'agrégation : activité des feux par État et par région."""
import plotly.express as px


# Function: aggregate_by_state
# Calcule, pour chaque État, trois indicateurs d'activité des feux :
#   - n_detections : nombre de détections (≈ surface touchée × durée)
#   - total_frp_gw : somme des FRP en gigawatts (≈ énergie totale dégagée)
#   - median_frp   : FRP médiane en MW (intensité d'un feu "typique")
#   - share_pct    : part de l'énergie nationale (%)
# Input:  df (DataFrame nettoyé avec `state`, `state_name`, `frp`)
# Output: DataFrame, une ligne par État, trié par énergie décroissante
def aggregate_by_state(df):
    agg = (df.groupby(["state", "state_name"])
             .agg(n_detections=("frp", "size"),     # nombre de lignes
                  total_frp=("frp", "sum"),         # somme des MW
                  median_frp=("frp", "median"))
             .reset_index())
    agg["total_frp_gw"] = (agg["total_frp"] / 1000).round(1)   # MW -> GW, plus lisible
    agg["share_pct"] = (agg["total_frp"] / agg["total_frp"].sum() * 100).round(1)
    agg["median_frp"] = agg["median_frp"].round(1)
    return agg.drop(columns="total_frp").sort_values("total_frp_gw", ascending=False).reset_index(drop=True)


# Function: aggregate_by_year_region
# Nombre de détections par année et par grande région.
# Input:  df (DataFrame nettoyé avec `year`, `region`)
# Output: DataFrame (year, region, n_detections)
def aggregate_by_year_region(df):
    return df.groupby(["year", "region"]).size().rename("n_detections").reset_index()


# Function: plot_state_map
# Carte des États colorés selon un indicateur.
# Input:  agg (DataFrame de aggregate_by_state), metric (str) — colonne à afficher
# Output: figure plotly
def plot_state_map(agg, metric="total_frp_gw"):
    titles = {"total_frp_gw": "Énergie cumulée des feux (GW)", "n_detections": "Nombre de détections"}
    fig = px.choropleth(agg, locations="state", locationmode="USA-states", scope="usa",
                        color=metric, color_continuous_scale="OrRd",
                        hover_name="state_name",
                        hover_data={"state": False, "n_detections": ":,", "total_frp_gw": ":,",
                                    "median_frp": True, "share_pct": True},
                        labels={metric: titles.get(metric, metric)})
    fig.update_layout(title=f"Q1 — {titles.get(metric, metric)} par État (2010-2020)",
                      margin=dict(l=0, r=0, t=50, b=0))
    return fig


# Function: plot_top_states
# Diagramme en barres des n États qui ont dégagé le plus d'énergie.
# Input:  agg (DataFrame de aggregate_by_state), n (int) — nombre d'États affichés
# Output: figure plotly
def plot_top_states(agg, n=10):
    top = agg.head(n).iloc[::-1]  # inversé : le 1er en haut du graphique
    fig = px.bar(top, x="total_frp_gw", y="state_name", orientation="h", text="share_pct",
                 labels={"total_frp_gw": "Énergie cumulée (GW)", "state_name": ""},
                 color_discrete_sequence=["#d95f02"])
    fig.update_traces(texttemplate="%{text} %", textposition="outside", cliponaxis=False)  # étiquette jamais coupée
    fig.update_layout(title=f"Q1 — Top {n} des États par énergie cumulée des feux")
    return fig


# Function: plot_year_region
# Barres empilées : nombre de détections par année, réparti par région.
# Input:  by_year (DataFrame de aggregate_by_year_region)
# Output: figure plotly
def plot_year_region(by_year):
    fig = px.bar(by_year, x="year", y="n_detections", color="region",
                 labels={"year": "Année", "n_detections": "Nombre de détections", "region": "Région"},
                 category_orders={"region": ["West", "South", "Midwest", "Northeast"]},
                 color_discrete_sequence=["#d95f02", "#1b9e77", "#7570b3", "#e7298a"])
    fig.update_layout(title="Q1 — Détections par année et par région "
                            "(2010 et 2020 incomplètes)")
    return fig
