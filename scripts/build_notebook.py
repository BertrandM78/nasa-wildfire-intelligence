"""Rend le notebook livrable autonome : recopie le code de src/wildfire/ dans ses cellules.

Le notebook final ne doit dépendre d'aucun fichier .py (il est déposé seul sur DVLC) et le
correcteur doit y lire chaque fonction. Ce script :
  1. rassemble tous les imports externes des modules dans la cellule d'imports ;
  2. transforme config.py en une classe `config` (les appels `config.X` restent identiques) ;
  3. insère une cellule de code par module, après la cellule "## Function definitions" ;
  4. vérifie que chaque fonction a son en-tête Function / Input / Output.

Les cellules générées portent un tag ("generated") : relancer le script les remplace,
sans toucher aux cellules de texte et de résultats écrites à la main.

Usage (depuis la racine du projet) :
    .venv/bin/python scripts/build_notebook.py
"""
import ast
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "wildfire"
NOTEBOOK = ROOT / "notebooks" / "Maigre_notebook.ipynb"
TAG = "generated"

# Ordre des modules = ordre des étapes du projet (chaque module n'utilise que les précédents)
MODULES = [
    ("config", "Configuration : chemins des fichiers, équipe, dataset"),
    ("loading", "Étape 1 — Chargement des données"),
    ("exploration", "Étape 1 — Exploration"),
    ("cleaning", "Étape 2 — Nettoyage"),
    ("geo", "Étape 2 — Enrichissement géographique (dataset externe)"),
    ("q1_aggregation", "Q1 — Agrégation"),
    ("q2_patterns", "Q2 — Motifs fréquents"),
    ("q3_forecast", "Q3 — Prévision temporelle"),
    ("q4_spatial", "Q4 — Clustering spatial"),
    ("dashboard", "Dashboard Dash"),
]

# Dans le notebook, il n'y a pas de __file__ : la racine du projet est déduite du dossier courant
NOTEBOOK_ROOT = ('ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()'
                 '  # racine du projet')


# Function: split_module
# Sépare le code d'un module en (imports externes, corps sans imports ni docstring).
# Les imports internes (`from wildfire ...`) sont supprimés : tout est dans le même notebook.
# Input:  source (str) — code du module
# Output: (liste des lignes d'import externes, corps du module en texte)
def split_module(source):
    tree = ast.parse(source)
    lines = source.splitlines()
    drop, imports = set(), []
    for node in tree.body:
        is_doc = (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                  and isinstance(node.value.value, str))
        if isinstance(node, (ast.Import, ast.ImportFrom)) or is_doc:
            drop.update(range(node.lineno - 1, node.end_lineno))
            internal = isinstance(node, ast.ImportFrom) and (node.module or "").startswith("wildfire")
            if not is_doc and not internal:
                imports.append(ast.unparse(node))
    body = "\n".join(l for i, l in enumerate(lines) if i not in drop).strip("\n")
    return imports, body


# Function: config_as_class
# Transforme le corps de config.py en classe `config`, pour garder la notation config.X.
# Input:  body (str) — corps de config.py (sans imports)
# Output: str — code de la classe
def config_as_class(body):
    lines = [NOTEBOOK_ROOT if l.startswith("ROOT =") else l for l in body.splitlines()]
    return ("# Classe utilisée comme espace de noms : config.ARCHIVE_FILE, config.TEAM, etc.\n"
            "class config:\n" + "\n".join(("    " + l) if l.strip() else "" for l in lines))


# Function: check_headers
# Vérifie que chaque fonction (y compris les callbacks imbriqués) est précédée
# d'un commentaire contenant "Function:", "Input:" et "Output:" (exigé par les consignes).
# Input:  name (str) — nom du module, source (str) — son code
# Output: liste des fonctions sans en-tête complet
def check_headers(name, source):
    lines = source.splitlines()
    missing = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef):
            first = min([d.lineno for d in node.decorator_list] + [node.lineno]) - 1
            comment, i = [], first - 1
            while i >= 0 and lines[i].strip().startswith("#"):
                comment.append(lines[i])
                i -= 1
            text = "\n".join(comment)
            if not all(k in text for k in ("Function:", "Input:", "Output:")):
                missing.append(f"{name}.{node.name}")
    return missing


# Function: build_cells
# Construit les cellules générées : imports, puis une cellule de code par module.
# Input:  aucun (lit src/wildfire/)
# Output: (cellule d'imports, liste des cellules de fonctions)
def build_cells():
    all_imports, func_cells, missing = [], [], []
    for name, title in MODULES:
        source = (SRC / f"{name}.py").read_text(encoding="utf-8")
        missing += check_headers(name, source)
        imports, body = split_module(source)
        all_imports += [i for i in imports if i not in all_imports]
        if name == "config":
            body = config_as_class(body)
        code = f"# ===== {title} (src/wildfire/{name}.py) =====\n\n{body}"
        func_cells.append(nbformat.v4.new_code_cell(code, metadata={"tags": [TAG]}))
    if missing:
        sys.exit(f"En-tête Function/Input/Output manquant : {', '.join(missing)}")
    # imports "import x" d'abord, puis "from x import y"
    all_imports.sort(key=lambda s: (s.startswith("from"), s))
    imports_code = ("# Toutes les bibliothèques utilisées par le projet\n"
                    + "\n".join(all_imports)
                    + '\n\npd.set_option("display.max_columns", None)')
    return nbformat.v4.new_code_cell(imports_code, metadata={"tags": [TAG]}), func_cells


# Function: build_notebook
# Remplace la cellule d'imports et les cellules de fonctions du notebook par une version
# générée depuis src/ ; toutes les autres cellules sont conservées telles quelles.
# Input:  path (Path) — notebook à mettre à jour
# Output: aucun (réécrit le notebook)
def build_notebook(path=NOTEBOOK):
    nb = nbformat.read(path, as_version=4)
    imports_cell, func_cells = build_cells()
    is_generated = lambda c: TAG in c.metadata.get("tags", [])
    # 1re exécution : l'ancienne cellule d'imports (sys.path + autoreload) est aussi remplacée
    is_old_imports = lambda c: c.cell_type == "code" and "from wildfire" in c.source
    cells = [c for c in nb.cells if not (is_generated(c) or is_old_imports(c))]
    i_imp = next(i for i, c in enumerate(cells) if c.source.startswith("## Import libraries"))
    cells.insert(i_imp + 1, imports_cell)
    i_fun = next(i for i, c in enumerate(cells) if c.source.startswith("## Function definitions"))
    cells[i_fun].source = (
        "## Function definitions\n"
        "Toutes les fonctions du projet, regroupées par étape. Chacune est précédée d'un commentaire "
        "**Function / Input / Output**.\n\n"
        "*Ces cellules sont générées automatiquement depuis `src/wildfire/` par "
        "`scripts/build_notebook.py` : pour modifier une fonction, modifier le fichier .py puis relancer "
        "le script.*")
    cells[i_fun + 1:i_fun + 1] = func_cells
    nb.cells = cells
    nbformat.validate(nb)
    nbformat.write(nb, path)
    print(f"{path.name} : {len(func_cells)} cellules de fonctions générées")


if __name__ == "__main__":
    build_notebook()
