"""Lance le dashboard hors du notebook (pratique pour la démo).

Usage (depuis la racine du projet) :
    .venv/bin/python scripts/run_dashboard.py            # http://127.0.0.1:8050
    .venv/bin/python scripts/run_dashboard.py --export   # écrit aussi reports/Maigre_dashboard.html
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wildfire import config  # noqa: E402
from wildfire.dashboard import build_app, compute_results, export_dashboard_html, free_port  # noqa: E402
from wildfire.loading import load_processed  # noqa: E402

if __name__ == "__main__":
    # Le fichier nettoyé est produit par la section 2 du notebook
    results = compute_results(load_processed(config.CLEAN_FILE))
    if "--export" in sys.argv:
        export_dashboard_html(results, config.DASHBOARD_HTML)
        print("Export :", config.DASHBOARD_HTML)
    build_app(results).run(debug=False, port=free_port(8050))
