"""Pure route-simulation helpers used by the Streamlit animation UI."""

def animation_steps(locations, route):
    """Return deterministic animation frames for a saved route.

    Each frame represents the vehicle after reaching one more route location.
    The returned data is UI-agnostic so it can be tested without Streamlit.
    """
    by_id = {location.id: location for location in locations}
    if not route:
        return []
    missing = [location_id for location_id in route if location_id not in by_id]
    if missing:
        raise ValueError(f"Route references unknown location(s): {missing}")

    steps = []
    visited = []
    for sequence, location_id in enumerate(route, start=1):
        visited.append(location_id)
        path = [by_id[item] for item in visited]
        vehicle = by_id[location_id]
        steps.append({
            "sequence": sequence,
            "location_id": location_id,
            "visited_ids": list(visited),
            "path_x": [point.x for point in path],
            "path_y": [point.y for point in path],
            "vehicle_x": vehicle.x,
            "vehicle_y": vehicle.y,
            "label": f"Stop {sequence}: {vehicle.name}",
        })
    return steps
