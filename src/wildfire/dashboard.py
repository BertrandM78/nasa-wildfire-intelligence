"""Phase 4 — dashboard Dash qui présente les résultats des 4 requêtes,
et export HTML statique (preuve de fonctionnement exigée par les consignes)."""
import socket

from dash import Dash, Input, Output, dcc, html

from wildfire import config
from wildfire.q1_aggregation import (aggregate_by_state, aggregate_by_year_region,
                                     plot_state_map, plot_top_states, plot_year_region)
from wildfire.q2_patterns import build_transactions, mine_rules, plot_rules
from wildfire.q3_forecast import (evaluate_forecast, fit_sarima, forecast, monthly_series,
                                  plot_forecast, split_train_test)
from wildfire.q4_spatial import plot_clusters, select_points, spatial_clustering, summarize_clusters

ORANGE = "#d95f02"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

# Textes de chaque section : question posée + comment lire les indicateurs
SECTIONS = {
    "q1": ("Q1 — Quels États brûlent le plus ?",
           "Agrégation par État. Énergie cumulée = somme des FRP (GW) : combine le nombre et la "
           "violence des feux. FRP médiane = intensité d'un feu typique."),
    "q2": ("Q2 — Quelles caractéristiques des feux vont ensemble ?",
           "Règles d'association (FP-Growth). Lift = combien de fois la conclusion est plus fréquente "
           "que d'habitude quand la condition est vraie (1 = aucun lien). Confiance = P(conclusion | condition)."),
    "q3": ("Q3 — Combien de feux le mois prochain ?",
           "Prévision SARIMA du nombre mensuel de détections. Testée sur oct. 2019 → sept. 2020, puis "
           "prévision des 12 mois suivants. Bande colorée = intervalle à 80 %. "
           "MAPE = erreur moyenne en %."),
    "q4": ("Q4 — Où étaient les grands foyers d'incendie en août-septembre 2020 ?",
           "Clustering DBSCAN (distance de haversine) des détections à confiance ≥ 80 %. "
           "Un foyer = au moins 20 détections, chacune à moins de « rayon » km d'une autre. "
           "Classement par énergie totale (GW)."),
}


# Function: compute_results
# Lance les 4 requêtes et regroupe tous leurs résultats dans un dictionnaire.
# Input:  df (DataFrame nettoyé de la section 2)
# Output: dict (tables et séries utilisées par le dashboard)
def compute_results(df):
    series = monthly_series(df)
    train, test = split_train_test(series)
    test_pred = forecast(fit_sarima(train), steps=len(test))
    comparison, mape = evaluate_forecast(series, test, test_pred)
    points = select_points(df)
    clustered = spatial_clustering(points)
    return {
        "df": df,
        "by_state": aggregate_by_state(df),
        "by_year_region": aggregate_by_year_region(df),
        "rules": mine_rules(build_transactions(df)),
        "series": series, "test_pred": test_pred, "comparison": comparison, "mape": mape,
        "future_pred": forecast(fit_sarima(series), steps=12),
        "points": points, "clustered": clustered, "clusters": summarize_clusters(clustered),
    }


# Function: compute_kpis
# Chiffres clés affichés en haut du dashboard.
# Input:  results (dict de compute_results)
# Output: liste de (libellé, valeur, détail)
def compute_kpis(results):
    df, by_state, series = results["df"], results["by_state"], results["series"]
    top = by_state.iloc[0]
    record = series.idxmax()
    return [
        ("Détections analysées", f"{len(df):,}".replace(",", " "), "feux de végétation, confiance ≥ 30 %"),
        ("Période", "2010 → 2020", f"{df['acq_date'].min():%d/%m/%Y} – {df['acq_date'].max():%d/%m/%Y}"),
        ("État le plus touché", top["state_name"], f"{top['share_pct']} % de l'énergie des feux"),
        ("Mois record", f"{record:%m/%Y}", f"{series.max():,} détections".replace(",", " ")),
    ]


# Function: df_to_table
# Convertit un DataFrame en tableau HTML simple (composants Dash).
# Input:  df (DataFrame), max_rows (int)
# Output: html.Table
def df_to_table(df, max_rows=10):
    cell = {"padding": "4px 10px", "borderBottom": "1px solid #ddd", "textAlign": "right"}
    head = html.Tr([html.Th(c, style={**cell, "background": "#f3f3f3"}) for c in df.columns])
    rows = [html.Tr([html.Td(str(v), style=cell) for v in row])
            for row in df.head(max_rows).itertuples(index=False)]
    return html.Table([html.Thead(head), html.Tbody(rows)],
                      style={"borderCollapse": "collapse", "fontSize": "13px", "margin": "8px 0"})


# Function: card
# Petite carte d'indicateur (titre, grande valeur, détail).
# Input:  label (str), value (str), detail (str)
# Output: html.Div
def card(label, value, detail):
    return html.Div([
        html.Div(label, style={"fontSize": "12px", "color": "#666", "textTransform": "uppercase"}),
        html.Div(value, style={"fontSize": "26px", "fontWeight": 600, "color": ORANGE}),
        html.Div(detail, style={"fontSize": "12px", "color": "#666"}),
    ], style={"flex": "1 1 200px", "background": "white", "borderRadius": "8px",
              "padding": "14px 16px", "boxShadow": "0 1px 3px rgba(0,0,0,.12)"})


# Function: section
# Bloc d'une requête : titre, explication des indicateurs, puis contenu.
# Input:  key (str, clé de SECTIONS), children (liste de composants)
# Output: html.Section
def section(key, children):
    title, text = SECTIONS[key]
    return html.Section([
        html.H2(title, style={"marginBottom": "4px"}),
        html.P(text, style={"color": "#555", "marginTop": 0, "maxWidth": "1000px"}),
        *children,
    ], id=key, style={"background": "white", "borderRadius": "8px", "padding": "16px 20px",
                      "margin": "16px 0", "boxShadow": "0 1px 3px rgba(0,0,0,.12)"})


# Function: build_header
# En-tête : titre du projet, nom du dataset, membres de l'équipe, lien GitHub.
# Input:  aucun
# Output: html.Header
def build_header():
    return html.Header([
        html.H1("NASA Wildfire Intelligence", style={"margin": "0 0 4px"}),
        html.Div([html.B("Dataset : "), config.DATASET_NAME]),
        html.Div([html.B("Dataset externe : "), config.EXTERNAL_DATASET_NAME]),
        html.Div([html.B("Équipe : "), " · ".join(config.TEAM)]),
        html.A("Dépôt GitHub", href=config.GITHUB_URL, target="_blank", style={"color": "white"}),
        html.Nav([html.A(SECTIONS[k][0].split(" — ")[0], href=f"#{k}",
                         style={"color": "white", "marginRight": "16px", "fontWeight": 600})
                  for k in SECTIONS], style={"marginTop": "8px"}),
    ], style={"background": ORANGE, "color": "white", "padding": "18px 24px", "borderRadius": "8px"})


# Function: build_app
# Construit l'application Dash : en-tête, chiffres clés, une section par requête.
# Les contrôles (liste déroulante, curseurs) mettent à jour les graphiques via des callbacks.
# Input:  results (dict de compute_results)
# Output: application Dash (à lancer avec app.run())
def build_app(results):
    app = Dash(__name__, title="NASA Wildfire Intelligence")
    r = results
    n_rules = len(r["rules"])

    app.layout = html.Div([
        build_header(),
        html.Div([card(*k) for k in compute_kpis(r)],
                 style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "margin": "16px 0"}),

        section("q1", [
            html.Label("Indicateur affiché sur la carte :"),
            dcc.Dropdown(id="q1-metric", clearable=False, value="total_frp_gw",
                         options=[{"label": "Énergie cumulée (GW)", "value": "total_frp_gw"},
                                  {"label": "Nombre de détections", "value": "n_detections"},
                                  {"label": "FRP médiane (MW)", "value": "median_frp"}],
                         style={"maxWidth": "320px"}),
            dcc.Graph(id="q1-map"),
            html.Div([dcc.Graph(figure=plot_top_states(r["by_state"]), style={"flex": "1 1 450px"}),
                      dcc.Graph(figure=plot_year_region(r["by_year_region"]), style={"flex": "1 1 450px"})],
                     style={"display": "flex", "flexWrap": "wrap"}),
        ]),

        section("q2", [
            html.Label("Nombre de règles affichées :"),
            dcc.Slider(id="q2-top", min=5, max=n_rules, step=1, value=min(15, n_rules),
                       marks={i: str(i) for i in range(5, n_rules + 1, 5)}),
            dcc.Graph(id="q2-rules"),
        ]),

        section("q3", [
            html.Div([card("Erreur SARIMA (MAPE)", f"{r['mape']['SARIMA']} %", "sur les 12 mois de test"),
                      card("Erreur méthode naïve", f"{r['mape']['naïf (N-1)']} %",
                           "« même mois l'an dernier »")],
                     style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "maxWidth": "600px"}),
            dcc.Graph(figure=plot_forecast(r["series"], r["test_pred"], r["future_pred"], "2019-10-01")),
            html.H4("Réel vs prévu sur la période de test"),
            df_to_table(r["comparison"].reset_index(names="mois")
                        .assign(mois=lambda t: t["mois"].dt.strftime("%m/%Y")), max_rows=12),
        ]),

        section("q4", [
            html.Label("Rayon de voisinage DBSCAN (km) :"),
            dcc.Slider(id="q4-eps", min=3, max=10, step=1, value=5,
                       marks={i: f"{i} km" for i in range(3, 11)}),
            html.Div(id="q4-summary", style={"fontWeight": 600, "margin": "8px 0"}),
            dcc.Graph(id="q4-map"),
            html.H4("Les 10 foyers les plus énergétiques"),
            html.Div(id="q4-table"),
        ]),

        html.Footer(["Sources : NASA FIRMS (MODIS C6) · US Census Bureau. ",
                     "Projet Programming for Data Science — ESILV."],
                    style={"color": "#666", "fontSize": "12px", "padding": "8px 0 24px"}),
    ], style={"fontFamily": FONT, "background": "#f6f6f6", "padding": "16px",
              "maxWidth": "1300px", "margin": "0 auto"})

    # --- Callbacks : chaque contrôle met à jour son graphique

    # Function: update_q1 (callback)
    # Redessine la carte Q1 quand on change l'indicateur dans la liste déroulante.
    # Input:  metric (str) — colonne choisie : total_frp_gw, n_detections ou median_frp
    # Output: figure plotly (carte des États)
    @app.callback(Output("q1-map", "figure"), Input("q1-metric", "value"))
    def update_q1(metric):
        return plot_state_map(r["by_state"], metric=metric)

    # Function: update_q2 (callback)
    # Redessine le graphique Q2 quand on change le nombre de règles avec le curseur.
    # Input:  top (int) — nombre de règles affichées
    # Output: figure plotly (barres des règles)
    @app.callback(Output("q2-rules", "figure"), Input("q2-top", "value"))
    def update_q2(top):
        return plot_rules(r["rules"], top=top)

    # Function: update_q4 (callback)
    # Relance DBSCAN avec le rayon choisi, puis met à jour la carte, le tableau et le résumé.
    # Input:  eps_km (int) — rayon de voisinage en km
    # Output: (figure plotly, tableau HTML des 10 premiers foyers, texte de résumé)
    @app.callback(Output("q4-map", "figure"), Output("q4-table", "children"),
                  Output("q4-summary", "children"), Input("q4-eps", "value"))
    def update_q4(eps_km):
        clustered = spatial_clustering(r["points"], eps_km=eps_km)  # DBSCAN relancé (~1 s)
        clusters = summarize_clusters(clustered)
        cols = ["rank", "state", "n_detections", "total_frp_gw", "start", "end", "duration_days"]
        table = clusters[cols].assign(start=clusters["start"].dt.strftime("%d/%m"),
                                      end=clusters["end"].dt.strftime("%d/%m"))
        summary = (f"{len(r['points']):,} détections → {len(clusters)} foyers · "
                   f"bruit : {(clustered['cluster'] < 0).mean():.1%}").replace(",", " ")
        return plot_clusters(clustered, clusters), df_to_table(table), summary

    return app


# Function: free_port
# Cherche un port libre à partir de `start`. Évite que le lancement échoue si le
# dashboard tourne déjà ailleurs (ex. scripts/run_dashboard.py ouvert pendant la démo).
# Input:  start (int) — premier port essayé, tries (int) — nombre de ports essayés
# Output: int — numéro du premier port libre
def free_port(start=8050, tries=10):
    for port in range(start, start + tries):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:  # rien n'écoute sur ce port
                return port
    raise RuntimeError(f"Aucun port libre entre {start} et {start + tries - 1}")


# Function: export_dashboard_html
# Exporte une version statique du dashboard (toutes les figures, sans serveur) dans un
# fichier HTML autonome : preuve de fonctionnement demandée par les consignes.
# Input:  results (dict de compute_results), file_path (str | Path)
# Output: aucun (écrit le fichier)
def export_dashboard_html(results, file_path):
    r = results
    figs = {
        "q1": [plot_state_map(r["by_state"]), plot_top_states(r["by_state"]),
               plot_year_region(r["by_year_region"])],
        "q2": [plot_rules(r["rules"])],
        "q3": [plot_forecast(r["series"], r["test_pred"], r["future_pred"], "2019-10-01")],
        "q4": [plot_clusters(r["clustered"], r["clusters"])],
    }
    first = True
    body = []
    for key, fig_list in figs.items():
        title, text = SECTIONS[key]
        body.append(f"<section><h2>{title}</h2><p>{text}</p>")
        for fig in fig_list:
            # plotly.js est intégré une seule fois (fichier lisible hors ligne)
            body.append(fig.to_html(full_html=False, include_plotlyjs=first))
            first = False
        if key == "q3":
            body.append(f"<p><b>MAPE SARIMA :</b> {r['mape']['SARIMA']} % — "
                        f"<b>MAPE naïf :</b> {r['mape']['naïf (N-1)']} %</p>")
            body.append(r["comparison"].to_html())
        if key == "q4":
            body.append(r["clusters"].head(10).to_html(index=False))
        body.append("</section>")
    kpis = "".join(f"<div class='kpi'><small>{a}</small><b>{b}</b><small>{c}</small></div>"
                   for a, b, c in compute_kpis(r))
    html_doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>NASA Wildfire Intelligence — dashboard</title>
<style>
body {{font-family:{FONT}; background:#f6f6f6; max-width:1300px; margin:0 auto; padding:16px}}
header {{background:{ORANGE}; color:white; padding:18px 24px; border-radius:8px}}
header a {{color:white}} section {{background:white; border-radius:8px; padding:16px 20px; margin:16px 0}}
.kpis {{display:flex; gap:12px; flex-wrap:wrap; margin:16px 0}}
.kpi {{flex:1 1 200px; background:white; border-radius:8px; padding:14px 16px; display:flex; flex-direction:column}}
.kpi b {{font-size:26px; color:{ORANGE}}} table {{border-collapse:collapse; font-size:13px}}
td, th {{padding:4px 10px; border-bottom:1px solid #ddd}}
</style></head><body>
<header><h1>NASA Wildfire Intelligence</h1>
<div><b>Dataset :</b> {config.DATASET_NAME}</div>
<div><b>Dataset externe :</b> {config.EXTERNAL_DATASET_NAME}</div>
<div><b>Équipe :</b> {" · ".join(config.TEAM)}</div>
<a href="{config.GITHUB_URL}">Dépôt GitHub</a></header>
<div class="kpis">{kpis}</div>
{"".join(body)}
<footer><small>Version statique du dashboard Dash (export). Sources : NASA FIRMS (MODIS C6) · US Census Bureau.</small></footer>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
