from math import isfinite


def validate_locations(locations):
    active = [x for x in locations if x.is_active]
    depots = [x for x in active if x.type == "Depot"]
    points = [x for x in active if x.type == "Collection"]

    if len(depots) != 1:
        raise ValueError("Exactly one active depot is required before optimization.")
    if not points:
        raise ValueError("Add at least one active collection point before optimization.")

    for location in active:
        if location.x is None or location.y is None:
            raise ValueError(f"Location '{location.name}' must have valid X/Y coordinates.")
        if not isfinite(float(location.x)) or not isfinite(float(location.y)):
            raise ValueError(f"Location '{location.name}' has invalid X/Y coordinates.")

    return depots[0], points


def validate_route(route, depot_id, collection_ids):
    if not route:
        raise ValueError("No route was generated.")
    if not collection_ids:
        raise ValueError("At least one collection point is required.")
    if route[0] != depot_id or route[-1] != depot_id:
        raise ValueError("Route must start and end at the depot.")

    visited = route[1:-1]
    expected = list(collection_ids)
    if len(visited) != len(expected) or set(visited) != set(expected):
        raise ValueError("Route must visit every active collection point exactly once.")
    if len(visited) != len(set(visited)):
        raise ValueError("Route contains duplicate collection points.")
    return True


def find_duplicate_coordinates(locations):
    active = [x for x in locations if x.is_active]
    groups = {}
    for location in active:
        key = (float(location.x), float(location.y))
        groups.setdefault(key, []).append(location)
    return [group for group in groups.values() if len(group) > 1]
