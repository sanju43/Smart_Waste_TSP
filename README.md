# Smart Waste Collection Route Optimizer

Offline-first coding science-exhibition project based on the GCERT 2026-27 concept **કચરા ગાડી ઓપ્ટિમાઇઝર મોડેલ / Traveling Salesman Problem (TSP)**.

## What the app does

The Streamlit application demonstrates an end-to-end waste-collection routing workflow using a deterministic synthetic dataset:

1. Load/reset the seven-location exhibition demo.
2. Model the depot and collection points as X/Y coordinates.
3. Build the Euclidean distance matrix.
4. Generate a baseline input-order route.
5. Improve the route with **Nearest Neighbor + 2-opt**.
6. Persist the scenario, distance matrix, route, and route points in SQLite.
7. Compare distance and estimated travel time.
8. Animate the route and explain the mathematics.
9. Export route CSV, scenario JSON, and a printable HTML report.
10. Run diagnostics and a full offline exhibition acceptance flow.

The core demonstration does **not require internet access, maps, geocoding, APIs, or external services**.

## Stack

- Python 3.11+
- Streamlit
- Plotly
- Pandas
- NumPy
- NetworkX
- SQLAlchemy 2.0.x
- SQLite
- pytest

## Quick start

From the repository root:

```bash
python -m venv .venv

# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# Windows Command Prompt
.venv\\Scripts\\activate.bat

pip install -r requirements.txt
streamlit run app.py
```

Then open the Streamlit app and select **Dashboard → Start Demo**.

The app creates/initializes its SQLite database automatically. The optional `database/seed.py` script can create the default dataset directly, but it is not required for the main exhibition flow.

## Exhibition run

For a short 2–3 minute demonstration:

1. Open **Dashboard**.
2. Click **Start Demo**.
3. Show the route and active-location count.
4. Open **Results & Comparison** and explain baseline distance, improved distance, saved distance, and estimated time.
5. Open **Science Explanation** to explain Euclidean distance, TSP, Nearest Neighbor, and 2-opt.
6. Open **Presentation Mode** for the guided presentation and route simulation.
7. Use **Reports & Export** if a CSV, JSON, or printable HTML result is needed.
8. Use **Diagnostics** before the exhibition if you want to verify application health and run the complete offline acceptance flow.
9. If the demo state needs to be restored, return to **Dashboard → Reset Demo**.

For an airplane/offline demonstration, start the application and load the demo before disconnecting from the network. The core demo uses only local code, local SQLite data, and synthetic coordinates.

## Algorithms

- **Baseline:** input order.
- **Demo optimizer:** Nearest Neighbor + 2-opt heuristic.
- **Exact mode:** brute-force exact solver for small datasets only.

The heuristic route is described as **improved/optimized**, not guaranteed to be globally shortest.

## Pages

- **Dashboard:** exhibition control panel, demo/reset controls, speed setting, and route view.
- **Scenarios:** create/select scenarios.
- **Locations:** manage depot and collection points.
- **Distance Matrix:** inspect calculated pairwise distances.
- **Optimizer:** run baseline/heuristic/exact routing.
- **Results & Comparison:** compare routes, metrics, sequence, and simulation.
- **Science Explanation:** explain the mathematical model and heuristic.
- **Presentation Mode:** guided exhibition sequence with route simulation.
- **Reports & Export:** CSV, JSON import/export, printable HTML, and optional PDF support.
- **Diagnostics:** health checks, pytest diagnostics, and the full exhibition acceptance flow.

## Testing

Run the complete test suite with:

```bash
python -m pytest -q
```

The repository CI runs the same pytest suite on Python 3.11 for pushes to `main`/feature branches and pull requests targeting `main`.

## Offline design

The routing model intentionally uses synthetic X/Y coordinates and local Euclidean distance calculations. No live traffic, GPS, map tiles, routing APIs, or network calls are required for the exhibition workflow.

SQLite stores the local application state in `smart_waste_tsp.db`. The database file is ignored by Git.

## Project structure

```text
algorithms/      TSP solvers and validation
components/      Plotly route/map/simulation components
database/        SQLite database, SQLAlchemy models, seed data
pages/           Streamlit application pages
services/        Demo, distance, results, routes, reports, diagnostics, presentation
tests/           Automated unit/integration/edge-case tests
.github/         GitHub Actions CI
app.py           Streamlit entry point
requirements.txt Python dependencies
```
