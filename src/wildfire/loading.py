"""Phase 1 — chargement des données brutes."""
import pandas as pd


# Function: load_data
# Lit un fichier CSV FIRMS (compressé ou non) dans un DataFrame.
# Input:  file_path (str | Path) — chemin vers le CSV (.csv ou .csv.gz)
# Output: DataFrame pandas, une ligne par détection de point chaud
def load_data(file_path):
    # acq_time est au format HHMM (ex. "0457") : lu en texte pour garder les zéros initiaux
    # version vaut 6.03 (archive) ou "6.0NRT" (NRT) : lue en texte pour un type homogène après fusion
    return pd.read_csv(file_path, dtype={"acq_time": str, "version": str})


# Function: merge_archive_nrt
# Concatène l'archive (qualité standard) et le fichier NRT (temps quasi réel).
# Input:  archive (DataFrame), nrt (DataFrame)
# Output: DataFrame unique avec une colonne `source` ("archive" / "nrt")
def merge_archive_nrt(archive, nrt):
    archive = archive.assign(source="archive")  # trace de l'origine de chaque ligne
    nrt = nrt.assign(source="nrt")
    # Le NRT n'a pas de colonne `type` : elle sera NaN pour ces lignes (traité en phase 2)
    return pd.concat([archive, nrt], ignore_index=True)
