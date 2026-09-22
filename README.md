# Smart Waste Collection Route Optimizer

Coding-only science exhibition project based on the GCERT 2026-27 concept **કચરા ગાડી ઓપ્ટિમાઇઝર મોડેલ / Traveling Salesman Problem (TSP)**.

## Stack
Python 3.11+, Streamlit, Plotly, Pandas, NumPy, NetworkX, SQLAlchemy, SQLite, pytest.

## Run
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
python database/seed.py
streamlit run app.py
```

Open the sidebar pages. Core demo is offline-first and uses synthetic X/Y coordinates.

## Algorithms
- Baseline: input order
- Demo default: Nearest Neighbor + 2-opt
- Exact mode: brute-force exact solver for small datasets only

Heuristic output is described as **improved/optimized**, not guaranteed globally shortest.

## Project modules
M01 Dashboard, M02 Scenario Manager, M03 Location Manager, M04 Digital Map/Grid, M05 Distance Matrix, M06 TSP Optimizer, M07 Route Simulation, M08 Results & Comparison, M09 Science Explanation, M10 Presentation Mode, M11 Demo Data/Settings, M12 Reports/Export, M13 Tests/Diagnostics.

This starter implementation covers the core end-to-end demo and foundational architecture. Modules such as full route animation, report export, diagnostics UI, repository abstraction, and advanced scenario selection can be expanded using the master specification.
