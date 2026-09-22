def route_distance(route, distance):
    return sum(distance[route[i]][route[i+1]] for i in range(len(route)-1))

def two_opt(route, distance):
    best = route[:]
    improved = True
    while improved:
        improved = False
        best_cost = route_distance(best, distance)
        for i in range(1, len(best)-2):
            for j in range(i+1, len(best)-1):
                candidate = best[:i] + best[i:j+1][::-1] + best[j+1:]
                cost = route_distance(candidate, distance)
                if cost + 1e-9 < best_cost:
                    best, best_cost, improved = candidate, cost, True
        
    return best
