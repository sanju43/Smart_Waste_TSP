def nearest_neighbor(nodes, distance):
    start = nodes[0]
    unvisited = set(nodes[1:])
    route = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda n: distance[current][n])
        route.append(nxt); unvisited.remove(nxt); current = nxt
    route.append(start)
    return route
