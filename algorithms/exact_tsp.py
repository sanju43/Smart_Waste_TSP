from itertools import permutations
from .two_opt import route_distance

def exact_tsp(nodes, distance):
    if len(nodes) > 9:
        raise ValueError("Exact mode is limited to small datasets (max 9 nodes including depot).")
    start = nodes[0]
    best = None; best_cost = float("inf")
    for perm in permutations(nodes[1:]):
        route = [start, *perm, start]
        cost = route_distance(route, distance)
        if cost < best_cost:
            best, best_cost = route, cost
    return best
