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


# Function: save_processed
# Sauvegarde les données nettoyées au format parquet (lecture ~10x plus rapide que le CSV).
# Input:  df (DataFrame), file_path (str | Path)
# Output: aucun (écrit le fichier)
def save_processed(df, file_path):
    df.to_parquet(file_path, index=False)


# Function: load_processed
# Recharge les données nettoyées depuis le cache parquet.
# Input:  file_path (str | Path)
# Output: DataFrame
def load_processed(file_path):
    return pd.read_parquet(file_path)
