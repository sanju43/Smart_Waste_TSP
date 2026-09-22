from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt
from algorithms.exact_tsp import exact_tsp

def optimize(node_ids, matrix, mode="Nearest Neighbor + 2-opt"):
    if mode == "Exact (small N)": return exact_tsp(node_ids, matrix), "Exact"
    initial = nearest_neighbor(node_ids, matrix)
    return two_opt(initial, matrix), "Nearest Neighbor + 2-opt"
