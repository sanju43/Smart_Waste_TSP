def validate_locations(locations):
    depots = [x for x in locations if x.type == "Depot" and x.is_active]
    points = [x for x in locations if x.type != "Depot" and x.is_active]

    if len(depots) != 1:
        raise ValueError("Exactly one active depot is required.")
    if not points:
        raise ValueError("At least one active collection point is required.")

    for location in locations:
        if location.is_active and (location.x is None or location.y is None):
            raise ValueError(f"Location '{location.name}' must have valid X/Y coordinates.")

    return depots[0], points

def validate_route(route, depot_id, collection_ids):
    if not route or route[0] != depot_id or route[-1] != depot_id:
        raise ValueError("Route must start and end at the depot.")
    visited = route[1:-1]
    if len(visited) != len(collection_ids) or set(visited) != set(collection_ids):
        raise ValueError("Route must visit every active collection point exactly once.")
    if len(visited) != len(set(visited)):
        raise ValueError("Route contains duplicate collection points.")
    return True
