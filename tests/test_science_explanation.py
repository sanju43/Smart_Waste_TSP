from pathlib import Path

def test_science_page_contains_core_tsp_terms():
    text = Path("pages/6_Science_Explanation.py").read_text(encoding="utf-8")
    for term in ("Traveling Salesman Problem", "Nearest Neighbor", "2-opt", "distance matrix", "heuristic"):
        assert term in text
