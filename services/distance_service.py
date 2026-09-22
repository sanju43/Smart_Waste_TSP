from math import hypot

def euclidean(a, b): return hypot(a.x - b.x, a.y - b.y)

def build_distance_matrix(locations):
    return {a.id: {b.id: euclidean(a,b) for b in locations} for a in locations}
