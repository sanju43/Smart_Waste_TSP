def route_metrics(route, distance, average_speed=30.0):
    if len(route) < 2:
        return {"total_distance": 0.0, "estimated_minutes": 0.0, "stops": 0}

    if average_speed <= 0:
        raise ValueError("Average vehicle speed must be greater than zero.")

    total = sum(float(distance[route[i]][route[i + 1]]) for i in range(len(route) - 1))
    return {
        "total_distance": total,
        "estimated_minutes": total / average_speed * 60,
        "stops": max(0, len(route) - 2),
    }


def compare(baseline, improved, distance, average_speed=30.0):
    baseline_metrics = route_metrics(baseline, distance, average_speed)
    improved_metrics = route_metrics(improved, distance, average_speed)
    baseline_distance = baseline_metrics["total_distance"]
    improved_distance = improved_metrics["total_distance"]
    saved = baseline_distance - improved_distance
    return {
        "baseline": baseline_distance,
        "improved": improved_distance,
        "saved": saved,
        "percent_saved": (saved / baseline_distance * 100 if baseline_distance else 0.0),
        "baseline_minutes": baseline_metrics["estimated_minutes"],
        "improved_minutes": improved_metrics["estimated_minutes"],
    }


def route_rows(route, locations, distance):
    """Return exhibition-friendly route sequence rows."""
    by_id = {location.id: location for location in locations}
    rows = []
    cumulative = 0.0
    for sequence, location_id in enumerate(route, start=1):
        location = by_id[location_id]
        leg = 0.0 if sequence == 1 else float(distance[route[sequence - 2]][location_id])
        cumulative += leg
        rows.append(
            {
                "Stop": sequence,
                "Location": location.name,
                "Type": location.type,
                "Distance from previous": round(leg, 2),
                "Cumulative distance": round(cumulative, 2),
            }
        )
    return rows
