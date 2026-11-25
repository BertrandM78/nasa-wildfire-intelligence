"""Q2 — Fouille de motifs fréquents : règles d'association (FP-Growth)."""
import numpy as np
import pandas as pd
import plotly.express as px
from mlxtend.frequent_patterns import association_rules, fpgrowth

# Classes d'intensité (FRP en MW), proches des quantiles observés en §1.5 :
# ~20 % des détections < 10 MW, ~15 % > 100 MW.
FRP_BINS = [0, 10, 100, np.inf]
FRP_LABELS = ["faible", "moyenne", "forte"]


# Function: build_transactions
# Transforme chaque détection en "panier" d'attributs (une transaction) :
#   saison, région, moment (jour/nuit), intensité (classe de FRP).
# La confiance n'est pas utilisée : la NASA la calcule en partie à partir de la chaleur
# du pixel, elle produirait des règles évidentes ("feu fort -> confiance haute").
# Chaque attribut devient une colonne booléenne "nom=valeur" (encodage one-hot).
# Input:  df (DataFrame nettoyé)
# Output: DataFrame booléen (une ligne par détection, une colonne par item)
def build_transactions(df):
    items = pd.DataFrame({
        "saison": df["season"],
        "région": df["region"],
        "moment": df["daynight"].map({"D": "jour", "N": "nuit"}),
        "intensité": pd.cut(df["frp"], bins=FRP_BINS, labels=FRP_LABELS),
    })
    return pd.get_dummies(items.astype(str), prefix_sep="=").astype(bool)


# Function: remove_redundant_rules
# Retire les règles "redondantes" : une règle {A, X} -> B est supprimée s'il existe une
# règle plus courte {A} -> B presque aussi forte. Ajouter X n'apporte alors rien.
# Input:  rules (DataFrame mlxtend, antecedents/consequents en frozenset)
#         min_gain (float) — gain de lift minimal exigé pour garder la règle longue (0.05 = +5 %)
# Output: DataFrame des règles non redondantes
def remove_redundant_rules(rules, min_gain=0.05):
    keep = []
    for _, r in rules.iterrows():
        # règles plus courtes, même conclusion, dont la prémisse est incluse dans celle de r
        shorter = rules[(rules["consequents"] == r["consequents"])
                        & rules["antecedents"].map(lambda a: a < r["antecedents"])]
        keep.append(shorter.empty or r["lift"] > shorter["lift"].max() * (1 + min_gain))
    return rules[keep]


# Function: mine_rules
# Cherche les combinaisons fréquentes (FP-Growth) puis en déduit des règles A -> B.
# Input:  transactions (DataFrame booléen de build_transactions)
#         min_support (float)    — part minimale des détections contenant la combinaison
#         min_confidence (float) — probabilité minimale P(B | A)
#         min_lift (float)       — gain minimal par rapport au hasard (lift > 1 = lien positif)
# Seules les règles à conclusion unique (B = un seul item) sont gardées : plus lisibles,
# et on évite les doublons du type A -> {B, C} / A, B -> C.
# Output: DataFrame des règles (antecedents, consequents, support, confidence, lift), trié par lift
def mine_rules(transactions, min_support=0.02, min_confidence=0.5, min_lift=1.2):
    itemsets = fpgrowth(transactions, min_support=min_support, use_colnames=True)
    rules = association_rules(itemsets, num_itemsets=len(transactions),
                              metric="confidence", min_threshold=min_confidence)
    rules = rules[(rules["lift"] >= min_lift) & (rules["consequents"].map(len) == 1)]
    rules = remove_redundant_rules(rules)
    # frozenset -> texte lisible
    to_txt = lambda s: ", ".join(sorted(s))
    rules = rules.assign(antecedents=rules["antecedents"].map(to_txt),
                         consequents=rules["consequents"].map(to_txt))
    cols = ["antecedents", "consequents", "support", "confidence", "lift"]
    return rules[cols].sort_values("lift", ascending=False).round(3).reset_index(drop=True)


# Function: plot_rules
# Diagramme en barres des règles les plus fortes, classées par lift.
# Le texte de chaque règle est affiché ; la confiance et le support sont au survol.
# Input:  rules (DataFrame de mine_rules), top (int) — nombre de règles affichées
# Output: figure plotly
def plot_rules(rules, top=15):
    r = rules.head(top).iloc[::-1].copy()  # inversé : la règle la plus forte en haut
    r["règle"] = "{" + r["antecedents"] + "} → " + r["consequents"]
    fig = px.bar(r, x="lift", y="règle", orientation="h", color="confidence",
                 color_continuous_scale="OrRd", range_color=(0.5, 1),
                 hover_data={"support": ":.3f", "confidence": ":.2f", "règle": False},
                 labels={"lift": "Lift (× plus fréquent que le hasard)", "règle": "",
                         "confidence": "Confiance"})
    fig.add_vline(x=1, line_dash="dot", line_color="grey")  # lift = 1 : aucun lien
    fig.update_layout(title=f"Q2 — Les {len(r)} règles d'association les plus fortes",
                      height=150 + 28 * len(r))
    return fig
