"""Q3 — Requête temporelle : prévision du nombre mensuel de détections (SARIMA)."""
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX


# Function: monthly_series
# Nombre de détections par mois. Le premier mois (sept. 2010) est retiré
# car il ne contient que 4 jours de données (série commencée le 27/09/2010).
# Input:  df (DataFrame nettoyé avec `acq_date`)
# Output: Series indexée par le 1er jour de chaque mois
def monthly_series(df):
    s = df.groupby(df["acq_date"].dt.to_period("M")).size()
    s.index = s.index.to_timestamp()
    s = s.asfreq("MS", fill_value=0)  # fréquence mensuelle explicite (requis par SARIMA)
    return s.iloc[1:].rename("n_detections")


# Function: split_train_test
# Sépare la série en apprentissage et test. Par défaut, le test couvre les 12 derniers mois
# (oct. 2019 -> sept. 2020) : un cycle saisonnier complet, qui inclut le fichier NRT.
# Input:  series (Series mensuelle), test_start (str) — premier mois de test
# Output: (train, test)
def split_train_test(series, test_start="2019-10-01"):
    return series[series.index < test_start], series[series.index >= test_start]


# Function: fit_sarima
# Ajuste un modèle SARIMA sur le logarithme des comptages.
# Le log stabilise la variance (les pics d'été sont très hauts) et garantit des prévisions positives.
# Input:  train (Series), order (p,d,q), seasonal_order (P,D,Q,s) — s = 12 mois
# Output: modèle statsmodels ajusté
def fit_sarima(train, order=(1, 0, 1), seasonal_order=(1, 1, 1, 12)):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # avertissements de convergence sans impact ici
        model = SARIMAX(np.log1p(train), order=order, seasonal_order=seasonal_order)
        return model.fit(disp=False)


# Function: forecast
# Prévision sur `steps` mois, avec un intervalle de confiance à 80 %.
# Input:  fitted (modèle de fit_sarima), steps (int)
# Output: DataFrame (forecast, lower, upper) indexé par mois, en nombre de détections
def forecast(fitted, steps):
    pred = fitted.get_forecast(steps)
    ci = pred.conf_int(alpha=0.2)
    out = pd.DataFrame({"forecast": pred.predicted_mean,
                        "lower": ci.iloc[:, 0], "upper": ci.iloc[:, 1]})
    return np.expm1(out).round(0)  # retour à l'échelle des comptages


# Function: evaluate_forecast
# Compare la prévision SARIMA à une référence naïve ("même mois l'année précédente")
# avec l'erreur absolue moyenne en pourcentage (MAPE).
# Input:  series (Series complète), test (Series), pred (DataFrame de forecast)
# Output: DataFrame mois par mois (réel, SARIMA, naïf) + MAPE de chaque méthode
def evaluate_forecast(series, test, pred):
    naive = series.shift(12).loc[test.index]  # valeur du même mois, un an plus tôt
    table = pd.DataFrame({"réel": test, "SARIMA": pred["forecast"].loc[test.index], "naïf (N-1)": naive})
    mape = {m: (abs(table[m] - table["réel"]) / table["réel"]).mean() * 100
            for m in ["SARIMA", "naïf (N-1)"]}
    return table.astype(int), pd.Series(mape, name="MAPE (%)").round(1)


# Function: plot_forecast
# Série observée, prévision sur la période de test et prévision future.
# Input:  series (Series), test_pred (DataFrame), future_pred (DataFrame), test_start (str)
# Output: figure plotly
def plot_forecast(series, test_pred, future_pred, test_start="2019-10-01"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series, name="Observé", line=dict(color="#555")))
    for pred, name, color in [(test_pred, "Prévision sur la période de test", "#1b9e77"),
                              (future_pred, "Prévision future (12 mois)", "#d95f02")]:
        # bande d'incertitude (intervalle à 80 %)
        fig.add_trace(go.Scatter(x=list(pred.index) + list(pred.index[::-1]),
                                 y=list(pred["upper"]) + list(pred["lower"][::-1]),
                                 fill="toself", fillcolor=color, opacity=0.2, line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=pred.index, y=pred["forecast"], name=name,
                                 line=dict(color=color, dash="dash")))
    fig.add_vline(x=pd.Timestamp(test_start), line_dash="dot", line_color="grey")
    fig.update_layout(title="Q3 — Détections mensuelles : observé et prévision SARIMA",
                      xaxis_title="Mois", yaxis_title="Nombre de détections")
    return fig
